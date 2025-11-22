"""
Persona generation workflow: Gemini is now used for both website content extraction and industry context. Playwright-based scraping is fully removed.
"""
import asyncio
import json
import logging
import os
import time
import re
import subprocess
from typing import Optional, Dict, Any

from app.ai.workflow_orchestrator import run_value_alignment_workflow
from app.database import fetch_all_value_components, save_persona
import app.utils as utils
from app.ai.prompts import (
    generate_company_summary_prompt,
)
from app.ai.gemini_prompts import industry_context_summary_prompt, website_content_extraction_prompt
from app.ai.gemini_client import gemini_client, get_grounded_company_summary

# Configure logging
ai_logger = logging.getLogger("ai_persona")







def clean_and_parse_json(text: str, pid: int = 0) -> dict:
    """
    Cleans and parses a JSON string, with multiple fallback strategies.
    This version is more robust against markdown and partial responses.
    """
    if not text or not isinstance(text, str):
        return {"error": "Invalid input: not a string or empty", "details": str(text)}

    ai_logger.info(f"[PID {pid}] Raw AI response text before cleaning:\n---\n{text}\n---")

    # Strategy 1: Look for a JSON block inside markdown fences (```json ... ```)
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
        ai_logger.info(f"[PID {pid}] Extracted JSON from markdown block.")
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            ai_logger.warning(f"[PID {pid}] Failed to parse JSON from markdown block: {e}. Falling back.")
            text = json_str 
    
    # Strategy 2: Try to parse the whole string directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        ai_logger.warning(f"[PID {pid}] Direct JSON parsing failed. Attempting to find JSON object within the text.")

    # Strategy 3: Find the first '{' and the last '}' as a fallback
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text[start_index : end_index + 1]
            ai_logger.info(f"[PID {pid}] Extracted and Cleaned JSON via find/rfind.")
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        ai_logger.error(f"[PID {pid}] Final JSON decode error after all cleaning attempts: {e}")
        return {"error": "Failed to parse or repair JSON from AI response", "details": str(e)}

    return {"error": "Could not find a valid JSON object in the AI response."}


async def build_buyer_persona(website: str, selected_industry: Optional[str] = None, pid: int = 0, 
                             progress_tracker = None, verified_company_name: Optional[str] = None):
    """
    Build buyer persona using either enhanced dual-model approach or legacy single-model approach.
    
    Args:
        website: Target website URL
        selected_industry: Industry classification
        pid: Process ID for logging
        progress_tracker: Progress tracking object
        verified_company_name: User-verified company name (optional)
    """
    ai_logger.info(f"[PID {pid}] [build_buyer_persona] Called with website: {website}")
    if verified_company_name:
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Using verified company: {verified_company_name}")
    
    # Check for demo mode first
    if website.startswith("demo://"):
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] DEMO MODE DETECTED: {website}")
        # Demo mode now handled by new dynamic demo system
        # Extract demo customer ID and use regular persona generation
        demo_customer_id = website.replace("demo://", "")
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Demo customer ID: {demo_customer_id}")
        # Continue with regular persona generation for demo customers
    
    # Check if enhanced persona generation is enabled
    from app.config import ENABLE_DUAL_MODEL_PERSONA
    
    if ENABLE_DUAL_MODEL_PERSONA:
        # Use enhanced dual-model persona generation
        from app.ai.enhanced_persona_generator import enhanced_persona_generator
        # Ensure selected_industry is a string (not None) for type compatibility
        industry_str = selected_industry if selected_industry is not None else ""
        return await enhanced_persona_generator.generate_enhanced_persona(
            website, industry_str, pid, progress_tracker, verified_company_name=verified_company_name
        )
    else:
        # Use legacy single-model approach
        return await _build_legacy_persona(website, selected_industry, pid, progress_tracker)

# Demo persona functionality removed - using new dynamic demo system

async def _build_legacy_persona(website: str, selected_industry: Optional[str] = None, pid: int = 0, progress_tracker = None):
    start_time = time.time()
    ai_logger.info(f"--- [PID {pid}] [build_buyer_persona] NEW REQUEST START for: {website} ---")

    try:
        # Step 1: Enhanced deep website analysis
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 1/6: Enhanced deep website analysis START")
        if progress_tracker:
            progress_tracker.start_step(0)
        
        # Use enhanced website analyzer for comprehensive analysis
        from app.ai.enhanced_website_analyzer import enhanced_website_analyzer
        
        industry = selected_industry.strip().lower() if selected_industry else 'unknown'
        
        # Perform deep website analysis
        deep_analysis = await enhanced_website_analyzer.analyze_website_deep(website, industry)
        
        # Update progress periodically during long operations
        if progress_tracker:
            from app.utils.spinner.persona_generation_spinner import update_persona_progress
            update_persona_progress(progress_tracker)
            
            # Add a small delay to show the progress update
            await asyncio.sleep(0.1)
        
        if "error" in deep_analysis:
            ai_logger.error(f"[PID {pid}] Enhanced website analysis failed: {deep_analysis['error']}")
            return {"error": f"Enhanced website analysis failed: {deep_analysis['error']}"}
        
        # Extract key components from deep analysis
        website_content = deep_analysis.get("website_content", "")
        business_analysis = deep_analysis.get("business_analysis", {})
        customer_insights = deep_analysis.get("customer_insights", {})
        competitive_analysis = deep_analysis.get("competitive_analysis", {})
        pain_points_analysis = deep_analysis.get("pain_points_analysis", {})
        persona_insights = deep_analysis.get("persona_insights", {})
        
        # Extract company name from business analysis if available
        extracted_company_name = None
        if business_analysis.get("company_info", {}).get("name"):
            extracted_company_name = business_analysis["company_info"]["name"]
        
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 1/6: Enhanced deep website analysis END")

        # Step 2: Industry Context & Market Intelligence
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 2/6: Industry Context & Market Intelligence START")
        if progress_tracker:
            progress_tracker.start_step(1)
        
        # --- Enhanced Industry Context with Market Intelligence ---
        company_name = extracted_company_name or "Unknown Company"
        
        # Get comprehensive market intelligence
        from app.ai.market_intelligence import market_intelligence_service
        from app.ai.enhanced_prompts import enhanced_prompt_builder
        
        # Detect NACE code for industry
        nace_result = enhanced_prompt_builder.nace_system.detect_industry_nace(industry)
        nace_code = nace_result.get("nace_code")
        
        # Update progress for market intelligence gathering
        if progress_tracker:
            update_persona_progress(progress_tracker)
        
        # Build enhanced industry context prompt with market intelligence
        industry_context_prompt = await enhanced_prompt_builder.build_enhanced_persona_prompt(
            website=website,
            industry_name=industry,
            company_summary=website_content
        )
        
        gemini_result = await gemini_client(industry_context_prompt)
        industry_context = None
        industry_context_industry = None
        industry_context_summary = None
        try:
            # Try to parse as JSON (should have 'industry' and 'summary')
            industry_context = clean_and_parse_json(gemini_result)
            industry_context_industry = industry_context.get("industry")
            industry_context_summary = industry_context.get("summary")
        except Exception as e:
            ai_logger.warning(f"[PID {pid}] Failed to parse industry context as JSON: {e}")
        if not industry_context_summary:
            # Fallback to previous summary-only logic
            industry_context_summary = gemini_result.strip() if isinstance(gemini_result, str) else str(gemini_result)
        # This prompt is for the company summary (Mistral/local)
        summary_prompt = generate_company_summary_prompt(website_content)
        summary = await gemini_client(summary_prompt)
        if not summary or "error" in summary:
            return {"error": "Failed to generate company summary from website content."}
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 2/6: Industry Context & Market Intelligence END")

        # Step 3: Value Alignment Analysis
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 3/6: Value Alignment Analysis START")
        if progress_tracker:
            progress_tracker.start_step(2)
        our_value_components = fetch_all_value_components()
        value_alignment_result = await run_value_alignment_workflow(summary, our_value_components)
        
        # Update progress for value alignment
        if progress_tracker:
            update_persona_progress(progress_tracker)
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 3/6: Value Alignment Analysis END")

        # Step 4: AI Persona Generation
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 4/6: AI Persona Generation START")
        if progress_tracker:
            progress_tracker.start_step(3)
        playbook = value_alignment_result if isinstance(value_alignment_result, dict) else {}
        if "error" in playbook:
            ai_logger.error(f"An error occurred in the value alignment workflow: {playbook['error']}")

        summary_trunc = utils.safe_truncate_text(summary, 1500)
        playbook_str = json.dumps(playbook, indent=2)
        playbook_trunc = utils.safe_truncate_text(playbook_str, 2000)

        json_structure_template = (
            '{\n'
            '  "company": {"name": "string", "year_established": "integer", "headquarters_location": "string", "website": "URL"},\n'
            '  "product_range": ["string (bullet points of key products/services)"],\n'
            '  "services": ["string (bullet points of key services)"],\n'
            '  "pain_points": ["string (bullet points of key challenges)"],\n'
            '  "goals": ["string (bullet points of key objectives)"],\n'
            '  "value_drivers": ["string (bullet points of what drives their decisions)"],\n'
            '  "value_signals": ["string (bullet points of how they evaluate solutions)"],\n'
            '  "likely_objections": ["string (bullet points of potential concerns)"],\n'
            '  "chain_of_thought": "string (brief explanation of reasoning)"\n'
            '}'
        )

        # Get market intelligence data for final persona generation
        market_data = await market_intelligence_service.get_market_data_for_prompts(
            industry_name=industry,
            company_summary=website_content,
            nace_code=nace_code
        )
        
        # Also get full market intelligence for display
        full_market_intelligence = await market_intelligence_service.get_comprehensive_market_intelligence(
            industry_name=industry,
            company_summary=website_content,
            nace_code=nace_code
        )
        
        # Build enhanced persona prompt with deep analysis insights
        persona_prompt = (
            f"Based on the following comprehensive analysis, generate a highly targeted buyer persona as a JSON object.\n\n"
            f"**REQUIRED JSON STRUCTURE:**\n{json_structure_template}\n\n"
            f"**DEEP WEBSITE ANALYSIS:**\n"
            f"Business Model: {json.dumps(business_analysis, indent=2)}\n"
            f"Customer Insights: {json.dumps(customer_insights, indent=2)}\n"
            f"Competitive Analysis: {json.dumps(competitive_analysis, indent=2)}\n"
            f"Pain Points Analysis: {json.dumps(pain_points_analysis, indent=2)}\n"
            f"Targeted Persona Insights: {json.dumps(persona_insights, indent=2)}\n\n"
            f"**STRATEGIC VALUE ALIGNMENT (Our solution vs. their needs):**\n"
            f"{playbook_trunc}\n\n"
            f"**COMPANY SUMMARY (from website):**\n"
            f"{summary_trunc}\n\n"
            f"**MARKET INTELLIGENCE (AI-Generated):**\n"
            f"{market_data}\n\n"
            f"**ENHANCED INSTRUCTIONS:**\n"
            f"1. Use the deep analysis insights to create HIGHLY SPECIFIC and TARGETED persona data.\n"
            f"2. Base pain_points, goals, and value_drivers on the actual business analysis and customer insights.\n"
            f"3. Use the competitive analysis to understand their market position and decision factors.\n"
            f"4. Leverage the pain points analysis to identify specific challenges they face.\n"
            f"5. Incorporate the targeted persona insights for maximum relevance.\n"
            f"6. Make ALL insights specific to THIS customer, not generic industry insights.\n"
            f"7. Output ONLY the JSON object, with no other text or markdown.\n"
            f"8. Prioritize specificity and relevance over generic industry knowledge.\n"
            f"9. **CRITICAL: Provide 3-8 focused bullet points for each field, not paragraphs.**\n"
            f"10. **Use bullet point format for better readability and actionability.**"
        )

        # Step 5: Data Integration
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 5/6: Data Integration START")
        if progress_tracker:
            progress_tracker.start_step(4)
        
        # Final AI call to generate persona
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Final AI call START")
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] FINAL PERSONA PROMPT (length: {len(persona_prompt)} chars)")
        
        # Update progress before final AI call
        if progress_tracker:
            update_persona_progress(progress_tracker)
        
        final_persona_json = await _execute_final_persona_generation(persona_prompt, pid=pid)
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Final AI call END.")
        
        # Step 6: Final Processing
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Step 6/6: Final Processing START")
        if progress_tracker:
            progress_tracker.start_step(5)

        if not final_persona_json or "error" in final_persona_json:
            error_message = final_persona_json.get('details', 'AI did not return a valid persona string.') if final_persona_json else 'AI returned no response.'
            ai_logger.error(f"AI did not return a valid persona string for the final persona.")
            return {"error": f"Error generating persona: {error_message}"}

        final_persona_json["advanced_value_alignment"] = playbook
        # --- Insert Gemini industry context summary and industry field ---
        final_persona_json["industry_context"] = {"industry": industry_context_industry, "summary": industry_context_summary}
        final_persona_json["industry"] = industry_context_industry
        # --- Insert market intelligence data ---
        final_persona_json["market_intelligence"] = market_data
        final_persona_json["full_market_intelligence"] = full_market_intelligence.get("market_intelligence", {}) if full_market_intelligence.get("success") else {}
        # --- Insert enhanced analysis data ---
        final_persona_json["enhanced_analysis"] = {
            "business_analysis": business_analysis,
            "customer_insights": customer_insights,
            "competitive_analysis": competitive_analysis,
            "pain_points_analysis": pain_points_analysis,
            "persona_insights": persona_insights
        }

        # --- Ensure Website URL and Company Name Integrity ---
        if "company" not in final_persona_json:
            final_persona_json["company"] = {} # Ensure the company dict exists
        final_persona_json["company"]["website"] = website
        if extracted_company_name and extracted_company_name.lower() != "unknown":
            ai_logger.info(f"[PID {pid}] [build_buyer_persona] Overwriting AI-generated company name with extracted: {extracted_company_name}")
            final_persona_json["company"]["name"] = extracted_company_name
        else:
            ai_logger.info(f"[PID {pid}] [build_buyer_persona] No reliable company name extracted; using AI-generated or fallback.")
        ai_logger.info(f"[PID {pid}] [build_buyer_persona] Overwriting AI-generated website with user-provided URL: {website}")
        
        # Update progress for final processing
        if progress_tracker:
            update_persona_progress(progress_tracker)

        total_time = time.time() - start_time
        ai_logger.info(f"--- [PID {pid}] [build_buyer_persona] REQUEST END. Total time: {total_time:.2f}s ---")
        return final_persona_json

    except Exception as e:
        ai_logger.error(f"[PID {pid}] [build_buyer_persona] An unexpected error occurred: {e}", exc_info=True)
        return {"error": "An unexpected error occurred during persona generation."}


async def _execute_final_persona_generation(prompt: str, pid: int, retries: int = 2) -> dict:
    """Wrapper to make the final AI call awaitable and include retries. Now uses Gemini for persona generation with deterministic configuration."""
    for attempt in range(retries):
        try:
            response_text = await gemini_client(prompt)
            if response_text:
                parsed_json = clean_and_parse_json(response_text, pid)
                if parsed_json and 'error' not in parsed_json:
                    # Ensure chain_of_thought is present
                    if "chain_of_thought" not in parsed_json or not parsed_json["chain_of_thought"]:
                        parsed_json["chain_of_thought"] = "No explicit reasoning provided. This field will explain the AI's step-by-step logic for the persona if available."
                    return parsed_json
            ai_logger.warning(f"[PID {pid}] [Final Persona Gen] Attempt {attempt + 1}/{retries} returned an empty or invalid response.")
        except Exception as e:
            ai_logger.error(f"[PID {pid}] [Final Persona Gen] An exception occurred during attempt {attempt + 1}/{retries}: {e}", exc_info=True)
        if attempt < retries - 1:
            ai_logger.info(f"[PID {pid}] [Final Persona Gen] Retrying in {attempt + 1} second(s)...")
            await asyncio.sleep(attempt + 1)
    ai_logger.error(f"[PID {pid}] [Final Persona Gen] Failed to get valid response after {retries} attempts.")
    return {"error": f"Failed to get valid JSON response after {retries} attempts."}


# =============================================================================
# BACKGROUND TASK RUNNER
# =============================================================================

async def run_persona_generation_background(task_id: str, website: str, user_id: str, 
                                          verified_company_name: Optional[str] = None,
                                          verified_industry: Optional[str] = None):
    """Run persona generation as background task with progress updates.
    
    Args:
        task_id: Background task ID
        website: Target website URL
        user_id: User ID
        verified_company_name: User-verified company name (optional)
        verified_industry: User-selected industry (optional)
    """
    from app.database import update_background_task, get_background_task
    from app.utils.spinner.persona_generation_spinner import PersonaGenerationProgress
    
    try:
        ai_logger.info(f"[Background Task {task_id}] Starting persona generation for {website}")
        if verified_company_name:
            ai_logger.info(f"[Background Task {task_id}] Using verified company: {verified_company_name}")
        
        # Create progress tracker for background task
        progress = PersonaGenerationProgress()
        
        # Update task status to running
        await update_background_task(task_id, 
            status="running",
            progress_percent=0,
            current_step="Initializing...",
            step_description="Starting persona generation process"
        )
        
        # Run the actual persona generation with real progress tracking
        ai_logger.info(f"[Background Task {task_id}] Running build_buyer_persona...")
        
        # Create a custom progress tracker that updates the background task
        class BackgroundTaskProgressTracker:
            def __init__(self, task_id, total_steps=8):
                self.task_id = task_id
                self.total_steps = total_steps
                self.current_step = 0
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
            
            async def start_step(self, step_index: int):
                """Start a new step and update background task."""
                try:
                    self.current_step = step_index
                    # Calculate progress as (step_index + 1) / total_steps to show meaningful progress
                    progress_percent = int(((step_index + 1) / self.total_steps) * 100)
                    
                    ai_logger.info(f"[Background Task {self.task_id}] Updating progress to {progress_percent}% for step {step_index + 1}")
                    
                    # Add timeout to prevent hanging (shorter for demo mode)
                    import asyncio
                    try:
                        await asyncio.wait_for(
                            update_background_task(
                                self.task_id,
                                progress_percent=progress_percent,
                                current_step=self.step_names[step_index],
                                step_description=self.step_descriptions[step_index]
                            ),
                            timeout=1.5  # 1.5 second timeout (reduced from 2)
                        )
                        
                        # CRITICAL: Also update session state cache for sidebar (if Streamlit is available)
                        # This ensures sidebar can show progress even in async contexts
                        try:
                            import streamlit as st
                            if hasattr(st, 'session_state'):
                                st.session_state[f"cached_progress_{self.task_id}"] = {
                                    "progress_percent": progress_percent,
                                    "current_step": self.step_names[step_index]
                                }
                        except Exception:
                            # Streamlit not available or not in Streamlit context - that's OK
                            pass
                        
                        ai_logger.info(f"[Background Task {self.task_id}] Step {step_index + 1}/{self.total_steps}: {self.step_names[step_index]} - Progress: {progress_percent}%")
                    except asyncio.TimeoutError:
                        ai_logger.warning(f"[Background Task {self.task_id}] Timeout updating progress for step {step_index + 1}, continuing...")
                    except Exception as e:
                        ai_logger.warning(f"[Background Task {self.task_id}] Error updating progress for step {step_index + 1}: {e}, continuing...")
                    
                except Exception as e:
                    ai_logger.error(f"[Background Task {self.task_id}] Error updating progress for step {step_index + 1}: {e}")
                    # Continue even if progress update fails
        
        # Use the custom progress tracker
        background_progress = BackgroundTaskProgressTracker(task_id)
        persona = await build_buyer_persona(
            website, 
            selected_industry=verified_industry,
            progress_tracker=background_progress,
            verified_company_name=verified_company_name
        )
        
        if persona and "error" not in persona:
            # Save the persona to database with user_id
            # Type checker note: save_persona is async and returns dict | None
            saved_persona: Optional[dict] = await save_persona(persona, website, user_id)  # type: ignore[misc]
            
            if saved_persona:
                # saved_persona is now the persona dict with ID, not just True
                # Ensure we have the persona ID for the result
                persona_id = saved_persona.get("id") or saved_persona.get("company", {}).get("id")
                if not persona_id:
                    # Fallback: try to extract from original persona
                    # Ensure persona is a dict before calling .get()
                    if isinstance(persona, dict):
                        persona_dict: Dict[str, Any] = persona  # Type narrowing for type checker
                        persona_id = persona_dict.get("id") or persona_dict.get("company", {}).get("id")
                        if persona_id:
                            saved_persona["id"] = persona_id
                
                # Update task with completed status and result (with timeout)
                try:
                    await asyncio.wait_for(
                        update_background_task(task_id,
                            status="completed",
                            progress_percent=100,
                            current_step="✅ Completed",
                            step_description="Persona generation completed successfully",
                            result_persona=saved_persona
                        ),
                        timeout=3.0
                    )
                    ai_logger.info(f"[Background Task {task_id}] Persona generation completed successfully with ID {persona_id}")
                except asyncio.TimeoutError:
                    ai_logger.warning(f"[Background Task {task_id}] Timeout updating completion status, but persona was generated successfully")
                except Exception as e:
                    ai_logger.warning(f"[Background Task {task_id}] Error updating completion status: {e}, but persona was generated successfully")
            else:
                # Failed to save persona (saved_persona is None)
                try:
                    await asyncio.wait_for(
                        update_background_task(task_id,
                            status="failed",
                            error_message="Failed to save persona to database"
                        ),
                        timeout=3.0
                    )
                except (asyncio.TimeoutError, Exception) as e:
                    ai_logger.warning(f"[Background Task {task_id}] Error updating failure status: {e}")
                ai_logger.error(f"[Background Task {task_id}] Failed to save persona to database")
        else:
            # Persona generation failed
            error_msg = persona.get("error", "Unknown error during persona generation") if persona else "No persona generated"
            try:
                await asyncio.wait_for(
                    update_background_task(task_id,
                        status="failed",
                        error_message=error_msg
                    ),
                    timeout=3.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                ai_logger.warning(f"[Background Task {task_id}] Error updating failure status: {e}")
            ai_logger.error(f"[Background Task {task_id}] Persona generation failed: {error_msg}")
            
    except Exception as e:
        ai_logger.error(f"[Background Task {task_id}] Exception during background persona generation: {e}", exc_info=True)
        await update_background_task(task_id,
            status="failed",
            error_message=f"Exception: {str(e)}"
        )