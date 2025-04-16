# Food Bank Management System

A comprehensive system for managing food bank operations, including volunteer scheduling, inventory management, and analytics.

## Features

- **User Management**
  - Role-based access control (Admin, Manager, Volunteer)
  - Secure authentication with JWT
  - User registration and login

- **Volunteer Management**
  - Volunteer registration and profiles
  - Availability tracking
  - Skills management
  - Shift scheduling

- **Inventory Management**
  - Track food items and quantities
  - Expiration date monitoring
  - Category-based organization
  - Low stock alerts

- **Analytics**
  - Volunteer participation metrics
  - Inventory statistics
  - Shift coverage analysis
  - Expiring items tracking

- **Notifications**
  - Email notifications
  - WhatsApp integration
  - Shift reminders
  - Inventory alerts

## Tech Stack

- **Backend**
  - Python 3.8+
  - Flask
  - SQLAlchemy
  - JWT Authentication
  - Twilio (for WhatsApp notifications)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/foodbank.git
cd foodbank
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
export SECRET_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret
export DATABASE_URL=sqlite:///foodbank.db
export TWILIO_ACCOUNT_SID=your-twilio-sid
export TWILIO_AUTH_TOKEN=your-twilio-token
export TWILIO_WHATSAPP_NUMBER=your-twilio-whatsapp-number
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## API Documentation

### Authentication

#### Login
```http
POST /auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

#### Register
```http
POST /auth/register
Content-Type: application/json

{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "role": "volunteer"
}
```

### Volunteers

#### Get All Volunteers
```http
GET /api/volunteers
Authorization: Bearer <token>
```

#### Add Volunteer
```http
POST /api/volunteers
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "availability": {
        "monday": ["09:00-17:00"],
        "wednesday": ["09:00-17:00"]
    },
    "skills": "Inventory Management"
}
```

### Shifts

#### Get All Shifts
```http
GET /api/shifts
Authorization: Bearer <token>
```

#### Create Shift
```http
POST /api/shifts
Authorization: Bearer <token>
Content-Type: application/json

{
    "start_time": "2024-04-20T09:00:00",
    "end_time": "2024-04-20T17:00:00",
    "volunteer_id": 1
}
```

### Inventory

#### Get Inventory
```http
GET /api/inventory
Authorization: Bearer <token>
```

#### Add Inventory Item
```http
POST /api/inventory
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Rice",
    "quantity": 100,
    "unit": "kg",
    "category": "non-perishable",
    "expiry_date": "2024-12-31"
}
```

### Analytics

#### Volunteer Analytics
```http
GET /api/analytics/volunteers
Authorization: Bearer <token>
```

#### Inventory Analytics
```http
GET /api/analytics/inventory
Authorization: Bearer <token>
```

## Error Handling

The API uses standard HTTP status codes and returns JSON responses in the following format:

```json
{
    "error": "Error Type",
    "message": "Detailed error message"
}
```

Common status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
