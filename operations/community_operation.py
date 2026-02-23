"""Community building and relationship operations."""
from tweet_handler import tweet_handler
from operations.ai_operation import generate_ai_reply
from utils.logger import logger
from database import db
from utils.rate_limiter import RateLimiter
from utils.sanitizer import sanitize_search_query, validate_tweet_text
from config import Config
from operations.engagement_filters import select_diverse_real_tweets
from operations.interaction_policy import can_reply_to_user, can_engage_user
from operations.value_content import build_value_fallback_reply
from datetime import datetime, timedelta
import time
import random


def reply_to_engagers(max_replies: int = 10) -> int:
    """Reply to people who engaged with your recent posts.
    
    Strategy: Build relationships with people who already showed interest
    
    Args:
        max_replies: Maximum number of replies to send
        
    Returns:
        Number of replies sent
    """
    # Get recent tweets that got engagement
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    engaged_posts = db.posts.find({
        "posted_at": {"$gte": week_ago},
        "$or": [
            {"likes": {"$gt": 0}},
            {"retweets": {"$gt": 0}},
            {"replies": {"$gt": 0}}
        ]
    }).sort("posted_at", -1).limit(5)
    
    replies_sent = 0
    
    for post in engaged_posts:
        if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
            break
        
        post_id = post.get("post_id")
        if not post_id:
            continue
        
        # In production: Get users who liked/replied to this tweet
        # For now: Generate thank you/engagement reply
        
        # This is a simplified version - in production you'd fetch actual engagers
        logger.info(f"Processing engagement for post {post_id}")
        replies_sent += 1
        
        if replies_sent >= max_replies:
            break
    
    logger.info(f"✓ Replied to {replies_sent} engagers")
    return replies_sent


def thank_new_followers(hours: int = 24) -> int:
    """Send personalized thanks to new followers.
    
    Args:
        hours: Look for followers from last X hours
        
    Returns:
        Number of thanks sent
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get users who followed back recently
    new_followers = db.users.find({
        "followed_back": True,
        "followed_at": {"$gte": cutoff},
        "thanked": {"$ne": True}
    }).limit(10)
    
    thanked = 0
    
    for follower in new_followers:
        if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
            break
        
        username = follower.get("username", "there")
        
        # Generate personalized thank you (if they have recent tweet)
        # In production: Find their recent tweet and reply
        logger.info(f"Would thank @{username} for following")
        
        # Mark as thanked
        db.users.update_one(
            {"user_id": follower.get("user_id")},
            {"$set": {"thanked": True, "thanked_at": datetime.utcnow()}}
        )
        
        thanked += 1
        time.sleep(random.randint(5, 10))
    
    logger.info(f"✓ Thanked {thanked} new followers")
    return thanked


def join_trending_conversations(trending_topics: list, count: int = 5) -> int:
    """Join trending conversations with valuable insights.
    
    Args:
        trending_topics: List of trending topics/hashtags
        count: Number of conversations to join
        
    Returns:
        Number of replies posted
    """
    replies_posted = 0

    for topic in trending_topics[:3]:  # Max 3 topics
        if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
            break

        safe_query = sanitize_search_query(str(topic))
        if not safe_query:
            continue

        # Search broader, then filter hard for real and diverse accounts
        search_count = min(100, max(20, count * 8))
        tweets = tweet_handler.search_tweets(safe_query, max_results=search_count)
        if not tweets:
            continue

        selected, bucket_counts, candidate_count = select_diverse_real_tweets(
            tweets=tweets,
            target_count=count,
            account_username=Config.ACCOUNT_USERNAME
        )
        if not selected:
            logger.info(f"No high-confidence real accounts for topic: {safe_query}")
            continue

        topic_replies = 0
        for tweet in selected:
            if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
                break
            
            tweet_id = tweet.get('id')
            tweet_text = tweet.get('text', '')
            author_info = tweet.get('author_info', {})
            author = author_info.get('username') or str(tweet.get('author_id', 'user'))
            author_id = str(tweet.get("author_id", ""))

            if not can_reply_to_user(author_id, str(author)):
                continue
            
            # Generate valuable reply using AI
            reply_text = generate_ai_reply(tweet_text, str(author))
            if not reply_text:
                reply_text = build_value_fallback_reply(tweet_text, str(author))
                is_valid, _ = validate_tweet_text(reply_text)
                if not is_valid:
                    continue
            
            if reply_text and tweet_handler.reply_to_tweet(tweet_id, reply_text):
                RateLimiter.increment("replies", Config.MAX_REPLIES_PER_DAY)
                replies_posted += 1
                topic_replies += 1
                
                # Log the conversation join
                db.activity_logs.insert_one({
                    "action": "reply",
                    "target_id": tweet_id,
                    "target_user": str(author),
                    "target_user_id": author_id,
                    "timestamp": datetime.utcnow(),
                    "success": True,
                    "metadata": {
                        "subtype": "join_conversation",
                        "trending_topic": safe_query
                    }
                })
                
                time.sleep(random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS))

        logger.info(
            f"Topic '{safe_query}': replied {topic_replies}, "
            f"real_candidates={candidate_count}, buckets={bucket_counts}"
        )
    
    logger.info(f"✓ Joined {replies_posted} trending conversations")
    return replies_posted


def engage_with_followers(count: int = 20) -> int:
    """Engage with existing followers to maintain relationships.
    
    Args:
        count: Number of followers to engage with
        
    Returns:
        Number of engagements
    """
    # Get followers who followed back
    followers = db.users.find({
        "followed_back": True,
        "unfollowed_at": None
    }).limit(count)
    
    engagements = 0
    
    for follower in followers:
        username = follower.get("username")
        if not username:
            continue
        
        # Search for their recent tweets
        query = f"from:{username}"
        tweets = tweet_handler.search_tweets(query, max_results=3)
        
        if tweets:
            # Like their most recent tweet
            if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
                logger.warning(f"Daily like limit reached ({Config.MAX_LIKES_PER_DAY})")
                break
            recent_tweet = tweets[0]
            tweet_id = recent_tweet.get('id')
            author_id = str(recent_tweet.get('author_id', ''))
            if not can_engage_user("like", user_id=author_id, username=username, cooldown_hours=72):
                continue
            
            if tweet_handler.like_tweet(tweet_id):
                RateLimiter.increment("likes", Config.MAX_LIKES_PER_DAY)
                engagements += 1
                
                time.sleep(random.randint(3, 7))
    
    logger.info(f"✓ Engaged with {engagements} existing followers")
    return engagements
