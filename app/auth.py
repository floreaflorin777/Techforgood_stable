from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.firestore_models import User
from datetime import timedelta

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Check if user already exists
        existing_user = User.get_by_email(data['email'])
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 400
        
        # Create new user
        user_id = User.create(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'volunteer'),
            phone=data.get('phone')
        )
        
        # If the role is volunteer, create a volunteer profile
        if data.get('role', 'volunteer') == 'volunteer':
            from app.firestore_models import Volunteer
            
            # Convert skills array to string if needed
            skills = data.get('skills', [])
            if isinstance(skills, list):
                skills = ', '.join(skills)
            
            Volunteer.create(
                user_id=user_id,
                availability=data.get('availability', {}),
                skills=skills
            )
        
        current_app.logger.info(f"User registered: {data['email']} with role {data.get('role', 'volunteer')}")
        return jsonify({"message": "User registered successfully", "id": user_id}), 201
    
    except Exception as e:
        current_app.logger.error(f"Error in registration: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        # Get user by email
        user = User.get_by_email(data['email'])
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check password
        if not User.check_password(user, data['password']):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check role if specified in request
        requested_role = data.get('role')
        if requested_role and user['role'] != requested_role:
            return jsonify({"error": f"User is not registered as a {requested_role}"}), 403
        
        # Create access token with user identity
        expires = timedelta(days=1)
        token = create_access_token(
            identity={"id": user['id'], "role": user['role']},
            expires_delta=expires
        )
        
        current_app.logger.info(f"User logged in: {user['email']}")
        return jsonify({
            "access_token": token,
            "role": user['role'],
            "name": user['name'],
            "id": user['id']
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in login: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    identity = get_jwt_identity()
    return jsonify({"message": f"Hello, {identity['role']}!"})

@auth.route('/user', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        identity = get_jwt_identity()
        user_id = identity['id']
        
        # Get user details
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Remove sensitive information
        if 'password_hash' in user:
            del user['password_hash']
            
        return jsonify({
            "success": True,
            "user": user
        })
    
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({"error": str(e)}), 500
