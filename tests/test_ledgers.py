import unittest

import build_index as B


AS_OF = "2026-08-18"


def primary(date="2026-06-30"):
    return {"title": "fixture", "url": "https://example.test/fixture",
            "date": date, "type": "primary"}


def qualified_asset(capital=50.0, statement_date="2026-06-30"):
    return {
        "name": "Alpha",
        "resource_statement_doc": "rr",
        "categories": {
            "mi_non_reserve": {
                "gross_moz": 2.0,
                "ownership_share": 0.5,
                "eligible_jurisdiction_share": 1.0,
                "jurisdiction_code": "AU-WA",
                "doc": "rr",
            },
            "inferred": {
                "gross_moz": 1.0,
                "ownership_share": 0.5,
                "eligible_jurisdiction_share": 1.0,
                "jurisdiction_code": "AU-WA",
                "doc": "rr",
            },
        },
        "metallurgy_recovery": {
            "pass": True, "recovery_pct": 0.92, "doc": "rr"},
        "processing_route": {
            "pass": True, "basis": "existing plant", "doc": "rr"},
        "land_permitting": {
            "pass": True, "status": "operating tenure", "doc": "rr"},
        "capital_path": {
            "pass": True,
            "additional_future_capital_aud_m": capital,
            "doc": "rr",
        },
        "encumbrances": {
            "pass": True,
            "treatment": "all material royalties included in study economics",
            "doc": "rr",
        },
        "_statement_date_for_fixture": statement_date,
    }


def company(asset=None, statement_date="2026-06-30"):
    c = {
        "ticker": "AAA", "name": "Alpha Gold", "sleeve": "producer",
        "pp_moz": 1.0, "eligible_ounce_share": 1.0,
        "mi_non_reserve_moz": 1.0, "inferred_moz": 0.5,
        "hedge_share_fwd24m": 0.0, "production_koz_yr": 1.0,
        "gold_nav_share": 1.0, "ineligible_nav_share": 0.0,
        "shares_out_m": 100.0, "net_debt_aud_m": 0.0,
        "aisc_aud_oz": 1000.0, "undrawn_facilities_aud_m": 0.0,
        "committed_capex_aud_m": 0.0, "largest_asset_pp_share": 1.0,
        "_docs": {"rr": primary(statement_date)},
    }
    if asset is not None:
        asset = dict(asset)
        asset.pop("_statement_date_for_fixture", None)
        c["optionality_assets"] = [asset]
    return c


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.companies, _, cls.market, _ = B.load_data()
        cls.conf = B.confidence_weights(cls.cfg)

    def test_core_uses_pp_specific_jurisdiction_share(self):
        c = company()
        c["eligible_ounce_share"] = 0.8
        c["eligible_pp_share"] = 0.75
        c["hedge_share_fwd24m"] = 0.1
        core, reason = B.core_ledger(c, 2.0)
        self.assertEqual(reason, "ok")
        self.assertAlmostEqual(core["eligible_pp_moz"], 0.75)
        self.assertAlmostEqual(core["hedged_moz"], 0.0002)
        self.assertAlmostEqual(core["core_claim_moz"], 0.7498)

    def test_mixed_jurisdiction_requires_pp_specific_share(self):
        c = company()
        c["eligible_ounce_share"] = 0.8
        core, reason = B.core_ledger(c, 2.0)
        self.assertIsNone(core)
        self.assertIn("eligible_pp_share missing", reason)

    def test_qualified_asset_counts_attributable_ounces_and_capital(self):
        c = company(qualified_asset())
        ledger = B.optionality_ledger(c, self.conf, AS_OF, 18)
        self.assertEqual(ledger["status"], "qualified")
        self.assertAlmostEqual(ledger["counted_mi_non_reserve_moz"], 1.0)
        self.assertAlmostEqual(ledger["counted_inferred_moz"], 0.5)
        self.assertAlmostEqual(ledger["optionality_claim_moz"], 0.6)
        self.assertAlmostEqual(ledger["additional_future_capital_aud_m"], 50.0)

    def test_stale_statement_excludes_only_optionality(self):
        c = company(qualified_asset(statement_date="2023-01-01"),
                    statement_date="2023-01-01")
        ledger, reason = B.ounce_ledger(c, self.conf, 2.0, AS_OF, 18)
        self.assertEqual(reason, "ok")
        self.assertAlmostEqual(ledger["core_claim_moz"], 1.0)
        self.assertEqual(ledger["optionality_claim_moz"], 0.0)
        self.assertIn("months old",
                      ledger["optionality"]["excluded_assets"][0]["reasons"][0])

    def test_missing_capital_never_defaults_to_zero_on_counted_asset(self):
        asset = qualified_asset()
        del asset["capital_path"]["additional_future_capital_aud_m"]
        ledger = B.optionality_ledger(company(asset), self.conf, AS_OF, 18)
        self.assertEqual(ledger["optionality_claim_moz"], 0.0)
        reasons = ledger["excluded_assets"][0]["reasons"]
        self.assertTrue(any("additional_future_capital" in r for r in reasons))

    def test_weight_denominator_includes_producer_optionality_capital(self):
        c = company(qualified_asset())
        rows, rejected = B.compute_raw_weights(
            [c], {"AAA": {"price": 10.0}}, {}, 6000.0, self.cfg,
            anchor_gold=6000.0, as_of=AS_OF)
        self.assertEqual(rejected, [])
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["ev_aud_m"], 1000.0)
        self.assertAlmostEqual(rows[0]["optionality_capital_aud_m"], 50.0)
        self.assertAlmostEqual(rows[0]["funded_ev_aud_m"], 1050.0)

    def test_live_rxl_record_counts_only_dfs_scheduled_optionality(self):
        rxl = next(c for c in self.companies if c["ticker"] == "RXL")
        ledger = B.optionality_ledger(
            rxl, self.conf, self.market["_sourced"],
            self.cfg["optionality"]["max_resource_statement_age_months"])
        self.assertEqual(ledger["status"], "qualified")
        self.assertAlmostEqual(ledger["counted_mi_non_reserve_moz"], 0.048)
        self.assertAlmostEqual(ledger["counted_inferred_moz"], 0.178)
        self.assertAlmostEqual(ledger["unqualified_mi_non_reserve_moz"], 0.824)
        self.assertAlmostEqual(ledger["unqualified_inferred_moz"], 0.445)
        self.assertAlmostEqual(ledger["additional_future_capital_aud_m"], 382.6)


if __name__ == "__main__":
    unittest.main()
