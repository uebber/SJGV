from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import build_index as B


ROOT = Path(__file__).resolve().parents[1]


class Gate1CapVariantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg, cls.companies, *_ = B.load_data()
        fixture = json.loads(
            (ROOT / "tests/fixtures/2026-08-21-capital-baseline.json").read_text()
        )
        cls.prices = {
            ticker: {"price": record["price"]}
            for ticker, record in fixture["market_inputs"].items()
        }

    def test_top_ten_are_selected_and_weighted_by_market_cap(self) -> None:
        rows, rejected = B.compute_gate1_cap_weights(
            self.companies, self.prices, self.cfg)

        self.assertEqual(len(rows), 10)
        self.assertEqual(len(rejected), 7)
        self.assertAlmostEqual(sum(row["weight"] for row in rows), 1.0)

        ranked = sorted(
            self.companies,
            key=lambda company: (
                -(company["shares_out_m"]
                  * self.prices[company["ticker"]]["price"]),
                company["ticker"],
            ),
        )
        selected = ranked[:10]
        total = sum(
            company["shares_out_m"] * self.prices[company["ticker"]]["price"]
            for company in selected
        )
        self.assertEqual(
            [row["ticker"] for row in rows],
            [company["ticker"] for company in selected],
        )
        for rank, company in enumerate(selected, start=1):
            row = next(r for r in rows if r["ticker"] == company["ticker"])
            expected_cap = (
                company["shares_out_m"] * self.prices[company["ticker"]]["price"]
            )
            self.assertEqual(row["market_cap_rank"], rank)
            self.assertAlmostEqual(row["market_cap_aud_m"], expected_cap)
            self.assertAlmostEqual(row["weight"], expected_cap / total)

        self.assertEqual(
            [row["market_cap_rank"] for row in rejected],
            list(range(11, 18)),
        )

    def test_later_gates_and_ounce_inputs_do_not_reach_variant(self) -> None:
        rows, _ = B.compute_gate1_cap_weights(
            self.companies, self.prices, self.cfg)
        tickers = {row["ticker"] for row in rows}

        # These names currently fail or cannot complete later SJGV stages, but
        # their large enough market caps still put them in the parallel top ten.
        self.assertTrue({"OBM", "WGX"} <= tickers)
        self.assertTrue(any(
            row["ticker"] == "BGL" and row["reason"].startswith("CONSTITUENT LIMIT")
            for row in B.compute_gate1_cap_weights(
                self.companies, self.prices, self.cfg)[1]
        ))

        stripped = copy.deepcopy(self.companies[0])
        for field in (
            "aisc_aud_oz", "production_koz_yr", "pp_moz",
            "mi_non_reserve_moz", "inferred_moz", "gold_nav_share",
            "remaining_execution_capex_aud_m",
        ):
            stripped.pop(field, None)
        stripped_rows, stripped_rejected = B.compute_gate1_cap_weights(
            [stripped], self.prices, self.cfg)
        self.assertEqual(stripped_rejected, [])
        self.assertEqual(stripped_rows[0]["weight"], 1.0)

    def test_mixed_jurisdiction_market_cap_is_not_haircut(self) -> None:
        companies = [
            copy.deepcopy(next(c for c in self.companies if c["ticker"] == ticker))
            for ticker in ("NST", "EVN")
        ]
        rows, rejected = B.compute_gate1_cap_weights(companies, self.prices, self.cfg)
        self.assertEqual(rejected, [])

        caps = {
            c["ticker"]: c["shares_out_m"] * self.prices[c["ticker"]]["price"]
            for c in companies
        }
        total = sum(caps.values())
        self.assertAlmostEqual(
            next(row for row in rows if row["ticker"] == "EVN")["weight"],
            caps["EVN"] / total,
        )

    def test_gate1_and_market_cap_gaps_reject_instead_of_defaulting(self) -> None:
        base = copy.deepcopy(self.companies[0])
        cases = [
            ("eligible_ounce_share", None, "eligible_ounce_share missing"),
            ("eligible_ounce_share", 0.0, "no ounces in a Tier A jurisdiction"),
            ("ineligible_nav_share", None, "entity cap is untested"),
            ("ineligible_nav_share", 0.26, "above 25% entity cap"),
            ("shares_out_m", None, "share count unavailable"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field, value=value):
                company = copy.deepcopy(base)
                company[field] = value
                rows, rejected = B.compute_gate1_cap_weights(
                    [company], self.prices, self.cfg)
                self.assertEqual(rows, [])
                self.assertIn(message, rejected[0]["reason"])

    def test_constituent_limit_must_be_a_positive_integer(self) -> None:
        for value in (0, -1, 10.0, True, None):
            with self.subTest(value=value):
                cfg = copy.deepcopy(self.cfg)
                cfg["variants"]["gate1_cap"]["max_constituents"] = value
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    B.compute_gate1_cap_weights(
                        self.companies, self.prices, cfg)


if __name__ == "__main__":
    unittest.main()
