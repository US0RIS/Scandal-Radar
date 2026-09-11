# First-pass findings — Merlin AI and Hola VPN

Date: 2026-09-10 / 2026-09-11 UTC

This document records leads, not allegations. No item below is above E1 under the repository evidence standard.

## Executive result

The strongest lead from the first pass is **Hola VPN's browsing-data disclosure language plus a concrete URL-bearing telemetry path in the exact current extension package**. Its current Chrome Web Store overview says its analytics do not collect browsing history or details about websites/services visited. The same Web Store listing's privacy disclosure identifies **Web history** as handled data, and Hola's April 14, 2026 privacy policy specifically states that log data obtained through the browser extension may include browsing history. Static inspection of v1.258.557 additionally shows ordinary supported UI paths that construct telemetry containing the active tab's full URL and serialize it to Hola's `perr.hola.org` endpoint. This materially strengthens the lead, but it remains E1 until the behavior is captured and reproduced under controls.

Merlin AI's exact current package contains a Give Freely integration with feature-gated code capable of sending Google search-result context and active-domain events. However, the live `merlinprod` Give Freely configuration captured in this investigation does **not** currently enable the relevant `countAppearances`, `anonymousActiveDomainLogging`, or `partnerSerpBox` flags. The code capability is therefore a lead about configuration/history and disclosure, not evidence that Merlin is presently transmitting routine browsing/search activity.

The attempted automated passive canary experiment is **incomplete**. An initial run appeared to show zero canary transmission, but post-run validation proved that the extensions were not actually installed in those browser profiles. That result was rejected. Subsequent Chrome-for-Testing attempts failed at the no-extension baseline before extension logic executed. No behavioral conclusion is drawn from those failures. A separate focused Hola Playwright probe has now been added to isolate passive behavior from controlled invocation of the production telemetry sender.

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

## Lead HOLA-01 — browsing-data disclosure vs URL-bearing telemetry

**Status: strong E1 documentary/static-code anomaly. Dynamic reproduction pending.**

Current public sources:

- Chrome Web Store listing: https://chromewebstore.google.com/detail/hola-vpn-your-website-unb/gkojfkhlekighikafcpjkiklfbnlmeio
  - Overview states that Hola does not log browsing activity or store identifiable user data.
  - Analytics description states that analytics tools do not collect browsing history or details about websites/services visited.
  - The same listing's privacy panel identifies `Web history` among handled data categories.
- Hola privacy policy: https://hola.org/legal/privacy
  - Last updated April 14, 2026.
  - The Log Data section specifically states that log data obtained through the browser extension may include browsing history and access times/dates.
- Hola browser-extension troubleshooting: https://hola.org/support/troubleshooting/extension
  - Documents the normal product flow in which a user opens the extension on a site and, under “Is it working?”, can select “no, fix it”.

### Static observations from exact package v1.258.557

A reproducible checker now lives at `lab/analyze_hola_telemetry.py`.

- Broad host permission: `*://*/*`.
- Relevant permissions include `proxy`, `webRequest`, `tabs`, `webNavigation`, `cookies`, `scripting`, and related networking APIs.
- The production configuration sets `url_perr` to `https://perr.hola.org/client_cgi`.
- The background model exports its rule module as `self.be_bg_main.be_rule`.
- `send_vpn_work_report()` constructs event `be_vpn_ok` and includes the current value of the extension's `active.url` field, i.e. the active tab's full URL, along with root URL, proxy country and other diagnostics.
- The UI `click_working()` path calls `send_vpn_work_report()`.
- The diagnostic `get_report()` used by `send_fix_it_report()` includes both `url` and `real_url` sourced from the active tab URL unless an explicit URL override is supplied.
- The UI `click_not_working()` path ultimately calls `send_fix_it_report()`; Hola's own support page documents the corresponding “no, fix it” workflow.
- The telemetry transport converts the info object to JSON, stores it in form field `info`, puts the event ID in the request query, and POSTs to `url_perr + '/perr'`.
- A tpopup-render telemetry path also constructs a `be_tpopup_open` event with both root URL and full URL; the occurrence conditions for that popup have not yet been characterized well enough to describe it as routine passive browsing behavior.

### Correction: `no_log_perrs` semantics

An earlier version of this document incorrectly interpreted the presence of `be_vpn_ok` in `no_log_perrs` as evidence that the event was suppressed. The code shows the opposite semantics.

The extension converts `conf.no_log_perrs` into an `allowed_perrs` lookup. Its no-log gate reports itself enabled for an event only when no-log mode is active **and the event is not in that lookup**. The common telemetry wrapper suppresses an event only when that gate is enabled. Therefore entries in `no_log_perrs` are exceptions that are still permitted through while no-log mode is active. `be_vpn_ok`, `be_ui_vpn_click_no_fix_it`, and `be_ui_vpn_click_no_fix_it_multi` are among those exceptions.

This correction is important because the previous interpretation understated the URL-bearing telemetry path. It still does not establish how often those paths are naturally triggered or whether every attempted request reaches/gets retained by Hola.

### What is established vs unknown

**Established by static package inspection:** current production code has normal UI-triggered telemetry paths that place the active tab's full URL into a payload destined for `perr.hola.org/client_cgi/perr`.

**Represented publicly:** the Web Store analytics language says browsing history and details about websites/services visited are not collected; the current Hola privacy policy separately says browser-extension Log Data may include browsing history.

**Not yet established:** continuous/passive collection of every site, server-side retention of any particular URL-bearing event, behavior across all users/cohorts, or whether Hola considers the diagnostic events outside the scope of the Web Store's “analytics tools” statement.

### Next decisive HOLA-01 tests

1. Verify the official extension ID in a fresh executable Chromium profile.
2. Browse a synthetic canary URL while the extension is installed but untouched; observe `perr.hola.org` during a passive window.
3. Separately invoke the normal “working” and “no, fix it” flows and inspect the URL-bearing request body.
4. Repeat successful observations in fresh profiles and compare against a no-extension control.
5. Compare disconnected vs connected VPN state and any applicable privacy/analytics settings.
6. Preserve raw request capture, exact version/hash, environment metadata and procedure before any E2 promotion.

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

The first automated passive probe produced a superficially reassuring zero-canary result. It was discarded because the workflow's post-check showed the official extensions had not actually been installed. We then added CRX3 identity reconstruction and explicit expected-ID verification. Chrome-for-Testing attempts failed during the **no-extension browser baseline** with `SessionNotCreatedException`, before either Merlin or Hola code executed. Consequently:

- zero-canary results from the invalid run are not findings;
- runner launch failures are not findings;
- the static/documentary leads above are the only first-pass results currently promoted.

A focused Hola Playwright workflow now records passive and controlled-invocation observations separately. Its controlled invocation calls the exact production sender only after verifying the official extension identity and a synthetic active-tab URL; that validates transport construction but will not be mischaracterized as natural-user triggering.

This is intentional: Scandal Radar should prefer “incomplete test” over a false negative or false accusation.
