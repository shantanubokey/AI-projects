"""
Deploy Intelligence Agent - The Historian
Maps real-time errors against CI/CD deployment timeline and service configuration changes.
"""

import json
import os
import random
from langchain_core.messages import HumanMessage, SystemMessage
from agents.bedrock_llm import get_bedrock_llm
from agents.commander_agent import InvestigationState


DEPLOY_SYSTEM = """You are the Deploy Intelligence Agent — a deployment historian and change analyst.

Your specialization:
- Map real-time errors against CI/CD deployment timelines
- Correlate incidents with recent service configuration changes
- Identify risky deployments (feature flags, schema migrations, dependency upgrades)
- Detect rollback candidates based on error onset timing
- Cross-reference AWS CodeDeploy, ECS task definition changes, and SSM Parameter Store updates

Return findings as JSON:
{
  "recent_deployments": [...],
  "config_changes": [...],
  "correlation_score": 0.0-1.0,
  "likely_culprit_deployment": {...},
  "rollback_recommendation": "yes|no|investigate",
  "change_timeline": [...]
}
"""


def get_llm():
    return get_bedrock_llm(max_tokens=2048, temperature=0.1)


def fetch_deployment_history(alert: dict) -> dict:
    """
    Production hook: fetch from AWS CodeDeploy, ECS, SSM Parameter Store.
    Replace with real boto3 calls in deployment.
    """
    # Simulated deployment history — swap with boto3 CodeDeploy list_deployments
    mock_a = {
        "recent_deployments": [
            {
                "id": "d-ABC123",
                "service": "payment-service",
                "version": "v2.4.1",
                "deployed_at": "2026-03-25T09:45:00Z",  # ~38 min before incident
                "deployed_by": "ci-pipeline",
                "changes": ["upgraded stripe-sdk 4.2.0 -> 4.3.0", "increased connection pool size"],
                "status": "SUCCEEDED",
            },
            {
                "id": "d-DEF456",
                "service": "order-service",
                "version": "v1.8.3",
                "deployed_at": "2026-03-25T08:00:00Z",
                "deployed_by": "ci-pipeline",
                "changes": ["bug fix: order status update"],
                "status": "SUCCEEDED",
            },
        ],
        "config_changes": [
            {
                "parameter": "/payment-service/db/max_connections",
                "old_value": "50",
                "new_value": "200",
                "changed_at": "2026-03-25T09:50:00Z",
                "changed_by": "ops-team",
            }
        ],
        "incident_start": alert.get("timestamp", "2026-03-25T10:23:00Z"),
        "service": alert.get("service", "unknown"),
    }
    mock_b = {
        "recent_deployments": [
            {
                "id": "d-GHI789",
                "service": "payment-service",
                "version": "v2.4.2",
                "deployed_at": "2026-03-25T10:05:00Z",  # ~18 min before incident
                "deployed_by": "ci-pipeline",
                "changes": ["introduced read-replica routing", "new DB retry policy"],
                "status": "SUCCEEDED",
            },
            {
                "id": "d-JKL012",
                "service": "orders-db",
                "version": "schema-2026-03-25",
                "deployed_at": "2026-03-25T09:55:00Z",
                "deployed_by": "db-migrations",
                "changes": ["added index on orders(user_id)", "updated lock timeout to 5s"],
                "status": "SUCCEEDED",
            },
        ],
        "config_changes": [
            {
                "parameter": "/payment-service/db/pool_size",
                "old_value": "80",
                "new_value": "40",
                "changed_at": "2026-03-25T10:00:00Z",
                "changed_by": "ops-team",
            }
        ],
        "incident_start": alert.get("timestamp", "2026-03-25T10:23:00Z"),
        "service": alert.get("service", "unknown"),
    }

    variant = os.getenv("MOCK_VARIANT", "default").lower()
    if variant == "random":
        return random.choice([mock_a, mock_b])
    if variant in ("alt", "b", "scenario_b"):
        return mock_b
    return mock_a


def deploy_agent_node(state: InvestigationState) -> InvestigationState:
    if "agents_to_invoke" in state and state["agents_to_invoke"] and "deploy_agent" not in state["agents_to_invoke"]:
        return {
            "deploy_findings": {"skipped": True, "reason": "not selected by commander"},
        }

    llm = get_llm()

    deployment_history = fetch_deployment_history(state["alert"])

    messages = [
        SystemMessage(content=DEPLOY_SYSTEM),
        HumanMessage(content=f"""
Alert: {json.dumps(state['alert'], indent=2)}
Investigation Plan: {state['investigation_plan']}

Deployment & Configuration History:
{json.dumps(deployment_history, indent=2)}

Analyze deployment timeline correlation with the incident and return structured findings.
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
        "deploy_findings": findings,
    }
