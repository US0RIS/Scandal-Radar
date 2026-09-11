#!/usr/bin/env python3
"""Exercise Hola's real extension popup against a synthetic browsing URL.

This probe opens the extension's actual browser-action popup with chrome.action.openPopup,
records visible UI, and attempts only user-facing controls. It never calls Hola's
telemetry sender directly. Any perr.hola.org traffic is observed through Playwright.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import secrets
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

EXPECTED_ID = "gkojfkhlekighikafcpjkiklfbnlmeio"
PERR_HOST = "perr.hola.org"


async def get_worker(context):
    workers = list(context.service_workers)
    if not workers:
        try:
            workers.append(await context.wait_for_event("serviceworker", timeout=20000))
        except Exception:
            pass
    return next((w for w in workers if f"chrome-extension://{EXPECTED_ID}/" in w.url), None)


async def wait_active(worker, marker, timeout=15):
    for _ in range(int(timeout * 4)):
        try:
            u = await worker.evaluate("() => self.be_bg_main?.be_tabs?.get('active.url')")
            if u and marker in u:
                return u
        except Exception:
            pass
        await asyncio.sleep(.25)
    return None


async def open_popup(context, worker):
    old = set(context.pages)
    result = await worker.evaluate("""async () => {
        try { await chrome.action.openPopup(); return {ok:true}; }
        catch (e) { return {ok:false, error:String(e)}; }
    }""")
    await asyncio.sleep(1)
    candidates = [p for p in context.pages if p not in old and f"chrome-extension://{EXPECTED_ID}/" in p.url]
    if not candidates:
        candidates = [p for p in context.pages if f"chrome-extension://{EXPECTED_ID}/js/popup.html" in p.url]
    return result, candidates[-1] if candidates else None


async def click_first_text(page, patterns):
    for pat in patterns:
        try:
            loc = page.get_by_text(re.compile(pat, re.I)).first
            if await loc.count() and await loc.is_visible():
                text = (await loc.inner_text()).strip()
                await loc.click(timeout=3000)
                return text
        except Exception:
            pass
    return None


async def one_run(browser_type, ext_dir: Path, n: int, out_dir: Path):
    marker = f"SCANDAL_RADAR_HOLA_UI_{n}_{secrets.token_hex(12).upper()}"
    target_url = f"https://example.com/?sr_ui_marker={marker}"
    requests = []
    profile = f"/tmp/scandal-radar-hola-ui-{n}-{secrets.token_hex(4)}"
    context = await browser_type.launch_persistent_context(
        profile,
        headless=False,
        args=[f"--disable-extensions-except={ext_dir}", f"--load-extension={ext_dir}", "--no-first-run", "--disable-sync"],
    )
    try:
        context.on("request", lambda req: requests.append({
            "url": req.url, "method": req.method, "post_data": req.post_data, "resource_type": req.resource_type
        }) if urlparse(req.url).hostname == PERR_HOST else None)

        worker = await get_worker(context)
        if not worker:
            raise RuntimeError("official Hola service worker not found")
        identity = await worker.evaluate("() => ({id:chrome.runtime.id, version:chrome.runtime.getManifest().version})")
        if identity["id"] != EXPECTED_ID:
            raise RuntimeError(f"wrong extension id: {identity}")

        # Let first-install pages settle, then create and force our synthetic page active.
        await asyncio.sleep(2)
        target = await context.new_page()
        await target.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        await target.bring_to_front()
        if not await wait_active(worker, marker):
            raise RuntimeError("synthetic target did not become Hola active.url")

        before = len(requests)
        popup_result, popup = await open_popup(context, worker)
        if not popup:
            return {"ok": False, "run": n, "identity": identity, "popup_open_result": popup_result,
                    "page_urls": [p.url for p in context.pages]}

        await popup.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        initial_text = (await popup.locator("body").inner_text())[:12000]
        initial_html = (await popup.locator("body").inner_html())[:30000]
        try:
            await popup.screenshot(path=str(out_dir / f"run-{n}-popup-initial.png"))
        except Exception:
            pass

        actions = []
        # If a country chooser is present, choose the US through the visible UI. Use
        # exact-ish visible labels and stop if no suitable control is present.
        country_clicked = await click_first_text(popup, [r"^United States$", r"^US$"])
        if country_clicked:
            actions.append({"action": "click_country", "text": country_clicked})
            await asyncio.sleep(8)

        # Popup may close/reopen after changing country. Reassert target and reopen it.
        await target.bring_to_front()
        await wait_active(worker, marker, timeout=10)
        popup_result2, popup2 = await open_popup(context, worker)
        if popup2:
            popup = popup2
            await asyncio.sleep(2)
        later_text = (await popup.locator("body").inner_text())[:12000]
        try:
            await popup.screenshot(path=str(out_dir / f"run-{n}-popup-after-country.png"))
        except Exception:
            pass

        # Prefer the documented negative diagnostic action. Fall back to the affirmative
        # working control if that is what the current UI exposes.
        clicked = await click_first_text(popup, [r"^No,?\s*fix it$", r"^No$", r"^Yes$"])
        if clicked:
            actions.append({"action": "click_working_prompt", "text": clicked})
            await asyncio.sleep(6)

        after_requests = requests[before:]
        marker_requests = [r for r in after_requests if marker in json.dumps(r, sort_keys=True)]
        event_ids = []
        for r in after_requests:
            m = re.search(r"[?&]id=([^&]+)", r["url"])
            if m:
                event_ids.append(m.group(1))

        return {
            "ok": True,
            "run": n,
            "marker": marker,
            "target_url": target_url,
            "identity": identity,
            "popup_open_result": popup_result,
            "initial_popup_text": initial_text,
            "later_popup_text": later_text,
            "actions": actions,
            "perr_requests_after_popup_open": after_requests,
            "perr_event_ids": event_ids,
            "marker_requests": marker_requests,
            "marker_transmitted": bool(marker_requests),
            "clicked_working_prompt": any(a["action"] == "click_working_prompt" for a in actions),
        }
    finally:
        await context.close()


async def run(args):
    args.out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        results=[]
        for n in range(1, args.repetitions+1):
            try:
                results.append(await one_run(p.chromium, args.extension_dir.resolve(), n, args.out_dir))
            except Exception as e:
                results.append({"ok":False,"run":n,"error":repr(e)})
        report={
            "probe":"hola-real-popup-ui",
            "repetitions":args.repetitions,
            "results":results,
            "all_runs_ok":all(r.get("ok") for r in results),
            "natural_ui_marker_transmissions":sum(bool(r.get("marker_transmitted")) for r in results),
            "working_prompt_clicks":sum(bool(r.get("clicked_working_prompt")) for r in results),
        }
        (args.out_dir/"ui-probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--extension-dir",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--repetitions",type=int,default=2)
    args=ap.parse_args()
    return asyncio.run(run(args))


if __name__=="__main__":
    raise SystemExit(main())
