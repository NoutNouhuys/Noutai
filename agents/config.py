"""
Agent configuratie voor multi-agent systeem.

Dit module bevat alle configuratie voor de verschillende agents,
inclusief model settings, system prompts en workflow definities.
"""

import os
from typing import Dict, Any, List

# Base directory voor agent prompts
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

# Agent configuraties
AGENT_CONFIG = {
    "issue_manager": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.2,
        "system_prompt": os.path.join(PROMPTS_DIR, "issue_manager.txt"),
        "class": "IssueManagerAgent",
        "description": "Analyseert project staat en beheert GitHub issues",
        "capabilities": [
            "project_analysis",
            "issue_creation",
            "issue_prioritization",
            "project_planning"
        ]
    },
    "code_developer": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.2,
        "system_prompt": os.path.join(PROMPTS_DIR, "code_developer.txt"),
        "class": "CodeDeveloperAgent",
        "description": "Schrijft en wijzigt code volgens specificaties",
        "capabilities": [
            "code_generation",
            "code_modification",
            "branch_management",
            "testing"
        ]
    },
    "pr_manager": {
        "model": "claude-3-haiku-20240307",
        "temperature": 0.2,
        "system_prompt": os.path.join(PROMPTS_DIR, "pr_manager.txt"),
        "class": "PRManagerAgent",
        "description": "Beheert pull requests en merge operaties",
        "capabilities": [
            "pr_creation",
            "pr_description",
            "merge_management",
            "branch_cleanup"
        ]
    },
    "documentation": {
        "model": "claude-3-haiku-20240307",
        "temperature": 0.3,
        "system_prompt": os.path.join(PROMPTS_DIR, "documentation.txt"),
        "class": "DocumentationAgent",
        "description": "Werkt project documentatie bij",
        "capabilities": [
            "project_info_update",
            "readme_update",
            "documentation_generation",
            "changelog_management"
        ]
    }
}

# Workflow definities
WORKFLOWS = {
    "development_cycle": {
        "description": "Volledige ontwikkel cyclus van issue tot merge",
        "steps": [
            {
                "agent": "issue_manager",
                "action": "analyze_project_state",
                "inputs": ["project_info", "project_stappen"],
                "outputs": ["next_issue", "priority"]
            },
            {
                "agent": "issue_manager",
                "action": "create_or_update_issue",
                "inputs": ["next_issue", "priority"],
                "outputs": ["issue_id", "issue_spec"]
            },
            {
                "agent": "code_developer",
                "action": "implement_feature",
                "inputs": ["issue_spec"],
                "outputs": ["code_changes", "branch_name"]
            },
            {
                "agent": "documentation",
                "action": "update_project_docs",
                "inputs": ["code_changes", "issue_spec"],
                "outputs": ["updated_docs"]
            },
            {
                "agent": "pr_manager",
                "action": "create_pull_request",
                "inputs": ["code_changes", "branch_name", "updated_docs"],
                "outputs": ["pr_id", "pr_url"]
            }
        ]
    },
    "issue_analysis": {
        "description": "Analyseer bestaand issue en maak implementatie plan",
        "steps": [
            {
                "agent": "issue_manager",
                "action": "analyze_issue",
                "inputs": ["issue_id"],
                "outputs": ["implementation_plan"]
            },
            {
                "agent": "code_developer",
                "action": "create_implementation_strategy",
                "inputs": ["implementation_plan"],
                "outputs": ["development_strategy"]
            }
        ]
    },
    "documentation_update": {
        "description": "Update project documentatie",
        "steps": [
            {
                "agent": "documentation",
                "action": "analyze_current_docs",
                "inputs": ["project_state"],
                "outputs": ["doc_updates_needed"]
            },
            {
                "agent": "documentation",
                "action": "update_documentation",
                "inputs": ["doc_updates_needed"],
                "outputs": ["updated_documentation"]
            }
        ]
    }
}

# Agent prioriteiten voor resource management
AGENT_PRIORITIES = {
    "issue_manager": 1,      # Hoogste prioriteit - bepaalt wat er gebeurt
    "code_developer": 2,     # Hoge prioriteit - core functionaliteit
    "documentation": 3,      # Medium prioriteit - ondersteunend
    "pr_manager": 4          # Lage prioriteit - afronding
}

# Model kosten (relatief, voor optimalisatie)
MODEL_COSTS = {
    "claude-3-5-sonnet-20241022": 10,  # Duurste, beste kwaliteit
    "claude-3-haiku-20240307": 1       # Goedkoopste, snelste
}

# Maximum gelijktijdige agents
MAX_CONCURRENT_AGENTS = 2

# Timeout settings (in seconden)
AGENT_TIMEOUTS = {
    "issue_manager": 300,     # 5 minuten
    "code_developer": 600,    # 10 minuten
    "documentation": 180,     # 3 minuten
    "pr_manager": 120         # 2 minuten
}

# Retry settings
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 5,  # seconden
    "exponential_backoff": True
}


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """
    Krijg configuratie voor een specifieke agent.
    
    Args:
        agent_name: Naam van de agent
        
    Returns:
        Configuratie dictionary voor de agent
        
    Raises:
        KeyError: Als de agent niet bestaat
    """
    if agent_name not in AGENT_CONFIG:
        raise KeyError(f"Agent '{agent_name}' not found in configuration")
    
    return AGENT_CONFIG[agent_name].copy()


def get_workflow_config(workflow_name: str) -> Dict[str, Any]:
    """
    Krijg configuratie voor een specifieke workflow.
    
    Args:
        workflow_name: Naam van de workflow
        
    Returns:
        Workflow configuratie dictionary
        
    Raises:
        KeyError: Als de workflow niet bestaat
    """
    if workflow_name not in WORKFLOWS:
        raise KeyError(f"Workflow '{workflow_name}' not found in configuration")
    
    return WORKFLOWS[workflow_name].copy()


def get_all_agent_names() -> List[str]:
    """
    Krijg lijst van alle beschikbare agent namen.
    
    Returns:
        Liste van agent namen
    """
    return list(AGENT_CONFIG.keys())


def get_all_workflow_names() -> List[str]:
    """
    Krijg lijst van alle beschikbare workflow namen.
    
    Returns:
        Liste van workflow namen
    """
    return list(WORKFLOWS.keys())


def validate_agent_config(agent_name: str) -> bool:
    """
    Valideer of een agent configuratie compleet en correct is.
    
    Args:
        agent_name: Naam van de agent om te valideren
        
    Returns:
        True als configuratie geldig is, False anders
    """
    try:
        config = get_agent_config(agent_name)
        
        # Check verplichte velden
        required_fields = ['model', 'temperature', 'system_prompt', 'class']
        for field in required_fields:
            if field not in config:
                return False
        
        # Check temperature range
        temp = config['temperature']
        if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 1.0:
            return False
        
        # Check of system prompt bestand bestaat
        if not os.path.exists(config['system_prompt']):
            return False
        
        return True
        
    except Exception:
        return False


def get_agent_cost_estimate(agent_name: str) -> int:
    """
    Krijg kosten schatting voor een agent.
    
    Args:
        agent_name: Naam van de agent
        
    Returns:
        Relatieve kosten schatting
    """
    config = get_agent_config(agent_name)
    model = config['model']
    return MODEL_COSTS.get(model, 5)  # Default medium cost


def get_optimal_agent_for_task(task_type: str) -> str:
    """
    Bepaal de optimale agent voor een specifiek taak type.
    
    Args:
        task_type: Type taak (bijv. 'code_generation', 'documentation')
        
    Returns:
        Naam van de optimale agent
    """
    # Zoek agents die deze capability hebben
    suitable_agents = []
    for agent_name, config in AGENT_CONFIG.items():
        if task_type in config.get('capabilities', []):
            cost = get_agent_cost_estimate(agent_name)
            suitable_agents.append((agent_name, cost))
    
    if not suitable_agents:
        # Fallback naar issue_manager als geen specifieke agent gevonden
        return "issue_manager"
    
    # Sorteer op kosten (laagste eerst) en return de goedkoopste
    suitable_agents.sort(key=lambda x: x[1])
    return suitable_agents[0][0]