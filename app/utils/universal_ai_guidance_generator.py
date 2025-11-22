import json
import asyncio
import logging
from typing import Dict, Any

class UniversalAIGuidanceGenerator:
    """Generates AI guidance based on actual company profile data"""
    
    def __init__(self):
        from app.utils.universal_company_context_extractor import UniversalCompanyContextExtractor
        self.context_extractor = UniversalCompanyContextExtractor()
    
    async def generate_field_guidance(self, user_input: str, field_description: str, 
                                    field_name: str, main_category: str, subcategory: str) -> Dict[str, Any]:
        """Generate AI guidance using actual company context"""
        
        # Extract dynamic company context
        company_context = self.context_extractor.extract_field_specific_context(
            field_name, main_category, subcategory
        )
        
        # Build dynamic prompt based on actual company data
        prompt = self._build_dynamic_prompt(user_input, field_description, field_name, 
                                          main_category, subcategory, company_context)
        
        # Get AI response
        ai_response = await self._get_ai_response(prompt)
        
        return ai_response
    
    def _build_dynamic_prompt(self, user_input: str, field_description: str, field_name: str,
                            main_category: str, subcategory: str, company_context: Dict[str, Any]) -> str:
        """Build dynamic prompt based on actual company data"""
        
        # Company basics
        company_basics = company_context["company_basics"]
        company_name = company_basics.get("name", "the company")
        core_business = company_basics.get("core_business", "the company's business")
        
        # Business context
        business_context = company_context["business_context"]
        company_type = business_context.get("company_type", "company")
        business_model = business_context.get("business_model", "business model")
        market_position = business_context.get("market_position", "market position")
        
        # Industry context
        industry_context = company_context["industry_context"]
        target_industries = industry_context.get("target_industries", [])
        target_customers = industry_context.get("target_customers", [])
        
        # Capability context
        capability_context = company_context["capability_context"]
        core_capabilities = capability_context.get("core_capabilities", [])
        technical_expertise = capability_context.get("technical_expertise", [])
        
        # Value context
        value_context = company_context["value_context"]
        primary_value = value_context.get("primary_value", "value proposition")
        customer_outcomes = value_context.get("customer_outcomes", [])
        
        # Field context
        field_context = company_context["field_specific"]
        expectation_type = field_context.get("expectation_type", "benefits")
        focus_areas = field_context.get("focus_areas", [])
        
        prompt = f"""
        Provide helpful guidance for user input regarding field relevance.
        Focus on constructive suggestions based on the actual company context.
        
        COMPANY CONTEXT:
        - Company: {company_name}
        - Core Business: {core_business}
        - Company Type: {company_type}
        - Business Model: {business_model}
        - Market Position: {market_position}
        
        INDUSTRY CONTEXT:
        - Target Industries: {', '.join(target_industries) if target_industries else 'Various industries'}
        - Target Customers: {', '.join(target_customers) if target_customers else 'Various customers'}
        
        CAPABILITIES:
        - Core Capabilities: {', '.join(core_capabilities) if core_capabilities else 'Various capabilities'}
        - Technical Expertise: {', '.join(technical_expertise) if technical_expertise else 'Technical expertise'}
        
        VALUE CONTEXT:
        - Primary Value: {primary_value}
        - Customer Outcomes: {', '.join(customer_outcomes) if customer_outcomes else 'Various outcomes'}
        
        FIELD ANALYSIS:
        - Field: {field_name}
        - Category: {main_category} > {subcategory}
        - Description: {field_description}
        - Expectation Type: {expectation_type}
        - Focus Areas: {', '.join(focus_areas)}
        
        USER INPUT: {user_input}
        
        TASK: Provide guidance that helps the user improve their input to be more relevant to this specific company and field.
        
        Provide guidance in this JSON format:
        {{
            "relevance_score": 75,
            "company_alignment": "How well the input aligns with the company's actual business",
            "industry_relevance": "How relevant the input is to the company's target industries",
            "capability_alignment": "How well the input leverages the company's actual capabilities",
            "suggestions": [
                "Specific suggestion based on company context",
                "Another suggestion based on actual capabilities"
            ],
            "company_context": "How this input relates to the company's actual business context",
            "examples": [
                "Example input that would be more relevant to this company",
                "Another example based on actual company capabilities"
            ],
            "strengths": [
                "What the input does well",
                "Another strength"
            ],
            "areas_for_improvement": [
                "Specific area that could be improved",
                "Another improvement area"
            ],
            "field_specific_guidance": "Specific guidance for this field type"
        }}
        """
        
        return prompt
    
    async def _get_ai_response(self, prompt: str) -> Dict[str, Any]:
        """Get AI response with error handling"""
        try:
            from app.ai.gemini_client import gemini_client
            response = await gemini_client(prompt, temperature=0.2)
            
            # Validate response
            if not response or not response.strip():
                logging.error("AI returned empty response")
                raise ValueError("Empty response from AI")
            
            # Try to parse JSON (handle markdown-wrapped JSON)
            try:
                # First try direct JSON parsing
                parsed_response = json.loads(response)
                return parsed_response
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                try:
                    # Look for JSON wrapped in markdown code blocks
                    if "```json" in response:
                        # Extract content between ```json and ```
                        start_marker = "```json"
                        end_marker = "```"
                        start_idx = response.find(start_marker) + len(start_marker)
                        end_idx = response.find(end_marker, start_idx)
                        if end_idx != -1:
                            json_content = response[start_idx:end_idx].strip()
                            parsed_response = json.loads(json_content)
                            return parsed_response
                    
                    # Try to find JSON object in the response
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(0)
                        parsed_response = json.loads(json_content)
                        return parsed_response
                        
                except (json.JSONDecodeError, ValueError) as inner_error:
                    logging.error(f"JSON parsing failed after markdown extraction: {inner_error}")
                    logging.error(f"Raw response: {response[:500]}...")  # Log first 500 chars
                    raise ValueError(f"Invalid JSON response: {inner_error}")
                
                # If we get here, all parsing attempts failed
                logging.error(f"JSON parsing failed after all attempts")
                logging.error(f"Raw response: {response[:500]}...")  # Log first 500 chars
                raise ValueError(f"Invalid JSON response after all parsing attempts")
                
        except Exception as e:
            logging.error(f"AI guidance generation failed: {e}")
            return {
                "relevance_score": 50,
                "company_alignment": "Unable to analyze company alignment",
                "industry_relevance": "Unable to analyze industry relevance",
                "capability_alignment": "Unable to analyze capability alignment",
                "suggestions": ["Please try again or proceed with current input"],
                "company_context": f"Error in analysis: {str(e)}",
                "examples": [],
                "strengths": [],
                "areas_for_improvement": ["Unable to provide specific guidance"],
                "field_specific_guidance": "Unable to provide field-specific guidance"
            }
