from flask import Blueprint, jsonify, request, current_app
from app.models import db, User, Volunteer, InventoryItem, Shift
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.notify import NotificationService
from datetime import datetime, timedelta
import json
import re
from sqlalchemy import func

main = Blueprint('main', __name__)
notification_service = NotificationService()

# Validation functions
def validate_email(email):
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format"
    return True, None

def validate_phone(phone):
    if phone and not re.match(r"^\+?[1-9]\d{1,14}$", phone):
        return False, "Invalid phone number format"
    return True, None

def validate_shift_times(start_time, end_time):
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        if start >= end:
            return False, "End time must be after start time"
        if (end - start).total_seconds() > 24 * 3600:
            return False, "Shift cannot be longer than 24 hours"
        return True, None
    except ValueError:
        return False, "Invalid date format"

# Error handlers
@main.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@main.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@main.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@main.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# Authentication middleware
def require_role(role):
    def decorator(f):
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()
            if current_user['role'] != role:
                return jsonify({'error': 'Forbidden', 'message': f'Requires {role} role'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Home route
@main.route('/')
def home():
    return jsonify({"message": "tech for good API is working!"})

# --------------------
# Volunteer Routes
# --------------------

@main.route('/api/volunteers', methods=['GET'])
@jwt_required()
def get_volunteers():
    volunteers = Volunteer.query.all()
    return jsonify([{
        'id': v.id,
        'name': v.name,
        'email': v.email,
        'phone': v.phone,
        'availability': json.loads(v.availability) if v.availability else None,
        'skills': v.skills
    } for v in volunteers]), 200

@main.route('/api/volunteers/<int:volunteer_id>', methods=['GET'])
@jwt_required()
def get_volunteer(volunteer_id):
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    return jsonify({
        'id': volunteer.id,
        'name': volunteer.name,
        'email': volunteer.email,
        'phone': volunteer.phone,
        'availability': json.loads(volunteer.availability) if volunteer.availability else None,
        'skills': volunteer.skills
    }), 200

@main.route('/api/volunteers', methods=['POST'])
@require_role('admin')
def add_volunteer():
    data = request.json
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400

    email_valid, email_error = validate_email(data['email'])
    if not email_valid:
        return jsonify({'error': email_error}), 400

    if 'phone' in data:
        phone_valid, phone_error = validate_phone(data['phone'])
        if not phone_valid:
            return jsonify({'error': phone_error}), 400

    volunteer = Volunteer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        availability=json.dumps(data.get('availability', {})),
        skills=data.get('skills')
    )
    volunteer.set_password(data.get('password', 'default_password'))
    
    db.session.add(volunteer)
    db.session.commit()
    current_app.logger.info(f'New volunteer added: {volunteer.email}')
    return jsonify({'message': 'Volunteer added successfully', 'id': volunteer.id}), 201

# Delete a volunteer
@main.route('/volunteers/<int:volunteer_id>', methods=['DELETE'])
def delete_volunteer(volunteer_id):
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    db.session.delete(volunteer)
    db.session.commit()
    return jsonify({"message": f"Volunteer with id {volunteer_id} deleted."}), 200

# --------------------
# Shift Routes
# --------------------

@main.route('/api/shifts', methods=['GET'])
@jwt_required()
def get_shifts():
    shifts = Shift.query.all()
    return jsonify([{
        'id': s.id,
        'start_time': s.start_time.isoformat(),
        'end_time': s.end_time.isoformat(),
        'volunteer_id': s.volunteer_id,
        'status': s.status
    } for s in shifts]), 200

@main.route('/api/shifts', methods=['POST'])
@require_role('admin')
def create_shift():
    data = request.json
    try:
        times_valid, time_error = validate_shift_times(data['start_time'], data['end_time'])
        if not times_valid:
            return jsonify({'error': time_error}), 400

        shift = Shift(
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            volunteer_id=data['volunteer_id'],
            created_by=get_jwt_identity()['id']
        )
        db.session.add(shift)
        db.session.commit()
        
        volunteer = Volunteer.query.get(data['volunteer_id'])
        notification_service.send_shift_notification(volunteer, shift)
        current_app.logger.info(f'New shift created for volunteer {volunteer.email}')
        
        return jsonify({'message': 'Shift created successfully', 'id': shift.id}), 201
    except Exception as e:
        current_app.logger.error(f'Error creating shift: {str(e)}')
        return jsonify({'error': 'Invalid shift data', 'message': str(e)}), 400

# --------------------
# Inventory Routes
# --------------------

@main.route('/api/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    items = InventoryItem.query.all()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'quantity': item.quantity,
        'unit': item.unit,
        'category': item.category,
        'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None
    } for item in items]), 200

@main.route('/api/inventory', methods=['POST'])
@require_role('manager')
def add_inventory_item():
    data = request.json
    try:
        if not data.get('name') or not data.get('quantity'):
            return jsonify({'error': 'Missing required fields'}), 400

        if not isinstance(data['quantity'], (int, float)) or data['quantity'] < 0:
            return jsonify({'error': 'Quantity must be a positive number'}), 400

        item = InventoryItem(
            name=data['name'],
            quantity=data['quantity'],
            unit=data.get('unit'),
            category=data.get('category'),
            expiry_date=datetime.fromisoformat(data['expiry_date']) if data.get('expiry_date') else None,
            added_by=get_jwt_identity()['id']
        )
        db.session.add(item)
        db.session.commit()
        current_app.logger.info(f'New inventory item added: {item.name}')
        return jsonify({'message': 'Item added successfully', 'id': item.id}), 201
    except Exception as e:
        current_app.logger.error(f'Error adding inventory item: {str(e)}')
        return jsonify({'error': 'Invalid item data', 'message': str(e)}), 400

@main.route('/api/inventory/<int:item_id>', methods=['PUT'])
@require_role('manager')
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    data = request.json
    
    try:
        if 'quantity' in data:
            item.quantity = data['quantity']
        if 'name' in data:
            item.name = data['name']
        if 'unit' in data:
            item.unit = data['unit']
        if 'category' in data:
            item.category = data['category']
        if 'expiry_date' in data:
            item.expiry_date = datetime.fromisoformat(data['expiry_date'])
        
        db.session.commit()
        return jsonify({'message': 'Item updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Invalid update data', 'message': str(e)}), 400

# Analytics Routes
@main.route('/api/analytics/volunteers', methods=['GET'])
@jwt_required()
def volunteer_analytics():
    total_volunteers = Volunteer.query.count()
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_volunteers = db.session.query(Volunteer).join(Shift).filter(
        Shift.start_time >= thirty_days_ago
    ).distinct().count()
    
    weekly_hours = db.session.query(
        func.date_trunc('week', Shift.start_time).label('week'),
        func.sum(Shift.end_time - Shift.start_time).label('total_hours')
    ).group_by('week').order_by('week').all()
    
    return jsonify({
        'total_volunteers': total_volunteers,
        'active_volunteers': active_volunteers,
        'weekly_hours': [{
            'week': week.strftime('%Y-%m-%d'),
            'hours': total_hours.total_seconds() / 3600
        } for week, total_hours in weekly_hours]
    })

@main.route('/api/analytics/inventory', methods=['GET'])
@jwt_required()
def inventory_analytics():
    total_items = InventoryItem.query.count()
    
    items_by_category = db.session.query(
        InventoryItem.category,
        func.count(InventoryItem.id).label('count'),
        func.sum(InventoryItem.quantity).label('total_quantity')
    ).group_by(InventoryItem.category).all()
    
    expiring_soon = InventoryItem.query.filter(
        InventoryItem.expiry_date <= datetime.utcnow() + timedelta(days=7)
    ).count()
    
    return jsonify({
        'total_items': total_items,
        'items_by_category': [{
            'category': category,
            'count': count,
            'total_quantity': total_quantity
        } for category, count, total_quantity in items_by_category],
        'expiring_soon': expiring_soon
    })
