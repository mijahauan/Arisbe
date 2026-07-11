# Arisbe — Capability & Maturity Map

> **What this is.** A single living table of *what Arisbe can do*, its maturity, where it lives in the
> code, and what test guards it. It replaces reading the layered `CURRENT_PLAN.md` session log to
> answer "what actually works." Update the relevant row when a capability ships or changes status.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [ROADMAP.md](ROADMAP.md) ·
> [GLOSSARY.md](GLOSSARY.md). Developer module map: [../CLAUDE.md](../CLAUDE.md).
>
> *Last consolidated: 2026-07-02.*

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
| Existential Graph Instance ([EGI](GLOSSARY.md#egi)) data model (`RelationalGraphWithCuts`) | SHIPPED | `egi_core_dau.py` → `test_egi_core_comprehensive.py` | Dau's `(V,E,ν,⊤,Cut,area,ρ)`; immutable. |
| Immutability / construction API | SHIPPED | `egi_core_dau.py` → same | `.with_vertex()`, `.with_edge()`; never `.add_*()`. |
| Six transformation rules (ERA, INS, IT±, DC±) | SHIPPED | `formal_transformation_rules.py` → `test_chapter15_formal_calculus.py`, `test_beta_proof_exercises.py` | Beta-aware; Dau Ch. 14/15. |
| Headless rule-interaction protocol | SHIPPED | `rule_interaction.py` → `test_rule_interaction.py` | Stepwise `begin→advance→apply` for all six. |
| Beta / FOL (lines of identity, shared vertices) | SHIPPED | `egi_core_dau.py`, `formal_transformation_rules.py` → `test_beta_proof_exercises.py` | Defining vs bound labels; ancestor-area vertices free. |
| Closure validation (Beta-aware) | SHIPPED | `subgraph_closure_validator.py` → `test_subgraph_closure_validation.py` | Free outer-area vertices. |
| Graph isomorphism (VF2, for IT−) | SHIPPED | `graph_isomorphism_engine.py` → `test_graph_isomorphism_engine.py` | NetworkX VF2 copy detection. |
| Ligature manipulation (Ch. 16–17) | SHIPPED | `ligature_manipulation_rules.py`, `single_object_ligature_detector.py` → `test_chapter16_17_ligature_soundness_simplified.py` | Sole non-test consumer is `chapter17_soundness_evaluation.py` — thinly held. |
| Syntactic equivalence (Ch. 20) | SHIPPED | `syntactic_equivalence_checker.py`, `chapter20_syntactic_equivalence_fixes.py` → `test_chapter20_syntactic_equivalence.py` | |
| Existential Graph ([EG](GLOSSARY.md#eg)) navigation / introspection | SHIPPED | `eg_navigation.py` → `test_introspection_and_rules.py` | Content-addressable selection; `same_graph` Beta authority. |
| Proof authoring chains (`ProofChain`/`ChainStep`) | SHIPPED | `proof_authoring.py` → `test_chain_persistence.py`, `test_branching_chain.py` | Rule-by-locator; deterministic replay. |

---

## B. Linear formats — *all production, round-trip tested*

| Capability | Status | Home (src → test) | Corpus |
|---|---|---|---|
| Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)) parse / generate | SHIPPED | `egif_parser_dau.py` / `egif_generator_dau.py` → `test_tomos_parsing.py` | 57+ (comment stripping is quote-aware — a `#` inside a constant, e.g. a URL, is data) |
| Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)) parse / generate (ISO/IEC) | SHIPPED | `cgif_parser_dau.py` / `cgif_generator_dau.py` → `test_tomos_parsing.py` | 40+ |
| Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)) parse / generate (Common Logic) | SHIPPED | `clif_parser_dau.py` / `clif_generator_dau.py` → `test_clif_unit.py`, `test_tomos_parsing.py` | 35+ |
| First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl)) translation (Φ/Ψ bidirectional) | SHIPPED | `chapter18_fopl_translation.py` → `test_egi_to_fol.py` | EGI ↔ FOL |
| EGI→FOL bridge (read-only inverse) | SHIPPED | `egi_to_fol.py` → `test_egi_to_fol.py` | Faithfulness pinned by Z3. |
| JSON I/O (with layout deltas) | SHIPPED | `egi_io.py` → `test_complete_serialization_simplified.py` | Deltas survive transforms. |

---

## C. Correspondence machinery — *the central problem, operational*

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Coordinate-free natural layout | SHIPPED | `natural_layout.py` → `test_natural_layout.py` | Containment + crossing-sequences + incidence; geometry-free. |
| Correspondence check (§3.3) runtime attestation | SHIPPED | `correspondence_attestation.py` → `test_correspondence_attestation.py`, `test_correspondence_invariant.py` | `attest_correspondence` hooked into layout_service + save/load. **Protected (added 2026-06-27).** |
| Regime-3 presentation algebra | SHIPPED | `presentation_ops.py` → `test_presentation_ops.py` | move/reshape/reroute; `Regime3Violation` on boundary crossing. **Protected (added 2026-06-27).** |
| Eclipse Layout Kernel ([ELK](GLOSSARY.md#elk)) layout engine (default) | SHIPPED | `elk_layout_engine.py` (+`elk_worker.js`) → `test_elk_layout_engine.py`, `test_elk_ligature_edge_cases.py` | Cut-aware; ligature edge cases audited. Ligature router carries an exact bounding-box quick reject (~140× on a large star-shaped graph, routes bit-identical). |
| Tension layout engine (opt-in) | PARTIAL | `tension_engine.py` → `test_tension_engine.py` | `?engine=tension`; 17/18 corpus attest, §3.3-gated with ELK fallback. |
| Tension sibling-order + stress | SHIPPED | `tension_layout.py` → `test_tension_layout.py` | `?tension` knob; crossing-sequence-independent. |
| SVG renderer | SHIPPED | `simple_svg_renderer.py` → `test_overview_attestation.py` | LayoutDTO → SVG; one engine across all modes. |
| Drawn→EG reader | SHIPPED | `eg_reader.py` → `test_eg_reader.py` | `read(render(egi))==egi` corpus-wide + human geometry. |
| Fix-time drawing validity | SHIPPED | `drawing_validity.py` → `test_drawing_validity.py` | Errors/warnings on a drawing with no EGI yet. |
| Drawing→EGI builder | SHIPPED | `drawing_to_egi.py` → `test_drawing_to_egi.py` | "fix = read"; corpus round-trip via `same_graph`. |
| Legible EGI diff | SHIPPED | `egi_diff.py` → `test_egi_diff.py` | structure/missing/extra/scope/incidence/order, content-aligned. |
| TikZ / export rendering (geometric) | SHIPPED | `web_api/services/tikz_export.py`, `export_service.py` | Dau/Sowa coordinate TikZ; `/export` formats EGIF / CGIF / CLIF / SVG / TikZ / PNG / PDF. |
| Authentic-Peirce LaTeX export | SHIPPED (phase 1+2) | `peirce_latex.py` + `tex/arisbe-eg.sty` → `test_peirce_latex.py` | `peirce-tikz` format: oval cuts, heavy lines of identity, hooks; pure TikZ, pdflatex-native (no PSTricks); wedded to the §3.3-attested Data Transfer Object ([DTO](GLOSSARY.md#dto)); delta-faithful (regime-3 nudges thread through `/export`). Phase 2: **iconic self-continuing [scroll](GLOSSARY.md#scroll) (a nested double cut — "if … then") glyph** (opt-in `scroll_glyph`, ink-only), **worked-chain → multi-figure LaTeX document** (`export_peirce_chain`, `POST /export/chain`), **drawing→EGI learning loop** (`layout_learning.py`: `arrangement_deltas` + `generalize_arrangement` → style [ladder](GLOSSARY.md#style-ladder)). |

---

## D. Diachronic / provenance

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Universe of Discourse entity | SHIPPED | `universe_of_discourse.py` → `test_universe_of_discourse.py` | Synchronic EGI + diachronic directed acyclic graph ([DAG](GLOSSARY.md#dag)) + deltas. |
| Branching transformation history | SHIPPED | `egi_transformation_history.py` → `test_egi_transformation_history.py` | Immutable states; append-only DAG. |
| Corpus persistence (`TomosService`) | SHIPPED | `tomos_service.py` → `test_chain_persistence.py` | save/load attest §3.3 at the boundary; chain JSONL. |
| Provenance + [warrant](GLOSSARY.md#warrant) / standing | SHIPPED | `provenance.py` → `test_provenance.py` | `standing_of` → posited/derived/withstood badge. |
| Presentation deltas + style ladder | SHIPPED | `presentation_deltas.py`, `style_loader.py`, `style_specification.py` → `test_presentation_deltas.py`, `test_styles.py` | Sparse regime-3 exemplars; extrapolation. |
| Liveness / desuetude | SHIPPED | `liveness.py` → `test_liveness.py` | Reversible retire/revive. |
| Annotations | SHIPPED | `annotations.py` → `test_annotations.py` | Persistent element metadata. |
| Proof serializer | SHIPPED | `proof_serializer.py` → `test_proof_serializer.py` | Chain JSON/JSONL replay schema. |
| Modal reading (◇/□ off the DAG) | SHIPPED | `modal_query.py` → `test_modal_and_dialog.py`, `test_organon_routes.py` | ◇φ = some legal trajectory scribes φ, □φ = every one does; no modal mark needed. Surfaced as the Organon **modal lens**. |
| Gamma demonstrations (Peirce's modal figures in Beta) | SHIPPED 2026-07-04 | `tools/build_gamma_modal_exemplars.py` → `test_gamma_demonstrations.py` | The broken-cut square (Lowell 1903), the *de inesse* / would-be pair (*Prolegomena*, CP 4.546 / Ms 490), the book of sheets — corpus exemplars with verified citations; the modal lens gained a **proposal reading** (◇G/□G peeled per world) + drawn world thumbnails. See `docs/GAMMA_DEMONSTRATIONS.md`. |
| Model revision through dialog | SHIPPED | `model_revision.py` → `test_modal_and_dialog.py` | The [Agonothetes](GLOSSARY.md#agonothetes) disposition taxonomy's M-revising subset (new_fact / generalization / challenge_to_M / …), each a real Dau move on M's sheet. Surfaced as the Organon **audit lens** (a standing proposal peeled against every successive M). |
| Provenance → publication citation | SHIPPED | `scholarly_citation.py` → `test_scholarly_citation.py` | `citation_for` → human line + BibTeX from a UoD's source record; fabricates nothing. `GET /export/citation` + the figure-caption `cite` flag. |

---

## E. The three web modes

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| HTTP API (live OpenAPI spec) | SHIPPED | `web_api/main.py` (FastAPI) | `/openapi.json` + `/docs` (Swagger) auto-served — 80+ routes across `/organon` `/ergasterion` `/agon` `/export` `/import` `/primer`. The machine-readable API reference is the running server; error vocabulary in `TROUBLESHOOTING.md`. |
| **Organon** — read-only archive | SHIPPED | `web_api/routes/organon.py` → `test_organon_routes.py`, `test_overview_routes.py` | Listing, Universe of Discourse ([UoD](GLOSSARY.md#uod)) detail, chain player; both load+render §3.3-attested. |
| Adaptive-scope lenses (overview) | SHIPPED | `overview_projection.py`, `eg_structure.py` → `test_overview_attestation.py` | Negation well + storyboard; LOD knob. |
| **Ergasterion** — workshop | SHIPPED | `web_api/routes/ergasterion.py` → `test_ergasterion_routes.py` | RuleInteraction-driven; regime-1 drafts; branch-on-edit; scratch store. |
| Freeform draw-then-read | SHIPPED | `web_viewer/js/freeform-canvas.js`, `drawing_*`→ `test_ergasterion_freeform.py`, `…_e2e.py` | Typed marks → gate ① read/fix. E2E (Playwright). |
| Graph↔Argument lock | SHIPPED | `web_api/routes/ergasterion.py` → `test_ergasterion_freeform.py` | No rules on unfixed; no meaning-change on fixed. |
| Challenge mode | SHIPPED | `challenge_mode.py` → `test_challenge_mode.py`, `test_ergasterion_challenge.py` | Difficulty gradient; graded by `same_graph` + diff; dragon targets. |
| Fold-to-define (abstraction) | SHIPPED | `definitions.py`, `eg_splice.py` → `test_definitions.py`, `test_ergasterion_define*.py` | Name a subgraph, reuse as one spot; local + reversible. |
| Composition palette / ops | SHIPPED | `composition_ops.py` → `test_composition_ops.py` | Regime-1 palette; per-branch phases. |
| **Agon** — [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game | PARTIAL (V1) | `endoporeutic_game.py`, `web_api/routes/agon.py` → `test_epg_exemplar_scripts.py`, `test_agon_routes.py` | Triadic framing; **hot-seat** (one user, both roles); nothing auto-asserts. Deferred: full auto-opponent UX, dynamic-M. The game also plays *autonomously*, headless — see §H. |
| Agon — interpretation register | SHIPPED | `semantic_game.py`, `domain_oracle.py`, `agon_models.py` → `test_semantic_game.py`, `test_agon_interpretation.py` | Choose M → [peel](GLOSSARY.md#peel) G outside-in → Kleene verdict + witness/counterexample + transcript. |
| Agon — where-it-holds (inverse pivot) | SHIPPED | `web_api/routes/agon.py` → `test_agon_interpretation.py` | Ranks domains: holds / partial / independent / contradicts. |
| Automated Grapheus (minimax opponent) | SHIPPED | `grapheus.py` → `test_grapheus.py` | Move-by-move contest; minimax over the peel. |
| Disposition taxonomy ([Agonothetes](GLOSSARY.md#agonothetes)) | SHIPPED | `web_api/services/agonothetes.py` → `test_agon_routes.py` | Verdict-annotated; nothing auto-asserts. |
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
| Theory query (terminological box ([T-box](GLOSSARY.md#t-box)) subsumption) | SHIPPED | `theory_query.py` → `test_theory_query.py` | `entails` by freeze-a-fresh-witness; Horn-complete. |
| Web Ontology Language ([OWL](GLOSSARY.md#owl)) → CLIF → EGI pipeline | SHIPPED | `domain_model_importer.py`, `tools/owl_to_clif.py` → `test_owl_import.py` | Untranslatable constructs reported, not dropped. |
| Resource Description Framework ([RDF](GLOSSARY.md#rdf)) front-end (Turtle/XML/N-Triples/JSON-LD) | SHIPPED | `domain_model_importer.py`, `tools/rdf_to_owl.py` → `test_rdf_import.py` | rdflib → same OWL AST. |
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

## H. The automated Endoporeutic Game — *model development against sources*

The game played autonomously under the incorruptible mechanical referee: a proposer (the
*membrane*) voices a claim, the [peel](GLOSSARY.md#peel) tests it against the developing model M,
a panel negotiates a disposition, the model revises, disuse decays what fell from use. Design of
record: [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) ·
[AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md).

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Automated evolution loop (closed membrane) | SHIPPED | `agon_evolution.py` → `test_agon_evolution.py` | A generation is a game round: produce → test → negotiate → inject → decay. Reproduces the hand-played swan trajectory on its own. |
| Three LLM roles (Graphist / Grapheus / Agonothetes) | SHIPPED | `agon_llm.py` → `test_agon_llm.py` | *The LLM argues, the calculus decides*: every move reduced to a calculus artifact and re-checked. Branch-the-DAG on irreducible disagreement. Prompt-injection quarantine + per-role telemetry. CI runs on a scripted fake client; live is key-gated. |
| Meta-learning (the game studying the game) | SHIPPED | `agon_metalearning.py` → `test_agon_metalearning.py` | Resolution principles, stickiness (decay-aware), friction, gaps, ablations, and the **poise** observable (engagement/settlement/absorption — perspectival, never a target). |
| Open membranes (raise-only / raise-and-resolve / wiki-dispute) | SHIPPED | `discourse_membrane.py`, `resolving_membrane.py`, `wiki_dispute_membrane.py` → `test_*_membrane.py` | Discourse (cross-source consistency only), world-teeth (prediction ledger; the world selects against the over-general theory), edit-war + editorial mechanism (which resolution produces *durable* knowledge). |
| Live runner (bounded, paced, checkpointed) | SHIPPED | `live_runner.py` → `test_live_runner.py` | Disuse-decay bounds \|M\| — **atom-level since 2026-07-03** (the affirmed rulebook: the habit is the fact, not the name; use = re-delivery; the warm-hub pinning of RUN_3 F1″ dissolved); segment → §3.3-attested checkpoint → prune RAM; stop conditions; crash/resume (the decay clock continues, not resets). Round compute flattened the same day (§16.2): the canonical-signature fix (15.7 s → 3.3 ms generating a 200-atom hub sheet) + a semi-naive `IncrementalMaterializer` per runner. |
| Re-generalization (predict→refute→re-generalize) | SHIPPED (run-8 machinery, 2026-07-07) | `weather_recalibration.py` + `live_runner` reseed hook → `test_weather_recalibration.py`, `test_resolving_membrane.py` | After the world falsifies a seeded law, an adaptive controller widens its discretization (temp band / PoP threshold) from the ledger track record and re-seeds it, so the game bets again instead of falling silent (F2⁷). Temp law is band-agnostic → re-generalization moves the *claim shape*, not the text; F1⁷ NWS retry/backoff + per-station error rates ship with it. The calibration payoff is **live-only** (a replay's claims are frozen at their recording band); `--regenerate` in `tools/run_live_weather.py`, off by default. See [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) Part II §11.3–11.5 (the principle) + Part III §12 (the run ledger). |
| Wikidata live source (crawl + change stream) | SHIPPED | `wikidata_source.py` → `test_wikidata_source.py` | Statements → ground facts; references → provenance; ranks → resolutions; label legibility with a degradation tripwire. `RotatingWikidataSource` (frontier crawl) + `RecentChangesSource` (live contestation stream). A reliable source overturns a bare value mechanically — no LLM. |
| Live runs 1–2 (executed evidence) | DONE (evidence on record) | `tools/run_live_wikidata.py` → `runs/RUN_1_LOG.md`, `runs/RUN_2_LOG.md` | Pre-registered priors; determinism canary green (offline replay reproduces the live trajectory). Run 1 = the monological-ingestion baseline; run 2 = the change stream is a firehose of novelty — neither passive membrane revisits. |
| Tropism (warm-set re-poll) | SHIPPED (increment 1, 2026-07-02) | `tropism.py` → `test_tropism.py` | Run 2's mandate: ingestion alone cannot test durability; only M's state directing re-engagement can. `WarmSetTropism` (M's standing facts → entity ids via the reversed label cache, decay-adjacent first; ambiguous/unmapped labels skipped + counted) + the `inject` seam on the crawl + `LiveRunner(tropism=…)` + the driver's `--warm-fraction` (0.5, fixed, affirmed). Offline headlines: a warm re-delivery reads as a non-revising round (the habit holding); a deprecation on a warm re-reach **meets its standing target** and retracts — the P2 event. Tropism affirmed (AUTOMATED_ENDOPOREUTIC_GAME.md §4d); **runs 3–4 executed & disposed 2026-07-03** (`runs/RUN_3_LOG.md`, `runs/RUN_4_LOG.md`): the seam ported to the stream (`RecentChangesSource.inject`; a quiet tick serves the warm set), the 2×2 (crawl/stream × passive/tropism) closed — non-revising 0 → 23.6 % (crawl) → 31.8 % (stream), tropism-attributable on both margins; the P2 event still world-starved (all live deprecations born-deprecated; the pre-registered rate branch fired — duration is the named lever). Instruments now atom-honest (`m_atoms` digest column + `max_m_atoms` net, RUN_3 F1″); the attest wall fixed (visibility-graph grid + lazy A*, 1075 s → 1.7 s at ~200 atoms) exposing round compute as the next super-linear cost (RUN_4 F2⁗ → the atom-decay rulebook question, evidence now in hand). The docket of doubts (`query_docket`) is now AUTOMATED_ENDOPOREUTIC_GAME.md Part I §4 (item 5). |

---

## I. Analysis / doctrine tooling

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Diagram↔narration check | SHIPPED (prototype) | `diagram_narration_check.py` → `test_diagram_narration_check.py` | Scorer over 8 chains/35 steps; 3 Centering/Discourse Representation Theory ([DRT](GLOSSARY.md#drt)) salience roles 100%. **Measurement tool — not surfaced in the UI.** See [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10. |
| Schema layer (graph-with-holes node) | SHIPPED | `schema.py`, `eg_splice.py` → `test_schema.py` | P7 least-number schema; induction scaffold. Schema-drawing/§3.3 is a frontier. |
| Derived rules (named UI moves) | SHIPPED | `derived_rules.py` → `test_derived_rules.py` | Built atop Dau's six. |
| Render-M UI (ground/legend + neighborhood) | SHIPPED | `m_render.py` → `test_m_render.py`, `test_agon_interpretation.py`, `test_agon_e2e.py` | Agon interpretation register draws M: the vocabulary legend (d) + the relevant-neighborhood fragment G touches (c, seed + one hop, budget-capped, horizon reported). Read-only chrome, M never asserted. See ROADMAP #2 / [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) (c)+(d). |
| Reference / transclusion node | SHIPPED (increment 1, intra-UoD) | `reference_node.py`, `reference_resolution_check.py` → `test_reference_node.py`, `test_reference_glyph.py`, `test_reference_resolution_check.py` | Form-2 reference edge + overlay mark, additive (`egi_core_dau` untouched); the law `RESOLVE ≡ INLINED-AND-ATTESTED` proven (R1–R4) before building. Cross-UoD (use/mention fork) deferred. ROADMAP #3. |

---

## J. Interfaces / adoption — *the referee, callable from outside*

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| MCP verifier service | SHIPPED | `mcp_verifier.py` (logic) + `mcp_server.py` (transport) → `test_mcp_verifier.py` | Exposes the mechanical referee as [Model Context Protocol](https://modelcontextprotocol.io) stdio tools: `check_egif` (parse+validate, content-addressed element ids), `peel` (three-valued `semantic_game.evaluate` against a supplied M), `apply_rule`/`validate_step` (a sound Dau rule), `attest` (§3.3 correspondence). Pure functions import no MCP SDK (CI-safe); `mcp` is an **optional extra** (`uv sync --extra mcp`), import-guarded. Additive, non-core. A wrapper over existing logic — *the LLM argues, the calculus decides.* See [MCP_VERIFIER.md](MCP_VERIFIER.md). |
| Accessible (non-visual) EG projection | SHIPPED 2026-07-07 | `accessible_projection.py` → `test_accessible_projection.py`, `test_organon_routes.py`, `test_organon_lenses_e2e.py` | A projection of the coordinate-free ground truth that is *not visual at all*: a traversable sheet → cut → area → ligature tree + an outside-in **spoken reading** (structural-faithful, never rephrasing scope) + the flat screen-reader reading order. Surfaced as the Organon **accessible lens** — a genuine ARIA tree (`role=tree/treeitem`, arrow-key nav) with the EGIF cross-check. Geometry-free (no §3.3 obligation); faithfulness earned by totality + crossing-fidelity tests; ordering id-independent so two parses read alike. First a11y surface in the repo. |

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
