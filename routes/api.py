from flask import Blueprint, jsonify, request, Response, current_app
import json
import queue
import threading
from flask_login import login_required, current_user
from anthropic_api import anthropic_api
from auth import check_lynxx_domain
from repositories.conversation_repository import ConversationRepository
from repositories.analytics_repository import AnalyticsRepository
from models.conversation import Conversation, Message
from conversation_manager import ConversationManager

# Create a Blueprint for the API routes
api_bp = Blueprint('api', __name__)

@api_bp.route('/models', methods=['GET'])
@login_required
@check_lynxx_domain
def get_models():
    """
    API endpoint to retrieve available Claude models.
    
    Returns:
        JSON response with available models
    """
    try:
        models = anthropic_api.get_available_models()
        return jsonify({
            "success": True,
            "models": models
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/llm-settings', methods=['GET'])
@login_required
@check_lynxx_domain
def get_llm_settings():
    """
    API endpoint to retrieve current LLM settings.

    Query parameters:
        model_id: Optional model identifier for model-specific settings
        preset_name: Optional preset name to load settings from
        
    Returns:
        JSON response with current LLM settings
    """
    try:
        model_id = request.args.get('model_id')
        preset_name = request.args.get('preset_name')
        
        settings = anthropic_api.get_llm_settings(model_id=model_id, preset_name=preset_name)
        
        return jsonify({
            "success": True,
            "settings": settings,
            "model_id": model_id,
            "preset_name": preset_name
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/llm-settings', methods=['PUT'])
@login_required
@check_lynxx_domain
def update_llm_settings():
    """
    API endpoint to update LLM settings (runtime only).
    
    Request body:
        temperature: Optional temperature value (0.0-1.0)
        max_tokens: Optional maximum tokens value (> 0)
        
    Returns:
        JSON response with updated settings
    """
    try:
        data = request.get_json() or {}
        
        temperature = data.get('temperature')
        max_tokens = data.get('max_tokens')
        
        # Validate input values
        if temperature is not None:
            try:
                temperature = float(temperature)
                if not 0.0 <= temperature <= 1.0:
                    return jsonify({
                        "success": False,
                        "error": "Temperature must be between 0.0 and 1.0"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "Temperature must be a valid number"
                }), 400
        
        if max_tokens is not None:
            try:
                max_tokens = int(max_tokens)
                if max_tokens <= 0:
                    return jsonify({
                        "success": False,
                        "error": "Max tokens must be greater than 0"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "Max tokens must be a valid integer"
                }), 400
        
        # Update settings
        updated_settings = anthropic_api.update_runtime_settings(
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return jsonify({
            "success": True,
            "settings": updated_settings,
            "message": "LLM settings updated successfully"
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/llm-settings/defaults', methods=['GET'])
@login_required
@check_lynxx_domain
def get_default_settings():
    """
    API endpoint to retrieve default LLM settings.
    
    Returns:
        JSON response with default settings
    """
    try:
        # Get default settings from config
        default_settings = {
            "temperature": anthropic_api.temperature,
            "max_tokens": anthropic_api.max_tokens,
            "default_model": anthropic_api.default_model
        }
        
        return jsonify({
            "success": True,
            "defaults": default_settings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/llm-settings/presets', methods=['GET'])
@login_required
@check_lynxx_domain
def get_presets():
    """
    API endpoint to retrieve available LLM presets.
    
    Returns:
        JSON response with available presets
    """
    try:
        presets = anthropic_api.get_available_presets()
        
        return jsonify({
            "success": True,
            "presets": presets
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def _validate_model_id(model_id: str) -> bool:
    """
    Validate if the provided model_id exists in available models.
    
    Args:
        model_id: The model ID to validate
        
    Returns:
        True if model exists, False otherwise
    """
    try:
        available_models = anthropic_api.get_available_models()
        valid_model_ids = [model['id'] for model in available_models]
        return model_id in valid_model_ids
    except Exception:
        return False

@api_bp.route('/conversations', methods=['GET'])
@login_required
@check_lynxx_domain
def list_conversations():
    """
    API endpoint to retrieve a user's conversations with pagination and filtering.
    
    Query parameters:
        limit: Maximum number of conversations to return (default: 50, max: 100)
        offset: Number of conversations to skip (default: 0)
        active_only: Return only active conversations (default: true)
        include_usage: Include token usage data (default: true)
        
    Returns:
        JSON response with list of conversations and pagination info
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
        offset = max(int(request.args.get('offset', 0)), 0)   # Non-negative
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        include_usage = request.args.get('include_usage', 'true').lower() == 'true'
        
        # Create conversation manager with database backend
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        # Get conversations with pagination
        conversations = conv_manager.list_conversations(
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        
        # Add token usage data if requested
        if include_usage:
            analytics_repo = AnalyticsRepository()
            for conversation in conversations:
                usage_summary = analytics_repo.get_usage_summary_by_conversation(conversation['id'])
                if not usage_summary.get('error'):
                    conversation['token_usage'] = usage_summary
        
        # Get total count for pagination info
        total_conversations = ConversationRepository.get_conversations(current_user.id, active_only)
        total_count = len(total_conversations)
        
        return jsonify({
            "success": True,
            "conversations": conversations,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_more": offset + limit < total_count
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/conversations/search', methods=['GET'])
@login_required
@check_lynxx_domain
def search_conversations():
    """
    API endpoint to search conversations by title or content.
    
    Query parameters:
        q: Search query string (required)
        limit: Maximum number of results to return (default: 20, max: 50)
        
    Returns:
        JSON response with matching conversations
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                "success": False,
                "error": "Search query is required"
            }), 400
            
        limit = min(int(request.args.get('limit', 20)), 50)  # Cap at 50
        
        # Create conversation manager with database backend
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        # Search conversations
        results = conv_manager.search_conversations(query, limit)
        
        return jsonify({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/conversations', methods=['POST'])
@login_required
@check_lynxx_domain
def create_conversation():
    """
    API endpoint to create a new conversation.
    
    Returns:
        JSON response with new conversation info
    """
    try:
        data = request.get_json() or {}
        
        # Create conversation manager with database backend
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        # Create new conversation
        conversation_id = conv_manager.create_conversation(
            title=data.get('title', 'New Conversation'),
            model=data.get('model', 'claude-3-haiku-20240307')
        )
        
        # Get the created conversation details
        conversation = ConversationRepository.get_conversation(int(conversation_id))
        
        if conversation is None:
            return jsonify({
                "success": False,
                "error": "Failed to create conversation"
            }), 500
            
        return jsonify({
            "success": True,
            "conversation": conversation.to_dict()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@login_required
@check_lynxx_domain
def get_conversation(conversation_id):
    """
    API endpoint to retrieve a conversation's history.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        
    Returns:
        JSON response with conversation history
    """
    try:
        # Get conversation with messages
        result = ConversationRepository.get_conversation_with_messages(conversation_id)
        
        if result is None:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
        
        # Verify the conversation belongs to the current user
        if result['conversation']['user_id'] != current_user.id:
            return jsonify({
                "success": False,
                "error": "Not authorized to access this conversation"
            }), 403
            
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/conversations/<int:conversation_id>', methods=['PUT', 'PATCH'])
@login_required
@check_lynxx_domain
def update_conversation(conversation_id):
    """
    API endpoint to update conversation metadata.
    
    Args:
        conversation_id: ID of the conversation to update
        
    Returns:
        JSON response with updated conversation
    """
    try:
        # Get the conversation
        conversation = ConversationRepository.get_conversation(conversation_id)
        
        if conversation is None:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
            
        # Verify the conversation belongs to the current user
        if conversation.user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": "Not authorized to update this conversation"
            }), 403
            
        # Update the conversation using ConversationManager
        data = request.get_json() or {}
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        success = conv_manager.update_conversation(
            conversation_id=conversation_id,
            title=data.get('title'),
            is_active=data.get('is_active')
        )
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Failed to update conversation"
            }), 500
            
        # Get updated conversation
        updated = ConversationRepository.get_conversation(conversation_id)
        
        return jsonify({
            "success": True,
            "conversation": updated.to_dict()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
@check_lynxx_domain
def delete_conversation(conversation_id):
    """
    API endpoint to delete a conversation.
    
    Args:
        conversation_id: ID of the conversation to delete
        
    Query parameters:
        soft_delete: If true, marks as inactive; if false, permanently deletes (default: true)
        
    Returns:
        JSON response with operation status
    """
    try:
        # Get the conversation
        conversation = ConversationRepository.get_conversation(conversation_id)
        
        if conversation is None:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
            
        # Verify the conversation belongs to the current user
        if conversation.user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": "Not authorized to delete this conversation"
            }), 403
            
        # Delete using ConversationManager
        soft_delete = request.args.get('soft_delete', 'true').lower() == 'true'
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        success = conv_manager.delete_conversation(conversation_id, soft_delete=soft_delete)
            
        if not success:
            return jsonify({
                "success": False,
                "error": "Failed to delete conversation"
            }), 500
            
        return jsonify({
            "success": True,
            "message": f"Conversation {'deactivated' if soft_delete else 'deleted'} successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/conversations/bulk', methods=['DELETE'])
@login_required
@check_lynxx_domain
def bulk_delete_conversations():
    """
    API endpoint to delete multiple conversations.
    
    Request body:
        conversation_ids: List of conversation IDs to delete
        soft_delete: If true, marks as inactive; if false, permanently deletes (default: true)
        
    Returns:
        JSON response with operation results
    """
    try:
        data = request.get_json() or {}
        conversation_ids = data.get('conversation_ids', [])
        
        if not conversation_ids or not isinstance(conversation_ids, list):
            return jsonify({
                "success": False,
                "error": "conversation_ids must be a non-empty list"
            }), 400
            
        soft_delete = data.get('soft_delete', True)
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        results = []
        for conv_id in conversation_ids:
            try:
                # Verify ownership
                conversation = ConversationRepository.get_conversation(conv_id)
                if not conversation or conversation.user_id != current_user.id:
                    results.append({
                        "conversation_id": conv_id,
                        "success": False,
                        "error": "Not found or not authorized"
                    })
                    continue
                    
                # Delete conversation
                success = conv_manager.delete_conversation(conv_id, soft_delete=soft_delete)
                results.append({
                    "conversation_id": conv_id,
                    "success": success,
                    "error": None if success else "Failed to delete"
                })
                
            except Exception as e:
                results.append({
                    "conversation_id": conv_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Count successes
        success_count = sum(1 for r in results if r["success"])
        
        return jsonify({
            "success": success_count > 0,
            "results": results,
            "summary": {
                "total": len(conversation_ids),
                "successful": success_count,
                "failed": len(conversation_ids) - success_count
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/analytics/conversations/<int:conversation_id>/usage', methods=['GET'])
@login_required
@check_lynxx_domain
def get_conversation_usage(conversation_id):
    """
    API endpoint to get token usage summary for a conversation.
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        JSON response with usage summary
    """
    try:
        # Verify the conversation belongs to the current user
        conversation = ConversationRepository.get_conversation(conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": "Conversation not found or not authorized"
            }), 404
        
        # Get usage summary
        analytics_repo = AnalyticsRepository()
        usage_summary = analytics_repo.get_usage_summary_by_conversation(conversation_id)
        
        if usage_summary.get('error'):
            return jsonify({
                "success": False,
                "error": usage_summary['error']
            }), 500
        
        return jsonify({
            "success": True,
            **usage_summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/analytics/users/<int:user_id>/usage', methods=['GET'])
@login_required
@check_lynxx_domain
def get_user_usage(user_id):
    """
    API endpoint to get token usage summary for a user.
    
    Args:
        user_id: ID of the user
        
    Query parameters:
        days: Number of days to look back (optional)
        
    Returns:
        JSON response with usage summary
    """
    try:
        # Verify the user is requesting their own data
        if user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": "Not authorized to access this user's data"
            }), 403
        
        days = request.args.get('days')
        if days:
            try:
                days = int(days)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Days must be a valid integer"
                }), 400
        
        # Get usage summary
        analytics_repo = AnalyticsRepository()
        usage_summary = analytics_repo.get_usage_summary_by_user(user_id, days)
        
        if usage_summary.get('error'):
            return jsonify({
                "success": False,
                "error": usage_summary['error']
            }), 500
        
        return jsonify({
            "success": True,
            **usage_summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@api_bp.route('/conversations/<int:conversation_id>/last_message', methods=['GET'])
@login_required
@check_lynxx_domain
def get_last_message(conversation_id):
    """
    API endpoint to retrieve the last message from Claude in a conversation.
    """
    try:
        # Get conversation with messages
        result = ConversationRepository.get_conversation_with_messages(conversation_id)

        if not result or 'messages' not in result:
            return jsonify({"success": False, "error": "No messages found"}), 404

        # Find the last assistant message
        last_message = next(
            (msg for msg in reversed(result["messages"]) if msg["role"] == "assistant"),
            None
        )

        if not last_message:
            return jsonify({"success": False, "error": "No assistant response found"}), 404

        return jsonify({"success": True, "last_message": last_message["content"]})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/prompt', methods=['POST'])
@login_required
@check_lynxx_domain
def send_prompt():
    """
    API endpoint to send a prompt to Claude and get a response.
    
    Request body:
        prompt: Text prompt to send to Claude
        model_id: (Optional) Claude model to use
        conversation_id: (Optional) ID of the conversation to continue
        system_prompt: (Optional) System prompt to control Claude's behavior
        temperature: (Optional) Temperature for response generation (0.0-1.0)
        max_tokens: (Optional) Maximum tokens for response
        preset_name: (Optional) LLM preset name to use
        
    Returns:
        JSON response with Claude's reply and metadata
    """
    try:
        # Get the data from the request
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "Prompt is required"
            }), 400
            
        # Extract parameters from request
        prompt = data.get('prompt')
        model_id = data.get('model_id', 'claude-3-haiku-20240307')  # Default to Haiku
        conversation_id = data.get('conversation_id')
        system_prompt = data.get('system_prompt')
        temperature = data.get('temperature')
        max_tokens = data.get('max_tokens')
        preset_name = data.get('preset_name')
        
        # Validate model_id
        if not _validate_model_id(model_id):
            return jsonify({
                "success": False,
                "error": "Geen geldig model geselecteerd. Wacht tot de modellen zijn geladen."
            }), 400
        
        # Validate temperature if provided
        if temperature is not None:
            try:
                temperature = float(temperature)
                if not 0.0 <= temperature <= 1.0:
                    return jsonify({
                        "success": False,
                        "error": "Temperature must be between 0.0 and 1.0"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "Temperature must be a valid number"
                }), 400
        
        # Validate max_tokens if provided
        if max_tokens is not None:
            try:
                max_tokens = int(max_tokens)
                if max_tokens <= 0:
                    return jsonify({
                        "success": False,
                        "error": "Max tokens must be greater than 0"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "Max tokens must be a valid integer"
                }), 400
        
        # Initialize ConversationManager with database backend for persistence
        conv_manager = ConversationManager(storage_backend=True, user_id=current_user.id)
        
        # Update anthropic_api to use the new conversation manager
        original_conv_manager = anthropic_api.conversation_manager
        anthropic_api.conversation_manager = conv_manager
        
        try:
            # Call the Anthropic API
            response = anthropic_api.send_prompt(
                prompt=prompt,
                model_id=model_id,
                conversation_id=conversation_id,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                preset_name=preset_name
            )
        finally:
            # Restore original conversation manager
            anthropic_api.conversation_manager = original_conv_manager

        active_mcp_servers = response.get("active_mcp_servers", [])
        
        # If conversation_id was provided, store the message in the database
        if conversation_id:
            # First check if the conversation exists and belongs to the user
            conversation = ConversationRepository.get_conversation(conversation_id)
            if conversation and conversation.user_id == current_user.id:
                # Save user message
                ConversationRepository.save_message(
                    conversation_id=conversation_id,
                    message_data={
                        'role': 'user',
                        'content': prompt
                    }
                )
                
                # Save assistant response - Check for both 'content' and 'message' fields
                response_content = response.get('content') or response.get('message')
                if response.get('success', False) and response_content:
                    message_data = {
                        'role': 'assistant',
                        'content': response_content,
                        'metadata': {
                            'model': model_id,
                            'temperature': response.get('temperature'),
                            'max_tokens': response.get('max_tokens'),
                            'preset_name': response.get('preset_name'),
                            'token_count': response.get('token_count', 0)
                        }
                    }
                    
                    # Add thinking content to metadata if available
                    if response.get('thinking'):
                        message_data['metadata']['thinking_content'] = response.get('thinking')
                    
                    ConversationRepository.save_message(
                        conversation_id=conversation_id,
                        message_data=message_data
                    )
                    
                # Save thinking content as separate message if available
                if response.get('thinking'):
                    ConversationRepository.save_message(
                        conversation_id=conversation_id,
                        message_data={
                            'role': 'thinking',
                            'content': response.get('thinking')
                        }
                    )
        # If no conversation_id, create a new conversation if the response was successful
        else:
            # Check for both 'content' and 'message' fields
            response_content = response.get('content') or response.get('message')
            if response.get('success', False) and response_content:
                # Create new conversation
                conversation = ConversationRepository.save_conversation(
                    user_id=current_user.id,
                    conversation_data={
                        'title': prompt[:50] + ('...' if len(prompt) > 50 else ''),
                        'model': model_id
                    }
                )
                
                if conversation:
                    # Save messages
                    ConversationRepository.save_message(
                        conversation_id=conversation.id,
                        message_data={
                            'role': 'user',
                            'content': prompt
                        }
                    )
                    
                    message_data = {
                        'role': 'assistant',
                        'content': response_content,
                        'metadata': {
                            'model': model_id,
                            'temperature': response.get('temperature'),
                            'max_tokens': response.get('max_tokens'),
                            'preset_name': response.get('preset_name'),
                            'token_count': response.get('token_count', 0)
                        }
                    }
                    
                    # Add thinking content to metadata if available
                    if response.get('thinking'):
                        message_data['metadata']['thinking_content'] = response.get('thinking')
                    
                    ConversationRepository.save_message(
                        conversation_id=conversation.id,
                        message_data=message_data
                    )
                    
                    # Save thinking content as separate message if available
                    if response.get('thinking'):
                        ConversationRepository.save_message(
                            conversation_id=conversation.id,
                            message_data={
                                'role': 'thinking',
                                'content': response.get('thinking')
                            }
                        )
                    
                    # Add conversation_id to the response
                    response['conversation_id'] = conversation.id
        
        # Voeg de actieve MCP-servers toe aan de response
        response["active_mcp_servers"] = active_mcp_servers

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/prompt_stream', methods=['GET'])
@login_required
@check_lynxx_domain
def send_prompt_stream():
    """Stream logs, thinking content, and the final response from Claude via Server-Sent Events."""
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    model_id = request.args.get('model_id', 'claude-3-haiku-20240307')
    conversation_id = request.args.get('conversation_id')
    system_prompt = request.args.get('system_prompt')
    temperature = request.args.get('temperature')
    max_tokens = request.args.get('max_tokens')
    preset_name = request.args.get('preset_name')
    
    # Validate model_id
    if not _validate_model_id(model_id):
        return jsonify({
            "success": False,
            "error": "Geen geldig model geselecteerd. Wacht tot de modellen zijn geladen."
        }), 400
    
    # Validate temperature if provided
    if temperature is not None:
        try:
            temperature = float(temperature)
            if not 0.0 <= temperature <= 1.0:
                return jsonify({
                    "success": False,
                    "error": "Temperature must be between 0.0 and 1.0"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Temperature must be a valid number"
            }), 400
    
    # Validate max_tokens if provided
    if max_tokens is not None:
        try:
            max_tokens = int(max_tokens)
            if max_tokens <= 0:
                return jsonify({
                    "success": False,
                    "error": "Max tokens must be greater than 0"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                    "error": "Max tokens must be a valid integer"
                }), 400
    
    # Capture user_id before starting the thread
    user_id = current_user.id if current_user.is_authenticated else None
    app = current_app._get_current_object()  # Get the actual app, not the proxy

    def event_stream():
        q = queue.Queue()

        def callback(msg: str) -> None:
            q.put({'type': 'log', 'data': msg})

        def worker(app, user_id):
            with app.app_context():
                # Initialize ConversationManager with database backend
                conv_manager = ConversationManager(storage_backend=True, user_id=user_id)
                
                # Update anthropic_api to use the new conversation manager
                original_conv_manager = anthropic_api.conversation_manager
                anthropic_api.conversation_manager = conv_manager
                
                try:
                    result = anthropic_api.send_prompt(
                        prompt=prompt,
                        model_id=model_id,
                        conversation_id=conversation_id,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        preset_name=preset_name,
                        log_callback=callback,
                    )
                    
                    # Handle database storage for streaming responses
                    if result.get('success', False):
                        # Save user message if conversation exists
                        if conversation_id:
                            conversation = ConversationRepository.get_conversation(conversation_id)
                            if conversation and conversation.user_id == user_id:
                                # Save user message
                                ConversationRepository.save_message(
                                    conversation_id=conversation_id,
                                    message_data={
                                        'role': 'user',
                                        'content': prompt
                                    }
                                )
                                
                                # Save assistant response
                                response_content = result.get('content') or result.get('message')
                                if response_content:
                                    message_data = {
                                        'role': 'assistant',
                                        'content': response_content,
                                        'metadata': {
                                            'model': model_id,
                                            'temperature': result.get('temperature'),
                                            'max_tokens': result.get('max_tokens'),
                                            'preset_name': result.get('preset_name'),
                                            'token_count': result.get('token_count', 0)
                                        }
                                    }
                                    
                                    # Add thinking content to metadata if available
                                    if result.get('thinking'):
                                        message_data['metadata']['thinking_content'] = result.get('thinking')
                                    
                                    ConversationRepository.save_message(
                                        conversation_id=conversation_id,
                                        message_data=message_data
                                    )
                                    
                                # Save thinking content as separate message if available
                                if result.get('thinking'):
                                    ConversationRepository.save_message(
                                        conversation_id=conversation_id,
                                        message_data={
                                            'role': 'thinking',
                                            'content': result.get('thinking')
                                        }
                                    )
                        
                        # Create new conversation if none exists
                        elif not conversation_id:
                            response_content = result.get('content') or result.get('message')
                            if response_content:
                                conversation = ConversationRepository.save_conversation(
                                    user_id=user_id,
                                    conversation_data={
                                        'title': prompt[:50] + ('...' if len(prompt) > 50 else ''),
                                        'model': model_id
                                    }
                                )
                                
                                if conversation:
                                    # Save user message
                                    ConversationRepository.save_message(
                                        conversation_id=conversation.id,
                                        message_data={
                                            'role': 'user',
                                            'content': prompt
                                        }
                                    )
                                    
                                    # Save assistant response
                                    message_data = {
                                        'role': 'assistant',
                                        'content': response_content,
                                        'metadata': {
                                            'model': model_id,
                                            'temperature': result.get('temperature'),
                                            'max_tokens': result.get('max_tokens'),
                                            'preset_name': result.get('preset_name'),
                                            'token_count': result.get('token_count', 0)
                                        }
                                    }
                                    
                                    # Add thinking content to metadata if available
                                    if result.get('thinking'):
                                        message_data['metadata']['thinking_content'] = result.get('thinking')
                                    
                                    ConversationRepository.save_message(
                                        conversation_id=conversation.id,
                                        message_data=message_data
                                    )
                                    
                                    # Save thinking content as separate message if available
                                    if result.get('thinking'):
                                        ConversationRepository.save_message(
                                            conversation_id=conversation.id,
                                            message_data={
                                                'role': 'thinking',
                                                'content': result.get('thinking')
                                            }
                                        )
                                    
                                    # Add conversation_id to result
                                    result['conversation_id'] = conversation.id
                                    result['title'] = conversation.title
                    
                finally:
                    # Restore original conversation manager
                    anthropic_api.conversation_manager = original_conv_manager
                    
                q.put({'type': 'final', 'data': result})

        threading.Thread(target=worker, args=(app, user_id)).start()

        while True:
            item = q.get()
            if item['type'] == 'log':
                yield f"event: log\ndata: {json.dumps(item['data'])}\n\n"
            elif item['type'] == 'thinking':
                yield f"event: thinking\ndata: {json.dumps(item['data'])}\n\n"
            elif item['type'] == 'final':
                # Send thinking event if thinking content is available
                thinking_content = item['data'].get('thinking')
                if thinking_content:
                    current_app.logger.debug(f"Sending thinking event with content length: {len(thinking_content)}")
                    yield f"event: thinking\ndata: {json.dumps(thinking_content)}\n\n"
                else:
                    current_app.logger.debug("No thinking content found in final result")
                
                yield f"event: final\ndata: {json.dumps(item['data'])}\n\n"
                break

    return Response(event_stream(), mimetype='text/event-stream')