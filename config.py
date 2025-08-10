"""
Configuration management for WhatsApp AI Bot
Handles environment variables and default settings
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the WhatsApp AI bot"""
    
    def __init__(self):
        # WhatsApp Configuration
        self.WHATSAPP_CREDS = self._get_whatsapp_creds()
        self.BOT_NAME = os.getenv("BOT_NAME", "AI Assistant 🤖")
        self.BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
        
        # AI Model Configuration
        self.AI_MODELS = {
            # Core conversation (300MB)
            "main_chat": "microsoft/DialoGPT-small",
            
            # Text generation & tasks (300MB) 
            "text_generation": "google/flan-t5-small",
            
            # Translation - covers 100+ languages (300MB)
            "translation": "Helsinki-NLP/opus-mt-en-mul",
            
            # Sentiment & emotion detection (500MB)
            "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest",
            
            # Text embeddings for similarity (80MB)
            "embeddings": "sentence-transformers/all-MiniLM-L6-v2"
        }
        
        self.AI_MODEL = os.getenv("AI_MODEL", self.AI_MODELS["main_chat"])
        self.MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "500"))
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
        self.USE_STREAMING = os.getenv("USE_STREAMING", "true").lower() == "true"
        
        # Timezone Configuration
        self.TIMEZONE = os.getenv("TIMEZONE", "Africa/Lagos")
        self.LOCALE = os.getenv("LOCALE", "en_NG")
        
        # Language Detection and Translation
        self.AUTO_TRANSLATE = os.getenv("AUTO_TRANSLATE", "true").lower() == "true"
        self.TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")
        self.SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ar", "hi", "yo", "ig", "ha"]
        
        # Voice Configuration (DISABLED for cloud deployment)
        self.TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en")
        self.VOICE_ENABLED = os.getenv("VOICE_ENABLED", "false").lower() == "true"  # Default disabled
        self.VOICE_SPEED = float(os.getenv("VOICE_SPEED", "1.0"))
        
        # Web Search Configuration - SearXNG instances  
        self.SEARXNG_URL = os.getenv("SEARXNG_URL", "https://searx.tiekoetter.com")
        self.SEARCH_ENABLED = os.getenv("SEARCH_ENABLED", "true").lower() == "true"
        self.MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
        self.AUTO_SEARCH_ON_QUESTIONS = os.getenv("AUTO_SEARCH_ON_QUESTIONS", "true").lower() == "true"
        
        # AI Model Performance Configuration
        self.LOW_MEMORY_MODE = os.getenv("LOW_MEMORY_MODE", "true").lower() == "true"  # Default true for Replit
        
        # Database Configuration
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        
        # Your WhatsApp User ID for style learning
        self.YOUR_USER_ID = os.getenv("YOUR_USER_ID", "your_phone_number@c.us")  # Replace with your actual WhatsApp ID
        
        # Auto-reply Configuration
        self.AUTO_REPLY_ENABLED = os.getenv("AUTO_REPLY_ENABLED", "false").lower() == "true"
        self.AUTO_REPLY_DELAY_MIN = int(os.getenv("AUTO_REPLY_DELAY_MIN", "5"))
        self.AUTO_REPLY_DELAY_MAX = int(os.getenv("AUTO_REPLY_DELAY_MAX", "15"))
        
        # Personality Configuration
        self.PERSONALITY_MODE = os.getenv("PERSONALITY_MODE", "humorous")
        self.JOKE_FREQUENCY = float(os.getenv("JOKE_FREQUENCY", "0.3"))
        self.PROACTIVE_MESSAGING = os.getenv("PROACTIVE_MESSAGING", "false").lower() == "true"
        
        # Feature Toggles
        self.MEME_GENERATION = os.getenv("MEME_GENERATION", "true").lower() == "true"
        self.ASCII_ART = os.getenv("ASCII_ART", "true").lower() == "true"
        self.TRANSLATION = os.getenv("TRANSLATION", "true").lower() == "true"
        self.CHAT_ANALYSIS = os.getenv("CHAT_ANALYSIS", "true").lower() == "true"
        
        # GitHub Actions Configuration
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.WORKFLOW_TIMEOUT = int(os.getenv("WORKFLOW_TIMEOUT", "18000"))  # 5 hours in seconds
        
        # Resource Optimization
        self.LOW_MEMORY_MODE = os.getenv("LOW_MEMORY_MODE", "true").lower() == "true"
        self.CACHE_SIZE = int(os.getenv("CACHE_SIZE", "100"))
        
        logger.info("⚙️ Configuration loaded successfully")
    
    def _get_whatsapp_creds(self) -> Optional[Dict[str, Any]]:
        """Load WhatsApp credentials from environment variable"""
        creds_str = os.getenv("WHATSAPP_CREDS")
        
        if not creds_str:
            logger.error("❌ WHATSAPP_CREDS environment variable not found")
            return None
            
        try:
            creds = json.loads(creds_str)
            logger.info("✅ WhatsApp credentials loaded successfully")
            return creds
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse WhatsApp credentials: {e}")
            return None
    
    def get_personality_settings(self) -> Dict[str, Any]:
        """Get personality configuration"""
        return {
            "mode": self.PERSONALITY_MODE,
            "joke_frequency": self.JOKE_FREQUENCY,
            "proactive": self.PROACTIVE_MESSAGING,
            "take_charge": True,
            "humor_level": "high",
            "interaction_style": "engaging"
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get enabled features"""
        return {
            "voice": self.VOICE_ENABLED,
            "search": self.SEARCH_ENABLED,
            "memes": self.MEME_GENERATION,
            "ascii_art": self.ASCII_ART,
            "translation": self.TRANSLATION,
            "chat_analysis": self.CHAT_ANALYSIS,
            "auto_reply": self.AUTO_REPLY_ENABLED
        }
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.WHATSAPP_CREDS:
            logger.error("❌ WhatsApp credentials are required")
            return False
            
        if not self.AI_MODEL:
            logger.error("❌ AI model configuration is required")
            return False
            
        logger.info("✅ Configuration validation passed")
        return True
