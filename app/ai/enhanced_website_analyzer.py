"""
Enhanced Website Analyzer
Provides deep, targeted analysis of customer websites for persona generation.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from app.ai.rate_limited_gemini import rate_limited_gemini
from app.ai.gemini_client import (
    get_grounded_company_summary, 
    get_grounded_company_summary_with_explicit_search,
    gemini_client_with_grounding
)

logger = logging.getLogger(__name__)

class EnhancedWebsiteAnalyzer:
    """Enhanced analyzer for deep customer website analysis"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    async def analyze_website_deep(self, website_url: str, target_industry: Optional[str] = None, 
                                   verified_company_name: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """
        Perform deep analysis of a customer website with targeted focus points.
        Returns comprehensive analysis for persona generation.
        
        Args:
            website_url: Target website URL
            target_industry: Industry classification (optional)
            verified_company_name: User-verified company name (optional, used as source of truth)
        """
        
        logger.info(f"[EnhancedWebsiteAnalyzer] Starting deep analysis of: {website_url}")
        if verified_company_name:
            logger.info(f"[EnhancedWebsiteAnalyzer] Using verified company: {verified_company_name}")
        
        try:
            # Step 1: Get comprehensive website content with grounding
            website_content = await self._get_comprehensive_website_content(website_url, verified_company_name)
            
            # Step 2: Analyze specific business aspects
            business_analysis = await self._analyze_business_aspects(website_url, website_content, target_industry, verified_company_name, pid=pid)
            
            # Step 3: Extract customer-specific insights
            customer_insights = await self._extract_customer_insights(website_url, website_content, business_analysis, verified_company_name, pid=pid)
            
            # Step 4: Analyze competitive positioning
            competitive_analysis = await self._analyze_competitive_positioning(website_url, website_content, business_analysis, verified_company_name, pid=pid)
            
            # Step 5: Identify specific pain points and opportunities
            pain_points_analysis = await self._identify_pain_points_and_opportunities(website_url, website_content, business_analysis, verified_company_name, pid=pid)
            
            # Step 6: Generate targeted persona insights
            persona_insights = await self._generate_targeted_persona_insights(
                website_url, website_content, business_analysis, customer_insights, competitive_analysis, pain_points_analysis, verified_company_name, pid=pid
            )
            
            # Combine all analyses
            comprehensive_analysis = {
                "website_url": website_url,
                "target_industry": target_industry,
                "verified_company_name": verified_company_name,  # Store verified name in analysis
                "website_content": website_content,
                "business_analysis": business_analysis,
                "customer_insights": customer_insights,
                "competitive_analysis": competitive_analysis,
                "pain_points_analysis": pain_points_analysis,
                "persona_insights": persona_insights,
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info(f"[EnhancedWebsiteAnalyzer] Deep analysis completed for: {website_url}")
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"[EnhancedWebsiteAnalyzer] Error in deep analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _build_verified_company_context(self, website_url: str, verified_company_name: Optional[str] = None) -> str:
        """Build verified company context for prompts"""
        if not verified_company_name:
            return ""
        
        return f"""
════════════════════════════════════════════════════════════
🎯 CRITICAL: USER-VERIFIED COMPANY (AUTHORITATIVE SOURCE)
════════════════════════════════════════════════════════════

The website {website_url} belongs to: {verified_company_name}

THIS IS USER-VERIFIED INFORMATION AND IS THE SOURCE OF TRUTH.

YOU MUST:
✅ Analyze ONLY {verified_company_name}
✅ Verify all information matches {verified_company_name}
✅ Ignore any other companies with similar names
✅ Confirm domain ownership matches {verified_company_name}

YOU MUST NOT:
❌ Analyze any other company, even with similar names
❌ Use information about companies that don't own this domain
❌ Confuse {verified_company_name} with similarly-named companies

════════════════════════════════════════════════════════════
"""
    
    async def _get_comprehensive_website_content(self, website_url: str, verified_company_name: Optional[str] = None) -> str:
        """Get comprehensive website content with multiple approaches"""
        
        # Try grounded analysis first
        grounded_content = get_grounded_company_summary(website_url)
        if grounded_content and not grounded_content.startswith("ERROR"):
            # Validate that the grounded content is about the correct company
            validation_result = await self._validate_company_focus(website_url, grounded_content)
            if validation_result.get("is_correct_company", False):
                logger.info(f"[_get_comprehensive_website_content] Successfully retrieved grounded content for {website_url}")
                return grounded_content
            else:
                logger.warning(f"Grounded content may be about wrong company. Trying explicit search fallback.")
        
        # If initial grounding failed or validation failed, try explicit search version
        if grounded_content.startswith("ERROR"):
            logger.warning(f"[_get_comprehensive_website_content] Initial grounding failed: {grounded_content[:100]}. Trying explicit search.")
            explicit_search_content = get_grounded_company_summary_with_explicit_search(website_url)
            if explicit_search_content and not explicit_search_content.startswith("ERROR"):
                validation_result = await self._validate_company_focus(website_url, explicit_search_content)
                if validation_result.get("is_correct_company", False):
                    logger.info(f"[_get_comprehensive_website_content] Successfully retrieved content via explicit search for {website_url}")
                    return explicit_search_content
                else:
                    logger.warning(f"Explicit search content may be about wrong company. Using enhanced fallback.")
        
        # Fallback: Enhanced content extraction with explicit Google Search instructions
        verified_context = self._build_verified_company_context(website_url, verified_company_name)
        
        enhanced_prompt = f"""
You are an expert business analyst conducting a comprehensive analysis of a SPECIFIC company. 
Your task is to analyze the company that owns and operates this website: {website_url}
{verified_context}

**CRITICAL INSTRUCTIONS:**
- Use Google Search to find comprehensive information about this company
- Do NOT attempt to access the website directly
- Use ONLY Google Search results from multiple sources (news articles, Wikipedia, company profiles, business directories, press releases)
- Search for information even if the website might be temporarily unavailable
- Analyze ONLY the company that owns and operates this specific website URL
- Do NOT analyze any other companies mentioned in search results
- Focus exclusively on the company that controls this domain

**TARGET COMPANY IDENTIFICATION:**
- The company to analyze is the one that owns and operates the domain: {website_url}
- This is the company whose products, services, and business information you should extract
- Ignore any mentions of other companies, partners, or customers unless they directly relate to the target company's business

**SEARCH STRATEGY:**
Search Google for:
- Company name and official business information
- Products and services portfolio
- Recent news articles and announcements
- Company profiles on business directories (Crunchbase, LinkedIn, industry databases)
- Wikipedia entries (if available)
- Press releases and official communications
- Industry reports and market information

FOCUS ON THESE SPECIFIC AREAS FOR THE TARGET COMPANY:

1. **COMPANY OVERVIEW**
   - Company name, history, size, location
   - Mission, vision, values
   - Key leadership and organizational structure

2. **PRODUCTS & SERVICES**
   - Detailed product/service portfolio
   - Technical specifications and features
   - Target applications and use cases
   - Pricing models (if available)

3. **CUSTOMER SEGMENTS**
   - Who are their target customers?
   - What industries do they serve?
   - Customer testimonials and case studies
   - Customer success stories

4. **VALUE PROPOSITIONS**
   - What problems do they solve?
   - What benefits do they offer?
   - Unique selling points
   - Competitive advantages

5. **MARKET POSITIONING**
   - How do they position themselves?
   - What makes them different?
   - Brand messaging and tone
   - Market reputation

6. **BUSINESS MODEL**
   - Revenue streams
   - Sales channels
   - Partnership strategies
   - Geographic reach

7. **TECHNOLOGY & INNOVATION**
   - Technology stack
   - R&D focus areas
   - Innovation initiatives
   - Digital transformation efforts

8. **CHALLENGES & OPPORTUNITIES**
   - Industry challenges they address
   - Market opportunities they pursue
   - Growth strategies
   - Risk factors

9. **CUSTOMER EXPERIENCE**
   - Customer service approach
   - Support and maintenance
   - Training and education
   - Customer engagement

10. **SUSTAINABILITY & COMPLIANCE**
    - Environmental initiatives
    - Regulatory compliance
    - Quality certifications
    - Corporate responsibility

ANALYSIS INSTRUCTIONS:
- Use Google Search to find information from multiple sources
- Synthesize information from news articles, company profiles, Wikipedia, and other indexed sources
- Extract specific details, numbers, and facts from search results
- Identify patterns in their messaging and approach
- Note any inconsistencies or gaps in information
- Focus on B2B aspects and decision-making factors
- **IMPORTANT: Only analyze the company that owns this website domain**
- Cite sources when possible (news articles, company profiles, etc.)

OUTPUT FORMAT:
Provide a comprehensive, structured analysis covering all the above areas. Be specific and detailed.
Include direct quotes and specific examples from search results where possible.
Mention the sources you found information from (e.g., "According to [source], the company...").
Start your analysis by clearly identifying the target company name and confirming it owns this website.
{f"**CRITICAL: The company name MUST be: {verified_company_name}**" if verified_company_name else ""}
"""
        
        # Use gemini_client_with_grounding to ensure Google Search is explicitly enabled
        content = await gemini_client_with_grounding(enhanced_prompt, temperature=0.1, max_tokens=32000)
        
        if content and not content.startswith("ERROR"):
            logger.info(f"[_get_comprehensive_website_content] Successfully retrieved content via enhanced fallback for {website_url}")
            return content
        elif content.startswith("ERROR"):
            logger.error(f"[_get_comprehensive_website_content] Enhanced fallback also failed: {content[:200]}")
            # Last resort: return a message indicating we need to use alternative sources
            return f"Unable to retrieve website content for {website_url}. Error: {content}. Please use alternative information sources for analysis."
        else:
            logger.warning(f"[_get_comprehensive_website_content] Enhanced fallback returned empty content for {website_url}")
            return "Failed to extract website content. Please use alternative information sources."
    
    async def _analyze_business_aspects(self, website_url: str, website_content: str, target_industry: Optional[str], 
                                       verified_company_name: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """Analyze specific business aspects of the company"""
        
        verified_context = self._build_verified_company_context(website_url, verified_company_name)
        
        prompt = f"""
You are a senior business analyst specializing in B2B market analysis. 
Analyze the following company information and provide detailed insights.
{verified_context}
**TARGET COMPANY:** {verified_company_name if verified_company_name else f"The company that owns and operates the website at: {website_url}"}
**TARGET INDUSTRY:** {target_industry or 'Unknown'}
**WEBSITE CONTENT:** {website_content}

**CRITICAL:** Focus your analysis ONLY on {verified_company_name if verified_company_name else "the company that owns and operates this website"}. Do not analyze any other companies mentioned in the content.

ANALYZE THESE SPECIFIC BUSINESS ASPECTS FOR THE TARGET COMPANY:

1. **BUSINESS MODEL ANALYSIS**
   - Revenue model (product sales, services, subscriptions, etc.)
   - Customer acquisition strategy
   - Pricing strategy and positioning
   - Sales and distribution channels

2. **TARGET CUSTOMER ANALYSIS**
   - Primary customer segments
   - Customer personas they target
   - Decision-making process they assume
   - Customer lifecycle and journey

3. **COMPETITIVE POSITIONING**
   - Direct competitors they mention
   - How they differentiate themselves
   - Market positioning strategy
   - Brand perception they aim for

4. **VALUE DELIVERY**
   - Core value propositions
   - Problem-solution fit
   - Customer benefits and outcomes
   - Success metrics they track

5. **OPERATIONAL FOCUS**
   - Key operational priorities
   - Quality and service standards
   - Technology and innovation focus
   - Geographic and market expansion

6. **FINANCIAL HEALTH INDICATORS**
   - Growth indicators
   - Investment in R&D
   - Market expansion efforts
   - Partnership and acquisition activities

OUTPUT FORMAT (JSON only):
{{
  "company_name": "{verified_company_name if verified_company_name else '[extracted from analysis]'}",
  "company_name_verified": {str(verified_company_name is not None).lower()},
  "domain_ownership_confirmed": true,
  "business_model": {{
    "revenue_model": "string",
    "customer_acquisition": "string",
    "pricing_strategy": "string",
    "sales_channels": ["string"]
  }},
  "target_customers": {{
    "primary_segments": ["string"],
    "customer_personas": ["string"],
    "decision_process": "string",
    "customer_journey": "string"
  }},
  "competitive_positioning": {{
    "direct_competitors": ["string"],
    "differentiation": ["string"],
    "positioning_strategy": "string",
    "brand_perception": "string"
  }},
  "value_delivery": {{
    "core_propositions": ["string"],
    "problem_solution_fit": "string",
    "customer_benefits": ["string"],
    "success_metrics": ["string"]
  }},
  "operational_focus": {{
    "priorities": ["string"],
    "quality_standards": "string",
    "innovation_focus": "string",
    "expansion_efforts": "string"
  }},
  "financial_indicators": {{
    "growth_indicators": ["string"],
    "rd_investment": "string",
    "market_expansion": "string",
    "partnerships": ["string"]
  }}
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        
        response = await rate_limited_gemini.rate_limited_call(prompt, temperature=0.2, max_tokens=16000, pid=pid)
        
        # Check if response is an error before trying to parse JSON
        # Check for various error formats: "ERROR:", "ERROR ", or contains "503" or "Service Unavailable"
        is_error = False
        if not response:
            is_error = True
        elif isinstance(response, str):
            response_upper = response.upper()
            is_error = (
                response.startswith("ERROR:") or 
                response.startswith("ERROR ") or
                "503" in response or
                "SERVICE UNAVAILABLE" in response_upper or
                "OVERLOADED" in response_upper or
                "UNAVAILABLE" in response_upper
            )
        
        if is_error:
            logger.error(f"Gemini API returned error for business analysis: {response[:200] if response else 'None'}")
            return {}
        
        try:
            # Extract JSON from markdown code blocks if present
            if response and "```json" in response:
                # Extract content between ```json and ```
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            
            # Try direct JSON parsing
            return json.loads(response) if response else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse business analysis JSON: {response[:200] if response else 'None'}")
            return {}
    
    async def _extract_customer_insights(self, website_url: str, website_content: str, business_analysis: Dict,
                                         verified_company_name: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """Extract customer-specific insights from the website"""
        
        verified_context = self._build_verified_company_context(website_url, verified_company_name)
        
        prompt = f"""
You are a customer insights specialist analyzing a B2B company's customer approach.
Extract deep customer insights from the following information.
{verified_context}
**TARGET COMPANY:** {verified_company_name if verified_company_name else f"The company that owns {website_url}"}

WEBSITE: {website_url}
WEBSITE CONTENT: {website_content}
BUSINESS ANALYSIS: {json.dumps(business_analysis, indent=2)}

EXTRACT THESE CUSTOMER INSIGHTS:

1. **CUSTOMER PAIN POINTS THEY ADDRESS**
   - What specific problems do they solve?
   - What customer frustrations do they mention?
   - What industry challenges do they tackle?

2. **CUSTOMER GOALS THEY SUPPORT**
   - What customer objectives do they help achieve?
   - What success outcomes do they promise?
   - What customer aspirations do they support?

3. **CUSTOMER DECISION FACTORS**
   - What factors do they assume drive customer decisions?
   - What criteria do they think customers use?
   - What objections do they anticipate?

4. **CUSTOMER RELATIONSHIP APPROACH**
   - How do they approach customer relationships?
   - What customer service philosophy do they have?
   - How do they support customers throughout the journey?

5. **CUSTOMER SUCCESS STORIES**
   - What customer success stories do they share?
   - What results do their customers achieve?
   - What customer testimonials do they highlight?

6. **CUSTOMER ENGAGEMENT STRATEGY**
   - How do they engage with customers?
   - What customer touchpoints do they create?
   - How do they build customer loyalty?

OUTPUT FORMAT (JSON only):
{{
  "company_name": "{verified_company_name if verified_company_name else '[extracted from analysis]'}",
  "company_name_verified": {str(verified_company_name is not None).lower() if verified_company_name else 'false'},
  "pain_points_addressed": ["string"],
  "customer_goals_supported": ["string"],
  "decision_factors": ["string"],
  "relationship_approach": "string",
  "success_stories": ["string"],
  "engagement_strategy": "string",
  "customer_philosophy": "string"
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        
        response = await rate_limited_gemini.rate_limited_call(prompt, temperature=0.2, max_tokens=16000, pid=pid)
        
        # Check if response is an error before trying to parse JSON
        # Check for various error formats: "ERROR:", "ERROR ", or contains "503" or "Service Unavailable"
        is_error = False
        if not response:
            is_error = True
        elif isinstance(response, str):
            response_upper = response.upper()
            is_error = (
                response.startswith("ERROR:") or 
                response.startswith("ERROR ") or
                "503" in response or
                "SERVICE UNAVAILABLE" in response_upper or
                "OVERLOADED" in response_upper or
                "UNAVAILABLE" in response_upper
            )
        
        if is_error:
            logger.error(f"Gemini API returned error for customer insights: {response[:200] if response else 'None'}")
            return {}
        
        try:
            # Extract JSON from markdown code blocks if present
            if response and "```json" in response:
                # Extract content between ```json and ```
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            
            # Try direct JSON parsing
            return json.loads(response) if response else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse customer insights JSON: {response[:200] if response else 'None'}")
            return {}
    
    async def _analyze_competitive_positioning(self, website_url: str, website_content: str, business_analysis: Dict,
                                              verified_company_name: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """Analyze competitive positioning and market strategy"""
        
        verified_context = self._build_verified_company_context(website_url, verified_company_name)
        
        prompt = f"""
You are a competitive intelligence analyst examining a company's market positioning.
Analyze the competitive positioning from the following information.
{verified_context}
**TARGET COMPANY:** {verified_company_name if verified_company_name else f"The company that owns {website_url}"}

WEBSITE: {website_url}
WEBSITE CONTENT: {website_content}
BUSINESS ANALYSIS: {json.dumps(business_analysis, indent=2)}

ANALYZE COMPETITIVE POSITIONING:

1. **MARKET POSITION**
   - Where do they position themselves in the market?
   - What market segment do they target?
   - How do they differentiate from competitors?

2. **COMPETITIVE ADVANTAGES**
   - What unique advantages do they claim?
   - What capabilities set them apart?
   - What resources do they leverage?

3. **COMPETITIVE THREATS**
   - What competitive pressures do they face?
   - What market changes affect them?
   - What competitive responses do they prepare for?

4. **MARKET OPPORTUNITIES**
   - What market opportunities do they pursue?
   - What growth areas do they target?
   - What market gaps do they fill?

5. **COMPETITIVE RESPONSE STRATEGY**
   - How do they respond to competition?
   - What competitive moves do they make?
   - How do they defend their position?

OUTPUT FORMAT (JSON only):
{{
  "company_name": "{verified_company_name if verified_company_name else '[extracted from analysis]'}",
  "company_name_verified": {str(verified_company_name is not None).lower() if verified_company_name else 'false'},
  "market_position": "string",
  "target_segment": "string",
  "differentiation": ["string"],
  "competitive_advantages": ["string"],
  "competitive_threats": ["string"],
  "market_opportunities": ["string"],
  "response_strategy": "string"
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        
        response = await rate_limited_gemini.rate_limited_call(prompt, temperature=0.2, max_tokens=16000, pid=pid)
        
        # Check if response is an error before trying to parse JSON
        # Check for various error formats: "ERROR:", "ERROR ", or contains "503" or "Service Unavailable"
        is_error = False
        if not response:
            is_error = True
        elif isinstance(response, str):
            response_upper = response.upper()
            is_error = (
                response.startswith("ERROR:") or 
                response.startswith("ERROR ") or
                "503" in response or
                "SERVICE UNAVAILABLE" in response_upper or
                "OVERLOADED" in response_upper or
                "UNAVAILABLE" in response_upper
            )
        
        if is_error:
            logger.error(f"Gemini API returned error for competitive analysis: {response[:200] if response else 'None'}")
            return {}
        
        try:
            # Extract JSON from markdown code blocks if present
            if response and "```json" in response:
                # Extract content between ```json and ```
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            
            # Try direct JSON parsing
            return json.loads(response) if response else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse competitive analysis JSON: {response[:200] if response else 'None'}")
            return {}
    
    async def _identify_pain_points_and_opportunities(self, website_url: str, website_content: str, business_analysis: Dict,
                                                     verified_company_name: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """Identify specific pain points and opportunities for this customer"""
        
        verified_context = self._build_verified_company_context(website_url, verified_company_name)
        
        prompt = f"""
You are a strategic consultant identifying pain points and opportunities for a specific customer.
Analyze the following information to identify what this customer needs and wants.
{verified_context}
**TARGET COMPANY:** {verified_company_name if verified_company_name else f"The company that owns {website_url}"}

WEBSITE: {website_url}
WEBSITE CONTENT: {website_content}
BUSINESS ANALYSIS: {json.dumps(business_analysis, indent=2)}

IDENTIFY SPECIFIC PAIN POINTS AND OPPORTUNITIES:

1. **OPERATIONAL PAIN POINTS**
   - What operational challenges do they likely face?
   - What inefficiencies might they have?
   - What resource constraints do they have?

2. **STRATEGIC PAIN POINTS**
   - What strategic challenges do they face?
   - What market pressures affect them?
   - What competitive threats do they have?

3. **TECHNOLOGICAL PAIN POINTS**
   - What technology challenges do they have?
   - What digital transformation needs do they have?
   - What integration challenges do they face?

4. **GROWTH OPPORTUNITIES**
   - What growth opportunities do they pursue?
   - What market expansion do they target?
   - What new capabilities do they need?

5. **EFFICIENCY OPPORTUNITIES**
   - What efficiency improvements do they need?
   - What cost optimization opportunities exist?
   - What process improvements do they need?

6. **INNOVATION OPPORTUNITIES**
   - What innovation areas do they focus on?
   - What new technologies do they need?
   - What product development opportunities exist?

OUTPUT FORMAT (JSON only):
{{
  "company_name": "{verified_company_name if verified_company_name else '[extracted from analysis]'}",
  "company_name_verified": {str(verified_company_name is not None).lower() if verified_company_name else 'false'},
  "operational_pain_points": ["string"],
  "strategic_pain_points": ["string"],
  "technological_pain_points": ["string"],
  "growth_opportunities": ["string"],
  "efficiency_opportunities": ["string"],
  "innovation_opportunities": ["string"],
  "priority_areas": ["string"]
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        
        response = await rate_limited_gemini.rate_limited_call(prompt, temperature=0.2, max_tokens=16000, pid=pid)
        
        # Check if response is an error before trying to parse JSON
        # Check for various error formats: "ERROR:", "ERROR ", or contains "503" or "Service Unavailable"
        is_error = False
        if not response:
            is_error = True
        elif isinstance(response, str):
            response_upper = response.upper()
            is_error = (
                response.startswith("ERROR:") or 
                response.startswith("ERROR ") or
                "503" in response or
                "SERVICE UNAVAILABLE" in response_upper or
                "OVERLOADED" in response_upper or
                "UNAVAILABLE" in response_upper
            )
        
        if is_error:
            logger.error(f"Gemini API returned error for pain points analysis: {response[:200] if response else 'None'}")
            return {}
        
        try:
            # Extract JSON from markdown code blocks if present
            if response and "```json" in response:
                # Extract content between ```json and ```
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            
            # Try direct JSON parsing
            return json.loads(response) if response else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse pain points analysis JSON: {response[:200] if response else 'None'}")
            return {}
    
    async def _generate_targeted_persona_insights(self, website_url: str, website_content: str, 
                                                business_analysis: Dict, customer_insights: Dict,
                                                competitive_analysis: Dict, pain_points_analysis: Dict,
                                                verified_company_name: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """Generate targeted persona insights based on all analyses"""
        
        verified_context = self._build_verified_company_context(website_url, verified_company_name)
        company_name_placeholder = verified_company_name if verified_company_name else '[extracted from analysis]'
        company_name_verified_value = str(verified_company_name is not None).lower() if verified_company_name else 'false'
        
        prompt = f"""
You are a B2B buyer persona specialist creating targeted insights for a specific customer.
Based on the comprehensive analysis below, generate specific persona insights.
{verified_context}
**TARGET COMPANY:** {verified_company_name if verified_company_name else f"The company that owns {website_url}"}

WEBSITE: {website_url}
WEBSITE CONTENT: {website_content}
BUSINESS ANALYSIS: {json.dumps(business_analysis, indent=2)}
CUSTOMER INSIGHTS: {json.dumps(customer_insights, indent=2)}
COMPETITIVE ANALYSIS: {json.dumps(competitive_analysis, indent=2)}
PAIN POINTS ANALYSIS: {json.dumps(pain_points_analysis, indent=2)}

GENERATE TARGETED PERSONA INSIGHTS:

1. **SPECIFIC PAIN POINTS** (based on their business model and challenges)
2. **SPECIFIC GOALS** (based on their strategic objectives and opportunities)
3. **VALUE DRIVERS** (what they prioritize based on their positioning)
4. **VALUE SIGNALS** (how they evaluate solutions based on their approach)
5. **LIKELY OBJECTIONS** (based on their decision-making process and constraints)
6. **BUYER ARCHETYPE** (based on their business characteristics and approach)
7. **PRICE SENSITIVITY** (based on their business model and market position)

OUTPUT FORMAT (JSON only):
{{
  "company_name": "{company_name_placeholder}",
  "company_name_verified": {company_name_verified_value},
  "pain_points": ["string (specific to this customer)"],
  "goals": ["string (specific to this customer)"],
  "value_drivers": ["string (specific to this customer)"],
  "value_signals": ["string (specific to this customer)"],
  "likely_objections": ["string (specific to this customer)"],
  "buyer_archetype": "string (Value Buyer|Relationship Buyer|Innovation Seeker|Risk Avoider|Service-Oriented)",
  "price_sensitivity_score": "int (1-10)",
  "price_sensitivity_rationale": "string",
  "decision_making_process": "string",
  "key_influencers": ["string"],
  "success_criteria": ["string"],
  "risk_factors": ["string"],
  "chain_of_thought": "string (detailed reasoning for all insights)"
}}

CRITICAL: 
- Make ALL insights specific to THIS customer, not generic
- Base insights on their actual business model, challenges, and approach
- Provide detailed reasoning in chain_of_thought
- Output ONLY valid JSON. No additional text or formatting.
"""
        
        response = await rate_limited_gemini.rate_limited_call(prompt, temperature=0.3, max_tokens=16000, pid=pid)
        
        # Check if response is an error before trying to parse JSON
        # Check for various error formats: "ERROR:", "ERROR ", or contains "503" or "Service Unavailable"
        is_error = False
        if not response:
            is_error = True
        elif isinstance(response, str):
            response_upper = response.upper()
            is_error = (
                response.startswith("ERROR:") or 
                response.startswith("ERROR ") or
                "503" in response or
                "SERVICE UNAVAILABLE" in response_upper or
                "OVERLOADED" in response_upper or
                "UNAVAILABLE" in response_upper
            )
        
        if is_error:
            logger.error(f"Gemini API returned error for persona insights: {response[:200] if response else 'None'}")
            return {}
        
        try:
            # Extract JSON from markdown code blocks if present
            if response and "```json" in response:
                # Extract content between ```json and ```
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            
            # Try direct JSON parsing
            return json.loads(response) if response else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse persona insights JSON: {response[:200] if response else 'None'}")
            return {}

    async def _validate_company_focus(self, website_url: str, content: str) -> Dict[str, Any]:
        """Validate that the content is about the correct company"""
        
        # Extract domain from URL for better validation
        from urllib.parse import urlparse
        parsed_url = urlparse(website_url)
        domain = parsed_url.netloc or parsed_url.path.split('/')[0]
        domain_base = domain.replace('www.', '').split('/')[0]
        
        prompt = f"""
You are a validation specialist. Your task is to verify that the provided content is about the correct company that OWNS the specific domain.

WEBSITE URL: {website_url}
DOMAIN: {domain_base}
CONTENT TO VALIDATE: {content[:2000]}...

**CRITICAL VALIDATION TASK:**
1. Extract the domain from the URL: {domain_base}
2. Identify which company actually OWNS this specific domain (not just companies with similar names)
3. Check if the content is about the company that owns {domain_base}
4. Verify the company name in the content matches the domain owner
5. Watch for common mistakes:
   - Analyzing "Kramer Electronics" (AV company) when domain is "kramer-online.com" (should be "Kramer-Werke GmbH")
   - Analyzing similarly-named companies that don't own the domain
   - Confusing different companies with the same or similar names

**VALIDATION CRITERIA:**
- The content must be about the company that owns {domain_base}
- Company name in content must match the domain owner
- Products/services mentioned must align with the domain owner's business
- Location/headquarters must match the domain owner's location

**OUTPUT FORMAT (JSON only):**
{{
  "is_correct_company": boolean,
  "extracted_domain": "{domain_base}",
  "content_company_name": "string (exact name from content)",
  "domain_owner_company": "string (who actually owns the domain)",
  "confidence_score": "int (1-10)",
  "reasoning": "string (explain why it matches or doesn't match)",
  "warning": "string (if there's a mismatch, explain what company was analyzed instead)"
}}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
        
        try:
            # Increased token limit to prevent truncation - validation responses can be complex
            response = await rate_limited_gemini.rate_limited_call(prompt, temperature=0.1, max_tokens=8000, pid=0)
            
            # Check if response is an error before trying to parse JSON
            # Check for various error formats: "ERROR:", "ERROR ", or contains "503" or "Service Unavailable"
            is_error = False
            if not response:
                is_error = True
            elif isinstance(response, str):
                response_upper = response.upper()
                is_error = (
                    response.startswith("ERROR:") or 
                    response.startswith("ERROR ") or
                    "503" in response or
                    "SERVICE UNAVAILABLE" in response_upper or
                    "OVERLOADED" in response_upper or
                    "UNAVAILABLE" in response_upper
                )
            
            if is_error:
                logger.error(f"Gemini API returned error for validation: {response[:200] if response else 'None'}")
                return {"is_correct_company": False}
            
            # Extract JSON from markdown code blocks if present
            json_content = None
            if response and "```json" in response:
                # Extract content between ```json and ```
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                else:
                    # If closing ``` not found, try to extract everything after ```json
                    json_content = response[start:].strip()
                    # Remove any trailing markdown or text
                    json_content = json_content.split('\n')[0] if '\n' in json_content else json_content
            
            # If no markdown block, try to find JSON object in response
            if not json_content:
                # Try to find JSON object using regex
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                else:
                    json_content = response.strip()
            
            # Try to fix incomplete JSON (add missing closing braces)
            if json_content:
                # Count opening and closing braces
                open_braces = json_content.count('{')
                close_braces = json_content.count('}')
                if open_braces > close_braces:
                    # Add missing closing braces
                    json_content += '}' * (open_braces - close_braces)
                    logger.warning(f"Fixed incomplete JSON by adding {open_braces - close_braces} closing brace(s)")
            
            # Try to parse JSON
            if json_content:
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error, trying to extract partial data: {e}")
                    # Try to extract at least the critical fields even if JSON is malformed
                    result: Dict[str, Any] = {"is_correct_company": False}
                    # Try to extract key fields using regex as fallback
                    domain_match = re.search(r'"extracted_domain"\s*:\s*"([^"]+)"', json_content)
                    if domain_match:
                        result["extracted_domain"] = domain_match.group(1)
                    company_match = re.search(r'"content_company_name"\s*:\s*"([^"]+)"', json_content)
                    if company_match:
                        result["content_company_name"] = company_match.group(1)
                    domain_owner_match = re.search(r'"domain_owner_company"\s*:\s*"([^"]+)"', json_content)
                    if domain_owner_match:
                        result["domain_owner_company"] = domain_owner_match.group(1)
                    is_correct_match = re.search(r'"is_correct_company"\s*:\s*(true|false)', json_content, re.IGNORECASE)
                    if is_correct_match:
                        result["is_correct_company"] = bool(is_correct_match.group(1).lower() == 'true')
                    logger.info(f"Extracted partial validation data: {result}")
                    return result
            
            # Fallback if all parsing fails
            logger.error(f"Failed to extract JSON from response: {response[:300] if response else 'None'}")
            return {"is_correct_company": False}
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation JSON: {str(e)}. Response: {response[:300] if response else 'None'}")
            return {"is_correct_company": False}
        except Exception as e:
            logger.error(f"Unexpected error parsing validation JSON: {str(e)}. Response: {response[:300] if response else 'None'}")
            return {"is_correct_company": False}

# Global instance
enhanced_website_analyzer = EnhancedWebsiteAnalyzer() 