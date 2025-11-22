import streamlit as st
import pandas as pd
import plotly.express as px
import re
import colorsys
from app.core.company_context_manager import CompanyContextManager

def normalize_category_key(cat):
    return (cat or '').strip().lower()

def normalize_subcategory_key(cat):
    return (cat or '').strip().title()

def clean_component_label(name):
    # Remove text in parentheses and strip
    return re.sub(r"\s*\(.*?\)", "", name or "").strip()

def get_first_word_only(label):
    """Get only the first word for outer ring display"""
    if not label or label == "(None)":
        return label
    words = label.split()
    return words[0] if words else label

def break_long_company_name(company_name, max_chars_per_line=20):
    """
    Break long company names into multiple lines for better display in sunburst chart center
    """
    if not company_name:
        return ""
    
    # If name is short enough, return as is
    if len(company_name) <= max_chars_per_line:
        return company_name
    
    # Split by words
    words = company_name.split()
    
    # If only one word, try to break it at reasonable points
    if len(words) == 1:
        word = words[0]
        if len(word) <= max_chars_per_line:
            return word
        
        # Try to break long single words at reasonable points
        if len(word) <= max_chars_per_line * 2:
            mid_point = len(word) // 2
            # Find a good breaking point (avoid breaking in the middle of words)
            for i in range(mid_point - 3, mid_point + 4):
                if i > 0 and i < len(word) - 2:
                    return f"{word[:i]}<br>{word[i:]}"
        return word
    
    # Multiple words - break into lines
    lines = []
    current_line = ""
    
    for word in words:
        # If adding this word would exceed the limit, start a new line
        if current_line and len(current_line + " " + word) > max_chars_per_line:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
    
    # Add the last line
    if current_line:
        lines.append(current_line)
    
    # Join with <br> for HTML line breaks
    return "<br>".join(lines)

def prune_zero_branches(labels, parents, values, customer_benefits=None):
    """
    Prune only leaf nodes with value 0, and recursively prune parents that become childless.
    Always preserve the full path from root to nonzero leaves.
    """
    from collections import defaultdict
    # Build node structure
    nodes = []
    label_to_idx = {}
    for i, (l, p, v) in enumerate(zip(labels, parents, values)):
        node = {
            'label': l,
            'parent': p,
            'value': v,
            'children': [],
            'idx': i
        }
        nodes.append(node)
        label_to_idx[l] = i
    # Build children lists
    for node in nodes:
        if node['parent'] != "":
            parent_idx = label_to_idx.get(node['parent'])
            if parent_idx is not None:
                nodes[parent_idx]['children'].append(node['idx'])
    # Recursive prune function
    def prune(idx):
        node = nodes[idx]
        # Prune children first
        kept_children = []
        for cidx in node['children']:
            if prune(cidx):
                kept_children.append(cidx)
        node['children'] = kept_children
        # If leaf and value == 0, prune
        if not node['children'] and node['value'] == 0 and idx != 0:
            return False
        # If not leaf, keep if has any children
        return True
    # Start pruning from root (index 0)
    prune(0)
    # Collect all kept nodes (reachable from root)
    kept = set()
    def collect(idx):
        kept.add(idx)
        for cidx in nodes[idx]['children']:
            collect(cidx)
    collect(0)
    # Rebuild lists
    new_labels, new_parents, new_values = [], [], []
    new_customer_benefits = [] if customer_benefits else None
    old_to_new = {}
    for i, node in enumerate(nodes):
        if i in kept:
            old_to_new[i] = len(new_labels)
            new_labels.append(node['label'])
            new_values.append(node['value'])
            if customer_benefits and new_customer_benefits is not None:
                new_customer_benefits.append(customer_benefits[i])
    for i, node in enumerate(nodes):
        if i in kept:
            if node['parent'] == "":
                new_parents.append("")
            else:
                parent_idx = label_to_idx.get(node['parent'])
                if parent_idx is not None and parent_idx in kept:
                    new_parents.append(nodes[parent_idx]['label'])
                else:
                    new_parents.append("")
    if customer_benefits:
        return new_labels, new_parents, new_values, new_customer_benefits
    else:
        return new_labels, new_parents, new_values

def wrap_label(label, max_len=18):
    words = label.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_len:
            lines.append(current)
            current = word
        else:
            current += (" " if current else "") + word
    if current:
        lines.append(current)
    return "<br>".join(lines)

async def render_company_overview_sunburst(value_components):
    """
    Render a company-wide sunburst chart with four levels:
    Root -> Main Category -> Subcategory -> Component (cleaned label).
    Handles lowercase DB keys robustly and always includes all four main categories.
    Prunes all-zero branches before rendering.
    """
    main_categories = [
        "Technical Value",
        "Business Value",
        "Strategic Value",
        "After Sales Value"
    ]
    main_categories_norm = [normalize_category_key(c) for c in main_categories]
    # Flatten all components from all categories into a single list
    all_components = []
    if isinstance(value_components, dict):
        for cat, comps in value_components.items():
            if isinstance(comps, list):
                all_components.extend([c for c in comps if isinstance(c, dict)])
    elif isinstance(value_components, list):
        # Demo companies may provide a flat list already
        all_components.extend([c for c in value_components if isinstance(c, dict)])
    else:
        all_components = []
    # Build unique subcategories and components per main category
    subcategories = {cat: set() for cat in main_categories}
    components = {}  # (main, subcat) -> set of component labels
    # Track which main categories are present in the DB
    present_main_cats = set()
    for comp in all_components:
        main_cat_lc = normalize_category_key(comp.get("main_category", ""))
        if main_cat_lc not in main_categories_norm:
            continue
        idx = main_categories_norm.index(main_cat_lc)
        cat_label = main_categories[idx]
        present_main_cats.add(cat_label)
        subcat = normalize_subcategory_key(comp.get("category", "")) or "(None)"
        comp_label = clean_component_label(comp.get("name", "") or "(None)")
        subcategories[cat_label].add(subcat)
        components.setdefault((cat_label, subcat), set()).add(comp_label)
    # For any missing main category, add a dummy subcategory/component
    for cat in main_categories:
        if cat not in present_main_cats:
            subcategories[cat].add("(None)")
            components[(cat, "(None)")] = set(["(None)"])
        if not subcategories[cat]:
            subcategories[cat].add("(None)")
        for subcat in subcategories[cat]:
            if (cat, subcat) not in components:
                components[(cat, subcat)] = set(["(None)"])
    # Calculate weights for each (main, subcat, comp)
    weights = {}
    for cat in main_categories:
        for subcat in subcategories[cat]:
            for comp_label in components[(cat, subcat)]:
                weights[(cat, subcat, comp_label)] = 0.0
    for comp in all_components:
        main_cat_lc = normalize_category_key(comp.get("main_category", ""))
        if main_cat_lc not in main_categories_norm:
            continue
        idx = main_categories_norm.index(main_cat_lc)
        cat_label = main_categories[idx]
        subcat = normalize_subcategory_key(comp.get("category", "")) or "(None)"
        comp_label = clean_component_label(comp.get("name", "") or "(None)")
        ai_benefit = comp.get("ai_processed_value", "") or comp.get("value", {}).get("ai_processed_value", "") or ""
        user_input = comp.get("original_value", "") or comp.get("value", {}).get("original_value", "") or ""
        user_rating = comp.get("user_rating", 1)
        # Prefer precomputed percentage from demo data if present
        def _parse_pct(val):
            if val is None:
                return None
            try:
                if isinstance(val, str):
                    val = val.strip().replace('%', '').replace(',', '.')
                return float(val)
            except Exception:
                return None
        pre_pct = (
            _parse_pct(comp.get("calculated_percentage"))
            or _parse_pct(comp.get("calculatedPercentage"))
            or _parse_pct(comp.get("value", {}).get("calculated_percentage"))
            or _parse_pct(comp.get("value", {}).get("calculatedPercentage"))
        )
        try:
            user_rating = int(user_rating)
        except Exception:
            user_rating = 1
        if pre_pct is not None and pre_pct > 0:
            weight = pre_pct
        elif ai_benefit.strip() or user_input.strip():
            weight = (len(ai_benefit.strip()) if ai_benefit.strip() else len(user_input.strip())) * user_rating
        else:
            weight = 0
        weights[(cat_label, subcat, comp_label)] += weight
    # Calculate totals for normalization
    category_totals = {cat: 0.0 for cat in main_categories}
    subcat_totals = {}  # (cat, subcat) -> float
    for (cat, subcat, comp_label), val in weights.items():
        category_totals[cat] += val
        subcat_totals[(cat, subcat)] = subcat_totals.get((cat, subcat), 0.0) + val
    grand_total = sum(category_totals.values())
    # Normalize with minimum segment size
    min_segment_size = 2.0  # Minimum 2% of total for readability
    if grand_total > 0:
        normalized_main = {cat: (val / grand_total) * 100 for cat, val in category_totals.items()}
        normalized_sub = {(cat, subcat): (val / grand_total) * 100 for (cat, subcat), val in subcat_totals.items()}
        normalized_comp = {(cat, subcat, comp_label): (val / grand_total) * 100 for (cat, subcat, comp_label), val in weights.items()}
        
        # Apply minimum segment size to components (outer ring)
        for key in normalized_comp:
            if normalized_comp[key] > 0 and normalized_comp[key] < min_segment_size:
                normalized_comp[key] = min_segment_size
    else:
        normalized_main = {cat: 0.0 for cat in main_categories}
        normalized_sub = {(cat, subcat): 0.0 for cat in main_categories for subcat in subcategories[cat]}
        normalized_comp = {(cat, subcat, comp_label): 0.0 for cat in main_categories for subcat in subcategories[cat] for comp_label in components[(cat, subcat)]}
    # Use company name as root label with line breaking for long names
    company_context = CompanyContextManager()
    company_name = company_context.get_company_name()
    root_label = break_long_company_name(company_name)
    # Build sunburst data: root -> main_category -> subcategory -> component
    labels = [root_label]
    parents = [""]
    values = [0.01]  # Even smaller value to make center circle much smaller
    full_labels = [root_label]  # For hover
    customer_benefits = [""]  # For hover - customer benefits
    # Metadata arrays aligned 1:1 with nodes
    original_values_arr = [""]
    main_cat_arr = [""]
    subcat_arr = [""]
    is_leaf_arr = [False]
    # Add main categories
    for cat in main_categories:
        labels.append(wrap_label(cat))
        parents.append(root_label)
        values.append(normalized_main[cat])
        full_labels.append(cat)
        customer_benefits.append("")  # Main categories don't have customer benefits
        original_values_arr.append("")
        main_cat_arr.append(cat)
        subcat_arr.append("")
        is_leaf_arr.append(False)
    
    # Add subcategories
    for cat in main_categories:
        for subcat in subcategories[cat]:
            labels.append(wrap_label(subcat))
            parents.append(wrap_label(cat))
            values.append(normalized_sub[(cat, subcat)])
            full_labels.append(subcat)
            customer_benefits.append("")  # Subcategories don't have customer benefits
            original_values_arr.append("")
            main_cat_arr.append(cat)
            subcat_arr.append(subcat)
            is_leaf_arr.append(False)
    # Add components
    for cat in main_categories:
        for subcat in subcategories[cat]:
            comp_list_for_labels = list(components[(cat, subcat)])
            for comp_idx, comp_label in enumerate(comp_list_for_labels):
                # Use only the first word of the full component label for outer ring
                display_label = get_first_word_only(comp_label)
                labels.append(wrap_label(display_label))
                parents.append(wrap_label(subcat))
                values.append(normalized_comp[(cat, subcat, comp_label)])
                full_labels.append(comp_label)  # Keep full label for hover
                
                # Find customer benefit and original value for this component
                customer_benefit = ""
                original_value = ""
                for comp in all_components:
                    main_cat_lc = normalize_category_key(comp.get("main_category", ""))
                    if main_cat_lc not in main_categories_norm:
                        continue
                    idx = main_categories_norm.index(main_cat_lc)
                    cat_label = main_categories[idx]
                    subcat_comp = normalize_subcategory_key(comp.get("category", "")) or "(None)"
                    comp_label_comp = clean_component_label(comp.get("name", "") or "(None)")
                    
                    if (cat_label == cat and subcat_comp == subcat and comp_label_comp == comp_label):
                        customer_benefit = comp.get("ai_processed_value", "") or comp.get("value", {}).get("ai_processed_value", "") or ""
                        original_value = comp.get("original_value", "") or comp.get("value", {}).get("original_value", "") or ""
                        # Add manual line breaks every 50 characters for better readability
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
                        break
                
                customer_benefits.append(customer_benefit)
                original_values_arr.append(original_value)
                main_cat_arr.append(cat)
                subcat_arr.append(subcat)
                is_leaf_arr.append(True)
    
    # Ensure all arrays have the same length (strict)
    min_length = min(len(labels), len(parents), len(values), len(full_labels), len(customer_benefits), len(original_values_arr), len(main_cat_arr), len(subcat_arr), len(is_leaf_arr))
    if not (len(labels) == len(parents) == len(values) == len(full_labels) == len(customer_benefits) == len(original_values_arr) == len(main_cat_arr) == len(subcat_arr) == len(is_leaf_arr)):
        labels = labels[:min_length]
        parents = parents[:min_length]
        values = values[:min_length]
        full_labels = full_labels[:min_length]
        customer_benefits = customer_benefits[:min_length]
        original_values_arr = original_values_arr[:min_length]
        main_cat_arr = main_cat_arr[:min_length]
        subcat_arr = subcat_arr[:min_length]
        is_leaf_arr = is_leaf_arr[:min_length]
    # --- DEBUG OUTPUT ---
    # st.markdown("<details><summary>Chart Data Debug</summary>", unsafe_allow_html=True)
    # st.write({
    #     "labels": labels,
    #     "parents": parents,
    #     "values": values
    # })
    # st.markdown("</details>", unsafe_allow_html=True)
    # Remove nodes with value very close to zero (e.g., < 1e-6), but keep root
    filtered = [
        (l, p, v, f, c, ov, mc, sc, leaf)
        for l, p, v, f, c, ov, mc, sc, leaf in zip(labels, parents, values, full_labels, customer_benefits, original_values_arr, main_cat_arr, subcat_arr, is_leaf_arr)
        if abs(v) > 1e-6 or p == ""
    ]
    if filtered:
        labels, parents, values, full_labels, customer_benefits, original_values_arr, main_cat_arr, subcat_arr, is_leaf_arr = zip(*filtered)
    else:
        labels, parents, values, full_labels, customer_benefits, original_values_arr, main_cat_arr, subcat_arr, is_leaf_arr = ([], [], [], [], [], [], [], [], [])
    # If no data remains after filtering, show a warning and return
    if not labels or not parents or not values or not full_labels:
        st.warning("No data to display in the sunburst chart.")
        return
    if all(v == 0 for v in values[1:]):
        st.warning("All chart values are zero. Please check your value components and ratings.")
        return
    # Always create the DataFrame using the dict constructor to guarantee columns exist
    df = pd.DataFrame({
        "labels": labels,
        "parents": parents,
        "values": values,
        "full_labels": full_labels,
        "customer_benefits": customer_benefits,
        "original_values": original_values_arr,
        "main_categories": main_cat_arr,
        "subcategories": subcat_arr,
        "is_leaf": is_leaf_arr,
    })
    # Precompute uppercase full labels for hover emphasis
    try:
        df["full_labels_upper"] = df["full_labels"].astype(str).str.upper()
    except Exception:
        df["full_labels_upper"] = df["full_labels"]
    if df.empty or "full_labels" not in df.columns or df["full_labels"].empty:
        st.warning("No data to display in the sunburst chart.")
        return
    # All chart code below this point is now protected
    # Assign highly distinct base colors to each main category
    base_colors = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple (if you ever add a 5th main category)
    ]
    color_map = {cat: base_colors[i % len(base_colors)] for i, cat in enumerate(main_categories)}
    import colorsys
    def adjust_lightness(color, amount=1.0, saturation=1.0):
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        l = max(0, min(1, l * amount))
        s = max(0, min(1, s * saturation))
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))

    def generate_analogous_colors(base_color, n, lightness_range=(0.85, 1.15), hue_shift=18):
        """
        Generate n visually distinct colors analogous to the base_color by varying hue and lightness.
        base_color: hex string
        n: number of colors
        lightness_range: tuple (min, max) multiplier for lightness
        hue_shift: max degrees to shift hue left/right
        Returns: list of hex colors
        """
        base_color = base_color.lstrip('#')
        r, g, b = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        colors = []
        for i in range(n):
            # Spread hue shifts evenly around the base hue
            if n == 1:
                hue = h
            else:
                hue = (h + ((i - (n-1)/2) * (hue_shift/360) / max(n-1,1))) % 1.0
            # Spread lightness evenly in the given range
            if n == 1:
                light = l
            else:
                light = min(1.0, max(0.0, l * (lightness_range[0] + (i * (lightness_range[1] - lightness_range[0]) / max(n-1,1)))))
            r2, g2, b2 = colorsys.hls_to_rgb(hue, light, s)
            colors.append('#%02x%02x%02x' % (int(r2*255), int(g2*255), int(b2*255)))
        return colors

    for i, cat in enumerate(main_categories):
        base = base_colors[i % len(base_colors)]
        subcat_list = list(subcategories[cat])
        n_subcats = len(subcat_list)
        # Generate analogous colors for subcategories
        subcat_colors = generate_analogous_colors(base, n_subcats, lightness_range=(0.85, 1.15), hue_shift=18)
        for j, subcat in enumerate(subcat_list):
            wrapped_subcat = wrap_label(subcat)
            color_map[wrapped_subcat] = subcat_colors[j]
            comp_list = list(components[(cat, subcat)])
            n_comps = len(comp_list)
            # Generate analogous colors for components, centered around the subcategory color
            comp_colors = generate_analogous_colors(subcat_colors[j], n_comps, lightness_range=(0.90, 1.10), hue_shift=10)
            for k, comp_label in enumerate(comp_list):
                # Map colors for both full label and first word only (for conditional display)
                wrapped_comp_label = wrap_label(comp_label)
                wrapped_first_word = wrap_label(get_first_word_only(comp_label))
                color_map[wrapped_comp_label] = comp_colors[k]
                color_map[wrapped_first_word] = comp_colors[k]  # Same color for first word version
                # Also map the first-word display label used in the chart
                generic_label = wrap_label(get_first_word_only(comp_label))
                color_map[generic_label] = comp_colors[k]
    # Set root node (company name) color to white
    color_map[root_label] = '#ffffff'
    # --- Display chart without legend for better space utilization ---
    with st.container():
        # df already constructed above
        custom_data = ["full_labels_upper", "customer_benefits", "original_values", "main_categories", "subcategories"]
        fig = px.sunburst(
            df,
            names="labels",
            parents="parents",
            values="values",
            color="labels",
            color_discrete_map=color_map,
            height=1100,
            width=1100,
            maxdepth=4,
            custom_data=custom_data,
            branchvalues="remainder" # This makes outer segments longer
         
        )
        fig.update_traces(
            textinfo= 'label',  # Only show label, no percent
            insidetextorientation = 'radial',
            insidetextfont=dict(size=28, color='black'),  # Bigger font for center
            outsidetextfont=dict(size=20, color='#333333'),  # Default outer font; we'll override leaves per-point below
            # Enable HTML support for line breaks in labels
            texttemplate='%{label}',
            # Add thicker white border to center circle for better visual hierarchy
            marker=dict(
                line=dict(
                    width=2,  # Slightly thinner border for smaller center
                    color='white'
                )
            ),
            # Configure hover behavior
            hoverlabel=dict(
                bgcolor="#FEF3C7",  # soft amber background
                bordercolor="#F59E0B",  # amber border
                font_size=12,
                font_family="Arial"
            )
        )
        # Build per-point hovertemplate (only for leaf nodes)
        hover_templates = []
        for is_leaf in df["is_leaf"].tolist():
            if is_leaf:
                hover_templates.append(
                    '<span style="font-weight:800;color:#000000">%{customdata[0]}</span><br><br>' +
                    '<span style="font-weight:700;color:#6b7280">Customer Benefit</span><br>' +
                    '<span style="width:220px;font-size:1.05em;white-space:normal;display:inline-block;word-break:break-word;overflow-wrap:break-word;color:#374151;">%{customdata[1]}</span>' +
                    '<extra></extra>'
                )
            else:
                hover_templates.append('<extra></extra>')
        try:
            if hasattr(fig, 'data') and fig.data and isinstance(fig.data, (list, tuple)) and len(fig.data) > 0:
                fig.data[0].hovertemplate = hover_templates  # type: ignore[attr-defined]
        except Exception:
            pass

        # Per-point text size: smaller for leaf nodes only
        try:
            sizes = [14 if leaf else 20 for leaf in df["is_leaf"].tolist()]
            if hasattr(fig, 'data') and fig.data and isinstance(fig.data, (list, tuple)) and len(fig.data) > 0:
                if hasattr(fig.data[0], "textfont") and isinstance(fig.data[0].textfont, dict):
                    fig.data[0].textfont.update({"size": sizes})  # type: ignore[attr-defined]
                else:
                    fig.update_traces(textfont=dict(size=sizes))
            else:
                fig.update_traces(textfont=dict(size=sizes))
        except Exception:
            pass

        # Cursor styling: only show pointer over leaf slices if Plotly assigns 'leaf' class
        st.markdown(
            """
            <style>
            .js-plotly-plot .plotly .sunburstlayer .sunburstslice { cursor: default !important; }
            .js-plotly-plot .plotly .sunburstlayer .sunburstslice.leaf { cursor: pointer !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        fig.update_layout(
            title="",
            title_font_size=32,
            title_x=0.5,
            dragmode='zoom',
            hovermode='closest',
            margin=dict(t=10, l=20, r=20, b=20),
            uniformtext_minsize=13,
            uniformtext_mode='show',
            # No visual button - rely on hover tooltip and navigation banner
            annotations=[],
            # Make the center ring physically smaller
            sunburstcolorway=None,
            # Adjust the inner radius to make center circle smaller
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            # Enable HTML support for labels
            font=dict(family="Arial, sans-serif")
        )
        
        # Render chart (original behavior without interactive click wiring)
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": False, 
            "scrollZoom": True,
            "staticPlot": False,
            "editable": False,
            "showTips": True,
            "showLink": False,
            "linkText": "",
            "modeBarButtonsToRemove": ["toImage", "toggleSpikelines", "resetScale2d"],
            "modeBarButtonsToAdd": [],
            "displaylogo": False,
            "responsive": False,
            "doubleClick": "reset+autosize",
            "showAxisDragHandles": True,
            "showAxisRangeEntryBoxes": True
        })
    
    # Add description below chart
    st.markdown("<div style='color: #888; font-size: 0.9em; margin-top: 0.5em;'>This chart shows the relative importance of each main value category, subcategory, and component for the company (sum = 100%).</div>", unsafe_allow_html=True) 