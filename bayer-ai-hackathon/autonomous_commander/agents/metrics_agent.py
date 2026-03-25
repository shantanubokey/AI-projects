"""
Metrics Agent - Telemetry Analyst
Monitors performance: CPU, latency, memory leak patterns.
"""

import json
import os
import random
from langchain_core.messages import HumanMessage, SystemMessage
from agents.bedrock_llm import get_bedrock_llm
from agents.commander_agent import InvestigationState


METRICS_SYSTEM = """You are the Metrics Agent — a telemetry analyst specializing in performance forensics.

Your specialization:
- Analyze CPU utilization spikes and saturation patterns
- Detect latency degradation (p50, p95, p99 percentiles)
- Identify memory leak patterns and GC pressure
- Correlate resource exhaustion with error timelines
- Spot anomalies in throughput, error rates, and saturation (USE method)

Return findings as JSON:
{
  "cpu_analysis": {...},
  "latency_analysis": {...},
  "memory_analysis": {...},
  "anomalies_detected": [...],
  "performance_timeline": [...],
  "resource_bottlenecks": [...]
}
"""


def get_llm():
    return get_bedrock_llm(max_tokens=2048, temperature=0.1)


def fetch_metrics_from_cloudwatch(alert: dict) -> dict:
    """
    Production hook: fetch metrics from AWS CloudWatch Metrics / X-Ray.
    Replace with real boto3 CloudWatch get_metric_data call in deployment.
    """
    # Simulated telemetry — swap with boto3 CloudWatch Metrics query
    mock_a = {
        "cpu_utilization": {
            "payment-service": [45, 48, 52, 89, 95, 98, 97, 94],  # spike at index 3
            "order-service": [30, 31, 32, 33, 35, 34, 33, 32],
        },
        "latency_p99_ms": {
            "payment-service": [120, 125, 130, 890, 1200, 1450, 1380, 1100],
            "api-gateway": [50, 52, 55, 600, 950, 1100, 980, 750],
        },
        "memory_utilization_percent": {
            "payment-service": [60, 62, 65, 70, 78, 85, 91, 95],  # leak pattern
        },
        "error_rate_percent": {
            "payment-service": [0.1, 0.1, 0.2, 5.4, 18.2, 22.1, 19.8, 15.3],
        },
        "interval_minutes": 5,
        "service": alert.get("service", "unknown"),
    }
    mock_b = {
        "cpu_utilization": {
            "payment-service": [35, 36, 38, 40, 42, 41, 39, 37],
            "db-proxy": [25, 28, 33, 45, 60, 72, 68, 55],
        },
        "latency_p99_ms": {
            "payment-service": [140, 160, 180, 600, 1200, 2200, 1800, 900],
            "api-gateway": [60, 65, 70, 300, 800, 1500, 1200, 650],
        },
        "memory_utilization_percent": {
            "payment-service": [58, 59, 60, 61, 62, 63, 64, 65],
        },
        "error_rate_percent": {
            "payment-service": [0.2, 0.2, 0.3, 1.2, 4.8, 9.6, 7.1, 3.5],
        },
        "interval_minutes": 5,
        "service": alert.get("service", "unknown"),
    }

    variant = os.getenv("MOCK_VARIANT", "default").lower()
    if variant == "random":
        return random.choice([mock_a, mock_b])
    if variant in ("alt", "b", "scenario_b"):
        return mock_b
    return mock_a


def metrics_agent_node(state: InvestigationState) -> InvestigationState:
    if "agents_to_invoke" in state and state["agents_to_invoke"] and "metrics_agent" not in state["agents_to_invoke"]:
        return {
            "metrics_findings": {"skipped": True, "reason": "not selected by commander"},
        }

    llm = get_llm()

    raw_metrics = fetch_metrics_from_cloudwatch(state["alert"])

    messages = [
        SystemMessage(content=METRICS_SYSTEM),
        HumanMessage(content=f"""
Alert: {json.dumps(state['alert'], indent=2)}
Investigation Plan: {state['investigation_plan']}

Raw Telemetry Data:
{json.dumps(raw_metrics, indent=2)}

Perform telemetry analysis and return structured findings.
"""),
    ]

    response = llm.invoke(messages)

    try:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        findings = json.loads(content[start:end])
    except Exception:
        findings = {"raw_analysis": response.content}

    return {
        "messages": [response],
        "metrics_findings": findings,
    }
