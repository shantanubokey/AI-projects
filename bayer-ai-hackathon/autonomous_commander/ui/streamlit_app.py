"""
Streamlit UI for Autonomous Commander.
Run: streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from graph.workflow import run_investigation
from agents.commander_agent import commander_node, InvestigationState


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_logs_override(raw: str, time_range: str) -> dict | None:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    return {
        "log_groups": ["ui-input"],
        "sample_errors": lines,
        "trace_ids": [],
        "time_range": time_range,
    }


st.set_page_config(page_title="Autonomous Commander", layout="wide")
st.title("Autonomous Commander — Demo UI")
st.caption("Provide logs, run the commander, and view the RCA artifact.")

with st.sidebar:
    st.subheader("Bedrock Config")
    model_id = st.text_input("BEDROCK_MODEL_ID", os.getenv("BEDROCK_MODEL_ID", ""))
    region = st.text_input("BEDROCK_REGION", os.getenv("BEDROCK_REGION", "us-east-1"))
    provider = st.text_input("BEDROCK_PROVIDER (optional)", os.getenv("BEDROCK_PROVIDER", ""))

    if model_id:
        os.environ["BEDROCK_MODEL_ID"] = model_id
    if region:
        os.environ["BEDROCK_REGION"] = region
    if provider:
        os.environ["BEDROCK_PROVIDER"] = provider

    st.subheader("Mock Selection")
    mock_variant = st.selectbox("MOCK_VARIANT", ["default", "alt", "random"])
    os.environ["MOCK_VARIANT"] = mock_variant

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.subheader("Input Logs")
    logs_text = st.text_area(
        "Paste logs (one line per entry)",
        height=320,
        placeholder="ERROR 2026-03-25T10:23:11Z [payment-service] NullPointerException at PaymentProcessor.java:142",
    )

with col2:
    st.subheader("Alert Context")
    service = st.text_input("Service", "payment-service")
    environment = st.text_input("Environment", "production")
    error_type = st.selectbox(
        "Error Type",
        ["LogError", "MetricError", "DeployError", "Unknown"],
        index=0,
    )
    error_message = st.text_input(
        "Error Message",
        "NullPointerException in PaymentProcessor — circuit breaker OPEN",
    )
    severity_hint = st.selectbox("Severity Hint", ["P1", "P2", "P3"], index=0)
    time_range = st.text_input("Time Range", "last 30 minutes")

st.divider()

if st.button("Run Investigation", type="primary"):
    alert = {
        "alert_id": f"ALT-{datetime.now().strftime('%Y%m%d')}-UI",
        "service": service,
        "environment": environment,
        "error_type": error_type,
        "error_message": error_message,
        "severity_hint": severity_hint,
        "timestamp": _now_iso(),
        "time_range": time_range,
        "affected_endpoints": [],
        "error_rate_percent": 0.0,
        "source": "Streamlit UI",
    }

    logs_override = _build_logs_override(logs_text, time_range)

    status = st.status("Commander analyzing alert...", state="running", expanded=True)
    try:
        pre_state: InvestigationState = {
            "messages": [],
            "alert": alert,
            "investigation_plan": [],
            "agents_to_invoke": [],
            "logs_findings": {},
            "metrics_findings": {},
            "deploy_findings": {},
            "final_report": "",
            "current_step": "start",
        }
        commander_state = commander_node(pre_state)
        status.write("Selected agents:")
        status.write(", ".join(commander_state.get("agents_to_invoke", [])) or "None")
        status.write("Investigation plan:")
        status.write(commander_state.get("investigation_plan", []))
        status.update(label="Running selected agents...", state="running")

        result = run_investigation(
            alert,
            logs_override=logs_override,
            precomputed_plan=commander_state.get("investigation_plan", []),
            precomputed_agents=commander_state.get("agents_to_invoke", []),
        )
    except Exception as exc:
        status.update(label="Investigation failed", state="error")
        st.error(f"Investigation failed: {exc}")
    else:
        status.update(label="Investigation complete", state="complete")

        st.subheader("Final RCA Artifact")
        st.write(result.get("final_report", ""))

        st.subheader("Commander Plan")
        st.json(
            {
                "investigation_plan": result.get("investigation_plan", []),
                "agents_to_invoke": result.get("agents_to_invoke", []),
            }
        )

        st.subheader("Logs Findings")
        st.json(result.get("logs_findings", {}))

        st.subheader("Metrics Findings")
        st.json(result.get("metrics_findings", {}))

        st.subheader("Deploy Findings")
        st.json(result.get("deploy_findings", {}))

        st.subheader("Raw Alert")
        st.json(alert)
