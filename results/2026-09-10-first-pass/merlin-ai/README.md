# Merlin AI — first-pass test

Status: automated static audit + passive differential canary test. This is not a finding of wrongdoing.

- Web Store version archived: `8.2.3`
- CRX SHA-256: `037f314b67709ff39b701042e1b945a2cdabac7264a8ea72dde92715d2d88d41`
- Official-ID policy install succeeded: `False`
- Baseline requests observed: `25`
- Extension-present requests observed: `10`
- Differential canary-bearing request events: `0`
- Hosts seen only with extension present: `none`

## Interpretation boundary

A canary-bearing differential request would be an E1 lead only and requires clean-profile reproduction and explanation of necessity. No canary match does not prove that no data was collected because some traffic may be pinned, encrypted above HTTP, or otherwise uninspectable.
