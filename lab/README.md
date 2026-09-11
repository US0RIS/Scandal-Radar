# Browser Extension Lab

This directory contains minimal tooling for authorized experiments on a clean local browser profile.

## 1. Start a synthetic canary page

```bash
python3 lab/canary_server.py
```

The server prints four fresh synthetic tokens and serves a page at `http://127.0.0.1:8765/` containing markers in the title, visible body, form field and query link.

Use those markers to distinguish:

- URL/path/query access
- visible page-content access
- editable-form access

from generic telemetry.

## 2. Static-triage an unpacked extension

```bash
python3 lab/inspect_extension.py /path/to/unpacked-extension --out artifacts/static.json
```

Or analyze a ZIP containing an unpacked extension:

```bash
python3 lab/inspect_extension.py extension.zip
```

The report inventories permissions, host permissions, content scripts, background configuration, literal remote hosts and selected keyword frequencies. **Static presence is capability/evidence-of-code only; it is not proof that a path executes.**

## 3. Capture authorized browser traffic

Install `mitmproxy` in an isolated Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install mitmproxy
```

Start the logger with the canaries printed by the local server:

```bash
export SCANDAL_RADAR_CANARIES='TOKEN1,TOKEN2,TOKEN3,TOKEN4'
export SCANDAL_RADAR_PROXY_LOG='artifacts/proxy.jsonl'
mitmdump -s lab/mitm_addon.py
```

Configure only the **test browser/profile you control** to use the proxy and trust the local mitmproxy certificate if needed for that test environment. Do not use certificate-pinning bypasses or intercept traffic from other users/devices.

The logger redacts common secret-bearing headers and records body hashes/canary matches. Review captures again before committing them; application-layer bodies may still contain sensitive information that is not in a standard secret header.

## 4. Clean-profile discipline

For each condition:

1. create a fresh Chrome profile
2. disable browser sync
3. install no extensions other than the target
4. record Chrome version, OS, target extension version and target extension ID
5. start capture before installation when practical
6. run the control/treatment procedure exactly
7. stop capture and hash the artifacts
8. repeat in a fresh profile

## 5. Affiliate experiments

Do not begin with a real purchase. First inspect whether a condition changes:

- redirects
- URL/query affiliate identifiers
- cookies
- local/session storage
- network requests

A purchase is only necessary if conversion behavior itself is the research question and the transaction is permitted by all applicable terms.

## 6. What a strong first result looks like

A useful E1 packet is narrow:

```text
Target: Example Extension v1.2.3
Control: affiliate referral -> retailer; extension absent
Treatment: same referral -> retailer; extension installed but untouched
Observation: treatment added/changed identifier X at timestamp T; control did not
Raw evidence: HAR + proxy JSONL + screen recording
Alternative explanations not yet excluded: ...
```

Then reproduce it before drawing conclusions.
