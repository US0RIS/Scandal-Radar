"""mitmproxy addon for Scandal Radar experiments.

Usage:
    SCANDAL_RADAR_CANARIES='TOKEN1,TOKEN2' mitmdump -s lab/mitm_addon.py

The addon records traffic from an authorized test environment, redacts common
secret-bearing headers, and flags synthetic canary matches. It does not attempt
to defeat certificate pinning or other access controls.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Iterable

from mitmproxy import http

OUT = Path(os.environ.get("SCANDAL_RADAR_PROXY_LOG", "artifacts/proxy.jsonl"))
OUT.parent.mkdir(parents=True, exist_ok=True)
CANARIES = [x for x in os.environ.get("SCANDAL_RADAR_CANARIES", "").split(",") if x]
SECRET_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
}


def safe_headers(headers: http.Headers) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items(multi=True):
        lower = key.lower()
        result[key] = "<redacted>" if lower in SECRET_HEADERS else value[:2048]
    return result


def body_summary(content: bytes | None) -> dict[str, object]:
    if not content:
        return {"length": 0, "sha256": None, "canary_matches": []}
    sample = content[:1_000_000]
    text = sample.decode("utf-8", errors="ignore")
    matches = [token for token in CANARIES if token in text]
    return {
        "length": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "canary_matches": matches,
    }


def text_canary_matches(parts: Iterable[str]) -> list[str]:
    joined = "\n".join(parts)
    return [token for token in CANARIES if token in joined]


def write(event: dict[str, object]) -> None:
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


def request(flow: http.HTTPFlow) -> None:
    req = flow.request
    event = {
        "event": "request",
        "ts_unix": time.time(),
        "flow_id": flow.id,
        "method": req.method,
        "scheme": req.scheme,
        "host": req.pretty_host,
        "port": req.port,
        "path": req.path,
        "url_canary_matches": text_canary_matches([req.pretty_url]),
        "headers": safe_headers(req.headers),
        "body": body_summary(req.raw_content),
    }
    write(event)


def response(flow: http.HTTPFlow) -> None:
    if flow.response is None:
        return
    resp = flow.response
    event = {
        "event": "response",
        "ts_unix": time.time(),
        "flow_id": flow.id,
        "status_code": resp.status_code,
        "headers": safe_headers(resp.headers),
        "body": body_summary(resp.raw_content),
    }
    write(event)
