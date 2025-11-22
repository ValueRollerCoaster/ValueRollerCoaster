"""
Value Delivery Helper
Utility functions to process value delivery information and enhance AI prompts.
"""

import logging
from typing import Dict, List, Any, Optional
from app.core.company_context_manager import CompanyContextManager

logger = logging.getLogger(__name__)

class ValueDeliveryHelper:
    """Helper class for processing value delivery information"""
    
    def __init__(self):
        company_context = CompanyContextManager()
        self.company_profile = company_context.get_company_profile()
        self.value_delivery = self.company_profile.get("value_delivery", {})
    
    def get_value_proposition_context(self) -> str:
        """Generate value proposition context for AI prompts"""
        vd = self.value_delivery
        
        context = f"""
        Primary Value Proposition: {vd.get('primary_value_proposition', 'Unknown')}
        
        Value Delivery Channels:
        {self._format_list(vd.get('value_delivery_channels', []))}
        
        Success Patterns:
        {self._format_list(vd.get('success_patterns', []))}
        
        Customer Outcomes:
        {self._format_list(vd.get('customer_outcomes', []))}
        
        Value Creation Process:
        {self._format_list(vd.get('value_creation_process', []))}
        """
        
        return context.strip()
    
    def get_customer_outcomes_for_field(self, field_category: str) -> List[str]:
        """Get relevant customer outcomes for a specific field category"""
        all_outcomes = self.value_delivery.get('customer_outcomes', []) or []
        
        # Map field categories to relevant outcomes
        category_outcome_mapping = {
            'technical': [
                "Improved equipment reliability",
                "Enhanced performance efficiency",
                "Extended product lifecycles"
            ],
            'business': [
                "Reduced operational costs",
                "Improved equipment reliability",
                "Enhanced performance efficiency"
            ],
            'strategic': [
                "Long-term partnership value",
                "Competitive advantage",
                "Market differentiation"
            ],
            'after_sales': [
                "Ongoing support and service",
                "Maintenance optimization",
                "Continuous improvement"
            ]
        }
        
        # Get relevant outcomes for the category
        relevant_outcomes = category_outcome_mapping.get(field_category.lower(), all_outcomes) or []
        
        # Filter to only include outcomes that exist in the company profile
        return [outcome for outcome in relevant_outcomes if outcome in all_outcomes]
    
    def get_success_patterns_for_field(self, field_category: str) -> List[str]:
        """Get relevant success patterns for a specific field category"""
        all_patterns = self.value_delivery.get('success_patterns', []) or []
        
        # Map field categories to relevant patterns
        category_pattern_mapping = {
            'technical': [
                "Custom engineering solutions",
                "Proven reliability in harsh environments"
            ],
            'business': [
                "Long-term OEM partnerships",
                "Global service support"
            ],
            'strategic': [
                "Long-term OEM partnerships",
                "Custom engineering solutions"
            ],
            'after_sales': [
                "Global service support",
                "Long-term OEM partnerships"
            ]
        }
        
        # Get relevant patterns for the category
        relevant_patterns = category_pattern_mapping.get(field_category.lower(), all_patterns) or []
        
        # Filter to only include patterns that exist in the company profile
        return [pattern for pattern in relevant_patterns if pattern in all_patterns]
    
    def get_value_creation_process_for_field(self, field_category: str) -> List[str]:
        """Get relevant value creation processes for a specific field category"""
        all_processes = self.value_delivery.get('value_creation_process', []) or []
        
        # Map field categories to relevant processes
        category_process_mapping = {
            'technical': [
                "Custom engineering and design",
                "Quality manufacturing processes",
                "Comprehensive testing and validation"
            ],
            'business': [
                "Quality manufacturing processes",
                "Global service and support"
            ],
            'strategic': [
                "Custom engineering and design",
                "Global service and support"
            ],
            'after_sales': [
                "Global service and support",
                "Comprehensive testing and validation"
            ]
        }
        
        # Get relevant processes for the category
        relevant_processes = category_process_mapping.get(field_category.lower(), all_processes) or []
        
        # Filter to only include processes that exist in the company profile
        return [process for process in relevant_processes if process in all_processes]
    
    def generate_value_focused_prompt(self, user_input: str, field_category: str) -> str:
        """Generate a value-focused prompt for AI processing"""
        vd = self.value_delivery
        
        # Get relevant information for the field category
        relevant_outcomes = self.get_customer_outcomes_for_field(field_category)
        relevant_patterns = self.get_success_patterns_for_field(field_category)
        relevant_processes = self.get_value_creation_process_for_field(field_category)
        
        prompt = f"""
        Company Value Context:
        Primary Value Proposition: {vd.get('primary_value_proposition', 'Unknown')}
        
        Relevant Customer Outcomes for {field_category}:
        {self._format_list(relevant_outcomes)}
        
        Relevant Success Patterns:
        {self._format_list(relevant_patterns)}
        
        Relevant Value Creation Processes:
        {self._format_list(relevant_processes)}
        
        User Input: {user_input}
        
        Task: Generate a customer benefit that aligns with the company's value proposition and focuses on the relevant outcomes, patterns, and processes for {field_category} value components.
        """
        
        return prompt.strip()
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for display"""
        if not items:
            return "None specified"
        return "\n".join([f"• {item}" for item in items])

# Global instance
value_delivery_helper = ValueDeliveryHelper()
