#!/usr/bin/env python3
"""Execute a controlled Hola telemetry transport probe in a fresh Chromium profile.

The probe uses only synthetic URLs. It first observes the exact extension while idle on
an example.com canary URL, then invokes the production `send_vpn_work_report` function
inside the extension service worker and records XMLHttpRequest construction plus any
browser-observed request to perr.hola.org.

The internal invocation validates the production transport path but is NOT represented
as a natural-user behavioral reproduction. A passive capture is recorded separately.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright

EXPECTED_ID = "gkojfkhlekighikafcpjkiklfbnlmeio"
PERR_HOST = "perr.hola.org"


async def wait_active_url(worker, marker: str, timeout_s: float = 15.0) -> str | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            value = await worker.evaluate(
                """() => self.be_bg_main && self.be_bg_main.be_tabs &&
                self.be_bg_main.be_tabs.get('active.url')"""
            )
            if value and marker in value:
                return value
        except Exception:
            pass
        await asyncio.sleep(0.25)
    return None


async def one_run(browser_type, extension_dir: Path, run_no: int, headed: bool) -> dict:
    marker = f"SCANDAL_RADAR_HOLA_{run_no}_{secrets.token_hex(12).upper()}"
    target = f"https://example.com/?sr_marker={marker}"
    profile = Path(f"/tmp/scandal-radar-hola-{run_no}-{secrets.token_hex(4)}")
    browser_requests: list[dict] = []

    args = [
        f"--disable-extensions-except={extension_dir}",
        f"--load-extension={extension_dir}",
        "--no-first-run",
        "--disable-sync",
    ]
    context = await browser_type.launch_persistent_context(
        str(profile),
        headless=not headed,
        args=args,
    )
    try:
        def on_request(req):
            try:
                if urlparse(req.url).hostname == PERR_HOST:
                    browser_requests.append({
                        "url": req.url,
                        "method": req.method,
                        "post_data": req.post_data,
                        "resource_type": req.resource_type,
                    })
            except Exception:
                pass

        context.on("request", on_request)
        workers = list(context.service_workers)
        if not workers:
            try:
                workers.append(await context.wait_for_event("serviceworker", timeout=20000))
            except Exception:
                pass
        if not workers:
            raise RuntimeError("Hola extension service worker did not start")

        worker = next((w for w in workers if f"chrome-extension://{EXPECTED_ID}/" in w.url), None)
        if worker is None:
            raise RuntimeError(f"Expected Hola service worker ID not found: {[w.url for w in workers]}")

        identity = await worker.evaluate(
            """() => ({
                runtime_id: chrome.runtime.id,
                version: chrome.runtime.getManifest().version,
                has_bg_main: !!self.be_bg_main,
                has_rule: !!(self.be_bg_main && self.be_bg_main.be_rule),
                has_sender: !!(self.be_bg_main && self.be_bg_main.be_rule &&
                    self.be_bg_main.be_rule.send_vpn_work_report)
            })"""
        )
        if identity.get("runtime_id") != EXPECTED_ID:
            raise RuntimeError(f"Unexpected runtime ID: {identity}")
        if not identity.get("has_sender"):
            raise RuntimeError(f"Production sender unavailable: {identity}")

        # Instrument the exact production XMLHttpRequest constructor. We do not replace
        # or suppress the request; this is a spy on method/URL/body arguments.
        await worker.evaluate(
            """() => {
                self.__scandal_radar_xhrs = [];
                const p = XMLHttpRequest.prototype;
                if (!p.__scandal_radar_patched) {
                    const originalOpen = p.open;
                    const originalSend = p.send;
                    p.open = function(method, url, ...rest) {
                        this.__scandal_radar_meta = {method: String(method), url: String(url)};
                        return originalOpen.call(this, method, url, ...rest);
                    };
                    p.send = function(body) {
                        const m = this.__scandal_radar_meta || {};
                        if (String(m.url || '').includes('perr.hola.org')) {
                            self.__scandal_radar_xhrs.push({
                                method: m.method || null,
                                url: m.url || null,
                                body: body == null ? null : String(body),
                                ts: Date.now()
                            });
                        }
                        return originalSend.call(this, body);
                    };
                    p.__scandal_radar_patched = true;
                }
            }"""
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(target, wait_until="domcontentloaded", timeout=30000)
        active_url = await wait_active_url(worker, marker)
        if not active_url:
            raise RuntimeError("Hola did not expose the synthetic active URL in its tab state")

        # Passive observation window: extension present, no feature invocation.
        await asyncio.sleep(8)
        passive_xhrs = await worker.evaluate("() => self.__scandal_radar_xhrs.slice()")
        passive_browser = list(browser_requests)

        # Controlled internal invocation of the exact production function. This proves
        # request assembly/transport, not the frequency of natural user triggering.
        invoke_started = time.time()
        await worker.evaluate(
            """() => self.be_bg_main.be_rule.send_vpn_work_report({
                rule: {country: 'US', name: 'example.com', type: 'site'},
                src: 'scandal-radar-controlled'
            })"""
        )
        await asyncio.sleep(5)
        all_xhrs = await worker.evaluate("() => self.__scandal_radar_xhrs.slice()")

        invoked_xhrs = all_xhrs[len(passive_xhrs):]
        invoked_browser = browser_requests[len(passive_browser):]
        canary_in_xhr = any(marker in json.dumps(x, sort_keys=True) for x in invoked_xhrs)
        canary_in_browser_request = any(marker in json.dumps(x, sort_keys=True) for x in invoked_browser)
        passive_canary = any(marker in json.dumps(x, sort_keys=True) for x in passive_xhrs + passive_browser)

        # Parse form body for compact evidence without relying on log formatting.
        parsed_events = []
        for item in invoked_xhrs:
            body = item.get("body") or ""
            parsed = parse_qs(body, keep_blank_values=True)
            info = parsed.get("info", [None])[0]
            parsed_events.append({
                "url": item.get("url"),
                "method": item.get("method"),
                "info": info,
                "contains_marker": marker in (info or ""),
            })

        return {
            "ok": True,
            "run": run_no,
            "marker": marker,
            "target_url": target,
            "active_url_observed_by_extension": active_url,
            "identity": identity,
            "passive_window_seconds": 8,
            "passive_perr_xhrs": passive_xhrs,
            "passive_browser_requests": passive_browser,
            "passive_canary_observed": passive_canary,
            "controlled_invocation_unix": invoke_started,
            "invoked_perr_xhrs": invoked_xhrs,
            "invoked_browser_requests": invoked_browser,
            "parsed_invoked_events": parsed_events,
            "canary_in_instrumented_xhr": canary_in_xhr,
            "canary_in_browser_request": canary_in_browser_request,
        }
    finally:
        await context.close()


async def run(args) -> int:
    async with async_playwright() as p:
        results = []
        for n in range(1, args.repetitions + 1):
            try:
                results.append(await one_run(p.chromium, args.extension_dir.resolve(), n, args.headed))
            except Exception as exc:
                results.append({"ok": False, "run": n, "error": repr(exc)})
        report = {
            "probe": "hola-controlled-transport",
            "expected_extension_id": EXPECTED_ID,
            "repetitions": args.repetitions,
            "headed": args.headed,
            "results": results,
            "all_runs_ok": all(r.get("ok") for r in results),
            "all_invoked_canaries_captured": all(
                r.get("ok") and r.get("canary_in_instrumented_xhr") for r in results
            ),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["all_runs_ok"] and report["all_invoked_canaries_captured"] else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extension-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--repetitions", type=int, default=2)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
