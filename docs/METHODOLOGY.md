# Methodology

## Objective

Find high-impact, reproducible discrepancies between user-facing representations and actual product behavior. The process is hypothesis-driven and intentionally attempts to disprove each lead.

## 1. Candidate discovery

Generate candidates broadly across categories where software has privileged access or opaque incentives:

- shopping/cashback extensions
- VPN/privacy/security extensions
- AI/browser assistants
- password managers
- ad blockers and anti-tracking tools
- screen capture / transcription tools
- connected TVs and streaming devices
- connected cars
- mobile SDKs and data brokers

A candidate is scored for **investigative expected value**, not suspected guilt.

## 2. Scoring

Each factor is scored 0-5 and converted to a weighted 100-point score.

| Factor | Weight | Question |
|---|---:|---|
| Scale | 12 | How many users/devices could plausibly be affected? |
| Privilege | 14 | How sensitive is the product's technical access? |
| Incentive conflict | 16 | Is there a monetization incentive users may not understand? |
| Claim specificity | 14 | Are there precise public statements/settings we can test? |
| Testability | 16 | Can behavior be measured in a controlled environment? |
| Potential harm | 10 | If the hypothesis were true, how consequential would it be? |
| Reproducibility | 10 | Can an independent researcher repeat the experiment cheaply? |
| Novelty | 8 | Is the question materially under-investigated? |

The score is:

```text
sum((factor / 5) * factor_weight)
```

Scores are expected to change after manifest capture and preliminary tests.

## 3. Freeze representations before testing

For every target capture:

- exact product/extension version
- Chrome Web Store listing
- privacy disclosure panel
- privacy policy
- terms / affiliate terms where applicable
- onboarding and consent UI
- settings UI
- relevant platform rules
- capture date and hashes where possible

Historical snapshots are valuable because representations and behavior can change after scrutiny.

## 4. Static triage

For browser extensions inspect:

- `manifest_version`
- permissions
- host permissions
- optional permissions
- content scripts and match patterns
- background service worker
- web-accessible resources
- externally connectable configuration
- remote endpoints present in source/configuration
- analytics/affiliate SDK names
- URL/cookie/webRequest-related APIs

Static evidence tells us what software *can* do, not necessarily what it *does*.

## 5. Differential dynamic testing

Use a clean browser profile and change one independent variable at a time.

### Generic matrix

| Condition | Extension | Interaction | Setting |
|---|---|---|---|
| C0 | absent | none | n/a |
| C1 | installed | none | defaults |
| C2 | installed | feature invoked | defaults |
| C3 | installed | none | privacy/analytics opt-out |
| C4 | installed | feature invoked | privacy/analytics opt-out |

Repeat each condition on synthetic pages containing unique path, query and body canaries.

### Shopping/affiliate matrix

Test at least:

1. direct navigation, extension absent
2. controlled affiliate referral, extension absent
3. controlled affiliate referral, extension installed but untouched
4. extension installed, coupon scan invoked, no coupon benefit found
5. extension installed, feature invoked and actual benefit produced
6. cashback explicitly activated

Capture redirect chains, cookie changes, query parameters, local/session storage and relevant network requests. Do not assume every attribution mechanism uses a cookie.

### Privacy/AI matrix

Test:

1. synthetic non-sensitive page
2. unique path/query canary
3. unique visible body-text canary
4. editable-field canary
5. extension installed but idle
6. feature explicitly invoked
7. analytics/privacy setting toggled if present
8. offline activity followed by reconnect

Look separately for hostname, path/query and content transmission.

## 6. Canary design

Use synthetic markers that cannot plausibly appear by coincidence:

```text
SCANDAL_RADAR_URL_20260910_A91C42
SCANDAL_RADAR_BODY_20260910_D712EF
SCANDAL_RADAR_FORM_20260910_9BB831
```

Never use real secrets, passwords, medical information, personal messages, or third-party data as canaries.

## 7. Attribution analysis

For every request/redirect record:

- timestamp
- initiator if available
- source process/context if available
- method
- destination hostname
- URL path/query after redaction
- request/response headers after secret redaction
- body hashes and selected synthetic-canary matches
- before/after cookie/storage diff

Endpoint ownership must be verified separately; CDN or analytics infrastructure can make naive hostname attribution wrong.

## 8. Repeat and blind reproduction

An interesting anomaly is rerun in a new browser profile. High-impact discrepancies should then be given to a second tester with the procedure but without the expected result when practical.

## 9. Vendor response

Before publishing an E4 claim:

- send the narrow technical finding
- provide exact version and reproduction steps
- ask whether behavior is expected
- ask which disclosure/setting authorizes it
- give the vendor's explanation a serious attempt at falsification
- preserve the response verbatim in the private case record

## 10. Publication threshold

The project's goal is not to maximize accusations. It is to maximize the probability that anything eventually published survives technical, legal, and adversarial scrutiny.
