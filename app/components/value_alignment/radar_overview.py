import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Any
import re

def categorize_value_component(component_name: str) -> str:
    """Categorize value component based on keywords."""
    component_lower = component_name.lower()
    
    # Technical Value keywords
    technical_keywords = ['technology', 'technical', 'innovation', 'product', 'development', 'engineering', 'automation', 'performance', 'quality', 'efficiency', 'sustainability', 'mechanical', 'chemical', 'thermal', 'device', 'integration', 'technical value']
    if any(keyword in component_lower for keyword in technical_keywords):
        return 'Technical Value'
    
    # Strategic Value keywords
    strategic_keywords = ['strategy', 'strategic', 'leadership', 'market', 'growth', 'expansion', 'competitive', 'positioning', 'vision', 'mission', 'advantage', 'differentiation', 'strategic value']
    if any(keyword in component_lower for keyword in strategic_keywords):
        return 'Strategic Value'
    
    # Business Value keywords
    business_keywords = ['business', 'financial', 'profit', 'revenue', 'cost', 'efficiency', 'operations', 'management', 'customer', 'satisfaction', 'processing', 'cost', 'business value']
    if any(keyword in component_lower for keyword in business_keywords):
        return 'Business Value'
    
    # After Sales Value keywords
    after_keywords = ['after', 'support', 'service', 'maintenance', 'training', 'warranty', 'repair', 'customer care', 'care', 'after sales', 'after-sales', 'after sales value']
    if any(keyword in component_lower for keyword in after_keywords):
        return 'After Sales Value'
    
    return 'Other'

def get_category_color(category: str) -> str:
    """Get color for each category."""
    colors = {
        'Technical Value': '#1f77b4',      # Blue
        'Strategic Value': '#d62728',      # Red
        'Business Value': '#9467bd',       # Purple
        'After Sales Value': '#ff7f0e',    # Orange
        'Other': '#7f7f7f'                 # Gray
    }
    return colors.get(category, '#7f7f7f')

def process_radar_data(alignment_matrix: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process alignment matrix data for radar chart visualization."""
    # Force refresh - debug code removed
    
    # Initialize category data
    categories = {
        'Technical Value': [],
        'Strategic Value': [],
        'Business Value': [],
        'After Sales Value': []
    }
    
    # Collect scores for each category
    for item in alignment_matrix:
        value_component = item.get('our_value_component', '')
        match_score = item.get('match_score_percent', 0)
        
        if not value_component or match_score == 0:
            continue
        
        # Extract individual components from combined strings
        components = extract_value_components(value_component)
        
        for comp in components:
            category = comp['category']
            if category in categories:
                # Convert percentage to 0-5 scale for radar chart
                score = (match_score / 100) * 5
                categories[category].append(score)
    
    # Calculate average scores for each category
    radar_data = {}
    for category, scores in categories.items():
        if scores:
            radar_data[category] = np.mean(scores)
        else:
            radar_data[category] = 0
    
    return radar_data

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
            category_name = category_match.group(1).title()
            name = category_match.group(2).strip()
            
            # Map to correct category names
            if category_name == 'Technical':
                category = 'Technical Value'
            elif category_name == 'Business':
                category = 'Business Value'
            elif category_name == 'Strategic':
                category = 'Strategic Value'
            elif category_name == 'After Sales':
                category = 'After Sales Value'
            else:
                category = categorize_value_component(part)
        else:
            # No category prefix, categorize based on content
            category = categorize_value_component(part)
            name = part
        
        components.append({
            'name': name,
            'category': category
        })
    
    return components

def create_customer_needs_profile(alignment_matrix: List[Dict[str, Any]]) -> Dict[str, float]:
    """Create a customer-specific needs profile based on their actual alignment data."""
    
    # Initialize category priorities
    category_priorities = {
        'Technical Value': [],
        'Strategic Value': [],
        'Business Value': [],
        'After Sales Value': []
    }
    
    # Analyze customer needs to determine their priorities
    for item in alignment_matrix:
        customer_need = item.get('prospect_need', '') or item.get('customer_need', '')
        match_score = item.get('match_score_percent', 0)
        
        if not customer_need or match_score == 0:
            continue
        
        # Categorize the customer need itself to understand their priorities
        need_category = categorize_customer_need(customer_need)
        
        if need_category in category_priorities:
            # Convert percentage to 0-5 scale
            priority_score = (match_score / 100) * 5
            category_priorities[need_category].append(priority_score)
    
    # Calculate average priorities for each category
    customer_profile = {}
    for category, scores in category_priorities.items():
        if scores:
            customer_profile[category] = np.mean(scores)
        else:
            # If no direct matches, use a neutral score
            customer_profile[category] = 2.5
    
    return customer_profile

def categorize_customer_need(customer_need: str) -> str:
    """Categorize customer need based on keywords to understand their priorities."""
    need_lower = customer_need.lower()
    
    # Technical Value priorities
    technical_keywords = ['technology', 'technical', 'innovation', 'product', 'development', 'engineering', 'automation', 'performance', 'quality', 'efficiency', 'sustainability', 'mechanical', 'chemical', 'thermal', 'device', 'integration', 'leadership', 'excellence']
    if any(keyword in need_lower for keyword in technical_keywords):
        return 'Technical Value'
    
    # Strategic Value priorities
    strategic_keywords = ['strategy', 'strategic', 'leadership', 'market', 'growth', 'expansion', 'competitive', 'positioning', 'vision', 'mission', 'advantage', 'differentiation', 'global', 'reach', 'competitive advantage']
    if any(keyword in need_lower for keyword in strategic_keywords):
        return 'Strategic Value'
    
    # Business Value priorities
    business_keywords = ['business', 'financial', 'profit', 'revenue', 'cost', 'efficiency', 'operations', 'management', 'customer', 'satisfaction', 'processing', 'cost', 'efficiency', 'scalability', 'resilience', 'supply chain']
    if any(keyword in need_lower for keyword in business_keywords):
        return 'Business Value'
    
    # After Sales Value priorities
    after_keywords = ['after', 'support', 'service', 'maintenance', 'training', 'warranty', 'repair', 'customer care', 'care', 'after sales', 'after-sales', 'satisfaction', 'loyalty']
    if any(keyword in need_lower for keyword in after_keywords):
        return 'After Sales Value'
    
    # Default based on common patterns
    if any(word in need_lower for word in ['customizable', 'tailor-made', 'solutions']):
        return 'Technical Value'
    elif any(word in need_lower for word in ['sustainability', 'responsible', 'eco-friendly']):
        return 'Business Value'
    else:
        return 'Strategic Value'  # Default to strategic for general business needs

def render_radar_overview(alignment_matrix: List[Dict[str, Any]]):
    """Render radar chart showing value component categories and profiles."""
    
    if not alignment_matrix:
        st.info("No alignment data available.")
        return
    
    # Process data for radar chart
    company_profile = process_radar_data(alignment_matrix)
    customer_profile = create_customer_needs_profile(alignment_matrix)
    
    if not company_profile:
        st.info("No valid alignment data found.")
        return
    
    # Prepare data for plotting
    categories = list(company_profile.keys())
    company_scores = list(company_profile.values())
    customer_scores = [customer_profile.get(cat, 0) for cat in categories]
    
    # Create radar chart
    fig = go.Figure()
    
    # Add company profile (blue)
    fig.add_trace(go.Scatterpolar(
        r=company_scores,
        theta=categories,
        fill='toself',
        name='Our Value Profile',
        line_color='#1f77b4',
        fillcolor='rgba(31, 119, 180, 0.3)',
        hovertemplate='<b>%{theta}</b><br>' +
                     'Score: %{r:.2f}/5<br>' +
                     'Profile: Our Value<br>' +
                     '<extra></extra>'
    ))
    
    # Add customer needs profile (red)
    fig.add_trace(go.Scatterpolar(
        r=customer_scores,
        theta=categories,
        fill='toself',
        name='Customer Needs Profile',
        line_color='#d62728',
        fillcolor='rgba(214, 39, 40, 0.3)',
        hovertemplate='<b>%{theta}</b><br>' +
                     'Score: %{r:.2f}/5<br>' +
                     'Profile: Customer Needs<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                ticktext=['0', '1', '2', '3', '4', '5'],
                tickvals=[0, 1, 2, 3, 4, 5],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#333333')
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        title={
            'text': 'Customer-Specific Value Alignment Profile',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        height=500,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    # Display the chart with enhanced interactions
    st.plotly_chart(
        fig, 
        use_container_width=True,
        config={
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['pan2d', 'select2d', 'resetScale2d'],
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'value_alignment_radar',
                'height': None,
                'width': None,
                'scale': 2
            }
        }
    )
    

    
 