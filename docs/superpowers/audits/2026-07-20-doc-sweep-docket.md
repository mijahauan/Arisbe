# Doc-sweep audit docket — commit 9edb60f — 87 top-level docs audited

0 of 87 came back clean-of-all-dimensions; every doc got at least a DEEP-tier pass (book
chapters, 7 dimensions) or a LIGHT-tier pass (non-book, dimensions 2/4/5 + dead-refs) and
most surfaced at least one finding somewhere in the cluster. 20 individual files read back
fully clean on every dimension in scope for their tier (named at the end of each tier
section below and in the Coverage line).

## Cluster → doc map

| Cluster | Tier | Docs (count) |
|---|---|---|
| A | DEEP | LINEAR_GRAPHICAL_CORRESPONDENCE, EXACT_CORRESPONDENCE, SOUNDNESS_BOUNDARY, PERFORMANCE_ENVELOPE, DAG_HISTORY_ARCHITECTURE, UNIVERSE_OF_DISCOURSE_ARCHITECTURE, CHAIN_OF_SEMIOSIS, MANIFEST_AND_MEANING, MEANING_BY_HISTORY, LEVEL_ZERO_AND_THE_REGISTERS (10) |
| B | DEEP | FIDELITY_AND_DEPARTURES, FIDELITY_A_PLAIN_ACCOUNT, FIDELITY_ENDOPOREUTIC_CHECK, ADVERSARIAL_EXAMINATION, MODALITY_WITHOUT_GAMMA, SECOND_ORDER_FRONTIER, VISION_AND_SCOPE, CAPABILITY_MAP, GLOSSARY, CONTRIBUTION_AND_PRIOR_ART (10) |
| C | DEEP | DOMAIN_ORACLE_AND_M, GENERATION_AND_TESTING, ENDOPOREUTIC_GAME_GUIDE, EXTERNAL_SOURCES_AND_IMPORT, IMPORT_EXPORT_FORMATS, CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION, NL_TO_LOGIC, EXEMPLARS (8) |
| D | DEEP | GETTING_STARTED, FIELD_GUIDE_AND_DRAGONS, TEACHING_PACK, TROUBLESHOOTING, ARISBE_IN_PRACTICE, ARISBE_FOR_SCHOLARS, FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION, FREEFORM_COMPOSITION_AND_LEARNING, GAMMA_DEMONSTRATIONS, DEPLOYMENT_AND_MULTIUSER, ALPHA_RELEASE_PLAN, ARISBE_CORE_API_REFERENCE, arisbe_triad_architecture (13) |
| E | LIGHT | AUTOMATED_MODEL_DEVELOPMENT, AUTOMATED_ENDOPOREUTIC_GAME, AUTOMATED_GRAPHEUS, M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE, CROSSING_DECISION_BRIEFS, SECOND_ORDER_CORE_OPENING, SECOND_ORDER_LANDSCAPE_AND_POSITIONING, SECOND_ORDER_CORRESPONDENCE_CONTRACT, FORCING_AND_THE_GAMMA_CROSSING, CATEGORIES_AND_THE_THREE_PARTS (10) |
| F | LIGHT | THE_KYTOS, THE_MEASURE_OF_KNOWLEDGE, THE_COMMENS_AND_THE_COMMUNITY, BOOTSTRAP_AND_DIRECTED_ENGAGEMENT, TUTOR_LOOP, RATE_AND_INTELLIGIBILITY, THE_MINIMAL_IN_VIEW_SET, MATHEMATICS_FROM_THE_SHEET, MATH_FIXTURES_ZFC_PEIRCE_1881, PRODUCT_VISION, PROSPECTS_MULTIPERSPECTIVE (11) |
| G | LIGHT | ADAPTIVE_SCOPE_VIEWER, TENSION_LAYOUT, PRESENTATION_DELTAS_AND_STYLE, STYLE_SYSTEM_GUIDE, WEB_VIEWER_DESIGN, UI_TRANSPARENCY_CHARTER, ELK_LAYOUT_IMPLEMENTATION_SUMMARY, TRANSFORMATION_WORKFLOW_SPEC, COMPOSITION_WORKFLOW_SPEC, UNIVERSAL_GENERALIZATION_DAU_HOMEWORK, ROADMAP (11) |
| H | LIGHT | DEFINITION_NODE, REFERENCE_AND_TRANSCLUSION_NODE, SCHEMA_HOLE_CORRESPONDENCE, CORE_API_USAGE_GUIDE, CORRESPONDENCE_CONTRACT, MCP_VERIFIER, PROOF_SERIALIZER, CORPUS_AND_IMPORT_MODEL, RETURN_TO_DEVELOPMENT, ARCHIVE_INDEX, ARISBE_EXISTENTIAL_GRAPH_DEFINITION, ALPHA_BETA_UX_DOCKET, JARGON_AUDIT, STORM_DOCS_AUDIT (14) |

10+10+8+13+10+11+11+14 = **87**.

---

# Tier 1 — Mechanical

Findings whose fix is a verified factual swap (a wrong count, a nonexistent file/method, a
stale timestamp, a self-contradicting parenthetical) rather than an editorial judgment call.
Every item below is independently code/repo-verified in the cluster read (re-spot-checked
for the (b)/(c) batches while assembling this docket).

## (a) Dead-refs
**None real.** The pre-pass's mechanical link check is clean corpus-wide; all 6 raw
candidates it flagged were false positives (slug/URL-decoding artifacts), and no cluster
found a new one. Nothing to fix.

## (b) Vocabulary-conformance
- docs/SECOND_ORDER_CORE_OPENING.md, docs/SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md,
  docs/SECOND_ORDER_CORRESPONDENCE_CONTRACT.md, docs/FORCING_AND_THE_GAMMA_CROSSING.md,
  docs/CROSSING_DECISION_BRIEFS.md (whole docs) · vocabulary · I · the 2026-07-20 mention-ascent
  rename (GLOSSARY.md:328) deliberately updated only "live" references and left these five
  design memos on the old "second-order"/"the crossing" vocabulary; `CROSSING_DECISION_BRIEFS.md`
  in particular is still the standing design-of-record gating the not-yet-built B-full step, so a
  reader following that thread today hits no pointer to the rename. FIX: add a one-line retirement
  pointer near the top of each ("this memo predates the mention-ascent rename 2026-07-20 — see
  GLOSSARY.md#mention-ascent") — or explicitly rule the five frozen historical record, matching
  the "Moses" RELEASE_NOTES precedent. *(Note the correction below — the literal retired phrase
  is not actually present; only the general "second-order" vocabulary is dated. See "Triaged
  false positive.")*
- docs/THE_MINIMAL_IN_VIEW_SET.md:156 · vocabulary drift · M · the bracketed citation label
  "commens:" (linking the external *Commens* Peirce-terms dictionary, written 2026-06-25) now
  reads as if it pointed at Arisbe's own ratified `commens` doctrine (THE_COMMENS_AND_THE_COMMUNITY.md,
  2026-07-20). FIX: gloss inline ("the *Commens* Peirce-terms dictionary, unrelated to Arisbe's
  later commens doctrine") or drop the bracketed label.

**Triaged false positive (dropped, per instruction):** Cluster E's dimension-5 finding
characterized all five SECOND_ORDER_*/FORCING/CROSSING_DECISION_BRIEFS docs as using the
literal string **"the second-order crossing"** throughout. Verified directly
(`grep -rn "second-order crossing" docs/*.md`): the phrase appears in exactly one place
corpus-wide — `docs/GLOSSARY.md:328`, the retirement pointer itself ("Mention-ascent...
retires the earlier name 'the second-order crossing'"). The five memos use "the crossing" /
"crossing the frontier" / bare "second-order" as an adjective — not the retired term. The
vocabulary-conformance fix above is retained (those docs do predate the rename and would
benefit from a pointer), but the specific "still contains the retired string" claim is false
and is not carried forward as a defect.

## (c) Dedup — Conant–Ashby + the 3 workstream-A deferred Minors
- docs/CONTRIBUTION_AND_PRIOR_ART.md:199-205 vs :296-299 · dedup · M · the Conant & Ashby
  good-regulator theorem ("every good regulator of a system must be a model of that system")
  is quoted and explained in full twice in the same document — once under "Cybernetics"
  (justifying M's existence + the requisite-variety corollary), again in the closing
  concordance-bullet list (licensing the three EPG roles). FIX: keep the fuller Cybernetics
  statement as canonical; have the closing bullet cross-reference it ("see Cybernetics, above")
  instead of re-quoting verbatim.
- **The 3 workstream-A deferred Minors** (cluster A's three Minor-severity findings, batched
  together as one low-priority fix-wave):
  - docs/DAG_HISTORY_ARCHITECTURE.md (whole doc) · staleness · M · no status/date header, unlike
    every sibling architecture doc in the cluster, and no note distinguishing the newer
    `TransformationChain`/`ChainStep` model from the `EGITransformationHistory` DAG this doc
    documents. FIX: add a status line + a short disambiguating note.
  - docs/DAG_HISTORY_ARCHITECTURE.md (whole doc) · readability · M · book-tier chapter reads as
    a raw API dump (bare `HistoryBranchType.EXPLORATION`/`.ALTERNATIVE` with no prose), out of
    step with the cluster's other careful first-use-definition docs. FIX: one or two sentences
    per enum value + GLOSSARY links.
  - docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md:738-755 · overclaim · M · closing rhetoric
    ("Arisbe transcends the limitations of diagram editors and becomes a true logical reasoning
    environment") reads as an asserted-terminus marketing claim, out of step with the cluster's
    hedged/tiered honesty (contrast SOUNDNESS_BOUNDARY.md's proven/verified/attested/argued
    tiers). FIX: soften, or explicitly frame as the doc's original 2025-10-14 aspirational
    conclusion, now superseded by CAPABILITY_MAP.md.

## (d) Stale counts / nonexistent files / signatures / dates (verified against the live repo)
Grouped by doc:

- **docs/GLOSSARY.md:546** — "Protected core — the 17 modules..." → **14** (CLAUDE.md +
  `tools/core_protection_system.py`'s live `protected_modules` set both authoritative at 14;
  verified directly).
- **docs/CORE_API_USAGE_GUIDE.md**:
  - :11 "16 protected core modules" → 14.
  - :58-59 `create_edge(relation="Human")` — `Edge`'s real constructor takes zero params today;
    example raises `TypeError` if run as written.
  - :130-131 `create_cut(area_id="cut_1")` — same problem, `Cut` constructor is zero-arg.
  - :140-142 `index.get_nesting_info("cut_1")` — no such method on `HierarchicalIndex`
    (real accessors: `get_polarity`, `get_nesting_level`, `get_parent`, `get_children`,
    `get_ancestors`).
  - :20-40 lists `cgif_parser_dau`/`egif_parser_dau` as protected-core (de-protected 2026-06-27)
    and five modules that don't exist on disk at all (`enhanced_ligature_algorithms`,
    `ligature_optimization_engine`, `ligature_aware_positioning_engine`,
    `obstacle_aware_ligature_router`, `area_spatial_constraint_system` — the tool's own comments
    call four of these "ghosts" removed May 2026).
  - :3 dated 2025-01-19 with no later verified marker despite the above drift.
  - FIX (whole doc): regenerate the module index from `tools/extract_core_api.py` /
    `ARISBE_CORE_API_REFERENCE.md`; rewrite the two constructor examples to the current
    zero-arg + `with_edge`/`rel`/`nu` path; add a last-verified date.
- **docs/RETURN_TO_DEVELOPMENT.md**:
  - :45 "Protected modules (17...)" → 14.
  - :50-51 "src/ — core modules (~32 .py files)" / "tests/ (~955 passing, 35 skipped)" → current
    `src/*.py` top-level count is 118; CLAUDE.md's current figure is "~1000 passing, 35 skipped."
  - FIX: refresh both counts, or replace with a live-count instruction (the doc already tells
    the reader to run pytest).
- **docs/ARCHIVE_INDEX.md:289-305** — "What Remains Active": src/ 177, tests/ 58, tools/ 88,
  docs/ 62, styles/ 8 → current: src/ 118 top-level, tests/ 172, tools/ 131, docs/ 87, styles/ 9.
  FIX: drop the specific counts (point-in-time cleanup record) or caption "as of 2026-06-08."
- **docs/DOMAIN_ORACLE_AND_M.md** — :210 "`test_semantic_game.py` (15 tests)" → 18 (verified via
  `pytest --collect-only`); :319 "`test_theory_query.py` (15)" → 16. FIX: update counts or drop
  the specific numbers.
- **docs/IMPORT_EXPORT_FORMATS.md:383** — lists "RDF/OWL (semantic web)" under "Possible Future
  Formats"; already shipped (`tools/owl_to_clif.py`, `tools/rdf_to_owl.py`,
  `domain_model_importer.py`, `tests/test_owl_import.py`). FIX: remove from the future list,
  point to EXTERNAL_SOURCES_AND_IMPORT.md §3.
- **docs/STYLE_SYSTEM_GUIDE.md** — :453-457 "File Locations" cites `layout_engine_styled.py` /
  `style_integration.py`, neither exists; :421-431 "Debug Tools" cites
  `tools/validate_style.py` / `tools/test_style_layout.py` / `tools/style_preview.py`, none
  exist. FIX: replace with the real modules (`style_loader.py`, `style_specification.py`,
  `elk_layout_engine.py`) and real tests (`tests/test_styles.py`,
  `tests/test_styled_layout_engine.py`, `tests/test_svg_style_rendering.py`).
- **docs/ARISBE_CORE_API_REFERENCE.md:3** (mechanical, auto-generated) — "Last Generated:
  2026-07-07T14:55:42" predates the B-min core opening (2026-07-16: `sort`/`quotation` maps,
  new constructors, six rules' quotation-boundary opacity) — neither "sort" nor "quotation"
  appears in the 2165-line reference. FIX: rerun `python tools/extract_core_api.py`.
- **docs/UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md** (whole doc, esp. §3) — presents
  `universal_generalization` as a still-to-write scaffold; it's already implemented
  (`src/derived_rules.py:204`, exported in `__all__`) with the exact test described
  (`tests/test_induction_proofs.py:798`, `test_totality_universal`). FIX: add a "✅ BUILT"
  status line.
- **docs/FREEFORM_COMPOSITION_AND_LEARNING.md:300,304** — build-order items 3 ("legible EGI
  diff") and 4 ("Challenge mode") carry no DONE marker unlike steps 0-2 above them; both are
  shipped (`src/egi_diff.py`, `src/challenge_mode.py` + tests). FIX: mark DONE with module names.
- **docs/ALPHA_RELEASE_PLAN.md:78** — self-contradiction: the parenthetical "(Minor staleness
  — `uv sync` missing `--extra web`, '~23 items' — to refresh later.)" is itself stale — build
  step 10 in the same file already records this fix as done, and live ARISBE_FOR_SCHOLARS.md
  has neither issue (verified). FIX: delete the parenthetical.
- **docs/JARGON_AUDIT.md:1** — header "Status: proposal awaiting author sign-off (2026-06-30)"
  contradicts the body's own "Resolved decisions (author, 2026-06-30)" section and GLOSSARY.md's
  confirmed entries for every ⊕-flagged term. FIX: header → "APPLIED (2026-06-30)"; strike the
  after-sign-off checklist.
- **docs/CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md**:
  - :24 claims "Comprehensive Testing (`tests/test_chapter18_*`)" with an itemized results
    table — no such test file exists anywhere in `tests/` (only hit for
    `chapter18_fopl_translation`/`Chapter18FOPLTranslator` in the whole test tree is one comment
    in `tests/test_induction_proofs.py:173`).
  - :113-126,183-188 — specific metrics ("100% success rate," ">95% structural preservation,"
    "100% across EGIF, CGIF, CLIF," "O(n) translation speed") have no backing test suite.
  - FIX: name the real coverage (or state it's untested) instead of a fabricated file-glob +
    results table; remove the ungrounded percentages. *(The :9,204-211 "✅ PRODUCTION READY" /
    "100% Dau Chapter 18 achieved" banner is the same underlying defect read as overclaim —
    see Tier 2(ii) note; it is not treated as a legitimate borderline overclaim, since the
    factual predicate under it is false.)*

## (e) Note
Book-membership recommendations (which recent top-level docs should join the Quarto book)
are a judgment call for the author — see **Tier 2 (iv)**, not Tier 1.

---

# Tier 2 — Judgment (author decision)

## (i) Staleness needing emphasis-rewrite or a code-verified call ("verify-then-fix")

Grouped by doc. Each of these needs prose rewritten to reflect current state, not a
mechanical swap — several share one root cause (the recurring "automated Grapheus /
dynamic M still open" miss, hit 5 times across 4 docs).

**The "automated Grapheus still open" miss (5 instances, 4 docs) —** all false: `src/grapheus.py`
(minimax opponent) and dynamic-M development (`agon_evolution.py`/`model_revision.py`) are both
SHIPPED (CAPABILITY_MAP.md:111).
- docs/GETTING_STARTED.md:193 — "Frontier: the automated Grapheus opponent and a learned
  dynamic M for the contest register."
- docs/GETTING_STARTED.md:304 — same claim repeated in the one-screen persona map table.
- docs/ARISBE_FOR_SCHOLARS.md:108 — "Still not built: the dialogical contest with an automated
  Grapheus" (highest scholarly visibility in the corpus — addressed directly to Pietarinen;
  doc's own "Reviewed: 2026-06-08" predates the ship date).
- docs/arisbe_triad_architecture.md:143 — Agon's "Current status" line names the same three
  items (semantic layer, automated Grapheus, dynamic M) as "deferred frontier" — all shipped.
- docs/arisbe_triad_architecture.md:121 — Agon's "Core functions" list omits the interpretation
  register (peel/materialize/theory_query) entirely.
FIX for all five: drop the stale Grapheus/dynamic-M clause; name the real current frontier
(the 3-LLM-role automated EPG, tropism/attention economy — CLAUDE.md's `agon_llm`/
`attention_economy` bullets) and add a pointer to DOMAIN_ORACLE_AND_M.md for the
interpretation register.

**Correspondence-doc reconciliation:**
- docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md:299, :313-317 — §8.1/§8.2 describe clockwise-hook
  placement as "pending"/"future work," but `src/clockwise_placement.py`'s
  `place_clockwise_hooks` is wired into `layout_service.py` and EXACT_CORRESPONDENCE.md §3c
  documents it **Done (2026-06-10)**. FIX: reconcile both docs' "pending" vs "done" framing in
  one wave, citing EXACT_CORRESPONDENCE.md §3c.
- docs/EXACT_CORRESPONDENCE.md:101 — "Phase 1... *In progress*" though Phases 2-4 (dated Done
  2026-06-10) structurally depend on Phase 1's machinery, which `presentation_ops.py` already
  implements (`cut_boundary`, `point_in_cut`, `bounds_in_cut`). FIX: mark Phase 1 Done or name
  the specific open sub-piece.

**UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md** (multiple):
- :759-761 footer "Last Updated: 2025-10-14... Next Steps: Model refactoring" directly
  contradicts the doc's own :610 note ("this roadmap is largely realized"). FIX: delete/rewrite
  the stale footer.
- :661-686 "Success Criteria" checklist entirely unchecked though the body confirms most items
  done. FIX: check off completed items or replace with a pointer to CAPABILITY_MAP.md.
- :235-240 — Graphist/Grapheus polarity assignment (see EPG-role section below).

**DAG_HISTORY_ARCHITECTURE.md:302-309** — "Future Enhancements" lists branch labels/colors/diff
views as not-yet-built; `chain_branches.py` already ships branch orientation (⑂ chip strip,
per-branch counters, 2026-07-16). FIX: move shipped items out of "Future Enhancements."

**docs/LEVEL_ZERO_AND_THE_REGISTERS.md:190-207 (§5)** — states M sits at odd depth in the scroll
(pre-"second relocation" picture); M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md §9 (ratified
2026-07-16) relocated M's standing residence to even-depth cells. No forward pointer exists.
FIX: add a note distinguishing the single-episode scroll antecedent from the corpus-standing
residence, with a forward link.

**SECOND_ORDER_FRONTIER.md:176-219** — the "toe in the water" section + closing paragraph frame
the second-order crossing as unresolved reconnaissance; Stage ⓪ + B-min already shipped
(`quotation_overlay.py`, `egi_core_dau.py` sort/quotation maps, S3 CHECKED — CAPABILITY_MAP.md
rows). FIX: rewrite to record Stage ⓪/B-min as shipped, cite CROSSING_DECISION_BRIEFS.md's
ratified verdicts, re-scope the open frontier to B-full only. (MODALITY_WITHOUT_GAMMA.md:413-418
carries the same root-cause echo but explicitly defers to this doc — no separate fix needed there.)

**FIDELITY_AND_DEPARTURES.md**:
- :336-338 — Corollary point 5 says the third tense "nominates `(superseded ⌜M⌝ …)` as a
  candidate" — now built as the `swan_third_tense` corpus exemplar. FIX: "is realized by," cite
  `quotation_overlay.py`/CAPABILITY_MAP.md.
- :723 vs :318-338 — footer changelog's last entry (2026-06-22) undercounts real edit history;
  §3b cites 2026-07-15/16 work never logged. FIX: add a changelog entry.

**docs/CAPABILITY_MAP.md:10** — banner "*Last consolidated: 2026-07-02*" undercounts ~3 weeks
of dated rows in the table itself (2026-07-15/16/19). FIX: bump the date or replace with "kept
current — see individual row dates."

**docs/ADVERSARIAL_EXAMINATION.md:1612-1622 vs docs/CONTRIBUTION_AND_PRIOR_ART.md:217-220** — the
exam's own disposition docket (①-⑫) covers Clusters A-D but never records that Cluster E's
Conway's-Life/requisite-variety fixes landed — the exam record is now out of sync with the doc
it audited. FIX: add a one-line disposition note mirroring the "— SUPERSEDED 2026-07-19" pattern
already used elsewhere in the same exam.

**Automated-game docs (cluster E):**
- docs/AUTOMATED_GRAPHEUS.md:1-5 — header still reads "Status: design-of-record (2026-06-12).
  Nothing built yet" in future/proposal tense throughout, but every increment shipped the same
  day (commit `012b2af`: `src/grapheus.py`, contest routes, frontend, the increment-4 warrant
  step) — CAPABILITY_MAP.md:111 independently marks it SHIPPED. FIX: add a "Status: BUILT
  (2026-06-12, same day)" banner, or fold into AUTOMATED_ENDOPOREUTIC_GAME.md's build ledger and
  mark this doc historical.
- docs/AUTOMATED_ENDOPOREUTIC_GAME.md:37,888 — "run 11... is built and awaiting the author's
  launch," contradicted by the same doc's own §12 run-ledger (run 11 executed and disposed,
  F1¹¹ confirmed). FIX: "runs 1-11 executed and disposed."
- docs/AUTOMATED_ENDOPOREUTIC_GAME.md:911 — run 12 row reads "launch pending... play resumes
  07-16," but per git history (`08b7a43`) and `runs/RUN_12_LOG.md` run 12 launched, ran, survived
  16 crashes (already patched on main), and was stopped cleanly 2026-07-20 with full final
  standings (P2¹²/P3¹²/P4¹² all answered). FIX: update the row + add a §11.8 synthesizing the
  disposed findings.
- docs/AUTOMATED_MODEL_DEVELOPMENT.md:224-225 — §9 "Deferred/open" still lists LLM-panel
  negotiation + DAG-branch-on-disagreement as an open question; shipped in `src/agon_llm.py`
  (documented BUILT in the sibling doc's own §5/§9). FIX: one-line pointer instead of leaving it
  listed open.

**docs/PROSPECTS_MULTIPERSPECTIVE.md:20-22** — "R4 remains open" though R4's core deliverable
(`accessible_projection.py`) shipped 2026-07-07, the same date the disposition note carries.
FIX: reword to state the core projection shipped, with only an accessibility-polish residual
open.

**docs/THE_MINIMAL_IN_VIEW_SET.md:574-585** — "the open architectural question... (b), the
reference/transclusion node" still framed as unresolved *immediately after* the doc's own
"Update (2026-06-29)" note says those three decisions are taken (REFERENCE_AND_TRANSCLUSION_NODE.md)
and `reference_node.py` is SHIPPED. FIX: replace with a pointer to the resolved decisions.

**Layout/workflow doc headers self-contradicting their own later sections (cluster G):**
- docs/TENSION_LAYOUT.md:3 — header "design speculation... Not built into the layout path"
  contradicts the same doc's own §8-§11 ("Wired... 2026-06-07," 18/18 corpus attesting).
- docs/TRANSFORMATION_WORKFLOW_SPEC.md:3 — header "not yet implemented" contradicts §5's own
  "All four are now complete."
- docs/ELK_LAYOUT_IMPLEMENTATION_SUMMARY.md (whole doc, esp. "Core ELK Integration"/"Known
  Limitations") — dated 2026-04-01, describes the engine as "395 lines"; it's now 1300 lines
  with substantial later work (ligature-anchor rebuild, tension-order wiring, the bbox
  quick-reject + visibility-graph optimizations) never mentioned.
- docs/ELK_LAYOUT_IMPLEMENTATION_SUMMARY.md:182 — "No incremental layout" limitation superseded
  by TRANSFORMATION_WORKFLOW_SPEC.md's ④a (pin-and-place, shipped 2026-06-06) and the tension
  engine.
FIX (all four): update header status lines / retitle as explicit historical snapshots with a
forward pointer, per the pattern each doc's own later sections already establish.

**docs/RETURN_TO_DEVELOPMENT.md:84-87** — "Agon shipped as a thin V1 arena 2026-06-01... next
frontier is deepening Agon" badly undersells current Agon capability (interpretation register,
model materialization, the LLM-driven EPG, meta-learning, live runners). This is the 5-minute
context-recovery doc — a returning reader would materially misjudge project status. FIX: drop
the stale snapshot, point to CAPABILITY_MAP.md/ROADMAP.md instead.

**docs/RETURN_TO_DEVELOPMENT.md:80-81** — "Rule-reversibility and closure-idempotence property
tests are still to be written (carried forward from issue #4 into issue #8)" — flagged
verify-then-fix rather than assumed stale; confirm issue #4/#8 status before editing.

**docs/ARISBE_EXISTENTIAL_GRAPH_DEFINITION.md** (whole doc) — undated early-vision doc describing
a never-built-as-designed 4-phase strategy and an `ArisbeExistentialGraph` dataclass, at odds
with CLAUDE.md's current Ergasterion role. Referenced only from ALPHA_RELEASE_PLAN.md and the
sweep plan itself. FIX: author call — archive with a banner pointing to VISION_AND_SCOPE.md +
CAPABILITY_MAP.md, or add a status banner if any part is still meant as live.

**docs/ALPHA_RELEASE_PLAN.md:110-111** — closing tally ("~31 BOOK... 7 ARCHIVE... 1 RETIRE") is
a 2026-06-30/07-02 snapshot; `docs/_quarto.yml` today lists ~41 chapters. FIX: label explicitly
as a point-in-time snapshot at alpha-close.

## (ii) Overclaim — borderline check

**Finding: no illegitimate borderline overclaims survived.** Every cluster that checked this
dimension confirmed the FIDELITY/EXAMINATION "final opinion" / convergence discussions
(ADVERSARIAL_EXAMINATION.md, FIDELITY_AND_DEPARTURES.md, FIDELITY_A_PLAIN_ACCOUNT.md,
ENDOPOREUTIC_GAME_GUIDE.md's "Against Convergence" section) are **legitimate critique of
Peirce's own doctrine** (concluding there is *no* fixed terminus — consistent with the ratified
Departure I), not an asserted terminus in Arisbe's own voice — record this explicitly as a
non-finding so a future pass doesn't re-flag the same twelve "final"-family hits the pre-pass
already enumerated. The one real overclaim in the whole sweep
(CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md's "✅ PRODUCTION READY"/"100% Dau Chapter 18") is
**not borderline** — it rests on a fabricated test suite (Tier 1(d)) and is filed there.
UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md:738-755's closing rhetoric is filed under Tier 1(c) (one
of the 3 workstream-A Minors) since it's a clear-cut tone mismatch, not a borderline call.

## (iii) EPG-role harmonized vision — the flagship (author decision OQB2)

**Canonical seat:** `docs/THE_COMMENS_AND_THE_COMMUNITY.md` §3 (the three roles as a
good-regulator *model* of the institution of inquiry — proposer/defender/judge, model-of never
instance-of) + CLAUDE.md's `agon_llm` bullet (`LLMGraphist` Stage-1 doubt-proposer /
`LLMGrapheus` Stage-2 disposition-voter / `LLMAgonothetes` Stage-3 judge that resolves votes or
forks the DAG).

**Proposed one-paragraph-per-role canonical description** (for author confirm/edit):

> **Graphist — the proposer.** Voices the doubt that drives inquiry: scribes a candidate graph
> G that stresses or extends the standing model M. In the classical two-player transformation
> game the Graphist *defends the proposal*, working negative (odd-depth) areas with
> INS/IT+/DC+; in the automated model-development game (`LLMGraphist`, `agon_llm.py` Stage 1)
> the Graphist's motive is named directly as *doubt* — it reads M's thin spots and proposes what
> stresses it. Both readings agree on the constant: Graphist is the source of variation, the one
> who puts a new sign forward to be tested. (Aliases across the corpus: Proposer, Utterer,
> Encoder, Speaker, Myself/Verifier, Representamen.)
>
> **Grapheus — the model-side.** Two distinct functions share this name and must be told apart.
> *Grapheus-the-tester* is the mechanical peel/semantic-game evaluator — Nature, Falsifier,
> Skeptic — that tests G against M at positive (even-depth) areas, picking conjuncts and ligature
> individuals ("refers to anything there may be"), winning when G's positive content fails to
> map; this function is always mechanical and incorruptible, and some docs (e.g.
> AUTOMATED_MODEL_DEVELOPMENT.md) name it "the Skeptic"/"the referee" precisely to keep it
> separate from the second function. *Grapheus-the-defender* is the arguing role Stage 2 of the
> automated EPG reifies as `LLMGrapheus` (`agon_llm.py`) — given the verdict, it votes the
> *minimal* revision that conserves M's coherence, and that vote must actually apply and
> re-peel before it counts (reduce-to-artifact). Both functions are properly "Grapheus": the
> tester decides truth-in-M; the defender decides how M should give ground when truth-in-M says
> no. (Aliases: Skeptic, Interpreter, Decoder, Listener, Nature/Falsifier, Object.)
>
> **Agonothetes — the judge, the game's interpretant.** Named for the ἀγωνοθέτης who organized
> Greek contests without competing — set the terms, oversaw play, declared what the outcome
> meant. Structurally the Peircean Interpretant to Graphist's Representamen and Grapheus's
> Object: the function that turns a boolean/three-valued verdict into a disposition that changes
> the standing record (a theorem registered, a model revised, a hypothesis held, a challenge
> mounted). This is a *function*, not necessarily a body: in hot-seat human play, the human plays
> it after the contest concludes, wearing a second hat; in the tutor loop it narrows to "the
> calculus as referee" (`same_graph`/`legible_diff`); in the fully automated game (Stage 3,
> `LLMAgonothetes`) it is *reified* as an active third role — a panel of policy-agents voting a
> disposition by priority, or a single judge choosing among the votes cast (never fabricating a
> disposition, never overruling the verdict) and, on irreducible disagreement, **branching the
> diachronic DAG** rather than forcing a resolution.

**The real tension, flagged for the author:** is the Agonothetes "not a player / the game's
interpretant" (`GLOSSARY.md:233-234`, `arisbe_triad_architecture.md:131` — "not a third player
but the telic function") or "an active third role that judges and branches"
(`CAPABILITY_MAP.md:162` "Three LLM roles"; `agon_llm.py`'s `LLMAgonothetes`)? **Proposed
reconciliation** (as drafted into the paragraph above): it is the interpretant *function*
always — in ordinary hot-seat/tutor play that function has no independent body, so "not a
player" is the accurate description; in the automated game the same function is *reified* as an
active agent so it can operate without a human occupying the seat. Both statements are true of
different registers of the same game; the fix is to make each doc that states one half say so
explicitly rather than reading as a flat contradiction.

**Docs currently diverging from this account (file:line — the propagation list once the author
confirms/edits the paragraph above):**

1. `docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md:235-240` — assigns Graphist=Defender/attacked,
   Grapheus=Challenger/attacker — the *opposite* polarity from the automated-game frame (Graphist
   attacks/doubts M, Grapheus defends M). Reconciled by: Graphist always defends *its own
   proposal G*; which party is said to "attack" depends on whether the sentence is about G (the
   Graphist defends G against Grapheus-the-tester) or about M (in model-development framing,
   Grapheus-the-defender resists the Graphist's doubt on M's behalf). Needs the disambiguating
   note, not a rewrite of the facts.
2. `docs/GLOSSARY.md:233-234` — states Agonothetes is "not a third player" with no acknowledgment
   that the automated game reifies it as one. Needs the reconciliation clause.
3. `docs/CAPABILITY_MAP.md:162` — "Three LLM roles (Graphist/Grapheus/Agonothetes)... SHIPPED" —
   correct for the automated game, but should cross-reference GLOSSARY's "not a player" framing
   so the two don't read as contradicting each other.
4. `docs/AUTOMATED_GRAPHEUS.md:29-30,66-105,216-244` — Graphist=the human (Myself/Verifier),
   Grapheus=the machine (Nature/Falsifier, merging tester+arbiter into one), Agonothetes=the same
   human wearing a second hat afterward. The sharpest 3-way variance in the corpus. Needs an
   explicit note naming which register (hot-seat human-vs-machine contest) this document
   describes, distinct from the fully-automated 3-LLM-agent register.
5. `docs/AUTOMATED_MODEL_DEVELOPMENT.md:107-127,207` — never uses "Grapheus" at all; names the
   mechanical peel "the Skeptic"/"incorruptible referee" and describes "the Agonothetes panel" as
   fundamentally *plural* (several policy-agents voting, "where emergence lives"). Needs a
   bridging footnote: Skeptic = Grapheus-the-tester; the panel = the reified Agonothetes.
6. `docs/AUTOMATED_ENDOPOREUTIC_GAME.md:69-105,556-595` — both Graphist *and* Grapheus are LLM
   agents, and the mechanical truth-arbiter is a *third*, separate thing called "the referee"
   (never named Grapheus) — sharply different from AUTOMATED_GRAPHEUS.md's assignment (#4).
   Needs the same bridging note: "the referee" here = Grapheus-the-tester, kept lexically
   distinct from Grapheus-the-defender (`LLMGrapheus`) for clarity, not a different entity.
7. `docs/DOMAIN_ORACLE_AND_M.md:136` — attributes choosing M (the opening move) to "an
   Agonothetes/Grapheus act," an ambiguous dual attribution; `ENDOPOREUTIC_GAME_GUIDE.md:691-697`
   gives a *third* attribution ("the Graphist and Grapheus agree on M"). Three different
   attributions for one function across two docs. Needs settling — recommend: M-selection is the
   Agonothetes' context-setting function (its "before the game" phase per
   ENDOPOREUTIC_GAME_GUIDE.md), with Graphist/Grapheus proposing candidates the Agonothetes ratifies.
8. `docs/TUTOR_LOOP.md:85-95` — casts "the calculus as referee" for the judge seat rather than
   naming Agonothetes at all. Consistent with the reconciliation above (a narrower, purely
   mechanical occupant of the same seat) but should say so explicitly rather than leaving the
   reader to infer the mapping.
9. `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md:285` — casts "the world" as a "more generic
   Grapheus" at project-vs-world scale, with no Agonothetes named (judged role diffused into
   "the record disposes"). Needs reconciliation with THE_COMMENS_AND_THE_COMMUNITY.md §3's
   "model of, never instance of" framing — is a project-scale game still *a model of* inquiry,
   or does the outer game genuinely lack a judge function? Author call.
10. `docs/FIDELITY_ENDOPOREUTIC_CHECK.md:55-58` — a fourth independent restatement (via
    Pietarinen 2005): Graphist="utterer... the verifier," Grapheus="interpreter... authorises the
    modifications," Agonothetes="the judge" (§3.4). Not contradictory, but should cross-reference
    the harmonized account as its scholarly citation rather than standing alone.

**Not divergent — additive/consistent, feed the canonical paragraph but need no fix:**
`docs/ENDOPOREUTIC_GAME_GUIDE.md` (by far the richest source — alias lists, the semiotic-triad +
etymology, the three-phase functional account, the temporal/quasi-mind readings — all
compatible, differing in depth not substance; good candidate to host the full harmonized
account with a link back to THE_COMMENS_AND_THE_COMMUNITY.md §3), `docs/arisbe_triad_architecture.md`
(consistent, contributes the polarity-by-area detail), `docs/ARISBE_FOR_SCHOLARS.md` (consistent,
ties Agonothetes to the disposition taxonomy), `docs/GETTING_STARTED.md`,
`docs/ARISBE_IN_PRACTICE.md`, `docs/GENERATION_AND_TESTING.md` (contributes the
judgment-not-function-of-verdict worked contrast), `docs/NL_TO_LOGIC.md`,
`docs/WEB_VIEWER_DESIGN.md:54` (pure UI color-token mention only).

**Vocabulary-drift companion finding:** `docs/ENDOPOREUTIC_GAME_GUIDE.md:2115-2116` describes the
Agonothetes as representing "the Commens — the community that realizes interpretation,"
conflating the in-UoD Agonothetes with the settled, outside-the-membrane `commens` doctrine
(THE_COMMENS_AND_THE_COMMUNITY.md). FIX: drop the parenthetical identification, or rephrase so
the Agonothetes *draws on* commens-level standards rather than *being* the commens.

**Propagation count: 10 docs** carry an explicit divergence/tension requiring the harmonized
paragraph (or its reconciliation clause) once the author confirms/edits it.

## (iv) Book-membership recommendation

None of the five candidates appear in `docs/_quarto.yml` today (verified directly). All five
are corpus-load-bearing design-of-record docs actively cited by CLAUDE.md and cross-referenced
from book chapters already in the ToC (e.g. cluster F used three of them as *canonical ground
truth* for vocabulary/EPG-role auditing across the whole sweep — a strong signal they're already
functioning as spine documents):

- **docs/THE_COMMENS_AND_THE_COMMUNITY.md** — recommend: **add.** It is the canonical seat for
  the EPG-role harmonization this docket just built (§3); leaving the canonical frame out of the
  book while book chapters (ENDOPOREUTIC_GAME_GUIDE, FIDELITY docs) reference it is backwards.
- **docs/THE_KYTOS.md** — recommend: **add.** Ratified 2026-07-19 as "the semiotic cell," the
  named cross-scale anatomy CLAUDE.md treats as a top-level concept; used as canonical ground
  truth in this very sweep.
- **docs/THE_MEASURE_OF_KNOWLEDGE.md** — recommend: **add.** Defines the K1-K4 measure now
  referenced throughout CLAUDE.md's module bullets (K2/K3/K4 all cite it); a reader of the book
  hits "K3" and "materialization_ratio" with no chapter to look it up in.
- **docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md** — recommend: **add**, though it is more actively
  in flux (rung-1/rung-2 staging, open author decisions in its own §5) — note this to the author
  as the one candidate where "add now" vs "add once rung 2 settles" is a real choice.
- **docs/TUTOR_LOOP.md** — recommend: **hold**, or add clearly marked "design-only, unauthorized
  build" (its own header already says this). It's forward-looking design-of-record rather than a
  built capability; the other four candidates describe or ground what exists today. Author rules.

Author decision requested on all five (add-now / add-with-banner / hold).

## (v) Readability nits

- `docs/FIDELITY_AND_DEPARTURES.md:392,402` — bare "§2's crux," "the §7 second-order residue,"
  "the §1 provability/trajectory reading" all refer to MODALITY_WITHOUT_GAMMA.md's own sections,
  violating the house convention (GLOSSARY.md "Notation & reference numbers": name the target
  document). FIX: "MODALITY_WITHOUT_GAMMA §2's crux," etc.
- `docs/ADVERSARIAL_EXAMINATION.md:82,94,133,149` — several bare "§4"/"§7"/"§1"/"§2" pointing
  into LEVEL_ZERO_AND_THE_REGISTERS.md/MODALITY_WITHOUT_GAMMA.md without naming the target.
  FIX: add a notation key near the top of the Departure I-III examination (Examination IV's own
  preface already sets this precedent), or name the doc at first use per department.
- `docs/EXEMPLARS.md:270` — bare "§8.1" (target: M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md §8.1,
  not named nearby, unlike the doc's other cross-refs). FIX: name the target doc.
- `docs/GAMMA_DEMONSTRATIONS.md:163-164,171-173` — bare "§5"/"§7"/"§2"/"§3" referring to
  MODALITY_WITHOUT_GAMMA.md's sections, while this doc has its own numbered "## 2"/"## 5"/"## 7"
  headings — genuine misresolution risk. FIX: name the target doc each time.
- `docs/ALPHA_RELEASE_PLAN.md:156` — bare "the VISION §7 diagram." FIX: "VISION_AND_SCOPE.md §7."
- `docs/GETTING_STARTED.md:24-25` / `docs/ARISBE_IN_PRACTICE.md:26-27` /
  `docs/ARISBE_FOR_SCHOLARS.md:12-13` — all three book chapters open with the identical
  verbatim sentence (also matching CLAUDE.md's "What This Project Is"). Low severity — likely
  intentional (each on-ramp doc must stand alone). FIX: none needed if the "standalone door"
  design is confirmed intentional; otherwise vary per chapter.

---

# Counts summary

**By dimension** (raw finding count, not counting the ~15 EPG-role "component capture" items
that carry no severity/fix and are informational harmonization material only):

| Dimension | Count |
|---|---|
| Staleness | 47 |
| Named-entity (EPG roles, with severity) | 5 |
| Vocabulary drift | 3 |
| Dedup | 2 |
| Overclaim | 2 (1 real — Tier 1(d); 1 tone-mismatch — Tier 1(c)) |
| Readability | 8 |
| Dead-refs | 0 |
| **Total findings with severity** | **67** |
| EPG-role components (informational, no severity — harmonization raw material) | ~19 |

**By tier:**
- Tier 1 (mechanical): batch (a) 0, (b) 2, (c) 4, (d) 20 → **26 findings**, all clear
  factual/count/nonexistent-reference fixes.
- Tier 2 (judgment): (i) staleness/emphasis 27, (ii) overclaim-borderline 0 real findings (a
  clean-bill note), (iii) EPG-role harmonization (1 flagship item, 10 propagation targets),
  (iv) book-membership (5 candidates), (v) readability 6 → **≈41 findings** (excluding the
  EPG-role component-capture items, tracked separately as harmonization inputs, not defects).

**By severity** (C=Critical/staleness-that-misleads-a-reader-badly, I=Important, M=Minor):
- Critical (C): 13 (the 5 "automated Grapheus still open" instances + CHAPTER18 fabricated-test
  claim + CORE_API_USAGE_GUIDE's 4 signature/count breaks + AUTOMATED_GRAPHEUS.md header +
  ELK_LAYOUT_IMPLEMENTATION_SUMMARY whole-doc + RETURN_TO_DEVELOPMENT Agon-undersell)
- Important (I): ~40
- Minor (M): ~14

---

# Coverage

All 87 top-level docs audited across 8 clusters (DEEP tier for the 41 Quarto book chapters in
clusters A-D, LIGHT tier — staleness/named-entity/vocabulary/dead-refs — for the 46 non-book
docs in clusters E-H). Fully clean on every in-scope dimension (no findings anywhere in their
cluster's report):

**DEEP-tier clean:** SOUNDNESS_BOUNDARY.md, PERFORMANCE_ENVELOPE.md, CHAIN_OF_SEMIOSIS.md,
MANIFEST_AND_MEANING.md, MEANING_BY_HISTORY.md (cluster A); FIDELITY_A_PLAIN_ACCOUNT.md
(cluster B); FIELD_GUIDE_AND_DRAGONS.md, TEACHING_PACK.md, TROUBLESHOOTING.md,
DEPLOYMENT_AND_MULTIUSER.md, FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md (cluster D).

**LIGHT-tier clean:** M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md, CATEGORIES_AND_THE_THREE_PARTS.md
(cluster E, on vocabulary/named-entity — staleness not in LIGHT scope for these two beyond what's
reported); THE_KYTOS.md, RATE_AND_INTELLIGIBILITY.md, MATHEMATICS_FROM_THE_SHEET.md,
MATH_FIXTURES_ZFC_PEIRCE_1881.md, PRODUCT_VISION.md (cluster F); PRESENTATION_DELTAS_AND_STYLE.md,
UI_TRANSPARENCY_CHARTER.md, COMPOSITION_WORKFLOW_SPEC.md, ROADMAP.md (cluster G); DEFINITION_NODE.md,
REFERENCE_AND_TRANSCLUSION_NODE.md, SCHEMA_HOLE_CORRESPONDENCE.md, CORRESPONDENCE_CONTRACT.md,
MCP_VERIFIER.md, PROOF_SERIALIZER.md, CORPUS_AND_IMPORT_MODEL.md, ALPHA_BETA_UX_DOCKET.md,
STORM_DOCS_AUDIT.md (cluster H).

Every other doc surfaced at least one Tier 1 or Tier 2 item above.
