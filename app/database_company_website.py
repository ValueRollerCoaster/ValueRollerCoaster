"""
Database operations for company website data caching.
Handles storage and retrieval of scraped company website content.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from qdrant_client.http import models
from app.database import QDRANT_CLIENT

logger = logging.getLogger(__name__)

def create_company_website_collection():
    """Create the company_website_data collection if it doesn't exist."""
    try:
        # Check if collection exists
        collections = QDRANT_CLIENT.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if "company_website_data" not in collection_names:
            QDRANT_CLIENT.create_collection(
                collection_name="company_website_data",
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
            logger.info("Created company_website_data collection")
        else:
            logger.info("company_website_data collection already exists")
            
    except Exception as e:
        logger.error(f"Error creating company_website_data collection: {e}")
        raise

def save_company_website_data(website_url: str, scraped_data: Dict[str, Any], content_hash: str) -> bool:
    """
    Save scraped company website data to the database.
    
    Args:
        website_url: The company's website URL
        scraped_data: Processed content extracted from the website
        content_hash: Hash of the content to detect changes
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        create_company_website_collection()
        
        # Create payload - flatten the scraped data
        payload = {
            "website_url": website_url,
            "last_scraped_at": datetime.utcnow().isoformat(),
            "content_hash": content_hash,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            # Flatten scraped data fields
            "pages_scraped": scraped_data.get('pages_scraped', 0),
            "total_words": scraped_data.get('total_words', 0),
            "content": scraped_data.get('content', {}),
            "scraped_at": scraped_data.get('scraped_at', datetime.utcnow().isoformat())
        }
        
        # Use website_url as the point ID (unique identifier)
        point_id = hash(website_url) % (10 ** 12)
        
        # Upsert the data
        QDRANT_CLIENT.upsert(
            collection_name="company_website_data",
            points=[models.PointStruct(
                id=point_id,
                vector=[0.0] * 384,  # Dummy vector
                payload=payload
            )]
        )
        
        logger.info(f"Saved company website data for {website_url}")
        logger.info(f"Payload keys: {list(payload.keys())}")
        logger.info(f"Content keys: {list(payload.get('scraped_data', {}).keys())}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving company website data: {e}")
        return False

def get_company_website_data() -> Optional[Dict[str, Any]]:
    """
    Get the latest company website data from the database.
    
    Returns:
        Dict containing website data or None if not found
    """
    try:
        create_company_website_collection()
        
        # Get all points (should be only one for single company)
        result = QDRANT_CLIENT.scroll(
            collection_name="company_website_data",
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        points = result[0]
        if points:
            return points[0].payload
        else:
            logger.info("No company website data found")
            return None
            
    except Exception as e:
        logger.error(f"Error getting company website data: {e}")
        return None

def update_company_website_data(website_url: str, scraped_data: Dict[str, Any], content_hash: str) -> bool:
    """
    Update existing company website data.
    
    Args:
        website_url: The company's website URL
        scraped_data: Updated processed content
        content_hash: New content hash
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        create_company_website_collection()
        
        # Get existing data to preserve created_at
        existing_data = get_company_website_data()
        created_at = existing_data.get("created_at", datetime.utcnow().isoformat()) if existing_data else datetime.utcnow().isoformat()
        
        # Create updated payload - flatten the scraped data
        payload = {
            "website_url": website_url,
            "last_scraped_at": datetime.utcnow().isoformat(),
            "content_hash": content_hash,
            "created_at": created_at,
            "updated_at": datetime.utcnow().isoformat(),
            # Flatten scraped data fields
            "pages_scraped": scraped_data.get('pages_scraped', 0),
            "total_words": scraped_data.get('total_words', 0),
            "content": scraped_data.get('content', {}),
            "scraped_at": scraped_data.get('scraped_at', datetime.utcnow().isoformat())
        }
        
        # Use website_url as the point ID
        point_id = hash(website_url) % (10 ** 12)
        
        # Upsert the updated data
        QDRANT_CLIENT.upsert(
            collection_name="company_website_data",
            points=[models.PointStruct(
                id=point_id,
                vector=[0.0] * 384,  # Dummy vector
                payload=payload
            )]
        )
        
        logger.info(f"Updated company website data for {website_url}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating company website data: {e}")
        return False

def delete_company_website_data() -> bool:
    """
    Delete all company website data.
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        create_company_website_collection()
        
        # Get all points and delete them
        result = QDRANT_CLIENT.scroll(
            collection_name="company_website_data",
            with_payload=False,
            with_vectors=False
        )
        
        points = result[0]
        if points:
            point_ids = [point.id for point in points]
            QDRANT_CLIENT.delete(
                collection_name="company_website_data",
                points_selector=models.PointIdsList(points=point_ids)
            )
            logger.info(f"Deleted {len(point_ids)} company website data points")
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting company website data: {e}")
        return False

def get_company_website_info() -> Optional[Dict[str, Any]]:
    """
    Get basic info about company website data (URL, last scraped, etc.).
    
    Returns:
        Dict with basic info or None if not found
    """
    try:
        data = get_company_website_data()
        if data:
            return {
                "website_url": data.get("website_url"),
                "last_scraped_at": data.get("last_scraped_at"),
                "content_hash": data.get("content_hash"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at")
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting company website info: {e}")
        return None
