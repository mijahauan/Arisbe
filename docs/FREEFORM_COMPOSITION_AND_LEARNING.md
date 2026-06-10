# Freeform composition, fix-as-read, and correspondence learning

A design arc for the Ergasterion composing phase, decided in conversation
2026-06-10. Companion to `docs/COMPOSITION_WORKFLOW_SPEC.md` (which fixes the
phase model) — this records *what composition becomes* and why.

## The arc, in three moves

1. **Freeform composition.** While composing the base graph, elements are **ink,
   not logic**: graphical marks (labelled spots, lines, closed cut-curves) that
   you position freely, with no live EGI and no live interpretation. The order of
   placement carries no meaning; the view holds only presence, position, and
   removal (spec §2.3). A cut is just a drawn curve — erase it and its contents
   stay exactly where they are; drag a mark across a boundary to change its area.
   The structural rigidity of the old live-EGI model (a cut *owns* its contents,
   well-formedness refusals on every action) is gone, because there is no
   structure yet — only geometry. This is the project's own thesis applied to
   composition: *logic in pictures*, and *the drawn shape is authoritative for
   containment* (see those memories).

2. **Fix = read.** Crossing gate ① **reads the drawing into a determinate sign**:
   run `eg_reader.read_drawing(dto)` → recover the EGI (area tree + incidence +
   argument order, *from geometry alone*) → check syntactic validity → show the
   linear forms ("tell you what it says") and §3.3-attest. Composition is silent;
   fixing is when the picture *speaks*. (On-demand "read it now" gives feedback
   before committing, so the author is never flying blind.)

3. **Challenge mode — correspondence, learned by doing.** Present a linear form,
   challenge the author to draw it freehand, then `read_drawing` their drawing and
   compare to the parsed target with `same_graph`. The **discrepancy report** is
   the pedagogy. This is the human-facing twin of §3.3: the engine attests *its*
   drawings; this trains the *human's*. The grader is isomorphism (`same_graph`),
   so it rewards **structure, not appearance** — a correct drawing may look nothing
   like the canonical render, which is itself the lesson (one linear form has many
   correct drawings). The tomos corpus (87+ examples) is a ready challenge bank.

These share one new surface — a freeform drawing canvas — and one new logical
piece — a **legible EGI diff** (the discrepancy report). Almost everything else
exists: the linear parsers (target), `eg_reader.read_drawing` (drawing→EGI),
`same_graph` (equivalence), `reading_matches_egi` (reading↔EGI).

## De-risk findings — `read_drawing` on human-messy geometry (2026-06-10)

Existing `test_eg_reader.py` proves the reader round-trips *clean engine layouts*
corpus-wide. The open question for freeform was whether it survives *human*
placement. Stress-tested directly (now pinned in `test_eg_reader.py`
`TestFreeformRobustness`). The reader's algorithm is **sound and faithful** — it
reads exactly what is drawn. The gaps are all imprecision/validity, and bounded:

| Case | What the reader does | Verdict | Fix (UI/validity, not the algorithm) |
|---|---|---|---|
| Spot 1px inside / 1px outside a cut edge | classifies by the exact drawn point (inside / outside / on-edge⇒inside) | **correct** — drawn shape is authoritative; but human *intent* near a line is ambiguous | **snap** placement clearly inside/outside near a boundary (or claim a margin) |
| Connecting line stops short, drifts toward a *decoy* vertex | incidence = **nearest** endpoint → reads the decoy | **brittle** — the one real fragility | require the line to **touch** a hook/vertex within tolerance; **snap** endpoints on draw; flag an unconnected line |
| Two cuts **overlap** (neither nests) | both read as sheet siblings; a spot in the overlap is assigned to one | ill-formed: a non-tree area | **prevent or flag** overlapping cuts at fix ("cuts must nest or be separate") |
| Lone relation, no line drawn | reads as 0-ary (incidence `[]`) | faithful, but maybe unintended | **validity at fix**: "relation P has unwired hooks / arity N expected" |

**Conclusion:** no reader rewrite. The freeform model needs (a) **draw-time
snapping** — line endpoints to hooks/vertices, spot placement to clearly-in/out of
a cut; and (b) a **fix-time validity pass** that catches the drawings the reader
*can* read but that aren't well-formed EGs (overlapping cuts, unwired hooks,
dangling lines) and reports them in EG vocabulary. Both are bounded.

## Visible, unambiguous containment regions (no invisible boundary)

The author's requirement (2026-06-10), and a correctness invariant, not just UX:

> **The region that reads as "inside a cut" must be one shape, *shown*, and
> identical to what the reader uses. There is no second, invisible boundary.**

The trap is a divergence between the *decorative* drawn curve and the *containment
region* `point_in_cut` uses. Today (`presentation_ops.point_in_cut`):
- **oval/circle** → inside the inscribed ellipse, and the renderer draws that same
  ellipse → region == drawing, consistent. Only the general at-the-edge question
  remains.
- **box / rounded-rectangle** → inside the **bounding box**, but the Dau render is
  a `<rect rx=cut_corner_radius>` (rounded), so the rounded-away corner reads
  **inside** (box) yet looks **outside**. That corner *void* is the "guess where
  the invisible boundary is" frustration.

  Why it is dormant *today* but a real freeform concern: `simple_svg_renderer`
  deliberately keeps decorative deviation (corner rounding, hand-drawn wobble)
  **under the engine's content clearance** — §3.3 reads the idealized DTO geometry,
  not the drawn stroke, and the engine grows cut boxes with margin, so no
  *engine-placed* element ever lands in a void. **Freeform human placement breaks
  that guarantee** — a person can drop a mark squarely in the corner void where the
  engine never would. Fix: **one curve per cut, used for both render and
  containment** (make `point_in_cut` shape-exact for the rounded corners, or render
  a true box), so the shown region *is* the read region with no clearance
  assumption. Oval already satisfies this; rounded-rectangle is the gap.

Design consequences for the freeform canvas:
1. **One curve per cut for render *and* containment** — eliminate the box/rounded/
   oval divergence in *what counts as inside*.
2. **Render the cut interior as a filled/translucent region** (the exact
   `point_in_cut` area), not a thin outline to place *near*. "Inside" becomes "on
   the tinted area," unambiguous by construction; wobble is pure boundary
   decoration.
3. **The cut line is a visible band = the snap threshold / no-drop zone.** Dragging
   a mark snaps it clearly inside (into the tint) or outside, never into the band.
4. **Live area feedback on drag** — name where the mark will land ("inside cut C" /
   "on the sheet") *before* release, so the boundary is confirmed up front.

This folds into build step 1 (snapping + validity) and the canvas (step 2): the
shaded region is what makes the snap legible rather than magic, and it is the same
region the reader and the renderer share.

## Build order

1. **Visible containment + snapping + validity (the de-risked core).** First make
   the containment region one shown shape (§"Visible containment regions" above):
   verify/fix the rounded-rectangle box-vs-render gap, render cut interiors as
   filled regions, add live area feedback. Then draw-time endpoint/containment
   snapping and a `read_drawing`-based fix-time validity pass with legible
   messages. This is what makes freeform usable and "fix = read" trustworthy.
2. **Freeform drawing canvas.** Replace the composing-phase palette's typed
   `composition_ops` with place/drag/erase of marks on a free `LayoutDTO`; no live
   EGI; live linear forms go silent until fix.
3. **The legible EGI diff** (the discrepancy report): align two EGIs by relation
   label + role (generic vertices by incidence), diff area trees and per-relation
   incidence/order, phrase in EG terms (containment / scope / incidence / order /
   missing / extra). Reused by both fix-time validity *and* challenge mode.
4. **Challenge mode** in Ergasterion: pick a tomos linear form, hide its drawing,
   grade the freehand attempt with `same_graph` + the diff. Difficulty gradient
   straight from the corpus: single relation → nested cuts (negation, the scroll)
   → Beta with a shared line crossing a boundary (∀x(P→Q)), where scope errors are
   the gold.

Building challenge mode *is* the ongoing stress test of `read_drawing` on human
input — the two efforts reinforce each other.
