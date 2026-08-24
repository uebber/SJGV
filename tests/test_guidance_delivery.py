from __future__ import annotations

import copy
import unittest

import build_index as B


class GuidanceDeliveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg, cls.companies, *_ = B.load_data()

    def test_live_producers_all_have_a_rating(self) -> None:
        for company in self.companies:
            if company["sleeve"] in {"producer", "near_producer"}:
                self.assertIsNotNone(company["_guidance_delivery"], company["ticker"])

    def test_approved_live_treatments_are_loaded(self) -> None:
        treatments = {
            c["ticker"]: c["_guidance_delivery"]["portfolio_treatment"]
            for c in self.companies if c.get("_guidance_delivery")
        }
        self.assertEqual({t for t, v in treatments.items() if v == "EXCLUDE"},
                         {"BC8", "BGL", "OBM", "PNR"})
        self.assertEqual({t for t, v in treatments.items() if v == "CAP"},
                         {"CYL", "WGX"})
        self.assertEqual(treatments["VAU"], "NONE")

    def test_delivery_cap_is_applied_before_redistribution(self) -> None:
        cfg = copy.deepcopy(self.cfg)
        rows = []
        for i in range(8):
            rows.append({
                "ticker": f"P{i}", "sleeve": "producer",
                "weight": 0.30 if i == 0 else 0.10,
                "single_asset": False, "largest_asset_pp_share": 0.5,
                "guidance_delivery": ({"portfolio_treatment": "CAP"}
                                      if i == 0 else {"portfolio_treatment": "NONE"}),
            })
        total = sum(r["weight"] for r in rows)
        for row in rows:
            row["weight"] /= total

        B.apply_constraints(rows, cfg)

        capped = next(r for r in rows if r["ticker"] == "P0")
        self.assertAlmostEqual(capped["weight"], 0.05)
        self.assertAlmostEqual(sum(r["weight"] for r in rows), 1.0)


if __name__ == "__main__":
    unittest.main()
