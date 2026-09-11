# Seed Sources — 2026-09-10

This file records the public sources used to seed the initial Chrome-extension target registry. These sources establish public representations, scale, and experiment design inputs. They do **not** establish misconduct.

## Chrome Web Store policy baselines

### Affiliate Ads policy

Source: https://developer.chrome.com/docs/webstore/program-policies/affiliate-ads/

Relevant test baseline as of capture: affiliate links/codes/cookies must be tied to a direct and transparent user benefit, and a related user action is required before inclusion. The policy gives examples including background affiliate injection, updating shopping cookies without the user's knowledge, and replacing existing affiliate codes without related user action.

FAQ: https://developer.chrome.com/docs/webstore/program-policies/affiliate-ads-faq/

### July 2026 privacy policy update

Source: https://developer.chrome.com/blog/cws-policy-updates-2026

Published 2026-07-01; enforcement stated to begin 2026-08-01. The update says extension-collected user data must be strictly necessary to the disclosed single purpose and all data collection must be prominently disclosed, including later changes in data-handling practices.

Limited Use policy: https://developer.chrome.com/docs/webstore/program-policies/limited-use/

## Seed targets

Install counts below are public Chrome Web Store counts observed in search/store results on or immediately before 2026-09-10 and are rounded by the store.

| Target | Public users | Source | Seed-relevant representation |
|---|---:|---|---|
| Grammarly | 40,000,000 | https://chromewebstore.google.com/detail/grammarly-ai-writing-assi/kbfnbcaeplbcioakkpcpgfkobkghlhen | Store privacy panel lists PII, personal communications, location, user activity, and website content. |
| PayPal Honey | 13,000,000 | https://chromewebstore.google.com/detail/honey-automated-coupons-r/bmnlcjabgnpnenekpadlanbbkooimhnj | Coupon/rewards extension; store panel lists web history, user activity, website content and other data categories. Prior public scrutiny reduces novelty, so it is mainly useful as a regression/control target. |
| Capital One Shopping | 11,000,000 | https://chromewebstore.google.com/detail/capital-one-shopping-save/nenlahapcbofgnanklpelkaejcehkggg | Automatically searches prices/codes while users shop. Affiliate/cashback boundaries are experimentally measurable. |
| Malwarebytes Browser Guard | 11,000,000 | https://chromewebstore.google.com/detail/malwarebytes-browser-guar/ihcjicgdanjaechkgeegckofjjedodee | Security/tracker-blocking product with high trust expectations and broad site visibility. |
| LastPass | 8,000,000 | https://chromewebstore.google.com/detail/lastpass-free-password-ma/hdokiejnpimakedhajhdlcegeplioahd | Store panel lists authentication information, location, user activity, and website content. |
| Urban VPN | 7,000,000 | https://chromewebstore.google.com/detail/urban-vpn-proxy/eppiocemhmnlbhjplcgkofciiegomcon | Free VPN/privacy product; connected/disconnected telemetry is directly measurable. |
| 1Password | 7,000,000 | https://chromewebstore.google.com/detail/1password-%E2%80%93-password-mana/aeblfdkhhhdcdjpifhhbdiojplfjncoa | Password manager with extremely sensitive context access; useful for data-minimization tests. |
| Sider | 5,000,000 | https://chromewebstore.google.com/detail/sider-chat-with-all-ai-gp/difoiogjjojoaoomphldepapgpbgkhkb | Store panel lists PII and website content; page-aware AI makes passive-vs-invoked tests straightforward. |
| Hola VPN | 4,000,000 | https://chromewebstore.google.com/detail/hola-vpn-your-website-unb/gkojfkhlekighikafcpjkiklfbnlmeio | Listing says analytics do not collect browsing history or details of websites/services visited, while the store privacy panel separately lists `Web history` among handled categories. This documentary tension requires technical and definitional testing before any conclusion. |
| DeepL | 4,000,000 | https://chromewebstore.google.com/detail/deepl-translate-and-write/cofdbpoegempjloogbagkncekinflcnj | Page-integrated translation/writing assistant; passive-vs-invoked content transmission is testable. |
| ChatGPT | 4,000,000 | https://chromewebstore.google.com/detail/chatgpt/hehggadaopoacecdllhhajmbjkdcmajg | Listing states the browser-control extension asks before sensitive actions such as accessing new sites and referencing browser history; consent boundaries are falsifiable. |
| ChatGPT Search | 4,000,000 | https://chromewebstore.google.com/detail/chatgpt-search/ejcfepkfckglbgocfkanmcdngdijcgld | Changes Chrome's default search engine to ChatGPT Search; lower-privilege navigation/query boundary target. |
| Rakuten | 3,000,000 | https://chromewebstore.google.com/detail/rakuten-get-cash-back-for/chhjbpecpncaggjpdakmflnfcopglcmi | Listing describes one-click cashback activation and explicitly discloses merchant-paid affiliate commissions. |
| Coupert | 3,000,000 | https://chromewebstore.google.com/detail/coupert-automatic-coupon/mfidniedemcgceagapgdekdbmanojomk | Coupon/cashback extension operating in the background; attribution and benefit conditions can be separated experimentally. |
| Merlin AI | 900,000 | https://chromewebstore.google.com/detail/merlin-ai/camppjleccjaphfdbohjdohecfnoikec | Listing states Merlin may receive commissions from companies and/or affiliate programs on sites visited/products purchased while using the extension. Combined with page-aware AI access, this creates two independent test families: attribution and content transmission. |
| MaxAI | 700,000 | https://chromewebstore.google.com/detail/maxai-ask-ai-anything-as/mhnlakgilnojmhinhkckjpncpbhabphi | Page-aware AI sidebar; passive-vs-invoked page-content transmission is measurable. |
| Karma | 500,000 | https://chromewebstore.google.com/detail/karma-online-shopping-but/emalgedpdlghbkikiaeocoblajamonoh | Listing says merchants may pay affiliate commissions, says the extension accesses the current page URL only for supported shopping features, and says it does not collect browsing history. These are unusually specific falsifiable boundaries. |
| RetailMeNot | 500,000 | https://chromewebstore.google.com/detail/retailmenot-codes-cash-ba/jjfblogammkiefalfpafidabbnamoknm | Listing says purchases through RetailMeNot links may generate commission; store panel lists web history and user activity. Attribution/activation behavior is measurable. |
| HARPA AI | 400,000 | https://chromewebstore.google.com/detail/harpa-ai-web-automation-w/eanggfilgoajaocelnaflolkadkeghjp | Page-aware AI automation and price monitoring create clear idle-vs-invoked experiments. |
| Ibotta | 200,000 | https://chromewebstore.google.com/detail/ibotta-price-compare-cash/mfaedmjlefifhnhpgipjjiiekchaimpk | Listing describes cashback as requiring the user to click `Activate`; that creates a precise attribution boundary to test. |

## Snapshot discipline

Before running any experiment, capture the live version of the target's listing and policies again. Store pages, install counts, extension versions, privacy disclosures and policies change. A source in this file should never be treated as proof of what a later version represented.
