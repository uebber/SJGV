# Sourcing brief — for a research agent working one ticker

You are sourcing data-layer fields for **one ASX gold miner** for the SJGV
index. Read this whole brief before fetching anything.

**You research and propose. You do not write to `data/`.** Several agents run in
parallel against the same `companies.json`; concurrent writes would clobber each
other. Return proposals; the orchestrator merges, validates and commits.

---

## 1. The one non-negotiable rule

**DERIVE OR FAIL.** See `data/README.md` → "Derive or fail" and
`config.estimation_policy`. A value may only be:

| | |
|---|---|
| **sourced** | read from a document you fetched and can quote |
| **derived** | arithmetic from other *sourced* numbers — `M&I non-reserve = M&I total − P&P`, `inferred = mr_total − M&I`, or the midpoint of a range **the issuer published**. State the arithmetic. |
| **bound** | a conservative limit that runs *against* the name, labelled as such |

**Forbidden — return `null` instead:** cohort medians, imputation, run-rate
annualisation into a period the company has not guided, apportioning a
multi-year programme by judgement, midpoints of ranges *you* constructed, or any
number whose note cannot name the arithmetic behind it.

> A missing value is visibly missing. An invented one looks like data and
> propagates. This project has already been burned twice: a resource-split
> imputation understated M&I ounces by 26–65% per name, and an apportioned capex
> figure nearly decided a binary survival gate the wrong way.

**If you cannot source it, say so and say what you tried.** That is a complete,
successful answer. Do not fill the gap.

---

## 2. What to source, and from where

Run `python tools/gaps.py --json` and `python tools/provenance.py` to see what
your ticker needs. Two categories:

- **Missing** — no value at all. Highest priority: `mi_non_reserve_moz` /
  `inferred_moz` (the M/I/Inferred table), which currently rejects six names.
- **Secondary** — a value exists but cites a news aggregator rather than a
  filing. Priority within these: anything in `GATE_FIELDS`
  (`tools/provenance.py`) on a weighted name, because a gate flips where a score
  merely degrades.

### Field → document that normally carries it

| Field | Document |
|---|---|
| `pp_moz`, `mr_total_moz`, `mi_non_reserve_moz`, `inferred_moz` | Annual Mineral Resource & Ore Reserve statement — the M/I/Inf table, not the headline |
| `reserve_price_aud`, `resource_price_aud` | Same statement, "material assumptions" / table notes — the **gold price the estimate was constrained at** |
| `aisc_aud_oz`, `production_koz_yr` | Quarterly activities report, or FY guidance |
| `net_debt_aud_m`, `undrawn_facilities_aud_m` | Quarterly cash + debt note, or annual borrowings note. Negative = net cash |
| `hedge_share_fwd24m` | Quarterly hedge book note — derive as hedged oz ÷ (2 × annual production) |
| `committed_capex_aud_m` | **Contracted or board-approved builds only.** Exploration is deferrable and excluded. Pre-FID projects are excluded — say so explicitly if one exists |
| `gold_nav_share`, `eligible_ounce_share`, `ineligible_nav_share` | Revenue by metal; ounces by jurisdiction |
| `study_stage`, `approvals_land_secured`, `remaining_capex_aud_m` | Developers only — PFS/DFS announcement, approvals releases |

### Channels, in the order that has actually worked

1. **ASX announcements feed** — the lodged document, highest quality:
   ```
   https://asx.api.markitdigital.com/asx-research/1.0/companies/{TICKER}/announcements
   → items[].documentKey
   https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/{documentKey}
   ```
   No token needed. **Capped at ~5 recent items**, so it catches what is
   published now, not the back catalogue.
2. **Issuer resources-and-reserves page.** Sometimes the full JORC table in HTML
   (Ausgold, Catalyst). Find it by fetching the homepage and grepping `href` for
   `resourc|reserv|jorc`; guessing URLs mostly 404s.
3. **Issuer annual report PDF** — reliable, but a year stale by August.
4. **listcorp.com / investegate.co.uk / api.investi.com.au** mirrors when the
   issuer blocks or JS-renders. *Largely untried — try these first if 1–3 fail.*
5. **Visual read** where the table is a PNG (Greatland does this; Pantoro's R&R
   page carries only the table's footnotes because the table is an image).
   Download the image and read it. No text extraction will reach it.

Use `python tools/fetch.py <url>` — it caches, sets a browser UA, runs
`pdftotext -layout` on PDFs, and flags image-only documents. `WebFetch` **cannot
read PDFs**.

---

## 3. Traps that have already caught this project

- **Appendix 2A / 3B show INCREMENTAL issuance, not totals.** Never read a share
  count off one.
- **Vintage mixing.** Capricorn's website showed a 6.6 Moz resource against a new
  5.24 Moz reserve — a 79% reserve/resource ratio that was an artefact of two
  different statements. Catalyst's R&R page mixes announcements from 2023–2025 in
  one table. **Every number in a proposal must come from the same statement.**
- **Attributable vs 100% basis.** Catalyst shows a Group Total Ore Reserve of
  861 koz *and* an Attributable Ore Reserve of 1,541 koz on the same page.
- **Gold vs gold-equivalent.** Never accept AuEq for a gold field.
- **Headline vs table.** Genesis headlined 4.4 Moz over a table summing to 4.2.
  **The table wins.**
- **URL vintage lies.** Ora Banda's "2026" URL served the FY25 statement. Check
  the date *inside* the document.
- **Measured may be absent.** Capricorn reports Indicated only, no Measured — so
  M&I = Indicated. That is normal, not an error.
- **Reserves are a subset of resources.** `mi_non_reserve = M&I total − P&P`,
  never M&I total on its own.

---

## 4. Verify before proposing

- **Arithmetic:** M&I + Inferred should reconcile to the resource total; tonnes ×
  grade should reconcile to ounces. Report any discrepancy rather than smoothing
  it.
- **Plausibility:** reserve/resource ratios above ~75% or below ~15% usually mean
  mixed vintages.
- **Share counts:** cross-check against the ASX API's own `marketCap ÷
  priceClose`.
- **Against the incumbent:** if you are replacing a secondary value and the
  primary disagrees by more than a few percent, that disagreement is a finding —
  lead with it.

---

## 5. Return format

Return JSON only. No prose outside it.

```json
{
  "ticker": "OBM",
  "documents": [
    {"key": "rr_fy26", "title": "...", "url": "...", "date": "2026-08-14",
     "type": "primary", "how_found": "ASX announcements feed, documentKey ..."}
  ],
  "proposals": [
    {"field": "mi_non_reserve_moz", "value": 1.84, "doc": "rr_fy26",
     "provenance": "derived",
     "arithmetic": "Indicated 7.082 Moz − Probable reserves 5.241 Moz",
     "quote": "Total 275.8 Mt @ 0.8 g/t for 7,082 koz Indicated",
     "confidence": "high",
     "note": "No Measured category reported, so M&I is Indicated only."}
  ],
  "unresolved": [
    {"field": "aisc_aud_oz", "why": "Company has never published an AISC; withheld
      in the Dec 2025 quarterly as unrepresentative and deferred to the FY26
      annual result.", "tried": ["ASX feed", "issuer site", "listcorp"],
     "when_available": "FY26 annual report, expected late Aug 2026"}
  ],
  "conflicts": [
    {"field": "pp_moz", "existing": 1.5, "found": 1.541,
     "which_is_right": "found — the existing value is the rounded figure from a
      secondary source; 1,541 koz is the attributable table in the statement."}
  ]
}
```

`confidence` is `high` only when you read the number in a table in a primary
document you fetched. Anything inferred from narrative text is `medium`.
Anything from a secondary source is `low` and must say why the primary failed.
