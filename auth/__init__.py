import tweepy
from config import config
from utils.logger import logger


class XAuthenticator:
    """Handles X API authentication."""
    
    def __init__(self):
        self.api: tweepy.API = None
        self.client: tweepy.Client = None
        
    def authenticate(self) -> tuple[tweepy.API, tweepy.Client]:
        """
        Authenticate with X API using OAuth 1.0a credentials.
        Returns both API v1.1 and v2 clients.
        """
        try:
            # OAuth 1.0a authentication
            auth = tweepy.OAuth1UserHandler(
                consumer_key=config.X_CONSUMER_KEY,
                consumer_secret=config.X_CONSUMER_SECRET,
                access_token=config.X_ACCESS_TOKEN,
                access_token_secret=config.X_ACCESS_TOKEN_SECRET
            )
            
            # API v1.1 (for some operations not yet in v2)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # API v2 (modern API)
            self.client = tweepy.Client(
                bearer_token=config.X_BEARER_TOKEN if config.X_BEARER_TOKEN else None,
                consumer_key=config.X_CONSUMER_KEY,
                consumer_secret=config.X_CONSUMER_SECRET,
                access_token=config.X_ACCESS_TOKEN,
                access_token_secret=config.X_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            
            # Verify credentials
            user = self.api.verify_credentials()
            logger.info(f"✓ Authenticated as @{user.screen_name}")
            logger.info(f"  Followers: {user.followers_count} | Following: {user.friends_count}")
            
            return self.api, self.client
            
        except tweepy.TweepyException as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise


# Global authenticator instance
auth = XAuthenticator()
