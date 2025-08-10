"""
Database Manager for WhatsApp AI Bot
Handles all database operations and integrations
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models import init_database, get_db
from database.chat_style_analyzer import ChatStyleAnalyzer

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the WhatsApp bot"""
    
    def __init__(self, your_user_id: str):
        self.your_user_id = your_user_id
        self.style_analyzer = ChatStyleAnalyzer(your_user_id)
        
        # Initialize database
        if not init_database():
            logger.error("❌ Failed to initialize database")
            raise Exception("Database initialization failed")
        
        logger.info(f"🗄️ Database manager initialized for user: {your_user_id}")
    
    async def process_message(self, message: str, sender_id: str, bot_response: str = None, 
                            sentiment_data: Dict = None) -> Dict[str, Any]:
        """Process and store a message with style learning"""
        try:
            # Analyze and store the message
            analysis = self.style_analyzer.analyze_message(
                message=message,
                sender_id=sender_id,
                bot_response=bot_response,
                sentiment_data=sentiment_data
            )
            
            logger.info(f"📊 Message analyzed for {sender_id}: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return {"error": str(e)}
    
    async def suggest_response(self, other_user_id: str, their_message: str, 
                             conversation_context: List[str] = None) -> Dict[str, Any]:
        """Get AI-generated response suggestion based on your style"""
        try:
            suggestion = self.style_analyzer.suggest_response(
                other_user_id=other_user_id,
                their_message=their_message,
                conversation_context=conversation_context
            )
            
            if suggestion.get("suggestion"):
                logger.info(f"💡 Response suggested for {other_user_id}: {suggestion['confidence']:.2f} confidence")
            
            return suggestion
            
        except Exception as e:
            logger.error(f"❌ Error generating response suggestion: {e}")
            return {"suggestion": None, "reason": f"Error: {e}"}
    
    def get_style_summary(self) -> Dict[str, Any]:
        """Get your communication style summary"""
        try:
            summary = self.style_analyzer.get_style_summary()
            logger.info(f"📋 Style summary retrieved for {self.your_user_id}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting style summary: {e}")
            return {"error": str(e)}
    
    def get_user_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user"""
        db = get_db()
        try:
            from database.models import Conversation
            
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.timestamp.desc()).limit(limit).all()
            
            history = []
            for conv in conversations:
                history.append({
                    "user_message": conv.user_message,
                    "bot_response": conv.bot_response,
                    "timestamp": conv.timestamp.isoformat(),
                    "sentiment": conv.sentiment_label,
                    "topics": conv.topics
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error getting conversation history: {e}")
            return []
        finally:
            db.close()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics and patterns"""
        db = get_db()
        try:
            from database.models import UserProfile, CommonPhrase, EmojiUsage, Conversation
            
            # Get user profile
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return {"error": "User not found"}
            
            # Get top phrases
            top_phrases = db.query(CommonPhrase).filter(
                CommonPhrase.user_id == user_id
            ).order_by(CommonPhrase.usage_count.desc()).limit(5).all()
            
            # Get top emojis
            top_emojis = db.query(EmojiUsage).filter(
                EmojiUsage.user_id == user_id
            ).order_by(EmojiUsage.usage_count.desc()).limit(5).all()
            
            # Get recent sentiment distribution
            recent_conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.timestamp.desc()).limit(50).all()
            
            sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
            for conv in recent_conversations:
                sentiment_counts[conv.sentiment_label] = sentiment_counts.get(conv.sentiment_label, 0) + 1
            
            return {
                "user_id": user_id,
                "total_messages": profile.total_messages,
                "learning_confidence": profile.learning_confidence,
                "last_interaction": profile.last_interaction.isoformat() if profile.last_interaction else None,
                "communication_style": profile.communication_style,
                "personality_traits": profile.personality_traits,
                "top_phrases": [(phrase.phrase, phrase.usage_count) for phrase in top_phrases],
                "top_emojis": [(emoji.emoji, emoji.usage_count) for emoji in top_emojis],
                "sentiment_distribution": sentiment_counts,
                "recent_topics": self._get_recent_topics(recent_conversations)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def _get_recent_topics(self, conversations: List) -> List[str]:
        """Extract recent topics from conversations"""
        topic_counts = {}
        for conv in conversations:
            for topic in conv.topics or []:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Return top 5 topics
        return [topic for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old conversation data to maintain performance"""
        db = get_db()
        try:
            from datetime import timedelta, timezone
            from database.models import Conversation, ResponseSuggestion
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            # Delete old conversations (keep recent ones for learning)
            old_conversations = db.query(Conversation).filter(
                Conversation.timestamp < cutoff_date
            ).count()
            
            if old_conversations > 0:
                db.query(Conversation).filter(
                    Conversation.timestamp < cutoff_date
                ).delete()
                
                logger.info(f"🧹 Cleaned up {old_conversations} old conversations")
            
            # Delete old response suggestions
            old_suggestions = db.query(ResponseSuggestion).filter(
                ResponseSuggestion.created_at < cutoff_date
            ).count()
            
            if old_suggestions > 0:
                db.query(ResponseSuggestion).filter(
                    ResponseSuggestion.created_at < cutoff_date
                ).delete()
                
                logger.info(f"🧹 Cleaned up {old_suggestions} old response suggestions")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            db.rollback()
        finally:
            db.close()
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export your learned chat style data for backup"""
        try:
            style_summary = self.get_style_summary()
            user_stats = self.get_user_stats(self.your_user_id)
            
            return {
                "your_user_id": self.your_user_id,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "style_summary": style_summary,
                "user_stats": user_stats,
                "conversation_history": self.get_user_conversation_history(self.your_user_id, limit=100)
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting learning data: {e}")
            return {"error": str(e)}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        db = get_db()
        try:
            from database.models import UserProfile, Conversation, CommonPhrase, EmojiUsage, ChatStyleLearning, ResponseSuggestion
            
            stats = {
                "total_users": db.query(UserProfile).count(),
                "total_conversations": db.query(Conversation).count(),
                "total_phrases": db.query(CommonPhrase).count(),
                "total_emojis": db.query(EmojiUsage).count(),
                "users_with_style_learning": db.query(ChatStyleLearning).count(),
                "total_response_suggestions": db.query(ResponseSuggestion).count(),
            }
            
            # Get most active users
            active_users = db.query(UserProfile).order_by(UserProfile.total_messages.desc()).limit(5).all()
            stats["most_active_users"] = [
                {"user_id": user.user_id, "messages": user.total_messages} 
                for user in active_users
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()