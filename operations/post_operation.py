from tweet_handler import tweet_handler
from utils.logger import logger
from utils.rate_limiter import RateLimiter
from utils.sanitizer import validate_tweet_text, sanitize_tweet_id
from config import Config


def post_tweet(text: str) -> bool:
    """Post a new tweet."""
    # Validate tweet text
    is_valid, message = validate_tweet_text(text)
    if not is_valid:
        logger.warning(f"Invalid tweet text: {message}")
        return False
    
    # Check rate limit
    if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
        logger.warning(f"Daily post limit reached ({Config.MAX_POSTS_PER_DAY})")
        return False
    
    tweet_id = tweet_handler.post_tweet(text)
    if tweet_id:
        # Increment rate limiter
        RateLimiter.increment("posts", Config.MAX_POSTS_PER_DAY)
        
        logger.info(f"✓ Posted tweet successfully")
        return True
    return False


def reply_to_tweet(tweet_id: str, reply_text: str) -> bool:
    """Reply to a specific tweet."""
    # Sanitize tweet ID
    tweet_id = sanitize_tweet_id(tweet_id)
    if not tweet_id:
        logger.warning("Invalid tweet ID")
        return False
    
    # Validate reply text
    is_valid, message = validate_tweet_text(reply_text)
    if not is_valid:
        logger.warning(f"Invalid reply text: {message}")
        return False
    
    # Check rate limit
    if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
        logger.warning(f"Daily reply limit reached ({Config.MAX_REPLIES_PER_DAY})")
        return False
    
    success = tweet_handler.reply_to_tweet(tweet_id, reply_text)
    if success:
        # Increment rate limiter
        RateLimiter.increment("replies", Config.MAX_REPLIES_PER_DAY)
        
        logger.info(f"✓ Replied to tweet {tweet_id}")
    return success
