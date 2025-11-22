from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging
from typing import Optional, Dict, Any, List, Sequence
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import ollama
import uuid
import time # Import time for potential delays
import httpx
import asyncio
from app.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_API_KEY,
    QDRANT_URL,
    COLLECTION_NAME,
    GLOBAL_SETTINGS_COLLECTION,
    VECTOR_DIM,
    INDEX_PARAMS,
    MAX_RETRIES,
    RETRY_DELAY,
    LOG_LEVEL,
    LOG_FORMAT
)
import asyncio
import hashlib
from app.categories import COMPONENT_STRUCTURES
from app.utils.spinner import database_spinner, ai_processing_spinner
import app.utils as utils

# Load environment variables
load_dotenv()

# Lazy Qdrant client to avoid connecting during import
_QDRANT_CLIENT = None

def get_qdrant_client():
    """Get Qdrant client instance (lazy initialization)."""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        # Support both local and cloud Qdrant configurations
        if QDRANT_URL:
            # Cloud Qdrant with URL
            if QDRANT_API_KEY:
                _QDRANT_CLIENT = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            else:
                _QDRANT_CLIENT = QdrantClient(url=QDRANT_URL)
        elif QDRANT_API_KEY:
            # Cloud Qdrant with host/port and API key
            _QDRANT_CLIENT = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, api_key=QDRANT_API_KEY)
        else:
            # Local Qdrant (default)
            _QDRANT_CLIENT = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _QDRANT_CLIENT

# For backward compatibility, create a property that calls the function
class QdrantClientProxy:
    def __getattr__(self, name):
        return getattr(get_qdrant_client(), name)

QDRANT_CLIENT = QdrantClientProxy()

# Configure logging
logger = logging.getLogger(__name__)
upsert_logger = logging.getLogger("upsert")
error_logger = logging.getLogger("error")
info_logger = logging.getLogger("info")

# Collection schemas (for Qdrant, just for reference, not used for creation)
COLLECTIONS = {
    GLOBAL_SETTINGS_COLLECTION: {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    },
    COLLECTION_NAME: {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    },
    "website_structure": {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    },
    "value_components": {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    },
    "personas": {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    },
    "background_tasks": {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    },
    "users": {
        "vector_size": 128,
        "distance": "Cosine"
    },
    "user_sessions": {
        "vector_size": 128,
        "distance": "Cosine"
    },
    "user_activities": {
        "vector_size": 128,
        "distance": "Cosine"
    },
    "archived_data": {
        "vector_size": 128,
        "distance": "Cosine"
    },
    "company_profiles": {
        "vector_size": 128,
        "distance": "Cosine"
    },
    "company_settings": {
        "vector_size": 128,
        "distance": "Cosine"
    },
    "framework_customizations": {
        "vector_size": VECTOR_DIM,
        "distance": "Cosine"
    }
}

PERSONA_COLLECTION = "personas"
PERSONA_VECTOR_DIM = VECTOR_DIM  # Use your existing VECTOR_DIM
GENERATOR_VERSION = "1.0.0"  # Increment this whenever persona generator logic/structure changes

# --- Qdrant helpers ---
def ensure_collection(collection_name: str, vector_size: int, distance: str = "Cosine"):
    """Ensure Qdrant collection exists with correct vector dimensions."""
    collection_recreated = False
    try:
        collection_info = QDRANT_CLIENT.get_collection(collection_name)
        # Check if vector dimension matches - if not, recreate collection
        current_vector_size = None
        try:
            # Try to get vector size from collection config
            vectors_config = collection_info.config.params.vectors
            if hasattr(vectors_config, 'size'):
                current_vector_size = vectors_config.size
            elif hasattr(vectors_config, 'params') and hasattr(vectors_config.params, 'size'):
                current_vector_size = vectors_config.params.size
        except Exception as e:
            logger.warning(f"Could not determine vector size for {collection_name}: {e}")
        
        # If dimension mismatch, recreate collection (this deletes existing data)
        if current_vector_size is not None and current_vector_size != vector_size:
            logger.warning(f"Collection {collection_name} has vector size {current_vector_size}, expected {vector_size}. Recreating collection...")
            QDRANT_CLIENT.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=getattr(models.Distance, distance.upper()))
            )
            logger.info(f"Recreated Qdrant collection {collection_name} with vector size {vector_size}")
            collection_recreated = True
        else:
            logger.debug(f"Collection {collection_name} exists with correct vector size {vector_size}")
    except Exception:
        # Collection doesn't exist, create it
        QDRANT_CLIENT.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=getattr(models.Distance, distance.upper()))
        )
        logger.info(f"Created Qdrant collection: {collection_name} with vector size {vector_size}")
        collection_recreated = True
    
    # After creating/recreating collection, ensure required indexes exist
    if collection_recreated:
        _ensure_collection_indexes(collection_name)

def _ensure_collection_indexes(collection_name: str):
    """Ensure required payload indexes exist for a collection after recreation."""
    try:
        # Define indexes needed for each collection
        indexes = {
            "value_components": [
                {"field": "user_id", "type": models.PayloadSchemaType.KEYWORD},
                {"field": "name", "type": models.PayloadSchemaType.KEYWORD},
                {"field": "main_category", "type": models.PayloadSchemaType.KEYWORD},
                {"field": "category", "type": models.PayloadSchemaType.KEYWORD}
            ],
            "framework_customizations": [
                {"field": "industry_name", "type": models.PayloadSchemaType.KEYWORD}
            ],
            "personas": [
                {"field": "user_id", "type": models.PayloadSchemaType.KEYWORD},
                {"field": "source_website", "type": models.PayloadSchemaType.KEYWORD}
            ],
            "background_tasks": [
                {"field": "task_id", "type": models.PayloadSchemaType.KEYWORD},
                {"field": "user_id", "type": models.PayloadSchemaType.KEYWORD}
            ]
        }
        
        if collection_name in indexes:
            for index_config in indexes[collection_name]:
                try:
                    QDRANT_CLIENT.create_payload_index(
                        collection_name=collection_name,
                        field_name=index_config["field"],
                        field_schema=index_config["type"]
                    )
                    logger.info(f"Created index on '{index_config['field']}' for collection '{collection_name}'")
                except Exception as e:
                    # Index might already exist (if collection wasn't actually recreated)
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        logger.warning(f"Could not create index on '{index_config['field']}' for '{collection_name}': {e}")
    except Exception as e:
        logger.warning(f"Error ensuring indexes for collection '{collection_name}': {e}")

# --- Connection logic ---
def get_connection() -> bool:
    """Qdrant is stateless, so just check if server is up."""
    try:
        QDRANT_CLIENT.get_collections()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return False

async def ensure_connection() -> bool:
    for attempt in range(MAX_RETRIES):
        if get_connection():
            return True
        if attempt < MAX_RETRIES - 1:
            logger.info(f"Retrying Qdrant connection in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
    return False

async def close_connection():
    # Qdrant client is stateless, nothing to close
    pass

# --- Collection management ---
def collection_exists(collection_name: str) -> bool:
    try:
        QDRANT_CLIENT.get_collection(collection_name)
        return True
    except Exception as e:
        logger.error(f"Error checking Qdrant collection existence: {str(e)}")
        return False

def create_collection(collection_name: str, schema: Dict[str, Any]):
    vector_size = schema.get("vector_size", VECTOR_DIM)
    distance = schema.get("distance", "Cosine")
    QDRANT_CLIENT.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=vector_size, distance=getattr(models.Distance, distance.upper()))
    )
    logger.info(f"Qdrant collection created: {collection_name}")

def drop_collection(collection_name: str):
    QDRANT_CLIENT.delete_collection(collection_name)
    logger.info(f"Qdrant collection dropped: {collection_name}")

async def ensure_collections_exist():
    try:
        if not await ensure_connection():
            logger.error("Failed to connect to Qdrant")
            return False
        for collection_name, schema in COLLECTIONS.items():
            ensure_collection(collection_name, schema["vector_size"], schema["distance"])
        # Also ensure indexes exist for all collections (even if not recreated)
        for collection_name in COLLECTIONS.keys():
            _ensure_collection_indexes(collection_name)
        logger.info("All Qdrant collections and indexes ensured.")
        return True
    except Exception as e:
        logger.error(f"Error ensuring Qdrant collections: {str(e)}", exc_info=True)
        return False

# --- Upsert, search, and CRUD helpers ---
def upsert_point(collection_name: str, point_id: int, vector: List[float], payload: dict):
    QDRANT_CLIENT.upsert(
        collection_name=collection_name,
        points=[models.PointStruct(id=point_id, vector=vector, payload=payload)]
    )
    logger.info(f"Upserted point {point_id} in {collection_name}")

def search_points(collection_name: str, query_vector: List[float], limit: int = 5, filter_payload: Optional[dict] = None):
    filter_obj = None
    if filter_payload:
        filter_obj = models.Filter(must=[models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in filter_payload.items()])  # type: ignore[arg-type]
    return QDRANT_CLIENT.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
        filter=filter_obj
    )

# --- Example: save_analysis, get_analysis, etc. ---
# def save_analysis(analysis: Dict[str, Any]) -> bool:
#     vector = analysis["vector"]
#     payload = {k: v for k, v in analysis.items() if k != "vector"}
#     point_id = int(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), 16) % (10 ** 12)
#     upsert_point(COLLECTION_NAME, point_id, vector, payload)
#     return True

def get_opportunity_statistics(*args, **kwargs):
    pass

def search_websites(*args, **kwargs):
    pass

def get_website_details(website: str) -> List[Dict[str, Any]]:
    """Retrieve all analyses for a given website from Qdrant."""
    try:
        # For now, just search by website field in payload
        results = QDRANT_CLIENT.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[models.FieldCondition(key="website", match=models.MatchValue(value=website))]),
            with_payload=True,
            with_vectors=False
        )
        return [point.payload for point in results[0]]
    except Exception as e:
        logger.error(f"Error getting website details: {str(e)}")
        return []

def save_analysis(analysis: Dict[str, Any]) -> bool:
    """Save an analysis document to Qdrant."""
    try:
        vector = analysis["vector"]
        payload = {k: v for k, v in analysis.items() if k != "vector"}
        point_id = int(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), 16) % (10 ** 12)
        upsert_point(COLLECTION_NAME, point_id, vector, payload)
        return True
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")
        return False

def get_value_component(name: str) -> Optional[Dict[str, Any]]:
    """Get a single value component by name from Qdrant."""
    try:
        filter_ = models.Filter(must=[models.FieldCondition(key="name", match=models.MatchValue(value=name))])  # type: ignore[arg-type]
        try:
            results = QDRANT_CLIENT.scroll(
                collection_name="value_components",
                scroll_filter=filter_,
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, fall back to manual filtering
            if "index" in str(e).lower() or "Index required" in str(e):
                logger.warning(f"[database.py] Index not found for name, using manual filtering")
                # Get all points and filter manually
                all_points, _ = QDRANT_CLIENT.scroll(
                    collection_name="value_components",
                    with_payload=True,
                    with_vectors=False
                )
                # Manual filtering
                for point in all_points:
                    if point.payload.get("name", "").lower() == name.lower():
                        return point.payload
                return None
            else:
                raise e
        
        for point in results[0]:
            return point.payload
        return None
    except Exception as e:
        logger.error(f"Error getting value component: {str(e)}")
        return None

def delete_value_component_by_key(main_category: str, category: str, name: str, user_id: Optional[str] = None) -> None:
    """Delete any value component in Qdrant with the same main_category, category, and name. Also remove any entries where both original_value and ai_processed_value are empty. Logs diagnostics for debugging. Now also attempts a fuzzy delete for similar keys."""
    try:
        # Normalize keys
        main_category_norm = (main_category or '').strip().lower()
        category_norm = (category or '').strip().lower()
        name_norm = (name or '').strip().lower()
        logging.warning(f"[database.py][DIAG] Attempting delete for main_category='{main_category_norm}', category='{category_norm}', name='{name_norm}', user_id='{user_id}'")
        
        # Build filter conditions
        filter_conditions = [
            models.FieldCondition(key="main_category", match=models.MatchValue(value=main_category_norm)),
            models.FieldCondition(key="category", match=models.MatchValue(value=category_norm)),
            models.FieldCondition(key="name", match=models.MatchValue(value=name_norm)),
        ]
        
        # Add user_id filter if provided
        if user_id:
            filter_conditions.append(models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)))
        
        filter_ = models.Filter(must=filter_conditions)  # type: ignore[arg-type]
        try:
            points = QDRANT_CLIENT.scroll(
                collection_name="value_components",
                scroll_filter=filter_,
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, fall back to manual filtering
            if "index" in str(e).lower() or "Index required" in str(e):
                logging.warning(f"[database.py] Index not found for main_category/category/name, using manual filtering")
                # Get all points and filter manually
                all_points, _ = QDRANT_CLIENT.scroll(
                    collection_name="value_components",
                    with_payload=True,
                    with_vectors=False
                )
                # Manual filtering
                filtered_points = []
                for point in all_points:
                    payload = point.payload
                    if (payload.get("main_category", "").lower() == main_category_norm and
                        payload.get("category", "").lower() == category_norm and
                        payload.get("name", "").lower() == name_norm):
                        if not user_id or payload.get("user_id") == user_id:
                            filtered_points.append(point)
                points = (filtered_points, None)
            else:
                raise e
        ids_to_delete = [point.id for point in points[0]]
        logging.warning(f"[database.py][DIAG] IDs to delete for {main_category_norm}/{category_norm}/{name_norm}: {ids_to_delete}")
        logging.warning(f"[database.py][DIAG] Payloads to delete: {[p.payload for p in points[0]]}")
        if ids_to_delete:
            QDRANT_CLIENT.delete(
                collection_name="value_components",
                points_selector=models.PointIdsList(points=ids_to_delete)
            )
            logging.warning(f"[database.py][DIAG] Deleted {len(ids_to_delete)} value_component(s) for {main_category_norm}/{category_norm}/{name_norm}")
        else:
            logging.warning(f"[database.py][DIAG] No value_components found to delete for {main_category_norm}/{category_norm}/{name_norm}")
        # --- Additional: Remove any entries for this key where both values are empty ---
        try:
            points_after, _ = QDRANT_CLIENT.scroll(
                collection_name="value_components",
                scroll_filter=filter_,
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, use manual filtering
            if "index" in str(e).lower() or "Index required" in str(e):
                all_points, _ = QDRANT_CLIENT.scroll(
                    collection_name="value_components",
                    with_payload=True,
                    with_vectors=False
                )
                points_after = [p for p in all_points if 
                               p.payload.get("main_category", "").lower() == main_category_norm and
                               p.payload.get("category", "").lower() == category_norm and
                               p.payload.get("name", "").lower() == name_norm and
                               (not user_id or p.payload.get("user_id") == user_id)]
            else:
                points_after = []
        empty_ids = [point.id for point in points_after if not point.payload.get("original_value", "").strip() and not point.payload.get("ai_processed_value", "").strip()]
        if empty_ids:
            QDRANT_CLIENT.delete(
                collection_name="value_components",
                points_selector=models.PointIdsList(points=empty_ids)
            )
            logging.warning(f"[database.py][DIAG] Deleted {len(empty_ids)} empty value_component(s) for {main_category_norm}/{category_norm}/{name_norm}")
        # --- Fuzzy delete: scan all points for similar keys ---
        all_points, _ = QDRANT_CLIENT.scroll(collection_name="value_components", with_payload=True, with_vectors=False)
        fuzzy_ids = []
        fuzzy_payloads = []
        for point in all_points:
            payload = point.payload
            main = (payload.get("main_category") or '').strip().lower()
            cat = (payload.get("category") or '').strip().lower()
            n = (payload.get("name") or '').strip().lower()
            if main == main_category_norm and cat == category_norm and n == name_norm:
                if point.id not in ids_to_delete and point.id not in empty_ids:
                    fuzzy_ids.append(point.id)
                    fuzzy_payloads.append(payload)
        if fuzzy_ids:
            QDRANT_CLIENT.delete(
                collection_name="value_components",
                points_selector=models.PointIdsList(points=fuzzy_ids)
            )
            logging.warning(f"[database.py][DIAG] Fuzzy deleted {len(fuzzy_ids)} value_component(s) for {main_category_norm}/{category_norm}/{name_norm}")
            for p in fuzzy_payloads:
                logging.warning(f"[database.py][DIAG] Fuzzy deleted payload: {p}")
        # Log what remains for this key
        points_final, _ = QDRANT_CLIENT.scroll(
            collection_name="value_components",
            scroll_filter=filter_,
            with_payload=True,
            with_vectors=False
        )
        logging.warning(f"[database.py][DIAG] Remaining payloads for {main_category_norm}/{category_norm}/{name_norm}: {[p.payload for p in points_final]}")
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in delete_value_component_by_key: {e}")

def save_value_component(component: Dict[str, Any]) -> bool:
    """Save a value component to Qdrant, using a new UUID for each upsert. After upsert, clean up old duplicates for the same logical key. Keys are normalized for consistency. Deep diagnostics enabled."""
    import logging
    import time
    import uuid
    from datetime import datetime
    from app.database import get_value_components, clean_duplicate_value_components
    from qdrant_client.http import models
    try:
        # --- Normalize keys ---
        main_category = (component.get('main_category','') or '').strip().lower()
        category = (component.get('category','') or '').strip().lower()
        name = (component.get('name','') or '').strip().lower()
        
        # --- Prevent saving empty entries ---
        if not component.get('original_value', '').strip() and not component.get('ai_processed_value', '').strip():
            logging.warning(f"[save_value_component] Skipping save: both original_value and ai_processed_value are empty for {main_category}/{category}/{name}")
            return False
        
        # --- Add created_at timestamp and ensure user_id is present ---
        payload = component.copy()
        payload['main_category'] = main_category
        payload['category'] = category
        payload['name'] = name
        payload['created_at'] = datetime.utcnow().isoformat()
        
        # Ensure user_id is present (for backward compatibility)
        if 'user_id' not in payload:
            # Use demo_profile_manager to get current user_id (handles demo/normal mode correctly)
            try:
                from app.components.demo_companies.demo_profile_manager import demo_profile_manager
                payload['user_id'] = demo_profile_manager.get_current_user_id()
            except Exception:
                # Fallback to session state if demo_profile_manager unavailable
                import streamlit as st
                payload['user_id'] = st.session_state.get('user_id', 'default_user')
        
        point_id = uuid.uuid4().int % (10 ** 12)
        
        print(f"[save_value_component][DIAG] Upserting point_id={point_id}, payload={payload}")
        
        # --- Always upsert with a dummy vector ---
        upsert_resp = QDRANT_CLIENT.upsert(collection_name="value_components", points=[models.PointStruct(id=point_id, vector=[0.0]*VECTOR_DIM, payload=payload)])
        print(f"[save_value_component][DIAG] Upsert response: {upsert_resp}")
        
        # --- Cleanup: remove old duplicates for this logical key ---
        deleted = clean_duplicate_value_components()
        print(f"[save_value_component][DIAG] Duplicates deleted after upsert: {deleted}")
        
        # --- Delay to allow Qdrant to index ---
        time.sleep(1)
        
        # --- Print all points in the collection for diagnostics ---
        all_points, _ = QDRANT_CLIENT.scroll(collection_name="value_components", with_payload=True, with_vectors=False)
        print("[save_value_component][DIAG] All points in value_components after upsert/cleanup:")
        for p in all_points:
            print(p.payload)
        
        # --- Post-save verification ---
        db_val = get_value_components(main_category=main_category, category=category, name=name)
        print(f"[save_value_component][DIAG] get_value_components result: {db_val}")
        if not db_val or not db_val.get(main_category) or not db_val[main_category]:
            print(f"[save_value_component][ERROR] Post-save verification failed: No value found after upsert and cleanup.")
            return False
        
        # Check if the saved value matches the intended value
        found = False
        for comp in db_val[main_category]:
            print(f"[save_value_component][DIAG] Comparing DB comp: {comp} to payload: {payload}")
            if comp['name'] == name and comp['original_value'] == payload['original_value']:
                found = True
        
        if not found:
            print(f"[save_value_component][ERROR] Post-save verification failed. Expected: {payload['original_value']}, DB: {db_val}")
            return False
        
        return True
    except Exception as e:
        print(f"[save_value_component][CRITICAL] Exception: {e}")
        return False

# --- CLEANUP: Remove duplicate value_components, keep only the latest for each (main_category, category, name) ---
def clean_duplicate_value_components():
    """Scan all value_components and delete all but the latest for each (main_category, category, name), using created_at timestamp. Keys are normalized for consistency."""
    try:
        all_components = []
        scroll_offset = None
        while True:
            results = QDRANT_CLIENT.scroll(
                collection_name="value_components",
                with_payload=True,
                with_vectors=False,
                offset=scroll_offset
            )
            points, next_offset = results
            all_components.extend(points)
            if not next_offset:
                break
            scroll_offset = next_offset
        # Group by normalized (main_category, category, name)
        from collections import defaultdict
        grouped = defaultdict(list)
        for point in all_components:
            payload = point.payload
            key = (
                (payload.get("main_category") or "").strip().lower(),
                (payload.get("category") or "").strip().lower(),
                (payload.get("name") or "").strip().lower()
            )
            grouped[key].append(point)
        deleted = 0
        for key, points in grouped.items():
            if len(points) > 1:
                # Sort by created_at (descending), keep the most recent
                points_sorted = sorted(points, key=lambda p: p.payload.get("created_at") or "", reverse=True)
                to_delete = [p.id for p in points_sorted[1:]]
                if to_delete:
                    QDRANT_CLIENT.delete(
                        collection_name="value_components",
                        points_selector=models.PointIdsList(points=to_delete)
                    )
                    deleted += len(to_delete)
        logger.info(f"[CLEANUP] Total duplicates deleted: {deleted}")
        return deleted
    except Exception as e:
        logger.error(f"[CLEANUP] Error cleaning duplicate value_components: {str(e)}")
        return 0

def fetch_all_value_components(user_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Get all value components from Qdrant, grouped by main_category. If user_id is provided, only fetch user's data."""
    try:
        with database_spinner("fetching value components"):
            all_components = []
            scroll_offset = None
            
            # Debug: Log what we're fetching
            logger.warning(f"[database.py] fetch_all_value_components called with user_id={user_id}")
            
            # Build filter for user-specific data if user_id provided
            if user_id:
                filter_ = models.Filter(must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))])  # type: ignore[arg-type]
                logger.warning(f"[database.py] Using filter for user_id={user_id}")
                try:
                    while True:
                        results = QDRANT_CLIENT.scroll(
                            collection_name="value_components",
                            scroll_filter=filter_,
                            with_payload=True,
                            with_vectors=False,
                            offset=scroll_offset
                        )
                        points, next_offset = results
                        all_components.extend([point.payload for point in points])
                        if not next_offset:
                            break
                        scroll_offset = next_offset
                except Exception as e:
                    # If index error, fall back to manual filtering
                    if "index" in str(e).lower() or "Index required" in str(e):
                        logger.warning(f"[database.py] Index not found for user_id, using manual filtering")
                        # Get all points and filter manually
                        all_points, _ = QDRANT_CLIENT.scroll(
                            collection_name="value_components",
                            with_payload=True,
                            with_vectors=False
                        )
                        all_components = [p.payload for p in all_points if p.payload.get("user_id") == user_id]
                    else:
                        raise e
            else:
                # Fetch all data (backward compatibility)
                while True:
                    results = QDRANT_CLIENT.scroll(
                        collection_name="value_components",
                        with_payload=True,
                        with_vectors=False,
                        offset=scroll_offset
                    )
                    points, next_offset = results
                    all_components.extend([point.payload for point in points])
                    if not next_offset:
                        break
                    scroll_offset = next_offset
            
            grouped = {}
            for comp in all_components:
                main_cat = comp.get("main_category", "Unknown")
                grouped.setdefault(main_cat, []).append(comp)
            
            # Debug: Log what was found
            logger.warning(f"[database.py] Found {len(all_components)} components, grouped into {len(grouped)} categories: {list(grouped.keys())}")
            
            # If no data found for this user, check if there's any data at all in the database
            if len(all_components) == 0 and user_id:
                logger.warning(f"[database.py] No data found for user_id={user_id}, checking if there's any data in database...")
                try:
                    # Check total data in database (without user filter)
                    total_results = QDRANT_CLIENT.scroll(
                        collection_name="value_components",
                        limit=10,
                        with_payload=True,
                        with_vectors=False
                    )
                    total_points = total_results[0]
                    logger.warning(f"[database.py] Total components in database: {len(total_points)}")
                    if len(total_points) > 0:
                        # Show sample of what users have data
                        sample_users = set()
                        for point in total_points[:5]:  # Check first 5 points
                            if 'user_id' in point.payload:
                                sample_users.add(point.payload['user_id'])
                        logger.warning(f"[database.py] Sample users with data: {list(sample_users)}")
                except Exception as e:
                    logger.warning(f"[database.py] Error checking total data: {e}")
            
            return grouped
    except Exception as e:
        logger.error(f"Error getting all value components: {str(e)}")
        return {}

def recreate_value_components_collection():
    """Drop and recreate the value_components collection."""
    try:
        drop_collection("value_components")
        ensure_collection("value_components", VECTOR_DIM)
        return True
    except Exception as e:
        logger.error(f"Error recreating value_components collection: {str(e)}")
        return False

def update_website_value_bricks(*args, **kwargs):
    pass

def save_website_structure(*args, **kwargs):
    pass

def get_website_structure(*args, **kwargs):
    pass

def get_value_components(main_category: str, category: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Fetch value components from Qdrant, standardizing all keys to lowercase for case-insensitive matching."""
    try:
        # Always lowercase keys for consistency
        main_category = main_category.lower()
        category = category.lower()
        must_conditions = [
            models.FieldCondition(key="main_category", match=models.MatchValue(value=main_category)),
            models.FieldCondition(key="category", match=models.MatchValue(value=category)),
        ]
        if name:
            must_conditions.append(models.FieldCondition(key="name", match=models.MatchValue(value=name.lower())))
        filter_ = models.Filter(must=must_conditions)  # type: ignore[arg-type]
        print(f"[get_value_components][DIAG] Using filter: {filter_}")
        try:
            points, _ = QDRANT_CLIENT.scroll(collection_name="value_components", scroll_filter=filter_, limit=100)
            print(f"[get_value_components][DIAG] Raw scroll results: {points}")
        except Exception as e:
            # If index error, fall back to manual filtering
            error_str = str(e).lower()
            if "index" in error_str or "index required" in error_str or "bad request" in error_str:
                logging.warning(f"[database.py] Index not found for main_category/category/name in get_value_components, using manual filtering: {e}")
                # Get all points and filter manually
                try:
                    all_points, _ = QDRANT_CLIENT.scroll(
                        collection_name="value_components",
                        with_payload=True,
                        with_vectors=False
                    )
                    # Manual filtering
                    filtered_points = []
                    for point in all_points:
                        payload = point.payload
                        if (payload.get("main_category", "").lower() == main_category and
                            payload.get("category", "").lower() == category):
                            if not name or payload.get("name", "").lower() == name.lower():
                                filtered_points.append(point)
                    points = (filtered_points, None)
                    print(f"[get_value_components][DIAG] Manual filter results: {len(filtered_points)} points")
                except Exception as e2:
                    logging.error(f"[database.py] Error in manual filtering fallback: {e2}")
                    return {main_category: []} if main_category else {}
            else:
                # For other errors, log and return empty result instead of raising
                logging.error(f"[database.py] Error in get_value_components: {e}")
                return {main_category: []} if main_category else {}
        
        # Parse and group results
        # Handle both tuple (points, offset) and list of points
        if isinstance(points, tuple):
            points_list = points[0]
        else:
            points_list = points
        components = [point.payload for point in points_list]
        grouped = {}
        for comp in components:
            main_cat = comp.get("main_category", "Unknown")
            grouped.setdefault(main_cat, []).append(comp)
        if main_category:
            return {main_category: grouped.get(main_category, [])}
        return grouped
    except Exception as e:
        # Catch any unexpected errors and return empty result
        logging.error(f"[database.py] Unexpected error in get_value_components: {e}")
        return {main_category.lower() if main_category else "": []}

def get_analysis_history() -> list:
    """Return all analyses from the main collection (for history view)."""
    try:
        results = QDRANT_CLIENT.scroll(
            collection_name=COLLECTION_NAME,
            with_payload=True,
            with_vectors=False
        )
        return [point.payload for point in results[0]]
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        return []

def ensure_persona_collection():
    ensure_collection(
        collection_name=PERSONA_COLLECTION,
        vector_size=PERSONA_VECTOR_DIM,
        distance="Cosine"
    )

async def generate_embedding(text: str, model: str = "mistral") -> List[float]:
    """Generate embedding for a given text using Ollama."""
    try:
        with ai_processing_spinner("generating embedding"):
            import httpx
            # Increased timeout to 60 seconds to handle slow Ollama responses
            # Also add connection timeout separately
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0)
            ) as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": model, "prompt": text}
                )
                if response.status_code == 200:
                    embedding = response.json()["embedding"]
                    # Check if embedding dimension matches expected dimension
                    if len(embedding) != VECTOR_DIM:
                        original_len = len(embedding)
                        logger.warning(f"Embedding dimension mismatch: got {original_len}, expected {VECTOR_DIM} (model: {model}). Padding to match.")
                        # Only pad if smaller (never truncate - we want full embeddings)
                        if original_len < VECTOR_DIM:
                            embedding.extend([0.0] * (VECTOR_DIM - original_len))
                            logger.info(f"Padded embedding from {original_len} to {VECTOR_DIM} dimensions")
                        else:
                            # If larger than expected, log warning but use full embedding
                            logger.warning(f"Embedding is larger than expected ({original_len} > {VECTOR_DIM}). Using full embedding.")
                    return embedding
                else:
                    logger.error(f"Error generating embedding: {response.status_code}")
                    return [0.0] * VECTOR_DIM  # Return zero vector as fallback
    except httpx.TimeoutException as e:
        logger.warning(f"Timeout generating embedding (using zero vector): {str(e)}")
        return [0.0] * VECTOR_DIM  # Return zero vector as fallback
    except Exception as e:
        logger.warning(f"Error generating embedding (using zero vector): {str(e)}")
        return [0.0] * VECTOR_DIM  # Return zero vector as fallback

async def save_persona(persona: dict, source_website: Optional[str] = None, user_id: Optional[str] = None):
    try:
        ensure_persona_collection()
        persona_name = persona.get("company", {}).get("name", persona.get("name", ""))
        value_drivers = persona.get("value_drivers", [])
        if value_drivers and isinstance(value_drivers[0], dict):
            value_driver_texts = [vd.get("name", "") for vd in value_drivers]
        else:
            value_driver_texts = value_drivers
        embedding_text = f"{persona_name} {persona.get('industry', '')} {' '.join(value_driver_texts)}"
        persona_id = persona.get('id') or str(uuid.uuid4())
        
        # Try to generate embedding, with fallback to zero vector
        try:
            embedding = await generate_embedding(embedding_text)
        except Exception as e:
            logger.warning(f"Failed to generate embedding for persona '{persona_name}': {e}. Using zero vector.")
            embedding = [0.0] * VECTOR_DIM
        
        # Ensure industry and scan_date are present at the top level
        industry = persona.get("industry")
        scan_date = datetime.utcnow().isoformat()
        
        # FIX: Use provided user_id or fallback to session state
        if user_id is None:
            try:
                import streamlit as st
                user_id = st.session_state.get('user_id', 'default_user')
            except:
                user_id = 'default_user'
        
        # Get user's display name for saving in persona
        created_by_display_name = "Unknown user"
        try:
            from app.auth.user_management import UserManager
            # QDRANT_CLIENT is defined in this module - get actual client instance
            # Ensure user_id is not None before calling
            if user_id:
                user_manager = UserManager(get_qdrant_client())  # type: ignore[arg-type]
                user_data = user_manager.get_user_by_id(user_id)
                if user_data:
                    created_by_display_name = user_data.get("display_name") or user_data.get("username") or "Unknown user"
        except Exception as e:
            logger.warning(f"Could not retrieve display name for user_id {user_id}: {e}. Using fallback.")
            # Try session state as fallback
            try:
                import streamlit as st
                created_by_display_name = st.session_state.get("display_name") or st.session_state.get("username") or "Unknown user"
            except:
                pass
        
        # Add metadata to persona dict itself for easier access
        persona_with_metadata = persona.copy()
        persona_with_metadata["created_at"] = scan_date
        persona_with_metadata["scan_date"] = scan_date
        persona_with_metadata["user_id"] = user_id
        persona_with_metadata["created_by_display_name"] = created_by_display_name
        
        payload = {
            "id": persona_id,
            "created_at": scan_date,
            "scan_date": scan_date,
            "source_website": source_website,
            "generator_version": GENERATOR_VERSION,
            "industry": industry,
            "user_id": user_id,  # FIX: Add user_id for data isolation
            "created_by_display_name": created_by_display_name,  # Store display name in payload too
            "persona": persona_with_metadata  # Save the persona dict with metadata as a snapshot
        }
        
        QDRANT_CLIENT.upsert(
            collection_name=PERSONA_COLLECTION,
            points=[
                models.PointStruct(
                    id=persona_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        upsert_logger.info(f"Successfully saved persona '{persona_name}' with ID {persona_id} for user {user_id}")
        # Return the saved persona dict with ID so it can be used in task results
        # Ensure the persona dict has the ID set at both top level and company level
        persona_with_id = persona_with_metadata.copy()
        # Always set top-level ID
        persona_with_id["id"] = persona_id
        # Also set company.id if company dict exists
        if isinstance(persona_with_id.get("company"), dict):
            persona_with_id["company"]["id"] = persona_id
        return persona_with_id
    except Exception as e:
        error_logger.error(f"Failed to save persona '{persona.get('company', {}).get('name', 'N/A')}': {e}", exc_info=True)
        return None

async def get_personas(query: Optional[dict] = None) -> list:
    """Retrieve persona payloads from Qdrant filtered by user_id."""
    try:
        ensure_persona_collection()
        
        # FIX: Add user_id filtering for data isolation
        import streamlit as st
        user_id = st.session_state.get('user_id', 'default_user')
        
        # Build filter for user-specific data
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        filter_conditions = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        
        # Add additional query filters if provided
        if query:
            for key, value in query.items():
                if key != "user_id":  # Don't override user_id filter
                    filter_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        
        # Scroll through points with user filter
        results, _ = QDRANT_CLIENT.scroll(
            collection_name=PERSONA_COLLECTION,
            scroll_filter=Filter(must=filter_conditions),  # type: ignore[arg-type]
            limit=100,
            with_payload=True
        )
        return [point.payload for point in results]
    except Exception as e:
        logger.error(f"Error getting personas from Qdrant: {str(e)}")
        return []

async def get_persona_by_id(persona_id: str) -> Optional[dict]:
    """Retrieve a single persona by its point ID from Qdrant, filtered by user_id."""
    try:
        # Get all personas and filter by ID (simpler approach)
        import streamlit as st
        user_id = st.session_state.get('user_id', 'default_user')
        
        # Get all personas for the user
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        filter_conditions = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        
        results, _ = QDRANT_CLIENT.scroll(
            collection_name=PERSONA_COLLECTION,
            scroll_filter=Filter(must=filter_conditions),  # type: ignore[arg-type]
            limit=100,
            with_payload=True
        )
        
        # Find the persona with matching ID
        for point in results:
            if point.payload.get("id") == persona_id:
                # Return the persona dict from payload, not the entire payload
                # The payload structure is: {"id": "...", "persona": {...}, ...}
                persona_dict = point.payload.get("persona")
                if persona_dict:
                    # Ensure the persona dict has the ID set for consistency
                    if isinstance(persona_dict, dict):
                        if "id" not in persona_dict:
                            persona_dict["id"] = persona_id
                        # Also ensure company.id is set if company dict exists
                        if isinstance(persona_dict.get("company"), dict) and "id" not in persona_dict["company"]:
                            persona_dict["company"]["id"] = persona_id
                        # Ensure metadata is present (for backward compatibility with old personas)
                        if "created_at" not in persona_dict:
                            persona_dict["created_at"] = point.payload.get("created_at") or point.payload.get("scan_date")
                        if "scan_date" not in persona_dict:
                            persona_dict["scan_date"] = point.payload.get("scan_date") or point.payload.get("created_at")
                        if "user_id" not in persona_dict:
                            persona_dict["user_id"] = point.payload.get("user_id")
                        if "created_by_display_name" not in persona_dict:
                            # Try to get from payload first, then look up user if needed
                            persona_dict["created_by_display_name"] = point.payload.get("created_by_display_name")
                            if not persona_dict["created_by_display_name"] and persona_dict.get("user_id"):
                                try:
                                    from app.auth.user_management import UserManager
                                    user_manager = UserManager(get_qdrant_client())  # type: ignore[arg-type]
                                    user_data = user_manager.get_user_by_id(persona_dict["user_id"])
                                    if user_data:
                                        persona_dict["created_by_display_name"] = user_data.get("display_name") or user_data.get("username") or "Unknown user"
                                    else:
                                        persona_dict["created_by_display_name"] = "Unknown user"
                                except:
                                    persona_dict["created_by_display_name"] = "Unknown user"
                    return persona_dict
                # Fallback: return payload if persona key doesn't exist (backward compatibility)
                return point.payload
        
        return None
    except Exception as e:
        logger.error(f"Error getting persona by ID {persona_id} from Qdrant: {str(e)}")
        return None

async def delete_persona_by_id(persona_id: str) -> bool:
    """Delete a single persona by its UUID from Qdrant, only if owned by current user."""
    try:
        # FIX: Verify user ownership before deletion
        import streamlit as st
        user_id = st.session_state.get('user_id', 'default_user')
        
        # Try to find the persona using filter (requires index)
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            FieldCondition(key="id", match=MatchValue(value=persona_id))
        ]
        
        point_to_delete = None
        
        try:
            # Try to search with filter (requires index on "id" and "user_id")
            results = QDRANT_CLIENT.search(
                collection_name=PERSONA_COLLECTION,
                query_vector=[0.0] * VECTOR_DIM,  # Dummy vector for filtering
                query_filter=Filter(must=filter_conditions),  # type: ignore[arg-type]
                limit=1,
                with_payload=True  # Need payload to verify, and we need point ID
            )
            
            if results:
                # Get the actual point from results (results are ScoredPoint objects)
                point_to_delete = results[0]
        except Exception as e:
            # If index error, fall back to manual filtering
            error_str = str(e).lower()
            if "index" in error_str or "index required" in error_str or "bad request" in error_str:
                logger.warning(f"[database.py] Index not found for persona deletion, using manual filtering")
                # Get all points and filter manually
                all_points, _ = QDRANT_CLIENT.scroll(
                    collection_name=PERSONA_COLLECTION,
                    with_payload=True,
                    with_vectors=False
                )
                # Manual filtering by user_id and payload.id
                matching_points = [
                    p for p in all_points 
                    if p.payload.get("user_id") == user_id and p.payload.get("id") == persona_id
                ]
                if matching_points:
                    point_to_delete = matching_points[0]
            else:
                raise e
        
        if not point_to_delete:
            logger.warning(f"Persona {persona_id} not found or not owned by user {user_id}")
            return False
        
        # Get the actual Qdrant point ID (integer) from the found point
        # point_to_delete could be a ScoredPoint (from search) or a Point (from scroll)
        if hasattr(point_to_delete, 'id'):
            qdrant_point_id = point_to_delete.id
        else:
            # Fallback: if it's a dict or something else, try to get ID
            qdrant_point_id = getattr(point_to_delete, 'id', None)
            if qdrant_point_id is None:
                logger.error(f"Could not extract point ID from search result for persona {persona_id}")
                return False
        
        # Delete using the actual Qdrant point ID (integer)
        response = QDRANT_CLIENT.delete(
            collection_name=PERSONA_COLLECTION,
            points_selector=models.PointIdsList(points=[qdrant_point_id]),
        )
        if response.status == models.UpdateStatus.COMPLETED:
            logger.info(f"Successfully deleted persona with ID: {persona_id} (point_id: {qdrant_point_id}) for user {user_id}")
            return True
        else:
            logger.error(f"Failed to delete persona {persona_id}. Status: {response.status}")
            return False
    except Exception as e:
        logger.error(f"Error deleting persona by ID {persona_id} from Qdrant: {str(e)}")
        return False

def delete_all_personas():
    """Delete the entire personas collection from Qdrant (removes all saved buyer personas)."""
    try:
        QDRANT_CLIENT.delete_collection(PERSONA_COLLECTION)
        logger.info("All buyer personas deleted (personas collection dropped).")
        return True
    except Exception as e:
        logger.error(f"Failed to delete personas collection: {e}")
        return False

SITE_VECTOR_DIM = 1536

def create_site_collection(site_id: str):
    collection_name = f"site_{site_id}"
    ensure_collection(collection_name, SITE_VECTOR_DIM, distance="Cosine")
    return collection_name

def upsert_site_chunk(site_id: str, chunk_text: str, embedding: list, metadata: dict):
    collection_name = f"site_{site_id}"
    point_id = str(uuid.uuid4())
    payload = {"chunk_text": chunk_text, **metadata}
    QDRANT_CLIENT.upsert(
        collection_name=collection_name,
        points=[models.PointStruct(id=point_id, vector=embedding, payload=payload)]
    )
    return point_id

def search_site_chunks(site_id: str, query_embedding: list, top_k: int = 5):
    collection_name = f"site_{site_id}"
    results = QDRANT_CLIENT.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True
    )
    return [point.payload for point in results]

def normalize_all_value_component_keys():
    """One-time migration: Normalize all main_category, category, name keys in value_components to lowercase/stripped. Includes vector in upsert."""
    from qdrant_client.http import models
    print("[normalize_all_value_component_keys] Starting normalization of all value_components...")
    all_points, _ = QDRANT_CLIENT.scroll(collection_name="value_components", with_payload=True, with_vectors=False)
    updated = 0
    for point in all_points:
        payload = point.payload.copy()
        orig_main = payload.get("main_category", "")
        orig_cat = payload.get("category", "")
        orig_name = payload.get("name", "")
        norm_main = (orig_main or "").strip().lower()
        norm_cat = (orig_cat or "").strip().lower()
        norm_name = (orig_name or "").strip().lower()
        if (orig_main != norm_main) or (orig_cat != norm_cat) or (orig_name != norm_name):
            payload["main_category"] = norm_main
            payload["category"] = norm_cat
            payload["name"] = norm_name
            # --- Fetch the vector for this point ---
            vector = None
            try:
                retrieved = QDRANT_CLIENT.retrieve(
                    collection_name="value_components",
                    ids=[point.id],
                    with_payload=False,
                    with_vectors=True
                )
                if retrieved and hasattr(retrieved[0], 'vector'):
                    vector = retrieved[0].vector
            except Exception as e:
                print(f"[normalize_all_value_component_keys] Could not fetch vector for point_id={point.id}: {e}")
            if vector is not None:
                QDRANT_CLIENT.upsert(
                    collection_name="value_components",
                    points=[models.PointStruct(id=point.id, vector=vector, payload=payload)]
                )
                print(f"[normalize_all_value_component_keys] Normalized point_id={point.id}: main_category='{orig_main}'→'{norm_main}', category='{orig_cat}'→'{norm_cat}', name='{orig_name}'→'{norm_name}'")
                updated += 1
            else:
                print(f"[normalize_all_value_component_keys] Skipped point_id={point.id} (no vector found)")
    print(f"[normalize_all_value_component_keys] Normalization complete. Updated {updated} points.")

def run_normalize_all_value_component_keys():
    import logging
    logging.warning("[database.py] Running normalization of all value_component keys...")
    normalize_all_value_component_keys()
    logging.warning("[database.py] Normalization complete.")

# --- Uncomment the following to run normalization at app startup ---
# run_normalize_all_value_component_keys()  # Disabled for performance - run manually if needed

def print_similar_value_components(main_category_substr: str, category_substr: str, name_substr: str):
    """Diagnostic: Print all DB entries where main_category, category, or name contain the provided substrings (case-insensitive, stripped)."""
    from qdrant_client.http import models
    main_sub = (main_category_substr or '').strip().lower()
    cat_sub = (category_substr or '').strip().lower()
    name_sub = (name_substr or '').strip().lower()
    points, _ = QDRANT_CLIENT.scroll(collection_name="value_components", with_payload=True, with_vectors=False)
    matches = []
    for point in points:
        payload = point.payload
        main = (payload.get("main_category") or '').strip().lower()
        cat = (payload.get("category") or '').strip().lower()
        name = (payload.get("name") or '').strip().lower()
        if main_sub in main and cat_sub in cat and name_sub in name:
            matches.append(payload)
    print(f"[print_similar_value_components] Found {len(matches)} matches for substrings: main='{main_sub}', cat='{cat_sub}', name='{name_sub}'")
    for m in matches:
        print(m)

def delete_all_value_components(user_id: Optional[str] = None) -> bool:
    """Delete all value components for a specific user or all users if user_id is None"""
    import logging
    from qdrant_client.http import models
    
    try:
        # Build filter for user_id if provided
        filter_conditions = []
        if user_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            )
        
        # Create filter if we have conditions
        query_filter = None
        if filter_conditions:
            query_filter = models.Filter(must=filter_conditions)  # type: ignore[arg-type]
        
        # Try to delete using filter selector
        try:
            result = QDRANT_CLIENT.delete(
                collection_name="value_components",
                points_selector=models.FilterSelector(filter=query_filter) if query_filter else models.PointIdsList(points=[])
            )
            logging.info(f"[database.py] Deleted all value components for user_id: {user_id}")
            return True
        except Exception as e:
            # If index error, fall back to manual filtering and deletion
            error_str = str(e).lower()
            if "index" in error_str or "index required" in error_str or "bad request" in error_str:
                logging.warning(f"[database.py] Index not found for user_id in delete_all_value_components, using manual filtering")
                # Get all points and filter manually
                all_points, _ = QDRANT_CLIENT.scroll(
                    collection_name="value_components",
                    with_payload=True,
                    with_vectors=False
                )
                # Manual filtering
                if user_id:
                    points_to_delete = [p for p in all_points if p.payload.get("user_id") == user_id]
                else:
                    points_to_delete = all_points
                
                # Extract point IDs
                point_ids = [point.id for point in points_to_delete]
                
                if point_ids:
                    # Delete all matching points
                    QDRANT_CLIENT.delete(
                        collection_name="value_components",
                        points_selector=models.PointIdsList(points=point_ids)
                    )
                    logging.info(f"[database.py] Deleted {len(point_ids)} value components for user_id={user_id} (manual filtering)")
                    return True
                else:
                    logging.info(f"[database.py] No value components found to delete for user_id={user_id}")
                    return True  # Success even if nothing to delete
            else:
                raise e
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in delete_all_value_components: {e}")
        return False

# =============================================================================
# BACKGROUND TASK MANAGEMENT FUNCTIONS
# =============================================================================

def normalize_website(website: str) -> str:
    """
    Normalize website URL for consistent comparison.
    Removes protocol, www, trailing slashes, and converts to lowercase.
    
    Examples:
        "https://www.demo-company.com/" -> "demo-company.com"
        "http://DEMO-COMPANY.COM" -> "demo-company.com"
        "demo-company.com" -> "demo-company.com"
    """
    if not website:
        return ""
    
    # Remove protocol (http://, https://)
    website = website.lower().strip()
    website = website.replace("https://", "").replace("http://", "")
    
    # Remove www.
    if website.startswith("www."):
        website = website[4:]
    
    # Remove trailing slash
    website = website.rstrip("/")
    
    # Remove leading/trailing whitespace again
    website = website.strip()
    
    return website

async def get_any_running_task_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if user has ANY running or pending task (regardless of website).
    Returns the task if found, None otherwise.
    """
    try:
        # Get all tasks for this user
        try:
            points, _ = QDRANT_CLIENT.scroll(
                collection_name="background_tasks",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, get all points and filter manually
            if "Index required" in str(e):
                logging.warning(f"[database.py] Index not found for user_id, using manual filtering")
                points, _ = QDRANT_CLIENT.scroll(
                    collection_name="background_tasks",
                    with_payload=True,
                    with_vectors=False
                )
                # Filter manually by user_id
                points = [p for p in points if p.payload.get("user_id") == user_id]
            else:
                raise e
        
        # Filter by status (running or pending)
        for point in points:
            task = point.payload
            task_status = task.get("status", "")
            
            # Check if status is running or pending
            if task_status in ["running", "pending"]:
                logging.info(f"[database.py] Found running task {task.get('task_id')} for user {user_id}")
                return task
        
        return None
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in get_any_running_task_for_user: {e}")
        return None

async def get_running_task_for_website(user_id: str, website: str) -> Optional[Dict[str, Any]]:
    """
    Check if there's already a running or pending task for a specific website.
    Returns the task if found, None otherwise.
    """
    try:
        # Normalize website for consistent comparison
        normalized_website = normalize_website(website)
        
        if not normalized_website:
            logging.warning(f"[database.py] Empty normalized website, cannot check for running task")
            return None
        
        # Get all tasks for this user
        try:
            points, _ = QDRANT_CLIENT.scroll(
                collection_name="background_tasks",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, get all points and filter manually
            if "Index required" in str(e):
                logging.warning(f"[database.py] Index not found for user_id, using manual filtering")
                points, _ = QDRANT_CLIENT.scroll(
                    collection_name="background_tasks",
                    with_payload=True,
                    with_vectors=False
                )
                # Filter manually by user_id
                points = [p for p in points if p.payload.get("user_id") == user_id]
            else:
                raise e
        
        # Filter by website and status
        for point in points:
            task = point.payload
            task_website = task.get("website", "")
            task_status = task.get("status", "")
            
            # Normalize task website for comparison
            normalized_task_website = normalize_website(task_website)
            
            # Check if website matches and status is running or pending
            if (normalized_task_website == normalized_website and 
                task_status in ["running", "pending"]):
                logging.info(f"[database.py] Found running task {task.get('task_id')} for website {website}")
                return task
        
        return None
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in get_running_task_for_website: {e}")
        return None

async def check_and_create_background_task(user_id: str, website: str) -> tuple[str, str, str]:
    """
    Atomically check if user has ANY running task and create one if allowed.
    Only ONE task per user can run at a time, regardless of website.
    
    Returns:
        tuple: (task_id, status, message)
        - task_id: The task ID (existing or new)
        - status: "created", "already_running", or "error"
        - message: Human-readable message
    """
    try:
        # Normalize website
        normalized_website = normalize_website(website)
        
        if not normalized_website:
            return ("", "error", "Invalid website URL")
        
        # FIRST: Check if user has ANY running task (regardless of website)
        any_running_task = await get_any_running_task_for_user(user_id)
        
        if any_running_task:
            task_id = any_running_task.get("task_id")
            if not task_id:
                return ("", "error", "Task ID not found in running task")
            task_status = any_running_task.get("status", "running")
            running_website = any_running_task.get("website", "unknown")
            logging.info(f"[database.py] User {user_id} already has task {task_id} {task_status} for {running_website}")
            return (task_id, "already_running", f"Persona generation already in progress for {running_website}. Only one generation per user at a time.")
        
        # No existing task, create new one
        task_id = await create_background_task(user_id, normalized_website)
        logging.info(f"[database.py] Created new task {task_id} for website {website}")
        return (task_id, "created", f"New task created for {website}")
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in check_and_create_background_task: {e}")
        return ("", "error", f"Error creating task: {str(e)}")

async def create_background_task(user_id: str, website: str) -> str:
    """Create a new background task and return task_id."""
    try:
        task_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "website": website,
            "status": "running",
            "progress_percent": 0,
            "current_step": "Initializing...",
            "step_description": "Starting persona generation process",
            "error_message": None,
            "result_persona": None,
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
        
        # CRITICAL: Qdrant point IDs must be integers, not UUID strings
        # Convert UUID string to integer hash for point ID
        point_id = abs(hash(task_id)) % (10 ** 12)
        
        # Store in Qdrant
        QDRANT_CLIENT.upsert(
            collection_name="background_tasks",
            points=[models.PointStruct(
                id=point_id,  # Use integer hash, not UUID string
                vector=[0.0] * VECTOR_DIM,  # Dummy vector for Qdrant
                payload=task_data  # UUID string stored in payload for querying
            )]
        )
        
        logging.info(f"[database.py] Created background task {task_id} (point_id: {point_id}) for user {user_id}")
        return task_id
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in create_background_task: {e}")
        raise

async def update_background_task(task_id: str, **updates):
    """Update task progress/status."""
    try:
        logging.info(f"[database.py] Starting update for task {task_id} with updates: {updates}")
        
        # Get current task data
        logging.info(f"[database.py] Getting current task data for {task_id}")
        try:
            points, _ = QDRANT_CLIENT.scroll(
                collection_name="background_tasks",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="task_id",
                            match=models.MatchValue(value=task_id)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, try to get all points and filter manually
            if "Index required" in str(e):
                logging.warning(f"[database.py] Index not found for task_id, using manual filtering")
                points, _ = QDRANT_CLIENT.scroll(
                    collection_name="background_tasks",
                    with_payload=True,
                    with_vectors=False
                )
                # Filter manually
                points = [p for p in points if p.payload.get("task_id") == task_id]
            else:
                raise e
        
        if not points:
            logging.warning(f"[database.py] Task {task_id} not found for update")
            return False
            
        task_data = points[0].payload
        task_data.update(updates)
        task_data["updated_at"] = datetime.now().isoformat()
        
        # CRITICAL: Get the point ID (integer) from the found point, not from task_id (UUID string)
        point_id = points[0].id
        
        logging.info(f"[database.py] Updating task {task_id} (point_id: {point_id}) with data: {task_data}")
        
        # Update in Qdrant with timeout
        import asyncio
        try:
            # Run the synchronous upsert in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: QDRANT_CLIENT.upsert(
                        collection_name="background_tasks",
                        points=[models.PointStruct(
                            id=point_id,  # Use the integer point ID from the found point
                            vector=[0.0] * VECTOR_DIM,
                            payload=task_data
                        )]
                    )
                ),
                timeout=2.0  # 2 second timeout (reduced from 3)
            )
            logging.info(f"[database.py] Successfully updated task {task_id}")
        except asyncio.TimeoutError:
            logging.warning(f"[database.py] Timeout updating task {task_id}, continuing...")
            return False
        except Exception as e:
            logging.error(f"[database.py] Error updating task {task_id}: {e}")
            return False
        
        logging.info(f"[database.py] Successfully updated background task {task_id}")
        return True
        
    except asyncio.TimeoutError:
        logging.error(f"[database.py] Timeout updating task {task_id}")
        return False
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in update_background_task: {e}")
        return False

async def get_background_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task by ID."""
    try:
        try:
            points, _ = QDRANT_CLIENT.scroll(
                collection_name="background_tasks",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="task_id",
                            match=models.MatchValue(value=task_id)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False
            )
        except Exception as e:
            # If index error, try to get all points and filter manually
            if "Index required" in str(e):
                logging.warning(f"[database.py] Index not found for task_id, using manual filtering")
                points, _ = QDRANT_CLIENT.scroll(
                    collection_name="background_tasks",
                    with_payload=True,
                    with_vectors=False
                )
                # Filter manually
                points = [p for p in points if p.payload.get("task_id") == task_id]
            else:
                raise e
        
        if points:
            return points[0].payload
        return None
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in get_background_task: {e}")
        return None

async def get_user_background_tasks(user_id: str) -> List[Dict[str, Any]]:
    """Get all tasks for a user."""
    try:
        points, _ = QDRANT_CLIENT.scroll(
            collection_name="background_tasks",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False
        )
        
        return [point.payload for point in points]
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in get_user_background_tasks: {e}")
        return []

async def cleanup_completed_tasks():
    """Clean up old completed tasks (older than 24 hours)."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Get old completed tasks
        points, _ = QDRANT_CLIENT.scroll(
            collection_name="background_tasks",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="status",
                        match=models.MatchValue(value="completed")
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False
        )
        
        # Filter tasks older than 24 hours
        old_tasks = []
        for point in points:
            try:
                updated_time = datetime.fromisoformat(point.payload.get("updated_at", "").replace('Z', '+00:00'))
                if updated_time < cutoff_time:
                    old_tasks.append(point)
            except:
                # If we can't parse the date, consider it old
                old_tasks.append(point)
        
        # Delete old tasks
        if old_tasks:
            task_ids = [point.id for point in old_tasks]
            QDRANT_CLIENT.delete(
                collection_name="background_tasks",
                points_selector=models.PointIdsList(points=task_ids)
            )
            logging.info(f"[database.py] Cleaned up {len(task_ids)} old background tasks")
        
        return True
        
    except Exception as e:
        logging.error(f"[database.py][ERROR] Exception in cleanup_completed_tasks: {e}")
        return False