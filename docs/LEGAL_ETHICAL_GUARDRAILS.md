# Legal and Ethical Guardrails

Scandal Radar is intended for authorized, reproducible consumer-tech research. The fact that a technique is technically possible does not make it appropriate or lawful.

## Allowed research posture

Use:

- hardware you own or are authorized to test
- browser profiles and accounts you control
- synthetic test pages and synthetic canary strings
- your own network traffic
- public product listings, policies, terms, developer documentation, public code, and public regulatory/court records
- controlled affiliate links/accounts only where their terms permit the experiment
- ordinary product features and documented settings

## Do not use this project to

- access systems or accounts without authorization
- steal or guess credentials
- intercept another person's private communications
- collect unrelated third-party personal data
- bypass authentication or technical access controls to obtain non-public data
- plant malware or persistence on third-party devices
- socially engineer employees for credentials or internal access
- impersonate another person to obtain protected records
- evade rate limits or anti-abuse controls in ways that create operational harm
- publish authentication tokens, session cookies, API keys, or personal communications

If a research question materially depends on access-control circumvention, interception law, confidential records, breach data, or testing infrastructure you do not own, stop and obtain specialist legal advice before proceeding.

## Privacy by design

Prefer synthetic data. A synthetic marker is stronger evidence than a real secret because it establishes provenance without creating collateral exposure.

For dynamic tests:

1. create a fresh browser profile
2. disable browser sync
3. install only the target extension
4. use synthetic pages/accounts where possible
5. capture only the traffic necessary for the experiment
6. redact tokens/cookies before committing artifacts
7. separate private raw evidence from public reproductions

## Affiliate experiments

Affiliate attribution experiments should use transactions/referrals you are authorized to conduct. Avoid intentionally generating invalid commissions, fake purchases, chargeback abuse, or activity prohibited by an affiliate network's terms.

Where a purchase is unnecessary, attribution can often be studied through redirect chains, cookies, storage, or network parameters before checkout.

## Vendor contact

For high-impact E2/E3 findings, contact the vendor before strong publication. Provide a narrow description, exact product version, reproduction procedure, and enough technical detail for the vendor to investigate.

A vendor's disagreement is evidence to evaluate, not evidence to ignore. Preserve the explanation and test it where possible.

## Public claims

Technical evidence rarely establishes intent by itself. Distinguish behavior from motive.

Good:

> In extension version X, installing the extension changed affiliate parameter Y during condition Z, while the matched control did not.

Not justified by that evidence alone:

> The company intentionally stole commissions.

Questions about deception, fraud, wiretapping, computer misuse, unfair practices, or privacy-law violations are legal conclusions that depend on jurisdiction and facts beyond a packet capture.
