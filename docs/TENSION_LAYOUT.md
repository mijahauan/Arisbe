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
correspondence-safe by construction. The promising next increments: (1) feed the
tension-minimizing sibling order into ELK as an order constraint (geometry still
ELK's job); (2) generalize the 1-D ordering to 2-D placement; (3) the
constrained taut-rubber-band router for the lines themselves.

The one-sentence version: **the containment tree says where things may live;
ligature tension, pulled taut against the cut boundaries the crossing-sequence
fixes, says where they settle — and in settling, the vertex tree lays out the cut
tree.**
