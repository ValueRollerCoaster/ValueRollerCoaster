"""
Domain Validator
Validates domain ownership and prevents website↔company misinterpretations.
"""

import logging
from typing import Dict, List, Any, Optional
from .sonar_client import sonar_client

logger = logging.getLogger(__name__)

class DomainValidator:
    """Validates domain ownership and prevents misinterpretations"""
    
    def __init__(self):
        logger.info("[DomainValidator] Initialized")
    
    async def validate_domain_ownership(self, website_url: str, website_content: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """
        Validate the actual company that owns and operates the website.
        
        Args:
            website_url: Target website URL
            website_content: Optional website content
            pid: Process ID for logging
            
        Returns:
            Domain ownership validation result
        """
        logger.info(f"[PID {pid}] [DomainValidator] Validating domain ownership for: {website_url}")
        
        try:
            prompt = self._build_domain_ownership_prompt(website_url, website_content)
            response = await sonar_client.generate_response(prompt, pid=pid)
            result = self._parse_domain_response(response, pid)
            
            logger.info(f"[PID {pid}] [DomainValidator] Domain validation complete - Owner: {result.get('actual_company_name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [DomainValidator] Error in domain validation: {e}")
            return {
                "actual_company_name": "Unknown",
                "company_business": "Unknown",
                "ownership_confidence": 0,
                "error": f"Domain validation failed: {str(e)}"
            }
    
    async def validate_content_ownership(self, website_content: str, website_url: str, pid: int = 0) -> Dict[str, Any]:
        """
        Analyze who the website content is actually about.
        
        Args:
            website_content: Website content to analyze
            website_url: Website URL for context
            pid: Process ID for logging
            
        Returns:
            Content ownership analysis result
        """
        logger.info(f"[PID {pid}] [DomainValidator] Analyzing content ownership for: {website_url}")
        
        try:
            prompt = self._build_content_ownership_prompt(website_content, website_url)
            response = await sonar_client.generate_response(prompt, pid=pid)
            result = self._parse_content_response(response, pid)
            
            logger.info(f"[PID {pid}] [DomainValidator] Content analysis complete - Owner: {result.get('content_owner', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [DomainValidator] Error in content analysis: {e}")
            return {
                "content_owner": "Unknown",
                "perspective": "unknown",
                "content_confidence": 0,
                "error": f"Content analysis failed: {str(e)}"
            }
    
    async def prevent_misinterpretations(self, analysis: Dict, website_url: str, pid: int = 0) -> Dict[str, Any]:
        """
        Prevent common website↔company misinterpretations.
        
        Args:
            analysis: Current analysis to validate
            website_url: Website URL for context
            pid: Process ID for logging
            
        Returns:
            Misinterpretation prevention result
        """
        logger.info(f"[PID {pid}] [DomainValidator] Checking for misinterpretations in: {website_url}")
        
        try:
            prompt = self._build_misinterpretation_prompt(analysis, website_url)
            response = await sonar_client.generate_response(prompt, pid=pid)
            result = self._parse_misinterpretation_response(response, pid)
            
            logger.info(f"[PID {pid}] [DomainValidator] Misinterpretation check complete - Correct: {result.get('interpretation_correct', False)}")
            return result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [DomainValidator] Error in misinterpretation check: {e}")
            return {
                "interpretation_correct": False,
                "confidence_score": 0,
                "error": f"Misinterpretation check failed: {str(e)}"
            }
    
    def _build_domain_ownership_prompt(self, website_url: str, website_content: Optional[str] = None) -> str:
        """Build domain ownership validation prompt"""
        
        prompt = f"""
        CRITICAL DOMAIN OWNERSHIP ANALYSIS: {website_url}
        
        Your task is to identify the ACTUAL COMPANY that owns and operates this website.
        
        ANALYSIS RULES:
        1. ✅ The target company is the one that OWNS the domain
        2. ✅ The target company is the one that PAYS for this website
        3. ✅ The target company is the one whose BUSINESS is being promoted
        4. ❌ Do NOT analyze companies mentioned as partners/customers
        5. ❌ Do NOT analyze companies in case studies
        6. ❌ Do NOT analyze companies in testimonials
        
        WEBSITE ANALYSIS CHECKLIST:
        - [ ] Who owns this domain? (Check domain registration)
        - [ ] Whose business is being promoted here?
        - [ ] Whose products/services are being sold?
        - [ ] Whose contact information is displayed?
        - [ ] Whose logo/branding is prominent?
        - [ ] Whose "About Us" section is this?
        
        RED FLAGS TO WATCH FOR:
        - Companies mentioned as "partners" or "customers"
        - Case studies about other companies
        - Testimonials from other companies
        - External company logos/mentions
        
        """
        
        if website_content:
            prompt += f"""
        WEBSITE CONTENT:
        {website_content[:2000]}
        """
        
        prompt += """
        Return JSON with:
        {{
            "actual_company_name": "Exact company name",
            "company_business": "What this company actually does",
            "domain_owner": "Who owns this domain",
            "business_focus": "What business is being promoted",
            "ownership_confidence": 1-10,
            "potential_confusions": ["wrong company 1", "wrong company 2"],
            "key_ownership_indicators": ["indicator1", "indicator2"]
        }}
        """
        
        return prompt
    
    def _build_content_ownership_prompt(self, website_content: str, website_url: str) -> str:
        """Build content ownership analysis prompt"""
        
        prompt = f"""
        CONTENT OWNERSHIP ANALYSIS: {website_url}
        
        Website Content: {website_content[:2000]}
        
        Determine WHO this content is actually about:
        
        OWNERSHIP INDICATORS:
        1. **First Person Language**: "We provide..." vs "They provide..."
        2. **Possessive Language**: "Our services" vs "Their services"
        3. **Contact Information**: Whose contact details are shown?
        4. **Company References**: How is the company referred to?
        5. **Action Language**: "We help..." vs "They help..."
        
        CONTENT ANALYSIS:
        - [ ] Is this written FROM the company's perspective?
        - [ ] Is this written ABOUT the company?
        - [ ] Whose products/services are being described?
        - [ ] Whose achievements are being highlighted?
        - [ ] Whose team is being introduced?
        
        CONFUSION DETECTION:
        - [ ] Are other companies mentioned prominently?
        - [ ] Are there case studies about other companies?
        - [ ] Are there partner/customer testimonials?
        - [ ] Is there external company branding?
        
        Return JSON with:
        {{
            "content_owner": "Company this content is about",
            "perspective": "FROM/ABOUT the company",
            "ownership_indicators": ["indicator1", "indicator2"],
            "confusion_sources": ["external company 1", "external company 2"],
            "content_confidence": 1-10
        }}
        """
        
        return prompt
    
    def _build_misinterpretation_prompt(self, analysis: Dict, website_url: str) -> str:
        """Build misinterpretation prevention prompt"""
        
        prompt = f"""
        MISINTERPRETATION PREVENTION CHECK: {website_url}
        
        Current Analysis: {str(analysis)[:1500]}
        
        COMMON MISINTERPRETATIONS TO CHECK:
        
        1. **Partner/Customer Confusion**:
           - ❌ "This company provides logistics services" (when they're a customer)
           - ✅ "This company manufactures equipment for logistics companies"
        
        2. **Case Study Confusion**:
           - ❌ "This company builds software" (when it's a case study)
           - ✅ "This company consults on software implementation"
        
        3. **Industry Confusion**:
           - ❌ "This is a technology company" (when they use technology)
           - ✅ "This is a manufacturing company that uses technology"
        
        4. **Service Confusion**:
           - ❌ "This company transports goods" (when they're the shipper)
           - ✅ "This company manufactures goods that get transported"
        
        VALIDATION QUESTIONS:
        - [ ] Is this analysis about the website OWNER?
        - [ ] Is this analysis about the DOMAIN OWNER?
        - [ ] Is this analysis about the BUSINESS being promoted?
        - [ ] Are we analyzing the right company's products/services?
        - [ ] Are we analyzing the right company's target market?
        
        Return JSON with:
        {{
            "interpretation_correct": true/false,
            "actual_company": "Correct company being analyzed",
            "misinterpretation_detected": "What was misinterpreted",
            "correction_needed": "What needs to be corrected",
            "confidence_score": 1-10
        }}
        """
        
        return prompt
    
    def _parse_domain_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse domain ownership response"""
        return self._parse_json_response(response, pid, "domain")
    
    def _parse_content_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse content ownership response"""
        return self._parse_json_response(response, pid, "content")
    
    def _parse_misinterpretation_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse misinterpretation prevention response"""
        return self._parse_json_response(response, pid, "misinterpretation")
    
    def _parse_json_response(self, response: str, pid: int, response_type: str) -> Dict[str, Any]:
        """Parse JSON response from Sonar"""
        
        if response.startswith("ERROR"):
            logger.error(f"[PID {pid}] [DomainValidator] Sonar {response_type} response error: {response}")
            return {"error": response}
        
        try:
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                logger.warning(f"[PID {pid}] [DomainValidator] No JSON found in {response_type} response: {response}")
                return {"error": f"Could not parse Sonar {response_type} response"}
                
        except json.JSONDecodeError as e:
            logger.error(f"[PID {pid}] [DomainValidator] JSON parse error in {response_type}: {e}")
            return {"error": f"JSON parse error in {response_type}: {str(e)}"} 