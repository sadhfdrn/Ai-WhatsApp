"""
Web Search Handler using Whoogle for privacy-focused searches
Includes fallback search methods and content extraction
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import urlencode, quote_plus
import trafilatura

logger = logging.getLogger(__name__)

class WebSearchHandler:
    """Web search handler with Whoogle integration"""
    
    def __init__(self, config):
        self.config = config
        self.whoogle_url = config.WHOOGLE_URL
        self.max_results = config.MAX_SEARCH_RESULTS
        self.timeout = 10
        
        # Fallback search engines
        self.fallback_engines = [
            "https://search.benbusby.com",  # Alternative Whoogle instance
            "https://whoogle.sdf.org",     # Another public instance
        ]
        
        # Request headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        logger.info("🔍 Web search handler initialized")
    
    async def search(self, query: str, num_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Perform web search using Whoogle"""
        try:
            if not query.strip():
                logger.warning("⚠️ Empty search query provided")
                return []
            
            num_results = num_results or self.max_results
            logger.info(f"🔍 Searching for: {query}")
            
            # Try primary Whoogle instance first
            results = await self.search_whoogle(query, num_results)
            
            if not results:
                # Try fallback instances
                for fallback_url in self.fallback_engines:
                    logger.info(f"🔄 Trying fallback search engine: {fallback_url}")
                    results = await self.search_whoogle(query, num_results, fallback_url)
                    if results:
                        break
            
            if results:
                logger.info(f"✅ Found {len(results)} search results")
                # Enhance results with content extraction
                enhanced_results = await self.enhance_search_results(results)
                return enhanced_results
            else:
                logger.warning("⚠️ No search results found")
                return []
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    async def search_whoogle(self, query: str, num_results: int, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search using Whoogle instance"""
        try:
            search_url = base_url or self.whoogle_url
            
            # Construct search URL
            search_params = {
                'q': query,
                'num': min(num_results, 20)  # Whoogle limit
            }
            
            url = f"{search_url}/search?{urlencode(search_params)}"
            
            # Make request
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse results
            results = await self.parse_whoogle_results(response.text, num_results)
            return results
            
        except requests.RequestException as e:
            logger.error(f"❌ Whoogle search request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Whoogle search error: {e}")
            return []
    
    async def parse_whoogle_results(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse Whoogle search results HTML"""
        try:
            results = []
            
            # Simple regex-based parsing for Whoogle results
            # In a production environment, consider using BeautifulSoup for more robust parsing
            
            # Pattern to match search result divs
            result_pattern = r'<div class="g">.*?<h3.*?><a href="([^"]+)"[^>]*>([^<]+)</a></h3>.*?<span class="st">([^<]*)</span>'
            matches = re.finditer(result_pattern, html, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                if len(results) >= max_results:
                    break
                
                url = match.group(1)
                title = match.group(2)
                snippet = match.group(3)
                
                # Clean up the extracted data
                url = url.replace('/url?q=', '').split('&')[0]  # Remove tracking parameters
                title = re.sub(r'<[^>]+>', '', title).strip()  # Remove HTML tags
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()  # Remove HTML tags
                
                if url and title:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet or 'No description available',
                        'source': 'whoogle'
                    })
            
            # If regex parsing fails, try alternative patterns
            if not results:
                results = await self.fallback_html_parsing(html, max_results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ HTML parsing error: {e}")
            return []
    
    async def fallback_html_parsing(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback HTML parsing method"""
        try:
            results = []
            
            # Try simpler pattern matching
            link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<span[^>]*>([^<]*)</span>'
            
            links = re.findall(link_pattern, html)
            snippets = re.findall(snippet_pattern, html)
            
            for i, (url, title) in enumerate(links[:max_results]):
                if url.startswith('http') and not url.startswith(self.whoogle_url):
                    snippet = snippets[i] if i < len(snippets) else 'No description available'
                    
                    results.append({
                        'title': title.strip(),
                        'url': url,
                        'snippet': snippet.strip(),
                        'source': 'whoogle_fallback'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Fallback parsing error: {e}")
            return []
    
    async def enhance_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance search results with additional content extraction"""
        try:
            enhanced_results = []
            
            for result in results:
                enhanced_result = result.copy()
                
                # Extract additional content from the page
                try:
                    page_content = await self.extract_page_content(result['url'])
                    if page_content:
                        enhanced_result['content_preview'] = page_content[:200] + "..."
                        enhanced_result['has_content'] = True
                    else:
                        enhanced_result['has_content'] = False
                        
                except Exception as e:
                    logger.warning(f"⚠️ Content extraction failed for {result['url']}: {e}")
                    enhanced_result['has_content'] = False
                
                enhanced_results.append(enhanced_result)
                
                # Small delay to be respectful to servers
                await asyncio.sleep(0.1)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"❌ Result enhancement error: {e}")
            return results  # Return original results if enhancement fails
    
    async def extract_page_content(self, url: str) -> Optional[str]:
        """Extract clean text content from a webpage using trafilatura"""
        try:
            # Use trafilatura for content extraction
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                return text
            return None
            
        except Exception as e:
            logger.error(f"❌ Content extraction error for {url}: {e}")
            return None
    
    async def search_news(self, query: str, num_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for news articles"""
        try:
            news_query = f"news {query}"
            results = await self.search(news_query, num_results)
            
            # Filter for news sources
            news_sources = ['bbc', 'cnn', 'reuters', 'ap', 'guardian', 'times', 'post', 'news']
            news_results = []
            
            for result in results:
                url_lower = result['url'].lower()
                title_lower = result['title'].lower()
                
                if any(source in url_lower or source in title_lower for source in news_sources):
                    result['category'] = 'news'
                    news_results.append(result)
            
            return news_results
            
        except Exception as e:
            logger.error(f"❌ News search error: {e}")
            return []
    
    async def search_with_date_filter(self, query: str, time_filter: str = "week") -> List[Dict[str, Any]]:
        """Search with time-based filter"""
        try:
            # Add time filter to query
            time_queries = {
                'hour': f"{query} past hour",
                'day': f"{query} past 24 hours",
                'week': f"{query} past week", 
                'month': f"{query} past month",
                'year': f"{query} past year"
            }
            
            filtered_query = time_queries.get(time_filter, query)
            return await self.search(filtered_query)
            
        except Exception as e:
            logger.error(f"❌ Date filtered search error: {e}")
            return []
    
    async def quick_fact_search(self, query: str) -> Optional[str]:
        """Quick search for factual information"""
        try:
            results = await self.search(f"what is {query}", 3)
            
            if results:
                # Try to extract a concise fact from the first result
                first_result = results[0]
                
                if first_result.get('has_content') and first_result.get('content_preview'):
                    content = first_result['content_preview']
                    # Look for definition-like sentences
                    sentences = content.split('. ')
                    
                    for sentence in sentences[:3]:
                        if any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'means']):
                            return f"{sentence.strip()}."
                
                # Fallback to snippet
                return first_result.get('snippet', 'No quick fact found')
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Quick fact search error: {e}")
            return None
    
    def format_search_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results for display"""
        try:
            if not results:
                return f"No results found for '{query}'. Try a different search term!"
            
            formatted = f"🔍 **Search Results for:** {query}\n\n"
            
            for i, result in enumerate(results[:5], 1):
                title = result['title'][:60] + "..." if len(result['title']) > 60 else result['title']
                snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
                
                formatted += f"{i}. **{title}**\n"
                formatted += f"   {snippet}\n"
                formatted += f"   🔗 {result['url']}\n\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"❌ Result formatting error: {e}")
            return f"Found results for '{query}' but couldn't format them properly."
