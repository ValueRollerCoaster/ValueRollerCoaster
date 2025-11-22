"""
Enhanced Prompt Engineering with Industry-Specific Context and Market Intelligence
This module provides sophisticated prompts that incorporate industry knowledge, market trends, and competitor analysis.
"""

import json
import os
from typing import Dict, List, Optional, Any
from app.nace_system import NACE_System
from app.core.company_context_manager import CompanyContextManager

class EnhancedPromptBuilder:
    """Builds industry-specific prompts with market intelligence"""
    
    def __init__(self):
        self.nace_system = NACE_System()
        
        # Industry-specific prompt templates
        self.industry_prompts = {
            "manufacturing": {
                "value_drivers": [
                    "Operational efficiency and cost reduction",
                    "Quality control and compliance",
                    "Supply chain resilience",
                    "Innovation and R&D capabilities",
                    "Sustainability and ESG compliance"
                ],
                "pain_points": [
                    "Supply chain disruptions and material shortages",
                    "Rising energy and raw material costs",
                    "Skilled labor shortage and training needs",
                    "Regulatory compliance and safety standards",
                    "Technology adoption and digital transformation"
                ],
                "trends": [
                    "Industry 4.0 and smart manufacturing",
                    "Circular economy and sustainability",
                    "Reshoring and supply chain localization",
                    "Automation and robotics integration",
                    "Digital twins and predictive maintenance"
                ]
            },
            "agriculture": {
                "value_drivers": [
                    "Precision agriculture and yield optimization",
                    "Sustainability and environmental compliance",
                    "Cost efficiency and resource management",
                    "Technology adoption and automation",
                    "Supply chain reliability and food safety"
                ],
                "pain_points": [
                    "Climate change and weather volatility",
                    "Rising input costs (fertilizers, fuel, labor)",
                    "Regulatory compliance and food safety standards",
                    "Technology adoption barriers",
                    "Market volatility and price fluctuations"
                ],
                "trends": [
                    "Precision agriculture and IoT integration",
                    "Sustainable farming practices",
                    "Vertical farming and controlled environment agriculture",
                    "Agricultural robotics and automation",
                    "Blockchain for supply chain transparency"
                ]
            },
            "construction": {
                "value_drivers": [
                    "Project efficiency and timely delivery",
                    "Cost control and budget management",
                    "Quality assurance and safety compliance",
                    "Sustainability and green building",
                    "Technology integration and BIM adoption"
                ],
                "pain_points": [
                    "Skilled labor shortage and training costs",
                    "Material price volatility and supply chain issues",
                    "Project delays and cost overruns",
                    "Regulatory compliance and safety standards",
                    "Technology adoption and digital transformation"
                ],
                "trends": [
                    "Modular and prefabricated construction",
                    "Green building and sustainability",
                    "BIM and digital twins",
                    "Construction robotics and automation",
                    "Smart cities and infrastructure"
                ]
            },
            "logistics": {
                "value_drivers": [
                    "Supply chain visibility and transparency",
                    "Cost efficiency and route optimization",
                    "Reliability and on-time delivery",
                    "Sustainability and carbon footprint reduction",
                    "Technology integration and automation"
                ],
                "pain_points": [
                    "Driver shortage and labor costs",
                    "Fuel price volatility and sustainability pressure",
                    "Last-mile delivery challenges",
                    "Supply chain disruptions and delays",
                    "Technology adoption and digital transformation"
                ],
                "trends": [
                    "Autonomous vehicles and drones",
                    "Green logistics and electric vehicles",
                    "Real-time tracking and visibility",
                    "Warehouse automation and robotics",
                    "Last-mile delivery optimization"
                ]
            }
        }
    
    def get_industry_context(self, industry_name: str, nace_code: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive industry context using dynamic frameworks"""
        
        # Import the dynamic framework generator
        from app.ai.market_intelligence import market_intelligence_service
        
        # Get framework for this industry
        framework = market_intelligence_service.framework_generator.get_framework_for_industry(industry_name)
        
        # Use provided NACE code or get from framework
        if not nace_code:
            nace_codes = framework.get('nace_codes', [])
            nace_code = nace_codes[0] if nace_codes else None
        
        # Get industry insights
        # Type narrowing: nace_code is Optional[str], ensure it's str before passing
        # The nace_system methods expect str but handle None internally, so we need to pass a string or skip
        insights = self.nace_system.get_industry_insights(nace_code) if nace_code else {}  # type: ignore[arg-type]
        
        # Get customer segments
        segments = self.nace_system.get_customer_segments(nace_code) if nace_code else {}  # type: ignore[arg-type]
        
        # Get value chain analysis
        value_chain = self.nace_system.get_value_chain_analysis(nace_code) if nace_code else {}  # type: ignore[arg-type]
        
        # Use dynamic framework data instead of hardcoded prompts
        industry_specific = {
            "value_drivers": framework.get('value_drivers', []),
            "pain_points": framework.get('pain_points', []),
            "trends": framework.get('trend_areas', [])
        }
        
        return {
            "nace_code": nace_code,
            "insights": insights,
            "segments": segments,
            "value_chain": value_chain,
            "industry_specific": industry_specific,
            "industry_name": framework.get('industry_name', industry_name)
        }
    
    def _normalize_industry_name(self, industry_name: str) -> str:
        """Normalize industry name for prompt lookup"""
        industry_lower = industry_name.lower()
        
        if any(word in industry_lower for word in ["manufacturing", "factory", "production"]):
            return "manufacturing"
        elif any(word in industry_lower for word in ["agriculture", "farming", "agri"]):
            return "agriculture"
        elif any(word in industry_lower for word in ["construction", "building", "infrastructure"]):
            return "construction"
        elif any(word in industry_lower for word in ["logistics", "transport", "warehouse", "supply chain"]):
            return "logistics"
        else:
            return "manufacturing"  # Default fallback
    
    async def build_enhanced_persona_prompt(self, website: str, industry_name: str, 
                                          company_summary: str) -> str:
        """Build an enhanced persona prompt with industry-specific context and market intelligence"""
        
        # Get comprehensive industry context
        industry_context = self.get_industry_context(industry_name)
        
        # Get market intelligence using Gemini
        from app.ai.market_intelligence import market_intelligence_service
        import logging
        logger = logging.getLogger("enhanced_prompts")
        
        logger.info(f"[DEBUG] Fetching market intelligence for {industry_name} industry in persona generation")
        market_data = await market_intelligence_service.get_market_data_for_prompts(
            industry_name=industry_name,
            company_summary=company_summary,
            nace_code=industry_context.get('nace_code')
        )
        logger.info(f"[DEBUG] Market intelligence data received for {industry_name} industry in persona generation")
        
        # Build industry-specific value drivers and pain points
        value_drivers = industry_context.get("industry_specific", {}).get("value_drivers", [])
        pain_points = industry_context.get("industry_specific", {}).get("pain_points", [])
        trends = industry_context.get("industry_specific", {}).get("trends", [])
        
        # Get customer segments for this industry
        segments = industry_context.get("segments", {})
        
        # Get company profile target customers as fallback
        company_context = CompanyContextManager()
        company_target_customers = company_context.get_target_customers()
        
        # Build dynamic customer segment fallbacks from company profile
        manufacturers_fallback = ', '.join(company_target_customers) if company_target_customers else 'Business customers'
        distributors_fallback = ', '.join([c for c in company_target_customers if any(keyword in c.lower() for keyword in ['distributor', 'reseller', 'dealer', 'channel'])]) if company_target_customers else 'Distribution partners'
        end_users_fallback = ', '.join([c for c in company_target_customers if any(keyword in c.lower() for keyword in ['end user', 'customer', 'client'])]) if company_target_customers else 'End users'
        
        # Build enhanced prompt
        prompt = f"""
You are an expert B2B buyer persona analyst specializing in {industry_name} industry. Your task is to generate a comprehensive buyer persona based on the provided company information.

INDUSTRY CONTEXT FOR {industry_name.upper()}:
- NACE Code: {industry_context.get('nace_code', 'Unknown')}
- Key Industry Trends: {', '.join(trends) if trends else 'Digital transformation, Sustainability, Cost optimization'}
- Typical Value Drivers: {', '.join(value_drivers) if value_drivers else 'Operational efficiency, Quality, Innovation'}
- Common Pain Points: {', '.join(pain_points) if pain_points else 'Cost pressure, Competition, Regulatory compliance'}

CUSTOMER SEGMENT ANALYSIS:
- Direct Customers: {', '.join(segments.get('manufacturers', [])) if segments.get('manufacturers') else manufacturers_fallback}
- Distribution Channels: {', '.join(segments.get('distributors', [])) if segments.get('distributors') else distributors_fallback}
- End Users: {', '.join(segments.get('end_users', [])) if segments.get('end_users') else end_users_fallback}

COMPANY INFORMATION:
Website: {website}
Industry: {industry_name}
Company Summary: {company_summary}

MARKET INTELLIGENCE (AI-Generated):
{market_data}

INSTRUCTIONS:
1. Analyze the company's position within the {industry_name} industry
2. Consider industry-specific challenges and opportunities for {industry_name}
3. Use the provided market intelligence to inform your analysis
4. Create a concise industry overview that explains this company's context within their industry
5. Focus on how industry trends and market conditions affect this specific company
6. Provide a clear, concise summary that would help understand this company's industry context

REQUIRED OUTPUT FORMAT (JSON only):
{{
  "industry": "string (industry name)",
  "summary": "string (5-10 sentence concise industry overview for this specific company)"
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        return prompt
    
    async def build_enhanced_value_alignment_prompt(self, prospect_data: str, company_profile: dict, 
                                                  value_components: str, industry_name: str) -> str:
        """Build an enhanced value alignment prompt with industry context and market intelligence"""
        
        # Get industry context
        industry_context = self.get_industry_context(industry_name)
        
        # Get market intelligence using Gemini
        from app.ai.market_intelligence import market_intelligence_service
        import logging
        logger = logging.getLogger("enhanced_prompts")
        
        logger.info(f"[DEBUG] Fetching market intelligence for {industry_name} industry in value alignment")
        market_data = await market_intelligence_service.get_market_data_for_prompts(
            industry_name=industry_name,
            company_summary=prospect_data,
            nace_code=industry_context.get('nace_code')
        )
        logger.info(f"[DEBUG] Market intelligence data received for {industry_name} industry")
        
        # Get industry-specific value drivers
        industry_value_drivers = industry_context.get("industry_specific", {}).get("value_drivers", [])
        
        prompt = f"""
You are an expert B2B value consultant specializing in {industry_name} industry. Your task is to create a strategic value alignment matrix between a prospect and our company.

INDUSTRY CONTEXT FOR {industry_name.upper()}:
- Key Value Drivers: {', '.join(industry_value_drivers)}
- Common Pain Points: {', '.join(industry_context.get('industry_specific', {}).get('pain_points', []))}
- Market Trends: {', '.join(industry_context.get('industry_specific', {}).get('trends', []))}

MARKET INTELLIGENCE (AI-Generated):
{market_data}

PROSPECT DATA:
{prospect_data}

OUR COMPANY PROFILE:
{json.dumps(company_profile, indent=2)}

OUR VALUE COMPONENTS:
{value_components}

INSTRUCTIONS:
1. Analyze the prospect's needs through the lens of {industry_name} industry challenges
2. Use the provided market intelligence to inform your analysis
3. Match prospect needs to our value components considering industry-specific factors
4. Provide industry-relevant rationales for each alignment
5. Consider market trends, competitive factors, and market conditions in {industry_name}
6. Suggest conversation starters that resonate with {industry_name} decision makers
7. Identify market opportunities and competitive advantages

REQUIRED OUTPUT FORMAT (JSON only):
{{
  "alignment_matrix": [
    {{
      "prospect_need": "string",
      "our_value_component": "string", 
      "rationale": "string",
      "match_score_percent": int (0-100),
      "conversation_starter": "string",
      "industry_relevance": "string",
      "market_context": "string"
    }}
  ],
  "unmatched_needs": ["string", ...],
  "industry_opportunities": ["string", ...],
  "competitive_advantages": ["string", ...],
  "market_risks": ["string", ...],
  "strategic_recommendations": ["string", ...]
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        return prompt

# Global instance
enhanced_prompt_builder = EnhancedPromptBuilder() 