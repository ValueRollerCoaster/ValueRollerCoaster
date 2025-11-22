import json
import time
from typing import Dict, Any, List

class UniversalCompanyContextExtractor:
    """Dynamically extracts company context based on actual profile data"""
    
    def __init__(self):
        self.company_profile = self._load_company_profile()
        self.context_cache = {}
    
    def _load_company_profile(self):
        """Load company profile dynamically"""
        try:
            from app.core.company_context_manager import CompanyContextManager
            company_context = CompanyContextManager()
            return company_context.get_company_profile()
        except ImportError:
            return {}
    
    def extract_field_specific_context(self, field_name: str, main_category: str, subcategory: str) -> Dict[str, Any]:
        """Extract context specific to field, adapting to actual company data"""
        
        cache_key = f"{field_name}_{main_category}_{subcategory}"
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]
        
        context = {
            "company_basics": self._extract_company_basics(),
            "business_context": self._extract_business_context(main_category, subcategory),
            "industry_context": self._extract_industry_context(),
            "capability_context": self._extract_capability_context(field_name),
            "value_context": self._extract_value_context(field_name),
            "field_specific": self._extract_field_specific_context(field_name, main_category, subcategory)
        }
        
        self.context_cache[cache_key] = context
        return context
    
    def _extract_company_basics(self) -> Dict[str, str]:
        """Extract basic company information"""
        basics = {}
        
        # Core company info
        if "company_name" in self.company_profile:
            basics["name"] = self.company_profile["company_name"]
        if "core_business" in self.company_profile:
            basics["core_business"] = self.company_profile["core_business"]
        if "vision" in self.company_profile:
            basics["vision"] = self.company_profile["vision"]
        if "location" in self.company_profile:
            basics["location"] = self.company_profile["location"]
        
        return basics
    
    def _extract_business_context(self, main_category: str, subcategory: str) -> Dict[str, Any]:
        """Extract business intelligence context"""
        business_context = {}
        
        if "business_intelligence" in self.company_profile:
            bi = self.company_profile["business_intelligence"]
            
            # Universal business attributes
            business_context["company_type"] = bi.get("company_type", "Unknown")
            business_context["business_model"] = bi.get("business_model", "Unknown")
            business_context["market_position"] = bi.get("market_position", "Unknown")
            business_context["industry_focus"] = bi.get("industry_focus", "Unknown")
            business_context["customer_relationship"] = bi.get("customer_relationship_type", "Unknown")
            business_context["innovation_focus"] = bi.get("innovation_focus", "Unknown")
            
            # Category-specific business context
            if main_category == "Technical Value":
                business_context["technical_focus"] = bi.get("innovation_focus", "Unknown")
            elif main_category == "Business Value":
                business_context["value_delivery"] = bi.get("value_delivery_method", "Unknown")
            elif main_category == "Strategic Value":
                business_context["competitive_advantage"] = bi.get("competitive_advantage_type", "Unknown")
        
        return business_context
    
    def _extract_industry_context(self) -> Dict[str, Any]:
        """Extract industry and market context"""
        industry_context = {}
        
        # Industries served
        if "industries_served" in self.company_profile:
            industry_context["target_industries"] = self.company_profile["industries_served"]
        
        # Target customers
        if "target_customers" in self.company_profile:
            industry_context["target_customers"] = self.company_profile["target_customers"]
        
        # Products/services
        if "products" in self.company_profile:
            industry_context["products"] = self.company_profile["products"]
        
        # Adaptability context
        if "adaptability" in self.company_profile:
            adaptability = self.company_profile["adaptability"]
            if "industry_adaptability" in adaptability:
                industry_context["industry_expertise"] = adaptability["industry_adaptability"].get("industry_expertise", [])
                industry_context["application_flexibility"] = adaptability["industry_adaptability"].get("application_flexibility", "Unknown")
        
        return industry_context
    
    def _extract_capability_context(self, field_name: str) -> Dict[str, Any]:
        """Extract capability context relevant to field"""
        capability_context = {}
        
        if "capabilities" in self.company_profile:
            capabilities = self.company_profile["capabilities"]
            
            # Core capabilities
            if "core_capabilities" in capabilities:
                capability_context["core_capabilities"] = capabilities["core_capabilities"]
            
            # Technical expertise
            if "technical_expertise" in capabilities:
                capability_context["technical_expertise"] = capabilities["technical_expertise"]
            
            # Operational strengths
            if "operational_strengths" in capabilities:
                capability_context["operational_strengths"] = capabilities["operational_strengths"]
            
            # Differentiation factors
            if "differentiation_factors" in capabilities:
                capability_context["differentiation_factors"] = capabilities["differentiation_factors"]
        
        return capability_context
    
    def _extract_value_context(self, field_name: str) -> Dict[str, Any]:
        """Extract value delivery context"""
        value_context = {}
        
        if "value_delivery" in self.company_profile:
            value_delivery = self.company_profile["value_delivery"]
            
            # Primary value proposition
            if "primary_value_proposition" in value_delivery:
                value_context["primary_value"] = value_delivery["primary_value_proposition"]
            
            # Value delivery channels
            if "value_delivery_channels" in value_delivery:
                value_context["delivery_channels"] = value_delivery["value_delivery_channels"]
            
            # Success patterns
            if "success_patterns" in value_delivery:
                value_context["success_patterns"] = value_delivery["success_patterns"]
            
            # Customer outcomes
            if "customer_outcomes" in value_delivery:
                value_context["customer_outcomes"] = value_delivery["customer_outcomes"]
        
        return value_context
    
    def _extract_field_specific_context(self, field_name: str, main_category: str, subcategory: str) -> Dict[str, Any]:
        """Extract context specific to the field type"""
        field_context = {}
        
        # Field-specific expectations based on category
        if main_category == "Technical Value":
            field_context["expectation_type"] = "technical_benefits"
            field_context["focus_areas"] = ["performance", "quality", "innovation", "sustainability"]
            
        elif main_category == "Business Value":
            field_context["expectation_type"] = "business_benefits"
            field_context["focus_areas"] = ["cost_savings", "revenue_growth", "efficiency", "productivity"]
            
        elif main_category == "Strategic Value":
            field_context["expectation_type"] = "strategic_benefits"
            field_context["focus_areas"] = ["competitive_advantage", "risk_mitigation", "market_position", "long_term_value"]
            
        elif main_category == "After Sales Value":
            field_context["expectation_type"] = "service_benefits"
            field_context["focus_areas"] = ["support", "maintenance", "training", "consulting"]
        
        # Subcategory-specific context
        field_context["subcategory_focus"] = subcategory.lower()
        
        return field_context
