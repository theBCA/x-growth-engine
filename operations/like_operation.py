from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from utils.rate_limiter import RateLimiter
from utils.sanitizer import sanitize_search_query
from operations.interaction_policy import can_engage_user, has_recent_any_engagement
from config import Config
from datetime import datetime, timedelta
import time
import random


def is_likely_bot(author_info: dict) -> bool:
    """Detect if an account is likely a bot based on various signals."""
    if not author_info:
        return True
    
    followers = author_info.get('followers_count', 0)
    following = author_info.get('following_count', 0)
    tweet_count = author_info.get('tweet_count', 0)
    account_age_days = author_info.get('account_age_days', 0)
    description = author_info.get('description', '')
    
    # Bot indicators
    bot_signals = 0
    
    # 1. Suspicious follower/following ratio
    if following > 0:
        ratio = followers / following
        if ratio < 0.1 and followers < 100:  # Following way more than followers
            bot_signals += 2
    
    # 2. Very new account with high activity
    if account_age_days < 30 and tweet_count > 1000:
        bot_signals += 2
    
    # 3. Very high tweet frequency
    if account_age_days > 0:
        tweets_per_day = tweet_count / account_age_days
        if tweets_per_day > 50:  # More than 50 tweets per day
            bot_signals += 1
    
    # 4. No profile description
    if not description or len(description) < 10:
        bot_signals += 1
    
    # 5. Suspicious following count (too many)
    if following > 5000 and followers < 100:
        bot_signals += 2
    
    # 6. Very low engagement despite high tweet count
    if tweet_count > 500 and followers < 10:
        bot_signals += 1
    
    return bot_signals >= 3


def calculate_account_quality_score(author_info: dict, tweet_metrics: dict) -> float:
    """Calculate quality score for an account (0-100)."""
    if not author_info:
        return 0.0
    
    score = 0.0
    
    # Verified accounts get bonus
    if author_info.get('verified', False):
        score += 30
    
    # Follower count (max 20 points)
    followers = author_info.get('followers_count', 0)
    if followers > 10000:
        score += 20
    elif followers > 1000:
        score += 15
    elif followers > 100:
        score += 10
    elif followers > 10:
        score += 5
    
    # Account age (max 15 points)
    account_age_days = author_info.get('account_age_days', 0)
    if account_age_days > 365:
        score += 15
    elif account_age_days > 180:
        score += 10
    elif account_age_days > 30:
        score += 5
    
    # Engagement on tweet (max 20 points)
    likes = tweet_metrics.get('like_count', 0)
    retweets = tweet_metrics.get('retweet_count', 0)
    engagement = likes + (retweets * 2)
    if engagement > 100:
        score += 20
    elif engagement > 50:
        score += 15
    elif engagement > 10:
        score += 10
    elif engagement > 0:
        score += 5
    
    # Profile completeness (max 15 points)
    description = author_info.get('description', '')
    if len(description) > 50:
        score += 15
    elif len(description) > 20:
        score += 10
    elif len(description) > 0:
        score += 5
    
    return min(score, 100.0)


def like_relevant_tweets(query: str, count: int = 50) -> int:
    """Like relevant tweets based on search query and save to database.
    
    Improvements:
    - Avoid liking multiple tweets from the same account
    - Filter out likely bot accounts
    - Prioritize high-engagement real accounts
    """
    # Sanitize query
    query = sanitize_search_query(query)
    if not query:
        logger.warning("Empty or invalid search query")
        return 0

    # Avoid search API calls when the daily like budget is already exhausted.
    if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
        logger.info("Skipping like search - like limit reached")
        return 0
    
    # X API search_recent_tweets requires max_results in [10, 100].
    search_count = min(100, max(10, count * 5))
    tweets = tweet_handler.search_tweets(query, max_results=search_count)
    if not tweets:
        logger.warning(f"No tweets found for query: {query}")
        return 0
    
    # Filter and score tweets
    filtered_tweets = []
    liked_authors = set()  # Track authors we've already liked in this session
    
    for tweet in tweets:
        author_id = tweet.get('author_id')
        author_info = tweet.get('author_info', {})
        author_username = author_info.get('username', 'unknown')
        
        # Skip if we already liked a tweet from this author in this session
        if author_id in liked_authors:
            logger.debug(f"Already liked a tweet from author {author_id} in this session, skipping")
            continue
        
        # Skip if likely a bot
        if is_likely_bot(author_info):
            logger.debug(f"Skipping likely bot account: {author_info.get('username', 'unknown')}")
            continue
        
        # Calculate quality score
        quality_score = calculate_account_quality_score(
            author_info,
            tweet.get('public_metrics', {})
        )
        
        # Only proceed with accounts scoring above threshold
        if quality_score < 20:  # Minimum quality threshold
            logger.debug(f"Low quality score ({quality_score}) for {author_info.get('username', 'unknown')}, skipping")
            continue
        
        tweet['quality_score'] = quality_score
        filtered_tweets.append(tweet)
    
    # Sort by quality score (highest first)
    filtered_tweets.sort(key=lambda t: t.get('quality_score', 0), reverse=True)
    
    logger.info(f"Filtered {len(filtered_tweets)}/{len(tweets)} tweets (removed bots and low-quality accounts)")
    
    success_count = 0
    for tweet in filtered_tweets:
        if success_count >= count:
            break
        # Check rate limit before each like
        if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
            logger.warning(f"Daily like limit reached ({Config.MAX_LIKES_PER_DAY})")
            break
        
        tweet_id = tweet['id']
        author_id = tweet.get('author_id')
        author_info = tweet.get('author_info', {})
        
        # Check if already liked this tweet
        existing = db.tweets.find_one({"tweet_id": tweet_id, "liked_at": {"$ne": None}})
        if existing:
            logger.debug(f"Tweet {tweet_id} already liked, skipping")
            continue
        
        # Check if we've recently liked tweets from this author (within last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_like = db.tweets.find_one({
            "author_id": author_id,
            "liked_at": {"$ne": None, "$gte": seven_days_ago}
        })
        if recent_like:
            logger.debug(f"Recently liked another tweet from author {author_id}, skipping")
            continue

        # Cross-action diversity: don't repeatedly engage the same user via other actions.
        if has_recent_any_engagement(user_id=str(author_id), username=author_username, cooldown_hours=96):
            continue

        if not can_engage_user("like", user_id=str(author_id), username=author_username, cooldown_hours=72):
            continue
        
        if tweet_handler.like_tweet(tweet_id):
            # Increment rate limiter
            RateLimiter.increment("likes", Config.MAX_LIKES_PER_DAY)
            
            liked_authors.add(author_id)
            success_count += 1
            
            # Save to database
            metrics = tweet.get('public_metrics', {})
            db.tweets.update_one(
                {"tweet_id": tweet_id},
                {
                    "$set": {
                        "tweet_id": tweet_id,
                        "author_id": author_id,
                        "author_username": author_info.get('username', 'unknown'),
                        "text": tweet.get('text'),
                        "likes": metrics.get('like_count', 0),
                        "retweets": metrics.get('retweet_count', 0),
                        "replies": metrics.get('reply_count', 0),
                        "engagement_score": metrics.get('like_count', 0) + metrics.get('retweet_count', 0),
                        "quality_score": tweet.get('quality_score', 0),
                        "created_at": tweet.get('created_at'),
                        "liked_at": datetime.utcnow(),
                        "search_query": query
                    }
                },
                upsert=True
            )
            
            # Log activity
            db.activity_logs.insert_one({
                "action": "like",
                "target_id": tweet_id,
                "target_type": "tweet",
                "target_user": author_username,
                "target_user_id": str(author_id),
                "timestamp": datetime.utcnow(),
                "success": True,
                "metadata": {
                    "query": query,
                    "author_id": author_id,
                    "quality_score": tweet.get('quality_score', 0)
                }
            })
            
            logger.info(f"✓ Liked tweet from @{author_info.get('username', 'unknown')} (quality: {tweet.get('quality_score', 0):.1f})")
            
            # Random delay
            delay = random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
            time.sleep(delay)
    
    logger.info(f"✓ Liked {success_count}/{len(filtered_tweets)} high-quality tweets")
    return success_count
