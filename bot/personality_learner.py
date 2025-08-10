"""
Personality Learning System
Analyzes user communication patterns and learns personalized response styles
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
import asyncio

logger = logging.getLogger(__name__)

class PersonalityLearner:
    """Intelligent learning system for user communication patterns"""
    
    def __init__(self, profile_manager):
        self.profile_manager = profile_manager
        self.current_profile = profile_manager.load_profile()
        self.conversation_buffer = []
        self.save_threshold = 10  # Save every 10 interactions
        self.interaction_count = 0
        
        # Learning weights for pattern analysis
        self.phrase_weight = 0.7
        self.emoji_weight = 0.8
        self.tone_weight = 0.6
        self.topic_weight = 0.5
        
        logger.info("🧠 Personality Learner initialized")
    
    async def learn_from_user_message(self, message: str, context: Dict[str, Any] = None):
        """Analyze and learn from user's message patterns"""
        try:
            if not message or len(message.strip()) < 3:
                return
            
            # Analyze message patterns
            patterns = await self.analyze_message_patterns(message)
            
            # Update conversation buffer
            conversation_entry = {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "message": message,
                "patterns": patterns,
                "context": context or {}
            }
            self.conversation_buffer.append(conversation_entry)
            
            # Update profile with new patterns
            await self.update_profile_with_patterns(patterns)
            
            self.interaction_count += 1
            
            # Save if threshold reached
            if await self.should_save_profile():
                await self.save_learned_data()
            
            logger.info(f"📚 Learned from message: {len(message)} chars, {self.interaction_count} interactions")
            
        except Exception as e:
            logger.error(f"❌ Failed to learn from message: {e}")
    
    async def analyze_message_patterns(self, message: str) -> Dict[str, Any]:
        """Extract comprehensive linguistic patterns from message"""
        patterns = {
            "length": len(message),
            "word_count": len(message.split()),
            "sentence_count": len(re.split(r'[.!?]+', message)),
            "exclamation_count": message.count('!'),
            "question_count": message.count('?'),
            "caps_ratio": sum(1 for c in message if c.isupper()) / len(message) if message else 0,
            "emoji_usage": self._extract_emojis(message),
            "common_phrases": self._extract_phrases(message),
            "tone_indicators": self._analyze_tone(message),
            "punctuation_style": self._analyze_punctuation(message),
            "topic_keywords": self._extract_keywords(message),
            "greeting_patterns": self._detect_greetings(message),
            "agreement_patterns": self._detect_agreement(message),
            "excitement_level": self._measure_excitement(message)
        }
        
        return patterns
    
    def _extract_emojis(self, message: str) -> Dict[str, int]:
        """Extract emoji usage patterns"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", 
            flags=re.UNICODE
        )
        
        emojis = emoji_pattern.findall(message)
        return dict(Counter(emojis))
    
    def _extract_phrases(self, message: str) -> Dict[str, int]:
        """Extract common phrases and expressions"""
        # Convert to lowercase for analysis
        lower_message = message.lower()
        
        # Common phrase patterns
        phrases = []
        
        # Multi-word expressions
        common_expressions = [
            r'\blol\b', r'\bhaha\b', r'\blmao\b', r'\bhehe\b',
            r'\bno way\b', r'\bthat\'s wild\b', r'\bno cap\b', r'\bfacts\b',
            r'\bfor sure\b', r'\babsolutely\b', r'\bdefinitely\b',
            r'\bthat\'s fire\b', r'\bthat\'s insane\b', r'\bwow\b',
            r'\byeah\b', r'\bnah\b', r'\bokay\b', r'\balright\b',
            r'\bbtw\b', r'\bomg\b', r'\bwow\b', r'\bcool\b'
        ]
        
        for pattern in common_expressions:
            matches = re.findall(pattern, lower_message)
            if matches:
                phrases.extend(matches)
        
        return dict(Counter(phrases))
    
    def _analyze_tone(self, message: str) -> Dict[str, float]:
        """Analyze emotional tone and mood indicators"""
        lower_message = message.lower()
        
        # Tone indicators
        tones = {
            "excited": len(re.findall(r'[!]{2,}|wow+|amazing|awesome|incredible', lower_message)),
            "casual": len(re.findall(r'\byeah\b|\bokay\b|\bcool\b|\balright\b', lower_message)),
            "questioning": message.count('?'),
            "emphatic": message.count('!'),
            "positive": len(re.findall(r'good|great|nice|love|like|happy|glad', lower_message)),
            "negative": len(re.findall(r'bad|hate|sad|angry|annoying|terrible', lower_message)),
            "technical": len(re.findall(r'api|code|python|javascript|github|programming', lower_message)),
            "humorous": len(re.findall(r'lol|haha|lmao|funny|joke|meme', lower_message))
        }
        
        # Normalize scores
        message_length = len(message.split())
        normalized_tones = {k: v / max(message_length, 1) for k, v in tones.items()}
        
        return normalized_tones
    
    def _analyze_punctuation(self, message: str) -> Dict[str, Any]:
        """Analyze punctuation usage patterns"""
        return {
            "uses_periods": message.count('.') > 0,
            "multiple_exclamations": '!!' in message or '!!!' in message,
            "multiple_questions": '??' in message,
            "ellipsis_usage": '...' in message or '…' in message,
            "comma_frequency": message.count(',') / len(message) if message else 0,
            "quotation_usage": message.count('"') > 0 or message.count("'") > 0
        }
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract topic keywords and interests"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'our', 'their', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b[a-zA-Z]+\b', message.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return list(set(keywords))  # Remove duplicates
    
    def _detect_greetings(self, message: str) -> Optional[str]:
        """Detect greeting patterns"""
        lower_message = message.lower().strip()
        
        greeting_patterns = {
            'casual': r'\b(hey|hi|hello|yo|sup|what\'s up)\b',
            'formal': r'\b(good morning|good afternoon|good evening|greetings)\b',
            'enthusiastic': r'\b(hey there|hi there|hello there)\b'
        }
        
        for style, pattern in greeting_patterns.items():
            if re.search(pattern, lower_message):
                return style
        
        return None
    
    def _detect_agreement(self, message: str) -> Optional[str]:
        """Detect agreement/disagreement patterns"""
        lower_message = message.lower()
        
        if re.search(r'\b(yes|yeah|yep|absolutely|definitely|for sure|exactly|true|facts)\b', lower_message):
            return 'agreement'
        elif re.search(r'\b(no|nah|nope|not really|disagree|wrong)\b', lower_message):
            return 'disagreement'
        
        return None
    
    def _measure_excitement(self, message: str) -> float:
        """Measure excitement level in message"""
        excitement_score = 0
        
        # Multiple exclamation marks
        excitement_score += message.count('!') * 0.3
        
        # ALL CAPS words
        caps_words = len(re.findall(r'\b[A-Z]{2,}\b', message))
        excitement_score += caps_words * 0.5
        
        # Excitement keywords
        excitement_words = len(re.findall(r'\b(wow|amazing|awesome|incredible|fantastic|omg|yooo|no way)\b', message.lower()))
        excitement_score += excitement_words * 0.4
        
        # Repeated letters (woooow, yessss)
        repeated_letters = len(re.findall(r'(\w)\1{2,}', message.lower()))
        excitement_score += repeated_letters * 0.2
        
        return min(excitement_score, 2.0)  # Cap at 2.0
    
    async def update_profile_with_patterns(self, patterns: Dict[str, Any]):
        """Update personality profile with newly learned patterns"""
        try:
            # Update phrase frequencies with weighted averaging
            for phrase, count in patterns.get('common_phrases', {}).items():
                current_count = self.current_profile['communication_style']['common_phrases'].get(phrase, 0)
                # Use exponential smoothing
                new_count = current_count * 0.8 + count * 0.2
                self.current_profile['communication_style']['common_phrases'][phrase] = new_count
            
            # Update emoji usage
            for emoji, count in patterns.get('emoji_usage', {}).items():
                current_count = self.current_profile['communication_style']['emoji_usage'].get(emoji, 0)
                new_count = current_count * 0.8 + count * 0.2
                self.current_profile['communication_style']['emoji_usage'][emoji] = new_count
            
            # Update tone patterns
            tone_indicators = patterns.get('tone_indicators', {})
            for tone, score in tone_indicators.items():
                if score > 0.1:  # Only update significant tone indicators
                    current_mood = self.current_profile['conversation_context']['mood_patterns'].get(tone, "neutral")
                    # Update based on observed patterns
                    if score > 0.5:
                        if patterns.get('caps_ratio', 0) > 0.3:
                            self.current_profile['conversation_context']['mood_patterns'][tone] = "emphatic_caps"
                        elif patterns.get('exclamation_count', 0) > 2:
                            self.current_profile['conversation_context']['mood_patterns'][tone] = "enthusiastic_exclamations"
                        else:
                            self.current_profile['conversation_context']['mood_patterns'][tone] = "expressive"
            
            # Update communication style preferences
            if patterns.get('length', 0) > 0:
                avg_length = patterns['length']
                if avg_length < 50:
                    length_pref = "short"
                elif avg_length < 150:
                    length_pref = "medium"
                else:
                    length_pref = "long"
                
                self.current_profile['communication_style']['response_length_preference'] = length_pref
            
            # Update caps usage frequency
            if 'caps_ratio' in patterns:
                current_caps = self.current_profile['communication_style']['caps_usage_frequency']
                new_caps = current_caps * 0.9 + patterns['caps_ratio'] * 0.1
                self.current_profile['communication_style']['caps_usage_frequency'] = new_caps
            
            # Update greeting style if detected
            greeting_style = patterns.get('greeting_patterns')
            if greeting_style:
                self.current_profile['learned_patterns']['greeting_style'] = greeting_style
            
            # Update topic interests
            keywords = patterns.get('topic_keywords', [])
            if keywords:
                current_topics = self.current_profile['conversation_context']['favorite_topics']
                # Add new keywords to topics list (limit to 50 topics)
                updated_topics = list(set(current_topics + keywords))[:50]
                self.current_profile['conversation_context']['favorite_topics'] = updated_topics
            
            # Update learning metadata
            metadata = self.current_profile['learning_metadata']
            metadata['total_messages_analyzed'] += 1
            metadata['last_learning_session'] = datetime.utcnow().isoformat() + 'Z'
            
            # Update confidence score based on data volume
            message_count = metadata['total_messages_analyzed']
            if message_count < 10:
                metadata['confidence_score'] = 0.2
                metadata['pattern_reliability'] = "low"
            elif message_count < 50:
                metadata['confidence_score'] = 0.5
                metadata['pattern_reliability'] = "medium"
            elif message_count < 200:
                metadata['confidence_score'] = 0.8
                metadata['pattern_reliability'] = "high"
            else:
                metadata['confidence_score'] = 0.95
                metadata['pattern_reliability'] = "very_high"
            
        except Exception as e:
            logger.error(f"❌ Failed to update profile with patterns: {e}")
    
    async def should_save_profile(self) -> bool:
        """Determine when to commit learned changes"""
        # Save every N interactions
        if self.interaction_count % self.save_threshold == 0:
            return True
        
        # Save on significant pattern changes
        metadata = self.current_profile.get('learning_metadata', {})
        confidence_score = metadata.get('confidence_score', 0)
        
        # Save when confidence crosses thresholds
        if confidence_score in [0.2, 0.5, 0.8, 0.95]:
            return True
        
        # Save if buffer is getting large
        if len(self.conversation_buffer) > 50:
            return True
        
        return False
    
    async def save_learned_data(self):
        """Save all learned data to repository"""
        try:
            # Save updated profile
            self.profile_manager.save_profile(self.current_profile)
            
            # Save conversation memory
            self.profile_manager.save_conversation_memory(self.conversation_buffer)
            
            # Clear buffer after saving
            self.conversation_buffer = []
            
            logger.info(f"💾 Saved learned data after {self.interaction_count} interactions")
            
        except Exception as e:
            logger.error(f"❌ Failed to save learned data: {e}")
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of current learning progress"""
        metadata = self.current_profile.get('learning_metadata', {})
        
        return {
            "total_interactions": self.interaction_count,
            "messages_analyzed": metadata.get('total_messages_analyzed', 0),
            "confidence_score": metadata.get('confidence_score', 0),
            "reliability": metadata.get('pattern_reliability', 'unknown'),
            "phrases_learned": len(self.current_profile.get('communication_style', {}).get('common_phrases', {})),
            "emojis_learned": len(self.current_profile.get('communication_style', {}).get('emoji_usage', {})),
            "topics_discovered": len(self.current_profile.get('conversation_context', {}).get('favorite_topics', [])),
            "buffer_size": len(self.conversation_buffer)
        }