import os
import pytest
import json
from flask import Flask, session
from unittest.mock import patch, MagicMock
from app import create_app
from config import Config
from user import User

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SECRET_KEY = 'test-key'
    GOOGLE_CLIENT_ID = 'test-client-id'
    GOOGLE_CLIENT_SECRET = 'test-client-secret'
    ALLOWED_DOMAINS = ['lynxx.com']
    

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestConfig)
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    """Test client for the Flask application."""
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_login_route(client):
    """Test login route redirects to Google"""
    # Mock the get_google_provider_cfg function
    with patch('auth.get_google_provider_cfg') as mock_get_cfg:
        mock_get_cfg.return_value = {"authorization_endpoint": "https://accounts.google.com/o/oauth2/auth"}
        
        # Make request to login route
        response = client.get('/auth/login')
        
        # Verify redirect to Google
        assert response.status_code == 302  # Redirect status code
        assert "accounts.google.com" in response.headers['Location']


def test_callback_with_valid_user():
    """Test OAuth callback with valid user"""
    # This would be a more complex test with mock responses
    pass


def test_callback_with_invalid_domain():
    """Test OAuth callback with non-Lynxx domain"""
    # This would be a more complex test with mock responses
    pass


def test_logout(client):
    """Test logout functionality"""
    # First need to simulate a login
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user_id'
    
    # Now test logout
    response = client.get('/auth/logout', follow_redirects=True)
    
    # Check user is redirected to home page
    assert response.status_code == 200
    
    # Check session is cleared (user_id should not be in session)
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_lynxx_domain_required():
    """Test the lynxx_domain_required decorator"""
    # This would test the decorator functionality
    pass


def test_user_model():
    """Test User model functionality"""
    # Create a test user
    test_user = User(
        id='123', 
        name='Test User', 
        email='test@lynxx.com', 
        profile_pic='http://example.com/pic.jpg'
    )
    
    # Test to_dict method
    user_dict = test_user.to_dict()
    assert user_dict['id'] == '123'
    assert user_dict['name'] == 'Test User'
    assert user_dict['email'] == 'test@lynxx.com'
    assert user_dict['profile_pic'] == 'http://example.com/pic.jpg'
