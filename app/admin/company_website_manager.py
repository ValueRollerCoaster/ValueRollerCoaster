"""
Admin UI for managing company website data.
Provides interface for setting website URL and triggering website scraping.
"""

import streamlit as st
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.database_company_website import (
    save_company_website_data, 
    get_company_website_data, 
    get_company_website_info,
    update_company_website_data,
    delete_company_website_data
)
from app.company_website_scraper import scrape_company_website
from app.config import COMPANY_WEBSITE_URL, ENABLE_COMPANY_WEBSITE_SCRAPING

logger = logging.getLogger(__name__)

class CompanyWebsiteManager:
    """Manager for company website data in admin interface."""
    
    def __init__(self):
        self.website_url = ""
        self.website_data = None
        
    def render_website_settings(self):
        """Render the company website settings section."""
        st.subheader("🌐 Company Website Settings")
        
        # Get current website data
        self.website_data = get_company_website_data()
        
        # Website URL input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            current_url = self.website_data.get('website_url', '') if self.website_data else COMPANY_WEBSITE_URL
            self.website_url = st.text_input(
                "Company Website URL",
                value=current_url,
                help="Enter your company's website URL for content extraction",
                placeholder="https://www.yourcompany.com"
            )
        
        with col2:
            if st.button("💾 Save URL", type="primary"):
                self._save_website_url()
        
        # Display current status
        self._render_website_status()
        
        # Website scraping controls
        self._render_scraping_controls()
        
        # Website data preview
        self._render_data_preview()
    
    def _save_website_url(self):
        """Save the website URL to configuration."""
        if not self.website_url:
            st.error("❌ Please enter a website URL")
            return
        
        if not self._is_valid_url(self.website_url):
            st.error("❌ Please enter a valid URL (e.g., https://www.example.com)")
            return
        
        try:
            # Update the configuration (in a real app, this would be saved to a config file or database)
            st.success(f"✅ Website URL saved: {self.website_url}")
            st.info("💡 Note: In a production environment, this would be saved to your configuration file.")
            
        except Exception as e:
            st.error(f"❌ Error saving website URL: {e}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if the URL is properly formatted."""
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return pattern.match(url) is not None
    
    def _render_website_status(self):
        """Render the current website status."""
        if not self.website_data:
            st.info("ℹ️ No website data found. Click 'Scrape Website' to extract content.")
            return
        
        # Display status information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Website URL", self.website_data.get('website_url', 'N/A'))
        
        with col2:
            last_scraped = self.website_data.get('last_scraped_at', 'Never')
            if last_scraped != 'Never':
                try:
                    last_scraped_dt = datetime.fromisoformat(last_scraped.replace('Z', '+00:00'))
                    last_scraped = last_scraped_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            st.metric("Last Scraped", last_scraped)
        
        with col3:
            pages_count = self.website_data.get('pages_scraped', 0)
            st.metric("Pages Scraped", pages_count)
    
    def _render_scraping_controls(self):
        """Render the website scraping controls."""
        st.markdown("---")
        st.subheader("🔍 Website Content Extraction")
        
        if not ENABLE_COMPANY_WEBSITE_SCRAPING:
            st.warning("⚠️ Website scraping is disabled in configuration.")
            return
        
        if not self.website_url:
            st.info("ℹ️ Please enter a website URL above before scraping.")
            return
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🌐 Scrape Website", type="primary", help="Extract content from the company website"):
                self._scrape_website()
        
        with col2:
            if st.button("🔄 Refresh Data", help="Re-scrape the website with fresh data"):
                self._scrape_website(force_refresh=True)
        
        with col3:
            if st.button("🗑️ Clear Data", help="Delete all scraped website data"):
                self._clear_website_data()
    
    def _scrape_website(self, force_refresh: bool = False):
        """Scrape the company website."""
        if not self.website_url:
            st.error("❌ Please enter a website URL first")
            return
        
        try:
            with st.spinner("🌐 Scraping website content... This may take a few minutes."):
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔍 Discovering pages...")
                progress_bar.progress(20)
                
                # Scrape the website
                scraped_data = asyncio.run(scrape_company_website(self.website_url))
                
                # Debug: Show scraping results
                st.write(f"**Debug Info:**")
                st.write(f"- Pages scraped: {scraped_data.get('pages_scraped', 0)}")
                st.write(f"- Total words: {scraped_data.get('total_words', 0)}")
                st.write(f"- Content categories: {list(scraped_data.get('content', {}).keys())}")
                
                status_text.text("💾 Saving data...")
                progress_bar.progress(80)
                
                # Save to database
                if force_refresh or not self.website_data:
                    success = save_company_website_data(
                        self.website_url,
                        scraped_data,
                        scraped_data.get('content_hash', '')
                    )
                else:
                    success = update_company_website_data(
                        self.website_url,
                        scraped_data,
                        scraped_data.get('content_hash', '')
                    )
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                
                if success:
                    st.success(f"✅ Successfully scraped {scraped_data.get('pages_scraped', 0)} pages with {scraped_data.get('total_words', 0)} words")
                    st.rerun()
                else:
                    st.error("❌ Failed to save scraped data")
                
        except Exception as e:
            st.error(f"❌ Error scraping website: {e}")
            logger.error(f"Website scraping error: {e}")
    
    def _clear_website_data(self):
        """Clear all website data."""
        try:
            if delete_company_website_data():
                st.success("✅ Website data cleared successfully")
                st.rerun()
            else:
                st.error("❌ Failed to clear website data")
        except Exception as e:
            st.error(f"❌ Error clearing website data: {e}")
    
    def _render_data_preview(self):
        """Render a preview of the scraped website data."""
        if not self.website_data:
            return
        
        st.markdown("---")
        st.subheader("📊 Scraped Content Preview")
        
        content = self.website_data.get('content', {})
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Words", self.website_data.get('total_words', 0))
        
        with col2:
            st.metric("Pages Scraped", self.website_data.get('pages_scraped', 0))
        
        with col3:
            categories = len([k for k, v in content.items() if isinstance(v, list) and v])
            st.metric("Content Categories", categories)
        
        # Show content by category
        with st.expander("📋 View Content by Category", expanded=False):
            for category, items in content.items():
                if isinstance(items, list) and items:
                    st.write(f"**{category.replace('_', ' ').title()}** ({len(items)} items)")
                    
                    # Show first few items
                    for i, item in enumerate(items[:3]):
                        st.write(f"• {item[:200]}{'...' if len(item) > 200 else ''}")
                    
                    if len(items) > 3:
                        st.write(f"... and {len(items) - 3} more items")
                    
                    st.write("---")

def render_company_website_admin():
    """Main function to render the company website admin interface."""
    manager = CompanyWebsiteManager()
    manager.render_website_settings()
