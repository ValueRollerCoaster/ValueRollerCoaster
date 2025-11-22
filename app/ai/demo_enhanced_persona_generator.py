"""
Demo Enhanced Persona Generator
Handles demo persona generation with realistic but fictional data.
"""

import asyncio
import json
import logging
import time
import streamlit as st
from typing import Dict, Any, Optional, List, Tuple
from app.components.demo_companies.company_data import DEMO_COMPANIES
from app.ai.demo_persona_generator import DemoPersonaGenerator

logger = logging.getLogger(__name__)

class DemoEnhancedPersonaGenerator:
    """Enhanced demo persona generator for fictional companies and customers."""
    
    def __init__(self):
        self.demo_generator = DemoPersonaGenerator()
        logger.info("[DemoEnhancedPersonaGenerator] Initialized")
    
    async def generate_demo_persona(self, website: str, selected_industry: Optional[str] = None, 
                                   pid: int = 0, progress_tracker = None) -> Dict[str, Any]:
        """
        Generate demo persona using demo-specific prompts and logic.
        
        Args:
            website: Demo website URL (e.g., "demo://customer_id")
            selected_industry: Industry classification
            pid: Process ID for logging
            progress_tracker: Progress tracking object
            
        Returns:
            Demo persona with fictional but realistic data
        """
        logger.info(f"[PID {pid}] [Demo Enhanced Persona Generator] Starting demo persona generation for: {website}")
        
        try:
            # Extract demo customer ID
            demo_customer_id = website.replace("demo://", "")
            
            # Find the demo customer
            demo_customer = self._find_demo_customer(demo_customer_id)
            
            if not demo_customer:
                logger.error(f"[PID {pid}] Demo customer not found: {demo_customer_id}")
                return {
                    "error": f"Demo customer not found: {demo_customer_id}",
                    "demo_mode": True
                }
            
            logger.info(f"[PID {pid}] Found demo customer: {demo_customer.get('company_name', 'Unknown')}")
            
            # Update progress
            if progress_tracker:
                await progress_tracker.start_step(0)
                await progress_tracker.update_progress(10, "Analyzing demo customer profile...")
            
            # Get demo context and prompts
            demo_context = self.demo_generator.get_demo_context()
            user_id = st.session_state.get("user_id", "default_user")
            persona_prompt = self.demo_generator.format_demo_persona_prompt(demo_customer, user_id)
            market_intelligence_prompt = self.demo_generator.format_demo_market_intelligence_prompt(user_id)
            
            # Update progress
            if progress_tracker:
                await progress_tracker.update_progress(20, "Generating market intelligence...")
            
            # Generate market intelligence using demo prompts
            market_intelligence = await self._generate_demo_market_intelligence(
                market_intelligence_prompt, demo_context, pid
            )
            
            # Update progress
            if progress_tracker:
                await progress_tracker.update_progress(40, "Generating buyer persona...")
            
            # Generate buyer persona using demo prompts
            buyer_persona = await self._generate_demo_buyer_persona(
                persona_prompt, demo_context, demo_customer, pid
            )
            
            # Update progress
            if progress_tracker:
                await progress_tracker.update_progress(60, "Running value alignment workflow...")
            
            # Run value alignment workflow with demo context
            value_alignment = await self._generate_demo_value_alignment(demo_customer, pid)
            
            # Update progress
            if progress_tracker:
                await progress_tracker.update_progress(80, "Finalizing demo persona...")
            
            # Create a complete demo persona structure
            demo_persona = self._create_demo_persona_structure(demo_customer, demo_customer_id)
            
            # Update progress
            if progress_tracker:
                await progress_tracker.update_progress(100, "Demo persona generation complete!")
            
            logger.info(f"[PID {pid}] [Demo Enhanced Persona Generator] Successfully generated demo persona for: {demo_customer.get('company_name')}")
            return demo_persona
            
        except Exception as e:
            logger.error(f"[PID {pid}] [Demo Enhanced Persona Generator] Error: {e}")
            return {
                "error": f"Demo persona generation failed: {str(e)}",
                "demo_mode": True
            }
    
    def _find_demo_customer(self, demo_customer_id: str) -> Optional[Dict[str, Any]]:
        """Find demo customer by ID."""
        for company in DEMO_COMPANIES.values():
            for customer in company.get('demo_customers', []):
                if customer.get('id') == demo_customer_id:
                    return customer
        return None
    
    def _create_demo_persona_structure(self, demo_customer: Dict[str, Any], demo_customer_id: str) -> Dict[str, Any]:
        """Create complete demo persona structure."""
        return {
            # Basic company info
            "company_name": demo_customer.get('company_name', 'Demo Customer'),
            "industry": demo_customer.get('industry', 'Technology'),
            "website": demo_customer.get('website', 'https://demo-company.com'),
            "year_established": "2020",
            "headquarters_location": demo_customer.get('location', 'Global'),
            
            # Company profile
            "company": {
                "name": demo_customer.get('company_name', 'Demo Customer'),
                "website": demo_customer.get('website', 'https://demo-company.com'),
                "year_established": "2020",
                "headquarters_location": demo_customer.get('location', 'Global')
            },
            
            # Product and service information
            "product_range": [
                f"Demo products for {demo_customer.get('industry', 'Technology')} industry",
                "Custom solutions for demo customers",
                "Demo service offerings"
            ],
            "services": [
                f"Demo consulting services for {demo_customer.get('industry', 'Technology')}",
                "Demo implementation support",
                "Demo training and onboarding"
            ],
            
            # Business strategy
            "goals": [
                f"Expand {demo_customer.get('industry', 'Technology')} market presence",
                "Increase demo customer satisfaction",
                "Grow demo revenue streams"
            ],
            "value_drivers": [
                "Demo cost savings",
                "Demo efficiency improvements", 
                "Demo competitive advantages"
            ],
            "value_signals": [
                "Demo market trends",
                "Demo customer feedback",
                "Demo performance metrics"
            ],
            
            # Pain points and objections
            "pain_points": [
                f"Demo challenges in {demo_customer.get('industry', 'Technology')} sector",
                "Demo operational inefficiencies",
                "Demo market competition"
            ],
            "likely_objections": [
                "Demo pricing concerns",
                "Demo implementation timeline",
                "Demo ROI expectations"
            ],
            
            # Market intelligence with proper structure for Industry Context tab
            "market_intelligence": self._create_demo_market_intelligence(demo_customer),
            
            "industry_context": {
                "market_overview": "Demo market analysis for fictional industry",
                "trends": ["Demo trend 1", "Demo trend 2", "Demo trend 3"],
                "opportunities": ["Demo opportunity 1", "Demo opportunity 2"]
            },
            
            # Value alignment with realistic demo data
            "advanced_value_alignment": {
                "alignment_matrix": self._create_demo_alignment_matrix(demo_customer)
            },
            
            # Demo metadata
            "demo_mode": True,
            "demo_customer_id": demo_customer_id,
            "demo_customer_name": demo_customer.get('company_name', 'Demo Customer'),
            "generation_context": "demo_fictional",
            "ai_prompts_used": "demo_specific",
            "metadata": self.demo_generator.get_demo_persona_metadata(demo_customer)
        }
    
    def _create_demo_market_intelligence(self, demo_customer: Dict[str, Any]) -> Dict[str, Any]:
        """Create demo market intelligence structure."""
        return {
            "market_overview": {
                "market_size": {
                    "global": "$50B+",
                    "european": "$15B+"
                },
                "growth_rate": "8-12% annually",
                "projection_5y": "Expected to reach $75B+ by 2029",
                "key_segments": [
                    f"Primary {demo_customer.get('industry', 'Technology')} segment",
                    "Secondary market opportunities",
                    "Emerging market segments"
                ]
            },
            "current_trends": [
                {
                    "trend": f"Digital transformation in {demo_customer.get('industry', 'Technology')}",
                    "description": "Industry-wide shift towards digital solutions and automation",
                    "impact": "High",
                    "business_implications": "Increased demand for technology solutions and consulting services"
                },
                {
                    "trend": "Sustainability and ESG focus",
                    "description": "Growing emphasis on environmental and social responsibility",
                    "impact": "Medium",
                    "business_implications": "New opportunities for green technology and sustainable practices"
                },
                {
                    "trend": "Remote and hybrid work models",
                    "description": "Permanent shift towards flexible work arrangements",
                    "impact": "High",
                    "business_implications": "Increased need for cloud-based solutions and collaboration tools"
                }
            ],
            "competitive_landscape": {
                "key_competitors": [
                    {
                        "name": "Demo Competitor A",
                        "positioning": "Premium solution provider",
                        "market_share": "25%"
                    },
                    {
                        "name": "Demo Competitor B", 
                        "positioning": "Cost-effective alternative",
                        "market_share": "20%"
                    },
                    {
                        "name": "Demo Competitor C",
                        "positioning": "Innovation leader",
                        "market_share": "15%"
                    }
                ],
                "competitive_advantages": [
                    "Superior customer service and support",
                    "Advanced technology integration",
                    "Flexible pricing models",
                    "Industry-specific expertise"
                ]
            }
        }
    
    def _create_demo_alignment_matrix(self, demo_customer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create demo alignment matrix with realistic data."""
        return [
            {
                "value_category": "Business Value",
                "subcategory": "Cost Savings",
                "component": "Operational Efficiency",
                "prospect_need": f"Reduce operational costs in {demo_customer.get('industry', 'Technology')}",
                "our_value_component": "Automated workflow optimization",
                "match_score_percent": 92,
                "rationale": "Our automation solutions directly address cost reduction needs",
                "conversation_starter": "How much time does your team currently spend on manual processes?"
            },
            {
                "value_category": "Business Value", 
                "subcategory": "Revenue Growth",
                "component": "Market Expansion",
                "prospect_need": f"Expand market reach in {demo_customer.get('industry', 'Technology')} sector",
                "our_value_component": "Scalable platform architecture",
                "match_score_percent": 88,
                "rationale": "Our platform enables rapid scaling to new markets",
                "conversation_starter": "What's your current market expansion strategy?"
            },
            {
                "value_category": "Strategic Value",
                "subcategory": "Competitive Advantage", 
                "component": "Innovation",
                "prospect_need": f"Stay ahead of competition in {demo_customer.get('industry', 'Technology')}",
                "our_value_component": "AI-powered insights and analytics",
                "match_score_percent": 85,
                "rationale": "Our AI capabilities provide significant competitive differentiation",
                "conversation_starter": "How do you currently track competitive intelligence?"
            },
            {
                "value_category": "Technical Value",
                "subcategory": "Performance",
                "component": "Speed and Scalability",
                "prospect_need": f"Handle increased {demo_customer.get('industry', 'Technology')} workload",
                "our_value_component": "High-performance cloud infrastructure",
                "match_score_percent": 90,
                "rationale": "Our infrastructure is designed for high-volume processing",
                "conversation_starter": "What's your current system's performance bottleneck?"
            },
            {
                "value_category": "After Sales Value",
                "subcategory": "Customer Support",
                "component": "Training and Onboarding",
                "prospect_need": f"Ensure team adoption of new {demo_customer.get('industry', 'Technology')} solutions",
                "our_value_component": "Comprehensive training and support program",
                "match_score_percent": 87,
                "rationale": "Our training program ensures successful implementation",
                "conversation_starter": "How do you typically handle team training for new systems?"
            },
            {
                "value_category": "Strategic Value",
                "subcategory": "Partnership Development",
                "component": "Strategic Roadmap Alignment",
                "prospect_need": f"Align technology with long-term {demo_customer.get('industry', 'Technology')} strategy",
                "our_value_component": "Strategic consulting and roadmap planning",
                "match_score_percent": 83,
                "rationale": "We provide strategic guidance aligned with your business goals",
                "conversation_starter": "What are your key strategic objectives for the next 3 years?"
            }
        ]
    
    async def _generate_demo_market_intelligence(self, prompt: str, demo_context: str, pid: int) -> Dict[str, Any]:
        """Generate market intelligence using demo-specific prompts."""
        try:
            # For demo mode, use fallback content to avoid AI client issues
            return {
                "market_analysis": "Demo market intelligence: This is a fictional demo scenario showing how the system analyzes market trends, competitive landscape, and business opportunities for demo companies.",
                "generated_by": "demo_fallback",
                "demo_context": True
            }
                
        except Exception as e:
            logger.error(f"[PID {pid}] Error generating demo market intelligence: {e}")
            return {
                "market_analysis": "Demo market intelligence (fallback)",
                "generated_by": "demo_fallback",
                "demo_context": True
            }
    
    async def _generate_demo_buyer_persona(self, prompt: str, demo_context: str, demo_customer: Dict[str, Any], pid: int) -> Dict[str, Any]:
        """Generate buyer persona using demo-specific prompts."""
        try:
            # For demo mode, use fallback content to avoid AI client issues
            customer_name = demo_customer.get('company_name', 'Demo Customer')
            industry = demo_customer.get('industry', 'Technology')
            size = demo_customer.get('size', 'Medium')
            location = demo_customer.get('location', 'Global')
            
            return {
                "persona_data": f"Demo buyer persona for {customer_name}: This is a fictional demo scenario showing how the system analyzes customer needs, pain points, and value drivers for {industry} companies in the {size} segment.",
                "generated_by": "demo_fallback",
                "demo_context": True,
                "customer_info": {
                    "name": customer_name,
                    "industry": industry,
                    "size": size,
                    "location": location
                }
            }
                
        except Exception as e:
            logger.error(f"[PID {pid}] Error generating demo buyer persona: {e}")
            return {
                "persona_data": "Demo buyer persona (fallback)",
                "generated_by": "demo_fallback",
                "demo_context": True,
                "customer_info": demo_customer
            }
    
    async def _generate_demo_value_alignment(self, demo_customer: Dict[str, Any], pid: int) -> Dict[str, Any]:
        """Generate value alignment for demo customer."""
        try:
            # Use demo-specific value alignment
            return {
                "alignment_score": 85,  # Demo score
                "key_matches": [
                    "Demo value proposition 1",
                    "Demo value proposition 2",
                    "Demo value proposition 3"
                ],
                "recommendations": [
                    "Focus on demo customer pain points",
                    "Highlight demo value propositions",
                    "Use demo-specific messaging"
                ],
                "generated_by": "demo_value_alignment",
                "demo_context": True
            }
            
        except Exception as e:
            logger.error(f"[PID {pid}] Error generating demo value alignment: {e}")
            return {
                "alignment_score": 75,
                "key_matches": ["Demo fallback matches"],
                "recommendations": ["Demo fallback recommendations"],
                "generated_by": "demo_fallback",
                "demo_context": True
            }

# Global instance
demo_enhanced_persona_generator = DemoEnhancedPersonaGenerator()
