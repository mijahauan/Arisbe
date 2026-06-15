# Adaptive-scope viewer — projection spike (findings)

**Date:** 2026-06-13. **Status:** spike complete; decision below. Plan:
`~/.claude/plans/validated-stirring-biscuit.md`.

## Why

Arisbe's logic is essentially complete; the gap is the *experience* of the pictures, walled
off by the **layout-perf frontier** (ELK is super-linear in nesting depth — the 86-cut SUMO
upper taxonomy is the largest stored UoD; the full 250-cut taxonomy ≈ 74 s,
`docs/CORPUS_AND_IMPORT_MODEL.md:145`). The viewer does purely geometric zoom with no notion of
semantic detail. Rather than declutter a flat SVG, we want to **spend the EGI's degrees of
freedom on a better projection** — Peirce's own cut-as-removal-from-the-plane, recto/verso
negation, the endoporeutic peel as a depth traversal. The architecture already anticipates this
(`natural_layout` is coordinate-free so a new projection is *additive*). This spike built thin
prototypes of competing projections over one shared structure and compared them on real graphs.

## What was built (read-only, additive, regime-3 — bedrock untouched)

- **`src/eg_structure.py`** + **`GET /organon/uods/{id}/structure`** / **`POST /organon/structure`** —
  the shared coordinate-free structure JSON (containment tree + per-area depth/polarity,
  recursive content counts, predicate/vertex inventory, per-ligature **required
  crossing-sequence**). Reuses `natural_layout` + `eg_navigation`; runs **no layout engine**, so
  it is O(n): the 86-cut SUMO structure returns in **~8 ms over HTTP** (vs ELK's seconds). Tests:
  `tests/test_eg_structure.py` (7).
- **`src/web_viewer/spike/`** (throwaway, unwired from the modes): `spike-common.js` (fetch +
  corpus/EGIF picker + model/hierarchy builders + recto/verso palette), **`circle-packing.html`**
  (P1, D3), **`shells-3d.html`** (P2, three.js), `index.html`. Run the server and open
  `/spike/`.

## The candidates

- **P1 — Zoomable circle-packing (2-D).** Cuts as nested ovals (Peirce's own notation);
  recto/verso as concentric color bands; zoom into a cut to expand. Ligatures drawn
  predicate→vertex, colored green→red by crossing count.
- **P2 — 3-D nested shells (three.js).** Negation depth on z; translucent shells; recto/verso
  edge tint; orbit + dolly to fly inward; ligatures drawn as 3-D lines that pierce the shells
  they cross.
- **P3 — Hyperbolic focus+context.** *Not built* — see verdict.

## Evidence (headless Chromium, zero console/WebGL errors on either prototype)

Three regimes, each fetched in ≤50 ms:

| Case | P1 circle-packing | P2 3-D shells |
|---|---|---|
| **Nested chain (depth 3)** | Recto/verso alternation crisp; P/Q/R at correct depths; content-count badges legible. `p1-circlepack-nested.png` | Shells nest in z; ligatures pierce them; z-separation a bit flat at default camera. `p2-shells3d-deep.png` (deeper case) |
| **Deep chain (depth 8)** | **Best of all** — concentric recto/verso rings, P0→P7 marching inward at exact depths. `p1-circlepack-deep.png` | **3-D's strength** — a green→red *fan* of one line-of-identity through 8 negation layers; the ligature's journey made vivid. `p2-shells3d-deep.png` |
| **Wide+shallow (SUMO, 86 cuts, depth 2)** | 86 sibling scrolls packed compactly & legibly in one view. `p1-circlepack-sumo86.png` | Collapses to a **flat grid** — z-axis barely engages; 2-D handles it better. `p2-shells3d-sumo86.png` |

Screenshots in `docs/assets/adaptive_scope_spike/`.

## Rubric

| Dimension | P1 circle-packing | P2 3-D shells |
|---|---|---|
| Correspondence-faithfulness | **High** — containment = nesting, polarity = concentric bands; ligature cross-cut routing approximate | Med–High — containment = z-nesting, crossings *vivid*; occlusion can hide structure |
| Focus + context | **High** — zoom-into-cut is canonical; whole graph → drill in | Med — orbit/dolly; context lost behind shells; no semantic collapse yet |
| Scalability to 100+ cuts | **High** — 86 packed legibly in 8 ms; 250 would pack fine | Med — wide-shallow → flat grid (the common corpus shape); deep → good but rare |
| Implementation cost / risk | **Low** — D3 pack is mature; near-1:1 with the notation | Med–High — 3-D camera, occlusion, labels, picking, WebGL |
| Peircean fidelity | **High** — nested ovals *are* Peirce's notation; recto/verso as bands | **High (conceptually)** — literal out-of-plane negation + endoporeutic fly-inward — the "moving pictures of thought" dream |

## Round 2 — the 2.5-D negation well (after design feedback)

Author feedback on round 1 sharpened two things: (1) **polarity must stay crystal-clear and
cheap** — simple alternating **white/gray** on the *value* channel — explicitly so the richer
channels stay **reserved for a future Gamma foray** (Peirce's **tinctures** → hue + texture;
the **broken cut / dotted lines of identity** → line-style); and (2) the 3-D depth of P2 is
compelling *if you can rotate to let nesting express itself in depth*, but the **danger** is
losing the parent–child clarity that 2-D enclosure conveys for free.

Built **P3 — the 2.5-D "negation well"** (`negation-well.html`) to resolve both:
- The **circle-packing footprint is the floor** (identical to P1), **negation depth is height**.
  **Top-down view IS the 2-D circle-packing** (`p3-well-deep-topdown.png`) — parent–child
  unambiguous by enclosure, the safe home. **Tilt/orbit lifts the rings into a telescoping
  well** (`p3-well-deep-tilt.png`) — the depth that was cramped in 2-D opens up, exactly the
  "loosen the flat constraint" the feedback asked for.
- **The danger is defused by construction:** child footprints stay nested inside parent
  footprints (the downward projection is always a valid containment map), and faint **parent→child
  struts** give a viewpoint-independent containment cue. You can always tilt back to top-down to
  recover the exact 2-D reading.
- **Polarity on value only:** crisp **white ring = recto, gray ring = verso** (read clearly even
  when tilted); hue + texture + line-style left entirely unspent (`spike-common.js polarityFill`,
  with `tinctureHatch`/`modalDash` reserved). Forward-compatible with Gamma by construction.
- Wide-shallow graphs (SUMO 86, `p3-well-sumo86-tilt.png`) use the compact packed floor — **no
  grid degradation** like the free-floating P2. The same projection subsumes both regimes.

This is the standard, proven pattern (CodeCity / 3-D treemaps / Beamtrees: footprint carries
containment, height carries the extra variable) and it **unifies P1 and P2** — P1 is the
top-down limit; P2's depth-fan reappears on tilt.

## Decision

**The 2.5-D negation well (P3) is the recommended projection.** It is the synthesis: it keeps
P1's unambiguous containment and instant whole-graph view (top-down) and its near-1:1 fidelity
to Peirce's nested ovals, *and* gains P2's depth reading (the endoporeutic well; a line of
identity threading its negation layers) on tilt — without P2's parent–child ambiguity or its
wide-shallow grid degradation. Polarity is crisp white/gray on the value channel; hue/texture
and line-style are reserved for Gamma. Round-1 P1 and P2 remain in the spike as reference
points (P1 = the top-down limit; P2 = the free-floating shells whose weaknesses motivated P3).

**P-hyperbolic is not needed** — top-down circle-packing already delivers whole-graph +
focus+context; the well adds depth on top.

## Round 3 — diachronic lenses (the flow of a line of thought)

The synchronic lenses view *one* EGI; a UoD is fundamentally a *process* (an evolving DAG of
states). Which view best supports the **flow of a line of thought**? Key reframe: the third
dimension was *imposed* on negation depth (2-D handles nesting natively) but is **earned** by the
diachronic axis — derivation order is genuinely orthogonal to the page — and a time view can be
built from the **real styled 2-D sheets**, so it *preserves* the Dau/Peirce conventions the
circle-packing well discarded.

Built two Organon lenses over a new read-only substrate
**`GET /organon/uods/{id}/history-structure`** (per-frame styled SVG + geometric `layout` +
per-step `legible_diff`; reuses `generate_layout` + `egi_diff`; each frame §3.3-attested):

- **Storyboard** (`storyboard.html`) — the states as a row of styled sheets, the rule + the
  EG-vocabulary diff + the authored annotation between them. **Immediately legible**; the whole
  argument at a glance (Praeclarum: blank sheet → DC+ → INS → IT+ …). `d1-storyboard-praeclarum.png`.
  The dependable baseline; the diachronic companion to reading a proof's numbered lines.
- **Time-stack** (`time-stack.html`) — the real styled sheets stacked along a derivation
  z-axis, **blue survivor threads** connecting an element that persists step→step (a thread that
  begins/ends marks what a rule added/erased). `d2-timestack-praeclarum.png`. **Concept proven,
  framing rough**: it confirms the styles survive depth and that survivor-continuity reads as
  threads, but needs tuning (camera, sheet spacing, drawing-vs-white-backing prominence) and is
  most legible when looking *along* the film. Survivor threads also exposed that the per-frame
  layouts aren't positionally conservative across the chain (threads slope) — a real finding:
  the production version wants conservative layout so survivors stay columnar.
  **→ Production (2026-06-15): `src/web_viewer/js/time-stack-lens.js`.** The "sloping threads"
  finding resolved without a conservative *layout* engine (which couldn't move an element
  independently of its drawn sheet without breaking correspondence): each frame is instead
  **rigidly registered** onto the previous by the best survivor-matching similarity (uniform
  scale + translation) — survivor drift on Praeclarum dropped 45.9 → 11.9 (~75 %), threads now
  read columnar. Camera/labels/entry-exit-dots tuned. See `ADAPTIVE_SCOPE_VIEWER.md` §10.

Decision: **storyboard is the immediate win** (legible, low-risk, the default time view);
**time-stack is the showpiece** for the "moving pictures of thought" — keep, tune later. The
**derivation-DAG** lens (branch structure) is still unbuilt and is the right next diachronic
experiment once a branching episode exists to exercise it.

## Next (returns to plan mode for the implementation plan)

Build the **2.5-D negation well** as a first-class projection alongside ELK/tension (consuming
the structure endpoint), wired into Organon first, with the white/gray reserved-channel
encoding and the top-down⇄tilt camera. Design the **navigation-projection attestation
semantics** (`attest_overview`: a collapsed/overview view is *not* a full §3.3 correspondence —
verify the visible part + faithful summaries; full §3.3 governs the expanded drawable); add the
server overview+expand path for the true perf frontier; reserve the hue/texture + line-style
channels for the eventual Gamma tinctures / broken cut; then the deferred cross-mode UX
consistency pass (shared design system, camera unification, terminology).
