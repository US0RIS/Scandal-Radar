#!/usr/bin/env python3
"""Static triage for an unpacked Chrome extension or ZIP archive.

This is intentionally conservative. It inventories declared privilege and obvious
remote endpoints/keywords; it does not claim that discovered code paths execute.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s\"'<>\\)]+", re.IGNORECASE)
KEYWORDS = (
    "affiliate",
    "commission",
    "cashback",
    "coupon",
    "analytics",
    "telemetry",
    "tracking",
    "webRequest",
    "cookies",
    "history",
    "tabs",
    "scripting",
)
TEXT_SUFFIXES = {".js", ".mjs", ".cjs", ".json", ".html", ".css", ".txt", ".map"}
MAX_FILE_BYTES = 10_000_000


def unpack_if_needed(path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if path.is_dir():
        return path, None
    if path.suffix.lower() != ".zip":
        raise ValueError("input must be an unpacked extension directory or .zip archive")
    tmp = tempfile.TemporaryDirectory(prefix="scandal-radar-")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(tmp.name)
    return Path(tmp.name), tmp


def find_manifest(root: Path) -> Path:
    direct = root / "manifest.json"
    if direct.exists():
        return direct
    matches = list(root.rglob("manifest.json"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one manifest.json, found {len(matches)}")
    return matches[0]


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            yield path, path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue


def analyze(root: Path) -> dict[str, object]:
    manifest_path = find_manifest(root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    urls: Counter[str] = Counter()
    keyword_hits: Counter[str] = Counter()
    scanned_files = 0

    for _, text in iter_text_files(root):
        scanned_files += 1
        for match in URL_RE.findall(text):
            try:
                parsed = urlparse(match.rstrip(".,;"))
                if parsed.hostname:
                    urls[parsed.hostname.lower()] += 1
            except ValueError:
                pass
        lowered = text.lower()
        for keyword in KEYWORDS:
            count = lowered.count(keyword.lower())
            if count:
                keyword_hits[keyword] += count

    content_scripts = []
    for script in manifest.get("content_scripts", []) or []:
        content_scripts.append(
            {
                "matches": script.get("matches", []),
                "exclude_matches": script.get("exclude_matches", []),
                "js": script.get("js", []),
                "run_at": script.get("run_at"),
                "all_frames": script.get("all_frames", False),
            }
        )

    return {
        "manifest_path": str(manifest_path.relative_to(root)),
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "manifest_version": manifest.get("manifest_version"),
        "permissions": manifest.get("permissions", []),
        "optional_permissions": manifest.get("optional_permissions", []),
        "host_permissions": manifest.get("host_permissions", []),
        "optional_host_permissions": manifest.get("optional_host_permissions", []),
        "background": manifest.get("background"),
        "content_scripts": content_scripts,
        "externally_connectable": manifest.get("externally_connectable"),
        "web_accessible_resources": manifest.get("web_accessible_resources", []),
        "scanned_text_files": scanned_files,
        "remote_hosts_by_literal_url_frequency": urls.most_common(100),
        "keyword_hits": dict(keyword_hits.most_common()),
        "warning": "Static presence does not establish runtime behavior or endpoint ownership.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("extension", type=Path, help="unpacked extension directory or ZIP")
    parser.add_argument("--out", type=Path, help="write JSON report to this path")
    args = parser.parse_args()

    root, tmp = unpack_if_needed(args.extension)
    try:
        report = analyze(root)
    finally:
        if tmp is not None:
            tmp.cleanup()

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
