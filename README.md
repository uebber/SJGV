# SJGV — Stable Jurisdiction Gold Value Index

SJGV is a rules-based gold-equity index built for a specific investment regime:
**gold is repriced materially higher, the value of future mineable inventory
rises with it, and the path is volatile enough that dilution and sovereign risk
matter.** Instead of giving the largest weight to the companies the market
already values most highly, SJGV asks a more direct question: *how much eligible,
unhedged gold in the ground do I control for each dollar of enterprise value?*

That question is the reason the index exists. Physical gold gives clean exposure
to the metal, but not to the expansion of economic mine inventory or to industry
consolidation. Gold miners can provide both, but conventional miner indices are
usually market-cap weighted: as a company's ounces become more expensive, the
index owns more of them. Simple EV-per-ounce screens have the opposite problem.
They can make weak resources, sold-forward production, unfunded projects and
fragile balance sheets look deceptively cheap. SJGV is designed to keep the useful
part of the gold-equity proposition while making those failure modes explicit.

> **The mandate:** own the largest sourceable claim on future unhedged gold per
> unit of enterprise value, in qualifying jurisdictions, while selecting
> companies whose survival and operating plans are not endangered by a severe
> gold drawdown.

The latest frozen v1.7 snapshot holds 12 ASX-listed companies at **A$826 of
all-in EV per confidence-weighted claimed ounce**. The v1.8 methodology-only
replay admits WGX and BGL and reads approximately **A$780/oz**; v1.9 tightens
the single-asset cap from 10% to 7.5% pending its first fresh build. See
[`docs/producer-execution-capital-impact-2026-08-23.md`](docs/producer-execution-capital-impact-2026-08-23.md).
No v1.8 or v1.9 snapshot has been created.

This is not a forecast and it is not a backtest. It is a transparent statement
of what the portfolio owns today.

---

## The investment case

SJGV is optimized for a gold revaluation in which the optionality embedded in
mineral inventory becomes economically important.

At higher gold prices, lower cut-off grades can become economic, mine lives can
extend and already-defined material can support new or larger mine plans. That
does **not** upgrade geological confidence by itself—Inferred material still
requires further work before it can become Measured or Indicated—but it can make
more of a known resource commercially relevant. A reserves-only portfolio owns
the ounces already admitted to the mine plan. SJGV also owns a discounted claim
on what may enter later.

The index can be rewarded in three distinct ways:

1. **Gold rises and future inventory becomes more valuable.** The portfolio owns
   non-reserve material before it enters a reserve or production plan.
2. **The valuation gap closes.** The present book controls more claimed gold per
   unit of enterprise value than the same names at market-cap weights. Gold need
   not rise for that relative discount to narrow.
3. **The sector consolidates.** A portfolio selected for attributable ounces and
   valuation naturally owns assets relevant to reserve replacement and corporate
   transactions.

The design is equally explicit about the path. A miner needing a modest capital
raise at the bottom of a cycle is damaged, not necessarily destroyed. Gate 2
therefore applies a literal two-year, 40% AUD-gold drawdown and asks whether the
rescue burden is manageable: no more than 30% of market capitalisation and no
more than two normal cash-generation years to repair. The goal is not to avoid
mark-to-market losses or every issuance; it is to avoid turning a cyclical loss
into permanent impairment or a multi-year operational setback.

### Where it should work—and where it should not

| Scenario | Expected behaviour |
|---|---|
| **Sharp, sustained gold revaluation** | The design case. Resource optionality, operating leverage and reserve replacement become more valuable. |
| **Sector consolidation** | The ounce-and-value discipline should favour companies whose ounces can replenish an acquirer's reserve base. |
| **Flat gold, valuation mean reversion** | The portfolio can benefit if cheap claims re-rate toward the sector. |
| **Gold drawdown** | The index will lose money. The health gate is intended to screen out permanent impairment and multi-year operational setbacks, not hedge the decline or prohibit every recapitalisation. |
| **Bull market led by expensive large-cap “quality”** | The structural weak case. SJGV underweights ounces the market already prices richly and sells into price strength when the disclosed claim does not change. |

---

## Why SJGV is different

### It weights the asset, not the market's opinion of the asset

The raw signal is claimed unhedged ounces divided by funded enterprise value.
There is no composite score, factor blend or discretionary quality overlay. A
term may affect a weight only if it changes either the amount of gold claimed or
the capital paid for that claim.

### It separates return drivers from ruin controls

Cheapness cannot compensate for a failed jurisdiction, RED health under the
stress case or an untradeable security. Those are gates applied before
weighting. Concentration limits are applied afterwards. The investment signal is
therefore not diluted by turning every risk into another score.

### It treats optionality explicitly

P&P reserves, M&I non-reserve material and Inferred material are not treated as
equivalent. They enter the ledger at 1.0, 0.5 and 0.2 respectively. The resulting
ledger makes the optionality exposure visible instead of hiding it in a narrative
or a proprietary valuation model.

### Missing data cannot improve a company

Every live input points to a source document. Values are derived only when the
arithmetic is reproducible from that document. An absent value is a gap, a
provisional gate result or a rejection—never a convenient zero. The repository's
working rule is **derive or fail**.

### It is designed to be falsifiable

The methodology publishes its gates, parameters, source notes, cap effects and
point-in-time snapshots. Reporting models may describe the portfolio, but they
cannot silently influence a weight. There is deliberately no simulated history:
the point-in-time resource statements and assumptions needed for an honest
historical reconstruction do not exist.

---

## How the index works

The full rules are in [`index-methodology.md`](index-methodology.md). The engine
follows a simple order: **qualify, count, price, weight, cap**.

### 1. Qualify the company

The starting universe is a defined set of ASX-listed gold companies. A company
must first satisfy the gold-purity requirement, then pass three gates:

| Gate | Question |
|---|---|
| **Jurisdiction** | Are the counted ounces in a country with its own floating currency, acceptable sovereign finances and no gold-control regime currently operating? |
| **Producer health** | Would a literal two-year, 40% AUD-gold drawdown require rescue capital too large to raise or take more than two normal years to repair? |
| **Tradability** | Is the security's regular-hours quoted spread inside the sleeve limit? |

Resource and reserve statements supporting the ledger must also be no more than
18 months old. Mixed-jurisdiction companies receive category-specific eligibility
shares for P&P, M&I non-reserve and Inferred ounces; one blended jurisdiction
share is not reused across all three categories.

Gate 1 reduces risk; it does not make confiscation impossible. Australia is the
only current national pass and dormant Part IV powers in the *Banking Act 1959*
remain an explicit, unpriced common risk. The methodology records that exposure
rather than claiming it has been eliminated.

### 2. Build the ounce ledger

For each survivor:

```text
Claimed ounces
    = 1.0 × eligible Proven & Probable
    + 0.5 × eligible Measured & Indicated outside reserves
    + 0.2 × eligible Inferred
    − ounces sold forward over the hedge horizon
```

Hedged ounces are subtracted from P&P first. A bought put does not reduce the
claim; a forward sale does, because its upside has already been sold.

The 1.0 / 0.5 / 0.2 values are policy discounts for confidence and development
distance. They do not assert that every ounce within a category has the same
grade, recovery, metallurgy, capital requirement or economic value.

### 3. Price the claim

The engine denominator is sleeve-specific:

```text
producer EV = market capitalisation + net debt
near-producer/developer all-in EV = producer EV + remaining execution capital
```

Established producers use standard EV because complete company-wide remaining
cost-to-completion schedules are not normally published. Any producer execution-
capital records remain provenance/reporting data and do not affect eligibility
or weight. Near-producers and developers continue to add gross remaining
execution capital. Available project funding is recorded separately; the engine
derives `max(0, execution capital − available funding)` and uses that residual
gap only in the developer Gate 2 dilution test. A fully funded project therefore
keeps its construction cost in the denominator without failing Gate 2.

Weight-bearing capital amounts carry directional evidence states. `POINT`,
`UPPER_BOUND`, and an in-date `CARRY_FORWARD` may enter a near-producer or
developer denominator. A `LOWER_BOUND` or `UNRESOLVED` amount rejects those
names rather than allowing missing cost to raise weight. For a producer the
same states are retained only as reporting evidence; absence stays absent.
[`docs/asset-evidence-capital-proposal.md`](docs/asset-evidence-capital-proposal.md)
is the design implemented by the engine;
[`docs/execution-capital-inventory.md`](docs/execution-capital-inventory.md) is
the completed per-constituent sourcing step. The coordinated replay and formal
methodology activation remain the later remediation steps; no snapshot is made
for this implementation check.

### 4. Set raw weights

```text
                         ClaimedUnhedgedOunces_i
Raw weight_i   ∝         ───────────────────────
                               FundedEV_i
```

Proportional signal weighting spreads the resource-value exposure across all
qualifying names. It is not the solution to a literal optimization that fills
the cheapest claim to its cap before buying the next one.

### 5. Apply impairment caps

| Constraint | Limit |
|---|---:|
| Single company | 15% |
| Company with ≥80% of eligible P&P at one asset | 7.5% |
| Developer sleeve | 15% |
| Single developer | 5% |
| Ineligible-jurisdiction NAV per constituent | 25% |

These limits address permanent, company-specific loss: a plant failure, flood,
geotechnical event, tenure dispute or failed development project can remove a
claim rather than merely mark it down.

### 6. Rebalance from current disclosure

- **Annual deep rebalance:** rebuild the resource, reserve and jurisdiction data.
- **Quarterly light rebalance:** update quarterly-disclosed financial and market
  inputs.
- **Event driven:** act on corporate transactions, jurisdiction events and gate
  breaches when they occur.

Market prices, spreads, gold history and risk statistics are obtained through a
local IBKR TWS session. The repository does not fabricate replacements when that
connection is unavailable.

That session now leaves a record. Every build writes `market_bundle.json` and
`market_bars.csv`: the request parameters, the contract identifiers IBKR
resolved, every quote field, the market-data type, the TWS error channel, the
UTC instants on either side of each call, the engine commit, and every
historical bar the session returned. The market leg was the one input to a
weight that carried no source document, and it carries one now — frozen into the
snapshot beside the data layer and the parameters.

## Gate 1 cap-weighted variant

The same build also produces **SJGV Gate 1 Cap-Weighted v1.1**, a deliberately
simple parallel index. It begins with the same candidate universe (currently 17
companies), applies only Gate 1, ranks the survivors by full issued market
capitalisation, retains the largest ten, and then weights those constituents by:

```text
MarketCap_i = sourced shares outstanding_i × common-session price_i
Weight_i    = MarketCap_i ÷ Σ MarketCap of the selected top ten
```

It does not apply Gate 2, Gate 3, the 18-month resource-statement bar, the ounce
ledger, enterprise-value weighting, or the §8 concentration caps. For a
mixed-jurisdiction company, Gate 1's 25% ineligible-NAV entity limit still must
pass; once admitted, the company's full market capitalisation enters the
ranking and weight. The eligible-ounce share is not turned into an undocumented
haircut. If fewer than ten companies pass Gate 1 with complete market-cap
inputs, the variant holds every survivor rather than inventing a constituent.

This is full issued market-cap weighting, not free-float-adjusted MSCI
weighting. The repository has sourced shares outstanding but no sourced
free-float inclusion factor, so it does not invent one. Builds write
`gate1_cap_weights.json` and `gate1_cap_weights.csv`; sized builds also write
`gate1_cap_basket.json` and `gate1_cap_basket.csv`. Both variants use the same
recorded market session and are frozen together by `tools/snapshot.py`.

---

## Latest frozen snapshot — v1.7

- **Market session:** 21 August 2026, spot A$6,444/oz
- **Resource data sourced:** 21 August 2026
- **Constituents:** 12
- **Headline all-in EV / claimed ounce:** A$826
- **Same names, market-cap weighted:** A$1,071 — a 23% discount
- **Claim mix:** 59.1% P&P / 28.7% M&I non-reserve / 12.2% Inferred
- **Reported gold beta:** 1.76
- **Effective number of holdings:** 11.1

Both A$/oz figures are emitted by the build. The market-cap comparator used to be
maintained by hand and had drifted to four different values across the tree — a
source comment said A$910, this README said A$917, an in-flight branch said A$915,
and the figure was A$892. It is now computed from the same rows as the headline,
so the two cannot disagree.

The claim mix is published to one decimal deliberately. The M&I share sat within
0.01pp of 29.50 on the twelve-name book, so a whole-percent reading flipped
between 29 and 30 on a move that is not a move — and this is the statistic the
methodology nominates as the one to watch over time.

Under v1.9, CYL and PNR are capped at 7.5% as single-asset companies; RXL remains
capped at 5% as a developer. The live build
writes the complete constituent table and cap effects to
snapshots/2026-08-21-v1.7-health rather than asking this README to serve as a
second output file.

Pantoro's v1.3 exclusion exposed a real weakness in the former binary test: the
verdict flipped across the issuer's own AISC range. Under v1.7 both ends remain
inside AMBER health, so PNR returns; v1.9 limits it to the 7.5% single-asset
cap. Ora Banda also
enters: after the 40% spot shock it needs about A$167m of rescue capital, only
5.3% of current market capitalisation and 0.61 normal cash-generation years.
That is damage, but not the existential or multi-year setback Gate 2 exists to
exclude.

**That staleness closed on 20 August 2026, and it closed in the direction the
rule predicted.** Westgold's ledger had been running on 30 June 2025 group
totals. On 18 August the company declared a maiden 1,145 koz Probable reserve at
Fletcher, and the arithmetic of splicing that one deposit into the stale group
figures implied a **+14%** claim. It was deliberately not entered, because doing
so assumes nothing else moved across a year in which the company mined 387 koz.
The complete FY26 group statement landed two days later and the claim actually
moved **−2.1%**, from 7.770 to 7.603 Moz: reserves grew 41% and the booking deck
rose from A$3,800 to A$4,800/oz, but depletion and the divestment of five
non-core assets more than offset the Fletcher gain. A 16-point error, avoided by
refusing a convenient patch — which is the clearest illustration in the book of
why the derive-or-fail rule exists.

The A$826 portfolio figure is the inverse of the portfolio's weighted claim
yield—a weighted harmonic construction statistic. It is useful for comparing
two weighting schemes on the same inputs, but it is not literally the equity
capital paid for a look-through ounce.

---

## What the index does not promise

- **It is not a hedge.** A gold drawdown will hurt, and high-cost ounces can lose
  value quickly.
- **It does not prove convexity.** The 57.8 / 29.5 / 12.7 ledger mix demonstrates
  exposure to resource optionality. The current fixed-plan NAV model is linear
  in gold price, and the realised up/down sample is too weak to establish more.
- **It does not make ounces economically identical.** Category discounts do not
  normalize grade, recovery, strip ratio, metallurgy, mine timing, royalties or
  future capital.
- **It will lag expensive quality when expensive quality leads.** That is the
  predictable cost of refusing to chase a re-rating unsupported by more ounces.
- **It is currently an Australian portfolio.** Name caps diversify operational
  failures, not the common legal, fiscal, labour or currency risks of one country.
- **It has no honest historical backtest.** Current disclosures are preserved as
  snapshots so a prospective record can be built from here.

These are not footnotes to the strategy. They define the conditions under which
the strategy should—and should not—be expected to work.

---

## Repository map

| Path | Purpose |
|---|---|
| [`index-methodology.md`](index-methodology.md) | Binding methodology and amendment record |
| `build_index.py` | Gates, ledger construction, weighting, caps and basket output |
| `data/` | Provenance-tracked company, jurisdiction and parameter data |
| [`data/README.md`](data/README.md) | Data schema and sourcing conventions |
| `nav_model.py` | Reporting-only NAV and implied-deck model |
| `tools/` | Provenance, gaps, sensitivity, regression, configuration audit, snapshots and asymmetry diagnostics |
| `tests/fixtures/` | Frozen regression evidence used to decompose construction changes without creating a rebalance snapshot |
| `snapshots/` | Frozen point-in-time inputs, outputs, parameters, raw TWS session and engine commit |
| `docs/` | Supporting studies: grade-tonnage disclosure survey, sourcing brief, execution-capital inventory, and the accepted capital-denominator design |

Two rules govern every production change:

1. **Derive or fail.** A sourceable value may be derived; an invented value may
   not enter the index.
2. **Every parameter names a consumer.** A declared rule that the engine does not
   read is a defect, not documentation.

---

## Licence and disclaimer

Provided for informational and educational purposes. Nothing in this repository
is investment advice, an offer, or a recommendation to buy or sell a security.
