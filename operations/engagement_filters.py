"""Shared filters for selecting diverse, real-looking accounts for engagement."""
from typing import Dict, List, Optional, Set, Tuple


def followers_bucket(followers: int) -> str:
    """Group accounts by follower size for diversity balancing."""
    if followers < 500:
        return "small"
    if followers < 5000:
        return "mid"
    return "large"


def evaluate_account_authenticity(author_info: dict, tweet_metrics: dict) -> Tuple[bool, float]:
    """Score account authenticity and return (is_real_enough, score)."""
    if not author_info:
        return False, 0.0

    followers = author_info.get("followers_count", 0)
    following = author_info.get("following_count", 0)
    tweet_count = author_info.get("tweet_count", 0)
    account_age_days = author_info.get("account_age_days", 0)
    description = (author_info.get("description", "") or "").strip()
    username = author_info.get("username", "") or ""

    # Hard filters for obvious low-quality or bot-like profiles.
    if account_age_days < 30:
        return False, 0.0
    if followers < 10:
        return False, 0.0
    if following > 15000:
        return False, 0.0
    if tweet_count < 20:
        return False, 0.0
    if len(description) < 8:
        return False, 0.0

    score = 0.0

    if account_age_days > 365:
        score += 20
    elif account_age_days > 180:
        score += 14
    else:
        score += 8

    if following > 0:
        ratio = followers / following
        if 0.2 <= ratio <= 5:
            score += 20
        elif 0.1 <= ratio <= 10:
            score += 12
        else:
            score += 3

    tweets_per_day = tweet_count / max(account_age_days, 1)
    if tweets_per_day <= 12:
        score += 15
    elif tweets_per_day <= 30:
        score += 8
    else:
        score += 1

    if len(description) >= 40:
        score += 10
    elif len(description) >= 20:
        score += 6
    else:
        score += 3

    if author_info.get("verified", False):
        score += 8

    digits_ratio = sum(ch.isdigit() for ch in username) / max(len(username), 1)
    if digits_ratio < 0.2:
        score += 5

    likes = tweet_metrics.get("like_count", 0)
    retweets = tweet_metrics.get("retweet_count", 0)
    replies = tweet_metrics.get("reply_count", 0)
    engagement = likes + (retweets * 2) + (replies * 2)
    if engagement >= 20:
        score += 12
    elif engagement >= 5:
        score += 8
    elif engagement >= 1:
        score += 4

    return score >= 40, score


def select_diverse_real_tweets(
    tweets: List[dict],
    target_count: int,
    account_username: str = "",
    excluded_usernames: Optional[Set[str]] = None
) -> Tuple[List[dict], Dict[str, int], int]:
    """Filter to real-looking accounts and pick a diverse set by follower bucket."""
    excluded_lower = {u.lower() for u in (excluded_usernames or set()) if u}
    seen_authors = set()
    candidates = []

    for tweet in tweets:
        author_info = tweet.get("author_info", {})
        author_username = (author_info.get("username", "") or "").strip()
        author_id = tweet.get("author_id")

        if not author_username:
            continue
        if account_username and author_username.lower() == account_username.lower():
            continue
        if author_username.lower() in excluded_lower:
            continue

        author_key = str(author_id) if author_id else author_username.lower()
        if author_key in seen_authors:
            continue
        seen_authors.add(author_key)

        is_real, score = evaluate_account_authenticity(
            author_info,
            tweet.get("public_metrics", {})
        )
        if not is_real:
            continue

        enriched = dict(tweet)
        followers = author_info.get("followers_count", 0)
        enriched["authenticity_score"] = score
        enriched["followers_bucket"] = followers_bucket(followers)
        candidates.append(enriched)

    candidates.sort(
        key=lambda t: (
            t.get("authenticity_score", 0),
            t.get("public_metrics", {}).get("like_count", 0),
            t.get("public_metrics", {}).get("reply_count", 0),
        ),
        reverse=True
    )

    selected = []
    seen_content = set()
    bucket_counts = {"small": 0, "mid": 0, "large": 0}
    bucket_limit = max(1, target_count // 2)

    for tweet in candidates:
        if len(selected) >= target_count:
            break

        bucket = tweet.get("followers_bucket", "mid")
        if bucket_counts.get(bucket, 0) >= bucket_limit and len(selected) < target_count - 1:
            continue

        text = tweet.get("text", "")
        fingerprint = text[:50].lower().strip()
        if fingerprint and fingerprint in seen_content:
            continue

        if fingerprint:
            seen_content.add(fingerprint)
        selected.append(tweet)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    return selected, bucket_counts, len(candidates)
