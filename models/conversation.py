"""
Conversation models for the Lynxx Anthropic Console.

This module defines the database models for conversations and messages.
"""

from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import db


class Conversation(db.Model):
    """
    Model representing a conversation with an Anthropic model.
    """
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    model = Column(String(100), nullable=False)  # Store which Anthropic model was used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Define relationship to messages
    messages = relationship("Message", back_populates="conversation", 
                            cascade="all, delete-orphan", lazy="dynamic")
    
    def __init__(self, user_id, title, model):
        self.user_id = user_id
        self.title = title
        self.model = model
    
    def to_dict(self):
        """Convert conversation to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'model': self.model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'message_count': self.messages.count()
        }


class Message(db.Model):
    """
    Model representing a message in a conversation.
    """
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column(Text)  # Optional JSON metadata - renamed from 'metadata' to avoid conflict
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Define relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __init__(self, conversation_id, role, content, metadata=None):
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.message_metadata = json.dumps(metadata) if metadata else None
    
    def to_dict(self):
        """Convert message to dictionary representation."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'metadata': json.loads(self.message_metadata) if self.message_metadata else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
