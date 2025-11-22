import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict, Any


def render_horizontal_bar_overview(alignment_matrix: List[Dict[str, Any]]):
    """
    Render a horizontal bar chart showing value alignment matches.
    
    Args:
        alignment_matrix: List of alignment items with match scores and categories
    """
    if not alignment_matrix:
        st.info("No value alignment data available for bar chart visualization.")
        return
    
    # Process data for horizontal bar chart
    bar_data = process_alignment_data_for_bars(alignment_matrix)
    
    if not bar_data:
        st.info("Unable to process alignment data for bar chart visualization.")
        return
    
    # Create horizontal bar chart
    fig = create_horizontal_bar_chart(bar_data)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def process_alignment_data_for_bars(alignment_matrix: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process alignment matrix data into horizontal bar chart format.
    
    Args:
        alignment_matrix: Raw alignment data
        
    Returns:
        Dictionary with processed data for bar chart
    """
    # Extract customer needs and value components
    customer_needs = []
    value_components = []
    match_scores = []
    categories = []
    
    for item in alignment_matrix:
        customer_need = item.get('prospect_need', 'Unknown Need')
        value_component = item.get('our_value_component', 'Unknown Component')
        match_score = item.get('match_score_percent', 0)
        
        # Truncate long text for better display
        if len(customer_need) > 50:
            customer_need = customer_need[:47] + "..."
        if len(value_component) > 50:
            value_component = value_component[:47] + "..."
        
        customer_needs.append(customer_need)
        value_components.append(value_component)
        match_scores.append(match_score)
        
        # Categorize for color coding
        category = categorize_value_component(value_component)
        categories.append(category)
    
    return {
        'customer_needs': customer_needs,
        'value_components': value_components,
        'match_scores': match_scores,
        'categories': categories
    }


def categorize_value_component(value_component: str) -> str:
    """
    Categorize value component into technical, strategic, or business value.
    
    Args:
        value_component: The value component string
        
    Returns:
        Category string
    """
    value_component_lower = value_component.lower()
    
    # Technical value keywords
    technical_keywords = [
        'technical', 'technology', 'innovation', 'efficiency', 'performance',
        'automation', 'optimization', 'integration', 'system', 'platform',
        'infrastructure', 'scalability', 'reliability', 'quality', 'process'
    ]
    
    # Strategic value keywords
    strategic_keywords = [
        'strategic', 'strategy', 'competitive', 'market', 'positioning',
        'differentiation', 'advantage', 'leadership', 'growth', 'expansion',
        'partnership', 'alliance', 'acquisition', 'transformation', 'vision'
    ]
    
    # Business value keywords
    business_keywords = [
        'business', 'financial', 'cost', 'revenue', 'profit', 'roi',
        'savings', 'investment', 'budget', 'expense', 'efficiency',
        'productivity', 'operations', 'management', 'compliance', 'risk'
    ]
    
    # Check for matches
    for keyword in technical_keywords:
        if keyword in value_component_lower:
            return "Technical Value"
    
    for keyword in strategic_keywords:
        if keyword in value_component_lower:
            return "Strategic Value"
    
    for keyword in business_keywords:
        if keyword in value_component_lower:
            return "Business Value"
    
    # Default categorization based on common patterns
    if any(word in value_component_lower for word in ['solution', 'service', 'support']):
        return "Technical Value"
    elif any(word in value_component_lower for word in ['consulting', 'advisory', 'planning']):
        return "Strategic Value"
    else:
        return "Business Value"


def get_category_color(category: str) -> str:
    """
    Get color for value category.
    
    Args:
        category: Value category name
        
    Returns:
        Hex color string
    """
    color_map = {
        "Technical Value": "#FF6B6B",  # Red
        "Strategic Value": "#9B59B6",  # Purple
        "Business Value": "#F39C12"    # Orange
    }
    return color_map.get(category, "#95A5A6")  # Default gray


def create_horizontal_bar_chart(bar_data: Dict[str, Any]) -> go.Figure:
    """
    Create horizontal bar chart showing customer needs vs value components.
    
    Args:
        bar_data: Processed data for bar chart
        
    Returns:
        Plotly figure object
    """
    customer_needs = bar_data['customer_needs']
    value_components = bar_data['value_components']
    match_scores = bar_data['match_scores']
    categories = bar_data['categories']
    
    # Create colors for each bar based on category
    colors = [get_category_color(cat) for cat in categories]
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Add bars for customer needs (left side)
    fig.add_trace(go.Bar(
        y=customer_needs,
        x=[-score for score in match_scores],  # Negative values for left side
        orientation='h',
        name='Customer Needs',
        marker_color='#3498DB',  # Blue for customer needs
        text=[f"{score}%" for score in match_scores],
        textposition='auto',
        hovertemplate="<b>Customer Need:</b> %{y}<br>" +
                     "<b>Match Score:</b> %{text}<br>" +
                     "<extra></extra>"
    ))
    
    # Add bars for value components (right side)
    fig.add_trace(go.Bar(
        y=value_components,
        x=match_scores,  # Positive values for right side
        orientation='h',
        name='Value Components',
        marker_color=colors,
        text=[f"{score}%" for score in match_scores],
        textposition='auto',
        hovertemplate="<b>Value Component:</b> %{y}<br>" +
                     "<b>Match Score:</b> %{text}<br>" +
                     "<b>Category:</b> %{customdata}<br>" +
                     "<extra></extra>",
        customdata=categories
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Value Alignment Matches",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50', 'weight': 'bold'}
        },
        xaxis=dict(
            title="Match Score (%)",
            range=[-100, 100],
            tickvals=[-100, -75, -50, -25, 0, 25, 50, 75, 100],
            ticktext=['100%', '75%', '50%', '25%', '0%', '25%', '50%', '75%', '100%']
        ),
        yaxis=dict(
            title="",
            showticklabels=False  # Hide y-axis labels for cleaner look
        ),
        barmode='overlay',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, l=20, r=20, b=20),
        height=max(400, len(customer_needs) * 40),  # Dynamic height based on number of items
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add vertical line at x=0
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig 