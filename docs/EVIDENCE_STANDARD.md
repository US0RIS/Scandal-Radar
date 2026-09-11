# Evidence Standard

Scandal Radar is designed to minimize false positives. Interesting behavior is not automatically misconduct, and a discrepancy is not automatically deception.

## Evidence states

### E0 — Lead
A falsifiable question with a reason to investigate it. Inputs may include a public claim, business-model incentive, permission set, prior report, or unusual architecture.

**Required:** hypothesis, expected observable, control, falsifying outcome.

### E1 — Anomaly
A single controlled observation differs from the expected behavior.

**Required:** raw capture preserved; exact product version; environment metadata; timestamps; control result.

**Do not:** characterize the anomaly publicly as intentional, unlawful, deceptive, or representative of all users.

### E2 — Reproduced discrepancy
The observation repeats under a fresh profile/environment and survives at least one reasonable alternative explanation.

**Required:** two or more successful reproductions; clean control; variable isolation; hashes of relevant artifacts; written procedure sufficient for another person to repeat.

### E3 — Independent reproduction
A second tester or independently built environment reproduces the discrepancy without relying on the original capture.

**Required:** independent procedure/capture; version match or documented version difference; comparison of outputs.

### E4 — Corroborated finding
Technical evidence is paired with strong documentary or external corroboration: a policy/contract statement, regulator filing, source-code behavior, historical version comparison, vendor acknowledgement, or independent research.

**Required before strong publication language:** company response requested; counter-explanations recorded; scope and limitations stated.

## Claim taxonomy

Every write-up should distinguish:

- **Observed:** directly present in a capture, file, log, or reproduced UI behavior.
- **Inferred:** the most likely explanation of observations.
- **Represented:** what the vendor/platform says in a listing, policy, UI, contract, or documentation.
- **Alleged by third party:** a claim made elsewhere that Scandal Radar has not independently reproduced.
- **Unknown:** not established by available evidence.

Never silently convert an inference into an observation.

## Reproducibility packet

For every E2+ result preserve, where applicable:

```text
case_id/
  README.md
  environment.json
  product/
    manifest.json
    artifact.sha256
    version.txt
  docs/
    listing.html-or-screenshot
    privacy-policy.html-or-pdf
    terms.html-or-pdf
  control/
    network.har
    proxy.jsonl
    screen-recording.*
  treatment/
    network.har
    proxy.jsonl
    screen-recording.*
  scripts/
  notes.md
```

Do not commit secrets, authentication tokens, session cookies, personal communications, or unrelated private data. Redact before publication while retaining an access-controlled original where legally appropriate.

## Alternative-explanation checklist

Before promoting E1 -> E2, explicitly test or consider:

1. Browser-native traffic mistaken for extension traffic.
2. Requests from another installed extension.
3. Cached service-worker/background traffic.
4. First-install/update telemetry rather than ongoing behavior.
5. Account sync or browser sync.
6. OS/browser safe-browsing or spellcheck services.
7. A/B tests, geography, account cohort, or feature flags.
8. Affiliate-network redirects caused by the merchant rather than the extension.
9. A setting that was not actually applied.
10. A stale extension version or cached policy/listing.
11. Endpoint ownership misattribution caused by a CDN, analytics provider, or shared infrastructure.
12. Encrypted payload assumptions: a connection to an endpoint does not establish payload contents.

## Language standard

Prefer narrow statements such as:

> In version X, under condition Y, we observed request Z after action A and did not observe it in the matched control.

Avoid broad statements such as:

> Company X spies on everyone.

unless evidence actually supports every material component of that claim.
