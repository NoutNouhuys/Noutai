"""
Agent Orchestrator voor multi-agent workflow management.

Deze module coördineert de uitvoering van workflows tussen verschillende agents,
beheert resource allocatie en monitort de voortgang van taken.
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from enum import Enum

from .config import (
    AGENT_CONFIG, WORKFLOWS, AGENT_PRIORITIES, AGENT_TIMEOUTS,
    MAX_CONCURRENT_AGENTS, RETRY_CONFIG,
    get_agent_config, get_workflow_config, validate_agent_config
)

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status van een workflow uitvoering."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowExecution:
    """Representeert een workflow uitvoering."""
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    current_step: int
    total_steps: int
    start_time: float
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    results: Dict[str, Any] = None
    active_agents: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.active_agents is None:
            self.active_agents = []


class AgentOrchestrator:
    """
    Orchestrator voor het beheren van multi-agent workflows.
    
    Coördineert de uitvoering van workflows, beheert agent resources
    en monitort de voortgang van taken.
    """
    
    def __init__(self):
        """Initialiseer de orchestrator."""
        self.agents: Dict[str, Any] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_AGENTS)
        self.workflow_callbacks: Dict[str, List[Callable]] = {}
        self._execution_counter = 0
        
        logger.info("AgentOrchestrator initialized")
    
    def load_agents(self) -> Dict[str, Any]:
        """
        Laad alle geconfigureerde agents.
        
        Returns:
            Dictionary van geladen agents
        """
        loaded_agents = {}
        
        for agent_name, config in AGENT_CONFIG.items():
            try:
                if not validate_agent_config(agent_name):
                    logger.error(f"Invalid configuration for agent '{agent_name}'")
                    continue
                
                # Dynamisch importeren van agent class
                agent_class = self._import_agent_class(config['class'])
                
                # Instantieer agent
                agent = agent_class(
                    name=agent_name,
                    model=config['model'],
                    temperature=config['temperature'],
                    system_prompt_file=config['system_prompt']
                )
                
                loaded_agents[agent_name] = agent
                logger.info(f"Loaded agent '{agent_name}' ({config['class']})")
                
            except Exception as e:
                logger.error(f"Failed to load agent '{agent_name}': {e}")
                continue
        
        self.agents = loaded_agents
        return loaded_agents
    
    def _import_agent_class(self, class_name: str):
        """
        Importeer een agent class dynamisch.
        
        Args:
            class_name: Naam van de class om te importeren
            
        Returns:
            De geïmporteerde class
        """
        # Mapping van class namen naar werkelijke classes
        class_mapping = {
            'IssueManagerAgent': self._get_issue_manager_class,
            'CodeDeveloperAgent': self._get_base_agent_class,
            'PRManagerAgent': self._get_base_agent_class,
            'DocumentationAgent': self._get_base_agent_class
        }
        
        class_getter = class_mapping.get(class_name, self._get_base_agent_class)
        return class_getter()
    
    def _get_base_agent_class(self):
        """Krijg BaseAgent class."""
        from .base_agent import BaseAgent
        return BaseAgent
    
    def _get_issue_manager_class(self):
        """Krijg IssueManagerAgent class."""
        from .issue_manager_agent import IssueManagerAgent
        return IssueManagerAgent
    
    def execute_workflow(self, workflow_name: str, initial_input: Dict[str, Any] = None) -> str:
        """
        Start de uitvoering van een workflow.
        
        Args:
            workflow_name: Naam van de workflow om uit te voeren
            initial_input: Initiële input data voor de workflow
            
        Returns:
            Workflow execution ID
            
        Raises:
            ValueError: Als de workflow niet bestaat
        """
        if workflow_name not in WORKFLOWS:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # Genereer unieke execution ID
        self._execution_counter += 1
        execution_id = f"{workflow_name}_{self._execution_counter}_{int(time.time())}"
        
        # Maak workflow execution object
        workflow_config = get_workflow_config(workflow_name)
        execution = WorkflowExecution(
            workflow_id=execution_id,
            workflow_name=workflow_name,
            status=WorkflowStatus.PENDING,
            current_step=0,
            total_steps=len(workflow_config['steps']),
            start_time=time.time()
        )
        
        self.active_executions[execution_id] = execution
        
        # Start workflow in background
        future = self.executor.submit(self._execute_workflow_steps, execution_id, initial_input or {})
        
        logger.info(f"Started workflow '{workflow_name}' with execution ID '{execution_id}'")
        return execution_id
    
    def _execute_workflow_steps(self, execution_id: str, input_data: Dict[str, Any]):
        """
        Voer de stappen van een workflow uit.
        
        Args:
            execution_id: ID van de workflow execution
            input_data: Input data voor de workflow
        """
        execution = self.active_executions[execution_id]
        
        try:
            execution.status = WorkflowStatus.RUNNING
            workflow_config = get_workflow_config(execution.workflow_name)
            
            current_data = input_data.copy()
            
            # Voeg project informatie toe aan input data
            current_data.update(self._get_project_context())
            
            for step_index, step in enumerate(workflow_config['steps']):
                execution.current_step = step_index + 1
                
                agent_name = step['agent']
                action = step['action']
                
                logger.info(f"Executing step {execution.current_step}/{execution.total_steps}: "
                           f"{agent_name}.{action}")
                
                # Check of agent beschikbaar is
                if agent_name not in self.agents:
                    raise ValueError(f"Agent '{agent_name}' not available")
                
                agent = self.agents[agent_name]
                execution.active_agents = [agent_name]
                
                # Voer agent actie uit met timeout
                timeout = AGENT_TIMEOUTS.get(agent_name, 300)
                
                try:
                    # Bereid input data voor
                    step_input = self._prepare_step_input(step, current_data)
                    step_input['action'] = action
                    
                    # Voer agent uit met retry logica
                    step_result = self._execute_agent_with_retry(agent, step_input, timeout)
                    
                    # Update current data met resultaten
                    current_data.update(step_result)
                    execution.results[f"step_{step_index + 1}"] = step_result
                    
                    logger.info(f"Completed step {execution.current_step}: {agent_name}.{action}")
                    
                except TimeoutError:
                    raise Exception(f"Agent '{agent_name}' timed out after {timeout} seconds")
                except Exception as e:
                    raise Exception(f"Agent '{agent_name}' failed: {str(e)}")
            
            # Workflow succesvol voltooid
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = time.time()
            execution.active_agents = []
            
            logger.info(f"Workflow '{execution.workflow_name}' completed successfully")
            
            # Trigger callbacks
            self._trigger_callbacks(execution_id, 'completed', execution.results)
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = time.time()
            execution.error_message = str(e)
            execution.active_agents = []
            
            logger.error(f"Workflow '{execution.workflow_name}' failed: {e}")
            
            # Trigger callbacks
            self._trigger_callbacks(execution_id, 'failed', {'error': str(e)})
    
    def _get_project_context(self) -> Dict[str, Any]:
        """
        Krijg project context informatie.
        
        Returns:
            Dictionary met project context
        """
        context = {}
        
        # Lees project bestanden
        try:
            with open('project_info.txt', 'r', encoding='utf-8') as f:
                context['project_info'] = f.read()
        except FileNotFoundError:
            context['project_info'] = ""
        
        try:
            with open('project_stappen.txt', 'r', encoding='utf-8') as f:
                context['project_stappen'] = f.read()
        except FileNotFoundError:
            context['project_stappen'] = ""
        
        return context
    
    def _prepare_step_input(self, step: Dict[str, Any], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bereid input data voor een workflow step.
        
        Args:
            step: Step configuratie
            current_data: Huidige data van de workflow
            
        Returns:
            Input data voor de step
        """
        step_input = {}
        
        # Voeg gevraagde inputs toe
        for input_key in step.get('inputs', []):
            if input_key in current_data:
                step_input[input_key] = current_data[input_key]
            else:
                logger.warning(f"Required input '{input_key}' not found in current data")
        
        return step_input
    
    def _execute_agent_with_retry(self, agent, input_data: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """
        Voer een agent uit met retry logica.
        
        Args:
            agent: De agent om uit te voeren
            input_data: Input data voor de agent
            timeout: Timeout in seconden
            
        Returns:
            Resultaat van de agent
        """
        max_retries = RETRY_CONFIG['max_retries']
        retry_delay = RETRY_CONFIG['retry_delay']
        exponential_backoff = RETRY_CONFIG['exponential_backoff']
        
        for attempt in range(max_retries + 1):
            try:
                # Voer agent uit met timeout
                future = self.executor.submit(agent.execute, input_data)
                result = future.result(timeout=timeout)
                return result
                
            except Exception as e:
                if attempt == max_retries:
                    # Laatste poging gefaald
                    raise e
                
                # Wacht voor retry
                delay = retry_delay * (2 ** attempt if exponential_backoff else 1)
                logger.warning(f"Agent execution failed (attempt {attempt + 1}/{max_retries + 1}), "
                              f"retrying in {delay} seconds: {e}")
                time.sleep(delay)
        
        # Dit punt zou nooit bereikt moeten worden
        raise Exception("Unexpected error in retry logic")
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Krijg de status van een workflow execution.
        
        Args:
            execution_id: ID van de execution
            
        Returns:
            Status informatie of None als execution niet bestaat
        """
        if execution_id not in self.active_executions:
            return None
        
        execution = self.active_executions[execution_id]
        
        # Bereken duration
        end_time = execution.end_time or time.time()
        duration = end_time - execution.start_time
        
        return {
            'execution_id': execution.workflow_id,
            'workflow_name': execution.workflow_name,
            'status': execution.status.value,
            'current_step': execution.current_step,
            'total_steps': execution.total_steps,
            'progress_percentage': (execution.current_step / execution.total_steps) * 100,
            'duration': duration,
            'active_agents': execution.active_agents,
            'error_message': execution.error_message,
            'has_results': bool(execution.results)
        }
    
    def get_all_executions_status(self) -> List[Dict[str, Any]]:
        """
        Krijg status van alle actieve executions.
        
        Returns:
            Liste van execution statuses
        """
        return [
            self.get_execution_status(execution_id)
            for execution_id in self.active_executions.keys()
        ]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Annuleer een workflow execution.
        
        Args:
            execution_id: ID van de execution om te annuleren
            
        Returns:
            True als succesvol geannuleerd, False anders
        """
        if execution_id not in self.active_executions:
            return False
        
        execution = self.active_executions[execution_id]
        
        if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False
        
        execution.status = WorkflowStatus.CANCELLED
        execution.end_time = time.time()
        execution.active_agents = []
        
        logger.info(f"Cancelled workflow execution '{execution_id}'")
        
        # Trigger callbacks
        self._trigger_callbacks(execution_id, 'cancelled', {})
        
        return True
    
    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """
        Krijg status van agents.
        
        Args:
            agent_name: Specifieke agent naam, of None voor alle agents
            
        Returns:
            Status informatie van agent(s)
        """
        if agent_name:
            if agent_name not in self.agents:
                return {}
            return self.agents[agent_name].get_status()
        
        # Return status van alle agents
        return {
            name: agent.get_status()
            for name, agent in self.agents.items()
        }
    
    def register_callback(self, execution_id: str, callback: Callable):
        """
        Registreer een callback voor workflow events.
        
        Args:
            execution_id: ID van de execution
            callback: Callback functie om aan te roepen
        """
        if execution_id not in self.workflow_callbacks:
            self.workflow_callbacks[execution_id] = []
        
        self.workflow_callbacks[execution_id].append(callback)
    
    def _trigger_callbacks(self, execution_id: str, event_type: str, data: Dict[str, Any]):
        """
        Trigger callbacks voor een workflow event.
        
        Args:
            execution_id: ID van de execution
            event_type: Type event (completed, failed, cancelled)
            data: Event data
        """
        if execution_id not in self.workflow_callbacks:
            return
        
        for callback in self.workflow_callbacks[execution_id]:
            try:
                callback(execution_id, event_type, data)
            except Exception as e:
                logger.error(f"Error in workflow callback: {e}")
    
    def cleanup_completed_executions(self, max_age_hours: int = 24):
        """
        Ruim oude voltooide executions op.
        
        Args:
            max_age_hours: Maximum leeftijd in uren voor voltooide executions
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        
        for execution_id, execution in self.active_executions.items():
            if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                if execution.end_time and (current_time - execution.end_time) > max_age_seconds:
                    to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.active_executions[execution_id]
            if execution_id in self.workflow_callbacks:
                del self.workflow_callbacks[execution_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old workflow executions")
    
    def shutdown(self):
        """Sluit de orchestrator af en ruim resources op."""
        logger.info("Shutting down AgentOrchestrator")
        
        # Cancel alle actieve executions
        for execution_id in list(self.active_executions.keys()):
            self.cancel_execution(execution_id)
        
        # Sluit thread pool af
        self.executor.shutdown(wait=True)
        
        logger.info("AgentOrchestrator shutdown complete")