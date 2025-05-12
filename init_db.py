#!/usr/bin/env python3
"""
Initialize Firebase Firestore with sample data
"""
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

def init_firebase():
    """Initialize Firebase Admin SDK"""
    # Path to service account key JSON file
    cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')
    
    try:
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        return None

def create_sample_data(db):
    """Create sample data in Firestore"""
    # Add sample users
    users_ref = db.collection('users')
    volunteers_ref = db.collection('volunteers')
    shifts_ref = db.collection('shifts')
    inventory_ref = db.collection('inventory')
    
    # Check if users already exist to avoid duplicates
    if len(list(users_ref.limit(1).stream())) > 0:
        print("Database already contains data. Skipping sample data creation.")
        return
    
    print("Creating sample data...")
    
    # Create admin user
    admin_user = {
        'name': 'Admin User',
        'email': 'admin@example.com',
        'password_hash': generate_password_hash('admin123'),
        'role': 'admin',
        'phone': '+1234567890',
        'is_active': True,
        'created_at': datetime.datetime.utcnow(),
        'notification_preferences': {}
    }
    admin_ref = users_ref.add(admin_user)[1]
    print(f"Created admin user with ID: {admin_ref.id}")
    
    # Create manager user
    manager_user = {
        'name': 'Manager User',
        'email': 'manager@example.com',
        'password_hash': generate_password_hash('manager123'),
        'role': 'manager',
        'phone': '+1234567891',
        'is_active': True,
        'created_at': datetime.datetime.utcnow(),
        'notification_preferences': {}
    }
    manager_ref = users_ref.add(manager_user)[1]
    print(f"Created manager user with ID: {manager_ref.id}")
    
    # Create volunteer users and profiles
    for i in range(1, 4):
        # Create user
        volunteer_user = {
            'name': f'Volunteer {i}',
            'email': f'volunteer{i}@example.com',
            'password_hash': generate_password_hash(f'volunteer{i}'),
            'role': 'volunteer',
            'phone': f'+123456789{i+1}',
            'is_active': True,
            'created_at': datetime.datetime.utcnow(),
            'notification_preferences': {}
        }
        volunteer_user_ref = users_ref.add(volunteer_user)[1]
        print(f"Created volunteer user {i} with ID: {volunteer_user_ref.id}")
        
        # Create volunteer profile
        volunteer_profile = {
            'user_id': volunteer_user_ref.id,
            'availability': {
                'monday': ['09:00-17:00'],
                'wednesday': ['09:00-17:00'],
                'friday': ['09:00-17:00']
            },
            'skills': f'Skill {i}, Skill {i+1}',
            'created_at': datetime.datetime.utcnow()
        }
        volunteer_profile_ref = volunteers_ref.add(volunteer_profile)[1]
        print(f"Created volunteer profile {i} with ID: {volunteer_profile_ref.id}")
        
        # Create shifts for volunteer
        for j in range(1, 3):
            day_offset = j * 2  # 2, 4, 6 days from now
            shift_date = datetime.datetime.utcnow() + datetime.timedelta(days=day_offset)
            shift = {
                'start_time': shift_date.replace(hour=9, minute=0, second=0, microsecond=0),
                'end_time': shift_date.replace(hour=17, minute=0, second=0, microsecond=0),
                'volunteer_id': volunteer_profile_ref.id,
                'volunteer_ids': [volunteer_profile_ref.id],
                'status': 'confirmed',
                'created_by': admin_ref.id,
                'created_at': datetime.datetime.utcnow(),
                'capacity': 3
            }
            shift_ref = shifts_ref.add(shift)[1]
            print(f"Created shift {j} for volunteer {i} with ID: {shift_ref.id}")
    
    # Create inventory items
    inventory_items = [
        {
            'name': 'Rice',
            'quantity': 100,
            'unit': 'kg',
            'category': 'non-perishable',
            'expiry_date': (datetime.datetime.utcnow() + datetime.timedelta(days=365)),
            'added_by': manager_ref.id,
            'added_at': datetime.datetime.utcnow(),
            'last_updated': datetime.datetime.utcnow()
        },
        {
            'name': 'Beans',
            'quantity': 50,
            'unit': 'kg',
            'category': 'non-perishable',
            'expiry_date': (datetime.datetime.utcnow() + datetime.timedelta(days=365)),
            'added_by': manager_ref.id,
            'added_at': datetime.datetime.utcnow(),
            'last_updated': datetime.datetime.utcnow()
        },
        {
            'name': 'Milk',
            'quantity': 20,
            'unit': 'l',
            'category': 'perishable',
            'expiry_date': (datetime.datetime.utcnow() + datetime.timedelta(days=7)),
            'added_by': manager_ref.id,
            'added_at': datetime.datetime.utcnow(),
            'last_updated': datetime.datetime.utcnow()
        },
        {
            'name': 'Bread',
            'quantity': 5,
            'unit': 'units',
            'category': 'perishable',
            'expiry_date': (datetime.datetime.utcnow() + datetime.timedelta(days=2)),
            'added_by': manager_ref.id,
            'added_at': datetime.datetime.utcnow(),
            'last_updated': datetime.datetime.utcnow()
        }
    ]
    
    for item in inventory_items:
        item_ref = inventory_ref.add(item)[1]
        print(f"Created inventory item {item['name']} with ID: {item_ref.id}")
    
    print("Sample data creation completed!")

if __name__ == "__main__":
    print("Initializing Firestore database...")
    db = init_firebase()
    
    if db:
        create_sample_data(db)
        print("Firestore initialization complete.")
    else:
        print("Failed to initialize Firestore database.")
