"""
Adaptability Helper
Utility functions to process adaptability information and enhance AI prompts with flexibility context.
"""

import logging
from typing import Dict, List, Any, Optional
from app.core.company_context_manager import CompanyContextManager

logger = logging.getLogger(__name__)

class AdaptabilityHelper:
    """Helper class for processing adaptability information"""
    
    def __init__(self):
        company_context = CompanyContextManager()
        self.company_profile = company_context.get_company_profile()
        self.adaptability = self.company_profile.get("adaptability", {})
    
    def get_adaptability_context(self) -> str:
        """Generate adaptability context for AI prompts"""
        adapt = self.adaptability
        
        context = f"""
        Industry Adaptability:
        • Core Technology: {adapt.get('industry_adaptability', {}).get('core_technology', 'Unknown')}
        • Application Flexibility: {adapt.get('industry_adaptability', {}).get('application_flexibility', 'Unknown')}
        • Customization Capability: {adapt.get('industry_adaptability', {}).get('customization_capability', 'Unknown')}
        • Scalability: {adapt.get('industry_adaptability', {}).get('scalability', 'Unknown')}
        
        Customer Adaptability:
        • Customer Size Range: {adapt.get('customer_adaptability', {}).get('customer_size_range', 'Unknown')}
        • Geographic Adaptability: {adapt.get('customer_adaptability', {}).get('geographic_adaptability', 'Unknown')}
        • Technical Adaptability: {adapt.get('customer_adaptability', {}).get('technical_adaptability', 'Unknown')}
        • Service Adaptability: {adapt.get('customer_adaptability', {}).get('service_adaptability', 'Unknown')}
        
        Market Adaptability:
        • Technology Evolution: {adapt.get('market_adaptability', {}).get('technology_evolution', 'Unknown')}
        • Market Trends: {adapt.get('market_adaptability', {}).get('market_trends', 'Unknown')}
        • Regulatory Changes: {adapt.get('market_adaptability', {}).get('regulatory_changes', 'Unknown')}
        • Customer Evolution: {adapt.get('market_adaptability', {}).get('customer_evolution', 'Unknown')}
        """
        
        return context.strip()
    
    def get_industry_expertise_for_field(self, field_category: str) -> List[str]:
        """Get relevant industry expertise for a specific field category"""
        all_expertise = self.adaptability.get('industry_adaptability', {}).get('industry_expertise', [])
        
        # Map field categories to relevant industry expertise
        category_expertise_mapping = {
            'technical': [
                "Mining",
                "Construction",
                "Agriculture"
            ],
            'business': [
                "Material Handling",
                "Utility",
                "Forestry"
            ],
            'strategic': [
                "Mining",
                "Construction",
                "Agriculture"
            ],
            'after_sales': [
                "Utility",
                "Forestry",
                "Material Handling"
            ]
        }
        
        # Get relevant expertise for the category
        relevant_expertise = category_expertise_mapping.get(field_category.lower(), all_expertise) or []
        
        # Filter to only include expertise that exists in the company profile
        all_expertise_list = all_expertise or []
        return [exp for exp in relevant_expertise if exp in all_expertise_list]
    
    def get_partnership_flexibility_for_field(self, field_category: str) -> List[str]:
        """Get relevant partnership flexibility for a specific field category"""
        all_partnerships = self.adaptability.get('customer_adaptability', {}).get('partnership_flexibility', [])
        
        # Map field categories to relevant partnerships
        category_partnership_mapping = {
            'technical': [
                "Direct OEM partnerships",
                "System integrator collaboration"
            ],
            'business': [
                "Distribution channel support",
                "Direct OEM partnerships"
            ],
            'strategic': [
                "Direct OEM partnerships",
                "System integrator collaboration"
            ],
            'after_sales': [
                "Distribution channel support",
                "System integrator collaboration"
            ]
        }
        
        # Get relevant partnerships for the category
        relevant_partnerships = category_partnership_mapping.get(field_category.lower(), all_partnerships) or []
        
        # Filter to only include partnerships that exist in the company profile
        all_partnerships_list = all_partnerships or []
        return [part for part in relevant_partnerships if part in all_partnerships_list]
    
    def get_market_adaptability_for_field(self, field_category: str) -> Dict[str, str]:
        """Get relevant market adaptability factors for a specific field category"""
        market_adapt = self.adaptability.get('market_adaptability', {})
        
        # Map field categories to relevant market factors
        category_market_mapping = {
            'technical': {
                'technology_evolution': market_adapt.get('technology_evolution', 'Unknown'),
                'market_trends': market_adapt.get('market_trends', 'Unknown')
            },
            'business': {
                'market_trends': market_adapt.get('market_trends', 'Unknown'),
                'regulatory_changes': market_adapt.get('regulatory_changes', 'Unknown')
            },
            'strategic': {
                'technology_evolution': market_adapt.get('technology_evolution', 'Unknown'),
                'customer_evolution': market_adapt.get('customer_evolution', 'Unknown')
            },
            'after_sales': {
                'regulatory_changes': market_adapt.get('regulatory_changes', 'Unknown'),
                'customer_evolution': market_adapt.get('customer_evolution', 'Unknown')
            }
        }
        
        result = category_market_mapping.get(field_category.lower(), market_adapt)
        if result is None:
            return {}
        # Ensure all values are strings
        return {k: str(v) if v is not None else 'Unknown' for k, v in result.items()}
    
    def generate_adaptability_focused_prompt(self, user_input: str, field_category: str) -> str:
        """Generate an adaptability-focused prompt for AI processing"""
        adapt = self.adaptability
        
        # Get relevant information for the field category
        relevant_expertise = self.get_industry_expertise_for_field(field_category)
        relevant_partnerships = self.get_partnership_flexibility_for_field(field_category)
        relevant_market = self.get_market_adaptability_for_field(field_category)
        
        prompt = f"""
        Company Adaptability Context:
        
        Industry Adaptability:
        • Core Technology: {adapt.get('industry_adaptability', {}).get('core_technology', 'Unknown')}
        • Customization Capability: {adapt.get('industry_adaptability', {}).get('customization_capability', 'Unknown')}
        • Relevant Industry Expertise:
        {self._format_list(relevant_expertise)}
        
        Customer Adaptability:
        • Customer Size Range: {adapt.get('customer_adaptability', {}).get('customer_size_range', 'Unknown')}
        • Geographic Adaptability: {adapt.get('customer_adaptability', {}).get('geographic_adaptability', 'Unknown')}
        • Relevant Partnership Flexibility:
        {self._format_list(relevant_partnerships)}
        
        Market Adaptability:
        • Technology Evolution: {relevant_market.get('technology_evolution', 'Unknown')}
        • Market Trends: {relevant_market.get('market_trends', 'Unknown')}
        • Regulatory Changes: {relevant_market.get('regulatory_changes', 'Unknown')}
        • Customer Evolution: {relevant_market.get('customer_evolution', 'Unknown')}
        
        User Input: {user_input}
        
        Task: Generate a customer benefit that emphasizes the company's adaptability and flexibility for {field_category} value components, highlighting how they can adapt to different customer needs and market conditions.
        """
        
        return prompt.strip()
    
    def get_adaptability_summary(self) -> str:
        """Get a summary of company adaptability for AI context"""
        adapt = self.adaptability
        
        summary = f"""
        This company demonstrates high adaptability through:
        • {adapt.get('industry_adaptability', {}).get('customization_capability', 'Unknown')}
        • {adapt.get('customer_adaptability', {}).get('geographic_adaptability', 'Unknown')}
        • {adapt.get('market_adaptability', {}).get('technology_evolution', 'Unknown')}
        • {adapt.get('market_adaptability', {}).get('market_trends', 'Unknown')}
        """
        
        return summary.strip()
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for display"""
        if not items:
            return "None specified"
        return "\n".join([f"• {item}" for item in items])

# Global instance
adaptability_helper = AdaptabilityHelper()
