"""
Simple Summary Panel
Replaces the existing summary panel with clean, simple display and soft motivation.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SimpleSummaryPanel:
    """Simple summary panel with soft motivation feedback"""
    
    def __init__(self):
        self.simple_quality_display = None
        self._load_components()
    
    def _load_components(self):
        """Load required components"""
        try:
            from app.components.simple_quality_display import simple_quality_display
            self.simple_quality_display = simple_quality_display
        except Exception as e:
            logger.warning(f"Could not load simple quality display: {e}")
    
    def render_simple_summary(
        self,
        main_category: str,
        subcategory: str,
        component_count: int,
        fields_with_benefits: int,
        db_lookup: Dict[str, Any],
        subcategories_details: Dict[str, Any]
    ) -> None:
        """
        Render simple, clean summary panel with soft motivation.
        
        Args:
            main_category: Main category (e.g., "Technical Value")
            subcategory: Subcategory (e.g., "Innovation")
            component_count: Total number of components
            fields_with_benefits: Number of fields with AI-generated benefits
            db_lookup: Database lookup dictionary
            subcategories_details: Component structure details
        """
        # Basic summary information (only once)
        st.markdown(f"### {subcategory}")
        st.markdown(f"**{component_count} components** • Focus on {subcategory.lower()} standards and practices")
        
        # Progress summary
        self._render_progress_summary(component_count, fields_with_benefits)
        
        # Soft motivation feedback for completed components
        if fields_with_benefits > 0 and self.simple_quality_display:
            self.simple_quality_display.render_simple_feedback(
                main_category, subcategory, component_count, 
                fields_with_benefits, db_lookup, subcategories_details
            )
        else:
            # Add spacing if no quality feedback
            st.markdown("<br>", unsafe_allow_html=True)
    
    def _render_progress_summary(self, component_count: int, fields_with_benefits: int) -> None:
        """Render progress summary with clean messaging"""
        if fields_with_benefits == 0:
            st.info(f"**0 fields with generated customer benefits**\n\nStart by entering text in the left column and clicking Save to generate AI insights.")
        elif fields_with_benefits == component_count:
            st.success(f"**{fields_with_benefits}/{component_count} fields completed!** 🎉\n\nAll components have AI-generated customer benefits.")
        else:
            remaining = component_count - fields_with_benefits
            st.warning(f"**{fields_with_benefits}/{component_count} fields completed**\n\n{remaining} more components need customer benefits.")

# Global instance
simple_summary_panel = SimpleSummaryPanel()
