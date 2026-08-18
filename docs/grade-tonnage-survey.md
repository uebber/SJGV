# Grade-tonnage curves — Phase 0 feasibility survey

**Run 18 August 2026.** The gated first step of `docs/plan-open-items.md` item 2 and
methodology §12.2 item 2.

**Verdict: LOW coverage. Zero of twelve constituents publish what the model needs.
Per the plan's own decision gate, the item closes as _not sourceable from public
disclosure_.** That is the complete answer, not a failure to find one.

---

## 1. What was being tested

Item 2 is not "go measure gamma". It is: **make the §6 ounce count a function of
the gold price.** Real gold-miner convexity is the cut-off grade falling as the
price rises — material that is waste at A$3,000 and ore at A$8,000 — which in
the ledger's terms moves ounces from the M&I non-reserve tranche into
P&P. Today the ledger counts what each company discloses at *its own* cut-off,
which is a snapshot at one price.

Phase 0 asked one question of seventeen names:

> Does this company publish tonnes and grade **by cut-off** — a grade-tonnage
> table, or a resource stated at two or more cut-offs — in any public document?

---

## 2. What was searched

Full-text search over every primary document on the record in
`data/companies.json` that is cached and text-extractable — **≈11 MB of
extracted text across 17 companies**, including the complete JORC Table 1
sections of the largest statements (NST 5.77 MB, GMD 3.45 MB, CYL 0.49 MB), the
five standalone feasibility and pre-feasibility studies (RXL Youanmi DFS, RMS
Never Never PFS and Rebecca-Roe DFS, CMM Mt Gibson PFS, AUC Katanning DFS
update), and the R&R statements for all seventeen.

Patterns: `grade[-–\s]?tonnage`, `tonnage[-–\s]?grade`, cut-off sensitivity,
"reported/stated at … cut-off", "range of cut-offs", "multiple cut-offs",
"incremental cut-off", and resources quoted at two numeric g/t values in one
clause. Every hit was read in context rather than counted.

Two targeted web checks were run where a non-JORC disclosure regime might carry
the table: Westgold's NI 43-101 suite (TSX listing) and Greatland's Havieron
Feasibility Study.

---

## 3. Result, per name

`Constituent?` is the 18 Aug 2026 book. **A = available** (resource at ≥2
cut-offs, or a grade-tonnage table). **P = partial.** **U = unknown, not
retrieved.** **N = not published.**

| | Const. | | What the disclosure actually gives |
|---|---|---|---|
| **NST** | ✓ | **N** | One diluted cut-off per domain — 1.2 g/t Au inside MSO shapes for Australian underground, 3.4 g/t (0.1 oz/short ton) at Pogo. No table, no second cut-off, in 5.77 MB including the whole of Table 1. |
| **EVN** | ✓ | **N** | Tables 3 and 4 carry a Cut-off *column*: Cowal OP 0.30 g/t, UG 1.4 g/t (resource) / 1.5–1.8 g/t (reserve); Mungari UG 2.20–2.65 g/t. The ranges are across sub-domains, not a sensitivity. Ernest Henry (~0.7% Cu), Northparkes (0.25–0.58% CuEq) and Marsden (0.3% Cu) are not gold-denominated at all. |
| **CMM** | ✓ | **N** | Cut-off notes only: MRE 0.3–0.4 g/t open pit and 1.5 g/t underground; ORE KGP >0.3 g/t, MGGP OP >0.4 g/t (heap-leach pad >0.3), MGGP UG >1.5 g/t. The 331 kB Mt Gibson PFS returns **zero** hits on any sensitivity pattern. |
| **GGP** | ✓ | **N** | **Not on a grade cut-off at all.** Havieron resources sit inside A$80/t NSR shells (Crescent, Link) and A$50/t NSR shells (Breccias); the reserve is a break-even A$82/t NSR. Telfer uses "a variable break-even calculation using net smelter return … A$4,000/oz Au and A$6.00/lb Cu". See §5. |
| **GMD** | ✓ | **N** | Cut-offs by material type — 0.4 g/t oxide, 0.8 g/t fresh, a 0.6 g/t "Process Only" cut-off, wireframes at 0.5 and 2.5 g/t. The nearest miss in the survey: one Table 1 passage compares contained metal "at 0.6g/t and 0.9g/t Au cut-offs", but it is a **validation of the LUC estimation method**, not a resource stated twice. |
| **RMS** | ✓ | **N** | "Open Pit resources are generally reported at a cutoff of >0.5g/t and Underground Resources … at >1.0g/t, with the exceptions of Penny, Never Never and Pepper." Both 2025 studies return zero hits. |
| **RRL** | ✓ | **N** | **Worse than a single cut-off.** The reserve table's own note reads: "Cut-off grades vary according to oxidation and lithology domains. Listed cut-offs are the **weighted average** of these various cut-off grades for that project classification." Regis publishes an average of cut-offs it does not publish. |
| **WGX** | ✓ | **U** | The JORC statement says only that "cut-offs are clearly stated in the relevant tables" and carries no curve. **But Westgold is TSX-listed and files NI 43-101 technical reports** — Beta Hunt (6 Aug 2025), Higginsville (6 Jun 2025), Meekatharra (18 Dec 2024), Cue (31 Oct 2024), Fortnum. Every issuer PDF path returns HTTP 404 and SEDAR+ was not retrieved, so **these were not read.** This is the survey's one genuine unknown. See §6. |
| **VAU** | ✓ | **N** | No hit on any pattern in the lodged 15 Sep 2025 statement. |
| **CYL** | ✓ | **N** | Open pit 0.5 g/t, Plutonic underground 1.5 g/t. **A false positive worth recording:** Catalyst *does* build grade-tonnage curves — but as an internal proxy for **exploration-target** estimation, taking the Zone 250 / Zone 400 MREs as an analogue for undrilled ground and applying a 75% confidence factor. Not a published curve for a reported resource. |
| **PNR** | ✓ | **N** | "All Open Pits (0.5 g/t cut-off applied) excluding Gladstone-Everlasting (0.7 g/t), OK and Scotia Underground Mines (2.0 g/t)." One cut-off per mining method. |
| **RXL** | ✓ | **P** | **The only positive in the universe.** Figure 8 of the July 2025 MRE is captioned "Youanmi 2025 MRE underground grade tonnage curve and cut-off grade", with a COG axis running ≈0.5–4.5 g/t. It is a **chart, not a table**; it covers the **underground resource only**; and RXL is a developer pinned at 5% by the §8.1 per-name developer cap. See §5 for what the DFS adds. |
| BGL | | **N** | "Mineral Resources are reported at a 2.5 g/t lower cut-off." One number, one project. |
| OBM | | **N** | "Reported at a diluted cut-off of 1.3 g/t Au inside simulated MSO shapes"; stockpile cut-offs "vary based on location". |
| BC8 | | **N** | The cut-offs are not even in the current statement: "varying cut-offs based off several factors discussed in the corresponding Table 1 which can be found with the original ASX announcements for each Resource" — announcements of June 2022 and July 2023 vintage. |
| AAR | | **N** | Reserves at 0.30 g/t (Mandilla) and 0.40 g/t (Feysville); resources at 0.40/0.39 g/t inside pit shells struck at A$4,500 / A$3,500 / A$2,500 per ounce. Three price shells, one cut-off each. |
| AUC | | **N** | No hit in the DFS update or the quarterly restating it. |

### Coverage against the plan's decision gate

| | Constituents (12) | All candidates (17) |
|---|---|---|
| **A — available** | **0** | **0** |
| P — partial | 1 (RXL) | 1 |
| U — unknown | 1 (WGX) | 1 |
| N — not published | 10 | 15 |

The gate reads: **High (≥10 of 12) → proceed. Partial → stop and report. Low →
close as not sourceable.** Zero of twelve is not partial. It is low, and it is
low by a wide margin.

---

## 4. Why this was the expected answer

**JORC does not require a grade-tonnage curve.** A Mineral Resource is reported
at a single stated cut-off, and Table 1 asks only for "the basis of the adopted
cut-off grade(s)". Every issuer in this universe answers that question with the
basis and the number, and none of them with the curve behind it.

The sharpest illustration is Rox, the one name that got closest. Its DFS says
plainly that the full calculation was done —

> "…were calculated for the full **range of cut-offs**, allowing the scenario
> which produced the highest margin (margin optimised cut-off grade) to be
> identified. The **selected** cut-off grades used in the Study are shown in
> Table 10."

— and then publishes Table 10. **The issuers run the curve and publish only its
argmax.** That is not an oversight anyone can source around; it is what the
disclosure standard asks for.

---

## 5. Three findings that would have blocked Phase 2 anyway

Recorded so that a future session does not re-derive them, and so that the
closure rests on more than a coverage count.

**5.1 There is no such thing as "the" cut-off grade for these companies.** Every
issuer reports several at once — by mining method, by oxidation and lithology
domain, by deposit, and sometimes by stockpile location. Northern Star alone
carries 1.2 g/t and 3.4 g/t simultaneously. Regis publishes a *weighted average*
of domain cut-offs it never discloses individually. A single price-responsive
cut-off per company is not a simplification of the disclosure; it is a different
quantity, and constructing it would be exactly the "midpoints of ranges the
analyst constructed rather than the issuer published" that
`config.estimation_policy.forbidden` names.

**5.2 A material part of the book is not on a gold-grade cut-off at all.**
Greatland's entire 5.0 Moz reserve — 8.2% of the index — is reported inside net
smelter return value shells (A$50/t, A$80/t, break-even A$82/t), which move with
a gold *and* copper basket. Evolution's Ernest Henry, Northparkes and Marsden
are on copper and CuEq cut-offs. For those assets the ounce count is not a
function of the gold price even in principle; it is a function of a basket, and
making it one would require a copper deck the methodology does not have and
§0's objective does not want.

**5.3 The marginal-cost problem is unchanged and unsolved.** The cut-off grade
is set by *marginal* cost. The data layer carries **one AISC per company, an
average**, and no issuer in this universe publishes marginal cost per tonne
milled. `plan-open-items.md` flagged this as an open modelling question; nothing
found in this survey answers it, and Phase 0's result means it does not need to
be answered.

---

## 6. What was NOT established, stated plainly

- **Westgold's five NI 43-101 technical reports were not read.** Every
  `westgold.com.au/pdf/...` path now returns 404 — the same breakage that killed
  the 2025 R&R statement URL (see `companies.json` WGX `rr2025_mirror`) — and
  SEDAR+ was not fetched. NI 43-101 Item 14 more often carries a sensitivity
  table than JORC does, so this is the single most likely place in the universe
  for a real grade-tonnage table.
- **It does not change the verdict.** Westgold is one constituent. Even if all
  five reports carried full grade-tonnage tables at every deposit, coverage
  would be **1 of 12 (2 of 12 counting RXL's chart)** against a gate of 10, and
  the plan is explicit that a price-responsive ounce count applied to a subset
  "makes the cross-section inconsistent in the weight numerator — which is
  precisely the failure the mandatory-M&I rule in §6.1 exists to prevent."
- Historical per-deposit MRE announcements were not exhaustively read for all
  seventeen. The R&R statements that supersede them were.

**What would reopen this item:** not more searching. A change in what issuers
publish — several of them, in the same cycle. That is a disclosure-standard
question, not a research task, and the cheap way to notice it is to re-run this
survey at the annual deep rebalance rather than to keep the item open.

---

## 7. What ships instead

The **ledger mix** already reports the same economic idea out of disclosed
numbers: the index claim is **57% unhedged reserves / 30% near-money M&I / 13%
inferred tail** (18 Aug 2026 build). Unlike §9.2's modelled asymmetry of 1.00 —
which is 1.00 *by construction*, because on a fixed mine plan at one AISC the
NAV is linear in the deck — every ounce in that mix is one an issuer has
declared. A book drifting toward reserves is a book losing its option inventory,
and that is measurable at every rebalance for free.

§9.2's 1.00 should keep saying what it says now: the model cannot see convexity
because the ounce count cannot move, and after this survey we know the ounce
count cannot be made to move from public disclosure. **The methodology does not claim
convexity it cannot measure.** It claims a cheaper claim on more ounces in a
jurisdiction that cannot take them, and that number is arithmetic on disclosed
inputs.
