"""
Personality Engine
Handles bot personality traits, humor injection, and response style modification
"""

import logging
import random
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class PersonalityEngine:
    """AI personality enhancement engine"""
    
    def __init__(self, config):
        self.config = config
        self.personality_settings = config.get_personality_settings()
        
        # Personality traits
        self.humor_level = self.personality_settings.get('humor_level', 'high')
        self.take_charge_attitude = self.personality_settings.get('take_charge', True)
        self.interaction_style = self.personality_settings.get('interaction_style', 'engaging')
        
        # Response modifiers
        self.confidence_boosters = [
            "Absolutely!",
            "Without a doubt!",
            "I'm confident that",
            "Here's the thing:",
            "Let me tell you:",
            "You know what?"
        ]
        
        self.engaging_transitions = [
            "Speaking of which,",
            "That reminds me,",
            "Here's what's interesting:",
            "On a related note,",
            "You know what's cool?",
            "Here's a fun fact:"
        ]
        
        self.humor_database = self.load_humor_database()
        
        logger.info(f"😄 Personality engine initialized - Mode: {self.personality_settings['mode']}")
    
    def load_humor_database(self) -> Dict[str, List[str]]:
        """Load humor database for different situations"""
        return {
            "puns": [
                "I was wondering why the ball kept getting bigger... then it hit me! ⚽",
                "I used to hate facial hair, but then it grew on me! 🧔",
                "Did you hear about the guy who invented knock-knock jokes? He won the 'No-bell' prize! 🏆",
                "I'm reading a book on anti-gravity. It's impossible to put down! 📚",
                "The math teacher called in sick with algebra! 🔢"
            ],
            "tech_humor": [
                "There are only 10 types of people: those who understand binary and those who don't! 👨‍💻",
                "Why do Java developers wear glasses? Because they can't C#! 👓",
                "A SQL query walks into a bar, approaches two tables, and asks: 'Can I join you?' 🍺",
                "How do you comfort a JavaScript bug? You console it! 🐛",
                "Why did the programmer quit his job? He didn't get arrays! 📊"
            ],
            "witty_comebacks": [
                "I'd agree with you, but then we'd both be wrong! 😏",
                "I'm not arguing, I'm just explaining why I'm right! 💡",
                "If I wanted to kill myself, I'd climb your ego and jump to your IQ! 🎯",
                "I'm not lazy, I'm just on energy-saving mode! 🔋",
                "I'm not short, I'm fun-sized! 📏"
            ],
            "encouragement": [
                "You've got this! 💪",
                "Believe in yourself - I certainly do! ⭐",
                "Every expert was once a beginner! 🌱",
                "Progress, not perfection! 📈",
                "You're doing better than you think! 👏"
            ]
        }
    
    async def enhance_response(self, base_response: str, original_message: str, user_context: Dict[str, Any]) -> str:
        """Enhance response with personality traits"""
        try:
            enhanced_response = base_response
            
            # Apply take-charge attitude
            if self.take_charge_attitude and random.random() < 0.4:
                enhanced_response = await self.add_confidence_boost(enhanced_response)
            
            # Apply engaging interaction style
            if self.interaction_style == 'engaging' and random.random() < 0.3:
                enhanced_response = await self.add_engaging_element(enhanced_response, original_message)
            
            # Add humor based on settings
            if self.humor_level == 'high' and random.random() < 0.25:
                enhanced_response = await self.inject_humor(enhanced_response, original_message)
            
            # Apply proactive suggestions
            if self.personality_settings.get('proactive', False) and random.random() < 0.2:
                enhanced_response = await self.add_proactive_suggestion(enhanced_response, user_context)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ Error enhancing response: {e}")
            return base_response
    
    async def add_confidence_boost(self, response: str) -> str:
        """Add confidence-boosting language"""
        if not response.strip():
            return response
        
        # Add confident starter
        if random.random() < 0.6:
            booster = random.choice(self.confidence_boosters)
            
            # Check if response already starts confidently
            confident_starters = ['absolutely', 'definitely', 'certainly', 'without', 'here\'s']
            if not any(response.lower().startswith(starter) for starter in confident_starters):
                response = f"{booster} {response.lower()}"
        
        # Add assertive language
        assertive_replacements = {
            'i think': 'I believe',
            'maybe': 'likely',
            'probably': 'most likely',
            'i guess': 'I\'d say',
            'perhaps': 'I suspect'
        }
        
        for weak, strong in assertive_replacements.items():
            response = response.replace(weak, strong)
        
        return response
    
    async def add_engaging_element(self, response: str, original_message: str) -> str:
        """Add engaging conversational elements"""
        # Add follow-up questions
        if not response.endswith('?') and random.random() < 0.4:
            follow_ups = [
                "What do you think about that?",
                "Have you experienced something similar?",
                "Does that match your experience?",
                "What's your take on this?",
                "How does that sound to you?"
            ]
            response += f" {random.choice(follow_ups)}"
        
        # Add engaging transitions for longer responses
        if len(response.split()) > 15 and random.random() < 0.3:
            sentences = response.split('. ')
            if len(sentences) > 1:
                transition = random.choice(self.engaging_transitions)
                # Insert transition between sentences
                insert_pos = len(sentences) // 2
                sentences[insert_pos] = f"{transition} {sentences[insert_pos].lower()}"
                response = '. '.join(sentences)
        
        return response
    
    async def inject_humor(self, response: str, original_message: str) -> str:
        """Inject appropriate humor into response"""
        try:
            message_lower = original_message.lower()
            
            # Choose humor type based on context
            if any(word in message_lower for word in ['code', 'program', 'computer', 'tech', 'software']):
                humor = random.choice(self.humor_database['tech_humor'])
            elif any(word in message_lower for word in ['sad', 'down', 'upset', 'bad']):
                humor = random.choice(self.humor_database['encouragement'])
            elif len(original_message.split()) < 5:  # Short message
                humor = random.choice(self.humor_database['puns'])
            else:
                # Random humor for general conversation
                all_humor = []
                for category in self.humor_database.values():
                    all_humor.extend(category)
                humor = random.choice(all_humor)
            
            # Add humor appropriately
            if random.random() < 0.5:
                # Add as separate line
                response += f"\n\n{humor}"
            else:
                # Add as continuation
                response += f" {humor}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error injecting humor: {e}")
            return response
    
    async def add_proactive_suggestion(self, response: str, user_context: Dict[str, Any]) -> str:
        """Add proactive suggestions based on context"""
        try:
            suggestions = []
            
            # Time-based suggestions
            hour = datetime.now().hour
            if 6 <= hour < 12:
                suggestions.extend([
                    "By the way, need any help planning your day?",
                    "Want me to search for something interesting to start your morning?",
                    "How about a motivational quote to kickstart your day?"
                ])
            elif 12 <= hour < 18:
                suggestions.extend([
                    "Need a quick break? I can tell you a joke!",
                    "Want me to find something cool online for you?",
                    "How about we generate a meme to brighten your afternoon?"
                ])
            else:
                suggestions.extend([
                    "Want to wind down with an interesting fact?",
                    "How about a relaxing story before you call it a day?",
                    "Need any help wrapping up your evening?"
                ])
            
            # Context-based suggestions
            recent_messages = user_context.get('messages', [])
            if len(recent_messages) > 5:
                suggestions.append("By the way, want me to analyze our recent conversation?")
            
            if user_context.get('preferences', {}).get('voice_responses'):
                suggestions.append("Want me to send my next response as a voice message?")
            
            if suggestions and random.random() < 0.7:
                suggestion = random.choice(suggestions)
                response += f"\n\n{suggestion}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error adding proactive suggestion: {e}")
            return response
    
    def get_personality_response_for_mood(self, mood: str) -> str:
        """Get personality-appropriate response for different moods"""
        mood_responses = {
            'excited': [
                "I love that energy! Let's keep this momentum going!",
                "Your excitement is contagious! What's got you so pumped?",
                "Yes! This is exactly the kind of vibe I'm here for!"
            ],
            'curious': [
                "Great question! I love when people dig deeper into things!",
                "Now that's the kind of curiosity that leads to awesome discoveries!",
                "I'm always up for exploring interesting topics together!"
            ],
            'frustrated': [
                "I hear you! Let's tackle this together and turn it around!",
                "Frustration means you care - let's channel that into solutions!",
                "Sometimes the best breakthroughs come after the toughest challenges!"
            ],
            'confused': [
                "No worries! Confusion just means we're learning something new!",
                "Let's break this down step by step - I'm here to help clarify!",
                "Questions are the beginning of understanding - let's explore this!"
            ]
        }
        
        return random.choice(mood_responses.get(mood, mood_responses['curious']))
    
    async def adapt_to_user_style(self, response: str, user_context: Dict[str, Any]) -> str:
        """Adapt response style to match user's communication pattern"""
        try:
            user_messages = user_context.get('messages', [])
            if len(user_messages) < 3:
                return response  # Not enough data to adapt
            
            # Analyze user's communication style
            recent_user_messages = [msg['content'] for msg in user_messages[-5:] if msg['role'] == 'user']
            
            if not recent_user_messages:
                return response
            
            # Calculate average message length
            avg_length = sum(len(msg.split()) for msg in recent_user_messages) / len(recent_user_messages)
            
            # Adapt response length
            if avg_length < 5:  # User prefers short messages
                # Shorten response if it's too long
                if len(response.split()) > 20:
                    sentences = response.split('. ')
                    response = '. '.join(sentences[:2]) + ('.' if not sentences[1].endswith('.') else '')
            
            elif avg_length > 20:  # User prefers longer messages
                # Add more detail if response is short
                if len(response.split()) < 10 and random.random() < 0.4:
                    elaborations = [
                        "Let me elaborate on that a bit more:",
                        "There's actually more to consider here:",
                        "This connects to some broader patterns I've noticed:",
                        "Here's why I find this particularly interesting:"
                    ]
                    response += f" {random.choice(elaborations)} [additional context would go here]"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error adapting to user style: {e}")
            return response
