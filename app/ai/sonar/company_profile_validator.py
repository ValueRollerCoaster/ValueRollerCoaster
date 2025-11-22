"""
Company Profile Validator
Integrates with our company profile to validate relevance of target websites.
"""

import logging
from typing import Dict, List, Any, Optional
from .sonar_client import sonar_client

logger = logging.getLogger(__name__)

class CompanyProfileValidator:
    """Validates website relevance against our company profile"""
    
    def __init__(self):
        # Load our company profile
        self._refresh_profile()
        logger.info(f"[CompanyProfileValidator] Loaded profile with {len(self.target_industries)} target industries")
    
    def _refresh_profile(self):
        """Refresh company profile data - useful for runtime updates"""
        self.company_profile = self._load_company_profile()
        # Ensure company_profile is a dict, not a string
        if not isinstance(self.company_profile, dict):
            logger.error(f"[CompanyProfileValidator] Company profile is not a dict! Type: {type(self.company_profile)}")
            self.company_profile = {}
        
        self.target_industries = self.company_profile.get("industries_served", [])
        self.products = self.company_profile.get("products", [])
        # Ensure products is a list and handle both string and dict formats
        if not isinstance(self.products, list):
            # If products is a string, try to convert it to a list
            if isinstance(self.products, str) and self.products.strip():
                # Non-empty string - convert to list with single item
                logger.info(f"[CompanyProfileValidator] Converting products string to list: '{self.products[:50]}...'")
                self.products = [{"category": self.products, "description": self.products}]
            else:
                # Empty string or other type - use empty list
                if self.products:
                    logger.debug(f"[CompanyProfileValidator] Products is not a list (type: {type(self.products)}), converting to empty list")
                self.products = []
        
        self.target_customers = self.company_profile.get("target_customers", [])
        self.core_business = self.company_profile.get("core_business", "")
        
        logger.info(f"[CompanyProfileValidator] Profile refreshed - {len(self.target_industries)} industries, {len(self.products)} products")
    
    def _load_company_profile(self) -> Dict[str, Any]:
        """Load our company profile from the profile file"""
        try:
            from app.core.company_context_manager import CompanyContextManager
            company_context = CompanyContextManager()
            profile = company_context.get_company_profile()
            # Validate that we have a usable profile
            if not profile or not isinstance(profile, dict):
                logger.warning("[CompanyProfileValidator] Company profile is empty or invalid")
                return {}
            return profile
        except ImportError:
            logger.error("[CompanyProfileValidator] Could not import CompanyContextManager - company profile not available")
            return {}
        except Exception as e:
            logger.error(f"[CompanyProfileValidator] Error loading company profile: {e}")
            return {}
    
    def _validate_profile_completeness(self) -> bool:
        """Validate that company profile has minimum required fields for validation"""
        required_fields = ["company_name", "core_business", "target_customers", "industries_served"]
        missing_fields = [field for field in required_fields if not self.company_profile.get(field)]
        
        if missing_fields:
            logger.warning(f"[CompanyProfileValidator] Profile missing required fields: {missing_fields}")
            return False
        
        if not self.target_industries:
            logger.warning("[CompanyProfileValidator] No target industries configured")
            return False
        
        if not self.target_customers:
            logger.warning("[CompanyProfileValidator] No target customers configured")
            return False
        
        return True
    
    async def validate_relevance(self, website_url: str, website_content: Optional[str] = None, pid: int = 0, refresh_profile: bool = False) -> Dict[str, Any]:
        """
        Validate if a website is relevant to our business.
        
        Args:
            website_url: Target website URL
            website_content: Optional website content for analysis
            pid: Process ID for logging
            refresh_profile: Whether to refresh profile data before validation
            
        Returns:
            Relevance validation result
        """
        logger.info(f"[PID {pid}] [CompanyProfileValidator] Validating relevance for: {website_url}")
        
        # Optionally refresh profile for runtime updates
        if refresh_profile:
            self._refresh_profile()
            logger.info(f"[PID {pid}] [CompanyProfileValidator] Profile refreshed before validation")
        
        # Validate profile completeness
        if not self._validate_profile_completeness():
            logger.error(f"[PID {pid}] [CompanyProfileValidator] Company profile incomplete - cannot validate relevance")
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "error": "Company profile is incomplete. Please configure company profile first.",
                "recommended_action": "skip"
            }
        
        try:
            # Extract target domain for search filtering
            target_domain = self._extract_domain_from_url(website_url)
            logger.info(f"[PID {pid}] [CompanyProfileValidator] Target domain: {target_domain}")
            
            # Build relevance validation prompt
            prompt = self._build_relevance_prompt(website_url, website_content)
            
            # Get Sonar response with domain filtering to prevent hallucination
            # Only pass search_domain_filter if target_domain exists
            search_filter: Optional[List[str]] = [target_domain] if target_domain else None
            response = await sonar_client.generate_response(
                prompt=prompt,
                search_domain_filter=search_filter,  # Focus on target website only
                pid=pid
            )
            
            # Parse response
            validation_result = self._parse_relevance_response(response, pid)
            
            # Add domain filtering metadata
            validation_result["target_domain"] = target_domain
            validation_result["search_filtered"] = True
            
            logger.info(f"[PID {pid}] [CompanyProfileValidator] Relevance validation complete: {validation_result.get('is_relevant', False)}")
            return validation_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [CompanyProfileValidator] Error in relevance validation: {e}")
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "error": f"Relevance validation failed: {str(e)}",
                "recommended_action": "skip"
            }
    
    def _build_relevance_prompt(self, website_url: str, website_content: Optional[str] = None) -> str:
        """Build the relevance validation prompt"""
        
        prompt = f"""
        RELEVANCE VALIDATION: {website_url}
        
        OUR COMPANY PROFILE:
        - Company: {self.company_profile.get('company_name', 'Unknown Company')}
        - Core Business: {self.core_business or 'Not specified'}
        - Target Customers: {', '.join(self.target_customers) if self.target_customers else 'Not specified'}
        - Industries Served: {', '.join(self.target_industries) if self.target_industries else 'Not specified'}
        - Products: {', '.join([p.get('category', '') if isinstance(p, dict) else str(p) for p in self.products]) if self.products else 'Not specified'}
        
        TASK: Determine if the company at {website_url} is RELEVANT to our business.
        
        RELEVANCE CRITERIA:
{self._build_relevance_criteria()}
        
        RELEVANCE CHECKLIST:
        - [ ] Does this company use products/services like ours?
        - [ ] Does this company operate in our target industries: {', '.join(self.target_industries) if self.target_industries else 'N/A'}?
        - [ ] Could this company be our customer based on our target customers: {', '.join(self.target_customers) if self.target_customers else 'N/A'}?
{self._build_red_flags()}
        
        """
        
        if website_content:
            prompt += f"""
        WEBSITE CONTENT:
        {website_content[:2000]}  # Limit content length
        """
        
        prompt += """
        Return JSON with:
        {{
            "is_relevant": true/false,
            "relevance_score": 1-10,
            "relevance_type": "direct_customer/oem/distributor/system_integrator/related_industry/not_relevant",
            "business_relationship": "How they relate to our business",
            "why_relevant": "Specific reasons for relevance",
            "why_not_relevant": "Specific reasons for irrelevance",
            "recommended_action": "proceed/redirect/ignore"
        }}
        """
        
        return prompt
    
    def _parse_relevance_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse the Sonar response into structured data"""
        
        if response.startswith("ERROR"):
            logger.error(f"[PID {pid}] [CompanyProfileValidator] Sonar response error: {response}")
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "error": response,
                "recommended_action": "skip"
            }
        
        try:
            # Try to extract JSON from response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                
                # Ensure required fields
                result.setdefault("is_relevant", False)
                result.setdefault("relevance_score", 0)
                result.setdefault("recommended_action", "skip")
                
                return result
            else:
                logger.warning(f"[PID {pid}] [CompanyProfileValidator] No JSON found in response: {response}")
                return {
                    "is_relevant": False,
                    "relevance_score": 0,
                    "error": "Could not parse Sonar response",
                    "recommended_action": "skip"
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"[PID {pid}] [CompanyProfileValidator] JSON parse error: {e}")
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "error": f"JSON parse error: {str(e)}",
                "recommended_action": "skip"
            }
    
    def get_target_industries(self) -> List[str]:
        """Get our target industries"""
        return self.target_industries
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get our products"""
        return self.products
    
    def get_target_customers(self) -> List[str]:
        """Get our target customers"""
        return self.target_customers
    
    def get_current_profile_info(self) -> Dict[str, Any]:
        """Get current profile information for debugging/monitoring"""
        return {
            "company_name": self.company_profile.get("company_name", "Unknown"),
            "target_industries": self.target_industries,
            "product_categories": [p.get("category", "") if isinstance(p, dict) else str(p) for p in self.products],
            "target_customers": self.target_customers,
            "core_business": self.core_business,
            "profile_loaded_at": "Current validation time"
        } 

    def _build_relevance_criteria(self) -> str:
        """Build relevance criteria dynamically from company profile"""
        criteria = []
        criteria_num = 1
        
        # Always include direct customer
        criteria.append(f"        {criteria_num}. ✅ **Direct Customer**: Buys our products/services")
        criteria_num += 1
        
        # Build criteria based on target_customers
        target_customers_lower = [str(c).lower() for c in self.target_customers]
        
        # Check for OEM/Manufacturer
        if any(keyword in target_customers_lower for keyword in ['oem', 'manufacturer', 'manufacturing', 'equipment manufacturer']):
            criteria.append(f"        {criteria_num}. ✅ **OEM/Manufacturer**: Uses our components in their equipment/products")
            criteria_num += 1
        
        # Check for Distributor
        if any(keyword in target_customers_lower for keyword in ['distributor', 'reseller', 'dealer', 'channel partner']):
            criteria.append(f"        {criteria_num}. ✅ **Distributor**: Sells our products")
            criteria_num += 1
        
        # Check for System Integrator
        if any(keyword in target_customers_lower for keyword in ['system integrator', 'integrator', 'solutions provider']):
            criteria.append(f"        {criteria_num}. ✅ **System Integrator**: Integrates our products into systems")
            criteria_num += 1
        
        # Always include related industry
        criteria.append(f"        {criteria_num}. ✅ **Related Industry**: Operates in industries we serve")
        criteria_num += 1
        
        # Always include unrelated business
        criteria.append(f"        {criteria_num}. ❌ **Unrelated Business**: Companies in industries unrelated to our business")
        
        return "\n".join(criteria)
    
    def _build_red_flags(self) -> str:
        """Build red flags dynamically based on company profile"""
        red_flags = []
        
        # Base red flag - always exclude unrelated industries
        if self.target_industries:
            red_flags.append(f"        - Companies in industries NOT in our target industries: {', '.join(self.target_industries)}")
        else:
            red_flags.append("        - Companies in industries unrelated to our business")
        
        # Build industry-specific exclusions
        # Only exclude business types that are clearly not in our target industries
        industries_lower = [str(i).lower() for i in self.target_industries]
        
        # Only suggest generic exclusions if we have specific industries
        if self.target_industries:
            # If we serve software industry, don't exclude software companies
            if not any(keyword in industries_lower for keyword in ['software', 'it', 'technology', 'saas']):
                red_flags.append("        - Software companies (unless they serve our target industries)")
            
            # If we serve retail, don't exclude retail
            if not any(keyword in industries_lower for keyword in ['retail', 'e-commerce', 'commerce']):
                red_flags.append("        - Retail stores (unless they serve our target industries)")
            
            # If we serve consulting/services, don't exclude services
            if not any(keyword in industries_lower for keyword in ['consulting', 'services', 'professional services']):
                red_flags.append("        - Service companies (consulting, marketing, etc.) unless they serve our target industries")
        
        if not red_flags:
            return "        RED FLAGS (NOT RELEVANT):\n        - Companies in industries unrelated to our business"
        
        return "        RED FLAGS (NOT RELEVANT):\n" + "\n".join(red_flags)
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL for search filtering"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"[CompanyProfileValidator] Could not extract domain from {url}: {e}")
            return "" 