"""Helpers for generating high-value fallback content."""
import re
import random


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "your", "you",
    "about", "what", "when", "where", "which", "into", "their", "they", "will",
    "would", "could", "should", "there", "here", "just", "more", "than", "then",
    "been", "being", "over", "under", "after", "before", "while", "through",
    "how", "why", "who", "are", "was", "were", "has", "had", "did", "does",
}


def extract_focus_terms(text: str, limit: int = 2) -> list[str]:
    """Extract a couple of useful non-trivial terms from text."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{3,}", (text or "").lower())
    ranked = []
    seen = set()
    for w in words:
        if w in _STOPWORDS or w in seen:
            continue
        seen.add(w)
        ranked.append(w)
        if len(ranked) >= limit:
            break
    return ranked


def build_value_fallback_reply(tweet_text: str, author_username: str = "") -> str:
    """Create a concrete, value-focused fallback reply."""
    terms = extract_focus_terms(tweet_text, limit=2)
    focus = " and ".join(terms) if terms else "this approach"
    prefix = f"@{author_username} " if author_username else ""

    templates = [
        f"{prefix}Useful point on {focus}. What metric would you track first to validate it?",
        f"{prefix}On {focus}, one practical move is to test a small rollout first. Which part would you pilot?",
        f"{prefix}Good thread on {focus}. Biggest tradeoff seems speed vs reliability. How would you balance it?",
        f"{prefix}Strong take. For {focus}, I'd start with a checklist and one measurable outcome. What would yours be?",
    ]
    return random.choice(templates)
