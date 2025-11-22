"""
Enhanced Sonar Validation
Provides Sonar validation functions for each step of the persona generation process.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from .sonar_client import sonar_client

logger = logging.getLogger(__name__)

class EnhancedSonarValidator:
    """Enhanced Sonar validation for persona generation steps"""
    
    def __init__(self):
        self.client = sonar_client
        logger.info("[EnhancedSonarValidator] Initialized")
    
    async def validate_website_analysis(self, gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                       website_url: str, pid: int = 0) -> Dict[str, Any]:
        """
        Step 1 Validation: Validate Gemini and ChatGPT website analysis results.
        
        Args:
            gemini_analysis: Gemini's website analysis
            chatgpt_analysis: ChatGPT's website analysis  
            website_url: Target website URL
            pid: Process ID for logging
            
        Returns:
            Validation result with confidence scores and corrections
        """
        logger.info(f"[PID {pid}] [EnhancedSonarValidator] Validating website analysis for: {website_url}")
        
        if not await self.client.is_available():
            return self._create_unavailable_response("website_analysis_validation")
        
        # Extract key claims from both analyses
        gemini_claims = self._extract_key_claims(gemini_analysis)
        chatgpt_claims = self._extract_key_claims(chatgpt_analysis)
        
        # Build validation prompt
        prompt = f"""
        WEBSITE ANALYSIS VALIDATION: {website_url}
        
        TASK: Validate and fact-check the website analysis results from two AI models.
        
        GEMINI CLAIMS:
        {json.dumps(gemini_claims, indent=2)}
        
        CHATGPT CLAIMS:
        {json.dumps(chatgpt_claims, indent=2)}
        
        VALIDATION INSTRUCTIONS:
        1. Search for information about {website_url} specifically
        2. Verify each claim against authoritative sources
        3. Identify any factual errors or hallucinations
        4. Provide confidence scores for each claim
        5. Suggest corrections for any errors found
        
        Return JSON with:
        {{
            "validation_passed": true/false,
            "overall_confidence": 1-10,
            "gemini_validation": {{
                "confidence_score": 1-10,
                "verified_claims": ["claim1", "claim2"],
                "questionable_claims": ["claim1", "claim2"],
                "corrections": ["correction1", "correction2"]
            }},
            "chatgpt_validation": {{
                "confidence_score": 1-10,
                "verified_claims": ["claim1", "claim2"],
                "questionable_claims": ["claim1", "claim2"],
                "corrections": ["correction1", "correction2"]
            }},
            "recommended_synthesis": "How to combine the validated results",
            "validation_notes": "Notes about the validation process"
        }}
        """
        
        # Use domain filtering to focus on the target website
        target_domain = self._extract_domain_from_url(website_url)
        search_domains = [target_domain] if target_domain else []
        
        response = await self.client.generate_response(
            prompt=prompt,
            search_domain_filter=search_domains,
            pid=pid
        )
        
        result = self._parse_json_response(response, pid)
        result["validation_type"] = "website_analysis"
        result["target_domain"] = target_domain
        
        return result
    
    async def validate_market_intelligence(self, market_intelligence: Dict, website_url: str, 
                                          industry: str, pid: int = 0) -> Dict[str, Any]:
        """
        Step 3 Validation: Validate market intelligence results.
        
        Args:
            market_intelligence: Market intelligence analysis
            website_url: Target website URL
            industry: Industry classification
            pid: Process ID for logging
            
        Returns:
            Validation result with confidence scores and corrections
        """
        logger.info(f"[PID {pid}] [EnhancedSonarValidator] Validating market intelligence for: {website_url}")
        
        if not await self.client.is_available():
            return self._create_unavailable_response("market_intelligence_validation")
        
        # Extract market intelligence claims
        market_claims = self._extract_market_claims(market_intelligence)
        
        prompt = f"""
        MARKET INTELLIGENCE VALIDATION: {website_url}
        
        INDUSTRY: {industry}
        
        TASK: Validate market intelligence analysis against current market data.
        
        MARKET INTELLIGENCE CLAIMS:
        {json.dumps(market_claims, indent=2)}
        
        VALIDATION INSTRUCTIONS:
        1. Search for current market trends in {industry} industry
        2. Verify market size, growth rates, and competitive landscape
        3. Check for recent industry developments and news
        4. Validate competitive positioning claims
        5. Verify market opportunity assessments
        
        Return JSON with:
        {{
            "validation_passed": true/false,
            "overall_confidence": 1-10,
            "verified_market_data": ["data1", "data2"],
            "questionable_claims": ["claim1", "claim2"],
            "market_corrections": ["correction1", "correction2"],
            "additional_market_insights": ["insight1", "insight2"],
            "validation_notes": "Notes about market validation"
        }}
        """
        
        # Use industry-specific domains for validation
        industry_domains = self._get_industry_domains(industry)
        
        response = await self.client.generate_response(
            prompt=prompt,
            search_domain_filter=industry_domains,
            pid=pid
        )
        
        result = self._parse_json_response(response, pid)
        result["validation_type"] = "market_intelligence"
        result["industry"] = industry
        
        return result
    
    async def validate_value_alignment(self, value_alignment: Dict, website_url: str, 
                                      pid: int = 0) -> Dict[str, Any]:
        """
        Step 4 Validation: Validate value alignment analysis.
        
        Args:
            value_alignment: Value alignment analysis
            website_url: Target website URL
            pid: Process ID for logging
            
        Returns:
            Validation result with confidence scores and corrections
        """
        logger.info(f"[PID {pid}] [EnhancedSonarValidator] Validating value alignment for: {website_url}")
        
        if not await self.client.is_available():
            return self._create_unavailable_response("value_alignment_validation")
        
        # Extract value alignment claims
        value_claims = self._extract_value_claims(value_alignment)
        
        prompt = f"""
        VALUE ALIGNMENT VALIDATION: {website_url}
        
        TASK: Validate value alignment analysis against company information.
        
        VALUE ALIGNMENT CLAIMS:
        {json.dumps(value_claims, indent=2)}
        
        VALIDATION INSTRUCTIONS:
        1. Search for information about {website_url} business needs
        2. Verify pain points and challenges mentioned
        3. Check if value drivers align with company profile
        4. Validate opportunity assessments
        5. Verify strategic recommendations
        
        Return JSON with:
        {{
            "validation_passed": true/false,
            "overall_confidence": 1-10,
            "verified_value_insights": ["insight1", "insight2"],
            "questionable_assessments": ["assessment1", "assessment2"],
            "value_corrections": ["correction1", "correction2"],
            "additional_opportunities": ["opportunity1", "opportunity2"],
            "validation_notes": "Notes about value alignment validation"
        }}
        """
        
        # Use target domain for validation
        target_domain = self._extract_domain_from_url(website_url)
        search_domains = [target_domain] if target_domain else []
        
        response = await self.client.generate_response(
            prompt=prompt,
            search_domain_filter=search_domains,
            pid=pid
        )
        
        result = self._parse_json_response(response, pid)
        result["validation_type"] = "value_alignment"
        result["target_domain"] = target_domain
        
        return result
    
    async def validate_creative_elements(self, creative_elements: Dict, website_url: str, 
                                        pid: int = 0) -> Dict[str, Any]:
        """
        Step 5 Validation: Validate creative persona elements.
        
        Args:
            creative_elements: Creative persona elements
            website_url: Target website URL
            pid: Process ID for logging
            
        Returns:
            Validation result with confidence scores and corrections
        """
        logger.info(f"[PID {pid}] [EnhancedSonarValidator] Validating creative elements for: {website_url}")
        
        if not await self.client.is_available():
            return self._create_unavailable_response("creative_elements_validation")
        
        # Extract creative elements
        creative_claims = self._extract_creative_claims(creative_elements)
        
        prompt = f"""
        CREATIVE ELEMENTS VALIDATION: {website_url}
        
        TASK: Validate creative persona elements for relevance and accuracy.
        
        CREATIVE ELEMENTS:
        {json.dumps(creative_claims, indent=2)}
        
        VALIDATION INSTRUCTIONS:
        1. Check if creative elements align with company profile
        2. Verify emotional factors and pain points are realistic
        3. Validate goals and objectives are appropriate
        4. Check if creative insights are grounded in reality
        5. Ensure elements are relevant to the target company
        
        Return JSON with:
        {{
            "validation_passed": true/false,
            "overall_confidence": 1-10,
            "validated_elements": ["element1", "element2"],
            "questionable_elements": ["element1", "element2"],
            "creative_corrections": ["correction1", "correction2"],
            "enhanced_insights": ["insight1", "insight2"],
            "validation_notes": "Notes about creative elements validation"
        }}
        """
        
        # Use target domain for validation
        target_domain = self._extract_domain_from_url(website_url)
        search_domains = [target_domain] if target_domain else []
        
        response = await self.client.generate_response(
            prompt=prompt,
            search_domain_filter=search_domains,
            pid=pid
        )
        
        result = self._parse_json_response(response, pid)
        result["validation_type"] = "creative_elements"
        result["target_domain"] = target_domain
        
        return result
    
    async def validate_final_synthesis_structure(self, final_persona: Dict, website_url: str = "", pid: int = 0) -> Dict[str, Any]:
        """
        Quick structure validation - checks for required fields presence.
        Full content validation should be deferred until after enrichment.
        
        Args:
            final_persona: Persona dictionary to validate
            website_url: Optional website URL
            pid: Process ID for logging
            
        Returns:
            Structure validation result
        """
        required_fields = ["company", "product_range", "services", "pain_points", "goals"]
        missing_fields = [field for field in required_fields if field not in final_persona]
        
        if missing_fields:
            return {
                "validation_passed": False,
                "overall_confidence": 3,
                "validation_type": "final_synthesis_structure",
                "missing_fields": missing_fields,
                "target_domain": self._extract_domain_from_url(website_url) if website_url else "",
                "validation_notes": f"Missing required structure fields: {missing_fields}. Content validation deferred."
            }
        
        # Check if optional fields are present (but don't fail if missing)
        optional_fields_present = []
        optional_fields_missing = []
        
        for field in ["target_market", "business_model", "challenges", "value_drivers", "value_signals"]:
            if field in final_persona and final_persona[field]:
                optional_fields_present.append(field)
            else:
                optional_fields_missing.append(field)
        
        return {
            "validation_passed": True,
            "overall_confidence": 7,
            "validation_type": "final_synthesis_structure",
            "verified_elements": required_fields + optional_fields_present,
            "missing_optional_fields": optional_fields_missing,
            "target_domain": self._extract_domain_from_url(website_url) if website_url else "",
            "validation_notes": f"All required structure fields present. Optional fields: {len(optional_fields_present)} present, {len(optional_fields_missing)} missing. Content validation deferred."
        }
    
    async def validate_final_synthesis(self, final_persona: Dict, website_url: str, 
                                      pid: int = 0) -> Dict[str, Any]:
        """
        Step 6 Validation: Validate final persona synthesis.
        
        Args:
            final_persona: Final synthesized persona
            website_url: Target website URL
            pid: Process ID for logging
            
        Returns:
            Validation result with confidence scores and corrections
        """
        logger.info(f"[PID {pid}] [EnhancedSonarValidator] Validating final synthesis for: {website_url}")
        
        if not await self.client.is_available():
            return self._create_unavailable_response("final_synthesis_validation")
        
        # Extract key persona elements
        persona_claims = self._extract_persona_claims(final_persona)
        
        prompt = f"""
        FINAL SYNTHESIS VALIDATION: {website_url}
        
        TASK: Validate the final synthesized persona for completeness and accuracy.
        
        FINAL PERSONA CLAIMS:
        {json.dumps(persona_claims, indent=2)}
        
        VALIDATION INSTRUCTIONS:
        1. Verify all key persona elements are accurate
        2. Check for completeness of information
        3. Validate logical consistency
        4. Ensure relevance to target company
        5. Check for any missing critical information
        
        Return JSON with:
        {{
            "validation_passed": true/false,
            "overall_confidence": 1-10,
            "completeness_score": 1-10,
            "accuracy_score": 1-10,
            "consistency_score": 1-10,
            "verified_elements": ["element1", "element2"],
            "missing_elements": ["element1", "element2"],
            "synthesis_corrections": ["correction1", "correction2"],
            "final_recommendations": ["recommendation1", "recommendation2"],
            "validation_notes": "Notes about final synthesis validation"
        }}
        """
        
        # Use target domain for validation
        target_domain = self._extract_domain_from_url(website_url)
        search_domains = [target_domain] if target_domain else []
        
        response = await self.client.generate_response(
            prompt=prompt,
            search_domain_filter=search_domains,
            pid=pid
        )
        
        result = self._parse_json_response(response, pid)
        result["validation_type"] = "final_synthesis"
        result["target_domain"] = target_domain
        
        return result
    
    def _extract_key_claims(self, analysis: Dict) -> Dict[str, Any]:
        """Extract key claims from analysis for validation"""
        claims = {
            "company_info": {},
            "business_model": "",
            "products_services": [],
            "target_market": "",
            "pain_points": [],
            "goals": []
        }
        
        try:
            # Extract company information
            if "company" in analysis:
                claims["company_info"] = analysis["company"]
            
            # Extract business model
            if "business_model" in analysis:
                claims["business_model"] = analysis["business_model"]
            
            # Extract products/services
            if "product_range" in analysis:
                claims["products_services"].extend(analysis["product_range"])
            if "services" in analysis:
                claims["products_services"].extend(analysis["services"])
            
            # Extract target market
            if "target_market" in analysis:
                claims["target_market"] = analysis["target_market"]
            
            # Extract pain points
            if "pain_points" in analysis:
                claims["pain_points"] = analysis["pain_points"]
            
            # Extract goals
            if "goals" in analysis:
                claims["goals"] = analysis["goals"]
                
        except Exception as e:
            logger.warning(f"[EnhancedSonarValidator] Error extracting claims: {e}")
        
        return claims
    
    def _extract_market_claims(self, market_intelligence: Dict) -> Dict[str, Any]:
        """Extract market intelligence claims for validation"""
        claims = {
            "industry_trends": [],
            "market_size": "",
            "competitive_landscape": [],
            "growth_opportunities": [],
            "risk_factors": []
        }
        
        try:
            if isinstance(market_intelligence, dict):
                claims["industry_trends"] = market_intelligence.get("industry_trends", [])
                claims["market_size"] = market_intelligence.get("market_size", "")
                claims["competitive_landscape"] = market_intelligence.get("competitive_landscape", [])
                claims["growth_opportunities"] = market_intelligence.get("growth_opportunities", [])
                claims["risk_factors"] = market_intelligence.get("risk_factors", [])
        except Exception as e:
            logger.warning(f"[EnhancedSonarValidator] Error extracting market claims: {e}")
        
        return claims
    
    def _extract_value_claims(self, value_alignment: Dict) -> Dict[str, Any]:
        """Extract value alignment claims for validation"""
        claims = {
            "value_drivers": [],
            "pain_points": [],
            "opportunities": [],
            "strategic_recommendations": []
        }
        
        try:
            if isinstance(value_alignment, dict):
                claims["value_drivers"] = value_alignment.get("value_drivers", [])
                claims["pain_points"] = value_alignment.get("pain_points", [])
                claims["opportunities"] = value_alignment.get("opportunities", [])
                claims["strategic_recommendations"] = value_alignment.get("strategic_recommendations", [])
        except Exception as e:
            logger.warning(f"[EnhancedSonarValidator] Error extracting value claims: {e}")
        
        return claims
    
    def _extract_creative_claims(self, creative_elements: Dict) -> Dict[str, Any]:
        """Extract creative elements claims for validation"""
        claims = {
            "innovative_pain_points": [],
            "creative_goals": [],
            "emotional_factors": [],
            "future_objectives": []
        }
        
        try:
            if isinstance(creative_elements, dict):
                claims["innovative_pain_points"] = creative_elements.get("innovative_pain_points", [])
                claims["creative_goals"] = creative_elements.get("creative_goals", [])
                claims["emotional_factors"] = creative_elements.get("emotional_factors", [])
                claims["future_objectives"] = creative_elements.get("future_objectives", [])
        except Exception as e:
            logger.warning(f"[EnhancedSonarValidator] Error extracting creative claims: {e}")
        
        return claims
    
    def _extract_persona_claims(self, final_persona: Dict) -> Dict[str, Any]:
        """Extract final persona claims for validation"""
        claims = {
            "company_info": {},
            "business_analysis": {},
            "customer_insights": {},
            "value_analysis": {},
            "market_intelligence": {}
        }
        
        try:
            if isinstance(final_persona, dict):
                claims["company_info"] = final_persona.get("company", {})
                claims["business_analysis"] = {
                    "product_range": final_persona.get("product_range", []),
                    "services": final_persona.get("services", []),
                    "target_market": final_persona.get("target_market", ""),  # Now explicitly requested in synthesis
                    "business_model": final_persona.get("business_model", "")  # Now explicitly requested in synthesis
                }
                claims["customer_insights"] = {
                    "pain_points": final_persona.get("pain_points", []),
                    "goals": final_persona.get("goals", []),
                    "challenges": final_persona.get("challenges", [])  # Now explicitly requested in synthesis
                }
                claims["value_analysis"] = {
                    "value_drivers": final_persona.get("value_drivers", []),
                    "value_signals": final_persona.get("value_signals", [])
                }
                claims["market_intelligence"] = final_persona.get("market_intelligence", {})
        except Exception as e:
            logger.warning(f"[EnhancedSonarValidator] Error extracting persona claims: {e}")
        
        return claims
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL for search filtering"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"[EnhancedSonarValidator] Could not extract domain from {url}: {e}")
            return ""
    
    def _get_industry_domains(self, industry: str) -> List[str]:
        """Get industry-specific domains for validation"""
        # Map industries to authoritative domains
        industry_domain_map = {
            "manufacturing": ["manufacturingtomorrow.com", "automationworld.com", "industryweek.com"],
            "construction": ["constructiondive.com", "engineeringnews-record.com", "constructionexec.com"],
            "agriculture": ["agriculture.com", "farmprogress.com", "agweb.com"],
            "mining": ["mining.com", "miningweekly.com", "mining-technology.com"],
            "logistics": ["logisticsmgmt.com", "supplychaindive.com", "dcvelocity.com"],
            "utilities": ["utilitydive.com", "energy.gov", "eia.gov"],
            "forestry": ["forestry.com", "forestindustry.com", "forestbusinessnetwork.com"],
            "material_handling": ["mhlnews.com", "materialhandling247.com", "mmh.com"]
        }
        
        industry_lower = industry.lower()
        for key, domains in industry_domain_map.items():
            if key in industry_lower:
                return domains
        
        return []
    
    def _parse_json_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse JSON response from Sonar"""
        
        if response.startswith("ERROR"):
            logger.error(f"[PID {pid}] [EnhancedSonarValidator] Sonar response error: {response}")
            return {"error": response}
        
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                logger.warning(f"[PID {pid}] [EnhancedSonarValidator] No JSON found in response: {response}")
                return {"error": "Could not parse Sonar response"}
                
        except json.JSONDecodeError as e:
            logger.error(f"[PID {pid}] [EnhancedSonarValidator] JSON parse error: {e}")
            return {"error": f"JSON parse error: {str(e)}"}
    
    def _create_unavailable_response(self, validation_type: str) -> Dict[str, Any]:
        """Create response when Sonar is unavailable"""
        return {
            "validation_passed": True,  # Default to proceed
            "overall_confidence": 5,
            "sonar_available": False,
            "validation_type": validation_type,
            "validation_notes": f"Sonar unavailable for {validation_type} validation"
        }

# Global instance
enhanced_sonar_validator = EnhancedSonarValidator() 