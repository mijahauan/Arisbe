# Calculus conformance and certified soundness

**Date:** 2026-11-25 · **Status:** Phases 0–2 built 2026-11-25 (§3.1 note, §3.3a, §3.3b); Phase 3 waits on R2 · **Rulings:** R1, R3–R8 ruled 2026-11-25, R7 amended the same day (CONSTANT_IDENTITY in scope, §4.4); R2 open (§7)
**Companions:** [2026-11-11-reassessment.md](2026-11-11-reassessment.md) ·
[2026-09-10-calculus-property-suite-design.md](2026-09-10-calculus-property-suite-design.md) ·
`tests/calculus_ledger.json` · `tests/calculus_rules.py` · `tests/calculus_expected.py`

> **How this was written.** Drafted by Claude (Opus, claude.ai session linked to this checkout) at
> HEAD `655a88c`, from the ledger's own recorded reasons and measurements, the engine source and the
> suite's oracle modules. Every Dau citation below is the one the ledger or the code already
> carries; **none was re-read from the book for this document.** The seven PROVISIONAL readings are
> exactly where that matters, and they are the author's to confirm against Dau (§7). Treat every
> file:line claim as a claim until the implementing session reproduces it (standing caution 5).

---

## 1. What the author ruled (2026-11-25)

1. **Conform or annotate.** Every place the engine differs from Dau's calculus is either brought
   into conformance or annotated precisely — how, where, and why it differs.
2. **Provably sound, by certificate.** Every applied inferential move carries a derivation
   certificate — the sequence of Dau's primitive rule applications it amounts to — checked at
   runtime by an independent kernel. Soundness of every recorded history then follows from Dau's
   soundness theorem plus the correctness of a small, auditable kernel. A full mechanization (Lean
   or Coq) is the later, stronger step (§9); the certificate format is its interface.
3. **Fused steps become discrete steps.** Where the engine performs two of Dau's steps as one, it
   will perform them as two, each recorded. A convenience that wants the fused effect becomes a
   named derived rule whose record holds the discrete steps — never an opaque primitive.
4. **No outreach until this is done** (§8 defines done).

## 2. Where the calculus stands

The ledger holds 17 entries. They are of three kinds, and the distinction governs everything below.

**Truth-losing moves: none known.** The unsound moves September found (iteration, deiteration, the
ligature rules) were fixed in September. The one soundness-layer entry,
`vertex-era-erases-a-line-not-an-equivalence`, records a move that is sound but one-way where Dau's
vertex rule is an equivalence: G ⊨ G′ on all 1,910 exhaustive moves, G′ ⊭ G.

**The engine performs a move other than the one named: seven entries.** Three are classed SEVERE
in the refusal layer (`dc-plus-ignores-target`, `era-auto-closes-a-vertex-selection`,
`vertex-era-erases-a-line-with-its-edges`), three DIFFERS in the structure layer
(`era-also-erases-the-vertex-it-isolates`, `it-plus-auto-closes-a-vertex-selection`,
`it-plus-reuses-a-selected-vertex-in-a-deeper-context`), and the soundness entry above. In every
measured case the move performed is Dau-licensed or equivalent to a Dau derivation; in none is it
the move named. These seven are exactly the ledger's PROVISIONAL entries — the readings awaiting the
author. (The 2026-11-11 consistency audit counted eight; the ledger holds seven.)

**The engine refuses what Dau allows: ten entries,** plus five rules with no entry point at all
(`ORIENT_IDENTITY`, `LIGATURE_VERTEX`, `CONSTANT_IDENTITY`, `CONSTANT_EXISTENCE`,
`SEPARATE_CONSTANT`). These make the engine incomplete, never unsound.

The evidence for all of this is the bounded exhaustive suite (2,382 tier-A graphs, 133 tier-B, 10
tier-S) and semantic checks at domain sizes 1–2. That is strong evidence and not a proof — which is
what §3 supplies.

## 3. The certificate architecture

### 3.1 The kernel

Promote the suite's oracle into `src/dau_kernel.py`: `legal()` and its helpers (`expand`, `tops`,
`theta`, the copy search behind `_it_minus`) from `tests/calculus_rules.py`; the licensed results
(`acceptable`, the reference constructors `remove`, `insert`, `double_cut`, `erase_double_cut`,
`add_vertex`, `iterate`) and `postconditions` from `tests/calculus_expected.py`. The tests then
import the kernel rather than owning it.

The property that made the oracle worth having must survive the move, and it must be enforced by a
test, not by prose: **the kernel imports no engine module.** Its permitted imports are the data
model (`egi_core_dau`), `eg_navigation.same_graph`, and `egif_parser_dau` (for INS content only).
Those four modules are the **trusted base**. The rule engine, the interaction protocol, the closure
analyser, the ligature engine, the layout and the UI are outside it.

> **Measured in Phase 1 (2026-11-25): the three named modules are not closed under import, so the
> trusted base is larger than this paragraph says.** Read from the imports by
> `tests/test_dau_kernel.py`, which pins the result:
>
> - *loaded when the kernel is imported:* `presentation_ops` and `layout_dto`, because
>   `eg_navigation` imports them at its top — so "the layout is outside it" does not hold of the
>   layout's data types;
> - *reached by calls the kernel makes:* `hierarchical_index` (every graph builds one) and
>   `graph_isomorphism_engine` with `canonical_signature` — `same_graph` is that engine's verdict,
>   so it is where "the result is a licensed one" is decided. `formal_transformation_rules` and
>   `rule_interaction` import that same isomorphism engine, so the judge and the judged share it;
> - *reachable through functions the kernel does not call:* `subgraph_closure_validator` (the
>   closure analyser, from `eg_navigation`) and `render_geometry` (from `presentation_ops`).
>
> No rule-engine module is in that closure, and the same test holds that. Whether the kernel should
> take `same_graph` by a shorter road (from `graph_isomorphism_engine` directly, shedding
> `eg_navigation`, `presentation_ops`, `layout_dto`, `render_geometry` and the closure analyser) is
> the author's ruling; Phase 1 moved the oracle unchanged and did not take it.
>
> **Ruled 2026-11-25: yes.** The kernel asks `graph_isomorphism_engine` directly. Its permitted
> imports are now `egi_core_dau`, `graph_isomorphism_engine` and `egif_parser_dau`, and the
> **trusted base is five modules of this repository**: those three, `hierarchical_index` and
> `canonical_signature` (both imported inside functions), with `networkx` and `frozendict` from
> outside it. This supersedes the paragraph above the note where the two differ. The judge and
> the judged still share the isomorphism engine; that is disclosed, not removed. Phase 5's
> trusted-base document lists these five.

### 3.2 The certificate

A certificate is a list of primitive steps `(rule, selection, target, content, hooks)`, each
applied to the graph the previous one produced. The kernel accepts step *i* iff
`legal(gᵢ, stepᵢ)` holds **and** `gᵢ₊₁` is `same_graph` to one of the kernel's licensed results
for that step (for the four ligature rules, split and merge, where no licensed result is built:
iff `postconditions(gᵢ, stepᵢ, gᵢ₊₁)` is empty). A primitive move's certificate has one step; a
derived rule's has its expansion. The rule named in each step is the Dau rule, by its table name —
so erasing an isolated *constant* vertex names `CONSTANT_EXISTENCE` (Def 24.10), not `VERTEX_ERA`.

### 3.3 One choke point

Every path that changes a graph by inference goes through one function —
`certify(g, act) -> (g′, certificate)` — which raises `CalculusViolation` (modelled on
`CorrespondenceViolation`, `src/correspondence_attestation.py:50`) when the kernel rejects a step.
Today the calculus is reached from at least `rule_interaction.apply_interaction`,
`FormalTransformationEngine.apply_rule`, `LigatureManipulationEngine.apply_rule`, the split/merge
classes, `proof_authoring.apply_rule`, `derived_rules`, `world_scroll`, `model_acts`,
`contest_context` and `endoporeutic_game`. The implementing session enumerates them all (graphify
`path`, then grep) and routes each through `certify`; a test asserts that no engine entry point is
reachable from a route or a UoD writer except through it.

The certificate is stored with the step in the UoD's history. On load, certificates are re-checked
by the kernel. Engine replay (`proof_authoring.replay_step`) stays as a reproducibility check; it is
no longer the soundness evidence, because it trusts the engine it replays.

### 3.3a The map of paths (Phase 0, 2026-11-25)

> **How this was made.** At HEAD `af3abb5`, whose code is `655a88c`'s. The knowledge graph was
> asked first and gave a thin answer: it holds the `calls` edges for plain function calls and
> misses method calls such as `_engine.apply_rule(...)`, so `routes/transformations.py` — a
> production route straight into the engine — was absent from its list. The map below comes from
> an AST scan of every call in `src/` and `tools/` that names an
> engine entry point, repeated one level up for the wrappers, then read at each site. Line numbers
> are from that scan. Three findings were reproduced by hand on small graphs and say so; the rest
> are read, not run.

**Where a rule's transformation is performed.** Four modules, and nothing else in `src/`
subclasses `FormalTransformationRule`:

| Module | What it holds |
|---|---|
| `formal_transformation_rules.py` | seven rule classes (DC+, DC−, INS, ERA, IT+, IT−, HEAVY_DOT) and `FormalTransformationEngine` |
| `rule_interaction.py` | six interactions (the protocol), `insert_from_egif`, `apply_interaction` |
| `ligature_manipulation_rules.py` | four rule classes and `LigatureManipulationEngine` |
| `vertex_splitting_merging_rules.py` | `VertexSplittingRule`, `VertexMergingRule` |

**The five ways in.** Everything outside those four modules reaches them by one of these:

| # | Way in | Who calls it |
|---|---|---|
| 1 | **The protocol** — `apply_interaction` → `RuleInteraction.apply` → the rule's `apply_transformation` (INS → `insert_from_egif`) | `proof_authoring.apply_rule` (`:75–99`); the workshop route `POST /ergasterion/sessions/{id}/apply` (`routes/ergasterion.py:1448–1467`); its dry run `rule-check` (`:1583–1591`) |
| 2 | **The engine** — `FormalTransformationEngine.apply_rule`, which builds a context and calls the rule with no protocol step | `POST /api/transform/apply` (`routes/transformations.py:248`, the six rules; HEAVY_DOT is not offered); `derived_rules.universal_generalization` (`:265`, HEAVY_DOT only) |
| 3 | **A rule class directly** — `rule.apply_transformation(context)` | `EndoporeuticGame.apply_move` (`endoporeutic_game.py:345`; INS by `insert_from_egif`, `:333`), behind its own permission check, reached from `POST /agon/games/{id}/move`. Also two evaluators, `chapter17_soundness_evaluation.py:142` and `z3_semantic_validator.py:324`, which nothing imports but each other |
| 4 | **The unchecked split and merge** — `VertexMergingRule()._apply_vertex_merge`, `VertexSplittingRule()._apply_vertex_split`, the private operations that perform the change and check nothing | `derived_rules.py:93`, `:144` (merge), `:194` (split); `world_scroll.py:494` (merge). The *checked* entry points — `merge_vertices` and the two `apply_transformation`s — have no caller in `src/` |
| 5 | **The ligature engine** — `LigatureManipulationEngine.apply_rule` | nobody in `src/` or `tools/`. Its four rules run only under `tests/calculus_apply.py` |

**What the calculus suite drives, against that list.** `tests/calculus_apply.py` reaches the six
rules, INS_EDGE and VERTEX_ERA by way 1, VERTEX_INS by way 2, the ligature rules by way 5, split
by the unchecked private operation and merge by the checked `merge_vertices`. So ways 2 and 3 for
the six rules, and the unchecked merge of way 4, are in production and outside the suite. The
ledger's entries describe way 1.

**The wrappers over `proof_authoring.apply_rule`.** Every one of these goes through way 1:

| Wrapper | Rules it applies | Its own callers |
|---|---|---|
| `ProofChain.apply` (`proof_authoring.py:231`) | any of the six, recorded as a `ChainStep` | `agon_evolution.run` (`:662`, `:668`), `revision_episode.exhibit_conflict` (`:151–177`); 23 scripts in `tools/` build chains through `ProofChain` (22 `build_*.py` and `run_vault_v0.py`) |
| `replay_step` (`:113`) | the step's recorded rule | `composition_ops.verify_chain_replay` only — which no module in `src/` calls |
| `contest_context` — `open_arena`, `posit`, `carry_in` | DC+, INS, IT+ | `world_scroll.wrap_m`, `wrap_state`, `withdraw_and_resupply`; `deliberate` |
| `world_scroll` — `enlarge_m`, `retract_from_m`, `entertain_episode`, `discharge_episode`, `abandon_episode`, `withdraw_and_resupply` | INS · ERA · DC+ IT+ INS · IT− IT− DC− · ERA · ERA DC+ INS | `m_steps` (the eight step recorders), `model_revision.revise_with_disposition_recorded`, `live_runner` (`:479`, `:667`), `oracle_notes.bank_answer`, `notion_provenance`, `west_coordinator` |
| `derived_rules` — `universal_instantiation`, `instantiate_to_lines`, `existential_generalization`, `universal_generalization` | IT+ · (none) · ERA · DC+ IT+, each with way 2 or way 4 beside it | `revision_episode` (`:147`, `:160`); `tools/build_barbara_chain.py`, `tools/build_group_identity_chain.py` |
| `model_acts` — `relinquish`, `admit_by_discharge` | ERA · IT− DC− | none in `src/` |
| `mcp_verifier.apply_rule`, `validate_step` | any of the six, on a graph parsed from text; stateless | `mcp_server` (two tools) |

**Where a changed graph is written down.** Four stores, each with its own record shape:

- `ProofChain` → `TransformationChain` → `TomosService.save_uod_with_chain`, called from
  `live_runner.py:685`, `web_api/services/agonothetes.py:293` and `:474`, and the tools above.
  `ProofChain.apply_derived` records whatever graph a caller's function returns, under whatever
  name the caller gives; its callers are `m_steps`, `agon_evolution` (`REVISE_M`,
  `REVISE_M(sibling)`, `DECAY`), `revision_episode` (`UI`), `quotation_overlay` (`QUOTE`, twice),
  `oracle_notes` (`BANK_TO_M`), `alternative_trace` and `alternative_survey` (identity steps).
- The workshop session — `ErgasterionSessionManager.add_step`, from the apply route and from
  `define-fold`, `define-unfold`, `fix-drawing`, `fix-graph`, `fix-chain` and `compose`.
- The viewer session — `session_manager.update_session`, from `/api/transform/apply`.
- `EGITransformationHistory.add_transformation`, from the game engine (`endoporeutic_game.py:358`).

**No stored chain is replayed when it is loaded.** `replay_step` has the one caller named above,
and nothing in `src/` calls that. Phase 4's "certificates are re-checked on load" is therefore a
new check, with no existing one to strengthen.

**Graph changes that name no rule.** These build the next graph with the data model's own
constructors, or by re-parsing text, and no engine entry point sees them:

| Site | What it does | How it is recorded |
|---|---|---|
| `derived_rules.py:91`, `:142` | scribes an identity edge with `with_edge(…, "=")`, then the unchecked merge. `instantiate_to_lines` first checks the area is negative; `universal_instantiation` checks nothing about the area | inside a `UI` step, or the caller's name |
| `world_scroll._join_admitted_individuals` (`:488–495`), run by every `enlarge_m` | moves the standing constant's vertex outward, scribes `=`, collapses the pair with the unchecked merge. The module says of the collapse that it "is *not* a Def 16.6 merge" and is "not a rule of Dau's" | derivation `["INS"]` |
| `world_scroll.discharge_episode` (`:738`) | `normalize_constants` after the three rule applications | derivation `["IT-", "IT-", "DC-"]` |
| `world_scroll.wrap_state` (`:364–367`) | re-houses a sheet-level M structurally; says so, and asks callers to record `earned: false` | caller's |
| `model_revision` — `assert_fact`, `add_rule` (re-parse of the joined text); `retract_subgraph`, `retract_atom`, `retract_relation` (`without_element`) | the sheet-level fallback for a model not resident in the world-scroll | derivation `[]` |
| `model_acts.assert_into`; `relinquish`'s fallback | juxtaposition onto the sheet; structural removal where ERA's closure refuses | an `Act` with `is_rule=False` |
| `live_runner.py:479` and `:667` | re-supplies a law and decays stale atoms on the model carried between segments | no chain step; the segment digest |
| `definitions.fold`, `expand_at`; `reference_node`; `schema` (all through `eg_splice`) | replaces a subgraph by a defined relation's spot, or the reverse | `definition.fold` / `definition.unfold` steps in the workshop |
| `quotation_overlay` (`:374–500`) | builds and removes the quotation apparatus | `QUOTE` |
| `composition_ops` | regime-1 drafting — not inference, listed so the choke-point test can exempt it by name | `compose.*` |

Two modules infer without changing any recorded graph — `model_materialization` (the Horn closure)
and `theory_query` — and are outside Dau's calculus altogether. They are named here so the
choke-point test does not have to discover them.

**What the corpus records.** 35 chains hold 146 steps (counted from `tomos/**/chain.jsonl`):
PEEL 27 · ADMIT_TO_M 26 · ERA 17 · DC+ 16 · INS 12 · IT− 8 · DC− 8 · QUOTE 5 · REVISE_M 5 ·
IT+ 5 · UI 4 · TRACE_ALTERNATIVES 4 · RETRACT_FROM_M 2 · and one each of ENTERTAIN,
DISCHARGE_TO_M, FOLD_NUMERAL, SURVEY_THIN_SPOTS, SURVEY_BRANCHES, PROPOSE, EXHIBIT. The 80
steps that are not one of the six all carry `derived: true`. 43 of them also carry a
`derivation` — a list of rule names, with no selections or targets, so it cannot be re-applied.
The 4 UI steps carry none.

**Five things this map found that the sections around it do not yet say.** Each is for the author;
none is resolved here.

1. **Two web routes apply the same rule by different ways in, and they disagree.** Reproduced: on
   `(P *x) ~[ (Q *y) ]`, DC+ of the `P` edge with the cut as its spot is *applied* by way 1 (the
   spot ignored — the ledger's `dc-plus-ignores-target`) and *refused* by way 2 ("Selected subgraph
   contains elements not in target area"). On `(P *x) (Q x)`, ERA of the vertex alone gives the
   blank sheet by both. Phase 2's gate — the kernel rejects exactly what the ledger describes and
   nothing else — is a statement about way 1. Ways 2 and 3 have never been measured, so rejections
   there are to be expected and are not, by themselves, the surprise that gate asks to be told about.
2. **DISCHARGE_TO_M does a fourth thing its derivation does not name.** Reproduced: discharging
   `(flies "Rex")` against a cell holding `(bird "Rex")` records `IT-, IT-, DC-`, and then
   `normalize_constants` turns two `Rex` vertices into one — the result is not `same_graph` to
   what the three rules produced. §3.4 classes DISCHARGE_TO_M as inferential-derived, "every step
   kernel-checked". The link between the two vertices is Dau's CONSTANT_IDENTITY, which §4.4
   schedules after this arc; the collapse is, in the module's own words, not Dau's at all. As
   written, §3.4 and §4.4 cannot both hold for this act.
   **Ruled 2026-11-25: CONSTANT_IDENTITY is brought into this arc (R7 as amended, §4.4), and the
   normalisation becomes a recorded expansion.** "Not Dau's at all" was this map's reading of the
   module's docstring before the book was opened; §4.4 now quotes the rule and gives the expansion
   it appears to license.
3. **ADMIT_TO_M's `["INS"]` is likewise not the whole move.** Reproduced: admitting
   `(white "Rex")` beside `(bird "Rex")` by `enlarge_m` yields one `Rex` vertex, moved out of its
   cell to the residence's area; the bare INS yields two, and the two results are not
   `same_graph`. §3.4 asks no certificate of an ampliative act, so nothing breaks — but the
   recorded derivation is one of the things §1's "conform or annotate" covers.
4. **The classification §3.4 adopts is not all in `proof_character.py`.** That module names the six
   rules, the ampliative set, `PEEL`, `QUOTE`, `TRACE_ALTERNATIVES`, `ENTERTAIN`,
   `DISCHARGE_TO_M` and `ABANDON_EPISODE`. It does not mention `UI`, `PROPOSE`, either `SURVEY_*`
   or `EXHIBIT`, and it puts `QUOTE` among the neutral acts where §3.4 makes it an extension.
   Names the code can record that §3.4's table does not list: `EXHIBIT`, `REVISE_M(sibling)`,
   `definition.fold`, `definition.unfold`, `compose.*`, `chain.fix`. Phase 2 has a table to build,
   not one to inherit.
5. **Production merges by the operation that checks nothing.** The three production merge sites and
   the one split use the private `_apply_*` operations; the suite's `MERGE_VERTICES` measures the
   checked `merge_vertices`, which production never calls. Whatever R2 settles about the IT+ split,
   `universal_instantiation`'s join is today an unchecked edge plus an unchecked merge.

### 3.3b What observe mode found (Phase 2, 2026-11-25)

`src/calculus_certify.py` is the door. Every call site in §3.3a's table now goes through it, and
`tests/test_certify_paths.py` fails on a call that performs a rule from anywhere else. The door
wraps the engine from outside, so no calculus-map module was edited. Certificates are computed
and checked; a rejection is counted and nothing is raised.

**The gate holds over the calculus suite.** In the default run 13,257 moves are applied. The
kernel accepts 9,273, rejects 3,869 and leaves 115 unjudged. The rejected instances are exactly
those on which a layer records a SEVERE, DIFFERS or NOT AN EQUIVALENCE failure — every one of them
ledgered — and the 3,869 are the refusal layer's 3,070 SEVERE plus the structure layer's 799
DIFFERS, move for move (`tests/test_calculus_certify.py`). Four rules carry all of them: DC+ 2,542,
ERA 578, IT+ 514, VERTEX_ERA 235. Those per-rule counts are pinned, and each Phase 3 family's gate
is its row falling to zero. All 115 unjudged are the quotation extension (§6): 100 moves that
touch the apparatus and 15 iterations on a quotation-bearing graph, where `legal()` abstains. An
unjudged step is not a certified one.

**The corpus's primitive steps are already conformant.** All 66 of them (DC+ 16, DC− 8, ERA 17,
INS 12, IT+ 5, IT− 8) replay from their recorded source state to their recorded result, and the
kernel accepts each as the Dau move it is recorded as (`tests/test_certify_departures.py`). None
is one of the fused moves the ledger describes. §5 expected the 17 ERA and 5 IT+ steps to need a
legacy expansion; as recorded, they do not. What the kernel cannot check in the corpus is its six
derived inferences (4 UI, ENTERTAIN, DISCHARGE_TO_M), none of which carries an expansion with
selections and targets (`tests/test_act_classes.py`).

**What production's own paths produce.** The whole suite was run with the door in place and its
log on, which records for each certificate the kernel did not accept the caller that asked for the
move. 36,685 certificates: 21,345 accepted, 15,224 rejected, 115 unjudged, and one kernel crash
planted by a test. Outside the calculus suite's own moves, 11,315 were not accepted, and two
callers in `src/` account for all but ten of them: `world_scroll._join_admitted_individuals`
(11,101) and `world_scroll.retract_from_m` (204). The remaining ten come from test code, the MCP
verifier's tests and one dry run.

**Four departures on production's own paths.** The directive: "Any other rejection is a finding:
stop and report it." The ledger describes the suite's moves; these are on roads the suite does
not take. Each is reproduced and pinned by name in `tests/test_certify_departures.py`
(`KNOWN_DEPARTURES`), the counterpart for production paths of the calculus ledger. The first is
a rejection no ledger entry describes; the second and third are gaps no certificate sees; the
fourth is a ledger entry met on a production caller:

1. **`admit-joins-a-named-vertex`** — the one true rejection. `world_scroll._join_admitted_individuals`
   merges the newly admitted constant's vertex into the standing one by the unchecked merge.
   Def 16.6 erases v₂ and Def 24.10 erases no name, so the kernel rejects it — every time a fact
   about a known individual is admitted. The licensed road is CONSTANT_IDENTITY then a merge (§4.4).
2. **`discharge-normalises-constants-unrecorded`** — not a rejection but a gap: the discharge's
   three steps are each certified and accepted, and the graph it returns is not the graph the last
   certificate vouched for. This is the named entry §4.4 said Phase 2 owed.
3. **`ui-scribes-its-identity-edge-by-no-rule`** — the same kind of gap.
   `derived_rules.universal_instantiation` iterates (accepted), adds the joining identity edge with
   the data model's own `with_edge`, then merges (accepted). The edge between the two certificates
   is named by no rule and checked by nothing. `instantiate_to_lines` does the same.
4. **`retract-leans-on-era-erasing-the-vertex-it-isolates`** — `world_scroll.retract_from_m`
   erases an atom by naming its edge alone and relies on ERA also taking the vertex the erasure
   isolates. That is the ledger's own `era-also-erases-the-vertex-it-isolates`. It matters for
   Phase 3 item 2: once ERA removes the edge only, retraction must name the vertex's erasure as
   its own step, or the individual is left standing in the model.

Departures 2 and 3 show what one certificate per engine call cannot see: a change made *between*
calls. Phase 4's stored certificates need a chain of custody — each certificate issued on the
graph the previous one vouched for — or these pass unseen.

**The two ways in still disagree, and now by certificate.** DC+ of nothing at a spot is an empty
double cut through the protocol and a cut round the whole area through the engine; each is
certified as the move it is. DC+ of an edge with another area as its spot is applied by the
protocol and rejected by the kernel, and refused by the engine outright (§3.3a, finding 1).

**Every recorded act has a class** (`src/act_classes.py`, §3.4's table name for name). Of the
corpus's 146 steps: 66 inferential primitive, 35 ampliative, 33 neutral, 6 inferential derived,
5 extension, 1 unruled. Six recordable names are in §3.4's table nowhere — `EXHIBIT`,
`REVISE_M(sibling)`, `definition.fold`, `definition.unfold`, `chain.fix` and everything under
`compose.` — and are held as unruled rather than guessed at.

### 3.4 Which acts the soundness claim covers

A recorded history is not one derivation: it contains acts that revise the model by choice. The
project already classifies them (`src/proof_character.py`), and the certificate scheme adopts that
classification as a type on every recorded act:

| Class | Acts (current names) | Certificate |
|---|---|---|
| **Inferential primitive** | ERA, INS, IT+, IT−, DC+, DC−, the vertex, ligature, split/merge and constant rules | one kernel-checked step |
| **Inferential derived** | UI, DISCHARGE_TO_M, ABANDON_EPISODE, ENTERTAIN, the fused conveniences of §4 | the recorded expansion, every step kernel-checked |
| **Ampliative** | REVISE_M, ADMIT_FACT, SCRIBE_AXIOM, SCRIBE_LAW, FOLD_NUMERAL, ADMIT_TO_M, RETRACT_FROM_M, DECAY, BANK_TO_M, PROPOSE | none — typed as a choice, never presented as an inference |
| **Neutral** | PEEL, TRACE_ALTERNATIVES, SURVEY_* | kernel checks the logical content is unchanged |
| **Extension** | QUOTE and the B-min quotation apparatus | outside Dau's Beta: its own soundness argument (§6) |

Opaque derived steps (`apply_derived` without a recorded expansion) are not admitted to a certified
history.

**The soundness statement this yields:** between any two ampliative acts, the inferential steps of a
recorded history form a derivation in Dau's calculus, every step checked by the kernel; by Dau's
soundness theorem (the project cites Ch. 17), the later graph is entailed by the earlier. That
holds unconditionally on everything outside the trusted base. It is conditional on the kernel
implementing Dau's definitions correctly — which the Tarski differential testing already examines,
and which a mechanization would settle (§9).

## 4. The seventeen entries, resolved

The resolutions follow the rulings in §1. "Conform" means the engine performs exactly the move
named, or refuses it. Several entries share a mechanism, so the fixes are fewer than the entries.

### 4.1 Fused or enlarged moves — split into discrete steps

**`era-also-erases-the-vertex-it-isolates`** (structure, PROVISIONAL, 5,860 exhaustive). Dau
Def 15.2 (p.165): erasing an edge removes the edge only, V^(e) := V. The engine's erasure closure
(`subgraph_closure_validator.analyze_closure(..., for_erasure=True)`, via `ERAInteraction`,
`rule_interaction.py:493`) adds each vertex the erasure isolates in the edge's own context, and
erases it too. **Resolution: split.** ERA of a named edge performs Dau's edge clause and leaves the
isolated vertex; erasing that vertex is a separate step (VERTEX_ERA, or CONSTANT_EXISTENCE for a
constant — 180 of the 250 default-mode moves involve constants). This also resolves
`era-closure-drags-a-quoting-name` (4.3), whose refusal is caused by the same closure. *Drawing
consequence:* an isolated heavy dot now remains on the sheet after an edge is erased; the
correspondence check must cover that state (it should already — verify).

**`it-plus-reuses-a-selected-vertex-in-a-deeper-context`** (structure, PROVISIONAL, 1,903).
Dau Def 15.2 iteration (p.166) copies every vertex of the subgraph: V′ := V×{1} ∪ V0×{2}.
`IterationRule` (`formal_transformation_rules.py:1290`) maps each selected top-level vertex to
itself when the target is deeper, extending the line instead — the ledger identifies this as Dau's
copy, plus a ligature extension (Def 15.2 second clause, p.164), plus a merge (Def 16.6 / Lemma
16.7, pp.175–178). **Resolution: split** into those three recorded steps, IT+ copying every vertex.
**A defect to fix on the way:** where the selection is an isolated vertex (56 of 78 default-mode
moves) the engine reports success and inserts nothing; Dau inserts a copy. **Interaction to check:**
`derived_rules.universal_instantiation` composes IT+ → `=` → merge on the assumption that IT+
produces a fresh line; after this change that assumption becomes exactly true, and the
implementing session must confirm UI does not now join twice (caution 4: read what the module says
about itself).

**`vertex-era-erases-a-line-with-its-edges`** (refusal, SEVERE, PROVISIONAL, 2,608) and its soundness
half **`vertex-era-erases-a-line-not-an-equivalence`** (PROVISIONAL, 1,900). Dau Def 15.2 (p.166):
the vertex rule erases a vertex with E_v = ∅ only, and is an equivalence. The engine has no
vertex-erasure entry point; ERA auto-expands the vertex to the vertex with all its edges.
**Resolution: a VERTEX_ERA entry point of its own**, erasing an isolated vertex in any context
(constants via CONSTANT_EXISTENCE), refusing a vertex with edges and saying which edges must be
erased first. Erasing a line with its edges becomes discrete steps: ERA of each edge (positive
context), then VERTEX_ERA — or one ERA of the closed subgraph, *if the user names it*. Vertex
erasure is an equivalence again. Also resolves `vertex-era-positive-only` (4.3).

### 4.2 Larger move than named — conform by refusing, with a proposal

**`era-auto-closes-a-vertex-selection`** (refusal, SEVERE, PROVISIONAL, 9,891). Dau Def 15.2
(pp.164–165) erases an edge, an isolated vertex, or a closed subgraph (Def 12.10, p.134:
E_v ⊆ E′ for every selected vertex). Named a vertex without all its edges, the engine erases the
closure. **Resolution: refuse the named selection; offer the closure as a proposal.** The analyser
keeps its job — it computes the closure — but `allow_expansion=True` leaves the apply path; the UI
may present "erase the closed subgraph this generates?", and if accepted, *that* is the move named
and recorded.

**`it-plus-auto-closes-a-vertex-selection`** (structure, PROVISIONAL, 10,802). Dau Def 15.2
iteration copies a not-necessarily-closed subgraph (Def 12.10), so a vertex named without its edges
is iterated as a vertex. `ITPlusInteraction` closes first (`rule_interaction.py:743`).
**Resolution: conform** — iterate exactly the named subgraph; offer the closure as a proposal on the
same terms as ERA.

**`dc-plus-ignores-target`** (refusal, SEVERE, PROVISIONAL, 22,366). Dau Def 15.2 (p.164) inserts
a double cut in the context whose contents it encloses. Given a subject and a different spot,
`DCPlusInteraction.build_context` (`rule_interaction.py:330`) ignores the spot. **Resolution:
refuse** when a spot is given that is not the subject's own area. Related, and to be decided at the
same time: with neither subject nor spot the protocol wraps the whole sheet (`:336–339`) — Dau-legal,
but a move nobody named; the recorded step must name the selection it actually enclosed.

### 4.3 Refusals — complete where cheap, otherwise annotate

**Named-with-contents normalisation** — `dc-plus-refuses-a-cut-named-with-its-contents` (5,824),
`era-refuses-…` (6,158), `it-plus-refuses-…` (7,154), `it-minus-refuses-…` (18). By Def 12.10 a
cut named with some of its contents names the same subgraph as the cut alone. **Resolution:** one
shared normaliser (`tops`, already in the oracle) applied before the same-area check in all four
interactions. **Open:** at tier A, IT− refuses the top-elements-only move too (0 of 8 applied), so
for IT− the normaliser may not be the whole story; investigate before claiming it fixed.

**`era-closure-drags-a-quoting-name`** (18) — resolved by the edge-only erasure of 4.1.

**`heavy-dot-negative-only`** (3,140) — Dau Def 15.2 (pp.164, 166) inserts an isolated vertex in
any context. `HEAVY_DOT` (`formal_transformation_rules.py:1809`) refuses positive contexts.
**Resolution: conform.** (Sound because Dau's structures have non-empty universes.)

**`vertex-era-positive-only`** (298) — resolved by the VERTEX_ERA entry point of 4.1.

**`ins-edge-has-no-entry-point`** (8) — inserting an edge onto vertices already present in a
negative context (the inverse of edge erasure, p.165). **Resolution:** an INS_EDGE entry point that
takes a relation name and existing vertex ids, not standalone EGIF. The kernel's `_ins_edge`
already judges it.

**`it-minus-strictly-enclosing-only`** (512) — iteration may copy into c = ctx(G0), so deiteration
may remove a copy whose original sits in the same context. `ITMinusInteraction`
(`rule_interaction.py:880–925`) searches strictly enclosing areas only. **Resolution: conform** —
include the candidate's own area, with the original disjoint from the copy.

**`move-branches-tries-one-direction-only`** (36) — Lemma 16.1 with symmetric Θ licenses the move
when some hook on either vertex qualifies; the engine fixes v_a by `_canonical_vertex_order`
(`ligature_manipulation_rules.py:243`). **Resolution: try both orientations** — the ledger's own
prescription, which explicitly warns against relaxing the side condition instead.

### 4.4 Rules with no entry point

`CONSTANT_EXISTENCE` is **in scope**: §4.1 needs it the moment an isolated constant is erased or
inserted, and the kernel must be able to name it (`legal()` does not judge it today:
`judged=False`). `ORIENT_IDENTITY`, `LIGATURE_VERTEX` and `SEPARATE_CONSTANT`
are completeness work, scheduled after §8's criteria are met, and disclosed until then. The
"Beta-complete" claim in `docs/CONTRIBUTION_AND_PRIOR_ART.md` (lines 61 and 459) is withdrawn now.

**`CONSTANT_IDENTITY` is in scope too (R7 as amended, ruled 2026-11-25).** The Phase 0 map found
that `world_scroll.discharge_episode` runs `vertex_scope.normalize_constants` after its three rules
(§3.3a, finding 2), so DISCHARGE_TO_M — inferential-derived, "every step kernel-checked" (§3.4) —
contains a graph change that no rule in scope could name. The alternative, recording the
normalisation as an act that is not an inference, was declined: the result is not `same_graph` to
its input, so it could not be certified as content-identity, and it sits inside the act by which a
fact enters M by inference.

The rule, read from the book on 2026-11-25 (Def 24.10, p.271; `pdftotext` of
`docs/references/mathematical_logic_with_diagrams.pdf`):

> **Constant Identity Rule.** Let C ∈ C be a constant name. Let v, w be vertices with
> ρ(v) = ρ(w) = C. Let c be a context with c ≤ ctx(v) and c ≤ ctx(w). Then arbitrary
> identity-links id with ν(id) = (ve, vf) may be inserted into d or erased from c.
>
> **Existence of Constants Rule.** Let C be a constant name. In each context c, we may add a fresh
> vertex v with ρ(v) = C. Vice versa, if v is an isolated vertex with ρ(v) = C v may be erased
> from c.

The link goes into a context enclosed by *both* vertices, so two same-name vertices in sibling
cuts cannot be linked directly. The expansion the normaliser's move appears to have — **a reading,
not yet reproduced on a graph, and to be reproduced before it is built:**

- the survivor already dominates the twin: CONSTANT_IDENTITY (the link, in the twin's context),
  then MERGE_VERTICES (Def 16.6, p.176), once per twin;
- twins in sibling cuts: CONSTANT_EXISTENCE of a fresh vertex at their least common area first,
  then the same pair per twin.

CONSTANT_IDENTITY is therefore sufficient only together with CONSTANT_EXISTENCE and a checked
merge — and production's merges are today the unchecked private operation (§3.3a, finding 5).
ADMIT_TO_M's join (§3.3a, finding 3) is the same move and takes the same recorded expansion,
though as an ampliative act it owes no certificate.

Two readings ride with this and are the author's (R2):

1. **The printed rule is corrupt.** "ν(id) = (ve, vf)" names vertices of the Functional Property
   Rule stated just above it, and "inserted into d" names a context the rule never introduces.
   The reading taken is ν(id) = (v, w) and "into c".
2. **Merging two constant vertices.** §24.4 (p.275) carries the Chapter 16 results over to
   vertex-based EGIs "as long as we do not change the set of its labels", which a merge of two
   C-labelled vertices satisfies. No Chapter 24 restatement of Def 16.6 itself was found.

**Until Phase 3 builds the expansion, the discharge's normalisation is one unrecorded step.**
Phase 2's observe-mode kernel will reject it, and it is in no ledger entry today. Phase 2 gives it
a named entry, so that the gate's "and nothing else" stays true.

## 5. Stored histories

Splitting moves changes what replaying an old chain produces. The tomos corpus records 17 ERA,
5 IT+ and 4 UI steps among its chains, and roughly 99,000 gitignored `runs/` artifacts must stay
loadable.

**Proposed:** every chain step gains a `rule_version`. Steps recorded before the change replay
through a *legacy expansion* that emits the discrete, kernel-checked steps the old fused move
amounted to — the ledger's measurements say what each was (`orphans_erased`, the
copy-extend-merge triple, the closed subgraph). The 52 corpus universes are then regenerated so the
exemplars show conforming proofs, with `same_graph` asserted per file before each rewrite (the
discipline the 2026-09-24 alphabet migration used). Ruling required (§7, R5).

## 6. Out of scope, declared

- **The language of a universe of discourse (Σ).** Dau's rules hold Σ fixed; INS can silently grow
  it (docket item 10). Inserting a new relation name in a negative context is sound over the
  extended language, so this is not a soundness gap, but the certificate records it as a language
  act once item 10 lands. Until then the kernel checks steps over the graph's derived alphabet and
  the gap is disclosed.
- **The quotation extension (B-min).** Quotation ovals, quoting names, `sort` and `quotation` are
  Arisbe's, not Dau's Beta. Its conservativity argument (ROADMAP thesis iii; Dau Ch. 26's
  reduction) is a separate document. Until it exists, a history containing QUOTE is certified on
  its Beta steps and says so.
- **Completeness** beyond §4.3, CONSTANT_EXISTENCE and CONSTANT_IDENTITY.

## 7. Rulings required

| # | Question | Proposed | Status |
|---|---|---|---|
| R1 | Fused moves become discrete recorded steps; conveniences become derived rules with recorded expansions | Yes | **Ruled 2026-11-25** |
| R2 | Confirm the seven PROVISIONAL readings of Def 15.2 / Def 12.10 (ledger entries 0, 2, 11, 13, 14, 15, 16) against the book — above all, what Def 15.2's second clause (p.164) licenses, which fixes the discrete steps of the IT+ split. Added with the R7 amendment: the two Chapter 24 readings in §4.4 (the corrupt printed text of the Constant Identity Rule; whether Def 16.6's merge covers two constant vertices) | — | **Open: author checking against the book.** Blocks Phase 3 only |
| R3 | Enlarged selections (ERA, IT+): refuse and offer the closure as an explicit proposal, rather than refuse outright | Refuse + propose | **Ruled 2026-11-25: refuse + propose** |
| R4 | DC+ with neither subject nor spot: keep the whole-sheet convenience, recording the enclosed selection; or remove it | Keep, recorded | **Ruled 2026-11-25: keep, recorded** |
| R5 | Stored chains: `rule_version` + legacy expansion; regenerate the corpus exemplars | Yes | **Ruled 2026-11-25: yes** |
| R6 | Neutral acts (PEEL, TRACE_ALTERNATIVES, SURVEY_*) certified as content-identity; QUOTE as a declared extension | Yes | **Ruled 2026-11-25: yes** |
| R7 | CONSTANT_EXISTENCE implemented in this arc; the other four missing rules after it | Yes | **Ruled 2026-11-25: yes. Amended the same day, after the Phase 0 map (§3.3a, finding 2): CONSTANT_IDENTITY is implemented in this arc as well; the other three after it** |
| R8 | The fused iterate-and-join survives as a named derived rule (or is retired in favour of UI) | Keep as derived | **Ruled 2026-11-25: named derived rule (e.g. ITERATE_AND_JOIN), expanding to copy, extend, merge** |

## 8. Done — the criterion for outreach

The calculus is ready to show when all of these hold:

1. Every ledger entry is resolved as conformed, split, or refused-and-annotated, with the author's
   rulings recorded in the entry; no SEVERE, DIFFERS or NOT-AN-EQUIVALENCE entry remains.
2. Every inferential act carries a kernel-checked certificate; `certify` is the only route to the
   engine, enforced by a test; certificates are re-checked on load.
3. The kernel imports no engine module, enforced by a test; the trusted base is listed in one
   document with its line count.
4. The default and exhaustive calculus suites are green against the kernel; the Tarski differential
   tests run against the kernel itself.
5. README, VISION_AND_SCOPE, SOUNDNESS_BOUNDARY, CAPABILITY_MAP, CONTRIBUTION_AND_PRIOR_ART and the
   Dau letter say only what (1)–(4) support, and state what remains incomplete.

## 9. Relation to a mechanization

The certificate is the interface to a proof assistant. A Lean or Coq formalization of Dau's EGIs,
his semantics and his rules, with a soundness theorem, plus a checker proved correct against that
formalization, would replace "the kernel implements Dau correctly" with a theorem. Certificates
produced by Arisbe would then be checked by the verified checker unchanged. Nothing in this arc has
to be undone to get there.
