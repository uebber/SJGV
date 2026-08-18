# Index Methodology — SJGV v1.0

**Index Name:** Stable Jurisdiction Gold Value (SJGV)
**Version:** 1.0
**Date:** 18 August 2026
**Status:** In force.
**Structure:** Private vehicle. Not UCITS, not RIC, not 40 Act. No regulatory diversification constraints apply.
**Simulation AUM:** €1,000,000 (≈ A$1.64M)

> **One formula, no scores.** A weight is claimed unhedged ounces divided by what
> those ounces cost all-in. There is no second step, no composite, and no term
> that does not change either how many ounces are claimed or what was paid for
> them. §6 is the ledger and §7 is the weight; together they fit on a page.


---

## 0. Objective

> **Own the largest possible claim on future unhedged gold ounces, per euro
> invested, in jurisdictions with no record of taking them and no live power to
> — and survive the drawdown in between.**

Formally:

```
maximise    ClaimedUnhedgedOunces / FundedEV
subject to  P(permanent impairment)  ≈  0
            P(forced equity issuance in a 40% real drawdown)  ≈  0
reported    β_gold ∈ [1.4, 1.8]
```

Three things are worth being precise about, because each is easy to lose under
a layer of machinery.

### 0.1 Why ounces, and why that forces the shape of everything else

Measured in ounces — the reporting numéraire (§10) — a linearly levered
portfolio **must** lose ounces over a round trip in the gold price.

Worked example. Index starts at 1.00 oz. Gold doubles; a 2× exposure triples the
index; ounces go 1.00 → 1.50. Gold then halves back to its starting level. At
symmetric capture the index falls 100% and the position is destroyed. At a
realistic 1.3× downside capture it ends at 1.05 oz — a 5% ounce gain from a full
round trip.

Consequences:

1. **Ounce accumulation over a cycle is a function of convexity, not leverage.**
2. This is the third and least-discussed reason gold equities failed to deliver
   leverage from 2011 to 2020. Gold round-tripped with a ~45% drawdown in the
   middle; leverage plus path dependency destroys capital mechanically,
   independent of the capital destruction and the de-rating that also occurred.
3. **It argues against a high beta target.** β 1.4–1.8, reported and checked, not
   optimised toward. A 2.0+ linear target was considered and rejected.

### 0.2 Where the convexity actually lives

Not in a score. **In which ounces get counted.**

A gold mine is a strip of call options on gold: one option per ounce, strike
equal to that ounce's all-in extraction cost, expiry at the year it appears in
the mine plan. Proven and Probable reserves are the in-the-money part of that
strip — ounces the company has committed to mine at a cost it has published.
Measured and Indicated non-reserve material is the near-money part: drilled to a
confidence that supports a mine plan, not yet economic enough to book. Inferred
is the far out-of-the-money tail.

**Counting all three, at 1.0 / 0.5 / 0.2, is the convexity position.** It is the
bet that sub-economic ounces come into the money as the price rises, which is
the mechanism — the cut-off grade falling — by which a gold miner is convex at
all. Nothing else in this document is needed to express it, and any attempt to
express it a second time in a score restates the same number.

### 0.3 The valuation frame, and its limits

The contingent-claims frame above is **a peacetime selection heuristic and
nothing more.** It assumes a liquid freely-traded reference price, the ability to
exercise, enforceable contracts, and no discontinuous state intervention. Every
one of those fails under the tail scenario this index exists to survive. In a
monopsony regime there is no market price to be in-the-money against.

The frame therefore sits **beneath** the gates, never alongside them.

---

## 1. Architecture

```
GATE 1   Sovereign immunity        →  absolute. No score, no partial credit, no offset.
GATE 2   Survival                  →  binary.
GATE 3   Tradability               →  binary.
LEDGER   Claimed unhedged ounces   →  counted, never scored.
WEIGHT   Ledger ÷ funded EV        →  and nothing else.
CAPS     Permanent-impairment caps →  §8.1.
```

**Gate, then count. Never score.**

The test any future addition must pass: *does it change how many ounces are
claimed, or what was paid for them?* If not, it is a report, not a parameter.

---

## 2. Gate 1 — Sovereign Immunity

### 2.1 Tier A (national, binary)

Applied to the country of *asset location*, not of listing or incorporation.

| # | Test | Metric | Threshold |
|---|------|--------|-----------|
| A1 | **Monetary sovereignty** | Own currency; freely floating; not a global reserve currency; not a member of a currency union | Pass/Fail |
| A2 | **Sovereign solvency** | General government net debt/GDP; interest/revenue; net international investment position | Net debt ≤ 60% of GDP **and** interest ≤ 10% of revenue |
| A3 | **Gold as strategic export** | Gold's share of national goods exports | **Disclosed, not gated** — see note |
| A4 | **Requisition history & dormant powers** | Gold confiscation, monopsony purchase mandates, or forced domestic sale in the modern era; **including statutory powers currently suspended rather than repealed** | Zero, and no live dormant power |

**Rationale for A1.** A country whose currency devalues freely has no need to
repress gold — the FX does the adjustment continuously and without policy
intervention. A reserve-currency issuer has both a unique motive (managing
devaluation while defending reserve status) and unique tools. A currency-union
member has neither monetary control nor exit.

**Rationale for A3, and why it is not gated.** A sovereign taxes what it needs
and seizes what it lacks. A state earning materially from a productive gold
industry has a structural incentive to keep it productive. But failing this test
does not imply a state *will* expropriate — only that it has no stake in
defending you. Gating on it would exclude New Zealand for a reason unrelated to
expropriation risk. **A3 is binary, and no
code ever read it.** It is now disclosed per jurisdiction and reasoned about, not
converted to a number that does nothing.

### 2.2 Tier A outcome as at August 2026

| Country | A1 | A2 | A3 | A4 | Verdict |
|---------|----|----|----|----|---------|
| **Australia** | Pass — AUD free-floating, non-reserve, commodity currency | Pass — net debt ~19–20% of GDP, gross ~51% | **Strong — gold is the #2 export at ~A$68bn, having overtaken coal** | Query — Banking Act 1959 Pt IV *suspended* by proclamation Jan 1976, repeal status unconfirmed | **PASS** |
| New Zealand | Pass | Pass | Weak — immaterial to exports | Pass | **Pass** (no eligible listed vehicle) |
| Canada | Pass | Marginal — general government gross >100% | Moderate | Query — Foreign Exchange Control Act 1939–51 | **Marginal — fail pending review** |
| Finland | **Fail — euro membership** | **Fail — gross ~80% and rising** | Weak | Pass | **FAIL (1 of 4)** |
| United States | **Fail — reserve issuer** | **Fail — net 100% → ~120%; gross 126% → 142% by 2031** | **Weak** | **Fail — EO 6102 (1933), Gold Reserve Act (1934), WPB Order L-208 (1942)** | **FAIL (0 of 4)** |

Norway, Sweden and Switzerland pass cleanly and host no gold mining of scale.
**Australia is the only Tier A pass with a material industry.**

### 2.3 Tier B (sub-national, disclosed)

Reframed from *"will they take it"* to **"how much of my upside does the state
already own, and is that claim fixed or escalating?"**

| # | Test | Metric |
|---|------|--------|
| B1 | **Fiscal convexity** | Structure of the royalty regime. Flat ad valorem = neutral. **Profit-based or price-linked sliding scale = the state holds a call spread written at your expense.** |
| B2 | **Fiscal variance** | Trailing 10-year standard deviation of effective total government take, plus count of legislated changes |
| B3 | **Tenure security** | **Statutory maximum determination periods** and the regulator's published **on-time compliance rate** |
| B4 | **Intervention events** | Retroactive revocations, executive withdrawals, output requisition, export licensing, forced domestic sale. Zero in trailing 10 years — this one **is** a gate |
| B5 | **Export & refining path** | Can metal physically leave and reach a free market? Does the route pass through a state-controlled chokepoint? |

**B1 produces a non-obvious ranking**, which is the point. Verified from
statutory instruments 18 August 2026 for every jurisdiction the index is
exposed to; rates and sources per entry in `data/jurisdictions.json`:

- **WA — flat ad valorem, 2.5%.** Convexity-neutral and the lowest verified rate
  in the set. One attempted increase in a decade (2017, blocked in the
  Legislative Council). Lowest fiscal variance in the eligible set.
- **VIC — flat ad valorem, 2.75%.** Convexity-neutral, but the only jurisdiction
  to have **enacted** a gold royalty inside the decade (0% → 2.75%, 1 Jan 2020).
- **NSW — flat ad valorem, 4.0%, verified.** Gold is absent from Schedule 6 of
  the Mining Regulation 2016, so it takes the 4% ad valorem rate on ex-mine
  value. No price-linked element. *§2.3 asserted "flat ad valorem" before the
  data supported it — `jurisdictions.json` carried `rate: null` and
  `verified: false` while this document stated the conclusion. Now confirmed
  rather than corrected.* NSW also carries the only completed s10 ATSIHP
  intervention against an advanced gold project (McPhillamys, August 2024);
  the December 2025 judicial review remains undecided.
- **QLD — price-linked sliding scale, 2.5% to 5.0%, verified, and the escalator
  is saturated.** Gold is a "prescribed mineral" under the Mineral Resources
  (Royalty) Regulation 2025, which repealed and replaced the 2013 regulation on
  1 September 2025. Reference price 1 is A$600/oz, reference price 2 A$890/oz,
  and at or above reference price 2 the rate is a flat 5%. Spot is seven times
  reference price 2 and the Revenue Office's own worked example already applied
  5% in the December 2020 quarter. **So the marginal convexity of the Queensland
  gold royalty, at any price this index cares about, is exactly zero** — what
  remains is a flat ad valorem regime at double WA's rate. A rule that
  "penalised in proportion to the escalator's slope" would have penalised
  Queensland for a slope of zero.
- **TAS — profit-based above a 1.9% ad valorem floor, capped at 5.35%,
  verified.** Negative on structure, bounded in effect, and **no longer an index
  exposure**: Catalyst sold Henty to Kaiser Reef in May 2025, so no constituent
  holds a Tasmanian asset. The verification stands; it is not load-bearing.
- **NT — profit-based, uncapped, unverified.** Structurally the worst on this
  test: as gold rises, profit rises faster than revenue. No index exposure.
- **SA and NZ** — unverified. No index exposure.

**The one that matters is not a royalty.** B3 for Western Australia is verified
and the answer reframes the test: there are **essentially no statutory maximum
determination periods** for WA mining approvals. The regulator's own timeframes
page classifies every step of the mining approval journey as a *target*, the two
genuine statutory clocks being EP Act Part IV steps that bracket an assessment
of unbounded duration. Against those targets, FY2023-24 performance was **42.4%
of Mining Proposals inside 30 business days against an 80% objective**, and
Programme of Work approvals fell from 77.1% to 53% in one year. A Mining
Proposal averaged 46 business days of agency time and **123 days end to end**.
Much of that gap is proponent-side — information requests affected 85.2% of
finalised proposals — but the direction is wrong and the department attributes
it to resourcing. In a book that is substantially all Western Australian and
holds 30% of its claim in M&I ounces waiting on conversion, **the WA tenure
exposure is schedule, not revocation.** (Searching under "DMIRS" would have
returned nothing: the department became DEMIRS in 2023 and DMPE in March 2025.)

**B1, B2, B3 and B5 are disclosed rather than scored.** Scored, they
were "scored" and "penalised in proportion to the escalator's slope" — a
sentence no code implemented and no data supported. B4 is the only one of the
five that ever decided anything, and it decides it as a gate. Writing down a
scoring rule nobody can execute is worse than writing down a disclosure
obligation somebody can. `data/jurisdictions.json` carried that dead vocabulary
until 18 August 2026 — a `b1_scoring_principle`, a `B2.score`, and two verdicts
of "ELIGIBLE BUT PENALISED ON B1" — precisely because nothing reads the file, so
nothing failed when it was wrong. It is now written as disclosure throughout.

### 2.4 Application to companies with mixed exposure

**The gate applies to the jurisdiction of the ounces, not to the company.** There
is no company-level production threshold — a safe-harbour production rule is
abolished.

1. **The ledger counts only eligible-jurisdiction ounces (§6).** Ounces in
   ineligible jurisdictions contribute zero. No threshold, no cliff, no boundary
   to argue about.
2. **A separate entity-level cap** limits ineligible-jurisdiction NAV share to
   **≤ 25%**, recognising a risk that is *not* proportional (§2.5).

This treats Northern Star correctly and automatically. Pogo (Alaska) is ~17% of
production but only ~11% of reserves — a short-life, high-depletion asset
relative to the WA book. Production-share haircutting would penalise NST by 17%;
the ledger penalises it by 9% of gross ounces, which is the economically correct
figure, because what the index buys is the option strip rather than this year's
output.

### 2.5 The jurisdictional hook (disclosure item)

Proportional treatment of ineligible ounces is economically right but
incomplete. **A subsidiary in an impaired jurisdiction is not X% exposure — it is
a jurisdictional hook into 100% of the entity.** A state with personal
jurisdiction over a subsidiary has control of its cash repatriation, standing
over the parent's locally-listed instruments, and a lever over group-wide
conduct. The plausible action is not "we are taking this mine" but "sell us your
other production, or lose this one."

This risk is not proportional to any production or reserve share. It is handled
by the §2.4(2) entity cap, and it must be disclosed to investors as a residual
exposure the index does not fully neutralise.

---

## 3. Gate 2 — Survival

Binary. Never a tilt.

> **Does this company reach the other side of a 40% real gold drawdown without
> issuing equity?**

Inputs, all publicly disclosed: cash and bullion, undrawn committed facilities,
free cash flow at the stress price, committed capital expenditure, debt maturity
schedule.

**The test is run unhedged.** The hedge book is marked to the stress price and
then disregarded. Otherwise a company passes survival on the strength of the very
forward sales that reduce its claim under §6.3.

**Cost lives here.** AISC is a survival input. It is not a quality reward and it
is not a score input of any kind. Rewarding low AISC with a weight
premium, which systematically tilted toward the lowest-beta names in the universe
while claiming to seek leverage; an operating-leverage score points the other
way and is no better. **Neither is here.** Cost decides whether a
company survives the drawdown. It does not decide how many ounces it owns.

**Why this gate exists at all**, given that the tail scenario in §0 is one where
gold rises violently: because §0.1's path-dependency argument requires surviving
the down leg to compound ounces through the cycle. **Gate 1 defends against 1933.
Gate 2 defends against 2013.** Different tails, both needed.

**The drawdown is applied to a trailing 3-year real average of AUD gold, not to
spot** (`gate2.anchor`). Anchoring a survival gate to spot makes it mechanically
weakest exactly when spot is most extended — i.e. when survival risk is highest.
At 40% off a A$6,217 spot the stress price was A$3,730 and every producer passed.
Against the trailing anchor the stress is A$2,966, which is 52% off spot, and it
deepens automatically as spot runs ahead of the average.

### 3.1 Developer variant of Gate 2

Pre-production companies cannot be tested on cash flow. The developer test is:

| # | Requirement | Threshold |
|---|-------------|-----------|
| D1 | **Study stage** | PFS minimum; DFS preferred. Scoping-study economics move too much to weight a portfolio on. |
| D2 | **Approvals** | All primary approvals received, **and land access secured** — including freehold, native title and access agreements. A permitting checkbox is not sufficient. |
| D3 | **Bounded dilution** | **Residual funding gap ≤ 30% of market capitalisation.** |

**D3 replaces a binary funded/unfunded test.** "Fully funded" treats a A$50m gap
against a A$400m market cap identically to a A$300m gap against a A$200m cap.
The first is 12% dilution — bounded, knowable, priced. The second is a zombie.

---

## 4. Gate 3 — Tradability

The market-capitalisation floor is **abolished**. Market cap is a proxy for
liquidity; spread is the thing itself.

| Sleeve | Median time-weighted quoted spread, continuous trading, trailing 3 months |
|--------|--------------------------------------------------------------------------|
| Producer / near-producer | **≤ 1.0%** |
| Developer | **≤ 4.0%** |

Measured on RTH bid/ask history, median rather than mean so one disorderly
session cannot decide a gate. A name that passes on the median while breaching on
p90 is flagged STRAINED rather than failed.

**Record honestly: this gate currently rejects nobody.** The widest producer is
Pantoro at 0.42% against a 1.0% cap and the median producer is at 0.20%. That is
arguably correct — the gate exists to exclude what cannot be traded, not to tilt
— but a gate that removes nobody should be known to remove nobody. Rox at 1.35%
passes only on the 4.0% developer cap; reclassify it as a producer and it fails
on the same spread, so the sleeve label is doing real work there.

### 4.1 Sleeves

| Sleeve | Definition | Target |
|--------|------------|--------|
| **Producer** | In commercial production, ramp complete | Balance |
| **Near-producer** | First pour achieved, still ramping to nameplate | Within producer sleeve, flagged |
| **Developer** | Pre-first-pour, passing §3.1 | **≤ 15%**, per-name cap 5% |

**Near-producers are called out deliberately.** They carry developer-like duration
and gamma with producer-like cash flow, funding risk behind them and option
inventory intact. On the Lassonde curve this is the steepest part of the
re-rate, and neither of the conventional buckets captures it.

**The developer sleeve is sized to what qualifies — never forced to fill.**

### 4.2 The ASX tick constraint, and the price floor it implies

ASX tick sizes are $0.001 below $0.10, $0.005 from $0.10 to $1.99, and $0.01 at
$2.00 and above. A 1% spread rule is therefore **a share-price floor, not a size
floor**: a A$0.10 stock cannot quote inside 5.0%, and A$0.55 is the first price at
which 1% is achievable.

**This must be disclosed as what it is.** §4 abolishes the market-cap floor as a
crude proxy and then reintroduces a price floor near A$0.50 by a different
route, which excludes exactly the sub-A$0.20 juniors carrying the largest
out-of-the-money ounce inventories relative to their EV. The exclusion may well
be right — a book that cannot be exited is not a claim — but it is a deliberate
choice and not a neutral consequence of measuring spreads.

### 4.3 Capacity — reported, never enforced

> Target position ≤ 5 days of median ADVT at ≤ 20% participation.

**Measured: A$21m (€13m), bound by the developer.** Rox at a 5.0% weight trades
A$1.1m a day; drop the developer sleeve and capacity quadruples to A$82m.

**This is a report and not a constraint, by decision.** At €1M AUM the test is
inert on its own terms. For one day it was live, and within that day it generated
a proposal to shrink the developer sleeve — the highest-claim-per-dollar part of
the book — in order to protect a fund size twenty times the actual one. Trading
real claim for hypothetical scalability is exactly the drift this index exists to
reverse. The number is re-derived every build and disclosed; it sizes nothing.

---

## 5. Base Universe and the Purity Gate

- Listed on a recognised exchange with continuous quoting.
- Primary business is gold mining or gold development. **Royalty and streaming companies remain excluded** — an NSR is near-unlevered top-line gold exposure with no cost leverage, which is a purity play rather than a claim on ounces in the ground.
- Passes Gates 1, 2 and 3.
- **Gold ≥ 75% of NAV.** Hard floor, binary.

No market-cap floor. No liquidity floor other than §4.

**There is no continuous × gold-share multiplier.** Such a multiplier would run
"floor plus multiplier, both, not either" to avoid a boundary flip on Evolution
at ~76%. Measured, the multiplier moved the book by 0.22pp on average and 10 of
12 names scored 1.00 — a gate wearing a multiplier's clothes. Either these are
gold ounces or they are not, and EVN at 0.78 against a 0.75 floor is now a
straight gate call that will be made explicitly when it comes.

The basis is TTM gold revenue share. Replacing it with forward
gold share of NAV once the §9 model existed; the model is gold-only and cannot
produce the denominator, and building non-gold reserves, grades and decks into
the data layer to serve one binary gate on one name is not proportionate.
**Recorded as a known limitation rather than as an open item.** Evolution signed a
scheme on 27 July 2026 to acquire Carnaby Resources, a copper play, for ~A$210m;
TTM revenue will not reflect it for a year, and the gate should be re-run by hand
when it completes.

---

## 6. The Ounce Ledger

**This is the model.** Every weight in the index is a row of this ledger divided
by that company's enterprise value. There is no second step.

```
  gross      P&P  +  M&I non-reserve  +  Inferred          as disclosed
  × eligible_ounce_share                                   Gate 1
  × confidence weight per category                         §6.1
  − ounces already sold forward                            §6.3
  = CLAIMED UNHEDGED OUNCES
```

### 6.1 Confidence weights

| Category | Weight | What it is |
|---|---|---|
| **Proven & Probable** | **1.0** | The in-the-money strip. Committed to a mine plan at a published cost. |
| **M&I non-reserve** | **0.5** | The near-money option. Drilled to a confidence that supports a mine plan, not yet economic enough to book. |
| **Inferred** | **0.2** | The far out-of-the-money tail. |

These three numbers are **the only judgement remaining anywhere in the weight**,
and they sit in the numerator where a judgement belongs: they decide how many
ounces are claimed, not how a claim is scored. They are a JORC-category discount.
Nothing about them is calibrated on this cohort, on any price history, or on any
backtest — which is precisely why they survived the cut and the scoring layer did
not.

**The mix they produce is the headline convexity statistic.** Currently the index
claim is **57% unhedged reserves, 30% near-money M&I, 13% inferred tail.** Watch
it over time: a book drifting toward reserves is a book losing its option
inventory.

**M&I non-reserve is required.** Every JORC and NI 43-101 annual statement
discloses it, so a null is a sourcing gap, and admitting a name on P&P alone
would put it in the cross-section counting only its in-the-money ounces against
peers counting all three. **Inferred may be null** — not always broken out, only
0.2-weighted — and its absence is reported and understates the name.

**Reconciliation.** P&P + M&I non-reserve + Inferred is checked against disclosed
total Mineral Resources on every build, and a gap over 2% is reported. All twelve
constituents currently reconcile.

### 6.2 What is deliberately *not* in the ledger

- **No in-situ A$/oz.** There is no way to set one that is not a judgement call.
- **No imputed category split.** Inventing the M/I/Inferred breakdown from a cohort ratio, for names that publish only a total, was tested and rejected: calibrated on the only two observations available it understated M&I non-reserve ounces by 26–65% per name, invisibly, because the output looked like data. **A name without a disclosed split is rejected, not estimated.**
- **No grade-tonnage response.** The count is what the company discloses at its own cut-off, which is a snapshot at one price. Making the ounce count a function of the gold price was the one genuinely unfinished piece of this methodology; the Phase 0 survey of 18 Aug 2026 established that **public disclosure does not support it** — zero of twelve constituents publish a resource at two or more cut-offs. §12.2 item 2 and `docs/grade-tonnage-survey.md`. The ledger is static in the gold price by necessity, not by choice, and it says so.

### 6.3 Hedges — subtracted, never multiplied

```
sold_moz = hedge_share_fwd24m × production_koz_yr / 1000 × 2
```

Taken off the **P&P tranche first**, because a forward is delivered from
reserves. Capped at the eligible P&P tranche — a hedge book larger than the
reserves behind it is a data error, not a negative claim.

**Only production the company has *sold* counts.** Flat forward sales, and the
sold-call leg of a collar. A position the company has **bought** counts for
nothing, in either direction:

1. **We are not buying producers to run an options desk.** A protective floor is a
   position the holder can put on directly and more cheaply, at the portfolio
   level, sized to the whole book rather than to one company's mine plan.
2. **It would be double-counted.** The premium is a real cash cost that already
   flows through AISC, net debt and therefore EV.
3. **There is no defensible magnitude.** No disclosure sets a coefficient on the
   bought leg, and picking one would be the judgement-call-decides-a-number
   pattern `config.estimation_policy` exists to refuse.

Worked cases: GGP (150,000 oz bought puts) and RXL (40,400 oz bought puts struck
above its own reserve deck) subtract **nothing**. OBM holds 199,992 oz of bought
puts and 33,128 oz of sold calls, and subtracts on the sold calls alone.

**This is a subtraction of ounces, not a multiplier on a score.** Multiplying a
name's whole claim by `(1 − sold_share)` would charge a **24-month forward book
against a thirty-year reserve life**. Northern
Star's 25.5% hedge cost it 25.5% of its whole claim; it has actually sold 0.79 Moz
against a 42.8 Moz claim, which is 1.8%. The ledger makes the magnitude explicit
and therefore arguable — which is the whole reason to build a ledger instead of a
score.

**Not addressed, because nothing in the universe does it:** a producer that
*writes* puts is selling insurance for premium income and taking on levered
downside. If a candidate ever discloses a written-put position, §6.3 needs
extending before that name can be counted.

---

## 7. Weighting

```
                ClaimedUnhedgedOunces_i
  w_i    ∝     ─────────────────────────
                    FundedEV_i
```

That is the entire formula.

### 7.1 Funded EV — what the ounces actually cost

```
FundedEV = market capitalisation + net debt + residual funding gap
```

**Enterprise value** is the standard part: debt is a prior claim on the same
ounces, so buying an ounce through a levered balance sheet costs the equity
holder more than the share price suggests.

**The residual funding gap is the correction added 18 August 2026**, and it
matters for one sleeve. EV prices a company as it stands today. For a
pre-production name the §6 ledger is counting ounces the company **has not yet
paid to unlock** — the gap has to be spent before a single one of them is mined.
Leaving it out prices the claim on capital that has not been raised.

Measured on the two developers Gate 2 currently rejects:

| | EV A$m | + gap | claim Moz | EV/oz | **all-in/oz** |
|---|---|---|---|---|---|
| AAR | 237 | 162 | 1.37 | A$173 | **A$291** |
| AUC | 583 | 354 | 1.82 | A$320 | **A$515** |
| RXL *(in the book)* | 558 | 0 | 1.23 | A$452 | **A$452** |

The discount roughly halves. Uncorrected, the headline metric would have ranked
an unfunded developer as the cheapest claim in the universe on the strength of
money it has not got. **RXL is fully funded, so today's book does not move** —
which is why this was a safe moment to change it.

Note what makes the correction safe rather than another silent default: **a
developer whose gap is unsourced never reaches the denominator**, because §3.1
D3 rejects it first. So absence cannot read as zero in the one sleeve where zero
would flatter. For a producer the field is absent because there is no
pre-production capital, and zero is right.

**Market capitalisation is not a weight driver.** It enters only as the equity
component of EV, and as an input to the reported capacity number. Cap weighting
in a mining index is a momentum bet on valuation multiples per ounce: as a stock
re-rates, the scheme buys more of it at a higher price per unit of claim. That is
precisely inverted from the objective.

**Nothing regressed from price history touches a weight.** β_gold, R² and σ_idio
are computed and printed as diagnostics. A name whose regression fails is
weighted normally and merely un-diagnosed. Excluding it — as any scheme with
σ_idio in the denominator must — would let a short listing history disqualify a
company's ounces.

### 7.2 What this produces

At the 18 August 2026 book: **A$684 of funded EV per claimed ounce, against
roughly A$910 for the same twelve names cap-weighted.** That single number is the strategy
working or not working, and it is computed from the same disclosed inputs as the
weights, with no history in it and therefore no survivorship or look-ahead bias.

**It reads A$684 and not A$644 because of a cap, not a market move.** Sourcing
the §8.1 single-asset input on 18 August pinned Pantoro and Catalyst — the two
cheapest claims in the universe at A$372/oz and A$530/oz — at 10% each, and
against an unchanged gold price that moved the headline from A$643.51 to
A$684.50. **Read the two numbers together:** A$644 is what the ounce ledger alone
would buy, A$684 is what it buys after refusing to let one operational failure
take out more than a tenth of the book. Neither is the "right" one; the
difference *is* the cap, priced.

---

## 8. Constraints

### 8.1 The caps, and the one question they all answer

| Constraint | Setting |
|------------|---------|
| Single-name maximum | **15%** |
| Single-asset company maximum | **10%** |
| Developer sleeve | **≤ 15%**; per-name **≤ 5%** |
| Ineligible-jurisdiction NAV per constituent | 25% (§2.4) |

Every one of these answers the same question, and it is a question §0 already
asks: **how much of the claim can a single uncorrelated operational failure
destroy permanently?** A fault, a flood, a tenement dispute or a fraud does not
mark a claim down — it removes it. That is `P(permanent impairment) ≈ 0`, and it
is in the objective function.

**The single-asset cap** is a cap on companies where one mine *is* the company,
and it binds directly. Note that any asset-level cap set *above* the 15% name cap
cannot bind on one company however concentrated — only on an asset two
constituents share — which is why this one is set below it.

**Sourced and live from 18 August 2026.** It binds on two constituents.

#### What "single-asset" means, and how the engine decides it

The engine does not read a hand-set boolean. It reads a sourced quantity and
derives the judgement against a declared threshold:

| | |
|---|---|
| `largest_asset_pp_share` | Sourced float in [0, 1], per company. The share of the company's **attributable, Gate-1-eligible Proven & Probable Ore Reserves** held at its single largest asset. |
| `constraints.single_asset_pp_share_threshold` | **0.80.** |
| `single_asset` | Derived: `share >= threshold`. **Tri-state** — an absent share derives `None` (UNTESTED), never `False`. |

Seventeen hand-set booleans would have been seventeen unrecorded judgement
calls, invisible to `tools/config_audit.py` and unperturbable by
`tools/sensitivity.py`. One threshold over seventeen sourced shares is a single
judgement call on the record, in `config.json`, where it can be argued with.
Reserves are the basis because they come off the *same table* `pp_moz` already
comes from, need no valuation and therefore no discount rate, and are where the
operating asset is.

**The asset unit.** An asset is **one processing plant together with the deposits
the mine plan feeds it**. Several pits or underground mines through one mill are
one asset regardless of pit count; ore trucked from a satellite deposit to a
shared mill belongs to that mill's asset. Where the issuer's own reserve table
groups deposits into a named production centre or hub, that grouping is used.
Where two groupings are both defensible, **the more concentrated one is
recorded** — ambiguity must tighten the cap, not let a name escape it.

**Development status is ignored: the test runs on reserves as disclosed.** A
reserve is by construction the forward mine plan, and §6's ledger counts future
ounces rather than this year's output, so an undeveloped project carrying
reserves is a second asset. This is the rule that decides Capricorn, and it was
fixed before the number was computed. On trailing production CMM is plainly
one mine — Karlawinda was 100% of FY26's 123,589 oz — but Mt Gibson holds 70% of
the group reserve, is federally permitted and contracted, and a flood at
Karlawinda does not remove it. **CMM reads 0.700 and does not flag**, which is
what §11's "Karlawinda *until* Mt Gibson" anticipated.

**A tri-state that is asserted, not documented.** An absent share reading as
`0.0` would derive `False`, silently restore the looser 15% cap, and report it
as a test that passed — the silent-zero trap pointed the dangerous way, and the
same failure as Gate 3's two unread spread limits. `_assert_single_asset_tristate()`
runs on every build, before the IBKR session, and also refuses a threshold
outside (0, 1] because one above 1.0 would disable the cap without saying so.

#### The sourced cross-section

| | Share | | | Share | |
|---|---|---|---|---|---|
| PNR | **1.000** | Norseman ◆ | VAU | 0.772 | Leonora Ops |
| RXL | **1.000** | Youanmi ◆ | RMS | 0.738 | MMG Hub |
| CYL | **1.000** | Plutonic Belt ◆ | BC8 | 0.736 | Kal East |
| GGP | **1.000** | Telfer–Havieron ◆ | CMM | 0.700 | Mt Gibson |
| BGL | **1.000** | Bellevue ◆ | WGX | 0.687 | Murchison |
| OBM | **1.000** | Davyhurst ◆ | GMD | 0.660 | Leonora hub |
| AAR | **1.000** | Mandilla ◆ | NST | 0.576 | KCGM |
| AUC | **1.000** | Katanning ◆ | EVN | 0.521 | Cowal |
| | | | RRL | 0.490 | McPhillamys |

**Eight of seventeen flag, not the four §11 listed.** The threshold is not
knife-edge: nothing in the universe sits between 0.773 and 0.999. Vault at 0.772
is the nearest miss and the only name a threshold of 0.75 would newly catch.

**What it cost.** PNR 15.00% → 10.00% and CYL 12.52% → 10.00%, 7.52% one-way
turnover, redistributed pro rata; RXL and GGP flag but are already below the cap.
Measured against an identical gold price, **the index's price per claimed ounce
rose from A$643.51 to A$684.50, +6.4%.** That is not a side-effect to bury: PNR
at A$372/oz and CYL at A$530/oz are the two cheapest claims in the universe, and
capping them necessarily makes the book dearer per ounce. **The committee is
being asked to pay 6.4% on the headline KPI to hold `P(permanent impairment) ≈ 0`,
and that is the whole content of the cap.** Reject the trade and the cap should
go, not be softened.

## 9. The NAV Model — reporting only

`nav_model.py`. Internal, rules-based, applied uniformly. Not broker consensus.

```
NAV = Σ_t  production × (deck − AISC) × (1 − tax) / (1 + r)^t   −  net debt
```

Reserves are mined first at the current rate and discounted at the producing
rate; non-reserve material follows at the same rate and the same AISC,
discounted at the development rate, converted at the §6.1 confidence weights.
Everything is real. Gold only. Growth capital and the ounces it buys are both
excluded.

**Its output reaches no weight, by decision rather than pending one.** There is no
adoption switch, no discount rate to publish and defend, and no §13 item 3. Two
reasons, in order of weight:

1. **It is not independent information.** P/NAV measured **+0.87 log-correlated
   with the §7 ounces-per-dollar ratio** that already sets the weights. Adopting
   it would mostly have re-multiplied the ledger by itself.
2. **It moves with a discount rate nobody can source.** 5% real producing and 9%
   real development were inherited placeholders that nobody defended in four
   months. The index does not let a judgement call size a position.

### 9.1 What it is for

**The implied deck.** The gold price at which the market's valuation of a company
equals a rules-based DCF of that company's own disclosed reserves. Across the
current book the market is pricing these names at **A$3,017–6,235/oz against a
spot of A$6,217** — Rox at A$3,017, Pantoro at A$4,169, Capricorn and Evolution at
spot. That is a statement about disagreement, in a unit anyone can argue with,
and it is worth printing on every build.

### 9.2 The gamma finding, and how to read it now

Modelled gamma is **identically zero**, and modelled NAV capture at ±40% is
1.61 up, 1.61 down — a ratio of exactly 1.00.

Read that carefully, because it is not "these companies have no convexity":

> On a **fixed** mine plan at **one** AISC, NAV is exactly `A × (deck − AISC) −
> debt`. That is linear in the deck, so every finite difference returns the same
> delta. The ratio is 1.00 by construction, not by measurement.

Real gold-miner convexity is the cut-off grade falling as the price rises, which
**moves ounces from the M&I non-reserve tranche of the §6 ledger
into P&P.** That is the measurement this ratio cannot make.

**And as of 18 August 2026 it cannot be made at all from public disclosure.**
The Phase 0 survey (§12.2 item 2, `docs/grade-tonnage-survey.md`) found that
**zero of twelve constituents** publish a resource at two or more cut-offs.
Issuers run the curve and publish only its argmax — Rox's DFS says so in as many
words, calculating "the full range of cut-offs" and then tabling the selected
one. Three further obstacles would have remained even with the data: there is no
single cut-off per company (Regis publishes a *weighted average* of domain
cut-offs it never discloses), 8% of the book is reported on net-smelter-return
value shells rather than a gold-grade cut-off at all, and the cut-off is set by
marginal cost while the data layer carries one average AISC per company.

So the **ledger mix** — 57% reserves / 30% M&I non-reserve / 13% inferred — is
not a placeholder for a better measure that is coming. It is the measure. Unlike
this ratio it is made entirely of disclosed ounces rather than of a model's blind
spot. **Report the mix; treat the 1.00 as a statement about the model; and do not
let a future session reopen the gap by assuming a cut-off elasticity, which would
manufacture the exact number the product is judged on.**

---

## 10. Measurement and Reporting

### 10.1 Numéraire

**Primary: gold ounces. Secondary: EUR.**

The index level is expressed as ounces of gold. Measuring a debasement hedge in a
debasing unit conceals whether it is working. Note the honesty this imposes: in
ounce terms the index only rises if the portfolio **outperforms gold**. A
high-beta portfolio in a gold bull market rises enormously in EUR and modestly in
ounces.

### 10.2 Headline KPI: A$ of EV per claimed ounce

**A$640/oz against A$910/oz cap-weighted.**

This replaces the asymmetry ratio as the headline. It is computed from the same
disclosed inputs as the weights, carries no history, and therefore cannot be
survivorship- or look-ahead-biased. It measures the thing the index is for.

### 10.3 Up-versus-down behaviour, and why it is demoted

Two measures, and which one you read decides the answer.

**CONVEXITY — the measure.** From `r_p = α + β_up·g⁺ + β_dn·g⁻ + ε`, weekly
against AUD gold. The intercept absorbs drift, so what remains is curvature: how
much of gold's up move the book takes against how much of its down move.

**`raw` — the classical compounded capture ratio.** Reported for continuity, and
because it was the headline KPI until 17 August 2026. **It is approximately 97%
a realised-return measure.** Drift raises compounded up-capture *and* cushions
compounded down-capture, so it enters the ratio twice in the same direction.
Measured per name over the window, the ratio correlated **+0.97 with total
return**. Vault read 3.32 — a merger spread, since GMD/VAU decoupled it from
gold. Pantoro read 0.62, having fallen 23%. Neither number describes ounce
inventory.

Weekly, full-coverage window (from 25 June 2025 — the only honest one), with
2,000-draw bootstrap intervals over periods:

| | β_up | β_dn | **convexity** | 95% CI | α/wk | raw | 95% CI |
|---|---|---|---|---|---|---|---|
| **SJGV** | 1.70 | **1.15** | **1.48** | [0.12, 4.44] | −0.19% | 1.50 | [−1.52, 7.31] |
| Cap-weighted, same names | 1.60 | 1.25 | 1.28 | [0.23, 3.96] | +0.07% | 1.59 | [0.16, 7.51] |
| GDX (AUD) | 1.72 | 1.74 | 0.99 | [0.19, 1.98] | +0.30% | 1.87 | [0.90, 3.79] |

Paired difference, SJGV minus cap-weighted: **+0.19, 95% CI [−0.70, +1.29].**

**Read three things off that table, in order.**

1. **The intervals contain everything.** A 95% range of [0.12, 4.44] spans "no
   convexity at all" and "three times gold". **23 down weeks cannot separate any
   row from any other.** No number here is a finding.
2. **The two measures rank the book oppositely.** On `raw`, SJGV 1.50 against
   cap-weighting's 1.59 — apparently behind. On convexity, 1.48 against 1.28 —
   apparently ahead. The whole difference is α: −0.19%/wk against +0.07%/wk. The
   raw ratio was rewarding cap-weighting for drift.
3. **α is disclosed rather than folded in.** For a value strategy the drift *is*
   the information. Over this window it is negative, and §10.3 of the handoff
   records why: cap-weighting holds 24.6% of Evolution, which returned +81%,
   against our 3.6% — one deliberate underweight in the most expensive claim in
   the universe accounts for +17pp of a +7pp total return gap. **That is the
   principal way this index underperforms, it is structural, and it is not
   fixable without abandoning the objective.**

**This was reported wrongly once.** On 17 August 2026 the −0.09 raw gap against
cap-weighting was written up as evidence the weighting scheme was not earning
its asymmetry. It had a 95% interval of roughly ±2.5. Both the drift-free
measure and the interval now ship in `tools/asymmetry.py` on every run, and the
tool refuses to fit the piecewise regression below 24 periods with at least 8 in
each state — the monthly full-coverage window has 13 and 5, and previously
produced a spuriously "significant" verdict off a numerically-zero bound.

**None of it is a backtest, and it cannot be made into one.** Survivorship- and
look-ahead-biased, both upward; point-in-time reserves and price decks do not
exist, so the gates cannot be re-run on any past date.

**Read this beside §9.2's modelled 1.00**, which is 1.00 by construction. Two
independent measurements, one forward and one backward, and neither
demonstrates asymmetry. This index does not claim otherwise. What it claims is a
cheaper claim on more ounces, in a jurisdiction that cannot take them, held
through the drawdown — and that claim is measured in §10.2 with no biased input
and no confidence interval, because it is arithmetic on disclosed numbers rather
than an estimate.

### 10.4 Secondary reporting

The ledger mix (§6.1); the reserve deck per name against spot; regressed β_gold,
R² and σ_idio; modelled delta and the implied deck (§9); effective number of
stocks; ineligible-jurisdiction NAV share; capacity ceiling; turnover and
realised trading cost in basis points.

`tools/snapshot.py` freezes the data layer, the parameters, the output and the
engine commit at each rebalance, and `--diff` reports one-way turnover, entries,
exits and which underlying fields moved. History before the first snapshot cannot
be reconstructed and is not claimed.

---

## 11. Concentration Disclosure

Applying Gate 1 honestly produces a portfolio that is **approximately 100%
Australian and predominantly Western Australian.**

This is a deliberate outcome, not an artefact. Australia is the only jurisdiction
on earth that combines monetary sovereignty in a freely-floating non-reserve
commodity currency, sovereign net debt near 19% of GDP, gold as its
second-largest export at ~A$68bn, a constitutional just-terms guarantee with live
precedent protecting mining tenements (*Newcrest Mining v Commonwealth* (1997)), a
flat ad valorem royalty regime, and a deep listed gold sector.

Investors must understand four things:

1. **This is a macro position, not merely a risk screen.** The index is
   structurally short US monetary credibility. That is a defensible bet and it
   should be sold as one.
2. **Jurisdiction-diversified has been traded for jurisdiction-quality.** One
   state royalty review, one power-grid event or one labour-market shock hits
   substantially the whole book at once.
3. **The book is four constituents deep in single-asset companies, and the
   sourced answer differs from the one this section used to give.** Until 18
   August 2026 §11 named four candidates from memory — Pantoro at Norseman, Rox
   at Youanmi, Capricorn at Karlawinda, Ora Banda at Davyhurst. Sourcing
   `largest_asset_pp_share` for all seventeen (§8.1) moved three of them:

   | Named here before | Sourced answer |
   |---|---|
   | Pantoro / Norseman | ✅ **1.000.** The only row in its reserve table. |
   | Rox / Youanmi | ✅ **1.000.** One project, one plant. |
   | Capricorn / Karlawinda | ❌ **0.700.** Mt Gibson is 70% of the reserve. §8.1 runs on reserves as disclosed, so "until Mt Gibson" has already happened. |
   | Ora Banda / Davyhurst | ✅ **1.000** — but it fails Gate 2 and is not in the book. |
   | *not named* | ✅ **Catalyst / Plutonic Belt, 1.000.** 100% of its 1,542 koz reserve is at the one Plutonic hub; Bendigo carries resource and no reserve. **This is the second-largest position in the index and the cap binds on it.** |
   | *not named* | ✅ **Greatland / Telfer–Havieron, 1.000.** Havieron has no processing route of its own — its ore is trucked 45 km to the Telfer plant. Below the cap today at ~8%. |
   | *not named* | ✅ Bellevue, Astral, Ausgold — all 1.000, none of them past Gate 2. |

   So the honest disclosure is **four of twelve constituents** (PNR, CYL, GGP,
   RXL) and **eight of seventeen candidates**. §8.1's 10% cap is applied from 18
   August 2026 and binds on **Pantoro and Catalyst**, at a cost of A$41 per
   claimed ounce on the headline KPI.

   Note what the two additions have in common with each other and not with the
   original four: neither is a one-*mine* company. Catalyst runs a hub with nine
   named deposits and Greatland runs an open pit, an underground and a
   development project 45 km apart. **They are single-asset because everything
   they own goes through one mill** — which is the failure mode the cap is
   about, and the reason §8.1 defines the unit as a processing plant rather than
   as a mine.
4. **The index addresses the asset side, not the investor side.** If capital
   controls are imposed on the investor's home jurisdiction, the binding
   constraint will be custody, repatriation or the wrapper — not the mine. Only
   unencumbered physical held in a third jurisdiction addresses that, and this
   index does not claim to.

### 11.1 Accepted risks — parked by committee decision

Not resolved; accepted unquantified. Both are disclosure items.

| Item | Nature of the residual risk |
|------|------------------------------|
| **Banking Act 1959 (Cth) Part IV** | Gold requisition powers suspended by proclamation in January 1976; repeal status unconfirmed. If the power remains on the statute book in suspended form, it is reactivable by proclamation — a Tier A A4 exposure the index does not currently price. |
| **s51(xxxi) does not bind the States** | The constitutional just-terms guarantee reaches the Commonwealth. Mining tenure is granted under the WA Mining Act 1978, and state parliaments are not subject to it. In a ~100% Australian, predominantly Western Australian portfolio, this single question carries most of the residual jurisdictional risk in the product. |

---

## 12. Rebalancing, Maintenance and Open Items

### 12.1 Cadence

| Cycle | Timing | Scope |
|-------|--------|-------|
| **Deep** | Annual, aligned to reserve statements | Full re-run: Gates 1–3, ledger rebuild, full reweight |
| **Light** | Quarterly | Quarterly-disclosed items only: AISC, hedge book, cash, production, share count |
| **Event-driven** | As required | Corporate actions, jurisdictional events, Gate 1 or Gate 2 breaches |

**Justification from the observed record.** Three transactions were in flight at
the May 2026 snapshot. Within ten weeks: the Regis/Vault merger *collapsed* after
Genesis outbid Regis; Genesis/Magnetic implemented on 22 June; and Agnico closed
on Rupert on 16 June. A semi-annual index would have carried three wrong
positions for a full cycle.

**Gate breaches are not deferred to the next cycle.** A Gate 1 or Gate 2 failure
removes a constituent immediately, with weight redistributed pro rata.

### 12.2 Open items

The register was three lines long, which was the point. **All three closed on 18
August 2026** — one by sourcing, one by verification, one by a survey that
established the data does not exist.

| # | Item | Outcome |
|---|------|---------|
| 1 | **Single-asset status, all 17.** | **CLOSED — sourced.** Replaced the unsourced `single_asset` boolean with a sourced `largest_asset_pp_share` and a declared 0.80 threshold (§8.1). Eight of seventeen flag, not the four §11 named; the cap binds on **PNR and CYL**, 7.52% one-way turnover, and it costs **+6.4% on A$ per claimed ounce**. Three regression names behaved: PNR and RXL returned 1.000, CMM returned 0.700 under the forward rule fixed before the number was computed. |
| 2 | **Grade-tonnage curves.** | **CLOSED — not sourceable from public disclosure.** Phase 0 survey over ≈11 MB of primary text across all seventeen: **zero of twelve constituents** publish a resource at two or more cut-offs or a grade-tonnage table. One partial (RXL, a *chart* for its underground resource only) and one unknown (WGX's five NI 43-101 reports, issuer URLs dead). Full write-up and the three findings that would have blocked Phase 2 regardless: `docs/grade-tonnage-survey.md`. **The §6 ledger stays static in the gold price and §9.2's modelled 1.00 keeps saying what it says.** |
| 3 | **Jurisdiction B1 / B3 verification.** | **CLOSED — verified.** B1 verified from statutory instruments for every exposed jurisdiction: WA 2.5% flat, VIC 2.75% flat, NSW **4.0% flat** (confirming a claim §2.3 was making ahead of its data), QLD a **price-linked 2.5–5.0% scale saturated at its 5% ceiling**, TAS profit-based capped at 5.35% and **no longer an exposure** (Henty sold May 2025). WA **B3 verified**, and it reframed the test: no statutory determination periods, 42.4% on-time against an 80% target. `jurisdictions.json` records the statutory instrument for each. Remaining unverified: B1 for SA, NT and NZ (nil exposure), and B2/B3/B4 outside WA. |

Three things the closures leave behind, none of them a reopening:

- **A trade for the committee, not a fact.** §8.1 now costs 6.4% of the headline
  KPI. That is the cap's whole content and it should be accepted or rejected as
  such.
- **One name at the boundary.** Vault at 0.772 against a 0.80 threshold is the
  only classification a definitional argument could move (§8.1).
- **A survey to re-run, not an item to keep open.** Grade-tonnage coverage
  changes only if issuers change what they publish. Re-run the Phase 0 scan at
  the annual deep rebalance; do not keep a research item open against it.

**Not open, and not to be reopened as parameters:** the NAV-model discount rates
and conservative deck (§9 is reporting-only, so there is nothing to adopt); the
entity-level ineligible-NAV cap calibration (25%, not binding on NST at 9% of
gross ounces); the developer sleeve's capacity effect (§4.3 is a report); the
forward-gold-share-of-NAV purity basis (§5, recorded as a limitation).

### 12.3 Process rule

Every parameter in `config.json` must name a consumer in
`build_index.CONFIG_PARAMS`, and `tools/config_audit.py` cross-checks the
declaration against the reads a real build recorded. The rule exists because a
declared-and-unread parameter has been found three times — Gate 3's spread
limits, then five constraints at once, then three parameters the engine had
*also* hardcoded so that editing config changed nothing.

A second rule governs what may be added at all, and it is the reason this
document is as short as it is:

> **A term enters the weight only if it changes how many ounces are claimed, or
> what was paid for them. Everything else is a report.**

---

## 13. Factor Inventory — everything that can move a weight

**46 inputs, and no others.** Established by perturbation rather than by reading
the code: every candidate input was moved and the resulting book compared. `Δw`
is the largest change in any single final weight, at ±50% on a data field and
±40% on a parameter. A factor that is *read* but cannot change a weight is listed
in §13.5 and should never be described as part of the model.

### 13.1 Numerator — the ounce ledger

Everything here answers one question: **how many ounces of gold will this company
be able to hand us, and how sure are we?**

| Factor | What it represents | Why it pays into the goal | Δw |
|---|---|---|---|
| `pp_moz` | Proven & Probable reserves | The **in-the-money strip** — ounces inside a funded mine plan at a published cost. This is the floor under the claim: the part that converts to metal without needing the gold price to do anything. | **1.03pp** |
| `mi_non_reserve_moz` | Measured & Indicated resource not yet booked as reserve | The **near-money option, and the largest single source of the index's convexity.** Drilled densely enough to support a mine plan, not yet economic at the company's own price deck. These are precisely the ounces a rising gold price converts into reserves — the mechanism §0.2 says the product exists to own. | **0.65pp** |
| `inferred_moz` | Inferred resource | The **far out-of-the-money tail.** Geologically real, sparsely drilled, worth little unless the price moves a long way — which is the exact payoff shape the sovereign-debasement thesis is buying. | **0.43pp** |
| `eligible_ounce_share` | Share of ounces under a Tier A sovereign | **Gate 1 expressed as a number instead of a verdict.** An ounce a state can requisition is not an ounce we own, so it is discarded at source rather than haircutting the company. This is the half of the objective that is not about leverage. | **0.12pp** |
| `hedge_share_fwd24m` | Production already sold forward | A sold-forward ounce is **a short gold position inside a long gold product.** It converts at a fixed price and cannot participate in the move the index exists to capture, so it is subtracted from the claim rather than scored against it. | **0.06pp** |
| `production_koz_yr` | Annual production rate | In the ledger it does one job: converting the disclosed hedge *percentage* into hedged *ounces*. (Also a Gate 2 input, where it does much more.) | via hedge |
| `confidence_weights.proven_probable` = 1.0 | Reserve ounce = the unit of account | The numéraire of the ledger. Every other ounce is priced relative to this one, so it is definitional rather than tunable. | **0.74pp** |
| `confidence_weights.measured_indicated_non_reserve` = 0.5 | A near-money ounce is worth half a reserve ounce | **The single most consequential dial in the methodology.** It sets the price the index pays for optionality: raise it and the book tilts toward explorers and undeveloped inventory, lower it and it tilts toward producing reserves. It is how much convexity the index buys, expressed as one number. | **0.50pp** |
| `confidence_weights.inferred` = 0.2 | A far-tail ounce is worth a fifth of a reserve ounce | Deliberately harsh. Inferred material cannot legally support a mine plan, so a fifth is a discount that survives being wrong — the index still gets tail exposure without letting a thin drill pattern set a position. | **0.34pp** |
| `confidence_weights.hedge_horizon_years` = 2.0 | Months of production a disclosed hedge book covers | **A unit conversion, not a tuning knob.** The disclosed field is a 24-month book; this turns a percentage into ounces. Change it only if the disclosure horizon changes. | **0.05pp** |

### 13.2 Denominator — enterprise value

**What we pay for the claim.** EV rather than market cap because the ounces
service the debt first: buying an ounce through a levered balance sheet costs the
equity holder more than the share price suggests.

| Factor | What it represents | Why it pays into the goal | Δw |
|---|---|---|---|
| `price_aud` | Live market price | Half of what we pay. The whole strategy is the gap between the ounce ranking and the price ranking, so this is one of the two columns that gap is made of. | **1.89pp** |
| `shares_out_m` | Shares on issue | The other half of market cap. **Dilution reduces ounces-per-euro directly**, so a stale share count silently overstates the claim — which is why there is no API fallback and it is sourced from filings. | **1.45pp** |
| `net_debt_aud_m` | Debt less cash and bullion | A **prior claim on the same ounces.** Adding it gives what the whole ounce base costs rather than just the equity slice; net cash correspondingly reduces the price paid. | **15.00pp** |

### 13.3 Gates — binary, and an exclusion reweights everyone through the normalisation

Nothing here scores. Each answers a yes/no question about whether the claim is
ours, is durable, and is reachable.

| Factor | What it represents | Why it pays into the goal | Δw |
|---|---|---|---|
| `gold_nav_share` · `gates.purity_floor_gold_nav_share` = 0.75 | Gold as a share of the business | **Is this a gold claim at all.** A copper sleeve dilutes the signal the product is sold on and imports pro-cyclical, China-levered exposure that a gold allocation exists to avoid. | **15.00pp** |
| `ineligible_nav_share` · `gates.max_ineligible_nav_share` = 0.25 | NAV under an ineligible sovereign | Catches the **jurisdictional hook** (§2.5) that proportional ounce-discounting cannot: a subsidiary in an impaired jurisdiction gives that state leverage over the *whole* entity, not over its share of production. | **3.63pp** |
| `aisc_aud_oz` | All-in sustaining cost per ounce | **A survival input only — never a reward.** High cost means more gold delta, which the index wants, right up to the point where the company cannot survive the down leg. That point is exactly where cost stops being an advantage and becomes a gate. | **15.00pp** |
| `committed_capex_aud_m` | Contracted, non-deferrable spend | A funded must-build **burns cash through the drawdown**; a deferrable project is a real option that can be left unexercised. Only the first destroys ounces you have already paid for. | **15.00pp** |
| `production_koz_yr` | Annual production | Sizes the stressed cash flow — how fast the company can earn its way through the drawdown. | **3.63pp** |
| `net_debt_aud_m` | Net debt | Opening liquidity for the stress test, and the maturity wall behind it. | **15.00pp** |
| **AUD gold history** → the Gate 2 anchor | Trailing 3y real average of AUD gold | The stress price. Anchoring to a **trailing average rather than spot** stops the gate weakening exactly when spot is most extended — i.e. when survival risk is actually highest. | **15.00pp** |
| `gate2.gold_drawdown` = 0.40 | Depth of the stress | §0.1: a levered book must survive the down leg to compound ounces through a cycle. This is how deep a hole each name must climb out of. | **15.00pp** |
| `gate2.count_undrawn_facilities` = true | Does a revolver count as survival | Decides whether committed-but-undrawn credit is liquidity or wishful thinking. **It is the parameter that currently decides EVN.** | **3.63pp** |
| `undrawn_facilities_aud_m` | Committed undrawn credit | Liquidity that exists but is not on the balance sheet. Absent is read as zero, which makes the gate harder — the safe direction. | 0.00pp *(not binding)* |
| `gate2.cost_inflation_pa` = 0.05 | AISC path through the stress | **Costs do not fall with the gold price.** They did not in 2013, which is why so much of the industry went cash-negative. Holding AISC flat is also an assumption, and it is the optimistic one. | 0.00pp *(bites at 30%)* |
| `gate2.horizon_years` = 2.0 | How long the company must hold out | Two years is where a balance sheet either holds or does not. The 2011–15 drawdown ran roughly four. | 0.00pp *(bites at 6y)* |
| `gate2.tax_rate` = 0.30 | The state's share of stressed cash flow | The sovereign takes its cut before the shareholder sees survival. | 0.00pp *(bites at 80%)* |
| `gate2.anchor` · `anchor_years` = 3.0 · `anchor_inflation_pa` = 0.03 | Window and deflator for the anchor | Put the historical anchor in the same money as the AISC path, which inflates at `cost_inflation_pa`. Setting inflation to zero gives a lower anchor and a harsher test. | 0.00pp *(anchor moves A$4,863–5,922, no name flips)* |
| `study_stage` · `gate2.developer_min_study_stage` | PFS minimum, DFS preferred | **Scoping-study economics move too much to weight a portfolio on.** A pre-PFS ounce count is a geologist's estimate, not a claim. | **5.00pp** |
| `approvals_land_secured` | Permits *and* land access | A permitting checkbox with unresolved native title or freehold access is not access. This is Gate 1 risk arriving at the project level. | **5.00pp** |
| `remaining_capex_aud_m` · `gate2.developer_max_funding_gap_of_mcap` = 0.30 | Residual funding gap vs market cap | **Bounded dilution.** An unbounded funding gap is an unbounded haircut on the claim. 12% dilution is priced; 150% is a zombie. The field is now **dual-role**: it gates here and it enters the denominator at §13.2, and the gate running first is what stops absence reading as zero there. | 0.00pp *(cannot bind — RXL's gap is 0)* |
| **spread history** · `gates.producer_max_spread_pct` = 1.0 · `developer_max_spread_pct` = 4.0 | Median RTH time-weighted quoted spread | **A claim that cannot be exited is not a position.** Spread rather than market cap, because cap is a proxy and spread is the thing itself. Developers get a wider limit because they are bought once and held to first pour. | **5.00pp** |
| `gates.spread_window` = 3M | Measurement window | Long enough that one disorderly session cannot decide a gate. | live |
| `gates.spread_measure` | Assertion, not a threshold | Halts the run if config claims to measure something the code does not. The gate ran on post-close quotes once and would have dropped 8 of 14 names on an artefact. | assertion |

### 13.4 Caps and classification

Every cap answers the same question, and it is the one §0 already asks:
**how much of the claim can a single uncorrelated operational failure destroy
permanently?** A fault, a flood, a tenement dispute or a fraud does not mark a
claim down — it removes it.

| Factor | What it represents | Why it pays into the goal | Δw |
|---|---|---|---|
| `constraints.max_single_name` = 0.15 | No one company is the index | `P(permanent impairment) ≈ 0`. Not a diversification target — Eff N is reported and never optimised toward. | 0.00pp *(no longer binds — the 10% cap catches PNR first)* |
| `constraints.max_developer_single_name` = 0.05 | Pre-production per-name cap | A developer can fail **outright** — no cash flow, no fallback asset, and the claim goes to zero rather than to a discount. | **7.91pp** *(binds on RXL)* |
| `constraints.max_developer_sleeve` = 0.15 | Pre-production sleeve cap | Bounds the aggregate of that failure mode. Sized to what qualifies, never forced to fill. | 0.00pp *(per-name cap binds first)* |
| `largest_asset_pp_share` | Share of eligible P&P reserves at one asset | Where there is no second asset, there is nothing to absorb the failure. **Sourced for all 17 on 18 Aug 2026** from per-asset Ore Reserve tables. Replaces the `single_asset` boolean, which was a hand-set judgement seventeen times over; the judgement now sits in one config threshold where the audit can see it. | **5.00pp** *(on PNR)* |
| `constraints.single_asset_pp_share_threshold` = 0.80 | Where the derived boolean flips | The only judgement in the classification, and it is declared rather than baked into the data. Set where the cross-section has a gap: nothing sits between 0.773 and 0.999. Tri-state — an absent share derives `None`, asserted on every build. | **3.30pp** *(on CYL; 1.70pp latent on WGX)* |
| `constraints.max_single_asset_name` = 0.10 | Tighter cap for one-mine companies | Derived from the objective, unlike the variance cap it replaced, which was calibrated on daily price noise and appeared nowhere in the mandate. **Binds on PNR and CYL.** Costs +6.4% on A$/claimed oz — see §8.1. | **5.00pp** |
| `sleeve` | producer / near-producer / developer | Not a number — a classification that **routes three tests at once**: the Gate 2 variant, the Gate 3 spread limit, and the developer caps. | routing |

### 13.5 Read, printed, and structurally unable to reach a weight

Pushed to absurdity, every one returns **exactly 0.000pp**. None of these is part
of the model, and none should be described as though it were.

| Factor | Verified by | What it is for instead |
|---|---|---|
| **Gold spot** | A$3,000 / A$6,216 / A$12,000 → identical book | Diagnostics and the §9 NAV report. Gold enters the *weights* nowhere; it enters the *gates* once, through the Gate 2 anchor. |
| `reserve_price_aud`, `resource_price_aud` | deleted from all 17 → 0.000pp | The §6 ledger's most informative disclosure: how far below spot the P&P tranche is booked, and therefore how under-booked it is. |
| `mr_total_moz` | deleted from all 17 → 0.000pp | Reconciling the ledger against the disclosed resource total. |
| `advt_shares_m`, `gates.capacity_max_*` | 5 days → 0.01 → 0.000pp | The §4.3 capacity report. Enforces nothing at €1m. |
| `nav_model.*` — discount rates, decks, bumps | 5% → 25% → 0.000pp | The §9 implied deck. No rate to defend because nothing depends on one. |
| `objective.beta_target` | set to [0.1, 0.2] → 0.000pp | A **check** on the §0 band, reported and flagged. Never optimised toward. |
| `risk.*` — estimator, lags, window; β_gold, R², σ_idio | Dimson → contemporaneous → 0.000pp | Diagnostics. §10 records why σ_idio stopped being a denominator. |
| EURAUD | — | Basket sizing only. |

### 13.6 Two consequences worth stating

**The gold price does not enter the weights.** Four times spot, identical book.
That is a design consequence rather than a coincidence: the numerator counts
ounces and the denominator counts dollars paid, and neither asks what an ounce is
worth today. Any term that divides by spot re-scores the book on the gold price
at every rebalance; there is none. **The practical
effect is that a gold rally on its own now generates zero turnover.** Rebalancing
is driven by ounces, share counts, balance sheets and prices, which is what §12's
cadence is aligned to.

**Read a 0.000pp line carefully.** Six of the seven largest measured effects are
*exclusions*, not reweightings — the binding constraints have moved to the gates
and the caps, exactly as a lexicographic architecture should. So "0.000pp" now
usually means *this input decides nothing at today's values*, which is a much
weaker statement than *this input is known*. `tools/sensitivity.py` says so in
those words for the same reason.

---

*SJGV v1.0 — 18 August 2026. The sole methodology in force.*
