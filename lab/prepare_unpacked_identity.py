#!/usr/bin/env python3
"""Prepare a CRX3 package for unpacked Chrome testing under its Web Store ID.

Chrome normally assigns a new ID to an unpacked extension if manifest.json lacks a
`key`. Web Store CRX3 files contain the publisher public key in their signed header.
This script extracts the proof whose public-key hash maps to the expected extension
ID, copies the unpacked package, and adds that public key as manifest `key`.

The extension code is otherwise unchanged. The output is for controlled testing only;
the original CRX and its SHA-256 remain the authoritative archived artifact.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import struct
from pathlib import Path


def read_varint(blob: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(blob):
            raise ValueError("truncated protobuf varint")
        byte = blob[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            raise ValueError("oversized protobuf varint")


def iter_proto_fields(blob: bytes):
    offset = 0
    while offset < len(blob):
        tag, offset = read_varint(blob, offset)
        number, wire_type = tag >> 3, tag & 7
        if wire_type == 0:
            value, offset = read_varint(blob, offset)
        elif wire_type == 1:
            value = blob[offset : offset + 8]
            offset += 8
        elif wire_type == 2:
            length, offset = read_varint(blob, offset)
            value = blob[offset : offset + length]
            offset += length
        elif wire_type == 5:
            value = blob[offset : offset + 4]
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire_type}")
        yield number, wire_type, value


def extension_id_for_public_key(public_key: bytes) -> str:
    # Chrome maps the first 128 bits of SHA-256 to a-p, one hex nibble per letter.
    prefix = hashlib.sha256(public_key).hexdigest()[:32]
    return "".join(chr(ord("a") + int(nibble, 16)) for nibble in prefix)


def extract_matching_public_key(crx: bytes, expected_id: str) -> bytes:
    if crx[:4] != b"Cr24" or struct.unpack_from("<I", crx, 4)[0] != 3:
        raise ValueError("expected CRX3 input")
    header_length = struct.unpack_from("<I", crx, 8)[0]
    header = crx[12 : 12 + header_length]

    candidates: list[bytes] = []
    # CRX3 CrxFileHeader fields 2/3 are RSA/ECDSA AsymmetricKeyProof messages.
    for number, wire_type, value in iter_proto_fields(header):
        if number not in (2, 3) or wire_type != 2 or not isinstance(value, bytes):
            continue
        for sub_number, sub_wire_type, sub_value in iter_proto_fields(value):
            if sub_number == 1 and sub_wire_type == 2 and isinstance(sub_value, bytes):
                candidates.append(sub_value)
                if extension_id_for_public_key(sub_value) == expected_id:
                    return sub_value
    observed = [extension_id_for_public_key(key) for key in candidates]
    raise ValueError(f"no CRX3 proof matched {expected_id}; observed IDs: {observed}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crx", type=Path, required=True)
    ap.add_argument("--unpacked", type=Path, required=True)
    ap.add_argument("--expected-id", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    public_key = extract_matching_public_key(args.crx.read_bytes(), args.expected_id)
    if args.out.exists():
        shutil.rmtree(args.out)
    shutil.copytree(args.unpacked, args.out)

    manifest_path = args.out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["key"] = base64.b64encode(public_key).decode("ascii")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = {
        "expected_id": args.expected_id,
        "derived_id": extension_id_for_public_key(public_key),
        "public_key_sha256": hashlib.sha256(public_key).hexdigest(),
        "prepared_dir": str(args.out),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
