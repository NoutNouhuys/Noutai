"""
Conversation management module.
Handles conversation state and history.
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


class ConversationManager:
    """Manages conversation state and history."""
    
    def __init__(self, storage_backend=None):
        """
        Initialize the conversation manager.
        
        Args:
            storage_backend: Optional storage backend for persistence
        """
        self.storage_backend = storage_backend
        self._conversations: Dict[str, Conversation] = {}
        
    def create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Optional ID for the conversation
            
        Returns:
            The conversation ID
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        conversation = Conversation(id=conversation_id)
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
        
        if conversation_id_str not in self._conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
            
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
        if self.storage_backend and isinstance(conversation_id, int):
            conversation = self._load_from_storage(conversation_id)
            if conversation:
                self._conversations[conversation_id_str] = conversation
                return conversation
                
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
        return conversation_id_str in self._conversations
    
    def add_repo_context(
        self,
        conversation_id: Union[str, int],
        repo_key: str,
        context: str
    ) -> None:
        """
        Add repository context to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            repo_key: Repository identifier (e.g., "owner/repo")
            context: Repository context content
        """
        conversation = self.get_conversation(conversation_id)
        
        # Initialize repo_contexts in metadata if not exists
        if "repo_contexts" not in conversation.metadata:
            conversation.metadata["repo_contexts"] = {}
        
        conversation.metadata["repo_contexts"][repo_key] = context
        logger.debug(f"Added repo context for {repo_key} to conversation {conversation_id}")
    
    def get_repo_context(
        self,
        conversation_id: Union[str, int],
        repo_key: str
    ) -> Optional[str]:
        """
        Get repository context from a conversation.
        
        Args:
            conversation_id: ID of the conversation
            repo_key: Repository identifier (e.g., "owner/repo")
            
        Returns:
            Repository context content or None if not found
        """
        conversation = self.get_conversation(conversation_id)
        return conversation.metadata.get("repo_contexts", {}).get(repo_key)
    
    def has_repo_context(
        self,
        conversation_id: Union[str, int],
        repo_key: str
    ) -> bool:
        """
        Check if repository context exists for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            repo_key: Repository identifier (e.g., "owner/repo")
            
        Returns:
            True if context exists
        """
        conversation = self.get_conversation(conversation_id)
        return repo_key in conversation.metadata.get("repo_contexts", {})
    
    def get_all_repo_contexts(
        self,
        conversation_id: Union[str, int]
    ) -> Dict[str, str]:
        """
        Get all repository contexts for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary of repo_key -> context mappings
        """
        conversation = self.get_conversation(conversation_id)
        return conversation.metadata.get("repo_contexts", {})
    
    def _load_from_storage(self, conversation_id: int) -> Optional[Conversation]:
        """
        Load conversation from storage backend.
        
        Args:
            conversation_id: Database ID of the conversation
            
        Returns:
            Conversation object or None if not found
        """
        if not self.storage_backend:
            return None
            
        try:
            # This would interface with ConversationRepository
            from repositories.conversation_repository import ConversationRepository
            
            db_messages = ConversationRepository.get_messages(conversation_id)
            if not db_messages:
                return None
                
            conversation = Conversation(id=str(conversation_id))
            
            for msg in db_messages:
                message = Message(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.created_at.timestamp()
                )
                conversation.messages.append(message)
                
            logger.info(f"Loaded conversation {conversation_id} from storage")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to load conversation from storage: {str(e)}")
            return None
    
    def clear(self) -> None:
        """Clear all in-memory conversations."""
        self._conversations.clear()
        logger.info("Cleared all in-memory conversations")