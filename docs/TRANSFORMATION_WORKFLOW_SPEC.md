# Transformation Workflow Specification

**Status:** reviewed design (2026-06-04), not yet implemented.
**Scope:** how the Ergasterion (and later Agon) UI lets a user select the
proper sub-graph — *including an empty space* — and carry out each of the
six Dau transformation rules, with a *consistent* look-and-feel between
rules and within each rule.

This document is the output of the "per-rule sub-graph selection review"
(CURRENT_PLAN "After this" item 0). It reconciles three things:

1. the **logic** (Dau's six rules, the actual engine in
   `formal_transformation_rules.py` / `rule_interaction.py`);
2. the **author's workflow vision** (a consistent grammar across rules,
   with visual continuity between successive states);
3. **what the code can express today** (and where it cannot).

Companion: [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
(the regimes, §3.3, regime-3 presentation ops) and
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (why each step is an attested
sign-transition).

---

## 1. The grammar: four beats, two families

Every rule application is one episode in a four-beat rhythm:

> **① Spot → ② Subject → ③ Commit → ④ Settle**

- **① Spot** — a *region/area*: the sheet, or the interior of any cut.
  The "pick a spot where it will appear."
- **② Subject** — a *closed proper sub-graph* (per `SubgraphClosureValidator`):
  either **selected** from the canvas, or **authored/copied into a buffer**
  that is then placed.
- **③ Commit** — the rule applies; the result appears.
- **④ Settle** — a logic-preserving rearrangement that makes the result
  *visually recognizable* (see §3). Two parts: automatic continuity (the
  engine) and manual touch-up (regime-3).

The six rules split into **two families** that use the beats differently.
This split is the organizing principle that makes the look-and-feel
consistent *between* rules while honoring that adding material and removing
material are genuinely different acts:

| Family | Rules | Beats | The "Spot" | The distinguishing visual act |
|---|---|---|---|---|
| **Placing** (adds material) | DC+, INS, IT+ | Spot + Buffer/Subject + Commit + Settle | **chosen** | a **ghost/preview** at the chosen spot ("where will it land?") |
| **Removing** (takes material) | ERA, DC−, IT− | Subject (+ justification) + Commit + Settle | **implied** by the subject | a **justification highlight** ("why is this legal, and what exactly goes?") |

Same skeleton, two visual dialects. A Placing rule asks *where* and *what*,
and shows you a preview of the addition. A Removing rule asks only *what*,
derives *where* from it, and proves the move legal by highlighting its
warrant before you commit.

---

## 2. Per-rule workflows (checked against the logic)

Each rule is given as its beats, then the constraint the engine actually
enforces, then any **gap** between the workflow and today's code.

### Placing family

#### DC+ — Double Cut Insertion ("insert a double negative")
- **Spot:** any area, any polarity (a double cut is logically inert).
- **Subject:** a closed sub-graph to wrap — *or nothing*.
- **Preview:** the two ovals drawn around the chosen subject (or empty) at
  the spot.
- **Logic:** a double cut may wrap any proper sub-graph in any context, or
  be empty at any spot.
- **⚠ Gap (logic-expressiveness, the one real one):** the engine equates
  *no selection* with *enclose everything in the target area*
  ([formal_transformation_rules.py:160-165](../src/formal_transformation_rules.py#L160-L165)).
  So a **truly empty** double cut is only achievable in an *already-empty*
  area. "A double negative at any spot, even around nothing" is **not
  expressible** for a non-empty area — there is no way to drop an empty
  double cut as a sibling beside existing content. The UI must therefore
  make three cases explicit and unambiguous, and the third needs an engine
  change:
  1. wrap **these selected** elements — ✓ works (`selected_subgraph`)
  2. wrap **everything in this area** — ✓ works (today's empty-selection default)
  3. wrap **nothing** (empty double cut as a new sibling) — ✗ needs
     `DoubleCutInsertionRule` to honor an *explicit-empty* selection
     distinct from "no selection." **Protected change.**

#### INS — Insertion (in a negative context)
- **Spot:** a **negative (verso)** area — enforced. The sheet is positive,
  so it must *visibly refuse* INS.
- **Subject (Buffer):** **authored**, not selected — the content does not
  exist on the canvas yet. Compose EGIF (later: draw) into a buffer, then
  place it at the spot.
- **Preview:** the authored content ghosted inside the chosen negative area.
- **Logic:** any closed graph may be inserted into an odd-depth area.

#### IT+ — Iteration
- **Spot:** the source's own area, or **any area nested within it**
  (descendant or equal — [formal_transformation_rules.py:675](../src/formal_transformation_rules.py#L675)).
- **Subject (Buffer):** **selected** from the canvas, then copied into the
  buffer.
- **Preview:** the copy ghosted at the destination, with its lines of
  identity connecting back to the originals.
- **⚠ Known wrinkle:** passing the *full closed set* as the source trips
  "All source elements must be in the same area." The UI should pass the
  single top element and let closure expand internally, or we fix the
  message (cosmetic engine-message change).

> **The buffer unifies INS and IT+:** both are "fill a buffer (by authoring
> or by copying), then place it at a chosen spot." The only differences are
> *how the buffer is filled* and *which spots are legal*. The UI should make
> them feel like one gesture with two sources.

### Removing family

#### ERA — Erasure (in a positive context)
- **Subject:** any closed sub-graph in a **positive (recto)** area.
- **Spot:** *implied* — wherever the subject sits; must be positive.
- **Justification:** positivity ("anything can be erased here").
- **Need:** **closure must be visible** — selecting one edge erases its
  whole closed sub-graph (incident vertices, etc.); the user must see that
  before commit.

#### DC− — Double Cut Erasure ("remove a double negative")
- **Subject:** a double-cut *pair* — two **adjacent** nested cuts with
  nothing in the area between them.
- **Justification highlight:** click *any* cut → if it is part of a legal
  pair, **both ovals highlight** and the UI says "these two cuts go; their
  contents stay." If it is not a legal pair, the affordance stays inert
  (the "it should be obvious what will be erased" requirement).

#### IT− — Deiteration
- **Subject:** a *copy* that is licensed by an identical original in a
  dominating area.
- **Justification highlight:** select the copy → the UI **highlights the
  governing original** (via `graph_isomorphism_engine`) that permits the
  erasure. Without that highlight deiteration looks arbitrary; with it, it
  is obvious *why* this is a legal removal ("identify the governing
  sub-graph that permits it").

---

## 3. The Settle beat: visual continuity as a first-class requirement

The author's strongest design point: **a transformation must preserve the
visual family resemblance between the before and after states.** Peirce's
existential graphs are "moving pictures of thought" precisely because human
visual pattern-recognition is doing the reasoning work. If applying a rule
triggers an algorithmic re-layout so dramatic that the resulting graph is no
longer recognizably *the same picture, plus or minus one element*, the user
loses the thread — they cannot see *what was added* or *what was removed*.
That breaks the central promise of the medium.

**The governing principles of visual continuity are not yet fully known and
are a subject of further study.** The v1 guiding principle is **layout
conservatism**: change the drawing as *little* as possible consistent with
the new logic, so the diff is locally legible — the addition appears in an
obvious new place; the removal leaves an obvious gap; everything that
survived stays where it was.

Settle therefore has **two parts**:

### ④a — Automatic continuity (the layout engine)
After Commit, the new state is re-drawn. This re-draw must be *incremental*,
not cold:
- Elements that survive the transform should keep their positions.
- A new element should be placed *near where it belongs* in the existing
  picture, perturbing neighbors minimally.
- A removed element's neighbors should *not* stampede to fill the gap.

**Where this logic resides, and how much it can anticipate.** Continuity is
*not* left to the user, and it is *not* reverse-engineered by diffing two
finished layouts. It lives in a **continuity policy in the projection
layer** (beside the engine/renderer, never in the math core — it is drawing,
not logic), driven by two inputs the apply path already holds:

1. **`previous_layout`** — positions of every surviving element (where things
   *were*);
2. **the transformation's `changes_made` diff** — exactly what was added,
   removed, or re-parented. Every rule already emits this (e.g.
   `DoubleCutInsertionRule` records `{outer_cut, inner_cut, enclosed_elements}`).

Driving from the *known* diff (not a post-hoc visual comparison) means we
never guess what changed — the rule tells us. So the policy can pin survivors
and place only the new material, and most of the continuity is **anticipated
programmatically**. The user's regime-3 touch-up (④b) is the small residual
for genuinely aesthetic cases; the goal is ④a doing ~90% so ④b is a light
touch, not the reverse.

Each rule has a natural **minimal-surprise signature** the policy encodes:

| Rule | Anticipated continuity behavior |
|---|---|
| DC+ | subject does *not* move — two ovals appear *around it in place* (empty: small double cut at the spot) |
| DC− | the two ovals *vanish*; contents stay put |
| ERA | sub-graph disappears; survivors hold; an obvious gap remains |
| INS | new content appears *at the chosen spot*; everything else holds |
| IT+ | copy appears at destination, ideally *echoing the original's shape* |
| IT− | copy disappears; survivors (incl. the governing original) hold |

v1 makes "conservatism" measurable: **minimize total displacement of
surviving elements subject to the new logic.** ELK's interactive /
fixed-position mode approximates this when seeded with the previous positions
— which is exactly the `layout_deltas` channel that is currently a no-op
(below). The deeper perceptual principles of "family resemblance" remain a
subject of further study; displacement-minimisation is the sensible first
heuristic.

**Two view conventions (camera management).** Visual continuity needs *two*
different camera behaviours depending on how much the content's size changes:
- **Hold-camera (stable viewport)** — for *small, local* changes (editing in
  the workshop): the view must not move, survivors keep their exact screen
  position, the user's focus is undisturbed. This is the Ergasterion/Agon
  convention (1a above).
- **Fit-to-content + animated dolly** — for *guided playback of states that
  vary widely in size* (the chain player walking a proof from a blank sheet to
  a full graph and back): each state is fitted so the whole (sub-)graph stays
  in scope, and the camera *dollies* (eased zoom + pan) from one frame's view to
  the next rather than snapping. This is the standard convention in graph
  editors and slide frameworks. Holding the camera here is *wrong* — a zoom set
  for one state overflows another. (Caveat the author noted: when sizes differ
  *dramatically*, no single zoom keeps everything both fully visible and
  legibly large; the accepted fallback is a comfort margin + a minimum legible
  zoom, then let the user pan/zoom with a "Fit" affordance.)

**Ligature continuity (Beta).** When a transform acts on an element sitting
on a line of identity — removing a spot on the line (IT−), or erasing a cut
the line crosses (DC−) — the *same continuous line* must still visibly thread
the picture afterward. The surviving geometry of the ligature must be **held
fixed**, not rerouted, or the family resemblance breaks even though the logic
is sound. The logic already preserves the *crossing-sequence* (see
`project-ligature-crossing-topological-invariant`); recognizability also
needs the *visual path* held stable. This is a distinct continuity
requirement the Beta modus ponens exemplar surfaces (§6.2).

**⚠ Current state — the hook exists but is a no-op.** `layout_service`
builds `LayoutDelta`s from the `previous_layout` and passes them to
`ELKLayoutEngine.generate_layout(..., layout_deltas=…)`
([layout_service.py:54-63](../src/web_api/services/layout_service.py#L54-L63)),
**but `generate_layout` never consumes the `layout_deltas` parameter**
([elk_layout_engine.py:48](../src/elk_layout_engine.py#L48) — it is accepted
and dropped). So every transform today runs ELK *cold* and re-lays-out from
scratch. This is the single biggest obstacle to visual continuity.

This belongs to the *projection* layer (it is about drawing, not logic), so
it composes cleanly with `NaturalLayout` and is invisible to §3.3 (which
reads the resulting DTO geometry regardless of how it was produced).

#### Experiment 2026-06-04 — "feed prior positions to ELK interactive" does **not** work
The obvious first attempt (consume `layout_deltas`: seed surviving nodes with
their prior coordinates + switch ELK to its interactive layering/crossing
strategies) was prototyped and **measured against the real Praeclarum chain**,
then reverted. Findings:

- **ELK is deterministic** for identical input (drift 0.0 over repeated runs)
  — good: continuity is tractable, and the cold "jump" is fully reproducible,
  not random.
- **Naive interactive seeding regresses every step.** Feeding absolute prior
  centres as seeds made surviving-element drift *worse* (≈80→724, 435→1666 px
  on steps 3 and 7) — ELK's INTERACTIVE *layering* reinterprets raw x across
  the changed hierarchy and reshuffles.
- **Parent-relative seeding is inconsistent.** Converting seeds into each
  area's local frame helped the shallow step (IT+ 788→179) but badly regressed
  the deeper ones (INS/IT+/IT−/DC−, up to 3400+ px). Re-parenting was *not* the
  cause (the chain re-parents almost nothing); the culprit is ELK's interactive
  strategies interacting with per-cut padding/nesting in opaque, fragile ways.

**Conclusion: automatic continuity is not an ELK option-flip.** A reliable
layer must *own* the placement rather than delegate the whole graph to ELK each
time. Candidate approaches, to be chosen deliberately (this is the "principles
not yet known — subject of further study" the author flagged):

1. **Stable viewport (cheapest, frontend-only).** ELK being deterministic, the
   biggest *perceived* jump is the camera: `svg-pan-zoom` re-`fit`s and
   re-`center`s on every render. Holding the viewport across a step removes
   most of the felt discontinuity with zero layout change. *Do this first.*
2. **Animated transition (frontend-only, philosophically apt).** Interpolate
   element positions old→new DTO. Human vision tracks *motion* superbly — the
   literal "moving picture" — so even a changed layout stays followable. High
   value-to-effort.
3. **Pin-and-place (the real "own the layout" investment).** Keep survivors'
   absolute positions fixed; run ELK (or a local heuristic) only on the changed
   sub-area to place new material. ELK demoted to a *local* optimizer within
   fixed survivors — consistent with `project-render-as-projection`. The
   principled but larger build.

The `changes_made` diff each rule emits is still the right driver for (2)/(3):
it says exactly what is new / removed / moved, so the policy never guesses.

### ④b — Manual adjustment (regime-3)
Even a conservative auto-layout will sometimes want a human nudge. After the
auto-redraw, the user may refine the appearance *without touching the logic*
via the regime-3 presentation algebra — `move_vertex`, `reshape_cut`,
`reroute_ligature` (`presentation_ops.py`), each of which refuses any
boundary-crossing change (raising `Regime3Violation`). These operations are
**built and tested** but **not yet wired to the canvas**
(CURRENT_PLAN: "Transformation UI w/ regime-3 (drag/reshape) affordances —
not started"). Until they are, Settle's manual half does not exist, and the
four-beat workflow is incomplete for all six rules.

---

## 4. Cross-cutting findings (the consistency audit)

1. **The canonical Ergasterion regressed on selection feedback.** The legacy
   `index.html` viewer had closure validation, auto-complete, and
   missing-element highlighting; the canonical `ergasterion.html` (the
   inline script) does not. The Subject beat needs a live "this closes up to
   N elements" preview restored and bettered.
2. **Spot is half-built and signaled by a hidden convention.** Cut interiors
   are reachable only because the cut shape is shift-clickable; the **sheet
   has no affordance** (the most important empty space — the start of every
   theorem proof). For a consistent feel, Spot and Subject should be
   *distinct, prompted acts* driven by the `/rules` step descriptors, not a
   modifier key.
3. **DC+ empty-double-cut semantics are ambiguous and partly
   unimplementable** (§2, DC+ gap).
4. **The two families must look deliberately different** — ghost-preview for
   Placing, justification-highlight for Removing — over one shared skeleton.
5. **Visual continuity is unbuilt at the engine level** (§3a no-op) and the
   manual half (regime-3 on canvas) is unbuilt too (§3b).

---

## 5. Build order (keystone-first)

Visual continuity is shared by all six rules and dominates three of the six
descriptions, so it is a **keystone, not a follow-up**.

1. **Automatic continuity (④a).** *Revised after the 2026-06-04 experiment
   (§3a): the ELK-interactive option-flip regresses and was reverted.* The
   foundation is staged:
   - **(1a) stable viewport — ✅ done + browser-verified.** Hold the camera
     (absolute scale + pan) across a continuation render; fresh open fits.
   - **(1b) animated transition — ✅ done + browser-verified.** FLIP on
     survivors + fade-in for new elements (`js/diagram-transition.js`), so
     motion keeps the picture followable.
   - **(1c) pin-and-place — subtractive case done.** Own survivor positions
     instead of re-flowing the whole graph. Split by the step's effect:
     *subtractive* (ERA / IT− / DC−) keeps survivors at their **exact** previous
     positions (the new element set is a subset of the old — nothing new to
     place); `layout_service._subtractive_layout` does this, §3.3-attested with
     a full-layout fallback (verified 0px drift on real DC−/IT− steps).
     *Additive DC+ wrap* is also done (`_additive_cut_layout`): DC+ adds only
     cuts, so survivors keep their exact positions and cut bounds are recomputed
     bottom-up around them (verified 0px drift on plain / Beta / multi-sibling /
     enclose-all). *INS and IT+* still fall back — placing genuinely new
     vertices/predicates in the survivors' frame, overlap-aware, is the harder
     remaining increment. Measurement ruled out the cheap alternatives: with
     deterministic ordering, survivors still drift 50–235px/step under full
     ELK, and rigid re-anchoring is insufficient (similarity-fit overfits to a
     degenerate flip on few points).
   §3.3 unaffected throughout.
2. **The Spot/Subject grammar with closure preview.** First-class region
   selection (incl. the sheet), driven by `/rules` step descriptors; restore
   closure preview; the two visual dialects (ghost-preview vs
   justification-highlight). Mostly unprotected UI + additive routes.
   *In progress (2026-06-05), built as increments:*
   - **2a — region/empty-space selection incl. the sheet + rule-step
     guidance. ✅ done + browser-verified (2026-06-05).** The sheet (the most
     important empty space — every theorem proof starts there) had no
     affordance; now **shift-click empty space selects the open sheet** (and
     shift-click a cut its interior), the sheet id coming from the session
     payload (`layout_dto.sheet_id` / `introspection.areas`). Each chosen rule
     shows a **step checklist** from `/rules` ("INS needs: ① content ☐ ②
     negative region ☐"), checks filling as you select. Verified in Chrome.
   - **2b — closure preview. ✅ done + browser-verified (2026-06-05).** A rule
     acts on a *closed* sub-graph, so selecting a **cut pulls in all its
     contents** (the user's point), an edge pulls in its vertices, etc. `POST
     /ergasterion/sessions/{id}/closure` runs the authoritative
     `SubgraphClosureValidator` on the session state; the workshop marks the
     *pulled-in* elements (dashed `.sel-closure`) and notes "closes to N (+M
     pulled in)". **DC− is the exception** (the user flagged it): its selected
     cut-pair is removed while the enclosed contents *stay*, so DC− is not
     treated as closure-as-acted-on — it shows "DC− removes the double cut;
     enclosed contents stay". Verified: ERA+cut → +3 pulled in; DC−+cut → the
     exception note, no pull-in.
   - **2c — step-driven click dispatch** (a click means *element* on a Subject
     step, *region* on a Spot step — resolving the cut-as-subject vs
     cut-interior-as-region ambiguity), and the two visual dialects.
3. **Manual Settle (④b).** Wire `move_vertex` / `reshape_cut` /
   `reroute_ligature` onto the canvas, refusing boundary crossings.
4. **DC+ empty-double-cut semantics.** Resolve the one logic-expressiveness
   gap — let DC+ honor an explicit-empty selection. **Protected change**
   (`rule_interaction.py` / `formal_transformation_rules.py`): requires
   `.core_modification_authorized` and the core suite staying green.

Items 1–3 are largely additive; item 4 is the only protected-module change.

---

## 6. Validation against the seeded exemplars

The grammar was walked step-by-step against the two real
`TransformationChain`s in the corpus (built by `tools/build_praeclarum_chain.py`
and `tools/build_beta_modus_ponens_chain.py`). Every step is unambiguously
Placing or Removing, and the Spot/Subject/justification slots fill correctly
— the grammar holds. Two refinements came out of it (DC+ empty-area
confirmation; ligature continuity).

### 6.1 Praeclarum Theorema — 7 steps, blank sheet → theorem

States as actually produced by the chain:

```
base:           (blank)
1. DC+  →  ~[ ~[ ] ]
2. INS  →  ~[ ~[ ] ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] ]
3. IT+  →  ~[ ~[ ~[ (P) ~[ (R) ] ] ] ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] ]
4. INS  →  ~[ ~[ ~[ (P) (Q) ~[ (R) ] ] ] ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] ]
5. IT+  →  ~[ ~[ ~[ (P) (Q) ~[ (R) ~[ (Q) ~[ (S) ] ] ] ] ] ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] ]
6. IT-  →  ~[ ~[ ~[ (P) (Q) ~[ (R) ~[ ~[ (S) ] ] ] ] ] ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] ]
7. DC-  →  ~[ ~[ ~[ (P) (Q) ~[ (R) (S) ] ] ] ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] ]
```

| # | Rule | Family | Spot | Subject | Continuity (minimal-surprise) |
|---|---|---|---|---|---|
| 1 | DC+ | Placing | the **blank sheet** | *nothing* (empty) | two ovals appear on the empty sheet |
| 2 | INS | Placing | outer cut interior (neg) | authored antecedent | inner empty cut holds; two scrolls appear beside it |
| 3 | IT+ | Placing | the inner cut | copy of (P⊃R) | clone nested in inner cut, **echoing** the original's shape |
| 4 | INS | Placing | the copied (P⊃R)'s cut (neg) | authored `(Q)` | `(Q)` appears beside `(P)`; everything else holds |
| 5 | IT+ | Placing | the cut around R | copy of (Q⊃S) | clone nested by R, echoing the original |
| 6 | IT− | Removing | *implied* | inner `(Q)` | inner Q vanishes; governing original = enclosing `(Q)` |
| 7 | DC− | Removing | *implied* | double cut `~[~[(S)]]` | rings vanish; `(S)` stays put, lands beside `(R)` |

Findings: **(a)** Step 1 confirms the DC+ empty-double-cut works *only because
the sheet is empty* (§2 DC+ gap) — in practice the empty double cut is almost
always on the blank sheet or an empty area, so the gap rarely bites, but the
UI must still distinguish "wrap nothing" from "wrap everything." **(b)** The
INS/IT+ spots are *cut interiors*, not the sheet — region selection must cover
cut interiors. **(c)** The shape grows (1–5) then contracts (6–7); without ④a
the picture would re-flow cold 7 times.

### 6.2 Beta modus ponens — 2 steps, premises → conclusion

```
base:        *x (P x) ~[ (P x) ~[ (Q x) ] ]
1. IT-  →    *x (P x) ~[ ~[ (Q x) ] ]
2. DC-  →    *x (P x) (Q x)
```

- **Step 1 (IT−, Removing):** subject = the inner `(P x)`; governing original
  = the `(P x)` **on the sheet**, on the same line of identity `x`.
- **Step 2 (DC−, Removing):** subject = the double cut; `(Q x)` stays on its
  line and lands beside `(P x)`.

Both moves act on spots sitting on the shared line `x`. This is what surfaced
the **ligature-continuity** requirement (§3a): the surviving geometry of `x`
must be held fixed across both steps, so the eye sees one continuous line
losing a spot / shedding its cut — not a rerouted tangle.
