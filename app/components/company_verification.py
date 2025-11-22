"""
Company Verification Component
Provides UI for user to verify/correct company identification before persona generation.
"""

import logging
import streamlit as st
from typing import Dict, Optional, Callable, Any
import asyncio

from app.utils.domain_company_lookup import get_domain_from_url, lookup_company_by_domain

logger = logging.getLogger(__name__)


async def render_company_verification_modal(website_url: str, pid: int = 0) -> Optional[Dict[str, Any]]:
    """
    Render company verification modal that requires user confirmation before proceeding.
    
    Args:
        website_url: Website URL to verify
        pid: Process ID for logging
        
    Returns:
        Dictionary with verified company information:
        {
            "company_name": str,
            "industry": Optional[str],
            "verified": bool
        }
        Returns None if user cancels
    """
    # Extract domain
    domain = get_domain_from_url(website_url)
    if not domain:
        st.error("Invalid website URL. Please check the URL and try again.")
        return None
    
    # Check if we already have verified company in session state
    verification_key = f"company_verification_{domain}"
    verification_in_progress_key = f"verification_in_progress_{domain}"
    
    if verification_key in st.session_state:
        verified_data = st.session_state[verification_key]
        # Only return early if it's verified
        if verified_data.get("verified", False):
            logger.info(f"[PID {pid}] Using cached verification for {domain}")
            return verified_data
    
    # Mark that verification is in progress (prevents auto-generation)
    # This MUST be set before any UI rendering to persist through reruns
    st.session_state[verification_in_progress_key] = True
    logger.info(f"[PID {pid}] Verification in progress flag set for domain {domain}")
    
    # Show verification modal
    st.markdown("---")
    st.markdown("### 🔍 Company Verification Required")
    st.info("Please verify the company information before we proceed with persona generation.")
    
    # Lookup company from domain
    lookup_result_key = f"domain_lookup_{domain}"
    if lookup_result_key not in st.session_state:
        # Perform lookup - use await since we're in async context
        with st.spinner("Identifying company from domain..."):
            try:
                lookup_result = await lookup_company_by_domain(domain, pid)
                st.session_state[lookup_result_key] = lookup_result
            except Exception as e:
                logger.error(f"[PID {pid}] Domain lookup error: {e}")
                st.session_state[lookup_result_key] = {
                    "company_name": None,
                    "confidence": 0.0,
                    "source": "error",
                    "industry": None,
                    "location": None,
                    "error": str(e)
                }
    
    lookup_result = st.session_state[lookup_result_key]
    identified_company = lookup_result.get("company_name")
    confidence = lookup_result.get("confidence", 0.0)
    source = lookup_result.get("source", "unknown")
    error = lookup_result.get("error")
    
    # Display domain (read-only, for reference)
    st.markdown(f"**Domain:** `{domain}`")
    st.caption("ℹ️ The domain is correct. If the company name below is wrong, please edit it.")
    
    # Show identified company info if available
    if identified_company and not error:
        if confidence < 0.7:
            st.warning(f"⚠️ Low confidence ({confidence*100:.0f}%) - Please verify this is correct")
        elif confidence < 0.9:
            st.info(f"ℹ️ Medium confidence ({confidence*100:.0f}%) - Please confirm")
        else:
            st.success(f"✓ High confidence ({confidence*100:.0f}%)")
    
    # Always show input field for company name - simple and direct
    # Pre-fill with identified company if available
    default_value = identified_company if identified_company and not error else ""
    
    if not identified_company or error:
        st.warning("⚠️ Unable to identify company from domain. Please enter the company name manually.")
        if error:
            st.caption(f"Error: {error}")
    
    # Always show the input field - user can edit directly
    company_name = st.text_input(
        "Company Name:",
        value=default_value,
        key=f"company_name_input_{domain}",
        help="Enter the exact company name that owns this domain. You can edit the identified name if it's incorrect.",
        placeholder="e.g. Wyland-Yutani Corporation "
    )
    
    # Show what was identified if different from current input
    if identified_company and identified_company != company_name and company_name:
        st.caption(f"💡 Identified: {identified_company} → You entered: {company_name}")
    
    # Industry dropdown (optional)
    industry_options = [
        "Select industry (optional)",
        "Construction Machinery",
        "Manufacturing",
        "Technology",
        "Healthcare",
        "Finance",
        "Retail",
        "Energy",
        "Automotive",
        "Aerospace",
        "Agriculture",
        "Food & Beverage",
        "Pharmaceuticals",
        "Telecommunications",
        "Real Estate",
        "Education",
        "Hospitality",
        "Transportation",
        "Other"
    ]
    
    # Pre-select industry if available from lookup
    default_industry_idx = 0
    if lookup_result.get("industry"):
        lookup_industry = lookup_result.get("industry")
        # Try to match with options
        for idx, option in enumerate(industry_options):
            if lookup_industry.lower() in option.lower() or option.lower() in lookup_industry.lower():
                default_industry_idx = idx
                break
    
    selected_industry = st.selectbox(
        "Industry (optional):",
        options=industry_options,
        index=default_industry_idx,
        key=f"industry_select_{domain}",
        help="Select the industry to help improve analysis accuracy"
    )
    
    # Convert "Select industry (optional)" to None
    industry = None if selected_industry == "Select industry (optional)" else selected_industry
    
    # Validation
    if not company_name or not company_name.strip():
        st.error("⚠️ Company name is required. Please enter the company name.")
        # Buttons (disabled until valid)
        col1, col2 = st.columns(2)
        with col1:
            st.button("✓ Confirm and Proceed", key=f"confirm_{domain}", disabled=True, type="primary")
        with col2:
            if st.button("Cancel", key=f"cancel_{domain}"):
                # Clear verification and editing state
                st.session_state[verification_key] = None
                if lookup_result_key in st.session_state:
                    del st.session_state[lookup_result_key]
                st.rerun()
        return None
    
    
    # Action buttons - these are the ONLY way to proceed or cancel
    col1, col2 = st.columns(2)
    confirmed = False
    cancelled = False
    
    with col1:
        confirm_button = st.button("✓ Confirm and Proceed", key=f"confirm_{domain}", type="primary", use_container_width=True)
        if confirm_button:
            confirmed = True
    
    with col2:
        cancel_button = st.button("Cancel", key=f"cancel_{domain}", use_container_width=True)
        if cancel_button:
            cancelled = True
    
    # Handle confirmation - ONLY if button was explicitly clicked
    if confirmed:
        # Check if company name was edited
        was_edited = False
        if identified_company and company_name.strip() != identified_company:
            was_edited = True
            logger.info(f"[PID {pid}] Company name was edited: '{identified_company}' -> '{company_name.strip()}'")
        
        # Store verified data
        verified_data = {
            "company_name": company_name.strip(),
            "industry": industry,
            "verified": True,
            "domain": domain,
            "source": "user_verified",
            "original_lookup": identified_company if identified_company else None,
            "was_edited": was_edited
        }
        st.session_state[verification_key] = verified_data
        
        # Clear verification in progress flag
        if verification_in_progress_key in st.session_state:
            del st.session_state[verification_in_progress_key]
        
        logger.info(f"[PID {pid}] Company verified: {company_name.strip()} for domain {domain} (was_edited: {was_edited})")
        # Don't call st.rerun() here - let the caller handle it
        return verified_data
    
    # Handle cancellation
    if cancelled:
        # Clear verification state
        if verification_key in st.session_state:
            del st.session_state[verification_key]
        if lookup_result_key in st.session_state:
            del st.session_state[lookup_result_key]
        if verification_in_progress_key in st.session_state:
            del st.session_state[verification_in_progress_key]
        logger.info(f"[PID {pid}] Company verification cancelled for domain {domain}")
        return None
    
    # Return None if no action taken yet - this means user hasn't clicked any button
    # The modal will stay visible and wait for explicit user action
    # CRITICAL: Do NOT proceed with generation - return None to stop the process
    logger.debug(f"[PID {pid}] Verification modal: No action taken, waiting for user to confirm or cancel")
    return None


def get_verified_company(domain: str) -> Optional[Dict[str, Any]]:
    """
    Get verified company information from session state.
    
    Args:
        domain: Domain name
        
    Returns:
        Verified company data or None
    """
    verification_key = f"company_verification_{domain}"
    return st.session_state.get(verification_key)

