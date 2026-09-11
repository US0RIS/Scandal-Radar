#!/usr/bin/env python3
"""Launch Chrome long enough for a force-installed Web Store extension to settle.

The workflow configures ExtensionInstallForcelist before calling this script. This
keeps the official Chrome Web Store extension ID, avoiding the identity change that
can occur when a CRX is merely unpacked and loaded with --load-extension.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, dest="extension_id")
    ap.add_argument("--profile", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    args.profile.mkdir(parents=True, exist_ok=True)
    opts = Options()
    opts.add_argument(f"--user-data-dir={args.profile.resolve()}")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-sync")
    opts.add_argument("--window-size=1280,900")

    status = {"installed": False, "extension_id": args.extension_id}
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get("chrome://policy/")
        deadline = time.time() + args.timeout
        ext_root = args.profile / "Default" / "Extensions" / args.extension_id
        while time.time() < deadline:
            if ext_root.exists():
                versions = sorted(p.name for p in ext_root.iterdir() if p.is_dir())
                if versions:
                    status["installed"] = True
                    status["installed_versions"] = versions
                    status["extension_root"] = str(ext_root)
                    break
            time.sleep(2)
        status["tabs"] = [h for h in driver.window_handles]
        status["final_url"] = driver.current_url
    except Exception as exc:
        status["error"] = repr(exc)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status))
    return 0 if status.get("installed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
