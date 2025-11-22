"""
Framework Completeness Validator
Ensures frameworks include all critical industry elements

Uses ChatGPT (gpt-4o-mini) for benchmark generation with better rate limits
and reliability compared to Gemini.
"""

import logging
from typing import Dict, List, Any
from app.ai.chatgpt_client import chatgpt_generate
import json
import re

logger = logging.getLogger(__name__)

class FrameworkCompletenessValidator:
    """Validates framework completeness against industry benchmarks"""
    
    # Industry benchmark templates (can be AI-generated or hardcoded)
    INDUSTRY_BENCHMARKS = {
        "manufacturing": {
            "key_metrics": {
                "required": ["cost efficiency", "quality metrics", "production efficiency"],
                "recommended": ["throughput", "downtime", "yield", "waste reduction"]
            },
            "trend_areas": {
                "required": ["automation", "digitalization", "sustainability"],
                "recommended": ["Industry 4.0", "supply chain resilience", "circular economy"]
            },
            "value_drivers": {
                "required": ["operational efficiency", "quality", "cost optimization"],
                "recommended": ["innovation", "customization", "sustainability"]
            },
            "pain_points": {
                "required": ["cost pressure", "supply chain challenges"],
                "recommended": ["skills gap", "technology adoption", "regulatory compliance"]
            }
        },
        "mining": {
            "key_metrics": {
                "required": ["safety metrics", "resource extraction efficiency", "environmental compliance"],
                "recommended": ["cost per ton", "equipment utilization", "waste management"]
            },
            "trend_areas": {
                "required": ["safety", "environmental compliance", "automation"],
                "recommended": ["green mining", "digital transformation", "sustainability"]
            },
            "value_drivers": {
                "required": ["safety", "efficiency", "compliance"],
                "recommended": ["sustainability", "innovation", "cost optimization"]
            },
            "pain_points": {
                "required": ["safety", "environmental regulations", "cost pressure"],
                "recommended": ["skills gap", "technology adoption", "market volatility"]
            }
        }
    }
    
    async def validate_completeness(self, framework_data: Dict[str, Any], 
                                   industry_name: str) -> Dict[str, Any]:
        """
        Validate framework completeness
        
        Returns:
            {
                "completeness_score": 82.5,  # 0-100
                "missing_critical": ["safety metrics", "environmental compliance"],
                "missing_recommended": ["Industry 4.0", "supply chain resilience"],
                "property_completeness": {
                    "key_metrics": {"score": 75, "missing": ["safety metrics"]},
                    ...
                }
            }
        """
        # Get or generate industry benchmark
        benchmark = await self._get_industry_benchmark(industry_name)
        
        if not benchmark:
            return {
                "completeness_score": 0.0,
                "error": "No benchmark available for this industry",
                "missing_critical": [],
                "missing_recommended": [],
                "property_completeness": {}
            }
        
        # Check each property
        property_completeness = {}
        all_missing_critical = []
        all_missing_recommended = []
        
        for prop_name, prop_items in framework_data.items():
            if prop_name in ["industry_name", "nace_codes", "_validation"]:
                continue
            
            if prop_name in benchmark:
                result = self._check_property_completeness(
                    prop_items, benchmark[prop_name]
                )
                property_completeness[prop_name] = result
                all_missing_critical.extend(result["missing_critical"])
                all_missing_recommended.extend(result["missing_recommended"])
        
        # Calculate overall completeness
        if property_completeness:
            avg_score = sum(r["score"] for r in property_completeness.values()) / len(property_completeness)
        else:
            avg_score = 0.0
        
        return {
            "completeness_score": round(avg_score, 1),
            "missing_critical": list(set(all_missing_critical)),
            "missing_recommended": list(set(all_missing_recommended)),
            "property_completeness": property_completeness
        }
    
    def _check_property_completeness(self, framework_items: List[str], 
                                    benchmark: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Check if property has all required/recommended items
        
        Returns:
            {
                "score": 75,  # 0-100
                "missing_critical": [...],
                "missing_recommended": [...],
                "present_critical": [...],
                "present_recommended": [...]
            }
        """
        framework_items_lower = [item.lower() for item in framework_items]
        
        required = benchmark.get("required", [])
        recommended = benchmark.get("recommended", [])
        
        # Check for required items (fuzzy matching)
        present_critical = []
        missing_critical = []
        
        for req_item in required:
            if self._fuzzy_match(req_item, framework_items_lower):
                present_critical.append(req_item)
            else:
                missing_critical.append(req_item)
        
        # Check for recommended items
        present_recommended = []
        missing_recommended = []
        
        for rec_item in recommended:
            if self._fuzzy_match(rec_item, framework_items_lower):
                present_recommended.append(rec_item)
            else:
                missing_recommended.append(rec_item)
        
        # Calculate score
        # Required items weighted 70%, recommended 30%
        required_score = (len(present_critical) / len(required) * 100) if required else 100
        recommended_score = (len(present_recommended) / len(recommended) * 100) if recommended else 100
        
        total_score = (required_score * 0.7) + (recommended_score * 0.3)
        
        return {
            "score": round(total_score, 1),
            "missing_critical": missing_critical,
            "missing_recommended": missing_recommended,
            "present_critical": present_critical,
            "present_recommended": present_recommended
        }
    
    def _fuzzy_match(self, benchmark_item: str, framework_items: List[str]) -> bool:
        """Fuzzy match benchmark item against framework items"""
        benchmark_lower = benchmark_item.lower()
        
        # Exact match
        if benchmark_lower in framework_items:
            return True
        
        # Partial match (benchmark item contains or is contained in framework item)
        for fw_item in framework_items:
            if benchmark_lower in fw_item or fw_item in benchmark_lower:
                return True
        
        # Keyword match (check if key words match)
        benchmark_words = set(benchmark_lower.split())
        for fw_item in framework_items:
            fw_words = set(fw_item.split())
            if len(benchmark_words & fw_words) >= len(benchmark_words) * 0.6:  # 60% word overlap
                return True
        
        return False
    
    async def _get_industry_benchmark(self, industry_name: str) -> Dict[str, Any]:
        """
        Get industry benchmark (from cache or generate with AI)
        """
        industry_lower = industry_name.lower()
        
        # Check hardcoded benchmarks first
        for key, benchmark in self.INDUSTRY_BENCHMARKS.items():
            if key in industry_lower or industry_lower in key:
                return benchmark
        
        # Generate benchmark with AI if not found
        return await self._generate_benchmark_with_ai(industry_name)
    
    async def _generate_benchmark_with_ai(self, industry_name: str) -> Dict[str, Any]:
        """Generate industry benchmark using AI"""
        try:
            prompt = f"""You are an industry analyst. Create a completeness benchmark for {industry_name} industry frameworks.

For each framework property, identify:
1. REQUIRED items (critical, must-have elements)
2. RECOMMENDED items (important but not critical)

Return ONLY JSON:
{{
    "key_metrics": {{
        "required": ["item1", "item2"],
        "recommended": ["item3", "item4"]
    }},
    "trend_areas": {{
        "required": [...],
        "recommended": [...]
    }},
    "value_drivers": {{
        "required": [...],
        "recommended": [...]
    }},
    "pain_points": {{
        "required": [...],
        "recommended": [...]
    }}
}}

Focus on industry-specific elements, not generic ones.
"""
            from app.config import CHATGPT_MAX_TOKENS
            # Use appropriate token limit for benchmark generation
            max_tokens_for_benchmark = min(CHATGPT_MAX_TOKENS, 3000)
            response = await chatgpt_generate(prompt, temperature=0.3, max_tokens=max_tokens_for_benchmark)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"Error generating benchmark: {e}")
        
        return {}

