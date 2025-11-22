"""
User Management System
Handles user creation, authentication, and session management.
"""

import hashlib
import time
import uuid
import logging
from typing import Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

class UserManager:
    """Manages user accounts and authentication."""
    
    def __init__(self, qdrant_client: Optional[QdrantClient] = None):
        self.client = qdrant_client
        self.users_collection = "users"
        self._collection_ensured = False  # Track if collection has been ensured
    
    def _ensure_client(self):
        """Ensure the Qdrant client is available."""
        if self.client is None:
            from app.database import QDRANT_CLIENT
            self.client = QDRANT_CLIENT
    
    def _ensure_users_collection(self):
        """Ensure the users collection exists."""
        if self._collection_ensured:
            return
        
        self._ensure_client()
        
        if not self.client:
            logger.error("Qdrant client is not available")
            raise RuntimeError("Qdrant client is not available")
            
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.users_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.users_collection,
                    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                )
                logger.info(f"Created users collection: {self.users_collection}")
                
                # Create default user
                self._create_default_user()
            else:
                logger.info(f"Users collection already exists: {self.users_collection}")
            
            self._collection_ensured = True
                
        except Exception as e:
            logger.error(f"Error ensuring users collection: {e}")
            raise
    
    def _create_default_user(self):
        """Create the default user for existing data migration."""
        if not self.client:
            logger.error("Qdrant client is not available")
            return
        
        default_user = {
            "user_id": "default_user",
            "username": "default_user",
            "display_name": "Default User",
            "password_hash": self._hash_password("default"),
            "created_at": time.time(),
            "is_active": True
        }
        
        try:
            self.client.upsert(
                collection_name=self.users_collection,
                points=[PointStruct(
                    id=hash(default_user["user_id"]) % (2**63),  # Convert to integer ID
                    vector=[0.0] * 128,  # Dummy vector
                    payload=default_user
                )]
            )
            logger.info("Created default user for data migration")
        except Exception as e:
            logger.error(f"Error creating default user: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user account."""
        self._ensure_users_collection()
        if not self.client:
            raise RuntimeError("Qdrant client is not available")
        
        try:
            # Check if username already exists
            existing_user = self.get_user_by_username(username)
            if existing_user:
                raise ValueError(f"Username '{username}' already exists")
            
            user_id = str(uuid.uuid4())
            user_data = {
                "user_id": user_id,
                "username": username,
                "display_name": display_name or username,
                "password_hash": self._hash_password(password),
                "created_at": time.time(),
                "is_active": True
            }
            
            self.client.upsert(
                collection_name=self.users_collection,
                points=[PointStruct(
                    id=hash(user_id) % (2**63),  # Convert to integer ID
                    vector=[0.0] * 128,  # Dummy vector
                    payload=user_data
                )]
            )
            
            logger.info(f"Created new user: {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password."""
        self._ensure_users_collection()
        try:
            user = self.get_user_by_username(username)
            if not user:
                return None
            
            if not user.get("is_active", True):
                logger.warning(f"Login attempt for inactive user: {username}")
                return None
            
            password_hash = self._hash_password(password)
            if user["password_hash"] == password_hash:
                logger.info(f"Successful authentication for user: {username}")
                return user
            else:
                logger.warning(f"Failed authentication for user: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        self._ensure_users_collection()
        if not self.client:
            return None
        
        try:
            response = self.client.scroll(
                collection_name=self.users_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="username", match=MatchValue(value=username))]  # type: ignore[arg-type]
                ),
                limit=1
            )
            
            if response[0]:
                return response[0][0].payload
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id."""
        self._ensure_users_collection()
        if not self.client:
            return None
        
        try:
            response = self.client.scroll(
                collection_name=self.users_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                ),
                limit=1
            )
            
            if response[0]:
                return response[0][0].payload
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_all_users(self) -> list:
        """Get all users from the database."""
        self._ensure_users_collection()
        if not self.client:
            return []
        
        try:
            response = self.client.scroll(
                collection_name=self.users_collection,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            users = []
            for point in response[0]:
                user_data = point.payload
                if not user_data:
                    continue
                
                # Add some default values for display
                if 'last_login' not in user_data:
                    user_data['last_login'] = 'Never'
                if 'login_count' not in user_data:
                    user_data['login_count'] = 0
                if 'email' not in user_data:
                    user_data['email'] = 'N/A'
                users.append(user_data)
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def update_user_status(self, user_id: str, is_active: bool) -> bool:
        """Update user active status."""
        self._ensure_users_collection()
        if not self.client:
            return False
        
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            user['is_active'] = is_active
            user['updated_at'] = time.time()
            
            self.client.upsert(
                collection_name=self.users_collection,
                points=[PointStruct(
                    id=hash(user_id) % (2**63),
                    vector=[0.0] * 128,
                    payload=user
                )]
            )
            
            logger.info(f"Updated user {user_id} status to {'active' if is_active else 'inactive'}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user status: {e}")
            return False
    
    def reset_user_password(self, user_id: str, new_password: Optional[str] = None) -> Dict[str, Any]:
        """Reset a user's password (admin function)."""
        self._ensure_users_collection()
        if not self.client:
            return {"success": False, "error": "Qdrant client is not available"}
        
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return {"success": False, "error": "User not found"}
            
            # Generate temporary password if not provided
            if not new_password:
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits
                new_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Update user password
            user['password_hash'] = self._hash_password(new_password)
            user['password_reset_at'] = time.time()
            user['force_password_change'] = True
            user['updated_at'] = time.time()
            
            self.client.upsert(
                collection_name=self.users_collection,
                points=[PointStruct(
                    id=hash(user_id) % (2**63),
                    vector=[0.0] * 128,
                    payload=user
                )]
            )
            
            logger.info(f"Password reset for user: {user_id}")
            return {
                "success": True,
                "temporary_password": new_password,
                "user_id": user_id,
                "username": user.get('username', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return {"success": False, "error": str(e)}
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information."""
        self._ensure_users_collection()
        if not self.client:
            return False
        
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Update user data
            user.update(updates)
            
            self.client.upsert(
                collection_name=self.users_collection,
                points=[PointStruct(
                    id=hash(user_id) % (2**63),  # Convert to integer ID
                    vector=[0.0] * 128,
                    payload=user
                )]
            )
            
            logger.info(f"Updated user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user account."""
        self._ensure_users_collection()
        if not self.client:
            return False
        
        try:
            # Find the point ID for this user
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Get all points to find the one with this user_id
            response = self.client.scroll(
                collection_name=self.users_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                ),
                limit=1
            )
            
            if response[0]:
                point_id = response[0][0].id
                self.client.delete(
                    collection_name=self.users_collection,
                    points_selector=[point_id]  # type: ignore[arg-type]
                )
                
                logger.info(f"Deleted user: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False 