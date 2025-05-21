from flask import Blueprint, jsonify, request, Response
import json
import queue
import threading
from flask_login import login_required, current_user
from anthropic_api import anthropic_api
from auth import check_lynxx_domain
from repositories.conversation_repository import ConversationRepository
from models.conversation import Conversation, Message

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

@api_bp.route('/conversations', methods=['GET'])
@login_required
@check_lynxx_domain
def list_conversations():
    """
    API endpoint to retrieve a user's conversations.
    
    Returns:
        JSON response with list of conversations
    """
    try:
        # Get conversations for the current user
        conversations = ConversationRepository.get_conversations(current_user.id)
        
        # Convert to dictionaries
        conversation_data = [conversation.to_dict() for conversation in conversations]
        
        return jsonify({
            "success": True,
            "conversations": conversation_data
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
        
        # Create new conversation in database
        conversation = ConversationRepository.save_conversation(
            user_id=current_user.id,
            conversation_data=data
        )
        
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
            
        # Update the conversation
        data = request.get_json() or {}
        updated = ConversationRepository.update_conversation(conversation_id, data)
        
        if updated is None:
            return jsonify({
                "success": False,
                "error": "Failed to update conversation"
            }), 500
            
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
            
        # Hard delete by default, can be changed to soft delete if specified
        hard_delete = request.args.get('hard_delete', 'true').lower() == 'true'
        
        if hard_delete:
            success = ConversationRepository.hard_delete_conversation(conversation_id)
        else:
            success = ConversationRepository.delete_conversation(conversation_id)
            
        if not success:
            return jsonify({
                "success": False,
                "error": "Failed to delete conversation"
            }), 500
            
        return jsonify({
            "success": True,
            "message": "Conversation deleted successfully"
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
        
        # Call the Anthropic API
        response = anthropic_api.send_prompt(
            prompt=prompt,
            model_id=model_id,
            conversation_id=conversation_id,
            system_prompt=system_prompt
        )

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
                    ConversationRepository.save_message(
                        conversation_id=conversation_id,
                        message_data={
                            'role': 'assistant',
                            'content': response_content,
                            'metadata': {
                                'model': model_id,
                                'token_count': response.get('token_count', 0)
                            }
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
                    
                    ConversationRepository.save_message(
                        conversation_id=conversation.id,
                        message_data={
                            'role': 'assistant',
                            'content': response_content,
                            'metadata': {
                                'model': model_id,
                                'token_count': response.get('token_count', 0)
                            }
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
    """Stream logs and the final response from Claude via Server-Sent Events."""
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    model_id = request.args.get('model_id', 'claude-3-haiku-20240307')
    conversation_id = request.args.get('conversation_id')
    system_prompt = request.args.get('system_prompt')

    def event_stream():
        q = queue.Queue()

        def callback(msg: str) -> None:
            q.put({'type': 'log', 'data': msg})

        def worker():
            result = anthropic_api.send_prompt(
                prompt=prompt,
                model_id=model_id,
                conversation_id=conversation_id,
                system_prompt=system_prompt,
                log_callback=callback,
            )
            q.put({'type': 'final', 'data': result})

        threading.Thread(target=worker).start()

        while True:
            item = q.get()
            if item['type'] == 'log':
                yield f"event: log\ndata: {json.dumps(item['data'])}\n\n"
            elif item['type'] == 'final':
                yield f"event: final\ndata: {json.dumps(item['data'])}\n\n"
                break

    return Response(event_stream(), mimetype='text/event-stream')
