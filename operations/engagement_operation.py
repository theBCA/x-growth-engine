from tweet_handler import tweet_handler
from utils.logger import logger
from utils.rate_limiter import RateLimiter
from operations.interaction_policy import can_engage_user
from config import Config


def engage_with_influencers(influencer_usernames: list, count: int = 10) -> int:
    """Engage with specific influencers' recent tweets."""
    total_engaged = 0
    
    for username in influencer_usernames:
        try:
            # Get user's recent tweets
            user = tweet_handler.api.get_user(screen_name=username)
            tweets = tweet_handler.api.user_timeline(user_id=user.id, count=count)
            
            for tweet in tweets[:3]:  # Engage with top 3 recent tweets
                tweet_id = str(tweet.id)
                author_id = str(user.id)
                if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
                    break
                if not can_engage_user("like", user_id=author_id, username=username, cooldown_hours=72):
                    continue
                
                # Like the tweet
                if tweet_handler.like_tweet(tweet_id):
                    RateLimiter.increment("likes", Config.MAX_LIKES_PER_DAY)
                    total_engaged += 1
                    logger.info(f"✓ Engaged with @{username}'s tweet")
                    
        except Exception as e:
            logger.error(f"Failed to engage with @{username}: {e}")
    
    logger.info(f"✓ Total engagements with influencers: {total_engaged}")
    return total_engaged


def monitor_keywords(keywords: list, action: str = "like", count: int = 20) -> int:
    """Monitor specific keywords and take action (like/retweet/reply)."""
    total_actions = 0
    
    for keyword in keywords:
        query = f"{keyword} -is:retweet"  # Exclude retweets
        tweets = tweet_handler.search_tweets(query, max_results=count)
        
        if not tweets:
            continue
        
        for tweet in tweets[:5]:  # Top 5 per keyword
            tweet_id = tweet.get('id')
            author_id = str(tweet.get('author_id', ''))
            author_username = tweet.get('author_info', {}).get('username', 'unknown')
            
            if action == "like":
                if not RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
                    break
                if not can_engage_user("like", user_id=author_id, username=author_username, cooldown_hours=72):
                    continue
                if tweet_handler.like_tweet(tweet_id):
                    RateLimiter.increment("likes", Config.MAX_LIKES_PER_DAY)
                    total_actions += 1
            elif action == "retweet":
                if not RateLimiter.check_limit("retweets", Config.MAX_RETWEETS_PER_DAY):
                    break
                if not can_engage_user("retweet", user_id=author_id, username=author_username, cooldown_hours=120):
                    continue
                if tweet_handler.retweet(tweet_id):
                    RateLimiter.increment("retweets", Config.MAX_RETWEETS_PER_DAY)
                    total_actions += 1
    
    logger.info(f"✓ Performed {total_actions} {action} actions on keywords")
    return total_actions
