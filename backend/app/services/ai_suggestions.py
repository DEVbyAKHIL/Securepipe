"""
Drop-in replacement for backend/app/services/ai_suggestions.py

WHY THIS CHANGES:
1. `google-generativeai` (the SDK the original file used) was fully deprecated by
   Google on 2025-11-30 — no more bug fixes, no guaranteed access to newer models.
   This file migrates to the current `google-genai` package instead.
     pip uninstall google-generativeai
     pip install google-genai
   and update requirements.txt accordingly.
2. The original silently swallowed the *real* Gemini error into a generic static
   fallback, which is why the AI-enrichment issue was hard to diagnose. This
   version logs the real exception message and exposes which source (ai/static)
   produced each suggestion, so failures are visible instead of invisible.
3. Empty/safety-filtered responses (response.candidates == []) used to throw an
   unhandled ValueError when accessing `.text` — now checked explicitly.
"""

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

_client = None


def _get_client():
    """Lazily create a single google-genai Client (thread-safe enough for our usage)."""
    global _client
    if _client is None:
        from google import genai as google_genai
        _client = google_genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def get_gemini_suggestion(finding: Finding, retries: int = 2) -> str:
    client = _get_client()
    prompt = (
        f"Security finding: {finding.title}\n"
        f"Severity: {finding.severity}\n"
        f"Description: {finding.description}\n"
        f"File: {finding.file}\n"
        "Provide a concise 2-sentence fix recommendation for a developer."
    )
    last_err = None
    for attempt in range(retries + 1):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL if hasattr(settings, "GEMINI_MODEL") else "gemini-2.5-flash",
                contents=prompt,
            )
            if not getattr(response, "candidates", None):
                raise ValueError("Gemini returned no candidates (likely safety-filtered)")
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Gemini returned an empty response")
            return text
        except Exception as e:
            last_err = e
            msg = str(e)
            is_rate_limit = "429" in msg or "RESOURCE_EXHAUSTED" in msg.upper()
            if is_rate_limit and attempt < retries:
                wait = 5 * (attempt + 1)
                logger.warning("gemini_rate_limit", attempt=attempt + 1, wait=wait, finding_id=finding.id)
                await asyncio.sleep(wait)
                continue
            # Log the REAL error instead of hiding it behind a generic static fallback.
            logger.error("gemini_fail", err=msg, finding_id=finding.id, attempt=attempt + 1)
            raise
    raise last_err  # pragma: no cover — unreachable, keeps type-checkers happy


async def enrich_all_findings(findings: List[Finding]) -> List[Finding]:
    if not settings.AI_ENABLED or not findings:
        for f in findings:
            f.fix_suggestion = f.fix_suggestion or STATIC.get(f.severity.value, STATIC["low"])
        return findings

    # Top 5 critical/high only — stays under Gemini free-tier RPM limits.
    priority = [f for f in findings if f.severity.value in ("critical", "high")][:5]

    ai_success, ai_failed = 0, 0
    for f in priority:
        try:
            f.fix_suggestion = await get_gemini_suggestion(f)
            ai_success += 1
        except Exception as e:
            ai_failed += 1
            logger.error("gemini_enrichment_fallback", finding_id=f.id, reason=str(e))
            f.fix_suggestion = STATIC.get(f.severity.value, STATIC["low"])
        await asyncio.sleep(1.5)  # stay under free-tier burst limits

    if priority:
        logger.info("ai_enrichment_summary", attempted=len(priority), succeeded=ai_success, failed=ai_failed)

    enriched_ids = {f.id for f in priority}
    for f in findings:
        if f.id not in enriched_ids and not f.fix_suggestion:
            f.fix_suggestion = STATIC.get(f.severity.value, STATIC["low"])

    return findings
