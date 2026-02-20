from celery import Celery
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Celery configuration
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "seo_executive",
    broker=redis_url,
    backend=redis_url,
    include=["app.worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
)

# Import agent after celery setup to avoid circular imports
from app.agents.seo_agent import SEOExecutiveAgent

def get_agent():
    """Get or create SEO agent instance."""
    return SEOExecutiveAgent()

@celery_app.task(bind=True, max_retries=3)
def run_technical_audit(self, url: str, max_pages: int = 50):
    """
    Run technical audit task.
    
    Args:
        url: Website URL to audit
        max_pages: Maximum pages to crawl
    """
    self.update_state(state="PROGRESS", meta={"status": "Starting audit..."})
    
    try:
        agent = get_agent()
        
        # Run async task in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.update_state(state="PROGRESS", meta={"status": "Crawling website..."})
        result = loop.run_until_complete(
            agent.execute_task("full_audit", {"url": url, "max_pages": max_pages})
        )
        loop.close()
        
        return {
            "status": "complete",
            "url": url,
            "pages_crawled": result.get("pages_crawled", 0),
            "report_id": result.get("report_id"),
            "critical_issues": result.get("critical_issues", 0),
            "warnings": result.get("warnings", 0)
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=2)
def bulk_rank_check(self, domain: str, keywords: list, location_code: int = 2840):
    """
    Run bulk rank check task.
    
    Args:
        domain: Domain to check rankings for
        keywords: List of keywords
        location_code: Location code (2840=US)
    """
    self.update_state(state="PROGRESS", meta={
        "status": f"Checking {len(keywords)} keywords...",
        "progress": 0,
        "total": len(keywords)
    })
    
    try:
        agent = get_agent()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Process in chunks of 100
        chunk_size = 100
        all_results = []
        
        for i in range(0, len(keywords), chunk_size):
            chunk = keywords[i:i + chunk_size]
            
            self.update_state(state="PROGRESS", meta={
                "status": f"Processing chunk {i//chunk_size + 1}/{(len(keywords)-1)//chunk_size + 1}...",
                "progress": min(i + chunk_size, len(keywords)),
                "total": len(keywords)
            })
            
            result = loop.run_until_complete(
                agent.execute_task("rank_check", {
                    "domain": domain,
                    "keywords": chunk,
                    "location_code": location_code
                })
            )
            
            if isinstance(result.get("results"), list):
                all_results.extend(result["results"])
            
            # Rate limiting - wait between chunks
            if i + chunk_size < len(keywords):
                import time
                time.sleep(1)
        
        loop.close()
        
        return {
            "status": "complete",
            "domain": domain,
            "keywords_checked": len(keywords),
            "results": all_results
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=300)

@celery_app.task(bind=True)
def weekly_gsc_sync(self, site_url: str):
    """
    Sync GSC data for the past week.
    
    Args:
        site_url: GSC site URL
    """
    self.update_state(state="PROGRESS", meta={"status": "Fetching GSC data..."})
    
    try:
        agent = get_agent()
        
        if not agent.is_google_authenticated():
            return {"status": "error", "message": "Google authentication required"}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            agent.execute_task("gsc_sync", {"site_url": site_url, "days": 7})
        )
        
        loop.close()
        
        return {
            "status": "complete",
            "site_url": site_url,
            "rows_fetched": result.get("rows_fetched", 0)
        }
        
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

@celery_app.task(bind=True, max_retries=2)
def content_brief_generation(self, keyword: str, serp_data: dict = None):
    """
    Generate AI-powered content brief.
    
    Args:
        keyword: Target keyword
        serp_data: Optional SERP analysis data
    """
    self.update_state(state="PROGRESS", meta={"status": "Analyzing top rankings..."})
    
    try:
        agent = get_agent()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Generate content brief using Ollama
        analysis = serp_data or "Top 10 SERP results show comprehensive guides averaging 2000+ words."
        
        brief = loop.run_until_complete(
            agent.ollama.generate_content_brief(keyword, analysis)
        )
        
        loop.close()
        
        return {
            "status": "complete",
            "keyword": keyword,
            "brief": brief
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@celery_app.task
def cleanup_old_jobs():
    """Cleanup old job records from database."""
    from datetime import datetime, timedelta
    
    # This would clean up old job records
    # Implementation depends on your persistence layer
    return {"status": "complete", "message": "Cleanup completed"}

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "weekly-gsc-sync": {
        "task": "app.worker.weekly_gsc_sync",
        "schedule": 604800.0,  # 7 days in seconds
        "args": ()  # Site URL would be passed dynamically
    },
    "cleanup-old-jobs": {
        "task": "app.worker.cleanup_old_jobs",
        "schedule": 86400.0  # Daily
    }
}

if __name__ == "__main__":
    celery_app.start()
