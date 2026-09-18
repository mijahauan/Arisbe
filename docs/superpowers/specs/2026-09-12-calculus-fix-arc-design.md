# The calculus fix arc — making the engine stay inside what Dau states

**Date:** 2026-09-12 · **Branch:** `calculus-fix-arc`, off `main` (`3b237c2`) · **Status:** BUILT
2026-09-17. All eleven tasks done; six engine defects fixed at the rule, Def 12.5 enforced at
construction, both stored non-EGIs repaired. See the eighteenth arc's block at the head of
[CURRENT_PLAN.md](../../../CURRENT_PLAN.md) for the outcome, what remains ledgered, and the three
findings that await the author. §4 step 7 (the alphabet question) is still the author's to decide.

**Predecessors:** the property suite
([spec](2026-09-10-calculus-property-suite-design.md),
[plan](../plans/2026-09-10-calculus-property-suite.md)) and its ledger
([runs/RUN_CALCULUS_SUITE_LEDGER.md](../../../runs/RUN_CALCULUS_SUITE_LEDGER.md)).

## 1. Why, and the standing rule

The suite established that no rule application Dau licenses changes a graph's meaning. It also
established that the engine performs moves Dau does not license, and that several of those change
meaning. The author's rule governs this arc:

> "we MUST remain Dau-compliant, testing in a manner that ensures this, and vigilant for examples
> that stress our implementation."

So every fix here is **proved, not asserted**: each one makes its ledger entry fail with "shrink
this entry", or flips a strict xfail to XPASS. Nothing is loosened to make a fix pass, and every
claim cites Dau by definition and page (`docs/references/mathematical_logic_with_diagrams.pdf`,
PDF page = book page + 10).

## 2. The author's four decisions (2026-09-12)

1. **Enforce at the engine choke points only.** Each rule's `check_preconditions` in
   `formal_transformation_rules` / `ligature_manipulation_rules`. The interaction protocol already
   routes through them (`ITPlusInteraction._get_rule` returns `IterationRule`), so one fix covers
   the protocol path the chains replay and any direct engine call. The law lives in one place.
2. **IT−'s copy condition goes in `DeiterationRule`,** not in the isomorphism engine. The engine
   keeps its single meaning — structural match — because challenge grading, drawing→EGI and
   `same_graph` all depend on it.
3. **The ligature survivor is chosen by canonical signature.** Deterministic for a given graph
   whatever the process or hash seed, with no change to the protected `TransformationContext`.
4. **The corpus is repaired by hoisting each offending vertex to the least common area of its
   uses** — the reading the parsers already apply.

## 3. The instrument comes first

Nothing in this section touches `src/`. Its purpose is that each engine fix afterwards is judged
by a suite that can tell a real repair from a partial one. Measured before writing this: the
structure layer checks six rules for EGI-hood and maps only (label `egi-only`), and a no-op
`RETRACT_LIGATURE` passes both structure and soundness.

1. **Real postconditions for those six rules** (the four ligature rules, split, merge): the result
   differs from the source, and each rule's own expected change in element count — split +1 vertex
   and +1 identity edge; merge and retract lose vertices and identity edges; move-branches and
   rearrange preserve counts. Re-pin the structure extent.
2. **A named stress tier**, beyond tier A's bounds (at most 3 elements by default, 4 at exhaustive,
   at most 2 cuts), run through all four layers, with its own counted extent:
   - `*x ~[ (P x) ~[ (Q x) ] ]` — the scroll carrying a line;
   - `*x (P x) ~[ ~[ (P x) ] ]` — deiteration across two cuts;
   - `*x *y (R x y) ~[ (R y x) ]` — an IT− match with the arguments swapped;
   - `*x *y (P x) ~[ (= x y) (P y) ]` — the Θ-linked copy;
   - parity at depth 3 and 4, e.g. `~[ ~[ ~[ (p) ] ] ]`;
   - a directly built graph carrying an alphabet and a quotation oval (tier A has no
     maps-bearing records);
   - the name-against-name IT− case;
   - `*x ~[ ]` with an edge insertion.
3. **`INS_EDGE`'s candidate moves enumerated**, so Dau's edge insertion onto existing vertices
   (p.165) lands as counted INCOMPLETE rather than only a table row.
4. **The refusal layer's `not:{rule}` label split by abstention reason**, and the four broad
   classifiers (`heavy-dot-negative-only`, `vertex-era-positive-only`,
   `vertex-era-erases-a-line-with-its-edges`, `merge-vertices-erases-a-constant-vertex`) narrowed
   to the mechanism each reason names, so a same-entry key trade cannot pass.

## 4. The engine fixes, in order

Each is one commit, verified before the next begins. Steps 1–4 edit protected modules; confirm
each with the author immediately before making it.

### 1. IT+ may not copy into its own selection
`IterationRule.check_preconditions` (`formal_transformation_rules.py`) checks only that the
destination is enclosed by the source. Dau's Def 15.2 (p.164, 166) also requires `c ∉ Cut₀`: the
destination may not be one of the cuts being copied. Add that condition, computed over the
selection's downward expansion.
**Proof:** `it-plus-into-its-own-selection` (refusal) and
`it-plus-into-its-own-selection-changes-meaning` (soundness, 706 UNSOUND at exhaustive) both fail
with "shrink this entry"; `~[ ~[ ] ]` no longer becomes `~[ ~[ ~[ ] ] ]`.

### 2. IT− may erase only a genuine copy
`DeiterationRule` delegates to `IsomorphismValidator.validate_deiteration_candidate`, which asks
for a structural match only. Per Dau Def 15.2 (p.166), a copy's edges reach either the copies of
the source's vertices or, through `e_{v,w}` with `wΘv`, the very same vertex. Filter the engine's
matches — each is `(area, matching_subgraph, IsomorphismMapping)` with a `vertex_mapping` — and
reject any where a selected edge reaches a vertex outside the selection that is not the same
vertex in the source.
**Proof:** the three strict xfails in `tests/test_calculus_it_minus_controls.py` flip to XPASS
(and so must be removed); `it-minus-erases-a-copy-of-another-line` and its `-changes-meaning`
twin shrink. The name-against-name case
`(Q "a") (Q "b") ~[ (P "b") ] ~[ ~[ (P "a") ] ]` must be refused.

### 3. The ligature rules
Four faults, all in `ligature_manipulation_rules.py`:
- **One context, including the edges.** `RetractLigatureRule.check_preconditions` requires the
  *vertices* to share a context but never the identity *edges*. Lemma 16.3 (p.173) requires
  `ctx(w) = c = ctx(f)` for every vertex and every edge of the ligature. That omission is why
  `*x *y ~[ (= x y) ]` retracts to `*x ~[ ]`, true becoming false. Add the edge condition here and
  in `LigatureRearrangementRule` (Def 16.4, p.174).
- **A deterministic survivor.** `apply_transformation` takes `list(context.selected_subgraph)[0]`
  off a frozenset. Choose by `canonical_signature` instead.
- **Generic vertices only.** Def 24.10 (p.270–272) states the ligature rules for generic vertices;
  the only rule that joins constants is the Constant Identity rule, and it requires the same name.
  Refuse a selection carrying a constant vertex.
- **MOVE_BRANCHES' side condition.** Lemma 16.1 (p.169–171) needs `v_aΘv_b` to hold without the
  hook being moved; the proof's deiteration step is otherwise unlicensed. Refuse when the edge
  carrying the hook is the only link witnessing `v_aΘv_b`.

**Proof:** `ligature-rules-take-a-join-deeper-than-its-vertices`,
`retract-ligature-erases-a-constant-vertex`, `merge-vertices-erases-a-constant-vertex` and
`move-branches-moves-the-identity-edge-it-moves-along` shrink; the suite's `InOrder` workaround in
`tests/calculus_apply.py` is retired, and the results stay identical across hash seeds.

### 4. The dominating-nodes helper
`egi_core_dau._context_dominates` tests the relation backwards and passes any edge on the sheet.
Def 12.5 (p.125) requires `ctx(e) ≤ ctx(v)`: the vertex's context is the edge's or encloses it.
Fixing the helper corrects three call sites — `has_dominating_nodes`, `replace_vertex_on_hook`
(Def 12.9, which today refuses lawful hook moves) and `add_vertex_to_ligature` (Def 12.14).
Correct the stale comment in `derived_rules.py` that called one of those refusals right.
**Proof:** `core-has-dominating-nodes-inverted` shrinks; the hand test that a lawful inner-to-outer
hook move is accepted passes.
**Not in this step:** enforcing Def 12.5 in `__post_init__`. That waits for step 6, or the two
corpus graphs stop loading.

### 5. `normalize_constants` places its survivor lawfully
`vertex_scope.normalize_constants` (unprotected) keeps whichever twin's id sorts first, where it
sits, and never hoists. Two same-name spots in sibling cuts therefore normalize to a non-EGI.
Hoist the survivor to the least common area of the twins' areas, which is the module's own stated
"outward only" rule. Its only caller is `world_scroll.discharge_episode`.
**Proof:** new cases in `tests/test_vertex_scope.py` for sibling cuts and for a survivor deeper
than a twin's edge; both results are EGIs.

### 6. The two corpus graphs
`bfo_core:current` (the generic vertex `v_x26`, 4 edge–vertex pairs) and `colore_field:current`
(`v_zero` and `v_one`, 8 pairs) are not EGIs. Measured while designing this: running
`vertex_scope.hoist_vertices_to_lca` on each makes it an EGI **and all three of its round trips
then hold**. Repair both through a tool script, saving via `TomosService`, so §3.3 attests at the
write.
**Proof:** the `corpus-graph-not-an-egi` ledger entry empties; all six `KNOWN_BROKEN` entries for
these graphs retire; `test_tomos_parsing`'s pin moves from `(156, 9, 6, 141)` to `(156, 9, 0, 147)`.
**Then, and only then:** enforce Def 12.5 at construction, so no non-EGI can enter again.

### 7. The alphabet question — its own decision sitting
Task 11c was blocked and reverted: wiring `egif_parser_dau._finalize_alphabet_and_rho` broke 15
tests, for two reasons that are themselves Dau-compliance findings. EGIF tests use one relation
name at two arities, which Def 12.6 (p.126) forbids, and the core's builders do not grow the
alphabet the way the six rules do. Two decisions belong to the author, and this spec does not
pre-empt them:
- Does the EGIF parser refuse a name used at two arities, and what becomes of the tests that
  assert the current behaviour?
- Do the core's builders extend the alphabet (touching protected `egi_core_dau`), or is the
  alphabet derived rather than stored?

Bring both to the author when the arc reaches this step.

## 5. Verification discipline

- The default calculus suite after every step; the full suite once before the arc closes.
- A step is done when its ledger entries have been **removed** (not edited) and the extents
  re-pinned, with the diff read.
- Where a fix changes an engine refusal, the suite's own `legal()` is not touched: if the two now
  disagree the other way, that is a finding, not a licence to adjust `legal()`.
- The exhaustive mode is run once, at the end, before the write-up (about 2 h 41 min at the
  measured budget).
- Expected outcomes, recorded before the work: P-K2 and P-K3 should become HELD for the fixed
  rules. If a fix does not move its ledger entry, the fix is wrong or the entry was mis-adjudicated
  — investigate, do not delete the entry.

## 6. Out of scope

The INCOMPLETE departures that remain after the unsound ones are fixed: HEAVY_DOT's negative-only
insertion and fixed id, DC+ ignoring its target, ERA auto-closing a vertex selection, and the five
other missing entry points (ORIENT_IDENTITY, LIGATURE_VERTEX, CONSTANT_IDENTITY,
CONSTANT_EXISTENCE, SEPARATE_CONSTANT). They are ledgered, counted, and none changes meaning.
Also out of scope: `semantic_game`'s co-denotation and `=` gaps, and the tracemalloc rewrite of
`test_memory_stability`.
