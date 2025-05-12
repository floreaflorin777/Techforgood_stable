from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.firestore_dao import FirestoreDAO

class User:
    """User model for Firestore."""
    
    COLLECTION = 'users'
    
    @staticmethod
    def create(name, email, password, role, phone=None, notification_preferences=None):
        """Create a new user.
        
        Args:
            name: User's full name
            email: User's email (unique)
            password: Plain text password to be hashed
            role: User role (admin, manager, volunteer)
            phone: Optional phone number
            notification_preferences: Optional notification settings
            
        Returns:
            User document ID
        """
        user_data = {
            'name': name,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'phone': phone,
            'created_at': datetime.utcnow(),
            'is_active': True,
            'notification_preferences': notification_preferences or {}
        }
        
        return FirestoreDAO.create_document(User.COLLECTION, user_data)
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        return FirestoreDAO.get_document(User.COLLECTION, user_id)
    
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        users = FirestoreDAO.query_collection(
            User.COLLECTION, 
            filters=[('email', '==', email)], 
            limit=1
        )
        return users[0] if users else None
    
    @staticmethod
    def update(user_id, data):
        """Update user fields."""
        return FirestoreDAO.update_document(User.COLLECTION, user_id, data)
    
    @staticmethod
    def delete(user_id):
        """Delete a user."""
        return FirestoreDAO.delete_document(User.COLLECTION, user_id)
    
    @staticmethod
    def check_password(user_data, password):
        """Check if password matches hash."""
        return check_password_hash(user_data['password_hash'], password)

    @staticmethod
    def get_all():
        """Get all users."""
        return FirestoreDAO.query_collection(User.COLLECTION)

    @staticmethod
    def get_by_role(role):
        """Get users by role."""
        return FirestoreDAO.query_collection(
            User.COLLECTION,
            filters=[('role', '==', role)]
        )

class Volunteer:
    """Volunteer model for Firestore."""
    
    COLLECTION = 'volunteers'
    
    @staticmethod
    def create(user_id, availability=None, skills=None):
        """Create a volunteer profile."""
        volunteer_data = {
            'user_id': user_id,
            'availability': availability or {},
            'skills': skills or '',
            'created_at': datetime.utcnow()
        }
        
        return FirestoreDAO.create_document(Volunteer.COLLECTION, volunteer_data)
    
    @staticmethod
    def get_by_id(volunteer_id):
        """Get volunteer by ID."""
        return FirestoreDAO.get_document(Volunteer.COLLECTION, volunteer_id)
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get volunteer by user ID."""
        volunteers = FirestoreDAO.query_collection(
            Volunteer.COLLECTION, 
            filters=[('user_id', '==', user_id)], 
            limit=1
        )
        return volunteers[0] if volunteers else None
    
    @staticmethod
    def update(volunteer_id, data):
        """Update volunteer fields."""
        return FirestoreDAO.update_document(Volunteer.COLLECTION, volunteer_id, data)
    
    @staticmethod
    def delete(volunteer_id):
        """Delete a volunteer."""
        return FirestoreDAO.delete_document(Volunteer.COLLECTION, volunteer_id)
    
    @staticmethod
    def get_all():
        """Get all volunteers."""
        return FirestoreDAO.query_collection(Volunteer.COLLECTION)

class Shift:
    """Shift model for Firestore."""
    
    COLLECTION = 'shifts'
    
    @staticmethod
    def create(start_time, end_time, volunteer_id, created_by, status='pending', capacity=5):
        """Create a new shift."""
        shift_data = {
            'start_time': start_time,
            'end_time': end_time,
            'volunteer_id': volunteer_id,
            'status': status,
            'created_by': created_by,
            'created_at': datetime.utcnow(),
            'capacity': capacity,
            'volunteer_ids': [volunteer_id] if volunteer_id else []
        }
        
        return FirestoreDAO.create_document(Shift.COLLECTION, shift_data)
    
    @staticmethod
    def get_by_id(shift_id):
        """Get shift by ID."""
        return FirestoreDAO.get_document(Shift.COLLECTION, shift_id)
    
    @staticmethod
    def update(shift_id, data):
        """Update shift fields."""
        return FirestoreDAO.update_document(Shift.COLLECTION, shift_id, data)
    
    @staticmethod
    def delete(shift_id):
        """Delete a shift."""
        return FirestoreDAO.delete_document(Shift.COLLECTION, shift_id)
    
    @staticmethod
    def get_all():
        """Get all shifts."""
        return FirestoreDAO.query_collection(Shift.COLLECTION)
    
    @staticmethod
    def get_by_volunteer(volunteer_id):
        """Get shifts for a specific volunteer."""
        return FirestoreDAO.query_collection(
            Shift.COLLECTION,
            filters=[('volunteer_ids', 'array_contains', volunteer_id)]
        )
    
    @staticmethod
    def get_upcoming():
        """Get upcoming shifts."""
        now = datetime.utcnow()
        return FirestoreDAO.query_collection(
            Shift.COLLECTION,
            filters=[('start_time', '>=', now)],
            order_by='start_time',
            order_direction='asc'
        )

class InventoryItem:
    """Inventory item model for Firestore."""
    
    COLLECTION = 'inventory'
    
    @staticmethod
    def create(name, quantity, added_by, unit=None, category=None, expiry_date=None):
        """Create a new inventory item."""
        item_data = {
            'name': name,
            'quantity': quantity,
            'unit': unit,
            'category': category,
            'expiry_date': expiry_date,
            'added_by': added_by,
            'added_at': datetime.utcnow(),
            'last_updated': datetime.utcnow()
        }
        
        return FirestoreDAO.create_document(InventoryItem.COLLECTION, item_data)
    
    @staticmethod
    def get_by_id(item_id):
        """Get inventory item by ID."""
        return FirestoreDAO.get_document(InventoryItem.COLLECTION, item_id)
    
    @staticmethod
    def update(item_id, data):
        """Update inventory item fields."""
        # Add last updated timestamp
        data['last_updated'] = datetime.utcnow()
        return FirestoreDAO.update_document(InventoryItem.COLLECTION, item_id, data)
    
    @staticmethod
    def delete(item_id):
        """Delete an inventory item."""
        return FirestoreDAO.delete_document(InventoryItem.COLLECTION, item_id)
    
    @staticmethod
    def get_all():
        """Get all inventory items."""
        return FirestoreDAO.query_collection(InventoryItem.COLLECTION)
    
    @staticmethod
    def get_by_category(category):
        """Get inventory items by category."""
        return FirestoreDAO.query_collection(
            InventoryItem.COLLECTION,
            filters=[('category', '==', category)]
        )
    
    @staticmethod
    def get_low_stock(threshold=10):
        """Get low stock inventory items."""
        return FirestoreDAO.query_collection(
            InventoryItem.COLLECTION,
            filters=[('quantity', '<=', threshold)]
        )
    
    @staticmethod
    def get_expiring_soon(days=7):
        """Get inventory items expiring within specified days."""
        from datetime import timedelta
        expiry_threshold = datetime.utcnow() + timedelta(days=days)
        return FirestoreDAO.query_collection(
            InventoryItem.COLLECTION,
            filters=[
                ('expiry_date', '<=', expiry_threshold),
                ('expiry_date', '>=', datetime.utcnow())
            ]
        ) 