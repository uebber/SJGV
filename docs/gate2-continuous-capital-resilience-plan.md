# Gate 2 producer-health simplification plan

**Created:** 22 August 2026
**Status:** replacement proposal; no production behaviour changed
**Baseline:** SJGV v1.7 and `snapshots/2026-08-21-v1.7-health`

This replaces the earlier continuous capital-resilience plan. The source audit
showed that the proposed cash-flow path cannot be built consistently from ASX
producer disclosures. The evidence is recorded in
[`gate2-capital-resilience-source-register-2026-08-22.md`](gate2-capital-resilience-source-register-2026-08-22.md),
and the repeatable retrieval process is in
[`primary-document-fetching-strategy.md`](primary-document-fetching-strategy.md).

## 1. Decision

Keep Gate 2 as a **binary admission gate with GREEN / AMBER / RED reporting**.
Do not introduce a continuous multiplier or a Gate 2 weight tilt.

The available disclosures can support a conservative screen for demonstrated
balance-sheet distress. They cannot support a reliable ranking of one
producer's capital resilience against another's. A continuous score would
either reward missing commitments, punish companies that disclose more, or
depend on analyst-built timing and overlap assumptions.

The simplified producer test asks:

> After a 40% fall in current AUD gold for two years, do sourced operating and
> balance-sheet facts demonstrate a rescue burden too large to be manageable?

Only demonstrated RED excludes. Incomplete commitment evidence is AMBER, not a
fabricated zero and not an automatic exclusion.

Developer D1, D2 and D3 remain unchanged.

## 2. What the fetched data can support

| Input | Cohort result | Use in Gate 2 |
|---|---|---|
| Production and AISC | Available for established producers, subject to the basis corrections in the source register; BC8 has no AISC | Core input; missing either is `UNTESTED` |
| Latest balance-sheet net debt | Available or arithmetically derivable from sourced cash and interest-bearing liabilities | Core opening-liquidity input |
| Contracted or non-deferrable capital | Partial and heterogeneous; no issuer supplies the proposed complete two-year schedule | Use only as a directional interval |
| Liability maturity schedules | Missing from half-years, stale for much of the cohort, and defective in some annual reports | Do not use |
| Facility amount and term | Sometimes available | Report only |
| Facility covenants and draw conditions | Not quantified for the cohort except EVN | Do not use; give facilities no Gate 2 credit |
| Intra-horizon payment timing | Not consistently disclosed | Do not model |

This is the useful intersection: operating output, operating cost, net debt and
whatever unavoidable obligations can actually be proved. It is enough for a
coarse health gate, not a quarterly liquidity simulation.

## 3. Simple producer rule

Retain the existing scenario parameters:

- a two-year horizon;
- a 40% fall from current AUD spot;
- 5% annual AISC inflation;
- no hedge benefit; and
- 30% tax on positive stressed cash generation, with no invented tax benefit
  on losses.

For each producer, calculate:

```text
stress price = current AUD spot × 60%

two-year stress cash generation
    = sum of annual production × (stress price − inflated AISC)
      less tax on positive cash generation

stress resources(C)
    = − net debt
      + two-year stress cash generation
      − C

rescue capital(C) = max(0, − stress resources(C))
rescue burden(C)  = rescue capital(C) ÷ current market capitalisation
recovery years(C) = rescue capital(C) ÷ normal-price annual cash generation
```

`net_debt_aud_m` remains the simple balance-sheet bridge. It must include
borrowings, leases and asset finance, less unrestricted cash and separately
identified cash-like bullion or liquid investments. In-circuit metal is
inventory, not cash. An issuer's “debt free” label does not establish zero when
the balance sheet carries interest-bearing liabilities. All included debt is
therefore charged without relying on its contractual maturity date. Do not add
a separate cash field, debt schedule, common-date roll-forward or
minimum-liquidity buffer.

Undrawn facilities contribute **zero**. They may be reported as contingent
liquidity, but their terms, covenants and drawability do not enter the gate.
This removes the only proposed input that cannot be verified consistently. On
the frozen v1.7 replay, every admitted producer remained non-RED without
facility credit; only OBM required manageable rescue capital. The simplification
therefore removes fragile machinery without changing the observed admission
result.

Use the current rescue limits:

```text
RED if rescue burden > 30%
    or recovery years > 2
```

Normal-price cash generation uses current AUD spot. A trailing repair deck,
equity-value haircut and implied ownership calculation are not part of the
gate.

## 4. Directional commitment evidence

Do not require a two-year commitment schedule. Record a simple interval:

```text
L = sourced minimum of quantified, non-deferrable obligations inside the horizon
U = finite conservative upper bound, when the source supports one
```

Examples:

- an executed growth EPC amount due inside the horizon can enter `L` when it is
  demonstrably outside AISC;
- an unseparated capital-commitments note may enter `U`, because it may overlap
  sustaining capital already inside AISC;
- a one-to-five-year bucket may enter `U` in full, but cannot be narrowed to a
  two-year point;
- one year of guidance is not annualised into year two;
- board-approved or discretionary growth is omitted unless cancellation is no
  longer a realistic response to the stress; and
- silence never establishes either zero or a complete upper bound.

The state follows from tests at the interval edges:

| State | Rule | Treatment |
|---|---|---|
| **RED** | The producer is RED even at `L` | Exclude; distress is demonstrated without assuming the missing tail |
| **GREEN** | A finite, scope-complete `U` exists and the producer needs no rescue at `U` | Eligible |
| **AMBER** | Every other testable, non-RED case: manageable rescue, incomplete commitments, conservative overlap, or uncertain operating basis | Eligible and reported |
| **UNTESTED** | Production, AISC, net debt or market capitalisation is unavailable | Exclude |

If a conservative upper bound produces RED but `L` does not, the result is
AMBER rather than RED: an upper bound can prove survival, but it cannot prove
failure. If `U` is absent, test `L`, report the missing tail and return AMBER
unless `L` already demonstrates RED.

For issuer-published production or AISC ranges, run every endpoint combination
and take the worst result. Do not use the midpoint to decide admission; lower
production is not always adverse when the stressed margin is negative.
Production and AISC must refer to compatible operating and ounce bases. If an
issuer does not state whether AISC is per ounce produced or sold, evaluate both
sourced same-period volumes, take the worse result and force AMBER; do not
invent a denominator.

## 5. Data work before implementation

The source register identifies corrections that should be made independently
of this methodology choice:

1. correct NST's facility dates;
2. split OBM's A$233m executed EPC from the A$142m board-approved balance;
3. remove GGP's covenant carried from the cancelled facility;
4. remove PNR's in-circuit gold from cash/net-debt treatment unless its liquidity
   and unrestricted status are proved;
5. replace VAU's superseded FY25 commitment figures with FY26 figures;
6. reconcile NST/KCGM so the same scope is not added twice; and
7. check WGX, CYL and OBM against their balance-sheet leases and asset finance
   rather than accepting “debt free” presentation labels.

Also encode the compatible production/AISC pairs documented in the source
register. AISC labels such as “produced”, “sold”, exclusions and by-product
credits must remain attached to their matching volumes.

Re-sweep the complete ASX announcement index from 26 August to 5 September for
CMM, GGP, WGX, BGL, OBM and CYL, then at the end of September for PNR and BC8.
Use the channel order and exact-PDF checks in the fetching strategy. New reports
may improve an interval or resolve a data correction, but the simple rule does
not depend on every issuer publishing a maturity or commitment schedule.

Do not copy findings into `data/companies.json` without a document key and
field-level citation. Run `tools/provenance.py` and `tools/gaps.py` after each
coherent data update.

## 6. Narrow implementation sequence

1. **Refresh and correct data.** Apply the source-register corrections and the
   scheduled FY26 re-sweep. Do not freeze a live build or snapshot yet.
2. **Simplify the calculation.** Remove facilities from producer stress
   resources, retain the existing operating stress, and evaluate commitment
   intervals using the directional rules above. No new schedule schema is
   required.
3. **Test the rule.** Cover adverse operating ranges, interval direction,
   missing core inputs, no-facility treatment and monotonicity. A larger `L`,
   higher AISC or more net debt must never improve a result; production ranges
   are checked at every endpoint because production is not globally monotone.
4. **Replay once.** Use the frozen v1.7 market bundle and report only admission
   changes, GREEN/AMBER/RED changes and the source field responsible for each.
5. **Activate deliberately.** If the replay is accepted, amend
   `index-methodology.md`, `data/README.md`, `README.md`, configuration and code
   together. Run the repository checks. Create no snapshot unless this is an
   approved rebalance.

## 7. Acceptance criteria

The simplified Gate 2 is ready only when:

- every admitted producer has sourced production, AISC, net debt and market
  capitalisation;
- every amount in `L` or `U` cites a primary document and states its scope,
  date, units and evidence direction;
- missing commitment coverage forces AMBER and never becomes zero or GREEN;
- facilities cannot alter eligibility;
- RED can be reproduced from sourced minimum obligations and adverse published
  operating ranges;
- no maturity schedule, covenant model, payment-timing assumption, continuous
  multiplier or confidence haircut can affect a weight;
- developer results are unchanged except for ordinary renormalisation after a
  genuine producer exclusion; and
- compile, provenance, gaps, configuration audit and the frozen replay pass.

## 8. Explicitly abandoned from the prior plan

Do not build:

- a checkpoint-by-checkpoint liquidity path;
- contractual principal-and-interest schedules;
- a balance-sheet roll-forward to the market-data date;
- a three-month minimum cash buffer;
- covenant-survival modelling;
- a trailing-real-gold repair price;
- facility/equity financing splits or dilution scenarios;
- a continuous capital-resilience multiplier;
- cap-release thresholds or multiplier attribution replays; or
- a new multi-schedule company-data schema.

Those features create precision the disclosure set cannot support. Gate 2 is a
ruin screen. The ounce ledger divided by standard EV for established producers,
or by EV plus gross remaining execution capital for near-producers and
developers, remains the weighting model under methodology amendment 10.
