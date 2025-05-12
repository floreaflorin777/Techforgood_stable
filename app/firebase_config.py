import firebase_admin
from firebase_admin import credentials, firestore
import os
from flask import current_app

def initialize_firebase(app):
    """Initialize Firebase Admin SDK with credentials."""
    try:
        # Path to service account key JSON file
        if 'FIREBASE_CREDENTIALS' in os.environ:
            # Use environment variable if available
            cred = credentials.Certificate(os.environ.get('FIREBASE_CREDENTIALS'))
        else:
            # Use local file as fallback
            # First try the new credentials file
            cred_path = os.path.join(os.path.dirname(app.root_path), 'tech-for-good-3ef04-firebase-adminsdk-fbsvc-e8551a8e0c.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # Fall back to the original path
                cred_path = os.path.join(app.root_path, 'firebase-credentials.json')
                cred = credentials.Certificate(cred_path)
            
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        app.logger.info('Firebase initialized successfully')
        return db
    except Exception as e:
        app.logger.error(f'Firebase initialization failed: {str(e)}')
        raise e

def get_firestore_db():
    """Helper function to get Firestore client."""
    if not firebase_admin._apps:
        # If Firebase is not initialized yet, return None
        return None
    return firestore.client() 