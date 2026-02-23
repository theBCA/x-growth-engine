"""Delay utilities for human-like behavior."""
import random
import time
from config import config
from utils.logger import logger


def random_delay(min_seconds: int = None, max_seconds: int = None) -> None:
    """Sleep for a random amount of time to mimic human behavior."""
    min_sec = min_seconds or config.MIN_DELAY_SECONDS
    max_sec = max_seconds or config.MAX_DELAY_SECONDS
    
    delay = random.randint(min_sec, max_sec)
    logger.debug(f"Waiting {delay} seconds...")
    time.sleep(delay)


def calculate_engagement_score(likes: int, retweets: int, replies: int) -> int:
    """Calculate engagement score for a tweet."""
    return (likes * 1) + (retweets * 2) + (replies * 3)
