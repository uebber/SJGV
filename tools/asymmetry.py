#!/usr/bin/env python3
"""
Measure §10.3 — how the book behaves against gold in up periods versus down.

Two measures, and the order matters:

  CONVEXITY   β_up / β_dn from  r_p = α + β_up·g⁺ + β_dn·g⁻ + ε.  READ THIS ONE.
              The intercept absorbs drift, so what is left is curvature.
  raw         compounded up-capture ÷ down-capture, the classical ratio.
              Reported for continuity and because it was the headline until
              17 Aug 2026 — but it is ~97% a realised-return measure (per-name
              correlation with total return over the window: +0.97), because
              drift raises the numerator and cushions the denominator at once.

Both carry a bootstrap 95% interval. On this sample they are very wide, and that
is the finding: 23 down weeks cannot separate 1.5 from 1.6 from 3.0.

    python tools/asymmetry.py            # 5Y window, weekly and monthly
    python tools/asymmetry.py --years 3

Reads the basket from weights.json, so run build_index.py first.

DEMOTED. This was once the headline KPI. It is now secondary, and §10.2's
A$ of EV per claimed ounce is the headline, because that number is computed from
disclosed inputs and carries none of the biases below. Read the two together and
weight them by how much bias each contains.

WHAT THIS IS NOT
----------------
Not a backtest. A real backtest needs point-in-time reserves, price decks and
gates, so that constituents are chosen with the information available on each
historical date. We do not have that data. This measures how TODAY's basket, at
TODAY's weights, would have behaved — which is survivorship-biased (the names
that failed are not in it) and look-ahead-biased (the weights encode what we now
know). Both biases push the ratio UP. Treat the number as an upper bound and a
relative comparison against the comparators, never as an expected return.

The window also matters more than usual here. Gold has been in a violent bull
market; a sample with few genuine down periods estimates downside capture — the
denominator, and the whole point of the ratio — on very little evidence. The
count of down periods is reported for exactly this reason. Read it first.

MEASUREMENT CHOICES
-------------------
Weekly and monthly, not daily. The ASX close leads the metals-bar close by ~15
hours, so at daily frequency a gold move lands in the next session's equity bar
(see config risk.dimson_note). That misclassifies up and down days and corrupts
both captures. Weekly aggregation dissolves the offset instead of modelling it.

Everything is measured in AUD against AUD gold, including GDX, because that is
the numéraire an AUD-cost, AUD-listed book actually lives in.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import build_index as B  # noqa: E402

HOST = os.getenv("IB_HOST", "127.0.0.1")
PORT = int(os.getenv("IB_PORT", "7497"))
CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "43"))

# Share of basket weight that must be listed and trading before a date counts as
# representing the actual portfolio.
FULL_COVERAGE = 0.99


# ──────────────────────────────────────────────────────────────────────────
# Series helpers
# ──────────────────────────────────────────────────────────────────────────

def resample(series: list[tuple[str, float]], freq: str) -> list[tuple[str, float]]:
    """Last observation in each week or month. Dates are ISO 'YYYY-MM-DD'."""
    out: dict[str, tuple[str, float]] = {}
    for d, v in series:
        y, m, day = (int(x) for x in d.split("-"))
        if freq == "M":
            key = f"{y:04d}-{m:02d}"
        else:
            iso = datetime(y, m, day).isocalendar()
            key = f"{iso[0]:04d}W{iso[1]:02d}"
        out[key] = (d, v)          # dict preserves insertion order; later wins
    return [out[k] for k in sorted(out)]


def simple_returns(series: list[tuple[str, float]]) -> list[tuple[str, float]]:
    return [(d1, v1 / v0 - 1.0)
            for (_, v0), (d1, v1) in zip(series, series[1:]) if v0 > 0]


BOOTSTRAP_DRAWS = 2000

# The piecewise fit spends three parameters. Below these counts it is not an
# estimate, it is an interpolation, and the bootstrap around it degenerates in a
# way that can print a spuriously narrow interval — the monthly full-coverage
# window (13 observations, 5 of them down) produced a CI of [-11.27, -0.00] and
# a "significant at 95%" verdict off a bound that was numerically zero. Refuse
# to fit rather than print that.
MIN_STATE_OBS = 8
MIN_TOTAL_OBS = 24


def _ols2(ys: list[float], c1: list[float], c2: list[float]):
    """OLS of y on [1, c1, c2] by normal equations. Returns coefs or None.

    Local rather than B._ols_multi because that one refuses n < 60 — correct for
    a two-year daily beta, wrong here, where 59 weekly observations is the whole
    honest sample and refusing to fit it would just hide the imprecision this
    function exists to expose.
    """
    n = len(ys)
    if n < 8:
        return None
    X = [[1.0, c1[i], c2[i]] for i in range(n)]
    M = [[sum(X[i][r] * X[i][c] for i in range(n)) for c in range(3)]
         + [sum(X[i][r] * ys[i] for i in range(n))] for r in range(3)]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(M[r][i]))
        M[i], M[piv] = M[piv], M[i]
        if abs(M[i][i]) < 1e-18:
            return None
        for r in range(3):
            if r != i:
                f = M[r][i] / M[i][i]
                for c in range(i, 4):
                    M[r][c] -= f * M[i][c]
    return [M[i][3] / M[i][i] for i in range(3)]


def _piecewise(pairs) -> dict:
    """Drift-free convexity:  r_p = α + β_up·g⁺ + β_dn·g⁻ + ε.

    THE MEASURE TO READ. The compounded capture ratio beside it is dominated by
    drift rather than by curvature — measured 17 Aug 2026, per-name asymmetry
    ratio correlated **+0.97 with per-name total return** over the window. Drift
    raises the numerator and cushions the denominator, so it enters the ratio
    twice in the same direction and a name that merely went up scores as convex.
    VAU read 3.32 on a merger spread; PNR read 0.62 having fallen 23%. Neither
    number said anything about ounce inventory.

    Here the intercept absorbs the drift and what is left is curvature: how much
    of gold's up move the book takes against how much of its down move. On the
    same data the ranking inverted — SJGV 1.47 against cap-weighting's 1.28,
    where the raw ratio had said 1.50 against 1.59.

    α is returned and printed rather than buried. For a value strategy the drift
    IS information, and hiding it inside a capture ratio puts it in the one
    place nobody looks.
    """
    up = sum(1 for _, _, b in pairs if b > 0)
    dn = sum(1 for _, _, b in pairs if b < 0)
    if len(pairs) < MIN_TOTAL_OBS or up < MIN_STATE_OBS or dn < MIN_STATE_OBS:
        return {"convexity": None,
                "why": f"{len(pairs)} periods, {up} up / {dn} down — below the "
                       f"{MIN_TOTAL_OBS}/{MIN_STATE_OBS}/{MIN_STATE_OBS} floor "
                       f"for a three-parameter fit"}
    co = _ols2([p for _, p, _ in pairs],
               [b if b > 0 else 0.0 for _, _, b in pairs],
               [b if b < 0 else 0.0 for _, _, b in pairs])
    if co is None or co[2] <= 0:
        return {"convexity": None, "why": "regression degenerate"}
    return {"alpha": co[0], "beta_up": co[1], "beta_dn": co[2],
            "convexity": co[1] / co[2]}


def _bootstrap(pairs, stat, draws: int = BOOTSTRAP_DRAWS) -> dict:
    """Percentile CI for a statistic of the paired (portfolio, benchmark) periods.

    Resamples PERIODS with replacement, so it prices the one thing that dominates
    every number in this file: there are 23 down weeks. A point estimate off 23
    observations is not a finding, and this file reported one as though it were
    on 17 Aug 2026 — a −0.09 difference against cap-weighting that turned out to
    have a 95% interval of roughly ±2.5. The interval ships from now on.

    Seeded, so a snapshot of this output is reproducible.
    """
    rng = random.Random(20260818)
    n = len(pairs)
    vals = []
    for _ in range(draws):
        samp = [pairs[rng.randrange(n)] for _ in range(n)]
        v = stat(samp)
        if v is not None and math.isfinite(v):
            vals.append(v)
    if len(vals) < draws * 0.5:
        return {"lo": None, "hi": None, "n_ok": len(vals)}
    vals.sort()
    return {"lo": vals[int(0.025 * len(vals))],
            "hi": vals[int(0.975 * len(vals))], "n_ok": len(vals)}


def capture(port: list[tuple[str, float]],
            bench: list[tuple[str, float]]) -> dict:
    """Compounded capture ratios, the drift-free convexity, and CIs for both."""
    pairs = B._join(port, bench)
    if len(pairs) < 8:
        return {"error": f"only {len(pairs)} common periods"}

    def compound(rs: list[float]) -> float:
        out = 1.0
        for r in rs:
            out *= (1.0 + r)
        return out - 1.0

    up_p = [p for _, p, b in pairs if b > 0]
    up_b = [b for _, _, b in pairs if b > 0]
    dn_p = [p for _, p, b in pairs if b < 0]
    dn_b = [b for _, _, b in pairs if b < 0]

    cu_p, cu_b = compound(up_p), compound(up_b)
    cd_p, cd_b = compound(dn_p), compound(dn_b)

    up = cu_p / cu_b if cu_b > 0 else None
    dn = cd_p / cd_b if cd_b < 0 else None
    out = {
        "n_periods": len(pairs),
        "n_up": len(up_p), "n_down": len(dn_p),
        "up_capture": up, "down_capture": dn,
        "asymmetry_ratio": (up / dn) if (up is not None and dn) else None,
        "bench_up_cum": cu_b, "bench_down_cum": cd_b,
        "port_up_cum": cu_p, "port_down_cum": cd_p,
    }
    out.update(_piecewise(pairs))

    # Both measures get an interval, because both rest on the same 23 down
    # periods and neither is worth quoting without one.
    def _raw(sample):
        ub = compound([b for _, _, b in sample if b > 0])
        db = compound([b for _, _, b in sample if b < 0])
        if ub <= 0 or db >= 0:
            return None
        u = compound([p for _, p, b in sample if b > 0]) / ub
        d = compound([p for _, p, b in sample if b < 0]) / db
        return u / d if d else None

    def _cvx(sample):
        r = _piecewise(sample)
        return r.get("convexity")

    out["convexity_ci"] = _bootstrap(pairs, _cvx)
    out["asymmetry_ci"] = _bootstrap(pairs, _raw)
    out["pairs"] = pairs
    return out


def portfolio_series(hist: dict[str, list[tuple[str, float]]],
                     weights: dict[str, float]) -> tuple[list[tuple[str, float]], dict]:
    """Fixed-weight daily index from constituent closes.

    Names with ragged histories (recent listings) are handled by renormalising
    across whoever is present on each date rather than truncating everyone to
    the shortest series — Greatland alone would cut the window to ~1 year. The
    weight actually covered per date is reported so the dilution is visible.
    """
    rets: dict[str, dict[str, float]] = {}
    for sym, series in hist.items():
        if sym in weights:
            rets[sym] = {d: r for d, r in simple_returns(series)}

    all_dates = sorted({d for r in rets.values() for d in r})
    level, out, coverage = 1.0, [], []
    for d in all_dates:
        present = [(s, weights[s]) for s in rets if d in rets[s]]
        wsum = sum(w for _, w in present)
        if wsum <= 0:
            continue
        r = sum(w * rets[s][d] for s, w in present) / wsum
        level *= (1.0 + r)
        out.append((d, level))
        coverage.append(wsum)

    # First date from which the basket is essentially all present. Before it the
    # series is a renormalised stub — a handful of names standing in for the
    # whole book — and any capture measured across that stretch describes a
    # portfolio that did not exist.
    full_from = None
    for (d, _), w in zip(out, coverage):
        if w >= FULL_COVERAGE:
            full_from = d
            break

    return out, {
        "first": out[0][0] if out else None,
        "last": out[-1][0] if out else None,
        "min_weight_covered": min(coverage) if coverage else 0.0,
        "mean_weight_covered": sum(coverage) / len(coverage) if coverage else 0.0,
        "full_coverage_from": full_from,
        "full_coverage_threshold": FULL_COVERAGE,
    }


# ──────────────────────────────────────────────────────────────────────────

def fetch(tickers: list[str], duration: str) -> dict:
    from ib_insync import IB, Contract, Forex, Stock, util

    util.logToConsole(logging.ERROR)
    ib = IB()
    ib.connect(HOST, PORT, clientId=CLIENT_ID, readonly=True)
    out: dict = {"history": {}}
    try:
        for t in tickers:
            c = Stock(t, "ASX", "AUD")
            try:
                ib.qualifyContracts(c)
            except Exception:
                continue
            out["history"][t] = B._history(ib, c, "TRADES", duration)

        gdx = Stock("GDX", "ARCA", "USD")
        try:
            ib.qualifyContracts(gdx)
            out["gdx"] = B._history(ib, gdx, "TRADES", duration)
        except Exception:
            out["gdx"] = []

        gold = Contract(secType="CMDTY", symbol="XAUUSD",
                        exchange="SMART", currency="USD")
        ib.qualifyContracts(gold)
        out["gold"] = B._history(ib, gold, "MIDPOINT", duration)

        fx = Forex("AUDUSD")
        ib.qualifyContracts(fx)
        out["audusd"] = B._history(ib, fx, "MIDPOINT", duration)
    finally:
        ib.disconnect()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, default=5, help="History window (default 5).")
    args = ap.parse_args()
    duration = f"{args.years} Y"

    wpath = ROOT / "weights.json"
    if not wpath.exists():
        print("ERROR: weights.json not found — run build_index.py first.",
              file=sys.stderr)
        return 2
    built = json.loads(wpath.read_text())
    weights = {r["ticker"]: r["weight"] for r in built["weights"]}

    meta, cons, _, _, _ = B.load_data()
    shares = {c["ticker"]: c.get("shares_out_m") for c in cons}

    # DEMOTED. This measure was once the headline KPI; it is now §10.3, a
    # secondary and openly biased one, and reporting.headline_kpi names
    # aud_per_claimed_ounce instead. The check is kept — pointed the other way —
    # because the failure it guards against has flipped: the risk is no longer
    # that the tool computes a renamed KPI, it is that a reader takes THIS
    # number for the headline when the methodology no longer does.
    kpi = meta["reporting"]["headline_kpi"]
    if kpi == "asymmetry_ratio":
        print(f"ERROR: reporting.headline_kpi is {kpi!r}, but §10.2 makes the "
              f"headline A$ of EV per claimed ounce and demotes this measure to "
              f"§10.3. Config and methodology disagree — fix one.", file=sys.stderr)
        return 2

    print(f"SJGV §10.3 realised asymmetry — {len(weights)} names, {duration} window")
    print(f"Basket built {built['generated_utc'][:19]}Z")
    print(f"SECONDARY measure. The headline KPI is reporting.headline_kpi = "
          f"{kpi!r} (§10.2),")
    print(f"which is computed from disclosed inputs and carries none of the biases "
          f"listed below.\n")

    md = fetch(sorted(weights), duration)

    gold_aud = [(d, g / fx) for d, g, fx in B._join(md["gold"], md["audusd"]) if fx > 0]
    if len(gold_aud) < 60:
        print("ERROR: no usable AUD gold series.", file=sys.stderr)
        return 2
    audusd = dict(md["audusd"])
    gdx_aud = [(d, p / audusd[d]) for d, p in md["gdx"] if d in audusd]

    port, cov = portfolio_series(md["history"], weights)

    # Cap-weighted comparator over the SAME names — isolates the effect of the
    # weighting scheme from the effect of the universe. GDX changes both at once.
    last_px = {s: v[-1][1] for s, v in md["history"].items() if v}
    caps = {s: last_px[s] * shares[s] for s in weights
            if shares.get(s) and s in last_px}
    tot = sum(caps.values())
    capw, _ = portfolio_series(md["history"], {s: c / tot for s, c in caps.items()})

    full_from = cov["full_coverage_from"]
    print(f"Portfolio series {cov['first']} → {cov['last']}, "
          f"weight covered {cov['min_weight_covered']:.0%} min / "
          f"{cov['mean_weight_covered']:.0%} mean")
    print(f"  {FULL_COVERAGE:.0%}+ of the basket listed only from {full_from}. "
          f"Before that the series is a renormalised stub of whoever existed.")
    if md["gdx"]:
        print(f"GDX {md['gdx'][0][0]} → {md['gdx'][-1][0]}, converted to AUD")
    else:
        print("GDX unavailable — comparison limited to the cap-weighted basket")
    print()

    def clip(s, frm):
        return [(d, v) for d, v in s if frm is None or d >= frm]

    results = {}
    windows = [("FULL", None)]
    if full_from and full_from > (cov["first"] or ""):
        windows.append(("FULL-COVERAGE", full_from))

    for wlabel, frm in windows:
        for freq, flabel in (("W", "WEEKLY"), ("M", "MONTHLY")):
            gb = simple_returns(resample(clip(gold_aud, frm), freq))
            rows = [
                ("SJGV v1.0", simple_returns(resample(clip(port, frm), freq))),
                ("Cap-weighted, same names",
                 simple_returns(resample(clip(capw, frm), freq))),
            ]
            if gdx_aud:
                rows.append(("GDX (AUD)",
                             simple_returns(resample(clip(gdx_aud, frm), freq))))

            span = f"from {frm}" if frm else f"{cov['first']} →"
            print(f"{flabel} · {wlabel} ({span}) — benchmark: AUD gold")
            print(f"  {'':<26}{'β_up':>6}{'β_dn':>6}{'CONVEX':>8}"
                  f"{'95% CI':>16}{'α/pd':>8}  |{'raw':>6}{'95% CI':>16}"
                  f"{'n_up':>6}{'n_dn':>5}")
            print("  " + "─" * 108)
            for name, series in rows:
                c = capture(series, gb)
                results[f"{wlabel}:{freq}:{name}"] = c
                if "error" in c:
                    print(f"  {name:<26}{c['error']:>35}")
                    continue
                f = lambda v: f"{v:.2f}" if v is not None else "—"  # noqa: E731
                def ci(d):
                    if not d or d.get("lo") is None:
                        return "—"
                    return f"[{d['lo']:.2f}, {d['hi']:.2f}]"
                al = (f"{c['alpha']*100:+.2f}%" if c.get("alpha") is not None else "—")
                print(f"  {name:<26}{f(c.get('beta_up')):>6}{f(c.get('beta_dn')):>6}"
                      f"{f(c.get('convexity')):>8}{ci(c.get('convexity_ci')):>16}"
                      f"{al:>8}  |{f(c['asymmetry_ratio']):>6}"
                      f"{ci(c.get('asymmetry_ci')):>16}"
                      f"{c['n_up']:>6}{c['n_down']:>5}")
                if c.get("convexity") is None and c.get("why"):
                    print(f"  {'':<26}CONVEX not estimated — {c['why']}")

            # The comparison the committee actually cares about, with the
            # interval attached: is the weighting scheme beating cap-weighting
            # on curvature, or is the difference inside the noise? Paired on the
            # same periods, which is far more powerful than comparing the two
            # confidence intervals above by eye — the books share their names,
            # so most of the sampling error is common and cancels.
            base = results.get(f"{wlabel}:{freq}:SJGV v1.0")
            comp = results.get(f"{wlabel}:{freq}:Cap-weighted, same names")
            if base and comp and base.get("convexity") and comp.get("convexity"):
                pv = {d: p for d, p, _ in base["pairs"]}
                pc = {d: p for d, p, _ in comp["pairs"]}
                gb_ = {d: b for d, _, b in base["pairs"]}
                common = [d for d in pv if d in pc]
                trip = [(pv[d], pc[d], gb_[d]) for d in common]

                def diff(sample):
                    a = _piecewise([(0, x[0], x[2]) for x in sample])
                    b = _piecewise([(0, x[1], x[2]) for x in sample])
                    if a.get("convexity") is None or b.get("convexity") is None:
                        return None
                    return a["convexity"] - b["convexity"]

                d0 = base["convexity"] - comp["convexity"]
                bs = _bootstrap(trip, diff)
                verdict = ("INSIDE the noise" if bs["lo"] is None
                           or (bs["lo"] < 0 < bs["hi"]) else
                           "significant at 95%")
                print(f"  → SJGV − cap-weighted convexity: {d0:+.2f}  "
                      f"95% CI [{bs['lo']:+.2f}, {bs['hi']:+.2f}]  — {verdict}"
                      if bs["lo"] is not None else
                      f"  → SJGV − cap-weighted convexity: {d0:+.2f}  CI unavailable")
            print()

    # §10.1 — the demanding test. Ounce RATIOS only; the index level is an
    # arbitrary base of 1.0, so its absolute ounce value means nothing.
    for wlabel, frm in windows:
        pg = B._join(clip(port, frm), gold_aud)
        if not pg:
            continue
        oz = [p / g for _, p, g in pg]
        peak, mdd = oz[0], 0.0
        for v in oz:
            peak = max(peak, v)
            mdd = min(mdd, v / peak - 1.0)
        print(f"Ounce terms (§10.1) · {wlabel}: {(oz[-1] / oz[0] - 1) * 100:+.1f}% "
              f"in gold ounces, max drawdown {mdd:.1%}")
    print("  Rising in ounces means outperforming gold. That is the demanding "
          "test and the one that matters.")

    wk = results.get("FULL-COVERAGE:W:SJGV v1.0") or results.get("FULL:W:SJGV v1.0", {})
    ci = (wk.get("convexity_ci") or {})
    print("\nREAD THIS BEFORE QUOTING ANY NUMBER ABOVE")
    print(f"  • READ THE INTERVALS, NOT THE POINT ESTIMATES. Weekly full-coverage "
          f"convexity is")
    if ci.get("lo") is not None:
        print(f"    {wk.get('convexity', float('nan')):.2f} with a 95% interval of "
              f"[{ci['lo']:.2f}, {ci['hi']:.2f}] — a range that contains 'no "
              f"convexity at all'")
        print(f"    and 'three times gold'. Nothing in this table separates the "
              f"rows from each other.")
    print(f"  • {wk.get('n_down', 0)} down weeks in the whole sample. Every "
          f"downside number rests on those.")
    print("  • CONVEX is the measure. `raw` is ~97% realised return: drift raises "
          "up-capture and")
    print("    cushions down-capture, so it counts twice. Per-name it correlated "
          "+0.97 with total")
    print("    return over this window. It was the headline until 17 Aug 2026 and "
          "it misled us once —")
    print("    a −0.09 gap against cap-weighting was reported as a finding and had "
          "a CI of about ±2.5.")
    print("  • α is printed on purpose. For a value strategy the drift IS "
          "information, and folding")
    print("    it into a capture ratio hides it in the one place nobody looks.")
    print(f"  • Quote the FULL-COVERAGE rows. The FULL rows include a stretch "
          f"where as little as {cov['min_weight_covered']:.0%} of the basket was "
          f"listed.")
    print("  • Survivorship- and look-ahead-biased: today's names at today's "
          "weights, applied to the past. Both biases inflate every row.")
    print("  • Not a backtest. Point-in-time reserves and decks do not exist in "
          "the data layer, so the gates cannot be re-run historically.")
    print("  • The cap-weighted row is the honest comparator: same names, same "
          "window, only the weighting differs. GDX changes the universe and the "
          "weighting at once, so it cannot attribute either.")
    print("  • Where convexity COMES FROM matters more than its level. β_up above "
          "1 with β_dn also above 1")
    print("    is leverage, and §0.1 says leverage bleeds ounces round a cycle. "
          "β_dn BELOW β_up is the")
    print("    convexity the mandate is buying. Read the two betas, not the ratio.")

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "window": duration,
        "basket_generated": built["generated_utc"],
        "weights": weights,
        "coverage": cov,
        # `pairs` is the raw period-by-period series each statistic was computed
        # from. It is kept on the in-memory result so the paired SJGV-minus-cap
        # bootstrap can reuse it, and dropped here — it is ~100x the size of
        # everything else and reconstructible from the inputs.
        "results": {k: {kk: vv for kk, vv in v.items() if kk != "pairs"}
                    for k, v in results.items()},
        "caveats": ["not a backtest", "survivorship bias", "look-ahead bias",
                    "gold bull-market sample",
                    "CONVEX (piecewise beta, drift-free) is the measure; `raw` "
                    "compounded capture is ~97% realised return",
                    "every interval is a 2000-draw bootstrap over periods; on "
                    "23 down weeks they are wide enough to contain almost any "
                    "hypothesis"],
    }
    (ROOT / "asymmetry.json").write_text(json.dumps(out, indent=2, default=str))
    print("\nWrote → asymmetry.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
