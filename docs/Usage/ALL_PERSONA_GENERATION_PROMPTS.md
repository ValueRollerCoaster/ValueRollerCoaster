# Complete AI Prompts Used in Buyer Persona Generation

This document lists **all AI prompts** used throughout the 8-step buyer persona generation process. Prompts are organized by step and include which AI model they use.

---

## 📋 Table of Contents

1. [System-Wide Prompt Templates](#system-wide-prompt-templates)
2. [Step 0: Relevance Validation](#step-0-relevance-validation)
3. [Step 1: Dual-Model Website Analysis](#step-1-dual-model-website-analysis)
4. [Step 1.5: Sonar Website Validation](#step-15-sonar-website-validation)
5. [Step 2: Cross-Model Validation & Synthesis](#step-2-cross-model-validation--synthesis)
6. [Step 2.5: Sonar Cross-Model Validation](#step-25-sonar-cross-model-validation)
7. [Step 3: Enhanced Market Intelligence](#step-3-enhanced-market-intelligence)
8. [Step 3.5: Sonar Market Intelligence Validation](#step-35-sonar-market-intelligence-validation)
9. [Step 4: Value Alignment Workflow](#step-4-value-alignment-workflow)
10. [Step 4.5: Sonar Value Alignment Validation](#step-45-sonar-value-alignment-validation)
11. [Step 5: Creative Persona Elements](#step-5-creative-persona-elements)
12. [Step 5.5: Sonar Creative Elements Validation](#step-55-sonar-creative-elements-validation)
13. [Step 6: Final Persona Synthesis](#step-6-final-persona-synthesis)
14. [Step 6.5: Sonar Final Synthesis Validation](#step-65-sonar-final-synthesis-validation)
15. [Step 7: Quality Assurance](#step-7-quality-assurance)
16. [Step 8: Final Sonar Quality Check](#step-8-final-sonar-quality-check)

---

## System-Wide Prompt Templates

### **SYSTEM_MESSAGE** (Used in legacy prompts)

**Location**: `app/ai/prompts.py`

**Purpose**: Universal instructions for JSON-only output

**Content**:
```
CRITICAL: Output ONLY a valid JSON object. Do NOT use YAML, Markdown, or any other format. If you do not output valid JSON, your answer will be ignored and considered invalid.
You are a JSON generator. Your task is to analyze the provided information and generate a valid JSON response.
CRITICAL: Output ONLY a valid JSON object. Do not include any other text, instructions, or formatting.

JSON RULES:
- Use double quotes for strings and property names
- Use float values for numbers
- Use proper JSON array syntax
- Do not include any text before or after the JSON
- Do not include any comments or explanations
- Ensure all required fields are present
- Ensure all values are properly formatted
- CRITICAL: Numerical values must be literal numbers (integers or floats), not expressions or calculations.
- CRITICAL: NEVER use calculation expressions like (100 - 50) or (x * y). Always provide the final calculated number.
- CRITICAL: For percentages, use numbers between 0-100, not expressions like (100 - x).

Example of valid JSON:
{
    "name": "Example Corp",
    "value": 123.45,
    "items": ["item1", "item2"]
}
```

**Used by**: Legacy persona generation prompts

---

## Step 0: Relevance Validation

### **Step 0: Pre-Analysis Relevance Validation (Sonar)**

**Model**: Sonar (Gemini with web search + domain filtering)

**Location**: `app/ai/enhanced_persona_generator.py` → `_step_0_relevance_validation()` → Calls `quality_gates.step_0_relevance_validation()`

**Purpose**: Determine if the target company is relevant before investing processing resources

**Prompt Location**: `app/ai/sonar/company_profile_validator.py`

**Note**: The actual prompt is built dynamically by `_build_relevance_prompt()` method, which:
- Extracts domain from website URL
- Filters web search to target domain only (prevents hallucination)
- Checks if company uses/could use products/services related to your business

**Example Prompt Structure**:
```
You are a business relevance analyst. Your task is to determine if a company is relevant to our business.

TARGET WEBSITE: {website_url}

SEARCH DOMAIN FILTER: Only search within {target_domain} to prevent hallucination.

RELEVANCE CRITERIA:
- Does the company use or could use products/services related to our business?
- Are they in an industry we serve?
- Do they have needs that our solutions address?

RETURN JSON:
{
  "is_relevant": true/false,
  "relevance_score": 0-10,
  "relevance_type": "string",
  "business_relationship": "string",
  "why_not_relevant": "string (if not relevant)"
}
```

**Returns**: 
- `is_relevant`: Boolean
- `relevance_score`: 0-10
- `recommended_action`: "proceed" or "reject"

---

## Step 1: Dual-Model Website Analysis

### **1A. Gemini Website Analysis**

**Model**: Gemini (with web search enabled)

**Location**: `app/ai/enhanced_persona_generator.py` → `_gemini_website_analysis()`

**Primary Analysis**: Uses `enhanced_website_analyzer.analyze_website_deep()` (separate prompt system)

**Additional Insights Prompt**:
```python
gemini_insights_prompt = f"""
Based on the website analysis of {website}, provide additional strategic insights:

**Analysis Data:**
{json.dumps(analysis, indent=2)}

**Additional Analysis Request:**
1. Strategic positioning analysis
2. Technology stack insights
3. Competitive differentiation factors
4. Growth trajectory indicators
5. Risk assessment

Provide insights as a JSON object with these fields:
- strategic_positioning: string
- technology_insights: string
- competitive_differentiation: string
- growth_indicators: string
- risk_assessment: string
"""
```

**Output**: Enhanced website analysis with additional Gemini-specific strategic insights

---

### **1B. ChatGPT Website Analysis**

**Model**: ChatGPT (with web search enabled)

**Location**: `app/ai/enhanced_persona_generator.py` → `_chatgpt_website_analysis()`

**Prompt**:
```python
chatgpt_prompt = f"""
Conduct a comprehensive analysis of the company website at {website} with web search grounding.

**Analysis Requirements:**
1. Company Overview (name, history, size, location)
2. Products & Services (detailed portfolio, features, applications)
3. Customer Segments (target customers, industries served)
4. Value Propositions (problems solved, benefits offered)
5. Market Positioning (differentiation, brand messaging)
6. Business Model (revenue streams, sales channels)
7. Technology & Innovation (tech stack, R&D focus)
8. Challenges & Opportunities (industry challenges, growth strategies)

**Additional ChatGPT-Specific Analysis:**
1. Creative market positioning insights
2. Innovative business model elements
3. Future growth opportunities
4. Customer experience analysis
5. Digital transformation readiness

Provide analysis as a JSON object with these fields:
- company_overview: object
- products_services: object
- customer_segments: object
- value_propositions: object
- market_positioning: object
- business_model: object
- technology_innovation: object
- challenges_opportunities: object
- chatgpt_creative_insights: object
"""
```

**Output**: Comprehensive website analysis with creative insights

---

## Step 1.5: Sonar Website Validation

### **Website Analysis Validation**

**Model**: Sonar (Gemini with web search + domain filtering)

**Location**: `app/ai/sonar/enhanced_validation.py` → `validate_website_analysis()`

**Prompt**:
```python
prompt = f"""
WEBSITE ANALYSIS VALIDATION: {website_url}

TASK: Validate and fact-check the website analysis results from two AI models.

GEMINI CLAIMS:
{json.dumps(gemini_claims, indent=2)}

CHATGPT CLAIMS:
{json.dumps(chatgpt_claims, indent=2)}

VALIDATION INSTRUCTIONS:
1. Search for information about {website_url} specifically
2. Verify each claim against authoritative sources
3. Identify any factual errors or hallucinations
4. Provide confidence scores for each claim
5. Suggest corrections for any errors found

Return JSON with:
{
    "validation_passed": true/false,
    "overall_confidence": 1-10,
    "verified_elements": ["element1", "element2"],
    "missing_elements": ["element1", "element2"],
    "synthesis_corrections": ["correction1", "correction2"],
    "validation_notes": "string"
}
"""
```

**Returns**: Validation results with confidence scores and corrections

---

### **Customer Focus Validation**

**Model**: Sonar (Gemini with web search)

**Location**: `app/ai/enhanced_persona_generator.py` → `_step_1_customer_focus_validation()` → Calls `quality_gates.step_1_customer_focus_validation()`

**Purpose**: Validate that analysis correctly identifies customer focus (B2B vs B2C)

**Note**: Prompt is built dynamically by Sonar quality gates

**Returns**: 
- `customer_focus_correct`: Boolean
- `confidence_score`: 1-10
- `should_proceed`: Boolean

---

## Step 2: Cross-Model Validation & Synthesis

### **Cross-Model Synthesis Prompt**

**Model**: Gemini

**Location**: `app/ai/enhanced_persona_generator.py` → `_cross_validate_and_synthesize()`

**Prompt**:
```python
synthesis_prompt = f"""
Compare and synthesize the analysis results from two AI models for the website {website}.

**Gemini Analysis (Analytical Focus):**
{json.dumps(gemini_analysis, indent=2)}

**ChatGPT Analysis (Creative Focus):**
{json.dumps(chatgpt_analysis, indent=2)}

**CRITICAL SYNTHESIS TASK:**
You must extract SPECIFIC, MEANINGFUL insights from both analyses. Do NOT return empty arrays.

1. **Areas of Agreement (Minimum 5-10 points):**
   - Find specific insights that BOTH models identified about the company
   - Focus on business model, target customers, products/services, challenges, opportunities
   - Be specific and detailed, not generic

2. **Unique Gemini Insights (Minimum 3-5 points):**
   - Extract analytical insights that ONLY Gemini identified
   - Focus on technical details, market analysis, competitive positioning
   - Include specific data points, metrics, or analytical observations

3. **Unique ChatGPT Insights (Minimum 3-5 points):**
   - Extract creative insights that ONLY ChatGPT identified
   - Focus on innovative perspectives, future opportunities, creative solutions
   - Include unique angles, creative suggestions, or novel observations

4. **Validation Process:**
   - Explain how you compared the two analyses
   - Describe what makes each insight unique or shared
   - Provide confidence score based on analysis quality

**REQUIRED OUTPUT FORMAT (JSON only):**
{
  "unified_analysis": {
    "company_overview": "Combined company description",
    "business_model": "Synthesized business model",
    "target_customers": "Combined customer segments",
    "products_services": "Combined offerings",
    "challenges_opportunities": "Synthesized insights"
  },
  "agreement_areas": [
    "Specific insight both models identified about business model",
    "Specific insight both models identified about target customers", 
    "Specific insight both models identified about products/services",
    "Specific insight both models identified about market position",
    "Specific insight both models identified about challenges",
    "Specific insight both models identified about opportunities"
  ],
  "unique_gemini_insights": [
    "Specific analytical insight only Gemini identified",
    "Specific technical detail only Gemini found",
    "Specific market analysis only Gemini provided",
    "Specific competitive insight only Gemini discovered"
  ],
  "unique_chatgpt_insights": [
    "Specific creative insight only ChatGPT identified",
    "Specific innovative perspective only ChatGPT found",
    "Specific future opportunity only ChatGPT suggested",
    "Specific creative solution only ChatGPT proposed"
  ],
  "confidence_score": 85,
  "validation_notes": "Detailed explanation of how I compared the analyses and identified agreement areas vs unique insights. I focused on extracting specific, actionable insights rather than generic observations."
}

**IMPORTANT:** 
- Return ONLY valid JSON, no additional text
- Ensure ALL arrays have meaningful content (no empty arrays)
- Be specific and detailed in all insights
- Focus on actionable, business-relevant information
"""
```

**Output**: Unified analysis with agreement areas and unique insights from each model

---

## Step 2.5: Sonar Cross-Model Validation

### **Cross-Model Validation**

**Model**: Sonar (Gemini with web search)

**Location**: `app/ai/enhanced_persona_generator.py` → `_step_2_sonar_cross_validation()`

**Purpose**: Validate cross-model synthesis and determine which model's output is more reliable

**Note**: Prompt is built dynamically by Sonar quality gates

**Returns**:
- `models_agree`: Boolean
- `recommended_synthesis`: "gemini_primary", "chatgpt_primary", or "balanced"
- `confidence_score`: 1-10

---

## Step 3: Enhanced Market Intelligence

### **Base Market Intelligence Prompt**

**Model**: Gemini

**Location**: `app/ai/market_intelligence/market_intelligence_service.py` → `get_comprehensive_market_intelligence()`

**Prompt**:
```python
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
{
  "market_overview": {
    "market_size": {
      "global": "string (e.g., €50B)",
      "european": "string (e.g., €15B)",
      "growth_rate": "string (e.g., 5.2% annually)",
      "projection_5y": "string (e.g., €20B by 2029)"
    },
    "market_maturity": "string (Emerging|Growing|Mature|Declining)",
    "key_segments": ["string", ...],
    "regional_variations": ["string", ...]
  },
  "current_trends": [
    {
      "trend": "string",
      "impact": "string (High|Medium|Low)",
      "description": "string",
      "business_implications": "string"
    }
  ],
  "competitive_landscape": {
    "key_competitors": [
      {
        "name": "string",
        "positioning": "string",
        "strengths": ["string", ...],
        "weaknesses": ["string", ...],
        "market_share": "string (estimated)"
      }
    ],
    "competitive_advantages": ["string", ...],
    "competitive_threats": ["string", ...],
    "market_positioning": "string"
  },
  "technology_adoption": {
    "current_adoption": ["string", ...],
    "emerging_technologies": ["string", ...],
    "adoption_barriers": ["string", ...],
    "investment_priorities": ["string", ...]
  },
  "sustainability_initiatives": {
    "current_practices": ["string", ...],
    "regulatory_pressure": ["string", ...],
    "customer_demand": ["string", ...],
    "investment_opportunities": ["string", ...]
  },
  "market_opportunities": ["string", ...],
  "risk_factors": ["string", ...],
  "strategic_recommendations": ["string", ...],
  "summary": "string"
}

Base your analysis on current market knowledge, industry reports, and best practices.
Provide realistic estimates and actionable insights for B2B decision making.
"""
```

**Temperature**: 0.3

**Output**: Comprehensive market intelligence JSON structure

---

### **ChatGPT Creative Market Insights**

**Model**: ChatGPT (with web search enabled)

**Location**: `app/ai/enhanced_persona_generator.py` → `_generate_enhanced_market_intelligence()`

**Prompt**:
```python
chatgpt_market_prompt = f"""
Based on the market intelligence and company analysis, provide creative market insights:

**Company Analysis:**
{json.dumps(validated_analysis.get("unified_analysis", {}), indent=2)}

**Base Market Intelligence:**
{json.dumps(base_intelligence, indent=2)}

**Creative Market Analysis Request:**
1. Emerging market trends specific to this company
2. Innovative strategies and opportunities
3. Untapped market potential
4. Future scenarios and disruptive impacts
5. Creative competitive positioning

Provide insights as a JSON object with these fields:
- emerging_trends: array
- innovative_strategies: array
- untapped_opportunities: array
- future_scenarios: array
- disruptive_impacts: array
"""
```

**Output**: Creative market insights to enhance base intelligence

---

## Step 3.5: Sonar Market Intelligence Validation

### **Market Intelligence Validation**

**Model**: Sonar (Gemini with web search + industry domain filtering)

**Location**: `app/ai/sonar/enhanced_validation.py` → `validate_market_intelligence()`

**Prompt**:
```python
prompt = f"""
MARKET INTELLIGENCE VALIDATION: {website_url}

INDUSTRY: {industry}

TASK: Validate market intelligence analysis against current market data.

MARKET INTELLIGENCE CLAIMS:
{json.dumps(market_claims, indent=2)}

VALIDATION INSTRUCTIONS:
1. Search for current market trends in {industry} industry
2. Verify market size, growth rates, and competitive landscape
3. Check for recent industry developments and news
4. Validate competitive positioning claims
5. Verify market opportunity assessments

Return JSON with:
{
    "validation_passed": true/false,
    "overall_confidence": 1-10,
    "verified_claims": ["claim1", "claim2"],
    "questionable_claims": ["claim1", "claim2"],
    "validation_notes": "string"
}
"""
```

**Output**: Validation results with confidence scores

---

## Step 4: Value Alignment Workflow

The value alignment step uses a **3-agent sequential workflow**. Each agent's output becomes input to the next.

---

### **4.1: Profiler Agent**

**Model**: ChatGPT

**Location**: `app/ai/value_alignment.py` → `_run_profiler_agent()`

**Prompt**:
```python
prompt = f"""
You are a Company Profiler. Analyze the following business summary and extract key strategic insights.

**Business Summary:**
{company_summary}

**Your Task:**
Produce a JSON object with the following fields:
- `key_goals`: A list of the company's most important stated or implied goals.
- `implicit_challenges`: A list of challenges the company is likely facing, based on the text.
- `overall_sentiment`: A single phrase describing the company's strategic focus (e.g., "Cost-Cutting & Efficiency", "Innovation & Market Expansion").

**JSON Output:**
"""
```

**Temperature**: 0.2  
**Max Tokens**: 16384

**Output**: Profiler analysis with key goals, implicit challenges, and overall sentiment

---

### **4.2: Hypothesizer Agent**

**Model**: ChatGPT

**Location**: `app/ai/value_alignment.py` → `_run_hypothesizer_agent()`

**Prompt**:
```python
prompt = f"""
You are a Strategy Hypothesizer. A company has been profiled, and now you must select which of our value components are the most promising fit.

**Company Profile:**
{json.dumps(profiler_analysis, indent=2)}

**Our Value Components (with Importance Score 0-3):**
{json.dumps(our_value_components, indent=2)}

**Your Task:**
Produce a JSON object with the following fields:
- `hypothesis_rationale`: A brief explanation of your reasoning. Why are you choosing these components? Refer to the company's sentiment and our components' importance scores.
- `shortlist`: A list of the names of the top 3-10 most relevant value components to investigate further.

**JSON Output:**
"""
```

**Temperature**: 0.2  
**Max Tokens**: 16384

**Output**: Hypothesis analysis with rationale and shortlist of value components

---

### **4.3: Final Aligner Agent**

**Model**: ChatGPT

**Location**: `app/ai/value_alignment.py` → `_run_final_aligner_agent()` → Uses `enhanced_prompt_builder.build_enhanced_value_alignment_prompt()`

**Enhanced Prompt Builder Location**: `app/ai/enhanced_prompts.py`

**Prompt**:
```python
prompt = f"""
You are an expert B2B value consultant specializing in {industry_name} industry. Your task is to create a strategic value alignment matrix between a prospect and our company.

INDUSTRY CONTEXT FOR {industry_name.upper()}>
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
{
  "alignment_matrix": [
    {
      "prospect_need": "string",
      "our_value_component": "string", 
      "rationale": "string",
      "match_score_percent": int (0-100),
      "conversation_starter": "string",
      "industry_relevance": "string",
      "market_context": "string"
    }
  ],
  "unmatched_needs": ["string", ...],
  "industry_opportunities": ["string", ...],
  "competitive_advantages": ["string", ...],
  "market_risks": ["string", ...],
  "strategic_recommendations": ["string", ...]
}

CRITICAL: Output ONLY valid JSON. No additional text or formatting.
"""
```

**Temperature**: 0.2  
**Max Tokens**: 16384

**Output**: Alignment matrix with prospect needs matched to value components

---

### **4.4: ChatGPT Creative Value Insights**

**Model**: ChatGPT (with web search enabled)

**Location**: `app/ai/enhanced_persona_generator.py` → `_generate_enhanced_value_alignment()`

**Prompt**:
```python
chatgpt_value_prompt = f"""
Based on the company analysis and value components, generate creative value propositions:

**Company Analysis:**
{json.dumps(company_summary, indent=2)}

**Value Components:**
{json.dumps(our_value_components, indent=2)}

**Creative Value Proposition Request:**
1. Innovative value propositions for each component
2. Unique selling angles
3. Creative positioning strategies
4. Emotional appeals
5. Future-focused value drivers

Provide insights as a JSON object with these fields:
- creative_value_propositions: array
- unique_selling_angles: array
- positioning_strategies: array
- emotional_appeals: array
- future_value_drivers: array
"""
```

**Output**: Creative value insights to enhance alignment matrix

---

## Step 4.5: Sonar Value Alignment Validation

### **Value Alignment Validation**

**Model**: Sonar (Gemini with web search + domain filtering)

**Location**: `app/ai/sonar/enhanced_validation.py` → `validate_value_alignment()`

**Prompt**:
```python
prompt = f"""
VALUE ALIGNMENT VALIDATION: {website_url}

TASK: Validate value alignment analysis against company information.

VALUE ALIGNMENT CLAIMS:
{json.dumps(value_claims, indent=2)}

VALIDATION INSTRUCTIONS:
1. Search for information about {website_url} business needs
2. Verify pain points and challenges mentioned
3. Check if value drivers align with company profile
4. Validate opportunity assessments
5. Verify strategic recommendations

Return JSON with:
{
    "validation_passed": true/false,
    "overall_confidence": 1-10,
    "verified_value_insights": ["insight1", "insight2"],
    "questionable_assessments": ["assessment1", "assessment2"],
    "validation_notes": "string"
}
"""
```

**Output**: Validation results for value alignment

---

## Step 5: Creative Persona Elements

### **Creative Persona Elements Prompt**

**Model**: ChatGPT (with web search enabled)

**Location**: `app/ai/enhanced_persona_generator.py` → `_generate_creative_persona_elements()`

**Prompt**:
```python
creative_prompt = f"""
Generate creative and innovative persona elements based on the analysis:

**Validated Analysis:**
{json.dumps(validated_analysis, indent=2)}

**Market Intelligence:**
{json.dumps(market_intelligence, indent=2)}

**Creative Persona Elements Request:**
1. Innovative pain point formulations
2. Creative goal statements
3. Unique value driver insights
4. Emotional decision factors
5. Future-focused objectives
6. Creative objection handling
7. Innovative success metrics

Provide insights as a JSON object with these fields:
- innovative_pain_points: array
- creative_goals: array
- unique_value_drivers: array
- emotional_factors: array
- future_objectives: array
- creative_objections: array
- success_metrics: array
"""
```

**Output**: Creative persona elements (pain points, goals, value drivers, etc.)

---

## Step 5.5: Sonar Creative Elements Validation

### **Creative Elements Validation**

**Model**: Sonar (Gemini with web search + domain filtering)

**Location**: `app/ai/sonar/enhanced_validation.py` → `validate_creative_elements()`

**Prompt**:
```python
prompt = f"""
CREATIVE ELEMENTS VALIDATION: {website_url}

TASK: Validate creative persona elements for relevance and accuracy.

CREATIVE ELEMENTS:
{json.dumps(creative_claims, indent=2)}

VALIDATION INSTRUCTIONS:
1. Check if creative elements align with company profile
2. Verify emotional factors and pain points are realistic
3. Validate goals and objectives are appropriate
4. Check if creative insights are grounded in reality
5. Ensure elements are relevant to the target company

Return JSON with:
{
    "validation_passed": true/false,
    "overall_confidence": 1-10,
    "validated_elements": ["element1", "element2"],
    "questionable_elements": ["element1", "element2"],
    "validation_notes": "string"
}
"""
```

**Output**: Validation results for creative elements

---

## Step 6: Final Persona Synthesis

### **Final Persona Synthesis Prompt**

**Model**: Gemini

**Location**: `app/ai/enhanced_persona_generator.py` → `_synthesize_final_persona()`

**Prompt**:
```python
synthesis_prompt = f"""
Synthesize all analysis into a comprehensive buyer persona JSON object.

**Validated Analysis:**
{json.dumps(validated_analysis, indent=2)}

**Market Intelligence:**
{json.dumps(market_intelligence, indent=2)}

**Value Alignment:**
{json.dumps(value_alignment, indent=2)}

**Creative Elements:**
{json.dumps(creative_elements, indent=2)}

**CRITICAL: You must respond with ONLY valid JSON. No additional text before or after the JSON.**

**Required JSON Structure (exact format required):**
{
  "company": {
    "name": "string",
    "year_established": integer,
    "headquarters_location": "string", 
    "website": "string"
  },
  "product_range": ["string", "string", "string"],
  "services": ["string", "string", "string"],
  "target_market": "string (EXPLICIT description of target market, customer segments, industries served, geographic focus)",
  "business_model": "string (EXPLICIT description of revenue model, sales channels, pricing strategy)",
  "pain_points": ["string", "string", "string"],
  "goals": ["string", "string", "string"],
  "challenges": ["string (distinct from pain_points - external challenges like regulatory changes, market shifts, competitive threats)"],
  "value_drivers": ["string", "string", "string"],
  "value_signals": ["string", "string", "string"],
  "likely_objections": ["string", "string", "string"],
  "chain_of_thought": "string"
}

**Synthesis Instructions:**
1. Combine insights from all sources
2. Prioritize validated analysis
3. Incorporate creative elements where appropriate
4. Ensure specificity to this company
5. Use bullet point format for all arrays
6. Provide comprehensive reasoning in chain_of_thought
7. **CRITICAL: Extract and explicitly state target_market from business_analysis.target_customers**
   - Include: Primary customer segments, industries served, geographic focus
   - Format: Single comprehensive string (e.g., "B2B customers in manufacturing, warehousing, and logistics sectors, including automotive, food and beverage, pharmaceuticals, and e-commerce. Key personas include Logistics Managers, Warehouse Managers, Operations Directors.")
8. **CRITICAL: Extract and explicitly state business_model from business_analysis.business_model**
   - Include: Revenue streams, sales channels, pricing strategy
   - Format: Single comprehensive string (e.g., "Product sales (forklift trucks, warehouse equipment) and service sales (maintenance, training, financing). Revenue through direct sales, dealer network, and flexible procurement options (purchase, leasing, rental). Value-based pricing strategy.")
9. **CRITICAL: Include challenges field (distinct from pain_points) - external factors affecting the company**
   - Extract from: validated_analysis.business_analysis.challenges_opportunities
   - Include: External challenges (regulatory changes, market shifts, competitive threats, supply chain disruptions)
   - Format: Array of strings (distinct from pain_points which are internal operational issues)
10. **CRITICAL: Include ALL value drivers - do not truncate or summarize this list**
11. **CRITICAL: Each field must contain complete information - use full descriptions, not summaries**
12. IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text
"""
```

**Max Tokens**: 32000 (to prevent truncation)

**Output**: Complete buyer persona JSON structure

---

## Step 6.5: Sonar Final Synthesis Validation

### **Final Synthesis Validation**

**Model**: Sonar (Gemini with web search + domain filtering)

**Location**: `app/ai/sonar/enhanced_validation.py` → `validate_final_synthesis_content()`

**Prompt**:
```python
prompt = f"""
FINAL SYNTHESIS VALIDATION: {website_url}

TASK: Validate the final synthesized persona for completeness and accuracy.

FINAL PERSONA CLAIMS:
{json.dumps(persona_claims, indent=2)}

VALIDATION INSTRUCTIONS:
1. Verify all key persona elements are accurate
2. Check for completeness of information
3. Validate logical consistency
4. Ensure relevance to target company
5. Check for any missing critical information

Return JSON with:
{
    "validation_passed": true/false,
    "overall_confidence": 1-10,
    "completeness_score": 1-10,
    "accuracy_score": 1-10,
    "issues_found": ["issue1", "issue2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "validation_notes": "string"
}
"""
```

**Output**: Final validation results with completeness and accuracy scores

---

## Step 7: Quality Assurance

**Model**: Python code (no AI prompt)

**Location**: `app/ai/enhanced_persona_generator.py` → `_quality_assurance_and_enhancement()`

**Purpose**: Extract alignment matrix from nested structures, ensure data accessibility, add metadata

**Note**: This step uses Python code, not AI prompts. It performs:
- Deep search for `alignment_matrix` in nested structures
- Data extraction and restructuring
- Metadata addition (generation method, models used, timestamps)

---

## Step 8: Final Sonar Quality Check

**Model**: Sonar (Gemini with web search)

**Location**: `app/ai/enhanced_persona_generator.py` → `_step_8_final_sonar_quality_check()` → Calls `quality_gates.step_8_final_quality_check()`

**Purpose**: Comprehensive quality check of entire persona

**Note**: Prompt is built dynamically by Sonar quality gates

**Returns**:
- `quality_passed`: Boolean
- `overall_confidence`: 1-10
- `issues`: Array of issues found
- `recommendations`: Array of recommendations

---

## 📊 Prompt Summary Statistics

### **By AI Model:**

- **Gemini**: ~8 prompts
  - Website analysis insights
  - Cross-model synthesis
  - Market intelligence (base)
  - Final persona synthesis
  - Sonar validations (multiple)

- **ChatGPT**: ~6 prompts
  - Website analysis
  - Creative market insights
  - Value alignment workflow (3 agents)
  - Creative value insights
  - Creative persona elements

- **Sonar (Gemini with web search)**: ~7 validation prompts
  - Relevance validation
  - Customer focus validation
  - Website analysis validation
  - Market intelligence validation
  - Value alignment validation
  - Creative elements validation
  - Final synthesis validation
  - Final quality check

### **Total Prompts**: ~21 unique prompts across the 8-step process

### **Prompt Characteristics:**

- **Temperature Settings**:
  - Most prompts: Default (0.7-0.9)
  - Market intelligence: 0.3 (more factual)
  - Value alignment agents: 0.2 (more deterministic)
  
- **Token Limits**:
  - Most prompts: Default (8192)
  - Final synthesis: 32000 (to prevent truncation)
  - Value alignment agents: 16384

- **Web Search Enabled**:
  - ChatGPT website analysis: ✅
  - ChatGPT creative market insights: ✅
  - ChatGPT creative persona elements: ✅
  - Sonar validations: ✅ (with domain filtering)
  - Gemini base prompts: ✅ (for market intelligence)

---

## 🔍 Key Prompt Patterns

1. **JSON-Only Output**: All prompts enforce JSON-only responses
2. **Structured Output**: Prompts specify exact JSON structure required
3. **Context-Rich**: Prompts include industry context, market intelligence, and previous analysis results
4. **Validation-Focused**: Sonar prompts focus on fact-checking and accuracy
5. **Creative Enhancement**: ChatGPT prompts focus on creative insights and alternative perspectives
6. **Synthesis Requirements**: Cross-model prompts require specific, actionable insights (no empty arrays)

---

## 📝 Notes

- Some prompts are built dynamically (e.g., Sonar quality gates, enhanced prompt builder)
- Prompts include extensive examples and format specifications
- Error handling and fallbacks are built into prompt responses
- Domain filtering is used in Sonar prompts to prevent hallucination
- Temperature and token limits are carefully tuned for each use case

---

**Last Updated**: Based on codebase analysis as of current date

