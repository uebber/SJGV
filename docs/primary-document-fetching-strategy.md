# Primary-document fetching strategy — 22 August 2026

**Purpose:** record the retrieval method that has actually worked for this
repository, so a fresh context does not rediscover it. Written after a sourcing
pass for the Gate 2 continuous capital-resilience plan reported serious
difficulty locating FY26 annual/interim financial reports.

This is a *retrieval* document. It does not relax the sourcing protocol in
`AGENTS.md` or `data/README.md`: every value still has to be read out of the
document itself, with issuer, title, publication date, reporting date, units,
currency and attribution basis verified inside the file.

## 1. Short answer: yes, it was directly at ASX

The channel that produced most of the accepted primary documents is the ASX's
own research API — the data service behind the exchange's company pages. No
token, no login, no scraping of a rendered page.

```sh
# 1. list a company's recent lodgements
curl -s -H "$UA" \
  'https://asx.api.markitdigital.com/asx-research/1.0/companies/NST/announcements'
#    → data.items[].documentKey, .headline, .date, .announcementType

# 2. download the lodged PDF by documentKey
curl -sL -H "$UA" \
  'https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/2924-03123134-6A1339301' \
  -o /tmp/nst-ar-fy26.pdf
pdftotext -layout /tmp/nst-ar-fy26.pdf -
```

Verified working 22 Aug 2026: the announcements endpoint returns HTTP 200 JSON,
and the CDN gateway returns `application/pdf` for a `documentKey` taken from it.

`tools/asx.py` already uses the same host for share counts and quotes, and
`tools/fetch.py` handles the download/`pdftotext`/cache mechanics with a browser
user-agent.

### 1.1 The complete back catalogue — also directly at ASX

The research API above is capped at 5 items (§2). The exchange's **legacy
statistics endpoint is not**, and it is the single most useful channel in this
document:

```sh
# full calendar-year index for any ticker — listable HTML table
https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode=BGL&timeframe=Y&year=2026

# each row: <td>dd/mm/yyyy<br><span class="dates-time">h:mm am</span></td>
#           <td class="pricesens">…</td>
#           <td><a href="/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId=03128460">Headline</a>
```

`displayAnnouncement.do` returns a terms-and-conditions interstitial, not the
PDF. The real path is in a hidden form field:

```sh
curl -s '…/displayAnnouncement.do?display=pdf&idsId=03128460' \
  | grep -oE 'name="pdfURL" value="[^"]+"'
# → https://announcements.asx.com.au/asxpdf/20260821/pdf/0731zk5sq1cl29.pdf
```

That solves the "needs the exact `{yyyymmdd}/{id}` pair" problem in §4 — the
pair is handed to you rather than guessed.

Verified 22 Aug 2026, HTTP 200 with a full year of rows: BGL 69, OBM 49, PNR 129,
WGX 95 announcements for calendar 2026. Query one `year=` per request.

Note `idsId` is **not** the documentKey middle segment — BGL's 21 Aug AGM notice
is `idsId=03128460` but documentKey `2924-03124400-6A1339712`. They are separate
identifier spaces; don't interconvert them.

Because the index is complete and unfiltered, it can prove a negative. "No
Appendix 4E was lodged in calendar 2026" becomes a checkable claim over all 69
rows, which is exactly what distinguishes *not lodged yet* from *scrolled out of
the window*.

## 2. The trap that makes it look broken

**The announcements endpoint is hard-capped at the 5 most recent items.**
Measured, not assumed — `?pageSize=50`, `?limit=50`, `?page=0&pageSize=200` and
`?itemsPerPage=100` all return exactly 5. There is no pagination parameter and
no `/history` sibling endpoint (404).

During the 18–31 August FY reporting peak, five announcements is roughly **one
day** of lodgements for an active name. A document lodged three days ago is
already invisible. On 22 Aug 2026 the live window shows:

| Ticker | FY26 annual/4E visible in the 5-item window? |
|---|---|
| VAU | yes — `Appendix 4E and Annual Financial Statements`, 20 Aug, `2924-03123712-6A1339495` |
| GMD | yes — `Annual Report to shareholders`, 20 Aug, `2924-03123696-6A1339483` |
| NST | partly — `Appendix 4E - revised`, 20 Aug, `2924-03123773-6A1339504`; the annual report itself has scrolled off |
| RMS, RRL, EVN | no — results announced 20–21 Aug, the financial report has already scrolled off |
| CMM, GGP, WGX, BGL, OBM, CYL, PNR, BC8 | no |

So an agent that only knows channel 1 will succeed on two names, fail on twelve,
and have no way to tell "not lodged yet" apart from "scrolled out of the
window". That is the failure mode to design around, and the most likely
explanation for the difficulty reported in
`docs/gate2-capital-resilience-source-register-2026-08-22.md`.

### 2.1 The cap is defeatable — announcement-number arithmetic

The CDN gateway keys off the **middle segment of the documentKey only**. Verified
on NST 22 Aug 2026: `2924-03123133-6A1339299`, `2924-03123133-6A1339300` and
`2924-03123133-XXXXXXX` all return the same PDF, byte-identical after
`pdftotext`. The trailing segment is decorative.

Middle segments are sequential in lodgement order across the whole market, so a
document that has scrolled out of the 5-item window is reachable by walking the
number around a key you already hold. NST's 20 Aug block recovered this way:

```
03123133  Appendix 4E (original)      ← not in the API window; found by decrementing
03123134  FY26 Annual Report
03123135  Appendix 3A.1
03123136  FY26 results announcement
03123137  FY26 Financial Results Presentation
03123138  FY26 Corporate Governance Statement
03123139  Appendix 4G
03123140  FY26 Modern Slavery Statement
```

Sequence numbers are global, not per-issuer, so neighbouring keys mostly belong
to other companies — **verify the issuer and title inside every PDF you pull
this way.** Used carefully this is the cheapest route to a same-day sibling
document (the 4E next to the annual report, the quarterly next to its
presentation). It is a supplement to channel 2, not a replacement: walking far
enough to reach last quarter's lodgement is not practical.

Second-order point: **not lodged yet is a real answer here.** A 30 June balance
date obliges an Appendix 4E within two months, i.e. by 31 August 2026. On 22
August, several of these names legitimately have no FY26 financial report in
existence. Recording that is a complete, correct result — not a fetch failure.

## 3. Channel order

1. **ASX research API + CDN gateway** (§1). Highest quality — it is the lodged
   document, from the exchange. Use it first, and expect it to cover only the
   last ~5 announcements.
2. **The issuer's own IR platform back catalogue.** Every name uses exactly one,
   and the mapping is already recoverable from the `documents` map in
   `data/companies.json` — see the table in §4. These platforms carry the full
   history, which is precisely what channel 1 lacks.
3. **Issuer website / investor-relations report page.** Reliable, but a
   published annual report can lag the ASX lodgement by days, and by August the
   linked "latest" report is often the prior year. Check the date inside.
4. **Identical-filing mirrors** — `announcements.asx.com.au/asxpdf/`,
   `app.sharelinktechnologies.com`, `yourir.info`, `listcorp.com`,
   `investegate.co.uk` (LSE RNS, for GGP's dual listing). Same PDF, different
   host; acceptable as a primary-equivalent when the issuer link is dead or
   bot-protected.
5. **Search engines for discovery only.** A headline or a documentKey from a
   search result is a lead. The evidence is the downloaded file.

## 4. Per-ticker back-catalogue host

Derived from the URLs already accepted in `data/companies.json`. When channel 1
comes up empty, go straight to the host on this row rather than guessing.

| Ticker | Back-catalogue channel |
|---|---|
| NST | `www.nsrltd.com/media/...` (issuer CDN, direct PDF paths) |
| EVN | `yourir.info/resources/851ef7ffa345f09f/announcements/evn.asx/{2A…}/{Title}.pdf` |
| CMM | `capmetals.com.au/wp-content/uploads/{yyyy}/{mm}/…` and `capmetals.com.au/investors/announcements/` |
| GGP | `investegate.co.uk` (LSE RNS), `app.sharelinktechnologies.com`, `greatland.com.au/investors/reports/` |
| GMD | `GMD.live.irmau.com/pdf/{uuid}/Platform/ListPage/{Title}.pdf`; index at `gmd.live.irmau.com/site/investor-centre/asx-announcements` (HTTP 200, listable) |
| RMS | `RMS.irmau.com/pdf/{uuid}/Platform/ListPage/{Title}.pdf`; same irmau index pattern |
| RRL | `app.sharelinktechnologies.com/announcement/asx/{hash}` |
| WGX | `www.westgold.com.au/pdf/{uuid}/{Title}.pdf`; `company-announcements.afr.com/asx/wgx/{uuid}.pdf` |
| VAU | `announcements.asx.com.au/asxpdf/{yyyymmdd}/pdf/{id}.pdf`; `listcorp.com/asx/vau/...` |
| BGL | `announcements.asx.com.au/asxpdf/...`; `wcsecure.weblink.com.au/clients/bellevuegold/v2/headline.aspx?headlineid=` |
| OBM | `wcsecure.weblink.com.au/clients/orabandamining/headline.aspx?headlineid={id}` — returns the PDF directly |
| CYL | `api.investi.com.au/api/announcements/cyl/{id}.pdf`; **full index** at `api.investi.com.au/api/announcements?apiKey=623c6325-b09e-4ef0-a034-acf207d0df01` |
| PNR | `announcements.asx.com.au/asxpdf/{yyyymmdd}/pdf/{id}.pdf` |
| BC8 | ASX CDN gateway (channel 1) |

**The complete, paginated, unfiltered feed — best general answer to the cap.**
`intelligentinvestor.com.au/shares/asx-{ticker}/{slug}/announcements?page=N`
returns the full ASX feed as server-rendered HTML, ~25 rows per page, including
non-price-sensitive items (Cleansing Notices, Appendix 3B, Director's Interest
notices). Its PDF links are
`aspecthuntley.com.au/asxdata/{yyyymmdd}/pdf/{id}.pdf`, **where `{id}` equals the
middle segment of the ASX documentKey** — the same segment §2.1 shows the CDN
gateway keys off. So this channel both enumerates the back catalogue and hands
back keys usable against the exchange's own CDN.

Verified on CMM 22 Aug 2026: its five most recent rows matched the ASX API
documentKeys exactly, and it gave a contiguous list from 13 Nov 2025 to 21 Aug
2026. Because it is unfiltered it can prove a negative — "nothing was lodged
between 31 July and 21 August except these four items" — which the ASX API
cannot.

**investi issuers (CYL) expose a full JSON index — with the key in plain sight.**
The issuer page loads `api.investi.com.au/investi.js?apiKey={uuid}`; that script
builds `api.investi.com.au/api/announcements?apiKey={uuid}`, which returns the
complete lodgement history as JSON (`date`, `headline`, `priceSensitive`,
`localPath`). CYL: apiKey `623c6325-b09e-4ef0-a034-acf207d0df01`, 514 items from
13 Jan 2020 to 19 Aug 2026. Recover the key by fetching the issuer's investor
page and grepping for `investi.js?apiKey=`. (An earlier draft of this document
said investi had no listable endpoint — it does; the `/list` path is simply the
wrong one.)

**ShareLink issuers (RRL, GGP) need no API at all.**
`app.sharelinktechnologies.com/widget/{widget-uuid}` returns the issuer's
*entire* announcement history inline as HTML table rows — date, headline and the
32-hex hash that forms the document URL — in one request. RRL's widget returned
1,653 items back to 2004 in 793 KB. The widget UUID is in the `src`/`href` of the
issuer's own announcements page (RRL:
`regisresources.com.au/investor-centre/asx-announcements/` → widget
`c837d795-7887-4665-a490-3d1707bd6925`). This is a complete one-shot answer to
the 5-item cap for any ShareLink issuer, and it makes exhaustive negative
searches possible — "no facility amendment was ever lodged" becomes a checkable
claim rather than an assumption.

Probe results, 22 Aug 2026: `announcements.asx.com.au/asxpdf/...` 200
`application/pdf`; `app.sharelinktechnologies.com/announcement/asx/{hash}` 200
`application/pdf`; `yourir.info/...pdf` 200 `application/pdf`;
`wcsecure.weblink.com.au/...headline.aspx?headlineid=` 200 `application/pdf`;
`listcorp.com/asx/{t}/{slug}/news` 200 HTML. The
`announcements.asx.com.au/asxpdf/` path needs the exact `{yyyymmdd}/{id}` pair —
a wrong pairing returns an HTTP 404 wrapped in a 139 KB HTML page, which is easy
to mistake for a successful fetch.

## 5. Mechanics that repeatedly cost time

- **`WebFetch` cannot read PDFs.** It returns the compressed object stream or a
  markdown conversion of nothing. Download with `curl -L`, then
  `pdftotext -layout`. Use `tools/fetch.py`, which does both and caches under
  `.cache/` keyed by URL hash (469 artifacts already there — check before
  re-fetching).
- **Send a browser user-agent.** Several issuer sites return 403 to a default
  one and 200 to Chrome's.
- **Sniff the bytes, not the status.** A 200 with `Content-Type: text/html` and
  ~100 KB where a PDF was expected is an error page. Check for the `%PDF` magic
  number.
- **Big financial reports need a page-targeted read.** An FY26 annual report is
  150–250 pages; `pdftotext -layout` output is thousands of lines. Grep for the
  note headings rather than reading linearly: `Contractual maturit`,
  `maturity analysis`, `Commitments`, `Capital commitments`, `Cash and cash
  equivalents`, `Borrowings`, `Lease liabilities`, `undrawn`.
- **URL vintage lies.** Ora Banda's "2026" URL served the FY25 statement. The
  date inside the document is the only date that counts.
- **Keep downloads in `/tmp`.** PDFs are audit material and are not committed.

## 6. What is being fetched, and why

The superseded continuous Gate 2 design targeted, for every producer-path
candidate, a **latest primary annual or interim financial report** containing
all three of:

1. the balance sheet — unrestricted cash and liquid bullion at a stated date;
2. the financial-liability **contractual maturity note** — undiscounted
   principal *and* contractual interest on borrowings, leases and asset finance,
   in timing buckets; and
3. the **capital commitments note** — contracted capital, with timing, and
   enough detail to reconcile against sustaining capital already inside AISC.

A quarterly activities report and Appendix 5B does **not** carry notes 2 or 3.
That is the structural reason the audit stalled, not a retrieval failure — and
it is why the collection target is the annual/interim report specifically.

Facility terms (amount, committed status, draw conditions, covenants, term date)
are a financing-split diagnostic only and may come from the borrowings note or a
separate executed-facility announcement.

The replacement Gate 2 plan no longer requires complete maturity and
commitment schedules. These documents remain useful for sourcing net debt,
known obligations and explicit conservative bounds; their absence no longer
triggers an attempt to manufacture a complete two-year cash-flow path.

## 7. Standing collection targets

| Ticker | Held | Still required |
|---|---|---|
| NST | FY26 annual report (20 Aug) inspected | revised Appendix 4E of 20 Aug — check what it revises |
| EVN | FY26 financial report (20 Aug) inspected | — (reconciliation, not retrieval) |
| RMS | FY26 annual financial report (21 Aug) inspected | maturity-note totals do not reconcile; restricted-cash split |
| GMD | FY26 annual report identified, download interrupted | retry via ASX CDN `2924-03123696-6A1339483` |
| VAU | FY25 annual, FY26 June quarterly | FY26 Appendix 4E + annual financial statements, 20 Aug |
| RRL | FY25 annual, FY26 June quarterly | FY26 Appendix 4E / annual financial report |
| CMM | FY26 June quarterly only | FY26 annual financial report — may not be lodged yet |
| GGP | FY25 annual, FY26 June quarterly | FY26 annual financial report — may not be lodged yet |
| WGX | March 2026 quarterly only | June 2026 quarterly **and** FY26 annual financial report |
| BGL | FY26 half-year (Dec 2025), June quarterly | FY26 annual financial report |
| OBM | FY26 June quarterly, Diggers presentation | FY26 annual/interim financial report |
| CYL | Dec 2025 half-year, Aug 2026 RCF announcement | FY26 annual financial report |
| PNR | FY25 annual, FY27 guidance | FY26 annual financial report |
| BC8 | FY26 June quarterly | FY26 annual financial report; no AISC history |

"May not be lodged yet" is a finding to confirm, not an assumption to carry.
