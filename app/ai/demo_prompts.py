"""
Demo-specific AI prompts for persona generation.
These prompts are designed to work with fictional demo companies and customers.
"""

# Demo context prompt to inform AI models about the demo nature
DEMO_CONTEXT_PROMPT = """
IMPORTANT DEMO CONTEXT:
- You are working with FICTIONAL demo companies and customers for demonstration purposes
- These companies do not exist in real life - they are created for showcasing the system
- Do NOT attempt to search the web or find real information about these companies
- Generate realistic but fictional buyer personas based on the provided company information
- Focus on creating educational examples that demonstrate the system's capabilities
- Use the provided company profile and value components to generate relevant personas
"""

# Demo persona generation prompt
DEMO_PERSONA_GENERATION_PROMPT = """
You are generating a buyer persona for a DEMO/FICTIONAL company. 

Company Context:
- Company Name: {company_name}
- Industry: {industry}
- Business Model: {business_model}
- Target Market: {target_market}

Value Components Available:
{value_components}

Instructions:
1. Create a realistic buyer persona based on the fictional company profile
2. The persona should be relevant to the company's industry and value propositions
3. Include typical pain points, goals, and characteristics for this type of customer
4. Make it educational and demonstrate the system's capabilities
5. Do NOT search for real information - this is a fictional demo scenario
6. Focus on creating a compelling example that shows how the system works

Generate a comprehensive buyer persona with:
- Demographics and firmographics
- Pain points and challenges
- Goals and objectives
- Buying behavior and preferences
- Decision-making process
- Communication preferences
"""

# Demo market intelligence prompt
DEMO_MARKET_INTELLIGENCE_PROMPT = """
You are analyzing market intelligence for a DEMO/FICTIONAL company.

Company Profile:
- Name: {company_name}
- Industry: {industry}
- Business Model: {business_model}
- Value Propositions: {value_propositions}

Instructions:
1. Generate realistic market intelligence based on the fictional company profile
2. Create industry insights that would be relevant to this type of business
3. Include market trends, competitive landscape, and opportunities
4. Make it educational and demonstrate the system's analytical capabilities
5. Do NOT search for real market data - this is a fictional demo scenario
6. Focus on creating realistic examples that show the system's value

Generate market intelligence covering:
- Industry trends and opportunities
- Competitive landscape analysis
- Market size and growth potential
- Customer segments and personas
- Key success factors
"""

# Demo website analysis prompt
DEMO_WEBSITE_ANALYSIS_PROMPT = """
You are analyzing a DEMO/FICTIONAL company website for persona generation.

Company Information:
- Name: {company_name}
- Industry: {industry}
- Business Model: {business_model}
- Website: {website_url} (NOTE: This is a fictional demo URL)

Instructions:
1. Generate a realistic website analysis based on the fictional company profile
2. Create insights about the company's positioning, messaging, and target audience
3. Identify potential buyer personas based on the company's value propositions
4. Make it educational and demonstrate the system's analytical capabilities
5. Do NOT attempt to access the website - this is a fictional demo scenario
6. Focus on creating realistic examples that show how the system works

Generate analysis covering:
- Company positioning and messaging
- Target audience characteristics
- Value proposition analysis
- Competitive differentiation
- Buyer persona insights
"""

# Demo customer profile prompt
DEMO_CUSTOMER_PROFILE_PROMPT = """
You are creating a customer profile for a DEMO/FICTIONAL scenario.

Customer Information:
- Name: {customer_name}
- Industry: {customer_industry}
- Company Size: {company_size}
- Location: {location}
- Description: {description}

Company Context (the vendor):
- Company Name: {vendor_company_name}
- Industry: {vendor_industry}
- Value Propositions: {vendor_value_propositions}

Instructions:
1. Create a realistic customer profile based on the fictional scenario
2. The customer should be a good fit for the vendor's value propositions
3. Include relevant pain points, goals, and buying behavior
4. Make it educational and demonstrate the system's matching capabilities
5. Do NOT search for real information - this is a fictional demo scenario
6. Focus on creating a compelling example that shows how the system works

Generate a customer profile with:
- Company background and context
- Current challenges and pain points
- Goals and objectives
- Buying behavior and decision-making process
- Fit with vendor's value propositions
- Recommended approach and messaging
"""
