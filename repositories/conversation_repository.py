"""
Conversation repository for the Lynxx Anthropic Console.

This module provides CRUD operations for conversations and messages.
"""

from typing import List, Dict, Optional, Any, Union
from sqlalchemy.exc import SQLAlchemyError
from models.conversation import Conversation, Message
from database import db


class ConversationRepository:
    """
    Repository for managing conversations and messages.
    """
    
    @staticmethod
    def save_conversation(user_id: str, conversation_data: Dict[str, Any]) -> Optional[Conversation]:
        """
        Save a new conversation to the database.
        
        Args:
            user_id: ID of the user who owns the conversation
            conversation_data: Dictionary containing conversation data
            
        Returns:
            Saved Conversation object or None if an error occurred
        """
        try:
            title = conversation_data.get('title', 'New Conversation')
            model = conversation_data.get('model', 'claude-3-opus-20240229')
            
            conversation = Conversation(user_id=user_id, title=title, model=model)
            db.session.add(conversation)
            db.session.commit()
            return conversation
        except SQLAlchemyError:
            db.session.rollback()
            return None
    
    @staticmethod
    def get_conversations(user_id: str, active_only: bool = True) -> List[Conversation]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: ID of the user
            active_only: If True, returns only active conversations
            
        Returns:
            List of Conversation objects
        """
        query = Conversation.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Conversation.updated_at.desc()).all()
    
    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[Conversation]:
        """
        Get a specific conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation object or None if not found
        """
        return Conversation.query.get(conversation_id)
    
    @staticmethod
    def update_conversation(conversation_id: int, 
                            conversation_data: Dict[str, Any]) -> Optional[Conversation]:
        """
        Update an existing conversation.
        
        Args:
            conversation_id: ID of the conversation to update
            conversation_data: Dictionary containing updated data
            
        Returns:
            Updated Conversation object or None if an error occurred
        """
        try:
            conversation = Conversation.query.get(conversation_id)
            if conversation is None:
                return None
            
            if 'title' in conversation_data:
                conversation.title = conversation_data['title']
            if 'model' in conversation_data:
                conversation.model = conversation_data['model']
            if 'is_active' in conversation_data:
                conversation.is_active = conversation_data['is_active']
                
            db.session.commit()
            return conversation
        except SQLAlchemyError:
            db.session.rollback()
            return None
    
    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """
        Delete a conversation (soft delete by setting is_active to False).
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = Conversation.query.get(conversation_id)
            if conversation is None:
                return False
            
            # Soft delete
            conversation.is_active = False
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @staticmethod
    def hard_delete_conversation(conversation_id: int) -> bool:
        """
        Permanently delete a conversation and all its messages.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = Conversation.query.get(conversation_id)
            if conversation is None:
                return False
            
            # Hard delete
            db.session.delete(conversation)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
    
    @staticmethod
    def save_message(conversation_id: int, message_data: Dict[str, Any]) -> Optional[Message]:
        """
        Save a new message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            message_data: Dictionary containing message data
            
        Returns:
            Saved Message object or None if an error occurred
        """
        try:
            # Verify the conversation exists
            conversation = Conversation.query.get(conversation_id)
            if conversation is None:
                return None
            
            # Create and save the message
            role = message_data.get('role', 'user')
            content = message_data.get('content', '')
            metadata = message_data.get('metadata')
            
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata  # This will be stored in message_metadata field
            )
            # Preserve metadata on the instance for immediate access in tests
            message.metadata = metadata
            
            # Update the conversation's updated_at timestamp
            conversation.updated_at = db.func.now()
            
            db.session.add(message)
            db.session.commit()
            return message
        except SQLAlchemyError:
            db.session.rollback()
            return None
    
    @staticmethod
    def get_messages(conversation_id: int) -> List[Message]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of Message objects
        """
        return Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at).all()
    
    @staticmethod
    def get_conversation_with_messages(conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a conversation and all its messages.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary containing conversation and messages data
        """
        conversation = Conversation.query.get(conversation_id)
        if conversation is None:
            return None
        
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at).all()
        
        return {
            'conversation': conversation.to_dict(),
            'messages': [message.to_dict() for message in messages]
        }
