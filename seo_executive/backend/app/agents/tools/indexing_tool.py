from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import List, Dict, Any
import time

class IndexingTool:
    """Google Indexing API tool for submitting URLs."""
    
    def __init__(self, credentials: Credentials):
        self.service = build('indexing', 'v3', credentials=credentials)
        self.daily_quota = 200
        self.submissions_today = 0
    
    def submit_url(self, url: str) -> Dict[str, Any]:
        """
        Submit a URL for indexing.
        
        Args:
            url: The URL to submit for indexing
            
        Returns:
            Response with status and details
        """
        if self.submissions_today >= self.daily_quota:
            return {
                "error": "Daily quota exceeded",
                "message": f"Maximum {self.daily_quota} URLs per day allowed"
            }
        
        try:
            response = self.service.urlNotifications().publish(
                body={
                    "url": url,
                    "type": "URL_UPDATED"
                }
            ).execute()
            
            self.submissions_today += 1
            
            return {
                "status": "success",
                "url": url,
                "notification_type": response.get('urlNotificationMetadata', {}).get('type'),
                "notify_time": response.get('urlNotificationMetadata', {}).get('notifyTime')
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    def get_status(self, url: str) -> Dict[str, Any]:
        """
        Get the indexing status of a URL.
        
        Args:
            url: The URL to check
            
        Returns:
            Status details
        """
        try:
            response = self.service.urlNotifications().getMetadata(
                url=url
            ).execute()
            
            return {
                "url": url,
                "latest_update": {
                    "type": response.get('latestUpdate', {}).get('type'),
                    "notify_time": response.get('latestUpdate', {}).get('notifyTime'),
                    "url": response.get('latestUpdate', {}).get('url')
                },
                "latest_remove": {
                    "type": response.get('latestRemove', {}).get('type'),
                    "notify_time": response.get('latestRemove', {}).get('notifyTime'),
                    "url": response.get('latestRemove', {}).get('url')
                } if response.get('latestRemove') else None
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    def submit_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Submit multiple URLs for indexing with rate limiting.
        
        Args:
            urls: List of URLs to submit
            
        Returns:
            List of submission results
        """
        results = []
        
        for url in urls:
            if self.submissions_today >= self.daily_quota:
                results.append({
                    "url": url,
                    "status": "skipped",
                    "reason": "Daily quota reached"
                })
                continue
            
            result = self.submit_url(url)
            results.append(result)
            
            # Rate limiting - wait between submissions
            if len(urls) > 1:
                time.sleep(1)
        
        return results
    
    def remove_url(self, url: str) -> Dict[str, Any]:
        """
        Submit a URL removal request.
        
        Args:
            url: The URL to remove from index
            
        Returns:
            Response with status
        """
        try:
            response = self.service.urlNotifications().publish(
                body={
                    "url": url,
                    "type": "URL_DELETED"
                }
            ).execute()
            
            return {
                "status": "success",
                "url": url,
                "action": "removal_requested",
                "notification_type": response.get('urlNotificationMetadata', {}).get('type'),
                "notify_time": response.get('urlNotificationMetadata', {}).get('notifyTime')
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota usage."""
        return {
            "daily_quota": self.daily_quota,
            "used_today": self.submissions_today,
            "remaining": self.daily_quota - self.submissions_today
        }
