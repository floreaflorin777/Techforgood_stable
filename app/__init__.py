from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Setup logging
    # Create logs directory in a safe way
    try:
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("Created logs directory")
    except Exception as e:
        print(f"Warning: Could not create logs directory: {str(e)}")
        
    # Configure file handler with error handling
    try:
        log_path = f'logs/foodbank_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10
        )
        print(f"Configured logging to: {log_path}")
    except Exception as e:
        print(f"Warning: Could not configure file logging: {str(e)}")
        file_handler = logging.NullHandler()
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Food Bank API startup')
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    limiter.init_app(app)
    jwt.init_app(app)
    
    # Setup database connection
    from app.database import get_database_url
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url(app)
    db.init_app(app)
    
    # Register blueprints
    from app.routes import main as main_blueprint
    from app.auth import auth as auth_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    return app
