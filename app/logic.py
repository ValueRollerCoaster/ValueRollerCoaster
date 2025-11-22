import pandas as pd
import numpy as np
from app.ai.ai_modules import (
    ai_generate,
    get_prompt_template,
    create_embedding,
    validate_ai_response,
    send_raw_ai_prompt,
    generate_ai_response,
    clean_ai_response_text
)
from app.utils.spinner import ai_processing_spinner
from app.database import (
    get_connection,
    ensure_collections_exist,
    get_opportunity_statistics,
    search_websites,
    get_website_details,
    save_analysis,
    get_analysis_history,
    ensure_connection,
    close_connection,
    save_value_component,
    get_value_components,
    fetch_all_value_components
)
import app.utils as utils
import logging
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import json
import re
import asyncio
from app.config import (
    AI_TIMEOUT,
    AI_MAX_RETRIES,
    LOG_LEVEL,
    LOG_FORMAT,
    MAX_RETRIES,
    RETRY_DELAY
)
from app.ai.ai_modules import (
    ai_generate,
    get_prompt_template,
    create_embedding,
    validate_ai_response,
    send_raw_ai_prompt,
    generate_ai_response
)
from bs4 import BeautifulSoup
from datetime import datetime
import aiohttp
import httpx
from app.categories import COMPONENT_STRUCTURES
from app.ai.gemini_client import gemini_client
import string
from app.core.company_context_manager import CompanyContextManager

# Configure logging
# logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def parse_roi_analysis(text: str) -> Dict[str, Any]:
    """
    Parse key data (ROI, savings) from the AI generated ROI analysis text.
    """
    parsed_data: Dict[str, Any] = {
        "roi_percentage": None,
        "annual_savings": None,
        "payback_period": None # Store as text for now
    }

    # Look for ROI percentage
    roi_match = re.search(r'ROI is approximately\s*(\d+%)', text, re.IGNORECASE)
    if roi_match:
        parsed_data["roi_percentage"] = roi_match.group(1)

    # Look for annual savings
    savings_match = re.search(r'annual savings of\s*(\$\d{1,3}(?:,\d{3})*(?:.\d{2})?)', text, re.IGNORECASE)
    if savings_match:
        parsed_data["annual_savings"] = savings_match.group(1)
        
    # Look for payback period (simple text extraction for now)
    payback_match = re.search(r'payback period is approximately\s*(.+?)[.,;]', text, re.IGNORECASE)
    if payback_match:
        parsed_data["payback_period"] = payback_match.group(1).strip()

    return parsed_data

def create_roi_chart(parsed_data: Dict[str, Any]) -> go.Figure:
    """
    Creates an ROI comparison chart based on parsed data.
    """
    roi_percent_str = parsed_data.get("roi_percentage")
    # Extract digits and convert to float, handle potential errors
    roi_percent_value = 0
    if roi_percent_str:
        try:
            # Remove % and convert to float
            roi_percent_value = float(roi_percent_str.strip('%'))
        except ValueError:
            logging.warning(f"Could not convert ROI percentage to float: {roi_percent_str}")

    savings_str = parsed_data.get("annual_savings")
    # Remove $ and commas, convert to float, handle potential errors
    savings_value = 0
    if savings_str:
        try:
            # Remove $ and commas, convert to float
            savings_value = float(savings_str.replace('$', '').replace(',', ''))
        except ValueError:
            logging.warning(f"Could not convert annual savings to float: {savings_str}")

    fig = go.Figure(data=[
        go.Bar(name='Your Product', x=['ROI (%)', 'Annual Savings ($)'], y=[roi_percent_value, savings_value])
    ])

    fig.update_layout(
        title='ROI Analysis',
        barmode='group',
        height=400,
        yaxis=dict(title='Value')
    )
    return fig

async def generate_value_waterfall(product: str, bom_cost: float, offer_price: float, website: str) -> Optional[Dict[str, Any]]:
    """Generate value waterfall analysis."""
    try:
        template = get_prompt_template("value_waterfall")
        if not template:
            logger.error("Failed to get value_waterfall prompt template")
            return None

        prompt = template.format(
            website=website,
            product=product,
            bom_cost=bom_cost,
            offer_price=offer_price
        )

        response = await ai_generate(prompt)
        
        if not response:
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(response)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error generating value waterfall: {str(e)}")
        return None
        
async def generate_buyer_persona(website: str) -> Optional[Dict[str, Any]]:
    """Generate buyer persona analysis."""
    try:
        template = get_prompt_template("persona")
        if not template:
            logger.error("Failed to get persona prompt template")
            return None

        prompt = template.format(
            website=website
        )

        response = await ai_generate(prompt)
        
        if not response:
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(response)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error generating buyer persona: {str(e)}")
        return None

async def calculate_roi(website: str, product: str, bom_cost: float, offer_price: float) -> Optional[Dict[str, Any]]:
    """Calculate ROI analysis."""
    try:
        template = get_prompt_template("roi")
        if not template:
            logger.error("Failed to get ROI prompt template")
            return None

        prompt = template.format(
            website=website,
            product=product,
            bom_cost=bom_cost,
            offer_price=offer_price
        )

        response = await ai_generate(prompt)
        
        if not response:
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(response)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}")
        return None

async def generate_objections(website: str, product: str, bom_cost: float, offer_price: float) -> Optional[Dict[str, Any]]:
    """Generate sales objections."""
    try:
        template = get_prompt_template("objection_handler")
        if not template:
            logger.error("Failed to get objection_handler prompt template")
            return None

        prompt = template.format(
            website=website,
            product=product,
            bom_cost=bom_cost,
            offer_price=offer_price
        )

        response = await ai_generate(prompt)
        
        if not response:
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(response)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error generating objections: {str(e)}")
        return None

async def generate_follow_ups(website: str, product: str) -> Optional[Dict[str, Any]]:
    """Generate follow-up suggestions."""
    try:
        template = get_prompt_template("followup_suggester")
        if not template:
            logger.error("Failed to get followup_suggester prompt template")
            return None

        prompt = template.format(
            website=website,
            product=product
        )

        response = await ai_generate(prompt)
        
        if not response:
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(response)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error generating follow-ups: {str(e)}")
        return None

async def generate_roi_analysis(product: str, bom_cost: float, offer_price: float, website: str) -> Optional[Dict[str, Any]]:
    """Generate ROI analysis."""
    try:
        # Get the prompt template
        template = get_prompt_template("roi")
        if not template:
            logger.error("Failed to get ROI prompt template")
            return None

        # Format the prompt
        prompt = template.format(
            website=website,
            product=product,
            bom_cost=bom_cost,
            offer_price=offer_price
        )

        # Generate analysis
        analysis = await ai_generate(prompt)
        if not analysis:
            logger.error("Failed to generate ROI analysis")
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(analysis)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None

    except Exception as e:
        logger.error(f"Error generating ROI analysis: {str(e)}")
        return None

async def generate_persona(website: str) -> Optional[Dict[str, Any]]:
    """Generate buyer persona."""
    try:
        # Get the prompt template
        template = get_prompt_template("persona")
        if not template:
            logger.error("Failed to get persona prompt template")
            return None

        # Format the prompt
        prompt = template.format(website=website)

        # Generate analysis
        analysis = await ai_generate(prompt)
        if not analysis:
            logger.error("Failed to generate buyer persona")
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(analysis)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None

    except Exception as e:
        logger.error(f"Error generating buyer persona: {str(e)}")
        return None

async def handle_objections(product: str, bom_cost: float, offer_price: float, website: str) -> Optional[Dict[str, Any]]:
    """Generate objection handlers."""
    try:
        # Get the prompt template
        template = get_prompt_template("objection_handler")
        if not template:
            logger.error("Failed to get objection handler prompt template")
            return None

        # Format the prompt
        prompt = template.format(
            website=website,
            product=product,
            bom_cost=bom_cost,
            offer_price=offer_price
        )

        # Generate analysis
        analysis = await ai_generate(prompt)
        if not analysis:
            logger.error("Failed to generate objection handlers")
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(analysis)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None

    except Exception as e:
        logger.error(f"Error generating objection handlers: {str(e)}")
        return None

async def suggest_followups(product: str, bom_cost: float, offer_price: float, website: str) -> Optional[Dict[str, Any]]:
    """Generate follow-up suggestions."""
    try:
        # Get the prompt template
        template = get_prompt_template("followup_suggester")
        if not template:
            logger.error("Failed to get followup suggester prompt template")
            return None

        # Format the prompt
        prompt = template.format(
            website=website,
            product=product,
            bom_cost=bom_cost,
            offer_price=offer_price
        )

        # Generate analysis
        analysis = await ai_generate(prompt)
        if not analysis:
            logger.error("Failed to generate follow-up suggestions")
            return None
        
        # Parse JSON response
        cleaned_json = clean_ai_response_text(analysis)
        if not cleaned_json:
            logger.error("Failed to extract JSON from AI response")
            return None
        
        try:
            parsed_response = json.loads(cleaned_json)
            if isinstance(parsed_response, dict):
                return parsed_response
            else:
                logger.warning(f"AI response is not a dict: {type(parsed_response)}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None

    except Exception as e:
        logger.error(f"Error generating follow-up suggestions: {str(e)}")
        return None

async def create_roi_chart_data(roi_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create ROI chart data."""
    try:
        if not roi_analysis or "roi_analysis" not in roi_analysis:
            logger.error("Invalid ROI analysis data")
            return {}

        roi_data = roi_analysis["roi_analysis"]
        return {
            "labels": ["Payback Period", "ROI", "Annual Savings", "Total Investment", "Break Even Point"],
            "values": [
                roi_data.get("payback_period", 0),
                roi_data.get("roi_percentage", 0),
                roi_data.get("annual_savings", 0),
                roi_data.get("total_investment", 0),
                roi_data.get("break_even_point", 0)
            ]
        }

    except Exception as e:
        logger.error(f"Error creating ROI chart: {str(e)}")
        return {}

async def update_website_value_bricks(website: str, value_bricks: List[Dict[str, Any]]) -> bool:
    """Update value bricks for a website."""
    try:
        if not utils.validate_value_bricks(value_bricks):
            logger.error("Invalid value bricks data")
            return False

        # Save to database
        save_success = True
        for comp in value_bricks:
            if not save_value_component(comp):
                logger.error(f"Failed to save value component: {comp}")
                save_success = False
        return save_success

    except Exception as e:
        logger.error(f"Error updating website value bricks: {str(e)}")
        return False

def create_default_roi_chart():
    """
    Creates a default ROI comparison chart.
    """
    fig = go.Figure(data=[
        go.Bar(name='Your Product', x=['ROI', 'Efficiency', 'Cost Savings'], y=[0, 0, 0]),
        go.Bar(name='Competitor A', x=['ROI', 'Efficiency', 'Cost Savings'], y=[0, 0, 0]),
        go.Bar(name='Competitor B', x=['ROI', 'Efficiency', 'Cost Savings'], y=[0, 0, 0])
    ])

    fig.update_layout(
        title='ROI Comparison Analysis',
        barmode='group',
        height=400
    )
    return fig 

async def process_value_component(category: str, name: str, value: str) -> Dict[str, Any]:
    """Process a value component using AI to generate additional information."""
    try:
        # Generate AI response
        response = await generate_ai_response(
            task_type="value_component",
            params={
                "category": category,
                "name": name,
                "value": value
            }
        )
        
        if not response or "component" not in response:
            raise Exception("Invalid AI response")
            
        component = response["component"]
        
        # Save the component
        save_value_component({
            "main_category": component["main_category"],
            "category": component["category"],
            "name": component["name"],
            "original_value": component.get("original_value", ""),
            "ai_processed_value": component.get("ai_processed_value", ""),
            "chain_of_thought": component.get("chain_of_thought", "") # Add chain_of_thought
        })
        return component
        
    except Exception as e:
        logger.error(f"Error processing value component: {str(e)}")
        raise

async def generate_sales_scenario(component: Dict[str, Any], customer_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a sales scenario for a specific value component and customer profile."""
    try:
        # Generate AI response
        response = await generate_ai_response(
            task_type="sales_scenario",
            params={
                "component": component,
                "customer_profile": customer_profile
            }
        )
        
        if not response or "scenario" not in response:
            raise Exception("Invalid AI response")
            
        return response["scenario"]
        
    except Exception as e:
        logger.error(f"Error generating sales scenario: {str(e)}")
        raise

async def calculate_and_save_value_bricks(new_components_raw: List[Dict[str, Any]], component_structures: Dict[str, Any]) -> bool:
    """Calculates percentage values based on input counts and saves to value_components collection."""
    try:
        logger.debug("[calculate_and_save_value_bricks] Starting...")
        logger.debug(f"[calculate_and_save_value_bricks] Input new_components_raw: {json.dumps(new_components_raw, indent=2)}")
        logger.debug(f"[calculate_and_save_value_bricks] Input component_structures: {json.dumps(component_structures, indent=2)}")

        # Deduplicate input: only keep the last occurrence of each key
        key_to_index = {}
        for idx, comp in enumerate(new_components_raw):
            key = f"{comp['main_category']}_{comp['category']}_{comp['name']}"
            if key in key_to_index:
                logger.warning(f"[calculate_and_save_value_bricks] DUPLICATE key in input: {key} (keeping last occurrence)")
            key_to_index[key] = idx
        deduped_components = [new_components_raw[i] for i in sorted(key_to_index.values())]
        # Now build bricks_dict from deduped_components
        bricks_dict = {}
        for comp in deduped_components:
            main_category = comp["main_category"]
            category = comp["category"]
            name = comp["name"]
            original_value = comp.get("original_value", "")
            ai_processed_value = comp.get("ai_processed_value", "")
            weight_from_ai = comp.get("weight", 0.0)
            subcategory_weight = component_structures.get(main_category, {}).get("subcategories", {}).get(category, {}).get("weight", 0.0)
            logger.debug(f"[calculate_and_save_value_bricks] Processing component: {name}")
            logger.debug(f"[calculate_and_save_value_bricks] - Main category: {main_category}")
            logger.debug(f"[calculate_and_save_value_bricks] - Category: {category}")
            logger.debug(f"[calculate_and_save_value_bricks] - Name: {name}")
            key = f"{main_category}_{category}_{name}"
            if key in bricks_dict:
                logger.warning(f"[calculate_and_save_value_bricks] WARNING: Overwriting existing key: {key}")
            bricks_dict[key] = comp
        logger.warning(f"[calculate_and_save_value_bricks] All keys before saving: {list(bricks_dict.keys())}")

        # Calculate total weight for normalization (only for non-empty fields)
        total_weight = sum(comp.get("weight", 0.0) for comp in deduped_components if comp.get("original_value", "").strip())
        for comp in deduped_components:
            weight = comp.get("weight", 0.0)
            original_value = comp.get("original_value", "")
            ai_processed_value = comp.get("ai_processed_value", "")
            if original_value.strip() and total_weight > 0:
                percentage = (weight / total_weight) * 100
            else:
                percentage = 0.0
            comp["value"] = {
                "original_value": original_value,
                "ai_processed_value": ai_processed_value,
                "calculated_percentage": round(percentage, 2)
            }

        # Print all keys before saving
        logger.warning(f"[calculate_and_save_value_bricks] All keys before saving: {list(bricks_dict.keys())}")

        # After deduplication and before saving, log all keys and names
        keys = [f"{c.get('main_category')}_{c.get('category')}_{c.get('name')}" for c in deduped_components]
        logging.warning(f"[logic.py] Saving value bricks: {keys}")
        logging.warning(f"[logic.py] Names being saved: {[c.get('name') for c in deduped_components]}")

        # Save each processed component to value_components
        from app.database import save_value_component
        save_success = True
        total_components = len(deduped_components)
        logger.info(f"[calculate_and_save_value_bricks] Saving {total_components} components to database...")
        
        for idx, comp in enumerate(deduped_components, 1):
            logger.info(f"[calculate_and_save_value_bricks] Saving component {idx}/{total_components}: {comp.get('name', 'Unknown')}")
            if not save_value_component(comp):
                logger.error(f"[calculate_and_save_value_bricks] Failed to save value component: {comp}")
                save_success = False
        
        if save_success:
            logger.info(f"[calculate_and_save_value_bricks] Successfully saved all {total_components} components")
        else:
            logger.error(f"[calculate_and_save_value_bricks] Failed to save some components")
        
        return save_success

    except Exception as e:
        logger.error(f"Error calculating and saving value bricks: {str(e)}", exc_info=True)
        return False

async def analyze_technical_subcategory_components(category_name: str, components: Dict[str, str], expected_item_names: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Analyzes a subcategory of technical components using Gemini to generate value propositions and percentage breakdowns.
    Implements a two-step AI process: (1) business benefit explanation, (2) customer-facing value proposition.
    """
    import difflib
    import string
    import logging
    import re
    def flatten(text):
        return ''.join(c for c in (text or '').lower() if c not in string.whitespace + string.punctuation)
    def is_similar(a, b, threshold=0.5):
        fa, fb = flatten(a), flatten(b)
        ratio = difflib.SequenceMatcher(None, fa, fb).ratio()
        return ratio > threshold
    def normalize_key(s):
        return ''.join(c for c in (s or '').lower() if c.isalnum())
    try:
        with ai_processing_spinner(f"analyzing {category_name} components", count=len(components)):
            # Step 1: For each component, get business benefit explanation
            business_benefits = {}
            total_components = len(components)
            for idx, (comp_name, tech_desc) in enumerate(components.items(), 1):
                logging.info(f"[logic.py][AI][Step1] Processing business benefit {idx}/{total_components} for '{comp_name}'...")
                step1_prompt = f"""
                Explain in clear, business-oriented language what is the business benefit of the following technical feature. Focus on the impact for the company, not technical details. Be concise (2-3 sentences).
                Technical feature:
                {tech_desc}
                """
                logging.info(f"[logic.py][AI][Step1] Sending business benefit prompt for '{comp_name}' to Gemini...")
                step1_response = await gemini_client(step1_prompt, temperature=0.2)
                if not step1_response or 'error' in step1_response.lower():
                    business_benefits[comp_name] = ""
                else:
                    business_benefits[comp_name] = step1_response.strip()
                logging.info(f"[logic.py][AI][Step1] Gemini business benefit for '{comp_name}': {business_benefits[comp_name]}")
            
            # Step 2: For each business benefit, get customer-facing value proposition
            value_props = {}
            for idx, (comp_name, benefit) in enumerate(business_benefits.items(), 1):
                logging.info(f"[logic.py][AI][Step2] Processing value proposition {idx}/{total_components} for '{comp_name}'...")
                if not benefit:
                    value_props[comp_name] = ""
                    continue
                step2_prompt = f"""
                Rephrase the following business benefit as a customer-facing value proposition (2-3 sentences). Focus on how this directly benefits the customer. Use clear, persuasive, business language. Do NOT repeat or paraphrase the original technical description. Start with a benefit-oriented phrase.
                Business benefit:
                {benefit}
                """
                logging.info(f"[logic.py][AI][Step2] Sending value proposition prompt for '{comp_name}' to Gemini...")
                step2_response = await gemini_client(step2_prompt, temperature=0.2)
                if not step2_response or 'error' in step2_response.lower():
                    value_props[comp_name] = ""
                else:
                    value_props[comp_name] = step2_response.strip()
                logging.info(f"[logic.py][AI][Step2] Gemini value proposition for '{comp_name}': {value_props[comp_name]}")
            
            # Step 3: Compose output structure and apply similarity check
            # For percentage, use the original prompt logic (single Gemini call for all components)
            logging.info(f"[logic.py][AI][Percent] Calculating percentage distribution for {category_name}...")
            percent_prompt = f"""
            For each of the following technical features, assign a percentage (out of 100) representing its relative importance. The total percentage must sum to 100%.
            Components:
            {json.dumps(components, indent=2)}
            Output ONLY a JSON object where keys are the component names and values are the percentage (number).
            Example: {{ "Component Name": 25, ... }}
            """
            logger.info(f"[logic.py][AI][Percent] Sending percentage prompt for {category_name} to Gemini...")
            percent_response = await gemini_client(percent_prompt, temperature=0.2)
            if not percent_response:
                logger.error(f"Gemini did not return percentages for {category_name}.")
                return None
            percent_response = re.sub(r"//.*", "", percent_response)
            json_match = re.search(r'\{.*\}', percent_response, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON object found in Gemini percentage response for {category_name}.")
                return None
            percent_json = json_match.group(0)
            try:
                percent_dict = json.loads(percent_json)
            except Exception as e:
                logger.error(f"Error parsing percentage JSON: {e}")
                return None
            
            # --- Robust key matching ---
            logging.info(f"[logic.py][AI] Finalizing results and applying similarity checks...")
            expected_keys_norm = {normalize_key(k): k for k in expected_item_names}
            filtered_result = {}
            for k in components.keys():
                norm_k = normalize_key(k)
                orig_key = expected_keys_norm.get(norm_k, k)
                user_input = components.get(k, "")
                ai_val = (value_props.get(k, "") or "").strip()
                # Similarity check: compare to both tech_desc and business_benefit
                if not ai_val or is_similar(ai_val, user_input) or is_similar(ai_val, business_benefits.get(k, "")):
                    ai_val = "AI could not generate a unique customer benefit. Please rephrase the input."
                filtered_result[orig_key] = {
                    "value_proposition": ai_val,
                    "percentage": percent_dict.get(k, 0.0)
                }
            
            logging.info(f"[logic.py][AI] Completed analysis for {category_name} with {len(filtered_result)} components")
            return filtered_result
    except Exception as e:
        logger.error(f"Error in analyze_technical_subcategory_components (two-step) with Gemini: {str(e)}")
        return None

def format_company_profile_for_prompt(profile):
    lines = [
        f"- Name: {profile.get('company_name', '')}",
        f"- Location: {profile.get('location', '')}",
        f"- Core business: {profile.get('core_business', '')}",
        f"- Industries served: {', '.join(profile.get('industries_served', []))}",
        f"- Target customers: {', '.join(profile.get('target_customers', []))}",
    ]
    return "\n".join(lines)

async def process_value_with_ai(value: str) -> str:
    """
    Enhanced AI processing with comprehensive company context from business intelligence, 
    value delivery, capabilities, and adaptability frameworks.
    """
    import logging
    import difflib
    import json
    from app.ai.gemini_client import gemini_client
    import string
    
    # Import the new helper classes
    from app.utils.business_intelligence_helper import business_intelligence_helper
    from app.utils.value_delivery_helper import value_delivery_helper
    from app.utils.capability_helper import capability_helper
    from app.utils.adaptability_helper import adaptability_helper

    def flatten(text):
        # Remove whitespace and punctuation, lowercase
        return ''.join(c for c in text.lower() if c not in string.whitespace + string.punctuation)
    
    def is_similar(a, b, threshold=0.5):
        fa, fb = flatten(a), flatten(b)
        ratio = difflib.SequenceMatcher(None, fa, fb).ratio()
        print(f"[process_value_with_ai][DIAG] Comparing: '{fa}' vs '{fb}' | Similarity ratio: {ratio:.2f} (threshold={threshold})")
        logging.warning(f"[process_value_with_ai][DIAG] Comparing: '{fa}' vs '{fb}' | Similarity ratio: {ratio:.2f} (threshold={threshold})")
        return ratio > threshold

    def contains_banned_phrases(text):
        banned = [
            "achieve", "maximize", "unlock", "seamless efficiency", "you can", "enabling you", "peak productivity", "focus on your core work", "confidently", "effortless operation", "superior results", "without interruption"
        ]
        text_lc = text.lower()
        return any(phrase in text_lc for phrase in banned)

    # Get comprehensive company context
    company_background = business_intelligence_helper.get_company_context_for_ai()
    value_context = value_delivery_helper.get_value_proposition_context()
    capability_context = capability_helper.get_capability_context()
    adaptability_context = adaptability_helper.get_adaptability_context()
    
    # Create enhanced prompt with all context
    prompt = (
        f"Company Background:\n{company_background}\n\n"
        f"Value Delivery Context:\n{value_context}\n\n"
        f"Capability Context:\n{capability_context}\n\n"
        f"Adaptability Context:\n{adaptability_context}\n\n"
        "Task:\n"
        "Based on the comprehensive company context above, write a factual, third-person paragraph explaining how the product benefits the customer.\n"
        "- Do NOT use slogans, taglines, or imperative sentences.\n"
        "- Do NOT use phrases like 'achieve', 'unlock', 'maximize', 'you can', or 'enabling you'.\n"
        "- Use third-person, descriptive language.\n"
        "- Explain the specific mechanism or feature that delivers the benefit.\n"
        "- Reference relevant company capabilities, value delivery methods, and adaptability factors.\n"
        "- Focus on customer outcomes and value creation.\n\n"
        f"Technical description:\n{value}\n\n"
        "Negative Example (to avoid):\n"
        '"Achieve seamless efficiency and peak productivity with a solution designed for effortless operation. '
        'You can confidently focus on your core work, knowing the underlying technology simply performs, enabling you to deliver superior results without interruption."\n\n'
        "Positive Example:\n"
        '"The robust design of the solution ensures that end users experience minimal downtime and do not need to intervene in machine operation. '
        'This reliability leads to higher user satisfaction and positive feedback, particularly in demanding industrial environments."\n\n'
        "Output:\n"
    )
    
    try:
        for attempt in range(2):
            ai_response = await gemini_client(prompt, temperature=0.2)
            print(f"[process_value_with_ai][DIAG] Raw Gemini response: {ai_response}")
            logging.warning(f"[process_value_with_ai][DIAG] Raw Gemini response: {ai_response}")
            
            # Try to extract value_proposition if JSON
            ai_text = None
            try:
                data = json.loads(ai_response)
                # Try to extract the first value_proposition
                for v in data.values():
                    if isinstance(v, dict) and 'value_proposition' in v:
                        ai_text = v['value_proposition']
                        break
            except Exception:
                ai_text = None
            
            if not ai_text:
                ai_text = ai_response.strip()
            
            # Compare and fallback if too similar
            if is_similar(ai_text, value):
                print("[process_value_with_ai][FALLBACK] AI response too similar to input. Using fallback message.")
                logging.warning("[process_value_with_ai][FALLBACK] AI response too similar to input. Using fallback message.")
                return "AI could not generate a unique customer benefit. Please rephrase the input."
            
            # Post-processing: check for banned phrases
            if not contains_banned_phrases(ai_text):
                return ai_text
            else:
                print("[process_value_with_ai][RETRY] AI output contained banned phrases. Re-prompting.")
                logging.warning("[process_value_with_ai][RETRY] AI output contained banned phrases. Re-prompting.")
        
        # If still not good after retry
        return "AI could not generate a suitable customer benefit. Please rephrase the input."
    except Exception as e:
        print(f"[process_value_with_ai][ERROR] Exception: {e}")
        logging.error(f"[process_value_with_ai][ERROR] Exception: {e}")
        return "AI could not generate a unique customer benefit. Please rephrase the input." 

async def generate_chain_of_thought(company_background, value, customer_benefit, component_title):
    """
    Generate a chain-of-thought reasoning for a value component, explaining step-by-step how the customer benefit was derived.
    """
    from app.ai.gemini_client import gemini_client
    cot_prompt = (
        f"Company Background:\n{company_background}\n\n"
        f"Component: {component_title}\n"
        f"User Input: {value}\n"
        f"Customer Benefit: {customer_benefit}\n\n"
        "Task: Explain step-by-step how the customer benefit was derived from the user input and company context. "
        "Focus on logical reasoning, factual connections, and any assumptions made. "
        "Output a concise, clear explanation in 2-4 sentences.\n"
    )
    cot = await gemini_client(cot_prompt, temperature=0.2)
    return cot.strip() 