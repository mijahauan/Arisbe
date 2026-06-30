# Arisbe — Capability & Maturity Map

> **What this is.** A single living table of *what Arisbe can do*, its maturity, where it lives in the
> code, and what test guards it. It replaces reading the `CURRENT_PLAN.md` session-log palimpsest to
> answer "what actually works." Update the relevant row when a capability ships or changes status.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [ROADMAP.md](ROADMAP.md) ·
> [GLOSSARY.md](GLOSSARY.md). Developer module map: [../CLAUDE.md](../CLAUDE.md).
>
> *Last consolidated: 2026-06-27.*

**Status legend**
- **SHIPPED** — working, with a passing test home.
- **PARTIAL** — built and useful, but a frontier/edge case is documented as open.
- **DESIGNED** — specified in docs, not yet built.
- **OUT** — explicitly not being built (with a reason; see [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §5).

> *Status is conservative: "SHIPPED" only where a passing test exists. Where CLAUDE.md and the code
> disagreed during consolidation, the code won.*

---

## A. Core data model & logic — *the bedrock*

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| EGI data model (`RelationalGraphWithCuts`) | SHIPPED | `egi_core_dau.py` → `test_egi_core_comprehensive.py` | Dau's `(V,E,ν,⊤,Cut,area,ρ)`; immutable. |
| Immutability / construction API | SHIPPED | `egi_core_dau.py` → same | `.with_vertex()`, `.with_edge()`; never `.add_*()`. |
| Six transformation rules (ERA, INS, IT±, DC±) | SHIPPED | `formal_transformation_rules.py` → `test_chapter15_formal_calculus.py`, `test_beta_proof_exercises.py` | Beta-aware; Dau Ch. 14/15. |
| Headless rule-interaction protocol | SHIPPED | `rule_interaction.py` → `test_rule_interaction.py` | Stepwise `begin→advance→apply` for all six. |
| Beta / FOL (lines of identity, shared vertices) | SHIPPED | `egi_core_dau.py`, `formal_transformation_rules.py` → `test_beta_proof_exercises.py` | Defining vs bound labels; ancestor-area vertices free. |
| Closure validation (Beta-aware) | SHIPPED | `subgraph_closure_validator.py` → `test_subgraph_closure_validation.py` | Free outer-area vertices. |
| Graph isomorphism (VF2, for IT−) | SHIPPED | `graph_isomorphism_engine.py` → `test_graph_isomorphism_engine.py` | NetworkX VF2 copy detection. |
| Ligature manipulation (Ch. 16–17) | SHIPPED | `ligature_manipulation_rules.py`, `single_object_ligature_detector.py` → `test_chapter16_17_ligature_soundness_simplified.py` | Sole non-test consumer is `chapter17_soundness_evaluation.py` — thinly held. |
| Syntactic equivalence (Ch. 20) | SHIPPED | `syntactic_equivalence_checker.py`, `chapter20_syntactic_equivalence_fixes.py` → `test_chapter20_syntactic_equivalence.py` | |
| EG navigation / introspection | SHIPPED | `eg_navigation.py` → `test_introspection_and_rules.py` | Content-addressable selection; `same_graph` Beta authority. |
| Proof authoring chains (`ProofChain`/`ChainStep`) | SHIPPED | `proof_authoring.py` → `test_chain_persistence.py`, `test_branching_chain.py` | Rule-by-locator; deterministic replay. |

---

## B. Linear formats — *all production, round-trip tested*

| Capability | Status | Home (src → test) | Corpus |
|---|---|---|---|
| EGIF parse / generate | SHIPPED | `egif_parser_dau.py` / `egif_generator_dau.py` → `test_tomos_parsing.py` | 57+ |
| CGIF parse / generate (ISO/IEC) | SHIPPED | `cgif_parser_dau.py` / `cgif_generator_dau.py` → `test_tomos_parsing.py` | 40+ |
| CLIF parse / generate (Common Logic) | SHIPPED | `clif_parser_dau.py` / `clif_generator_dau.py` → `test_clif_unit.py`, `test_tomos_parsing.py` | 35+ |
| FOPL translation (Φ/Ψ bidirectional) | SHIPPED | `chapter18_fopl_translation.py` → `test_egi_to_fol.py` | EGI ↔ FOL |
| EGI→FOL bridge (read-only inverse) | SHIPPED | `egi_to_fol.py` → `test_egi_to_fol.py` | Faithfulness pinned by Z3. |
| JSON I/O (with layout deltas) | SHIPPED | `egi_io.py` → `test_complete_serialization_simplified.py` | Deltas survive transforms. |

---

## C. Correspondence machinery — *the central problem, operational*

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Coordinate-free natural layout | SHIPPED | `natural_layout.py` → `test_natural_layout.py` | Containment + crossing-sequences + incidence; geometry-free. |
| §3.3 runtime attestation | SHIPPED | `correspondence_attestation.py` → `test_correspondence_attestation.py`, `test_correspondence_invariant.py` | `attest_correspondence` hooked into layout_service + save/load. **Protected (added 2026-06-27).** |
| Regime-3 presentation algebra | SHIPPED | `presentation_ops.py` → `test_presentation_ops.py` | move/reshape/reroute; `Regime3Violation` on boundary crossing. **Protected (added 2026-06-27).** |
| ELK layout engine (default) | SHIPPED | `elk_layout_engine.py` (+`elk_worker.js`) → `test_elk_layout_engine.py`, `test_elk_ligature_edge_cases.py` | Cut-aware; ligature edge cases audited. |
| Tension layout engine (opt-in) | PARTIAL | `tension_engine.py` → `test_tension_engine.py` | `?engine=tension`; 17/18 corpus attest, §3.3-gated with ELK fallback. |
| Tension sibling-order + stress | SHIPPED | `tension_layout.py` → `test_tension_layout.py` | `?tension` knob; crossing-sequence-independent. |
| SVG renderer | SHIPPED | `simple_svg_renderer.py` → `test_overview_attestation.py` | LayoutDTO → SVG; one engine across all modes. |
| Drawn→EG reader | SHIPPED | `eg_reader.py` → `test_eg_reader.py` | `read(render(egi))==egi` corpus-wide + human geometry. |
| Fix-time drawing validity | SHIPPED | `drawing_validity.py` → `test_drawing_validity.py` | Errors/warnings on a drawing with no EGI yet. |
| Drawing→EGI builder | SHIPPED | `drawing_to_egi.py` → `test_drawing_to_egi.py` | "fix = read"; corpus round-trip via `same_graph`. |
| Legible EGI diff | SHIPPED | `egi_diff.py` → `test_egi_diff.py` | structure/missing/extra/scope/incidence/order, content-aligned. |
| TikZ / export rendering (geometric) | SHIPPED | `web_api/services/tikz_export.py`, `export_service.py` | Dau/Sowa coordinate TikZ; `/export` formats EGIF / CGIF / CLIF / SVG / TikZ / PNG / PDF. |
| Authentic-Peirce LaTeX export | SHIPPED (phase 1+2) | `peirce_latex.py` + `tex/arisbe-eg.sty` → `test_peirce_latex.py` | `peirce-tikz` format: oval cuts, heavy lines of identity, hooks; pure TikZ, pdflatex-native (no PSTricks); wedded to the §3.3-attested DTO; delta-faithful (regime-3 nudges thread through `/export`). Phase 2: **iconic self-continuing scroll glyph** (opt-in `scroll_glyph`, ink-only), **worked-chain → multi-figure LaTeX document** (`export_peirce_chain`, `POST /export/chain`), **drawing→EGI learning loop** (`layout_learning.py`: `arrangement_deltas` + `generalize_arrangement` → style ladder). |

---

## D. Diachronic / provenance

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Universe of Discourse entity | SHIPPED | `universe_of_discourse.py` → `test_universe_of_discourse.py` | Synchronic EGI + diachronic DAG + deltas. |
| Branching transformation history | SHIPPED | `egi_transformation_history.py` → `test_egi_transformation_history.py` | Immutable states; append-only DAG. |
| Corpus persistence (`TomosService`) | SHIPPED | `tomos_service.py` → `test_chain_persistence.py` | save/load attest §3.3 at the boundary; chain JSONL. |
| Provenance + warrant / standing | SHIPPED | `provenance.py` → `test_provenance.py` | `standing_of` → posited/derived/withstood badge. |
| Presentation deltas + style ladder | SHIPPED | `presentation_deltas.py`, `style_loader.py`, `style_specification.py` → `test_presentation_deltas.py`, `test_styles.py` | Sparse regime-3 exemplars; extrapolation. |
| Liveness / desuetude | SHIPPED | `liveness.py` → `test_liveness.py` | Reversible retire/revive. |
| Annotations | SHIPPED | `annotations.py` → `test_annotations.py` | Persistent element metadata. |
| Proof serializer | SHIPPED | `proof_serializer.py` → `test_proof_serializer.py` | Chain JSON/JSONL replay schema. |

---

## E. The three web modes

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| **Organon** — read-only archive | SHIPPED | `web_api/routes/organon.py` → `test_organon_routes.py`, `test_overview_routes.py` | Listing, UoD detail, chain player; both load+render §3.3-attested. |
| Adaptive-scope lenses (overview) | SHIPPED | `overview_projection.py`, `eg_structure.py` → `test_overview_attestation.py` | Negation well + storyboard; LOD knob. |
| **Ergasterion** — workshop | SHIPPED | `web_api/routes/ergasterion.py` → `test_ergasterion_routes.py` | RuleInteraction-driven; regime-1 drafts; branch-on-edit; scratch store. |
| Freeform draw-then-read | SHIPPED | `web_viewer/js/freeform-canvas.js`, `drawing_*`→ `test_ergasterion_freeform.py`, `…_e2e.py` | Typed marks → gate ① read/fix. E2E (Playwright). |
| Graph↔Argument lock | SHIPPED | `web_api/routes/ergasterion.py` → `test_ergasterion_freeform.py` | No rules on unfixed; no meaning-change on fixed. |
| Challenge mode | SHIPPED | `challenge_mode.py` → `test_challenge_mode.py`, `test_ergasterion_challenge.py` | Difficulty gradient; graded by `same_graph` + diff; dragon targets. |
| Fold-to-define (abstraction) | SHIPPED | `definitions.py`, `eg_splice.py` → `test_definitions.py`, `test_ergasterion_define*.py` | Name a subgraph, reuse as one spot; local + reversible. |
| Composition palette / ops | SHIPPED | `composition_ops.py` → `test_composition_ops.py` | Regime-1 palette; per-branch phases. |
| **Agon** — Endoporeutic Game | PARTIAL (V1) | `endoporeutic_game.py`, `web_api/routes/agon.py` → `test_epg_exemplar_scripts.py`, `test_agon_routes.py` | Triadic framing; **hot-seat** (one user, both roles); nothing auto-asserts. Deferred: full auto-opponent UX, dynamic-M. |
| Agon — interpretation register | SHIPPED | `semantic_game.py`, `domain_oracle.py`, `agon_models.py` → `test_semantic_game.py`, `test_agon_interpretation.py` | Choose M → peel G outside-in → Kleene verdict + witness/counterexample + transcript. |
| Agon — where-it-holds (inverse pivot) | SHIPPED | `web_api/routes/agon.py` → `test_agon_interpretation.py` | Ranks domains: holds / partial / independent / contradicts. |
| Automated Grapheus (minimax opponent) | SHIPPED | `grapheus.py` → `test_grapheus.py` | Move-by-move contest; minimax over the peel. |
| Disposition taxonomy (Agonothetes) | SHIPPED | `web_api/services/agonothetes.py` → `test_agon_routes.py` | Verdict-annotated; nothing auto-asserts. |
| Cross-mode context reflex | SHIPPED | `web_viewer/js/context-reflex.js`, `introspection.py` → `test_context_reflex_e2e.py` | Ground (universe/standing/derivation) + enclosing-cut breadcrumb. **Overlay docking open — ROADMAP #5.** |
| Shared diagram viewer (pan/zoom/camera) | SHIPPED | `web_viewer/js/diagram-viewer.js` | One component all three modes use. |
| Newcomer "first graph" primer | SHIPPED | `web_viewer/js/primer.js`, `web_api/routes/primer.py` → `test_primer_route.py`, `test_primer_e2e.py` | The four marks + EGIF key + worked first graphs drawn by the real engine; dragon chips deep-link into challenge mode. "New here?" on every mode page + the home door. ROADMAP #4 stage 2(b). |

---

## F. Model checking, import & ontology

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Domain oracle (M queried, not held) | SHIPPED | `domain_oracle.py` → `test_domain_oracle.py` | `resolve`/`witness`/`match_atoms`; open-world. |
| Semantic game / peel (Kleene 3-valued) | SHIPPED | `semantic_game.py` → `test_semantic_game.py` | Model-checking, not inference. |
| Model materialization (Horn forward-chain) | SHIPPED | `model_materialization.py` → `test_model_materialization.py` | Least Herbrand model; non-Horn skipped honestly. |
| Theory query (T-box subsumption) | SHIPPED | `theory_query.py` → `test_theory_query.py` | `entails` by freeze-a-fresh-witness; Horn-complete. |
| OWL → CLIF → EGI pipeline | SHIPPED | `domain_model_importer.py`, `tools/owl_to_clif.py` → `test_owl_import.py` | Untranslatable constructs reported, not dropped. |
| RDF front-end (Turtle/XML/N-Triples/JSON-LD) | SHIPPED | `domain_model_importer.py`, `tools/rdf_to_owl.py` → `test_rdf_import.py` | rdflib → same OWL AST. |
| cl-imports auto-resolution | SHIPPED | `cl_import_resolver.py` → `test_cl_import_resolver.py` | Mapping/Directory/ColoreWeb/Caching/Chain. |
| Ontology EGIF encoder | SHIPPED | `ontology_egif.py` → `test_ontology_import.py` | Subsumption = scroll. |
| Z3 SMT validation | SHIPPED | `z3_semantic_validator.py` | Semantic cross-check. |
| FOLIO native engine (FOL decision) | SHIPPED | `folio_fol.py`, `folio_native.py`, `folio_model_finder.py` → `test_folio_*.py` | Native coverage 95.1% at 100% soundness vs Z3. |
| DLCore reasoning services | PARTIAL | `dl_reasoning.py` → `test_dl_reasoning.py` | Instance-check 75%, consistency dl 100%/el 60%; abstainers beyond domain cap are honest, not unsound. |
| Manchester OWL syntax | OUT | — | No maintained Python parser; low real-world value. |
| Layout of very large ontologies | PARTIAL | `elk_layout_engine.py` | Super-linear ≳127 axioms; 130-cut density closure imports as data but stays undrawn (layout-perf frontier). |

---

## G. NL → logic (*LLM proposes, Arisbe disposes*)

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| NL → FOL proposal | SHIPPED | `nl_to_logic.py` → `test_nl_to_logic.py` | LLM emits only a FOL string + vocabulary; everything downstream deterministic + pre-tested. LLM never touches the EGI. |
| `/agon/propose-nl` route | SHIPPED | `web_api/routes/agon.py` → `test_propose_nl_route.py` | Resolve M → hint → propose → reconcile → peel; LOW warrant, nothing persisted. |
| Plain-English door (Agon setup UI) | SHIPPED | `web_viewer/agon.html` → `test_agon_e2e.py` | "…or describe G in plain English" textarea + ✶ Translate → fills Proposal G from the drafted EGIF; shows the reading, the vocabulary-miss vs fact-miss split, honest non-results. ROADMAP #4 stage 2(a). |
| Multi-candidate disambiguation (G1,G2,G3 by verdict) | DESIGNED | — | "Disambiguate by interpretation, not parser confidence." See ROADMAP. |
| LOW-warrant `/import/admit` persistence | DESIGNED | — | Persist a tested proposal with its NL+LLM provenance trace. See ROADMAP. |

---

## H. Analysis / doctrine tooling

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Diagram↔narration check | SHIPPED (prototype) | `diagram_narration_check.py` → `test_diagram_narration_check.py` | Scorer over 8 chains/35 steps; 3 Centering/DRT salience roles 100%. **Measurement tool — not surfaced in the UI.** See [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10. |
| Schema layer (graph-with-holes node) | SHIPPED | `schema.py`, `eg_splice.py` → `test_schema.py` | P7 least-number schema; induction scaffold. Schema-drawing/§3.3 is a frontier. |
| Derived rules (named UI moves) | SHIPPED | `derived_rules.py` → `test_derived_rules.py` | Built atop Dau's six. |
| Render-M UI (ground/legend + neighborhood) | SHIPPED | `m_render.py` → `test_m_render.py`, `test_agon_interpretation.py`, `test_agon_e2e.py` | Agon interpretation register draws M: the vocabulary legend (d) + the relevant-neighborhood fragment G touches (c, seed + one hop, budget-capped, horizon reported). Read-only chrome, M never asserted. See ROADMAP #2 / [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) (c)+(d). |
| Reference / transclusion node | DESIGNED | — | Architectural fork; touches `egi_core_dau` + §3.3. Author decision. ROADMAP #3. |

---

## Out of scope (with reasons)

| Item | Why | Pointer |
|---|---|---|
| Gamma as a *modal* extension | The diachronic DAG already *is* the drawn Kripke frame; no modal mark needed. | [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) |
| Raster image → EGI | The hard inverse problem; structured-drawing reading is in scope, pixels are not. | [EXACT_CORRESPONDENCE.md](EXACT_CORRESPONDENCE.md) |
| Qt desktop GUI | Archived May 2026; web app is canonical. | `archive/qt-gui-2025/` |

---

## The protected-core set (authoritative)

The **14** modules guarded by `tools/core_protection_system.py` (require `.core_modification_authorized`
to modify) — the genuine calculus core. This is the **actual** list from the source:

`egi_core_dau` · `egi_io` · `hierarchical_index` · `universe_of_discourse` ·
`egi_transformation_history` · `formal_transformation_rules` · `rule_interaction` ·
`subgraph_closure_validator` · `graph_isomorphism_engine` · `ligature_manipulation_rules` ·
`single_object_ligature_detector` · **`correspondence_attestation`** · **`presentation_ops`** ·
**`natural_layout`**.

> **Set history (2026-06-27):** the three correspondence enforcers were **added** (decision (a) — the
> runtime guards of the central invariant); the six EGIF/CGIF/CLIF parsers/generators were **removed**
> (decision (b) — application-level I/O, not the calculus; the rules don't import them; guarded instead
> by the corpus round-trip tests in CI). Net 17 → 20 → 14. The set's inline comments now double as the
> bedrock note — there is no separate CODEOWNERS file (it wouldn't fire in a solo, no-PR workflow).
