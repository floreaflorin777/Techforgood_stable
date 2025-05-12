from firebase_admin import firestore
from flask import current_app
from datetime import datetime
from app.firebase_config import get_firestore_db

class FirestoreDAO:
    """Data Access Object for Firestore operations."""
    
    @staticmethod
    def get_db():
        """Get Firestore database client."""
        db = get_firestore_db()
        if not db:
            db = current_app.config.get('FIRESTORE_DB')
        return db
    
    @staticmethod
    def create_document(collection, data, doc_id=None):
        """Create a new document in a collection.
        
        Args:
            collection: Collection name
            data: Document data dictionary
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        db = FirestoreDAO.get_db()
        if doc_id:
            db.collection(collection).document(doc_id).set(data)
            return doc_id
        else:
            doc_ref = db.collection(collection).add(data)[1]
            return doc_ref.id
    
    @staticmethod
    def get_document(collection, doc_id):
        """Get a document by its ID.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            
        Returns:
            Document data with ID added, or None if not found
        """
        db = FirestoreDAO.get_db()
        doc = db.collection(collection).document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    
    @staticmethod
    def update_document(collection, doc_id, data):
        """Update fields in a document.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            data: Fields to update
            
        Returns:
            True on success
        """
        db = FirestoreDAO.get_db()
        db.collection(collection).document(doc_id).update(data)
        return True
    
    @staticmethod
    def delete_document(collection, doc_id):
        """Delete a document.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            
        Returns:
            True on success
        """
        db = FirestoreDAO.get_db()
        db.collection(collection).document(doc_id).delete()
        return True
    
    @staticmethod
    def query_collection(collection, filters=None, order_by=None, order_direction='desc', limit=None):
        """Query documents in a collection with optional filters and ordering.
        
        Args:
            collection: Collection name
            filters: List of filter tuples (field, operator, value)
            order_by: Field to order by
            order_direction: 'desc' or 'asc'
            limit: Maximum number of results
            
        Returns:
            List of document dictionaries with IDs
        """
        db = FirestoreDAO.get_db()
        query = db.collection(collection)
        
        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)
        
        if order_by:
            query = query.order_by(order_by, direction=order_direction)
        
        if limit:
            query = query.limit(limit)
        
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        
        return results 