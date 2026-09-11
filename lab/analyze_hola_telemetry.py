#!/usr/bin/env python3
"""Assert key Hola URL-telemetry paths in an unpacked extension.

This does not execute the extension. It records narrow static observations so package
updates can be compared reproducibly without relying on hand inspection of minified JS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

CHECKS = {
    "config_perr_endpoint": (
        "js/bg.conf.bundle.js",
        r'"url_perr":"https://perr\.hola\.org/client_cgi"',
    ),
    "no_log_defaults_include_be_vpn_ok": (
        "js/bg.bg.bundle.js",
        r'no_log_perrs:\[[^\]]*"be_vpn_ok"',
    ),
    "no_log_allowed_lookup": (
        "js/bg.bg.bundle.js",
        r'allowed_perrs=.*?bool_lookup\(conf\.no_log_perrs\|\|\[\]\)',
    ),
    "no_log_gate_exempts_allowed_event_ids": (
        "js/bg.bg.bundle.js",
        r'E\.enabled=perr_id=>enabled&&!\(perr_id&&allowed_perrs\[perr_id\]\)',
    ),
    "vpn_work_report_event": (
        "js/bg.bg.bundle.js",
        r'E\.send_vpn_work_report=function\(opt\).*?perr\("be_vpn_ok"',
    ),
    "vpn_work_report_active_full_url": (
        "js/bg.bg.bundle.js",
        r'E\.send_vpn_work_report=function\(opt\).*?url:.*?get\("active\.url"\)',
    ),
    "fix_report_active_full_url": (
        "js/bg.bg.bundle.js",
        r'function get_report\(opt\).*?let url=opt\.url\|\|.*?get\("active\.url"\).*?real_url:.*?get\("active\.url"\)',
    ),
    "working_ui_calls_vpn_report": (
        "js/507.bundle.js",
        r'E\.click_working=.*?E\.send_vpn_work_report\(\{rule,src\}\)',
    ),
    "not_working_ui_calls_fix_report": (
        "js/507.bundle.js",
        r'E\.click_not_working=.*?E\.send_fix_it_report',
    ),
    "mv3_perr_send_serializes_info": (
        "js/bg.bg.bundle.js",
        r'function perr_send\(id,info,opt\).*?data\.info=info;qs\.id=id;opt=\{url:conf\.url_perr\+"/perr",qs,data,method:"POST",json:1\}',
    ),
    "mv3_ajax_uses_fetch": (
        "js/bg.bg.bundle.js",
        r'function do_fetch\(opt\).*?fetch\(url,\{method,body,signal:controller\.signal,headers',
    ),
    "tpopup_event_has_full_url": (
        "js/507.bundle.js",
        r'be_tpopup_open"\s*,\s*\{root_url,url\}',
    ),
    "render_stats_called_after_init": (
        "js/458.bundle.js",
        r'useEffect\)\(\(\)=>\{if\(!inited\)return;.*?send_render_stats\(\)',
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extension_dir", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    root = args.extension_dir

    manifest = json.loads((root / "manifest.json").read_text())
    results = {}
    for name, (rel, pattern) in CHECKS.items():
        path = root / rel
        text = path.read_text(errors="replace") if path.exists() else ""
        match = re.search(pattern, text, re.S)
        results[name] = {
            "matched": bool(match),
            "file": rel,
            "offset": match.start() if match else None,
        }

    report = {
        "version": manifest.get("version"),
        "manifest_version": manifest.get("manifest_version"),
        "extension_id_expected": "gkojfkhlekighikafcpjkiklfbnlmeio",
        "host_permissions": manifest.get("host_permissions"),
        "permissions": manifest.get("permissions"),
        "checks": results,
        "all_required_matched": all(v["matched"] for v in results.values()),
        "files_sha256": {
            rel: sha256(root / rel)
            for rel in sorted({entry[0] for entry in CHECKS.values()})
            if (root / rel).exists()
        },
    }
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(output)
    print(output, end="")
    return 0 if report["all_required_matched"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
