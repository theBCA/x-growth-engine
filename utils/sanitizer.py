"""Input sanitization and validation utilities."""
import re
from utils.logger import logger


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text safe for processing
    """
    if not text:
        return ""
    
    # 1. Limit length
    if len(text) > max_length:
        logger.warning(f"Input truncated from {len(text)} to {max_length} chars")
        text = text[:max_length]
    
    # 2. Remove control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # 3. Remove potential command injection patterns
    dangerous_patterns = [
        r';\s*rm\s+-rf',  # rm -rf
        r';\s*DROP\s+TABLE',  # SQL injection
        r'<script',  # XSS
        r'javascript:',  # XSS
        r'\$\(.*\)',  # Command substitution
        r'`.*`',  # Backtick execution
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected and removed: {pattern}")
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 4. Normalize whitespace
    text = ' '.join(text.split())
    
    return text


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent injection attacks.
    
    Args:
        query: Search query to sanitize
        
    Returns:
        Sanitized query safe for API use
    """
    if not query:
        return ""
    
    # Allow X query operators/syntax too (e.g., -is:retweet, quotes, parens).
    query = re.sub(r'[^\w\s\-#@.,!?:\"()]', '', query)
    
    # Limit length
    query = query[:100]
    
    # Remove multiple spaces
    query = ' '.join(query.split())
    
    return query


def validate_tweet_text(text: str) -> tuple[bool, str]:
    """
    Validate tweet text meets requirements.
    
    Args:
        text: Tweet text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Tweet text cannot be empty"
    
    if len(text) > 280:
        return False, f"Tweet too long: {len(text)} chars (max 280)"
    
    if len(text.strip()) == 0:
        return False, "Tweet contains only whitespace"
    
    # Check for excessive repetition (spam indicator)
    words = text.split()
    if len(words) > 0:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        max_repetition = max(word_counts.values())
        if max_repetition > len(words) * 0.5:  # More than 50% same word
            return False, "Excessive word repetition detected"
    
    return True, ""


def sanitize_for_ai_prompt(text: str) -> str:
    """
    Sanitize text before passing to AI to prevent prompt injection.
    
    Args:
        text: User-provided text
        
    Returns:
        Sanitized text safe for AI prompts
    """
    # First, basic sanitization
    text = sanitize_input(text, max_length=2000)
    
    # Remove prompt injection attempts
    injection_patterns = [
        r'ignore\s+all\s+previous\s+instructions',
        r'disregard\s+.*\s+instructions',
        r'you\s+are\s+now',
        r'new\s+instructions:',
        r'system\s*:',
        r'assistant\s*:',
        r'<\|.*\|>',  # Special tokens
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Prompt injection attempt detected: {pattern}")
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
    
    return text


def validate_username(username: str) -> bool:
    """
    Validate Twitter username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Twitter username: 1-15 chars, alphanumeric + underscore
    pattern = r'^[A-Za-z0-9_]{1,15}$'
    return bool(re.match(pattern, username))


def sanitize_tweet_id(tweet_id: str) -> str:
    """
    Sanitize tweet ID to ensure it's a valid numeric ID.
    
    Args:
        tweet_id: Tweet ID to sanitize
        
    Returns:
        Sanitized tweet ID or empty string if invalid
    """
    # Tweet IDs are numeric strings
    if not tweet_id or not tweet_id.isdigit():
        logger.warning(f"Invalid tweet ID format: {tweet_id}")
        return ""
    
    # Tweet IDs are typically 18-19 digits
    if len(tweet_id) > 20:
        logger.warning(f"Tweet ID too long: {tweet_id}")
        return ""
    
    return tweet_id
