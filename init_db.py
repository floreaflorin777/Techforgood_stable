from dotenv import load_dotenv
import os
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sshtunnel import SSHTunnelForwarder

# Load environment variables
load_dotenv()

def get_ssh_tunnel():
    return SSHTunnelForwarder(
        ('ssh.eu.pythonanywhere.com', 22),
        ssh_username='florinm12',
        ssh_password='1Q2w3e4r5t.',
        remote_bind_address=('florinm12.mysql.eu.pythonanywhere-services.com', 3306)
    )

def test_connection():
    try:
        # Create SSH tunnel
        with get_ssh_tunnel() as tunnel:
            # Test direct PyMySQL connection through tunnel
            connection = pymysql.connect(
                host='127.0.0.1',
                port=tunnel.local_bind_port,
                user='florinm12',
                password='Techforgood',
                database='florinm12$foodbank'
            )
            print("Direct PyMySQL connection successful!")
            connection.close()
            
            # Test SQLAlchemy connection through tunnel
            db_url = f"mysql+pymysql://florinm12:Techforgood@127.0.0.1:{tunnel.local_bind_port}/florinm12$foodbank"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                print("SQLAlchemy connection successful!")
                result = conn.execute("SELECT DATABASE()")
                print(f"Connected to database: {result.scalar()}")
            
    except Exception as e:
        print(f"Connection error: {str(e)}")
        raise

def init_database():
    from app import create_app, db
    from app.models import User, Volunteer, InventoryItem, Shift, Notification

    app = create_app()
    with app.app_context():
        try:
            # Test connection first
            test_connection()
            
            # Create all tables
            db.create_all()
            print("Database tables created successfully!")

            # Check if admin user exists
            admin = User.query.filter_by(email='admin@foodbank.com').first()
            if not admin:
                # Create admin user
                admin = User(
                    email='admin@foodbank.com',
                    role='admin'
                )
                admin.set_password('admin123')  # Remember to change this password
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
            else:
                print("Admin user already exists!")
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            db.session.rollback()
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        finally:
            db.session.close()

if __name__ == '__main__':
    init_database() 