import requests
import base64
from typing import List, Dict, Any, Optional
import os
import time

class KeywordResearch:
    """DataForSEO Keyword Research API integration."""
    
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
    
    def seed_keywords_analysis(
        self, 
        seed: str, 
        location_code: int = 2840,
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Analyze seed keywords and get related data.
        
        Args:
            seed: Seed keyword to analyze
            location_code: Location code (2840=US)
            language_code: Language code
            
        Returns:
            Keyword analysis results
        """
        endpoint = "keywords_data/google/search_volume/live"
        
        data = {
            "data": [{
                "keywords": [seed],
                "location_code": location_code,
                "language_code": language_code
            }]
        }
        
        response = self._make_request(endpoint, data)
        return self._parse_keyword_data(response)
    
    def keyword_suggestions(
        self, 
        seed: str, 
        depth: int = 2,
        location_code: int = 2840,
        language_code: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Get keyword suggestions based on seed keyword.
        
        Args:
            seed: Seed keyword
            depth: Depth of suggestions (1-4)
            location_code: Location code
            language_code: Language code
            
        Returns:
            List of keyword suggestions
        """
        endpoint = "keywords_data/google/keywords_for_keywords/live"
        
        data = {
            "data": [{
                "keywords": [seed],
                "location_code": location_code,
                "language_code": language_code,
                "depth": depth,
                "include_serp_info": True
            }]
        }
        
        response = self._make_request(endpoint, data)
        
        keywords = []
        tasks = response.get("tasks", [])
        for task in tasks:
            results = task.get("result", [])
            for result in results:
                items = result.get("items", [])
                for item in items:
                    keywords.append({
                        "keyword": item.get("keyword"),
                        "search_volume": item.get("search_volume"),
                        "competition": item.get("competition"),
                        "cpc": item.get("cpc"),
                        "category": item.get("category", [])
                    })
        
        return keywords
    
    def keyword_difficulty_analysis(
        self, 
        keyword_list: List[str],
        location_code: int = 2840,
        language_code: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Analyze keyword difficulty for a list of keywords.
        
        Args:
            keyword_list: List of keywords to analyze
            location_code: Location code
            language_code: Language code
            
        Returns:
            List of keywords with difficulty scores
        """
        endpoint = "keywords_data/google/keyword_difficulty/live"
        
        results = []
        # Process in batches of 1000
        for i in range(0, len(keyword_list), 1000):
            batch = keyword_list[i:i+1000]
            data = {
                "data": [{
                    "keywords": batch,
                    "location_code": location_code,
                    "language_code": language_code
                }]
            }
            
            response = self._make_request(endpoint, data)
            
            tasks = response.get("tasks", [])
            for task in tasks:
                task_results = task.get("result", [])
                for result in task_results:
                    items = result.get("items", [])
                    for item in items:
                        results.append({
                            "keyword": item.get("keyword"),
                            "difficulty": item.get("keyword_difficulty"),
                            "search_volume": item.get("search_volume"),
                            "competition": item.get("competition"),
                            "cpc": item.get("cpc")
                        })
            
            if i + 1000 < len(keyword_list):
                time.sleep(1)
        
        return results
    
    def _parse_keyword_data(self, response: Dict) -> Dict[str, Any]:
        """Parse keyword data from API response."""
        if "error" in response:
            return response
        
        tasks = response.get("tasks", [])
        results = []
        
        for task in tasks:
            task_results = task.get("result", [])
            for result in task_results:
                items = result.get("items", [])
                for item in items:
                    results.append({
                        "keyword": item.get("keyword"),
                        "search_volume": item.get("search_volume"),
                        "competition": item.get("competition"),
                        "cpc": item.get("cpc"),
                        "competition_index": item.get("competition_index"),
                        "low_top_of_page_bid": item.get("low_top_of_page_bid"),
                        "high_top_of_page_bid": item.get("high_top_of_page_bid"),
                        "categories": item.get("category", [])
                    })
        
        return {
            "results": results,
            "total_count": len(results)
        }
    
    def get_related_keywords(
        self, 
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Get related keywords and questions.
        
        Args:
            keyword: Target keyword
            location_code: Location code
            language_code: Language code
            
        Returns:
            Related keywords and questions
        """
        endpoint = "keywords_data/google/search_intent/live"
        
        data = {
            "data": [{
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code
            }]
        }
        
        response = self._make_request(endpoint, data)
        
        related = []
        tasks = response.get("tasks", [])
        for task in tasks:
            results = task.get("result", [])
            for result in results:
                items = result.get("items", [])
                for item in items:
                    related.append({
                        "keyword": item.get("keyword"),
                        "search_volume": item.get("search_volume"),
                        "intent": item.get("search_intent_info", {}).get("main_intent")
                    })
        
        return related
