# Capital resilience in SJGV v2.2

Gate 2 protects the future gold claim from a path-dependent failure: severe
down-cycle financing that permanently dilutes or disables the later upside. It
is a survival boundary, not a quality score and not a forecast.

## Design

Producers face a two-year unhedged stress at 40% below current AUD gold, with
AISC inflated 5% annually. Sourced non-deferrable commitments are deducted.
Undrawn credit counts only when its sourced term extends beyond the stress
window. A company is RED only when required rescue capital exceeds 30% of
market capitalisation or more than two years of normal-price cash generation.

This boundary deliberately permits an ordinary recapitalisation. Requiring
zero equity issuance would select for excess balance-sheet conservatism and
exclude otherwise durable claims; allowing an unbounded raise would leave
existing holders without the upside the index sought to buy.

Incomplete commitment coverage is AMBER, not GREEN. The engine uses known
obligations and reports the incomplete adverse edge. It does not extrapolate an
issuer's one-year plan into a second undisclosed year or assume discretionary
growth continues through crisis. Missing decisive operating or balance-sheet
inputs remain UNTESTED and exclude.

## Why producers and developers differ

An operating or near-producing company on the producer path is tested through
production, AISC and liquidity. A developer has no operating cash flow, so its
test is instead study maturity, approvals and bounded residual funding gap.

Gross remaining construction cost enters a developer or near-producer's funded
EV even when financing is available. This avoids calling a fully financed plant
economically free. Available funding is subtracted only to calculate potential
dilution in the gate.

For established producers, public reporting normally does not provide a
complete company-wide remaining-cost schedule. Making that schedule mandatory
would grade disclosure format and systematically treat an absent cost as either
zero or exclusion. Standard EV is therefore the comparable denominator, while
sourced unavoidable commitments still enter the stress test.

## Release evidence

The 25 August v2.2 snapshot records a stress price of about A$3,866/oz. All admitted
producers were GREEN or AMBER; AMBER chiefly recorded incomplete commitment
coverage rather than a required rescue. Six companies were rejected after the
full construction: four for execution delivery and two developers for approval
or funding-gap failures. The release retained one developer at 5%; its A$319.7m
gross remaining construction cost was included in funded EV even though sourced
funding reduced its residual gap to zero.

These observations show that the gate ran and that its developer capital logic
was weight-bearing. They do not prove the 40%, two-year or 30% thresholds are
optimal. Those are policy boundaries intended to represent a severe but
survivable cycle.

## Known limits

- AISC is an issuer-defined average, not a mine-by-mine marginal cost curve.
- Taxes and cost inflation are simplified uniformly.
- Incomplete commitment coverage can leave an admitted AMBER company with
  unquantified additional obligations.
- A facility can be unavailable in practice even when its contractual term
  extends past the window.
- A common operational or sovereign shock can affect several companies at once.

These limits are disclosed rather than concealed in an elaborate model. The
binding arithmetic and failure states are in
[`../index-methodology.md`](../index-methodology.md#3-gate-2--capital-resilience).
