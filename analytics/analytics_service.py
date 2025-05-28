"""
Analytics service for data aggregation and insights.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from analytics.token_tracker import TokenTracker
from analytics.cost_calculator import CostCalculator
from repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics data aggregation and insights."""
    
    def __init__(self, token_tracker: Optional[TokenTracker] = None,
                 cost_calculator: Optional[CostCalculator] = None,
                 analytics_repository: Optional[AnalyticsRepository] = None):
        """
        Initialize analytics service.
        
        Args:
            token_tracker: Optional token tracker instance
            cost_calculator: Optional cost calculator instance
            analytics_repository: Optional analytics repository instance
        """
        self.token_tracker = token_tracker or TokenTracker()
        self.cost_calculator = cost_calculator or CostCalculator()
        self.analytics_repository = analytics_repository or AnalyticsRepository()
    
    def get_dashboard_data(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            Dashboard data dictionary
        """
        try:
            # Get overall usage summary
            usage_summary = self.analytics_repository.get_usage_summary_by_user(user_id, days)
            
            # Get daily trends
            daily_trends = self.analytics_repository.get_daily_usage_trends(user_id, days)
            
            # Get model breakdown
            model_breakdown = self.analytics_repository.get_model_usage_breakdown(user_id, days)
            
            # Get top conversations
            top_conversations = self.analytics_repository.get_top_conversations_by_usage(user_id, 5, days)
            
            # Get preset usage
            preset_usage = self.analytics_repository.get_usage_by_preset(user_id, days)
            
            # Get cost trends
            cost_trends = self.analytics_repository.get_cost_trends(user_id, days)
            
            # Calculate insights
            insights = self._generate_insights(usage_summary, daily_trends, model_breakdown)
            
            return {
                'period_days': days,
                'user_id': user_id,
                'usage_summary': usage_summary,
                'daily_trends': daily_trends,
                'model_breakdown': model_breakdown,
                'top_conversations': top_conversations,
                'preset_usage': preset_usage,
                'cost_trends': cost_trends,
                'insights': insights,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}
    
    def get_conversation_analytics(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation analytics dictionary
        """
        try:
            # Get usage summary
            usage_summary = self.analytics_repository.get_usage_summary_by_conversation(conversation_id)
            
            # Get detailed usage records
            usage_records = self.analytics_repository.get_token_usage_by_conversation(conversation_id)
            
            # Calculate message-level analytics
            message_analytics = []
            for record in usage_records:
                message_analytics.append({
                    'message_id': record.message_id,
                    'model_name': record.model_name,
                    'tokens': record.total_tokens,
                    'cost': record.total_cost,
                    'timestamp': record.created_at.isoformat() if record.created_at else None,
                    'preset_used': record.preset_used,
                    'temperature': record.temperature
                })
            
            # Calculate efficiency metrics
            efficiency_metrics = self._calculate_conversation_efficiency(usage_records)
            
            return {
                'conversation_id': conversation_id,
                'usage_summary': usage_summary,
                'message_analytics': message_analytics,
                'efficiency_metrics': efficiency_metrics,
                'total_messages': len(usage_records)
            }
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {'error': str(e)}
    
    def get_cost_analysis(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed cost analysis.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            Cost analysis dictionary
        """
        try:
            # Get cost trends
            cost_trends = self.analytics_repository.get_cost_trends(user_id, days)
            
            # Get model cost breakdown
            model_breakdown = self.analytics_repository.get_model_usage_breakdown(user_id, days)
            
            # Calculate cost projections
            projections = self._calculate_cost_projections(cost_trends['daily_costs'])
            
            # Get cost efficiency metrics
            efficiency = self._calculate_cost_efficiency(model_breakdown)
            
            # Get pricing information
            pricing_info = self.cost_calculator.get_all_model_pricing()
            
            return {
                'period_days': days,
                'cost_trends': cost_trends,
                'model_cost_breakdown': model_breakdown,
                'projections': projections,
                'efficiency_metrics': efficiency,
                'pricing_info': pricing_info,
                'analysis_date': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cost analysis: {e}")
            return {'error': str(e)}
    
    def get_usage_patterns(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Analyze usage patterns and trends.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            Usage patterns dictionary
        """
        try:
            # Get daily trends
            daily_trends = self.analytics_repository.get_daily_usage_trends(user_id, days)
            
            # Get model usage patterns
            model_breakdown = self.analytics_repository.get_model_usage_breakdown(user_id, days)
            
            # Get preset usage patterns
            preset_usage = self.analytics_repository.get_usage_by_preset(user_id, days)
            
            # Analyze patterns
            patterns = self._analyze_usage_patterns(daily_trends, model_breakdown, preset_usage)
            
            return {
                'period_days': days,
                'daily_trends': daily_trends,
                'model_patterns': model_breakdown,
                'preset_patterns': preset_usage,
                'pattern_analysis': patterns,
                'analysis_date': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting usage patterns: {e}")
            return {'error': str(e)}
    
    def get_model_comparison(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Compare performance and costs across different models.
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            Model comparison dictionary
        """
        try:
            # Get model breakdown
            model_breakdown = self.analytics_repository.get_model_usage_breakdown(user_id, days)
            
            # Calculate comparison metrics
            comparison_metrics = []
            for model_data in model_breakdown:
                model_name = model_data['model_name']
                pricing = self.cost_calculator.get_model_pricing(model_name)
                
                metrics = {
                    'model_name': model_name,
                    'usage_stats': model_data,
                    'pricing_info': pricing,
                    'cost_per_token': model_data['total_cost'] / model_data['total_tokens'] if model_data['total_tokens'] > 0 else 0,
                    'efficiency_score': self._calculate_model_efficiency_score(model_data, pricing)
                }
                comparison_metrics.append(metrics)
            
            # Sort by efficiency score
            comparison_metrics.sort(key=lambda x: x['efficiency_score'], reverse=True)
            
            return {
                'period_days': days,
                'model_comparison': comparison_metrics,
                'recommendations': self._generate_model_recommendations(comparison_metrics),
                'analysis_date': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting model comparison: {e}")
            return {'error': str(e)}
    
    def _generate_insights(self, usage_summary: Dict[str, Any], 
                          daily_trends: List[Dict[str, Any]], 
                          model_breakdown: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate insights from analytics data."""
        insights = []
        
        try:
            # Usage insights
            if usage_summary.get('total_tokens', 0) > 0:
                avg_cost_per_token = usage_summary['total_cost'] / usage_summary['total_tokens']
                insights.append({
                    'type': 'cost_efficiency',
                    'title': 'Average Cost per Token',
                    'description': f"Your average cost is ${avg_cost_per_token:.6f} per token",
                    'value': f"${avg_cost_per_token:.6f}"
                })
            
            # Daily usage trends
            if len(daily_trends) >= 7:
                recent_avg = sum(day['total_tokens'] for day in daily_trends[-7:]) / 7
                earlier_avg = sum(day['total_tokens'] for day in daily_trends[-14:-7]) / 7 if len(daily_trends) >= 14 else recent_avg
                
                if recent_avg > earlier_avg * 1.2:
                    insights.append({
                        'type': 'trend',
                        'title': 'Increasing Usage',
                        'description': f"Your usage has increased by {((recent_avg - earlier_avg) / earlier_avg * 100):.1f}% in the last week",
                        'value': f"+{((recent_avg - earlier_avg) / earlier_avg * 100):.1f}%"
                    })
                elif recent_avg < earlier_avg * 0.8:
                    insights.append({
                        'type': 'trend',
                        'title': 'Decreasing Usage',
                        'description': f"Your usage has decreased by {((earlier_avg - recent_avg) / earlier_avg * 100):.1f}% in the last week",
                        'value': f"-{((earlier_avg - recent_avg) / earlier_avg * 100):.1f}%"
                    })
            
            # Model efficiency insights
            if model_breakdown:
                most_used_model = max(model_breakdown, key=lambda x: x['total_tokens'])
                most_efficient_model = min(model_breakdown, key=lambda x: x['total_cost'] / x['total_tokens'] if x['total_tokens'] > 0 else float('inf'))
                
                if most_used_model['model_name'] != most_efficient_model['model_name']:
                    savings_potential = (most_used_model['total_cost'] / most_used_model['total_tokens'] - 
                                       most_efficient_model['total_cost'] / most_efficient_model['total_tokens']) * most_used_model['total_tokens']
                    
                    insights.append({
                        'type': 'optimization',
                        'title': 'Model Optimization Opportunity',
                        'description': f"Switching to {most_efficient_model['model_name']} could save approximately ${savings_potential:.4f}",
                        'value': f"${savings_potential:.4f}"
                    })
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    def _calculate_conversation_efficiency(self, usage_records: List) -> Dict[str, Any]:
        """Calculate efficiency metrics for a conversation."""
        if not usage_records:
            return {}
        
        total_tokens = sum(record.total_tokens for record in usage_records)
        total_cost = sum(record.total_cost or 0 for record in usage_records)
        
        return {
            'avg_tokens_per_message': total_tokens / len(usage_records),
            'avg_cost_per_message': total_cost / len(usage_records),
            'cost_per_token': total_cost / total_tokens if total_tokens > 0 else 0,
            'total_messages': len(usage_records)
        }
    
    def _calculate_cost_projections(self, daily_costs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost projections based on trends."""
        if len(daily_costs) < 7:
            return {'error': 'Insufficient data for projections'}
        
        # Simple linear projection based on last 7 days
        recent_costs = [day['cost'] for day in daily_costs[-7:]]
        avg_daily_cost = sum(recent_costs) / len(recent_costs)
        
        return {
            'daily_average': avg_daily_cost,
            'weekly_projection': avg_daily_cost * 7,
            'monthly_projection': avg_daily_cost * 30,
            'yearly_projection': avg_daily_cost * 365
        }
    
    def _calculate_cost_efficiency(self, model_breakdown: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost efficiency metrics."""
        if not model_breakdown:
            return {}
        
        total_tokens = sum(model['total_tokens'] for model in model_breakdown)
        total_cost = sum(model['total_cost'] for model in model_breakdown)
        
        # Find most and least efficient models
        model_efficiency = []
        for model in model_breakdown:
            if model['total_tokens'] > 0:
                efficiency = model['total_cost'] / model['total_tokens']
                model_efficiency.append({
                    'model_name': model['model_name'],
                    'cost_per_token': efficiency,
                    'total_tokens': model['total_tokens']
                })
        
        model_efficiency.sort(key=lambda x: x['cost_per_token'])
        
        return {
            'overall_cost_per_token': total_cost / total_tokens if total_tokens > 0 else 0,
            'most_efficient_model': model_efficiency[0] if model_efficiency else None,
            'least_efficient_model': model_efficiency[-1] if model_efficiency else None,
            'efficiency_range': {
                'min': model_efficiency[0]['cost_per_token'] if model_efficiency else 0,
                'max': model_efficiency[-1]['cost_per_token'] if model_efficiency else 0
            }
        }
    
    def _analyze_usage_patterns(self, daily_trends: List[Dict[str, Any]], 
                               model_breakdown: List[Dict[str, Any]], 
                               preset_usage: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze usage patterns and identify trends."""
        patterns = {}
        
        # Daily usage patterns
        if daily_trends:
            # Find peak usage days
            max_usage_day = max(daily_trends, key=lambda x: x['total_tokens'])
            min_usage_day = min(daily_trends, key=lambda x: x['total_tokens'])
            
            patterns['daily_patterns'] = {
                'peak_usage_day': max_usage_day,
                'lowest_usage_day': min_usage_day,
                'usage_variance': max_usage_day['total_tokens'] - min_usage_day['total_tokens']
            }
        
        # Model preferences
        if model_breakdown:
            total_requests = sum(model['request_count'] for model in model_breakdown)
            patterns['model_preferences'] = [
                {
                    'model_name': model['model_name'],
                    'usage_percentage': (model['request_count'] / total_requests * 100) if total_requests > 0 else 0,
                    'avg_tokens_per_request': model['avg_tokens_per_request']
                }
                for model in model_breakdown
            ]
        
        # Preset usage patterns
        if preset_usage:
            total_preset_requests = sum(preset['request_count'] for preset in preset_usage)
            patterns['preset_preferences'] = [
                {
                    'preset_name': preset['preset_name'],
                    'usage_percentage': (preset['request_count'] / total_preset_requests * 100) if total_preset_requests > 0 else 0
                }
                for preset in preset_usage
            ]
        
        return patterns
    
    def _calculate_model_efficiency_score(self, model_data: Dict[str, Any], 
                                        pricing: Optional[Dict[str, float]]) -> float:
        """Calculate efficiency score for a model (0-100)."""
        if not pricing or model_data['total_tokens'] == 0:
            return 0
        
        # Base score on cost per token (lower is better)
        cost_per_token = model_data['total_cost'] / model_data['total_tokens']
        
        # Normalize against typical pricing range (0.0001 to 0.1 per token)
        min_cost = 0.0001
        max_cost = 0.1
        
        # Invert score so lower cost = higher score
        normalized_score = max(0, min(100, (max_cost - cost_per_token) / (max_cost - min_cost) * 100))
        
        return round(normalized_score, 2)
    
    def _generate_model_recommendations(self, comparison_metrics: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate recommendations based on model comparison."""
        recommendations = []
        
        if not comparison_metrics:
            return recommendations
        
        # Recommend most efficient model
        most_efficient = comparison_metrics[0]
        recommendations.append({
            'type': 'efficiency',
            'title': 'Most Efficient Model',
            'description': f"{most_efficient['model_name']} offers the best cost efficiency",
            'action': f"Consider using {most_efficient['model_name']} for cost-sensitive tasks"
        })
        
        # Identify underused efficient models
        for model in comparison_metrics:
            if model['efficiency_score'] > 70 and model['usage_stats']['request_count'] < 10:
                recommendations.append({
                    'type': 'underused',
                    'title': 'Underused Efficient Model',
                    'description': f"{model['model_name']} is highly efficient but rarely used",
                    'action': f"Try {model['model_name']} for better cost efficiency"
                })
        
        return recommendations