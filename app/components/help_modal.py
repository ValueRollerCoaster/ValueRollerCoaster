"""
Help Modal Component
Provides comprehensive help information about the ValueRollerCoaster application.
"""

import streamlit as st
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class HelpModal:
    """Help modal component with organized content sections."""
    
    def __init__(self):
        self.help_content = self._initialize_help_content()
    
    def _initialize_help_content(self) -> Dict[str, Any]:
        """Initialize help content structure."""
        return {
            "overview": {
                "title": "🎢 ValueRollerCoaster Overview",
                "content": """
**ValueRollerCoaster** is an AI-powered tool that helps you:

• **Generate Buyer Personas** - Create detailed customer profiles from website analysis

• **Analyze Value Components** - Break down value propositions into measurable components  

• **Build Value Components** - Play with value components to create your own value propositions.

• **Search & Manage Personas** - Find and analyze existing customer profiles

The app uses advanced AI models (Gemini, ChatGPT, Sonar) to provide accurate, actionable insights for your sales and marketing efforts.
                """
            },
            "persona_generator": {
                "title": "👤 Persona Generator",
                "content": """
**How to Generate Buyer Personas:**

1. **Enter Website URL** - Paste the target company's website

2. **Click Generate** - The AI will analyze the website in 8 steps

**What You Get:**

• Detailed company profile and business model

• Pain points and goals analysis

• Value drivers and signals

• Likely objections and responses

• Strategic insights and recommendations
                """
            },
            "value_components": {
                "title": "💎 Value Components",
                "content": """
**Value Components** help you break down value propositions:

**Categories Available:**

• **Technical Value** - Quality, performance, efficiency, innovation, sustainability

• **Business Value** - Cost savings, revenue growth, efficiency gains

• **Strategic Value** - Competitive advantage, risk mitigation, partnership development

• **After-Sales Value** - Customer support, maintenance and updates, user experience & integration

**How to Use:**

1. Select a category from the sidebar

2. View existing value components

3. Change the user Input field

4. Set the importance (weight)  of the value component from 1 to 3

5. Use AI to generate customer benefits

6. Save

                """
            },
            "persona_search": {
                "title": "🔍 Persona Search",
                "content": """
**Search and Manage Generated Personas:**

**Search Features:**

• Search by company name or website

• Filter by industry or date

• View detailed persona profiles



**Persona Details Include:**

• Company information and business model

• Product/service analysis

• Pain points and goals

• Value drivers and signals

• Likely objections and responses

• Market intelligence insights


                """
            },
            "api_chart": {
                "title": "📊 API Chart",
                "content": """
**API Chart** provides data visualization and analytics from Eurostat.

Use it to get the latest data for the country your targeted customer is from.

**Available Charts:**

• Industry production

• Producer prices

• Industry turnover

• Construction production


                """
            },
            "tips": {
                "title": "💡 Tips & Best Practices",
                "content": """
**Getting the Best Results:**

**Website Analysis:**

• Use company's main website (not landing pages)

• Ensure website is accessible and in English

• Include industry selection for better accuracy

**Value Components:**

• Be specific with metrics and numbers

• Include both direct and indirect value

• Regular updates based on customer feedback

**Persona Management:**

• Review and validate AI-generated insights

• Add your own observations and notes

• Share personas with your sales team

**Performance:**

• Persona generation takes 4-7 minutes

• Use the progress spinner to track status

• Save results to avoid re-generation
                """
            },
            
            
        }
    
    def render_help_modal(self):
        """Render the help modal with organized content."""
        
        # Check if help modal should be shown
        if not st.session_state.get('show_help_modal', False):
            return
        
        # Add styling for compact help container
        st.markdown("""
        <style>
        /* Remove top spacing when help is shown */
        .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Compact help styling */
        .help-header-inline {
            margin: 0;
            padding: 0;
            font-size: 1.1em;
            font-weight: bold;
            color: #2c3e50;
            display: inline-block;
            vertical-align: middle;
            line-height: 1.2;
        }
        
        .help-label {
            margin: 0;
            color: #6b7280;
            font-weight: 500;
            font-size: 0.85em;
        }
        
        .help-content {
            background: white;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e5e7eb;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Compact close button */
        .help-close-button {
            width: 80px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        
        /* Dropdown width adjustment */
        .stSelectbox > div {
            width: fit-content !important;
        }
        
        /* Reduce column gaps for better inline alignment */
        .row-widget.stHorizontal {
            gap: 0.5rem !important;
        }
        
        /* Inline alignment for header and dropdown */
        .help-navigation-row {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        /* Compact container styling */
        .main .block-container {
            width: 30vw !important;
            margin: 0 auto !important;
            background: white !important;
            border-radius: 8px !important;
            padding: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            border: 1px solid #e5e7eb !important;
        }

        </style>
        """, unsafe_allow_html=True)
        
        # Get current page and determine contextual help section dynamically
        current_page = st.session_state.get("current_page", "Value Components")
        current_section = self._get_contextual_help_section(current_page)
        
        # Navigation sections with icons
        nav_sections = list(self.help_content.keys())
        nav_labels = [self.help_content[section]['title'] for section in nav_sections]
        
        # Initialize help section in session state if not exists
        if 'help_current_section' not in st.session_state:
            st.session_state['help_current_section'] = current_section
        
        # Create inline layout using columns with minimal gap
        col1, col2 = st.columns([0.3, 2.7])
        
        with col1:
            st.markdown('<span style="font-weight: bold; color: #2c3e50; font-size: 1.1em;">HELP</span>', unsafe_allow_html=True)
        
        with col2:
            # Interactive dropdown for navigation with enhanced state management
            selected_section = st.selectbox(
                "Choose a help section:",
                options=nav_sections,
                format_func=lambda x: self.help_content[x]['title'],
                index=nav_sections.index(st.session_state.get('help_current_section', current_section)) if st.session_state.get('help_current_section', current_section) in nav_sections else 0,
                key="help_navigation_dropdown",
                label_visibility="collapsed",  # Hide the label since we have our own
                on_change=self._update_help_section
            )
            
            # Update session state immediately when selection changes
            if selected_section != st.session_state.get('help_current_section'):
                st.session_state['help_current_section'] = selected_section
        
        # Get selected section content using session state for consistency
        active_section = st.session_state.get('help_current_section', selected_section)
        selected_title = self.help_content[active_section]['title']
        selected_content = self.help_content[active_section]['content']
        
        # Display content directly in a dynamic container (no expander)
        st.markdown(f"""
        <div class="help-content">
            <h3 style="margin-top: 0; margin-bottom: 15px; color: #2c3e50; font-size: 1.1em; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
                {selected_title}
            </h3>
            <div style="font-size: 0.9em; line-height: 1.5;">
                {selected_content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Close button - shorter and centered
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("❌ Close", use_container_width=False, key="close_help_modal"):
                self.hide_help_modal()
                st.rerun()
    
    def show_help_modal(self, section: str = 'overview'):
        """Show the help modal with specified section."""
        st.session_state['show_help_modal'] = True
        st.session_state['help_current_section'] = section
        # Force immediate update
        st.rerun()
    
    def hide_help_modal(self):
        """Hide the help modal."""
        st.session_state['show_help_modal'] = False
    
    def _get_contextual_help_section(self, current_page: str) -> str:
        """Get the appropriate help section based on current page."""
        # Check if user is in notification center (special UI state)
        if st.session_state.get("show_notification_center", False):
            return "notification_center"
        
        page_to_help_mapping = {
            "Value Components": "value_components",
            "Persona Generator": "persona_generator", 
            "Persona Search": "persona_search",
            "API Chart": "api_chart"
        }
        
        result = page_to_help_mapping.get(current_page, "overview")
        
        return result

    def _update_help_section(self):
        """Callback function to update help section when dropdown changes."""
        # This function is called when the dropdown selection changes
        # The actual update is handled in the main render method
        pass
    
    def _update_sidebar_help_section(self):
        """Callback function to update sidebar help section when dropdown changes."""
        # Mark that the sidebar help section has changed to trigger immediate update
        st.session_state["sidebar_help_section_changed"] = True

# Global help modal instance
help_modal = HelpModal()

def render_help_button():
    """Render help dropdown directly in sidebar."""
    # Get current page for contextual help
    current_page = st.session_state.get("current_page", "Value Components")
    current_section = help_modal._get_contextual_help_section(current_page)
    
    # Create help dropdown in sidebar
    st.sidebar.markdown("### 📚 Help")
    
    # Get all help sections
    nav_sections = list(help_modal.help_content.keys())
    nav_labels = [help_modal.help_content[section]['title'] for section in nav_sections]
    
    # Add default option
    options_with_default = ["Choose help section..."] + nav_sections
    format_func_options = ["Choose help section..."] + nav_labels
    
    # Check if help should be shown (for close button functionality)
    show_help = st.session_state.get("show_sidebar_help", False)
    
    # Create dropdown for help sections with default option
    selected_help_section = st.sidebar.selectbox(
        "Choose help section:",
        options=options_with_default,
        format_func=lambda x: x if x == "Choose help section..." else help_modal.help_content[x]['title'],
        index=0 if not show_help else (options_with_default.index(st.session_state.get("last_help_section", "Choose help section...")) if st.session_state.get("last_help_section") in options_with_default else 0),
        key="sidebar_help_dropdown",
        label_visibility="collapsed",
        on_change=help_modal._update_sidebar_help_section
    )
    
    # Update session state immediately when selection changes
    if selected_help_section != "Choose help section...":
        st.session_state["show_sidebar_help"] = True
        st.session_state["last_help_section"] = selected_help_section
        # Force immediate update by triggering rerun
        if st.session_state.get("sidebar_help_section_changed", False):
            st.session_state["sidebar_help_section_changed"] = False
            st.rerun()
    
    # Display selected help content directly in sidebar (only if not default)
    if selected_help_section and selected_help_section != "Choose help section...":
        selected_title = help_modal.help_content[selected_help_section]['title']
        selected_content = help_modal.help_content[selected_help_section]['content']
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**{selected_title}**")
        st.sidebar.markdown(selected_content)
        
        # Add close button
        if st.sidebar.button("❌ Close Help", key="close_sidebar_help", use_container_width=True):
            # Hide help by setting flag
            st.session_state["show_sidebar_help"] = False
            st.session_state["last_help_section"] = "Choose help section..."
            st.rerun() 