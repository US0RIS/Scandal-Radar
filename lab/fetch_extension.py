#!/usr/bin/env python3
"""Fetch and archive the exact current Chrome Web Store CRX, then statically inspect it.

This uses Google's public extension update endpoint. The CRX is preserved byte-for-byte,
SHA-256 hashed, and its ZIP payload is extracted for analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from inspect_extension import analyze


def crx_zip_offset(blob: bytes) -> int:
    if blob[:4] != b"Cr24":
        if blob[:4] == b"PK\x03\x04":
            return 0
        raise ValueError("not a CRX/ZIP payload")
    version = struct.unpack_from("<I", blob, 4)[0]
    if version == 2:
        pub_len, sig_len = struct.unpack_from("<II", blob, 8)
        return 16 + pub_len + sig_len
    if version == 3:
        header_len = struct.unpack_from("<I", blob, 8)[0]
        return 12 + header_len
    raise ValueError(f"unsupported CRX version {version}")


def fetch(extension_id: str, chrome_version: str) -> bytes:
    x = urllib.parse.quote(f"id={extension_id}&uc")
    url = (
        "https://clients2.google.com/service/update2/crx"
        f"?response=redirect&prodversion={urllib.parse.quote(chrome_version)}"
        "&acceptformat=crx2,crx3"
        f"&x={x}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": f"Mozilla/5.0 Chrome/{chrome_version}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, dest="extension_id")
    ap.add_argument("--chrome-version", default="140.0.0.0")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    blob = fetch(args.extension_id, args.chrome_version)
    crx_path = args.out / f"{args.extension_id}.crx"
    crx_path.write_bytes(blob)
    sha = hashlib.sha256(blob).hexdigest()

    offset = crx_zip_offset(blob)
    zip_path = args.out / "extension.zip"
    zip_path.write_bytes(blob[offset:])
    unpacked = args.out / "unpacked"
    unpacked.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(unpacked)

    report = analyze(unpacked)
    report["extension_id"] = args.extension_id
    report["crx_sha256"] = sha
    report["crx_bytes"] = len(blob)
    (args.out / "static.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.out / "SHA256.txt").write_text(f"{sha}  {crx_path.name}\n")
    print(json.dumps({"version": report.get("version"), "sha256": sha, "bytes": len(blob)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
