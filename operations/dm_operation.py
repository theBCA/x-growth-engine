"""Handle direct messages with AI responses."""
from openai import OpenAI
from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from utils.sanitizer import sanitize_for_ai_prompt, validate_tweet_text
from utils.rate_limiter import RateLimiter
from datetime import datetime
from config import Config

MODEL = Config.OPENAI_MODEL
_client = None
_client_init_failed = False


def get_openai_client():
    """Lazily initialize OpenAI client to avoid import-time crashes."""
    global _client, _client_init_failed
    if _client is not None:
        return _client
    if _client_init_failed:
        return None

    try:
        _client = OpenAI(api_key=Config.OPENAI_API_KEY)
        return _client
    except Exception as e:
        _client_init_failed = True
        logger.error(f"OpenAI client initialization failed: {e}")
        logger.error("Check package compatibility (openai/httpx) and OPENAI_API_KEY")
        return None


def get_unresponded_dms(max_results: int = 10) -> list:
    """Get direct messages that haven't been responded to."""
    try:
        unresponded = list(db.mentions.find({"responded": False}).limit(max_results))
        logger.info(f"✓ Found {len(unresponded)} unresponded mentions")
        return unresponded
    except Exception as e:
        logger.error(f"Failed to get DMs: {e}")
        return []


def generate_dm_response(dm_text: str, sender_username: str) -> str:
    """Generate an intelligent DM response using OpenAI."""
    try:
        client = get_openai_client()
        if client is None:
            return None

        # Sanitize inputs before sending to AI
        dm_text = sanitize_for_ai_prompt(dm_text)
        sender_username = sanitize_for_ai_prompt(sender_username)
        
        if not dm_text or not sender_username:
            logger.warning("Empty or invalid input for DM response generation")
            return None
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are @khanorX responding to direct messages professionally and authentically.

HARD RULES (NEVER):
❌ Generate racist, sexist, homophobic, or discriminatory content
❌ Create personal attacks or harassment
❌ Provide financial/medical/legal advice - REFUSE and redirect to professional
❌ Use disclaimers like "Not advice" as loophole to give prohibited advice
❌ Spread misinformation or conspiracy theories
❌ Generate scams or malicious content
❌ Create adult content or violence
❌ Impersonate real people
❌ Disclose private information

DM RESPONSE GUIDELINES:
✅ Personal and genuine tone
✅ Concise (1-3 sentences max)
✅ Action-oriented when needed
✅ Open to further conversation
✅ Helpful but not promotional
✅ Respectful and inclusive
✅ Honest about limitations
✅ Disclose: "This is an AI response"

If asked for professional advice:
→ "I appreciate the question. For [financial/legal/medical] matters, I'd recommend consulting a professional [accountant/lawyer/doctor]."

If asked to engage in harmful content:
→ "I can't help with that. Is there something else I can assist with?"

Always maintain professionalism and respect."""
                },
                {
                    "role": "user",
                    "content": f"Generate a response to this DM from @{sender_username}:\n\n{dm_text}"
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        dm_response = response.choices[0].message.content.strip()
        
        # Validate generated response
        is_valid, message = validate_tweet_text(dm_response)
        if not is_valid:
            logger.warning(f"Generated DM response failed validation: {message}")
            return None
        
        logger.info(f"✓ Generated DM response for @{sender_username}")
        return dm_response
        
    except Exception as e:
        logger.error(f"Failed to generate DM response: {e}")
        return None


def respond_to_mentions_with_ai(max_mentions: int = 10) -> int:
    """Get mentions and respond with AI-generated replies."""
    try:
        mentions = get_unresponded_dms(max_mentions)
        if not mentions:
            return 0
        
        response_count = 0
        for mention in mentions:
            # Check rate limit before each reply
            if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
                logger.warning(f"Daily reply limit reached ({Config.MAX_REPLIES_PER_DAY})")
                break
            
            mention_id = mention.get('mention_id')
            text = mention.get('text')
            author_id = mention.get('author_id')
            
            # Generate response
            response_text = generate_dm_response(text, author_id)
            if not response_text:
                continue
            
            try:
                # Post reply
                success = tweet_handler.reply_to_tweet(mention_id, response_text)
                
                if success:
                    # Increment rate limiter
                    RateLimiter.increment("replies", Config.MAX_REPLIES_PER_DAY)
                    
                    response_count += 1
                    
                    # Mark as responded
                    db.mentions.update_one(
                        {"mention_id": mention_id},
                        {
                            "$set": {
                                "responded": True,
                                "response_text": response_text,
                                "responded_at": datetime.utcnow(),
                                "ai_generated": True
                            }
                        }
                    )
                    
                    logger.info(f"✓ Replied to mention {mention_id}")
                    
            except Exception as e:
                logger.error(f"Failed to reply to {mention_id}: {e}")
        
        logger.info(f"✓ Responded to {response_count}/{len(mentions)} mentions with AI")
        return response_count
        
    except Exception as e:
        logger.error(f"Failed to process AI mentions: {e}")
        return 0
