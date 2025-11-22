"""
Simple Quality Display Component
Shows soft motivation feedback without intimidating metrics.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Tuple, Union

logger = logging.getLogger(__name__)

class SimpleQualityDisplay:
    """Simple, user-friendly quality display component"""
    
    def __init__(self):
        self.soft_motivation = None
        self._load_soft_motivation()
    
    def _load_soft_motivation(self):
        """Load soft motivation system"""
        try:
            from app.components.soft_motivation_system import soft_motivation_system
            self.soft_motivation = soft_motivation_system
        except Exception as e:
            logger.warning(f"Could not load soft motivation system: {e}")
    
    def render_simple_feedback(
        self,
        main_category: str,
        subcategory: str,
        component_count: int,
        fields_with_benefits: int,
        db_lookup: Union[Dict[str, Any], Dict[Tuple[str, str, str], Any]],
        subcategories_details: Dict[str, Any]
    ) -> None:
        """
        Render simple, encouraging feedback for completed components.
        
        Args:
            main_category: Main category (e.g., "Technical Value")
            subcategory: Subcategory (e.g., "Innovation")
            component_count: Total number of components
            fields_with_benefits: Number of completed components
            db_lookup: Database lookup dictionary
            subcategories_details: Component structure details
        """
        if fields_with_benefits == 0:
            return  # No feedback needed if no components completed
        
        try:
            # Get completed components data
            completed_components = self._get_completed_components_data(
                main_category, subcategory, db_lookup, subcategories_details
            )
            
            if not completed_components:
                return
            
            # Generate soft feedback
            if self.soft_motivation:
                feedback_data = self.soft_motivation.generate_soft_feedback(
                    main_category, subcategory, completed_components
                )
                
                # Display simple feedback
                self._display_simple_feedback(feedback_data, subcategory)
            else:
                # Fallback simple feedback
                self._display_fallback_feedback(subcategory, fields_with_benefits, component_count)
                
        except Exception as e:
            logger.error(f"Error rendering simple feedback: {e}")
            # Show fallback feedback
            self._display_fallback_feedback(subcategory, fields_with_benefits, component_count)
    
    def _get_completed_components_data(
        self, 
        main_category: str, 
        subcategory: str, 
        db_lookup: Union[Dict[str, Any], Dict[Tuple[str, str, str], Any]], 
        subcategories_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get data for completed components"""
        completed_components = []
        
        for comp in subcategories_details[subcategory]["items"]:
            comp_name = comp["name"]
            comp_name_lc = comp_name.lower()
            
            # Check if this component has AI-generated content
            db_key = (main_category.lower(), subcategory.lower(), comp_name_lc)
            # Handle both tuple key and string key dictionaries
            if isinstance(db_lookup, dict):
                db_data = db_lookup.get(db_key, {})  # type: ignore[arg-type]
            else:
                db_data = {}
            if not isinstance(db_data, dict):
                db_data = {}
            db_ai_val = db_data.get("ai_processed_value", "")
            
            if db_ai_val and db_ai_val.strip():
                completed_components.append({
                    "name": comp_name,
                    "original_value": db_data.get("original_value", ""),
                    "ai_guidance": db_data.get("ai_guidance", ""),  # AI guidance data
                    "ai_processed_value": db_ai_val,
                    "user_rating": db_data.get("user_rating", 1)
                })
        
        return completed_components
    
    def _display_simple_feedback(self, feedback_data: Dict[str, Any], subcategory: str) -> None:
        """Display simple, encouraging feedback"""
        feedback = feedback_data.get("feedback", "")
        motivation_level = feedback_data.get("motivation_level", "building")
        completed_components = feedback_data.get("completed_components", 0)
        total_components = feedback_data.get("total_components", 0)
        
        # Create a simple, clean display
        with st.container():
            # Simple progress indicator
            progress_text = f"**{completed_components}/{total_components} components completed**"
            
            # Choose color based on motivation level
            if motivation_level == "excellent":
                st.success(progress_text)
            elif motivation_level == "great":
                st.success(progress_text)
            elif motivation_level == "good":
                st.info(progress_text)
            else:
                st.warning(progress_text)
            
            # Simple feedback message
            if feedback:
                # Choose appropriate container based on motivation level
                if motivation_level == "excellent":
                    st.success(feedback)
                elif motivation_level == "great":
                    st.success(feedback)
                elif motivation_level == "good":
                    st.info(feedback)
                else:
                    st.info(feedback)
            
            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
    
    def _display_fallback_feedback(self, subcategory: str, fields_with_benefits: int, component_count: int) -> None:
        """Display fallback feedback if soft motivation system is not available"""
        progress_text = f"**{fields_with_benefits}/{component_count} components completed**"
        
        if fields_with_benefits == component_count:
            st.success(progress_text)
            st.success(f"Great work on {subcategory}! All components completed! 🎉")
        elif fields_with_benefits > 0:
            st.info(progress_text)
            st.info(f"Keep going with {subcategory}! You're making good progress! 💪")
        else:
            st.warning(progress_text)
            st.warning(f"Start working on your {subcategory} components! 🚀")
        
        st.markdown("<br>", unsafe_allow_html=True)

# Global instance
simple_quality_display = SimpleQualityDisplay()
