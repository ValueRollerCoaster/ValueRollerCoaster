"""
Enhanced Summary Panel with Quality Assessment
Extends the existing summary panel with quality assessment functionality.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from app.components.quality_assessment_panel import quality_assessment_panel

logger = logging.getLogger(__name__)

class EnhancedSummaryPanel:
    """Enhanced summary panel with quality assessment capabilities"""
    
    def __init__(self):
        self.quality_panel = quality_assessment_panel
    
    def render_enhanced_summary(
        self,
        main_category: str,
        subcategory: str,
        component_count: int,
        fields_with_benefits: int,
        db_lookup: Dict[str, Any],
        subcategories_details: Dict[str, Any]
    ) -> None:
        """
        Render enhanced summary panel with quality assessment.
        
        Args:
            main_category: Main category (e.g., "Technical Value")
            subcategory: Subcategory (e.g., "Quality")
            component_count: Total number of components
            fields_with_benefits: Number of fields with AI-generated benefits
            db_lookup: Database lookup dictionary
            subcategories_details: Component structure details
        """
        # Basic summary information
        st.markdown(f"### {subcategory}")
        st.markdown(f"**{component_count} components** • Focus on {subcategory.lower()} standards and practices")
        
        # Progress summary with enhanced messaging
        self._render_progress_summary(component_count, fields_with_benefits)
        
        # Quality assessment for completed components
        if fields_with_benefits > 0:
            self._render_quality_assessment(main_category, subcategory, db_lookup, subcategories_details)
        
        # Add some spacing
        st.markdown("<br><br>", unsafe_allow_html=True)
    
    def _render_progress_summary(self, component_count: int, fields_with_benefits: int) -> None:
        """Render progress summary with enhanced messaging"""
        if fields_with_benefits == 0:
            st.info(f"**0 fields with generated customer benefits**\n\nStart by entering text in the left column and clicking Save to generate AI insights.")
        elif fields_with_benefits == component_count:
            st.success(f"**{fields_with_benefits}/{component_count} fields completed!** 🎉\n\nAll components have AI-generated customer benefits.")
        else:
            remaining = component_count - fields_with_benefits
            st.warning(f"**{fields_with_benefits}/{component_count} fields completed**\n\n{remaining} more components need customer benefits.")
    
    def _render_quality_assessment(
        self, 
        main_category: str, 
        subcategory: str, 
        db_lookup: Dict[str, Any], 
        subcategories_details: Dict[str, Any]
    ) -> None:
        """Render quality assessment for completed components"""
        try:
            # Get completed components data
            completed_components = self._get_completed_components_data(
                main_category, subcategory, db_lookup, subcategories_details
            )
            
            if not completed_components:
                return
            
            # Render compact quality assessment
            assessment_data = self.quality_panel.render_compact_assessment(
                main_category, subcategory, completed_components
            )
            
            if assessment_data:
                self._render_compact_quality_display(assessment_data, subcategory)
                
        except Exception as e:
            logger.error(f"Error rendering quality assessment: {e}")
    
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
                    "ai_processed_value": db_ai_val,
                    "user_rating": db_data.get("user_rating", 1),
                    "chain_of_thought": db_data.get("chain_of_thought", "")
                })
        
        return completed_components
    
    def _render_compact_quality_display(self, assessment_data: Dict[str, Any], subcategory: str) -> None:
        """Render compact quality display in the summary panel"""
        overall_score = assessment_data.get("overall_score", 0)
        avg_rating = assessment_data.get("average_rating", 0)
        quality_rate = assessment_data.get("quality_rate", 0)
        
        # Determine quality level and color
        if overall_score >= 90:
            quality_level = "Excellent"
            color = "🟢"
            emoji = "🎉"
        elif overall_score >= 80:
            quality_level = "Very Good"
            color = "🟢"
            emoji = "👍"
        elif overall_score >= 70:
            quality_level = "Good"
            color = "🟡"
            emoji = "✅"
        elif overall_score >= 60:
            quality_level = "Developing"
            color = "🟡"
            emoji = "📈"
        else:
            quality_level = "Building"
            color = "🔴"
            emoji = "💪"
        
        # Create expandable quality section
        with st.expander(f"{emoji} {subcategory} Quality Assessment", expanded=False):
            # Quality score
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric(
                    label="Quality Score",
                    value=f"{overall_score}/100",
                    delta=f"{color} {quality_level}"
                )
            
            with col2:
                st.markdown(f"**{quality_level} quality** based on your company profile alignment")
            
            # Additional metrics
            col3, col4 = st.columns(2)
            
            with col3:
                st.metric(
                    label="Avg Rating",
                    value=f"{avg_rating}/5",
                    help="Average user rating"
                )
            
            with col4:
                st.metric(
                    label="Quality Rate",
                    value=f"{quality_rate}%",
                    help="Components rated 4+ stars"
                )
            
            # Motivational message
            self._render_motivational_message(overall_score, quality_level, subcategory)
    
    def _render_motivational_message(self, score: int, quality_level: str, subcategory: str) -> None:
        """Render motivational message based on quality score"""
        if score >= 90:
            message = f"🎉 Outstanding! Your {subcategory} components are excellent and strongly align with your company profile. You're ready to impress customers!"
        elif score >= 80:
            message = f"👍 Great work! Your {subcategory} components are very good and show strong company alignment. Keep up the excellent work!"
        elif score >= 70:
            message = f"✅ Good progress! Your {subcategory} components are solid. A few tweaks could make them even better."
        elif score >= 60:
            message = f"📈 You're on the right track! Your {subcategory} components are developing well. Focus on the feedback to improve quality."
        else:
            message = f"💪 You're building the foundation! Your {subcategory} components are a good start. Use the assessment feedback to enhance them further."
        
        st.info(message)
    
    def render_detailed_quality_assessment(
        self,
        main_category: str,
        subcategory: str,
        db_lookup: Union[Dict[str, Any], Dict[Tuple[str, str, str], Any]],
        subcategories_details: Dict[str, Any]
    ) -> None:
        """Render detailed quality assessment in a separate section"""
        try:
            # Get completed components data
            completed_components = self._get_completed_components_data(
                main_category, subcategory, db_lookup, subcategories_details
            )
            
            if not completed_components:
                st.info(f"No completed {subcategory} components to assess.")
                return
            
            # Render full quality assessment (async call - use asyncio.run)
            import asyncio
            try:
                # Check if we're in an async context
                loop = asyncio.get_running_loop()
                # We're in async context - this shouldn't happen in a sync method
                # Log warning and skip
                logger.warning("render_detailed_quality_assessment called from async context - skipping async render")
            except RuntimeError:
                # No running loop - safe to use asyncio.run
                asyncio.run(self.quality_panel.render_assessment_panel(
                    main_category, subcategory, completed_components
                ))
            
        except Exception as e:
            logger.error(f"Error rendering detailed quality assessment: {e}")
            st.error("Unable to load quality assessment. Please try again.")

# Global instance
enhanced_summary_panel = EnhancedSummaryPanel()
