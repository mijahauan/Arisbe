# Tension layout — the vertex tree as a natural organizing principle

**Status:** design speculation + proof-of-concept (2026-06-07). Not built into
the layout path. This note records a candidate organizing principle for EG
layout and the small experiment that tests whether it behaves. Read alongside
[LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) (§3.1–3.2
natural layout / crossing-sequence invariant) and the memories
`project-render-as-projection-own-dimensionality`,
`project-layout-orientation-and-clustering`.

---

## 1. Two structures, opposite characters

A diagram carries two structures over the same elements:

- **The containment tree** — Dau's `area` is a *function*, so every element is in
  exactly one area; the cuts nest into a strict tree rooted at the sheet. It is a
  hard, discrete partition of the plane: **where an element *may* be.**
- **The vertex / ligature structure** — spots joined by lines of identity, each
  line threading predicate hooks (the incidence given by `ν`). It is a soft,
  continuous web of attractions: identity says "these are the same," and the same
  thing wants to be in one place — **where an element *wants* to be.**

The proposal: make the vertex structure the **organizer** and the containment
tree the **constraint**. One scaffold says where you may live; one field says
where you settle.

## 2. Tension as a variational principle

Model each line of identity as elastic. Total energy

```
E = Σ tension(ligatures)          # attractive: identity pulls together
  + Σ repulsion(unrelated)        # spreading: avoid collapse / overlap
  + boundary terms                # containment walls, area pressure
```

and **minimize E**. Two natural tension laws:

- **energy ∝ length** (a taut rubber band, constant tension) → minimizing total
  *length* → straight **geodesics**; crisp, Dau-like.
- **energy ∝ length²** (a Hooke spring) → smooth **stress-majorization** layouts.

This is the force-directed / stress family (Eades, Kamada–Kawai,
Fruchterman–Reingold) — a well-worn wheel. The EG-specific twist is what makes it
interesting.

## 3. The twist: minimization inside a fixed homotopy class

An ordinary spring layout lets edges cross freely and flip topology. Here the
topology is **given** by the EGI: a line must cross exactly the cuts on its
area-chain (the per-ligature **crossing-sequence** invariant), no others. So we
do **not** minimize Euclidean length — we minimize **geodesic length in the
cut-punctured plane, within the homotopy class the invariant fixes.**

> **A line of identity is a rubber band threaded through a fixed sequence of
> pegs.** The crossing-sequence names which cut boundaries it must pass through,
> and in what order; tension pulls it taut; the result is the geodesic that hugs
> the cuts it must cross and bends around the ones it must not.

The topological invariant stops being an external rule we *check after the fact*
and becomes the **boundary conditions** the tension resolves against. §3.3 goes
from referee to law of motion.

## 4. Why this organizes *both* trees at once

The key consequence: **the vertex tree positions the nodes of the containment
tree.** A cut's placement inside its parent is not arbitrary — it is pulled to
wherever its *internal* lines of identity want to reach *outward*. A deeply
nested taut line drags the stack of cuts it crosses into alignment along its
pull. The soft field shapes the hard scaffold's geometry; the scaffold
constrains the field's routing. The two trees co-determine each other through one
energy instead of being laid out separately.

Three previously-open or hard problems fall out for free:

1. **Sibling cut ordering** (`projection_conventions.sibling_cut_ordering =
   "elk_emergent"` — logically free, currently whatever ELK emits). Order
   siblings to minimize the tension of lines running between them. Principled,
   non-arbitrary, derived from the identity structure. **This is what the
   proof-of-concept tests.**
2. **Conceptual clustering** (`project-layout-orientation-and-clustering`:
   "as graphs get bigger, cluster by relations"). Shared-vertex affinity *is* the
   spring network — identified things attract, so clusters emerge from tension
   rather than from a separate clustering pass.
3. **Orientation.** Reading-axis stops being a hard `elk.direction` knob and
   becomes a weak external **bias field** ("gravity" pulling outer/earlier
   material leftward) layered on the structural energy. Small graphs read
   linearly; large ones fill 2-D — the size-adaptive behavior we want — without
   forcing an axis.

## 5. Other features worth putting in the energy

- **Bending energy** at predicate hooks and spot junctions (penalize sharp turns,
  reward even angular spacing). Generalizes the perimeter-anchor fix
  (`rebuild_ligature_anchors`) and pushes toward **Lombardi-style** drawings
  (smooth arcs, perfect angular resolution) — strikingly close to Peirce's own
  flowing lines. Hook distribution around a predicate becomes an equilibrium, not
  a heuristic.
- **Cut-as-membrane.** Treat a cut boundary as an elastic loop under outward
  pressure from its contents and inward tension from lines passing through. The
  cut *shape* then emerges — a blob that bulges where full and pinches at a
  crossing. Peirce's ovals become physically motivated, and the existing
  rendering wobble gains a cause.
- **Repulsion / minimum-separation** to prevent the degenerate collapse pure
  length-minimization invites, and to satisfy §3.3's distinct-position /
  non-overlap needs.

## 6. How it fits the architecture

Not a rewrite. It slots into "render as projection; own the dimensionality" as
**a different projection/optimizer consuming the same `natural_layout`**, which
already emits this model's inputs: the containment tree (hard constraints),
per-ligature crossing-sequence (homotopy classes / the pegs), incidence (the
spring topology), ports. ELK stays available; a tension solver is an alternative
the way a 3-D projection would be — additive. ELK's own `stress`/`force`
algorithms are a starting substrate, though the homotopy constraint likely needs
an augmented solver.

## 7. The honest hard parts

- **Homotopy preservation during optimization.** A node sliding could shove a
  line across a forbidden cut. Either constrain so it never happens, or
  detect-and-reject per step — and the per-step check already exists
  (crossing-sequence equality / §3.3). The invariant doubles as the optimizer's
  guardrail.
- **Co-optimizing regions and points.** Cut bounds are areas, not points;
  solving shapes + positions together (the membrane especially) is heavier than
  node-only layout.
- **Determinism.** Force methods are initialization-sensitive; layout invariant
  L1 (cross-process determinism) pushes toward stress-majorization with a
  deterministic seed rather than a stochastic spring embedder.

## 8. Proof of concept — sibling ordering by tension

`tools/tension_poc.py` tests the smallest concrete claim from §4.1 on real and
constructed EGIs, **at the structural level only** (no geometry, no solver):

- Build the spring set from `ν` incidence (one spring per predicate–vertex pair).
- Pick an area; its **blocks** are its direct children (sub-cuts, vertices,
  predicates). Each deeper element belongs to the top-level block containing it.
- **Tension(order)** = Σ over intra-area springs of `|pos[block(u)] −
  pos[block(v)]|` for a 1-D ordering of the blocks (the reading axis).
- Find the tension-minimizing order (brute force for few blocks; barycenter /
  median heuristic otherwise) and compare to the baseline (id) order.
- **Invariant check:** the crossing-sequence of every ligature is computed from
  the area tree alone (`presentation_ops.crossing_sequence`) and is therefore
  **identical under every ordering** — proving tension optimizes the *free*
  projection dimension with **zero** effect on correspondence.

The PoC's purpose is to see whether "minimize ligature tension" picks the
*readable* arrangement of the free choices, and to confirm it never touches the
invariant. If it behaves, the next step is wiring a tension-derived sibling order
into the ELK pass as an ordering constraint (still using ELK for geometry), then
later a full constrained tension solver as an alternative projection.

### Results (2026-06-07) — it behaves

- **Constructed two-cluster graph** `(A *x)(B x)(C *y)(D y)(E x)(F y)` — `x` ties
  {A,B,E}, `y` ties {C,D,F}. Tension over the 8 sheet blocks spans **8…30**; the
  minimum (8) is `[(B) • (A) (E) | (F) • (D) (C)]` — the two identity clusters
  cleanly **separate**, each with its vertex. Clustering emerged from tension
  alone, no clustering pass. (Stored order 18 → 8, −56%.)
- **`sowa_cat_on_mat`** (real corpus UoD) — tension over the 5 sheet blocks spans
  **4…11**; the minimum (4) is `[(Mat) • (On) • (Cat)]`: the binary relation
  **On** lands *between* its two arguments with each shared vertex adjacent to its
  other predicate. **Tension recovered the readable "a cat is on a mat" reading**
  of the relation. (Stored 9 → 4, −56%.)
- **Invariant:** in both, every ligature's crossing-sequence is computed from the
  area tree alone and is identical under all orderings — the optimization moved
  only the free projection dimension; §3.3 was never at risk.

Run it: `uv run python tools/tension_poc.py [uod_id]`.

So the principle organizes the free choices toward readability *and* is
correspondence-safe by construction.

### Wired into the layout pass (2026-06-07)

The reusable core is `src/tension_layout.py` (`springs`, `block_of`, `tension`,
`optimize_order`, `sibling_order`). The honored convention
`projection_conventions.tension_sibling_order` (default **off** → output
byte-identical) makes `ELKLayoutEngine._build_area_children` order each area's
sibling blocks by `sibling_order` (tension primary, the structural key as
deterministic tie-break, so isomorphic areas still match), and feed ELK
`considerModelOrder` so the order survives the layout.

**elkjs limitation found & dodged.** `considerModelOrder` crashes elkjs on nested
*ported* groups (the cut interiors) — ~10/18 corpus UoDs failed when it was set
on every area. It is therefore applied at the **sheet (root) level only**, which
is crash-free across the whole corpus and is where free sibling ordering
(disconnected sibling cuts) most commonly lives; nested-cut children are fed in
tension order but left to ELK (best-effort). A defensive retry in
`generate_layout` drops model-order on any residual elkjs failure (never
triggered on the corpus). Exposed for live comparison as
`generate_layout(tension=True)` / the workshop `?tension=true` query. Tests in
`tests/test_tension_layout.py` (incl. corpus-wide no-crash + byte-identical-when-off).

The promising next increments: (1) lift the sheet-only limitation (newer elkjs,
or a post-hoc geometric sibling-slot permutation that needs no elkjs option);
(2) generalize the 1-D ordering to 2-D placement; (3) the constrained
taut-rubber-band router for the lines themselves.

## 9. Tension-driven 2-D placement — PoC (2026-06-07)

The bigger readability win: the Peircean **single-line reading** where a relation
sits *between* its argument vertices (`Cat —•— On —•— Mat`), instead of ELK's
bipartite **two-column** split (predicates in one layer, line-of-identity dots in
the next — the reason `cat_on_mat` currently renders as two vertical stacks).

`tools/tension2d_poc.py` places the incidence graph (predicates + vertices as
nodes, one spring per `ν` incidence) by **stress majorization (SMACOF)** — the
exact tension energy `Σ w_ij(‖p_i−p_j‖ − d_ij)²`, `d_ij` = graph distance,
`w_ij = 1/d_ij²`. Pure numpy (no scipy), deterministic init.

**Result — it produces the reading:**
- `cat_on_mat`: ELK is two columns (predicate x≈32–35, vertex x≈78; total spring
  length 230.5). Stress lays it out as the chain `Mat • On • Cat` with the binary
  relation **On between its two arguments** and total spring length **46.1 (≈5×
  lower)**. The single-line reading emerges from tension alone.

**Honest gap — containment.** The PoC is *unconstrained*: on `peirce_modus_ponens`
(which has cuts) stress places **both** cut-bound elements *outside* their cut, so
§3.3 would refuse. Pure stress ignores the containment tree. So 2-D placement is
not "run a force layout"; it is **constrained** stress that respects the area
tree.

### Wiring plan (the real work, not yet built)

A new opt-in *projection* (alternative to ELK; consumes `natural_layout`,
produces a `LayoutDTO`, attested by §3.3), built in increments:

1. **Hierarchical constrained SMACOF.** Lay out each area's contents by stress,
   **bottom-up**: lay out a cut's interior in its own frame, size the cut box to
   fit, then treat the cut as a single node in its parent's stress layout.
   Containment holds by construction (each area solved in its own frame; a cut is
   atomic to its parent). This is "the vertex tree positions the cut tree" made
   literal.
2. **Cross-boundary springs.** A line of identity from inside a cut to outside
   attaches to the cut's boundary as a port; the parent layout pulls the cut
   toward the outside end, the child pulls the inside end toward the boundary —
   the coupling that lets tension shape the nesting.
3. **Non-overlap + routing.** Add repulsion / min-separation (stress alone lets
   nodes coincide), then route lines with the existing cut-aware router so the
   crossing-sequence is realized exactly.
4. **Guardrails.** Deterministic init (L1); §3.3 attestation as the per-result
   gate; behind a convention flag (default ELK), opt-in `?engine=tension` for
   live comparison — same pattern as `?tension` / `?direction`.

Start with the cut-free and single-cut cases (where the PoC already wins), prove
each increment against the corpus, and only then make it selectable.

### Built — increment 1 (2026-06-07)

`src/tension_engine.py` (`TensionLayoutEngine`) implements the plan as an opt-in
projection; **ELK stays the default**.

- **Hierarchical constrained stress.** Each area is laid out in its own frame by
  `tension_layout.stress_majorize` over its direct children (sub-cuts are atomic
  sized boxes); a cut enters its parent as one box sized to its interior, so
  **containment holds by construction**.
- **Crossing-point proxies.** A line crossing an area's boundary is an edge to a
  proxy node; after the solve the proxy is projected onto the boundary and
  becomes the crossing point used both by the parent (to pull the cuts together)
  and by ligature routing. The proxy set is *given* by each line's
  crossing-sequence — tension only places it along the boundary.
- **Left-to-right.** Each area is rotated so its principal axis is horizontal
  (boxes recomputed from the rotated content stay axis-aligned), then box
  overlaps are removed by order-preserving uniform scaling. `cat_on_mat` →
  `Cat —•— On —•— Mat` on one horizontal line, On between its arguments.
- **Determinism (L1).** Children and proxies are sorted; the SMACOF init is
  fixed — same EGI → same layout.
- **§3.3-gated with ELK fallback.** Today **17/18** corpus UoDs attest directly;
  the rest (a line clipping a sibling cut — routing refinement is future work)
  fall back to ELK at the service, so `?engine=tension` never fails.
- **Exposed** as `generate_layout(engine="tension")` and the workshop
  `?engine=tension`. Tests: `tests/test_tension_engine.py` (between-arguments,
  containment, corpus attest-most + determinism, service fallback) and the
  `tension_layout` stress core in `tests/test_tension_layout.py`.

**Next on this engine:** the cut-aware router for lines so the last few graphs
attest (lift the 17/18 to full coverage); non-overlap tuning; then 2-D placement
quality (the 1-D principal-axis reading generalized).

## 10. Ligature-as-thread layout — PoC (2026-06-07)

The deeper lesson from `dau_theorem_proving`: its graph is a single chain
`P — x — Q — y — R — z — S` threading 5 nested cuts (every vertex degree-2). The
node-placement engines (ELK's layers, tension's stars around a vertex *point*)
can't make that chain collinear, because they place each predicate/vertex
independently and draw each incidence as its own stub. The fix is to make the
**line of identity the primary object**: lay the *thread* as one taut path
through the nested areas and hang the predicates on it.

`tools/thread_layout_poc.py` does this for a single monotone thread: extract the
ordered chain, place it collinear (one axis), size each cut bottom-up around its
contiguous run of the thread (so the cuts telescope and nest by construction),
and route each incidence along the axis through the cut crossings. Result on
`dau_theorem_proving`:

```
S@0 — •@90 — R@180 — •@270 — Q@360 — •@450 — P@540   (all y=0)
c_a0ab[-28,28] ⊂ c_a53b[-50,208] ⊂ c_3197[-72,230] ⊂ c_8b47[-94,388] ⊂ c_2cc6[-116,568]
```

One straight collinear line of identity through 5 telescoped cuts, each crossed
exactly once, **§3.3-attested in Dau and Peirce**. This is the straight
pass-through the example called for, and it follows from one principle (the
thread pulled taut through the containment nest) with no special cases.

> **Scope note (2026-07-16, sweep #2).** The thread/tree fast paths place only
> the line of identity and box the cuts around it, so a cut with an **empty
> area** — no thread content to anchor it — would box at the origin, atop the
> thread. The world-scroll residence makes off-thread empty cuts routine (the
> hold, the scars), so `generate_layout` now takes the hierarchical placement
> (whose sibling overlap-removal handles content-free cuts) whenever the graph
> carries an empty cut; the thread/tree paths remain for pure lines of
> identity, unchanged.

**Variable spacing (cut area ∝ length²).** Peirce ovals are √2-grown to bound
their contents, so cut area scales with the *square* of the thread length — a
uniform step wastes it. Each gap is instead sized to only what must fit there:
label clearance always, plus one nesting inset per cut boundary that actually
crosses between the two elements. So same-area neighbours sit close and a gap
widens only where boundaries pass:

```
S@0 —(54,1×)— •@53 —(26,0×)— R@79 —(76,2×)— •@154 —(26,0×)— Q@180 —(54,1×)— •@234 —(26,0×)— P@259
```

(gap, #crossings). Thread length **540 → 260**, outer cut width 684 → 404 — a
~4× cut-area reduction, still collinear and §3.3-valid. The spacing reflects the
topology, not a magic constant.

### Wired into the engine (2026-06-07)

`TensionLayoutEngine.generate_layout` now dispatches: if the graph is a **single
thread** (`tension_layout.extract_thread` — one connected line of identity, no
branches), it lays it out collinearly (`_thread_layout`, the PoC logic with
variable spacing); otherwise it uses the §9 hierarchical node placement. The
thread path **self-attests** and falls through to hierarchical on a non-monotone
thread that doesn't realize its crossing-sequence. ELK remains the default
engine; this is still `?engine=tension`.

Corpus: **10 of the 11 single-thread graphs** get the collinear thread layout
(the 11th is non-monotone → hierarchical); all 18 attest at the engine (no ELK
fallback needed). `cat_on_mat` reads `Cat —•— On —•— Mat`. Tests in
`tests/test_tension_engine.py` (single-thread collinear; variable spacing;
branch graph falls back yet still attests).

**Remaining generalization:** multiple threads; branch points (degree-≥3
vertices); non-monotone threads (in-and-out of cuts); composing several threads
+ their shared cuts. The thread becomes the unit the tension solve places, with
containment as the nest it threads — the node-placement engine reframed around
ligatures.

The one-sentence version: **the containment tree says where things may live;
ligature tension, pulled taut against the cut boundaries the crossing-sequence
fixes, says where they settle — and in settling, the vertex tree lays out the cut
tree.**

## 11. Branch points — the thread becomes a taut tree (2026-06-07)

The first frontier case after the single thread: a line of identity that **forks**
to three or more predicates (a degree-≥3 junction). Its incidence graph is no
longer a path but is still **one connected acyclic tree** — so the thread
generalizes to a small tree pulled taut through the cut nest. `extract_tree`
(`src/tension_layout.py`) certifies the shape (`|E| = |V|−1`, one component) and
fixes the node order; `TensionLayoutEngine._tree_layout` realizes it, dispatched
after `extract_thread` and before the §9 hierarchical fallback.

The construction, faithful to the thread's ideas:

1. **One global taut embedding.** The incidence graph (predicates + vertices, one
   node each) is laid out by global stress majorization. Each ligature's
   crossing-sequence is inserted as **chained proxy nodes** between the predicate
   and the vertex, so a deep incidence relaxes to a straight run through exactly
   the boundaries it must cross — a path straightens, a junction fans.
2. **Per-edge ideal lengths (compaction).** Every edge is given its *own* ideal
   length — two half-extents (a predicate's label, a vertex's dot, a crossing
   proxy's small boundary hop) plus a gap — via `stress_majorize(edge_len=…)`
   (weighted shortest-path distances). So each edge is only as long as it must be:
   a crossing-proxy hop stays short instead of inflating to a full uniform "scale"
   the way unit-hop graph distance did. This is the thread's "each gap only as
   wide as what must fit" carried into 2-D, and it is what keeps a branched
   ligature from spreading far past what it needs.
3. **Cut boxes bottom-up** (the shared `_box_cuts`): each cut is the bounding box
   of its drawn contents plus an inset, so the boxes nest by construction.

Stress alone ignores containment (§9's "honest gap"): it can pull an *outside*
junction into a cut's hull, because more of its neighbours sit inside. So after
the solve, any node that landed inside a cut it does **not** belong to is pushed
to that cut's nearest boundary; the boxes are re-derived and the push repeats to a
fixpoint. Each ligature crossing is then snapped to where the straight
predicate→vertex segment meets the cut box (`_seg_box_hit`), so the
crossing-sequence is realized geometrically. The whole result **self-attests**
(§3.3).

**Two embeddings, tried in order.** A tight junction with neighbours on both
sides of a cut can defeat the *compact* embedding: pushing the junction out one
side leaves its outside line crossing the cut. So the engine tries the compact
(per-edge-length) embedding first and, if it doesn't attest, falls back to the
**unweighted** embedding (uniform graph-distance shape) *compacted to its minimal
non-overlapping size* by an order-preserving uniform scale (`_compact_scale`) —
the balanced fan at the smallest scale, no magic constant — then to §9
hierarchical placement. Same try/attest/fallback discipline as `_thread_layout`.

**Result.** All **5** corpus branch graphs lay out as clean, *compact* taut trees
and attest at the engine — so the whole corpus attests with **no ELK fallback**
(18/18, up from 17/18). The two predicate-fork stars (`ternary_relation_challenge`,
`peirce_complex_scope`) and the cross-boundary vertex-forks the hierarchical
engine drew awkwardly (`dau_2006_p112_ligature`, `peirce_modus_ponens` — the
junction stranded outside its cuts with long lines reaching back in) now settle
the junction **against the cut boundary**, the predicates fanning into their cut,
via the compact embedding. `roberts_domain_modeling` (a degree-4 junction across
two cuts) takes the compacted unweighted fallback — the balanced fan, now ~513×562
instead of the ~810×1040 it first produced. Both layout engines are selectable in
the **workshop** *and* the **Organon** archive (`?engine=tension`). Tests in
`tests/test_tension_engine.py` (tree path taken + attests for every branch graph;
the push keeps an outside junction outside its cuts; the branch tree stays compact
with no predicate-on-vertex overlap) and `tests/test_tension_layout.py` (the
weighted vs unweighted `stress_majorize` paths).

**Two refinements (2026-06-07b).**

- *Oval cuts (now backed by shape-aware §3.3).* For an oval style (Peirce/Sowa)
  the renderer draws the cut as an ellipse *inscribed* in the cut box, smaller
  than the box. The principled rule (see `LINEAR_GRAPHICAL_CORRESPONDENCE.md` L7):
  **the drawn shape is authoritative for containment** — §3.3 reads "inside" off
  the inscribed ellipse, not the box (`presentation_ops.point_in_cut` /
  `bounds_in_cut` / `count_cut_crossings`, keyed on `style.cut_shape`). So the
  layout *must* place content inside the ellipse, and the shared `_box_cuts`
  (and the hierarchical `_layout_area`) grow each cut box ∝ its content (the √2
  rule, the same `k = (√2−1)/2` as `ELKLayoutEngine._oval_padding`), bottom-up.
  This is no longer an *episodic accommodation* of the style — it is the layout
  meeting a constraint the attestation now actually checks, so the shape is
  immaterial to which area an element is in, and a previously-latent hole (a
  Peirce render with an element visually outside its cut yet passing a
  box-based §3.3) is closed.
- *Alpha defers to ELK.* The tension engine exists to lay out the **line of
  identity**. A pure-Alpha graph (no predicate–vertex incidence — `springs(egi)`
  empty, e.g. `theorem_praeclarum`) has nothing for tension to organize, so a
  "tension" layout of it is meaningless; `generate_layout` defers to ELK rather
  than impose a node placement that is just a worse ELK. (So selecting *Tension*
  on an Alpha proof shows the ELK layout — the meaningful one.)

**Remaining generalization:** multiple threads (a *forest* — `mixed_quantifier_complex`)
and cyclic ligatures (`beta_converse_mp`), both still hierarchical; composing
several trees + their shared cuts; non-monotone threads. The unit the tension
solve places is now the ligature *tree*; next it becomes a *forest* sharing a cut
nest.

## 12. Top-down crossing reconciliation — the "slash" fix (2026-06-08)

The hierarchical placement (§9) sized and placed everything bottom-up, including
each line's **cut-boundary crossing point** — but at that moment the *outside*
endpoint of the line wasn't placed yet, so a crossing could land on the side of
the box *away* from where the line was headed, and the line would slash back
across the box to reach its vertex. The `group_identity` proof showed it
starkly: a "theta" graph (two lines `x`,`y` joined by three parallel relations —
two `M`s and a deep `=`), where the `=`'s line slashed corner-to-corner through
the double cut. (A wrong "defer to ELK for these graphs" fix was tried and
reverted — the user prefers the tension look and wants it rendered.)

The fix is a **top-down reconciliation pass** in `_hierarchical_layout`, after
everything is placed: for each predicate→vertex line, re-snap each crossing to
where the *straight* predicate→vertex segment meets that cut's box
(`_seg_box_hit`, the same primitive the tree layout uses). The line then
enters/exits every cut on the side **facing its endpoint** — no slash. The
crossing stays on the boundary, so the crossing-sequence / §3.3 containment is
unchanged (only *which* boundary point moves); a crossing whose straight segment
misses the box keeps its bottom-up value. Verified visually (render→PNG): the
`=` now sits cleanly in its double cut with both lines exiting toward `x`,`y`;
`barbara`'s scroll lines exit cleanly; `beta_converse_mp`'s X-crossing (the
converse — the crossing *is* the meaning) is unaffected. The genuine
multi-relation tangle of the denser proof states (several relations sharing two
vertices) remains — that's the §11 forest frontier, not the slash. 26
tension/layout tests + the corpus attest-most test green.
