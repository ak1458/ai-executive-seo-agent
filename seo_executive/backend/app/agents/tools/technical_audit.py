from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime

class TechnicalAudit:
    """Technical SEO audit tool using Playwright."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.visited_urls: Set[str] = set()
        self.results = []
    
    async def crawl(self, start_url: str, max_pages: int = 50) -> Dict[str, Any]:
        """
        Crawl website and perform technical audit.
        
        Args:
            start_url: Starting URL for crawl
            max_pages: Maximum pages to crawl
            
        Returns:
            Audit results
        """
        self.visited_urls = set()
        self.results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (compatible; SEOAuditBot/1.0)"
            )
            
            # Crawl starting from homepage
            to_visit = [start_url]
            domain = urlparse(start_url).netloc
            
            while to_visit and len(self.visited_urls) < max_pages:
                batch = to_visit[:self.max_concurrent]
                to_visit = to_visit[self.max_concurrent:]
                
                tasks = [self._audit_page(url, context, domain) for url in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        continue
                    if result:
                        self.results.append(result)
                        # Add new URLs to visit
                        for link in result.get("internal_links", []):
                            if link not in self.visited_urls and link not in to_visit:
                                to_visit.append(link)
            
            await browser.close()
        
        return self._compile_audit_results(start_url)
    
    async def _audit_page(self, url: str, context, domain: str) -> Optional[Dict[str, Any]]:
        """Audit a single page."""
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            page = await context.new_page()
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # Extract SEO elements
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_desc_content = meta_desc.get('content', '') if meta_desc else ""
            
            h1_tags = soup.find_all('h1')
            h2_tags = soup.find_all('h2')
            
            # Check images without alt
            images = soup.find_all('img')
            images_without_alt = [img.get('src', '') for img in images if not img.get('alt')]
            
            # Check canonical
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            canonical_url = canonical.get('href', '') if canonical else ""
            
            # Check schema markup
            schema_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
            has_schema = len(schema_scripts) > 0
            
            # Get internal links
            links = soup.find_all('a', href=True)
            internal_links = []
            for link in links:
                href = link.get('href', '')
                full_url = urljoin(url, href)
                if urlparse(full_url).netloc == domain:
                    internal_links.append(full_url)
            
            # Get status code
            status_code = response.status if response else 0
            
            await page.close()
            
            return {
                "url": url,
                "status_code": status_code,
                "title": title_text,
                "title_length": len(title_text),
                "meta_description": meta_desc_content,
                "meta_description_length": len(meta_desc_content),
                "h1_count": len(h1_tags),
                "h1_content": [h.get_text(strip=True) for h in h1_tags],
                "h2_count": len(h2_tags),
                "images_total": len(images),
                "images_without_alt": images_without_alt,
                "images_without_alt_count": len(images_without_alt),
                "canonical_url": canonical_url,
                "has_canonical": bool(canonical_url),
                "has_schema": has_schema,
                "internal_links": list(set(internal_links))[:20],  # Limit stored links
                "internal_links_count": len(set(internal_links))
            }
            
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "internal_links": []
            }
    
    def _compile_audit_results(self, base_url: str) -> Dict[str, Any]:
        """Compile audit results and identify issues."""
        issues = {
            "critical": [],
            "warnings": [],
            "info": []
        }
        
        total_pages = len(self.results)
        pages_without_title = 0
        pages_without_meta = 0
        pages_multiple_h1 = 0
        pages_missing_alt = 0
        pages_without_canonical = 0
        pages_without_schema = 0
        
        for result in self.results:
            if result.get("error"):
                issues["critical"].append({
                    "page": result["url"],
                    "issue": f"Page error: {result['error']}"
                })
                continue
            
            # Check title
            if not result.get("title"):
                pages_without_title += 1
                issues["critical"].append({
                    "page": result["url"],
                    "issue": "Missing title tag"
                })
            elif result.get("title_length", 0) > 60:
                issues["warnings"].append({
                    "page": result["url"],
                    "issue": f"Title too long ({result['title_length']} chars)"
                })
            
            # Check meta description
            if not result.get("meta_description"):
                pages_without_meta += 1
                issues["warnings"].append({
                    "page": result["url"],
                    "issue": "Missing meta description"
                })
            
            # Check H1
            if result.get("h1_count", 0) == 0:
                issues["warnings"].append({
                    "page": result["url"],
                    "issue": "Missing H1 tag"
                })
            elif result.get("h1_count", 0) > 1:
                pages_multiple_h1 += 1
                issues["warnings"].append({
                    "page": result["url"],
                    "issue": f"Multiple H1 tags ({result['h1_count']})"
                })
            
            # Check images
            if result.get("images_without_alt_count", 0) > 0:
                pages_missing_alt += 1
                if result["images_without_alt_count"] > 5:
                    issues["critical"].append({
                        "page": result["url"],
                        "issue": f"Many images without alt text ({result['images_without_alt_count']})"
                    })
                else:
                    issues["warnings"].append({
                        "page": result["url"],
                        "issue": f"Some images without alt text ({result['images_without_alt_count']})"
                    })
            
            # Check canonical
            if not result.get("has_canonical"):
                pages_without_canonical += 1
                issues["info"].append({
                    "page": result["url"],
                    "issue": "Missing canonical tag"
                })
            
            # Check schema
            if not result.get("has_schema"):
                pages_without_schema += 1
                issues["info"].append({
                    "page": result["url"],
                    "issue": "No schema markup detected"
                })
        
        return {
            "base_url": base_url,
            "crawl_date": datetime.utcnow().isoformat(),
            "pages_crawled": total_pages,
            "summary": {
                "pages_without_title": pages_without_title,
                "pages_without_meta": pages_without_meta,
                "pages_multiple_h1": pages_multiple_h1,
                "pages_missing_alt": pages_missing_alt,
                "pages_without_canonical": pages_without_canonical,
                "pages_without_schema": pages_without_schema
            },
            "issues": issues,
            "pages": self.results
        }
