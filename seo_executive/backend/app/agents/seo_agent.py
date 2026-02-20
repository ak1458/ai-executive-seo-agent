import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

from ..services.ollama_service import OllamaService
from ..services.google_auth import GoogleAuthService
from .tools.gsc_tool import GSCTool
from .tools.indexing_tool import IndexingTool
from .tools.rank_tracker import RankTracker
from .tools.keyword_research import KeywordResearch
from .tools.technical_audit import TechnicalAudit
from .tools.drive_storage import DriveStorage

class SEOExecutiveAgent:
    """Main SEO Executive Agent that orchestrates all SEO tools."""
    
    def __init__(self):
        self.ollama = OllamaService()
        self.google_auth = GoogleAuthService()
        self.tools = {}
        self._init_tools()
    
    def _init_tools(self):
        """Initialize tools that require Google authentication."""
        credentials = self.google_auth.load_credentials()
        
        if credentials:
            self.tools = {
                "gsc": GSCTool(credentials),
                "indexing": IndexingTool(credentials),
                "ranking": RankTracker(),
                "keywords": KeywordResearch(),
                "audit": TechnicalAudit(),
                "storage": DriveStorage(credentials)
            }
        else:
            # Tools that don't require Google auth
            self.tools = {
                "ranking": RankTracker(),
                "keywords": KeywordResearch(),
                "audit": TechnicalAudit()
            }
    
    async def execute_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task based on task type.
        
        Args:
            task_type: Type of task to execute
            params: Task parameters
            
        Returns:
            Task results
        """
        if task_type == "full_audit":
            return await self._full_website_audit(params.get("url"), params.get("max_pages", 50))
        elif task_type == "keyword_research":
            return await self._keyword_research_flow(params)
        elif task_type == "rank_check":
            return await self._rank_tracking_flow(params)
        elif task_type == "gsc_sync":
            return await self._gsc_sync_flow(params)
        elif task_type == "submit_indexing":
            return await self._submit_indexing_flow(params)
        elif task_type == "competitor_analysis":
            return await self._competitor_analysis_flow(params)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _full_website_audit(self, url: str, max_pages: int = 50) -> Dict[str, Any]:
        """Execute full website audit workflow."""
        if not url:
            return {"error": "URL is required"}
        
        print(f"Starting full website audit for: {url}")
        
        # 1. Technical crawl
        print("Phase 1: Technical crawl...")
        audit_data = await self.tools["audit"].crawl(url, max_pages=max_pages)
        
        # 2. GSC data (if authenticated and GSC property available)
        gsc_data = None
        if "gsc" in self.tools:
            try:
                print("Phase 2: Fetching GSC data...")
                gsc_data = self.tools["gsc"].fetch_performance_data(url)
            except Exception as e:
                print(f"GSC data fetch failed: {e}")
        
        # 3. AI Analysis via Ollama
        print("Phase 3: AI analysis...")
        analysis_input = {
            "audit_data": audit_data,
            "gsc_data": gsc_data if gsc_data else "No GSC data available"
        }
        
        analysis = await self.ollama.analyze_audit_results(analysis_input)
        
        # 4. Save to Drive (if authenticated)
        report_id = None
        if "storage" in self.tools:
            try:
                print("Phase 4: Saving report to Drive...")
                folder_structure = self.tools["storage"].create_folder_structure(
                    url.replace("https://", "").replace("http://", "").split("/")[0]
                )
                report_id = self.tools["storage"].create_audit_report(
                    url, audit_data, analysis, folder_structure.get("audits")
                )
            except Exception as e:
                print(f"Drive save failed: {e}")
        
        return {
            "status": "complete",
            "url": url,
            "pages_crawled": audit_data.get("pages_crawled", 0),
            "critical_issues": len(audit_data.get("issues", {}).get("critical", [])),
            "warnings": len(audit_data.get("issues", {}).get("warnings", [])),
            "report_id": report_id,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _keyword_research_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute keyword research workflow."""
        seed = params.get("seed")
        location_code = params.get("location_code", 2840)
        language_code = params.get("language_code", "en")
        depth = params.get("depth", 2)
        
        if not seed:
            return {"error": "Seed keyword is required"}
        
        print(f"Starting keyword research for: {seed}")
        
        # 1. Get seed analysis
        print("Phase 1: Analyzing seed keyword...")
        seed_analysis = self.tools["keywords"].seed_keywords_analysis(
            seed, location_code, language_code
        )
        
        # 2. Get keyword suggestions
        print("Phase 2: Getting keyword suggestions...")
        suggestions = self.tools["keywords"].keyword_suggestions(
            seed, depth, location_code, language_code
        )
        
        # 3. Analyze difficulty for top suggestions
        print("Phase 3: Analyzing keyword difficulty...")
        top_keywords = [kw["keyword"] for kw in suggestions[:20] if kw.get("keyword")]
        difficulty_data = self.tools["keywords"].keyword_difficulty_analysis(
            top_keywords, location_code, language_code
        )
        
        # 4. AI Analysis
        print("Phase 4: AI analysis of keyword opportunities...")
        keyword_list = [kw["keyword"] for kw in difficulty_data[:10]]
        ai_analysis = await self.ollama.analyze(
            f"Analyze these keywords for SEO opportunity: {', '.join(keyword_list)}. "
            f"Seed keyword was: {seed}. "
            "Provide recommendations for content topics and priority.",
            system_prompt="You are an SEO keyword research expert. Provide strategic recommendations."
        )
        
        # 5. Save to Sheets (if authenticated)
        spreadsheet_id = None
        if "storage" in self.tools:
            try:
                print("Phase 5: Saving to Google Sheets...")
                import pandas as pd
                
                df = pd.DataFrame(difficulty_data)
                folder_structure = self.tools["storage"].create_folder_structure(
                    f"Research_{seed.replace(' ', '_')}"
                )
                spreadsheet_id = self.tools["storage"].create_spreadsheet(
                    f"Keyword Research - {seed}",
                    {"Keywords": df},
                    folder_structure.get("keywords")
                )
            except Exception as e:
                print(f"Sheets save failed: {e}")
        
        return {
            "status": "complete",
            "seed": seed,
            "total_keywords": len(suggestions),
            "keywords_analyzed": len(difficulty_data),
            "spreadsheet_id": spreadsheet_id,
            "ai_recommendations": ai_analysis,
            "keywords": difficulty_data[:20],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _rank_tracking_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rank tracking workflow."""
        domain = params.get("domain")
        keywords = params.get("keywords", [])
        location_code = params.get("location_code", 2840)
        
        if not domain or not keywords:
            return {"error": "Domain and keywords are required"}
        
        print(f"Checking rankings for {domain}...")
        
        results = self.tools["ranking"].check_rankings(
            domain, keywords, location_code
        )
        
        # Save to Sheets if authenticated
        spreadsheet_id = None
        if "storage" in self.tools and isinstance(results, list):
            try:
                import pandas as pd
                df = pd.DataFrame(results)
                folder_structure = self.tools["storage"].create_folder_structure(
                    domain.replace("https://", "").replace("http://", "").split("/")[0]
                )
                spreadsheet_id = self.tools["storage"].create_spreadsheet(
                    f"Rankings - {datetime.now().strftime('%Y-%m-%d')}",
                    {"Rankings": df},
                    folder_structure.get("rankings")
                )
            except Exception as e:
                print(f"Sheets save failed: {e}")
        
        return {
            "status": "complete",
            "domain": domain,
            "keywords_checked": len(keywords),
            "results": results,
            "spreadsheet_id": spreadsheet_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _gsc_sync_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GSC data sync workflow."""
        if "gsc" not in self.tools:
            return {"error": "Google authentication required"}
        
        site_url = params.get("site_url")
        days = params.get("days", 28)
        
        if not site_url:
            return {"error": "Site URL is required"}
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = self.tools["gsc"].fetch_performance_data(
            site_url,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        return {
            "status": "complete",
            "site_url": site_url,
            "days": days,
            "rows_fetched": len(data) if isinstance(data, list) else 0,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _submit_indexing_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute URL indexing submission workflow."""
        if "indexing" not in self.tools:
            return {"error": "Google authentication required"}
        
        urls = params.get("urls", [])
        if not urls:
            return {"error": "At least one URL is required"}
        
        results = self.tools["indexing"].submit_batch(urls)
        
        return {
            "status": "complete",
            "urls_submitted": len(urls),
            "results": results,
            "quota_status": self.tools["indexing"].get_quota_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _competitor_analysis_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute competitor analysis workflow."""
        my_domain = params.get("my_domain")
        competitor_domain = params.get("competitor_domain")
        keywords = params.get("keywords", [])
        location_code = params.get("location_code", 2840)
        
        if not my_domain or not competitor_domain:
            return {"error": "Both my_domain and competitor_domain are required"}
        
        print(f"Analyzing {competitor_domain} vs {my_domain}...")
        
        # Get rankings for both
        print("Fetching competitor rankings...")
        my_rankings = self.tools["ranking"].check_rankings(my_domain, keywords, location_code)
        competitor_rankings = self.tools["ranking"].check_rankings(competitor_domain, keywords, location_code)
        
        # AI analysis
        print("Running AI analysis...")
        my_keywords_ranked = [r["keyword"] for r in my_rankings if r.get("rank")]
        competitor_keywords_ranked = [r["keyword"] for r in competitor_rankings if r.get("rank")]
        
        gap_analysis = await self.ollama.analyze_competitor_gap(
            my_keywords_ranked, competitor_keywords_ranked
        )
        
        return {
            "status": "complete",
            "my_domain": my_domain,
            "competitor_domain": competitor_domain,
            "my_rankings": my_rankings,
            "competitor_rankings": competitor_rankings,
            "gap_analysis": gap_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def is_google_authenticated(self) -> bool:
        """Check if Google authentication is available."""
        return self.google_auth.is_authenticated()
    
    def get_auth_url(self) -> str:
        """Get Google OAuth URL."""
        return self.google_auth.get_auth_url()
    
    def exchange_auth_code(self, code: str) -> Dict[str, Any]:
        """Exchange OAuth code for tokens."""
        result = self.google_auth.exchange_code(code)
        # Re-initialize tools with new credentials
        self._init_tools()
        return result
