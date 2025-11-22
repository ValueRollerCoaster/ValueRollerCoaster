"""
Sonar Integration Utilities
Helper functions to integrate Sonar validation results with existing analyses.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SonarIntegrationUtils:
    """Utilities for integrating Sonar validation with existing analyses"""
    
    @staticmethod
    def merge_validated_website_analysis(gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                        sonar_validation: Dict, pid: int = 0) -> Dict[str, Any]:
        """
        Merge website analysis with Sonar validation results.
        
        Args:
            gemini_analysis: Original Gemini analysis
            chatgpt_analysis: Original ChatGPT analysis
            sonar_validation: Sonar validation results
            pid: Process ID for logging
            
        Returns:
            Enhanced analysis with Sonar validation integrated
        """
        logger.info(f"[PID {pid}] [SonarIntegrationUtils] Merging website analysis with Sonar validation")
        
        # Start with original analyses
        enhanced_analysis = {
            "gemini_analysis": gemini_analysis,
            "chatgpt_analysis": chatgpt_analysis,
            "sonar_validation": sonar_validation,
            "enhanced_metadata": {
                "sonar_validation_applied": True,
                "overall_confidence": sonar_validation.get("overall_confidence", 5),
                "validation_passed": sonar_validation.get("validation_passed", True)
            }
        }
        
        # Apply Sonar corrections if available
        if sonar_validation.get("validation_passed", True) and "error" not in sonar_validation:
            enhanced_analysis = SonarIntegrationUtils._apply_sonar_corrections(
                enhanced_analysis, sonar_validation, pid
            )
        
        return enhanced_analysis
    
    @staticmethod
    def merge_validated_market_intelligence(market_intelligence: Dict, sonar_validation: Dict, 
                                           pid: int = 0) -> Dict[str, Any]:
        """
        Merge market intelligence with Sonar validation results.
        
        Args:
            market_intelligence: Original market intelligence
            sonar_validation: Sonar validation results
            pid: Process ID for logging
            
        Returns:
            Enhanced market intelligence with Sonar validation integrated
        """
        logger.info(f"[PID {pid}] [SonarIntegrationUtils] Merging market intelligence with Sonar validation")
        
        enhanced_market_intelligence = {
            "original_market_intelligence": market_intelligence,
            "sonar_validation": sonar_validation,
            "enhanced_metadata": {
                "sonar_validation_applied": True,
                "overall_confidence": sonar_validation.get("overall_confidence", 5),
                "validation_passed": sonar_validation.get("validation_passed", True)
            }
        }
        
        # Apply Sonar corrections and additional insights
        if sonar_validation.get("validation_passed", True) and "error" not in sonar_validation:
            enhanced_market_intelligence = SonarIntegrationUtils._apply_market_corrections(
                enhanced_market_intelligence, sonar_validation, pid
            )
        
        return enhanced_market_intelligence
    
    @staticmethod
    def merge_validated_value_alignment(value_alignment: Dict, sonar_validation: Dict, 
                                       pid: int = 0) -> Dict[str, Any]:
        """
        Merge value alignment with Sonar validation results.
        
        Args:
            value_alignment: Original value alignment
            sonar_validation: Sonar validation results
            pid: Process ID for logging
            
        Returns:
            Enhanced value alignment with Sonar validation integrated
        """
        logger.info(f"[PID {pid}] [SonarIntegrationUtils] Merging value alignment with Sonar validation")
        
        enhanced_value_alignment = {
            "original_value_alignment": value_alignment,
            "sonar_validation": sonar_validation,
            "enhanced_metadata": {
                "sonar_validation_applied": True,
                "overall_confidence": sonar_validation.get("overall_confidence", 5),
                "validation_passed": sonar_validation.get("validation_passed", True)
            }
        }
        
        # Apply Sonar corrections and additional opportunities
        if sonar_validation.get("validation_passed", True) and "error" not in sonar_validation:
            enhanced_value_alignment = SonarIntegrationUtils._apply_value_corrections(
                enhanced_value_alignment, sonar_validation, pid
            )
        
        return enhanced_value_alignment
    
    @staticmethod
    def merge_validated_creative_elements(creative_elements: Dict, sonar_validation: Dict, 
                                         pid: int = 0) -> Dict[str, Any]:
        """
        Merge creative elements with Sonar validation results.
        
        Args:
            creative_elements: Original creative elements
            sonar_validation: Sonar validation results
            pid: Process ID for logging
            
        Returns:
            Enhanced creative elements with Sonar validation integrated
        """
        logger.info(f"[PID {pid}] [SonarIntegrationUtils] Merging creative elements with Sonar validation")
        
        enhanced_creative_elements = {
            "original_creative_elements": creative_elements,
            "sonar_validation": sonar_validation,
            "enhanced_metadata": {
                "sonar_validation_applied": True,
                "overall_confidence": sonar_validation.get("overall_confidence", 5),
                "validation_passed": sonar_validation.get("validation_passed", True)
            }
        }
        
        # Apply Sonar corrections and enhanced insights
        if sonar_validation.get("validation_passed", True) and "error" not in sonar_validation:
            enhanced_creative_elements = SonarIntegrationUtils._apply_creative_corrections(
                enhanced_creative_elements, sonar_validation, pid
            )
        
        return enhanced_creative_elements
    
    @staticmethod
    def merge_validated_final_persona(final_persona: Dict, sonar_validation: Dict, 
                                     pid: int = 0) -> Dict[str, Any]:
        """
        Merge final persona with Sonar validation results.
        
        Args:
            final_persona: Original final persona
            sonar_validation: Sonar validation results
            pid: Process ID for logging
            
        Returns:
            Enhanced final persona with Sonar validation integrated
        """
        logger.info(f"[PID {pid}] [SonarIntegrationUtils] Merging final persona with Sonar validation")
        
        enhanced_persona = final_persona.copy()
        
        # Add Sonar validation metadata
        enhanced_persona["sonar_validation"] = sonar_validation
        enhanced_persona["enhanced_metadata"] = enhanced_persona.get("enhanced_metadata", {})
        enhanced_persona["enhanced_metadata"].update({
            "sonar_validation_applied": True,
            "overall_confidence": sonar_validation.get("overall_confidence", 5),
            "validation_passed": sonar_validation.get("validation_passed", True),
            "completeness_score": sonar_validation.get("completeness_score", 5),
            "accuracy_score": sonar_validation.get("accuracy_score", 5),
            "consistency_score": sonar_validation.get("consistency_score", 5)
        })
        
        # Apply Sonar corrections if available
        if sonar_validation.get("validation_passed", True) and "error" not in sonar_validation:
            enhanced_persona = SonarIntegrationUtils._apply_persona_corrections(
                enhanced_persona, sonar_validation, pid
            )
        
        return enhanced_persona
    
    @staticmethod
    def _apply_sonar_corrections(enhanced_analysis: Dict, sonar_validation: Dict, pid: int) -> Dict[str, Any]:
        """Apply Sonar corrections to website analysis"""
        
        # Add recommended synthesis if available
        if "recommended_synthesis" in sonar_validation:
            enhanced_analysis["sonar_synthesis_recommendation"] = sonar_validation["recommended_synthesis"]
        
        # Add validation notes
        if "validation_notes" in sonar_validation:
            enhanced_analysis["sonar_validation_notes"] = sonar_validation["validation_notes"]
        
        return enhanced_analysis
    
    @staticmethod
    def _apply_market_corrections(enhanced_market_intelligence: Dict, sonar_validation: Dict, pid: int) -> Dict[str, Any]:
        """Apply Sonar corrections to market intelligence"""
        
        # Add verified market data
        if "verified_market_data" in sonar_validation:
            enhanced_market_intelligence["sonar_verified_market_data"] = sonar_validation["verified_market_data"]
        
        # Add market corrections
        if "market_corrections" in sonar_validation:
            enhanced_market_intelligence["sonar_market_corrections"] = sonar_validation["market_corrections"]
        
        # Add additional market insights
        if "additional_market_insights" in sonar_validation:
            enhanced_market_intelligence["sonar_additional_insights"] = sonar_validation["additional_market_insights"]
        
        # Add validation notes
        if "validation_notes" in sonar_validation:
            enhanced_market_intelligence["sonar_validation_notes"] = sonar_validation["validation_notes"]
        
        return enhanced_market_intelligence
    
    @staticmethod
    def _apply_value_corrections(enhanced_value_alignment: Dict, sonar_validation: Dict, pid: int) -> Dict[str, Any]:
        """Apply Sonar corrections to value alignment"""
        
        # Add verified value insights
        if "verified_value_insights" in sonar_validation:
            enhanced_value_alignment["sonar_verified_insights"] = sonar_validation["verified_value_insights"]
        
        # Add value corrections
        if "value_corrections" in sonar_validation:
            enhanced_value_alignment["sonar_value_corrections"] = sonar_validation["value_corrections"]
        
        # Add additional opportunities
        if "additional_opportunities" in sonar_validation:
            enhanced_value_alignment["sonar_additional_opportunities"] = sonar_validation["additional_opportunities"]
        
        # Add validation notes
        if "validation_notes" in sonar_validation:
            enhanced_value_alignment["sonar_validation_notes"] = sonar_validation["validation_notes"]
        
        return enhanced_value_alignment
    
    @staticmethod
    def _apply_creative_corrections(enhanced_creative_elements: Dict, sonar_validation: Dict, pid: int) -> Dict[str, Any]:
        """Apply Sonar corrections to creative elements"""
        
        # Add validated elements
        if "validated_elements" in sonar_validation:
            enhanced_creative_elements["sonar_validated_elements"] = sonar_validation["validated_elements"]
        
        # Add creative corrections
        if "creative_corrections" in sonar_validation:
            enhanced_creative_elements["sonar_creative_corrections"] = sonar_validation["creative_corrections"]
        
        # Add enhanced insights
        if "enhanced_insights" in sonar_validation:
            enhanced_creative_elements["sonar_enhanced_insights"] = sonar_validation["enhanced_insights"]
        
        # Add validation notes
        if "validation_notes" in sonar_validation:
            enhanced_creative_elements["sonar_validation_notes"] = sonar_validation["validation_notes"]
        
        return enhanced_creative_elements
    
    @staticmethod
    def _apply_persona_corrections(enhanced_persona: Dict, sonar_validation: Dict, pid: int) -> Dict[str, Any]:
        """Apply Sonar corrections to final persona"""
        
        # Add verified elements
        if "verified_elements" in sonar_validation:
            enhanced_persona["sonar_verified_elements"] = sonar_validation["verified_elements"]
        
        # Add missing elements
        if "missing_elements" in sonar_validation:
            enhanced_persona["sonar_missing_elements"] = sonar_validation["missing_elements"]
        
        # Add synthesis corrections
        if "synthesis_corrections" in sonar_validation:
            enhanced_persona["sonar_synthesis_corrections"] = sonar_validation["synthesis_corrections"]
        
        # Add final recommendations
        if "final_recommendations" in sonar_validation:
            enhanced_persona["sonar_final_recommendations"] = sonar_validation["final_recommendations"]
        
        # Add validation notes
        if "validation_notes" in sonar_validation:
            enhanced_persona["sonar_validation_notes"] = sonar_validation["validation_notes"]
        
        return enhanced_persona
    
    @staticmethod
    def calculate_overall_confidence(sonar_validations: List[Dict]) -> float:
        """
        Calculate overall confidence score from multiple Sonar validations.
        
        Args:
            sonar_validations: List of Sonar validation results
            
        Returns:
            Overall confidence score (0-10)
        """
        if not sonar_validations:
            return 5.0  # Default confidence
        
        # Calculate average confidence from all validations
        total_confidence = 0
        valid_count = 0
        
        for validation in sonar_validations:
            if "error" not in validation and validation.get("sonar_available", True):
                confidence = validation.get("overall_confidence", 5)
                total_confidence += confidence
                valid_count += 1
        
        if valid_count == 0:
            return 5.0  # Default if no valid validations
        
        return round(total_confidence / valid_count, 1)
    
    @staticmethod
    def summarize_sonar_validations(sonar_validations: List[Dict]) -> Dict[str, Any]:
        """
        Create a summary of all Sonar validations.
        
        Args:
            sonar_validations: List of Sonar validation results
            
        Returns:
            Summary of all validations
        """
        summary = {
            "total_validations": len(sonar_validations),
            "passed_validations": 0,
            "failed_validations": 0,
            "unavailable_validations": 0,
            "overall_confidence": 5.0,
            "validation_types": [],
            "key_issues": [],
            "key_insights": []
        }
        
        for validation in sonar_validations:
            validation_type = validation.get("validation_type", "unknown")
            summary["validation_types"].append(validation_type)
            
            if validation.get("sonar_available", True):
                if validation.get("validation_passed", True):
                    summary["passed_validations"] += 1
                else:
                    summary["failed_validations"] += 1
                    
                # Collect key issues and insights
                if "validation_notes" in validation:
                    summary["key_insights"].append(f"{validation_type}: {validation['validation_notes']}")
            else:
                summary["unavailable_validations"] += 1
        
        # Calculate overall confidence
        summary["overall_confidence"] = SonarIntegrationUtils.calculate_overall_confidence(sonar_validations)
        
        return summary

# Global instance
sonar_integration_utils = SonarIntegrationUtils() 