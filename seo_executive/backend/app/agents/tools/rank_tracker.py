import requests
import base64
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import time

class RankTracker:
    """DataForSEO Rank Tracking API integration."""
    
    def __init__(self):
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.base_url = "https://api.dataforseo.com/v3"
        
        if self.login and self.password:
            auth_str = f"{self.login}:{self.password}"
            self.auth_header = base64.b64encode(auth_str.encode()).decode()
        else:
            self.auth_header = None
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to DataForSEO."""
        if not self.auth_header:
            return {"error": "DataForSEO credentials not configured"}
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def check_rankings(
        self, 
        domain: str, 
        keywords: List[str], 
        location_code: int = 2840,
        language_code: str = "en",
        depth: int = 100
    ) -> Dict[str, Any]:
        """
        Check rankings for keywords.
        
        Args:
            domain: The domain to check rankings for
            keywords: List of keywords to check
            location_code: Location code (2840=US, 2826=UK)
            language_code: Language code
            depth: Number of results to check (max 100)
            
        Returns:
            Ranking results
        """
        endpoint = "serp/google/organic/live/advanced"
        
        tasks = []
        for keyword in keywords:
            task = {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": depth,
                "include_serp_info": True
            }
            tasks.append(task)
        
        # Process in batches of 100
        all_results = []
        for i in range(0, len(tasks), 100):
            batch = tasks[i:i+100]
            data = {"data": batch}
            response = self._make_request(endpoint, data)
            
            if "error" in response:
                return response
            
            tasks_data = response.get("tasks", [])
            for task in tasks_data:
                result = task.get("result", [])
                if result:
                    all_results.extend(result)
            
            # Rate limiting
            if i + 100 < len(tasks):
                time.sleep(1)
        
        return self._parse_rankings(all_results, domain)
    
    def _parse_rankings(self, results: List[Dict], target_domain: str) -> List[Dict[str, Any]]:
        """Parse ranking results to find target domain position."""
        parsed_results = []
        
        for result in results:
            keyword = result.get("keyword")
            items = result.get("items", [])
            
            rank = None
            url_found = None
            title = None
            
            for i, item in enumerate(items, 1):
                url = item.get("url", "")
                domain = url.replace("https://", "").replace("http://", "").split("/")[0]
                
                if target_domain in domain or domain in target_domain:
                    rank = i
                    url_found = url
                    title = item.get("title", "")
                    break
            
            parsed_results.append({
                "keyword": keyword,
                "rank": rank,
                "url": url_found,
                "title": title,
                "checked_at": datetime.utcnow().isoformat(),
                "total_results": len(items)
            })
        
        return parsed_results
    
    def get_ranking_history(self, keyword_id: int, db_session) -> List[Dict[str, Any]]:
        """
        Get ranking history for a keyword from database.
        
        Args:
            keyword_id: The keyword ID
            db_session: Database session
            
        Returns:
            List of historical rankings
        """
        # This would query the database for historical data
        # Implementation depends on your database schema
        from ...models.database import Keyword
        
        keyword = db_session.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            return [{
                "keyword": keyword.keyword,
                "rank": keyword.current_rank,
                "checked_at": keyword.last_checked.isoformat() if keyword.last_checked else None
            }]
        return []
    
    def get_competitor_rankings(
        self, 
        competitor_domain: str, 
        keywords: List[str],
        location_code: int = 2840
    ) -> Dict[str, Any]:
        """
        Check rankings for a competitor domain.
        
        Args:
            competitor_domain: Competitor domain to analyze
            keywords: List of keywords to check
            location_code: Location code
            
        Returns:
            Competitor ranking data
        """
        return self.check_rankings(competitor_domain, keywords, location_code)
