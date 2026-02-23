import argparse
from datetime import datetime
from typing import Dict, List, Tuple

from config import Config
from config_topics import SEARCH_QUERIES, INFLUENCERS
from database import db
from operations.engagement_filters import evaluate_account_authenticity
from operations.trends_operation import get_trending_topics
from tweet_handler import tweet_handler
from utils.logger import logger
from utils.sanitizer import sanitize_search_query


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual research feed (read-only)")
    parser.add_argument(
        "--topics",
        type=str,
        default="",
        help="Comma-separated topics/queries to research (overrides auto topics).",
    )
    parser.add_argument(
        "--per-query",
        type=int,
        default=30,
        help="Tweets per query (X API range 10-100).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many tweets to print per section.",
    )
    parser.add_argument(
        "--min-big-followers",
        type=int,
        default=5000,
        help="Minimum followers to classify as big account.",
    )
    parser.add_argument(
        "--min-big-engagement",
        type=int,
        default=30,
        help="Minimum weighted engagement for big-account shortlist.",
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save shortlisted research candidates into MongoDB activity_logs.",
    )
    return parser.parse_args()


def _weighted_engagement(metrics: Dict) -> int:
    likes = int(metrics.get("like_count", 0) or 0)
    retweets = int(metrics.get("retweet_count", 0) or 0)
    replies = int(metrics.get("reply_count", 0) or 0)
    return likes + (retweets * 2) + (replies * 2)


def _candidate_score(tweet: Dict) -> float:
    author = tweet.get("author_info", {}) or {}
    metrics = tweet.get("public_metrics", {}) or {}
    followers = int(author.get("followers_count", 0) or 0)
    verified_bonus = 6 if author.get("verified", False) else 0
    engagement = _weighted_engagement(metrics)
    is_real, auth_score = evaluate_account_authenticity(author, metrics)
    if not is_real:
        return 0.0

    size_bonus = 0.0
    if followers >= 100000:
        size_bonus = 18.0
    elif followers >= 25000:
        size_bonus = 12.0
    elif followers >= 5000:
        size_bonus = 8.0
    elif followers >= 1000:
        size_bonus = 4.0

    engagement_bonus = 0.0
    if engagement >= 300:
        engagement_bonus = 22.0
    elif engagement >= 120:
        engagement_bonus = 16.0
    elif engagement >= 50:
        engagement_bonus = 10.0
    elif engagement >= 10:
        engagement_bonus = 5.0

    return round(min(100.0, (auth_score * 0.55) + size_bonus + engagement_bonus + verified_bonus), 1)


def _build_queries(topics: List[str]) -> List[Tuple[str, str]]:
    """Return list of (source, query)."""
    queries: List[Tuple[str, str]] = []
    seen = set()

    for t in topics:
        base = sanitize_search_query(str(t).strip())
        if not base:
            continue
        for q in [base, f"{base} -is:retweet", f'"{base}" -is:retweet']:
            key = q.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            queries.append(("topic", q))

    for h in INFLUENCERS[:5]:
        q = sanitize_search_query(f"@{h} -is:retweet")
        if not q:
            continue
        key = q.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        queries.append(("influencer", q))

    return queries


def _discover_topics(user_topics: str) -> List[str]:
    if user_topics.strip():
        return [x.strip() for x in user_topics.split(",") if x.strip()]

    rotated = get_trending_topics(limit=6)
    if rotated:
        return rotated
    return SEARCH_QUERIES[:6] if SEARCH_QUERIES else ["#ai", "#iosdev", "#swiftui", "#vibecoding"]


def _print_section(title: str, rows: List[Dict], top_n: int) -> None:
    logger.info("")
    logger.info(title)
    logger.info("-" * len(title))
    if not rows:
        logger.info("No candidates")
        return

    for idx, t in enumerate(rows[:top_n], 1):
        author = t.get("author_info", {}) or {}
        username = author.get("username", "unknown")
        followers = int(author.get("followers_count", 0) or 0)
        engagement = _weighted_engagement(t.get("public_metrics", {}) or {})
        score = t.get("manual_score", 0)
        tid = t.get("id")
        url = f"https://x.com/{username}/status/{tid}" if tid else "N/A"
        text = (t.get("text", "") or "").replace("\n", " ").strip()
        if len(text) > 140:
            text = f"{text[:137]}..."

        logger.info(
            f"{idx:02d}. @{username} | followers={followers} | engagement={engagement} | score={score} | {url}"
        )
        logger.info(f"    {text}")


def run_manual_research() -> int:
    args = _parse_args()
    per_query = min(100, max(10, args.per_query))
    top_n = max(1, args.top)

    logger.info("=" * 60)
    logger.info("🔎 MANUAL RESEARCH MODE (read-only, no posting)")
    logger.info("=" * 60)

    topics = _discover_topics(args.topics)
    logger.info(f"Topics: {topics}")
    queries = _build_queries(topics)
    logger.info(f"Query plan: {len(queries)} queries (per_query={per_query})")

    raw: List[Dict] = []
    for source, query in queries:
        tweets = tweet_handler.search_tweets(query, max_results=per_query)
        if not tweets:
            continue
        for t in tweets:
            tweet = dict(t)
            tweet["research_source"] = source
            tweet["research_query"] = query
            raw.append(tweet)

    if not raw:
        logger.warning("No tweets found in manual research.")
        return 0

    deduped: List[Dict] = []
    seen_ids = set()
    for t in raw:
        tid = str(t.get("id", "")).strip()
        if not tid or tid in seen_ids:
            continue
        seen_ids.add(tid)
        deduped.append(t)

    scored: List[Dict] = []
    for t in deduped:
        score = _candidate_score(t)
        if score <= 0:
            continue
        t["manual_score"] = score
        scored.append(t)

    scored.sort(
        key=lambda x: (
            x.get("manual_score", 0.0),
            _weighted_engagement(x.get("public_metrics", {}) or {}),
            (x.get("author_info", {}) or {}).get("followers_count", 0),
        ),
        reverse=True,
    )

    big_accounts: List[Dict] = []
    rising_accounts: List[Dict] = []
    for t in scored:
        author = t.get("author_info", {}) or {}
        followers = int(author.get("followers_count", 0) or 0)
        engagement = _weighted_engagement(t.get("public_metrics", {}) or {})
        if followers >= args.min_big_followers and engagement >= args.min_big_engagement:
            big_accounts.append(t)
        else:
            rising_accounts.append(t)

    _print_section("BIG ACCOUNT CANDIDATES", big_accounts, top_n)
    _print_section("RISING ACCOUNT CANDIDATES", rising_accounts, top_n)

    logger.info("")
    logger.info(
        f"Summary: raw={len(raw)} deduped={len(deduped)} real_scored={len(scored)} "
        f"big={len(big_accounts)} rising={len(rising_accounts)}"
    )

    if args.save_db:
        now = datetime.utcnow()
        docs = []
        for t in (big_accounts[:top_n] + rising_accounts[:top_n]):
            author = t.get("author_info", {}) or {}
            docs.append(
                {
                    "action": "manual_research_candidate",
                    "target_id": str(t.get("id", "")),
                    "target_type": "tweet",
                    "target_user": author.get("username", "unknown"),
                    "target_user_id": str(t.get("author_id", "")),
                    "timestamp": now,
                    "success": True,
                    "metadata": {
                        "score": t.get("manual_score", 0),
                        "followers": author.get("followers_count", 0),
                        "engagement": _weighted_engagement(t.get("public_metrics", {}) or {}),
                        "query": t.get("research_query", ""),
                    },
                }
            )
        if docs:
            db.activity_logs.insert_many(docs)
            logger.info(f"Saved {len(docs)} research candidates into activity_logs")

    logger.info("=" * 60)
    return len(scored)


def main() -> None:
    try:
        Config.validate()
        db.connect()
        run_manual_research()
    finally:
        if db.client:
            db.disconnect()


if __name__ == "__main__":
    main()
