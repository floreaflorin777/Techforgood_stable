from flask import current_app
from app.models import Notification, db, User
from datetime import datetime
import os

class NotificationService:
    def __init__(self):
        pass

    def send_email(self, to_email, subject, message):
        # Basic email sending implementation
        print(f"Email sent to {to_email}: {subject} - {message}")
        return True

    def create_notification(self, user_id, message, notification_type):
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
        notification = self.create_notification(user.id, message, notification_type)
        
        try:
            if notification_type == 'email':
                self.send_email(user.email, "Food Bank Notification", message)
            
            notification.status = 'sent'
            notification.sent_at = datetime.utcnow()
        except Exception as e:
            notification.status = 'failed'
            current_app.logger.error(f"Notification failed: {str(e)}")
        
        db.session.commit()
        return notification

    def send_shift_notification(self, volunteer, shift):
        message = f"New shift assigned: {shift.start_time} to {shift.end_time}"
        self.send_notification(volunteer, message, 'email')

    def send_inventory_alert(self, item):
        message = f"Alert: {item.name} is running low. Current quantity: {item.quantity} {item.unit}"
        # Get all managers
        managers = User.query.filter_by(role='manager').all()
        for manager in managers:
            self.send_notification(manager, message, 'email')
