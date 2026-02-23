"""Trend analysis and intelligent content generation based on trending topics."""
from tweet_handler import tweet_handler
from operations.trends_operation import get_trending_topics as get_engagement_topics
from operations.research_engine import collect_research_candidates
from operations.decision_engine import select_reply_targets, generate_best_reply, generate_best_post
from utils.logger import logger
from utils.sanitizer import sanitize_search_query
from database import db
from datetime import datetime
from config import Config


def analyze_trending_topics(limit: int = 10) -> list:
    """Fetch engagement topics from X-native trend discovery."""
    try:
        logger.info(f"📊 Fetching top {limit} engagement topics...")
        trends = get_engagement_topics(limit=limit)
        if trends:
            logger.info(f"✓ Got {len(trends)} X-focused topics")
            return [{'name': t, 'tweet_volume': 0} for t in trends]

        logger.info("Using fallback popular topics...")
        fallback_topics = [
            "artificial intelligence",
            "machine learning",
            "cybersecurity",
            "software development",
            "technology news",
            "startup news",
            "data science",
            "cloud computing",
            "mobile apps",
            "web development"
        ]
        return [{'name': t, 'tweet_volume': 0} for t in fallback_topics[:limit]]
        
    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        return []


def generate_trend_based_content(trend_name: str) -> str:
    """Generate original content based on a trending topic."""
    try:
        logger.info(f"🎯 Generating content based on trend: {trend_name}")
        topic = f"Perspective on the {trend_name} trend"
        niche = (Config.NICHE[0].strip() if Config.NICHE else "technology") or "technology"
        tweet = generate_best_post(topic, niche=niche)
        if tweet:
            logger.info(f"✓ Generated trend-based content")
            return tweet
        return None
        
    except Exception as e:
        logger.error(f"Failed to generate trend content: {e}")
        return None


# Track users we've replied to in this session to avoid duplicates
_replied_users = set()


def build_safe_trend_query(trend_name: str) -> str:
    """Create a safe, short query from noisy trend titles."""
    query = sanitize_search_query(str(trend_name or ""))
    if not query:
        return ""

    # Keep query compact to reduce X operator parsing failures
    words = query.split()
    if len(words) > 8:
        query = " ".join(words[:8])

    # Remove wrapping punctuation characters that can break search parsing
    query = query.strip(" .,!?'\"-")
    return query


def engage_with_trending_tweets(trend_name: str, count: int = 5) -> int:
    """Find and engage with tweets using research + decision scoring."""
    try:
        logger.info(f"💬 Engaging with tweets about: {trend_name}")
        from utils.rate_limiter import RateLimiter
        if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
            logger.info("Skipping trend replies - reply limit reached")
            return 0

        safe_query = build_safe_trend_query(trend_name)
        if not safe_query:
            logger.warning(f"Invalid trend query after sanitization: {trend_name}")
            return 0

        candidates = collect_research_candidates(safe_query, max_candidates=min(100, max(30, count * 12)))
        if not candidates:
            logger.warning(f"No quality candidates found for trend query: {safe_query}")
            return 0
        targets, bucket_counts = select_reply_targets(
            candidates=candidates,
            count=count,
            account_username=Config.ACCOUNT_USERNAME,
            session_replied_users=_replied_users,
        )
        if not targets:
            logger.info("Decision engine selected no reply targets")
            return 0

        engaged_count = 0
        for tweet in targets:
            tweet_id = tweet.get("id")
            author_info = tweet.get("author_info", {})
            author_username = author_info.get("username", "unknown")
            tweet_text = tweet.get("text", "")
            bucket = tweet.get("followers_bucket", "mid")
            reply = generate_best_reply(tweet_text, author_username)

            if reply and tweet_handler.reply_to_tweet(tweet_id, reply):
                engaged_count += 1
                _replied_users.add(author_username)  # Track this user
                logger.info(
                    f"✓ Replied to @{author_username} (candidate_score={tweet.get('candidate_score', 0):.1f}, bucket={bucket})"
                )
                
                # Log activity
                try:
                    db.activity_logs.insert_one({
                        "action": "reply",
                        "target_id": tweet_id,
                        "target_type": "tweet",
                        "target_user": author_username,
                        "target_user_id": str(tweet.get("author_id", "")),
                        "timestamp": datetime.utcnow(),
                        "success": True,
                        "metadata": {
                            "trend": trend_name,
                            "safe_query": safe_query,
                            "research_query": tweet.get("research_query", safe_query),
                            "candidate_score": tweet.get("candidate_score", 0),
                            "reply_text": reply[:100]
                        }
                    })
                except:
                    pass  # Continue even if DB logging fails
        
        logger.info(
            f"✓ Engaged with {engaged_count}/{count} real-person accounts "
            f"(researched={len(candidates)}, selected={len(targets)}, buckets={bucket_counts})"
        )
        return engaged_count
        
    except Exception as e:
        logger.error(f"Failed to engage with trending tweets: {e}")
        return 0


def create_trend_awareness_post(trend_name: str) -> bool:
    """Create and post a tweet acknowledging a trend with original take."""
    try:
        logger.info(f"📝 Creating trend awareness post about: {trend_name}")
        
        # Generate content
        content = generate_trend_based_content(trend_name)
        
        if not content:
            return False
        
        # Post it
        post_id = tweet_handler.post_tweet(content)
        
        if post_id:
            # Log to database
            db.posts.insert_one({
                "post_id": post_id,
                "text": content,
                "posted_at": datetime.utcnow(),
                "ai_generated": True,
                "topic": trend_name,
                "based_on_trend": True
            })
            
            logger.info(f"✓ Posted trend-aware content")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to create trend awareness post: {e}")
        return False


def intelligent_content_strategy(max_posts: int = 3, max_replies: int = 5) -> dict:
    """Execute an intelligent, trend-aware content strategy."""
    try:
        logger.info("=" * 60)
        logger.info("🎯 INTELLIGENT CONTENT STRATEGY - Trend Aware")
        logger.info("=" * 60)
        
        stats = {
            "trends_analyzed": 0,
            "posts_created": 0,
            "replies_generated": 0,
            "engagements": 0
        }
        
        # 1. Analyze current trends
        logger.info("\n[1] Analyzing Trending Topics...")
        trends = analyze_trending_topics(limit=10)
        stats["trends_analyzed"] = len(trends)
        
        if not trends:
            logger.warning("No relevant trends found")
            return stats
        
        # 2. Create posts based on top trends
        logger.info(f"\n[2] Creating Posts Based on Trends (max {max_posts})...")
        for trend in trends[:max_posts]:
            if create_trend_awareness_post(trend.get('name')):
                stats["posts_created"] += 1
        
        # 3. Engage with trending conversations
        logger.info(f"\n[3] Engaging with Trending Tweets (max {max_replies})...")
        for trend in trends[:3]:
            replies = engage_with_trending_tweets(trend.get('name'), count=max_replies // 3)
            stats["replies_generated"] += replies
        
        stats["engagements"] = stats["posts_created"] + stats["replies_generated"]
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✓ STRATEGY COMPLETE")
        logger.info(f"  Trends Analyzed: {stats['trends_analyzed']}")
        logger.info(f"  Posts Created: {stats['posts_created']}")
        logger.info(f"  Replies Generated: {stats['replies_generated']}")
        logger.info(f"  Total Engagements: {stats['engagements']}")
        logger.info("=" * 60)
        
        return stats
        
    except Exception as e:
        logger.error(f"Content strategy failed: {e}")
        return {}
