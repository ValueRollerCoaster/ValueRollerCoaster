"""
Company website scraper for extracting value proposition content.
Scrapes the company's own website to generate better initial value components.
"""

import logging
import hashlib
import re
import asyncio
from typing import Dict, Any, List, Optional, cast
from bs4 import Tag
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
import streamlit as st

logger = logging.getLogger(__name__)

class CompanyWebsiteScraper:
    """Scraper for extracting value proposition content from company websites."""
    
    def __init__(self):
        self.session = None
        self.base_url = None
        self.scraped_content = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted elements
        text = re.sub(r'[^\w\s.,!?;:()\-&]', '', text)
        
        return text
    
    def _extract_text_from_element(self, element) -> str:
        """Extract clean text from BeautifulSoup element."""
        if not element:
            return ""
        
        # Remove script and style elements
        for script in element(["script", "style"]):
            script.decompose()
        
        text = element.get_text()
        return self._clean_text(text)
    
    def _is_relevant_page(self, url: str, title: str, content: str) -> bool:
        """Check if a page is relevant for value proposition extraction."""
        # Skip pages that are clearly not relevant
        skip_keywords = [
            'login', 'register', 'signup', 'signin', 'logout', 'admin',
            'cart', 'checkout', 'payment', 'billing', 'account',
            'privacy', 'terms', 'legal', 'cookie', 'sitemap',
            '404', 'error', 'not-found', 'search', 'contact'
        ]
        
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Skip pages with irrelevant keywords
        if any(keyword in url_lower or keyword in title_lower for keyword in skip_keywords):
            return False
        
        # Check content length (should have some content)
        content_substantial = len(content) > 50  # Reduced from 200 to 50
        
        # For homepage, be more lenient
        is_homepage = url_lower.endswith('/') or url_lower.count('/') <= 3
        
        if is_homepage:
            return content_substantial  # Homepage just needs some content
        
        # For other pages, check for business-relevant content
        business_keywords = [
            'about', 'company', 'services', 'products', 'solutions',
            'value', 'benefits', 'why', 'features', 'capabilities',
            'mission', 'vision', 'expertise', 'experience', 'team',
            'what', 'how', 'our', 'we', 'business', 'industry'
        ]
        
        # Check URL, title, or content for business keywords
        has_business_content = any(
            keyword in url_lower or 
            keyword in title_lower or 
            keyword in content_lower 
            for keyword in business_keywords
        )
        
        return content_substantial and has_business_content
    
    async def _scrape_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single page and extract relevant content."""
        try:
            logger.info(f"Scraping page: {url}")
            
            if not self.session:
                logger.error("Session not initialized")
                return None
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic page info
            title = self._extract_text_from_element(soup.find('title'))
            description = self._extract_text_from_element(soup.find('meta', attrs={'name': 'description'}))
            
            # Extract main content
            main_content = ""
            
            # Try to find main content areas
            content_selectors = [
                'main', 'article', '.content', '.main-content', 
                '.page-content', '#content', '.container'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    main_content = self._extract_text_from_element(element)
                    break
            
            # If no main content found, use body
            if not main_content:
                body = soup.find('body')
                if body:
                    main_content = self._extract_text_from_element(body)
            
            # Extract headings
            headings = []
            for level in range(1, 7):
                for heading in soup.find_all(f'h{level}'):
                    heading_text = self._extract_text_from_element(heading)
                    if heading_text:
                        headings.append({
                            'level': level,
                            'text': heading_text
                        })
            
            # Extract lists (often contain value propositions)
            lists = []
            for ul in soup.find_all(['ul', 'ol']):
                ul_tag = cast(Tag, ul)
                list_items = []
                for li in ul_tag.find_all('li'):
                    item_text = self._extract_text_from_element(li)
                    if item_text and len(item_text) > 10:  # Only meaningful items
                        list_items.append(item_text)
                
                if list_items:
                    lists.append({
                        'type': ul_tag.name,
                        'items': list_items
                    })
            
            # Extract paragraphs with substantial content
            paragraphs = []
            for p in soup.find_all('p'):
                p_text = self._extract_text_from_element(p)
                if p_text and len(p_text) > 50:  # Only substantial paragraphs
                    paragraphs.append(p_text)
            
            page_data = {
                'url': url,
                'title': title,
                'description': description,
                'main_content': main_content,
                'headings': headings,
                'lists': lists,
                'paragraphs': paragraphs,
                'word_count': len(main_content.split()),
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Successfully scraped {url}: {page_data['word_count']} words")
            return page_data
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return None
    
    async def _discover_pages(self, base_url: str) -> List[str]:
        """Discover relevant pages to scrape from the website."""
        try:
            logger.info(f"Discovering pages from {base_url}")
            
            if not self.session:
                logger.error("Session not initialized")
                return [base_url]
            
            response = await self.session.get(base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pages_to_scrape = [base_url]  # Always include homepage
            
            # Find internal links
            for link in soup.find_all('a', href=True):
                link_tag = cast(Tag, link)
                href_attr = link_tag.get('href')
                if not href_attr:
                    continue
                
                # Handle href as string or list
                href = href_attr if isinstance(href_attr, str) else str(href_attr)
                full_url = urljoin(base_url, href)
                
                # Only process internal links
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    # Skip common non-content pages
                    skip_patterns = [
                        'mailto:', 'tel:', '#', 'javascript:', 'pdf', 'doc', 'docx',
                        'jpg', 'jpeg', 'png', 'gif', 'css', 'js', 'xml'
                    ]
                    
                    href_lower = href.lower() if isinstance(href, str) else str(href).lower()
                    if not any(pattern in href_lower for pattern in skip_patterns):
                        pages_to_scrape.append(full_url)
            
            # Remove duplicates and limit to reasonable number
            unique_pages = list(set(pages_to_scrape))[:10]  # Limit to 10 pages max
            
            logger.info(f"Found {len(unique_pages)} pages to scrape")
            return unique_pages
            
        except Exception as e:
            logger.error(f"Error discovering pages: {e}")
            return [base_url]  # Fallback to just homepage
    
    async def scrape_website(self, website_url: str) -> Dict[str, Any]:
        """
        Scrape the company website and extract value proposition content.
        
        Args:
            website_url: The company's website URL
            
        Returns:
            Dict containing scraped content organized by category
        """
        try:
            logger.info(f"Starting website scrape for {website_url}")
            
            self.base_url = website_url
            
            # Discover pages to scrape
            pages_to_scrape = await self._discover_pages(website_url)
            logger.info(f"Discovered {len(pages_to_scrape)} pages to scrape: {pages_to_scrape}")
            
            # Scrape each page
            scraped_pages = []
            for page_url in pages_to_scrape:
                logger.info(f"Processing page: {page_url}")
                page_data = await self._scrape_page(page_url)
                
                if page_data:
                    title = page_data.get('title', '')
                    content = page_data.get('main_content', '')
                    word_count = page_data.get('word_count', 0)
                    
                    logger.info(f"Page data: title='{title[:50]}...', content_length={len(content)}, words={word_count}")
                    
                    is_relevant = self._is_relevant_page(page_url, title, content)
                    logger.info(f"Page relevance check: {is_relevant}")
                    
                    if is_relevant:
                        scraped_pages.append(page_data)
                        logger.info(f"✅ Page added to scraped pages: {page_url}")
                    else:
                        logger.info(f"❌ Page filtered out: {page_url}")
                else:
                    logger.warning(f"❌ Failed to scrape page: {page_url}")
            
            # If no pages were scraped, try to scrape just the homepage with relaxed filtering
            if not scraped_pages:
                logger.warning("No pages were scraped with normal filtering. Trying homepage with relaxed filtering...")
                homepage_data = await self._scrape_page(website_url)
                if homepage_data:
                    # Force include homepage even if it doesn't meet relevance criteria
                    scraped_pages.append(homepage_data)
                    logger.info(f"✅ Added homepage with relaxed filtering: {website_url}")
            
            # Organize content by category
            organized_content = self._organize_content(scraped_pages)
            
            # Generate content hash for change detection
            content_hash = self._generate_content_hash(organized_content)
            
            result = {
                'website_url': website_url,
                'scraped_at': datetime.utcnow().isoformat(),
                'content_hash': content_hash,
                'pages_scraped': len(scraped_pages),
                'total_words': sum(page.get('word_count', 0) for page in scraped_pages),
                'content': organized_content
            }
            
            logger.info(f"Website scrape completed: {result['pages_scraped']} pages, {result['total_words']} words")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping website {website_url}: {e}")
            raise
    
    def _organize_content(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize scraped content into categories for value components generation."""
        organized = {
            'company_overview': [],
            'products_services': [],
            'value_propositions': [],
            'benefits': [],
            'features': [],
            'testimonials': [],
            'about_us': []
        }
        
        for page in pages:
            content = page.get('main_content', '')
            title = page.get('title', '')
            url = page.get('url', '')
            paragraphs = page.get('paragraphs', [])
            headings = page.get('headings', [])
            lists = page.get('lists', [])
            
            # Combine all content sources for better categorization
            all_content = []
            all_content.extend(paragraphs)
            all_content.extend([h['text'] for h in headings if h.get('text')])
            all_content.extend([item for list_data in lists for item in list_data.get('items', [])])
            
            # Add main content chunks (split by sentences)
            if content:
                sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
                all_content.extend(sentences)
            
            # Categorize based on URL patterns first
            if any(keyword in url.lower() for keyword in ['about', 'company', 'mission', 'vision', 'team']):
                organized['about_us'].extend(all_content)
            elif any(keyword in url.lower() for keyword in ['products', 'services', 'solutions', 'applications']):
                organized['products_services'].extend(all_content)
            elif any(keyword in url.lower() for keyword in ['benefits', 'value', 'why', 'advantages']):
                organized['value_propositions'].extend(all_content)
            else:
                # Categorize based on content keywords
                content_lower = content.lower()
                title_lower = title.lower()
                
                # Check for benefits and value propositions
                if any(keyword in content_lower or keyword in title_lower 
                      for keyword in ['benefit', 'advantage', 'value', 'why choose', 'advantage', 'superior', 'better']):
                    organized['benefits'].extend(all_content)
                
                # Check for features and capabilities
                if any(keyword in content_lower or keyword in title_lower 
                      for keyword in ['feature', 'capability', 'function', 'specification', 'technology', 'innovation']):
                    organized['features'].extend(all_content)
                
                # Check for value propositions
                if any(keyword in content_lower or keyword in title_lower 
                      for keyword in ['solution', 'deliver', 'provide', 'offer', 'ensure', 'guarantee']):
                    organized['value_propositions'].extend(all_content)
                
                # Check for company overview
                if any(keyword in content_lower or keyword in title_lower 
                      for keyword in ['company', 'about', 'overview', 'mission', 'vision', 'expertise', 'experience']):
                    organized['company_overview'].extend(all_content)
                
                # If no specific category matched, add to company overview
                if not any([
                    any(keyword in content_lower or keyword in title_lower 
                        for keyword in ['benefit', 'advantage', 'value', 'why choose', 'advantage', 'superior', 'better']),
                    any(keyword in content_lower or keyword in title_lower 
                        for keyword in ['feature', 'capability', 'function', 'specification', 'technology', 'innovation']),
                    any(keyword in content_lower or keyword in title_lower 
                        for keyword in ['solution', 'deliver', 'provide', 'offer', 'ensure', 'guarantee']),
                    any(keyword in content_lower or keyword in title_lower 
                        for keyword in ['company', 'about', 'overview', 'mission', 'vision', 'expertise', 'experience'])
                ]):
                    organized['company_overview'].extend(all_content)
            
            # Extract lists as potential value propositions and benefits
            for list_data in lists:
                list_items = list_data.get('items', [])
                list_text = ' '.join(list_items).lower()
                
                if any(keyword in list_text for keyword in ['benefit', 'advantage', 'value', 'why', 'superior']):
                    organized['benefits'].extend(list_items)
                elif any(keyword in list_text for keyword in ['feature', 'capability', 'function', 'specification']):
                    organized['features'].extend(list_items)
                elif any(keyword in list_text for keyword in ['solution', 'deliver', 'provide', 'offer']):
                    organized['value_propositions'].extend(list_items)
                else:
                    # Default to value propositions for general lists
                    organized['value_propositions'].extend(list_items)
        
        # Clean and deduplicate content
        for category in organized:
            organized[category] = list(set([
                self._clean_text(item) for item in organized[category] 
                if item and len(item.strip()) > 20
            ]))
        
        return organized
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate a hash of the content for change detection."""
        content_str = str(content)
        return hashlib.md5(content_str.encode()).hexdigest()

async def scrape_company_website(website_url: str) -> Dict[str, Any]:
    """
    Main function to scrape a company website.
    
    Args:
        website_url: The company's website URL
        
    Returns:
        Dict containing scraped and organized content
    """
    async with CompanyWebsiteScraper() as scraper:
        return await scraper.scrape_website(website_url)

# Import datetime at the top
from datetime import datetime
