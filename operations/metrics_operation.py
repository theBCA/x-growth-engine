from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from datetime import datetime


def get_account_metrics() -> dict:
    """Get current account metrics and save to database."""
    stats = tweet_handler.get_account_stats()
    if stats:
        logger.info(f"✓ Account: @{stats['username']}")
        logger.info(f"  Followers: {stats['followers']} | Following: {stats['following']}")
        logger.info(f"  Total Tweets: {stats['tweets']}")
        
        # Save metrics snapshot to database
        db.metrics_history.insert_one({
            "username": stats['username'],
            "followers": stats['followers'],
            "following": stats['following'],
            "tweets": stats['tweets'],
            "verified": stats.get('verified', False),
            "timestamp": datetime.utcnow()
        })
        
        return stats
    return {}
