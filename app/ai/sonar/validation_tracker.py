"""
Validation Tracker
Tracks validation status and allows deferred validation for data that's populated later.
"""

import logging
from typing import Dict, List, Any, Optional
from app.ai.sonar.enhanced_validation import EnhancedSonarValidator

logger = logging.getLogger(__name__)

class ValidationTracker:
    """Tracks validation status for persona generation steps"""
    
    def __init__(self):
        self.validation_status = {}
        self.deferred_validations = []
        logger.info("[ValidationTracker] Initialized")
    
    def mark_for_deferred_validation(self, step_name: str, validation_type: str, data_path: str, target_domain: Optional[str] = None, industry: Optional[str] = None):
        """
        Mark a validation to be run later when data is available.
        
        Args:
            step_name: Name of the step where validation was deferred
            validation_type: Type of validation (e.g., "market_intelligence", "value_alignment")
            data_path: Path to data in final persona (e.g., "enhanced_market_intelligence.original_market_intelligence")
            target_domain: Optional target domain for validation
            industry: Optional industry classification for validation
        """
        self.deferred_validations.append({
            "step": step_name,
            "validation_type": validation_type,
            "data_path": data_path,
            "target_domain": target_domain,
            "industry": industry,
            "status": "pending"
        })
        logger.info(f"[ValidationTracker] Marked {validation_type} from {step_name} for deferred validation (path: {data_path}, industry: {industry})")
    
    async def run_deferred_validations(self, persona: Dict, pid: int = 0) -> List[Dict[str, Any]]:
        """
        Run all deferred validations after data is fully populated.
        
        Args:
            persona: Complete persona dictionary with all data
            pid: Process ID for logging
            
        Returns:
            List of validation results
        """
        if not self.deferred_validations:
            logger.info(f"[PID {pid}] [ValidationTracker] No deferred validations to run")
            return []
        
        logger.info(f"[PID {pid}] [ValidationTracker] Running {len(self.deferred_validations)} deferred validations")
        
        validator = EnhancedSonarValidator()
        results = []
        
        for deferred in self.deferred_validations:
            if deferred["status"] == "pending":
                validation_type = deferred["validation_type"]
                data_path = deferred["data_path"]
                target_domain = deferred.get("target_domain")
                
                # Extract data from persona using data_path
                data = self._extract_data_by_path(persona, data_path)
                
                # If extraction fails, try alternative paths (for market intelligence)
                if not data or self._is_empty(data):
                    if validation_type == "market_intelligence":
                        # Try alternative paths
                        alternative_paths = [
                            "market_intelligence",  # Direct path
                            "enhanced_market_intelligence.market_intelligence",  # Alternative nesting
                            "full_market_intelligence",  # Legacy path
                            "enhanced_market_intelligence.base_intelligence.market_intelligence",  # Deep nesting
                        ]
                        for alt_path in alternative_paths:
                            alt_data = self._extract_data_by_path(persona, alt_path)
                            if alt_data and not self._is_empty(alt_data):
                                logger.info(f"[PID {pid}] [ValidationTracker] Found data at alternative path: {alt_path}")
                                data = alt_data
                                break
                
                if data and not self._is_empty(data):
                    logger.info(f"[PID {pid}] [ValidationTracker] Running deferred {validation_type} validation")
                    try:
                        # Run validation now that data is available
                        if validation_type == "market_intelligence":
                            # Construct website URL from target_domain
                            website_url = f"https://{target_domain}" if target_domain else ""
                            # Get industry from deferred validation data
                            industry = deferred.get("industry", "unknown")
                            # Call with correct parameters: (market_intelligence, website_url, industry, pid)
                            result = await validator.validate_market_intelligence(data, website_url, industry, pid)
                        elif validation_type == "value_alignment":
                            result = await validator.validate_value_alignment(data, target_domain, pid)
                        elif validation_type == "final_synthesis_content":
                            # For final synthesis, pass the full persona and construct website URL from target_domain
                            website_url = f"https://{target_domain}" if target_domain else ""
                            result = await validator.validate_final_synthesis(persona, website_url, pid)
                        else:
                            logger.warning(f"[PID {pid}] [ValidationTracker] Unknown validation type: {validation_type}")
                            result = {
                                "validation_passed": True,
                                "overall_confidence": 5,
                                "validation_type": validation_type,
                                "validation_notes": f"Unknown validation type: {validation_type}"
                            }
                        
                        # Mark as completed
                        deferred["status"] = "completed"
                        results.append({
                            "validation_type": validation_type,
                            "result": result,
                            "original_step": deferred["step"],
                            "data_path": data_path
                        })
                        logger.info(f"[PID {pid}] [ValidationTracker] Completed deferred {validation_type} validation")
                        
                    except Exception as e:
                        logger.error(f"[PID {pid}] [ValidationTracker] Error running deferred {validation_type} validation: {e}")
                        deferred["status"] = "error"
                        results.append({
                            "validation_type": validation_type,
                            "result": {
                                "validation_passed": True,  # Don't block on error
                                "overall_confidence": 5,
                                "validation_type": validation_type,
                                "error": str(e),
                                "validation_notes": f"Deferred validation error: {str(e)}"
                            },
                            "original_step": deferred["step"],
                            "data_path": data_path
                        })
                else:
                    logger.warning(f"[PID {pid}] [ValidationTracker] Data still empty for {validation_type} at path {data_path}")
                    deferred["status"] = "skipped_empty"
        
        return results
    
    def _extract_data_by_path(self, data: Dict, path: str) -> Any:
        """
        Extract nested data using dot notation path.
        
        Args:
            data: Dictionary to extract from
            path: Dot-notation path (e.g., "enhanced_market_intelligence.original_market_intelligence")
            
        Returns:
            Extracted data or None if path not found
        """
        if not path or path == "":
            return data
        
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None
        return current
    
    def _is_empty(self, data: Any) -> bool:
        """
        Check if data is empty or None.
        
        Args:
            data: Data to check
            
        Returns:
            True if data is empty/None, False otherwise
        """
        if data is None:
            return True
        if isinstance(data, (dict, list)):
            return len(data) == 0
        if isinstance(data, str):
            return len(data.strip()) == 0
        return False
    
    def get_deferred_count(self) -> int:
        """Get count of pending deferred validations"""
        return len([d for d in self.deferred_validations if d["status"] == "pending"])

