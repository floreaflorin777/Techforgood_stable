from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from flask_mail import Message
from app import mail
from app.firestore_models import User
from app.firestore_dao import FirestoreDAO

notify = Blueprint('notify', __name__)

class NotificationService:
    def __init__(self):
        self.COLLECTION = 'notifications'
    
    def send_email(self, to_email, subject, message):
        """Send an actual email using Flask-Mail."""
        try:
            msg = Message(subject=subject,
                          recipients=[to_email],
                          body=message)
            mail.send(msg)
            current_app.logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            current_app.logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    def create_notification(self, user_id, message, notification_type):
        """Create a notification entry in Firestore."""
        try:
            notification_data = {
                'user_id': user_id,
                'message': message,
                'type': notification_type,
                'status': 'pending',
                'created_at': datetime.utcnow(),
                'sent_at': None
            }
            
            notification_id = FirestoreDAO.create_document(self.COLLECTION, notification_data)
            return {
                'id': notification_id,
                **notification_data
            }
        except Exception as e:
            current_app.logger.error(f"Error creating notification: {str(e)}")
            return None

    def send_notification(self, user, message, notification_type):
        """Send a notification to the user (email or other types)."""
        notification = self.create_notification(user['id'], message, notification_type)
        
        if not notification:
            return None
        
        try:
            if notification_type == 'email':
                if self.send_email(user['email'], "Food Bank Notification", message):
                    # Update notification status
                    FirestoreDAO.update_document(
                        self.COLLECTION, 
                        notification['id'], 
                        {
                            'status': 'sent',
                            'sent_at': datetime.utcnow()
                        }
                    )
                    notification['status'] = 'sent'
                    notification['sent_at'] = datetime.utcnow()
                else:
                    # Update notification status to failed
                    FirestoreDAO.update_document(
                        self.COLLECTION, 
                        notification['id'], 
                        {'status': 'failed'}
                    )
                    notification['status'] = 'failed'
            
            # Add other notification types if needed (SMS, Push, etc.)
            
            return notification

        except Exception as e:
            # Update notification status to failed
            FirestoreDAO.update_document(
                self.COLLECTION, 
                notification['id'], 
                {'status': 'failed'}
            )
            current_app.logger.error(f"Notification failed: {str(e)}")
            return notification

    def send_shift_notification(self, volunteer_id, shift_id):
        """Send a notification about assigned shift to a volunteer."""
        try:
            # Get volunteer and associated user
            from app.firestore_models import Volunteer, Shift
            
            volunteer = Volunteer.get_by_id(volunteer_id)
            if not volunteer:
                current_app.logger.error(f"Cannot send shift notification: volunteer with ID {volunteer_id} not found")
                return None
                
            user = User.get_by_id(volunteer['user_id'])
            if not user:
                current_app.logger.error(f"Cannot send shift notification: user associated with volunteer ID {volunteer_id} not found")
                return None
            
            shift = Shift.get_by_id(shift_id)
            if not shift:
                current_app.logger.error(f"Cannot send shift notification: shift with ID {shift_id} not found")
                return None
                
            # Format dates for message
            start_time = shift['start_time']
            end_time = shift['end_time']
            
            if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                message = f"New shift assigned: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"
            else:
                message = f"New shift assigned: {start_time} to {end_time}"
                
            return self.send_notification(user, message, 'email')
        except Exception as e:
            current_app.logger.error(f"Error sending shift notification: {str(e)}")
            return None

    def send_inventory_alert(self, item_id):
        """Send an inventory alert to managers when an item is low in stock."""
        try:
            # Get the inventory item
            from app.firestore_models import InventoryItem
            
            item = InventoryItem.get_by_id(item_id)
            if not item:
                current_app.logger.error(f"Cannot send inventory alert: item with ID {item_id} not found")
                return None
                
            message = f"Alert: {item['name']} is running low. Current quantity: {item['quantity']} {item.get('unit', '')}"
            
            # Get all managers
            managers = User.get_by_role('manager')
            results = []
            
            for manager in managers:
                result = self.send_notification(manager, message, 'email')
                results.append(result)
                
            return results
        except Exception as e:
            current_app.logger.error(f"Error sending inventory alert: {str(e)}")
            return None

notification_service = NotificationService()

@notify.route('/api/notifications/<user_id>', methods=['GET'])
def get_user_notifications(user_id):
    try:
        # Query notifications for user
        notifications = FirestoreDAO.query_collection(
            'notifications',
            filters=[('user_id', '==', user_id)],
            order_by='created_at',
            order_direction='desc'
        )
        
        # Format dates for JSON serialization
        for notification in notifications:
            if 'created_at' in notification and notification['created_at'] and isinstance(notification['created_at'], datetime):
                notification['created_at'] = notification['created_at'].isoformat()
                
            if 'sent_at' in notification and notification['sent_at'] and isinstance(notification['sent_at'], datetime):
                notification['sent_at'] = notification['sent_at'].isoformat()
        
        return jsonify(notifications), 200
    except Exception as e:
        current_app.logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve notifications', 'message': str(e)}), 500
