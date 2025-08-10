"""
AI Processing Module
Handles AI model interactions, response generation, and personality injection
"""

import asyncio
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from bot.personality import PersonalityEngine

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI processing engine with personality and context awareness"""
    
    def __init__(self, config):
        self.config = config
        self.personality = PersonalityEngine(config)
        
        # Response caching
        self.response_cache = {}
        self.cache_size = config.CACHE_SIZE
        
        # Context management
        self.conversation_history = {}
        self.max_history_length = 50
        
        # Model streaming simulation (in real implementation, use transformers)
        self.model_loaded = False
        
        logger.info("🧠 AI Processor initialized")
    
    async def generate_response(self, message: str, user_id: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate AI response with personality"""
        try:
            # Initialize user context if needed
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Add message to history
            self.conversation_history[user_id].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Trim history if too long
            if len(self.conversation_history[user_id]) > self.max_history_length:
                self.conversation_history[user_id] = self.conversation_history[user_id][-self.max_history_length:]
            
            # Check cache first
            cache_key = f"{user_id}:{hash(message)}"
            if cache_key in self.response_cache and len(self.response_cache) < self.cache_size:
                logger.info("💾 Using cached response")
                return self.response_cache[cache_key]
            
            # Generate base response
            base_response = await self.generate_base_response(message, user_id)
            
            # Apply personality
            personality_response = await self.personality.enhance_response(
                base_response, 
                message, 
                user_context or {}
            )
            
            # Add humor if configured
            if random.random() < self.config.JOKE_FREQUENCY:
                personality_response = await self.add_humor_element(personality_response, message)
            
            # Add response to history
            self.conversation_history[user_id].append({
                'role': 'assistant',
                'content': personality_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Cache response
            self.response_cache[cache_key] = personality_response
            
            return personality_response
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return await self.get_fallback_response(message)
    
    async def generate_base_response(self, message: str, user_id: str) -> str:
        """Generate base AI response (simulated - in real implementation use transformers)"""
        try:
            # Simulate model loading and streaming
            if not self.model_loaded:
                logger.info("🔄 Loading AI model...")
                await asyncio.sleep(1)  # Simulate loading time
                self.model_loaded = True
                logger.info("✅ AI model loaded")
            
            # Get conversation context
            history = self.conversation_history.get(user_id, [])
            context = self.build_context(history[-10:])  # Last 10 messages
            
            # Simulate AI processing
            await asyncio.sleep(0.3)  # Simulate processing time
            
            # Generate response based on message patterns
            response = await self.pattern_based_response(message, context)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in base response generation: {e}")
            return "I'm having trouble processing that right now. Could you try rephrasing?"
    
    async def pattern_based_response(self, message: str, context: str) -> str:
        """Generate response using pattern matching (simulation of AI model)"""
        message_lower = message.lower()
        
        # Greeting patterns
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'howdy', 'sup']):
            greetings = [
                "Hey there! Ready to have some fun?",
                "Hello! What's cooking in your world?",
                "Hi! I'm here and ready to chat!",
                "Howdy! What can I help you with today?",
                "Hey! Good to hear from you!"
            ]
            return random.choice(greetings)
        
        # Question patterns
        if message.endswith('?'):
            if 'how are you' in message_lower:
                return "I'm doing fantastic! Always ready to chat and help out. How about you?"
            elif 'what' in message_lower and ('do' in message_lower or 'can' in message_lower):
                return "I can help with lots of things! Search the web, generate memes, tell jokes, have conversations, and much more. What interests you?"
            elif 'why' in message_lower:
                return "Great question! Let me think about that... " + await self.generate_thoughtful_response(message)
            elif 'when' in message_lower:
                return "Timing is everything! That's a good question about timing - it really depends on the context."
            else:
                return "That's a great question! I'd love to explore that with you. What made you curious about that?"
        
        # Emotional expressions
        if any(word in message_lower for word in ['sad', 'upset', 'angry', 'frustrated', 'depressed']):
            return await self.generate_supportive_response(message)
        elif any(word in message_lower for word in ['happy', 'excited', 'great', 'awesome', 'wonderful']):
            return await self.generate_enthusiastic_response(message)
        
        # Commands and requests
        if any(word in message_lower for word in ['please', 'help', 'can you', 'would you']):
            return "Absolutely! I'm here to help with whatever you need. Search, jokes, memes, conversations, or anything else - just let me know!"
        
        # Technical topics
        if any(word in message_lower for word in ['code', 'programming', 'computer', 'technology', 'software']):
            return "Now we're talking tech! I love discussing programming and technology. What's on your mind?"
        
        # Default conversational response
        return await self.generate_conversational_response(message, context)
    
    async def generate_thoughtful_response(self, message: str) -> str:
        """Generate thoughtful response for 'why' questions"""
        responses = [
            "That's because life is full of interesting patterns and connections!",
            "Well, from what I understand, it's all about the underlying principles at work.",
            "Good point! It usually comes down to how different factors interact with each other.",
            "That's a deep question! It often relates to cause and effect relationships.",
            "Interesting perspective! It's probably connected to broader patterns we see everywhere."
        ]
        return random.choice(responses)
    
    async def generate_supportive_response(self, message: str) -> str:
        """Generate supportive response for emotional messages"""
        responses = [
            "I hear you, and that sounds tough. Want to talk about it? Sometimes sharing helps!",
            "Sorry you're going through a rough time. I'm here to listen and maybe lighten the mood a bit!",
            "That doesn't sound fun at all. How about we try to turn this day around together?",
            "I get it - we all have those moments. Want me to tell you a joke or find something interesting to distract you?",
            "Sending virtual hugs your way! 🤗 What would help you feel better right now?"
        ]
        return random.choice(responses)
    
    async def generate_enthusiastic_response(self, message: str) -> str:
        """Generate enthusiastic response for positive messages"""
        responses = [
            "That's awesome! Your excitement is totally contagious! 🎉",
            "Yes! I love that energy! Tell me more about what's got you so pumped!",
            "Fantastic! Days like this are what make life interesting!",
            "That's the spirit! Nothing beats good vibes and positive energy!",
            "Woohoo! 🚀 Keep that momentum going - you're on fire!"
        ]
        return random.choice(responses)
    
    async def generate_conversational_response(self, message: str, context: str) -> str:
        """Generate general conversational response"""
        # Analyze message content
        words = message.lower().split()
        
        if len(words) > 20:
            # Long message - acknowledge and engage
            return "Wow, you've got a lot on your mind! That's really interesting. What aspect of that interests you most?"
        elif len(words) < 3:
            # Short message - encourage more
            responses = [
                "Tell me more! I'm listening.",
                "Interesting! What's the story behind that?",
                "I'm curious - can you expand on that?",
                "That's intriguing! Got any details?",
                "Cool! What made you think of that?"
            ]
            return random.choice(responses)
        else:
            # Medium message - balanced response
            responses = [
                "That's a great point! I hadn't thought about it that way before.",
                "Really interesting perspective! It makes me think about similar situations.",
                "I can see where you're coming from on that. It's definitely worth considering.",
                "That's pretty cool! Have you noticed that pattern in other places too?",
                "Nice observation! It's always fascinating how these things work out.",
                "I like how you put that! It gives me a new way to think about it.",
                "That's the kind of insight I enjoy hearing! Thanks for sharing that perspective."
            ]
            return random.choice(responses)
    
    async def pick_conversation_thread(self, message: str) -> str:
        """Pick an interesting thread from a long message"""
        # Simple keyword extraction simulation
        interesting_words = []
        words = message.lower().split()
        
        for word in words:
            if len(word) > 6 and word not in ['because', 'through', 'without', 'between', 'something']:
                interesting_words.append(word)
        
        if interesting_words:
            word = random.choice(interesting_words)
            return f"The '{word}' part really caught my attention. What's your experience with that?"
        else:
            return "What aspect of that interests you most?"
    
    async def generate_balanced_response(self, message: str) -> str:
        """Generate balanced conversational response"""
        responses = [
            "That's a great point! I hadn't thought about it that way before.",
            "Really interesting perspective! It makes me think about similar situations.",
            "I can see where you're coming from on that. It's definitely worth considering.",
            "That's pretty cool! Have you noticed that pattern in other places too?",
            "Nice observation! It's always fascinating how these things work out.",
            "I like how you put that! It gives me a new way to think about it.",
            "That's the kind of insight I enjoy hearing! Thanks for sharing that perspective."
        ]
        return random.choice(responses)
    
    async def add_humor_element(self, response: str, original_message: str) -> str:
        """Add humor to response"""
        try:
            humor_additions = [
                " (Just kidding around!)",
                " Haha!",
                " (I couldn't resist!)"
            ]
            
            # Sometimes add a humorous comment
            if random.random() < 0.3:
                humorous_comments = [
                    "By the way, did you hear about the programmer who got stuck in the shower? The instructions said: Lather, Rinse, Repeat!",
                    "Fun fact: I'm 99% sure I'm an AI, but there's always that 1% doubt!",
                    "Speaking of which, why did the robot go on a diet? It had a byte problem!",
                    "Random thought: If I were human, I'd probably be the type who puts pineapple on pizza!",
                    "Totally unrelated, but I just 'learned' that octopi have three hearts. Show-offs!"
                ]
                response += "\n\n" + random.choice(humorous_comments)
            else:
                response += random.choice(humor_additions)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error adding humor: {e}")
            return response
    
    async def generate_joke(self, category: str = "random") -> str:
        """Generate a joke"""
        try:
            jokes = {
                "tech": [
                    "Why do programmers prefer dark mode? Because light attracts bugs!",
                    "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
                    "Why did the developer go broke? Because he used up all his cache!",
                    "What's a programmer's favorite hangout place? Foo Bar!",
                    "Why don't robots ever panic? They have nerves of steel!"
                ],
                "general": [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "What do you call a fake noodle? An impasta!",
                    "Why did the scarecrow win an award? He was outstanding in his field!",
                    "What do you call a bear with no teeth? A gummy bear!",
                    "Why don't eggs tell jokes? They'd crack each other up!"
                ],
                "random": []
            }
            
            # Combine all categories for random
            if category == "random":
                jokes["random"] = jokes["tech"] + jokes["general"]
            
            # Default to general if category not found
            joke_list = jokes.get(category, jokes["general"])
            
            return random.choice(joke_list)
            
        except Exception as e:
            logger.error(f"❌ Error generating joke: {e}")
            return "Why did the AI tell a bad joke? It was still learning! 😅"
    
    def build_context(self, history: List[Dict[str, Any]]) -> str:
        """Build conversation context from history"""
        if not history:
            return ""
        
        context_parts = []
        for entry in history[-5:]:  # Last 5 messages
            role = entry['role']
            content = entry['content'][:100]  # Truncate long messages
            context_parts.append(f"{role}: {content}")
        
        return " | ".join(context_parts)
    
    async def get_fallback_response(self, message: str) -> str:
        """Get fallback response when AI processing fails"""
        fallbacks = [
            "I'm having a bit of trouble processing that right now. Could you try rephrasing?",
            "My circuits are a bit scrambled at the moment! 🤖 Can you help me understand what you meant?",
            "Hmm, I didn't quite catch that. Mind saying it differently?",
            "I'm still learning! Could you help me out by explaining that another way?",
            "My AI brain is buffering... 🔄 Could you try that again?"
        ]
        return random.choice(fallbacks)
    
    async def generate_time_aware_response(self, message: str, user_id: str = "default") -> str:
        """Generate time-aware response"""
        responses = [
            "That's a good question about timing - it really depends on the context.",
            "Timing is crucial! From my perspective, it varies based on the situation.",
            "Good point about when things happen - context is everything!",
            "I'd say the timing depends on several factors we should consider."
        ]
        return random.choice(responses)
    
    async def generate_question_response(self, message: str, user_id: str = "default") -> str:
        """Generate response specifically for questions"""
        responses = [
            "That's a great question! I'd love to explore that with you. What made you curious about that?",
            "Interesting question! Let me share my thoughts on that.",
            "Good point to bring up! That's something worth discussing.",
            "That's worth thinking about! I appreciate you asking that."
        ]
        return random.choice(responses)
    
    async def generate_helpful_response(self, message: str, user_id: str = "default") -> str:
        """Generate helpful response for assistance requests"""
        responses = [
            "I'm here to help! Let me see what I can do for you.",
            "Absolutely! I'd be happy to assist with that.",
            "Sure thing! I love helping out - what do you need?",
            "Of course! That's what I'm here for. How can I help?"
        ]
        return random.choice(responses)
    
    async def generate_tech_response(self, message: str, user_id: str = "default") -> str:
        """Generate technical response for tech-related queries"""
        responses = [
            "That's an interesting technical question! I enjoy discussing tech topics.",
            "Great tech question! I love diving into technical discussions.",
            "From a technical perspective, that's definitely worth exploring.",
            "Now we're talking tech! That's right up my alley."
        ]
        return random.choice(responses)
    
    async def generate_story(self, story_prompt: str) -> str:
        """Generate a story based on prompt"""
        try:
            story_templates = [
                f"Once upon a time, in a world where {story_prompt}, there lived a character who would change everything...",
                f"The adventure began when {story_prompt} happened, setting off a chain of unexpected events...",
                f"In a land not so different from ours, {story_prompt} was about to become the center of an amazing tale...",
                f"They say that {story_prompt} is impossible, but this story proves otherwise..."
            ]
            
            story_start = random.choice(story_templates)
            
            story_developments = [
                " The protagonist faced challenges that seemed insurmountable, but with determination and clever thinking, they found a way forward.",
                " What started as a simple situation quickly became an epic adventure filled with surprises and discoveries.",
                " Through unexpected friendships and amazing discoveries, the main character learned valuable lessons about courage and perseverance.",
                " The journey was filled with twists, turns, and moments of pure magic that changed everyone involved."
            ]
            
            story_endings = [
                " In the end, they realized that the real treasure was the experience gained and the friends made along the way.",
                " The adventure concluded with a new understanding that some of the best stories come from taking chances.",
                " As the tale came to a close, it was clear that this was just the beginning of many more adventures to come.",
                " And so the story reminds us that extraordinary things can happen when we dare to dream big."
            ]
            
            full_story = story_start + random.choice(story_developments) + random.choice(story_endings)
            return full_story
            
        except Exception as e:
            logger.error(f"❌ Story generation error: {e}")
            return f"Here's a quick tale: In a world where {story_prompt}, amazing adventures unfold. The characters face challenges, discover new things, and learn valuable lessons along the way. It's a story of growth, friendship, and the magic that happens when we believe in ourselves!"
