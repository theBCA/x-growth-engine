"""Content creation and posting operations for organic growth."""
from operations.ai_operation import (
    post_ai_generated_tweet,
    post_ai_thread,
    generate_ai_structured_post,
    post_text_with_continuation,
)
from utils.logger import logger
from utils.rate_limiter import RateLimiter
from config import Config
from config_topics import SEARCH_QUERIES
from database import db
from datetime import datetime


# Optimal posting times (based on Twitter engagement data)
PEAK_HOURS = [9, 13, 19]  # 9am, 1pm, 7pm (user's timezone)


def _default_niche() -> str:
    return (Config.NICHE[0].strip() if Config.NICHE else "technology") or "technology"


def should_post_now() -> bool:
    """Check if current time is optimal for posting."""
    current_hour = datetime.now().hour
    return current_hour in PEAK_HOURS


def post_daily_content(topics: list) -> int:
    """Post 2-3 AI-generated tweets per day at optimal times.
    
    Args:
        topics: List of topics to create content about
        
    Returns:
        Number of posts created
    """
    if not should_post_now():
        logger.info(f"Current hour not optimal for posting (peak hours: {PEAK_HOURS})")
        return 0
    
    # Check rate limit
    if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
        logger.warning(f"Daily post limit reached ({Config.MAX_POSTS_PER_DAY})")
        return 0
    
    posted = 0
    for topic in topics[:3]:  # Max 3 topics
        if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
            break
        
        success = post_ai_generated_tweet(
            topic=topic,
            niche=_default_niche()
        )
        
        if success:
            posted += 1
            logger.info(f"✓ Posted content about: {topic}")
    
    return posted


def post_weekly_thread(topic: str) -> int:
    """Post an educational thread once per week.
    
    Args:
        topic: Topic for the thread
        
    Returns:
        Number of tweets posted in thread
    """
    # Check if it's a good time for a thread (weekday mornings)
    now = datetime.now()
    if now.weekday() >= 5:  # Weekend
        logger.info("Skipping thread - weekend has lower engagement")
        return 0
    
    if now.hour not in [9, 10]:  # Post threads in morning
        logger.info("Skipping thread - not optimal time (best: 9-10am)")
        return 0
    
    logger.info(f"Creating educational thread about: {topic}")
    return post_ai_thread(topic)


def create_engagement_content(trending_topic: str) -> bool:
    """Create timely content based on trending topics.
    
    Args:
        trending_topic: Current trending topic in your niche
        
    Returns:
        True if post successful
    """
    if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
        return False
    
    # Create content that joins the conversation
    topic = f"Quick take on {trending_topic}"
    
    return post_ai_generated_tweet(
        topic=topic,
        niche=_default_niche()
    )


def _already_posted_today(post_type: str) -> bool:
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    existing = db.posts.find_one({
        "post_type": post_type,
        "posted_at": {"$gte": start}
    })
    return existing is not None


def _pick_daily_topic() -> str:
    if SEARCH_QUERIES:
        return SEARCH_QUERIES[datetime.utcnow().day % len(SEARCH_QUERIES)]
    return "AI-assisted iOS development workflow"


def post_daily_original_lane() -> int:
    """
    Post one structured daily original post:
    problem -> tried -> concrete result/metric -> takeaway.
    Uses ++ continuation replies automatically when too long.
    """
    if not Config.DAILY_ORIGINAL_POST_ENABLED:
        return 0
    if _already_posted_today("daily_lane"):
        logger.info("Daily lane post already published today")
        return 0

    topic = _pick_daily_topic()
    niche = _default_niche()
    structured = generate_ai_structured_post(topic=topic, niche=niche)
    if not structured:
        logger.warning("Failed to generate structured daily post")
        return 0

    return post_text_with_continuation(
        text=structured,
        topic=topic,
        niche=niche,
        post_type="daily_lane",
    )


def post_followup_from_replies() -> int:
    """
    Turn successful reply threads into one follow-up post on own profile.
    """
    if not Config.FOLLOWUP_POST_ENABLED:
        return 0
    if _already_posted_today("followup"):
        logger.info("Follow-up post already published today")
        return 0

    since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    replies = list(db.activity_logs.find({
        "action": "reply",
        "success": True,
        "timestamp": {"$gte": since}
    }).sort("timestamp", -1).limit(20))
    if len(replies) < 3:
        logger.info("Not enough reply signal for follow-up post")
        return 0

    topics = [r.get("metadata", {}).get("safe_query") or r.get("metadata", {}).get("trend") for r in replies]
    topics = [t for t in topics if t]
    if not topics:
        return 0

    # Most common recent discussion angle.
    pivot = max(set(topics), key=topics.count)
    followup_topic = f"What I learned today from replying about {pivot}"
    niche = _default_niche()
    structured = generate_ai_structured_post(topic=followup_topic, niche=niche)
    if not structured:
        return 0

    return post_text_with_continuation(
        text=structured,
        topic=followup_topic,
        niche=niche,
        post_type="followup",
    )
