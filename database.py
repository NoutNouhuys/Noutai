"""
Database module for the Lynxx Anthropic Console.

This module handles database initialization, configuration, and provides
a SQLAlchemy session factory for other modules to use.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the SQLAlchemy object
db = SQLAlchemy()
migrate = Migrate()


def init_db(app: Flask):
    """
    Initialize the database with the given Flask application.

    Args:
        app: Flask application instance
    """
    # Configure database URI if not already set (tests may provide their own)
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        database_path = os.path.join(app.instance_path, 'anthropic_console.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Make sure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize the database with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Create all tables in the database
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from models.conversation import Conversation, Message
        db.create_all()


def get_session():
    """
    Get a database session.

    Returns:
        SQLAlchemy session object
    """
    return db.session
