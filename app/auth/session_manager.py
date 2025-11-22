"""
Session Management System
Handles user sessions in Streamlit application.
"""

import streamlit as st
import logging
import time
import hashlib
from typing import Dict, Any, Optional
from .user_management import UserManager

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions in Streamlit."""
    
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
        self.session_timeout = 30 * 24 * 60 * 60  # 30 days for "remember me" in seconds
        self.session_collection = "user_sessions"
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently logged-in user."""
        if "user_id" not in st.session_state:
            return None
        
        user_id = st.session_state.user_id
        return self.user_manager.get_user_by_id(user_id)
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        # Check if we have session data
        if "user_id" not in st.session_state or st.session_state.user_id is None:
            return False
        
        # For now, be more lenient with session timeouts to prevent logout on refresh
        # In a production system, you'd want proper session management
        return True
    
    def login_user(self, username: str, password: str) -> bool:
        """Log in a user with username and password."""
        try:
            # FIX: Clear any existing session state before login to prevent data leakage
            self._clear_user_session_state()
            
            user_data = self.user_manager.authenticate_user(username, password)
            if user_data:
                # Store user data in session
                st.session_state.user_id = user_data.get("user_id")
                st.session_state.username = user_data.get("username")
                st.session_state.display_name = user_data.get("display_name", username)
                st.session_state.is_authenticated = True
                st.session_state.session_start_time = time.time()
                
                # Generate and store session token
                user_id = user_data.get("user_id")
                if not user_id:
                    logger.error("User data missing user_id")
                    return False
                
                session_token = self._generate_session_token(user_id, username)
                if self._store_session_in_database(user_id, username, session_token):
                    st.session_state.session_token = session_token
                    
                    # Generate public session ID for URL display
                    public_id = self._generate_public_session_id(session_token)
                    
                    # Store public session ID in URL for persistence across page refresh
                    st.query_params["value"] = public_id
                    
                    logger.info(f"User logged in: {username} (public_id: {public_id})")
                    return True
                else:
                    logger.error(f"Failed to store session in database for user: {username}")
                    return False
            else:
                logger.warning(f"Failed login attempt for: {username}")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def logout_user(self):
        """Log out the current user."""
        if "user_id" in st.session_state:
            username = st.session_state.get("username", "unknown")
            session_token = st.session_state.get("session_token")
            logger.info(f"User logged out: {username}")
            
            # Delete session from database
            if session_token:
                self._delete_session_from_database(session_token)
        
        # Clear session state - including persona-related data
        keys_to_clear = [
            # Authentication keys
            "user_id", "username", "display_name", "is_authenticated", 
            "session_start_time", "session_token",
            
            # Persona-related keys (FIX: Clear to prevent data leakage)
            "persona", "persona_saved", "generator_version", "persona_in_progress",
            "generation_step", "generated_persona", "generation_success_time",
            "selected_persona_id", "persona_to_delete_id", "clear_input_on_next_run",
            "website_input", "status_checked", "value_components_toast_shown",
            
            # Progress tracking keys
            "persona_progress", "global_processing",
            
            # UI state keys that might contain user-specific data
            "main_tab_selectbox", "main_tab_radio", "selected_main_category"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear session ID from URL
        if "value" in st.query_params:
            del st.query_params["value"]
        
        # Session cleared
        logger.info(f"Session state cleared for user: {username}")
    
    def require_auth(self) -> str:
        """Require authentication and return current user_id."""
        if not self.is_authenticated():
            st.error("Please log in to access this feature.")
            st.stop()
        
        return st.session_state.user_id
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID without requiring authentication."""
        return st.session_state.get("user_id")
    
    def get_username(self) -> Optional[str]:
        """Get current username."""
        return st.session_state.get("username")
    
    def get_display_name(self) -> Optional[str]:
        """Get current user's display name."""
        return st.session_state.get("display_name")
    
    def update_session_user(self, user_data: Dict[str, Any]):
        """Update session with new user data."""
        st.session_state.username = user_data.get("username")
        st.session_state.display_name = user_data.get("display_name")
    
    def create_user_and_login(self, username: str, password: str, display_name: Optional[str] = None) -> bool:
        """Create a new user and log them in."""
        try:
            user_data = self.user_manager.create_user(username, password, display_name)
            return self.login_user(username, password)
        except Exception as e:
            logger.error(f"Error creating user and logging in: {e}")
            return False
    
    def _generate_session_token(self, user_id: str, username: str) -> str:
        """Generate a session token for persistence."""
        timestamp = str(int(time.time()))
        token_data = f"{user_id}:{username}:{timestamp}"
        return hashlib.sha256(token_data.encode()).hexdigest()
    
    def _generate_public_session_id(self, session_token: str) -> str:
        """Generate a funky B2B action-rollercoaster-color-meaningful session ID for URL display."""
        # Create a business-related identifier from the session token
        # Use MD5 hash to get consistent mapping
        hash_value = hashlib.md5(session_token.encode()).hexdigest()
        
        # Business action verbs for B2B applications (20 words)
        action_words = [
            "analyze", "evaluate", "optimize", "transform", "enhance",
            "accelerate", "boost", "launch", "scale", "drive",
            "unlock", "maximize", "leverage", "harness", "amplify",
            "ignite", "spark", "catalyze", "propel", "elevate"
        ]
        
        # Business process words for B2B applications (20 words)
        process_words = [
            "negotiate", "strategize", "implement", "execute", "deliver",
            "manage", "coordinate", "facilitate", "orchestrate", "streamline",
            "automate", "integrate", "consolidate", "standardize", "innovate",
            "evolve", "adapt", "plan", "design", "architect"
        ]
        
        # Analytics & intelligence words for B2B applications (20 words)
        analytics_words = [
            "measure", "track", "monitor", "assess", "benchmark",
            "compare", "contrast", "validate", "forecast", "predict",
            "project", "estimate", "calculate", "quantify", "qualify",
            "verify", "confirm", "certify", "analyze", "evaluate"
        ]
        
        # Business words for B2B applications (20 core words)
        business_words = [
            "partner", "invoice", "client", "vendor", "contract",
            "quote", "proposal", "account", "project", "service",
            "solution", "strategy", "market", "value", "business",
            "revenue", "profit", "growth", "network", "success"
        ]
        
        # Financial & value words for B2B applications (20 words)
        financial_words = [
            "invest", "return", "profit", "revenue", "margin",
            "cost", "budget", "expense", "savings", "efficiency",
            "value", "worth", "benefit", "advantage", "gain",
            "loss", "risk", "reward", "opportunity", "potential"
        ]
        
        # Strategic & planning words for B2B applications (20 words)
        strategic_words = [
            "plan", "design", "architect", "blueprint", "roadmap",
            "vision", "mission", "goal", "objective", "target",
            "strategy", "tactic", "approach", "method", "framework",
            "initiative", "program", "campaign", "project", "venture"
        ]
        
        # Rollercoaster/entertainment words for funky B2B theme (20 words)
        rollercoaster_words = [
            "loop", "drop", "spin", "ride", "twist",
            "jump", "dive", "soar", "swoop", "glide",
            "swing", "bounce", "float", "drift", "rush",
            "blast", "boost", "launch", "orbit", "flight"
        ]
        
        # Space mission words for alternative B2B theme (20 words)
        space_words = [
            "mission", "voyage", "expedition", "journey", "quest",
            "orbit", "launch", "flight", "cruise", "drift",
            "explore", "discover", "navigate", "pilot", "steer",
            "traverse", "cross", "reach", "arrive", "land"
        ]
        
        # Color words for visual appeal (20 colors)
        color_words = [
            "red", "blue", "gold", "purple", "silver",
            "emerald", "ruby", "sapphire", "amber", "crystal",
            "crimson", "azure", "bronze", "violet", "platinum",
            "jade", "coral", "indigo", "copper", "diamond"
        ]
        
        # Meaningful number contexts (20 contexts)
        number_contexts = [
            "times", "miles", "degrees", "feet", "knots",
            "rounds", "levels", "steps", "cycles", "waves",
            "peaks", "valleys", "zones", "spheres", "dimensions",
            "chapters", "verses", "beats", "pulses", "sparks"
        ]
        
        # Use hash to select theme (rollercoaster vs space vs B2B categories)
        theme_selector = int(hash_value[:2], 16) % 6  # 0-1 = rollercoaster, 2-3 = space, 4 = process, 5 = analytics
        
        # Use hash to select all components
        action_index = int(hash_value[2:4], 16) % len(action_words)
        business_index = int(hash_value[4:6], 16) % len(business_words)
        color_index = int(hash_value[6:8], 16) % len(color_words)
        context_index = int(hash_value[8:10], 16) % len(number_contexts)
        
        action_word = action_words[action_index]
        business_word = business_words[business_index]
        color_word = color_words[color_index]
        context_word = number_contexts[context_index]
        
        # Select theme-based word
        if theme_selector in [0, 1]:
            # Rollercoaster theme (33%)
            theme_index = int(hash_value[10:12], 16) % len(rollercoaster_words)
            theme_word = rollercoaster_words[theme_index]
        elif theme_selector in [2, 3]:
            # Space theme (33%)
            theme_index = int(hash_value[10:12], 16) % len(space_words)
            theme_word = space_words[theme_index]
        elif theme_selector == 4:
            # Business process theme (17%)
            theme_index = int(hash_value[10:12], 16) % len(process_words)
            theme_word = process_words[theme_index]
        else:
            # Analytics theme (17%)
            theme_index = int(hash_value[10:12], 16) % len(analytics_words)
            theme_word = analytics_words[theme_index]
        
        # Generate meaningful number (1-99 for better readability)
        number = int(hash_value[12:14], 16) % 99 + 1
        
        return f"{action_word}-{business_word}-{theme_word}-{color_word}-{number}-{context_word}"
    
    def _get_session_token_by_public_id(self, public_id: str) -> Optional[str]:
        """Get the actual session token from a public session ID."""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Search for session with matching public_id
            session_filter = Filter(
                must=[
                    FieldCondition(key="public_id", match=MatchValue(value=public_id)),
                    FieldCondition(key="is_active", match=MatchValue(value=True))
                ]
            )
            
            results = QDRANT_CLIENT.scroll(
                collection_name=self.session_collection,
                scroll_filter=session_filter,
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if results[0]:
                return results[0][0].payload.get("session_token")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session token by public ID: {e}")
            return None
    
    def _validate_session_token(self, token: str, user_id: str, username: str) -> bool:
        """Validate a session token."""
        if not token or not user_id or not username:
            return False
        
        # For now, we'll use a simple validation
        # In a production system, you'd want to store tokens in the database
        return True
    
    def _store_session_in_database(self, user_id: str, username: str, session_token: str) -> bool:
        """Store session data in database for persistence across page refresh."""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import PointStruct
            
            # Generate public session ID for URL display
            public_id = self._generate_public_session_id(session_token)
            
            # Create session data
            session_data = {
                "user_id": user_id,
                "username": username,
                "session_token": session_token,
                "public_id": public_id,  # Add public ID for URL lookup
                "created_at": time.time(),
                "last_accessed": time.time(),
                "is_active": True
            }
            
            # Store in database
            point = PointStruct(
                id=abs(hash(session_token)) % (2**63),  # Use positive hash as point ID
                payload=session_data,
                vector=[0.0] * 128  # Dummy vector for Qdrant
            )
            
            QDRANT_CLIENT.upsert(
                collection_name=self.session_collection,
                points=[point]
            )
            
            logger.info(f"Session stored in database for user: {username} (public_id: {public_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing session in database: {e}")
            return False
    
    def _get_session_from_database(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from database."""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Create filter to find session by token
            session_filter = Filter(
                must=[
                    FieldCondition(key="session_token", match=MatchValue(value=session_token)),
                    FieldCondition(key="is_active", match=MatchValue(value=True))
                ]
            )
            
            # Search for session
            results = QDRANT_CLIENT.scroll(
                collection_name=self.session_collection,
                scroll_filter=session_filter,
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if results[0]:
                session_data = results[0][0].payload
                
                # Check if session is expired
                created_at = session_data.get("created_at", 0)
                if time.time() - created_at > self.session_timeout:
                    logger.info(f"Session expired for user: {session_data.get('username', 'unknown')}")
                    self._delete_session_from_database(session_token)
                    return None
                
                # Update last accessed time
                self._update_session_access_time(session_token)
                
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session from database: {e}")
            return None
    
    def _update_session_access_time(self, session_token: str) -> bool:
        """Update the last accessed time for a session."""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Find session
            session_filter = Filter(
                must=[FieldCondition(key="session_token", match=MatchValue(value=session_token))]  # type: ignore[arg-type]
            )
            
            results = QDRANT_CLIENT.scroll(
                collection_name=self.session_collection,
                scroll_filter=session_filter,
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if results[0]:
                session_data = results[0][0].payload
                session_data["last_accessed"] = time.time()
                
                # Update session
                from qdrant_client.models import PointStruct
                point = PointStruct(
                    id=results[0][0].id,
                    payload=session_data,
                    vector=[0.0] * 128
                )
                
                QDRANT_CLIENT.upsert(
                    collection_name=self.session_collection,
                    points=[point]
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating session access time: {e}")
            return False
    
    def _delete_session_from_database(self, session_token: str) -> bool:
        """Delete session from database."""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Find session
            session_filter = Filter(
                must=[FieldCondition(key="session_token", match=MatchValue(value=session_token))]  # type: ignore[arg-type]
            )
            
            results = QDRANT_CLIENT.scroll(
                collection_name=self.session_collection,
                scroll_filter=session_filter,
                limit=1,
                with_payload=False,
                with_vectors=False
            )
            
            if results[0]:
                # Delete session
                QDRANT_CLIENT.delete(
                    collection_name=self.session_collection,
                    points_selector=[results[0][0].id]
                )
                
                logger.info(f"Session deleted from database: {session_token}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting session from database: {e}")
            return False
    
    def _ensure_session_collection_exists(self):
        """Ensure the session collection exists in the database."""
        try:
            from app.database import QDRANT_CLIENT
            
            # Check if collection exists
            collections = QDRANT_CLIENT.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.session_collection not in collection_names:
                # Create collection
                from qdrant_client.models import Distance, VectorParams
                
                QDRANT_CLIENT.create_collection(
                    collection_name=self.session_collection,
                    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                )
                
                logger.info(f"Created session collection: {self.session_collection}")
            
        except Exception as e:
            logger.error(f"Error ensuring session collection exists: {e}")
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from the database."""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import Filter, FieldCondition, Range
            
            # Find expired sessions
            current_time = time.time()
            expired_filter = Filter(
                must=[
                    FieldCondition(
                        key="created_at",
                        range=Range(
                            lt=current_time - self.session_timeout
                        )
                    )
                ]
            )
            
            # Get expired sessions
            results = QDRANT_CLIENT.scroll(
                collection_name=self.session_collection,
                scroll_filter=expired_filter,
                limit=1000,
                with_payload=False,
                with_vectors=False
            )
            
            if results[0]:
                # Delete expired sessions
                expired_ids = [point.id for point in results[0]]
                QDRANT_CLIENT.delete(
                    collection_name=self.session_collection,
                    points_selector=expired_ids
                )
                
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
                return len(expired_ids)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def restore_session(self) -> bool:
        """Try to restore session from persistent storage."""
        try:
            # Method 1: Check if we have session data in session state (for same-session navigation)
            if ("user_id" in st.session_state and 
                "username" in st.session_state and 
                "session_token" in st.session_state):
                
                user_id = st.session_state.user_id
                username = st.session_state.username
                session_token = st.session_state.session_token
                
                # Validate the session token
                if self._validate_session_token(session_token, user_id, username):
                    # Verify user still exists in database
                    user = self.user_manager.get_user_by_id(user_id)
                    if user and user.get("is_active", True):
                        # Restore session data
                        st.session_state.display_name = user.get("display_name", username)
                        st.session_state.is_authenticated = True
                        
                        # Update session start time if not present
                        if "session_start_time" not in st.session_state:
                            st.session_state.session_start_time = time.time()
                        
                        # Restore user's active background tasks
                        self._restore_user_background_tasks(user_id)
                        
                        # Clean up old tasks periodically (every 10th login)
                        if not hasattr(st.session_state, 'cleanup_counter'):
                            st.session_state.cleanup_counter = 0
                        st.session_state.cleanup_counter += 1
                        
                        if st.session_state.cleanup_counter % 10 == 0:
                            self._cleanup_old_tasks()
                        
                        logger.info(f"Session restored from session state for user: {username}")
                        return True
                    else:
                        logger.warning(f"User no longer exists or is inactive: {username}")
                        self.logout_user()
                        return False
                else:
                    logger.warning(f"Invalid session token for user: {username}")
                    self.logout_user()
                    return False
            
            # Method 2: Try to restore from database using public session ID from URL
            # This is for page refresh scenarios
            session_token = self._get_session_token_from_storage()
            if session_token:
                session_data = self._get_session_from_database(session_token)
                if session_data:
                    user_id = session_data.get("user_id")
                    username = session_data.get("username")
                    
                    # Verify user still exists in database
                    if not user_id:
                        logger.warning("Session data missing user_id")
                        self._delete_session_from_database(session_token)
                        return False
                    
                    user = self.user_manager.get_user_by_id(user_id)
                    if user and user.get("is_active", True):
                        # Restore session data
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.display_name = user.get("display_name", username)
                        st.session_state.is_authenticated = True
                        st.session_state.session_start_time = time.time()
                        st.session_state.session_token = session_token
                        
                        # Ensure public session ID is in URL
                        public_id = session_data.get("public_id")
                        if public_id and st.query_params.get("value") != public_id:
                            st.query_params["value"] = public_id
                        
                        logger.info(f"Session restored from database for user: {username}")
                        return True
                    else:
                        logger.warning(f"User no longer exists or is inactive: {username}")
                        self._delete_session_from_database(session_token)
                        return False
                else:
                    logger.warning(f"Session not found in database")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error restoring session: {e}")
            return False
    
    def _restore_user_background_tasks(self, user_id: str):
        """Restore user's active background tasks after login/session restore."""
        try:
            from app.database import get_user_background_tasks
            import asyncio
            
            # Get user's active tasks
            tasks = asyncio.run(get_user_background_tasks(user_id))
            
            # Find the most recent running task
            running_tasks = [task for task in tasks if task.get("status") == "running"]
            if running_tasks:
                # Sort by creation time, get the most recent
                latest_task = max(running_tasks, key=lambda x: x.get("created_at", ""))
                task_id = latest_task.get("task_id")
                
                if task_id:
                    # Restore the task ID to session state
                    st.session_state.background_persona_task_id = task_id
                    logger.info(f"Restored background task {task_id} for user {user_id}")
                    
                    # Clear any failed task flags
                    if "failed_task_shown" in st.session_state:
                        del st.session_state.failed_task_shown
            else:
                # Check for recently completed tasks (within last 5 minutes)
                completed_tasks = [task for task in tasks if task.get("status") == "completed"]
                if completed_tasks:
                    # Find the most recent completed task
                    latest_completed = max(completed_tasks, key=lambda x: x.get("updated_at", ""))
                    
                    # Check if it was completed recently (within last 5 minutes)
                    from datetime import datetime, timedelta
                    try:
                        updated_time = datetime.fromisoformat(latest_completed.get("updated_at", "").replace('Z', '+00:00'))
                        if datetime.now() - updated_time < timedelta(minutes=5):
                            # Show notification for recently completed task
                            task_id = latest_completed.get("task_id")
                            if task_id:
                                st.session_state.background_persona_task_id = task_id
                                st.session_state.recently_completed_task = True
                                logger.info(f"Found recently completed task {task_id} for user {user_id}")
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Error restoring background tasks for user {user_id}: {e}")
    
    def _cleanup_old_tasks(self):
        """Clean up old background tasks to prevent database bloat."""
        try:
            from app.database import cleanup_completed_tasks
            import asyncio
            
            # Run cleanup in background
            asyncio.create_task(cleanup_completed_tasks())
            logger.info("Started cleanup of old background tasks")
            
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")
    
    def _get_session_token_from_storage(self) -> Optional[str]:
        """Get session token from various storage mechanisms."""
        try:
            # Method 1: Try to get public session ID from URL parameters
            query_params = st.query_params
            public_id = query_params.get("value", None)
            if public_id:
                # Convert public ID to actual session token
                session_token = self._get_session_token_by_public_id(public_id)
                if session_token:
                    return session_token
            
            # Method 2: Try to get from session state (fallback)
            return st.session_state.get("session_token", None)
            
        except Exception as e:
            logger.error(f"Error getting session token from storage: {e}")
            return None
    
    def _clear_user_session_state(self):
        """Clear all user-specific session state to prevent data leakage."""
        keys_to_clear = [
            # Authentication keys
            "user_id", "username", "display_name", "is_authenticated", 
            "session_start_time", "session_token",
            
            # Persona-related keys (FIX: Clear to prevent data leakage)
            "persona", "persona_saved", "generator_version", "persona_in_progress",
            "generation_step", "generated_persona", "generation_success_time",
            "selected_persona_id", "persona_to_delete_id", "clear_input_on_next_run",
            "website_input", "status_checked", "value_components_toast_shown",
            
            # Progress tracking keys
            "persona_progress", "global_processing",
            
            # UI state keys that might contain user-specific data
            "main_tab_selectbox", "main_tab_radio", "selected_main_category"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear session ID from URL
        if "value" in st.query_params:
            del st.query_params["value"]
        
        logger.info("User-specific session state cleared.")
    

    
 