# Why SJGV v2.1 fits the mandate

SJGV is designed for one view: gold is materially repriced, economically useful
mine inventory becomes more valuable, and the path is volatile enough that
financing, jurisdiction and execution determine who retains that upside.

The mandate is therefore not “own gold miners” in general. It is:

> Give more capital to stronger sourceable claims on future unhedged gold ounces
> per unit of enterprise value, in qualifying jurisdictions, while limiting
> avoidable ways that the claim can be lost before it pays off.

The binding rules are in [`../index-methodology.md`](../index-methodology.md).
This document explains why that construction is the best fit for the mandate
and what the evidence does—and does not—establish.

## 1. Why equities rather than only bullion

Bullion is the cleanest exposure to the metal price. It does not, however, own
three sources of equity upside:

1. operating margin expands when revenue rises faster than the cost base;
2. material outside current reserves may become worth studying and developing;
3. scarce deposits and reserve replacement can attract corporate bids.

Those sources come with failure modes bullion avoids: dilution, construction
risk, operational concentration, management execution and sovereign action.
SJGV accepts the equity-specific upside only after treating those failure modes
as gates or caps. It is a complement to bullion for an investor seeking greater
gold sensitivity, not a substitute for bullion's simplicity.

## 2. Why ounces per enterprise value

Market-cap weighting answers “which companies are already most valuable?” It
systematically adds weight as the market makes an ounce more expensive. That is
useful for capacity, but it is not a value rule and it does not target control
of gold inventory.

Equal weighting ignores both the amount of gold owned and its price. Production
weighting favours current throughput and misses inventory that may matter most
in a revaluation. A DCF can model the inventory, but its ranking is highly
dependent on analyst-selected long-term prices, discount rates, production
schedules and capital assumptions that are neither uniformly disclosed nor
sourceable.

SJGV instead uses a transparent balance-sheet purchase price:

```text
claimed unhedged ounces / funded enterprise value
```

Enterprise value is preferable to equity value because debt is a prior claim on
the same assets. Near-producers and developers also include remaining execution
capital: available financing may solve dilution, but it does not make the plant
free. For established producers, complete company-wide cost-to-completion
schedules are not normally published, so standard EV is both comparable and
sourceable.

The ratio orders the eligible universe; it does not size positions in direct
proportion to its measured magnitude. Public reserve and resource statements
differ in estimation precision, category mix, attribution basis and reporting
date, while enterprise value is a point-in-time market observation. Treating a
measured ratio of 2.00 as exactly twice as deserving of capital as 1.00 claims
more precision than those inputs support.

SJGV therefore assigns descending linear rank points: with `N` qualifying
companies, ranks receive `N, N−1, …, 1` points before caps. Exact ties share the
average points of their occupied ranks. This retains the full value ordering,
reduces sensitivity to small measurement differences and avoids the cliff and
estimation concentration of a cap-filling optimiser. It does not maximise the
portfolio's claimed ounces per dollar; that foregone concentration is the
explicit robustness cost of v2.1.

The 25 August 2026 release cost **A$909 per claimed ounce**, versus **A$1,037**
for the separately published Gate-1 cap-weighted comparison on the same market
session. That 12% difference is a point-in-time description, not a forecast or
a backtest, but it confirms that the rule currently buys a meaningfully cheaper
claim than market-cap weighting.

## 3. Why count non-reserve inventory

P&P reserves are the most economically mature ounces: the issuer has applied
the Modifying Factors and placed them in a mine plan. A reserves-only portfolio
therefore owns the highest-confidence inventory but omits much of the pathway by
which a sustained higher price can extend plans or justify development work.

M&I non-reserve material is geologically better defined but is not yet reserve.
Inferred material has lower geological confidence and cannot support a reserve
until further work upgrades it. A higher gold price does not change those
confidence classifications by itself. It can, however, improve the case for the
drilling, studies, approvals and capital needed to turn already-defined material
into an economic plan.

The ledger reflects that hierarchy at 1.0 / 0.5 / 0.2. These are policy
discounts, not fitted probabilities. They deliberately avoid pretending that
public disclosure supports a full price-responsive resource model. A review of
the candidate universe found no company publishing a complete grade-tonnage
table or resource at multiple cut-offs for all relevant assets; one developer
published a partial chart. Company-level marginal costs were also unavailable.
Any dynamic cut-off model would therefore require invented inputs, contrary to
the repository's derive-or-fail rule.

In the v2.1 snapshot, the confidence-weighted portfolio ledger was **58.6% P&P,
29.3% M&I non-reserve and 12.2% Inferred**. The position is mostly reserve-backed
while retaining a material, explicitly discounted optionality sleeve.

## 4. Why subtract hedges rather than score them

A forward sale transfers the upside of specified future production to another
party. It is therefore not part of the unhedged claim. SJGV converts the
disclosed 24-month hedge share into ounces and subtracts those ounces from P&P.

This is more faithful than multiplying the entire resource base by an annual
hedge percentage. A two-year forward book should not haircut decades of
resources. Bought puts preserve upside and are not subtracted.

## 5. Why the gates come before value

Cheapness cannot compensate for a claim that is outside the mandate or is
unlikely to remain available to shareholders. The construction is
lexicographic: qualify first, then compare value.

### Jurisdiction

The strategy's tail case is not merely a higher nominal gold price. It is a
revaluation large enough to increase the attraction of controls over metal,
exports or ownership. Gate 1 therefore counts ounces only where the currency can
adjust freely, the currency issuer is within stated solvency limits, and no
gold-control regime is operating.

The test reduces risk; it cannot eliminate future legislation. Australia is the
only current pass with a material eligible universe, so the portfolio has a
large common-country exposure. Dormant Part IV powers in the *Banking Act 1959*
remain an explicit residual risk. The honest conclusion is “concentrated in the
best qualifying jurisdiction available,” not “sovereign-risk free.”

### Capital resilience

Gold equities are path dependent. A company forced into a large issue during a
drawdown can permanently transfer much of the later upside to new capital.
Gate 2 applies a literal two-year 40% AUD-gold fall and rejects a producer only
when the rescue exceeds 30% of market capitalisation or needs more than two
normal-price cash-generation years to repair. It allows manageable
recapitalisation rather than demanding an unrealistically perfect balance
sheet. The detailed reasoning is in
[`capital-resilience.md`](capital-resilience.md).

### Tradability and currency of evidence

Quoted spread measures the cost of reaching a position more directly than a
market-cap floor. A three-month regular-hours median avoids one stale or halted
session deciding eligibility. The 18-month statement limit prevents stale
ounces from appearing cheap merely because depletion or corporate change has
not been reflected.

### Delivery discipline

The ounce ledger depends on management turning plans into production while
containing costs. Repeated misses against original guidance reveal information
that a revised end-of-year target can hide. The rule therefore uses original
and final guidance separately and distinguishes repeated failure from a
recoverable reset. Its evidence and limitations are in
[`guidance-delivery.md`](guidance-delivery.md).

## 6. Why caps are separate from the signal

Operational loss is discontinuous. A flood, geotechnical failure, tenure event
or failed development can remove an asset rather than shave a few percent from
its value. A volatility penalty is a poor proxy: daily price noise does not
measure how much of the physical claim one event can destroy.

SJGV therefore keeps value intact until the portfolio step, then limits any
company to 15%, a company with at least 80% of eligible P&P at one asset to
7.5%, any developer to 5%, and the developer sleeve to 15%. A cap-rated delivery
record is also limited to 5%.

This protection has a visible price: caps move weight away from some of the
cheapest claims. The release still cost less per claimed ounce than the
cap-weighted comparison, while its top weight was 15.0%, effective N was 8.72,
and the developer sleeve was 5%. The method does not optimise effective N; it
reports it so the investor can see the resulting concentration.

## 7. Evidence from the v2.1 release

The frozen release is a point-in-time implementation check, not performance
evidence:

| Measure | 25 August 2026 result | What it demonstrates |
|---|---:|---|
| Constituents | 11 | The gates leave a usable, concentrated portfolio |
| A$ per claimed ounce | 909 | Purchase price of the ledger at that session |
| Gate-1 cap-weighted comparison | A$1,037/oz | The value rule bought a cheaper claim on identical market inputs |
| Ledger mix | 58.6% / 29.3% / 12.2% | Reserve / M&I non-reserve / Inferred after confidence weights |
| Dimson gold beta | 1.72 | Observed gold sensitivity was inside the diagnostic 1.4–1.8 band |
| Effective N | 8.72 | Concentration after caps, reported rather than targeted |
| Top weight | 15.0% | General name cap respected |
| Developer sleeve | 5.0% | Pre-production risk remained bounded |
| Capacity at €1m | A$24.7m binding estimate | Every released position passed the reporting capacity check |

The beta uses ASX/gold timing lags and has full constituent coverage, but its
weighted R² was only 0.21. Gold explains a minority of daily equity variation.
The beta is therefore corroboration of exposure, not a promise or a weight
input.

## 8. Where the approach should and should not work

| Environment | Expected behaviour |
|---|---|
| Sustained gold revaluation | Intended case: operating margin, inventory and reserve-replacement value can rise |
| Sector consolidation | Ounce-rich, lower-valued assets may be relevant to acquirers |
| Flat gold with valuation convergence | Can benefit if cheap claims re-rate toward peers |
| Gold drawdown | Will lose money; Gate 2 seeks to limit permanent impairment, not price loss |
| Rally led by expensive large caps | Likely relative weak case because the method does not chase market value |
| Cost inflation matching gold | Equity leverage may disappoint even when bullion rises |
| Australia-specific adverse event | Material common exposure; company diversification does not solve it |

## 9. What is not established

There is no simulated performance history. Reconstructing old resource
statements, category splits, hedge books, balance sheets and disclosure states
without look-ahead would require point-in-time inputs the repository does not
possess. A modern portfolio backfilled with today's disclosures would be
misleading.

The methodology also does not prove that 1.0/0.5/0.2 are optimal, that A$909 per
claimed ounce is intrinsically cheap, or that the caps maximise risk-adjusted
return. It argues that these rules are transparent, sourceable and aligned with
the mandate. The investment thesis should be judged prospectively by:

- claimed ounces retained per invested dollar through rebalances;
- dilution and permanent-impairment outcomes in drawdowns;
- reserve and mine-plan conversion of the discounted inventory;
- delivery records after admission; and
- realised performance against bullion and transparent miner benchmarks.

That is the appropriate standard: not whether every rule would have won in an
unreconstructable past, but whether each rule has a direct, auditable connection
to the exposure the investor intended to buy.
