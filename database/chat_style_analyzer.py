"""
Advanced Chat Style Analyzer
Analyzes your messaging patterns to help generate better responses to other users
"""

import logging
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from database.models import (
    get_db, UserProfile, Conversation, CommonPhrase, EmojiUsage, 
    ChatStyleLearning, ResponseSuggestion, get_user_profile, update_user_stats
)

logger = logging.getLogger(__name__)

class ChatStyleAnalyzer:
    """Analyzes chat patterns to learn your communication style"""
    
    def __init__(self, your_user_id: str):
        self.your_user_id = your_user_id
        
    def analyze_message(self, message: str, sender_id: str, bot_response: str = None, 
                       message_type: str = "text", sentiment_data: Dict = None) -> Dict[str, Any]:
        """Analyze a message and update learning patterns"""
        
        db = get_db()
        if db is None:
            logger.warning("⚠️ Database not available, skipping message analysis")
            return {"error": "Database not available"}
            
        try:
            # Store conversation
            conversation = Conversation(
                user_id=sender_id,
                user_message=message,
                bot_response=bot_response,
                message_type=message_type,
                detected_language=self._detect_language(message),
                sentiment_score=sentiment_data.get('score', 0.0) if sentiment_data else 0.0,
                sentiment_label=sentiment_data.get('label', 'NEUTRAL') if sentiment_data else 'NEUTRAL',
                topics=self._extract_topics(message),
                timestamp=datetime.now(timezone.utc)
            )
            db.add(conversation)
            
            # Update user profile and stats
            update_user_stats(db, sender_id)
            
            # If this is your message, learn from your style
            if sender_id == self.your_user_id:
                self._learn_from_your_message(db, message, sentiment_data)
            
            # Extract phrases and emojis
            self._extract_phrases(db, sender_id, message)
            self._extract_emojis(db, sender_id, message)
            
            db.commit()
            
            analysis = {
                "language": conversation.detected_language,
                "sentiment": conversation.sentiment_label,
                "topics": conversation.topics,
                "phrases_found": self._count_phrases_in_message(message),
                "emojis_found": self._count_emojis_in_message(message)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing message: {e}")
            if db:
                db.rollback()
            return {"error": str(e)}
        finally:
            if db:
                db.close()
    
    def _learn_from_your_message(self, db: Session, message: str, sentiment_data: Dict = None):
        """Learn patterns from your messages to improve responses to others"""
        
        # Get or create your chat style learning record
        style_learning = db.query(ChatStyleLearning).filter(
            ChatStyleLearning.user_id == self.your_user_id
        ).first()
        
        if not style_learning:
            style_learning = ChatStyleLearning(user_id=self.your_user_id)
            db.add(style_learning)
        
        # Analyze response patterns
        response_patterns = style_learning.response_patterns or {}
        
        # Length preference
        message_length = len(message)
        length_category = "short" if message_length < 50 else "medium" if message_length < 150 else "long"
        response_patterns["length_preference"] = response_patterns.get("length_preference", {})
        response_patterns["length_preference"][length_category] = response_patterns["length_preference"].get(length_category, 0) + 1
        
        # Punctuation style
        punctuation_score = self._analyze_punctuation(message)
        response_patterns["punctuation_style"] = punctuation_score
        
        # Formality level
        formality_score = self._analyze_formality(message)
        response_patterns["formality_level"] = formality_score
        
        # Question asking tendency
        has_questions = "?" in message
        response_patterns["asks_questions"] = response_patterns.get("asks_questions", 0) + (1 if has_questions else 0)
        response_patterns["total_messages"] = response_patterns.get("total_messages", 0) + 1
        
        # Update tone preferences
        tone_preferences = style_learning.tone_preferences or {}
        if sentiment_data:
            sentiment_label = sentiment_data.get('label', 'NEUTRAL').lower()
            tone_preferences[sentiment_label] = tone_preferences.get(sentiment_label, 0) + 1
        
        # Extract conversation starters if this might be a conversation starter
        if self._is_conversation_starter(message):
            starters = style_learning.conversation_starters or []
            if message not in starters and len(starters) < 20:
                starters.append(message)
                style_learning.conversation_starters = starters
        
        # Update response templates based on message type
        self._update_response_templates(style_learning, message)
        
        # Calculate confidence score
        total_messages = response_patterns.get("total_messages", 0)
        style_learning.confidence_score = min(total_messages / 100.0, 1.0)  # Max confidence at 100 messages
        
        # Update fields
        style_learning.response_patterns = response_patterns
        style_learning.tone_preferences = tone_preferences
        style_learning.total_interactions_analyzed = total_messages
        style_learning.last_learning_update = datetime.now(timezone.utc)
        style_learning.updated_at = datetime.now(timezone.utc)
    
    def _update_response_templates(self, style_learning: ChatStyleLearning, message: str):
        """Update response templates based on message types"""
        message_lower = message.lower()
        
        # Greeting templates
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good evening"]):
            greetings = style_learning.greeting_templates or []
            if message not in greetings and len(greetings) < 10:
                greetings.append(message)
                style_learning.greeting_templates = greetings
        
        # Question response templates
        if "?" in message and any(word in message_lower for word in ["how", "what", "why", "when", "where"]):
            questions = style_learning.question_response_templates or []
            if message not in questions and len(questions) < 10:
                questions.append(message)
                style_learning.question_response_templates = questions
        
        # Supportive response templates
        if any(word in message_lower for word in ["thanks", "thank you", "great", "awesome", "good job", "well done"]):
            supportive = style_learning.supportive_response_templates or []
            if message not in supportive and len(supportive) < 10:
                supportive.append(message)
                style_learning.supportive_response_templates = supportive
        
        # Humor templates
        if any(indicator in message_lower for indicator in ["😂", "😄", "😆", "lol", "haha", "funny"]):
            humor = style_learning.humor_templates or []
            if message not in humor and len(humor) < 10:
                humor.append(message)
                style_learning.humor_templates = humor
    
    def suggest_response(self, other_user_id: str, their_message: str, 
                        conversation_context: List[str] = None) -> Dict[str, Any]:
        """Generate response suggestions based on your learned style"""
        
        db = get_db()
        try:
            # Get your style learning data
            style_learning = db.query(ChatStyleLearning).filter(
                ChatStyleLearning.user_id == self.your_user_id
            ).first()
            
            if not style_learning or style_learning.confidence_score < 0.1:
                return {"suggestion": None, "reason": "Not enough style data learned yet"}
            
            # Analyze their message
            message_analysis = self._analyze_incoming_message(their_message)
            
            # Generate response based on your style
            suggestion = self._generate_styled_response(style_learning, message_analysis, conversation_context)
            
            # Store the suggestion
            response_suggestion = ResponseSuggestion(
                other_user_id=other_user_id,
                other_user_message=their_message,
                conversation_context={"context": conversation_context or [], "analysis": message_analysis},
                suggested_response=suggestion["text"],
                response_tone=suggestion["tone"],
                confidence_score=suggestion["confidence"],
                reasoning=suggestion["reasoning"]
            )
            db.add(response_suggestion)
            db.commit()
            
            return {
                "suggestion": suggestion["text"],
                "tone": suggestion["tone"],
                "confidence": suggestion["confidence"],
                "reasoning": suggestion["reasoning"],
                "suggestion_id": str(response_suggestion.id)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating response suggestion: {e}")
            return {"suggestion": None, "reason": f"Error: {e}"}
        finally:
            db.close()
    
    def _generate_styled_response(self, style_learning: ChatStyleLearning, 
                                 message_analysis: Dict, context: List[str] = None) -> Dict[str, Any]:
        """Generate a response that matches your communication style"""
        
        response_patterns = style_learning.response_patterns or {}
        tone_preferences = style_learning.tone_preferences or {}
        
        # Determine response tone based on your preferences
        preferred_tone = max(tone_preferences.items(), key=lambda x: x[1])[0] if tone_preferences else "neutral"
        
        # Determine response length based on your patterns
        length_prefs = response_patterns.get("length_preference", {})
        preferred_length = max(length_prefs.items(), key=lambda x: x[1])[0] if length_prefs else "medium"
        
        # Select appropriate template
        message_type = message_analysis["type"]
        suggestion_text = ""
        reasoning = ""
        
        if message_type == "greeting":
            templates = style_learning.greeting_templates or []
            if templates:
                suggestion_text = self._adapt_template(templates[0], message_analysis)
                reasoning = "Based on your typical greeting style"
        
        elif message_type == "question":
            templates = style_learning.question_response_templates or []
            if templates:
                suggestion_text = self._adapt_template(templates[0], message_analysis)
                reasoning = "Based on how you typically answer questions"
        
        elif message_type == "supportive_needed":
            templates = style_learning.supportive_response_templates or []
            if templates:
                suggestion_text = self._adapt_template(templates[0], message_analysis)
                reasoning = "Based on your supportive communication style"
        
        else:
            # Generate general response based on your patterns
            formality = response_patterns.get("formality_level", 0.5)
            if formality > 0.7:
                suggestion_text = self._generate_formal_response(message_analysis)
                reasoning = "Based on your formal communication style"
            else:
                suggestion_text = self._generate_casual_response(message_analysis)
                reasoning = "Based on your casual communication style"
        
        # Apply length preference
        suggestion_text = self._adjust_response_length(suggestion_text, preferred_length)
        
        # Calculate confidence based on available data
        confidence = min(style_learning.confidence_score + 0.2, 1.0)
        
        return {
            "text": suggestion_text or "I'd respond in a way that matches your style, but need more examples to learn from.",
            "tone": preferred_tone,
            "confidence": confidence,
            "reasoning": reasoning or "Based on general style patterns"
        }
    
    def _analyze_incoming_message(self, message: str) -> Dict[str, Any]:
        """Analyze the incoming message to determine appropriate response type"""
        message_lower = message.lower()
        
        # Determine message type
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning"]):
            msg_type = "greeting"
        elif "?" in message:
            msg_type = "question"
        elif any(word in message_lower for word in ["help", "problem", "issue", "trouble", "sad", "worried"]):
            msg_type = "supportive_needed"
        elif any(word in message_lower for word in ["thanks", "thank you", "appreciate"]):
            msg_type = "appreciation"
        else:
            msg_type = "general"
        
        return {
            "type": msg_type,
            "sentiment": self._quick_sentiment_analysis(message),
            "length": len(message),
            "has_emoji": bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message)),
            "formality": self._analyze_formality(message)
        }
    
    def get_style_summary(self) -> Dict[str, Any]:
        """Get a summary of your learned communication style"""
        
        db = get_db()
        try:
            style_learning = db.query(ChatStyleLearning).filter(
                ChatStyleLearning.user_id == self.your_user_id
            ).first()
            
            if not style_learning:
                return {"summary": "No style data available yet. Chat more to build your style profile!"}
            
            response_patterns = style_learning.response_patterns or {}
            tone_preferences = style_learning.tone_preferences or {}
            
            # Get top phrases and emojis
            user_profile = get_user_profile(db, self.your_user_id)
            top_phrases = db.query(CommonPhrase).filter(
                CommonPhrase.user_id == self.your_user_id
            ).order_by(CommonPhrase.usage_count.desc()).limit(5).all()
            
            top_emojis = db.query(EmojiUsage).filter(
                EmojiUsage.user_id == self.your_user_id
            ).order_by(EmojiUsage.usage_count.desc()).limit(5).all()
            
            return {
                "confidence_score": style_learning.confidence_score,
                "total_messages_analyzed": style_learning.total_interactions_analyzed,
                "preferred_tone": max(tone_preferences.items(), key=lambda x: x[1])[0] if tone_preferences else "neutral",
                "response_length_preference": self._get_preferred_length(response_patterns),
                "formality_level": response_patterns.get("formality_level", 0.5),
                "asks_questions_frequency": self._calculate_question_frequency(response_patterns),
                "top_phrases": [phrase.phrase for phrase in top_phrases],
                "top_emojis": [emoji.emoji for emoji in top_emojis],
                "greeting_templates_count": len(style_learning.greeting_templates or []),
                "response_templates_count": len(style_learning.question_response_templates or []),
                "last_updated": style_learning.last_learning_update.isoformat() if style_learning.last_learning_update else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting style summary: {e}")
            return {"error": f"Failed to get style summary: {e}"}
        finally:
            db.close()
    
    # Helper methods
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # This would use langdetect in production
        return "en"  # Default to English for now
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        # Simple keyword extraction
        keywords = []
        text_lower = text.lower()
        
        topic_keywords = {
            "technology": ["tech", "computer", "software", "app", "website", "code", "programming"],
            "work": ["work", "job", "office", "meeting", "project", "business", "career"],
            "personal": ["family", "friend", "home", "life", "personal", "feeling"],
            "entertainment": ["movie", "music", "game", "fun", "entertainment", "hobby"],
            "news": ["news", "politics", "world", "country", "government", "economy"]
        }
        
        for topic, words in topic_keywords.items():
            if any(word in text_lower for word in words):
                keywords.append(topic)
        
        return keywords[:3]  # Limit to top 3 topics
    
    def _extract_phrases(self, db: Session, user_id: str, message: str):
        """Extract and store common phrases"""
        # Split into potential phrases (2-5 words)
        words = message.lower().split()
        for i in range(len(words) - 1):
            for j in range(i + 2, min(i + 6, len(words) + 1)):
                phrase = " ".join(words[i:j])
                if len(phrase) > 10:  # Only meaningful phrases
                    
                    # Check if phrase exists
                    existing = db.query(CommonPhrase).filter(
                        CommonPhrase.user_id == user_id,
                        CommonPhrase.phrase == phrase
                    ).first()
                    
                    if existing:
                        existing.usage_count += 1
                        existing.last_used = datetime.now(timezone.utc)
                    else:
                        new_phrase = CommonPhrase(
                            user_id=user_id,
                            phrase=phrase,
                            phrase_type=self._classify_phrase_type(phrase)
                        )
                        db.add(new_phrase)
    
    def _extract_emojis(self, db: Session, user_id: str, message: str):
        """Extract and store emoji usage"""
        emojis = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message)
        
        for emoji in emojis:
            existing = db.query(EmojiUsage).filter(
                EmojiUsage.user_id == user_id,
                EmojiUsage.emoji == emoji
            ).first()
            
            if existing:
                existing.usage_count += 1
                existing.last_used = datetime.now(timezone.utc)
            else:
                new_emoji = EmojiUsage(
                    user_id=user_id,
                    emoji=emoji,
                    context=self._classify_emoji_context(emoji)
                )
                db.add(new_emoji)
    
    def _analyze_punctuation(self, text: str) -> float:
        """Analyze punctuation usage (0=minimal, 1=heavy)"""
        punctuation_count = len(re.findall(r'[!?.,:;]', text))
        return min(punctuation_count / max(len(text.split()), 1), 1.0)
    
    def _analyze_formality(self, text: str) -> float:
        """Analyze formality level (0=very casual, 1=very formal)"""
        formal_indicators = ["please", "thank you", "would", "could", "kindly", "sincerely"]
        casual_indicators = ["lol", "haha", "yeah", "nah", "gonna", "wanna", "btw"]
        
        formal_count = sum(1 for word in formal_indicators if word in text.lower())
        casual_count = sum(1 for word in casual_indicators if word in text.lower())
        
        if formal_count + casual_count == 0:
            return 0.5  # Neutral
        
        return formal_count / (formal_count + casual_count)
    
    def _is_conversation_starter(self, message: str) -> bool:
        """Check if message is likely a conversation starter"""
        starters = ["hello", "hi", "hey", "good morning", "how are you", "what's up", "hope you're"]
        return any(starter in message.lower() for starter in starters)
    
    def _classify_phrase_type(self, phrase: str) -> str:
        """Classify the type of phrase"""
        if any(word in phrase for word in ["hello", "hi", "good morning"]):
            return "greeting"
        elif "?" in phrase:
            return "question"
        elif any(word in phrase for word in ["thanks", "thank you"]):
            return "appreciation"
        else:
            return "statement"
    
    def _classify_emoji_context(self, emoji: str) -> str:
        """Classify emoji context"""
        happy_emojis = ["😀", "😃", "😄", "😁", "😊", "😍", "🥰", "😘"]
        sad_emojis = ["😢", "😭", "😔", "😞", "😟", "😕"]
        
        if emoji in happy_emojis:
            return "happy"
        elif emoji in sad_emojis:
            return "sad"
        else:
            return "neutral"
    
    def _count_phrases_in_message(self, message: str) -> int:
        """Count number of phrases found in message"""
        return len(message.split())  # Simplified for now
    
    def _count_emojis_in_message(self, message: str) -> int:
        """Count emojis in message"""
        return len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message))
    
    def _quick_sentiment_analysis(self, text: str) -> str:
        """Quick sentiment analysis"""
        positive = ["good", "great", "awesome", "happy", "love", "excellent"]
        negative = ["bad", "terrible", "sad", "hate", "awful", "horrible"]
        
        pos_count = sum(1 for word in positive if word in text.lower())
        neg_count = sum(1 for word in negative if word in text.lower())
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def _adapt_template(self, template: str, analysis: Dict) -> str:
        """Adapt a template to current context"""
        # Simple template adaptation
        return template  # For now, return as-is
    
    def _generate_formal_response(self, analysis: Dict) -> str:
        """Generate formal response"""
        if analysis["type"] == "question":
            return "Thank you for your question. Let me provide you with a thoughtful response."
        else:
            return "I appreciate your message and would like to respond appropriately."
    
    def _generate_casual_response(self, analysis: Dict) -> str:
        """Generate casual response"""
        if analysis["type"] == "question":
            return "Good question! Here's what I think..."
        else:
            return "Thanks for reaching out! I'd love to chat about this."
    
    def _adjust_response_length(self, response: str, preferred_length: str) -> str:
        """Adjust response length to match preference"""
        if preferred_length == "short" and len(response) > 50:
            return response[:50] + "..."
        elif preferred_length == "long" and len(response) < 100:
            return response + " I'd be happy to discuss this further."
        return response
    
    def _get_preferred_length(self, patterns: Dict) -> str:
        """Get preferred response length"""
        length_prefs = patterns.get("length_preference", {})
        if not length_prefs:
            return "medium"
        return max(length_prefs.items(), key=lambda x: x[1])[0]
    
    def _calculate_question_frequency(self, patterns: Dict) -> float:
        """Calculate how often you ask questions"""
        asks_questions = patterns.get("asks_questions", 0)
        total_messages = patterns.get("total_messages", 1)
        return asks_questions / total_messages