import os
import unittest
from unittest import mock
from flask import Flask
from config import (
    BaseConfig, DevelopmentConfig, TestingConfig, 
    ProductionConfig, DockerConfig, get_config
)


class TestConfig(unittest.TestCase):
    """Tests voor de Configuratie Module"""
    
    def test_base_config(self):
        """Test of de basis configuratie correct is"""
        config = BaseConfig()
        
        # Basisinstellingen moeten aanwezig zijn
        self.assertIsNotNone(config.SECRET_KEY)
        self.assertTrue(config.SESSION_COOKIE_HTTPONLY)
        self.assertTrue(config.REMEMBER_COOKIE_HTTPONLY)
        self.assertEqual(config.SESSION_COOKIE_SAMESITE, 'Lax')
        
        # Lynxx domein configuratie
        self.assertIn('lynxx.com', config.ALLOWED_DOMAINS)
        self.assertTrue(config.ENABLE_DOMAIN_RESTRICTION)
        
    def test_development_config(self):
        """Test of de development configuratie correct is"""
        config = DevelopmentConfig()
        
        # Development specifieke instellingen
        self.assertTrue(config.DEBUG)
        self.assertFalse(config.TESTING)
        self.assertFalse(config.SESSION_COOKIE_SECURE)
        self.assertFalse(config.REMEMBER_COOKIE_SECURE)
        self.assertFalse(config.SSL_REDIRECT)
        self.assertFalse(config.ENABLE_DOMAIN_RESTRICTION)
        
    def test_testing_config(self):
        """Test of de testing configuratie correct is"""
        config = TestingConfig()
        
        # Testing specifieke instellingen
        self.assertFalse(config.DEBUG)
        self.assertTrue(config.TESTING)
        self.assertEqual(config.DATABASE_URI, 'sqlite:///:memory:')
        self.assertFalse(config.CSRF_ENABLED)
        
    def test_production_config(self):
        """Test of de production configuratie de juiste validaties heeft"""
        # Voor production moeten omgevingsvariabelen gezet zijn
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ANTHROPIC_API_KEY': 'test-api-key',
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        }):
            config = ProductionConfig()
            
            # Production specifieke instellingen
            self.assertFalse(config.DEBUG)
            self.assertFalse(config.TESTING)
            self.assertTrue(config.SESSION_COOKIE_SECURE)
            self.assertTrue(config.REMEMBER_COOKIE_SECURE)
            self.assertTrue(config.SSL_REDIRECT)
            self.assertTrue(config.RATE_LIMITING_ENABLED)
            
    def test_production_config_validation(self):
        """Test of de production configuratie foutmeldingen geeft bij ontbrekende variabelen"""
        # Test zonder SECRET_KEY
        with self.assertRaises(ValueError):
            with mock.patch.dict(os.environ, {
                'ANTHROPIC_API_KEY': 'test-api-key',
                'GOOGLE_CLIENT_ID': 'test-client-id',
                'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            }, clear=True):
                ProductionConfig()
        
        # Test zonder ANTHROPIC_API_KEY
        with self.assertRaises(ValueError):
            with mock.patch.dict(os.environ, {
                'SECRET_KEY': 'test-secret-key',
                'GOOGLE_CLIENT_ID': 'test-client-id',
                'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            }, clear=True):
                ProductionConfig()
        
        # Test zonder Google OAuth credentials
        with self.assertRaises(ValueError):
            with mock.patch.dict(os.environ, {
                'SECRET_KEY': 'test-secret-key',
                'ANTHROPIC_API_KEY': 'test-api-key',
            }, clear=True):
                ProductionConfig()
    
    def test_docker_config(self):
        """Test of de docker configuratie correct is"""
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ANTHROPIC_API_KEY': 'test-api-key',
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        }):
            config = DockerConfig()
            
            # Docker specifieke instellingen
            self.assertFalse(config.SSL_REDIRECT)  # Overridden in Docker config
            
    def test_get_config(self):
        """Test of de get_config functie de juiste configuratie teruggeeft"""
        # Test default
        with mock.patch.dict(os.environ, {}, clear=True):
            config = get_config()
            self.assertIsInstance(config, DevelopmentConfig)
        
        # Test development
        with mock.patch.dict(os.environ, {'FLASK_ENV': 'development'}, clear=True):
            config = get_config()
            self.assertIsInstance(config, DevelopmentConfig)
        
        # Test testing
        with mock.patch.dict(os.environ, {'FLASK_ENV': 'testing'}, clear=True):
            config = get_config()
            self.assertIsInstance(config, TestingConfig)
        
        # Test production
        with mock.patch.dict(os.environ, {
            'FLASK_ENV': 'production',
            'SECRET_KEY': 'test-secret-key',
            'ANTHROPIC_API_KEY': 'test-api-key',
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        }):
            config = get_config()
            self.assertIsInstance(config, ProductionConfig)
        
        # Test docker
        with mock.patch.dict(os.environ, {
            'FLASK_ENV': 'docker',
            'SECRET_KEY': 'test-secret-key',
            'ANTHROPIC_API_KEY': 'test-api-key',
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        }):
            config = get_config()
            self.assertIsInstance(config, DockerConfig)
        
        # Test onbekende omgeving (moet default teruggeven)
        with mock.patch.dict(os.environ, {'FLASK_ENV': 'unknown'}, clear=True):
            config = get_config()
            self.assertIsInstance(config, DevelopmentConfig)


class TestConfigWithApp(unittest.TestCase):
    """Tests voor de integratie van de Configuratie Module met Flask app"""
    
    def setUp(self):
        """Setup voor tests"""
        self.app = Flask(__name__)
    
    def test_config_with_app(self):
        """Test of de configuratie correct werkt met een Flask app"""
        self.app.config.from_object(DevelopmentConfig())
        
        # Check of configuratie correct is toegepast
        self.assertTrue(self.app.config['DEBUG'])
        self.assertFalse(self.app.config['TESTING'])
        self.assertIn('lynxx.com', self.app.config['ALLOWED_DOMAINS'])


if __name__ == '__main__':
    unittest.main()
