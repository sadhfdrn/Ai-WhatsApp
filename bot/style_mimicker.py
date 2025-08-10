"""
Style Mimicker
Applies learned user communication patterns to AI responses for authentic personalization
"""

import re
import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class StyleMimicker:
    """Applies learned communication style to AI responses"""
    
    def __init__(self, profile_data: Dict[str, Any]):
        self.profile = profile_data
        self.communication_style = profile_data.get('communication_style', {})
        self.learned_patterns = profile_data.get('learned_patterns', {})
        self.conversation_context = profile_data.get('conversation_context', {})
        
        logger.info("🎭 Style Mimicker initialized with learned patterns")
    
    def apply_user_style(self, base_response: str, context: Dict[str, Any] = None) -> str:
        """Apply comprehensive learned communication style to AI response"""
        try:
            if not base_response.strip():
                return base_response
            
            styled_response = base_response
            
            # Apply response length preference
            styled_response = self._adjust_response_length(styled_response)
            
            # Apply learned punctuation style
            styled_response = self._apply_punctuation_style(styled_response)
            
            # Apply caps usage patterns
            styled_response = self._apply_caps_patterns(styled_response)
            
            # Insert learned phrases naturally
            styled_response = self._insert_common_phrases(styled_response)
            
            # Add appropriate emojis
            styled_response = self._add_learned_emojis(styled_response, context)
            
            # Apply tone based on context
            styled_response = self._apply_contextual_tone(styled_response, context)
            
            # Apply greeting/closing patterns
            styled_response = self._apply_greeting_closing_patterns(styled_response)
            
            return styled_response.strip()
            
        except Exception as e:
            logger.error(f"❌ Failed to apply user style: {e}")
            return base_response
    
    def _adjust_response_length(self, response: str) -> str:
        """Adjust response length based on user preference"""
        length_pref = self.communication_style.get('response_length_preference', 'medium')
        
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if length_pref == 'short' and len(sentences) > 2:
            # Keep only first 1-2 sentences
            response = '. '.join(sentences[:2]) + '.'
        elif length_pref == 'long' and len(sentences) < 3:
            # Add elaboration phrases
            elaborations = [
                "Let me explain further.",
                "Here's more detail on that.",
                "There's actually more to it.",
                "I can expand on this."
            ]
            if random.random() < 0.3:
                response += " " + random.choice(elaborations)
        
        return response
    
    def _apply_punctuation_style(self, response: str) -> str:
        """Apply learned punctuation patterns"""
        punctuation_style = self.communication_style.get('punctuation_style', 'standard')
        
        if punctuation_style == 'minimal_periods_lots_exclamations':
            # Reduce periods, increase exclamations for enthusiastic messages
            if random.random() < 0.4:
                response = response.replace('.', '!')
        elif punctuation_style == 'minimal_punctuation':
            # Remove some periods at end of sentences
            response = re.sub(r'\.(\s+)(?=[A-Z])', r'\1', response)
        
        # Apply ellipsis patterns if user uses them
        if random.random() < 0.2 and 'ellipsis_usage' in self.communication_style:
            response = response.replace('.', '...')
        
        return response
    
    def _apply_caps_patterns(self, response: str) -> str:
        """Apply capitalization patterns based on user style"""
        caps_frequency = self.communication_style.get('caps_usage_frequency', 0.1)
        
        if caps_frequency > 0.2:  # User uses caps frequently
            words = response.split()
            
            # Randomly capitalize some words for emphasis
            for i, word in enumerate(words):
                if len(word) > 3 and random.random() < caps_frequency * 0.5:
                    # Emphasize important words
                    if word.lower() in ['amazing', 'awesome', 'incredible', 'wow', 'yes', 'definitely']:
                        words[i] = word.upper()
            
            response = ' '.join(words)
        
        return response
    
    def _insert_common_phrases(self, response: str) -> str:
        """Naturally insert user's common phrases"""
        common_phrases = self.communication_style.get('common_phrases', {})
        
        if not common_phrases:
            return response
        
        # Sort phrases by frequency
        sorted_phrases = sorted(common_phrases.items(), key=lambda x: x[1], reverse=True)
        
        # Insert most common phrases occasionally
        for phrase, frequency in sorted_phrases[:5]:  # Top 5 most common phrases
            if frequency > 5 and random.random() < 0.15:  # 15% chance for frequent phrases
                # Insert at natural points
                if phrase.lower() in ['lol', 'haha', 'lmao']:
                    # Add humor phrases at the end
                    response += f" {phrase}"
                elif phrase.lower() in ['btw', 'oh']:
                    # Add transition phrases at the beginning
                    response = f"{phrase.capitalize()}, {response.lower()}"
                elif phrase.lower() in ['facts', 'absolutely', 'definitely']:
                    # Add agreement phrases at the beginning
                    response = f"{phrase.capitalize()}! {response}"
                break  # Only add one phrase per response
        
        return response
    
    def _add_learned_emojis(self, response: str, context: Dict[str, Any] = None) -> str:
        """Add emojis based on learned usage patterns"""
        emoji_usage = self.communication_style.get('emoji_usage', {})
        
        if not emoji_usage:
            return response
        
        # Sort emojis by frequency
        sorted_emojis = sorted(emoji_usage.items(), key=lambda x: x[1], reverse=True)
        
        # Determine response sentiment for appropriate emoji selection
        response_lower = response.lower()
        
        # Select emoji based on response content
        for emoji, frequency in sorted_emojis[:10]:  # Top 10 most used emojis
            if frequency > 3:  # Only use frequently used emojis
                
                # Match emojis to response content
                add_emoji = False
                
                if emoji in ['😂', '🤣', '😄'] and any(word in response_lower for word in ['funny', 'haha', 'joke', 'lol']):
                    add_emoji = random.random() < 0.6
                elif emoji in ['🔥', '💯', '⭐'] and any(word in response_lower for word in ['awesome', 'amazing', 'great', 'perfect']):
                    add_emoji = random.random() < 0.5
                elif emoji in ['🤔', '🧐'] and any(word in response_lower for word in ['think', 'consider', 'maybe', 'wonder']):
                    add_emoji = random.random() < 0.4
                elif emoji in ['💪', '🙌', '👏'] and any(word in response_lower for word in ['great job', 'well done', 'success', 'achieve']):
                    add_emoji = random.random() < 0.5
                elif frequency > 20:  # Very frequently used emojis
                    add_emoji = random.random() < 0.2
                
                if add_emoji:
                    response += f" {emoji}"
                    break  # Only add one emoji per response
        
        return response
    
    def _apply_contextual_tone(self, response: str, context: Dict[str, Any] = None) -> str:
        """Apply tone based on conversation context and learned mood patterns"""
        if not context:
            context = {}
        
        mood_patterns = self.conversation_context.get('mood_patterns', {})
        
        # Detect response sentiment
        response_lower = response.lower()
        
        # Apply learned tone patterns
        if any(word in response_lower for word in ['excited', 'amazing', 'awesome']):
            excited_pattern = mood_patterns.get('excited', 'enthusiastic_responses')
            if excited_pattern == 'caps_multiple_exclamations':
                response = re.sub(r'!', '!!!', response)
                # Capitalize some words
                words = response.split()
                for i, word in enumerate(words):
                    if word.lower() in ['wow', 'amazing', 'awesome', 'incredible']:
                        words[i] = word.upper()
                response = ' '.join(words)
        
        elif any(word in response_lower for word in ['casual', 'okay', 'sure']):
            casual_pattern = mood_patterns.get('casual', 'relaxed_tone')
            if casual_pattern == 'lowercase_minimal_punctuation':
                response = response.lower()
                response = response.replace('!', '')
                response = response.replace('.', '')
        
        return response
    
    def _apply_greeting_closing_patterns(self, response: str) -> str:
        """Apply learned greeting and closing patterns"""
        greeting_style = self.learned_patterns.get('greeting_style', 'casual')
        
        # Check if this looks like a greeting response
        if any(word in response.lower() for word in ['hello', 'hi', 'hey']):
            greeting_replacements = {
                'casual': {'hello': 'hey', 'hi': 'yo', 'good morning': 'morning'},
                'enthusiastic': {'hello': 'hey there!', 'hi': 'hi there!'},
                'formal': {'hey': 'hello', 'yo': 'good day'}
            }
            
            replacements = greeting_replacements.get(greeting_style, {})
            for formal, casual in replacements.items():
                response = re.sub(r'\b' + re.escape(formal) + r'\b', casual, response, flags=re.IGNORECASE)
        
        return response
    
    def get_contextual_response_style(self, topic: str = None, mood: str = None) -> Dict[str, Any]:
        """Get appropriate style settings for specific context"""
        style_config = {
            "emoji_probability": 0.3,
            "phrase_insertion_probability": 0.2,
            "caps_usage": self.communication_style.get('caps_usage_frequency', 0.1),
            "punctuation_style": self.communication_style.get('punctuation_style', 'standard'),
            "response_length": self.communication_style.get('response_length_preference', 'medium')
        }
        
        # Adjust based on topic
        if topic:
            favorite_topics = self.conversation_context.get('favorite_topics', [])
            if topic.lower() in [t.lower() for t in favorite_topics]:
                # User is interested in this topic - be more enthusiastic
                style_config["emoji_probability"] = 0.5
                style_config["phrase_insertion_probability"] = 0.3
        
        # Adjust based on mood
        if mood:
            mood_patterns = self.conversation_context.get('mood_patterns', {})
            mood_style = mood_patterns.get(mood, 'neutral')
            
            if 'enthusiastic' in mood_style or 'excited' in mood_style:
                style_config["emoji_probability"] = 0.6
                style_config["caps_usage"] *= 2
            elif 'casual' in mood_style:
                style_config["punctuation_style"] = 'minimal'
                style_config["response_length"] = 'short'
        
        return style_config
    
    def generate_personalized_greeting(self) -> str:
        """Generate a greeting in user's learned style"""
        greeting_style = self.learned_patterns.get('greeting_style', 'casual')
        common_phrases = self.communication_style.get('common_phrases', {})
        
        base_greetings = {
            'casual': ['hey', 'hi there', 'what\'s up'],
            'enthusiastic': ['hey there!', 'hi!', 'hello there!'],
            'formal': ['hello', 'good day', 'greetings']
        }
        
        greeting = random.choice(base_greetings.get(greeting_style, base_greetings['casual']))
        
        # Add user's common phrases if appropriate
        if 'yo' in common_phrases and common_phrases['yo'] > 5:
            greeting = 'yo'
        
        return greeting
    
    def update_profile(self, new_profile_data: Dict[str, Any]):
        """Update the profile data used for styling"""
        self.profile = new_profile_data
        self.communication_style = new_profile_data.get('communication_style', {})
        self.learned_patterns = new_profile_data.get('learned_patterns', {})
        self.conversation_context = new_profile_data.get('conversation_context', {})
        
        logger.info("🔄 Style Mimicker updated with new profile data")