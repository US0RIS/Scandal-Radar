#!/usr/bin/env python3
"""Compare passive browser-control and extension proxy captures conservatively."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def requests(rows):
    return [r for r in rows if r.get("event") == "request"]


def hosts(rows):
    return Counter(str(r.get("host", "")).lower() for r in requests(rows) if r.get("host"))


def canary_events(rows):
    out = []
    for r in requests(rows):
        matches = set(r.get("url_canary_matches") or [])
        body = r.get("body") or {}
        matches.update(body.get("canary_matches") or [])
        # Header values are preserved except known secret-bearing headers.
        for value in (r.get("headers") or {}).values():
            for token in TOKENS:
                if token in str(value):
                    matches.add(token)
        if matches:
            out.append({
                "ts_unix": r.get("ts_unix"),
                "method": r.get("method"),
                "host": r.get("host"),
                "path": r.get("path"),
                "matches": sorted(matches),
                "body_length": body.get("length"),
                "body_sha256": body.get("sha256"),
            })
    return out


def main() -> int:
    global TOKENS
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--extension", type=Path, required=True)
    ap.add_argument("--tokens", required=True)
    ap.add_argument("--static", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    TOKENS = [x for x in args.tokens.split(",") if x]

    b = load(args.baseline)
    e = load(args.extension)
    hb, he = hosts(b), hosts(e)
    bce, ece = canary_events(b), canary_events(e)
    baseline_match_signatures = {(x["host"], tuple(x["matches"])) for x in bce}
    differential = [x for x in ece if (x["host"], tuple(x["matches"])) not in baseline_match_signatures]

    report = {
        "baseline_request_count": len(requests(b)),
        "extension_request_count": len(requests(e)),
        "baseline_hosts": dict(hb.most_common()),
        "extension_hosts": dict(he.most_common()),
        "hosts_only_seen_with_extension": sorted(set(he) - set(hb)),
        "baseline_canary_request_events": bce,
        "extension_canary_request_events": ece,
        "differential_canary_request_events": differential,
        "interpretation": (
            "A differential canary event is a lead, not proof of improper collection. "
            "Browser referrers, first-run flows, vendor endpoints, and feature necessity must be ruled out. "
            "Absence of a canary match does not prove absence of collection because certificate pinning, "
            "encryption above HTTP, alternate transports, or unlogged fields may prevent inspection."
        ),
    }
    if args.static and args.static.exists():
        s = json.loads(args.static.read_text())
        report["extension_version"] = s.get("version")
        report["crx_sha256"] = s.get("crx_sha256")
        report["manifest_permissions"] = s.get("permissions")
        report["host_permissions"] = s.get("host_permissions")
        report["content_scripts"] = s.get("content_scripts")
        report["literal_remote_hosts_top25"] = (s.get("remote_hosts_by_literal_url_frequency") or [])[:25]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "differential_canary_events": len(differential),
        "hosts_only_seen_with_extension": report["hosts_only_seen_with_extension"],
    }, indent=2))
    return 0


TOKENS: list[str] = []
if __name__ == "__main__":
    raise SystemExit(main())
