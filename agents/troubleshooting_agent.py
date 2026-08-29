"""
Troubleshooting Agent — handles the technical diagnosis and produces
concrete step-by-step actions for the employee's issue category.
"""
from app.agents.llm_config import call_llm

SYSTEM_PROMPT = """You are the Troubleshooting Agent of an IT Service Desk multi-agent system.
Given an employee's IT issue and its category, produce a short numbered list (3-6 steps)
of practical troubleshooting actions. Be concrete and specific. Do not add any preamble."""

_MOCK_STEPS = {
    "network": [
        "Disconnect and reconnect the VPN client.",
        "Confirm your internet connection is active (try opening a website).",
        "Restart the VPN client application.",
        "Check that your credentials/MFA token have not expired.",
        "Restart your router/laptop network adapter if the issue persists.",
    ],
    "hardware": [
        "Power cycle the device (full shutdown, wait 10s, power on).",
        "Check all cable connections are firmly seated.",
        "Try a different port/cable/peripheral to isolate the fault.",
        "Update the relevant driver from the manufacturer's site.",
    ],
    "software": [
        "Restart the application.",
        "Check for and install pending software updates.",
        "Clear the application cache/temp files.",
        "Reinstall the application if the issue continues.",
    ],
    "account": [
        "Verify Caps Lock is off and credentials are typed correctly.",
        "Use the self-service password reset portal.",
        "Confirm your account has not been locked after failed attempts.",
        "Check MFA device time is synced correctly.",
    ],
    "other": [
        "Gather more detail about when the issue started.",
        "Check if the issue affects other users/devices.",
        "Restart the affected system or service.",
    ],
}


def run_troubleshooting(request_text: str, category: str) -> list:
    def mock():
        steps = _MOCK_STEPS.get(category, _MOCK_STEPS["other"])
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

    raw = call_llm(
        SYSTEM_PROMPT,
        f"Category: {category}\nIssue: \"{request_text}\"",
        mock_fn=mock,
    )
    # normalize into a clean list of steps
    lines = [ln.strip(" -\t") for ln in raw.split("\n") if ln.strip()]
    cleaned = []
    for ln in lines:
        # strip leading "1. " / "1) " numbering
        parts = ln.split(".", 1)
        if len(parts) == 2 and parts[0].strip().isdigit():
            cleaned.append(parts[1].strip())
        else:
            cleaned.append(ln)
    return cleaned[:6] if cleaned else _MOCK_STEPS.get(category, _MOCK_STEPS["other"])
