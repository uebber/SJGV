# Sourcing Log — 17 August 2026

Full URLs live in `companies.json` under each record's `documents` map. This file
records the **narrative**: what was checked, what conflicted, how conflicts were
resolved, and what remains open.

---

## 1. Corrections to prior working assumptions

Four things the index was carrying that turned out to be wrong.

### 1.1 Astral Resources is not funded — and the error came from a conflated source

**Prior position (13 Aug working note):** Astral was the one developer clearly
passing the funding gate — "fully funded to first gold in the June quarter of
2027 following a A$193m equity raising and US$120m bond financing, with all
regulatory approvals received."

**What Astral actually discloses**, at its own Diggers & Dealers presentation
(4 Aug 2026): DFS **delayed to the March quarter of 2027** on split tenure rights
and consent requirements tied to the underlying tenement owner; pre-production
capital revised **up to ~A$227m** on WA construction cost inflation; cash
**~A$65m** plus a **~A$50m** MMS joint-venture commitment at Feysville. That is
~A$115m of visibility against ~A$227m of capex — a **~A$112m gap**, or 34–43% of
a market cap variously quoted at A$261–333m.

**Verdict: fails D2 (land access) and D3 (bounded dilution ≤30%).** Excluded.

**Root cause.** The A$193m-equity/US$120m-bond description matches **Rox
Resources**, not Astral: A$200m placement plus an upsized A$18m SPP, A$350m of
debt facilities documented, all approvals received, first gold mid-2027. A trade
press round-up appears to have merged the two developers into one paragraph.
This is why the protocol in `README.md` now requires primary-before-secondary and
forbids reconciling conflicting sources by averaging.

### 1.2 Rox Resources is the developer that passes — and was misclassified

Held as `near_producer` on the assumption it was already in production. It is
pre-first-pour. Reclassified to `developer`, and it is the **only name in the
universe passing all three developer tests**:

- **D1** DFS completed November 2025 (requirement is PFS minimum)
- **D2** Final regulatory approval received; plant construction and underground development commenced
- **D3** Funding gap zero — A$200m + A$18m equity raised, A$350m debt documented, A$152.7m cash at 30 June 2026

It also holds **bought put options over roughly half of ramp-up production**.
Per §6.2 that earns no credit — a bought position scores the same as no position
at all. It is recorded at zero because nothing is *sold*, not because the puts
are rewarded.

### 1.3 Northern Star's ounce base is far larger than carried

Carried at 20 Moz P&P with no resource figure. The 3 June 2026 statement (as at
31 March 2026, reaffirmed at Diggers to 2 August) reports **28.4 Moz reserves and
88.9 Moz resources**, with a full Measured/Indicated/Inferred table. Hemi enters
for the first time at 13.198 Moz MR / 5.508 Moz OR. Pogo grew to 9.3 Moz MR /
2.4 Moz OR.

This matters beyond the number: NST was previously being **penalised by missing
data** in the weighting formula, because confidence-weighted ounces sits in the
numerator and an absent resource figure scored as zero resources.

### 1.4 Greatland's reserves were restated — up 62%

Carried at 3.1 Moz pending restatement. The March 2026 Group Ore Reserve
Statement puts reserves at **5.0 Moz** (Telfer 1.8 Moz including a maiden Main
Dome underground reserve of 200 koz, Havieron 3.3 Moz).

---

## 2. Reserve price assumptions — the Channel 2a harvest

Sourced for 11 of 17. This is the field the methodology treats as the sharpest
edge available, and the cross-section justifies that.

| Ticker | Deck A$/oz | Spot multiple | Basis |
|---|---|---|---|
| CMM | 2,400 | **2.57×** | Disclosed range A$2,200–2,600, midpoint |
| BC8 | 2,500 | 2.47× | Paulsens modifying factors |
| BGL | 2,750 | 2.24× | Cut-off grade basis, up from A$1,750 in 2022 |
| NST | 2,900 | 2.13× | AU assets. US assets at US$1,900 |
| AUC | 3,000 | 2.06× | June 2025 DFS constraint |
| GGP | 3,030 | 2.04× | Derived: Telfer A$4,000 (1.8 Moz), Havieron A$2,500 (3.3 Moz) |
| RRL | 3,500 | 1.76× | UG feasibility. McPhillamys PFS at A$4,000 |
| WGX | 3,800 | 1.62× | Stated maximum for reserves and cut-offs |
| RXL | 5,200 | 1.19× | DFS, set 16% below Oct 2025 spot average |
| VAU | 5,546 | 1.11× | Spot at 10 Sep 2025 for unhedged ounces |

Against spot of A$6,170/oz. **A 2.3× spread across the cross-section.** Capricorn
books reserves at ~39% of spot; Vault at ~90%. Same commodity, same country,
same quarter — the entire difference is accounting conservatism, and it is
precisely the unbooked optionality Channel 2a exists to capture.

Note: Genesis discloses A$2,500–3,500/oz as a **resource** guideline, not a
reserve deck. Excluded from the table rather than misused.

**Unsourced:** EVN, RMS, GMD, CYL, PNR, OBM. All are disclosed in the respective
annual statements — this is a PDF-reading task, not a data availability problem.

---

## 3. Hedge books

| Ticker | Position | Treatment |
|---|---|---|
| WGX | Fully unhedged, confirmed | 0.0 |
| CMM | No hedging, explicit | 0.0 |
| RRL | 100% unhedged | 0.0 |
| GGP | No forwards; **bought puts at US$4,200 CY26** | 0.0, scores positive |
| RXL | No forwards; **bought puts over ~half of ramp-up** | 0.0, scores positive |
| VAU | Nominal | 0.03 |
| CYL | **30,000 oz sold at A$6,075/oz**, 15 months from Aug 2026 | 0.15 |
| BGL | **68.7 koz**, cut 83.4 koz during FY26; no mandatory delivery to end-FY27 | 0.24 |

Unsourced: NST, EVN, RMS, GMD, OBM, PNR, BC8, AAR, AUC.

The distinction the methodology draws is doing real work here, though **not** in
the direction an earlier draft claimed. Greatland and Rox both hold options over
gold; both are recorded at **zero sold production** and are therefore neither
penalised nor rewarded — per §6.2 a bought position earns no credit. Catalyst and
Bellevue have sold forward and are penalised. A framework that lumped
"derivatives" together would get all four wrong, by inventing a penalty on the
two that bought protection.

---

## 4. Conflicts left unresolved

**Ausgold share count.** ADVFN reports 2,296,141,208 shares and a A$2.34bn market
cap; Stockopedia A$460m; stockanalysis A$591m; TradingView A$381m at A$0.880.
The ADVFN share count is internally inconsistent with every quoted cap and looks
like a stale pre-consolidation figure. Quoted caps imply roughly 450–650m shares.
**Field omitted** rather than guessed.

**Astral share count.** ADVFN 1,801,045,606 for A$333m; Australian Stock Report
1.45bn for A$255m. Unreconciled. **Field omitted.** Moot for now — AAR fails the
developer gate on fundamentals.

**Regis placement.** One source reports Regis planning to issue up to 732 million
new ordinary shares around 10 September 2026. Against 757m on issue that is a
~97% increase. It is almost certainly stale — it relates to the scrip
consideration for the **terminated** Vault merger. Flagged in `companies.json`
as requiring verification before any rebalance. Not applied.

**Capricorn resources.** Reserves are sourced at 5.24 Moz (August 2026) but the
last sourced resource figure is 6.6 Moz (May 2026). A 79% reserve-to-resource
ratio is implausible and implies the MRE also grew. `mr_total_moz` omitted.

**Pantoro reserves.** Sources give 859 koz and 949–958 koz depending on vintage.
Conservative figure used; updated statement due in the September 2026 quarter.

---

## 4a. Second sourcing pass — resource splits read from source

The first pass imputed the M&I/Inferred split for 13 of 17 names. That was not
acceptable: the term sits in the numerator of the weighting formula, so an
estimate there moves weights directly. A second pass went to the primary
statements.

**Result: splits now sourced for 11 of 17, and for 9 of the 10 names carrying
weight.** Only OBM among weighted names remains imputed.

| Ticker | P&P (Moz) | M&I non-reserve (Moz) | Inferred (Moz) | Source shape |
|---|---|---|---|---|
| NST | 28.419 | 24.770 | 35.683 | PDF |
| EVN | 12.0 | 11.3 | 8.1 | inline HTML |
| GGP | 5.0 | 3.16 | 6.8 | **page images** |
| GMD | 4.2 | 8.845 | 5.5 | inline HTML |
| RMS | 4.2 | 4.64 | 3.2 | PDF |
| RRL | 3.855 | 2.715 | 1.70 | PDF |
| WGX | 3.5 | 5.7 | 7.1 | PDF |
| VAU | 3.608 | 4.990 | 3.634 | listcorp mirror |
| BGL | 1.29 | 0.71 | 1.1 | HTML table |
| AUC | 1.33 | 0.890 | 0.220 | stated 91% M&I |

### Corrections this pass produced

- **VAU eligible ounce share 1.0 → 0.929.** Sugar Zone (Ontario) carries no *reserve*, which is why it was recorded as fully eligible — but it holds 789 koz M&I and 440 koz Inferred. Ineligible ounces were being counted as eligible.
- **VAU reserve deck A$5,546 → A$4,500.** The A$5,546 figure was spot at 10 Sep 2025, quoted in the statement as pricing *context* for hedged versus unhedged ounces. The actual 30 June 2025 ORE deck is A$4,500/oz, up from A$3,500 the prior year. This materially changes VAU's Channel 2a score.
- **NST eligible ounce share 0.901 → 0.910**, now computed from Pogo's own disclosed split rather than by assuming it mirrored the group.
- **EVN eligible ounce share 0.818 → 0.801**, from Red Lake's own tables.
- **BGL reserves 1.34 → 1.29 Moz**, all Probable.
- **RRL reserves 3.89 → 3.855 Moz** (1.965 group + 1.89 McPhillamys).
- **GMD reserves 4.4 → 4.2 Moz.** The R&R page headline says 4.4; its own table sums to 4.2. Table taken as primary.
- **RRL reserve deck**: two decks, not one — Regis-managed at A$3,500/oz ORE, Tropicana JV (set by AngloGold) at US$1,700/oz (A$2,576). Recorded with both.
- **OBM reserve decks** recovered from the FY25 statement: A$2,500/oz Sand King and Riverina UG, A$2,400 Waihi OP, A$4,400 UG low grade and stockpiles.

### The imputation itself was biased, and the bias was structural

The 58%/42% default came from a two-point calibration on NST (59.8%) and WGX
(56.4%). With nine observations the median is **69.0%** and the range is
54.8–79.3% — NST and WGX sit at the *bottom*, because they hold the two largest
resource bases and resource maturity runs inversely to size in this cohort.

Understatement of M&I non-reserve ounces per name: RRL 65%, EVN 47%, RMS 40%,
VAU 38%, BGL 35%, GMD 26%. Every affected name was underweighted.

Default recalibrated to **69/31** for producers. The general lesson is recorded
in `README.md`: below five observations, reject rather than impute.

---

## 4b. Third sourcing pass — the six rejected names, 17 August 2026

Six parallel research agents, one per ticker, used the source protocol now
consolidated in `data/README.md` and `docs/primary-source-operations.md`.
Agents proposed JSON only; every value was merged, arbitrated and written here.
**All six M/I/Inferred splits are now sourced**, which is what §12's DERIVE OR FAIL
rejection was waiting on. The book went 9 → 12 constituents, Eff N 8.4 → 10.5, and
the developer sleeve exists again at 5.0%.

### Channels discovered — these defeat the 5-item ASX feed cap

The ASX announcements feed returns only ~5 recent items, which is why the back
catalogue had never been reachable. Two routes around it were found independently:

1. **investi.com.au archive.** Many issuer announcement pages are an investi JS
   widget. The API key sits in `https://api.investi.com.au/investi.js` or in the
   page's `investi.js?apiKey=` reference. Then
   `GET https://api.investi.com.au/api/announcements?apiKey=<key>` returns the
   **full lodged archive** as JSON with PDF paths — 689 items for RXL, 513 for CYL.
   Direct `/api/announcements/<tick>/<hash>.pdf` paths 403 unless resolved through
   the listing route first. Keys: RXL `306618af-fd8b-4b86-926b-869e9857531d`,
   CYL `623c6325-b09e-4ef0-a034-acf207d0df01`.
2. **weblink `admin-ajax`.** For weblink-hosted issuers,
   `POST https://<issuer>/wp-admin/admin-ajax.php` with
   `action=filter_weblink_downloads&year=2026&cat=0&limit=50&paged=1` returns the
   full year's list with `wcsecure.weblink.com.au/...headline.aspx?headlineid=N`
   links that serve the lodged PDF directly. This found OBM's real R&R statement,
   which **is not on the issuer's own website at all**.

Dead ends worth not repeating: `astralresources.com.au` returns HTTP 429, but it
is a **Vercel bot challenge, not a rate limit** — backoff will never clear it.
`asx.api` pagination parameters (`count`, `limit`, `pageSize`, `itemsPerPage`) are
all silently ignored. `bc8.com.au/resources-and-reserves/` now 404s. Sequential
URL-ID sweeping of listcorp returns nothing and wastes wall-clock.

### The two findings that moved the index

**OBM `committed_capex_aud_m` 233 → 455. Ora Banda now FAILS Gate 2 by A$212m.**
The recorded A$233m was the GR Engineering **EPC contract sum** — a line item
inside the A$375m the Board approved on 18 May 2026 (A$233m EPC + A$142m
supporting infrastructure and contingency), with a further A$90m approved for
Waihi Underground. The A$455m is the issuer's own FY27/FY28 phasing of the
board-approved lines only. It fails on every reading tested: A$465m (no
apportionment), A$375m (mill only), A$280m, even A$273m. The tipping point is
~A$243m. **This retires the "Ora Banda problem" of §4.** It was never a scoring
problem that Gate 2 was failing to catch — the gate was being fed an understated
input, and the A$10m survival margin was an artefact of charging one line item
instead of the build. The name is now excluded on the merits.

**AAR `remaining_capex_aud_m` 112 → 162. D3 fails at 60% of market cap, not 38%.**
The A$50m "MMS JV commitment" netted off the funding gap does not exist in any
lodged document. What the quarterly describes is MMS funding 100% of **Think Big's
own** development costs — a ~32,000 oz deposit — recovering them from initial
cash flow and then taking 30–50% of profits. It is also still only a Letter of
Intent nine months on. An unsourced credit running in the name's favour was
removed. The verdict was already FAIL; the margin is roughly double what was
recorded.

### Corrections that did not move the index but were wrong

| Ticker | Field | Was | Now | Why it mattered |
|---|---|---|---|---|
| CYL | `mr_total_moz` | 3.6 | **4.24** | 18% low. Traced to the stale pre-Sept-2025 table on the issuer's R&R page, sitting alongside a current attributable summary — the mixed-vintage trap. |
| RXL | `reserve_price_aud` | 5,200 | **3,200** | A$5,200 is the DFS *financial evaluation* base case. The JORC Table 1 reserve deck is A$3,200, stated four times. Channel 2a goes 1.19× → 1.93×. |
| BC8 | `pp_moz` | 0.243 | **0.330** | Kal East alone. Paulsens *is* separately disclosed at 87 koz. Coyote genuinely has no reserve — pre-PFS. |
| BC8 | `production_koz_yr` | 50 | **66.3** | Both prior figures wrong in different directions: 50 koz was a CY26 aggregator target; the 91 koz headline includes 24,537 oz of third-party toll ore under an arrangement that **ended** in the March quarter. |
| CYL | `aisc_aud_oz` | 2,666 | **2,738** | 2,666 was a single quarter on ounces *produced*. |
| CYL | `net_debt_aud_m` | −323 | **−331** | −323 was a pre-close cover-panel figure. |
| OBM | `pp_moz`/`mr_total_moz` docs | mis-cited | repointed | Both `rr2026` and `rr2025` pointed at the **same URL**, which serves the FY25 statement (2.11 Moz / 236 koz). The values were right; the citation was broken. The `/2026/03/` path is a re-upload date. |
| AAR | doc `pfs` | typed `primary` | **retired** | It is a proactiveinvestors article mis-typed as primary, backing four fields including two GATE inputs. It was inflating the primary share in `tools/provenance.py`. |

### Issuer defects found — read before trusting any summary table

- **CYL publishes two different Indicated totals for the same 30 June 2025
  estimate.** The 10 Sep 2025 announcement says 3,647 koz; the FY25 Annual Report
  says 3,475 koz. The gap is one cell — the announcement's "Plutonic Belt Open
  Pit" row reads Indicated 634 + Inferred 219 but Total 679. Confirmed by visual
  read, not an extraction artefact, and it propagates into the August 2026
  investor deck. Taking either would overstate M&I non-reserve ounces by 9%.
- **RXL's DFS misprints its own resource total row**, carrying the superseded
  January 2024 Indicated figure (1,561 koz) into the July 2025 table. It fails
  three internal checks; the MRE and annual report both print 1,546 koz.
- **PNR's website is a full year stale.** The image tables at
  `pantoro.com.au/resources-reserves` are the 26 Sep 2024 vintage — reading the
  split off them gives 1.511 / 2.302 Moz, both wrong by a year.
- **AAR's Inferred total grade cell** reads 1.2 g/t where the tonnes and ounces
  imply 0.98 g/t. Ounces are right; the grade cell is a typo carried through two
  lodged documents.

### Values deliberately NOT filled

- **BC8 `aisc_aud_oz`** — confirmed still unpublished at 17 Aug 2026. The June
  quarterly restates the refusal more explicitly than December's. Operating costs
  give ~A$2,706/oz on own ounces or ~A$1,975/oz on total — a 37% spread on
  denominator choice alone, and both exclude sustaining capital and corporate.
  Per-project *study* AISC of A$1,613–1,882/oz exist in the FY24 annual report but
  are 2022–24 estimates struck at A$3,500/oz gold. BC8 stays blocked.
- **PNR `reserve_price_aud`** — the 22 Sep 2025 statement could not be obtained
  through any channel, and every document restating its tables omits the revenue
  factor. The prior-vintage 2024 statement says A$2,600/oz; **not carried
  forward**, since it predates a ~A$2,000/oz move in spot.
- **OBM and CYL `resource_price_aud`** — neither issuer publishes a single group
  figure, and the deposit-level weights needed to construct one are not disclosed.
- **BC8 `committed_capex_aud_m`** — the Lakewood expansion has long-lead items
  ordered but no dollar amount and timing conditional on ramp-up.

### One ambiguity escalated rather than decided

**OBM `reserve_price_aud`.** The 1 Apr 2026 statement uses four constraint prices
(underground A$2,500 covering 53% of reserve ounces, Waihi open pit A$2,400, Round
Dam open pit A$3,600 covering 37%, low-grade A$3,400–5,000) *and* states for every
mine that the economics were run at a single A$3,600/oz financial-evaluation
price. If the field means the price the estimate was **constrained** at, A$2,500
is right for the underground; if it means the price the reserve was **justified**
at, A$3,600 is the statement-wide answer and runs against the name. A$2,500 is
retained. Immaterial while OBM fails Gate 2 — but decide before it is re-admitted.

---

## 4c. Fourth sourcing pass — the weighted gate inputs, 17 August 2026

Seven parallel agents, one per weighted name, re-sourcing the 29 gate inputs that
`tools/provenance.py` flagged as decided on aggregators. **All 29 are now primary.
The layer went from 70.6% to 99.6% primary-sourced, and non-primary gate inputs on
weighted names went from 29 to zero.**

No constituent entered or left. That is the correct outcome for a provenance pass —
but four of the seven names carried a value that was simply *wrong*, and two of
those errors were in the data layer's own transcription rather than in the source.

### Four more archive channels

Wave 1 found two. This pass found four more, and between them they cover every
issuer in the book. **The ASX feed's 5-item cap is no longer a constraint on
anything.**

| Channel | Pattern | Found for |
|---|---|---|
| **Umbraco media API** | `nsrltd.com/umbraco/api/media/getmedia/?q=&year=2026&type=&skip=0`, endpoint in `/dist/js/main.min.js` | NST — 83 items for 2026 |
| **ShareLink** | `app.sharelinktechnologies.com/announcement/asx/{id}`, widget id in the page | RRL — 1,653 items back to 2004 |
| **IRM** | `{TICK}.live.irmau.com/ShowListPageXml.aspx?CategoryID=8&ArchiveYear=2026&Page=N` | GMD |
| **yourir.info API v5** | `yourir.info/api/v5/symbols/{sym}.asx/announcements?appID=…`, appID in the page's loader script | EVN |

Neither the investi nor the weblink route applies to CMM (`admin-ajax` returns 400,
and the investi key on the page is a Turnstile site key, not an API key). CMM's
own site with a browser UA was sufficient.

### The four value errors

**GGP `production_koz_yr` 310 → 329.** The recorded figure was the *top of the FY26
guidance range* entered as though it were the outcome — the note even read "FY26
beat guidance of 260–310 koz". Actual production was 328,987 oz. The secondary
source had reported it correctly; the error was ours.

**GGP `undrawn_facilities_aud_m` 500 → 475.** A$500m is the total package. Only the
A$475m of revolving credit is undrawn drawable cash; the remaining A$25m contingent
instrument facility is drawn to A$9m and exists to issue bank guarantees. The
issuer's own liquidity arithmetic settles it — 1,289 + 475 = A$1,764m. Again the
secondary source was right and the entry was wrong. **This one ran in the name's
favour and overstated Gate 2 liquidity by A$26m.**

**VAU `committed_capex_aud_m` 53 → 173.** Vault *does* publish a consolidated FY27
growth capital figure, in Table 3 of the lodged quarterly, and the site columns
foot to it exactly (62 + 10 + 5 + 96). The A$53m was reconstructed from a
trade-press summary by excluding Deflector and Mount Monger as "largely captured
in AISC" — the company states the opposite: *"AISC excludes capital expenditure for
mine development, services and mining fleet"*. The A$48m the earlier pass excluded
was not even a Deflector programme; it is the group FY26 quarterly growth spend.

**GMD `undrawn_facilities_aud_m` 300 → 100, and `net_debt_aud_m` −155 → −320.1.**
The A$300m was the *size* of the facility, not the undrawn balance: Genesis upsized
it to A$300m and drew A$200m in the same quarter to fund the Magnetic cash
consideration. That same A$200m is the bank debt — so the pair counted it once as
available headroom and never against. The net debt figure it sat beside was the
last surviving **forbidden estimate** in the layer ("A$600m at 31 Mar less ~A$445m
Magnetic cash component"); it is now the company's stated A$320.1m net cash.

### Six period-basis errors — all the same shape

Every one of these was a **single quarter or a part-year recorded as a full year**.
It is the most common defect in the layer and it is worth naming as a class.

| | Was | Is | What the recorded figure actually was |
|---|---|---|---|
| NST `aisc_aud_oz` | 2,651 | **2,698** | June quarter only |
| RRL `aisc_aud_oz` | 2,850 | **2,945** | H1 FY26 only |
| GGP `aisc_aud_oz` | 2,056 | **2,179** | March quarter only |
| CMM `aisc_aud_oz` | 1,623 | **1,629** | 9-month FY26 YTD |
| CYL `aisc_aud_oz` *(wave 1)* | 2,666 | **2,738** | June quarter, per oz produced |
| EVN `aisc_aud_oz` | 1,700 | **1,717** | guidance midpoint, not actual |

Five of the six ran **against** the recorded value, i.e. the layer was understating
the Gate 2 cost base on five of twelve constituents at once.

### Three reserve decks corrected on the same principle

`reserve_price_aud` is supposed to be the price the estimate was *constrained* at.
Where an issuer publishes several decks and discloses the ounce split, the right
answer is an ounce-weighted blend — the convention GGP's record already used
(Telfer A$4,000 / Havieron A$2,500 → A$3,030). Three names were not following it:

- **RRL 3,500 → 2,769.** A$3,500 covered Duketon's 1,389 koz, 36% of the base.
  Adding McPhillamys — optimised at **A$2,290/oz** — took the reserve to 3,855 koz,
  with Tropicana at A$2,576. *Runs in the name's favour; made deliberately.*
- **CMM 2,400 → 2,394.** Value barely moves, but the note claimed the per-pit ounce
  split was undisclosed. **It is disclosed, on pages 15–16 of the statement already
  cited.** So the figure stops being a *constructed midpoint*, which DERIVE OR FAIL
  forbids, and becomes a *derived weighted average*, which it permits.
- **GGP `resource_price_aud` 4,200 → 3,336.** Telfer-only, where Havieron is 7.0 of
  the 14.9 Moz group resource.

Two decks were sourced for the first time — **GMD A$2,800** (uniform across every
deposit, one of the lowest in the universe) and **EVN A$3,000** — turning Channel 2a
on for both. GMD's convexity rose 1.60 → 1.72 as a result.

### Hedge books: two zeros were wrong, and one was wrong about the currency

- **NST `hedge_share_fwd24m` absent → 0.255.** The largest position in the index had
  been scoring an unpenalised zero on §6 purity while carrying 787,500 hedged oz,
  every one inside the 24-month window. The book is in run-off at an average
  A$3,397/oz against a Q4 realised A$5,041/oz. NST's purity falls 0.95 → 1.00 on the
  revenue term but the hedge penalty now bites; net weight effect −1.9pp.
- **GMD 0.0 → 0.0079.** A single 4,500 oz zero-cost-collar line. Trivial in size, but
  a zero is the *favourable* value, so the correction runs against the name.
- **GGP's note said the puts were struck at US$4,200. They are A$4,200.** Sanity
  check: FY26 realised gold was A$6,223/oz, so an A$4,200 strike is deep out of the
  money — cheap insurance, as described. US$4,200 would be ≈A$6,400, near the money,
  which contradicts "partial downside protection". The bought-put structure was
  verified three ways, including that **the premium is booked as a cash outflow** —
  a forward sale carries no premium. That test is now the standard check.

### EVN: the knife edge is gone, but read how

The standing instruction was to re-run EVN after FY27 guidance on 19 August. **It has
not landed** — the most recent lodgement is 6 August, and the Appendix 4E, FY26
report and FY27 guidance all arrive pre-opening on **19 August 2026**. The instruction
stands. What changed anyway:

- **`gold_nav_share` 0.76 → 0.78**, from the issuer's own FY26 revenue pie,
  reconciled independently from the quarterly's sales table to 0.7795. **EVN has 3pp
  of headroom against the purity floor, not 1pp.**
- **The claim that Carnaby breaches the floor is wrong by about 2pp and is
  withdrawn.** Carnaby holders will own ~0.9% of Evolution. Attributing *all* of its
  value to copper gives 0.773 against a 0.75 floor. Greater Duchess is pre-production
  at PFS with no FID, so it contributes nothing to committed capex either.
- **`undrawn_facilities_aud_m` 0 → 525**, the largest single change in this pass.
- Gate 2 ending liquidity goes **+A$17m → +A$418m**. But `ending_strict` is −A$107m,
  so **`survives_on_cash_alone` flips to false**: EVN now survives *only* by drawing
  the revolver, and that facility is disclosed as "available until 2028" — at or just
  inside the horizon. Break-even committed capex is ~A$1,628m, so at the company's own
  A$1,800m two-year run-rate **EVN still fails**. The capex-basis question still
  decides this name; it now decides it at A$1,628m rather than A$1,193m.

### Two corporate actions, both further away than recorded

**The ACCC has not been notified of the Genesis/Vault merger.** A party search of the
acquisitions register returns only the *dead Regis* matter (MN-65020, "Assessment
ceased"). Under the mandatory regime in force since 1 January 2026 an entry appears
within one business day of notification, so as at 17 August the transaction had not
been notified — 34 days after the SID. Phase 1 runs 30 business days from effective
notification, so the earliest determination is early October and a Phase 2 referral
pushes well past the November target. The parties built a three-month ACCC buffer into
the End Date themselves (14 Jan 2027, extending to 14 Apr 2027). **No event-driven
index action is triggered and the November target looks optimistic.**

**RRL's McPhillamys flag needed rewriting in both halves.** Judgment is still reserved
eight months after the December 2025 hearing — the complete 1,653-item archive to
12 August contains no judgment, and one would be immediately disclosable. But it is
**no longer a binary on the 1.89 Moz**: the June 2026 PFS reinstated the reserve on an
Integrated Waste Landform *"located entirely within land owned by Regis and does not
encroach on the Section 10 declared area"*. The reserve stands whichever way the court
rules; a win is upside, not a precondition. Separately, the **~732m share placement
flag is dead** — the Vault scheme was terminated and the Appendix 3B formally
cancelled on 30 July.

### Open question left for the committee, not resolved here

**Period basis.** `committed_capex_aud_m` is an **FY27** figure for RRL, VAU, CMM, GMD
and NST, while `aisc_aud_oz` and `production_koz_yr` are **FY26 actuals** across the
whole cohort. Gate 2 subtracts capex from free cash flow computed off production and
AISC, so the two legs are on different years. Four agents flagged it independently.

FY26 actuals were kept, because cross-ticker comparability matters more than
within-ticker period alignment and switching one name would be worse than switching
none. Two mitigants: `config.gate2.cost_inflation_pa` already escalates AISC at 5%/yr
over the horizon, and the direction is not uniform — VAU's FY27 AISC is A$326/oz worse
but its FY27 production is 28 koz higher. **This is a methodology decision, not a
sourcing one.** The cleanest resolution is to re-run the whole cohort on FY27 guidance
once every name has published it, which for most of them is within the next fortnight.

**PARTLY ADDRESSED 19 Aug 2026 — methodology §3.2, and it cost a constituent.** The
open question above is about which *year* the two legs are drawn from. Underneath it
sat a second question nobody had asked: whether a capex figure covers the *window* it
is charged against. It often does not. `committed_capex_aud_m` now carries
`horizon_years`, and seven constituents turn out to charge one guided year against the
two-year stress window — RRL, VAU, CMM, NST, PNR, CYL and BGL — while WGX's record
establishes no period at all. GGP and EVN run past the window and over-charge, which is
safe; an earlier capital inventory generalised from those two to "direction is
safe" and that conclusion was withdrawn. The shortfall is **printed, not filled**:
annualising a guided year is forbidden above, and a cohort rate on an unguided period is
the same invention in a peer group's clothes.

**PNR is the name where the period question was never academic**, and it is the one
constituent whose AISC and production are FY27 *guidance* rather than FY26 actuals — so
it was period-aligned with its own capex and imprecise instead. Both legs were recorded
at the midpoint of the issuer's published range. Gate 2 passed at A$3,100/oz and failed
at A$3,400/oz, the top of the same guidance sentence. Under §3.2 that is UNRESOLVED, and
PNR is rejected: **10.00pp of one-way turnover, headline A$662 → A$739/oz.** The four
other names carrying a published capex range — RRL, NST, CMM and GGP — are invariant
across theirs, CMM including its disclosed ±25% no-contingency band.

### Values still deliberately absent

- **WGX `committed_capex_aud_m`** — `UNRESOLVED` after the 21 August refresh.
  The former A$145m covers a stage now under review and omits larger uncosted
  Higginsville and Murchison scopes; retaining it would preserve a favourable
  lower bound. The next primary trigger is the early-September Strategic Outlook.
- **PNR and RMS `reserve_price_aud`** — Channel 2a scores nothing for either.
- **NST `net_debt_aud_m` on a fully-loaded basis.** Recorded at −364 on NST's *own*
  definition, which excludes A$520.2m of secured asset financing and A$390.9m of
  lease liabilities. **On a fully-loaded basis the sign flips to roughly +A$547m of
  net debt.** Immaterial — the whole spread is 2.8% of a A$32bn EV — but it is the
  one place in the layer where a definitional choice changes a sign, and the audited
  figure lands 20 August.

## 4d. Fifth pass — constraint inputs, 17 August 2026 (evening)

Two §9.1/§4.3 constraints were wired that had been declared in `config.json` and
read by no code. Wiring them exposed that neither had an input in the data layer,
which is the reason they could not have been enforced even if someone had noticed.

**`advt_shares_m` — sourced for all 17, same channel as the share counts.**
`asx.api.markitdigital.com/asx-research/1.0/companies/{T}/key-statistics` returns
`volumeAverage`, the exchange's own average daily volume in shares. The averaging
window is undocumented, so it was measured rather than assumed: `volumeAverage ×
90` is an exact integer on every ticker tested (NST, WGX, PNR, RXL), which makes
it a **90-session mean** — the same quarter §4 already uses for the spread. It is
written by `tools/asx.py --write` alongside the share count so both come from one
feed at one instant, and priced at the build-time market price rather than the
API's stale close.

The capacity number this produced is not the one §4.3 assumed. Measured ceiling
**A$21m**, against a judgement estimate of A$50–100m, and the binding name is the
*developer* rather than the small-cap producer tail: RXL at 5.0% of the book
trades A$1.1m a day. Drop the developer sleeve and capacity is A$82m, bound by
PNR. §4.3 has been rewritten around the measurement.

**`single_asset_shares` — sourced for none, and deliberately not attempted.**
The cap it feeds provably cannot bind on a single-asset company while the 15%
name cap sits below the 20% asset cap; it binds only on an asset two constituents
*share*, and no pair here does. `tools/gaps.py` reports it as disclosure-only for
that reason. The work is worth doing for §15 — four constituents are single-asset
— but it is a disclosure job and should be ranked as one, not as a blocked
constraint.

Also on this pass: `tools/asx.py` no longer rewrites a field with its own value.
Seventeen unchanged share counts were previously re-emitted with a fresh note and
date on every run, which churned provenance for no informational gain.

---

## 4e. Sixth pass — the §8.1 single-asset input, 18 August 2026

**`largest_asset_pp_share`, all seventeen, from per-asset Ore Reserve tables.**
This closes the item §4d deliberately left open, and it closes it as a
*measurement* rather than as the disclosure job §4d expected.

### The field changed shape before it was sourced, and that was the point

§4d recorded `single_asset_shares` as "sourced for none, and deliberately not
attempted" because the 20% asset cap it fed could not bind. That was replaced
cap with a 10% cap on single-asset *companies*, which binds directly, and the
field became a hand-set boolean. **It was not sourced as one.** Seventeen
booleans is seventeen unrecorded judgement calls, invisible to
`tools/config_audit.py` and unperturbable by `tools/sensitivity.py`; two people
sourcing them would not have agreed and neither answer would have been arguable
after the fact.

So the data layer now holds a quantity — the share of attributable,
Gate-1-eligible P&P reserves at the largest asset — and the engine derives the
boolean against `constraints.single_asset_pp_share_threshold` = 0.80. The single
judgement is in `config.json`, declared, audited and perturbable.

### The definition was fixed before any number was computed

Three rules, all now in methodology §8.1. They were settled first precisely
because two of them change an answer:

1. **An asset is one processing plant plus the deposits the mine plan feeds it**
   — not one mine.
2. **Reserves as disclosed, no adjustment for development status.**
3. **Where two groupings are both defensible, record the more concentrated one.**

Rule 1 is what makes Greatland 1.000 rather than 0.66: Havieron and Telfer are
separate deposits 45 km apart, but Havieron has no processing route of its own
and its ore goes to the Telfer plant. Rule 2 is what makes Capricorn 0.700 rather
than 1.000. **Both rules were written down before the tables were read**, which
is the only thing that stops this being a definition chosen to fit an answer.

### The result

| | Share | Largest asset | | Share | Largest asset |
|---|---|---|---|---|---|
| PNR | **1.000** | Norseman ◆ | VAU | 0.772 | Leonora Operations |
| RXL | **1.000** | Youanmi ◆ | RMS | 0.738 | MMG Hub |
| CYL | **1.000** | Plutonic Belt ◆ | BC8 | 0.736 | Kal East |
| GGP | **1.000** | Telfer–Havieron ◆ | CMM | 0.700 | Mt Gibson |
| BGL | **1.000** | Bellevue ◆ | WGX | 0.687 | Murchison |
| OBM | **1.000** | Davyhurst ◆ | GMD | 0.660 | Leonora hub |
| AAR | **1.000** | Mandilla ◆ | NST | 0.576 | KCGM |
| AUC | **1.000** | Katanning ◆ | EVN | 0.521 | Cowal |
| | | | RRL | 0.490 | McPhillamys |

**Eight of seventeen, against the four methodology §11 named from memory.** The
regression test behaved: PNR and RXL came back at 1.000 on any reading. CMM
landed at 0.700, which is where the forward rule puts it.

### The two findings that moved the index

**CYL is single-asset and §11 did not say so.** 100% of Catalyst's 1,542 koz Ore
Reserve sits under one line of its own statement — "Total Plutonic and Marymia" —
across nine deposits (Plutonic UG 817, Trident 397, Old Highway UG 101, Cinnamon
65, Hermes 62, Old Highway OP 39, Plutonic East 34, K2 20, Trident West 6), all
spokes of a hub-and-spoke plan whose stated rationale is "the latent processing
capacity at the Plutonic processing plant". Bendigo carries 163 koz of resource
and **zero reserve**. Catalyst was a cap-bound position in the book at
12.52%, was capped at 10% when the rule was adopted, and is capped at 7.5%
under v1.9.

**GGP is single-asset and it is the case the asset rule decides.** Deposit names
give Havieron 3.3 Moz of 5.0 = 66%. One plant gives 100%. The issuer's own
language is singular — "the Telfer-Havieron gold-copper complex", "a substantial
and long-life gold-copper operation". Below the cap at ~8% today, so no weight
moved; recorded because the definition and not the arithmetic decides it.

### What it cost, stated as a cost

PNR 15.00% → 10.00%, CYL 12.52% → 10.00%, 7.52% one-way turnover, redistributed
pro rata across the ten uncapped names. Against an **unchanged** gold price
(A$6,216 both runs, so this is not market drift), the index's price per claimed
ounce rose **A$643.51 → A$684.50, +6.4%**. PNR at A$372/oz and CYL at A$530/oz
are the two cheapest claims in the universe; capping them necessarily makes the
book dearer per ounce. That is the trade §8.1 asks for and it should be put to
the committee in those words.

### Document work this pass required

- **WGX `rr2025_mirror`** — every `westgold.com.au/pdf/...` path now returns 404,
  including the one this record cited for four fields. Re-sourced to the PR
  Newswire distribution copy of Westgold's own release. Not a report about the
  filing; the filing.
- **VAU `rr2025_asx`** — the two listcorp URLs previously cited return a page
  title and no table text. Re-sourced to the lodged ASX PDF.
- **AUC `q_dec2025`** — added for Appendix B, which restates the DFS-update
  reserve by zone.

### One ledger inconsistency found and NOT fixed

Vault's `pp_moz` of 3.608 Moz is the **eligible** reserve — Sugar Zone's 389 koz
is already excluded — while `mi_non_reserve_moz` of 4.99 is group M&I less that
eligible P&P. So Sugar Zone's *reserve* ounces currently sit in the M&I
non-reserve tranche at a 0.5 weight and then take the 0.929 eligibility haircut
as well. The direction runs **against** the name, and correcting it is a §6
ledger change rather than part of this pass, so it is recorded in the field note
and left for the committee. The previous note's claim that "Sugar Zone carries no
reserve" is wrong: the lodged statement gives it 2,253 kt at 5.4 g/t for 389 koz.

---

## 4f. Jurisdiction B1 / B3 verification, 18 August 2026

Statutory instruments and regulator publications, not trade press. Full detail in
`data/jurisdictions.json`; the three findings worth carrying:

**QLD B1 — verified, and the escalator is spent.** Gold *is* on a price-linked
sliding scale, which is exactly what §2.3 B1 exists to find. Mineral Resources
(Royalty) Regulation 2025 Schedule 1 part 1 s2 — which **repealed and replaced
the Mineral Resources Regulation 2013 this repo was still citing**, effective 1
September 2025 — sets reference price 1 at A$600/oz and reference price 2 at
A$890/oz, with 2.5% below the first, a formula between, and **5% at or above the
second**. Spot is seven times reference price 2, and the Revenue Office's own
worked example already applied 5% in the December 2020 quarter. So marginal
convexity at any price this index cares about is **exactly zero**, and what
remains is a flat regime at double WA's rate. A rule "penalising in proportion to
the escalator's slope" would have penalised Queensland for a slope of zero — a
good argument for treating B1 as disclosure rather than a score.

**NSW B1 — verified at a flat 4.0%.** Gold is absent from Schedule 6 of the
Mining Regulation 2016, so it takes the ad valorem rate on ex-mine value. §2.3
was already asserting "flat ad valorem" while `jurisdictions.json` carried
`rate: null` and `verified: false`; the prose was ahead of its data and is now
confirmed rather than corrected.

**WA B3 — verified, and the answer reframes the test.** There are essentially
**no statutory maximum determination periods** for WA mining approvals: the
regulator's own timeframes page has a column headed "Is it statutory, regulatory
or target?" and every mining row answers *target*, the two genuine statutory
clocks being EP Act Part IV steps that bracket an assessment of unbounded
duration. Against those targets, FY2023-24: **42.4% of Mining Proposals inside 30
business days against an 80% objective**, PoWs down from 77.1% to 53% in a year,
NVCPs 67.5%. A Mining Proposal averaged 46 business days of agency time and **123
days end to end**. Qualifiers both ways: 85.2% of finalised Mining Proposals had
information requested from the proponent, averaging 69.4 business days, so much
of the gap is not regulatory; but the department attributes its own shortfall to
"resourcing constraints, staff turnover and training". **The WA tenure exposure
this finds is schedule, not revocation.**

Two housekeeping corrections in the same file. **The regulator has been renamed
twice** — DMIRS → DEMIRS (2023) → DMPE (March 2025) — and this repo was searching
under the oldest name, which would have returned nothing and looked like an
absence of published data. And **`_status` pointed at "open item §13.2"**, which
is "Denominator — enterprise value"; the register is §12.2.

**AU-TAS index exposure is nil, not "Catalyst's Henty mine".** Catalyst completed
the sale of Henty to Kaiser Reef on 16 May 2025. Its own resources-and-reserves
page lists no Tasmanian asset and 100% of its reserve is at Plutonic and Marymia
in WA. The Tasmanian verification stands and was worth doing; it is simply not
load-bearing, and methodology §2.3's "and now matters (Catalyst's Henty mine)"
was stale when written.

---

## 4g. Grade-tonnage Phase 0 survey, 18 August 2026

Not a sourcing pass — a search that established there is nothing to source.
≈11 MB of primary text across all seventeen names, including the complete JORC
Table 1 sections of the three largest statements and all five standalone
feasibility studies. **Zero of twelve constituents publish a resource at two or
more cut-offs, or a grade-tonnage table.** One partial (RXL: a grade-tonnage
*chart*, underground only) and one unknown (WGX's five NI 43-101 technical
reports — every issuer URL 404s and SEDAR+ was not retrieved).

The cleanest evidence is Rox's own DFS, which says the calculation was done and
the output withheld: values "were calculated for the full **range of cut-offs**,
allowing the scenario which produced the highest margin … to be identified. The
**selected** cut-off grades used in the Study are shown in Table 10." Issuers run
the curve and publish its argmax.

The current conclusion and its investment consequence are consolidated in
`docs/investment-case.md` §3; the underlying source record remains here and in
the knowledge store.

---

## 4h. Load-bearing capital and facility refresh, 21 August 2026

Four issue-2 records were re-read from primary filings. Evidence states are now
stored beside accepted load-bearing values; the engine validation of those states
belongs to issue 3.

| Name | Primary evidence | Recorded result | State |
|---|---|---|---|
| RMS | Audited FY26 report, Note 27, p109 | A$79.218m capital commitments within one year | `POINT` for that coverage; no second year inferred |
| NST | Audited FY26 Annual Report, pp31 and 68 | A$1.75bn undrawn in equal tranches maturing Mar-2030 and Mar-2031 | `POINT`; 1 Mar 2030 is the conservative earliest day |
| GGP | 1 Jun facility execution announcement plus 29 Jul June quarterly | A$475m undrawn revolvers; five- and seven-year terms | `POINT`; shorter tranche conservatively dated from 1 Apr 2031 |
| WGX | 18 Aug Fletcher filing and ASX announcement feed checked 21 Aug | No complete execution-capital amount or coverage period; A$600m facility limit not restated with tenor | capital `UNRESOLVED` and absent; facility `CARRY_FORWARD`, uncredited in Gate 2 |

**RMS is two different capital facts, not one.** The A$79.218m commitments-note
amount is exact over its disclosed one-year period and now closes the current
`committed_capex_aud_m` gap. It does not reconcile spend to the October 2025
A$381m Mt Magnet programme, so that separate execution-capital candidate remains
an `UPPER_BOUND`, not a point balance.

**WGX stays absent rather than estimated.** The former A$145m approved 2.6 Mtpa
stage is a lower bound after Westgold disclosed that it is reviewing a larger
4 Mtpa case and has committed or planned additional Murchison milling capacity
without a total. The FY26 financial result and Strategic Outlook were not in the
ASX feed on 21 August. FY26 non-sustaining spend is not a remaining-capital
balance and was not substituted.

**Facility dependency is now source-complete where it matters.** NST's shorter
tranche and both GGP revolvers extend beyond the August 2028 Gate 2 horizon. The
WGX facility still has no verified term date and is therefore credited at zero;
WGX survives the current bridge on treasury alone, so that absence cannot favour
its verdict.

---

## 5. Open gap register

Ordered by what blocks the build.

> **Superseded in every particular, 18 August 2026.** `tools/gaps.py` is the live
> register — **clean 13, partial 3, blocked 1** — and `data/README.md` carries the
> current narrative. Share counts were resolved by `tools/asx.py` (§4b), resource
> splits by §4b/§4c, constraint inputs by §4d, the §8.1 single-asset input by
> §4e, and the whole Tier B jurisdiction list by §4f. Grade-tonnage curves closed
> by §4g, which established that public disclosure does not support them.
>
> **What genuinely remains: three fields and one boundary case.** BC8's AISC (a
> disclosure gap the company has declined to close, not a sourcing failure);
> PNR's reserve deck, which reads 0.000pp because nothing consumes it; WGX's
> unresolved committed capital, which remains absent. Plus VAU's
> `largest_asset_pp_share` at 0.772 against a 0.80 threshold — sourced, not a
> gap, but the one classification a definitional argument could move.
>
> The tables below are kept because they record what was blocking and when.

### Blocking — name cannot be weighted

| Ticker | Missing |
|---|---|
| CYL | **Tasmania Tier B assessment.** Henty is Tasmanian; Tasmania has never been assessed. Also: Plutonic/Henty ounce split, share count |
| CMM | `mr_total_moz` — website still shows the pre-Diggers 6.6 Moz MR against the new 5.24 Moz reserve. Vintages cannot be mixed. |
| PNR | Share count |
| BC8 | Share count, AISC, net debt, group reserve total (only Kal East's 243 koz located) |
| RXL | Post-placement share count |
| AAR | Share count *(moot — fails Gate 2)* |
| AUC | Share count, cash *(moot — fails Gate 2)* |
| OBM | Verified share count (~1,920m estimated from a 5 Feb 2026 cap) |

### Non-blocking — degrades a score

- **M&I / Inferred splits** still imputed for OBM, CYL, PNR, BC8, RXL, AAR. Of these only OBM currently carries weight; the rest are rejected at the gates anyway.
- **Reserve decks** for EVN, RMS, GMD, CYL, PNR. All three weighted ones are on the respective R&R pages — a reading task.
- **Hedge books** for nine names.
- **OBM FY26 statement.** The PDF at the company's March 2026 URL is the FY25 statement (2.11 Moz MR / 236 koz OR as at 1 Jul 2025). The FY26 figures used here (3.69 Moz / 610 koz as at 1 Apr 2026) come from secondary reporting of the July 2026 release. Source the primary.

### Jurisdictional — mostly CLOSED 18 August 2026 (§4f)

- ~~**AU-QLD B1**~~ — **VERIFIED.** Gold *is* on a price-linked sliding scale, but
  it is capped at 5% and reference price 2 is A$890/oz, so it has been saturated
  for two decades and its marginal convexity is zero. Not "materially worse than
  WA on convexity" — identical on convexity, at double the rate. Read from the
  Mineral Resources (Royalty) Regulation **2025**, which repealed the 2013
  instrument this line named.
- ~~**AU-NSW B1**~~ — **VERIFIED** at a flat 4.0% ad valorem on ex-mine value; no
  price-linked element. Gold is outside Schedule 6 of the Mining Regulation 2016.
- ~~**AU-TAS**~~ — **VERIFIED** (and index exposure is now nil: Henty was sold in
  May 2025).
- ~~**AU-WA B3**~~ — **VERIFIED**, and it was the largest real gap in the layer
  rather than the QLD/SA/TAS list this register named. There are essentially no
  statutory determination periods; 42.4% of Mining Proposals met the 30-business-day
  target in FY2023-24 against an 80% objective.
- **AU-NT B1** — profit-based royalty; confirm rate and base from the Mineral
  Royalty Act 1982. Structurally the worst in the set. **No index exposure**, so
  unverified costs nothing today.
- **AU-SA B1** — confirm rate and whether the refined/ore differential creates an
  effective escalator. No index exposure. Note Queensland as the cautionary case:
  "presumed neutral" would have been wrong on structure there, and right only by
  accident of where the price sits.
- **B2 / B3 / B4 outside WA** — still unverified everywhere. B4 is the only one
  of the five that is a gate, and it is the one carrying an unresolved event
  (McPhillamys, NSW) and an undecided application (Lake Miranda, WA).

---

## 6. Watch items

- **RMS FY26 commitments and NST facility terms are closed** from their 20–21
  August audited reports. RMS execution-capital spend allocation remains unavailable.
- **WGX** FY26 financial result and Strategic Outlook were not filed at the
  21 August check; the Strategic Outlook is expected in early September. Re-source
  execution capital, coverage, facility tenor, AISC basis and treasury split then.
- **PNR** and **CYL** resource/reserve updates due September 2026 quarter; CYL also guides FY27 then.
- **GMD/VAU** scheme completion targeted November 2026, ACCC the open condition. Event-driven removal of VAU.
- **EVN/Carnaby** scheme — will push gold NAV share toward the 0.75 floor.
- **RRL McPhillamys** judicial review judgment outstanding since the December 2025 hearing. Binary on 1.89 Moz, roughly half the reserve base.
- **AUC** FID targeted end-2026 with project financing — re-test D3 then.
- **OBM** FY26 AISC came in ~21% above original guidance at A$3,496/oz, the highest in the universe, with A$233m of committed EPC capex. Run Gate 2 properly.
