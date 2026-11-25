# Calculus conformance and certified soundness

**Date:** 2026-11-25 · **Status:** specification, nothing built · **Rulings:** R1, R3–R8 ruled 2026-11-25; R2 open (§7)
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
`judged=False`). `ORIENT_IDENTITY`, `LIGATURE_VERTEX`, `CONSTANT_IDENTITY` and `SEPARATE_CONSTANT`
are completeness work, scheduled after §8's criteria are met, and disclosed until then. The
"Beta-complete" claim in `docs/CONTRIBUTION_AND_PRIOR_ART.md` (lines 61 and 459) is withdrawn now.

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
- **Completeness** beyond §4.3 and CONSTANT_EXISTENCE.

## 7. Rulings required

| # | Question | Proposed | Status |
|---|---|---|---|
| R1 | Fused moves become discrete recorded steps; conveniences become derived rules with recorded expansions | Yes | **Ruled 2026-11-25** |
| R2 | Confirm the seven PROVISIONAL readings of Def 15.2 / Def 12.10 (ledger entries 0, 2, 11, 13, 14, 15, 16) against the book — above all, what Def 15.2's second clause (p.164) licenses, which fixes the discrete steps of the IT+ split | — | **Open: author checking against the book.** Blocks Phase 3 only |
| R3 | Enlarged selections (ERA, IT+): refuse and offer the closure as an explicit proposal, rather than refuse outright | Refuse + propose | **Ruled 2026-11-25: refuse + propose** |
| R4 | DC+ with neither subject nor spot: keep the whole-sheet convenience, recording the enclosed selection; or remove it | Keep, recorded | **Ruled 2026-11-25: keep, recorded** |
| R5 | Stored chains: `rule_version` + legacy expansion; regenerate the corpus exemplars | Yes | **Ruled 2026-11-25: yes** |
| R6 | Neutral acts (PEEL, TRACE_ALTERNATIVES, SURVEY_*) certified as content-identity; QUOTE as a declared extension | Yes | **Ruled 2026-11-25: yes** |
| R7 | CONSTANT_EXISTENCE implemented in this arc; the other four missing rules after it | Yes | **Ruled 2026-11-25: yes** |
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
