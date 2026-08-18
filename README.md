# SJGV — Stable Jurisdiction Gold Value Index

**A gold miner index that counts ounces instead of market capitalisation.**

Buy a gold miner and what you are actually buying is a pile of gold that hasn't
been dug up yet. SJGV weights each company by **how much of that pile you get per
euro**, and buys nothing whose pile sits somewhere a government has a motive to
take.

Twelve ASX-listed companies. **A$679 of enterprise value per ounce of claimed
gold — against A$917 for the same twelve companies weighted by market cap.**
Same names, same day, same disclosed reserves. A quarter more gold in the ground
for the same money, purely from how the weights are set.

---

## Why ounces

A mine is a strip of call options on gold: one option per ounce, strike equal to
what that ounce costs to extract, expiring in whatever year the mine plan digs it
up. If you own gold miners for exposure to the gold price, the thing you want is
**the most options, at the lowest strikes, for the least money.**

Market-cap weighting cannot do that, and not by accident. It sizes each position
by what the market currently pays for that company's ounces, so the more
expensive an ounce becomes, the more of it you hold. Every re-rating buys you
less gold per euro and the index calls that a bigger position.

SJGV inverts it. One formula, no scores:

```
              ClaimedUnhedgedOunces_i
  w_i    ∝    ───────────────────────
                    FundedEV_i
```

Nothing else. No composite, no ranking, no quality tilt, no factor blend. A term
is allowed into the weight only if it changes **how many ounces are claimed, or
what was paid for them.** Everything else in this repository is a report.

---

## What goes into the count, and why it is not obvious

**Resources, not just reserves.** Proven & Probable is only the part a company
has already committed to mining at today's prices. SJGV also counts Measured &
Indicated at 0.5 and Inferred at 0.2. Those discounts are the only judgement left
anywhere in the weight, and they sit where a judgement belongs — deciding how
many ounces are claimed, not scoring a company.

This is the whole convexity position. Sub-economic ounces come into the money as
the gold price rises and the cut-off grade falls; that mechanism is the *reason*
a gold miner is geared to gold at all. An index counting only reserves owns the
in-the-money strip and none of the option. The current book is **57% reserves,
30% near-money M&I, 13% inferred tail** — and a book drifting toward reserves is
a book quietly losing its optionality.

**Hedged ounces are subtracted.** Gold a company has already sold forward is gold
you do not own the upside to. It comes off the reserve tranche first, because
that is where a forward gets delivered from.

**Unfunded capex is added to the price.** A developer sitting on ounces it cannot
afford to dig up has not really got them yet. The money still to be spent before
first pour is added to enterprise value, so the ounces are priced at what they
genuinely cost. Uncorrected, an unfunded project looks like the cheapest gold in
the world on the strength of money it has not raised.

**Everything is sourced to a document.** No estimated inputs, ever. A value with
no source is a gap to close or a company to reject — never a number someone made
up. Absence must never read as zero where zero would flatter.

---

## Two gates, and the two disasters they are for

Weighting only happens after two binary tests. Neither is a score, neither can be
offset by cheapness, and each is aimed at a different way of losing everything.

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
- **No requisition history, and no sleeping powers** — no confiscation, monopsony
  purchase mandate or forced domestic sale in the modern era, *including statutory
  powers suspended rather than repealed.* A dormant power is a live one.

Nothing here promises a state *cannot* take your gold. The claim is narrower and
testable: these are places with no record of doing it, no law still on the books
permitting it, and no structural reason to want to. It is a measured judgement
about relative likelihood, and the measurements are in the repository.

**Gate 2 — who is still standing.** *Does this company reach the other side of a
40% real gold drawdown without issuing equity?* Cash, undrawn facilities, free
cash flow at the stress price, committed capex, debt maturities. Run **unhedged**,
so nobody passes survival on the strength of the forward sales that reduce their
claim. The drawdown is applied to a three-year real average rather than to spot,
because anchoring to spot makes a survival gate weakest exactly when spot is most
extended.

Cost lives here and only here. AISC decides whether a company survives; it does
not decide how many ounces it owns, so it never reaches a weight.

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

## The book

**12 constituents · A$679 per claimed ounce · β_gold 1.72 · effective N 11.3**
Built 18 August 2026 against live IBKR prices, spot A$6,218/oz.

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

**It will lag when expensive quality re-rates.** Evolution is the most expensive
claim in the universe at A$1,827/oz and is held at 4%, against roughly 25% in a
cap-weighted book. When a name like that runs, this index does not participate.
That is not a flaw to be tuned away — it is the objective, working.

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
| [`index-methodology.md`](index-methodology.md) | The methodology. §6 is the ounce ledger and §7 the weight — those two sections are the entire model. §13 is the factor inventory: 46 inputs, established by perturbing each one and measuring the book, and no others |
| `build_index_v2.py` | The engine: gates, ledger, weighting, caps, basket sizing |
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
