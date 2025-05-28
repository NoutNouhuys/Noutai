"""
Cost calculator for token usage based on model pricing.
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculator for token usage costs based on model pricing."""
    
    # Default pricing configuration (USD per 1K tokens)
    # Based on Anthropic pricing as of 2024
    DEFAULT_PRICING = {
        'claude-3-5-sonnet-20241022': {
            'input_cost_per_1k_tokens': 0.003,
            'output_cost_per_1k_tokens': 0.015,
            'cache_creation_cost_per_1k_tokens': 0.00375,  # 25% markup for cache creation
            'cache_read_cost_per_1k_tokens': 0.0003,  # 90% discount for cache reads
        },
        'claude-3-5-sonnet-20240620': {
            'input_cost_per_1k_tokens': 0.003,
            'output_cost_per_1k_tokens': 0.015,
            'cache_creation_cost_per_1k_tokens': 0.00375,
            'cache_read_cost_per_1k_tokens': 0.0003,
        },
        'claude-3-5-haiku-20241022': {
            'input_cost_per_1k_tokens': 0.001,
            'output_cost_per_1k_tokens': 0.005,
            'cache_creation_cost_per_1k_tokens': 0.00125,
            'cache_read_cost_per_1k_tokens': 0.0001,
        },
        'claude-3-opus-20240229': {
            'input_cost_per_1k_tokens': 0.015,
            'output_cost_per_1k_tokens': 0.075,
            'cache_creation_cost_per_1k_tokens': 0.01875,
            'cache_read_cost_per_1k_tokens': 0.0015,
        },
        'claude-3-sonnet-20240229': {
            'input_cost_per_1k_tokens': 0.003,
            'output_cost_per_1k_tokens': 0.015,
            'cache_creation_cost_per_1k_tokens': 0.00375,
            'cache_read_cost_per_1k_tokens': 0.0003,
        },
        'claude-3-haiku-20240307': {
            'input_cost_per_1k_tokens': 0.00025,
            'output_cost_per_1k_tokens': 0.00125,
            'cache_creation_cost_per_1k_tokens': 0.0003125,
            'cache_read_cost_per_1k_tokens': 0.000025,
        },
        # Claude 4 Sonnet (new model)
        'claude-sonnet-4-20250514': {
            'input_cost_per_1k_tokens': 0.003,
            'output_cost_per_1k_tokens': 0.015,
            'cache_creation_cost_per_1k_tokens': 0.00375,
            'cache_read_cost_per_1k_tokens': 0.0003,
        }
    }
    
    def __init__(self, custom_pricing: Optional[Dict[str, Any]] = None):
        """
        Initialize cost calculator.
        
        Args:
            custom_pricing: Optional custom pricing configuration to override defaults
        """
        self.pricing_config = self.DEFAULT_PRICING.copy()
        if custom_pricing:
            self.pricing_config.update(custom_pricing)
    
    def calculate_cost(self, model_name: str, input_tokens: int = 0, output_tokens: int = 0,
                      cache_creation_tokens: int = 0, cache_read_tokens: int = 0) -> Dict[str, float]:
        """
        Calculate cost for token usage.
        
        Args:
            model_name: Name of the model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_creation_tokens: Number of tokens for cache creation
            cache_read_tokens: Number of tokens read from cache
            
        Returns:
            Dictionary with cost breakdown
        """
        if model_name not in self.pricing_config:
            logger.warning(f"No pricing configuration found for model: {model_name}")
            return {
                'input_cost': 0.0,
                'output_cost': 0.0,
                'cache_creation_cost': 0.0,
                'cache_read_cost': 0.0,
                'total_cost': 0.0,
                'warning': f'No pricing data for model {model_name}'
            }
        
        pricing = self.pricing_config[model_name]
        
        # Calculate costs per token type
        input_cost = (input_tokens / 1000) * pricing['input_cost_per_1k_tokens']
        output_cost = (output_tokens / 1000) * pricing['output_cost_per_1k_tokens']
        cache_creation_cost = (cache_creation_tokens / 1000) * pricing.get('cache_creation_cost_per_1k_tokens', pricing['input_cost_per_1k_tokens'])
        cache_read_cost = (cache_read_tokens / 1000) * pricing.get('cache_read_cost_per_1k_tokens', pricing['input_cost_per_1k_tokens'] * 0.1)
        
        total_cost = input_cost + output_cost + cache_creation_cost + cache_read_cost
        
        return {
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'cache_creation_cost': round(cache_creation_cost, 6),
            'cache_read_cost': round(cache_read_cost, 6),
            'total_cost': round(total_cost, 6)
        }
    
    def get_model_pricing(self, model_name: str) -> Optional[Dict[str, float]]:
        """
        Get pricing configuration for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Pricing configuration or None if not found
        """
        return self.pricing_config.get(model_name)
    
    def get_all_model_pricing(self) -> Dict[str, Dict[str, float]]:
        """
        Get pricing configuration for all models.
        
        Returns:
            Complete pricing configuration
        """
        return self.pricing_config.copy()
    
    def update_model_pricing(self, model_name: str, pricing: Dict[str, float]) -> None:
        """
        Update pricing for a specific model.
        
        Args:
            model_name: Name of the model
            pricing: New pricing configuration
        """
        self.pricing_config[model_name] = pricing
        logger.info(f"Updated pricing for model: {model_name}")
    
    def estimate_cost(self, model_name: str, estimated_input_tokens: int, 
                     estimated_output_tokens: int) -> Dict[str, float]:
        """
        Estimate cost for a request before making it.
        
        Args:
            model_name: Name of the model
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            Estimated cost breakdown
        """
        return self.calculate_cost(
            model_name=model_name,
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens
        )
    
    def format_cost(self, cost: float, currency: str = 'USD') -> str:
        """
        Format cost for display.
        
        Args:
            cost: Cost amount
            currency: Currency symbol
            
        Returns:
            Formatted cost string
        """
        if cost < 0.01:
            return f"${cost:.6f}"
        elif cost < 1.0:
            return f"${cost:.4f}"
        else:
            return f"${cost:.2f}"
    
    def get_cost_summary(self, costs: list) -> Dict[str, Any]:
        """
        Generate cost summary from list of cost calculations.
        
        Args:
            costs: List of cost dictionaries
            
        Returns:
            Summary with totals and averages
        """
        if not costs:
            return {
                'total_cost': 0.0,
                'average_cost': 0.0,
                'total_input_cost': 0.0,
                'total_output_cost': 0.0,
                'total_cache_cost': 0.0,
                'count': 0
            }
        
        total_cost = sum(c.get('total_cost', 0) for c in costs)
        total_input_cost = sum(c.get('input_cost', 0) for c in costs)
        total_output_cost = sum(c.get('output_cost', 0) for c in costs)
        total_cache_creation_cost = sum(c.get('cache_creation_cost', 0) for c in costs)
        total_cache_read_cost = sum(c.get('cache_read_cost', 0) for c in costs)
        total_cache_cost = total_cache_creation_cost + total_cache_read_cost
        
        return {
            'total_cost': round(total_cost, 6),
            'average_cost': round(total_cost / len(costs), 6),
            'total_input_cost': round(total_input_cost, 6),
            'total_output_cost': round(total_output_cost, 6),
            'total_cache_cost': round(total_cache_cost, 6),
            'total_cache_creation_cost': round(total_cache_creation_cost, 6),
            'total_cache_read_cost': round(total_cache_read_cost, 6),
            'count': len(costs)
        }