# STORM Documentation Audit — the book interrogated by thirteen readers

> **What this is.** A perspective-guided audit of Arisbe's documentation, produced by the
> STORM method (Stanford OVAL): thirteen reader-personas each generated the questions they
> would genuinely bring to the book from its table of contents alone; a repo-grounded
> "documentation expert" then answered each against the actual sources, verdicting
> **ANSWERED / PARTIAL / GAP**. This file is the curated docket — questions clustered into
> gap themes, counted, prioritized, never silently dropped (the same discipline the
> `query_docket` applies to M). It is a **working/dev doc**, not a book chapter.
>
> Run 2026-07-06→07. Method note: the persona question-generation and the web-grounded
> prospect surveys ran as multi-agent workflows; the grounded-answering fan-out was
> **truncated by session rate limits**, so the ANSWERED/PARTIAL/GAP verdicts below were
> completed in the main loop from repository knowledge plus targeted verification greps
> (each load-bearing verdict cites the file checked). ~180 persona questions across 13
> readers; the follow-up deepening round was dropped for budget. Companion:
> [PROSPECTS_MULTIPERSPECTIVE.md](PROSPECTS_MULTIPERSPECTIVE.md) (the forward-looking half).

## The thirteen readers

Seven from `ARISBE_IN_PRACTICE.md` (newcomer-student, teacher, researcher,
logician-mathematician, Peirce scholar, domain professional, ontologist) + six **delta
perspectives** discovered by surveying how comparable projects' docs serve audiences
Arisbe's book does not yet name: **course designer**, **evaluator** (adopt-vs-Lean/TLA+/
Protégé), **API integrator**, **AI-agent integrator**, **run operator**, **open-source
contributor**. The deltas were the sharpest questioners — their gaps dominate the docket.

## The gap docket — clustered, verdicted, prioritized

Priority = (breadth across personas × severity), newcomer- and adopter-blocking first.
"Disposed" marks a gap this same effort fixed (see the disposal section).

| # | Gap theme | Verdict | Asked by | Where it stands / what's missing | Priority |
|---|---|---|---|---|---|
| G1 | **HTTP API reference** — endpoint list, JSON schemas (LayoutDTO, EGI), error codes, a minimal client example | **PARTIAL → DISPOSED (partial)** | API-integrator, AI-integrator, teacher (batch-grade), course-designer, evaluator | `ARISBE_CORE_API_REFERENCE.md` is **Python-only**; routes documented only implicitly in test-file descriptions. **But FastAPI auto-serves `/docs` (Swagger) + `/openapi.json`** (`web_api/main.py:22`, defaults on) — undocumented, not missing. **Disposed:** documented the live spec + a minimal client recipe (see D1). Remaining: hand-written payload/error schemas for the highest-traffic routes. | **P0** |
| G2 | **Error / refusal index** — what a stuck user sees and does for each refusal | **GAP → DISPOSED** | teacher, newcomer, API-integrator, operator, contributor, logician | The refusal vocabulary (`CorrespondenceViolation`, `Regime3Violation`, `PHASE_REFUSED` 409, `NO_PROPOSAL`, `CHAIN_NOT_FOUND`, `MODAL_PROPOSAL_INVALID`, drawing-validity findings) is well-designed but **nowhere catalogued**. **Disposed:** new `TROUBLESHOOTING.md` (D2). | **P0** |
| G3 | **"When NOT to use Arisbe" / positioning** vs Lean, Coq, Isabelle, TLA+, Alloy, Protégé | **PARTIAL → DISPOSED** | evaluator (whole set), logician, domain-pro, ontologist | Comparisons are scattered (`ADVERSARIAL_EXAMINATION.md`, `CONTRIBUTION_AND_PRIOR_ART.md`) but there is **no positioning section and no explicit anti-pitch** (verified: no "when not to use" in VISION/CAPABILITY). The single most-requested thing from the evaluator. **Disposed:** added a "When to reach for something else" section to `VISION_AND_SCOPE.md` (D3). | **P0** |
| G4 | **Contributor guide** — protected-vs-additive, the socket contracts, the test gate, review norms | **GAP → DISPOSED** | contributor (whole set), ontologist, logician, AI-integrator | Deep guidance exists but only in `CLAUDE.md` / `AGENTS.md` (insider/agent-facing); **no `CONTRIBUTING.md`** (verified absent). **Disposed:** new root `CONTRIBUTING.md` orienting the outsider (D4). | **P0** |
| G5 | **Operations runbook** — launch a long unattended run, stop conditions, resume, digest fields, tripwires, disposal | **PARTIAL** | operator (whole set), researcher, AI-integrator | The knowledge is real but lives in `runs/RUN_*_LOG.md` (lab notebooks) + `AUTOMATED_ENDOPOREUTIC_GAME.md` §10 + tool `--help`. No operator-facing runbook consolidates the driver command, the digest-field glossary, and the resume/disposal procedure. **Not disposed** (larger; queued). | P1 |
| G6 | **Teaching pack** — author your own challenge targets keyed to a syllabus; batch-grade N submissions; gradeable/collectable artifacts; multi-user | **PARTIAL/GAP** | teacher, course-designer, education (implicit) | `CHALLENGE_BANK` is a code list (`challenge_mode.py:76`) with no documented user-authoring path; `same_graph`/`legible_diff` grading exists but no batch/CLI grading doc; sessions are **in-memory, per-process** (`ergasterion.py:8`) → no multi-user story. Queued. | P1 |
| G7 | **Scale & performance envelope** — largest graph/proof/ontology that stays interactive; where the super-linear walls sit *now* | **PARTIAL** | evaluator, logician, ontologist, operator, domain-pro, researcher | The RUN logs + CAPABILITY_MAP carry the real numbers (canonical-signature fix, visibility-graph fix, ~200-atom attest) but they are scattered across dated notebooks; no single "performance envelope" table. Queued. | P1 |
| G8 | **Soundness boundary — proven vs tested vs claimed** | **PARTIAL** | logician (whole set), evaluator, Peirce scholar, AI-integrator | The `FIDELITY_*` + `ADVERSARIAL_EXAMINATION` chapters are honest and strong, but a reader cannot quickly see *which* results rest on the ~118 core tests vs paper argument vs corpus round-trips, or what an external re-checker would need. Partly a docs gap, partly the prospects R1 (proof certificates). Queued. | P1 |
| G9 | **Multi-user / concurrency / day-two ops** | **GAP** | teacher, domain-pro, evaluator, API-integrator | Confirmed single-user in-memory; no CORS/auth/locking story; `save_uod_with_chain` concurrency unaddressed in docs. Honest scoping note owed. Queued. | P2 |
| G10 | **Import fidelity specifics** — exact OWL-2 construct coverage, skip-report contents, round-trip guarantee | **ANSWERED (mostly)** | ontologist, domain-pro, researcher | `EXTERNAL_SOURCES_AND_IMPORT.md` + `IMPORT_EXPORT_FORMATS.md` + `test_owl_import.py` cover this well; the skip-report is real and per-construct. Minor: a one-page "OWL 2 profile coverage" table would close it. Low-priority. | P3 |
| G11 | **Newcomer first-hour path** | **ANSWERED** | newcomer, teacher | `GETTING_STARTED.md` (role-aware), the in-app primer, `FIELD_GUIDE_AND_DRAGONS.md`, the challenge ladder, and the glossary reading-order are genuinely strong and cross-linked. The book's best-served reader. | — |
| G12 | **Provenance / citation granularity** | **ANSWERED** | Peirce scholar, domain-pro, researcher | `scholarly_citation.py` + provenance model + the citation chapter answer per-assertion attribution, honest-omission, BibTeX. Peirce-specific identifier alignment (Robin/LoF sigla) is a *prospect*, not a doc gap (see prospects R6). | — |

## Coverage tally

- **ANSWERED (well-served):** G11 (newcomer), G12 (provenance), G10 (import, near-complete) — the book's conceptual and on-ramp core is strong.
- **PARTIAL:** G1, G3, G5, G6, G7, G8 — knowledge exists in the repo but not where the asking reader looks (scattered across code docstrings, run logs, or insider docs).
- **GAP → now disposed:** G2 (error index, → `TROUBLESHOOTING.md`), G4 (contributor, →
  `CONTRIBUTING.md`); **still GAP:** G9 (multi-user/auth/CORS) — genuinely absent, and the
  cold read found it is *structural* (single in-memory process, one shared corpus), not just
  undocumented.
- **The pattern:** Arisbe's documentation is **excellent at the conceptual/why layer and the newcomer on-ramp, and thin at the task/how-to/reference layer** — exactly the genre gap the phase-0 survey predicted (comparable projects ship cookbooks, error indices, positioning FAQs, and contributor guides; Arisbe ships design-of-record docs, worked exemplars, and pre-registered run logs — a differentiator worth keeping, not diluting).

## Cold-reader independence check (2026-07-07)

Three fresh agents cold-read the three least-certain PARTIAL/GAP clusters (G1 API, G5
operations, G6 teaching) with no priors, to catch author-familiarity blind spots. All three
**confirmed** the cluster verdicts and sharpened them — and G1 caught two real defects in this
audit's own disposals, plus a portability bug the audit undersold. Corrections applied below.

- **G1 (API):** verdict holds, but the honest shape is *1 disposed / 3 partial / 3 full GAP* —
  the single "PARTIAL" hid that a **minimal HTTP client example (Q4) did not exist** (the
  original D1 claim of a "client recipe" was **overstated** — only OpenAPI pointers were
  added) and that **auth/CORS/multi-tenancy (Q6, tracked as G9) and seam stability (Q7)** are
  full GAPs not surfaced under G1. Also: `TROUBLESHOOTING.md` was **not in the book nav**.
  *Fixed this pass:* a real curl client example added to `install.qmd`; `TROUBLESHOOTING.md`
  added to the Quarto book (Part III) + `_devlinks`; and the **hardcoded-corpus-path bug** the
  cold read exposed (see below).
- **G5 (operations):** confirmed PARTIAL. Sharpening — the launch/stop/resume flow is actually
  *well* covered by the driver `--help` + AEG §10 + `TROUBLESHOOTING.md`; the two genuine holes
  are a **digest-field glossary with healthy/stop thresholds** and a **one-page disposal
  checklist**. Those two artifacts (not re-documenting the flow) are the highest-leverage
  runbook work when G5 is disposed.
- **G6 (teaching):** confirmed GAP-leaning-PARTIAL. Sharpening — one **bright spot** the audit
  undersold: the *grading pedagogy* (beginner-vocabulary legible diff + `same_graph` accepts
  any isomorphic answer) **is** well-documented (`TROUBLESHOOTING.md`, `ARISBE_IN_PRACTICE.md`,
  `FREEFORM_COMPOSITION_AND_LEARNING.md`). What's absent is the classroom-*operations* surface
  (author → distribute → collect → batch-grade → attributed artifact → 30 users), which is not
  merely undocumented but structurally single-user.

### Spillover finding — a real portability bug (fixed 2026-07-07)

The G6/G9 cold read found the web app **hardcoded the author's absolute corpus path**
(`/Users/mjh/Sync/GitHub/Arisbe/tomos`) across 8 route files — so a clone on any other machine
served no corpus; the app only ran on one laptop. This is worse than "no multi-user story": a
*single* user on a second machine was already blocked. **Fixed:** a new `src/web_api/paths.py`
resolves `TOMOS_PATH`/`SCRATCH_PATH` **relative to the repo** with `ARISBE_TOMOS`/
`ARISBE_SCRATCH` env overrides; verified the app boots and serves 42 UoDs from the relative
path. The largest single win of the whole STORM exercise — and one the audit's own author would
not have found, being over-familiar with a repo that always ran from that path.

## Disposed this effort

- **D1 — API discoverability *and* a real client example.** `install.qmd` gained an "HTTP API"
  section pointing at the live `/docs` (Swagger UI) and `/openapi.json`, **a working curl
  client example** (list corpus → open a graph), the env-override deployment note, and the
  honest single-user caveat; `CAPABILITY_MAP.md` gained a row. *(Corrected 2026-07-07: the
  first pass claimed a client recipe it did not include — the cold read caught it; now it does.)*
- **D2 — `docs/TROUBLESHOOTING.md`** (new): the refusal/error index in EG vocabulary —
  each refusal, what it means, what the user does. Serves G2 across six personas.
- **D3 — positioning.** `VISION_AND_SCOPE.md` gained a "When to reach for something else"
  section (the honest anti-pitch: Lean/Isabelle for dependent types & big proof automation;
  TLA+/Alloy for temporal model-finding; a production OWL reasoner for large-scale
  classification — and what Arisbe uniquely offers instead).
- **D4 — `CONTRIBUTING.md`** (new, repo root): the outsider's orientation — protected core
  vs additive surface, the socket contracts (Proposer/LiveSource/PolicyAgent/lens), the
  test gate, the CI-safety convention, and where the deeper guidance lives.

## Queued (named, not silently dropped)

G5 (operations runbook), G6 (teaching pack), G7 (performance-envelope table), G8 (a
proven-vs-tested-vs-claimed matrix), G9 (multi-user honest-scope note). Each is a
bounded doc task; none blocks the newcomer or the conceptual reader. The performance and
soundness-boundary gaps (G7, G8) also connect to prospect candidates (R1, R5) — best
written once those directions are decided.
