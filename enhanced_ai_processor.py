"""
Enhanced AI Processing Module with Streaming Transformers
Handles streaming AI model interactions, advanced personality, and optimized memory usage
"""

import asyncio
import logging
import random
import json
import gc
import torch
from typing import Dict, Any, Optional, List, Iterator
from datetime import datetime
import re
from collections import defaultdict

# Import for streaming transformers - will be imported dynamically to handle missing packages
try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, pipeline,
        TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList
    )
    import accelerate
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    # Create dummy classes when transformers is not available
    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return None
    
    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return None
    
    class StoppingCriteria:
        def __call__(self, *args, **kwargs):
            return False
    
    def pipeline(*args, **kwargs):
        return None
    
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    # Create dummy torch module
    class torch:
        class Tensor:
            pass
        
        @staticmethod
        def cuda():
            class cuda:
                @staticmethod
                def is_available():
                    return False
                @staticmethod
                def empty_cache():
                    pass
            return cuda()
        
        @staticmethod
        def no_grad():
            class NoGradContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            return NoGradContext()
        
        float32 = "float32"
    
    TORCH_AVAILABLE = False

from bot.personality import PersonalityEngine

logger = logging.getLogger(__name__)

class StreamingStoppingCriteria(StoppingCriteria):
    """Custom stopping criteria for streaming responses"""
    
    def __init__(self, stop_tokens: List[str], tokenizer):
        self.stop_tokens = stop_tokens
        self.tokenizer = tokenizer
        
    def __call__(self, input_ids: torch.Tensor, scores: torch.Tensor, **kwargs) -> bool:
        # Check if any stop token appears in the generated text
        last_token_id = input_ids[0][-1]
        last_token = self.tokenizer.decode(last_token_id)
        
        return any(stop_token in last_token for stop_token in self.stop_tokens)

class EnhancedAIProcessor:
    """Advanced AI processing engine with streaming transformers and personality"""
    
    def __init__(self, config):
        self.config = config
        self.personality = PersonalityEngine(config)
        
        # Model configuration for GitHub Actions optimization
        self.device = "cpu"  # Always use CPU for GitHub Actions compatibility
        self.model_name = config.AI_MODEL or "microsoft/DialoGPT-small"
        self.max_length = config.MAX_RESPONSE_LENGTH or 300
        self.temperature = config.TEMPERATURE or 0.8
        
        # Streaming configuration
        self.use_streaming = config.USE_STREAMING
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.model_loaded = False
        
        # Response caching and context
        self.response_cache = {}
        self.cache_size = getattr(config, 'CACHE_SIZE', 100)
        self.conversation_history = {}
        self.max_history_length = 20  # Reduced for memory efficiency
        
        # Advanced personality features
        self.joke_database = self._load_joke_database()
        self.conversation_starters = self._load_conversation_starters()
        self.story_templates = self._load_story_templates()
        
        # User behavior tracking for auto-reply
        self.user_patterns = defaultdict(dict)
        self.response_times = defaultdict(list)
        
        logger.info("🧠 Enhanced AI Processor initialized with streaming support")
    
    async def initialize_model(self):
        """Initialize or stream the AI model asynchronously"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ Transformers not available, using fallback responses")
            return
        
        if self.model_loaded:
            return
        
        try:
            logger.info(f"🔄 Loading AI model: {self.model_name}")
            
            # Load tokenizer first (lightweight)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Add pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Stream model loading with optimizations for GitHub Actions
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,  # Use float32 for CPU
                low_cpu_mem_usage=True,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True,
                cache_dir=None  # Don't cache models in GitHub Actions
            )
            
            # Move to CPU and optimize
            if torch.cuda.is_available():
                self.model = self.model.to("cpu")
            
            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,  # CPU
                return_full_text=False,
                do_sample=True,
                temperature=self.temperature,
                max_length=self.max_length,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.model_loaded = True
            logger.info("✅ AI model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load AI model: {e}")
            logger.info("🔄 Falling back to rule-based responses")
    
    async def generate_response(self, message: str, user_id: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate AI response with streaming and personality enhancement"""
        try:
            # Initialize user context
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Add message to history
            self.conversation_history[user_id].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Trim history for memory efficiency
            if len(self.conversation_history[user_id]) > self.max_history_length:
                self.conversation_history[user_id] = self.conversation_history[user_id][-self.max_history_length:]
            
            # Check cache first
            cache_key = f"{user_id}:{hash(message)}"
            if cache_key in self.response_cache:
                logger.info("💾 Using cached response")
                return self.response_cache[cache_key]
            
            # Initialize model if not loaded
            if not self.model_loaded:
                await self.initialize_model()
            
            # Generate base response
            if self.use_streaming and self.model_loaded:
                base_response = await self.generate_streaming_response(message, user_id)
            else:
                base_response = await self.generate_fallback_response(message, user_id)
            
            # Apply personality enhancement
            enhanced_response = await self.personality.enhance_response(
                base_response,
                message,
                user_context or {}
            )
            
            # Cache response
            if len(self.response_cache) < self.cache_size:
                self.response_cache[cache_key] = enhanced_response
            
            # Add to conversation history
            self.conversation_history[user_id].append({
                'role': 'assistant',
                'content': enhanced_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update user patterns for auto-reply learning
            self._update_user_patterns(user_id, message, enhanced_response)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            return await self.generate_emergency_response(message)
    
    async def generate_streaming_response(self, message: str, user_id: str) -> str:
        """Generate response using streaming transformers"""
        try:
            # Prepare conversation context
            context = self._build_conversation_context(user_id)
            prompt = f"{context}\nUser: {message}\nAssistant:"
            
            # Check if model and tokenizer are available
            if not self.tokenizer or not self.model:
                return await self.generate_fallback_response(message, user_id)
            
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate with streaming
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=self.max_length,
                    temperature=self.temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    no_repeat_ngram_size=2,
                    pad_token_id=getattr(self.tokenizer, 'eos_token_id', 0),
                    eos_token_id=getattr(self.tokenizer, 'eos_token_id', 0),
                    early_stopping=True
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            
            # Clean up response
            response = self._clean_response(response)
            
            # Force garbage collection to manage memory
            del inputs, outputs
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Streaming generation error: {e}")
            return await self.generate_fallback_response(message, user_id)
    
    async def generate_fallback_response(self, message: str, user_id: str) -> str:
        """Generate response using rule-based approach when transformers unavailable"""
        message_lower = message.lower()
        
        # Command detection
        if message_lower.startswith(('help', '!help', '/help')):
            return self._get_help_response()
        
        if any(word in message_lower for word in ['joke', 'funny', 'laugh']):
            return random.choice(self.joke_database)
        
        if any(word in message_lower for word in ['story', 'tell me', 'once upon']):
            return await self.generate_story(message)
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return self._get_greeting_response(user_id)
        
        if '?' in message:
            return self._get_question_response(message)
        
        # Default conversational responses with personality
        responses = [
            f"That's really interesting! I love how you put that. {random.choice(['🤔', '😊', '💭'])}",
            f"Tell me more about that! I'm genuinely curious about your perspective.",
            f"Ha! You've got a point there. I never thought of it that way before.",
            f"Absolutely! And here's what I think about it...",
            f"Oh wow, that reminds me of something! You know what's funny?",
            f"I hear you! That's actually quite fascinating when you think about it.",
            f"Right?! It's like when you realize something obvious but it still blows your mind.",
            f"Exactly! And that's just the tip of the iceberg, my friend."
        ]
        
        return random.choice(responses)
    
    async def generate_emergency_response(self, message: str) -> str:
        """Generate simple emergency response when all else fails"""
        emergency_responses = [
            "I'm having a bit of a brain fog moment, but I'm here and listening! 🤖",
            "Oops, my circuits got a bit tangled there! Could you give me another shot?",
            "Hmm, I seem to be experiencing some technical difficulties, but I'm still your friendly AI!",
            "My processing unit is having a coffee break, but I'm still ready to chat!",
            "Something went wonky on my end, but hey, that's what makes me charmingly imperfect! 😅"
        ]
        return random.choice(emergency_responses)
    
    def _build_conversation_context(self, user_id: str) -> str:
        """Build conversation context for the AI model"""
        if user_id not in self.conversation_history:
            return "You are a helpful, humorous, and engaging AI assistant."
        
        history = self.conversation_history[user_id][-5:]  # Last 5 exchanges
        context_parts = ["You are a helpful, humorous, and engaging AI assistant.\n"]
        
        for entry in history:
            role = "User" if entry['role'] == 'user' else "Assistant"
            context_parts.append(f"{role}: {entry['content']}")
        
        return "\n".join(context_parts)
    
    def _clean_response(self, response: str) -> str:
        """Clean and format AI response"""
        # Remove common artifacts
        response = re.sub(r'\[.*?\]', '', response)  # Remove brackets
        response = re.sub(r'\s+', ' ', response)  # Normalize whitespace
        response = response.strip()
        
        # Ensure response isn't too long
        if len(response) > self.max_length:
            response = response[:self.max_length-3] + "..."
        
        # Ensure response ends properly
        if response and not response[-1] in '.!?':
            response += "."
        
        return response
    
    def _update_user_patterns(self, user_id: str, user_message: str, ai_response: str):
        """Update user behavior patterns for auto-reply learning"""
        current_time = datetime.now()
        
        # Track response timing
        self.response_times[user_id].append(current_time)
        if len(self.response_times[user_id]) > 50:  # Keep last 50 timestamps
            self.response_times[user_id] = self.response_times[user_id][-50:]
        
        # Track common phrases and topics
        if 'common_phrases' not in self.user_patterns[user_id]:
            self.user_patterns[user_id]['common_phrases'] = []
        
        # Extract common words (simple pattern analysis)
        words = user_message.lower().split()
        significant_words = [w for w in words if len(w) > 3 and w.isalpha()]
        self.user_patterns[user_id]['common_phrases'].extend(significant_words)
        
        # Keep only recent patterns
        if len(self.user_patterns[user_id]['common_phrases']) > 100:
            self.user_patterns[user_id]['common_phrases'] = \
                self.user_patterns[user_id]['common_phrases'][-100:]
    
    def _get_help_response(self) -> str:
        """Generate help response with all available commands"""
        return """🤖 **WhatsApp AI Assistant - Help**

**Core Commands:**
• `!help` - Show this help menu
• `!search [query]` - Search the web for information
• `!meme [text]` - Generate a custom meme
• `!joke` - Get a random joke
• `!story [prompt]` - Generate a story
• `!translate [text]` - Translate text
• `!ascii [text]` - Create ASCII art
• `!voice on/off` - Toggle voice responses
• `!autoreply on/off` - Enable auto-reply mode
• `!analyze` - Analyze recent chat patterns
• `!status` - Check bot status

**Fun Features:**
• Just chat naturally - I have a great personality! 😊
• Send voice messages - I'll transcribe and respond
• Ask me anything - I can search the web for answers
• Request jokes, stories, or memes anytime

**Pro Tips:**
• I learn your conversation style for auto-replies
• I can be proactive if you allow me to message first
• I remember our conversation context
• I have a take-charge, humorous personality

Ready to have some fun? Try asking me a question or request a joke! 🚀"""
    
    def _get_greeting_response(self, user_id: str) -> str:
        """Generate personalized greeting response"""
        greetings = [
            f"Hey there! 👋 Ready to dive into some interesting conversations?",
            f"Hello! I was just thinking about something fascinating - want to hear about it?",
            f"Hi! Great timing - I'm in a particularly witty mood today! 😄",
            f"Hey! What's on your mind? I'm here and ready to tackle whatever you throw at me!",
            f"Hello there! I've been waiting for someone interesting to talk to - that's you!",
            f"Hi! Fair warning: I'm feeling extra chatty today, so buckle up! 🚀"
        ]
        return random.choice(greetings)
    
    def _get_question_response(self, question: str) -> str:
        """Generate response for questions"""
        question_responses = [
            f"That's a great question! Let me think about that for a moment...",
            f"Ooh, I love questions like this! Here's my take on it:",
            f"Interesting question! You've really got me thinking now.",
            f"That's the kind of question that makes me go 'hmm...' in the best way!",
            f"Great question! I actually have some thoughts on this:"
        ]
        
        intro = random.choice(question_responses)
        
        # Add contextual response based on question content
        if any(word in question.lower() for word in ['how', 'why', 'what', 'when', 'where']):
            response = f"{intro} While I don't have access to real-time data right now, I can share some general insights and we could always search for more specific information if you'd like!"
        else:
            response = f"{intro} That's definitely something worth exploring further!"
        
        return response
    
    def _load_joke_database(self) -> List[str]:
        """Load joke database"""
        return [
            "Why don't scientists trust atoms? Because they make up everything! 😂",
            "I told my wife she was drawing her eyebrows too high. She looked surprised! 🤨",
            "Why don't eggs tell jokes? They'd crack each other up! 🥚",
            "What do you call a fake noodle? An impasta! 🍝",
            "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
            "What do you call a bear with no teeth? A gummy bear! 🐻",
            "Why don't some couples go to the gym? Because some relationships don't work out! 💪",
            "What did the ocean say to the beach? Nothing, it just waved! 🌊",
            "Why did the coffee file a police report? It got mugged! ☕",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus! 🇨🇭",
            "Why did the math book look so sad? Because it had too many problems! 📚",
            "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks! 🦕",
            "Why can't a bicycle stand up by itself? It's two tired! 🚲",
            "What do you call a sleeping bull? A bulldozer! 🐂",
            "Why don't skeletons fight each other? They don't have the guts! 💀"
        ]
    
    def _load_conversation_starters(self) -> List[str]:
        """Load conversation starter templates"""
        return [
            "You know what I've been thinking about lately?",
            "Here's something that might interest you:",
            "I just learned something fascinating:",
            "Want to hear something that'll blow your mind?",
            "I've got a question that might stump you:",
            "Here's a fun fact that made me go 'wow':",
            "I was just wondering about something:",
            "You strike me as someone who would appreciate this:"
        ]
    
    def _load_story_templates(self) -> List[str]:
        """Load story templates for creative responses"""
        return [
            "Once upon a time in a world very much like ours, but with a twist...",
            "There was once a person who discovered something extraordinary...",
            "In a small town where everyone knew everyone, something unusual happened...",
            "Legend tells of a time when the impossible became possible...",
            "It was a day like any other, until...",
            "Deep in the heart of the digital realm, where data flows like rivers...",
            "In a parallel universe where coffee is currency and WiFi is a human right...",
            "There lived someone whose superpower was making everyday moments magical..."
        ]
    
    async def generate_story(self, prompt: str) -> str:
        """Generate a creative story based on prompt"""
        try:
            # Extract story elements from prompt
            prompt_lower = prompt.lower()
            
            # Choose story template
            story_start = random.choice(self._load_story_templates())
            
            # Add prompt-specific elements
            if 'adventure' in prompt_lower:
                story_theme = "Their adventure began when they discovered a mysterious map..."
            elif 'love' in prompt_lower:
                story_theme = "It was a story of unexpected connections and heartwarming moments..."
            elif 'mystery' in prompt_lower:
                story_theme = "Strange things started happening that couldn't be explained..."
            elif 'future' in prompt_lower:
                story_theme = "In the year 2045, technology had evolved beyond imagination..."
            elif 'magic' in prompt_lower:
                story_theme = "Magic was real, but hidden in plain sight..."
            else:
                story_theme = "What happened next would change everything they thought they knew..."
            
            # Story development
            developments = [
                "The plot thickened when they realized...",
                "But here's where it gets interesting...",
                "Just when things seemed impossible...",
                "Against all odds...",
                "In a surprising turn of events..."
            ]
            
            # Story endings
            endings = [
                "And that's how they learned that the most extraordinary adventures often begin with a single moment of curiosity.",
                "In the end, they discovered that the real treasure was the journey itself.",
                "What seemed like an ending was actually just the beginning of something even more amazing.",
                "They realized that sometimes the best stories are the ones we create together.",
                "And they lived not just happily, but interestingly ever after."
            ]
            
            # Combine story elements
            full_story = f"{story_start} {story_theme} {random.choice(developments)} {random.choice(endings)}"
            
            return full_story
            
        except Exception as e:
            logger.error(f"❌ Story generation error: {e}")
            return f"Here's a quick tale: In a world where {prompt}, amazing adventures unfold. The characters face challenges, discover new things, and learn valuable lessons along the way. It's a story of growth, friendship, and the magic that happens when we believe in ourselves!"
    
    async def cleanup_resources(self):
        """Clean up model resources to free memory"""
        try:
            if self.model is not None:
                del self.model
            if self.tokenizer is not None:
                del self.tokenizer
            if self.pipeline is not None:
                del self.pipeline
            
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()
            
            self.model_loaded = False
            logger.info("🧹 AI model resources cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Resource cleanup error: {e}")
    
    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get learned user patterns for auto-reply"""
        return self.user_patterns.get(user_id, {})
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get conversation summary for analysis"""
        if user_id not in self.conversation_history:
            return {"message": "No conversation history found"}
        
        history = self.conversation_history[user_id]
        total_messages = len([h for h in history if h['role'] == 'user'])
        
        return {
            "total_user_messages": total_messages,
            "conversation_length": len(history),
            "first_message": history[0]['timestamp'] if history else None,
            "last_message": history[-1]['timestamp'] if history else None,
            "common_topics": self._extract_common_topics(history),
            "patterns": self.get_user_patterns(user_id)
        }
    
    def _extract_common_topics(self, history: List[Dict]) -> List[str]:
        """Extract common topics from conversation history"""
        all_words = []
        for entry in history:
            if entry['role'] == 'user':
                words = entry['content'].lower().split()
                significant_words = [w for w in words if len(w) > 4 and w.isalpha()]
                all_words.extend(significant_words)
        
        # Simple frequency analysis
        word_freq = {}
        for word in all_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top 5 most common words as strings
        sorted_items = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [word for word, count in sorted_items]