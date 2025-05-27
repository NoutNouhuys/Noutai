"""
API endpoints voor multi-agent systeem.

Deze module bevat alle REST API endpoints voor het beheren van
agents, workflows en multi-agent operaties.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List

from agents.orchestrator import AgentOrchestrator
from agents.config import get_all_agent_names, get_all_workflow_names, get_agent_config

logger = logging.getLogger(__name__)

# Blueprint voor agent endpoints
agents_bp = Blueprint('agents', __name__, url_prefix='/api/agents')

# Global orchestrator instance
orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """
    Krijg de global orchestrator instance.
    
    Returns:
        AgentOrchestrator instance
    """
    global orchestrator
    if orchestrator is None:
        orchestrator = AgentOrchestrator()
        orchestrator.load_agents()
    return orchestrator


@agents_bp.route('/status', methods=['GET'])
def get_agents_status():
    """
    Krijg status van alle agents.
    
    Returns:
        JSON response met agent statuses
    """
    try:
        orch = get_orchestrator()
        
        # Krijg status van alle agents
        agent_status = orch.get_agent_status()
        
        # Krijg status van actieve executions
        executions = orch.get_all_executions_status()
        
        return jsonify({
            'success': True,
            'agents': agent_status,
            'active_executions': executions,
            'total_agents': len(agent_status),
            'active_executions_count': len([e for e in executions if e['status'] == 'running'])
        })
        
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/execute', methods=['POST'])
def execute_workflow():
    """
    Start uitvoering van een workflow.
    
    Expected JSON body:
    {
        "workflow_name": "development_cycle",
        "input_data": {...}
    }
    
    Returns:
        JSON response met execution ID
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON body required'
            }), 400
        
        workflow_name = data.get('workflow_name')
        if not workflow_name:
            return jsonify({
                'success': False,
                'error': 'workflow_name is required'
            }), 400
        
        input_data = data.get('input_data', {})
        
        orch = get_orchestrator()
        execution_id = orch.execute_workflow(workflow_name, input_data)
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'workflow_name': workflow_name,
            'status': 'started'
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/execution/<execution_id>', methods=['GET'])
def get_execution_status(execution_id: str):
    """
    Krijg status van een specifieke workflow execution.
    
    Args:
        execution_id: ID van de execution
        
    Returns:
        JSON response met execution status
    """
    try:
        orch = get_orchestrator()
        status = orch.get_execution_status(execution_id)
        
        if status is None:
            return jsonify({
                'success': False,
                'error': 'Execution not found'
            }), 404
        
        return jsonify({
            'success': True,
            'execution': status
        })
        
    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/execution/<execution_id>/cancel', methods=['POST'])
def cancel_execution(execution_id: str):
    """
    Annuleer een workflow execution.
    
    Args:
        execution_id: ID van de execution om te annuleren
        
    Returns:
        JSON response met cancellation status
    """
    try:
        orch = get_orchestrator()
        success = orch.cancel_execution(execution_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Execution not found or cannot be cancelled'
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Execution {execution_id} cancelled'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling execution: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<agent_name>/chat', methods=['GET'])
def get_agent_chat(agent_name: str):
    """
    Krijg chat history voor een specifieke agent.
    
    Args:
        agent_name: Naam van de agent
        
    Returns:
        JSON response met chat history
    """
    try:
        orch = get_orchestrator()
        
        if agent_name not in orch.agents:
            return jsonify({
                'success': False,
                'error': f'Agent {agent_name} not found'
            }), 404
        
        agent = orch.agents[agent_name]
        
        # Krijg conversation history
        conversation_id = agent.conversation_id
        if not conversation_id:
            return jsonify({
                'success': True,
                'messages': [],
                'conversation_id': None
            })
        
        # Gebruik conversation manager om messages op te halen
        messages = agent.conversation_manager.get_messages(conversation_id)
        
        return jsonify({
            'success': True,
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ],
            'conversation_id': conversation_id,
            'agent_name': agent_name
        })
        
    except Exception as e:
        logger.error(f"Error getting agent chat: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<agent_name>/send', methods=['POST'])
def send_message_to_agent(agent_name: str):
    """
    Stuur een bericht naar een specifieke agent.
    
    Args:
        agent_name: Naam van de agent
        
    Expected JSON body:
    {
        "message": "Bericht voor de agent",
        "action": "optionele actie",
        "parameters": {...}
    }
    
    Returns:
        JSON response met agent response
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON body required'
            }), 400
        
        message = data.get('message')
        if not message:
            return jsonify({
                'success': False,
                'error': 'message is required'
            }), 400
        
        orch = get_orchestrator()
        
        if agent_name not in orch.agents:
            return jsonify({
                'success': False,
                'error': f'Agent {agent_name} not found'
            }), 404
        
        agent = orch.agents[agent_name]
        
        # Stuur bericht naar agent
        response = agent.send_message(message)
        
        return jsonify({
            'success': True,
            'response': response,
            'agent_name': agent_name,
            'conversation_id': agent.conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error sending message to agent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/config', methods=['GET'])
def get_agents_config():
    """
    Krijg configuratie van alle agents.
    
    Returns:
        JSON response met agent configuraties
    """
    try:
        agent_names = get_all_agent_names()
        workflow_names = get_all_workflow_names()
        
        agents_config = {}
        for agent_name in agent_names:
            config = get_agent_config(agent_name)
            # Verwijder system_prompt pad voor security
            config_safe = config.copy()
            config_safe.pop('system_prompt', None)
            agents_config[agent_name] = config_safe
        
        return jsonify({
            'success': True,
            'agents': agents_config,
            'workflows': workflow_names,
            'total_agents': len(agent_names),
            'total_workflows': len(workflow_names)
        })
        
    except Exception as e:
        logger.error(f"Error getting agents config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """
    Krijg lijst van beschikbare workflows.
    
    Returns:
        JSON response met workflow informatie
    """
    try:
        from agents.config import WORKFLOWS
        
        workflows_info = {}
        for workflow_name, config in WORKFLOWS.items():
            workflows_info[workflow_name] = {
                'name': workflow_name,
                'description': config.get('description', ''),
                'steps_count': len(config.get('steps', [])),
                'agents_involved': list(set(step['agent'] for step in config.get('steps', [])))
            }
        
        return jsonify({
            'success': True,
            'workflows': workflows_info
        })
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/cleanup', methods=['POST'])
def cleanup_executions():
    """
    Ruim oude voltooide executions op.
    
    Expected JSON body:
    {
        "max_age_hours": 24
    }
    
    Returns:
        JSON response met cleanup resultaat
    """
    try:
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        
        orch = get_orchestrator()
        
        # Tel executions voor cleanup
        before_count = len(orch.active_executions)
        
        # Voer cleanup uit
        orch.cleanup_completed_executions(max_age_hours)
        
        # Tel executions na cleanup
        after_count = len(orch.active_executions)
        cleaned_count = before_count - after_count
        
        return jsonify({
            'success': True,
            'cleaned_executions': cleaned_count,
            'remaining_executions': after_count,
            'max_age_hours': max_age_hours
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up executions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers
@agents_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@agents_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405


@agents_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500