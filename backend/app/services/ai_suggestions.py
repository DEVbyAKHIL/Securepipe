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

async def get_gemini_suggestion(finding: Finding) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (f"Security finding: {finding.title}\n"
                  f"Severity: {finding.severity}\n"
                  f"Description: {finding.description}\n"
                  f"File: {finding.file}\n"
                  f"Provide a concise 2-sentence fix recommendation for a developer.")
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip()
    except Exception as e:
        logger.error("gemini_fail", err=str(e))
        raise

async def enrich_all_findings(findings: List[Finding]) -> List[Finding]:
    if not settings.AI_ENABLED or not findings:
        for f in findings:
            f.fix_suggestion = f.fix_suggestion or STATIC.get(f.severity.value, STATIC["low"])
        return findings
    priority = [f for f in findings if f.severity.value in ("critical","high")][:10]
    async def enrich(f: Finding):
        try:
            f.fix_suggestion = await get_gemini_suggestion(f)
        except:
            f.fix_suggestion = STATIC.get(f.severity.value, STATIC["low"])
    await asyncio.gather(*[enrich(f) for f in priority])
    for f in findings:
        if not f.fix_suggestion:
            f.fix_suggestion = STATIC.get(f.severity.value, STATIC["low"])
    return findings
