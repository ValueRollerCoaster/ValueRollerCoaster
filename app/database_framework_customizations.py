"""
Framework Customizations Database
Stores industry framework customizations (added/removed/modified items)
Shared across all users - admin-only feature
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from qdrant_client.http import models
from app.database import QDRANT_CLIENT, ensure_collection, VECTOR_DIM

logger = logging.getLogger(__name__)

# Collection name for framework customizations
FRAMEWORK_CUSTOMIZATIONS_COLLECTION = "framework_customizations"

def ensure_framework_customizations_collection():
    """Ensure the framework customizations collection exists with proper indexes"""
    ensure_collection(FRAMEWORK_CUSTOMIZATIONS_COLLECTION, VECTOR_DIM, "Cosine")
    
    # Create index on industry_name for efficient filtering
    try:
        QDRANT_CLIENT.create_payload_index(
            collection_name=FRAMEWORK_CUSTOMIZATIONS_COLLECTION,
            field_name="industry_name",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        logger.info(f"Created index on 'industry_name' for {FRAMEWORK_CUSTOMIZATIONS_COLLECTION}")
    except Exception as e:
        # Index might already exist, which is fine
        if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
            logger.warning(f"Could not create index on 'industry_name' (may already exist): {e}")

# Note: Framework customizations are shared across all users (admin-only feature)
# No user_id needed - customizations are per-industry only

def save_framework_customization(industry_name: str, customizations: Dict[str, Any]) -> bool:
    """
    Save framework customizations for an industry (shared across all users)
    
    Args:
        industry_name: Normalized industry name (e.g., "construction")
        customizations: Dict with structure:
            {
                "added_items": {
                    "key_metrics": ["Project completion time"],
                    "trend_areas": [...]
                },
                "removed_items": {
                    "key_metrics": ["Some metric"],
                    ...
                },
                "modified_items": {
                    "key_metrics": {
                        "old": "Old value",
                        "new": "New value"
                    }
                }
            }
    
    Returns:
        bool: True if saved successfully
    """
    try:
        ensure_framework_customizations_collection()
        
        normalized_industry = industry_name.lower().replace(" ", "_")
        
        # Create unique ID from industry only (shared across all users)
        point_id = abs(hash(normalized_industry)) % (10 ** 12)
        
        payload = {
            "industry_name": normalized_industry,
            "customizations": customizations,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        QDRANT_CLIENT.upsert(
            collection_name=FRAMEWORK_CUSTOMIZATIONS_COLLECTION,
            points=[models.PointStruct(
                id=point_id,
                vector=[0.0] * VECTOR_DIM,  # Dummy vector
                payload=payload
            )]
        )
        
        logger.info(f"Saved framework customizations for industry: {normalized_industry} (shared across all users)")
        return True
        
    except Exception as e:
        logger.error(f"Error saving framework customizations: {e}", exc_info=True)
        return False

def get_framework_customization(industry_name: str) -> Optional[Dict[str, Any]]:
    """
    Get framework customizations for an industry (shared across all users)
    
    Args:
        industry_name: Normalized industry name
    
    Returns:
        Dict with customizations or None if not found
    """
    try:
        ensure_framework_customizations_collection()
        
        normalized_industry = industry_name.lower().replace(" ", "_")
        
        # Search for customizations (no user_id filter - shared across all users)
        # Use scroll without filter if index doesn't exist, then filter manually
        try:
            results = QDRANT_CLIENT.scroll(
                collection_name=FRAMEWORK_CUSTOMIZATIONS_COLLECTION,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="industry_name",
                            match=models.MatchValue(value=normalized_industry)
                        )
                    ]
                ),
                limit=1
            )
        except Exception as e:
            # If index error, fall back to manual filtering
            if "index" in str(e).lower() or "Index required" in str(e):
                logger.warning(f"Index not found for industry_name, using manual filtering: {e}")
                all_results = QDRANT_CLIENT.scroll(
                    collection_name=FRAMEWORK_CUSTOMIZATIONS_COLLECTION,
                    limit=100  # Get all customizations (should be small number)
                )
                # Filter manually
                points = all_results[0] if all_results[0] else []
                matching_points = [p for p in points if p.payload.get("industry_name") == normalized_industry]
                if matching_points:
                    return matching_points[0].payload.get("customizations")
                return None
            else:
                raise e
        
        if results[0]:  # results is (points, next_page_offset)
            point = results[0][0]
            return point.payload.get("customizations")
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting framework customizations: {e}", exc_info=True)
        return None

def apply_customizations_to_framework(framework_data: Dict[str, Any], industry_name: str) -> Dict[str, Any]:
    """
    Apply saved customizations to a framework
    
    Args:
        framework_data: Original framework data
        industry_name: Normalized industry name
    
    Returns:
        Framework data with customizations applied
    """
    customizations = get_framework_customization(industry_name)
    
    if not customizations:
        return framework_data
    
    # Create a copy to avoid modifying original
    customized_framework = framework_data.copy()
    
    # Apply added items
    added_items = customizations.get("added_items", {})
    for property_name, items in added_items.items():
        if property_name in customized_framework and isinstance(customized_framework[property_name], list):
            # Add items that don't already exist
            for item in items:
                if item not in customized_framework[property_name]:
                    customized_framework[property_name].append(item)
    
    # Apply removed items
    removed_items = customizations.get("removed_items", {})
    for property_name, items in removed_items.items():
        if property_name in customized_framework and isinstance(customized_framework[property_name], list):
            for item in items:
                if item in customized_framework[property_name]:
                    customized_framework[property_name].remove(item)
    
    # Apply modified items (replace)
    modified_items = customizations.get("modified_items", {})
    for property_name, modifications in modified_items.items():
        if property_name in customized_framework and isinstance(customized_framework[property_name], list):
            for mod in modifications:
                old_value = mod.get("old")
                new_value = mod.get("new")
                try:
                    index = customized_framework[property_name].index(old_value)
                    customized_framework[property_name][index] = new_value
                except ValueError:
                    # Old value not found, skip
                    pass
    
    return customized_framework

def update_customization_add_item(industry_name: str, property_name: str, item: str) -> bool:
    """Add an item to customizations"""
    customizations = get_framework_customization(industry_name) or {
        "added_items": {},
        "removed_items": {},
        "modified_items": {}
    }
    
    if "added_items" not in customizations:
        customizations["added_items"] = {}
    
    if property_name not in customizations["added_items"]:
        customizations["added_items"][property_name] = []
    
    # Add item if not already there
    if item not in customizations["added_items"][property_name]:
        customizations["added_items"][property_name].append(item)
    
    # Remove from removed_items if it was there
    if "removed_items" in customizations:
        if property_name in customizations["removed_items"]:
            if item in customizations["removed_items"][property_name]:
                customizations["removed_items"][property_name].remove(item)
                if not customizations["removed_items"][property_name]:
                    del customizations["removed_items"][property_name]
    
    return save_framework_customization(industry_name, customizations)

def update_customization_remove_item(industry_name: str, property_name: str, item: str) -> bool:
    """Remove an item from customizations"""
    customizations = get_framework_customization(industry_name) or {
        "added_items": {},
        "removed_items": {},
        "modified_items": {}
    }
    
    if "removed_items" not in customizations:
        customizations["removed_items"] = {}
    
    if property_name not in customizations["removed_items"]:
        customizations["removed_items"][property_name] = []
    
    # Add to removed_items if not already there
    if item not in customizations["removed_items"][property_name]:
        customizations["removed_items"][property_name].append(item)
    
    # Remove from added_items if it was there
    if "added_items" in customizations:
        if property_name in customizations["added_items"]:
            if item in customizations["added_items"][property_name]:
                customizations["added_items"][property_name].remove(item)
                if not customizations["added_items"][property_name]:
                    del customizations["added_items"][property_name]
    
    return save_framework_customization(industry_name, customizations)

def update_customization_replace_item(industry_name: str, property_name: str, old_item: str, new_item: str) -> bool:
    """Replace an item in customizations"""
    customizations = get_framework_customization(industry_name) or {
        "added_items": {},
        "removed_items": {},
        "modified_items": {}
    }
    
    if "modified_items" not in customizations:
        customizations["modified_items"] = {}
    
    if property_name not in customizations["modified_items"]:
        customizations["modified_items"][property_name] = []
    
    # Add modification
    modification = {"old": old_item, "new": new_item}
    # Check if this modification already exists
    existing_mods = customizations["modified_items"][property_name]
    for mod in existing_mods:
        if mod.get("old") == old_item:
            mod["new"] = new_item  # Update existing
            break
    else:
        existing_mods.append(modification)
    
    return save_framework_customization(industry_name, customizations)

