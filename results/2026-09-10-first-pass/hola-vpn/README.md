# Hola VPN — first-pass test

Status: automated static audit + passive differential canary test. This is not a finding of wrongdoing.

- Web Store version archived: `1.258.557`
- CRX SHA-256: `1a0b25c190053040c87d0a71d0df8e5751237d470920511f5062925f9c5e6a65`
- Official-ID policy install succeeded: `False`
- Baseline requests observed: `22`
- Extension-present requests observed: `10`
- Differential canary-bearing request events: `0`
- Hosts seen only with extension present: `none`

## Interpretation boundary

A canary-bearing differential request would be an E1 lead only and requires clean-profile reproduction and explanation of necessity. No canary match does not prove that no data was collected because some traffic may be pinned, encrypted above HTTP, or otherwise uninspectable.
