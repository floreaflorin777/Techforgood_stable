from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import re
from datetime import datetime
from app.firestore_models import User, Volunteer

volunteers_bp = Blueprint('volunteers', __name__)

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

# Validation functions
def validate_email(email):
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format"
    return True, None

def validate_phone(phone):
    if phone and not re.match(r"^\+?[1-9]\d{1,14}$", phone):
        return False, "Invalid phone number format"
    return True, None

@volunteers_bp.route('/api/volunteers', methods=['GET'])
@jwt_required()
def get_volunteers():
    try:
        # Get all volunteers from Firestore
        volunteers_data = Volunteer.get_all()
        
        # Prepare result including user data for each volunteer
        result = []
        for volunteer in volunteers_data:
            user = User.get_by_id(volunteer['user_id'])
            if user:
                result.append({
                    'id': volunteer['id'],
                    'user_id': volunteer['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'phone': user.get('phone'),
                    'availability': volunteer.get('availability', {}),
                    'skills': volunteer.get('skills', '')
                })
        
        return jsonify(result), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting volunteers: {str(e)}')
        return jsonify({'error': 'Failed to retrieve volunteers', 'message': str(e)}), 500

@volunteers_bp.route('/api/volunteers/<volunteer_id>', methods=['GET'])
@jwt_required()
def get_volunteer(volunteer_id):
    try:
        # Get volunteer from Firestore
        volunteer = Volunteer.get_by_id(volunteer_id)
        if not volunteer:
            return jsonify({'error': 'Volunteer not found'}), 404
        
        # Get associated user data
        user = User.get_by_id(volunteer['user_id'])
        if not user:
            return jsonify({'error': 'User not found for this volunteer'}), 404
        
        return jsonify({
            'id': volunteer['id'],
            'user_id': volunteer['user_id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user.get('phone'),
            'availability': volunteer.get('availability', {}),
            'skills': volunteer.get('skills', '')
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting volunteer {volunteer_id}: {str(e)}')
        return jsonify({'error': 'Failed to retrieve volunteer', 'message': str(e)}), 500

@volunteers_bp.route('/api/volunteers', methods=['POST'])
@require_role('admin')
def add_volunteer():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('email'):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate email and phone
        email_valid, email_error = validate_email(data['email'])
        if not email_valid:
            return jsonify({'error': email_error}), 400

        if 'phone' in data:
            phone_valid, phone_error = validate_phone(data['phone'])
            if not phone_valid:
                return jsonify({'error': phone_error}), 400

        # Check if user already exists
        existing_user = User.get_by_email(data['email'])
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400

        # Create user
        user_id = User.create(
            name=data['name'],
            email=data['email'],
            password=data.get('password', 'default_password'),
            role='volunteer',
            phone=data.get('phone')
        )
        
        # Create volunteer profile
        volunteer_id = Volunteer.create(
            user_id=user_id,
            availability=data.get('availability', {}),
            skills=data.get('skills', '')
        )
        
        current_app.logger.info(f'New volunteer added: {data["email"]}')
        return jsonify({
            'message': 'Volunteer added successfully',
            'id': volunteer_id,
            'user_id': user_id
        }), 201
    
    except Exception as e:
        current_app.logger.error(f'Error adding volunteer: {str(e)}')
        return jsonify({'error': 'Failed to add volunteer', 'message': str(e)}), 500

@volunteers_bp.route('/api/volunteers/<volunteer_id>', methods=['PUT'])
@require_role('admin')
def update_volunteer(volunteer_id):
    try:
        data = request.json
        
        # Validate email and phone if provided
        if 'email' in data:
            email_valid, email_error = validate_email(data['email'])
            if not email_valid:
                return jsonify({'error': email_error}), 400
                
        if 'phone' in data:
            phone_valid, phone_error = validate_phone(data['phone'])
            if not phone_valid:
                return jsonify({'error': phone_error}), 400
        
        # Get volunteer from Firestore
        volunteer = Volunteer.get_by_id(volunteer_id)
        if not volunteer:
            return jsonify({'error': 'Volunteer not found'}), 404
        
        # Update volunteer data
        volunteer_update = {}
        if 'availability' in data:
            volunteer_update['availability'] = data['availability']
        if 'skills' in data:
            volunteer_update['skills'] = data['skills']
            
        if volunteer_update:
            Volunteer.update(volunteer_id, volunteer_update)
        
        # Update associated user data
        user_update = {}
        if 'name' in data:
            user_update['name'] = data['name']
        if 'email' in data:
            user_update['email'] = data['email']
        if 'phone' in data:
            user_update['phone'] = data['phone']
            
        if user_update:
            User.update(volunteer['user_id'], user_update)
        
        current_app.logger.info(f'Volunteer updated: {volunteer_id}')
        return jsonify({'message': 'Volunteer updated successfully'}), 200
    
    except Exception as e:
        current_app.logger.error(f'Error updating volunteer {volunteer_id}: {str(e)}')
        return jsonify({'error': 'Failed to update volunteer', 'message': str(e)}), 500

@volunteers_bp.route('/api/volunteers/<volunteer_id>', methods=['DELETE'])
@require_role('admin')
def delete_volunteer(volunteer_id):
    try:
        # Get volunteer from Firestore
        volunteer = Volunteer.get_by_id(volunteer_id)
        if not volunteer:
            return jsonify({'error': 'Volunteer not found'}), 404
        
        # Get associated user
        user_id = volunteer['user_id']
        user = User.get_by_id(user_id)
        
        # Delete volunteer profile first
        Volunteer.delete(volunteer_id)
        
        if user:
            # Only delete the user if they exist and have role=volunteer
            # This prevents accidental deletion of admin or manager users
            if user['role'] == 'volunteer':
                User.delete(user_id)
            else:
                # If the user has a different role, don't delete user record
                current_app.logger.info(f"User {user['email']} has role {user['role']}, not deleting user record")
        
        current_app.logger.info(f'Volunteer deleted: {volunteer_id}')
        return jsonify({"message": f"Volunteer with id {volunteer_id} deleted."}), 200
    
    except Exception as e:
        current_app.logger.error(f'Error deleting volunteer {volunteer_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete volunteer', 'message': str(e)}), 500 