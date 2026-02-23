"""Configuration management for X growth tool."""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # X API Credentials
    X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN', '')
    X_CONSUMER_KEY = os.getenv('X_CONSUMER_KEY', '')
    X_CONSUMER_SECRET = os.getenv('X_CONSUMER_SECRET', '')
    X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN', '')
    X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET', '')
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/x-growth')
    
    # OpenAI (gpt-4o - proven to work reliably)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    # Account Settings
    ACCOUNT_USERNAME = os.getenv('ACCOUNT_USERNAME', '')
    NICHE: List[str] = os.getenv('NICHE', 'technology').split(',')
    TARGET_AUDIENCE: List[str] = os.getenv('TARGET_AUDIENCE', 'developers').split(',')
    
    # Rate Limits (Daily)
    MAX_LIKES_PER_DAY = int(os.getenv('MAX_LIKES_PER_DAY', '150'))
    MAX_RETWEETS_PER_DAY = int(os.getenv('MAX_RETWEETS_PER_DAY', '30'))
    MAX_FOLLOWS_PER_DAY = int(os.getenv('MAX_FOLLOWS_PER_DAY', '100'))
    MAX_UNFOLLOWS_PER_DAY = int(os.getenv('MAX_UNFOLLOWS_PER_DAY', '50'))
    MAX_POSTS_PER_DAY = int(os.getenv('MAX_POSTS_PER_DAY', '5'))
    MAX_REPLIES_PER_DAY = int(os.getenv('MAX_REPLIES_PER_DAY', '50'))
    MAX_DM_RESPONSES_PER_DAY = int(os.getenv('MAX_DM_RESPONSES_PER_DAY', '20'))
    
    # Behavior Settings (Optimized for speed - X has no strict action limits)
    MIN_DELAY_SECONDS = int(os.getenv('MIN_DELAY_SECONDS', '2'))  # Fast: 2-5 sec instead of 30-180
    MAX_DELAY_SECONDS = int(os.getenv('MAX_DELAY_SECONDS', '5'))
    ENGAGEMENT_SCORE_THRESHOLD = int(os.getenv('ENGAGEMENT_SCORE_THRESHOLD', '5'))
    MAX_REPLY_DRAFTS = int(os.getenv('MAX_REPLY_DRAFTS', '2'))
    MAX_POST_DRAFTS = int(os.getenv('MAX_POST_DRAFTS', '2'))
    REPLY_LANGUAGE = os.getenv('REPLY_LANGUAGE', 'en')
    MAX_RESEARCH_QUERIES = int(os.getenv('MAX_RESEARCH_QUERIES', '2'))
    MAX_RESULTS_PER_RESEARCH_QUERY = int(os.getenv('MAX_RESULTS_PER_RESEARCH_QUERY', '10'))
    MAX_TREND_TOPICS_PER_RUN = int(os.getenv('MAX_TREND_TOPICS_PER_RUN', '4'))
    TOPIC_RESEARCH_POOL_SIZE = int(os.getenv('TOPIC_RESEARCH_POOL_SIZE', '10'))
    TOPIC_RESEARCH_SAMPLE_SIZE = int(os.getenv('TOPIC_RESEARCH_SAMPLE_SIZE', '15'))
    REPLY_TARGETS_PER_TOPIC = int(os.getenv('REPLY_TARGETS_PER_TOPIC', '2'))
    LIKE_TARGETS_PER_TOPIC = int(os.getenv('LIKE_TARGETS_PER_TOPIC', '2'))
    TOPIC_DISCOVERY_LOOKBACK_DAYS = int(os.getenv('TOPIC_DISCOVERY_LOOKBACK_DAYS', '14'))
    INFLUENCER_ENGAGEMENT_TARGET = int(os.getenv('INFLUENCER_ENGAGEMENT_TARGET', '4'))
    MAX_RETWEET_QUERIES_PER_RUN = int(os.getenv('MAX_RETWEET_QUERIES_PER_RUN', '1'))
    MAX_SEARCH_CALLS_PER_RUN = int(os.getenv('MAX_SEARCH_CALLS_PER_RUN', '20'))
    DRY_RUN_MODE = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'
    DAILY_ORIGINAL_POST_ENABLED = os.getenv('DAILY_ORIGINAL_POST_ENABLED', 'true').lower() == 'true'
    FOLLOWUP_POST_ENABLED = os.getenv('FOLLOWUP_POST_ENABLED', 'true').lower() == 'true'
    MAX_FOLLOWUP_POSTS_PER_DAY = int(os.getenv('MAX_FOLLOWUP_POSTS_PER_DAY', '1'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/x-growth.log')
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        required_fields = {
            'X_BEARER_TOKEN': cls.X_BEARER_TOKEN,
            'X_CONSUMER_KEY': cls.X_CONSUMER_KEY,
            'X_CONSUMER_SECRET': cls.X_CONSUMER_SECRET,
            'X_ACCESS_TOKEN': cls.X_ACCESS_TOKEN,
            'X_ACCESS_TOKEN_SECRET': cls.X_ACCESS_TOKEN_SECRET,
            'MONGODB_URI': cls.MONGODB_URI,
        }
        
        missing = [k for k, v in required_fields.items() if not v]
        
        if missing:
            raise RuntimeError(f"❌ Missing required config: {', '.join(missing)}")
        
        # Validate OpenAI key if AI operations are used
        if not cls.OPENAI_API_KEY:
            print("⚠️ OPENAI_API_KEY not set - AI operations will fail")
        
        # Validate rate limits are positive
        if cls.MAX_LIKES_PER_DAY <= 0:
            raise ValueError("MAX_LIKES_PER_DAY must be positive")
        if cls.MAX_RETWEETS_PER_DAY <= 0:
            raise ValueError("MAX_RETWEETS_PER_DAY must be positive")
        if cls.MAX_FOLLOWS_PER_DAY <= 0:
            raise ValueError("MAX_FOLLOWS_PER_DAY must be positive")


config = Config()
