import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict, Any


def render_treemap_overview(alignment_matrix: List[Dict[str, Any]]):
    """
    Render a treemap chart showing comprehensive value alignment coverage.
    
    Args:
        alignment_matrix: List of alignment items with match scores and categories
    """
    if not alignment_matrix:
        st.info("No value alignment data available for treemap visualization.")
        return
    
    # Process data for treemap
    treemap_data = process_alignment_data_for_treemap(alignment_matrix)
    
    if not treemap_data:
        st.info("Unable to process alignment data for treemap visualization.")
        return
    
    # Create treemap chart
    fig = create_treemap_chart(treemap_data)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def process_alignment_data_for_treemap(alignment_matrix: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process alignment matrix data into simplified treemap format (category-level only).
    Uses weighted approach: box size = number of matches, labels show average score.
    
    Args:
        alignment_matrix: Raw alignment data
        
    Returns:
        List of processed data for treemap visualization
    """
    treemap_data = []
    
    # Group by value categories
    categories = {}
    
    for item in alignment_matrix:
        # Extract value component and categorize
        value_component = item.get('our_value_component', 'Unknown')
        match_score = item.get('match_score_percent', 0)
        
        # Determine category based on value component keywords
        category = categorize_value_component(value_component)
        

        
        if category not in categories:
            categories[category] = []
        
        categories[category].append(match_score)
    
    # Create simplified treemap data with weighted approach
    for category, scores in categories.items():
        total_score = sum(scores)
        average_score = total_score / len(scores) if scores else 0
        count = len(scores)
        
        treemap_data.append({
            'ids': f"{category}",
            'labels': f"{category}",
            'parents': "Value Alignment",
            'values': count,  # Box size = number of matches (weighted by count)
            'category': category,
            'color': get_category_color(category),
            'average_score': average_score,
            'count': count,
            'total_score': total_score
        })
    
    return treemap_data


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


def create_treemap_chart(treemap_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create simplified Plotly treemap chart (category-level only).
    
    Args:
        treemap_data: Processed data for treemap
        
    Returns:
        Plotly figure object
    """
    # Extract data for plotting
    ids = [item['ids'] for item in treemap_data]
    labels = [f"{item['labels']}<br>({item['average_score']:.0f}% avg, {item['count']} matches)" for item in treemap_data]
    parents = [item['parents'] for item in treemap_data]
    values = [item['values'] for item in treemap_data]  # Box size = count
    colors = [item['color'] for item in treemap_data]
    average_scores = [item['average_score'] for item in treemap_data]
    
    # Create simplified treemap
    fig = go.Figure(go.Treemap(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=3, color='white')
        ),
        textinfo="label",
        textfont=dict(size=14, color='white'),
        hovertemplate="<b>%{label}</b><br>" +
                     "Number of Matches: %{value}<br>" +
                     "Average Score: %{customdata:.1f}%<br>" +
                     "<extra></extra>",
        customdata=average_scores,
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.8)",
            font_size=14,
            font_family="Arial",
            font_color="white"
        )
    ))
    
    # Update layout for better readability
    fig.update_layout(
        title={
            'text': "Value Alignment by Category",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50', 'weight': 'bold'}
        },
        margin=dict(t=60, l=20, r=20, b=20),
        height=350,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig 