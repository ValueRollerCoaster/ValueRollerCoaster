import asyncio
import json
import logging
import os
from typing import Optional

# Setup value alignment logger directly
def setup_value_alignment_logger():
    """Sets up a dedicated logger for the value alignment process."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger('value_alignment')
    logger.setLevel(logging.INFO)
    
    # Prevent logs from propagating to the root logger
    logger.propagate = False
    
    # If handlers are already present, do nothing
    if logger.handlers:
        return logger
        
    # File handler
    log_file = os.path.join(log_dir, 'value_alignment.log')
    handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to the logger
    logger.addHandler(handler)
    
    return logger

value_alignment_logger = setup_value_alignment_logger()
from app.ai.value_alignment import (
    _run_profiler_agent,
    _run_hypothesizer_agent,
    _run_final_aligner_agent
)

# Define the sequence of steps for our value alignment workflow.
# This structure makes it easy to add, remove, or reorder steps.
VALUE_ALIGNMENT_WORKFLOW = [
    {
        "name": "Profiler",
        "agent_function": _run_profiler_agent,
        "inputs": ["company_summary"],
        "output_key": "profiler_analysis"
    },
    {
        "name": "Hypothesizer",
        "agent_function": _run_hypothesizer_agent,
        "inputs": ["profiler_analysis", "our_value_components"],
        "output_key": "hypothesis_analysis"
    },
    {
        "name": "Final Aligner",
        "agent_function": _run_final_aligner_agent,
        "inputs": ["profiler_analysis", "hypothesis_analysis", "company_summary", "our_value_components", "company_profile"],
        "output_key": "final_alignment" # This agent's output contains the matrix
    }
]

class WorkflowExecutor:
    """
    A generic engine to execute a workflow defined as a list of steps.
    It manages the state and data flow between agentic steps.
    """
    def __init__(self, workflow_definition):
        self.workflow = workflow_definition
        self.playbook = {}
        self.reasoning_steps = []

    async def run(self, initial_context: dict):
        """
        Executes the defined workflow step-by-step.
        
        Args:
            initial_context: A dictionary with the initial data needed for the first step.
        
        Returns:
            A comprehensive playbook dictionary containing the outputs of all steps.
        """
        self.playbook = initial_context.copy()
        self.reasoning_steps = []

        for idx, step in enumerate(self.workflow):
            step_name = step["name"]
            agent_func = step["agent_function"]
            input_keys = step["inputs"]
            output_key = step["output_key"]

            # Prepare the arguments for the agent function
            try:
                kwargs = {key: self.playbook[key] for key in input_keys}
            except KeyError as e:
                error_msg = f"Workflow failed at step '{step_name}'. Missing input: {e}"
                value_alignment_logger.error(error_msg)
                self.playbook['error'] = error_msg
                return self.playbook

            # Execute the agent
            value_alignment_logger.info(f"Executing workflow step: {step_name}")
            try:
                result = await agent_func(**kwargs)
            except Exception as e:
                error_msg = f"Workflow step '{step_name}' raised an exception: {str(e)}"
                value_alignment_logger.error(error_msg, exc_info=True)
                self.playbook['error'] = error_msg
                # Ensure alignment_matrix exists even on error
                if output_key == "final_alignment":
                    self.playbook[output_key] = {"alignment_matrix": [], "error": error_msg}
                self.playbook["reasoning_steps"] = self.reasoning_steps
                return self.playbook

            # Store the result and check for errors
            if result is None:
                error_msg = f"Workflow step '{step_name}' returned no output."
                value_alignment_logger.error(error_msg)
                self.playbook['error'] = error_msg
                # Ensure alignment_matrix exists even on error
                if output_key == "final_alignment":
                    self.playbook[output_key] = {"alignment_matrix": [], "error": error_msg}
                self.playbook["reasoning_steps"] = self.reasoning_steps
                return self.playbook
            
            # Check if result contains an error (from agent functions)
            if isinstance(result, dict) and "error" in result:
                error_msg = result.get('error', f"Workflow step '{step_name}' returned an error.")
                value_alignment_logger.error(error_msg)
                self.playbook['error'] = error_msg
                # Preserve the result but ensure alignment_matrix exists
                if output_key == "final_alignment":
                    if "alignment_matrix" not in result:
                        result["alignment_matrix"] = []
                self.playbook[output_key] = result
                self.playbook["reasoning_steps"] = self.reasoning_steps
                return self.playbook
                
            self.playbook[output_key] = result
            # Try to extract a reasoning string for this step
            reasoning = None
            if isinstance(result, dict):
                # Try common keys for reasoning
                for key in ["overall_sentiment", "hypothesis_rationale"]:
                    if key in result:
                        reasoning = result[key]
                        break
            # Special handling for Final Aligner (last step)
            if idx == len(self.workflow) - 1 and output_key == "final_alignment":
                alignment_matrix = result.get('alignment_matrix', []) if isinstance(result, dict) else []
                if alignment_matrix:
                    summary_lines = []
                    for item in alignment_matrix:
                        summary_lines.append(
                            f"- **Customer Need:** {item.get('customer_need', '')}\n"
                            f"  - **Our Solution:** {item.get('our_component', '')}\n"
                            f"  - **Rationale:** {item.get('rationale', '')}\n"
                            f"  - **Strength:** {item.get('strength_score', '')}, Confidence: {item.get('confidence_score', '')}%\n"
                            f"  - **Evidence:** {item.get('evidence_source', '')}\n"
                        )
                    reasoning = (
                        "The final Value Alignment Matrix was generated, matching the following customer needs to our solutions:\n\n"
                        + "\n".join(summary_lines)
                    )
                else:
                    reasoning = "No alignments were found for this company."
            if not reasoning:
                # Fallback: use stringified result or a default message
                reasoning = str(result) if result else f"No reasoning for {step_name}"
            self.reasoning_steps.append({
                "step": len(self.reasoning_steps) + 1,
                "title": step_name,
                "content": reasoning
            })
        value_alignment_logger.info("Workflow execution completed successfully.")
        self.playbook["reasoning_steps"] = self.reasoning_steps
        return self.playbook

async def run_value_alignment_workflow(company_summary: str, our_value_components: dict, company_profile: Optional[dict] = None) -> dict:
    """
    A convenience function to run the entire value alignment workflow.
    
    Args:
        company_summary: Summary of the prospect company
        our_value_components: Our company's value components
        company_profile: Our company profile (optional, will be loaded if not provided)
    """
    # Load company_profile if not provided
    if company_profile is None:
        from app.core.company_context_manager import CompanyContextManager
        company_context = CompanyContextManager()
        company_profile = company_context.get_company_profile()
        if not isinstance(company_profile, dict):
            company_profile = {}
    
    executor = WorkflowExecutor(VALUE_ALIGNMENT_WORKFLOW)
    initial_data = {
        "company_summary": company_summary,
        "our_value_components": our_value_components,
        "company_profile": company_profile
    }
    final_playbook = await executor.run(initial_data)
    
    # Restructure the final output for cleaner integration
    value_alignment_logger.info(f"[DEBUG] Final playbook keys before restructuring: {list(final_playbook.keys())}")
    
    if 'error' not in final_playbook:
        final_alignment = final_playbook.pop('final_alignment', {})
        value_alignment_logger.info(f"[DEBUG] Extracted final_alignment type: {type(final_alignment)}")
        if isinstance(final_alignment, dict):
            value_alignment_logger.info(f"[DEBUG] final_alignment keys: {list(final_alignment.keys())}")
            alignment_matrix = final_alignment.get('alignment_matrix', [])
            if alignment_matrix:
                value_alignment_logger.info(f"[DEBUG] alignment_matrix type: {type(alignment_matrix)}, length: {len(alignment_matrix) if isinstance(alignment_matrix, list) else 'N/A'}")
            else:
                value_alignment_logger.warning(f"[DEBUG] alignment_matrix is empty or missing. final_alignment content: {json.dumps(final_alignment, indent=2)[:500]}")
        else:
            value_alignment_logger.warning(f"[DEBUG] final_alignment is not a dict: {type(final_alignment)}, value: {str(final_alignment)[:200]}")
            alignment_matrix = []
        final_playbook['alignment_matrix'] = alignment_matrix
        value_alignment_logger.info(f"Value alignment workflow completed with {len(alignment_matrix)} alignments")
    else:
        # Even on error, ensure alignment_matrix exists
        value_alignment_logger.error(f"[DEBUG] Workflow had error: {final_playbook.get('error')}")
        if 'alignment_matrix' not in final_playbook:
            final_alignment = final_playbook.get('final_alignment', {})
            value_alignment_logger.info(f"[DEBUG] Extracting alignment_matrix from final_alignment on error path")
            value_alignment_logger.info(f"[DEBUG] final_alignment type: {type(final_alignment)}, keys: {list(final_alignment.keys()) if isinstance(final_alignment, dict) else 'N/A'}")
            alignment_matrix = final_alignment.get('alignment_matrix', []) if isinstance(final_alignment, dict) else []
            final_playbook['alignment_matrix'] = alignment_matrix
        value_alignment_logger.error(f"Value alignment workflow completed with error: {final_playbook.get('error')}. Alignment matrix has {len(final_playbook.get('alignment_matrix', []))} items")
    
    value_alignment_logger.info(f"[DEBUG] Final playbook keys after restructuring: {list(final_playbook.keys())}")
    value_alignment_logger.info(f"[DEBUG] Final alignment_matrix length: {len(final_playbook.get('alignment_matrix', []))}")
    
    return final_playbook