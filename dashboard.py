"""Web dashboard to view bot analytics and data."""
from flask import Flask, render_template, jsonify
from flask_httpauth import HTTPBasicAuth
from database import db
from datetime import datetime, timedelta
from config import Config
import os
import json

app = Flask(__name__)
auth = HTTPBasicAuth()

# Dashboard credentials from environment
DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME', 'admin')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'changeme123')


@auth.verify_password
def verify_password(username, password):
    """Verify dashboard credentials."""
    if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
        return username
    return None


@app.route('/')
@auth.login_required
def index():
    """Dashboard home page."""
    # Connect to DB if not connected
    if not db.client:
        db.connect()
    
    # Get summary stats
    stats = get_summary_stats()
    recent_activity = get_recent_activity(limit=20)
    growth_data = get_growth_data()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_activity=recent_activity,
                         growth_data=growth_data)


@app.route('/api/stats')
@auth.login_required
def api_stats():
    """API endpoint for stats."""
    if not db.client:
        db.connect()
    return jsonify(get_summary_stats())


@app.route('/api/health')
def api_health():
    """Health check endpoint (no auth required)."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database connection
    try:
        if not db.client:
            db.connect()
        db.client.server_info()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Check X API credentials
    try:
        Config.validate()
        health_status["checks"]["api_credentials"] = "configured"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["api_credentials"] = f"error: {str(e)}"
    
    # Check last operation
    try:
        last_activity = db.activity_logs.find_one(sort=[("timestamp", -1)])
        if last_activity:
            health_status["checks"]["last_operation"] = last_activity["timestamp"].isoformat()
        else:
            health_status["checks"]["last_operation"] = "none"
    except Exception as e:
        health_status["checks"]["last_operation"] = f"error: {str(e)}"
    
    return jsonify(health_status)


@app.route('/tweets')
@auth.login_required
def tweets():
    """View all tweets."""
    if not db.client:
        db.connect()
    
    # Get liked and retweeted tweets
    tweets_list = list(db.tweets.find().sort("liked_at", -1).limit(100))
    
    # Convert ObjectId to string for JSON serialization
    for tweet in tweets_list:
        tweet['_id'] = str(tweet['_id'])
        if 'created_at' in tweet:
            tweet['created_at'] = str(tweet['created_at'])
        if 'liked_at' in tweet:
            tweet['liked_at'] = str(tweet['liked_at'])
        if 'retweeted_at' in tweet:
            tweet['retweeted_at'] = str(tweet['retweeted_at'])
    
    return render_template('tweets.html', tweets=tweets_list)


@app.route('/users')
@auth.login_required
def users():
    """View all followed users."""
    if not db.client:
        db.connect()
    
    users_list = list(db.users.find().sort("followed_at", -1).limit(100))
    
    for user in users_list:
        user['_id'] = str(user['_id'])
        if 'followed_at' in user:
            user['followed_at'] = str(user['followed_at'])
    
    return render_template('users.html', users=users_list)


@app.route('/activity')
@auth.login_required
def activity():
    """View activity logs."""
    if not db.client:
        db.connect()
    
    logs = get_recent_activity(limit=200)
    return render_template('activity.html', logs=logs)


def get_summary_stats():
    """Get summary statistics."""
    stats = {
        'total_tweets_liked': db.tweets.count_documents({"liked_at": {"$ne": None}}),
        'total_tweets_retweeted': db.tweets.count_documents({"retweeted_at": {"$ne": None}}),
        'total_users_followed': db.users.count_documents({"unfollowed_at": None}),
        'total_mentions': db.mentions.count_documents({}),
        'total_actions': db.activity_logs.count_documents({}),
    }
    
    # Get latest metrics
    latest_metrics = db.metrics_history.find_one(sort=[("timestamp", -1)])
    if latest_metrics:
        stats['current_followers'] = latest_metrics.get('followers', 0)
        stats['current_following'] = latest_metrics.get('following', 0)
        stats['current_tweets'] = latest_metrics.get('tweets', 0)
    else:
        stats['current_followers'] = 0
        stats['current_following'] = 0
        stats['current_tweets'] = 0
    
    # Calculate today's activity
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    stats['today_actions'] = db.activity_logs.count_documents({
        "timestamp": {"$gte": today}
    })
    
    return stats


def get_recent_activity(limit=50):
    """Get recent activity logs."""
    logs = list(db.activity_logs.find().sort("timestamp", -1).limit(limit))
    
    for log in logs:
        log['_id'] = str(log['_id'])
        if 'timestamp' in log:
            log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    return logs


def get_growth_data():
    """Get growth data for charts."""
    # Get metrics from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    metrics = list(db.metrics_history.find({
        "timestamp": {"$gte": thirty_days_ago}
    }).sort("timestamp", 1))
    
    growth_data = {
        'dates': [],
        'followers': [],
        'following': []
    }
    
    for metric in metrics:
        growth_data['dates'].append(metric['timestamp'].strftime('%Y-%m-%d'))
        growth_data['followers'].append(metric.get('followers', 0))
        growth_data['following'].append(metric.get('following', 0))
    
    return growth_data


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 X-Bot Dashboard Starting")
    print("="*50)
    print("\nOpen your browser and go to:")
    print("👉 http://localhost:5001")
    print("\nPress CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
