"""
Data Migration System
Migrates existing data to support user-based isolation.
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

logger = logging.getLogger(__name__)

class DataMigration:
    """Handles migration of existing data to support user isolation."""
    
    def __init__(self, qdrant_client: QdrantClient):
        self.client = qdrant_client
        self.default_user_id = "default_user"
        self.collections_to_migrate = [
            "value_components",
            "value_waterfall_analyses", 
            "website_structure"
        ]
    
    def migrate_all_data(self) -> Dict[str, int]:
        """Migrate all existing data to default user."""
        results = {}
        
        for collection_name in self.collections_to_migrate:
            try:
                migrated_count = self._migrate_collection(collection_name)
                results[collection_name] = migrated_count
                logger.info(f"Migrated {migrated_count} items in {collection_name}")
            except Exception as e:
                logger.error(f"Error migrating {collection_name}: {e}")
                results[collection_name] = 0
        
        return results
    
    def _migrate_collection(self, collection_name: str) -> int:
        """Migrate a specific collection to add user_id field."""
        try:
            # Get all points from collection
            response = self.client.scroll(
                collection_name=collection_name,
                limit=1000  # Adjust based on your data size
            )
            
            if not response[0]:
                logger.info(f"No data to migrate in {collection_name}")
                return 0
            
            migrated_count = 0
            points_to_update = []
            
            for point in response[0]:
                payload = point.payload
                if not payload:
                    continue
                
                # Check if user_id already exists
                if "user_id" in payload:
                    continue
                
                # Add user_id to payload
                payload["user_id"] = self.default_user_id
                
                # Handle vector field - some points might not have vectors
                vector: List[float] = [0.0] * 128  # Default vector
                if hasattr(point, 'vector') and point.vector is not None:
                    if isinstance(point.vector, list) and len(point.vector) > 0:
                        # Ensure it's a flat list of floats
                        first_elem = point.vector[0]
                        if isinstance(first_elem, (int, float)):
                            vector = [float(v) if isinstance(v, (int, float)) else 0.0 for v in point.vector]  # type: ignore[arg-type]
                
                # Prepare point for update
                points_to_update.append(PointStruct(
                    id=point.id,
                    vector=vector,
                    payload=payload
                ))
                
                migrated_count += 1
            
            # Update points in batch
            if points_to_update:
                self.client.upsert(
                    collection_name=collection_name,
                    points=points_to_update
                )
                logger.info(f"Updated {migrated_count} points in {collection_name}")
            
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating collection {collection_name}: {e}")
            raise
    
    def verify_migration(self) -> Dict[str, Dict[str, int]]:
        """Verify that migration was successful."""
        results = {}
        
        for collection_name in self.collections_to_migrate:
            try:
                # Check total count
                total_response = self.client.scroll(
                    collection_name=collection_name,
                    limit=1
                )
                total_count = len(total_response[0]) if total_response[0] else 0
                
                # Check count with user_id
                user_response = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[FieldCondition(key="user_id", match=MatchValue(value=self.default_user_id))]  # type: ignore[arg-type]
                    ),
                    limit=1
                )
                user_count = len(user_response[0]) if user_response[0] else 0
                
                # Check count without user_id
                no_user_response = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must_not=[FieldCondition(key="user_id", match=MatchValue(value=self.default_user_id))]
                    ),
                    limit=1
                )
                no_user_count = len(no_user_response[0]) if no_user_response[0] else 0
                
                results[collection_name] = {
                    "total": total_count,
                    "with_user_id": user_count,
                    "without_user_id": no_user_count,
                    "migration_complete": no_user_count == 0
                }
                
            except Exception as e:
                logger.error(f"Error verifying migration for {collection_name}: {e}")
                results[collection_name] = {
                    "error": str(e)
                }
        
        return results
    
    def rollback_migration(self, collection_name: Optional[str] = None) -> bool:
        """Rollback migration by removing user_id field (use with caution)."""
        try:
            collections: List[str] = [collection_name] if collection_name else self.collections_to_migrate
            
            for coll_name in collections:
                response = self.client.scroll(
                    collection_name=coll_name,
                    limit=1000
                )
                
                if not response[0]:
                    continue
                
                points_to_update = []
                for point in response[0]:
                    payload = point.payload
                    if not payload:
                        continue
                    
                    payload = payload.copy()
                    
                    # Remove user_id field
                    if "user_id" in payload:
                        del payload["user_id"]
                        
                        # Handle vector field
                        vector: List[float] = [0.0] * 128  # Default vector
                        if hasattr(point, 'vector') and point.vector is not None:
                            if isinstance(point.vector, list) and len(point.vector) > 0:
                                # Ensure it's a flat list of floats
                                first_elem = point.vector[0]
                                if isinstance(first_elem, (int, float)):
                                    vector = [float(v) if isinstance(v, (int, float)) else 0.0 for v in point.vector]  # type: ignore[arg-type]
                        
                        points_to_update.append(PointStruct(
                            id=point.id,
                            vector=vector,
                            payload=payload
                        ))
                
                if points_to_update:
                    self.client.upsert(
                        collection_name=coll_name,
                        points=points_to_update
                    )
                    logger.info(f"Rolled back {len(points_to_update)} points in {coll_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back migration: {e}")
            return False 