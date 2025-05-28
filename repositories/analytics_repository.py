"""
Repository for analytics and token usage data access.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import joinedload

from models.token_usage import TokenUsage
from models.conversation import Conversation, Message
from database import db

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository for analytics and token usage data operations."""
    
    def get_token_usage_by_conversation(self, conversation_id: int) -> List[TokenUsage]:
        """
        Get all token usage records for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of TokenUsage records
        """
        try:
            return TokenUsage.query.filter_by(conversation_id=conversation_id).order_by(
                TokenUsage.created_at.asc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting token usage by conversation: {e}")
            return []
    
    def get_token_usage_by_user(self, user_id: int, limit: Optional[int] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[TokenUsage]:
        """
        Get token usage records for a user.
        
        Args:
            user_id: ID of the user
            limit: Optional limit on number of records
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of TokenUsage records
        """
        try:
            query = db.session.query(TokenUsage).join(
                Conversation, TokenUsage.conversation_id == Conversation.id
            ).filter(Conversation.user_id == user_id)
            
            if start_date:
                query = query.filter(TokenUsage.created_at >= start_date)
            if end_date:
                query = query.filter(TokenUsage.created_at <= end_date)
            
            query = query.order_by(TokenUsage.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting token usage by user: {e}")
            return []
    
    def get_usage_summary_by_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get usage summary for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Usage summary dictionary
        """
        try:
            result = db.session.query(
                func.sum(TokenUsage.input_tokens).label('total_input_tokens'),
                func.sum(TokenUsage.output_tokens).label('total_output_tokens'),
                func.sum(TokenUsage.total_tokens).label('total_tokens'),
                func.sum(TokenUsage.total_cost).label('total_cost'),
                func.count(TokenUsage.id).label('request_count'),
                func.max(TokenUsage.created_at).label('last_usage')
            ).filter_by(conversation_id=conversation_id).first()
            
            if not result or result.total_tokens is None:
                return {
                    'conversation_id': conversation_id,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'request_count': 0,
                    'last_usage': None
                }
            
            return {
                'conversation_id': conversation_id,
                'total_input_tokens': int(result.total_input_tokens or 0),
                'total_output_tokens': int(result.total_output_tokens or 0),
                'total_tokens': int(result.total_tokens or 0),
                'total_cost': float(result.total_cost or 0.0),
                'request_count': int(result.request_count or 0),
                'last_usage': result.last_usage
            }
        except Exception as e:
            logger.error(f"Error getting usage summary by conversation: {e}")
            return {'error': str(e)}
    
    def get_usage_summary_by_user(self, user_id: int, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get usage summary for a user.
        
        Args:
            user_id: ID of the user
            days: Optional number of days to look back
            
        Returns:
            Usage summary dictionary
        """
        try:
            query = db.session.query(
                func.sum(TokenUsage.input_tokens).label('total_input_tokens'),
                func.sum(TokenUsage.output_tokens).label('total_output_tokens'),
                func.sum(TokenUsage.total_tokens).label('total_tokens'),
                func.sum(TokenUsage.total_cost).label('total_cost'),
                func.count(TokenUsage.id).label('request_count'),
                func.count(func.distinct(TokenUsage.conversation_id)).label('conversation_count')
            ).join(
                Conversation, TokenUsage.conversation_id == Conversation.id
            ).filter(Conversation.user_id == user_id)
            
            if days:
                start_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(TokenUsage.created_at >= start_date)
            
            result = query.first()
            
            if not result or result.total_tokens is None:
                return {
                    'user_id': user_id,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'request_count': 0,
                    'conversation_count': 0,
                    'period_days': days
                }
            
            return {
                'user_id': user_id,
                'total_input_tokens': int(result.total_input_tokens or 0),
                'total_output_tokens': int(result.total_output_tokens or 0),
                'total_tokens': int(result.total_tokens or 0),
                'total_cost': float(result.total_cost or 0.0),
                'request_count': int(result.request_count or 0),
                'conversation_count': int(result.conversation_count or 0),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting usage summary by user: {e}")
            return {'error': str(e)}
    
    def get_daily_usage_trends(self, user_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily usage trends.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            List of daily usage data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.session.query(
                func.date(TokenUsage.created_at).label('date'),
                func.sum(TokenUsage.total_tokens).label('total_tokens'),
                func.sum(TokenUsage.total_cost).label('total_cost'),
                func.count(TokenUsage.id).label('request_count')
            )
            
            if user_id:
                query = query.join(
                    Conversation, TokenUsage.conversation_id == Conversation.id
                ).filter(Conversation.user_id == user_id)
            
            query = query.filter(TokenUsage.created_at >= start_date).group_by(
                func.date(TokenUsage.created_at)
            ).order_by(func.date(TokenUsage.created_at).asc())
            
            results = query.all()
            
            return [
                {
                    'date': result.date.isoformat(),
                    'total_tokens': int(result.total_tokens or 0),
                    'total_cost': float(result.total_cost or 0.0),
                    'request_count': int(result.request_count or 0)
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error getting daily usage trends: {e}")
            return []
    
    def get_model_usage_breakdown(self, user_id: Optional[int] = None, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get usage breakdown by model.
        
        Args:
            user_id: Optional user ID to filter by
            days: Optional number of days to look back
            
        Returns:
            List of model usage data
        """
        try:
            query = db.session.query(
                TokenUsage.model_name,
                func.sum(TokenUsage.total_tokens).label('total_tokens'),
                func.sum(TokenUsage.total_cost).label('total_cost'),
                func.count(TokenUsage.id).label('request_count'),
                func.avg(TokenUsage.total_tokens).label('avg_tokens_per_request')
            )
            
            if user_id:
                query = query.join(
                    Conversation, TokenUsage.conversation_id == Conversation.id
                ).filter(Conversation.user_id == user_id)
            
            if days:
                start_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(TokenUsage.created_at >= start_date)
            
            query = query.group_by(TokenUsage.model_name).order_by(
                func.sum(TokenUsage.total_tokens).desc()
            )
            
            results = query.all()
            
            return [
                {
                    'model_name': result.model_name,
                    'total_tokens': int(result.total_tokens or 0),
                    'total_cost': float(result.total_cost or 0.0),
                    'request_count': int(result.request_count or 0),
                    'avg_tokens_per_request': float(result.avg_tokens_per_request or 0.0)
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error getting model usage breakdown: {e}")
            return []
    
    def get_top_conversations_by_usage(self, user_id: Optional[int] = None, 
                                     limit: int = 10, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get top conversations by token usage.
        
        Args:
            user_id: Optional user ID to filter by
            limit: Number of conversations to return
            days: Optional number of days to look back
            
        Returns:
            List of conversation usage data
        """
        try:
            query = db.session.query(
                TokenUsage.conversation_id,
                Conversation.title,
                func.sum(TokenUsage.total_tokens).label('total_tokens'),
                func.sum(TokenUsage.total_cost).label('total_cost'),
                func.count(TokenUsage.id).label('request_count'),
                func.max(TokenUsage.created_at).label('last_usage')
            ).join(
                Conversation, TokenUsage.conversation_id == Conversation.id
            )
            
            if user_id:
                query = query.filter(Conversation.user_id == user_id)
            
            if days:
                start_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(TokenUsage.created_at >= start_date)
            
            query = query.group_by(
                TokenUsage.conversation_id, Conversation.title
            ).order_by(
                func.sum(TokenUsage.total_tokens).desc()
            ).limit(limit)
            
            results = query.all()
            
            return [
                {
                    'conversation_id': result.conversation_id,
                    'title': result.title,
                    'total_tokens': int(result.total_tokens or 0),
                    'total_cost': float(result.total_cost or 0.0),
                    'request_count': int(result.request_count or 0),
                    'last_usage': result.last_usage.isoformat() if result.last_usage else None
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error getting top conversations by usage: {e}")
            return []
    
    def get_usage_by_preset(self, user_id: Optional[int] = None, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get usage breakdown by preset.
        
        Args:
            user_id: Optional user ID to filter by
            days: Optional number of days to look back
            
        Returns:
            List of preset usage data
        """
        try:
            query = db.session.query(
                TokenUsage.preset_used,
                func.sum(TokenUsage.total_tokens).label('total_tokens'),
                func.sum(TokenUsage.total_cost).label('total_cost'),
                func.count(TokenUsage.id).label('request_count')
            )
            
            if user_id:
                query = query.join(
                    Conversation, TokenUsage.conversation_id == Conversation.id
                ).filter(Conversation.user_id == user_id)
            
            if days:
                start_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(TokenUsage.created_at >= start_date)
            
            query = query.filter(TokenUsage.preset_used.isnot(None)).group_by(
                TokenUsage.preset_used
            ).order_by(func.sum(TokenUsage.total_tokens).desc())
            
            results = query.all()
            
            return [
                {
                    'preset_name': result.preset_used,
                    'total_tokens': int(result.total_tokens or 0),
                    'total_cost': float(result.total_cost or 0.0),
                    'request_count': int(result.request_count or 0)
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error getting usage by preset: {e}")
            return []
    
    def delete_old_usage_records(self, days_to_keep: int = 90) -> int:
        """
        Delete old token usage records.
        
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
            
            logger.info(f"Deleted {deleted_count} old token usage records")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting old usage records: {e}")
            db.session.rollback()
            return 0
    
    def get_cost_trends(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get cost trends over time.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            Cost trends data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily cost trends
            daily_query = db.session.query(
                func.date(TokenUsage.created_at).label('date'),
                func.sum(TokenUsage.total_cost).label('total_cost')
            )
            
            if user_id:
                daily_query = daily_query.join(
                    Conversation, TokenUsage.conversation_id == Conversation.id
                ).filter(Conversation.user_id == user_id)
            
            daily_query = daily_query.filter(TokenUsage.created_at >= start_date).group_by(
                func.date(TokenUsage.created_at)
            ).order_by(func.date(TokenUsage.created_at).asc())
            
            daily_results = daily_query.all()
            
            # Total cost in period
            total_query = db.session.query(
                func.sum(TokenUsage.total_cost).label('total_cost')
            )
            
            if user_id:
                total_query = total_query.join(
                    Conversation, TokenUsage.conversation_id == Conversation.id
                ).filter(Conversation.user_id == user_id)
            
            total_query = total_query.filter(TokenUsage.created_at >= start_date)
            total_result = total_query.first()
            
            return {
                'period_days': days,
                'total_cost': float(total_result.total_cost or 0.0),
                'daily_costs': [
                    {
                        'date': result.date.isoformat(),
                        'cost': float(result.total_cost or 0.0)
                    }
                    for result in daily_results
                ],
                'average_daily_cost': float(total_result.total_cost or 0.0) / days if total_result.total_cost else 0.0
            }
        except Exception as e:
            logger.error(f"Error getting cost trends: {e}")
            return {'error': str(e)}