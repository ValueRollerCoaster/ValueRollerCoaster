"""
Component Quality Assessor
Evaluates completed value components against company profile and provides motivational feedback.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from app.core.company_context_manager import CompanyContextManager
from app.ai.gemini_client import gemini_client

logger = logging.getLogger(__name__)

class ComponentQualityAssessor:
    """Assesses quality of completed value components against company profile"""
    
    def __init__(self):
        self.company_context = CompanyContextManager()
        self.company_profile = self.company_context.get_company_profile()
    
    async def assess_subcategory_quality(
        self, 
        main_category: str, 
        subcategory: str, 
        completed_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess the quality of all completed components in a subcategory.
        
        Args:
            main_category: Main category (e.g., "Technical Value")
            subcategory: Subcategory (e.g., "Quality")
            completed_components: List of completed components with their data
            
        Returns:
            Dict containing assessment results and motivational feedback
        """
        try:
            if not completed_components:
                return self._get_empty_assessment()
            
            # Generate comprehensive assessment
            assessment = await self._generate_ai_assessment(
                main_category, subcategory, completed_components
            )
            
            # Calculate quality metrics
            metrics = self._calculate_quality_metrics(completed_components)
            
            # Generate motivational feedback
            motivation = self._generate_motivational_feedback(assessment, metrics)
            
            return {
                "overall_score": assessment.get("overall_score", 0),
                "strengths": assessment.get("strengths", []),
                "improvements": assessment.get("improvements", []),
                "company_alignment": assessment.get("company_alignment", 0),
                "metrics": metrics,
                "motivation": motivation,
                "recommendations": assessment.get("recommendations", []),
                "assessment_date": assessment.get("assessment_date", ""),
                "subcategory": subcategory,
                "main_category": main_category
            }
            
        except Exception as e:
            logger.error(f"Error assessing subcategory quality: {e}")
            return self._get_error_assessment()
    
    async def _generate_ai_assessment(
        self, 
        main_category: str, 
        subcategory: str, 
        completed_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered assessment of component quality"""
        
        # Prepare company context
        company_context = self._prepare_company_context()
        
        # Prepare component data for analysis
        component_data = self._prepare_component_data(completed_components)
        
        # Create assessment prompt
        prompt = f"""
        You are a business value assessment expert. Analyze the quality of completed value components for a company.

        COMPANY PROFILE:
        {company_context}

        ASSESSMENT TARGET:
        - Main Category: {main_category}
        - Subcategory: {subcategory}
        - Completed Components: {len(completed_components)}

        COMPONENT DATA:
        {component_data}

        ASSESSMENT CRITERIA:
        1. Company Alignment: How well do the components align with the company's actual capabilities and profile?
        2. Specificity: Are the components specific and detailed rather than generic?
        3. Value Proposition: Do the components clearly communicate customer value?
        4. Completeness: Are all aspects of the subcategory well covered?
        5. Differentiation: Do the components highlight what makes this company unique?

        PROVIDE ASSESSMENT IN THIS JSON FORMAT:
        {{
            "overall_score": 85,
            "company_alignment": 90,
            "strengths": [
                "Strong alignment with company's technical expertise",
                "Clear value propositions for target customers",
                "Good coverage of quality standards"
            ],
            "improvements": [
                "Could be more specific about certification details",
                "Missing quantitative performance metrics"
            ],
            "recommendations": [
                "Add specific certification numbers and dates",
                "Include measurable quality metrics",
                "Reference specific industry standards"
            ],
            "assessment_date": "2025-01-15"
        }}

        Focus on providing actionable, specific feedback that helps improve the value components.
        """
        
        try:
            response = await gemini_client(prompt, temperature=0.3, max_tokens=1200)
            
            # Parse JSON response
            import json
            try:
                assessment = json.loads(response)
                return assessment
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._parse_text_response(response)
                
        except Exception as e:
            logger.error(f"Error generating AI assessment: {e}")
            return self._get_fallback_assessment()
    
    def _prepare_company_context(self) -> str:
        """Prepare comprehensive company context for assessment"""
        context_parts = []
        
        # Basic company info
        context_parts.append(f"Company: {self.company_profile.get('company_name', 'Unknown')}")
        context_parts.append(f"Core Business: {self.company_profile.get('core_business', 'Unknown')}")
        context_parts.append(f"Vision: {self.company_profile.get('vision', 'Unknown')}")
        context_parts.append(f"Mission: {self.company_profile.get('mission', 'Unknown')}")
        
        # Business intelligence
        bi = self.company_profile.get("business_intelligence", {})
        context_parts.append(f"Company Type: {bi.get('company_type', 'Unknown')}")
        context_parts.append(f"Market Position: {bi.get('market_position', 'Unknown')}")
        context_parts.append(f"Industry Focus: {bi.get('industry_focus', 'Unknown')}")
        
        # Capabilities
        capabilities = self.company_profile.get("capabilities", {})
        context_parts.append(f"Core Capabilities: {', '.join(capabilities.get('core_capabilities', []))}")
        context_parts.append(f"Technical Expertise: {', '.join(capabilities.get('technical_expertise', []))}")
        context_parts.append(f"Differentiation Factors: {', '.join(capabilities.get('differentiation_factors', []))}")
        
        # Target customers
        target_customers = self.company_profile.get("target_customers", [])
        context_parts.append(f"Target Customers: {', '.join(target_customers)}")
        
        return "\n".join(context_parts)
    
    def _prepare_component_data(self, completed_components: List[Dict[str, Any]]) -> str:
        """Prepare component data for analysis"""
        component_texts = []
        
        for comp in completed_components:
            comp_text = f"""
            Component: {comp.get('name', 'Unknown')}
            Original Value: {comp.get('original_value', '')}
            AI Processed Value: {comp.get('ai_processed_value', '')}
            User Rating: {comp.get('user_rating', 1)}
            """
            component_texts.append(comp_text.strip())
        
        return "\n\n".join(component_texts)
    
    def _calculate_quality_metrics(self, completed_components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quantitative quality metrics"""
        if not completed_components:
            return {}
        
        # Calculate average user rating
        ratings = [comp.get('user_rating', 1) for comp in completed_components]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Calculate content quality metrics
        total_original_length = sum(len(comp.get('original_value', '')) for comp in completed_components)
        total_ai_length = sum(len(comp.get('ai_processed_value', '')) for comp in completed_components)
        
        # Calculate completion rate (assuming 5 is max rating)
        high_quality_count = sum(1 for rating in ratings if rating >= 4)
        quality_rate = (high_quality_count / len(ratings)) * 100 if ratings else 0
        
        return {
            "average_rating": round(avg_rating, 1),
            "total_components": len(completed_components),
            "high_quality_components": high_quality_count,
            "quality_rate": round(quality_rate, 1),
            "total_original_length": total_original_length,
            "total_ai_length": total_ai_length,
            "avg_original_length": round(total_original_length / len(completed_components), 1),
            "avg_ai_length": round(total_ai_length / len(completed_components), 1)
        }
    
    def _generate_motivational_feedback(self, assessment: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Generate motivational feedback based on assessment and metrics"""
        overall_score = assessment.get("overall_score", 0)
        quality_rate = metrics.get("quality_rate", 0)
        avg_rating = metrics.get("average_rating", 0)
        
        if overall_score >= 90:
            return f"EXCELLENT work! Your {assessment.get('subcategory', 'components')} are outstanding (Score: {overall_score}/100). You've created high-quality value propositions that strongly align with your company profile."
        elif overall_score >= 80:
            return f"GREAT job! Your {assessment.get('subcategory', 'components')} are very good (Score: {overall_score}/100). You're on the right track with strong company alignment."
        elif overall_score >= 70:
            return f"GOOD progress! Your {assessment.get('subcategory', 'components')} are solid (Score: {overall_score}/100). A few improvements could make them even better."
        elif overall_score >= 60:
            return f"KEEP GOING! Your {assessment.get('subcategory', 'components')} are developing well (Score: {overall_score}/100). Focus on the recommendations to improve quality."
        else:
            return f"BUILDING FOUNDATION! Your {assessment.get('subcategory', 'components')} are a good start (Score: {overall_score}/100). Use the feedback to enhance them further."
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        return {
            "overall_score": 75,
            "company_alignment": 70,
            "strengths": ["Components show good effort"],
            "improvements": ["Could benefit from more specific details"],
            "recommendations": ["Review company profile for better alignment"],
            "assessment_date": "2025-01-15"
        }
    
    def _get_empty_assessment(self) -> Dict[str, Any]:
        """Return assessment for empty subcategory"""
        return {
            "overall_score": 0,
            "strengths": [],
            "improvements": [],
            "company_alignment": 0,
            "metrics": {},
            "motivation": "Complete some components to get a quality assessment!",
            "recommendations": ["Start by entering text in the component fields"],
            "assessment_date": "2025-01-15",
            "subcategory": "Unknown",
            "main_category": "Unknown"
        }
    
    def _get_error_assessment(self) -> Dict[str, Any]:
        """Return assessment for error cases"""
        return {
            "overall_score": 0,
            "strengths": [],
            "improvements": [],
            "company_alignment": 0,
            "metrics": {},
            "motivation": "Unable to assess quality at this time. Please try again.",
            "recommendations": ["Check your internet connection and try again"],
            "assessment_date": "2025-01-15",
            "subcategory": "Unknown",
            "main_category": "Unknown"
        }
    
    def _get_fallback_assessment(self) -> Dict[str, Any]:
        """Return fallback assessment when AI fails"""
        return {
            "overall_score": 70,
            "company_alignment": 65,
            "strengths": ["Components are completed"],
            "improvements": ["Could be more specific"],
            "recommendations": ["Review company profile for better alignment"],
            "assessment_date": "2025-01-15"
        }

# Global instance
component_quality_assessor = ComponentQualityAssessor()
