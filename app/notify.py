from flask import current_app
from app.models import Notification, db, User
from flask_mail import Message
from datetime import datetime
from app import mail  # Import mail instance from app

class NotificationService:
    def __init__(self):
        pass

    def send_email(self, to_email, subject, message):
        """Send an actual email using Flask-Mail."""
        try:
            msg = Message(subject=subject,
                          recipients=[to_email],  # You can send to multiple recipients by passing a list
                          body=message)
            mail.send(msg)  # Flask-Mail will handle sending the email
            current_app.logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            current_app.logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    def create_notification(self, user_id, message, notification_type):
        """Create a notification entry in the database."""
        notification = Notification(
            user_id=user_id,
            message=message,
            type=notification_type,
            status='pending'
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    def send_notification(self, user, message, notification_type):
        """Send a notification to the user (email or other types)."""
        notification = self.create_notification(user.id, message, notification_type)
        
        try:
            if notification_type == 'email':
                if self.send_email(user.email, "Food Bank Notification", message):
                    notification.status = 'sent'
                    notification.sent_at = datetime.utcnow()
                else:
                    notification.status = 'failed'
            
            # Add other notification types if needed (SMS, Push, etc.)
            db.session.commit()
            return notification

        except Exception as e:
            notification.status = 'failed'
            current_app.logger.error(f"Notification failed: {str(e)}")
            db.session.commit()
            return notification

    def send_shift_notification(self, volunteer, shift):
        """Send a notification about assigned shift to a volunteer."""
        # Get the associated user from the volunteer profile
        user = volunteer.user
        
        if not user:
            current_app.logger.error(f"Cannot send shift notification: volunteer (id: {volunteer.id}) has no associated user")
            return None
            
        message = f"New shift assigned: {shift.start_time} to {shift.end_time}"
        return self.send_notification(user, message, 'email')

    def send_inventory_alert(self, item):
        """Send an inventory alert to managers when an item is low in stock."""
        message = f"Alert: {item.name} is running low. Current quantity: {item.quantity} {item.unit}"
        
        # Get all managers
        managers = User.query.filter_by(role='manager').all()
        for manager in managers:
            self.send_notification(manager, message, 'email')
