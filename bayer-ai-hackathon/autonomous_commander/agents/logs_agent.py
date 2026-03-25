"""
Logs Agent - Forensic Expert
Deep scans distributed logs to find stack traces and error correlations.
"""

import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrock
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
    from langchain_aws import ChatBedrock
    return ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
        model_kwargs={"max_tokens": 2048, "temperature": 0.1},
    )


def fetch_logs_from_cloudwatch(alert: dict) -> dict:
    """
    Production hook: fetch logs from AWS CloudWatch Logs Insights.
    Replace with real boto3 CloudWatch query in deployment.
    """
    # Simulated log data — swap with boto3 CloudWatch Logs Insights query
    return {
        "log_groups": ["/aws/lambda/payment-service", "/aws/ecs/order-service"],
        "sample_errors": [
            "ERROR 2026-03-25T10:23:11Z [payment-service] NullPointerException at PaymentProcessor.java:142",
            "ERROR 2026-03-25T10:23:12Z [order-service] Connection timeout to payment-service after 30000ms",
            "FATAL 2026-03-25T10:23:15Z [api-gateway] Circuit breaker OPEN for payment-service",
        ],
        "trace_ids": ["1-abc123", "1-abc124"],
        "time_range": alert.get("time_range", "last 30 minutes"),
    }


def logs_agent_node(state: InvestigationState) -> InvestigationState:
    llm = get_llm()

    # Fetch raw logs (CloudWatch in production)
    raw_logs = fetch_logs_from_cloudwatch(state["alert"])

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
        **state,
        "messages": state["messages"] + [response],
        "logs_findings": findings,
    }
