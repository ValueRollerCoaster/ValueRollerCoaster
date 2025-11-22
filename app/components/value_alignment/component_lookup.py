"""
Shared utility for looking up value components in the database.
This ensures consistent categorization across all visualizations.
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def find_component_in_db(component_name: str, all_components: dict) -> Optional[Dict[str, Any]]:
    """
    Find a value component in the database by matching the name field.
    Uses multiple matching strategies for robustness:
    1. Exact match (case-insensitive)
    2. Partial match (substring match)
    3. Fuzzy match (word-level matching)
    
    Args:
        component_name: The component name to search for
        all_components: Dictionary of all components from database (grouped by main_category)
        
    Returns:
        Dict with main_category, category, and name, or None if not found.
    """
    if not component_name or not all_components:
        return None  # type: ignore[return-value]
    
    component_name_lower = component_name.lower().strip()
    component_words = set(component_name_lower.split())
    
    # Strategy 1: Try exact match first (most reliable)
    for main_cat, components_list in all_components.items():
        for comp in components_list:
            comp_name = comp.get('name', '').lower().strip()
            if comp_name == component_name_lower:
                logger.debug(f"[component_lookup] Exact match found: '{component_name}' -> '{comp.get('name')}'")
                return {
                    'main_category': comp.get('main_category', 'Unknown'),
                    'category': comp.get('category', 'Unknown'),
                    'name': comp.get('name', component_name)
                }
    
    # Strategy 2: Try partial match (one contains the other)
    for main_cat, components_list in all_components.items():
        for comp in components_list:
            comp_name = comp.get('name', '').lower().strip()
            # Check if either string contains the other
            if component_name_lower in comp_name or comp_name in component_name_lower:
                logger.debug(f"[component_lookup] Partial match found: '{component_name}' -> '{comp.get('name')}'")
                return {
                    'main_category': comp.get('main_category', 'Unknown'),
                    'category': comp.get('category', 'Unknown'),
                    'name': comp.get('name', component_name)
                }
    
    # Strategy 3: Try word-level fuzzy match (if at least 50% of words match)
    best_match = None
    best_match_score = 0
    for main_cat, components_list in all_components.items():
        for comp in components_list:
            comp_name = comp.get('name', '').lower().strip()
            comp_words = set(comp_name.split())
            
            if len(component_words) > 0 and len(comp_words) > 0:
                # Calculate word overlap percentage
                common_words = component_words.intersection(comp_words)
                overlap_score = len(common_words) / max(len(component_words), len(comp_words))
                
                # Require at least 50% word overlap and at least 2 common words for short names
                if overlap_score >= 0.5 and len(common_words) >= min(2, len(component_words)):
                    if overlap_score > best_match_score:
                        best_match_score = overlap_score
                        best_match = comp
    
    if best_match:
        logger.debug(f"[component_lookup] Fuzzy match found ({best_match_score:.0%}): '{component_name}' -> '{best_match.get('name')}'")
        return {
            'main_category': best_match.get('main_category', 'Unknown'),
            'category': best_match.get('category', 'Unknown'),
            'name': best_match.get('name', component_name)
        }
    
    return None  # type: ignore[return-value]


def get_category_indicator_from_db(value_component: str, all_db_components: dict) -> str:
    """
    Get the color indicator emoji for a value component by looking it up in the database.
    
    Args:
        value_component: The component name string
        all_db_components: Dictionary of all components from database
        
    Returns:
        Emoji string: 🔵 (Technical), 🟣 (Business), 🔴 (Strategic), 🟠 (After Sales)
    """
    db_component = find_component_in_db(value_component, all_db_components)
    
    if db_component:
        main_category = db_component.get('main_category', '').lower()
        if 'technical' in main_category:
            return '🔵'  # Technical Value
        elif 'business' in main_category:
            return '🟣'  # Business Value
        elif 'strategic' in main_category:
            return '🔴'  # Strategic Value
        elif 'after' in main_category or 'sales' in main_category:
            return '🟠'  # After Sales Value
    
    return '🔵'  # Default fallback

