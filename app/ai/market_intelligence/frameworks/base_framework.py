"""
Base Industry Framework
Abstract base class for all industry-specific analysis frameworks.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseIndustryFramework(ABC):
    """Base class for industry-specific analysis frameworks"""
    
    @property
    @abstractmethod
    def industry_name(self) -> str:
        """Industry name"""
        pass
    
    @property
    @abstractmethod
    def nace_codes(self) -> List[str]:
        """Relevant NACE codes for this industry"""
        pass
    
    @property
    @abstractmethod
    def key_metrics(self) -> List[str]:
        """Key performance metrics for this industry"""
        pass
    
    @property
    @abstractmethod
    def trend_areas(self) -> List[str]:
        """Key trend areas to analyze"""
        pass
    
    @property
    @abstractmethod
    def competitive_factors(self) -> List[str]:
        """Key competitive factors"""
        pass
    
    @property
    @abstractmethod
    def value_drivers(self) -> List[str]:
        """Industry-specific value drivers"""
        pass
    
    @property
    @abstractmethod
    def pain_points(self) -> List[str]:
        """Common pain points in this industry"""
        pass
    
    @property
    @abstractmethod
    def technology_focus(self) -> List[str]:
        """Technology areas of focus"""
        pass
    
    @property
    @abstractmethod
    def sustainability_initiatives(self) -> List[str]:
        """Sustainability initiatives relevant to this industry"""
        pass
    
    def get_framework_data(self) -> Dict[str, Any]:
        """Get complete framework data as dictionary"""
        return {
            "industry_name": self.industry_name,
            "nace_codes": self.nace_codes,
            "key_metrics": self.key_metrics,
            "trend_areas": self.trend_areas,
            "competitive_factors": self.competitive_factors,
            "value_drivers": self.value_drivers,
            "pain_points": self.pain_points,
            "technology_focus": self.technology_focus,
            "sustainability_initiatives": self.sustainability_initiatives
        }
    
    def get_analysis_prompt_context(self) -> str:
        """Get formatted context for analysis prompts"""
        return f"""
INDUSTRY: {self.industry_name}
NACE CODES: {', '.join(self.nace_codes)}
KEY METRICS: {', '.join(self.key_metrics)}
TREND AREAS: {', '.join(self.trend_areas)}
COMPETITIVE FACTORS: {', '.join(self.competitive_factors)}
VALUE DRIVERS: {', '.join(self.value_drivers)}
PAIN POINTS: {', '.join(self.pain_points)}
TECHNOLOGY FOCUS: {', '.join(self.technology_focus)}
SUSTAINABILITY: {', '.join(self.sustainability_initiatives)}
""" 