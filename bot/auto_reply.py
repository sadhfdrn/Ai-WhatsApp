"""
Auto-Reply Management System
Handles automatic responses, user mimicking, and proactive messaging
"""

import asyncio
import logging
import random
from typing import Dict, Any, Set, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class AutoReplyManager:
    """Manages automatic replies and user behavior mimicking"""
    
    def __init__(self, config):
        self.config = config
        self.enabled_users: Set[str] = set()
        self.user_patterns: Dict[str, Dict[str, Any]] = {}
        self.scheduled_replies: Dict[str, Dict[str, Any]] = {}
        
        # Auto-reply settings
        self.min_delay = config.AUTO_REPLY_DELAY_MIN
        self.max_delay = config.AUTO_REPLY_DELAY_MAX
        self.enabled_globally = config.AUTO_REPLY_ENABLED
        
        # Pattern learning settings
        self.min_messages_for_pattern = 5
        self.pattern_confidence_threshold = 0.7
        
        # Proactive messaging
        self.proactive_enabled = config.PROACTIVE_MESSAGING
        self.proactive_cooldown = 3600  # 1 hour between proactive messages
        self.last_proactive_message: Dict[str, datetime] = {}
        
        logger.info("🔄 Auto-reply manager initialized")
    
    def enable_for_user(self, user_id: str):
        """Enable auto-reply for specific user"""
        self.enabled_users.add(user_id)
        logger.info(f"✅ Auto-reply enabled for user: {user_id}")
    
    def disable_for_user(self, user_id: str):
        """Disable auto-reply for specific user"""
        self.enabled_users.discard(user_id)
        
        # Cancel any scheduled replies
        if user_id in self.scheduled_replies:
            del self.scheduled_replies[user_id]
        
        logger.info(f"⏹️ Auto-reply disabled for user: {user_id}")
    
    def is_enabled_for_user(self, user_id: str) -> bool:
        """Check if auto-reply is enabled for user"""
        return user_id in self.enabled_users and self.enabled_globally
    
    async def schedule_reply(self, user_id: str, message: str, whatsapp_client):
        """Schedule an automatic reply"""
        if not self.is_enabled_for_user(user_id):
            return
        
        try:
            # Learn from user's message patterns
            await self.learn_user_pattern(user_id, message)
            
            # Generate delay based on user patterns or default range
            delay = self.calculate_reply_delay(user_id)
            
            # Schedule the reply
            reply_data = {
                'user_id': user_id,
                'original_message': message,
                'scheduled_time': datetime.now() + timedelta(seconds=delay),
                'client': whatsapp_client
            }
            
            self.scheduled_replies[user_id] = reply_data
            
            # Schedule the actual reply
            asyncio.create_task(self.execute_scheduled_reply(reply_data))
            
            logger.info(f"📅 Auto-reply scheduled for {user_id} in {delay}s")
            
        except Exception as e:
            logger.error(f"❌ Auto-reply scheduling error: {e}")
    
    async def execute_scheduled_reply(self, reply_data: Dict[str, Any]):
        """Execute a scheduled reply"""
        try:
            # Wait for the scheduled time
            delay = (reply_data['scheduled_time'] - datetime.now()).total_seconds()
            
            if delay > 0:
                await asyncio.sleep(delay)
            
            user_id = reply_data['user_id']
            
            # Check if auto-reply is still enabled
            if not self.is_enabled_for_user(user_id):
                logger.info(f"⏹️ Auto-reply cancelled for {user_id} - disabled")
                return
            
            # Generate contextual auto-reply
            reply_message = await self.generate_auto_reply(
                user_id, 
                reply_data['original_message']
            )
            
            if reply_message:
                # Send the reply
                client = reply_data['client']
                await client.send_message(user_id, reply_message, add_ai_icon=True)
                
                logger.info(f"🤖 Auto-reply sent to {user_id}: {reply_message[:50]}...")
            
            # Clean up scheduled reply
            if user_id in self.scheduled_replies:
                del self.scheduled_replies[user_id]
                
        except Exception as e:
            logger.error(f"❌ Auto-reply execution error: {e}")
    
    async def learn_user_pattern(self, user_id: str, message: str):
        """Learn communication patterns from user messages"""
        try:
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {
                    'messages': [],
                    'avg_length': 0,
                    'common_words': {},
                    'response_times': [],
                    'emoji_usage': {},
                    'conversation_style': 'neutral'
                }
            
            pattern = self.user_patterns[user_id]
            
            # Store message for analysis
            pattern['messages'].append({
                'text': message,
                'timestamp': datetime.now().isoformat(),
                'length': len(message.split())
            })
            
            # Keep only recent messages for pattern learning
            if len(pattern['messages']) > 50:
                pattern['messages'] = pattern['messages'][-50:]
            
            # Update average message length
            lengths = [msg['length'] for msg in pattern['messages']]
            pattern['avg_length'] = sum(lengths) / len(lengths)
            
            # Analyze word frequency
            words = message.lower().split()
            for word in words:
                if len(word) > 2:  # Skip very short words
                    pattern['common_words'][word] = pattern['common_words'].get(word, 0) + 1
            
            # Analyze emoji usage
            import re
            emoji_pattern = re.compile("["
                                     "\U0001F600-\U0001F64F"  # emoticons
                                     "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                     "\U0001F680-\U0001F6FF"  # transport & map
                                     "\U0001F1E0-\U0001F1FF"  # flags
                                     "]+", flags=re.UNICODE)
            
            emojis = emoji_pattern.findall(message)
            for emoji in emojis:
                pattern['emoji_usage'][emoji] = pattern['emoji_usage'].get(emoji, 0) + 1
            
            # Determine conversation style
            pattern['conversation_style'] = self.analyze_conversation_style(pattern)
            
            logger.debug(f"📊 Pattern updated for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Pattern learning error: {e}")
    
    def analyze_conversation_style(self, pattern: Dict[str, Any]) -> str:
        """Analyze user's conversation style"""
        try:
            messages = pattern['messages']
            if len(messages) < 3:
                return 'neutral'
            
            # Analyze characteristics
            avg_length = pattern['avg_length']
            emoji_count = sum(pattern['emoji_usage'].values())
            message_count = len(messages)
            
            # Check for enthusiasm indicators
            enthusiastic_words = ['awesome', 'great', 'amazing', 'love', 'excited', 'cool']
            enthusiastic_count = sum(
                pattern['common_words'].get(word, 0) for word in enthusiastic_words
            )
            
            # Check for casual indicators
            casual_words = ['yeah', 'ok', 'sure', 'nah', 'lol', 'haha']
            casual_count = sum(
                pattern['common_words'].get(word, 0) for word in casual_words
            )
            
            # Determine style
            emoji_ratio = emoji_count / message_count if message_count > 0 else 0
            
            if emoji_ratio > 0.5 or enthusiastic_count > 2:
                return 'enthusiastic'
            elif casual_count > 2 or avg_length < 5:
                return 'casual'
            elif avg_length > 15:
                return 'detailed'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"❌ Style analysis error: {e}")
            return 'neutral'
    
    def calculate_reply_delay(self, user_id: str) -> int:
        """Calculate appropriate reply delay based on user patterns"""
        try:
            if user_id in self.user_patterns:
                pattern = self.user_patterns[user_id]
                style = pattern.get('conversation_style', 'neutral')
                
                # Adjust delay based on conversation style
                if style == 'enthusiastic':
                    # Reply faster to enthusiastic users
                    min_delay = max(2, self.min_delay - 2)
                    max_delay = max(8, self.max_delay - 5)
                elif style == 'casual':
                    # Moderate delay for casual users
                    min_delay = self.min_delay
                    max_delay = self.max_delay
                elif style == 'detailed':
                    # Longer delay for detailed users (they might expect thoughtful responses)
                    min_delay = self.min_delay + 3
                    max_delay = self.max_delay + 10
                else:
                    min_delay = self.min_delay
                    max_delay = self.max_delay
            else:
                min_delay = self.min_delay
                max_delay = self.max_delay
            
            return random.randint(min_delay, max_delay)
            
        except Exception as e:
            logger.error(f"❌ Delay calculation error: {e}")
            return random.randint(self.min_delay, self.max_delay)
    
    async def generate_auto_reply(self, user_id: str, original_message: str) -> Optional[str]:
        """Generate automatic reply mimicking user's style"""
        try:
            if user_id not in self.user_patterns:
                return None
            
            pattern = self.user_patterns[user_id]
            style = pattern.get('conversation_style', 'neutral')
            
            # Generate reply based on user's style
            if style == 'enthusiastic':
                replies = await self.generate_enthusiastic_replies(original_message, pattern)
            elif style == 'casual':
                replies = await self.generate_casual_replies(original_message, pattern)
            elif style == 'detailed':
                replies = await self.generate_detailed_replies(original_message, pattern)
            else:
                replies = await self.generate_neutral_replies(original_message, pattern)
            
            if replies:
                return random.choice(replies)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Auto-reply generation error: {e}")
            return None
    
    async def generate_enthusiastic_replies(self, message: str, pattern: Dict[str, Any]) -> List[str]:
        """Generate enthusiastic auto-replies"""
        # Get user's favorite emojis
        favorite_emojis = sorted(pattern['emoji_usage'].items(), key=lambda x: x[1], reverse=True)[:3]
        emoji_str = ''.join([emoji[0] for emoji in favorite_emojis]) if favorite_emojis else '😄🎉⚡'
        
        replies = [
            f"That's amazing! {emoji_str}",
            f"I love your energy! {emoji_str}",
            f"You always bring such great vibes! {emoji_str}",
            f"That's so cool! Thanks for sharing {emoji_str}",
            f"Your enthusiasm is contagious! {emoji_str}",
            f"Yes! That's exactly what I was thinking! {emoji_str}",
            f"You're absolutely right about that! {emoji_str}"
        ]
        
        return replies
    
    async def generate_casual_replies(self, message: str, pattern: Dict[str, Any]) -> List[str]:
        """Generate casual auto-replies"""
        casual_words = ['yeah', 'ok', 'cool', 'nice', 'sure', 'gotcha', 'alright']
        
        # Use user's common casual words if available
        user_casual = [word for word in casual_words if word in pattern['common_words']]
        if user_casual:
            primary_word = random.choice(user_casual)
        else:
            primary_word = random.choice(casual_words)
        
        replies = [
            f"{primary_word.capitalize()}, that makes sense",
            f"{primary_word.capitalize()}!",
            f"Oh {primary_word}, I see what you mean",
            f"{primary_word.capitalize()}, good point",
            f"Mm {primary_word}, interesting",
            f"{primary_word.capitalize()}, thanks for that",
            f"Right, {primary_word}"
        ]
        
        return replies
    
    async def generate_detailed_replies(self, message: str, pattern: Dict[str, Any]) -> List[str]:
        """Generate detailed auto-replies"""
        replies = [
            "That's a really thoughtful perspective. I appreciate how you've broken that down and the nuance you've brought to the topic.",
            "I find your analysis quite compelling. There are definitely multiple layers to consider when thinking about this kind of situation.",
            "You've raised some excellent points that I hadn't fully considered before. The way you've connected these ideas shows real insight.",
            "This is exactly the kind of detailed thinking that leads to better understanding. Thank you for taking the time to explain your viewpoint so thoroughly.",
            "Your comprehensive approach to this topic is refreshing. It's clear you've given this considerable thought and consideration.",
            "I appreciate the depth of your response. These are complex issues that benefit from the kind of careful analysis you've provided."
        ]
        
        return replies
    
    async def generate_neutral_replies(self, message: str, pattern: Dict[str, Any]) -> List[str]:
        """Generate neutral auto-replies"""
        replies = [
            "Thanks for sharing that with me.",
            "I understand what you're saying.",
            "That's a good point to consider.",
            "I appreciate you letting me know.",
            "Thanks for the update.",
            "That's helpful to know.",
            "I see where you're coming from.",
            "Good to hear from you.",
            "Thanks for thinking of me.",
            "I'm glad you shared that."
        ]
        
        return replies
    
    async def should_send_proactive_message(self, user_id: str) -> bool:
        """Check if it's appropriate to send a proactive message"""
        try:
            if not self.proactive_enabled:
                return False
            
            if not self.is_enabled_for_user(user_id):
                return False
            
            # Check cooldown
            if user_id in self.last_proactive_message:
                time_since_last = datetime.now() - self.last_proactive_message[user_id]
                if time_since_last.total_seconds() < self.proactive_cooldown:
                    return False
            
            # Check if user has been active recently
            if user_id in self.user_patterns:
                pattern = self.user_patterns[user_id]
                recent_messages = [
                    msg for msg in pattern['messages']
                    if datetime.fromisoformat(msg['timestamp']) > datetime.now() - timedelta(hours=6)
                ]
                
                # Only send proactive messages to recently active users
                return len(recent_messages) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Proactive message check error: {e}")
            return False
    
    async def generate_proactive_message(self, user_id: str) -> Optional[str]:
        """Generate a proactive message for the user"""
        try:
            if not await self.should_send_proactive_message(user_id):
                return None
            
            pattern = self.user_patterns.get(user_id, {})
            style = pattern.get('conversation_style', 'neutral')
            
            # Time-based proactive messages
            hour = datetime.now().hour
            
            if 6 <= hour < 12:  # Morning
                time_messages = [
                    "Good morning! Hope you're having a great start to your day!",
                    "Morning! Anything interesting planned for today?",
                    "Hey there! How's your morning going so far?"
                ]
            elif 12 <= hour < 18:  # Afternoon
                time_messages = [
                    "Hope your day is going well! Anything exciting happening?",
                    "Afternoon check-in! How are things on your end?",
                    "Hey! Just wanted to see how your day is shaping up."
                ]
            else:  # Evening
                time_messages = [
                    "Evening! How did your day go?",
                    "Hope you had a good day! Anything worth sharing?",
                    "Hey there! Winding down from the day?"
                ]
            
            # Style-specific adjustments
            if style == 'enthusiastic':
                proactive_messages = [msg + " 😊🌟" for msg in time_messages]
            elif style == 'casual':
                proactive_messages = ["Hey, " + msg.lower() for msg in time_messages]
            else:
                proactive_messages = time_messages
            
            # Mark that we sent a proactive message
            self.last_proactive_message[user_id] = datetime.now()
            
            return random.choice(proactive_messages)
            
        except Exception as e:
            logger.error(f"❌ Proactive message generation error: {e}")
            return None
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user"""
        if user_id not in self.user_patterns:
            return {"error": "No data available for this user"}
        
        pattern = self.user_patterns[user_id]
        
        return {
            "auto_reply_enabled": self.is_enabled_for_user(user_id),
            "messages_analyzed": len(pattern['messages']),
            "avg_message_length": round(pattern['avg_length'], 1),
            "conversation_style": pattern['conversation_style'],
            "favorite_emojis": list(pattern['emoji_usage'].keys())[:5],
            "common_words": list(pattern['common_words'].keys())[:10],
            "last_proactive_message": self.last_proactive_message.get(user_id, "Never").isoformat() if isinstance(self.last_proactive_message.get(user_id), datetime) else str(self.last_proactive_message.get(user_id, "Never"))
        }
