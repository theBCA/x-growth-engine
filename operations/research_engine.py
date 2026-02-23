"""Research layer for gathering and normalizing conversation candidates."""
from typing import List, Dict, Any

from tweet_handler import tweet_handler
from utils.logger import logger
from utils.sanitizer import sanitize_search_query
from operations.quality_scorer import score_candidate_value
from config import Config


def _query_variants(topic: str) -> List[str]:
    base = sanitize_search_query(topic or "")
    if not base:
        return []

    variants = [base, f"{base} -is:retweet", f'"{base}" -is:retweet']

    deduped = []
    seen = set()
    for q in variants:
        cleaned = sanitize_search_query(q).strip()
        if cleaned and cleaned not in seen:
            deduped.append(cleaned)
            seen.add(cleaned)
    return deduped[:max(1, Config.MAX_RESEARCH_QUERIES)]


def collect_research_candidates(topic: str, max_candidates: int = 80) -> List[Dict[str, Any]]:
    """Collect, dedupe, and score candidate tweets for engagement."""
    variants = _query_variants(topic)
    if not variants:
        return []

    per_query = max(10, min(Config.MAX_RESULTS_PER_RESEARCH_QUERY, max_candidates // max(1, len(variants))))
    raw: List[Dict[str, Any]] = []

    for q in variants:
        tweets = tweet_handler.search_tweets(q, max_results=per_query)
        if tweets:
            for t in tweets:
                t = dict(t)
                t["research_query"] = q
                raw.append(t)

    if not raw:
        return []

    deduped = []
    seen_tweet_ids = set()
    for t in raw:
        tid = str(t.get("id", ""))
        if not tid or tid in seen_tweet_ids:
            continue
        seen_tweet_ids.add(tid)
        deduped.append(t)

    for t in deduped:
        t["candidate_score"] = score_candidate_value(t)

    deduped.sort(key=lambda x: x.get("candidate_score", 0), reverse=True)
    selected = [t for t in deduped if t.get("candidate_score", 0) >= 40][:max_candidates]
    logger.info(
        f"Research: topic='{topic}' variants={len(variants)} raw={len(raw)} deduped={len(deduped)} selected={len(selected)}"
    )
    return selected
