# Firebase Migration Update

## Overview

This project has been migrated from MySQL to Firebase Firestore as the database backend. This change resolves several issues:

1. Eliminates connectivity problems with PythonAnywhere's MySQL database
2. Provides real-time data synchronization capabilities
3. Simplifies deployment and scaling
4. Removes the need for SSH tunneling for local development

## Key Changes

- Replaced SQLAlchemy ORM with Firebase Admin SDK
- Created a data access layer for Firestore operations
- Implemented Firestore model representations of all data models
- Updated all API routes to use Firebase models
- Added Firebase project configuration
- Reorganized project structure for clarity

## Requirements

The project now requires:

- Firebase Admin SDK (`firebase-admin`)
- Google Cloud Firestore (`google-cloud-firestore`) 
- A Firebase project with Firestore enabled
- Firebase credentials (service account JSON file)

## Setup Instructions

1. Follow the instructions in `docs/FIREBASE_SETUP.md` to create a Firebase project and obtain credentials.
2. Place your Firebase credentials in a file named `firebase-credentials.json` in the project root.
3. Set the `FIREBASE_CREDENTIALS` environment variable to point to your credentials file if not using the default location.
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   flask run
   ```

## Project Structure

The project has been reorganized for clarity:

- `/app`: Application code and Firebase models
  - `firebase_config.py`: Firebase initialization
  - `firestore_dao.py`: Data access layer
  - `firestore_models.py`: Model representations
  - `routes_*.py`: Route files organized by feature
- `/docs`: Documentation
- `/templates`: HTML templates
- `/static`: Static assets

## Authentication

Authentication now uses Firebase with JWT. The login and registration flows remain the same, but the backend uses Firebase for user management.

## Data Migration

If you have existing data in MySQL that you want to migrate:

1. Export your MySQL data using a tool like MySQL Workbench or phpMyAdmin
2. Create a migration script to import the data into Firestore
3. Run the migration script once to populate Firestore

## Troubleshooting

- If you encounter connection issues, make sure your Firebase credentials are valid and you have internet access
- If data isn't showing up, check Firebase permissions and rules
- For authentication issues, verify your JWT configuration in `config.py`

## Benefits of Firebase

- Real-time data synchronization
- Simplified scaling
- No need for database server management
- Built-in authentication options
- Offline support for web and mobile clients 