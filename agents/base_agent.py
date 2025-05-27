"""
Base Agent class voor multi-agent architectuur.

Deze module bevat de basis functionaliteit die alle agents delen,
inclusief conversation management, context handling en communicatie.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from anthropic_api import AnthropicAPI
from conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class voor alle agents in het multi-agent systeem.
    
    Elke agent heeft zijn eigen conversation context, model configuratie
    en gespecialiseerde functionaliteit.
    """
    
    def __init__(self, name: str, model: str, temperature: float, system_prompt_file: str):
        """
        Initialiseer een nieuwe agent.
        
        Args:
            name: Unieke naam voor de agent
            model: Claude model om te gebruiken (bijv. claude-3-haiku-20240307)
            temperature: Temperature setting voor de agent (0.0-1.0)
            system_prompt_file: Pad naar het system prompt bestand
        """
        self.name = name
        self.model = model
        self.temperature = temperature
        self.system_prompt_file = system_prompt_file
        self.system_prompt = self._load_system_prompt()
        self.conversation_id = None
        self.conversation_manager = ConversationManager()
        self.anthropic_api = AnthropicAPI()
        self.status = "idle"  # idle, active, error, completed
        self.last_output = None
        self.context_data = {}
        
        logger.info(f"Initialized agent '{name}' with model {model} and temperature {temperature}")
    
    def _load_system_prompt(self) -> str:
        """
        Laad het system prompt bestand voor deze agent.
        
        Returns:
            De inhoud van het system prompt bestand
            
        Raises:
            FileNotFoundError: Als het system prompt bestand niet bestaat
        """
        try:
            with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                logger.debug(f"Loaded system prompt for agent '{self.name}' from {self.system_prompt_file}")
                return content
        except FileNotFoundError:
            logger.error(f"System prompt file not found: {self.system_prompt_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading system prompt for agent '{self.name}': {e}")
            raise
    
    @abstractmethod
    def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Voer de agent-specifieke taak uit.
        
        Args:
            task_input: Input data voor de taak
            
        Returns:
            Output data van de uitgevoerde taak
        """
        pass
    
    def start_conversation(self, title: str = None) -> str:
        """
        Start een nieuwe conversation voor deze agent.
        
        Args:
            title: Optionele titel voor de conversation
            
        Returns:
            De conversation ID
        """
        if not title:
            title = f"{self.name} - {self._generate_conversation_title()}"
        
        self.conversation_id = self.conversation_manager.start_conversation(title)
        logger.info(f"Started conversation {self.conversation_id} for agent '{self.name}'")
        return self.conversation_id
    
    def _generate_conversation_title(self) -> str:
        """
        Genereer een automatische titel voor de conversation.
        
        Returns:
            Een beschrijvende titel
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"Session {timestamp}"
    
    def send_message(self, message: str, **kwargs) -> str:
        """
        Stuur een bericht naar de AI en krijg een response.
        
        Args:
            message: Het bericht om te sturen
            **kwargs: Extra parameters voor de API call
            
        Returns:
            De AI response
        """
        if not self.conversation_id:
            self.start_conversation()
        
        self.status = "active"
        
        try:
            # Merge agent-specifieke settings met kwargs
            api_kwargs = {
                'model': self.model,
                'temperature': self.temperature,
                **kwargs
            }
            
            response = self.anthropic_api.send_prompt(
                message,
                conversation_id=self.conversation_id,
                **api_kwargs
            )
            
            self.last_output = response
            self.status = "completed"
            
            logger.info(f"Agent '{self.name}' processed message successfully")
            return response
            
        except Exception as e:
            self.status = "error"
            logger.error(f"Error in agent '{self.name}' while processing message: {e}")
            raise
    
    def clear_context(self):
        """
        Reset de conversation context voor een nieuwe taak.
        """
        if self.conversation_id:
            logger.info(f"Clearing context for agent '{self.name}', conversation {self.conversation_id}")
        
        self.conversation_id = None
        self.status = "idle"
        self.last_output = None
        self.context_data.clear()
    
    def set_context_data(self, key: str, value: Any):
        """
        Sla context data op voor gebruik in latere operaties.
        
        Args:
            key: De sleutel voor de data
            value: De waarde om op te slaan
        """
        self.context_data[key] = value
        logger.debug(f"Set context data for agent '{self.name}': {key}")
    
    def get_context_data(self, key: str, default: Any = None) -> Any:
        """
        Haal context data op.
        
        Args:
            key: De sleutel van de data
            default: Standaardwaarde als de sleutel niet bestaat
            
        Returns:
            De opgeslagen waarde of de standaardwaarde
        """
        return self.context_data.get(key, default)
    
    def pass_to_next(self, next_agent: 'BaseAgent', data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Geef data door aan de volgende agent in de workflow.
        
        Args:
            next_agent: De agent om data naar door te geven
            data: De data om door te geven
            
        Returns:
            Het resultaat van de volgende agent
        """
        logger.info(f"Passing data from agent '{self.name}' to agent '{next_agent.name}'")
        
        # Voeg metadata toe over de vorige agent
        data['previous_agent'] = self.name
        data['previous_output'] = self.last_output
        
        # Voer de volgende agent uit
        return next_agent.execute(data)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Krijg de huidige status van de agent.
        
        Returns:
            Status informatie van de agent
        """
        return {
            'name': self.name,
            'status': self.status,
            'model': self.model,
            'temperature': self.temperature,
            'conversation_id': self.conversation_id,
            'has_output': self.last_output is not None,
            'context_keys': list(self.context_data.keys())
        }
    
    def __str__(self) -> str:
        """String representatie van de agent."""
        return f"Agent(name='{self.name}', model='{self.model}', status='{self.status}')"
    
    def __repr__(self) -> str:
        """Repr representatie van de agent."""
        return (f"BaseAgent(name='{self.name}', model='{self.model}', "
                f"temperature={self.temperature}, status='{self.status}')")