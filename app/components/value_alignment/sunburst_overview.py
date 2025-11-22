import streamlit as st
import plotly.express as px
import pandas as pd
import logging
from app.database import fetch_all_value_components
from app.components.demo_companies.demo_profile_manager import demo_profile_manager
from app.components.value_alignment.component_lookup import find_component_in_db

logger = logging.getLogger(__name__)

def summarize_text(text, max_words=3):
    words = text.split()
    return ' '.join(words[:max_words]) + ('...' if len(words) > max_words else '')


def render_sunburst_overview(alignment_matrix):
    if not alignment_matrix:
        return
    
    # Fetch all value components from database for lookup
    try:
        user_id = demo_profile_manager.get_current_user_id()
        all_db_components = fetch_all_value_components(user_id=user_id)
        logger.info(f"[sunburst_overview] Loaded {sum(len(v) for v in all_db_components.values())} components from DB for lookup")
    except Exception as e:
        logger.warning(f"[sunburst_overview] Failed to load components from DB: {e}. Using keyword categorization only.")
        all_db_components = {}
    
    # Prepare data for sunburst: Root > Value Category > Subcategory > Component
    sunburst_rows = []
    for item in alignment_matrix:
        value_component = item.get('our_value_component', 'N/A')
        score = item.get('match_score_percent', 0)
        
        if not value_component or value_component == 'N/A':
            continue
        
        # Get customer need for hover
        customer_need = item.get('prospect_need', '') or item.get('customer_need', '')
        
        # Look up the component in the database to get the full value path
        # The alignment_matrix contains component names that were matched during value alignment
        # We need to find the actual component in DB to get its hierarchy: main_category → category → name
        db_component = find_component_in_db(value_component, all_db_components)
        
        if db_component:
            # Use the actual component data from database - this is the source of truth
            value_category = db_component.get('main_category', 'Unknown')
            subcategory = db_component.get('category', 'Unknown')
            component = db_component.get('name', value_component)
            logger.info(f"[sunburst_overview] Found component in DB: '{value_component}' -> {value_category}/{subcategory}/{component}")
        else:
            # Component not found in database - this indicates a data consistency issue
            # The alignment_matrix contains component names that should exist in the database
            # Skip this item to maintain data integrity (showing incorrect category would be worse than not showing it)
            logger.warning(f"[sunburst_overview] Component '{value_component}' not found in database. This suggests:"
                          f" (1) Component was deleted/renamed in DB, (2) Name mismatch in alignment_matrix,"
                          f" or (3) Database lookup failed. Skipping this alignment item to maintain data integrity.")
            continue
        
        sunburst_rows.append({
            'Root': 'Value Alignment',
            'Value Category': value_category,
            'Subcategory': subcategory,
            'Component': component,
            'Component_full': value_component,
            'Customer_Need': customer_need,
            'Score': score
        })
    
    if not sunburst_rows:
        logger.warning("[sunburst_overview] No rows generated from alignment_matrix")
        st.info("No valid alignment data available for visualization.")
        return
    
    logger.info(f"[sunburst_overview] Generated {len(sunburst_rows)} sunburst rows from {len(alignment_matrix)} alignment items")
    df_sunburst = pd.DataFrame(sunburst_rows)
    
    # Mark all rows as leaf nodes (Component level) - these are the outermost ring
    df_sunburst['is_leaf'] = True
    
    # Build mappings for parent node lookup
    # Map (Value Category, Subcategory) -> list of components
    subcategory_to_components = {}
    for _, row in df_sunburst.iterrows():
        key = (row['Value Category'], row['Subcategory'])
        if key not in subcategory_to_components:
            subcategory_to_components[key] = []
        subcategory_to_components[key].append({
            'component': row['Component_full'],
            'subcategory': row['Subcategory'],
            'customer_need': row['Customer_Need'],
            'score': row['Score']
        })
    
    # Map Value Category -> list of all components
    category_to_components = {}
    for _, row in df_sunburst.iterrows():
        key = row['Value Category']
        if key not in category_to_components:
            category_to_components[key] = []
        category_to_components[key].append({
            'component': row['Component_full'],
            'subcategory': row['Subcategory'],
            'customer_need': row['Customer_Need'],
            'score': row['Score']
        })
    
    # Log what we're creating to verify only matched components
    logger.info(f"[sunburst_overview] Components to display: {df_sunburst['Component_full'].tolist()}")
    
    # Don't use hover_data - we'll manually set customdata only for leaf nodes
    fig = px.sunburst(
        df_sunburst,
        path=['Root', 'Value Category', 'Subcategory', 'Component'],
        values='Score',
        color='Value Category',
        color_discrete_sequence=px.colors.qualitative.Set3,
        maxdepth=3
    )
    
    # Manually set customdata ONLY for leaf nodes (outermost ring components)
    # Customdata structure: [Component_full, Subcategory, Customer_Need, Score]
    # First, get all points that Plotly created
    if hasattr(fig, 'data') and fig.data and isinstance(fig.data, (list, tuple)) and len(fig.data) > 0:
        if hasattr(fig.data[0], 'labels') and fig.data[0].labels is not None:
            labels_list = list(fig.data[0].labels) if hasattr(fig.data[0].labels, '__len__') else []
            num_points = len(labels_list)
        else:
            labels_list = []
            num_points = 0
    else:
        labels_list = []
        num_points = 0
    leaf_component_names = set(df_sunburst['Component'].str.lower().str.strip())
    
    # Build customdata array - only leaf nodes get data, parent nodes get None
    customdata_array = []
    for i in range(num_points):
        label = labels_list[i] if i < len(labels_list) else ""
        if label and str(label).lower().strip() in leaf_component_names:
            # This is a leaf node - find matching row in DataFrame
            matching_row = df_sunburst[df_sunburst['Component'].str.lower().str.strip() == str(label).lower().strip()]
            if not matching_row.empty:
                row = matching_row.iloc[0]
                customdata_array.append([
                    row['Component_full'],
                    row['Subcategory'],
                    row['Customer_Need'],
                    row['Score']
                ])
            else:
                customdata_array.append(None)
        else:
            # Parent node - no customdata
            customdata_array.append(None)
    
    # Set customdata on the figure
    if hasattr(fig, 'data') and fig.data and isinstance(fig.data, (list, tuple)) and len(fig.data) > 0:
        fig.data[0].customdata = customdata_array  # type: ignore[attr-defined]
    
    # Update traces first to ensure proper initialization
    fig.update_traces(
        textinfo='label',
        insidetextorientation='auto',
        textfont_size=18
    )
    
    # Build per-point hovertemplate - show detailed info ONLY on outermost ring (leaf nodes)
    # Customdata structure: [Component_full, Subcategory, Customer_Need, Score]
    # Display order: 1. Customer Need, 2. Component, 3. Subcategory (one level higher), 4. Match Score
    try:
        hover_templates = []
        for i in range(num_points):
            customdata = customdata_array[i]
            
            # Only show hover if customdata exists (leaf nodes only)
            if customdata and isinstance(customdata, (list, tuple)) and len(customdata) >= 4:
                customer_need = customdata[2]
                component_full = customdata[0]
                subcategory = customdata[1]
                score = customdata[3]
                
                # Verify data is valid (allow empty customer_need but require component)
                if component_full and str(component_full).strip():
                    # Leaf node - show detailed hover in specified order
                    customer_need_display = str(customer_need).strip() if customer_need else "N/A"
                    hover_templates.append(
                        '<span style="width:300px;white-space:normal;display:inline-block;">' +
                        '<b>Customer Need:</b><br>%{customdata[2]}<br><br>' +
                        '<b>Matched component:</b><br> %{customdata[0]} [%{customdata[1]}]<br><br>' +
                        '<b>Match Score:</b> %{customdata[3]}%' +
                        '</span><extra></extra>'
                    )
                else:
                    # Invalid data - suppress hover
                    hover_templates.append('<extra></extra>')
            else:
                # Parent node or no data - check if it has multiple children
                label = labels_list[i] if i < len(labels_list) else ""
                matching_components = []
                
                # Try to match by label to find matching components
                for (val_cat, subcat), components in subcategory_to_components.items():
                    if label and str(label).strip().lower() == str(subcat).strip().lower():
                        matching_components = components
                        break
                
                if not matching_components:
                    for val_cat, components in category_to_components.items():
                        if label and str(label).strip().lower() == str(val_cat).strip().lower():
                            matching_components = components
                            break
                
                # Show hover for parent nodes with 1 or more children (consistent format for all cases)
                if matching_components and len(matching_components) >= 1:
                    component_list_parts = []
                    for comp in matching_components[:5]:  # Limit to 5 for display
                        component_list_parts.append(f"• {comp['component']} [{comp['subcategory']}] ({comp['score']}%)")
                    component_list = '<br>'.join(component_list_parts)
                    
                    if len(matching_components) > 5:
                        component_list += f"<br>... and {len(matching_components) - 5} more"
                    
                    # Use consistent format: "X component(s) matched:" for both singular and plural
                    component_text = "component" if len(matching_components) == 1 else "components"
                    hover_templates.append(
                        '<span style="width:300px;white-space:normal;display:inline-block;">' +
                        f'<b>{label}</b><br><br>' +
                        f'<b>{len(matching_components)} {component_text} matched:</b><br>' +
                        component_list +
                        '</span><extra></extra>'
                    )
                else:
                    # Root node or unmatched - suppress hover
                    hover_templates.append('<extra></extra>')
        
        # Apply per-point hovertemplates
        if hasattr(fig, 'data') and fig.data and isinstance(fig.data, (list, tuple)) and len(fig.data) > 0:
            if len(hover_templates) == num_points:
                fig.data[0].hovertemplate = hover_templates  # type: ignore[attr-defined]
                num_leaf = sum(1 for t in hover_templates if '<b>Customer Need:</b>' in t)
                num_parent = sum(1 for t in hover_templates if 'components matched:' in t)
                logger.info(f"[sunburst_overview] Set {len(hover_templates)} hovertemplates ({num_leaf} leaf nodes, {num_parent} parent nodes with multiple children, {num_points - num_leaf - num_parent} suppressed)")
            else:
                logger.error(f"[sunburst_overview] Template count mismatch: {len(hover_templates)} != {num_points}")
                # Emergency: suppress all hover
                fig.data[0].hovertemplate = ['<extra></extra>'] * num_points  # type: ignore[attr-defined]
    except Exception as e:
        logger.error(f"[sunburst_overview] Failed to set hovertemplates: {e}")
        import traceback
        logger.error(f"[sunburst_overview] Traceback: {traceback.format_exc()}")
        # Emergency: suppress all hover
        try:
            if hasattr(fig, 'data') and fig.data and isinstance(fig.data, (list, tuple)) and len(fig.data) > 0:
                fig.data[0].hovertemplate = ['<extra></extra>'] * num_points  # type: ignore[attr-defined]
        except:
            pass
    
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        height=500,
        title_text='',  # Remove chart title
        showlegend=False,  # Hide default legend since we have custom one
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)'   # Transparent paper background
    )
    st.plotly_chart(fig, use_container_width=True) 