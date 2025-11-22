import streamlit as st
import asyncio
import time
from typing import Dict, Any, Optional

class UniversalUserDrivenValidation:
    """Universal user-driven validation that adapts to any company profile"""
    
    def __init__(self):
        from app.utils.universal_company_context_extractor import UniversalCompanyContextExtractor
        from app.utils.universal_ai_guidance_generator import UniversalAIGuidanceGenerator
        from app.utils.dynamic_example_generator import DynamicExampleGenerator
        
        self.context_extractor = UniversalCompanyContextExtractor()
        self.guidance_generator = UniversalAIGuidanceGenerator()
        self.example_generator = DynamicExampleGenerator()
    
    async def create_validation_interface(self, field_name: str, field_description: str, 
                                  main_category: str, subcategory: str, current_value: str = "", tooltip_content: Optional[str] = None):
        """Create universal validation interface"""
        
        # Input field
        input_key = f"{main_category}_{subcategory}_{field_name}_input"
        user_input = st.text_area(
            f"Enter {field_name}",
            value=current_value,
            key=input_key,
            height=68,
            label_visibility="collapsed"
        )
        
        if user_input:
            # AI assistance section
            await self._render_ai_assistance(user_input, field_name, field_description, 
                                     main_category, subcategory)
        
        return user_input
    

    async def _render_ai_assistance(self, user_input: str, field_name: str, field_description: str,
                              main_category: str, subcategory: str):
        """Render AI assistance options with tooltips"""
        #st.write("**🤖 AI Assistance**")
        
        # Main guidance button only
        if st.button("💡 Get AI Guidance", key=f"guidance_{field_name}"):
            guidance = await self.guidance_generator.generate_field_guidance(
                user_input, field_description, field_name, main_category, subcategory
            )
            st.session_state[f"{field_name}_guidance"] = guidance
            st.session_state[f"{field_name}_show_context"] = False
        
        # Display AI guidance only if guidance exists
        if st.session_state.get(f"{field_name}_guidance"):
            self._display_ai_guidance(field_name)
    
    def _display_ai_guidance(self, field_name: str, guidance_key: Optional[str] = None):
        """Display AI guidance results with company context integration"""
        if guidance_key is None:
            guidance_key = f"{field_name}_guidance"
        
        # Use the field_name for context toggle keys to avoid conflicts
        context_toggle_key = f"{field_name}_show_context"
        show_context = st.session_state.get(context_toggle_key, False)
        
        with st.expander("🤖 AI Guidance", expanded=True):
            # Custom styling for the expander
            st.markdown("""
            <style>
            .stExpander > div > div > div > div {
                background-color: #fefefe !important;
            }
            </style>
            """, unsafe_allow_html=True)
            # Header with dynamic button
            col1, col2 = st.columns([3, 1])
            with col1:
                # Extract field name for display (e.g., "ethical sourcing" from "Ethical Sourcing")
                field_name_words = field_name.split()
                display_field_name = " ".join(field_name_words).lower()
                st.write(f"**AI Assistance for {display_field_name}**")
            with col2:
                if show_context:
                    # Show back button when in context view
                    if st.button("← Back to AI Guidance", key=f"back_to_guidance_{field_name}"):
                        st.session_state[context_toggle_key] = False
                        st.rerun()
                else:
                    # Show company context button when in guidance view
                    if st.button("🔍 Company Context", key=f"context_toggle_{field_name}", 
                               help="Switch to company context view"):
                        st.session_state[context_toggle_key] = True
                        st.rerun()
            
            if show_context:
                # Display company context
                self._display_company_context_inline(field_name)
            else:
                # Display AI guidance
                if st.session_state.get(guidance_key):
                    guidance = st.session_state[guidance_key]
                    
                    # Build analysis content HTML
                    analysis_html = ""
                    
                    # Company alignment
                    analysis_html += "<div style='margin: 15px 0;'><strong>Company Alignment</strong><br>"
                    analysis_html += f"{guidance.get('company_alignment', 'No alignment analysis available')}<br></div>"
                    
                    # Industry relevance
                    analysis_html += "<div style='margin: 15px 0;'><strong>Industry Relevance</strong><br>"
                    analysis_html += f"{guidance.get('industry_relevance', 'No industry analysis available')}<br></div>"
                    
                    # Capability alignment
                    analysis_html += "<div style='margin: 15px 0;'><strong>Capability Alignment</strong><br>"
                    analysis_html += f"{guidance.get('capability_alignment', 'No capability analysis available')}<br></div>"
                    
                    # Display styled analysis content in single gray div
                    st.markdown(f'<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; margin: 15px 0;">{analysis_html}</div>', unsafe_allow_html=True)
                    
                    # Suggestions (in single light yellow box)
                    suggestions = guidance.get("suggestions", [])
                    if suggestions:
                        st.write("**Suggestions:**")
                        suggestions_html = ""
                        for i, suggestion in enumerate(suggestions, 1):
                            suggestions_html += f"<div style='margin: 8px 0;'>{i}. {suggestion}</div>"
                        
                        st.markdown(f'<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ffc107;">{suggestions_html}</div>', unsafe_allow_html=True)
    
    def _display_company_context_inline(self, field_name: str):
        """Display company context inline within the AI guidance expander"""
        st.write("**🔍 Company Context**")
        
        # Get company context
        from app.utils.universal_company_context_extractor import UniversalCompanyContextExtractor
        context_extractor = UniversalCompanyContextExtractor()
        
        # Extract context based on field (simplified for inline display)
        context = context_extractor.extract_field_specific_context(
            field_name, "sustainability", "environmental_impact"  # Default values
        )
        
        # Build context content HTML
        context_html = ""
        
        # Company basics
        basics = context.get("company_basics", {})
        if basics:
            context_html += "<div style='margin: 15px 0;'><strong>Company Information</strong><br><br>"
            for key, value in basics.items():
                context_html += f"• <strong>{key.title()}:</strong> {value}<br>"
            context_html += "</div>"
        
        # Business context
        business = context.get("business_context", {})
        if business:
            context_html += "<div style='margin: 15px 0;'><strong>Business Context</strong><br><br>"
            for key, value in business.items():
                context_html += f"• <strong>{key.replace('_', ' ').title()}:</strong> {value}<br>"
            context_html += "</div>"
        
        # Industry context
        industry = context.get("industry_context", {})
        if industry:
            context_html += "<div style='margin: 15px 0;'><strong>Industry Context</strong><br><br>"
            if "target_industries" in industry:
                context_html += f"• <strong>Target Industries:</strong> {', '.join(industry['target_industries'])}<br>"
            if "target_customers" in industry:
                context_html += f"• <strong>Target Customers:</strong> {', '.join(industry['target_customers'])}<br>"
            context_html += "</div>"
        
        # Display styled context content
        if context_html:
            st.markdown(f'<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; margin: 15px 0;">{context_html}</div>', unsafe_allow_html=True)
    
    def _display_examples_modal(self, field_name: str, main_category: str, subcategory: str):
        """Display examples in a modal popup"""
        if st.session_state.get(f"{field_name}_show_examples_modal", False):
            # Create modal-like container
            with st.container():
                st.markdown("""
                <style>
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    z-index: 1000;
                }
                .modal-content {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1001;
                    max-width: 80%;
                    max-height: 80%;
                    overflow-y: auto;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Modal content
                st.markdown("### 📋 Field Examples")
                examples = self.example_generator.generate_field_examples(
                    field_name, main_category, subcategory
                )
                
                for i, example in enumerate(examples, 1):
                    st.write(f"**Example {i}:**")
                    st.code(example["text"])
                    st.write(f"*Why it's good: {example['explanation']}*")
                    st.write("---")
                
                # Close button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("Close", key=f"close_examples_{field_name}"):
                        st.session_state[f"{field_name}_show_examples_modal"] = False
                        st.rerun()
    
    def _display_company_context_modal(self, field_name: str, main_category: str, subcategory: str):
        """Display company context in a modal popup"""
        if st.session_state.get(f"{field_name}_show_context_modal", False):
            # Create modal-like container
            with st.container():
                # Modal content
                st.markdown("### 🔍 Company Context")
                context = self.context_extractor.extract_field_specific_context(
                    field_name, main_category, subcategory
                )
                
                # Company basics
                basics = context.get("company_basics", {})
                if basics:
                    st.write("**Company Information:**")
                    for key, value in basics.items():
                        st.write(f"• **{key.title()}:** {value}")
                
                # Business context
                business = context.get("business_context", {})
                if business:
                    st.write("**Business Context:**")
                    for key, value in business.items():
                        st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
                
                # Industry context
                industry = context.get("industry_context", {})
                if industry:
                    st.write("**Industry Context:**")
                    if "target_industries" in industry:
                        st.write(f"• **Target Industries:** {', '.join(industry['target_industries'])}")
                    if "target_customers" in industry:
                        st.write(f"• **Target Customers:** {', '.join(industry['target_customers'])}")
                
                # Close button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("Close", key=f"close_context_{field_name}"):
                        st.session_state[f"{field_name}_show_context_modal"] = False
                        st.rerun()
