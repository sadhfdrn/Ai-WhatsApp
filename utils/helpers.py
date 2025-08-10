"""
Helper utilities for WhatsApp AI Bot
Common functions used across different modules
"""

import re
import html
import unicodedata
import hashlib
import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text for safe display and transmission
    
    Args:
        text: Input text to sanitize
        max_length: Maximum length to truncate to
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    try:
        # Remove HTML entities
        text = html.unescape(text)
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove potentially problematic characters
        text = text.replace('\u0000', '')  # Null bytes
        text = text.replace('\ufeff', '')  # BOM
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length - 3] + "..."
        
        return text
        
    except Exception as e:
        logger.error(f"❌ Text sanitization error: {e}")
        return str(text)[:max_length] if max_length else str(text)

def format_timestamp(dt: datetime, format_type: str = "readable") -> str:
    """
    Format datetime for display
    
    Args:
        dt: Datetime to format
        format_type: Type of formatting (readable, iso, compact)
    
    Returns:
        Formatted datetime string
    """
    try:
        if format_type == "readable":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "iso":
            return dt.isoformat()
        elif format_type == "compact":
            return dt.strftime("%m/%d %H:%M")
        elif format_type == "relative":
            return format_relative_time(dt)
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
            
    except Exception as e:
        logger.error(f"❌ Timestamp formatting error: {e}")
        return str(dt)

def format_relative_time(dt: datetime) -> str:
    """Format time relative to now (e.g., '5 minutes ago')"""
    try:
        now = datetime.now()
        if dt.tzinfo is not None:
            # If dt is timezone-aware, make now timezone-aware too
            import pytz
            now = now.replace(tzinfo=pytz.UTC)
        
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days < 7:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"
            
    except Exception as e:
        logger.error(f"❌ Relative time formatting error: {e}")
        return "unknown time"

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)

def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text"""
    mention_pattern = re.compile(r'@([a-zA-Z0-9_]+)')
    return mention_pattern.findall(text)

def extract_hashtags(text: str) -> List[str]:
    """Extract #hashtags from text"""
    hashtag_pattern = re.compile(r'#([a-zA-Z0-9_]+)')
    return hashtag_pattern.findall(text)

def clean_phone_number(phone: str) -> str:
    """Clean and standardize phone number format"""
    try:
        # Remove all non-numeric characters
        cleaned = re.sub(r'[^\d]', '', phone)
        
        # Remove leading zeros
        cleaned = cleaned.lstrip('0')
        
        # Add country code if missing (assume international format)
        if len(cleaned) == 10:  # US format
            cleaned = '1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            pass  # Already has US country code
        elif len(cleaned) < 10:
            logger.warning(f"⚠️ Phone number too short: {phone}")
            
        return cleaned
        
    except Exception as e:
        logger.error(f"❌ Phone cleaning error: {e}")
        return phone

def create_hash(data: Union[str, Dict, List]) -> str:
    """Create SHA256 hash of data"""
    try:
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()[:16]
        
    except Exception as e:
        logger.error(f"❌ Hash creation error: {e}")
        return "error"

def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # If this isn't the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence break
            last_period = text.rfind('.', start, end)
            last_exclaim = text.rfind('!', start, end)
            last_question = text.rfind('?', start, end)
            
            sentence_break = max(last_period, last_exclaim, last_question)
            
            if sentence_break > start:
                end = sentence_break + 1
            else:
                # Look for word break
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = max(start + 1, end - overlap)
    
    return chunks

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        import urllib.parse
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"⚠️ JSON parsing failed: {e}")
        return default

def safe_json_dumps(data: Any, default: Any = "null") -> str:
    """Safely dump JSON with fallback"""
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        logger.warning(f"⚠️ JSON serialization failed: {e}")
        return str(default)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_retries + 1} attempts")
            
            if last_exception:
                raise last_exception
            else:
                raise Exception("Unknown error occurred")
        
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_retries + 1} attempts")
            
            if last_exception:
                raise last_exception
            else:
                raise Exception("Unknown error occurred")
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def generate_unique_id(prefix: str = "") -> str:
    """Generate unique ID with optional prefix"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}" if prefix else unique_id

def parse_command_args(command_string: str) -> Dict[str, Union[str, List[str]]]:
    """Parse command string into command and arguments"""
    try:
        parts = command_string.strip().split()
        if not parts:
            return {"command": "", "args": [], "raw_args": ""}
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        raw_args = " ".join(args)
        
        return {
            "command": command,
            "args": args,
            "raw_args": raw_args
        }
        
    except Exception as e:
        logger.error(f"❌ Command parsing error: {e}")
        return {"command": "", "args": [], "raw_args": ""}

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    try:
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"
            
    except Exception:
        return "unknown"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    return text.strip()

def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())

def count_sentences(text: str) -> int:
    """Count sentences in text"""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract potential keywords from text"""
    # Simple keyword extraction - remove common words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    keywords = [word for word in words 
                if len(word) >= min_length and word not in stop_words]
    
    # Return unique keywords maintaining order
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)
    
    return unique_keywords

def is_question(text: str) -> bool:
    """Check if text appears to be a question"""
    text = text.strip()
    
    # Ends with question mark
    if text.endswith('?'):
        return True
    
    # Starts with question words
    question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 
                     'whose', 'whom', 'is', 'are', 'was', 'were', 'do', 'does', 
                     'did', 'can', 'could', 'will', 'would', 'should', 'may', 
                     'might', 'must']
    
    first_word = text.split()[0].lower() if text.split() else ""
    return first_word in question_words

async def timeout_after(seconds: float):
    """Async timeout context manager"""
    await asyncio.sleep(seconds)
    raise asyncio.TimeoutError(f"Operation timed out after {seconds}s")

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_proceed(self) -> bool:
        """Check if call can proceed without hitting rate limit"""
        now = datetime.now()
        
        # Remove old calls outside time window
        cutoff = now - timedelta(seconds=self.time_window)
        self.calls = [call_time for call_time in self.calls if call_time > cutoff]
        
        # Check if under limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def time_until_next_call(self) -> float:
        """Get seconds until next call is allowed"""
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = min(self.calls)
        time_since_oldest = (datetime.now() - oldest_call).total_seconds()
        return max(0.0, self.time_window - time_since_oldest)
