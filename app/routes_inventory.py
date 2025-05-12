from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.firestore_models import InventoryItem

inventory_bp = Blueprint('inventory', __name__)

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

@inventory_bp.route('/api/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    try:
        # Get all inventory items from Firestore
        items = InventoryItem.get_all()
        
        for item in items:
            # Format dates for JSON serialization
            if 'expiry_date' in item and item['expiry_date']:
                if isinstance(item['expiry_date'], datetime):
                    item['expiry_date'] = item['expiry_date'].isoformat()
        
        return jsonify(items), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting inventory: {str(e)}')
        return jsonify({'error': 'Failed to retrieve inventory', 'message': str(e)}), 500

@inventory_bp.route('/api/inventory/<item_id>', methods=['GET'])
@jwt_required()
def get_inventory_item(item_id):
    try:
        # Get inventory item from Firestore
        item = InventoryItem.get_by_id(item_id)
        if not item:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        # Format dates for JSON serialization
        if 'expiry_date' in item and item['expiry_date']:
            if isinstance(item['expiry_date'], datetime):
                item['expiry_date'] = item['expiry_date'].isoformat()
        
        return jsonify(item), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting inventory item {item_id}: {str(e)}')
        return jsonify({'error': 'Failed to retrieve inventory item', 'message': str(e)}), 500

@inventory_bp.route('/api/inventory', methods=['POST'])
@require_role('manager')
def add_inventory_item():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('quantity'):
            return jsonify({'error': 'Missing required fields'}), 400

        # Get the current user's ID from JWT
        current_user = get_jwt_identity()
        
        # Convert expiry_date string to datetime if provided
        expiry_date = None
        if data.get('expiry_date'):
            expiry_date = datetime.fromisoformat(data['expiry_date'])
        
        # Create inventory item
        item_id = InventoryItem.create(
            name=data['name'],
            quantity=int(data['quantity']),
            unit=data.get('unit'),
            category=data.get('category'),
            expiry_date=expiry_date,
            added_by=current_user['id']
        )
        
        current_app.logger.info(f'New inventory item added: {data["name"]}')
        return jsonify({
            'message': 'Inventory item added successfully',
            'id': item_id
        }), 201
    
    except Exception as e:
        current_app.logger.error(f'Error adding inventory item: {str(e)}')
        return jsonify({'error': 'Failed to add inventory item', 'message': str(e)}), 500

@inventory_bp.route('/api/inventory/<item_id>', methods=['PUT'])
@require_role('manager')
def update_inventory_item(item_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No update data provided'}), 400
        
        # Get inventory item from Firestore
        item = InventoryItem.get_by_id(item_id)
        if not item:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        # Prepare update data
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
            
        if 'quantity' in data:
            update_data['quantity'] = int(data['quantity'])
            
        if 'unit' in data:
            update_data['unit'] = data['unit']
            
        if 'category' in data:
            update_data['category'] = data['category']
            
        if 'expiry_date' in data:
            if data['expiry_date']:
                update_data['expiry_date'] = datetime.fromisoformat(data['expiry_date'])
            else:
                update_data['expiry_date'] = None
        
        # Update item in Firestore (this also adds last_updated timestamp)
        InventoryItem.update(item_id, update_data)
        
        current_app.logger.info(f'Inventory item updated: {item_id}')
        return jsonify({'message': 'Inventory item updated successfully'}), 200
    
    except Exception as e:
        current_app.logger.error(f'Error updating inventory item {item_id}: {str(e)}')
        return jsonify({'error': 'Failed to update inventory item', 'message': str(e)}), 500

@inventory_bp.route('/api/inventory/<item_id>', methods=['DELETE'])
@require_role('manager')
def delete_inventory_item(item_id):
    try:
        # Get inventory item from Firestore
        item = InventoryItem.get_by_id(item_id)
        if not item:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        # Delete item from Firestore
        InventoryItem.delete(item_id)
        
        current_app.logger.info(f'Inventory item deleted: {item_id}')
        return jsonify({'message': 'Inventory item deleted successfully'}), 200
    
    except Exception as e:
        current_app.logger.error(f'Error deleting inventory item {item_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete inventory item', 'message': str(e)}), 500

@inventory_bp.route('/api/inventory/low-stock', methods=['GET'])
@jwt_required()
def get_low_stock():
    try:
        threshold = request.args.get('threshold', 10, type=int)
        items = InventoryItem.get_low_stock(threshold)
        
        for item in items:
            # Format dates for JSON serialization
            if 'expiry_date' in item and item['expiry_date']:
                if isinstance(item['expiry_date'], datetime):
                    item['expiry_date'] = item['expiry_date'].isoformat()
        
        return jsonify(items), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting low stock items: {str(e)}')
        return jsonify({'error': 'Failed to retrieve low stock items', 'message': str(e)}), 500

@inventory_bp.route('/api/inventory/expiring-soon', methods=['GET'])
@jwt_required()
def get_expiring_soon():
    try:
        days = request.args.get('days', 7, type=int)
        items = InventoryItem.get_expiring_soon(days)
        
        for item in items:
            # Format dates for JSON serialization
            if 'expiry_date' in item and item['expiry_date']:
                if isinstance(item['expiry_date'], datetime):
                    item['expiry_date'] = item['expiry_date'].isoformat()
        
        return jsonify(items), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting expiring items: {str(e)}')
        return jsonify({'error': 'Failed to retrieve expiring items', 'message': str(e)}), 500 