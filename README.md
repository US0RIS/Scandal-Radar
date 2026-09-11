# Scandal Radar

Scandal Radar is a reproducible consumer-tech investigation pipeline for finding high-impact discrepancies between what products **say they do** and what they **actually do** under controlled conditions.

The project is deliberately allegation-averse. A company appearing in `data/candidates.csv` means only that it is a good **research target**: it has scale, privileged access, a testable business-model incentive, specific public claims, or some combination of those. It does **not** mean misconduct has been found.

## Current focus

**Phase 1: Chrome extensions (September 2026).** The initial hunt concentrates on extensions because they combine large install bases, broad access to browser activity, comparatively opaque monetization, and excellent experimental reproducibility.

The initial priority queue is generated from eight dimensions:

- Scale
- Privileged access
- Incentive conflict
- Specificity of public claims
- Experimental testability
- Potential user harm
- Reproducibility
- Novelty / likelihood the question is not already exhausted

Run:

```bash
python3 scripts/rank_candidates.py
```

The current seed set contains 20 extensions with public Chrome Web Store install counts captured on 2026-09-10. Scores rank **investigative expected value**, not trustworthiness.

## Initial high-priority leads

| Rank | Target | Why it is experimentally interesting |
|---:|---|---|
| 1 | Merlin AI | Page-aware AI extension plus explicit disclosure that it may receive affiliate commissions on visited sites/products; attribution behavior is directly testable. |
| 2 | Hola VPN | High-privilege privacy product with specific claims about analytics and browsing-history collection that can be tested against observed network behavior. |
| 3 | Capital One Shopping | 11M-user shopping extension; affiliate attribution, coupon activation, and passive-vs-active behavior are measurable. |
| 4 | Coupert | 3M-user coupon/cashback extension; strong affiliate incentive and straightforward controlled-purchase experiments. |
| 5 | Rakuten | 3M-user cashback extension with explicit one-click activation language; attribution boundaries are testable. |
| 6 | Karma | Explicitly says current-page URL access is limited to shopping features and that it does not collect browsing history; unusually crisp canary tests are possible. |
| 7 | PayPal Honey | Large and experimentally rich, but reduced novelty because affiliate-attribution behavior has already received extensive public scrutiny. |
| 8 | Urban VPN | 7M-user privacy/security extension with privileged traffic access and measurable connected/disconnected telemetry. |
| 9 | RetailMeNot | Coupon/cashback economics create clean attribution and user-benefit experiments. |
| 10 | Ibotta | Cashback activation language makes passive-versus-active attribution behavior falsifiable. |

These rankings will change as we capture permissions, manifests, historical versions, disclosures, network endpoints, and first-pass test results.

## Evidence ladder

Scandal Radar separates a **lead** from a **finding**:

- **E0 — Lead:** a hypothesis worth testing.
- **E1 — Anomaly:** one observation inconsistent with the expected behavior.
- **E2 — Reproduced discrepancy:** the anomaly survives clean-profile repetition and controls.
- **E3 — Independent reproduction:** a second environment/person reproduces the discrepancy.
- **E4 — Corroborated finding:** technical evidence is paired with authoritative documentary evidence, vendor response, or another independent source.

No repository language should characterize a target as deceptive, unlawful, malicious, or a “scandal” merely because it is an E0/E1 lead.

See [`docs/EVIDENCE_STANDARD.md`](docs/EVIDENCE_STANDARD.md).

## Experimental philosophy

The core primitive is the **differential test**. Change one factor and compare:

```text
extension absent       vs installed
feature never invoked  vs invoked
tracking/analytics on  vs off
cashback not activated vs activated
clean destination URL  vs synthetic canary URL
fresh profile          vs aged profile
normal flow            vs known affiliate-referral flow
online                 vs offline -> reconnect
```

Prefer synthetic data and controlled pages. A useful test page might contain a unique marker such as:

```text
SCANDAL_RADAR_CANARY_7F41D2C9
```

If the marker appears in traffic from the test machine, that is evidence about transmission without exposing anyone else's data.

## Repository layout

```text
data/
  candidates.csv             Seed target registry and factor scores
  hypotheses.csv             Falsifiable hypotheses, controls and expected observations

docs/
  EVIDENCE_STANDARD.md       Rules for promoting a lead into a finding
  LEGAL_ETHICAL_GUARDRAILS.md
  METHODOLOGY.md

lab/
  canary_server.py           Local synthetic test-page server
  mitm_addon.py              mitmproxy logger for traffic from owned test environments
  inspect_extension.py       Static manifest / endpoint triage for unpacked extensions

scripts/
  rank_candidates.py         Deterministic scoring/ranking CLI

sources/
  seed_sources.md            Public-source snapshot behind the initial registry

tests/
  test_scoring.py
```

## First investigation sequence

1. Freeze the current Web Store listing, privacy disclosure, privacy policy, version, extension ID, and install count for the top targets.
2. Download/archive the exact extension version used for testing and hash it.
3. Inspect `manifest.json`, requested permissions, host permissions, externally reachable resources, and obvious remote endpoints.
4. Run a clean-profile baseline with the extension absent.
5. Install the extension but do not interact with it; repeat synthetic browsing.
6. Invoke the relevant feature and repeat.
7. Repeat with applicable privacy/analytics/cashback settings toggled.
8. For affiliate extensions, compare clean/direct navigation, a controlled affiliate referral, passive extension presence, and explicit extension activation.
9. Promote only reproducible differences to E2.
10. Ask a second tester to reproduce any high-impact E2 finding before public characterization.

## Safety boundary

This project is for observation of software, accounts, devices, traffic, and test infrastructure that the researcher owns or is authorized to test. It is not a framework for unauthorized access, credential theft, intercepting third-party communications, bypassing access controls, or obtaining other users' private data.

## Status

`v0.1`: repository initialized; scoring model, 20-target seed registry, experiment hypotheses, evidence standard, and local lab scaffolding are being established.
