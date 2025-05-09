import os
import json
import requests
from flask import Blueprint, redirect, url_for, session, request, current_app, flash
from oauthlib.oauth2 import WebApplicationClient
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from user import User
from functools import wraps

# Create Blueprint for auth-related routes
auth_bp = Blueprint('auth', __name__)

# OAuth 2 client setup
client = None

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Log in met je Lynxx account om toegang te krijgen'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get(user_id)

def init_oauth(app):
    """Initialize OAuth client with app configuration."""
    global client
    
    # Allow OAuth over HTTP in development environments
    if app.config.get('DEBUG', False) and not os.environ.get('OAUTHLIB_INSECURE_TRANSPORT'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        app.logger.warning('OAUTHLIB_INSECURE_TRANSPORT is enabled. OAuth requests will be made over HTTP.')
    
    client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])
    login_manager.init_app(app)

def get_google_provider_cfg():
    """Retrieve Google's OAuth 2.0 endpoint configuration."""
    return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()

@auth_bp.route('/login')
def login():
    """Route to initiate the Google OAuth login flow."""
    # Get Google's OAuth config
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Prepare the redirect URI for Google OAuth
    redirect_uri = url_for('auth.callback', _external=True)
    
    # Build authorization URL
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=["openid", "email", "profile"],
    )
    
    return redirect(request_uri)

@auth_bp.route('/login/callback')
def callback():
    """Handle the OAuth callback from Google."""
    # Get authorization code from the callback request
    code = request.args.get('code')
    
    # Get token endpoint and exchange code for tokens
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Prepare and send token request
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for('auth.callback', _external=True),
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(current_app.config['GOOGLE_CLIENT_ID'], current_app.config['GOOGLE_CLIENT_SECRET']),
    )

    # Parse the token response
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # Verify user information
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        user_email = userinfo_response.json()["email"]
        user_name = userinfo_response.json().get("given_name", "")
        user_picture = userinfo_response.json().get("picture", "")
        
        # Check if user's email domain is allowed
        email_domain = user_email.split('@')[1]
        if email_domain not in current_app.config['ALLOWED_DOMAINS']:
            flash('Je hebt geen toegang met dit e-mailadres. Alleen @lynxx.com e-mailadressen zijn toegestaan.', 'error')
            return redirect(url_for('home'))
        
        # Create/update user in database
        user = User(
            id=unique_id,
            name=user_name,
            email=user_email,
            profile_pic=user_picture
        )
        User.create_or_update(user)
        
        # Log in the user
        login_user(user)
        
        # Redirect to the main application
        return redirect(url_for('home'))
    else:
        flash('Kon je account niet verifiëren. Probeer het opnieuw.', 'error')
        return redirect(url_for('home'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    session.clear()
    flash('Je bent uitgelogd.', 'info')
    return redirect(url_for('home'))

# Custom decorator to check if user is from lynxx.com domain
def check_lynxx_domain(f):
    """Decorator to check if user's email domain is from lynxx.com."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            email_domain = current_user.email.split('@')[1]
            if email_domain not in current_app.config['ALLOWED_DOMAINS']:
                flash('Je hebt geen toegang met dit e-mailadres. Alleen @lynxx.com e-mailadressen zijn toegestaan.', 'error')
                logout_user()
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Keep old name for backwards compatibility, but only for legacy references
# Do not use this in new code
lynxx_domain_required = check_lynxx_domain
