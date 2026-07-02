# Alpha Release — Documentation Consolidation Plan

**Status:** planning (started 2026-06-30). **Goal:** prepare an alpha release of Arisbe to
share with others, delivering the documentation as **both a book (PDF/epub) and a browseable
web help**, single-sourced, plus a clean "clone → run → open the book" path.

This is the working artifact for the track. It holds: (1) the agreed book structure, (2) a
full triage of every doc, (3) the open tooling/strategy decisions, (4) the build sequence.

---

## 1. Book structure (Diátaxis-aligned, agreed 2026-06-30)

One source serves both the linear book and the web help. Five reader parts + a separate
in-repo Dev section excluded from the reader's book.

- **I · Why** — Intro & motivation; **The central problem** (linear↔graphical
  correspondence) as its own chapter; Philosophy.
- **II · Getting started** — Install & run from the repo; Your first graph; Doors by background.
- **III · Using Arisbe** — the three modes in practice; Worked examples (the exemplars);
  Import/export incl. the Peirce-edition path; How-to / FAQ.
- **IV · How it works** — Architecture; the §3.3 correspondence contract in depth; Capability map.
- **V · Reference** — linear formats; Core API; Glossary; References / prior art; Index.
- **Dev (in-repo, excluded from the book)** — roadmap, plans, design-of-record, session logs,
  evaluations, spikes.

---

## 2. Triage of `docs/` (61 .md + subdirs)

**Disposition key:** `BOOK` = reader's book (Part noted) · `DEV` = keep in repo, design-of-record,
excluded from book · `ARCHIVE` = historical, move to dev archive · `MERGE` = fold into another
doc then retire · `RETIRE` = drop.

### → BOOK

| Doc | Part | Notes |
|---|---|---|
| VISION_AND_SCOPE.md | I | Primary intro; absorb PRODUCT_VISION. |
| LINEAR_GRAPHICAL_CORRESPONDENCE.md | I (+IV) | The central-problem chapter; also the in-depth §3.3 contract for IV. |
| CHAIN_OF_SEMIOSIS.md | I | Philosophy. |
| MANIFEST_AND_MEANING.md | I | Philosophy (blank = only truth; warrant gradient). |
| FIDELITY_A_PLAIN_ACCOUNT.md | I | The accessible fidelity chapter. |
| LEVEL_ZERO_AND_THE_REGISTERS.md | I | Philosophy. |
| MODALITY_WITHOUT_GAMMA.md | I | Philosophy. |
| FIDELITY_AND_DEPARTURES.md | I (appendix) | Deep version; book appendix or scholarly link. |
| GETTING_STARTED.md | II | Doors by background (already role-aware). |
| FIELD_GUIDE_AND_DRAGONS.md | II | Your first graph + the dragons. |
| ARISBE_IN_PRACTICE.md | III | The three modes through their users. |
| ENDOPOREUTIC_GAME_GUIDE.md | III | The game (2090 lines — may split into sections). |
| EXEMPLARS.md | III | Worked examples = the seeded corpus. |
| EXTERNAL_SOURCES_AND_IMPORT.md | III | The consolidating import doc; absorb CORPUS_AND_IMPORT_MODEL. |
| IMPORT_EXPORT_FORMATS.md | III/V | Formats how-to; format details may move to V. |
| FREEFORM_COMPOSITION_AND_LEARNING.md | III | Compose-by-drawing how-to. |
| FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md | III | Peirce-edition publishing how-to (trim feature/dev framing). |
| NL_TO_LOGIC.md | III | "LLM proposes, Arisbe disposes" how-to. |
| arisbe_triad_architecture.md | IV | Architecture overview. |
| UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md | IV | Core paradigm. |
| DAG_HISTORY_ARCHITECTURE.md | IV | Branching history. |
| EXACT_CORRESPONDENCE.md | IV | The §3.3 contract realized geometrically. |
| DOMAIN_ORACLE_AND_M.md | IV | How the interpretation register works. |
| GENERATION_AND_TESTING.md | IV | Making (Ergasterion) vs the game (Agon). |
| CAPABILITY_MAP.md | IV/V | What works / maturity. |
| GLOSSARY.md | V | Glossary + reading order. |
| CONTRIBUTION_AND_PRIOR_ART.md | V | References / prior art. |
| ARISBE_CORE_API_REFERENCE.md | V (appendix) | Auto-generated; reference appendix. |
| CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md | V | Linear-format reference (FOPL). |
| ARISBE_EXISTENTIAL_GRAPH_DEFINITION.md | V/I | EG definition; reference or intro support. |

### → MERGE / retire

| Doc | Disposition | Notes |
|---|---|---|
| PRODUCT_VISION.md | **MERGED → VISION_AND_SCOPE.md (done 2026-06-30)** | Superseded + partly stale (listed NL→logic as out-of-scope, but it ships). Replaced with a redirect stub; live code/doc refs repointed. |
| CORPUS_AND_IMPORT_MODEL.md | **KEEP as DEV (revised)** | *Not* a merge after content review: EXTERNAL_SOURCES_AND_IMPORT is a summary that **depends on** it (points to its §5–§5.3 for COLORE wrinkles, worked landings, the import-kind taxonomy). The summary is the book chapter; this stays as the dev deep-doc behind it. |
| ARISBE_FOR_SCHOLARS.md | **KEEP + promote to a BOOK chapter (revised)** | *Not* a merge after content review: it is a distinctive **scholarly invitation** (direct address to Pietarinen; the Agonothetes + mechanized-iconicity critique asks), not redundant on-ramp material. Added as a Part II chapter. (Minor staleness — `uv sync` missing `--extra web`, "~23 items" — to refresh later.) |

### → DEV (keep in repo, design-of-record; excluded from book)

ROADMAP.md · RETURN_TO_DEVELOPMENT.md · CORE_API_USAGE_GUIDE.md · AUTOMATED_GRAPHEUS.md ·
THE_MINIMAL_IN_VIEW_SET.md · TENSION_LAYOUT.md · PRESENTATION_DELTAS_AND_STYLE.md ·
ELK_LAYOUT_IMPLEMENTATION_SUMMARY.md · STYLE_SYSTEM_GUIDE.md · WEB_VIEWER_DESIGN.md ·
REFERENCE_AND_TRANSCLUSION_NODE.md · DEFINITION_NODE.md · SCHEMA_HOLE_CORRESPONDENCE.md ·
UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md · PROOF_SERIALIZER.md · ADAPTIVE_SCOPE_VIEWER.md ·
MATH_FIXTURES_ZFC_PEIRCE_1881.md · TRANSFORMATION_WORKFLOW_SPEC.md · COMPOSITION_WORKFLOW_SPEC.md ·
ARCHIVE_INDEX.md · ADVERSARIAL_EXAMINATION.md *(or book appendix)* · **CORPUS_AND_IMPORT_MODEL.md**
*(deep-doc behind EXTERNAL_SOURCES_AND_IMPORT)* · **AUTOMATED_MODEL_DEVELOPMENT.md** ·
**AUTOMATED_ENDOPOREUTIC_GAME.md** *(both added 2026-06-30→07-02: design-of-record for the
automated-EPG arc — `_devlinks.lua` already routes book links to them to GitHub, no manifest change
needed; the arc's user-visible summary lives in CAPABILITY_MAP §H)*

### → ARCHIVE (historical; move to dev archive)

SESSION_LOG_2026-06-10.md · SESSION_LOG_2026-06-11.md · ADAPTIVE_SCOPE_SPIKE.md ·
SPROTTY_EVALUATION.md · FOLIO_EVALUATION.md · ORGANON_IMPORT_WALKTHROUGH.md ·
coherence/egi_ligature_position_cooptimization_spec.md

### → RETIRE

DOCUMENTATION_REVIEW_PREP.md *(stale process doc)*

### Subdirectories (unchanged)

- `references/` — source PDFs (Dau, Peirce, Sowa, etc.); cite from the book, don't bundle.
- `derived/` — extracted text/summaries of the PDFs; dev-only.
- `styles/`, `assets/`, `archived/` — leave in place; `archived/` is already the historical bin.

**Tally (revised after content review):** ~31 BOOK (incl. ARISBE_FOR_SCHOLARS) · 1 MERGE
(PRODUCT_VISION, done) · ~22 DEV (incl. CORPUS_AND_IMPORT_MODEL) · 7 ARCHIVE · 1 RETIRE.

---

## 3. Decisions (taken 2026-06-30)

1. **Single-source tooling → Quarto.** One markdown source → HTML site + PDF + epub; native
   BibTeX citations that pair with `scholarly_citation`; can embed live engine SVG.
2. **Reorganization strategy → keep files flat; the manifest selects.** `docs/*.md` stay where
   they are. The **Quarto project root is `docs/` itself** (`docs/_quarto.yml`), so each canonical
   doc is listed **directly** as a chapter and its relative cross-links (`SIBLING.md`,
   `../CLAUDE.md`) resolve naturally — no include indirection, no link rewriting. Only the two
   book-specific pages (`docs/index.qmd` preface, `docs/install.qmd`) are authored. Dev docs are
   simply not listed, so they are not rendered into the book. Dev/book separation is logical, not
   physical. *(Earlier this session used a `docs/book/` subdir + `{{< include >}}` stubs; that
   broke the flat docs' relative links, so it was replaced by the docs-root layout.)*
3. **One source, two renders → yes.** The rendered HTML site (`docs/_book/`) is served by the web
   app at `/book` (mounted in `web_api/main.py`, active once rendered).

---

## 4. Build sequence / progress

1. ✅ Decisions above.
2. ✅ **Book scaffold (docs-root layout)** — `docs/_quarto.yml` (5 parts, 31 chapters listing the
   flat docs directly), `docs/index.qmd` preface, `docs/install.qmd` (the authored install/run/
   build chapter). `.gitignore` excludes `docs/_book/` + `docs/.quarto/`.
3. ✅ **README quickstart rewritten** — clone + `uv sync --extra dev --extra web` + uvicorn + the
   three live mode routes + the `quarto render docs` book build + the `/book` route; stale
   Agon-pending row and PRODUCT_VISION pointer fixed.
4. ✅ **Part II · Getting started** — authored `install.qmd`, plus FIELD_GUIDE_AND_DRAGONS,
   GETTING_STARTED, and the promoted ARISBE_FOR_SCHOLARS as chapters.
5. ✅ **`/book` route wired** — conditional `StaticFiles` mount of `docs/_book` in
   `web_api/main.py` (before the `/` catch-all; active once rendered; app import verified).
6. ✅ **Render verified, all formats** — Quarto 1.9.38 (local) + TinyTeX: `quarto render docs` →
   **30 HTML pages, ZERO link warnings** (docs-root layout resolves all book↔book links), no dev
   docs leaked into `_book`; `--to pdf` → `Arisbe.pdf` (504 pp, 2 MB) and `--to epub` →
   `Arisbe.epub` (588 KB) both build. `_book/` git-ignored (0 generated files tracked).
7. ✅ **Merge 1 — PRODUCT_VISION retired** → VISION_AND_SCOPE; redirect stub left; live code/doc
   refs repointed (`organon.py`, `ergasterion.py`, `AI_CONDUCT_GUIDELINES`, `RETURN_TO_DEVELOPMENT`,
   `CHAIN_OF_SEMIOSIS`). Merges 2 & 3 revised to **keep** (see §2 table) after content review.
8. ✅ **PDF margins fixed** — overfull boxes 167 → **0 severe / 0 visible** (90 are <5pt,
   imperceptible). `_quarto.yml` pdf: `geometry margin=1in`, `fontsize 10pt`, `code-overflow: wrap`,
   header adds `microtype` + `xurl` + `hyphenat[htt]` (breaks long inline `module.function`/path
   tokens) + `\sloppy`/`\emergencystretch` + `\fvset{fontsize=\small}`; two wide source blocks
   (the VISION §7 diagram, a FEATURE_PEIRCE TikZ sample) trimmed; a slash-run in CAPABILITY_MAP
   spaced. PDF now ~1 MB.
9. ✅ **Residual dead links fixed** — two moves: **(a) promoted** three heavily-linked book-grade
   docs to chapters — FIDELITY_AND_DEPARTURES + ADVERSARIAL_EXAMINATION (Part I), GENERATION_AND_TESTING
   (Part IV); **(b) `_devlinks.lua`** (registered `filters:`) rewrites links to *non-book* docs
   (ROADMAP, CORPUS_AND_IMPORT_MODEL, THE_MINIMAL_IN_VIEW_SET, …) and repo-root files (`../CLAUDE.md`)
   → GitHub-source URLs **at render time**, so source files keep clean relative links for in-repo
   reading while the book/help has no dead internal links. Verified: dev links → github.com,
   book↔book → `./X.html`. 33 HTML pages now.
10. ✅ **Book-voice (started)** — ARISBE_FOR_SCHOLARS factual fixes (the `uv sync --extra dev --extra
    web` install + de-numbered the stale "~23 items"; pointer to the Install chapter).
11. ✅ **Abbreviation clarity pass** — added an anchored **Abbreviations** quick-reference to the
    Glossary (each term a `### ABBR` heading → clean `#egi`/`#t-box`/… slugs that resolve on GitHub
    *and* in Quarto), then expanded each important abbreviation on **first use per chapter** to
    *Full Term ([ABBR](GLOSSARY.md#anchor))* across 28 source docs (174 links). Done as **source
    edits** (benefits in-repo + book) via 5 parallel agents on a strict spec (first prose occurrence
    only; skip code/headings; link-only when already expanded). All 20 used anchors verified to
    resolve; render clean; 2 awkward label/compound spots tuned to link-only.

12. ✅ **Currency sweep after the automated-EPG arc (2026-07-02)** — the arc (agon_evolution /
    agon_llm / metalearning / three membranes / live_runner / wikidata_source; live runs 1–2
    executed) landed *after* the book's chapters were consolidated, so a staleness sweep
    (subagent scan over all 30 chapters) found and fixed: **CAPABILITY_MAP** re-consolidated
    (new **§H — the automated Endoporeutic Game** table; modal/audit/citation + reference-node
    rows added; EGIF quote-aware-`#` and ELK bbox-quick-reject notes); **VISION_AND_SCOPE**
    (in-scope gains the automated game; the stale "automated Grapheus + dynamic-M deferred"
    entry replaced by the real open item, tropism); **ENDOPOREUTIC_GAME_GUIDE** (the 2026-06-11
    Frontier list re-marked shipped-vs-open; the ontology-import banner; module map + arena
    section point at autonomous play); **DOMAIN_ORACLE_AND_M** (steps 2/3/6 annotated DONE /
    realized-differently); **NL_TO_LOGIC** (the proposer is now one of three LLM seats);
    **GENERATION_AND_TESTING** (the testing register runs autonomously; grammar unchanged);
    **EXTERNAL_SOURCES_AND_IMPORT** (**family C — live sources**, doorway = the game itself);
    **GLOSSARY** (membrane's open/closed senses + new entries: disposition, disuse-decay,
    stickiness, poise, tropism). Triage table gains the two arc design-of-record docs as DEV
    (`_devlinks.lua` already routes them to GitHub — no manifest change).

### ▶ Remaining

- **Book-voice (deeper pass)** — the chapters still carry doc-style front-matter (`> What this is /
  Read this first / Companion documents`, `Last consolidated:` footers, `Status/Reviewed` lines) that
  read as standalone-doc chrome in a linear book. They remain *useful in-repo*, so the call is whether
  to (a) leave them (they render fine and links resolve), (b) strip them only in the book via a Lua
  filter, or (c) edit per-doc. **Author decision.** Also: trim FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION's
  feature/reconciliation framing toward a usage chapter.
- ~~**PDF size**~~ — done: `ARISBE_CORE_API_REFERENCE` is HTML-only in the book
  (`.content-visible when-format="html"`), PDF 504 → ~314 pp.
- **Keep `_devlinks.lua`'s BOOK set in sync** with `_quarto.yml` chapters when chapters change.
- **Move DEV/ARCHIVE/RETIRE docs** to a physical `docs/dev/` (optional) and refresh `ARCHIVE_INDEX.md`.
- **CI** (optional) — render the book on push; publish the site.

> Quarto note: installed locally (now on PATH at `/usr/local/bin/quarto`) with TinyTeX
> (`quarto install tinytex`) for the PDF. Render with `quarto render docs`; preview with
> `quarto preview docs`.
