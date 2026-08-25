#!/usr/bin/env python3
"""
SJGV v2.2 §9 — the internal NAV model. REPORTING ONLY.

    from nav_model import value_company, value_all, implied_deck

Built 17 August 2026 to feed Channel 1 of the convexity score. Later the same
day the convexity score was deleted (see build_index.py and methodology §10),
and this model was kept — but demoted, deliberately and permanently, to a
reporting instrument. Nothing it computes reaches a weight.

The demotion is not a delay pending better parameters. It is the conclusion:

  * The output that would have been weighted, NAV/price, measured +0.87
    log-correlated with the ounces-per-dollar ledger that already sets the
    weights. Adopting it would mostly have re-multiplied the ledger by itself.
  * Every NAV here moves with a discount rate that cannot be sourced from any
    filing. The index does not let a judgement call size a position, and a
    discount rate is the purest form of one.

What survives is the single sentence this model tells better than anything else
in the repo — the IMPLIED DECK. The gold price at which the market's valuation
of a company equals a rules-based DCF of that company's own disclosed reserves
is a statement about disagreement, in a unit anyone can argue with. Printed on
every build, weighted never.

WHAT THIS IS
------------
A rules-based, uniform, company-level DCF. Not broker consensus, and not an
asset-by-asset model: the data layer carries one production rate and one AISC
per company, because that is what is disclosed, so the model is built on what is
disclosed rather than on a mine schedule nobody has published.

    NAV = Σ_t  production × (deck − AISC) × (1 − tax) / (1 + r)^t   −  net debt

Ounces are mined in two phases:

  Phase 1  Reserves (P&P) at the current production rate, discounted at
           discount_rate_real_producing.
  Phase 2  Non-reserve material — M&I non-reserve and Inferred — at the SAME
           rate and the SAME AISC, starting the year reserves run out, and
           discounted at discount_rate_real_development. Ounces are converted at
           the §6.1 confidence weights, so 1 Moz of Inferred contributes 0.2 Moz
           of mine life.

Everything is real: a real discount rate against a flat real deck and a flat
real AISC. Nominal escalation of both sides of a margin is two assumptions that
mostly cancel, and inventing them would add nothing a reader could check.

WHY NON-RESERVE MATERIAL IS MINED RATHER THAN PRICED
----------------------------------------------------
§9 asks for in-situ A$/oz by confidence category. There is no way to set that
number that is not a judgement call, and `config.estimation_policy` exists
because judgement calls dressed as data are what this project keeps having to
withdraw. Mining the ounces instead reuses a parameter the committee has already
adopted (§6.1) and adds none.

It also makes gamma emerge instead of being assumed. An ounce twenty years out,
carried at today's AISC, is worth almost nothing at a low gold price and a great
deal at a high one — the option inventory is priced as an option because it is
discounted as one, not because a convexity factor was bolted on afterwards.

WHAT IT DELIBERATELY DOES NOT DO — read this before quoting a NAV
------------------------------------------------------------------
1. **No growth capital, and no ounces from growth capital.** Committed capex is
   excluded and so is the production it buys. Subtracting the spend without
   crediting the output would penalise every builder in the book, and committed
   capex is unsourced for five names, so including it would break the
   cross-section as well. The number is therefore the value of the CURRENT
   operation at the CURRENT rate — for NST, KCGM as it runs today, not as the
   mill expansion will run it.
2. **Gold only.** It has no denominator for non-gold NAV, so it cannot produce a
   forward gold-share-of-NAV. Methodology §5 keeps purity as a binary gate on
   TTM gold revenue and records that as a known limitation rather than an open
   item — building a non-gold data layer to serve one binary gate on one name
   (EVN, buying a copper company) is not proportionate.
3. **No cost curve.** One AISC per company. A company whose ounces sit at one
   cost and a company with the same average across a wide curve model
   identically here, and they should not. This is the same gap as methodology
   §12.2 item 2, seen from the valuation side instead of the ledger side.

AISC is used as the full cash cost per ounce because the WGC definition already
includes sustaining capital, royalties and corporate G&A. That is why no
separate line appears for any of them, and why no capitalised-overhead deduction
is taken: it would be a second charge for the same thing.

STATUS
------
Reporting only. There is no adoption switch, no `parameters_adopted` flag, and
no discount rate to publish and defend, because nothing depends on one. 5% real
producing and 9% real development are stated on every build and should be read
as what they are: the parameters of a diagnostic, held to the standard of a
diagnostic. If they ever need to meet a higher standard, something has gone
wrong upstream — a NAV has reached a weight.
"""

from __future__ import annotations

# A mine life longer than this is treated as a perpetuity of ounces nobody will
# ever produce. It binds on nothing in the current universe (the longest is
# Northern Star at ~47 years of confidence-weighted inventory) but it stops a
# company that reports a large resource against a small production rate from
# collecting value from years no discount rate meaningfully reaches.
MAX_MINE_LIFE_YEARS = 60.0


def _annuity_pv(cash_per_year: float, start_year: float, years: float,
                rate: float) -> float:
    """PV of a flat annual cash flow running from start_year for `years` years.

    Paid at the end of each year, and the final part-year is prorated rather
    than rounded up — a partial year of ounces is a partial year of cash, and
    rounding it up flatters every short-life name in the universe.
    """
    if years <= 0 or cash_per_year == 0:
        return 0.0
    pv, t = 0.0, start_year
    remaining = years
    while remaining > 1e-9:
        slice_yrs = min(1.0, remaining)
        t += slice_yrs
        pv += cash_per_year * slice_yrs / (1.0 + rate) ** t
        remaining -= slice_yrs
    return pv


def mine_plan(c: dict, conf: tuple[float, float, float]) -> dict | None:
    """Years of reserve and of confidence-weighted non-reserve inventory.

    Returns None when the company cannot be modelled at all, which is a stated
    outcome and not a zero: a NAV that silently reads zero would make a name look
    expensive rather than unmodelled.
    """
    prod = c.get("production_koz_yr")
    pp = c.get("pp_moz")
    if not prod or prod <= 0 or pp is None:
        return None

    w_pp, w_mi, w_inf = conf
    reserve_moz = pp * w_pp
    non_reserve_moz = ((c.get("mi_non_reserve_moz") or 0.0) * w_mi
                       + (c.get("inferred_moz") or 0.0) * w_inf)

    per_year_moz = prod / 1_000.0
    reserve_years = reserve_moz / per_year_moz
    non_reserve_years = non_reserve_moz / per_year_moz
    total = reserve_years + non_reserve_years
    truncated = total > MAX_MINE_LIFE_YEARS
    if truncated:
        non_reserve_years = max(0.0, MAX_MINE_LIFE_YEARS - reserve_years)

    return {
        "production_koz_yr": prod,
        "reserve_moz": reserve_moz,
        "non_reserve_cw_moz": non_reserve_moz,
        "reserve_years": reserve_years,
        "non_reserve_years": non_reserve_years,
        "truncated_at_max_life": truncated,
    }


def value_company(c: dict, deck_aud: float, cfg: dict,
                  conf: tuple[float, float, float]) -> dict | None:
    """NAV in A$m for one company at one gold deck. None if unmodellable.

    Developers are handled on the same arithmetic with two differences: the
    whole schedule is discounted at the development rate, and gross remaining
    execution capital is subtracted as a near-term outflow. Their
    production_koz_yr is planned nameplate from the study the §3.1 D1 gate
    already requires, so the input exists for every name that can pass that gate.
    """
    plan = mine_plan(c, conf)
    if plan is None:
        return None
    aisc = c.get("aisc_aud_oz")
    if aisc is None:
        return None

    nm = cfg["nav_model"]
    if nm["non_reserve_conversion"] != "confidence_weights":
        raise ValueError(
            f"nav_model.non_reserve_conversion is "
            f"{nm['non_reserve_conversion']!r}; this model converts non-reserve "
            f"material at the §6.1 confidence weights and has no other rule. "
            f"An in-situ A$/oz alternative would need the parameter that "
            f"config.estimation_policy exists to stop anyone inventing.")
    r_prod = nm["discount_rate_real_producing"]
    r_dev = nm["discount_rate_real_development"]
    tax = cfg["gate2"]["tax_rate"]
    developer = c.get("sleeve") == "developer"

    margin = deck_aud - aisc
    cash_per_year = plan["production_koz_yr"] * 1_000.0 * margin / 1e6  # A$m

    # Tax is charged on profit, not refunded on loss. A loss-making year in a
    # low-deck scenario is a loss, not a credit against tax the company is not
    # paying — treating it as a credit would flatter exactly the high-cost names
    # whose downside the deck sensitivity exists to expose.
    after_tax = cash_per_year * (1.0 - tax) if cash_per_year > 0 else cash_per_year

    r_reserve = r_dev if developer else r_prod
    pv_reserve = _annuity_pv(after_tax, 0.0, plan["reserve_years"], r_reserve)
    pv_non_reserve = _annuity_pv(after_tax, plan["reserve_years"],
                                 plan["non_reserve_years"], r_dev)

    net_debt = c.get("net_debt_aud_m") or 0.0
    remaining_capex = (
        c.get("remaining_execution_capex_aud_m") or 0.0
    ) if developer else 0.0

    nav = pv_reserve + pv_non_reserve - net_debt - remaining_capex
    return {
        "deck_aud": deck_aud,
        "nav_aud_m": nav,
        "pv_reserve_aud_m": pv_reserve,
        "pv_non_reserve_aud_m": pv_non_reserve,
        "net_debt_aud_m": net_debt,
        "remaining_execution_capex_aud_m": remaining_capex,
        "margin_aud_oz": margin,
        "discount_rate_reserve": r_reserve,
        "discount_rate_non_reserve": r_dev,
        **plan,
    }


def conservative_deck(cfg: dict, anchor_aud: float | None) -> tuple[float | None, str]:
    """The §9 conservative long-term deck, and where it came from.

    Default is the trailing 3-year real average of AUD gold. It is a
    reporting-only reference under v1.7; Gate 2 applies its shock to spot.
    Set nav_model.conservative_deck to "fixed" and give
    conservative_deck_aud_oz a value to override it.
    """
    nm = cfg["nav_model"]
    mode = nm["conservative_deck"]
    if mode == "fixed":
        v = nm.get("conservative_deck_aud_oz")
        return (v, f"fixed A${v:,.0f}/oz (config)") if v else (
            None, "fixed deck configured but conservative_deck_aud_oz is null")
    if mode not in {"trailing_real_reference", "gate2_anchor"}:
        raise ValueError(f"unknown nav_model.conservative_deck {mode!r}")
    if anchor_aud:
        return anchor_aud, "trailing real average of AUD gold"
    return None, "no trailing real AUD-gold reference available"


def value_all(constituents: list[dict], spot_aud: float, cfg: dict,
              conf: tuple[float, float, float],
              anchor_aud: float | None = None) -> dict[str, dict]:
    """NAV at both decks, plus modelled delta and gamma, per ticker.

    Delta is the elasticity of NAV to the gold price — %ΔNAV per %ΔAu — measured
    by a symmetric finite difference at ±delta_bump. That is the quantity
    directly comparable to a regressed β_gold, which is the point of §9.2:
    the two numbers can be put side by side and the difference argued about.

    Gamma is the change in that elasticity across the same bump — and READ THE
    NEXT PARAGRAPH BEFORE QUOTING IT.

    LOCAL GAMMA IS ZERO BY CONSTRUCTION, AND THAT IS A FINDING, NOT A RESULT.
    With a fixed mine plan, one AISC and no cut-off-grade response, NAV is
    exactly A·(deck − AISC) − debt: linear in the deck, so every finite
    difference of it returns the same delta and gamma vanishes identically. It
    is not that these companies have no gamma; it is that the disclosed data
    cannot express where their gamma comes from. Real convexity in a gold miner
    is the cut-off grade falling as the price rises — ounces that are waste at
    A$3,000 and ore at A$6,000 — and measuring that needs the grade-tonnage
    curves of §12.2 item 2, which the data layer does not carry for any name.

    So gamma is measured over a WIDE bump as well, where the model does bend:
    below the point where margin turns negative the company burns rather than
    earns, and net debt is a fixed subtraction that the equity feels more and
    more as NAV shrinks. That curvature is real, it is financial and operating
    leverage rather than option inventory, and §0.1 is explicit that leverage of
    that kind is what the product is trying NOT to be paid in. Reporting it next
    to a zero local gamma is the honest way to say both things at once.
    """
    nm = cfg["nav_model"]
    bump = nm["delta_bump"]
    stress = nm["stress_bump"]
    decks = nm["decks"]
    cons_deck, cons_basis = conservative_deck(cfg, anchor_aud)

    out: dict[str, dict] = {}
    for c in constituents:
        base = value_company(c, spot_aud, cfg, conf)
        if base is None:
            out[c["ticker"]] = {
                "modelled": False,
                "why": ("production, reserves or AISC unsourced — §8 cannot value "
                        "this name, which is reported rather than scored as zero"),
            }
            continue

        def nav_at(mult: float) -> float | None:
            v = value_company(c, spot_aud * mult, cfg, conf)
            return None if v is None else v["nav_aud_m"]

        nav = base["nav_aud_m"]
        up, down = nav_at(1.0 + bump), nav_at(1.0 - bump)
        s_up, s_down = nav_at(1.0 + stress), nav_at(1.0 - stress)

        delta = gamma = delta_up = delta_down = None
        up_capture = down_capture = asymmetry = stress_gamma = None
        if nav and nav > 0:
            # Elasticities measured over each half-bump separately, so gamma is
            # a real second difference rather than the average re-differenced.
            delta_up = (up - nav) / nav / bump
            delta_down = (nav - down) / nav / bump
            delta = (up - down) / (2.0 * bump * nav)
            gamma = (delta_up - delta_down) / bump

            # The same three quantities over the stress bump, where the model
            # actually bends. up_capture / down_capture is an asymmetry ratio on
            # MODELLED NAV — the §10.3 measure without the survivorship and
            # look-ahead bias, because nothing about it is historical.
            up_capture = (s_up - nav) / nav / stress
            down_capture = (nav - s_down) / nav / stress
            asymmetry = (up_capture / down_capture) if down_capture else None
            stress_gamma = (up_capture - down_capture) / stress

        rec = {
            "modelled": True,
            "nav_aud_m": nav,
            "nav_spot": base,
            "modelled_delta": delta,
            "modelled_delta_up": delta_up,
            "modelled_delta_down": delta_down,
            "modelled_gamma": gamma,
            "stress_bump": stress,
            "nav_up_capture": up_capture,
            "nav_down_capture": down_capture,
            "nav_asymmetry": asymmetry,
            "stress_gamma": stress_gamma,
            "nav_at_stress_up": s_up,
            "nav_at_stress_down": s_down,
            "reserve_years": base["reserve_years"],
            "total_life_years": base["reserve_years"] + base["non_reserve_years"],
            "truncated_at_max_life": base["truncated_at_max_life"],
            "decks": {"spot": nav},
            "deck_basis": {"spot": f"A${spot_aud:,.0f}/oz"},
        }
        if "conservative_long_term" in decks and cons_deck:
            cons = value_company(c, cons_deck, cfg, conf)
            rec["decks"]["conservative_long_term"] = cons["nav_aud_m"]
            rec["deck_basis"]["conservative_long_term"] = (
                f"A${cons_deck:,.0f}/oz — {cons_basis}")
            # The spread between decks IS the sensitivity (§9). Reported as the
            # share of spot NAV that survives the conservative deck, because a
            # ratio is comparable across a 300× range of company size.
            rec["deck_sensitivity"] = (cons["nav_aud_m"] / nav) if nav > 0 else None
        out[c["ticker"]] = rec
    return out


def portfolio_nav_asymmetry(rows: list[dict], navs: dict[str, dict]) -> dict:
    """Modelled upside and downside capture for the book, and the ratio.

    This is §10.3's realised ratio computed forward instead of backward. The
    historical version cannot be made into a backtest — no point-in-time
    reserves, no point-in-time decks, so the gates cannot be re-run on any past
    date — and both of its biases push it up. This one has no history in it at
    all: it is what the model says today's book does to a ±stress in the gold
    price, from today's balance sheets.

    **Read it as a statement about the model, not about the book.** On a fixed
    mine plan at one AISC, NAV is A×(deck − AISC) − debt, which is linear in the
    deck, so this ratio is 1.00 by construction and cannot be anything else. It
    measures NAV rather than price, so it says nothing about whether the market
    re-rates, and what curvature it does show at a wide bump is leverage rather
    than option inventory.

    Neither this nor the realised ratio is the headline KPI any more. §10.2 is:
    A$ of EV per claimed ounce, which is computed from the same disclosed inputs
    as the weights and carries no history and no discount rate. The honest proxy
    for convexity is the §6.1 ledger mix — how much of the claim is M&I
    non-reserve and Inferred rather than already-booked reserves.

    Coverage is reported because a weighted average over whichever names happen
    to be modellable is not a portfolio number, and that matters most exactly
    when the unmodelled ones are the unusual ones.
    """
    acc = {k: 0.0 for k in ("delta", "gamma", "up", "down", "w")}
    missing = []
    for r in rows:
        rec = navs.get(r["ticker"]) or {}
        if rec.get("modelled_delta") is None or rec.get("nav_up_capture") is None:
            missing.append(r["ticker"])
            continue
        w = r["weight"]
        acc["delta"] += w * rec["modelled_delta"]
        acc["gamma"] += w * (rec.get("stress_gamma") or 0.0)
        acc["up"] += w * rec["nav_up_capture"]
        acc["down"] += w * rec["nav_down_capture"]
        acc["w"] += w
    if acc["w"] <= 0:
        return {"coverage": 0.0, "missing": missing}
    w = acc["w"]
    up, down = acc["up"] / w, acc["down"] / w
    return {"delta": acc["delta"] / w, "stress_gamma": acc["gamma"] / w,
            "up_capture": up, "down_capture": down,
            "asymmetry": (up / down) if down else None,
            "coverage": w, "missing": missing}


def implied_deck(c: dict, mcap_aud_m: float, cfg: dict,
                 conf: tuple[float, float, float],
                 lo: float = 100.0, hi: float = 30_000.0) -> float | None:
    """The gold price at which modelled NAV equals the market capitalisation.

    The market's implied deck, which is the honest way to read a P/NAV: "priced
    at 0.6× NAV" and "priced as though gold were A$4,100/oz" are the same
    statement, but only the second can be argued with. Bisection, because NAV is
    monotonic in the deck by construction.
    """
    def f(p: float) -> float | None:
        v = value_company(c, p, cfg, conf)
        return None if v is None else v["nav_aud_m"] - mcap_aud_m

    flo, fhi = f(lo), f(hi)
    if flo is None or fhi is None or flo > 0 or fhi < 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2.0
        fm = f(mid)
        if fm is None:
            return None
        if abs(fm) < 1e-6 or hi - lo < 0.5:
            return mid
        if fm < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def summarise(navs: dict[str, dict]) -> str:
    """One line for the build header."""
    modelled = [v for v in navs.values() if v.get("modelled")]
    if not modelled:
        return "§8 NAV model: no name could be valued"
    lives = [v["total_life_years"] for v in modelled]
    return (f"§8 NAV model: {len(modelled)}/{len(navs)} valued, "
            f"inventory life {min(lives):.0f}–{max(lives):.0f} years")


__all__ = ["value_company", "value_all", "portfolio_nav_asymmetry",
           "conservative_deck", "implied_deck", "mine_plan", "summarise",
           "MAX_MINE_LIFE_YEARS"]
