"""
Framework Properties Display Component
Shows individual framework properties with customization indicators
"""

import streamlit as st
import logging
from typing import Dict, Any, List
from ..utils.framework_helpers import get_customization_source

logger = logging.getLogger(__name__)

def render_framework_properties(framework_data: Dict[str, Any], 
                               company_profile: Dict[str, Any],
                               industry_name: str,
                               validation_enabled: bool = False) -> None:
    """Render framework properties with validation indicators"""
    
    # Show overall quality score if validation enabled
    if validation_enabled:
        validation = framework_data.get("_validation", {})
        overall_quality = validation.get("overall_quality", 0)
        
        if overall_quality > 0:
            st.markdown("### 📊 Framework Quality")
            
            # Quality score with color coding
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if overall_quality >= 80:
                    quality_color = "green"
                    quality_label = "🟢 Excellent"
                elif overall_quality >= 60:
                    quality_color = "orange"
                    quality_label = "🟡 Good"
                else:
                    quality_color = "red"
                    quality_label = "🔴 Needs Improvement"
                
                st.markdown(f"**Overall Quality:** <span style='color: {quality_color}; font-size: 1.2em'>{overall_quality:.1f}/100</span> - {quality_label}", 
                           unsafe_allow_html=True)
                st.progress(overall_quality / 100)
            
            with col2:
                relevance_avg = _get_avg_relevance(validation)
                st.metric("Relevance", f"{relevance_avg:.1f}/100")
            
            with col3:
                completeness = validation.get("completeness", {}).get("completeness_score", 0)
                st.metric("Completeness", f"{completeness:.1f}/100")
            
            # Show issues if any
            issues = []
            missing_count = len(validation.get("completeness", {}).get("missing_critical", []))
            consistency_count = len(validation.get("consistency", {}).get("issues", []))
            low_relevance_count = sum(
                len(prop.get("low_relevance_items", []))
                for prop in validation.get("relevance", {}).values()
                if isinstance(prop, dict)
            )
            
            if missing_count > 0:
                issues.append(f"⚠️ {missing_count} missing critical elements")
            if consistency_count > 0:
                issues.append(f"⚠️ {consistency_count} consistency issues")
            if low_relevance_count > 0:
                issues.append(f"⚠️ {low_relevance_count} low relevance items")
            
            if issues:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.warning(" | ".join(issues))
                with col2:
                    if st.button("📋 View All Issues", key=f"view_issues_{industry_name}", use_container_width=True):
                        st.session_state[f"show_issues_{industry_name}"] = not st.session_state.get(f"show_issues_{industry_name}", False)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                # Apply AI Refinements button
                ai_validation = validation.get("ai_validation", {})
                refinements = ai_validation.get("refinements", [])
                high_confidence_refinements = [r for r in refinements if r.get("confidence", 0) >= 0.85]
                
                if high_confidence_refinements:
                    if st.button(f"✅ Apply AI Refinements ({len(high_confidence_refinements)})", 
                                key=f"apply_refinements_{industry_name}", use_container_width=True):
                        _apply_ai_refinements(framework_data, industry_name, high_confidence_refinements)
                        st.success(f"Applied {len(high_confidence_refinements)} high-confidence refinements!")
                        st.rerun()
            
            with col2:
                # Re-validate button
                if st.button("🔄 Re-validate", key=f"revalidate_{industry_name}", use_container_width=True):
                    # Clear validation to force re-validation
                    if "framework_validations" in st.session_state:
                        if industry_name in st.session_state["framework_validations"]:
                            # Store previous validation for comparison
                            st.session_state[f"prev_validation_{industry_name}"] = st.session_state["framework_validations"][industry_name]
                            del st.session_state["framework_validations"][industry_name]
                    st.info("Validation cleared. Click '🔍 Validate' to re-validate.")
                    st.rerun()
            
            with col3:
                # Show comparison if previous validation exists
                prev_validation = st.session_state.get(f"prev_validation_{industry_name}")
                if prev_validation:
                    prev_quality = prev_validation.get("overall_quality", 0)
                    current_quality = overall_quality
                    improvement = current_quality - prev_quality
                    if improvement > 0:
                        st.success(f"📈 +{improvement:.1f} improvement")
                    elif improvement < 0:
                        st.warning(f"📉 {improvement:.1f} change")
            
            st.markdown("---")
            
            # Issues Panel (expandable)
            if st.session_state.get(f"show_issues_{industry_name}", False):
                _render_issues_panel(framework_data, validation, industry_name)
    
    # Define all 9 framework properties
    properties = [
        ("industry_name", "Industry Name", "The normalized and display name for the industry"),
        ("nace_codes", "NACE Codes", "European industry classification codes"),
        ("key_metrics", "Key Metrics", "Performance metrics relevant to this industry"),
        ("trend_areas", "Trend Areas", "Current and emerging trends in the industry"),
        ("competitive_factors", "Competitive Factors", "Factors that drive competition"),
        ("value_drivers", "Value Drivers", "What creates value in this industry"),
        ("pain_points", "Pain Points", "Common challenges and pain points"),
        ("technology_focus", "Technology Focus", "Technology areas of focus"),
        ("sustainability_initiatives", "Sustainability Initiatives", "Sustainability-related initiatives")
    ]
    
    for prop_key, prop_label, prop_description in properties:
        with st.expander(f"**{prop_label}** ({len(framework_data.get(prop_key, []))} items)", expanded=False):
            st.caption(prop_description)
            
            # Show property-level validation if available
            if validation_enabled and prop_key != "industry_name":
                validation = framework_data.get("_validation", {})
                relevance = validation.get("relevance", {})
                prop_validation = relevance.get(prop_key, {})
                
                if prop_validation and prop_validation.get("property_score"):
                    score = prop_validation["property_score"]
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if score >= 80:
                            score_color = "green"
                        elif score >= 60:
                            score_color = "orange"
                        else:
                            score_color = "red"
                        st.markdown(f"**Relevance Score:** <span style='color: {score_color}'>{score:.1f}/100</span>", 
                                   unsafe_allow_html=True)
                    with col2:
                        st.progress(score / 100)
                    
                    # Show low relevance items
                    low_relevance = prop_validation.get("low_relevance_items", [])
                    if low_relevance:
                        st.warning(f"⚠️ Low relevance items: {', '.join(low_relevance[:3])}")
                    
                    st.markdown("---")
            
            # Get customization sources
            if prop_key != "industry_name":
                sources = get_customization_source(prop_key, framework_data, company_profile)
                if sources:
                    st.markdown(f"**Customization Sources:** {' '.join(sources)}")
            
            # Display property value
            prop_value = framework_data.get(prop_key, [])
            
            if prop_key == "industry_name":
                st.markdown(f"**Display Name:** {prop_value}")
                st.markdown(f"**Normalized:** {industry_name}")
            elif prop_key == "nace_codes":
                if prop_value:
                    for code in prop_value:
                        st.markdown(f"• **{code}**")
                else:
                    st.warning("No NACE codes detected for this industry")
            elif isinstance(prop_value, list):
                if prop_value:
                    # Show item-level scores if available
                    if validation_enabled:
                        validation = framework_data.get("_validation", {})
                        relevance = validation.get("relevance", {})
                        prop_validation = relevance.get(prop_key, {})
                        item_scores = prop_validation.get("item_scores", {}) if prop_validation else {}
                        
                        for item in prop_value:
                            score = item_scores.get(item, None)
                            if score is not None:
                                if score >= 80:
                                    icon = "✅"
                                elif score >= 60:
                                    icon = "⚠️"
                                else:
                                    icon = "❌"
                                
                                # Show item with remove button for low relevance items
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"{icon} **{item}** <small style='color: #666'>({score:.0f}/100)</small>", 
                                               unsafe_allow_html=True)
                                with col2:
                                    if score < 60:  # Low relevance - show remove button
                                        if st.button("🗑️", key=f"remove_{prop_key}_{item}_{industry_name}", 
                                                    help="Remove low relevance item"):
                                            _remove_framework_item(framework_data, prop_key, item, industry_name)
                                            st.rerun()
                            else:
                                st.markdown(f"• {item}")
                    else:
                        for item in prop_value:
                            st.markdown(f"• {item}")
                else:
                    st.info("No items in this property")
            else:
                st.markdown(str(prop_value))
            
            st.markdown("---")

def _get_avg_relevance(validation: Dict[str, Any]) -> float:
    """Get average relevance score"""
    relevance = validation.get("relevance", {})
    if isinstance(relevance, dict):
        scores = [
            r.get("property_score", 0) 
            for r in relevance.values() 
            if isinstance(r, dict)
        ]
        if scores:
            return sum(scores) / len(scores)
    return 0.0

def _render_issues_panel(framework_data: Dict[str, Any], validation: Dict[str, Any], industry_name: str) -> None:
    """Render detailed issues panel with actions"""
    st.markdown("### 🔍 Validation Issues & Actions")
    
    # Missing Critical Elements
    completeness_data = validation.get("completeness", {})
    missing_critical = completeness_data.get("missing_critical", [])
    property_completeness = completeness_data.get("property_completeness", {})
    
    # Also check AI validation for missing elements
    ai_missing = validation.get("ai_validation", {}).get("missing_elements", [])
    
    # Combine both sources and map strings to properties
    all_missing = []
    
    # Process completeness validator results (strings need property mapping)
    if missing_critical:
        # Try to map strings to properties from property_completeness
        for item in missing_critical:
            if isinstance(item, str):
                # String format from completeness validator - try to find which property it belongs to
                property_name = "unknown"
                # Check property_completeness to find which property this item belongs to
                for prop_name, prop_data in property_completeness.items():
                    if isinstance(prop_data, dict):
                        prop_missing = prop_data.get("missing_critical", [])
                        if item in prop_missing or any(item.lower() in str(m).lower() for m in prop_missing):
                            property_name = prop_name
                            break
                
                all_missing.append({
                    "element": item,
                    "property": property_name,
                    "reason": "Missing critical element"
                })
            elif isinstance(item, dict):
                # Dictionary format (shouldn't happen from completeness validator, but handle it)
                all_missing.append({
                    "element": item.get("element", "Unknown"),
                    "property": item.get("property", "unknown"),
                    "reason": item.get("reason", "")
                })
    
    # Process AI validator results (should be dictionaries)
    if ai_missing:
        for item in ai_missing:
            if isinstance(item, dict):
                all_missing.append({
                    "element": item.get("element", "Unknown"),
                    "property": item.get("property", "unknown"),
                    "reason": item.get("reason", "")
                })
            elif isinstance(item, str):
                # Fallback if AI validator returns strings
                all_missing.append({
                    "element": item,
                    "property": "unknown",
                    "reason": "Missing element"
                })
    
    if all_missing:
        st.markdown("#### ⚠️ Missing Critical Elements")
        for issue in all_missing:
            property_name = issue.get("property", "unknown")
            element = issue.get("element", "Unknown element")
            reason = issue.get("reason", "")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if property_name != "unknown":
                    st.markdown(f"**{element}** ({property_name})")
                else:
                    st.markdown(f"**{element}**")
                if reason and reason not in ["Missing critical element", "Missing element"]:
                    st.caption(f"Reason: {reason}")
            with col2:
                if property_name != "unknown":
                    if st.button("➕ Add", key=f"add_missing_{property_name}_{element}_{industry_name}", 
                               use_container_width=True):
                        _add_framework_item(framework_data, property_name, element, industry_name)
                        st.rerun()
                else:
                    st.info("Property unknown")
        st.markdown("---")
    
    # Low Relevance Items
    relevance = validation.get("relevance", {})
    low_relevance_all = []
    for prop_name, prop_validation in relevance.items():
        if isinstance(prop_validation, dict):
            low_items = prop_validation.get("low_relevance_items", [])
            item_scores = prop_validation.get("item_scores", {})
            for item in low_items:
                score = item_scores.get(item, 0)
                low_relevance_all.append({
                    "property": prop_name,
                    "item": item,
                    "score": score
                })
    
    if low_relevance_all:
        st.markdown("#### ❌ Low Relevance Items")
        for issue in low_relevance_all[:10]:  # Limit to 10 for display
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{issue['item']}** ({issue['property']}) - Score: {issue['score']:.0f}/100")
            with col2:
                if st.button("🗑️ Remove", key=f"remove_low_{issue['property']}_{issue['item']}_{industry_name}", 
                           use_container_width=True):
                    _remove_framework_item(framework_data, issue['property'], issue['item'], industry_name)
                    st.rerun()
            with col3:
                if st.button("✏️ Edit", key=f"edit_low_{issue['property']}_{issue['item']}_{industry_name}", 
                           use_container_width=True):
                    st.session_state[f"editing_{issue['property']}_{issue['item']}_{industry_name}"] = True
                    st.rerun()
        if len(low_relevance_all) > 10:
            st.caption(f"... and {len(low_relevance_all) - 10} more low relevance items")
        st.markdown("---")
    
    # Consistency Issues
    consistency_issues = validation.get("consistency", {}).get("issues", [])
    if consistency_issues:
        st.markdown("#### ⚠️ Consistency Issues")
        for issue in consistency_issues:
            issue_type = issue.get("type", "unknown")
            description = issue.get("description", "No description")
            severity = issue.get("severity", "medium")
            
            severity_color = "red" if severity == "high" else "orange" if severity == "medium" else "gray"
            st.markdown(f"**{issue_type.replace('_', ' ').title()}** - <span style='color: {severity_color}'>{severity}</span>", 
                       unsafe_allow_html=True)
            st.caption(description)
        st.markdown("---")
    
    # AI Refinements
    ai_validation = validation.get("ai_validation", {})
    refinements = ai_validation.get("refinements", [])
    if refinements:
        st.markdown("#### 🤖 AI Suggested Refinements")
        
        high_conf = [r for r in refinements if r.get("confidence", 0) >= 0.85]
        medium_conf = [r for r in refinements if 0.70 <= r.get("confidence", 0) < 0.85]
        low_conf = [r for r in refinements if r.get("confidence", 0) < 0.70]
        
        if high_conf:
            st.markdown("**High Confidence (≥85%):**")
            for ref in high_conf:
                _render_refinement(ref, framework_data, industry_name, "high")
        
        if medium_conf:
            st.markdown("**Medium Confidence (70-84%):**")
            for ref in medium_conf:
                _render_refinement(ref, framework_data, industry_name, "medium")
        
        if low_conf:
            with st.expander("Low Confidence (<70%)", expanded=False):
                for ref in low_conf:
                    _render_refinement(ref, framework_data, industry_name, "low")

def _render_refinement(ref: Dict[str, Any], framework_data: Dict[str, Any], industry_name: str, confidence_level: str) -> None:
    """Render a single refinement suggestion"""
    property_name = ref.get("property", "unknown")
    action = ref.get("action", "unknown")
    item = ref.get("item", "")
    suggestion = ref.get("suggestion", "")
    confidence = ref.get("confidence", 0) * 100
    
    if action == "add":
        st.markdown(f"➕ Add **{suggestion}** to {property_name} ({confidence:.0f}% confidence)")
        if st.button("Apply", key=f"apply_ref_{property_name}_{suggestion}_{industry_name}", 
                    use_container_width=True):
            _add_framework_item(framework_data, property_name, suggestion, industry_name)
            st.rerun()
    elif action == "remove":
        st.markdown(f"🗑️ Remove **{item}** from {property_name} ({confidence:.0f}% confidence)")
        if st.button("Apply", key=f"apply_ref_remove_{property_name}_{item}_{industry_name}", 
                    use_container_width=True):
            _remove_framework_item(framework_data, property_name, item, industry_name)
            st.rerun()
    elif action == "replace":
        st.markdown(f"🔄 Replace **{item}** with **{suggestion}** in {property_name} ({confidence:.0f}% confidence)")
        if st.button("Apply", key=f"apply_ref_replace_{property_name}_{item}_{industry_name}", 
                    use_container_width=True):
            _replace_framework_item(framework_data, property_name, item, suggestion, industry_name)
            st.rerun()

def _apply_ai_refinements(framework_data: Dict[str, Any], industry_name: str, refinements: List[Dict[str, Any]]) -> None:
    """Apply high-confidence AI refinements to framework"""
    import asyncio
    from app.ai.market_intelligence.validation.ai_validator import AIFrameworkValidator
    
    # Get framework from session state
    framework = st.session_state.get(f"framework_data_{industry_name}", framework_data)
    
    ai_validator = AIFrameworkValidator()
    updated_framework = asyncio.run(ai_validator.apply_refinements(framework, refinements))
    
    # Save customizations to database
    normalized_industry = industry_name.lower().replace(" ", "_")
    try:
        from app.database_framework_customizations import (
            update_customization_add_item,
            update_customization_remove_item,
            update_customization_replace_item
        )
        
        # Process each refinement and save to database
        for refinement in refinements:
            property_name = refinement.get("property")
            action = refinement.get("action")
            confidence = refinement.get("confidence", 0.0)
            
            # Only save high-confidence refinements (same threshold as apply_refinements)
            if confidence < 0.85:
                continue
            
            # Skip if property_name is missing
            if not property_name:
                continue
            
            if action == "add":
                suggestion = refinement.get("suggestion")
                if suggestion:
                    update_customization_add_item(normalized_industry, property_name, suggestion)
            elif action == "remove":
                item = refinement.get("item")
                if item:
                    update_customization_remove_item(normalized_industry, property_name, item)
            elif action == "replace":
                item = refinement.get("item")
                suggestion = refinement.get("suggestion")
                if item and suggestion:
                    update_customization_replace_item(normalized_industry, property_name, item, suggestion)
    except Exception as e:
        logger.warning(f"Could not save AI refinement customizations: {e}")
    
    # Update framework in session state
    st.session_state[f"framework_data_{industry_name}"] = updated_framework
    
    # Clear validation to force re-validation
    if "framework_validations" in st.session_state:
        if industry_name in st.session_state["framework_validations"]:
            del st.session_state["framework_validations"][industry_name]

def _add_framework_item(framework_data: Dict[str, Any], property_name: str, item: str, industry_name: str) -> None:
    """Add item to framework property"""
    # Get framework from session state or use provided
    framework = st.session_state.get(f"framework_data_{industry_name}", framework_data)
    
    if property_name in framework and isinstance(framework[property_name], list):
        if item not in framework[property_name]:
            framework[property_name].append(item)
            # Update session state
            st.session_state[f"framework_data_{industry_name}"] = framework
            
            # Save to database for persistence
            try:
                from app.database_framework_customizations import update_customization_add_item
                normalized_industry = industry_name.lower().replace(" ", "_")
                update_customization_add_item(normalized_industry, property_name, item)
                
                # Note: Customizations are applied on every framework load,
                # so cache clearing is not necessary
            except Exception as e:
                logger.warning(f"Could not save framework customization: {e}")
            
            # Clear validation to force re-validation
            if "framework_validations" in st.session_state:
                if industry_name in st.session_state["framework_validations"]:
                    del st.session_state["framework_validations"][industry_name]

def _remove_framework_item(framework_data: Dict[str, Any], property_name: str, item: str, industry_name: str) -> None:
    """Remove item from framework property"""
    # Get framework from session state or use provided
    framework = st.session_state.get(f"framework_data_{industry_name}", framework_data)
    
    if property_name in framework and isinstance(framework[property_name], list):
        if item in framework[property_name]:
            framework[property_name].remove(item)
            # Update session state
            st.session_state[f"framework_data_{industry_name}"] = framework
            
            # Save to database for persistence
            try:
                from app.database_framework_customizations import update_customization_remove_item
                normalized_industry = industry_name.lower().replace(" ", "_")
                update_customization_remove_item(normalized_industry, property_name, item)
                
                # Note: Customizations are applied on every framework load,
                # so cache clearing is not necessary
            except Exception as e:
                logger.warning(f"Could not save framework customization: {e}")
            
            # Clear validation to force re-validation
            if "framework_validations" in st.session_state:
                if industry_name in st.session_state["framework_validations"]:
                    del st.session_state["framework_validations"][industry_name]

def _replace_framework_item(framework_data: Dict[str, Any], property_name: str, old_item: str, new_item: str, industry_name: str) -> None:
    """Replace item in framework property"""
    # Get framework from session state or use provided
    framework = st.session_state.get(f"framework_data_{industry_name}", framework_data)
    
    if property_name in framework and isinstance(framework[property_name], list):
        try:
            index = framework[property_name].index(old_item)
            framework[property_name][index] = new_item
            # Update session state
            st.session_state[f"framework_data_{industry_name}"] = framework
            
            # Save to database for persistence
            try:
                from app.database_framework_customizations import update_customization_replace_item
                normalized_industry = industry_name.lower().replace(" ", "_")
                update_customization_replace_item(normalized_industry, property_name, old_item, new_item)
                
                # Note: Customizations are applied on every framework load,
                # so cache clearing is not necessary
            except Exception as e:
                logger.warning(f"Could not save framework customization: {e}")
            
            # Clear validation to force re-validation
            if "framework_validations" in st.session_state:
                if industry_name in st.session_state["framework_validations"]:
                    del st.session_state["framework_validations"][industry_name]
        except ValueError:
            pass

