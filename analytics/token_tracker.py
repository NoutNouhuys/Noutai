"""
Token tracker for monitoring and recording token usage.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta

from models.token_usage import TokenUsage
from analytics.cost_calculator import CostCalculator
from database import db

logger = logging.getLogger(__name__)


class TokenTracker:
    """Tracks token usage and calculates costs for AI model interactions."""
    
    def __init__(self, cost_calculator: Optional[CostCalculator] = None):
        """
        Initialize token tracker.
        
        Args:
            cost_calculator: Optional custom cost calculator
        """
        self.cost_calculator = cost_calculator or CostCalculator()
    
    def record_usage(self, conversation_id: int, model_name: str, 
                    usage_data: Dict[str, Any], message_id: Optional[int] = None,
                    request_metadata: Optional[Dict[str, Any]] = None) -> TokenUsage:
        """
        Record token usage for a conversation/message.
        
        Args:
            conversation_id: ID of the conversation
            model_name: Name of the model used
            usage_data: Token usage data from API response
            message_id: Optional message ID
            request_metadata: Optional metadata about the request
            
        Returns:
            Created TokenUsage record
        """
        try:
            # Extract token counts from usage data
            input_tokens = usage_data.get('input_tokens', 0)
            output_tokens = usage_data.get('output_tokens', 0)
            cache_creation_tokens = usage_data.get('cache_creation_input_tokens', 0)
            cache_read_tokens = usage_data.get('cache_read_input_tokens', 0)
            
            # Extract metadata
            metadata = request_metadata or {}
            model_version = metadata.get('model_version')
            request_type = metadata.get('request_type', 'chat')
            temperature = metadata.get('temperature')
            max_tokens = metadata.get('max_tokens')
            preset_used = metadata.get('preset_used')
            
            # Create token usage record
            token_usage = TokenUsage(
                conversation_id=conversation_id,
                message_id=message_id,
                model_name=model_name,
                model_version=model_version,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_creation_input_tokens=cache_creation_tokens,
                cache_read_input_tokens=cache_read_tokens,
                request_type=request_type,
                temperature=temperature,
                max_tokens=max_tokens,
                preset_used=preset_used
            )
            
            # Calculate costs
            cost_data = self.cost_calculator.calculate_cost(
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_creation_tokens=cache_creation_tokens,
                cache_read_tokens=cache_read_tokens
            )
            
            # Set cost data
            token_usage.input_cost = cost_data.get('input_cost', 0.0)
            token_usage.output_cost = cost_data.get('output_cost', 0.0)
            token_usage.total_cost = cost_data.get('total_cost', 0.0)
            
            # Save to database
            db.session.add(token_usage)
            db.session.commit()
            
            logger.info(f"Recorded token usage: {token_usage.total_tokens} tokens, "
                       f"${token_usage.total_cost:.6f} for conversation {conversation_id}")
            
            return token_usage
            
        except Exception as e:
            logger.error(f"Error recording token usage: {e}")
            db.session.rollback()
            raise
    
    def get_conversation_usage(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get token usage summary for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Usage summary dictionary
        """
        try:
            usage_records = TokenUsage.query.filter_by(conversation_id=conversation_id).all()
            
            if not usage_records:
                return {
                    'conversation_id': conversation_id,
                    'total_tokens': 0,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'total_cost': 0.0,
                    'message_count': 0,
                    'models_used': [],
                    'records': []
                }
            
            # Calculate totals
            total_tokens = sum(r.total_tokens for r in usage_records)
            total_input_tokens = sum(r.input_tokens + r.cache_creation_input_tokens + r.cache_read_input_tokens for r in usage_records)
            total_output_tokens = sum(r.output_tokens for r in usage_records)
            total_cost = sum(r.total_cost or 0.0 for r in usage_records)
            
            # Get unique models used
            models_used = list(set(r.model_name for r in usage_records))
            
            return {
                'conversation_id': conversation_id,
                'total_tokens': total_tokens,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_cost': round(total_cost, 6),
                'message_count': len(usage_records),
                'models_used': models_used,
                'records': [r.to_dict() for r in usage_records]
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation usage: {e}")
            return {'error': str(e)}
    
    def get_usage_trends(self, days: int = 30, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get token usage trends over time.
        
        Args:
            days: Number of days to look back
            user_id: Optional user ID to filter by
            
        Returns:
            Trends data dictionary
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Base query
            query = TokenUsage.query.filter(TokenUsage.created_at >= start_date)
            
            # Filter by user if provided (through conversation relationship)
            if user_id:
                from models.conversation import Conversation
                query = query.join(Conversation).filter(Conversation.user_id == user_id)
            
            usage_records = query.all()
            
            if not usage_records:
                return {
                    'period_days': days,
                    'total_records': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'daily_usage': [],
                    'model_breakdown': {},
                    'cost_breakdown': {}
                }
            
            # Group by date
            daily_usage = {}
            model_breakdown = {}
            
            for record in usage_records:
                date_key = record.created_at.date().isoformat()
                
                # Daily usage
                if date_key not in daily_usage:
                    daily_usage[date_key] = {
                        'date': date_key,
                        'tokens': 0,
                        'cost': 0.0,
                        'requests': 0
                    }
                
                daily_usage[date_key]['tokens'] += record.total_tokens
                daily_usage[date_key]['cost'] += record.total_cost or 0.0
                daily_usage[date_key]['requests'] += 1
                
                # Model breakdown
                if record.model_name not in model_breakdown:
                    model_breakdown[record.model_name] = {
                        'tokens': 0,
                        'cost': 0.0,
                        'requests': 0
                    }
                
                model_breakdown[record.model_name]['tokens'] += record.total_tokens
                model_breakdown[record.model_name]['cost'] += record.total_cost or 0.0
                model_breakdown[record.model_name]['requests'] += 1
            
            # Sort daily usage by date
            daily_usage_list = sorted(daily_usage.values(), key=lambda x: x['date'])
            
            # Round costs
            for day in daily_usage_list:
                day['cost'] = round(day['cost'], 6)
            
            for model_data in model_breakdown.values():
                model_data['cost'] = round(model_data['cost'], 6)
            
            total_tokens = sum(r.total_tokens for r in usage_records)
            total_cost = sum(r.total_cost or 0.0 for r in usage_records)
            
            return {
                'period_days': days,
                'total_records': len(usage_records),
                'total_tokens': total_tokens,
                'total_cost': round(total_cost, 6),
                'daily_usage': daily_usage_list,
                'model_breakdown': model_breakdown,
                'cost_breakdown': model_breakdown  # Same as model breakdown for now
            }
            
        except Exception as e:
            logger.error(f"Error getting usage trends: {e}")
            return {'error': str(e)}
    
    def get_cost_estimate(self, model_name: str, estimated_input_tokens: int,
                         estimated_output_tokens: int = None) -> Dict[str, float]:
        """
        Get cost estimate for a request.
        
        Args:
            model_name: Name of the model
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens (optional)
            
        Returns:
            Cost estimate dictionary
        """
        # Use a reasonable default for output tokens if not provided
        if estimated_output_tokens is None:
            estimated_output_tokens = min(estimated_input_tokens // 2, 1000)
        
        return self.cost_calculator.estimate_cost(
            model_name=model_name,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens
        )
    
    def get_model_usage_stats(self, model_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get usage statistics for a specific model.
        
        Args:
            model_name: Name of the model
            days: Number of days to look back
            
        Returns:
            Model usage statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            usage_records = TokenUsage.query.filter(
                TokenUsage.model_name == model_name,
                TokenUsage.created_at >= start_date
            ).all()
            
            if not usage_records:
                return {
                    'model_name': model_name,
                    'period_days': days,
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'average_tokens_per_request': 0,
                    'average_cost_per_request': 0.0
                }
            
            total_tokens = sum(r.total_tokens for r in usage_records)
            total_cost = sum(r.total_cost or 0.0 for r in usage_records)
            total_requests = len(usage_records)
            
            return {
                'model_name': model_name,
                'period_days': days,
                'total_requests': total_requests,
                'total_tokens': total_tokens,
                'total_cost': round(total_cost, 6),
                'average_tokens_per_request': round(total_tokens / total_requests, 2),
                'average_cost_per_request': round(total_cost / total_requests, 6)
            }
            
        except Exception as e:
            logger.error(f"Error getting model usage stats: {e}")
            return {'error': str(e)}
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old token usage records.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = TokenUsage.query.filter(
                TokenUsage.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old token usage records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            db.session.rollback()
            return 0