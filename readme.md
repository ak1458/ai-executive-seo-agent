[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000?logo=ollama&logoColor=white)](https://ollama.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

``markdown

# AI SEO EXECUTIVE - AUTONOMOUS BUILD MANIFEST

Version: 1.0
Target: Local AI Agent (Ollama + Python)
Status: EXECUTE IMMEDIATELY
Stop Condition: All Phase 5 checkpoints marked COMPLETE

## 0. SYSTEM PREREQUISITES (VERIFY BEFORE START)

- [ ] Ollama running locally (verify: `ollama list`)
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (for frontend)
- [ ] Google Cloud project with APIs enabled (GSC, Drive, Indexing, Sheets)
- [ ] DataForSEO account (credits available)
- [ ] Git initialized in project directory

## 1. PROJECT SCAFFOLDING (Phase 1)

Create directory structure:

```
seo_executive/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py (FastAPI entry)
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── seo_agent.py (main orchestrator)
│   │   │   └── tools/
│   │   │       ├── gsc_tool.py
│   │   │       ├── indexing_tool.py
│   │   │       ├── rank_tracker.py
│   │   │       ├── keyword_research.py
│   │   │       ├── technical_audit.py
│   │   │       └── drive_storage.py
│   │   ├── models/
│   │   │   ├── database.py (SQLAlchemy)
│   │   │   └── schemas.py (Pydantic)
│   │   └── services/
│   │       ├── ollama_service.py (local LLM)
│   │       └── google_auth.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html (single-page app)
│   ├── app.js (vanilla JS, no frameworks)
│   └── styles.css
└── data/ (gitignored)
    └── cache/
```

## 2. DEPENDENCY INSTALLATION (Phase 2)

File: `backend/requirements.txt`

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
redis==5.0.1
httpx==0.26.0
google-api-python-client==2.116.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
pandas==2.2.0
python-multipart==0.0.6
celery==5.3.6
playwright==1.41.0
beautifulsoup4==4.12.3
lxml==5.1.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
requests==2.31.0
```

Execute:

```bash
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 3. CONFIGURATION LAYER (Phase 3)

File: `backend/.env`

```env
# Google APIs
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# DataForSEO
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password

# Local LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:13b  # or mistral:7b, codellama:13b

# App
DATABASE_URL=sqlite:///data/seo_executive.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=generate_random_32_char_string
```

## 4. CORE IMPLEMENTATION (Phase 4 - PRIORITY CRITICAL)

### 4.1 Database Models (`backend/app/models/database.py`)

Implement SQLAlchemy models:

- `Website` (id, url, gsc_property, created_at)
- `Keyword` (id, website_id, keyword, volume, difficulty, current_rank, last_checked)
- `Audit` (id, website_id, audit_type, status, results_json, created_at)
- `GSCData` (id, website_id, url, clicks, impressions, ctr, position, date)

### 4.2 Ollama Integration (`backend/app/services/ollama_service.py`)

```python
import httpx
from typing import Optional

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral:7b"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def analyze(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are an expert SEO analyst.",
            "stream": False
        }
        response = await self.client.post(f"{self.base_url}/api/generate", json=payload)
        return response.json()["response"]
    
    async def analyze_competitor_gap(self, my_keywords: list, competitor_keywords: list) -> dict:
        prompt = f"""Analyze keyword gap. My keywords: {my_keywords}. Competitor keywords: {competitor_keywords}. 
        Return JSON with: opportunities (high volume, low difficulty), threats (competitor ranking for my terms), content_gaps."""
        return await self.analyze(prompt)
```

### 4.3 Google Search Console Tool (`backend/app/agents/tools/gsc_tool.py`)

Implement methods:

- `fetch_performance_data(site_url, start_date, end_date, dimensions=["query", "page"])`
- `get_index_coverage(site_url)`
- `get_sitemaps(site_url)`
Use `googleapiclient.discovery` with OAuth2 credentials.

### 4.4 Indexing API Tool (`backend/app/agents/tools/indexing_tool.py`)

- `submit_url(url)` - POST to indexing.googleapis.com/v3/urlNotifications:publish
- `get_status(url)` - GET urlNotifications/metadata
- Handle batch submissions with rate limiting (max 200/day)

### 4.5 Rank Tracker (`backend/app/agents/tools/rank_tracker.py`)

Using DataForSEO:

- `check_rankings(domain, keywords, location_code=2840)` (US=2840, UK=2826)
- Store results in DB with timestamp
- Method `get_ranking_history(keyword_id)`

### 4.6 Keyword Research (`backend/app/agents/tools/keyword_research.py`)

DataForSEO endpoints:

- `seed_keywords_analysis(seed, location, language)`
- `keyword_suggestions(seed, depth=2)`
- `keyword_difficulty_analysis(keyword_list)`
- Return structured data: volume, kd, cpc, competition, parent_topic

### 4.7 Technical Audit (`backend/app/agents/tools/technical_audit.py`)

Combine:

- Playwright crawl (respect robots.txt, 10 concurrent max)
- Lighthouse/PSI API integration for Core Web Vitals
- Check: Title length, meta description, H1, images alt, canonicals, schema markup
- Output: Issue severity (Critical, Warning, Info)

### 4.8 Drive Storage (`backend/app/agents/tools/drive_storage.py`)

- `create_spreadsheet(title, dataframes)` - Create Google Sheets with multiple tabs
- `create_folder_structure(client_name)` - Organize by date
- `upload_report(file_path, folder_id)`
- `share_file(file_id, emails)`

### 4.9 Main Agent Orchestrator (`backend/app/agents/seo_agent.py`)

```python
class SEOExecutiveAgent:
    def __init__(self):
        self.ollama = OllamaService()
        self.tools = {
            "gsc": GSCTool(),
            "indexing": IndexingTool(),
            "ranking": RankTracker(),
            "keywords": KeywordResearch(),
            "audit": TechnicalAudit(),
            "storage": DriveStorage()
        }
    
    async def execute_task(self, task_type: str, params: dict):
        if task_type == "full_audit":
            return await self._full_website_audit(params["url"])
        elif task_type == "keyword_research":
            return await self._keyword_research_flow(params)
        elif task_type == "rank_check":
            return await self._rank_tracking_flow(params)
        # Add more task types
    
    async def _full_website_audit(self, url: str):
        # 1. Technical crawl
        audit_data = await self.tools["audit"].crawl(url)
        
        # 2. GSC data
        gsc_data = await self.tools["gsc"].fetch_performance_data(url, days_ago=28)
        
        # 3. AI Analysis via Ollama
        analysis = await self.ollama.analyze(
            f"Analyze this SEO audit data and provide prioritized recommendations: {audit_data}",
            system_prompt="You are a technical SEO expert. Return structured JSON with issues, impact, difficulty, and fix instructions."
        )
        
        # 4. Save to Drive
        report_id = await self.tools["storage"].create_audit_report(url, audit_data, analysis)
        
        return {"status": "complete", "report_id": report_id, "summary": analysis}
```

### 4.10 FastAPI Endpoints (`backend/app/main.py`)

Required routes:

- `POST /auth/google` - Initiate OAuth
- `GET /auth/callback` - OAuth callback
- `POST /task` - Submit task (returns job_id)
- `GET /task/{job_id}` - Check status
- `GET /websites` - List monitored sites
- `POST /websites` - Add new site
- `GET /keywords/{website_id}` - Get keywords
- `POST /keywords/research` - Start research job
- `GET /audits/{website_id}` - Get audit history
- `POST /indexing/submit` - Submit URLs for indexing

## 5. FRONTEND IMPLEMENTATION (Phase 5)

Single-file vanilla JS approach (`frontend/index.html`):

Features required:

- Dashboard showing active websites
- "New Audit" button (triggers backend task)
- Keyword research interface (input seed, select location, get results in table)
- GSC data visualization (simple charts using Chart.js CDN)
- Task queue status (polling `/task/{id}`)
- Google Drive folder viewer (iframe or API listing)

Critical UI flows:

1. **Connect Google**: Button → OAuth flow → Save token
2. **Run Audit**: Input URL → Select depth → Show progress → Display results with "View in Drive" link
3. **Keyword Research**: Input seed → Location dropdown → Loading state → Export to Sheets button
4. **Rank Tracker**: Add keywords → Schedule dropdown → History chart

## 6. BACKGROUND WORKERS (Phase 6)

File: `backend/app/worker.py` (Celery configuration)

- Task `run_technical_audit` (timeout: 30min)
- Task `bulk_rank_check` (chunk keywords, 100/day limit handling)
- Task `weekly_gsc_sync` (fetch latest data)
- Task `content_brief_generation` (AI-powered, uses Ollama)

## 7. TESTING & VALIDATION (Phase 7 - STOP CHECKPOINT)

Before marking COMPLETE, verify:

- [ ] **OAuth Flow**: Can authenticate with Google, token refreshes automatically
- [ ] **GSC Integration**: Can pull last 28 days data for any verified property
- [ ] **Indexing API**: Successfully submits URL and returns status (test with 2 URLs)
- [ ] **DataForSEO**: Rank check returns position data (test with 5 keywords)
- [ ] **Ollama**: Local analysis works offline (test competitor gap analysis)
- [ ] **Drive Export**: Creates spreadsheet with proper formatting in correct folder
- [ ] **Technical Audit**: Crawls 50 pages, detects missing alt tags, measures Core Web Vitals
- [ ] **Frontend**: All buttons work, data displays, no console errors
- [ ] **Database**: Migrations run, data persists between restarts
- [ ] **Background Jobs**: Celery tasks process without hanging

## 8. DEPLOYMENT SCRIPT (Phase 8)

File: `start.sh`

```bash
#!/bin/bash
redis-server --daemonize yes
cd backend && source venv/bin/activate
alembic upgrade head
celery -A app.worker worker --loglevel=info --detach
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

File: `frontend_server.py` (simple Python HTTP server)

```python
import http.server
import socketserver
PORT = 3000
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend at http://localhost:{PORT}")
    httpd.serve_forever()
```

## 9. EXECUTION CHECKPOINTS (STOP CONDITIONS)

**STOP 1**: After Phase 4.4 (Indexing API)
Verify: Can submit URL via API call and verify in Google Search Console

**STOP 2**: After Phase 4.8 (Drive Storage)
Verify: Can create Sheets file with sample data in specific Drive folder

**STOP 3**: After Phase 4.9 (Agent Orchestrator)
Verify: Running `python -c "from app.agents.seo_agent import SEOExecutiveAgent; import asyncio; print(asyncio.run(SEOExecutiveAgent().execute_task('full_audit', {'url': 'https://example.com'})))"` executes without errors

**STOP 4**: After Phase 5 (Frontend)
Verify: Opening `http://localhost:3000` shows dashboard, can trigger audit, see results

**STOP 5**: FINAL COMPLETION
All Phase 7 checkboxes marked true. System is self-contained and operational.

## 10. POST-COMPLETION FEATURES (Optional Extensions)

Only implement after STOP 5 confirmed:

- **Content Brief Generator**: AI analyzes top 10 SERP results via Ollama, generates outline
- **Internal Linking Suggester**: Graph analysis of site structure
- **Automated Indexing**: Webhook listener for sitemap changes, auto-submit new URLs
- **Slack/Discord Bot**: Notifications for ranking changes
- **Competitor Monitoring**: Scheduled weekly competitor rank checks

## EXECUTION COMMAND

As Kimi Code 2.5 with Ollama access, execute this manifest sequentially. Do not skip phases. Stop at each STOP checkpoint and await confirmation before proceeding unless explicitly told "autonomous mode".

Begin with Phase 1 now.

```

**Usage Instructions:**
1. Copy the entire markdown block above
2. Paste it into your AI agent interface (or give it to me, Kimi)
3. The AI will execute sequentially, stopping at verification checkpoints
4. Have your Google Cloud credentials and DataForSEO login ready before starting
5. Ensure Ollama is running with at least a 7B model pulled (`ollama pull mistral:7b`)

The system is designed to be **fully functional but minimal** - no React, no Kubernetes, just Python/FastAPI + vanilla JS + SQLite + Redis. This fits the "easy way" requirement while maintaining professional capabilities.

Ready to execute?
