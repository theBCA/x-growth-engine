from operations.retweet_operation import retweet_high_engagement
from operations.trends_operation import discover_active_topics
from operations.like_operation import like_relevant_tweets
from operations.content_operation import post_daily_original_lane, post_followup_from_replies
from operations.targeting_operation import engage_with_influencer_followers, unfollow_inactive_accounts
from operations.analytics_operation import analyze_best_performing_content, track_follower_growth, get_weekly_theme_insights
from operations.community_operation import reply_to_engagers, engage_with_followers
from operations.trend_strategy import engage_with_trending_tweets
from config_topics import INFLUENCERS
from config import Config
from utils.logger import logger
from utils.rate_limiter import RateLimiter
import time


def _to_topic_strings(items: list, limit: int) -> list:
    topics = []
    for item in items[:limit]:
        if isinstance(item, dict):
            topics.append(str(item.get("name", "")).strip())
        else:
            topics.append(str(item).strip())
    return [t for t in topics if t]


def run_growth_strategy():
    """Primary production flow."""
    logger.info("=" * 60)
    logger.info("🚀 GROWTH STRATEGY - Trend-Aware Organic Growth")
    logger.info("=" * 60)
    
    # PHASE 0: DAILY ORIGINAL POST (Highest value)
    logger.info("\n[0/9] 🧠 Daily Original Post")
    daily_parts = post_daily_original_lane()
    if daily_parts > 0:
        logger.info(f"✓ Published daily original post in {daily_parts} part(s)")
    time.sleep(2)

    # PHASE 1: Targeted influencer-follower engagement
    logger.info("\n[1/9] ⭐ Engaging with Influencer Followers")
    if RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY):
        for influencer in INFLUENCERS[:2]:
            engage_with_influencer_followers(
                influencer,
                count=max(1, Config.INFLUENCER_ENGAGEMENT_TARGET),
            )
            time.sleep(3)
    else:
        logger.info("Skipping influencer engagement - like limit reached")
    
    # PHASE 2: join high-signal conversations from active topic research.
    logger.info("\n[2/9] 💬 Joining Trending Conversations (Varied Angles)")
    topic_limit = max(1, Config.MAX_TREND_TOPICS_PER_RUN)
    can_reply = RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY)
    can_like = RateLimiter.check_limit("likes", Config.MAX_LIKES_PER_DAY)
    trending_topics = []
    if can_reply or can_like:
        trending = discover_active_topics(
            limit=topic_limit,
            pool_size=Config.TOPIC_RESEARCH_POOL_SIZE,
            sample_size=Config.TOPIC_RESEARCH_SAMPLE_SIZE,
        )
        trending_topics = _to_topic_strings(trending or [], topic_limit)

        if not trending_topics:
            logger.info("No active topics discovered; skipping trend engagement phase")

        for topic in trending_topics:
            # Reply for conversation depth.
            if can_reply:
                engage_with_trending_tweets(topic, count=max(1, Config.REPLY_TARGETS_PER_TOPIC))
            # Like nearby quality tweets in same topic cluster.
            if can_like:
                like_relevant_tweets(topic, count=max(1, Config.LIKE_TARGETS_PER_TOPIC))
            time.sleep(2)
    else:
        logger.info("Skipping trend engagement - like/reply limits reached")
    time.sleep(2)

    # PHASE 3: selective retweets of big tweets.
    logger.info("\n[3/9] 🔁 Retweeting Big Tweets (High Engagement Only)")
    if RateLimiter.check_limit("retweets", Config.MAX_RETWEETS_PER_DAY):
        rt_query_limit = max(0, Config.MAX_RETWEET_QUERIES_PER_RUN)
        big_tweet_queries = (trending_topics[:rt_query_limit] if trending_topics else [])
        for query in big_tweet_queries:
            # Keep this conservative: high engagement threshold + low count.
            retweet_high_engagement(query, count=1, min_engagement=200)
            time.sleep(2)
    else:
        logger.info("Skipping retweet phase - retweet limit reached")
    
    # PHASE 5: COMMUNITY BUILDING
    logger.info("\n[4/9] 🤝 Building Community")
    reply_to_engagers(max_replies=3)
    engage_with_followers(count=5)
    time.sleep(2)
    
    # PHASE 6: STRATEGIC CLEANUP
    logger.info("\n[5/9] 🧹 Cleaning Up Inactive Follows")
    unfollow_inactive_accounts(days_inactive=30)
    time.sleep(2)

    # PHASE 7: Follow-up post from today's best reply threads.
    logger.info("\n[6/9] 🧵 Follow-up Post from Reply Threads")
    followup_parts = post_followup_from_replies()
    if followup_parts > 0:
        logger.info(f"✓ Published follow-up post in {followup_parts} part(s)")
    time.sleep(2)
    
    # PHASE 7: ANALYTICS & OPTIMIZATION
    logger.info("\n[7/9] 📊 Analyzing Performance")
    analytics = analyze_best_performing_content()
    growth = track_follower_growth()
    weekly = get_weekly_theme_insights(days=7)
    
    # PHASE 8: FINAL INSIGHTS
    logger.info("\n[8/9] 🔍 Final Insights")
    logger.info(f"   Best Topic: {analytics.get('best_topic', 'N/A')}")
    logger.info(f"   Weekly Theme Winner: {weekly.get('best_theme', 'N/A')}")
    logger.info(f"   Followback Rate: {growth.get('followback_rate', 0)}%")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ GROWTH STRATEGY COMPLETE - Trend Aware & Diverse")
    logger.info("=" * 60)
