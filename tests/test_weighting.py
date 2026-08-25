from __future__ import annotations

import copy
import unittest

import build_index as B


class RankWeightingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg, *_ = B.load_data()

    def test_descending_linear_rank_points_replace_signal_magnitudes(self) -> None:
        rows = [
            {"ticker": "HIGH", "raw": 100.0},
            {"ticker": "MID", "raw": 2.0},
            {"ticker": "LOW", "raw": 1.0},
        ]

        B.apply_rank_weights(rows, self.cfg)

        by_ticker = {row["ticker"]: row for row in rows}
        self.assertEqual(by_ticker["HIGH"]["value_rank"], 1.0)
        self.assertEqual(by_ticker["MID"]["value_rank"], 2.0)
        self.assertEqual(by_ticker["LOW"]["value_rank"], 3.0)
        self.assertEqual(by_ticker["HIGH"]["rank_points"], 3.0)
        self.assertEqual(by_ticker["MID"]["rank_points"], 2.0)
        self.assertEqual(by_ticker["LOW"]["rank_points"], 1.0)
        self.assertAlmostEqual(by_ticker["HIGH"]["weight"], 3 / 6)
        self.assertAlmostEqual(by_ticker["MID"]["weight"], 2 / 6)
        self.assertAlmostEqual(by_ticker["LOW"]["weight"], 1 / 6)

    def test_exact_ties_share_average_occupied_rank_points(self) -> None:
        rows = [
            {"ticker": "A", "raw": 3.0},
            {"ticker": "B", "raw": 2.0},
            {"ticker": "C", "raw": 2.0},
            {"ticker": "D", "raw": 1.0},
        ]

        B.apply_rank_weights(rows, self.cfg)

        by_ticker = {row["ticker"]: row for row in rows}
        self.assertEqual(by_ticker["B"]["value_rank"], 2.5)
        self.assertEqual(by_ticker["C"]["value_rank"], 2.5)
        self.assertEqual(by_ticker["B"]["rank_points"], 2.5)
        self.assertEqual(by_ticker["C"]["rank_points"], 2.5)
        self.assertEqual(by_ticker["B"]["weight"], by_ticker["C"]["weight"])
        self.assertAlmostEqual(sum(row["rank_points"] for row in rows), 10.0)
        self.assertAlmostEqual(sum(row["weight"] for row in rows), 1.0)

    def test_unknown_weighting_configuration_fails_closed(self) -> None:
        cfg = copy.deepcopy(self.cfg)
        cfg["weighting"]["method"] = "proportional_signal"
        with self.assertRaisesRegex(ValueError, "supports 'descending_linear_rank'"):
            B.apply_rank_weights([{"ticker": "A", "raw": 1.0}], cfg)

    def test_nonpositive_signal_cannot_receive_a_rank_weight(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires every value signal"):
            B.apply_rank_weights([{"ticker": "A", "raw": 0.0}], self.cfg)

    def test_cap_audit_includes_names_hit_during_redistribution(self) -> None:
        rows = [
            {"ticker": "A", "weight": 0.40},
            {"ticker": "B", "weight": 0.30},
            {"ticker": "C", "weight": 0.30},
        ]
        bound = B._cap_and_redistribute(rows, {"A": 0.20, "B": 0.35, "C": 0.60})

        self.assertEqual(bound, {"A", "B"})
        self.assertAlmostEqual(rows[0]["weight"], 0.20)
        self.assertAlmostEqual(rows[1]["weight"], 0.35)
        self.assertAlmostEqual(rows[2]["weight"], 0.45)

    def test_unsupported_equity_price_basis_fails_before_tws_connection(self) -> None:
        with self.assertRaisesRegex(ValueError, "latest_asx_daily_close"):
            B.fetch_market_data([], equity_price_basis="live_quote")


if __name__ == "__main__":
    unittest.main()
