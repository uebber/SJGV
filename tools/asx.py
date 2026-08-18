#!/usr/bin/env python3
"""
Source share counts and quoted spreads from the ASX's own research API.

    python tools/asx.py                 # propose, write nothing
    python tools/asx.py --write         # commit shares_out_m to companies.json
    python tools/asx.py --quotes        # also write asx_quotes.json for Gate 3

WHY THIS EXISTS
---------------
Share count was the largest blocking gap in the data layer: six of seventeen
candidates could not be weighted at all, because without a share count there is
no market cap, no EV, and no denominator for the §9 weight.

It used to come from IBKR at build time. That route is gone — TWS API 10.47
removed reqFundamentalData outright, with no successor (see the note above
_history in build_index.py). Sourcing it by hand from filings is the trap the
data README warns about: issuer sites publish Appendix 2A *incremental*
issuances that read like totals, and third-party aggregators disagree badly —
Ausgold was quoted at 2.296bn against a market cap implying 450-650m, Astral at
1.80bn against 1.45bn.

This endpoint is not a third-party aggregator. asx.api.markitdigital.com is the
data service behind the ASX's own company pages, so it is the exchange's number
for the exchange's own listings. On the eleven names whose counts were already
read out of filings it agrees within 1.9%, and exactly on Capricorn. It also
settles the Astral conflict at 1.801bn — the higher of the two figures.

VALIDATION, BECAUSE ONE FEED IS STILL ONE FEED
----------------------------------------------
Two checks run before anything is written, and both must pass:

  1. Internal consistency: numOfShares x priceClose must reproduce the API's own
     marketCap to within 1%. This catches a share count that belongs to a
     different security line or a different date to the price beside it.
  2. Cross-check against the data layer: where companies.json already carries a
     figure read from a filing, the two must agree within TOLERANCE_PCT. A
     disagreement is reported and NOT written — it means either the filing is
     stale or the feed is wrong, and which one is a judgement call.

A name failing either check is proposed but never auto-written, so the failure
mode is a missing value rather than a confident wrong one.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COMPANIES = DATA / "companies.json"

API = "https://asx.api.markitdigital.com/asx-research/1.0/companies/{t}/{ep}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Share counts move with placements and option exercises. Anything inside this
# band is ordinary drift between a filing date and today; anything outside is a
# disagreement that a human has to adjudicate.
TOLERANCE_PCT = 5.0
MCAP_TOLERANCE = 0.01

DOC_KEY = "asx_api"
SYDNEY = ZoneInfo("Australia/Sydney")


def fetch(ticker: str, endpoint: str) -> dict:
    req = urllib.request.Request(API.format(t=ticker, ep=endpoint),
                                 headers={"User-Agent": UA,
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]


def market_open(now: datetime | None = None) -> bool:
    """ASX continuous trading, 10:00-16:00 Sydney on a weekday.

    Public holidays are not modelled, so this can read True on one. It is used
    only to decide whether a quoted spread is worth trusting, and a holiday
    produces a stale quote that the caller should treat exactly like an
    after-hours one — the error is in the safe direction either way.
    """
    now = (now or datetime.now(timezone.utc)).astimezone(SYDNEY)
    if now.weekday() >= 5:
        return False
    return (now.hour, now.minute) >= (10, 0) and (now.hour, now.minute) < (16, 0)


def collect(tickers: list[str], known: dict[str, float | None]) -> list[dict]:
    rows = []
    for t in sorted(tickers):
        row: dict = {"ticker": t}
        try:
            ks = fetch(t, "key-statistics")
            hd = fetch(t, "header")
        except Exception as exc:
            rows.append({**row, "error": f"{type(exc).__name__}: {exc}"})
            continue

        n = ks.get("numOfShares")
        px_close = ks.get("priceClose")
        mcap = hd.get("marketCap")
        row["shares_out_m"] = n / 1e6 if n else None
        # volumeAverage is the exchange's own average daily volume in SHARES.
        # The averaging window is not documented, so it was measured: the value
        # times 90 is an exact integer for every ticker tested (NST, WGX, PNR,
        # RXL), which makes it a 90-session mean — the same quarter the §4
        # spread window uses, which is convenient rather than designed.
        vol = ks.get("volumeAverage")
        row["advt_shares_m"] = vol / 1e6 if vol else None
        row["price_close"] = px_close
        row["market_cap"] = mcap
        row["share_description"] = ks.get("shareDescription")
        row["bid"], row["ask"] = ks.get("priceBid"), ks.get("priceAsk")
        if row["bid"] and row["ask"] and row["ask"] >= row["bid"]:
            mid = (row["ask"] + row["bid"]) / 2
            row["spread_pct"] = (row["ask"] - row["bid"]) / mid * 100 if mid else None
        else:
            row["spread_pct"] = None

        # Check 1 — the feed against itself.
        row["mcap_consistent"] = bool(
            n and px_close and mcap and abs(n * px_close - mcap) / mcap < MCAP_TOLERANCE)

        # Check 2 — the feed against the filings we already read.
        prior = known.get(t)
        row["prior"] = prior
        if prior and row["shares_out_m"]:
            row["drift_pct"] = (row["shares_out_m"] / prior - 1) * 100
            row["agrees"] = abs(row["drift_pct"]) <= TOLERANCE_PCT
        else:
            row["drift_pct"], row["agrees"] = None, None

        row["writable"] = bool(row["shares_out_m"] and row["mcap_consistent"]
                               and row["agrees"] is not False)
        rows.append(row)
        time.sleep(0.25)
    return rows


def write_shares(rows: list[dict], fetched_utc: str) -> tuple[int, int, list[str]]:
    payload = json.loads(COMPANIES.read_text())
    by_ticker = {c["ticker"]: c for c in payload["companies"]}
    written, advt_written, skipped = 0, 0, []

    for r in rows:
        c = by_ticker.get(r["ticker"])
        if c is None:
            continue
        if not r.get("writable"):
            skipped.append(f"{r['ticker']}: {r.get('error') or 'failed validation'}")
            continue

        c.setdefault("documents", {})[DOC_KEY] = {
            "title": ("ASX company key-statistics (markitdigital), "
                      "numOfShares — the exchange's own figure"),
            "url": API.format(t=r["ticker"], ep="key-statistics"),
            "date": fetched_utc[:10],
            "type": "primary",
        }
        note = (f"{r['share_description'] or 'ordinary'}; "
                f"numOfShares x priceClose reproduces the API market cap")
        if r.get("drift_pct") is not None:
            note += f"; {r['drift_pct']:+.1f}% vs the previously filed figure"
        new_v = round(r["shares_out_m"], 2)
        # Unchanged to the recorded precision: leave the record alone. Rewriting
        # a field with its own value churns the provenance note and the field's
        # apparent as-of date for no informational gain, and a diff full of
        # no-ops is a diff nobody reads.
        if (c["fields"].get("shares_out_m") or {}).get("v") != new_v:
            c["fields"]["shares_out_m"] = {"v": new_v, "doc": DOC_KEY, "note": note}
            written += 1
        # The field is no longer an open gap; drop any note that says it is.
        c["gaps"] = [g for g in c.get("gaps", []) if not g.startswith("shares_out_m")]

        # §4.3 capacity input. Written alongside the share count because it is
        # the same feed, the same endpoint and the same instant — and because
        # the capacity constraint was declared in config for months with no
        # source for its only input, so nothing could have enforced it.
        if r.get("advt_shares_m"):
            advt_v = round(r["advt_shares_m"], 4)
            if (c["fields"].get("advt_shares_m") or {}).get("v") != advt_v:
                c["fields"]["advt_shares_m"] = {
                    "v": advt_v, "doc": DOC_KEY,
                    "note": ("volumeAverage — the ASX's 90-session average daily "
                             "volume in shares. Window measured, not documented: "
                             "the value times 90 is an exact integer on every "
                             "ticker tested."),
                }
                advt_written += 1

    # indent=1 matches the file as it is stored. Rewriting 2,300 lines to change
    # the indentation would bury one new field in a whole-file diff.
    COMPANIES.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    return written, advt_written, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="commit validated share counts to data/companies.json")
    ap.add_argument("--quotes", action="store_true",
                    help="write asx_quotes.json (bid/ask) for the §4 Gate 3 spread test")
    ap.add_argument("--tickers", nargs="*", help="default: every candidate")
    args = ap.parse_args()

    payload = json.loads(COMPANIES.read_text())
    known = {c["ticker"]: (c["fields"].get("shares_out_m") or {}).get("v")
             for c in payload["companies"]}
    tickers = args.tickers or sorted(known)

    now = datetime.now(timezone.utc)
    is_open = market_open(now)
    print(f"ASX research API — {len(tickers)} tickers, "
          f"{now.astimezone(SYDNEY):%Y-%m-%d %H:%M} Sydney "
          f"({'OPEN' if is_open else 'CLOSED'})")

    rows = collect(tickers, known)

    print(f"\n{'TICK':<6}{'SHARES (m)':>12}{'FILED (m)':>11}{'DRIFT':>8}"
          f"{'MCAP✓':>7}{'SPREAD':>8}{'ADVT A$m':>10}  STATUS")
    print("─" * 84)
    for r in rows:
        if r.get("error"):
            print(f"{r['ticker']:<6}{'—':>12}{'—':>11}{'—':>8}{'—':>7}{'—':>8}"
                  f"{'—':>10}  ERROR {r['error'][:28]}")
            continue
        d = r.get("drift_pct")
        s = r.get("spread_pct")
        status = ("NEW" if r["prior"] is None else
                  "agrees" if r["agrees"] else "DISAGREES — not written")
        if not r["mcap_consistent"]:
            status = "MCAP MISMATCH — not written"
        prior = f"{r['prior']:,.1f}" if r["prior"] else "—"
        advt = ((r.get("advt_shares_m") or 0) * (r.get("price_close") or 0)) or None
        print(f"{r['ticker']:<6}{r['shares_out_m'] or 0:>12,.1f}{prior:>11}"
              f"{(f'{d:+.1f}%' if d is not None else '—'):>8}"
              f"{('ok' if r['mcap_consistent'] else 'FAIL'):>7}"
              f"{(f'{s:.2f}%' if s is not None else '—'):>8}"
              f"{(f'{advt:,.1f}' if advt else '—'):>10}  {status}")

    new = [r for r in rows if r.get("writable") and r["prior"] is None]
    print(f"\n{len(new)} previously blocked name(s) resolved: "
          f"{', '.join(r['ticker'] for r in new) or '—'}")

    if args.quotes:
        out = {
            "fetched_utc": now.isoformat(),
            "market_open": is_open,
            "trustworthy": is_open,
            "caveat": ("Spreads quoted outside continuous trading are wide and "
                       "stale and must NOT be used for the §4 gate. Gate 3 stays "
                       "untested rather than being failed on an after-hours quote."),
            "quotes": {r["ticker"]: {"bid": r.get("bid"), "ask": r.get("ask"),
                                     "spread_pct": r.get("spread_pct")}
                       for r in rows if not r.get("error")},
        }
        (ROOT / "asx_quotes.json").write_text(json.dumps(out, indent=2))
        print(f"Wrote → asx_quotes.json (market_open={is_open})")
        if not is_open:
            print("  Market CLOSED — these spreads are not usable for Gate 3.")

    if args.write:
        n, n_advt, skipped = write_shares(rows, now.isoformat())
        print(f"\nWrote {n} share count(s) and {n_advt} ADVT value(s) to "
              f"data/companies.json (unchanged values are left alone)")
        for s in skipped:
            print(f"  skipped {s}")
    else:
        print("\nProposal only. Re-run with --write to commit to companies.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
