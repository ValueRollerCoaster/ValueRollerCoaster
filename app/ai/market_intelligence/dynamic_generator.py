"""
Dynamic Industry Framework Generator
Generates industry frameworks dynamically based on company profile.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .frameworks import get_framework, get_available_frameworks

logger = logging.getLogger(__name__)

class DynamicIndustryFrameworkGenerator:
    """Generates industry frameworks dynamically based on company profile"""
    
    def __init__(self):
        self.company_profile = self._load_company_profile()
        self.framework_cache = {}
        self.last_profile_check = None
    
    def _load_company_profile(self) -> Dict[str, Any]:
        """Load company profile from file"""
        try:
            # Import company profile
            from app.core.company_context_manager import CompanyContextManager
            company_context = CompanyContextManager()
            return company_context.get_company_profile()
        except ImportError as e:
            logger.error(f"Failed to load company profile: {e}")
            return {"industries_served": []}  # Empty fallback - no assumptions
    
    def _check_profile_updated(self) -> bool:
        """Check if company profile has been updated"""
        current_time = datetime.now()
        
        # Check every 5 minutes
        if (self.last_profile_check is None or 
            (current_time - self.last_profile_check).seconds > 300):
            self.last_profile_check = current_time
            return True
        
        return False
    
    def get_company_industries(self) -> List[str]:
        """Get list of industries served by the company"""
        if self._check_profile_updated():
            self.company_profile = self._load_company_profile()
        
        industries = self.company_profile.get("industries_served", [])
        
        # Normalize industry names
        normalized_industries = []
        for industry in industries:
            normalized = industry.lower().replace(" ", "_")
            normalized_industries.append(normalized)
        
        return normalized_industries
    
    def get_framework_for_industry(self, industry_name: str) -> Dict[str, Any]:
        """Get framework for a specific industry"""
        normalized_name = industry_name.lower().replace(" ", "_")
        
        # Check cache first
        if normalized_name in self.framework_cache:
            cached_framework = self.framework_cache[normalized_name]
        else:
            # Reload company profile to ensure we have latest data
            if self._check_profile_updated():
                self.company_profile = self._load_company_profile()
            
            # Get framework instance - pass company profile for generic frameworks
            framework_instance = get_framework(industry_name, self.company_profile)
            framework_data = framework_instance.get_framework_data()
            
            # Cache the base framework (without customizations)
            self.framework_cache[normalized_name] = framework_data
            cached_framework = framework_data
        
        # Always apply customizations (even if from cache) to ensure latest customizations are applied
        try:
            from app.database_framework_customizations import apply_customizations_to_framework
            customized_framework = apply_customizations_to_framework(cached_framework, normalized_name)
            return customized_framework
        except Exception as e:
            logger.warning(f"Could not load framework customizations: {e}")
            return cached_framework
    
    def get_company_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Get frameworks for all company industries"""
        company_industries = self.get_company_industries()
        frameworks = {}
        
        for industry in company_industries:
            frameworks[industry] = self.get_framework_for_industry(industry)
        
        return frameworks
    
    def get_multi_industry_context(self) -> str:
        """Get combined context for all company industries"""
        frameworks = self.get_company_frameworks()
        
        context_parts = []
        context_parts.append("COMPANY INDUSTRIES SERVED:")
        
        for industry_name, framework_data in frameworks.items():
            context_parts.append(f"\n{framework_data['industry_name'].upper()}:")
            context_parts.append(f"  NACE Codes: {', '.join(framework_data['nace_codes'])}")
            context_parts.append(f"  Key Metrics: {', '.join(framework_data['key_metrics'])}")
            context_parts.append(f"  Trend Areas: {', '.join(framework_data['trend_areas'])}")
            context_parts.append(f"  Value Drivers: {', '.join(framework_data['value_drivers'])}")
            context_parts.append(f"  Pain Points: {', '.join(framework_data['pain_points'])}")
            context_parts.append(f"  Technology Focus: {', '.join(framework_data['technology_focus'])}")
            context_parts.append(f"  Sustainability: {', '.join(framework_data['sustainability_initiatives'])}")
        
        return "\n".join(context_parts)
    
    def get_industry_mapping(self) -> Dict[str, str]:
        """Get mapping from normalized names to display names"""
        frameworks = self.get_company_frameworks()
        mapping = {}
        
        for normalized_name, framework_data in frameworks.items():
            mapping[normalized_name] = framework_data['industry_name']
        
        return mapping
    
    def validate_industry_coverage(self) -> Dict[str, Any]:
        """
        Validate that all company industries can have frameworks generated.
        Since frameworks are now dynamic, all industries are supported.
        """
        company_industries = self.get_company_industries()
        
        # All industries are covered since frameworks are dynamic
        coverage = {
            "company_industries": company_industries,
            "available_frameworks": [],  # No predefined frameworks
            "covered_industries": company_industries,  # All industries are covered dynamically
            "missing_industries": [],  # No missing industries
            "coverage_percentage": 100.0 if company_industries else 0.0,
            "framework_type": "dynamic"  # All frameworks are generated dynamically
        }
        
        return coverage
    
    async def get_validated_framework_for_industry(self, industry_name: str, 
                                                validate: bool = True) -> Dict[str, Any]:
        """
        Get framework with optional AI validation
        
        Args:
            industry_name: Industry name
            validate: Whether to run validation (default: True)
        
        Returns:
            Framework data with optional _validation key
        """
        # Get base framework (existing logic)
        framework_data = self.get_framework_for_industry(industry_name)
        
        # Run validation if requested
        if validate:
            try:
                from app.ai.market_intelligence.validation.framework_validator import FrameworkValidator
                
                validator = FrameworkValidator(self.company_profile)
                validation_results = await validator.validate(framework_data, industry_name)
                
                # Attach validation results
                framework_data["_validation"] = validation_results
                
                # Optionally apply high-confidence refinements
                if validation_results.get("ai_validation", {}).get("refinements"):
                    refinements = [
                        r for r in validation_results["ai_validation"]["refinements"]
                        if r.get("confidence", 0) >= 0.90  # Only high confidence
                    ]
                    if refinements:
                        from app.ai.market_intelligence.validation.ai_validator import AIFrameworkValidator
                        ai_validator = AIFrameworkValidator()
                        framework_data = await ai_validator.apply_refinements(framework_data, refinements)
                        
                        # Re-validate after refinements
                        validation_results = await validator.validate(framework_data, industry_name)
                        framework_data["_validation"] = validation_results
                
            except Exception as e:
                logger.warning(f"Validation failed for {industry_name}: {e}")
                # Continue without validation if it fails
                framework_data["_validation"] = {
                    "error": str(e),
                    "overall_quality": 0
                }
        
        return framework_data
    
    async def get_validated_company_frameworks(self, validate: bool = True) -> Dict[str, Dict[str, Any]]:
        """Get all company frameworks with validation"""
        company_industries = self.get_company_industries()
        frameworks = {}
        
        for industry in company_industries:
            frameworks[industry] = await self.get_validated_framework_for_industry(industry, validate)
        
        return frameworks
    
    def get_framework_summary(self) -> Dict[str, Any]:
        """Get summary of all frameworks"""
        frameworks = self.get_company_frameworks()
        coverage = self.validate_industry_coverage()
        
        summary = {
            "total_industries": len(frameworks),
            "coverage_percentage": coverage["coverage_percentage"],
            "industries": {}
        }
        
        for industry_name, framework_data in frameworks.items():
            summary["industries"][industry_name] = {
                "display_name": framework_data["industry_name"],
                "nace_codes": len(framework_data["nace_codes"]),
                "key_metrics": len(framework_data["key_metrics"]),
                "trend_areas": len(framework_data["trend_areas"]),
                "value_drivers": len(framework_data["value_drivers"]),
                "pain_points": len(framework_data["pain_points"])
            }
        
        return summary 