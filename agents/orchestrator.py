"""
Orchestrator — wires the five agents into a LangGraph StateGraph that
mirrors the flowchart exactly:

Employee -> Manager Agent (classify) -> Troubleshooting Agent
         -> Knowledge Agent -> Database Agent -> Problem solved?
             YES -> Response Agent -> Close ticket
             NO  -> Human Escalation -> Close ticket
"""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.agents import manager_agent, troubleshooting_agent, knowledge_agent, database_agent, response_agent


class DeskState(TypedDict, total=False):
    employee_id: int
    request_text: str
    category: str
    priority: str
    summary: str
    steps: List[str]
    kb_articles: List[Dict[str, Any]]
    db_context: Dict[str, Any]
    problem_solved: bool
    final_response: str
    escalated: bool
    log: List[Dict[str, str]]


def _log(state: DeskState, agent: str, message: str) -> DeskState:
    state.setdefault("log", [])
    state["log"].append({"agent": agent, "message": message})
    return state


def manager_node(state: DeskState) -> DeskState:
    result = manager_agent.classify_request(state["request_text"])
    state["category"] = result["category"]
    state["priority"] = result["priority"]
    state["summary"] = result.get("summary", state["request_text"][:80])
    _log(state, "manager_agent",
         f"Classified as '{state['category']}' (priority: {state['priority']}). Delegating to Troubleshooting Agent.")
    return state


def troubleshooting_node(state: DeskState) -> DeskState:
    steps = troubleshooting_agent.run_troubleshooting(state["request_text"], state["category"])
    state["steps"] = steps
    _log(state, "troubleshooting_agent", f"Generated {len(steps)} troubleshooting step(s).")
    return state


def knowledge_node(state: DeskState) -> DeskState:
    articles = knowledge_agent.search_knowledge_base(state["request_text"], state["category"])
    state["kb_articles"] = articles
    _log(state, "knowledge_agent", f"Found {len(articles)} relevant knowledge base article(s).")
    return state


def database_node(state: DeskState) -> DeskState:
    ctx = database_agent.check_employee_context(state["employee_id"], state["category"])
    state["db_context"] = ctx
    _log(state, "database_agent",
         f"Checked employee/device records — {ctx['device_count']} device(s) on file, "
         f"{len(ctx['flagged_devices'])} flagged.")
    return state


def decision_node(state: DeskState) -> DeskState:
    solved = response_agent.decide_if_solved(
        state["category"], state["steps"], state["kb_articles"], state["db_context"]
    )
    state["problem_solved"] = solved
    _log(state, "database_agent", f"Problem solved decision: {'YES' if solved else 'NO'}.")
    return state


def response_node(state: DeskState) -> DeskState:
    text = response_agent.compose_response(
        state["request_text"], state["category"], state["steps"], state["kb_articles"], state["db_context"]
    )
    state["final_response"] = text
    state["escalated"] = False
    _log(state, "response_agent", "Prepared final response for employee. Ticket resolved.")
    return state


def escalation_node(state: DeskState) -> DeskState:
    state["final_response"] = (
        "We attempted automated troubleshooting but couldn't fully resolve this issue. "
        "Your ticket has been escalated to a human IT technician who will follow up shortly."
    )
    state["escalated"] = True
    _log(state, "human_escalation", "Automated resolution insufficient — escalated to human technician.")
    return state


def _route_after_decision(state: DeskState) -> str:
    return "response" if state.get("problem_solved") else "escalation"


def build_graph():
    graph = StateGraph(DeskState)

    graph.add_node("manager", manager_node)
    graph.add_node("troubleshooting", troubleshooting_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("database", database_node)
    graph.add_node("decision", decision_node)
    graph.add_node("response", response_node)
    graph.add_node("escalation", escalation_node)

    graph.set_entry_point("manager")
    graph.add_edge("manager", "troubleshooting")
    graph.add_edge("troubleshooting", "knowledge")
    graph.add_edge("knowledge", "database")
    graph.add_edge("database", "decision")
    graph.add_conditional_edges("decision", _route_after_decision, {
        "response": "response",
        "escalation": "escalation",
    })
    graph.add_edge("response", END)
    graph.add_edge("escalation", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_service_desk(employee_id: int, request_text: str) -> DeskState:
    graph = get_graph()
    initial_state: DeskState = {
        "employee_id": employee_id,
        "request_text": request_text,
        "log": [{"agent": "employee", "message": f'Submitted request: "{request_text}"'}],
    }
    result = graph.invoke(initial_state)
    return result
