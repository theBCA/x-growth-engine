"""Test individual bot operations one by one."""
from utils.logger import logger
from operations import (
    like_relevant_tweets,
    retweet_high_engagement,
    follow_relevant_users,
    check_mentions,
    get_account_metrics,
    get_trending_topics
)


def test_account_metrics():
    """Test: Get account metrics."""
    logger.info("\n" + "=" * 50)
    logger.info("TEST 1: Account Metrics")
    logger.info("=" * 50)
    
    stats = get_account_metrics()
    return stats


def test_trending_topics():
    """Test: Get trending topics."""
    logger.info("\n" + "=" * 50)
    logger.info("TEST 2: Trending Topics")
    logger.info("=" * 50)
    
    trends = get_trending_topics(limit=5)
    return trends


def test_search_and_like():
    """Test: Search and like tweets."""
    logger.info("\n" + "=" * 50)
    logger.info("TEST 3: Like Relevant Tweets")
    logger.info("=" * 50)
    
    # Test with small count (min 10 for X API)
    query = "#python"
    count = like_relevant_tweets(query, count=10)
    logger.info(f"Liked {count} tweets")
    return count


def test_search_and_retweet():
    """Test: Search and retweet tweets."""
    logger.info("\n" + "=" * 50)
    logger.info("TEST 4: Retweet High-Engagement Content")
    logger.info("=" * 50)
    
    # Test with small count (min 10 for X API)
    query = "#python"
    count = retweet_high_engagement(query, count=10, min_engagement=100)
    logger.info(f"Retweeted {count} tweets")
    return count


def test_follow_users():
    """Test: Follow relevant users."""
    logger.info("\n" + "=" * 50)
    logger.info("TEST 5: Follow Relevant Users")
    logger.info("=" * 50)
    
    # Test with small count (min 10 for X API)
    query = "#python"
    count = follow_relevant_users(query, count=10)
    logger.info(f"Followed {count} users")
    return count


def test_check_mentions():
    """Test: Check mentions."""
    logger.info("\n" + "=" * 50)
    logger.info("TEST 6: Check Mentions")
    logger.info("=" * 50)
    
    count = check_mentions(max_results=5)
    logger.info(f"Found {count} mentions")
    return count


def main():
    """Run individual tests."""
    logger.info("Starting Individual Operation Tests")
    logger.info("You can comment out tests you don't want to run\n")
    
    try:
        # Test 1: Account Metrics (safe, no writes)
        test_account_metrics()
        
        # Test 2: Trending Topics (safe, read-only)
        test_trending_topics()
        
        # Test 3: Check Mentions (safe, read-only)
        test_check_mentions()
        
        # WRITE OPERATIONS - These will actually like, retweet, and follow!
        logger.info("\n⚠️  STARTING WRITE OPERATIONS (LIKE, RETWEET, FOLLOW)")
        
        test_search_and_like()
        test_search_and_retweet()
        test_follow_users()
        
        logger.info("\n" + "=" * 50)
        logger.info("All Tests Completed!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
