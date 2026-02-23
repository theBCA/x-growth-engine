from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from utils.rate_limiter import RateLimiter
from utils.sanitizer import sanitize_search_query
from operations.interaction_policy import can_engage_user
from config import Config
from datetime import datetime
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


def calculate_follow_worthiness_score(author_info: dict, tweet_metrics: dict) -> float:
    """Calculate how worthy an account is to follow (0-100)."""
    if not author_info:
        return 0.0
    
    score = 0.0
    
    # Verified accounts get bonus
    if author_info.get('verified', False):
        score += 25
    
    # Follower count (max 25 points) - sweet spot is 1k-100k
    followers = author_info.get('followers_count', 0)
    if 1000 <= followers <= 100000:
        score += 25
    elif 100 <= followers < 1000:
        score += 20
    elif followers > 100000:
        score += 15  # Very large accounts less likely to follow back
    elif followers > 50:
        score += 10
    
    # Following ratio (max 20 points) - healthy ratio important
    following = author_info.get('following_count', 0)
    if following > 0:
        ratio = followers / following
        if 0.5 <= ratio <= 2.0:  # Balanced ratio
            score += 20
        elif 0.2 <= ratio < 0.5 or 2.0 < ratio <= 5.0:
            score += 15
        elif ratio > 0.1:
            score += 10
    
    # Account age (max 15 points) - prefer established accounts
    account_age_days = author_info.get('account_age_days', 0)
    if account_age_days > 365:
        score += 15
    elif account_age_days > 180:
        score += 12
    elif account_age_days > 90:
        score += 8
    elif account_age_days > 30:
        score += 5
    
    # Tweet engagement (max 15 points)
    likes = tweet_metrics.get('like_count', 0)
    retweets = tweet_metrics.get('retweet_count', 0)
    engagement = likes + (retweets * 2)
    if engagement > 100:
        score += 15
    elif engagement > 50:
        score += 12
    elif engagement > 10:
        score += 8
    elif engagement > 0:
        score += 4
    
    return min(score, 100.0)


def follow_relevant_users(query: str, count: int = 50) -> int:
    """Follow users tweeting about relevant topics and save to database.
    
    Improvements:
    - Filter out likely bot accounts
    - Prioritize high-engagement real accounts
    - Score accounts based on follow-worthiness
    """
    # Sanitize query
    query = sanitize_search_query(query)
    if not query:
        logger.warning("Empty or invalid search query")
        return 0
    
    tweets = tweet_handler.search_tweets(query, max_results=count)
    if not tweets:
        logger.warning(f"No tweets found for query: {query}")
        return 0
    
    # Build list of unique users with scores
    user_scores = {}
    for tweet in tweets:
        author_id = tweet.get('author_id')
        if not author_id or author_id in user_scores:
            continue
        
        author_info = tweet.get('author_info', {})
        
        # Skip if likely a bot
        if is_likely_bot(author_info):
            logger.debug(f"Skipping likely bot account: {author_info.get('username', 'unknown')}")
            continue
        
        # Calculate follow-worthiness score
        score = calculate_follow_worthiness_score(
            author_info,
            tweet.get('public_metrics', {})
        )
        
        # Only consider accounts above threshold
        if score < 30:  # Minimum follow threshold
            logger.debug(f"Low follow score ({score}) for {author_info.get('username', 'unknown')}, skipping")
            continue
        
        user_scores[author_id] = {
            'score': score,
            'username': author_info.get('username', 'unknown'),
            'author_info': author_info,
            'source_tweet_id': tweet.get('id')
        }
    
    # Sort users by score (highest first)
    sorted_users = sorted(user_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    
    logger.info(f"Filtered {len(sorted_users)}/{len(tweets)} users (removed bots and low-quality accounts)")
    
    success_count = 0
    for author_id, user_data in sorted_users:
        # Check rate limit before each follow
        if not RateLimiter.check_limit("follows", Config.MAX_FOLLOWS_PER_DAY):
            logger.warning(f"Daily follow limit reached ({Config.MAX_FOLLOWS_PER_DAY})")
            break
        
        # Check if already following
        existing = db.users.find_one({"user_id": author_id, "unfollowed_at": None})
        if existing:
            continue

        username = user_data['username']
        if not can_engage_user("follow", user_id=str(author_id), username=username, cooldown_hours=168):
            continue
        
        if tweet_handler.follow_user(author_id):
            # Increment rate limiter
            RateLimiter.increment("follows", Config.MAX_FOLLOWS_PER_DAY)
            
            success_count += 1
            
            author_info = user_data['author_info']
            
            # Save to database
            db.users.insert_one({
                "user_id": author_id,
                "username": user_data['username'],
                "followers_count": author_info.get('followers_count', 0),
                "following_count": author_info.get('following_count', 0),
                "follow_score": user_data['score'],
                "followed_at": datetime.utcnow(),
                "followed_back": False,
                "source_query": query,
                "source_tweet_id": user_data['source_tweet_id']
            })
            
            # Log activity
            db.activity_logs.insert_one({
                "action": "follow",
                "target_id": author_id,
                "target_type": "user",
                "target_user": username,
                "target_user_id": str(author_id),
                "timestamp": datetime.utcnow(),
                "success": True,
                "metadata": {
                    "query": query,
                    "follow_score": user_data['score'],
                    "followers": author_info.get('followers_count', 0)
                }
            })
            
            logger.info(f"✓ Followed @{user_data['username']} (score: {user_data['score']:.1f}, followers: {author_info.get('followers_count', 0)})")
            
            # Random delay
            delay = random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
            time.sleep(delay)
    
    logger.info(f"✓ Followed {success_count}/{len(sorted_users)} high-quality users")
    return success_count
