"""
Autonomous Commander — Entry Point
Run a full multi-agent investigation from the command line.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import run_investigation
from graph.visualize import print_ascii_graph


SAMPLE_ALERT = {
    "alert_id": "ALT-20260325-001",
    "service": "payment-service",
    "environment": "production",
    "error_type": "HighErrorRate",
    "error_message": "NullPointerException in PaymentProcessor — circuit breaker OPEN",
    "severity_hint": "P1",
    "timestamp": "2026-03-25T10:23:00Z",
    "time_range": "last 30 minutes",
    "affected_endpoints": ["/api/v1/payments", "/api/v1/checkout"],
    "error_rate_percent": 22.1,
    "source": "CloudWatch Alarm",
}


def main():
    print("\n" + "="*65)
    print("  AUTONOMOUS COMMANDER — MULTI-AGENT INCIDENT INVESTIGATION")
    print("="*65)

    print_ascii_graph()

    print("\n[Commander] Received alert:")
    print(json.dumps(SAMPLE_ALERT, indent=2))
    print("\n[Commander] Starting autonomous investigation...\n")

    result = run_investigation(SAMPLE_ALERT)

    print("\n" + "="*65)
    print("  FINAL ROOT CAUSE ANALYSIS REPORT")
    print("="*65)
    print(result["final_report"])

    print("\n[Logs Findings]")
    print(json.dumps(result.get("logs_findings", {}), indent=2))

    print("\n[Metrics Findings]")
    print(json.dumps(result.get("metrics_findings", {}), indent=2))

    print("\n[Deploy Findings]")
    print(json.dumps(result.get("deploy_findings", {}), indent=2))


if __name__ == "__main__":
    main()
