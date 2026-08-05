# Arisbe — Capability & Maturity Map

> **What this is.** A single living table of *what Arisbe can do*, its maturity, where it lives in the
> code, and what test guards it. It replaces reading the layered `CURRENT_PLAN.md` session log to
> answer "what actually works." Update the relevant row when a capability ships or changes status.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [ROADMAP.md](ROADMAP.md) ·
> [GLOSSARY.md](GLOSSARY.md). Developer module map: [../CLAUDE.md](../CLAUDE.md).
>
> *Kept current — see individual row dates (latest: 2026-07-26).*

**Status legend**
- **SHIPPED** — working, with a passing test home.
- **PARTIAL** — built and useful, but a frontier or edge case stands documented as open.
- **DESIGNED** — specified in docs, not yet built.
- **OUT** — explicitly not being built (with a reason; see [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §5).

> *Status stays conservative. "SHIPPED" appears only where a passing test exists. Where CLAUDE.md
> and the code disagreed during consolidation, the code won.*

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
| Model revision through dialog | SHIPPED | `model_revision.py` → `test_modal_and_dialog.py`, `test_model_revision.py` | The [Agonothetes](GLOSSARY.md#agonothetes) disposition taxonomy's M-revising subset (new_fact / generalization / challenge_to_M / …), each a real Dau move on M. `revise_with_disposition` is **residence-aware** (sweep #2): on a resident M every disposition dispatches to the licensed cell moves (INS-of-cell / ERA-in-cell), with the sheet-level primitives retained as the bare-fixture fallback. Surfaced as the Organon **audit lens** (a standing proposal peeled against every successive M). |
| M-residence: cells at even depth of the standing [world-scroll](GLOSSARY.md#world-scroll) + explicit M-steps | SHIPPED 2026-07-15 · **relocated to cells 2026-07-16 (sweep #2, M_RESIDENCE §9)** | `world_scroll.py`, `m_steps.py` → `test_world_scroll.py`, `test_m_steps.py`, `test_corpus_polarity_discipline.py` | M's elements reside in per-admission **cells at even depth** beside the hold — `~[ ~[cell] … ~[ ] ]`, at least one empty cut keeping vacuity (nothing contingent at depth 0); `m_view` is the one shared read primitive (oracle · materializer · theory query · render-M · the loops' scans). Enlargement = `ADMIT_TO_M` (one licensed INS of a closed cell); retraction = `RETRACT_FROM_M` (one licensed ERA inside a cell — refutation and disuse-fading one move, split by the recorded `flavor`; the emptied husk stands as a scar); the challenge = `REVISE_M` (ONE composite step, ERA + INS); world-withdrawal (the triple) retired to rare full replacement; every verdict an explicit, recomputable `PEEL` step. **The live loops emit native rule-licensed chains** (§8.1 discharged — `agon_evolution.run` opens DC+ · INS; decay is the licensed ERA). The standing corpus-polarity gate guards all 18 M-bearing UoDs (the §9.3 inventory, verdict recompute, ligature closure); allowlist empty. Deferred, named: D5 dusty rooms (designation-by-record) + D6 room-granularity pruning. |
| The EPG episode in ink: entertain · confirm · discharge | SHIPPED 2026-07-16 (M_RESIDENCE §10) | `world_scroll.py` (`entertain_episode`/`discharge_episode`/`abandon_episode`), `m_steps.py` (`ENTERTAIN`/`DISCHARGE_TO_M`/`ABANDON_EPISODE`) → `test_world_scroll.py::TestEpisode`, `test_m_steps.py::TestEpisodeSteps`, the gate | "If M then P" built as ink inside the agreed context (DC+ · IT+ of M · INS of `~[P]`, the vacuity rider keeping it forceless — the **episode theorem**: the DC+ must land in an even context at depth ≥ 2; at depth 0 the discharge is unreachable by soundness itself); the discharge = drawn modus ponens (IT− · IT− · DC−), P landing in M *derived, never inserted*. **Ruling (b)**: the ⊥-door makes the licence unconditional, so `discharge_step` refuses without a confirming PEEL to cite; the gate re-asserts every citation and the **m_view tripwire** refuses any silent M-change. A discharged chain reads *theorematic* (ENTERTAIN = Peirce's auxiliary line). Exemplar: `episode_discharge` (absent → derived-only → standing). |
| Provenance → publication citation | SHIPPED | `scholarly_citation.py` → `test_scholarly_citation.py` | `citation_for` → human line + BibTeX from a UoD's source record; fabricates nothing. `GET /export/citation` + the figure-caption `cite` flag. |

---

## E. The three web modes

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| HTTP API (live OpenAPI spec) | SHIPPED | `web_api/main.py` (FastAPI) | `/openapi.json` + `/docs` (Swagger) auto-served — 80+ routes across `/organon` `/ergasterion` `/agon` `/export` `/import` `/primer`. The machine-readable API reference is the running server; error vocabulary in `TROUBLESHOOTING.md`. |
| **Organon** — read-only archive | SHIPPED | `web_api/routes/organon.py`, `chain_branches.py` → `test_organon_routes.py`, `test_overview_routes.py`, `test_chain_branches.py`, `test_branching_chain.py` | Listing, Universe of Discourse ([UoD](GLOSSARY.md#uod)) detail, chain player; both load+render §3.3-attested. The player is **branch-oriented** (2026-07-16): on a branching chain it follows one line at a time with a ⑂ chip strip (labels from the recorded `branch_id`s, "main"/"branch N" fallback), an honest per-branch counter ("a counter never aggregates incompatible futures"), fork/convergence cues, and per-world branch tags in the modal lens. |
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

The game plays autonomously under the incorruptible mechanical referee. A proposer (the
*membrane*) voices a claim, the [peel](GLOSSARY.md#peel) tests it against the developing model M,
a panel negotiates a disposition, the model revises, and disuse decays what fell from use. Design of
record: [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) ·
[AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md).

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Automated evolution loop (closed membrane) | SHIPPED | `agon_evolution.py` → `test_agon_evolution.py` | A generation is a game round: produce → test → negotiate → inject → decay. Reproduces the hand-played swan trajectory on its own. |
| Three LLM roles (Graphist / Grapheus / Agonothetes) | SHIPPED | `agon_llm.py` → `test_agon_llm.py` | *The LLM argues, the calculus decides*: every move reduced to a calculus artifact and re-checked. Branch-the-DAG on irreducible disagreement. Prompt-injection quarantine + per-role telemetry. CI runs on a scripted fake client; live is key-gated. **"Three roles" ≠ three players:** two players (Graphist = proposal-side / Grapheus = Model-M-side) + the Agonothetes fate-selector *reified as an agent acting on the outcome*, never a third contestant — canonical account [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §3. |
| Meta-learning (the game studying the game) | SHIPPED | `agon_metalearning.py` → `test_agon_metalearning.py` | Resolution principles, stickiness (decay-aware), friction, gaps, ablations, and the **poise** observable (engagement/settlement/absorption — perspectival, never a target). |
| Open membranes (raise-only / raise-and-resolve / wiki-dispute) | SHIPPED | `discourse_membrane.py`, `resolving_membrane.py`, `wiki_dispute_membrane.py` → `test_*_membrane.py` | Discourse (cross-source consistency only), world-teeth (prediction ledger; the world selects against the over-general theory), edit-war + editorial mechanism (which resolution produces *durable* knowledge). |
| Live runner (bounded, paced, checkpointed) | SHIPPED | `live_runner.py` → `test_live_runner.py` | Disuse-decay bounds \|M\| — **atom-level since 2026-07-03** (the affirmed rulebook: the habit is the fact, not the name; use = re-delivery; the warm-hub pinning of RUN_3 F1″ dissolved); segment → §3.3-attested checkpoint → prune RAM; stop conditions; crash/resume (the decay clock continues, not resets). Round compute flattened the same day (§16.2): the canonical-signature fix (15.7 s → 3.3 ms generating a 200-atom hub sheet) + a semi-naive `IncrementalMaterializer` per runner. |
| Re-generalization (predict→refute→re-generalize) | SHIPPED (run-8 machinery, 2026-07-07) | `weather_recalibration.py` + `live_runner` reseed hook → `test_weather_recalibration.py`, `test_resolving_membrane.py` | After the world falsifies a seeded law, an adaptive controller widens its discretization (temp band / PoP threshold) from the ledger track record and re-seeds it, so the game bets again instead of falling silent (F2⁷). Temp law is band-agnostic → re-generalization moves the *claim shape*, not the text; F1⁷ NWS retry/backoff + per-station error rates ship with it. The calibration payoff is **live-only** (a replay's claims are frozen at their recording band); `--regenerate` in `tools/run_live_weather.py`, off by default. See [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) Part II §11.3–11.5 (the principle) + Part III §12 (the run ledger). |
| Wikidata live source (crawl + change stream) | SHIPPED | `wikidata_source.py` → `test_wikidata_source.py` | Statements → ground facts; references → provenance; ranks → resolutions; label legibility with a degradation tripwire. `RotatingWikidataSource` (frontier crawl) + `RecentChangesSource` (live contestation stream). A reliable source overturns a bare value mechanically — no LLM. |
| Live runs 1–2 (executed evidence) | DONE (evidence on record) | `tools/run_live_wikidata.py` → `runs/RUN_1_LOG.md`, `runs/RUN_2_LOG.md` | Pre-registered priors; determinism canary green (offline replay reproduces the live trajectory). Run 1 = the monological-ingestion baseline; run 2 = the change stream is a firehose of novelty — neither passive membrane revisits. |
| Tropism (warm-set re-poll) | SHIPPED (increment 1, 2026-07-02) | `tropism.py` → `test_tropism.py` | Run 2's mandate: ingestion alone cannot test durability; only M's state directing re-engagement can. `WarmSetTropism` (M's standing facts → entity ids via the reversed label cache, decay-adjacent first; ambiguous/unmapped labels skipped + counted) + the `inject` seam on the crawl + `LiveRunner(tropism=…)` + the driver's `--warm-fraction` (0.5, fixed, affirmed). Offline headlines: a warm re-delivery reads as a non-revising round (the habit holding); a deprecation on a warm re-reach **meets its standing target** and retracts — the P2 event. Tropism affirmed (AUTOMATED_ENDOPOREUTIC_GAME.md §4d); **runs 3–4 executed & disposed 2026-07-03** (`runs/RUN_3_LOG.md`, `runs/RUN_4_LOG.md`): the seam ported to the stream (`RecentChangesSource.inject`; a quiet tick serves the warm set), the 2×2 (crawl/stream × passive/tropism) closed — non-revising 0 → 23.6 % (crawl) → 31.8 % (stream), tropism-attributable on both margins; the P2 event still world-starved (all live deprecations born-deprecated; the pre-registered rate branch fired — duration is the named lever). Instruments now atom-honest (`m_atoms` digest column + `max_m_atoms` net, RUN_3 F1″); the attest wall fixed (visibility-graph grid + lazy A*, 1075 s → 1.7 s at ~200 atoms) exposing round compute as the next super-linear cost (RUN_4 F2⁗ → the atom-decay rulebook question, evidence now in hand). The docket of doubts (`query_docket`) is now AUTOMATED_ENDOPOREUTIC_GAME.md Part I §4 (item 5). |

---

## I. Directed engagement — *the action arm (bootstrap rungs)*

The Minimal Predictive Automaton's *missing fifth* names the action arm that chooses *which* reach
to make next. It runs as an attention economy over candidate reaches, with pluggable worlds behind
one `Proposer` socket. Design of record:
[BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md).

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Attention economy (the socket, rung 1) | SHIPPED 2026-07-17 | `attention_economy.py` → `test_attention_economy.py` | `Want` + `AttentionEconomy`: severity-weighted decayed-yield-per-cost ordering of reaches; musement reservation + boredom detector; noisy-TV decay at kind and want level; degrade-to-mechanical; bounded registers with counted drops. Plus the `Horizon`/`HorizonItem` register (the not-yet-legible, retained/counted/re-attemptable). See [BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md) §3. |
| Probe-directed feed base (the socket base) | SHIPPED | `probe_feed.py` → `test_probe_feed.py` | `ProbeDirectedFeedBase`: the generic drain-refill `propose()` loop, model-delta yield read via `world_scroll.m_view`, FIFO/scatter baseline choosers, `replay_choices`, and the **count-or-refuse** dispatch rule (a chosen want the feed cannot voice is refused and counted, never silently dropped). |
| Arithmetic world (world #1) | SHIPPED 2026-07-17 | `arithmetic_world.py` → `test_arithmetic_world.py` | Computed arithmetic (atoms by computation; probe cost = primality-test cost; deterministic `coin` noise) + `ProbeDirectedFeed`. Headline (S1–S5, pre-registered): **Fermat's 1640 conjecture refuted at F5 (Euler 1732) under budget only by the economy arm** — the FIFO/scatter baselines never reach it within 90 rounds. |
| Vault world (world #2, the metadata membrane) | SHIPPED 2026-07-18 (RUN 13) | `vault_world.py` → `test_vault_world.py` | `VaultWorld` reads an Obsidian-style vault **structure-only** (path/folder/frontmatter/wikilinks/size/mtime — never body content, the custody constraint) + the journal's **two-timeline reader** (event-time vs deliberately-absent writing-time). `VaultFeed` is the socket's `Proposer` consumer, journal seeded at severity 8.0 (the author's datelined voice outranks a folder scan). Journal spine pinned from disuse-decay (RUN_13 F4¹³). |
| Oracle notes loop (V2a) | SHIPPED 2026-07-18 | `oracle_notes.py` → `test_oracle_notes.py` | The Obsidian-native oracle loop: candidates (provenance / multi-journal / horizon / reflective) → budget-bounded markdown with **sealed** forecasts (salted SHA-256, never plaintext) → the author's `**A:**` edits parsed back → an append-only JSONL ledger → reveals → a plain-English conjectures gloss. Banking an answer into M as an attributed quotation cell (V2a.2 item 2, `BANK_TO_M`); decline/silence first-class. |

---

## J. Analysis / doctrine tooling

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| The knowledge measure (K1–K4) | PARTIAL (K2, K3 built; a vector, never a scalar) | `modal_query.durability_modality` (K2), `model_materialization.materialization_ratio` (K3) → `test_modal_query.py`, `test_model_materialization.py` | The four-component measure of [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md): **K1** severity-weighted track record · **K2** durability/stickiness (`durability_modality` reads ◇/□ necessity off the branching DAG) · **K3** compression (`materialization_ratio` → `KnowledgeCompression`, derived ÷ (explicit + derived), extent-invariant in [0,1]) · **K4** use/decay (the `UsageLedger`). Three standing guards: **never truth · never a target · a vector, never a scalar over agents** (the un-possessability of the commens, [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §2a). Read across the fractal levels atom→law→M→mechanism→project. |
| Diagram↔narration check | SHIPPED (prototype) | `diagram_narration_check.py` → `test_diagram_narration_check.py` | Scorer over 8 chains/35 steps; 3 Centering/Discourse Representation Theory ([DRT](GLOSSARY.md#drt)) salience roles 100%. **Measurement tool — not surfaced in the UI.** See [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10. |
| Schema layer (graph-with-holes node) | SHIPPED | `schema.py`, `eg_splice.py` → `test_schema.py` | P7 least-number schema; induction scaffold. Schema-drawing/§3.3 is a frontier. |
| Derived rules (named UI moves) | SHIPPED | `derived_rules.py` → `test_derived_rules.py` | Built atop Dau's six. |
| Render-M UI (ground/legend + neighborhood) | SHIPPED | `m_render.py` → `test_m_render.py`, `test_agon_interpretation.py`, `test_agon_e2e.py` | Agon interpretation register draws M: the vocabulary legend (d) + the relevant-neighborhood fragment G touches (c, seed + one hop, budget-capped, horizon reported). Read-only chrome, M never asserted. See ROADMAP #2 / [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) (c)+(d). |
| Reference / transclusion node | SHIPPED (increment 1, intra-UoD) | `reference_node.py`, `reference_resolution_check.py` → `test_reference_node.py`, `test_reference_glyph.py`, `test_reference_resolution_check.py` | Form-2 reference edge + overlay mark, additive (`egi_core_dau` untouched); the law `RESOLVE ≡ INLINED-AND-ATTESTED` proven (R1–R4) before building. Cross-UoD *use* (scroll-import) deferred to the B-min core opening; the *mention* side is exercised overlay-first by the quotation stratum (next row). ROADMAP #3. |
| Second-order quotation overlay (Stage ⓪ of the crossing) | SHIPPED 2026-07-15 | `quotation_overlay.py`, `second_order_check.py` → `test_quotation_overlay.py`, `test_second_order_check.py` | The first build rung of the crossing verdicts ([CROSSING_DECISION_BRIEFS.md](CROSSING_DECISION_BRIEFS.md), 2026-07-16): `QuotationMark` — a proposition-sorted name in the host graph + a serialisable overlay beside the EGI (`quotations.json`, the `reference_node` pattern; no protected-core change) — with a resolver seam (inline EGIF / chain-step record / corpus-UoD mention), boundary hooks bridging into the `second_order_check` law (S1 stratification read off the *drawn* enclosure; S2 quote-equals-quoted + the correspondence check (§3.3) one level down; S5 per state; S4 horizons named; **S3 skip-named** until B-min puts the sort in the drawing), and a dotted-oval render glyph (pure chrome, off by default). Three blessed corpus exemplars: `swan_third_tense` (the withdrawn law as exhibit — present without force; S5 names s4–s7), `forcing_forces` (`(forces s φ)` under the Montague rider — every claim recomputed via the peel/`settlement` before scribing; the trichotomy as trajectory-relative resolution), `peirce_law_commentary` (cross-UoD mention with the real Peirce 1885 citation). |
| Second-order core (stage ① B-min — the authorized core opening) | SHIPPED 2026-07-16 | `egi_core_dau.py` (`sort`/`quotation` maps + `with_sort`/`with_quotation`/`with_quotation_binding`/`without_quotation`), `formal_transformation_rules.py` (`_rebuild_graph`, `_refuse_quotation_boundary`), `second_order_reader.py`, `second_order_limits.py`, `eg_reader.py` (`assign_second_order_marks`, second-order `read_drawing`), `correspondence_attestation.py` (committed-convention checks) → `test_second_order_core.py`, `test_rules_second_order.py`, `test_second_order_reader.py`, `test_second_order_conservativity.py`, `test_use_mention_fork.py` | The one genuine protected-core edit of the crossing (SECOND_ORDER_CORE_OPENING §5 step 2 + §7 build note): sort-on-incidence + graph-valued area as parallel `ρ`-pattern maps (first-order graphs bit-identical); the six Dau rules sort-preserving with the quotation boundary **opaque** (mention, not use — ERA takes the whole exhibit or nothing; DC− refuses a dotted oval as half a double cut; IT± refuse the apparatus; the rebuild also repairs the historical alphabet/rho drop, with the alphabet growing to cover lawful new vocabulary); the committed drawn convention (dotted stroke + sort badge + attachment tie, the `order_label` idiom) held total by §3.3; **S3 (read-back one order up) CHECKED** via the second-order reader on `swan_third_tense`/`forcing_forces` (cross-UoD mention = sort-half + named horizon); the A3 conservativity gate (invisibility / erasure-projection / rules-restraint tiers — the quoted layer licenses nothing); linear generators refuse loudly, corpus surfaces serve the first-order projection + named limit; the use/mention fork's mention half discharged (use = scroll-only, the deferral pinned as a test). Named limits: no linear sort syntax, no quotation-in-quotation, no IT± of exhibits. Next: ② B-full (native element kind, ν-hookable blank). |

---

## J.1 West-in-kytē — *the apportionment program, executed*

The Q-B apportionment / West experiment (doctrine §5) measures one big Arisbe against distributed
kytē plus a coordinator. Design of record: [WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md); what
the harness does and does not establish, §8 of that doc.

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Synthetic vault generator | SHIPPED | `vault_generator.py` → (exercised by the West test suite) | Deterministic, structure-only synthetic vault (folders/notes/cross-links) — the West program's reproducible substrate, seed-parametrized. |
| West measure (cost + K-readers) | SHIPPED | `west_measure.py` → `test_west_measure.py` | `CountingMaterializer`/`TracingMaterializer` (peel-cost instrumentation), `CostBreakdown`/`QualityReading`/`read_quality`, `MemberCostReading`/`read_member_costs`, `PowerLawFit`/`fit_power_law` (the β scaling exponent), `round_robin_buckets` + `link_aware_buckets`, `UCurveReading`/`read_ucurve`. The shared cost/K2/K3/\|M\| vocabulary every West run reads through. |
| West coordinator | SHIPPED | `west_coordinator.py` → `test_west_coordinator.py` | `Coordinator`: the attributed-cell digest protocol federated members report through, a cross-member consistency scan, coverage accounting, and the broker (arbitrates contested cells). The coordination-tax currency E1–E3 measure against. |
| West experiment (E1/E2) | SHIPPED 2026-07-22 | `west_experiment.py` → `test_west_experiment.py`, `test_west_experiment_e3.py` | `run_mono`/`run_fed` — paired monolith-vs-federation runs. E1 (federation vs. monolith): all four priors held, FED ~5.2× cheaper under the size-charging cost meter (the ratio tracks the member count; the K2 parity clause carries no weight — that reader registers no failures here, see [WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md) §8). E2 (size sweep): β_mono 1.277 > β_fed(I) 1.025, a 25× coordinator-scan-discipline cost spread — the program's most durable finding. Drivers `tools/run_west_e1.py`, `tools/run_west_e2.py`, `tools/run_west_e2b.py` (calibration: interior optimum N\*=3). |
| West meta-Agon (E3) | SHIPPED 2026-07-23 | `west_meta_agon.py` → `test_west_meta_agon.py` | The endogenous-partition walk: `split_moves`/`merge_moves`/`slate_moves`, `MemoEvaluator` (memoized cost/quality), `run_meta_walk`/`replay_walk`, the broker-quality gate (`find_biting_regime`/`run_broker_quality`), `assemble_e3_report`. A meta-Agon over folder-bucketings — converges to a granularity, not a unique partition (multi-basin). Driver `tools/run_west_e3.py`. |
| West basin map (E3b) | SHIPPED 2026-07-26 | `west_basin_map.py` → `test_west_basin_map.py`, `test_run_west_e3b_driver.py` | `structured_starts`/`contiguous_compositions`, `map_basins` (steepest-descent walk from every start) + watershed inversion, `distinct_optima`, `assemble_basin_report` (the PM1–PM4 verdicts). Headline: 19 local optima, one dominant 10/1/1 cost family capturing 75% of the attractor mass, PM4's sparsity prior refuted-as-finding. Driver `tools/run_west_e3b.py`. |
| West symmetry-breaking rider (E3c) | DISPOSED 2026-07-27 | `tools/run_west_e3c.py` → `test_run_west_e3c_driver.py` | Pre-registered in the E3b spec §10 (PS1/PS2): does a minimal perturbation of a stranded bucketing escape to the cheap family? **PS1 refuted** (stranding is a positive-measure dear basin; 1 of 3 escaped; optima 19→21); **PS2 held** (the floor twice). See `runs/WEST_E3C_LOG.md`. |
| C-series (community scaling), stages 1–3 | SHIPPED 2026-07-30; re-measured 2026-08-01; channels audited 2026-08-05 | `c_field.py` · `c_membrane.py` · `c_unit.py` · `c_marks.py` · `c_use.py` → `test_c_*.py` (217 tests) | Four communication channels (assert / ask / challenge-corroborate / typify) over a domained law-bearing field; **none discriminates on a law's truth** — the only discriminating mechanism is the silence window. Speaker-variance added 2026-07-30 (`ObserverNoise`) on the author's ruling. **Re-measurement pass (2026-08-01, `docs/superpowers/specs/2026-07-31-net-score-retirement-and-window-re-measurement-design.md`):** `net_score` retired as a *gate* statistic — the property survives unchanged, its docstring demoted to "observability, never a gate" — after five measured inversions (the score rose in both directions of the thing it was meant to gate); the standing rule is no gate decided by comparing hits − misses BETWEEN arms, only within one arm or on the law components with a participation clause. `Unit.attended` (written after the act, per THE_KYTOS.md §1.3) plus a test-side reader over `MarkBoard`/`MembraneLedger` gives the cost component ruling 2's terminal-unit invariance needs, without a new `src/` instrument — an earlier design proposing one (`c_score.py`, a `CostLedger`) was refused on that same doctrine. The cost reading carries a named limit (`tests/test_c_channels.py`'s `_cost_reading` docstring; `src/c_unit.py`'s `corroboration_window` docstring): it sees channel acts and attendance but not the internal work a standing doubt occasions, so the price of patience is "still unmeasured in one respect," named not closed. `corroboration_window` moved 5 → 8, with a uniformity guard (`_assert_uniform_rate`) refusing a community whose units disagree on the rate triple. Headline re-measured figures: GATE 1's live-world net −106 → −185 (exactly the ruling's own predicted sweep row); four-unit scoring preferences 1 → 0 (typification's last foothold gone). **Channel audit (2026-08-05, `runs/RUN_C_AUDIT_LOG.md`):** 23 published arms replayed under `tests/c_channel_probe.py` — calls against mints, then ablation. `Unit.corroborate` is **dead in all twenty arms that play it** (1920–2880 calls, zero mints; `challenge` runs first in the same round and spends their shared once-per-law-ever key), and `Unit.answer` is **live but inert** in 11 of 13 full-community arms (`publish` emits the same content from the same author in the same round). **No published number is falsified** — the baseline pass re-derived each one it touched — but three attributions are: the 45 corroborations are `dispose_challenges` counting distinct foreign challengers rather than a call answered, the K1/K2 repair is carried by `ask` + `adopt` rather than `answer`, and what blocks a fabricated atom is at the asker's end. Both defects (`D-A1`, `D-A2`) are deferred to `src/c_unit.py` as subject-matter, not measurement. Standing discipline: all three measurement harnesses are `@audited()`, so an arm whose channel minted nothing fails instead of printing a null — three declared silences only, and a tripwire that retires the `corroborate` allowlist the moment that method can mint. **The guard covers one of the audit spec's two classes of deadness and is a floor, not a ceiling**: it cannot see a *live-but-inert* channel — which is `D-A2` itself, still in the tree, minting 668 marks that move nothing and passing this guard indefinitely — nor a channel that is never *called*, a third case the spec's own classification does not name (the silence check requires calls > 0 — D-1's defect (4), and `whom_to_ask` is the standing candidate). Inertness is only visible to the ablation pass, which is a driver run and not a suite check. Design: `docs/superpowers/specs/2026-07-28-community-scaling-experiment-design.md`, audit spec `docs/superpowers/specs/2026-08-04-c-series-channel-audit-design.md`; examined in ADVERSARIAL_EXAMINATION VII. |

Evidence: `runs/WEST_E1_LOG.md`, `WEST_E2_LOG.md`, `WEST_E2B_LOG.md`, `WEST_E3_LOG.md`,
`WEST_E3B_LOG.md`.

---

## J.2 Alternatives — *index-over-ink, the deliberation register*

The AlternativeSet serves as an index over real chain steps, not a store of evidence. The record
holds pointers into gate-checked history, re-checked forever. Design of record:
`docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md`.

| Capability | Status | Home (src → test) | Note |
|---|---|---|---|
| Alternative index | SHIPPED 2026-07-26 | `alternative_index.py` → `test_alternative_index.py`, `test_alternative_law.py`, `test_alternative_persistence.py` | `alt_key`, Materiality as a **vector** (never a scalar), `Reception` + a contextualization-adequacy classifier, `AlternativeRecord` (three kinds, each carrying one `{atom, denial}` witness), the bounded `AlternativeRegister` (settle-by-introducing-ink, `rebuild_from_chain`), the **AS1–AS4 law** + its attest hook. No field named `warrant` — that word stays doctrinal, never a code attribute. |
| Alternative trace | SHIPPED 2026-07-26 | `alternative_trace.py` → `test_alternative_trace.py` | The dry-run consequence trace (the PEEL-twin, ruling R-A): a generic slot becomes a defining variable (`*x`, never the string `"None"`), question-pattern exclusion, every emitted atom verification-parsed (count-or-refuse on the unrepresentable), `KyteProfile`, `BoundedRegister` (snapshot/restore like every other standing register). `TRACE_ALTERNATIVES` chain step. |
| Alternative survey | SHIPPED 2026-07-26 | `alternative_survey.py` → `test_alternative_survey.py` | Thin-spot + branch PEEL-twin surveys (the hypothetical/modal survey producers); D-2 (zero-grounded) and D-3 (contested-not-held) reception classes. |
| Producer / consumer wiring | SHIPPED | `semantic_game.py` (`unknown_atoms`, producer) → `attention_economy.py` (`wants_from_alternatives`, consumer) → `test_wants_from_alternatives.py` | The peel's unresolved atoms feed the attention economy as `Want`s; the **temperament dial** governs how eagerly they're taken up (author ruling: a reserved knob, defaults byte-identical). |
| Corpus sidecar | SHIPPED | `alternatives.jsonl` (per-UoD, alongside the chain history) | Attested at the tomos boundary like `quotations.json`; never inlined into the EGI. |
| Exemplar | SHIPPED 2026-07-26 | `swan_alternatives` (via the corpus builders) | De-vacuates the gate's trace+survey recompute obligations — a real chain the AS1–AS4 checks bite on, not a fixture. |

Gate: `test_corpus_polarity_discipline.py`'s recompute obligations (AC1–AC10, the Tasks 5–6
producer→consumer loop) + `test_alternative_loop.py`. Suite state at close: 4232/0.

---

## K. Interfaces / adoption — *the referee, callable from outside*

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
to modify) make up the genuine calculus core. The **actual** list below comes from the source:

`egi_core_dau` · `egi_io` · `hierarchical_index` · `universe_of_discourse` ·
`egi_transformation_history` · `formal_transformation_rules` · `rule_interaction` ·
`subgraph_closure_validator` · `graph_isomorphism_engine` · `ligature_manipulation_rules` ·
`single_object_ligature_detector` · **`correspondence_attestation`** · **`presentation_ops`** ·
**`natural_layout`**.

> **Set history (2026-06-27):** decision (a) **added** the three correspondence enforcers, the
> runtime guards of the central invariant. Decision (b) **removed** the six EGIF/CGIF/CLIF
> parsers/generators as application-level I/O rather than the calculus; the rules don't import them,
> and the corpus round-trip tests in CI guard them instead. Net 17 → 20 → 14. The set's inline
> comments now double as the bedrock note. No separate CODEOWNERS file exists, since it wouldn't
> fire in a solo, no-PR workflow.
