"""
Business Intelligence Helper
Utility functions to process and enhance business intelligence data for AI consumption.
"""

import logging
from typing import Dict, List, Any, Optional
from app.core.company_context_manager import CompanyContextManager

logger = logging.getLogger(__name__)

class BusinessIntelligenceHelper:
    """Helper class for processing business intelligence data"""
    
    def __init__(self):
        company_context = CompanyContextManager()
        self.company_profile = company_context.get_company_profile()
        self.business_intelligence = self.company_profile.get("business_intelligence", {})
    
    def get_company_context_for_ai(self) -> str:
        """Generate comprehensive company context for AI prompts"""
        context_parts = []
        
        # Basic company info
        context_parts.append(f"Company: {self.company_profile.get('company_name', 'Unknown')}")
        context_parts.append(f"Core Business: {self.company_profile.get('core_business', 'Unknown')}")
        context_parts.append(f"Vision: {self.company_profile.get('vision', 'Unknown')}")
        
        # Business intelligence
        bi = self.business_intelligence
        context_parts.append(f"Company Type: {bi.get('company_type', 'Unknown')}")
        context_parts.append(f"Business Model: {bi.get('business_model', 'Unknown')}")
        context_parts.append(f"Market Position: {bi.get('market_position', 'Unknown')}")
        context_parts.append(f"Company Size: {bi.get('company_size', 'Unknown')}")
        context_parts.append(f"Maturity Stage: {bi.get('maturity_stage', 'Unknown')}")
        context_parts.append(f"Geographic Scope: {bi.get('geographic_scope', 'Unknown')}")
        context_parts.append(f"Industry Focus: {bi.get('industry_focus', 'Unknown')}")
        context_parts.append(f"Value Delivery: {bi.get('value_delivery_method', 'Unknown')}")
        context_parts.append(f"Revenue Model: {bi.get('revenue_model', 'Unknown')}")
        context_parts.append(f"Customer Relationship: {bi.get('customer_relationship_type', 'Unknown')}")
        context_parts.append(f"Innovation Focus: {bi.get('innovation_focus', 'Unknown')}")
        context_parts.append(f"Competitive Advantage: {bi.get('competitive_advantage_type', 'Unknown')}")
        
        return "\n".join(context_parts)
    
    def get_value_proposition_context(self) -> str:
        """Generate value proposition context for AI"""
        bi = self.business_intelligence
        
        context = f"""
        This company is a {bi.get('company_size', 'Unknown')} {bi.get('company_type', 'Unknown')} 
        operating as a {bi.get('business_model', 'Unknown')} with {bi.get('market_position', 'Unknown')} 
        market position. They deliver value through {bi.get('value_delivery_method', 'Unknown')} 
        and focus on {bi.get('innovation_focus', 'Unknown')}. Their competitive advantage is 
        {bi.get('competitive_advantage_type', 'Unknown')} and they maintain {bi.get('customer_relationship_type', 'Unknown')} 
        relationships with customers.
        """
        
        return context.strip()
    
    def get_ai_prompt_context(self, field_category: Optional[str] = None) -> str:
        """Generate AI prompt context based on field category"""
        bi = self.business_intelligence
        
        base_context = self.get_company_context_for_ai()
        
        if field_category:
            # Add category-specific context
            if "technical" in field_category.lower():
                context_addition = f"""
                Focus on technical capabilities and {bi.get('innovation_focus', 'Unknown')} aspects.
                Emphasize {bi.get('competitive_advantage_type', 'Unknown')} in technical terms.
                """
            elif "business" in field_category.lower():
                context_addition = f"""
                Focus on business value and {bi.get('value_delivery_method', 'Unknown')} benefits.
                Emphasize {bi.get('revenue_model', 'Unknown')} and customer relationships.
                """
            elif "strategic" in field_category.lower():
                context_addition = f"""
                Focus on strategic positioning and {bi.get('market_position', 'Unknown')} advantages.
                Emphasize long-term {bi.get('customer_relationship_type', 'Unknown')} value.
                """
            else:
                context_addition = ""
            
            return base_context + context_addition
        
        return base_context

# Global instance
business_intelligence_helper = BusinessIntelligenceHelper()
