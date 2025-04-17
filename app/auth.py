from flask import Blueprint, request, jsonify
from app.models import db, User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.json
    user = User(
        name=data['name'],
        email=data['email'],
        role=data.get('role', 'volunteer')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password is correct
    if user and user.check_password(data['password']):
        # Check role if specified in request
        requested_role = data.get('role')
        if requested_role and user.role != requested_role:
            return jsonify({"error": f"User is not registered as a {requested_role}"}), 403
        
        # Create access token with user identity
        token = create_access_token(identity={"id": user.id, "role": user.role})
        return jsonify({
            "access_token": token,
            "role": user.role,
            "name": user.name,
            "id": user.id
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    identity = get_jwt_identity()
    return jsonify({"message": f"Hello, {identity['role']}!"})
