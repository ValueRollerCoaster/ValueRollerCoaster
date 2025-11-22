"""
Company website data enhancer for value components generation.
Integrates scraped website content with AI-generated value components.
"""

import logging
from typing import Dict, Any, List, Optional
from app.database_company_website import get_company_website_data
from app.config import ENABLE_COMPANY_WEBSITE_SCRAPING

logger = logging.getLogger(__name__)

class CompanyWebsiteEnhancer:
    """Enhances value components generation with company website data."""
    
    def __init__(self):
        self.website_data = None
        self._load_website_data()
    
    def _load_website_data(self):
        """Load company website data from database."""
        try:
            if ENABLE_COMPANY_WEBSITE_SCRAPING:
                self.website_data = get_company_website_data()
                if self.website_data:
                    logger.info("Company website data loaded successfully")
                else:
                    logger.info("No company website data available")
        except Exception as e:
            logger.error(f"Error loading company website data: {e}")
            self.website_data = None
    
    def has_website_data(self) -> bool:
        """Check if website data is available."""
        return self.website_data is not None
    
    def get_enhanced_prompts(self, base_prompts: Dict[str, str]) -> Dict[str, str]:
        """
        Enhance base prompts with company website data.
        
        Args:
            base_prompts: Dictionary of base prompts for value components
            
        Returns:
            Enhanced prompts with website context
        """
        if not self.has_website_data():
            logger.info("No website data available, using base prompts")
            return base_prompts
        
        try:
            if not self.website_data:
                return base_prompts
            
            content = self.website_data.get('content', {})
            
            # Extract relevant content for each category
            company_overview = self._extract_company_overview(content)
            products_services = self._extract_products_services(content)
            value_propositions = self._extract_value_propositions(content)
            benefits = self._extract_benefits(content)
            features = self._extract_features(content)
            
            # Enhance prompts with website context
            enhanced_prompts = {}
            
            for category, base_prompt in base_prompts.items():
                enhanced_prompt = self._enhance_prompt_for_category(
                    category, base_prompt, {
                        'company_overview': company_overview,
                        'products_services': products_services,
                        'value_propositions': value_propositions,
                        'benefits': benefits,
                        'features': features
                    }
                )
                enhanced_prompts[category] = enhanced_prompt
            
            logger.info("Enhanced prompts with website data")
            return enhanced_prompts
            
        except Exception as e:
            logger.error(f"Error enhancing prompts with website data: {e}")
            return base_prompts
    
    def _extract_company_overview(self, content: Dict[str, Any]) -> str:
        """Extract company overview content."""
        overview_parts = []
        
        # Get about us content
        about_us = content.get('about_us', [])
        if about_us:
            overview_parts.extend(about_us[:3])  # First 3 paragraphs
        
        # Get company overview content
        company_overview = content.get('company_overview', [])
        if company_overview:
            overview_parts.extend(company_overview[:2])  # First 2 paragraphs
        
        return ' '.join(overview_parts)
    
    def _extract_products_services(self, content: Dict[str, Any]) -> str:
        """Extract products and services content."""
        products_services = content.get('products_services', [])
        return ' '.join(products_services[:3])  # First 3 items
    
    def _extract_value_propositions(self, content: Dict[str, Any]) -> str:
        """Extract value propositions content."""
        value_props = content.get('value_propositions', [])
        return ' '.join(value_props[:5])  # First 5 items
    
    def _extract_benefits(self, content: Dict[str, Any]) -> str:
        """Extract benefits content."""
        benefits = content.get('benefits', [])
        return ' '.join(benefits[:5])  # First 5 items
    
    def _extract_features(self, content: Dict[str, Any]) -> str:
        """Extract features content."""
        features = content.get('features', [])
        return ' '.join(features[:5])  # First 5 items
    
    def _enhance_prompt_for_category(self, category: str, base_prompt: str, website_context: Dict[str, str]) -> str:
        """Enhance a specific prompt with relevant website context."""
        
        # Map categories to relevant website content
        category_mapping = {
            'company_overview': ['company_overview', 'about_us'],
            'products_services': ['products_services', 'value_propositions'],
            'value_propositions': ['value_propositions', 'benefits'],
            'benefits': ['benefits', 'value_propositions'],
            'features': ['features', 'products_services'],
            'technical_value': ['features', 'products_services'],
            'business_value': ['value_propositions', 'benefits'],
            'strategic_value': ['company_overview', 'value_propositions'],
            'after_sales_value': ['benefits', 'value_propositions']
        }
        
        # Get relevant content for this category
        relevant_content = []
        for content_type in category_mapping.get(category, []):
            content_text = website_context.get(content_type, '')
            if content_text:
                relevant_content.append(content_text)
        
        if not relevant_content:
            return base_prompt
        
        # Create enhanced prompt
        website_context_text = ' '.join(relevant_content)
        
        enhanced_prompt = f"""
{base_prompt}

ADDITIONAL COMPANY CONTEXT FROM WEBSITE:
{website_context_text}

Use this additional context from the company's website to generate more accurate and relevant value components. 
Focus on the specific benefits, features, and value propositions mentioned on the website.
"""
        
        return enhanced_prompt.strip()
    
    def get_website_summary(self) -> Dict[str, Any]:
        """Get a summary of available website data."""
        if not self.has_website_data() or not self.website_data:
            return {
                'available': False,
                'message': 'No website data available'
            }
        
        content = self.website_data.get('content', {})
        
        return {
            'available': True,
            'website_url': self.website_data.get('website_url', 'Unknown'),
            'last_scraped': self.website_data.get('last_scraped_at', 'Unknown'),
            'pages_scraped': self.website_data.get('pages_scraped', 0),
            'total_words': self.website_data.get('total_words', 0),
            'content_categories': {
                'company_overview': len(content.get('company_overview', [])),
                'products_services': len(content.get('products_services', [])),
                'value_propositions': len(content.get('value_propositions', [])),
                'benefits': len(content.get('benefits', [])),
                'features': len(content.get('features', []))
            }
        }

def get_enhanced_prompts(base_prompts: Dict[str, str]) -> Dict[str, str]:
    """
    Main function to get enhanced prompts with website data.
    
    Args:
        base_prompts: Dictionary of base prompts for value components
        
    Returns:
        Enhanced prompts with website context
    """
    enhancer = CompanyWebsiteEnhancer()
    return enhancer.get_enhanced_prompts(base_prompts)

def get_website_enhancement_status() -> Dict[str, Any]:
    """
    Get the status of website enhancement capabilities.
    
    Returns:
        Dictionary with enhancement status information
    """
    enhancer = CompanyWebsiteEnhancer()
    return enhancer.get_website_summary()
