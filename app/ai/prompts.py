"""
This file contains all AI prompt templates for the application.
Edit these templates to improve or change the behavior of the AI model.
All comments and variable names are in English for clarity and maintainability.
"""

import os
import json

# System message for all prompts
SYSTEM_MESSAGE = (
    "CRITICAL: Output ONLY a valid JSON object. Do NOT use YAML, Markdown, or any other format. If you do not output valid JSON, your answer will be ignored and considered invalid.\n"
    "You are a JSON generator. Your task is to analyze the provided information and generate a valid JSON response.\n"
    "CRITICAL: Output ONLY a valid JSON object. Do not include any other text, instructions, or formatting.\n\n"
    "JSON RULES:\n"
    "- Use double quotes for strings and property names\n"
    "- Use float values for numbers\n"
    "- Use proper JSON array syntax\n"
    "- Do not include any text before or after the JSON\n"
    "- Do not include any comments or explanations\n"
    "- Ensure all required fields are present\n"
    "- Ensure all values are properly formatted\n"
    "- CRITICAL: Numerical values must be literal numbers (integers or floats), not expressions or calculations.\n"
    "- CRITICAL: NEVER use calculation expressions like (100 - 50) or (x * y). Always provide the final calculated number.\n"
    "- CRITICAL: For percentages, use numbers between 0-100, not expressions like (100 - x).\n\n"
    "Example of valid JSON:\n"
    "{{\n    \"name\": \"Example Corp\",\n    \"value\": 123.45,\n    \"items\": [\"item1\", \"item2\"]\n}}"
)

# Load the canonical example for persona output
EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'buyer_persona_example.json')
try:
    with open(EXAMPLE_PATH, 'r', encoding='utf-8') as f:
        BUYER_PERSONA_EXAMPLE = f.read()
except Exception:
    BUYER_PERSONA_EXAMPLE = '{\n  "pain_points": ["High production costs", "Regulatory complexity"],\n  "goals": ["Expand to new markets", "Increase automation"],\n  "value_drivers": ["Operational efficiency", "Reliability", "Sustainability"],\n  "value_signals": ["Award-winning technology", "24/7 support", "Patented process"],\n  "likely_objections": ["Integration with legacy systems", "Upfront cost"],\n  "chain_of_thought": "The company emphasizes efficiency and innovation on its website, but also highlights challenges with cost and compliance.",\n  "industry_context": {\n    "eurostat_dataset_code": "sbs_na_ind_r2",\n    "market_size": "€10B",\n    "growth_rate": "5% annually",\n    "employment": "50,000 in EU",\n    "summary": "The EU manufacturing sector is growing steadily, driven by demand for automation and sustainability."\n  }\n}'

PROMPT_TEMPLATES = {
    "value_waterfall": [
        SYSTEM_MESSAGE,
        "\n\nInput:\n",
        "Website: {website}\n",
        "Product: {product}\n",
        "BOM Cost: {bom_cost}\n",
        "Manufacturing Cost: {manufacturing_cost}\n",
        "Offer Price: {offer_price}\n\n",
        "Required JSON structure (AI MUST return a JSON object matching this format):\n",
        "{{\n    \"company_info\": {{ object with keys: \"name\" (string), \"industry\" (string), \"size\" (string), \"location\" (string) }},\n    \"bom_cost\": float,\n    \"manufacturing_cost\": float,\n    \"value_add\": float,\n    \"final_price\": float,\n    \"value_bricks\": [ {{ object with keys: \"name\" (string), \"description\" (string), \"value\" (float) }} ]\n}}\n",
        "\nExample response for input (BOM Cost: 100, Manufacturing Cost: 20, Offer Price: 200):\n",
        "{{\n    \"company_info\": {{\n        \"name\": \"Example Corp\",\n        \"industry\": \"Manufacturing\",\n        \"size\": \"Medium\",\n        \"location\": \"Germany\"\n    }},\n    \"bom_cost\": 100.0,\n    \"manufacturing_cost\": 20.0,\n    \"value_add\": 80.0,\n    \"final_price\": 200.0,\n    \"value_bricks\": [\n        {{\n            \"name\": \"Quality Materials\",\n            \"description\": \"High-quality components and materials\",\n            \"value\": 50.0\n        }},\n        {{\n            \"name\": \"Efficient Manufacturing\",\n            \"description\": \"Optimized production process\",\n            \"value\": 30.0\n        }},\n        {{\n            \"name\": \"Brand Value\",\n            \"description\": \"Market recognition and brand equity\",\n            \"value\": 20.0\n        }}\n    ]\n}}\n",
        "\nCRITICAL: Output ONLY the JSON object. Do not include any other text or formatting."
    ],
    "roi": [
        SYSTEM_MESSAGE,
        "\n\nWebsite: {website}\n",
        "Product: {product}\n",
        "BOM Cost: {bom_cost}\n",
        "Offer Price: {offer_price}\n\n",
        "Required JSON format:\n",
        "{{\n    \"roi_analysis\": {{\n        \"payback_period\": float,\n        \"roi_percentage\": float,\n        \"annual_savings\": float,\n        \"total_investment\": float,\n        \"break_even_point\": float\n    }}\n}}\n",
        "\nExample response:\n",
        "{{\n    \"roi_analysis\": {{\n        \"payback_period\": 12.5,\n        \"roi_percentage\": 25.0,\n        \"annual_savings\": 50000.0,\n        \"total_investment\": 200000.0,\n        \"break_even_point\": 8.0\n    }}\n}}\n"
    ],
    "persona": [
        SYSTEM_MESSAGE,
        "\n\nWebsite: {website}\n\n",
        "Required JSON format:\n",
        "Here is an example of the required JSON structure:\n",
        BUYER_PERSONA_EXAMPLE,
        "\n",
        "CRITICAL: Output ONLY a valid JSON object. Do not include any other text, explanation, summary, or bullet points. If you do not output valid JSON, your answer will be ignored and considered invalid."
    ],
    "value_component": [
        SYSTEM_MESSAGE,
        "\n\nCategory: {category}\n",
        "Component: {name}\n",
        "Current Value: {value}\n\n",
        "Required JSON format:\n",
        "{{\n    \"component\": {{\n        \"category\": \"string\",\n        \"name\": \"string\",\n        \"value\": \"string\",\n        \"benefits\": [\"string\"],\n        \"examples\": [\"string\"],\n        \"metrics\": [\"string\"]\n    }}\n}}\n"
    ],
    "persona_advanced": [
        SYSTEM_MESSAGE,
        "\nCompany Info:\n{company_info}\n",
        "Website Sections:\n{website_sections}\n",
        "Value Signals:\n{value_signals}\n",
        "Sentiment Score: {sentiment_score}\n",
        "Industry context (from Eurostat): {industry_summary}\n\n",
        "Eurostat data for the last, current, and next year (if available): {eurostat_data}\n\n",
        "First, reason step by step about what this company's most important value drivers are and why.",
        "Then, estimate how sensitive they are to price (1=not at all, 10=extremely), and provide a rationale based on the website.",
        "Classify the buyer persona into one of these archetypes: 'Value Buyer', 'Relationship Buyer', 'Innovation Seeker', 'Risk Avoider', or 'Service-Oriented'.",
        "Predict likely objections they may raise in a B2B sales process, especially related to price.",
        "Output ONLY this JSON structure:\n"
        "{{\n"
        "  \"value_drivers\": [\"string\", ...],\n"
        "  \"price_sensitivity_score\": int (1-10),\n"
        "  \"price_sensitivity_rationale\": \"string\",\n"
        "  \"archetype\": \"string\",\n"
        "  \"likely_objections\": [\"string\", ...],\n"
        "  \"chain_of_thought\": \"string (explanation of reasoning)\""
        "}}\n"
        "Do not include any other text, explanation, summary, or bullet points. If you do not output valid JSON, your answer will be ignored and considered invalid."
    ],
    "value_alignment": [
        "You are a B2B strategy consultant. Your task is to find strategic alignment between a potential customer's values and our company's core value propositions.\n\n"
        "Below are the customer's stated value drivers and signals, extracted from their website:\n"
        "{customer_values}\n\n"
        "Below are OUR company's core value components (our strengths):\n"
        "{our_value_components}\n\n"
        "Instructions:\n"
        "1. For each of the customer's value drivers, identify the SINGLE most relevant value component from OUR list that supports it.\n"
        "2. For each match, write a concise 'Rationale' explaining WHY our value component helps the customer achieve their stated value. Start the rationale with 'because...'.\n"
        "3. If no direct match is found for a customer value, state 'No direct alignment found' and provide a brief explanation.\n\n"
        "Output a JSON object containing a single key 'alignment_matrix', which is an array of objects. Each object must have three keys: 'customer_value', 'our_component', and 'rationale'.\n\n"
        "Example output format:\n"
        "{\n"
        '  "alignment_matrix": [\n'
        '    {\n'
        '      "customer_value": "Customer\'s stated value (e.g., \'Innovation in manufacturing\')",\n'
        '      "our_component": "Our matching value component (e.g., \'Advanced R&D Department\')",\n'
        '      "rationale": "because our commitment to R&D directly enables the innovation they are seeking."\n'
        '    }\n'
        '  ]\n'
        "}"
    ]
}

def generate_company_summary_prompt(raw_content_text: str) -> str:
    """
    Generates the prompt for summarizing website content to understand a company.
    """
    # This prompt is for the company summary, not Eurostat.
    return (
        f"Summarize the following website text to understand the company's business, "
        f"products, value propositions, and strategy. Be concise but comprehensive.\\n\\n"
        f"Website Text:\\n{raw_content_text}"
    )

persona_advanced = PROMPT_TEMPLATES["persona_advanced"]

# --- Eurostat persona prompt (from to_merge/prompts.py) ---
EUROSTAT_PERSONA_PROMPT = """
You are generating a buyer persona for a global company in the {industry} sector.

- The company operates in Europe, USA, Asia, and other major markets.
- Use industry context and statistics primarily from European sources (Eurostat), focusing on EU-wide or pan-European data, not individual countries.
- Clearly state in the persona that the industry context is based on European data, but generalize the insights to be useful for a global audience.

Below are available Eurostat datasets for this industry and their dimensions:

{eurostat_context}

Instructions:
1. Choose the most relevant dataset for this industry and generate filters for a global context (use 'EU27_2020' or 'EU' for 'geo').
2. Only use dataset codes and dimension values exactly as listed above.
3. Output a JSON with:
   - dataset_code
   - filters (dict of dimension:value)
   - short reason for your choice
   - a brief summary of industry trends, phrased for a global audience but noting the European data source.
"""
# --- End Eurostat persona prompt --- 