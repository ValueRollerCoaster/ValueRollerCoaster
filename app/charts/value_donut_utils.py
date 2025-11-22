def calculate_normalized_percentages(components):
    """
    Given a list of value components, calculate normalized percentages for donut chart display.
    Each component's weight is the length of its ai_processed_value (or 1 if empty), multiplied by user_rating (default 1).
    Returns a list of dicts with calculated_percentage summing to 100%.
    """
    donut_data = []
    weights = []
    for comp in components:
        ai_benefit = comp.get("ai_processed_value", "") or comp.get("value", {}).get("ai_processed_value", "") or ""
        user_rating = comp.get("user_rating", 1)
        try:
            user_rating = int(user_rating)
        except Exception:
            user_rating = 1
        weight = (len(ai_benefit.strip()) if ai_benefit.strip() else 1) * user_rating
        weights.append(weight)
        donut_data.append({
            "main_category": comp.get("category", ""),
            "category": comp.get("category", ""),
            "name": comp.get("name", ""),
            "customer_benefit": ai_benefit,
            "weight": weight
        })
    total_weight = sum(weights)
    n = len(donut_data)
    if n == 0:
        return []
    if total_weight == 0:
        # fallback: equal distribution
        for d in donut_data:
            d["calculated_percentage"] = 100.0 / n
    else:
        for d in donut_data:
            d["calculated_percentage"] = d["weight"] / total_weight * 100
    # --- Normalization step ---
    total_percentage = sum(d["calculated_percentage"] for d in donut_data)
    if abs(total_percentage - 100.0) > 1e-6:
        for d in donut_data:
            d["calculated_percentage"] = d["calculated_percentage"] / total_percentage * 100.0
    # After calculating percentages, log all names and their calculated_percentage
    import logging
    for d in donut_data:
        logging.warning(f"[value_donut_utils.py] {d.get('name','')} calculated_percentage: {d.get('calculated_percentage')}")
    return donut_data 