# SJGV — Data Layer

Every input the index consumes lives here. The engine (`../build_index.py`)
reads this directory and nothing else. Code and data are separated because the
data changes at every rebalance and the code does not.

## Structure

```
data/
├── README.md          this file — schema and sourcing protocol
├── SOURCES.md         master source log, one section per company
├── companies.json     constituent fundamentals with per-field provenance
├── jurisdictions.json Gate 1 Tier B — sub-national fiscal and tenure data
├── sovereign.json     Gate 1 Tier A — national tests
└── market.json        gold price, FX, and reference decks
```

## Provenance schema

Every company carries a `documents` map and a `fields` map. Each field points at
the document it came from, so any number in the index can be traced to a primary
filing without duplicating the citation on every line.

```jsonc
{
  "ticker": "XYZ",
  "documents": {
    "rr2026": {
      "title": "Annual Mineral Resources and Ore Reserves Statement",
      "url":   "https://...",
      "date":  "2026-06-03",
      "type":  "primary"        // primary | secondary | derived
    }
  },
  "fields": {
    "pp_moz": { "v": 28.419, "doc": "rr2026" },
    "aisc_aud_oz": { "v": 2651, "doc": "q4fy26", "note": "Jun-qtr, not TTM" }
  }
}
```

A field value is normally a number. **One is a boolean:**
`approvals_land_secured`.

### `largest_asset_pp_share` — a quantity where a judgement used to be

The §8.1 single-asset cap reads a sourced float in [0, 1]: **the share of the
company's attributable, Gate-1-eligible Proven & Probable Ore Reserves held at
its single largest asset.** The engine derives the boolean:

```
single_asset = largest_asset_pp_share >= constraints.single_asset_pp_share_threshold   # 0.80
```

This is the third shape the field has had, and the history is the argument for
the current one:

| | Why it went |
|---|---|
| `single_asset_shares`, a `{asset: share}` map | Fed a 20% *asset* cap that sat above the 15% name cap, so it could only bind on an asset two constituents shared. No pair shared one. It never ran. |
| `single_asset`, a hand-set boolean | Fed a cap that binds — but seventeen hand-set booleans are seventeen unrecorded judgement calls. None is visible to `config_audit.py`, none is perturbable by `sensitivity.py`, and two sourcing agents would not have agreed. |
| `largest_asset_pp_share` + a config threshold (18 Aug 2026) | The data layer holds a **measured quantity**; the single judgement lives in `config.json` where it is declared, audited and perturbable. |

**Source the low cases too.** A sourced 0.490 is a recorded result. An absent
share is UNTESTED, derives `None` rather than `False`, and leaves the name at the
full 15% with the cap reported as unapplied.

**Three rules that decide the value**, all in methodology §8.1 — read them before
sourcing a new name, because the arithmetic is trivial and the definition is not:

1. **The asset is one processing plant plus the deposits the mine plan feeds it.**
   Not one mine. Catalyst's nine deposits through the Plutonic mill are one
   asset; Greatland's Havieron is part of Telfer because its ore is trucked 45 km
   to the Telfer plant.
2. **Reserves as disclosed, no adjustment for development status.** A reserve is
   the forward mine plan. Capricorn reads 0.700 because Mt Gibson carries 70% of
   the reserve, even though Karlawinda is 100% of production today.
3. **Where two groupings are both defensible, record the more concentrated one.**
   Ambiguity tightens the cap; it does not let a name escape it.

Record the site-level M&I non-reserve and Inferred split in the `note` while you
are in the R&R table, even though nothing reads it yet — if the committee ever
moves the test onto total claimed ounces, that must not need a second pass.

`type` matters:

- **primary** — company filing, regulator publication, statutory instrument, IMF/World Bank series.
- **secondary** — trade press reporting a primary source. Acceptable, but the primary should replace it before a live rebalance.
- **derived** — computed here from other fields. The derivation is stated in `note`.

A field with no `doc` is not permitted. If a value is unknown, the field is
omitted entirely rather than guessed — the engine then rejects the name and says
which field was missing.

## Derive or fail — the governing rule

**Adopted 17 August 2026. `config.estimation_policy`. This overrides the
imputation section below, which is retained as the worked example of why.**

No field value may be invented. A value may only enter this layer as one of:

| Provenance | Meaning |
|---|---|
| **sourced** | read from a document, which the field cites by key |
| **derived** | computed from other **sourced** fields by an arithmetic identity or an explicitly stated formula — `inferred = mr_total − M&I`, `net_debt = debt − cash`, or the midpoint of a range **the issuer published**. Every input sourced, the formula written in the note. |
| **bound** | a conservative limit that runs *against* the name, stated as such. Not an estimate of the true value — a value the true one cannot be worse than. |

Forbidden, explicitly:

- cohort-median or calibrated **imputation** of something the issuer has not published
- **run-rate annualisation** of a disclosed period into an undisclosed one
- **apportioning** a multi-year programme across a shorter window by judgement
- midpoints of ranges *the analyst* constructed rather than the issuer published
- any figure whose note cannot name the arithmetic that produced it

### What happens instead

A field that cannot be sourced or derived **stays absent**. It is never filled.
The engine then does one of two things:

- **Gate input** → `gate_input_invariant()` re-runs the gate at both ends of the
  range the cohort actually reports. Same verdict at both ends means the missing
  number cannot decide anything, and the name proceeds **with a warning**.
  Different verdicts mean the answer is unknown, and the name **fails**.
- **Score input** → absence mutes the term. That understates the name, which is
  the safe direction, and it is reported in every run.

A warning instead of a failure is permitted only where the unresolved input
cannot move any final weight by more than **0.2pp**. `tools/sensitivity.py`
measures that; it is not asserted.

### Why

Written after a session in which invented inputs repeatedly produced confident
wrong answers. An A$800m apportionment of Evolution's approved capital was
recorded and then withdrawn on the realisation that a judgement call was deciding
a binary gate — at the company's own stated run-rate the same name fails Gate 2
by A$573m. Ramelius carried a committed capex annualised from one quarter into a
period the company had explicitly declined to guide. Both looked like data.

**An estimate that is wrong is worse than a gap that is known**, because a gap
stops the pipeline and an estimate propagates through it silently.

The cost of the rule is visible and was accepted: applying it removed six names
from the index in one run, taking it from 13 constituents to 9.

---

## Imputation — DELETED, kept as the worked example

> **Disabled 17 August 2026 under the DERIVE OR FAIL rule above, and deleted
> from the engine and from `config.json` the same day**. This section is
> retained because it is the archetype of the forbidden pattern and the lesson
> below is the reason the rule exists. Names lacking the split are **rejected**,
> not estimated.

One imputation was permitted, and only one.

**Resource category split.** Most companies disclose total Mineral Resources and
total Ore Reserves in the headline of their annual statement, but the
Measured/Indicated/Inferred breakdown sits in a table inside the PDF. Where
`mr_total_moz` and `pp_moz` were sourced but the split was not, the engine
applied a sleeve-specific split and flagged the name.

Observed producer splits, all read from source statements:

| Company | M&I share of MR | Inferred share |
|---|---|---|
| RRL | 79.3% | 20.7% |
| EVN | 75.2% | 24.8% |
| RMS | 73.7% | 26.3% |
| VAU | 70.3% | 29.7% |
| GMD | 69.0% | 31.0% |
| BGL | 64.5% | 35.5% |
| NST | 59.8% | 40.2% |
| WGX | 56.4% | 43.6% |
| GGP | 54.8% | 45.2% |
| **median** | **69.0%** | **31.0%** |

### Why the first calibration was wrong — keep this lesson

The initial default was **58% / 42%**, calibrated on the only two splits then in
hand: NST (59.8%) and WGX (56.4%). Both sit at the *bottom* of the observed
range, because they hold the two largest resource bases in the universe and
resource maturity runs inversely to size in this cohort — big Inferred tails are
what large exploration budgets buy.

The result was a systematic **11 percentage point** understatement, which
translated into M&I non-reserve ounces being understated by **26–65% per name**
(RRL 65%, EVN 47%, VAU 38%, BGL 35%, RMS 40%, GMD 26%). Since that term sits in
the numerator of the weighting formula, every affected name was underweighted —
invisibly, because the output looked like data.

**A two-point calibration on unrepresentative points is worse than no
calibration**, because it looks quantitative. If fewer than five observations
support an imputation, reject the affected names instead.

### The same three numbers, used the other way round

`build_index.reconcile_resource` now checks that
`pp_moz + mi_non_reserve_moz + inferred_moz` adds back to `mr_total_moz` within
2%, and reports the gap on every build. A mismatch means a category was read off
the wrong table, or one of the four numbers is a different vintage from the
others — the period-basis defect class, applied to ounces instead of to
production. All twelve constituents currently reconcile.

That is the whole arc worth remembering: **the same data that was used to invent
a value is now used to check one.** Reconciliation is what imputation should
have been.

## Sourcing protocol

1. **Primary before secondary.** A company's own ASX/AIM/TSX filing outranks any
   report of it. Where only secondary is available, mark it and log the gap.
2. **Date every field.** Gold equities restate reserves annually and guidance
   quarterly. A number without an `as_of` is unusable.
3. **`remaining_capex_aud_m` is mandatory for a developer, twice over.** It gates
   §3.1 D3 *and* it is added to EV to price the claim all-in (§7.1), because the
   ledger counts ounces the company has not yet paid to unlock. A developer
   without it is rejected at the gate, which is what stops absence reading as
   zero in the denominator. Record it as a BOUND — remaining pre-production
   capital less available funding, floored at zero — and say so in the note.
4. **Reserve price assumptions are mandatory sourcing** — but reporting-only
   JORC Table 1 and NI 43-101 both require the price deck to be
   disclosed, and it says how under-booked a company's P&P tranche is, which is
   the most informative thing on the ledger table. It no longer moves a weight:
   Turning `spot / deck` into a convexity multiplier is a functional
   form with no derivation. Source it, print it, do not score it. Never impute it.
5. **Never reconcile conflicting sources by averaging.** Pick the primary, or
   omit the field. Two of the errors caught in the 17 August 2026 sourcing pass
   came from trade press conflating two companies.
6. **Corporate actions are event-driven.** A pending scheme is recorded in
   `pending_corporate_action`, not silently pre-applied to share count.

## Extraction methods that work

Recorded because the obvious route fails more often than not.

| Source shape | Method | Worked for |
|---|---|---|
| Inline HTML tables | `curl` with a browser UA, strip tags, regex the Total rows | GMD, EVN, VAU (via listcorp) |
| Tables published as **page images** | download the PNG, read it visually | GGP — both tables are images and no text extraction can reach them |
| PDF statements | `curl` then `pdftotext -layout`, grep the group summary | NST, RRL, RMS, WGX, OBM |
| Bot-protected sites (403) | try the ASX/listcorp mirror of the same announcement | VAU |

WebFetch cannot read PDFs — it returns the compressed object stream. Download
and run `pdftotext` instead. Several company sites (Greatland, Genesis, Vault,
LSE) return 403 to WebFetch but 200 to `curl` with a normal browser User-Agent.

## Known gaps as at 2026-08-17, end of day

`tools/gaps.py` is the live register — **clean 13, partial 3, blocked 1** — and
`tools/sensitivity.py` prices each gap in pp of final weight. This list is the
narrative; those two are the record.

Resolved 17 Aug: all six missing M/I/Inferred splits, every reserve price deck
but one, every share count, CMM's resource total, and the whole Gate 3 spread
measurement. The imputation rule that filled resource splits is deleted.

**The clean count went 12 → 0 → 13, and neither move was noise.** It fell to zero
on 17 Aug when the §8.1 cap changed shape and made `single_asset` a real field
that was unsourced for all seventeen: a register reading "clean 12" while a
declared cap could not be applied to any name is the failure mode this tool
exists to prevent. It rose to 13 on 18 Aug when the replacement field,
`largest_asset_pp_share`, was sourced for all seventeen from per-asset Ore
Reserve tables. The four names that are not clean are not clean for unrelated
reasons (BC8's unpublished AISC, RMS's capex, AUC's net debt, BGL's facilities).

Still open:

- **PNR `reserve_price_aud`** — the deck sits only in JORC Table 1 of a statement
  no channel reaches; resolves with the Sept-26 quarter. The 2024-vintage
  A$2,600 must **not** be carried forward. *This was the worst open gap in the
  register at 0.59pp. It is now worth 0.000pp because the deck is read for
  reporting only. It did not close because anyone sourced it — read a 0.000pp
  line as "does not move a weight", never as "known".*
- **BC8 `aisc_aud_oz`** — a disclosure gap, not a sourcing failure; the company
  has declined to publish one. Blocks the name. FY26 annual result, by 30 Sep.
  Do **not** derive it from operating costs: the two defensible denominators
  differ by 37%.
- **RMS `committed_capex_aud_m`** — last provisional Gate 2 pass; gate-invariant
  across the whole cohort range, so it decides nothing. 21 Aug 2026.
**Closed 18 Aug 2026, and worth reading as two different kinds of closure:**

- **`largest_asset_pp_share` — CLOSED BY SOURCING, all 17.** Read off per-asset
  Ore Reserve tables. Eight names flag at or above the 0.80 threshold, not the
  four methodology §11 named from memory: PNR, RXL, OBM and — newly — **CYL,
  GGP**, BGL, AAR, AUC. CMM did **not** flag, at 0.700, because §8.1 runs on
  reserves as disclosed and Mt Gibson is 70% of them. The cap binds on PNR
  (15.00% → 10.00%) and CYL (12.52% → 10.00%), 7.52% one-way turnover, and it
  raises A$ per claimed ounce from A$643.51 to A$684.50 against an unchanged
  gold price. VAU at 0.772 is the nearest miss in the cohort.
- **Grade-tonnage curves — CLOSED BY ESTABLISHING THE DATA DOES NOT EXIST.**
  Phase 0 surveyed ≈11 MB of primary text across all seventeen and found **zero
  of twelve constituents** publishing a resource at two or more cut-offs or a
  grade-tonnage table. One partial (RXL: a grade-tonnage *chart* for its
  underground resource only) and one unknown (WGX's five NI 43-101 technical
  reports — issuer URLs all 404, SEDAR+ not retrieved). Issuers run the curve
  and publish only its argmax. `docs/grade-tonnage-survey.md` has the per-name
  table and the three findings that would have blocked Phase 2 regardless.
  **This is a complete answer, not a failure to find one**, and the item should
  not be reopened by research — only by issuers changing what they publish, which
  is cheapest to notice by re-running the survey at the annual deep rebalance.
- **Non-gold reserves, grades and decks** — *not sought.* They would be needed
  so §6.1 purity could move off TTM revenue onto forward gold share of NAV.
  only by a continuous purity multiplier. Purity is a binary gate, and building a non-gold data layer to serve one
  binary gate on one name (EVN) is not proportionate. Recorded as a known
  limitation in methodology §5; re-run the gate by hand when Carnaby completes.
- ~~CMM `mr_total_moz` omitted~~ — **resolved.** 8.659 Moz (KGP 2,990 koz + MGGP
  5,669 koz), which supersedes the 6.6 Moz still on the company website and
  pre-dating the 5.24 Moz reserve announced at Diggers. The implausible 79%
  reserve-to-resource ratio was the tell that two vintages were being mixed, and
  it is exactly the kind of thing the §6 ledger reconciliation now catches
  automatically on every build.
- ~~Tasmania (Catalyst's Henty) has never been assessed under Gate 1 Tier B.~~ —
  **resolved twice over, and the second resolution retired the question.**
  Tasmania was assessed on 17 Aug (profit-based above a 1.9% floor, capped at
  5.35%, Mineral Resources Regulations 2026). Then on 18 Aug the *exposure* turned
  out not to exist: **Catalyst sold Henty to Kaiser Reef in May 2025**, its own
  resources-and-reserves page lists no Tasmanian asset, and 100% of its reserve
  is at Plutonic and Marymia in WA. Tasmania joins SA, NT and NZ as
  verified-but-unexposed. Worth keeping as a case: the entry was chased for eight
  weeks on the strength of a mine the constituent no longer owned, and nothing in
  the pipeline noticed, because `jurisdictions.json` is read by no code.

## Point-in-time

`tools/snapshot.py` freezes `companies.json`, `config.json`, the build output and
the engine's git commit at each rebalance, under `snapshots/<date>/`. Run it
after every deep and light rebalance.

The history before the first snapshot (17 August 2026) cannot be reconstructed:
point-in-time reserves and price decks are not published anywhere, so the gates
cannot be re-run on a past date, which is also why §11.2's realised ratio can
never become a backtest. Every rebalance that goes by without a snapshot is a
cycle of that history permanently lost.
