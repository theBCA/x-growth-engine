"""Topic and keyword configuration (niche-agnostic, env-driven)."""
import os


def _split_csv(value: str) -> list:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


DEFAULT_TOPICS = [
    "artificial intelligence",
    "software engineering",
    "startup growth",
    "product management",
    "cloud architecture",
]

DEFAULT_QUERIES = [
    "#ai",
    "#programming",
    "#softwareengineering",
    "#productivity",
    "#startups",
]

DEFAULT_INFLUENCERS = [
    "sama",
    "paulg",
    "levelsio",
    "ycombinator",
    "naval",
]

TOPICS_LIST = _split_csv(os.getenv("BOT_TOPICS", ",".join(DEFAULT_TOPICS)))
SEARCH_QUERIES = _split_csv(os.getenv("BOT_SEARCH_QUERIES", ",".join(DEFAULT_QUERIES)))
INFLUENCERS = _split_csv(os.getenv("BOT_INFLUENCERS", ",".join(DEFAULT_INFLUENCERS)))

# Optional grouped map for UI/reporting compatibility.
TOPICS = {"primary": TOPICS_LIST}

# Generic templates; can be overridden by env.
DEFAULT_REPLY_TEMPLATES = [
    "Interesting angle. What metric would you watch first?",
    "Good point. What tradeoff matters most here?",
    "Useful take. How would you test this in a small rollout?",
    "I like this perspective. What outcome would define success?",
    "Solid insight. Which part is highest risk in practice?",
]
REPLY_TEMPLATES = _split_csv(
    os.getenv("BOT_REPLY_TEMPLATES", ",".join(DEFAULT_REPLY_TEMPLATES))
)
