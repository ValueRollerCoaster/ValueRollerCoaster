"""
Relevance Validator
Main logic for validating website relevance to our business.
"""

import logging
from typing import Dict, List, Any, Optional
from .sonar_client import sonar_client
from .company_profile_validator import CompanyProfileValidator

logger = logging.getLogger(__name__)

class RelevanceValidator:
    """Main relevance validation logic"""
    
    def __init__(self):
        self.company_validator = CompanyProfileValidator()
        logger.info("[RelevanceValidator] Initialized with company profile validator")
    
    async def validate_website_relevance(self, website_url: str, website_content: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """
        Main method to validate website relevance.
        
        Args:
            website_url: Target website URL
            website_content: Optional website content
            pid: Process ID for logging
            
        Returns:
            Comprehensive relevance validation result
        """
        logger.info(f"[PID {pid}] [RelevanceValidator] Starting relevance validation for: {website_url}")
        
        try:
            # Step 1: Basic relevance check
            relevance_result = await self.company_validator.validate_relevance(website_url, website_content, pid)
            
            # Step 2: Industry alignment check (if relevant)
            industry_result = None
            if relevance_result.get("is_relevant", False):
                industry_result = await self._check_industry_alignment(website_url, website_content, pid)
            
            # Step 3: Product relevance check (if relevant)
            product_result = None
            if relevance_result.get("is_relevant", False):
                product_result = await self._check_product_relevance(website_url, website_content, pid)
            
            # Step 4: Combine results
            final_result = self._combine_validation_results(relevance_result, industry_result, product_result, pid)
            
            logger.info(f"[PID {pid}] [RelevanceValidator] Validation complete - Relevant: {final_result.get('is_relevant', False)}, Score: {final_result.get('relevance_score', 0)}")
            return final_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [RelevanceValidator] Error in validation: {e}")
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "error": f"Relevance validation failed: {str(e)}",
                "recommended_action": "skip"
            }
    
    async def _check_industry_alignment(self, website_url: str, website_content: Optional[str], pid: int) -> Dict[str, Any]:
        """Check if the company operates in our target industries"""
        
        target_industries = self.company_validator.get_target_industries()
        
        # Build dynamic industry mapping based on target industries
        industry_mapping = self._build_industry_mapping(target_industries)
        
        prompt = f"""
        INDUSTRY ALIGNMENT CHECK: {website_url}
        
        OUR TARGET INDUSTRIES: {', '.join(target_industries) if target_industries else 'Not specified'}
        
        TASK: Determine if this company operates in ANY of our target industries.
        
        INDUSTRY MAPPING:
{industry_mapping}
        
        INDUSTRY INDICATORS:
        - [ ] Operates in one or more of our target industries
        - [ ] Provides products/services relevant to our target industries
        - [ ] Serves customers in our target industries
        - [ ] Uses equipment/products relevant to our target industries
        - [ ] Business model aligns with our target industries
        
        """
        
        if website_content:
            prompt += f"""
        WEBSITE CONTENT:
        {website_content[:1500]}
        """
        
        prompt += """
        Return JSON with:
        {{
            "industry_match": true/false,
            "matched_industries": ["industry1", "industry2"],
            "industry_confidence": 1-10,
            "industry_indicators": ["indicator1", "indicator2"],
            "business_type": "equipment_manufacturer/machinery_producer/etc"
        }}
        """
        
        response = await sonar_client.generate_response(prompt, pid=pid)
        return self._parse_json_response(response, pid)
    
    def _build_industry_mapping(self, target_industries: List[str]) -> str:
        """Build dynamic industry mapping based on target industries"""
        if not target_industries:
            return "        - Industries: Not specified - analyze based on company profile"
        
        # Generic industry descriptions that can apply to any industry
        industry_mapping_lines = []
        for industry in target_industries:
            industry_lower = industry.lower()
            
            # Build industry-specific descriptions based on common patterns
            if any(keyword in industry_lower for keyword in ['manufacturing', 'production', 'factory']):
                description = f"{industry}: Manufacturing processes, production equipment, industrial machinery"
            elif any(keyword in industry_lower for keyword in ['construction', 'building', 'infrastructure']):
                description = f"{industry}: Construction equipment, building machinery, infrastructure projects"
            elif any(keyword in industry_lower for keyword in ['agriculture', 'farming', 'agri']):
                description = f"{industry}: Agricultural equipment, farming machinery, crop production"
            elif any(keyword in industry_lower for keyword in ['mining', 'extraction']):
                description = f"{industry}: Mining equipment, excavation, drilling, extraction machinery"
            elif any(keyword in industry_lower for keyword in ['logistics', 'transport', 'warehouse']):
                description = f"{industry}: Logistics equipment, transportation, warehousing, supply chain"
            elif any(keyword in industry_lower for keyword in ['technology', 'software', 'it', 'saas']):
                description = f"{industry}: Technology solutions, software products, IT services"
            elif any(keyword in industry_lower for keyword in ['healthcare', 'medical', 'health']):
                description = f"{industry}: Healthcare equipment, medical devices, health services"
            elif any(keyword in industry_lower for keyword in ['energy', 'power', 'utilities']):
                description = f"{industry}: Energy equipment, power generation, utility services"
            else:
                # Generic description for industries not matching common patterns
                description = f"{industry}: Products and services relevant to {industry} industry"
            
            industry_mapping_lines.append(f"        - {description}")
        
        return "\n".join(industry_mapping_lines)
    
    async def _check_product_relevance(self, website_url: str, website_content: Optional[str], pid: int) -> Dict[str, Any]:
        """Check if the company could use our products"""
        
        products = self.company_validator.get_products()
        
        # Safety check: if products is empty, return early with neutral result
        if not products:
            logger.debug(f"[PID {pid}] [RelevanceValidator] No products configured, skipping product relevance check")
            return {
                "uses_our_products": False,
                "applicable_products": [],
                "application_areas": [],
                "product_confidence": 0,
                "specific_applications": []
            }
        
        product_categories = [p.get('category', '') if isinstance(p, dict) else str(p) for p in products]
        core_business = self.company_validator.core_business
        
        # Build dynamic product analysis section based on actual products
        product_analysis = ""
        for product in products:
            if isinstance(product, dict):
                category = product.get('category', '')
                features = product.get('features', [])
                product_analysis += f"""
        {category}:
        - [ ] Does this company use or need {category.lower()}?
        - [ ] Would {category.lower()} be relevant to their business operations?
        - [ ] Do they manufacture or use products that could integrate {category.lower()}?
        """
            else:
                product_analysis += f"""
        {str(product)}:
        - [ ] Does this company use or need {str(product).lower()}?
        - [ ] Would {str(product).lower()} be relevant to their business operations?
        """
        
        prompt = f"""
        PRODUCT RELEVANCE CHECK: {website_url}
        
        OUR CORE BUSINESS: {core_business}
        OUR PRODUCTS: {', '.join(product_categories) if product_categories else 'Products and services'}
        
        TASK: Determine if this company could use our products/services.
        
        PRODUCT APPLICATION ANALYSIS:
        {product_analysis}
        
        """
        
        if website_content:
            prompt += f"""
        WEBSITE CONTENT:
        {website_content[:1500]}
        """
        
        prompt += """
        Return JSON with:
        {{
            "uses_our_products": true/false,
            "applicable_products": ["product1", "product2"],
            "application_areas": ["area1", "area2"],
            "product_confidence": 1-10,
            "specific_applications": ["application1", "application2"]
        }}
        """
        
        response = await sonar_client.generate_response(prompt, pid=pid)
        return self._parse_json_response(response, pid)
    
    def _combine_validation_results(self, relevance_result: Dict, industry_result: Optional[Dict] = None, 
                                   product_result: Optional[Dict] = None, pid: int = 0) -> Dict[str, Any]:
        """Combine all validation results into final result"""
        
        # Start with basic relevance result
        final_result = relevance_result.copy()
        
        # If not relevant, return early
        if not relevance_result.get("is_relevant", False):
            return final_result
        
        # Add industry alignment info
        if industry_result:
            final_result["industry_alignment"] = industry_result
            industry_confidence = industry_result.get("industry_confidence", 0)
            final_result["industry_match"] = industry_result.get("industry_match", False)
        else:
            industry_confidence = 0
            final_result["industry_match"] = False
        
        # Add product relevance info
        if product_result:
            final_result["product_relevance"] = product_result
            product_confidence = product_result.get("product_confidence", 0)
            final_result["uses_our_products"] = product_result.get("uses_our_products", False)
        else:
            product_confidence = 0
            final_result["uses_our_products"] = False
        
        # Calculate combined confidence score
        base_score = relevance_result.get("relevance_score", 0)
        combined_score = (base_score + industry_confidence + product_confidence) / 3
        
        final_result["relevance_score"] = round(combined_score, 1)
        final_result["validation_details"] = {
            "base_relevance": base_score,
            "industry_confidence": industry_confidence,
            "product_confidence": product_confidence,
            "combined_score": combined_score
        }
        
        # Determine recommended action
        if combined_score >= 7:
            final_result["recommended_action"] = "proceed"
        elif combined_score >= 4:
            final_result["recommended_action"] = "proceed_with_caution"
        else:
            final_result["recommended_action"] = "skip"
        
        return final_result
    
    def _parse_json_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse JSON response from Sonar"""
        
        if response.startswith("ERROR"):
            logger.error(f"[PID {pid}] [RelevanceValidator] Sonar response error: {response}")
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
                logger.warning(f"[PID {pid}] [RelevanceValidator] No JSON found in response: {response}")
                return {"error": "Could not parse Sonar response"}
                
        except json.JSONDecodeError as e:
            logger.error(f"[PID {pid}] [RelevanceValidator] JSON parse error: {e}")
            return {"error": f"JSON parse error: {str(e)}"}
    
    async def is_sonar_available(self) -> bool:
        """Check if Sonar is available for validation"""
        return await sonar_client.is_available() 