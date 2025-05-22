import os
import logging
from dotenv import load_dotenv

# Setup module logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
load_dotenv()

class BaseConfig:
    """Base configuration class with common settings for all environments"""
    # Application Name
    APP_NAME = "Lynxx Anthropic Console"
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-unsafe-for-production'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    
    # Anthropic API Configuration
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_DEFAULT_MODEL = os.environ.get('ANTHROPIC_DEFAULT_MODEL') or 'claude-3-haiku-20240307'
    ANTHROPIC_MAX_TOKENS = int(os.environ.get('ANTHROPIC_MAX_TOKENS') or 4000)

    _base_path = os.path.dirname(__file__)
    _system_prompt_path = os.path.join(_base_path, 'system_prompt.txt')
    try:
        with open(_system_prompt_path, 'r', encoding='utf-8') as file:
            ANTHROPIC_SYSTEM_PROMPT = file.read()
    except FileNotFoundError:
        logger.warning(f"system_prompt.txt not found at {_system_prompt_path}")
        ANTHROPIC_SYSTEM_PROMPT = None
    
    # Database Configuration
    DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Lynxx Domain Configuration
    ALLOWED_DOMAINS = ['lynxx.com']
    ENABLE_DOMAIN_RESTRICTION = True
    
    # Security Configuration
    CSRF_ENABLED = True
    SSL_REDIRECT = False
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # MCP Configuration
    MCP_SERVERS = os.getenv("MCP_SERVERS", "").split(",")
    #print(f"DEBUG: Hier wordt MCP_SERVERS WEL GELADEN MAAR: {MCP_SERVERS}")
    
    # Rate Limiting
    RATE_LIMITING_ENABLED = True
    MAX_REQUESTS_PER_MINUTE = 30
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx', 'docx'}

    # Caching
    CACHE_DEFAULT_EXPIRATION = int(os.environ.get('CACHE_DEFAULT_EXPIRATION', 300))


class DevelopmentConfig(BaseConfig):
    """Development configuration with debug features enabled"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = logging.INFO
    RATE_LIMITING_ENABLED = False
    ENABLE_DOMAIN_RESTRICTION = False  # Allow any domain in development
    
    # Security settings for development
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    """Testing configuration optimized for automated tests"""
    DEBUG = False
    TESTING = True
    DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory database for testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SERVER_NAME = 'localhost.localdomain'
    
    # Security settings relaxed for testing
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for tests
    RATE_LIMITING_ENABLED = False
    ENABLE_DOMAIN_RESTRICTION = False


class ProductionConfig(BaseConfig):
    """Production configuration with security features enforced"""
    DEBUG = False
    TESTING = False
    
    # Ensure these are set in production environment 
    # and not using default development values
    def __init__(self):
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("Production environment requires SECRET_KEY to be set")
        
        if not os.environ.get('ANTHROPIC_API_KEY'):
            raise ValueError("Production environment requires ANTHROPIC_API_KEY to be set")
        
        if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
            raise ValueError("Production environment requires Google OAuth credentials to be set")
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SSL_REDIRECT = True
    
    # Enable rate limiting in production
    RATE_LIMITING_ENABLED = True


class DockerConfig(ProductionConfig):
    """Configuration for Docker deployments"""
    # Override specific settings for Docker environment
    SSL_REDIRECT = False  # Handled by reverse proxy in typical Docker setups


# Configuration dictionary to map environment names to config classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Load and return the appropriate configuration class based on the
    FLASK_ENV environment variable.
    
    Returns:
        Config class appropriate for the current environment
    """
    env = os.environ.get('FLASK_ENV', 'default')
    config_class = config.get(env, config['default'])
    return config_class()


# For backwards compatibility with existing code
Config = BaseConfig
