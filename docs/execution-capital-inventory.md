# Execution capital — Step 1 sourcing inventory

**Status:** inventory plus 21 August 2026 primary-source refresh. This document
was the pre-implementation evidence record; issue 3 subsequently changed the
schema, engine and parameters without replacing the frozen generated baseline.
**Purpose:** establish, per constituent, what the disclosure regime actually supplies
for `remaining_execution_capex_aud_m` and its Gate 2 within-horizon portion, before
any definitional or schema decision is taken.
**As-of:** capital evidence refreshed 2026-08-21; EV remains from the frozen
2026-08-18 replay anchor.

This is Step 1 of the capital migration proposed in `asset-evidence-capital-proposal.md`.
Two committee decisions were taken before it began:

1. **Gate 2 is in scope.** The §3.4 bridge is to be built and `committed_capex_aud_m`
   re-derived on a strict within-horizon basis in the same pass, rather than frozen.
2. **The annual-guidance names are reported, not pre-judged.** No rule separating
   discrete builds from recurring growth capital is adopted here; this document
   supplies the evidence for that decision.

The original inventory used only figures already in `data/companies.json`.
Section 6 now records the 21 August primary-source refresh and its remaining
publication gaps.

---

## 1. Summary

| | Count | Names |
|---|---|---|
| Discrete build, project total or admissible upper bound disclosed | 6 | GGP, CMM, RXL, GMD, RMS, NST |
| Board-approved totals, spend-to-date undisclosed | 1 | EVN |
| Recurring annual guidance, no project total | 4 | RRL, VAU, PNR, CYL |
| Unresolved | 1 | WGX *(replacement scopes are larger or uncosted)* |

**No constituent with admissible capital evidence is de minimis at the proposed
1% threshold** (§5). WGX is unresolved before that test is reached.

**One name blocks the switch on disclosure rather than effort: WGX.** Its former
A$145m scope is under review in favour of larger or additional uncosted scopes.
EVN's four board-approved totals remain a poor but admissible `UPPER_BOUND`:
treating the gross A$1,210m as remaining assumes no spend-down and can only run
against the name.

**RMS remains sourceable on the RXL convention** as a A$381m `UPPER_BOUND` —
see §4.11. Its 21 August commitments note makes the one-year Gate 2 amount exact,
not the remaining execution-capital balance.

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

~~**Direction is safe** — today's treatment makes survival *harder* than §3 specifies,
so nothing unsound is live.~~ **WITHDRAWN 19 Aug 2026.** The gate is not measuring the
two-year burn it claims to, and the error varies by name — that part stands. The
conclusion drawn from it does not. The table above lists only the names whose figures
run *past* the window, and generalised from them. The names that run *short* of it were
never tabled: **PNR, RRL, VAU, CYL, NST and CMM's KGP leg are single guided years
charged against a two-year window, and WGX's record establishes no period at all.** A
one-year figure against a two-year window understates the burn, which is the direction
a survival gate must never err in, and it is live on seven constituents rather than
zero.

Methodology §3.2 now records `horizon_years` per figure and prints the shortfall. It is
not filled: annualising a guided year into an unguided one is `estimation_policy`
forbidden, and a cohort rate on an unguided period is the same invention in a peer
group's clothes — the cohort's upper rate is CMM building a second mine, which on WGX's
387 koz would charge A$3.4bn and eject the book's largest position on a number nobody
published.

**PNR is out of the book**, but not on this limb. Its FY27 AISC and production are
recorded at the midpoints of the issuer's published ranges, and the Gate 2 verdict flips
between A$2,800 and A$3,400/oz — UNRESOLVED under §3.2, 10.00pp of turnover. See
`data/SOURCES.md`.

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

### 4.11 RMS — exact Gate 2 commitment, bounded execution capital
The former gaps note rejected every route to a number before the FY26 annual
report. Its treatment of A$223m (the plant leg alone) was correct: that amount is
a *lower* bound running *for* the name. But the full board-approved and
unconditional programme —
A$223m plant + A$76m Never Never pre-production development + A$82m site
infrastructure = **A$381m**, struck October 2025 — taken as remaining on the
assumption that nothing has been spent is an **upper** bound running *against* the
name in both uses. That is precisely the convention already applied to RXL
("assuming NOTHING has been spent, which is the conservative end").

A$163.3m of group growth capital has been spent since across a mix of projects, so the
figure is conservative by an unquantified amount. Rebecca-Roe (A$340m) stays excluded:
FID is conditional on Roe environmental permitting, unresolved as at the 29 Jul 2026
quarterly.

**REFRESHED 21 AUGUST 2026.** Note 27 of the audited FY26 report discloses
A$79.218m of capital expenditure commitments within one year at 30 June 2026.
That is entered as a `POINT` for its stated one-year Gate 2 coverage. It does not
identify which Mt Magnet scopes the contracts serve and does not reconcile the
A$163.3m group growth spend to the A$381m programme. The execution-capital
candidate therefore remains A$381m `UPPER_BOUND`; it did not become exact.

### 4.12 WGX — thinnest record in the book
`committed_capex_aud_m` is now absent and explicitly `UNRESOLVED`. The former
A$145m value covered the approved 2.6 Mtpa Higginsville stage, which the 18 August
Fletcher filing places under review in favour of a larger, uncosted 4 Mtpa case.
The same filing calls additional Murchison milling capacity committed or planned
without giving an amount. Retaining A$145m would therefore retain a favourable
`LOWER_BOUND`.

The ASX feed was rechecked on 21 August. Neither the FY26 financial result nor
the Strategic Outlook had been filed. The filing says a preliminary assessment
will arrive in the Strategic Outlook expected in early September and that a
definitive timeline is premature. The amount and coverage period remain absent;
FY26 non-sustaining spend is not substituted for a remaining balance.

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
| WGX | 4,676 | 46.8 | — | — | · | · | · |
| CYL | 1,396 | 14.0 | 22.0 | 1.58% | Y | Y | · |
| NST | 32,677 | 326.8 | 385.0 | 1.18% | Y | Y | · |

**At the proposed 1%, the threshold excludes none of the names with admissible
capital evidence.** WGX is unresolved before materiality is tested. Like the §6.4
statement-age bar, the threshold would be adopted while binding on nothing. Only
at 2% does it begin to work, dropping NST and CYL.

---

## 6. Remaining Step 1 fetch work

| Name | Needed | Availability |
|---|---|---|
| RMS | FY26 Commitments note, capital expenditure commitments at 30 Jun 2026 | **Closed 21 Aug:** A$79.218m within one year; execution roll-forward still unavailable |
| WGX | FY26 full-year result / Strategic Outlook: Higginsville and Murchison scope, completion date, funding and coverage | **Not filed at 21 Aug:** Strategic Outlook expected early September |
| EVN | Cumulative spend to 30 Jun 2026 per project; phasing for E22, Bert, CPF | Unknown — may not be disclosed |
| CYL | FY26 annual report Commitments note at 30 Jun 2026 | Pending |
| NST | FY27 guidance and audited facility terms | **Closed 20 Aug:** facility A$1.75bn undrawn; capital guidance refreshed separately |
| GGP | Facility execution/availability; whether the June-2025 Havieron cost base has been escalated | **Facility closed:** A$475m undrawn through at least 1 Apr 2031; audited cost refresh still pending |
| All | Confirmation that no other material unfinished scope exists — a sourced zero, not silence | Per name |

RMS, NST and GGP are closed for the issue-2 questions. WGX remains absent because
the named primary documents are not yet published; no substitute is inferred.

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
