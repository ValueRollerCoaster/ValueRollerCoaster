"""
Soft Motivation System for Quality Assessment
Provides gentle, encouraging feedback instead of complex scoring.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SoftMotivationSystem:
    """Provides soft, encouraging feedback for value components"""
    
    def __init__(self):
        self.company_context_manager = None
        self._load_company_context()
    
    def _load_company_context(self):
        """Load company context for assessment"""
        try:
            from app.core.company_context_manager import CompanyContextManager
            self.company_context_manager = CompanyContextManager()
        except Exception as e:
            logger.warning(f"Could not load company context: {e}")
    
    def generate_soft_feedback(
        self, 
        main_category: str, 
        subcategory: str, 
        completed_components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate soft, encouraging feedback for completed components.
        
        Args:
            main_category: Main category (e.g., "Technical Value")
            subcategory: Subcategory (e.g., "Innovation")
            completed_components: List of completed components with data
            
        Returns:
            Dict with soft feedback and simple metrics
        """
        if not completed_components:
            return self._get_empty_feedback(subcategory)
        
        try:
            # Analyze the three-way comparison
            analysis = self._analyze_components(completed_components)
            
            # Generate soft feedback based on analysis
            feedback = self._generate_encouraging_feedback(analysis, subcategory)
            
            return {
                "subcategory": subcategory,
                "total_components": len(completed_components),
                "completed_components": len(completed_components),
                "feedback": feedback,
                "analysis": analysis,
                "motivation_level": self._get_motivation_level(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error generating soft feedback: {e}")
            return self._get_fallback_feedback(subcategory)
    
    def _analyze_components(self, completed_components: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze components using three-way comparison"""
        analysis: Dict[str, float] = {
            "guidance_following": 0.0,  # How well user followed AI guidance
            "input_quality": 0.0,       # Quality of user input
            "benefit_quality": 0.0,     # Quality of AI-generated benefits
            "company_alignment": 0.0,   # How well benefits align with company
            "overall_progress": 0.0     # Overall assessment
        }
        
        total_score = 0
        component_count = len(completed_components)
        
        for comp in completed_components:
            comp_analysis = self._analyze_single_component(comp)
            
            # Add to overall analysis
            for key in analysis:
                if key != "overall_progress":
                    analysis[key] += comp_analysis.get(key, 0)
            
            total_score += comp_analysis.get("overall_score", 0)
        
        # Calculate averages
        for key in analysis:
            if key != "overall_progress":
                analysis[key] = float(analysis[key] / component_count if component_count > 0 else 0.0)
        
        analysis["overall_progress"] = float(total_score / component_count if component_count > 0 else 0.0)
        
        return analysis
    
    def _analyze_single_component(self, component: Dict[str, Any]) -> Dict[str, float]:
        """Analyze a single component using three-way comparison"""
        original_value = component.get("original_value", "")
        ai_guidance = component.get("ai_guidance", "")
        ai_processed_value = component.get("ai_processed_value", "")
        user_rating = component.get("user_rating", 1)
        
        analysis: Dict[str, float] = {
            "guidance_following": 0.0,
            "input_quality": 0.0,
            "benefit_quality": 0.0,
            "company_alignment": 0.0,
            "overall_score": 0.0
        }
        
        # 1. Guidance Following: How well did user incorporate AI guidance?
        if ai_guidance and original_value:
            guidance_similarity = self._calculate_text_similarity(original_value, ai_guidance)
            analysis["guidance_following"] = float(min(guidance_similarity * 100, 100))
        
        # 2. Input Quality: Quality of user's original input
        input_quality = self._assess_input_quality(original_value)
        analysis["input_quality"] = float(input_quality)
        
        # 3. Benefit Quality: Quality of AI-generated benefits
        benefit_quality = self._assess_benefit_quality(ai_processed_value)
        analysis["benefit_quality"] = float(benefit_quality)
        
        # 4. Company Alignment: How well benefits align with company profile
        company_alignment = self._assess_company_alignment(ai_processed_value)
        analysis["company_alignment"] = float(company_alignment)
        
        # 5. Overall Score: Weighted combination
        weights = {
            "guidance_following": 0.2,
            "input_quality": 0.2,
            "benefit_quality": 0.3,
            "company_alignment": 0.3
        }
        
        overall_score = 0.0
        for key, weight in weights.items():
            overall_score += analysis[key] * weight
        
        analysis["overall_score"] = float(overall_score)
        
        return analysis
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _assess_input_quality(self, input_text: str) -> float:
        """Assess quality of user input"""
        if not input_text:
            return 0.0
        
        score = 0.0
        
        # Length factor (not too short, not too long)
        length = len(input_text)
        if 20 <= length <= 200:
            score += 30
        elif 10 <= length < 20 or 200 < length <= 400:
            score += 20
        else:
            score += 10
        
        # Specificity factor (numbers, specific terms)
        if any(char.isdigit() for char in input_text):
            score += 20
        
        # Technical terms or business language
        business_terms = ['quality', 'performance', 'innovation', 'reliable', 'efficient', 'advanced', 'certified', 'standard']
        if any(term in input_text.lower() for term in business_terms):
            score += 20
        
        # Completeness factor
        if len(input_text.split('.')) > 1:  # Multiple sentences
            score += 30
        
        return min(score, 100)
    
    def _assess_benefit_quality(self, benefit_text: str) -> float:
        """Assess quality of AI-generated benefits"""
        if not benefit_text:
            return 0.0
        
        score = 0.0
        
        # Customer-focused language
        customer_terms = ['customer', 'benefit', 'value', 'advantage', 'solution', 'help', 'ensure', 'provide']
        if any(term in benefit_text.lower() for term in customer_terms):
            score += 40
        
        # Specificity and detail
        if len(benefit_text) > 50:
            score += 30
        
        # Professional tone
        if any(word in benefit_text.lower() for word in ['professional', 'expertise', 'experience', 'quality', 'reliable']):
            score += 30
        
        return min(score, 100)
    
    def _assess_company_alignment(self, benefit_text: str) -> float:
        """Assess how well benefits align with company profile"""
        if not benefit_text or not self.company_context_manager:
            return 50.0  # Default moderate score
        
        try:
            company_profile = self.company_context_manager.get_company_profile()
            if not company_profile:
                return 50.0
            
            # Simple keyword matching with company profile
            company_keywords = []
            
            # Extract keywords from company profile
            core_business = company_profile.get("core_business", "").lower()
            if core_business:
                company_keywords.extend(core_business.split())
            
            capabilities = company_profile.get("capabilities", {})
            for cap_list in capabilities.values():
                if isinstance(cap_list, list):
                    company_keywords.extend([cap.lower() for cap in cap_list])
            
            # Check alignment
            if company_keywords:
                benefit_lower = benefit_text.lower()
                matches = sum(1 for keyword in company_keywords if keyword in benefit_lower)
                alignment_score = min((matches / len(company_keywords)) * 100, 100)
                return alignment_score
            
            return 50.0
            
        except Exception as e:
            logger.warning(f"Error assessing company alignment: {e}")
            return 50.0
    
    def _generate_encouraging_feedback(self, analysis: Dict[str, Any], subcategory: str) -> str:
        """Generate encouraging feedback based on analysis"""
        guidance_following = analysis.get("guidance_following", 0)
        input_quality = analysis.get("input_quality", 0)
        benefit_quality = analysis.get("benefit_quality", 0)
        company_alignment = analysis.get("company_alignment", 0)
        overall_progress = analysis.get("overall_progress", 0)
        
        # Generate positive feedback based on strengths
        feedback_parts = []
        
        if guidance_following > 70:
            feedback_parts.append("Great job following the AI guidance! *")
        elif guidance_following > 40:
            feedback_parts.append("You're incorporating AI suggestions well! +")
        else:
            feedback_parts.append("Try incorporating more of the AI guidance! ^")
        
        if input_quality > 70:
            feedback_parts.append("Your input really helped create strong benefits! *")
        elif input_quality > 40:
            feedback_parts.append("Your input quality is improving! +")
        else:
            feedback_parts.append("More detailed input will help create better benefits! ^")
        
        if company_alignment > 70:
            feedback_parts.append("Perfect alignment with your company profile! *")
        elif company_alignment > 40:
            feedback_parts.append("Good company alignment! Keep it up! +")
        else:
            feedback_parts.append("Focus on your company's unique strengths! ^")
        
        # Overall encouragement
        if overall_progress > 80:
            return f"Outstanding work on {subcategory}! " + " ".join(feedback_parts[:2])
        elif overall_progress > 60:
            return f"Great progress on {subcategory}! " + " ".join(feedback_parts[:2])
        elif overall_progress > 40:
            return f"You're on the right track with {subcategory}! " + " ".join(feedback_parts[:1])
        else:
            return f"Keep building your {subcategory} components! " + " ".join(feedback_parts[:1])
    
    def _get_motivation_level(self, analysis: Dict[str, Any]) -> str:
        """Get motivation level based on analysis"""
        overall_progress = analysis.get("overall_progress", 0)
        
        if overall_progress > 80:
            return "excellent"
        elif overall_progress > 60:
            return "great"
        elif overall_progress > 40:
            return "good"
        else:
            return "building"
    
    def _get_empty_feedback(self, subcategory: str) -> Dict[str, Any]:
        """Get feedback for empty components"""
        return {
            "subcategory": subcategory,
            "total_components": 0,
            "completed_components": 0,
            "feedback": f"Start working on your {subcategory} components! ^",
            "analysis": {},
            "motivation_level": "starting"
        }
    
    def _get_fallback_feedback(self, subcategory: str) -> Dict[str, Any]:
        """Get fallback feedback if analysis fails"""
        return {
            "subcategory": subcategory,
            "total_components": 0,
            "completed_components": 0,
            "feedback": f"Keep working on your {subcategory} components! +",
            "analysis": {},
            "motivation_level": "building"
        }

# Global instance
soft_motivation_system = SoftMotivationSystem()
