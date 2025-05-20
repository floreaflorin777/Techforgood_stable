from flask import Flask, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask_mail import Mail
from flask_talisman import Talisman
from flask_jwt_extended.exceptions import JWTExtendedException

# Load environment variables
load_dotenv()

# Initialize extensions
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
talisman = Talisman()

def create_app(config_name='development'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Setup logging
    try:
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("Created logs directory")
    except Exception as e:
        print(f"Warning: Could not create logs directory: {str(e)}")
        
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
    mail.init_app(app)
    
    # Initialize Talisman with content security policy disabled (we'll implement our own headers)
    talisman.init_app(app, content_security_policy=None, force_https=False)
    
    # Request middleware - Check authentication before routing
    @app.before_request
    def check_protected_routes():
        # Skip for static files, auth routes, and non-protected pages
        if request.path.startswith(('/static', '/auth')) or request.path in ('/', '/register', '/contact'):
            app.logger.debug(f"Skipping auth check for public path: {request.path}")
            return None
        
        app.logger.debug(f"Checking auth for protected path: {request.path}")
            
        # For API routes, enforce JWT and return JSON errors
        if request.path.startswith('/api/'):
            try:
                verify_jwt_in_request()
                identity = get_jwt_identity()
                if request.path.startswith('/api/admin/') and (not isinstance(identity, dict) or identity.get('role') != 'admin'):
                    claims = get_jwt()
                    if claims.get("role") != 'admin':
                        app.logger.warning(f"Non-admin API access attempt: {identity} to {request.path}")
                        return jsonify({"error": "Admin privileges required for this API"}), 403
                
            except JWTExtendedException as e:
                app.logger.info(f"Unauthenticated API access attempt to {request.path}, Error: {str(e)}")
                return jsonify({"error": "Authentication required", "details": str(e)}), 401
            except Exception as e:
                app.logger.error(f"Error in API auth middleware for {request.path}: {str(e)}", exc_info=True)
                return jsonify({"error": "Authentication error", "details": str(e)}), 500
            return None

        # For HTML page routes (like /admin/dashboard, /volunteer/dashboard)
        elif request.path.startswith(('/admin', '/volunteer')):
            try:
                if 'Authorization' in request.headers:
                    verify_jwt_in_request()
                    identity = get_jwt_identity()
                    app.logger.debug(f"Token verified for HTML page access: {request.path}, Identity: {identity}")
                else:
                    app.logger.info(f"No Authorization header for HTML page: {request.path}. Client-side will check.")
            except JWTExtendedException as e:
                app.logger.info(f"Invalid token for HTML page access: {request.path}, Error: {str(e)}. Client-side will handle.")
            except Exception as e:
                app.logger.error(f"Error in HTML page auth middleware for {request.path}: {str(e)}", exc_info=True)
            
            return None

        # For any other routes not covered, default to allowing if not explicitly protected
        return None
    
    # Add response processor to set cache control headers
    @app.after_request
    def add_security_headers(response):
        # Set cache control headers to prevent caching of authenticated pages
        if request.path.startswith('/admin') or request.path.startswith('/volunteer'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
    # Initialize Firebase
    from app.firebase_config import initialize_firebase
    app.config['FIRESTORE_DB'] = initialize_firebase(app)
    app.logger.info('Firebase initialized')
    
    # Register blueprints
    # First, register main routes for views
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Register Firebase-based routes
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes_volunteers import volunteers_bp
    app.register_blueprint(volunteers_bp)
    
    from app.routes_inventory import inventory_bp
    app.register_blueprint(inventory_bp)
    
    from app.routes_shifts import shifts_bp
    app.register_blueprint(shifts_bp)
    
    from app.routes_admin import admin_bp
    app.register_blueprint(admin_bp)
    
    from app.notify import notify as notify_blueprint
    app.register_blueprint(notify_blueprint, url_prefix='/notify')
    
    return app
