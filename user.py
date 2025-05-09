from flask_login import UserMixin
from flask import current_app
import json
import os
import time
from pathlib import Path

# This is a simple file-based user storage for development
# In a production environment, this would use a database
class User(UserMixin):
    """User class for authentication and session management."""
    
    # Dictionary to store users in memory
    _users = {}
    
    def __init__(self, id, name, email, profile_pic):
        """Initialize a user with Google OAuth information."""
        self.id = id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.created_at = time.time()
        self.last_login = time.time()
    
    @classmethod
    def get(cls, user_id):
        """Get a user by ID."""
        # Try to get from memory first
        if user_id in cls._users:
            return cls._users[user_id]
        
        # Try to load from file if not in memory
        user_data = cls._load_user_from_file(user_id)
        if user_data:
            user = cls(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email'],
                profile_pic=user_data['profile_pic']
            )
            user.created_at = user_data.get('created_at', time.time())
            user.last_login = user_data.get('last_login', time.time())
            cls._users[user_id] = user
            return user
        
        return None
    
    @classmethod
    def create_or_update(cls, user):
        """Create or update a user in storage."""
        cls._users[user.id] = user
        cls._save_user_to_file(user)
        return user
    
    @classmethod
    def _get_users_dir(cls):
        """Get the directory where user data is stored."""
        users_dir = Path(current_app.instance_path) / 'users'
        os.makedirs(users_dir, exist_ok=True)
        return users_dir
    
    @classmethod
    def _load_user_from_file(cls, user_id):
        """Load a user from a file."""
        user_file = cls._get_users_dir() / f"{user_id}.json"
        if user_file.exists():
            with open(user_file, 'r') as f:
                return json.load(f)
        return None
    
    @classmethod
    def _save_user_to_file(cls, user):
        """Save a user to a file."""
        user_file = cls._get_users_dir() / f"{user.id}.json"
        
        # Update last_login time
        user.last_login = time.time()
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'profile_pic': user.profile_pic,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
        
        with open(user_file, 'w') as f:
            json.dump(user_data, f, indent=4)
    
    def to_dict(self):
        """Convert user to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'profile_pic': self.profile_pic,
            'created_at': self.created_at,
            'last_login': self.last_login
        }