"""MongoDB connection and operations."""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional

from config import config
from utils.logger import logger


class MongoDB:
    """MongoDB database manager."""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        
    def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(config.MONGODB_URI)
            # Get database name from URI or use default
            db_name = config.MONGODB_URI.split('/')[-1].split('?')[0] or 'x-growth'
            self.db = self.client[db_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB successfully (database: {db_name})")
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def _create_indexes(self) -> None:
        """Create database indexes for better performance."""
        try:
            # Tweets collection
            self.tweets.create_index([("tweet_id", ASCENDING)], unique=True)
            self.tweets.create_index([("engagement_score", DESCENDING)])
            self.tweets.create_index([("created_at", DESCENDING)])
            
            # Users collection
            self.users.create_index([("user_id", ASCENDING)], unique=True)
            self.users.create_index([("followed_at", DESCENDING)])
            
            # Trends collection
            self.trends.create_index([("fetched_at", DESCENDING)])
            self.trends.create_index([("name", ASCENDING)])
            
            # Activity log collection
            self.activity_logs.create_index([("timestamp", DESCENDING)])
            self.activity_logs.create_index([("action", ASCENDING)])
            
            # Direct messages collection
            self.direct_messages.create_index([("message_id", ASCENDING)], unique=True)
            self.direct_messages.create_index([("received_at", DESCENDING)])
            
            # Posts collection
            self.posts.create_index([("posted_at", DESCENDING)])
            
            logger.info("✓ Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Some indexes may already exist: {e}")
    
    @property
    def tweets(self) -> Collection:
        """Get tweets collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['tweets']
    
    @property
    def users(self) -> Collection:
        """Get users collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['users']
    
    @property
    def trends(self) -> Collection:
        """Get trends collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['trends']
    
    @property
    def activity_logs(self) -> Collection:
        """Get activity logs collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['activity_logs']
    
    @property
    def mentions(self) -> Collection:
        """Get mentions collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['mentions']
    
    @property
    def direct_messages(self) -> Collection:
        """Get direct messages collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['direct_messages']
    
    @property
    def posts(self) -> Collection:
        """Get posts collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['posts']
    
    @property
    def metrics_history(self) -> Collection:
        """Get metrics history collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['metrics_history']
    
    @property
    def rate_limits(self) -> Collection:
        """Get rate limits collection for tracking daily operation counts."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db['rate_limits']


# Global database instance
db = MongoDB()
