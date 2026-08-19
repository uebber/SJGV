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
> companies able to survive a severe gold drawdown without forced equity issuance.

The current construction holds 12 ASX-listed companies at **A$677 of funded EV
per confidence-weighted claimed ounce**, versus approximately **A$915 for the
same companies at market-cap weights**. That is a 26% lower headline EV per
claimed ounce, produced by portfolio construction alone. The claim is 57.8% Proven & Probable
reserves, 29.5% Measured & Indicated non-reserve material and 12.7% Inferred material.

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

The design is equally explicit about the path. A miner that must issue equity at
the bottom of a cycle permanently reduces the ounces behind each existing share.
Gate 2 therefore asks whether the company can survive a two-year, 40% real gold
drawdown without doing so. The goal is not to avoid mark-to-market losses; it is
to avoid turning a cyclical loss into permanent impairment.

### Where it should work—and where it should not

| Scenario | Expected behaviour |
|---|---|
| **Sharp, sustained gold revaluation** | The design case. Resource optionality, operating leverage and reserve replacement become more valuable. |
| **Sector consolidation** | The ounce-and-value discipline should favour companies whose ounces can replenish an acquirer's reserve base. |
| **Flat gold, valuation mean reversion** | The portfolio can benefit if cheap claims re-rate toward the sector. |
| **Gold drawdown** | The index will lose money. The survival gate is intended to preserve the claim through the cycle, not hedge the decline. |
| **Bull market led by expensive large-cap “quality”** | The structural weak case. SJGV underweights ounces the market already prices richly and sells into price strength when the disclosed claim does not change. |

---

## Why SJGV is different

### It weights the asset, not the market's opinion of the asset

The raw signal is claimed unhedged ounces divided by funded enterprise value.
There is no composite score, factor blend or discretionary quality overlay. A
term may affect a weight only if it changes either the amount of gold claimed or
the capital paid for that claim.

### It separates return drivers from ruin controls

Cheapness cannot compensate for a failed jurisdiction, an inability to survive
the stress case or an untradeable security. Those are binary gates applied before
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
| **Survival** | Can the company withstand the methodology's two-year, 40% real gold drawdown without forced equity issuance? |
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

The current production denominator is:

```text
Funded EV = market capitalisation + net debt + residual developer funding gap
```

The developer adjustment prevents an unfunded project from looking cheap merely
because the capital required to build it has not yet been raised.

This field is also the main open design issue. Residual funding gap measures
financing capacity, while remaining execution capital measures economic cost;
they are not the same quantity. [PR #3](https://github.com/uebber/SJGV/pull/3)
specifies a production migration to separate them and apply remaining execution
capital consistently to producers and developers. Until that migration is
approved, the headline A$/oz figure should be read as the current construction
statistic, not as a complete look-through acquisition-and-build cost.

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
| Company with ≥80% of eligible P&P at one asset | 10% |
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

---

## Current construction

**Market-data anchor:** 18 August 2026  
**Constituents:** 12  
**Headline funded EV / claimed ounce:** A$677  
**Same names, market-cap weighted:** approximately A$915  
**Claim mix:** 57.8% P&P / 29.5% M&I non-reserve / 12.7% Inferred  
**Reported gold beta:** 1.72  
**Effective number of holdings:** approximately 11.2

Westgold is the largest position at approximately 12.3%. PNR and CYL are capped
at 10% as single-asset companies; RXL is capped at 5% as a developer. The live
build writes the complete constituent table and cap effects to the point-in-time
snapshot rather than asking this README to serve as a second output file.

The A$677 portfolio figure is the inverse of the portfolio's weighted claim
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
| `tools/` | Provenance, gaps, sensitivity, configuration audit, snapshots and asymmetry diagnostics |
| `snapshots/` | Frozen point-in-time inputs, outputs, parameters and engine commit |
| `docs/` | Supporting studies: grade-tonnage disclosure survey, sourcing brief, execution-capital inventory |

Two rules govern every production change:

1. **Derive or fail.** A sourceable value may be derived; an invented value may
   not enter the index.
2. **Every parameter names a consumer.** A declared rule that the engine does not
   read is a defect, not documentation.

---

## Licence and disclaimer

Provided for informational and educational purposes. Nothing in this repository
is investment advice, an offer, or a recommendation to buy or sell a security.
