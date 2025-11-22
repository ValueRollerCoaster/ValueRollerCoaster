"""
Capability Helper
Utility functions to process capability and strength information for enhanced AI prompts.
"""

import logging
from typing import Dict, List, Any, Optional
from app.core.company_context_manager import CompanyContextManager

logger = logging.getLogger(__name__)

class CapabilityHelper:
    """Helper class for processing capability and strength information"""
    
    def __init__(self):
        company_context = CompanyContextManager()
        self.company_profile = company_context.get_company_profile()
        self.capabilities = self.company_profile.get("capabilities", {})
    
    def get_capability_context(self) -> str:
        """Generate capability context for AI prompts"""
        cap = self.capabilities
        
        context = f"""
        Core Capabilities:
        {self._format_list(cap.get('core_capabilities', []))}
        
        Technical Expertise:
        {self._format_list(cap.get('technical_expertise', []))}
        
        Operational Strengths:
        {self._format_list(cap.get('operational_strengths', []))}
        
        Differentiation Factors:
        {self._format_list(cap.get('differentiation_factors', []))}
        """
        
        return context.strip()
    
    def get_capabilities_for_field(self, field_category: str) -> List[str]:
        """Get relevant capabilities for a specific field category"""
        all_capabilities = self.capabilities.get('core_capabilities', [])
        
        # Map field categories to relevant capabilities
        category_capability_mapping = {
            'technical': [
                "Custom engineering and design",
                "Quality assurance",
                "Technical support"
            ],
            'business': [
                "Global manufacturing",
                "Global service network",
                "Technical support"
            ],
            'strategic': [
                "Custom engineering and design",
                "Global service network",
                "Technical support"
            ],
            'after_sales': [
                "Global service network",
                "Technical support",
                "Quality assurance"
            ]
        }
        
        # Get relevant capabilities for the category
        relevant_capabilities = category_capability_mapping.get(field_category.lower(), all_capabilities) or []
        
        # Filter to only include capabilities that exist in the company profile
        all_capabilities_list = all_capabilities or []
        return [cap for cap in relevant_capabilities if cap in all_capabilities_list]
    
    def get_technical_expertise_for_field(self, field_category: str) -> List[str]:
        """Get relevant technical expertise for a specific field category"""
        all_expertise = self.capabilities.get('technical_expertise', [])
        
        # Map field categories to relevant expertise (generic terms that apply across industries)
        category_expertise_mapping = {
            'technical': [
                "Custom engineering and design",
                "Precision manufacturing",
                "Performance optimization"
            ],
            'business': [
                "Quality control systems",
                "Performance optimization"
            ],
            'strategic': [
                "Custom engineering and design",
                "Performance optimization"
            ],
            'after_sales': [
                "Quality control systems",
                "Performance optimization"
            ]
        }
        
        # Get relevant expertise for the category
        relevant_expertise = category_expertise_mapping.get(field_category.lower(), all_expertise) or []
        
        # Filter to only include expertise that exists in the company profile
        all_expertise_list = all_expertise or []
        return [exp for exp in relevant_expertise if exp in all_expertise_list]
    
    def get_operational_strengths_for_field(self, field_category: str) -> List[str]:
        """Get relevant operational strengths for a specific field category"""
        all_strengths = self.capabilities.get('operational_strengths', [])
        
        # Map field categories to relevant strengths
        category_strength_mapping = {
            'technical': [
                "Long-term experience",
                "Quality certifications"
            ],
            'business': [
                "Global presence",
                "Customer partnerships"
            ],
            'strategic': [
                "Global presence",
                "Long-term experience"
            ],
            'after_sales': [
                "Global presence",
                "Customer partnerships"
            ]
        }
        
        # Get relevant strengths for the category
        relevant_strengths = category_strength_mapping.get(field_category.lower(), all_strengths) or []
        
        # Filter to only include strengths that exist in the company profile
        all_strengths_list = all_strengths or []
        return [strength for strength in relevant_strengths if strength in all_strengths_list]
    
    def get_differentiation_factors_for_field(self, field_category: str) -> List[str]:
        """Get relevant differentiation factors for a specific field category"""
        all_factors = self.capabilities.get('differentiation_factors', [])
        
        # Map field categories to relevant factors
        category_factor_mapping = {
            'technical': [
                "Proven reliability",
                "Custom engineering speed"
            ],
            'business': [
                "Global service support",
                "Long-term partnerships"
            ],
            'strategic': [
                "Proven reliability",
                "Long-term partnerships"
            ],
            'after_sales': [
                "Global service support",
                "Long-term partnerships"
            ]
        }
        
        # Get relevant factors for the category
        relevant_factors = category_factor_mapping.get(field_category.lower(), all_factors) or []
        
        # Filter to only include factors that exist in the company profile
        all_factors_list = all_factors or []
        return [factor for factor in relevant_factors if factor in all_factors_list]
    
    def generate_capability_focused_prompt(self, user_input: str, field_category: str) -> str:
        """Generate a capability-focused prompt for AI processing"""
        cap = self.capabilities
        
        # Get relevant information for the field category
        relevant_capabilities = self.get_capabilities_for_field(field_category)
        relevant_expertise = self.get_technical_expertise_for_field(field_category)
        relevant_strengths = self.get_operational_strengths_for_field(field_category)
        relevant_factors = self.get_differentiation_factors_for_field(field_category)
        
        prompt = f"""
        Company Capability Context:
        
        Relevant Core Capabilities for {field_category}:
        {self._format_list(relevant_capabilities)}
        
        Relevant Technical Expertise:
        {self._format_list(relevant_expertise)}
        
        Relevant Operational Strengths:
        {self._format_list(relevant_strengths)}
        
        Relevant Differentiation Factors:
        {self._format_list(relevant_factors)}
        
        User Input: {user_input}
        
        Task: Generate a customer benefit that leverages the company's relevant capabilities, expertise, strengths, and differentiation factors for {field_category} value components.
        """
        
        return prompt.strip()
    
    def get_strength_summary(self) -> str:
        """Get a summary of company strengths for AI context"""
        cap = self.capabilities
        
        summary = f"""
        This company excels in:
        • {', '.join(cap.get('differentiation_factors', [])[:2])}
        • {', '.join(cap.get('operational_strengths', [])[:2])}
        • {', '.join(cap.get('technical_expertise', [])[:2])}
        """
        
        return summary.strip()
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for display"""
        if not items:
            return "None specified"
        return "\n".join([f"• {item}" for item in items])

# Global instance
capability_helper = CapabilityHelper()
