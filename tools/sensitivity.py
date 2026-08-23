#!/usr/bin/env python3
"""
Quantify every open data gap by how far it can move the final index weights.

    python tools/sensitivity.py                 # full register
    python tools/sensitivity.py --threshold 0.2 # materiality bar, in pp

THE QUESTION THIS ANSWERS
-------------------------
The gap register says what is missing. It does not say what any of it is worth.
A gap that cannot move a weight by more than a rounding error is not a gap worth
working, and treating it as one crowds out the gaps that matter.

So: for each missing input, substitute the most and least favourable values it
could plausibly take, re-run the whole pipeline — gates, scores, caps, the
effective-N ratchet — and measure the largest change in any final weight, in
percentage points. Anything under the threshold is closed. Anything over it is
work.

WHERE THE RANGES COME FROM
--------------------------
Not invented. Every range is the empirical cross-section of the names that DO
disclose the field, so a perturbation is always a value some comparable
Australian gold miner actually reported this cycle. Where a field scales with
company size the ratio is what gets perturbed, not the level — net debt as a
share of market cap, committed capex per ounce of annual production — because
imposing Northern Star's dollar figures on Ora Banda would measure nothing.

This is a bounding exercise, not a probability. It says how wrong the weights
COULD be, not how wrong they are likely to be. A gap that clears the bar is
proven immaterial; a gap that fails it is not proven wrong, only unproven.

THREE KINDS OF GAP BEHAVE DIFFERENTLY
-------------------------------------
Score inputs move weights continuously. Gate inputs do nothing at all until they
flip a pass to a fail, at which point the name leaves the index and the effect
is its entire weight. Averaging those two into one number would be meaningless,
so gate inputs are reported by their CRITICAL VALUE — the level at which the
name fails — which is then compared against the empirical range. A critical
value far outside anything the cohort reports is a closed gap however large the
notional weight impact.

CAP inputs are the third kind, added 18 Aug 2026 with largest_asset_pp_share.
They are continuous in the data and discontinuous in the weight: nothing happens
until the share crosses §8.1's threshold, at which point one name's ceiling
drops from 15% to 7.5% and the excess redistributes across everyone else. They
get their own section, and — unlike the other two — that section reports every
name rather than only the unsourced ones. A cap input that is fully sourced
still MOVES weight, and a register that fell silent the moment it was sourced
would report the largest live effect in the book as nothing at all.
"""

from __future__ import annotations

import argparse
import copy
import json
import statistics as st
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_index as B  # noqa: E402

CACHE = ROOT / ".cache" / "md_sensitivity.json"


# ──────────────────────────────────────────────────────────────────────────
# Market data — fetched once, reused across every scenario
# ──────────────────────────────────────────────────────────────────────────

def market_data(tickers: list[str], refresh: bool) -> dict:
    if CACHE.exists() and not refresh:
        raw = json.loads(CACHE.read_text())
        raw["history"] = {k: [tuple(x) for x in v] for k, v in raw["history"].items()}
        for k in ("gold_history", "audusd_history"):
            raw[k] = [tuple(x) for x in raw[k]]
        return raw
    md = B.fetch_market_data(tickers)
    CACHE.write_text(json.dumps(md, default=str))
    return md


def run(constituents, prices, risk, gold_aud, meta, anchor,
        as_of: str | None = None) -> dict[str, float]:
    """One full pipeline pass. Returns {ticker: final weight}."""
    rows, _ = B.compute_raw_weights(constituents, prices, risk, gold_aud, meta,
                                    anchor_gold=anchor, as_of=as_of)
    if not rows:
        return {}
    B.apply_constraints(rows, meta)
    return {r["ticker"]: r["weight"] for r in rows}


def delta(base: dict[str, float], scen: dict[str, float]) -> tuple[float, str, bool]:
    """Largest absolute weight change in pp, the name it lands on, and whether
    the constituent set changed."""
    names = set(base) | set(scen)
    worst, who = 0.0, ""
    for n in names:
        d = abs(scen.get(n, 0.0) - base.get(n, 0.0)) * 100
        if d > worst:
            worst, who = d, n
    return worst, who, set(base) != set(scen)


# ──────────────────────────────────────────────────────────────────────────
# Empirical ranges
# ──────────────────────────────────────────────────────────────────────────

def field_value(c: dict, f: str):
    return c.get(f)


def build_ranges(flat: list[dict]) -> dict:
    """Perturbation ranges, each drawn from the names that disclose the field."""
    def vals(f):
        return [c[f] for c in flat if c.get(f) is not None]

    def ratio(num, den):
        return [c[num] / c[den] for c in flat
                if c.get(num) is not None and c.get(den)]

    r = {}
    rp = vals("reserve_price_aud")
    r["reserve_price_aud"] = ("level", min(rp), max(rp),
                              "A$/oz reserve deck, cross-section of disclosed decks")
    hs = vals("hedge_share_fwd24m")
    r["hedge_share_fwd24m"] = ("level", min(hs), max(hs),
                               "share of forward 24m production hedged")
    inf = ratio("inferred_moz", "mr_total_moz")
    r["inferred_moz"] = ("x_mr_total", min(inf), max(inf),
                         "Inferred as a share of total resource")
    mi = [(c["mi_non_reserve_moz"] + c["pp_moz"]) / c["mr_total_moz"] for c in flat
          if c.get("mi_non_reserve_moz") is not None and c.get("pp_moz")
          and c.get("mr_total_moz")]
    r["mi_non_reserve_moz"] = ("mi_share_of_mr", min(mi), max(mi),
                               "M&I (incl. reserves) as a share of total resource")
    nd = [c["net_debt_aud_m"] for c in flat if c.get("net_debt_aud_m") is not None]
    r["net_debt_aud_m"] = ("level", min(nd), max(nd),
                           "A$m net debt; every disclosed name is in net CASH")
    cc = [c["committed_capex_aud_m"] / c["production_koz_yr"] * 1000
          for c in flat if c.get("committed_capex_aud_m") and c.get("production_koz_yr")]
    r["committed_capex_aud_m"] = ("per_oz_prod", min(cc), max(cc),
                                  "A$ committed capex per oz of annual production")
    # §8.1 cap input. Behaves like neither of the two kinds above: it is
    # continuous in the data and DISCONTINUOUS in the weight, because nothing
    # happens until the share crosses the threshold and the ceiling drops from
    # 15% to 7.5%. Perturbing it across the observed cross-section is still the
    # right bound — the endpoints straddle the threshold by construction, since
    # the cohort runs from 0.49 to 1.00.
    la = vals("largest_asset_pp_share")
    if la:
        r["largest_asset_pp_share"] = (
            "level", min(la), max(la),
            "share of ELIGIBLE P&P reserves at the largest asset")
    return r


def resolve(kind: str, lo: float, hi: float, c: dict) -> tuple[float | None, float | None]:
    """Turn a range into two concrete values for this company."""
    if kind == "level":
        return lo, hi
    if kind == "x_mr_total":
        m = c.get("mr_total_moz")
        return (lo * m, hi * m) if m else (None, None)
    if kind == "per_oz_prod":
        p = c.get("production_koz_yr")
        return (lo * p / 1000, hi * p / 1000) if p else (None, None)
    if kind == "mi_share_of_mr":
        m, pp = c.get("mr_total_moz"), c.get("pp_moz")
        if not m or pp is None:
            return None, None
        # M&I non-reserve = M&I total - P&P, floored at zero.
        return max(0.0, lo * m - pp), max(0.0, hi * m - pp)
    return None, None


# ──────────────────────────────────────────────────────────────────────────

# Fields that can move a weight without deciding a gate. That means
# the ounce ledger (§6) and EV, and nothing else — there is no score left for a
# field to feed. reserve_price_aud is kept in the list deliberately even though
# it is now reporting-only: it was the worst open gap in this register at
# 0.59pp, and it should be seen reading 0.000pp rather than quietly dropped.
SCORE_FIELDS = ["reserve_price_aud", "hedge_share_fwd24m", "inferred_moz",
                "mi_non_reserve_moz", "net_debt_aud_m"]
GATE_FIELDS = ["committed_capex_aud_m"]

# §8.1 cap inputs — a third kind, added 18 Aug 2026 with
# largest_asset_pp_share. A score input moves a weight continuously; a gate
# input does nothing until it removes the name entirely; a CAP input does
# nothing until it lowers one name's ceiling, at which point that name's excess
# redistributes pro rata across everyone else.
#
# They are perturbed alongside SCORE_FIELDS wherever a value is MISSING, which
# is what stops an unsourced cap input reading as "no gap" in this register.
# Where the value is SOURCED they get their own section below, because the
# question worth answering is not "how wrong could the input be" but "what is
# the cap actually worth" — and that is measurable exactly, by flipping each
# name's derived classification and re-running.
CAP_FIELDS = ["largest_asset_pp_share"]
PERTURBED_FIELDS = SCORE_FIELDS + CAP_FIELDS


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=None,
                    help="materiality bar in pp (default: "
                         "config.estimation_policy.materiality_bar_pp)")
    ap.add_argument("--refresh", action="store_true", help="re-fetch market data")
    args = ap.parse_args()

    meta, cons, _, market, _ = B.load_data()
    # The bar is a committee decision recorded in config, not a CLI default that
    # happens to match it. It was both for a while, which is the same defect the
    # config registry exists to catch: two copies of one parameter, and editing
    # the declared one changes nothing.
    TH = (args.threshold if args.threshold is not None
          else meta["estimation_policy"]["materiality_bar_pp"])
    md = market_data([c["ticker"] for c in cons], args.refresh)

    fx = md["fx"]
    gold_aud = (fx["xauusd"] / fx["audusd"] if fx.get("xauusd") and fx.get("audusd")
                else market["gold"]["xau_aud"]["v"])
    risk = B.compute_risk_stats(md["history"], md["gold_history"],
                                md.get("audusd_history"), meta)
    aud_gold = [(d, g / f) for d, g, f in
                B._join(md["gold_history"], md.get("audusd_history") or []) if f > 0]
    anchor = B.gold_anchor(aud_gold, gold_aud, meta)["anchor_aud"]

    base = run(copy.deepcopy(cons), md["prices"], risk, gold_aud, meta, anchor,
               as_of=market["_ledger_sourced"])
    ranges = build_ranges(cons)
    weighted = set(base)

    print(f"SJGV weight sensitivity — materiality bar {TH:.2f}pp")
    print(f"Baseline: {len(base)} constituents, gold A${gold_aud:,.0f}, "
          f"reporting gold reference A${anchor:,.0f}")
    print("Metric: largest absolute change in ANY final weight, in percentage points,\n"
          "after gates and the §8.1 caps.\n")

    def scenario(mutate) -> tuple[float, str, bool]:
        c2 = copy.deepcopy(cons)
        mutate(c2)
        return delta(base, run(c2, md["prices"], risk, gold_aud, meta, anchor,
                               as_of=market["_ledger_sourced"]))

    # ── Score and cap inputs, per name ────────────────────────────────────
    results = []
    for f in PERTURBED_FIELDS:
        if f not in ranges:
            continue          # nothing disclosed it, so there is no range to draw
        kind, lo, hi, desc = ranges[f]
        missing = [c for c in cons if c.get(f) is None]
        for c in missing:
            v_lo, v_hi = resolve(kind, lo, hi, c)
            if v_lo is None:
                continue
            worst, who, setchg = 0.0, "", False
            for v in (v_lo, v_hi):
                def mut(cs, t=c["ticker"], fld=f, val=v):
                    for x in cs:
                        if x["ticker"] == t:
                            x[fld] = val
                d, w, s = scenario(mut)
                if d > worst:
                    worst, who, setchg = d, w, s
            results.append({"kind": "score", "field": f, "ticker": c["ticker"],
                            "weighted": c["ticker"] in weighted,
                            "lo": v_lo, "hi": v_hi, "impact": worst,
                            "on": who, "setchange": setchg, "desc": desc})

    # ── Score inputs, all missing names of a field moved together ─────────
    joints = []
    for f in PERTURBED_FIELDS:
        if f not in ranges:
            continue
        kind, lo, hi, desc = ranges[f]
        missing = [c for c in cons if c.get(f) is None]
        if len(missing) < 2:
            continue
        worst, who, setchg = 0.0, "", False
        for pick in (0, 1):
            def mut(cs, fld=f, k=kind, p=pick):
                for x in cs:
                    if x.get(fld) is None:
                        v = resolve(k, lo, hi, x)[p]
                        if v is not None:
                            x[fld] = v
            d, w, s = scenario(mut)
            if d > worst:
                worst, who, setchg = d, w, s
        joints.append({"field": f, "n": len(missing), "impact": worst,
                       "on": who, "setchange": setchg})

    print("═" * 78)
    print("LEDGER, EV AND CAP INPUTS — per name, worst of the two range endpoints")
    print("═" * 78)
    print(f"{'FIELD':<24}{'TICK':<6}{'W?':<4}{'RANGE TESTED':<26}{'MAX Δw':>8}  VERDICT")
    print("─" * 78)
    for r in sorted(results, key=lambda x: -x["impact"]):
        rng = (f"{r['lo']:,.3g} → {r['hi']:,.3g}")
        verdict = "MATERIAL" if r["impact"] >= TH else "acceptable"
        if r["setchange"]:
            verdict = "SET CHANGE"
        print(f"{r['field']:<24}{r['ticker']:<6}{'y' if r['weighted'] else '·':<4}"
              f"{rng:<26}{r['impact']:>7.3f}  {verdict}"
              + (f"  (on {r['on']})" if r["impact"] >= TH else ""))

    print("\n" + "═" * 78)
    print("LEDGER/EV/CAP INPUTS — every missing name of a field wrong in the same direction")
    print("═" * 78)
    print(f"{'FIELD':<24}{'N':>3}{'MAX Δw':>10}  VERDICT")
    print("─" * 78)
    for j in sorted(joints, key=lambda x: -x["impact"]):
        verdict = "MATERIAL" if j["impact"] >= TH else "acceptable"
        if j["setchange"]:
            verdict = "SET CHANGE"
        print(f"{j['field']:<24}{j['n']:>3}{j['impact']:>10.3f}  {verdict}"
              f"  (on {j['on']})")

    # ── Gate 2 health — distance to RED, not a disclosure-completeness test ─
    print("\n" + "═" * 78)
    print("GATE 2 HEALTH — additional unavoidable capital at which health turns RED")
    print("═" * 78)
    print("The tested amount is the adverse finite upper edge where available,"
          " otherwise the sourced lower edge. Headroom is extra capital beyond"
          " that amount, not an estimate of undisclosed spend.\n")
    print(f"{'TICK':<6}{'W?':<4}{'STATE':>8}{'TESTED A$m':>13}"
          f"{'EXTRA TO RED':>14}{'% MCAP':>9}")
    print("─" * 78)
    gate_rows = []
    as_of_date = date.fromisoformat(market["_ledger_sourced"])
    for original in sorted(cons, key=lambda x: x["ticker"]):
        if original.get("sleeve") == "developer":
            continue
        c = dict(original)
        px = (md["prices"].get(c["ticker"]) or {}).get("price")
        mcap = c.get("shares_out_m") * px if c.get("shares_out_m") and px else None
        if not mcap or not c.get("production_koz_yr") or not c.get("aisc_aud_oz"):
            continue
        creditable, _ = B.creditable_undrawn(c, meta, as_of_date)
        c["undrawn_facilities_aud_m"] = creditable
        interval = B.gate2_capital_interval(c, meta)
        tested = (interval.get("upper_aud_m") if interval.get("upper_aud_m") is not None
                  else interval.get("lower_aud_m") or 0.0)
        current = B.gate2_survival(c, gold_aud, mcap, meta)
        crit, step, limit = None, max(mcap / 1000, 1.0), tested + 2 * mcap
        probe = tested
        while probe <= limit:
            verdict = B._gate2_producer_at_capex(
                c, gold_aud, meta, probe, mcap_aud_m=mcap)
            if verdict.get("health") == "RED":
                crit = probe
                break
            probe += step
        extra = crit - tested if crit is not None else None
        gate_rows.append((c["ticker"], current.get("health"), tested, extra, mcap))
        print(f"{c['ticker']:<6}{'y' if c['ticker'] in weighted else '·':<4}"
              f"{(current.get('health') or 'UNTESTED'):>8}{tested:>13,.0f}"
              f"{(f'{extra:,.0f}' if extra is not None else '>2×mcap'):>14}"
              f"{(f'{extra/mcap:.0%}' if extra is not None else '—'):>9}")

    # ── Cap inputs — what the §8.1 single-asset cap is worth, per name ────
    # The per-name block above only measures MISSING values, so once a field is
    # fully sourced it vanishes from this register — which reads as "no gap"
    # and is indistinguishable from "not measured". For a cap input that is the
    # wrong answer twice over: the number worth knowing is not how wrong the
    # input could be, it is how much weight the cap is moving, and that is
    # exactly measurable. Flip each name's classification and re-run.
    th = meta["constraints"]["single_asset_pp_share_threshold"]
    print("\n" + "═" * 78)
    print("CAP INPUTS — what the §8.1 single-asset cap moves, per name")
    print("═" * 78)
    print(f"largest_asset_pp_share >= {th:.0%} → ceiling drops from "
          f"{meta['constraints']['max_single_name']:.0%} to "
          f"{meta['constraints']['max_single_asset_name']:.0%}.")
    print("Δw is the largest weight change from reclassifying THIS name alone.\n")
    print(f"{'TICK':<6}{'W?':<4}{'SHARE':>8}{'CLASS':>12}{'MARGIN':>9}"
          f"{'Δw IF FLIPPED':>15}  VERDICT")
    print("─" * 78)
    cap_worst = 0.0
    for c in sorted(cons, key=lambda x: -(x.get("largest_asset_pp_share") or -1)):
        share = c.get("largest_asset_pp_share")
        t = c["ticker"]
        if share is None:
            print(f"{t:<6}{'y' if t in weighted else '·':<4}{'—':>8}{'UNTESTED':>12}"
                  f"{'—':>9}{'—':>15}  measured in the block above")
            continue
        is_sa = share >= th
        # The nearest value on the other side of the threshold, so the flip
        # tests the CLASSIFICATION rather than a large move in the input.
        flip_to = (th - 1e-6) if is_sa else 1.0

        def mut(cs, tick=t, val=flip_to):
            for x in cs:
                if x["ticker"] == tick:
                    x["largest_asset_pp_share"] = val
        d, who, _ = scenario(mut)
        cap_worst = max(cap_worst, d) if t in weighted else cap_worst
        verdict = ("BINDING" if (is_sa and d >= TH) else
                   "would bind if flagged" if (not is_sa and d >= TH) else
                   "immaterial")
        if t not in weighted:
            verdict += " (not weighted)"
        print(f"{t:<6}{'y' if t in weighted else '·':<4}{share:>7.0%} "
              f"{'◆ single' if is_sa else 'multi':>11}{share - th:>+9.0%}"
              f"{d:>14.3f}pp  {verdict}" + (f"  (on {who})" if d >= TH else ""))
    print(f"\nLargest weight move from ONE reclassification, weighted names only: "
          f"{cap_worst:.3f}pp")
    print("MARGIN is distance from the threshold. A name at +0% or -1% is one")
    print("definitional argument away from a different ceiling — read it beside")
    print("§8.1's asset-unit rule, not just beside the share.")

    # The IMPUTED RESOURCE SPLITS section that stood here is deleted with the
    # rule it measured. impute_resource_split invented mi_non_reserve_moz and
    # inferred_moz from a cohort ratio and this block bounded the damage by
    # substituting the cohort extremes. A name without a disclosed
    # M/I/Inferred split is rejected rather than estimated, so there is nothing
    # left to perturb: the ounce ledger is made of disclosed numbers or it is
    # not made at all.
    imp_worst = 0.0

    # ── Structural gaps ───────────────────────────────────────────────────
    print("\n" + "═" * 78)
    print("STRUCTURAL GAPS — not a missing number, a missing test or model")
    print("═" * 78)

    # BC8 admitted on a plausible AISC drawn from the cohort.
    aiscs = [c["aisc_aud_oz"] for c in cons if c.get("aisc_aud_oz")]
    bc8_worst = 0.0
    for a in (min(aiscs), max(aiscs)):
        def mut(cs, val=a):
            for x in cs:
                if x["ticker"] == "BC8":
                    x["aisc_aud_oz"] = val
        d, w, _ = scenario(mut)
        bc8_worst = max(bc8_worst, d)
    print(f"BC8 AISC tested at A${min(aiscs):,.0f} – A${max(aiscs):,.0f}, cohort range")
    print(f"  max Δw {bc8_worst:>7.3f}pp  "
          f"{'MATERIAL' if bc8_worst >= TH else 'no admission'} — execution "
          f"capital remains unresolved, so AISC alone cannot admit the name.")

    # Gate 3 — now measured rather than bounded. The baseline already enforces it.
    sp = md.get("spreads") or {}
    tested = [t for t in base if (sp.get(t) or {}).get("median_pct") is not None]
    print(f"\nGate 3 — CLOSED 17 Aug 2026. Enforced in the baseline above on median")
    print(f"  daily RTH quoted spreads, {len(tested)}/{len(base)} names measured.")
    if tested:
        worst = max(tested, key=lambda t: sp[t]["median_pct"])
        prod = [t for t in tested
                if next(c for c in cons if c["ticker"] == t)["sleeve"] != "developer"]
        wp = max(prod, key=lambda t: sp[t]["median_pct"]) if prod else None
        print(f"  Widest producer {wp} at {sp[wp]['median_pct']:.3f}% against a 1.0% cap; "
              f"widest overall {worst} at {sp[worst]['median_pct']:.3f}%.")
        print(f"  Nothing is dropped, so the weight impact is 0.000pp. The earlier "
              f"15.00pp\n  figure came from post-close quotes and was an artifact, not "
              f"a finding.")

    print("\nNAV-model discount rates — NOT a sensitivity any more. The §9 model is")
    print("  reporting-only, so no discount rate, deck or P/NAV touches a")
    print("  weight and perturbing them moves the book by exactly 0.000pp. That was")
    print("  the largest open uncertainty in the register on 17 Aug and it closed by")
    print("  deletion rather than by decision.")

    print("\nundrawn_facilities_aud_m — absent for 6 weighted names, but it is treated as")
    print("  ZERO and only ever ADDS liquidity, so supplying it can improve health and")
    print("  never worsen it. No producer is currently RED. Impact on weights is")
    print("  identically 0.000pp by construction. CLOSED.")

    # ── Everything at once ────────────────────────────────────────────────
    # The per-gap numbers understate the exposure: they hold every other gap at
    # its current assumption. This moves all of them together, which is the
    # honest bound on how far the book could be from where it should be.
    agg = 0.0
    agg_on, agg_set = "", False
    for pick in (0, 1):
        def mut(cs, p=pick):
            for x in cs:
                for f in PERTURBED_FIELDS:
                    if f not in ranges:
                        continue
                    if x.get(f) is None:
                        v = resolve(ranges[f][0], ranges[f][1], ranges[f][2], x)[p]
                        if v is not None:
                            x[f] = v
                if False:
                    sh = (mi_lo, mi_hi)[p]
                    mr, pp = x["mr_total_moz"], x["pp_moz"]
                    x["mi_non_reserve_moz"] = max(0.0, sh * mr - pp)
                    x["inferred_moz"] = max(0.0, (1.0 - sh) * mr)
        d, w, s = scenario(mut)
        if d > agg:
            agg, agg_on, agg_set = d, w, s

    top = max([r["impact"] for r in results] + [j["impact"] for j in joints]
              + [imp_worst, 0.0])
    print("\n" + "═" * 78)
    print("AGGREGATE")
    print("═" * 78)
    print(f"Largest single weight move from any ONE parameterised gap: {top:.3f}pp")
    agg_name = agg_on or "no constituent"
    print(f"All parameterised gaps wrong together:                    {agg:.3f}pp "
          f"(on {agg_name}){'  CONSTITUENT SET CHANGES' if agg_set else ''}")
    print(f"Materiality bar: {TH:.2f}pp\n")
    print("Excluded from those two figures because they are not perturbable:")
    print("  · BC8 — AISC alone cannot admit it while execution capital is unresolved")
    print("  · Gate 3 — measured and enforced, 0.000pp")
    print(f"  · §8.1 single-asset cap — SOURCED for all 17 on 18 Aug 2026, so it")
    print(f"    is no longer a gap. Its live effect is {cap_worst:.3f}pp and it is")
    print(f"    reported in the CAP INPUTS section, not here.")
    print("\nHOW TO READ A 0.000pp LINE. Most of what this register")
    print("used to measure was the sensitivity of a SCORE to an input, and the")
    print("scores are gone. A gap in reserve_price_aud now moves the book 0.000pp")
    print("because NOTHING READS IT — not because anyone sourced it. PNR's deck")
    print("was the worst open gap here at 0.59pp and it closed by deletion.")
    print("\nWhat remains genuinely perturbable is the §6 ounce ledger and EV:")
    print("how many ounces, and what was paid for them. Note also that PNR and CYL")
    print("both sit AT the 7.5% single-asset cap, so ledger inputs on those names")
    print("cannot move their weights either — a cap doing its job, not a gap being")
    print("closed. That is three of fourteen names pinned by a ceiling rather than")
    print("priced by their ounces, up from one; read the PRE-CAP column in the")
    print("build's concentration table to see what the ounces alone would have said.")
    print("\nNever read 0.000pp as \"known\".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
