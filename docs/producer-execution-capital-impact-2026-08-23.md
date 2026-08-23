# Producer execution-capital methodology impact — 23 August 2026

**Scope:** methodology-only replay on the frozen market inputs in
`tests/fixtures/2026-08-21-capital-baseline.json`. No sourced company value was
changed and no snapshot was created.

## Eligibility

| Ticker | Before | After | Reason |
|---|---|---|---|
| WGX | Excluded | Eligible, AMBER | Unresolved producer execution capital is reporting-only; Gate 2 uses the sourced unavoidable commitment lower edge and reports incomplete coverage. |
| BGL | Excluded | Eligible, AMBER | Missing complete producer execution capital is no longer a denominator requirement; incomplete commitment coverage remains AMBER. |
| BC8 | Excluded | Excluded, UNTESTED | AISC remains unsourced. BC8 is also a near-producer, so denominator-safe gross execution capital remains deliberately required after the AISC gap is resolved. |
| AAR | Excluded | Excluded | Developer D2 fails and the sourced residual funding gap exceeds the D3 limit. |
| AUC | Excluded | Excluded | Developer D2 fails and the directional funding evidence leaves D3 unresolved. |

All other previously eligible names remain eligible. Producer execution-capital
records remain in the data and knowledge layers but do not decide eligibility or
weight. Near-producer and developer requirements are unchanged.

## Weight impact

| Ticker | Before | After | Change |
|---|---:|---:|---:|
| BGL | 0.00% | 5.33% | +5.33pp |
| CMM | 7.50% | 6.05% | -1.44pp |
| CYL | 10.00% | 10.00% | 0.00pp |
| EVN | 4.48% | 3.48% | -1.00pp |
| GGP | 8.39% | 7.13% | -1.26pp |
| GMD | 9.75% | 7.52% | -2.23pp |
| NST | 11.82% | 8.97% | -2.85pp |
| OBM | 4.41% | 3.84% | -0.57pp |
| PNR | 10.00% | 10.00% | 0.00pp |
| RMS | 9.25% | 7.30% | -1.94pp |
| RRL | 9.81% | 7.35% | -2.47pp |
| RXL | 5.00% | 5.00% | 0.00pp |
| VAU | 9.61% | 7.30% | -2.30pp |
| WGX | 0.00% | 10.73% | +10.73pp |

One-way turnover is **16.06 percentage points**. The index price per claimed
ounce falls from approximately **A$826/oz to A$780/oz** (about 5.6%), reflecting
both the admission of WGX and BGL and the removal of producer execution capital
from established-producer denominators. RXL remains at its 5% developer cap and
continues to include A$319.723m of gross remaining execution capital despite a
zero derived residual funding gap.

## Remaining exclusions: source gap versus policy requirement

- **BC8:** source gap — AISC is not published, so producer-path Gate 2 is
  `UNTESTED`; deliberate requirement — its `near_producer` sleeve still needs
  denominator-safe gross execution capital.
- **AUC:** source gap — available funding/net debt evidence is incomplete;
  deliberate requirements — developer approvals/land access and D3 bounded
  dilution must pass.
- **AAR:** deliberate developer protections — land access is not secured and
  its sourced residual funding gap is above the 30% market-cap limit.
