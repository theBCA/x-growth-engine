"""AI-powered operations using OpenAI."""
from openai import OpenAI
from tweet_handler import tweet_handler
from utils.logger import logger
from database import db
from utils.sanitizer import sanitize_for_ai_prompt, validate_tweet_text
from utils.rate_limiter import RateLimiter
from datetime import datetime
from config import Config

MODEL = Config.OPENAI_MODEL  # Configurable via .env
_client = None
_client_init_failed = False


def is_low_value_text(text: str) -> bool:
    """Basic quality gate to block generic, low-value output."""
    if not text:
        return True
    lowered = text.lower().strip()
    generic_patterns = [
        "great point",
        "totally agree",
        "that's interesting",
        "thanks for sharing",
        "nice post",
    ]
    if any(p in lowered for p in generic_patterns):
        return True

    words = [w for w in lowered.split() if w.isalpha() or w.replace("?", "").isalpha()]
    if len(words) < 7:
        return True

    # Value signals: question, tradeoff, metric, action framing
    value_signals = ["?", "tradeoff", "metric", "measure", "test", "pilot", "rollout", "risk", "impact"]
    return not any(v in lowered for v in value_signals)


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


def generate_ai_reply(
    tweet_text: str,
    tweet_author: str,
    max_tokens: int = 100,
    angle: str = "conversational",
    response_mode: str = "mixed",
) -> str:
    """Generate an intelligent reply to a tweet using OpenAI with varied angles."""
    try:
        client = get_openai_client()
        if client is None:
            return None

        tweet_text = sanitize_for_ai_prompt(tweet_text)
        tweet_author = sanitize_for_ai_prompt(tweet_author)
        
        if not tweet_text or not tweet_author:
            logger.warning("Empty or invalid input for AI reply generation")
            return None
        
        angle_prompts = {
            "conversational": "Reply naturally, like a real person having a conversation. Be friendly and add your own perspective.",
            "questioning": "Ask a thoughtful, specific question that deepens the conversation. Show genuine curiosity.",
            "agreeing": "Agree with their point and add a fresh angle or example they haven't mentioned.",
            "contrasting": "Respectfully present a different viewpoint or consideration. Be diplomatic and thoughtful.",
            "curious": "Express genuine curiosity and ask for elaboration on a specific detail.",
            "supportive": "Show support and offer a concrete insight or suggestion that adds value."
        }
        mode_prompts = {
            "statement": (
                "Prefer a declarative statement with a concrete take. "
                "Do not end with a question unless absolutely necessary."
            ),
            "question": "Ask one focused, high-signal question.",
            "mixed": "Mix statement and question naturally; avoid forcing a question every time.",
        }
        
        angle_instruction = angle_prompts.get(angle, angle_prompts["conversational"])
        mode_instruction = mode_prompts.get(response_mode, mode_prompts["mixed"])
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are @khanorX replying to tweets. Sound like a REAL human, not a bot.

CRITICAL - AVOID REPETITION:
- NEVER start with "That's interesting/intriguing/fascinating"
- VARY your sentence structures completely
- NO generic phrases like "Great point!" or "Totally agree!"
- Each reply must be UNIQUE in style and wording
- Mix short and long sentences
- Sometimes start with a question, sometimes a statement
- Use varied vocabulary - don't repeat words

STYLE GUIDELINES:
- Be authentic and conversational
- Add your own specific insight or question
- Must provide one concrete value element:
  1) a concrete observation, OR
  2) a practical next step, OR
  3) one tradeoff/metric to watch, OR
  4) a diagnostic question
- Keep under 200 characters
- Use 0-1 emoji max (not always)
- Sound like you're texting a friend, not writing formally
- Be respectful but casual
- Reply language must be: {Config.REPLY_LANGUAGE}. Never switch to other languages.

CURRENT ANGLE: {angle_instruction}
RESPONSE MODE: {mode_instruction}

EXAMPLES OF VARIETY:
- "Wait, how would that work with...?"
- "Never thought about it that way."
- "This reminds me of..."
- "Curious - what's your take on...?"
- "Fair point, though I wonder..."

NO generic templates. Make it fresh."""
                },
                {
                    "role": "user",
                    "content": (
                        f"Reply to @{tweet_author}'s tweet:\n{tweet_text}\n\n"
                        f"Angle: {angle_instruction}\n"
                        f"Mode: {mode_instruction}\n"
                        f"Make it unique, under 200 chars, authentic, concretely useful, and strictly in {Config.REPLY_LANGUAGE}."
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=0.9  # Higher temperature for more variety
        )
        
        reply = response.choices[0].message.content.strip()
        is_valid, message = validate_tweet_text(reply)
        if not is_valid:
            logger.warning(f"Generated reply failed validation: {message}")
            return None
        if is_low_value_text(reply):
            logger.warning("Generated reply rejected: low value/generic")
            return None
        
        logger.info(f"✓ Generated AI reply: {reply[:50]}...")
        return reply
        
    except Exception as e:
        logger.error(f"Failed to generate AI reply: {e}")
        return None


def generate_ai_tweet(topic: str, niche: str = "", max_tokens: int = 100, angle: str = "educational") -> str:
    """Generate an original tweet about a topic using OpenAI with varied angles."""
    try:
        client = get_openai_client()
        if client is None:
            return None

        topic = sanitize_for_ai_prompt(topic)
        if not niche:
            niche = (Config.NICHE[0].strip() if Config.NICHE else "technology") or "technology"
        niche = sanitize_for_ai_prompt(niche)
        
        if not topic or not niche:
            logger.warning("Empty or invalid input for AI tweet generation")
            return None
        
        angle_prompts = {
            "educational": "Explain clearly. Make it informative and eye-opening.",
            "conversational": "Ask a question or share a personal take. Be casual.",
            "critical": "Share a critical perspective. Challenge assumptions.",
            "news": "Comment on recent developments or emerging trends.",
            "practical": "Share actionable advice, tips, or best practices.",
            "insights": "Share a surprising insight that makes people think."
        }
        
        angle_instruction = angle_prompts.get(angle, angle_prompts["educational"])
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are @khanorX, expert in {niche}. Write diverse, authentic tweets.

CRITICAL - SOUND HUMAN, NOT BOT:
- Vary angles, tones, perspectives  
- Don't repeat similar points
- Mix styles: questions, statements, insights, tips
- Use complete hashtags only (no "#..")
- MUST BE under 270 characters
- Professional but conversational
- Every tweet must include concrete value:
  1) one specific insight, and
  2) one practical action, example, or metric

BOUNDARIES - NEVER:
- Racist, sexist, homophobic content
- Financial/medical/legal advice
- Misinformation or conspiracy theories
- Personal attacks or harassment
- Adult content or violence

CONTENT RULES:
- Stay tightly on-topic for the niche: {niche}
- Prioritize practical and educational value
- Avoid hype/shilling and unverifiable claims"""
                },
                {
                    "role": "user",
                    "content": f"Write ONE tweet about: {topic}\nAngle: {angle_instruction}\nMust be under 270 chars, unique, human-sounding, and practically useful."
                }
            ],
            max_tokens=max_tokens,
            temperature=0.8
        )
        
        tweet = response.choices[0].message.content.strip()
        
        if not tweet or len(tweet) == 0:
            logger.warning("Generated tweet is empty")
            return None
        
        is_valid, message = validate_tweet_text(tweet)
        if not is_valid:
            logger.debug(f"Validation warning: {message}, attempting to trim")
            if len(tweet) > 280:
                words = tweet.split()
                trimmed = []
                char_count = 0
                for word in words:
                    if char_count + len(word) + 1 <= 270:
                        trimmed.append(word)
                        char_count += len(word) + 1
                    else:
                        break
                if trimmed:
                    tweet = " ".join(trimmed)
        if is_low_value_text(tweet):
            logger.warning("Generated tweet rejected: low value/generic")
            return None
        
        logger.info(f"✓ Generated AI tweet: {tweet[:80]}...")
        return tweet
        
    except Exception as e:
        logger.error(f"Failed to generate AI tweet: {e}")
        return None


def generate_ai_thread(topic: str, num_tweets: int = 5) -> list:
    """Generate a multi-tweet thread using OpenAI."""
    try:
        client = get_openai_client()
        if client is None:
            return []

        topic = sanitize_for_ai_prompt(topic)
        
        if not topic:
            logger.warning("Empty or invalid topic for AI thread generation")
            return []
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are @khanorX creating an educational {num_tweets}-tweet thread.

THREAD STRUCTURE:
- Start with compelling hook
- Each tweet under 280 characters
- Flow naturally and build on each other
- End with clear takeaway
- Number each tweet (1/{num_tweets}, etc.)
- Include 2-3 relevant emoji total

COMPLIANCE:
- NO racist, sexist, homophobic content
- NO misinformation or conspiracy theories
- NO financial/medical/legal advice
- NO personal attacks or harassment
- NO adult content or violence
- Be transparent: "This was written by AI"
- Cite sources for factual claims"""
                },
                {
                    "role": "user",
                    "content": f"Create a {num_tweets}-tweet thread about: {topic}"
                }
            ],
            max_tokens=500,
            temperature=0.8
        )
        
        content = response.choices[0].message.content.strip()
        tweets = [t.strip() for t in content.split('\n') if t.strip()]
        
        valid_tweets = []
        for tweet in tweets[:num_tweets]:
            is_valid, _ = validate_tweet_text(tweet)
            if is_valid:
                valid_tweets.append(tweet)
        
        logger.info(f"✓ Generated {len(valid_tweets)} valid tweets for thread")
        return valid_tweets
        
    except Exception as e:
        logger.error(f"Failed to generate thread: {e}")
        return []


def _split_for_continuation(text: str, max_len: int = 270) -> list:
    """Split long text into tweet-sized chunks for continuation replies."""
    if not text:
        return []
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for w in words:
        add_len = len(w) + (1 if current else 0)
        if current_len + add_len <= max_len:
            current.append(w)
            current_len += add_len
        else:
            chunks.append(" ".join(current))
            current = [w]
            current_len = len(w)
    if current:
        chunks.append(" ".join(current))
    return chunks


def generate_ai_structured_post(topic: str, niche: str = "", max_tokens: int = 220) -> str:
    """Generate a high-signal structured post: problem -> tried -> result -> takeaway."""
    try:
        client = get_openai_client()
        if client is None:
            return None

        topic = sanitize_for_ai_prompt(topic)
        if not niche:
            niche = (Config.NICHE[0].strip() if Config.NICHE else "technology") or "technology"
        niche = sanitize_for_ai_prompt(niche)
        if not topic or not niche:
            return None

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are @khanorX writing practical posts for {niche}.

Write in this exact order:
Problem: ...
Tried: ...
Result: ... (include one concrete metric or observable outcome)
Takeaway: ...

Rules:
- Be specific and actionable.
- No hype, no vague statements.
- Natural human tone.
- If needed, write longer than 280 chars (it will be continued in replies)."""
                },
                {
                    "role": "user",
                    "content": f"Create one structured post on: {topic}"
                },
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )

        text = response.choices[0].message.content.strip()
        if not text or is_low_value_text(text):
            return None
        return text
    except Exception as e:
        logger.error(f"Failed to generate structured post: {e}")
        return None


def post_text_with_continuation(text: str, topic: str, niche: str = "", post_type: str = "daily_lane") -> int:
    """Post text and continue as ++ replies if it exceeds one tweet."""
    try:
        if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
            logger.warning(f"Daily post limit reached ({Config.MAX_POSTS_PER_DAY})")
            return 0

        chunks = _split_for_continuation(text, max_len=270)
        if not chunks:
            return 0

        first = chunks[0]
        is_valid, msg = validate_tweet_text(first)
        if not is_valid:
            logger.warning(f"Structured post first chunk invalid: {msg}")
            return 0

        root_id = tweet_handler.post_tweet(first)
        if not root_id:
            return 0
        RateLimiter.increment("posts", Config.MAX_POSTS_PER_DAY)

        posted = 1
        parent_id = root_id
        for chunk in chunks[1:]:
            if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
                logger.warning("Reply limit reached while continuing post")
                break
            reply_chunk = f"++ {chunk}"
            is_valid, _ = validate_tweet_text(reply_chunk)
            if not is_valid:
                continue
            if tweet_handler.reply_to_tweet(parent_id, reply_chunk):
                RateLimiter.increment("replies", Config.MAX_REPLIES_PER_DAY)
                posted += 1
            else:
                break

        db.posts.insert_one({
            "post_id": root_id,
            "text": chunks[0],
            "full_text": text,
            "chunks": posted,
            "posted_at": datetime.utcnow(),
            "ai_generated": True,
            "topic": topic,
            "niche": niche,
            "post_type": post_type,
        })
        db.activity_logs.insert_one({
            "action": "post",
            "target_id": root_id,
            "target_type": "tweet",
            "timestamp": datetime.utcnow(),
            "success": True,
            "metadata": {
                "topic": topic,
                "niche": niche,
                "post_type": post_type,
                "chunks": posted,
            }
        })
        logger.info(f"✓ Posted structured content in {posted} part(s)")
        return posted
    except Exception as e:
        logger.error(f"Failed posting structured content: {e}")
        return 0


def post_ai_generated_tweet(topic: str, niche: str = "") -> bool:
    """Generate and post an AI tweet."""
    try:
        if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
            logger.warning(f"Daily post limit reached ({Config.MAX_POSTS_PER_DAY})")
            return False
        
        effective_niche = niche or ((Config.NICHE[0].strip() if Config.NICHE else "technology") or "technology")
        tweet_text = generate_ai_tweet(topic, effective_niche)
        if not tweet_text:
            return False
        
        tweet_id = tweet_handler.post_tweet(tweet_text)
        if tweet_id:
            RateLimiter.increment("posts", Config.MAX_POSTS_PER_DAY)
            db.posts.insert_one({
                "post_id": tweet_id,
                "text": tweet_text,
                "posted_at": datetime.utcnow(),
                "ai_generated": True,
                "topic": topic
            })
            db.activity_logs.insert_one({
                "action": "post",
                "target_id": tweet_id,
                "target_type": "tweet",
                "timestamp": datetime.utcnow(),
                "success": True,
                "metadata": {
                    "topic": topic,
                    "niche": effective_niche,
                    "post_type": "single",
                }
            })
            logger.info(f"✓ Posted AI-generated tweet")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to post AI tweet: {e}")
        return False


def post_ai_thread(topic: str) -> int:
    """Generate and post an AI thread."""
    try:
        tweets = generate_ai_thread(topic, num_tweets=5)
        if not tweets:
            return 0
        
        posted_count = 0
        parent_tweet_id = None
        
        for i, tweet_text in enumerate(tweets):
            try:
                if i == 0:
                    if not RateLimiter.check_limit("posts", Config.MAX_POSTS_PER_DAY):
                        logger.warning(f"Daily post limit reached ({Config.MAX_POSTS_PER_DAY})")
                        break
                    tweet_id = tweet_handler.post_tweet(tweet_text)
                    if tweet_id:
                        RateLimiter.increment("posts", Config.MAX_POSTS_PER_DAY)
                        parent_tweet_id = tweet_id
                else:
                    if not RateLimiter.check_limit("replies", Config.MAX_REPLIES_PER_DAY):
                        logger.warning(f"Daily reply limit reached ({Config.MAX_REPLIES_PER_DAY})")
                        break
                    tweet_id = tweet_handler.reply_to_tweet(parent_tweet_id, tweet_text)
                    if tweet_id:
                        RateLimiter.increment("replies", Config.MAX_REPLIES_PER_DAY)
                        parent_tweet_id = tweet_id
                
                if tweet_id:
                    posted_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to post tweet {i+1}: {e}")
        
        logger.info(f"✓ Posted {posted_count}/{len(tweets)} tweets in thread")
        return posted_count
        
    except Exception as e:
        logger.error(f"Failed to post thread: {e}")
        return 0


def analyze_tweet_performance() -> dict:
    """Analyze recent tweet performance and get insights."""
    try:
        recent_tweets = list(db.posts.find().sort("posted_at", -1).limit(10))
        
        if not recent_tweets:
            return {"tweets_analyzed": 0}
        
        analysis = {
            "tweets_analyzed": len(recent_tweets),
            "avg_engagement": 0,
            "best_performing": None,
            "posting_times": [],
        }
        
        total_engagement = 0
        for tweet in recent_tweets:
            engagement = tweet.get("likes", 0) + tweet.get("retweets", 0)
            total_engagement += engagement
            
            if not analysis["best_performing"] or engagement > analysis["best_performing"]["engagement"]:
                analysis["best_performing"] = {
                    "text": tweet.get("text", "")[:50],
                    "engagement": engagement
                }
            
            analysis["posting_times"].append(tweet["posted_at"].strftime("%H:%M"))
        
        analysis["avg_engagement"] = total_engagement / len(recent_tweets)
        logger.info(f"✓ Analyzed {len(recent_tweets)} tweets")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        return {}
