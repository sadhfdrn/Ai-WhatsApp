"""
Enhanced Auto-Reply Manager
Learns user patterns and provides intelligent auto-replies with personality
"""

import asyncio
import logging
import random
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class AutoReplyManager:
    """Enhanced auto-reply system with pattern learning and personality"""
    
    def __init__(self, config):
        self.config = config
        self.enabled_users = set()
        self.user_patterns = defaultdict(dict)
        self.conversation_styles = defaultdict(dict)
        self.response_timing = defaultdict(list)
        
        # Auto-reply settings
        self.min_delay = config.AUTO_REPLY_DELAY_MIN
        self.max_delay = config.AUTO_REPLY_DELAY_MAX
        self.learning_mode = getattr(config, 'LEARNING_MODE', True)
        
        # Pattern analysis
        self.message_history = defaultdict(list)
        self.topic_preferences = defaultdict(dict)
        self.interaction_patterns = defaultdict(dict)
        
        # Auto-reply templates with personality
        self.response_templates = self._load_response_templates()
        
        logger.info("🤖 Enhanced Auto-Reply Manager initialized")
    
    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates categorized by situation"""
        return {
            'greeting_responses': [
                "Hey! Great to hear from you! 😊",
                "Hi there! What's on your mind today?",
                "Hello! I was just thinking about our last conversation!",
                "Hey! Perfect timing - I was hoping you'd message!",
                "Hi! Ready for another interesting chat?"
            ],
            'question_responses': [
                "That's a great question! Let me think about that...",
                "Interesting! Here's what I think about that:",
                "Ooh, I love questions like this! My take is:",
                "Great question! You always ask the good ones!",
                "That's definitely worth discussing! I'd say:"
            ],
            'agreement_responses': [
                "Absolutely! You're spot on about that!",
                "Exactly! I couldn't agree more!",
                "Yes! You've hit the nail on the head!",
                "Totally! That's exactly what I was thinking!",
                "Right?! You get it completely!"
            ],
            'encouragement_responses': [
                "You've got this! I believe in you! 💪",
                "That sounds challenging, but you're capable of handling it!",
                "I'm confident you'll figure it out - you always do!",
                "Keep going! You're making great progress!",
                "Don't give up! You're closer than you think!"
            ],
            'empathy_responses': [
                "I hear you. That sounds really tough.",
                "That must be frustrating. I'm here to listen.",
                "I can understand why you'd feel that way.",
                "That's a lot to deal with. How are you holding up?",
                "Thanks for sharing that with me. I appreciate your trust."
            ],
            'curiosity_responses': [
                "Tell me more about that! I'm genuinely curious.",
                "That sounds fascinating! What happened next?",
                "Interesting! I'd love to hear more details.",
                "Wow, that's intriguing! Can you elaborate?",
                "That caught my attention! What's the full story?"
            ],
            'transition_responses': [
                "Speaking of which, have you thought about...",
                "That reminds me of something interesting...",
                "On a related note, did you know...",
                "While we're on this topic...",
                "That makes me think of..."
            ]
        }
    
    async def enable_auto_reply(self, user_id: str, ai_processor=None) -> str:
        """Enable auto-reply for a user"""
        try:
            self.enabled_users.add(user_id)
            
            # Initialize user patterns if not exists
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {
                    'message_frequency': [],
                    'common_topics': [],
                    'response_style': 'casual',
                    'preferred_length': 'medium',
                    'emoji_usage': 'moderate',
                    'question_frequency': 0.3
                }
            
            # Learn from existing conversation if AI processor available
            if ai_processor:
                await self._analyze_existing_patterns(user_id, ai_processor)
            
            logger.info(f"✅ Auto-reply enabled for user: {user_id}")
            return f"🤖 Auto-reply is now enabled! I'll respond to your messages automatically based on your conversation style. You can disable it anytime with `!autoreply off`."
            
        except Exception as e:
            logger.error(f"❌ Error enabling auto-reply: {e}")
            return "Sorry, I couldn't enable auto-reply right now. Please try again later."
    
    async def disable_auto_reply(self, user_id: str) -> str:
        """Disable auto-reply for a user"""
        try:
            self.enabled_users.discard(user_id)
            logger.info(f"🔇 Auto-reply disabled for user: {user_id}")
            return "🔇 Auto-reply disabled. I'll only respond when you specifically ask me something!"
        except Exception as e:
            logger.error(f"❌ Error disabling auto-reply: {e}")
            return "I had trouble disabling auto-reply, but you can try again."
    
    def is_enabled(self, user_id: str) -> bool:
        """Check if auto-reply is enabled for user"""
        return user_id in self.enabled_users
    
    async def should_auto_reply(self, user_id: str, message: str, context: Dict[str, Any]) -> bool:
        """Determine if bot should auto-reply to this message"""
        if not self.is_enabled(user_id):
            return False
        
        try:
            # Don't auto-reply to commands
            if message.strip().startswith(('!', '/', '@')):
                return False
            
            # Don't auto-reply to very short messages sometimes
            if len(message.split()) < 2 and random.random() < 0.3:
                return False
            
            # Check timing patterns
            if not await self._is_good_timing(user_id):
                return False
            
            # Analyze message to decide reply probability
            reply_probability = await self._calculate_reply_probability(user_id, message, context)
            
            return random.random() < reply_probability
            
        except Exception as e:
            logger.error(f"❌ Error determining auto-reply: {e}")
            return False
    
    async def generate_auto_reply(self, user_id: str, message: str, context: Dict[str, Any], ai_processor=None) -> Optional[str]:
        """Generate contextual auto-reply based on user patterns"""
        try:
            if not self.is_enabled(user_id):
                return None
            
            # Update patterns with this message
            await self._update_user_patterns(user_id, message)
            
            # Analyze message sentiment and type
            message_analysis = await self._analyze_message(message)
            
            # Get user's conversation style
            user_style = self.user_patterns[user_id]
            
            # Generate response based on analysis and style
            response = await self._generate_contextual_response(
                user_id, message, message_analysis, user_style, context, ai_processor
            )
            
            # Apply user's preferred style
            response = await self._apply_user_style(response, user_style)
            
            # Record response timing
            self.response_timing[user_id].append(time.time())
            if len(self.response_timing[user_id]) > 50:
                self.response_timing[user_id] = self.response_timing[user_id][-50:]
            
            logger.info(f"🤖 Auto-reply generated for {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generating auto-reply: {e}")
            return None
    
    async def _analyze_existing_patterns(self, user_id: str, ai_processor):
        """Analyze existing conversation patterns from AI processor"""
        try:
            if hasattr(ai_processor, 'conversation_history'):
                history = ai_processor.conversation_history.get(user_id, [])
                
                if len(history) < 3:
                    return  # Not enough data
                
                # Analyze user messages
                user_messages = [h['content'] for h in history if h['role'] == 'user']
                
                if user_messages:
                    # Calculate average message length
                    avg_length = sum(len(msg.split()) for msg in user_messages) / len(user_messages)
                    
                    # Determine preferred response length
                    if avg_length < 5:
                        self.user_patterns[user_id]['preferred_length'] = 'short'
                    elif avg_length > 20:
                        self.user_patterns[user_id]['preferred_length'] = 'long'
                    else:
                        self.user_patterns[user_id]['preferred_length'] = 'medium'
                    
                    # Analyze emoji usage
                    emoji_count = sum(msg.count('😊') + msg.count('😂') + msg.count('🔥') + 
                                    msg.count('❤️') + msg.count('👍') for msg in user_messages)
                    emoji_ratio = emoji_count / len(user_messages)
                    
                    if emoji_ratio > 0.5:
                        self.user_patterns[user_id]['emoji_usage'] = 'high'
                    elif emoji_ratio > 0.2:
                        self.user_patterns[user_id]['emoji_usage'] = 'moderate'
                    else:
                        self.user_patterns[user_id]['emoji_usage'] = 'low'
                    
                    # Analyze question frequency
                    question_count = sum('?' in msg for msg in user_messages)
                    self.user_patterns[user_id]['question_frequency'] = question_count / len(user_messages)
                    
                    logger.info(f"📊 Analyzed patterns for {user_id}: {self.user_patterns[user_id]}")
                    
        except Exception as e:
            logger.error(f"❌ Error analyzing existing patterns: {e}")
    
    async def _is_good_timing(self, user_id: str) -> bool:
        """Check if timing is appropriate for auto-reply"""
        try:
            # Check recent response frequency
            recent_responses = [
                t for t in self.response_timing[user_id] 
                if time.time() - t < 300  # Last 5 minutes
            ]
            
            # Don't overwhelm user with responses
            if len(recent_responses) > 3:
                return False
            
            # Random delay based on user patterns
            if random.random() < 0.3:  # 30% chance to skip for natural feel
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking timing: {e}")
            return True
    
    async def _calculate_reply_probability(self, user_id: str, message: str, context: Dict[str, Any]) -> float:
        """Calculate probability of replying based on message and context"""
        try:
            base_probability = 0.6  # Base 60% chance
            
            # Increase for questions
            if '?' in message:
                base_probability += 0.3
            
            # Increase for longer messages
            if len(message.split()) > 10:
                base_probability += 0.2
            
            # Increase for emotional content
            emotional_words = ['excited', 'sad', 'happy', 'frustrated', 'amazing', 'terrible']
            if any(word in message.lower() for word in emotional_words):
                base_probability += 0.25
            
            # Decrease for very recent activity
            recent_messages = context.get('recent_message_count', 0)
            if recent_messages > 5:
                base_probability -= 0.3
            
            # Cap probability
            return min(base_probability, 0.9)
            
        except Exception as e:
            logger.error(f"❌ Error calculating reply probability: {e}")
            return 0.5
    
    async def _analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze message for sentiment, type, and content"""
        message_lower = message.lower()
        
        analysis = {
            'type': 'statement',
            'sentiment': 'neutral',
            'topics': [],
            'urgency': 'normal',
            'emotional_tone': 'neutral'
        }
        
        # Message type
        if '?' in message:
            analysis['type'] = 'question'
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
            analysis['type'] = 'greeting'
        elif any(word in message_lower for word in ['thanks', 'thank you', 'appreciate', 'grateful']):
            analysis['type'] = 'gratitude'
        elif any(word in message_lower for word in ['help', 'problem', 'issue', 'trouble']):
            analysis['type'] = 'help_request'
        
        # Sentiment analysis (simple)
        positive_words = ['good', 'great', 'awesome', 'amazing', 'love', 'happy', 'excited']
        negative_words = ['bad', 'terrible', 'sad', 'frustrated', 'angry', 'disappointed']
        
        positive_count = sum(word in message_lower for word in positive_words)
        negative_count = sum(word in message_lower for word in negative_words)
        
        if positive_count > negative_count:
            analysis['sentiment'] = 'positive'
        elif negative_count > positive_count:
            analysis['sentiment'] = 'negative'
        
        # Emotional tone
        if any(word in message_lower for word in ['!', 'wow', 'omg', 'amazing', 'incredible']):
            analysis['emotional_tone'] = 'excited'
        elif any(word in message_lower for word in ['sad', 'disappointed', 'upset']):
            analysis['emotional_tone'] = 'sad'
        elif any(word in message_lower for word in ['frustrated', 'angry', 'annoyed']):
            analysis['emotional_tone'] = 'frustrated'
        
        return analysis
    
    async def _generate_contextual_response(self, user_id: str, message: str, analysis: Dict[str, Any], 
                                          user_style: Dict[str, Any], context: Dict[str, Any], ai_processor=None) -> str:
        """Generate contextual response based on analysis"""
        try:
            response_type = analysis['type']
            sentiment = analysis['sentiment']
            
            # Choose appropriate response template
            if response_type == 'greeting':
                templates = self.response_templates['greeting_responses']
            elif response_type == 'question':
                templates = self.response_templates['question_responses']
            elif sentiment == 'positive':
                templates = self.response_templates['agreement_responses']
            elif sentiment == 'negative':
                templates = self.response_templates['empathy_responses']
            elif response_type == 'help_request':
                templates = self.response_templates['encouragement_responses']
            else:
                templates = self.response_templates['curiosity_responses']
            
            # Select base response
            base_response = random.choice(templates)
            
            # Add contextual elements
            if analysis['emotional_tone'] == 'excited':
                base_response += " Your energy is contagious!"
            elif analysis['emotional_tone'] == 'sad':
                base_response += " I'm here if you need to talk more about it."
            
            # Add follow-up based on user patterns
            if user_style.get('question_frequency', 0) > 0.4:
                follow_ups = [
                    " What's your take on that?",
                    " How do you see it?",
                    " What do you think about it?",
                    " Does that resonate with you?"
                ]
                base_response += random.choice(follow_ups)
            
            # Use AI processor for enhanced responses if available
            if ai_processor and random.random() < 0.3:  # 30% chance for AI enhancement
                try:
                    ai_enhanced = await ai_processor.generate_response(message, user_id, context)
                    if ai_enhanced and len(ai_enhanced) < 200:  # Use if not too long
                        return ai_enhanced
                except:
                    pass  # Fall back to template response
            
            return base_response
            
        except Exception as e:
            logger.error(f"❌ Error generating contextual response: {e}")
            return "That's interesting! I'd love to hear more about your thoughts on this."
    
    async def _apply_user_style(self, response: str, user_style: Dict[str, Any]) -> str:
        """Apply user's preferred communication style to response"""
        try:
            # Adjust length
            preferred_length = user_style.get('preferred_length', 'medium')
            
            if preferred_length == 'short' and len(response.split()) > 15:
                # Shorten response
                sentences = response.split('. ')
                response = sentences[0] + ('.' if not sentences[0].endswith('.') else '')
            elif preferred_length == 'long' and len(response.split()) < 10:
                # Extend response
                extensions = [
                    " I've been thinking about this kind of thing lately.",
                    " It's fascinating how these topics come up in conversation.",
                    " There's always more to explore on subjects like this.",
                    " I find these discussions really engaging."
                ]
                response += random.choice(extensions)
            
            # Adjust emoji usage
            emoji_usage = user_style.get('emoji_usage', 'moderate')
            
            if emoji_usage == 'high' and not any(char in response for char in ['😊', '😂', '🔥', '❤️', '👍', '💪', '🤔']):
                # Add appropriate emoji
                emojis = ['😊', '🤔', '💭', '✨', '🌟']
                response += f" {random.choice(emojis)}"
            elif emoji_usage == 'low':
                # Remove emojis
                response = ''.join(char for char in response if ord(char) < 127 or char.isspace())
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error applying user style: {e}")
            return response
    
    async def _update_user_patterns(self, user_id: str, message: str):
        """Update user patterns based on new message"""
        try:
            current_time = time.time()
            
            # Update message history
            self.message_history[user_id].append({
                'content': message,
                'timestamp': current_time,
                'length': len(message.split())
            })
            
            # Keep only recent history
            if len(self.message_history[user_id]) > 100:
                self.message_history[user_id] = self.message_history[user_id][-100:]
            
            # Update frequency patterns
            recent_messages = [
                msg for msg in self.message_history[user_id]
                if current_time - msg['timestamp'] < 3600  # Last hour
            ]
            
            if len(recent_messages) > 1:
                # Calculate average time between messages
                intervals = []
                for i in range(1, len(recent_messages)):
                    interval = recent_messages[i]['timestamp'] - recent_messages[i-1]['timestamp']
                    intervals.append(interval)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    self.user_patterns[user_id]['avg_message_interval'] = avg_interval
            
        except Exception as e:
            logger.error(f"❌ Error updating user patterns: {e}")
    
    async def get_auto_reply_delay(self, user_id: str) -> float:
        """Get appropriate delay before auto-reply"""
        try:
            # Base delay from config
            base_delay = random.uniform(self.min_delay, self.max_delay)
            
            # Adjust based on user patterns
            user_pattern = self.user_patterns.get(user_id, {})
            avg_interval = user_pattern.get('avg_message_interval', 30)
            
            # If user typically responds quickly, respond quicker
            if avg_interval < 10:
                base_delay *= 0.7
            elif avg_interval > 60:
                base_delay *= 1.3
            
            return max(2.0, min(base_delay, 30.0))  # Between 2-30 seconds
            
        except Exception as e:
            logger.error(f"❌ Error calculating delay: {e}")
            return random.uniform(self.min_delay, self.max_delay)
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get auto-reply statistics for user"""
        try:
            return {
                'auto_reply_enabled': self.is_enabled(user_id),
                'patterns': self.user_patterns.get(user_id, {}),
                'message_history_count': len(self.message_history.get(user_id, [])),
                'recent_responses': len([
                    t for t in self.response_timing.get(user_id, [])
                    if time.time() - t < 3600
                ])
            }
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return {'error': str(e)}