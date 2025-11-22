"""
Persona Generation Spinner
Specialized spinner for persona generation with real-time step tracking using Streamlit's native components.
"""

import streamlit as st
import time
from contextlib import contextmanager
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PersonaGenerationProgress:
    """Tracks progress through persona generation steps."""
    
    def __init__(self):
        self.current_step = 0
        self.total_steps = 8
        self.step_names = [
            "🎯 Pre-analysis Relevance Validation",
            "🔍 Dual-Model Website Analysis",
            "✅ Enhanced Cross-Model Validation",
            "🏭 Enhanced Market Intelligence",
            "🎯 Dual-Model Value Alignment",
            "🎨 Creative Persona Elements",
            "🧠 Final Persona Synthesis",
            "🔍 Quality Assurance & Final Check"
        ]
        self.step_descriptions = [
            "Validating website relevance to our business using Sonar...",
            "Analyzing website with Gemini and ChatGPT in parallel...",
            "Validating and synthesizing results from both AI models with Sonar...",
            "Gathering market intelligence with Sonar validation...",
            "Creating value alignment with Sonar validation...",
            "Generating innovative persona elements with Sonar validation...",
            "Synthesizing final persona with Sonar validation...",
            "Performing quality assurance and final Sonar validation..."
        ]
        self.start_time = time.time()
        self.step_start_times = {}
    
    def start_step(self, step_index: int):
        """Start a new step."""
        self.current_step = step_index
        self.step_start_times[step_index] = time.time()
        logger.info(f"Starting persona generation step {step_index + 1}/{self.total_steps}: {self.step_names[step_index]}")
        
        # Calculate progress percentage
        progress_percent = (step_index / self.total_steps)
        
        # Update session state for live UI updates
        st.session_state.persona_progress = {
            'current_step': step_index,
            'progress_percent': int(progress_percent * 100),
            'step_name': self.step_names[step_index],
            'step_description': self.step_descriptions[step_index],
            'elapsed_time': time.time() - self.start_time,
            'step_elapsed_time': 0
        }
        
        # Force re-render of the modal with updated progress
        render_progress_display()
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        elapsed = time.time() - self.start_time
        step_elapsed = 0
        if self.current_step in self.step_start_times:
            step_elapsed = time.time() - self.step_start_times[self.current_step]
        
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "step_name": self.step_names[self.current_step],
            "step_description": self.step_descriptions[self.current_step],
            "progress_percent": int((self.current_step / self.total_steps) * 100),
            "elapsed_time": elapsed,
            "step_elapsed_time": step_elapsed
        }

def render_progress_display():
    """Render a modal popup with blurred background using CSS overlay."""
    
    # Get current progress from session state
    progress_info = st.session_state.get('persona_progress', {
        'current_step': 0,
        'progress_percent': 0,
        'step_name': '🎯 Pre-analysis Relevance Validation',
        'step_description': 'Validating website relevance to our business using Sonar...',
        'elapsed_time': 0,
        'step_elapsed_time': 0
    })
    
    # Format elapsed time
    elapsed_time = float(progress_info.get('elapsed_time', 0))
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)
    time_str = f"{elapsed_minutes}m {elapsed_seconds}s"
    
    # Create step indicators
    step_icons = ["🎯", "🔍", "✅", "🏭", "🎯", "🎨", "🧠", "🔍"]
    current_step = int(progress_info.get('current_step', 0))
    
    # Use CSS-based modal overlay (most reliable approach)
    st.markdown("""
    <style>
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(3px);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .modal-content {
        background: white;
        border-radius: 10px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        max-width: 700px;
        width: 95%;
        text-align: center;
    }
    .step-indicator {
        margin: 0 8px;
        font-size: 24px;
        display: inline-block;
        min-width: 30px;
    }
    .progress-bar {
        background: #f0f0f0;
        border-radius: 5px;
        height: 20px;
        margin: 15px 0;
        overflow: hidden;
    }
    .progress-fill {
        background: linear-gradient(90deg, #3498db, #27ae60);
        height: 100%;
        border-radius: 5px;
        transition: width 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the modal content
    step_indicators = ""
    for i, icon in enumerate(step_icons):
        if i < current_step:
            step_indicators += f'<span class="step-indicator">✅ {icon}</span>'
        elif i == current_step:
            step_indicators += f'<span class="step-indicator">🔄 {icon}</span>'
        else:
            step_indicators += f'<span class="step-indicator">⚪ {icon}</span>'
    
    modal_content = f"""
    <div class="modal-overlay">
        <div class="modal-content">
            <h3>🧠 Generating Buyer Persona</h3>
            <div style="margin: 20px 0; white-space: nowrap; overflow-x: auto; padding: 10px 0;">
                {step_indicators}
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress_info['progress_percent']}%;"></div>
            </div>
            <p><strong>{progress_info['step_name']}</strong></p>
            <p><em>{progress_info['step_description']}</em></p>
            <p style="font-size: 12px; color: #666;">⏱️ Elapsed: {time_str} | Step {current_step + 1} of 8</p>
        </div>
    </div>
    """
    
    st.markdown(modal_content, unsafe_allow_html=True)

@contextmanager
def persona_generation_spinner():
    """
    Enhanced progress tracker for persona generation with real-time step tracking.
    
    Usage:
        with persona_generation_spinner() as progress:
            # Step 0: Pre-analysis Relevance Validation (Sonar)
            progress.start_step(0)
            relevance_result = await self._step_0_relevance_validation(website, pid)
            
            # Step 1: Dual-Model Website Analysis
            progress.start_step(1)
            gemini_analysis, chatgpt_analysis = await self._parallel_website_analysis(website, industry, pid)
            
            # Step 2: Enhanced Cross-Model Validation
            progress.start_step(2)
            validated_analysis = await self._cross_validate_and_synthesize(gemini_analysis, chatgpt_analysis, website, pid)
            
            # Step 3: Enhanced Market Intelligence
            progress.start_step(3)
            enhanced_market_intelligence = await self._generate_enhanced_market_intelligence(website, validated_analysis, industry, pid)
            
            # Step 4: Dual-Model Value Alignment
            progress.start_step(4)
            enhanced_value_alignment = await self._generate_enhanced_value_alignment(validated_analysis, pid)
            
            # Step 5: Creative Persona Elements
            progress.start_step(5)
            creative_elements = await self._generate_creative_persona_elements(validated_analysis, enhanced_market_intelligence, pid)
            
            # Step 6: Final Persona Synthesis
            progress.start_step(6)
            final_persona = await self._synthesize_final_persona(validated_analysis, enhanced_market_intelligence, enhanced_value_alignment, creative_elements, pid)
            
            # Step 7: Quality Assurance & Final Check
            progress.start_step(7)
            enhanced_persona = await self._quality_assurance_and_enhancement(final_persona, validated_analysis, creative_elements, enhanced_value_alignment, enhanced_market_intelligence, pid)
    """
    
    progress = PersonaGenerationProgress()
    
    try:
        # Initialize session state for progress tracking
        if 'persona_progress' not in st.session_state:
            st.session_state.persona_progress = {
                'current_step': 0,
                'progress_percent': 0,
                'step_name': '🎯 Pre-analysis Relevance Validation',
                'step_description': 'Validating website relevance to our business using Sonar...',
                'elapsed_time': 0,
                'step_elapsed_time': 0
            }
        
        # Render the progress display
        render_progress_display()
        
        # Start with step 0
        progress.start_step(0)
        
        # Yield the progress tracker
        yield progress
        
    except Exception as e:
        logger.error(f"Error in persona generation spinner: {e}")
        raise
    finally:
        # Clean up - remove the modal when the context exits
        # The modal will disappear when the page re-renders after persona generation
        pass

def update_persona_progress(progress: PersonaGenerationProgress):
    """
    Update the persona generation progress display.
    This function should be called periodically during persona generation.
    """
    try:
        progress_info = progress.get_progress_info()
        
        # Update session state for live updates
        st.session_state.persona_progress = {
            'current_step': progress_info['current_step'],
            'progress_percent': progress_info['progress_percent'],
            'step_name': progress_info['step_name'],
            'step_description': progress_info['step_description'],
            'elapsed_time': progress_info['elapsed_time'],
            'step_elapsed_time': progress_info['step_elapsed_time']
        }
        
        # Log the progress update for debugging
        logger.info(f"Progress update: Step {progress_info['current_step'] + 1}/{progress_info['total_steps']} - {progress_info['progress_percent']}% - {progress_info['step_name']}")
        
    except Exception as e:
        logger.error(f"Error updating persona progress: {e}")

# Convenience function for quick step updates
def update_step(progress: PersonaGenerationProgress, step_index: int):
    """Quick function to update to a specific step."""
    progress.start_step(step_index) 