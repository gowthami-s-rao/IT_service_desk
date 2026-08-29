"""
Central LLM access point for all agents.

Uses Ollama (local LLM runtime) via langchain-ollama. If Ollama is unreachable
or AGENT_MOCK_MODE=true, falls back to lightweight rule-based mock responses
so the rest of the application (UI, DB, workflow) can be demoed/tested without
a local model installed.
"""
import os
import json
from flask import current_app

_llm_instance = None


def get_llm():
    """Return a cached ChatOllama instance, or None if mock mode is forced."""
    global _llm_instance

    if current_app.config.get("AGENT_MOCK_MODE"):
        return None

    if _llm_instance is not None:
        return _llm_instance

    try:
        from langchain_ollama import ChatOllama
        _llm_instance = ChatOllama(
            model=current_app.config["OLLAMA_MODEL"],
            base_url=current_app.config["OLLAMA_BASE_URL"],
            temperature=0.2,
        )
        return _llm_instance
    except Exception:
        # Ollama not installed / not reachable — degrade gracefully.
        return None


def call_llm(system_prompt: str, user_prompt: str, mock_fn=None):
    """
    Call the LLM with a system + user prompt. Returns plain text.
    If the LLM is unavailable, calls mock_fn() (a callable returning a string)
    so every agent still produces a sensible result.
    """
    llm = get_llm()

    if llm is None:
        return mock_fn() if mock_fn else "[Agent unavailable: Ollama is not running]"

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        return response.content.strip()
    except Exception as exc:
        current_app.logger.warning(f"LLM call failed, falling back to mock: {exc}")
        return mock_fn() if mock_fn else f"[Agent error: {exc}]"


def call_llm_json(system_prompt: str, user_prompt: str, mock_fn=None):
    """Call the LLM and attempt to parse a JSON object from the response."""
    raw = call_llm(system_prompt, user_prompt, mock_fn=mock_fn)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return None
