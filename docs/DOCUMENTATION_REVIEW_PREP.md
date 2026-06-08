# Documentation Review — Preparation

**Prepared:** 2026-06-08, as the scaffold for a *next-session* thorough review of
the documentation. This file is the plan, not the review. The aim (author's words):

> Let the documentation settle on **what truly describes the fundamental arc we
> have constructed — from Peirce's vision (with the aid of Dau, Roberts, Sowa,
> Pietarinen, …) to our Arisbe** — consolidating and clarifying with reference to
> the *particular literature resources and examples we have in hand* and the *real
> implementation we have built*. We are far from finished; the end game — the
> **Endoporeutic Game** — remains to complete. But we can consolidate and clarify
> now.

Substantial legacy, possibly erroneous or obsolete description and developmental
decision-making is expected to be found and either corrected, merged, or retired.

---

## 1. The fundamental arc (the target spine)

The review should measure every document against a single coherent narrative. A
proposed spine (to be refined in the session):

1. **Peirce's vision — logic in pictures, not pictures of logic.** The diagram is
   the reasoning, not an illustration of it. Iconicity: the perceptual reading of
   the picture (inside/outside a closed line, tracing a connection) *is* the
   inference. The **Endoporeutic** (dialogical, game-theoretic) reading is Peirce's
   own semantics — and Arisbe's end game.
   *Sources:* Roberts, *The Existential Graphs of C. S. Peirce*; Pietarinen,
   *Signs of Logic* + Bellucci & Pietarinen analyses; Peirce CP (rules of
   inference, conventions). In hand: `docs/references/Existential Graphs of
   Peirce.pdf`, `Signs_of_Logic.pdf`, `Peirce_Rules_of_Inference.pdf`,
   `Egpeirce Documentation.pdf`.

2. **The correspondence problem (the central engineering + research problem).**
   Inerrant correspondence between an EG's linear written form and its graphical
   drawn form — picture and proposition denoting the same object across every
   transformation, regeneration, edit, round-trip.
   *Doc:* `LINEAR_GRAPHICAL_CORRESPONDENCE.md` (the contract). Recently sharpened:
   the **drawn mark is its logical sign**; the **drawn shape is authoritative for
   containment**; **argument order** is drawn (Dau numbered / Peirce clockwise).

3. **The guarantor and the scholarship.** Dau's formalization is the mathematical
   bedrock (the `RelationalGraphWithCuts` `(V,E,ν,>,Cut,area)`, the six rules,
   soundness) guaranteeing correctness; Sowa supplies the conceptual-graph bridge
   and the linear forms (EGIF/CGIF, Common Logic); Roberts/Pietarinen supply the
   historical-systematic reading and the drawing conventions.
   *In hand:* `mathematical_logic_with_diagrams.pdf` (Dau), `EGIF-Sowa.pdf`,
   `eg2cg.pdf`, `Common_Logic_final.pdf`. All have `docs/derived/*_extracted.txt`.

4. **Arisbe's construction — three co-equal expressions of one EG.** The EG (the
   thought) is the foundation; the **linear form, the drawn form, and the EGI** are
   three co-equal expressions of it, none privileged. Methods connect them:
   linear↔EGI (parsers/generators), EGI→drawn (layout + render as *projection*),
   drawn→EG (the new `eg_reader`). Correspondence = the three denote one EG.

5. **Regimes, gates, and the chain of semiosis.** The invariant is scoped — three
   regimes (composition / asserted / presentation-only); three gates
   (integrity / context / truth); every rule application is an attestation event.
   *Docs:* `CHAIN_OF_SEMIOSIS.md`, `MANIFEST_AND_MEANING.md`,
   `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`, `DAG_HISTORY_ARCHITECTURE.md`.

6. **The three modes and the end game.** Organon (archive), Ergasterion
   (workshop), Agon (the **Endoporeutic Game** — dialogical contest where a graph
   earns the corpus). The end game is *not finished* — the review should mark the
   boundary between what is built and what the game still needs.
   *Docs:* `ENDOPOREUTIC_GAME_GUIDE.md` (1965 lines — review heavily; separate
   the implemented engine from the aspirational design), `arisbe_triad_*`.

**Examples in hand:** the `tomos/` corpus (87+ canonical EGs with EGIF/CGIF/CLIF/
FOPL variants), and the harvested examples under `tomos_backups/…harvest_*`. The
review should tie claims to *named* corpus examples (e.g. `dau_theorem_proving`,
`theorem_praeclarum`, `ternary_relation_challenge`) rather than abstractions.

---

## 2. Documentation inventory & first-pass triage

Status legend: **CANON** (the spine; keep, light revise) · **SPEC** (feature/
subsystem; verify vs implementation) · **REF** (reference/auto-gen; regenerate) ·
**REVIEW** (overlap/age/likely-stale — decide keep/merge/retire) · **DEDUPE**.

### Spine / vision
| Doc | Status | Note |
|---|---|---|
| `LINEAR_GRAPHICAL_CORRESPONDENCE.md` | CANON | Central contract; just revised (L6/L7/R8). Anchor of the arc. |
| `CHAIN_OF_SEMIOSIS.md` | CANON | Peircean grounding; current. |
| `MANIFEST_AND_MEANING.md` | CANON | Philosophical floor; current. |
| `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` | CANON | Core paradigm (750 lines) — check for pre-web/aspirational drift. |
| `PRODUCT_VISION.md` (docs/) | CANON | Vision. **DEDUPE:** identical md5 to top-level `PRODUCT_VISION.md` — keep one. |
| `PRODUCT_VISION.md` (top-level) | DEDUPE | Exact duplicate of `docs/PRODUCT_VISION.md`. |
| `README.md` | CANON | Front door; verify currency. |

### Specs / subsystems (verify against the real implementation)
| Doc | Status | Note |
|---|---|---|
| `TENSION_LAYOUT.md` | SPEC | Current (§9–§11). Has layered "PoC" sections — fold PoC into "as-built" where shipped. |
| `PRESENTATION_DELTAS_AND_STYLE.md` | SPEC | The projection ladder; current. |
| `TRANSFORMATION_WORKFLOW_SPEC.md` | SPEC | Four-beat grammar; current. |
| `ELK_LAYOUT_IMPLEMENTATION_SUMMARY.md` | SPEC | Verify vs `elk_layout_engine.py`. |
| `PROOF_SERIALIZER.md` | SPEC | Verify vs chain persistence. |
| `DAG_HISTORY_ARCHITECTURE.md` | SPEC | Verify vs `egi_transformation_history`. |
| `IMPORT_EXPORT_FORMATS.md` | SPEC | Verify vs parsers/generators + `/import`. |
| `ARISBE_EXISTENTIAL_GRAPH_DEFINITION.md` | SPEC | The formal object; reconcile with Dau §-level definitions. |
| `DAU_SEMANTIC_EVALUATION_GUIDE.md` | SPEC | Verify vs `z3_semantic_validator`. |
| `ENDOPOREUTIC_GAME_GUIDE.md` | REVIEW | 1965 lines — the end game. Separate implemented engine (Agon) from aspiration; this is the unfinished frontier. |
| `SPROTTY_EVALUATION.md` | SPEC | Decision record (borrow, don't adopt); keep. |

### Reference / generated
| Doc | Status | Note |
|---|---|---|
| `ARISBE_CORE_API_REFERENCE.md` | REF | Auto-generated (`tools/extract_core_api.py`); regenerate at review end. |
| `CORE_API_USAGE_GUIDE.md` | REF | Patterns; verify examples still run. |
| `ARCHIVE_INDEX.md` | REF | Index of `docs/archived/`; keep, update. |
| `RETURN_TO_DEVELOPMENT.md` | REF | 5-min recovery; update to current state. |

### Likely legacy / overlap (decide: merge, update, or retire to `docs/archived/`)
| Doc | Status | Note |
|---|---|---|
| `WEB_VIEWER_IMPLEMENTATION_PLAN.md` | REVIEW | 1227 lines, a *plan* (Apr) now largely built — convert to "as-built" or retire. |
| `ARCHITECTURE_STYLE_SYSTEM.md` | REVIEW | Dec 2025; **contains Qt/legacy-GUI markers**. Merge with ↓. |
| `STYLE_SYSTEM_GUIDE.md` | REVIEW | Sept 2025; overlaps the above + `docs/styles/`. One canonical style doc. |
| `arisbe_triad_architecture.md` | REVIEW | Mar; **Qt markers**; reconcile with the live three-modes (Organon/Ergasterion/Agon). |
| `UOD_DEVELOPER_GUIDE.md` | REVIEW | Mar (734 lines); overlaps `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` — reconcile. |
| `ARISBE_IN_PRACTICE.md` | REVIEW | Mar; verify against current modes/flows. |
| `FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md` | REVIEW | Mar; fold into the scholarship section / styles. |
| `CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md` | REVIEW | Sept 2025; verify vs `chapter18_fopl_translation.py`. |
| `DAU_THEOREM_CORRESPONDENCE_DOCUMENTATION.md` | REVIEW | Sept 2025; verify vs current correspondence story (may predate §3.3). |
| `AI_CONDUCT_GUIDELINES.md` (top) | REVIEW | Oct 2025 meta; reconcile with `AGENTS.md`/`CLAUDE.md`. |
| `docs/coherence/egi_ligature_position_cooptimization_spec.md` | REVIEW | Stray spec; place or retire. |

### Developer/meta (keep; maintenance)
`AGENTS.md`, `CLAUDE.md`, `CURRENT_PLAN.md` (the running log — 1317 lines; consider
rolling older sessions into an archive at review time).

---

## 3. Known errors / legacy patterns to hunt

- **Superseded claims now corrected elsewhere** — e.g. "argument order is not
  visually distinguishable" (the old R8) was wrong; "containment is the cut's
  bounding box" (pre shape-aware §3.3). Grep for the same mistaken framings lurking
  in other docs.
- **Pre-web GUI references** — Qt / `gui_clean` / `unified_d3` / `arisbe.py` as if
  live (the Qt GUI was archived May 2026). Confirmed in `ARCHITECTURE_STYLE_SYSTEM.md`
  and `arisbe_triad_architecture.md`; sweep the rest.
- **"PLAN" docs that are now built** — present them as as-built or retire (don't
  leave a plan masquerading as the spec).
- **Duplication** — the two `PRODUCT_VISION.md`; the two style docs; the two UoD
  docs. One canonical home each.
- **Unsourced assertions** — wherever a doc asserts a Peirce/Dau convention, tie it
  to the literature in `docs/references/` (we did this for clockwise/numbered
  order; do it for the rest). The `docs/derived/*_extracted.txt` make the PDFs
  greppable.
- **Implementation drift** — a spec that names a function/flag/module that has
  since moved or been renamed (verify against `src/`).

## 4. Proposed process for the review session

1. **Fix the spine first.** Confirm/refine §1 here, then make
   `LINEAR_GRAPHICAL_CORRESPONDENCE.md` + `CHAIN_OF_SEMIOSIS.md` +
   `MANIFEST_AND_MEANING.md` + the (deduped) `PRODUCT_VISION.md` the agreed
   backbone, each opening by locating itself on the arc.
2. **Triage outward.** Walk the table §2 doc-by-doc: keep / revise / merge /
   retire-to-archived. Move retired docs to `docs/archived/` and note them in
   `ARCHIVE_INDEX.md` (don't delete — git history + the index).
3. **Ground in sources + examples.** For each retained doc, ensure its claims cite
   the literature (`docs/references/`) and a named `tomos/` example where apt.
4. **Verify against `src/`.** Spot-check that named modules/functions exist
   (the API reference + `grep` over `src/`).
5. **Regenerate** `ARISBE_CORE_API_REFERENCE.md`; refresh `RETURN_TO_DEVELOPMENT.md`
   and `ARCHIVE_INDEX.md`; roll old `CURRENT_PLAN.md` sessions to an archive.
6. **Leave the end game clearly marked** — `ENDOPOREUTIC_GAME_GUIDE.md` should
   state plainly what is implemented (Agon V1) vs what the game still needs, so the
   unfinished frontier is honest, not buried.

## 5. Assets in hand (for citation)

- **Literature (PDF + extracted text):** `docs/references/` — Dau
  (`mathematical_logic_with_diagrams.pdf`), Sowa (`EGIF-Sowa.pdf`, `eg2cg.pdf`),
  Common Logic (`Common_Logic_final.pdf`), Peirce/Roberts (`Existential Graphs of
  Peirce.pdf`, `Egpeirce Documentation.pdf`, `egpeirce.sty.txt`), Pietarinen
  (`Signs_of_Logic.pdf`), `Peirce_Rules_of_Inference.pdf`. Greppable extracts in
  `docs/derived/`.
- **Examples:** `tomos/` (87+ canonical EGs, all linear variants), and the
  harvested set in `tomos_backups/`.
- **The implementation:** `src/` (the protected mathematical core + the
  layout/render/reader/correspondence layer), the web app (`src/web_api`,
  `src/web_viewer`), and the test suite (~1039 passing) as the executable spec.
