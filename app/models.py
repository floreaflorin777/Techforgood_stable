from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin, manager, volunteer
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    notification_preferences = db.Column(db.JSON)  # Store notification preferences

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Volunteer(db.Model):
    """
    Volunteer model that establishes a one-to-one relationship with User,
    rather than inheritance which can cause issues with SQLAlchemy.
    """
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    availability = db.Column(db.JSON)  # Store weekly availability
    skills = db.Column(db.String(200))  # Store volunteer skills
    
    # Establish relationship with User
    user = db.relationship('User', backref=db.backref('volunteer_profile', uselist=False))
    
    # Establish relationship with Shift
    shifts = db.relationship('Shift', backref='volunteer_profile', lazy=True)
    
    @property
    def name(self):
        return self.user.name if self.user else None
    
    @property
    def email(self):
        return self.user.email if self.user else None
    
    @property
    def phone(self):
        return self.user.phone if self.user else None

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    capacity = db.Column(db.Integer, default=5)
    
    # Add relationship to the user who created the shift
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_shifts')
    
    # Add many-to-many relationship
    shift_volunteers = db.Table('shift_volunteers',
        db.Column('shift_id', db.Integer, db.ForeignKey('shift.id')),
        db.Column('volunteer_id', db.Integer, db.ForeignKey('volunteer.id'))
    )
    
    volunteers = db.relationship('Volunteer', secondary=shift_volunteers, backref='shifts')

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20))  # kg, pieces, etc.
    category = db.Column(db.String(50))  # perishable, non-perishable, etc.
    expiry_date = db.Column(db.DateTime)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50))  # email, whatsapp, system
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    feedback_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship with User (optional)
    user = db.relationship('User', backref='feedback')
