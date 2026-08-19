# Index Methodology — SJGV v1.5

**Index Name:** Stable Jurisdiction Gold Value (SJGV)
**Version:** 1.5
**Date:** 20 August 2026
**Status:** In force.
**Structure:** Private vehicle. Not UCITS, not RIC, not 40 Act. No regulatory diversification constraints apply.
**Simulation AUM:** €1,000,000 (≈ A$1.64M)

> **One formula, no scores.** A weight is claimed unhedged ounces divided by what
> those ounces cost all-in. There is no second step, no composite, and no term
> that does not change either how many ounces are claimed or what was paid for
> them. §6 is the ledger and §7 is the weight; together they fit on a page.

**Amendment record.** A gate definition may not change without a line here.

| # | Date | Change |
|---|------|--------|
| 5 | 20 Aug 2026 | **§3.2 horizon limb resolved on materiality; version 1.4 → 1.5. No weight moves today, and that is the point.** The v1.3 shortfall report is retained and now carries a gate. **Binding on coverage was rejected**: the missing figure is FY28 guidance, Australian miners guide one year ahead, so the rule could not be satisfied by diligence and would grade disclosure format — OBM publishes an FY27+FY28 phasing table and RRL publishes one year, identical solvency, opposite verdicts. PR #5 proposed it; applied as its own §2 states rather than as its §4.1 tabulates it would have left **four constituents at an effective 3.6 and a 30% top weight the §8.1 caps cannot hold**, breaking the objective's own `P(permanent impairment) ≈ 0` to enforce a survival test nothing was failing. What gates instead is whether the shortfall could decide anything: the guided annual leg is continued across the unsourced remainder and the pass must survive it, at `gate2.horizon_continuation_cover` = 1.0. Cover runs 2.0× (GGP) to 18.8× (CYL), so it binds on nobody today — the §6.4 discipline — and it would have caught PNR independently at 0.51×. WGX has no established period and therefore no leg to continue: reported **UNTESTED** and routed to §12.2 item 6, whose trigger is the early-September Strategic Outlook. New sourced field `annual_leg_aud_m`; new parameter `gate2.horizon_continuation_cover`. |
| 4 | 20 Aug 2026 | **Binding text corrected; version 1.3 → 1.4. No rule changed and no weight moved by this line.** Four misstatements in the binding document, all found by external review and all landed from PR #5. **§0** stated the construction as `maximise ClaimedUnhedgedOunces / FundedEV subject to …`; nothing searches over portfolios, each name is held in proportion to its own claim yield, and the section now says so and prices the difference — a literal cap-filling optimiser reaches ~A$630/oz over 8 names against the proportional book's A$739 at an effective 10.2. **§0.2, §6.1, §9.2 and §13.1** described JORC categories as option moneyness and said a falling cut-off moves ounces from M&I into P&P; confidence and economics are orthogonal axes, conversion needs the Modifying Factors at PFS level or better, and Inferred cannot convert at all until upgraded. **§3** listed a debt maturity schedule among the engine's inputs, which the engine does not consume. **§7.2 and §10.2** froze A$684/A$910 and A$640/A$910 into the binding text while the engine emitted neither — the §12.3 defect applied to an output; live figures now come from the build and its snapshot only. |
| 3 | 19 Aug 2026 | **§3.2 added — Gate 2 input basis; version 1.2 → 1.3.** `estimation_policy.on_absence` requires a gate verdict to be invariant across a range it cannot pin down, and that rule was wired for *absent* inputs only. **A value recorded at the midpoint of a range the issuer published bypassed it**, and on one name it was deciding the gate: Pantoro's AISC is the midpoint of its own FY27 guidance of A$2,800–3,400/oz, passing by A$51m at the midpoint and failing by A$12m at the top of the same sentence. Invariance across issuer-published ranges now **gates**, and **PNR is rejected** — the only name it decides; every other constituent is invariant, including Capricorn across its disclosed ±25% no-contingency band. Separately, `committed_capex_aud_m` now carries `horizon_years`, because seven constituents charge one guided year against the two-year window and Westgold's record establishes no period at all; that shortfall is **printed, not filled**, since annualising a guided year is `estimation_policy.forbidden`. **This moves weights: PNR out, 10.00pp one-way turnover, headline A$662 → A$739/oz.** |
| 2 | 19 Aug 2026 | **§2.1 A2 redefined; version 1.1 → 1.2.** A2 is now measured on the **currency issuer** rather than on consolidated general government, and carries a third limb: **gross debt ≤ 85% of GDP**. **This is a rule change and not a sourcing fix, and the direction matters.** §12.2 item 4 asked for Canada's specified metrics to be sourced and A2 applied as written. Sourced, **Canada passes A2 as v1.1 wrote it** — general government net debt ~10–13% of GDP, *below Australia's ~19%*, and general government interest 8.8% of revenue against a 10% limit. Recording a FAIL against that would have been the v1.0 A4 defect exactly: the test passing and the verdict recorded anyway. The rule was therefore changed in the open. On the amended rule Canada fails twice — gross debt 105–110% of GDP, and **federal** interest at 10.3% of revenue. What the change gives up, and the Maastricht threshold rejected on measurement, is in §2.1. **No weight changes** — `data/sovereign.json` is a record, no engine code reads it, and Canada's exclusion is unchanged, so `eligible_ounce_share` does not move for EVN, VAU or NST. §12.2 item 4 closes; item 5 stays open. |
| 1 | 18 Aug 2026 | **§2.1 A4 redefined; version 1.0 → 1.1.** v1.0 gated A4 on requisition history *and* on statutory powers suspended rather than repealed. Australia fails that test on both limbs and the v1.0 table recorded it as a PASS regardless. A4 is now a present-tense test of gold controls **in operation**; dormant powers and historical use are disclosed per country and carried as residual risk (§11.1). What the change gives up is stated in §2.1, not buried. **No weight changes** — `data/sovereign.json` is a record, and no engine code reads it. Canada's A2 and the s51(xxxi) characterisation question are reopened as §12.2 items 4 and 5. |


---

## 0. Objective

> **Own the largest possible claim on future unhedged gold ounces, per euro
> invested, in jurisdictions running no gold-control regime and holding the
> weakest motive to start one — and survive the drawdown in between.**

That is the mandate. The construction rule that serves it is **fixed, not
searched**:

```
eligible_i     only after Gates 1-3 and the §6.4 currency bar
RawWeight_i  =  ClaimedUnhedgedOunces_i / FundedEV_i
Weight       =  normalise(apply_declared_caps(RawWeight))
reported        β_gold ∈ [1.4, 1.8]
constrained     P(permanent impairment) ≈ 0 — via the §8.1 caps
                P(forced equity issuance in a 40% real drawdown) ≈ 0 — via Gate 2
```

**Read that as a construction, not as an optimisation.** Earlier versions of this
section wrote `maximise ClaimedUnhedgedOunces / FundedEV subject to …`, which is
not what the engine does and overstates the claim. Nothing searches over
portfolios. Each qualifying name is held in proportion to its own claim yield, so
the book is a weighted harmonic average of those yields rather than the best
attainable one. Measured on the current book, a literal cap-filling optimiser
would buy the cheapest claim to its cap before the next and land near **A$630/oz
across 8 names**, against the proportional book's A$739 at an effective 10.2.
Proportional weighting costs roughly 5% on the headline and buys the
diversification — the same trade §8.1 prices for the single-asset cap, and it
should be quoted the same way.
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

A mine can be read economically as a bundle of contingent claims on gold: each
ounce carries a cost to extract and a date it would be mined, so a higher price
brings more of the bundle into the money. That intuition is why the ledger counts
more than reserves.

**But JORC categories are not moneyness labels, and this section used to say they
were.** Measured, Indicated and Inferred describe *geological confidence* — how
well the tonnes and grade are known. Ore Reserves are the economically mineable
subset of Measured and Indicated Resources, after the Modifying Factors are
applied at a Pre-Feasibility level or better. The two axes are orthogonal: a
sparsely drilled ounce can be richly economic and a densely drilled one
marginal. Calling M&I "near-money" and Inferred "the far out-of-the-money tail"
conflated confidence with economics, and the conflation is withdrawn.

A higher gold price can lower an economic cut-off and enlarge the material with
reasonable prospects for eventual economic extraction. **It cannot by itself
upgrade geological confidence, and it cannot by itself convert a Mineral Resource
into an Ore Reserve** — the study work and the Modifying Factors still have to be
done, and Inferred material cannot support a Reserve at all without first being
upgraded.

**Counting all three at 1.0 / 0.5 / 0.2 is SJGV's declared confidence discount
and its optionality position.** Those three numbers are a methodology choice, not
a restatement of anything JORC means. Nothing else in the weighting formula adds
a second optionality term.

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
CURRENCY Statement not >18mo old   →  binary, §6.4. A precondition on counting.
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
| A2 | **Sovereign solvency** | **Currency issuer.** Net debt/GDP; gross debt/GDP; interest/revenue | Net debt ≤ 60% of GDP **and** gross debt ≤ 85% of GDP **and** interest ≤ 10% of revenue. Any one breach fails |
| A3 | **Gold as strategic export** | Gold's share of national goods exports | **Disclosed, not gated** — see note |
| A4 | **Gold controls in operation** | Confiscation, compulsory delivery, administered monopsony or gold-export prohibition **in force at the review date**, verified against primary law | None in operation. Dormant powers and historical use are **disclosed, not gated** — see note |

**Rationale for A1.** A country whose currency devalues freely has no need to
repress gold — the FX does the adjustment continuously and without policy
intervention. A reserve-currency issuer has both a unique motive (managing
devaluation while defending reserve status) and unique tools. A currency-union
member has neither monetary control nor exit.

**Rationale for A2, and what v1.1 left unspecified.** A2 is a **motive** test, and v1.1 never said whose motive. It named "general government" for the debt limb and left the interest limb's consolidation level open, which is how Canada came to be excluded on a gross figure by a rule written on a net one.

The entity being tested is **the one that can act**: the government that issues the currency, directs the central bank and could proclaim a bullion control. A1 already scopes Gate 1 to exactly that entity. A province, a state or a canton cannot print, cannot impose exchange control and cannot requisition gold, so consolidating its balance sheet into the test answers a question the gate is not asking. A2 is therefore measured on the national government, with general-government figures recorded alongside as context.

**And netting has limits.** Net debt credits a sovereign with assets that are earmarked, illiquid, or owned by somebody else. Canada is the worked case and it is stark: general government net debt of ~10% of GDP — *lower than Australia's ~19%* — against gross debt of 105–110%, a gap that is almost entirely CPP/QPP social-security assets. Those assets are legally committed to pension obligations. A pension fund's equity portfolio does not service the sovereign's coupon. Excluding social-security funds, Statistics Canada puts general government net financial liabilities near 50% of GDP, and the federal government already spends **10.3 cents of every revenue dollar on interest**, with the Parliamentary Budget Officer projecting 13.1% by 2030-31.

So the third limb is **gross debt**, because gross debt is what must be *rolled*, and rollover at rising rates is the actual channel from solvent-on-paper to reaching-for-the-metal.

**The threshold is 85%, and it is set in a gap rather than derived.** Say so plainly: nothing recorded falls between Australia at ~61% general government (~36% Commonwealth) and Canada at ~105–110%. That is the same construction as `constraints.single_asset_pp_share_threshold`, which sits at 0.80 because nothing in that cross-section lies between 0.773 and 0.999. **The Maastricht 60% reference value was tried first** — the externally-anchored number that could not be accused of being tuned — and rejected on measurement: on the IMF's general-government basis Australia reads ~61% and would fail it, leaving the index with no eligible jurisdiction. A rule that vetoes the entire asset class is not a gate; it is a decision not to run the product, and §2.1 has already refused that once. The 85% bar applies prospectively and evenly. **If Australian general government gross debt reaches it, Australia fails and there is nothing left to hold.**

**What this amendment costs, stated rather than buried.** Canada's exclusion now survives on the amended rule and would *not* survive on the rule as v1.1 wrote it. That is a real concession and it is the reason the change is an amendment-record line rather than a note: a reader is entitled to see that the test was rewritten and to disagree with the rewrite. The defence is that v1.1's A2 was underspecified rather than wrong, that the specification chosen is the one A1 already implies, and that it was fixed before the number decided anything — the eligible universe is unchanged, so nothing in the book moved and nothing in the book was protected.

**Rationale for A3, and why it is not gated.** A sovereign taxes what it needs
and seizes what it lacks. A state earning materially from a productive gold
industry has a structural incentive to keep it productive. But failing this test
does not imply a state *will* expropriate — only that it has no stake in
defending you. Gating on it would exclude New Zealand for a reason unrelated to
expropriation risk. **A3 is binary, and no
code ever read it.** It is now disclosed per jurisdiction and reasoned about, not
converted to a number that does nothing.

**Rationale for A4, and what v1.0 got wrong.** v1.0 gated on two things: no
requisition in the modern era, and no statutory power suspended rather than
repealed. **Australia fails both.** Part IV of the Banking Act 1959 (Cth) —
compulsory delivery of privately held gold to the Reserve Bank, an export ban, a
purchase monopsony — *was in operation* until 30 January 1976, when it ceased by
Proclamation under s 40(3), gazetted 1976 No S17. It has never been repealed, and
Parliament has not left it to rot: ss 41, 42, 45 and 46 have been amended since,
most recently by No 4, 2016. The v1.0 table nonetheless recorded Australia as a
PASS. That was not a data gap waiting on counsel. It was the test failing, and the
PASS was the tell.

Applied evenly, the v1.0 rule excludes almost every rule-of-law state, because
almost all of them kept their wartime bullion machinery on the statute book. A
rule that vetoes the entire asset class — including the only jurisdiction with a
material industry — is not a gate. It is a decision not to run the product,
disguised as a test.

What a statute-book search *can* establish is present tense: **is a gold-control
regime operating in this jurisdiction now?** That is binary, verifiable from
primary law, and it is a real exclusion — any state currently running bullion or
exchange controls is out. What it cannot establish is whether a state will
legislate one tomorrow. **The motive test is A1 and A2.** A reserve issuer
managing devaluation, or an insolvent one, has a reason to reach for the metal; a
solvent state whose currency devalues on its own does not. A4 tests the
machinery. Machinery that is not running is a disclosed residual risk, not a veto.

Two consequences, stated rather than buried:

1. **As at August 2026, A4 excludes none of the five recorded countries.** The
   v1.0 A4 excluded four of five — but only by a test Australia also failed. All
   of Gate 1's exclusionary force now sits in A1 and A2, which is where it was
   doing the work all along.
2. **This test would not have caught a dormant EO 6102.** EO 6102 was a public
   executive instrument and surrender was paid at a published statutory price; it
   fails A4 only while it is operating. That weakness is accepted deliberately,
   because any formulation strong enough to catch a dormant EO 6102 also catches
   Banking Act Part IV — which is to say it catches Australia, and there is
   nothing left to hold.

Dormant powers are recorded per country in `data/sovereign.json` under
`dormant_powers`. Only Australia's has been compiled to primary-law standard;
the others are recorded, not verified, and say so. The Australian register —
every provision, its activation route, and whether any compensation reaches it —
is summarised in §11.1, and it is worse than a single reassuring sentence about
s 44 would suggest.

### 2.2 Tier A outcome as at August 2026

| Country | A1 | A2 | A3 | A4 | Verdict |
|---------|----|----|----|----|---------|
| **Australia** | Pass — AUD free-floating, non-reserve, commodity currency | Pass on all three — net debt ~19%, Commonwealth gross ~36% (general government ~61%), interest 3.5% of revenue | **Strong — gold is the #2 export at ~A$68bn, having overtaken coal** | Pass — none in operation. Banking Act 1959 Pt IV ceased 30 Jan 1976 (s 40(3), gaz 1976 No S17); unrepealed and disclosed at §11.1 | **PASS** |
| New Zealand | Pass | Pass | Weak — immaterial to exports | Pass — none in operation | **Pass** (no eligible listed vehicle) |
| Canada | Pass | **Fail — gross debt 105–110% of GDP against the 85% limb, and federal interest 10.3% of revenue against the 10% limb. Net debt ~10–13% passes** | Moderate | Pass — none in operation; 1939–51 Foreign Exchange Control Board regime disclosed | **FAIL — A2** |
| Finland | **Fail — euro membership** | Gross ~80% and rising — *inside* the 85% limb today, so A2 no longer carries this exclusion | Weak | Pass — none in operation | **FAIL — A1** |
| United States | **Fail — reserve issuer** | **Fail — net 100% → ~120%; gross 126% → 142% by 2031** | **Weak** | Pass — none in operation; 1933–42 interventions disclosed, and see §2.1 consequence 2 | **FAIL — A1 and A2** |

Norway, Sweden and Switzerland pass cleanly and host no gold mining of scale.
**Australia is the only Tier A pass with a material industry.**

Read the A4 column honestly: **it now excludes nobody.** Canada, Finland and the
United States are excluded on solvency and monetary sovereignty.

Canada's exclusion rests on A2 alone, and **§12.2 item 4 closed on 19 August 2026
by changing A2 rather than by sourcing it.** The mismatch item 4 identified was
real: the recorded evidence was general government *gross* debt against a
threshold written on *net* debt. Sourced, the specified metrics **passed** —
Canadian general government net debt is ~10–13% of GDP, below Australia's ~19%,
and general government interest is 8.8% of revenue against a 10% limit. So the
choice was to admit Canada or to change the rule, and the rule was changed: A2
now measures the currency issuer and carries a gross-debt limb (§2.1). Canada
fails both new limbs. **Two things follow that should not be smoothed over.**
First, this exclusion would not survive the v1.1 rule, and the amendment record
says so. Second, Canada's A4 dormant-power register was never compiled to the
standard applied to Australia — `data/sovereign.json` records the gap — and it
stays uncompiled only because A2 still excludes the country. Revisit A2 and that
work becomes required, starting with the Emergencies Act 1988, invoked in
February 2022 to freeze accounts without a court order and therefore a
*recently exercised* financial-control power rather than a dormant one.

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

**The share is applied per resource category, not as one blend.** Three names
carry ineligible ounces, and for each the data layer records a share per
category as well as the group figure:

| | P&P | M&I non-reserve | Inferred | Blended |
|---|---|---|---|---|
| Northern Star — Pogo (Alaska) | 91.6% | 92.7% | 85.6% | 91.0% |
| Vault — Sugar Zone (Ontario) | 100.0% | 84.2% | 87.9% | 92.9% |
| Evolution — Red Lake (Ontario) | 83.3% | 76.1% | 70.4% | 80.1% |

The blended figure is itself confidence-weighted — ineligible confidence-weighted
ounces over group confidence-weighted ounces — so multiplying all three tranches
by it is not merely an approximation. It reproduces the **right total claim and
the wrong split**: an ineligible asset that is reserve-light and Inferred-heavy,
as Pogo and Red Lake both are, silently moves claim out of the reserve tranche
and into the tail. That was tolerable while the ledger mix was a curiosity and
became a defect once §10.4 published it as the convexity position — the blend
read 57.3 / 29.6 / 13.1 where the category shares read 57.9 / 29.5 / 12.7 on
the same book,
overstating the inferred tail by 0.5pp *in the direction that flatters the
product*.

Since the blend is an identity over the category shares, the two are a check on
each other: `build_index.reconcile_eligibility` recomputes the blend from the
three shares and reports any disagreement beyond rounding, in the same way
`reconcile_resource` checks the category split against disclosed total resources.
Neither corrects anything. Where the category shares are absent the blend is the
fallback, and it is exact for the fourteen names whose share is 1.0.

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

Engine inputs, all publicly disclosed: cash and bullion, undrawn committed
facilities, free cash flow at the stress price, and committed capital
expenditure. **Debt maturity schedules are read and reported where sourced, but
the engine does not consume a maturity ledger and models no separate
within-horizon repayment.** Net debt enters as opening liquidity, which is
equivalent to assuming the whole balance is repaid at the horizon and is
therefore harsher than modelling actual maturities — every constituent is in net
cash today, so nothing turns on it. This section previously listed the maturity
schedule as an input without qualification, which was a claim the code did not
support. The limitation stays stated until either the code or the coverage
exists.

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

### 3.2 Input basis — the horizon a figure covers, and the range it came from

`estimation_policy.on_absence` already settles what to do with a gate input the
engine cannot pin down: run the gate across the range, and if the verdict differs
at the two ends then **the answer is unknown, not favourable.** That doctrine was
wired for *absent* inputs only. Two ways of being imprecise walked straight past
it, and both ran in the direction that flatters.

**1. A published range recorded at its midpoint — this gates.**
`estimation_policy.permitted_provenance` allows "the midpoint of a range the
issuer itself published" as a derived value, and that is right for recording a
number. It is not right for *deciding* one. Pantoro is the case: its AISC is the
midpoint of the issuer's own FY27 guidance of A$2,800–3,400/oz, and at A$3,100 it
clears the stress by A$51m while at A$3,400 — the top of the same sentence — it
fails by A$12m. A gate settled by which point of a published span the analyst
picked is not a gate.

> **A Gate 2 verdict must be invariant across every range the issuer published
> for an input the gate reads. A name whose verdict flips is UNRESOLVED and is
> rejected**, exactly as an absent input that flips is.

Three boundaries, each deliberate:

- **Issuer-published only.** Vault's committed capex could be A$173m or A$364m
  depending on which capital lines are treated as committed. That span is a
  choice between two analyst conventions, not a range Vault disclosed, and
  probing it would gate on the analyst's indecision. It stays in the note.
- **Each input on its own.** The sweep runs one field at a time, which is what
  the absent-input test already does.
- **The compound is reported, never gated.** Driving every ranged input to its
  against-the-name end simultaneously is a scenario no disclosure asserts. A name
  that survives each range alone and fails their compound is flagged **STRAINED**
  — the same call §4 already makes on a spread that passes on the median and
  breaches on p90. No constituent is STRAINED today.

**2. A figure that covers less window than it is charged against — the coverage
is reported, and its *materiality* gates.** Gate 2 charges
`committed_capex_aud_m` over `horizon_years`, and the cohort does not supply it
on one basis. Ora Banda's is the issuer's own FY27 plus FY28 lines summed.
Greatland's and Evolution's are whole-project totals that run *past* the window,
which over-charges — and overstating a survival cost is the safe direction. But
**Regis's, Vault's, Catalyst's, Northern Star's, Capricorn's KGP leg and
Greatland's Telfer leg are a single guided year charged against two**, and
Westgold's record establishes no period at all. A one-year figure against a
two-year window understates the burn, and `docs/execution-capital-inventory.md`
§3 concluded "direction is safe" from the two names that over-charge without
checking the seven that do not.

Every such figure now carries `horizon_years`, transcribed from the note that
already establishes the period, and **an absent one reads as `unknown`, never as
covered.**

**Gating on coverage itself was considered and rejected.** The missing number is
FY28 capital guidance, and Australian gold miners guide one year ahead — so a
coverage rule could not be satisfied by any amount of diligence, only by
disclosure format. Ora Banda publishes an FY27+FY28 phasing table; Regis
publishes one year. Identical solvency, opposite verdicts. This document has
already deleted one rule for grading disclosure habits rather than substance, and
will not adopt another. Filling the gap is worse still: annualising a guided year
into an unguided one is `estimation_policy.forbidden` in as many words, and a
cohort rate transferred onto an unguided period is the same invention wearing a
peer group's clothes — the cohort's upper rate is Capricorn building a second
mine, which on Westgold's 387 koz would charge A$3.4bn and reject the largest
position in the book on a number nobody has published.

**What gates is whether the shortfall could decide anything.** Take the recurring
annual leg the issuer *has* guided, continue it across the unsourced remainder of
the window, and require the pass to survive:

```
remainder  =  annual leg × shortfall years
probe      =  committed capex + remainder
cover      =  ending liquidity ÷ remainder          ≥ gate2.horizon_continuation_cover
```

> **A pass must survive one more year at the rate the issuer itself guided.**
> A name whose verdict turns on the unguided tail of the window has not passed;
> it is UNRESOLVED, and it is rejected.

The probe is a robustness test and **never an estimate of year two**. No field is
filled from it and nothing records it. It is the same shape `gate_input_invariant`
already applies to an absent input: evaluate at a bound, require the verdict to
hold there. `annual_leg_aud_m` excludes any finite build already spanning the
window, because such a build does not recur — Capricorn's Mt Gibson and
Greatland's Havieron are out of their legs for that reason, leaving A$78m and
A$325m of genuinely annual guidance.

**Adopted while binding on nobody**, which is the §6.4 discipline. Cover across
the book runs from **2.0× at Greatland** and 2.1× at Capricorn to 18.8× at
Catalyst; the two tightest are the mixed names whose project legs already
over-cover. It would have caught Pantoro independently — A$51m of headroom
against a A$101m guided year is **0.51×** — which passed the arithmetic and was
removed by the published-range limb instead.

Swept, the bar is inert to **2.0×** and first ejects Greatland at 2.05×, then
Capricorn at 2.2×. So 1.0 sits a full doubling clear of the nearest name, in the
same kind of gap the 0.80 single-asset threshold occupies, and the setting can be
argued in `config.json` rather than inferred from an exclusion it produced.

**UNTESTED is said out loud and is not a pass.** A record that establishes no
period has no annual leg to continue, so there is nothing to probe. That is not a
horizon question but a capital-**state** question: an unresolved scope. Westgold
is the only such name — A$145m for a Higginsville stage the issuer has deferred
in favour of an uncosted 4 Mtpa case — and it is routed to §12.2 item 6, which
carries its own dated trigger in the Strategic Outlook of early September 2026.
Routing it is a recorded decision, not a silent pass.

The three rules sit at deliberately different strengths, and the ordering is the
point. **A published range** is evidence the issuer supplied about a quantity the
gate reads, so it decides. **A missing period** is evidence nobody supplied, so it
discloses — gating on it would punish disclosure format. **Whether that missing
period could change the answer** is arithmetic on figures the issuer did supply,
so it decides too. Nothing here fills a gap; each rule asks only what the
disclosure already on the record is capable of settling.

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
| **Proven & Probable** | **1.0** | Economically mineable Ore Reserves, after the Modifying Factors have been applied. The ledger's unit of account. |
| **M&I non-reserve** | **0.5** | Higher-confidence Mineral Resources not converted to Ore Reserves. The category describes drilling confidence; it implies nothing about their economics either way. |
| **Inferred** | **0.2** | Lower-confidence Mineral Resources. They cannot support an Ore Reserve without further drilling and study, whatever the gold price does. |

These three numbers are **the only judgement remaining anywhere in the weight**,
and they sit in the numerator where a judgement belongs: they decide how many
ounces are claimed, not how a claim is scored. They are **SJGV's own confidence
discounts applied to JORC categories, not discounts JORC supplies.** Nothing about
them is calibrated on this cohort, on any price history, or on any backtest —
which is precisely why they survived the cut and the scoring layer did not.

**The mix they produce is the headline optionality statistic**, and it is
generated on every build from the current ledger and weights. **No live mix is
frozen into this document** — read the build output and its dated snapshot. It is
published to one decimal rather than whole percent for a reason worth keeping:
the M&I share has sat within 0.01pp of a rounding boundary, so an integer reading
flipped between 29 and 30 on a 0.18pp weight move that changed nothing in the
ledger. Watch the series over time: a book drifting toward reserves is a book
losing its option inventory.

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

### 6.4 Currency of the statement — an 18-month bar

A reserve and resource statement is an **annual** obligation. A ledger input
older than one full reporting cycle plus six months of issuer timing is not a
current claim; it is the last claim, carried forward. So:

> **No counted tranche may rest on a resource statement more than 18 months old
> at the data layer's sourcing date. A name that breaches it is rejected.**

Three properties, each deliberate:

1. **It is a gate, not a discount.** An ounce whose statement has gone stale is
   not a cheaper ounce, it is an unverified one, and there is no coefficient that
   expresses that honestly. Like Gates 1–3 it cannot be offset by cheapness.
2. **It is applied to the document behind *every* counted tranche.** Not to one
   nominated statement — the tranches are separately sourced, and Regis reads P&P
   off a July quarterly and Inferred off an April resource release. The older of
   the two dates the claim. A tranche the ledger does not count (an absent
   Inferred) does not date it.
3. **A month-only date is tested, not rounded.** Two Greatland releases are dated
   only to the month, because that is all the source states. Picking a day would
   be inventing an input. Instead both ends of the month are tested and the name
   passes only if the verdict is invariant across them — the same rule
   `config.estimation_policy.on_absence` already applies to a missing number.
   A statement that straddles the bar fails: the answer is unknown, not
   favourable.

**It binds on nobody today, and that is the argument for adopting it now.** The
oldest ledger document in the book is Rox's July 2025 MRE at 12.9 months; the
median constituent sits at 3.6. Swept downward, the bar first removes a
constituent at **12 months** (Rox), then Vault and Westgold at 11 and Catalyst at
10 — so 18 sits a full six months clear of the nearest name. A rule adopted while it costs nothing is a rule
adopted on its merits rather than to justify an exclusion someone already wanted.
The name to watch is Rox: its Interceptor and Commonwealth resource updates are
flagged for H2 2026, and without them it crosses the bar in January 2027 and is
rejected outright.

Adopted 18 August 2026 from SJGV PR#2, which applied it to non-reserve ounces
only. Extended here to the whole ledger, because a statement eighteen months
stale is no more current for a reserve ounce than for an inferred one.

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

Every build publishes three figures from the same disclosed inputs as the
weights: SJGV's A$ of funded EV per claimed ounce, the same constituents
cap-weighted, and the gap between the two. All three carry no history and
therefore no survivorship or look-ahead bias. **No live A$/oz value is frozen
into this document** — `weights.json` and the dated snapshot are the source, and
this section carried A$684 against A$910 long after both had moved, which is the
§12.3 defect applied to an output instead of a parameter.

**Read the headline together with what the caps cost it.** The §8.1 single-asset
cap pins the cheapest claims in the universe at 10% each, which necessarily makes
the book dearer per ounce; the build reports that difference so the trade is
priced rather than buried. It is a construction statistic, not a literal
look-through purchase price for an ounce.

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

**Sourced and live from 18 August 2026.** It bound on two constituents when it was
adopted. **From 19 August 2026 it binds on Catalyst alone** — Pantoro left the book at
Gate 2 under §3.2, not at this cap.

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

Real gold-miner convexity comes from the economic cut-off falling as the price
rises, which enlarges the material worth mining. **It does not move ounces from
M&I into P&P by itself**: conversion to an Ore Reserve requires the Modifying
Factors and a study at Pre-Feasibility level or better, and Inferred material
cannot convert at all until it is first upgraded on drilling. The issuer has to
do that work, and the ledger sees it only when the issuer reports it. That is the
measurement this ratio cannot make.

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

So the **generated ledger mix** is not a placeholder for a better measure that is
coming. It is the measure. Unlike this ratio it is made entirely of disclosed
ounces rather than of a model's blind spot. **Report the dated mix from the build;
treat the 1.00 as a statement about the model; and do not let a future session
reopen the gap by assuming a cut-off elasticity, which would manufacture the exact
number the product is judged on.**

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

**Generated on every build, and deliberately not written down here.** This
section carried A$640 against A$910 while §7.2 carried A$684 against A$910 and the
engine emitted neither — three published figures for one statistic, none of them
current. The headline and its cap-weighted comparator now come from the build
output and the dated snapshot only.

It replaces the asymmetry ratio as the headline. It is computed from the same
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
   August 2026 and bound on **Pantoro and Catalyst**, at a cost of A$41 per
   claimed ounce on the headline KPI. Pantoro has since been rejected at Gate 2
   (§3.2, 19 Aug 2026), so the cap now binds on Catalyst alone and the book is
   **three of eleven** single-asset constituents: CYL, GGP and RXL.

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

Not resolved; accepted unquantified. Both are disclosure items. The first is no
longer a *query* — it is now read, and it is worse than v1.0 recorded.

| Item | Nature of the residual risk |
|------|------------------------------|
| **Banking Act 1959 (Cth) Part IV — Gold** | Read against compilation C2026C00104 (Compilation No. 69, to 31 March 2026). Part IV ceased to be in operation on **30 January 1976** by Proclamation under s 40(3), gazetted 1976 No S17 — so it is not merely dormant, it *ran*, until living memory. It has not been repealed, and ss 41, 42, 45 and 46 have been amended since suspension, most recently by No 4, 2016. **Revival is a same-day executive act:** s 40(2) lets the Governor-General, satisfied it is expedient for the protection of the currency or the public credit, declare by Proclamation that the Part comes into operation. **The register:** s 41 export ban; s 42 compulsory delivery to the Reserve Bank; s 43 vesting; s 44 payment; s 45 sale and purchase only to or from the Reserve Bank — an administered monopsony; s 46 prohibition on working gold; s 48 discretionary Reserve Bank exemptions. **Two things make the compensation story thinner than it first reads.** s 44 pays only for gold *"delivered in pursuance of section 42"* — ss 41, 45 and 46 carry no compensation provision anywhere in Part IV. And s 40(2) permits **partial** activation, "such of the provisions of this Part as are specified in the Proclamation", so an export ban plus a monopsony plus a manufacturing prohibition can be switched on with s 44 left off entirely. Where s 44 does apply, the price is administered by the Reserve Bank, with an action for compensation against it as the only route to a different number. Unpriced. |
| **Does s51(xxxi) reach the control limbs of Part IV?** | Part IV is Commonwealth law, so the just-terms guarantee reaches it — a stronger floor than s 44, and the point the first attempt at this record missed. But Australian law distinguishes *acquisition* of property from mere deprivation or regulation. Compulsory delivery and vesting (ss 42–43) is plainly an acquisition; *Newcrest Mining v Commonwealth* (1997) 190 CLR 513 is live precedent that sterilising mining tenements can be one too. An export ban, a monopsony or a ban on working gold may instead be characterised as regulation, attracting no just-terms obligation at all. **The compensation floor is firm for the delivery limb and genuinely contestable for the control limbs.** This is the question for Australian counsel — §12.2 item 5. |
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
established the data does not exist. **Two opened the same day**, on the back of
the A4 amendment: items 4 and 5. **Item 6 opened on 19 August 2026** and is the
only one of the three that is a defect in the live build rather than a question
about it. **Item 4 closed on 19 August 2026**, by an A2 amendment rather than by
the sourcing it asked for — the sourcing came back the other way. Two items are
open: 5 and 6.

| # | Item | Outcome |
|---|------|---------|
| 1 | **Single-asset status, all 17.** | **CLOSED — sourced.** Replaced the unsourced `single_asset` boolean with a sourced `largest_asset_pp_share` and a declared 0.80 threshold (§8.1). Eight of seventeen flag, not the four §11 named; the cap bound on **PNR and CYL** when adopted (CYL alone from 19 Aug 2026, §3.2), 7.52% one-way turnover, and it costs **+6.4% on A$ per claimed ounce**. Three regression names behaved: PNR and RXL returned 1.000, CMM returned 0.700 under the forward rule fixed before the number was computed. |
| 2 | **Grade-tonnage curves.** | **CLOSED — not sourceable from public disclosure.** Phase 0 survey over ≈11 MB of primary text across all seventeen: **zero of twelve constituents** publish a resource at two or more cut-offs or a grade-tonnage table. One partial (RXL, a *chart* for its underground resource only) and one unknown (WGX's five NI 43-101 reports, issuer URLs dead). Full write-up and the three findings that would have blocked Phase 2 regardless: `docs/grade-tonnage-survey.md`. **The §6 ledger stays static in the gold price and §9.2's modelled 1.00 keeps saying what it says.** |
| 3 | **Jurisdiction B1 / B3 verification.** | **CLOSED — verified.** B1 verified from statutory instruments for every exposed jurisdiction: WA 2.5% flat, VIC 2.75% flat, NSW **4.0% flat** (confirming a claim §2.3 was making ahead of its data), QLD a **price-linked 2.5–5.0% scale saturated at its 5% ceiling**, TAS profit-based capped at 5.35% and **no longer an exposure** (Henty sold May 2025). WA **B3 verified**, and it reframed the test: no statutory determination periods, 42.4% on-time against an 80% target. `jurisdictions.json` records the statutory instrument for each. Remaining unverified: B1 for SA, NT and NZ (nil exposure), and B2/B3/B4 outside WA. |
| 4 | **Canada's A2, now load-bearing alone.** | **CLOSED 19 Aug 2026 — sourced, and then the rule was changed. Read both halves.** Sourced first, as the item asked: Canadian general government net debt is **~10–13% of GDP — below Australia's ~19%** — and general government interest is **8.8% of revenue** against a 10% limit. **Canada passed A2 as v1.1 wrote it.** Recording FAIL anyway would have repeated the v1.0 A4 defect one amendment after fixing it. So A2 was rewritten instead (§2.1, amendment 2): measured on the **currency issuer**, with a third limb at **gross debt ≤ 85% of GDP**. Canada fails on gross (105–110%) and on federal interest (**10.3%** of revenue, PBO projecting 13.1% by 2030-31); the net-debt limb still passes and is not the basis. **Zero weight change** — Canada stays out, so no `eligible_ounce_share` moves, and no engine code reads `data/sovereign.json`. What the closure leaves behind is recorded in §2.2: the exclusion does not survive the old rule, and Canada's A4 dormant-power register remains uncompiled by decision. |
| 5 | **Does s51(xxxi) reach the control limbs of Banking Act Part IV?** | **OPEN — opened 18 Aug 2026 by the A4 amendment.** Australian counsel, and the one question in this file a search engine genuinely cannot answer. s 44 compensates only gold delivered under s 42, and s 40(2) permits partial activation, so the export ban (s 41), the monopsony (s 45) and the prohibition on working gold (s 46) can operate with no statutory compensation. Whether the just-terms guarantee reaches them turns on the acquisition-versus-regulation distinction. **This does not gate** — A4 is present-tense and Part IV is not in operation — but it sizes the residual risk in §11.1, which is currently unpriced. |
| 6 | **`remaining_capex_aud_m` does two incompatible jobs, and the §7.1 denominator gets the wrong one.** | **OPEN — opened 19 Aug 2026, and this one moves weights.** Gate 2 D3 needs the **residual funding gap** (financing capacity); the §7.1 denominator needs **gross remaining execution capital** (economic cost). One field carries both, so three conventions are live in the book at once: AUC gross at A$354m, AAR net of cash at A$162m, and **RXL net of cash *and* drawable debt at A$0m** — the full A$382.6m Youanmi DFS pre-production capital enters the denominator of a current 5%-capped constituent as zero. Where the gap is derived net of cash, EV has already netted it and the cash is credited twice. The mirror error is larger: **producers are charged nothing at all** for board-approved builds, so GGP's A$1,065m Havieron capital and CMM's A$474m Mt Gibson capital are absent from a denominator that charges developers for the same activity. Full diagnosis: `docs/asset-evidence-capital-proposal.md`; per-constituent sourcing: `docs/execution-capital-inventory.md`; production decisions: `docs/capital-gate2-production-decision.md`. **THE BLOCKER WAS MISRECORDED AND IS CORRECTED 20 Aug 2026: it is WGX, not EVN.** EVN's four gross board-approved totals are an admissible `UPPER_BOUND` — treating all approved capital as remaining omits no spend and can only raise the denominator, which is the convention RXL and RMS already use. It is a poor bound, not an inadmissible one. WGX is the genuine blocker: A$145m is a lower bound on a scope now deferred in favour of an uncosted 4 Mtpa case, and the issuer separately calls further Murchison milling committed without costing it. Also settled: **CMM enters at A$593m**, the upper end of the issuer's own disclosed ±25% band, rather than A$474m relabelled a `POINT` when the same source says no contingency is included; **GGP holds at A$1,065m** with its June 2025 cost base recorded and no assumed spend-down. |

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

**51 inputs, and no others.** Established by perturbation rather than by reading
the code: every candidate input was moved and the resulting book compared. `Δw`
is the largest change in any single final weight, at ±50% on a data field and
±40% on a parameter. A factor that is *read* but cannot change a weight is listed
in §13.5 and should never be described as part of the model.

### 13.1 Numerator — the ounce ledger

Everything here answers one question: **how many ounces of gold will this company
be able to hand us, and how sure are we?**

| Factor | What it represents | Why it pays into the goal | Δw |
|---|---|---|---|
| `pp_moz` | Proven & Probable reserves | **The economically mineable tranche** — ounces the issuer has carried through the Modifying Factors and into a mine plan at a published cost. This is the floor under the claim: the part that converts to metal without needing the gold price to do anything. | **1.03pp** |
| `mi_non_reserve_moz` | Measured & Indicated resource not yet booked as reserve | **The largest single source of the index's optionality.** Drilled densely enough to support a mine plan, not converted to reserve at the company's own price deck. A higher price can make more of this material worth mining, but conversion still needs the Modifying Factors and a study — §0.2. The category is a confidence statement, not a moneyness one. | **0.65pp** |
| `inferred_moz` | Inferred resource | **The lowest-confidence tranche.** Geologically real but sparsely drilled, and it cannot support an Ore Reserve at any gold price until it is upgraded on further drilling. Counted at a fifth precisely because that conversion is neither certain nor free. | **0.43pp** |
| `eligible_ounce_share` | Share of ounces under a Tier A sovereign | **Gate 1 expressed as a number instead of a verdict.** An ounce sitting under a gold-control regime, or under a state with the motive to start one, is not an ounce we own, so it is discarded at source rather than haircutting the company. This is the half of the objective that is not about leverage. Now the *fallback*, exact for the fourteen names at 1.0 and for the total claim of the three that are not. | **0.12pp** |
| `eligible_pp_share` · `eligible_mi_share` · `eligible_inferred_share` | The same Gate 1 share, per resource category | The blended figure is confidence-weighted, so applying it to each tranche gets the **total right and the split wrong** (§2.4). Sourced for the three mixed-jurisdiction names from the per-asset counts their group figure was already derived from, so nothing new was fetched. *Adopting* them moved no weight by more than 0.01pp; what moved was the **published ledger mix**, from 57.3/29.6/13.1 to 57.9/29.5/12.7 on the book as it then stood. The current mix reads 57.8/29.5/12.7 because the later Westgold net-debt correction moved that name's weight. | **2.27pp** / 1.08pp / 0.53pp |
| `hedge_share_fwd24m` | Production already sold forward | A sold-forward ounce is **a short gold position inside a long gold product.** It converts at a fixed price and cannot participate in the move the index exists to capture, so it is subtracted from the claim rather than scored against it. | **0.06pp** |
| `production_koz_yr` | Annual production rate | In the ledger it does one job: converting the disclosed hedge *percentage* into hedged *ounces*. (Also a Gate 2 input, where it does much more.) | via hedge |
| `confidence_weights.proven_probable` = 1.0 | An Ore Reserve ounce = the unit of account | The numéraire of the ledger. Every other ounce is priced relative to this one, so it is definitional rather than tunable. | **0.74pp** |
| `confidence_weights.measured_indicated_non_reserve` = 0.5 | An M&I non-reserve ounce is worth half a reserve ounce | **The single most consequential dial in the methodology.** It sets the price the index pays for optionality: raise it and the book tilts toward explorers and undeveloped inventory, lower it and it tilts toward producing reserves. It is how much convexity the index buys, expressed as one number. | **0.50pp** |
| `confidence_weights.inferred` = 0.2 | An Inferred ounce is worth a fifth of a reserve ounce | Deliberately harsh. Inferred material cannot legally support a mine plan, so a fifth is a discount that survives being wrong — the index still gets tail exposure without letting a thin drill pattern set a position. | **0.34pp** |
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
| `<input>_range` on a Gate 2 input | The span the **issuer** published, where the recorded value is its midpoint | **The midpoint may record a number; it may not decide a gate (§3.2).** Sweeping each ranged input to both of its own published ends and requiring one verdict is `estimation_policy.on_absence` applied to imprecision that is disclosed rather than missing. It decides exactly one name today and that name is a 10% position. | **10.00pp** *(rejects PNR on `aisc_aud_oz` [2800, 3400])* |
| `committed_capex_aud_m_horizon_years` | Years of the stress window the capex figure actually covers | Sets the shortfall the continuation probe runs over. **Coverage itself never gates** (§3.2) — that would grade disclosure format rather than solvency — but it sizes the test that does. | via the probe |
| `committed_capex_aud_m_annual_leg_aud_m` · `gate2.horizon_continuation_cover` = 1.0 | The recurring guided portion, and how much headroom a pass must hold against it continued across the unsourced tail | **A pass must survive one more year at the rate the issuer itself guided.** The leg excludes finite builds already spanning the window, because those do not recur. Binds on nobody today — cover runs 2.0× to 18.8× — and would have rejected PNR at 0.51×. Adopted while costing nothing, on the §6.4 precedent. | **10.00pp** *(latent: the weight of any name whose cover falls under 1.0×)* |
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
| **resource statement dates** · `gates.max_resource_statement_age_months` = 18 | Currency of the claim (§6.4) | **A stale statement is not a cheaper ounce, it is an unverified one.** One annual reporting cycle plus six months of issuer timing, applied to the document behind every counted tranche. Adopted while it binds on nobody — the oldest is Rox at 12.9 months — which is the only honest time to adopt a gate. Asymmetric under perturbation: loosening it to 25 months changes nothing, tightening it to 10.8 ejects two names. | **12.16pp** *(at ×0.6; 0.00pp at ×1.4)* |

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
| `constraints.max_single_asset_name` = 0.10 | Tighter cap for one-mine companies | Derived from the objective, unlike the variance cap it replaced, which was calibrated on daily price noise and appeared nowhere in the mandate. Bound on PNR and CYL when adopted; **binds on CYL alone from 19 Aug 2026**, PNR having been rejected at Gate 2 under §3.2. Costs +6.4% on A$/claimed oz — see §8.1. | **5.00pp** |
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

*SJGV v1.5 — 20 August 2026. The sole methodology in force.*
