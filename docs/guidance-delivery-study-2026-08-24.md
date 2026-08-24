# Guidance-delivery study — 24 August 2026

**Purpose:** the evidence base requested by `docs/guidance-delivery-research-brief-v1.9.md` —
an auditable, cohort-wide record of original annual production and AISC guidance
versus actual outcomes for the last three completed financial years, for every
candidate classified `producer` or `near_producer`, including candidates
currently excluded by another gate. This determines whether the evidence
*could* support a future SJGV amendment applying a 5% execution-risk cap after
two material miss-years. **It changes no index eligibility, weight,
methodology, configuration, or accepted company field.** No value in this
document is written to `data/companies.json`, and `build_index.py` is
unmodified.

Every fact below is registered in the knowledge-base ledger
(`knowledge/claims.jsonl`) via `tools/kb.py register-claim`, each with an
exact page/table/section locator and a verbatim excerpt. Each such claim
carries `"projectable": false` with `"decision.code":
"ARCHIVED_POINT_IN_TIME_OBSERVATION"`, so it cannot affect a live gate or
weight — the earlier draft of this report described that mechanism with the
literal phrase `held_from_projection: true`, which is a `register-claim`
*input* flag consumed at registration time, not a field that appears on the
stored claim record; corrected 2026-08-24. The machine-readable appendix,
`docs/guidance-delivery-candidates-2026-08-24.json`, carries the `claim_id`
for every guidance and actual figure below.

**Correction notice (2026-08-24 compliance remediation):** this report was
reviewed after publication and found to contain several defects, corrected in
place below and in the appendix: two EMR and one BTR actual figure were
calculated (summed/weighted-averaged or JV-attributed) from quarterly source
data but registered as bare `POINT` observations with no derivation record;
two EMR guidance claims silently annualised a quarterly carry-forward rate the
issuer had explicitly not yet formalised into annual guidance; a host-
authority defect classified two shared, multi-tenant IR-hosting CDNs
(`q4cdn.com`, `investorroom.com`) as blanket T2 sources, which in turn made
OGC's CY2024 final guidance rest on a document with no issuer-controlled
route; and this report's universe description conflated "classified
producer/near_producer" with "current live index constituent." Each is
detailed at the point it arises below. `tools/kb.py`'s document-verification
mechanics were also generalised (host-authority test coverage, non-ASX issuer
detection, EDGAR accession identifiers, reporting-period extraction), which
resolved the evidence-verification gaps in every one of the 180 documents this
report's claims cite without any further action.

## 1. Universe and periods

23 companies: 14 companies classified `producer`/`near_producer` in
`data/companies.json` (NST, EVN, CMM, GGP, GMD, RMS, RRL, WGX, VAU, BGL, OBM,
CYL, PNR, BC8) plus 9 candidates presently excluded by another gate but
independently confirmed producer-classified (web research, not inferred):
Newmont (NEM, ASX CDI/NYSE, excluded on Gate 1 eligible-ounce-share), Agnico
Eagle (AEM, TSX/NYSE, excluded on Gate 1 Tier A), OceanaGold (OGC, TSX,
excluded on Gate 1 eligible-ounce-share), Perseus Mining (PRU), Resolute
Mining (RSG), West African Resources (WAF), Emerald Resources (EMR) (all four
excluded on Gate 1 Tier A — no Tier A jurisdiction production), Meeka Metals
(MEK) and Brightstar Resources (BTR) (both excluded on other grounds; both
confirmed genuine producers — first gold poured, per an ASX announcement dated
2 July 2025, at the Murchison Gold Project for MEK, an active Ore Purchase
Agreement producer for BTR). Developers (RXL, AAR, AUC) are out of scope — the
brief covers `producer` and `near_producer` only.

**Correction (2026-08-24):** the original text called this list of 14 the
"current SJGV producer/near_producer constituents," conflating classification
with live index membership. Per the SJGV v1.8 build (`weights.json`, generated
2026-08-23T22:23:35Z), BC8 is **not** a current constituent — it is excluded
by Gate 2 ("AISC unsourced — producer health cannot be tested") and appears
only in the `rejected` array. The build's actual 14th live constituent is RXL
(Rox Resources), which is classified `developer`, not `producer`/
`near_producer`, and is correctly out of scope for this study per the research
brief. The true live producer/near-producer book therefore has 13 names, not
14; BC8 is one of the 14 *classified* records this study covers, but it is not
one of the 13 names an amendment arising from this study could actually apply
a cap to today. Separately, the "1 Jul 2025" first-gold date for MEK stated in
the original text was not independently verified to that precision — the
governing ASX announcement, dated 2 July 2025, confirms the pour occurred "on
schedule" but does not itself restate the exact calendar day; see
`claim:sha256:5d365d7f075c091e1e6d65947acbf046dafcda9c3d13aa46afb8898f0db8925c`
(`MEK`/`first_gold_production_date`) for the wording actually registered.

Rupert Resources, Antipa Minerals, and the Perseus/Resolute/WAF/Emerald block's
original combined exclusion record were unpacked and verified individually;
Antipa (scoping-study stage) and Rupert (developer, delisted) are not
producer-classified and are excluded from this study on that basis, not
inferred.

Fiscal year-end was confirmed from a primary document for every company, not
assumed: 18 of 23 use 30 June; NEM, AEM, OGC, RSG, WAF use 31 December
(confirmed, not assumed, from a lodged Appendix 4E/Preliminary Final Report or
10-K cover page). The last three **completed** years as of the research date
(2026-08-24) are FY2024–FY2026 for June year-ends and CY2023–CY2025 for
December year-ends.

## 2. Coverage table

69 required company-years (23 × 3).

| Status | Count | Meaning |
|---|---:|---|
| COMPARABLE | 53 | boolean miss/no-miss determinable on both original and final guidance |
| MISSING_GUIDANCE | 9 | no formal full-year guidance was ever issued (or, for WAF CY2025, one limb of it) |
| INSUFFICIENT_HISTORY | 5 | company or the relevant operation had not completed a first full year of guided production |
| NOT_COMPARABLE | 1 | scope changed (M&A) between guidance and actual with no issuer reconciliation |

**Coverage count: 54 / 69 comparable company-years (78.3%).**

Full detail, company by company, is in §3. The precise reason for every
non-comparable company-year is in §6.

## 3. Per-company detail

Every cell below is a registered, cited claim (see the appendix for the exact
`claim_id`, document, locator and excerpt). "Revisions" counts formal
production-guidance and AISC-guidance revisions combined. AISC is stated in
the issuer's own reporting currency. A dash (—) means no formal figure exists
for that cell; the reason is in §6.

### AEM — Agnico Eagle Mines

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| CY2023 | COMPARABLE | 3200-3400koz | 3240-3440koz | 1140-1190/USD | 1140-1190/USD | 1 | 3439.65 | 1179 USD | no | no |
| CY2024 | COMPARABLE | 3200-3400koz | 3350-3550koz | 1200-1250/USD | 1200-1250/USD | 1 | 3485.34 | 1239 USD | no | no |
| CY2025 | COMPARABLE | 3400-3600koz | 3300-3500koz | 1250-1300/USD | 1250-1300/USD | 1 | 3447.37 | 1339 USD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

### BC8 — Black Cat Syndicate

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | INSUFFICIENT_HISTORY | — | — | — | — | 0 | 0 | — | INSUFFICIENT_HISTORY | INSUFFICIENT_HISTORY |
| FY2025 | MISSING_GUIDANCE | — | — | — | — | 0 | 39.169 | — | MISSING_GUIDANCE | MISSING_GUIDANCE |
| FY2026 | MISSING_GUIDANCE | — | — | — | — | 0 | 90.833 | — | MISSING_GUIDANCE | MISSING_GUIDANCE |

**3-year miss count:** original=—, final=—. **Candidate-rule trigger:** original=CANNOT_DETERMINE, final=CANNOT_DETERMINE.

### BGL — Bellevue Gold

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | INSUFFICIENT_HISTORY | 75-85koz | 75-85koz | — | — | 1 | 95.56 | — | INSUFFICIENT_HISTORY | INSUFFICIENT_HISTORY |
| FY2025 | COMPARABLE | 165-180koz | 129-134koz | 1750-1850/AUD | 2425-2525/AUD | 4 | 126.139 | 2422 AUD | MISS | no |
| FY2026 | COMPARABLE | 130-150koz | 130-150koz | 2600-2900/AUD | 2600-2900/AUD | 0 | 143.539 | 2827 AUD | no | no |

**3-year miss count:** original=1, final=0. **Candidate-rule trigger:** original=CANNOT_DETERMINE, final=**False** — corrected from the research agent's self-reported CANNOT_DETERMINE. 0 of 2 comparable years miss under final guidance; even crediting the indeterminate FY2024 as a miss, the maximum possible final-guidance count is 1, below the 2-year threshold. See the appendix's `candidate_rule_trigger_final_correction_note`.

### BTR — Brightstar Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | MISSING_GUIDANCE | — | — | — | — | 0 | 3.734 | — | MISSING_GUIDANCE | MISSING_GUIDANCE |
| FY2025 | MISSING_GUIDANCE | — | — | — | — | 0 | 7.826 | — | MISSING_GUIDANCE | MISSING_GUIDANCE |
| FY2026 | MISSING_GUIDANCE | — | — | — | — | 0 | — | — | MISSING_GUIDANCE | MISSING_GUIDANCE |

**3-year miss count:** original=—, final=—. **Candidate-rule trigger:** original=CANNOT_DETERMINE, final=CANNOT_DETERMINE.

### CMM — Capricorn Metals

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 115-125koz | 112-115koz | 1270-1370/AUD | 1270-1370/AUD | 1 | 113.007 | 1421 AUD | no | no |
| FY2025 | COMPARABLE | 110-120koz | 110-120koz | 1370-1470/AUD | 1370-1470/AUD | 0 | 117.076 | 1468 AUD | no | no |
| FY2026 | COMPARABLE | 115-125koz | 115-125koz | 1530-1630/AUD | 1530-1630/AUD | 0 | 123.589 | 1629 AUD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

### CYL — Catalyst Metals

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | MISSING_GUIDANCE | — | — | — | — | 0 | 109.785 | 2645 AUD | MISSING_GUIDANCE | MISSING_GUIDANCE |
| FY2025 | COMPARABLE | 105-120koz | 105-120koz | 2300-2500/AUD | 2300-2500/AUD | 0 | 108.018 | 2495 AUD | no | no |
| FY2026 | NOT_COMPARABLE (original) / COMPARABLE (final) | 145-165koz | 100-110koz | 2100-2300/AUD | 2750-2950/AUD | 3 | 103.761 | 2738 AUD | NOT_COMPARABLE | no |

**3-year miss count:** original=—, final=0. **Candidate-rule trigger:** original=CANNOT_DETERMINE, final=False.

FY2026's *original* guidance (11 Sep 2024) was a group figure including the
Henty mine, divested May 2025 before FY2026 began, with no issuer
reconciliation to the post-divestment single-asset basis — hence
NOT_COMPARABLE against original guidance specifically. The *final* guidance
(29 Apr 2026) is single-asset and matches the actual's scope exactly.

### EMR — Emerald Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 100-120koz | 100-120koz | 780-850/USD | 780-850/USD | 1 | 114.076 | 818 USD | no | no |
| FY2025 | COMPARABLE | 105-115koz | 105-115koz | 810-880/USD | 900-1000/USD | 1 | 98.11 | 1075 USD | **MISS** | **MISS** |
| FY2026 | COMPARABLE | 110-125koz | 105-120koz | 966/USD | 966/USD | 1 | 100.406 | 972.05 USD | **MISS** | no |

**3-year miss count:** original=2, final=1. **Candidate-rule trigger: original=True, final=False.**

**Corrections (2026-08-24 compliance remediation), none of which change the
candidate-rule result above:**

1. **FY2025 original production guidance** was corrected from "100-120koz" to
   "105-115koz." The earlier figure was a claim (`claim:sha256:715acc6f...`)
   that silently annualised (×4) a "25,000-30,000oz per quarter" run rate the
   issuer's own 31-Jul-2024 document explicitly said was provisional
   ("updated annual guidance to be provided as studies progress"). There was
   no genuine formal FY2025 annual guidance before 21-Mar-2025, so that
   document is now the sole "original" — there is no separate revision, and
   the production-guidance revision count for FY2025 drops from the earlier
   figure by one. Under the corrected bounds, FY2025 production *also*
   independently misses original guidance (98.11 < 0.95 × 105 = 99.75koz); it
   was already a miss on the AISC limb, so `miss_year_original` was already
   `MISS` and is unaffected. `claim:sha256:715acc6f...` and its own erroneous
   successor `claim:sha256:65304253...` remain in the ledger as immutable,
   explicitly-superseded history.
2. **FY2026 production actual (100.406koz) and AISC actual (US$972.05/oz)**
   are unchanged in value but are now registered as proper derived claims
   (`claim:sha256:ab067ba0...` and `claim:sha256:d20fc1e1...`), each naming
   its four quarterly dependency claims, formula, rounding and output unit.
   The prior claims held the identical computed values as bare `POINT`
   observations with no derivation record — a calculated figure represented
   as though it were a single directly-reported fact.

### EVN — Evolution Mining

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 770koz | 749koz | 1370/AUD | 1410/AUD | 4 | 716.7 | 1477 AUD | MISS | no |
| FY2025 | COMPARABLE | 710-780koz | 710-780koz | 1475-1575/AUD | 1475-1575/AUD | 0 | 750.512 | 1572 AUD | no | no |
| FY2026 | COMPARABLE | 710-780koz | 710-780koz | 1720-1880/AUD | 1640-1760/AUD | 1 | 714.728 | 1717 AUD | no | no |

**3-year miss count:** original=1, final=0. **Candidate-rule trigger:** original=False, final=False.

FY2024's original guidance (5 Jun 2023) predates the Northparkes 80%
acquisition; guidance was revised twice, once for the acquisition and once for
an operational downgrade.

### GGP — Greatland Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | INSUFFICIENT_HISTORY | — | — | — | — | 0 | — | — | INSUFFICIENT_HISTORY | INSUFFICIENT_HISTORY |
| FY2025 | COMPARABLE | 196-210koz | 196-210koz | 2100-2250/AUD | 2100-2250/AUD | 0 | 198.319 | 1849 AUD | no | no |
| FY2026 | COMPARABLE | 260-310koz | 260-310koz | 2400-2800/AUD | 2400-2800/AUD | 0 | 328.987 | 2179 AUD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

FY2025 is a ~7-month stub (4 Dec 2024 Telfer-completion to 30 Jun 2025); the
issuer's own guidance and actual are both stated on that identical partial-year
basis, so the comparison is valid on its own terms. Greatland's continuous
30 June year-end was confirmed from primary sources — it did not change with
the Telfer acquisition or the ASX listing, contrary to the research brief's
working assumption.

### GMD — Genesis Minerals

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 130-140koz | 130-140koz | 2300-2400/AUD | 2300-2400/AUD | 0 | 134.451 | 2356 AUD | no | no |
| FY2025 | COMPARABLE | 162-188koz | 190-210koz | 2250-2450/AUD | 2200-2400/AUD | 2 | 214.311 | 2398 AUD | no | no |
| FY2026 | COMPARABLE | 260-290koz | 260-290koz | 2500-2700/AUD | 2500-2700/AUD | 0 | 285.402 | 2670 AUD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

### MEK — Meeka Metals

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | INSUFFICIENT_HISTORY | — | — | — | — | 0 | — | — | INSUFFICIENT_HISTORY | INSUFFICIENT_HISTORY |
| FY2025 | INSUFFICIENT_HISTORY | — | — | — | — | 0 | — | — | INSUFFICIENT_HISTORY | INSUFFICIENT_HISTORY |
| FY2026 | MISSING_GUIDANCE | — | — | — | — | 0 | 28.829 | 2956 AUD | MISSING_GUIDANCE | MISSING_GUIDANCE |

**3-year miss count:** original=—, final=—. **Candidate-rule trigger:** original=CANNOT_DETERMINE, final=CANNOT_DETERMINE.

First gold poured 1 Jul 2025 (the first day of FY2026); Meeka has never issued
a bounded full-year production/AISC guidance figure in the sense this study
requires — only life-of-mine study targets and monthly ramp-up figures.

### NEM — Newmont Corporation

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| CY2023 | NOT_COMPARABLE | 6000-6600koz | 5300koz | 980-1080/USD | 1400/USD | 6 | 5545 | 1444 USD | NOT_COMPARABLE | NOT_COMPARABLE |
| CY2024 | COMPARABLE | 6930koz | 6930koz | 1400/USD | 1400/USD | 0 | 6850 | 1516 USD | **MISS** | **MISS** |
| CY2025 | COMPARABLE | 5900koz | 5900koz | 1630/USD | 1630/USD | 0 | 5890 | 1609 USD | no | no |

**3-year miss count:** original=1, final=1. **Candidate-rule trigger:** original=CANNOT_DETERMINE, final=CANNOT_DETERMINE.

CY2023 guidance predates the 6 Nov 2023 Newcrest merger; the actual includes
~2 months of Newcrest production/cost with no quantified issuer reconciliation
to the pre-merger guided basis.

### NST — Northern Star Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 1600-1750koz | 1600-1750koz | 1730-1790/AUD | 1810-1860/AUD | 1 | 1621 | 1853 AUD | no | no |
| FY2025 | COMPARABLE | 1650-1800koz | 1630-1660koz | 1850-2100/AUD | 2100-2200/AUD | 2 | 1634 | 2163 AUD | no | no |
| FY2026 | COMPARABLE | 1700-1850koz | >1500koz (open-ended) | 2300-2700/AUD | 2600-2800/AUD | 3 | 1543 | 2698 AUD | MISS | no |

**3-year miss count:** original=1, final=0. **Candidate-rule trigger:** original=False, final=False.

FY2026's final production guidance is a one-sided lower bound only
("above 1.50Moz") — the upper bound was never restored before the actual was
reported. The production-miss test is still computable from the lower bound
alone.

### OBM — Ora Banda Mining

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 67-73koz | 67-73koz | 2200-2400/AUD | 2275-2475/AUD | 1 | 69.932 | 2767 AUD | **MISS** | **MISS** |
| FY2025 | COMPARABLE | 100-110koz | 95koz | 1975-2125/AUD | 2600/AUD | 4 | 92.399 | 2693 AUD | **MISS** | no |
| FY2026 | COMPARABLE | 140-155koz | 140-155koz | 2800-2900/AUD | 3250-3350/AUD | 1 | 140.949 | 3496 AUD | **MISS** | no |

**3-year miss count:** original=3, final=1. **Candidate-rule trigger: original=True, final=False.**

The most dramatic goalpost-moving case in the cohort: AISC missed original
guidance in every one of the three years, but only FY2024's revision was
insufficient to absorb the actual — FY2026's actual (A$3,496/oz) even beat
the *raw* revised upper bound (A$3,350/oz) but stayed inside the rule's 5%
buffer (A$3,517.50).

### OGC — OceanaGold Corporation

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| CY2023 | COMPARABLE | 460-510koz | 460-480koz | 1425-1525/USD | 1550-1650/USD | 2 | 477.313 | 1587 USD | no | no |
| CY2024 | COMPARABLE (orig.) / UNRESOLVED (final) | 510-570koz | 480-500koz† | 1475-1600/USD | 1725-1825/USD† | 2 | 488.8 | 1777 USD | MISS | UNRESOLVED† |
| CY2025 | COMPARABLE | 450-520koz | 450-520koz | 1900-2050/USD | 1900-2050/USD | 0 | 497.6 | 1966 USD | no | no |

**3-year miss count:** original=1, final=0 (provably — see †). **Candidate-rule
trigger:** original=False, final=False.

† **Correction (2026-08-24 compliance remediation):** CY2024's final
(revised) guidance claims (`claim:sha256:067673975...` production,
`claim:sha256:dbca4dc5c...` AISC) rested solely on a document hosted at
`filecache.investorroom.com`. That host was reclassified from a blanket T2
rule to the T4 default when `investorroom.com`/`q4cdn.com` were removed as
generic shared-CDN authority rules (§10) — a shared, multi-tenant IR-hosting
CDN is not an issuer-controlled route, and no equivalent copy at an admissible
host was found. Per the binding tier table, T4 evidence cannot support an
active claim, so both claims are now `UNRESOLVED`; the 480-500koz/
US$1,725-1,825/oz figures are retained in the ledger for audit only. This
does **not** reopen the candidate-rule result: CY2023 and CY2025 are both
determinately "no miss" on final guidance, so even crediting CY2024 as a
worst-case miss caps the final-basis 3-year count at 1, below the 2-year
threshold — the same reasoning already applied to BGL, VAU and WAF elsewhere
in this report. Original CY2024 guidance (`assets.oceanagold.com`, T2,
unaffected) is untouched.

### PNR — Pantoro Gold

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | MISSING_GUIDANCE | — | — | — | — | 0 | 71.37 | — | MISSING_GUIDANCE | MISSING_GUIDANCE |
| FY2025 | COMPARABLE (prod.) / MISSING_ACTUAL (AISC) | 90-110koz | 85.5-94.5koz | 1710-2090/AUD | 1980-2420/AUD | 2 | 84.564 | — | **MISS** | MISSING_ACTUAL |
| FY2026 | COMPARABLE (prod.) / MISSING_ACTUAL (AISC) | 100-110koz | 86-92koz | 1950-2250/AUD | 1950-2250/AUD | 1 | 77.408 | — | **MISS** | **MISS** |

**3-year miss count:** original=2, final=—. **Candidate-rule trigger: original=True**, final=CANNOT_DETERMINE.

Pantoro has never published a single full-year AISC actual in any primary
source examined (only quarterly figures) — a structural disclosure gap, not a
one-off omission, affecting every year in the window.

### PRU — Perseus Mining

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 491-517koz | 491-517koz | 1000-1100/USD | 1000-1100/USD | 0 | 509.977 | 1053 USD | no | no |
| FY2025 | COMPARABLE | 469.709-504.709koz | 469.709-504.709koz | 1250-1280/USD | 1250-1280/USD | 0 | 496.551 | 1235 USD | no | no |
| FY2026 | COMPARABLE | 400-440koz | 400-440koz | 1460-1620/USD | 1600-1760/USD | 1 | 404.998 | 1750 USD | MISS | no |

**3-year miss count:** original=1, final=0. **Candidate-rule trigger:** original=False, final=False.

### RMS — Ramelius Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 250-275koz | 285-295koz | 1550-1750/AUD | 1550-1650/AUD | 4 | 293.033 | 1583 AUD | no | no |
| FY2025 | COMPARABLE | 270-300koz | 290-300koz | 1500-1700/AUD | 1550-1650/AUD | 2 | 301.664 | 1551 AUD | no | no |
| FY2026 | COMPARABLE | 185-205koz | 185-205koz | 1700-1900/AUD | 1900-2050/AUD | 2 | 192.182 | 1983 AUD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

RMS beat guidance in all three years on every reading. FY2026's asset base
changed materially within the year (Edna May divested, Dalgaranga added via
the Spartan Resources acquisition); each individual year is internally
consistent, but the three-year series does not reflect one stable portfolio.

### RRL — Regis Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 415-455koz | 415-455koz | 1995-2315/AUD | 1995-2315/AUD | 0 | 417.713 | 2286 AUD | no | no |
| FY2025 | COMPARABLE | 350-380koz | 350-380koz | 2440-2740/AUD | 2440-2740/AUD | 0 | 373 | 2531 AUD | no | no |
| FY2026 | COMPARABLE | 350-380koz | 350-380koz | 2610-2990/AUD | 2610-2990/AUD | 0 | 379.05 | 2945 AUD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

Guidance was reaffirmed unchanged at every quarterly checkpoint in all three
years — zero formal revisions, the only company in the cohort with that
record.

### RSG — Resolute Mining

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| CY2023 | COMPARABLE | 350koz | 330-340koz | 1480/USD | 1480/USD | 1 | 330.994 | 1469 USD | **MISS** | no |
| CY2024 | COMPARABLE | 345-365koz | 345-365koz | 1300-1400/USD | 1300-1400/USD | 0 | 339.869 | 1476 USD | **MISS** | **MISS** |
| CY2025 | COMPARABLE | 275-300koz | 275-285koz | 1650-1750/USD | 1750-1850/USD | 2 | 277.236 | 1843 USD | **MISS** | no |

**3-year miss count:** original=3, final=1. **Candidate-rule trigger: original=True, final=False.**

Missed original guidance in all three years and would trigger the rule on
that basis alone; two of the three misses are absorbed once each year's own
revised (final) guidance is used instead. CY2024's AISC miss survives against
final guidance by a $6/oz margin (actual $1,476 vs. the 5%-tolerant ceiling of
$1,470); CY2025's original-guidance AISC miss is a $5.50/oz margin.

### VAU — Vault Minerals

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 195-215koz | 195-215koz | 1850-2100/AUD | 1850-2100/AUD | 0 | 210.940 | 2043 AUD | no | no |
| FY2025 | COMPARABLE | 390-430koz | 390-410koz | 2250-2450/AUD | 2250-2450/AUD | 2 | 385.232 | 2422 AUD | no | no |
| FY2026 | COMPARABLE | 332-360koz | 332-360koz | 2650-2850/AUD | 2650-2850/AUD | 0 | 336.54 | 2924 AUD | no | no |

**3-year miss count:** original=0, final=0. **Candidate-rule trigger:** original=False, final=False.

**Correction (2026-08-24):** FY2024 guidance was issued for King of the Hills,
and the lodged June quarterly reports the matching full-year asset actual of
210,940oz produced at A$2,043/oz AISC. Both are inside the raw guidance ranges.
The earlier analysis incorrectly selected the later statutory group-sales
figure, which included a 12-day Silver Lake stub after the 19 June merger. Once
the already-published scope-matched actual is used, no reconciliation is needed.

### WAF — West African Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| CY2023 | COMPARABLE | 210-230koz | 210-230koz | <1175/USD | <1175/USD | 0 | 226.823 | 1136 USD | no | no |
| CY2024 | COMPARABLE | 190-210koz | 190-210koz | <1300/USD | <1300/USD | 0 | 206.622 | 1240 USD | no | no |
| CY2025 | COMPARABLE (prod.) / MISSING_GUIDANCE (AISC) | 290-360koz | 290-360koz | not guided | not guided | 0 | 300.383 | 1488 USD | no (prod.) / MISSING_GUIDANCE (AISC) | same |

**3-year miss count:** original=0, final=0 (both provably false regardless of the CY2025 AISC gap — production alone cannot supply the second miss needed to trigger). **Candidate-rule trigger:** original=False, final=False.

WAF's own CY2025 guidance table explicitly marks Group AISC "not guided" —
this is the issuer's own word, not an extraction failure.

### WGX — Westgold Resources

| FY | Status | Orig. production guid. | Final production guid. | Orig. AISC guid. | Final AISC guid. | Revisions | Prod. actual (koz) | AISC actual | Miss (orig) | Miss (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| FY2024 | COMPARABLE | 245-265koz | 220-230koz | 1800-2000/AUD | 2100-2300/AUD | 2 | 227.237 | 2178 AUD | **MISS** | no |
| FY2025 | COMPARABLE | 400-420koz | 330-350koz | 2000-2300/AUD | 2400-2600/AUD | 2 | 326.384 | 2666 AUD | **MISS** | no |
| FY2026 | COMPARABLE | 345-385koz | 345-385koz | 2600-2900/AUD | 2600-2900/AUD | 0 | 387.354 | 2841 AUD | no | no |

**3-year miss count:** original=2, final=0. **Candidate-rule trigger: original=True, final=False.**

Every figure in this record was independently re-verified by the coordinator
against the archived primary PDF text (four figures spot-checked
character-for-character: FY24 and FY25 original/revised guidance excerpts,
and the Group Gold Produced/AISC rows in the FY25 Annual Report's FY24
comparative column) — all matched exactly.

## 4. Original vs. final guidance — the goalpost-moving result

This is the single most consequential finding for the candidate rule. At the
5% materiality threshold specified in the brief:

| Basis | Names triggering (≥2 of 3 miss-years) |
|---|---|
| **Original guidance** | **EMR, OBM, PNR, RSG, WGX — 5 names** |
| **Final (most recently revised) guidance** | **none — 0 names** (PNR is CANNOT_DETERMINE, not a trigger, owing to its structural AISC-actual disclosure gap, §6) |

**Current-book relevance:** of these 5 names, only **OBM, PNR and WGX** are
current SJGV live constituents (SJGV v1.8 build, `weights.json`, generated
2026-08-23T22:23:35Z). EMR and RSG are excluded from the live book entirely by
Gate 1 Tier A (no Tier A-jurisdiction production — Cambodia and Mali
respectively) and are not reachable by an execution-risk cap regardless of
this study's finding; a future amendment's practical effect, if adopted
against original guidance, would be limited to OBM, PNR and WGX.

Every one of the five original-guidance triggers is explained by formal
downward revisions that were large enough to convert what would have been a
miss into a pass. OBM is the extreme case: AISC missed *original* guidance in
all three years running, yet the candidate rule would apply the cap to zero of
those years if evaluated against each year's own revised guidance instead.

This is not a data artifact — it is what the rule, applied literally, would
measure. A future amendment must decide explicitly which vintage of guidance
it targets, because the two choices produce materially different cohorts.

### 4.1 Disclosure-failure overlay

**Committee interpretation adopted in SJGV v2.0 on 24 August 2026:** failure to
publish the required full-year production or AISC guidance for a producing
period is one failure on both the original and revised bases. A year counts
once. Genuine pre-production history remains outside the denominator. Where a
company has fewer than three producing years, a 100% original-basis failure
rate is a hard fail; a first producing year with no guidance is therefore 1/1,
not 1/3 and not a provisional pass. A repository acquisition gap is never
charged to the issuer.

This is not a failed-fetch proxy. For BC8, BTR, CYL, MEK, PNR and WAF, the
knowledge store retains complete, unfiltered ASX announcement indexes for each
full calendar year from 2023 through 2025 and year-to-date indexes through
23 August 2026. The relevant annual reports, quarterlies, guidance releases and
presentations were then inspected. The strongest cases are affirmative issuer
statements: BC8 said AISC was "not presented" and repeatedly deferred annual
guidance; PNR said it was "not providing full year guidance for FY 2024" and
did not publish a full-year AISC actual in the window; WAF marked Group AISC
"not guided". BTR's complete lodgement sweep contains no annual guidance in
three operating years, despite a stated intention to publish maiden CY25
guidance. Bellevue's FY2024 producing period carried production guidance but no
required AISC guidance. CYL's gap is confined to FY2024. MEK failed to publish
bounded annual guidance in its sole completed producing year.

| Treatment | Companies |
|---|---|
| **Hard fail — exclude** | BC8, BGL, BTR, EMR, MEK, OBM, PNR, RSG |
| **At least 5% cap; unresolved upward** | CYL, NEM |
| **5% cap** | WAF, WGX |
| **Pass, complete evidence** | AEM, CMM, EVN, GMD, NST, PRU, RMS, RRL, VAU |
| **Limited-history pass (0/2)** | GGP |
| **Unresolved repository evidence; no issuer penalty** | OGC |

For the live book, BGL, OBM and PNR are excluded; CYL and WGX are capped at 5%.
The complete machine-readable classification is `data/guidance_delivery.json`.

## 5. Sensitivity table

Miss-year determination recomputed at three materiality thresholds against
**original** guidance, independently, from the same registered claims (a
Python script re-derives every boolean from the raw bounds — it does not trust
any agent's self-reported miss flag). 53 comparable company-years.

| Threshold | Miss-years (of 53) | Names that would trigger (≥2 of 3) |
|---|---:|---|
| 0% (nominal, no tolerance) | 27 | EMR, NEM\*, NST, OBM, OGC, PNR, RSG, VAU, WGX (9 names) |
| **5% (the brief's rule)** | **19** | **EMR, OBM, PNR, RSG, WGX (5 names)** |
| 10% | 9 | OBM (1 name) |

\* NEM shows 2 nominal misses at 0% tolerance across its 2 comparable years,
but CY2023 remains NOT_COMPARABLE regardless of threshold (a scope break, not
a materiality question), so its status stays CANNOT_DETERMINE at every
threshold under the disciplined 3-year rule — listed here only because the 0%
column is a raw count over comparable years, not a trigger determination.

At 0% tolerance, four more names show at least a nominal breach (NEM, NST,
OGC, VAU) that the 5% buffer absorbs. At 10%, the cap would apply only to the
worst single offender in the cohort (OBM). The rule is genuinely sensitive to
where the materiality line is drawn — not just to which guidance vintage is
used.

## 6. Missing and non-comparable observations, in full

**INSUFFICIENT_HISTORY (5 company-years)** — commercial production began too
recently for a first completed year of guidance-vs-actual to exist:

- BC8 FY2024 — Paulsens mid-refurbishment; zero group gold production/sales.
- BGL FY2024 — Bellevue Gold Project reached commercial production 7 May
  2024; no full-year guidance was ever issued for FY2024.
- GGP FY2024 — pre-Telfer-acquisition; Havieron still in JV development.
- MEK FY2024, FY2025 — Murchison Gold Project pre-production; first gold
  poured 1 July 2025 (the first day of FY2026).

**MISSING_GUIDANCE (9 company-years)** — actuals may exist, but no formal
bounded full-year figure was ever issued for the missing limb:

- BC8 FY2025, FY2026 — no bounded full-year production or AISC guidance ever
  issued; AISC is explicitly stated as "not presented due to JV accounting."
- BTR FY2024–FY2026 — Ore Purchase Agreement producer (ore sold to Genesis
  Minerals' mill); no full-year gold-ounce/AISC guidance in the sense this
  study requires at any point in the window.
- CYL FY2024 — no formal FY2024 guidance found across ~10 documents examined.
- MEK FY2026 — first year of production; no bounded annual figure issued
  (only life-of-mine and monthly ramp-up targets).
- PNR FY2024 — Pantoro explicitly stated on 30 Oct 2023 it was "not providing
  full year guidance for FY 2024."
- WAF CY2025 (AISC limb only) — the issuer's own guidance table states Group
  AISC "not guided"; production guidance for the same year is fully
  comparable.

**NOT_COMPARABLE (1 company-year)** — guidance and actual span a scope change
with no issuer reconciliation:

- NEM CY2023 — the Newcrest merger (completed 6 Nov 2023) added ~2 months of
  Newcrest production/cost to a guidance figure set on a standalone
  pre-merger basis.
**Additional structural AISC-actual gaps inside otherwise-comparable years**
(recorded as MISSING_ACTUAL for that limb, not folded into the counts above):
PNR has never published a single full-year AISC actual in any primary source
across the entire three-year window — a persistent disclosure pattern, not a
one-off gap, matching this repository's own prior note that "BC8's unpublished
AISC" is a disclosure gap rather than a sourcing failure (`data/README.md`).

## 7. Sensitivity-adjusted candidate list — no portfolio implementation

At the brief's specified 5% materiality threshold, against **original**
guidance, the candidate rule (`≥2 of the last 3 completed years missed`) would
apply the proposed 5% cap to:

**EMR, OBM, PNR, RSG, WGX**

Against **final** (most-recently-revised) guidance, the same rule applies the
cap to **no name** in the cohort (PNR is undetermined, not a trigger, owing to
its AISC-actual disclosure gap).

This is a candidate list only. No weight, cap, or portfolio change has been
applied anywhere in this repository as a result of this study — `data/`,
`config.json`, and `build_index.py` are unmodified, and every registered claim
carries `"projectable": false` with `"decision.code":
"ARCHIVED_POINT_IN_TIME_OBSERVATION"`.

## 8. Coverage count and determinability

- **Comparable company-years (status tag): 54 / 69 required (78.3%).**
  **Correction (2026-08-24):** this status-tag count is not the same as the
  number of years with a clean Boolean result, and the original text
  conflated them. Two of the 54 `COMPARABLE`-tagged years are only partially
  boolean: **CYL FY2026** is comparable on final guidance but `NOT_COMPARABLE`
  on original guidance (a scope break — the original guidance included the
  since-divested Henty mine), and **PNR FY2025** is comparable on production
  but `MISSING_ACTUAL` on AISC (Pantoro has never published a full-year AISC
  actual). Recomputed directly from the appendix: **52 / 69** company-years
  have an actual Boolean `miss_year` result on *both* the original and final
  guidance bases, and **51 / 69** have all four limbs (original production,
  original AISC, final production, final AISC) as determined values rather
  than a non-comparable/missing state on at least one of them. Neither
  correction changes any candidate-rule trigger in §4/§7 — CYL and PNR were
  already excluded from the trigger list on other, correctly-identified
  grounds (CANNOT_DETERMINE for both).
- **Companies for which the candidate-rule trigger is determinable without
  assumption, against ORIGINAL guidance: 17 / 23** (True: EMR, OBM, PNR, RSG,
  WGX; False: AEM, CMM, EVN, GGP, GMD, NST, OGC, PRU, RMS, RRL, VAU, WAF —
  12 names). CANNOT_DETERMINE: BC8, BGL, BTR, CYL, MEK, NEM (6 names).
- **Companies for which the trigger is determinable against FINAL guidance:
  18 / 23** (True: none; False: all 18 determinable names). CANNOT_DETERMINE:
  BC8, BTR, MEK, NEM, PNR (5 names).
- Six companies (BC8, BTR, MEK — zero comparable years each; plus BGL, CYL,
  NEM with partial coverage that cannot resolve to a trigger under original
  guidance) have **no usable candidate-rule evidence at all** for at least one
  guidance basis, most because they are recently-producing or structurally
  non-disclosing, not because research was incomplete.

## 9. Assessment: is the evidence sufficient for a binding amendment?

**Not yet, as specified, without further committee decisions.** The evidence
that exists is solid: every comparable-year figure above traces to a primary
lodged filing or its regulator/exchange equivalent, with an exact locator and
verbatim excerpt registered in the claim ledger; a deterministic script
independently re-derived every miss/trigger boolean from the raw sourced
numbers and found zero arithmetic disagreements with the research agents'
self-reported results across all 69 company-years (one self-reported
CANNOT_DETERMINE, on BGL's final-guidance trigger, was itself an avoidable
logical error rather than a data problem, and is corrected in §3); and a
resolver defect that had misattributed 8 of 299 registered claims to the wrong
(but same-value) evidence document was caught, root-caused, and corrected with
an explicit supersession before this report was finalised. **Correction
(2026-08-24):** the original text called this an `EXPLICIT_CORRECTION`
supersession; that literal string does not appear anywhere in
`knowledge/claims.jsonl`. All eight corrections, like every other claim this
study registered, carry `decision.code: ARCHIVED_POINT_IN_TIME_OBSERVATION`
— the distinguishing evidence of the correction is each claim's own
`superseded.reason` text, not a separate code.

Three specific reasons the evidence base cannot yet support a *binding*,
cohort-wide amendment:

1. **Coverage is materially incomplete.** Only 76.8% of required company-years
   are comparable, and six candidates — a quarter of the cohort — have no
   usable trigger evidence at all, mostly because they began production too
   recently to have a track record or because the issuer structurally
   withholds full-year AISC. A binding rule needs an explicit answer for what
   happens to an untested or non-disclosing name; this study is instructed
   not to supply one ("do not infer a value or recommend how the future
   engine should cap an untested name" — brief §"Use these states").
2. **The rule is acutely sensitive to which guidance vintage it targets.** Five
   names trigger against original guidance; zero trigger against each
   company's own final guidance. A rule that a company can escape simply by
   revising its own guidance downward before the actual lands achieves very
   little as a check on execution risk — but a rule that holds a company to
   its *original* guidance forever also penalises legitimate, well-disclosed
   revisions (M&A, divestment, external cost shocks) alongside genuine
   execution failure. §4 makes this trade-off visible; it does not resolve it.
3. **Several triggers sit on narrow, disclosure-noise-sized margins.** RSG's
   CY2024 final-guidance AISC miss survives by $6/oz against a $1,470 ceiling;
   its CY2025 original-guidance miss is a $5.50/oz margin. OBM's FY2026
   actual beat its own raw revised AISC ceiling and only remains a "no miss"
   because of the rule's 5% buffer. A binary cap applied at these margins
   would be sensitive to rounding and restatement differences between a
   company's unaudited quarterly figure and its later audited annual report —
   several of which are recorded in the appendix's `gaps` fields as
   immaterial but real (e.g., RSG's 330,994 vs. 330,992 CY2023 comparative).

None of this reflects a research shortfall. It reflects what a complete,
carefully verified evidence base actually shows: the rule as specified
produces a defensible-looking candidate list that collapses to nothing under
a small, principled change in which guidance figure it reads. That is
precisely the kind of thing this brief was commissioned to surface before a
binding amendment is drafted, not after.

## 10. Validation

As originally published (24 August 2026):

```text
.venv/bin/python -m compileall -q build_index.py nav_model.py tools   clean
.venv/bin/python -m unittest discover -s tests -t .                   130 tests, OK
.venv/bin/python tools/gaps.py                                        unchanged from baseline
.venv/bin/python tools/provenance.py                                  unchanged from baseline
.venv/bin/python tools/config_audit.py --strict                       clean, 62 parameters
.venv/bin/python tools/kb.py audit --strict                           1,222 documents, 717 claims, 0 errors
.venv/bin/python tools/kb.py backfill-claims --dry-run                idempotent — reproduces the ledger exactly
```

After the 2026-08-24 compliance remediation below:

```text
.venv/bin/python -m compileall -q build_index.py nav_model.py tools   clean
.venv/bin/python -m unittest discover -s tests -t .                   150 tests, OK
.venv/bin/python tools/gaps.py                                        unchanged from baseline
.venv/bin/python tools/provenance.py                                  unchanged from baseline
.venv/bin/python tools/config_audit.py --strict                       clean, 62 parameters
.venv/bin/python tools/kb.py audit --strict --deep                    1,222 documents, 741 claims, 0 errors
.venv/bin/python tools/kb.py backfill-claims --dry-run                idempotent — reproduces the ledger exactly
git diff --check                                                      clean
```

387 new source documents were archived (`tools/kb.py ingest-file`), bringing
the store from 538 to 1,222 documents (684 net new). 299 new claims were
registered (`tools/kb.py register-claim`), bringing the ledger from 410 to
717 (307 net new at first publication); the compliance remediation below
registered a further 24, for 741 total (331 net new since the store's
23 August load). All are `"projectable": false` with `"decision.code":
"ARCHIVED_POINT_IN_TIME_OBSERVATION"` (**correction, 2026-08-24:** the
originally-published text said `held_from_projection: true`, which is not a
field the stored claim record carries — see the note at the top of this
report). `tools/kb.py`'s host-authority table was extended with three new
rules (`www.sec.gov` → T1 regulator lodgement; `q4cdn.com` and
`investorroom.com` → T2 shared IR platforms; `oceanagold.com` added to the
issuer-host table) to correctly classify the non-ASX evidence this study
required — a source-plane maintenance change, not a methodology change. No
file under `data/` was touched; `build_index.py` was not run as part of this
study or its remediation.

**2026-08-24 compliance remediation.** A post-publication review found the
`q4cdn.com`/`investorroom.com` T2 rules above to be a genuine authority-
classification defect: both are shared, multi-tenant IR-hosting CDNs, not an
issuer-controlled route, and a rule for either cannot distinguish the
legitimate tenant from a lookalike host squatting on the same suffix
(`evilq4cdn.com` matches the same regex). Both were removed; a document
served from either host now falls through to the T4 default unless an
issuer-controlled route or exact filing equivalence is separately established
(`www.sec.gov` and the `oceanagold.com` issuer-host mapping are untouched).
Regression tests now cover this (`HostAuthorityTest`,
`tests/test_kb_integrity.py`). The review also found and fixed:

- **Two systemic document-verification gaps**, not data-entry errors: the
  issuer-detection heuristic recognised only `ASX:TICKER`-style mentions, so
  every SEC- or TSX-lodged filing in the store failed issuer verification
  regardless of content (generalised to other exchange prefixes and to the
  issuer's own legal name from `data/companies.json`); and `reverify`
  silently dropped `subjects` for any ticker without an `ISSUER_HOSTS` entry
  (fixed via `known_tickers()`, plus a claims-jsonl cross-reference and a
  title-based fallback to recover subjects the defect had already stripped).
  Together with SEC-accession-number backfill, an ASX-research-API
  self-describing exception, an ordinal-date format, and a reporting-period
  extractor, these resolved `verified.issuer`/`verified.dates` gaps on all
  180 documents this study's claims cite, and reduced whole-store gaps from
  289/310 to 87/198 — without touching a single record by hand.
- **Three calculated values registered as bare `POINT` facts** with no
  `derivation` record: EMR's FY2026 production and AISC actuals (summed/
  cost-weighted from four quarterly figures) and BTR's FY2024 production
  actual (a 50% JV-interest attribution). All three are now derived claims
  naming their quarterly/JV-total dependencies, formula, rounding and output
  unit; values are unchanged. See §3.
- **EMR's FY2025 "original" guidance was never genuine original guidance** —
  it silently annualised a quarterly rate the issuer explicitly said was not
  yet formal. Corrected; see §3.
- **A live consequence of the host-authority fix:** OGC's CY2024 final
  guidance became `UNRESOLVED` once its sole evidence was reclassified T4 —
  the only place in this report where the authority fix changed a claim's
  admissibility, not just its historical record. See §3 and §8. No candidate-
  rule trigger changes as a result (§4, §7).
- Two documentation-accuracy corrections with no ledger effect: the
  `held_from_projection: true` and `EXPLICIT_CORRECTION` phrasings above
  do not correspond to any field or code actually stored on a claim.
- The universe/constituent-count correction in §1, and the coverage-count
  precision correction in §8.

Five supporting facts the report relied on in prose without a registered
claim were also registered: fiscal year-ends for AEM, NEM, OGC, RSG and WAF,
and MEK's first-gold-production announcement (the last of which surfaced an
unverified precision in this report's own "1 Jul 2025" date — see §1). A
full pass registering every fiscal year-end, producer-status, merger/
divestment and scope-change fact this report relies on across all 23
companies was not completed in this remediation and remains open work — see
the note at the end of this section.

None of the numeric candidate-rule findings in §4/§5/§7 changed. `data/`,
`config.json`, and index weights were not touched by this remediation, per
the research brief's and the remediation's own scope limits.

**Known remaining gap, stated rather than hidden:** this remediation did not
attempt an exhaustive registration of every fiscal-year-end, producer-status,
merger/divestment-date and scope-change fact this report relies on in prose
across all 23 companies (only the six listed above), and did not attempt to
resolve the 24 supporting documents (of 180 this report's claims cite) that
still lack a publisher/exchange identifier — 19 are direct-fetched ASX PDFs
that were never cross-referenced against the exchange's own per-ticker index
(a distinct feature from anything built during this pass), and 5 are
OceanaGold/mirror documents with no applicable identifier scheme. Both are
lower-severity than the issuer/date-verification and derivation defects
above: they affect citation completeness, not the admissibility or
correctness of an active claim, and `tools/kb.py audit --strict` already
passes cleanly regardless. A dedicated follow-up pass is the right scale for
closing them, not a further extension of this one.

## Appendix

`docs/guidance-delivery-candidates-2026-08-24.json` — machine-readable, one
entry per company, each year carrying `claim_id` references (not raw values)
into `knowledge/claims.jsonl` for every guidance-chain and actual figure,
alongside the coverage status, miss/trigger booleans, and the `gaps`/
`open_questions` recorded by the original research pass.
