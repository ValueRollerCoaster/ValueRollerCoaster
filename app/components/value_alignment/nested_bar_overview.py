import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any
import re

def categorize_value_component(component_name: str) -> str:
    """Categorize value component based on keywords."""
    component_lower = component_name.lower()
    
    # Technical keywords
    technical_keywords = ['technology', 'technical', 'innovation', 'product', 'development', 'engineering', 'automation', 'performance', 'quality', 'efficiency', 'sustainability']
    if any(keyword in component_lower for keyword in technical_keywords):
        return 'Technical Value'
    
    # Strategic keywords
    strategic_keywords = ['strategy', 'strategic', 'leadership', 'market', 'growth', 'expansion', 'competitive', 'positioning', 'vision', 'mission']
    if any(keyword in component_lower for keyword in strategic_keywords):
        return 'Strategic Value'
    
    # Business keywords
    business_keywords = ['business', 'financial', 'profit', 'revenue', 'cost', 'efficiency', 'operations', 'management', 'customer', 'satisfaction']
    if any(keyword in component_lower for keyword in business_keywords):
        return 'Business Value'
    
    # After-sales keywords
    after_keywords = ['after', 'support', 'service', 'maintenance', 'training', 'warranty', 'repair', 'customer care']
    if any(keyword in component_lower for keyword in after_keywords):
        return 'After Sales Value'
    
    # Default to Strategic Value for any unmatched components
    return 'Strategic Value'

def get_category_color(category: str) -> str:
    """Get color for each category."""
    colors = {
        'Technical Value': '#1f77b4',      # Blue
        'Strategic Value': '#d62728',      # Red
        'Business Value': '#9467bd',       # Purple
        'After Sales Value': '#ff7f0e',    # Orange
    }
    return colors.get(category, '#7f7f7f')  # Default gray for any unmatched

def calculate_component_shares(alignment_matrix: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate percentage shares of value components within each customer need."""
    processed_data = []
    
    for item in alignment_matrix:
        customer_need = item.get('prospect_need', '') or item.get('customer_need', '')
        value_component = item.get('our_value_component', '')
        match_score = item.get('match_score_percent', 0)
        
        if not customer_need or not value_component:
            continue
        
        # Extract value components from the string (e.g., "business value: energy efficiency & technical value: circular economy")
        components = extract_value_components(value_component)
        
        if not components:
            # If no components extracted, treat the whole string as one component
            components = [{
                'name': value_component,
                'category': categorize_value_component(value_component)
            }]
        
        # Calculate total score for this customer need (use match_score as the total)
        total_score = match_score
        
        # Distribute the match score among components (equal distribution for now)
        component_count = len(components)
        score_per_component = total_score / component_count if component_count > 0 else 0
        
        # Calculate percentage shares for each component
        components_with_shares = []
        for comp in components:
            percentage = (score_per_component / total_score) * 100 if total_score > 0 else 0
            
            components_with_shares.append({
                'name': comp['name'],
                'alignment_score': score_per_component,
                'percentage_share': percentage,
                'category': comp['category']
            })
        
        processed_data.append({
            'customer_need': customer_need,
            'total_score': total_score,  # This is the bar length
            'components': components_with_shares
        })
    
    return processed_data

def extract_value_components(value_component_string: str) -> List[Dict[str, str]]:
    """Extract individual value components from a combined string."""
    components = []
    
    # Split by common separators
    parts = re.split(r'\s*[&|,]\s*', value_component_string)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Check if it has a category prefix (e.g., "business value:", "technical value:")
        category_match = re.match(r'(\w+)\s+value:\s*(.+)', part, re.IGNORECASE)
        if category_match:
            category_word = category_match.group(1).title()
            # Map to full category name
            if category_word == 'Technical':
                category = 'Technical Value'
            elif category_word == 'Business':
                category = 'Business Value'
            elif category_word == 'Strategic':
                category = 'Strategic Value'
            elif category_word == 'After':
                category = 'After Sales Value'
            else:
                category = categorize_value_component(part)
            name = category_match.group(2).strip()
        else:
            # No category prefix, categorize based on content
            category = categorize_value_component(part)
            name = part
        
        components.append({
            'name': name,
            'category': category
        })
    
    return components

def render_nested_bar_overview(alignment_matrix: List[Dict[str, Any]]):
    """Render nested horizontal bar chart showing customer needs with value components inside."""
    
    if not alignment_matrix:
        st.info("No alignment data available.")
        return
    
    # Process data to calculate component shares
    processed_data = calculate_component_shares(alignment_matrix)
    
    if not processed_data:
        st.info("No valid alignment data found.")
        return
    
    # Sort by total score (highest first) and limit bar width
    processed_data.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Create the nested bar chart
    fig = go.Figure()
    
    # Track position for each customer need
    y_positions = []
    y_labels = []
    
    for i, data in enumerate(processed_data):
        customer_need = data['customer_need']
        components = data['components']
        
        # Use full customer need text (no truncation)
        y_positions.append(i)
        y_labels.append(customer_need)
        
        # Create nested bars for each component
        bar_length = data['total_score']  # This is the alignment score (e.g., 90%)
        current_x = 0
        
        for comp in components:
            # Calculate actual segment width based on percentage share of the bar length
            segment_width = (comp['percentage_share'] / 100) * bar_length
            category = comp['category']
            color = get_category_color(category)
            
            # Find the original alignment data for this customer need
            original_data = None
            for item in alignment_matrix:
                if (item.get('prospect_need', '') or item.get('customer_need', '')) == customer_need:
                    original_data = item
                    break
            
            # Enhanced tooltip with rationale and conversation starter
            rationale = original_data.get('rationale', 'No rationale provided.') if original_data else 'No rationale provided.'
            conversation = original_data.get('conversation_starter', 'No conversation starter provided.') if original_data else 'No conversation starter provided.'
            
            # Truncate long text for tooltip
            if len(rationale) > 150:
                rationale = rationale[:147] + "..."
            if len(conversation) > 100:
                conversation = conversation[:97] + "..."
            
            # Add bar segment for this component
            fig.add_trace(go.Bar(
                y=[i],
                x=[segment_width],
                name=comp['name'],
                orientation='h',
                marker_color=color,
                marker_line_width=1,
                marker_line_color='white',
                hovertemplate=f"<b>{comp['name']}</b><br>" +
                            f"<b>Category:</b> {category}<br>" +
                            f"<b>Share:</b> {comp['percentage_share']:.1f}%<br>" +
                            "<extra></extra>",
                showlegend=False,
                base=current_x
            ))
            
            current_x += segment_width
    
    # Update layout with animation and interactions
    fig.update_layout(
        title="",
        xaxis_title="Alignment Score (%)",
        yaxis_title="Customer Needs",
        barmode='stack',
        height=max(400, len(processed_data) * 40),  # Compressed height for thinner bars
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            range=[0, 100],
            tickformat='.0f',
            ticktext=['0%', '25%', '50%', '75%', '100%'],
            tickvals=[0, 25, 50, 75, 100],
            fixedrange=True  # Disable zoom on x-axis
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=y_positions,
            ticktext=y_labels,
            tickangle=0,
            tickfont=dict(size=14),  # Bigger font for customer needs
            side='left',
            fixedrange=True  # Disable zoom on y-axis
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # No animation frames - static chart
    
    # Add grid
    fig.add_hline(y=-0.5, line_dash="dash", line_color="gray", opacity=0.3)
    for i in range(len(y_positions)):
        fig.add_hline(y=i+0.5, line_dash="dash", line_color="gray", opacity=0.3)
    
    # Display the chart with minimal interactions
    st.plotly_chart(
        fig, 
        use_container_width=True,
        config={
            'displayModeBar': False,
            'displaylogo': False,
            'scrollZoom': False,
            'doubleClick': False,
            'showTips': False
        }
    )
    
    # Create legend - only show the 4 main categories we use
    main_categories = ['Technical Value', 'Business Value', 'Strategic Value', 'After Sales Value']
    st.markdown("**📊 Component Categories:**")
    legend_html = ""
    for category in main_categories:
        color = get_category_color(category)
        legend_html += f'<span style="color: {color}; font-weight: bold;">■</span> {category}  '
    
    st.markdown(legend_html, unsafe_allow_html=True)
    
 