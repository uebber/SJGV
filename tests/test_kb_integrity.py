"""Evidence-plane rules that the strict audit has to enforce.

Each test states a defect an acceptance review found in the store and checks
that the tooling now refuses it: a T1 tier resting on a filename, an index
claiming coverage of days that have not happened, one URL or exchange
identifier resolving to several artifacts with nothing recorded about their
relation, and analysis sitting in a title field.

The second review added four more, and they are the classes at the end of this
file: a market session demoted out of its own authority by the reverify that
was supposed to preserve it, a local file classified from an inferred ticker
rather than a tested route, short analytical suffixes surviving in titles, and
a booked retry date that nothing honoured.
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


def document(**overrides) -> dict:
    doc = {
        "document_id": "sha256:" + "a" * 64,
        "sha256": "a" * 64,
        "bytes": 1024,
        "mime_type": "application/pdf",
        "title": "Quarterly Activities Report",
        "authority_tier": "T2",
        "authority_domains": ["issuer.announcement"],
        "tier_basis": "issuer-host:example.com",
        "source_ids": [],
        "url_aliases": [],
        "object_locator": "knowledge/objects/sha256/aa/" + "a" * 64,
        "storage_state": "local",
        "verified": {"issuer": False, "title": False, "dates": False, "bytes": True},
        "subjects": ["NST"],
        "acquisition": [],
        "review": [],
    }
    doc.update(overrides)
    return doc


class UnsupportedPromotionTest(unittest.TestCase):
    """A tier is a claim about origin. It needs a basis outside our own naming."""

    def test_filename_derived_identifier_does_not_reach_t1(self) -> None:
        doc = document(
            authority_tier="T1", tier_basis="asx_document_key:local-filename",
            source_ids=[kb.source_id("asx_document_key", "2924-03123136-6A1339303",
                                     "local-filename", False)])

        self.assertIsNotNone(kb.audit_promotion(doc))

    def test_identifier_from_the_retrieval_url_does_reach_t1(self) -> None:
        doc = document(
            authority_tier="T1", tier_basis="asx_document_key:retrieval-url",
            source_ids=[kb.source_id("asx_document_key", "2924-03123136-6A1339303",
                                     "retrieval-url", True)])

        self.assertIsNone(kb.audit_promotion(doc))

    def test_an_alias_on_an_exchange_host_supports_t1_once_it_was_fetched(self) -> None:
        url = "https://announcements.asx.com.au/asxpdf/20260820/pdf/06abc.pdf"
        doc = document(authority_tier="T1", tier_basis="host-rule",
                       url_aliases=[{"url": url}])

        # The address alone proves nothing: it is where the bytes are SAID to
        # have come from. What supports the tier is having gone and got them.
        self.assertIn("no retrieval event", kb.audit_promotion(doc))

        doc["acquisition"] = [{"at": "2026-08-23T11:00:00+00:00", "url": url,
                               "via": "kb.acquire — initial KB load"}]
        self.assertIsNone(kb.audit_promotion(doc))

    def test_an_exchange_alias_built_from_a_filename_does_not_support_t1(self) -> None:
        url = kb.ASX_CDN + "2924-03123136-6A1339303"
        doc = document(authority_tier="T1", tier_basis="host-rule",
                       url_aliases=[{"url": url}],
                       acquisition=[{"at": "2026-08-23T11:41:55+00:00", "url": url,
                                     "via": "local /tmp artifact from the 21-22 Aug 2026 "
                                            "sourcing pass"}])

        self.assertIn("no retrieval event", kb.audit_promotion(doc))

    def test_checked_equivalence_with_a_verified_artifact_supports_t1(self) -> None:
        doc = document(
            authority_tier="T1", tier_basis="equivalence-with-verified-artifact",
            equivalence={"group": "asx_document_key:2924-1-6A1", "equivalent": True,
                         "inherits_tier": "T1", "verified_member": "sha256:" + "b" * 64,
                         "basis": "identical extracted text"})

        self.assertIsNone(kb.audit_promotion(doc))

    def test_tier_assignment_refuses_to_promote_on_an_inferred_identifier(self) -> None:
        doc = document(
            source_ids=[kb.source_id("asx_document_key", "2924-1-6A1",
                                     "local-filename", False)])

        kb.assign_tier(doc)

        self.assertEqual(doc["authority_tier"], "T4")
        self.assertEqual(doc["tier_basis"], "local-artifact-no-route")


class CoverageTest(unittest.TestCase):
    """An index sweep is evidence over the interval it was swept, and no more."""

    def test_current_year_sweep_covers_only_the_year_to_date(self) -> None:
        cover = kb.index_coverage("NST", 2026, "2026-08-23T11:52:00+00:00", 92)

        self.assertEqual(cover["covered_from"], "2026-01-01")
        self.assertEqual(cover["covered_to"], "2026-08-23")
        self.assertFalse(cover["complete"])
        self.assertIn("year to date", cover["completeness"])
        self.assertNotIn("full calendar year", cover["completeness"])

    def test_closed_year_sweep_covers_the_whole_year(self) -> None:
        cover = kb.index_coverage("NST", 2025, "2026-08-23T11:52:00+00:00", 140)

        self.assertEqual(cover["covered_to"], "2025-12-31")
        self.assertTrue(cover["complete"])
        self.assertIn("full calendar year", cover["completeness"])

    def test_audit_rejects_coverage_running_past_the_retrieval(self) -> None:
        doc = document(reporting_dates=["2026-01-01", "2026-12-31"],
                       coverage={"covered_from": "2026-01-01", "covered_to": "2026-12-31",
                                 "complete": True,
                                 "retrieved_at": "2026-08-23T11:52:00+00:00"})

        problems = kb.audit_coverage(doc, "2026-08-23")

        self.assertTrue(any("in the future" in p for p in problems))
        self.assertTrue(any("retrieved on 2026-08-23" in p for p in problems))

    def test_audit_accepts_a_correctly_stated_partial_year(self) -> None:
        doc = document(reporting_dates=["2026-01-01", "2026-08-23"],
                       coverage=kb.index_coverage("NST", 2026,
                                                  "2026-08-23T11:52:00+00:00", 92))

        self.assertEqual(kb.audit_coverage(doc, "2026-08-23"), [])


class AmbiguityTest(unittest.TestCase):
    """Several artifacts under one key is normal. Not saying how they relate is not."""

    def make_pair(self, **extra) -> dict:
        url = "https://cdn-api.markitdigital.com/apiman-gateway/ASX/x/file/2924-1-6A1"
        first = document(
            document_id="sha256:" + "a" * 64, sha256="a" * 64,
            url_aliases=[{"url": url, "first_seen": "2026-08-23T11:41:50+00:00"}])
        second = document(
            document_id="sha256:" + "b" * 64, sha256="b" * 64,
            url_aliases=[{"url": url, "first_seen": "2026-08-23T11:41:55+00:00"}],
            **extra)
        return {"a" * 64: first, "b" * 64: second}

    def test_one_url_two_artifacts_without_a_recorded_relation_fails(self) -> None:
        problems = kb.audit_ambiguity(self.make_pair())

        self.assertEqual(len(problems), 1)
        self.assertIn("no recorded version relation", problems[0])

    def test_recorded_equivalence_settles_it(self) -> None:
        docs = self.make_pair()
        kb.link_equivalents(docs)

        # Neither artifact has extractions on disk here, so equivalence cannot be
        # established — but it is recorded as an open question, not left silent.
        for doc in docs.values():
            self.assertEqual(doc["equivalence"]["group"],
                             "url:https://cdn-api.markitdigital.com/apiman-gateway/"
                             "ASX/x/file/2924-1-6A1")
        self.assertEqual(kb.audit_ambiguity(docs), [])

    def test_versions_are_ordered_by_retrieval_not_by_hash(self) -> None:
        docs = self.make_pair()
        groups = kb.publication_groups(docs)
        members = groups["url:https://cdn-api.markitdigital.com/apiman-gateway/"
                         "ASX/x/file/2924-1-6A1"]

        self.assertEqual([m["sha256"][:1] for m in members], ["a", "b"])

    def test_overlapping_url_and_identifier_groups_are_one_publication(self) -> None:
        # The .cache copy and the fetched copy share the URL; the /tmp copy
        # shares only the documentKey. All three are versions of one thing.
        docs = self.make_pair()
        for doc in docs.values():
            doc["source_ids"] = [kb.source_id("asx_document_key", "2924-1-6A1",
                                              "retrieval-url", True)]
        docs["c" * 64] = document(
            document_id="sha256:" + "c" * 64, sha256="c" * 64, url_aliases=[],
            acquisition=[{"at": "2026-08-23T11:41:52+00:00", "via": "local /tmp artifact"}],
            source_ids=[kb.source_id("asx_document_key", "2924-1-6A1",
                                     "local-filename", False)])

        clusters = kb.publication_clusters(docs)

        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]["members"]), 3)
        self.assertEqual(clusters[0]["primary"], "asx_document_key:2924-1-6A1")
        kb.link_equivalents(docs)
        self.assertEqual(kb.audit_ambiguity(docs), [])

    def test_two_documents_under_one_exchange_identifier_fails(self) -> None:
        docs = self.make_pair()
        for doc in docs.values():
            doc["source_ids"] = [kb.source_id("asx_document_key", "2924-1-6A1",
                                              "retrieval-url", True)]
            doc["url_aliases"] = []
            doc["equivalence"] = {"group": "asx_document_key:2924-1-6A1",
                                  "keys": ["asx_document_key:2924-1-6A1"],
                                  "equivalent": False, "basis": "extracted text differs"}

        problems = kb.audit_ambiguity(docs)

        self.assertTrue(any("cannot name two documents" in p for p in problems))


class TitleTest(unittest.TestCase):
    """Titles are publisher metadata; a reading of the document is not."""

    def test_narrative_note_is_not_a_title(self) -> None:
        note = ("THE BLOCKING QUESTION IS ANSWERED. Queensland does run gold on a "
                "price-linked sliding scale, but the escalator is CAPPED at 5% and has "
                "been saturated for two decades.")

        title, analysis = kb.publisher_title(note)

        self.assertIsNone(title)
        self.assertEqual(analysis, note)

    def test_headline_is_split_from_its_gloss(self) -> None:
        title, analysis = kb.publisher_title(
            "FY26 result and FY27 guidance (29 Jul 2026) — Havieron FID APPROVED June "
            "2026; A$1.065bn pre-production capital to first gold in FY29.")

        self.assertEqual(title, "FY26 result and FY27 guidance (29 Jul 2026)")
        self.assertIn("A$1.065bn", analysis)

    def test_a_publisher_headline_survives_intact(self) -> None:
        for headline in ("1.1Moz Maiden Fletcher Ore Reserve",
                         "Quarterly Activities & Cashflow Report",
                         "Resource & Reserve Update Round Dam and Waihi - Correction"):
            with self.subTest(headline=headline):
                self.assertEqual(kb.publisher_title(headline), (headline, None))

    def test_audit_rejects_analysis_in_the_title_field(self) -> None:
        self.assertIsNotNone(kb.audit_title(document(title="x " * 150)))
        self.assertIsNotNone(kb.audit_title(document(
            title="Appendix 4E. It confirms the facility is undrawn.")))
        self.assertIsNone(kb.audit_title(document(title="Appendix 4E - 30 June 2026")))

    def test_opaque_url_segments_do_not_become_titles(self) -> None:
        self.assertIsNone(kb.url_filename_title("https://x.com/9bbcfd5b-c55.pdf"))
        self.assertEqual(
            kb.url_filename_title("https://www.mrt.tas.gov.au/APPROVED-Fees-under-the-"
                                  "Mineral-Resources-Regulations-2026.pdf"),
            "APPROVED-Fees-under-the-Mineral-Resources-Regulations-2026")


class InferredProvenanceTest(unittest.TestCase):
    """A filename is a lead about where bytes came from, never the evidence."""

    def test_a_documentkey_filename_yields_no_url_alias(self) -> None:
        subjects, note, inferred = kb.tmp_provenance(
            Path("/tmp/nst-2924-03123136-6A1339303.pdf"))

        self.assertEqual(subjects, ["NST"])
        self.assertIn("inferred, not verified", note)
        self.assertEqual(inferred["state"], "unverified")
        self.assertFalse(inferred["source_ids"][0]["verified"])
        self.assertTrue(inferred["candidate_urls"][0]["url"].startswith(kb.ASX_CDN))

    def test_evidence_upgrades_an_inferred_identifier_in_place(self) -> None:
        doc = document(source_ids=[])
        kb.add_source_id(doc, kb.source_id("asx_document_key", "2924-1-6A1",
                                           "local-filename", False))
        kb.add_source_id(doc, kb.source_id("asx_document_key", "2924-1-6A1",
                                           "retrieval-url", True))

        self.assertEqual(len(doc["source_ids"]), 1)
        self.assertTrue(doc["source_ids"][0]["verified"])
        self.assertEqual(doc["source_ids"][0]["previously_inferred_from"], "local-filename")


class MarketSessionAuthorityTest(unittest.TestCase):
    """An approved provider's own observation keeps its authority through every
    recomputation. The session cannot be re-fetched, so nothing else can restore
    it — a demotion here is permanent."""

    def bundle(self, **extra) -> dict:
        doc = document(
            document_id="sha256:" + "c" * 64, sha256="c" * 64, mime_type="application/json",
            title=None, title_source=None, publisher=None,
            authority_tier="T4", authority_domains=["unclassified"],
            subjects=["NST", "EVN", "CMM"], refetchable=False,
            observation_as_of="2026-08-23T13:18:59.203306+00:00",
            market_session={
                "provider": "ibkr-tws", "role": "session bundle",
                "session_start": "2026-08-23T13:18:59.203306+00:00",
                "title": "IBKR TWS market session 2026-08-23T13:18:59Z",
                "verification_basis": "self-describing session record"})
        doc.update(extra)
        return doc

    def test_the_bundle_stays_t1_however_often_the_tier_is_recomputed(self) -> None:
        doc = self.bundle()

        for _ in range(3):
            kb.assign_tier(doc)

        self.assertEqual(doc["authority_tier"], "T1")
        self.assertEqual(doc["authority_domains"], ["market.observation"])
        self.assertEqual(doc["tier_basis"], kb.MARKET_PROVIDER_BASIS)
        self.assertIn("Interactive Brokers", doc["publisher"])

    def test_the_bar_series_stays_t1_too(self) -> None:
        # The bars are a separate artifact and were demoted with the bundle: the
        # tickers they quote were read as their publisher.
        bars = self.bundle(
            document_id="sha256:" + "d" * 64, sha256="d" * 64, mime_type="text/csv",
            part_of="sha256:" + "c" * 64,
            market_session={"provider": "ibkr-tws", "role": "bar series",
                            "session_start": "2026-08-23T13:18:59.203306+00:00",
                            "title": "IBKR TWS daily/intraday bars 2026-08-23",
                            "verification_basis": "digest recorded in the session bundle"})

        for _ in range(3):
            kb.assign_tier(bars)

        self.assertEqual(bars["authority_tier"], "T1")
        self.assertEqual(bars["authority_domains"], ["market.observation"])
        self.assertNotIn("issuer.NST", bars["authority_domains"])

    def test_a_ticker_it_quotes_never_becomes_its_publisher(self) -> None:
        doc = self.bundle()
        kb.assign_tier(doc)

        self.assertNotEqual(doc["publisher"], "NST")
        self.assertEqual(doc["authority_domains"], ["market.observation"])

    def test_title_and_verification_survive_the_reverify_passes(self) -> None:
        doc = self.bundle(title="IBKR TWS market session 2026-08-23T13:18:59Z — 17 tickers, "
                                "prices and bars as observed",
                          title_source="carried from ingest")

        for _ in range(2):
            kb.apply_market_session(doc)

        # The analytical tail the first load put in the title is gone, and the
        # title is the one the session record states.
        self.assertEqual(doc["title"], "IBKR TWS market session 2026-08-23T13:18:59Z")
        self.assertEqual(doc["title_source"], "market session record")
        self.assertTrue(all(doc["verified"].values()))
        self.assertIsNone(kb.audit_title(doc))
        self.assertIsNone(kb.audit_promotion(doc))

    def test_a_session_archived_before_the_block_existed_is_repaired(self) -> None:
        legacy = document(
            document_id="sha256:" + "e" * 64, sha256="e" * 64,
            authority_tier="T2", authority_domains=["issuer.NST"],
            tier_basis="local-artifact-no-route", publisher="NST",
            observation_as_of="2026-08-23T13:18:59.203306+00:00",
            source_ids=[kb.source_id("engine_commit", "287eb60", "session-record", True)],
            acquisition=[{"at": "2026-08-23T13:22:02+00:00",
                          "via": "IBKR/TWS market session — TWS session 2026-08-23 → ..."}])
        docs = {"e" * 64: legacy}

        self.assertEqual(kb.repair_market_sessions(docs), 1)

        self.assertEqual(legacy["authority_tier"], "T1")
        self.assertEqual(legacy["market_session"]["role"], "session bundle")
        self.assertEqual(legacy["market_session"]["engine_commit"], "287eb60")

    def test_the_tier_basis_string_alone_does_not_buy_t1(self) -> None:
        # Authority comes from the provider registry, not from a record that
        # names itself. Otherwise the audit only checks our own spelling.
        doc = document(authority_tier="T1", tier_basis=kb.MARKET_PROVIDER_BASIS)

        self.assertIsNotNone(kb.audit_promotion(doc))


class LocalArtifactRouteTest(unittest.TestCase):
    """A file on disk is not a document until something says where it came from."""

    def test_an_inferred_ticker_does_not_buy_the_issuer_tier(self) -> None:
        doc = document(subjects=["WGX"], subject_basis="inferred from the document text",
                       url_aliases=[], authority_tier="T2")

        kb.assign_tier(doc)

        self.assertEqual(doc["authority_tier"], "T4")
        self.assertEqual(doc["authority_domains"], ["unclassified"])
        self.assertIsNone(doc["publisher"])
        self.assertIn("retrieval-route-untested", kb.review_flags(doc))

    def test_a_previously_inferred_publisher_is_withdrawn(self) -> None:
        # The discarded rule wrote the ticker into `publisher`. Recomputing the
        # tier has to take it back, or the unsupported claim simply persists.
        doc = document(subjects=["WGX"], publisher="WGX", url_aliases=[])

        kb.assign_tier(doc)

        self.assertIsNone(doc["publisher"])

    def test_a_tested_route_to_the_lodged_artifact_earns_the_lodged_tier(self) -> None:
        doc = document(
            subjects=["NST"], url_aliases=[],
            source_ids=[{"scheme": "asx_ids_id", "value": "03127196",
                         "basis": kb.INDEX_ROUTE_BASIS, "verified": False}],
            retrieval_route={"channel": "asx_announcement_index",
                             "state": "equivalent-regeneration", "ids_id": "03127196",
                             "pdf_url": "https://announcements.asx.com.au/asxpdf/x.pdf",
                             "equivalent_artifact": "sha256:" + "f" * 64},
            equivalence={"group": "asx_ids_id:03127196", "equivalent": True,
                         "inherits_tier": "T1", "verified_member": "sha256:" + "f" * 64,
                         "basis": "identical text page for page"})

        kb.assign_tier(doc)

        self.assertEqual(doc["authority_tier"], "T1")
        self.assertEqual(doc["tier_basis"], "equivalence-with-verified-artifact")
        self.assertIsNone(kb.audit_promotion(doc))
        self.assertNotIn("retrieval-route-untested", kb.review_flags(doc))

    def test_the_index_route_identifier_is_never_marked_verified(self) -> None:
        # The exchange served the OTHER artifact. The identifier names the
        # publication; it is not evidence about these bytes.
        doc = document(
            url_aliases=[],
            source_ids=[{"scheme": "asx_ids_id", "value": "03127196",
                         "basis": kb.INDEX_ROUTE_BASIS, "verified": False}],
            retrieval_route={"state": "equivalent-regeneration", "ids_id": "03127196",
                             "equivalent_artifact": "sha256:" + "f" * 64})

        kb.normalize_source_ids(doc)

        self.assertFalse(doc["source_ids"][0]["verified"])
        self.assertEqual(doc["source_ids"][0]["basis"], kb.INDEX_ROUTE_BASIS)
        self.assertIn("equivalence with", doc["source_ids"][0]["resolved_by"])
        self.assertIsNone(kb.verified_exchange_id(doc))

    def test_an_untested_artifact_is_not_offered_as_routed(self) -> None:
        docs = {"a" * 64: document(url_aliases=[], subjects=["NST"])}

        self.assertEqual(len(kb.unrouted_local(docs)), 1)

    def test_a_tested_but_unresolved_artifact_is_not_retested_by_default(self) -> None:
        docs = {"a" * 64: document(url_aliases=[], subjects=["NST"],
                                   retrieval_route={"state": "unresolved"})}

        self.assertEqual(kb.unrouted_local(docs), [])
        self.assertEqual(len(kb.unrouted_local(docs, recheck=True)), 1)


class SamePublicationTest(unittest.TestCase):
    """Two distributors of one lodged PDF do not produce one extraction."""

    def test_reading_order_is_a_property_of_the_renderer_not_the_document(self) -> None:
        a = "Financial Results\nRecord performance\nFor personal use only\n"
        b = "Financial Results\nFor personal use only\nRecord performance\n"

        same, why = kb.same_publication(a * 20, b * 20)

        self.assertTrue(same)
        self.assertIn("page for page", why)

    def test_the_exchange_stamp_may_differ_but_nothing_else_may(self) -> None:
        page = "Appendix 4E results for the year ended 30 June 2026. " * 8
        same, why = kb.same_publication(page + "For personal use only", page)
        self.assertTrue(same)
        self.assertIn("For personal use only", why)

        differing = page.replace("30 June 2026", "30 June 2025")
        verdict, why = kb.same_publication(page, differing)
        self.assertFalse(verdict)
        self.assertIn("distinct version", why)

    def test_a_different_page_count_is_a_different_document(self) -> None:
        page = "Quarterly activities report for the June 2026 quarter. " * 8

        same, why = kb.same_publication(page, page + "\f" + page)

        self.assertFalse(same)
        self.assertIn("pages against", why)

    def test_two_unreadable_scans_are_unproven_not_equivalent(self) -> None:
        same, why = kb.same_publication("", "")

        self.assertIsNone(same)
        self.assertIn("visual read", why)


class TitleSuffixTest(unittest.TestCase):
    """The short analytical tails the second review returned. A title names the
    document; a note number, a table, or half a sentence is a reading of it."""

    ANALYTICAL = [
        "Appendix 4E and Annual Report 2025 — Note 17 Revolving Credit Facility, Note 6 Cash",
        "Half Year Report to 31 Dec 2025 (Replacement) — audited balance sheet, Note 14 "
        "Borrowings, Note 13 Lease liabilities",
        "ASX company key-statistics (markitdigital), numOfShares — the exchange's own figure",
        "FY26 Financial Results Presentation — FY27 Group guidance table and FY27 KCGM "
        "guidance slide",
        "June 2026 Quarterly Activities Report — FY26 full-year actuals, Gold Price "
        "Protection note, cash and gold table",
        "Final Investment Decision approved for Youanmi — Board FID 17 March 2026 following "
        "MDCP construction approval",
        "March 2026 Quarterly Report and AISC Guidance Update — live URL replacing a "
        "bsk-pdf-manager path that now 301s to HTML",
        "Divestment of the Big Springs Gold Project (Nevada) to Sentinel Metals — the only "
        "non-Australian asset CMM held",
    ]
    PUBLISHER = [
        "Appendix 4E - revised",
        "Quarterly Activities Report - December 2025",
        "Resource & Reserve Update Round Dam and Waihi - Correction",
        "Appendix 4E - Unaudited Preliminary FY2025 Final Report",
        "Half-Year Financial Report - 31 December 2024",
        "Appendix 3A.1 - Notification of dividend / distribution",
        "Mandilla Project Pre-Feasibility Study - Maiden Ore Reserve",
        "Half Year Financial Results Summary - H1 FY26",
        "Greatland - A Leading Australian Gold-Copper Producer",
    ]

    def test_the_suffix_moves_to_the_notes_and_the_headline_stays(self) -> None:
        for raw in self.ANALYTICAL:
            with self.subTest(raw=raw):
                title, analysis = kb.publisher_title(raw)
                self.assertIsNotNone(analysis)
                self.assertNotEqual(title, raw)
                if title:
                    self.assertNotIn("—", title)

    def test_a_publisher_headline_with_a_dash_survives_intact(self) -> None:
        for raw in self.PUBLISHER:
            with self.subTest(raw=raw):
                self.assertEqual(kb.publisher_title(raw), (raw, None))

    def test_the_audit_rejects_the_analytical_suffixes(self) -> None:
        for raw in self.ANALYTICAL:
            with self.subTest(raw=raw):
                complaint = kb.audit_title(document(title=raw, title_source="legacy title"))
                self.assertIsNotNone(complaint)
                self.assertIn("analytical suffix", complaint)

    def test_the_audit_accepts_publisher_headlines(self) -> None:
        for raw in self.PUBLISHER:
            with self.subTest(raw=raw):
                self.assertIsNone(kb.audit_title(
                    document(title=raw, title_source="exchange index headline")))

    def test_a_publisher_title_is_not_split_on_its_own_punctuation(self) -> None:
        # A news headline whose dash is part of the sentence. Splitting it would
        # invent an analytical note nobody wrote.
        headline = ("'It's unprecedented' – four investor takeaways from Diggers & Dealers "
                    "2026 - Australian Resources & Investment")

        self.assertEqual(kb.publisher_title(headline, from_publisher=True), (headline, None))
        self.assertIsNone(kb.audit_title(document(title=headline,
                                                  title_source="html <title>")))


class RetryScheduleTest(unittest.TestCase):
    """A refusal books a retry date, and the date is enforced (§7.4)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patch = mock.patch.object(kb, "AVAILABILITY", self.dir / "availability.jsonl")
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_refusal_books_a_date_without_being_asked(self) -> None:
        kb.availability("https://www.imf.org/x.pdf", "BLOCKED", http_status=403)
        kb.availability("https://issuer.example/gone.pdf", "LINK_DEAD", http_status=404)

        booked = {r["target"]: r.get("next_retry_at") for r in kb.read_jsonl(kb.AVAILABILITY)}

        self.assertEqual(booked["https://www.imf.org/x.pdf"],
                         kb.retry_after("BLOCKED", kb.now()))
        self.assertGreater(booked["https://issuer.example/gone.pdf"],
                           booked["https://www.imf.org/x.pdf"])

    def test_a_success_releases_the_block(self) -> None:
        url = "https://issuer.example/report.pdf"
        kb.availability(url, "BLOCKED", http_status=403)
        kb.availability("sha256:abc", "AVAILABLE_LOCAL", url=url)

        latest = kb.availability_by_address()

        self.assertIsNone(kb.retry_block(url, latest, "2026-08-23"))

    def test_a_future_date_blocks_and_a_past_one_does_not(self) -> None:
        latest = {"https://a/": {"result": "BLOCKED", "checked_at": "2026-08-23T00:00:00+00:00",
                                 "next_retry_at": "2026-08-30"},
                  "https://b/": {"result": "BLOCKED", "checked_at": "2026-07-01T00:00:00+00:00",
                                 "next_retry_at": "2026-07-08"}}

        self.assertIsNotNone(kb.retry_block("https://a/", latest, "2026-08-23"))
        self.assertIsNone(kb.retry_block("https://b/", latest, "2026-08-23"))

    def test_plan_defers_a_url_whose_retry_date_has_not_arrived(self) -> None:
        url = "https://www.pbo.gov.au/outlook.pdf"
        with mock.patch.object(kb, "VIEWS", self.dir), \
             mock.patch.object(kb, "load_documents", return_value={}), \
             mock.patch.object(kb, "legacy_index", return_value={url: {"title": "Outlook"}}), \
             mock.patch.object(kb, "availability_by_address", return_value={
                 url: {"result": "MISSING_OBJECT", "checked_at": kb.now(),
                       "next_retry_at": "2099-01-01"}}), \
             contextlib.redirect_stdout(io.StringIO()):
            kb.cmd_plan(argparse.Namespace(verbose=False))

        item = json.loads((self.dir / "acquisition_queue.json").read_text())["items"][0]
        self.assertEqual(item["next_retry_at"], "2099-01-01")
        self.assertIn("not retried before 2099-01-01", item["deferred"])

    def acquire(self, item: dict, **flags):
        (self.dir / "acquisition_queue.json").write_text(
            json.dumps({"items": [item]}))
        fetched: list[str] = []

        def fake_get(url, referer=None):
            fetched.append(url)
            return b"%PDF-1.7 fake", {"status": 200, "final_url": url,
                                      "content_type": "application/pdf"}

        args = argparse.Namespace(**{"tier": ["T1"], "limit": 0, "dry_run": False,
                                     "include_deferred": False, "retry_now": False,
                                     "reason": "test", **flags})
        with mock.patch.object(kb, "VIEWS", self.dir), \
             mock.patch.object(kb, "cmd_plan"), \
             mock.patch.object(kb, "load_documents", return_value={}), \
             mock.patch.object(kb, "save_documents"), \
             mock.patch.object(kb, "refresh_derived"), \
             mock.patch.object(kb, "ingest_bytes", return_value=document()), \
             mock.patch.object(kb, "POLITE_DELAY", 0), \
             mock.patch.object(kb, "http_get", fake_get), \
             contextlib.redirect_stdout(io.StringIO()):
            kb.cmd_acquire(args)
        return fetched

    def test_acquire_will_not_fetch_before_the_booked_date(self) -> None:
        item = {"url": "https://www.imf.org/x.pdf", "authority_tier": "T1",
                "tier_kind": "agency", "next_retry_at": "2099-01-01",
                "deferred": "BLOCKED on 2026-08-23; not retried before 2099-01-01"}

        self.assertEqual(self.acquire(item), [])

    def test_include_deferred_is_not_an_override_of_the_schedule(self) -> None:
        # --include-deferred means "fetch the leads too", not "ignore what the
        # host told us". Only the explicit override does that.
        item = {"url": "https://www.imf.org/x.pdf", "authority_tier": "T1",
                "tier_kind": "agency", "next_retry_at": "2099-01-01",
                "deferred": "BLOCKED on 2026-08-23; not retried before 2099-01-01"}

        self.assertEqual(self.acquire(dict(item), include_deferred=True), [])

    def test_the_explicit_override_fetches_and_says_so(self) -> None:
        item = {"url": "https://www.imf.org/x.pdf", "authority_tier": "T1",
                "tier_kind": "agency", "next_retry_at": "2099-01-01",
                "deferred": "BLOCKED on 2026-08-23; not retried before 2099-01-01"}

        self.assertEqual(self.acquire(item, retry_now=True), ["https://www.imf.org/x.pdf"])

    def test_a_url_with_no_booked_date_is_still_fetched(self) -> None:
        item = {"url": "https://qro.qld.gov.au/rates.pdf", "authority_tier": "T1",
                "tier_kind": "regulator"}

        self.assertEqual(self.acquire(item), ["https://qro.qld.gov.au/rates.pdf"])


if __name__ == "__main__":
    unittest.main()
