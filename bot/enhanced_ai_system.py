"""
Enhanced AI System for WhatsApp Bot
Handles multiple AI models, web search, timezone, and translation
"""

import os
import json
import logging
import asyncio
import random
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import traceback

# Import dependencies with fallbacks
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    
try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        AutoModelForSeq2SeqLM, pipeline,
        T5ForConditionalGeneration, T5Tokenizer
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from bot.web_search import WebSearchHandler
from config import Config

logger = logging.getLogger(__name__)

class EnhancedAISystem:
    """Enhanced AI system with multiple models and advanced features"""
    
    def __init__(self, config: Config):
        self.config = config
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.web_search = WebSearchHandler(config)
        
        # Initialize timezone
        self.timezone = self._setup_timezone()
        
        # Conversation context
        self.conversation_history = {}
        self.max_history_length = 10
        
        # Initialize models
        self._initialize_models()
        
        logger.info("🤖 Enhanced AI System initialized")
    
    def _setup_timezone(self):
        """Setup timezone for time-related queries"""
        if not PYTZ_AVAILABLE:
            logger.warning("⚠️ pytz not available, using system timezone")
            return None
            
        try:
            return pytz.timezone(self.config.TIMEZONE)
        except Exception as e:
            logger.warning(f"⚠️ Invalid timezone {self.config.TIMEZONE}, using UTC: {e}")
            return pytz.UTC
    
    def _initialize_models(self):
        """Initialize AI models based on availability"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ Transformers not available, using fallback responses")
            return
            
        # Initialize models based on availability and memory settings
        low_memory = getattr(self.config, 'LOW_MEMORY_MODE', True)  # Default to low memory for Replit
        
        if not low_memory and TRANSFORMERS_AVAILABLE:
            self._load_conversation_model()
            self._load_translation_model()
            self._load_sentiment_model()
            
        if SENTENCE_TRANSFORMERS_AVAILABLE and not low_memory:
            self._load_embeddings_model()
        
        logger.info(f"🧠 AI models initialized (low_memory={low_memory})")
    
    def _load_conversation_model(self):
        """Load conversation model"""
        try:
            model_name = self.config.AI_MODELS["main_chat"]
            logger.info(f"🔄 Loading conversation model: {model_name}")
            
            self.tokenizers["chat"] = AutoTokenizer.from_pretrained(model_name, padding_side='left')
            self.models["chat"] = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            if self.tokenizers["chat"].pad_token is None:
                self.tokenizers["chat"].pad_token = self.tokenizers["chat"].eos_token
                
            logger.info("✅ Conversation model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load conversation model: {e}")
    
    def _load_translation_model(self):
        """Load translation model"""
        try:
            model_name = self.config.AI_MODELS["text_generation"]
            logger.info(f"🔄 Loading translation model: {model_name}")
            
            self.pipelines["translation"] = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=model_name,
                max_length=512,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Translation model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load translation model: {e}")
    
    def _load_sentiment_model(self):
        """Load sentiment analysis model"""
        try:
            model_name = self.config.AI_MODELS["sentiment"]
            logger.info(f"🔄 Loading sentiment model: {model_name}")
            
            self.pipelines["sentiment"] = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Sentiment model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load sentiment model: {e}")
    
    def _load_embeddings_model(self):
        """Load embeddings model"""
        try:
            model_name = self.config.AI_MODELS["embeddings"]
            logger.info(f"🔄 Loading embeddings model: {model_name}")
            
            self.models["embeddings"] = SentenceTransformer(model_name)
            
            logger.info("✅ Embeddings model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embeddings model: {e}")
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        if not LANGDETECT_AVAILABLE or not text.strip():
            return "en"
            
        try:
            detected = detect(text)
            confidence_langs = detect_langs(text)
            
            # Check if confidence is high enough
            if confidence_langs and confidence_langs[0].prob > 0.7:
                return detected
            else:
                return "en"  # Default to English if low confidence
                
        except Exception as e:
            logger.debug(f"Language detection failed: {e}")
            return "en"
    
    def translate_text(self, text: str, target_lang: str = "en") -> str:
        """Translate text to target language"""
        if not text.strip():
            return text
            
        detected_lang = self.detect_language(text)
        
        # Don't translate if already in target language
        if detected_lang == target_lang:
            return text
            
        # Use AI model if available
        if "translation" in self.pipelines:
            try:
                prompt = f"Translate this {detected_lang} text to {target_lang}: {text}"
                result = self.pipelines["translation"](prompt, max_length=len(text) + 50)
                return result[0]["generated_text"].strip()
            except Exception as e:
                logger.error(f"❌ AI translation failed: {e}")
        
        # Fallback to basic translation patterns
        return self._basic_translation(text, detected_lang, target_lang)
    
    def _basic_translation(self, text: str, source_lang: str, target_lang: str) -> str:
        """Basic translation fallback"""
        # Simple translation patterns for common Nigerian languages
        translations = {
            "yo": {  # Yoruba
                "bawo": "how are you",
                "eku": "greetings", 
                "ese": "thank you",
                "pele": "sorry/well done"
            },
            "ig": {  # Igbo
                "kedu": "how are you",
                "ndewo": "hello",
                "dalu": "thank you"
            },
            "ha": {  # Hausa
                "sannu": "hello",
                "yaya": "how",
                "na gode": "thank you"
            }
        }
        
        if source_lang in translations:
            for local_word, english in translations[source_lang].items():
                if local_word.lower() in text.lower():
                    text = text.replace(local_word, english)
        
        return text
    
    def get_current_time(self, timezone_name: Optional[str] = None) -> str:
        """Get current time in specified timezone"""
        if not PYTZ_AVAILABLE:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        try:
            if timezone_name:
                tz = pytz.timezone(timezone_name)
            else:
                tz = self.timezone or pytz.UTC
                
            current_time = datetime.now(tz)
            
            # Format with timezone info
            formatted_time = current_time.strftime("%A, %B %d, %Y at %I:%M %p")
            timezone_str = current_time.strftime("%Z")
            
            return f"{formatted_time} ({timezone_str})"
            
        except Exception as e:
            logger.error(f"❌ Timezone error: {e}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if "sentiment" in self.pipelines:
            try:
                result = self.pipelines["sentiment"](text)
                return {
                    "label": result[0]["label"],
                    "score": result[0]["score"],
                    "confidence": "high" if result[0]["score"] > 0.8 else "medium" if result[0]["score"] > 0.6 else "low"
                }
            except Exception as e:
                logger.error(f"❌ Sentiment analysis failed: {e}")
        
        # Fallback sentiment analysis
        positive_words = ["good", "great", "awesome", "happy", "love", "excellent", "amazing"]
        negative_words = ["bad", "terrible", "hate", "sad", "awful", "horrible", "worst"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return {"label": "POSITIVE", "score": 0.7, "confidence": "medium"}
        elif negative_count > positive_count:
            return {"label": "NEGATIVE", "score": 0.7, "confidence": "medium"}
        else:
            return {"label": "NEUTRAL", "score": 0.5, "confidence": "low"}
    
    async def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search the web for information"""
        try:
            results = await self.web_search.search(query, max_results)
            return results
        except Exception as e:
            logger.error(f"❌ Web search failed: {e}")
            return []
    
    def generate_response(self, message: str, sender: str, context: Optional[Dict] = None) -> str:
        """Generate AI response to message"""
        try:
            # Detect and translate if needed
            detected_lang = self.detect_language(message)
            original_message = message
            
            if detected_lang != "en" and self.config.AUTO_TRANSLATE:
                message = self.translate_text(message, "en")
                logger.info(f"🔄 Translated {detected_lang} -> en: {original_message} -> {message}")
            
            # Handle special commands
            response = self._handle_special_commands(message, sender, context)
            if response:
                # Translate response back if needed
                if detected_lang != "en" and self.config.AUTO_TRANSLATE:
                    response = self.translate_text(response, detected_lang)
                return response
            
            # Generate AI response
            if "chat" in self.models and "chat" in self.tokenizers:
                response = self._generate_ai_response(message, sender)
            else:
                response = self._generate_fallback_response(message, sender)
            
            # Translate response back if needed
            if detected_lang != "en" and self.config.AUTO_TRANSLATE:
                response = self.translate_text(response, detected_lang)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return self._get_error_response()
    
    def _handle_special_commands(self, message: str, sender: str, context: Optional[Dict] = None) -> Optional[str]:
        """Handle special commands like time, search, etc."""
        message_lower = message.lower().strip()
        
        # Time commands
        if any(word in message_lower for word in ["time", "clock", "what time", "current time"]):
            return f"Current time: {self.get_current_time()}"
        
        # Search commands  
        if message_lower.startswith("search ") or "search for" in message_lower:
            query = message_lower.replace("search ", "").replace("search for ", "").strip()
            if query:
                # This will be handled asynchronously
                return f"Searching for: {query}..."
        
        # Weather (placeholder - would need weather API)
        if any(word in message_lower for word in ["weather", "temperature", "forecast"]):
            return f"I'd love to help with weather info! For now, try searching 'weather in Lagos' for current conditions."
        
        # Language help
        if any(word in message_lower for word in ["translate", "language", "meaning"]):
            return "I can help translate between English and Nigerian languages (Yoruba, Igbo, Hausa). Just send me text in any language!"
        
        return None
    
    def _generate_ai_response(self, message: str, sender: str) -> str:
        """Generate response using AI model"""
        try:
            # Get conversation history
            history = self.conversation_history.get(sender, [])
            
            # Build conversation context
            chat_history = ""
            for h in history[-5:]:  # Last 5 exchanges
                chat_history += f"Human: {h['message']}\nAI: {h['response']}\n"
            
            # Prepare input
            prompt = f"{chat_history}Human: {message}\nAI:"
            
            # Tokenize
            inputs = self.tokenizers["chat"].encode(prompt, return_tensors="pt", truncate=True, max_length=512)
            
            # Generate
            with torch.no_grad():
                outputs = self.models["chat"].generate(
                    inputs,
                    max_new_tokens=self.config.MAX_RESPONSE_LENGTH,
                    temperature=self.config.TEMPERATURE,
                    do_sample=True,
                    pad_token_id=self.tokenizers["chat"].eos_token_id,
                    no_repeat_ngram_size=3,
                    early_stopping=True
                )
            
            # Decode response
            response = self.tokenizers["chat"].decode(outputs[0], skip_special_tokens=True)
            response = response.split("AI:")[-1].strip()
            
            # Update conversation history
            self._update_conversation_history(sender, message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}")
            return self._generate_fallback_response(message, sender)
    
    def _generate_fallback_response(self, message: str, sender: str) -> str:
        """Generate fallback response when AI models aren't available"""
        message_lower = message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            greetings = [
                f"Hello! How can I help you today?",
                f"Hi there! What's on your mind?",
                f"Hey! Great to hear from you!",
                f"Greetings! How are you doing?"
            ]
            return random.choice(greetings)
        
        # Question responses
        if any(word in message_lower for word in ["how are you", "how you doing", "what's up", "sup"]):
            responses = [
                "I'm doing great, thanks for asking! How about you?",
                "All good here! What brings you here today?",
                "I'm fantastic! Ready to help with whatever you need.",
                "Doing well! How can I assist you?"
            ]
            return random.choice(responses)
        
        # Thank you responses
        if any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
            responses = [
                "You're very welcome!",
                "Happy to help!",
                "Anytime!",
                "My pleasure!"
            ]
            return random.choice(responses)
        
        # Help requests
        if any(word in message_lower for word in ["help", "assist", "support"]):
            return ("I'm here to help! I can:\n"
                   "• Chat and answer questions\n"
                   "• Search the web for information\n" 
                   "• Tell you the current time\n"
                   "• Translate between languages\n"
                   "• Generate memes and ASCII art\n"
                   "Just ask me anything!")
        
        # Default responses
        responses = [
            "That's interesting! Tell me more.",
            "I hear you. What else is on your mind?",
            "Thanks for sharing that with me!",
            "Hmm, that's a good point. What do you think about it?",
            "I'm listening. Go on!",
            "That sounds important to you."
        ]
        
        return random.choice(responses)
    
    def _update_conversation_history(self, sender: str, message: str, response: str):
        """Update conversation history for context"""
        if sender not in self.conversation_history:
            self.conversation_history[sender] = []
        
        self.conversation_history[sender].append({
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.conversation_history[sender]) > self.max_history_length:
            self.conversation_history[sender] = self.conversation_history[sender][-self.max_history_length:]
    
    def _get_error_response(self) -> str:
        """Get response when errors occur"""
        responses = [
            "Sorry, I'm having a bit of trouble right now. Can you try again?",
            "Oops! Something went wrong on my end. Please give me another try!",
            "I encountered an issue processing that. Mind rephrasing?",
            "Technical hiccup on my side! Let's try that again."
        ]
        return random.choice(responses)
    
    async def process_message_with_search(self, message: str, sender: str) -> str:
        """Process message with intelligent web search integration"""
        message_lower = message.lower().strip()
        
        # Enhanced search trigger detection
        search_triggers = [
            "search", "find", "look up", "google", "what is", "who is", "where is", 
            "when is", "how to", "tell me about", "information about", "latest news",
            "current", "recent", "today", "now", "weather", "temperature", "stock price"
        ]
        
        # Question patterns that benefit from search
        question_words = ["what", "who", "where", "when", "how", "why", "which"]
        is_question = any(message_lower.startswith(word) for word in question_words)
        
        # Current information indicators
        current_info_words = ["today", "now", "current", "latest", "recent", "2025", "this year"]
        needs_current_info = any(word in message_lower for word in current_info_words)
        
        # Automatic search conditions
        is_search_request = any(trigger in message_lower for trigger in search_triggers)
        auto_search_enabled = getattr(self.config, 'AUTO_SEARCH_ON_QUESTIONS', True)
        
        should_search = (
            is_search_request or 
            (auto_search_enabled and is_question and len(message.split()) > 2) or
            (needs_current_info and len(message.split()) > 1)
        )
        
        if should_search:
            # Extract and clean search query
            search_query = self._extract_search_query(message, message_lower)
            
            # Perform web search with streaming
            try:
                search_results = await self.search_web(search_query, max_results=getattr(self.config, 'MAX_SEARCH_RESULTS', 5))
                
                if search_results:
                    # Enhanced response formatting with streaming
                    if getattr(self.config, 'USE_STREAMING', False):
                        response = await self._format_search_response_streaming(search_query, search_results)
                    else:
                        response = self._format_search_response(search_query, search_results)
                    
                    # Add AI-generated summary if models available
                    if "chat" in self.models:
                        summary = self._generate_search_summary(search_query, search_results)
                        if summary:
                            response = f"{summary}\n\n{response}"
                    
                    return response
                else:
                    # Fallback to AI response with search attempt note
                    base_response = self.generate_response(message, sender)
                    return f"{base_response}\n\n💡 I also tried searching for current information but couldn't find additional details right now."
                    
            except Exception as e:
                logger.error(f"❌ Search processing failed: {e}")
                return self.generate_response(message, sender)
        
        # Regular message processing with context awareness
        return self.generate_response(message, sender)
    
    def _extract_search_query(self, original_message: str, message_lower: str) -> str:
        """Extract clean search query from message"""
        # Remove common search prefixes
        prefixes_to_remove = [
            "search for", "search", "find", "look up", "google", "tell me about",
            "what is", "who is", "where is", "when is", "how to", "information about"
        ]
        
        query = message_lower
        for prefix in prefixes_to_remove:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        # Clean up the query
        query = query.replace("?", "").replace("!", "").strip()
        
        # Use original case for better search results
        if query:
            # Find the position in original message
            start_pos = original_message.lower().find(query)
            if start_pos >= 0:
                return original_message[start_pos:start_pos + len(query)]
        
        return query or original_message
    
    def _format_search_response(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Format search results into response"""
        response = f"🔍 **Search Results for:** {query}\n\n"
        
        for i, result in enumerate(results[:5], 1):
            title = result.get('title', 'Result')
            snippet = result.get('snippet', 'No description available')
            url = result.get('url', '')
            
            response += f"**{i}. {title}**\n{snippet}\n"
            if url:
                response += f"🔗 {url}\n\n"
            else:
                response += "\n"
        
        return response.strip()
    
    async def _format_search_response_streaming(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Format search results with streaming effect"""
        # For now, return formatted response (streaming would be implemented in the UI layer)
        return self._format_search_response(query, results)
    
    def _generate_search_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate AI summary of search results"""
        if not results or "chat" not in self.models:
            return ""
        
        try:
            # Combine snippets for summary
            combined_info = " ".join([result.get('snippet', '') for result in results[:3]])
            
            if len(combined_info) > 50:
                summary_prompt = f"Based on this information about '{query}': {combined_info[:500]}... Provide a brief summary:"
                
                # Generate summary using AI model
                summary = self._generate_ai_response(summary_prompt, "system")
                if summary and len(summary) < 200:
                    return f"📝 **Summary:** {summary}\n"
        except Exception as e:
            logger.debug(f"Summary generation failed: {e}")
        
        return ""