"""
Enhanced AI Processor
Advanced AI processing with field-specific context from business intelligence, 
value delivery, capabilities, and adaptability frameworks.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from app.ai.gemini_client import gemini_client
from app.utils.business_intelligence_helper import business_intelligence_helper
from app.utils.value_delivery_helper import value_delivery_helper
from app.utils.capability_helper import capability_helper
from app.utils.adaptability_helper import adaptability_helper

logger = logging.getLogger(__name__)

class EnhancedAIProcessor:
    """Enhanced AI processor with comprehensive company context"""
    
    def __init__(self):
        self.bi_helper = business_intelligence_helper
        self.vd_helper = value_delivery_helper
        self.cap_helper = capability_helper
        self.adapt_helper = adaptability_helper
    
    async def process_value_with_field_context(self, value: str, field_category: str, component_name: Optional[str] = None) -> str:
        """
        Process value with field-specific context from all frameworks
        
        Args:
            value: User input value
            field_category: Category of the field (technical, business, strategic, after_sales)
            component_name: Name of the component for additional context
        """
        
        # Get field-specific context from all frameworks
        bi_context = self.bi_helper.get_ai_prompt_context(field_category)
        vd_prompt = self.vd_helper.generate_value_focused_prompt(value, field_category)
        cap_prompt = self.cap_helper.generate_capability_focused_prompt(value, field_category)
        adapt_prompt = self.adapt_helper.generate_adaptability_focused_prompt(value, field_category)
        
        # Create comprehensive field-specific prompt
        prompt = self._create_field_specific_prompt(
            value, field_category, component_name,
            bi_context, vd_prompt, cap_prompt, adapt_prompt
        )
        
        try:
            # Process with AI
            ai_response = await gemini_client(prompt, temperature=0.15)  # Lower temperature for more consistent results
            
            # Extract and validate response
            processed_value = self._extract_and_validate_response(ai_response, value)
            
            return processed_value
            
        except Exception as e:
            logger.error(f"Error in enhanced AI processing: {e}")
            return "AI could not generate a suitable customer benefit. Please rephrase the input."
    
    def _create_field_specific_prompt(self, value: str, field_category: str, component_name: Optional[str],
                                    bi_context: str, vd_prompt: str, cap_prompt: str, adapt_prompt: str) -> str:
        """Create a comprehensive field-specific prompt"""
        
        # Field-specific instructions
        field_instructions = self._get_field_specific_instructions(field_category)
        
        prompt = f"""
        COMPREHENSIVE FIELD-SPECIFIC CUSTOMER BENEFIT GENERATION
        
        FIELD CATEGORY: {field_category.upper()}
        COMPONENT: {component_name or 'General'}
        
        ===== BUSINESS INTELLIGENCE CONTEXT =====
        {bi_context}
        
        ===== VALUE DELIVERY CONTEXT =====
        {vd_prompt}
        
        ===== CAPABILITY CONTEXT =====
        {cap_prompt}
        
        ===== ADAPTABILITY CONTEXT =====
        {adapt_prompt}
        
        ===== FIELD-SPECIFIC INSTRUCTIONS =====
        {field_instructions}
        
        ===== USER INPUT =====
        {value}
        
        ===== TASK =====
        Generate a customer benefit that:
        1. Aligns with the {field_category} category focus
        2. Leverages relevant company capabilities and strengths
        3. Emphasizes value delivery methods appropriate for this field
        4. Highlights adaptability factors relevant to {field_category} value components
        5. Uses factual, third-person language (no slogans or imperatives)
        6. Explains the specific mechanism that delivers the benefit
        7. References relevant customer outcomes and success patterns
        
        FORMAT: Single paragraph, 2-3 sentences, factual and descriptive
        
        OUTPUT:
        """
        
        return prompt.strip()
    
    def _get_field_specific_instructions(self, field_category: str) -> str:
        """Get field-specific instructions for AI processing"""
        
        instructions = {
            'technical': """
            TECHNICAL FIELD FOCUS:
            - Emphasize technical capabilities and engineering expertise
            - Highlight performance, reliability, and precision aspects
            - Reference technical specifications and engineering processes
            - Focus on technical problem-solving and optimization
            - Use technical terminology appropriately
            """,
            
            'business': """
            BUSINESS FIELD FOCUS:
            - Emphasize business value and ROI aspects
            - Highlight cost savings, efficiency gains, and operational benefits
            - Reference business processes and operational improvements
            - Focus on business outcomes and strategic advantages
            - Use business terminology and value propositions
            """,
            
            'strategic': """
            STRATEGIC FIELD FOCUS:
            - Emphasize long-term strategic advantages and positioning
            - Highlight competitive differentiation and market advantages
            - Reference strategic partnerships and market positioning
            - Focus on strategic value and long-term benefits
            - Use strategic terminology and positioning language
            """,
            
            'after_sales': """
            AFTER-SALES FIELD FOCUS:
            - Emphasize ongoing support, service, and maintenance benefits
            - Highlight service network, availability, and support capabilities
            - Reference service processes and customer support excellence
            - Focus on post-purchase value and ongoing relationship benefits
            - Use service and support terminology
            """
        }
        
        return instructions.get(field_category.lower(), instructions['business'])
    
    def _extract_and_validate_response(self, ai_response: str, original_value: str) -> str:
        """Extract and validate AI response"""
        
        # Try to extract JSON response
        try:
            data = json.loads(ai_response)
            if isinstance(data, dict):
                # Look for common response fields
                for key in ['value_proposition', 'benefit', 'result', 'output']:
                    if key in data:
                        return data[key]
        except:
            pass
        
        # Use raw response if not JSON
        ai_text = ai_response.strip()
        
        # Basic validation
        if len(ai_text) < 20:
            return "AI response too short. Please rephrase the input."
        
        if len(ai_text) > 500:
            # Truncate if too long
            ai_text = ai_text[:500] + "..."
        
        return ai_text
    
    async def process_multiple_values(self, values: List[Dict[str, str]]) -> List[str]:
        """Process multiple values with their respective field contexts"""
        
        results = []
        
        for value_data in values:
            value = value_data.get('value', '')
            field_category = value_data.get('field_category', 'business')
            component_name = value_data.get('component_name', None)
            
            result = await self.process_value_with_field_context(
                value, field_category, component_name or None
            )
            results.append(result)
        
        return results

# Global instance
enhanced_ai_processor = EnhancedAIProcessor()
