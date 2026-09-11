#!/usr/bin/env python3
"""Exercise Hola's actual browser-action popup through Chrome DevTools Protocol.

The target website remains the browser's active tab. The popup is opened with
chrome.action.openPopup(), attached as its own DevTools target, and visible controls
are clicked in the popup DOM. No Hola telemetry function is called directly.
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

EXT_ID = "gkojfkhlekighikafcpjkiklfbnlmeio"
PERR_HOST = "perr.hola.org"


async def get_worker(context):
    workers = list(context.service_workers)
    if not workers:
        try:
            workers.append(await context.wait_for_event("serviceworker", timeout=20000))
        except Exception:
            pass
    return next((w for w in workers if f"chrome-extension://{EXT_ID}/" in w.url), None)


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


class NestedTarget:
    def __init__(self, root, session_id):
        self.root = root
        self.session_id = session_id
        self.seq = 0
        self.pending = {}
        root.on("Target.receivedMessageFromTarget", self._on_message)

    def _on_message(self, event):
        if event.get("sessionId") != self.session_id:
            return
        try:
            msg = json.loads(event.get("message") or "{}")
        except Exception:
            return
        fut = self.pending.pop(msg.get("id"), None)
        if fut and not fut.done():
            fut.set_result(msg)

    async def send(self, method, params=None, timeout=10):
        self.seq += 1
        ident = self.seq
        fut = asyncio.get_running_loop().create_future()
        self.pending[ident] = fut
        message = json.dumps({"id": ident, "method": method, "params": params or {}})
        await self.root.send("Target.sendMessageToTarget", {"sessionId": self.session_id, "message": message})
        msg = await asyncio.wait_for(fut, timeout=timeout)
        if "error" in msg:
            raise RuntimeError(f"CDP {method}: {msg['error']}")
        return msg.get("result", {})

    async def eval(self, expression):
        r = await self.send("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
        return (r.get("result") or {}).get("value")


async def popup_target(root, worker, timeout=8):
    opened = await worker.evaluate("""async () => {
        try { await chrome.action.openPopup(); return {ok:true}; }
        catch (e) { return {ok:false,error:String(e)}; }
    }""")
    if not opened.get("ok"):
        return opened, None, None
    for _ in range(int(timeout * 10)):
        infos = (await root.send("Target.getTargets")).get("targetInfos", [])
        matches = [t for t in infos if t.get("url", "").startswith(f"chrome-extension://{EXT_ID}/js/popup.html")]
        if matches:
            t = matches[-1]
            a = await root.send("Target.attachToTarget", {"targetId": t["targetId"], "flatten": False})
            nested = NestedTarget(root, a["sessionId"])
            await nested.send("Runtime.enable")
            return opened, t, nested
        await asyncio.sleep(.1)
    return opened, None, None


CLICK_JS = r"""(patterns => {
  const visible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const els = Array.from(document.querySelectorAll('button,a,[role="button"],input,label,div,span'));
  for (const p of patterns) {
    const rx = new RegExp(p, 'i');
    const hits = els.filter(e => visible(e) && rx.test((e.innerText || e.value || '').trim()))
      .sort((a,b) => (a.innerText||a.value||'').length - (b.innerText||b.value||'').length);
    if (hits.length) {
      const e = hits[0];
      const text = (e.innerText || e.value || '').trim();
      e.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, cancelable:true, view:window}));
      e.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, cancelable:true, view:window}));
      e.click();
      return {clicked:true,text,tag:e.tagName,cls:e.className};
    }
  }
  return {clicked:false};
})"""


async def click_patterns(nested, patterns):
    return await nested.eval(f"({CLICK_JS})({json.dumps(patterns)})")


async def one_run(browser_type, ext_dir: Path, n: int):
    marker = f"SCANDAL_RADAR_HOLA_POPUP_{n}_{secrets.token_hex(12).upper()}"
    target_url = f"https://example.com/?sr_popup_marker={marker}"
    requests = []
    context = await browser_type.launch_persistent_context(
        f"/tmp/hola-popup-cdp-{n}-{secrets.token_hex(4)}",
        headless=False,
        args=[f"--disable-extensions-except={ext_dir}", f"--load-extension={ext_dir}", "--no-first-run", "--disable-sync"],
    )
    try:
        def seen(req):
            if urlparse(req.url).hostname == PERR_HOST:
                requests.append({"url":req.url,"method":req.method,"post_data":req.post_data,"resource_type":req.resource_type})
        context.on("request", seen)
        worker = await get_worker(context)
        if not worker:
            raise RuntimeError("Hola service worker missing")
        identity = await worker.evaluate("() => ({id:chrome.runtime.id,version:chrome.runtime.getManifest().version})")
        if identity["id"] != EXT_ID:
            raise RuntimeError(f"wrong ID: {identity}")

        await asyncio.sleep(2)
        target = await context.new_page()
        await target.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        await target.bring_to_front()
        active = await wait_active(worker, marker)
        if not active:
            raise RuntimeError("test URL never became active.url")

        browser = context.browser
        if browser is None:
            raise RuntimeError("Playwright browser object unavailable")
        root = await browser.new_browser_cdp_session()
        await root.send("Target.setDiscoverTargets", {"discover": True})
        start = len(requests)

        opened, info, popup = await popup_target(root, worker)
        if not popup:
            infos=(await root.send("Target.getTargets")).get("targetInfos", [])
            return {"ok":False,"run":n,"identity":identity,"popup_open":opened,"targets":infos}
        await asyncio.sleep(2)
        initial_text = await popup.eval("document.body.innerText")
        initial_buttons = await popup.eval("Array.from(document.querySelectorAll('button,a,[role=button]')).filter(e=>e.offsetWidth&&e.offsetHeight).map(e=>(e.innerText||e.textContent||'').trim()).filter(Boolean).slice(0,200)")

        # Try a visible country choice if this is the current screen.
        country = await click_patterns(popup, [r"^United States$", r"^United Kingdom$", r"^Canada$", r"^Germany$"])
        if country.get("clicked"):
            await asyncio.sleep(10)

        # Reassert the test site as active, reopen the real popup and operate the
        # documented "Is it working?" control if present.
        await target.bring_to_front()
        active2 = await wait_active(worker, marker, timeout=10)
        opened2, info2, popup2 = await popup_target(root, worker)
        if popup2:
            popup = popup2
        await asyncio.sleep(2)
        later_text = await popup.eval("document.body.innerText")
        later_buttons = await popup.eval("Array.from(document.querySelectorAll('button,a,[role=button]')).filter(e=>e.offsetWidth&&e.offsetHeight).map(e=>(e.innerText||e.textContent||'').trim()).filter(Boolean).slice(0,200)")
        diagnostic = await click_patterns(popup, [r"^No,?\s*fix it$", r"^No$", r"^Yes$"])
        if diagnostic.get("clicked"):
            await asyncio.sleep(7)

        relevant = requests[start:]
        marker_requests = [r for r in relevant if marker in json.dumps(r,sort_keys=True)]
        event_ids=[]
        for r in relevant:
            m=re.search(r"[?&]id=([^&]+)",r["url"])
            if m: event_ids.append(m.group(1))
        return {
            "ok":True,"run":n,"identity":identity,"target_url":target_url,"active_initial":active,
            "active_before_second_popup":active2,"initial_popup_text":initial_text[:12000],
            "initial_buttons":initial_buttons,"country_click":country,"later_popup_text":later_text[:12000],
            "later_buttons":later_buttons,"diagnostic_click":diagnostic,"perr_event_ids":event_ids,
            "marker_requests":marker_requests,"marker_transmitted":bool(marker_requests),"all_perr_requests":relevant,
        }
    finally:
        await context.close()


async def run(args):
    args.out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        results=[]
        for n in range(1,args.repetitions+1):
            try: results.append(await one_run(p.chromium,args.extension_dir.resolve(),n))
            except Exception as e: results.append({"ok":False,"run":n,"error":repr(e)})
        report={"probe":"hola-actual-action-popup-cdp","repetitions":args.repetitions,"results":results,
                "all_runs_ok":all(r.get("ok") for r in results),
                "ui_marker_transmissions":sum(bool(r.get("marker_transmitted")) for r in results),
                "diagnostic_ui_clicks":sum(bool((r.get("diagnostic_click") or {}).get("clicked")) for r in results)}
        (args.out_dir/"popup-cdp.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--extension-dir",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--repetitions",type=int,default=2)
    return asyncio.run(run(ap.parse_args()))


if __name__=="__main__":
    raise SystemExit(main())
