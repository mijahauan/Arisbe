> **Archived 2026-07-02** (alpha-release docs triage — see `../ALPHA_RELEASE_PLAN.md` §2). A dated session log. The chronological log lives in `../../CURRENT_PLAN.md`.

# Session log — 2026-06-10: the exact-correspondence engine, completed (Phases 1–4)

A thorough record of one long session. It carried the **exact-correspondence
engine** (docs/EXACT_CORRESPONDENCE.md) from "Phases 1, 2, 3a, 3b shipped" to
**complete (Phases 1–4)**, and ends pointed at the **freeform composition canvas**.
The narrative and the *decisions* are the value here — the per-phase mechanics live
in docs/EXACT_CORRESPONDENCE.md, the commits, and the memory files.

> One-line state at session end: **Phases 1–4 done; §3.3 corpus green; the whole
> §3.3 invariant is now a set of exact facts about the literal drawn picture; next
> arc = the freeform canvas (build step 0 of FREEFORM_COMPOSITION is exactly this
> engine, so the next session starts at step 1).**

## What shipped (in order), with the commits

1. **Label-aware ligature routing** (`d80fda8`) — Phase 3b's *deferred third
   occlusion property* + its constructive partner.
   - §3.3 **check #3**: refuse a line of identity through the open interior of a
     label box it is **not** incident to (`path_intersects_box`).
   - **The partner**: `elk_layout_engine._build_ligature_paths` routes non-incident
     lines *around* label boxes — a **two-tier router**: forbidden cuts are **hard**
     (never crossed, soundness), label boxes are **soft** (skirted only when a
     detour still clears every hard cut; else the label yields to the sound route).
   - Method: ran check #3 with *no* routing first → only `roberts_domain_modeling`
     (the shared-vertex fan-in after IT+) failed → confirmed the check was tuned
     before building the partner. Cleared that strike-through.

2. **Phase 3c — clockwise placement as the order carrier** — the long thread of the
   session, *reframed three times at the author's direction*. The final shape:
   - **Clockwise is a *writing* convention** (`bd9c367`): ν specifies the order, so
     the hooks are **drawn clockwise around the spot in ν-order by construction**
     (`clockwise_placement.place_clockwise_hooks`, best-fit rotation = crossings
     minimized) — not retrofitted onto wherever the layout dropped the vertices.
   - **The hook *position* carries the order** (`7fc5561`), not the line's
     direction: place the hook at its clockwise slot on the spot's edge, run the
     line **straight** to its vertex (no stub, no kink); `read_drawing` /
     `_clockwise_order` key off `points[0]`. This fixed the kinked/bent
     hand-drawn render the author flagged.
   - **Consistent across every style/layout** (`7fc5561`): the placement is *correct
     layout*, not a Peirce-only flourish, so it runs for Dau/numbered and Sowa too;
     `argument_order_convention` governs only whether numerals are *also* drawn.
   - **A single start anchor** carries the order with ≤1 mark per relation
     (Conv. 13's start index); `read_drawing` is anchor-aware. The numeral is a
     presentation-only toggle (`argument_order_numerals: auto|always|never`).
   - **No line may strike through any predicate label** (`8ec8a49`) — including its
     **own** spot (a hook forced opposite its vertex would run the line across the
     name; the author caught it on `peirce_complex_scope` in the viewer). The
     placement guard reverts such a predicate to its natural hooks + numeral.

3. **Phase 4 — cut as a drawn polyline + browser as client-side arbiter**
   (`f24f035`) — the foundation for human-drawn (freeform) cuts.
   - `presentation_ops.cut_boundary(...)` generates a cut's drawn curve as a closed
     polyline; `point_in_polygon` / `polyline_polygon_crossings` test it.
   - `LayoutDTO.cut_boundary` carries it (a freeform cut *is* the polyline);
     `resolve_cut_boundaries(dto)` is the boundary of record shared by §3.3 +
     `eg_reader` (carried polyline → point-in-polygon; analytic cut → exact
     `point_in_cut`). The three containment functions gained an optional `boundary`.
   - The renderer draws a carried polyline as `<path>`; `diagram-viewer.js
     ::areaAtPoint(x,y)` uses `isPointInFill` for placement/drag hit-testing.

## The decisions (the part worth re-reading)

These were live design forks resolved *with the author* — recorded so they are not
re-litigated.

- **Clockwise placement is a *writing* convention, not a reading retrofit.** My first
  cut was a corpus-tuned "fragile-patch." The author's correction — "if the EGI
  specifies the order, that should be the order they're drawn around the predicate,
  clockwise" — was right and made the code *simpler*. Lesson, recorded in memory:
  don't tune to the toy corpus ("can't use it to gauge how common this is — assume
  complicated graphs"); reach for the principled convention.

- **Constrained layout for clock-face placement: CONSIDERED and DECLINED.** Forcing
  a clock face for stacked/high-arity arguments would need the *layout* to order
  each relation's argument-vertices clockwise around its spot. It does not scale: a
  **shared line of identity** gives one vertex *k* conflicting clockwise demands
  (one per incident spot), unsatisfiable for *k ≥ 2*; it would be a second
  structural system fighting the cut-containment hierarchy. **This is exactly why
  Dau numbers the lines.** Resolution: *order lives in ν; the numeral/anchor is the
  scalable carrier of record; clockwise placement is a best-effort small-graph
  aesthetic that yields to the numeral* — consistent with "render as projection."
  The one guarantee kept at every scale: **no line strikes a label.**

- **The hand-drawn wobble stays a render-only cosmetic, not attested geometry.**
  Phase 4 *could* test the wobbled curve; doing so surfaced one false positive
  (`roberts_1973`, a label inside the ideal ellipse but past a wobble dent). The
  existing architecture deliberately treats wobble as a stroke-only flourish capped
  within the containment margin (`render_geometry`). So `resolve_cut_boundaries`
  returns a polyline only for **carried (freeform)** cuts; analytic cuts keep the
  exact `point_in_cut`. Phase 4's polyline is for *human-drawn* cuts, not the wobble.

## Verification (what "green" meant)

- §3.3 attestation + correspondence-invariant suites green corpus-wide at each step.
- Final Phase 4 comprehensive run: **565 passed, 34 skipped**.
- New tests: router soft-skirt / hard+soft / soundness fallback
  (`test_projection_conventions`); adversarial strike-through, single-start-anchor,
  writing-convention, high-arity no-strike, **freeform polyline** containment + read
  (`test_eg_reader`, `test_correspondence_attestation`).

## Where this leaves the engine

The whole §3.3 invariant — area partition (cut containment), incidence + argument
order, ligature crossing-sequence, label/numeral extents, and no improper occlusion
— is now checked as **exact facts about the literal drawn picture**, and a cut can
*be* an arbitrary human-drawn curve tested point-in-polygon by both the attestation
and the reader, drawn as its own `<path>`, and hit-tested geometrically on the
client. That is the complete geometric realization of inerrant correspondence
(EXACT_CORRESPONDENCE.md), and it is precisely **build step 0** of
FREEFORM_COMPOSITION_AND_LEARNING.md.

## Next arc — freeform composition (start at step 1)

See `CURRENT_PLAN.md ▶ NEXT SESSION` and
`docs/FREEFORM_COMPOSITION_AND_LEARNING.md` (build order). Step 0 (exact extents) is
done; the remaining build is: **(1)** visible containment regions + draw-time
snapping + a `read_drawing`-based fix-time validity pass; **(2)** the freeform
drawing canvas (place/drag/erase typed marks on a free `LayoutDTO`, live forms
silent until gate ①); **(3)** the legible EGI diff; **(4)** challenge mode over the
tomos corpus. The building blocks are all in hand (`read_drawing` de-risked on human
geometry, `areaAtPoint`, `cut_boundary`, §3.3 at gate ①, `same_graph`).
