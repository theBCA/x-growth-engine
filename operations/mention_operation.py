from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from utils.sanitizer import sanitize_input
from datetime import datetime


def check_mentions(max_results: int = 10) -> int:
    """Check recent mentions and save to database."""
    mentions = tweet_handler.get_mentions(max_results=max_results)
    if not mentions:
        logger.info("ℹ No new mentions found")
        return 0
    
    logger.info(f"✓ Found {len(mentions)} mentions to review")
    
    # Save mentions to database
    for mention in mentions:
        mention_id = mention.get('id')
        
        # Check if already saved
        existing = db.mentions.find_one({"mention_id": mention_id})
        if existing:
            continue
        
        # Sanitize mention text before saving
        mention_text = sanitize_input(mention.get('text', ''))
        
        # Save mention
        db.mentions.insert_one({
            "mention_id": mention_id,
            "author_id": mention.get('author_id'),
            "text": mention_text,
            "created_at": mention.get('created_at'),
            "received_at": datetime.utcnow(),
            "responded": False
        })
        
        logger.info(f"  - From: {mention.get('author_id')} | Text: {mention_text[:50]}...")
    
    return len(mentions)
