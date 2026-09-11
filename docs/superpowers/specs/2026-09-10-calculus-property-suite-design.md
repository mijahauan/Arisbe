# Testing the calculus directly — a property suite with a counted extent

**Date:** 2026-09-10 · **Branch:** `tier0-readiness` · **Status:** design, approved section by
section in session; not built.

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

- **ERA, INS, IT+ are one-way** — every model of G is a model of G′;
- **DC+, DC−, IT−, HEAVY_DOT and the ligature rules are equivalences** — both directions.

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
- **`P-K3`.** No tier-A soundness failure in the one-way rules (ERA, INS, IT+).
  *Fails if* any structure models G but not G′.
- **`P-K4`.** Where both evaluators answer, they agree. *Fails if* any disagreement is counted.

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
