"""Decision layer for selecting targets and generating best content drafts."""
import random
from typing import List, Dict, Any, Tuple, Set, Optional

from operations.ai_operation import generate_ai_reply, generate_ai_tweet
from operations.engagement_filters import followers_bucket
from operations.interaction_policy import can_reply_to_user, has_recent_any_engagement
from operations.quality_scorer import score_reply_quality, score_post_quality
from operations.value_content import build_value_fallback_reply
from utils.sanitizer import validate_tweet_text
from config import Config


def _is_low_value_reply_target(username: str, text: str) -> bool:
    """Skip aggregator/update-style accounts and machine-like text targets."""
    u = (username or "").strip().lower()
    t = (text or "").strip().lower()
    if not u:
        return True

    noisy_username_terms = [
        "updates",
        "update",
        "repo",
        "signal",
        "news",
        "alerts",
        "bot",
    ]
    if any(term in u for term in noisy_username_terms):
        return True

    # Heavy symbol/digit usernames are often low-value targets.
    digit_ratio = sum(ch.isdigit() for ch in u) / max(1, len(u))
    if digit_ratio > 0.35:
        return True

    # Skip obvious feed-like text.
    feed_terms = ["release notes", "new version", "just updated", "changelog", "patch notes"]
    if any(term in t for term in feed_terms):
        return True
    return False


def select_reply_targets(
    candidates: List[Dict[str, Any]],
    count: int,
    account_username: str = "",
    session_replied_users: Optional[Set[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Select diverse, high-score targets while honoring interaction policy."""
    session_replied_users = {
        str(u).strip().lower() for u in (session_replied_users or set()) if str(u).strip()
    }

    filtered = []
    for t in candidates:
        author = t.get("author_info", {}) or {}
        username = (author.get("username", "") or "").strip()
        user_id = str(t.get("author_id", ""))
        text = (t.get("text", "") or "").strip()

        if not username:
            continue
        if account_username and username.lower() == account_username.lower():
            continue
        if username.lower() in session_replied_users:
            continue
        if not can_reply_to_user(user_id, username):
            continue
        if has_recent_any_engagement(user_id=user_id, username=username, cooldown_hours=72):
            continue
        if _is_low_value_reply_target(username, text):
            continue
        if "http://" in text.lower() or "https://" in text.lower():
            continue
        if len(text.split()) < 8:
            continue

        t = dict(t)
        t["followers_bucket"] = followers_bucket(author.get("followers_count", 0))
        filtered.append(t)

    filtered.sort(key=lambda x: x.get("candidate_score", 0), reverse=True)

    picked = []
    buckets = {"small": 0, "mid": 0, "large": 0}
    bucket_limit = max(1, count // 2)
    seen_fingerprint = set()
    picked_users = set()

    for t in filtered:
        if len(picked) >= count:
            break
        username = (t.get("author_info", {}) or {}).get("username", "").strip().lower()
        if username and username in picked_users:
            continue
        bucket = t.get("followers_bucket", "mid")
        if buckets.get(bucket, 0) >= bucket_limit and len(picked) < count - 1:
            continue

        fp = (t.get("text", "") or "")[:60].lower()
        if fp in seen_fingerprint:
            continue
        seen_fingerprint.add(fp)

        picked.append(t)
        if username:
            picked_users.add(username)
        buckets[bucket] = buckets.get(bucket, 0) + 1

    return picked, buckets


def generate_best_reply(tweet_text: str, author_username: str) -> Optional[str]:
    """Generate multiple reply drafts and return the highest-quality one."""
    angles = ["practical", "contrasting", "supportive", "conversational", "curious", "questioning"]
    random.shuffle(angles)
    drafts = []
    draft_budget = max(1, min(4, Config.MAX_REPLY_DRAFTS))

    for angle in angles[:draft_budget]:
        # Prefer statement-like replies for more human variance.
        response_mode = "statement" if random.random() < 0.7 else "mixed"
        if angle == "questioning":
            response_mode = "question"

        draft = generate_ai_reply(tweet_text, author_username, angle=angle, response_mode=response_mode)
        if not draft:
            continue
        is_valid, _ = validate_tweet_text(draft)
        if not is_valid:
            continue
        score = score_reply_quality(draft)
        drafts.append((score, draft))

    if drafts:
        drafts.sort(key=lambda x: x[0], reverse=True)
        if drafts[0][0] >= 50:
            return drafts[0][1]

    fallback = build_value_fallback_reply(tweet_text, author_username)
    is_valid, _ = validate_tweet_text(fallback)
    return fallback if is_valid else None


def generate_best_post(topic: str, niche: Optional[str] = None) -> Optional[str]:
    """Generate multiple post drafts and return the highest-quality one."""
    niche = niche or ((Config.NICHE[0].strip() if Config.NICHE else "technology") or "technology")
    angles = ["practical", "insights", "critical", "educational", "conversational"]
    draft_budget = max(1, min(len(angles), Config.MAX_POST_DRAFTS))
    drafts = []

    for angle in angles[:draft_budget]:
        draft = generate_ai_tweet(topic, niche=niche, angle=angle)
        if not draft:
            continue
        is_valid, _ = validate_tweet_text(draft)
        if not is_valid:
            continue
        score = score_post_quality(draft)
        drafts.append((score, draft))

    if not drafts:
        return None

    drafts.sort(key=lambda x: x[0], reverse=True)
    return drafts[0][1] if drafts[0][0] >= 50 else None
