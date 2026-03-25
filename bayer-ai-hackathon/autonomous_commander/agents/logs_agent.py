"""
Logs Agent - Forensic Expert
Deep scans distributed logs to find stack traces and error correlations.
"""

import json
import os
import random
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from agents.bedrock_llm import get_bedrock_llm
from agents.commander_agent import InvestigationState


LOGS_SYSTEM = """You are the Logs Agent — a forensic expert in distributed systems log analysis.

Your specialization:
- Deep scan distributed logs across microservices
- Identify stack traces, exception chains, and error propagation paths
- Correlate errors across services using trace IDs and timestamps
- Detect log anomaly patterns (error spikes, repeated failures, cascading errors)

Given an alert and investigation plan, analyze the logs context and return findings as JSON:
{
  "stack_traces": [...],
  "error_correlations": [...],
  "affected_services": [...],
  "anomaly_patterns": [...],
  "root_cause_indicators": [...]
}
"""


def get_llm():
    return get_bedrock_llm(max_tokens=2048, temperature=0.1)


def _load_custom_mock(alert: dict) -> dict | None:
    mock_path = os.getenv("MOCK_LOGS_FILE")
    if mock_path:
        path = Path(mock_path)
    else:
        path = Path(__file__).resolve().parents[1] / "mock_inputs" / "logs_mock.json"

    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "time_range" not in data:
            data["time_range"] = alert.get("time_range", "last 30 minutes")
        return data
    except Exception:
        return None


def fetch_logs_from_cloudwatch(alert: dict) -> dict:
    """
    Production hook: fetch logs from AWS CloudWatch Logs Insights.
    Replace with real boto3 CloudWatch query in deployment.
    """
    # Simulated log data — swap with boto3 CloudWatch Logs Insights query
    custom = _load_custom_mock(alert)
    if custom:
        return custom

    mock_a = {
        "log_groups": ["/aws/lambda/payment-service", "/aws/ecs/order-service"],
        "sample_errors": [
            "ERROR 2026-03-25T10:23:11Z [payment-service] NullPointerException at PaymentProcessor.java:142",
            "ERROR 2026-03-25T10:23:12Z [order-service] Connection timeout to payment-service after 30000ms",
            "FATAL 2026-03-25T10:23:15Z [api-gateway] Circuit breaker OPEN for payment-service",
        ],
        "trace_ids": ["1-abc123", "1-abc124"],
        "time_range": alert.get("time_range", "last 30 minutes"),
    }
    mock_b = {
        "log_groups": ["/aws/ecs/inventory-service", "/aws/ecs/payment-service"],
        "sample_errors": [
            "ERROR 2026-03-25T11:02:41Z [inventory-service] Deadlock detected in InventoryLockManager.java:88",
            "WARN  2026-03-25T11:02:45Z [payment-service] Retry storm detected on /api/v1/checkout",
            "ERROR 2026-03-25T11:02:49Z [payment-service] Database pool exhausted (active=50, max=50)",
            "FATAL 2026-03-25T11:03:05Z [api-gateway] Upstream timeout after 60000ms",
        ],
        "trace_ids": ["1-def456", "1-def457", "1-def458"],
        "time_range": alert.get("time_range", "last 30 minutes"),
    }

    variant = os.getenv("MOCK_VARIANT", "default").lower()
    if variant == "random":
        return random.choice([mock_a, mock_b])
    if variant in ("alt", "b", "scenario_b"):
        return mock_b
    return mock_a


def logs_agent_node(state: InvestigationState) -> InvestigationState:
    if "agents_to_invoke" in state and state["agents_to_invoke"] and "logs_agent" not in state["agents_to_invoke"]:
        return {
            "logs_findings": {"skipped": True, "reason": "not selected by commander"},
        }

    llm = get_llm()

    # Fetch raw logs (CloudWatch in production)
    raw_logs = state.get("logs_override") or fetch_logs_from_cloudwatch(state["alert"])

    messages = [
        SystemMessage(content=LOGS_SYSTEM),
        HumanMessage(content=f"""
Alert: {json.dumps(state['alert'], indent=2)}
Investigation Plan: {state['investigation_plan']}

Raw Log Data:
{json.dumps(raw_logs, indent=2)}

Perform forensic log analysis and return structured findings.
"""),
    ]

    response = llm.invoke(messages)

    # Parse findings
    try:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        findings = json.loads(content[start:end])
    except Exception:
        findings = {"raw_analysis": response.content}

    return {
        "messages": [response],
        "logs_findings": findings,
    }
