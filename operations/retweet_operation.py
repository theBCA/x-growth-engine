from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from utils.rate_limiter import RateLimiter
from utils.sanitizer import sanitize_search_query
from operations.interaction_policy import can_engage_user, has_recent_any_engagement
from config import Config
from datetime import datetime
import time
import random


def retweet_high_engagement(query: str, count: int = 30, min_engagement: int = 50) -> int:
    """Retweet high engagement tweets and save to database."""
    # Sanitize query
    query = sanitize_search_query(query)
    if not query:
        logger.warning("Empty or invalid search query")
        return 0

    # Avoid search API calls when the daily retweet budget is exhausted.
    if not RateLimiter.check_limit("retweets", Config.MAX_RETWEETS_PER_DAY):
        logger.info("Skipping retweet search - retweet limit reached")
        return 0
    
    # X API requires max_results between 10 and 100.
    search_count = min(100, max(10, count * 5))
    tweets = tweet_handler.search_tweets(query, max_results=search_count)
    if not tweets:
        logger.warning(f"No tweets found for query: {query}")
        return 0
    
    eligible = []
    for tweet in tweets:
        tweet_id = tweet['id']
        author_id = tweet.get('author_id')
        author_username = tweet.get('author_info', {}).get('username', 'unknown')
        metrics = tweet.get('public_metrics', {})
        engagement = metrics.get('like_count', 0) + metrics.get('retweet_count', 0)
        
        # Check if already retweeted
        existing = db.tweets.find_one({"tweet_id": tweet_id, "retweeted_at": {"$ne": None}})
        if existing:
            continue

        if not can_engage_user("retweet", user_id=str(author_id), username=author_username, cooldown_hours=120):
            continue
        if has_recent_any_engagement(user_id=str(author_id), username=author_username, cooldown_hours=120):
            continue

        tweet["_engagement"] = engagement
        eligible.append(tweet)

    if not eligible:
        logger.info("No eligible retweet candidates after dedupe/cooldown checks")
        return 0

    eligible.sort(key=lambda t: t.get("_engagement", 0), reverse=True)
    selected = [t for t in eligible if t.get("_engagement", 0) >= min_engagement]

    # Keep "big tweet" intent, but avoid always returning 0 in niche searches.
    if len(selected) < count:
        adaptive_floor = max(25, min_engagement // 2)
        adaptive = [t for t in eligible if t.get("_engagement", 0) >= adaptive_floor and t not in selected]
        selected.extend(adaptive)

    selected = selected[:max(1, count)]
    success_count = 0
    for tweet in selected:
        # Check rate limit before each retweet
        if not RateLimiter.check_limit("retweets", Config.MAX_RETWEETS_PER_DAY):
            logger.warning(f"Daily retweet limit reached ({Config.MAX_RETWEETS_PER_DAY})")
            break

        tweet_id = tweet['id']
        author_id = tweet.get('author_id')
        author_username = tweet.get('author_info', {}).get('username', 'unknown')
        metrics = tweet.get('public_metrics', {})
        engagement = tweet.get("_engagement", 0)

        if tweet_handler.retweet(tweet_id):
            # Increment rate limiter
            RateLimiter.increment("retweets", Config.MAX_RETWEETS_PER_DAY)
            
            success_count += 1
            
            # Save to database
            db.tweets.update_one(
                {"tweet_id": tweet_id},
                {
                    "$set": {
                        "tweet_id": tweet_id,
                        "author_id": author_id,
                        "author_username": author_username,
                        "text": tweet.get('text'),
                        "likes": metrics.get('like_count', 0),
                        "retweets": metrics.get('retweet_count', 0),
                        "replies": metrics.get('reply_count', 0),
                        "engagement_score": engagement,
                        "created_at": tweet.get('created_at'),
                        "retweeted_at": datetime.utcnow(),
                        "search_query": query
                    }
                },
                upsert=True
            )
            
            # Log activity
            db.activity_logs.insert_one({
                "action": "retweet",
                "target_id": tweet_id,
                "target_type": "tweet",
                "target_user": author_username,
                "target_user_id": str(author_id),
                "timestamp": datetime.utcnow(),
                "success": True,
                "metadata": {"query": query, "engagement": engagement}
            })
            
            if success_count >= count:
                break

            # Random delay
            delay = random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
            time.sleep(delay)
    
    logger.info(f"✓ Retweeted {success_count} high-engagement tweets")
    return success_count
