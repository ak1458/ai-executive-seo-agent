import httpx
import json
from typing import Optional, Dict, Any
import os

class OllamaService:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def analyze(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send a prompt to Ollama and return the response."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt or "You are an expert SEO analyst.",
                "stream": False
            }
            response = await self.client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def analyze_competitor_gap(self, my_keywords: list, competitor_keywords: list) -> Dict[str, Any]:
        """Analyze keyword gap between my site and competitor."""
        prompt = f"""Analyze keyword gap between my site and competitor.

My keywords: {', '.join(my_keywords[:50])}

Competitor keywords: {', '.join(competitor_keywords[:50])}

Provide analysis in this JSON format:
{{
    "opportunities": ["keyword1", "keyword2"],
    "threats": ["keyword1", "keyword2"],
    "content_gaps": ["topic1", "topic2"],
    "recommendations": ["action1", "action2"]
}}

Opportunities are high-value keywords the competitor ranks for that I don't.
Threats are keywords where competitor is outranking me.
Content gaps are topics I should cover."""

        response = await self.analyze(prompt)
        try:
            # Try to parse JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            return {"raw_response": response}
        except json.JSONDecodeError:
            return {"raw_response": response, "error": "Could not parse JSON"}
    
    async def analyze_audit_results(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical audit results and provide recommendations."""
        prompt = f"""Analyze this SEO audit data and provide prioritized recommendations:

{json.dumps(audit_data, indent=2)}

Return structured JSON with:
{{
    "critical_issues": [{"issue": "...", "impact": "...", "fix": "..."}],
    "warnings": [{"issue": "...", "impact": "...", "fix": "..."}],
    "opportunities": [{"area": "...", "potential": "...", "action": "..."}],
    "prioritized_actions": ["action1", "action2", "action3"]
}}

Be specific and actionable."""

        response = await self.analyze(
            prompt,
            system_prompt="You are a technical SEO expert. Provide detailed, actionable recommendations."
        )
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            return {"raw_response": response}
        except json.JSONDecodeError:
            return {"raw_response": response, "error": "Could not parse JSON"}
    
    async def generate_content_brief(self, keyword: str, top_ranking_analysis: str) -> Dict[str, Any]:
        """Generate a content brief based on SERP analysis."""
        prompt = f"""Create a content brief for the keyword: "{keyword}"

Top ranking pages analysis:
{top_ranking_analysis}

Generate a content brief in JSON format:
{{
    "target_keyword": "{keyword}",
    "content_type": "article/guide/list/comparison",
    "suggested_word_count": 1500,
    "key_topics": ["topic1", "topic2", "topic3"],
    "subheadings": ["H2 heading 1", "H2 heading 2"],
    "questions_to_answer": ["question1", "question2"],
    "recommended_internal_links": ["page1", "page2"],
    "content_structure": "Introduction -> Section 1 -> Section 2 -> Conclusion"
}}"""

        response = await self.analyze(
            prompt,
            system_prompt="You are a content strategist. Create detailed content briefs for SEO."
        )
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            return {"raw_response": response}
        except json.JSONDecodeError:
            return {"raw_response": response, "error": "Could not parse JSON"}
