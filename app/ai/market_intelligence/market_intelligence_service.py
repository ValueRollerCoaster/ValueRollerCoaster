"""
Market Intelligence Service
Provides comprehensive market intelligence using Gemini AI and dynamic industry frameworks.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from app.nace_system import NACE_System
from app.ai.gemini_client import gemini_client
from .dynamic_generator import DynamicIndustryFrameworkGenerator

logger = logging.getLogger(__name__)

def clean_json_response(response_text: str) -> str:
    """
    Clean JSON response by removing markdown formatting and other artifacts.
    Handles ```json ... ``` blocks and general text cleaning.
    """
    if not response_text or not isinstance(response_text, str):
        return ""
    
    cleaned_response = response_text.strip()
    
    # Remove markdown code block formatting if present
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]  # Remove "```json"
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]  # Remove "```"
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]  # Remove trailing "```"
    
    # Clean up any remaining whitespace
    cleaned_response = cleaned_response.strip()
    
    # Remove common instruction phrases that might be inside the JSON
    instruction_phrases = [
        'Output ONLY the JSON object',
        'Do not include any other text',
        'CRITICAL:',
        'IMPORTANT:',
        'JSON RULES:',
        'Example of valid JSON:',
        'Required JSON structure:',
        'Input:',
        'Now, analyze',
        'generate a valid JSON response',
        'Example response:',
        'Required JSON format:'
    ]
    
    for phrase in instruction_phrases:
        cleaned_response = cleaned_response.replace(phrase, '')
    
    # Remove trailing commas before closing brackets/braces
    cleaned_response = re.sub(r',\s*([}\]])', r'\1', cleaned_response)
    
    return cleaned_response.strip()

class MarketIntelligenceService:
    """Service for gathering comprehensive market intelligence using Gemini AI"""
    
    def __init__(self):
        self.nace_system = NACE_System()
        self.framework_generator = DynamicIndustryFrameworkGenerator()
        
    async def get_comprehensive_market_intelligence(self, industry_name: str, company_summary: str, 
                                                   nace_code: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive market intelligence using Gemini AI"""
        
        try:
            # Get framework for this industry
            framework = self.framework_generator.get_framework_for_industry(industry_name)
            
            # Get NACE insights if available
            nace_insights = self.nace_system.get_industry_insights(nace_code) if nace_code else {}
            
            # Build comprehensive market intelligence prompt
            intelligence_prompt = f"""
You are a senior market intelligence analyst with expertise in {industry_name} industry. 
Your task is to provide comprehensive market intelligence for B2B decision making.

INDUSTRY FRAMEWORK:
{framework.get('industry_name', industry_name)}
NACE CODES: {', '.join(framework.get('nace_codes', []))}
KEY METRICS: {', '.join(framework.get('key_metrics', []))}
TREND AREAS: {', '.join(framework.get('trend_areas', []))}
COMPETITIVE FACTORS: {', '.join(framework.get('competitive_factors', []))}
VALUE DRIVERS: {', '.join(framework.get('value_drivers', []))}
PAIN POINTS: {', '.join(framework.get('pain_points', []))}
TECHNOLOGY FOCUS: {', '.join(framework.get('technology_focus', []))}
SUSTAINABILITY: {', '.join(framework.get('sustainability_initiatives', []))}

COMPANY CONTEXT: {company_summary}

Please provide a comprehensive market intelligence analysis covering:

1. MARKET TRENDS & OPPORTUNITIES
2. COMPETITIVE LANDSCAPE
3. MARKET SIZE & GROWTH
4. TECHNOLOGY ADOPTION
5. SUSTAINABILITY INITIATIVES
6. REGIONAL VARIATIONS
7. FUTURE OUTLOOK

Output format (JSON only):
{{
  "market_overview": {{
    "market_size": {{
      "global": "string (e.g., €50B)",
      "european": "string (e.g., €15B)",
      "growth_rate": "string (e.g., 5.2% annually)",
      "projection_5y": "string (e.g., €20B by 2029)"
    }},
    "market_maturity": "string (Emerging|Growing|Mature|Declining)",
    "key_segments": ["string", ...],
    "regional_variations": ["string", ...]
  }},
  "current_trends": [
    {{
      "trend": "string",
      "impact": "string (High|Medium|Low)",
      "description": "string",
      "business_implications": "string"
    }}
  ],
  "competitive_landscape": {{
    "key_competitors": [
      {{
        "name": "string",
        "positioning": "string",
        "strengths": ["string", ...],
        "weaknesses": ["string", ...],
        "market_share": "string (estimated)"
      }}
    ],
    "competitive_advantages": ["string", ...],
    "competitive_threats": ["string", ...],
    "market_positioning": "string"
  }},
  "technology_adoption": {{
    "current_adoption": ["string", ...],
    "emerging_technologies": ["string", ...],
    "adoption_barriers": ["string", ...],
    "investment_priorities": ["string", ...]
  }},
  "sustainability_initiatives": {{
    "current_practices": ["string", ...],
    "regulatory_pressure": ["string", ...],
    "customer_demand": ["string", ...],
    "investment_opportunities": ["string", ...]
  }},
  "market_opportunities": ["string", ...],
  "risk_factors": ["string", ...],
  "strategic_recommendations": ["string", ...],
  "summary": "string"
}}

Base your analysis on current market knowledge, industry reports, and best practices.
Provide realistic estimates and actionable insights for B2B decision making.
"""
            
            # Get comprehensive market intelligence from Gemini
            intelligence_response = await gemini_client(intelligence_prompt, temperature=0.3)
            
            # Parse response
            if intelligence_response and not intelligence_response.startswith("ERROR"):
                try:
                    # Handle markdown-wrapped JSON responses
                    cleaned_response = clean_json_response(intelligence_response)
                    
                    intelligence_data = json.loads(cleaned_response)
                    return {
                        "success": True,
                        "industry_name": industry_name,
                        "nace_code": nace_code,
                        "market_intelligence": intelligence_data,
                        "nace_insights": nace_insights,
                        "framework_used": framework.get('industry_name', industry_name),
                        "timestamp": datetime.now().isoformat(),
                        "data_quality": "AI-generated comprehensive analysis"
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse market intelligence JSON: {e}")
                    logger.error(f"Raw response: {intelligence_response[:500]}...")
            
            # Fallback to basic intelligence
            # Get company profile target customers for dynamic fallback
            from app.core.company_context_manager import CompanyContextManager
            company_context = CompanyContextManager()
            company_target_customers = company_context.get_target_customers()
            
            # Use company profile target customers if available, otherwise generic fallback
            if company_target_customers:
                key_segments = company_target_customers
            else:
                key_segments = ["Business customers"]
            
            fallback_data = {
                "market_overview": {
                    "market_size": {
                        "global": "€100B+",
                        "european": "€30B+",
                        "growth_rate": "3-5% annually",
                        "projection_5y": "Growing steadily"
                    },
                    "market_maturity": "Growing",
                    "key_segments": key_segments,
                    "regional_variations": ["Strong growth in Eastern Europe", "Mature markets in Western Europe"]
                },
                "current_trends": [
                    {
                        "trend": "Digital transformation",
                        "impact": "High",
                        "description": "Industry-wide adoption of digital technologies",
                        "business_implications": "Increased automation and efficiency"
                    }
                ],
                "competitive_landscape": {
                    "key_competitors": [],
                    "competitive_advantages": ["Quality", "Service", "Innovation"],
                    "competitive_threats": ["Price competition", "New entrants"],
                    "market_positioning": "Specialized solutions provider"
                },
                "technology_adoption": {
                    "current_adoption": ["Industry 4.0", "Automation"],
                    "emerging_technologies": ["AI/ML", "IoT", "Robotics"],
                    "adoption_barriers": ["Cost", "Skills gap", "Integration complexity"],
                    "investment_priorities": ["Digital transformation", "Sustainability"]
                },
                "sustainability_initiatives": {
                    "current_practices": ["ESG compliance", "Green manufacturing"],
                    "regulatory_pressure": ["Environmental regulations", "Carbon reduction targets"],
                    "customer_demand": ["Sustainable products", "Transparent supply chains"],
                    "investment_opportunities": ["Green technology", "Circular economy"]
                },
                "market_opportunities": ["Digital transformation", "Sustainability initiatives", "Market expansion"],
                "risk_factors": ["Economic uncertainty", "Supply chain disruptions", "Technology disruption"],
                "strategic_recommendations": ["Invest in digital capabilities", "Focus on sustainability", "Strengthen partnerships"],
                "summary": f"{industry_name} market shows steady growth driven by technology adoption and sustainability initiatives."
            }
            
            return {
                "success": False,
                "industry_name": industry_name,
                "nace_code": nace_code,
                "market_intelligence": fallback_data,
                "nace_insights": nace_insights,
                "framework_used": framework.get('industry_name', industry_name),
                "timestamp": datetime.now().isoformat(),
                "data_quality": "Fallback analysis"
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive market intelligence: {e}")
            return {
                "success": False,
                "error": str(e),
                "industry_name": industry_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_multi_industry_intelligence(self, company_summary: str) -> Dict[str, Any]:
        """Get market intelligence for all company industries"""
        
        try:
            company_industries = self.framework_generator.get_company_industries()
            
            # Get intelligence for each industry
            intelligence_tasks = []
            for industry in company_industries:
                task = self.get_comprehensive_market_intelligence(
                    industry_name=industry,
                    company_summary=company_summary
                )
                intelligence_tasks.append(task)
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*intelligence_tasks, return_exceptions=True)
            
            # Process results
            multi_industry_intelligence = {
                "success": True,
                "company_industries": company_industries,
                "industry_intelligence": {},
                "summary": {},
                "timestamp": datetime.now().isoformat()
            }
            
            for i, result in enumerate(results):
                industry = company_industries[i]
                if isinstance(result, Exception):
                    logger.error(f"Error getting intelligence for {industry}: {result}")
                    multi_industry_intelligence["industry_intelligence"][industry] = {
                        "success": False,
                        "error": str(result)
                    }
                else:
                    multi_industry_intelligence["industry_intelligence"][industry] = result
            
            # Generate summary
            successful_intelligence = [
                result for result in results 
                if not isinstance(result, Exception) and isinstance(result, dict) and result.get("success")
            ]
            
            if successful_intelligence:
                multi_industry_intelligence["summary"] = {
                    "total_industries": len(company_industries),
                    "successful_analyses": len(successful_intelligence),
                    "success_rate": len(successful_intelligence) / len(company_industries) * 100
                }
            
            return multi_industry_intelligence
            
        except Exception as e:
            logger.error(f"Error getting multi-industry intelligence: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_industry_specific_insights(self, industry_name: str, company_summary: str, 
                                           focus_area: str = "trends") -> Dict[str, Any]:
        """Get industry-specific insights for a particular focus area"""
        
        try:
            # Get framework for this industry
            framework = self.framework_generator.get_framework_for_industry(industry_name)
            
            # Build focused analysis prompt
            focus_prompt = f"""
You are a specialized industry analyst focusing on {focus_area} in {industry_name} industry.
Provide detailed insights for B2B decision making.

INDUSTRY FRAMEWORK:
{framework.get('industry_name', industry_name)}
KEY METRICS: {', '.join(framework.get('key_metrics', []))}
TREND AREAS: {', '.join(framework.get('trend_areas', []))}
COMPETITIVE FACTORS: {', '.join(framework.get('competitive_factors', []))}
VALUE DRIVERS: {', '.join(framework.get('value_drivers', []))}
PAIN POINTS: {', '.join(framework.get('pain_points', []))}

FOCUS AREA: {focus_area}
COMPANY CONTEXT: {company_summary}

Please provide detailed analysis of {focus_area} in {industry_name} industry.

Output format (JSON only):
{{
  "focus_area": "{focus_area}",
  "industry": "{industry_name}",
  "key_insights": ["string", ...],
  "current_state": "string",
  "future_outlook": "string",
  "business_implications": ["string", ...],
  "recommendations": ["string", ...],
  "summary": "string"
}}

Base your analysis on current market knowledge and industry best practices.
"""
            
            # Get focused insights from Gemini
            insights_response = await gemini_client(focus_prompt, temperature=0.3)
            
            # Parse response
            if insights_response and not insights_response.startswith("ERROR"):
                try:
                    # Handle markdown-wrapped JSON responses
                    cleaned_response = clean_json_response(insights_response)
                    
                    insights_data = json.loads(cleaned_response)
                    return {
                        "success": True,
                        "focus_area": focus_area,
                        "industry": industry_name,
                        "insights": insights_data,
                        "framework_used": framework.get('industry_name', industry_name),
                        "timestamp": datetime.now().isoformat()
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse insights JSON: {e}")
                    logger.error(f"Raw response: {insights_response[:500]}...")
            
            # Fallback insights
            fallback_insights = {
                "focus_area": focus_area,
                "industry": industry_name,
                "key_insights": [f"Key insights for {focus_area} in {industry_name}"],
                "current_state": f"Current state of {focus_area} in {industry_name}",
                "future_outlook": f"Future outlook for {focus_area} in {industry_name}",
                "business_implications": ["Business implications for the focus area"],
                "recommendations": ["Strategic recommendations"],
                "summary": f"Summary of {focus_area} analysis for {industry_name}"
            }
            
            return {
                "success": False,
                "focus_area": focus_area,
                "industry": industry_name,
                "insights": fallback_insights,
                "framework_used": framework.get('industry_name', industry_name),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting industry-specific insights: {e}")
            return {
                "success": False,
                "error": str(e),
                "focus_area": focus_area,
                "industry": industry_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_market_data_for_prompts(self, industry_name: str, company_summary: str, 
                                        nace_code: Optional[str] = None) -> str:
        """Get market data formatted for use in prompts"""
        
        try:
            # Get comprehensive market intelligence
            intelligence = await self.get_comprehensive_market_intelligence(industry_name, company_summary, nace_code)
            
            if intelligence.get("success"):
                market_data = intelligence.get("market_intelligence", {})
                
                # Format for prompt usage
                formatted_data = {
                    "market_size": market_data.get("market_overview", {}).get("market_size", {}),
                    "trends": [trend.get("trend", "") for trend in market_data.get("current_trends", [])],
                    "opportunities": market_data.get("market_opportunities", []),
                    "risks": market_data.get("risk_factors", []),
                    "technology": market_data.get("technology_adoption", {}).get("current_adoption", []),
                    "sustainability": market_data.get("sustainability_initiatives", {}).get("current_practices", [])
                }
                
                return json.dumps(formatted_data, indent=2)
            else:
                return "Market data unavailable"
                
        except Exception as e:
            logger.error(f"Error formatting market data for prompts: {e}")
            return "Market data unavailable"
    
    def get_company_industry_frameworks(self) -> Dict[str, Any]:
        """Get frameworks for all company industries"""
        return self.framework_generator.get_company_frameworks()
    
    def get_company_industries(self) -> List[str]:
        """Get list of industries served by the company"""
        return self.framework_generator.get_company_industries()
    
    def validate_industry_coverage(self) -> Dict[str, Any]:
        """Validate that all company industries have frameworks"""
        return self.framework_generator.validate_industry_coverage()
    
    def get_framework_summary(self) -> Dict[str, Any]:
        """Get summary of all frameworks"""
        return self.framework_generator.get_framework_summary()

# Global instance
market_intelligence_service = MarketIntelligenceService() 