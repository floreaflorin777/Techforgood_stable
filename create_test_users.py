from app import create_app
from app.firestore_models import User, Volunteer
import os

def create_users():
    """Create test volunteer users"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Create volunteer users with different availabilities
        volunteers = [
            {
                "name": "John Smith",
                "email": "john@volunteer.com",
                "password": "password123",
                "phone": "1234567890",
                "availability": {
                    "monday": ["morning", "afternoon"],
                    "wednesday": ["afternoon"],
                    "friday": ["morning"]
                },
                "skills": "Food sorting, Customer service"
            },
            {
                "name": "Sarah Johnson",
                "email": "sarah@volunteer.com",
                "password": "password123",
                "phone": "9876543210",
                "availability": {
                    "tuesday": ["morning"],
                    "thursday": ["afternoon", "evening"],
                    "saturday": ["morning", "afternoon"]
                },
                "skills": "Inventory management, Driving"
            },
            {
                "name": "Mike Williams",
                "email": "mike@volunteer.com",
                "password": "password123",
                "phone": "5554443333",
                "availability": {
                    "monday": ["evening"],
                    "wednesday": ["evening"],
                    "sunday": ["morning", "afternoon"]
                },
                "skills": "Heavy lifting, Organization"
            }
        ]
        
        for volunteer in volunteers:
            # Check if volunteer user already exists
            email = volunteer["email"]
            existing_user = User.get_by_email(email)
            
            if not existing_user:
                print(f"Creating volunteer user with email: {email}")
                
                # Create user account
                volunteer_id = User.create(
                    name=volunteer["name"],
                    email=email,
                    password=volunteer["password"],
                    role="volunteer",
                    phone=volunteer["phone"]
                )
                
                # Create volunteer profile
                volunteer_profile_id = Volunteer.create(
                    user_id=volunteer_id,
                    availability=volunteer["availability"],
                    skills=volunteer["skills"]
                )
                
                print(f"Volunteer user created with ID: {volunteer_id}")
                print(f"Volunteer profile created with ID: {volunteer_profile_id}")
            else:
                print(f"Volunteer with email {email} already exists with ID: {existing_user.get('id')}")

if __name__ == "__main__":
    create_users() 