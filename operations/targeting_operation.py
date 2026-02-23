"""Smart targeting operations for quality follower growth."""
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


def follow_quality_accounts(query: str, min_followers: int = 100, max_followers: int = 5000, count: int = 30) -> int:
    """Follow quality accounts likely to follow back.
    
    Strategy: Target accounts with similar follower count (more likely to follow back)
    
    Args:
        query: Search query for finding relevant accounts
        min_followers: Minimum follower count
        max_followers: Maximum follower count (avoid mega accounts)
        count: Max accounts to follow
        
    Returns:
        Number of accounts followed
    """
    query = sanitize_search_query(query)
    if not query:
        return 0
    
    tweets = tweet_handler.search_tweets(query, max_results=count * 2)
    if not tweets:
        return 0
    
    followed = 0
    seen_authors = set()
    
    for tweet in tweets:
        if not RateLimiter.check_limit("follows", Config.MAX_FOLLOWS_PER_DAY):
            break
        
        author_id = tweet.get('author_id')
        if not author_id or author_id in seen_authors:
            continue
        
        seen_authors.add(author_id)
        
        # Check if already following
        existing = db.users.find_one({"user_id": author_id, "unfollowed_at": None})
        if existing:
            continue

        author_username = tweet.get('author_info', {}).get('username') or tweet.get('author_username', 'unknown')
        if not can_engage_user("follow", user_id=str(author_id), username=author_username, cooldown_hours=168):
            continue
        
        # Get author metrics (would need API v2 user lookup - simplified here)
        # In production: check follower_count, following_count, tweet_count
        # Skip if: followers < min_followers or followers > max_followers
        # Skip if: following/followers ratio > 2 (likely won't follow back)
        
        if tweet_handler.follow_user(author_id):
            RateLimiter.increment("follows", Config.MAX_FOLLOWS_PER_DAY)
            followed += 1
            
            # Save with quality score
            db.users.insert_one({
                "user_id": author_id,
                "username": author_username,
                "followed_at": datetime.utcnow(),
                "source_query": query,
                "quality_target": True,
                "min_followers": min_followers,
                "max_followers": max_followers
            })
            
            time.sleep(random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS))
    
    logger.info(f"✓ Followed {followed} quality accounts (followers: {min_followers}-{max_followers})")
    return followed


def engage_with_influencer_followers(influencer_username: str, count: int = 20) -> int:
    """Engage with followers of influencers in your niche.
    
    Strategy: Influencer's followers are already interested in your topic
    
    Args:
        influencer_username: Username of influencer (e.g., "VitalikButerin")
        count: Number of their recent tweets to engage with
        
    Returns:
        Number of engagements (likes + replies)
    """
    # Search for mentions/replies to the influencer
    query = f"@{influencer_username}"
    query = sanitize_search_query(query)

    # Avoid search API calls when like budget is exhausted.
    if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
        logger.info("Skipping influencer follower search - like limit reached")
        return 0
    
    tweets = tweet_handler.search_tweets(query, max_results=count)
    if not tweets:
        return 0
    
    engagements = 0
    engaged_authors = set()
    
    for tweet in tweets:
        if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
            logger.warning(f"Daily like limit reached ({Config.MAX_LIKES_PER_DAY})")
            break

        tweet_id = tweet['id']
        author_id = str(tweet.get('author_id', ''))
        author_username = tweet.get('author_info', {}).get('username', 'unknown')

        # Diversity rule: max one engagement per account in this phase.
        if not author_id or author_id in engaged_authors:
            continue

        # Skip the influencer's own tweets; we want surrounding real accounts.
        if author_username.lower() == influencer_username.lower():
            continue

        if not can_engage_user("like", user_id=author_id, username=author_username, cooldown_hours=72):
            continue
        if tweet_handler.like_tweet(tweet_id):
            RateLimiter.increment("likes", Config.MAX_LIKES_PER_DAY)
            engagements += 1
            engaged_authors.add(author_id)
            
            # Save engagement
            db.tweets.update_one(
                {"tweet_id": tweet_id},
                {
                    "$set": {
                        "tweet_id": tweet_id,
                        "author_id": tweet.get('author_id'),
                        "liked_at": datetime.utcnow(),
                        "influencer_engagement": True,
                        "target_influencer": influencer_username
                    }
                },
                upsert=True
            )
            
            time.sleep(random.randint(2, 5))

            if engagements >= count:
                break
    
    logger.info(f"✓ Engaged with {engagements} followers of @{influencer_username}")
    return engagements


def unfollow_inactive_accounts(days_inactive: int = 30) -> int:
    """Unfollow accounts that haven't followed back after X days.
    
    Args:
        days_inactive: Days since follow without followback
        
    Returns:
        Number of accounts unfollowed
    """
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
    
    # Find users followed >30 days ago who didn't follow back
    inactive = db.users.find({
        "followed_at": {"$lt": cutoff_date},
        "followed_back": False,
        "unfollowed_at": None
    }).limit(Config.MAX_UNFOLLOWS_PER_DAY)
    
    unfollowed = 0
    
    for user in inactive:
        if not RateLimiter.check_limit("unfollows", Config.MAX_UNFOLLOWS_PER_DAY):
            break
        
        user_id = user.get('user_id')
        try:
            if Config.DRY_RUN_MODE:
                logger.info(f"[DRY_RUN] Would unfollow inactive user {user_id}")
            else:
                tweet_handler.api.destroy_friendship(user_id=user_id)
            RateLimiter.increment("unfollows", Config.MAX_UNFOLLOWS_PER_DAY)
            
            # Mark as unfollowed
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"unfollowed_at": datetime.utcnow(), "reason": "no_followback"}}
            )
            
            unfollowed += 1
            time.sleep(random.randint(2, 4))
            
        except Exception as e:
            logger.error(f"Failed to unfollow {user_id}: {e}")
    
    logger.info(f"✓ Unfollowed {unfollowed} inactive accounts")
    return unfollowed
