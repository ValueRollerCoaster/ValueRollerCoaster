"""
Dynamic Industry Framework
Generates industry frameworks dynamically based on company profile and NACE system.
Always uses company profile data - no hardcoded industry assumptions.
"""

from typing import List, Dict, Any, Optional
from .base_framework import BaseIndustryFramework

class DynamicIndustryFramework(BaseIndustryFramework):
    """Dynamic industry framework that adapts to any industry using company profile and NACE system"""
    
    def __init__(self, industry_name: str, company_profile: Optional[Dict[str, Any]] = None):
        """
        Initialize dynamic framework for an industry
        
        Args:
            industry_name: Name of the industry
            company_profile: Company profile data for context
        """
        self._industry_name = industry_name
        self._company_profile = company_profile or {}
        self._target_customers = self._company_profile.get("target_customers", [])
        self._core_business = self._company_profile.get("core_business", "")
        self._products = self._company_profile.get("products", [])
        self._industries_served = self._company_profile.get("industries_served", [])
        
        # Initialize NACE system for industry-specific data
        try:
            from app.nace_system import NACE_System
            self._nace_system = NACE_System()
            
            # Detect NACE code for this industry
            nace_result = self._nace_system.detect_industry_nace(industry_name)
            self._nace_code = nace_result.get("nace_code")
            self._nace_insights = self._nace_system.get_industry_insights(self._nace_code) if self._nace_code else {}
        except Exception:
            self._nace_system = None
            self._nace_code = None
            self._nace_insights = {}
    
    @property
    def industry_name(self) -> str:
        """Return the industry name"""
        return self._industry_name.title() if self._industry_name else "Industry"
    
    @property
    def nace_codes(self) -> List[str]:
        """Get NACE codes for this industry using NACE system"""
        if self._nace_code and self._nace_system:
            # Get related NACE codes
            try:
                related = self._nace_system.get_related_nace_codes(self._nace_code)
                return [self._nace_code] + related
            except Exception:
                return [self._nace_code] if self._nace_code else []
        return [self._nace_code] if self._nace_code else []
    
    @property
    def key_metrics(self) -> List[str]:
        """Generate key metrics based on company profile and industry"""
        # Base metrics applicable to all industries
        base_metrics = [
            "operational efficiency",
            "cost management",
            "quality standards",
            "customer satisfaction",
            "revenue growth",
            "market share",
            "innovation capability",
            "sustainability performance"
        ]
        
        # Enhance with industry-specific metrics from NACE insights if available
        if self._nace_insights and self._nace_insights.get("insights"):
            # Add industry-specific insights as potential metrics
            pass  # NACE insights are used elsewhere
        
        # Customize based on company profile products/services
        if self._products:
            # If company has specific products, add product-related metrics
            if isinstance(self._products, list):
                product_categories = [p.get('category', '') if isinstance(p, dict) else str(p) for p in self._products]
                if product_categories:
                    base_metrics.insert(0, f"{', '.join(product_categories[:2])} performance")
        
        return base_metrics
    
    @property
    def trend_areas(self) -> List[str]:
        """Generate trend areas from NACE insights and company profile"""
        # Start with NACE system trends if available
        trends = []
        
        if self._nace_insights and self._nace_insights.get("trends"):
            trends.extend(self._nace_insights["trends"])
        
        # Add generic trends if not enough from NACE
        generic_trends = [
            "digital transformation",
            "sustainability initiatives",
            "cost optimization",
            "innovation and technology",
            "market expansion",
            "customer experience",
            "regulatory compliance",
            "operational excellence"
        ]
        
        # Combine and deduplicate
        all_trends = trends + generic_trends
        seen = set()
        unique_trends = []
        for trend in all_trends:
            trend_lower = trend.lower()
            if trend_lower not in seen:
                seen.add(trend_lower)
                unique_trends.append(trend)
        
        return unique_trends[:8]  # Limit to 8 most relevant
    
    @property
    def competitive_factors(self) -> List[str]:
        """Generate competitive factors based on company profile"""
        factors = [
            "cost efficiency",
            "quality and reliability",
            "innovation capability",
            "customer service",
            "market positioning",
            "technical expertise",
            "delivery speed",
            "value proposition"
        ]
        
        # Customize based on target customers
        if self._target_customers:
            target_lower = [str(tc).lower() for tc in self._target_customers]
            if any('oem' in tc or 'manufacturer' in tc for tc in target_lower):
                factors.insert(0, "technical integration capability")
            if any('distributor' in tc or 'reseller' in tc for tc in target_lower):
                factors.insert(0, "channel partner support")
        
        return factors
    
    @property
    def value_drivers(self) -> List[str]:
        """Generate value drivers from company profile and NACE insights"""
        drivers = []
        
        # Use core business to inform value drivers
        if self._core_business:
            # Add business-specific drivers
            core_lower = self._core_business.lower()
            if any(keyword in core_lower for keyword in ['quality', 'reliability', 'durability']):
                drivers.append("quality and reliability")
            if any(keyword in core_lower for keyword in ['innovation', 'technology', 'advanced']):
                drivers.append("innovation and technology")
            if any(keyword in core_lower for keyword in ['cost', 'efficiency', 'affordable']):
                drivers.append("cost optimization")
            if any(keyword in core_lower for keyword in ['sustainable', 'green', 'environmental']):
                drivers.append("sustainability")
        
        # Add from NACE opportunities if available
        if self._nace_insights and self._nace_insights.get("opportunities"):
            drivers.extend(self._nace_insights["opportunities"][:3])  # Top 3 opportunities
        
        # Add generic drivers
        generic_drivers = [
            "operational efficiency",
            "customer satisfaction",
            "technical expertise",
            "value delivery",
            "customization",
            "support and service"
        ]
        
        # Combine and deduplicate
        all_drivers = drivers + generic_drivers
        seen = set()
        unique_drivers = []
        for driver in all_drivers:
            driver_lower = driver.lower()
            if driver_lower not in seen:
                seen.add(driver_lower)
                unique_drivers.append(driver)
        
        return unique_drivers[:8]  # Limit to 8 most relevant
    
    @property
    def pain_points(self) -> List[str]:
        """Generate pain points from company profile context"""
        pain_points = [
            "cost pressure and margin compression",
            "market competition",
            "regulatory compliance",
            "technology adoption",
            "skills and talent gap",
            "supply chain challenges",
            "customer expectations",
            "sustainability requirements"
        ]
        
        # Customize based on industries served
        if self._industries_served:
            industries_lower = [str(ind).lower() for ind in self._industries_served]
            if any('manufacturing' in ind or 'production' in ind for ind in industries_lower):
                pain_points.insert(0, "supply chain disruptions")
            if any('construction' in ind or 'building' in ind for ind in industries_lower):
                pain_points.insert(0, "project delays and cost overruns")
            if any('technology' in ind or 'software' in ind for ind in industries_lower):
                pain_points.insert(0, "rapid technology change")
        
        return pain_points
    
    @property
    def technology_focus(self) -> List[str]:
        """Generate technology focus areas based on industry and company profile"""
        tech_focus = [
            "digital transformation",
            "automation",
            "data analytics",
            "AI and machine learning",
            "cloud computing",
            "IoT integration",
            "cybersecurity",
            "process optimization"
        ]
        
        # Customize based on core business
        if self._core_business:
            core_lower = self._core_business.lower()
            if any(keyword in core_lower for keyword in ['manufacturing', 'production']):
                tech_focus.insert(0, "Industry 4.0")
                tech_focus.insert(1, "predictive maintenance")
            if any(keyword in core_lower for keyword in ['software', 'technology', 'digital']):
                tech_focus.insert(0, "cloud-native architecture")
                tech_focus.insert(1, "API integration")
        
        return tech_focus
    
    @property
    def sustainability_initiatives(self) -> List[str]:
        """Generate sustainability initiatives"""
        initiatives = [
            "energy efficiency",
            "waste reduction",
            "carbon footprint reduction",
            "sustainable practices",
            "ESG compliance",
            "resource optimization",
            "environmental responsibility",
            "sustainable supply chain"
        ]
        
        # Add from NACE insights if available
        if self._nace_insights:
            # NACE insights may contain sustainability-related information
            pass
        
        return initiatives
