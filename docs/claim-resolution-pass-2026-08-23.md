# Claim-resolution pass — 23 August 2026

**Purpose:** record the first research pass over the initialized claim ledger,
which set out to resolve every claim in `knowledge/claims.jsonl` whose state was
not `ACCEPTED`, *where the evidence permits*. The binding design is
`source-knowledge-base.md`; the load this pass builds on is
`docs/knowledge-store-initialization-2026-08-23.md`. Nothing here amends the
methodology, and no weight, snapshot or `data/` value was changed.

The pass opened with 3 `PROVISIONAL`, 10 `UNRESOLVED`, 34 `STALE` and 57
pointer-only quarantine records. It closes with **1 `PROVISIONAL`, 10
`UNRESOLVED`, 34 `STALE`, 2 `SUPERSEDED` and 61 quarantine records**, against
363 accepted claims. Two of the three provisional claims were resolved by
primary evidence at an unchanged value. The rest are non-accepted because the
issuers have not published the fact, and §3 says so name by name.

## 1. What changed in the ledger

Eight claims were registered through the new `kb.py register-claim` path (§5).
Two legacy claims were superseded by link, keeping their value, evidence and
decision.

### 1.1 Resolved — T3 provisional replaced by T1 lodged evidence, value unchanged

| Claim | Was | Now |
|---|---|---|
| WGX `aisc_aud_oz` A$2,931/oz | `PROVISIONAL`, T3, no as-of, document-level citation | `SUPERSEDED` by `claim:sha256:b67615fd…` — `ACCEPTED`, T1, as-of 2026-03-31 |
| WGX `undrawn_facilities_aud_m` A$600m | `PROVISIONAL`, T3, `CARRY_FORWARD`, no as-of | `SUPERSEDED` by `claim:sha256:1623da5f…` — `ACCEPTED`, T1, `POINT`, as-of 2026-06-30 |

- **AISC.** The T3 record cited a ceo.ca redistribution of Westgold's March 2026
  quarterly. The lodged original was acquired off the exchange index
  (29 April 2026, `ids_id` 03087291) and states the identical figure on page 1:
  *"All in Sustaining Cost (AISC) of $2,931/oz (excl. ore purchase agreement
  (OPA)) – with AISC including OPA of $3,338/oz"*. Same value, same assertion,
  one tier up, with the own-ore basis and the March-quarter period now in the
  claim scope and the as-of separated from the 29 April publication date.
- **Undrawn facilities.** The carry-forward is retired rather than re-dated. The
  lodged June 2026 Quarterly Report states the position at the measurement date
  directly, page 18 under *Corporate — Debt*: *"Westgold maintains undrawn $600M
  unsecured syndicated revolving facilities"*. The evidence state moves from
  `CARRY_FORWARD` to `POINT` at 30 June 2026 because the amount no longer rests
  on carrying an older limit forward.

Both new claims carry the projection for their `data/companies.json` field, and
the superseded records keep the path in `projection_history` — one field, one
projection basis.

### 1.2 Registered as new dated knowledge, deliberately held out of the projection

Each is `ACCEPTED` with `projectable: false` and
`decision.code = HELD_FOR_REVIEWED_REBALANCE`, because adopting it changes a
live gate or weighting input. Each carries a `projection_pending` block saying
exactly what `data/` would become.

| Claim | Fact | Evidence |
|---|---|---|
| `claim:sha256:0a49c1b0…` | WGX `aisc_aud_oz` A$2,802/oz, as-of 2026-06-30 | June 2026 Quarterly Results, p.1 — *"Q4 FY26 Gold production of 98,854oz Au at AISC of $2,802/oz"*. The same page states FY26 AISC of A$2,841/oz, a different period and therefore a different claim key. |
| `claim:sha256:64ebfb78…` | WGX facility earliest maturity **2029-03-01**, as-of 2026-03-12 | *Westgold Strengthens Balance Sheet Flexibility*, p.3, Appendix A — *"Tranche A $300M March 2029 / Tranche B $200M March 2030 / Tranche C $100M March 2031"*. Normalized to the earliest day of the earliest stated maturity month, per the `term_date` rule in `data/README.md`. |
| `claim:sha256:84b11d74…` | WGX Higginsville 1.6→2.6 Mtpa expansion, approved capital A$145m, as-of 2026-03-10 | *Board Approves Higginsville Expansion Plan*, p.6 — *"…a combined total capital requirement of approximately $145M, representing the investment needed to deliver the 2.6Mtpa processing plant"*. Records the 18 August review as a conflict. |
| `claim:sha256:ea189aca…` | BGL paste plant approved capital A$37.5m (published range A$35–40m, 10% contingency), as-of 2026-02-17 | *Paste plant approval & further hedge book reduction*, p.1. |
| `claim:sha256:ba3f360e…` | BGL paste plant **remaining** capital ~A$30m, as-of 2026-06-30 | 28 July 2026 Quarterly Activities Report, p.7, *FY27 Guidance* — *"the remaining capital expenditure on the paste plant (~$30 million)… substantially complete through the first half of FY27"*. |
| `claim:sha256:7f38e58f…` | BC8 Lakewood 1.2→1.5 Mtpa expansion, approved capital A$20m, as-of 2026-02-26 | *Fingals & Majestic online, Lakewood expansion approved*, p.2 — *"The capital budget for the expansion is $20M"*. |

The last four are project-scoped facts with no matching project record in
`data/`. They are knowledge, not a projection, and §3 explains why none of them
is promoted to a company or Gate 2 horizon amount.

### 1.3 Quarantine — four new pointer-only records

No candidate value is stored. Each points at the document and locator and gives
the reason it was not adopted, linked to the claim it bears on.

| Reason code | Points at |
|---|---|
| `APPROVED_SCOPE_UNDER_REVIEW_NOT_A_HORIZON_AMOUNT` | WGX Higginsville approved capital, p.6 Table 2 |
| `SCOPING_STUDY_ESTIMATE_NOT_APPROVED_SCOPE` | WGX Cue Hub expansion capital, p.11 Table 4 |
| `PARTIAL_ENUMERATION_CANNOT_TOTAL_A_SCOPE` | BGL FY27 non-sustaining itemisation, p.7 |
| `SINGLE_SCOPE_TOTAL_CANNOT_BOUND_THE_PROGRAMME` | BC8 Lakewood approved capital, p.2 |

## 2. Documents

Fifty-eight artifacts were acquired through `kb.py asx-acquire`, off the already
archived exchange index, and the store went from 480 to 538 documents. Every one
is T1 `exchange.lodgement` with the index row, the `displayAnnouncement` address
and the resolved PDF address recorded. The load-bearing additions:

- **WGX** — March 2026 Quarterly Results (the lodged original of the T3 copy),
  March and June 2026 quarterly webcast presentations, *Board Approves
  Higginsville Expansion Plan* (10 Mar 2026), the April 2025 *Higginsville
  Expansion Plan* study, *Cue Hub Expansion to 1.7Mtpa in FY28* (5 Aug 2026),
  two 2026 Corporate Updates, the 3-Year Outlook webinar, FY26 Guidance,
  September and December 2025 quarterlies.
- **BGL** — *Paste plant approval & further hedge book reduction* (17 Feb 2026),
  the 2026 Diggers & Dealers, Macquarie, Canaccord and Northern Hemisphere
  presentations, the March 2026 production update, FY25 and FY26 quarterly
  activities and cash-flow reports.
- **BC8** — *Fingals & Majestic online, Lakewood expansion approved*
  (26 Feb 2026), *Coyote Discovery and Growth Plan 2026*, the July 2026 Lakewood
  updates, the June 2026 quarterly results presentation, the 2025 and 2026
  Diggers presentations, investor presentations and quarter snapshots.

Reused without a request: the June 2026 quarterly, *Westgold Strengthens Balance
Sheet Flexibility*, the Fletcher Ore Reserve release, the 28 July 2026 BGL
quarterly and the BC8 June 2026 activities report were already held.

An earlier acquisition attempt lost DNS partway and recorded 25 `MISSING_OBJECT`
events with booked retry dates; all 25 were re-fetched successfully once the
connection returned, and a later success releases the block.

## 3. What correctly remains non-accepted

### 3.1 WGX `gold_nav_share` = 1.0 — stays `PROVISIONAL`

No lodged filing states a NAV share by commodity. What the primary record does
say is that Westgold describes itself as a gold producer; that FY25 silver
revenue was A$5.155m against total revenue from contracts with customers of
A$1,360.299m, or 0.38% (FY25 Appendix 4E and Annual Financial Report, p.56); and
that at 30 June 2026 it held A$208m of listed equity investments, not all of
them gold (June 2026 quarterly, p.18). The gate is a purity floor at 0.75 and gold is
plainly the whole operating business, so the claim is not in doubt directionally
— but "1.0" exactly is a repository judgement, not a sourced fact, and this pass
will not manufacture certainty to clear a state. Re-expressing the field as an
issuer-sourced bound would be a field-policy change and needs separate
authorization.

### 3.2 WGX execution capital — four claims stay `UNRESOLVED`

The 10 March 2026 board approval is a real, finite, costed scope: A$145m,
Class-2 DFS, construction readiness Q1 FY27, practical completion Mid FY28 —
entirely inside the Gate 2 window. It is registered as knowledge (§1.2). It
cannot become a company or within-horizon amount, because the 18 August 2026
Fletcher Ore Reserve release, p.8, says Westgold *"has accelerated definitive
design work on a 4Mtpa expansion case and is reviewing the optimal timing and
scope of the previously approved 2.6Mtpa stage"*, that the approach *"may extend
the period that Higginsville operates at its current 1.6Mtpa capacity"*, and
that capital is being prioritised to the Murchison first.

That matters in both directions, which is the point. The A$145m is not a floor,
because the stage may be deferred; and it is not a ceiling either, because the
alternative under study is **larger and uncosted**. Spend to date on the scope is
not separately disclosed — the June 2026 quarterly reports group non-sustaining
capital only. The Cue Hub A$22m is scoping-study level with no FID. Contracted
capital commitments within one year are disclosed at A$28.095m (30 June 2025)
and A$44.904m (31 December 2025), principally for the purchase and maintenance
of plant and equipment, with no project split — and neither date is the
30 June 2026 measurement date.

### 3.3 BGL execution capital — two claims stay `UNRESOLVED`

The paste plant now has a proper bridge: A$35–40m approved on 17 February 2026,
~A$30m stated as remaining at the FY27 guidance, substantially complete in
H1 FY27. Both are registered (§1.2). Neither resolves the company field, and the
reason is one word in the source: the FY27 sentence begins *"Non-sustaining
capital **includes**…"*. An expressly partial enumeration cannot be summed into a
total, and summing it anyway would understate remaining execution capital in the
favourable direction. FY28 non-sustaining capital is not guided at all, so the
one-year programme scope has no completion total either. The paused 1.0→1.6 Mtpa
mill expansion is not quantified as a residual commitment anywhere in the lodged
record.

### 3.4 BC8 execution capital — four claims stay `UNRESOLVED`

One correction to the record: a total **was** disclosed for the Lakewood
expansion — A$20m, board-approved 26 February 2026, approvals in place, first
ore through the expanded mill scheduled for the March 2027 quarter. The claim
note that said no total was disclosed rested on documents this pass acquired for
the first time.

It still does not resolve the four claims. A$20m covers one scope of three:
Coyote and Mt Clement are pre-FID with no published total. BC8 incurred A$131.2m
of growth capital in FY26 without publishing scope totals for it, so treating
A$20m as a company ceiling would understate execution capital in the favourable
direction. And the 30 July 2026 quarterly makes the timing conditional — *"The
timing of the expansion will progress in line with the planned ramp-up of mining
activities at Fingals and Majestic"* — while p.1 states the company *"is
reviewing aspects of the growth strategy which will be revisited at an
appropriate time"*. No Gate 2 coverage period is established. The half-year
report states *"There are no material contractual commitments as at 31 December
2025 (30 June 2025: $nil) not otherwise disclosed"* — both dates pre-date the
30 June 2026 measurement date, so that is not a sourced zero at the basis date
either. BC8 remains separately blocked on undisclosed AISC.

### 3.5 The 34 point-in-time market claims stay `STALE`

This is the intended state, not a gap. The 17 August key-statistics bytes were
never archived and the endpoint is live, so nothing can evidence that as-of; the
newer readings are new claims at a new as-of, never a retroactive correction. No
attempt was made to reconstruct the missing endpoint bytes.

The link audit was re-run independently of the research job: **408 of 408 checks
pass on all 34 claims** — every stale claim resolves to an existing successor,
every successor is `ACCEPTED`, shares the subject and predicate, carries a later
as-of, cites a registered document whose object is on disk with an exact JSON
pointer locator, is `projectable: false` under
`ARCHIVED_POINT_IN_TIME_OBSERVATION`, and reconciles to the archived bytes at
`raw ÷ 1,000,000`. Every stale claim carries `supports_claim_as_of: false` and
its value equals what `data/companies.json` projects today. Coverage is
symmetric: 17 tickers × 2 predicates on each side.

## 4. Prepared projection updates — not applied

Nothing below is written. Each requires a separately authorised rebalance.

### 4.1 Market observations, 17 August → 23 August

| Ticker | Predicate | 17 Aug | 23 Aug | Change |
|---|---|---:|---:|---:|
| AUC | `advt_shares_m` | 0.5342 | 1.236089 | **+131.39%** |
| RXL | `advt_shares_m` | 2.0772 | 2.210165 | +6.40% |
| CYL | `advt_shares_m` | 1.2861 | 1.325471 | +3.06% |
| VAU | `advt_shares_m` | 6.3452 | 6.534589 | +2.98% |
| GMD | `advt_shares_m` | 5.8314 | 6.005219 | +2.98% |
| GGP | `advt_shares_m` | 1.8820 | 1.835940 | −2.45% |
| AAR | `advt_shares_m` | 6.6145 | 6.765088 | +2.28% |
| BC8 | `advt_shares_m` | 2.9871 | 2.939259 | −1.60% |
| CMM | `advt_shares_m` | 2.1723 | 2.206219 | +1.56% |
| PNR | `advt_shares_m` | 3.0097 | 3.052544 | +1.42% |
| NST | `advt_shares_m` | 6.0574 | 6.120312 | +1.04% |
| RMS | `advt_shares_m` | 8.0752 | 7.998384 | −0.95% |
| BGL | `advt_shares_m` | 6.4336 | 6.389731 | −0.68% |
| OBM | `advt_shares_m` | 7.2780 | 7.320067 | +0.58% |
| **EVN** | **`shares_out_m`** | **2031.09** | **2041.823440** | **+0.53%** |
| RRL | `advt_shares_m` | 4.5874 | 4.609149 | +0.47% |
| WGX | `advt_shares_m` | 3.4937 | 3.506404 | +0.36% |
| EVN | `advt_shares_m` | 7.5011 | 7.496756 | −0.06% |
| **BGL** | **`shares_out_m`** | **1490.66** | **1491.502384** | **+0.06%** |
| GMD | `shares_out_m` | 1173.31 | 1173.540674 | +0.02% |

The remaining 14 `shares_out_m` observations move by less than 0.002%.

**What consumes them.** `shares_out_m` is total issued shares — not free float —
and feeds market capitalisation, hence enterprise value (`build_index.py`
§ EV assembly) and the §14 Gate 1 cap-weighted variant, which selects the
largest eligible names by full market cap. `advt_shares_m` feeds only the §4.3
capacity report, which the methodology itself records as enforcing nothing at
€1m (methodology §14 sensitivity table: 0.000pp). The AUC and RXL volume jumps
are therefore loud and inert.

**What could actually move.** Only the three share-count changes bear on a
weight, and only EVN's +0.53% is more than rounding. It shifts EVN's market cap,
its EV, its A$/oz rank and its share of the cap-weighted variant. Whether it
changes an eligibility decision cannot be settled from share counts alone: the
Gate 1 cap variant ranks on market cap, which needs prices from the same
session. That is the first co-requisite below.

**Co-requisites for a coherent update.** Adopting the share counts alone would
pair a 23 August share count with a 17 August price. A coherent update needs, in
one transaction: prices from the same archived 23 August session; the `as_of`
dates and source notes on each field; the `asx_api` document key in each
company's `documents` map re-pointed at the archived 23 August responses; and
confirmation that the pending corporate actions have not been implemented —
EVN's Carnaby scheme (copper, which would touch the purity gate) and the
Genesis–Vault scheme affecting VAU and GGP. `shares_out_m` is a raw issued-share
count, so a pending scheme must not be pre-applied to it.

### 4.2 WGX `aisc_aud_oz` — 2931 → 2802

`/companies/7/fields/aisc_aud_oz` currently projects the March 2026 quarter. The
June 2026 quarter (A$2,802/oz) and FY26 (A$2,841/oz) are both lodged and
archived. AISC is a live Gate and score input; choosing which period the field
should carry is a methodology-and-rebalance decision, not a storage one.

### 4.3 WGX `undrawn_facilities_aud_m.term_date` — absent → 2029-03-01

This is the one prepared change that flips a gate mechanic. `creditable_undrawn`
credits an undrawn facility only if its term date reaches the end of the Gate 2
stress window, and an absent date is not credited. All three tranches mature
after 30 June 2028, so recording the term date would make A$600m creditable in
Gate 2 for the first time. The legacy note reasoned that this "decides nothing
because WGX survives on cash alone"; that remains likely, but it is a gate input
and is not adopted here.

### 4.4 Citations that would change even with no value change

`/companies/7/fields/aisc_aud_oz` and `/companies/7/fields/undrawn_facilities_aud_m`
both cite `q3fy26`, the T3 ceo.ca copy. The KB now cites the lodged originals.
Re-pointing the `documents` map is value-neutral, but it is a `data/` edit and
was left for the same reviewed pass.

## 5. The second write path: `kb.py register-claim`

The store had one way to write a claim — `backfill-claims`, which migrates what
`data/` already asserted. Registering a newly researched claim had no sanctioned
path at all, and hand-editing `claims.jsonl` is forbidden. `register-claim`
closes that hole. It takes a JSON spec and writes atomically: a spec that breaks
one rule writes nothing.

What it enforces, and the rule behind each:

- **The evidence is archived first (§2.2).** The `document_id` must resolve in
  `documents.jsonl` and its object must be on disk.
- **Authority is copied from the artifact (§4).** Tier and domain come from the
  document record; a spec cannot assert them.
- **The complete §6.2 record.** An active claim needs an exact locator, a
  verbatim excerpt, and an ISO as-of date kept apart from the publication date.
  A new claim gets none of the legacy migration exceptions.
- **A missing amount stays unresolved (§2.8).** A null value cannot be accepted.
- **Units are identity (§5).** A predicate the schema knows may not be
  registered under a different unit; an AUD scope must state its currency.
- **Precedence runs per key (§5.1).** A lower-tier candidate incompatible with an
  active higher-tier claim is refused and told to quarantine instead. An
  incompatible candidate at the same tier now creates one non-projectable
  `UNRESOLVED` decision containing both evidence paths and retires the former
  projection basis. A second active claim for one key is refused. A claim that
  resolves an `UNRESOLVED` key must supersede it explicitly. Only an explicit
  correction, restatement, or same-as-of update may select a conflicting
  same-tier successor.
- **Supersession is a link (§2.9).** The predecessor keeps its value, evidence
  and decision and gains `superseded_by`. Only the `projection` block moves, to
  `projection_history`, so one field never has two records claiming to be what
  `data/` reads. Targets must share the same subject and predicate and, where
  both claims project, the same projection path. Links are reciprocal, an
  already superseded predecessor cannot be redirected, and an existing stable
  claim identity cannot be overwritten with different content. The strict
  audit verifies those properties on the stored ledger.
- **Quarantine holds pointers (§2.7).** A candidate carrying a value is refused;
  `blocked_by` must name a controlling active claim.
- **Re-running the migration is safe.** `backfill-claims` now owns only what it
  regenerates: registered claims are carried across and supersessions are kept,
  so a second run cannot resurrect a replaced value.

`tests/test_kb_claims.py` covers these in 51 tests, each named for the defect it
prevents; the suite is 124 tests.

## 6. Validation

| Check | Result |
|---|---|
| `compileall build_index.py nav_model.py tools` | clean |
| `unittest discover -s tests -t .` | 124 tests, OK |
| `tools/gaps.py` | unchanged — clean 5, the same provisional producer-commitment register |
| `tools/provenance.py` | unchanged — one non-primary value (AUC `approvals_land_secured`) |
| `tools/config_audit.py --strict` | clean, 62 parameters |
| `tools/kb.py views` | 538 documents, 410 claims, 61 quarantine pointers |
| `tools/kb.py audit --strict --deep` | **0 errors**, 1,614 warnings (all pre-existing classes) |
| `tools/kb.py audit --strict --projection` | **34 errors — the same 34 stale market fields §9 of the load note identified as the cutover blockers.** No new blocker. |
| `tools/kb.py backfill-claims --dry-run` | reproduces the ledger exactly: 410 claims, 61 quarantine records |

The post-review hardening also repaired the 34 legacy stale-market links through
`kb.py backfill-claims`: each accepted successor now names the stale predecessor
that already pointed to it. This changes no claim state, value, or projection.

Two warning counts fell as a side effect: document-level-only citations from 242
to 240, as the two upgraded claims gained exact locators.

## 7. Incidental findings, recorded not acted on

- **WGX `net_debt_aud_m` has a closeable gap.** Its field note says "Westgold
  does not disclose the cash/bullion/investments split, so a cash-only reading
  cannot be constructed" and points at the FY26 annual report. The lodged June
  2026 quarterly, p.18, already gives it: cash A$667m, bullion A$112m, liquid
  investments A$160m, total A$939m, with a further A$48m of escrowed Valiant
  stock excluded from liquid investments. The claim is `ACCEPTED` and outside
  this pass's scope, but the gap it declares can now be closed.
- **No FY26 accounts have been lodged** for WGX, BGL or BC8 as at the
  23 August 2026 index sweep, which covers 1 January to that date. The FY26
  reporting gap recorded on 22–23 August is unchanged. A re-sweep from
  26 August remains worth running; several of these claims resolve with those
  filings.
