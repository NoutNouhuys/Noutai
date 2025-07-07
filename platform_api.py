"""
Platform API module for managing GitHub and Bitbucket integrations.
Provides endpoints for platform configuration, connection management, and status.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required
import logging
from anthropic_config import AnthropicConfig
from mcp_integration import MCPIntegration

logger = logging.getLogger(__name__)

# Create blueprint
platform_api = Blueprint('platform_api', __name__, url_prefix='/api/platform')

# Global MCP integration instance
mcp_integration = None

def init_platform_api(app):
    """Initialize platform API with app context."""
    global mcp_integration
    
    with app.app_context():
        config = AnthropicConfig()
        mcp_integration = MCPIntegration(config)
    
    app.register_blueprint(platform_api)


@platform_api.route('/config', methods=['GET'])
@login_required
def get_platform_config():
    """Get platform configuration and available platforms."""
    try:
        config = AnthropicConfig()
        
        platforms = config.get_available_platforms()
        default_platform = config.default_platform
        
        return jsonify({
            'success': True,
            'default_platform': default_platform,
            'available_platforms': [p['id'] for p in platforms],
            'platforms': platforms
        })
        
    except Exception as e:
        logger.error(f"Error getting platform config: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_api.route('/status', methods=['GET'])
@login_required
def get_platform_status():
    """Get current platform connection status."""
    try:
        if not mcp_integration:
            return jsonify({
                'success': True,
                'connected': False,
                'active_platform': None,
                'connected_platforms': []
            })
        
        connected_platforms = mcp_integration.connected_platforms
        active_platform = mcp_integration.active_platform
        is_connected = mcp_integration.is_connected
        
        # Get active MCP servers info
        active_servers = []
        if is_connected:
            if mcp_integration.config.PLATFORM_GITHUB in connected_platforms:
                active_servers.append('GitHub MCP')
            if mcp_integration.config.PLATFORM_BITBUCKET in connected_platforms:
                active_servers.append('Bitbucket API')
        
        return jsonify({
            'success': True,
            'connected': is_connected,
            'active_platform': active_platform,
            'connected_platforms': connected_platforms,
            'active_mcp_servers': active_servers
        })
        
    except Exception as e:
        logger.error(f"Error getting platform status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_api.route('/connect', methods=['POST'])
@login_required
def connect_platform():
    """Connect to a specific platform."""
    try:
        data = request.get_json()
        platform = data.get('platform')
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Platform parameter is required'
            }), 400
        
        config = AnthropicConfig()
        if not config.is_platform_supported(platform):
            return jsonify({
                'success': False,
                'error': f'Unsupported platform: {platform}'
            }), 400
        
        # Initialize MCP integration if not already done
        global mcp_integration
        if not mcp_integration:
            mcp_integration = MCPIntegration(config)
        
        # Attempt to connect to the platform
        success = await mcp_integration.connect(platform=platform)
        
        if success:
            # Store active platform in session
            session['active_platform'] = platform
            
            # Get active servers info
            active_servers = []
            connected_platforms = mcp_integration.connected_platforms
            if config.PLATFORM_GITHUB in connected_platforms:
                active_servers.append('GitHub MCP')
            if config.PLATFORM_BITBUCKET in connected_platforms:
                active_servers.append('Bitbucket API')
            
            return jsonify({
                'success': True,
                'platform': platform,
                'connected_platforms': connected_platforms,
                'active_mcp_servers': active_servers
            })
        else:
            # Determine specific error message based on platform
            if platform == config.PLATFORM_GITHUB:
                if not config.is_github_configured():
                    error_msg = 'GitHub MCP server not configured. Check MCP_SERVER_SCRIPT environment variable.'
                else:
                    error_msg = 'Failed to connect to GitHub MCP server. Check server configuration and availability.'
            elif platform == config.PLATFORM_BITBUCKET:
                if not config.is_bitbucket_configured():
                    error_msg = 'Bitbucket API not configured. Check BITBUCKET_WORKSPACE, BITBUCKET_USERNAME, and BITBUCKET_APP_PASSWORD environment variables.'
                else:
                    error_msg = 'Failed to connect to Bitbucket API. Check credentials and network connectivity.'
            else:
                error_msg = f'Failed to connect to {platform}'
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
    except Exception as e:
        logger.error(f"Error connecting to platform {platform}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_api.route('/disconnect', methods=['POST'])
@login_required
def disconnect_platform():
    """Disconnect from a specific platform or all platforms."""
    try:
        data = request.get_json()
        platform = data.get('platform')  # Optional - if not provided, disconnect all
        
        if not mcp_integration:
            return jsonify({
                'success': True,
                'message': 'No platforms connected'
            })
        
        if platform:
            # Disconnect specific platform (not directly supported by current MCPIntegration)
            # For now, we'll disconnect all and reconnect to others
            config = AnthropicConfig()
            if not config.is_platform_supported(platform):
                return jsonify({
                    'success': False,
                    'error': f'Unsupported platform: {platform}'
                }), 400
            
            # Get currently connected platforms
            connected_platforms = mcp_integration.connected_platforms.copy()
            
            # Disconnect all
            await mcp_integration.disconnect()
            
            # Reconnect to other platforms
            for other_platform in connected_platforms:
                if other_platform != platform:
                    await mcp_integration.connect(platform=other_platform)
            
            # Update session
            if session.get('active_platform') == platform:
                remaining_platforms = mcp_integration.connected_platforms
                session['active_platform'] = remaining_platforms[0] if remaining_platforms else None
        else:
            # Disconnect all platforms
            await mcp_integration.disconnect()
            session.pop('active_platform', None)
        
        return jsonify({
            'success': True,
            'connected_platforms': mcp_integration.connected_platforms if mcp_integration else [],
            'active_platform': mcp_integration.active_platform if mcp_integration else None
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting from platform: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_api.route('/switch', methods=['POST'])
@login_required
def switch_platform():
    """Switch active platform without disconnecting."""
    try:
        data = request.get_json()
        platform = data.get('platform')
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Platform parameter is required'
            }), 400
        
        if not mcp_integration:
            return jsonify({
                'success': False,
                'error': 'No MCP integration available'
            }), 500
        
        # Check if platform is connected
        if platform not in mcp_integration.connected_platforms:
            return jsonify({
                'success': False,
                'error': f'Platform {platform} is not connected'
            }), 400
        
        # Set as active platform
        success = mcp_integration.set_active_platform(platform)
        
        if success:
            session['active_platform'] = platform
            return jsonify({
                'success': True,
                'active_platform': platform,
                'connected_platforms': mcp_integration.connected_platforms
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to set {platform} as active platform'
            }), 500
        
    except Exception as e:
        logger.error(f"Error switching to platform {platform}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_api.route('/tools', methods=['GET'])
@login_required
def get_platform_tools():
    """Get available tools for a specific platform or all connected platforms."""
    try:
        platform = request.args.get('platform')
        
        if not mcp_integration:
            return jsonify({
                'success': True,
                'tools': [],
                'platforms': []
            })
        
        tools = await mcp_integration.get_tools(platform=platform)
        
        return jsonify({
            'success': True,
            'tools': tools,
            'platform': platform,
            'connected_platforms': mcp_integration.connected_platforms
        })
        
    except Exception as e:
        logger.error(f"Error getting platform tools: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_api.route('/validate', methods=['POST'])
@login_required
def validate_platform_config():
    """Validate platform configuration without connecting."""
    try:
        data = request.get_json()
        platform = data.get('platform')
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Platform parameter is required'
            }), 400
        
        config = AnthropicConfig()
        
        if not config.is_platform_supported(platform):
            return jsonify({
                'success': False,
                'error': f'Unsupported platform: {platform}',
                'valid': False
            })
        
        # Check platform-specific configuration
        if platform == config.PLATFORM_GITHUB:
            valid = config.is_github_configured()
            missing_config = []
            if not config.mcp_server_script:
                missing_config.append('MCP_SERVER_SCRIPT')
            
            return jsonify({
                'success': True,
                'platform': platform,
                'valid': valid,
                'missing_config': missing_config,
                'config_info': {
                    'mcp_server_script': bool(config.mcp_server_script),
                    'mcp_server_venv_path': bool(config.mcp_server_venv_path)
                }
            })
            
        elif platform == config.PLATFORM_BITBUCKET:
            valid = config.is_bitbucket_configured()
            missing_config = []
            if not config.bitbucket_workspace:
                missing_config.append('BITBUCKET_WORKSPACE')
            if not config.bitbucket_username:
                missing_config.append('BITBUCKET_USERNAME')
            if not config.bitbucket_app_password:
                missing_config.append('BITBUCKET_APP_PASSWORD')
            
            return jsonify({
                'success': True,
                'platform': platform,
                'valid': valid,
                'missing_config': missing_config,
                'config_info': {
                    'workspace': config.bitbucket_workspace,
                    'username': config.bitbucket_username,
                    'has_app_password': bool(config.bitbucket_app_password)
                }
            })
        
        return jsonify({
            'success': False,
            'error': f'Unknown platform: {platform}',
            'valid': False
        })
        
    except Exception as e:
        logger.error(f"Error validating platform config: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_mcp_integration():
    """Get the global MCP integration instance."""
    return mcp_integration