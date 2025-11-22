"""
Activity Tracking System for User Management
Tracks user actions, sessions, and system usage for admin analytics
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams, Distance
import json

logger = logging.getLogger(__name__)

class ActivityTracker:
    """Tracks user activity and system usage for analytics."""
    
    def __init__(self, qdrant_client: QdrantClient):
        self.client = qdrant_client
        self.activities_collection = "user_activities"
        self.sessions_collection = "user_sessions"
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure activity tracking collections exist."""
        try:
            # Check if activities collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.activities_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.activities_collection,
                    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.activities_collection}")
            
            if self.sessions_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.sessions_collection,
                    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.sessions_collection}")
                
        except Exception as e:
            logger.error(f"Error ensuring activity collections: {e}")
    
    def log_activity(self, user_id: str, activity_type: str, details: Optional[Dict[str, Any]] = None):
        """Log a user activity."""
        try:
            activity_data = {
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "details": details or {}
            }
            
            self.client.upsert(
                collection_name=self.activities_collection,
                points=[PointStruct(
                    id=int(time.time() * 1000) % (2**63),  # Unique timestamp-based ID
                    vector=[0.0] * 128,  # Dummy vector
                    payload=activity_data
                )]
            )
            
            logger.debug(f"Logged activity: {user_id} - {activity_type}")
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def start_session(self, user_id: str, session_id: Optional[str] = None):
        """Start tracking a user session."""
        try:
            if not session_id:
                session_id = f"{user_id}_{int(time.time())}"
            
            session_data = {
                "user_id": user_id,
                "session_id": session_id,
                "start_time": time.time(),
                "start_datetime": datetime.now().isoformat(),
                "is_active": True,
                "pages_visited": [],
                "last_activity": time.time()
            }
            
            self.client.upsert(
                collection_name=self.sessions_collection,
                points=[PointStruct(
                    id=hash(session_id) % (2**63),
                    vector=[0.0] * 128,
                    payload=session_data
                )]
            )
            
            logger.info(f"Started session: {session_id} for user: {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return None
    
    def end_session(self, session_id: str):
        """End a user session."""
        try:
            # Get session data
            response = self.client.scroll(
                collection_name=self.sessions_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]  # type: ignore[arg-type]
                ),
                limit=1
            )
            
            if response[0]:
                session_data = response[0][0].payload
                if session_data:
                    session_data["end_time"] = time.time()
                    session_data["end_datetime"] = datetime.now().isoformat()
                    session_data["is_active"] = False
                    session_data["duration"] = session_data["end_time"] - session_data["start_time"]
                    
                    self.client.upsert(
                        collection_name=self.sessions_collection,
                        points=[PointStruct(
                            id=hash(session_id) % (2**63),
                            vector=[0.0] * 128,
                            payload=session_data
                        )]
                    )
                    
                    logger.info(f"Ended session: {session_id}, duration: {session_data['duration']:.2f}s")
                
        except Exception as e:
            logger.error(f"Error ending session: {e}")
    
    def update_session_activity(self, session_id: str, page_visited: Optional[str] = None):
        """Update session with current activity."""
        try:
            response = self.client.scroll(
                collection_name=self.sessions_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]  # type: ignore[arg-type]
                ),
                limit=1
            )
            
            if response[0]:
                session_data = response[0][0].payload
                if session_data:
                    session_data["last_activity"] = time.time()
                    
                    if page_visited:
                        if "pages_visited" not in session_data:
                            session_data["pages_visited"] = []
                        session_data["pages_visited"].append({
                            "page": page_visited,
                            "timestamp": time.time(),
                            "datetime": datetime.now().isoformat()
                        })
                    
                    self.client.upsert(
                        collection_name=self.sessions_collection,
                        points=[PointStruct(
                            id=hash(session_id) % (2**63),
                            vector=[0.0] * 128,
                            payload=session_data
                        )]
                    )
                
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    def get_recent_activities(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict]:
        """Get recent activities for the activity feed."""
        try:
            filter_conditions = []
            if user_id:
                filter_conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
            
            scroll_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            response = self.client.scroll(
                collection_name=self.activities_collection,
                scroll_filter=scroll_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            activities = []
            for point in response[0]:
                activity = point.payload
                if activity:
                    # Convert timestamp to readable format
                    if "timestamp" in activity:
                        activity["readable_time"] = datetime.fromtimestamp(activity["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    activities.append(activity)
            
            # Sort by timestamp (newest first)
            activities.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    def get_activity_heatmap_data(self, days: int = 7) -> Dict[str, Any]:
        """Get activity heatmap data for visualization."""
        try:
            # Get activities from the last N days
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            response = self.client.scroll(
                collection_name=self.activities_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="timestamp", match=MatchValue(value=cutoff_time, range={"gte": cutoff_time}))]  # type: ignore[arg-type]
                ),
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            # Initialize heatmap data structure
            heatmap_data = {}
            
            for point in response[0]:
                activity = point.payload
                if activity:
                    timestamp = activity.get("timestamp", 0)
                    dt = datetime.fromtimestamp(timestamp)
                    
                    # Create hour-based key (0-23)
                    hour_key = dt.hour
                    day_key = dt.strftime("%Y-%m-%d")
                    
                    if day_key not in heatmap_data:
                        heatmap_data[day_key] = {}
                    
                    if hour_key not in heatmap_data[day_key]:
                        heatmap_data[day_key][hour_key] = 0
                    
                    heatmap_data[day_key][hour_key] += 1
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Error getting heatmap data: {e}")
            return {}
    
    def get_session_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get session analytics data."""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            response = self.client.scroll(
                collection_name=self.sessions_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="start_time", match=MatchValue(value=cutoff_time, range={"gte": cutoff_time}))]  # type: ignore[arg-type]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            analytics = {
                "total_sessions": 0,
                "active_sessions": 0,
                "avg_session_duration": 0,
                "total_duration": 0,
                "page_visits": {},
                "user_sessions": {}
            }
            
            completed_sessions = []
            
            for point in response[0]:
                session = point.payload
                if session:
                    analytics["total_sessions"] += 1
                    
                    if session.get("is_active", False):
                        analytics["active_sessions"] += 1
                    
                    if "duration" in session:
                        completed_sessions.append(session["duration"])
                        analytics["total_duration"] += session["duration"]
                    
                    # Track page visits
                    pages = session.get("pages_visited", [])
                    for page_visit in pages:
                        page_name = page_visit.get("page", "Unknown")
                        if page_name not in analytics["page_visits"]:
                            analytics["page_visits"][page_name] = 0
                        analytics["page_visits"][page_name] += 1
                    
                    # Track user sessions
                    user_id = session.get("user_id", "Unknown")
                    if user_id not in analytics["user_sessions"]:
                        analytics["user_sessions"][user_id] = 0
                    analytics["user_sessions"][user_id] += 1
            
            if completed_sessions:
                analytics["avg_session_duration"] = sum(completed_sessions) / len(completed_sessions)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return {}
    
    def get_peak_usage_times(self, days: int = 7) -> Dict[str, Any]:
        """Get peak usage times analysis."""
        try:
            heatmap_data = self.get_activity_heatmap_data(days)
            
            # Aggregate by hour across all days
            hourly_activity = {}
            for day_data in heatmap_data.values():
                for hour, count in day_data.items():
                    if hour not in hourly_activity:
                        hourly_activity[hour] = 0
                    hourly_activity[hour] += count
            
            # Find peak hours
            if hourly_activity:
                max_activity = max(hourly_activity.values())
                peak_hours = [hour for hour, count in hourly_activity.items() if count == max_activity]
                
                # Sort by activity level
                sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
                
                return {
                    "hourly_activity": hourly_activity,
                    "peak_hours": peak_hours,
                    "peak_activity": max_activity,
                    "sorted_hours": sorted_hours,
                    "total_activities": sum(hourly_activity.values())
                }
            
            return {"hourly_activity": {}, "peak_hours": [], "peak_activity": 0, "sorted_hours": [], "total_activities": 0}
            
        except Exception as e:
            logger.error(f"Error getting peak usage times: {e}")
            return {}
    
    def cleanup_old_activities(self, days_to_keep: int = 30):
        """Clean up old activity data to save storage."""
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            # Get old activities
            response = self.client.scroll(
                collection_name=self.activities_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="timestamp", match=MatchValue(value=cutoff_time, range={"lt": cutoff_time}))]  # type: ignore[arg-type]
                ),
                limit=10000,
                with_payload=False,
                with_vectors=False
            )
            
            if response[0]:
                point_ids = [point.id for point in response[0]]
                self.client.delete(
                    collection_name=self.activities_collection,
                    points_selector=point_ids  # type: ignore[arg-type]
                )
                logger.info(f"Cleaned up {len(point_ids)} old activity records")
            
            # Clean up old sessions
            response = self.client.scroll(
                collection_name=self.sessions_collection,
                scroll_filter=Filter(
                    must=[FieldCondition(key="start_time", match=MatchValue(value=cutoff_time, range={"lt": cutoff_time}))]  # type: ignore[arg-type]
                ),
                limit=10000,
                with_payload=False,
                with_vectors=False
            )
            
            if response[0]:
                point_ids = [point.id for point in response[0]]
                self.client.delete(
                    collection_name=self.sessions_collection,
                    points_selector=point_ids  # type: ignore[arg-type]
                )
                logger.info(f"Cleaned up {len(point_ids)} old session records")
                
        except Exception as e:
            logger.error(f"Error cleaning up old activities: {e}") 