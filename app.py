from flask import Flask, render_template, flash, request, jsonify
import os
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from config import get_config
from auth import auth_bp, init_oauth, login_required, check_lynxx_domain
from flask_login import current_user
from routes.api import api_bp
from routes.agents import agents_bp
from database import init_db

def create_app(config_class=None):
    """Create and configure the Flask application
    
    Args:
        config_class: Optional config class to use (defaults to environment-based config)
    
    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__)
    
    # Load configuration based on environment if not explicitly provided
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    # Set up logging
    configure_logging(app)
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Create upload folder if configured
    if hasattr(app.config, 'UPLOAD_FOLDER'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize security features
    configure_security(app)
    
    # Initialize database
    init_db(app)
    
    # Initialize authentication
    app.register_blueprint(auth_bp, url_prefix='/auth')
    init_oauth(app)
    
    # Register API routes
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(agents_bp)  # Agents API routes (already has /api/agents prefix)
    
    # Register main routes
    register_routes(app)

    return app

def configure_logging(app):
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_level = app.config.get('LOG_LEVEL', logging.INFO)

    # Zet basisniveau op WARNING zodat externe libs stil blijven
    logging.basicConfig(level=log_level, format=log_format)

    # Stel logniveau expliciet in voor je eigen modules
    for module in [
        'app',
        'anthropic_api',
        'api',  # afhankelijk van hoe je het importeert
        'routes.api',
        'routes.agents',
        'agents.orchestrator',
        'agents.base_agent',
        'agents.issue_manager_agent'
    ]:
        logging.getLogger(module).setLevel(log_level)

    app.logger.setLevel(log_level)
    app.logger.info(f"Application starting in {os.environ.get('FLASK_ENV', 'default')} mode")

def configure_security(app):
    """Configure security features for the application"""
    # Initialize CSRF protection if enabled
    if app.config.get('CSRF_ENABLED', True):
        csrf = CSRFProtect()
        csrf.init_app(app)
    
    # Configure proxies if behind a reverse proxy
    if app.config.get('PROXY_COUNT', 0) > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app, 
            x_for=app.config.get('PROXY_COUNT'),
            x_proto=app.config.get('PROXY_COUNT'), 
            x_host=app.config.get('PROXY_COUNT')
        )
    
    # Enable SSL redirect if configured
    if app.config.get('SSL_REDIRECT', False):
        from flask_sslify import SSLify
        SSLify(app)
    
    # Set up rate limiting if enabled
    if app.config.get('RATE_LIMITING_ENABLED', False):
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[f"{app.config.get('MAX_REQUESTS_PER_MINUTE', 30)} per minute"]
        )

def register_routes(app):
    """Register all application routes"""
    @app.route('/')
    def home():
        return render_template('home.html', title=app.config.get('APP_NAME', 'Lynxx Anthropic Console'))
    
    @app.route('/dashboard')
    @login_required
    @check_lynxx_domain
    def dashboard():
        """Protected dashboard that requires authentication"""
        return render_template(
            'home.html', 
            title=f"{app.config.get('APP_NAME', 'Lynxx Anthropic Console')} - Welkom {current_user.name}"
        )
    
    @app.route('/conversations')
    @login_required
    @check_lynxx_domain
    def conversations():
        """Show user's conversation history"""
        return render_template(
            'conversations.html',
            title=f"{app.config.get('APP_NAME', 'Lynxx Anthropic Console')} - Uw Gesprekken"
        )
    
    @app.route('/agents')
    @login_required
    @check_lynxx_domain
    def agents():
        """Show multi-agent interface"""
        return render_template(
            'agents.html',
            title=f"{app.config.get('APP_NAME', 'Lynxx Anthropic Console')} - Multi-Agent System"
        )
    
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({
                "success": False,
                "error": "Endpoint niet gevonden"
            }), 404
        
        flash('De opgevraagde pagina kon niet worden gevonden.', 'error')
        return render_template('home.html', title=  'Pagina niet gevonden'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal server error: {str(e)}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "success": False,
                "error": "Interne serverfout"
            }), 500
            
        flash('Er is een serverfout opgetreden. Probeer het later opnieuw.', 'error')
        return render_template('home.html', title='Serverfout'), 500

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(
        debug=app.config.get('DEBUG', False),
        host=host,
        port=port
    )