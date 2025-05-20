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
        current_app.logger.info(f"Login attempt for: {data.get('email')} with role {data.get('role')}")
        
        user = User.get_by_email(data['email'])
        if not user:
            current_app.logger.warning(f"Login failed - user not found: {data.get('email')}")
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not User.check_password(user, data['password']):
            current_app.logger.warning(f"Login failed - invalid password for: {data.get('email')}")
            return jsonify({"error": "Invalid credentials"}), 401
        
        requested_role = data.get('role')
        if requested_role and user['role'] != requested_role:
            current_app.logger.warning(f"Login failed - role mismatch. Requested {requested_role}, actual {user['role']}")
            return jsonify({"error": f"User is not registered as a {requested_role}"}), 403
        
        expires = timedelta(days=1)
        # Use user ID string as the direct identity for JWT subject
        # Store other information like role in additional_claims
        user_id_str = str(user['id'])
        token = create_access_token(
            identity=user_id_str,
            additional_claims={"role": user['role'], "name": user['name']},
            expires_delta=expires
        )
        
        current_app.logger.info(f"User logged in successfully: {user['email']}")
        login_response = {
            "access_token": token,
            "role": user['role'], # Still send role in login response for frontend convenience
            "name": user['name'],  # Still send name for frontend convenience
            "id": user_id_str
        }
        current_app.logger.debug(f"Login response: {login_response}")
        return jsonify(login_response)
    
    except Exception as e:
        current_app.logger.error(f"Error in login: {str(e)}", exc_info=True) # Added exc_info
        return jsonify({"error": str(e)}), 500

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # get_jwt_identity() will now return the user_id_str
    current_user_id = get_jwt_identity() 
    # To get additional claims:
    # from flask_jwt_extended import get_jwt
    # current_user_claims = get_jwt()
    # current_user_role = current_user_claims.get("role")
    return jsonify({"message": f"Hello, user_id: {current_user_id}!"}) 

@auth.route('/user', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        # get_jwt_identity() now returns the user_id string directly
        user_id = get_jwt_identity() 
        
        if not user_id: # Should not happen if @jwt_required passed and identity is set
            current_app.logger.error("No identity (user_id) found in JWT!")
            return jsonify({"error": "No identity found in token"}), 401

        current_app.logger.info(f"Getting user profile for ID: {user_id} (type: {type(user_id)})") # Log type
        
        user_details = User.get_by_id(user_id) # User.get_by_id should handle string ID
        if not user_details:
            current_app.logger.warning(f"User not found for ID: {user_id}")
            return jsonify({"error": "User not found"}), 404

        # To get additional claims like role if needed here:
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        user_role_from_token = claims.get("role")
        user_name_from_token = claims.get("name")

        # Remove sensitive information
        if 'password_hash' in user_details:
            del user_details['password_hash']
        
        # Ensure the returned user object for the frontend has id and role as expected by setUserSession
        # The user_details from Firestore already contains 'id' and 'role'.
        # We can enrich it or ensure consistency.
        
        current_app.logger.debug(f"Returning user profile: {user_details}, role from token: {user_role_from_token}")
        return jsonify({
            "success": True,
            # Ensure the 'user' object in response matches what frontend expects
            # after login (id, name, role)
            "user": {
                "id": user_details.get('id'), 
                "name": user_details.get('name', user_name_from_token), # Fallback to token name
                "role": user_details.get('role', user_role_from_token)  # Fallback to token role
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
