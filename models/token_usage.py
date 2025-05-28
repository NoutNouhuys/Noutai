"""
Database model for token usage tracking and analytics.
"""

from datetime import datetime
from database import db


class TokenUsage(db.Model):
    """Model for tracking token usage per message and conversation."""
    
    __tablename__ = 'token_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    
    # Model information
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(50), nullable=True)
    
    # Token counts
    input_tokens = db.Column(db.Integer, nullable=False, default=0)
    output_tokens = db.Column(db.Integer, nullable=False, default=0)
    total_tokens = db.Column(db.Integer, nullable=False, default=0)
    
    # Cache tokens (for ephemeral caching)
    cache_creation_input_tokens = db.Column(db.Integer, nullable=True, default=0)
    cache_read_input_tokens = db.Column(db.Integer, nullable=True, default=0)
    
    # Cost information (in USD)
    input_cost = db.Column(db.Float, nullable=True, default=0.0)
    output_cost = db.Column(db.Float, nullable=True, default=0.0)
    total_cost = db.Column(db.Float, nullable=True, default=0.0)
    
    # Metadata
    request_type = db.Column(db.String(50), nullable=True)  # 'chat', 'tool_use', etc.
    temperature = db.Column(db.Float, nullable=True)
    max_tokens = db.Column(db.Integer, nullable=True)
    preset_used = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    conversation = db.relationship('Conversation', backref='token_usage_records')
    message = db.relationship('Message', backref='token_usage_record', uselist=False)
    
    def __init__(self, conversation_id, model_name, input_tokens=0, output_tokens=0, 
                 message_id=None, model_version=None, cache_creation_input_tokens=0,
                 cache_read_input_tokens=0, request_type=None, temperature=None,
                 max_tokens=None, preset_used=None):
        """Initialize TokenUsage record."""
        self.conversation_id = conversation_id
        self.message_id = message_id
        self.model_name = model_name
        self.model_version = model_version
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens or 0
        self.cache_read_input_tokens = cache_read_input_tokens or 0
        self.request_type = request_type
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.preset_used = preset_used
    
    def calculate_costs(self, pricing_config):
        """Calculate costs based on pricing configuration."""
        if not pricing_config or self.model_name not in pricing_config:
            return
        
        model_pricing = pricing_config[self.model_name]
        
        # Calculate input costs (including cache costs)
        input_cost_per_token = model_pricing.get('input_cost_per_1k_tokens', 0) / 1000
        cache_creation_cost_per_token = model_pricing.get('cache_creation_cost_per_1k_tokens', input_cost_per_token) / 1000
        cache_read_cost_per_token = model_pricing.get('cache_read_cost_per_1k_tokens', input_cost_per_token * 0.1) / 1000
        
        self.input_cost = (
            self.input_tokens * input_cost_per_token +
            self.cache_creation_input_tokens * cache_creation_cost_per_token +
            self.cache_read_input_tokens * cache_read_cost_per_token
        )
        
        # Calculate output costs
        output_cost_per_token = model_pricing.get('output_cost_per_1k_tokens', 0) / 1000
        self.output_cost = self.output_tokens * output_cost_per_token
        
        # Total cost
        self.total_cost = self.input_cost + self.output_cost
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'message_id': self.message_id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'cache_creation_input_tokens': self.cache_creation_input_tokens,
            'cache_read_input_tokens': self.cache_read_input_tokens,
            'input_cost': self.input_cost,
            'output_cost': self.output_cost,
            'total_cost': self.total_cost,
            'request_type': self.request_type,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'preset_used': self.preset_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<TokenUsage {self.id}: {self.model_name} - {self.total_tokens} tokens>'