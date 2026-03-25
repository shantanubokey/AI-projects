"""
LangGraph Workflow — Autonomous Commander Multi-Agent System
Defines the graph: Commander → [Logs | Metrics | Deploy] → Synthesis
"""

from langgraph.graph import StateGraph, END
from agents.commander_agent import InvestigationState, commander_node, synthesis_node
from agents.logs_agent import logs_agent_node
from agents.metrics_agent import metrics_agent_node
from agents.deploy_agent import deploy_agent_node


def build_graph() -> StateGraph:
    """Build and compile the multi-agent investigation graph."""

    graph = StateGraph(InvestigationState)

    # ── Register nodes ──────────────────────────────────────────────────────────
    graph.add_node("commander", commander_node)
    graph.add_node("logs_agent", logs_agent_node)
    graph.add_node("metrics_agent", metrics_agent_node)
    graph.add_node("deploy_agent", deploy_agent_node)
    graph.add_node("synthesis", synthesis_node)

    # ── Entry point ─────────────────────────────────────────────────────────────
    graph.set_entry_point("commander")

    # ── Commander fans out to all three specialized agents ──────────────────────
    # LangGraph parallel fan-out: commander → all three agents simultaneously
    graph.add_edge("commander", "logs_agent")
    graph.add_edge("commander", "metrics_agent")
    graph.add_edge("commander", "deploy_agent")

    # ── All three agents converge into synthesis ────────────────────────────────
    graph.add_edge("logs_agent", "synthesis")
    graph.add_edge("metrics_agent", "synthesis")
    graph.add_edge("deploy_agent", "synthesis")

    # ── Synthesis → END ─────────────────────────────────────────────────────────
    graph.add_edge("synthesis", END)

    return graph.compile()


def run_investigation(
    alert: dict,
    logs_override: dict | None = None,
    precomputed_plan: list[str] | None = None,
    precomputed_agents: list[str] | None = None,
) -> dict:
    """
    Entry point to run a full autonomous investigation.

    Args:
        alert: dict with keys like service, error_type, timestamp, severity_hint

    Returns:
        Final state with all findings and RCA report
    """
    app = build_graph()

    initial_state: InvestigationState = {
        "messages": [],
        "alert": alert,
        "investigation_plan": precomputed_plan or [],
        "agents_to_invoke": precomputed_agents or ["logs_agent", "metrics_agent", "deploy_agent"],
        "logs_findings": {},
        "metrics_findings": {},
        "deploy_findings": {},
        "final_report": "",
        "current_step": "start",
    }
    if logs_override:
        initial_state["logs_override"] = logs_override
    if precomputed_plan or precomputed_agents:
        initial_state["commander_precomputed"] = True

    final_state = app.invoke(initial_state)
    return final_state
