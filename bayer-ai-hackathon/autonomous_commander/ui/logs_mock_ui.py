"""
Minimal UI to edit logs mock data.
Run: python ui/logs_mock_ui.py
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MOCK_PATH = Path(os.getenv("MOCK_LOGS_FILE", ROOT / "mock_inputs" / "logs_mock.json"))

DEFAULT_DATA = {
    "log_groups": ["/aws/lambda/payment-service", "/aws/ecs/order-service"],
    "sample_errors": [
        "ERROR 2026-03-25T10:23:11Z [payment-service] NullPointerException at PaymentProcessor.java:142",
        "ERROR 2026-03-25T10:23:12Z [order-service] Connection timeout to payment-service after 30000ms",
        "FATAL 2026-03-25T10:23:15Z [api-gateway] Circuit breaker OPEN for payment-service",
    ],
    "trace_ids": ["1-abc123", "1-abc124"],
    "time_range": "last 30 minutes",
}


def _load_data() -> dict:
    if MOCK_PATH.exists():
        try:
            return json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_DATA
    return DEFAULT_DATA


def _save_data(data: dict) -> None:
    MOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    MOCK_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Autonomous Commander — Logs Mock Editor</title>
    <style>
      :root {{
        --bg: #0f141a;
        --bg2: #151b22;
        --panel: #1c2430;
        --text: #e7eef8;
        --muted: #9ab0c7;
        --accent: #3ed2a4;
        --accent2: #62a0ff;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Space Grotesk", "IBM Plex Sans", "Segoe UI", sans-serif;
        color: var(--text);
        background:
          radial-gradient(1200px 600px at 10% -10%, rgba(62, 210, 164, 0.18), transparent),
          radial-gradient(900px 500px at 110% 10%, rgba(98, 160, 255, 0.2), transparent),
          linear-gradient(180deg, var(--bg), var(--bg2));
        min-height: 100vh;
        padding: 32px;
      }}
      .wrap {{
        max-width: 980px;
        margin: 0 auto;
      }}
      .header {{
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 20px;
      }}
      .title {{
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 0.3px;
      }}
      .subtitle {{
        color: var(--muted);
        font-size: 14px;
      }}
      .panel {{
        background: var(--panel);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
      }}
      textarea {{
        width: 100%;
        min-height: 420px;
        background: #0f1319;
        color: #dfe9f6;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px;
        font-family: "JetBrains Mono", "SFMono-Regular", ui-monospace, monospace;
        font-size: 13px;
        line-height: 1.5;
        resize: vertical;
      }}
      .actions {{
        margin-top: 12px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }}
      button {{
        background: linear-gradient(90deg, var(--accent), var(--accent2));
        border: none;
        color: #0b1016;
        font-weight: 700;
        padding: 10px 16px;
        border-radius: 10px;
        cursor: pointer;
      }}
      .ghost {{
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: var(--text);
      }}
      .status {{
        margin-top: 10px;
        color: var(--muted);
        font-size: 13px;
      }}
      .pill {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(62, 210, 164, 0.15);
        color: var(--accent);
        font-size: 12px;
      }}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="header">
        <div>
          <div class="title">Logs Mock Editor</div>
          <div class="subtitle">Edit CloudWatch log mock payloads used by the Logs Agent</div>
        </div>
        <span class="pill">Local Only</span>
      </div>
      <div class="panel">
        <textarea id="mock"></textarea>
        <div class="actions">
          <button id="save">Save Mock</button>
          <button id="reload" class="ghost">Reload</button>
        </div>
        <div class="status" id="status"></div>
      </div>
    </div>
    <script>
      const statusEl = document.getElementById("status");
      const textarea = document.getElementById("mock");

      function setStatus(msg) {{
        statusEl.textContent = msg;
      }}

      async function load() {{
        const res = await fetch("/api/logs");
        const data = await res.json();
        textarea.value = JSON.stringify(data, null, 2);
        setStatus("Loaded mock from disk.");
      }}

      async function save() {{
        let payload;
        try {{
          payload = JSON.parse(textarea.value);
        }} catch (e) {{
          setStatus("Invalid JSON. Fix errors before saving.");
          return;
        }}
        const res = await fetch("/api/logs", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(payload)
        }});
        const data = await res.json();
        setStatus(data.message || "Saved.");
      }}

      document.getElementById("save").addEventListener("click", save);
      document.getElementById("reload").addEventListener("click", load);

      load();
    </script>
  </body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: str, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/logs":
            data = _load_data()
            body = json.dumps(data)
            self._send(200, body, "application/json")
            return

        self._send(200, HTML_TEMPLATE, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/logs":
            self._send(404, "Not Found", "text/plain")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
            _save_data(data)
            body = json.dumps({"status": "ok", "message": f"Saved to {MOCK_PATH}"})
            self._send(200, body, "application/json")
        except json.JSONDecodeError:
            body = json.dumps({"status": "error", "message": "Invalid JSON payload."})
            self._send(400, body, "application/json")


def main() -> None:
    host = "127.0.0.1"
    port = int(os.getenv("MOCK_UI_PORT", "5055"))
    server = HTTPServer((host, port), Handler)
    print(f"Mock UI running at http://{host}:{port}")
    print(f"Editing: {MOCK_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
