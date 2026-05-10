import asyncio
from typing import List
from app.core.models import Finding
from app.core.config import settings
from app.core.logging import logger

STATIC = {
    "critical": "Immediate action required. Rotate credentials, patch the dependency, and conduct a full security review.",
    "high":     "Prioritize this fix in the next sprint. Apply the vendor patch or configuration change.",
    "medium":   "Schedule remediation. Follow OWASP guidelines for this vulnerability class.",
    "low":      "Address in routine maintenance. Low exploitability but still worth fixing.",
}

async def get_gemini_suggestion(finding: Finding, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = (
                f"Security finding: {finding.title}
"
                f"Severity: {finding.severity}
"
                f"Description: {finding.description}
"
                f"File: {finding.file}
"
                f"Provide a concise 2-sentence fix recommendation for a developer."
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                wait = 5 * (attempt + 1)  # 5s on first retry, 10s on second
                logger.warning("gemini_rate_limit", attempt=attempt + 1, wait=wait)
                await asyncio.sleep(wait)
            else:
                logger.error("gemini_fail", err=str(e))
                raise

async def enrich_all_findings(findings: List[Finding]) -> List[Finding]:
    if not settings.AI_ENABLED or not findings:
        for f in findings:
            f.fix_suggestion = f.fix_suggestion or STATIC.get(f.severity.value, STATIC["low"])
        return findings

    # Only enrich top 5 critical/high findings — avoids free-tier burst limit
    priority = [f for f in findings if f.severity.value in ("critical", "high")][:5]

    # Sequential with 1.5s gap — keeps usage under 15 req/min free tier limit
    for f in priority:
        try:
            f.fix_suggestion = await get_gemini_suggestion(f)
            await asyncio.sleep(1.5)
        except Exception:
            f.fix_suggestion = STATIC.get(f.severity.value, STATIC["low"])

    # All remaining findings get static suggestions
    enriched_ids = {f.id for f in priority}
    for f in findings:
        if f.id not in enriched_ids and not f.fix_suggestion:
            f.fix_suggestion = STATIC.get(f.severity.value, STATIC["low"])

    return findings