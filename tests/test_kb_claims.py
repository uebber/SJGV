"""Knowledge-plane migration invariants, and the rules a registered claim obeys.

The first class covers the additive backfill of the legacy projection. The rest
cover `kb.py register-claim`, which is the other write path into `claims.jsonl`:
a claim established by reading a source, which the migration exceptions
deliberately do not grandfather. Each test names the thing the store refuses and
why refusing it is the point.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import kb  # noqa: E402


class ClaimBackfillTest(unittest.TestCase):
    def test_claim_ids_are_stable_under_dictionary_order(self) -> None:
        left = {"subject": "NST", "predicate": "pp_moz", "scope": {"unit": "Moz"}}
        right = {"scope": {"unit": "Moz"}, "predicate": "pp_moz", "subject": "NST"}

        self.assertEqual(kb.stable_record_id("claim", left),
                         kb.stable_record_id("claim", right))

    def test_only_explicit_document_locations_become_exact(self) -> None:
        locator = kb.exact_legacy_locator(
            "reserve_price_aud", "Table 7 and pages 15-16 state the reserve decks")

        self.assertTrue(locator["exact"])
        self.assertIn("Table 7", locator["references"])
        self.assertIn("pages 15-16", locator["references"])
        self.assertIsNone(kb.exact_legacy_locator(
            "reserve_price_aud", "The issuer states the reserve deck is A$2,800/oz"))

    def test_market_json_fields_have_exact_pointers(self) -> None:
        self.assertEqual(kb.exact_legacy_locator("shares_out_m", None)["pointer"],
                         "/data/numOfShares")
        self.assertEqual(kb.exact_legacy_locator("advt_shares_m", None)["pointer"],
                         "/data/volumeAverage")

    def test_quarantine_record_has_no_candidate_value(self) -> None:
        claim = {"claim_id": "claim:sha256:" + "a" * 64, "state": "ACCEPTED"}

        record = kb.quarantine_record(
            claim, "/companies/0/fields/pp_moz",
            "SUPERSEDED_OR_REJECTED_LEGACY_CANDIDATE", "superseded")

        for forbidden in ("value", "typed_value", "reported_value", "range"):
            self.assertNotIn(forbidden, record)
        self.assertEqual(record["blocked_by"], claim["claim_id"])

    def test_unresolved_candidate_points_to_related_claim(self) -> None:
        claim = {"claim_id": "claim:sha256:" + "b" * 64, "state": "UNRESOLVED"}

        record = kb.quarantine_record(
            claim, "/companies/0/fields/committed_capex_aud_m",
            "WITHHELD_UNRESOLVED_CANDIDATE", "not established")

        self.assertEqual(record["related_claim"], claim["claim_id"])
        self.assertNotIn("blocked_by", record)


class BackfillPreservesResearchTest(unittest.TestCase):
    """A second migration run must not undo what research established.

    The backfill regenerates every legacy claim from `data/`. Without the merge
    it would drop registered claims and resurrect superseded ones, leaving two
    active claims for one key — the exact defect the strict audit refuses."""

    @staticmethod
    def backfilled(**over) -> dict:
        rec = {"claim_id": "claim:sha256:" + "1" * 64, "state": "PROVISIONAL",
               "projectable": True,
               "projection": {"file": "data/companies.json", "path": "/c/0/f/x"}}
        rec.update(over)
        return rec

    def test_a_registered_claim_survives_a_second_backfill(self) -> None:
        registered = {"claim_id": "claim:sha256:" + "2" * 64, "state": "ACCEPTED"}

        merged = kb.merge_backfill_claims([self.backfilled()],
                                          [self.backfilled(), registered])

        self.assertIn(registered, merged)

    def test_a_superseded_backfill_claim_is_not_resurrected(self) -> None:
        successor = "claim:sha256:" + "2" * 64
        previous = self.backfilled(state="SUPERSEDED", projectable=False,
                                   superseded_by=successor,
                                   projection_history=[{"path": "/c/0/f/x"}])
        del previous["projection"]

        merged = kb.merge_backfill_claims(
            [self.backfilled()], [previous, {"claim_id": successor, "state": "ACCEPTED"}])
        regenerated = merged[0]

        self.assertEqual(regenerated["state"], "SUPERSEDED")
        self.assertFalse(regenerated["projectable"])
        self.assertEqual(regenerated["superseded_by"], successor)
        self.assertNotIn("projection", regenerated)


def registered_document(tmp: Path, **over) -> dict:
    (tmp / "obj.pdf").write_bytes(b"%PDF-1.7 bytes")
    doc = {
        "document_id": "sha256:" + "c" * 64, "sha256": "c" * 64,
        "authority_tier": "T1", "authority_domains": ["exchange.lodgement"],
        "published_on": "2026-04-29", "object_locator": "obj.pdf",
        "url_aliases": [{"url": "https://announcements.asx.com.au/asxpdf/x.pdf"}],
    }
    doc.update(over)
    return doc


def spec(**over) -> dict:
    entry = {
        "subject": "WGX", "predicate": "aisc_aud_oz", "as_of": "2026-03-31",
        "value": 2931, "evidence_state": "POINT", "state": "ACCEPTED",
        "document_id": "sha256:" + "c" * 64,
        "locator": {"type": "pdf-location", "page": 1, "exact": True},
        "excerpt": "All in Sustaining Cost (AISC) of $2,931/oz",
        "decision": {"code": "PRIMARY_EVIDENCE_TIER_UPGRADE", "reason": "lodged original"},
    }
    entry.update(over)
    return entry


class RegisteredClaimRecordTest(unittest.TestCase):
    """§6.2 is the whole record, and a new claim does not get the legacy
    exceptions. Each refusal below is a hole the migration was allowed to carry
    and researched knowledge is not."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.docs = {"c" * 64: registered_document(self.dir)}
        patch = mock.patch.object(kb, "ROOT", self.dir)
        patch.start()
        self.addCleanup(patch.stop)

    def build(self, **over) -> dict:
        return kb.build_registered_claim(spec(**over), self.docs, kb.now())

    def refuses(self, message: str, **over) -> None:
        with self.assertRaises(kb.ClaimSpecError) as caught:
            self.build(**over)
        self.assertIn(message, str(caught.exception))

    def test_the_evidence_must_be_archived_first(self) -> None:
        self.refuses("is not in the store", document_id="sha256:" + "d" * 64)

    def test_an_active_claim_needs_an_exact_locator(self) -> None:
        self.refuses("exact page/table/note/section/image locator",
                     locator={"type": "document", "exact": False})

    def test_an_active_claim_needs_a_verbatim_excerpt(self) -> None:
        self.refuses("verbatim excerpt", excerpt="  ")

    def test_a_missing_amount_is_never_accepted_as_a_value(self) -> None:
        self.refuses("stays UNRESOLVED", value=None)

    def test_a_new_claim_does_not_get_the_legacy_as_of_exception(self) -> None:
        self.refuses("as_of must be an ISO date", as_of="2026-04")

    def test_the_tier_comes_from_the_artifact_not_the_spec(self) -> None:
        claim = self.build(authority_tier="T3", authority_domains=["issuer.announcement"])

        self.assertEqual(claim["authority_tier"], "T1")
        self.assertEqual(claim["authority_domains"], ["exchange.lodgement"])

    def test_a_publication_date_may_not_contradict_the_artifact(self) -> None:
        self.refuses("contradicts the artifact", publication_date="2026-04-30")

    def test_a_unit_that_is_not_the_field_unit_is_refused(self) -> None:
        self.refuses("is not the aisc_aud_oz unit",
                     scope={"entity_level": "issuer", "category": "all-in sustaining cost",
                            "unit": "USD/oz"})

    def test_an_aud_scope_must_state_its_currency(self) -> None:
        self.refuses("must state its currency",
                     predicate="undrawn_facilities_aud_m",
                     scope={"entity_level": "issuer", "category": "committed undrawn "
                            "facilities", "unit": "AUD million"})

    def test_a_derivation_names_its_formula_and_dependencies(self) -> None:
        self.refuses("ordered dependency claim id",
                     derivation={"formula": "a - b", "dependencies": []})

    def test_a_held_claim_says_why_it_is_held(self) -> None:
        self.refuses("must say why", held_from_projection=True)

    def test_a_held_claim_cannot_also_be_the_projection_basis(self) -> None:
        self.refuses("cannot also be the live projection basis",
                     held_from_projection=True,
                     decision={"code": "HELD_FOR_REVIEWED_REBALANCE", "reason": "rebalance"},
                     projection={"file": "data/companies.json", "path": "/c/0/f/x"})

    def test_a_held_claim_is_accepted_but_not_projectable(self) -> None:
        claim = self.build(held_from_projection=True,
                           decision={"code": "HELD_FOR_REVIEWED_REBALANCE",
                                     "reason": "adoption is a rebalance decision"})

        self.assertEqual(claim["state"], "ACCEPTED")
        self.assertFalse(claim["projectable"])

    def test_the_as_of_is_kept_apart_from_the_publication_date(self) -> None:
        claim = self.build()

        self.assertEqual(claim["claim_key"]["as_of"], "2026-03-31")
        self.assertEqual(claim["publication_date"], "2026-04-29")

    def test_a_verification_exception_needs_a_code_and_a_reason(self) -> None:
        self.refuses("a code and a reason", verification_exception={"code": "X"})

    def test_a_verification_exception_is_recorded_on_the_claim(self) -> None:
        claim = self.build(verification_exception={
            "code": "SELF_DESCRIBING_ARTIFACT", "reason": "explained in the audit"})

        self.assertEqual(claim["verification_exception"],
                         {"code": "SELF_DESCRIBING_ARTIFACT", "reason": "explained in the audit"})


class PrecedenceTest(unittest.TestCase):
    """§5.1 run for one normalized key. Authority is the barrier, not recency."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patch = mock.patch.object(kb, "ROOT", self.dir)
        patch.start()
        self.addCleanup(patch.stop)

    def claim(self, tier: str, value, state: str = "ACCEPTED") -> dict:
        docs = {"c" * 64: registered_document(self.dir, authority_tier=tier,
                                              authority_domains=["exchange.lodgement"])}
        return kb.build_registered_claim(spec(value=value, state=state), docs, kb.now())

    def test_a_lower_tier_candidate_cannot_replace_a_higher_tier_claim(self) -> None:
        held = self.claim("T1", 2931)
        candidate = self.claim("T3", 3100)

        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.check_precedence(candidate, [held], set())
        self.assertIn("quarantine pointer instead of a second value",
                      str(caught.exception))

    def test_an_incompatible_candidate_at_the_same_tier_leaves_it_unresolved(self) -> None:
        held = self.claim("T1", 2931)
        candidate = self.claim("T1", 3100)

        with self.assertRaises(kb.SameTierConflict) as caught:
            kb.check_precedence(candidate, [held], set())
        self.assertIn("requires an UNRESOLVED decision", str(caught.exception))
        self.assertEqual(caught.exception.conflicting_ids, [held["claim_id"]])

    def test_two_active_claims_for_one_key_are_refused(self) -> None:
        held = self.claim("T1", 2931)
        candidate = self.claim("T1", 2931)
        candidate["claim_id"] = "claim:sha256:" + "9" * 64

        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.check_precedence(candidate, [held], set())
        self.assertIn("already active for this key", str(caught.exception))

    def test_resolving_a_key_must_supersede_the_unresolved_record(self) -> None:
        held = self.claim("T1", 2931, state="UNRESOLVED")
        candidate = self.claim("T1", 2931)
        candidate["claim_id"] = "claim:sha256:" + "9" * 64

        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.check_precedence(candidate, [held], set())
        self.assertIn("holds this key UNRESOLVED", str(caught.exception))

    def test_an_explicit_supersession_of_a_lower_tier_claim_is_allowed(self) -> None:
        held = self.claim("T3", 2931)
        candidate = self.claim("T1", 2802)
        candidate["claim_id"] = "claim:sha256:" + "9" * 64

        kb.check_precedence(candidate, [held], {held["claim_id"]})

    def test_a_lower_tier_claim_may_not_supersede_an_incompatible_higher_one(self) -> None:
        held = self.claim("T1", 2931)
        candidate = self.claim("T3", 2802)
        candidate["claim_id"] = "claim:sha256:" + "9" * 64

        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.check_precedence(candidate, [held], {held["claim_id"]})
        self.assertIn("cannot supersede an incompatible", str(caught.exception))


class ValueConflictTest(unittest.TestCase):
    """Two values conflict only after rounding and published ranges (§5)."""

    @staticmethod
    def claim(value, span=None) -> dict:
        return {"value": {"type": "number", "value": value}, "reported_range": span}

    def test_a_published_range_containing_the_other_point_is_not_a_conflict(self) -> None:
        self.assertFalse(kb.values_conflict(self.claim(95, [90, 100]), self.claim(97)))

    def test_the_same_value_at_different_precision_is_not_a_conflict(self) -> None:
        self.assertFalse(kb.values_conflict(self.claim(2931), self.claim(2931.0)))
        self.assertFalse(kb.values_conflict(self.claim(600), self.claim(600.4)))

    def test_a_genuinely_different_amount_is_a_conflict(self) -> None:
        self.assertTrue(kb.values_conflict(self.claim(2931), self.claim(2802)))

    def test_silence_does_not_conflict_with_a_value(self) -> None:
        self.assertFalse(kb.values_conflict(
            {"value": {"type": "null", "value": None}}, self.claim(2931)))


class SupersessionTest(unittest.TestCase):
    """History is a link forward, never an edit in place (§2.9)."""

    def setUp(self) -> None:
        self.predecessor = {
            "claim_id": "claim:sha256:" + "1" * 64, "state": "PROVISIONAL",
            "projectable": True, "value": {"type": "number", "value": 2931},
            "evidence": {"document_id": "sha256:" + "e" * 64},
            "projection": {"file": "data/companies.json", "path": "/c/0/f/x"}}
        self.successor = {
            "claim_id": "claim:sha256:" + "2" * 64,
            "projection": {"file": "data/companies.json", "path": "/c/0/f/x"}}

    def test_the_predecessor_keeps_its_value_and_evidence(self) -> None:
        kb.apply_supersession(self.predecessor, self.successor, kb.now(), "upgraded")

        self.assertEqual(self.predecessor["value"]["value"], 2931)
        self.assertEqual(self.predecessor["evidence"]["document_id"], "sha256:" + "e" * 64)
        self.assertEqual(self.predecessor["state"], "SUPERSEDED")
        self.assertEqual(self.predecessor["superseded_by"], self.successor["claim_id"])
        self.assertFalse(self.predecessor["projectable"])

    def test_only_one_record_remains_the_projection_basis(self) -> None:
        kb.apply_supersession(self.predecessor, self.successor, kb.now(), "upgraded")

        self.assertNotIn("projection", self.predecessor)
        self.assertEqual(self.predecessor["projection_history"][0]["path"], "/c/0/f/x")

    def test_a_successor_that_does_not_project_leaves_the_basis_alone(self) -> None:
        kb.apply_supersession(self.predecessor, {"claim_id": "claim:sha256:" + "2" * 64},
                              kb.now(), "newer observation, held")

        self.assertEqual(self.predecessor["projection"]["path"], "/c/0/f/x")

    def test_an_unrelated_claim_cannot_be_superseded(self) -> None:
        self.predecessor["claim_key"] = {"subject": "NST", "predicate": "pp_moz"}
        self.successor["claim_key"] = {"subject": "WGX", "predicate": "aisc_aud_oz"}

        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.validate_supersession_relation(self.successor, self.predecessor)

        self.assertIn("cannot supersede unrelated", str(caught.exception))

    def test_projection_paths_must_match(self) -> None:
        self.predecessor["claim_key"] = {"subject": "WGX", "predicate": "aisc_aud_oz"}
        self.successor["claim_key"] = {"subject": "WGX", "predicate": "aisc_aud_oz"}
        self.successor["projection"]["path"] = "/c/1/f/y"

        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.validate_supersession_relation(self.successor, self.predecessor)

        self.assertIn("does not match", str(caught.exception))


class RegisteredQuarantineTest(unittest.TestCase):
    """A quarantine record is a pointer and a reason, never a second value."""

    def setUp(self) -> None:
        self.active = {"claim_id": "claim:sha256:" + "1" * 64, "state": "ACCEPTED"}
        self.unresolved = {"claim_id": "claim:sha256:" + "2" * 64, "state": "UNRESOLVED"}
        self.by_id = {c["claim_id"]: c for c in (self.active, self.unresolved)}

    def test_a_candidate_carrying_a_value_is_refused(self) -> None:
        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.build_registered_quarantine(
                {"candidate": {"pointer": "/x", "value": 145}, "reason_code": "X",
                 "reason": "y", "related_claim": self.unresolved["claim_id"]}, self.by_id)
        self.assertIn("never a second", str(caught.exception))

    def test_blocked_by_must_name_a_controlling_active_claim(self) -> None:
        with self.assertRaises(kb.ClaimSpecError) as caught:
            kb.build_registered_quarantine(
                {"candidate": {"pointer": "/x"}, "reason_code": "X", "reason": "y",
                 "blocked_by": self.unresolved["claim_id"]}, self.by_id)
        self.assertIn("controlling ACTIVE claim", str(caught.exception))

    def test_a_pointer_to_an_unresolved_claim_is_a_related_claim(self) -> None:
        record = kb.build_registered_quarantine(
            {"candidate": {"pointer": "/x", "document_id": "sha256:" + "c" * 64},
             "reason_code": "SCOPING_STUDY_ESTIMATE_NOT_APPROVED_SCOPE",
             "reason": "pre-FID", "related_claim": self.unresolved["claim_id"]},
            self.by_id)

        self.assertEqual(record["related_claim"], self.unresolved["claim_id"])
        for forbidden in ("value", "reported_value", "range"):
            self.assertNotIn(forbidden, record)


class DerivationAuditTest(unittest.TestCase):
    """`build_registered_claim` refuses a derivation missing either half at
    registration time; the audit checked dependencies but not formula, so a
    claim written by any other path (or hand-assembled) could carry
    dependencies with no formula and pass unnoticed."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for name in ("claims", "quarantine"):
            patch = mock.patch.object(kb, name.upper(), self.dir / f"{name}.jsonl")
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def claim(derivation: dict) -> dict:
        return {"claim_id": "claim:sha256:" + "6" * 64,
                "claim_key": {"subject": "EMR", "predicate": "production_actual_koz",
                              "scope": {"unit": "koz"}, "as_of": "2026-06-30"},
                "value": {"type": "number", "value": 100.406},
                "evidence": {"locator": {"exact": True}},
                "state": "ACCEPTED", "projectable": True, "derivation": derivation}

    def test_a_derivation_with_no_formula_is_an_error(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim({"dependencies": ["claim:sha256:" + "1" * 64]})])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane({})

        self.assertTrue(any("derivation has no formula" in e for e in errors), errors)

    def test_a_derivation_with_both_is_fine(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim({"formula": "sum(q1..q4)",
                                               "dependencies": ["claim:sha256:" + "1" * 64]})])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane({})

        self.assertFalse([e for e in errors if "derivation has no" in e], errors)


class ProjectionBasisAuditTest(unittest.TestCase):
    """One field, one projection basis. Two records claiming it is the silent
    choice the version-history correction exists to prevent."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for name in ("claims", "quarantine"):
            patch = mock.patch.object(kb, name.upper(), self.dir / f"{name}.jsonl")
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def claim(cid: str) -> dict:
        return {"claim_id": "claim:sha256:" + cid * 64,
                "claim_key": {"subject": "WGX", "predicate": "aisc_aud_oz",
                              "scope": {"unit": "AUD/oz"}, "as_of": "2026-03-31"},
                "value": {"type": "number", "value": 2931},
                "evidence": {"locator": {"exact": True}},
                "state": "SUPERSEDED", "projectable": False,
                "projection": {"file": "data/companies.json", "path": "/c/0/f/x"}}

    def test_two_records_claiming_one_field_is_an_error(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim("1"), self.claim("2")])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane({})

        self.assertTrue(any("both record themselves as the projection basis" in e
                            for e in errors), errors)

    def test_one_record_claiming_one_field_is_fine(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim("1")])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane({})

        self.assertFalse([e for e in errors if "projection basis" in e], errors)

    def test_a_persisted_supersession_cannot_cross_projection_paths(self) -> None:
        predecessor = self.claim("1")
        successor = self.claim("2")
        predecessor.update(
            state="SUPERSEDED", superseded_by=successor["claim_id"],
            projection_history=[predecessor.pop("projection")])
        successor.update(
            state="ACCEPTED", projectable=True,
            supersedes=[predecessor["claim_id"]],
            projection={"file": "data/companies.json", "path": "/c/9/f/y"})
        kb.write_jsonl(kb.CLAIMS, [predecessor, successor])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane({})

        self.assertTrue(any("supersession projection path" in e for e in errors), errors)


class UnverifiedEvidenceAuditTest(unittest.TestCase):
    """24 August 2026 remediation: a registered (not backfilled) active claim
    must cite evidence with a verified issuer and publication date — the study
    that motivated this rule accepted 22 such claims without either check.
    `verification_exception` is a recorded, reviewed bypass; it still warns."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for name in ("claims", "quarantine"):
            patch = mock.patch.object(kb, name.upper(), self.dir / f"{name}.jsonl")
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def claim(**overrides) -> dict:
        base = {"claim_id": "claim:sha256:" + "7" * 64,
                "claim_key": {"subject": "AEM", "predicate": "aisc_actual",
                              "scope": {"unit": "USD/oz"}, "as_of": "2023-02-23"},
                "value": {"type": "number", "value": 1030},
                "evidence": {"document_id": "sha256:" + "b" * 64,
                             "locator": {"exact": True}},
                "authority_tier": "T1", "authority_domains": ["regulator.lodgement"],
                "state": "ACCEPTED", "projectable": True,
                "decision": {"producing_tool": kb.REGISTER_TOOL}}
        base.update(overrides)
        return base

    @staticmethod
    def docs(**verified) -> dict:
        v = {"issuer": True, "title": True, "dates": True, "bytes": True}
        v.update(verified)
        return {"b" * 64: {"authority_tier": "T1", "authority_domains": ["regulator.lodgement"],
                           "verified": v}}

    def test_a_registered_claim_with_unverified_issuer_is_refused(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim()])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane(self.docs(issuer=False))

        self.assertTrue(any("unverified issuer" in e for e in errors), errors)

    def test_a_registered_claim_with_verified_evidence_is_fine(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim()])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane(self.docs())

        self.assertFalse([e for e in errors if "unverified" in e], errors)

    def test_a_backfilled_claim_is_not_subject_to_the_new_rule(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim(
            decision={"producing_tool": "tools/kb.py backfill-claims"})])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane(self.docs(issuer=False, dates=False))

        self.assertFalse([e for e in errors if "unverified" in e], errors)

    def test_an_explicit_exception_downgrades_the_refusal_to_a_warning(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim(verification_exception={
            "code": "SELF_DESCRIBING_ARTIFACT", "reason": "test override"})])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, warnings = kb.audit_claim_plane(self.docs(issuer=False))

        self.assertFalse([e for e in errors if "unverified" in e], errors)
        self.assertTrue(any("permitted by exception" in w for w in warnings), warnings)


class TierConsistencyAuditTest(unittest.TestCase):
    """24 August 2026 remediation: a superseded claim's authority_tier is a
    frozen snapshot of what its evidence was believed to be when the claim was
    made. It can never be redirected to track a later correction to that
    document's tier — the same immutability rule that refuses to redirect an
    already-superseded claim's supersession (`validate_supersession_relation`).
    Only an active claim must still match its artifact today."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for name in ("claims", "quarantine"):
            patch = mock.patch.object(kb, name.upper(), self.dir / f"{name}.jsonl")
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def claim(state: str) -> dict:
        return {"claim_id": "claim:sha256:" + "9" * 64,
                "claim_key": {"subject": "NEM", "predicate": "aisc_guidance",
                              "scope": {"unit": "USD/oz"}, "as_of": "2021-12-02"},
                "value": {"type": "number", "value": 1030},
                "evidence": {"document_id": "sha256:" + "a" * 64,
                             "locator": {"exact": True}},
                "authority_tier": "T2", "authority_domains": ["issuer.release"],
                "state": state, "projectable": state in kb.ACTIVE_CLAIM_STATES}

    @staticmethod
    def docs() -> dict:
        # The document was reclassified from T2 to T4 by a later host-authority
        # fix, after this claim was already registered against it.
        return {"a" * 64: {"authority_tier": "T4", "authority_domains": ["unclassified"]}}

    def test_an_active_claim_must_match_its_artifacts_current_tier(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim("ACCEPTED")])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane(self.docs())

        self.assertTrue(any("authority tier does not match" in e for e in errors), errors)

    def test_a_superseded_claim_is_not_forced_to_track_a_later_tier_correction(self) -> None:
        kb.write_jsonl(kb.CLAIMS, [self.claim("SUPERSEDED")])
        kb.write_jsonl(kb.QUARANTINE, [])

        errors, _ = kb.audit_claim_plane(self.docs())

        self.assertFalse([e for e in errors if "authority tier does not match" in e], errors)


class RegisterCommandTest(unittest.TestCase):
    """The command is atomic: a spec that breaks one rule writes nothing."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        for attr, name in (("CLAIMS", "claims.jsonl"), ("QUARANTINE", "quarantine.jsonl")):
            patch = mock.patch.object(kb, attr, self.dir / name)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.object(kb, "ROOT", self.dir)
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.object(kb, "load_documents",
                                  return_value={"c" * 64: registered_document(self.dir)})
        patch.start()
        self.addCleanup(patch.stop)
        kb.write_jsonl(kb.CLAIMS, [])
        kb.write_jsonl(kb.QUARANTINE, [])

    def run_register(self, payload: dict, dry_run: bool = False) -> int:
        path = self.dir / "spec.json"
        path.write_text(json.dumps(payload))
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            return kb.cmd_register_claim(
                argparse.Namespace(file=str(path), dry_run=dry_run))

    def test_a_valid_spec_is_written_once_and_is_idempotent(self) -> None:
        self.assertEqual(self.run_register({"claims": [spec()]}), 0)
        self.assertEqual(len(kb.read_jsonl(kb.CLAIMS)), 1)

        self.assertEqual(self.run_register({"claims": [spec()]}), 0)
        self.assertEqual(len(kb.read_jsonl(kb.CLAIMS)), 1)

    def test_a_dry_run_writes_nothing(self) -> None:
        self.assertEqual(self.run_register({"claims": [spec()]}, dry_run=True), 0)

        self.assertEqual(kb.read_jsonl(kb.CLAIMS), [])

    def test_one_bad_entry_rejects_the_whole_spec(self) -> None:
        code = self.run_register({"claims": [spec(), spec(value=None, as_of="2026-06-30")]})

        self.assertEqual(code, 1)
        self.assertEqual(kb.read_jsonl(kb.CLAIMS), [])

    def test_superseding_an_unknown_claim_is_refused(self) -> None:
        code = self.run_register(
            {"claims": [spec(supersedes=["claim:sha256:" + "f" * 64])]})

        self.assertEqual(code, 1)
        self.assertEqual(kb.read_jsonl(kb.CLAIMS), [])

    def test_same_tier_conflict_retires_projection_and_records_unresolved(self) -> None:
        docs = kb.load_documents()
        incumbent = kb.build_registered_claim(
            spec(projection={"file": "data/companies.json", "path": "/c/0/f/x"}),
            docs, kb.now())
        kb.write_jsonl(kb.CLAIMS, [incumbent])

        code = self.run_register({"claims": [spec(
            value=3100, excerpt="All in Sustaining Cost of $3,100/oz",
            projection={"file": "data/companies.json", "path": "/c/0/f/x"})]})

        self.assertEqual(code, 0)
        claims = kb.read_jsonl(kb.CLAIMS)
        old = next(c for c in claims if c["claim_id"] == incumbent["claim_id"])
        decision = next(c for c in claims
                        if c.get("decision", {}).get("code") == "CONTROLLING_TIER_CONFLICT")
        self.assertEqual(old["state"], "SUPERSEDED")
        self.assertNotIn("projection", old)
        self.assertEqual(decision["state"], "UNRESOLVED")
        self.assertIsNone(decision["value"]["value"])
        self.assertFalse(decision["projectable"])
        self.assertEqual(len(decision["conflicts"]), 2)

    def test_same_tier_conflict_registration_is_idempotent(self) -> None:
        docs = kb.load_documents()
        incumbent = kb.build_registered_claim(spec(), docs, kb.now())
        kb.write_jsonl(kb.CLAIMS, [incumbent])
        payload = {"claims": [spec(value=3100,
                                   excerpt="All in Sustaining Cost of $3,100/oz")]}

        self.assertEqual(self.run_register(payload), 0)
        first = kb.CLAIMS.read_bytes()
        self.assertEqual(self.run_register(payload), 0)
        self.assertEqual(kb.CLAIMS.read_bytes(), first)

    def test_superseding_an_unrelated_claim_is_refused(self) -> None:
        docs = kb.load_documents()
        unrelated = kb.build_registered_claim(
            spec(subject="NST", predicate="pp_moz", value=28.4,
                 scope={"entity_level": "issuer", "category": "reserves", "unit": "Moz"}),
            docs, kb.now())
        kb.write_jsonl(kb.CLAIMS, [unrelated])

        code = self.run_register(
            {"claims": [spec(supersedes=[unrelated["claim_id"]])]})

        self.assertEqual(code, 1)
        self.assertEqual(kb.read_jsonl(kb.CLAIMS), [unrelated])

    def test_existing_claim_identity_cannot_be_overwritten(self) -> None:
        self.assertEqual(self.run_register({"claims": [spec()]}), 0)
        before = kb.CLAIMS.read_bytes()

        changed = spec(decision={"code": "PRIMARY_EVIDENCE_TIER_UPGRADE",
                                 "reason": "silently changed decision"})
        self.assertEqual(self.run_register({"claims": [changed]}), 1)
        self.assertEqual(kb.CLAIMS.read_bytes(), before)

    def test_an_explicit_same_tier_correction_can_supersede(self) -> None:
        docs = kb.load_documents()
        incumbent = kb.build_registered_claim(spec(), docs, kb.now())
        kb.write_jsonl(kb.CLAIMS, [incumbent])
        corrected = spec(
            value=3100, excerpt="Corrected AISC of $3,100/oz",
            supersedes=[incumbent["claim_id"]],
            supersession_basis="EXPLICIT_CORRECTION")

        self.assertEqual(self.run_register({"claims": [corrected]}), 0)
        claims = kb.read_jsonl(kb.CLAIMS)
        self.assertEqual(len(claims), 2)
        self.assertEqual(next(c for c in claims if c["state"] == "ACCEPTED")
                         ["value"]["value"], 3100)
        self.assertEqual(next(c for c in claims if c["state"] == "SUPERSEDED")
                         ["superseded_by"],
                         next(c for c in claims if c["state"] == "ACCEPTED")["claim_id"])


if __name__ == "__main__":
    unittest.main()
