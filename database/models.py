"""
Database models for WhatsApp AI Bot
Stores chat patterns, personality data, and conversation history
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, JSON, DateTime, 
    Float, Boolean, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserProfile(Base):
    """Store user personality and communication patterns"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    
    # Communication style patterns
    communication_style = Column(JSON, default=dict)
    personality_traits = Column(JSON, default=dict)
    learned_patterns = Column(JSON, default=dict)
    
    # Statistics
    total_messages = Column(Integer, default=0)
    learning_confidence = Column(Float, default=0.0)
    last_interaction = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    phrases = relationship("CommonPhrase", back_populates="user", cascade="all, delete-orphan")
    emojis = relationship("EmojiUsage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', messages={self.total_messages})>"

class Conversation(Base):
    """Store conversation history and context"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), ForeignKey("user_profiles.user_id"), nullable=False)
    
    # Message data
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text)
    message_type = Column(String(50), default="text")  # text, voice, image, etc.
    
    # Context and analysis
    detected_language = Column(String(10), default="en")
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    topics = Column(JSON, default=list)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    response_time_ms = Column(Integer)
    search_used = Column(Boolean, default=False)
    ai_model_used = Column(String(100))
    
    # Relationships
    user = relationship("UserProfile", back_populates="conversations")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_conversations_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_conversations_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Conversation(user_id='{self.user_id}', timestamp='{self.timestamp}')>"

class CommonPhrase(Base):
    """Track commonly used phrases by users"""
    __tablename__ = "common_phrases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), ForeignKey("user_profiles.user_id"), nullable=False)
    
    phrase = Column(String(500), nullable=False)
    usage_count = Column(Integer, default=1)
    phrase_type = Column(String(50))  # greeting, question, exclamation, etc.
    context = Column(String(100))  # when it's typically used
    
    # Metadata
    first_seen = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    last_used = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("UserProfile", back_populates="phrases")
    
    # Indexes
    __table_args__ = (
        Index('idx_phrases_user_count', 'user_id', 'usage_count'),
        Index('idx_phrases_phrase', 'phrase'),
    )
    
    def __repr__(self):
        return f"<CommonPhrase(phrase='{self.phrase[:30]}...', count={self.usage_count})>"

class EmojiUsage(Base):
    """Track emoji usage patterns"""
    __tablename__ = "emoji_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), ForeignKey("user_profiles.user_id"), nullable=False)
    
    emoji = Column(String(10), nullable=False)
    usage_count = Column(Integer, default=1)
    context = Column(String(100))  # happy, sad, greeting, etc.
    
    # Metadata
    first_seen = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    last_used = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("UserProfile", back_populates="emojis")
    
    # Indexes
    __table_args__ = (
        Index('idx_emoji_user_count', 'user_id', 'usage_count'),
        Index('idx_emoji_emoji', 'emoji'),
    )
    
    def __repr__(self):
        return f"<EmojiUsage(emoji='{self.emoji}', count={self.usage_count})>"

class ChatStyleLearning(Base):
    """Store learned chat styles for responding to other users"""
    __tablename__ = "chat_style_learning"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)  # Your user ID
    
    # Style analysis
    response_patterns = Column(JSON, default=dict)  # How you typically respond
    tone_preferences = Column(JSON, default=dict)  # Formal, casual, humorous, etc.
    topic_expertise = Column(JSON, default=dict)  # Topics you're knowledgeable about
    conversation_starters = Column(JSON, default=list)  # How you start conversations
    
    # Response templates based on your style
    greeting_templates = Column(JSON, default=list)
    question_response_templates = Column(JSON, default=list)
    supportive_response_templates = Column(JSON, default=list)
    humor_templates = Column(JSON, default=list)
    
    # Contextual adaptations
    formal_style_indicators = Column(JSON, default=list)
    casual_style_indicators = Column(JSON, default=list)
    technical_response_patterns = Column(JSON, default=list)
    
    # Learning metadata
    confidence_score = Column(Float, default=0.0)
    total_interactions_analyzed = Column(Integer, default=0)
    last_learning_update = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<ChatStyleLearning(user_id='{self.user_id}', confidence={self.confidence_score})>"

class ResponseSuggestion(Base):
    """Store AI-generated response suggestions based on your style"""
    __tablename__ = "response_suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Context
    other_user_id = Column(String(100), nullable=False)  # User you're responding to
    other_user_message = Column(Text, nullable=False)
    conversation_context = Column(JSON, default=dict)
    
    # Suggestions based on your style
    suggested_response = Column(Text, nullable=False)
    response_tone = Column(String(50))  # casual, formal, humorous, supportive
    confidence_score = Column(Float, default=0.0)
    reasoning = Column(Text)  # Why this response was suggested
    
    # User feedback
    was_used = Column(Boolean, default=False)
    user_modified = Column(Boolean, default=False)
    actual_response = Column(Text)  # What you actually sent
    feedback_score = Column(Integer)  # 1-5 rating if provided
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_suggestions_other_user', 'other_user_id'),
        Index('idx_suggestions_timestamp', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ResponseSuggestion(other_user='{self.other_user_id}', confidence={self.confidence_score})>"

# Database utility functions
def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def init_database():
    """Initialize database tables"""
    try:
        logger.info("🗄️ Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False

def get_user_profile(db: Session, user_id: str) -> Optional[UserProfile]:
    """Get or create user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_user_stats(db: Session, user_id: str, increment_messages: bool = True):
    """Update user statistics"""
    profile = get_user_profile(db, user_id)
    if increment_messages:
        profile.total_messages += 1
    profile.last_interaction = datetime.now(timezone.utc)
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()