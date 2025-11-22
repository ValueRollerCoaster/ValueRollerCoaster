"""
Helper functions for framework display and analysis
"""

from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def get_framework_summary_stats(frameworks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for all frameworks"""
    if not frameworks:
        return {
            "total_industries": 0,
            "avg_metrics": 0,
            "avg_trends": 0,
            "avg_value_drivers": 0,
            "nace_coverage": 0,
            "total_nace_codes": 0
        }
    
    total_industries = len(frameworks)
    total_metrics = 0
    total_trends = 0
    total_value_drivers = 0
    industries_with_nace = 0
    total_nace_codes = 0
    
    for framework_data in frameworks.values():
        total_metrics += len(framework_data.get("key_metrics", []))
        total_trends += len(framework_data.get("trend_areas", []))
        total_value_drivers += len(framework_data.get("value_drivers", []))
        
        nace_codes = framework_data.get("nace_codes", [])
        if nace_codes:
            industries_with_nace += 1
            total_nace_codes += len(nace_codes)
    
    return {
        "total_industries": total_industries,
        "avg_metrics": round(total_metrics / total_industries, 1) if total_industries > 0 else 0,
        "avg_trends": round(total_trends / total_industries, 1) if total_industries > 0 else 0,
        "avg_value_drivers": round(total_value_drivers / total_industries, 1) if total_industries > 0 else 0,
        "nace_coverage": round((industries_with_nace / total_industries) * 100, 1) if total_industries > 0 else 0,
        "total_nace_codes": total_nace_codes
    }

def get_customization_source(property_name: str, framework_data: Dict[str, Any], 
                            company_profile: Dict[str, Any]) -> List[str]:
    """
    Determine the source of customization for a framework property.
    Returns list of source indicators.
    """
    sources = []
    
    # Check if property has NACE-based data
    if property_name in ["trend_areas", "value_drivers"]:
        nace_codes = framework_data.get("nace_codes", [])
        if nace_codes:
            sources.append("📊 NACE")
    
    # Check if property is customized based on company profile
    target_customers = company_profile.get("target_customers", [])
    products = company_profile.get("products", "")
    core_business = company_profile.get("core_business", "")
    industries_served = company_profile.get("industries_served", [])
    
    if property_name == "competitive_factors":
        if target_customers:
            target_lower = [str(tc).lower() for tc in target_customers]
            if any('oem' in tc or 'manufacturer' in tc for tc in target_lower):
                sources.append("🔗 Target Customers")
            if any('distributor' in tc or 'reseller' in tc for tc in target_lower):
                sources.append("🔗 Target Customers")
    
    if property_name == "value_drivers":
        if core_business:
            core_lower = core_business.lower()
            if any(keyword in core_lower for keyword in ['quality', 'reliability', 'innovation', 'cost', 'sustainable']):
                sources.append("🏢 Company Profile")
    
    if property_name == "key_metrics":
        if products:
            sources.append("📦 Products")
    
    if property_name == "pain_points":
        if industries_served:
            sources.append("🏭 Industries Served")
    
    if property_name == "technology_focus":
        if core_business:
            core_lower = core_business.lower()
            if any(keyword in core_lower for keyword in ['manufacturing', 'production', 'software', 'technology']):
                sources.append("🏢 Company Profile")
    
    # If no specific sources, it's base/default
    if not sources:
        sources.append("⚪ Base")
    
    return sources

def format_framework_context_for_display(framework_data: Dict[str, Any]) -> str:
    """Format framework data as it would appear in a prompt"""
    lines = []
    lines.append(f"INDUSTRY: {framework_data.get('industry_name', 'N/A')}")
    lines.append(f"NACE CODES: {', '.join(framework_data.get('nace_codes', []))}")
    lines.append(f"KEY METRICS: {', '.join(framework_data.get('key_metrics', []))}")
    lines.append(f"TREND AREAS: {', '.join(framework_data.get('trend_areas', []))}")
    lines.append(f"COMPETITIVE FACTORS: {', '.join(framework_data.get('competitive_factors', []))}")
    lines.append(f"VALUE DRIVERS: {', '.join(framework_data.get('value_drivers', []))}")
    lines.append(f"PAIN POINTS: {', '.join(framework_data.get('pain_points', []))}")
    lines.append(f"TECHNOLOGY FOCUS: {', '.join(framework_data.get('technology_focus', []))}")
    lines.append(f"SUSTAINABILITY: {', '.join(framework_data.get('sustainability_initiatives', []))}")
    return "\n".join(lines)

def estimate_prompt_tokens(text: str) -> int:
    """Rough estimate of token count (1 token ≈ 4 characters)"""
    return len(text) // 4

