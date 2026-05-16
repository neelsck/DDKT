#!/usr/bin/env python3
"""Local HTTP UI for asking questions about Maria's Bakery contract FSMs."""
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from contracts.marias_bakery_reasoner import contract_summaries, rank_scenarios


ROOT = Path(__file__).resolve().parent
UI_PATH = ROOT / "marias_bakery_ui.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "MariasBakeryFSM/0.1"

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, content_type: str = "text/html; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_text(UI_PATH.read_text())
            return
        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if parsed.path == "/api/contracts":
            self._send_json({"contracts": contract_summaries()})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            question = str(payload.get("question") or "").strip()
            if not question:
                raise ValueError("question is required")
            self._send_json(rank_scenarios(question))
        except Exception as exc:  # pragma: no cover - visible in UI/API
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Maria's Bakery FSM UI: http://{args.host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
