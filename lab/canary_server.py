#!/usr/bin/env python3
"""Serve a synthetic page for extension/network experiments.

The page intentionally contains unique markers in multiple contexts so a researcher
can determine whether page URLs, visible text, or form content leave the browser.
Use only in an authorized test environment.
"""

from __future__ import annotations

import argparse
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def marker(prefix: str) -> str:
    return f"SCANDAL_RADAR_{prefix}_{secrets.token_hex(6).upper()}"


class Handler(BaseHTTPRequestHandler):
    server_version = "ScandalRadarCanary/0.1"

    def _log(self) -> None:
        parsed = urlparse(self.path)
        event = {
            "ts_unix": time.time(),
            "method": self.command,
            "path": parsed.path,
            "query": parse_qs(parsed.query, keep_blank_values=True),
            "client": self.client_address[0],
            "user_agent": self.headers.get("User-Agent"),
            "referer": self.headers.get("Referer"),
        }
        with self.server.log_path.open("a", encoding="utf-8") as fh:  # type: ignore[attr-defined]
            fh.write(json.dumps(event, sort_keys=True) + "\n")

    def do_GET(self) -> None:  # noqa: N802
        self._log()
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        tokens = self.server.tokens  # type: ignore[attr-defined]
        html = f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>{tokens['title']}</title>
</head>
<body>
  <h1>Scandal Radar synthetic test page</h1>
  <p id=\"body-canary\">{tokens['body']}</p>
  <p>This page contains synthetic data only. Nothing here is a real secret.</p>
  <label>Synthetic form value
    <input id=\"form-canary\" value=\"{tokens['form']}\">
  </label>
  <p><a id=\"query-canary\" href=\"/?radar={tokens['query']}\">Canary query link</a></p>
  <pre>{json.dumps(tokens, indent=2)}</pre>
</body>
</html>
""".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep terminal output concise; the complete request record goes to JSONL.
        print(f"{self.address_string()} - {fmt % args}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log", type=Path, default=Path("artifacts/canary_server.jsonl"))
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    tokens = {
        "title": marker("TITLE"),
        "body": marker("BODY"),
        "form": marker("FORM"),
        "query": marker("QUERY"),
    }

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.tokens = tokens  # type: ignore[attr-defined]
    server.log_path = args.log  # type: ignore[attr-defined]

    print(json.dumps({"url": f"http://{args.host}:{args.port}/", "tokens": tokens}, indent=2))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
