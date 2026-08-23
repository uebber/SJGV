from __future__ import annotations

import copy
import json
import unittest
from datetime import date
from pathlib import Path

import build_index as B


ROOT = Path(__file__).resolve().parents[1]


class ExecutionCapitalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg, companies, *_ = B.load_data()
        cls.companies = {company["ticker"]: company for company in companies}
        fixture = json.loads(
            (ROOT / "tests/fixtures/2026-08-21-capital-baseline.json").read_text()
        )
        cls.prices = {
            ticker: {"price": record["price"]}
            for ticker, record in fixture["market_inputs"].items()
        }
        cls.gold = fixture["baseline"]["gold_aud_oz"]
        cls.anchor = fixture["baseline"]["gate2_anchor"]["anchor_aud"]
        cls.as_of = fixture["baseline"]["data_sourced"]

    def test_data_layer_has_no_ambiguous_or_stored_derived_field(self) -> None:
        payload = json.loads((ROOT / "data/companies.json").read_text())
        for company in payload["companies"]:
            fields = company["fields"]
            self.assertNotIn("remaining_capex_aud_m", fields)
            self.assertNotIn("residual_funding_gap_aud_m", fields)
            if company["sleeve"] in {"near_producer", "developer"}:
                self.assertIn("remaining_execution_capex_aud_m", fields)

    def test_fully_funded_project_keeps_positive_economic_capital(self) -> None:
        rox = self.companies["RXL"]
        gap = B.derive_residual_funding_gap(rox, self.cfg)
        capital = B.execution_capital_ledger(
            rox, 565.0, self.cfg, date.fromisoformat(self.as_of)
        )
        self.assertEqual(gap["state"], "POINT")
        self.assertEqual(gap["value_aud_m"], 0.0)
        self.assertAlmostEqual(capital["effective_aud_m"], 319.723)
        nav = B.nav_model.value_company(
            rox, self.gold, self.cfg, B.confidence_weights(self.cfg)
        )
        self.assertAlmostEqual(
            nav["remaining_execution_capex_aud_m"], 319.723
        )

    def test_project_funding_never_reduces_denominator_capital(self) -> None:
        base = self.companies["RXL"]
        less_funding = copy.deepcopy(base)
        less_funding["available_project_funding_aud_m"] = 0.0
        self.assertNotEqual(
            B.derive_residual_funding_gap(base, self.cfg)["value_aud_m"],
            B.derive_residual_funding_gap(less_funding, self.cfg)["value_aud_m"],
        )
        for company in (base, less_funding):
            capital = B.execution_capital_ledger(
                company, 565.0, self.cfg, date.fromisoformat(self.as_of)
            )
            self.assertAlmostEqual(capital["effective_aud_m"], 319.723)

    def test_lower_bound_and_unresolved_cannot_enter_denominator(self) -> None:
        company = copy.deepcopy(self.companies["RXL"])
        for state in ("LOWER_BOUND", "UNRESOLVED"):
            company[f"{B.EXECUTION_CAPITAL_FIELD}_evidence_state"] = state
            if state == "UNRESOLVED":
                company[B.EXECUTION_CAPITAL_FIELD] = None
            result = B.execution_capital_ledger(
                company, 565.0, self.cfg, date.fromisoformat(self.as_of)
            )
            self.assertFalse(result["ok"])

    def test_schema_rejects_unknown_state_and_unresolved_value(self) -> None:
        record = {
            "ticker": "TEST", "sleeve": "producer",
            "documents": {"source": {"date": "2026-06-30", "type": "primary"}},
            "fields": {
                B.EXECUTION_CAPITAL_FIELD: {
                    "v": 1.0, "evidence_state": "UNRESOLVED", "doc": "source"
                }
            },
        }
        errors = B._validate_capital_schema(record)
        self.assertTrue(any("UNRESOLVED but carries value" in e for e in errors))
        record["fields"][B.EXECUTION_CAPITAL_FIELD]["evidence_state"] = "ESTIMATE"
        errors = B._validate_capital_schema(record)
        self.assertTrue(any("invalid evidence_state" in e for e in errors))

    def test_materiality_can_only_remove_a_sourced_small_amount(self) -> None:
        company = copy.deepcopy(self.companies["RXL"])
        company[B.EXECUTION_CAPITAL_FIELD] = 5.0
        capital = B.execution_capital_ledger(
            company, 1_000.0, self.cfg, date.fromisoformat(self.as_of)
        )
        self.assertTrue(capital["ok"])
        self.assertEqual(capital["disclosed_aud_m"], 5.0)
        self.assertEqual(capital["effective_aud_m"], 0.0)

    def test_carry_forward_expires_without_assumed_spend_down(self) -> None:
        company = copy.deepcopy(self.companies["RXL"])
        field = B.EXECUTION_CAPITAL_FIELD
        company[f"{field}_evidence_state"] = "CARRY_FORWARD"
        company[f"{field}_as_of"] = "2026-01-01"
        in_time = B.resolve_execution_capital(company, self.cfg, date(2026, 6, 30))
        expired = B.resolve_execution_capital(company, self.cfg, date(2026, 8, 1))
        self.assertTrue(in_time["ok"])
        self.assertAlmostEqual(in_time["value_aud_m"], 319.723)
        self.assertFalse(expired["ok"])

    def test_directional_funding_bound_does_not_create_a_favourable_pass(self) -> None:
        auc = self.companies["AUC"]
        gap = B.derive_residual_funding_gap(auc, self.cfg)
        self.assertEqual(gap["state"], "UPPER_BOUND")
        self.assertEqual(gap["lower_aud_m"], 0.0)
        self.assertEqual(gap["upper_aud_m"], 354.0)
        verdict = B.gate2_survival(auc, self.anchor, 800.0, self.cfg)
        self.assertFalse(verdict["pass"])  # D2 fails; D3 is explicitly unresolved.
        self.assertIn("D3 residual funding gap spans", verdict["reason"])

    def test_producer_uses_standard_ev_and_keeps_capital_reporting_only(self) -> None:
        rows, rejected = B.compute_raw_weights(
            [self.companies["GMD"]], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rejected, [])
        row = rows[0]
        self.assertEqual(row["remaining_execution_capex_aud_m"], 280.0)
        self.assertIsNone(row["execution_capital_in_denominator_aud_m"])
        self.assertEqual(row["all_in_ev_aud_m"], row["ev_aud_m"])

    def test_producer_execution_capital_may_be_absent_without_zero_imputation(self) -> None:
        payload = json.loads((ROOT / "data/companies.json").read_text())
        record = copy.deepcopy(next(c for c in payload["companies"]
                                    if c["ticker"] == "GMD"))
        record["fields"].pop(B.EXECUTION_CAPITAL_FIELD)
        for project in record["execution_capital_projects"]:
            for key in (B.EXECUTION_CAPITAL_FIELD,
                        "execution_capital_range_aud_m",
                        "execution_capital_state", "execution_capital_doc"):
                project.pop(key, None)
        self.assertEqual(B._validate_capital_schema(record), [])

        company = B._flatten(record)
        rows, rejected = B.compute_raw_weights(
            [company], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rejected, [])
        self.assertIsNone(rows[0]["remaining_execution_capex_aud_m"])
        self.assertIsNone(rows[0]["execution_capital_in_denominator_aud_m"])
        self.assertEqual(rows[0]["all_in_ev_aud_m"], rows[0]["ev_aud_m"])

    def test_near_producer_still_requires_and_adds_execution_capital(self) -> None:
        company = copy.deepcopy(self.companies["RXL"])
        company["sleeve"] = "near_producer"
        rows, rejected = B.compute_raw_weights(
            [company], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rejected, [])
        row = rows[0]
        self.assertAlmostEqual(row["execution_capital_in_denominator_aud_m"], 319.723)
        self.assertAlmostEqual(row["all_in_ev_aud_m"], row["ev_aud_m"] + 319.723)

    def test_developer_still_requires_gross_capital_despite_full_funding(self) -> None:
        rows, rejected = B.compute_raw_weights(
            [self.companies["RXL"]], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rejected, [])
        row = rows[0]
        self.assertEqual(row["residual_funding_gap_aud_m"], 0.0)
        self.assertAlmostEqual(row["execution_capital_in_denominator_aud_m"], 319.723)
        self.assertAlmostEqual(row["all_in_ev_aud_m"], row["ev_aud_m"] + 319.723)

    def test_unresolved_producer_capital_does_not_reject_wgx_or_bgl(self) -> None:
        for ticker in ("WGX", "BGL"):
            rows, rejected = B.compute_raw_weights(
                [self.companies[ticker]], self.prices, {}, self.gold, self.cfg,
                anchor_gold=self.anchor, as_of=self.as_of,
            )
            self.assertEqual(rejected, [])
            self.assertEqual(rows[0]["gate2"]["health"], "AMBER")
            self.assertIsNone(rows[0]["remaining_execution_capex_aud_m"])
            self.assertEqual(rows[0]["all_in_ev_aud_m"], rows[0]["ev_aud_m"])

    def test_unresolved_near_producer_capital_still_rejects(self) -> None:
        company = copy.deepcopy(self.companies["RXL"])
        company["sleeve"] = "near_producer"
        company[B.EXECUTION_CAPITAL_FIELD] = None
        company[f"{B.EXECUTION_CAPITAL_FIELD}_evidence_state"] = "UNRESOLVED"
        rows, rejected = B.compute_raw_weights(
            [company], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rows, [])
        self.assertIn("EXECUTION CAPITAL", rejected[0]["reason"])
        self.assertIn("UNRESOLVED", rejected[0]["reason"])

    def test_missing_producer_net_debt_is_gate2_untested(self) -> None:
        company = copy.deepcopy(self.companies["GMD"])
        company["net_debt_aud_m"] = None
        verdict = B.gate2_survival(company, self.gold, 1_000.0, self.cfg)
        self.assertIsNone(verdict["pass"])
        self.assertEqual(verdict["health"], "UNTESTED")
        self.assertIn("net debt", verdict["reason"])

    def test_bc8_remains_excluded_on_missing_aisc(self) -> None:
        rows, rejected = B.compute_raw_weights(
            [self.companies["BC8"]], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rows, [])
        self.assertIn("AISC unsourced", rejected[0]["reason"])

    def test_project_capital_reconciles_to_company_records(self) -> None:
        payload = json.loads((ROOT / "data/companies.json").read_text())
        for record in payload["companies"]:
            if record["sleeve"] == "developer":
                continue
            self.assertEqual(B._validate_capital_schema(record), [])

        broken = copy.deepcopy(next(
            c for c in payload["companies"] if c["ticker"] == "GMD"))
        broken["execution_capital_projects"][0][
            "remaining_execution_capex_aud_m"] += 1.0
        errors = B._validate_capital_schema(broken)
        self.assertTrue(any("project execution capital does not reconcile" in e
                            for e in errors))

    def test_explicit_dates_detect_under_and_over_coverage(self) -> None:
        under = B.gate2_capital_interval(self.companies["NST"], self.cfg)
        over = B.gate2_capital_interval(self.companies["EVN"], self.cfg)
        self.assertEqual(under["projects"][0]["coverage_state"], "UNDER")
        self.assertEqual(under["state"], "LOWER_BOUND")
        self.assertEqual(over["projects"][0]["coverage_state"], "OVER")
        self.assertEqual(over["state"], "UPPER_BOUND")

        payload = json.loads((ROOT / "data/companies.json").read_text())
        raw = {c["ticker"]: c for c in payload["companies"]}
        wrong_under = copy.deepcopy(raw["NST"])
        wrong_under["execution_capital_projects"][0][
            "committed_capex_state"] = "POINT"
        self.assertTrue(any("under-coverage requires LOWER_BOUND" in e
                            for e in B._validate_capital_schema(wrong_under)))
        wrong_over = copy.deepcopy(raw["EVN"])
        wrong_over["execution_capital_projects"][0][
            "committed_capex_state"] = "POINT"
        self.assertTrue(any("over-coverage requires UPPER_BOUND" in e
                            for e in B._validate_capital_schema(wrong_over)))

    def test_lower_bound_health_pass_is_amber_but_distress_is_red(self) -> None:
        nst = self.companies["NST"]
        amber = B.gate2_survival(nst, self.gold, 1_000.0, self.cfg)
        self.assertTrue(amber["pass"])
        self.assertEqual(amber["health"], "AMBER")
        self.assertFalse(amber["detail"]["capital_evidence_complete"])

        failure = copy.deepcopy(nst)
        project = failure["execution_capital_projects"][0]
        project["committed_within_gate2_horizon_aud_m"] = 10_000.0
        project["committed_capex_range_aud_m"] = [10_000.0, 10_000.0]
        failure["committed_capex_aud_m"] = 10_000.0
        failed = B.gate2_survival(failure, self.gold, 1_000.0, self.cfg)
        self.assertFalse(failed["pass"])
        self.assertEqual(failed["health"], "RED")

    def test_finite_upper_bound_can_prove_green_or_red(self) -> None:
        evn = self.companies["EVN"]
        passed = B.gate2_survival(evn, self.gold, 10_000.0, self.cfg)
        self.assertTrue(passed["pass"])
        self.assertEqual(passed["health"], "GREEN")

        uncertain = copy.deepcopy(evn)
        uncertain["execution_capital_projects"][0][
            "committed_within_gate2_horizon_aud_m"] = 10_000.0
        uncertain["committed_capex_aud_m"] = 10_000.0
        verdict = B.gate2_survival(uncertain, self.gold, 10_000.0, self.cfg)
        self.assertFalse(verdict["pass"])
        self.assertEqual(verdict["health"], "RED")

    def test_manageable_rescue_is_eligible_amber(self) -> None:
        company = copy.deepcopy(self.companies["OBM"])
        company["undrawn_facilities_aud_m"] = B.creditable_undrawn(
            company, self.cfg, date.fromisoformat(self.as_of)
        )[0]
        verdict = B.gate2_survival(
            company, self.gold, 3_100.0, self.cfg
        )
        self.assertTrue(verdict["pass"])
        self.assertEqual(verdict["health"], "AMBER")
        self.assertGreater(verdict["detail"]["rescue_capital_aud_m"], 0.0)
        self.assertLessEqual(
            verdict["detail"]["rescue_capital_of_mcap"],
            self.cfg["gate2"]["producer_max_rescue_capital_of_mcap"],
        )
        self.assertLessEqual(
            verdict["detail"]["recovery_years"],
            self.cfg["gate2"]["producer_max_recovery_years"],
        )

    def test_producer_health_thresholds_are_validated(self) -> None:
        broken = copy.deepcopy(self.cfg)
        broken["gate2"]["producer_max_rescue_capital_of_mcap"] = 1.1
        with self.assertRaisesRegex(ValueError, "must be in"):
            B.gate2_survival(
                self.companies["EVN"], self.gold, 10_000.0, broken
            )

    def test_infeasible_survivor_set_cannot_breach_caps(self) -> None:
        rows = [
            {"ticker": "P1", "sleeve": "producer", "single_asset": False,
             "weight": 0.4},
            {"ticker": "P2", "sleeve": "producer", "single_asset": False,
             "weight": 0.4},
            {"ticker": "D1", "sleeve": "developer", "single_asset": True,
             "weight": 0.2},
        ]
        with self.assertRaisesRegex(ValueError, "constraint set is infeasible"):
            B.apply_constraints(rows, self.cfg)


if __name__ == "__main__":
    unittest.main()
