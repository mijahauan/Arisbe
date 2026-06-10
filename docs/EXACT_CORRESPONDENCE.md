# Exact correspondence — the picture *is* the logic, geometrically

**Status:** architecture + phased plan, opened 2026-06-10. The canonical statement
of the advance worked out in conversation; `docs/FREEFORM_COMPOSITION_AND_LEARNING.md`
and `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` point here.

## The advance, in one sentence

Delete the approximating layer: make a cut **be its drawn curve** and every mark
**be its drawn extent**, so containment, incidence, crossing-sequence, and
argument order are *exact facts about the literal picture* — with the renderer (and,
client-side, the browser) as the faithful, pixel-exact bridge, and the logic
staying coordinate-free.

## Why the gap exists today, and why it is eliminable

Three layers; only the middle one approximates:
1. **Logic (EGI)** — *topological*: which elements sit in which nested areas, which
   line is a predicate's argument *i*. Exact, pixel-agnostic.
2. **Drawing** — *closed curves and extents*. By the **Jordan Curve Theorem** any
   closed curve has a precise inside/outside, for any shape. Exact, for free.
3. **Geometry layer** (`presentation_ops.point_in_cut` / `bounds_in_cut` /
   crossing helpers) — the *only* approximator, because it tests a **proxy shape**
   (bounding box, inscribed ellipse) and treats marks as **points**, not extents.

The proxy is an engineering convenience, not a necessity. Both ends are exact;
removing the proxy closes the gap.

## The model

- **A cut is a closed boundary polyline.** Containment is **point-in-polygon**
  (ray-cast / winding) against that boundary — exact, cheap, style-agnostic.
  Nesting (`bounds_in_cut`) is "child boundary wholly inside parent boundary."
- **Single source of truth for the boundary.** The renderer already derives each
  cut's drawn shape deterministically from `(bounds, style, seed)` — rounded
  `<rect rx>`, ellipse, or `_wobbled_oval_path`. Factor that into **one
  `cut_boundary(bounds, style, seed) -> [Point]`** consumed by *both* the renderer
  (draws it) and the geometry layer (tests it). Identical by construction → no
  divergence. (For **freeform** human-drawn cuts the boundary is not a function of
  bounds+style but the *actual drawn curve*; then it is carried as data. Same
  abstraction: a cut HAS a boundary polyline, computed for engine layouts, carried
  for freeform.)
- **Ligatures are open paths; crossing is path-vs-path.** "Does this line cross cut
  C, how many times" = intersections of the ligature polyline with C's boundary
  (equivalently: inside/outside transitions along the line). The per-ligature
  **crossing-sequence invariant** (actual-vs-required crossing multiset) is then
  checked against the literal curves. Enables precise chosen crossing points, no
  spurious crossings, and obstacle-aware routing (route around unrelated marks /
  sibling cuts) — routing stays constrained (ELK / tension are the substrate) but
  its constraints and verification become exact.
- **Every mark is an extent, wholly within its area, unoccluded.** A predicate /
  constant is a **label box** (its containment uses the box, not an anchor point —
  it must not straddle a cut); a vertex is a dot; a ligature is a path. **Readability
  is a correctness property**: an occluded or straddling label cannot be recovered
  by the reader → correspondence breaks. §3.3 extends to "every mark wholly within
  its area and unoccluded enough to read"; layout/routing treat label boxes as
  obstacles.
- **Argument-order numerals are convention-dependent annotation.** Order *is* logic
  (`(loves x y) ≠ (loves y x)`), but the numeral is one way to draw it; the other is
  **clockwise placement** (Peirce). Under clockwise placement the order lives in the
  geometry and the numeral is a **toggleable, presentation-only annotation** (free,
  regime-3 — hide/overwrite loses nothing). Only under the pure-numbered convention
  is it the sole, load-bearing carrier. Goal: make clockwise *placement* the
  carrier (the clockwise *reader* exists), so numerals become a clean show/hide aid.

## The browser as the client-side exact arbiter

The engine that decides where every pixel of a curve goes is the same one that can
answer inside/outside against that very path: Canvas `Path2D` +
`ctx.isPointInPath(path, x, y)`; SVG `pathElement.isPointInFill(point)` /
`isPointInStroke(point)`. So for live freeform hit-testing (placement, drag
feedback, "which area is this in") the browser is the authority, pixel-for-pixel
with what it draws. The logic still never touches a pixel; it receives the partition
the exact test yields.

## Why it fits the existing architecture

No new layer. The logic stays **coordinate-free** (`natural_layout` imports no
geometry — "own the dimensionality"); geometry lives entirely in the **projection**
(renderer + `presentation_ops`); correspondence is checked at that boundary
(`correspondence_attestation`, `eg_reader`). We are making the projection's tests
**exact** instead of proxied — the **extent-based §3.3** the "drawn shape is
authoritative" note already named as next, taken to its conclusion. End state: the
entire §3.3 invariant (partition + incidence + crossing-sequence + argument order)
is a set of exact facts about the literal drawn picture.

## What it retires

- the box/ellipse/rounded special-casing in `point_in_cut`;
- the "keep decorative wobble under content-clearance" fudge (the wobble *is* the
  boundary now);
- the rounded-corner void (the §3.3 gap the author spotted);
- argument order depending on a textual label (it moves into the arrangement).

It also *characterizes* the one illegal case cleanly: curves that **cross** have
well-defined insides individually but no consistent nesting — exactly "cuts must
nest or be separate," now falling out of the geometry.

## Phased plan (each phase: full suite + §3.3 corpus suite green before the next)

**Phase 1 — exact cut containment (the foundation).** *In progress.*
- New `render_geometry.cut_boundary(bounds, style, seed) -> [Point]` — the canonical
  closed polyline (rounded-rect with corner radius, sampled ellipse, wobbled oval),
  and `point_in_polygon` / `polygon_in_polygon`.
- `presentation_ops.point_in_cut` / `bounds_in_cut` test against `cut_boundary`
  (keep a fast path for the plain axis-aligned box). This closes the rounded-corner
  void: a point in the corner now reads *outside*, matching the drawing.
- `simple_svg_renderer` draws the wobbled/oval/rect cut from the *same*
  `cut_boundary` polyline, so render == test.
- Verify: corpus §3.3 round-trip still green (engine keeps marks clear of corners,
  so tightening the test must not regress); new tests pin the corner-void fix.

**Phase 2 — exact ligature crossing. *Done* (2026-06-10).** Crossing now reads off
the *same* drawn boundary as Phase 1's containment: `count_cut_crossings` takes the
corner radius and counts a ligature segment's crossings against the rounded
rectangle the renderer draws — straight edges inset by the radius plus four
quarter-circle corner arcs (`_rounded_rect_secant_crossings` / `_seg_arc_crossings`,
the rounded-rect analogue of the box `_outside_edge_crossings` and the
`_ellipse_secant_crossings` it already had). So a ligature that clips a rounded-away
corner is counted as the eye sees it — *outside* the cut — not as a spurious entry,
closing the crossing-side of the corner void. The crossing-multiset attestation in
`correspondence_attestation` threads `cut_radius` into the call. Verified
corpus-wide: 457 §3.3 tests green, zero regression; new unit tests pin the
corner-graze (square box counts 2, rounded counts 0), straddle (1), and clean
pass-through (2). *Still open (deferred to routing/Phase 4):* chosen-crossing-point
*placement* in the renderer — Phase 2 made the crossing *test* exact; deliberately
*placing* each crossing on the boundary is a routing concern.

**Phase 3 — extents for labels + numerals.** Predicate/constant containment uses
the label box (wholly inside the cut boundary); a §3.3 "no straddle / no improper
occlusion" check; layout/routing treat label boxes as obstacles. Clockwise
*placement* as the order carrier → numerals become a toggleable annotation
(presentation-only); a show/hide control.

**Phase 4 — browser as client-side arbiter + freeform.** Carry the cut boundary
polyline in the DTO (needed once cuts can be human-drawn); client-side
`isPointInPath` hit-testing for placement/drag in the freeform canvas
(`docs/FREEFORM_COMPOSITION_AND_LEARNING.md`).

The phases are independent wins: Phase 1 alone fixes a real §3.3 gap and is the
prerequisite for the freeform canvas's "visible, unambiguous containment regions."

## Scope boundary: structured placement, not pixel recognition

**The load-bearing design choice — and the reason the "read" direction is
tractable at all.** "Convert a user drawing into an EGI" hides two problems that
are worlds apart:

- **In scope — reading *structured placement*.** In Arisbe's freeform canvas the
  user places **typed marks**: *this is a cut, this is a relation labelled P, this
  is a line of identity* — the tool that made each mark already carries its
  identity. The system never *recognises* anything; it only reads the
  **relationships** (containment, incidence, crossing-sequence, order) from
  geometry — which is exactly `eg_reader.read_drawing`, already round-tripping the
  whole corpus and made *exact* by this document. The only open work is human
  *imprecision* (a line stopping short, a spot near a boundary), handled by
  **snapping + validity**, not intelligence. **Arisbe reads structured placement,
  not pixels.**

- **DEFERRED, out of current scope — reading a *raster image*.** A photo, scan, or
  true stylus-freehand of a hand-drawn EG (e.g. a figure from a book, Peirce's
  notebook) is a different and genuinely hard problem: stroke segmentation, mark
  classification, label handwriting recognition, structure inference from noisy
  pixels. That is computer vision / sketch recognition, **not** what freeform
  composition or challenge mode needs, and it must not contaminate their scoping.

  **It is a real "to do," just not now — and likely a hand-off to external AI image
  recognition rather than something built internally.** The natural shape: an
  outside vision/recognition step produces a *structured placement* (typed marks +
  positions, i.e. a `LayoutDTO`-shaped result), which then enters the *same*
  `read_drawing` → EGI → validity pipeline as freeform. So the internal system stays
  geometry-on-known-marks; the hard pixel problem is isolated behind that boundary
  and can be filled by an AI service when wanted. This is the engine half of the
  by-hand "reading desk / import" idea (see that backlog item); keep the two
  distinct so future scoping stays honest.
