"""
Framework Relevance Scorer
Scores framework properties and items for relevance to company profile
"""

import logging
import json
import re
import asyncio
from typing import Dict, List, Any
from app.ai.chatgpt_client import chatgpt_generate

logger = logging.getLogger(__name__)

class FrameworkRelevanceScorer:
    """Scores framework properties for relevance to company profile"""
    
    def __init__(self, company_profile: Dict[str, Any]):
        self.company_profile = company_profile
        self.target_customers = company_profile.get("target_customers", [])
        self.core_business = company_profile.get("core_business", "")
        self.products = company_profile.get("products", "")
        self.industries_served = company_profile.get("industries_served", [])
    
    async def score_property_relevance(self, property_name: str, property_items: List[str], 
                                      industry_name: str) -> Dict[str, Any]:
        """
        Score a framework property for relevance
        
        Returns:
            {
                "property_score": 85,  # Overall property relevance (0-100)
                "item_scores": {
                    "cost efficiency": 95,
                    "customer acquisition cost": 45,
                    ...
                },
                "low_relevance_items": ["customer acquisition cost"],
                "high_relevance_items": ["cost efficiency", "quality metrics"]
            }
        """
        if not property_items:
            return {
                "property_score": 0.0,
                "item_scores": {},
                "low_relevance_items": [],
                "high_relevance_items": [],
                "total_items": 0,
                "scored_items": 0
            }
        
        # Build company context summary
        company_context = self._build_company_context()
        
        # Batch score items to reduce API calls and token usage
        # Score 5-8 items at a time depending on item length
        batch_size = 8 if len(property_items) > 8 else len(property_items)
        item_scores = {}
        
        for batch_start in range(0, len(property_items), batch_size):
            batch_items = property_items[batch_start:batch_start + batch_size]
            
            try:
                # Add delay between batches to avoid rate limiting
                if batch_start > 0:
                    await asyncio.sleep(2.0)  # 2 second delay between batches to avoid 429 errors
                
                # Score batch of items together
                batch_scores = await self._score_items_batch(
                    batch_items, property_name, industry_name, company_context
                )
                item_scores.update(batch_scores)
                
            except Exception as e:
                logger.warning(f"Error scoring batch starting at {batch_start}: {e}")
                # Fallback to rule-based scoring for this batch
                for item in batch_items:
                    item_scores[item] = self._rule_based_score(item, property_name)
                # Add delay even on error
                await asyncio.sleep(0.5)
        
        # Calculate overall property score (weighted average)
        property_score = sum(item_scores.values()) / len(item_scores) if item_scores else 0
        
        # Identify low/high relevance items
        low_relevance = [item for item, score in item_scores.items() if score < 50]
        high_relevance = [item for item, score in item_scores.items() if score >= 80]
        
        return {
            "property_score": round(property_score, 1),
            "item_scores": item_scores,
            "low_relevance_items": low_relevance,
            "high_relevance_items": high_relevance,
            "total_items": len(property_items),
            "scored_items": len(item_scores)
        }
    
    async def _score_items_batch(self, items: List[str], property_name: str, 
                                  industry_name: str, company_context: str) -> Dict[str, float]:
        """
        Score multiple items in one API call to reduce token usage and API calls
        
        Returns: Dict mapping item -> score (0-100)
        """
        try:
            items_list = "\n".join([f"- {item}" for item in items])
            
            # Simplified prompt - no reasoning requested to reduce token usage
            prompt = f"""Score relevance of framework items (0-100 each).

COMPANY: {company_context.strip()}
INDUSTRY: {industry_name}
PROPERTY: {property_name}

ITEMS TO SCORE:
{items_list}

Return ONLY JSON with scores:
{{
    "scores": {{
        "{items[0]}": 85,
        "{items[1] if len(items) > 1 else items[0]}": 90
    }}
}}

Guidelines:
- 90-100: Highly relevant to company/industry
- 70-89: Relevant but generic
- 50-69: Somewhat relevant
- 30-49: Low relevance
- 0-29: Not relevant

Return JSON only, no explanation."""
            
            from app.config import CHATGPT_MAX_TOKENS
            # For batched scoring, need more tokens but still reasonable
            # Estimate: ~100 tokens per item + base prompt
            estimated_tokens = 200 + (len(items) * 100)
            max_tokens_for_batch = min(CHATGPT_MAX_TOKENS, max(2000, estimated_tokens))
            
            response = await chatgpt_generate(
                prompt, 
                temperature=0.2,
                max_tokens=max_tokens_for_batch
            )
            
            # Parse JSON response
            if not response or response.startswith("ERROR:"):
                logger.warning(f"AI returned error response: {response[:100]}")
                return {item: self._rule_based_score(item, property_name) for item in items}
            
            # Extract JSON - try multiple patterns
            json_match = re.search(r'\{[^{}]*"scores"[^{}]*\{[^}]*\}\s*\}', response, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\{.*?"scores".*?\}', response, re.DOTALL)
            
            if json_match:
                try:
                    json_str = json_match.group(0)
                    json_str = json_str.replace("//", "").strip()
                    result = json.loads(json_str)
                    scores = result.get("scores", {})
                    
                    # Validate and return scores
                    item_scores = {}
                    for item in items:
                        score = scores.get(item, None)
                        if score is None:
                            # Try case-insensitive match
                            for key, value in scores.items():
                                if key.lower() == item.lower():
                                    score = value
                                    break
                        
                        if score is not None and isinstance(score, (int, float)) and 0 <= score <= 100:
                            item_scores[item] = float(score)
                        else:
                            item_scores[item] = self._rule_based_score(item, property_name)
                    
                    return item_scores
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"JSON parse error: {e}, response: {response[:300]}")
            
            # Fallback: try to extract individual scores
            item_scores = {}
            for item in items:
                # Try to find score for this item in response
                score_pattern = rf'["\']?{re.escape(item)}["\']?\s*:\s*(\d+)'
                score_match = re.search(score_pattern, response, re.IGNORECASE)
                if score_match:
                    try:
                        score = int(score_match.group(1))
                        if 0 <= score <= 100:
                            item_scores[item] = float(score)
                            continue
                    except ValueError:
                        pass
                
                # Fallback to rule-based
                item_scores[item] = self._rule_based_score(item, property_name)
            
            return item_scores
            
        except Exception as e:
            logger.warning(f"Error in batch scoring: {e}")
            return {item: self._rule_based_score(item, property_name) for item in items}
    
    def _rule_based_score(self, item: str, property_name: str) -> float:
        """
        Fallback rule-based scoring when AI fails
        """
        item_lower = item.lower()
        company_context_lower = (
            self.core_business.lower() + " " + 
            str(self.products).lower() + " " +
            " ".join([str(tc).lower() for tc in self.target_customers])
        )
        
        # Check for keyword matches
        item_words = set(item_lower.split())
        context_words = set(company_context_lower.split())
        common_words = item_words & context_words
        
        if len(common_words) >= 2:
            return 75.0  # Medium-high relevance
        elif len(common_words) >= 1:
            return 60.0  # Medium relevance
        
        # Check for generic terms (low relevance)
        generic_terms = ["general", "common", "standard", "typical", "basic", "generic"]
        if any(term in item_lower for term in generic_terms):
            return 40.0  # Low relevance
        
        return 60.0  # Default medium relevance
    
    def _build_company_context(self) -> str:
        """Build company context summary for scoring"""
        return f"""
Company: {self.company_profile.get('company_name', 'N/A')}
Core Business: {self.core_business}
Products/Services: {self.products}
Target Customers: {', '.join(self.target_customers)}
Industries Served: {', '.join(self.industries_served)}
Business Model: {self.company_profile.get('business_intelligence', {}).get('business_model', 'N/A')}
"""

