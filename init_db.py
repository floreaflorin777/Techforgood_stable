from dotenv import load_dotenv
import os
import pymysql
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import socket

# Load environment variables
load_dotenv()

def is_running_on_pythonanywhere():
    """Check if the code is running on PythonAnywhere"""
    return 'PYTHONANYWHERE_DOMAIN' in os.environ

def get_database_credentials():
    """Get database credentials from environment variables"""
    db_user = os.getenv('DB_USER', 'florinm12')
    db_password = os.getenv('DB_PASSWORD', 'Techforgood')
    db_host = os.getenv('DB_HOST', 'florinm12.mysql.eu.pythonanywhere-services.com')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_name = os.getenv('DB_NAME', 'florinm12$foodbank')
    return db_user, db_password, db_host, db_port, db_name

def test_direct_connection():
    """Test direct connection to the database (for PythonAnywhere)"""
    db_user, db_password, db_host, db_port, db_name = get_database_credentials()
    
    try:
        # Test direct PyMySQL connection
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        print("Direct PyMySQL connection successful!")
        connection.close()
        
        # Test SQLAlchemy connection
        db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("SQLAlchemy connection successful!")
            result = conn.execute(text("SELECT DATABASE()"))
            print(f"Connected to database: {result.scalar()}")
        return True
    except Exception as e:
        print(f"Direct connection error: {str(e)}")
        return False

def init_database():
    from app import create_app, db
    from app.models import User, Volunteer, InventoryItem, Shift, Notification

    app = create_app()
    with app.app_context():
        try:
            # Test connection first
            test_direct_connection()
            
            # Create all tables
            db.create_all()
            print("Database tables created successfully!")

            # Check if admin user exists
            admin = User.query.filter_by(email='admin@foodbank.com').first()
            if not admin:
                # Create admin user
                admin = User(
                    name='Admin',
                    email='admin@foodbank.com',
                    role='admin'
                )
                admin.set_password('admin123')  # Remember to change this password
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
            else:
                print("Admin user already exists!")
                
            # Create a sample manager if none exists
            manager = User.query.filter_by(email='manager@foodbank.com').first()
            if not manager:
                manager = User(
                    name='Manager',
                    email='manager@foodbank.com',
                    role='manager',
                    phone='+1234567890'
                )
                manager.set_password('manager123')
                db.session.add(manager)
                db.session.commit()
                print("Manager user created successfully!")
            
            # Create a sample volunteer if none exists
            volunteer_user = User.query.filter_by(email='volunteer@foodbank.com').first()
            if not volunteer_user:
                volunteer_user = User(
                    name='John Volunteer',
                    email='volunteer@foodbank.com',
                    role='volunteer',
                    phone='+9876543210'
                )
                volunteer_user.set_password('volunteer123')
                db.session.add(volunteer_user)
                db.session.commit()
                
                # Check if volunteer profile exists
                volunteer = Volunteer.query.filter_by(user_id=volunteer_user.id).first()
                if not volunteer:
                    volunteer = Volunteer(
                        user_id=volunteer_user.id,
                        availability=json.dumps({
                            "monday": ["09:00-17:00"],
                            "wednesday": ["13:00-18:00"],
                            "friday": ["09:00-14:00"]
                        }),
                        skills="Inventory management, Food distribution"
                    )
                    db.session.add(volunteer)
                    db.session.commit()
                    print("Sample volunteer created successfully!")
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            db.session.rollback()
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        finally:
            db.session.close()

if __name__ == '__main__':
    init_database()
