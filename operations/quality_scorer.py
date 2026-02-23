"""Scoring utilities for conversation and content quality."""
from typing import Dict, Any

from operations.engagement_filters import evaluate_account_authenticity


def score_candidate_value(tweet: Dict[str, Any]) -> float:
    """Score a tweet candidate for reply-worthiness (0-100)."""
    text = (tweet.get("text", "") or "").strip()
    metrics = tweet.get("public_metrics", {}) or {}
    author_info = tweet.get("author_info", {}) or {}

    if not text:
        return 0.0

    is_real, account_score = evaluate_account_authenticity(author_info, metrics)
    if not is_real:
        return 0.0

    score = account_score * 0.6

    likes = metrics.get("like_count", 0)
    retweets = metrics.get("retweet_count", 0)
    replies = metrics.get("reply_count", 0)
    engagement = likes + (retweets * 2) + (replies * 2)

    if engagement >= 80:
        score += 20
    elif engagement >= 25:
        score += 14
    elif engagement >= 8:
        score += 9
    elif engagement >= 1:
        score += 4

    # Prefer conversational text over link dumps/low-context lines.
    lowered = text.lower()
    if "http://" in lowered or "https://" in lowered:
        score -= 20
    elif len(text.split()) >= 12:
        score += 8
    elif len(text.split()) >= 8:
        score += 4
    else:
        score -= 10

    return max(0.0, min(100.0, score))


def score_reply_quality(reply_text: str) -> float:
    """Score reply usefulness (0-100)."""
    if not reply_text:
        return 0.0

    text = reply_text.strip().lower()
    score = 0.0

    # Basic structure/value signals.
    if "?" in text:
        score += 8
    # Reward useful declarative statements.
    if any(k in text for k in ["one practical move", "in practice", "you can", "i'd start with", "the key is"]):
        score += 16
    if any(k in text for k in ["metric", "tradeoff", "risk", "test", "pilot", "measure", "outcome"]):
        score += 25
    if any(k in text for k in ["next step", "would you", "how would", "which part"]):
        score += 18

    word_count = len(text.split())
    if 10 <= word_count <= 30:
        score += 20
    elif 6 <= word_count < 10:
        score += 10

    generic = ["great point", "totally agree", "thanks for sharing", "nice post"]
    if any(g in text for g in generic):
        score -= 30

    return max(0.0, min(100.0, score))


def score_post_quality(post_text: str) -> float:
    """Score post usefulness (0-100)."""
    if not post_text:
        return 0.0

    text = post_text.strip().lower()
    score = 0.0

    if any(k in text for k in ["how to", "checklist", "framework", "metric", "tradeoff", "risk"]):
        score += 30
    if any(k in text for k in ["for example", "e.g.", "start with", "first step"]):
        score += 25
    if any(k in text for k in ["?"]):
        score += 8

    wc = len(text.split())
    if 18 <= wc <= 45:
        score += 20
    elif 10 <= wc < 18:
        score += 12

    generic = ["gm", "good morning", "just sharing", "random thought"]
    if any(g in text for g in generic):
        score -= 20

    return max(0.0, min(100.0, score))
