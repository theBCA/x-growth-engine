"""Rate limiting enforcement for X API operations."""
from datetime import datetime, date
from typing import Optional
from database import db
from utils.logger import logger
from config import Config


class RateLimiter:
    """Enforces daily rate limits for bot operations."""
    
    @staticmethod
    def get_daily_count(action: str, today: Optional[date] = None) -> int:
        """
        Get count for action today.
        
        Args:
            action: Action name (e.g., 'likes', 'retweets', 'follows')
            today: Date to check (defaults to today)
            
        Returns:
            Count of actions performed today
        """
        if today is None:
            today = datetime.utcnow().date()
        
        try:
            result = db.rate_limits.find_one({
                "action": action,
                "date": today.isoformat()
            })
            return result["count"] if result else 0
        except Exception as e:
            logger.error(f"Failed to get rate limit count: {e}")
            return 0
    
    @staticmethod
    def check_limit(action: str, limit: int) -> bool:
        """
        Check if action is under daily limit.
        
        Args:
            action: Action name
            limit: Maximum allowed per day
            
        Returns:
            True if under limit, False if limit reached
        """
        # Dry run should preview decisions without being blocked by persisted counters.
        if Config.DRY_RUN_MODE:
            return True

        count = RateLimiter.get_daily_count(action)
        
        if count >= limit:
            logger.warning(f"⚠️ Rate limit reached for {action}: {count}/{limit}")
            return False
        
        return True
    
    @staticmethod
    def increment(action: str, limit: int) -> bool:
        """
        Increment counter for action and check if still under limit.
        
        Args:
            action: Action name
            limit: Maximum allowed per day
            
        Returns:
            True if operation allowed, False if limit exceeded
        """
        # Dry run should not mutate counters.
        if Config.DRY_RUN_MODE:
            return True

        today = datetime.utcnow().date().isoformat()
        
        try:
            # Increment counter
            db.rate_limits.update_one(
                {"action": action, "date": today},
                {
                    "$inc": {"count": 1},
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )
            
            # Check if over limit
            count = RateLimiter.get_daily_count(action)
            
            if count > limit:
                logger.warning(f"⚠️ Rate limit EXCEEDED for {action}: {count}/{limit}")
                return False
            
            logger.debug(f"✓ Rate limit OK for {action}: {count}/{limit}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to increment rate limit: {e}")
            # Fail safe: allow operation if tracking fails
            return True
    
    @staticmethod
    def reset_daily_limits() -> None:
        """Reset all rate limits (called at midnight)."""
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Delete old entries (older than 7 days)
            cutoff = datetime.utcnow().date()
            db.rate_limits.delete_many({
                "date": {"$lt": cutoff.isoformat()}
            })
            
            logger.info("✓ Daily rate limits reset")
            
        except Exception as e:
            logger.error(f"Failed to reset rate limits: {e}")
    
    @staticmethod
    def get_limits_status() -> dict:
        """
        Get current status of all rate limits.
        
        Returns:
            Dictionary with action: (count, limit) pairs
        """
        limits = {
            "likes": Config.MAX_LIKES_PER_DAY,
            "retweets": Config.MAX_RETWEETS_PER_DAY,
            "follows": Config.MAX_FOLLOWS_PER_DAY,
            "posts": Config.MAX_POSTS_PER_DAY,
            "dm_responses": Config.MAX_DM_RESPONSES_PER_DAY,
        }
        
        status = {}
        for action, limit in limits.items():
            count = RateLimiter.get_daily_count(action)
            status[action] = {
                "count": count,
                "limit": limit,
                "remaining": max(0, limit - count),
                "percentage": (count / limit * 100) if limit > 0 else 0
            }
        
        return status
    
    @staticmethod
    def is_safe_to_operate(action: str) -> bool:
        """
        Check if it's safe to perform an action (not close to limit).
        
        Args:
            action: Action to check
            
        Returns:
            True if safe (under 90% of limit), False otherwise
        """
        limits = {
            "likes": Config.MAX_LIKES_PER_DAY,
            "retweets": Config.MAX_RETWEETS_PER_DAY,
            "follows": Config.MAX_FOLLOWS_PER_DAY,
            "posts": Config.MAX_POSTS_PER_DAY,
            "dm_responses": Config.MAX_DM_RESPONSES_PER_DAY,
        }
        
        if action not in limits:
            return True
        
        limit = limits[action]
        count = RateLimiter.get_daily_count(action)
        
        # Safe if under 90% of limit
        safe_threshold = limit * 0.9
        return count < safe_threshold
