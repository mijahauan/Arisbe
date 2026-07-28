# Freeform composition, fix-as-read, and correspondence learning

A design arc for the Ergasterion composing phase, decided in conversation
2026-06-10. It accompanies `docs/COMPOSITION_WORKFLOW_SPEC.md`, which fixes the
phase model; this document records *what composition becomes* and why.

## The arc, in three moves

1. **Freeform composition.** While you compose the base graph, elements remain
   **ink, not logic**: graphical marks (labelled spots, lines, closed cut-curves)
   that you position freely, with no live Existential Graph Instance ([EGI](GLOSSARY.md#egi)) and no live interpretation. The order of
   placement carries no meaning; the view holds only presence, position, and
   removal (spec §2.3). A cut amounts to a drawn curve — erase it and its contents
   stay exactly where they are; drag a mark across a boundary to change its area.
   The structural rigidity of the old live-EGI model (a cut *owns* its contents,
   well-formedness refusals on every action) falls away, because no structure
   exists yet — only geometry. Composition here obeys the project's own thesis:
   *logic in pictures*, and *the drawn shape is authoritative for
   containment* (see those memories).

2. **Fix = read.** Crossing gate ① **reads the drawing into a determinate sign**:
   run `eg_reader.read_drawing(dto)` → recover the EGI (area tree + incidence +
   argument order, *from geometry alone*) → check syntactic validity → show the
   linear forms ("tell you what it says") and §3.3-attest. Composition stays
   silent; at fixing the picture *speaks*. (On-demand "read it now" gives feedback
   before committing, so the author never flies blind.)

3. **Challenge mode — correspondence, learned by doing.** Present a linear form,
   challenge the author to draw it freehand, then `read_drawing` their drawing and
   compare to the parsed target with `same_graph`. The **discrepancy report** is
   the pedagogy. This is the human-facing twin of the correspondence check (§3.3): the engine attests *its*
   drawings; this trains the *human's*. The grader is isomorphism (`same_graph`),
   so it rewards **structure, not appearance** — a correct drawing may look nothing
   like the canonical render, which is itself the lesson (one linear form has many
   correct drawings). The [tomos](GLOSSARY.md#tomos) corpus (87+ examples) is a ready challenge bank.

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
*can* read but that aren't well-formed Existential Graphs ([EGs](GLOSSARY.md#eg)) (overlapping cuts, unwired hooks,
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
  **under the engine's content clearance** — §3.3 reads the idealized Data Transfer Object ([DTO](GLOSSARY.md#dto)) geometry,
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

## Exact correspondence: the cut *is* its curve (the target architecture)

> **Canonical: [docs/EXACT_CORRESPONDENCE.md](EXACT_CORRESPONDENCE.md)** — the
> architecture and phased implementation plan live there. The summary below is the
> freeform-facing view; keep the two in sync.

**Decided with the author 2026-06-10.** The deepest version of the requirement
above, and the architecture the build should aim at from the start — refine the
*model*, not the *approximation*. This generalizes beyond freeform: it is the
geometric realization of the whole §3.3 invariant.

**The diagnosis.** Imprecision lives in exactly one place, and it is eliminable.
There are three layers, and only the middle one approximates:
1. **The logic (EGI)** is *topological* — "X is inside C" is a partition of
   elements into nested areas. Exact, pixel-agnostic; it does not want coordinates.
2. **The drawing** is a set of *closed curves*. By the **Jordan Curve Theorem**,
   any closed curve — box, oval, hand-drawn wobble — has a precise inside and
   outside. So "inside the cut you drew" is also exact, for any shape, for free.
3. **The geometry layer** (`point_in_cut`) is the *only* approximator, and only
   because it tests a **proxy shape** (bounding box / inscribed ellipse) instead of
   the **actual drawn curve**. Delete the proxy and the gap closes.

**The model.** A cut *is a closed path* — the literal points the renderer draws —
not a `BoundingBox`. Containment is **point-in-that-path** (ray-cast / winding
number): exact, cheap, style-agnostic. The renderer draws the path; the test uses
the same path; *what you see is what reads*. (This also recovers Peirce: a cut is a
**boundary** — the *sep*, a line you cross — not a region; a box was already a small
betrayal of that.)

**The browser as the exact arbiter.** Client-side, the rendering engine that
decides where every pixel of the curve goes is the same one that answers
inside/outside: Canvas `Path2D` + `ctx.isPointInPath(path, x, y)`, or SVG
`pathElement.isPointInFill(point)`. Hit-tested against the very path rendered — no
second opinion to diverge. The logic still never touches a pixel; it receives the
partition the exact test yields. (Server-side: sample each cut spline to a fine
polyline once, share that one polyline between renderer and test.)

**Ligatures fall out of the same move.** Once a cut is an exact closed path, a
ligature is an exact *open* path, and **crossing becomes exact**: "does this line
cross cut C, and how many times" = intersections of the ligature path with C's
closed path (equivalently: transitions of inside/outside along the line). So the
per-ligature **crossing-sequence invariant** (actual-vs-required crossing
multiset — the project's topological ligature law) is checked against the literal
drawn curves, no proxy. Three consequences, including the two the author named:
- **Cross at a precise, chosen point on the actual boundary** — a clean single
  transition outside→inside at a deterministic spot on C's curve, never a
  tangential graze that a proxy might miscount.
- **No spurious crossings** — the renderer can guarantee the line dips inside/
  outside *only* the cuts in its required sequence, because it can test exactly.
- **Obstacle avoidance** — knowing every exact path and spot/label position, route
  the line *around* unrelated marks and sibling cuts it must not cross. (Routing
  stays a constrained problem — connect A→B, cross exactly {C…}, avoid the rest —
  but the constraints and the verification are now exact; Eclipse Layout Kernel ([ELK](GLOSSARY.md#elk)) orthogonal routing
  and the tension taut-thread router are the substrate.)

**What it retires.** The box/ellipse/rounded special-casing in `point_in_cut`; the
"keep decorative wobble under content-clearance" fudge (the wobble *is* the
boundary now); the freeform corner-void. And it *characterizes* the one illegal
case cleanly: curves that **cross** have well-defined insides individually but no
consistent nesting — exactly the "cuts must nest or be separate" rule, now falling
out of the geometry instead of bolted on.

**What it costs, and why it fits.** The layout DTO must carry each cut's **path**
(and consume the *same* path in renderer and test) rather than a bounding box —
that is the whole change. It honors the existing layering: the logic stays
**coordinate-free** (`natural_layout` imports no geometry — "own the
dimensionality"), geometry lives entirely in the **projection** (renderer), and
correspondence is checked at that boundary (`correspondence_attestation` /
`eg_reader`). We are not adding a layer; we are making the projection's
inside/outside and crossing tests *exact* instead of proxied — the
**extent-based §3.3** the "drawn shape is authoritative" note already named as next,
taken to its exact conclusion. End state: the entire §3.3 invariant (partition +
incidence + crossing-sequence) is a set of *exact facts about the literal drawn
picture*. Inerrant correspondence, realized geometrically.

### Every mark is an extent: labels and ligature numerals (the final piece)

**Decided with the author 2026-06-10.** The same principle reaches the text. A
predicate or constant is drawn as *text*, and that text consumes an **area** — a
footprint — not just its font pixels and not a point. The argument-order **numerals**
on ligatures (Dau's numbers / Peirce's Convention-13 overrides) are marks with
footprints too — and "easily overwritten" today, because their footprint is not
reserved. So the completion: **every drawn mark that carries logical content has an
extent** — cut (closed curve), predicate/constant **label box**, vertex dot,
ligature line, order **numeral box** — and the extent is the sign.

Keep two senses of "area" distinct: a mark's **logical area** (which cut-nest it
belongs to — combinatorial) versus its **footprint** (the screen region it occupies
— geometric). Two requirements bind them:
1. **Each footprint lies wholly within its logical area.** A predicate label must
   not *straddle* a cut boundary — its whole box is inside one area, like a cut's
   contents. So containment for a predicate is "its **label box** is inside the cut
   path," not "its anchor *point* is" — the same point→extent upgrade as box→curve.
   The layout must grow cuts to enclose label *boxes* (ELK's `_compute_element_sizes`
   already sizes labels; the containment *test* and §3.3 must use the box).
2. **No footprint occludes another.** Labels must not overlap labels; a ligature
   line must not run through an unrelated label; and a numeral's box must be kept
   **clear** so it is readable.

**Why this is correspondence, not cosmetics.** The drawing is one of three co-equal
expressions of the EG, and the reader must recover the EG from the marks. An
**occluded or straddling label cannot be recovered** → correspondence breaks.
**Readability is a correctness property**: §3.3 should extend to "every mark is
wholly within its area and unoccluded enough to be read," and routing/layout must
treat every label box as an obstacle that lines route around and cuts enclose whole.

**The argument-order numerals are a special, *convention-dependent* case.** These
are the numbers on the ligatures incident to a predicate — each line's position in
that predicate's ν. Argument order *is* logic (`(loves x y) ≠ (loves y x)`), but
the numeral is only *one* way to draw it; the other is **clockwise placement**
(Peirce, CP 4.470 / Conv. 13) — the order read from the geometric arrangement of
the hooks around the spot. So:
- Under **clockwise placement**, the order lives in the geometry; the numeral is a
  toggleable **annotation** — presentation-only (regime-3), free, not affecting the
  logic. Hiding it (or even overwriting it) loses nothing readable, because the
  arrangement still encodes ν. *This is the robust, Peircean ideal.*
- Under the pure **numbered** convention (Dau §11.2, placement not arranged
  clockwise), the numeral is the *sole* carrier of order — load-bearing; hiding it
  loses ν-order. There its footprint must be reserved like any other mark.

So a numeral, *when drawn*, still has a footprint and obeys the extent rules; but
whether it is correctness-critical or a free annotation depends on whether the
order is independently carried by clockwise placement. Make clockwise placement the
order-carrier (the clockwise *reader* exists; clockwise *placement* is the pending
piece) and the numeral becomes a clean show/hide interpretation aid.

End state with this piece: the whole picture is a set of **extents** — curves,
boxes, dots, lines, (annotation) numeral boxes — each wholly within its logical
area, none
improperly occluding another (lawful nesting and crossing excepted), every one
readable. *That* is the complete geometric realization of inerrant correspondence.

## Build order

0. **Exact extents (the foundation). — DONE 2026-06-10 (exact-correspondence engine,
   Phases 1–4; see docs/EXACT_CORRESPONDENCE.md + archived/SESSION_LOG_2026-06-10.md).** Cut
   containment / ligature crossing read off the rounded-rect / ellipse the renderer
   draws; predicate/constant containment uses the **label box** (not the anchor
   point); §3.3 has the "every mark wholly within its area and unoccluded" checks
   (text-on-text, cut-line straddle, line through a non-incident label, with
   label-aware ligature routing); argument order by clockwise placement + single
   anchor. **Phase 4** carries each cut's **polyline** in the DTO and tests
   point-in-polygon, with the browser's `isPointInFill` (`diagram-viewer.areaAtPoint`)
   as the client-side arbiter — exactly what a human-drawn cut needs. One open
   refinement deferred by design: the hand-drawn **wobble** stays a render-only
   cosmetic (not attested), so a *human-drawn* cut is carried as an explicit polyline
   rather than relying on the wobble of an analytic shape. **The next session starts
   at step 1.**
1. **Visible containment + snapping + validity (the de-risked core).** Render cut
   interiors as filled regions (the exact path area) with live area feedback; then
   draw-time endpoint/containment snapping and a `read_drawing`-based fix-time
   validity pass with legible messages. This is what makes freeform usable and
   "fix = read" trustworthy.
   - **Fix-time validity pass — DONE 2026-06-10** (`src/drawing_validity.py`,
     `tests/test_drawing_validity.py`). `validate_drawing(dto) → ValidityReport`
     reads the drawing and reports the ill-formed cases the reader *can* read, in EG
     vocabulary — **errors** `overlapping_cuts` (curves cross → areas aren't a tree)
     and `dangling_line` (a loose end touches no mark, incl. the stops-short/drift
     brittleness); **warnings** `boundary_band` (a mark on a cut's boundary stroke),
     `unwired_predicate` (reads as 0-ary), `label_overlap`. It is the twin of
     `correspondence_attestation` (which checks a drawing against a *known* EGI):
     this checks a freeform drawing with *no EGI yet*. Geometry of record reused from
     `presentation_ops`, so "inside / on the boundary" is the same curve the renderer
     draws and §3.3 attests; clean engine layouts raise zero errors.
   - **Remaining:** filled/translucent containment regions + live area feedback on
     drag (`diagram-viewer.areaAtPoint`) + draw-time snapping, and wiring
     `validate_drawing` into the fix endpoint — all of which need the drag surface and
     a free-`LayoutDTO` source, so they ship with the canvas (step 2).
2. **Freeform drawing canvas — DONE 2026-06-11** (backend tested; frontend shipped,
   interactive layer pending author's-eyes check). Composition is *draw-then-read*:
   the browser owns the ink, no live EGI, linear forms silent until gate ①.
   - **`src/drawing_to_egi.build_egi_from_drawing`** — the construction half of
     fix=read: `read_drawing` gives structure (area tree + ordered incidence), the
     drawing carries content (relation names, constant labels), and this joins them
     into a real EGI. Corpus round-trip via `same_graph`.
   - **Routes** (additive; typed `composition_ops` untouched): `read-drawing` (non-
     mutating preview — validity + linear forms when well-formed) and `fix-drawing`
     (gate ①: validate → build → install as composing state → cross into deriving;
     §3.3 attested at the render boundary; ill-formed refused in EG vocabulary).
   - **`web_viewer/js/freeform-canvas.js`** — a self-contained `FreeformCanvas` SVG
     surface: tools Move / Line / Relation / Constant / Cut (drag an ellipse) /
     Connect / Erase; translucent cut fills (polarity by nesting depth); live
     point-in-polygon area feedback (the **visible containment + live feedback** of
     step 1, realized here on the canvas); a cut is just ink (erase it, contents
     stay; drag a mark across to change its area). Wired into the composing palette
     by an opt-in toggle; "Read it now" + freeform "① Fix this graph".
   - **Snapping — DONE 2026-06-11.** Line endpoints attach to marks by construction
     (the line tool connects a clicked predicate to a clicked vertex, so the
     stops-short/drift case cannot arise); a *spot* (vertex/predicate) snaps clear
     of any cut boundary (`_snapSpot`, keeping the side it is on) on placement and
     on drag-release, so its area is never the ambiguous boundary band. Live area
     feedback (`areaAt`) names the destination while dragging. **Step 1 is now
     complete** (validity + visible containment + live feedback + snapping).
3. **The legible EGI diff — DONE 2026-06-11** (`src/egi_diff.py`,
   `tests/test_egi_diff.py`). The discrepancy report: align two EGIs by relation
   label + role (generic vertices by incidence), diff area trees and per-relation
   incidence/order, phrase in EG terms (containment / scope / incidence / order /
   missing / extra). Reused by both fix-time validity *and* challenge mode.
4. **Challenge mode — DONE 2026-06-11** (`src/challenge_mode.py`,
   `tests/test_challenge_mode.py`, `tests/test_ergasterion_challenge.py`) in
   Ergasterion: pick a tomos linear form, hide its drawing,
   grade the freehand attempt with `same_graph` + the diff. Difficulty gradient
   straight from the corpus: single relation → nested cuts (negation, the [scroll](GLOSSARY.md#scroll) (a nested double cut — "if … then"))
   → Beta with a shared line crossing a boundary (∀x(P→Q)), where scope errors are
   the gold.

Building challenge mode *is* the ongoing stress test of `read_drawing` on human
input — the two efforts reinforce each other.
