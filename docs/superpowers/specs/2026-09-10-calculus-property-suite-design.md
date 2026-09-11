# Testing the calculus directly — a property suite with a counted extent

**Date:** 2026-09-10 · **Branch:** `tier0-readiness` · **Status:** built 2026-09-11; priors recorded in §7.

## 1. Why this, and why now

The sixteenth arc re-framed the goal. The letters assumed a firm basis for sending them, and the
round-trip arc put that assumption in doubt — not by finding the calculus wrong, but by finding
that the evidence it was right had gone missing for eleven months. The bedrock answer from that
arc stands: `egi_core_dau`, `formal_transformation_rules`, `subgraph_closure_validator` and
`graph_isomorphism_engine` reference no linear form, so the 53 CGIF/CLIF defects could not reach
the calculus. But "could not reach it" says nothing about whether the calculus is right. Nothing
tests that directly today.

What exists is narrow. The three `test_properties_*.py` files draw graphs from an EGIF strategy
offering arities 1–2, at most one cut, and never an empty cut, then apply one hand-picked move
and test *reversibility*. None tests *soundness*. None lists the legal moves on a graph — no
module in the codebase does. And the core already enforces Dau's structural constraints at
construction (`RelationalGraphWithCuts.__post_init__`), so "the output is a valid graph" is true
by construction and tests nothing.

The pattern this suite must not repeat, met six times in two arcs: **coverage derived from
incidental state, with no assertion about its extent.** Every layer here counts what it covered
and pins the count.

## 1a. What reading Dau changed (added during planning, 2026-09-10)

Dau's book is in the repo (`docs/references/mathematical_logic_with_diagrams.pdf`); the plan
was written against Chapters 12, 13, 15, 16.1 and 24, transcribed page by page. Six things in
this spec were wrong or incomplete, and the plan follows the corrections, not the text above.

1. **"Dau's constraints are enforced at construction" is false.** Dominating nodes — ctx(e) ≤
   ctx(v) for every edge and incident vertex (Def 12.5, p.125) — is part of the *definition* of an
   EGI (Def 12.7, p.126; Def 24.1, p.260). The core does not enforce it: a vertex inside a cut
   with its edge on the sheet constructs without complaint. Worse, the core's own check is
   **inverted**: `has_dominating_nodes()` returns False on the ordinary `(P *x) ~[ (Q x) ]` and True
   on the ill-formed graph (probed). The inverted helper `_context_dominates` also guards
   `replace_vertex_on_hook` and the add-vertex-to-ligature path, and `derived_rules.py` carries a
   comment calling one of its wrong refusals right. The suite carries its own check; the core
   defect goes to the ledger. Fixing it is a protected-core change and is **not** in this plan.
2. **The rule table follows Dau, not the engine.** Def 15.2 (p.164–166): erasure and insertion are
   one-way; iteration, deiteration, double cuts, and the **isolated-vertex rules** are mutually
   inverse pairs — and an isolated vertex may be inserted or erased **in any context**. Def 12.14
   (p.138) adds the ligature transformation rules; Lemmas 16.1–16.7 (p.169–178) the derived
   ligature rules, all equivalences; Def 24.10 (p.270–271) the rules for constants. Each Dau rule
   maps to an engine entry point or to none. The engine's HEAVY_DOT covers vertex insertion in
   *negative* contexts only, and mints the fixed id `heavy_dot_vertex`, so a second application
   silently does nothing and reports success (probed). Vertex erasure outside positive contexts,
   orientation of an identity edge, adding/removing a ligature vertex, and the three constant
   rules have **no** entry point: they are counted as unimplemented and pinned, not enumerated.
3. **The vertex split/merge rules are live** (`derived_rules`, `world_scroll` call
   `_apply_vertex_split` / `_apply_vertex_merge`) and join the table as Def 16.6 / Lemma 16.7.
4. **Arisbe does not write lines the way Dau does.** Dau joins areas with identity edges (`=`);
   Arisbe writes a line crossing cuts as one vertex in the outer context, with edges nested below
   it — lawful under dominating nodes. So `legal()` reads each rule *in that representation*: a
   Dau application composed with the ligature transformations that re-express an outer line
   (Def 12.14; Lemmas 16.1–16.3; Dau's own worked remark, p.166–167). Each rule's docstring states
   the reading and its derivation. Refusal agreement is **not** judged for the four
   ligature-engine rules and split/merge, whose parameters underdetermine the move; they get the
   structural and strict-soundness layers only, and the extent says so.
5. **Semantics.** The domain is non-empty (Def 13.1, p.141) and two names may co-denote (nothing in
   Ch. 24 forbids it). `=` is equality (Def 13.1), so tier A's alphabet includes `=` and `tarski`
   fixes its extension; `semantic_game` does **not** special-case `=`, so the differential layer
   encodes the diagonal `(= u u)` into each facts graph. The syntax admits 0-ary relations (Defs
   12.1, 12.6) but the semantics as printed does not (Def 13.1 uses ℕ): `tarski` reads a 0-ary
   relation as a truth value — a declared extension, flagged as such.
6. **INS content** is standalone EGIF, which cannot write `(p)` or an isolated constant; the content
   catalogue excludes them and the extent says so. The 8/8 and 3/8 validation pairs of the
   constant-normal-form ruling were measured ad hoc and never kept; `tarski` is validated on
   freshly built pairs of the same two kinds instead.

Dau's own text carries errata the transcription flagged (Def 12.4 counts a cut as enclosing
itself; p.166 prints κ(v) = ⊤; Def 16.6 names its direction backwards). The suite follows the
reading the calculus requires and cites the page.

## 2. The shape

Four units in `tests/`, each testable without the others:

| Unit | Does | Depends on |
|---|---|---|
| `calculus_enum.py` | builds tier-A graphs, gathers tier-B graphs, enumerates candidate moves, states Dau's preconditions independently (`legal`) | the data model, `canonical_signature`, `TomosService` |
| `tarski.py` | Dau-faithful evaluator over finite structures; model sets as bitsets | the data model only |
| four layer test files | refusal agreement · structure · soundness · differential | the two above, `proof_authoring.apply_rule`, `semantic_game` |
| `calculus_ledger.json` | the shrinking record of known failures | — |

Rules are applied through `proof_authoring.apply_rule` — the `RuleInteraction` protocol path that
chains replay through.

**Rule extent.** The suite declares the rules it covers — ERA, INS, IT+, IT−, DC+, DC−,
HEAVY_DOT, and the ligature rules of `ligature_manipulation_rules` (live: imported by
`formal_transformation_rules`). A meta-test compares the declaration with the engines'
`get_available_rules()`; a rule the suite does not enumerate fails it.

## 3. The enumerator — `tests/calculus_enum.py`

### 3.1 Tier A: every small graph, built directly

Graphs are built with the core's constructors, never from EGIF text, so the suite does not inherit
a linear form's blind spots. Default bounds, each a parameter, fixed after task 1 measures them:

- up to 2 cuts, in every tree shape (none; one; two siblings; two nested);
- up to 3 edges, over relations of arity **0, 1, 2 and 3**;
- up to 2 generic vertices and up to 2 constants (`a`, `b` — two, so co-denotation is testable);
- isolated vertices and empty cuts allowed;
- every vertex placed in *every* area enclosing its uses, not only the lowest — the line above its
  uses is the `colore_field` shape.

Graphs are de-duplicated up to isomorphism by `canonical_signature`. A graph `__post_init__`
refuses is discarded **and counted**. Unnormalized constants — two spots for one constant — are
included: Dau's calculus is defined on them, and the constant-normal-form ruling found them
semantically inert (8/8).

### 3.2 Tier B: the corpus as used

The current graph of each of the 52 corpus UoDs plus the 178 states of the 35 saved chains,
de-duplicated by signature.

### 3.3 Moves

`moves(rule, graph, tier)` yields every *candidate* application, legal or not — refusal agreement
needs the illegal ones.

- **Tier A:** every subset of the graph's elements as the selection, crossed with every area as the
  target where the rule takes one.
- **Tier B:** every structural unit — each edge, each cut with its contents, each vertex with its
  closure, each whole area — plus every selection of at most two elements. The budget is a move
  count per graph; every skipped move is recorded with its reason.
- **INS content** comes from a fixed catalogue: the tier-A graphs of at most two elements.

Measured cost of one application: 0.1–0.4 ms, `bfo_core` and `colore_field` included. The budget
goes to structures, not to rules.

### 3.4 Preconditions, stated independently

`legal(rule, graph, move) -> (bool, reason)` is written fresh from Dau's definitions and imports
nothing from `formal_transformation_rules` or `subgraph_closure_validator`. It is the second
witness for refusal agreement, and it earns that role with its own unit tests: hand-built legal
and illegal cases for each rule, each citing the Dau definition it enacts.

## 4. The evaluator — `tests/tarski.py`

A structure is a domain U, an assignment of constants into U (two names **may** share a value),
and an extension for each relation — a zero-arity relation read as a truth value. Evaluation is
endoporeutic: an area is satisfied under a valuation iff some extension to its **own** generic
vertices makes every edge in it hold and no cut in it satisfied. A generic line is quantified where
it is placed, so a line above its uses reads ∃x ¬P(x), not ¬∃x P(x). No binding ceiling, no open
world, no UNKNOWN. Quotation ovals are skipped — mention, not use, as the A3 gate requires.

Why not `semantic_game`: it identifies constants by label (unique names, so co-denoting models go
unexamined), returns UNKNOWN past `MAX_BINDINGS` (a silent ceiling), and it is itself code under
trust. It is tested against `tarski` in §5.4 instead of serving as the oracle.

**Validated before it is trusted**, on pairs whose answer is known:

- the constant-normal-form pairs must *not* separate (8/8 equivalent);
- the generic-line control pairs must separate (the 3/8 that differed);
- **the falsifier** — prior `P-K1` below.

## 5. The layers

### 5.1 Refusal agreement

Every candidate move falls in one cell of engine (applied/refused) × `legal` (true/false):

- applied, legal — passes to the other layers;
- refused, illegal — correct;
- refused, legal — **incompleteness**; ledger;
- applied, illegal — **the severe cell**; ledger.

A refusal must arrive as the protocol's own rejection (`AssertionError` from `apply_rule`). Any
other exception is a crash, and a crash is a defect.

### 5.2 Structure: each rule changes exactly what it licenses

For each legal move the *expected* G′ is built independently from the data model's primitive
builders (`with_*`, `without_element`) — never from the rule module — and compared with the
engine's G′ by `same_graph`:

- **ERA** — G less the selection's closure, nothing else;
- **INS** — G plus the content graph, in the target area;
- **DC+ / DC−** — exactly two nested cuts added around the selection, or removed;
- **HEAVY_DOT** — exactly one isolated vertex added.

**IT+, IT− and the ligature rules** are checked by postcondition, because building their expected
result independently would be a second rule engine: the added or removed part is isomorphic to
its source and sits in the target, and the complement is unchanged. The semantic layer backs them.

On every output: the B-min maps (`alphabet`, `rho`, `sort`, `quotation`) carry forward, and no
existing line moves — the placement defect's family. Constant normal form is **not** required;
the ruling puts it at the construction boundary, and INS of `a` into a cut may lawfully create a
second spot.

### 5.3 Soundness, strict

For each legal move G→G′:

- **ERA and INS are one-way** — every model of G is a model of G′ (Def 15.2, p.164–165);
- **every other rule is an equivalence** — both directions: IT+ and IT− (each the other's
  inverse, Def 15.2 p.164, 166), DC+, DC−, the vertex rules (VERTEX_INS via HEAVY_DOT,
  VERTEX_ERA) and the ligature rules. This is the rule table's direction column
  (`calculus_rules.RULES`, §1a.2); an earlier draft of this section filed IT+ with the one-way
  rules, which the table and Dau p.166 contradict.

The equivalence check is stricter than soundness: it catches a rule that is sound but loses
information. The author asked for that strictness. The split is a **declared table** taken from
Dau's statement of each rule, with a citation per row — the six rules' classification is
settled, but each ligature rule's is to be confirmed against Chapter 16 when the table is
written, not assumed here.

Each graph's set of satisfying structures is computed once, as a bitset over a fixed universe of
structures for its vocabulary, cached by `canonical_signature`; a move then costs one subset test.

- **Tier A:** exhaustive over domains of size 1–3, up to a declared cap on total relation tuples;
  past the cap, a seeded sample, and the extent names which pairs were sampled.
- **Tier B:** a seeded, counted sample, **stated as a sample.** Exhaustive structures over a corpus
  vocabulary are out of reach, and the suite says so rather than implying otherwise.

A finite search cannot prove soundness. It can refute it: one separating structure is decisive.

### 5.4 Differential: `semantic_game` against `tarski`

On tier-A graphs where `semantic_game`'s assumptions hold — unique names, closed world — each
structure is encoded as a facts graph for a closed `CorpusOracle`, and the two verdicts compared.
Three counted columns: **agree**; **disagree** (a defect; ledger); **`semantic_game` said
UNKNOWN** (its ceiling — counted, never scored as agreement). Agon's verdicts rest on this
evaluator, so its agreement with Dau's semantics is measured here for the first time.

## 6. The ledger and the extent

**`tests/calculus_ledger.json`**, committed. Each entry: an id, a layer, a rule, a hand-written
reason, and the set of instances it covers. An instance key is the canonical signature plus the
move expressed in canonical element positions, so keys survive re-minted UUIDs. Two rules:

1. every failing instance belongs to some entry — else the suite fails and names it as **new**;
2. every instance in an entry still fails — else the suite fails with **"shrink this entry"**.

A partial repair announces itself; the ledger can only shrink by someone deciding it should.

**Extent pinned exactly, never a floor.** Each layer asserts its counts *equal* pinned figures:
graphs enumerated and discarded, moves by rule and tier, structures exhaustive and sampled, skips
by reason. `test_tomos_parsing.py`'s `holding >= 90` against a measured 141 is the counterexample
— 51 regressions could land under it unseen.

**Two modes.** The default suite runs tier A at a reduced bound plus tier B's current graphs,
units only; `-m exhaustive` runs everything. Each mode pins its own extent. Target: the default
slice in two minutes or less; the exhaustive run in whatever it costs, reported.

**Where the build departed from this section (recorded 2026-09-11).** Three budgets were set in
Task 10 to keep the two modes inside their time limits, and each shows in the extent rather than
being hidden. First, tier B takes at most 100 moves per rule per graph in the default mode and
500 in the exhaustive mode, the first ones in enumeration order. That is a prefix, not a random
sample, and every move past it is counted under `skipped` (for DC+ at exhaustive bounds, 36,977
taken and 3,215,111 skipped). Second, a tier-B universe larger than 36,864 structures is
sampled. Third, `ENGINE_PATTERN_CEILING` in `calculus_run.py` does not apply an IT- move whose
expanded selection exceeds 64 elements, because the engine's search for the original does not
finish on such patterns. Those moves are counted as `engine-does-not-finish`: 9 in the default
mode and 239 at exhaustive bounds. Of these, 3 and 144 exceed 100 elements, which was the
ceiling before Task 10 lowered it; the other 6 and 95 are the ones the lowering added. Separately,
2,289 default and 3,000 exhaustive tier-B soundness moves are counted `too-large` and not
evaluated.

## 7. Pre-registered priors

All are **existence** questions — answerable in the calculus as it stands.

- **`P-K1` — the falsifier.** `tarski` finds a structure separating `colore_field` from its EGIF
  round trip, and the separating structure turns on one of its 24 lines placed above their uses.
  *Fails if* no separating structure exists (the round trip preserves meaning, and the plan's
  diagnosis of that residue is wrong) or one exists but turns on something else.
  **Outcome (2026-09-10 run):** REFUTED: premise — colore_field's stored graph is not an EGI: it
  violates dominating nodes (Def 12.5, p.125) at 8 edge–vertex pairs on 2 vertices, and its EGIF
  round trip is Def-12.5-clean, so the round trip repairs it rather than changing a meaning. The
  same census finds exactly one other non-EGI in the corpus — bfo_core (4 pairs, 1 vertex) — and
  none among 178 chain states: the two are exactly the round-trip residue. The "lines above their
  uses" diagnosis was wrong.
- **`P-K2`.** The severe cell is empty on tier A: the engine applies no move `legal` rejects.
  *Fails if* any tier-A instance lands there.
  **Outcome (2026-09-10 run, default bounds, 208 graphs):** REFUTED — `dc-plus-strands-a-vertex`,
  `dc-plus-ignores-target`, `era-auto-closes-a-vertex-selection`,
  `vertex-era-erases-a-line-with-its-edges`, `it-plus-into-its-own-selection` (all ledgered
  PROVISIONAL, for the author). Two are defects of substance: IT+ copies a selected cut into itself
  (Def 15.2 p.164 forbids c ∈ Cut₀), and on 17 instances the step is unsound — `~[ ~[ ] ]` (true)
  becomes `~[ ~[ ~[ ] ] ]` (false); and DC+ wraps a vertex while leaving its edges outside, yielding
  a non-EGI (Def 12.5 p.125) on 297 moves (288 distinct instance keys). The other three are protocol conventions — the
  engine performs a larger or differently placed Dau-legal move than the one named (auto-closing a
  selection; ignoring DC+'s spot when a subject is given) — sound on every instance measured, but
  the named move is not refused.
  *Note (added in Task 10; the prior and its outcome above stand unedited):* tier B, the corpus
  as used, adds two SEVERE mechanisms that tier A cannot build (they need five elements, or a
  name at two arities).
  - `it-minus-erases-a-copy-of-another-line`: IT- erases an edge whose supposed original hooks a
    different vertex. 33 moves in the default mode, 64 at exhaustive. UNSOUND on the hand-built
    control `*x *y (P x) ~[ (P y) ]` → `*x *y (P x) ~[ ]`, and at exhaustive on group_identity's
    chain states.
  - `ins-mixes-arities-without-an-alphabet`: with no declared alphabet, INS accepts a name at a
    second arity, against Def 12.6–12.7 (p.126). 52 moves in the default mode, 244 at exhaustive.

  Both are ledgered PROVISIONAL. At exhaustive bounds the refusal ledger holds 77,636 keys in 15
  entries, pinned by count per kind, with 0 failing keys spanning two cells.
- **`P-K3`.** No tier-A soundness failure in the one-way rules (ERA, INS, IT+).
  *Fails if* any structure models G but not G′.
  *Note (added at the Task 8 review):* this prior was written under §5.3's superseded reading
  that filed IT+ with the one-way rules; the suite checks IT+ as an equivalence (Dau p.166).
  **Outcome (2026-09-10 run, default bounds, 208 graphs, domain sizes 1–2):** REFUTED —
  `it-plus-into-its-own-selection-changes-meaning`. 17 tier-A IT+ moves are UNSOUND —
  `~[ ~[ ] ]` (true in every structure) becomes `~[ ~[ ~[ ] ] ]` (false in every structure) — and
  154 more are not the equivalence IT+ must be. Every one is a move `legal` rejects: the engine
  iterates a selected cut into itself (Def 15.2 p.164 forbids c ∈ Cut₀), the soundness half of
  refusal entry `it-plus-into-its-own-selection`. **No soundness failure on any move `legal`
  judges legal**, in any rule. Legal moves evaluated, every one passing: ERA 765 and INS 700
  (one-way), IT+ 1,252 (equivalence); separately, illegal moves the engine applies that also
  pass: ERA 243, IT+ 83 (printed by `calculus_adjudication_soundness` as the evaluated passes
  by rule and legal verdict). (The check holds IT+ to equivalence, per the rule table — stricter
  than §5.3's list, which files IT+ with the one-way rules.) Four more soundness entries, none on a
  legal move: `vertex-era-erases-a-line-not-an-equivalence` (sound, but an erasure where the vertex
  rule is an equivalence) and three ligature entries on moves `legal` does not judge —
  `merge-vertices-erases-a-constant-vertex`, `retract-ligature-erases-a-constant-vertex`,
  `move-branches-moves-the-identity-edge-it-moves-along` (each turns `(= "a" "b")` into a graph
  that no longer says a = b; the last also fails on a generic line, and raises a question about
  Lemma 16.1's statement). At exhaustive bounds with the exhaustive semantics (sizes 1–3; figures
  only, ledgered in Task 10; 3,729 s), `calculus_adjudication_soundness --exhaustive` counts **no
  failure on a legal move over all 5,451 failures**, classified or not. The UNSOUND ones: IT+ 289
  (illegal), and on moves `legal` does not judge MERGE_VERTICES 12, MOVE_BRANCHES 18,
  RETRACT_LIGATURE 18 and REARRANGE_LIGATURE 14 — in negative contexts, or where an identity
  edge sits in a cut deeper than the vertices it joins. 24 of them (RETRACT_LIGATURE 10,
  REARRANGE_LIGATURE 14) are not yet classified: e.g. `*x *y ~[ (= x y) ]` retracts to `*x ~[ ]`. Of the moves that pass, 4,093 were checked over every structure of
  sizes 1–2 and 1,736 over a seeded sample of 64 per size (tuple bits over 6) — pinned in
  `calculus_extent.json` as `default:soundness`; 297 non-EGI DC+ results cannot be evaluated.
  *Note (added in Task 10; the prior and its outcome above stand unedited):* extended to tier B,
  the corpus as used. The default mode takes the 52 current graphs; the exhaustive mode takes 133
  corpus graphs (current graphs and chain states, de-duplicated), with universes sampled above
  36,864 structures. Still **no soundness failure on any move `legal` judges legal**: 0 in the
  default mode, and 0 of 6,343 failures in the exhaustive mode, tier A and tier B. Tier B and the
  exhaustive run add UNSOUND steps, every one on a move `legal` rejects or does not judge:
  - IT+ into its own selection: 711;
  - the ligature rules taking a join deeper than its vertices (`*x *y ~[ (= x y) ]` → `*x ~[ ]`):
    40;
  - MOVE_BRANCHES: 36;
  - RETRACT_LIGATURE erasing a constant: 24;
  - MERGE_VERTICES: 12;
  - IT- erasing an edge whose supposed original hooks another vertex, on group_identity's chain
    states: 4. Separating structure `Structure(2, (), (('M', ((0, 0, 0),)),))`.
- **`P-K4`.** Where both evaluators answer, they agree. *Fails if* any disagreement is counted.
  **Outcome (2026-09-10 run, default bounds, 208 graphs, domain sizes 1–2, unique names, closed
  world):** HELD — 4,392 comparisons, **0 disagreements, 0 UNKNOWN**; 808 over every structure
  of the size, 3,584 over a seeded sample of 64 per size (tuple bits over 6); pinned in
  `calculus_extent.json` as `default:differential`. The verdicts are not one-sided (tarski TRUE
  2,290 / FALSE 2,102), and the graphs carry an identity edge (40), a constant (157), a cut (91),
  a generic vertex (78), a 0-ary relation (44). The instrument bites: with the diagonal `(= u u)`
  left out of the facts graph, the same pass counts 214 disagreements — `semantic_game` reads `=`
  as an ordinary relation (§1a.5), so against a model that does not list its identities, a graph
  using `=` is misjudged. Declared open, the same oracle returns UNKNOWN on 1,828 of 4,392.
  Figures regenerate from `calculus_adjudication_differential`. At exhaustive bounds with the
  exhaustive semantics (sizes 1–3; figures only, pinned in Task 10; 159 s): 3,941,334
  comparisons (3,401,174 exhaustive, 540,160 sampled), again 0 disagreements, 0 UNKNOWN.
  Outside the layer's assumptions
  nothing is claimed: co-denoting names (Def 24.2 allows them; `semantic_game` matches constants
  by label) and open worlds are not compared here.

`bfo_core` carries no prior: it has none of the line-above-use shape and remains undiagnosed.

## 8. Build order

1. Tier-A enumerator; measure counts and runtime; pin the bounds. Its tests assert **shape
   coverage** — at least one graph each with an empty cut, a zero-arity relation, a ternary
   relation, co-denotable constants, an unnormalized constant, and a line above its uses.
2. `tarski.py`; validate on the known pairs; run `P-K1`.
3. `legal()` and its Dau-cited unit tests.
4. On tier A, in order: refusal agreement, structure, soundness, differential.
5. Tier B; the `exhaustive` marker; the extent pins.
6. The agreed side items:
   - `drawing_validity`: a warning for two spots naming one individual (do **not** merge in
     `drawing_to_egi` — §3.3 checks injectivity against the DTO, so a merge would fail
     attestation against the very picture the EGI was read from);
   - delete the zero-byte `tests/test_it_minus_dau_compliance.py`;
   - wire in the never-called `egif_parser_dau._finalize_alphabet_and_rho`, with a test that
     EGIF-parsed graphs carry the same alphabet and ρ as CGIF- and CLIF-parsed ones;
   - replace `test_tomos_parsing.py`'s `>= 90` floor with an exact pin.

## 9. Out of scope

Multi-step defects (a random-walk supplement may follow, never as the spine); Z3 as an oracle
(its FOPL parser fails on ordinary negated content); the linear forms, except as the falsifier's
subject; `bfo_core`'s diagnosis, which this suite may inform but does not own.
