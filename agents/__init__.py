"""
Multi-Agent System Package

Dit package bevat alle componenten voor het multi-agent systeem,
inclusief agent classes, orchestrator en configuratie.
"""

from .base_agent import BaseAgent
from .orchestrator import AgentOrchestrator
from .issue_manager_agent import IssueManagerAgent
from .config import (
    AGENT_CONFIG,
    WORKFLOWS,
    get_agent_config,
    get_workflow_config,
    get_all_agent_names,
    get_all_workflow_names
)

__version__ = "1.0.0"
__author__ = "AI Development Team"

__all__ = [
    'BaseAgent',
    'AgentOrchestrator', 
    'IssueManagerAgent',
    'AGENT_CONFIG',
    'WORKFLOWS',
    'get_agent_config',
    'get_workflow_config',
    'get_all_agent_names',
    'get_all_workflow_names'
]