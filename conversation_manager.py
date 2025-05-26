"""
Conversation management module.
Handles conversation state and history with database persistence.
"""
import time
import uuid
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class Conversation:
    """Represents a conversation with its messages."""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    model: Optional[str] = None
    is_active: bool = True


class ConversationManager:
    """Manages conversation state and history with database persistence."""
    
    def __init__(self, storage_backend=None, user_id: Optional[str] = None):
        """
        Initialize the conversation manager.
        
        Args:
            storage_backend: Optional storage backend for persistence
            user_id: User ID for database operations (required for persistence)
        """
        self.storage_backend = storage_backend
        self.user_id = user_id
        self._conversations: Dict[str, Conversation] = {}
        
        # Import repository if storage backend is enabled
        if self.storage_backend:
            try:
                from repositories.conversation_repository import ConversationRepository
                self.repository = ConversationRepository
            except ImportError:
                logger.warning("ConversationRepository not available, falling back to in-memory storage")
                self.storage_backend = None
                self.repository = None
        else:
            self.repository = None
        
    def create_conversation(self, conversation_id: Optional[str] = None, 
                          title: Optional[str] = None, 
                          model: Optional[str] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Optional ID for the conversation
            title: Optional title for the conversation
            model: Optional model name for the conversation
            
        Returns:
            The conversation ID
        """
        # If using database storage, create in database first
        if self.storage_backend and self.repository and self.user_id:
            conversation_data = {
                'title': title or 'New Conversation',
                'model': model or 'claude-3-haiku-20240307'
            }
            
            db_conversation = self.repository.save_conversation(self.user_id, conversation_data)
            if db_conversation:
                conversation_id = str(db_conversation.id)
                logger.info(f"Created new conversation in database: {conversation_id}")
            else:
                logger.error("Failed to create conversation in database")
                raise RuntimeError("Failed to create conversation in database")
        else:
            # Fall back to UUID for in-memory storage
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
            
        # Create in-memory representation
        conversation = Conversation(
            id=conversation_id,
            title=title,
            model=model
        )
        self._conversations[conversation_id] = conversation
        
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def add_message(
        self,
        conversation_id: Union[str, int],
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (user/assistant)
            content: Message content
            metadata: Optional metadata for the message
            
        Raises:
            ValueError: If conversation doesn't exist
        """
        conversation_id_str = str(conversation_id)
        
        # Ensure conversation exists in memory
        if conversation_id_str not in self._conversations:
            # Try to load from database
            if not self._load_conversation_if_needed(conversation_id):
                raise ValueError(f"Conversation {conversation_id} not found")
        
        # Save to database if storage enabled
        if self.storage_backend and self.repository:
            message_data = {
                'role': role,
                'content': content,
                'metadata': metadata
            }
            
            db_message = self.repository.save_message(int(conversation_id), message_data)
            if not db_message:
                logger.error(f"Failed to save message to database for conversation {conversation_id}")
                # Continue with in-memory storage as fallback
        
        # Add to in-memory conversation
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self._conversations[conversation_id_str].messages.append(message)
        logger.debug(f"Added message to conversation {conversation_id_str}")
        
    def add_exchange(
        self,
        conversation_id: Union[str, int],
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a user-assistant exchange to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            user_message: User's message
            assistant_message: Assistant's response
            metadata: Optional metadata for the exchange
        """
        self.add_message(conversation_id, "user", user_message, metadata)
        self.add_message(conversation_id, "assistant", assistant_message, metadata)
        
    def get_conversation(self, conversation_id: Union[str, int]) -> Conversation:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            The conversation object
            
        Raises:
            ValueError: If conversation doesn't exist
        """
        conversation_id_str = str(conversation_id)
        
        # First check in-memory store
        if conversation_id_str in self._conversations:
            return self._conversations[conversation_id_str]
            
        # Try to load from storage backend if available
        if self._load_conversation_if_needed(conversation_id):
            return self._conversations[conversation_id_str]
                
        raise ValueError(f"Conversation {conversation_id} not found")
    
    def get_messages(self, conversation_id: Union[str, int]) -> List[Message]:
        """
        Get all messages in a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of messages
        """
        conversation = self.get_conversation(conversation_id)
        return conversation.messages
    
    def get_messages_for_api(self, conversation_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get messages formatted for the Anthropic API.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of message dictionaries
        """
        messages = self.get_messages(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    def exists(self, conversation_id: Union[str, int]) -> bool:
        """
        Check if a conversation exists.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if conversation exists
        """
        conversation_id_str = str(conversation_id)
        
        # Check in-memory first
        if conversation_id_str in self._conversations:
            return True
            
        # Check database if available
        if self.storage_backend and self.repository:
            try:
                db_conversation = self.repository.get_conversation(int(conversation_id))
                return db_conversation is not None and db_conversation.is_active
            except (ValueError, TypeError):
                pass
                
        return False
    
    def list_conversations(self, active_only: bool = True, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List conversations for the current user with pagination.
        
        Args:
            active_only: If True, returns only active conversations
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            
        Returns:
            List of conversation dictionaries with metadata
        """
        if not self.storage_backend or not self.repository or not self.user_id:
            # Return in-memory conversations if no database
            conversations = []
            for conv_id, conv in self._conversations.items():
                if not active_only or conv.is_active:
                    conversations.append({
                        'id': conv_id,
                        'title': conv.title or 'Untitled Conversation',
                        'model': conv.model or 'Unknown',
                        'created_at': datetime.fromtimestamp(conv.created_at).isoformat(),
                        'message_count': len(conv.messages),
                        'is_active': conv.is_active
                    })
            return conversations[offset:offset + limit]
        
        # Get from database
        try:
            db_conversations = self.repository.get_conversations(self.user_id, active_only)
            
            # Apply pagination
            paginated = db_conversations[offset:offset + limit]
            
            return [conv.to_dict() for conv in paginated]
        except Exception as e:
            logger.error(f"Failed to list conversations: {str(e)}")
            return []
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by title or content.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching conversation dictionaries
        """
        if not self.storage_backend or not self.repository or not self.user_id:
            # Basic in-memory search
            results = []
            query_lower = query.lower()
            for conv_id, conv in self._conversations.items():
                if (conv.title and query_lower in conv.title.lower()) or \
                   any(query_lower in msg.content.lower() for msg in conv.messages):
                    results.append({
                        'id': conv_id,
                        'title': conv.title or 'Untitled Conversation',
                        'model': conv.model or 'Unknown',
                        'created_at': datetime.fromtimestamp(conv.created_at).isoformat(),
                        'message_count': len(conv.messages),
                        'is_active': conv.is_active
                    })
            return results[:limit]
        
        # Database search would be implemented here
        # For now, fall back to basic filtering
        try:
            all_conversations = self.repository.get_conversations(self.user_id, active_only=True)
            query_lower = query.lower()
            
            results = []
            for conv in all_conversations:
                if query_lower in conv.title.lower():
                    results.append(conv.to_dict())
                    if len(results) >= limit:
                        break
                        
            return results
        except Exception as e:
            logger.error(f"Failed to search conversations: {str(e)}")
            return []
    
    def update_conversation(self, conversation_id: Union[str, int], 
                          title: Optional[str] = None,
                          is_active: Optional[bool] = None) -> bool:
        """
        Update conversation metadata.
        
        Args:
            conversation_id: ID of the conversation
            title: New title for the conversation
            is_active: Whether the conversation is active
            
        Returns:
            True if update was successful
        """
        conversation_id_str = str(conversation_id)
        
        # Update database if available
        if self.storage_backend and self.repository:
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if is_active is not None:
                update_data['is_active'] = is_active
                
            if update_data:
                try:
                    result = self.repository.update_conversation(int(conversation_id), update_data)
                    if not result:
                        logger.error(f"Failed to update conversation {conversation_id} in database")
                        return False
                except Exception as e:
                    logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
                    return False
        
        # Update in-memory if present
        if conversation_id_str in self._conversations:
            if title is not None:
                self._conversations[conversation_id_str].title = title
            if is_active is not None:
                self._conversations[conversation_id_str].is_active = is_active
        
        return True
    
    def delete_conversation(self, conversation_id: Union[str, int], soft_delete: bool = True) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            soft_delete: If True, marks as inactive; if False, permanently deletes
            
        Returns:
            True if deletion was successful
        """
        conversation_id_str = str(conversation_id)
        
        # Delete from database if available
        if self.storage_backend and self.repository:
            try:
                if soft_delete:
                    success = self.repository.delete_conversation(int(conversation_id))
                else:
                    success = self.repository.hard_delete_conversation(int(conversation_id))
                    
                if not success:
                    logger.error(f"Failed to delete conversation {conversation_id} from database")
                    return False
            except Exception as e:
                logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
                return False
        
        # Remove from in-memory store
        if conversation_id_str in self._conversations:
            if soft_delete:
                self._conversations[conversation_id_str].is_active = False
            else:
                del self._conversations[conversation_id_str]
        
        return True
    
    def _load_conversation_if_needed(self, conversation_id: Union[str, int]) -> bool:
        """
        Load conversation from storage backend if not in memory.
        
        Args:
            conversation_id: Database ID of the conversation
            
        Returns:
            True if conversation was loaded successfully
        """
        if not self.storage_backend or not self.repository:
            return False
            
        try:
            conversation_id_str = str(conversation_id)
            conversation_id_int = int(conversation_id)
            
            # Get conversation with messages from database
            result = self.repository.get_conversation_with_messages(conversation_id_int)
            if not result:
                return False
                
            conv_data = result['conversation']
            messages_data = result['messages']
            
            # Create in-memory conversation
            conversation = Conversation(
                id=conversation_id_str,
                title=conv_data.get('title'),
                model=conv_data.get('model'),
                is_active=conv_data.get('is_active', True)
            )
            
            # Convert database messages to in-memory messages
            for msg_data in messages_data:
                message = Message(
                    role=msg_data['role'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['created_at']).timestamp() if msg_data.get('created_at') else time.time(),
                    metadata=msg_data.get('metadata', {})
                )
                conversation.messages.append(message)
                
            self._conversations[conversation_id_str] = conversation
            logger.info(f"Loaded conversation {conversation_id} from storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load conversation from storage: {str(e)}")
            return False
    
    def clear(self) -> None:
        """Clear all in-memory conversations."""
        self._conversations.clear()
        logger.info("Cleared all in-memory conversations")