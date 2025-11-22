#!/usr/bin/env python3
"""
Comprehensive NACE Code System
Full NACE Rev. 2 classification with industry mappings and Eurostat API integration
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class NACE_System:
    """Comprehensive NACE code system with full coverage and API integration"""
    
    def __init__(self):
        self.eurostat_api_base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"
        self.cache_dir = Path("app/nace_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # NACE Rev. 2 sections
        self.nace_sections = {
            "A": "Agriculture, forestry and fishing",
            "B": "Mining and quarrying", 
            "C": "Manufacturing",
            "D": "Electricity, gas, steam and air conditioning supply",
            "E": "Water supply; sewerage, waste management and remediation activities",
            "F": "Construction",
            "G": "Wholesale and retail trade; repair of motor vehicles and motorcycles",
            "H": "Transportation and storage",
            "I": "Accommodation and food service activities",
            "J": "Information and communication",
            "K": "Financial and insurance activities",
            "L": "Real estate activities",
            "M": "Professional, scientific and technical activities",
            "N": "Administrative and support service activities",
            "O": "Public administration and defence; compulsory social security",
            "P": "Education",
            "Q": "Human health and social work activities",
            "R": "Arts, entertainment and recreation",
            "S": "Other service activities",
            "T": "Activities of households as employers",
            "U": "Activities of extraterritorial organisations and bodies"
        }
        
        # Comprehensive industry to NACE mapping
        self.industry_nace_mapping = {
            # Core industries
            "agriculture": "A", "farming": "A01", "food": "C10", "mining": "B",
            "manufacturing": "C", "construction": "F", "retail": "G47", "transport": "H",
            "logistics": "H52", "warehousing": "H52", "it": "J", "software": "J62",
            "finance": "K", "banking": "K64", "insurance": "K65", "healthcare": "Q86",
            "education": "P", "consulting": "M70", "real estate": "L",
            
            # Manufacturing subsectors
            "automotive": "C29", "cars": "C29", "aerospace": "C30", "electronics": "C26",
            "machinery": "C28", "material handling": "C28.22", "forklifts": "C28.22",
            "steel": "C24", "chemicals": "C20", "pharmaceuticals": "C21", "textiles": "C13",
            "clothing": "C14", "food processing": "C10", "beverages": "C11",
            
            # Energy and utilities
            "energy": "D", "electricity": "D35.1", "gas": "D35.2", "renewable energy": "D35.1",
            "solar": "D35.1", "wind": "D35.1", "nuclear": "D35.1", "hydrogen": "D35.2",
            
            # Modern/emerging industries
            "artificial intelligence": "J62", "ai": "J62", "blockchain": "J62",
            "cryptocurrency": "K64", "fintech": "K64", "biotechnology": "C21",
            "nanotechnology": "C26", "robotics": "C28", "3d printing": "C28",
            "autonomous vehicles": "C29", "electric vehicles": "C29", "battery": "C27",
            "quantum computing": "C26", "space": "C30", "satellites": "C30",
            "cybersecurity": "J62", "cloud computing": "J62", "big data": "J62",
            "machine learning": "J62", "iot": "C26", "smart cities": "F",
            
            # Services
            "hospitality": "I", "hotels": "I55", "restaurants": "I56", "tourism": "I",
            "telecommunications": "J61", "media": "J59", "publishing": "J58",
            "advertising": "M73", "legal": "M69", "accounting": "M69", "research": "M72",
            "security": "N80", "cleaning": "N81", "waste management": "E38",
            
            # Specialized
            "defense": "C25", "weapons": "C25", "medical devices": "C32",
            "furniture": "C31", "jewelry": "C32", "wholesale": "G46", "e-commerce": "G47"
        }
        
        # Load cached NACE data if available
        self.nace_cache = self._load_nace_cache()
        
        # Enhanced downstream/final user mapping with specificity levels
        self.downstream_nace_map = {
            "A": {
                "direct": ["C10", "C11", "C12"],  # Food processing, beverages, tobacco
                "indirect": ["G46", "G47", "H52"],  # Wholesale, retail, warehousing
                "end_consumers": ["I56", "Q86"],  # Restaurants, healthcare
                "value_chain": ["C16", "C20", "C21"]  # Wood products, chemicals, pharmaceuticals
            },
            "B": {
                "direct": ["C24", "C25", "C26", "C27"],  # Metals, fabricated metal, electronics, batteries
                "indirect": ["C28", "C29", "C30", "F"],  # Machinery, vehicles, construction
                "end_consumers": ["D", "E", "G", "H"],  # Energy, utilities, trade, transport
                "value_chain": ["C20", "C21", "C22"]  # Chemicals, pharmaceuticals, rubber/plastic
            },
            "C": {
                "direct": ["F", "G46", "G47", "H52"],  # Construction, wholesale, retail, warehousing
                "indirect": ["H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All service sectors
                "end_consumers": ["G47", "I56", "Q86"],  # Retail, restaurants, healthcare
                "value_chain": ["C28", "C29", "C30"]  # Machinery, vehicles, transport equipment
            },
            "D": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56"],  # Retail, hotels, restaurants
                "value_chain": ["C26", "C27", "C28"]  # Electronics, batteries, machinery
            },
            "E": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56"],  # Retail, hotels, restaurants
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "F": {
                "direct": ["G46", "G47", "L68"],  # Wholesale, retail, real estate
                "indirect": ["H", "I", "J", "K", "M", "N", "O", "P", "Q"],  # Service sectors
                "end_consumers": ["L68", "G47"],  # Real estate, retail
                "value_chain": ["C16", "C23", "C25", "C26"]  # Wood, glass, metals, electronics
            },
            "G": {
                "direct": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["H52", "I55", "I56"],  # Logistics, hospitality
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "H": {
                "direct": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "I55", "I56"],  # Trade, hospitality
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C29", "C30", "C26"]  # Vehicles, transport equipment, electronics
            },
            "I": {
                "direct": ["G47", "C10", "C11", "C12"],  # Retail, food processing
                "indirect": ["H52", "M73", "N80"],  # Logistics, advertising, security
                "end_consumers": ["G47", "I55", "I56"],  # Retail, hotels, restaurants
                "value_chain": ["C10", "C11", "C12", "C26"]  # Food, beverages, electronics
            },
            "J": {
                "direct": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "K": {
                "direct": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "L": {
                "direct": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "indirect": ["H", "I", "J", "K", "M", "N", "O", "P", "Q"],  # Service sectors
                "end_consumers": ["G47", "I55", "I56"],  # Retail, hospitality
                "value_chain": ["C16", "C23", "C25", "C26"]  # Wood, glass, metals, electronics
            },
            "M": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "N": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "O": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "P": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C26", "C28", "C29"]  # Electronics, machinery, vehicles
            },
            "Q": {
                "direct": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],  # All sectors
                "indirect": ["G47", "H52"],  # Trade, logistics
                "end_consumers": ["G47", "I55", "I56", "Q86"],  # Retail, hospitality, healthcare
                "value_chain": ["C21", "C26", "C32"]  # Pharmaceuticals, electronics, medical devices
            },
            "R": {
                "direct": ["G47", "I55", "I56"],  # Retail, hospitality
                "indirect": ["H52", "M73", "N80"],  # Logistics, advertising, security
                "end_consumers": ["G47", "I55", "I56"],  # Retail, hospitality
                "value_chain": ["C26", "C32", "C33"]  # Electronics, medical devices, repair
            },
            "S": {
                "direct": ["G47", "I55", "I56"],  # Retail, hospitality
                "indirect": ["H52", "M73", "N80"],  # Logistics, advertising, security
                "end_consumers": ["G47", "I55", "I56"],  # Retail, hospitality
                "value_chain": ["C26", "C32", "C33"]  # Electronics, medical devices, repair
            }
            # T, U: not mapped (household activities, extraterritorial)
        }
    
    def _load_nace_cache(self) -> Dict:
        """Load cached NACE data from file"""
        cache_file = self.cache_dir / "nace_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load NACE cache: {e}")
        return {}
    
    def _save_nace_cache(self):
        """Save NACE data to cache file"""
        cache_file = self.cache_dir / "nace_cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.nace_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save NACE cache: {e}")
    
    def get_nace_from_eurostat(self, nace_code: str = "NACE_R2") -> Optional[Dict]:
        """Get NACE codes from Eurostat API"""
        try:
            url = f"{self.eurostat_api_base}/codelist/ESTAT/{nace_code}"
            params = {"format": "JSON"}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the result
            self.nace_cache[nace_code] = {
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            self._save_nace_cache()
            
            return data
            
        except Exception as e:
            # Eurostat API is optional fallback - log as warning, not error
            logger.warning(f"Eurostat API unavailable (using hardcoded mappings): {e}")
            return None
    
    def detect_industry_nace(self, industry_name: str, use_api: bool = True) -> Dict:
        """Detect NACE code for an industry name"""
        industry_name_lower = industry_name.lower()
        
        # First, try exact matches
        exact_matches = []
        for keyword, nace_code in self.industry_nace_mapping.items():
            if keyword == industry_name_lower:
                exact_matches.append((keyword, nace_code))
        
        # Then try partial matches
        partial_matches = []
        for keyword, nace_code in self.industry_nace_mapping.items():
            if keyword in industry_name_lower or industry_name_lower in keyword:
                partial_matches.append((keyword, nace_code))
        
        # Try regex pattern matching
        nace_pattern = re.compile(r'\b[A-Z]\d{2}(?:\.\d{2})?\b')
        regex_matches = nace_pattern.findall(industry_name.upper())
        
        result = {
            "input_industry": industry_name,
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "regex_matches": regex_matches,
            "best_match": None,
            "confidence": "LOW",
            "nace_code": None,
            "section": None,
            "description": None
        }
        
        # Determine best match
        if exact_matches:
            best_keyword, best_nace = exact_matches[0]
            result["best_match"] = best_keyword
            result["nace_code"] = best_nace
            result["confidence"] = "HIGH"
        elif partial_matches:
            # Sort by keyword length (longer = more specific)
            partial_matches.sort(key=lambda x: len(x[0]), reverse=True)
            best_keyword, best_nace = partial_matches[0]
            result["best_match"] = best_keyword
            result["nace_code"] = best_nace
            result["confidence"] = "MEDIUM"
        elif regex_matches:
            result["nace_code"] = regex_matches[0]
            result["confidence"] = "HIGH"
        
        # Get section information
        if result["nace_code"]:
            section = result["nace_code"][0]
            result["section"] = section
            result["description"] = self.nace_sections.get(section, "Unknown")
        
        # Try Eurostat API if requested and no good match found
        if use_api and result["confidence"] == "LOW":
            eurostat_data = self.get_nace_from_eurostat()
            if eurostat_data:
                result["eurostat_data_available"] = True
        
        return result
    
    def get_related_nace_codes(self, nace_code: str) -> List[str]:
        """Get related NACE codes for a given code"""
        if not nace_code:
            return []
        
        section = nace_code[0]
        related = []
        
        # Add section-level codes
        related.append(section)
        
        # Add 2-digit codes in the same section
        if len(nace_code) >= 2:
            two_digit = nace_code[:2]
            related.append(two_digit)
        
        # Add specific related codes based on section
        if section == "C":  # Manufacturing
            related.extend(["C28", "C29", "C30"])  # Machinery, vehicles, transport equipment
        elif section == "F":  # Construction
            related.extend(["C16", "C23", "C25"])  # Wood, glass, fabricated metal
        elif section == "H":  # Transportation
            related.extend(["C29", "C30", "F"])  # Vehicles, construction
        elif section == "G":  # Trade
            related.extend(["C", "H52"])  # Manufacturing, warehousing
        
        return list(set(related))  # Remove duplicates
    
    def get_industry_insights(self, nace_code: str) -> Dict:
        """Get industry insights based on NACE code"""
        if not nace_code:
            return {"insights": [], "trends": [], "opportunities": []}
        
        section = nace_code[0]
        
        # Industry-specific insights
        insights_map = {
            "A": {
                "insights": ["Sustainable farming practices", "Precision agriculture", "Organic food demand"],
                "trends": ["Digitalization", "Climate adaptation", "Supply chain resilience"],
                "opportunities": ["Smart farming technology", "Organic certification", "Direct-to-consumer"]
            },
            "B": {
                "insights": ["Critical raw materials", "Energy transition", "Environmental compliance"],
                "trends": ["Green mining", "Automation", "Circular economy"],
                "opportunities": ["Rare earth extraction", "Mining automation", "Recycling technology"]
            },
            "C": {
                "insights": ["Industry 4.0 adoption", "Supply chain resilience", "Sustainability focus"],
                "trends": ["Digital transformation", "Automation", "Green manufacturing"],
                "opportunities": ["Smart factory solutions", "Circular manufacturing", "Customization"]
            },
            "F": {
                "insights": ["Housing demand", "Infrastructure investment", "Green building"],
                "trends": ["Modular construction", "Sustainable materials", "Digital twins"],
                "opportunities": ["Prefabricated solutions", "Green building materials", "Construction tech"]
            },
            "G": {
                "insights": ["E-commerce growth", "Omnichannel retail", "Supply chain optimization"],
                "trends": ["Digital commerce", "Last-mile delivery", "Personalization"],
                "opportunities": ["E-commerce platforms", "Logistics solutions", "Customer analytics"]
            },
            "H": {
                "insights": ["Supply chain resilience", "Last-mile delivery", "Sustainability"],
                "trends": ["Autonomous vehicles", "Green logistics", "Digital platforms"],
                "opportunities": ["Logistics automation", "Green transport", "Supply chain visibility"]
            },
            "J": {
                "insights": ["Digital transformation", "Cybersecurity", "AI adoption"],
                "trends": ["Cloud computing", "Edge computing", "Quantum computing"],
                "opportunities": ["AI solutions", "Cybersecurity", "Digital platforms"]
            },
            "K": {
                "insights": ["Fintech disruption", "Digital banking", "ESG investing"],
                "trends": ["Open banking", "Cryptocurrency", "Green finance"],
                "opportunities": ["Fintech solutions", "ESG products", "Digital banking"]
            },
            "Q": {
                "insights": ["Aging population", "Digital health", "Preventive care"],
                "trends": ["Telemedicine", "AI diagnostics", "Personalized medicine"],
                "opportunities": ["Digital health platforms", "Medical devices", "Health analytics"]
            }
        }
        
        return insights_map.get(section, {
            "insights": ["Industry analysis", "Market trends", "Competitive landscape"],
            "trends": ["Digitalization", "Sustainability", "Innovation"],
            "opportunities": ["Technology adoption", "Market expansion", "Process optimization"]
        })
    
    def validate_nace_code(self, nace_code: str) -> bool:
        """Validate if a NACE code is properly formatted"""
        if not nace_code:
            return False
        
        # Check format: A, A01, A01.1, A01.11
        pattern = re.compile(r'^[A-U](\d{2}(\.\d{1,2})?)?$')
        return bool(pattern.match(nace_code))
    
    def get_nace_hierarchy(self, nace_code: str) -> Dict:
        """Get the hierarchical structure of a NACE code"""
        if not self.validate_nace_code(nace_code):
            return {"error": "Invalid NACE code format"}
        
        hierarchy = {
            "section": nace_code[0],
            "section_name": self.nace_sections.get(nace_code[0], "Unknown"),
            "division": None,
            "group": None,
            "class": None
        }
        
        if len(nace_code) >= 3:
            hierarchy["division"] = nace_code[:2]
        
        if len(nace_code) >= 4:
            hierarchy["group"] = nace_code[:4]
        
        if len(nace_code) >= 6:
            hierarchy["class"] = nace_code
        
        return hierarchy
    
    def get_downstream_nace_codes(self, nace_code: str) -> List[str]:
        """Get downstream/final user NACE codes for a given code"""
        if not nace_code:
            return []
        section = nace_code[0]
        downstream_data = self.downstream_nace_map.get(section, {})
        if isinstance(downstream_data, dict):
            # Flatten all lists from the dict values
            result = []
            for value_list in downstream_data.values():
                if isinstance(value_list, list):
                    result.extend(value_list)
            return result
        elif isinstance(downstream_data, list):
            return downstream_data
        else:
            return []

    def get_customer_segments(self, nace_code: str) -> Dict:
        """Get detailed customer segmentation for a NACE code"""
        if not nace_code:
            return {}
        
        section = nace_code[0]
        downstream = self.downstream_nace_map.get(section, {})
        
        segments = {
            "manufacturers": downstream.get("direct", []),
            "distributors": downstream.get("indirect", []),
            "end_users": downstream.get("end_consumers", []),
            "suppliers": self.get_upstream_suppliers(nace_code),
            "competitors": self.get_competitor_codes(nace_code)
        }
        
        return segments

    def get_upstream_suppliers(self, nace_code: str) -> List[str]:
        """Get upstream supplier NACE codes for a given code"""
        if not nace_code:
            return []
        
        section = nace_code[0]
        
        # Reverse mapping: who supplies to this section
        upstream_map = {
            "A": ["C16", "C20", "C21", "C28"],  # Agriculture gets wood, chemicals, pharmaceuticals, machinery
            "B": ["C25", "C26", "C28"],  # Mining gets metals, electronics, machinery
            "C": ["B", "C24", "C25", "C26", "C27"],  # Manufacturing gets mining, metals, electronics, batteries
            "D": ["B", "C26", "C27", "C28"],  # Energy gets mining, electronics, batteries, machinery
            "E": ["C26", "C28", "C29"],  # Water/Utilities gets electronics, machinery, vehicles
            "F": ["C16", "C23", "C25", "C26"],  # Construction gets wood, glass, metals, electronics
            "G": ["C", "H52"],  # Trade gets manufacturing, logistics
            "H": ["C29", "C30", "C26"],  # Transport gets vehicles, transport equipment, electronics
            "I": ["C10", "C11", "C12", "C26"],  # Hospitality gets food, beverages, electronics
            "J": ["C26", "C28"],  # IT gets electronics, machinery
            "K": ["C26", "C28"],  # Finance gets electronics, machinery
            "L": ["F", "C16", "C23", "C25"],  # Real estate gets construction, wood, glass, metals
            "M": ["C26", "C28"],  # Professional services gets electronics, machinery
            "N": ["C26", "C28"],  # Administrative services gets electronics, machinery
            "O": ["C26", "C28"],  # Public admin gets electronics, machinery
            "P": ["C26", "C28"],  # Education gets electronics, machinery
            "Q": ["C21", "C26", "C32"],  # Healthcare gets pharmaceuticals, electronics, medical devices
            "R": ["C26", "C32", "C33"],  # Arts gets electronics, medical devices, repair
            "S": ["C26", "C32", "C33"]  # Other services gets electronics, medical devices, repair
        }
        
        return upstream_map.get(section, [])

    def get_competitor_codes(self, nace_code: str) -> List[str]:
        """Get competitor NACE codes for a given code"""
        if not nace_code:
            return []
        
        section = nace_code[0]
        
        # Competitor mapping: similar businesses in the same or related sections
        competitor_map = {
            "A": ["A"],  # Agriculture competes within agriculture
            "B": ["B"],  # Mining competes within mining
            "C": ["C"],  # Manufacturing competes within manufacturing
            "D": ["D"],  # Energy competes within energy
            "E": ["E"],  # Water/Utilities competes within utilities
            "F": ["F"],  # Construction competes within construction
            "G": ["G"],  # Trade competes within trade
            "H": ["H"],  # Transport competes within transport
            "I": ["I"],  # Hospitality competes within hospitality
            "J": ["J"],  # IT competes within IT
            "K": ["K"],  # Finance competes within finance
            "L": ["L"],  # Real estate competes within real estate
            "M": ["M"],  # Professional services competes within professional services
            "N": ["N"],  # Administrative services competes within administrative services
            "O": ["O"],  # Public admin competes within public admin
            "P": ["P"],  # Education competes within education
            "Q": ["Q"],  # Healthcare competes within healthcare
            "R": ["R"],  # Arts competes within arts
            "S": ["S"]  # Other services competes within other services
        }
        
        return competitor_map.get(section, [])

    def get_value_chain_analysis(self, nace_code: str) -> Dict:
        """Get comprehensive value chain analysis"""
        if not nace_code:
            return {}
        
        section = nace_code[0]
        
        value_chains = {
            "A": {
                "upstream": ["C16", "C20", "C21", "C28"],  # Wood, chemicals, pharmaceuticals, machinery
                "core_activities": ["A01", "A02", "A03"],  # Crop, animal, fishing
                "downstream": ["C10", "C11", "C12", "G47"],  # Food processing, retail
                "support_services": ["H52", "M69", "N80"]  # Logistics, accounting, security
            },
            "B": {
                "upstream": ["C25", "C26", "C28"],  # Metals, electronics, machinery
                "core_activities": ["B05", "B06", "B07", "B08", "B09"],  # Mining activities
                "downstream": ["C24", "C25", "C26", "C27"],  # Metal products, electronics
                "support_services": ["H52", "M69", "N80"]  # Logistics, accounting, security
            },
            "C": {
                "upstream": ["B", "C24", "C25", "C26", "C27"],  # Mining, metals, electronics, batteries
                "core_activities": ["C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29", "C30", "C31", "C32", "C33"],  # All manufacturing
                "downstream": ["F", "G46", "G47", "H52"],  # Construction, wholesale, retail, warehousing
                "support_services": ["H52", "M69", "N80", "J62"]  # Logistics, accounting, security, software
            },
            "D": {
                "upstream": ["B", "C26", "C27", "C28"],  # Mining, electronics, batteries, machinery
                "core_activities": ["D35"],  # Energy production
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["H52", "M69", "N80", "J62"]  # Logistics, accounting, security, software
            },
            "E": {
                "upstream": ["C26", "C28", "C29"],  # Electronics, machinery, vehicles
                "core_activities": ["E36", "E37", "E38", "E39"],  # Water, waste, remediation
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["H52", "M69", "N80", "J62"]  # Logistics, accounting, security, software
            },
            "F": {
                "upstream": ["C16", "C23", "C25", "C26"],  # Wood, glass, metals, electronics
                "core_activities": ["F41", "F42", "F43"],  # Construction activities
                "downstream": ["G46", "G47", "L68"],  # Wholesale, retail, real estate
                "support_services": ["H52", "M69", "N80", "J62"]  # Logistics, accounting, security, software
            },
            "G": {
                "upstream": ["C", "H52"],  # Manufacturing, logistics
                "core_activities": ["G45", "G46", "G47"],  # Trade activities
                "downstream": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["H52", "M69", "N80", "J62"]  # Logistics, accounting, security, software
            },
            "H": {
                "upstream": ["C29", "C30", "C26"],  # Vehicles, transport equipment, electronics
                "core_activities": ["H49", "H50", "H51", "H52", "H53"],  # Transport activities
                "downstream": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["M69", "N80", "J62"]  # Accounting, security, software
            },
            "I": {
                "upstream": ["C10", "C11", "C12", "C26"],  # Food, beverages, electronics
                "core_activities": ["I55", "I56"],  # Hospitality activities
                "downstream": ["G47"],  # Retail
                "support_services": ["H52", "M73", "N80"]  # Logistics, advertising, security
            },
            "J": {
                "upstream": ["C26", "C28"],  # Electronics, machinery
                "core_activities": ["J58", "J59", "J60", "J61", "J62", "J63"],  # IT activities
                "downstream": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["M69", "N80"]  # Accounting, security
            },
            "K": {
                "upstream": ["C26", "C28"],  # Electronics, machinery
                "core_activities": ["K64", "K65", "K66"],  # Finance activities
                "downstream": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["M69", "N80", "J62"]  # Accounting, security, software
            },
            "L": {
                "upstream": ["F", "C16", "C23", "C25"],  # Construction, wood, glass, metals
                "core_activities": ["L68"],  # Real estate activities
                "downstream": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "support_services": ["M69", "N80", "J62"]  # Accounting, security, software
            },
            "M": {
                "upstream": ["C26", "C28"],  # Electronics, machinery
                "core_activities": ["M69", "M70", "M71", "M72", "M73", "M74", "M75"],  # Professional services
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"],  # All sectors
                "support_services": ["N80", "J62"]  # Security, software
            },
            "N": {
                "upstream": ["C26", "C28"],  # Electronics, machinery
                "core_activities": ["N77", "N78", "N79", "N80", "N81", "N82"],  # Administrative services
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"],  # All sectors
                "support_services": ["J62"]  # Software
            },
            "O": {
                "upstream": ["C26", "C28"],  # Electronics, machinery
                "core_activities": ["O84"],  # Public administration
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"],  # All sectors
                "support_services": ["J62"]  # Software
            },
            "P": {
                "upstream": ["C26", "C28"],  # Electronics, machinery
                "core_activities": ["P85"],  # Education
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"],  # All sectors
                "support_services": ["J62"]  # Software
            },
            "Q": {
                "upstream": ["C21", "C26", "C32"],  # Pharmaceuticals, electronics, medical devices
                "core_activities": ["Q86", "Q87", "Q88"],  # Healthcare activities
                "downstream": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],  # All sectors
                "support_services": ["J62"]  # Software
            },
            "R": {
                "upstream": ["C26", "C32", "C33"],  # Electronics, medical devices, repair
                "core_activities": ["R90", "R91", "R92", "R93"],  # Arts activities
                "downstream": ["G47", "I55", "I56"],  # Retail, hospitality
                "support_services": ["H52", "M73", "N80"]  # Logistics, advertising, security
            },
            "S": {
                "upstream": ["C26", "C32", "C33"],  # Electronics, medical devices, repair
                "core_activities": ["S94", "S95", "S96"],  # Other services
                "downstream": ["G47", "I55", "I56"],  # Retail, hospitality
                "support_services": ["H52", "M73", "N80"]  # Logistics, advertising, security
            }
        }
        
        return value_chains.get(section, {})

    def get_customer_journey(self, nace_code: str) -> Dict:
        """Map customer journey for a NACE code"""
        if not nace_code:
            return {}
        
        section = nace_code[0]
        
        journeys = {
            "A": {
                "awareness": ["G47", "I56", "Q86"],  # Retail, restaurants, healthcare
                "consideration": ["C10", "C11", "C12"],  # Food processors
                "purchase": ["G46", "G47"],  # Wholesale, retail
                "usage": ["I56", "Q86"],  # Restaurants, healthcare
                "loyalty": ["G47", "I56"]  # Retail, restaurants
            },
            "B": {
                "awareness": ["C24", "C25", "C26", "C27"],  # Manufacturing
                "consideration": ["C28", "C29", "C30"],  # Machinery, vehicles
                "purchase": ["C24", "C25", "C26", "C27"],  # Manufacturing
                "usage": ["F", "D", "E"],  # Construction, energy, utilities
                "loyalty": ["C24", "C25", "C26", "C27"]  # Manufacturing
            },
            "C": {
                "awareness": ["F", "G46", "G47", "H52"],  # Construction, wholesale, retail, warehousing
                "consideration": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "purchase": ["F", "G46", "G47", "H52"],  # Construction, wholesale, retail, warehousing
                "usage": ["F", "G47", "H52"],  # Construction, retail, warehousing
                "loyalty": ["F", "G46", "G47"]  # Construction, wholesale, retail
            },
            "D": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H"],  # Manufacturing, construction, trade, transport
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]  # All sectors
            },
            "E": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H"],  # Manufacturing, construction, trade, transport
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]  # All sectors
            },
            "F": {
                "awareness": ["G46", "G47", "L68"],  # Wholesale, retail, real estate
                "consideration": ["G46", "G47", "L68"],  # Wholesale, retail, real estate
                "purchase": ["G46", "G47", "L68"],  # Wholesale, retail, real estate
                "usage": ["G46", "G47", "L68"],  # Wholesale, retail, real estate
                "loyalty": ["G46", "G47", "L68"]  # Wholesale, retail, real estate
            },
            "G": {
                "awareness": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "purchase": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]  # All sectors
            },
            "H": {
                "awareness": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "purchase": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "G46", "G47", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]  # All sectors
            },
            "I": {
                "awareness": ["G47", "C10", "C11", "C12"],  # Retail, food processing
                "consideration": ["G47", "C10", "C11", "C12"],  # Retail, food processing
                "purchase": ["G47", "C10", "C11", "C12"],  # Retail, food processing
                "usage": ["G47", "I55", "I56"],  # Retail, hotels, restaurants
                "loyalty": ["G47", "I55", "I56"]  # Retail, hotels, restaurants
            },
            "J": {
                "awareness": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q"]  # All sectors
            },
            "K": {
                "awareness": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q"]  # All sectors
            },
            "L": {
                "awareness": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "consideration": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "purchase": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "usage": ["F", "G46", "G47"],  # Construction, wholesale, retail
                "loyalty": ["F", "G46", "G47"]  # Construction, wholesale, retail
            },
            "M": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "N", "O", "P", "Q"]  # All sectors
            },
            "N": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "O", "P", "Q"]  # All sectors
            },
            "O": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "Q"]  # All sectors
            },
            "P": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Q"]  # All sectors
            },
            "Q": {
                "awareness": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],  # All sectors
                "consideration": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],  # All sectors
                "purchase": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],  # All sectors
                "usage": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],  # All sectors
                "loyalty": ["C", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]  # All sectors
            },
            "R": {
                "awareness": ["G47", "I55", "I56"],  # Retail, hospitality
                "consideration": ["G47", "I55", "I56"],  # Retail, hospitality
                "purchase": ["G47", "I55", "I56"],  # Retail, hospitality
                "usage": ["G47", "I55", "I56"],  # Retail, hospitality
                "loyalty": ["G47", "I55", "I56"]  # Retail, hospitality
            },
            "S": {
                "awareness": ["G47", "I55", "I56"],  # Retail, hospitality
                "consideration": ["G47", "I55", "I56"],  # Retail, hospitality
                "purchase": ["G47", "I55", "I56"],  # Retail, hospitality
                "usage": ["G47", "I55", "I56"],  # Retail, hospitality
                "loyalty": ["G47", "I55", "I56"]  # Retail, hospitality
            }
        }
        
        return journeys.get(section, {})

# Global instance for easy access
nace_system = NACE_System() 