# SJGV data layer

This is the binding schema and sourcing protocol for live index inputs. Index
rules belong in [`../index-methodology.md`](../index-methodology.md); source
authority and conflict resolution belong in
[`../source-knowledge-base.md`](../source-knowledge-base.md).

## Files

| File | Purpose |
|---|---|
| `companies.json` | Company fundamentals, classifications, documents and field provenance |
| `guidance_delivery.json` | Adopted v2.0 delivery ratings and portfolio treatments |
| `config.json` | Declared methodology and reporting parameters |
| `sovereign.json` | Gate 1 national observations |
| `jurisdictions.json` | Gate 1 sub-national observations |
| `market.json` | Non-session market references, where applicable |
| `SOURCES.md` | Legacy human-readable source log; the knowledge store is the evidence plane |

The production engine reads only declared parameters and known company fields.
`tools/config_audit.py --strict` checks configuration consumers; `tools/gaps.py`
and `tools/provenance.py` check company data.

## Company record

Every company has identity and sleeve metadata, a `documents` map, and a
`fields` map. Every accepted field cites a key in that company's document map.

```jsonc
{
  "ticker": "XYZ",
  "name": "Example Gold",
  "sleeve": "producer",
  "documents": {
    "rr2026": {
      "title": "Annual Mineral Resources and Ore Reserves Statement",
      "url": "https://...",
      "date": "2026-06-03",
      "type": "primary"
    }
  },
  "fields": {
    "pp_moz": {"v": 5.1, "doc": "rr2026", "note": "attributable total"}
  }
}
```

Document `type` is `primary`, `secondary`, or `derived`. A URL is an access
route, not document identity. The knowledge store retains the artifact and
claim record; the company map supplies the projection citation used by the
engine.

## Derive or fail

A field may enter only as:

| State | Requirement |
|---|---|
| Sourced | Read from the cited artifact with units, date, scope and attribution preserved |
| Derived | Arithmetic identity over sourced values; record every input and the formula |
| Conservative bound | A sourced limit explicitly labelled and adverse to the company |

Forbidden:

- cohort or calibrated imputation;
- annualising a disclosed period into an undisclosed period;
- judgementally allocating a multi-year programme;
- midpoints of analyst-created ranges;
- treating missing values as zero; and
- a value whose note cannot explain its arithmetic.

A publisher-provided midpoint is recordable as a derived value only when the
publisher supplied the range. A gate must still test the relevant range edges.
If a load-bearing value cannot be sourced or derived, omit it and allow the
engine to report, degrade or reject according to the methodology.

## Field object and evidence sub-keys

The normal field object is `{"v": value, "doc": "key"}` with an optional
`note`. `approvals_land_secured` is boolean; numeric fields must not use booleans.

| Sub-key | Meaning |
|---|---|
| `range` | `[lo, hi]` published for the same quantity, scope and period as `v` |
| `term_date` | Earliest ISO date an undrawn facility may lapse |
| `evidence_state` | `POINT`, `UPPER_BOUND`, `LOWER_BOUND`, `CARRY_FORWARD`, or `UNRESOLVED` |
| `as_of` | Measurement date; distinct from document publication date |
| `cost_base_date` | Date of prices underlying a project estimate |
| `accuracy_range` | Publisher-provided estimate accuracy |
| `contingency_included` | Whether the disclosed estimate includes contingency |

An `UNRESOLVED` shell may omit `v`; it is not numeric zero. An exact day must
not be invented from a month-only facility term: record the earliest possible
lapse date. If `as_of` is absent, the cited document date is used.

Legacy `horizon_years` and `annual_leg_aud_m` sub-keys may exist in frozen
fixtures but are not live interval inputs.

## Resource and reserve fields

| Field | Definition |
|---|---|
| `pp_moz` | Attributable Proven & Probable Ore Reserves, Moz |
| `mi_non_reserve_moz` | Attributable Measured & Indicated Mineral Resources outside reserves, Moz |
| `inferred_moz` | Attributable Inferred Mineral Resources, Moz |
| `mr_total_moz` | Disclosed attributable total Mineral Resources, Moz; reconciliation only |
| `reserve_price_aud` | Issuer's reserve gold-price assumption, A$/oz; reporting only |
| `resource_price_aud` | Issuer's resource gold-price assumption, A$/oz; reporting only |

Preserve JORC/NI 43-101 categories and issuer attribution. P&P is not added to
total M&I if the reported M&I already includes reserves. M&I non-reserve must be
read directly or derived from compatible sourced categories with the identity
recorded. Inferred may not be created from an incomplete category set.

Do not convert analyst judgement about cut-offs, confidence, metallurgy or mine
planning into ounces. For scanned tables, inspect rendered pages rather than
treating missing extraction as zero.

Every counted category cites the document establishing it so statement age can
be tested separately. Preserve the reporting/as-of date independently of the
publication date.

## Jurisdiction and purity fields

| Field | Definition |
|---|---|
| `eligible_pp_share` | Gate-1-eligible share of P&P |
| `eligible_mi_share` | Gate-1-eligible share of M&I non-reserve |
| `eligible_inferred_share` | Gate-1-eligible share of Inferred |
| `eligible_ounce_share` | Confidence-weighted eligible share; fallback and reconciliation |
| `ineligible_nav_share` | Share of company NAV in ineligible jurisdictions |
| `gold_nav_share` | Trailing gold share used by the purity gate |

Category shares must be derived from the same per-asset ounce tables as their
resource fields. Do not reuse production share as an ounce share. The blended
share is not a substitute where category shares can be established.

The live purity basis is the repository's declared trailing gold revenue share,
despite the historical field name `gold_nav_share`. Do not estimate a forward
NAV split without a methodology amendment and a sourced non-gold data layer.

## Operating, balance-sheet and market fields

| Field | Definition |
|---|---|
| `production_koz_yr` | Scope-matched annual gold production, koz |
| `aisc_aud_oz` | Issuer-reported AISC, A$/oz, preserving attribution and period |
| `hedge_share_fwd24m` | Share of next 24 months' production sold forward |
| `net_debt_aud_m` | Debt less cash and bullion, A$m |
| `shares_out_m` | Full issued shares, millions |
| `undrawn_facilities_aud_m` | Committed undrawn credit, A$m, with `term_date` where creditable |
| `committed_capex_aud_m` | Contracted or non-deferrable Gate 2 commitments, A$m |
| `advt_shares_m` | 90-session average daily traded volume, million shares |

Do not infer AISC from operating expenditure or mix incompatible production and
cost scopes. A range is valid only if the issuer published it. Net debt derived
from debt less cash must cite compatible reporting dates and state the formula.
Share count is full issued capital, not free float.

Hedge share describes sold-forward production, not puts or general treasury
hedging. Preserve the disclosure horizon; the engine's two-year multiplier is a
unit conversion for this field.

## Execution capital and developer funding

Keep three quantities distinct:

```text
remaining_execution_capex_aud_m = gross economic spend still required
available_project_funding_aud_m = cash and committed cash-drawable project funding
residual_funding_gap_aud_m       = max(0, execution capital − funding)
```

The first two are sourced fields. The residual is engine-derived and must not be
stored. Gross execution capital is mandatory and weight-bearing for near-
producers and developers. It is optional reporting evidence for established
producers. Developer funding affects Gate 2 only.

A weight-bearing capital state accepts `POINT`, `UPPER_BOUND`, or an unexpired
`CARRY_FORWARD`. `LOWER_BOUND` and `UNRESOLVED` reject rather than understate
cost. A no-contingency base estimate is not an exact point. A numeric zero must
cite evidence establishing no finite material scope.

Recurring operating or annual growth guidance is not a remaining total to
completion and must not enter the denominator.

### Project interval records

Every producer-path company carries `execution_capital_projects`. Each record
joins an issuer-defined project scope to Gate 2 commitment coverage:

```jsonc
{
  "project_id": "project-id",
  "scope": "Issuer-defined boundary",
  "as_of": "2026-06-30",
  "gate2_horizon_start": "2026-07-01",
  "gate2_horizon_end": "2028-06-30",
  "committed_within_gate2_horizon_aud_m": 100,
  "committed_capex_range_aud_m": [90, 110],
  "committed_capex_state": "LOWER_BOUND",
  "committed_capex_doc": "fy27",
  "coverage_start": "2026-07-01",
  "coverage_end": "2027-06-30",
  "coverage_doc": "fy27",
  "coverage_note": "FY27 only; FY28 undisclosed",
  "remaining_execution_capex_aud_m": 250,
  "execution_capital_state": "POINT",
  "execution_capital_doc": "study"
}
```

Project totals reconcile to company fields. Evidence ending before the Gate 2
horizon is a lower bound; evidence extending beyond it is an upper bound; exact
coverage retains its sourced state. A finite project explicitly costed to
completion may establish zero for the same scope after completion. Evidence
that both omits and exceeds parts of the window must be decomposed or marked
`UNRESOLVED`. Never calendar-prorate or annualise to fill the interval.

## Developer classification fields

| Field | Definition |
|---|---|
| `study_stage` | Current sourced stage such as PFS or DFS |
| `approvals_land_secured` | True only when primary approvals and required land access are secured |

A permit alone does not prove freehold, native-title or access arrangements.
Record unresolved elements rather than interpreting silence as approval.

## Single-asset concentration

`largest_asset_pp_share` is the share of attributable, Gate-1-eligible P&P held
at the largest asset. It is a sourced float in `[0,1]`; the engine derives
single-asset status against the configured 0.80 threshold.

The asset unit is one processing plant plus deposits feeding its mine plan.
Use the issuer's production-centre grouping. Include undeveloped projects where
they already carry reserves. If two groupings are defensible, record the more
concentrated result and explain it. Source low shares as carefully as high ones;
absence is UNTESTED, not false.

## Guidance-delivery ratings

`guidance_delivery.json` is the weight-bearing classification plane for
methodology §8. It contains the adopted rating, treatment and failure counts.
The underlying original guidance, final guidance and actual claims remain in
the knowledge store.

Verified issuer non-publication may count as failure only after a complete
exchange/issuer disclosure sweep. `INSUFFICIENT_HISTORY`, `NOT_COMPARABLE` and a
repository acquisition gap retain their distinct states and are not converted
to invented passes or failures.

## Sourcing workflow

1. Read the field definition and binding methodology rule.
2. Run `tools/kb.py plan` and search retained records before network access.
3. Acquire the highest-authority admissible artifact needed for the field.
4. Verify issuer, title, dates, units, scope, attribution and exact locator.
5. Register the document and claim through `tools/kb.py`; never hand-edit the
   knowledge registry or generated views.
6. Project the reviewed value into the company document/field maps, preserving
   any derivation and evidence state.
7. Run gaps, provenance and strict knowledge/configuration audits.

Never average conflicting sources. Apply the authority and precedence rules;
quarantine a lower-tier conflict and seek a controlling correction.

## Point-in-time releases

`tools/snapshot.py` freezes company data, delivery ratings, configuration,
weights, basket, market bundle, historical bars and engine commit under a dated
snapshot. Take a snapshot only after a reviewed rebalance, never for an ordinary
code check.

The market bundle is provenance for that session. It records resolved
contracts, request parameters, quote fields, market-data type, errors and UTC
call boundaries. A URL or later live session cannot reproduce an old market
observation; the snapshot can.
