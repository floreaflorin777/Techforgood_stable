from sshtunnel import SSHTunnelForwarder
from flask import current_app

def get_ssh_tunnel():
    """Create and return an SSH tunnel for database access."""
    return SSHTunnelForwarder(
        (current_app.config['SSH_HOST'], current_app.config['SSH_PORT']),
        ssh_username=current_app.config['SSH_USERNAME'],
        ssh_password=current_app.config['SSH_PASSWORD'],
        remote_bind_address=(current_app.config['DB_HOST'], current_app.config['DB_PORT'])
    )

def get_database_url():
    """Get the database URL through the SSH tunnel."""
    with get_ssh_tunnel() as tunnel:
        return f"mysql+pymysql://{current_app.config['DB_USER']}:{current_app.config['DB_PASSWORD']}@127.0.0.1:{tunnel.local_bind_port}/{current_app.config['DB_NAME']}" 