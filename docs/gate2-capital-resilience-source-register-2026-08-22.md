# Gate 2 capital-resilience source register — 22 August 2026

**Purpose:** durable source register for Phase 1 of the superseded continuous
capital-resilience design, and the evidence base for the simpler replacement
plan. It records, for every producer-path candidate, whether the former §7
default ASX producer pack can actually be sourced from a primary document, and
what the document says.

Retrieval method and channel evidence are in
`docs/primary-document-fetching-strategy.md`. PDFs are temporary audit material
under `/tmp` and are not stored in the repository.

This is an evidence register, not an assertion that a document supplies the new
common-date cash, debt-cash-outflow, or contractual-commitment schedule. The
field-to-document mapping remains authoritative in `data/companies.json`.

## 1. Availability of the FY26 primary financial report

Fourteen candidates were swept on 22 August 2026 against the ASX research API,
the exchange's full-calendar-year announcement index, and each issuer's own
back-catalogue platform. Where a report is recorded as absent, the absence was
established from a complete index, not from the 5-item API window.

| Ticker | FY26 annual/interim report | Basis |
|---|---|---|
| NST | **lodged** 20 Aug 2026 | inspected; a revised Appendix 4E of the same date changes only the DRP election date |
| EVN | **lodged** 19–20 Aug 2026 | inspected |
| RMS | **lodged** 21 Aug 2026 | inspected |
| GMD | **lodged** 20 Aug 2026 | inspected |
| VAU | **lodged** 20 Aug 2026 | inspected |
| RRL | **lodged** 21 Aug 2026 | inspected |
| CMM | not lodged | due 31 Aug; single combined "Full Year Statutory Accounts" expected 26 Aug – 5 Sep |
| GGP | not lodged | Appendix 4E by 31 Aug is **unaudited and carries no notes**; audited report ~late Sep |
| WGX | not lodged | expected 25–31 Aug with FY27 guidance, per its own quarterly |
| BGL | not lodged | lodges the annual report in place of a 4E; expected 26–31 Aug |
| OBM | not lodged | expected 25–31 Aug (FY25 4E was 26 Aug 2025) |
| CYL | not lodged | expected 28–31 Aug (29 Aug in each of the last two years) |
| PNR | **not required** | a *mining exploration entity*, so LR 4.3A does not apply and no 4E has ever been lodged; annual report due 30 Sep under LR 4.5.1 |
| BC8 | not lodged | combined annual report, historically late Sep |

Six of fourteen have FY26 accounts today. For the other eight the latest primary
report is a December 2025 half-year or a June 2025 annual — and a half-year is
not a substitute, for the reason in §3.

## 2. Determinative finding: the former §7 commitments baseline does not exist

The superseded plan's §7 hypothesised that an annual contractual
capital-commitments note is
"routinely available from an established ASX gold producer", and instructs the
audit to verify that rather than assume it. **It is not available in the form
the plan requires. No candidate publishes a contractual capital-commitment
schedule with timing that spans the two-year horizon.**

| Ticker | Capital commitments disclosure | Timing |
|---|---|---|
| EVN | A$146.411m within 1yr; A$75.525m 1–5yr (Note 19(a)(ii)) | two buckets; 1–5yr **cannot** be narrowed to the pre-20-Aug-2028 portion |
| VAU | A$175.163m ≤1yr; A$37.199m 1–2yr (Note 31) | two buckets; up 48% on FY25 |
| NST | A$406.1m (Note 15(a)) | **no timing split**; A$69.1m unattributed to any named project |
| RMS | A$79.218m within one year (Note 27) | one row; beyond-one-year rows **omitted** while adjacent tables in the same note carry them |
| WGX | A$44.904m within one year (Note 21, Dec-25) | one row |
| CYL | A$21.969m within one year (Note 17, Dec-25) | one row; the half-year also **drops** the exploration-commitments table the annual carries |
| PNR | A$2.755m (HY Note 15, Dec-25); A$5.636m (FY25 Note 27(a)) | one row, "within one year" |
| BGL | A$14.773m (Note 14(a), Dec-25) | no timing split |
| OBM | A$7.688m within one year (FY25 Note 22(b)) | one row, **12 months stale**; pre-dates its own A$233m EPC contract |
| GGP | A$37.8m (Dec-25) | **not a note** — one trailing sentence under PP&E |
| GMD | **none** | Note 22 is one narrative sentence with no amount |
| RRL | **none** | Note 23 refers only to A$4.517m of exploration commitments |
| CMM | **none** | Note 33 refers only to gold-delivery (nil) and exploration commitments |
| BC8 | **"no material contractual commitments"** at both balance dates | explicit nil |

Two candidates (EVN, VAU) give any bucket beyond one year, and neither aligns to
the horizon. Three publish no capital-commitments note at all. Under the
superseded plan's §6.2, an unresolved in-scope adverse tail was load-bearing and
made the producer `UNTESTED`; on this evidence that applied to substantially
the whole cohort, including GMD and OBM, which the 21 August coverage audit had
treated as carrying usable commitment intervals.

Nor can the sustaining/growth split required by the superseded §7(6)
AISC-overlap reconciliation be made from any commitments note in the cohort.
Not one separates them.

## 3. A half-year report is not a fallback

AASB 134 does not require a liquidity-risk or contractual-maturity disclosure,
and in practice these issuers omit it. Confirmed absent from every half-year
inspected: **CYL** (19 notes, none on financial instruments), **BGL** (19 pages,
"matur" appears three times, all narrative), **OBM** (notes 1–16, no
financial-instruments note), **GGP** (notes 1–18, none on liquidity), **WGX**
(24 notes, zero hits for maturity or liquidity risk), **BC8** (no AASB 7
disclosure; the only table is a discounted lease carrying-amount split), **CMM**
(no maturity analysis).

Consequence: for the eight candidates without FY26 accounts, the newest
contractual-maturity schedule is 30 June 2025 — **fourteen months stale at the
build date**. For OBM that schedule pre-dates the entire DRIVE to 300
balance-sheet change.

## 4. Maturity notes that are published are not uniformly reliable

| Ticker | Note | Assessment |
|---|---|---|
| NST | 10(c)(ii) | sound. Undiscounted stated; interest confirmed arithmetically (A$387.3m on borrowings, reconciling to a 6.125% semi-annual coupon on US$600m); every row and column foots to the balance sheet |
| EVN | 17(d)(ii) | sound. Undiscounted, interest included (A$363.5m on USPP). No bank-debt row — term loans repaid Oct 2025 |
| VAU | 21(c) | sound, and complete: no borrowings row because VAU has no debt. Cross-checks exactly to the Note 18 lease schedule |
| RRL | 18 | sound but thin — trade payables and leases only; no debt |
| GMD | 18 | **two defects.** Lease contractual cash flows (A$14.839m) fall *below* carrying amount (A$16.275m), and the 1–2yr/2–5yr buckets are identical to the FY25 comparatives — a roll-forward error. Separately, the A$200m bank principal is bucketed at 2–5 years while Note 17 gives the facility expiry as March 2028, i.e. the note **implicitly assumed a refinance** forbidden by the superseded plan's §5.1 |
| RMS | 18 | **unusable.** The lease row excludes A$18.810m of contractual interest despite a stated undiscounted basis and omits the >5yr column; the royalty row's buckets (A$89.427m) sit *below* carrying (A$135.179m) while its total (A$166.663m) exceeds it — the row mixes bases internally. Use Note 12 (leases, A$98.279m undiscounted, foots exactly) and Note 13 (royalty, discounted, no timing) instead |
| GGP | 22 (FY25) | states "contractual **discounted** cash flows", but leases and deferred consideration both exceed carrying value — it is undiscounted and interest-inclusive. Issuer drafting error |
| BC8 | 22 (FY25) | asserts "including estimated interest payments" yet lease contractual flows (A$20.263m) fall below carrying (A$21.460m). Flag, do not consume |
| WGX | 4(d) (FY25) | sound and explicitly interest-inclusive; equipment finance is material at A$83.9m |
| OBM | 25(c) (FY25) | internally consistent, but 14 months stale |

## 5. Facility term against the 20 August 2028 horizon

| Ticker | Facility | Expiry | Credit |
|---|---|---|---|
| RMS | A$500m RCF, undrawn | **31 Mar 2031** | qualifies. Term is disclosed **only** in the Dec-25 half-year's subsequent-events note; no standalone facility announcement was ever lodged |
| GGP | A$250m / A$225m / A$25m CIF | **~2031 / ~2033** | qualifies. The A$75m working-capital facility that the plan flagged as expiring in-horizon was **cancelled** and replaced on 1 Jun 2026 |
| WGX | A$600m in three tranches, undrawn, **unsecured** | Mar 2029 / 2030 / 2031 | qualifies |
| NST | A$1.75bn, two A$875m tranches, undrawn | **1 Mar 2030 / 1 Mar 2031** | qualifies. Exact days, not months — the current field note's "earliest possible expiry" caveat is superseded |
| OBM | A$200m RCF, undrawn | **30 Jun 2029** | qualifies on term, but sourced only from an 18 May 2026 announcement. OBM's prior SFA sat signed-but-not-closed for 3½ months, and no auditor has seen this one |
| EVN | A$525m RCF, undrawn | **1 Aug 2028** | **fails by 19 days.** The report's A$1,872.5m "total liquidity" headline is therefore not usable |
| GMD | A$100m undrawn of A$300m revolving | **Mar 2028** | **fails** |
| RRL | A$300m RCF, undrawn | **~3 Feb 2028** | **fails.** No expiry appears in any primary document; derived from "Tenor — Three years" in the Feb 2025 establishment announcement, and the agreement has since been varied without a lodgement |
| CYL | A$200m RCF, undrawn | **not sourceable** | four-year tenor "at financial close"; the close date is never stated |
| VAU, CMM, PNR, BGL | none | — | VAU and CMM state nil explicitly; BGL confirms nil undrawn via Appendix 5B item 7.5 |
| BC8 | A$30m CBA asset facility, undrawn | **not disclosed** | no term, committed status, covenant or draw condition anywhere in 874 lodgements |

**Covenants are quantified by exactly one issuer.** EVN discloses tangible net
worth ≤0.5:1, leverage ≤2.5:1 and interest cover ≥3.5:1, tested semi-annually.
Every other candidate names covenant *types* or says "customary for a facility
of this nature". The superseded plan's §5.1 requirement of demonstrated
covenant survival under stress was therefore unsatisfiable for the cohort bar
EVN.

EVN additionally carries an in-window exposure absent from any maturity bucket:
performance bond Facilities C (A$340m, expiring 31 Jul 2028) and D (CAD 150m,
31 Mar 2027) carry the A$300.4m of environmental guarantees and both expire
inside the horizon.

## 6. "Debt free" is a defined term, and it is not zero

Four issuers describe themselves as debt free while carrying interest-bearing
liabilities. This must not be read into `net_debt_aud_m` or the stress bridge.

- **WGX** — "100% debt free" refers to the syndicated facility. Note 15 at 31
  Dec 2025: lease liabilities A$84.808m plus equipment loans A$76.459m =
  **A$161.267m**, at a 7.73% weighted average rate on 36-month terms, with
  A$26.06m of new equipment loans added in the half.
- **CYL** — "Debt: Nil" excludes hire purchase and insurance-premium funding.
  Proven from its own FY25 pair: the Chairman's letter says "debt free" while
  Note 21 carries A$14.495m. At 31 Dec 2025 the figure is **A$15.386m**.
- **OBM** — "Debt | Nil" excludes AASB 16 leases, which were A$28.3m at 31 Dec
  2025 and consumed A$8.3m of principal and interest in the June quarter alone.
- **PNR** — `net_debt_aud_m: -223.4` is cash **plus bullion at spot**. Appendix
  5B item 5.5 gives cash alone as **A$202.88m**; the difference is 3,494 oz of
  in-circuit gold at A$5,792.40.

## 7. AISC basis is heterogeneous, and the headline denominator is usually wrong

§5.6(4) requires compatible volume and AISC bases. Six distinct conventions are
in use, and in five cases the correct denominator is *not* the headline
production figure.

| Ticker | AISC | Basis | Matching volume |
|---|---|---|---|
| RRL | A$2,945/oz | per ounce **produced** (stated) | 379,050 oz produced |
| CMM | A$1,629/oz | per ounce **produced** (stated) | 123,589 oz produced |
| GGP | A$2,179/oz | per ounce **produced**, net of copper credits | 328,987 oz produced |
| WGX | A$2,841/oz | per ounce produced **excluding purchased-ore ounces** | **331,216 oz**, not the 387,354 oz headline |
| GMD | A$2,670/oz | per ounce sold **excluding third-party OPA ounces** | **≈251koz**, not 285koz produced or 289koz sold |
| OBM | A$3,496/oz | per **equivalent ounce sold**, including attributed ounces | 140,641 oz |
| EVN | A$1,717/oz | per ounce sold, **continuing operations ex-Mt Rawdon**, copper as by-product credit | **687,324 oz**, not 714,728 oz produced |
| RMS | A$1,983/oz | per ounce **sold** (remuneration scorecard) | 190,261 oz sold |
| BGL | A$2,827/oz | per ounce **sold** | 142,000 oz sold |
| CYL | A$2,738 / A$2,747 | publishes **both** bases as a matched pair | 99,359 sold / 103,761 produced |
| PNR | none for FY26 | quarterly table only, produced excl. OPA | no full-year figure published |
| VAU | A$2,924/oz | **not stated anywhere** | 336,540 produced / 334,904 sold, 0.5% apart |
| BC8 | **never published** | — | — |

BC8 has explicitly withheld AISC as unrepresentative during ramp-up and will
publish its first figure as FY27 guidance. Its absence from the data layer is
the issuer's own position, not a gap.

## 8. Consequences for the plan

1. The superseded §7 working hypothesis failed on its own terms. Its instruction
   was to stop after the coverage audit and propose the narrowest fallback when
   the core pack was not routine. The replacement plan does that.
2. The superseded §11.2 fallback set did not survive. It assumed EVN, GMD, OBM
   and RXL might remain admissible. GMD publishes no quantified commitments
   note; OBM's is twelve months stale and pre-dates its own A$233m EPC contract.
3. Eight of fourteen candidates have no FY26 accounts, and six of those are due
   within nine days. A re-sweep from 26 Aug to 5 Sep, plus late September for
   PNR and BC8, would change the picture materially and cheaply.
4. Covenant survival under stress is unsatisfiable for every producer except
   EVN. That is why the replacement plan gives facilities no Gate 2 credit.

## 9. Items to correct in `data/companies.json`

- **NST** `undrawn_facilities_aud_m` — the note says the issuer gives only the
  month and records 2030-03-01 as an earliest-possible bound. Note 10(c)(i)
  gives exact days and the per-tranche A$875m split. It is a point value.
- **OBM** `execution_capital_projects` — the A$375m mill package is carried at
  `committed_capex_state: POINT`. Only **A$233m** is contracted (GR Engineering
  EPC, executed 15 Jun 2026); A$142m is a board approval of owner's costs and
  contingency with no counterparty.
- **GGP** — the 1.2× EBITDA/net-debt covenant belongs to the **cancelled**
  December 2024 facility and must not be carried forward.
- **PNR** — `net_debt_aud_m: -223.4` conflates cash with bullion; see §6.
- **VAU** — FY25 commitment figures are superseded by FY26 (A$212.362m total
  contracted capital, up 48%).
- **NST/KCGM** — the superseded §7(9) dual-use reconciliation is confirmed live: Note 15(a)
  carries A$254.5m of contracted KCGM commitments whose scope, including the
  tailings dam and thermal power plant, overlaps the A$350–470m FY27 guidance
  line in the project ledger. They are not additive.

## 10. Obligations inside the horizon that appear in no maturity bucket

Collected because each is a real in-window cash movement that a bridge built
only from maturity notes would miss.

- **NST** — KCGM electricity supply agreement, ~A$131m/year, recognised as a
  lease only on commissioning in FY28.
- **EVN** — A$101.7m of Northparkes contingent consideration, ceasing 30 Jun
  2027 with final payment July 2027; FVTPL, so outside the AASB 7 table.
- **VAU** — A$50.7m break fee paid to Regis in July 2026 (after the balance
  date), and A$81.4m of current tax due December 2026.
- **GMD** — A$100.8m current tax with a A$100–120m catch-up guided for December
  2026, plus ~A$32m of stamp duty guided for CY2027.
- **BGL** — A$25.0m expected to become restricted cash on 31 December 2026 on
  transfer to a Debt Service Reserve Account, held until the final repayment.
- **WGX** — ~A$200m of FY26 tax payable in FY27.
