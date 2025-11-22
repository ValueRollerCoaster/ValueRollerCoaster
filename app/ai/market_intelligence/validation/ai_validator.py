"""
AI Framework Validator
Uses AI to validate and refine framework properties

Uses ChatGPT (gpt-4o-mini) for comprehensive validation with better rate limits
and reliability compared to Gemini.
"""

import logging
import json
import re
import asyncio
from typing import Dict, List, Any
from app.ai.chatgpt_client import chatgpt_generate

logger = logging.getLogger(__name__)

class AIFrameworkValidator:
    """AI-powered framework validation and refinement"""
    
    async def validate_framework(self, framework_data: Dict[str, Any], 
                                                          company_profile: Dict[str, Any],
                                                          industry_name: str) -> Dict[str, Any]:
        """
        Comprehensive AI validation of framework
        
        Returns:
            {
                "overall_quality": 87,
                "relevance_scores": {...},
                "missing_elements": [...],
                "inconsistencies": [...],
                "refinements": [...]
            }
        """
        # Build comprehensive validation prompt
        prompt = self._build_validation_prompt(framework_data, company_profile, industry_name)
        
        try:
            from app.config import CHATGPT_MAX_TOKENS
            # Use appropriate token limit for comprehensive validation
            # ChatGPT has 4000 max, use up to 3500 for validation to ensure complete responses
            max_tokens_for_validation = min(CHATGPT_MAX_TOKENS, 3500)
            response = await chatgpt_generate(
                prompt,
                temperature=0.2,  # Low temperature for consistent validation
                max_tokens=max_tokens_for_validation
            )
            
            # Parse structured response
            validation_result = self._parse_validation_response(response)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in AI validation: {e}")
            return {
                "overall_quality": 0,
                "error": str(e)
            }
    
    def _build_validation_prompt(self, framework_data: Dict[str, Any], 
                                company_profile: Dict[str, Any],
                                industry_name: str) -> str:
        """Build comprehensive validation prompt (simplified to reduce tokens)"""
        
        # Simplify framework data - only include key properties, limit items
        simplified_framework = {
            "key_metrics": framework_data.get("key_metrics", [])[:8],
            "trend_areas": framework_data.get("trend_areas", [])[:8],
            "value_drivers": framework_data.get("value_drivers", [])[:8],
            "pain_points": framework_data.get("pain_points", [])[:8],
            "technology_focus": framework_data.get("technology_focus", [])[:8],
            "sustainability_initiatives": framework_data.get("sustainability_initiatives", [])[:8]
        }
        
        # Simplified company context
        core_business = company_profile.get('core_business', 'N/A')
        if len(core_business) > 150:
            core_business = core_business[:150] + "..."
        
        return f"""Validate framework quality for {industry_name}.

COMPANY: {company_profile.get('company_name', 'N/A')}
BUSINESS: {core_business}
CUSTOMERS: {', '.join(company_profile.get('target_customers', [])[:3])}

FRAMEWORK:
{json.dumps(simplified_framework, indent=1)}

Return JSON only:
{{
    "overall_quality": 87,
    "relevance_scores": {{
        "key_metrics": 85,
        "trend_areas": 92,
        "value_drivers": 78,
        "pain_points": 88,
        "technology_focus": 90,
        "sustainability_initiatives": 75
    }},
    "missing_elements": [
        {{"property": "trend_areas", "element": "Regulatory trends"}}
    ],
    "inconsistencies": [
        {{"type": "contradiction", "description": "Brief description"}}
    ],
    "refinements": [
        {{"property": "key_metrics", "action": "add", "item": "New metric", "confidence": 0.95}}
    ]
}}

Keep responses concise. No explanations."""
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse AI validation response with better error handling"""
        if not response or response.startswith("ERROR:"):
            logger.warning(f"AI returned error response: {response[:100]}")
            return {
                "overall_quality": 0,
                "error": "AI returned error response"
            }
        
        try:
            # Try to extract JSON - handle truncated responses
            json_match = re.search(r'\{.*"overall_quality".*\}', response, re.DOTALL)
            if not json_match:
                # Try broader match
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                # Clean up common JSON issues
                json_str = json_str.replace("//", "").strip()
                
                # Try to fix incomplete JSON if truncated
                if not json_str.strip().endswith('}'):
                    # Try to close the JSON object
                    if '"overall_quality"' in json_str:
                        # Extract overall_quality if present
                        quality_match = re.search(r'"overall_quality"\s*:\s*(\d+)', json_str)
                        if quality_match:
                            quality = int(quality_match.group(1))
                            return {
                                "overall_quality": quality,
                                "partial_response": True,
                                "note": "Response was truncated, only overall_quality extracted"
                            }
                
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parse error: {e}, response: {response[:300]}")
                    # Try to extract just the overall_quality score
                    quality_match = re.search(r'"overall_quality"\s*:\s*(\d+)', response)
                    if quality_match:
                        return {
                            "overall_quality": int(quality_match.group(1)),
                            "partial_response": True
                        }
        except Exception as e:
            logger.warning(f"Error parsing validation response: {e}")
        
        # Fallback: return empty result
        return {
            "overall_quality": 0,
            "error": "Could not parse AI response"
        }
    
    async def apply_refinements(self, framework_data: Dict[str, Any], 
                               refinements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply AI-suggested refinements to framework
        
        Returns: Refined framework data
        """
        refined_framework = framework_data.copy()
        
        for refinement in refinements:
            property_name = refinement.get("property")
            action = refinement.get("action")
            confidence = refinement.get("confidence", 0.0)
            
            # Only apply high-confidence refinements automatically
            if confidence < 0.85:
                continue
            
            if action == "replace":
                item = refinement.get("item")
                suggestion = refinement.get("suggestion")
                
                if property_name in refined_framework and isinstance(refined_framework[property_name], list):
                    # Replace item
                    try:
                        index = refined_framework[property_name].index(item)
                        refined_framework[property_name][index] = suggestion
                    except ValueError:
                        # Item not found, skip
                        pass
            
            elif action == "add":
                suggestion = refinement.get("suggestion")
                
                if property_name in refined_framework and isinstance(refined_framework[property_name], list):
                    if suggestion not in refined_framework[property_name]:
                        refined_framework[property_name].append(suggestion)
            
            elif action == "remove":
                item = refinement.get("item")
                
                if property_name in refined_framework and isinstance(refined_framework[property_name], list):
                    if item in refined_framework[property_name]:
                        refined_framework[property_name].remove(item)
        
        return refined_framework

