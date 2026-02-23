from utils.logger import logger
import random
from datetime import datetime, timedelta
from database import db
from config_topics import SEARCH_QUERIES, TOPICS_LIST, INFLUENCERS
from tweet_handler import tweet_handler
from utils.sanitizer import sanitize_search_query
from config import Config


def _weighted_engagement(tweet: dict) -> int:
    metrics = tweet.get("public_metrics", {}) or {}
    likes = int(metrics.get("like_count", 0) or 0)
    retweets = int(metrics.get("retweet_count", 0) or 0)
    replies = int(metrics.get("reply_count", 0) or 0)
    return likes + (retweets * 2) + (replies * 2)


def _normalize_topic(name: str) -> str:
    return " ".join((name or "").lower().split())


def _is_topic_query_usable(topic: str) -> bool:
    """Keep discovery topics short, searchable, and operator-safe."""
    t = (topic or "").strip()
    if not t:
        return False

    lower = t.lower()
    words = t.split()

    # Skip long headline-like strings that frequently break search parsing.
    if len(words) > 6:
        return False
    if len(t) > 48:
        return False

    # Skip quote-heavy/news-title style values.
    if ":" in t or '"' in t or "'" in t:
        return False

    # Skip obvious URL-ish or noisy text fragments.
    if "http" in lower or "/" in t:
        return False

    return True


def _select_fresh_topics(trends: list, source: str, limit: int, lookback_hours: int = 24) -> list:
    """
    Prefer topics that were not selected recently.
    Falls back to older/repeated topics only if needed.
    """
    if not trends:
        return []

    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
    recent_names = set()
    try:
        recent = db.trends.find(
            {"fetched_at": {"$gte": cutoff}, "source": source},
            {"name": 1}
        )
        recent_names = {_normalize_topic(doc.get("name", "")) for doc in recent}
    except Exception as e:
        logger.debug(f"Trend history lookup skipped: {e}")

    unique = []
    seen = set()
    for t in trends:
        key = _normalize_topic(t)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(t)

    fresh = [t for t in unique if _normalize_topic(t) not in recent_names]
    selected = fresh[:limit]
    if len(selected) < limit:
        remainder = [t for t in unique if t not in selected]
        random.shuffle(remainder)
        selected.extend(remainder[: max(0, limit - len(selected))])

    try:
        if selected:
            now = datetime.utcnow()
            db.trends.insert_many([
                {"name": topic, "source": source, "fetched_at": now}
                for topic in selected
            ])
    except Exception as e:
        logger.debug(f"Trend history write skipped: {e}")

    return selected[:limit]


def get_trending_topics(limit: int = 5) -> list:
    """Get engagement topics from curated query sets (no X trends endpoint calls)."""
    # Try 1: Curated niche queries.
    try:
        logger.info("Using curated niche queries for trend discovery...")
        pool = [q.strip() for q in SEARCH_QUERIES if q and q.strip()]
        random.shuffle(pool)
        selected = _select_fresh_topics(pool, source="curated_queries", limit=limit, lookback_hours=12)
        if selected:
            logger.info(f"✓ Got {len(selected)} rotated curated topics")
            return selected
    except Exception as e:
        logger.debug(f"Curated topics fallback failed: {e}")

    # Final fallback: configured queries or generic technology topics.
    fallback_topics = SEARCH_QUERIES or [
        "#ai",
        "#programming",
        "#softwareengineering",
        "#productivity",
        "#startups",
    ]
    logger.info("Using configured fallback topics")
    return fallback_topics[:limit]


def discover_active_topics(limit: int = 5, pool_size: int = 10, sample_size: int = 10) -> list:
    """
    Discover and rank active topics using live search signals.
    Returns top topic strings for main engagement flow.
    """
    pool = []
    for t in SEARCH_QUERIES + TOPICS_LIST:
        cleaned = sanitize_search_query(str(t).strip())
        if cleaned and _is_topic_query_usable(cleaned):
            pool.append(cleaned)

    # Add influencer-adjacent discovery to catch larger conversation clusters.
    for influencer in INFLUENCERS[:4]:
        q = sanitize_search_query(f"@{influencer}")
        if q and _is_topic_query_usable(q):
            pool.append(q)

    # Expand pool with what has worked recently (day-by-day adaptive discovery).
    lookback_days = max(1, Config.TOPIC_DISCOVERY_LOOKBACK_DAYS)
    since = datetime.utcnow() - timedelta(days=lookback_days)
    try:
        recent_reply_topics = db.activity_logs.find(
            {
                "action": "reply",
                "success": True,
                "timestamp": {"$gte": since},
            },
            {"metadata.trend": 1, "metadata.safe_query": 1},
        ).sort("timestamp", -1).limit(120)
        for doc in recent_reply_topics:
            meta = doc.get("metadata", {}) or {}
            for key in ("safe_query", "trend"):
                topic = sanitize_search_query(str(meta.get(key, "")).strip())
                if topic and _is_topic_query_usable(topic):
                    pool.append(topic)
    except Exception as e:
        logger.debug(f"Recent reply topic expansion skipped: {e}")

    # Do not reuse old generic trend-name history here; it can include noisy headlines.

    # Dedup while preserving order.
    seen = set()
    deduped = []
    for topic in pool:
        key = _normalize_topic(topic)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(topic)

    if not deduped:
        return []

    random.shuffle(deduped)
    # Expand candidate set slightly each day to avoid stale loops.
    day_bonus = datetime.utcnow().timetuple().tm_yday % 3
    candidates = deduped[: max(limit, pool_size + day_bonus)]

    # Prefer topics not selected in the recent window.
    recent_selected = set()
    try:
        recent = db.trends.find(
            {
                "source": "active_discovery_selected",
                "fetched_at": {"$gte": since},
            },
            {"name": 1},
        )
        recent_selected = {_normalize_topic(doc.get("name", "")) for doc in recent}
    except Exception as e:
        logger.debug(f"Recent active-topic lookup skipped: {e}")

    fresh_candidates = [c for c in candidates if _normalize_topic(c) not in recent_selected]
    if len(fresh_candidates) >= limit:
        candidates = fresh_candidates
    ranked = []
    bounded_sample = min(100, max(10, sample_size))

    for topic in candidates:
        tweets = tweet_handler.search_tweets(topic, max_results=bounded_sample) or []
        if not tweets:
            continue

        engagements = [_weighted_engagement(t) for t in tweets]
        avg_eng = sum(engagements) / max(1, len(engagements))
        max_eng = max(engagements) if engagements else 0
        unique_authors = len({str(t.get("author_id", "")) for t in tweets if t.get("author_id")})
        big_author_hits = 0
        for t in tweets:
            followers = (t.get("author_info", {}) or {}).get("followers_count", 0)
            if followers >= 5000:
                big_author_hits += 1

        score = (len(tweets) * 8) + (avg_eng * 0.7) + (max_eng * 0.3) + (unique_authors * 1.2) + (big_author_hits * 6)
        ranked.append((score, topic, len(tweets), int(avg_eng), int(max_eng), big_author_hits))

    if not ranked:
        return []

    ranked.sort(key=lambda x: x[0], reverse=True)
    # Diversity: avoid selecting only hashtags every run.
    selected = []
    max_hashtags = max(1, limit // 2)
    hashtag_count = 0
    for r in ranked:
        topic = r[1]
        is_hashtag = topic.startswith("#")
        if is_hashtag and hashtag_count >= max_hashtags and len(selected) < limit - 1:
            continue
        selected.append(topic)
        if is_hashtag:
            hashtag_count += 1
        if len(selected) >= max(1, limit):
            break

    # Fill if diversity constraints were too tight.
    if len(selected) < max(1, limit):
        for r in ranked:
            topic = r[1]
            if topic in selected:
                continue
            selected.append(topic)
            if len(selected) >= max(1, limit):
                break

    try:
        now = datetime.utcnow()
        if selected:
            db.trends.insert_many(
                [{"name": t, "source": "active_discovery_selected", "fetched_at": now} for t in selected]
            )
    except Exception as e:
        logger.debug(f"Active topic history write skipped: {e}")

    logger.info(f"✓ Active topic research selected {len(selected)} topics from pool={len(candidates)}")
    for _, topic, count, avg_eng, max_eng, big_hits in ranked[:max(1, limit)]:
        logger.info(f"  - topic='{topic}' tweets={count} avg_eng={avg_eng} max_eng={max_eng} big_authors={big_hits}")
    return selected
