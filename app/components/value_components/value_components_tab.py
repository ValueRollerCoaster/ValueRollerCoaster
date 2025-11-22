from app.components.value_components.header import render_value_components_header
# from app.components.value_components.category_selector import render_category_selector  # No longer needed
from app.components.value_components.components_tab import render_components_tab
from app.components.value_components.distribution_tab import render_distribution_tab
from app.categories import COMPONENT_STRUCTURES
import streamlit as st
from app.components.value_components.summary_sunburst import render_company_overview_sunburst
from app.database import fetch_all_value_components
from app.utils.demo_data_integration import demo_function
from app.database import delete_all_value_components
from app.utils.spinner import ui_refresh_spinner
from app.components.demo_companies import DemoIntegration

async def render_value_components_tab(value_components, ai_processed_values, process_value_with_ai, calculate_and_save_value_bricks, refresh_callback=None, selected_main_category=None):
    if "main_tab_mode" not in st.session_state:
        st.session_state["main_tab_mode"] = "Components"
    from app.categories import COMPONENT_STRUCTURES
    # Use the parameter passed to the function, fallback to session state
    selected_tab = selected_main_category if selected_main_category else st.session_state.get("selected_main_category", "Summary")

    # Detect demo mode toggle and force immediate refresh of data source
    curr_demo_mode = st.session_state.get("user_demo_mode", False)
    prev_demo_mode = st.session_state.get("prev_user_demo_mode", curr_demo_mode)
    if prev_demo_mode != curr_demo_mode:
        # Clear cached data and session copies to avoid stale view
        try:
            st.cache_data.clear()
        except Exception:
            pass
        # Reset in-memory structures so fresh DB data is loaded
        st.session_state.value_components = {}
        st.session_state.ai_processed_values = {}
        # Clear any demo-related flags to ensure clean switch
        if not curr_demo_mode:
            # Switching FROM demo TO normal - clear demo toast flags
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("demo_saved_data_toast_shown_"):
                    st.session_state[key] = False
        st.session_state.prev_user_demo_mode = curr_demo_mode
        st.rerun()
    else:
        st.session_state.prev_user_demo_mode = curr_demo_mode
    
    # Add demo mode indicator as toast notification
    user_demo_mode = st.session_state.get("user_demo_mode", False)
    if user_demo_mode and not st.session_state.get("demo_mode_toast_shown", False):
        st.toast("🎭 **Demo Mode Active** - Value components still required for quality personas", icon="🎭")
        st.session_state.demo_mode_toast_shown = True

    st.markdown("""
    <style>
    [data-testid='stRadio'] > div {
        display: flex;
        gap: 0;
    }
    [data-testid='stRadio'] label {
        border-radius: 8px 8px 0 0;
        padding: 0.6em 1.5em;
        font-size: 1.2em;
        font-weight: 800;
        background: #f5f5f5;
        color: #222;
        border-bottom: 3px solid transparent;
        margin-right: 0;
        cursor: pointer;
    }
    [data-testid='stRadio'] label[data-selected='true'] {
        background: #b6f5c6 !important;
        color: #1a4d2e !important;
        border-bottom: 3px solid #4be07b;
        z-index: 2;
    }
    
    /* Aggressive spacing reduction for better layout */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    
    /* Remove all margins between elements */
    .stMarkdown {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Minimize column spacing */
    .stColumn {
        padding: 0.1rem;
    }
    
    /* Reduce spacing in columns */
    .stColumn > div {
        margin-bottom: 0 !important;
    }
    
    /* Remove extra spacing from title */
    h1 {
        margin-bottom: 0.5rem !important;
    }
    
    /* 3-column layout optimization */
    .stColumn:first-child {
        padding-right: 0.25rem !important;
        padding-left: 0 !important;
    }
    
    .stColumn:nth-child(2) {
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
    }
    
    .stColumn:last-child {
        padding-left: 0.25rem !important;
        padding-right: 0 !important;
    }
    
    /* Force chart to align left */
    .stColumn:first-child > div {
        text-align: left !important;
    }
    
    /* Optimize chart container positioning */
    .stPlotlyChart {
        margin-left: 0 !important;
        margin-right: auto !important;
    }
    /* Add more space between chart and demo options */
    .stColumn:nth-child(2) {
        margin-left: 1rem !important;
    }
    /* Ensure demo options have proper spacing */
    .stColumn:nth-child(2) > div {
        padding-left: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if selected_tab == "Summary":
        # Create a header row with title and control buttons
        col_title, col_controls = st.columns([3, 1])
        
        with col_title:
            st.title("Company Value Overview")
        
        with col_controls:
            # Control buttons for value components management - ONLY when user demo mode is NOT active
            user_demo_mode = st.session_state.get("user_demo_mode", False)
            
            # Only show control buttons if user demo mode is NOT active
            if not user_demo_mode:
                st.markdown("<br>", unsafe_allow_html=True)  # Add some vertical spacing
                
                # Check if there are any value components loaded
                from app.components.demo_companies.demo_profile_manager import demo_profile_manager
                user_id = demo_profile_manager.get_current_user_id()
                all_components = fetch_all_value_components(user_id=user_id)
                has_components = isinstance(all_components, (dict, list)) and len(all_components) > 0
                
                if has_components:
                    # Show control buttons in a vertical layout
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("🗑️ Clear All", help="Clear all value components and start over", type="secondary", use_container_width=True):
                            st.session_state.clear_all_data = True
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("⚡ Generate Missing", help="Generate input for missing fields", type="secondary", use_container_width=True):
                            st.session_state.generate_missing_fields = True
                            st.rerun()
                    
                    # Additional button for full regeneration
                    if st.button("🔄 Regenerate All", help="Regenerate all value components from scratch", type="primary", use_container_width=True):
                        st.session_state.regenerate_all_components = True
                        st.rerun()
                # When no components exist, don't show any buttons in the control area
            # When demo mode is active, just show empty space (no message)
        
        # 3-column layout for better control - more space for chart, demo options pushed right
        col1, col2, col3 = st.columns([1.8, 0.7, 0.4])
        
        with col1:
            # Main chart area - left aligned
            # Check if we're in demo mode to determine what data to show
            user_demo_mode = st.session_state.get("user_demo_mode", False)
            
            if user_demo_mode:
                # Demo mode active - show demo data or blank chart
                from app.components.demo_companies.demo_profile_manager import demo_profile_manager
                from app.components.demo_companies.demo_integration import DemoIntegration
                
                demo_integration = DemoIntegration()
                
                if demo_integration.is_demo_mode_active():
                    # Demo company is selected - prioritize DB data (preserves user edits)
                    demo_company_id = demo_profile_manager.get_current_demo_company_id()
                    if demo_company_id:
                        user_id = demo_profile_manager.get_current_user_id()
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"[value_components_tab.py] Demo mode - demo_company_id={demo_company_id}, user_id={user_id}")
                        # First: fetch from DB (may contain user edits)
                        all_components = fetch_all_value_components(user_id=user_id)
                        
                        # Check if DB has data (handle both dict and list formats)
                        has_db_data = False
                        if isinstance(all_components, dict):
                            has_db_data = len(all_components) > 0
                        elif isinstance(all_components, list):
                            has_db_data = len(all_components) > 0
                        
                        # Show toast if saved changes exist (once per demo company)
                        toast_key = f"demo_saved_data_toast_shown_{demo_company_id}"
                        if has_db_data:
                            if not st.session_state.get(toast_key, False):
                                st.toast("💾 Using your saved changes for this demo company", icon="💾")
                                st.session_state[toast_key] = True
                        
                        # Fallback: if DB is empty, use inline demo profile data (first-time load)
                        if not has_db_data:
                            demo_company = demo_profile_manager.get_demo_company_profile(demo_company_id)
                            all_components = demo_company.get('value_components', []) if demo_company else []
                            # Reset toast flag when using fresh demo data
                            if all_components:
                                st.session_state[toast_key] = False
                    else:
                        all_components = []
                else:
                    # No demo company selected - show blank chart
                    all_components = []
            else:
                # Normal mode - show real company data (use the authenticated session user id)
                # Use demo_profile_manager.get_current_user_id() which handles mode switching correctly
                from app.components.demo_companies.demo_profile_manager import demo_profile_manager
                import logging
                session_user_id = demo_profile_manager.get_current_user_id()
                logger = logging.getLogger(__name__)
                logger.warning(f"[value_components_tab.py] Normal mode - session_user_id={session_user_id}")
                all_components = fetch_all_value_components(user_id=session_user_id)
            
            # Debug: Log the components data
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[value_components_tab.py] Chart rendering - demo_mode={user_demo_mode}")
            if isinstance(all_components, dict):
                logger.warning(f"[value_components_tab.py] Components type: dict, keys: {list(all_components.keys())}, total_items: {sum(len(v) if isinstance(v, list) else 1 for v in all_components.values())}")
            elif isinstance(all_components, list):
                logger.warning(f"[value_components_tab.py] Components type: list, length: {len(all_components)}")
                if all_components:
                    logger.warning(f"[value_components_tab.py] First component: {all_components[0]}")
            else:
                logger.warning(f"[value_components_tab.py] Components type: {type(all_components)}, value: {all_components}")
            
            # Render the chart here to align with demo options (handles empty data gracefully)
            # render_company_overview_sunburst is async
            result = await render_company_overview_sunburst(all_components)  # type: ignore[awaitable]
        
        with col2:
            # Demo options - only visible when demo mode is enabled and active
            from app.config import ENABLE_DEMO_MODE
            user_demo_mode = st.session_state.get("user_demo_mode", False)
            
            if ENABLE_DEMO_MODE and user_demo_mode:
                demo_integration = DemoIntegration()
                
                # Check if demo data is already populated
                if demo_integration.is_demo_mode_active():
                    # Show demo mode indicator only
                    demo_integration.render_demo_mode_indicator()
                else:
                    # Show demo company selector
                    selected_company_id = await demo_integration.render_demo_company_selector()
                
        
        with col3:
            # Demo action buttons - positioned to the right (original behavior)
            if ENABLE_DEMO_MODE and user_demo_mode:
                demo_integration = DemoIntegration()
                
                # Only show Load Demo button if no demo is currently active
                if not demo_integration.is_demo_mode_active():
                    # Show Load Demo Data button if company is selected
                    selected_company_id = demo_integration.render_load_demo_button()
                    if selected_company_id:
                        await demo_integration._handle_demo_data_loading(selected_company_id)
                
                # Always show clear data button
                if st.button("🗑️ Clear Data", help="Clear all value component data", type="secondary"):
                    st.session_state.clear_all_data = True
        
        # Handle non-demo mode
        if not user_demo_mode:
            st.markdown("""
            <div style='text-align: center; padding: 0.8em; background: #f8f9fa; border-radius: 8px; color: #6c757d;'>
                <div style='font-size: 0.9em;'>Enable DEMO Mode in sidebar to access demo options</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Handle demo button click
        if st.session_state.get('demo_button_clicked', False):
            st.session_state.demo_button_clicked = False
            preserve_existing = st.session_state.get('demo_preserve_existing', True)
            await handle_demo_data_population(preserve_existing)
        
        # Handle clear all data
        if st.session_state.get('clear_all_data', False):
            st.session_state.clear_all_data = False
            await handle_clear_all_data()
        
        # Handle generate missing fields
        if st.session_state.get('generate_missing_fields', False):
            st.session_state.generate_missing_fields = False
            await handle_generate_missing_fields()
        
        # Handle regenerate all components
        if st.session_state.get('regenerate_all_components', False):
            st.session_state.regenerate_all_components = False
            await handle_regenerate_all_components()
        
        # Note: Generate initial components is handled elsewhere in the UI
        
        st.markdown("</br></br>", unsafe_allow_html=True)
        
        # Chart is now rendered in the column layout above
    else:
        render_value_components_header(selected_tab)
        if "main_tab_mode" not in st.session_state:
            st.session_state["main_tab_mode"] = "Components"
        options2 = ["Components", "Distribution & Summary"]
        default_tab2 = options2[0]
        current_tab2 = st.session_state.get("selected_tab2", default_tab2)
        if current_tab2 not in options2:
            current_tab2 = default_tab2
        selected_tab2 = st.pills(
            label="Section2",
            options=options2,
            default=current_tab2,
            key="selected_tab2_pills",
            label_visibility="collapsed"
        )
        st.markdown("<div style='height: 1.5em'></div>", unsafe_allow_html=True)
        if selected_tab2 == "Components":
            await render_components_tab(selected_tab, value_components, ai_processed_values, process_value_with_ai, calculate_and_save_value_bricks, refresh_callback)
        else:
            render_distribution_tab(selected_tab, value_components)
    return selected_tab

async def handle_demo_data_population(preserve_existing: bool = True):
    """Handle demo data population when demo button is clicked"""
    try:
        from app.components.demo_companies.demo_profile_manager import demo_profile_manager
        user_id = demo_profile_manager.get_current_user_id()
        
        # Show appropriate loading message
        if preserve_existing:
            existing_count = _count_existing_data()
            loading_msg = f"🎯 Loading demo data (preserving {existing_count} existing fields)..."
        else:
            loading_msg = "🔄 Loading demo data (replacing all existing data)..."
        
        with st.spinner(loading_msg):
            # Populate demo data
            if hasattr(demo_function, 'populate_demo_data'):
                result = await demo_function.populate_demo_data(user_id, preserve_existing)  # type: ignore[attr-defined]
            else:
                st.error("Demo function does not support populate_demo_data")
                return
            
            if result and result.get("success") and (result.get("components") or result.get("customers")):
                # Update session state with new demo data structure
                if hasattr(demo_function, 'update_session_state'):
                    demo_function.update_session_state(  # type: ignore[attr-defined]
                        result.get("components", {}), 
                        result.get("customers", {})
                    )
                
                # Show appropriate success message
                if preserve_existing:
                    st.success("✅ Demo data loaded successfully! Empty fields have been populated with realistic sample data while preserving your existing content.")
                else:
                    st.success("✅ Demo data loaded successfully! All value component fields have been populated with realistic sample data and AI customer benefits have been generated.")
                
                # Force refresh
                st.rerun()
            else:
                st.error("❌ Failed to load demo data. Please try again.")
                
    except Exception as e:
        st.error(f"❌ Error loading demo data: {str(e)}")

def _count_existing_data() -> int:
    """Count how many fields have existing data"""
    count = 0
    try:
        value_components = st.session_state.get('value_components', {})
        for main_cat in value_components.values():
            if isinstance(main_cat, dict):
                for sub_cat in main_cat.values():
                    if isinstance(sub_cat, dict):
                        for value in sub_cat.values():
                            if value and str(value).strip():
                                count += 1
    except (AttributeError, TypeError):
        pass
    return count

async def handle_clear_all_data():
    """Handle clearing all value component data"""
    try:
        from app.components.demo_companies.demo_profile_manager import demo_profile_manager
        
        # Check if we're in demo mode
        if demo_profile_manager.is_demo_mode_active():
            # Clear demo company data and reset to defaults
            demo_company_id = demo_profile_manager.get_current_demo_company_id()
            if demo_company_id:
                result = await demo_profile_manager.clear_demo_company_data(demo_company_id)
                if result.get("success"):
                    st.success(f"🗑️ Demo company data cleared successfully!")
                else:
                    st.error(f"❌ Failed to clear demo data: {result.get('error', 'Unknown error')}")
            else:
                st.error("❌ No demo company selected")
        else:
            # Clear real company data
            from app.components.demo_companies.demo_profile_manager import demo_profile_manager
            user_id = demo_profile_manager.get_current_user_id()
            
            # Clear from database
            if user_id:
                delete_all_value_components(user_id)
            
            # Clear session state
            st.session_state.value_components = {}
            st.session_state.ai_processed_values = {}
            st.session_state.demo_data_populated = False
            
            # Show success message
            st.success("🗑️ All value component data has been cleared.")
        
        # Force refresh
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error clearing data: {str(e)}")

async def handle_generate_missing_fields():
    """Handle generating input for missing fields"""
    try:
        from app.components.demo_companies.demo_profile_manager import demo_profile_manager
        from app.database import fetch_all_value_components, save_value_component
        from app.logic import analyze_technical_subcategory_components
        import asyncio
        
        user_id = demo_profile_manager.get_current_user_id()
        all_components = fetch_all_value_components(user_id=user_id)
        
        if not all_components:
            st.warning("⚠️ No value components found to generate missing fields for.")
            return
        
        # Find missing or empty fields
        missing_fields = []
        
        if isinstance(all_components, dict):
            for main_category, categories in all_components.items():
                if isinstance(categories, dict):
                    for subcategory, components in categories.items():
                        if isinstance(components, list):
                            for component in components:
                                if not component.get('ai_processed_value', '').strip():
                                    missing_fields.append({
                                        'main_category': main_category,
                                        'category': subcategory,
                                        'name': component.get('name', ''),
                                        'original_value': component.get('original_value', ''),
                                        'user_id': user_id
                                    })
        
        if not missing_fields:
            st.success("✅ All fields are already complete!")
            return
        
        # Show progress
        with st.spinner(f"Generating AI input for {len(missing_fields)} missing fields..."):
            # Process missing fields in batches
            batch_size = 5
            for i in range(0, len(missing_fields), batch_size):
                batch = missing_fields[i:i + batch_size]
                
                # Group by main category for AI processing
                ai_input = {}
                for field in batch:
                    if field['original_value']:
                        ai_input[field['name']] = field['original_value']
                
                if ai_input:
                    # Generate AI content
                    try:
                        ai_results = await analyze_technical_subcategory_components(
                            batch[0]['main_category'], 
                            ai_input, 
                            list(ai_input.keys())
                        )
                        
                        # Save results
                        for field in batch:
                            if ai_results and field['name'] in ai_results:
                                ai_benefit = ai_results[field['name']].get('value_proposition', '') if isinstance(ai_results[field['name']], dict) else ''
                                if ai_benefit:
                                    component_data = {
                                        'main_category': field['main_category'],
                                        'category': field['category'],
                                        'name': field['name'],
                                        'original_value': field['original_value'],
                                        'ai_processed_value': ai_benefit,
                                        'user_id': field['user_id']
                                    }
                                    save_value_component(component_data)
                    except Exception as e:
                        st.warning(f"⚠️ Could not generate AI content for batch: {e}")
                        continue
        
        st.success(f"✅ Generated AI input for {len(missing_fields)} missing fields!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error generating missing fields: {e}")

async def handle_regenerate_all_components():
    """Handle regenerating all value components from scratch"""
    try:
        from app.components.demo_companies.demo_profile_manager import demo_profile_manager
        from app.database import fetch_all_value_components, save_value_component
        from app.logic import analyze_technical_subcategory_components
        import asyncio
        
        user_id = demo_profile_manager.get_current_user_id()
        all_components = fetch_all_value_components(user_id=user_id)
        
        if not all_components:
            st.warning("⚠️ No value components found to regenerate.")
            return
        
        # Get all components that have original values
        components_to_regenerate = []
        
        if isinstance(all_components, dict):
            for main_category, categories in all_components.items():
                if isinstance(categories, dict):
                    for subcategory, components in categories.items():
                        if isinstance(components, list):
                            for component in components:
                                if component.get('original_value', '').strip():
                                    components_to_regenerate.append({
                                        'main_category': main_category,
                                        'category': subcategory,
                                        'name': component.get('name', ''),
                                        'original_value': component.get('original_value', ''),
                                        'user_id': user_id
                                    })
        
        if not components_to_regenerate:
            st.warning("⚠️ No components with original values found to regenerate.")
            return
        
        # Show progress
        with st.spinner(f"Regenerating AI content for {len(components_to_regenerate)} components..."):
            # Process components in batches
            batch_size = 5
            for i in range(0, len(components_to_regenerate), batch_size):
                batch = components_to_regenerate[i:i + batch_size]
                
                # Group by main category for AI processing
                ai_input = {}
                for component in batch:
                    ai_input[component['name']] = component['original_value']
                
                if ai_input:
                    # Generate AI content
                    try:
                        ai_results = await analyze_technical_subcategory_components(
                            batch[0]['main_category'], 
                            ai_input, 
                            list(ai_input.keys())
                        )
                        
                        # Save results
                        for component in batch:
                            if ai_results and component['name'] in ai_results:
                                ai_benefit = ai_results[component['name']].get('value_proposition', '') if isinstance(ai_results[component['name']], dict) else ''
                                if ai_benefit:
                                    component_data = {
                                        'main_category': component['main_category'],
                                        'category': component['category'],
                                        'name': component['name'],
                                        'original_value': component['original_value'],
                                        'ai_processed_value': ai_benefit,
                                        'user_id': component['user_id']
                                    }
                                    save_value_component(component_data)
                    except Exception as e:
                        st.warning(f"⚠️ Could not regenerate AI content for batch: {e}")
                        continue
        
        st.success(f"✅ Regenerated AI content for {len(components_to_regenerate)} components!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error regenerating components: {e}")

# Note: handle_generate_initial_components function removed as it's handled elsewhere in the UI 