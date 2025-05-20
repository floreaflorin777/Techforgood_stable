from flask import Blueprint, render_template, send_from_directory, request, jsonify, redirect, url_for, flash
import os
from app.firestore_models import User, Volunteer
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from flask_jwt_extended.exceptions import NoAuthorizationError

main = Blueprint('main', __name__)

# Home route
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register')
def register():
    return render_template('register.html')

@main.route('/admin/dashboard')
def admin_dashboard():
    # Authentication check is handled by middleware
    return render_template('admin_dashboard.html')

@main.route('/volunteer/dashboard')
def volunteer_dashboard():
    # Authentication check is handled by middleware
    return render_template('volunteer_dashboard.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

@main.route('/volunteer/shifts')
def shifts():
    # Authentication check is handled by middleware
    return render_template('shifts.html')

@main.route('/volunteer/report_hours')
def report_hours():
    # Authentication check is handled by middleware
    return render_template('report_hours.html')

@main.route('/volunteer/my_shifts')
def my_shifts():
    # Authentication check is handled by middleware
    return render_template('my_shifts.html')

@main.route('/volunteer/my_profile')
def my_profile():
    # Authentication check is handled by middleware
    return render_template('my_profile.html')

@main.route('/volunteer/calendar')
def calendar():
    # Authentication check is handled by middleware
    return render_template('calendar.html')

@main.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle volunteer feedback submission."""
    try:
        # Get form data
        name = request.form.get('name', 'Anonymous')
        email = request.form.get('email', 'Not provided')
        feedback_type = request.form.get('feedback_type')
        message = request.form.get('message')
        rating = request.form.get('rating')
        
        # Create a feedback document in Firestore
        # This assumes you have a Feedback model, or you can create a direct Firestore document
        from app.firebase_config import get_firestore_db
        db = get_firestore_db()
        feedback_ref = db.collection('feedback').document()
        
        feedback_ref.set({
            'name': name,
            'email': email,
            'feedback_type': feedback_type,
            'message': message,
            'rating': rating,
            'submitted_at': datetime.utcnow(),
            'status': 'new'
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Thank you for your feedback! We appreciate your input.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to submit feedback: {str(e)}'
        }), 500

# Serve static files as needed
@main.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'), filename)
