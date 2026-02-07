#!/usr/bin/env python3
"""
Cloud Storage Application - Production Ready
Main application file with production configurations
"""

from flask import Flask
from config import get_config
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='storage_templates', 
                static_folder='storage_static')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Setup logging
    if not app.debug:
        setup_logging(app)
    
    # Initialize storage directories
    init_storage(app)
    
    # Register blueprints (routes)
    from routes import register_routes
    register_routes(app)
    
    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    return app

def init_storage(app):
    """Initialize storage directories"""
    upload_folder = app.config['UPLOAD_FOLDER']
    shared_folder = app.config['SHARED_FOLDER']
    
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(shared_folder, exist_ok=True)
    
    # Initialize database if needed
    from database import init_db
    init_db(app.config['DATABASE_FILE'])

def setup_logging(app):
    """Setup production logging"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/cloud_storage.log', 
        maxBytes=10240000, 
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Cloud Storage startup')

if __name__ == '__main__':
    app = create_app()
    
    print("=" * 60)
    print("Cloud Storage Application Starting")
    print("=" * 60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Host: {app.config['HOST']}")
    print(f"Port: {app.config['PORT']}")
    print(f"Debug: {app.config['DEBUG']}")
    print(f"Max Users: {app.config['MAX_USERS']}")
    print(f"Storage per User: {app.config['STORAGE_LIMIT_PER_USER'] / (1024**3):.1f}GB")
    print("=" * 60)
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
