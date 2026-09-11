# Hola focused telemetry probe

This is a controlled research result, not an allegation of intent or illegality.

- Extension ID reconstructed/expected: `gkojfkhlekighikafcpjkiklfbnlmeio`
- Static telemetry assertions all matched: `True`
- Successful controlled transport capture: `True`
- Passive canary-bearing telemetry observations: `0`

The controlled invocation calls the exact production `send_vpn_work_report` function inside the extension service worker after loading a synthetic active-tab URL. It validates request construction/transport but is not, by itself, a natural-user behavioral reproduction.

A passive canary match, if present, is more significant and requires fresh-profile reproduction and controls before promotion under the evidence ladder.
