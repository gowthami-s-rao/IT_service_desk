"""
Response Agent — synthesizes the manager's classification, the
troubleshooting steps, the knowledge base results, and the database
context into a single final response for the employee, and decides
whether the problem is likely solved or needs human escalation.
"""
from app.agents.llm_config import call_llm

SYSTEM_PROMPT = """You are the Response Agent of an IT Service Desk multi-agent system.
You will receive the employee's issue, troubleshooting steps, relevant knowledge base
articles, and account/device context. Write a warm, clear, concise final response for
the employee (plain text, no markdown headers) that:
1) Acknowledges the issue
2) Gives the troubleshooting steps in order
3) References any relevant knowledge base guidance
4) Ends with a clear next step
Keep it under 180 words."""


def compose_response(request_text, category, steps, kb_articles, db_context) -> str:
    kb_text = "\n".join(f"- {a['title']}: {a['content'][:150]}" for a in kb_articles) or "None found."
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    flagged = db_context.get("flagged_devices", [])
    flagged_text = ", ".join(d["device_name"] for d in flagged) or "None"

    def mock():
        base = (
            f"Thanks for reaching out about this — I can see this falls under {category}. "
            f"Here's what to try:\n{steps_text}\n\n"
        )
        if kb_articles:
            base += f"Related help article: {kb_articles[0]['title']}.\n\n"
        if flagged:
            base += f"Note: we also noticed an issue with your device(s): {flagged_text}. "
        base += "If these steps don't resolve it, this ticket will be escalated to a human technician."
        return base

    user_prompt = (
        f"Issue: \"{request_text}\"\nCategory: {category}\n\n"
        f"Troubleshooting steps:\n{steps_text}\n\n"
        f"Knowledge base:\n{kb_text}\n\n"
        f"Device context: {db_context.get('device_count', 0)} device(s) on file, "
        f"flagged devices: {flagged_text}, "
        f"open duplicate ticket: {db_context.get('has_open_duplicate')}"
    )

    return call_llm(SYSTEM_PROMPT, user_prompt, mock_fn=mock)


def decide_if_solved(category: str, steps: list, kb_articles: list, db_context: dict) -> bool:
    """
    Heuristic used to mirror the flowchart's "Problem solved?" decision node.
    In a full production system this could poll the employee or re-run
    diagnostics; here we use available signal (KB coverage + no flagged
    hardware + no unresolved duplicate ticket) to decide automatically.
    """
    if db_context.get("flagged_devices"):
        return False
    if db_context.get("has_open_duplicate"):
        return False
    if not kb_articles and not steps:
        return False
    return True
