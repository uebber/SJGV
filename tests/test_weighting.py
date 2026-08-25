from __future__ import annotations

import copy
import unittest

import build_index as B


class OptimisedWeightingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg, *_ = B.load_data()

    @staticmethod
    def rows(signals: list[float]) -> list[dict]:
        return [
            {
                "ticker": f"P{i}", "raw": signal, "sleeve": "producer",
                "single_asset": False, "largest_asset_pp_share": 0.5,
                "guidance_delivery": {"portfolio_treatment": "NONE"},
            }
            for i, signal in enumerate(signals)
        ]

    def test_optimiser_maximises_value_at_effective_n_floor(self) -> None:
        rows = self.rows([4.0, 3.0, 2.0, 1.0])
        result = B.apply_constraints(rows, self.cfg)

        self.assertAlmostEqual(sum(row["weight"] for row in rows), 1.0)
        self.assertAlmostEqual(B.effective_n(rows), 2.6, places=8)
        self.assertAlmostEqual(result["effective_n_target"], 2.6)
        self.assertGreater(rows[0]["weight"], rows[1]["weight"])
        self.assertGreater(rows[1]["weight"], rows[2]["weight"])
        self.assertGreaterEqual(rows[2]["weight"], rows[3]["weight"])

    def test_large_signal_gap_can_exceed_old_general_cap(self) -> None:
        rows = self.rows([100.0, 2.0, 1.0])
        B.apply_constraints(rows, self.cfg)

        self.assertGreater(rows[0]["weight"], 0.15)
        self.assertAlmostEqual(B.effective_n(rows), 1.95, places=8)

    def test_exact_ties_receive_equal_weights_when_equally_constrained(self) -> None:
        rows = self.rows([3.0, 2.0, 2.0, 1.0])
        B.assign_value_ranks(rows, self.cfg)
        B.apply_constraints(rows, self.cfg)

        self.assertEqual(rows[1]["value_rank"], 2.5)
        self.assertEqual(rows[2]["value_rank"], 2.5)
        self.assertAlmostEqual(rows[1]["weight"], rows[2]["weight"])

    def test_single_asset_and_delivery_caps_remain_binding(self) -> None:
        rows = self.rows([100.0, 90.0] + [float(i) for i in range(8, 0, -1)])
        rows[0]["single_asset"] = True
        rows[0]["largest_asset_pp_share"] = 0.9
        rows[1]["guidance_delivery"] = {"portfolio_treatment": "CAP"}

        B.apply_constraints(rows, self.cfg)

        self.assertAlmostEqual(rows[0]["weight"], 0.075)
        self.assertAlmostEqual(rows[1]["weight"], 0.05)

    def test_unknown_weighting_configuration_fails_closed(self) -> None:
        cfg = copy.deepcopy(self.cfg)
        cfg["weighting"]["method"] = "descending_linear_rank"
        with self.assertRaisesRegex(ValueError, "max_oz_per_ev_at_effective_n"):
            B.assign_value_ranks([{"ticker": "A", "raw": 1.0}], cfg)

    def test_nonpositive_signal_cannot_enter_optimizer(self) -> None:
        rows = self.rows([1.0, 0.0])
        with self.assertRaisesRegex(ValueError, "requires every value signal"):
            B.apply_constraints(rows, self.cfg)

    def test_infeasible_effective_n_fails_closed(self) -> None:
        cfg = copy.deepcopy(self.cfg)
        cfg["weighting"]["effective_n_fraction"] = 1.0
        rows = self.rows([3.0, 2.0, 1.0])
        rows[0]["single_asset"] = True
        rows[0]["largest_asset_pp_share"] = 1.0
        with self.assertRaisesRegex(ValueError, "effective N"):
            B.apply_constraints(rows, cfg)

    def test_unsupported_equity_price_basis_fails_before_tws_connection(self) -> None:
        with self.assertRaisesRegex(ValueError, "latest_asx_daily_close"):
            B.fetch_market_data([], equity_price_basis="live_quote")


if __name__ == "__main__":
    unittest.main()
