#!/usr/bin/env python3
"""Run a passive canary probe in a fresh Chrome profile.

The test visits example.com, then modifies the DOM locally so the canaries were never
sent by the origin server. It changes the visible body, an unsubmitted input field,
the document title, and the URL via history.pushState (no navigation). The browser is
then left idle. Any outbound appearance of those synthetic markers is recorded by the
mitmproxy addon, with a separate no-extension control required for interpretation.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--proxy", required=True)
    ap.add_argument("--idle-seconds", type=int, default=25)
    args = ap.parse_args()

    tokens = [x for x in os.environ.get("SCANDAL_RADAR_CANARIES", "").split(",") if x]
    if len(tokens) < 4:
        raise SystemExit("SCANDAL_RADAR_CANARIES must contain URL,BODY,INPUT,TITLE tokens")
    url_token, body_token, input_token, title_token = tokens[:4]

    args.profile.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    opts = Options()
    opts.add_argument(f"--user-data-dir={args.profile.resolve()}")
    opts.add_argument(f"--proxy-server={args.proxy}")
    opts.add_argument("--proxy-bypass-list=<-loopback>")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-sync")
    opts.add_argument("--disable-translate")
    opts.add_argument("--window-size=1280,900")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    started = time.time()
    status = {"ok": False, "started_unix": started, "idle_seconds": args.idle_seconds}
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get("https://example.com/")
        time.sleep(3)
        driver.execute_script(
            """
            const [u,b,i,t] = arguments;
            document.title = t;
            document.body.innerHTML = `
              <main id='scandal-radar'>
                <h1>Controlled synthetic probe</h1>
                <p id='body-canary'>${b}</p>
                <label>Unsubmitted field <input id='input-canary' type='text'></label>
              </main>`;
            document.getElementById('input-canary').value = i;
            history.pushState({}, '', '/scandal-radar-probe?marker=' + encodeURIComponent(u));
            """,
            url_token,
            body_token,
            input_token,
            title_token,
        )
        status["page_url_after_pushstate"] = driver.current_url
        status["title_after_injection"] = driver.title
        status["injected_unix"] = time.time()
        time.sleep(args.idle_seconds)
        status["browser_console"] = driver.get_log("browser")[-100:]
        status["ok"] = True
    except Exception as exc:
        status["error"] = repr(exc)
    finally:
        status["finished_unix"] = time.time()
        try:
            driver.quit()
        except Exception:
            pass
        args.out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
