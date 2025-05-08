"""
Database connection utilities for the Food Bank Management System.
"""
from flask import current_app
import os

def get_database_url(app):
    """
    Get the appropriate database URL based on the environment.
    
    When running on PythonAnywhere, we can connect directly to the MySQL database
    without using an SSH tunnel.
    
    Returns:
        str: Database URL for SQLAlchemy
    """
    # Determine if running on PythonAnywhere by checking environment
    is_pythonanywhere = 'PYTHONANYWHERE_DOMAIN' in os.environ
    
    if is_pythonanywhere:
        # Direct connection for PythonAnywhere
        # Format: mysql+pymysql://username:password@hostname/database_name
        return (
            f"mysql+pymysql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@"
            f"{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
        )
    else:
        # For development environments, we might still use SSH tunneling
        from app.db_tunnel import get_tunneled_database_url
        return get_tunneled_database_url()
