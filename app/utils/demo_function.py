"""
Dynamic Demo Data Generation System
Generates demo value components and customers based on company profile using Gemini AI
"""

import streamlit as st
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicDemoGenerator:
    """Generates demo data based on company profile using AI"""
    
    def __init__(self):
        self.company_context = None
        self._load_company_context()
    
    def _load_company_context(self):
        """Load company context for demo generation"""
        try:
            from app.core.company_context_manager import CompanyContextManager
            self.company_context = CompanyContextManager()
        except Exception as e:
            logger.error(f"Error loading company context: {e}")
            self.company_context = None
    
    async def generate_demo_value_components(self, user_id: str) -> Dict[str, Any]:
        """Generate demo value components based on company profile"""
        if not self.company_context:
            return {"error": "Company context not available"}
        
        try:
            from app.ai.gemini_client import gemini_client
            
            # Get company context
            company_name = self.company_context.get_company_name()
            core_business = self.company_context.get_core_business()
            target_customers = self.company_context.get_target_customers()
            industries_served = self.company_context.get_industries_served()
            products = self.company_context.get_products()
            
            # Create prompt for demo value components
            prompt = f"""
            Generate realistic demo value components for {company_name} based on their business profile.
            
            COMPANY PROFILE:
            - Company: {company_name}
            - Core Business: {core_business}
            - Target Customers: {', '.join(target_customers)}
            - Industries Served: {', '.join(industries_served)}
            - Products/Services: {products}
            
            Generate demo value components in the following categories:
            1. Technical Value (Quality, Performance, Innovation, Reliability)
            2. Business Value (Cost Efficiency, ROI, Productivity, Scalability)
            3. Strategic Value (Partnership, Growth, Market Position, Competitive Advantage)
            4. After-Sales Value (Support, Training, Maintenance, Service)
            
            For each component, provide:
            - Realistic technical specifications or business metrics
            - Customer benefits that align with the target market
            - Industry-specific value propositions
            
            Return as JSON with this structure:
            {{
                "technical_value": {{
                    "quality": ["component1", "component2"],
                    "performance": ["component1", "component2"],
                    "innovation": ["component1", "component2"],
                    "reliability": ["component1", "component2"]
                }},
                "business_value": {{
                    "cost_efficiency": ["component1", "component2"],
                    "roi": ["component1", "component2"],
                    "productivity": ["component1", "component2"],
                    "scalability": ["component1", "component2"]
                }},
                "strategic_value": {{
                    "partnership": ["component1", "component2"],
                    "growth": ["component1", "component2"],
                    "market_position": ["component1", "component2"],
                    "competitive_advantage": ["component1", "component2"]
                }},
                "after_sales_value": {{
                    "support": ["component1", "component2"],
                    "training": ["component1", "component2"],
                    "maintenance": ["component1", "component2"],
                    "service": ["component1", "component2"]
                }}
            }}
            """
            
            # Generate with Gemini
            response = await gemini_client(prompt, temperature=0.3, max_tokens=4000)
            
            if response:
                # Parse and structure the response
                demo_components = self._parse_demo_components(response)
                return {
                    "success": True,
                    "components": demo_components,
                    "company_name": company_name
                }
            else:
                return {"error": "Failed to generate demo components"}
            
        except Exception as e:
            logger.error(f"Error generating demo value components: {e}")
            return {"error": str(e)}
    
    async def generate_demo_customers(self, user_id: str) -> Dict[str, Any]:
        """Generate 3 demo customers based on company profile"""
        if not self.company_context:
            return {"error": "Company context not available"}
        
        try:
            from app.ai.gemini_client import gemini_client
            
            # Get company context
            company_name = self.company_context.get_company_name()
            core_business = self.company_context.get_core_business()
            target_customers = self.company_context.get_target_customers()
            industries_served = self.company_context.get_industries_served()
            
            # Create prompt for demo customers
            prompt = f"""
            Generate 3 realistic demo customer companies that would be potential customers for {company_name}.
            
            COMPANY PROFILE:
            - Company: {company_name}
            - Core Business: {core_business}
            - Target Customers: {', '.join(target_customers)}
            - Industries Served: {', '.join(industries_served)}
            
            Generate 3 different customer companies with:
            1. Different company sizes (small, medium, large)
            2. Different industries from the target industries
            3. Different pain points and needs
            4. Different decision-making processes
            5. Different value drivers
            
            For each customer, provide:
            - Company name and industry
            - Company size and location
            - Key pain points and challenges
            - Business goals and objectives
            - Decision-making process
            - Value drivers and priorities
            - Website URL (realistic but fictional)
            
            Return as JSON with this structure:
            {{
                "customers": [
                    {{
                        "company_name": "Customer Company 1",
                        "industry": "Industry",
                        "size": "Small/Medium/Large",
                        "location": "City, Country",
                        "pain_points": ["pain1", "pain2", "pain3"],
                        "goals": ["goal1", "goal2", "goal3"],
                        "decision_process": "Description of how they make decisions",
                        "value_drivers": ["driver1", "driver2", "driver3"],
                        "website": "https://customer1.com"
                    }},
                    {{
                        "company_name": "Customer Company 2",
                        "industry": "Industry",
                        "size": "Small/Medium/Large",
                        "location": "City, Country",
                        "pain_points": ["pain1", "pain2", "pain3"],
                        "goals": ["goal1", "goal2", "goal3"],
                        "decision_process": "Description of how they make decisions",
                        "value_drivers": ["driver1", "driver2", "driver3"],
                        "website": "https://customer2.com"
                    }},
                    {{
                        "company_name": "Customer Company 3",
                        "industry": "Industry",
                        "size": "Small/Medium/Large",
                        "location": "City, Country",
                        "pain_points": ["pain1", "pain2", "pain3"],
                        "goals": ["goal1", "goal2", "goal3"],
                        "decision_process": "Description of how they make decisions",
                        "value_drivers": ["driver1", "driver2", "driver3"],
                        "website": "https://customer3.com"
                    }}
                ]
            }}
            """
            
            # Generate with Gemini
            response = await gemini_client(prompt, temperature=0.3, max_tokens=4000)
            
            if response:
                # Parse and structure the response
                demo_customers = self._parse_demo_customers(response)
                return {
                    "success": True,
                    "customers": demo_customers,
                    "company_name": company_name
                }
            else:
                return {"error": "Failed to generate demo customers"}
            
        except Exception as e:
            logger.error(f"Error generating demo customers: {e}")
            return {"error": str(e)}
    
    def _parse_demo_components(self, response: str) -> Dict[str, Any]:
        """Parse demo components from AI response"""
        try:
            import json
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                # Fallback to default structure
                return self._get_default_demo_components()
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing demo components: {e}")
            return self._get_default_demo_components()
    
    def _parse_demo_customers(self, response: str) -> List[Dict[str, Any]]:
        """Parse demo customers from AI response"""
        try:
            import json
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                # Fallback to default structure
                return self._get_default_demo_customers()
            
            data = json.loads(json_str)
            return data.get("customers", [])
        except Exception as e:
            logger.error(f"Error parsing demo customers: {e}")
            return self._get_default_demo_customers()
    
    def _get_default_demo_components(self) -> Dict[str, Any]:
        """Get default demo components if AI generation fails"""
        return {
            "technical_value": {
                "quality": ["High-quality materials", "ISO certification"],
                "performance": ["Optimized performance", "Efficient operation"],
                "innovation": ["Latest technology", "Innovative solutions"],
                "reliability": ["Proven reliability", "Long-term durability"]
            },
            "business_value": {
                "cost_efficiency": ["Reduced operational costs", "Lower maintenance"],
                "roi": ["Quick ROI", "Long-term savings"],
                "productivity": ["Increased productivity", "Streamlined processes"],
                "scalability": ["Scalable solutions", "Growth support"]
            },
            "strategic_value": {
                "partnership": ["Strategic partnership", "Long-term relationship"],
                "growth": ["Growth support", "Market expansion"],
                "market_position": ["Market leadership", "Competitive advantage"],
                "competitive_advantage": ["Unique solutions", "Market differentiation"]
            },
            "after_sales_value": {
                "support": ["24/7 support", "Technical assistance"],
                "training": ["Comprehensive training", "Knowledge transfer"],
                "maintenance": ["Preventive maintenance", "Service contracts"],
                "service": ["Professional service", "Expert consultation"]
            }
        }
    
    def _get_default_demo_customers(self) -> List[Dict[str, Any]]:
        """Get default demo customers if AI generation fails"""
        return [
            {
                "company_name": "Tech Solutions Inc",
                "industry": "Technology",
                "size": "Medium",
                "location": "San Francisco, USA",
                "pain_points": ["High operational costs", "Inefficient processes"],
                "goals": ["Increase efficiency", "Reduce costs"],
                "decision_process": "Technical evaluation followed by business case",
                "value_drivers": ["ROI", "Performance", "Support"],
                "website": "https://techsolutions.com"
            },
            {
                "company_name": "Global Manufacturing Co",
                "industry": "Manufacturing",
                "size": "Large",
                "location": "Detroit, USA",
                "pain_points": ["Equipment downtime", "Maintenance costs"],
                "goals": ["Improve reliability", "Reduce downtime"],
                "decision_process": "Multi-department evaluation with budget approval",
                "value_drivers": ["Reliability", "Cost efficiency", "Partnership"],
                "website": "https://globalmanufacturing.com"
            },
            {
                "company_name": "Startup Innovations",
                "industry": "Startup",
                "size": "Small",
                "location": "Austin, USA",
                "pain_points": ["Limited resources", "Need for scalability"],
                "goals": ["Rapid growth", "Market expansion"],
                "decision_process": "Quick decision by founder/CTO",
                "value_drivers": ["Innovation", "Scalability", "Cost"],
                "website": "https://startupinnovations.com"
            }
        ]

# Global demo function instance
demo_generator = DynamicDemoGenerator()

async def populate_demo_data(user_id: str, preserve_existing: bool = True) -> Dict[str, Any]:
    """Populate demo data for the current company profile"""
    try:
        # Generate demo value components
        components_result = await demo_generator.generate_demo_value_components(user_id)
        
        # Generate demo customers
        customers_result = await demo_generator.generate_demo_customers(user_id)
        
        return {
            "success": True,
            "components": components_result,
            "customers": customers_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error populating demo data: {e}")
        return {"error": str(e)}

def update_session_state(components: Dict[str, Any], customers: Dict[str, Any]):
    """Update session state with demo data"""
    try:
        # Update session state for demo data
        st.session_state.demo_data_populated = True
        st.session_state.demo_components = components
        st.session_state.demo_customers = customers
        st.session_state.demo_timestamp = datetime.now().isoformat()
        
        logger.info("Demo data session state updated successfully")
    except Exception as e:
        logger.error(f"Error updating session state: {e}")

# Legacy function for backward compatibility
demo_function = type('DemoFunction', (), {
    'populate_demo_data': populate_demo_data,
    'update_session_state': update_session_state
})()
