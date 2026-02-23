from operations.like_operation import like_relevant_tweets
from operations.retweet_operation import retweet_high_engagement
from operations.follow_operation import follow_relevant_users
from operations.mention_operation import check_mentions
from operations.metrics_operation import get_account_metrics
from operations.trends_operation import get_trending_topics
from operations.post_operation import post_tweet, reply_to_tweet
from operations.reply_operation import reply_to_relevant_tweets
from operations.unfollow_operation import unfollow_non_followers
from operations.engagement_operation import engage_with_influencers, monitor_keywords
from operations.ai_operation import (
    generate_ai_reply,
    generate_ai_tweet,
    generate_ai_thread,
    post_ai_generated_tweet,
    post_ai_thread,
    analyze_tweet_performance
)
from operations.dm_operation import respond_to_mentions_with_ai, get_unresponded_dms
from operations.analytics_operation import (
    get_engagement_metrics,
    get_follower_growth,
    get_most_engaged_topics,
    get_cost_analysis,
    generate_daily_report,
    analyze_best_performing_content,
    track_follower_growth,
    get_weekly_theme_insights
)
from operations.content_operation import (
    post_daily_content,
    post_weekly_thread,
    create_engagement_content,
    post_daily_original_lane,
    post_followup_from_replies
)
from operations.targeting_operation import follow_quality_accounts, engage_with_influencer_followers, unfollow_inactive_accounts
from operations.community_operation import reply_to_engagers, join_trending_conversations, engage_with_followers

__all__ = [
    # Basic operations
    'like_relevant_tweets',
    'retweet_high_engagement',
    'follow_relevant_users',
    'check_mentions',
    'get_account_metrics',
    'get_trending_topics',
    'post_tweet',
    'reply_to_tweet',
    'reply_to_relevant_tweets',
    'unfollow_non_followers',
    'engage_with_influencers',
    'monitor_keywords',
    # AI operations
    'generate_ai_reply',
    'generate_ai_tweet',
    'generate_ai_thread',
    'post_ai_generated_tweet',
    'post_ai_thread',
    'analyze_tweet_performance',
    # DM operations
    'respond_to_mentions_with_ai',
    'get_unresponded_dms',
    # Analytics
    'get_engagement_metrics',
    'get_follower_growth',
    'get_most_engaged_topics',
    'get_cost_analysis',
    'generate_daily_report',
    'analyze_best_performing_content',
    'track_follower_growth',
    'get_weekly_theme_insights',
    # Content Creation (NEW)
    'post_daily_content',
    'post_weekly_thread',
    'create_engagement_content',
    'post_daily_original_lane',
    'post_followup_from_replies',
    # Smart Targeting (NEW)
    'follow_quality_accounts',
    'engage_with_influencer_followers',
    'unfollow_inactive_accounts',
    # Community Building (NEW)
    'reply_to_engagers',
    'join_trending_conversations',
    'engage_with_followers'
]
