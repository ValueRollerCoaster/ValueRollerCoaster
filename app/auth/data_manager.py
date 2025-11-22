"""
Data Management System for Admin Operations
Handles bulk data cleanup, migration, backup, archiving, and storage optimization
"""

import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
import hashlib

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data operations for admin functions."""
    
    def __init__(self, qdrant_client: QdrantClient):
        self.client = qdrant_client
        self.backup_dir = "backups"
        self.archive_collection = "archived_data"
        self._ensure_archive_collection()
        self._ensure_backup_dir()
    
    def _ensure_archive_collection(self):
        """Ensure archive collection exists."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.archive_collection not in collection_names:
                from qdrant_client.models import VectorParams, Distance
                self.client.create_collection(
                    collection_name=self.archive_collection,
                    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                )
                logger.info(f"Created archive collection: {self.archive_collection}")
                
        except Exception as e:
            logger.error(f"Error ensuring archive collection: {e}")
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
                logger.info(f"Created backup directory: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Error creating backup directory: {e}")
    
    def bulk_data_cleanup(self, days_old: int = 90, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up old and unused data across all users."""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            cleanup_stats = {
                "value_components": {"found": 0, "deleted": 0},
                "personas": {"found": 0, "deleted": 0},
                "analyses": {"found": 0, "deleted": 0},
                "total_space_saved_mb": 0
            }
            
            collections_to_clean = ["value_components", "personas", "value_waterfall_analyses"]
            
            for collection_name in collections_to_clean:
                try:
                    # Find old data
                    response = self.client.scroll(
                        collection_name=collection_name,
                        scroll_filter=Filter(
                            must=[FieldCondition(key="created_at", match=MatchValue(value=cutoff_time, range={"lt": cutoff_time}))]  # type: ignore[arg-type]
                        ),
                        limit=10000,
                        with_payload=False,
                        with_vectors=False
                    )
                    
                    old_data = response[0]
                    cleanup_stats[collection_name.replace("value_waterfall_", "")]["found"] = len(old_data)
                    
                    if not dry_run and old_data:
                        point_ids = [point.id for point in old_data]
                        self.client.delete(
                            collection_name=collection_name,
                            points_selector=point_ids  # type: ignore[arg-type]
                        )
                        cleanup_stats[collection_name.replace("value_waterfall_", "")]["deleted"] = len(point_ids)
                        cleanup_stats["total_space_saved_mb"] += len(point_ids) * 0.1  # Rough estimate
                        
                        logger.info(f"Cleaned up {len(point_ids)} old records from {collection_name}")
                        
                except Exception as e:
                    logger.error(f"Error cleaning up {collection_name}: {e}")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error in bulk data cleanup: {e}")
            return {"error": str(e)}
    
    def migrate_data_between_users(self, source_user_id: str, target_user_id: str, 
                                 collections: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
        """Migrate data between users."""
        try:
            if not collections:
                collections = ["value_components", "personas", "value_waterfall_analyses"]
            
            migration_stats = {
                "migrated_items": 0,
                "collections_processed": [],
                "errors": []
            }
            
            for collection_name in collections:
                try:
                    # Get source user data
                    response = self.client.scroll(
                        collection_name=collection_name,
                        scroll_filter=Filter(
                            must=[FieldCondition(key="user_id", match=MatchValue(value=source_user_id))]  # type: ignore[arg-type]
                        ),
                        limit=10000,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    source_data = response[0]
                    if not source_data:
                        continue
                    
                    # Update user_id in data
                    updated_points = []
                    for point in source_data:
                        payload = point.payload
                        if not payload:
                            continue
                        
                        payload = payload.copy()
                        payload["user_id"] = target_user_id
                        payload["migrated_at"] = time.time()
                        payload["migrated_from"] = source_user_id
                        
                        updated_points.append(PointStruct(
                            id=point.id,
                            vector=[0.0] * 128,  # Dummy vector
                            payload=payload
                        ))
                    
                    if not dry_run and updated_points:
                        self.client.upsert(
                            collection_name=collection_name,
                            points=updated_points
                        )
                        migration_stats["migrated_items"] += len(updated_points)
                        migration_stats["collections_processed"].append(collection_name)
                        
                        logger.info(f"Migrated {len(updated_points)} items from {source_user_id} to {target_user_id} in {collection_name}")
                    
                except Exception as e:
                    error_msg = f"Error migrating {collection_name}: {e}"
                    migration_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return migration_stats
            
        except Exception as e:
            logger.error(f"Error in data migration: {e}")
            return {"error": str(e)}
    
    def create_system_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a complete system backup."""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Type narrowing: backup_name is guaranteed to be str here
            if not isinstance(backup_name, str):
                return {"success": False, "error": "Failed to generate backup name"}
            
            backup_data = {
                "backup_info": {
                    "name": backup_name,
                    "created_at": time.time(),
                    "created_datetime": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "collections": {}
            }
            
            # Get all collections
            collections = self.client.get_collections()
            
            for collection in collections.collections:
                collection_name = collection.name
                try:
                    # Get all data from collection
                    response = self.client.scroll(
                        collection_name=collection_name,
                        limit=100000,  # Large limit for backup
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    collection_data = []
                    for point in response[0]:
                        collection_data.append(point.payload)
                    
                    backup_data["collections"][collection_name] = {
                        "count": len(collection_data),
                        "data": collection_data
                    }
                    
                    logger.info(f"Backed up {len(collection_data)} items from {collection_name}")
                    
                except Exception as e:
                    logger.error(f"Error backing up {collection_name}: {e}")
                    backup_data["collections"][collection_name] = {"error": str(e)}
            
            # Save backup to file
            backup_file = os.path.join(self.backup_dir, f"{backup_name}.json")
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"System backup created: {backup_file}")
            return {
                "success": True,
                "backup_file": backup_file,
                "backup_name": backup_name,
                "collections_backed_up": len(backup_data["collections"]),
                "total_items": sum(col.get("count", 0) for col in backup_data["collections"].values() if isinstance(col, dict))
            }
            
        except Exception as e:
            logger.error(f"Error creating system backup: {e}")
            return {"success": False, "error": str(e)}
    
    def restore_from_backup(self, backup_file: str, dry_run: bool = True) -> Dict[str, Any]:
        """Restore system from backup file."""
        try:
            if not os.path.exists(backup_file):
                return {"success": False, "error": "Backup file not found"}
            
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            restore_stats = {
                "collections_restored": 0,
                "items_restored": 0,
                "errors": []
            }
            
            for collection_name, collection_data in backup_data["collections"].items():
                try:
                    if "error" in collection_data:
                        restore_stats["errors"].append(f"Collection {collection_name}: {collection_data['error']}")
                        continue
                    
                    data_items = collection_data.get("data", [])
                    if not data_items:
                        continue
                    
                    # Prepare points for restoration
                    points = []
                    for item in data_items:
                        points.append(PointStruct(
                            id=hash(str(item)) % (2**63),  # Generate new ID
                            vector=[0.0] * 128,
                            payload=item
                        ))
                    
                    if not dry_run and points:
                        self.client.upsert(
                            collection_name=collection_name,
                            points=points
                        )
                        restore_stats["items_restored"] += len(points)
                        restore_stats["collections_restored"] += 1
                        
                        logger.info(f"Restored {len(points)} items to {collection_name}")
                    
                except Exception as e:
                    error_msg = f"Error restoring {collection_name}: {e}"
                    restore_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return restore_stats
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return {"success": False, "error": str(e)}
    
    def archive_inactive_user_data(self, days_inactive: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """Archive data from inactive users."""
        try:
            cutoff_time = time.time() - (days_inactive * 24 * 60 * 60)
            archive_stats = {
                "users_archived": 0,
                "items_archived": 0,
                "space_saved_mb": 0,
                "archived_users": []
            }
            
            # Get all users
            from app.auth.user_management import UserManager
            user_manager = UserManager(self.client)
            all_users = user_manager.get_all_users()
            
            collections_to_archive = ["value_components", "personas", "value_waterfall_analyses"]
            
            for user in all_users:
                user_id = user.get("user_id")
                last_login = user.get("last_login")
                
                # Check if user is inactive
                if last_login == "Never" or (isinstance(last_login, (int, float)) and last_login < cutoff_time):
                    user_archive_stats = {"user_id": user_id, "items": 0}
                    
                    for collection_name in collections_to_archive:
                        try:
                            # Get user data
                            response = self.client.scroll(
                                collection_name=collection_name,
                                scroll_filter=Filter(
                                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                                ),
                                limit=10000,
                                with_payload=True,
                                with_vectors=False
                            )
                            
                            user_data = response[0]
                            if not user_data:
                                continue
                            
                            # Archive data
                            archive_points = []
                            for point in user_data:
                                payload = point.payload
                                if not payload:
                                    continue
                                
                                payload = payload.copy()
                                payload["archived_at"] = time.time()
                                payload["archived_from_collection"] = collection_name
                                payload["original_user_id"] = user_id
                                
                                archive_points.append(PointStruct(
                                    id=hash(f"{user_id}_{collection_name}_{point.id}") % (2**63),
                                    vector=[0.0] * 128,
                                    payload=payload
                                ))
                            
                            if not dry_run and archive_points:
                                self.client.upsert(
                                    collection_name=self.archive_collection,
                                    points=archive_points
                                )
                                user_archive_stats["items"] += len(archive_points)
                                
                                # Delete from original collection
                                point_ids = [point.id for point in user_data]
                                self.client.delete(
                                    collection_name=collection_name,
                                    points_selector=point_ids  # type: ignore[arg-type]
                                )
                                
                                logger.info(f"Archived {len(archive_points)} items for user {user_id} from {collection_name}")
                            
                        except Exception as e:
                            logger.error(f"Error archiving data for user {user_id} from {collection_name}: {e}")
                    
                    if user_archive_stats["items"] > 0:
                        archive_stats["users_archived"] += 1
                        archive_stats["items_archived"] += user_archive_stats["items"]
                        archive_stats["space_saved_mb"] += user_archive_stats["items"] * 0.1
                        archive_stats["archived_users"].append(user_archive_stats)
            
            return archive_stats
            
        except Exception as e:
            logger.error(f"Error archiving inactive user data: {e}")
            return {"error": str(e)}
    
    def analyze_storage_usage(self) -> Dict[str, Any]:
        """Analyze storage usage and identify optimization opportunities."""
        try:
            storage_analysis = {
                "collections": {},
                "total_items": 0,
                "estimated_storage_mb": 0,
                "duplicates_found": 0,
                "optimization_recommendations": []
            }
            
            collections = self.client.get_collections()
            
            for collection in collections.collections:
                collection_name = collection.name
                try:
                    # Get collection info
                    collection_info = self.client.get_collection(collection_name)
                    
                    # Get sample data for analysis
                    response = self.client.scroll(
                        collection_name=collection_name,
                        limit=1000,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    items = response[0]
                    points_count = collection_info.points_count if collection_info.points_count is not None else 0
                    storage_analysis["collections"][collection_name] = {
                        "total_points": points_count,
                        "sample_size": len(items),
                        "estimated_size_mb": points_count * 0.1
                    }
                    
                    storage_analysis["total_items"] += points_count
                    storage_analysis["estimated_storage_mb"] += points_count * 0.1
                    
                    # Check for duplicates (simple hash-based check)
                    if items:
                        content_hashes = {}
                        for item in items:
                            content_str = json.dumps(item.payload, sort_keys=True)
                            content_hash = hashlib.md5(content_str.encode()).hexdigest()
                            
                            if content_hash in content_hashes:
                                storage_analysis["duplicates_found"] += 1
                            else:
                                content_hashes[content_hash] = item.id
                    
                except Exception as e:
                    logger.error(f"Error analyzing collection {collection_name}: {e}")
            
            # Generate recommendations
            if storage_analysis["duplicates_found"] > 0:
                storage_analysis["optimization_recommendations"].append(
                    f"Found {storage_analysis['duplicates_found']} potential duplicate items"
                )
            
            if storage_analysis["estimated_storage_mb"] > 100:
                storage_analysis["optimization_recommendations"].append(
                    "Consider archiving old data to reduce storage usage"
                )
            
            return storage_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing storage usage: {e}")
            return {"error": str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        try:
            backups = []
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.backup_dir, filename)
                        file_stats = os.stat(filepath)
                        
                        backup_info = {
                            "filename": filename,
                            "filepath": filepath,
                            "size_mb": file_stats.st_size / (1024 * 1024),
                            "created_at": file_stats.st_ctime,
                            "created_datetime": datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                        }
                        
                        # Try to get backup metadata
                        try:
                            with open(filepath, 'r') as f:
                                backup_data = json.load(f)
                                backup_info["backup_name"] = backup_data.get("backup_info", {}).get("name", filename)
                                backup_info["collections_count"] = len(backup_data.get("collections", {}))
                                backup_info["total_items"] = sum(
                                    col.get("count", 0) for col in backup_data.get("collections", {}).values() 
                                    if isinstance(col, dict)
                                )
                        except Exception:
                            pass
                        
                        backups.append(backup_info)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def delete_backup(self, backup_filename: str) -> bool:
        """Delete a backup file."""
        try:
            backup_file = os.path.join(self.backup_dir, backup_filename)
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"Deleted backup: {backup_filename}")
                return True
            else:
                logger.error(f"Backup file not found: {backup_filename}")
                return False
        except Exception as e:
            logger.error(f"Error deleting backup {backup_filename}: {e}")
            return False 