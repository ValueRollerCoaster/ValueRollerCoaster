import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from app.database import get_personas, delete_persona_by_id, GENERATOR_VERSION
from app.utils.spinner import delete_spinner, search_spinner

def get_sortable_value(persona, column):
    """Extract sortable value from persona for the given column."""
    persona_details = persona.get("persona", {})
    
    if column == "company_name":
        company_name = persona_details.get("company", {}).get("name") or persona_details.get("company_name", "Unnamed Company")
        return company_name.lower()
    
    elif column == "website":
        website_url = persona_details.get("company", {}).get("website") or persona_details.get("website", "N/A")
        return website_url.lower()
    
    elif column == "scan_date":
        scan_date_str = persona.get("scan_date", "N/A")
        if scan_date_str != "N/A":
            try:
                # Convert to datetime for proper sorting
                return datetime.fromisoformat(scan_date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return datetime.min  # Put invalid dates at the beginning
        return datetime.min  # Put N/A dates at the beginning
    
    return ""

def sort_personas(personas, sort_column, sort_direction):
    """Sort personas by the specified column and direction."""
    if not sort_column:
        return personas
    
    reverse = sort_direction == "desc"
    
    # Special handling for scan_date (chronological sorting)
    if sort_column == "scan_date":
        return sorted(personas, key=lambda p: get_sortable_value(p, sort_column), reverse=reverse)
    
    # For other columns (alphabetical sorting)
    return sorted(personas, key=lambda p: get_sortable_value(p, sort_column), reverse=reverse)

async def run_persona_search_tab():
    main_col, _ = st.columns([17, 3])  # Use 85% of the width
    with main_col:
        st.title("Saved Buyer Personas")
        
        
        # --- State Initialization ---
        if "selected_persona_id" not in st.session_state:
            st.session_state.selected_persona_id = None
        if "persona_to_delete_id" not in st.session_state:
            st.session_state.persona_to_delete_id = None
        
        # --- Sorting State Initialization ---
        if "sort_column" not in st.session_state:
            st.session_state.sort_column = None
        if "sort_direction" not in st.session_state:
            st.session_state.sort_direction = "asc"

        # --- Data Fetching and Filtering ---
        with search_spinner("personas"):
            personas = await get_personas()
        if not isinstance(personas, list):
            st.error("Error: Could not retrieve personas")
            return
        
        search_query = st.text_input("Search by company, website, or scan date", "")
        
        filtered_personas = personas
        if search_query:
            search_query_lc = search_query.lower()
            filtered_personas = [
                p for p in personas if (
                    search_query_lc in str(p.get("persona", {}).get("company", {}).get("name", "")).lower() or
                    search_query_lc in str(p.get("persona", {}).get("company_name", "")).lower() or
                    search_query_lc in str(p.get("persona", {}).get("website", "")).lower() or
                    search_query_lc in str(p.get("scan_date", "")).lower()
                )
            ]
        
        # --- Apply Sorting ---
        filtered_personas = sort_personas(filtered_personas, st.session_state.sort_column, st.session_state.sort_direction)
        
        st.write(f"Found {len(filtered_personas)} personas.")

        # --- Confirmation Dialog for Deletion ---
        if st.session_state.persona_to_delete_id:
            persona_id_to_delete = st.session_state.persona_to_delete_id
            persona_to_delete = next((p for p in personas if p.get("id") == persona_id_to_delete), None)
            persona_name = persona_to_delete.get("persona", {}).get("name", "this persona") if persona_to_delete else "this persona"

            st.warning(f"Are you sure you want to delete **{persona_name}**?")
            col1, col2, _ = st.columns([1, 1, 5])
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    with delete_spinner("persona"):
                        deleted = await delete_persona_by_id(persona_id_to_delete)
                        if deleted:
                            st.success("Persona deleted successfully.")
                        else:
                            st.error("Failed to delete persona.")
                        st.session_state.persona_to_delete_id = None
                        st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.persona_to_delete_id = None
                    st.rerun()
            return # Stop further rendering to only show confirmation

        # --- Sortable Column Headers ---
        header_cols = st.columns([3, 2, 2, 1, 1])
        
        # Company Name Header
        with header_cols[0]:
            sort_indicator = ""
            if st.session_state.sort_column == "company_name":
                sort_indicator = " 🔽" if st.session_state.sort_direction == "desc" else " 🔼"
            if st.button(f"**Company Name{sort_indicator}**", key="sort_company_name", use_container_width=True):
                if st.session_state.sort_column == "company_name":
                    # Toggle direction if same column
                    st.session_state.sort_direction = "desc" if st.session_state.sort_direction == "asc" else "asc"
                else:
                    # New column, set to ascending
                    st.session_state.sort_column = "company_name"
                    st.session_state.sort_direction = "asc"
                st.rerun()
        
        # Website Header
        with header_cols[1]:
            sort_indicator = ""
            if st.session_state.sort_column == "website":
                sort_indicator = " 🔽" if st.session_state.sort_direction == "desc" else " 🔼"
            if st.button(f"**Website{sort_indicator}**", key="sort_website", use_container_width=True):
                if st.session_state.sort_column == "website":
                    # Toggle direction if same column
                    st.session_state.sort_direction = "desc" if st.session_state.sort_direction == "asc" else "asc"
                else:
                    # New column, set to ascending
                    st.session_state.sort_column = "website"
                    st.session_state.sort_direction = "asc"
                st.rerun()
        
        # Scan Date Header
        with header_cols[2]:
            sort_indicator = ""
            if st.session_state.sort_column == "scan_date":
                sort_indicator = " 🔽" if st.session_state.sort_direction == "desc" else " 🔼"
            if st.button(f"**Scan Date{sort_indicator}**", key="sort_scan_date", use_container_width=True):
                if st.session_state.sort_column == "scan_date":
                    # Toggle direction if same column
                    st.session_state.sort_direction = "desc" if st.session_state.sort_direction == "asc" else "asc"
                else:
                    # New column, set to ascending
                    st.session_state.sort_column = "scan_date"
                    st.session_state.sort_direction = "asc"
                st.rerun()
        
        st.markdown("---")

        for p in filtered_personas:
            persona_id = p.get("id")
            if not persona_id:
                continue  # Skip personas without a valid id
            persona_details = p.get("persona", {})
            # Version check
            loaded_version = p.get("generator_version")
            if loaded_version and loaded_version != GENERATOR_VERSION:
                st.warning(f"Persona {persona_details.get('company', {}).get('name', 'Unknown')} was generated with version {loaded_version}, but the current generator version is {GENERATOR_VERSION}. Some fields may be missing or different.")
            
            row_cols = st.columns([3, 2, 2, 1, 1])

            # Get company name with fallbacks
            company_name = persona_details.get("company", {}).get("name") or persona_details.get("company_name", "Unnamed Company")
            row_cols[0].write(company_name)

            website_url = persona_details.get("company", {}).get("website") or persona_details.get("website", "N/A")
            if "http" not in website_url and website_url != "N/A":
                 website_url = "https://" + website_url
            row_cols[1].markdown(f"[{website_url}]({website_url})", unsafe_allow_html=True)
            
            scan_date_str = p.get("scan_date", "N/A")
            if scan_date_str != "N/A":
                try:
                    scan_date_str = datetime.fromisoformat(scan_date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    scan_date_str = "Invalid Date" # Handle potential format errors
            row_cols[2].write(scan_date_str)

            with row_cols[3]:
                if st.button("View", key=f"view_{persona_id}"):
                    st.session_state.selected_persona_id = persona_id
                    st.session_state['came_from_search'] = True
                    st.session_state['current_page'] = "Persona Generator"
                    st.rerun()
            
            with row_cols[4]:
                if st.button("Delete", key=f"delete_{persona_id}"):
                    st.session_state.persona_to_delete_id = persona_id
                    st.rerun()

async def persona_search_tab():
    await run_persona_search_tab() 