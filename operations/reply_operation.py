from tweet_handler import tweet_handler
from utils.logger import logger
from utils.rate_limiter import RateLimiter
from utils.sanitizer import sanitize_search_query, validate_tweet_text
from config import Config
from operations.engagement_filters import select_diverse_real_tweets
from operations.interaction_policy import can_reply_to_user
from database import db
from datetime import datetime
import random
import time


def reply_to_relevant_tweets(query: str, reply_template: str, count: int = 10) -> int:
    """Find and reply to relevant tweets from diverse, real-looking accounts."""
    # Sanitize query
    query = sanitize_search_query(query)
    if not query:
        logger.warning("Empty or invalid search query")
        return 0
    
    # Validate reply template
    is_valid, message = validate_tweet_text(reply_template)
    if not is_valid:
        logger.warning(f"Invalid reply template: {message}")
        return 0
    
    search_count = min(100, max(20, count * 8))
    tweets = tweet_handler.search_tweets(query, max_results=search_count)
    if not tweets:
        logger.warning(f"No tweets found for query: {query}")
        return 0

    selected, bucket_counts, candidate_count = select_diverse_real_tweets(
        tweets=tweets,
        target_count=count,
        account_username=Config.ACCOUNT_USERNAME
    )
    if not selected:
        logger.warning("No high-confidence real accounts found for replies")
        return 0

    our_user = tweet_handler.api.verify_credentials()
    our_user_id = str(our_user.id)

    success_count = 0
    for tweet in selected:
        # Check rate limit before each reply
        if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
            logger.warning(f"Daily reply limit reached ({Config.MAX_REPLIES_PER_DAY})")
            break

        tweet_id = tweet.get('id')
        author_id = tweet.get('author_id')

        # Skip if it's our own tweet
        if str(author_id) == our_user_id:
            continue
        if not can_reply_to_user(str(author_id), tweet.get('author_info', {}).get('username', '')):
            continue

        author_username = tweet.get('author_info', {}).get('username', '')
        reply_text = reply_template.replace("{username}", author_username)
        is_valid, _ = validate_tweet_text(reply_text)
        if not is_valid:
            continue

        if tweet_handler.reply_to_tweet(tweet_id, reply_text):
            # Increment rate limiter
            RateLimiter.increment("replies", Config.MAX_REPLIES_PER_DAY)
            success_count += 1

            try:
                db.activity_logs.insert_one({
                    "action": "reply",
                    "target_id": tweet_id,
                    "target_type": "tweet",
                    "target_user": author_username,
                    "target_user_id": str(author_id),
                    "timestamp": datetime.utcnow(),
                    "success": True,
                    "metadata": {
                        "query": query,
                        "authenticity_score": tweet.get("authenticity_score", 0),
                        "bucket": tweet.get("followers_bucket", "mid")
                    }
                })
            except Exception:
                pass

            delay = random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
            time.sleep(delay)

    logger.info(
        f"✓ Replied to {success_count}/{count} tweets "
        f"(real_candidates={candidate_count}, buckets={bucket_counts})"
    )
    return success_count
