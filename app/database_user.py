"""
User-Aware Database Operations
Extends the existing database functionality with user-based filtering.
"""

import logging
from typing import Optional, Dict, Any, List
from qdrant_client.models import Filter, FieldCondition, MatchValue
from .database import QDRANT_CLIENT, ensure_collections_exist

logger = logging.getLogger(__name__)

class UserAwareDatabase:
    """Database operations with user-based filtering."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = QDRANT_CLIENT
    
    def _get_user_filter(self) -> Filter:
        """Get filter for current user's data."""
        return Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=self.user_id))]  # type: ignore[arg-type]
        )
    
    def _get_user_filter_optional(self) -> Optional[Filter]:
        """Get filter for current user's data (optional, for backward compatibility)."""
        if self.user_id:
            return self._get_user_filter()
        return None
    
    def fetch_user_value_components(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch value components for the current user."""
        try:
            response = self.client.scroll(
                collection_name="value_components",
                scroll_filter=self._get_user_filter(),
                limit=1000
            )
            
            components = {}
            for point in response[0]:
                payload = point.payload
                main_category = payload.get("main_category", "Unknown")
                category = payload.get("category", "Unknown")
                
                if main_category not in components:
                    components[main_category] = {}
                if category not in components[main_category]:
                    components[main_category][category] = []
                
                components[main_category][category].append(payload)
            
            return components
            
        except Exception as e:
            logger.error(f"Error fetching user value components: {e}")
            return {}
    
    def save_user_value_component(self, component: Dict[str, Any]) -> bool:
        """Save a value component for the current user."""
        try:
            # Add user_id to component
            component["user_id"] = self.user_id
            
            # Use existing save logic from database.py
            from .database import save_value_component
            return save_value_component(component)
            
        except Exception as e:
            logger.error(f"Error saving user value component: {e}")
            return False
    
    def get_user_value_component(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific value component for the current user."""
        try:
            response = self.client.scroll(
                collection_name="value_components",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=self.user_id)),
                        FieldCondition(key="name", match=MatchValue(value=name))
                    ]
                ),
                limit=1
            )
            
            if response[0]:
                return response[0][0].payload
            return None
            
        except Exception as e:
            logger.error(f"Error getting user value component: {e}")
            return None
    
    def delete_user_value_component(self, name: str) -> bool:
        """Delete a value component for the current user."""
        try:
            response = self.client.scroll(
                collection_name="value_components",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=self.user_id)),
                        FieldCondition(key="name", match=MatchValue(value=name))
                    ]
                ),
                limit=1
            )
            
            if response[0]:
                point_id = response[0][0].id
                self.client.delete(
                    collection_name="value_components",
                    points_selector=[point_id]
                )
                logger.info(f"Deleted user value component: {name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user value component: {e}")
            return False
    
    def get_user_personas(self, query: Optional[dict] = None) -> List[Dict[str, Any]]:
        """Get personas for the current user."""
        try:
            # Build filter
            filter_conditions = [FieldCondition(key="user_id", match=MatchValue(value=self.user_id))]
            
            if query:
                for key, value in query.items():
                    if key != "user_id":  # Don't override user_id filter
                        filter_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            
            response = self.client.scroll(
                collection_name="personas",
                scroll_filter=Filter(must=filter_conditions),  # type: ignore[arg-type]
                limit=1000
            )
            
            return [point.payload for point in response[0]]
            
        except Exception as e:
            logger.error(f"Error getting user personas: {e}")
            return []
    
    def save_user_persona(self, persona: Dict[str, Any], source_website: Optional[str] = None) -> bool:
        """Save a persona for the current user."""
        try:
            # Add user_id to persona
            persona["user_id"] = self.user_id
            
            # Use existing save logic from database.py
            from .database import save_persona
            import asyncio
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(save_persona(persona, source_website))
                return result is not None
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Error saving user persona: {e}")
            return False
    
    def get_user_persona_by_id(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific persona for the current user."""
        try:
            response = self.client.scroll(
                collection_name="personas",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=self.user_id)),
                        FieldCondition(key="id", match=MatchValue(value=persona_id))
                    ]
                ),
                limit=1
            )
            
            if response[0]:
                return response[0][0].payload
            return None
            
        except Exception as e:
            logger.error(f"Error getting user persona: {e}")
            return None
    
    def delete_user_persona(self, persona_id: str) -> bool:
        """Delete a persona for the current user."""
        try:
            response = self.client.scroll(
                collection_name="personas",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=self.user_id)),
                        FieldCondition(key="id", match=MatchValue(value=persona_id))
                    ]
                ),
                limit=1
            )
            
            if response[0]:
                point_id = response[0][0].id
                self.client.delete(
                    collection_name="personas",
                    points_selector=[point_id]
                )
                logger.info(f"Deleted user persona: {persona_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user persona: {e}")
            return False
    
    def get_user_analyses(self) -> List[Dict[str, Any]]:
        """Get value rollercoaster analyses for the current user."""
        try:
            response = self.client.scroll(
                collection_name="value_waterfall_analyses",
                scroll_filter=self._get_user_filter(),
                limit=1000
            )
            
            return [point.payload for point in response[0]]
            
        except Exception as e:
            logger.error(f"Error getting user analyses: {e}")
            return []
    
    def save_user_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Save a value rollercoaster analysis for the current user."""
        try:
            # Add user_id to analysis
            analysis["user_id"] = self.user_id
            
            # Use existing save logic from database.py
            from .database import save_analysis
            return save_analysis(analysis)
            
        except Exception as e:
            logger.error(f"Error saving user analysis: {e}")
            return False
    
    def get_user_website_structures(self) -> List[Dict[str, Any]]:
        """Get website structures for the current user."""
        try:
            response = self.client.scroll(
                collection_name="website_structure",
                scroll_filter=self._get_user_filter(),
                limit=1000
            )
            
            return [point.payload for point in response[0]]
            
        except Exception as e:
            logger.error(f"Error getting user website structures: {e}")
            return []
    
    def save_user_website_structure(self, website: str, structure: Dict[str, Any]) -> bool:
        """Save a website structure for the current user."""
        try:
            # Add user_id to structure
            structure["user_id"] = self.user_id
            structure["website"] = website
            
            # Use existing save logic from database.py
            from .database import save_website_structure
            result = save_website_structure(website, structure)
            return result if result is not None else True
            
        except Exception as e:
            logger.error(f"Error saving user website structure: {e}")
            return False
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get statistics for the current user."""
        try:
            stats = {
                "value_components": 0,
                "personas": 0,
                "analyses": 0,
                "website_structures": 0
            }
            
            # Count value components
            vc_response = self.client.scroll(
                collection_name="value_components",
                scroll_filter=self._get_user_filter(),
                limit=1
            )
            stats["value_components"] = len(vc_response[0]) if vc_response[0] else 0
            
            # Count personas
            p_response = self.client.scroll(
                collection_name="personas",
                scroll_filter=self._get_user_filter(),
                limit=1
            )
            stats["personas"] = len(p_response[0]) if p_response[0] else 0
            
            # Count analyses
            a_response = self.client.scroll(
                collection_name="value_waterfall_analyses",
                scroll_filter=self._get_user_filter(),
                limit=1
            )
            stats["analyses"] = len(a_response[0]) if a_response[0] else 0
            
            # Count website structures
            ws_response = self.client.scroll(
                collection_name="website_structure",
                scroll_filter=self._get_user_filter(),
                limit=1
            )
            stats["website_structures"] = len(ws_response[0]) if ws_response[0] else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {"error": str(e)} 