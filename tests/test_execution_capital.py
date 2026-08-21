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

    def test_weight_pipeline_adds_execution_capital_for_both_sleeves(self) -> None:
        for ticker in ("NST", "RXL"):
            rows, rejected = B.compute_raw_weights(
                [self.companies[ticker]], self.prices, {}, self.gold, self.cfg,
                anchor_gold=self.anchor, as_of=self.as_of,
            )
            self.assertEqual(rejected, [])
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertAlmostEqual(
                row["all_in_ev_aud_m"],
                row["ev_aud_m"] + row["remaining_execution_capex_aud_m"],
            )
        self.assertEqual(rows[0]["residual_funding_gap_aud_m"], 0.0)

    def test_unresolved_execution_capital_rejects_instead_of_defaulting_zero(self) -> None:
        rows, rejected = B.compute_raw_weights(
            [self.companies["WGX"]], self.prices, {}, self.gold, self.cfg,
            anchor_gold=self.anchor, as_of=self.as_of,
        )
        self.assertEqual(rows, [])
        self.assertIn("EXECUTION CAPITAL", rejected[0]["reason"])
        self.assertIn("UNRESOLVED", rejected[0]["reason"])


if __name__ == "__main__":
    unittest.main()
