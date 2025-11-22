def industry_context_summary_prompt(company_name: str, industry: str, website_text: str) -> str:
    """
    Returns a prompt for Gemini to generate a concise, factual, and user-friendly summary of the customer's business landscape/industry,
    and to classify the company into a standardized industry label.
    The output must be a JSON object with both 'industry' and 'summary' fields.
    """
    return f"""
You are an expert business analyst. Your task is to analyze the following company and its website context, and provide:
- A concise, standardized industry classification for this company (e.g., 'Agricultural Machinery', 'Pharmaceuticals', 'Software', etc.)
- A concise, readable summary of the business landscape for this company and industry.

- Company: {company_name}
- Industry: {industry}
- Website/Context:
{website_text}

Instructions:
- Use ONLY the information provided above. Do NOT invent or guess facts.
- For the 'industry' field, use a short, standardized label that best fits the company's main business (e.g., 'Agricultural Machinery', 'Pharmaceuticals', 'Software', 'Retail', etc.).
- For the 'summary' field:
    - Write a CONCISE summary that is easy to read and suitable for direct display in a web UI tab.
    - Use plain, accessible language for a general business audience.
    - **CRITICAL: Keep it to 5-10 sentences maximum.**
    - Focus on the most important aspects: company background, key products/services, target customers, and market position.
    - Avoid lengthy explanations or detailed lists.
    - If information is missing, acknowledge it briefly rather than making assumptions.
- Output ONLY a valid JSON object with two fields: 'industry' and 'summary'.
- Do not include any extra commentary, formatting, or text outside the JSON object.

Example output:
{{
  "industry": "Agricultural Machinery",
  "summary": "Grimme is a German family-owned company, founded in 1861, specializing in agricultural machinery. They manufacture potato and beet harvesting equipment, serving farmers across Europe and globally. The company focuses on innovation and precision engineering, with a strong emphasis on sustainability and efficiency. Their target customers are large-scale agricultural operations and farming cooperatives. Grimme positions itself as a premium manufacturer with 'Made in Germany' quality and extensive after-sales support."
}}
"""

def website_content_extraction_prompt(website_url: str) -> str:
    """
    Returns a prompt for Gemini to extract and summarize the most relevant information about a company's business, products, value propositions, and strategy from a website URL.
    """
    return f"""
You are an expert business analyst. Given the website URL below, extract and summarize the most relevant information about the company's business, products, value propositions, and strategy. Focus on content that would be useful for generating a B2B buyer persona. Be concise but comprehensive. If possible, structure the output as a summary string.

Website URL: {website_url}
"""

def value_alignment_matrix_prompt(prospect_data: str, company_profile: dict, value_components: str) -> str:
    """
    Returns a prompt for Gemini to generate a B2B Value Alignment Matrix, matching prospect needs/goals to our value components, with rationale, match score, and conversation starter.
    """
    return f"""
You are an expert B2B value consultant. Your task is to help our internal sales team prepare for a high-value conversation with a prospective customer.

Context:
- The prospect's company details, offerings, needs, pain points, and strategic goals are provided below.
- Our company's profile and value components (unique selling points, solutions, differentiators) are also provided.

Instructions:
1. Carefully review the prospect's needs, pain points, and strategic goals.
2. For each need, pain point, or goal, identify the most relevant value component(s) from our company that could address it.
3. For each match, provide:
    - The prospect's need/goal/pain point (verbatim or summarized).
    - The matching value component(s) from our company.
    - A rationale: Explain why this is a good fit, using B2B, value-based, and win-win language.
    - A match score (as a percentage, 0–100%) indicating how well our value component addresses the prospect's need.
    - A suggested "conversation starter" or question for our sales team to use in a meeting.
4. If a need cannot be matched, suggest it as a "potential opportunity" for future product or service development.

Output Format (JSON):
```
{{
  "alignment_matrix": [
    {{
      "prospect_need": "string",
      "our_value_component": "string",
      "rationale": "string",
      "match_score_percent": 0-100,
      "conversation_starter": "string"
    }}
    // ...repeat for each need/goal/pain point...
  ],
  "unmatched_needs": [
    "string" // List any prospect needs/goals that could not be matched
  ]
}}
```

Prospect Data:
```
{prospect_data}
```

Our Company Profile (Perspective):
```
{company_profile}
```

Our Company Value Components:
```
{value_components}
```

Instructions for Gemini:
- Be concise, factual, and use B2B value-based language.
- Focus on actionable insights for sales.
- Always provide a match score for each alignment.
- If unsure, estimate the match score based on available information.
""" 