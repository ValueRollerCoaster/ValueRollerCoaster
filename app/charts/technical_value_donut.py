import plotly.graph_objects as go
import pandas as pd
from app.charts.value_donut_utils import calculate_normalized_percentages
import plotly.express as px
from colorsys import rgb_to_hls, hls_to_rgb

def lighten_color(hex_color, amount=0.5):
    """Lighten the given hex color by the given amount (0=original, 1=white)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    h, l, s = rgb_to_hls(r/255, g/255, b/255)
    l = min(1, l + (1 - l) * amount)
    r, g, b = hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

def technical_value_donut_chart(all_components):
    """
    Create a normalized donut chart for all Technical Value components (across all subcategories).
    Args:
        all_components: dict or list of all value components (as returned by get_all_value_components)
    Returns:
        Plotly Figure object
    """
    if isinstance(all_components, dict):
        tech_components = all_components.get("Technical Value", [])
    elif isinstance(all_components, list):
        tech_components = [c for c in all_components if c.get("main_category") == "Technical Value"]
    else:
        tech_components = []

    # Do NOT filter out empty fields; include all for the chart
    donut_data = calculate_normalized_percentages(tech_components)

    # Set percentage to 0 and label as '(cleared)' for fields with no data
    for d in donut_data:
        if not (d.get("customer_benefit", "").strip()):
            d["calculated_percentage"] = 0.0
            d["customer_benefit"] = "(cleared)"
            d["name"] = d["name"] + " (cleared)"

    if donut_data:
        df = pd.DataFrame(donut_data)
        fig = go.Figure(go.Pie(
            labels=df["name"] + " (" + df["main_category"] + ")",
            values=df["calculated_percentage"],
            hole=0.5,
            marker=dict(colors=[
                "#4CAF50" if cat=="Quality" else
                "#2196F3" if cat=="Performance" else
                "#FFC107" if cat=="Innovation" else
                "#9C27B0" if cat=="Sustainability" else
                "#607D8B" for cat in df["main_category"]
            ]),
            hovertemplate='<b>%{label}</b><br>Value: %{value:.2f}%<br>Benefit: %{customdata}',
            customdata=df["customer_benefit"]
        ))
        fig.update_layout(
            height=900,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                font=dict(size=12),
                itemwidth=50
            )
        )
        return fig
    else:
        fig = go.Figure(go.Pie(
            labels=["No data"],
            values=[100],
            hole=0.5,
            marker=dict(colors=["#BDBDBD"]),
            textinfo='label+percent',
            hoverinfo='label'
        ))
        fig.update_layout(
            height=400,
            showlegend=False,
            annotations=[dict(text="No data", x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        return fig

def technical_value_sunburst_chart(all_components, height=600, title_font_size=28):
    """
    Create a sunburst chart for Technical Value components, grouped by subcategory.
    Inner ring: subcategory (e.g., Quality, Performance, etc.)
    Outer ring: component (e.g., Testing and Validation)
    Hover shows customer benefit.
    height: chart height in px
    title_font_size: font size for the chart title
    """
    if isinstance(all_components, dict):
        # Use case-insensitive key lookup
        tech_components = all_components.get("Technical Value", []) or all_components.get("technical value", [])
        if not tech_components:
            # Try to find the key in a case-insensitive way
            for k in all_components:
                if k.lower() == "technical value":
                    tech_components = all_components[k]
                    break
    elif isinstance(all_components, list):
        tech_components = [c for c in all_components if (c.get("main_category") or "").lower() == "technical value"]
    else:
        tech_components = []

    donut_data = calculate_normalized_percentages(tech_components)
    for d in donut_data:
        if not (d.get("customer_benefit", "").strip()):
            d["calculated_percentage"] = 0.0
            d["customer_benefit"] = "(cleared)"
            d["name"] = d["name"] + " (cleared)"

    subcategories = list({d["category"] for d in donut_data})
    labels = []
    parents = []
    values = []
    customdata = []
    # Assign a base color to each subcategory
    base_colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set2 + px.colors.qualitative.Set3
    subcat_color_map = {subcat: base_colors[i % len(base_colors)] for i, subcat in enumerate(subcategories)}
    colors = []
    # For each subcategory, assign tints to its components
    for subcat_idx, subcat in enumerate(subcategories):
        subcat_total = sum(d["calculated_percentage"] for d in donut_data if d["category"] == subcat)
        labels.append(subcat)
        parents.append("")
        values.append(subcat_total)
        customdata.append("")
        colors.append(subcat_color_map[subcat])
        # Get all components for this subcategory
        subcat_components = [d for d in donut_data if d["category"] == subcat]
        n = len(subcat_components)
        for comp_idx, d in enumerate(subcat_components):
            labels.append(d["name"])
            parents.append(subcat)
            values.append(d["calculated_percentage"])
            
            # Process customer benefit to add line breaks
            customer_benefit = d["customer_benefit"]
            if customer_benefit:
                words = customer_benefit.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) > 50:
                        if current_line:
                            lines.append(current_line)
                            current_line = word
                        else:
                            lines.append(word)
                    else:
                        current_line += (" " + word) if current_line else word
                if current_line:
                    lines.append(current_line)
                customer_benefit = "<br>".join(lines)
            
            customdata.append(customer_benefit)
            # Generate a lighter tint for each component
            tint_amount = 0.3 + 0.5 * (comp_idx / max(1, n-1)) if n > 1 else 0.5
            colors.append(lighten_color(subcat_color_map[subcat], amount=tint_amount))
    if labels:
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            hovertemplate='<b>%{label}</b><br>' +
                          '<span style="width:180px;font-size:1.1em;white-space:normal;display:inline-block;word-break:break-word;overflow-wrap:break-word;">' +
                          'Value: %{value:.2f}%<br><br>' +
                          '<span style="color:#666;font-size:1.0em;line-height:1.2;word-break:break-word;overflow-wrap:break-word;">%{customdata}</span>' +
                          '</span><extra></extra>',
            customdata=customdata,
            insidetextfont=dict(size=18),
            outsidetextfont=dict(size=16)
        ))
        fig.update_layout(
            height=height,
            margin=dict(t=40, l=0, r=0, b=0)
        )
        return fig
    else:
        fig = go.Figure(go.Sunburst(
            labels=["No data"],
            parents=[""],
            values=[100],
            marker=dict(colors=["#BDBDBD"]),
            insidetextfont=dict(size=18),
            outsidetextfont=dict(size=16)
        ))
        fig.update_layout(
            height=height,
            margin=dict(t=40, l=0, r=0, b=0)
        )
        return fig 