"""
Drop-in replacement for backend/app/services/ai_suggestions.py

WHY THIS CHANGES:
1. Migrated to `google-genai` SDK.
2. Uses **Batch Prompting** to send up to 5 findings in a single Gemini request,
   reducing latency and preventing free-tier rate limits (15 RPM) from being quickly exhausted.
3. Added dynamic wait extraction for `429 RESOURCE_EXHAUSTED` responses.
"""

import asyncio
import json
import re
from typing import List, Dict
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
_last_status = "not_tested"


def get_last_status() -> str:
    return _last_status


def set_last_status(status: str):
    global _last_status
    _last_status = status


def _get_client():
    """Lazily create a single google-genai Client."""
    global _client
    if _client is None:
        from google import genai as google_genai
        _client = google_genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={'timeout': 120000}
        )
    return _client


def _extract_wait_time(error_msg: str, default: int) -> int:
    """Extract 'Please retry in X.Xs.' from error messages if present."""
    match = re.search(r"Please retry in ([\d\.]+)s", error_msg)
    if match:
        try:
            return int(float(match.group(1))) + 1  # Add 1s buffer
        except (ValueError, TypeError):
            pass
    return default


async def get_gemini_batch_suggestions(findings: List[Finding], retries: int = 2) -> Dict[str, str]:
    if not findings:
        return {}
        
    client = _get_client()
    model_name = settings.GEMINI_MODEL if hasattr(settings, "GEMINI_MODEL") else "gemini-2.5-flash"
    
    # Prepare finding data for the prompt
    findings_data = []
    for f in findings:
        findings_data.append({
            "id": f.id,
            "title": f.title,
            "severity": f.severity.value,
            "description": f.description[:500],  # Truncate to save tokens
            "file": f.file
        })
        
    prompt = (
        "You are a strict JSON API. Provide a concise 2-sentence fix recommendation for each of the following security findings.\n"
        f"Findings:\n{json.dumps(findings_data, indent=2)}\n\n"
        "Return ONLY a JSON array of objects, with each object containing EXACTLY two keys: 'id' (the finding ID) and 'suggestion' (the 2-sentence fix string). "
        "Do not include markdown codeblocks (like ```json), just output the raw JSON."
    )
    
    # We log 'ai_request_started' only once per batch!
    logger.info("ai_batch_request_started", count=len(findings), model=model_name)
    last_err = None
    
    for attempt in range(retries + 1):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
            )
            if not getattr(response, "candidates", None):
                logger.warning("gemini_safety_filtered", batch_size=len(findings))
                raise ValueError("Gemini returned no candidates (likely safety-filtered)")
            
            text = (response.text or "").strip()
            if not text:
                logger.warning("gemini_empty_response", batch_size=len(findings))
                raise ValueError("Gemini returned an empty response")
                
            # Strip markdown if present
            if text.startswith("```json"):
                text = text.replace("```json", "", 1)
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            try:
                parsed = json.loads(text)
                if not isinstance(parsed, list):
                    raise ValueError("Gemini returned JSON, but not an array")
                
                result_map = {item["id"]: item["suggestion"] for item in parsed if "id" in item and "suggestion" in item}
                logger.info("ai_batch_request_success", count=len(result_map), model=model_name)
                return result_map
            except json.JSONDecodeError as e:
                logger.error("gemini_json_parse_error", text=text)
                raise ValueError(f"Failed to parse Gemini JSON: {e}")
                
        except Exception as e:
            last_err = e
            msg = str(e)
            is_rate_limit = "429" in msg or "RESOURCE_EXHAUSTED" in msg.upper()
            if is_rate_limit and attempt < retries:
                wait = _extract_wait_time(msg, 5 * (attempt + 1))
                logger.warning("gemini_rate_limit", attempt=attempt + 1, wait=wait, batch_size=len(findings))
                await asyncio.sleep(wait)
                continue
                
            # Log the REAL error without exposing the API key
            safe_msg = msg
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY in safe_msg:
                safe_msg = safe_msg.replace(settings.GEMINI_API_KEY, "***REDACTED***")
                
            logger.error("gemini_fail", err=safe_msg, attempt=attempt + 1)
            raise ValueError(safe_msg)
            
    raise last_err


async def enrich_all_findings(findings: List[Finding]) -> List[Finding]:
    model_name = settings.GEMINI_MODEL if hasattr(settings, "GEMINI_MODEL") else "gemini-2.5-flash"
    
    if not settings.AI_ENABLED or not findings:
        set_last_status("unavailable")
        for f in findings:
            f.suggestion = f.suggestion or STATIC.get(f.severity.value, STATIC["low"])
            f.suggestion_source = "unavailable"
        return findings

    # Top 5 critical/high only
    priority = [f for f in findings if f.severity.value in ("critical", "high")][:5]

    if priority:
        try:
            # Send exactly 1 request for the entire batch
            suggestions_map = await get_gemini_batch_suggestions(priority)
            
            for f in priority:
                if f.id in suggestions_map:
                    f.suggestion = suggestions_map[f.id]
                    f.suggestion_source = "gemini"
                    f.model = model_name
                    f.error_reason = None
                else:
                    # In case Gemini didn't return an ID, fallback safely
                    f.suggestion = STATIC.get(f.severity.value, STATIC["low"])
                    f.suggestion_source = "fallback"
                    f.error_reason = "Gemini did not return a suggestion for this ID in the batch JSON"
                    
            logger.info("ai_batch_enrichment_summary", attempted=len(priority), succeeded=len(suggestions_map))
            set_last_status("success")
            
        except Exception as e:
            safe_msg = str(e)
            logger.error("ai_batch_fallback_activated", count=len(priority), reason=safe_msg)
            for f in priority:
                f.suggestion = STATIC.get(f.severity.value, STATIC["low"])
                f.suggestion_source = "fallback"
                f.error_reason = safe_msg
            set_last_status("fallback")

    enriched_ids = {f.id for f in priority}
    for f in findings:
        if f.id not in enriched_ids and not f.suggestion:
            f.suggestion = STATIC.get(f.severity.value, STATIC["low"])
            f.suggestion_source = "unavailable"

    return findings
