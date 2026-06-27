# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Start here each session:** active work and the next-session handoff live in
> [CURRENT_PLAN.md](CURRENT_PLAN.md) (`▶ NEXT SESSION` section) — read it first.

## What This Project Is

Arisbe is an environment for **doing logic in pictures, not pictures of logic** — Charles Sanders Peirce's "moving pictures of thought" made operational. Frithjof Dau's formalization is the guarantor of correctness; that bedrock is non-negotiable. The **central engineering and research problem** the codebase exists to solve is the **inerrant correspondence between an EGI's linear written form and its graphical drawn form** — picture and proposition denoting the same mathematical object across every transformation, every layout regeneration, every user edit, every round-trip.

The fundamental entity is the **Universe of Discourse (UoD)** — a diachronic (evolving) process of logical reasoning, not a static diagram. A single EG is a synchronic snapshot within that process. The correspondence invariant is scoped to three regimes: **composition** (Ergasterion drafts, invariant suspended); **asserted/canonical** (Agon, Organon, every rule application, invariant mandatory and runtime-attested); **presentation-only** (always free, preserved by construction via the `presentation_ops` API). See [docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md) for the full contract.

## Environment & Commands

Dependencies are managed by **uv** (Python 3.12). One-time setup: `uv sync --extra dev --extra web` (the `web` extra carries FastAPI/uvicorn — the route tests and the web viewer need it; `uv sync` is exact and will prune them if you omit it). Run commands via `uv run` (no manual activation needed), or `source .venv/bin/activate` first.

```bash
# Testing
uv run pytest tests/ -q          # Full test suite (quiet)
uv run pytest tests/test_foo.py  # Single test file

# Quality assurance
uv run python tools/quality_gate_system.py         # Pre-commit checks (auto-run on commit)
uv run python tools/core_protection_system.py --report  # Check protected module status
uv run python tools/daily_quality_dashboard.py     # Overall system status

# Web viewer (canonical UI as of May 2026)
uv run uvicorn --app-dir src web_api.main:app --reload --port 8000   # API + static viewer at /
```

The Qt-based GUI (`arisbe.py`, `src/gui_clean/`) and its `unified_d3` layout
engine were archived to `archive/qt-gui-2025/` in May 2026 — see that
directory's README for context. They remain in git history if needed.

## Core Protection System

**17 modules in `src/` are protected** and cannot be modified without authorization:

```bash
touch .core_modification_authorized   # Required before modifying protected modules
python tools/core_protection_system.py --report  # Check what's protected
```

**The mathematical core test suite must always pass.** The core suite is the subset of `tests/` that covers `egi_core_dau`, `formal_transformation_rules`, `rule_interaction`, `subgraph_closure_validator`, `graph_isomorphism_engine`, and the Beta/logical proof exercises (~118 tests today). Failing core tests indicate real mathematical correctness issues, not test infrastructure problems.

## Architecture

### Three-Mode Conceptual Architecture

| Mode | Greek meaning | Role |
|------|--------------|------|
| **Organon** | "instrument" | Archive/corpus browser, timeline navigation, read-only |
| **Ergasterion** | "workshop" | Private editor, transformation practice, draft graphs |
| **Agon** | "contest" | Endoporeutic Game engine, formal validation, official record |

These are *conceptual modes*. The original Qt implementation (`src/gui_clean/`)
that mirrored them as separate windows was archived in May 2026. The current
plan is to surface them as routes within the web app (`src/web_api/`,
`src/web_viewer/`); that mapping is still ahead.

### Key `src/` Modules

- `egi_core_dau.py` — `RelationalGraphWithCuts` data model (immutable)
- `formal_transformation_rules.py` — Six Dau rules: ERA, INS, IT+, IT−, DC+, DC− (Beta-aware)
- `rule_interaction.py` — Headless RuleInteraction protocol for stepwise proof construction
- `eg_navigation.py` — Content-addressable structural selection over an EGI: name elements by what they are / where they sit (`cut_holding_relation`, `empty_cut_in`, `child_edges`, `edges_on_vertex`, `vertex_by_label`), `area_signature` (Alpha) + `same_graph` (full iso, the Beta authority), `describe` (kind/area/polarity introspection). The query half of the proof-authoring layer; area topology delegates to `presentation_ops`.
- `proof_authoring.py` — `ProofChain`: fluent builder that applies Dau rules by *locator* (`callable(egi)→id`, resolved against the current state) and records each `ChainStep` with deterministic ids/timestamps; `apply_rule` / `replay_step` are the shared engine/replay primitives. The action half — turns the dogfood friction (authoring by ephemeral id) into a readable chain. Used by `tools/build_*_chain.py`.
- `subgraph_closure_validator.py` — Closure validation (Beta-aware: free outer-area vertices)
- `universe_of_discourse.py` — UoD entity (synchronic EGI + diachronic DAG history + layout deltas)
- `egi_transformation_history.py` — DAG-based branching transformation history
- `endoporeutic_game.py` — Two-player dialogical game engine
- `elk_layout_engine.py` (+ `elk_worker.js`) — Cut-aware ELK-based layout, the default layout path; also `rebuild_ligature_anchors` (re-derive ligature endpoints from element geometry after a regime-3 move)
- `tension_layout.py` — the vertex tree as organizing principle: `sibling_order` (tension-minimizing free order of an area's siblings, the `?tension` knob) + `stress_majorize` (SMACOF). Correspondence-safe: a crossing-sequence is order-independent. See `docs/TENSION_LAYOUT.md`
- `tension_engine.py` — `TensionLayoutEngine`, an opt-in alternative projection (`?engine=tension`): hierarchical constrained stress with crossing-point proxies that places a relation *between* its arguments (Peircean single-line reading). Containment by construction; §3.3-gated with ELK fallback (17/18 corpus attest)
- `simple_svg_renderer.py` — LayoutDTO → SVG
- `layout_dto.py` — Platform-independent layout DTO shared by layout engines and renderers
- `presentation_ops.py` — Regime-3 algebra: `move_vertex`, `move_predicate`, `reshape_cut`, `move_cut` (rigid translate of a cut + contents), `reroute_ligature`, each raising `Regime3Violation` on attempted boundary crossings. Also exports the public area-topology helpers (`element_area`, `cut_parents`, `area_chain`, `crossing_sequence`, `deepest_containing_cut`). `area_chain` (allowed areas, incl. LCA) and `crossing_sequence` (ordered cuts crossed, excl. LCA) share one `_tree_path` walk — the single source of truth consumed by `natural_layout.authorized_crossings` and `ELKLayoutEngine._authorized_cuts`.
- `natural_layout.py` — Coordinate-free projection-independent layout: `NaturalLayout` (containment tree, per-ligature required crossing-sequence, incidence, ports) built by `natural_layout(egi)`. The "own the dimensionality" layer; imports no geometry so a future 3-D projection is additive. See `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` §3.1–3.2.
- `correspondence_attestation.py` — Runtime §3.3 check: `attest_correspondence(egi, dto)` raises `CorrespondenceViolation` on failure. Hooked into `web_api/services/layout_service.py` so every served (EGI, drawing) pair is verified.
- `eg_reader.py` — the **drawn→EG** reader (inverse of layout/render): `read_drawing(dto)` recovers the area tree + ordered incidence from geometry alone (inside/outside the drawn cut curves; tracing ligatures); `reading_matches_egi`, `assign_order_labels` (carry argument order with the fewest drawn numerals). De-risked on human geometry — the foundation of freeform composition.
- `drawing_validity.py` — fix-time well-formedness of a freeform drawing, in EG vocabulary: `validate_drawing(dto) → ValidityReport` (errors `overlapping_cuts` / `dangling_line`; warnings `boundary_band` / `unwired_predicate` / `label_overlap`). The twin of `correspondence_attestation` for a drawing with *no EGI yet*. See `docs/FREEFORM_COMPOSITION_AND_LEARNING.md`.
- `drawing_to_egi.py` — `build_egi_from_drawing(dto, predicate_labels, vertex_labels)`: the construction half of *fix = read* — joins recovered structure (`read_drawing`) with carried content (relation names, constants) into a real EGI. Corpus round-trip via `same_graph`.
- `egi_diff.py` — `legible_diff(target, attempt) → DiffReport`: the discrepancy report (the *how-they-differ* to `same_graph`'s yes/no), in EG terms — `structure`/`missing`/`extra`/`scope`/`incidence`/`order`. Content-aligned, not id-aligned (constants by label, relations by name + arg signature, generic lines by incidence). Powers challenge mode.
- `challenge_mode.py` — Freeform step 4: a curated `CHALLENGE_BANK` difficulty gradient + `grade(target, attempt) → DiffReport` (`same_graph` + the legible diff). Correspondence learned by doing — draw a target freehand, get graded in EG vocabulary.
- **The Agon interpretation register** (`docs/GENERATION_AND_TESTING.md`, `docs/DOMAIN_ORACLE_AND_M.md`) — the inning *given M, then G*: choose M → peel → decide. The conceptual cut is **eliminative (the game = Agon/testing) vs additive (making = Ergasterion)**; deduction earns the corpus through Agon (self-certifies validity, not warrant).
  - `domain_oracle.py` — M is **queried, not held**: a thin `DomainOracle` (`resolve` / `witness` / `match_atoms` / `individuals`), backed by `CorpusOracle` over local EGIs. "Enough" of M = what the proposal touches (vocabulary-bounded + open-world horizon).
  - `semantic_game.py` — `evaluate(egi, oracle)` reads G **outside-in** (the peel), asking the oracle at each negation-free layer; returns three-valued Kleene `Verdict3` (TRUE/FALSE/UNKNOWN, sound open-world) + transcript + structured `winning_witness` / `counterexample`. Model-checking, **not** inference; truth-in-a-model, **not** validity.
  - `model_materialization.py` — `materialize_egi(egi) → (facts_egi, report)`: forward-chain M's **Horn fragment** (`~[ B ~[ H ] ]`, range-restricted) to the least Herbrand model so a model authored as *facts + rules* is testable (the syllogism works); non-Horn shapes left to the contest game with an honest skip-report. **A model is the facts; rules are a theory.**
  - `theory_query.py` — `entails(theory, query)`: is the universal G a **theorem of the theory M**? The deduction step *ontology-as-M* needs — model-checking a subsumption over a pure T-box (SUMO, no individuals) reads *vacuously* TRUE/UNKNOWN, so decide it by **freeze-a-fresh-witness** (assert G's body over arbitrary constants → materialize M over them → check the head). Sound (witnesses arbitrary) + Horn-complete; a negative is FALSE only when M is wholly Horn, else UNKNOWN (skipped non-Horn axioms might bear). Wired into `/agon/interpret` as a `theorem` block beside the extensional verdict. See `docs/DOMAIN_ORACLE_AND_M.md` §6.2.
  - `agon_models.py` — curated reference-model scenarios (the persona innings) for the `/agon` model picker; corpus UoDs are the other source. The **inverse pivot** (`/agon/where-it-holds`) ranges the peel across these to answer "in what domain does G hold?" — holds / partial (residue = contribution) / independent / contradicts.
- `tomos_service.py` — Unified corpus API. `save_uod` / `load_uod` attest §3.3 at the save/load boundary. `save_uod_with_chain(uod, chain)` + `load_chain(uod_id)` persist a workshop chain (V1 linear) as `history/chain.jsonl` + `history/states/<id>.egi.json` alongside the UoD record; §3.3 fires inside `save_uod` before any chain files are written, so a refusal aborts cleanly with no half-saved chain on disk. `TransformationChain` / `ChainStep` are the slim on-disk shape (NOT a hydration of the protected `EGITransformationHistory`).
- `z3_semantic_validator.py` — Z3 SMT-solver semantic validation
- `graph_isomorphism_engine.py` — NetworkX VF2 matching for goal detection
- `web_api/` (FastAPI) + `web_viewer/` (static HTML/JS) — the canonical user interface. All three mode routes are live: `/organon` (read-only archive, both load+render boundaries §3.3-attested), `/ergasterion` (workshop / composition — regime-1 drafts; a session holds a forest of branches with move-by-move navigation; output goes to a regime-1 **scratch** store or is **sent to Agon**, never straight to the corpus — there is no direct workshop→corpus route. Composition is **freeform draw-then-read** (`web_viewer/js/freeform-canvas.js`): typed marks placed/dragged/erased on a free canvas with no live EGI, read into a sign only at gate ① via `read-drawing` (preview) / `fix-drawing` (commit) — backed by `drawing_validity` + `drawing_to_egi`. A **Graph↔Argument** two-mode switch makes fixed/unfixed unmistakable and enforces "no rules on an unfixed graph; no meaning-change on a fixed one"; "Edit base graph" re-opens a fixed/corpus graph as an independent copy via `state-drawing` seeding; **challenge mode** — pick a target linear form, draw it freehand, get graded with `same_graph` + the legible diff), `/agon` (Endoporeutic Game arena — the **contest** register is the hot-seat transformation game; the **interpretation register** is the inning *given M, then G*: choose a reference model M (the picker lists curated scenarios + corpus UoDs, optionally **materialized**), `/agon/interpret` peels G against it → verdict + transcript + witness/counterexample, `/agon/where-it-holds` runs the inverse pivot, and the Agonothetes' disposition taxonomy is annotated by the verdict). The mode contract: a graph reaches the attested corpus only by being tested through Agon or as a style-only reprojection of an attested graph (§3.3 attests *correspondence, not truth*). A shared left-column nav (`web_viewer/js/mode-nav.js`) links the three modes + home. Rendering is one engine end to end: server-side EGI→SVG (`layout_service` + `simple_svg_renderer`, §3.3-attested) and client-side **`web_viewer/js/diagram-viewer.js`** (`DiagramViewer.render(svg, {camera:'fit'|'hold', dolly, transition})`) — the single pan/zoom/camera component all three modes use.

### Linear Format Support (all production, round-trip tested)

| Format | Module | Corpus tested |
|--------|--------|--------------|
| EGIF | `egif_parser_dau.py` / `egif_generator_dau.py` | 57+ examples |
| CGIF (ISO/IEC) | `cgif_parser_dau.py` / `cgif_generator_dau.py` | 40+ examples |
| CLIF (Common Logic) | `clif_parser_dau.py` / `clif_generator_dau.py` | 35+ examples |
| FOPL | `chapter18_fopl_translation.py` | Φ/Ψ bidirectional |
| JSON | `egi_io.py` | With layout deltas |

### Data Model Invariants

- **EGI is immutable**: use `.with_vertex()`, `.with_edge()` — never `.add_*()`
- **Import pattern**: `from module_name import Foo` (not `from src.module_name`)
- **UoD state**: `State_n = (EGI_n, LayoutDeltas_n)` — deltas persist through transformations

### Beta Graph Support (FOL)

- **Beta graphs** use shared vertices across cut boundaries (lines of identity)
- EGIF: `*x` = defining label (new vertex), `x` = bound label (existing vertex in enclosing scope)
- `~[ (P *x) ~[ (Q x) ] ]` = ∀x(P(x) → Q(x)) — one shared vertex
- `SubgraphClosureValidator` with `context_area` treats ancestor-area vertices as free
- `IterationRule` extends lines of identity (reuses source-area vertices, no copy)
- `RuleInteraction` protocol: `begin_interaction` → `advance_interaction` → `apply_interaction`

## API Discovery

**Never guess function signatures.** The complete API is documented in
`docs/ARISBE_CORE_API_REFERENCE.md` (regenerated from
`tools/core_protection_system.py`'s protected-modules set):

```bash
grep -i "function_name" docs/ARISBE_CORE_API_REFERENCE.md
cat docs/CORE_API_USAGE_GUIDE.md          # Common development patterns
uv run python tools/extract_core_api.py   # Regenerate the reference
```

Before starting any implementation task, check whether a solution already exists:
```bash
python tools/context_awareness_system.py --check "task description"
```

## Key Documentation

- `AGENTS.md` — Developer guidelines with code patterns and usage examples
- `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` — **The central contract.** Read before touching anything that produces or consumes (EGI, LayoutDTO) pairs (transformation rules, layout, rendering, sessions, the three modes, the Endoporeutic Game).
- `docs/CHAIN_OF_SEMIOSIS.md` — **The Peircean grounding.** Why a reasoning episode is a chain of sound, attested sign-transitions; why every rule application is an attestation event; how Arisbe's provenance/immutability model relates to Git/Datomic/wikis and where it departs (the sound-step requirement). Read for the *purpose* behind the chain model, the regimes, and the Ergasterion promotion boundary.
- `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` — Core paradigm (read before touching UoD/history)
- `docs/DAG_HISTORY_ARCHITECTURE.md` — Branching transformation history
- `docs/ARISBE_CORE_API_REFERENCE.md` — Auto-generated API reference
- `docs/RETURN_TO_DEVELOPMENT.md` — 5-minute context recovery for the returning author
- `tomos/` — 87+ canonical EG examples with EGIF/CGIF/CLIF/FOPL variants

## Mathematical Foundation

Code chapters correspond to Dau's formal textbook:
- Ch. 14/15 → `formal_transformation_rules.py` (six transformation rules, Beta-aware)
- Ch. 14/15 → `rule_interaction.py` (headless stepwise protocol for all rules)
- Ch. 16–17 → `ligature_manipulation_rules.py`, `chapter17_soundness_evaluation.py`
- Ch. 18 → `chapter18_fopl_translation.py` (linear format Φ/Ψ translations)
- Ch. 20 → `syntactic_equivalence_checker.py`, `chapter20_syntactic_equivalence_fixes.py`

## Testing (~1000 passing, 35 skipped)

Key test files:
- `test_correspondence_invariant.py` — All six §7 test shapes from `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` (totality/injectivity, containment, incidence + arg-order, identity 3-way, transformation invariance, regime-3 non-interference) against the tomos corpus
- `test_correspondence_attestation.py` — Module contract: corpus-wide happy path plus adversarial unit tests confirming each §3.3 property's failure raises `CorrespondenceViolation`
- `test_presentation_ops.py` — Regime-3 API contract: happy + refusal paths for `move_vertex` / `move_predicate` / `reshape_cut` / `move_cut` / `reroute_ligature`
- `test_layout_service_attestation.py` — The web boundary hook fires on a real UoD and refuses when the engine returns a corrupted DTO
- `test_chain_persistence.py` — Transformation-chain JSONL round-trip; §3.3 refusal at save_uod_with_chain leaves no chain files on disk
- `test_ergasterion_routes.py` — Workshop route contract: session lifecycle, RuleInteraction-driven apply, regime-1 drafts don't fire corpus-record §3.3, move-by-move navigation (a UoD's worked sequence hydrates + any state renders), branch-on-edit (apply from an earlier state forks; branches switchable), scratch store (save/list/open/delete; never the corpus). (Direct workshop→corpus promotion was retired; its §3.3 mechanism lives in `test_chain_persistence.py`.)
- `test_eg_reader.py` — drawn→EG round trips (`read(render(egi)) == egi`) corpus-wide, both engines/styles + full argument order; `TestFreeformRobustness` pins the reader on *human* geometry (the freeform de-risk)
- `test_drawing_validity.py` — fix-time validity pass: each error/warning + clean engine layouts raise zero errors
- `test_drawing_to_egi.py` — drawing→EGI builder: corpus round-trip via `same_graph` (both styles, nested cuts, argument order, constant-vs-generic)
- `test_ergasterion_freeform.py` — freeform routes: `read-drawing`/`fix-drawing` round-trip to `same_graph`, ill-formed refusal, JS-serialize↔backend contract, `state-drawing` seeding, editable corpus copies
- `test_ergasterion_freeform_e2e.py` — headless-Chromium E2E (Playwright): draw→read→fix, the Graph↔Argument round-trip, corpus edit-base consistency, spot snapping (skipped if Playwright/Chromium absent)
- `test_egi_diff.py` — legible diff: same-graph→no findings; missing/extra/scope/incidence/order findings
- `test_challenge_mode.py` / `test_ergasterion_challenge.py` — challenge mode (freeform step 4): the difficulty gradient parses, grading passes a same-graph attempt regardless of surface form and fails wrong ones with the right finding; routes grade a freehand drawing (ill-formed ink → validity feedback, non-mutating)
- `test_domain_oracle.py` — the `DomainOracle` contract: `resolve` CONFIRMED/UNKNOWN/DENIED (open vs closed), constants by label, arg-order via `nu`, provenance, cut refusal; `match_atoms` enumerates all bindings
- `test_semantic_game.py` — the peel: ground atoms, negation, the scroll/universal open-vs-closed, existential witness selection; structured `winning_witness` / `counterexample` (the student's Whale, the physician's Biscuit)
- `test_model_materialization.py` — Horn forward-chaining (syllogism, chained rules, recursive transitive closure, binary join) to the least Herbrand model; non-Horn shapes skipped with the right reason
- `test_theory_query.py` — theory query / freeze-a-witness (`entails`): applicability (only a range-restricted Horn universal), direct + transitive subsumption TRUE, underivable FALSE (wholly Horn) vs UNKNOWN (non-Horn residue), multi-var typing rule, conjunctive head; the real corpus ontologies (SUMO subsumption theorems, Porphyry ladder + disjointness residue, FOAF typing chains through subsumption)
- `test_owl_import.py` — the OWL→CLIF→EGI pipeline (`tools/owl_to_clif` + `domain_model_importer.from_owl_*`): each OWL 2 functional-syntax axiom form → its Common-Logic shape (subsumption / equivalent / disjoint / sub-property / domain-range / inverse / symmetric / transitive / intersection body / someValuesFrom head / assertions / sameAs); untranslatable constructs (cardinality, union, annotation, ⊑Thing) reported not dropped; IRI/prefix → local name; the `zoo.ofn` fixture imports to an EGI; the loop closes — an OWL-imported ontology decides subsumption / intersection / transitivity theorems via `theory_query.entails`
- `test_agon_interpretation.py` — the interpretation register routes: the five persona innings reproduce their verdicts; `set-model`; verdict-annotated dispositions (full taxonomy, nothing auto-asserts); materialize makes the syllogism hold; the inverse pivot ranks domains (holds/partial/independent/contradicts) with the residue
- `test_organon_routes.py` — Archive route contract: corpus listing, UoD detail, both load+render attestation hooks fire per detail request
- `test_epg_exemplar_scripts.py` — 16 Endoporeutic Game scenarios (outcomes, strategies, engine integration)
- `test_beta_proof_exercises.py` — 20 Beta graph tests (FOL, shared vertices, EGIF round-trips)
- `test_logical_proof_exercises.py` — Propositional tautology derivations (modus ponens, etc.)
- `test_rule_interaction.py` — Headless RuleInteraction protocol integration tests
- `test_subgraph_closure_validation.py` — Closure validator including Beta-aware checks
- `test_graph_isomorphism_engine.py` — VF2 isomorphism for IT- validation
- `test_tomos_parsing.py` — EGIF/CGIF/CLIF round-trip across 87+ tomos examples
