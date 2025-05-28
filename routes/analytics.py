"""
Analytics API routes for token usage and cost data.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from analytics.analytics_service import AnalyticsService
from analytics.token_tracker import TokenTracker
from analytics.cost_calculator import CostCalculator
from repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Initialize services
analytics_service = AnalyticsService()
token_tracker = TokenTracker()
cost_calculator = CostCalculator()
analytics_repository = AnalyticsRepository()


@analytics_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Get comprehensive analytics dashboard data."""
    try:
        days = request.args.get('days', 30, type=int)
        user_id = current_user.id
        
        dashboard_data = analytics_service.get_dashboard_data(user_id, days)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/token-usage', methods=['GET'])
@login_required
def get_token_usage():
    """Get token usage data for the current user."""
    try:
        days = request.args.get('days', 30, type=int)
        conversation_id = request.args.get('conversation_id', type=int)
        user_id = current_user.id
        
        if conversation_id:
            # Get usage for specific conversation
            usage_data = analytics_service.get_conversation_analytics(conversation_id)
        else:
            # Get usage summary for user
            usage_data = analytics_repository.get_usage_summary_by_user(user_id, days)
            usage_data['daily_trends'] = analytics_repository.get_daily_usage_trends(user_id, days)
        
        return jsonify({
            'success': True,
            'data': usage_data
        })
    except Exception as e:
        logger.error(f"Error getting token usage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/costs', methods=['GET'])
@login_required
def get_costs():
    """Get cost analysis data."""
    try:
        days = request.args.get('days', 30, type=int)
        user_id = current_user.id
        
        cost_data = analytics_service.get_cost_analysis(user_id, days)
        
        return jsonify({
            'success': True,
            'data': cost_data
        })
    except Exception as e:
        logger.error(f"Error getting cost data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/trends', methods=['GET'])
@login_required
def get_trends():
    """Get usage trends and patterns."""
    try:
        days = request.args.get('days', 30, type=int)
        user_id = current_user.id
        
        trends_data = analytics_service.get_usage_patterns(user_id, days)
        
        return jsonify({
            'success': True,
            'data': trends_data
        })
    except Exception as e:
        logger.error(f"Error getting trends data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/models', methods=['GET'])
@login_required
def get_model_analytics():
    """Get model usage and comparison data."""
    try:
        days = request.args.get('days', 30, type=int)
        user_id = current_user.id
        
        model_data = analytics_service.get_model_comparison(user_id, days)
        
        return jsonify({
            'success': True,
            'data': model_data
        })
    except Exception as e:
        logger.error(f"Error getting model analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/conversations/top', methods=['GET'])
@login_required
def get_top_conversations():
    """Get top conversations by usage."""
    try:
        limit = request.args.get('limit', 10, type=int)
        days = request.args.get('days', 30, type=int)
        user_id = current_user.id
        
        top_conversations = analytics_repository.get_top_conversations_by_usage(
            user_id, limit, days
        )
        
        return jsonify({
            'success': True,
            'data': {
                'conversations': top_conversations,
                'period_days': days,
                'limit': limit
            }
        })
    except Exception as e:
        logger.error(f"Error getting top conversations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_conversation_analytics(conversation_id):
    """Get detailed analytics for a specific conversation."""
    try:
        analytics_data = analytics_service.get_conversation_analytics(conversation_id)
        
        return jsonify({
            'success': True,
            'data': analytics_data
        })
    except Exception as e:
        logger.error(f"Error getting conversation analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/estimate-cost', methods=['POST'])
@login_required
def estimate_cost():
    """Estimate cost for a request."""
    try:
        data = request.get_json()
        
        if not data or 'model_name' not in data or 'estimated_input_tokens' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: model_name, estimated_input_tokens'
            }), 400
        
        model_name = data['model_name']
        estimated_input_tokens = data['estimated_input_tokens']
        estimated_output_tokens = data.get('estimated_output_tokens')
        
        cost_estimate = token_tracker.get_cost_estimate(
            model_name, estimated_input_tokens, estimated_output_tokens
        )
        
        return jsonify({
            'success': True,
            'data': {
                'model_name': model_name,
                'estimated_input_tokens': estimated_input_tokens,
                'estimated_output_tokens': estimated_output_tokens,
                'cost_estimate': cost_estimate
            }
        })
    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/pricing', methods=['GET'])
@login_required
def get_pricing_info():
    """Get pricing information for all models."""
    try:
        model_name = request.args.get('model_name')
        
        if model_name:
            pricing = cost_calculator.get_model_pricing(model_name)
            if not pricing:
                return jsonify({
                    'success': False,
                    'error': f'No pricing information found for model: {model_name}'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'model_name': model_name,
                    'pricing': pricing
                }
            })
        else:
            all_pricing = cost_calculator.get_all_model_pricing()
            return jsonify({
                'success': True,
                'data': {
                    'pricing': all_pricing
                }
            })
    except Exception as e:
        logger.error(f"Error getting pricing info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/export', methods=['GET'])
@login_required
def export_analytics_data():
    """Export analytics data for the current user."""
    try:
        days = request.args.get('days', 30, type=int)
        format_type = request.args.get('format', 'json')
        user_id = current_user.id
        
        if format_type not in ['json', 'csv']:
            return jsonify({
                'success': False,
                'error': 'Unsupported format. Use json or csv.'
            }), 400
        
        # Get comprehensive data
        dashboard_data = analytics_service.get_dashboard_data(user_id, days)
        
        if format_type == 'json':
            return jsonify({
                'success': True,
                'data': dashboard_data,
                'export_format': 'json',
                'exported_at': dashboard_data.get('generated_at')
            })
        
        # CSV export would require additional formatting
        # For now, return JSON with a note about CSV
        return jsonify({
            'success': False,
            'error': 'CSV export not yet implemented. Use format=json.'
        }), 501
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_old_data():
    """Clean up old analytics data (admin function)."""
    try:
        # This could be restricted to admin users
        data = request.get_json()
        days_to_keep = data.get('days_to_keep', 90) if data else 90
        
        deleted_count = analytics_repository.delete_old_usage_records(days_to_keep)
        
        return jsonify({
            'success': True,
            'data': {
                'deleted_records': deleted_count,
                'days_kept': days_to_keep
            }
        })
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for analytics service."""
    try:
        # Basic health check
        return jsonify({
            'success': True,
            'service': 'analytics',
            'status': 'healthy',
            'timestamp': analytics_service.analytics_repository.analytics_repository if hasattr(analytics_service, 'analytics_repository') else 'unknown'
        })
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return jsonify({
            'success': False,
            'service': 'analytics',
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# Error handlers
@analytics_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Analytics endpoint not found'
    }), 404


@analytics_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal analytics service error'
    }), 500