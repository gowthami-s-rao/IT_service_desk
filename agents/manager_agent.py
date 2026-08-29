"""
Manager Agent — understands the incoming request and classifies it so the
workflow can be delegated to the right specialist agents.
"""
from app.agents.llm_config import call_llm_json

CATEGORIES = ["network", "hardware", "software", "account", "other"]

SYSTEM_PROMPT = """You are the Manager Agent of an IT Service Desk multi-agent system.
Your only job is to read an employee's IT request and classify it.
Respond ONLY with a JSON object of the form:
{"category": "network|hardware|software|account|other", "priority": "low|medium|high|critical", "summary": "<one line summary>"}
No extra text, no markdown fences."""


def _mock_classify(request_text: str):
    text = request_text.lower()
    if any(k in text for k in ["vpn", "wifi", "network", "internet", "connect"]):
        category = "network"
    elif any(k in text for k in ["laptop", "monitor", "printer", "mouse", "keyboard", "device", "hardware"]):
        category = "hardware"
    elif any(k in text for k in ["password", "login", "account", "locked", "access", "mfa", "2fa"]):
        category = "account"
    elif any(k in text for k in ["software", "app", "install", "update", "crash", "error", "bug"]):
        category = "software"
    else:
        category = "other"

    priority = "high" if any(k in text for k in ["urgent", "asap", "critical", "down", "cannot work"]) else "medium"
    return f'{{"category": "{category}", "priority": "{priority}", "summary": "{request_text[:80]}"}}'


def classify_request(request_text: str) -> dict:
    result = call_llm_json(
        SYSTEM_PROMPT,
        f"Employee request: \"{request_text}\"",
        mock_fn=lambda: _mock_classify(request_text),
    )
    if not result or result.get("category") not in CATEGORIES:
        # graceful fallback if JSON parsing failed
        result = {
            "category": "other",
            "priority": "medium",
            "summary": request_text[:80],
        }
    return result
