# Current Plan

**▶▶▶ THIS SESSION (2026-06-30, cont. 2) — SCHOLARLY CITATION + BATCH EXPORT (the genuinely-remaining
items in `docs/FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md`).** Author opened the feature doc; first fixed
its Workflow-A example (it stated "if a man is wise…" but transcribed/rendered the cat-on-mat graph) to
work through `~[ (man *x) (wise x) ~[ (rich x) ~[ (happy x) ] ] ]` end-to-end (EGIF/FOPL/TikZ verified
against the live parser + exporter). Then **audited the doc's 10 "Needs Implementation" items against the
current codebase** — most were already shipped (the authentic-Peirce exporter #2, CGIF/CLIF/FOPL parsers
#4, drawing mode #5, the Organon LaTeX-export button #1, fidelity waver #3) or obsolete (Qt-era pseudocode).
The **genuinely-remaining publishing path** (#7 citation, #10 citation-into-LaTeX, #9 batch) was built,
fully additive (core-protection CLEAN — `provenance`/`peirce_latex`/`export_service`/routes are unprotected):
**(#7)** new `src/scholarly_citation.py` — `format_citation` (human author-date line from a CSL record) +
`bibtex_entry` (CSL `type`→BibTeX) + `citation_for` (bundle, prefers `theorem_source`, falls back to
transcribed-proof / method / free-text `source_citation`); **fabricates nothing** (absent field omitted,
sourceless graph → `has_source:false`); self-contained. `GET /export/citation`.
**(#10)** `export_peirce_latex(..., caption=)` stamps the citation as a `\footnotesize` line **under** the
figure — ink *outside* the tikzpicture, so `cut_bounds`/§3.3 are byte-identical with/without it; threaded
through `export_egi(caption=)` + `ExportRequest.cite` + the **"cite" checkbox** in Organon's export panel
(shown only for `peirce-tikz`). (standalone wrapper gains `varwidth=12cm` when captioned so the line wraps.)
**(#9)** `export_service.export_peirce_document` (an **appendix of several UoDs**, one captioned figure each,
reusing the chain-document assembler) + `POST /export/document` (reports skipped ids). **Deferred with
rationale:** Ergasterion export (#1 — drafts have no provenance; export belongs to attested Organon by the
mode contract), handwriting-font/ink-bleed (#3), template library (#6 — corpus+primer cover it), overlay
comparison (#8 — niche). **Tests:** `test_scholarly_citation.py` (11), `test_export_routes.py` +7
(citation route, cited-caption ink-outside, batch+missing), `test_peirce_latex.py` +2 (caption ink-only +
**pdflatex compile** of a captioned doc). All green; UI cite-checkbox verified in headless Chromium; core-
protection CLEAN. Docs: rewrote the feature doc's Required-Features into a reconciliation table + built/deferred
sections + a real cited Example Output; CLAUDE.md module/route entries. [[project_corpus_exemplars_meat_on_bones]].

**▶▶▶ THIS SESSION (2026-06-30) — UI SURFACE for the modal-query lens + the M-revision dialogue
(the open follow-up from the exemplars session).** The `modal_query` (◇/□) and `model_revision`
(M-through-dialogue) modules shipped backend+corpus only; this session surfaces both in Organon as two
read-only **diachronic reading lenses**, fully additive (core-protection CLEAN). **(1) Modal lens** —
new `GET /organon/uods/{id}/modal` (geometry-free, `attest=False`) reads ◇/□ off a UoD's chain via
`modal_query`: every relation scribed across the reachable sheets is classified □ Necessary (on every
sheet) / ◇ Possible (on some), with the worlds the modality ranges over and a `states`/`leaves` toggle;
`web_viewer/js/modal-lens.js` draws the two columns + worlds strip + the "necessity is convergence,
possibility is branching" footer. Verified on `possible_and_necessary`: □cold, ◇cloudy/◇calm.
**(2) Audit lens** — new `GET /organon/uods/{id}/audit` peels a standing proposal G against every
successive model M in the chain (materialize + `CorpusOracle(closed)` + `semantic_game.evaluate`, mirroring
the build script's `_verdict`), returning the verdict at each state; `web_viewer/js/audit-lens.js` draws
the **verdict ribbon** with each transition labelled by the admitted fact and "verdict flips" flagged.
The proposal defaults to the UoD's **declared `audit-proposal` annotation** (added to
`build_dialog_model_evolution.py`; re-seeded `dialogue_model_revision` — only `annotations.json` changed,
id-churn reverted) or any EGIF the reader types. Verified: FALSE→TRUE→FALSE→TRUE. Both lenses wired into
`organon.html`'s `#view-lens` (offered for any chain), `lens-common.js` got `fetchModal`/`fetchAudit`.
**Tests:** `test_organon_routes.py` +8 (modal reading/leaves/synchronic/unknown; audit default-flip/explicit/
NO_PROPOSAL/AUDIT_ERROR), `test_organon_lenses_e2e.py` +2 (modal □/◇ columns + leaves toggle; audit ribbon +
pre-filled proposal + flips). All green; lenses E2E 10/10; core-protection CLEAN.
**THEN (same session, author's mid-task ask): the EPG inning-outcome taxonomy now informs the
Domain-Model-revision examples.** `model_revision` enacted only `new_fact`/`retract_fact`; broadened to the
whole M-revising subset of the disposition taxonomy. New **`REVISION_TAXONOMY`** (the subset that *transforms
M*, each carrying its **Peircean mode** induction/deduction/abduction/convention + structural **kind**
enlargement/relinquishment): `new_fact`(3a), `generalization`(Case 8), `conditional_acceptance`(3e),
`abductive_hypothesis`(3b), `definition`(3d), `reductio`(2d), `theorem_registration`(1a), `challenge_to_M`(2b).
New primitives `add_rule` (enlarge by a law) + **`retract_subgraph`** (relinquish a sheet-level law/cut by a
*genuine Dau ERA*, verified by reconstruction — the structural generalization of `retract_relation`);
`revise_with_disposition` dispatches all of them; `revision_taxonomy(key)` rejects the non-revising
dispositions (`redundancy`/`rejection`/…). New exemplar **`dialogue_swan_revision`**
(`tools/build_swan_generalization.py`) — the guide's own swan/black-swan story, walking **all three modes**:
FALSE→TRUE→TRUE→TRUE→FALSE as induction observes Ciel + leaps to the law *all swans white*, the law **absorbs a
newcomer** (Dover stays TRUE where insurance's Cal flipped FALSE — deduction over an inductive law vs a bare
tally), then abduction meets the black swan Nox and **relinquishes the over-general law**. The **audit lens**
now shows each transition's **disposition · mode** (endpoint frame carries `disposition`/`mode`/`fact`).
**Tests** `test_modal_and_dialog.py` +6 (taxonomy modes/kinds; non-revising rejected; add_rule↔retract_subgraph
round-trip; law-covers-newcomer; challenge relinquishes+admits; swan walk) and `test_organon_routes.py` +1
(audit surfaces disposition/mode). All green (60 across organon+modal/dialog+exemplars); core-protection CLEAN
(model_revision additive, not protected). Docs: EXEMPLARS §6 (swan table + taxonomy + audit-lens), CLAUDE.md
module entry. [[project_corpus_exemplars_meat_on_bones]]. **▶ NEXT:** open author decisions unchanged
(reference-node increment 2, 2nd-order frontier #13); the modal/dialogue exemplars now have a UI surface and
the M-revision examples now span the inning-outcome taxonomy.

**▶▶▶ THIS SESSION (2026-06-29, cont. 5) — CORPUS EXEMPLARS: "meat on the bones" (foundation batch).**
Author asked for more loadable exemplars — proofs, Endoporeutic-Game innings, domain models (≥1 needed to
play at all), diachronic-branching/modality demos, and M-transforms-through-dialog. Decided **foundation
first** (proofs + domain models now; modality + dialog with the *thin missing code* in a second pass, after
review). Mapped the machinery with 3 parallel Explore agents (proof-chain build pattern; EPG + domain models;
diachronic DAG + modality) — key finding: branching DAG persists today but the modal □/◇ *query* and active
M-revision are conceptual, hence the two-pass plan. **SHIPPED this turn (all verified, additive):**
**(1) Four propositional proof exemplars** (`tools/build_propositional_exemplars.py`, real `ProofChain`s):
`de_morgan` (DC+×2 — disjunction is the double-cut law), `contraposition` (one DC+ — P→Q and ¬Q→¬P are the
*same graph*), `ex_falso_quodlibet` (INS — explosion, insertion only legal in a negative context),
`hypothetical_syllogism` (IT+/IT−/DC−/ERA/ERA — the meaty transitivity proof). **Together they exercise all
six Dau rules.** Each verified to build to its conclusion (`same_graph`), §3.3-attests at save, and replays
soundly from disk. **(2) Two domain-model boards** (`tools/build_domain_model_exemplars.py`, `kind=domain_model`
standalone UoDs): `zoo_world` (closed Horn taxonomy — materializes dog→mammal→warm-blooded, so "every dog is
warm-blooded" holds via the chain and "every warm-blooded thing is a mammal" fails naming **Pip** the sparrow)
and `harbor_town` (open civic world — "Bayside hosts a market" reads UNKNOWN/independent). Both load + §3.3-attest;
both appear in the Agon picker's corpus list. **(3) Picker wiring:** three curated `ExampleModel` innings
(`zoo-chain`/`zoo-refuted`/`harbor-open`) in `src/agon_models.py`; added a `materialize` field to `ExampleModel`
(a board that is a *theory* forward-chains its Horn rules before the peel) threaded through `/agon/models` +
`agon.html` (sets the existing materialize checkbox on example-pick) + the existing route test.
**Tests:** new `tests/test_new_exemplars.py` (16) — proofs build to conclusion + all-six-rules + low-warrant
provenance; domain models materialize + peel to advertised verdicts; innings present + peel as promised.
Updated `test_agon_interpretation.py`'s enumerate-all-examples test (+3 verdicts, passes `materialize`).
**Doc:** `docs/EXEMPLARS.md` (catalogue + a "second pass" section). Spine: CLAUDE.md Key Documentation.
**SECOND PASS (same session) — SHIPPED, additive, with the thin missing code (author pre-approved).**
**(a) Modality as diachronic branching:** `src/modal_query.py` (NEW) reads ◇/□ off the branching DAG — the
*trajectory reading* of MODALITY_WITHOUT_GAMMA §1 (worlds=sheets, R=legal transitions): `possibly`/
`necessarily` over `reachable_states`/`leaf_states`, predicate helpers `scribes_relation`/`equals_graph`/
`is_blank`, `over="states"|"leaves"`. Geometry-free, no §3.3 obligation. Exemplar `tools/build_modal_branching.py`
→ `possible_and_necessary` UoD: from `(cloudy)(cold)(calm)`, two legal ERA lines drop a feature and converge on
`(cold)` — □cold (necessary=convergence), ◇cloudy/◇calm (possible=branching, not □). Built/attested; query reads
it correctly. (The *alethic* reading ◇/□-across-models is already `/agon/where-it-holds`.) **(b) M transforms
through dialog:** `src/model_revision.py` (NEW) — `assert_fact` (enlargement = a `new_fact` posit juxtaposed onto
M's sheet, low warrant) + `retract_relation` (relinquishment = ERA dual, free to demote) + `revise_with_disposition`.
Exemplar `tools/build_dialog_model_evolution.py` → `dialogue_model_revision` UoD: standing proposal "every patient
is insured" peeled after each revision **flips FALSE→TRUE→FALSE→TRUE** as the dialogue admits Ben's insurance, a
new patient Cal (unsettles it), then Cal's coverage — M persisted as its own diachronic history (steps =
`apply_derived("ADMIT_FACT")`). **Tests:** `tests/test_modal_and_dialog.py` (12). **Doc:** EXEMPLARS.md §5+§6
rewritten from "what's next" to shipped. Both new UoDs load+§3.3-attest. CLAUDE.md module map += modal_query +
model_revision. core-protection CLEAN (both modules additive, not in the protected set).
**▶ NEXT (open):** the corpus now has read+play+modal+dialogue exemplars across Organon/Agon; remaining author
decisions unchanged — reference-node increment 2 (cross-UoD, ROADMAP #3), second-order frontier (#13). A thin
*UI surface* for the modal-query lens / the M-revision dialogue could be a follow-up if wanted (currently
backend + corpus only). [[project_corpus_exemplars_meat_on_bones]].

**▶▶▶ THIS SESSION (2026-06-29, cont. 4) — DOCS: shipped ROADMAP #15 + #16 (two consolidating docs;
no code).** Author asked to beef up documentation per #15 and #16. Both were *documentation* tracks; both
now done, additive, links-out-not-restate, in the established spine voice.
**#15 → `docs/GETTING_STARTED.md`** — the written, role-aware on-ramp the in-app primer/Field Guide lacked
a companion for. Structure: §0 three-sentence what-it-is → §1 a **shared "five minutes"** (run it with
`uv sync --extra dev --extra web` + uvicorn; the three modes as a table; first graph two ways — read
`peirce_cp_4_394_man_mortal` in Organon / draw dragon `🐉1` in challenge mode; the *attest correspondence
not truth* discipline) → §2 a **door per reader** (newcomer / ontologist / logician / mathematician / Peirce
scholar), each with *what to read first · do first · your honest frontier* → §3 the contributor pointer →
§4 a one-screen door map. Assumes **no logic/math** at the entrance, branches by expertise the way
VISION_AND_SCOPE / GLOSSARY do.
**#16 → `docs/EXTERNAL_SOURCES_AND_IMPORT.md`** — the consolidating import map (the machinery was scattered
across CORPUS_AND_IMPORT_MODEL, MANIFEST_AND_MEANING, IMPORT_EXPORT_FORMATS, the OWL/RDF importers,
`cl_import_resolver`). Structure: §1 the **low-warrant floor** (attest correspondence not truth; provenance
outside §3.3; no fabricated citation) → §2 the **two families** (formal files vs human-read material) → §3
family A (T-box axiom→EG-shape table; the OWL/RDF/SUO-KIF/CLIF/COLORE→CLIF→EGI paths; the honest
skip-report + function-relationalisation; closing the loop with `theory_query.entails` import-as-M) → §4
family B (`/import` linear-form doorway with citation; NL→logic "LLM proposes, Arisbe disposes"; the future
reading desk) → §5 the **tool/module map** table → §6 forward edges → §7 one-paragraph summary.
**Wired into the spine:** ROADMAP #15+#16 marked ✅ DONE; VISION_AND_SCOPE front-matter "New here?" pointer;
GLOSSARY reading-order new "New user, just arriving" entry; CLAUDE.md Key Documentation (two new bullets).
**Verified** every cross-reference resolves (7 linked docs exist, `/agon/propose-nl` + `/import/*` routes
exist, `domain_model_importer` exposes `from_owl/from_clif/from_rdf_*`, the `peirce_cp_4_394_man_mortal`
corpus id is real). No code, no tests touched; core-protection untouched (docs only).
[[project_tidyup_tracks_post_reference_node]]. **▶ NEXT:** the tidy-up tracks (#14–16) are now all done;
the open author decision remains **reference-node increment 2** (the cross-UoD use/mention fork, ROADMAP #3),
the named research frontier being second-order logic about the graphs (#13).

**▶▶▶ THIS SESSION (2026-06-29, cont. 3) — FINISHED ROADMAP #14 (d): the drawing→EGI learning loop. #14
COMPLETE.** After committing+pushing phases 1+2 (`cf79974`), built (d). New `src/layout_learning.py` +
`tests/test_layout_learning.py` (6 green): `arrangement_deltas(egi, canonical_dto, drawn_dto)` recovers the
regime-3 `PresentationDelta`s carrying Arisbe's canonical layout to a human-drawn arrangement of the *same* EGI
(the **inverse of `presentation_deltas.apply_deltas`** — move_vertex/predicate/cut + reshape_cut, each tagged by
`describe` for generalization); `generalize_arrangement` is the loop-closing pass-through to `extrapolate_deltas`
(crystallise the learned placements onto untouched siblings → a refined Peirce-style regularity). This makes the
replica-then-parse signal (journey 2) into the codebase's delta currency — reads only regime-3 facts so it's
correspondence-safe, and replay re-attests §3.3. Tests build a §3.3-valid "drawn" arrangement by replaying known
moves onto canonical, then verify recovery (vertex/predicate/cut reshape), no-op on identical layouts, exact
round-trip, and sibling generalization. Adjacent `test_presentation_deltas` (25 total) green; core-protection
CLEAN; additive. **#14 (LaTeX export for the Peirce Edition Project) is now fully done — phases 1+2+(d).** Only a
thin UI surface remains optional (an Ergasterion route feeding the freeform canvas's drawn DTO into the loop; a
session-export convenience route). Docs: ROADMAP #14 → complete; CAPABILITY_MAP; CLAUDE.md module+test entries.
[[project_tidyup_tracks_post_reference_node]].

**▶▶▶ THIS SESSION (2026-06-29, cont. 2) — BUILT ROADMAP #14 phase 2 (3 of 4 items): iconic scroll glyph,
worked-chain LaTeX document, HTTP route deltas.** Author picked (a)+(b)+(c), then asked to finish (d) too.
Done lowest-risk-first. **(c) route deltas** — `ExportRequest.deltas` (JSON `PresentationDelta` shape) +
`scroll_glyph`; the route converts via `deltas_from_list` (→ `BAD_DELTAS` on a malformed item) and threads into
`export_egi(deltas=…)`; `export_egi` gained the `deltas`/`previous_layout`/`scroll_glyph` params. So the PEP
transcribe-then-tune path works over HTTP, not just the Python layer (found `parse_egif` ids are *randomized per
call*, so the route deltas test is driven from a corpus UoD whose stored ids are stable). **(b) worked-chain →
multi-figure LaTeX document** — `export_peirce_chain(chain)` lays out the initial state + each step's result
(each §3.3-attested), renders via `export_peirce_latex(standalone=False)`, and `export_peirce_chain_document`
assembles one `article` doc (macros inlined once) with a captioned figure per step (rule + Peirce label +
description); `POST /export/chain` (`ExportChainRequest`, → `CHAIN_NOT_FOUND`). Verified visually: `beta_modus_ponens`
renders as a titled derivation — initial P⊃Q scroll+P, then IT− deiteration, then DC− leaving Q—P. **(a) iconic
self-continuing scroll glyph** (the hard "do better than egpeirce" win — Jukka admits PSTricks scrolls "look
awful") — opt-in `scroll_glyph=`; for a detected scroll `~[A ~[B]]` the outer cut is drawn as an oval with a
downward **neck that crosses itself and wraps over the inner oval**, the inner loop nestling in the neck (verified
visually on `~[ Man ~[ Mortal ] ]`). **Crucially ink-only:** it changes only the stroke, never `cut_bounds`, so
§3.3 + `read_drawing` validate exactly as before (the same discipline as the hand-drawn waver and the crossing
bridges) — faithfulness holds with the glyph on or off. Default off keeps the robust nested-oval baseline.
**Tests +13** (`test_peirce_latex.py` 51, `test_export_routes.py` 13): scroll-glyph opt-in + ink-only-faithful +
compiles; worked-chain assembles (one figure per step, names every rule) + compiles; route deltas (effect +
malformed rejection) + chain route (+ CHAIN_NOT_FOUND). core-protection CLEAN; additive only. **Deferred: (d) the
drawing→EGI learning loop** (parsed-replica deltas → presentation-deltas/style ladder) + a session-export
convenience route. Docs: ROADMAP #14 phase-2 SHIPPED; CAPABILITY_MAP; CLAUDE.md. [[project_tidyup_tracks_post_reference_node]].

**▶▶▶ THIS SESSION (2026-06-29, cont.) — BUILT ROADMAP #14 phase 1: the authentic-Peirce LaTeX/TikZ export
path for the Peirce Edition Project.** Author chose #14 first of the three tidy-up tracks. **Discovery:** a
*geometric* Dau/Sowa TikZ exporter already existed (`tikz_export.py`, wired into `/export`), but its docstring
said the **authentic-Peirce path is a separate exporter** never built. Author's brief, refined across the session:
replicate the *function* of Jukka Nikulainen's `egpeirce.sty` (oval cuts, scrolls, heavy lines of identity, hooks)
but with a **modern, robust, widely-supported, easier-to-use** implementation — **pure TikZ, plain pdflatex, no
PSTricks** — *not bound to egpeirce's spec, improving where we can* (Jukka admits its limits); and **CRITICAL:
stay wedded to the logic of an EGI** (egpeirce is pure typesetting with no model underneath — Arisbe's edge is
the LaTeX is *generated from* the §3.3-attested EGI, so the printed picture provably denotes the same object).
Author also enriched the design with the **PEP use cases**: (1) transcribe-then-tune (write a journal graph's
EGIF, Arisbe draws it, scholar **adjusts within the logic** — regime-3 deltas — to match Peirce's page, then
exports) and (2) replica-then-parse (draw a Peirce-style replica → parse to EGI; the drawing→EGI layout deltas
that differ from Arisbe's canonical output are *a learning experience* feeding the Peirce-style spec). So export
must be **delta-faithful** ("export what you adjusted to see"). **The load-bearing design decision:** draw at the
**§3.3-attested `LayoutDTO`'s own coordinates** — ovals at `cut_bounds`, heavy lines from `vertex_positions` to a
hook on the `predicate→points[0]` ray (which **preserves the hook angle** the reader keys argument order off) — so
the picture *is* the DTO and the existing reader (`eg_reader.read_drawing`+`reading_matches_egi`) vouches for it,
**correspondence for free, no new prover**. **SHIPPED (additive; core-protection CLEAN):** `src/tex/arisbe-eg.sty`
(a modern, hand-authorable semantic TikZ macro package — the egpeirce replacement: `\egcut`/`\egloi`/`\egdot`/
`\egpred`/`\egconst`/`\egnum`, key-value `\egset`, no PSTricks), `src/peirce_latex.py` (`export_peirce_latex(dto,
egi)` — oval cuts in nesting order with parity shading; **branching** heavy lines of identity grouped by vertex
with a branch dot at teridentities; hooks trimmed to the predicate label-box edge on the angle-preserving ray;
bridges at crossings reusing `render_geometry`; argument-order numerals honoring `order_label`; constants from
`rho`; scroll **detection**→annotation with nested ovals; TeX-escaping; standalone inlines the `.sty` with
`article` fallback for minimal installs), and wiring in `export_service.py` (new `peirce-tikz` format forcing the
oval style; `export_egi` gained `deltas`/`previous_layout` pass-through for the PEP path). **Tests
`tests/test_peirce_latex.py` (47 green):** corpus-wide totality+traceability over all 29 UoDs (every id in the
`.tex`, macro counts match); reader-faithfulness on a representative subset + a falsifier (doctored DTO reads back
different — the check has teeth); **actual pdflatex compilation** of a curated 6 (alpha double-cut, beta
teridentity, scroll, isolated vertex, empty cut, TeX-special `under_score` name); the PEP delta path; format/route
wiring. Verified visually: `(Human *x) ~[ (Mortal x) ]` → a shaded **oval cut** with italic "Mortal" inside and a
continuous **heavy line of identity** from "Human" on the sheet bending into the cut — recognizably authentic
Peirce, ∃x(Human(x) ∧ ¬Mortal(x)). Honest reader limit surfaced + documented: dense ontologies (`bfo_core`,
`skos_core`) don't fully read back — a reader-heuristic property, **not** the exporter; §3.3 still attests them
(covered by the corpus tier). Updated the existing `test_export_routes` format-set assertion. **Phase 2 deferred
(flagged):** the iconic self-intersecting `\egscroll` glyph (via the DTO `cut_boundary` so the reader still
validates — where egpeirce admits defeat); a **worked-chain → multi-figure LaTeX document** (the "and likely a
worked chain" clause); an HTTP route-level deltas field / session-export convenience; the drawing→EGI **learning
loop** feeding the presentation-deltas → style ladder. Docs: ROADMAP #14 → phase-1 SHIPPED; CAPABILITY_MAP row;
CLAUDE.md module + test entries. Plan file: `~/.claude/plans/fluffy-seeking-hartmanis.md`.
[[project_tidyup_tracks_post_reference_node]].

**▶▶▶ THIS SESSION (2026-06-29) — DE-RISK: prototyped the reference/transclusion-node *validation harness* (ROADMAP
#3, the precursor before touching the protected core). SUCCESS.** Author's framing: "prototype the validation
harness; if successful we dig into the reference/transclusion node." Built it **read-only, no protected-core change**:
`src/reference_resolution_check.py` + `tools/run_reference_resolution_check.py` + `tests/test_reference_resolution_check.py`
(11). It is the analogue of `attest_overview` for the reference contract — §12 decision 3 named the law,
**RESOLVE ≡ INLINED-AND-ATTESTED**. Per candidate: **R1** resolve-equals-inline (`same_graph(resolve(), inlined)` —
the heart), **R2** resolved-is-§3.3-attested (`attest_correspondence` on the resolved graph; `layout_fn` injected so
the pure module imports no geometry), **R3** recoverable (`same_graph(refold(resolve()), host)`, only when an inverse
exists), **R4** honest horizon (unresolved names reported, never silently dropped — informational). **The insight that
made it cheap:** the reference node already exists in miniature in **unprotected** code — `definitions.py` (a defined
edge → a body elsewhere; `expand`/`expand_at` resolve, `fold` is the exact inverse, `test_definitions.py:65` already
proves expand recovers an independently-authored raw fixture). Transclusion (b) = the generalization (reference another
UoD/module by name+provenance); identical law, only *where the body comes from* differs (registry vs corpus/text-assembly
— exactly how `cl_import_resolver` works). **Result: PASS on every real candidate** — definition references (Power Set:
full R1+R2+R3; Infinity: multi-reference whole-graph expand) **and** a transclusion reference (inter-graph cl-imports
model that names its `no_such_module` horizon). **Falsifiers bite** (R1 doctored-inline, R3 lossy-refold, R2
rejecting-attest, resolve-raises) so the PASS is earned; the real-ELK §3.3 path runs (not skipped). Core-protection
CLEAN; 11/11 green; `test_definitions` (15) green. **What it tells the author for the (b) decision:** the law is
representation-independent (it holds with the reference modeled *out of core*), so first-class-element-hood is needed
only for *drawing the glyph + §3.3 totality over it*, **not** for correctness of resolution; `attest_reference` is just
"resolve, then ordinary §3.3 on the resolved EGI" (no new §3.3 machinery); and **recoverability is a real asymmetry** —
definitions have a clean local inverse (`fold`), transclusion does not (R3 N/A, surfaced in `honest_limits`). The three
§12 decisions (form / calculus-entry under level-0 / attestation contract) are now ready for the author. Docs: ROADMAP
#3 → "law DE-RISKED"; [[project_reference_node_validation_harness]]. **Then (same session) the author chose to lay
out the three §12 decisions and took them — new design-of-record `docs/REFERENCE_AND_TRANSCLUSION_NODE.md`:** Form =
**Form 2, a relation-shaped reference *edge* generalizing the definition node** (resolve=`expand`/`fold`; §3.3 already
covers it as a predicate — zero §3.3 change; Form 1 = new element kind rejected as highest-cost, Form 3 = overlay kept
as a cheap legibility *complement*, not a substitute). Calculus entry = like a definition, conditioned in a cut
(level-0 clean), LOW warrant. Attestation = `attest_reference` = the harness R-checks. Timing = **additive-first, core
later** (author's call): increment 1 touches NO protected module (generalize resolver `DefinitionRegistry`→corpus-UoD-by-name
via `TomosService.load_uod`; reference-ness + provenance in the overlay; reference glyph style-only; `attest_reference`
at the serve boundary). **The author asked whether this choice helps/hurts the 2nd-order frontier (ROADMAP #13) later —
answer: BETTER, banked as an invariant.** definition/schema/reference are ONE family (relation-shaped, port-bearing,
`eg_splice.splice`-resolved); schema.py's "metalevel generator + expansion-to-instances" soundness dodge IS the harness
law, so Form 2 inherits it; Form 1 would force a later 3-way reconciliation. Invariant to preserve: keep references in the
splice/port/expansion family + the abstraction hook (foldable/abstractable, nameable by a line of identity). Honest scope:
*alignment* (one mechanism to extend), NOT *advancement* (no in-logic 2nd-order quantification — schema.py dodges that).
Docs cross-linked from ROADMAP #3 + THE_MINIMAL_IN_VIEW_SET §12. **Then (author said "Proceed") BUILT increment 1a —
the reference-node logic layer, fully additive, core-protection CLEAN:** new `src/reference_node.py` (a Form-2 reference
edge + an OVERLAY `ReferenceMark` keyed by edge id carrying target/kind/origin/`warrant="low"`, kept beside the EGI so
`egi_core_dau` is untouched; the `ReferenceResolver` Protocol shaped like `cl_import_resolver.ImportResolver` with
`DefinitionReferenceResolver` (resolution = `expand_at`, inverse = `fold`) + `ChainReferenceResolver` so schema/UoD
resolvers drop in additively; `mark_reference`/`resolve_reference`/`refold_reference`/`attest_reference` boundary hook
building a `reference_resolution_check.Reference` and attesting R2+R3) + `tests/test_reference_node.py` (11: mark
round-trip, refuse-unresolvable=R4, resolve=raw fixture=R1, refold=host=R3, boundary hook bites on doctored inlining,
chain dispatch, real-ELK R2). 22 green (node + harness); `test_definitions`+`test_schema` (34) green; core-protection
CLEAN. At a production boundary R1 is trivial (no independent inlining) so R3 carries the round-trip weight; R1-vs-ground-truth
is the offline proof in tests. **Then (author "Proceed") BUILT increment 1b — the render glyph**, additive, core-protection CLEAN: `simple_svg_renderer`
(unprotected) gains an optional `reference_marks={edge_id: horizon}` param → a marked predicate spot draws with a **dashed
accent box** + a **"+N beyond view"** badge (`reference_node.reference_horizon` = spliced-body size; `render_marks` builds
the map). Pure chrome — reads the overlay, never the EGI, changes **no DTO geometry**, so §3.3 (which reads the DTO) is
untouched; default `None` byte-identical. +3 tests (`test_reference_glyph.py`: horizon>0, glyph drawn only when marked,
geometry unchanged). 25 green (glyph+node+harness); **95 corpus-wide §3.3/render/organon/layout-service tests green**
(2.5 min ELK run) confirming zero regression; core-protection CLEAN. Wiring `layout_service`/web routes to *supply* marks
is a thin follow-on (no UI authors references yet). **Increment 1 (1a+1b) COMPLETE. NEXT = increment 2: cross-UoD as the
use(scroll-import)/mention(2nd-order-naming) fork (§7) — an author decision (the use branch = governed import; mention =
the 2nd-order frontier).** Docs: REFERENCE_AND_TRANSCLUSION_NODE §5 → 1a+1b SHIPPED. [[project_reference_node_validation_harness]],
[[project_minimal_in_view_set]].

**▶▶▶ THIS SESSION (2026-06-28, cont. 4) — UX: shipped (#4) stage 2(a), the plain-English authoring door — the
on-ramp (#4) is now COMPLETE.** The NL→logic front-end (`POST /agon/propose-nl`, `src/nl_to_logic.py`: *LLM
proposes, Arisbe disposes*) was fully built and route-tested but had **no UI** — a non-logician could read a lit
verdict but still had to hand-author EGIF to *author* a G. **Shipped (purely additive — `agon.html` only; core-
protection CLEAN):** a **"…or describe G in plain English — Arisbe drafts the graph"** textarea + **✶ Translate
to a proposal G** button in Agon's setup, just above the Proposal G field. `proposeNL()` posts the description
with the chosen M (whose signature hints the translation) → `renderProposeNL()` fills `#setup-proposal` from the
drafted EGIF and shows the **reading** (`read as <FOL>`), the **drafted G** (`→ filled below; review it`), and —
the distinctive value — the **vocabulary-miss** (terms M can't even address, "not even wrong in this model",
maroon) made legible *as distinct from* the **fact-miss** (the peel's verdict, shown as "in M this reads
TRUE/FALSE/UNKNOWN — press 'Does G hold in M?' for the peel"). Honest non-results render fail-soft, never as an
error: an `unmappable` sentence → "Can't be said as a first-order graph — <reason>"; a malformed candidate →
"Couldn't form a graph from the draft — <reason>"; an **absent translator** (no SDK / no key on the server) →
"The plain-English translator isn't available on this server — type the proposal G as EGIF below instead." The
button requires M chosen first (consistent with `interpret()`; M's vocabulary is the translation hint). Nothing
is asserted — a proposal is at LOW warrant, earning warrant only by withstanding Agon. Tests: +2 Agon E2E
(`test_plain_english_door_drafts_a_proposal` — happy path: fills G + shows reading + "every term is in M's
vocabulary" + TRUE; `test_plain_english_door_surfaces_the_vocabulary_miss` — the vocab-miss surface), both
**network-stubbed** (`page.route` fulfills `/agon/propose-nl`) so the wiring is tested deterministically without
the live LLM. 14 green across the propose-nl route + Agon E2E suites; core-protection CLEAN. Verified visually
(headless Chromium, network-stubbed): the field, the translate button, the reading (`read as ∀x (mammal(x) →
warmblooded(x))`), the green "every term is in M's vocabulary", the TRUE fact-side reading, and the auto-filled
Proposal G all render faithfully. Docs: ROADMAP #4 → **DONE** (all three stages shipped), CAPABILITY_MAP +
plain-English-door row → SHIPPED. [[project_next_cross_mode_ux_coherence]], [[project_nl_to_logic_arisbe_as_interpretant]].

**▶▶▶ THIS SESSION (2026-06-28) — UX: shipped (#5) the Context-reflex overlay docking (auto-dim-on-overlap).**
The reflex panel floated absolute top-left over every board and could occlude a left-heavy / frame-filling
drawing. Chose **auto-dim-on-overlap** (over dock-as-column / leave) — the only option that is uniform across
all three modes with no per-mode layout surgery and **zero regression** when there's no overlap. All in
`web_viewer/js/context-reflex.js`: the panel watches the drawn extent (the `.svg-pan-zoom_viewport` group's
screen rect — the same measure `DiagramViewer._contentFitsViewport` uses) and toggles `cx-occluding` when the
*open* panel overlaps it → the panel recedes to a faint "Context" chip and its body becomes **click-through**
(`pointer-events:none`) so nothing under it is unreachable; **hover/focus** (`cx-peek`) restores it in full.
Because `fit`+`centre` leaves margins, the picture only reaches the top-left corner when it is genuinely large,
so a small/centred drawing leaves the panel untouched. Re-tested on render, on camera changes (wheel-zoom /
pan-drag end, rAF-coalesced) and on resize; opacity/background only, so the overlap test never oscillates.
Exposed `recomputeOcclusion` / `_rectsOverlap`. Tests: +2 in `test_context_reflex_e2e.py` (the `_rectsOverlap`
logic on every mode page + a deterministic synthetic-host occluding/peek check); all 5 green, adjacent
Agon/Organon E2E (13) green, core-protection CLEAN. Verified visually (headless Chromium): dimmed → faint chip
+ drawing shows through; peek → full ground panel back. Docs: ROADMAP #5 → DONE, WEB_VIEWER_DESIGN §5 +
docking paragraph. [[project_context_reflex_built]], [[project_next_cross_mode_ux_coherence]].

**▶▶▶ THIS SESSION (2026-06-28, cont.) — UX: shipped (#2) the render-M UI (ground/legend + relevant-neighborhood
M-render).** The Agon interpretation register drew only G; M sat as a wall of raw EGIF text. Now M is *drawn*,
read-only (M never asserted — the "fourth thing"). New pure module **`src/m_render.py`**: `vocabulary_overlap`
= **(d) the ground/legend** (how G's and M's vocabularies meet — shared / G-only = the addressability gap /
M-only = context beyond G) and `m_fragment` = **(c) the relevant-neighborhood** (the part of M G *touches* —
seed = M's sheet atoms whose relation/individual G uses, then one hop along the same individual or line of
identity, budget-capped ~8, the rest reported as a **horizon** "+N more facts beyond view"; materialized
forward-chained facts render too; empty when M's vocabulary is alien). Wired into `_interpret_payload` as a
`render_m` block (the caller renders the returned fragment EGI through the ordinary `generate_layout` path; the
module stays web/layout-free so it's unit-testable); drawn in `agon.html`'s reading strip (the legend chips +
a small M-fragment board mounted via a fresh `DiagramViewer`). Decisions: kept M-rendering purely additive +
fail-soft (any error degrades to legend-only / text-only, never breaks an inning); rendered the *materialized*
facts when materialize is on. Tests: `test_m_render.py` (6 unit), `test_agon_interpretation.py` (+3 route:
legend+fragment, empty-alien, materialized facts drawn), `test_agon_e2e.py` (+1 browser: legend text + the
`#m-frag-board svg` mounts beside G). 74 green across render-M/agon/semantic suites; core-protection CLEAN;
additive only. Verified visually (headless Chromium): the strip shows "Model M — what your terms mean here",
the touched-fragment board, and "M can speak to: …" chips; the empty case reads "M says nothing about your
terms." Docs: ROADMAP #2 → DONE, CAPABILITY_MAP render-M → SHIPPED, THE_MINIMAL_IN_VIEW_SET (c)+(d) → BUILT,
CLAUDE.md module + test entries. [[project_minimal_in_view_set]], [[project_domain_oracle_and_m]].

**▶▶▶ THIS SESSION (2026-06-28, cont. 2) — UX: started (#4) the newcomer on-ramp — the corpus is now a source
of *proposals*, not only of models (Organon → propose-as-G into Agon).** Brought options to the author per the
"start with design" note; the author **reframed the arc**: a newcomer's journey is **Organon → Ergasterion →
Agon**, and "a proposed Graph G can be **picked from Organon** or composed in Ergasterion" — so the first,
highest-value slice is making the *carry-a-G flow* work (audience: "both, in sequence" — plain-English / notation
learning comes later). Found a concrete **asymmetry**: Organon's single "⚔ Use in Agon" hardcoded the graph into
the **M (model)** slot (`/agon?model_egif=…`) — the corpus could only ever supply a *model*, never a *proposal*,
directly contradicting the author's framing. **Shipped (additive, `*.html` + 1 E2E only; core-protection CLEAN):**
**(1)** split Organon's action into two roles — **"⚔ Propose in Agon"** (→ `?proposal_egif=…`, the graph becomes
the proposal G; PRIMARY, the learner's path) + **"⚖ as model M"** (→ `?model_egif=…`, the prior behavior, kept).
`ITEM_ACTION_IDS` enables both when a UoD is open. **(2)** generalized Agon's incoming-handoff status to name the
real origin mode (a G can now arrive from Organon, not just Ergasterion). **(3) fixed a real bug found en route:**
Agon's "land on a worked example" default (`loadModels`→`onPickModel`, 2026-06-26) is **async**, so its awaited
`onPickModel()` silently **clobbered** an incoming `?proposal_egif`/`?model_egif` the URL-handoff IIFE had just
set — a carried G/M was overwritten by the default example. Guard added: skip the auto-land when the URL carries a
hand-off (the deliberate carry wins; empty arrival still lands on the example). Tests: +1 Organon E2E
(`test_propose_in_agon_carries_the_graph_as_proposal_g` — clicks the real button, asserts `?proposal_egif=` +
`#setup-proposal` prefilled / `#setup-model` empty for propose; `?model_egif=` + `#setup-model` prefilled for
model). Organon-lenses E2E (8), Agon E2E (7, incl. the worked-example landing + origin-ground handoff), Agon
route+interpretation+Organon route (60) all green; core-protection CLEAN. **NOT done (the rest of #4):** the
notation-learning on-ramp (guided "first graph" / in-app Field Guide) and the plain-English authoring door
(surface the *already-built but UI-less* `/agon/propose-nl` / `nl_to_logic.py`) — these are stage 2 ("both, in
sequence"). **Then mirrored the same two verbs in Ergasterion** (author-approved): "Send to Agon" became
**⚔ Propose in Agon** + **⚖ as model M** (`sendToAgon(asModel)` branch on `proposal_egif` vs `model_egif`), so
the carry-a-graph hand-off is fully symmetric across both source modes. [[project_next_cross_mode_ux_coherence]].

**▶▶▶ THIS SESSION (2026-06-28, cont. 3) — UX: shipped (#4) stage 2(b), the guided "first graph" primer (the
in-app front door to the Field Guide for the notation learner).** Author chose (b) primer-first over (a)
plain-English door (the "both, in sequence" pair). The newcomer's journey is Organon → Ergasterion → Agon, and
to *author* a graph the learner first needs the notation; the primer teaches it without throwing EGIF cold.
**Shipped (additive; 1 small read-only route + 1 shared JS module + `*.html` wiring; core-protection CLEAN):**
new **`src/web_api/routes/primer.py`** (`GET /primer/examples` — renders the curated first graphs cat-on-mat /
the human→mortal scroll / the empty cut through the **real** `generate_layout` so the picture↔proposition
correspondence is *shown*, not described; fail-soft, asserts nothing) + new shared **`web_viewer/js/primer.js`**
overlay (self-contained, themed off CSS vars, mirrors mode-nav/context-reflex tag pattern): the **four marks in
plain sight**, the **EGIF key table** ("you type / it means / in a drawing"), the **worked first graphs drawn by
Arisbe**, the **five drawable dragons** each deep-linking into Ergasterion challenge mode, and where-to-practice.
Reached by a **"New here? — start with the marks"** link auto-injected into the shared mode-nav (so present on all
three mode pages) + a green **"New here?"** door on the home page (`index.html`). Added a **`?challenge=🐉N`**
deep-link handler to `ergasterion.html` so a dragon chip lands in a ready session with that challenge engaged,
freehand-armed. All content faithful to `docs/FIELD_GUIDE_AND_DRAGONS.md`. Tests: `test_primer_route.py` (3:
examples served+drawn, scroll+empty-cut present, each parses+renders), `test_primer_e2e.py` (5: home door opens
the overlay with ≥3 drawn SVGs; "New here?" link on all 3 mode pages opens it; dragon chip deep-links into
challenge mode). 96 route tests + 14 adjacent E2E (challenge/context-reflex/agon) green; core-protection CLEAN.
Verified visually (headless Chromium): the overlay shows the four marks, the key table, and the live-drawn
cat-on-mat + scroll. Docs: ROADMAP #4 → stage 2(b) DONE (only 2(a) plain-English door remains), CAPABILITY_MAP
primer row → SHIPPED. [[project_next_cross_mode_ux_coherence]], [[feedback_newcomer_accessibility_dragons]].

**▶▶▶ NEXT SESSION — ROADMAP #14 (authentic-Peirce LaTeX export) is COMPLETE (phases 1 + 2 + (d)). Next = #15
or #16 (the two remaining tidy-up tracks), or back to reference-node increment 2 — author's pick.** The reference
node is PAUSED on the 2nd-order frontier (increment 2 = cross-UoD use/mention fork, DoR §4½/§7 — author decision).
Of the three tidy-up tracks the author set, **#14 is fully done** (oval cuts, heavy LoI, hooks, iconic scroll
glyph, worked-chain document, route deltas, drawing→EGI learning loop); only an optional thin UI surface remains
(Ergasterion route into the learning loop; session-export route). Remaining tracks:
**(#15) layered start-up guidance** for new users assuming no math/logic background, then branching to what an
**ontologist / logician / mathematician / Peirce expert** each needs (a written, role-aware companion to the shipped
in-app primer / Field Guide);
**(#16) external-sources & import documentation** — a consolidating doc making the end-to-end import story legible
(ontologies OWL/RDF/CLIF/SUOKIF; textbooks/websites/papers; what enters, at what warrant, attributed/attested how —
gathering CORPUS_AND_IMPORT_MODEL + MANIFEST_AND_MEANING + the OWL/RDF importers + `cl_import_resolver`).
Bring sequencing options for #14–#16 to the author at session start.

**Last Updated**: 2026-06-27. **▶▶▶ This session (2026-06-27) — CONSOLIDATION / PLANNING SPINE shipped + the
protected-core re-audit.** Built the top-down orientation Arisbe never had, as **four thin, cross-linked,
additive docs** (decisions taken with the author at session start: small-set / layered-for-both-audiences /
backlog-with-near-term-detail): **`docs/VISION_AND_SCOPE.md`** (what Arisbe is, the central correspondence
problem, the bedrock non-negotiables + three regimes, who it's for, scope in/out/deferred, governing
principles, system-at-a-glance, trajectory), **`docs/CAPABILITY_MAP.md`** (one living status table — every
capability → SHIPPED/PARTIAL/DESIGNED/OUT → src module → test home; corrected the extraction's over-clean
"all-shipped" with honest PARTIAL/DESIGNED/OUT rows for tension_engine 17/18, Agon V1 hot-seat, DLCore
abstainers, layout-perf, NL-disambiguation, render-M, reference-node, Gamma/raster OUT), **`docs/ROADMAP.md`**
(one sequenced backlog consolidating the scattered open tracks; near-term items expanded), and
**`docs/GLOSSARY.md`** (Peirce/Dau/Arisbe vocabulary + reading-order by audience). All four linked from
CLAUDE.md's "Start here" block. Method = read-only multi-agent extraction from the three authoritative sources
(protected-core = non-negotiables, tests/ = behavior, docs spine = the why), then synthesis; every cited
test/src filename verified to exist on disk. **The protected-core re-audit (author-added sub-task) findings,
folded into VISION_AND_SCOPE §3 + ROADMAP #1 as a DECISION for the author:** (a) the "16 vs 17" count drift is
**already reconciled** (report prints 17, matches CLAUDE.md; no ghosts — every member has a live importer);
(b) **the mechanism does NOT guard the central invariant** — `correspondence_attestation.py` (28 importers) +
`presentation_ops.py` (31 importers) are the *most-imported* modules in src/ yet **unprotected** → recommend
adding them (+ maybe `natural_layout.py`); (c) the real guard is the ~150-test core subset, which itself omits
`test_correspondence_invariant`/`_attestation` from the fast gate; (d) the linear parsers/generators are
architecturally I/O, not calculus (the six rules don't import them); (e) two thinly-held ligature members
(single consumer = chapter17_soundness_evaluation). Options (keep+extend / keep+trim / replace-with-bedrock-note)
laid out in ROADMAP #1. **Author chose option (a) "keep + extend" — EXECUTED this session:** added
`correspondence_attestation.py` + `presentation_ops.py` + `natural_layout.py` to the protected set (now
**20 modules**, report verified) — the §3.3 enforcers now require authorization to change; spine docs +
CLAUDE.md updated to 20. (Edits are in `tools/`, not `src/`, so core-protection stays CLEAN; no protected
src module touched.) **Caught + corrected mid-task:** I first also added the `test_correspondence_*` suites
to the fast gate, but measured them at **>6.5 min** (corpus-wide ELK layout generation) — they would bust
the gate's <30s budget / 180s timeout and fail every commit. Reverted that half with an explanatory comment;
the invariant is guarded at commit time by the module protection + in full CI, not the fast gate. Docs
(VISION §3 / ROADMAP #1) corrected to the honest version. **Then the author took (b) + (c) too:** **(b)
trimmed** the six EGIF/CGIF/CLIF parsers/generators out of the set (application-level I/O the calculus
doesn't import; guarded by corpus round-trip tests in CI) → **net 17 → 20 → 14 modules** (the genuine
calculus core; report verified 14/CLEAN). **(c) declined CODEOWNERS** — it routes PR reviews and does
nothing in a solo/no-PR workflow; instead the protected set's inline comments now **double as the bedrock
note** (one artifact that documents *and* enforces); the gate is kept because its real value is an **AI
tripwire** on the calculus. **Repo hygiene (author-approved):** fast-forwarded `main` (was stale 9 commits
behind) → pushed; **pruned all 7 stale branches** (local + remote; all fully merged, 0 unique commits) so
only `main` remains; **deleted the dead `.git/hooks/post-merge`** (imported a non-existent
`architectural_integrity_system`). Going forward: work on `main` directly (solo, local-primary). **Then, at the author's request, a LITERATURE / CONTRIBUTION ASSESSMENT** (3 adversarial
web-research sweeps: EG-software landscape · formal/theoretical claims · endoporeutic/iconicity) →
**`docs/CONTRIBUTION_AND_PRIOR_ART.md`**. Honest headline: Arisbe's contribution is **operationalization +
integration, not new logic**; the **one element with no located prior art = the runtime-attested
linear↔graphical correspondence invariant** (the signature claim); Beta-complete Dau-faithful interactive
editing fills an apparently empty niche (the one maintained interactive EG prover, RAIR's Peirce-My-Heart, is
Alpha-only); most other claims are "KNOWN IDEA NEWLY OPERATIONALIZED" (EG≅DRS = Sowa/Kamp, endoporeutic-as-game
= Hilpinen/Hintikka/Pietarinen, modality = standard translation/Zeman, iconicity = Stjernfelt/Shin — all must
be cited); two overclaim risks flagged (EG≅DRS isomorphism is textbook Sowa; "Gamma unnecessary" cuts against
Ma & Pietarinen). Gap Arisbe could fill: no machine-checked Dau formalization found. **Then an ATTRIBUTION-HONESTY PASS** (author:
"give clear and explicit credit ... describe gaps in expressibility not using gamma exposes + the diagrammatic
advantages Ma & Pietarinen find"): deep research (Ma & Pietarinen 2018 *Gamma graph calculi*; van Benthem;
Vardi; Zeman; Roberts; Peirce CP 4.516/MS R 467) + a docs overclaim audit. Fixed real misrepresentations
(audit's "docs already fine" was unreliable): **(1)** `MODALITY_WITHOUT_GAMMA.md` — added explicit credits
(van Benthem/Zeman/Ma & Pietarinen) + a **References section** (had none); reframed "the case Peirce kept
failing at" honestly (Peirce *left the broken-cut iteration rule open*, not "failed"; Ma & Pietarinen
**rehabilitate** it — sound-complete calculi for 15 modal logics, "only (DMN),(B),(5) new", algebraic not
Kripke completeness); added a 3-part **expressibility ledger** (no object-language loss for propositional
modality / genuine gaps = second-order + metalinguistic / perspicuity-decidability cost — Vardi) + a "What
Gamma keeps" section naming the diagrammatic advantages (position-polarity off cut topology, no NNF, no labels,
ambient-space free bookkeeping) + the iconicity caveat (contested by Pietarinen himself, "Two Dogmas");
reframed thesis to "no modal *mark* needed for Arisbe's architecture," NOT "Gamma dispensable for logic".
**(2)** `THE_MINIMAL_IN_VIEW_SET.md` — corrected the EG↔DRT overclaim (it said "no published EG→DRS reduction
exists"): the **static DRS≅EG isomorphism is Sowa's** (tracing to Kamp 1981), credited in 4 spots + refs;
Arisbe's contribution scoped to the *dynamic* step↔update **scorer**. **(3)** `CONTRIBUTION_AND_PRIOR_ART.md`
Gamma ledger entry sharpened + year fixed (Synthese 2018). **Docs only; core-protection CLEAN.**
[[project_consolidation_requirements_spine]]. *(Prior 2026-06-26 web-presentation audit below.)*

**▶▶ Prior session (2026-06-26) — WEB PRESENTATION AUDIT (observe-and-assess)
→ 5 fidelity fixes shipped.** Walked the running web server across all three modes with headless Chromium
(drove each like a real user, captured + read ~30 screenshots), judging how faithfully the rendered screen shows
the implemented ideas. **Verdict: the experience corresponds FAITHFULLY — no idea is garbled or
misrepresented; the gaps were polish + onboarding.** Organon: standing/warrant badges, the full provenance
bundle, the chain-of-semiosis player (per-move rule + narration, e.g. "INS — Insert Q into the cut holding the
iterated (P⊃R)"), clean nested-cut drawings, the context reflex + correspondence chord all read true.
Ergasterion: the regime-1 labeling, the Graph↔Argument lock/unlock contract (rules appear only after ① fix),
the typed-mark palette + freeform draw + Fragment graft, the scratch/Agon-only mode contract, fold-to-define,
and the dragon challenges all faithful. Agon: the triadic framing, the ①-board-stays-present with the peel
transcript (verifier/falsifier moves + witnesses), the verdict-coherent disposition taxonomy (nothing
auto-asserts), and the inverse pivot all faithful. **Then, at the author's direction ("do all but 4 and 7"),
shipped 5 fixes (all additive; core-protection CLEAN):** **(1)** the documented launch command
(`uvicorn web_api.main:app`) **failed** — `ModuleNotFoundError: web_api` — fixed to the self-contained
`uvicorn --app-dir src web_api.main:app` across all 7 docs (CLAUDE/AGENTS/README/CURRENT_PLAN + 3 docs/).
**(2)** Agon now **lands on a worked example** (`teacher-mammals`, a clean TRUE) so the arena is runnable on
arrival — the empty fields' placeholders had read as if pre-filled, and "Does G hold in M?" just reported
"enter a proposal G". **(3)** Ergasterion **challenge mode surfaced** — lifted from two-levels-deep inside the
freeform tools into an always-visible `🎯 Challenge` disclosure during composition; picking a target now
auto-engages the freeform canvas for the learner. **(5)** Organon's header **`shape` is qualified at the base
frame** (`0V / 0E / 0C · starting context`) so the blank starting context no longer reads as the theorem's own
(empty) shape; the qualifier drops as you step. **(6) VERIFIED, no fix needed** — the witness/counterexample
line-of-identity **does** light on the Agon board (DOM-confirmed maroon `#eba0ac` stroke on the Biscuit
counterexample; green for an existential witness); the universal-TRUE case I'd flagged has **no single witness
by design**, so its un-lit line was correct. Tests: route+challenge+interpretation suites green (133), agon /
challenge / freeform / define / organon-lenses / context-reflex E2E green; updated `test_ergasterion_challenge_e2e`
to open the new disclosure. **DEFERRED for the author's decision (4 & 7):** **(4)** the Context reflex floats as
an absolute top-left overlay on every board — the one shared element that can sit over the drawing (dock vs
auto-dim?); **(7)** the newcomer / EGIF-authoring on-ramp (a non-logician can read a lit verdict but can't yet
easily author M/G — already flagged 2026-06-24). [[project_next_cross_mode_ux_coherence]]. *(Prior 2026-06-26
session — BUILD (g) the diagram↔narration harness — below.)*

**▶▶▶ Prior this session (2026-06-26) — BUILD (g): the diagram↔narration validation
harness, prototyped → corpus → SUPER-BUDGET chain (the spatial S1 metric now live).** Third iteration:
authored the corpus's first **super-budget** worked chain — `tomos/universes/crowded_modus_ponens`
(`tools/build_crowded_modus_ponens_chain.py`): the fact `(A)` + the matching rule `A⊃B` among **ten unrelated
rules `Dk⊃Ek`** (twelve sibling chunks, over the ~7 budget), then ordinary modus ponens (IT-, DC-) on the one
matching rule → `(B)`. Every other corpus chain is sub-budget, so the spatial overview metric (S1) degenerated
on all of them; this makes it **falsifiable**. Extended the harness with `spatial_visible` — a focus-centered
DOI collapse (cut-nesting distance, Furnas; a *model* of the overview budget, not the production engine): at each
step it hides the interiors of cuts far from the focus. New metric **salient-in-view (S1)**: every narrated item
survives the collapse. On the crowded chain the matching rule + fact stay visible while all ten distractor
consequents `Ek` (two cuts deep) collapse off-view, and **the proof's narration names only the fact + matching
rule → salient-in-view 100 % [LIVE]** — direct evidence for S1 (an expert keeps the narration in a bounded
focus-neighborhood amid a dozen chunks). A **fourth falsifier** proves it bites: a doctored "…recall (Ek)" naming
a collapsed distractor drops it below 100 %. (Fixed a real bug found en route: `depth()` subtracted the sheet,
collapsing all sibling cuts to DOI-distance 0 — the ranking was degenerate; and scoped the metric so a
rule-*erased* token isn't an in-view failure, only a *collapsed* one is — caught by branching_confluence's
all-ERA steps.) Corpus now **8 chains/35 steps**; all salience-role metrics 100 % across all 8 (ref-align 7/8,
the group_identity macro-residual). 26 tests (4 falsifiers + per-chain corpus param + spatial). Doc §10 gains a
"spatial rule goes live — the super-budget chain" subsection + salient-in-view table row. Adjacent suites
(organon/tomos/chain-persistence/correspondence) green; core-protection CLEAN; additive. [[project_minimal_in_view_set]].
*(First two iterations of this session below.)*

**▶▶ Earlier this session (2026-06-26) — BUILD (g) iterations 1–2.** The 2026-06-25 doc designed §10's
harness but left it unbuilt ("needs a scorer, not a schema"). Built the scorer and ran it on the ground-truth
fixture, the transcribed Dau **Praeclarum** chain (whose 7-step segmentation Arisbe did not design — honest
ground truth). New, **read-only**, additive, core-protection **CLEAN**: `src/diagram_narration_check.py` +
`tools/run_diagram_narration_check.py` + `tests/test_diagram_narration_check.py` (12, incl. **two falsifiers**).
Per move `Gᵢ₋₁→Gᵢ` it computes — all exact functions of the two immutable EGIs + the recorded gold `selection` —
the **focal set Φ** (delta `added∪removed` ∪ selection ∪ each one's **sticky enclosing cut**, S3) and the
**referenced set Ρ** (standing material the move reuses = the iteration source). It parses each transcribed
narration **deterministically** (sound for the controlled {P,Q,R,S} Peircean register) into **operated** vs.
**locative** relation tokens via a verb/locative-marker split — the Centering distinction between the
utterance's *center* (operated object) and the material that merely *addresses* it ("into the cut **holding**
(P⊃R)", "**around** S"). **The crux finding:** the first crude "everything-mentioned ⊆ focal" metric scored
71 % with unexplained misses — because it conflated operated mentions with *locative* ones; the misses were
**all locative** (P,R locating a cut; S as "the double cut around S"). The refined metric splits them, and the
**EG↔DRT step-update bridge then holds on Praeclarum: operated→Φ 100 %, locative→Ρ 100 %, reference-alignment
100 %** across all 7 steps (a narrated proof step = a DRS update; new vs. reused referents = added vs. reused
graph elements — the long-acknowledged-but-never-operationalized bridge). The two falsifier tests prove the
metrics **bite** (doctored "Erase S" drops coverage; doctored "into the cut around R" on the inserting step
drops grounding) → the 100 % is **earned, not vacuous**. Spatial metrics (S1/S2 overview) degenerate because
Praeclarum is sub-budget (max area fan-out 3, depth 4 ≤ 7) — the harness **detects and declares** this, and
`honest_limits` keeps every caveat surfaced (deterministic-not-LLM alignment; single narration not a corpus, so
*alignment* never *optimality*; token-level salience). **Then extended to the WHOLE corpus of narrated worked
chains (7 UoDs, 33 steps) — and the corpus did its job: it falsified the two-role model.** The operated/locative
parse scored 100 % on the two Alpha *construction* proofs (Praeclarum, Peirce's-law) but failed systematically on
every *eliminative/macro* chain (DC-/ERA/IT-, 38–75 %) — the misses all a **third role** the model lacked:
**restatement** of the resulting proposition ("→ every S is P", "leaving (R)", "landing S on the sheet", "the
bare theorem e = f"). Two principled refinements faithful to §9: (1) the **D3 effect set** — when a cut is
added/erased its surviving *subtree* changed scope and joins Φ ("enclose P and ~[(Q)] in a double cut", "erase
the double cut, landing Q on the sheet"); (2) the **three Centering/DRT roles** — operated→Φ (center),
locative→Ρ (anchor), restatement→in-view V (discourse-old upshot), bucketed by earliest-occurrence vs
locative/restatement markers (+ a `:=` substitution-vs-identity tokenizer fix). **Corpus result: all three
salience roles hold 100 % across all 7 chains; reference-alignment 100 % on 6/7.** **The lone residual is itself
a finding:** `group_identity` step-1 is a **squashed macro move** (insert+merge+erase collapsed into one node)
whose narrated stance is *introduce* but whose net delta is *pure removal* → reference-alignment honestly fails =
the **D4 squash phenomenon** (needs sub-step expansion, not a metric patch). 21 tests (2 falsifiers + per-chain
corpus parametrization + the macro-residual). Doc §10 "half-built" → **"prototype scorer (built — corpus
result)"** with a three-role table + metric/falsifier/result table + named next falsifications (super-budget
chain to make S1/S2 + restatement-in-view live; narration corpus for inter-narrator agreement; LLM bridge for
free narration; macro sub-step expansion; metric-3 chapter-boundary on a branching DAG). [[project_minimal_in_view_set]].
**Other open threads from 2026-06-25 unchanged:** (d)+(c) render-M UI (safe, near-term), (b) reference/transclusion
node (the architectural fork, author's decision). *(Prior 2026-06-25 session below.)*

**▶▶▶ Prior session (2026-06-25) — DOCTRINE/DESIGN doc: the minimal in-view set
(scale, attention, scoping) + the diagram↔narration check.** Discharged the *design* of the deferred "render
M" task by reframing it (author-led, three deepening passes) as the Peircean cognitive problem: EGs leverage
bounded visual attention, so the question is normative — *what minimum subset of a UoD stays in view, and what
rules govern it, synchronically and diachronically?* New doc **`docs/THE_MINIMAL_IN_VIEW_SET.md`** (design-of-
record, no code): (1) the **three scale axes** "too big" conflates — synchronic EGI (`overview_projection`),
diachronic history DAG, ambient model M (`domain_oracle`); "render M" = axis (iii). (2) **One governing
principle** = Relevance (Sperber & Wilson) capped at ~4 chunks (Cowan), along two distances — cut-nesting
(Furnas DOI) in space, steps-from-HEAD (git) in time; Arisbe's 4 primitives map 1:1 onto the cognitive
literature (overview=DOI, fold=chunking, ContextReflex=common ground, oracle=extended mind / long-term working
memory). (3) The **normative rules** S1–S5 (synchronic) / D1–D4 (diachronic). (4) **The keystone — a falsifiable
*diagram↔narration* check**: a narrated proof is a chain of DRSs and a DRS *is* a Beta EG (Kamp & Reyle; the
EG↔DRT bridge, acknowledged but never made operational — Arisbe would be first); Centering (per-step salient
set) + Grosz/Sidner focus-stack (chaptering) supply the metrics; verbal reports of *current contents* are valid
data (Ericsson & Simon). The check is **already half-built** — every chain node/edge carries narration
(`StateSnapshot.natural_language_summary`/`linear_forms`, `TransformationStep.natural_language_description`,
`LogicalProvenance.rule_citation`); fixture = the transcribed Dau **Praeclarum** chain; needs a *scorer*, not a
schema. (5) Answer to "scoping without recapitulation" = accessibility (DRT) + focus-stack + LTWM retrieval
cues (Ericsson & Kintsch) + the math register's black-boxing — all already sound in Arisbe (oracle, fold-no-
global-unfold, `rule_citation`). **Recommendation:** near-term safe path = (d) ground/legend panel + (c)
relevant-neighborhood M-render (extends shipped code); **prototype (g) the validation harness first** (turns the
rules into tested claims); **(b) a first-class reference/transclusion node** is the open architectural fork
(touches `egi_core_dau`+§3.3) — the author's decision. Docs only; core-protection untouched; cross-linked from
ADAPTIVE_SCOPE_VIEWER / DOMAIN_ORACLE_AND_M / LINEAR_GRAPHICAL_CORRESPONDENCE. [[project_minimal_in_view_set]].
*(Prior 2026-06-24 session below.)*

**▶▶▶ Prior session (2026-06-24) — cross-mode UX coherence, pass 1 (explore →
decide → BUILD).** Walked the three modes against six personas (teacher/Organon, student/Ergasterion,
researcher + domain-expert/Agon, cold-start newcomer, logician round-trip) via parallel read-only catalogues,
brought findings to the author, who anchored on **①** (keep the drawing present in Agon) **and ④** (carry the
form's ground across mode handoffs). Both shipped, additive, core-protection CLEAN.
**① the board stays present in Agon** — the interpret / where-it-holds / contest registers no longer hide the
canvas behind a text peel; they now draw the proposal **G** beside the reading and **light the deciding line of
identity on it**. Backend: `semantic_game.SemanticResult` gains `witness_vertex_ids` (line token → G vertex id,
from the existing `_gen_name` map; `None` on UNKNOWN); `agon.py` `_interpret_payload` / `where_it_holds` /
`_contest_payload` each render G (`generate_layout`) and return `svg` + `introspection` + `witness_vertex_ids`
(contest emits the full line-token→vid map so fixed selectives light up; its frontier already carries real
edge/cut ids). Frontend (`agon.html`): center `#board-row` (board + a 380px reading strip), shared
`showReadingBoard` / `renderReadingContext` / `highlightEvidence` + `paintContestBoard`; witness=green,
counterexample=maroon, contested area=yellow, conjunct option lit blue on hover. `diagram-viewer.js`'s
`highlightElement`/`clearHighlights` were already there — the gap was payload ids + not hiding the board.
**④ the form's ground travels** — Organon→Ergasterion / Organon→Agon / Ergasterion→Agon handoff URLs now carry
`&from=<name>&fromMode=<mode>`; each destination captures it into `currentOrigin` and threads `ground.origin`
into its ContextReflex; shared `context-reflex.js` `groundHtml` renders a **`carried from: <name> (<mode>)`**
row (additive, ignores-unknown contract preserved). So Agon's generic "the contest board" now also says where the
proposition came from — the same form stays recognizable across modes. Tests: +1 `test_semantic_game`
(witness_vertex_ids locate the line on G), +4 `test_agon_interpretation` (interpret/standalone/inverse/contest
carry a board + locate evidence; vid really appears as `data-element-id` in the svg), +2 `test_agon_e2e`
(Playwright: board stays visible + evidence lit; handoff origin reaches the ground panel). 248 web/mode tests
green; quality gate 152 core green; core-protection CLEAN. **Scope deliberately deferred** (flagged to author):
rendering M, a structured/clickable transcript, and the bigger **newcomer / EGIF-authoring on-ramp** (a
non-logician can read the lit board now but still can't easily *author* M/G — `index.html` + Agon setup throw
jargon cold). [[project_next_cross_mode_ux_coherence]]. *(Prior 2026-06-23 session below.)*

**▶▶▶ Prior session (2026-06-23) — UX fast-follows (author said "proceed
with both"): (1) WARRANT — standing surfaced in **Agon** (both disposition services return a `standing`
block; an `✓ Asserted into the corpus` badge card in `agon.html`; contest → ⚔ withstood, game → ⛓ derived)
+ a **style-only reprojection** note in Organon's view toolbar (`↺ standing unchanged`); badge markup
extracted to shared `js/standing-badge.js`. (2) CORRESPONDENCE CHORD — the shared `LinearFormPanel` (all 3
modes) now shows `≡ picture ↔ proposition · §3.3 correspondence, not truth` with an explanatory tooltip.
Tests: +2 route asserts, +3 E2E; core-protection CLEAN; additive (one new JS module). See the two ✅ DONE
2026-06-23 bullets in ▶ NEXT SESSION. — Prior 2026-06-22 session: (1) DOCTRINE — LEVEL_ZERO rework +
`assertion-4` closure (c5be85f); (2) UX — the cross-mode **context reflex** panel (c2d561f); (3) **DOCUMENTARY
HOUSE-CLEANING** (author-directed: make the challenge/dialog record accessible) — examined the author's new
*fair-access* reframing of the worth-ladder (3-opponent panel → falls as stated, re-grounded methodologically:
*gate the claim by method, never the agent by worth; owe every claim its uptake*), recorded as **Examination
III** + a revised FIDELITY Corollary, and wrote a plain-language front-door **`docs/FIDELITY_A_PLAIN_ACCOUNT.md`**
(the whole arc of doubt→challenge→resolution→what-changed, a worked example per principle) + light prefaces on
the 3 technical docs + a visual-alphabet primer for FIELD_GUIDE. UX work is PAUSED per author. NEXT (still
queued, when UX resumes) = correspondence-not-truth chord · warrant fast-follows (⚔ in Agon, style-only
reprojection).**

**▶▶▶ DOCUMENTARY PASS (2026-06-22) — accessibility of the challenge record.** Author's directive: the recent
challenge-driven docs (LEVEL_ZERO, ADVERSARIAL, FIDELITY, FIELD_GUIDE) are specialist-only except FIELD_GUIDE,
which is still opaque; make the *dialog* (what excited the doubt, how expressed, how negotiated, what changed in
the author's position / in Arisbe / in our reading of Peirce & the tradition) legible to a well-read
non-specialist, **with a clear worked example — adherence or obvious breaking — for every principle.** Done:
(a) **fair-access examined then recorded** (author chose examine-first): the equal-dignity premise → fair-access
→ (post-exam) *method-is-the-only-legitimate-gate-on-claims + uptake-obligation*; the worth-ladder denial no
longer imports equal dignity. (b) New **`FIDELITY_A_PLAIN_ACCOUNT.md`** front door (4 doubts as a narrative;
examples: Galileo's telescope, the reactor corridor, the augurs' contest, cat-on-mat, Praeclarum). (c) "New
here? read the story first" prefaces atop FIDELITY/ADVERSARIAL/LEVEL_ZERO. (d) FIELD_GUIDE: a "marks in plain
sight" primer (the 4-mark alphabet + an EGIF key table) so notation isn't thrown cold; dragon-6 carries the
method-gate/uptake guard + its examples. Docs only; core-protection untouched. ([[project_fidelity_and_departures]],
[[feedback_newcomer_accessibility_dragons]].)

**(C) DOCTRINE — A & B examined to Departure-I parity, then MERGED into FIDELITY as a corollary.** Captured
two perspectives that "cost the sophisticate her investment" — **A** (the larger game; we hold no referee's
chair; "principalities and powers" as an FSM-style reductio demoting every context-less *terminus ad quem*)
and **B** (the common sheet; no ladder of worth/nearness). At the author's challenge ("have these been tested
as thoroughly as the Departures?" — they had not), ran the **full iterative dissolution-press (4 rounds, 3
fresh opponent panels)**. Honest outcome (the kind the author courts): **neither survives as an independent
perspective.** **A → `departure_absorbed`** (≈0.81): no proposition independent of Departure I (negative
orientation + first-order non-locution) + Departure II (the low-warrant assertoric posit — the killer: run
with Dep II's *real* two-register content the "context-less end is malformed" analogy backfires, since an end
is a licit *posit*; and an end is Thirdness, not a level-0 *marks*-theorem). Residue = the
*no-founder-exemption* FSM pedagogy. **B → `departure_narrowed`** (≈0.75): metric terminus dissolved (= Dep
I), but the context-free **comparative efficacy-vector is CONCEDED** (= structural realism — only the *summit*
was ever a non-locution, never the vector); residue = the **worth-ladder denial** vs the convergent dreams'
competence/worth fusion, held *at parity in the axiological register* on an *imported equal-dignity premise*.
Immanent-tendency cap re-typed: **enclosure, not scope — WON, not parity** (§3.3 + negative orientation
instance the category). Honest billing: **one discipline (Deps I+II) + an imported equal-dignity premise +
conceded structural realism, two targets.** **Then merged** (author's call): the standalone
THE_LARGER_GAME_AND_THE_COMMON_SHEET.md was deleted and folded into `docs/FIDELITY_AND_DEPARTURES.md` as the
closing **Corollary**; `ADVERSARIAL_EXAMINATION.md` carries "Examination II" (rounds 1–4 + resting place); all
links redirected. **Live floor:** the warrant badge reads as in-context competence, NEVER
worth/nearness/context-free Progress. **Docs only; core-protection untouched.** Memory:
[[project_larger_game_common_sheet]].

**(UX PASS — two threads shipped this session.)**

**(B) WARRANT GRADIENT VISIBLE (thread 2).** Made a graph's *standing* legible in Organon. `provenance.py`
gains a `standing_of(...)` projection over the existing warrant model + corpus signals → an ordered badge
(`blank ○` · `posited ◇` · `derived ⛓` · `withstood ⚔`), each carrying the **"correspondence, not truth"
non-claim** in words (so the badge is never read as a verdict — this also discharges field-guide 🐉6).
Highest standing wins: withstood (`warrant:withstood_agon` tag / `tested` warrant) ▸ derived (a sound
chain reaches it, via new cheap `TomosService.has_chain`) ▸ posited (the low floor) ▸ blank. Exposed in
the Organon **list** (per-row, computed from cheap side-files — no `load_uod`) and **detail** payloads;
rendered as a pill in `organon.html` (compact glyph in list rows, full badge in the detail header, tooltip
= meaning + non-claim). Visually verified (Playwright screenshot: 29 badges, derived Praeclarum shows
⛓ Derived). Corpus today: 21 posited, 7 derived, 0 withstood (none asserted through Agon yet). Tests:
+5 unit (`test_provenance` standing branches) +2 route (`test_organon_routes` list+detail carry standing).
Ergasterion (regime-1, no standing by design) + Agon untouched. Memory: [[project_warrant_gradient_visible]].

**(A) DRAGONS CHALLENGE SET (thread 1).** With the author's steer ("Dragons challenge set" from the UX menu), wired the field guide's five
*drawable* dragons into challenge mode end to end: `src/challenge_mode.py` gains `dragon`/`temptation`/
`antidote` on `Challenge` + two new targets (🐉2 the empty cut `~[ ]` = false; 🐉3 the removable double
cut `~[ ~[ P ] ]`, the look-alike contrast to the scroll) + `list_dragons()`; existing rungs tagged to
their dragon (🐉1 universal, 🐉4 shared line, 🐉5 argument order). The `/ergasterion/challenges` route
exposes the metadata; `grade-challenge` returns the field-guide **antidote** when a dragon attempt fails.
UI (`ergasterion.html`): 🐉N badges in the picker, the temptation shown on select, the antidote surfaced
in a highlighted box on a wrong grade. Field guide cross-links the set (dragons 6-8 are conceptual — not
drawable — and belong to the warrant / correspondence-not-truth threads). Tests: +6 core
(`test_challenge_mode`) +5 route (`test_ergasterion_challenge`, incl. both new targets round-tripping
through the *drawing reader*); 102 in the ergasterion/freeform/diff sweep green, quality gate 152 core
green, **core-protection CLEAN**. Memory: [[project_dragons_challenge_set]]. **The other UX threads
(warrant gradient · context reflex · correspondence-not-truth) remain open — see the menu below.**

*(Prior session — 2026-06-19:)* (1) **shipped BUILD A frontend** — the fold-to-define UI +
Playwright E2E (commit fdf4cb8; build A now complete end-to-end). (2) Discharged the author's
**fidelity-to-Peirce** request: wrote `docs/FIDELITY_AND_DEPARTURES.md` (the debt + three departures +
their Peirce-rooted justifications + points of confusion) and ran a **five-round multi-agent adversarial
examination** (`docs/ADVERSARIAL_EXAMINATION.md`) — all three departures **survive WITH AMENDMENT**; the
four doctrine docs were amended to their post-examination form (Departure I "inquiry doesn't converge"
fell to one open joint held at parity, negative orientation secured from Peirce's own *Fixation*; II/III
survive as scope-corrections). Commit 406746b. (3) Wrote a **beginner field guide** —
`docs/FIELD_GUIDE_AND_DRAGONS.md` (plain on-ramp + 8 "here-be-dragons" pitfalls with EGIF examples
*verified against the parser/FOPL*; + the **context reflex**: a fragment is a building block, ask after
its ground). Commits 2115e5f / 30b081b. **Bedrock untouched, core-protection CLEAN throughout; all
pushed.** Memories: [[project_fidelity_and_departures]], [[feedback_newcomer_accessibility_dragons]],
[[project_fold_to_define]]. **The UX has been neglected while doctrine/backend ran — next session turns
to how all of this *plays out in the interface* (see the ▶ NEXT SESSION UX block below).**

*(Prior session recap — 2026-06-18, two doctrine passes:)* (1) discharged the 2026-06-18 external-conversation handoff — `docs/MODALITY_WITHOUT_GAMMA.md`
(modality needs no Gamma; the diachronic DAG/corpus *is* the drawn Kripke frame; real frontier =
second-order logic about the graphs). (2) A second part-two conversation → `docs/LEVEL_ZERO_AND_THE_REGISTERS.md`
(level 0 bears *form* not free-floating content; demonstrative vs assertoric **registers**; the
**scroll** `cut[M cut[P]]` is the Alpha home of "given M, then P" + model-revision-as-INS — i.e. the
Agon inning + the formal home of "free to demote"). Reconciled MANIFEST_AND_MEANING (floors #4/#6/#2 +
membrane), CHAIN_OF_SEMIOSIS (third position + two registers), DOMAIN_ORACLE_AND_M (§4a scroll),
adaptive-scope reserved-channel wording. Bedrock untouched, core-protection clean. **Next: BUILD A —
fold-to-define UI** (wire the built+tested `definitions.fold_selection` into the drawing canvas:
draw a body → fold under a named definition → unfold; the visible face of the second-order/abstraction
layer; hard logic done, UI+route+E2E remain). See ✅ DONE 2026-06-18b/c under ▶ NEXT SESSION.
*(Prior-session recap follows.)* **This [2026-06-15] session:** committed the prior session's
cross-mode UX consistency pass (was done-but-uncommitted), then built **both halves of the
FOLIO/DLCore coverage lever** — the **disjunctive case-split** (refutation) and the **finite-model
finder** (model construction). Native FOLIO coverage **23 % → 63.2 %** at **100 % soundness vs Z3**
(decides 61 of 69 gold-Uncertain; the 9 gold-disagreements are all Z3-corroborated noise — 0 genuine
errors). See the ✅ blocks under ▶ NEXT SESSION. *(Prior-session recap follows.)* **The 2026-06-14
visualization/UX pivot:** with the
logic underpinnings essentially complete (basics, not options), the session pivoted to the
*experience* of the pictures and shipped the **adaptive-scope viewer** end to end — read-only
Organon **lenses** (2.5-D negation well + storyboard, behind a Lens selector, over O(n) structure
endpoints; bedrock untouched) via a decide-by-prototype spike — plus **FOLIO increment 3** (the
native bounded engine, soundness 100% / coverage 23%) and deep philosophical additions to
`docs/MANIFEST_AND_MEANING.md` (the membrane/separation, the **no-mark-bears-actuality** guardrail,
two-deaths/liveness, Peirce's cable). See ▶ NEXT SESSION. *(The 2026-06-12 recap below is prior
context.)* The 2026-06-12 session **completed the P2 import-breadth
queue**: (1) finished the **OWL construct fragment** — `ObjectHasValue` + `ObjectMinCardinality 1`
(≡ someValues, sound either polarity) added to `_class_expr`; `ObjectComplementOf` in
superclass position (`(not 〚D〛)`, head-only like ∀R.D); higher/max/exact cardinality +
hasSelf + oneOf reported. (2) Added an **RDF front-end** (`tools/rdf_to_owl.py`): rdflib
(BSD-3) parses Turtle / RDF-XML / N-Triples / JSON-LD, a triple→`Node` mapper reconstructs
the *same* functional-syntax AST the OWL translator consumes (blank-node `owl:Restriction`
decoding, `intersectionOf`/`unionOf` RDF-list handling, structural A-box detection), and
`translate_axiom_forms` (extracted shared core) reuses every axiom + class-expression rule.
Wired `from_rdf_text/from_rdf_file` into the importer; a Turtle-imported ontology reasons
end-to-end (subsumption + ∀R.D-Horn materialization). 41 OWL tests + 16 RDF tests; 238
regression green. **Manchester deferred** (no maintained Python parser; rdflib doesn't cover
it; low real-world value). Earlier this session: **P2 — OWL `ObjectUnionOf` +
`ObjectAllValuesFrom` heads** (`tools/owl_to_clif.py`): disjunction translates in either
polarity (the De-Morgan `(or …)` double cut; a disjunctive head is non-Horn → contest peel),
and a **universal restriction in superclass position** prenexes to the flat OWL-2-RL Horn
rule (`SubClassOf(C, ∀R.D)` → `∀x∀y(C(x)∧R(x,y)→D(y))`) the materializer recognises — so it
genuinely fires (derives facts) + decides theorems via `theory_query`; `∀R.D` in negative
position stays reported-not-translated (first-reference vertex placement flips it unsoundly).
Strictly additive — stored ontology UoDs re-import byte-for-byte; 32 OWL tests (was 23), no
regressions. Earlier this session: **P2 — `cl-imports`
auto-resolution** (`src/cl_import_resolver.py`): a Common-Logic module's import closure is
resolved automatically (pluggable Mapping/Directory/ColoreWeb/Caching/Chain resolvers; BFS
dedupe; unresolved reported), wired into `from_clif_text/from_clif_file`. Landed
**`colore_field`** — the COLORE field algebra (4-module auto-resolved closure, nested
function terms relationalised), the first machine-resolved corpus ontology, drawn +
§3.3-attested (28 cuts); the 130-cut density closure is vendored + imports as data but stays
undrawn (layout-perf frontier). Prior sessions: **function terms relationalise on import**
(`(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧ density(z))`) + a **CLIF universal-quantifier
correctness fix** (parser+generator); the **T-box theorem query**
(`theory_query.entails`, freeze-a-witness), the **OWL→CLIF→EGI pipeline** (`owl_to_clif`),
two real ontologies landed (`bfo_core` BFO + `colore_between` from the real COLORE repo),
the `theorem` verdict **visible in `/agon`**, and a clutch of import fixes (CLIF `/* */`
comments, alpha-renaming reused variables, M-as-data non-attesting load), and P0/P1 (the 7
red layout tests triaged + Playwright E2E over `/agon` + challenge mode). **▶ Next session:
see ▶ NEXT SESSION** below for the open forks. Prior: the **freeform composition arc is COMPLETE** (steps
1–4: fix-time validity → draw-then-read canvas → legible EGI diff → **challenge
mode**). Also this session: the **persona narrative** (`docs/ARISBE_PERSONAS.md`)
and the **Domain Oracle** for Agon's model M (`docs/DOMAIN_ORACLE_AND_M.md`, step 1
built). The exact-correspondence engine (Phases 1–4) remains complete. Detailed
freeform history is condensed below; per-module mechanics live in git/docs/memory.

---

## ▶ NEXT SESSION — start here

**✅ DONE 2026-06-26 — the web-presentation audit ran + 5 fidelity fixes shipped (see the ▶▶▶ This session
block at the top).** Verdict: the rendered experience corresponds faithfully to the implemented ideas. Fixed
items 1/2/3/5 (launch-command doc bug · Agon worked-example default · challenge-mode discoverability · Organon
base-frame shape qualifier) and verified item 6 (witness line lights — no fix needed).

**▶▶▶ IMMEDIATE NEXT TASK (2026-06-27 directive): a CONSOLIDATION / planning pass — a tighter top-down
description of Arisbe (a "Vision & Scope + current-capability map + trajectory" spine) to serve three goals the
author named:** (a) capture retrospectively *what Arisbe does and why*, (b) state its *trajectory toward
fruition*, (c) enable focus / prioritization + onboarding of new collaborators. The author is not a trained
software engineer and did not start from a requirements doc; the raw material is abundant but **distributed and
episodic** (CURRENT_PLAN is a session-log palimpsest, not a spec; the docs/ spine is topic-deep but
context-assuming; much is implicit in `tests/` + the protected-core set). **This is consolidation/synthesis,
NOT from-scratch authoring** — the new spine should be thin and LINK to the deep docs, not restate them. See
the session-opening advice memo (to be written) for the recommended artifact shape + method (reverse-engineer
the de-facto requirements from tests + docs spine + `core_protection_system` set, then synthesize). Explicitly
**avoid heavyweight SRS/IEEE-830 ceremony** — wrong fit for a research-grade project. Decisions to settle at
session start: single-doc vs small set; how much roadmap detail; audience (solo-author vs newcomer-facing).

**▶ PART OF THIS PASS (author-added 2026-06-27): explicitly reconsider the "protected core."** It is one of
the three authoritative sources for the spine's *non-negotiables*, so re-audit it as part of the consolidation
rather than treat it as given. Cover: **(a) definition & mechanism** — today a git-diff guard on ~17 modules
(`tools/core_protection_system.py`: EGI data model + IO `egi_core_dau`/`egi_io`/`hierarchical_index`; the
linear parsers/generators EGIF/CGIF/CLIF; diachronic `universe_of_discourse`/`egi_transformation_history`; Dau
rules `formal_transformation_rules`/`rule_interaction`; Beta validators `subgraph_closure_validator`/
`graph_isomorphism_engine`; ligature `ligature_manipulation_rules`/`single_object_ligature_detector`),
enforced at pre-commit via `.core_modification_authorized` + the coupling "the mathematical core suite must
pass." **(b) how & why we have it** — guard Dau's formalization (the correctness bedrock) from inadvertent
change; force a deliberate authorization speed-bump. **(c) right scope now?** — reconcile the **count drift**
(gate says "16 modules", CLAUDE.md says "17"); question whether the *linear parsers/generators* are bedrock in
the same sense as the rules or are application-level; confirm the ligature/`hierarchical_index` members are
still load-bearing (ghosts were pruned May 2026 — verify no new ones); and weigh **ADDING** the newer
correspondence machinery now central to §3.3 (`correspondence_attestation.py`, `presentation_ops.py`,
`natural_layout.py`) — the correspondence invariant is *the central problem*, yet its runtime attestors may be
unprotected. **(d) still necessary?** — is it genuine safety or ceremony given the ~1000-test suite already
guards behavior; for a solo author, does the `.core_modification_authorized` dance + list-maintenance earn its
keep, or would "tests-as-spec + a CODEOWNERS-style note" suffice? Outcome feeds the spine's bedrock section.

**▶▶ MARKED FOR RECONSIDERATION LATER (author's call 2026-06-27 — do NOT pick up without a fresh directive):**
- **(4) the Context reflex overlay.** Leave as-is for now. It floats absolute top-left over every board (the
  one shared element that can occlude a left-heavy/large drawing). Revisit: dock-as-a-column vs
  auto-dim/collapse-on-overlap vs leave. (`js/context-reflex.js`, all 3 modes.)
- **(7) the newcomer / EGIF-authoring on-ramp.** A non-logician can now read a lit Agon verdict + land on a
  worked example, but still can't easily *author* their own M/G (jargon thrown cold at `index.html` + the
  Agon/Ergasterion setup). The larger, longstanding UX arc (first flagged 2026-06-24).

*(The original audit directive, now discharged, follows for the record.)*

**▶▶▶ ORIGINAL DIRECTIVE (2026-06-26, DISCHARGED): walk the web server and judge presentation ↔ underlying
ideas.** The author wants to **return to actually look at what the web server presents** (run
`uv run uvicorn --app-dir src web_api.main:app --reload --port 8000`, open `/organon`, `/ergasterion`, `/agon`) and assess
**how well the rendered experience corresponds to the underlying ideas we've implemented** — the correspondence
invariant, the three regimes, the warrant/standing gradient, the context reflex, the chain-of-semiosis, the
freeform draw-then-read flow, the Agon interpretation register, and the doctrine made legible (correspondence-
not-truth, level-zero, fidelity/departures). This is an **observe-and-assess pass first, not a build**: drive
each mode like a real user, catalogue where the screen faithfully *shows* an implemented idea vs. where the idea
is real in the code but invisible/garbled/misleading on screen, and bring the gaps back to the author before
editing. (Much backend/doctrine has shipped while the *interface's* faithfulness to it went unaudited; the last
true UX passes were cross-mode coherence pass 1 (2026-06-24) and the 2026-06-15 consistency pass. The
just-built diagram↔narration harness is a *measurement* tool, not surfaced in the UI — consider whether any of
its in-view findings should inform what the viewer shows.) Use the `verify`/`run` skills to launch and observe.
*(The cross-mode UX coherence arc below is the prior framing; this directive narrows it to "does the picture on
screen match the idea in the code?")*

**▶▶ Prior framing (2026-06-23 directive): cross-mode UX coherence, use-case-driven.** The author
wants to return to the **whole-experience** UX across the three modes — Organon, Ergasterion, Agon — judged
against **several distinctly different use cases** (not internal-consistency drift, the 2026-06-15 pass
already did that). Two goals: **(1) a recognizable, consistent experience** — a user moving between modes
should find the chrome, vocabulary, camera, panels, and affordances familiar and predictable; **(2) the
views + interactions give a natural, intuitive appreciation of the *drawings* themselves** — the pictures
read as logic-in-pictures, not as diagrams to decode. This is **explore-and-decide first, not a fixed
build:** enumerate a handful of concrete personas/use-cases (e.g. a teacher walking a class through a proof
in Organon; a student composing freehand in Ergasterion; a researcher contesting a claim in Agon; a logician
round-tripping a form across modes), walk each end-to-end, and catalogue where the experience breaks
recognizability or where a drawing fails to read intuitively. Bring findings back to the author before
committing edits. *(The doctrine-legibility threads below — warrant gradient, context reflex, dragons,
correspondence chord — all shipped; this is the next, broader UX arc.)*

**▶▶ Prior framing (2026-06-19 handoff): the UX pass — "how all this plays out in the interface."** Candidate
doctrine-legibility threads (now all shipped — kept for the record):
- ~~**Make posited-vs-derived / the warrant gradient visible.**~~ ✅ **DONE 2026-06-20** — `standing_of`
  + the Organon list/detail badge (○ posited / ◇ … / ⛓ derived / ⚔ withstood) with the
  correspondence-not-truth non-claim in the tooltip. ([[project_warrant_gradient_visible]].) **Fast-follows
  ✅ DONE 2026-06-23:** (1) **standing surfaced in Agon** — both disposition services
  (`apply_disposition` game-path, `apply_contest_disposition` contest-path) now return a `standing` block
  (`standing_of(tags, has_chain=True)` — contest → ⚔ withstood, game → ⛓ derived, honestly), rendered as an
  `✓ Asserted into the corpus` confirmation card with the badge + non-claim in `agon.html` (both
  `dispose`/`disposeContest`). (2) **style-only reprojection affordance** — Organon's view toolbar shows a
  `↺ style-only reprojection · standing unchanged` note whenever a non-default style/layout is active,
  stating in words that the restyle redraws the same proposition and inherits its standing. Extracted the
  badge markup+CSS into a shared `js/standing-badge.js` (Organon migrated to it; Agon reuses it). Tests:
  +2 route asserts (`test_grapheus_routes`/`test_agon_routes` carry `standing`), +1 E2E (reprojection note
  toggles). Core-protection CLEAN. ([[project_warrant_gradient_visible]].)
- ~~**The context reflex in the UI.**~~ ✅ **DONE 2026-06-22** — a shared `ContextReflex` panel
  (`js/context-reflex.js`) across **all three modes** (author chose the cross-mode option): "what context
  lets you read this?" = **the ground** (universe + standing + derivation position "state N of M") + on
  element click **the structure** (the enclosing-cut breadcrumb `⊙ sheet › ¬ › ¬ ▸ here`, polarity/depth in
  words). The UI face of the just-closed *contextual honesty* doctrine. Key fix: introspection must be
  bundled with the render (matching ids), so added it to Organon's detail + chain-frame payloads (Ergasterion
  + Agon already carried it). Polarity in words, never hue (floor #6). E2E `test_context_reflex_e2e.py` (4);
  17 existing mode E2E still green; core-protection CLEAN. ([[project_context_reflex_built]];
  [[feedback_newcomer_accessibility_dragons]].)
- ~~**"Correspondence, not truth" made legible.**~~ ✅ **DONE 2026-06-23** — the shared `LinearFormPanel`
  (`js/linear-form-panel.js`, in **all three modes**) now carries a **correspondence chord** line in its
  body: `≡ picture ↔ proposition · §3.3 correspondence, not truth`, with a tooltip naming what §3.3 silently
  attests on every render — *this linear form and the drawing denote the SAME graph; it certifies they match,
  NOT that either is true*. The panel was already the picture-beside-proposition home, so the chord just
  names the relation. E2E `test_correspondence_chord_on_linear_form`. *(The 2026-06-20 seed — the standing
  badge tooltip's non-claim, 🐉6 — remains; this adds the picture↔proposition chord itself.)*
- ~~**A "dragons" challenge set.**~~ ✅ **DONE 2026-06-20** — the five *drawable* field-guide dragons are
  now challenges (🐉 in the picker), graded with the antidote handed back on a wrong attempt. Dragons 6-8
  are conceptual, not drawable — they fold into the warrant / correspondence-not-truth threads above.
  ([[project_dragons_challenge_set]].)
- **General cross-mode learner affordances.** The last focused UX pass was the 2026-06-15 cross-mode
  consistency pass (design-system.css, camera, vocab); this is the first UX pass aimed at *newcomers and
  the doctrine's legibility*, not internal consistency.

**✅ DONE 2026-06-21 — DOCTRINE: the LEVEL_ZERO rework + the `assertion-4` closure** (author-flagged
2026-06-20, "we must not forget to make this crystal clear"). Discharged this session, docs only,
core-protection untouched: (1) `docs/LEVEL_ZERO_AND_THE_REGISTERS.md` reworked with the gapless account of
assertion as its **spine** — thesis recast (the blank is the only unconditioned thing; no unconditioned posit
anywhere; the Alpha asymmetry makes a positive-recto contingent posit a *forbidden move*); §4 assertoric
register = a **conditioned given via `INS`**, not a naked recto posit; §5 retitled + new "How a given enters:
the construction from the blank" (`DC+`·`INS`·`IT+`·`DC+`) + two worked cases (**Praeclarum** demonstrative-
all-cuts, **the scroll** assertoric-given); §7 guard refined; §8 committed-position rewritten + a boxed
`assertion-4`-closed note. (2) `docs/ADVERSARIAL_EXAMINATION.md` — correction note + superseded amendment-4
in **Departure II** (the handoff said "Examination II", but `assertion-4` actually lives in *Departure II* of
the first examination; Examination II = the A&B Larger-Game examination, where no verdict moves — corrected in
place with a parenthetical noting the slip). (3) `docs/FIDELITY_AND_DEPARTURES.md` §3 "A construction…"
paragraph strengthened to the gapless form for consistency. Memory [[project_level_zero_registers]] TODO
discharged. *(The original crux follows, kept for the record.)*

**▶▶▶ THE DOCTRINE CRUX (recorded; now realized in the docs above):**

- **The blank sheet is the ONLY unconditioned thing — and it is not a posit; it asserts nothing** (true by
  withholding). It is the sole fixed point.
- **There is no unconditioned posit anywhere.** An "unconditioned M" — a contingent claim sitting
  categorically on the *positive* recto — would **violate the rules** (insertion into a positive context is
  forbidden). So a bare contingent assertion on the sheet is not a foundation; it is a *forbidden move*.
- **Every assertion enters as a contingent GIVEN in a NEGATIVE context, built from the blank by legal,
  truth-preserving nesting:** `DC+` opens a negative ring · `INS` places the given there · `IT+` carries any
  graph (incl. a domain model) where it must bear · `DC+` again opens the next ring. The recto stays
  **nothing but cuts** (consistent with the earlier-agreed "truth-preserving UoD = all cuts, no exposed
  predicate"). A domain model is built-from-scratch (nesting) or imported-and-embedded via `INS` into a
  negative context — a **running, dialogical, world-tested, sweepable** (`ERA` from positive = "free to
  demote") contingency; never an unconditioned foundation.
- **What the calculus does NOT supply is the *content* (which M)** — and that is *not a gap* but the proper
  contingency, answered in the world and the Agon. (`assertion-4` conflated "can't fix which M" with "can't
  *place* M"; `INS` places it.) → **Examination II's conceded `assertion-4` gap is CLOSED (over-conceded);
  the LEVEL_ZERO "always-already conditioned / inside" thesis is gapless, vindicated.** No A/B verdict moves.
- **THE STANDING CHALLENGE is contextual honesty:** tracking *what context (nesting / regime / given)
  delivers a graph's interpretive meaning* — which IS the central correspondence problem, the field guide's
  context reflex, the three regimes, and §3.3, at once.

Tasks: (1) rework `docs/LEVEL_ZERO_AND_THE_REGISTERS.md` with this as the spine; re-scope the "cannot say" /
"always-already inside" language to the now-gapless form; worked cases = Praeclarum (built from blank, all
cuts) + the scroll + DC+/IT+/INS nesting. (2) Add a **correction-note to `docs/ADVERSARIAL_EXAMINATION.md`
"Examination II": `assertion-4` closed by the nesting argument.** ([[project_level_zero_registers]].)

**▶▶ Also still open (deferred, not urgent):** fork-(c) fast-follows (multi-candidate disambiguation;
LOW-warrant `/import/admit` persistence); the **reflexive-diagonal** argument for
Departure I's open joint ([[project_fidelity_and_departures]]). See "▶▶ Other open tracks" below for the
full menu.

**✅ DONE 2026-06-18e — BUILD A frontend + E2E (the fold-to-define UI; build A now COMPLETE).**
`src/web_viewer/ergasterion.html` only (unprotected; backend/routes were 0b1f1aa). A **"Define —
abstract a subgraph"** panel inside `derive-block` (shown in the deriving/Argument workspace): a name
input + a **"⟝ Designate ports"** toggle (`definitionPortMode`) that routes canvas clicks to an ordered
`definitionPorts` list — a click names the next hook line (a vertex) in argument order, mauve
`.def-port` highlight, "ports: 1·x  2·y" readout — while the existing `selectedSubgraph` stays the body.
**Define & fold** → `POST …/define-fold` (selection=body, ports=ordered, from_state_id=current view so
an earlier state forks a branch), resets authoring + holds the camera on success, and reports refusals
in-panel (`#def-feedback`; a missing name is caught client-side, never reaching the server). A
`#definitions-list` rendered from the payload's `definitions` block lists authored names with a
per-live-spot **unfold** button → `POST …/define-unfold`. Esc and engaging Settle disarm port mode.
Tests `tests/test_ergasterion_define_e2e.py` (2, Playwright: draw man(x)→fix→select+designate-port+fold
→ a live unfoldable spot, 'man' abstracted away; unfold → body back, definition persists; no-name fold
refused in-panel + non-mutating). 74 green across ergasterion/freeform/define route+E2E suites; 2 new
E2E green; core-protection CLEAN; additive (one HTML file + one test). Memory: [[project_fold_to_define]].

**▶▶ Other open tracks** — the adaptive-scope viewer track, the cross-mode
UX pass, the FOLIO/DLCore coverage lever, **fork (a)** (EGI bridge + EPR lever), **fork (b)**
(schema-drawing/§3.3 — found already built+tested, closed), AND **fork (c) increment 1 + the
`/agon/propose-nl` web route** (the NL→logic LLM front-end — ✅ block immediately below) are all
complete. **Open next:** fork (c)'s remaining fast-follows — **multi-candidate disambiguation**
(G1,G2,G3 ranked by verdict — the distinctively-Peircean "disambiguate by interpretation, not
parser confidence") and **LOW-warrant `/import/admit`** persistence of a tested proposal carrying
its NL+LLM provenance as the bibliographic trace. *(The author's external-conversation re-evaluation
is now DISCHARGED — see ✅ DONE 2026-06-18b below + `docs/MODALITY_WITHOUT_GAMMA.md`: modality needs
no Gamma; the real frontier is second-order logic about the graphs.)*
*Residual coverage tails left as honest, runtime-bounded frontiers (not soundness gaps):* DLCore
consistency/instance abstainers beyond the finder's domain cap; 2 non-EPR (Skolem-function) FOLIO
entailments; 8 unparsed FOLIO formulas (parser limits).

**✅ DONE 2026-06-18 — fork (c) increment 1: the NL→logic LLM front-end (*LLM proposes, Arisbe
disposes*).** The deferred front-end is unblocked now both backends are in place and the
vocabulary-miss/fact-miss gate (`dl_reasoning.OUT_OF_SIGNATURE`) exists. The thinnest sound slice,
with a **strict boundary**: the LLM emits only a candidate **FOL string** (the existing `folio_fol`
grammar) + a declared vocabulary; everything downstream is deterministic and pre-tested.
`src/nl_to_logic.py` (unprotected, additive): `propose(nl, *, vocabulary_hint, client=…)` calls
Claude (`claude-opus-4-8`, **forced-tool structured output** `emit_fol`, adaptive thinking; SDK
import **guarded by `ANTHROPIC_AVAILABLE`**, client injectable) → `build_proposal` parses
deterministically (`parse_fol` → `folio_fol_to_egi` → `generate_egif`) — a malformed candidate is
**reported** (`parse_error`), an `unmappable` sentence stays honestly unbuilt, an API error is
captured (never crashes). `reconcile` splits the proposal's predicates into **addressable** vs
**out-of-signature** against M (`ontology_signature`) — the vocabulary-miss made first-class.
`interpret_against` runs the **same peel** as `/agon/interpret` (mirrors `_interpret_payload`).
The LLM **never touches the EGI and never asserts truth**. `tools/nl_to_logic_cli.py` drives it,
incl. a `--no-llm --fol` path that exercises the whole disposing half with zero network. Decisions
locked with the author: FOL target / single best parse / module+CLI surface. Tests:
`tests/test_nl_to_logic.py` (12 + 1 live, key-gated) — round-trip via `same_graph`, malformed→
reported, unmappable, API-failure capture, declared≠used flag, reconcile split, peel verdict +
cross-check vs `_interpret_payload`. Regression: 101 green across nl/folio/agon/dl/egi-to-fol;
core-protection CLEAN; CLI smoke verified (deterministic path + graceful no-key failure). Dep:
`anthropic>=0.40` in a new optional `nl` extra. **Also shipped the `POST /agon/propose-nl` web
route** (`AgonProposeNLRequest`; resolve M → hint the LLM with M's signature → propose →
reconcile → peel; an unmappable/malformed candidate returns `parsed:false` with the reason, not
an error; LOW warrant, nothing persisted) + `tests/test_propose_nl_route.py` (5, LLM mocked at
`_default_client`) + **full doc `docs/NL_TO_LOGIC.md`**. Memory:
[[project_nl_to_logic_arisbe_as_interpretant]].

**✅ DONE 2026-06-18b — the external-conversation handoff is DISCHARGED (doctrine, not code).**
The author supplied the conversation (archived `docs/references/EG-modality-conversation.pdf`). It
was overwhelmingly *confirmatory* of the existing floor and settled one long-open question
definitively: **Gamma conceived as a modal extension is not a problem Arisbe needs to solve.** New
doc **`docs/MODALITY_WITHOUT_GAMMA.md`** makes and defends the claim at the level of model theory:
the **standard translation** sends □/◇ to ordinary Beta quantifiers over an accessibility relation,
and Arisbe's diachronic DAG (worlds = sheets, R = legal transition) and corpus of M's (worlds = M's)
*are* that frame, **drawn rather than hidden** — so the broken cut → ∃/∀ over accessible sheets,
tinctures → the explicit identity of which UoD a region inhabits, and Peirce's unsolved trans-world
identity → a **line of identity carried across a legal transition** (the across-DAG invariant Arisbe
already keeps inerrant). Complete (modal logic = the bisimulation-invariant fragment of FOL, van
Benthem) and clearer (the frame is exhibited, not metalinguistic); honest limits stated (first-order-
definable frames only; succinctness traded for explicitness; adequacy argument, not a mechanized
theorem). Reconciled `docs/MANIFEST_AND_MEANING.md` (floor #6 → "no modal mark needed at all"; floor
#4 → fact = defeasible last-standing status; the membrane → the **third position** recorded
*alongside* Peirce's convergence, not replacing it) and `docs/CHAIN_OF_SEMIOSIS.md` (convergence
divergence noted; pointer added). Adjusted the "reserved-for-Gamma" channel wording in the adaptive-
scope docs (the channels are *not* reserved against modality). **No code, no bedrock touched**
(core-protection clean). **Two horizons named, neither started:** (1) **the real frontier =
second-order logic about the graphs themselves** (graphs of graphs, abstraction, predication of
qualities — *not* modal, *not* a colour mark; toe-in-the-water = the φ-hole/schema node `src/schema.py`
+ the math track [[project_math_fixtures_zfc_peirce_schema]]); (2) **concision-bearing abbreviation**
(the "map" level-of-detail doctrine — a future modal-*looking* glyph is admissible only as a
non-load-bearing map symbol gated by the overview *expansion law*, generalizing the shipped
adaptive-scope overview). **Scoped-not-built code candidate:** an explicit *logical demotion* event
(first-class "free to demote") — verdict: **no new bedrock needed**; Agon (a graph drawn back under a
cut + re-challenged) and `src/liveness.py` (reversible retire/revive) already cover it; at most a thin
convenience, flagged not built. Memory: [[project_modality_without_gamma]].

**✅ DONE 2026-06-18c — second doctrine pass: Level Zero + the two registers (no code).** A part-two
conversation (archived `docs/references/EG-level-zero-conversation.pdf`) → new
**`docs/LEVEL_ZERO_AND_THE_REGISTERS.md`**. Overwhelmingly confirmatory + foundational. Key results:
**(a)** "context" equivocates between *enclosure* (depth, what the formal literature handles) and
*ground* (whose sheet/universe/commitments — context-as-ground, on which level 0 is silent); the
blank sheet is itself a graph (Peirce's Phemic Sheet; assertion = assuming responsibility = exposure =
falsifiability). **(b)** The author's **level-0 theorem** — no unenclosed *contingent* proposition is
derivable from the blank — confirmed from **soundness**; only scaffolding (the scroll) originates at
depth 0. **(c)** Two **registers**: *demonstrative* (derived-truth-preservingly = the **chain**) vs
*assertoric* (posited-under-warrant = a premise / **import at LOW warrant** / sent to Agon); the
literature's sin is leaving the seam unmarked — Arisbe already marks it. **(d) The standout:**
assertion has a formal Alpha home — the **scroll** `cut[ M cut[P] ]` ("P given M"), and because M sits
in a negative context, **revising M is a sound INS on the antecedent**, not stance-taking. This is
*literally* the Agon interpretation register's "given M, then G" inning + the formal home of the
diachronic **"free to demote"**. **(e)** Sharpened *falsifiability* (world-facing, the membrane) vs
*defeasibility* (in the rules, the scroll). Reconciled MANIFEST floor #2, CHAIN_OF_SEMIOSIS (two
registers), DOMAIN_ORACLE_AND_M (new §4a), MODALITY_WITHOUT_GAMMA (free-to-demote home + footer). The
"names can't purchase permissions" theme is the philosophical backdrop for **build A** (a definition's
legitimacy = its expansion + soundness gate, not its name). Core-protection clean. Memory:
[[project_level_zero_registers]].

**✅ DONE 2026-06-18d — BUILD A backend + routes (fold-to-define; frontend shipped in 18e above).** The
visible face of the second-order/abstraction layer — *name this drawn subgraph and reuse it as a
single spot.* **Backend + routes (this block) + frontend/E2E (✅ 18e above) all complete.**
- **Backend core** (`src/definitions.py`, additive): `Definition.from_egi` (a definition whose body
  is a pre-built EGI, not EGIF text) + `definition_from_selection(egi, selection, ports, name)` —
  re-roots a selected sub-structure into a standalone body EGI so `fold_selection` can fold under it
  and `expand_at` unfold it; the body is the selection re-rooted, isomorphic by construction (and
  re-checked by `fold_selection`'s two soundness gates). Refuses a dangling line. Tests
  `tests/test_definition_authoring.py` (4): nested-cut + flat round-trips via `same_graph`, refusals.
- **Routes** (`/ergasterion/sessions/{id}/define-fold` + `/define-unfold`): author+fold / unfold a
  defined spot, recorded as meaning-preserving `definition.fold`/`definition.unfold` chain steps
  (earlier `from_state_id` forks a branch); phase-gated to a *fixed* graph. A **session-scoped
  `DefinitionRegistry`** on `WorkshopSession` persists authored definitions; the session payload now
  carries a `definitions` block (names + live spots). Tests `tests/test_ergasterion_define.py` (5):
  round trip + dangling/duplicate-name/non-spot/composing refusals. 104 green across ergasterion/
  freeform/challenge/definitions/chain-persistence; core-protection CLEAN; additive only.
- **Frontend + E2E: DONE (✅ 2026-06-18e above)** — the Define panel, ordered port designation, fold,
  per-spot unfold, and 2 Playwright E2E. **Later (not built):** folded-graph promotion to Agon
  (expand-first); a richer definitions side panel; multi-port re-ordering.

**✅ DONE 2026-06-17 — fork (a): the EGI model-finder bridge + the EPR complete-decision lever.**
Two deliverables, both sound and measured against Z3.
- **(a1) The EGI→FOL bridge + DLCore's negative half.** `src/egi_to_fol.py` — the **read-only**
  inverse of `folio_native._build` (cut→¬, juxtaposition→∧, generic vertex→∃ at its home area,
  constant vertex→free term). It *observes* the immutable graph and emits a `folio_fol.Formula`;
  it never mutates, never calls a `with_*` builder, and is wholly outside the transformation
  calculus — **the bedrock (egi_core_dau, the six rules) is untouched; core-protection CLEAN**.
  Faithfulness pinned by Z3 (read-back of `_build(φ)` ≡ φ). Wired into `dl_reasoning`:
  `check_instance` now exhibits a model of `M∪{¬C(a)}` to certify **non-entailment** (sound NO),
  `check_consistency` a model of M to certify **consistency** (sound YES) — the two branches the
  Horn engine could only abstain on. UNA is sound here by construction (EGs are equality-free;
  identity is the shared *line*, not an equality atom, so M can't force two constants equal) and
  surfaced in the verdict. **DL-ReasonSuite instance-check 50 % → 75 %, soundness 100 %** (0 wrong);
  consistency dl 100 %/el 60 %, subsumption 100 % (unchanged; abstainers beyond the domain cap).
- **(a2) The EPR (Bernays–Schönfinkel) lever — FOLIO native 63.2 % → 95.1 %.** The 75 abstentions
  were 61 unrefuted gold-True/False (a disjunction trapped *under* a ∀ — the top-level case-split
  can't reach it) + 6 gold-Uncertain. FOLIO is function-free relational FOL **without equality**,
  so an `∃*∀*` (no ∃-under-∀) inning is EPR and has the finite-model property: grounding over the
  small-model bound (`|consts|+|∃|`) is a **complete** sound decision. `folio_model_finder.decide_epr`
  reuses the finder's grounder+Tseitin+DPLL; `decide_native` calls it **last** (after the cheaper
  paths) so it purely adds coverage, `via="epr"`. **Coverage 63.2 % → 95.1 % (194/204), soundness
  100 % vs Z3 (194/194), 0 genuine errors.** The "raise the model bound" lever proved unnecessary —
  EPR subsumed the structured headroom (incl. the gold-Uncertain via both-`sat`). Tests:
  `test_egi_to_fol.py` (14) + `test_folio_model_finder.py` (→14) + `test_folio_native.py` (21) +
  `test_dl_reasoning.py` (→15). Regression: 237 across folio/dl/theory-query/materialization/agon/
  grapheus/semantic/owl/rdf + math core green. Additive (new module + unprotected-module edits).
  Docs: `docs/FOLIO_EVALUATION.md`. Memory: [[project_nl_to_logic_arisbe_as_interpretant]].

**✅ DONE 2026-06-15 — the finite-model-finder lever (FOLIO coverage lever, model-construction half).**
The dual of refutation: soundly certify `Uncertain` (and non-entailment) by **exhibiting a model**.
`src/folio_model_finder.py` — a bounded finite-model finder (Arisbe's *own*, not Z3): `M ⊭ C`
witnessed by a model of `M ∪ {¬C}`, `M ⊭ ¬C` by a model of `M ∪ {C}`; **both exist ⇒ Uncertain**
(two real models prove independence). FOLIO's fragment is function-free relational FOL (no equality),
so a finite model = finite domain + predicate extension: domain = constants (distinct, sound UNA) +
a few anonymous existential witnesses; **ground** quantifiers over it (`∀`→∧, `∃`→∨); **Tseitin→CNF→
DPLL** (a small home-grown solver). An independent `satisfies` evaluator re-checks every found model
against the original FOL before it is trusted (the guard the verdict's soundness rests on); bounded
by a witness cap + DPLL node budget, abstains on exhaustion. Wired into `decide_native` (verdict
`Uncertain`, `via="model_construction"`). **Validation (204): coverage 28.9 % → 63.2 % (59 → 129),
soundness 100 % vs Z3 (129/129 decided agree with the complete oracle)** — decides **61 of 69**
gold-`Uncertain` (0 before), zero over-firing. **Soundness is now judged against the FOL semantics
(Z3), not the noisy gold:** the only 9 gold-disagreements are *all* corroborated by Z3 as gold-noise
(same conservative X→Uncertain errors increment 1 found) — **0 genuine errors**. The `--native`
harness was reworked to cross-check each decided verdict against Z3 and report soundness-vs-Z3 +
gold-noise. Tests: `tests/test_folio_model_finder.py` (9) + `test_folio_native.py` (→21, the old
"never predicts Uncertain" tests repurposed to the new sound capability). Regression: 112 green
across folio/dl/theory-query/materialization/agon. Additive (new module + harness rework + docstring/
`NativeResult` updates). Docs: `docs/FOLIO_EVALUATION.md`. Memory: [[project_nl_to_logic_arisbe_as_interpretant]].

**✅ DONE 2026-06-15 — the disjunctive case-split lever (FOLIO coverage lever, refutation half).**
The bounded native engine could not reach an entailment that needs **reasoning by cases**
(`P∨Q, P→R, Q→R ⊢ R` — every disjunct forces `R`, but no single denial fires). Added the tableau
β-rule on top of the Horn closure (`src/folio_native.py`: `_refutes_cases` / `_refute_rec` /
`_disjuncts` / `_flatten_and`): `M ∪ {A∨B}` is unsatisfiable **iff** `M ∪ {A}` and `M ∪ {B}` both
are, so a **top-level** disjunction is split and *every* branch must close at the existing sound
Horn+denial primitive; `∨` branches directly, `⊕`/`↔` via their two models; a split budget bounds
the search and `all(...)` short-circuits. **Sound by construction** — branches are exhaustive given
the disjunctive conjunct holds (all-refuted ⇒ refuted; one branch open ⇒ abstain, never
over-decides a genuine `Uncertain`); splits **only** top-level disjunctions (one trapped under a ∀
is left to the residue, since `∀x(P∨Q) ≠ (∀x P)∨(∀x Q)`). **Validation (204): coverage 23.0 % →
28.9 % (+12 decided, 47 → 59), soundness held at 100 % (59/59), confusion still clean,
gold-`Uncertain` still never decided.** Tests: `tests/test_folio_native.py` 16 → **20**.
Regression: 102 green across folio/dl/theory-query/materialization/agon. Purely additive (new
functions + `decide_native` wiring tags `via="case_split"`). Docs: `docs/FOLIO_EVALUATION.md`.
Memory: [[project_nl_to_logic_arisbe_as_interpretant]].

**✅ DONE 2026-06-15 — the cross-mode UX consistency pass** (the last adaptive-scope item; the
viewer track is now closed). Audit-first per the plan: an Explore agent catalogued the drift across
`organon.html` / `ergasterion.html` / `agon.html` + the shared `diagram-viewer.js` / `mode-nav.js`
/ lenses before any edit. Findings → four reconciliations.
- **Shared tokens.** New `src/web_viewer/css/design-system.css` is the single source of truth —
  the palette named by provenance (**Catppuccin Mocha** dark chrome `--ctp-*` + **Catppuccin Latte**
  for Organon's read-only detail header `--ltt-*` + custom `--select-*`/`--phase-*`/`--kind-*`/
  `--lens-*`), semantic aliases (`--panel-bg`/`--text-muted`/`--accent`/…), an 8-step spacing scale,
  radii, type, and shell rhythm (`--panel-width`/`--header-pad`/`--statusbar-pad`). All three shells
  link it after `styles.css` and **fully consume it: zero `#rrggbb` literals remain in any shell**
  (verified) — every prior literal maps to a value-identical token, so the change is centralization,
  not recolour. (Lens three.js numeric colours can't take CSS vars; `--lens-*` is their documented
  mirror.)
- **Camera convention.** The three modes' `DiagramViewer.render` options are *deliberately*
  different, not drift: canonical default `fit` on a new graph; Organon re-`fit`s independent chain
  frames (+`dolly`) & `keep`s on overview-expand, Ergasterion `keep`s but yields to overflow, Agon
  `hold`s absolutely (the board must not move under the player). Documented, not force-unified.
- **Vocabulary.** Canon = **move** (a rule application) / **state** (a position in a derivation).
  Aligned Organon's visible strings (was "step"/"frames" → "move"/"state"; nav titles → "Previous/
  Next move") + the storyboard lens label; Ergasterion/Agon already matched.
- **Chrome.** Fixed Organon's status-bar padding drift (`6px 18px` → `--statusbar-pad`); header/
  status paddings tokenized. Agon's 340px columns left intentional (denser setup/disposition) and
  documented as such.
- **Doc:** `docs/WEB_VIEWER_DESIGN.md` — the scoped "DESIGN.md" companion (tokens + camera + vocab +
  chrome + known follow-ups). Decided *against* a global DESIGN.md (redundant with CLAUDE.md + the
  docs spine); the article's value applies precisely to the web viewer's design system, which had a
  real gap. **Tests:** 99 web route/interpretation + 18 browser E2E (lenses, overview, agon,
  freeform, challenge, grapheus) all green; every referenced token verified defined. Purely
  additive (new CSS + new doc; HTML/lens edits are literal→token + string-only). Memory:
  [[project_adaptive_scope_viewer]], [[project_web_viewer_design_system]].

**✅ DONE 2026-06-15 — derivation-DAG lens** (branch structure; the 3rd deferred item). A
reasoning episode is a DAG: two rules from one state **fork**, two reaching the same graph
**converge** (alternate-proofs diamond). Three pieces: **(1) substrate** — made the V1-linear
chain DAG-capable: `ChainStep.branch_id` (optional); `ProofChain.at(state_id)` (fork),
`branch=` label, `converge_last_into(state_id)` (merge, refuses non-`same_graph`); persistence
round-trips the topology. **(2) native fixture** — `tools/build_branching_demo_chain.py` → corpus
UoD `branching_confluence` (*confluence of erasure*: from `(P)(Q)(R)` erase P,Q either order →
`(R)`; real ERA per edge, §3.3-attestable; authored demonstration, method-only provenance). The
alternate-proofs idea realized **natively** in Dau's calculus, not imported from TSTP/Metamath
(their steps aren't Peirce rules → would break the sound-step floor — see the discussion this
session). **(3) endpoint + lens** — `/history-structure` emits a `dag` block (node/state +
edge/step + longest-path depth + `branching`); `/chain` carries `branching` so linear lenses
(storyboard/time-stack) show only for a line, the DAG lens for any chain;
`src/web_viewer/js/derivation-dag-lens.js` layers states by depth, real drawing per node, edges
arrowed+coloured by branch with rule/diff pills (prior art: Sutcliffe's IDV, borrowed in spirit).
Tests: `test_branching_chain.py` (8) + E2E. Additive (+ `ChainStep.branch_id` field; corpus +1
UoD). Doc: `docs/ADAPTIVE_SCOPE_VIEWER.md` §10. Memory: [[project_adaptive_scope_viewer]].

**✅ DONE 2026-06-15 — liveness/desuetude tracking** (manifest floor #7, *two deaths so track
liveness*). `src/liveness.py` — a `LivenessLog` (one compact summary per UoD: first/last/count/
per-kind tally/retired, in a single gitignored `tomos/.liveness.json`) + desuetude policy
(`alive` if consulted ≤ `DORMANT_AFTER_DAYS=90`, else `dormant`; `unconsulted` if never;
`retired` if deliberate — re-consulting revives). Consultations recorded at two chokepoints:
**Organon view** (`GET /uods/{id}` → `viewed`) and **Agon model-use** (`_resolve_model_egif` →
`model`). Surfaced as a forward-facing facet in the Organon detail panel (status dot + "consulted
N× · last …" + a reversible **Retire/Revive** toggle; routes `POST/GET …/liveness[/retire]`) and
a list-row status dot. Outside §3.3 (consulting a sign is not a sign); never mutates the UoD.
Tests: `test_liveness.py` (8) + `test_liveness_routes.py` (6, both chokepoints) + E2E facet
toggle. Additive (new module + routes + organon.html facet; manifest "provenance faces forward"
now realized). Doc: `docs/ADAPTIVE_SCOPE_VIEWER.md` §10 + `docs/MANIFEST_AND_MEANING.md`. Memory:
[[project_adaptive_scope_viewer]].

**✅ DONE 2026-06-15 — time-stack production lens** (first deferred item). `src/web_viewer/js/
time-stack-lens.js` (ES module, lazy-imported), wired into `organon.html`'s Lens selector beside
Storyboard (both shown only for a chained UoD). The recorded derivation as a navigable 2.5-D
solid: each sheet the *real styled* drawing at that state stacked along the (earned) derivation
z-axis, **blue survivor threads** + **green/red entry/exit dots** (rule added/erased) + per-sheet
rule labels. The spike's flagged **sloping threads** fixed *correctly*: a survivor can't move
independently of its drawn sheet (the thread must touch it — correspondence), so instead of a
conservative *layout* each frame is **rigidly registered** onto the previous by the best
survivor-matching similarity (uniform scale + translation, no distortion) — survivors stand
columnar; a thread slopes only on an honest relayout. Validated on the 8-frame Praeclarum chain:
mean survivor drift **45.9 → 11.9** world units (~75 %). E2E
`test_organon_lenses_e2e.py::test_time_stack_lens_for_a_chained_uod` (3 lens E2E green, zero
console errors). Purely additive (new lens module + 3 small organon.html wiring edits). Screenshot
`docs/assets/adaptive_scope_spike/d2-timestack-praeclarum-aligned.png`. Doc:
`docs/ADAPTIVE_SCOPE_VIEWER.md` §10. Memory: [[project_adaptive_scope_viewer]].

**✅ DONE 2026-06-15 — the 250-cut frontier wall-clock measurement (build-order step 4 tail) —
which also found & fixed a budget mis-tuning.** `tools/overview_frontier_benchmark.py` — the
paired baseline on the genuine frontier UoD, the **full SUMO ground taxonomy** (123 subsumptions
→ **246 cuts**, 132 V, 255 E), rebuilt from `docs/references/SUMO1.2.txt` via
`tools/suokif_to_eg.py` (it is *not* stored — only the depth-≤2 86-cut `sumo_upper` spine is,
which lays out in ~1 s and hides the win; the full taxonomy is the ELK super-linear shape that
can't be saved as a drawn UoD — the very frontier this measures). **Result (this laptop): full
ELK `generate_layout` of all 246 cuts ≈ 289 s (unusable interactively) vs overview at the
(newly-tuned) default budget ≈ 0.8 s — a ~340× speedup — and it §3.3-attests (`attest_overview`
passes).** Overview lays ELK out over **147 cuts** (24 opened + 123 leaf placeholders) instead
of 246 cuts with full interiors + 255 cross-cutting lines; 99 hidden. **Finding — the frontier
is *breadth*, not depth:** SUMO is only depth 2, yet slow, because ELK super-linearly packs 123
sibling scrolls + routes 255 lines of identity among them (a deep nested *chain* = ~0.2 s).
**The budget cliff + the fix:** the cost tracks the lines routed *among* opened cuts, not the
opened *count*, so the budget cliffs hard — a deterministic sweep shows **0→35 all <1 s but
40 → ≈210 s, 60 → ≈275 s** (≈ whole-graph time). The old `DEFAULT_OVERVIEW_BUDGET=40` thus put
the *default* overview of the frontier graph back over the cliff. Fixed: (a) `_resolve_collapsed`
now **sorts** the auto-expand BFS (deterministic — per-process hash randomization had made it
vary, and an early ad-hoc run fluked a misleading fast 1.1 s); (b) default lowered to **24**
(≈0.8 s, margin below the cliff). Future refinement = a degree-aware budget (hub scrolls force
global routing). Additive except the two small `layout_service` tweaks (sort + default). Doc:
`docs/ADAPTIVE_SCOPE_VIEWER.md` §9 step 4 + §1. Memory: [[project_adaptive_scope_viewer]].

**✅ DONE 2026-06-15 — overview client wiring + E2E (build-order step 3 + the E2E half of step 4).**
The overview is now usable in the browser. `web_viewer/organon.html`: a new **"Drawing — overview
(adaptive scope)"** Lens option; `renderOverview()` fetches `?lod=overview&expand=…` and renders
via the shared `DiagramViewer` (camera `fit` on entry, `keep` on expand so detail appears in place
— the map-app feel); `decorateOverview()` overlays a **badge** on each collapsed placeholder (read
from the cut `<g>`'s `getBBox()`, so no renderer-offset math), showing form-only counts (rel /
cuts / lines, + "⇢ N enter" when a line of identity crosses in) and a "＋ expand" hint;
**tap-to-expand** is wired per-badge (a `mousedown` `stopPropagation` so svg-pan-zoom doesn't eat
the click as a pan), plus a **Collapse-all** control. Style changes reproject the overview;
loading a new UoD resets it. `tests/test_overview_e2e.py` (Playwright: enter overview → badges
render → tap a placeholder → that cut is drawn open → Collapse-all restores → back to Drawing
restores the §3.3 SVG; zero console errors). All 33 overview + lens tests green together (no
regression to the existing Well/Storyboard lenses). **Found while building:** expanding an *outer*
subsumption cut reveals its *inner* cut as a new placeholder (net placeholder count can hold
steady) — the correct invariant is "the *tapped* cut is no longer collapsed," not "the total
drops." Spike screenshots/manual: server-verified 86-cut SUMO → 43 placeholders in ~1 s, each
expand ~0.6 s.

**✅ DONE 2026-06-15 — overview server path (build-order step 2).** The server can now serve
an overview. `layout_service.generate_overview_layout(egi, expand, budget)` =
`_resolve_collapsed` (the expanded-set → frontier-placeholder resolver: explicit `expand` opens
a cut + its ancestors; absent ⇒ the auto-expand policy opens cuts BFS-from-the-sheet to a
`DEFAULT_OVERVIEW_BUDGET=40` drawn-cut budget) → `collapse_quotient` → `generate_layout(quotient)`
→ `attest_overview` backstop. A small graph (≤ budget cuts) opens fully — an overview of it is
the ordinary drawing. The `GET /organon/uods/{id}?lod=overview&expand=<cutId>,…` branch returns
the SVG + layout DTO + a `collapsed` badge map (placeholder cut id → counts/polarity/boundary
degree; *form*, never actuality) for the client's badges and drill affordances; `lod=full`
(default) is unchanged. `tests/test_overview_routes.py` (8: small-graph-opens-fully,
budget/expand collapse + re-attest, faithful badge, auto-policy budget, ancestor-inclusion;
route returns collapsed map / full has none). Regression: organon routes 15, overview
attestation 22, correspondence-invariant fast subset 326 (the heavy `domain_model` ontology UoDs
deselected — the pre-existing layout-perf frontier, untouched by these additive changes).

**✅ DONE 2026-06-15 — overview attestation core (design doc + the navigation-projection
contract, build-order step 1).** `docs/ADAPTIVE_SCOPE_VIEWER.md` written FIRST (the conceptual
piece — the membrane / *no-mark-bears-actuality* guardrail governs what a placeholder may bear:
*form* counts/polarity/boundary-degree, never actuality). Then `src/overview_projection.py`
(`collapse_quotient` builds a real smaller EGI with each frontier cut a leaf placeholder; the one
boundary case — a predicate *hidden inside* a collapsed cut wired to a vertex *visible outside*
it, since a vertex sits at the **outermost** area its line reaches — is carried by an **anonymous
synthetic boundary predicate** inside the placeholder, which makes ordinary §3.3 attest the
boundary line's crossing+endpoint *for free*; + `boundary_incidences`/`boundary_degree`,
`frontier_placeholders`, `overview_summary`, `synthetic_boundary_id`). `attest_overview` /
`check_overview` / `OverviewViolation` added to `src/correspondence_attestation.py`: **P1** = full
§3.3 on the quotient (subsumes boundary integrity / "P3"), **P2** = faithful badge (counts +
polarity + boundary degree exact); the expansion law — empty collapse ≡ `attest_correspondence`,
full expansion = the real §3.3 picture. Overview is **outside the three regimes** (a *viewing*
op like pan/zoom; deliberately drops §3.3 totality; never a promotion source — the canonical
full-expansion drawable stays §3.3-governed). `tests/test_overview_attestation.py` (22:
expansion-law base case, boundary/closed/wide/nested collapses, frontier-vs-hidden, P1
adversarial, boundary-integrity-via-P1, P2 lying-badge, monotonicity, quotient validity). 95
passed on the touched modules; purely additive (no edit to existing `check_correspondence`).

**▶ Then the lighter deferred items (after overview+expand — author's stated order):**
time-stack *production* lens (tune the rough framing the spike flagged); **liveness/desuetude**
tracking (manifest floor #7 — which UoDs/models are still consulted; forward-facing provenance, an
Organon facet/badge); the **derivation-DAG** lens (branch structure; needs a branching episode to
exercise); the broader **cross-mode UX consistency** pass (shared `design-system.css`, camera
unification across the three modes, step/move terminology — the round-1 cross-mode findings).

**▶ DONE this session (2026-06-14) — the visualization/UX pivot, all committed + pushed, bedrock untouched:**
- **Adaptive-scope viewer.** `src/eg_structure.py` + `GET /organon/uods/{id}/structure` &
  `/history-structure` (coordinate-free, O(n) — 86-cut SUMO structure in ~8 ms where ELK takes
  seconds; `tests/test_eg_structure.py`). A decide-by-prototype **spike** → findings/decision in
  `docs/ADAPTIVE_SCOPE_SPIKE.md`. Then production Organon **lenses** behind a Lens selector:
  **Well** (`web_viewer/js/negation-well-lens.js` — the 2.5-D negation well; three.js; top-down =
  the circle-packing so parent–child stays unambiguous, tilt = earned depth; white/gray polarity,
  hue/texture + line-style reserved for Gamma) and **Storyboard** (`web_viewer/js/storyboard-lens.js`
  — the diachronic line of thought as a styled strip), over `web_viewer/js/lens-common.js`. Wired
  in `web_viewer/organon.html`; E2E `tests/test_organon_lenses_e2e.py`. Spike prototypes retired.
- **FOLIO increment 3** — `src/folio_native.py` (the "Both" arc complete; `docs/FOLIO_EVALUATION.md`).
- **`docs/MANIFEST_AND_MEANING.md`** — the philosophical floor the lenses obey (membrane/separation;
  *no mark bears actuality*; two-deaths/liveness; Peirce's cable).

**▶ Other open tracks (deferred behind the viewer work):** the **FOLIO/DLCore coverage lever**
(disjunctive / case-split for the non-Horn negative half); the **schema-drawing / §3.3** math
frontier ([[project_math_fixtures_zfc_peirce_schema]]); the deferred **LLM front-end** of the
NL→logic arc (both backends now in place — [[project_nl_to_logic_arisbe_as_interpretant]]).
*The math track and FOLIO "Both" arc are COMPLETE — see the ✅ blocks below.*

*Last session (2026-06-13) recap:* recovered from an OOM mid-build and shipped a lot — the
**automated Grapheus** (all 4 increments incl. the warrant), the **DL-ReasonSuite DLCore**
integration (soundness 100% / coverage 67% on 3620 tasks; found+fixed the materialize edge-id
collision), the **persona/practice docs merge**, and **FOLIO increments 1+2** (Z3 entailment
91.2% val; FOL→EG pictures 99.3% built / 85.5% round-trip). Also: dev-env fixes (httpx + z3 in
the dev extra; `uv sync --extra dev --extra web` is the correct setup). All on `main`.

*(Older context, still valid below.)* **This session [earlier]: completed the P2 import-breadth
queue** — the OWL construct fragment + an RDF front-end (`tools/rdf_to_owl.py`). Real ontologies
now import from where they actually live.

**✅ DONE — the automated Grapheus (the dialogical contest), all four increments built and
green (2026-06-12/13).** Design-of-record `docs/AUTOMATED_GRAPHEUS.md`; ✅ blocks below cover
increments 1+2+3 (driver + routes + board) and increment 4 (the warrant). Memory:
[[project_automated_grapheus_design]], [[project_agon_arena_v1_design]],
[[project_domain_oracle_and_m]], [[project_chain_of_semiosis_grounding]]. The import↔Agon arc
is now closed for a single G: a Graphist-won contest can be asserted into the corpus as
"withstood Agon" ([[project_import_low_warrant_and_floor]]).

**▶ CURRENT TRACK — NL→logic as *interpretation*, Arisbe as the interpretant/verifier (not
the parser).** See [[project_nl_to_logic_arisbe_as_interpretant]] for the framing (the
bidirectional "G1,G2,G3 in M?" / "G in M1,M2,M3?" reading; the LLM-proposes/Agon-disposes
arc; the vocabulary-miss vs fact-miss distinction). Agreed order: **(1) DL-ReasonSuite DLCore →
(2) FOLIO via its FOL side → NOT (3) the LLM front-end yet** (the "understandable but
unmappable" caveat needs the backend + a vocabulary-miss notion first).

**▶ Docs (2026-06-13): `ARISBE_PERSONAS.md` + the scenario narrative MERGED into
`docs/ARISBE_IN_PRACTICE.md`** (one on-ramp; now/frontier refreshed — Grapheus/warrant/DL
shipped; math horizon stays frontier). [[project_persona_capabilities_narrative]].

**▶ Step 2 (FOLIO) — engine decision = BOTH; increment 1 (Z3 verdict) DONE.** FOLIO cloned at
/Users/mjh/Sync/GitHub/FOLIO (data/v0.0/folio-{train,validation}.jsonl; label True=entailed /
False=contradicted / Uncertain=neither). z3-solver added (dev extra).
- **Increment 1 — the authoritative Z3 verdict (DONE, ✅):** `src/folio_fol.py` (own FOL
  parser ∀∃¬∧∨→↔⊕ + constants → AST → **direct** Z3 compile, NOT via the lossy EG→FOPL
  string) + `tools/folio_benchmark.py` + `tests/test_folio_fol.py` (11). **Validation (204):
  accuracy 91.2%, parse coverage 96.1%, recall T/F/U = 88/90/96%; of 10 disagreements, 9 are
  X→Uncertain (conservative) and ZERO True↔False flips.** Parser reads 99% of corpus FOL; the
  rest (comma-as-conjunction, decimal constants, unbalanced parens) abstain as Unparsed.
- **Increment 2 — the pictures + fidelity (DONE, ✅):** `folio_fol.ast_to_clif` + `folio_fol_to_egi`
  (CLIF emitter; ⊕→¬(a↔b)) → `clif_parser_dau` → EGI; `tools/folio_benchmark.py --fidelity`.
  **Validation (1288 formulas): built 99.3% (0 build failures), round-trip exact 85.5%** — exact
  for EG-native ∧¬→∀∃; ∨/↔/⊕ build but expand to De Morgan cuts that re-emit equivalently, not
  identically (a real correspondence boundary, reported).
- **Increment 3 — the native-coverage half (DONE, ✅):** `src/folio_native.py` decides FOLIO
  on Arisbe's *own* bounded engine (Horn materializer + freeze-witness `theory_query` +
  denial-based `check_consistency`), abstaining where the fragment can't decide.
  **Validation (204): SOUNDNESS 100.0% (47/47 decided correct), COVERAGE 23.0%** — confusion
  clean (gold-True→27T/0F, gold-False→20F/0T, gold-Uncertain→all abstain); never predicts
  Uncertain. `tools/folio_benchmark.py --native`; `tests/test_folio_native.py` (16). Write-up:
  `docs/FOLIO_EVALUATION.md`. See the ✅ block below.

**▶ MATH TRACK (do not drop — author flagged 2026-06-13):** finish the mathematics horizon —
validate the draft EGIF fixtures (docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md) against the parser,
then the **definition layer** (named graphs) + the **graph-with-holes schema node**
(Separation/Replacement/induction), then **∀x** via the Dau-native scaffold (homework done:
isolated-vertex insertion = equivalence in any context). [[project_math_fixtures_zfc_peirce_schema]],
[[project_universal_generalization_dau_homework]], [[project_definition_node_vs_phi_hole]].
Companion to FOLIO — interleave per author preference.

**▶ Earlier resume note (step 1 lever, optional):**
- **Step 1 (DL-ReasonSuite DLCore) — DONE: full 3620-task run, real map below.** Dataset:
  github.com/okanss/DL-ReasonSuite (stable checkout at /home/mjh/Sync/GitHub/DL-ReasonSuite;
  earlier run used a /tmp clone). `tools/dl_reasonsuite.py --suite-dir <checkout>/dl-reason-suite --full`.
  **Full run: soundness 100% (0 wrong / 3620), coverage 67%** — and every gap is principled:
  - subsumption 1200/1200 (100% cover) — freeze-a-witness decides every entailed subsumption;
  - instance **exactly 50%** — decides every *entailed* instance (YES, sound), **abstains on every
    *not_entailed*** (UNKNOWN): open-world incompleteness made honest (NO only when wholly Horn;
    these ontologies carry existential restrictions). Verified: entailed→yes 80/80, not_entailed→
    unknown 80/80;
  - consistency — detects every inconsistency (dl 10/10, fired denial), certifies consistency only
    within the fragment (el 6/10).
  **The coverage lever** (next, optional): a refutation / model-construction capability (or an
  explicit closed-world / NAF mode) for the *negative* half — instance non-entailment and
  consistency certification. Real extension, not a bugfix. Also: write up the soundness×coverage
  result (the honest "bounded sound reasoner vs full-DL benchmark — abstains, never errs" story).
- **Step 2 (FOLIO):** a FOLIO-FOL → CLIF importer, then score import fidelity (`same_graph`
  round-trip) + entailment, rendering the proofs as pictures.

**Other open tracks (deferred while the NL→logic track runs):** layout follow-ups; the math
menu ([[project_universal_generalization_dau_homework]] / [[project_definition_node_vs_phi_hole]]);
Agon depth (doc §10 — Beta sub-game ordering, the false-band warrant, two-Grapheus dialogue);
the by-hand reading desk ([[project_by_hand_import_reading_desk]]); math fixtures
([[project_math_fixtures_zfc_peirce_schema]]).

*What the design settled (so the build doesn't re-litigate):*
- **The contest is the semantic game** (`src/semantic_game.py`), **not** the Dau transformation
  game (`src/endoporeutic_game.py`, which stays the proof apparatus). Pietarinen maps EGs
  directly onto the outside-in semantic game; that *is* "the walk through levels of negation."
- **The auto-Grapheus = minimax over the existing evaluator.** `semantic_game._holds` already
  computes every subgame's Kleene value; the Grapheus plays a child that wins for it (the
  peel's `counterexample`/`winning_witness` *are* the selectives). No new search — **lift the
  evaluator into an interactive extensive-form driver**.
- **Roles by polarity, total at every history; swap once per cut** (janus-faced cut, Peirce CP
  3.480/4.458/4.556). Human = **Graphist** (proposes G, Verifier); machine = **Grapheus**
  (Nature/Falsifier + M-adjudicator) — not "auto-Skeptic vs auto-Proposer" but "the machine
  plays the model side, local role assigned by polarity." A *turn* runs to the next contested
  frontier; the per-cut swap is internal bookkeeping.
- **The record is the extensive-form `Play`** (selectives + choices + payoff) — a game record,
  **not** a Dau `TransformationChain`. "Withstood challenge" = a Graphist win against the
  model-warranted Grapheus; a corpus-boundary `ChainStep` is minted only on assertion,
  referencing the `Play` (the import↔Agon warrant link, [[project_import_low_warrant_and_floor]]).
- **Open-world UNKNOWN** is our deliberate overlay on Pietarinen's 2-valued closed game: a
  Grapheus frontier M can't settle → Grapheus declines → Agonothetes records **independent**
  (the hand-off to `/agon/where-it-holds`).

*Build order (`docs/AUTOMATED_GRAPHEUS.md` §9):* (1) **`src/grapheus.py`** headless driver +
tests (self-play reproduces `evaluate()`'s verdict corpus-wide) — the whole logical core; (2)
routes (start/apply/get/concede, reuse `_interpret_payload` model resolution + `materialize`);
(3) frontend + Playwright; (4) the warrant `ChainStep`. First opponent: **`skos_core`** (its
materialised broaderTransitive closure gives the Grapheus non-trivial selectives).

*Alternatives if priorities shift:* the two **layout follow-ups** (reader robustness on dense
ELK / tension compaction — both in Backlog); or the **math menu** (∀x scaffold tactic /
selection-driven fold). (The "land a cited Turtle/RDF ontology" consolidation is now **DONE** —
`skos_core` landed 2026-06-12, ✅ block below.)

---

## ✅ DONE 2026-06-13b — FOLIO increment 3: the native bounded engine (soundness × coverage)

The "Both" FOLIO arc's third leg — decide FOLIO with Arisbe's *own* reasoner beside Z3, the
DL-style honest-bounded story over natural-language-grounded full first-order logic.

- **`src/folio_native.py`** — `decide_native(premises, conclusion)`. Both directions reduce
  to one sound primitive: `M ⊨ C ⟺ M ∪ {¬C}` unsat (→ True), `M ⊨ ¬C ⟺ M ∪ {C}` unsat
  (→ False), with unsat detected soundly-but-incompletely by `dl_reasoning.check_consistency`
  (materialize the Horn fragment → a **denial** firing in the least Herbrand model = a genuine
  inconsistency, since it uses only a subset of the axioms). Universal/subsumption conclusions
  (no denial to fire) are recovered by freeze-a-witness `theory_query.entails`. **Never predicts
  Uncertain** — soundly certifying "neither" needs a completeness the fragment lacks, so it
  abstains (`Unknown`). Same shape as DLCore instance-checking.
- **Three soundness traps the build surfaced**, all handled by compiling the AST **directly**
  to an EGI (`_build`, not via CLIF/EGIF text): (1) `clif_parser_dau` has no Dau **constant** —
  it reads every term as a generic line; the builder makes a FOLIO constant a shared
  `is_generic=False` sheet vertex (matches only itself). (2) `parse_clif` **collapses** every
  premise's `∀x` into one line of identity under `(and …)`; direct building gives each
  quantifier its own vertex (no alpha-rename needed). (3) **existential-under-negation** —
  `check_consistency` reads a sheet cut `~[A…]` as a *universal* denial, which over-fires for
  `∃x (P(x) ∧ ¬Q(x))`; a polarity-aware guard (`_denial_reading_unsound`) abstains the
  refutation direction whenever a negated atom carries an existentially-bound variable
  (disjointness `∀x¬(A∧B)` stays decidable). A meaning-preserving `normalize` turns
  `A→¬B ≡ ¬(A∧B)` (+ exportation + conjunctive-head split) so disjointness builds as flat
  denials.
- **Validation (204): SOUNDNESS 100.0% (47/47), COVERAGE 23.0% (47/204 decided).** Confusion
  clean: gold-True→27 True/0 False, gold-False→20 False/0 True, gold-Uncertain→0 decided. 157
  principled abstentions (non-Horn premises: ∨, ⊕, ∃-under-¬; every Uncertain gold). Zero
  unsound verdicts. (Train split ships no `conclusion-FOL`, so validation is the entailment-
  scorable split — as in increment 1.)
- **Harness:** `tools/folio_benchmark.py --native` (soundness×coverage printer). **Tests:**
  `tests/test_folio_native.py` (16) — the two provers, the guard, honest abstention, normalize,
  and a soundness invariant over a FOLIO-shaped sample. No regressions across
  folio/dl/theory-query/materialization (77). **Write-up:** `docs/FOLIO_EVALUATION.md` (all
  three increments). **Coverage lever (deferred, the real extension):** a disjunctive /
  model-construction (case-split) capability for the non-Horn negative half — the same frontier
  DLCore defers to.

---

## ✅ DONE 2026-06-13 — DLCore reasoning services + benchmark harness (NL→logic step 1, core)

The reasoning core of step 1 (DL-ReasonSuite's DLCore track), composed from what's built —
no new reasoning power, just the DLCore task shape + a consistency check + fragment/signature
honesty.

- **`src/dl_reasoning.py`** — three services over a theory M (a `RelationalGraphWithCuts`):
  `check_subsumption(M, C, D)` (wraps `theory_query.entails` over `~[ (C *x) ~[ (D x) ] ]`),
  `check_instance(M, a, C)` (materialize the Horn fragment → read the least Herbrand model),
  `check_consistency(M)` (materialize, then test each **denial** `~[ A… ]` against the closure
  — a denial satisfied in the least model is violated in every model → sound INCONSISTENT).
  Verdicts are three-valued + two refusals: `YES`/`NO`/`UNKNOWN` (open-world / non-Horn
  residue), `UNSUPPORTED` (construct outside the fragment), `OUT_OF_SIGNATURE` (query names
  vocabulary M never defined — the vocabulary-miss vs fact-miss distinction). A consistency
  `YES` is given only within the fragment; an inconsistency is reliable whenever found.
- **`tools/dl_benchmark.py`** — runs a task suite (subsumption/instance/consistency, gold
  2-valued) and scores it the way a *bounded* reasoner deserves: **soundness** (1 − wrong/decided,
  must be 1.0) + **coverage** (decided/total), abstentions reported not penalised. Dataset-
  independent task schema (`ontology_egif` or `ontology_ref`); the DL-ReasonSuite OWL-DL→schema
  adapter is the remaining thin layer. `--self-test` demo: 6 tasks, soundness 100%, coverage 83%.
- **Tests:** `test_dl_reasoning.py` (12) + `test_dl_benchmark.py` (4) — the verdict mapping,
  the consistency check (clean / direct violation / through-the-closure / unsupported-residue),
  signature refusal, and the harness's soundness/coverage + loud wrong-detection.

---

## ✅ DONE 2026-06-13 — automated Grapheus increment 4 (the warrant: "withstood Agon")

The corpus-boundary warrant that closes the import↔Agon arc — a Graphist-won (or independent)
contest can be asserted into the corpus, carrying its `Play` as proof. The semantic-game record
is a `Play` (selectives + path), not a transformation-game episode, so this is a **`Play`-aware
warrant**, not a reuse of `_episode_to_chain` (per design §7).

- **`agonothetes.apply_contest_disposition` + `_play_to_warrant_chain`** (over a
  `GrapheusSession`). The asserted graph is **G itself** (the proposal that withstood Agon); the
  single warrant `ChainStep` does not *transform* G (from==to EGI) — it **attests** that G crossed
  the regime boundary by withstanding the contest (CHAIN_OF_SEMIOSIS's "fullest form" of regime-2
  = withstood challenge, distinct from §3.3 = correspondence). The step's `parameters` carry the
  whole `Play` as provenance (verdict, outcome, the selectives M supplied, the outside-in
  transcript). Persisted via `save_uod_with_chain` (EPG_SESSION UoD; tags incl.
  `warrant:withstood_agon`) — so §3.3 still fires on G at the boundary, before any disk write.
- **The guard**: a **Grapheus win blocks assertion** (a lost inning cannot assert G; the
  false-band's own assertions — assert ¬G, revise M — are out of V1 scope and *reported*, not
  faked). A Graphist win or an **independent** inning may assert; non-asserting dispositions
  record the judgment on the session only. Nothing auto-asserts.
- **Route** `POST /agon/contests/{id}/disposition` (reuses `AgonDispositionRequest`); **frontend**
  — the contest board's disposition taxonomy is now interactive (select → asserting fields →
  "Record disposition"; lost-inning asserts shown blocked). **Tests**: +5 route (won→warrant
  chain round-trips with `Play` provenance; lost→blocked; independent→new_fact; non-asserting;
  target-id required) + 1 Playwright (record a non-asserting disposition). 42 grapheus +
  41 chain/EPG/organon regression green.

**The automated-Grapheus build is COMPLETE (increments 1–4).**

---

## ✅ DONE 2026-06-12 — automated Grapheus increments 1 + 2 + 3 (driver + routes + board)

The semantic-game contest, built as the design's first two increments and verified green
(37 grapheus tests + 55 agon/semantic regression, all passing).

**Increment 1 — the headless driver** (`src/grapheus.py`, `tests/test_grapheus.py`).
`GrapheusContest` lifts `semantic_game`'s one-shot peel into an interactive extensive-form
**`Play`**: a single descending cursor, polarity-owned decisions (defender maximises,
challenger minimises the *local* Kleene value — `_or3`==max, `_and3`==min, uniform across the
per-cut swap), `start`/`choose`/`autoplay`/`concede`. Self-play reproduces `evaluate()`'s
verdict across the truth table (both worlds) + the real `skos_core` model + a tomos slice.
**Two bugs found and fixed while wiring the routes** (the earlier "exit 0" runs were *masked
timeouts* — `| tail` / trailing `echo` ate pytest's real exit code; the driver had been
hanging, never actually passing): (a) **infinite loop** — pursuing an atom conjunct recorded
the terminal but didn't advance the cursor, so `_decision_here` re-offered the same conjuncts
forever; fixed with a `_terminal_atom` guard. (b) **open-world horizon divergence** — the
single concrete play walks only *known* individuals (Kleene max), but `_holds` bumps an
unsatisfied existential to UNKNOWN in an open world (the unknown-individual horizon, lines
226–229); on an open-world universal (`logician-open`) the contest read TRUE where `evaluate`
reads UNKNOWN. Fixed by mirroring the bump: at a witness frontier where M's value is UNKNOWN
but no known individual beats FALSE, the defender **declines** → independent (doc §6).
Closed-world cases are untouched (no bump → no decline).

**Increment 2 — the routes** (`src/web_api/routes/agon.py` + `services/grapheus_session_manager.py`
+ `AgonContestStartRequest`/`AgonContestChooseRequest`; `tests/test_grapheus_routes.py`, 10
tests). `POST /agon/contests` (start, with `autoplay`), `GET /agon/contests/{id}`,
`/choose`, `/concede`, `DELETE`. Reuses `_resolve_model_egif` + a factored `_materialization_dict`
(shared with `_interpret_payload`) so M resolves from raw EGIF or a corpus UoD, optionally
materialized. Route conformance: the five persona innings autoplay to `/interpret`'s verdict;
`skos_core` (materialized) — the Grapheus must concede the derived broaderTransitive fact
(Graphist wins) and declines Dog⊳Cat (independent); the interactive Graphist witnesses a line
and wins. Ephemeral sessions (4-h TTL), no corpus touch.

**Increment 3 — the interactive board** (`web_viewer/agon.html` + `tests/test_grapheus_e2e.py`,
2 Playwright tests). A "⚔ Contest the Grapheus (move-by-move)" action opens `/agon/contests`;
`renderContest` shows the contested Graphist frontier as clickable option buttons (witness an
individual / pursue a conjunct), the play transcript outside-in, the fixed lines of identity,
and on termination the verdict + the verdict-annotated disposition taxonomy (read-only — the
warrant step is increment 4). The machine Grapheus auto-advances server-side. E2E: the human
witnesses x:=Rex and wins (selective recorded, disposition shown); concession hands the inning
to the Grapheus.

**Next: increment 4 (the `Play`-aware warrant `ChainStep`).**

---

## ✅ DONE 2026-06-12 — `skos_core` landed (the RDF/Turtle front-end into the corpus)

Landed the first corpus ontology imported from **RDF (Turtle)** — `skos_core`, the
semantic-relation core of **W3C SKOS** (Miles & Bechhofer 2009) — to give the Grapheus a
*populated, rule-bearing* domain (the corpus was heavy on pure T-boxes: SUMO, BFO; and
relational algebras: COLORE).

- **The drawn fragment** (`corpus/ontologies/skos_core.ttl`, faithfully transcribed from the
  official vocabulary): the SKOS classes (Concept / ConceptScheme / Collection, pairwise
  disjoint) + the three **reasoning-critical** property axioms — `broader ⊑ broaderTransitive`,
  `broaderTransitive` transitive, the symmetric `related` (all ⊑ `semanticRelation`) — over a
  small **illustrative animal thesaurus** (Animal ⊐ Mammal ⊐ Carnivore ⊐ {Dog, Cat, Wolf};
  authored here, honestly noted as *not* part of SKOS). 13 cuts, **3.5 s** at the §3.3 save
  boundary; materialization fires (`broader ⊑ broaderTransitive` + transitivity close the
  chain → `(broaderTransitive "Dog" "Animal")`; symmetry → `(related "Wolf" "Dog")`). The
  semantic peel decides it end to end: Dog⊳Animal TRUE, Wolf~Dog TRUE, Dog⊳Cat UNKNOWN
  (sound open-world). A live semantic-game / Grapheus target.
- **The layout-perf frontier, respected.** The **full** official W3C vocabulary is vendored
  verbatim beside it (`corpus/ontologies/skos.rdf`) as the source of record — 62 EG axioms
  incl. every inverse / domain / range pair → **124 relational-scroll cuts**, ~134 s to draw
  (super-linear, like `bfo_core`'s full axiomatisation). It imports fine *as data*; only the
  contested fragment is drawn ("M is data, draw only the contested fragment").
- **Wiring:** `tools/build_ontologies.py` `skos_core()` (cited W3C source; in `build_all()`);
  auto-appears in the `/agon` model picker (corpus UoDs are listed there). Corpus = 27 UoDs
  (7 ontologies). Conformance `CITED` + `ONTOLOGIES` sets updated.
- **Tests:** `tests/test_rdf_import.py` (+2: broaderTransitive/symmetric closure; drawable
  fragment < 20 cuts). Regressions green — RDF/OWL import, corpus-conformance, agon-
  interpretation, materialization, theory-query (188); eg_reader / attestation / organon.

---

## ✅ DONE 2026-06-12 — P2: completed the import-breadth queue (OWL constructs + RDF)

The remaining P2 queue closed in two moves.

**(1) The OWL construct fragment is complete** (`tools/owl_to_clif.py`). Beyond the prior
union + ∀R.D-head work:
- **`ObjectHasValue(R, a)`** → `(R x a)` (a binary atom with the individual fixed) and
  **`ObjectMinCardinality 0/1`** (0 ≡ `owl:Thing`; `1 R [C]` ≡ `ObjectSomeValuesFrom`, an
  existential) added to `_class_expr` — both add no cut around the bound variable, so they're
  sound in **either** polarity.
- **`ObjectComplementOf(D)`** in superclass position → `(if 〚C〛 (not 〚D〛))` via `_head_clauses`
  (head-only, like ∀R.D — the `not`-cut would misplace the variable in negative position,
  verified). Non-Horn → contest.
- Reported (honest floor): `ObjectMinCardinality n≥2`, `ObjectMaxCardinality`,
  `ObjectExactCardinality`, `ObjectHasSelf`, `ObjectOneOf`, and ∀R.D / ¬D in negative position.
- 41 OWL tests (was 32).

**(2) RDF front-end** (`tools/rdf_to_owl.py`) — the real-world surface syntaxes. Decision
(with the author): add **rdflib** (BSD-3, pure-Python) rather than hand-roll a Turtle/XML
parser — most functionality for least effort, no commercial encumbrance. rdflib parses any
RDF serialization (**Turtle, RDF/XML, N-Triples, JSON-LD**); `rdf_to_forms(graph)`
reconstructs the *same* functional-syntax `Node` AST the OWL translator consumes, so every
axiom + class-expression rule is reused. The hard parts rdflib makes tractable: blank-node
`owl:Restriction` decoding (some/all/hasValue/≥1-card), `owl:intersectionOf`/`unionOf`/
`complementOf` (RDF-list members via `rdflib.collection.Collection`), and **structural A-box
detection** (an object-property assertion `a P b` is recognised by a non-builtin predicate
with URIRef ends — so it's recovered even when the property isn't explicitly typed
`owl:ObjectProperty`, the common lightweight-Turtle case). Unsupported class shapes
(datatypes, oneOf, hasSelf, max/exact card) become a sentinel the translator *reports* — no
silent drop. `translate(text)` was split into a thin parser wrapper + the shared
`translate_axiom_forms(forms)` core both front-ends call. Wired
`from_rdf_text/from_rdf_file` (extension-guessed format) into `domain_model_importer` (+ the
`DomainModelImporter` methods). A Turtle-imported ontology reasons end to end: subsumption
theorems decide, the ∀R.D-Horn rule fires on the asserted A-box, the subclass chain
materializes (`Dog(Fido)` → `Animal(Fido)`). Tests: `tests/test_rdf_import.py` (16) +
`tests/fixtures/zoo.ttl`. **Manchester** (`.omn`) deferred — rdflib doesn't parse it, there's
no maintained Python Manchester parser, and it's an editing syntax rather than a common
distribution format (low import value).

No regressions: 238 import/ontology/agon/materialization/theory-query/corpus-conformance/
organon tests green. `rdflib>=7.6.0` added to `pyproject.toml` (main deps — import is a user
feature). Docs: both translator module docstrings.

---

## ✅ DONE 2026-06-12 — P2: OWL `ObjectUnionOf` + `ObjectAllValuesFrom` heads

Two more OWL 2 class-expression forms cross from *reported-as-skipped* into the translated
fragment, widening what imports as a domain model M (all in `tools/owl_to_clif.py`, unprotected):

- **`ObjectUnionOf` (disjunction), any position.** Added to `_class_expr` as
  `(or 〚C〛 〚D〛)`, which `parse_clif` renders as the De-Morgan double cut
  `~[ ~[A] ~[B] ]`. Verified sound in **both** polarities (the bound line settles universal
  in a body, existential on the sheet — the cut nesting carries it). `C ⊔ Thing` ↦ Thing,
  empty disjuncts dropped. A disjunctive *head* is non-Horn (materialization skips it) but is
  sound EG the contest peel uses. Flows through the existing `SubClassOf`/`EquivalentClasses`/
  `DisjointClasses` paths (previously these axioms were skipped).
- **`ObjectAllValuesFrom` (universal restriction), superclass position only.** A new
  `_head_clauses` compiler **prenexes** a head ∀-restriction into a flat OWL-2-RL Horn rule:
  `SubClassOf(C, ∀R.D)` → `(forall (x y) (if (and (C x) (R x y)) (D y)))`. Crucially this is
  the *flat* scroll `~[ (C x)(R x y) ~[ (D y) ] ]` the materializer recognises (the
  compositional *nested* encoding reads as "negation in head" and would fall only to the
  contest) — so the rule genuinely **fires** (materializes `Dog(Fido)` from `Dog(Rex)` +
  `hasParent(Rex,Fido)`) and **decides theorems** (`theory_query.entails`: a Dog's parent is a
  Mammal, chained through subsumption). A mixed intersection head splits into several rules
  (`C ⊑ Agent ⊓ ∀R.Person` → `C⊑Agent` **and** `C⊓R(x,y)⊑Person(y)`), itself a sound,
  layout-friendly decomposition. ∀R.D nests (composes through intersection + nested ∀).
- **`∀R.D` in negative position stays reported, not translated.** In subclass / equivalent /
  disjoint position, `parse_clif` places a vertex at its *first-reference* area (not its LCA),
  so a universal-in-the-antecedent silently flips to existential (verified empirically) — the
  honest floor reports it rather than mistranslate.
- **Strictly additive.** The existing-superclass compiler is tried first and unchanged; the
  head-clause path engages **only** when it returns `None` (i.e. a ∀-restriction is present).
  Every prior translation is byte-for-byte identical, so the landed ontology UoDs re-import
  unchanged. Tests: `tests/test_owl_import.py` 23 → **32** (union both polarities + equivalence;
  ∀-head prenex + intersection split + materialize-fires + theory-query-decides + negative-
  position skip). No regressions: 166 import/ontology/agon/materialization/theory-query +
  102 corpus-conformance/ontology/organon green. Doc: the translator module docstring.

---

## ✅ DONE 2026-06-12 — P2: `cl-imports` auto-resolution + `colore_field` landed

The closure resolver (`src/cl_import_resolver.py`) auto-resolves a Common-Logic module's
`cl-imports` chain (pluggable Mapping/Directory/ColoreWeb/Caching/Chain resolvers; BFS
dedupe; unresolved reported, never dropped), wired into `from_clif_text/from_clif_file`.
Landed **`colore_field`** — the COLORE real-number field algebra (4-module auto-resolved
closure `field → commutative_ring → ring → semiring`, nested function terms relationalised),
a drawn §3.3-attested corpus UoD (28 cuts). The fuller density closure (7 modules, 130 cuts)
is **vendored** (`corpus/ontologies/colore_cache/`) + imports as data, but stays undrawn at
the layout-perf frontier (like `bfo_core`). Earlier the same day: function-term
relationalization + a CLIF universal-quantifier correctness fix (parser + generator),
**P0** (the 7 pre-existing red layout tests triaged + resolved via a documented
`_reader_frontier` helper + one xfail — detail in the Backlog), and **P1** (Playwright E2E
over `/agon` interpretation + challenge mode — `tests/test_agon_e2e.py`,
`tests/test_ergasterion_challenge_e2e.py`, 9/9 green).

---

## ✅ DONE 2026-06-12 — P2: `cl-imports` auto-resolution + `colore_field` landed

Where `colore_between` had its import chain resolved **by hand**, a Common-Logic module's
`cl-imports` closure is now resolved **automatically**, and the first machine-resolved
ontology landed in the corpus.

- **`src/cl_import_resolver.py`** — the closure walk + pluggable resolution.
  `resolve_from_text` / `resolve_from_iri` do a BFS over the `(cl-imports …)` graph
  (dedupe by IRI — a diamond import contributes once; cycle-safe), conjuncting each
  module's **verbatim** text under `;; ===== <iri> =====` headers into one self-contained
  source that feeds the existing `from_clif_text` pipeline (the now-satisfied `cl-imports`
  directives stay as harmless parser no-ops). Unresolved IRIs are **reported** on the
  closure (`ResolvedClosure.unresolved` + a `UNRESOLVED:` line), never silently dropped.
  Resolvers: `MappingResolver` (pure dict — the offline test backend), `DirectoryResolver`
  (IRI path under a base dir), `ColoreWebResolver` (raw-GitHub fetch, certifi-verified SSL,
  opt-in), `CachingResolver` (remote → persists a local mirror), `ChainResolver`.
- **Wired** into `from_clif_text(…, resolver=…)` / `from_clif_file(…, resolver=…)` (result
  carries `resolved_modules` + `unresolved_imports`; no resolver ⇒ unchanged behaviour).
- **COLORE wrinkle fixed at the same boundary:** the ringoid files carry `(cl-comment '…')`
  whose **single-quoted** strings contain parens (`'Annihilation by zero (entailed for
  rings)'`); `_clif_tokenize` now reads `'…'` as one literal and `_strip_cl_comments` drops
  the (logically-empty) annotations before parsing — like `_strip_block_comments`.
- **`colore_field` landed** (`tools/build_ontologies.py`): the COLORE real-number field
  algebra `field → commutative_ring → ring → semiring` (4 modules auto-resolved),
  **heavily function-bearing** — the ring axioms use nested function terms
  `(= (sum (sum x y) z) (sum x (sum y z)))`, each relationalised on import — drawn and
  §3.3-attested at the save boundary (V59 E46 **Cut28**, ~2.6 s; the stronger eg_reader
  round-trip passes, no `_reader_frontier` deferral). Cited (COLORE / Grüninger, CC BY-SA
  4.0), in the `/agon` picker. Corpus = 26 (6 ontologies).
- **Density stays data.** The full `density → amount, spatial_volume → ringoids` closure
  (7 modules, **130 cuts**) is **vendored** in `corpus/ontologies/colore_cache/` (each file
  verbatim with its CC-BY-SA header; a README documents provenance) and imports fine, but
  is *not* stored as a drawn UoD — a 130-cut relational theory is super-linear to lay out at
  the §3.3 save boundary (the layout-perf frontier, as with `bfo_core`; *M is data, draw
  only the contested fragment*).
- **Tests:** `tests/test_cl_import_resolver.py` (22 — closure dedupe / cycle-safety /
  unresolved-reporting; Directory/Caching/Chain on a tmp dir; end-to-end through the
  importer; one **live-network** test that actually runs when COLORE is reachable). No
  regressions across import / ontology / agon / materialization / theory-query / corpus-
  conformance / eg_reader / organon (`colore_field` added to the conformance `CITED` set).
  Doc: `docs/CORPUS_AND_IMPORT_MODEL.md` §5.3.

---

## ✅ DONE 2026-06-12 — CLIF universal-quantifier correctness (parser + generator)

A follow-on to the relationalization work surfaced a **mutually-compensating pair of bugs**
between the protected `clif_parser_dau` and `clif_generator_dau`, now both fixed (authorized
core change; full suite green).

- **Parser — positive-body universals.** `(forall (x⃗) body)` only built the universal's
  negative context when `body` was a material conditional (`if`) — it dropped the binder and
  leaned on the conditional's scroll. A **positive** body (a bare atom, conjunction, or
  existential — and, it turned out, a biconditional) had nowhere to place the bound line, so
  the universal silently collapsed to an existential (a line on the sheet **is** ∃). The
  `forall`/`exists` handlers were in fact identical code. Fixed: keep the established shape
  when the body is `if`/`not` (the bound line settles in their cut — the canonical
  subsumption scroll is unchanged), and otherwise build the double cut `~[ *x⃗ ~[ body ] ]`
  explicitly (binders in the outer/negative cut → universal; the body's own existentials
  stay existential at even depth). `(forall (x) (P x))` now reads `~[ *x ~[ (P x) ] ]` = ∀x P,
  not `~[ *x (P x) ]` = ∃x P. `iff` moved to the wrap path (its two scrolls are siblings, so
  a shared line hoists to the sheet — positive — unlike `if`).
- **Generator — quantifier by polarity.** `generate_with_quantification` wrapped *every*
  free variable in one blanket `forall`, mislabelling every sheet-level existential; it only
  round-tripped because the old parser read `forall` back as `exists`. Fixed: classify each
  line by the polarity of its home area (`is_oddly_enclosed`) — a positive (even-depth)
  vertex is existential, a negative (odd-depth) one universal. An all-existential graph now
  emits honest `(exists …)`, an all-universal one honest `(forall …)`. (The cut structure
  already pins each universal line negatively, so the parser derives ∀ from structure, not
  the keyword — `exists` therefore round-trips every shape faithfully; a graph mixing both
  polarities can't be rendered prenex without loss and keeps the faithful-round-trip `exists`.)
- **Verified:** `tests/test_properties_cgif_clif_round_trip.py` (the 6 known-example
  round-trips + count-preservation + idempotency) now pass *and* the emitted CLIF is
  semantically honest (`(P *x)` → `(exists (x) (P x))`; `~[ (Cat *x) ~[ (Animal x) ] ]` →
  `(forall (x) (not (and (Cat x) (not (Animal x)))))`). Full suite green; 152 core tests pass.

---

## ✅ DONE 2026-06-12 — function terms relationalise on import

The function-bearing COLORE modules (the majority) now import. The protected CLIF parser
(`_parse_atomic_formula`) accepts only *names* in argument position, so a nested function
application `(f t₁ … tₙ)` there — e.g. `density.clif`'s `(density (dmv v m))` — was a parse
error. Functions are EG-expressible by **relationalisation** (a function = a relation whose
last argument is uniquely determined — its graph), so the importer does the
meaning-preserving reduction at its own boundary, leaving the protected lexer untouched
(like `_strip_block_comments` / `_disambiguate_variables`).

- **`_relationalize_functions` (`src/domain_model_importer.py`)** — a CLIF→CLIF pass over
  the existing s-expression reader (`_clif_tokenize` / `_clif_read_all` / `_clif_serialize`).
  Logical structure (connectives / quantifiers / `cl-text`/`cl-imports` wrappers) is
  recursed through untouched; at every predication — including `(= t₁ t₂)`, since the
  parser reads `=` as an ordinary relation — each function-term argument is lifted: mint a
  fresh `z`, replace the occurrence with `z`, conjoin the graph atom `(f …args… z)` under a
  fresh `exists`. `(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧ density(z))`. Nested `(f (g x))`
  lifts inside-out; the **value-as-equality** case `(= (dmv x y) (dmv z y))` relationalises
  both sides → `(= z₁ z₂)`. The ∃-form is sound in *any* polarity (the value exists in
  every context given totality), so a lifted atom inside a `not` stays correct.
- **Functionality is optional + non-Horn.** `from_clif_text(…, assert_functionality=True)`
  emits totality `∀x⃗∃z R_f` + uniqueness `∀x⃗∀z∀z′ (R_f(x⃗,z)∧R_f(x⃗,z′)→z=z′)`; default
  off (the minimal correct import needs only the graph atom; functionality uses `=` → falls
  to the contest residue like the rest of COLORE).
- **Verified** on the real COLORE `density.clif` (downloaded from `gruninger/colore`):
  `dmv`, `add_density`, `mult_density`, … all import as relations; the canonical axiom
  round-trips via `same_graph`. 8 new tests
  (`tests/test_domain_model_importer.py::TestFunctionRelationalization`); no regressions
  across the import / ontology / agon / materialization / theory-query suites (162 tests).
  Doc: `docs/CORPUS_AND_IMPORT_MODEL.md` §5.2.
- **Not committed:** a *fully cited* function-bearing COLORE corpus UoD (the
  `colore_between` treatment for `density`) — that needs `cl-imports` closure resolution
  (`density` → `amount` → `field`, the real-number field axioms), which is the separate
  import-breadth fork. `colore_between` stays the resolved-closure exemplar.

---

### For reference — the consolidate-&-make-visible sequence (steps 1–2 DONE 2026-06-12)

Three sessions built deep inference power (peel → materialization → theory query →
OWL/COLORE import). Steps 1–2 made it visible:
1. **Render the `theorem` verdict in `/agon`** — DONE (browser-verified).
2. **Land a real ontology** — DONE: `bfo_core` (BFO taxonomy, OWL→CLIF→EGI) +
   `colore_between` (real COLORE, CLIF→EGI). Both in the `/agon` picker.
3. **Playwright E2E** — the open companion debt (folded into the list above).

---

## ✅ DONE 2026-06-12 — COLORE validation + `colore_between` landed

Validated the pipeline against the **real COLORE repository**
(`github.com/gruninger/colore`) — which immediately surfaced and fixed two genuine bugs
that synthetic content had hidden, and landed the first corpus ontology from an external
CL repository.

- **`/* */` header bug (fixed).** Every COLORE file carries a `/* Copyright … University
  of Toronto **and** others … */` block; the protected CLIF lexer strips only `;;`, so
  "and"/"if"/"not" inside the header tokenised as keywords and broke the parse — *no real
  COLORE file could be read*. `from_clif_text` now strips `/* */` blocks (leaving `//` for
  `http://` IRIs).
- **Variable-collapse bug (fixed — a correctness bug).** Many `(forall (x) …)` sentences
  reusing `x` had every `x` unified by `parse_clif` into one line of identity, turning
  `(∀x A→B) ∧ (∀x C→D)` into the weaker `∃x (A→B)∧(C→D)` (+ a layout blowup). Fixed by
  **alpha-renaming** all quantified variables globally-unique before parse
  (`_disambiguate_variables`, in `from_clif_text` + `compose_models`) — the CLIF analogue
  of the OWL translator's per-axiom fresh variables.
- **`colore_between` landed.** The COLORE *betweenness* ontology (resolved `cl-imports`
  closure, verbatim CC-BY-SA content attributed) as a cited `kind=ontology` UoD, in the
  `/agon` picker. Corpus = 25.

Honest boundaries confirmed (not bugs): COLORE is mostly **non-Horn FOL** (materialization
skips it — betweenness forward-chains nothing, its value is the contest); **function terms**
`(dmv v m)` are not handled by *our CLIF parser* (parse error — an implementation gap, not a
limit of EG: functions relationalise — `(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧ density(z))`
+ functionality — and Dau gives a direct extension, ICCS 2007; the fix is to relationalise on
import); `cl-imports` still needs hand resolution; and COLORE uses **underscores** (which round-trip
in EGIF), so it doesn't exercise the hyphen fix — that stays pinned by the in-repo
hyphenated `animal_taxonomy`. (I was also wrong earlier that there was "no internet" —
`WebFetch`/`WebSearch` and Bash all reach the network.)

---

## ✅ DONE 2026-06-12 — consolidate & make visible (steps 1–2)

**Step 1 — the `theorem` verdict is visible in `/agon`.** `renderInterpretation`
(`web_viewer/agon.html`) now paints a **"Theorem of M? (deduction)"** block beside the
extensional peel: the deduction verdict + the freeze-witness `body ⊢ head` + which head
atoms derived. So when the peel reads *vacuously* over an empty A-box (a pure T-box), the
real answer is shown. Browser-verified (Playwright/Chromium).

**Step 2 — a real ontology landed in the corpus: `bfo_core`.** The Basic Formal Ontology
upper taxonomy (Arp, Smith & Spear 2015), authored as `corpus/ontologies/bfo_core.ofn`
and imported **OWL→CLIF→EGI** into a `kind=ontology` UoD (cited; `tools/build_ontologies.py`
`bfo()`). It's a pure T-box — the ideal companion to step 1: select it in the `/agon`
picker, propose `Object ⊑ Entity`, materialize → empty, **theorem block → TRUE** (freeze
`(Object __w1) ⊢ (Entity __w1)`), the disjointness as the honest non-Horn residue.
Browser-verified end to end.

The forcing function did its job — landing a real ontology surfaced two genuine gaps,
both fixed:
- **A translator bug:** `owl_to_clif` emitted the bound variable `x` for *every* axiom,
  and `parse_clif` unifies same-named variables across sentences → all 24 subsumption
  scrolls collapsed onto **one** line of identity threaded through 47 cuts (a correctness
  smell + a 176s layout). Fixed: **fresh per-axiom variables** (`x1`, `x2`, …) — 24
  distinct lines, layout 176s → 21s. Regression-tested.
- **Per-query attestation cost:** `/agon/interpret` against a corpus model called
  `load_uod`, which **attests §3.3 (a full layout, 21s for BFO)** at the load boundary —
  even though M is read purely as *data* (materialize/peel never draw it), and
  `where-it-holds` would attest *every* UoD. Fixed: `load_uod(..., attest=False)` for the
  M-as-data reads (the "M is data, draw only the contested fragment" principle,
  `DOMAIN_ORACLE_AND_M.md` §5). Picker→interpret **22.5s → 0.1s**. Default stays
  `attest=True` for every caller that draws.

A documented frontier remains: BFO's **relational** scrolls (transitive/inverse, multi-var
bodies) are super-linear to lay out, so the stored `bfo_core` is the *taxonomy* only
(subsumption + disjointness); the full `.ofn` (with RO relations + A-box) is the source of
record and imports fine as data — the layout-perf frontier, not a correctness gap.

---

## ✅ DONE 2026-06-12 — the OWL→CLIF→EGI import pipeline (front half)

The named pipeline's **back half already existed** (`clif_parser_dau.parse_clif` turns a
Common Logic sentence into exactly the EG shapes — subsumption scroll, conjunctive Horn
body, existential-head scroll, disjointness denial). The missing **front half** is now
built: `tools/owl_to_clif.py` reads **OWL 2 Functional-Style Syntax** and translates the
EG-expressible axioms to CLIF (class expressions: named classes, `ObjectIntersectionOf`,
`ObjectSomeValuesFrom`):

- **Forms:** `SubClassOf`, `EquivalentClasses`/`DisjointClasses` (pairwise),
  `SubObjectPropertyOf`, `ObjectPropertyDomain`/`Range`, `InverseObjectProperties`,
  `Symmetric`/`TransitiveObjectProperty`, `ClassAssertion`, `ObjectPropertyAssertion`,
  `SameIndividual`/`DifferentIndividuals`.
- **Honest floor** (the SUO-KIF discipline): cardinality, union, complement,
  `AllValuesFrom`, datatypes, functional/key, annotations → **reported by construct**;
  `⊑ owl:Thing` dropped as trivial; `Declaration` counted as vocabulary. IRIs/prefixed
  names reduce to sanitized local identifiers.
- **First-class:** `domain_model_importer.from_owl_text` / `from_owl_file` (warnings
  carry the skip-report); composes with the CLIF path; wraps as a `kind=ontology` UoD.
- **The loop closes:** an OWL-imported ontology is a real M whose subsumption /
  intersection / transitivity theorems `theory_query.entails` decides. Tests:
  `tests/test_owl_import.py` (23) + `tests/fixtures/zoo.ofn`. Doc:
  `docs/CORPUS_AND_IMPORT_MODEL.md` §5.1.

---

## ✅ DONE 2026-06-12 — ontology-as-M (step 1): the T-box theorem query

Cashed in materialization + the interpretation register on the **real corpus ontology
UoDs**, and closed the gap the exercise exposed.

**What exercising revealed.** Materializing the three ontologies:
- **Porphyry** (`(Man "Socrates")` + 5 subsumption rules) → derives Socrates is
  Animal/Living/Body/Substance (the full ladder); the persona promise is concretely
  true wherever M carries an A-box.
- **FOAF** (Alice/Bob Persons + typing rules) → derives both are Agents.
- **SUMO upper spine** — a **pure T-box** (43 subsumption rules, *zero* individuals) →
  materializes to the **empty model**. A subsumption proposal then reads **vacuously
  TRUE** (closed — a nonsense universal reads TRUE too) or **UNKNOWN** (open). *Model-
  checking cannot decide a theorem of the theory.*

**The fix — `src/theory_query.py` (`entails`, 15 tests).** The deduction
`GENERATION_AND_TESTING.md` routes to "the contest/deduction game": decide a universal
`~[ B ~[ H ] ]` by **freeze-a-fresh-witness** — mint an arbitrary constant per body
line, assert B over it, **materialize M ∪ {frozen B}**, check H. Sound (witnesses
mentioned nowhere in M ⇒ holds for all) + Horn-complete (least Herbrand model). A
negative is FALSE only when M is **wholly Horn**, else **UNKNOWN** (skipped non-Horn
axioms might bear) — so `Man ⊑ Beast` over Porphyry is honestly UNKNOWN (its Man/Beast
**disjointness** is the skipped denial that would settle it). Verified on the corpus:
SUMO `Object ⊑ Entity` TRUE / `Object ⊑ Occurrent` FALSE; FOAF `knows(y,z) → Agent(y)`
TRUE (typing chained through subsumption).

**Wiring.** `/agon/interpret` + `_interpret_payload` return a `theorem` block beside
the extensional `verdict` whenever `materialize` is set and G is a universal Horn scroll.
Peel stays pure model-checking; the theory query is the inference step. Doc:
`docs/DOMAIN_ORACLE_AND_M.md` §6.2. *Frontend rendering of the `theorem` block is the
next small task.*

---

### Done previous session (the Agon interpretation arc) — for reference

1. **The semantic-game seam — DONE 2026-06-11** (`src/semantic_game.py`, 17 tests):
   `evaluate(egi, oracle)` reads G outside-in, returns three-valued `Verdict3` +
   transcript + structured `winning_witness` / `counterexample`. Kleene logic.
2. **The interpretation register in Agon — DONE 2026-06-11.** The inning *given M,
   then G*: part 1 choose M (`set-model` + new-game framing), part 2 peel
   (`POST /agon/games/{id}/interpret` runs the semantic game, non-mutating), part 3
   decide (`available_dispositions(game, verdict)` annotates the taxonomy by the
   outcome — a hint, never a filter; nothing auto-asserts). 14 route tests; the five
   persona innings reproduce through the route. Design-of-record:
   `docs/GENERATION_AND_TESTING.md` (the eliminative/additive cut; making=Ergasterion,
   game=Agon; deduction-through-Agon; model-checking-vs-inference; truth-vs-validity;
   part-3-is-a-judgment).
3. **Agon frontend — DONE 2026-06-11.** `/agon` now has a reference-model picker
   (`GET /agon/models` = curated persona scenarios + corpus UoDs; `src/agon_models.py`),
   an open/closed toggle, and a **"▷ Does G hold in M?"** button running the
   standalone `POST /agon/interpret` (resolve M → peel → verdict + transcript +
   witness/counterexample + verdict-annotated dispositions, shown in place of the
   board). "Play it out" still starts a full contest. Nothing asserted.
4. **Next: materialize the model** (oracle step 3, `docs/DOMAIN_ORACLE_AND_M.md`
   §6.1) — author M as *facts + Horn rules*, forward-chain to the least Herbrand
   model, peel against that. Resolves "model-checking, not inference" (the syllogism
   works; corpus UoDs carrying rules become testable); precondition for ontology-as-M.
   `src/model_materialization.py` (`materialize_egi`), reusing `match_atoms`; opt-in on
   `CorpusOracle.from_egif(..., materialize=True)` and `/agon/interpret`.
5. **The inverse pivot — DONE 2026-06-11.** `POST /agon/where-it-holds` + a "🔎 Where
   does G hold?" button: fix G, range the peel across candidate models (examples +
   corpus, optionally materialized), rank by relationship — holds / partial (residue =
   the contribution) / independent / contradicts. Abductive context-retrieval; reused
   the oracle unchanged (`docs/DOMAIN_ORACLE_AND_M.md` §7).
6. **Then:** oracle steps 4–6 (demand-driven cache → horizon/open-closed params →
   `SparqlOracle`/Wikidata); downstream warrant lifecycle, **ontology-as-M** (now
   unblocked — materialize the T-box, peel/search against it).
3. **Diachronic exemplars (Praeclarum first)** — interleave once the seam exists:
   ingest canonical worked proofs as real `TransformationChain`s; the shakedown
   cruise for the semantic game. `docs/` + the diachronic-exemplars memory.
4. **Math menu** (independent, ready): ∀x scaffold tactic → selection-driven `fold`
   → ZFC/Peirce-1881 fixtures + graph-with-holes schema node. Palate-cleanser depth.
5. **Editor-persona frontier** (off the Agon path): by-hand reading desk + LaTeX/TikZ
   export (the `egpeirce.sty` lineage; exporter exists, DTO→TikZ adapter + web button
   don't). Do when the external Peirce-edition audience is the priority.

The **Domain Oracle** (`src/domain_oracle.py`, 16 tests) is built and waiting on
step 1: `resolve(g)` = conjunctive-query homomorphism of a negation-free `g` into a
model's asserted atoms → CONFIRMED/UNKNOWN/DENIED with provenance; `witness()` for
the negative-area pick. Built on the public EGI API, not the protected iso engine.

---

## ✅ DONE 2026-06-11 — challenge mode (freeform step 4)

Correspondence, learned by doing: present a linear form, draw it freehand, grade the
attempt against the parsed target. The grader is isomorphism (`same_graph`); the
feedback is the **legible EGI diff** in EG vocabulary (missing/extra/scope/incidence/
order), never a pixel comparison — a drawing that *looks* different but denotes the
same graph passes; one that mis-scopes a line fails with a scope finding.

- **`src/challenge_mode.py`** (12 tests) — standalone gradeable core: `Challenge` +
  a curated `CHALLENGE_BANK` difficulty gradient (one-relation → argument-order →
  shared line → negation → the scroll → the universal `~[ (man *x) ~[ (mortal x) ] ]`,
  where a line crossing a cut boundary makes scope the gold error); `list_challenges`
  / `get_challenge`; `grade(target, attempt) → DiffReport` (parse target, `legible_diff`).
- **Routes** (`web_api/routes/ergasterion.py`, 9 tests in `test_ergasterion_challenge.py`):
  `GET /ergasterion/challenges` (prompts only, never a drawing) and
  `POST /ergasterion/sessions/{id}/grade-challenge` (read the drawing → ill-formed ink
  returns validity feedback not a grade; well-formed → `matches` + findings +
  `target_linear_forms`). **Non-mutating** — grading never touches session state.
  `ChallengeGradeRequest` in `api_models.py`.
- **Frontend** (`web_viewer/ergasterion.html`): a challenge picker + prompt/hint +
  "Grade my drawing" + result panel inside the freeform tools; populated from the
  bank on first arming; node `--check` clean, page serves, endpoint verified. Real-
  browser interaction unverified here (no headless browser this session).

Building challenge mode was the ongoing stress test of `read_drawing` on human input,
as designed (`docs/FREEFORM_COMPOSITION_AND_LEARNING.md`).

---

## Freeform composition arc (Thread B) — COMPLETE (steps 1–4, 2026-06-10/11)

**Designated next task: the freeform composition canvas** — composition becomes
*draw-then-read*. The exact-correspondence engine (Phases 1–4) is done; that was
**build step 0** of `docs/FREEFORM_COMPOSITION_AND_LEARNING.md`, so the next session
**starts at step 1**. Read that doc's "Build order" + the three-move arc, and
`docs/SESSION_LOG_2026-06-10.md` for how the foundation got here.

**The build, in order (each a shippable increment):**
1. **Visible containment + snapping + fix-time validity** (the de-risked core).
   - **Fix-time validity pass — DONE 2026-06-10** (`src/drawing_validity.py` +
     `tests/test_drawing_validity.py`, 13 tests). `validate_drawing(dto) →
     ValidityReport` runs `read_drawing` and catches the ill-formed drawings the
     reader *can* read, in EG vocabulary: **errors** (`overlapping_cuts` — cut curves
     cross, so the areas aren't a tree; `dangling_line` — a line end touches no mark
     within tolerance, the brittle stops-short/drift case) and **warnings**
     (`boundary_band` — a mark on a cut's boundary stroke; `unwired_predicate` — reads
     as 0-ary; `label_overlap`). `report.is_well_formed` = no errors. Geometry of
     record reused from `presentation_ops` (`cut_boundary`/`point_in_polygon`/
     `predicate_label_box`), so "inside / on the boundary" is the same curve the
     renderer draws and §3.3 attests; clean engine layouts raise zero errors.
   - **Visible containment + live feedback + snapping — DONE 2026-06-11** (on the
     freeform canvas). Cut interiors render as translucent filled regions (polarity
     by nesting depth); **live area feedback on drag** ("inside cut C" / "on the
     sheet") via point-in-polygon `areaAt`; **snapping** — line endpoints attach to
     marks by construction (click-a-mark line tool, so no stops-short/drift), and a
     **spot snaps clear of any cut boundary** (`_snapSpot`) on placement and
     drag-release so its area is never ambiguous (E2E-tested). `validate_drawing` is
     wired into the fix/read endpoints. **Step 1 is complete.**
2. **The freeform drawing canvas — DONE 2026-06-11** (backend tested; frontend
   shipped, interactive layer pending author's-eyes verification). Composition is
   now *draw-then-read*: the browser owns the ink, no live EGI, linear forms silent
   until gate ①.
   - **Backend (`src/drawing_to_egi.py` + two routes).**
     `build_egi_from_drawing(dto, predicate_labels, vertex_labels)` is the
     construction half of *fix = read*: `read_drawing` recovers structure (area
     tree + ordered incidence), the drawing carries content (relation names,
     constant labels), and this joins them into a real EGI. Corpus round-trip via
     `same_graph` (both styles, nested cuts, argument order, constant-vs-generic).
     `POST /ergasterion/sessions/{id}/read-drawing` (non-mutating preview: validity
     + linear forms) and `POST …/fix-drawing` (gate ①: validate → build → install
     as composing state → cross into deriving; §3.3 attested; refuses ill-formed in
     EG vocabulary). Additive — the typed `composition_ops` path is untouched.
   - **Frontend (`web_viewer/js/freeform-canvas.js` + Ergasterion integration).**
     Self-contained `FreeformCanvas` SVG surface (own coordinate space): tools
     Move / Line (vertex) / Relation / Constant / Cut (drag an ellipse) / Connect /
     Erase; translucent cut fills (polarity by nesting depth); **live area feedback**
     on drag (point-in-polygon `areaAt`, the same test the server uses); a cut is
     just ink (erase it, contents stay; drag a mark across a boundary to change
     area). "👁 Read it now" → preview; "① Fix this graph" → `fix-drawing` when ink
     is present. Opt-in toggle in the composing palette.
   - **Tests:** `test_drawing_to_egi.py` (6), `test_ergasterion_freeform.py` (12,
     incl. JS-serialize↔backend contract for binary order + ellipse-cut negation).
     Both JS files syntax-clean; page + asset serve. **Pending:** interactive
     pointer/drag behaviour in a real browser (no headless browser here).
3. **The legible EGI diff — DONE 2026-06-11** (`src/egi_diff.py`, 11 tests).
   `legible_diff(target, attempt) → DiffReport`: empty (and `matches` True) iff
   `same_graph`; else EG-vocabulary findings — `structure` (cut count),
   `missing`/`extra` (relations + individuals), `scope` (wrong cut/polarity — the
   gold Beta error), `incidence` (wrong connections), `order` (argument order).
   Content-aligned, not id-aligned (constants by label, relations by name +
   best-match arg signature, generic lines by incidence overlap aligned *first*).
   Ready for challenge mode.
4. **Challenge mode**: pick a tomos linear form, hide its drawing, grade the freehand
   attempt with `same_graph` + the diff. Difficulty gradient straight from the
   corpus (single relation → nested cuts → Beta with a shared line crossing a
   boundary). Building (4) *is* the ongoing stress test of `read_drawing` on humans.

**Building blocks in hand:** `read_drawing` (de-risked on human geometry,
`test_eg_reader.py::test_freeform_*`), `diagram-viewer.areaAtPoint` +
`isPointInFill` (Phase 4), `presentation_ops.cut_boundary` + `LayoutDTO.cut_boundary`
(a cut as a drawn polyline), §3.3 attestation at gate ①, `same_graph` /
`reading_matches_egi`. The one genuinely new logical piece is the **legible EGI diff**
(step 3). Scope boundary (load-bearing): Arisbe reads **structured placement, not
pixels** — reading a raster image is deferred (a hand-off to external AI that emits a
structured placement into the same `read_drawing` pipeline).

After freeform: the appetite-driven **math menu** (∀x scaffold tactic; selection-driven
`fold`) and the **Agon web arena** — independent and ready to pick.

### Phase 3c — clockwise placement (Peirce's writing convention) — DONE 2026-06-10
*ν specifies the order, so the drawing shows it: hooks drawn clockwise around the
spot in ν-order, by construction — consistently across every style and layout.*
`clockwise_placement.place_clockwise_hooks` (pre-attestation in `layout_service`,
applied for **all** styles): every ≥2-ary predicate's hooks → clockwise slots in
ν-order at the **rotation that best aligns with the vertices** (crossings
minimized). The **hook position** (`points[0]`) carries the order, so lines run
**straight to their vertices — no stub, no kink**. Locally guarded so **no line
strikes through any predicate label** (a spoke forced across its own spot reverts
to the natural hook); also reverts where a cut would be pierced. Carried by a
**single start anchor** (`assign_order_labels` ≤1 mark/relation; `read_drawing`
anchor-aware) + `argument_order_numerals: auto|always|never` toggle. §3.3 green; no
label strike-throughs; ordered round-trip **23/23** (`auto`) — placement where the
layout cooperates, numeral where it reverts. **Decision (2026-06-10): constrained
layout for clock-face placement considered and DECLINED** — it doesn't scale (a
shared line of identity gives a vertex conflicting clockwise demands from every spot
it touches; it would fight the cut hierarchy — exactly why Dau numbers the lines).
Order lives in ν; the numeral/anchor is the scalable carrier of record; clockwise
placement is a best-effort small-graph aesthetic. **Phase 3 / the exact-correspondence
extents work is DONE.**

### Label-aware ligature routing — DONE 2026-06-10
*Phase 3b's deferred third occlusion property shipped with its constructive
partner.* The §3.3 check (`correspondence_attestation` check #3) refuses any line
of identity running through a label box it is **not** incident to
(`path_intersects_box`, open interior). The partner
(`elk_layout_engine._build_ligature_paths`) routes non-incident lines *around*
label boxes as **soft obstacles** in a two-tier router: forbidden cuts are **hard**
(never crossed — soundness), label boxes are **soft** (skirted only when a detour
still clears every hard cut; otherwise the label yields to the sound route). Cleared
the `roberts_domain_modeling` IT+ strike-through ("Person" struck by the
shared-vertex fan-in); full §3.3 corpus + transformation + routing suites green.
Unit tests: `test_projection_conventions.py` (soft-skirt / hard+soft / soundness
fallback) + `test_correspondence_attestation.py::test_label_box_struck_through_by_non_incident_line`.

### Thread A — the exact-correspondence engine (`docs/EXACT_CORRESPONDENCE.md`)
*Delete the geometry proxy: a cut **is** its drawn curve; containment / crossing /
extents are exact facts about the literal picture; the browser is the client-side
arbiter; the logic stays coordinate-free.*

- **Phase 1 — exact cut containment — DONE** (`629a161`): `point_in_cut`/
  `bounds_in_cut` test the rounded rectangle the renderer draws (corner radius), so
  the corner void is gone. Threaded through `eg_reader` + `correspondence_attestation`;
  zero regression (482 §3.3 tests).
- **Phase 2 — exact ligature crossing — DONE** (2026-06-10): `count_cut_crossings`
  takes the corner radius and counts crossings against the rounded rectangle the
  renderer draws (edges inset by the radius + four corner arcs —
  `_rounded_rect_secant_crossings`), so a ligature grazing a rounded-away corner
  reads *outside* (not a spurious cut entry). Attestation threads `cut_radius`; 457
  §3.3 tests green, new unit tests pin corner-graze / straddle / pass-through.
  *Still open:* chosen-crossing-point *placement* in the renderer (a routing concern,
  deferred).
- **Phase 3 — label/numeral extents.** Three sub-pieces:
  - **3a — label-box containment / no straddle — DONE** (2026-06-10):
    `presentation_ops.predicate_label_box` is the single source of truth (renderer
    draws from it; §3.3 tests it). A predicate's containment is its drawn label box —
    wholly inside ancestor cuts, wholly outside others (`box_intrudes_cut`), no
    straddle. Vertices stay dots. 521 §3.3 tests green corpus-wide.
  - **3b — no improper occlusion — DONE** (2026-06-10): three §3.3 properties green
    corpus-wide — text-on-text overlap (`boxes_overlap`), vertex/constant label
    no-straddle (cut-aware `vertex_label_box`, factored out of the renderer as the
    single source of truth, the way 3a factored `predicate_label_box`; renderer draws
    text centred in that box), and **no strike-through** (a non-incident line through
    a label box, `path_intersects_box`) — the last shipped with its constructive
    partner, **label-aware ligature routing** (`_build_ligature_paths` skirts label
    boxes as soft obstacles, cuts stay hard; cleared the `roberts_domain_modeling`
    IT+ fan-in strike-through). Surfaced + fixed one real straddle ("Socrates" at a
    cut edge in `peirce_cp_4_394_man_mortal`).
  - **3c — clockwise placement (writing convention) — DONE** (2026-06-10): hooks
    drawn clockwise around the spot in ν-order by construction
    (`place_clockwise_hooks`, best-fit rotation = crossings minimized; 10-ary = a
    clock face), carried by a single start anchor + the `argument_order_numerals:
    auto|always|never` toggle. §3.3 green; ordered round-trip 23/23 with zero
    numerals (`never`).
- **Phase 4 — cut as a drawn polyline + browser as client-side arbiter — DONE**
  (2026-06-10): `LayoutDTO.cut_boundary` carries a cut's literal polyline (freeform
  human-drawn cuts); `resolve_cut_boundaries` shares it between §3.3 + `eg_reader`
  (point-in-polygon); renderer draws it as `<path>`; `diagram-viewer.areaAtPoint`
  hit-tests via `isPointInFill`. Wobble stays render-only cosmetic. Unblocks the
  freeform canvas.

### Thread B — freeform composition + challenge mode (`docs/FREEFORM_COMPOSITION_AND_LEARNING.md`)
*Composition becomes freeform drawing (typed marks at free positions, no live EGI);
the picture is read into a sign only at gate ① (`read_drawing` → EGI → validity →
"what it says"). Then challenge mode: show a linear form, draw it freehand, grade
with `same_graph` + a legible EGI diff — correspondence learned by doing.*

Reader **de-risk is DONE** (`read_drawing` is sound on human geometry; gaps are only
snapping + validity, pinned in `tests/test_eg_reader.py::test_freeform_*`). Build
order: (1) snapping + fix-time validity pass (depends on Phase-1 exact containment,
now in); (2) the freeform drawing canvas (replace the composing-phase typed
`composition_ops` with place/drag/erase on a free `LayoutDTO`; live forms silent
until fix); (3) the legible EGI diff (align by label+role, diff area-tree +
incidence/order — reused by validity *and* challenge mode); (4) challenge mode over
the tomos corpus. Building (4) *is* the ongoing stress test of (1).

*Scope boundary (load-bearing): Arisbe reads **structured placement, not pixels**.
Reading a raster image (photo/scan/freehand) is deferred — likely a hand-off to
external AI that emits a structured placement into the same pipeline.*

### Ready-to-pick math tasks (independent, both unprotected)
- **∀x scaffold tactic** — `universal_generalization` in `src/derived_rules.py`,
  closing `∀x∀y∃z plus` (parametric totality already proven). Sound-by-construction
  recipe in `docs/UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md` §2–§3 (the dual-rule
  approach is provably unsound — use the scaffold).
- **Selection-driven `fold`** — `fold_selection` in `src/definitions.py`: iso-match a
  drawn body to a definition and contract it (sound gate = selection ≅ body, ports
  aligned). `docs/DEFINITION_NODE.md` "Open / next".

---

## Backlog (queued, lower priority)

- **✅ P0 TRIAGED + RESOLVED 2026-06-12 — the 7 pre-existing red layout tests.** A full-suite
  run (1657 passed, 7 failed) flagged them; **confirmed not from the CLIF work** (reproduce
  with `src/clif_*_dau.py` stashed; import no CLIF). A comprehensive per-(engine, style,
  convention) corpus sweep pinned the *exact* frontier, and **§3.3 (`test_correspondence_invariant`)
  still attests every one of these (EGI, drawing) pairs faithful corpus-wide** — what failed is
  the *stronger* `read_drawing(render(egi)) == egi` geometric inversion, on two large imported
  reasoning ontologies (landed for theory-query/materialization, not for drawing):
  - **`bfo_core` under ELK only** — ELK packs its 47 cuts so densely the reader misreads the
    structure; the **Tension** engine lays the *same* graph out invertibly (passes there). An
    ELK layout-density frontier (the "layout-perf frontier" noted when bfo_core landed).
  - **`colore_between` under clockwise-ordered only** — the clockwise convention can't carry
    the argument order of its ternary `between(x,y,z)` atoms recoverably; the **numbered**
    convention (the authoritative ν carrier; clockwise is best-effort by design, Phase 3c)
    does, so numbered/unordered round-trip fine.
  Resolution: a documented `_reader_frontier(uod, engine, clockwise)` helper in
  `tests/test_eg_reader.py` defers *exactly* those (uod, engine, convention) combos (preserving
  every passing case — e.g. bfo_core/Tension and colore_between/numbered stay tested, and the
  §3.3 + no-strikethrough checks still run for both). The 7th,
  `test_tension_engine.py::test_branch_tree_is_compact`, is **xfail**'d: a deterministic
  compaction regression in the **opt-in** tension engine (`roberts_domain_modeling` spreads to
  ~1189×686 vs ~325×443 under default ELK; still §3.3-faithful, just not compact). Two genuine
  follow-ups remain (below).
- **Reader robustness on dense ELK layouts (follow-up to P0).** Make `bfo_core`'s 47-cut ELK
  layout reader-invertible (Tension already is) — either sparser ELK packing for dense
  ontologies or a more robust `read_drawing` cut/incidence recovery. Then drop `bfo_core` from
  `_reader_frontier`. §3.3 already guarantees the correspondence; this is the stronger
  round-trip.
- **Tension-engine compaction regression (follow-up to P0).** `test_branch_tree_is_compact` is
  xfail'd: `roberts_domain_modeling` (degree-4 cross-cut junction) spreads to ~1189px wide vs
  the `<650` the compaction targets and ~325px under ELK. Deterministic; suspected origin is
  the `_box_cuts` style-aware refactor in `40286a7` (the test passed when added in `8685dad`).
  Fix the tension tree/fallback compaction, then remove the xfail. Opt-in engine, so lower
  stakes.
- **Schema generator — shared ambient parameter** so `instance_of_schema` can
  generate the hand-written induction instance (φ threaded through all hole
  occurrences); assert `same_graph` to the hand-written one.
- **CG / ISO 24707 conformance write-up** for the definition node (marked-parameter
  syntax, contraction/expansion) — cite alongside the fixtures.
- **Corpus-import the math theories** — ZFC + Peirce 1881 as real UoDs (schemas +
  definitions store them finitely; the R7 horizon).
- **Gamma frontier** — predicate/property quantification, modality / the broken cut
  (the schema drew the map).
- **Publish-to-Organon as an unattested record** (composition spec §5.3) — a
  mode-contract question for the author; disposition today = vault (scratch) or Agon.
- **Agon depth** — semantic layer, auto-Grapheus, dynamic move set (deferred from V1).
- *(optional, PROTECTED)* widen `HeavyDotInsertionRule` to Dau's any-context rule.

---

## Recently shipped (newest first — detail in git / docs / memory)

- **2026-06-11** — **Freeform step 2: the draw-then-read canvas** (backend tested;
  frontend shipped). `drawing_to_egi.build_egi_from_drawing` is the construction half
  of fix=read (structure from `read_drawing` + content from carried labels → a real
  EGI; corpus round-trip via `same_graph`). Two additive Ergasterion routes:
  `read-drawing` (non-mutating preview) and `fix-drawing` (gate ①: validate → build →
  install → derive; §3.3 attested; ill-formed refused in EG vocabulary). Frontend
  `freeform-canvas.js`: a self-contained SVG drawing surface (place/drag/erase typed
  marks, cuts as drawn ellipses, translucent fills, live point-in-polygon area
  feedback) wired into the composing palette via an opt-in toggle; "Read it now" +
  freeform "① Fix this graph". 18 new tests (builder corpus round-trip + route
  round-trip + JS-serialize↔backend contract). Interactive pointer layer pending
  author's-eyes verification (no headless browser available).
- **2026-06-10** — **Freeform step 1: fix-time validity pass** (`src/drawing_validity.py`,
  13 tests). `validate_drawing(dto) → ValidityReport`: the well-formedness backstop of
  *fix = read* — `read_drawing` reads exactly what is drawn even when it isn't a legal
  EG, so this catches the ill-formed drawings in EG vocabulary. Errors:
  `overlapping_cuts` (curves cross → areas not a tree), `dangling_line` (a loose end,
  incl. the stops-short/drift brittleness). Warnings: `boundary_band`,
  `unwired_predicate` (0-ary), `label_overlap`. Twin of `correspondence_attestation`
  (which checks against a *known* EGI); this checks a freeform drawing with *no EGI
  yet*. Reuses `presentation_ops` geometry of record; clean engine layouts raise zero
  errors. Remaining step-1 UI (filled regions + live drag feedback + snapping) folds
  into step 2's canvas.
- **2026-06-10** — **Phase 4: cut boundary as a drawn polyline + browser as
  client-side arbiter.** A cut can be carried as its literal closed polyline
  (`LayoutDTO.cut_boundary`), the foundation for human-drawn freeform cuts.
  `presentation_ops.cut_boundary` generates the curve; `point_in_polygon` /
  `polyline_polygon_crossings` test it; `resolve_cut_boundaries` is the boundary of
  record shared by §3.3 + `eg_reader` (carried polyline → point-in-polygon; analytic
  cut → exact `point_in_cut`). `point_in_cut`/`bounds_in_cut`/`count_cut_crossings`
  take an optional `boundary`. Renderer draws a carried polyline as `<path>`;
  `diagram-viewer.js::areaAtPoint` uses `isPointInFill` for placement/drag
  hit-testing. Wobble stays a render-only cosmetic (not attested — testing it was a
  false positive, correctly left alone). §3.3 corpus green; new freeform tests.
- **2026-06-10** — **Phase 3c: clockwise placement as Peirce's writing convention**
  (consistent across all styles/layouts). `clockwise_placement.place_clockwise_hooks`
  draws every ≥2-ary relation's hooks clockwise around the spot in ν-order by
  construction, at the best-fit rotation (crossings minimized; 10-ary = a clock
  face). The hook *position* (`points[0]`) carries the order, so lines run straight
  to vertices — no stub, no kink. Applied for **every** style (numbered draws them
  clockwise + numbered; Peirce clockwise + zero/anchor) so the picture reads the
  same everywhere. Hook-position carrier (`points[0]`) = straight lines, no kinks.
  Locally guarded so **no line strikes through any predicate label** (a spoke forced
  across its own spot reverts to the natural hook + numeral). Single start anchor +
  `argument_order_numerals: auto|always|never` toggle. §3.3 green; no label
  strike-throughs; ordered round-trip 23/23 (`auto`). Reframed across the session at
  the author's direction: corpus-tuned fragile-patch → writing convention →
  hook-position carrier (no kinks) → consistent across styles → no own-label strikes.
  Constrained-layout clock faces **considered + declined** (doesn't scale — shared
  lines of identity give conflicting clockwise demands; numerals are the scalable
  carrier, clockwise is small-graph sugar). Phase 3 complete.
- **2026-06-10** — **Label-aware ligature routing** (Phase 3b's third occlusion
  property + its constructive partner). §3.3 check #3 refuses a line of identity
  running through a label box it is *not* incident to (`path_intersects_box`); the
  partner routes such lines *around* label boxes — two-tier routing in
  `_build_ligature_paths` (forbidden cuts **hard** / soundness; label boxes **soft**
  / legibility, yielding to cuts). Cleared the `roberts_domain_modeling` IT+
  shared-vertex strike-through; full §3.3 corpus + transformation + routing suites
  green. Phase 3b now complete (three properties).
- **2026-06-10** — Exact-correspondence **Phase 3b** (no improper occlusion): two
  §3.3 properties green corpus-wide — text-on-text label overlap (`boxes_overlap`)
  and vertex/constant label no-straddle (cut-aware `vertex_label_box`, the renderer's
  placement factored into one source of truth; text drawn centred in the box). Fixed
  a real straddle ("Socrates" at a cut edge). The non-incident-ligature property is
  deferred with its routing partner (`path_intersects_box` primitive in hand).
- **2026-06-10** — Exact-correspondence **Phase 3a** (label-box containment): a
  predicate's containment is its drawn label box, not the anchor point
  (`predicate_label_box` single source of truth — renderer draws it, §3.3 tests it;
  `box_intrudes_cut` forbids straddling into non-ancestor cuts). 521 §3.3 green.
- **2026-06-10** — Exact-correspondence **Phase 2** (exact ligature crossing): the
  crossing test reads off the same rounded-rect boundary as Phase 1's containment
  (`count_cut_crossings` corner-radius-aware; `_rounded_rect_secant_crossings` /
  `_seg_arc_crossings`), closing the crossing-side of the corner void. 457 §3.3 green.
- **2026-06-10** — Exact-correspondence Phase 1 (exact cut containment) +
  architecture doc + scope boundary. Ergasterion review: keep-in-view camera;
  composition reconceived as **synchronic** (no `compose.*` steps; chain begins at
  gate ①) then as **freeform draw-then-read**; `read_drawing` de-risked.
  Docs: `EXACT_CORRESPONDENCE.md`, `FREEFORM_COMPOSITION_AND_LEARNING.md`,
  `DEVIN_SETUP.md`.
- **2026-06-09** — Cut-level `IT-`/`ERA` in the engine; **parametric totality of
  addition** assembled (∀Y∃z plus(x,Y,z)). Dau ∀x homework (scaffold tactic).
  Hole/schema §3.3 (a hole corresponds). Definition-node local reversible
  `expand_at`/`fold` (Borges-map guardrail). Composition workflow built (palette, two
  fixings, per-branch phases). Docs: `UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md`,
  `SCHEMA_HOLE_CORRESPONDENCE.md`, `DEFINITION_NODE.md`, `COMPOSITION_WORKFLOW_SPEC.md`.
- **2026-06-08/09** — Recursion fixtures + the induction arc; graph-with-holes schema
  node + definition layer (`schema.py`, `definitions.py`, `eg_splice.py`); math
  fixtures (ZFC + Peirce 1881). Organon import build: provenance/annotation layer, 3
  fixtures, corpus retrofit (`CORPUS_AND_IMPORT_MODEL.md`). Ontology import.
- **2026-06-06/07** — Tension layout engine (`TENSION_LAYOUT.md`); presentation-delta
  / style ladder (`PRESENTATION_DELTAS_AND_STYLE.md`); four-beat transformation
  grammar complete for all six rules (`TRANSFORMATION_WORKFLOW_SPEC.md`); Settle
  editing surface; NaturalLayout — "own the dimensionality".
- **2026-06-01/03** — All three web modes live (Organon / Ergasterion / Agon);
  runtime §3.3 correspondence attestation; the drawn→EG reader (`eg_reader`);
  Peirce visual-fidelity tiers (oval cuts, hand-drawn wobble, TikZ parity);
  import doorway (low-warrant) + export arc; `MANIFEST_AND_MEANING.md`,
  `CHAIN_OF_SEMIOSIS.md`.

---

## Notes on workflow

Primary development is local, on `main`; GitHub is backup, not a collaboration
surface. No PR ceremony (single developer, single site): commit to `main`, push to
back up. Feature branches are optional backup points, fast-forwarded into `main`
rather than merged via PR. The pre-commit quality gate runs the core suite; the full
suite (`uv run pytest tests/ -q`) is ~11 min. Protected core modules need
`touch .core_modification_authorized` (gitignored); the active threads above are all
unprotected.
