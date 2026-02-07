"""
Cloud Storage Application - Production Configuration
Supports deployment to production servers with proper security
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    
    # File Upload
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'user_storage'
    SHARED_FOLDER = os.environ.get('SHARED_FOLDER') or 'shared_storage'
    
    # Database
    DATABASE_FILE = os.environ.get('DATABASE_FILE') or 'users.json'
    
    # Session
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get('SESSION_LIFETIME_HOURS', 1)))
    
    # Application
    MAX_USERS = int(os.environ.get('MAX_USERS', 10))
    STORAGE_LIMIT_PER_USER = int(os.environ.get('STORAGE_LIMIT_GB', 10)) * 1024 * 1024 * 1024
    
    # Server
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    
    # Override with required environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # if not SECRET_KEY:
    #     raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
