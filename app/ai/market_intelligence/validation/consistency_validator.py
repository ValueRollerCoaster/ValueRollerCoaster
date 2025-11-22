"""
Framework Consistency Validator
Checks for logical consistency within and across frameworks
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class FrameworkConsistencyValidator:
    """Validates framework consistency"""
    
    def validate_consistency(self, framework_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate internal consistency of a framework
        
        Returns:
            {
                "consistency_score": 95.0,  # 0-100
                "issues": [
                    {
                        "rule": "pain_point_value_driver_alignment",
                        "severity": "medium",
                        "description": "Pain point 'high costs' not addressed in value drivers",
                        "suggestion": "Add 'cost efficiency' to value drivers"
                    }
                ],
                "rule_results": {...}
            }
        """
        issues = []
        rule_results = {}
        
        # Run consistency rules
        rule_results["pain_point_value_driver_alignment"] = self._check_pain_value_alignment(framework_data)
        rule_results["trend_technology_alignment"] = self._check_trend_tech_alignment(framework_data)
        rule_results["sustainability_cross_property"] = self._check_sustainability_consistency(framework_data)
        
        # Collect issues
        for rule_name, result in rule_results.items():
            if not result.get("passed", False):
                issues.append({
                    "rule": rule_name,
                    "severity": result.get("severity", "medium"),
                    "description": result.get("description", ""),
                    "suggestion": result.get("suggestion", "")
                })
        
        # Calculate consistency score
        total_rules = len(rule_results)
        passed_rules = sum(1 for r in rule_results.values() if r.get("passed", False))
        consistency_score = (passed_rules / total_rules * 100) if total_rules > 0 else 0
        
        return {
            "consistency_score": round(consistency_score, 1),
            "issues": issues,
            "rule_results": rule_results,
            "total_rules": total_rules,
            "passed_rules": passed_rules
        }
    
    def _check_pain_value_alignment(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        """Check if pain points are addressed in value drivers"""
        pain_points = [p.lower() for p in framework.get("pain_points", [])]
        value_drivers = [v.lower() for v in framework.get("value_drivers", [])]
        
        issues = []
        
        # Check for common pain points that should have corresponding value drivers
        pain_value_mapping = {
            "cost": ["cost", "efficiency", "optimization", "reduction"],
            "quality": ["quality", "reliability", "standards"],
            "time": ["speed", "efficiency", "time", "delivery"],
            "compliance": ["compliance", "regulatory", "standards"],
            "technology": ["technology", "digital", "automation", "innovation"]
        }
        
        for pain_point in pain_points:
            # Find matching category
            matched = False
            for category, keywords in pain_value_mapping.items():
                if any(kw in pain_point for kw in [category] + keywords[:1]):
                    # Check if value drivers address this
                    if any(kw in vd for vd in value_drivers for kw in keywords):
                        matched = True
                        break
            
            if not matched:
                issues.append({
                    "pain_point": pain_point,
                    "suggestion": f"Add corresponding value driver for '{pain_point}'"
                })
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "description": f"Found {len(issues)} unaddressed pain points" if issues else "All pain points addressed"
        }
    
    def _check_trend_tech_alignment(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        """Check if trends align with technology focus"""
        trends = [t.lower() for t in framework.get("trend_areas", [])]
        tech_focus = [tf.lower() for tf in framework.get("technology_focus", [])]
        
        tech_trends = [t for t in trends if any(kw in t for kw in ["digital", "tech", "ai", "automation", "iot", "cloud"])]
        
        if tech_trends and not tech_focus:
            return {
                "passed": False,
                "description": "Technology trends present but no technology focus",
                "suggestion": "Add technology focus areas"
            }
        
        return {"passed": True, "description": "Trends and technology focus aligned"}
    
    def _check_sustainability_consistency(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        """Check sustainability consistency across properties"""
        sustainability_items = framework.get("sustainability_initiatives", [])
        
        if not sustainability_items:
            return {"passed": True, "description": "No sustainability items to check"}
        
        # Check if sustainability appears in other properties
        value_drivers = [v.lower() for v in framework.get("value_drivers", [])]
        trend_areas = [t.lower() for t in framework.get("trend_areas", [])]
        
        has_sustainability_in_others = (
            any("sustain" in vd or "green" in vd or "environment" in vd for vd in value_drivers) or
            any("sustain" in ta or "green" in ta or "environment" in ta for ta in trend_areas)
        )
        
        if sustainability_items and not has_sustainability_in_others:
            return {
                "passed": False,
                "description": "Sustainability initiatives not reflected in value drivers or trends",
                "suggestion": "Add sustainability to value drivers or trend areas"
            }
        
        return {"passed": True, "description": "Sustainability consistent across properties"}

