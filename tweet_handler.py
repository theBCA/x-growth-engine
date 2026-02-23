import tweepy
from typing import Optional, List, Dict, Any
from auth import auth
from config import Config
from utils.logger import logger
from datetime import datetime

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    logger.warning("tenacity is not installed; retry decorators are disabled")

    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None

    def retry_if_exception_type(*args, **kwargs):
        return None


class TweetHandler:
    """Handles all tweet operations for X API."""
    
    def __init__(self):
        self.api, self.client = auth.authenticate()
        self._search_calls_this_run = 0
    
    # ========== POST OPERATIONS ==========
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def post_tweet(self, text: str) -> Optional[str]:
        """Post a new tweet. Returns tweet ID on success."""
        try:
            if Config.DRY_RUN_MODE:
                dry_id = f"dry_{int(datetime.utcnow().timestamp())}"
                logger.info(f"[DRY_RUN] Would post tweet: {text[:120]}...")
                return dry_id
            response = self.client.create_tweet(text=text)
            tweet_id = response.data['id']
            logger.info(f"✓ Tweet posted. ID: {tweet_id}")
            return tweet_id
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def reply_to_tweet(self, tweet_id: str, text: str) -> bool:
        """Reply to a specific tweet."""
        try:
            if Config.DRY_RUN_MODE:
                logger.info(f"[DRY_RUN] Would reply to {tweet_id}: {text[:120]}...")
                return True
            self.client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
            logger.info(f"✓ Replied to tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reply: {e}")
            return False
    
    # ========== INTERACTION OPERATIONS ==========
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet."""
        try:
            if Config.DRY_RUN_MODE:
                logger.info(f"[DRY_RUN] Would like tweet {tweet_id}")
                return True
            self.client.like(tweet_id)
            logger.info(f"✓ Liked tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to like tweet: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet."""
        try:
            if Config.DRY_RUN_MODE:
                logger.info(f"[DRY_RUN] Would retweet {tweet_id}")
                return True
            self.client.retweet(tweet_id)
            logger.info(f"✓ Retweeted {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to retweet: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def follow_user(self, user_id: str) -> bool:
        """Follow a user."""
        try:
            if Config.DRY_RUN_MODE:
                logger.info(f"[DRY_RUN] Would follow user {user_id}")
                return True
            self.client.follow_user(user_id)
            logger.info(f"✓ Followed user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to follow user: {e}")
            return False
    
    # ========== SEARCH & RETRIEVE OPERATIONS ==========
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def get_mentions(self, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get recent mentions of the bot."""
        try:
            user = self.api.verify_credentials()
            response = self.client.get_users_mentions(
                id=user.id_str,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'public_metrics']
            )
            if response.data:
                logger.info(f"✓ Retrieved {len(response.data)} mentions")
                return response.data
            return None
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def search_tweets(self, query: str, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Search for tweets by query."""
        try:
            if self._search_calls_this_run >= Config.MAX_SEARCH_CALLS_PER_RUN:
                logger.warning(
                    f"Skipping search for '{query}' - per-run search budget reached "
                    f"({self._search_calls_this_run}/{Config.MAX_SEARCH_CALLS_PER_RUN})"
                )
                return None

            # Enforce X API bounds defensively.
            bounded_results = min(100, max(10, int(max_results)))
            self._search_calls_this_run += 1
            response = self.client.search_recent_tweets(
                query=query,
                max_results=bounded_results,
                tweet_fields=['created_at', 'author_id', 'public_metrics'],
                expansions=['author_id'],
                user_fields=['created_at', 'public_metrics', 'verified', 'description']
            )
            if response.data:
                # Add user info to each tweet
                tweets = []
                users_dict = {}
                if response.includes and 'users' in response.includes:
                    users_dict = {user.id: user for user in response.includes['users']}
                
                for tweet in response.data:
                    tweet_dict = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'author_id': tweet.author_id,
                        'public_metrics': tweet.public_metrics
                    }
                    if tweet.author_id in users_dict:
                        user = users_dict[tweet.author_id]
                        tweet_dict['author_info'] = {
                            'username': user.username,
                            'followers_count': user.public_metrics['followers_count'],
                            'following_count': user.public_metrics['following_count'],
                            'tweet_count': user.public_metrics['tweet_count'],
                            'verified': user.verified if hasattr(user, 'verified') else False,
                            'description': user.description if hasattr(user, 'description') else '',
                            'account_age_days': (datetime.utcnow() - user.created_at.replace(tzinfo=None)).days if hasattr(user, 'created_at') and user.created_at else 0
                        }
                    tweets.append(tweet_dict)
                
                logger.info(f"✓ Found {len(tweets)} tweets for: {query}")
                return tweets
            return None
        except Exception as e:
            logger.error(f"Failed to search tweets: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def get_tweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tweet by ID."""
        try:
            response = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=['created_at', 'author_id', 'public_metrics']
            )
            logger.info(f"✓ Retrieved tweet {tweet_id}")
            return response.data
        except Exception as e:
            logger.error(f"Failed to get tweet: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def get_trending_topics(self) -> Optional[List[Dict[str, Any]]]:
        """Get worldwide trending topics."""
        try:
            trends = self.api.get_place_trends(id=1)  # 1 = worldwide
            if trends:
                logger.info(f"✓ Retrieved {len(trends[0]['trends'])} trending topics")
                return trends[0]['trends']
            return None
        except Exception as e:
            logger.error(f"Failed to get trends: {e}")
            return None
    
    # ========== ANALYTICS OPERATIONS ==========
    def analyze_tweet_engagement(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a tweet's engagement metrics."""
        try:
            metrics = tweet.get('public_metrics', {})
            likes = metrics.get('like_count', 0)
            retweets = metrics.get('retweet_count', 0)
            replies = metrics.get('reply_count', 0)
            impressions = metrics.get('impression_count', 1)
            
            engagement_rate = ((likes + retweets + replies) / impressions * 100) if impressions > 0 else 0
            
            return {
                'tweet_id': tweet.get('id'),
                'text': tweet.get('text'),
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'impressions': impressions,
                'engagement_rate': round(engagement_rate, 2)
            }
        except Exception as e:
            logger.error(f"Failed to analyze tweet: {e}")
            return {}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((tweepy.TweepyException, Exception)),
        reraise=True
    )
    def get_account_stats(self) -> Optional[Dict[str, Any]]:
        """Get current account statistics."""
        try:
            user = self.api.verify_credentials()
            return {
                'username': user.screen_name,
                'followers': user.followers_count,
                'following': user.friends_count,
                'tweets': user.statuses_count,
                'verified': user.verified
            }
        except Exception as e:
            logger.error(f"Failed to get account stats: {e}")
            return None


# Global instance
tweet_handler = TweetHandler()
