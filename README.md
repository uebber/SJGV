# SJGV — Stable Jurisdiction Gold Value Index

**A gold miner index that separates reserve claims from mine-development
optionality, then counts both instead of market capitalisation.**

Buy a gold miner and what you are actually buying is a pile of gold that hasn't
been dug up yet. SJGV weights each company by **how much of that pile you get per
euro**, and buys nothing whose pile sits somewhere a government has a motive to
take.

Version 2 is implemented. Its first live snapshot is pending the asset-level
optionality data migration described below. The stored 18 August construction is
the final v1 snapshot and remains in `snapshots/` as immutable history; its A$/oz
figures must not be presented as v2 results.

---

## Why ounces

A mine has option-like exposure because a higher gold price can lower economic
cut-offs and make more mineralised material economic. The analogy has limits:
AISC is not the strike price of every ounce, and price alone does not upgrade
geological confidence. SJGV therefore treats reserves and non-reserve resources
as different ledgers.

Market-cap weighting cannot do that, and not by accident. It sizes each position
by what the market currently pays for that company's ounces, so the more
expensive an ounce becomes, the more of it you hold. Every re-rating buys you
less gold per euro and the index calls that a bigger position.

SJGV inverts it. One formula, no scores:

```
              CoreClaim_i + QualifiedOptionality_i
  w_i    ∝    ─────────────────────────────────────
                            FundedEV_i
```

Nothing else. No composite, no ranking, no quality tilt, no factor blend. A term
is allowed into the weight only if it changes **how many ounces are claimed, or
what was paid for them.** Everything else in this repository is a report.

---

## What goes into the count

**Core claim.** Attributable, Gate-1-eligible Proven & Probable ounces, less
ounces already sold forward. Mixed-jurisdiction companies must source a
P&P-specific eligibility share; the old blended all-resource share is not used.

**Optionality inventory.** M&I non-reserve and Inferred ounces enter only asset
by asset. Every asset needs a current primary resource statement, category-level
ownership and jurisdiction, credible metallurgy and recovery, a processing
route or development basis, land/permitting status, a disclosed capital path,
and complete treatment of material streams and royalties. After those gates,
M&I receives 0.5 and Inferred 0.2 for geological confidence.

Price can support a larger economic shell or reserve conversion where geological
confidence and other Modifying Factors are adequate. It cannot move Inferred to
M&I without more work. The optionality mix is therefore an exposure diagnostic,
not proof of portfolio convexity.

**Hedged ounces are subtracted.** Gold a company has already sold forward is gold
you do not own the upside to. It comes off the reserve tranche first, because
that is where a forward gets delivered from.

**Future capital is added to the price.** A developer's residual core funding gap
still enters funded EV. In v2, every counted optionality asset also brings its
incremental future capital into the denominator, for producers and developers
alike. Missing capital excludes the asset; it never defaults to zero.

**Everything is sourced to a document.** No estimated inputs, ever. A value with
no source is a gap to close or a company to reject — never a number someone made
up. Absence must never read as zero where zero would flatter.

---

## Three gates, and the disasters they are for

Weighting only happens after the binary company gates; optionality then faces its
own asset gates. None is a score and none can be offset by cheapness.

> **Gate 1 defends against 1933. Gate 2 defends against 2013.**

**Gate 1 — where the ounces are.** The scenario this index is built for is gold
repricing violently upward. In that scenario the danger is not a permitting delay,
it is a government that wants the metal. So the test is applied to the country
where the rock physically sits, and it asks whether that state has the motive and
the machinery:

- **Own, freely floating currency** — not a reserve currency, not a currency-union
  member. A state whose currency can devalue has no need to repress gold; the FX
  does the adjustment for it. A reserve issuer has both a unique motive and unique
  tools.
- **Solvent sovereign** — net debt ≤ 60% of GDP and interest ≤ 10% of revenue.
- **No operative gold-control regime, and bounded dormant powers** — no
  confiscation, compulsory delivery, administered monopsony or gold-export ban
  is currently in force. A dormant power can pass only if activation requires a
  new public act and compulsory acquisition carries a published compensation or
  judicial-review route.

Nothing here promises a state *cannot* take your gold. The claim is narrower and
testable: no coercive gold regime is operating today, and latent machinery cannot
be activated silently or operate without a compensation path. Historical use and
ease of activation remain disclosed residual risks rather than permanent vetoes.
Australia passes this narrower test: Part IV of the Banking Act is inactive,
activation requires a public Proclamation, and s44 provides a published-price or
court-compensation route. That is a bounded risk, not an assertion of immunity.

**Gate 2 — who is still standing.** *Does this company reach the other side of a
40% real gold drawdown without issuing equity?* Cash, undrawn facilities, free
cash flow at the stress price, committed capex, debt maturities. Run **unhedged**,
so nobody passes survival on the strength of the forward sales that reduce their
claim. The drawdown is applied to a three-year real average rather than to spot,
because anchoring to spot makes a survival gate weakest exactly when spot is most
extended.

Cost lives here and only here. AISC decides whether a company survives; it does
not decide how many ounces it owns, so it never reaches a weight.

**Gate 3 — can it be traded.** Median regular-hours quoted spread must be within
1% for producers or 4% for developers. Capacity is reported separately and does
not alter weights.

**Four caps follow**, and all four answer one question: *how much of the claim can
a single uncorrelated operational failure destroy permanently?* A fault, a flood,
a tenement dispute or a fraud does not mark a claim down — it removes it.

| Constraint | Setting |
|---|---|
| Single-name maximum | 15% |
| Single-asset company maximum | 10% |
| Developer sleeve | ≤ 15%, per name ≤ 5% |
| Ineligible-jurisdiction NAV per constituent | 25% |

---

## The investment case

Three ways it pays, and one thing it protects.

**You buy the claim rather than the popularity.** The final v1 snapshot showed
the same twelve names could be arranged at a lower harmonic funded-EV-per-claim
statistic than cap weighting. Version 2 makes the comparison stricter: it will
not publish a new advantage until the optionality assets and their capital paths
have passed the new gates.

**You can own optionality without calling every resource ounce equivalent.**
M&I and Inferred inventory can matter in a higher-price environment, but only
where the asset has a credible economic path. Version 2 gives that qualified
inventory a separate ledger and charges the denominator for the capital needed
to unlock it. A reserves-only company remains investable; an unsourced resource
does not become a free option.

**You hold what an acquirer buys.** Acquirers in this sector transact on ounces
in the ground, and this book is, by construction, the cheapest ounces in the only
jurisdiction that passes Gate 1. That is not hypothetical here: **Vault is 8.4%
of the book and under a signed Genesis scheme** targeting November 2026,
Evolution is itself acquiring Carnaby, and five schemes have moved across the
sector since May 2026 — one of them collapsing mid-flight when a rival outbid it,
inside a ten-week window.

**And Gate 1 protects you from being right.** The scenario this index exists for
is the one in which gold becomes politically interesting. Owning the correct
asset into that scenario is worth nothing if it sits somewhere with a motive to
take it.

### Where the convexity is — and where it is not

A higher gold price can lower the economic cut-off, expand the supportable
resource shell and help convert suitable M&I material to reserves once all other
Modifying Factors are adequate. It does not upgrade Inferred material without
additional drilling and technical work. The qualified optionality ledger owns
exposure to that economic response without pretending the category label alone
makes an ounce developable.

Three things must be said plainly about how far that can be evidenced.

**The NAV model shows zero gamma, and that is a statement about the model.**
Modelled capture at ±40% is 1.61 up and 1.61 down — a ratio of exactly 1.00. On a
fixed mine plan at a single AISC, NAV is `A × (deck − AISC) − debt`, which is
linear in the deck, so every finite difference returns the same delta. The 1.00
is arithmetic, not evidence of an absence.

**The mechanism cannot be measured from public disclosure.** A survey of ≈11 MB
of primary text found that **zero of twelve constituents publish a resource at two
or more cut-off grades.** Issuers run the curve and table only its argmax. So the
ledger is static in the gold price by necessity, not by choice, and no cut-off
elasticity is assumed — assuming one would manufacture the exact number the
product is judged on.

**Realised up-versus-down capture is not a finding either.** β_up 1.70 against
β_dn 1.15, a ratio of 1.48 against 1.28 for the same names cap-weighted — on 23
down weeks, with a 95% interval of [0.12, 4.44]. That interval spans "no
convexity at all" and "three times gold". It is reported because it was measured,
not because it demonstrates anything.

**So the ledger mix is an exposure diagnostic, not proof of convexity.** Version
2 reports core reserves, qualified M&I and qualified Inferred separately, plus
the share of disclosed optionality that failed or has not yet been assessed.

### Why not simply take leverage instead

Because measured in ounces, linear leverage *must* lose over a round trip. Start
at 1.00 oz; gold doubles and a 2× exposure triples the index, taking you to 1.50
oz; gold halves back to where it began and symmetric capture destroys the
position entirely. At a realistic 1.3× downside capture you end at 1.05 oz — a 5%
gain from a full round trip in which gold went nowhere.

Ounce accumulation across a cycle is therefore a function of **convexity, not
leverage**, and this is the third and least-discussed reason gold equities failed
to deliver leverage between 2011 and 2020. It is why β_gold is reported and
checked against a 1.4–1.8 band rather than maximised, why a 2.0+ target was
considered and rejected, and why Gate 2 exists at all.

### When it is worth holding, and when it is not

| Scenario | How this index behaves |
|---|---|
| **Gold reprices violently upward** | The design case. Economic cut-offs can fall and qualified optionality can become more valuable; reserve conversion still requires geological confidence and the other Modifying Factors. Gate 1 is what keeps the win. |
| **The sector consolidates** | You are holding the list an acquirer screens for. Evidenced above, and running now. |
| **Gold flat, miners de-rate** | The plain value case. Nothing needs to happen to the gold price; the position pays if A$ per ounce mean-reverts toward what the market pays elsewhere. |
| **Gold drawdown** | You lose money. Nothing here is a hedge and the book is geared. What Gate 2 buys is that the loss is not made *permanent*: every constituent reaches the far side of a 40% real drawdown without issuing equity, so the ounces behind each share are the ones you started with. Dilution at the bottom is how gold equity holders were destroyed in the last cycle. |
| **Sustained bull led by expensive large caps** | The worst case, and structural rather than fixable. See below. |

One asymmetry worth knowing: the ledger counts an ounce at A$1,717 AISC and an
ounce at A$3,100 identically. High-cost ounces have the most operating leverage
to a rising price and are the first to be worth nothing in a falling one, so the
book is more geared in both directions than the ounce count alone suggests.

---

## Final v1 book — historical, not a v2 result

**12 constituents · A$679 per v1 claimed ounce · β_gold 1.72 · effective N 11.3**
Built 18 August 2026 against live IBKR prices, spot A$6,218/oz. These weights
used company-level M&I and Inferred totals before the v2 asset gates and are
retained only as the last v1 snapshot.

| | Weight | A$/claimed oz | Claimed Moz | Sleeve |
|---|---|---|---|---|
| Westgold Resources (WGX) | 12.16% | 602 | 7.77 | producer |
| Catalyst Metals (CYL) | 10.00% | 530 | 2.63 | producer |
| Pantoro Gold (PNR) | 10.00% | 372 | 2.03 | producer |
| Northern Star Resources (NST) | 9.59% | 763 | 42.84 | producer |
| Regis Resources (RRL) | 8.93% | 819 | 5.55 | producer |
| Genesis Minerals (GMD) | 8.64% | 846 | 10.02 | producer |
| Vault Minerals (VAU) | 8.44% | 867 | 6.34 | producer |
| Ramelius Resources (RMS) | 8.31% | 880 | 7.14 | producer |
| Greatland Resources (GGP) | 8.18% | 895 | 7.94 | producer |
| Capricorn Metals (CMM) | 6.74% | 1,085 | 6.48 | producer |
| Rox Resources (RXL) | 5.00% | 458 | 1.23 | developer |
| Evolution Mining (EVN) | 4.01% | 1,827 | 15.44 | producer |

Caps bind on three: PNR 15.8% → 10%, CYL 11.1% → 10%, RXL 12.8% → 5%.

---

## What you are giving up

Stated plainly, because a methodology that only lists its strengths is selling
something.

**It will lag when expensive quality re-rates.** The final v1 snapshot held
Evolution at 4%, against roughly 25% in a cap-weighted book. When a name like
that runs, this index participates less. That is not a flaw to be tuned away —
it is the objective working.

**It sells into strength.** Because market cap sits in the denominator, a company
whose share price rises on unchanged ounces gets a *smaller* weight. The index is
structurally contrarian, and in a sustained sector re-rating that costs money.

**It is concentrated and currently single-country.** Twelve names, all
ASX-listed. The jurisdictional framework is applied globally and whitelists
nobody — Australia is an output, not an input — but today it is the only Tier A
pass, so this is an Australian book with Australian weather, Australian politics
and Australian labour costs.

**It cannot be backtested, and no simulated track record will ever appear here.**
Point-in-time reserve statements and price decks do not exist for past dates, so
the gates cannot be honestly re-run on history. Every number published is
arithmetic on currently disclosed inputs — which is also why none of it carries
survivorship or look-ahead bias.

---

## Repository

| Path | What it is |
|---|---|
| [`index-methodology.md`](index-methodology.md) | The v2 methodology. §6 defines the separate core and optionality ledgers; §7 combines them with fully loaded funded EV |
| `build_index.py` | The engine: company gates, asset optionality gates, two ledgers, weighting, caps and basket sizing |
| `nav_model.py` | The §9 NAV model — implied deck and P/NAV. **Reporting only, by decision.** No output reaches a weight |
| `data/` | The provenance-tracked data layer — every value names the document it came from. [`data/README.md`](data/README.md) has the schema |
| `tools/` | `gaps.py` (what is missing) · `provenance.py` (whether it is any good) · `sensitivity.py` (what each gap is worth in pp) · `config_audit.py` (does the code read what config declares) · `snapshot.py` (point-in-time record and turnover) · `asymmetry.py` (up-versus-down capture) · `asx.py` (share counts, ADVT) · `fetch.py` / `extract.py` (sourcing) |
| `snapshots/` | One frozen directory per rebalance: data, parameters, output, engine commit |

Two rules govern every change:

- **DERIVE OR FAIL.** No invented inputs. A value without a source document is a
  gap to be closed or a name to be rejected, never an estimate.
- **Every parameter names a consumer.** `tools/config_audit.py` cross-checks each
  `config.json` leaf against the reads a real build recorded. A parameter that is
  declared but never read is a bug: it describes a rule the index does not apply.

---

## Licence

Provided for informational and educational purposes. This is not financial advice.
