"""
Workflow Visualization
Renders the LangGraph workflow as a PNG and ASCII diagram.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.workflow import build_graph


def save_graph_png(output_path: str = "workflow_graph.png"):
    """Save the compiled graph as a PNG image."""
    app = build_graph()
    try:
        png_bytes = app.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        print(f"Graph saved to {output_path}")
    except Exception as e:
        print(f"PNG export requires graphviz/mermaid: {e}")
        print_ascii_graph()


def print_ascii_graph():
    """Print ASCII representation of the workflow."""
    diagram = """
╔══════════════════════════════════════════════════════════════════╗
║           AUTONOMOUS COMMANDER — INVESTIGATION WORKFLOW          ║
╚══════════════════════════════════════════════════════════════════╝

                    ┌─────────────────────┐
                    │   INCOMING ALERT    │
                    │  (Error / Anomaly)  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   COMMANDER AGENT   │
                    │   (Orchestrator)    │
                    │                     │
                    │ • Evaluate alert    │
                    │ • Classify severity │
                    │ • Build inv. plan   │
                    │ • Coordinate agents │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  LOGS AGENT  │  │METRICS AGENT │  │ DEPLOY AGENT │
   │   Forensic   │  │  Telemetry   │  │  Historian   │
   │   Expert     │  │  Analyst     │  │              │
   │              │  │              │  │              │
   │• Stack traces│  │• CPU spikes  │  │• CI/CD diff  │
   │• Error corr. │  │• Latency p99 │  │• Config chg  │
   │• Trace IDs   │  │• Memory leak │  │• Rollback?   │
   │• Log anomaly │  │• Error rates │  │• Culprit dep │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   SYNTHESIS NODE    │
                 │  (Commander RCA)    │
                 │                     │
                 │ • Root Cause        │
                 │ • Contributing Fctrs│
                 │ • Timeline          │
                 │ • Remediation Steps │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    FINAL REPORT     │
                 │   (RCA Document)    │
                 └─────────────────────┘
"""
    print(diagram)


if __name__ == "__main__":
    print_ascii_graph()
    save_graph_png("workflow_graph.png")
