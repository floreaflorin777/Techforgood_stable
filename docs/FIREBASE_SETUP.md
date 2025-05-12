# Firebase Setup Guide

This guide will help you set up Firebase for the Food Bank Management System.

## 1. Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" and follow the prompts to create a new project
3. Give your project a name (e.g., "FoodBankSystem")
4. Choose whether to enable Google Analytics (optional)
5. Click "Create Project"

## 2. Set Up Firestore Database

1. In your Firebase project, navigate to "Firestore Database" in the sidebar
2. Click "Create database"
3. Choose "Start in production mode" or "Start in test mode" (choose test mode for development)
4. Select a location that's geographically close to your users
5. Click "Enable"

## 3. Generate Service Account Credentials

1. In your Firebase project, click the gear icon (⚙️) next to "Project Overview" and select "Project settings"
2. Navigate to the "Service accounts" tab
3. Click "Generate new private key" button
4. Save the JSON file securely - this contains sensitive credentials
5. Rename the file to `firebase-credentials.json` and place it in the root directory of your project

## 4. Configure Environment Variables

Set the following environment variables in your `.env` file:

```
FIREBASE_CREDENTIALS=./firebase-credentials.json
```

Alternatively, you can set the full path to your credentials file:

```
FIREBASE_CREDENTIALS=/absolute/path/to/firebase-credentials.json
```

## 5. Security Rules

For optimal security, set up Firestore security rules:

1. In your Firebase project, navigate to "Firestore Database" in the sidebar
2. Click the "Rules" tab
3. Modify the rules to secure your collections (example below)

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Only authenticated users can read/write any document
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
    
    // User profiles can only be read by the user themselves or admins
    match /users/{userId} {
      allow read: if request.auth.uid == userId || 
                   get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow write: if request.auth.uid == userId || 
                    get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
    
    // Volunteers can only be written by admins
    match /volunteers/{volunteerId} {
      allow read: if request.auth != null;
      allow write: if get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
  }
}
```

## 6. Testing Your Connection

After setting up Firebase, you can test your connection by:

1. Running the application with `flask run`
2. Creating a new user account via the `/auth/register` endpoint
3. Checking that data appears in your Firestore Database console

## Troubleshooting

### Permission Issues

If you encounter permission issues, check:
- The service account credentials have the necessary permissions
- Your Firebase project has Firestore enabled
- Your application has the correct path to the credentials file

### Connection Issues

If your application can't connect to Firebase:
- Verify your internet connection
- Check that your credentials file is correctly formatted
- Ensure you have the firebase-admin package installed (`pip install firebase-admin`)

### Data Not Appearing

If data isn't appearing in your collections:
- Check for errors in your application logs
- Verify that the collection names match between your code and Firestore
- Ensure write operations are completing successfully 