"""Database models and schema definitions."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Tweet:
    """Tweet model."""
    tweet_id: str
    author_id: str
    author_username: str
    text: str
    likes: int
    retweets: int
    replies: int
    engagement_score: int
    created_at: datetime
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    liked_at: Optional[datetime] = None
    retweeted_at: Optional[datetime] = None


@dataclass
class User:
    """User model."""
    user_id: str
    username: str
    name: str
    followers_count: int
    following_count: int
    bio: str
    followed_at: datetime
    followed_back: bool = False
    unfollowed_at: Optional[datetime] = None


@dataclass
class Trend:
    """Trending topic model."""
    name: str
    tweet_volume: int
    rank: int
    fetched_at: datetime


@dataclass
class ActivityLog:
    """Activity log model."""
    action: str  # 'like', 'retweet', 'follow', 'post', 'dm_response'
    target_id: str
    target_type: str  # 'tweet', 'user', 'dm'
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DirectMessage:
    """Direct message model."""
    message_id: str
    sender_id: str
    sender_username: str
    text: str
    received_at: datetime
    responded_at: Optional[datetime] = None
    response_text: Optional[str] = None


@dataclass
class Post:
    """Posted tweet model."""
    post_id: str
    text: str
    posted_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    impressions: Optional[int] = None
