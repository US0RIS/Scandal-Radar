#!/usr/bin/env python3
"""Execute a controlled Hola telemetry transport probe in a fresh Chromium profile.

The probe uses only synthetic URLs. It first observes the exact extension while idle on
an example.com canary URL, then invokes the production `send_vpn_work_report` function
inside the extension service worker and records the MV3 fetch construction plus any
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
from urllib.parse import urlparse

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
                    self.be_bg_main.be_rule.send_vpn_work_report),
                has_fetch: typeof self.fetch === 'function'
            })"""
        )
        if identity.get("runtime_id") != EXPECTED_ID:
            raise RuntimeError(f"Unexpected runtime ID: {identity}")
        if not identity.get("has_sender") or not identity.get("has_fetch"):
            raise RuntimeError(f"Production sender/fetch unavailable: {identity}")

        await worker.evaluate(
            """() => {
                self.__scandal_radar_fetches = [];
                if (!self.__scandal_radar_original_fetch) {
                    self.__scandal_radar_original_fetch = self.fetch.bind(self);
                    self.fetch = function(input, init) {
                        let url = '';
                        try { url = typeof input === 'string' ? input : String(input.url || input); }
                        catch (e) { url = String(input); }
                        if (url.includes('perr.hola.org')) {
                            self.__scandal_radar_fetches.push({
                                url,
                                method: init && init.method ? String(init.method) : 'GET',
                                body: init && init.body != null ? String(init.body) : null,
                                ts: Date.now()
                            });
                        }
                        return self.__scandal_radar_original_fetch(input, init);
                    };
                }
            }"""
        )

        # Always create a dedicated target tab. Hola may open a first-install welcome
        # page asynchronously; using context.pages[0] allowed that tab to steal focus in
        # an earlier run and made the report contain Hola's own welcome URL.
        page = await context.new_page()
        await page.goto(target, wait_until="domcontentloaded", timeout=30000)
        await page.bring_to_front()
        active_url = await wait_active_url(worker, marker)
        if not active_url:
            raise RuntimeError("Hola did not expose the synthetic active URL in its tab state")

        # Passive observation window: extension present, no feature invocation.
        await asyncio.sleep(8)
        passive_fetches = await worker.evaluate("() => self.__scandal_radar_fetches.slice()")
        passive_browser = list(browser_requests)

        # Reassert target focus immediately before the controlled invocation. This
        # removes the first-install welcome-tab race from the URL-bearing test.
        await page.bring_to_front()
        active_url_before_invocation = await wait_active_url(worker, marker, timeout_s=10.0)
        if not active_url_before_invocation:
            raise RuntimeError("Synthetic target was not active immediately before invocation")

        invoke_started = time.time()
        await worker.evaluate(
            """() => self.be_bg_main.be_rule.send_vpn_work_report({
                rule: {country: 'US', name: 'example.com', type: 'site'},
                src: 'scandal-radar-controlled'
            })"""
        )
        await asyncio.sleep(5)
        all_fetches = await worker.evaluate("() => self.__scandal_radar_fetches.slice()")

        invoked_fetches = all_fetches[len(passive_fetches):]
        invoked_browser = browser_requests[len(passive_browser):]
        canary_in_fetch = any(marker in json.dumps(x, sort_keys=True) for x in invoked_fetches)
        canary_in_browser_request = any(marker in json.dumps(x, sort_keys=True) for x in invoked_browser)
        passive_canary = any(marker in json.dumps(x, sort_keys=True) for x in passive_fetches + passive_browser)

        parsed_events = []
        for item in invoked_fetches:
            raw_body = item.get("body") or ""
            try:
                body = json.loads(raw_body)
            except Exception:
                body = None
            raw_info = body.get("info") if isinstance(body, dict) else None
            try:
                info = json.loads(raw_info) if isinstance(raw_info, str) else raw_info
            except Exception:
                info = raw_info
            parsed_events.append({
                "url": item.get("url"),
                "method": item.get("method"),
                "body": body,
                "info": info,
                "contains_marker": marker in json.dumps(info, sort_keys=True) if info is not None else False,
            })

        return {
            "ok": True,
            "run": run_no,
            "marker": marker,
            "target_url": target,
            "active_url_observed_by_extension": active_url,
            "active_url_before_invocation": active_url_before_invocation,
            "identity": identity,
            "passive_window_seconds": 8,
            "passive_perr_fetches": passive_fetches,
            "passive_browser_requests": passive_browser,
            "passive_canary_observed": passive_canary,
            "controlled_invocation_unix": invoke_started,
            "invoked_perr_fetches": invoked_fetches,
            "invoked_browser_requests": invoked_browser,
            "parsed_invoked_events": parsed_events,
            "canary_in_instrumented_fetch": canary_in_fetch,
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
                r.get("ok") and r.get("canary_in_instrumented_fetch") for r in results
            ),
            "all_invoked_browser_requests_captured": all(
                r.get("ok") and r.get("canary_in_browser_request") for r in results
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
