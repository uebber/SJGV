# Index methodology — SJGV v2.1

**Index:** Stable Jurisdiction Gold Value (SJGV)

**Version:** 2.1

**Effective:** 25 August 2026

**Status:** in force

**Vehicle:** private; no regulatory diversification constraints apply

This is the sole binding specification for the primary index. The investment
argument is in [`docs/investment-case.md`](docs/investment-case.md), the input
schema in [`data/README.md`](data/README.md), and source authority in
[`source-knowledge-base.md`](source-knowledge-base.md). None may silently alter
a rule stated here.

## 0. Objective and construction

SJGV gives more capital to qualifying companies offering a stronger sourceable
claim on future unhedged gold ounces per unit of enterprise value, without
accepting a foreseeable route to permanent impairment through financial
failure, undeliverable plans, an untradeable security, or excessive single-name
risk. It uses ranks rather than exact signal magnitudes because heterogeneous
public reserve, resource and balance-sheet disclosures do not support that
degree of sizing precision.

```text
candidate universe
  → gold-purity gate
  → Gate 1: jurisdiction and entity exposure
  → Gate 2: capital resilience
  → Gate 3: tradability
  → current-statement gate
  → execution-delivery treatment
  → claimed-unhedged-ounce ledger
  → ledger / funded enterprise value signal
  → descending linear rank weights
  → concentration caps and redistribution
```

There is no composite score or optimiser. A term may affect the value rank only
by changing the ounces claimed or the capital paid for them. Risk, NAV and beta
statistics are reporting only unless this document defines a gate or cap.

Version 2.1 replaces magnitude-proportional signal weights with descending
linear rank weights. The value ordering is unchanged; the exact distance
between two disclosed ratios no longer determines the distance between their
positions. This is a robustness choice, not a claim that rank weights maximise
ounces per invested dollar. Version 2.0 remains recoverable from Git and its
frozen snapshot.

All numeric parameters are declared in `data/config.json`. Every parameter must
name its consumer in `build_index.CONFIG_PARAMS`; an undocumented hard-coded
default or a declared but unread parameter is a defect.

## 1. Dates, universe and missing data

The candidate universe is the maintained set of ASX-listed gold companies in
`data/companies.json`. A security requires complete positive price and share-
count inputs at calculation time. Equity prices are the latest ASX daily TRADES
close returned by TWS; quote fields are retained only as cross-checks. The
market bundle records the price date and contract identity. Delisted securities
are excluded.

The data cut-off is the build's recorded sourcing date. Market observations use
the recorded IBKR session and UTC timestamps in `market_bundle.json`; no market
input is fabricated when TWS or Gateway is unavailable.

Every company field must cite a document key. A value may be sourced directly,
derived arithmetically from sourced values with its formula recorded, or entered
as an explicitly labelled conservative bound adverse to the company. Otherwise
it remains absent. Analyst-created ranges, cohort imputation, run-rate
extrapolation into undisclosed periods, and judgemental allocation of multi-year
programmes are prohibited. Publisher-provided ranges are tested at the relevant
edges. Missing information never becomes a favourable zero.

## 2. Gate 1 — jurisdiction

Gate 1 applies to asset location, not listing or incorporation. Ounces in a
country that fails Tier A contribute zero.

### 2.1 National test

| Test | Requirement |
|---|---|
| Monetary sovereignty | Own freely floating currency; not a global reserve currency; not a currency-union member |
| Sovereign solvency | Currency issuer net debt ≤60% of GDP, gross debt ≤85% of GDP, and interest ≤10% of revenue; any breach fails |
| Gold controls | No confiscation, compulsory delivery, administered monopsony, or gold-export prohibition in operation at the review date |

Gold's national export share and dormant or historical controls are disclosed
but do not gate. Observations and sources are in `data/sovereign.json`.

At v2.0's effective date Australia and New Zealand pass. Canada fails solvency;
Finland fails monetary sovereignty; the United States fails both. Australia is
the only passing jurisdiction with a material eligible listed universe. This is
an observation, not an exemption: a later breach excludes its ounces.

### 2.2 Sub-national test

A jurisdiction fails if, in the trailing ten years, it has used retroactive
revocation, executive withdrawal, output requisition, export licensing, or
forced domestic sale against the relevant mining interest. Royalty structure,
tenure timing and export routes are mandatory disclosures, not scores. Current
records are in `data/jurisdictions.json`.

### 2.3 Mixed-jurisdiction companies

The ledger applies separate eligible shares to P&P, M&I non-reserve and
Inferred ounces. A sourced blended share is a fallback only where category
shares are absent; the engine reconciles both when available.

A company is excluded if more than **25% of its NAV** lies in ineligible
jurisdictions. This entity-level limit addresses leverage an ineligible state
may have over the whole issuer, which an ounce haircut cannot remove.

## 3. Gate 2 — capital resilience

Gate 2 is binary at the index boundary and never tilts an eligible weight. It
prevents a cheap claim from qualifying when a severe down-cycle would make that
claim unavailable to existing shareholders.

### 3.1 Producers

The stress is an unhedged **40% fall from current AUD gold lasting two years**.
AISC rises by **5% a year** and tax is **30%**. Only sourced contracted or
genuinely non-deferrable commitments are deducted; discretionary growth is not
assumed to continue in a crisis.

```text
stress price      = current AUD spot × 0.60
stress resources  = net cash
                    + qualifying undrawn facilities
                    + two-year post-AISC stress cash generation
                    − unavoidable commitments
rescue capital    = max(0, −stress resources)
rescue burden     = rescue capital / market capitalisation
recovery years    = rescue capital / annual cash generation at current spot
```

An undrawn facility counts only if its sourced term reaches the stress-window
end. Refinancing is not assumed and hedge gains are disregarded.

| State | Definition | Treatment |
|---|---|---|
| GREEN | No rescue capital at the adverse sourced commitment edge | Eligible |
| AMBER | Bounded rescue required, or commitment coverage incomplete | Eligible and disclosed |
| RED | Rescue exceeds 30% of market cap or two years of normal-price cash generation | Excluded |
| UNTESTED | Production, AISC, net debt, market cap, or another decisive input is missing | Excluded |

A finite adverse edge of a publisher-provided range is tested. A lower-bound or
unresolved commitment makes the result at least AMBER; it does not invent the
unreported amount. RED at any tested publisher-provided edge excludes.

Complete producer-wide remaining construction cost is not an admission
condition and does not enter a producer denominator. Producer execution-capital
records are reporting evidence only.

### 3.2 Near-producers and developers

Near-producers follow the producer health test where operating guidance is
required and also require denominator-safe gross execution capital. Developers
instead must have at least a PFS; all primary approvals and land access secured;
and a sourced residual funding gap no greater than **30% of market
capitalisation**.

Developer residual gap is `max(0, gross remaining execution capital − available
project funding)`. Gross execution capital enters both near-producer and
developer weight denominators. A
lower-bound or unresolved gross cost cannot enter the denominator and excludes
the name. An unchanged incumbent amount may carry forward for at most six
months. Aggregated scopes below 1% of pre-capex EV are de minimis.

## 4. Gate 3 — tradability and capacity

Gate 3 uses the trailing three-month median of daily regular-hours,
time-weighted quoted spreads from IBKR BID_ASK bars:

| Sleeve | Maximum median spread |
|---|---:|
| Producer or near-producer | 1.0% |
| Developer | 4.0% |

A security whose ASX tick makes compliance impossible is excluded without a
market-data request. A median pass with a p90 breach is reported as strained.

Capacity is reported, not enforced: position size is compared with five days at
20% participation in 90-session average daily volume. It cannot change weights
without a methodology amendment.

## 5. Gold purity

Trailing gold revenue share must be at least **75%**. The test is binary and
does not multiply the ledger. An absent value is untestable and excludes.

## 6. Current disclosure and the ounce ledger

No counted tranche may rely on a reserve or resource statement more than **18
months** old at the sourcing date. The test applies to every counted category.
If a month-only date straddles the boundary, the company fails.

```text
claimed unhedged ounces
  = 1.0 × eligible Proven & Probable reserves
  + 0.5 × eligible Measured & Indicated resources outside reserves
  + 0.2 × eligible Inferred resources
  − forward-sold ounces over the next 24 months
```

P&P, M&I non-reserve and Inferred retain their reporting definitions and
attribution bases. M&I non-reserve is not total M&I: reserve ounces already
contained in M&I are removed. Inferred is not derived unless sourced categories
permit an arithmetic identity.

The factors discount confidence and development distance; they do not assert
equal grade, recovery, metallurgy, capital need or economics within a category.
Forward-sold ounces equal hedge share × annual production × two years and come
off eligible P&P first. Bought puts do not reduce the claim. The engine
reconciles categories to disclosed total resources but never repairs a mismatch.

## 7. Weighting

```text
signal_i = claimed_unhedged_ounces_i / funded_EV_i

producer funded EV
  = market capitalisation + net debt

near-producer/developer funded EV
  = market capitalisation + net debt + gross remaining execution capital

rank_i   = descending rank of signal_i, where 1 is strongest
points_i = N + 1 − rank_i
pre-cap weight_i = points_i / sum(points)
```

Market capitalisation uses the current recorded price and sourced full issued
share count. Net debt is debt less cash and bullion. Funded EV must be positive.
Every positive-signal survivor is ranked. Distinct ranks receive `N, N−1, …, 1`
points. Exact ties share the average rank and average points of the positions
they occupy, so an alphabetical tie-break cannot move capital. Rank points are
normalised before caps.

This is capped linear-rank weighting, not magnitude-proportional weighting or
cap-filling optimisation. It preserves the signal's ordering while declining
to treat small measured differences as exact position-size ratios. Gold spot
does not enter the signal, though it can change eligibility through Gate 2.

## 8. Constraints

### 8.1 Portfolio caps

Caps are applied iteratively, redistributing excess in proportion to uncapped
pre-cap rank weights until no constraint is breached:

| Constraint | Maximum |
|---|---:|
| Any company | 15% |
| Single-asset company | 7.5% |
| Delivery-cap company | 5% |
| Any developer | 5% |
| Developer sleeve | 15% |

A company is single-asset when its largest operating asset contains at least
**80%** of attributable, Gate-1-eligible P&P reserves. One processing plant and
the deposits feeding it form one asset; issuer production-hub groupings are
used. Where two groupings are defensible, record the more concentrated. An
absent share is UNTESTED, never false.

The effective ceiling is the tightest applicable cap. Caps need not be filled
and cannot make an otherwise infeasible universe valid.

### 8.2 Execution-delivery discipline

The latest three completed producing periods are assessed against earliest
formal annual production and AISC guidance and, separately, final revised
guidance. Production fails below 95% of the guided lower bound; AISC fails above
105% of the guided upper bound. A year fails once if either limb fails.

Verified non-publication of required annual guidance is a failure on both
bases. This requires a complete disclosure sweep; a repository gap is never
charged to the issuer. Genuine pre-production periods are excluded. With fewer
than three producing periods, a 100% original-basis failure rate is a hard fail.

| Record | Treatment |
|---|---|
| 100% original-basis failure rate | Exclude |
| At least two original failures and any revised failure | Exclude |
| Two original failures and no revised failure | 5% cap |
| One original and one revised failure | 5% cap |
| Evidence proves at least a cap but not whether exclusion applies | 5% cap pending resolution |
| Otherwise, with complete evidence | Pass |

The authoritative ratings are in `data/guidance_delivery.json` and refresh at
the annual deep rebalance.

## 9. Reporting-only NAV model

`nav_model.py` applies a uniform gold-only discounted cash-flow model at the
configured producing and development discount rates. It reports NAV, P/NAV,
implied gold deck and modelled delta. Its simplified mine plan, one company-level
AISC and unsourceable discount-rate choice make it unsuitable as a weight input.
No NAV output affects eligibility or weight.

## 10. Measurement and reporting

A successful build publishes weights, exclusions, gate states, ledger, cap
effects, diagnostics and market provenance. A sized build also publishes the
basket. The dated snapshot, not narrative prose, is authoritative for a build.

The primary reporting numéraire is gold ounces and EUR is secondary. The
headline KPI is A$ of funded EV per claimed ounce. Gold beta, R-squared,
idiosyncratic volatility, effective N, NAV, implied deck, capacity and ledger
mix are diagnostics only.

## 11. Concentration disclosure

Every build reports the top weight, effective N, developer sleeve, single-asset
names, cap effects and jurisdiction concentration. These disclosures do not add
constraints beyond §8. Australia-wide sovereign and statutory risk is common to
most constituents and must not be described as diversified away.

## 12. Rebalancing and governance

### 12.1 Cadence and events

| Cycle | Scope |
|---|---|
| Annual deep | Re-source gates, statements, delivery record and ledger; rebuild weights |
| Quarterly light | Update quarterly-disclosed financial and market inputs |
| Event-driven | Corporate actions, delistings, jurisdiction events, and Gate 1 or Gate 2 breaches |

A gate breach is not deferred. Corrections use the controlled data and
knowledge-store workflow, then a recorded market session. Snapshots are
immutable.

### 12.2 Governance and corrections

A methodology change requires a new version, effective date, corresponding
engine/config/test changes, and a frozen successful build. A sourced-data
correction is not a methodology amendment, but its source, as-of date and
snapshot effect must remain auditable.

The v2.1 release snapshot is
[`snapshots/2026-08-25-v2.1`](snapshots/2026-08-25-v2.1). It records the engine
commit, inputs, market session and output hashes. The v2.0 snapshot remains
immutable; earlier development history is available in Git and is not part of
this specification.

## 14. Gate 1 cap-weighted variant

The separately named **SJGV Gate 1 Cap-Weighted v1.1** is not the primary index.
It applies Gate 1 and the 25% entity limit, requires positive price and sourced
full share count, ranks by full issued market capitalisation, retains the
largest ten (or all if fewer qualify), and normalises to 100%. It applies none
of Gates 2–3, purity, statement age, delivery treatment, the ledger, funded-EV
weighting, or portfolio caps. Its dated snapshot output is authoritative.
