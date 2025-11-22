"""
Framework Validator Orchestrator
Coordinates all validation components
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from .relevance_scorer import FrameworkRelevanceScorer
from .completeness_validator import FrameworkCompletenessValidator
from .consistency_validator import FrameworkConsistencyValidator
from .ai_validator import AIFrameworkValidator

logger = logging.getLogger(__name__)

class FrameworkValidator:
    """Orchestrates all framework validation"""
    
    def __init__(self, company_profile: Dict[str, Any]):
        self.company_profile = company_profile
        self.relevance_scorer = FrameworkRelevanceScorer(company_profile)
        self.completeness_validator = FrameworkCompletenessValidator()
        self.consistency_validator = FrameworkConsistencyValidator()
        self.ai_validator = AIFrameworkValidator()
    
    async def validate(self, framework_data: Dict[str, Any], 
                      industry_name: str) -> Dict[str, Any]:
        """
        Run all validation checks
        
        Returns comprehensive validation report
        """
        validation_results = {
            "industry_name": industry_name,
            "validation_timestamp": datetime.now().isoformat(),
            "overall_quality": 0.0
        }
        
        # 1. Relevance Scoring (with rate limiting)
        try:
            relevance_results = {}
            properties_to_score = [
                "key_metrics", "trend_areas", "competitive_factors",
                "value_drivers", "pain_points", "technology_focus",
                "sustainability_initiatives"
            ]
            
            for idx, prop_name in enumerate(properties_to_score):
                prop_items = framework_data.get(prop_name, [])
                if prop_items:
                    # Add delay between properties to avoid rate limiting
                    if idx > 0:
                        await asyncio.sleep(2.0)  # 2 second delay between properties to avoid 429 errors
                    
                    try:
                        score_result = await self.relevance_scorer.score_property_relevance(
                            prop_name, prop_items, industry_name
                        )
                        relevance_results[prop_name] = score_result
                    except Exception as e:
                        logger.warning(f"Error scoring property '{prop_name}': {e}")
                        # Continue with other properties even if one fails
                        relevance_results[prop_name] = {
                            "property_score": 0,
                            "error": str(e)
                        }
            
            validation_results["relevance"] = relevance_results
            
        except Exception as e:
            logger.error(f"Error in relevance scoring: {e}")
            validation_results["relevance"] = {"error": str(e)}
        
        # Add delay before next validation step
        await asyncio.sleep(2.0)  # Longer delay to avoid rate limiting
        
        # 2. Completeness Checks
        try:
            completeness_result = await self.completeness_validator.validate_completeness(
                framework_data, industry_name
            )
            validation_results["completeness"] = completeness_result
        except Exception as e:
            logger.error(f"Error in completeness validation: {e}")
            validation_results["completeness"] = {"error": str(e)}
        
        # Add delay before next validation step
        await asyncio.sleep(2.0)  # Longer delay to avoid rate limiting
        
        # 3. Consistency Validation (no API calls, fast)
        try:
            consistency_result = self.consistency_validator.validate_consistency(framework_data)
            validation_results["consistency"] = consistency_result
        except Exception as e:
            logger.error(f"Error in consistency validation: {e}")
            validation_results["consistency"] = {"error": str(e)}
        
        # Add delay before AI validation
        await asyncio.sleep(3.0)  # Longer delay before final validation step
        
        # 4. AI Validation Layer
        try:
            ai_result = await self.ai_validator.validate_framework(
                framework_data, self.company_profile, industry_name
            )
            validation_results["ai_validation"] = ai_result
        except Exception as e:
            logger.error(f"Error in AI validation: {e}")
            validation_results["ai_validation"] = {"error": str(e)}
        
        # Calculate overall quality score
        validation_results["overall_quality"] = self._calculate_overall_quality(validation_results)
        
        return validation_results
    
    def _calculate_overall_quality(self, results: Dict[str, Any]) -> float:
        """Calculate weighted overall quality score"""
        scores = []
        weights = []
        
        # Relevance (30% weight)
        if "relevance" in results and isinstance(results["relevance"], dict):
            relevance_scores = [
                r["property_score"] 
                for r in results["relevance"].values() 
                if isinstance(r, dict) and "property_score" in r
            ]
            if relevance_scores:
                scores.append(sum(relevance_scores) / len(relevance_scores))
                weights.append(0.3)
        
        # Completeness (25% weight)
        if "completeness" in results and isinstance(results["completeness"], dict):
            comp_score = results["completeness"].get("completeness_score", 0)
            if comp_score > 0:
                scores.append(comp_score)
                weights.append(0.25)
        
        # Consistency (25% weight)
        if "consistency" in results and isinstance(results["consistency"], dict):
            cons_score = results["consistency"].get("consistency_score", 0)
            if cons_score > 0:
                scores.append(cons_score)
                weights.append(0.25)
        
        # AI Validation (20% weight)
        if "ai_validation" in results and isinstance(results["ai_validation"], dict):
            ai_score = results["ai_validation"].get("overall_quality", 0)
            if ai_score > 0:
                scores.append(ai_score)
                weights.append(0.2)
        
        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            return round(weighted_sum / total_weight, 1)
        
        return 0.0

