"""
Commander Agent - The Orchestrator
Evaluates initial alerts, develops investigation plans, and coordinates specialized agents.
"""

import json
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agents.bedrock_llm import get_bedrock_llm


# ── State ──────────────────────────────────────────────────────────────────────

class InvestigationState(TypedDict):
    messages: Annotated[list, add_messages]
    alert: dict                        # raw incoming alert
    investigation_plan: List[str]      # ordered steps commander decides
    agents_to_invoke: List[str]        # agents selected by commander
    logs_findings: dict                # output from logs agent
    metrics_findings: dict             # output from metrics agent
    deploy_findings: dict              # output from deploy intelligence agent
    final_report: str                  # consolidated RCA report
    current_step: str                  # tracks which node is active
    logs_override: dict                # optional override for logs input
    commander_precomputed: bool        # skip commander LLM if plan already computed


# ── LLM setup (Bedrock Claude) ─────────────────────────────────────────────────

def get_llm():
    return get_bedrock_llm(max_tokens=4096, temperature=0.1)


# ── Commander Node ─────────────────────────────────────────────────────────────

COMMANDER_SYSTEM = """You are the Commander Agent — an autonomous incident response orchestrator.

Your responsibilities:
1. Evaluate incoming alerts and classify severity (P1/P2/P3).
2. Develop a step-by-step investigation plan.
3. Decide which specialized agents to invoke: logs_agent, metrics_agent, deploy_agent.
4. Synthesize findings into a Root Cause Analysis (RCA) report.

When given an alert, respond with a JSON investigation plan:
{
  "severity": "P1|P2|P3",
  "summary": "brief description",
  "plan": ["step1", "step2", ...],
  "agents_to_invoke": ["logs_agent", "metrics_agent", "deploy_agent"]
}

Select agents based on the alert error type. For example:
- Log or exception errors → prefer logs_agent
- Latency/throughput/memory errors → prefer metrics_agent
- Deployment/config changes → prefer deploy_agent
If unsure, invoke all three.
"""

def commander_node(state: InvestigationState) -> InvestigationState:
    if state.get("commander_precomputed") and state.get("investigation_plan") and state.get("agents_to_invoke"):
        return {
            **state,
            "current_step": "investigating",
        }

    llm = get_llm()
    alert = state["alert"]

    messages = [
        SystemMessage(content=COMMANDER_SYSTEM),
        HumanMessage(content=f"Incoming alert:\n{json.dumps(alert, indent=2)}\n\nDevelop an investigation plan."),
    ]

    response = llm.invoke(messages)

    # Parse plan from response
    try:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        plan_data = json.loads(content[start:end])
    except Exception:
        plan_data = {
            "severity": "P2",
            "summary": "Unable to parse plan, defaulting to full investigation.",
            "plan": ["check logs", "check metrics", "check deployments"],
            "agents_to_invoke": ["logs_agent", "metrics_agent", "deploy_agent"],
        }

    return {
        **state,
        "messages": state["messages"] + [response],
        "investigation_plan": plan_data.get("plan", []),
        "agents_to_invoke": plan_data.get("agents_to_invoke", ["logs_agent", "metrics_agent", "deploy_agent"]),
        "current_step": "investigating",
    }


# ── Synthesis Node ─────────────────────────────────────────────────────────────

SYNTHESIS_SYSTEM = """You are the Commander Agent synthesizing findings from your specialized investigators.
Produce a concise Root Cause Analysis (RCA) report with:
- Root Cause
- Contributing Factors
- Timeline of Events
- Recommended Remediation Steps
"""

def synthesis_node(state: InvestigationState) -> InvestigationState:
    llm = get_llm()

    context = f"""
Alert: {json.dumps(state['alert'], indent=2)}
Investigation Plan: {state['investigation_plan']}

=== Logs Agent Findings ===
{json.dumps(state.get('logs_findings', {}), indent=2)}

=== Metrics Agent Findings ===
{json.dumps(state.get('metrics_findings', {}), indent=2)}

=== Deploy Intelligence Findings ===
{json.dumps(state.get('deploy_findings', {}), indent=2)}
"""

    messages = [
        SystemMessage(content=SYNTHESIS_SYSTEM),
        HumanMessage(content=context),
    ]

    response = llm.invoke(messages)

    return {
        **state,
        "messages": state["messages"] + [response],
        "final_report": response.content,
        "current_step": "complete",
    }


# ── Router ─────────────────────────────────────────────────────────────────────

def route_after_commander(state: InvestigationState) -> str:
    """Always fan out to all three agents in parallel via a coordinator."""
    return "logs_agent"
