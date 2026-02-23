"""Analytics and performance tracking operations."""
from database import db
from utils.logger import logger
from datetime import datetime, timedelta
from config import Config
from config_topics import SEARCH_QUERIES


def analyze_best_performing_content() -> dict:
    """Analyze which content gets the most engagement."""
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_posts = list(db.posts.find({
        "posted_at": {"$gte": week_ago}
    }).sort("posted_at", -1))
    
    if not recent_posts:
        return {"message": "No recent posts"}
    
    total_posts = len(recent_posts)
    topics_performance = {}
    
    for post in recent_posts:
        engagement = post.get("likes", 0) + post.get("retweets", 0)
        topic = post.get("topic", "unknown")
        
        if topic not in topics_performance:
            topics_performance[topic] = {"posts": 0, "engagement": 0}
        topics_performance[topic]["posts"] += 1
        topics_performance[topic]["engagement"] += engagement
    
    # Find best topic
    best_topic = max(topics_performance.items(), 
                     key=lambda x: x[1]["engagement"] / x[1]["posts"] if x[1]["posts"] > 0 else 0,
                     default=(None, {}))[0]
    
    logger.info(f"✓ Best performing topic: {best_topic}")
    return {"best_topic": best_topic, "breakdown": topics_performance}


def track_follower_growth() -> dict:
    """Track follower growth and followback rate."""
    total_followed = db.users.count_documents({"followed_at": {"$ne": None}})
    followed_back = db.users.count_documents({"followed_back": True})
    followback_rate = (followed_back / total_followed * 100) if total_followed > 0 else 0
    
    logger.info(f"✓ Followback rate: {followback_rate:.1f}%")
    return {
        "total_followed": total_followed,
        "followed_back": followed_back,
        "followback_rate": round(followback_rate, 1)
    }


def get_engagement_metrics(days: int = 7) -> dict:
    """Get engagement metrics for the last N days."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get actions from last N days
        actions = list(db.activity_logs.find({
            "timestamp": {"$gte": start_date}
        }))
        
        metrics = {
            "period_days": days,
            "total_actions": len(actions),
            "likes": len([a for a in actions if a["action"] == "like"]),
            "retweets": len([a for a in actions if a["action"] == "retweet"]),
            "follows": len([a for a in actions if a["action"] == "follow"]),
            "posts": len([a for a in actions if a["action"] == "post"]),
        }
        
        # Calculate daily average
        metrics["daily_average"] = metrics["total_actions"] / days if days > 0 else 0
        
        logger.info(f"✓ Got engagement metrics for last {days} days")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get engagement metrics: {e}")
        return {}


def get_follower_growth(days: int = 7) -> dict:
    """Get follower growth over time."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get metrics history
        metrics = list(db.metrics_history.find({
            "timestamp": {"$gte": start_date}
        }).sort("timestamp", 1))
        
        if len(metrics) < 2:
            return {"data_points": len(metrics), "growth": 0}
        
        first = metrics[0]["followers"]
        last = metrics[-1]["followers"]
        growth = last - first
        growth_percent = (growth / first * 100) if first > 0 else 0
        
        timeline = {
            "start_followers": first,
            "end_followers": last,
            "growth": growth,
            "growth_percent": round(growth_percent, 2),
            "data_points": len(metrics),
            "dates": [m["timestamp"].strftime("%Y-%m-%d") for m in metrics]
        }
        
        logger.info(f"✓ Follower growth: +{growth} ({growth_percent:.1f}%)")
        return timeline
        
    except Exception as e:
        logger.error(f"Failed to get follower growth: {e}")
        return {}


def get_most_engaged_topics() -> list:
    """Find which topics/queries generated most engagement."""
    try:
        # Get tweets with highest engagement
        top_tweets = list(db.tweets.find().sort("engagement_score", -1).limit(10))
        
        topics = {}
        for tweet in top_tweets:
            query = tweet.get("search_query", "unknown")
            engagement = tweet.get("engagement_score", 0)
            
            if query not in topics:
                topics[query] = {"engagement": 0, "count": 0}
            
            topics[query]["engagement"] += engagement
            topics[query]["count"] += 1
        
        # Sort by total engagement
        sorted_topics = sorted(topics.items(), key=lambda x: x[1]["engagement"], reverse=True)
        
        result = [
            {
                "topic": topic,
                "total_engagement": data["engagement"],
                "tweet_count": data["count"],
                "avg_engagement": data["engagement"] / data["count"]
            }
            for topic, data in sorted_topics[:5]
        ]
        
        logger.info(f"✓ Found top topics by engagement")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get top topics: {e}")
        return []


def get_cost_analysis() -> dict:
    """Analyze bot cost based on API usage."""
    try:
        all_actions = list(db.activity_logs.find())
        
        # Rough cost estimate per action
        cost_per_action = {
            "like": 0.001,
            "retweet": 0.001,
            "follow": 0.005,
            "post": 0.01,
            "search": 0.001
        }
        
        total_cost = 0
        breakdown = {}
        
        for action in all_actions:
            action_type = action.get("action", "unknown")
            cost = cost_per_action.get(action_type, 0.001)
            total_cost += cost
            
            if action_type not in breakdown:
                breakdown[action_type] = {"count": 0, "cost": 0}
            
            breakdown[action_type]["count"] += 1
            breakdown[action_type]["cost"] += cost
        
        logger.info(f"✓ Total estimated cost: ${total_cost:.2f}")
        
        return {
            "total_cost": round(total_cost, 2),
            "total_actions": len(all_actions),
            "breakdown": breakdown,
            "cost_per_action": round(total_cost / len(all_actions), 4) if all_actions else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze costs: {e}")
        return {}


def generate_daily_report() -> dict:
    """Generate comprehensive daily report."""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_actions = list(db.activity_logs.find({
            "timestamp": {"$gte": today}
        }))
        
        report = {
            "date": today.strftime("%Y-%m-%d"),
            "today_stats": {
                "total_actions": len(today_actions),
                "likes": len([a for a in today_actions if a["action"] == "like"]),
                "retweets": len([a for a in today_actions if a["action"] == "retweet"]),
                "follows": len([a for a in today_actions if a["action"] == "follow"]),
                "posts": len([a for a in today_actions if a["action"] == "post"]),
            },
            "week_metrics": get_engagement_metrics(7),
            "growth": get_follower_growth(7),
            "top_topics": get_most_engaged_topics(),
            "costs": get_cost_analysis()
        }
        
        logger.info(f"✓ Generated daily report")
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return {}


def get_weekly_theme_insights(days: int = 7) -> dict:
    """
    Weekly theme performance using available proxies.
    Note: X API does not provide profile visits/follows-by-post in this flow.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        posts = list(db.posts.find({"posted_at": {"$gte": start_date}}))
        if not posts:
            return {"best_theme": None, "themes": {}}

        lane_terms = set()
        for n in Config.NICHE:
            term = (n or "").strip().lower()
            if term:
                lane_terms.add(term)
        for q in SEARCH_QUERIES:
            qn = (q or "").lower().replace("#", "").strip()
            for token in qn.split():
                if len(token) >= 3:
                    lane_terms.add(token)

        def _is_current_lane(topic: str, niche: str) -> bool:
            topic_l = (topic or "").lower()
            niche_l = (niche or "").lower()
            if niche_l and any(t in niche_l for t in lane_terms):
                return True
            return any(t in topic_l for t in lane_terms)

        themes = {}
        for p in posts:
            topic = p.get("topic", "unknown")
            niche = p.get("niche", "")
            if not _is_current_lane(topic, niche):
                continue
            engagement = p.get("likes", 0) + p.get("retweets", 0) + p.get("replies", 0)
            if topic not in themes:
                themes[topic] = {"posts": 0, "engagement": 0, "score": 0}
            themes[topic]["posts"] += 1
            themes[topic]["engagement"] += engagement

        if not themes:
            return {"best_theme": None, "themes": {}}

        # Add conversation momentum proxy from successful replies referencing same theme/query.
        replies = list(db.activity_logs.find({
            "action": "reply",
            "success": True,
            "timestamp": {"$gte": start_date}
        }))
        for r in replies:
            md = r.get("metadata", {})
            ref = md.get("safe_query") or md.get("trend")
            if ref in themes:
                themes[ref]["score"] += 2

        for t, data in themes.items():
            data["score"] += data["engagement"] + (data["posts"] * 3)

        best_theme = max(themes.items(), key=lambda x: x[1]["score"])[0]
        logger.info(f"✓ Weekly theme winner: {best_theme}")
        return {"best_theme": best_theme, "themes": themes}
    except Exception as e:
        logger.error(f"Failed to get weekly theme insights: {e}")
        return {"best_theme": None, "themes": {}}
