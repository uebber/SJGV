#!/usr/bin/env python3
"""
SJGV v2.0 — index construction and basket sizing.

Computes the basket from the data layer rather than from a hardcoded list, and
May-2026 weights (including RUP, delisted 16 Jun 2026 into Agnico Eagle).

What changed structurally
-------------------------
Weights are computed from an ounce ledger:

    w_i  ∝   ClaimedUnhedgedOunces_i  ÷  FundedEV_i

where the numerator is built by subtraction, never by scoring:

    attributable ounces, by JORC category
      × eligible_ounce_share      Gate 1 — ounces outside an eligible
                                  jurisdiction are not owned in any sense
                                  this product recognises
      × confidence weight         P&P 1.0, M&I non-reserve 0.5, Inferred 0.2
      − ounces sold forward       hedge_share_fwd24m × 24 months of production,
                                  taken off the P&P tranche because that is
                                  what a forward is delivered from
      = the claim

and the denominator is sleeve-specific:

    producer:                EV = market cap + net debt
    near-producer/developer: AllInEV = EV + remaining execution capital

Established producers use standard enterprise value because issuers do not
normally publish a complete company-wide cost-to-completion schedule.  Their
sourced execution-capital records remain reporting evidence, not weight inputs.
Near-producers and developers still pay gross remaining execution capital;
developer project funding stays separate and reduces only the residual funding
gap used by developer Gate 2, never the denominator.

There is no scoring layer between that ledger and the
weight: a five-channel convexity score, a purity multiplier, an inverse-σ_idio
denominator, and an idiosyncratic-variance cap. They were measured against the
book on 17 August 2026 and the finding was unambiguous — the channels were
monotone restatements of the ledger (c1 +0.87, c2b +0.55 and c3 +0.56 in log
correlation with ounces/EV), one of them was algebraically identical to the
numerator (c2b == eligible_cw_moz / pp_moz, so the resource inventory entered
the weight SQUARED), and σ_idio at +0.77 with ounces/EV cancelled the very
signal the numerator exists to express. Deleting all of it left the same twelve
constituents, the same delta, and a book holding MORE ounces per dollar:
A$642/oz of EV against A$682/oz. The current design principle is documented in
docs/investment-case.md §2.

The rule that replaced them: a term enters the weight only if it changes how
many ounces are claimed, or what was paid for them. Nothing else is a weight.

Market cap is NOT a weight driver — it enters only through EV (as the equity
component) and via the reported capacity number. Constituent fundamentals live
in data/; this file is the engine.

Risk statistics (β_gold, R², σ_idio) are regressed from IBKR daily bars against
gold in AUD — the correct regressor for AUD-listed, AUD-cost producers. They are
REPORTED ONLY. β_gold checks the §0 mandate band; nothing regressed from price
history touches a weight, so a name with too little listing history is still
weightable and merely un-diagnosed.

Base currency is EUR (simulation AUM €1,000,000). The reporting numéraire is
gold ounces per methodology §10.1: the index level is expressed in ounces and
EUR is secondary. In ounce terms the portfolio only gains if it
outperforms gold, which is the demanding measure and the right one.

Missing data is never silently defaulted. A constituent lacking an input the
ledger requires is EXCLUDED with a stated reason and reported in the diagnostics
block. There is no longer anywhere for a missing value to "degrade a score
toward neutral" — a term either counts ounces or it does not exist — and an
unsourced hedge book is NOT read as unhedged: it excludes the name, because an
unknown short position against the claim is not a claim that can be sized.

Nor is a declared parameter silently unenforced. Every key in data/config.json
must name a consumer in CONFIG_PARAMS, every claim of "engine-read" is checked
against what the build actually touched, and tools/config_audit.py holds the two
against each other. That machinery exists because the opposite happened three
times: Gate 3 never ran, five §8.1 constraints were declared and unwired, and
three more parameters were declared in config AND hardcoded here to the same
values, so editing config changed nothing.

The §8 NAV model (nav_model.py) runs on every build and is REPORTING ONLY, by
decision rather than pending one. It states what deck the market is implying for
each name — the most useful single sentence in the output — and it is not
allowed near a weight, because a discount rate is a judgement and this index
does not let judgements set positions. That closes the old §13 item 3: there is
no discount rate left to adopt or defend.

Setup
-----
1. pip install ib_insync
2. Run TWS or IB Gateway. Configure → API → Settings:
     - Enable ActiveX and Socket Clients
     - Read-Only API is fine
     - Ports: 7497 (paper) / 7496 (live), 4002 (gw paper) / 4001 (gw live)
3. Optional env vars (defaults shown):
     export IB_HOST=127.0.0.1
     export IB_PORT=7497
     export IB_CLIENT_ID=42

Run
---
    python build_index.py                      # weights + diagnostics only
    python build_index.py 1000000              # size a €1,000,000 basket
    python build_index.py 1000000 --commission 0.1
    python build_index.py --nav-detail         # per-name §8 NAV, P/NAV, implied deck
    python build_index.py --gold-aud 6170 --euraud 1.636   # offline overrides

Outputs weights.csv/json for SJGV and gate1_cap_weights.csv/json for the parallel
Gate-1-only market-cap variant. When sized, it likewise writes basket.csv/json
and gate1_cap_basket.csv/json. Every run also writes market_bundle.json +
market_bars.csv — the raw TWS session shared by both variants: request
parameters, contract identifiers, per-quote market-data type, timestamps at
both ends of every call, and the engine commit. That is the market leg's source
document, and tools/snapshot.py freezes it with the rest. Then:

    python tools/config_audit.py --strict         # after any config edit
    python tools/snapshot.py                      # after any rebalance
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import itertools
import json
import logging
import math
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import nav_model

HOST = os.getenv("IB_HOST", "127.0.0.1")
PORT = int(os.getenv("IB_PORT", "7497"))
CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "42"))

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

# Gold and AUD/USD are pulled over a longer window than the equities because the
# trailing NAV reference averages over gate2.anchor_years. The regression is unaffected:
# it inner-joins on the equity dates, so it still spans the equity window.
GOLD_HISTORY_DURATION = "5 Y"

# Fallbacks only. The live values are config.risk.regression_window and
# config.gates.spread_window; these two constants are what the engine used
# before those keys were wired, and they are kept solely so a caller that never
# loads the config still gets the documented window rather than an exception.
#
# The equity window balances responsiveness against the noise of an OLS on
# volatile small caps. The spread window matches the §12 light-rebalance cadence
# and is long enough that one disorderly session cannot decide a gate.
HISTORY_DURATION_DEFAULT = "2 Y"
SPREAD_DURATION_DEFAULT = "3 M"
TRADING_DAYS = 252
# Mean Gregorian month. Only ever used to express a document age in months for a
# threshold measured in months; nothing compounds on it.
DAYS_PER_MONTH = 30.4375

MARKET_DATA_TYPE_LABELS = {1: "live", 2: "frozen", 3: "delayed", 4: "delayed-frozen"}

# What the session asks TWS for. 4 = frozen realtime where the account is
# subscribed, delayed-frozen otherwise. Named here because the bundle records it
# as the REQUESTED type alongside the type each ticker actually came back as,
# and those two disagree per contract depending on entitlement and time of day.
MARKET_DATA_TYPE_REQUESTED = 4

# The raw bar record, in IBKR's own field order. BID_ASK bars do not carry
# prices in these fields' usual sense — see _spread_history — so the columns are
# named after the API, not after what a TRADES bar happens to mean.
BAR_COLUMNS = ("series", "date", "open", "high", "low", "close", "volume",
               "average", "bar_count")

# Ticker fields copied verbatim into the bundle. A defined list rather than a
# sweep of the object: the point of a frozen input is that the same build reads
# the same fields next year, and an attribute that appears or disappears with an
# ib_insync release would silently change the record. Anything absent on this
# version records as null rather than vanishing.
TICKER_FIELDS = (
    "marketDataType", "bid", "bidSize", "ask", "askSize", "last", "lastSize",
    "prevBid", "prevAsk", "prevLast", "volume", "open", "high", "low", "close",
    "vwap", "halted", "delayedBid", "delayedAsk", "delayedLast", "delayedClose",
)

# Contract fields copied verbatim. conId is the identifier that matters: symbol
# and exchange are what we ASKED for, conId is what IBKR resolved it to, and a
# reissued or re-listed ASX code is exactly the case where the two diverge.
CONTRACT_FIELDS = (
    "conId", "secType", "symbol", "localSymbol", "tradingClass", "exchange",
    "primaryExchange", "currency", "multiplier", "lastTradeDateOrContractMonth",
)


# ──────────────────────────────────────────────────────────────────────────
# Numeric helpers
# ──────────────────────────────────────────────────────────────────────────

def _f(x) -> float | None:
    """None for NaN/None, else float."""
    if x is None:
        return None
    try:
        if math.isnan(x):
            return None
    except TypeError:
        return None
    return float(x)


def _pos(x) -> float | None:
    """Float only if finite and strictly positive. IBKR uses -1.0 as a 'no data'
    sentinel on delayed-frozen tickers, and 0.0 is never a valid price — both
    must be rejected before they leak into sizing math."""
    v = _f(x)
    if v is None or v <= 0:
        return None
    return v


def _ols(ys: list[float], xs: list[float]) -> tuple[float, float, float, float] | None:
    """OLS of y on x. Returns (alpha, beta, r2, residual_std) or None.

    Pure Python to avoid a numpy dependency the rest of the module doesn't need.
    """
    n = len(ys)
    if n < 60 or n != len(xs):
        return None

    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None

    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = sxy / sxx
    alpha = my - beta * mx

    resid = [y - (alpha + beta * x) for x, y in zip(xs, ys)]
    ss_res = sum(r * r for r in resid)
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Two parameters estimated, hence n - 2.
    resid_std = math.sqrt(ss_res / (n - 2)) if n > 2 else 0.0
    return alpha, beta, r2, resid_std


def _ols_multi(ys: list[float],
               cols: list[list[float]]) -> tuple[list[float], float, float] | None:
    """OLS of y on an intercept plus each column. Returns (coefs, r2, resid_std).

    coefs[0] is the intercept. Solved through the normal equations with partial
    pivoting — the design here is three collinear-ish return columns, small
    enough that the numerical shortcomings of X'X don't bite.
    """
    n = len(ys)
    k = len(cols) + 1
    if n < 60 or any(len(c) != n for c in cols):
        return None

    X = [[1.0] + [c[i] for c in cols] for i in range(n)]
    M = [[sum(X[i][r] * X[i][c] for i in range(n)) for c in range(k)]
         + [sum(X[i][r] * ys[i] for i in range(n))] for r in range(k)]

    for i in range(k):
        p = max(range(i, k), key=lambda r: abs(M[r][i]))
        M[i], M[p] = M[p], M[i]
        if abs(M[i][i]) < 1e-18:
            return None
        for r in range(k):
            if r != i:
                f = M[r][i] / M[i][i]
                for c in range(i, k + 1):
                    M[r][c] -= f * M[i][c]
    coefs = [M[i][k] / M[i][i] for i in range(k)]

    my = sum(ys) / n
    resid = [y - sum(co * xv for co, xv in zip(coefs, X[i]))
             for i, y in enumerate(ys)]
    ss_res = sum(r * r for r in resid)
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return coefs, r2, math.sqrt(ss_res / (n - k)) if n > k else 0.0


def _log_returns(closes: list[float]) -> list[float]:
    return [
        math.log(b / a)
        for a, b in zip(closes, closes[1:])
        if a and b and a > 0 and b > 0
    ]


# ──────────────────────────────────────────────────────────────────────────
# Configuration registry
# ──────────────────────────────────────────────────────────────────────────

# Every parameter in data/config.json, and what consumes it.
#
# WHY THIS EXISTS. Three separate times a parameter has been declared in
# config.json, cited to a methodology section, and read by no code whatsoever:
# producer_max_spread_pct and developer_max_spread_pct (Gate 3 had never run);
# then max_idio_variance_contribution, max_single_asset, capacity_max_days_advt,
# capacity_max_participation and min_r2_gold; and beneath those, the whole
# confidence_weights block, the regression window and the spread window, each of
# which the engine had hardcoded to a constant that merely happened to agree.
#
# A declared parameter nothing reads is worse than a missing one. The
# methodology then states that the index enforces something it does not enforce,
# and every reader of config.json believes it — including the next session.
#
# KNOWN_FIELDS closed exactly this hole on companies.json: tools/gaps.py imports
# it and cross-checks in BOTH directions, so the data and its audit cannot
# silently disagree. This is the equivalent for config.json and
# tools/config_audit.py is the equivalent auditor. Every parameter must name a
# consumer, and a key ending in `.*` claims everything beneath it:
#
#   engine       read on every build. CONFIG_READS proves it at runtime — a line
#                here is a CLAIM, and the claim is checked against what the
#                process actually touched.
#   conditional  read by the engine only on some paths: a developer in the
#                universe, a fallback, a switched-off rule. Not observed every
#                run, so silence is not evidence of a defect.
#   tools/x.py   read by a tool rather than by the build.
#   process      a committee decision no code consumes BY DESIGN — a cadence, a
#                label. The reason is mandatory, so that "nothing reads it" is a
#                decision on the record rather than an oversight.
#   evidence     observations a parameter was calibrated on, kept for audit.
CONFIG_PARAMS: dict[str, tuple[str, str]] = {
    "methodology": ("engine", "printed in the build header"),
    "adopted": ("engine", "printed in the build header"),

    "objective.beta_target": ("engine", "§0 mandate band, checked and reported"),

    "risk.beta_estimator": ("engine", "dimson | contemporaneous — diagnostic only"),
    "risk.dimson_lags": ("engine", "±k days summed into β_gold"),
    "risk.regression_window": ("engine", "IBKR durationStr for the equity history"),

    "confidence_weights.proven_probable": ("engine", "§6 P&P ounce weight"),
    "confidence_weights.measured_indicated_non_reserve": (
        "engine", "§6 M&I non-reserve ounce weight"),
    "confidence_weights.inferred": ("engine", "§6 Inferred ounce weight"),
    "confidence_weights.hedge_horizon_years": (
        "engine", "§6.3 months of production a disclosed hedge book covers"),

    "gates.purity_floor_gold_nav_share": ("engine", "§5 hard floor"),
    "gates.max_ineligible_nav_share": ("engine", "§2.4 entity-level cap"),
    "gates.producer_max_spread_pct": ("engine", "§4 Gate 3"),
    "gates.developer_max_spread_pct": ("engine", "§4 Gate 3, developer sleeve"),
    "gates.spread_measure": ("engine", "asserted against what _spread_history measures"),
    "gates.spread_window": ("engine", "IBKR durationStr for the BID_ASK history"),
    "gates.capacity_max_days_advt": ("engine", "§4.3 capacity, REPORTED not enforced"),
    "gates.capacity_max_participation": (
        "engine", "§4.3 capacity, REPORTED not enforced"),
    "gates.max_resource_statement_age_months": (
        "engine", "§6.4 — the bar statement_currency() applies to the document "
                  "behind every counted tranche"),

    "gate2.gold_drawdown": ("engine", "§3 stress"),
    "gate2.anchor": ("engine", "trailing_average | spot"),
    "gate2.anchor_years": ("engine", "length of the trailing real average"),
    "gate2.anchor_inflation_pa": ("engine", "past prices into today's money"),
    "gate2.cost_inflation_pa": ("engine", "AISC path over the horizon"),
    "gate2.horizon_years": ("engine", "§3 survival horizon"),
    "gate2.tax_rate": ("engine", "§3 survival FCF, and the §8 NAV model"),
    "gate2.count_undrawn_facilities": ("engine", "§3 liquidity definition"),
    "gate2.stress_price_basis": ("engine", "spot basis for the literal drawdown"),
    "gate2.producer_max_rescue_capital_of_mcap": (
        "engine", "largest manageable producer recapitalisation"),
    "gate2.producer_max_recovery_years": (
        "engine", "maximum normalised recovery burden"),
    "gate2.developer_min_study_stage": (
        "conditional", "§3.1 D1 — read only when a developer is in the universe"),
    "gate2.developer_max_funding_gap_of_mcap": (
        "conditional", "§3.1 D3 — read only when a developer is in the universe"),
    "execution_capital.materiality_of_ev": (
        "engine", "build_index.execution_capital_ledger — aggregate execution "
                  "capital below this share of pre-capex EV is de minimis"),
    "execution_capital.incumbent_max_carry_forward_months": (
        "engine", "build_index.resolve_execution_capital — maximum age of an "
                  "unchanged gross incumbent capital balance"),
    "constraints.max_single_name": ("engine", "§8.1 impairment cap"),
    "constraints.max_single_asset_name": (
        "engine", "§8.1 tighter cap for single-asset companies"),
    "constraints.max_guidance_delivery_name": (
        "engine", "§8.2 cap for names with a delivery CAP rating"),
    "constraints.single_asset_pp_share_threshold": (
        "engine", "§8.1 — largest_asset_pp_share at or above this derives "
                  "single_asset; see derive_single_asset()"),
    "constraints.max_developer_sleeve": ("engine", "§8.1"),
    "constraints.max_developer_single_name": ("engine", "§8.1"),

    "nav_model.built": ("engine", "guards the §9 model"),
    "nav_model.discount_rate_real_producing": ("engine", "§9, reporting only"),
    "nav_model.discount_rate_real_development": ("engine", "§9, reporting only"),
    "nav_model.conservative_deck": (
        "engine", "trailing_real_reference | fixed"),
    "nav_model.conservative_deck_aud_oz": (
        "conditional", "read only when conservative_deck is 'fixed'"),
    "nav_model.decks": ("engine", "§9, the decks NAV is reported at"),
    "nav_model.non_reserve_conversion": ("engine", "§9 resource treatment"),
    "nav_model.delta_bump": ("engine", "§9 finite-difference step for dNAV/dAu"),
    "nav_model.stress_bump": ("engine", "wide bump for modelled NAV up/down capture"),

    "estimation_policy.materiality_bar_pp": (
        "tools/sensitivity.py", "the 0.2pp bar a gap must clear to be closed"),
    "estimation_policy.permitted_provenance.*": (
        "process", "the sourcing rule humans apply; no code can enforce it"),

    "rebalance.deep": ("process", "§12 cadence, executed by the operator"),
    "rebalance.light": ("process", "§12 cadence, executed by the operator"),
    "rebalance.event_driven": ("process", "§12 trigger list, judged by the operator"),

    "reporting.numeraire_primary": ("engine", "§10.1 — labels the sizing output"),
    "reporting.numeraire_secondary": ("engine", "§10.1 — labels the sizing output"),
    "reporting.headline_kpi": ("tools/asymmetry.py", "§10.2 names the KPI it measures"),

    "variants.gate1_cap.methodology": (
        "engine", "§14 name and version for the Gate-1-only cap-weighted variant"),
    "variants.gate1_cap.adoption_date": (
        "engine", "§14 adoption date for the Gate-1-only cap-weighted variant"),
    "variants.gate1_cap.weighting": (
        "engine", "§14 assertion that the variant uses full market capitalisation"),
    "variants.gate1_cap.max_constituents": (
        "engine", "§14 number of largest eligible companies retained"),
}

# Keys carrying prose rather than parameters. Rationale — the reason a number is
# what it is — belongs beside the number, and this codebase keeps it there
# deliberately, so the audit has to be able to tell the two apart. Nested only:
# a top-level scalar is always a parameter.
DOC_KEY_NAMES = frozenset({"ref", "why", "rule", "on_absence", "forbidden",
                           "adopted", "decks_note"})
DOC_KEY_SUFFIXES = ("_note", "_notes", "_warning", "_withdrawn")


def is_documentation(path: str) -> bool:
    """True for a config key that is prose, not a parameter."""
    leaf = path.rsplit(".", 1)[-1]
    if "." not in path:
        return leaf.startswith("_")
    return (leaf.startswith("_") or leaf in DOC_KEY_NAMES
            or leaf.endswith(DOC_KEY_SUFFIXES))


def config_leaves(cfg: dict, prefix: str = "") -> list[str]:
    """Every parameter path in a config tree, documentation excluded."""
    out = []
    for key, value in cfg.items():
        path = f"{prefix}.{key}" if prefix else key
        if is_documentation(path):
            continue
        if isinstance(value, dict):
            out.extend(config_leaves(value, path))
        else:
            out.append(path)
    return out


def claimed_by(path: str) -> tuple[str, str] | None:
    """The registry entry covering `path`, directly or by a `.*` prefix."""
    if path in CONFIG_PARAMS:
        return CONFIG_PARAMS[path]
    parts = path.split(".")
    for i in range(len(parts) - 1, 0, -1):
        wildcard = ".".join(parts[:i]) + ".*"
        if wildcard in CONFIG_PARAMS:
            return CONFIG_PARAMS[wildcard]
    return None


# Populated at runtime by _TrackedConfig. This is the half of the audit that
# cannot be faked: CONFIG_PARAMS records what the engine CLAIMS to read, and
# this records what it actually touched.
CONFIG_READS: set[str] = set()
CONFIG_MISSES: set[str] = set()


class _TrackedConfig(dict):
    """A config dict that records the dotted path of every key read from it.

    A declaration is a claim; this is the evidence. Every access — including a
    .get() for a key that is absent, which is how a hardcoded default silently
    overrides a parameter nobody noticed was missing — lands in CONFIG_READS or
    CONFIG_MISSES, and tools/config_audit.py holds the two against each other.
    """

    def __init__(self, data: dict, path: str = ""):
        super().__init__(data)
        self._path = path

    def _resolve(self, key, value):
        path = f"{self._path}.{key}" if self._path else str(key)
        CONFIG_READS.add(path)
        return _TrackedConfig(value, path) if isinstance(value, dict) else value

    def __getitem__(self, key):
        return self._resolve(key, super().__getitem__(key))

    def get(self, key, default=None):
        if key in self:
            return self._resolve(key, super().__getitem__(key))
        CONFIG_MISSES.add(f"{self._path}.{key}" if self._path else str(key))
        return default

    # Plain dicts on the way out: nothing downstream should inherit tracking, and
    # a copy must not need the (data, path) constructor.
    def __copy__(self):
        return dict(self)

    def __deepcopy__(self, memo):
        import copy as _copy
        return {k: _copy.deepcopy(v, memo) for k, v in self.items()}


def unread_engine_params() -> list[str]:
    """Parameters claimed as engine-read that this process never touched."""
    return sorted(p for p, (consumer, _) in CONFIG_PARAMS.items()
                  if consumer == "engine" and not p.endswith(".*")
                  and p not in CONFIG_READS)


# ──────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────

# Every field name the engine reads out of data/companies.json. Any field in the
# data outside this set is a typo or an orphan; any name the engine reads that
# isn't here would silently return None. Validated at load (see load_data) so a
# misspelling fails loudly instead of degrading a score to zero — the exact
# failure mode that let a renamed reserve_price field silently read as absent.
#
# ELIGIBLE_CATEGORY_FIELDS maps each ledger tranche to its own Gate 1 share.
# Absent, the blended eligible_ounce_share stands in — see eligible_shares() and
# ounce_ledger property 4. The mapping is keyed by the ounce field so that
# statement_currency() can iterate the same three tranches.
ELIGIBLE_CATEGORY_FIELDS = {
    "pp_moz": "eligible_pp_share",
    "mi_non_reserve_moz": "eligible_mi_share",
    "inferred_moz": "eligible_inferred_share",
}

# How far the confidence-weighted blend of the category shares may sit from the
# stored eligible_ounce_share before it is reported. 0.5% clears the 2dp rounding
# in the two stored blends (0.15% and 0.07%) and nothing else.
ELIGIBILITY_RECONCILE_TOLERANCE = 0.005

KNOWN_FIELDS = {
    "pp_moz", "mr_total_moz", "mi_non_reserve_moz", "inferred_moz",
    "reserve_price_aud", "resource_price_aud",
    "eligible_ounce_share", *ELIGIBLE_CATEGORY_FIELDS.values(),
    "ineligible_nav_share", "gold_nav_share",
    "aisc_aud_oz", "hedge_share_fwd24m", "net_debt_aud_m", "shares_out_m",
    # Gate 2 (§3) inputs
    "production_koz_yr", "undrawn_facilities_aud_m", "committed_capex_aud_m",
    "study_stage", "approvals_land_secured",
    # Economic capital is deliberately separate from financing capacity.  It
    # reaches near-producer and developer denominators; producer records are
    # retained for reporting only.  Funding reaches developer Gate 2 only.
    # residual_funding_gap_aud_m is derived and is not a data field.
    "remaining_execution_capex_aud_m", "available_project_funding_aud_m",
    # §4.3 capacity (reported) and §8.1 single-asset concentration.
    #
    # `largest_asset_pp_share` is a float in [0, 1]: the share of the company's
    # attributable, Gate-1-ELIGIBLE Proven & Probable Ore Reserves held at its
    # single largest asset. §8.1 defines the asset unit. The engine DERIVES the
    # single_asset boolean from it against a declared threshold — see
    # derive_single_asset() — rather than reading a hand-set flag, because
    # seventeen hand-set booleans are seventeen unrecorded judgement calls and
    # one threshold over seventeen sourced shares is one recorded judgement call
    # that config_audit, sensitivity and the committee can all argue with.
    #
    # It supersedes a hand-set `single_asset` boolean, which in turn superseded
    # `single_asset_shares`, a {asset: share} map that was unsourced for all
    # seventeen names and fed a 20% cap that could not bind.
    "advt_shares_m", "largest_asset_pp_share",
}

CAPITAL_EVIDENCE_STATES = {
    "POINT", "UPPER_BOUND", "LOWER_BOUND", "CARRY_FORWARD", "UNRESOLVED",
}
EXECUTION_CAPITAL_FIELD = "remaining_execution_capex_aud_m"
PROJECT_FUNDING_FIELD = "available_project_funding_aud_m"
EXECUTION_CAPITAL_PROJECTS_KEY = "execution_capital_projects"
GATE2_CAPITAL_PROJECT_KEYS = {
    "project_id", "scope", "as_of", "gate2_horizon_start", "gate2_horizon_end",
    "committed_within_gate2_horizon_aud_m", "committed_capex_range_aud_m",
    "committed_capex_state", "committed_capex_doc", "coverage_start",
    "coverage_end", "coverage_doc", "coverage_note",
    EXECUTION_CAPITAL_FIELD, "execution_capital_range_aud_m",
    "execution_capital_state", "execution_capital_doc",
}


def _directional_interval(value: object, state: object,
                          disclosed_range: object = None
                          ) -> tuple[float, float] | None:
    """Turn one directional capital record into a closed/non-negative interval.

    A published range refines the amount before direction is applied.  It never
    changes the direction: a one-year A$350–470m guide is still only a lower
    bound on a two-year window, so its interval is [350, +inf), not [350, 470].
    """
    if state not in CAPITAL_EVIDENCE_STATES:
        return None
    if state == "UNRESOLVED":
        return 0.0, math.inf
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    value = float(value)
    if not math.isfinite(value) or value < 0:
        return None
    lo = hi = value
    if disclosed_range is not None:
        if (not isinstance(disclosed_range, (list, tuple))
                or len(disclosed_range) != 2):
            return None
        lo, hi = disclosed_range
        if (not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                    for v in (lo, hi))
                or not all(math.isfinite(float(v)) for v in (lo, hi))
                or float(lo) < 0 or float(lo) > float(hi)
                or not float(lo) <= value <= float(hi)):
            return None
        lo, hi = float(lo), float(hi)
    if state in ("POINT", "CARRY_FORWARD"):
        return lo, hi
    if state == "UPPER_BOUND":
        return 0.0, hi
    if state == "LOWER_BOUND":
        return lo, math.inf
    return 0.0, math.inf


def _iso_date(raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _flatten(record: dict) -> dict:
    """Collapse the per-field provenance schema of data/companies.json into the
    plain value dict the engine works with, keeping the ticker-level metadata.

    Input shape:  {"fields": {"pp_moz": {"v": 28.4, "doc": "rr2026"}, ...}}
    Output shape: {"pp_moz": 28.4, ...}

    Provenance is preserved separately on `_docs` so the build output can cite
    where any number came from. An omitted field stays omitted — the schema
    forbids guessed values, so absence here means genuinely unsourced.

    Optional sub-keys travel with the value and are flattened alongside it,
    because a gate has to be able to read them (§3.2):

      `range`          [lo, hi] — the span the ISSUER published, where `v` is
                       its midpoint. Flattened to `<field>_range`.
      `horizon_years`, `annual_leg_aud_m`
                       legacy issue-3 basis retained in build fixtures. Live
                       Gate 2 capital coverage now comes from the explicit
                       per-project intervals in `execution_capital_projects`.
      `evidence_state` directional classification used by capital validation.
      `as_of`           measurement date for an amount, including carry-forward.
      `cost_base_date`, `accuracy_range`, `contingency_included`
                       estimate-quality facts retained for capital reporting.

    These are transcriptions of what a cited document already states. Neither
    may be inferred. The legacy horizon keys remain available to regression
    tooling, but only the dated project records decide live Gate 2 coverage.
    """
    flat = {k: v for k, v in record.items() if k not in ("fields", "documents")}
    flat["_docs"] = record.get("documents", {})
    flat["_field_specs"] = record.get("fields", {})
    flat["_field_docs"] = {}
    for name, spec in record.get("fields", {}).items():
        flat[name] = spec.get("v")
        if spec.get("range") is not None:
            flat[f"{name}_range"] = tuple(spec["range"])
        if spec.get("horizon_years") is not None:
            flat[f"{name}_horizon_years"] = spec["horizon_years"]
        if spec.get("annual_leg_aud_m") is not None:
            flat[f"{name}_annual_leg_aud_m"] = spec["annual_leg_aud_m"]
        if spec.get("term_date") is not None:
            flat[f"{name}_term_date"] = spec["term_date"]
        for key in ("evidence_state", "as_of", "cost_base_date",
                    "accuracy_range", "contingency_included"):
            if key in spec:
                flat[f"{name}_{key}"] = spec[key]
        flat["_field_docs"][name] = {"doc": spec.get("doc"), "note": spec.get("note")}
    return flat


def _validate_capital_schema(record: dict) -> list[str]:
    """Validate directional capital evidence before it can reach a formula.

    Near-producers and developers require denominator-safe execution-capital
    evidence.  Producer execution capital is optional reporting data, but when
    supplied it is still validated.  Every producer-health path also requires
    project records for Gate 2 commitments and their coverage dates.
    """
    errors: list[str] = []
    fields = record.get("fields", {})
    ticker = record.get("ticker", "?")

    if "remaining_capex_aud_m" in fields:
        errors.append("remaining_capex_aud_m is retired; split economic capital "
                      "from available project funding")
    if "residual_funding_gap_aud_m" in fields:
        errors.append("residual_funding_gap_aud_m is engine-derived and may not "
                      "be stored")
    sleeve = record.get("sleeve")
    execution_required = sleeve in {"developer", "near_producer"}
    if execution_required and EXECUTION_CAPITAL_FIELD not in fields:
        errors.append(f"{EXECUTION_CAPITAL_FIELD} missing for {sleeve}")
    if record.get("sleeve") == "developer" and PROJECT_FUNDING_FIELD not in fields:
        errors.append(f"{PROJECT_FUNDING_FIELD} missing for developer")

    for name, spec in fields.items():
        if not isinstance(spec, dict):
            continue
        state = spec.get("evidence_state")
        if name in (EXECUTION_CAPITAL_FIELD, PROJECT_FUNDING_FIELD) and state is None:
            errors.append(f"{name} has no evidence_state")
            continue
        if state is None:
            continue
        if state not in CAPITAL_EVIDENCE_STATES:
            errors.append(f"{name} has invalid evidence_state {state!r}")
            continue
        value = spec.get("v")
        if state == "UNRESOLVED":
            if value is not None:
                errors.append(f"{name} is UNRESOLVED but carries value {value!r}")
        elif not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{name} state {state} requires a numeric value")
        elif not math.isfinite(float(value)) or value < 0:
            errors.append(f"{name} must be a finite non-negative amount")
        doc = spec.get("doc")
        if not doc or doc not in record.get("documents", {}):
            errors.append(f"{name} evidence_state {state} has no valid document")

    if sleeve != "developer":
        projects = record.get(EXECUTION_CAPITAL_PROJECTS_KEY)
        if not isinstance(projects, list) or not projects:
            errors.append(f"{EXECUTION_CAPITAL_PROJECTS_KEY} missing or empty")
        else:
            errors.extend(_validate_execution_capital_projects(
                record, projects, require_execution_capital=execution_required))

    return [f"{ticker}: {error}" for error in errors]


def _validate_execution_capital_projects(record: dict,
                                     projects: list[object],
                                     require_execution_capital: bool = True
                                     ) -> list[str]:
    """Validate and reconcile the per-project issue-4 capital bridge."""
    errors: list[str] = []
    documents = record.get("documents", {})
    fields = record.get("fields", {})
    seen: set[str] = set()
    horizon: tuple[date, date] | None = None
    common_as_of: date | None = None
    committed_values: list[float] = []
    committed_range_lows: list[float] = []
    committed_range_highs: list[float] = []
    execution_values: list[float] = []
    execution_lower = 0.0
    execution_upper = 0.0
    any_committed_unresolved = False
    any_execution_unresolved = False

    for index, project in enumerate(projects):
        label = f"{EXECUTION_CAPITAL_PROJECTS_KEY}[{index}]"
        if not isinstance(project, dict):
            errors.append(f"{label} is not an object")
            continue
        project_id = project.get("project_id")
        if not isinstance(project_id, str) or not project_id.strip():
            errors.append(f"{label} has no id")
            project_id = label
        elif project_id in seen:
            errors.append(f"{label} duplicates id {project_id!r}")
        seen.add(project_id)
        stray = set(project) - GATE2_CAPITAL_PROJECT_KEYS
        if stray:
            errors.append(f"{project_id}: unknown keys {sorted(stray)}")
        if not isinstance(project.get("scope"), str) or not project["scope"].strip():
            errors.append(f"{project_id}: scope missing")
        project_as_of = _iso_date(project.get("as_of"))
        if project_as_of is None:
            errors.append(f"{project_id}: invalid or missing as_of date")
        elif common_as_of is None:
            common_as_of = project_as_of
        elif project_as_of != common_as_of:
            errors.append(f"{project_id}: project records do not share one as_of date")

        h_start = _iso_date(project.get("gate2_horizon_start"))
        h_end = _iso_date(project.get("gate2_horizon_end"))
        if h_start is None or h_end is None or h_start > h_end:
            errors.append(f"{project_id}: invalid Gate 2 horizon dates")
        else:
            current = (h_start, h_end)
            if horizon is None:
                horizon = current
            elif horizon != current:
                errors.append(f"{project_id}: project horizons do not match")

        c_start = _iso_date(project.get("coverage_start"))
        c_end = _iso_date(project.get("coverage_end"))
        coverage_present = c_start is not None and c_end is not None
        if ((project.get("coverage_start") is None)
                != (project.get("coverage_end") is None)):
            errors.append(f"{project_id}: coverage_start and coverage_end must travel together")
        elif coverage_present and c_start > c_end:
            errors.append(f"{project_id}: coverage_start is after coverage_end")
        if not isinstance(project.get("coverage_note"), str):
            errors.append(f"{project_id}: coverage_note missing")

        committed_state = project.get("committed_capex_state")
        committed_value = project.get("committed_within_gate2_horizon_aud_m")
        committed_range = project.get("committed_capex_range_aud_m")
        committed_interval = _directional_interval(
            committed_value, committed_state, committed_range)
        if committed_interval is None:
            errors.append(f"{project_id}: invalid committed-capex amount/state/range")
        if committed_state == "UNRESOLVED":
            any_committed_unresolved = True
            if committed_value is not None:
                errors.append(f"{project_id}: UNRESOLVED committed capex carries a value")
            if coverage_present:
                errors.append(f"{project_id}: UNRESOLVED committed capex claims coverage dates")
        else:
            if isinstance(committed_value, (int, float)) and not isinstance(committed_value, bool):
                committed_values.append(float(committed_value))
                if isinstance(committed_range, list) and len(committed_range) == 2:
                    committed_range_lows.append(float(committed_range[0]))
                    committed_range_highs.append(float(committed_range[1]))
                else:
                    committed_range_lows.append(float(committed_value))
                    committed_range_highs.append(float(committed_value))
            if not coverage_present:
                errors.append(f"{project_id}: resolved committed capex has no coverage dates")

        committed_doc = project.get("committed_capex_doc")
        coverage_doc = project.get("coverage_doc")
        for key, doc in (("committed_capex_doc", committed_doc),
                         ("coverage_doc", coverage_doc)):
            if doc not in documents:
                errors.append(f"{project_id}: {key} is not a valid document key")

        if (h_start is not None and h_end is not None and coverage_present
                and committed_state != "UNRESOLVED"):
            under = c_start > h_start or c_end < h_end
            over = c_start < h_start or c_end > h_end
            if under and over:
                errors.append(f"{project_id}: coverage both omits and exceeds the horizon; "
                              "the amount must be decomposed or UNRESOLVED")
            elif under and committed_state != "LOWER_BOUND":
                errors.append(f"{project_id}: under-coverage requires LOWER_BOUND")
            elif over and committed_state != "UPPER_BOUND":
                errors.append(f"{project_id}: over-coverage requires UPPER_BOUND")

        execution_present = any(key in project for key in (
            EXECUTION_CAPITAL_FIELD, "execution_capital_range_aud_m",
            "execution_capital_state", "execution_capital_doc"))
        if require_execution_capital or execution_present:
            execution_state = project.get("execution_capital_state")
            execution_value = project.get(EXECUTION_CAPITAL_FIELD)
            execution_range = project.get("execution_capital_range_aud_m")
            execution_interval = _directional_interval(
                execution_value, execution_state, execution_range)
            if execution_interval is None:
                errors.append(f"{project_id}: invalid execution-capital amount/state/range")
            else:
                execution_lower += execution_interval[0]
                execution_upper = (execution_upper + execution_interval[1]
                                   if math.isfinite(execution_upper)
                                   and math.isfinite(execution_interval[1])
                                   else math.inf)
            if execution_state == "UNRESOLVED":
                any_execution_unresolved = True
                if execution_value is not None:
                    errors.append(f"{project_id}: UNRESOLVED execution capital carries a value")
            elif isinstance(execution_value, (int, float)) and not isinstance(execution_value, bool):
                execution_values.append(float(execution_value))
            if project.get("execution_capital_doc") not in documents:
                errors.append(f"{project_id}: execution_capital_doc is not a valid document key")

    committed = fields.get("committed_capex_aud_m") or {}
    committed_value = committed.get("v") if isinstance(committed, dict) else None
    if any_committed_unresolved:
        if committed_value is not None:
            errors.append("aggregate committed_capex_aud_m carries a value while a project is UNRESOLVED")
    elif not isinstance(committed_value, (int, float)) or isinstance(committed_value, bool):
        errors.append("aggregate committed_capex_aud_m missing despite resolved projects")
    elif not math.isclose(float(committed_value), sum(committed_values), abs_tol=1e-6):
        errors.append("project committed capex does not reconcile to committed_capex_aud_m")
    elif isinstance(committed.get("range"), list):
        aggregate_range = committed["range"]
        if (len(aggregate_range) != 2
                or not math.isclose(float(aggregate_range[0]),
                                    sum(committed_range_lows), abs_tol=1e-6)
                or not math.isclose(float(aggregate_range[1]),
                                    sum(committed_range_highs), abs_tol=1e-6)):
            errors.append("project committed ranges do not reconcile to committed_capex_aud_m")

    execution = fields.get(EXECUTION_CAPITAL_FIELD)
    if require_execution_capital or execution is not None:
        execution = execution or {}
        execution_value = execution.get("v") if isinstance(execution, dict) else None
        if any_execution_unresolved:
            if execution_value is not None:
                errors.append(f"aggregate {EXECUTION_CAPITAL_FIELD} carries a value while a project is UNRESOLVED")
        elif not isinstance(execution_value, (int, float)) or isinstance(execution_value, bool):
            errors.append(f"aggregate {EXECUTION_CAPITAL_FIELD} missing despite resolved projects")
        elif not math.isclose(float(execution_value), sum(execution_values), abs_tol=1e-6):
            errors.append(f"project execution capital does not reconcile to {EXECUTION_CAPITAL_FIELD}")
        aggregate_execution_interval = _directional_interval(
            execution.get("v"), execution.get("evidence_state"),
            execution.get("accuracy_range"))
        if aggregate_execution_interval is not None:
            agg_lo, agg_hi = aggregate_execution_interval
            same_upper = ((math.isinf(agg_hi) and math.isinf(execution_upper))
                          or math.isclose(agg_hi, execution_upper, abs_tol=1e-6))
            if (not math.isclose(agg_lo, execution_lower, abs_tol=1e-6)
                    or not same_upper):
                errors.append(f"project execution-capital interval does not reconcile to {EXECUTION_CAPITAL_FIELD}")
    return errors


def reconcile_resource(c: dict) -> str | None:
    """Does the disclosed category split add back to the disclosed total?

    P&P + M&I non-reserve + Inferred should equal total Mineral Resources, since
    JORC reports reserves as a subset of resources and this data layer stores the
    non-reserve remainder. A mismatch means a category was read off the wrong
    table, or one of the four numbers is a different vintage from the others —
    the period-basis defect class, applied to ounces instead of to
    production.

    Reported, never corrected. This function used to be `impute_resource_split`,
    which INVENTED the split from a cohort ratio when it was not disclosed; that
    rule was disabled under DERIVE OR FAIL and is now deleted outright. The same
    three numbers are now used the other way round — to check the ledger rather
    than to fill it.
    """
    mr, pp = c.get("mr_total_moz"), c.get("pp_moz")
    mi, inf = c.get("mi_non_reserve_moz"), c.get("inferred_moz")
    if mr is None or pp is None or mi is None:
        return None
    built = pp + mi + (inf or 0.0)
    if mr <= 0:
        return None
    gap = (built - mr) / mr
    if abs(gap) <= 0.02:
        return None
    return (f"ledger {built:.2f} Moz vs disclosed MR {mr:.2f} Moz "
            f"({gap:+.1%}) — check the category vintages")


def reconcile_eligibility(c: dict) -> str | None:
    """Do the per-category Gate 1 shares reproduce the blended one?

    eligible_ounce_share is defined as ineligible confidence-weighted ounces over
    group confidence-weighted ounces, so it is an identity: the confidence-
    weighted blend of the three category shares MUST equal it. That makes the two
    representations a check on each other, in the same spirit as
    reconcile_resource — one derived number verifying another rather than filling
    it in.

    Reported, never corrected. Where they disagree the category shares win,
    because they are read off exact per-category ounce counts while the blend is
    stored rounded; the two names that disagree today do so by 0.15% and 0.07%
    for exactly that reason. A gap materially larger than rounding means one of
    the four numbers was read off the wrong row.
    """
    blend = c.get("eligible_ounce_share")
    pp, mi = c.get("pp_moz"), c.get("mi_non_reserve_moz")
    inf = c.get("inferred_moz") or 0.0
    if blend is None or pp is None or mi is None:
        return None
    shares = [c.get(f) for f in ELIGIBLE_CATEGORY_FIELDS.values()]
    if any(s is None for s in shares):
        return None
    s_pp, s_mi, s_inf = shares
    cw_total = pp + 0.5 * mi + 0.2 * inf
    if cw_total <= 0:
        return None
    implied = (pp * s_pp + 0.5 * mi * s_mi + 0.2 * inf * s_inf) / cw_total
    gap = implied - blend
    if abs(gap) <= ELIGIBILITY_RECONCILE_TOLERANCE:
        return None
    return (f"category Gate 1 shares imply a blended {implied:.4f} vs the stored "
            f"eligible_ounce_share {blend:.4f} ({gap:+.2%}) — one of the "
            f"per-category ineligible ounce counts does not match the group figure")


def load_data() -> tuple[dict, list[dict], list[dict], dict, list[str]]:
    """Read the data layer. Returns (config, companies, excluded, market, notes).

    The config comes back wrapped in _TrackedConfig so that every parameter the
    build touches is recorded. See CONFIG_PARAMS for why.
    """
    cfg = _TrackedConfig(json.loads((DATA_DIR / "config.json").read_text()))

    # An unclaimed parameter is the defect this registry exists to stop, and it
    # is cheapest to catch at load: config.json is edited far more often than
    # the engine, and a new key added there with no consumer looks exactly like
    # a live constraint to anyone reading the file.
    unclaimed = [p for p in config_leaves(cfg) if claimed_by(p) is None]
    if unclaimed:
        raise ValueError(
            f"data/config.json declares parameters no consumer claims: "
            f"{', '.join(unclaimed)}. Add each to CONFIG_PARAMS with a consumer "
            f"(engine / conditional / tools/x.py / process / evidence), or if it "
            f"is rationale rather than a parameter, rename it to end in _note.")

    payload = json.loads((DATA_DIR / "companies.json").read_text())
    delivery = json.loads((DATA_DIR / "guidance_delivery.json").read_text())
    delivery_ratings = delivery.get("ratings", {})
    market = json.loads((DATA_DIR / "market.json").read_text())

    # §6.4 measures a resource statement's age against the date the LEDGER was
    # sourced, and the ledger is companies.json. Two files carry a `_sourced`
    # date and they are allowed to differ — market.json records when the
    # offline price fallbacks were taken, which has nothing to do with when a
    # reserve statement was read. The gate used to read market.json's, and on
    # 20 Aug 2026 that ejected Westgold at ~13% of the book: its FY26 group
    # statement is dated the 20th and the market file still said the 17th, so
    # the document looked like it came from the future. Note the direction the
    # old coupling erred in when the two merely disagreed rather than crossed —
    # an earlier as_of makes every document look YOUNGER, which is the lenient
    # side of a staleness bar.
    market["_ledger_sourced"] = payload.get("_sourced") or market["_sourced"]

    companies, notes = [], []
    unknown: dict[str, set[str]] = {}
    capital_schema_errors: list[str] = []
    for record in payload["companies"]:
        stray = set(record.get("fields", {})) - KNOWN_FIELDS
        if stray:
            unknown[record["ticker"]] = stray
        capital_schema_errors.extend(_validate_capital_schema(record))
        c = _flatten(record)
        c["_guidance_delivery"] = delivery_ratings.get(c["ticker"])
        c["_data_sourced"] = payload.get("_sourced")
        for check in (reconcile_resource, reconcile_eligibility):
            mismatch = check(c)
            if mismatch:
                notes.append(f"{c['ticker']}: {mismatch}")
        companies.append(c)

    if unknown:
        detail = "; ".join(f"{t}: {sorted(f)}" for t, f in unknown.items())
        raise ValueError(
            f"data/companies.json contains field names the engine does not read — "
            f"these would be silently ignored: {detail}. "
            f"Add them to KNOWN_FIELDS or fix the spelling.")

    if capital_schema_errors:
        raise ValueError("invalid capital evidence schema: "
                         + "; ".join(capital_schema_errors))

    unrated = [c["ticker"] for c in companies
               if c.get("sleeve") in {"producer", "near_producer"}
               and c.get("_guidance_delivery") is None]
    if unrated:
        raise ValueError("producer guidance-delivery rating absent: "
                         + ", ".join(sorted(unrated)))

    return cfg, companies, payload.get("excluded", []), market, notes


# ──────────────────────────────────────────────────────────────────────────
# IBKR
# ──────────────────────────────────────────────────────────────────────────

def engine_commit() -> str | None:
    """The commit the build ran from, with a dirty flag if the tree was edited.

    tools/snapshot.py records this too, but it records it when the SNAPSHOT is
    taken. That is a different instant, and on any workflow where the build runs
    first and the snapshot lands after an edit, it is a different commit — which
    would pin the wrong engine to the numbers. Stamp it in the session, where the
    market data was actually read.
    """
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                             capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=HERE,
                               capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return None
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")
    except Exception:
        return None


def short_commit(commit: str | None) -> str:
    """Twelve characters of sha, and the dirty flag intact.

    Slicing the raw string would drop the "-dirty" suffix, which is the part
    that says the build does not correspond to any commit anyone else can check
    out. Same rule as tools/snapshot.py.
    """
    if not commit:
        return "—"
    sha, _, flag = commit.partition("-")
    return sha[:12] + (f"-{flag}" if flag else "")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contract_raw(contract) -> dict:
    """Contract identity as IBKR resolved it, not as we asked for it."""
    out = {}
    for f in CONTRACT_FIELDS:
        v = getattr(contract, f, None)
        out[f] = None if v in ("", 0) else v
    return out


def _ticker_raw(tk) -> dict:
    """One quote, verbatim, with NaN normalised to null.

    ib_insync carries "no value" as float('nan'), which json.dumps happily
    writes as the bare token NaN — not valid JSON, and it would make the frozen
    bundle unreadable by anything stricter than Python. Every numeric field
    therefore goes through _f().
    """
    out: dict = {}
    for f in TICKER_FIELDS:
        v = getattr(tk, f, None)
        out[f] = v if isinstance(v, (bool, str)) or v is None else _f(v)
    out["marketDataTypeLabel"] = MARKET_DATA_TYPE_LABELS.get(
        out.get("marketDataType"), str(out.get("marketDataType")))
    # Derived by ib_insync from the fields above, not sent by TWS. Recorded
    # because _first_price and the price ladder in fetch_market_data read them,
    # so a bundle without them cannot reproduce which field won.
    out["_derived"] = {"marketPrice": _f(tk.marketPrice()),
                       "midpoint": _f(tk.midpoint())}
    out["time_utc"] = tk.time.isoformat() if getattr(tk, "time", None) else None
    return out


class IBRecorder:
    """Everything the TWS session was asked, and everything it answered.

    WHY THIS EXISTS
    ---------------
    Every other input to a weight carries the document it was read from —
    data/companies.json will not accept a value without one, and tools/
    provenance.py grades the documents. The market leg carried nothing. A build
    printed a price and a spread and a beta, and the only record of where they
    came from was the number itself: not the contract IBKR resolved, not the
    window requested, not whether the quote was live, frozen or delayed, not
    what the account was entitled to at that minute, and not the bars the
    regression consumed. Re-running the build a day later gives different
    numbers and no way to tell which part moved.

    So the session logs itself. The log is not a debugging aid — it is the
    source document for the one class of input that could not otherwise have
    one, and it is frozen into the snapshot alongside the data layer and the
    parameters.

    WHAT IS RECORDED
    ----------------
        session    host/port/client id, TWS server version and clock, the
                   requested market-data type, the engine commit
        requests   every API call in order, with its parameters and the UTC
                   instants either side of it
        contracts  what was asked for and what conId came back
        quotes     each ticker's raw fields, and the market-data type that
                   ticker actually returned
        errors     everything TWS said on the error channel, including the
                   informational messages — a subscription refusal arrives here
                   and nowhere else, and without it a quote of -1.0 looks like
                   a price rather than a rejection
        prices     which field each name's price was finally taken from
        bars       every bar of every historical series, unaggregated

    Nothing here is derived, and nothing here is corrected. A failed request is
    recorded as a failed request; that is the point.

    ONE CAVEAT ON marketDataType. The value recorded per quote is ib_insync's
    Ticker.marketDataType, which is initialised to 1 ("live") and overwritten
    only if TWS sends a market-data-type message for that request. A session
    where TWS sends nothing therefore records "live" by default rather than by
    observation. Read it against `errors` and against `prices`: a ticker
    reporting "live" with -1.0 quotes, a subscription error and a price resolved
    from histDailyClose was not a live quote, and the bundle carries all four
    facts so the reader is not required to trust the first one.
    """

    def __init__(self, host: str, port: int, client_id: int):
        self.session: dict = {
            "host": host, "port": port, "client_id": client_id, "readonly": True,
            "market_data_type_requested": MARKET_DATA_TYPE_REQUESTED,
            "market_data_type_requested_label":
                MARKET_DATA_TYPE_LABELS.get(MARKET_DATA_TYPE_REQUESTED),
            "engine_commit": engine_commit(),
            "started_utc": _utc(),
        }
        self.requests: list[dict] = []
        self.contracts: dict[str, dict] = {}
        self.quotes: dict[str, dict] = {}
        self.errors: list[dict] = []
        self.prices: dict[str, dict] = {}
        self.series: dict[str, dict] = {}
        self.bar_rows: list[list] = []

    @contextlib.contextmanager
    def call(self, name: str, **params):
        """Log one API call around its own execution.

        The caller sets entry["result"]. An exception is recorded and re-raised:
        the callers below swallow IBKR failures by design (a missing FX leg
        degrades to a fallback rather than killing the build), and a swallowed
        failure that left no trace is how a bundle would come to look complete
        while a series was silently empty.
        """
        entry = {"seq": len(self.requests) + 1, "call": name, "params": params,
                 "sent_utc": _utc()}
        self.requests.append(entry)
        try:
            yield entry
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            entry["received_utc"] = _utc()

    def contract(self, requested: dict, qualified) -> dict:
        rec = {"requested": requested, "qualified": _contract_raw(qualified)}
        self.contracts[str(rec["qualified"]["conId"] or requested.get("symbol"))] = rec
        return rec

    def quote(self, tk) -> None:
        self.quotes[str(getattr(tk.contract, "conId", None))] = {
            "contract": _contract_raw(tk.contract), "ticker": _ticker_raw(tk)}

    def error(self, req_id, code, message, contract) -> None:
        """One message off the TWS error channel.

        IBKR sends status notices down the same channel as failures — 2104
        "market data farm connection is OK" is not an error and 354 "requested
        market data is not subscribed" is. Both are kept: the farm notices state
        which data farms were up at the moment the build read prices, which is
        part of what the session was, and filtering to "real" errors would mean
        this file deciding which of TWS's statements about itself to preserve.
        """
        self.errors.append({
            "utc": _utc(), "req_id": req_id, "code": code, "message": message,
            "con_id": getattr(contract, "conId", None) or None,
            "symbol": getattr(contract, "symbol", None) or None,
        })

    def price(self, symbol: str, resolved: dict) -> None:
        """Which field the engine's price ladder finally settled on.

        `field` is the whole point. A price taken from `last` and a price taken
        from `histDailyClose` are the same number type and completely different
        claims — the first is a quote, the second is yesterday's (or today's)
        session close standing in for one — and only this line separates them.
        """
        self.prices[symbol] = resolved

    def bars(self, key: str, meta: dict, bars) -> None:
        """Store a historical series verbatim.

        Bars go to market_bars.csv rather than into the JSON: 11 names over two
        years of daily TRADES, three months of BID_ASK and five years of gold
        and AUDUSD is roughly nine thousand rows, and nine thousand indented
        JSON objects is a file nobody opens. The JSON keeps the index — request
        parameters, count, first and last date — and the CSV keeps the numbers.
        """
        self.series[key] = {**meta, "n_bars": len(bars),
                            "first": str(bars[0].date) if bars else None,
                            "last": str(bars[-1].date) if bars else None}
        for b in bars:
            self.bar_rows.append([
                key, str(b.date), _f(b.open), _f(b.high), _f(b.low), _f(b.close),
                _f(b.volume), _f(getattr(b, "average", None)),
                getattr(b, "barCount", None),
            ])

    def bundle(self) -> dict:
        self.session["finished_utc"] = _utc()
        return {
            "_schema": "Raw IBKR/TWS session for one build: request parameters, "
                       "contract identifiers, quote fields, market-data type and "
                       "the index of every historical series. Bars themselves are "
                       "in market_bars.csv, keyed on `series`. Written by "
                       "build_index.py; frozen by tools/snapshot.py.",
            "session": self.session,
            "requests": self.requests,
            "errors": self.errors,
            "contracts": self.contracts,
            "quotes": self.quotes,
            "prices": self.prices,
            "series": self.series,
        }


class NullRecorder(IBRecorder):
    """Records nothing, for callers that are not producing a frozen build.

    tools/asymmetry.py and tools/sensitivity.py open their own sessions to
    answer a diagnostic question; they are not the index and their reads are not
    an index input, so they should not silently overwrite the build's bundle.
    Skipping the git call in __init__ also keeps _history usable with no
    repository at all.
    """

    def __init__(self):
        self.session, self.requests = {}, []
        self.contracts, self.quotes, self.series, self.bar_rows = {}, {}, {}, []


def _series_key(contract, what: str, duration: str) -> str:
    """Stable name for one historical series, unique within a session.

    Keyed on the local symbol rather than the conId so the CSV stays legible;
    the conId is one hop away in market_bundle.json → series → con_id, and a
    build that pulled two contracts with one local symbol would be a different
    problem entirely.
    """
    sym = getattr(contract, "localSymbol", None) or contract.symbol
    return f"{sym}:{what}:{duration.replace(' ', '')}"


def write_market_bundle(bundle: dict, bar_rows: list[list]) -> dict:
    """Write market_bundle.json + market_bars.csv; return the digest block.

    The digests go into weights.json so the output names the exact input that
    produced it. Two files can sit next to each other in a snapshot directory
    and still not belong together — someone re-runs a build, copies one file and
    not the other — and a sha256 is the only thing that catches it.
    """
    bars_path = HERE / "market_bars.csv"
    with bars_path.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(BAR_COLUMNS)
        wr.writerows(bar_rows)
    bars_sha = hashlib.sha256(bars_path.read_bytes()).hexdigest()

    bundle["bars_file"] = {"path": "market_bars.csv", "columns": list(BAR_COLUMNS),
                           "n_rows": len(bar_rows), "sha256": bars_sha}
    text = json.dumps(bundle, indent=2, default=str) + "\n"
    (HERE / "market_bundle.json").write_text(text)

    observed = sorted({q["ticker"]["marketDataTypeLabel"]
                       for q in bundle["quotes"].values()})
    fields: dict[str, int] = {}
    for p in bundle["prices"].values():
        k = p["field"] or "unresolved"
        fields[k] = fields.get(k, 0) + 1
    return {
        "bundle": "market_bundle.json",
        "bundle_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "bars": "market_bars.csv",
        "bars_sha256": bars_sha,
        "bars_rows": len(bar_rows),
        "engine_commit": bundle["session"]["engine_commit"],
        "session_started_utc": bundle["session"]["started_utc"],
        "session_finished_utc": bundle["session"]["finished_utc"],
        "market_data_type_requested":
            bundle["session"]["market_data_type_requested_label"],
        "market_data_type_observed": observed,
        # Where the prices in this build actually came from. Kept next to the
        # market-data type because the two together are the honest statement and
        # either alone is not: "live" over a set of histDailyClose fields means
        # the quote channel returned nothing and the closes carried the build.
        "price_fields": dict(sorted(fields.items())),
        "n_requests": len(bundle["requests"]),
        "n_contracts": len(bundle["contracts"]),
        "n_series": len(bundle["series"]),
        "n_errors": len(bundle["errors"]),
        "error_codes": sorted({e["code"] for e in bundle["errors"]}),
    }


def _gold_and_fx(ib, rec: IBRecorder) -> dict:
    """Spot gold in USD and the two FX legs we need.

    Gold in AUD drives the reserve-price gap and operating-leverage terms;
    EUR/AUD converts the fund's EUR base into the AUD sizing currency.
    """
    from ib_insync import Contract, Forex

    out: dict[str, float | None | str] = {
        "xauusd": None, "audusd": None, "euraud": None, "source": "ibkr",
    }

    def _first_price(ticker) -> float | None:
        for cand in (ticker.marketPrice(), ticker.last, ticker.close,
                     ticker.midpoint(), ticker.bid, ticker.ask):
            v = _pos(cand)
            if v is not None:
                return v
        return None

    try:
        spec = {"secType": "CMDTY", "symbol": "XAUUSD",
                "exchange": "SMART", "currency": "USD"}
        gold = Contract(**spec)
        with rec.call("qualifyContracts", contracts=[spec]) as e:
            ib.qualifyContracts(gold)
            e["result"] = [_contract_raw(gold)]
        rec.contract(spec, gold)
        with rec.call("reqTickers", conIds=[gold.conId], symbols=["XAUUSD"]) as e:
            [tk] = ib.reqTickers(gold)
            rec.quote(tk)
            e["result"] = {"XAUUSD": _ticker_raw(tk)}
        out["xauusd"] = _first_price(tk)
    except Exception:
        pass

    for key, pair in (("audusd", "AUDUSD"), ("euraud", "EURAUD")):
        try:
            fx = Forex(pair)
            spec = {"secType": "CASH", "pair": pair, "exchange": "IDEALPRO"}
            with rec.call("qualifyContracts", contracts=[spec]) as e:
                ib.qualifyContracts(fx)
                e["result"] = [_contract_raw(fx)]
            rec.contract(spec, fx)
            with rec.call("reqTickers", conIds=[fx.conId], symbols=[pair]) as e:
                [tk] = ib.reqTickers(fx)
                rec.quote(tk)
                e["result"] = {pair: _ticker_raw(tk)}
            out[key] = _first_price(tk)
        except Exception:
            pass

    return out


# Share count used to be pulled here from IBKR's fundamental snapshot, on the
# reasoning that taking it from the same feed as the price made EV internally
# consistent, and that filings are an unreliable source for it — issuer sites
# publish Appendix 2A *incremental* issuances that read like totals, and third
# parties disagree badly (Ausgold quoted at 2.296bn by one aggregator against
# quoted market caps implying 450-650m; Astral at 1.80bn versus 1.45bn).
#
# That path is gone. TWS API 10.47 REMOVED reqFundamentalData, cancelFundamental-
# Data, the fundamentalData callback and tick type FUNDAMENTAL_RATIOS = 47 (the
# generic-258 route), with no successor. Verified 17 Aug 2026 against TWS server
# version 176: every report type and the 258 tick both return error 10358
# "Fundamentals data is not allowed", for AAPL exactly as for the ASX names. It
# is not an entitlement and no subscription restores it — the TWS UI still shows
# fundamentals because the UI does not use this API path.
#
# Share count therefore comes from data/companies.json only, which is arguably
# where it belonged: every other field in that file carries the document it was
# read from, and an IBKR-sourced count carried none.
#
#   https://www.ibkrguides.com/releasenotes/prod-2026.htm  ("De-Supported
#   Fundamentals Data Request", under 10.47)


def _history(ib, contract, what: str = "TRADES",
             duration: str | None = None,
             rec: IBRecorder | None = None) -> list[tuple[str, float]]:
    """(date, close) daily bars over `duration`. Historical-bar
    entitlements are usually broader than live-tick entitlements, so this often
    works where streaming data doesn't.

    Dates travel with the closes because the beta regression joins three
    calendars — ASX equities, the metals feed and IDEALPRO FX — and they do not
    share holidays. Pairing three ragged series by tail position silently
    regresses an ASX return on the wrong day's gold return, and that
    misalignment attenuates beta toward zero.

    whatToShow is TRADES for equities. FX and spot metals have no trade prints,
    so they need MIDPOINT; TRADES against them returns an empty series rather
    than an error, which would look like "no history" downstream. Both attempts
    are recorded, and the one the engine consumed is flagged `used` — a series
    silently sourced from the fallback is a different measurement, and the
    bundle should say so rather than leave it to be inferred from the numbers.
    """
    rec = rec or NullRecorder()
    duration = duration or HISTORY_DURATION_DEFAULT
    attempts = [what] if what == "MIDPOINT" else [what, "MIDPOINT"]
    for w in attempts:
        key = _series_key(contract, w, duration)
        params = {"con_id": getattr(contract, "conId", None),
                  "symbol": contract.symbol, "endDateTime": "",
                  "durationStr": duration, "barSizeSetting": "1 day",
                  "whatToShow": w, "useRTH": True, "formatDate": 1}
        try:
            with rec.call("reqHistoricalData", series=key, **params) as e:
                bars = ib.reqHistoricalData(
                    contract, endDateTime="", durationStr=duration,
                    barSizeSetting="1 day", whatToShow=w, useRTH=True,
                    formatDate=1,
                )
                e["result"] = {"n_bars": len(bars)}
        except Exception:
            continue
        series = [(str(b.date), float(b.close))
                  for b in bars if b.close and b.close > 0]
        rec.bars(key, {**params, "requested_what_to_show": what,
                       "used": bool(series)}, bars)
        if series:
            return series
    return []


def _spread_history(ib, contract, duration: str = SPREAD_DURATION_DEFAULT,
                    rec: IBRecorder | None = None) -> list[dict]:
    """Daily time-averaged quoted spread over regular trading hours.

    IBKR's BID_ASK daily bars do not carry prices in the usual sense: `open` is
    the time-weighted average BID across the session and `close` the
    time-weighted average ASK, while `high`/`low` are the session's max ask and
    min bid. So close − open is the average quoted spread during the day, which
    is exactly the §4 input, and high − low is an intraday range that must NOT
    be mistaken for one.

    Measured rather than snapped, because a snapshot is not a measurement here.
    Quotes taken outside continuous trading are wide and stale: on 17 Aug 2026
    the post-close book showed Westgold at 2.25% and Northern Star at 0.56%,
    against RTH-averaged figures of 0.172% and 0.043% — inflated by roughly an
    order of magnitude, enough to fail eight names on an artifact. useRTH=True
    confines this to continuous trading.
    """
    rec = rec or NullRecorder()
    key = _series_key(contract, "BID_ASK", duration)
    params = {"con_id": getattr(contract, "conId", None),
              "symbol": contract.symbol, "endDateTime": "",
              "durationStr": duration, "barSizeSetting": "1 day",
              "whatToShow": "BID_ASK", "useRTH": True, "formatDate": 1}
    try:
        with rec.call("reqHistoricalData", series=key, **params) as e:
            bars = ib.reqHistoricalData(
                contract, endDateTime="", durationStr=duration,
                barSizeSetting="1 day", whatToShow="BID_ASK", useRTH=True,
                formatDate=1,
            )
            e["result"] = {"n_bars": len(bars)}
    except Exception:
        return []
    rec.bars(key, {**params, "used": True,
                   "bid_ask_convention": "open = session time-weighted average "
                                         "bid, close = average ask"}, bars)
    out = []
    for b in bars:
        bid, ask = float(b.open), float(b.close)
        if bid > 0 and ask > 0 and ask >= bid:
            out.append({"date": str(b.date), "bid": bid, "ask": ask,
                        "spread_pct": (ask - bid) / ((ask + bid) / 2) * 100})
    return out


def spread_stats(series: list[dict]) -> dict | None:
    """Median and 90th-percentile daily quoted spread.

    The gate reads the MEDIAN: it is the cost of trading this name on a normal
    day, and it is robust to the occasional halted or disorderly session that
    would drag a mean. p90 is carried alongside as a diagnostic — a name whose
    median passes but whose p90 breaches is tradable in calm markets and not
    necessarily in the ones where a rebalance would actually be forced.
    """
    if len(series) < 10:
        return None
    vals = sorted(s["spread_pct"] for s in series)
    n = len(vals)
    return {
        "median_pct": vals[n // 2],
        "p90_pct": vals[min(n - 1, int(n * 0.9))],
        "max_pct": vals[-1],
        "n_days": n,
        "first": series[0]["date"], "last": series[-1]["date"],
    }


def _join(a: list[tuple[str, float]],
          b: list[tuple[str, float]]) -> list[tuple[str, float, float]]:
    """Inner join two dated series on date, preserving a's order."""
    bd = dict(b)
    return [(d, v, bd[d]) for d, v in a if d in bd]


def fetch_market_data(tickers: list[str], history_duration: str | None = None,
                      spread_duration: str | None = None) -> dict:
    """One IBKR session: spot prices, daily history, gold history, FX.

    The two windows are methodology parameters (risk.regression_window and
    gates.spread_window), not implementation details — the estimation window is
    what makes β_gold responsive or stable, and the spread window is what stops
    one disorderly session deciding a gate. They arrive from config; the
    defaults exist only for a caller that has not loaded it.

    The session records itself into `result["bundle"]` — see IBRecorder. Nothing
    downstream reads it; it exists so the market leg of the build carries a
    source document like every other input.
    """
    history_duration = history_duration or HISTORY_DURATION_DEFAULT
    spread_duration = spread_duration or SPREAD_DURATION_DEFAULT
    import ib_insync
    from ib_insync import IB, Contract, Forex, Stock, util

    util.logToConsole(logging.WARNING)
    ib = IB()
    rec = IBRecorder(HOST, PORT, CLIENT_ID)
    # Subscribed before connecting, so a refusal during the handshake is caught
    # too. This is the only channel on which TWS explains itself.
    ib.errorEvent += rec.error
    with rec.call("connect", host=HOST, port=PORT, clientId=CLIENT_ID,
                  readonly=True) as e:
        ib.connect(HOST, PORT, clientId=CLIENT_ID, readonly=True)
        e["result"] = {"server_version": ib.client.serverVersion()}

    result: dict = {"prices": {}, "history": {}, "spreads": {}, "gold_history": [],
                    "audusd_history": [], "fx": {}}

    try:
        # The TWS clock, not ours. A frozen build is timestamped by this machine,
        # and a machine whose clock has drifted would date the bundle wrongly
        # with nothing to check it against.
        with rec.call("reqCurrentTime") as e:
            server_now = ib.reqCurrentTime()
            e["result"] = {"server_time_utc": server_now.isoformat()}
        rec.session.update({
            "ib_insync_version": ib_insync.__version__,
            "tws_server_version": ib.client.serverVersion(),
            "tws_server_time_utc": server_now.isoformat(),
            "history_duration": history_duration,
            "spread_duration": spread_duration,
            "gold_history_duration": GOLD_HISTORY_DURATION,
            "tickers_requested": list(tickers),
        })

        with rec.call("reqMarketDataType",
                      marketDataType=MARKET_DATA_TYPE_REQUESTED,
                      label=MARKET_DATA_TYPE_LABELS[MARKET_DATA_TYPE_REQUESTED]):
            # Frozen realtime if subscribed, else delayed-frozen. What each
            # ticker actually came back as is recorded per quote, because the
            # request is not the answer.
            ib.reqMarketDataType(MARKET_DATA_TYPE_REQUESTED)

        specs = [{"secType": "STK", "symbol": t, "exchange": "ASX",
                  "currency": "AUD"} for t in tickers]
        contracts = [Stock(t, "ASX", "AUD") for t in tickers]
        with rec.call("qualifyContracts", contracts=specs) as e:
            ib.qualifyContracts(*contracts)
            e["result"] = [_contract_raw(c) for c in contracts]
        for spec, c in zip(specs, contracts):
            rec.contract(spec, c)

        with rec.call("reqTickers", conIds=[c.conId for c in contracts],
                      symbols=list(tickers)) as e:
            quotes = ib.reqTickers(*contracts)
            e["result"] = {"n_tickers": len(quotes)}
        for tk in quotes:
            rec.quote(tk)

        for tk in quotes:
            sym = tk.contract.symbol
            candidates = [
                ("marketPrice", _pos(tk.marketPrice())),
                ("last", _pos(tk.last)),
                ("close", _pos(tk.close)),
                ("delayedLast", _pos(getattr(tk, "delayedLast", None))),
                ("delayedClose", _pos(getattr(tk, "delayedClose", None))),
            ]
            price = next((v for _, v in candidates if v is not None), None)
            field = next((n for n, v in candidates if v is not None), None)

            # Live top-of-book, kept only as a cross-check. It is NOT what Gate 3
            # reads — see _spread_history.
            bid, ask = _pos(tk.bid), _pos(tk.ask)
            spread_pct = (ask - bid) / ((ask + bid) / 2) * 100 if bid and ask else None

            closes = _history(ib, tk.contract, duration=history_duration, rec=rec)
            result["spreads"][sym] = spread_stats(
                _spread_history(ib, tk.contract, spread_duration, rec=rec))
            if price is None and closes:
                price, field = closes[-1][1], "histDailyClose"

            result["prices"][sym] = {
                "price": price, "field": field,
                "bid": bid, "ask": ask, "spread_pct": spread_pct,
                "market_data_type": MARKET_DATA_TYPE_LABELS.get(
                    getattr(tk, "marketDataType", None),
                    str(getattr(tk, "marketDataType", None))),
                "con_id": getattr(tk.contract, "conId", None),
            }
            rec.price(sym, {**result["prices"][sym],
                            "candidates": {n: v for n, v in candidates}})
            result["history"][sym] = closes

        gold_spec = {"secType": "CMDTY", "symbol": "XAUUSD",
                     "exchange": "SMART", "currency": "USD"}
        gold = Contract(**gold_spec)
        try:
            with rec.call("qualifyContracts", contracts=[gold_spec]) as e:
                ib.qualifyContracts(gold)
                e["result"] = [_contract_raw(gold)]
            rec.contract(gold_spec, gold)
            result["gold_history"] = _history(ib, gold, "MIDPOINT",
                                              GOLD_HISTORY_DURATION, rec=rec)
        except Exception:
            result["gold_history"] = []

        # AUD/USD daily bars turn the USD gold series into the AUD one the
        # regression actually wants (§7). Without it beta is measured against
        # the wrong numéraire for an all-AUD cost base.
        try:
            audusd = Forex("AUDUSD")
            audusd_spec = {"secType": "CASH", "pair": "AUDUSD",
                           "exchange": "IDEALPRO"}
            with rec.call("qualifyContracts", contracts=[audusd_spec]) as e:
                ib.qualifyContracts(audusd)
                e["result"] = [_contract_raw(audusd)]
            rec.contract(audusd_spec, audusd)
            result["audusd_history"] = _history(ib, audusd, "MIDPOINT",
                                                GOLD_HISTORY_DURATION, rec=rec)
        except Exception:
            result["audusd_history"] = []

        result["fx"] = _gold_and_fx(ib, rec)
    finally:
        with rec.call("disconnect") as e:
            # Byte and message counts, from TWS's side of the socket. A session
            # that returned a suspiciously small bundle should show a
            # suspiciously small byte count, and if it does not, the loss
            # happened in this file rather than on the wire.
            with contextlib.suppress(Exception):
                s = ib.client.connectionStats()
                e["result"] = {"duration_s": round(s.duration, 3),
                               "msgs_sent": s.numMsgSent,
                               "msgs_recv": s.numMsgRecv,
                               "bytes_sent": s.numBytesSent,
                               "bytes_recv": s.numBytesRecv}
                rec.session["connection_stats"] = e["result"]
            ib.disconnect()

    result["bundle"] = rec.bundle()
    result["bar_rows"] = rec.bar_rows
    return result


# ──────────────────────────────────────────────────────────────────────────
# Risk statistics
# ──────────────────────────────────────────────────────────────────────────

def compute_risk_stats(history: dict[str, list[tuple[str, float]]],
                       gold_history: list[tuple[str, float]],
                       audusd_history: list[tuple[str, float]] | None = None,
                       cfg: dict | None = None) -> dict[str, dict]:
    """β_gold, R² and annualised idiosyncratic vol per name. REPORTING ONLY.

    Nothing here reaches a weight. β_gold checks the §0 mandate band and σ_idio
    and R² are printed as diagnostics; a name whose regression fails is still
    weighted, because the ounce ledger does not depend on price history.

    That is a deliberate reversal. σ_idio used to divide every weight, and on
    17 August 2026 it was measured at +0.77 log-correlation with ounces/EV —
    i.e. the denominator was cancelling the numerator, removing most of the
    cross-sectional signal the ledger exists to express. It also ran −0.76
    against P/NAV and −0.62 against EV, so it was simultaneously a bet against
    cheap names and a tilt toward large ones, neither of which appears anywhere
    in the objective. It is now a column in a table and nothing else.

    Regressed against gold in AUD where an AUD/USD series is available — the
    economically correct regressor for AUD-listed producers with an AUD cost
    base. Falls back to USD gold with a flag, which understates beta for these
    names because AUD weakness in a risk-off gold rally is a margin tailwind
    the USD series doesn't capture.

    Every series is joined on date before anything is differenced, so each
    equity return and its paired gold return span the same interval. Beta is
    still the §0 mandate check, so calendar or FX noise leaking into the pairing
    would misreport the one number the mandate is tested against.

    Beta is then estimated Dimson-style, summing the coefficients on gold at
    t−1, t and t+1, because the ASX and the metals feed do not close at the same
    instant. See config risk.dimson_note for the measurement that established
    this. The contemporaneous figures are returned alongside so the size of the
    correction is visible rather than buried.
    """
    risk_cfg = (cfg or {}).get("risk") or {}
    lags = risk_cfg.get("dimson_lags", 1) \
        if risk_cfg.get("beta_estimator", "dimson") == "dimson" else 0

    stats: dict[str, dict] = {}
    if not gold_history or len(gold_history) < 61:
        return stats

    if audusd_history:
        gold_series = [(d, g / fx) for d, g, fx in _join(gold_history, audusd_history)
                       if fx > 0]
        basis = "AUD"
    else:
        gold_series = list(gold_history)
        basis = "USD (fallback — beta understated for AUD-cost producers)"

    if len(gold_series) < 61:
        return stats

    for sym, closes in history.items():
        if len(closes) < 61:
            stats[sym] = {"error": f"only {len(closes)} bars"}
            continue

        paired = _join(closes, gold_series)
        if len(paired) < 61:
            stats[sym] = {"error": f"only {len(paired)} dates in common with gold"}
            continue

        rets = _log_returns([p for _, p, _ in paired])
        gold_rets = _log_returns([g for _, _, g in paired])
        n = len(rets)
        if n < 60 or n != len(gold_rets):
            stats[sym] = {"error": f"only {n} overlapping returns"}
            continue

        fit = _ols(rets, gold_rets)
        if fit is None:
            stats[sym] = {"error": "regression failed"}
            continue
        _, beta_now, r2_now, resid_now = fit

        # Dimson sum-of-lags. See config risk.dimson_note: the ASX close leads
        # the metals-bar close by ~15 hours, so a gold bar is not priced by the
        # ASX until the next session. Contemporaneous OLS therefore splits each
        # response across two bars and reports roughly half the true beta.
        beta, r2, resid_std, est = beta_now, r2_now, resid_now, "contemporaneous"
        if lags >= 1 and n > 2 * lags + 60:
            span = range(lags, n - lags)
            cols = [[gold_rets[t + k] for t in span]
                    for k in range(-lags, lags + 1)]
            mfit = _ols_multi([rets[t] for t in span], cols)
            if mfit is not None:
                coefs, r2, resid_std = mfit
                beta = sum(coefs[1:])
                est = f"dimson±{lags}"

        mean = sum(rets) / n
        total_std = math.sqrt(sum((r - mean) ** 2 for r in rets) / (n - 1))
        stats[sym] = {
            "beta_gold": beta,
            "beta_contemporaneous": beta_now,
            "estimator": est,
            "r2": r2,
            "r2_contemporaneous": r2_now,
            "sigma_idio": resid_std * math.sqrt(TRADING_DAYS),
            "sigma_total": total_std * math.sqrt(TRADING_DAYS),
            "n_obs": n,
            "basis": basis,
        }

    # The weekly and cohort-shrunk σ_idio estimators that used to be computed
    # here are deleted along with the σ_idio denominator they were candidates
    # for. The old §13 item 7 asked which of three ways to estimate a parameter
    # was best; the answer turned out to be that the parameter should not have
    # been in the formula. Deleting the question is cheaper than answering it.

    return stats


# ──────────────────────────────────────────────────────────────────────────
# The ounce ledger
# ──────────────────────────────────────────────────────────────────────────

def confidence_weights(cfg: dict) -> tuple[float, float, float]:
    """§6 discounts by resource category: (P&P, M&I non-reserve, Inferred).

    Read from config, not hardcoded. They were both, for a while — config
    declared confidence_weights citing §6.1 and the engine carried three module
    constants that happened to hold the same numbers. Two sources for one
    parameter is the same defect as none: editing the declared one changes
    nothing and says nothing.
    """
    cw = cfg["confidence_weights"]
    return (cw["proven_probable"],
            cw["measured_indicated_non_reserve"],
            cw["inferred"])


def eligible_shares(c: dict) -> tuple[float, float, float]:
    """§2.4 Gate 1 share per resource category: (P&P, M&I non-reserve, Inferred).

    Falls back to the blended eligible_ounce_share per category, which is exact
    for the ~100%-eligible majority and, for a mixed-jurisdiction name, is exact
    on the TOTAL and wrong on the split. See ounce_ledger property 4.
    """
    blend = c["eligible_ounce_share"]
    return tuple(  # type: ignore[return-value]
        blend if c.get(field) is None else c[field]
        for field in ELIGIBLE_CATEGORY_FIELDS.values())


def ounce_ledger(c: dict, conf: tuple[float, float, float],
                 hedge_years: float) -> tuple[dict | None, str]:
    """The whole model. Every ounce this company can deliver to us, by type.

    Returns (ledger, reason). `ledger` is None when the claim cannot be counted,
    and `reason` says which line was missing.

        gross      P&P + M&I non-reserve + Inferred, as disclosed
        eligible   × the Gate 1 share FOR THAT CATEGORY. Ounces under a sovereign
                   that fails Tier A are not counted at all, at any discount.
                   This is what makes a company-level production threshold
                   unnecessary (§2.4): Pogo simply is not an ounce we own,
                   rather than triggering a cliff at some arbitrary 65% line.
        claimed    each category × its confidence weight (§6)
        hedged     less ounces already sold forward (§6.3)
        net        what the weight is computed on

    Four properties worth stating, because each one replaces a score:

    1. **The categories are the convexity.** P&P is the in-the-money strip:
       ounces the company has committed to mine at a cost it has published.
       M&I non-reserve is the near-money option — drilled to a confidence that
       supports a mine plan, not yet economic enough to book. Inferred is the
       far out-of-the-money tail. Counting all three at 1.0 / 0.5 / 0.2 IS the
       bet that the sub-economic inventory comes into the money on a gold move.
       No separate convexity score is needed and none is computed; the old one
       turned out to be this same ratio re-derived (c2b was exactly
       net_ounces / pp_moz, so the inventory entered the weight squared).

    2. **The hedge is a subtraction, not a multiplier.** A forward sale alienates
       the ounces it covers and no others. Multiplying a whole claim by
       (1 − sold_share), which charged a 24-month forward book against a
       thirty-year reserve life: Northern Star's 25.5% hedge cost it 25.5% of
       its whole claim instead of the 0.79 Moz it has actually sold. The ledger
       makes the magnitude explicit and therefore arguable.

    3. **M&I is required, Inferred is not.** M&I non-reserve is disclosed in
       every JORC and NI 43-101 annual statement, so a null is a sourcing gap,
       and letting a name through P&P-only would put it in the cross-section
       counting only its in-the-money ounces against peers counting all three.
       Inferred is not always broken out and is only 0.2-weighted, so its
       absence is reported and treated as zero — which understates the name.

    4. **Gate 1 is applied per category, not as a blend.** eligible_ounce_share
       is a CONFIDENCE-WEIGHTED share: ineligible confidence-weighted ounces over
       group confidence-weighted ounces. Multiplying all three tranches by it
       therefore reproduces the right TOTAL claim and the wrong SPLIT — an
       ineligible asset that is reserve-light and Inferred-heavy, as Pogo and Red
       Lake both are, moves claim out of the reserve tranche and into the tail.
       That mattered once the ledger mix became the published convexity number:
       the blend read 57.3/29.6/13.1 where the category shares read
       57.9/29.5/12.7 on the same book, overstating the inferred tail by 0.5pp. Where the
       per-category shares are sourced they are authoritative and the blend
       becomes a reconciliation control (see reconcile_eligibility); where they
       are not, the blend is the fallback and is exact whenever it is 1.0.
    """
    pp = c.get("pp_moz")
    if pp is None:
        return None, "pp_moz missing"
    mi = c.get("mi_non_reserve_moz")
    if mi is None:
        return None, ("mi_non_reserve_moz missing — the M&I non-reserve tranche is "
                      "the near-money option inventory and every JORC statement "
                      "discloses it; counting this name on P&P alone would put it "
                      "in the cross-section against peers counting all three")
    elig = c.get("eligible_ounce_share")
    if elig is None:
        return None, "eligible_ounce_share missing (jurisdiction split unresolved)"
    elig_pp_s, elig_mi_s, elig_inf_s = eligible_shares(c)

    hedge_share = c.get("hedge_share_fwd24m")
    if hedge_share is None:
        return None, ("hedge_share_fwd24m missing — an unknown short position "
                      "against the claim is not a claim that can be sized (§6.3)")
    prod = c.get("production_koz_yr")
    if prod is None:
        return None, "production_koz_yr missing — the hedged tranche cannot be sized"

    w_pp, w_mi, w_inf = conf
    inf = c.get("inferred_moz")

    # Sold ounces come off P&P first: a forward contract is delivered from
    # reserves, not from inferred material, so it consumes the most certain
    # tranche. Capped at the eligible P&P tranche — a hedge book larger than the
    # reserves behind it is a data error, not a negative claim.
    elig_pp = pp * elig_pp_s
    hedged = min(hedge_share * (prod / 1000.0) * hedge_years, elig_pp)

    net = ((elig_pp - hedged) * w_pp
           + mi * elig_mi_s * w_mi
           + (inf or 0.0) * elig_inf_s * w_inf)
    if net <= 0:
        return None, "no net claimed ounces after Gate 1 and the hedge book"

    return {
        "gross_moz": pp + mi + (inf or 0.0),
        "pp_moz": pp, "mi_moz": mi, "inferred_moz": inf or 0.0,
        "eligible_share": elig,
        "eligible_pp_share": elig_pp_s,
        "eligible_mi_share": elig_mi_s,
        "eligible_inferred_share": elig_inf_s,
        "eligible_by_category": any(
            c.get(k) is not None for k in ELIGIBLE_CATEGORY_FIELDS.values()),
        "elig_pp_moz": elig_pp,
        "elig_mi_moz": mi * elig_mi_s,
        "elig_inferred_moz": (inf or 0.0) * elig_inf_s,
        "hedged_moz": hedged,
        "hedge_share_fwd": hedge_share,
        "claimed_moz": net,
        "inferred_absent": inf is None,
    }, "ok"


def _date_bounds(text: object) -> tuple[date, date] | None:
    """The earliest and latest day a recorded document date can mean.

    YYYY-MM-DD is a single day. YYYY-MM is a real thing in this data layer —
    two Greatland releases are dated only to the month, because that is all the
    source states — and it is a RANGE, not an invitation to pick the 1st. The
    caller tests both ends, exactly as gate_input_invariant does for an absent
    number. Anything else returns None and the caller fails the name.
    """
    if not isinstance(text, str):
        return None
    try:
        return (date.fromisoformat(text), date.fromisoformat(text))
    except ValueError:
        pass
    if re.fullmatch(r"\d{4}-\d{2}", text):
        first = date.fromisoformat(f"{text}-01")
        nxt = date(first.year + first.month // 12, first.month % 12 + 1, 1)
        return (first, nxt - timedelta(days=1))
    return None


def statement_currency(c: dict, as_of: date,
                       max_age_months: float) -> tuple[bool, float | None, str]:
    """§6.4. Is the resource statement behind the counted ounces current?

    Returns (pass, age_months_of_the_oldest_counted_tranche, reason).

    A reserve and resource statement is an annual obligation, so a ledger input
    older than one reporting cycle plus six months of issuer timing is not a
    current claim — it is the last claim, carried forward. This is not a quality
    score and cannot be offset: an ounce whose statement has gone stale is not a
    cheaper ounce, it is an unverified one.

    The bar is applied to the document behind EVERY tranche the ledger counts,
    not to one nominated statement, because the tranches are separately sourced —
    Regis reads P&P off a July quarterly and Inferred off an April resource
    release, and it is the older of the two that dates the claim.

    Absence fails. A month-only date is tested at both ends of the month and
    passes only if the verdict is invariant across it, which is the same rule
    config.estimation_policy.on_absence already applies to a missing number:
    invariant means the missing precision cannot decide the answer.
    """
    oldest_age, oldest_field, unknown = None, None, []
    for field in ELIGIBLE_CATEGORY_FIELDS:
        if c.get(field) is None:          # Inferred may legitimately be absent
            continue
        doc_key = (c.get("_field_docs", {}).get(field) or {}).get("doc")
        bounds = _date_bounds((c.get("_docs", {}).get(doc_key) or {}).get("date"))
        if bounds is None:
            unknown.append(f"{field} ({doc_key or 'no document'})")
            continue
        # Oldest end first: it is the one that can fail.
        ages = sorted(((as_of - d).days / DAYS_PER_MONTH for d in bounds),
                      reverse=True)
        if ages[0] > max_age_months >= ages[1]:
            return False, ages[0], (
                f"resource statement for {field} is dated {doc_key!r} to the month "
                f"only and straddles the {max_age_months:g}-month bar "
                f"({ages[1]:.1f}–{ages[0]:.1f} months) — the verdict is unknown, "
                f"not favourable")
        if ages[1] < 0:
            return False, ages[1], (
                f"resource statement for {field} is dated after the build")
        if oldest_age is None or ages[0] > oldest_age:
            oldest_age, oldest_field = ages[0], field
    if unknown:
        return False, None, ("no usable date on the resource statement behind "
                             + ", ".join(unknown))
    if oldest_age is None:
        return False, None, "no resource statement backs any counted tranche"
    if oldest_age > max_age_months:
        return False, oldest_age, (
            f"resource statement behind {oldest_field} is {oldest_age:.1f} months "
            f"old against a {max_age_months:g}-month bar (§6.4)")
    return True, oldest_age, "current"


def gate_input_invariant(c: dict, field: str, lo: float, hi: float,
                         anchor_gold: float, mcap: float | None,
                         cfg: dict) -> tuple[bool, str]:
    """Can an ABSENT gate input change the gate's answer?

    This is what config.estimation_policy requires in place of filling the value
    in. A missing number is not an invitation to invent one — it is a question
    about whether the answer is knowable without it. So run the gate at both ends
    of the range the cohort actually reports. If the verdict is the same at both,
    the missing value cannot decide anything and the name proceeds with a warning.
    If it differs, the answer is genuinely unknown and the name fails.

    The asymmetry is deliberate. Absence currently reads as zero, which for
    committed capex makes a SURVIVAL test easier — the one direction a gate must
    never err in. Testing the range removes the free pass without substituting a
    guess for it.
    """
    verdicts = set()
    for v in (lo, hi):
        probe = dict(c)
        probe[field] = v
        verdicts.add(gate2_survival(probe, anchor_gold, mcap, cfg).get("pass"))
    if len(verdicts) == 1:
        return True, (f"{field} absent, but Gate 2 is invariant across "
                      f"{lo:,.0f}–{hi:,.0f} — the missing value cannot change the verdict")
    return False, (f"{field} absent and Gate 2 FLIPS across {lo:,.0f}–{hi:,.0f}: "
                   f"the outcome is unknown, not favourable")


# The Gate 2 inputs a disclosed range or a horizon basis can attach to. Listed
# rather than inferred so that adding a range to some unrelated field cannot
# silently start deciding a gate.
GATE2_RANGED_INPUTS = ("aisc_aud_oz", "production_koz_yr",
                       "undrawn_facilities_aud_m", "net_debt_aud_m")


def disclosed_ranges(c: dict) -> dict[str, tuple[float, float]]:
    """Issuer-published ranges attached to this name's Gate 2 inputs (§3.2).

    A range is here only when the record took a midpoint of a span the ISSUER
    published for the SAME quantity over the SAME period. An analyst's span
    between two defensible conventions is not one — Vault's "the honest span is
    173-364" is a scope choice and stays in the note, because probing it would
    gate on which convention the analyst was undecided about rather than on
    anything Vault disclosed.
    """
    return {f: c[f"{f}_range"] for f in GATE2_RANGED_INPUTS
            if c.get(f"{f}_range") is not None and c.get(f) is not None}


def gate2_range_invariance(c: dict, ranges: dict[str, tuple[float, float]],
                           anchor_gold: float, mcap: float | None,
                           cfg: dict) -> dict:
    """Is the Gate 2 verdict invariant across the ranges the issuer published?

    `estimation_policy.on_absence` already says what to do with a gate input the
    engine cannot pin down: run the gate across the range, and if the verdict
    differs at the ends then the answer is unknown rather than favourable. That
    doctrine was wired for ABSENT inputs only, so a value the issuer published as
    a RANGE — recorded at its midpoint, which `permitted_provenance` allows —
    walked past it. Pantoro is the case that exposed it: recorded at the midpoint
    of its own FY27 AISC guidance it survives the stress by A$51m, and at the top
    of that same guidance range it fails. A midpoint is a permitted way to record
    a number. It is not a permitted way to decide a gate.

    Two verdicts come back and they are deliberately different in kind.

    SINGLE-FIELD gates. Each ranged input is swept to both of its ends on its
    own, which is exactly what gate_input_invariant already does for an absent
    one. A flip means this issuer's own disclosure does not determine the answer.

    JOINT is reported, never gated. Every ranged input at its against-the-name
    end at once is a compound of independent uncertainties, and treating that as
    a failure would reject a name for a scenario no disclosure asserts. It is
    flagged STRAINED instead — the same call Gate 3 already makes on a name that
    passes on the median spread and breaches on p90.
    """
    out = {"tested": sorted(ranges), "flipped": [], "strained": False}
    if not ranges:
        return {**out, "ok": True, "reason": "no issuer-published range on a Gate 2 input"}

    for field, (lo, hi) in sorted(ranges.items()):
        ok, why = gate_input_invariant(c, field, lo, hi, anchor_gold, mcap, cfg)
        if not ok:
            out["flipped"].append(f"{field} {lo:,.0f}–{hi:,.0f}")

    corners = {gate2_survival({**c, **dict(zip(ranges, corner))},
                              anchor_gold, mcap, cfg).get("pass")
               for corner in itertools.product(*(ranges[f] for f in ranges))}
    out["strained"] = len(corners) > 1 and not out["flipped"]

    if out["flipped"]:
        return {**out, "ok": False,
                "reason": ("Gate 2 is not invariant across the issuer's own published "
                           f"range for {', '.join(out['flipped'])} — the verdict is "
                           "unknown, not favourable")}
    return {**out, "ok": True,
            "reason": ("invariant across every published range"
                       + (" on each input alone, but NOT at every combination of "
                          "their against-the-name ends — STRAINED, reported not gated"
                          if out["strained"] else ""))}


def gate2_capital_interval(c: dict, cfg: dict) -> dict:
    """Aggregate project Gate 2 capital without imputing missing periods.

    Coverage dates determine direction before amounts are summed.  A project
    record that ends before the Gate 2 horizon is a lower bound; one that runs
    past the horizon is an upper bound.  The data validator requires those
    directions to be explicit, and this evaluator preserves them as an interval
    rather than promoting either side to a point.
    """
    projects = c.get(EXECUTION_CAPITAL_PROJECTS_KEY)
    if not isinstance(projects, list) or not projects:
        return {
            "ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
            "upper_aud_m": None,
            "reason": "no per-project Gate 2 capital records",
            "projects": [],
        }

    lower = 0.0
    upper = 0.0
    nominal_total = 0.0
    has_unresolved = False
    project_rows = []
    expected_horizon: tuple[date, date] | None = None
    expected_days = cfg["gate2"]["horizon_years"] * 365.25

    for project in projects:
        project_id = project.get("project_id", "?") if isinstance(project, dict) else "?"
        if not isinstance(project, dict):
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None, "reason": "invalid project capital record",
                    "projects": project_rows}
        h_start = _iso_date(project.get("gate2_horizon_start"))
        h_end = _iso_date(project.get("gate2_horizon_end"))
        if h_start is None or h_end is None or h_start > h_end:
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": f"{project_id} has invalid Gate 2 horizon dates",
                    "projects": project_rows}
        if abs((h_end - h_start).days - expected_days) > 2.0:
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": (f"{project_id} horizon is {(h_end - h_start).days} days, "
                               f"not configured {cfg['gate2']['horizon_years']:g} years"),
                    "projects": project_rows}
        if expected_horizon is None:
            expected_horizon = (h_start, h_end)
        elif expected_horizon != (h_start, h_end):
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": "project Gate 2 horizons do not match",
                    "projects": project_rows}

        interval = _directional_interval(
            project.get("committed_within_gate2_horizon_aud_m"),
            project.get("committed_capex_state"),
            project.get("committed_capex_range_aud_m"),
        )
        if interval is None:
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": f"{project_id} has invalid committed-capex evidence",
                    "projects": project_rows}
        lo, hi = interval
        lower += lo
        upper = upper + hi if math.isfinite(upper) and math.isfinite(hi) else math.inf
        committed_value = project.get("committed_within_gate2_horizon_aud_m")
        if project.get("committed_capex_state") == "UNRESOLVED":
            has_unresolved = True
        elif isinstance(committed_value, (int, float)) and not isinstance(committed_value, bool):
            nominal_total += float(committed_value)

        c_start = _iso_date(project.get("coverage_start"))
        c_end = _iso_date(project.get("coverage_end"))
        if c_start is None or c_end is None:
            coverage_state = "UNRESOLVED"
        else:
            under = c_start > h_start or c_end < h_end
            over = c_start < h_start or c_end > h_end
            coverage_state = ("MIXED" if under and over else
                              "UNDER" if under else "OVER" if over else "EXACT")
        state = project.get("committed_capex_state")
        if (coverage_state == "UNRESOLVED" and state != "UNRESOLVED"):
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": f"{project_id} has no usable coverage dates",
                    "projects": project_rows}
        if coverage_state == "MIXED":
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": f"{project_id} both omits and exceeds the horizon",
                    "projects": project_rows}
        if coverage_state == "UNDER" and state != "LOWER_BOUND":
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": f"{project_id} under-coverage is not a LOWER_BOUND",
                    "projects": project_rows}
        if coverage_state == "OVER" and state != "UPPER_BOUND":
            return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                    "upper_aud_m": None,
                    "reason": f"{project_id} over-coverage is not an UPPER_BOUND",
                    "projects": project_rows}
        project_rows.append({
            "project_id": project_id,
            "state": project.get("committed_capex_state"),
            "lower_aud_m": lo,
            "upper_aud_m": hi if math.isfinite(hi) else None,
            "coverage_state": coverage_state,
            "coverage_start": project.get("coverage_start"),
            "coverage_end": project.get("coverage_end"),
            "coverage_note": project.get("coverage_note"),
        })

    reported = c.get("committed_capex_aud_m")
    if ((has_unresolved and reported is not None)
            or (not has_unresolved
                and (not isinstance(reported, (int, float))
                     or isinstance(reported, bool)
                     or not math.isclose(float(reported), nominal_total,
                                         abs_tol=1e-6)))):
        return {"ok": False, "state": "UNRESOLVED", "lower_aud_m": 0.0,
                "upper_aud_m": None,
                "reason": "project capital does not reconcile to committed_capex_aud_m",
                "projects": project_rows}

    if math.isfinite(upper) and math.isclose(lower, upper, abs_tol=1e-12):
        state = "POINT"
    elif math.isfinite(upper):
        state = "UPPER_BOUND" if lower == 0 else "BOUNDED_RANGE"
    elif lower > 0:
        state = "LOWER_BOUND"
    else:
        state = "UNRESOLVED"
    start, end = expected_horizon or (None, None)
    return {
        "ok": True,
        "state": state,
        "lower_aud_m": lower,
        "upper_aud_m": upper if math.isfinite(upper) else None,
        "gate2_horizon_start": start.isoformat() if start else None,
        "gate2_horizon_end": end.isoformat() if end else None,
        "projects": project_rows,
        "reason": None,
    }


def gold_anchor(aud_gold_series: list[tuple[str, float]], spot_aud: float,
                cfg: dict) -> dict:
    """Trailing real-gold reference for the conservative reporting NAV deck.

    Before v1.7 this was also the Gate 2 origin. Producer health now applies its
    literal drawdown to spot; this reference remains because the reporting-only
    NAV model needs a conservative long-term deck.

    Past prices are inflated to today's money at anchor_inflation_pa. That is
    required for a like-for-like reporting deck.
    """
    g = cfg["gate2"]

    if g.get("anchor") != "trailing_average" or not aud_gold_series:
        why = ("configured to spot" if g.get("anchor") != "trailing_average"
               else "NO GOLD HISTORY — fell back to spot")
        return {"anchor_aud": spot_aud,
                "basis": f"spot ({why})", "n_obs": 0,
                "degraded": g.get("anchor") == "trailing_average"}

    years = g.get("anchor_years", 3.0)
    infl = g.get("anchor_inflation_pa", 0.0)
    window = aud_gold_series[-int(round(years * TRADING_DAYS)):]

    # Weight each observation up to today's money by its age in the window.
    n = len(window)
    adjusted = [p * (1.0 + infl) ** ((n - 1 - i) / TRADING_DAYS)
                for i, p in enumerate(v for _, v in window)]
    anchor = sum(adjusted) / n

    return {
        "anchor_aud": anchor,
        "basis": (f"trailing {years:g}y real average of AUD gold, "
                  f"{window[0][0]}→{window[-1][0]}, "
                  f"inflated to today at {infl:.1%}/yr"),
        "n_obs": n,
        "years_available": round(n / TRADING_DAYS, 2),
        "degraded": n < int(round(years * TRADING_DAYS)) * 0.8,
    }


def creditable_undrawn(c: dict, cfg: dict, as_of: date) -> tuple[float, str | None]:
    """§3 — a facility that lapses inside the stress window is not stress liquidity.

    Gate 2 credits committed-but-undrawn credit as liquidity available through a
    two-year drawdown. That is only true if the facility still exists at the end
    of it. Evolution's audited FY26 report settled the question the record had
    been carrying as a caveat: Revolving Credit Facility A terms 1 August 2028,
    NINETEEN DAYS inside a window opened on the 20 August 2026 build. Regis's
    A$300m lapses in February 2028, six months inside. Both were being counted in
    full.

    So a facility is creditable only if its term date is on or after the horizon
    ends. An ABSENT term date is not creditable either: crediting an unverified
    facility makes a survival test easier, which is the one direction it may not
    err in, and the fix is to source the date rather than to assume the lender.

    Refinancing is not assumed. A revolver rolled every three years for a decade
    is still a contract that ends on a date, and in the drawdown this gate
    describes it is exactly the kind of contract that does not get rolled.

    Returns (creditable amount, reason to report) — the amount is zero and the
    reason is set whenever a disclosed facility is dropped.
    """
    amt = c.get("undrawn_facilities_aud_m") or 0.0
    if amt <= 0 or not cfg["gate2"]["count_undrawn_facilities"]:
        return amt, None
    horizon_end = as_of + timedelta(days=365.25 * cfg["gate2"]["horizon_years"])
    raw = c.get("undrawn_facilities_aud_m_term_date")
    if raw is None:
        return 0.0, (f"A${amt:,.0f}m of undrawn facilities NOT credited — no term "
                     f"date sourced, and an unverified facility cannot prove "
                     f"liquidity at {horizon_end:%b %Y}")
    term = date.fromisoformat(raw)
    if term < horizon_end:
        return 0.0, (f"A${amt:,.0f}m of undrawn facilities NOT credited — the "
                     f"facility lapses {term:%d %b %Y}, inside a window running to "
                     f"{horizon_end:%d %b %Y}")
    return amt, None


def _capital_as_of(c: dict, field: str) -> date | None:
    """Return a capital field's explicit as-of date, then its document date."""
    raw = c.get(f"{field}_as_of")
    if raw:
        try:
            return date.fromisoformat(raw)
        except (TypeError, ValueError):
            return None
    doc_key = (c.get("_field_docs", {}).get(field) or {}).get("doc")
    raw = (c.get("_docs", {}).get(doc_key) or {}).get("date")
    if raw:
        try:
            return date.fromisoformat(raw)
        except (TypeError, ValueError):
            return None
    return None


def _capital_evidence(c: dict, field: str, cfg: dict,
                      as_of: date) -> dict:
    """Resolve one directional amount without turning absence into zero."""
    # Read on every resolution so config_audit can prove the declared consumer
    # is live even when today's cross-section contains no execution-capital
    # carry-forward.
    max_months = cfg["execution_capital"]["incumbent_max_carry_forward_months"]
    state = c.get(f"{field}_evidence_state")
    value = c.get(field)
    out = {"field": field, "state": state, "value_aud_m": value}
    if state not in CAPITAL_EVIDENCE_STATES:
        return {**out, "usable": False,
                "reason": f"{field} evidence state is missing or invalid"}
    if state == "UNRESOLVED":
        return {**out, "usable": False,
                "reason": f"{field} is UNRESOLVED"}
    if value is None:
        return {**out, "usable": False,
                "reason": f"{field} state {state} has no amount"}
    if state == "CARRY_FORWARD":
        source_date = _capital_as_of(c, field)
        if source_date is None:
            return {**out, "usable": False,
                    "reason": f"{field} CARRY_FORWARD has no valid as-of date"}
        age_months = max(0.0, (as_of - source_date).days / DAYS_PER_MONTH)
        out.update({"source_date": source_date.isoformat(),
                    "age_months": round(age_months, 2),
                    "max_age_months": max_months})
        if age_months > max_months:
            return {**out, "usable": False,
                    "reason": (f"{field} CARRY_FORWARD is {age_months:.1f} months "
                               f"old, above the {max_months:g}-month limit")}
    return {**out, "usable": True, "reason": None}


def _amount_interval(evidence: dict) -> tuple[float, float]:
    """Convert a validated directional amount to a non-negative interval."""
    if not evidence.get("usable"):
        return 0.0, math.inf
    value = float(evidence["value_aud_m"])
    state = evidence["state"]
    if state in ("POINT", "CARRY_FORWARD"):
        return value, value
    if state == "UPPER_BOUND":
        return 0.0, value
    if state == "LOWER_BOUND":
        return value, math.inf
    return 0.0, math.inf


def derive_residual_funding_gap(c: dict, cfg: dict,
                                as_of: date | None = None,
                                ev_aud_m: float | None = None) -> dict:
    """Derive the developer funding gap and preserve its direction.

    ``gap = max(0, remaining execution capital - available project funding)``.
    Intervals prevent a bound from being silently promoted to a point.  Gate 2
    can therefore prove a pass at the adverse upper gap or a failure at the
    lower gap; an interval straddling its threshold is unresolved.
    """
    if as_of is None:
        raw = c.get("_data_sourced")
        as_of = date.fromisoformat(raw) if raw else datetime.now(timezone.utc).date()
    execution = _capital_evidence(c, EXECUTION_CAPITAL_FIELD, cfg, as_of)
    funding = _capital_evidence(c, PROJECT_FUNDING_FIELD, cfg, as_of)
    c_lo, c_hi = _amount_interval(execution)
    f_lo, f_hi = _amount_interval(funding)
    materiality = cfg["execution_capital"]["materiality_of_ev"]
    de_minimis = (ev_aud_m is not None and ev_aud_m > 0
                  and math.isfinite(c_hi) and c_hi / ev_aud_m < materiality)
    if de_minimis:
        c_lo, c_hi = 0.0, 0.0
    lower = max(0.0, c_lo - f_hi) if math.isfinite(f_hi) else 0.0
    upper = max(0.0, c_hi - f_lo) if math.isfinite(c_hi) else math.inf

    if math.isfinite(upper) and math.isclose(lower, upper, abs_tol=1e-12):
        state, amount = "POINT", lower
    elif math.isfinite(upper):
        state, amount = "UPPER_BOUND", upper
    elif lower > 0:
        state, amount = "LOWER_BOUND", lower
    else:
        state, amount = "UNRESOLVED", None
    return {
        "state": state,
        "value_aud_m": amount,
        "lower_aud_m": lower,
        "upper_aud_m": upper if math.isfinite(upper) else None,
        "execution_capital_de_minimis": de_minimis,
        "execution_capital": execution,
        "available_project_funding": funding,
    }


def resolve_execution_capital(c: dict, cfg: dict, as_of: date) -> dict:
    """Admit only denominator-safe execution-capital evidence."""
    evidence = _capital_evidence(c, EXECUTION_CAPITAL_FIELD, cfg, as_of)
    if not evidence.get("usable"):
        return {**evidence, "ok": False}
    if evidence["state"] == "LOWER_BOUND":
        return {**evidence, "ok": False,
                "reason": (f"{EXECUTION_CAPITAL_FIELD} is a LOWER_BOUND; using it "
                           "would shrink the denominator and raise the weight")}
    return {**evidence, "ok": True}


def execution_capital_ledger(c: dict, ev_aud_m: float, cfg: dict,
                             as_of: date) -> dict:
    """Resolve company execution capital and apply aggregate materiality."""
    materiality = cfg["execution_capital"]["materiality_of_ev"]
    resolved = resolve_execution_capital(c, cfg, as_of)
    if not resolved.get("ok"):
        return resolved
    disclosed = float(resolved["value_aud_m"])
    ratio = disclosed / ev_aud_m if ev_aud_m > 0 else math.inf
    included = disclosed > 0 and ratio >= materiality
    effective = disclosed if included else 0.0
    return {
        **resolved,
        "ok": True,
        "disclosed_aud_m": disclosed,
        "effective_aud_m": effective,
        "of_ev": ratio,
        "materiality_of_ev": materiality,
        "material": included,
        "reason": (None if included else
                   ("sourced zero" if disclosed == 0 else
                    f"below {materiality:.1%} of pre-capex EV")),
    }


def gate2_survival(c: dict, anchor_gold: float, mcap_aud_m: float | None,
                   cfg: dict, stress_gold: float | None = None,
                   normal_gold: float | None = None) -> dict:
    """Methodology §3 — producer health under a severe but repairable shock.

    Gate 2 excludes demonstrated distress, not every company that might need
    financing.  The adverse edge of a finite capital interval is used where it
    exists.  A lower-bound or unresolved record contributes only its sourced,
    unavoidable lower edge and makes the result AMBER rather than inventing a
    future commitment.  GREEN and AMBER remain eligible; RED is excluded.
    """
    if c.get("sleeve") == "developer":
        return _gate2_developer(c, mcap_aud_m, cfg)

    capital = gate2_capital_interval(c, cfg)
    lower = capital.get("lower_aud_m") or 0.0
    upper = capital.get("upper_aud_m") if capital.get("ok") else None
    complete = upper is not None
    tested_capex = upper if complete else lower
    health = _gate2_producer_at_capex(
        c, anchor_gold, cfg, tested_capex, mcap_aud_m=mcap_aud_m,
        stress_gold=stress_gold, normal_gold=normal_gold)
    if health.get("pass") is not True:
        return {**health, "capital_interval": capital, "provisional": False}
    if complete:
        return {**health, "capital_interval": capital, "provisional": False}

    evidence = (capital.get("reason") or
                f"only A${lower:,.0f}m of unavoidable commitments is sourced")
    detail = {**(health.get("detail") or {}),
              "capital_evidence_complete": False,
              "capital_evidence_note": evidence}
    return {
        **health, "pass": True, "health": "AMBER", "detail": detail,
        "reason": (f"AMBER — health check uses A${lower:,.0f}m of sourced "
                   f"unavoidable commitments; future discretionary or unresolved "
                   f"capital is not assumed ({evidence})"),
        "capital_interval": capital, "provisional": True,
    }


def _gate2_producer_at_capex(c: dict, anchor_gold: float, cfg: dict,
                             capex_val: float,
                             stress_gold: float | None = None,
                             normal_gold: float | None = None,
                             mcap_aud_m: float | None = None) -> dict:
    """Evaluate producer damage and recovery at one explicit capital amount.

    A deficit is not automatically fatal.  It is RED only when the rescue raise
    is too large relative to market capitalisation or normalised cash generation
    would take too many years to repair it.  Smaller deficits are AMBER.

    Three things about the construction matter.

    Run UNHEDGED. Revenue is computed at the stress price on all production and
    any hedge gain is disregarded. Otherwise a company passes survival on the
    strength of the very forward sales that penalise it under §6 — Catalyst's
    30 koz sold at A$6,075/oz would pay off handsomely in precisely this
    scenario, and crediting that would let a purity failure buy a survival pass.

    Committed capex only. Discretionary growth capital is deferrable in a
    drawdown; contracted spend is not. Counting all growth capex would fail
    almost every producer for spending they would simply stop.

    Direction and missing evidence are resolved by :func:`gate2_survival`
    before this point; this helper performs no defaulting or inference.
    """
    g = cfg["gate2"]
    max_rescue_ratio = g["producer_max_rescue_capital_of_mcap"]
    max_recovery_years = g["producer_max_recovery_years"]
    if not 0.0 <= max_rescue_ratio <= 1.0:
        raise ValueError("gate2.producer_max_rescue_capital_of_mcap must be in [0, 1]")
    if max_recovery_years <= 0:
        raise ValueError("gate2.producer_max_recovery_years must be positive")
    if stress_gold is None:
        stress_gold = anchor_gold * (1.0 - g["gold_drawdown"])
    normal_gold = normal_gold if normal_gold is not None else anchor_gold
    horizon = g["horizon_years"]

    core = {
        "production": c.get("production_koz_yr"),
        "AISC": c.get("aisc_aud_oz"),
        "net debt": c.get("net_debt_aud_m"),
        "market capitalisation": mcap_aud_m,
    }
    missing_core = [name for name, value in core.items()
                    if value is None or (name == "market capitalisation" and value <= 0)]
    if missing_core:
        return {
            "pass": None,
            "health": "UNTESTED",
            "reason": (f"{', '.join(missing_core)} unsourced — producer health "
                       "cannot be tested"),
            "provisional": True,
        }
    prod = core["production"]
    aisc = core["AISC"]

    # AISC is defined to include sustaining capital, so margin x ounces is a fair
    # pre-tax, pre-growth free cash flow proxy.
    #
    # Costs are inflated, not held flat. Holding AISC constant is ALSO an
    # assumption and it is the optimistic one: in 2013 costs did not fall with
    # the price, which is exactly why so much of the industry went cash-negative.
    # An explicit, stated rate is more honest than an implicit zero.
    infl = g.get("cost_inflation_pa", 0.0)
    fcf_horizon = 0.0
    remaining, year = horizon, 0
    while remaining > 1e-9:
        year += 1
        slice_yrs = min(1.0, remaining)
        aisc_y = aisc * (1.0 + infl) ** year
        fcf_y = prod * 1_000 * (stress_gold - aisc_y) / 1e6 * slice_yrs
        fcf_horizon += fcf_y
        remaining -= slice_yrs

    # Year-one margin, for reporting.
    margin = stress_gold - aisc * (1.0 + infl)
    fcf_annual = prod * 1_000 * margin / 1e6          # A$m
    if fcf_horizon > 0:
        fcf_horizon *= (1.0 - g["tax_rate"])

    # net_debt is negative when the company is in net cash.
    opening = -core["net debt"]
    undrawn = c.get("undrawn_facilities_aud_m") or 0.0
    ending_strict = opening + fcf_horizon - capex_val
    ending_full = ending_strict + (undrawn if g["count_undrawn_facilities"] else 0.0)
    rescue_gap = max(0.0, -ending_full)
    rescue_ratio = (rescue_gap / mcap_aud_m
                    if mcap_aud_m is not None and mcap_aud_m > 0 else None)
    normal_margin = normal_gold - aisc * (1.0 + infl)
    normal_fcf = prod * 1_000 * normal_margin / 1e6
    if normal_fcf > 0:
        normal_fcf *= (1.0 - g["tax_rate"])
    recovery_years = (rescue_gap / normal_fcf if rescue_gap and normal_fcf > 0
                      else 0.0 if not rescue_gap else math.inf)
    red = rescue_gap > 0 and (
        rescue_ratio is None
        or rescue_ratio > max_rescue_ratio
        or recovery_years > max_recovery_years)
    health = "RED" if red else "AMBER" if rescue_gap else "GREEN"
    detail = {
        "stress_gold_aud": round(stress_gold),
        "margin_aud_oz": round(margin),
        "fcf_annual_aud_m": round(fcf_annual, 1),
        "fcf_horizon_aud_m": round(fcf_horizon, 1),
        "opening_liquidity_aud_m": round(opening, 1),
        "undrawn_aud_m": round(undrawn, 1),
        "committed_capex_aud_m": capex_val,
        "ending_strict_aud_m": round(ending_strict, 1),
        "ending_with_facilities_aud_m": round(ending_full, 1),
        "survives_on_cash_alone": ending_strict >= 0.0,
        "rescue_capital_aud_m": round(rescue_gap, 1),
        "rescue_capital_of_mcap": (round(rescue_ratio, 3)
                                    if rescue_ratio is not None else None),
        "normal_gold_aud": round(normal_gold),
        "normal_fcf_annual_aud_m": round(normal_fcf, 1),
        "recovery_years": (round(recovery_years, 2)
                            if math.isfinite(recovery_years) else None),
    }
    if health == "GREEN":
        reason = (f"GREEN — A${ending_full:,.0f}m headroom after {horizon:g}y at "
                  f"A${stress_gold:,.0f}/oz")
    else:
        years = (f"{recovery_years:.1f}y" if math.isfinite(recovery_years)
                 else "no positive normalised cash flow")
        ratio_text = (f"{rescue_ratio:.0%} of market cap"
                      if rescue_ratio is not None else "market-cap burden unavailable")
        reason = (f"{health} — A${rescue_gap:,.0f}m rescue capital, "
                  f"{ratio_text}, recovery {years}")
    return {"pass": not red, "health": health, "reason": reason,
            "detail": detail, "provisional": False}


def breaking_point(c: dict, spot_aud: float, cfg: dict,
                   mcap_aud_m: float | None = None,
                   step: float = 0.01) -> float | None:
    """Drawdown FROM SPOT at which producer health first turns RED.

    The gate excludes only RED health. This diagnostic deepens the literal spot
    shock until rescue capital exceeds a health threshold; it therefore ranks
    the cushion without adding another construction rule.
    """
    dd = step
    while dd <= 0.95:
        if gate2_survival(c, spot_aud, mcap_aud_m, cfg,
                          stress_gold=spot_aud * (1.0 - dd)).get("pass") is False:
            return dd
        dd += step
    return None


def _gate2_developer(c: dict, mcap_aud_m: float | None, cfg: dict) -> dict:
    """Methodology §3.1 — developers cannot be tested on cash flow.

    D3 replaces a binary funded/unfunded test with a bounded-dilution test,
    because "fully funded" treats a A$50m gap against a A$400m market cap the
    same as a A$300m gap against a A$200m cap. The first is 12% dilution —
    bounded, knowable, priced. The second is a zombie.
    """
    g = cfg["gate2"]
    fails, unresolved, detail = [], [], {}

    stage = c.get("study_stage")
    detail["study_stage"] = stage
    if stage is None:
        fails.append("D1 study stage unsourced")
    elif stage not in g["developer_min_study_stage"]:
        fails.append(f"D1 study stage is {stage}, PFS minimum required")

    land = c.get("approvals_land_secured")
    detail["approvals_land_secured"] = land
    if land is None:
        fails.append("D2 approvals/land status unsourced")
    elif not land:
        fails.append("D2 approvals or land access not secured")

    ev = ((mcap_aud_m + (c.get("net_debt_aud_m") or 0.0))
          if mcap_aud_m is not None else None)
    gap = derive_residual_funding_gap(c, cfg, ev_aud_m=ev)
    detail["residual_funding_gap"] = gap
    if mcap_aud_m and mcap_aud_m > 0:
        limit_ratio = g["developer_max_funding_gap_of_mcap"]
        limit = limit_ratio * mcap_aud_m
        lower = gap["lower_aud_m"]
        upper = gap["upper_aud_m"]
        detail["funding_gap_aud_m"] = gap["value_aud_m"]
        detail["funding_gap_state"] = gap["state"]
        detail["funding_gap_lower_aud_m"] = lower
        detail["funding_gap_upper_aud_m"] = upper
        if upper is not None and upper <= limit:
            detail["funding_gap_of_mcap"] = round(upper / mcap_aud_m, 3)
        elif lower > limit:
            ratio = lower / mcap_aud_m
            detail["funding_gap_of_mcap"] = round(ratio, 3)
            fails.append(f"D3 funding gap at least {ratio:.0%} of market cap, limit "
                         f"{limit_ratio:.0%}")
        else:
            hi = "unbounded" if upper is None else f"A${upper:,.0f}m"
            unresolved.append(
                f"D3 residual funding gap spans A${lower:,.0f}m–{hi} around the "
                f"A${limit:,.0f}m limit")
    else:
        fails.append("D3 market cap unavailable — gap cannot be sized")

    if fails:
        reason = "; ".join(fails + unresolved)
        return {"pass": False, "reason": reason, "detail": detail,
                "provisional": False}
    if unresolved:
        return {"pass": None, "reason": "; ".join(unresolved), "detail": detail,
                "provisional": False}
    return {"pass": True, "reason": "passes D1 study stage, D2 approvals and land, "
                                    "D3 bounded dilution",
            "detail": detail, "provisional": False}


def gate3_tradability(c: dict, spread: dict | None, cfg: dict) -> dict:
    """Methodology §4 — binary tradability gate on quoted spread.

    Spread-based rather than market-cap-based by decision: market cap is a proxy
    for liquidity and a bad one in this cohort, where a A$400m developer can
    quote tighter than a A$2bn producer with a concentrated register.

    Reads the MEDIAN daily time-averaged quoted spread over SPREAD_DURATION of
    regular trading hours, not a live snapshot. See _spread_history for why: an
    after-hours snapshot overstates the spread by an order of magnitude and
    would fail most of the book on an artifact.

    A missing measurement returns pass=None, not pass=True. The Gate 2 precedent
    sets the rule: for a gate, an absent input makes the test easier, so a name
    that has never been tested must not be reported as one that passed. Nothing
    is rejected on absence — that would empty the index on a data entitlement —
    but the run says so out loud.
    """
    limits = cfg["gates"]
    cap = (limits["developer_max_spread_pct"] if c.get("sleeve") == "developer"
           else limits["producer_max_spread_pct"])

    if not spread or spread.get("median_pct") is None:
        return {"pass": None, "limit_pct": cap, "spread_pct": None,
                "reason": "no RTH spread history — NOT TESTED"}

    med, p90 = spread["median_pct"], spread.get("p90_pct")
    out = {"limit_pct": cap, "spread_pct": med, "p90_pct": p90,
           "n_days": spread.get("n_days")}
    if med > cap:
        return {**out, "pass": False,
                "reason": f"median spread {med:.2f}% above {cap:.1f}% limit "
                          f"over {spread['n_days']} sessions"}
    # Passing on the median while breaching on p90 is a real distinction: the
    # name trades acceptably in calm markets and not necessarily in the
    # conditions that would force a rebalance. Passed, but said out loud.
    strained = p90 is not None and p90 > cap
    return {**out, "pass": True, "strained": strained,
            "reason": (f"median spread {med:.2f}% within {cap:.1f}%"
                       + (f" — but p90 {p90:.2f}% breaches it" if strained else ""))}


# ──────────────────────────────────────────────────────────────────────────
# Weighting
# ──────────────────────────────────────────────────────────────────────────

def compute_gate1_cap_weights(constituents: list[dict], prices: dict,
                              meta: dict) -> tuple[list[dict], list[dict]]:
    """Build the §14 variant: Gate 1, top-N selection, then cap weighting.

    This branch deliberately stops before every later SJGV rule. It does not
    read Gate 2, Gate 3, statement currency, the ounce ledger, enterprise value,
    or the §8 caps. The largest configured number of eligible companies are
    retained by full market capitalisation and renormalised. A mixed-jurisdiction
    company may survive under §2.4's entity-level limit; once admitted, its
    *full* equity market capitalisation is used. Multiplying market cap by the
    eligible-ounce share would create an undocumented fundamental tilt rather
    than a market-cap index.

    ``shares_out_m`` is total issued shares, so this is full market-cap
    weighting. It is not described as free-float adjusted: the data layer has no
    sourced foreign-inclusion/free-float factor, and derive-or-fail forbids
    manufacturing one.
    """
    variant = meta["variants"]["gate1_cap"]
    if variant["weighting"] != "full_market_cap":
        raise ValueError(
            f"variants.gate1_cap.weighting is {variant['weighting']!r}; "
            "the §14 implementation supports 'full_market_cap' and nothing else")
    max_constituents = variant["max_constituents"]
    if (not isinstance(max_constituents, int) or isinstance(max_constituents, bool)
            or max_constituents <= 0):
        raise ValueError(
            "variants.gate1_cap.max_constituents must be a positive integer")

    max_ineligible = meta["gates"]["max_ineligible_nav_share"]
    rows: list[dict] = []
    rejected: list[dict] = []

    for c in constituents:
        ticker = c["ticker"]

        def reject(reason: str) -> None:
            rejected.append({
                "ticker": ticker,
                "name": c["name"],
                "sleeve": c["sleeve"],
                "reason": reason,
            })

        eligible_share = c.get("eligible_ounce_share")
        if eligible_share is None:
            reject("GATE 1 — eligible_ounce_share missing")
            continue
        if not 0.0 <= eligible_share <= 1.0:
            reject(f"GATE 1 — eligible_ounce_share {eligible_share!r} outside [0, 1]")
            continue
        if eligible_share == 0.0:
            reject("GATE 1 — no ounces in a Tier A jurisdiction")
            continue

        ineligible_nav_share = c.get("ineligible_nav_share")
        if ineligible_nav_share is None:
            reject("GATE 1 — ineligible_nav_share missing; entity cap is untested")
            continue
        if not 0.0 <= ineligible_nav_share <= 1.0:
            reject(f"GATE 1 — ineligible_nav_share {ineligible_nav_share!r} outside [0, 1]")
            continue
        if ineligible_nav_share > max_ineligible:
            reject(
                f"GATE 1 — ineligible NAV {ineligible_nav_share:.0%} above "
                f"{max_ineligible:.0%} entity cap (§2.4)")
            continue

        price = (prices.get(ticker) or {}).get("price")
        shares = c.get("shares_out_m")
        if not shares or not price:
            missing = "share count" if not shares else "market price"
            reject(f"{missing} unavailable — market capitalisation cannot be derived")
            continue
        market_cap = shares * price
        if market_cap <= 0:
            reject(f"non-positive market capitalisation (A${market_cap:,.0f}m)")
            continue

        rows.append({
            "ticker": ticker,
            "name": c["name"],
            "sleeve": c["sleeve"],
            "weight": 0.0,
            "market_cap_aud_m": market_cap,
            "mcap_aud_m": market_cap,
            "price_aud": price,
            "shares_out_m": shares,
            "eligible_ounce_share": eligible_share,
            "ineligible_nav_share": ineligible_nav_share,
            "shares_src": "data",
        })

    rows.sort(key=lambda row: (-row["market_cap_aud_m"], row["ticker"]))
    for rank, row in enumerate(rows, start=1):
        row["market_cap_rank"] = rank
    omitted = rows[max_constituents:]
    rows = rows[:max_constituents]
    for row in omitted:
        rejected.append({
            "ticker": row["ticker"],
            "name": row["name"],
            "sleeve": row["sleeve"],
            "market_cap_aud_m": row["market_cap_aud_m"],
            "market_cap_rank": row["market_cap_rank"],
            "reason": (
                f"CONSTITUENT LIMIT — market-cap rank {row['market_cap_rank']} "
                "is outside the "
                f"largest {max_constituents} Gate-1-eligible companies"),
        })

    total_market_cap = sum(r["market_cap_aud_m"] for r in rows)
    if total_market_cap > 0:
        for row in rows:
            row["weight"] = row["market_cap_aud_m"] / total_market_cap
    return rows, rejected


def compute_raw_weights(constituents: list[dict], prices: dict,
                        risk: dict, gold_aud: float, meta: dict,
                        anchor_gold: float | None = None,
                        spreads: dict | None = None,
                        navs: dict[str, dict] | None = None,
                        as_of: str | None = None,
                        ) -> tuple[list[dict], list[dict]]:
    """Apply the §7 formula — claimed unhedged ounces ÷ all-in EV. Returns
    (weighted rows, rejected rows).

    There is nothing between the ledger and the weight. No score, no tilt, no
    risk denominator. A name's weight is the share of the index's total claimed
    ounces that its ounces represent, per dollar of enterprise value paid for
    them, and that is the entire statement of the strategy.

    gold_aud is spot, used for Gate 2, the breaking-point diagnostic and the §9
    NAV report. anchor_gold is the conservative reporting deck; it does not
    affect eligibility or weights.

    `navs` is the §9 NAV model output. It is carried onto the rows for reporting
    and is never read by the weight — see nav_model.py.

    `as_of` dates the §6.4 statement-currency gate. Callers pass the data layer's
    sourcing date so the same data always produces the same book.
    """
    anchor_gold = anchor_gold if anchor_gold is not None else gold_aud
    conf = confidence_weights(meta)
    hedge_years = meta["confidence_weights"]["hedge_horizon_years"]
    max_statement_age = meta["gates"]["max_resource_statement_age_months"]
    # §6.4 measures document age against the date the data layer was sourced, not
    # against the wall clock, so a build is reproducible: replaying today's data
    # in six months must reject what it rejected today.
    as_of = date.fromisoformat(as_of) if as_of else datetime.now(timezone.utc).date()
    rows: list[dict] = []
    rejected: list[dict] = []
    floor = meta["gates"]["purity_floor_gold_nav_share"]
    max_inelig = meta["gates"]["max_ineligible_nav_share"]

    for c in constituents:
        sym = c["ticker"]
        reject = lambda why: rejected.append(  # noqa: E731
            {"ticker": sym, "name": c["name"], "sleeve": c["sleeve"], "reason": why})

        delivery = c.get("_guidance_delivery")
        if delivery and delivery.get("portfolio_treatment") == "EXCLUDE":
            reject(f"EXECUTION DELIVERY — HARD FAIL ({delivery.get('original_failures')}/"
                   f"{delivery.get('rated_years')} original, "
                   f"{delivery.get('revised_failures')}/"
                   f"{delivery.get('rated_years')} revised)")
            continue

        # §5 purity is a GATE and only a gate. The continuous ×gold-share
        # multiplier that used to sit beside it moved the book by 0.22pp on
        # average and is deleted: either these are gold ounces or they are not.
        purity = c.get("gold_nav_share")
        if purity is None:
            reject("gold_nav_share missing — purity gate cannot be evaluated")
            continue
        if purity < floor:
            reject(f"purity {purity:.0%} below {floor:.0%} floor (§5)")
            continue

        inelig = c.get("ineligible_nav_share")
        if inelig is not None and inelig > max_inelig:
            reject(f"ineligible NAV {inelig:.0%} above {max_inelig:.0%} cap (§2.4)")
            continue

        # §6.4 — the claim must be current before it can be counted. Ahead of
        # the ledger, because a stale statement is not a smaller claim to be
        # discounted, it is a claim that has not been restated. Not numbered as a
        # fourth gate: Gates 1–3 each name a way of losing the money, and this
        # names a way of not knowing what you own.
        current, age_months, why = statement_currency(c, as_of, max_statement_age)
        if not current:
            reject(f"STALE (§6.4) — {why}")
            continue

        ledger, why = ounce_ledger(c, conf, hedge_years)
        if ledger is None:
            reject(why)
            continue
        oz = ledger["claimed_moz"]

        pq = prices.get(sym) or {}
        px = pq.get("price")
        # Data layer only — the IBKR route was removed in TWS API 10.47; see the
        # note above _history. EV therefore pairs a live price with a share count
        # as of its filing date, so a name that has issued stock since then is
        # understated. Which filing is recorded per field in companies.json.
        shares = c.get("shares_out_m")
        shares_src = "data"
        if not shares or not px:
            missing = "share count" if not shares else "live price"
            reject(f"{missing} unavailable — EV cannot be computed "
                   f"(no API source since TWS 10.47; needs sourcing from filings)")
            continue
        mcap_aud_m = shares * px
        net_debt = c.get("net_debt_aud_m")
        if net_debt is None and c.get("sleeve") != "developer":
            reject("GATE 2 — net debt unsourced — producer health cannot be tested")
            continue
        # Preserve the developer path: D3's directional funding evidence, not a
        # newly introduced net-debt rule, decides its current exclusions.
        if net_debt is None:
            net_debt = 0.0
        ev_aud_m = mcap_aud_m + net_debt
        if ev_aud_m <= 0:
            reject(f"non-positive EV (A${ev_aud_m:,.0f}m) — net cash exceeds market cap")
            continue

        # §3 — a facility that lapses inside the stress window is not stress
        # liquidity. Applied to the record BEFORE the gate so that every probe
        # downstream — the breaking point and invariance sweeps — sees the same
        # corrected liquidity.
        creditable, facility_note = creditable_undrawn(c, meta, as_of)
        if facility_note:
            c = {**c, "undrawn_facilities_aud_m": creditable}

        # ── GATE 2 (§3) — binary, lexicographic, before any scoring ──────────
        # Sits here rather than earlier only because the developer variant needs
        # market cap to size the funding gap. Nothing downstream can buy a name
        # past a Gate 2 failure: a name that fails is rejected outright, never
        # weighted down.
        stress_basis = meta["gate2"]["stress_price_basis"]
        if stress_basis != "spot":
            raise ValueError(f"gate2.stress_price_basis is {stress_basis!r}; "
                             "the health check implements a literal drawdown "
                             "from spot")
        g2 = gate2_survival(c, gold_aud, mcap_aud_m, meta)
        g2["facility_note"] = facility_note
        if g2["pass"] is not True:
            reject(f"GATE 2 — {g2['reason']}")
            continue

        # §3.2 — the same doctrine, for an input that IS present but was recorded
        # at the midpoint of a range the issuer published. Absence was already
        # caught above; a published range was not, and it is the same question.
        g2["range_invariance"] = gate2_range_invariance(
            c, disclosed_ranges(c), gold_aud, mcap_aud_m, meta)
        if not g2["range_invariance"]["ok"]:
            reject(f"GATE 2 UNRESOLVED — {g2['range_invariance']['reason']}")
            continue

        # ── GATE 3 (§4) — tradability, binary ────────────────────────────────
        g3 = gate3_tradability(c, (spreads or {}).get(sym), meta)
        if g3["pass"] is False:
            reject(f"GATE 3 — {g3['reason']}")
            continue

        # ── The price of the claim (§7) ──────────────────────────────────────
        # Established producers use standard EV. Their execution-capital data
        # remains visible as provenance/reporting but is neither required nor
        # added. Near-producers and developers still require and add gross
        # remaining execution capital; funding never reduces that denominator.
        if c.get("sleeve") == "producer":
            execution = _capital_evidence(c, EXECUTION_CAPITAL_FIELD, meta, as_of)
            reported_execution_capital = c.get(EXECUTION_CAPITAL_FIELD)
            denominator_execution_capital = None
            all_in_ev_aud_m = ev_aud_m
        else:
            execution = execution_capital_ledger(c, ev_aud_m, meta, as_of)
            if not execution.get("ok"):
                reject(f"EXECUTION CAPITAL — {execution['reason']}")
                continue
            reported_execution_capital = execution["effective_aud_m"]
            denominator_execution_capital = execution["effective_aud_m"]
            all_in_ev_aud_m = ev_aud_m + denominator_execution_capital
        residual_gap = (g2.get("detail", {}).get("residual_funding_gap")
                        if c.get("sleeve") == "developer" else None)

        # Risk stats are diagnostics now, so their absence no longer excludes a
        # name. Under the old formula σ_idio was the weight denominator, which
        # meant a name with under 60 usable bars could not be held at all — a
        # newly-listed developer was unweightable for a reason that had nothing
        # to do with how many ounces it owned.
        rstat = risk.get(sym) or {}
        nav_rec = (navs or {}).get(sym) or {}

        rows.append({
            "ticker": sym, "name": c["name"], "sleeve": c["sleeve"],
            "claimed_moz": oz, "ledger": ledger, "purity": purity,
            "statement_age_months": age_months,
            "ev_aud_m": ev_aud_m, "mcap_aud_m": mcap_aud_m, "price_aud": px,
            "remaining_execution_capex_aud_m": reported_execution_capital,
            "execution_capital_in_denominator_aud_m": denominator_execution_capital,
            "execution_capital": execution,
            "residual_funding_gap_aud_m": (
                residual_gap.get("value_aud_m") if residual_gap else None),
            "residual_funding_gap_state": (
                residual_gap.get("state") if residual_gap else None),
            "all_in_ev_aud_m": all_in_ev_aud_m,
            # Output aliases retained for consumers of pre-migration build JSON;
            # neither is an input and neither restores the deleted data field.
            "funded_ev_aud_m": all_in_ev_aud_m,
            "funding_gap_aud_m": (
                residual_gap.get("value_aud_m") if residual_gap else None),
            "aud_per_oz": all_in_ev_aud_m / oz,
            "aud_per_oz_ex_execution_capital": ev_aud_m / oz,
            "aud_per_oz_ex_gap": ev_aud_m / oz,
            "beta_gold": rstat.get("beta_gold"), "r2": rstat.get("r2"),
            "beta_contemporaneous": rstat.get("beta_contemporaneous"),
            "beta_estimator": rstat.get("estimator"),
            "sigma_idio": rstat.get("sigma_idio"),
            "risk_error": rstat.get("error"),
            "spread_pct": g3.get("spread_pct"),
            "spread_p90_pct": g3.get("p90_pct"),
            "raw": oz / all_in_ev_aud_m,
            "shares_src": shares_src,
            "gate2": g2, "gate3": g3,
            "breaking_point": breaking_point(c, gold_aud, meta, mcap_aud_m),
            "reserve_price_aud": c.get("reserve_price_aud"),
            "resource_price_aud": c.get("resource_price_aud"),
            "mr_total_moz": c.get("mr_total_moz"),
            # §9 NAV model — reporting only, never read by the weight.
            "nav_aud_m": nav_rec.get("nav_aud_m"),
            "p_nav": (mcap_aud_m / nav_rec["nav_aud_m"]
                      if nav_rec.get("nav_aud_m") else None),
            "modelled_delta": nav_rec.get("modelled_delta"),
            "modelled_gamma": nav_rec.get("modelled_gamma"),
            "nav_up_capture": nav_rec.get("nav_up_capture"),
            "nav_down_capture": nav_rec.get("nav_down_capture"),
            "nav_asymmetry": nav_rec.get("nav_asymmetry"),
            "deck_sensitivity": nav_rec.get("deck_sensitivity"),
            "advt_shares_m": c.get("advt_shares_m"),
            # §8.1. Sourced quantity, derived judgement — never a hand-set flag.
            "largest_asset_pp_share": c.get("largest_asset_pp_share"),
            "single_asset": derive_single_asset(c, meta),
            "guidance_delivery": delivery,
        })

    total = sum(r["raw"] for r in rows)
    for r in rows:
        r["weight"] = r["raw"] / total if total > 0 else 0.0
    return rows, rejected


def _cap_and_redistribute(rows: list[dict], caps: dict[str, float]) -> None:
    """Cap names and push the excess pro rata onto the uncapped, until no cap is
    breached. In place on rows['weight'].

    The loop is still here because redistribution can push a previously-free
    name over its own cap, but it now converges in a pass or two: the ceilings
    are constants. Were they not — as with an idiosyncratic-variance
    ceilings moved with the weights they constrained, so this ran inside a
    200-iteration fixed point that had its own non-convergence warning.
    """
    for _ in range(100):
        breached = [r for r in rows if r["weight"] > caps[r["ticker"]] + 1e-12]
        if not breached:
            return
        excess = 0.0
        for r in breached:
            excess += r["weight"] - caps[r["ticker"]]
            r["weight"] = caps[r["ticker"]]
        free = [r for r in rows if r["weight"] < caps[r["ticker"]] - 1e-12]
        pool = sum(r["weight"] for r in free)
        if not free or pool <= 0:
            # Every name is at its cap; renormalise and accept the shortfall.
            tot = sum(r["weight"] for r in rows)
            if tot > 0:
                for r in rows:
                    r["weight"] /= tot
            return
        for r in free:
            r["weight"] += excess * (r["weight"] / pool)


def effective_n(rows: list[dict]) -> float:
    ssq = sum(r["weight"] ** 2 for r in rows)
    return 1.0 / ssq if ssq > 0 else 0.0


def derive_single_asset(c: dict, meta: dict) -> bool | None:
    """§8.1 — is one asset substantially the whole company? TRI-STATE.

        True   largest_asset_pp_share >= constraints.single_asset_pp_share_threshold
        False  a sourced share below the threshold — a RESULT, not an absence
        None   no sourced share: UNTESTED, and the tighter cap cannot be applied

    Derived, not read. A hand-set boolean per name is a hand-set judgement call
    per name, seventeen times over, and none of them is visible to the config
    audit or perturbable by tools/sensitivity.py. A sourced share against one
    declared threshold moves the judgement into config.json where it can be
    argued with, and leaves the data layer holding only a measured quantity.

    THE `None` IS LOAD-BEARING. `largest_asset_pp_share` absent must not be read
    as 0.0: that derives False, silently restores the looser 15% name cap, and
    reports it as a test that PASSED. This is the silent-zero trap
    pointed the dangerous way — the direction where absence makes a test easier
    — and it is the same failure Gate 3's two unread spread limits were. A test
    that never ran is not a test that passed. `_assert_single_asset_tristate()`
    asserts it on every build rather than trusting this docstring.
    """
    share = c.get("largest_asset_pp_share")
    if share is None:
        return None
    return share >= meta["constraints"]["single_asset_pp_share_threshold"]


def _assert_single_asset_tristate(meta: dict) -> None:
    """Prove the absent-share case derives None rather than False.

    Cheap, and it runs on every build. The property it protects is one line of
    code away from silently reversing — `c.get("largest_asset_pp_share", 0.0)`
    or a `float(...)` coercion would each turn UNTESTED into a passed test on
    every unsourced name at once.
    """
    th = meta["constraints"]["single_asset_pp_share_threshold"]
    # A share is a share. A threshold above 1.0 would disable the cap silently
    # — every name multi-asset, every ceiling back at 15%, and nothing in the
    # output saying so — which is the same failure as an absence reading False.
    if not 0.0 < th <= 1.0:
        raise ValueError(
            f"constraints.single_asset_pp_share_threshold is {th}; it is a share "
            f"of reserves and must lie in (0, 1]. Above 1.0 no company can ever "
            f"flag and the §8.1 cap is disabled without saying so.")
    cases = [({}, None), ({"largest_asset_pp_share": None}, None),
             ({"largest_asset_pp_share": 0.0}, False),
             ({"largest_asset_pp_share": th - 1e-9}, False),
             ({"largest_asset_pp_share": th}, True),
             ({"largest_asset_pp_share": 1.0}, True)]
    for rec, want in cases:
        got = derive_single_asset(rec, meta)
        if got is not want:
            raise AssertionError(
                f"derive_single_asset({rec}) returned {got!r}, expected {want!r}. "
                f"An absent largest_asset_pp_share MUST derive None (UNTESTED); "
                f"deriving False would restore the 15% cap and report it as a "
                f"test that passed (§8.1).")


def single_asset_names(rows: list[dict]) -> tuple[list[str], list[str]]:
    """Which constituents are one mine, and which could not be told either way.

    A single-asset company is not a diversification question, it is an
    impairment question: one fault, one flood, one tenement dispute and the
    claim is gone permanently rather than marked down. §0's objective already
    contains P(permanent impairment) ≈ 0, which is where the tighter cap in
    §8.1 comes from — it is derived from the objective, unlike the
    idiosyncratic-variance cap it replaces, which was calibrated on daily price
    noise and appeared nowhere in the mandate.

    `single_asset` is DERIVED by derive_single_asset() from the sourced
    `largest_asset_pp_share` against a declared threshold, and is tri-state.
    Absent means UNTESTED and is reported as such, never read as False — the
    Gate 3 precedent: a test that never ran is not a test that passed. The old
    `single_asset_shares` {asset: share} map two revisions back was unsourced
    for all seventeen names and fed a 20% cap sitting ABOVE the 15% name cap, so
    it could not bind on one company however concentrated. This one can, and as
    at 18 Aug 2026 it binds on two: PNR and CYL.
    """
    flagged = [r["ticker"] for r in rows if r.get("single_asset") is True]
    untested = [r["ticker"] for r in rows if r.get("single_asset") is None]
    return sorted(flagged), sorted(untested)


def capacity(rows: list[dict], aum_aud: float, cfg: dict) -> dict:
    """§4.3 — can each target position be built, and at what AUM does it stop?

    Days to build = position notional ÷ (participation × median daily turnover).
    ADVT is the ASX's own 90-session average volume (companies.json
    advt_shares_m, sourced by tools/asx.py) priced at the build-time price.

    The pass/fail is nearly useless on its own: §4.3 already says the test is
    inert at €1m and the whole universe is trivially buildable. What is worth
    knowing is the AUM at which the FIRST name breaches, because that is the
    methodology's capacity — §4.3 estimates A$50–100m and this measures it.
    """
    g = cfg["gates"]
    max_days = g["capacity_max_days_advt"]
    participation = g["capacity_max_participation"]

    names, unmeasured, ceilings = [], [], []
    for r in rows:
        advt_shares_m = r.get("advt_shares_m")
        if not advt_shares_m or not r.get("price_aud") or r["weight"] <= 0:
            unmeasured.append(r["ticker"])
            continue
        advt_aud_m = advt_shares_m * r["price_aud"]
        absorbable_aud_m = advt_aud_m * participation * max_days
        # AUM at which this name alone exhausts the limit.
        ceiling_aud_m = absorbable_aud_m / r["weight"]
        days = (aum_aud / 1e6 * r["weight"]) / (advt_aud_m * participation)
        names.append({"ticker": r["ticker"], "weight": r["weight"],
                      "advt_aud_m": advt_aud_m, "days_to_build": days,
                      "ceiling_aud_m": ceiling_aud_m,
                      "pass": days <= max_days})
        ceilings.append((ceiling_aud_m, r["ticker"]))

    ceilings.sort()
    return {
        "max_days_advt": max_days,
        "participation": participation,
        "aum_aud": aum_aud,
        "names": sorted(names, key=lambda x: -x["days_to_build"]),
        "unmeasured": unmeasured,
        "binding_ticker": ceilings[0][1] if ceilings else None,
        "capacity_aud_m": ceilings[0][0] if ceilings else None,
        "breaches": [n["ticker"] for n in names if not n["pass"]],
    }


def apply_constraints(rows: list[dict], meta: dict) -> dict:
    """§8.1 — three caps, all derived from P(permanent impairment) ≈ 0.

        max_single_name             15%   no one company is the index
        max_single_asset_name      7.5%   tighter where one mine is the company
        max_guidance_delivery_name   5%   repeated delivery weakness
        max_developer_sleeve        15%   pre-production names can fail outright
        max_developer_single_name    5%

    Nothing here is a risk-model output. Each cap answers the same question —
    how much of the claim can one uncorrelated operational failure destroy — and
    that question is in the objective function. What is NOT here any more:

    * the idiosyncratic-variance cap, which moved Pinnacle 14.96% → 9.23%, five
      times the entire cross-sectional influence of the convexity score it sat
      beside, on a criterion found nowhere in §0. It pinned three names at 30.5%
      of the book so their weights came from a variance estimate rather than
      from their ounces.
    * the minimum-effective-N ratchet, which tightened the name cap until a
      diversification statistic cleared a floor. Eff N is still reported. It is
      an observation about the book, not a target the book is bent to hit.

    Caps are applied to convergence with the excess pushed pro rata onto the
    uncapped, which is a fixed point in one pass because the ceilings are
    constants — the old inner loop existed only because the idio ceilings moved
    with the weights they constrained.
    """
    con = meta["constraints"]
    notes: list[str] = []
    single = con["max_single_name"]
    single_asset_cap = con["max_single_asset_name"]
    delivery_cap = con["max_guidance_delivery_name"]
    flagged, untested = single_asset_names(rows)

    if not rows:
        return {"effective_n": 0.0, "notes": ["no constituents to constrain"],
                "single_name_cap": single, "single_asset_cap": single_asset_cap,
                "single_asset_names": [], "single_asset_untested": []}

    dev_total = sum(r["weight"] for r in rows if r["sleeve"] == "developer")
    if dev_total > con["max_developer_sleeve"] and dev_total > 0:
        scale = con["max_developer_sleeve"] / dev_total
        freed = dev_total - con["max_developer_sleeve"]
        for r in rows:
            if r["sleeve"] == "developer":
                r["weight"] *= scale
        others = [r for r in rows if r["sleeve"] != "developer"]
        pool = sum(r["weight"] for r in others)
        if pool > 0:
            for r in others:
                r["weight"] += freed * (r["weight"] / pool)
        notes.append(
            f"developer sleeve scaled {dev_total:.1%} → {con['max_developer_sleeve']:.1%}")

    def ceiling(r: dict) -> float:
        if r["sleeve"] == "developer":
            return min(single, con["max_developer_single_name"])
        cap = single_asset_cap if r.get("single_asset") is True else single
        if (r.get("guidance_delivery") or {}).get("portfolio_treatment") == "CAP":
            cap = min(cap, delivery_cap)
        return cap

    caps = {r["ticker"]: ceiling(r) for r in rows}
    producer_capacity = sum(caps[r["ticker"]] for r in rows
                            if r["sleeve"] != "developer")
    developer_capacity = min(
        con["max_developer_sleeve"],
        sum(caps[r["ticker"]] for r in rows if r["sleeve"] == "developer"),
    )
    feasible_capacity = producer_capacity + developer_capacity
    if feasible_capacity < 1.0 - 1e-12:
        raise ValueError(
            "constraint set is infeasible for the surviving universe: name and "
            f"sleeve caps provide only {feasible_capacity:.1%} total capacity")
    precap = {r["ticker"]: r["weight"] for r in rows}
    _cap_and_redistribute(rows, caps)
    breaches = [r["ticker"] for r in rows
                if r["weight"] > caps[r["ticker"]] + 1e-9]
    if breaches:
        raise AssertionError("cap redistribution left breaches: "
                             + ", ".join(sorted(breaches)))

    bound = [r["ticker"] for r in rows
             if precap[r["ticker"]] > caps[r["ticker"]] + 1e-9]
    if bound:
        detail = ", ".join(
            f"{t} {precap[t]:.1%}→{caps[t]:.0%}" for t in sorted(bound))
        notes.append(f"name caps bound on {len(bound)}: {detail} (§8.1/§8.2)")

    if flagged:
        th = con["single_asset_pp_share_threshold"]
        detail = ", ".join(
            f"{t} {next(r['largest_asset_pp_share'] for r in rows if r['ticker'] == t):.0%}"
            for t in flagged)
        notes.append(
            f"single-asset companies at the {single_asset_cap:.0%} cap: {detail} "
            f"— reserve share at one asset at or above the {th:.0%} threshold, "
            f"so one mine carries the claim (§8.1, §11)")
    if untested:
        notes.append(
            f"single-asset status UNTESTED for {len(untested)}/{len(rows)}: "
            f"{', '.join(untested)} — `largest_asset_pp_share` unsourced, so the "
            f"tighter cap could not be applied and these names ran at {single:.0%}")

    dev_final = sum(r["weight"] for r in rows if r["sleeve"] == "developer")
    if dev_total > 0:
        per_name_bound = any(
            r["sleeve"] == "developer"
            and abs(r["weight"] - con["max_developer_single_name"]) < 1e-9
            for r in rows)
        if abs(dev_final - dev_total) < 1e-9:
            notes.append(
                f"developer sleeve {dev_final:.1%} — under the "
                f"{con['max_developer_sleeve']:.0%} cap, sized to qualifiers "
                f"not forced (§4.1)")
        else:
            why = (f"the {con['max_developer_single_name']:.0%} per-name developer cap"
                   if per_name_bound else "the caps above")
            notes.append(
                f"developer sleeve {dev_total:.1%} raw → {dev_final:.1%} shipped, "
                f"bound by {why}, not by the "
                f"{con['max_developer_sleeve']:.0%} sleeve cap (§4.1)")

    return {"effective_n": effective_n(rows), "notes": notes,
            "single_name_cap": single, "single_asset_cap": single_asset_cap,
            "guidance_delivery_cap": delivery_cap,
            "single_asset_names": flagged, "single_asset_untested": untested,
            "precap_weights": precap}


def portfolio_stats(rows: list[dict], meta: dict) -> dict:
    """What the book is, measured. Nothing here is a target except beta_target,
    and that is a band the mandate is checked against rather than optimised to.
    """
    w = {r["ticker"]: r["weight"] for r in rows}
    tot = sum(w.values()) or 1.0

    def wavg(key: str) -> float | None:
        vals = [(r["weight"], r[key]) for r in rows if r.get(key) is not None]
        if not vals:
            return None
        wsum = sum(x for x, _ in vals)
        return sum(x * y for x, y in vals) / wsum if wsum > 0 else None

    def coverage(key: str) -> float:
        return sum(r["weight"] for r in rows if r.get(key) is not None) / tot

    regressed = wavg("beta_gold")
    lo, hi = meta["objective"]["beta_target"]

    # The index's own price per ounce of claim: total EV bought per ounce
    # claimed, weighted as the book actually holds them. This is the headline
    # construction number.
    oz_per_dollar = sum(r["weight"] * r["claimed_moz"] / r["all_in_ev_aud_m"]
                        for r in rows)

    # The same names on market-cap weights, same formula. This is the only
    # comparator the headline number means anything against, and until 19 Aug
    # 2026 it was maintained BY HAND: this comment said A$910, README.md said
    # A$917 and an in-flight PR said A$915, while the true figure was A$892.
    # Four values, none of them derived from anything. A published number with
    # no consumer in the engine is the defect §12.3 exists to prevent, and it
    # applies to outputs and not just to parameters. Computed here so it cannot
    # drift again.
    tot_mcap = sum(r["mcap_aud_m"] for r in rows if r.get("mcap_aud_m"))
    capw_oz_per_dollar = (
        sum((r["mcap_aud_m"] / tot_mcap) * r["claimed_moz"] / r["all_in_ev_aud_m"]
            for r in rows if r.get("mcap_aud_m"))
        if tot_mcap > 0 else 0.0)

    # Which tranche the index's claim actually comes from. Each tranche is taken
    # AFTER its confidence weight, so the three shares sum to 1 and describe the
    # claim rather than the gross resource — the point of the mix is how much of
    # what we own is already in the money.
    w_pp, w_mi, w_inf = confidence_weights(meta)
    contrib = {
        "reserves": sum(r["weight"] * (r["ledger"]["elig_pp_moz"]
                                       - r["ledger"]["hedged_moz"]) * w_pp
                        for r in rows),
        "mi_non_reserve": sum(r["weight"] * r["ledger"]["elig_mi_moz"] * w_mi
                              for r in rows),
        "inferred": sum(r["weight"] * r["ledger"]["elig_inferred_moz"] * w_inf
                        for r in rows),
    }
    claim_tot = sum(contrib.values()) or 1.0
    ledger_mix = {k: v / claim_tot for k, v in contrib.items()}
    # Two separate shrinkages, reported separately because they mean different
    # things. The first is ounces we do not own — wrong sovereign, or already
    # sold. The second is ounces we own but discount for confidence, and those
    # are still there: an Inferred ounce counted at 0.2 is the option, not a
    # write-off. Netting them into one number would hide that.
    gross_tot = sum(r["weight"] * r["ledger"]["gross_moz"] for r in rows) or 1.0
    owned = sum(r["weight"] * (r["ledger"]["elig_pp_moz"] - r["ledger"]["hedged_moz"]
                               + r["ledger"]["elig_mi_moz"]
                               + r["ledger"]["elig_inferred_moz"]) for r in rows)
    ledger_mix["not_ours_share_of_gross"] = 1.0 - owned / gross_tot
    ledger_mix["confidence_discount_of_owned"] = (
        1.0 - claim_tot / owned) if owned > 0 else None

    return {
        "effective_n": effective_n(rows),
        "n_constituents": len(rows),
        "portfolio_beta_gold": regressed,
        "beta_coverage": coverage("beta_gold"),
        "portfolio_modelled_delta": wavg("modelled_delta"),
        "portfolio_beta_contemporaneous": wavg("beta_contemporaneous"),
        "beta_target": [lo, hi],
        "beta_in_target": (lo <= regressed <= hi) if regressed is not None else None,
        "wavg_r2": wavg("r2"),
        "wavg_sigma_idio": wavg("sigma_idio"),
        "wavg_p_nav": wavg("p_nav"),
        "wavg_deck_sensitivity": wavg("deck_sensitivity"),
        "aud_per_claimed_oz": (1.0 / oz_per_dollar) if oz_per_dollar > 0 else None,
        "capweighted_aud_per_claimed_oz": ((1.0 / capw_oz_per_dollar)
                                           if capw_oz_per_dollar > 0 else None),
        "ledger_mix": ledger_mix,
        "max_statement_age_months": meta["gates"]["max_resource_statement_age_months"],
        "oldest_statement_months": max(
            (r["statement_age_months"] for r in rows
             if r.get("statement_age_months") is not None), default=None),
        "developer_sleeve": sum(r["weight"] for r in rows
                                if r["sleeve"] == "developer") / tot,
        "top_weight": max(w.values()) if w else 0.0,
    }


# ──────────────────────────────────────────────────────────────────────────
# Basket sizing
# ──────────────────────────────────────────────────────────────────────────

def _recompute(row: dict, commission_rate: float) -> None:
    row["notional_aud"] = row["shares"] * row["price_aud"]
    row["commission_aud"] = row["notional_aud"] * commission_rate
    row["spend_aud"] = row["notional_aud"] + row["commission_aud"]
    row["spend_eur"] = row["spend_aud"] / row["euraud"]


def _reallocate_residual(basket: list[dict], amount_eur: float,
                         euraud: float, commission_rate: float) -> int:
    """Greedy: award +1 share at a time to the most under-allocated name that
    can still fit one. Never adds to a name already at or over its target, so
    rounding residue can't drift the basket past its weights."""
    actionable = [r for r in basket if r.get("shares") is not None]
    added = 0
    while True:
        remaining = amount_eur - sum(r["spend_eur"] for r in actionable)
        candidates = []
        for r in actionable:
            deficit = r["alloc_eur"] - r["spend_eur"]
            if deficit <= 0:
                continue
            cost_eur = r["price_aud"] * (1 + commission_rate) / euraud
            if cost_eur <= remaining:
                candidates.append((deficit, r))
        if not candidates:
            return added
        candidates.sort(key=lambda t: -t[0])
        r = candidates[0][1]
        r["shares"] += 1
        _recompute(r, commission_rate)
        added += 1


def size_basket(rows: list[dict], amount_eur: float, euraud: float,
                commission_rate: float) -> list[dict]:
    """Floor allocation per name, then greedy residual reallocation.

    euraud is AUD per EUR.
    """
    basket: list[dict] = []
    for r in rows:
        alloc_eur = amount_eur * r["weight"]
        alloc_aud = alloc_eur * euraud
        max_notional = alloc_aud / (1.0 + commission_rate)
        line = {
            "ticker": r["ticker"], "name": r["name"], "sleeve": r["sleeve"],
            "weight": r["weight"], "alloc_eur": alloc_eur,
            "price_aud": r["price_aud"], "euraud": euraud,
            "shares": int(math.floor(max_notional / r["price_aud"])),
        }
        _recompute(line, commission_rate)
        basket.append(line)

    extra = _reallocate_residual(basket, amount_eur, euraud, commission_rate)
    spend = sum(r["spend_eur"] for r in basket)
    basket.append({
        "ticker": "TOTAL", "name": "", "sleeve": "",
        "weight": sum(r["weight"] for r in basket),
        "alloc_eur": amount_eur, "price_aud": None, "euraud": euraud,
        "shares": None,
        "notional_aud": sum(r["notional_aud"] for r in basket),
        "commission_aud": sum(r["commission_aud"] for r in basket),
        "spend_aud": sum(r["spend_aud"] for r in basket),
        "spend_eur": spend,
        "note": f"residual €{amount_eur - spend:,.2f}; +{extra} shares from reallocation",
    })
    return basket


# ──────────────────────────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────────────────────────

def print_gate1_cap_weights(rows: list[dict], rejected: list[dict],
                            methodology: str) -> None:
    """Print the parallel §14 book without implying that later SJGV gates ran."""
    print(f"\n{methodology.upper()} (§14) — GATE 1, THEN TOP-N FULL MARKET CAP")
    print(f"  {'TICK':<6}{'WEIGHT':>10}{'MARKET CAP A$m':>17}{'PRICE A$':>11}"
          f"{'ELIG OZ':>10}{'INELIG NAV':>12}")
    print("  " + "─" * 66)
    for row in sorted(rows, key=lambda item: -item["weight"]):
        print(f"  {row['ticker']:<6}{row['weight']*100:>9.2f}%"
              f"{row['market_cap_aud_m']:>17,.0f}{row['price_aud']:>11.3f}"
              f"{row['eligible_ounce_share']:>10.1%}"
              f"{row['ineligible_nav_share']:>12.1%}")
    print("    Full issued market cap = sourced shares outstanding × market price; "
          "no free-float factor is available.")
    print("    Gate 2, Gate 3, statement currency, ounce logic and §8 caps do not "
          "reach this variant.")
    if rejected:
        print(f"    Not included after Gate 1, cap-input and top-N selection "
              f"({len(rejected)}):")
        for row in sorted(rejected, key=lambda item: item["ticker"]):
            print(f"      {row['ticker']}: {row['reason']}")


def print_weights(rows: list[dict], stats: dict, con: dict) -> None:
    """The book. Weight, the claim behind it, and what was paid for it."""
    print(f"\n{'TICK':<6} {'SLEEVE':<14} {'WEIGHT':>8} {'CLAIM Moz':>10} "
          f"{'A$/oz':>8} {'ALL-IN EV':>10} {'β_Au':>6} {'R²':>6} {'SPREAD':>7}")
    print("─" * 88)
    for r in sorted(rows, key=lambda x: -x["weight"]):
        fmt = lambda v, p=2: f"{v:.{p}f}" if v is not None else "—"  # noqa: E731
        spread = f"{r['spread_pct']:.2f}%" if r.get("spread_pct") is not None else "—"
        sa = " ◆" if r.get("single_asset") is True else ""
        print(f"{r['ticker']:<6} {r['sleeve']:<14} {r['weight']*100:>7.2f}% "
              f"{r['claimed_moz']:>10.2f} {r['aud_per_oz']:>8,.0f} "
              f"{r['all_in_ev_aud_m']:>10,.0f} {fmt(r['beta_gold']):>6} "
              f"{fmt(r['r2']):>6} {spread:>7}{sa}")

    print("─" * 88)
    print(f"Constituents {stats['n_constituents']}   "
          f"Eff N {stats['effective_n']:.1f}   "
          f"Top weight {stats['top_weight']*100:.1f}%   "
          f"Developer sleeve {stats['developer_sleeve']*100:.1f}%")
    print(f"Index price per claimed ounce: A${stats['aud_per_claimed_oz']:,.0f}/oz "
          f"all-in.  ◆ = single-asset company.")
    capw = stats.get("capweighted_aud_per_claimed_oz")
    if capw:
        print(f"  Same {len(rows)} names on MARKET-CAP weights: A${capw:,.0f}/oz — a "
              f"{(1 - stats['aud_per_claimed_oz'] / capw) * 100:.0f}% discount, and "
              f"the only")
        print(f"  comparator the number above means anything against. Same names, "
              f"same day, same")
        print(f"  disclosed ounces; the entire difference is how the weights are set.")
    capital = [r for r in rows
               if r.get("execution_capital_in_denominator_aud_m")]
    print("  DENOMINATOR: producers use standard EV; near-producers and developers "
          "add gross remaining execution capital.")
    if capital:
        print("  Financing does not reduce economic cost; project funding affects "
              "developer Gate 2 only:")
        for r in sorted(capital,
                        key=lambda x: -x["execution_capital_in_denominator_aud_m"]):
            print(f"    {r['ticker']} +A${r['execution_capital_in_denominator_aud_m']:,.0f}m "
                  f"({r['execution_capital']['state']}) — "
                  f"A${r['aud_per_oz_ex_execution_capital']:,.0f}/oz on EV alone, "
                  f"A${r['aud_per_oz']:,.0f}/oz all-in")
    else:
        print("  No near-producer or developer constituent carries material remaining "
              "execution capital, so every constituent denominator equals EV.")

    beta = stats["portfolio_beta_gold"]
    lo, hi = stats["beta_target"]
    if beta is not None:
        flag = "  ✓ in target" if stats["beta_in_target"] else f"  ✗ OUTSIDE [{lo}, {hi}]"
        cov = stats["beta_coverage"]
        print(f"Portfolio β_gold {beta:.2f}{flag}   "
              f"wtd R² {stats['wavg_r2']:.2f}   "
              f"wtd σ_idio {stats['wavg_sigma_idio']:.1%}"
              + (f"   coverage {cov:.0%} of weight" if cov < 0.999 else ""))
        print(f"  β is a CHECK on the §0 band, not an input. Neither β nor σ_idio "
              f"touches a weight.")
        naive = stats.get("portfolio_beta_contemporaneous")
        if naive is not None and abs(naive - beta) > 0.05:
            print(f"  (contemporaneous OLS would read {naive:.2f} — the "
                  f"non-synchronous-close artifact, config risk.dimson_note. "
                  f"Do not quote it.)")
    for n in con["notes"]:
        print(f"  • {n}")

    print_gate2_basis(rows)


def print_gate2_basis(rows: list[dict]) -> None:
    """Print the evidence basis behind accepted Gate 2 verdicts."""
    dropped = [r for r in rows if (r.get("gate2") or {}).get("facility_note")]
    intervals = [(r, r["gate2"]["capital_interval"]) for r in rows
                 if (r.get("gate2") or {}).get("capital_interval")]
    strained = [r for r in rows
                if (r.get("gate2") or {}).get("range_invariance", {}).get("strained")]
    if not intervals and not strained and not dropped:
        return

    print("\nGATE 2 INPUT BASIS (§3.2) — explicit project intervals")
    for r, interval in intervals:
        upper = interval.get("upper_aud_m")
        span = (f"A${interval['lower_aud_m']:,.0f}m–A${upper:,.0f}m"
                if upper is not None else
                f"A${interval['lower_aud_m']:,.0f}m–unbounded")
        coverage = ", ".join(
            f"{p['project_id']}:{p['coverage_state'].lower()}"
            for p in interval.get("projects", []))
        print(f"    {r['ticker']:<5} {interval['state']:<13} {span:<24} {coverage}")
    if intervals:
        print("  A finite adverse upper edge is tested where sourced. Otherwise the known")
        print("  lower edge is subtracted and the verdict is at least AMBER; incomplete")
        print("  two-year guidance is disclosed, not invented and not itself exclusionary.")
    if dropped:
        print("  Undrawn facilities NOT credited — a facility that lapses inside the "
              "window is not")
        print("  stress liquidity (§3). Every one of these names still passes without it:")
        for r in dropped:
            print(f"    {r['ticker']:<5} {r['gate2']['facility_note']}")
    if strained:
        for r in strained:
            print(f"  {r['ticker']} STRAINED — passes every published range one at a time, "
                  f"fails at the compound")
            print(f"    of their against-the-name ends. Flagged, not rejected (Gate 3 p90 "
                  f"precedent).")


def print_ledger(rows: list[dict], stats: dict, gold_aud: float) -> None:
    """§6 — the ounce ledger. This IS the model, so it prints in full.

    Every weight in the book above is a row of this table divided by the EV
    column of that one. There is no third table.
    """
    print("\nOUNCE LEDGER (§6) — what each company can actually deliver, by type")
    print(f"  {'TICK':<6}{'P&P':>8}{'M&I nr':>8}{'INFER':>8}{'GROSS':>8}"
          f"{'ELIG':>7}{'HEDGED':>8}{'CLAIM':>8}{'DECK':>7}{'AGE':>7}")
    print("  " + "─" * 77)
    split = []
    for r in sorted(rows, key=lambda x: -x["weight"]):
        L = r["ledger"]
        deck = r.get("reserve_price_aud")
        hedged = f"-{L['hedged_moz']:.2f}" if L["hedged_moz"] > 0.005 else "—"
        age = r.get("statement_age_months")
        if L["eligible_by_category"]:
            split.append(f"{r['ticker']} {L['eligible_pp_share']:.1%}/"
                         f"{L['eligible_mi_share']:.1%}/"
                         f"{L['eligible_inferred_share']:.1%}")
        print(f"  {r['ticker']:<6}{L['pp_moz']:>8.2f}{L['mi_moz']:>8.2f}"
              f"{L['inferred_moz']:>8.2f}{L['gross_moz']:>8.2f}"
              f"{L['eligible_pp_share']*100:>6.0f}%{hedged:>8}"
              f"{L['claimed_moz']:>8.2f}"
              f"{(f'{deck:,.0f}' if deck else '—'):>7}"
              f"{(f'{age:.0f}mo' if age is not None else '—'):>7}")
    mix = stats["ledger_mix"]
    print("  " + "─" * 77)
    if split:
        print(f"  ELIG is the Gate 1 share of the P&P tranche. Each tranche carries "
              f"its own share, because")
        print(f"  the blended figure is confidence-weighted — right on the total, "
              f"wrong on the split (§2.4).")
        print(f"  P&P/M&I/Inferred: {'  '.join(split)}")
    print(f"  AGE is the oldest document behind a counted tranche, against the "
          f"§6.4 {stats['max_statement_age_months']:g}-month bar.")
    print(f"  CLAIM applies the §6 confidence weights: P&P 1.0, M&I non-reserve 0.5, "
          f"Inferred 0.2.")
    # One decimal, not zero. The M&I share currently sits at 29.50%, so an
    # integer percentage flips between 29 and 30 on a 0.01pp move — and this is
    # the statistic §10.4 calls the one to watch over time. A published number
    # that changes when nothing has is worse than a less round one.
    print(f"  The index's claim is {mix['reserves']:.1%} unhedged reserves, "
          f"{mix['mi_non_reserve']:.1%} near-money M&I and")
    print(f"  {mix['inferred']:.1%} inferred tail. That mix IS the convexity position "
          f"and it is the number to")
    print(f"  watch over time: M&I and inferred ounces are waste at a low gold price "
          f"and ore at a high")
    print(f"  one, and the index holds them at half and a fifth of a reserve ounce. "
          f"A book drifting")
    print(f"  toward reserves is a book losing its option inventory.")
    print(f"  Of gross disclosed ounces, {mix['not_ours_share_of_gross']:.0%} are "
          f"NOT OURS — wrong sovereign, or already sold")
    print(f"  forward. A further {mix['confidence_discount_of_owned']:.0%} of what "
          f"remains is discounted for confidence, which is")
    print(f"  a haircut and not a write-off: an Inferred ounce counted at 0.2 is "
          f"the option, still held.")
    print(f"  DECK is the gold price the company booked its reserves at, against "
          f"spot A${gold_aud:,.0f}. A low")
    print(f"  deck means ounces are under-booked and will convert on the next "
          f"statement. Reported, not scored.")


def print_nav(rows: list[dict], navs: dict[str, dict], constituents: list[dict],
              stats: dict, meta: dict, detail: bool) -> None:
    """§9 — the NAV model. REPORTING ONLY, by decision.

    Its one job is the implied deck: the gold price at which the market's
    valuation of a company equals a rules-based DCF of its own disclosed
    reserves. That is a sentence about disagreement, and disagreement is worth
    printing. It is not worth weighting, because the number moves with a
    discount rate nobody can source, and this index does not let a judgement
    call size a position.
    """
    if not navs:
        return
    conf = confidence_weights(meta)
    by_ticker = {c["ticker"]: c for c in constituents}

    print("\n§9 NAV MODEL — REPORT ONLY, not in any weight")
    unmodelled = [t for t, v in navs.items() if not v.get("modelled")]
    if unmodelled:
        print(f"  Not modellable ({len(unmodelled)}): {', '.join(sorted(unmodelled))}"
              f" — reported, not scored as zero.")

    if detail:
        print(f"  {'TICK':<6}{'NAV A$m':>10}{'MCAP A$m':>10}{'P/NAV':>7}"
              f"{'IMPLIED':>9}{'LIFE y':>8}{'δ':>7}{'CONS':>7}")
        print("  " + "─" * 64)
        for r in sorted(rows, key=lambda x: -x["weight"]):
            rec = navs.get(r["ticker"]) or {}
            if not rec.get("modelled"):
                continue
            imp = nav_model.implied_deck(by_ticker[r["ticker"]], r["mcap_aud_m"],
                                         meta, conf)
            f2 = lambda v, p=2: f"{v:.{p}f}" if v is not None else "—"  # noqa: E731
            print(f"  {r['ticker']:<6}{rec['nav_aud_m']:>10,.0f}"
                  f"{r['mcap_aud_m']:>10,.0f}{f2(r['p_nav']):>7}"
                  f"{(f'{imp:,.0f}' if imp else '—'):>9}"
                  f"{rec['total_life_years']:>8.0f}"
                  f"{f2(rec['modelled_delta']):>7}"
                  f"{f2(rec.get('deck_sensitivity')):>7}")
        print("    IMPLIED is the gold price at which modelled NAV equals market cap —")
        print("    the same statement as P/NAV, in a unit that can be argued with.")

    port = nav_model.portfolio_nav_asymmetry(rows, navs)
    d = port.get("delta")
    reg = stats.get("portfolio_beta_gold")
    if d is not None:
        lo, hi = stats["beta_target"]
        inside = "within" if lo <= d <= hi else "OUTSIDE"
        print(f"  Portfolio modelled delta {d:.2f} ({inside} the {lo}–{hi} mandate)"
              + (f", regressed β_gold {reg:.2f}" if reg else "")
              + (f", coverage {port['coverage']:.0%} of weight"
                 if port["coverage"] < 0.999 else ""))
        print(f"    Two independent methods {abs(d - reg):.2f} apart, if both are "
              f"available. Neither sets a weight.")
        if port.get("up_capture") is not None:
            bump = meta["nav_model"]["stress_bump"]
            asym = port["asymmetry"]
            print(f"  Modelled NAV capture at ±{bump:.0%}: up {port['up_capture']:.2f}, "
                  f"down {port['down_capture']:.2f}, ratio "
                  f"{(f'{asym:.2f}' if asym else '—')}")
            print(f"    On a FIXED mine plan at ONE AISC, NAV is A×(deck − AISC) − debt "
                  f"— linear in the deck, so")
            print(f"    this ratio is 1.00 by construction and says nothing about the "
                  f"book. Real convexity is the")
            print(f"    cut-off grade falling as the price rises, which moves ounces "
                  f"from the M&I tranche of the §6")
            print(f"    ledger into P&P. Measuring it needs grade-tonnage curves; the "
                  f"LEDGER MIX is the honest")
            print(f"    proxy until they are sourced, and unlike this ratio it is "
                  f"made of disclosed ounces.")


def print_concentration(rows: list[dict], con: dict, stats: dict, meta: dict) -> None:
    """§8.1 / §11 — where one operational failure would land."""
    print("\nCONCENTRATION (§8.1, §11)")
    precap = con.get("precap_weights") or {}
    print(f"  {'TICK':<6}{'WEIGHT':>9}{'PRE-CAP':>10}{'CLAIM Moz':>11}"
          f"{'oz RANK':>9}{'σ_idio':>9}{'1-ASSET':>9}")
    print("  " + "─" * 65)
    by_oz = {r["ticker"]: i + 1 for i, r in
             enumerate(sorted(rows, key=lambda x: -x["claimed_moz"]))}
    for r in sorted(rows, key=lambda x: -x["weight"]):
        t = r["ticker"]
        sig = f"{r['sigma_idio']:.2f}" if r.get("sigma_idio") else "—"
        # The SHARE, not the boolean it derives. A defect hides in a composite:
        # printing only ◆/blank would hide both how far a flagged name is past
        # the threshold and how close an unflagged one is to it.
        share = r.get("largest_asset_pp_share")
        col = "UNTESTED" if share is None else f"{share:>7.0%}"
        sa = "  ◆ single-asset" if r.get("single_asset") is True else ""
        print(f"  {t:<6}{r['weight']*100:>8.2f}%{precap.get(t, r['weight'])*100:>9.2f}%"
              f"{r['claimed_moz']:>11.2f}{by_oz[t]:>9}{sig:>9}{col:>9}{sa}")
    print(f"    oz RANK is the name's rank by claimed ounces. Weight rank and oz rank")
    print(f"    differ only through EV — that is the whole strategy, visible in two "
          f"columns.")
    print(f"    σ_idio is printed and unused. It was the weight denominator until "
          f"17 Aug 2026,")
    print(f"    when it measured +0.77 correlated with ounces/EV — cancelling the "
          f"signal it divided.")
    th = meta["constraints"]["single_asset_pp_share_threshold"]
    print(f"    1-ASSET is largest_asset_pp_share: the share of ELIGIBLE P&P reserves")
    print(f"    at one asset. ◆ at or above {th:.0%} (§8.1) → the "
          f"{con['single_asset_cap']:.0%} cap, not {con['single_name_cap']:.0%}.")
    if con["single_asset_untested"]:
        print(f"  Single-asset status UNSOURCED for "
              f"{len(con['single_asset_untested'])}/{len(rows)}. The "
              f"{con['single_asset_cap']:.0%} cap could not be applied to them.")


def print_capacity(cap: dict, euraud: float) -> None:
    """§4.3 — reported, never enforced. Two lines, deliberately.

    This number spent a day as a live constraint and generated a proposal to
    shrink the developer sleeve — the highest-claim-per-dollar part of the book
    — to protect a fund size twenty times the actual one. At €1m it is a fact
    about the future, not an input to today's weights.
    """
    if not cap.get("names"):
        return
    print(f"\nCAPACITY (§4.3, reported): ceiling A${cap['capacity_aud_m']:,.0f}m "
          f"(≈ €{cap['capacity_aud_m']/euraud:,.0f}m), first bound by "
          f"{cap['binding_ticker']}, at {cap['participation']:.0%} participation "
          f"over {cap['max_days_advt']:g} days.")
    if cap["unmeasured"]:
        print(f"  unmeasured for {len(cap['unmeasured'])}: "
              f"{', '.join(sorted(cap['unmeasured']))} — advt_shares_m unsourced.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build the SJGV v2.0 index and optionally size a basket.")
    ap.add_argument("amount", nargs="?", type=float, default=None,
                    help="EUR amount to size the basket for (e.g. 1000000).")
    ap.add_argument("--euraud", type=float, default=None,
                    help="Override AUD per EUR. Default: fetched from IBKR.")
    ap.add_argument("--gold-aud", type=float, default=None,
                    help="Override spot gold in AUD/oz. Default: derived from IBKR.")
    ap.add_argument("--commission", type=float, default=0.0,
                    help="Per-order commission in PERCENT of notional (0.1 = 0.1%%).")
    ap.add_argument("--nav-detail", action="store_true",
                    help="per-name §9 NAV, P/NAV, implied deck and modelled delta.")
    args = ap.parse_args()

    commission_rate = args.commission / 100.0
    if commission_rate < 0:
        ap.error("--commission must be >= 0")

    meta, constituents, excluded, market, impute_notes = load_data()
    tickers = [c["ticker"] for c in constituents]

    # config.gates.spread_measure describes what Gate 3 reads. _spread_history
    # measures exactly one thing, so a config that asks for another is a silent
    # mismatch between the declared methodology and the number in the table.
    if meta["gates"]["spread_measure"] != "median_daily_rth_time_weighted_quoted":
        raise ValueError(
            f"gates.spread_measure is {meta['gates']['spread_measure']!r}; the "
            f"engine measures the median daily RTH time-weighted quoted spread "
            f"and nothing else. Change the code or change the parameter back.")

    # §10.1. Read here rather than where the sizing output is formatted, so that
    # a build with no basket still checks it — and so that a wrong numéraire
    # fails before the IBKR session rather than after it.
    numeraire = (meta["reporting"]["numeraire_primary"],
                 meta["reporting"]["numeraire_secondary"])
    if numeraire[0] != "gold_ounces":
        raise ValueError(
            f"reporting.numeraire_primary is {numeraire[0]!r}; the engine reports "
            f"in gold ounces (§10.1) and the whole §0.1 argument depends on it. "
            f"Change the code or change the parameter back.")

    # §8.1. The tri-state is a property of the code, not of the data, so it is
    # asserted rather than eyeballed — an absent largest_asset_pp_share deriving
    # False would restore the 15% cap on every unsourced name and report it as a
    # test that PASSED. Runs before the IBKR session so it fails in a second.
    _assert_single_asset_tristate(meta)

    print(f"SJGV {meta['methodology']} — adopted {meta['adopted']}")
    print(f"Data layer sourced {market['_ledger_sourced']}"
          + ("" if market["_ledger_sourced"] == market["_sourced"]
             else f" (market fallbacks {market['_sourced']})"))
    print(f"Universe: {len(tickers)} candidates, {len(excluded)} pre-excluded")
    for n in impute_notes:
        print(f"  RESOURCE RECONCILIATION: {n}")

    try:
        md = fetch_market_data(tickers,
                               history_duration=meta["risk"]["regression_window"],
                               spread_duration=meta["gates"]["spread_window"])
    except Exception as exc:
        print(f"ERROR: IBKR fetch failed: {exc}", file=sys.stderr)
        print("Start TWS/IB Gateway with the API enabled, or pass "
              "--gold-aud/--euraud to work offline (weights still need prices).",
              file=sys.stderr)
        return 2

    # Written here, before anything downstream can fail, because the session is
    # the one input that cannot be re-read: TWS will answer the same questions
    # differently in an hour, and a build that died after the fetch would
    # otherwise throw away the only copy of what it was told.
    bundle = write_market_bundle(md["bundle"], md["bar_rows"])
    bundle["cli_overrides"] = {"gold_aud": args.gold_aud, "euraud": args.euraud}
    print(f"\nIBKR session {bundle['session_started_utc'][11:19]}Z–"
          f"{bundle['session_finished_utc'][11:19]}Z  "
          f"{bundle['n_requests']} requests, {bundle['n_contracts']} contracts, "
          f"{bundle['n_series']} series, {bundle['bars_rows']:,} bars")
    print(f"  market data requested {bundle['market_data_type_requested']}, "
          f"returned {'/'.join(bundle['market_data_type_observed']) or '—'}"
          f"   engine {short_commit(bundle['engine_commit'])}")
    print("  prices from "
          + (", ".join(f"{k}×{v}" for k, v in bundle["price_fields"].items()) or "—")
          + (f"   {bundle['n_errors']} TWS message(s), codes "
             f"{', '.join(str(c) for c in bundle['error_codes'])}"
             if bundle["n_errors"] else ""))
    if bundle["price_fields"].get("histDailyClose"):
        print(f"  {bundle['price_fields']['histDailyClose']} price(s) are a "
              f"historical daily close, not a quote: the quote channel returned "
              f"nothing for those contracts on this session. Per-name detail in "
              f"market_bundle.json → prices.")
    print("  Wrote → market_bundle.json, market_bars.csv")

    fx = md["fx"]
    gold_aud, gold_src = args.gold_aud, "cli"
    if gold_aud is None and fx.get("xauusd") and fx.get("audusd"):
        gold_aud, gold_src = fx["xauusd"] / fx["audusd"], "ibkr"
    if gold_aud is None:
        gold_aud = market["gold"]["xau_aud"]["v"]
        gold_src = f"data/market.json fallback ({market['gold']['xau_aud']['as_of']})"

    euraud, fx_src = args.euraud, "cli"
    if euraud is None:
        euraud, fx_src = fx.get("euraud"), "ibkr"
    if euraud is None:
        euraud = market["fx"]["eur_aud"]["v"]
        fx_src = f"data/market.json fallback ({market['fx']['eur_aud']['as_of']})"

    print(f"\nGold  A${gold_aud:,.0f}/oz [{gold_src}]"
          + (f"  (US${fx['xauusd']:,.2f})" if fx.get("xauusd") else ""))
    print(f"EURAUD {euraud:.4f} [{fx_src}]")

    # Parallel §14 variant. It shares the candidate data and the exact price
    # observations from this session, then deliberately stops after Gate 1.
    # Computing it here keeps it independent of every later SJGV gate and of
    # the ounce/EV model while still pinning both books to one market record.
    gate1_cap_cfg = meta["variants"]["gate1_cap"]
    gate1_cap_methodology = gate1_cap_cfg["methodology"]
    gate1_cap_adopted = gate1_cap_cfg["adoption_date"]
    gate1_cap_rows, gate1_cap_rejected = compute_gate1_cap_weights(
        constituents, md["prices"], meta)
    if not gate1_cap_rows:
        print("\nERROR: no constituent passed Gate 1 with complete market-cap data.",
              file=sys.stderr)
        for row in gate1_cap_rejected:
            print(f"  {row['ticker']:<6} {row['reason']}", file=sys.stderr)
        return 2

    risk = compute_risk_stats(md["history"], md["gold_history"],
                              md.get("audusd_history"), meta)

    # β_gold is the §0 mandate constraint and σ_idio divides every raw weight,
    # so the regressor and its sample size are results in their own right, not
    # plumbing. State them; never let a silent USD fallback pass for the answer.
    bases = sorted({s["basis"] for s in risk.values() if s.get("basis")})
    n_obs = [s["n_obs"] for s in risk.values() if s.get("n_obs")]
    if not risk:
        print("\nNote: no gold history — β_gold and R² unavailable. Weights are "
              "unaffected; the §0 mandate band simply cannot be checked on this run.")
    else:
        ests = sorted({s["estimator"] for s in risk.values() if s.get("estimator")})
        print(f"Regressor: gold in {'; '.join(bases)}  "
              f"({min(n_obs)}–{max(n_obs)} date-matched daily returns, "
              f"{'/'.join(ests)})")
        print("  Reported only — no risk statistic reaches a weight (§7).")
        if any(b.startswith("USD") for b in bases):
            print("  AUDUSD history unavailable — beta is measured in the wrong "
                  "numéraire and reads LOW for these names. Treat any β_gold "
                  "below the 1.4 floor as unproven until this resolves.")

    # Trailing real reference for the reporting-only conservative NAV deck.
    aud_gold_series = [(d, g / fx) for d, g, fx
                       in _join(md["gold_history"], md.get("audusd_history") or [])
                       if fx > 0]
    anchor = gold_anchor(aud_gold_series, gold_aud, meta)
    print(f"Trailing real gold reference A${anchor['anchor_aud']:,.0f}/oz — "
          f"{anchor['basis']} (reporting NAV deck)")
    print(f"  Gate 2 health stress "
          f"A${gold_aud * (1-meta['gate2']['gold_drawdown']):,.0f}/oz "
          f"= {meta['gate2']['gold_drawdown']:.0%} off current spot")
    if anchor["degraded"]:
        print("  WARNING: trailing NAV reference is degraded — using spot or a short "
              "window. Gate 2 is unaffected because its stress starts at spot.")

    # ── §8 NAV model ─────────────────────────────────────────────────────────
    # Runs on every build whether or not its output is allowed to reach a
    # weight. See nav_model.py: the committee cannot adopt a discount rate
    # without seeing what it does, and it cannot see what it does unless the
    # model runs against the live book.
    conf = confidence_weights(meta)
    navs: dict[str, dict] = {}
    if meta["nav_model"]["built"]:
        navs = nav_model.value_all(constituents, gold_aud, meta, conf,
                                   anchor_aud=anchor["anchor_aud"])
        cons_deck, cons_basis = nav_model.conservative_deck(meta,
                                                            anchor["anchor_aud"])
        print(f"{nav_model.summarise(navs)}; decks A${gold_aud:,.0f} spot / "
              + (f"A${cons_deck:,.0f} conservative — {cons_basis}"
                 if cons_deck else f"conservative unavailable — {cons_basis}"))
        print(f"  discount rates {meta['nav_model']['discount_rate_real_producing']:.0%} "
              f"real producing / "
              f"{meta['nav_model']['discount_rate_real_development']:.0%} real "
              f"development, tax {meta['gate2']['tax_rate']:.0%}"
              " — REPORTING ONLY, no NAV output reaches a weight (§9)")

    rows, rejected = compute_raw_weights(constituents, md["prices"], risk, gold_aud,
                                         meta, anchor_gold=anchor["anchor_aud"],
                                         spreads=md.get("spreads"), navs=navs,
                                         as_of=market["_ledger_sourced"])

    if not rows:
        print("\nERROR: no constituent passed the gates with complete data.",
              file=sys.stderr)
        for r in rejected:
            print(f"  {r['ticker']:<6} {r['reason']}", file=sys.stderr)
        return 2

    con = apply_constraints(rows, meta)
    stats = portfolio_stats(rows, meta)
    print_weights(rows, stats, con)
    print_ledger(rows, stats, gold_aud)

    if rejected:
        print(f"\nEXCLUDED AT BUILD TIME ({len(rejected)}) — not silently defaulted:")
        for r in sorted(rejected, key=lambda x: x["ticker"]):
            print(f"  {r['ticker']:<6} {r['sleeve']:<14} {r['reason']}")

    gate2_stress = gold_aud * (1.0 - meta["gate2"]["gold_drawdown"])
    print(f"\nGATE 2 — PRODUCER HEALTH (§3): "
          f"{meta['gate2']['gold_drawdown']:.0%} AUD-gold drawdown off spot, "
          f"A${gate2_stress:,.0f}/oz over "
          f"{meta['gate2']['horizon_years']:g}y, run unhedged. BREAKS is off spot.")
    print(f"  {'TICK':<6}{'MARGIN':>9}{'FCF/yr':>10}{'OPEN':>9}{'UNDRAWN':>9}"
          f"{'CAPEX':>8}{'ENDING':>10}{'BREAKS':>8}  VERDICT")
    print("  " + "─" * 104)
    for r in sorted(rows, key=lambda x: -x["weight"]):
        d = (r.get("gate2") or {}).get("detail") or {}
        if not d or "margin_aud_oz" not in d:
            continue
        health = (r.get("gate2") or {}).get("health") or "PASS"
        flag = "" if d["survives_on_cash_alone"] else "  (financing needed)"
        bp = r.get("breaking_point")
        bp_s = f"{bp*100:.0f}%" if bp else ">95%"
        print(f"  {r['ticker']:<6}{d['margin_aud_oz']:>9,.0f}"
              f"{d['fcf_annual_aud_m']:>10,.0f}{d['opening_liquidity_aud_m']:>9,.0f}"
              f"{d['undrawn_aud_m']:>9,.0f}{d['committed_capex_aud_m']:>8,.0f}"
              f"{d['ending_with_facilities_aud_m']:>10,.0f}{bp_s:>8}  {health}{flag}")
    g2fails = [r for r in rejected if r["reason"].startswith("GATE 2")]
    for r in sorted(g2fails, key=lambda x: x["ticker"]):
        print(f"  {r['ticker']:<6}{'':>45}  FAIL — {r['reason'][8:][:70]}")

    print("\nDATA QUALITY")
    if impute_notes:
        print(f"  Resource ledger does NOT reconcile to disclosed MR for "
              f"{len(impute_notes)}:")
        for n in impute_notes:
            print(f"    {n}")
        print(f"    Reported, never corrected. P&P + M&I non-reserve + Inferred should")
        print(f"    equal total Mineral Resources; a gap means a category was read off")
        print(f"    the wrong table or from a different vintage.")
    prov = [r for r in rows if (r.get("gate2") or {}).get("provisional")]
    if prov:
        tickers = sorted(r["ticker"] for r in prov)
        print(f"  Gate 2 AMBER on incomplete commitment evidence for {len(prov)}: "
              f"{', '.join(tickers)}")
        print("    Only the sourced unavoidable lower edge was subtracted. No future spend")
        print("    was filled in or treated as zero; complete two-year guidance is not an")
        print("    admission condition under the producer health check:")
        for r in sorted(prov, key=lambda x: x["ticker"]):
            note = ((r.get("gate2") or {}).get("detail") or {}).get(
                "capital_evidence_note", "commitment evidence incomplete")
            print(f"      {r['ticker']}: {note}")
    untested3 = [r["ticker"] for r in rows if (r.get("gate3") or {}).get("pass") is None]
    if untested3:
        print(f"  Gate 3 NOT TESTED for {len(untested3)}/{len(rows)}: "
              f"{', '.join(sorted(untested3))}")
        print(f"    No RTH bid/ask history returned, so the §4 tradability gate did")
        print(f"    not run. These names are untested, not passed.")
    strained = [r["ticker"] for r in rows if (r.get("gate3") or {}).get("strained")]
    if strained:
        print(f"  Gate 3 STRAINED for {len(strained)}: {', '.join(sorted(strained))}")
        print(f"    Median spread passes but the 90th percentile breaches the limit.")
        print(f"    Tradable on a normal day, not necessarily on the day a gate breach")
        print(f"    or a Gate 1 event would force the rebalance.")
    no_deck = [r["ticker"] for r in rows if r["reserve_price_aud"] is None]
    if no_deck:
        print(f"  Reserve price deck UNSOURCED for {len(no_deck)}: "
              f"{', '.join(sorted(no_deck))}")
        print(f"    A reporting gap in the §6 ledger, not a scoring one — the deck")
        print(f"    says how under-booked the P&P tranche is. No weight moves.")
    no_risk = [r["ticker"] for r in rows if r.get("beta_gold") is None]
    if no_risk:
        print(f"  β_gold / R² unavailable for {len(no_risk)}: "
              f"{', '.join(sorted(no_risk))}")
        print(f"    These names are WEIGHTED NORMALLY. Under any scheme with a")
        print(f"    excluded outright, because σ_idio was the weight denominator and a")
        print(f"    short listing history therefore disqualified a company's ounces.")

    print_nav(rows, navs, constituents, stats, meta, args.nav_detail)
    print_concentration(rows, con, stats, meta)

    cap = capacity(rows, (args.amount or 0.0) * euraud, meta)
    print_capacity(cap, euraud)
    print_gate1_cap_weights(gate1_cap_rows, gate1_cap_rejected,
                            gate1_cap_methodology)

    # Declared-but-unread is the defect this build is closing; the run reports
    # its own instance of it rather than waiting for the auditor to be invoked.
    unread = unread_engine_params()
    if unread:
        print(f"\nCONFIG — {len(unread)} parameter(s) claimed as engine-read and NOT "
              f"read on this run:")
        for p in unread:
            print(f"  {p}")
        print("  Either wire it, or move it to another consumer in CONFIG_PARAMS.")
    if CONFIG_MISSES:
        print(f"\nCONFIG — the engine looked for {len(CONFIG_MISSES)} key(s) that "
              f"config.json does not define, so a hardcoded default decided the "
              f"answer: {', '.join(sorted(CONFIG_MISSES))}")

    generated_utc = datetime.now(timezone.utc).isoformat()
    out = {
        "generated_utc": generated_utc,
        "methodology": meta["methodology"],
        "data_sourced": market["_ledger_sourced"],
        "gold_aud_oz": gold_aud, "gold_source": gold_src,
        "euraud": euraud, "fx_source": fx_src,
        # The market leg's source document: which TWS session, which contracts,
        # which market-data type, which engine — and the digests that say these
        # weights came from THAT bundle and not a neighbouring copy of it.
        "market_input": bundle,
        # The numéraire the regression ran in ("AUD" / "USD (fallback…)").
        "regressor_basis": bases,
        "gold_reference": anchor,
        "resource_reconciliation": impute_notes,
        "reserve_deck_unsourced": no_deck,
        "stats": stats, "constraints": con,
        "weights": rows,
        "ledger": {r["ticker"]: r["ledger"] for r in rows},
        "rejected": rejected,
        "pre_excluded": excluded,
        "nav_model": {
            "built": meta["nav_model"]["built"],
            "reporting_only": True,
            "detail": navs,
        },
        "capacity": cap,
        # What the build actually touched in config.json. tools/config_audit.py
        # holds this against CONFIG_PARAMS: the registry is a claim, this is the
        # evidence, and a parameter that appears in the first and not the second
        # is the defect class that has now bitten three times.
        "config_reads_observed": sorted(CONFIG_READS),
        "config_keys_missing": sorted(CONFIG_MISSES),
    }
    (HERE / "weights.json").write_text(json.dumps(out, indent=2, default=str))
    with (HERE / "weights.csv").open("w", newline="") as f:
        cols = ["ticker", "name", "sleeve", "weight", "claimed_moz", "aud_per_oz",
                "aud_per_oz_ex_execution_capital", "all_in_ev_aud_m",
                "remaining_execution_capex_aud_m",
                "execution_capital_in_denominator_aud_m",
                "residual_funding_gap_aud_m",
                "residual_funding_gap_state",
                "aud_per_oz_ex_gap", "funded_ev_aud_m", "funding_gap_aud_m",
                "pp_moz", "mi_moz", "inferred_moz", "eligible_share", "hedged_moz",
                "ev_aud_m", "price_aud", "beta_gold", "r2", "spread_pct",
                "largest_asset_pp_share", "single_asset"]
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows({**r, **r["ledger"]}
                     for r in sorted(rows, key=lambda x: -x["weight"]))

    selected_market_cap = sum(
        row["market_cap_aud_m"] for row in gate1_cap_rows)
    omitted_market_cap = sum(
        row.get("market_cap_aud_m", 0.0) for row in gate1_cap_rejected)
    eligible_market_cap = selected_market_cap + omitted_market_cap
    gate1_cap_stats = {
        "n_constituents": len(gate1_cap_rows),
        "max_constituents": gate1_cap_cfg["max_constituents"],
        "total_market_cap_aud_m": selected_market_cap,
        "selected_market_cap_aud_m": selected_market_cap,
        "eligible_market_cap_aud_m": eligible_market_cap,
        "eligible_market_cap_coverage": (
            selected_market_cap / eligible_market_cap
            if eligible_market_cap > 0 else None),
        "effective_n": effective_n(gate1_cap_rows),
        "top_weight": max(row["weight"] for row in gate1_cap_rows),
    }
    gate1_cap_out = {
        "generated_utc": generated_utc,
        "methodology": gate1_cap_methodology,
        "adopted": gate1_cap_adopted,
        "data_sourced": market["_ledger_sourced"],
        "construction": {
            "universe": "shared data/companies.json candidate universe",
            "eligibility": "Gate 1 only",
            "selection": (
                f"largest {gate1_cap_cfg['max_constituents']} eligible companies "
                "by full market capitalisation"),
            "weighting": "full_market_cap",
            "formula": "shares_out_m * price_aud / total_market_cap_aud_m",
            "not_applied": [
                "Gate 2", "Gate 3", "resource-statement currency",
                "ounce ledger", "enterprise-value weighting", "section 8 caps",
            ],
        },
        "gate1": {
            "max_ineligible_nav_share": meta["gates"]["max_ineligible_nav_share"],
            "mixed_jurisdiction_treatment": (
                "admit the whole company when the entity cap passes; do not "
                "haircut market capitalisation by eligible-ounce share"),
        },
        "market_input": bundle,
        "stats": gate1_cap_stats,
        "weights": gate1_cap_rows,
        "rejected": gate1_cap_rejected,
        "outside_shared_candidate_records": {
            "records": excluded,
            "note": (
                "Carried for universe audit only. These records are outside the "
                "shared data/companies.json candidate set and were not tested "
                "or excluded by this variant's post-selection rules."),
        },
        "config_reads_observed": sorted(CONFIG_READS),
        "config_keys_missing": sorted(CONFIG_MISSES),
    }
    (HERE / "gate1_cap_weights.json").write_text(
        json.dumps(gate1_cap_out, indent=2, default=str))
    with (HERE / "gate1_cap_weights.csv").open("w", newline="") as f:
        cols = ["market_cap_rank", "ticker", "name", "sleeve", "weight",
                "market_cap_aud_m", "price_aud", "shares_out_m",
                "eligible_ounce_share", "ineligible_nav_share", "shares_src"]
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(sorted(gate1_cap_rows, key=lambda row: -row["weight"]))
    print("\nWrote → weights.csv, weights.json, gate1_cap_weights.csv, "
          "gate1_cap_weights.json")

    if args.amount is None:
        return 0
    if not euraud:
        print("\nERROR: EURAUD unavailable — pass --euraud <AUD per EUR>.",
              file=sys.stderr)
        return 2

    basket = size_basket(rows, args.amount, euraud, commission_rate)
    total = basket[-1]

    print(f"\nSizing €{args.amount:,.2f} at EURAUD {euraud:.4f} "
          f"(commission {args.commission:.4f}%)")
    print(f"\n{'TICK':<6} {'SHARES':>9} {'WEIGHT':>8} {'PRICE A$':>9} "
          f"{'NOTIONAL A$':>13} {'SPEND €':>12}")
    print("─" * 62)
    for r in basket[:-1]:
        print(f"{r['ticker']:<6} {r['shares']:>9,} {r['weight']*100:>7.2f}% "
              f"{r['price_aud']:>9.3f} {r['notional_aud']:>13,.2f} "
              f"{r['spend_eur']:>12,.2f}")
    print("─" * 62)
    print(f"{'TOTAL':<6} {'':>9} {total['weight']*100:>7.2f}% {'':>9} "
          f"{total['notional_aud']:>13,.2f} {total['spend_eur']:>12,.2f}")
    print(f"  {total['note']}")

    # Numéraire per §10.1: the fund's job is accumulating ounces, so report the
    # position in ounces alongside the currency figures. Which unit leads is a
    # methodology parameter, not a formatting choice — in ounce terms the index
    # only rises if it beats gold, and that is the whole argument of §0.1.
    gold_eur = gold_aud / euraud
    print(f"\nNuméraire (§10.1): {total['spend_eur'] / gold_eur:,.3f} oz gold "
          f"deployed at A${gold_aud:,.0f}/oz "
          f"({numeraire[1].upper()} secondary: €{gold_eur:,.2f}/oz)")

    with (HERE / "basket.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(basket[0].keys()), extrasaction="ignore")
        wr.writeheader()
        wr.writerows(basket)
    (HERE / "basket.json").write_text(json.dumps(
        {"amount_eur": args.amount, "euraud": euraud, "gold_aud_oz": gold_aud,
         "ounces_deployed": total["spend_eur"] / gold_eur,
         "commission_pct": args.commission, "basket": basket}, indent=2, default=str))
    print("Wrote → basket.csv, basket.json")

    gate1_cap_basket = size_basket(
        gate1_cap_rows, args.amount, euraud, commission_rate)
    gate1_cap_total = gate1_cap_basket[-1]
    with (HERE / "gate1_cap_basket.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(gate1_cap_basket[0].keys()),
                            extrasaction="ignore")
        wr.writeheader()
        wr.writerows(gate1_cap_basket)
    (HERE / "gate1_cap_basket.json").write_text(json.dumps({
        "methodology": gate1_cap_methodology,
        "amount_eur": args.amount,
        "euraud": euraud,
        "commission_pct": args.commission,
        "basket": gate1_cap_basket,
    }, indent=2, default=str))
    print(f"\nGate 1 cap-weighted sizing: €{args.amount:,.2f}, "
          f"{len(gate1_cap_basket) - 1} holdings, "
          f"€{gate1_cap_total['spend_eur']:,.2f} deployed")
    print("Wrote → gate1_cap_basket.csv, gate1_cap_basket.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
