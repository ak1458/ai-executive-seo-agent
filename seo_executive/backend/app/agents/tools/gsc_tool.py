from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class GSCTool:
    def __init__(self, credentials: Credentials):
        self.service = build('webmasters', 'v3', credentials=credentials)
    
    def fetch_performance_data(
        self, 
        site_url: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        dimensions: List[str] = None,
        row_limit: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Fetch performance data from Google Search Console.
        
        Args:
            site_url: The site URL (e.g., 'https://example.com/')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dimensions: List of dimensions (query, page, device, country)
            row_limit: Maximum number of rows to return
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not dimensions:
            dimensions = ["query", "page"]
        
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': row_limit
        }
        
        try:
            response = self.service.searchanalytics().query(siteUrl=site_url, body=request).execute()
            rows = response.get('rows', [])
            
            results = []
            for row in rows:
                result = {
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': row.get('ctr', 0.0),
                    'position': row.get('position', 0.0)
                }
                
                # Add dimension values
                keys = row.get('keys', [])
                for i, dim in enumerate(dimensions):
                    if i < len(keys):
                        result[dim] = keys[i]
                
                results.append(result)
            
            return results
        except Exception as e:
            return {"error": str(e)}
    
    def get_index_coverage(self, site_url: str) -> Dict[str, Any]:
        """Get index coverage summary for the site."""
        try:
            response = self.service.urlInspection().index().inspect(
                body={
                    "inspectionUrl": site_url,
                    "siteUrl": site_url
                }
            ).execute()
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def get_sitemaps(self, site_url: str) -> List[Dict[str, Any]]:
        """Get list of sitemaps for the site."""
        try:
            response = self.service.sitemaps().list(siteUrl=site_url).execute()
            return response.get('sitemap', [])
        except Exception as e:
            return {"error": str(e)}
    
    def submit_sitemap(self, site_url: str, sitemap_url: str) -> Dict[str, Any]:
        """Submit a sitemap to Google Search Console."""
        try:
            response = self.service.sitemaps().submit(
                siteUrl=site_url,
                feedpath=sitemap_url
            ).execute()
            return {"status": "success", "message": "Sitemap submitted successfully"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_sites(self) -> List[str]:
        """Get list of sites the user has access to."""
        try:
            response = self.service.sites().list().execute()
            sites = response.get('siteEntry', [])
            return [site['siteUrl'] for site in sites]
        except Exception as e:
            return {"error": str(e)}
