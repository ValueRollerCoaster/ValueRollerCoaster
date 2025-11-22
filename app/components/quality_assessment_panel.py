"""
Quality Assessment Panel
UI component for displaying component quality assessment and motivational feedback.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from app.utils.component_quality_assessor import component_quality_assessor

logger = logging.getLogger(__name__)

class QualityAssessmentPanel:
    """UI panel for displaying quality assessment results"""
    
    def __init__(self):
        self.assessor = component_quality_assessor
    
    async def render_assessment_panel(
        self, 
        main_category: str, 
        subcategory: str, 
        completed_components: List[Dict[str, Any]]
    ) -> None:
        """
        Render the quality assessment panel for a subcategory.
        
        Args:
            main_category: Main category (e.g., "Technical Value")
            subcategory: Subcategory (e.g., "Quality")
            completed_components: List of completed components
        """
        if not completed_components:
            self._render_empty_state(subcategory)
            return
        
        # Show loading spinner while assessing
        with st.spinner(f"Assessing {subcategory} quality..."):
            assessment = await self.assessor.assess_subcategory_quality(
                main_category, subcategory, completed_components
            )
        
        # Render assessment results
        self._render_assessment_results(assessment)
    
    def _render_empty_state(self, subcategory: str) -> None:
        """Render empty state when no components are completed"""
        st.info(f"Complete some {subcategory} components to get a quality assessment!")
    
    def _render_assessment_results(self, assessment: Dict[str, Any]) -> None:
        """Render the assessment results"""
        # Overall score and motivation
        self._render_score_and_motivation(assessment)
        
        # Quality metrics
        self._render_quality_metrics(assessment.get("metrics", {}))
        
        # Strengths and improvements
        self._render_feedback_sections(assessment)
        
        # Recommendations
        self._render_recommendations(assessment.get("recommendations", []))
    
    def _render_score_and_motivation(self, assessment: Dict[str, Any]) -> None:
        """Render overall score and motivational feedback"""
        overall_score = assessment.get("overall_score", 0)
        motivation = assessment.get("motivation", "")
        subcategory = assessment.get("subcategory", "components")
        
        # Score display with color coding
        if overall_score >= 90:
            score_color = "🟢"
            score_emoji = "🎉"
        elif overall_score >= 80:
            score_color = "🟢"
            score_emoji = "👍"
        elif overall_score >= 70:
            score_color = "🟡"
            score_emoji = "✅"
        elif overall_score >= 60:
            score_color = "🟡"
            score_emoji = "📈"
        else:
            score_color = "🔴"
            score_emoji = "💪"
        
        # Score section
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.metric(
                label=f"{subcategory} Quality Score",
                value=f"{overall_score}/100",
                delta=f"{score_emoji} {score_color}"
            )
        
        with col2:
            st.markdown(f"**{motivation}**")
    
    def _render_quality_metrics(self, metrics: Dict[str, Any]) -> None:
        """Render quality metrics"""
        if not metrics:
            return
        
        st.markdown("### 📊 Quality Metrics")
        
        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Average Rating",
                value=f"{metrics.get('average_rating', 0)}/5",
                help="Average user rating across all components"
            )
        
        with col2:
            st.metric(
                label="Quality Rate",
                value=f"{metrics.get('quality_rate', 0)}%",
                help="Percentage of components rated 4+ stars"
            )
        
        with col3:
            st.metric(
                label="Total Components",
                value=metrics.get('total_components', 0),
                help="Number of completed components"
            )
        
        with col4:
            st.metric(
                label="High Quality",
                value=metrics.get('high_quality_components', 0),
                help="Components rated 4+ stars"
            )
    
    def _render_feedback_sections(self, assessment: Dict[str, Any]) -> None:
        """Render strengths and improvements sections"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💪 Strengths")
            strengths = assessment.get("strengths", [])
            if strengths:
                for strength in strengths:
                    st.markdown(f"• {strength}")
            else:
                st.markdown("*No specific strengths identified*")
        
        with col2:
            st.markdown("### 🎯 Areas for Improvement")
            improvements = assessment.get("improvements", [])
            if improvements:
                for improvement in improvements:
                    st.markdown(f"• {improvement}")
            else:
                st.markdown("*No specific improvements needed*")
    
    def _render_recommendations(self, recommendations: List[str]) -> None:
        """Render recommendations section"""
        if not recommendations:
            return
        
        st.markdown("### 💡 Recommendations")
        
        for i, recommendation in enumerate(recommendations, 1):
            st.markdown(f"{i}. {recommendation}")
    
    def render_compact_assessment(
        self, 
        main_category: str, 
        subcategory: str, 
        completed_components: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Render a compact assessment that can be embedded in the summary panel.
        
        Returns:
            Assessment data or None if no components
        """
        if not completed_components:
            return None
        
        # For compact view, we'll use a simplified assessment
        # This could be cached or use a lighter version
        try:
            # Calculate basic metrics
            ratings = [comp.get('user_rating', 1) for comp in completed_components]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            high_quality_count = sum(1 for rating in ratings if rating >= 4)
            quality_rate = (high_quality_count / len(ratings)) * 100 if ratings else 0
            
            # Simple quality score based on ratings and content length
            content_quality = self._calculate_content_quality(completed_components)
            overall_score = min(100, int((avg_rating * 20) + (quality_rate * 0.3) + content_quality))
            
            return {
                "overall_score": overall_score,
                "average_rating": round(avg_rating, 1),
                "quality_rate": round(quality_rate, 1),
                "total_components": len(completed_components),
                "high_quality_components": high_quality_count
            }
            
        except Exception as e:
            logger.error(f"Error in compact assessment: {e}")
            return None
    
    def _calculate_content_quality(self, completed_components: List[Dict[str, Any]]) -> float:
        """Calculate content quality score based on length and completeness"""
        if not completed_components:
            return 0
        
        total_score = 0
        for comp in completed_components:
            original_length = len(comp.get('original_value', ''))
            ai_length = len(comp.get('ai_processed_value', ''))
            
            # Score based on content length (more content = higher score)
            length_score = min(20, (original_length + ai_length) / 50)
            total_score += length_score
        
        return total_score / len(completed_components)

# Global instance
quality_assessment_panel = QualityAssessmentPanel()
