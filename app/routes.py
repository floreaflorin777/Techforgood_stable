from flask import Blueprint, jsonify, request, current_app, render_template, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json
import re
from sqlalchemy import func
import os

main = Blueprint('main', __name__)

# Authentication middleware
def require_role(role):
    def decorator(f):
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            if current_user['role'] != role:
                return jsonify({'error': 'Forbidden', 'message': f'Requires {role} role'}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__  # Preserve the original function name
        return wrapper
    return decorator

# Home route
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/admin/dashboard')
@require_role('admin')
def admin_dashboard():
    return send_from_directory(os.path.join(os.getcwd()), 'admin.html')

@main.route('/volunteer/dashboard')
def volunteer_dashboard():
    return render_template('volunteer_dashboard.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

# Import models and services after Blueprint creation to avoid circular imports
from app.models import db, User, Volunteer, InventoryItem, Shift
from app.notify import NotificationService

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


# --------------------
# Volunteer Routes
# --------------------

@main.route('/api/volunteers', methods=['GET'])
@jwt_required()
def get_volunteers():
    volunteers = Volunteer.query.all()
    return jsonify([{
        'id': v.id,
        'user_id': v.user_id,
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

    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        role='volunteer'
    )
    user.set_password(data.get('password', 'default_password'))
    
    volunteer = Volunteer(
        availability=json.dumps(data.get('availability', {})),
        skills=data.get('skills')
    )
    
    db.session.add(user)
    db.session.flush()  
    
    volunteer.user_id = user.id
    db.session.add(volunteer)
    db.session.commit()
    
    current_app.logger.info(f'New volunteer added: {user.email}')
    return jsonify({
        'message': 'Volunteer added successfully', 
        'id': volunteer.id,
        'user_id': user.id
    }), 201

@main.route('/api/volunteers/<int:volunteer_id>', methods=['DELETE'])
@require_role('admin')
def delete_volunteer(volunteer_id):
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    
    user = User.query.get(volunteer.user_id)
    
    db.session.delete(volunteer)
    
    if user:
        if user.role == 'volunteer':
            db.session.delete(user)
        else:
            current_app.logger.info(f"User {user.email} has role {user.role}, not deleting user record")
    
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
    
@main.route('/api/shifts/recent', methods=['GET'])
@require_role('admin')
@jwt_required()
def recent_shifts():
    recent = Shift.query.order_by(Shift.start_time.desc()).limit(10).all()
    result = []
    for shift in recent:
        volunteer_name = getattr(getattr(shift, 'volunteer', None), 'name', 'Unknown')
        result.append({
            "volunteer_name": volunteer_name,
            "start_time": shift.start_time.isoformat() if shift.start_time else "",
            "status": shift.status
        })
    return jsonify({"shifts": result})

# Edit a shift
@main.route('/api/shifts/<int:shift_id>', methods=['PUT'])
@require_role('admin')
def edit_shift(shift_id):
    data = request.json
    try:
        times_valid, time_error = validate_shift_times(data['start_time'], data['end_time'])
        if not times_valid:
            return jsonify({'error': time_error}), 400

        shift = Shift.query.get(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404

        shift.start_time = datetime.fromisoformat(data['start_time'])
        shift.end_time = datetime.fromisoformat(data['end_time'])
        shift.volunteer_id = data.get('volunteer_id', shift.volunteer_id)

        db.session.commit()
        
        current_app.logger.info(f'Shift updated: {shift_id}')
        return jsonify({'message': 'Shift updated successfully'}), 200
    except Exception as e:
        current_app.logger.error(f'Error updating shift: {str(e)}')
        return jsonify({'error': 'Failed to update shift', 'message': str(e)}), 400

# Delete a shift
@main.route('/api/shifts/<int:shift_id>', methods=['DELETE'])
@require_role('admin')
def delete_shift(shift_id):
    try:
        shift = Shift.query.get(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404

        db.session.delete(shift)
        db.session.commit()

        current_app.logger.info(f'Shift deleted: {shift_id}')
        return jsonify({'message': 'Shift deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f'Error deleting shift: {str(e)}')
        return jsonify({'error': 'Failed to delete shift', 'message': str(e)}), 400


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
    if not data or not data.get('name') or not data.get('quantity'):
        return jsonify({'error': 'Missing required fields'}), 400

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
    return jsonify({'message': 'Inventory item added successfully', 'id': item.id}), 201

@main.route('/api/inventory/<int:item_id>', methods=['PUT'])
@require_role('manager')
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    data = request.json

    if 'quantity' in data:
        item.quantity = data['quantity']
    if 'unit' in data:
        item.unit = data['unit']
    if 'category' in data:
        item.category = data['category']
    if 'expiry_date' in data:
        item.expiry_date = datetime.fromisoformat(data['expiry_date'])

    db.session.commit()
    current_app.logger.info(f'Inventory item updated: {item.name}')
    return jsonify({'message': 'Inventory item updated successfully'}), 200

@main.route('/api/analytics/inventory', methods=['GET'])
@require_role('admin')
@jwt_required()
def inventory_analytics():
    total_items = InventoryItem.query.count()
    # Example: low stock = quantity < 10
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity < 10).all()
    return jsonify({
        "total_items": total_items,
        "low_stock_items": len(low_stock_items),
        "low_stock_items_list": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "min_quantity": item.min_quantity
            } for item in low_stock_items
        ]
    }), 200

# --------------------
# Analytics Routes
# --------------------

@main.route('/api/analytics/volunteers', methods=['GET'])
@jwt_required()
def volunteers_analytics():
    total_volunteers = Volunteer.query.count()
    active_volunteers = Volunteer.query.join(User, Volunteer.user_id == User.id).filter(User.is_active == True).count()
    
    # Shifts this month
    shifts_this_month = Shift.query.filter(
        Shift.start_time >= datetime.utcnow().replace(day=1),
        Shift.start_time < (datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1)
    ).count()

    # Additional analytics
    volunteers_with_shifts = db.session.query(Volunteer.id).distinct().join(Shift).count()
    
    return jsonify({
        'total_volunteers': total_volunteers,
        'active_volunteers': active_volunteers,
        'shifts_this_month': shifts_this_month,
        'volunteers_with_shifts': volunteers_with_shifts
    }), 200

@main.route('/api/analytics/inventory', methods=['GET'])
@jwt_required()
def inventory_analytics():
    total_items = InventoryItem.query.count()
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity < 10).count()
    expiring_soon = InventoryItem.query.filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= datetime.utcnow() + timedelta(days=7)
    ).count()

    return jsonify({
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'expiring_soon': expiring_soon
    }), 200

@main.route('/api/analytics/volunteers', methods=['GET'])
@jwt_required()
def volunteers_analytics():
    total_volunteers = Volunteer.query.count()
    active_volunteers = Volunteer.query.filter_by(status='active').count()
    return jsonify({
        "total_volunteers": total_volunteers,
        "active_volunteers": active_volunteers
    }), 200