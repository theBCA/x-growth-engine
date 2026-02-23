from tweet_handler import tweet_handler
from utils.logger import logger
from utils.rate_limiter import RateLimiter
from config import Config


def unfollow_non_followers(max_unfollow: int = 50) -> int:
    """Unfollow users who don't follow back (follow/unfollow strategy)."""
    try:
        user = tweet_handler.api.verify_credentials()
        
        # Get users we're following
        following = tweet_handler.api.get_friend_ids(user_id=user.id)
        
        # Get our followers
        followers = tweet_handler.api.get_follower_ids(user_id=user.id)
        
        # Find non-followers
        non_followers = set(following) - set(followers)
        
        if not non_followers:
            logger.info("✓ Everyone you follow also follows you back")
            return 0
        
        success_count = 0
        for user_id in list(non_followers)[:max_unfollow]:
            # Check rate limit before each unfollow
            if not RateLimiter.check_limit("unfollows", Config.MAX_UNFOLLOWS_PER_DAY):
                logger.warning(f"Daily unfollow limit reached ({Config.MAX_UNFOLLOWS_PER_DAY})")
                break
            
            try:
                if Config.DRY_RUN_MODE:
                    logger.info(f"[DRY_RUN] Would unfollow user {user_id}")
                else:
                    tweet_handler.api.destroy_friendship(user_id=user_id)
                
                # Increment rate limiter
                RateLimiter.increment("unfollows", Config.MAX_UNFOLLOWS_PER_DAY)
                
                success_count += 1
                logger.info(f"✓ Unfollowed user {user_id}")
            except Exception as e:
                logger.error(f"Failed to unfollow {user_id}: {e}")
        
        logger.info(f"✓ Unfollowed {success_count} non-followers")
        return success_count
        
    except Exception as e:
        logger.error(f"Failed to unfollow non-followers: {e}")
        return 0
