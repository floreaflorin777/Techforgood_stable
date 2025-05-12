from flask import Blueprint, jsonify, request, render_template, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.firestore_models import User, Volunteer, Shift, InventoryItem

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    """Render admin dashboard page."""
    return render_template('admin.html')

# API endpoints for admin dashboard

@admin_bp.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """Get admin dashboard statistics."""
    # Verify the user is an admin
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Collect statistics
    all_volunteers = Volunteer.get_all()
    active_volunteers = [v for v in all_volunteers if v.get('is_active', True)]
    all_items = InventoryItem.get_all()
    low_stock_items = InventoryItem.get_low_stock(threshold=10)
    
    stats = {
        'totalVolunteers': len(all_volunteers),
        'activeVolunteers': len(active_volunteers),
        'totalItems': len(all_items),
        'lowStockItems': len(low_stock_items)
    }
    
    return jsonify(stats)

@admin_bp.route('/api/admin/recent-shifts', methods=['GET'])
@jwt_required()
def get_recent_shifts():
    """Get recent shifts for admin dashboard."""
    # Verify the user is an admin
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get upcoming shifts
    shifts = Shift.get_upcoming()
    result = []
    
    for shift in shifts[:5]:  # Get the 5 most recent
        volunteer_id = shift.get('volunteer_id')
        volunteer_name = "Unknown"
        
        if volunteer_id:
            volunteer = User.get_by_id(volunteer_id)
            if volunteer:
                volunteer_name = volunteer.get('name', 'Unknown')
        
        result.append({
            'id': shift.get('id'),
            'volunteerName': volunteer_name,
            'startTime': shift.get('start_time'),
            'endTime': shift.get('end_time'),
            'status': shift.get('status', 'pending')
        })
    
    return jsonify(result)

@admin_bp.route('/api/admin/low-stock', methods=['GET'])
@jwt_required()
def get_low_stock():
    """Get low stock items for admin dashboard."""
    # Verify the user is an admin
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get low stock items
    items = InventoryItem.get_low_stock(threshold=10)
    result = []
    
    for item in items:
        result.append({
            'id': item.get('id'),
            'name': item.get('name'),
            'quantity': item.get('quantity'),
            'unit': item.get('unit', '')
        })
    
    return jsonify(result)

@admin_bp.route('/api/admin/volunteers', methods=['GET'])
@jwt_required()
def get_volunteers():
    """Get all volunteers for admin dashboard."""
    # Verify the user is an admin
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all users with volunteer role
    volunteers = User.get_by_role('volunteer')
    result = []
    
    for volunteer in volunteers:
        result.append({
            'id': volunteer.get('id'),
            'name': volunteer.get('name'),
            'email': volunteer.get('email'),
            'phone': volunteer.get('phone'),
            'isActive': volunteer.get('is_active', True)
        })
    
    return jsonify(result)

@admin_bp.route('/api/admin/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    """Get all inventory items for admin dashboard."""
    # Verify the user is an admin
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all inventory items
    items = InventoryItem.get_all()
    result = []
    
    for item in items:
        result.append({
            'id': item.get('id'),
            'name': item.get('name'),
            'quantity': item.get('quantity'),
            'unit': item.get('unit'),
            'category': item.get('category'),
            'expiryDate': item.get('expiry_date')
        })
    
    return jsonify(result)

@admin_bp.route('/api/admin/shifts', methods=['GET'])
@jwt_required()
def get_shifts():
    """Get all shifts for admin dashboard."""
    # Verify the user is an admin
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all shifts
    shifts = Shift.get_all()
    result = []
    
    for shift in shifts:
        volunteer_id = shift.get('volunteer_id')
        volunteer_name = "Unknown"
        
        if volunteer_id:
            volunteer = User.get_by_id(volunteer_id)
            if volunteer:
                volunteer_name = volunteer.get('name', 'Unknown')
        
        result.append({
            'id': shift.get('id'),
            'volunteerName': volunteer_name,
            'startTime': shift.get('start_time'),
            'endTime': shift.get('end_time'),
            'status': shift.get('status', 'pending')
        })
    
    return jsonify(result) 