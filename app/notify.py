from flask import current_app
from app.models import Notification, db, User
from datetime import datetime
import os
from twilio.rest import Client

class NotificationService:
    def __init__(self):
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER')

    def send_email(self, to_email, subject, message):
        # Implement email sending logic here
        # You can use Flask-Mail or any other email service
        pass

    def send_whatsapp(self, to_number, message):
        try:
            message = self.twilio_client.messages.create(
                from_=f'whatsapp:{self.whatsapp_from}',
                body=message,
                to=f'whatsapp:{to_number}'
            )
            return True
        except Exception as e:
            current_app.logger.error(f"WhatsApp notification failed: {str(e)}")
            return False

    def send_sms(self, to_number, message):
        # Implement your preferred SMS service here
        # This is a placeholder that returns True to maintain compatibility
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
            elif notification_type == 'whatsapp':
                self.send_whatsapp(user.phone, message)
            elif notification_type == 'sms':
                self.send_sms(user.phone, message)
            
            notification.status = 'sent'
            notification.sent_at = datetime.utcnow()
        except Exception as e:
            notification.status = 'failed'
            current_app.logger.error(f"Notification failed: {str(e)}")
        
        db.session.commit()
        return notification

    def send_shift_notification(self, volunteer, shift):
        message = f"New shift assigned: {shift.start_time.strftime('%Y-%m-%d %H:%M')} to {shift.end_time.strftime('%H:%M')}"
        return self.send_notification(volunteer, message, 'sms')

    def send_inventory_alert(self, item):
        message = f"Alert: {item.name} is running low. Current quantity: {item.quantity} {item.unit}"
        # Get all managers
        managers = User.query.filter_by(role='manager').all()
        for manager in managers:
            self.send_notification(manager, message, 'email')
