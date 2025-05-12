from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.firestore_models import Shift, Volunteer
from app.notify import notification_service

shifts_bp = Blueprint('shifts', __name__)

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

@shifts_bp.route('/api/shifts', methods=['GET'])
@jwt_required()
def get_shifts():
    try:
        # Get all shifts from Firestore
        shifts = Shift.get_all()
        
        # Format dates for JSON serialization
        for shift in shifts:
            if 'start_time' in shift and shift['start_time']:
                if isinstance(shift['start_time'], datetime):
                    shift['start_time'] = shift['start_time'].isoformat()
            
            if 'end_time' in shift and shift['end_time']:
                if isinstance(shift['end_time'], datetime):
                    shift['end_time'] = shift['end_time'].isoformat()
        
        return jsonify(shifts), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting shifts: {str(e)}')
        return jsonify({'error': 'Failed to retrieve shifts', 'message': str(e)}), 500

@shifts_bp.route('/api/shifts/<shift_id>', methods=['GET'])
@jwt_required()
def get_shift(shift_id):
    try:
        # Get shift from Firestore
        shift = Shift.get_by_id(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # Format dates for JSON serialization
        if 'start_time' in shift and shift['start_time'] and isinstance(shift['start_time'], datetime):
            shift['start_time'] = shift['start_time'].isoformat()
        
        if 'end_time' in shift and shift['end_time'] and isinstance(shift['end_time'], datetime):
            shift['end_time'] = shift['end_time'].isoformat()
        
        return jsonify(shift), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting shift {shift_id}: {str(e)}')
        return jsonify({'error': 'Failed to retrieve shift', 'message': str(e)}), 500

@shifts_bp.route('/api/shifts', methods=['POST'])
@require_role('admin')
def create_shift():
    try:
        data = request.json
        
        # Validate shift times
        if not data or not data.get('start_time') or not data.get('end_time'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        times_valid, time_error = validate_shift_times(data['start_time'], data['end_time'])
        if not times_valid:
            return jsonify({'error': time_error}), 400
        
        # Get the current user's ID from JWT
        current_user = get_jwt_identity()
        
        # Check if volunteer exists if volunteer_id is provided
        volunteer_id = data.get('volunteer_id')
        
        if volunteer_id:
            volunteer = Volunteer.get_by_id(volunteer_id)
            if not volunteer:
                return jsonify({'error': 'Volunteer not found'}), 404
        
        # Create shift in Firestore
        shift_id = Shift.create(
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            volunteer_id=volunteer_id,
            created_by=current_user['id'],
            status=data.get('status', 'pending'),
            capacity=data.get('capacity', 5)
        )
        
        # Notify volunteer about the new shift
        if volunteer_id:
            try:
                notification_service.send_shift_notification(volunteer_id, shift_id)
            except Exception as notify_error:
                current_app.logger.error(f'Error sending shift notification: {str(notify_error)}')
        
        current_app.logger.info(f'New shift created: {shift_id}')
        return jsonify({
            'message': 'Shift created successfully',
            'id': shift_id
        }), 201
    
    except Exception as e:
        current_app.logger.error(f'Error creating shift: {str(e)}')
        return jsonify({'error': 'Failed to create shift', 'message': str(e)}), 500

@shifts_bp.route('/api/shifts/<shift_id>', methods=['PUT'])
@require_role('admin')
def update_shift(shift_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No update data provided'}), 400
        
        # Get shift from Firestore
        shift = Shift.get_by_id(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # Validate shift times if provided
        if 'start_time' in data and 'end_time' in data:
            times_valid, time_error = validate_shift_times(data['start_time'], data['end_time'])
            if not times_valid:
                return jsonify({'error': time_error}), 400
        
        # Prepare update data
        update_data = {}
        
        if 'start_time' in data:
            update_data['start_time'] = datetime.fromisoformat(data['start_time'])
            
        if 'end_time' in data:
            update_data['end_time'] = datetime.fromisoformat(data['end_time'])
            
        if 'volunteer_id' in data:
            # Check if volunteer exists
            volunteer_id = data['volunteer_id']
            if volunteer_id:
                volunteer = Volunteer.get_by_id(volunteer_id)
                if not volunteer:
                    return jsonify({'error': 'Volunteer not found'}), 404
            
            update_data['volunteer_id'] = volunteer_id
            
            # Update volunteer_ids array as well
            if volunteer_id:
                update_data['volunteer_ids'] = [volunteer_id]
            else:
                update_data['volunteer_ids'] = []
        
        if 'status' in data:
            update_data['status'] = data['status']
            
        if 'capacity' in data:
            update_data['capacity'] = int(data['capacity'])
        
        # Update shift in Firestore
        Shift.update(shift_id, update_data)
        
        current_app.logger.info(f'Shift updated: {shift_id}')
        return jsonify({'message': 'Shift updated successfully'}), 200
    
    except Exception as e:
        current_app.logger.error(f'Error updating shift {shift_id}: {str(e)}')
        return jsonify({'error': 'Failed to update shift', 'message': str(e)}), 500

@shifts_bp.route('/api/shifts/<shift_id>', methods=['DELETE'])
@require_role('admin')
def delete_shift(shift_id):
    try:
        # Get shift from Firestore
        shift = Shift.get_by_id(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # Delete shift from Firestore
        Shift.delete(shift_id)
        
        current_app.logger.info(f'Shift deleted: {shift_id}')
        return jsonify({'message': 'Shift deleted successfully'}), 200
    
    except Exception as e:
        current_app.logger.error(f'Error deleting shift {shift_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete shift', 'message': str(e)}), 500

@shifts_bp.route('/api/shifts/volunteer/<volunteer_id>', methods=['GET'])
@jwt_required()
def get_volunteer_shifts(volunteer_id):
    try:
        # Check if volunteer exists
        volunteer = Volunteer.get_by_id(volunteer_id)
        if not volunteer:
            return jsonify({'error': 'Volunteer not found'}), 404
        
        # Get shifts for volunteer
        shifts = Shift.get_by_volunteer(volunteer_id)
        
        # Format dates for JSON serialization
        for shift in shifts:
            if 'start_time' in shift and shift['start_time'] and isinstance(shift['start_time'], datetime):
                shift['start_time'] = shift['start_time'].isoformat()
            
            if 'end_time' in shift and shift['end_time'] and isinstance(shift['end_time'], datetime):
                shift['end_time'] = shift['end_time'].isoformat()
        
        return jsonify(shifts), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting shifts for volunteer {volunteer_id}: {str(e)}')
        return jsonify({'error': 'Failed to retrieve volunteer shifts', 'message': str(e)}), 500

@shifts_bp.route('/api/shifts/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_shifts():
    try:
        # Get upcoming shifts
        shifts = Shift.get_upcoming()
        
        # Format dates for JSON serialization
        for shift in shifts:
            if 'start_time' in shift and shift['start_time'] and isinstance(shift['start_time'], datetime):
                shift['start_time'] = shift['start_time'].isoformat()
            
            if 'end_time' in shift and shift['end_time'] and isinstance(shift['end_time'], datetime):
                shift['end_time'] = shift['end_time'].isoformat()
        
        return jsonify(shifts), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting upcoming shifts: {str(e)}')
        return jsonify({'error': 'Failed to retrieve upcoming shifts', 'message': str(e)}), 500 