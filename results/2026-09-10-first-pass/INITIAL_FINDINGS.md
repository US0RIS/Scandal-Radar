# First-pass findings — Merlin AI and Hola VPN

Date: 2026-09-10 / 2026-09-11 UTC

This document records leads, not allegations. No item below is above E1 under the repository evidence standard.

## Executive result

The strongest lead from the first pass is **Hola VPN's public disclosure language**. Its current Chrome Web Store overview says it does not log browsing activity and that its analytics do not collect browsing history or details about websites/services visited. The same Web Store listing's privacy disclosure says the extension handles **Web history**, and Hola's current privacy-policy page says Log Data may include the web pages a user visits and time spent on them. This is a documentary discrepancy that deserves behavioral testing; it is not yet proof of undisclosed collection.

Merlin AI's exact current package contains a Give Freely integration with feature-gated code capable of sending Google search-result context and active-domain events. However, the live `merlinprod` Give Freely configuration captured in this investigation does **not** currently enable the relevant `countAppearances`, `anonymousActiveDomainLogging`, or `partnerSerpBox` flags. The code capability is therefore a lead about configuration/history and disclosure, not evidence that Merlin is presently transmitting routine browsing/search activity.

The attempted automated passive canary experiment is **incomplete**. An initial run appeared to show zero canary transmission, but post-run validation proved that the extensions were not actually installed in those browser profiles. That result was rejected. Subsequent runs reconstructed the original Web Store IDs from the CRX3 signing keys, but the GitHub-hosted Chrome-for-Testing process failed at the no-extension baseline before extension logic executed. No behavioral conclusion is drawn from those failures.

## Frozen packages

### Merlin AI

- Chrome extension ID: `camppjleccjaphfdbohjdohecfnoikec`
- Version: `8.2.3`
- CRX SHA-256: `037f314b67709ff39b701042e1b945a2cdabac7264a8ea72dde92715d2d88d41`
- Exact CRX3 publisher key was successfully reconstructed to the expected Web Store ID for controlled unpacked testing.

### Hola VPN

- Chrome extension ID: `gkojfkhlekighikafcpjkiklfbnlmeio`
- Version: `1.258.557`
- CRX SHA-256: `1a0b25c190053040c87d0a71d0df8e5751237d470920511f5062925f9c5e6a65`
- Exact CRX3 publisher key was successfully reconstructed to the expected Web Store ID for controlled unpacked testing.

## Lead HOLA-01 — disclosure mismatch about browsing history

**Status: E1 documentary anomaly.**

Current public sources:

- Chrome Web Store listing: https://chromewebstore.google.com/detail/hola-vpn-your-website-unb/gkojfkhlekighikafcpjkiklfbnlmeio
  - Overview states that Hola does not log browsing activity or store identifiable user data.
  - Analytics description states that analytics tools do not collect browsing history or details about websites/services visited.
  - The same listing's privacy panel identifies `Web history` among handled data categories.
- Hola privacy policy: https://hola.org/legal/privacy
  - The Log Data section says data may include IP address, operating system, browser type, web pages visited, time spent on those pages, and access times/dates.

Possible innocent explanations that must be tested before promotion:

1. The Web Store overview may use “log browsing activity” in a narrower sense than the privacy policy.
2. The privacy policy may cover Hola products/services beyond this specific Chrome extension.
3. `Web history` in the Chrome disclosure may reflect local processing necessary for VPN operation rather than server-side retention.
4. The privacy policy may describe optional/error/diagnostic paths rather than routine browsing telemetry.

Static package observations relevant to the next experiment:

- Broad host permission: `*://*/*`.
- Relevant extension permissions include `proxy`, `webRequest`, `tabs`, `webNavigation`, `cookies`, `scripting`, and related networking APIs.
- The background code maintains active-tab URL state and limited per-tab host history for VPN operation.
- The package contains a remote diagnostic/event mechanism targeting `https://perr.hola.org/client_cgi/perr`.
- Some diagnostic call sites are structurally capable of attaching URL fields.
- Importantly, a prominent `be_vpn_ok` URL-bearing event is present in the package's static `no_log_perrs` defaults, so its existence must **not** be represented as evidence that routine active URLs are currently sent remotely.

### Next decisive HOLA-01 tests

Run on a local real Chrome/Chromium environment where extension installation can be visually and programmatically verified:

1. Disconnected baseline: synthetic URL/body/input/title canaries.
2. Connected VPN mode on a supported destination.
3. Applicable analytics/privacy settings on vs off.
4. Successful VPN route vs connection/error path.
5. CAPTCHA/error and payment-related flows only where they can be triggered safely with synthetic/test data.
6. Specifically inspect requests to `perr.hola.org` and determine whether site URLs, URL-derived identifiers, search terms, or page content appear.
7. Repeat any anomaly in a fresh profile before E2.

## Lead MERLIN-01 — dormant Give Freely browsing/search telemetry capability

**Status: E0/E1 code/configuration lead; no current behavioral discrepancy established.**

Current exact package observations:

- Merlin v8.2.3 bundles a `giveFreely.js` content script running at `document_idle` on `<all_urls>`.
- The package initializes Give Freely with production partner key `merlinprod`.
- Give Freely configuration is fetched from public CDN configuration including:
  - `https://cdn.givefreely.com/data/behavioral/global.json`
  - `https://cdn.givefreely.com/data/behavioral/merlinprod.json`
- The configured event endpoint is `https://events.givefreely.com/popup`.
- Feature-gated code exists for:
  - `countAppearances`: on Google search-result pages, extract merchant results and construct events containing current search URL / merchant-result context.
  - `anonymousActiveDomainLogging`: construct active-domain logging events.
  - `partnerSerpBox`: alter/inject partner search-result UI.

Live configuration captured during this investigation is preserved under `results/2026-09-10-first-pass/merlin-ai/live-config/`.

At capture time, the merged production configuration had:

- `popupEnabled`: `true`
- `eventsUrl`: `https://events.givefreely.com/popup`
- `countAppearances`: unset/null
- `anonymousActiveDomainLogging`: unset/null
- `partnerSerpBox`: unset/null
- `enhancedLogging`: unset/null

Therefore the current evidence does **not** support saying that Merlin presently enables those search/active-domain logging paths.

## Lead MERLIN-02 — Give Freely disclosure scope discrepancy

**Status: E1 documentary anomaly, subject to scope/version explanation.**

Relevant current public pages:

- Merlin / Give Freely page: https://givefreely.com/merlin
- Give Freely transparency: https://givefreely.com/transparency
- Give Freely privacy policy: https://givefreely.com/privacy-policy

The Merlin-facing and transparency materials characterize Give Freely as not collecting/tracking browsing behavior. The broader privacy policy describes installed Platform “Apps” as potentially automatically tracking websites visited and activity such as searches, views, clicks, browsing activity, and transactions.

This may be explained by the privacy policy covering other Give Freely products/configurations, historical behavior, or optional features. Because the Merlin package actually contains feature-gated code for some browsing/search telemetry, the discrepancy is worth preserving and testing, but current configuration evidence weakens any claim that the capability is active for Merlin today.

### Next decisive MERLIN tests

1. Archive `global.json` and `merlinprod.json` over time and diff feature flags.
2. Run a verified extension-present canary test on a local browser.
3. Run controlled Google-search-result tests while watching `events.givefreely.com`.
4. Separately test affiliate attribution: extension installed/untouched vs Give Freely interaction vs actual user benefit.
5. Test whether pre-existing affiliate attribution is preserved as represented by Give Freely.
6. Repeat anomalies across clean profiles/merchants before promotion.

## Dynamic-test integrity note

The first automated passive probe produced a superficially reassuring zero-canary result. It was discarded because the workflow's post-check showed the official extensions had not actually been installed. We then added CRX3 identity reconstruction and explicit expected-ID verification. Current GitHub-hosted Chrome-for-Testing attempts fail during the **no-extension browser baseline** with `SessionNotCreatedException`, before either Merlin or Hola code executes. Consequently:

- zero-canary results from the invalid run are not findings;
- runner launch failures are not findings;
- the static/documentary leads above are the only first-pass results currently promoted.

This is intentional: Scandal Radar should prefer “incomplete test” over a false negative or false accusation.
