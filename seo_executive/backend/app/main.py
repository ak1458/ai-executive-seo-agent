from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os

from .models.database import init_db, get_db, Website, Keyword, Audit, GSCData
from .models.schemas import (
    WebsiteCreate, WebsiteResponse, KeywordCreate, KeywordResponse,
    AuditCreate, AuditResponse, TaskRequest, TaskResponse,
    KeywordResearchRequest, IndexingSubmitRequest
)
from .agents.seo_agent import SEOExecutiveAgent
from .services.google_auth import GoogleAuthService

# Initialize FastAPI app
app = FastAPI(
    title="SEO Executive API",
    description="AI-powered SEO automation platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
seo_agent = SEOExecutiveAgent()

# Job tracking (in production, use Redis)
job_store = {}

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("Database initialized")

# Auth endpoints
@app.get("/auth/google")
def auth_google():
    """Get Google OAuth URL."""
    auth_url = seo_agent.get_auth_url()
    return {"auth_url": auth_url}

@app.get("/auth/callback")
def auth_callback(code: str):
    """Handle OAuth callback."""
    try:
        result = seo_agent.exchange_auth_code(code)
        return {"status": "success", "message": "Authentication successful", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/status")
def auth_status():
    """Check authentication status."""
    return {
        "google_authenticated": seo_agent.is_google_authenticated()
    }

# Task endpoints
@app.post("/task", response_model=TaskResponse)
def create_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """Submit a new task."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "pending", "result": None}
    
    # Run task in background
    background_tasks.add_task(run_task, job_id, task.task_type, task.params)
    
    return TaskResponse(
        job_id=job_id,
        status="pending",
        message="Task submitted successfully"
    )

@app.get("/task/{job_id}")
def get_task_status(job_id: str):
    """Get task status and results."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_store[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job.get("result")
    }

async def run_task(job_id: str, task_type: str, params: dict):
    """Run task and update job store."""
    job_store[job_id]["status"] = "running"
    
    try:
        result = await seo_agent.execute_task(task_type, params)
        job_store[job_id]["status"] = "complete"
        job_store[job_id]["result"] = result
    except Exception as e:
        job_store[job_id]["status"] = "error"
        job_store[job_id]["result"] = {"error": str(e)}

# Website endpoints
@app.get("/websites", response_model=List[WebsiteResponse])
def list_websites(db: Session = Depends(get_db)):
    """List all monitored websites."""
    return db.query(Website).all()

@app.post("/websites", response_model=WebsiteResponse)
def create_website(website: WebsiteCreate, db: Session = Depends(get_db)):
    """Add a new website to monitor."""
    db_website = Website(
        url=website.url,
        gsc_property=website.gsc_property
    )
    db.add(db_website)
    db.commit()
    db.refresh(db_website)
    return db_website

@app.get("/websites/{website_id}")
def get_website(website_id: int, db: Session = Depends(get_db)):
    """Get website details."""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@app.delete("/websites/{website_id}")
def delete_website(website_id: int, db: Session = Depends(get_db)):
    """Delete a website."""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    db.delete(website)
    db.commit()
    return {"status": "success", "message": "Website deleted"}

# Keyword endpoints
@app.get("/keywords/{website_id}", response_model=List[KeywordResponse])
def list_keywords(website_id: int, db: Session = Depends(get_db)):
    """Get keywords for a website."""
    return db.query(Keyword).filter(Keyword.website_id == website_id).all()

@app.post("/keywords")
def add_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    """Add a keyword to track."""
    db_keyword = Keyword(
        website_id=keyword.website_id,
        keyword=keyword.keyword,
        volume=keyword.volume,
        difficulty=keyword.difficulty,
        current_rank=keyword.current_rank
    )
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

@app.post("/keywords/research")
def research_keywords(request: KeywordResearchRequest, background_tasks: BackgroundTasks):
    """Start keyword research job."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "pending", "result": None}
    
    params = {
        "seed": request.seed,
        "location_code": 2840 if request.location == "us" else 2826,
        "language_code": request.language,
        "depth": request.depth
    }
    
    background_tasks.add_task(run_task, job_id, "keyword_research", params)
    
    return TaskResponse(
        job_id=job_id,
        status="pending",
        message="Keyword research started"
    )

# Audit endpoints
@app.get("/audits/{website_id}", response_model=List[AuditResponse])
def list_audits(website_id: int, db: Session = Depends(get_db)):
    """Get audit history for a website."""
    return db.query(Audit).filter(Audit.website_id == website_id).all()

@app.post("/audits")
def create_audit(website_id: int, max_pages: int = 50, background_tasks: BackgroundTasks = None):
    """Start a new audit."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "pending", "result": None}
    
    params = {
        "url": None,  # Will be fetched from website record
        "max_pages": max_pages
    }
    
    # TODO: Fetch website URL from database
    background_tasks.add_task(run_task, job_id, "full_audit", params)
    
    return TaskResponse(
        job_id=job_id,
        status="pending",
        message="Audit started"
    )

# Indexing endpoints
@app.post("/indexing/submit")
def submit_indexing(request: IndexingSubmitRequest, background_tasks: BackgroundTasks):
    """Submit URLs for indexing."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "pending", "result": None}
    
    params = {"urls": request.urls}
    
    background_tasks.add_task(run_task, job_id, "submit_indexing", params)
    
    return TaskResponse(
        job_id=job_id,
        status="pending",
        message="URLs submitted for indexing"
    )

@app.get("/indexing/status")
def check_indexing_status(url: str):
    """Check indexing status of a URL."""
    if "indexing" not in seo_agent.tools:
        raise HTTPException(status_code=401, detail="Google authentication required")
    
    status = seo_agent.tools["indexing"].get_status(url)
    return status

# Rank tracking endpoints
@app.post("/rankings/check")
def check_rankings(domain: str, keywords: List[str], location_code: int = 2840, background_tasks: BackgroundTasks = None):
    """Check rankings for keywords."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "pending", "result": None}
    
    params = {
        "domain": domain,
        "keywords": keywords,
        "location_code": location_code
    }
    
    background_tasks.add_task(run_task, job_id, "rank_check", params)
    
    return TaskResponse(
        job_id=job_id,
        status="pending",
        message="Rank check started"
    )

# GSC endpoints
@app.post("/gsc/sync")
def sync_gsc(site_url: str, days: int = 28, background_tasks: BackgroundTasks = None):
    """Sync GSC data."""
    if not seo_agent.is_google_authenticated():
        raise HTTPException(status_code=401, detail="Google authentication required")
    
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "pending", "result": None}
    
    params = {
        "site_url": site_url,
        "days": days
    }
    
    background_tasks.add_task(run_task, job_id, "gsc_sync", params)
    
    return TaskResponse(
        job_id=job_id,
        status="pending",
        message="GSC sync started"
    )

@app.get("/gsc/sites")
def list_gsc_sites():
    """List GSC verified sites."""
    if not seo_agent.is_google_authenticated():
        raise HTTPException(status_code=401, detail="Google authentication required")
    
    if "gsc" not in seo_agent.tools:
        raise HTTPException(status_code=500, detail="GSC tool not initialized")
    
    sites = seo_agent.tools["gsc"].get_sites()
    return {"sites": sites}

# Health check
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "google_authenticated": seo_agent.is_google_authenticated(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
