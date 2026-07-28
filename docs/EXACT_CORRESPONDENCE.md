# Exact correspondence — the picture *is* the logic, geometrically

**Status:** architecture + phased plan, opened 2026-06-10. This page states the
advance worked out in conversation; `docs/FREEFORM_COMPOSITION_AND_LEARNING.md`
and `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` point here.

## The advance, in one sentence

Delete the approximating layer: make a cut **be its drawn curve** and every mark
**be its drawn extent**, so that containment, incidence, crossing-sequence, and
argument order become *exact facts about the literal picture*, with the renderer
(and, client-side, the browser) serving as the faithful, pixel-exact bridge while
the logic stays coordinate-free.

## Why the gap exists today, and why it is eliminable

Three layers; only the middle one approximates:
1. **Logic (the [EGI](GLOSSARY.md#egi))** — *topological*: which elements sit in which nested areas, which
   line is a predicate's argument *i*. Exact, pixel-agnostic.
2. **Drawing** — *closed curves and extents*. By the **Jordan Curve Theorem** any
   closed curve has a precise inside/outside, for any shape. Exact, for free.
3. **Geometry layer** (`presentation_ops.point_in_cut` / `bounds_in_cut` /
   crossing helpers) — the *only* approximator, because it tests a **proxy shape**
   (bounding box, inscribed ellipse) and treats marks as **points**, not extents.

The proxy amounts to an engineering convenience, not a necessity. Both ends
already read exact, and removing the proxy closes the gap.

## The model

- **A cut is a closed boundary polyline.** Containment means **point-in-polygon**
  (ray-cast / winding) against that boundary — exact, cheap, style-agnostic.
  Nesting (`bounds_in_cut`) means "child boundary wholly inside parent boundary."
- **Single source of truth for the boundary.** The renderer already derives each
  cut's drawn shape deterministically from `(bounds, style, seed)` — rounded
  `<rect rx>`, ellipse, or `_wobbled_oval_path`. Factor that into **one
  `cut_boundary(bounds, style, seed) -> [Point]`** consumed by *both* the renderer
  (draws it) and the geometry layer (tests it). Identical by construction → no
  divergence. (For **freeform** human-drawn cuts the boundary follows not from
  bounds+style but from the *actual drawn curve*; then it travels as data. Same
  abstraction: a cut HAS a boundary polyline, computed for engine layouts, carried
  for freeform.)
- **Ligatures are open paths; crossing is path-vs-path.** "Does this line cross cut
  C, how many times" = intersections of the ligature polyline with C's boundary
  (equivalently: inside/outside transitions along the line). The per-ligature
  **crossing-sequence invariant** (actual-vs-required crossing multiset) is then
  checked against the literal curves. This enables precise chosen crossing points,
  no spurious crossings, and obstacle-aware routing around unrelated marks and
  sibling cuts. Routing stays constrained, with Eclipse Layout Kernel ([ELK](GLOSSARY.md#elk)) and tension as the
  substrate, but its constraints and verification become exact.
- **Every mark is an extent, wholly within its area, unoccluded.** A predicate /
  constant is a **label box** (its containment uses the box, not an anchor point —
  it must not straddle a cut); a vertex is a dot; a ligature is a path. **Readability
  is a correctness property**: an occluded or straddling label cannot be recovered
  by the reader → correspondence breaks. The correspondence check (§3.3) extends to "every mark wholly within
  its area and unoccluded enough to read"; layout/routing treat label boxes as
  obstacles.
- **Argument-order numerals are convention-dependent annotation.** Order *is* logic
  (`(loves x y) ≠ (loves y x)`), but the numeral offers only one way to draw it;
  **clockwise placement** (Peirce) offers the other. Under clockwise placement the
  order lives in the geometry and the numeral becomes a **toggleable,
  presentation-only annotation** (free, regime-3 — hide/overwrite loses nothing).
  Only under the pure-numbered convention does the numeral carry the order alone.
  We want clockwise *placement* to carry it (the clockwise *reader* already
  exists), so numerals become a clean show/hide aid.

## The browser as the client-side exact arbiter

The engine that decides where every pixel of a curve goes can also answer
inside/outside against that very path: Canvas `Path2D` with
`ctx.isPointInPath(path, x, y)`; SVG `pathElement.isPointInFill(point)` /
`isPointInStroke(point)`. So for live freeform hit-testing (placement, drag
feedback, "which area is this in") the browser holds the authority, pixel-for-pixel
with what it draws. The logic still never touches a pixel. It receives the
partition the exact test yields.

## Why it fits the existing architecture

No new layer. The logic stays **coordinate-free** (`natural_layout` imports no
geometry — "own the dimensionality"); geometry lives entirely in the **projection**
(renderer + `presentation_ops`); the correspondence check happens at that boundary
(`correspondence_attestation`, `eg_reader`). We make the projection's tests
**exact** instead of proxied. That extent-based §3.3 is what the "drawn shape is
authoritative" note already named as next, taken to its conclusion. In the end the
entire §3.3 invariant (partition + incidence + crossing-sequence + argument order)
consists of exact facts about the literal drawn picture.

## What it retires

- the box/ellipse/rounded special-casing in `point_in_cut`;
- the "keep decorative wobble under content-clearance" fudge (the wobble *is* the
  boundary now);
- the rounded-corner void (the §3.3 gap the author spotted);
- argument order depending on a textual label (it moves into the arrangement).

It also *characterizes* the one illegal case cleanly. Curves that **cross** have
well-defined insides individually but no consistent nesting. That gives exactly
"cuts must nest or be separate," now falling out of the geometry.

## Phased plan (each phase: full suite + §3.3 corpus suite green before the next)

**Phase 1 — exact cut containment (the foundation). *Done* (2026-06-10).**
- `presentation_ops.cut_boundary(bounds, style, seed) -> [Point]` — the canonical
  closed polyline (rounded-rect with corner radius, sampled ellipse, wobbled oval),
  and `point_in_polygon` / `polyline_polygon_crossings`.
- `presentation_ops.point_in_cut` / `bounds_in_cut` test against `cut_boundary`
  (keep a fast path for the plain axis-aligned box). This closes the rounded-corner
  void: a point in the corner now reads *outside*, matching the drawing.
- `simple_svg_renderer` draws the wobbled/oval/rect cut from the *same*
  `cut_boundary` polyline, so render == test.
- Verify: corpus §3.3 round-trip still green (engine keeps marks clear of corners,
  so tightening the test must not regress); new tests pin the corner-void fix.

**Phase 2 — exact ligature crossing. *Done* (2026-06-10).** Crossing now reads off
the *same* drawn boundary as Phase 1's containment. `count_cut_crossings` takes the
corner radius and counts a ligature segment's crossings against the rounded
rectangle the renderer draws: straight edges inset by the radius plus four
quarter-circle corner arcs (`_rounded_rect_secant_crossings` / `_seg_arc_crossings`,
the rounded-rect analogue of the box `_outside_edge_crossings` and the
`_ellipse_secant_crossings` it already had). So a ligature that clips a rounded-away
corner counts as the eye sees it, *outside* the cut, rather than as a spurious
entry. That closes the crossing side of the corner void. The crossing-multiset
attestation in `correspondence_attestation` threads `cut_radius` into the call.
Verified corpus-wide: 457 §3.3 tests green, zero regression; new unit tests pin the
corner-graze (square box counts 2, rounded counts 0), straddle (1), and clean
pass-through (2). *Still open (deferred to routing/Phase 4):* chosen-crossing-point
*placement* in the renderer. Phase 2 made the crossing *test* exact; deliberately
*placing* each crossing on the boundary remains a routing concern.

**Phase 3 — extents for labels + numerals.** Three sub-pieces, taken separately.

- **3a — label-box containment / no straddle. *Done* (2026-06-10).** A predicate's
  containment is its *drawn label box*, not its anchor point. `presentation_ops.
  predicate_label_box(label, center, style)` serves as the single source of truth,
  the exact rectangle the renderer draws (`simple_svg_renderer` now draws *from* it,
  so picture and test never diverge). §3.3 (`correspondence_attestation`) checks the box
  sits wholly inside every ancestor cut (`bounds_in_cut`) and wholly outside every
  non-ancestor cut (`box_intrudes_cut` — the box analogue of the ligature
  "enters forbidden cut" check), so a label may not straddle a cut boundary. A
  vertex stays a *dot* (point containment); a constant is a labeled dot, so its dot
  is point-contained (its offset label's readability belongs to 3b's occlusion
  concern).
  521 §3.3 tests green corpus-wide (the engine keeps boxes clear of boundaries);
  new tests pin the straddle refusal and the shared box formula.
- **3b — no improper occlusion. *Done* (2026-06-10).** §3.3 gained a "marks don't
  overlap each other / cut lines illegibly" check (an occluded label can't be
  recovered by the reader → correspondence breaks). Three properties shipped, all
  green corpus-wide:
  - **text-on-text** — two label boxes (predicate or vertex) may not overlap on a
    positive-area region (`presentation_ops.boxes_overlap`; abutting edges stay
    legible and allowed).
  - **vertex/constant label no-straddle** — a vertex label box must sit wholly
    inside its area cut and clear of every non-ancestor cut, the vertex-label
    analogue of 3a's predicate no-straddle (closing the constant/vertex case 3a
    left out). This required factoring the renderer's direction-adaptive vertex
    label placement into a shared, **cut-aware** `presentation_ops.vertex_label_box`
    (single source of truth, like `predicate_label_box`): it places the label in the
    freest angular gap between incident ligatures *that keeps the box inside its cut
    and clear of siblings*, trying the free direction then the four cardinals, so the
    engine keeps labels legible without yet reserving room. The renderer draws the
    text centred in this same box. The one real straddle this surfaced
    (`peirce_cp_4_394_man_mortal`, "Socrates" parked at the cut's right edge) the
    cut-aware placement fixes by choosing an inward direction.
  - **no strike-through (line through a non-incident box). *Done* (2026-06-10),
    paired with its routing.** A line of identity running through a label box it
    is **not** incident to bisects the text, a genuine occlusion. It surfaced a
    real strike-through in the shared-vertex fan-in after IT+ on
    `roberts_domain_modeling`, where several lines converged on one vertex through
    the intervening "Person"/predicate boxes. Shipped as a matched pair so honest
    layouts stay green:
    - **the §3.3 check** (`correspondence_attestation`): for each label box, any
      ligature *not* incident to it (≠ that predicate / ≠ that vertex) passing
      through the box's open interior (`presentation_ops.path_intersects_box` —
      Liang–Barsky clip + strict interior, so a graze along an edge stays legible)
      is refused.
    - **the constructive partner** (`elk_layout_engine._build_ligature_paths`):
      label boxes (the same `predicate_label_box` / `vertex_label_box` the check
      reads) become **soft obstacles** the router skirts. Routing runs two tiers.
      Forbidden cuts count as **hard** (never crossed; soundness), label boxes as
      **soft** (skirted only when a detour exists that still clears every hard
      cut; otherwise the label gives way to the sound route). A finite
      visibility-graph path through hard ∪ soft avoids the cuts by construction.
      Vertex-label placement reads off a stable provisional straight pass
      (routing bends only a line's middle, not its endpoints), so the two passes
      don't chase each other.
- **3c — clockwise placement as the order carrier (Peirce's *writing* convention).
  *Done* (2026-06-10).** ν *specifies* the argument order, so the drawing *shows*
  it: a relation's hooks are drawn **clockwise around the spot in ν-order, by
  construction** (CP 4.470 / Conv. 13). The clockwise reading then gives ν by
  construction. Order lives in the geometry, not in a number on every line. Three
  pieces:
  - **the writing-convention placement** (`clockwise_placement.place_clockwise_hooks`,
    run pre-attestation in `layout_service` for **every style and layout**; drawing
    a relation's hooks clockwise in ν-order counts as correct layout, not a
    Peirce-only flourish, so the picture reads the same across styles, and the
    convention setting governs only whether numerals are *also* drawn). Every ≥2-ary
    predicate's hooks sit on the spot's edge at evenly-spaced clockwise slots in
    ν-order, at the **rotation that best aligns the fan with where the vertices
    actually lie**, which minimizes crossings. When the layout already put the
    vertices in ν-clockwise order the hooks point straight at them and nothing
    crosses; otherwise the orientation with the least bending wins. A 10-ary relation
    becomes ten spokes 36° apart, a clock face read clockwise — *when the layout
    places the vertices around the spot*. ELK often stacks a relation's arguments to
    one side, where a full clockwise fan becomes geometrically impossible without
    spokes crossing the name, and the predicate reverts (below). The **hook
    position** carries the order (Peirce reads the hooks' positions around the spot,
    not the lines' directions — `read_drawing`/`_clockwise_order` key off
    `points[0]`), so each line runs **straight to its vertex with no artificial stub
    or kink**. Each line reroutes around cuts and label boxes through the two-tier
    router, under a local guard: crossing-multiset and area endpoints unchanged,
    **and no line may strike through any predicate label, including its own spot**
    (a hook forced opposite its vertex would run the line across the name). A
    predicate the spread can't keep clean — a strike-through, or a relation crammed
    in a tight cut whose spokes would pierce the boundary — reverts to its natural
    hooks, degrading gracefully, and the numeral then carries its order; the whole
    result is re-attested with a fallback.

    **Design decision — clockwise placement is a *local, best-effort* sugar, not a
    layout constraint (constrained layout considered and *declined*).** A *clock
    face* for stacked/high-arity arguments would need the layout to order each
    relation's argument-vertices clockwise around its spot. We deliberately do **not**
    build that. It does not scale. A **shared line of identity** makes one vertex
    incident to many spots, possibly across cuts, so each spot demands a different
    clockwise angle for it: *k* conflicting demands for a degree-*k* vertex,
    unsatisfiable for *k ≥ 2*. It would amount to a second structural system
    competing with the cut-containment hierarchy, which carries the load and stays
    non-negotiable. A presentation convention would push down into the structural
    layout and fight the cuts as density grows. This is exactly why Dau prescinds
    from position and **numbers the lines** (§11.2): the numeral or anchor costs O(1)
    per line, stays always available, and composes with any nesting and density. So
    the labour divides three ways. **Order lives in ν. The numeral (or single start
    anchor) carries it at scale and on the record. Clockwise placement stays a
    small-graph aesthetic that applies when free and yields to the numeral
    otherwise.** That agrees with "render as projection": order lives in the
    projection-independent layer, and each projection shows it differently.
  - **a single start anchor.** The clockwise placement carries the *order*, but a
    reader still needs ν's *first* hook. Pinning the fan to vertically-above would
    fight the crossing-minimizing fit, so instead `assign_order_labels` marks at most
    one line per relation: the numeral 1 on ν's first line (Conv. 13's start index),
    and none where the fit already reads ν from the top. **One mark, any arity**,
    never a number on every line. (`read_drawing` reads that anchor: the placement
    gives the cyclic order, the anchor says where it begins.) Genuine permutations
    fall back to full numbering; the by-construction placement never produces one,
    only a sound-reverted predicate can.
  - **the numeral is a presentation-only toggle.** `argument_order_numerals: auto |
    always | never`: `never` draws none (pure placement, Peirce-pure), `always`
    numbers every line, `auto` (default) draws the sparse start anchors. Toggling
    never touches geometry, so §3.3 stays indifferent.
  *Result:* corpus-wide §3.3 green; **no line strikes through any predicate label**;
  the ordered round trip recovers ν everywhere (`auto`, 23/23). Placement carries
  it where the layout cooperates, and the numeral carries any predicate that
  reverted. This applies for every style and layout, so the picture reads the same
  across them.

**Phase 4 — browser as client-side arbiter + freeform. *Done* (2026-06-10).** A cut
can now travel as its **literal drawn polyline**. That gives the foundation for
human-drawn cuts on the freeform canvas, where the polyline *is* the cut with no
analytic shape behind it.
- **One generator** (`presentation_ops.cut_boundary(bounds, shape, corner_radius,
  wobble, seed, samples)`) samples the drawn curve (rounded rectangle / inscribed
  ellipse / wobble) as a closed polyline; `point_in_polygon` and
  `polyline_polygon_crossings` test against it.
- **The Data Transfer Object ([DTO](GLOSSARY.md#dto)) carries it** (`LayoutDTO.cut_boundary: {cut_id: polyline}`, optional).
  `resolve_cut_boundaries(dto)` is the boundary of record shared by §3.3 and
  `eg_reader`: a carried polyline (freeform cut) → tested point-in-polygon; an
  analytic cut → `None`, read by the exact `point_in_cut` from `cut_bounds` + style.
  `point_in_cut` / `bounds_in_cut` / `count_cut_crossings` all take an optional
  `boundary` and use it when present. So §3.3 refuses a drawing whose *drawn cut
  curve* excludes a mark even when the bounding box would contain it.
- **The renderer draws a carried polyline** as its literal `<path>` (one source of
  truth: the curve §3.3 tests, the renderer draws, and the browser hit-tests).
- **The browser serves as the client-side arbiter.** `diagram-viewer.js`
  `areaAtPoint(x, y)` uses `SVGGeometryElement.isPointInFill` against the drawn cut
  shapes (`<rect>`/`<ellipse>`/`<path>` alike) to answer which area a point falls
  in — the deepest containing cut — for placement and drag on the freeform canvas.
- *Scope note:* the hand-drawn **wobble** stays a render-only cosmetic flourish
  (capped within the containment margin, not part of the attested geometry — see
  `render_geometry`). Phase 4's polyline serves *human-drawn* cuts, not the
  attesting of the wobble, which testing surfaced as a false positive and which we
  correctly left alone.

Each phase wins independently. Phase 1 alone fixes a real §3.3 gap, and it stands
as the prerequisite for the freeform canvas's "visible, unambiguous containment
regions."

## Scope boundary: structured placement, not pixel recognition

**The load-bearing design choice**, and the reason the "read" direction stays
tractable at all. "Convert a user drawing into an EGI" hides two problems that lie
worlds apart:

- **In scope — reading *structured placement*.** In Arisbe's freeform canvas the
  user places **typed marks**: *this is a cut, this is a relation labelled P, this
  is a line of identity* — the tool that made each mark already carries its
  identity. The system never *recognises* anything. It only reads the
  **relationships** (containment, incidence, crossing-sequence, order) from
  geometry, which is exactly what `eg_reader.read_drawing` does, already
  round-tripping the whole corpus and made *exact* by this document. The only open
  work concerns human *imprecision*: a line stopping short, a spot near a boundary.
  **Snapping + validity** handle that, not intelligence. **Arisbe reads structured
  placement, not pixels.**

- **DEFERRED, out of current scope — reading a *raster image*.** A photo, scan, or
  true stylus-freehand of a hand-drawn Existential Graph ([EG](GLOSSARY.md#eg)) (e.g. a figure from a book, Peirce's
  notebook) poses a different and genuinely hard problem: stroke segmentation, mark
  classification, label handwriting recognition, structure inference from noisy
  pixels. That work belongs to computer vision and sketch recognition. Freeform
  composition and challenge mode do **not** need it, and it must not contaminate
  their scoping.

  **It remains a real "to do," just not now — and likely a hand-off to external AI
  image recognition rather than something built internally.** The shape follows
  naturally. An outside vision or recognition step produces a *structured placement*
  (typed marks + positions, i.e. a `LayoutDTO`-shaped result), which then enters the
  *same* `read_drawing` → EGI → validity pipeline as freeform. So the internal
  system stays geometry-on-known-marks, the hard pixel problem sits isolated behind
  that boundary, and an AI service can fill it when wanted. This gives the engine
  the by-hand "reading desk / import" idea would need (see that backlog item); keep
  the two distinct so future scoping stays honest.
