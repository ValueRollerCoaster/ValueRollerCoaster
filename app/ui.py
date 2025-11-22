import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import asyncio
import logging
import uuid
import json
from typing import Dict, Any, Optional, List
from app.config import (
    LOG_LEVEL,
    LOG_FORMAT,
    MAX_URL_LENGTH,
    MAX_ANALYSIS_SIZE,
    MAX_VALUE_BRICKS
)
import app.utils as utils
from app.utils.spinner import search_spinner, ui_refresh_spinner
from app.logic import (
    generate_value_waterfall,
    generate_roi_analysis,
    handle_objections,
    suggest_followups,
    process_value_component,
    create_roi_chart as logic_create_roi_chart,
    calculate_and_save_value_bricks,
    process_value_with_ai
)
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
    get_value_component,
    save_value_component,
    fetch_all_value_components,  # Renamed from get_all_value_components
    recreate_value_components_collection
)
from app.ai.ai_modules import ai_generate
from datetime import datetime
from app.components.value_components.value_components_tab import render_value_components_tab
from app.categories import COMPONENT_STRUCTURES
from qdrant_client import QdrantClient
import traceback
import inspect
from app.charts.technical_value_donut import technical_value_donut_chart
from app.charts.business_value_donut import business_value_donut_chart
from app.charts.strategic_value_donut import strategic_value_donut_chart
from app.charts.after_sales_value_donut import after_sales_value_donut_chart
from app.components.persona_tab import persona_tab
from app.components.persona_search_tab import persona_search_tab
from app.components.api_chart_tab import api_chart_tab

__all__ = ["show_main_ui"]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Value Components"

# Loading state for initial components generation
if "is_generating_initial_value_components" not in st.session_state:
    st.session_state["is_generating_initial_value_components"] = False

# Configure logging
# logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

#copilot generated
def update_state_and_rerun(key, value):
    st.session_state[key] = value
    st.rerun()


# MOVE COMPONENT_STRUCTURES definition to a new file: app/categories.py

# Initialize Qdrant connection and collections
async def initialize_qdrant():
    """Initialize Qdrant connection and collections."""
    try:
        if not await ensure_connection():
            logger.error("Failed to establish Qdrant connection during initialization.")
            return False
        await ensure_collections_exist() # Ensure all collections exist
        logger.info("Qdrant collections ensured.")
        return True
    except Exception as e:
        st.error(f"Error initializing Qdrant: {str(e)}")
        return False
    finally:
        await close_connection()

# Qdrant initialization moved to lazy loading to improve startup performance
# initialize_qdrant() will be called when needed instead of on startup

def create_waterfall_chart(waterfall_data: Dict[str, float]) -> go.Figure:
    """Create a waterfall chart with validation."""
    try:
        fig = go.Figure(go.Waterfall(
            name="Value Breakdown",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["BOM Cost", "Manufacturing", "Value Add", "Final Price"],
            y=[
                -waterfall_data.get("bom_cost", 0),
                -waterfall_data.get("manufacturing_cost", 0),
                waterfall_data.get("value_add", 0),
                waterfall_data.get("final_price", 0)
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        
        fig.update_layout(
            title="Value Rollercoaster Analysis",
            showlegend=True,
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig
    except Exception as e:
        logger.error(f"Error creating waterfall chart: {str(e)}")
        return go.Figure()

# All value component data for charts and summaries should use fetch_all_value_components()
async def load_value_bricks_from_qdrant(website: str) -> list:
    """Load value bricks from Qdrant for the given website."""
    try:
        analyses = get_website_details(website)
        if analyses and isinstance(analyses, list) and len(analyses) > 0:
            latest_analysis = analyses[0]
            if 'value_bricks' in latest_analysis and latest_analysis['value_bricks']:
                loaded_bricks = latest_analysis['value_bricks']
                if isinstance(loaded_bricks, list):
                    logger.info(f"Successfully loaded {len(loaded_bricks)} value bricks from Qdrant for {website}")
                    return loaded_bricks
                else:
                    logger.warning(f"Loaded value_bricks data is not a list: {loaded_bricks}")
            else:
                logger.info(f"No value_bricks found in latest analysis for {website}")
        else:
            logger.info(f"No analyses found for website: {website}")
    except Exception as e:
        logger.error(f"Error loading value bricks for {website}: {str(e)}")
    return []

async def show_saved_websites():
    """Display saved websites with improved error handling."""
    st.title("Saved Websites")
    # Search form
    st.subheader("🔍 Search Websites")
    search_query = st.text_input("Search by keywords")
    # Search button
    if st.button("Search"):
        with search_spinner("websites"):
            try:
                results = search_websites(search_query)
                if results and isinstance(results, (list, tuple)):
                    st.subheader("📚 Search Results")
                    for website in results:  # type: ignore[union-attr]
                        with st.expander(f"{utils.safe_str(website.get('website', 'Unknown'))}"):
                            # Safely get analysis data, ensure it's a dict
                            analysis_data = website.get('analysis', {}) or {}
                            if not isinstance(analysis_data, dict):
                                logger.warning(f"Analysis data for {website.get('website', 'Unknown')} is not a dictionary, defaulting to empty dict: {analysis_data}")
                                analysis_data = {}
                            # Company info
                            st.write("**🏢 Company Information:**")
                            company_info = analysis_data.get('company_info', {})
                            if isinstance(company_info, dict):
                                for k, v in company_info.items():
                                    st.write(f"- **{utils.safe_str(k).capitalize()}**: {utils.safe_str(v)}")
                            else:
                                st.write(utils.safe_str(company_info))
                            # Create tabs for different analyses
                            tabs = st.tabs([
                                "📊 Value Rollercoaster",
                                "👤 Buyer Persona",
                                "📈 Financial Analysis",
                                "🌐 Market Analysis",
                                "🧱 Value Bricks"
                            ])
                            with tabs[0]:  # Value Rollercoaster
                                st.subheader("📊 Value Rollercoaster Analysis")
                                waterfall_data = {
                                    "bom_cost": analysis_data.get("bom_cost", 0),
                                    "manufacturing_cost": analysis_data.get("manufacturing_cost", 0),
                                    "value_add": analysis_data.get("value_add", 0),
                                    "final_price": analysis_data.get("final_price", 0)
                                }
                                fig = create_waterfall_chart(waterfall_data)
                                st.plotly_chart(fig)
                            with tabs[1]:  # Buyer Persona
                                try:
                                    st.subheader("👤 Buyer Persona")
                                    persona = analysis_data.get('persona', {})
                                    if persona:
                                        with st.expander("💡 Value Signals"):
                                            value_signals = persona.get("value_signals", [])
                                            if isinstance(value_signals, (list, tuple)):
                                                for v in utils.flatten_and_stringify(value_signals):
                                                    st.write(f"- {utils.safe_str(v)}")
                                            elif value_signals:
                                                st.write(utils.safe_str(value_signals))
                                            else:
                                                st.write("No value signals found.")
                                        with st.expander("😫 Pain Points"):
                                            pain_points = persona.get("pain_points", [])
                                            if isinstance(pain_points, list):
                                                for point in utils.flatten_and_stringify(pain_points):
                                                    st.write(f"- {utils.safe_str(point)}")
                                            elif pain_points:
                                                st.write(utils.safe_str(pain_points))
                                            else:
                                                st.write("No pain points found.")
                                        with st.expander("🎯 Goals"):
                                            goals = persona.get("goals", [])
                                            if isinstance(goals, list):
                                                for goal in utils.flatten_and_stringify(goals):
                                                    st.write(f"- {utils.safe_str(goal)}")
                                            elif goals:
                                                st.write(utils.safe_str(goals))
                                            else:
                                                st.write("No goals found.")
                                        with st.expander("🚀 Value Drivers"):
                                            value_drivers = persona.get("value_drivers", [])
                                            if isinstance(value_drivers, list):
                                                for driver in utils.flatten_and_stringify(value_drivers):
                                                    st.write(f"- {utils.safe_str(driver)}")
                                            elif value_drivers:
                                                st.write(utils.safe_str(value_drivers))
                                            else:
                                                st.write("No value drivers found.")
                                        with st.expander("⛔ Likely Objections"):
                                            likely_objections = persona.get("likely_objections", [])
                                            if isinstance(likely_objections, list):
                                                for obj in utils.flatten_and_stringify(likely_objections):
                                                    st.write(f"- {utils.safe_str(obj)}")
                                            elif likely_objections:
                                                st.write(utils.safe_str(likely_objections))
                                            else:
                                                st.write("No likely objections found.")
                                        with st.expander("🧠 Chain of Thought"):
                                            chain_of_thought = persona.get("chain_of_thought", "")
                                            if chain_of_thought:
                                                st.write(chain_of_thought)
                                            else:
                                                st.write("No chain of thought provided.")
                                        with st.expander("📊 Industry Context (Eurostat)"):
                                            industry_ctx = persona.get("industry_context", {})
                                            st.write(f"- Market Size: {utils.safe_str(industry_ctx.get('market_size', '-'))}")
                                            st.write(f"- Growth Rate: {utils.safe_str(industry_ctx.get('growth_rate', '-'))}")
                                            st.write(f"- Employment: {utils.safe_str(industry_ctx.get('employment', '-'))}")
                                            if industry_ctx.get("eurostat_dataset_code"):
                                                st.write(f"- Eurostat Dataset Code: {utils.safe_str(industry_ctx['eurostat_dataset_code'])}")
                                            if industry_ctx.get("summary"):
                                                st.info(industry_ctx["summary"])
                                    else:
                                        st.info("No buyer persona data available.")
                                except Exception as e:
                                    tb = traceback.format_exc()
                                    logging.error(f"[UI] Exception in Buyer Persona tab: {e}\n{tb}")
                                    st.error(f"An error occurred in Buyer Persona tab: {e}\n\n{tb}")
                            with tabs[2]:  # Financial Analysis
                                st.subheader("📈 Financial Analysis")
                                financial = persona.get('financial_analysis', {})
                                if financial:
                                    with st.expander("💰 Financial Stability"):
                                        st.write(f"**Stability Level:** {financial.get('stability', 'N/A')}")
                                        st.write(f"**Growth Rate:** {financial.get('growth_rate', 'N/A')}")
                                        st.write(f"**Profitability:** {financial.get('profitability', 'N/A')}")
                                        st.write(f"**Risk Level:** {financial.get('risk_level', 'N/A')}")
                                    
                                    with st.expander("📊 Financial Metrics"):
                                        st.write(financial.get('metrics', {}))
                                    
                                    with st.expander("📈 Growth Analysis"):
                                        st.write(financial.get('growth_analysis', {}))
                                else:
                                    st.info("No financial analysis data available.")

                            with tabs[3]:  # Market Analysis
                                st.subheader("🌐 Market Analysis")
                                market = persona.get('industry_analysis', {})
                                if market:
                                    with st.expander("📊 Market Position"):
                                        st.write(f"**Position:** {market.get('position', 'N/A')}")
                                        st.write(f"**Market Share:** {market.get('market_share', 'N/A')}")
                                    
                                    with st.expander("💪 Competitive Advantages"):
                                        for advantage in market.get('competitive_advantages', []):
                                            st.write(f"- {advantage}")
                                    
                                    with st.expander("⚠️ Competitive Threats"):
                                        for threat in market.get('competitive_threats', []):
                                            st.write(f"- {threat}")
                                    
                                    with st.expander("🌱 Growth Opportunities"):
                                        for opportunity in market.get('growth_opportunities', []):
                                            st.write(f"- {opportunity}")
                                else:
                                    st.info("No market analysis data available.")

                            with tabs[4]:  # Value Bricks
                                #copilot generated
                                with tabs[4]:  # Value Bricks
                                    st.subheader("�� Value Components")

                                    # Always prefer session state for freshest data
                                    value_bricks = st.session_state.get('value_bricks') or website.get('value_bricks', [])

                                    # Add a manual refresh button
                                    if st.button("Refresh Value Bricks"):
                                        new_bricks = await load_value_bricks_from_qdrant(website['website'])
                                        update_state_and_rerun('value_bricks', new_bricks)
                                        return  # UI will rerun

                                    if value_bricks:
                                        total_calculated_percentage = 0.0
                                        valid_bricks = []
                                        for brick in value_bricks:
                                            try:
                                                value_data = brick.get('value', {})
                                                if isinstance(value_data, str):
                                                    value_data = utils.safe_json_loads(value_data)
                                                    if value_data is None:
                                                        value_data = {}
                                                calculated_percentage = value_data.get('calculated_percentage')
                                                if calculated_percentage is not None:
                                                    numeric_percentage = float(calculated_percentage)
                                                    total_calculated_percentage += numeric_percentage
                                                    valid_bricks.append({
                                                        "name": brick.get("name", "N/A"),
                                                        "description": brick.get("description", ""),
                                                        "calculated_percentage": numeric_percentage
                                                    })
                                            except (ValueError, TypeError) as e:
                                                logger.warning(f"Skipping invalid value brick in show_saved_websites: {brick} - {e}")
                                                continue

                                        if valid_bricks:
                                            st.write("### Value Distribution")
                                            st.progress(total_calculated_percentage / 100.0)
                                            st.write(f"**Total Used:** {total_calculated_percentage:.1f}% | **Remaining:** {100.0 - total_calculated_percentage:.1f}%")
                                            for brick in valid_bricks:
                                                col1, col2, col3 = st.columns([3, 1, 1])
                                                with col1:
                                                    st.write(f"**{brick['name']}**")
                                                    st.write(f"*{brick['description']}*")
                                                with col2:
                                                    st.write(f"{brick['calculated_percentage']:.1f}%")
                                                with col3:
                                                    st.progress(brick['calculated_percentage'] / 100.0)
                                        else:
                                            st.info("No valid value components available to display.")
                                    else:
                                        st.info("No value components available.")
                            # Display creation date
                            if 'created_at' in website:
                                st.write(f"**Created:** {datetime.fromtimestamp(website['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")

                else:
                    st.info("No results found.")
            except Exception as e:
                logger.error(f"Error searching websites: {str(e)}")
                st.error("An error occurred while searching. Please try again.")

def create_value_waterfall_chart(components_dict: Dict[str, float]) -> go.Figure:
    """Create a waterfall chart showing the distribution of value components."""
    try:
        categories = []
        values = []
        measures = []
        
        # Sort components by value
        sorted_components = sorted(components_dict.items(), key=lambda x: x[1], reverse=True)
        
        current_sum = 0.0
        for component_id, value in sorted_components:
            # component_id is like "MainCategory_Category_Name"
            parts = component_id.split('_')
            
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid value for chart component {component_id}: {value}")
                continue

            if len(parts) == 3: # Expecting MainCategory, Category, Name
                main_category = parts[0]
                category = parts[1]
                name = parts[2]
                # Make labels shorter and more descriptive
                categories.append(f"{main_category.replace(' Value', '')} - {category} - {name}")
                values.append(numeric_value)
                measures.append("relative")
                current_sum += numeric_value
            else:
                logger.warning(f"Skipping malformed component_id: {component_id}")
                continue
        
        if not values:
            # If no valid values, return an empty figure to prevent errors
            return go.Figure()
            
        # Add total, which is the sum of all plotted components
        categories.append("Total")
        values.append(current_sum)
        measures.append("total")
        
        # Create figure with explicit layout
        fig = go.Figure()
        
        # Add waterfall trace
        fig.add_trace(go.Waterfall(
            name="Value Distribution",
            orientation="v",
            measure=measures,
            x=categories,
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            textposition="outside",
            text=[f"{v:.1f}%" for v in values],
            decreasing={"marker": {"color": "Maroon"}},
            increasing={"marker": {"color": "Teal"}},
            totals={"marker": {"color": "deep sky blue"}}
        ))
        
        # Update layout with explicit parameters
        fig.update_layout(
            title="Value Components Distribution",
            showlegend=True,
            height=600,
            margin=dict(l=50, r=50, t=50, b=50),
            yaxis=dict(
                title="Percentage (%)",
                range=[0, max(100.0, current_sum * 1.1)]
            ),
            xaxis=dict(
                title="Components",
                tickangle=45
            )
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating value rollercoaster chart: {str(e)}")
        return go.Figure()

async def render_value_distribution_chart(main_category: Optional[str] = None):
    """Render the value distribution chart."""
    try:
        # FIX: Get user_id from session state and pass it to fetch_all_value_components
        user_id = st.session_state.get('user_id', None)
        all_components = fetch_all_value_components(user_id=user_id)
        if not all_components:
            st.warning("No value components found.")
            return
        # Filter components by main category if specified
        if isinstance(all_components, dict):
            if main_category:
                components = all_components.get(main_category, [])
            else:
                components = []
                for category_components in all_components.values():
                    components.extend(category_components)
        elif isinstance(all_components, list):
            components = all_components
        else:
            components = []
        if not components:
            st.warning(f"No value components found for category: {main_category}")
            return
        # Create DataFrame for plotting
        df = pd.DataFrame(components)
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=df['name'],
            values=df['value'].apply(lambda x: x.get('calculated_percentage', 0)) if 'value' in df else [],
            hole=.3
        )])
        # Update layout
        title = f"Value Distribution - {main_category}" if main_category else "Value Distribution"
        fig.update_layout(
            title=title,
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        logger.error(f"Error rendering value distribution chart: {str(e)}")
        st.error(f"An error occurred while rendering the chart: {str(e)}")

async def show_main_ui(current_page: str, user_db=None):
    """Main UI router."""
    # Map page names to their corresponding functions - match original app exactly
    pages = {
        "Value Components": show_value_components_page,
        "Persona Generator": show_buyer_persona,
        "Persona Search": persona_search_tab,
        "API Chart": api_chart_tab,
    }

    page_to_show = pages.get(current_page.strip())

    if page_to_show:
        try:
            logging.info(f"Navigating to page: {current_page}")
            if current_page.strip() == "API Chart":
                page_to_show()  # Call synchronously
            elif current_page.strip() == "Value Components":
                # Only Value Components page needs user_db parameter
                await page_to_show(user_db=user_db)
            else:
                # Other pages don't need user_db parameter
                await page_to_show()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logging.error(f"Exception in page '{current_page}': {e}\n{tb}")
            st.error(f"An error occurred while loading this page: {e}")
    else:
        logging.error(f"Unknown page requested: '{current_page}'")
        st.error(f"Unknown page: {current_page}")

# NOTE: This function always rebuilds session state for value_components and ai_processed_values from the DB on navigation.
# This ensures that after clearing and saving, navigating away and returning always loads fresh data from the DB, and never shows stale cleared fields.
async def show_value_components_page(user_db=None):
    # --- Use demo profile manager for proper data isolation ---
    from app.components.demo_companies.demo_profile_manager import demo_profile_manager
    user_id = demo_profile_manager.get_current_user_id()
    all_components = fetch_all_value_components(user_id=user_id)
    
    # Debug: Log the user ID and data being fetched
    logging.warning(f"[ui.py] Using user_id={user_id}, demo_mode={st.session_state.get('user_demo_mode', False)}")
    logging.warning(f"[ui.py] Session state user_id={st.session_state.get('user_id', 'NOT_SET')}")
    logging.warning(f"[ui.py] Fetched {len(all_components) if isinstance(all_components, (dict, list)) else 'unknown'} components from database")
    
    # Debug: Show what's in all_components
    if isinstance(all_components, dict):
        logging.warning(f"[ui.py] Database returned {len(all_components)} main categories: {list(all_components.keys())}")
    else:
        logging.warning(f"[ui.py] Database returned non-dict: {type(all_components)} = {all_components}")
    
    # Show helpful message if no data found
    if isinstance(all_components, dict) and len(all_components) == 0 and not st.session_state.get("user_demo_mode", False):
        st.info("📝 **No value components data found!** Your company profile is configured, but you haven't filled out the detailed value components yet.")
        
        # Add button to populate initial data based on company profile
        from app.config import ENABLE_DEMO_MODE
        
        is_generating = st.session_state.get("is_generating_initial_value_components", False)
        button_label = "⏳ Generating..." if is_generating else "🚀 Generate Initial Value Components"
        button_kwargs = {"type": "primary", "help": "Generate initial value components based on your company profile", "disabled": is_generating}

        if ENABLE_DEMO_MODE:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(button_label, **button_kwargs):
                    # Set flag and rerun immediately to update UI (disable button + show spinner)
                    st.session_state.is_generating_initial_value_components = True
                    st.rerun()
            with col2:
                if st.button("🎭 Try Demo Mode", help="See how the app works with demo data"):
                    st.session_state.user_demo_mode = True
                    st.rerun()
        else:
            # Demo mode disabled, only show generate button
            if st.button(button_label, **button_kwargs):
                # Set flag and rerun immediately to update UI (disable button + show spinner)
                st.session_state.is_generating_initial_value_components = True
                st.rerun()

        # If flagged as generating, run the generation with a visible spinner
        if st.session_state.get("is_generating_initial_value_components", False):
            with st.spinner("Generating initial value components..."):
                await generate_initial_value_components(user_id)
    
    # Only initialize session state if not already populated (preserve demo data)
    if "value_components" not in st.session_state:
        st.session_state.value_components = {}
    if "ai_processed_values" not in st.session_state:
        st.session_state.ai_processed_values = {}
    
    # Always populate session state from database when not in demo mode
    # or when session state is empty (preserve demo data)
    demo_mode_active = st.session_state.get("user_demo_mode", False)
    session_state_empty = not st.session_state.value_components and not st.session_state.ai_processed_values
    
    if not demo_mode_active or session_state_empty:
        # Debug: Log what we're doing
        if not demo_mode_active:
            logging.warning(f"[ui.py] Loading real company data for user_id={user_id}")
        else:
            logging.warning(f"[ui.py] Loading data because session state is empty")
        
        # Handle the format returned by fetch_all_value_components
        # It returns: {"main_category": [{"category": "...", "name": "...", ...}, ...]}
        if isinstance(all_components, dict):
            for main_cat, components_list in all_components.items():
                if isinstance(components_list, list):
                    for comp in components_list:
                        if isinstance(comp, dict):  # Ensure comp is a dictionary
                            sub_cat = comp.get("category", "")
                            comp_name = comp.get("name", "")
                            original_val = comp.get("original_value", "")
                            ai_processed_val = comp.get("ai_processed_value", "")
                            # Always set the values, even if empty - don't skip empty fields
                            if comp_name:
                                st.session_state.value_components.setdefault(main_cat, {}).setdefault(sub_cat, {})[comp_name] = original_val
                                st.session_state.ai_processed_values.setdefault(main_cat, {}).setdefault(sub_cat, {})[comp_name] = ai_processed_val
                else:
                    # Handle case where components_list is not a list (shouldn't happen but safety check)
                    logging.warning(f"Unexpected format for components_list: {type(components_list)}")
        elif isinstance(all_components, list):
            # Handle legacy format if it's a list
            for comp in all_components:  # type: ignore[union-attr]
                if isinstance(comp, dict):  # Ensure comp is a dictionary
                    main_cat = comp.get("main_category", "")
                    sub_cat = comp.get("category", "")
                    comp_name = comp.get("name", "")
                    original_val = comp.get("original_value", "")
                    ai_processed_val = comp.get("ai_processed_value", "")
                    # Always set the values, even if empty - don't skip empty fields
                    if comp_name:
                        st.session_state.value_components.setdefault(main_cat, {}).setdefault(sub_cat, {})[comp_name] = original_val
                        st.session_state.ai_processed_values.setdefault(main_cat, {}).setdefault(sub_cat, {})[comp_name] = ai_processed_val
    
    # Always fill in any missing fields with empty strings (ensures structure exists)
    for main_cat, details in COMPONENT_STRUCTURES.items():
        for sub_cat, subcat_details in details["subcategories"].items():
            for comp in subcat_details["items"]:
                comp_name = comp["name"]
                st.session_state.value_components.setdefault(main_cat, {}).setdefault(sub_cat, {}).setdefault(comp_name, "")
                st.session_state.ai_processed_values.setdefault(main_cat, {}).setdefault(sub_cat, {}).setdefault(comp_name, "")
    # --- Main Content: Value Components Tab ---
    selected_main_category = st.session_state.get("selected_main_category", "Summary")
    
    # Debug: Log session state values
    logging.warning(f"[ui.py] Session state value_components has {len(st.session_state.value_components)} main categories")
    for main_cat, cat_data in st.session_state.value_components.items():
        logging.warning(f"[ui.py] Main category {main_cat}: {len(cat_data)} subcategories")
    
    st.markdown("<div style='height: 1em'></div>", unsafe_allow_html=True)
    await render_value_components_tab(
        st.session_state.value_components,
        st.session_state.ai_processed_values,
        process_value_with_ai,
        calculate_and_save_value_bricks,
        refresh_callback=refresh_value_components_ui,
        selected_main_category=selected_main_category
    )
    logging.warning(f"[ui.py] After await render_value_components_tab, current_selected_main_category: {selected_main_category}")

async def show_sales_objections_page(user_db=None):
    """Show the Sales Objections page."""
    st.write("Sales Objections page content goes here.")

async def show_follow_ups_page(user_db=None):
    """Show the Follow-ups page."""
    st.write("Follow-ups page content goes here.")

async def show_value_waterfall(user_db=None):
    """Show the Value Rollercoaster page."""
    st.write("Value Rollercoaster page content goes here.")

async def show_buyer_persona(user_db=None):
    await persona_tab()  # type: ignore[awaitable]

async def show_value_roi(user_db=None):
    """Show the ROI analysis page."""
    st.write("ROI Analysis page content goes here.")

async def refresh_value_components_ui(user_db=None):
    try:
        logging.warning("[ui.py] refresh_value_components_ui called")
        with ui_refresh_spinner():
            if user_db:
                all_components = user_db.fetch_user_value_components()
            else:
                # FIX: Get user_id from session state and pass it to fetch_all_value_components
                user_id = st.session_state.get('user_id', None)
                all_components = fetch_all_value_components(user_id=user_id)
        for main_cat, components_list in all_components.items() if isinstance(all_components, dict) else []:
            subcategories = {}
            for comp in components_list:
                sub_cat = comp.get("category", "")
                if sub_cat not in subcategories:
                    subcategories[sub_cat] = []
                subcategories[sub_cat].append(comp)
            for sub_cat, comps in subcategories.items():
                for comp_data in comps:
                    comp_name = comp_data.get("name", "")
                    original_val = comp_data.get("original_value", "")
                    ai_processed_val = comp_data.get("ai_processed_value", "")
                    user_rating = comp_data.get("user_rating", 1)
                    rating_key = f"rating_{main_cat}_{sub_cat}_{comp_name}"
                    if comp_name:
                        st.session_state.value_components[main_cat][sub_cat][comp_name] = original_val
                        st.session_state.ai_processed_values[main_cat][sub_cat][comp_name] = ai_processed_val
        logging.warning("[ui.py] refresh_value_components_ui end, returning asyncio.sleep(0)")
        await asyncio.sleep(0)
        return None
    except Exception as e:
        logging.error(f"[ui.py] Error in refresh_value_components_ui: {e}")
        raise
        return asyncio.sleep(0)

async def generate_initial_value_components(user_id: str):
    """Generate initial value components based on company profile and website data."""
    try:
        from app.core.company_context_manager import CompanyContextManager
        from app.components.demo_companies.demo_populator import DemoPopulator
        from app.company_website_enhancer import get_enhanced_prompts, get_website_enhancement_status
        
        # Get company profile
        company_context = CompanyContextManager()
        company_profile = company_context.get_company_profile()
        
        if not company_profile:
            st.error("❌ No company profile found. Please configure your company profile first.")
            return
        
        # Check if website enhancement is available
        website_status = get_website_enhancement_status()
        if website_status['available']:
            st.info(f"🌐 Using website data from {website_status['website_url']} to enhance value components generation")
        
        # Use demo populator to generate components based on real company data
        populator = DemoPopulator()
        
        # Show progress indicator while generating and saving
        with st.spinner("Generating initial value components..."):
            # Generate value components based on company profile (real companies can use website data)
            value_components = populator._generate_value_components(company_profile, use_website_data=True)
        
        # Save components to database
        from app.database import save_value_component
        saved_count = 0
        
        for main_cat, subcats in value_components.items():
            for sub_cat, components in subcats.items():
                for comp_name, comp_value in components.items():
                    component_data = {
                        "main_category": main_cat,
                        "category": sub_cat,
                        "name": comp_name,
                        "original_value": comp_value,
                        "ai_processed_value": comp_value,  # Use same value initially
                        "user_id": user_id,
                        "weight": len(comp_value) if comp_value else 1,
                        "user_rating": 3  # Default rating
                    }
                    
                    if save_value_component(component_data):
                        saved_count += 1
        
        if saved_count > 0:
            st.success(f"✅ Generated {saved_count} initial value components based on your company profile!")
            st.cache_data.clear()  # Clear cache to reload data
            # Clear generating flag before rerun
            st.session_state.is_generating_initial_value_components = False
            st.rerun()
        else:
            st.error("❌ Failed to save value components. Please try again.")
            st.session_state.is_generating_initial_value_components = False
            
    except Exception as e:
        st.error(f"❌ Error generating initial value components: {str(e)}")
        logging.error(f"Error generating initial value components: {e}")
        st.session_state.is_generating_initial_value_components = False


