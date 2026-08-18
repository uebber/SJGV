# Execution capital — Step 1 sourcing inventory

**Status:** inventory only. No engine, data, gate, parameter or weight changes.
**Purpose:** establish, per constituent, what the disclosure regime actually supplies
for `remaining_execution_capex_aud_m` and its Gate 2 within-horizon portion, before
any definitional or schema decision is taken.
**As-of:** data layer sourced 2026-08-17; EV from the frozen 2026-08-18 replay anchor.

This is Step 1 of the capital migration proposed in `asset-evidence-capital-proposal.md`.
Two committee decisions were taken before it began:

1. **Gate 2 is in scope.** The §3.4 bridge is to be built and `committed_capex_aud_m`
   re-derived on a strict within-horizon basis in the same pass, rather than frozen.
2. **The annual-guidance names are reported, not pre-judged.** No rule separating
   discrete builds from recurring growth capital is adopted here; this document
   supplies the evidence for that decision.

Nothing below is a new fetch. Every figure is already in `data/companies.json`,
sourced to a primary document. Step 1's remaining fetch work is listed in §6.

---

## 1. Summary

| | Count | Names |
|---|---|---|
| Discrete build, project total disclosed | 6 | GGP, CMM, RXL, GMD, WGX, NST |
| Board-approved totals, spend-to-date undisclosed | 1 | EVN |
| Recurring annual guidance, no project total | 4 | RRL, VAU, PNR, CYL |
| Absent | 1 | RMS *(unblocks 21 Aug 2026)* |

**No constituent is de minimis at the proposed 1% threshold** (§5). The materiality
parameter, as proposed, excludes nobody in the current book.

**One name blocks the switch on disclosure rather than effort: EVN.** Its four
board-approved project totals are disclosed, but cumulative spend against them is
not, and the note itself records that "a material but unquantified share of the
A$1,210m is already spent". Remaining execution capital is therefore not derivable
without apportionment, which `estimation_policy` forbids.

**RMS is sourceable today on the RXL convention**, contrary to its own gaps note —
see §4.11. It becomes exact on 21 August 2026.

---

## 2. The inventory

`K` = candidate whole-project remaining execution capital. `H` = portion inside the
2-year Gate 2 horizon. Both are the *current sourced position*, not a recommendation.

| | Scope | K A$m | as-of | H A$m | Basis for the split |
|---|---|---:|---|---:|---|
| **GGP** | Havieron build to first gold | 1,065 | Jun-25 cost base, FID Jun-26 | ~865 | Issuer: build runs ~2.5y to first gold FY29; note already quantifies ~A$200m outside |
| | Telfer growth FY27 | 325 | FY27 guidance | 325 | Annual; FY28 not guided |
| **EVN** | Northparkes E22 block cave (80%) | 545 | Feb-26 approval | **unknown** | First production end-FY30 |
| | Cowal Open Pit Continuation | 430 | Apr-25 approval | ~123 | Issuer: "spread over the seven year period to FY31" |
| | Ernest Henry Bert | 160 | Feb-26 approval | unknown | No phasing disclosed |
| | Northparkes Coarse Particle Flotation | 75 | Feb-26 approval | unknown | No phasing disclosed |
| **CMM** | Mt Gibson pre-production | 474 | Jun-26 | 474 | 15 months pre-production mining → inside horizon |
| | KGP growth FY27 | 77.5 | FY27 guidance | 77.5 | Annual |
| **RMS** | Mt Magnet 5 Mtpa plant + Never Never + infrastructure | 381 | Oct-25 approval | unknown | Gross programme; A$163.3m group growth spent since, not apportionable |
| **RXL** | Youanmi DFS pre-production | 382.6 | Nov-25 DFS | 382.6 | First gold mid-CY2027 → inside horizon |
| **NST** | KCGM mill expansion tail | ~160 | FY27 | ~160 | In first-phase commissioning |
| | KCGM tailings dam facilities | 110 | FY27 | 110 | FY27 item |
| | KCGM thermal power + transmission | 115 | FY27 | 115 | FY27 item |
| **GMD** | Tower Hill mill — **issuer total** | 250–280 | 2026 | 250–280 | First ore FY28 → inside horizon |
| | *(of which EPC contract sum)* | *229* | May-26 | *229* | Executed contract; a floor, not the total |
| **VAU** | Sugar Zone growth (**Ontario**) | 96 | FY27 guidance | 96 | UG development commenced 1 Jul 2026 |
| | Leonora / Deflector / Mt Monger growth | 77 | FY27 guidance | 77 | Annual |
| **RRL** | Duketon (Rosemont Stage 3 UG + pre-strip) | 235–245 | FY27 guidance | same | Annual; no project total |
| | Tropicana Havana UG (30%) | 15–25 | FY27 guidance | same | Annual; no project total |
| **PNR** | New UG mines + Gladstone Stage 3 pre-strip | 101 | FY27 guidance | 101 | Annual; board-approved, not contracted |
| **CYL** | Capital contracted not provided for | 22 | 31-Dec-25 | 22 | Commitments note, "within one year" |

---

## 3. What the bridge shows about Gate 2

The §3.4 identity requires `committed_capex = Σ(within-horizon) + other non-project
burn`. The current cohort does not satisfy it, and the inconsistency is not uniform.

| | Horizon-aware today? | Evidence |
|---|---|---|
| OBM *(rejected)* | Yes | "summing only contracted or Board-approved lines **inside the two-year horizon**: FY27 A$240m + FY28 A$135m" |
| GMD | Yes | "first ore in FY28, so the whole contract sits inside the window" |
| RXL | Yes | First gold mid-CY2027 |
| CMM | Yes | 15 months pre-production mining |
| GGP | **No — quantified** | "the full A$1,065m is charged inside a two-year window although the build runs about two and a half years… leaving roughly A$200m outside it" |
| EVN | **No — unquantified** | "most of the remainder falls outside the two-year window" |

**EVN is the material case.** Removing only Cowal's out-of-horizon portion
(~A$307m, being 5/7 of A$430m spread to FY31):

```
ending_strict = 18 + 1,087.5 − 1,210 = −104.5   today → fails strict, passes on facilities
ending_strict = 18 + 1,087.5 −   903 = +202.5   horizon-correct → survives on cash alone
```

That flips EVN's `survives_on_cash_alone`, and §13.3 records
`gate2.count_undrawn_facilities` as "the parameter that currently decides EVN".
Northparkes E22 (A$545m, first production end-FY30) would move it further.

**Direction is safe** — today's treatment makes survival *harder* than §3 specifies,
so nothing unsound is live. But the gate is not measuring the two-year burn it
claims to, and the error varies by name.

**Nothing flips into the book.** BGL's A$95m is FY27-only, so a true two-year figure
is larger, not smaller; OBM is already horizon-correct and fails by A$211m.

---

## 4. Per-name notes

### 4.1 GGP — cleanest large case, two offsetting biases already recorded
Havieron A$1,065m is board-approved (FID June 2026), AUD-denominated, "to first gold"
on a June 2025 cost base, and explicitly excludes A$673m of post-first-gold expansion.
The FY27 Havieron guide of A$365–435m is a first-year subset and is not additive.
The existing note already states both biases: understated by one unguided year of
Telfer growth, overstated by ~A$200m of Havieron falling outside the horizon.
**Sourceable now. Cost base is 14 months old and should be checked for escalation.**

### 4.2 EVN — the blocking name
Four totals disclosed; cumulative spend disclosed at neither project nor group level
in a form that can be apportioned. Cowal has been drawing since FY25. Converting
gross-approved to remaining requires exactly the apportionment
`estimation_policy` forbids. A gross-as-remaining upper bound is available and runs
*against* the name in both uses, so it is a permitted bound — but it is a poor one
here, because "material but unquantified" spend has already occurred on a
seven-year programme.
**Needs: cumulative project spend to 30 Jun 2026, and phasing for E22, Bert and CPF.**

### 4.3 CMM — well-defined, with a disclosed accuracy band
Mt Gibson A$474m = A$345m plant and infrastructure + A$129m for 15 months of
pre-production mining, footed in the issuer's own table. A$105m of "Other LOM Project
Capital" correctly excluded as post-production. **No contingency is included** and the
estimate is "±25% accuracy with a 90% confidence level", so an against-the-name bound
on that leg is A$593m. **Sourceable now.**

### 4.4 RXL — roll-forward is available and should be applied
A$382.6m is DFS Table 30 at Nov-25, on the explicit assumption that nothing has been
spent. FY26 Appendix 5B discloses A$47.089m of PP&E plus A$15.788m of assets under
construction = **A$62.877m**, giving a rolled-forward A$319.7m at 30 Jun 2026.
Single-asset, so no apportionment is needed. Available project funding is
A$152.666m cash + A$320m cash-drawable debt = A$472.7m (the A$30m bank guarantee
facility is not cash). **Sourceable now, and the roll-forward is the sourced
improvement §4.4 of the proposal asks for.**

### 4.5 NST — marginal on materiality, one uncosted item
Three separately costed FY27 KCGM items. KCGM Mill Expansion is in first-phase
commissioning, so the A$160m is a tail. Hemi excluded (FID late FY27); Operational
Growth Capital of A$1,140–1,200m/yr excluded as deferrable. **Two open risks recorded
in the note: uncosted "renewable energy infrastructure" added in the June quarterly,
and ~A$10m of FY26 Operational Readiness underspend that may roll forward.** At
A$385m against a A$326.8m threshold, NST sits at 1.18% of EV and drops out at a 2%
materiality setting.

### 4.6 GMD — the EPC-is-not-the-total case, plus scheme risk
Rule 3 of §4.2 is directly evidenced here: the executed EPC contract sum is A$229m
but **the issuer's total anticipated capital cost is A$250–280m**, the difference
being a A$40m owner's cost allowance. A$24m of long-lead mill items is reported as
ordered with no statement of whether it sits inside the A$229m.
**Scheme risk:** GMD's own guidance describes the Tower Hill mill as "obviated post
completion of Vault merger". The Genesis/Vault scheme was signed 14 Jul 2026 and
targets November 2026. Under §4.3 capital is removed only on a primary source, so it
stands — but GMD's largest execution scope may be cancelled, and GMD and VAU may
cease to be two constituents.

### 4.7 VAU — ineligible-jurisdiction capital, an issue the proposal does not cover
A$96m of the A$173m FY27 growth capital is **Sugar Zone, in Ontario**, which is Gate 1
ineligible (`data/jurisdictions.json`, `CA-ON`). Underground development commenced
1 July 2026, so it is not pre-FID and cannot be excluded as deferrable.

The numerator excludes Sugar Zone's ounces entirely. If the denominator charges its
capital, the index pays for ounces it does not count. See §7.1.

### 4.8 RRL — recurring, but on named projects
FY27 group growth capital A$250–270m, composed of Duketon A$235–245m (Rosemont Stage 3
underground plus pre-strip of new open pits) and Tropicana A$15–25m. The issuer defines
growth capital as "open pit and underground pre-production mining costs, other
growth-related project, property, plant and equipment costs and acquisitions". FY26
guidance was A$240–255m against A$248.1m actual — a stable annual run-rate, not a
depleting project balance. **No project total is disclosed for Rosemont Stage 3.**
McPhillamys excluded (FID targeted H1 CY2028, and the spend is expensed not capitalised).

### 4.9 PNR — annual, board-approved, not contracted
A$101m of FY27 "major project and growth capital… new underground mines and
pre-stripping costs for Stage 3 at Gladstone open pit". Green Lantern re-commencement,
Gladstone Stage 3 and Daisy South are board-approved. Guided spend, not a contracted
sum. At 13.4% of EV this is the second-largest relative exposure in the book after RXL.

### 4.10 CYL — contracted commitments, and stale
A$21.969m of "capital expenditure contracted but not provided for… within one year",
Note 17 of the reviewed half-year accounts **at 31 December 2025** — eight months old.
PP2 mill expansion A$50–75m correctly excluded as pre-FID. The FY27 plant back-end
upgrade carries no disclosed figure. **Supersedes at the FY26 annual report.** At 1.58%
of EV, CYL also drops out at a 2% materiality setting.

### 4.11 RMS — sourceable today, contrary to its own gaps note
The gaps note rejects every route to a number. That reasoning is correct **for Gate 2**,
where it evaluated A$223m (the plant leg alone) and identified it as a *lower* bound
running *for* the name. But the full board-approved and unconditional programme —
A$223m plant + A$76m Never Never pre-production development + A$82m site
infrastructure = **A$381m**, struck October 2025 — taken as remaining on the
assumption that nothing has been spent is an **upper** bound running *against* the
name in both uses. That is precisely the convention already applied to RXL
("assuming NOTHING has been spent, which is the conservative end").

A$163.3m of group growth capital has been spent since across a mix of projects, so the
figure is conservative by an unquantified amount. Rebecca-Roe (A$340m) stays excluded:
FID is conditional on Roe environmental permitting, unresolved as at the 29 Jul 2026
quarterly.

**RMS reports its FY26 result pre-market Friday 21 August 2026**, which will carry the
Commitments note as at 30 June 2026 and make this exact.

### 4.12 WGX — thinnest record in the book
`committed_capex_aud_m = 145`, and the entire note reads *"Approved Higginsville mill
expansion, 1.6 to 2.6 Mtpa."* No scope decomposition, no completion date, no exclusions.
Its source is the **March 2026** quarterly, dated to the month only (`2026-04`), while
every other constituent runs off a June 2026 quarterly. `net_debt_aud_m` carries an
**empty note**. The record's own flag says "FY26 statement pending alongside August
full-year results."

This is a data-quality gap independent of the capital work, on a name that is the
book's largest weight at 12.16% and is elsewhere described as "the most complete data
record in the universe".

---

## 5. Materiality test

Candidate `K` against pre-capex EV, at the four thresholds the proposal asks to be
replayed. `Y` = included.

| | EV A$m | 1% of EV | K A$m | K/EV | 0.5% | 1% | 2% |
|---|---:|---:|---:|---:|:-:|:-:|:-:|
| RXL | 565 | 5.6 | 382.6 | 67.72% | Y | Y | Y |
| GGP | 7,104 | 71.0 | 1,065.0 | 14.99% | Y | Y | Y |
| PNR | 755 | 7.5 | 101.0 | 13.38% | Y | Y | Y |
| CMM | 7,030 | 70.3 | 474.0 | 6.74% | Y | Y | Y |
| RMS | 6,283 | 62.8 | 381.0 | 6.06% | Y | Y | Y |
| RRL | 4,549 | 45.5 | 260.0 | 5.71% | Y | Y | Y |
| EVN | 28,194 | 281.9 | 1,210.0 | 4.29% | Y | Y | Y |
| VAU | 5,500 | 55.0 | 173.0 | 3.15% | Y | Y | Y |
| GMD | 8,480 | 84.8 | 265.0 | 3.13% | Y | Y | Y |
| WGX | 4,676 | 46.8 | 145.0 | 3.10% | Y | Y | Y |
| CYL | 1,396 | 14.0 | 22.0 | 1.58% | Y | Y | · |
| NST | 32,677 | 326.8 | 385.0 | 1.18% | Y | Y | · |

**At the proposed 1%, the threshold excludes nobody.** Like the §6.4 statement-age
bar, it would be adopted while binding on nothing — which is the honest moment to
adopt it, but it should be stated rather than presented as a live filter. Only at 2%
does it begin to work, dropping NST and CYL.

---

## 6. Remaining Step 1 fetch work

| Name | Needed | Availability |
|---|---|---|
| RMS | FY26 Commitments note, capital contracted not provided for at 30 Jun 2026 | **21 Aug 2026**, confirmed in writing |
| WGX | June 2026 quarterly / FY26 full-year result: Higginsville scope, completion date, net debt | August 2026, per the record's own flag |
| EVN | Cumulative spend to 30 Jun 2026 per project; phasing for E22, Bert, CPF | Unknown — may not be disclosed |
| CYL | FY26 annual report Commitments note at 30 Jun 2026 | Pending |
| NST | FY27 guidance, 20 Aug 2026: KCGM remaining works, the uncosted renewable energy item | **20 Aug 2026** |
| GGP | Whether the June-2025 Havieron cost base has been escalated | Check FY26 result |
| All | Confirmation that no other material unfinished scope exists — a sourced zero, not silence | Per name |

Three of the seven resolve within days. EVN is the only one where the disclosure may
simply not exist.

---

## 7. Issues this inventory raises that the proposal does not cover

### 7.1 Execution capital in an ineligible jurisdiction
VAU's A$96m Sugar Zone spend builds ounces that Gate 1 excludes from the numerator.
Charging it to the denominator makes the index pay for ounces it refuses to count;
excluding it means the denominator understates what a buyer must actually fund. The
same question will arise for NST (Pogo) and EVN (Red Lake) if either discloses
project capital there.

§2.4 already answers the numerator half — "Pogo simply is not an ounce we own". The
denominator half is unanswered, and it is not obviously symmetric: the ounces are not
ours, but the cash outflow is.

### 7.2 A permitted upper bound is available more often than the notes assume
RMS was recorded as unsourceable because the *decomposition* could not be derived. But
gross-as-remaining is an upper bound running against the name, which the RXL record
already establishes as permitted. This may unblock other names and should be applied
consistently rather than case by case.

### 7.3 Scheme risk is not a capital state in the schema
GMD's Tower Hill is described by its own issuer as "obviated post completion of Vault
merger", and VAU and GMD are merging under a scheme targeting November 2026. §4.3
covers completion and cancellation but not *conditional obsolescence*, where a scope
is live today and contractually pointless on an event with a known target date.

### 7.4 Cost-base age is not a schema field
GGP's A$1,065m is on a June 2025 cost base; RMS's A$381m was struck October 2025;
CMM's A$474m carries "no contingency" at ±25%. §3.4 requires an as-of date, which
captures when the estimate was made but not the cost base it was struck on, nor a
disclosed accuracy band. Both bear directly on whether a figure is a bound or a point
estimate.
