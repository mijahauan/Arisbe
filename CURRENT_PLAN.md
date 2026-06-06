# Current Plan

**Last Updated**: 2026-06-06 (Manual Settle ④b drag layer + DC+ empty-double-cut semantics)

Living scratchpad for where development stands and what's next. The
durable vision lives in [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md);
this file tracks the active front. The pre-commit quality gate reads the
**Last Updated** date here, so keep it current.

---

## Session 2026-06-06 — Manual Settle ④b + DC+ empty-double-cut (both shipped)

Completed the two threads at the top of the prior session's start list:
**#1 Manual Settle ④b** (the four-beat workflow's final beat) and
**#3 DC+ empty-double-cut semantics** (the one logic-expressiveness gap).
All on `main`; full suite **941 passed, 35 skipped**; quality gate green.

**#1 Manual Settle ④b — the regime-3 drag layer (browser-verified).**
The four-beat grammar (Spot→Subject→Commit→Settle) now has its manual
touch-up. The workshop canvas drags to tidy appearance *after* a transform,
logic held fixed:
- **Backend** — `layout_service.attest_and_render(egi, dto)` renders an
  already-built DTO (no ELK pass, so the nudge survives) and still §3.3-attests.
  `POST /ergasterion/sessions/{id}/adjust` dispatches to `presentation_ops`
  (`move_vertex` / `reshape_cut` / `reroute_ligature`); pure presentation
  (EGI untouched, **no chain step**); `Regime3Violation` → clean `REGIME3_VIOLATION`.
- **Frontend** — `web_viewer/js/settle-adjust.js` (self-contained): a Settle
  toggle; drag a **vertex** (→ move_vertex), a **cut corner handle** (→
  reshape_cut), or a **line of identity** (→ reroute_ligature). Screen→DTO via
  the pan-zoom viewport CTM + the renderer's `(-min+pad)` offset (deltas are
  offset-invariant; absolute bounds/waypoints subtract the offset). Re-renders
  with the camera held (1a) and redraws handles. The ligature `<path>` is now
  tagged `data-predicate-id`/`data-vertex-id`/`data-port-index` (renderer,
  unprotected; Dau output still byte-identical — attrs are additive).
- **The layered guarantee, made a contract.** A reshape can satisfy
  `presentation_ops`' own membership guards yet still break §3.3 (enlarging a
  cut so a ligature newly crosses it) — `attest_and_render` is the authority
  and refuses it as `CORRESPONDENCE_VIOLATION`. `presentation_ops` = local
  guards; attestation = the backstop. Pinned in a route test.
- **Browser-verified** (system Chrome): Settle on → 8 handles (4 corners × 2
  cuts); vertex drag +70,+45px moved the spot **exactly** +70,+45px (coordinate
  transform is pixel-exact), move_vertex + reshape_cut + reroute_ligature all
  round-tripped "appearance updated (logic unchanged)". Tests:
  `test_ergasterion_routes.py` (+6).

**#3 DC+ empty-double-cut — "a double negative at any spot, even around
nothing" (protected change).** DC+ used to equate empty selection with
*enclose the whole area*, so a truly-empty double cut only worked in an
already-empty area.
- `formal_transformation_rules.py` — `TransformationContext.enclose_empty:
  bool = False` (additive). DC+ now: non-empty selection → enclose those; empty
  + `enclose_empty` → empty double cut around nothing; empty + not → legacy
  whole-area wrap (backward-compatible).
- `rule_interaction.py` — `DCPlusInteraction` gains an optional `SELECT_AREA`
  step (the Spot). Empty Subject + explicit Spot → `enclose_empty=True` in that
  area; nothing at all → legacy sheet-wrap. The route already maps
  `SELECT_AREA → target_area`, so no route change.
- **UI** — DC+ param form gains a Spot field (shift-click a region fills it);
  `readRuleParameters` sends `target_area`. Browser-verified: empty double cut
  inserted into the non-empty cut `c_6ea5bf60` (cut_count 2→4) *without*
  wrapping its contents. Tests: `test_rule_interaction.py` (+3),
  `test_introspection_and_rules.py` updated.
- Needed `.core_modification_authorized` + core suite (415 passed directly);
  `docs/ARISBE_CORE_API_REFERENCE.md` regenerated.

**Start next session with one of (rough priority):**
1. **INS / IT+ positional pinning** (the remaining ④a 1c additive case) — place
   genuinely new vertices/predicates in the survivors' frame, overlap-aware
   (§3.3 won't catch visual overlap, so the safety net is weaker). The agreed
   pause point; the hardest continuity increment.
2. **Dogfood the now-complete four-beat grammar** on a real multi-step proof
   end-to-end in the browser (compose → settle each step → promote); a literal
   **ghost-preview** for Placing rules.
3. **Agon V2** (semantic-evaluation inner layer / auto-Grapheus / dynamic M) or
   a first-class **warrant gradient**.

---

## Session 2026-06-05 — done this session, and where to start next

The per-rule sub-graph selection review (the prior session's directive) was
completed and turned into a built-out **transformation workflow** layer. See
[docs/TRANSFORMATION_WORKFLOW_SPEC.md](docs/TRANSFORMATION_WORKFLOW_SPEC.md)
(the design + status) and memory `project-transformation-workflow-grammar`.

**Shipped + verified this session (all on `main`, pushed):**
- **Reviewed grammar** — four beats (Spot→Subject→Commit→Settle), two families
  (Placing / Removing); visual continuity is the keystone. Validated against the
  real Praeclarum (7-step) and Beta modus ponens chains.
- **Settle ④a continuity** — 1a stable viewport (workshop hold-camera), 1b FLIP
  animation, 1c positional pinning for **subtractive** rules (ERA/IT−/DC−) +
  **DC+ wrap** (survivors move 0px; §3.3-attested, full-layout fallback).
- **Diachronic chain player** (Organon) — play a worked proof step-by-step;
  **view-style selector** (Dau/Peirce/Sowa) without the export path.
- **Spot/Subject grammar 2a/2b/2c (complete)** — sheet/region selection;
  per-rule `/rules` step checklist; closure preview (a cut pulls in its
  contents; DC− "cuts go, contents stay"); step-driven click dispatch (no
  modifier); justification highlights (DC− pair, IT− governing original, ERA
  positivity).
- **Layout fixes** — empty cuts visible (`EMPTY_CUT_MIN_SIZE`); id-independent
  `_structural_key` ordering (IT+ copies no longer flip; layout reproducible);
  removed "Existential Graph"/stats chrome; per-frame "shape".

**Start next session with one of (rough priority):**
1. **Manual Settle ④b** — wire `presentation_ops` (`move_vertex` /
   `reshape_cut` / `reroute_ligature`, already built + tested) to the canvas,
   completing the four-beat workflow (lets a user tidy appearance after a
   transform, logic-preserving). The natural completion of the Settle arc.
2. **INS / IT+ positional pinning** (the rest of 1c) — the hard *additive*
   case: place genuinely new vertices/predicates in the survivors' frame,
   overlap-aware (§3.3 won't catch visual overlap, so the safety net is weaker).
3. **DC+ empty-double-cut semantics** — the one **protected-module** change
   (`rule_interaction.py`/`formal_transformation_rules.py`): let DC+ honor an
   explicit-empty selection so a truly-empty double cut works in a non-empty
   area (spec §2 DC+ gap). Needs `.core_modification_authorized` + core suite.
4. **Dogfood the grammar** on a real proof (the workshop is now genuinely
   usable for per-rule selection); a literal **ghost-preview** for Placing;
   **Agon V2**; a first-class **warrant gradient**.

---

## Where we are

**Phase 3 — Web UI (the three modes as routes).** The conceptual modes
(Organon / Ergasterion / Agon) map onto the three correspondence regimes
(see [docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md) §4)
and onto the Peircean chain-of-semiosis grounding (see
[docs/CHAIN_OF_SEMIOSIS.md](docs/CHAIN_OF_SEMIOSIS.md)).

| Workstream | Status |
|---|---|
| FastAPI + ELK + SVG render path, §3.3-attested at the service boundary | ✅ done |
| **Organon** (archive, read-only) | ✅ live — `/organon` (+ diachronic **chain player**: step/▶ through a worked proof, each rule application + resulting graph, with continuity; **view-style selector**: see any form/frame in Dau / Peirce / Sowa directly, no export round-trip) |
| **Ergasterion** (workshop, composition) | ✅ live — `/ergasterion` |
| Chain persistence (regime-1 → regime-2 boundary) | ✅ `tomos_service.save_uod_with_chain` / `load_chain` |
| **Agon** (Endoporeutic Game arena) | 🟢 V1 live — `/agon` (thin, flexible slice) |
| On-canvas element selection for rule application | ✅ live + browser-verified — click→select, introspection-named chips, polarity hints; **Spot/Subject grammar (2a/2b/2c complete)**: sheet/region selectable, per-rule `/rules` step checklist, **closure preview** (a cut pulls in its contents; DC− "cuts go, contents stay"), **step-driven click dispatch** (Subject step → element, Spot step → region; no modifier), **justification highlights** (DC− pair, IT− governing original via iso engine, ERA positivity) |
| Transformation UI w/ regime-3 (drag/reshape) affordances | ✅ live + browser-verified — **Manual Settle ④b**: `/ergasterion/.../adjust` + `web_viewer/js/settle-adjust.js` drag a vertex (move_vertex) / cut corner (reshape_cut) / line (reroute_ligature); pure presentation, `Regime3Violation`→clean refusal, `attest_and_render` is the §3.3 backstop |

**What the Ergasterion build settled.** Bringing the workshop online
forced the **regime-1 → regime-2 promotion boundary** into a concrete
implementation: a workshop session accumulates a `TransformationChain`
(base state + ordered `ChainStep`s) against an explicitly chosen context;
promotion forks a new `PRACTICE_SESSION` UoD and persists the whole chain,
with §3.3 attestation firing at the corpus boundary before any disk write
(clean refusal on drift). This was the strategic reason to build
Ergasterion before Agon — Agon now has a defined record to assert *into*
and *against*.

---

## Active thread: NaturalLayout — own the dimensionality

A deliberate detour ahead of dogfooding/Agon, prioritized because the
logic→spatial mapping is the project's central difficulty (the recurring
"ligatures crossing cuts illegitimately" pain). Stance and grounding:
memories `project-render-as-projection-own-dimensionality` and
`project-ligature-crossing-topological-invariant`. The renderer is a
*projection*; the projection-independent structure (containment tree,
per-ligature crossing-sequence, incidence, ports) is what we own;
conventions are the projection's free parameters; 3-D becomes additive
iff the natural layer stays coordinate-free.

**Sequencing — all five steps DONE (2026-06-01):**

1. ✅ `c9a8e71` — probe + coordinate-free `src/natural_layout.py`
   (`NaturalLayout`, `authorized_crossings`), `tools/natural_layout_probe.py`,
   `tests/test_natural_layout.py`. **Finding:** zero illegitimate /
   wrong-parity crossings across 15 corpus UoDs (49 incidences) and the
   synthetic stress + large shapes (deep-20, wide-20, comb-10, sibling-
   spanning). Verdict: the refactor is **unification, not correctness
   rescue** — the existing routing is already crossing-correct, and
   `natural_layout`'s independent computation agrees with ELK's output.
2. ✅ `ee1fe41` — unified the area-tree walk: `presentation_ops._tree_path`
   is the single source; `area_chain` (allowed areas) and
   `crossing_sequence` (cuts crossed) derive from it; `natural_layout`
   and `ELKLayoutEngine._authorized_cuts` delegate; the engine's bespoke
   walk deleted.
3. ✅ `71fe593` — §3.3 identity check upgraded from sampled-containment to
   crossing-multiset equality (`count_boundary_crossings` in
   presentation_ops; attestation requires each authorized cut crossed
   once, no forbidden cut crossed). Adversarial test added.
4. ✅ `Conventions` object (`src/projection_conventions.py`) — the
   projection's free parameters enumerated in one place: honored knobs
   (`detour_pad`, `visibility_pad`, wired through the engine) + descriptive
   fields (cut_shape, hook_placement, ligature_routing,
   ligature_crossing_marks=R6, sibling_cut_ordering). Makes the §3.3
   "convention compliance" row enumerable instead of folklore.
   `tests/test_projection_conventions.py` proves defaults = current
   behavior and that the knobs are genuinely wired.
5. ✅ dimension-free discipline locked: `test_natural_layout` now also
   forbids `natural_layout` importing any projection module (engine,
   renderer, conventions, layout_service) — so 3-D stays additive.

**Caveats kept on the record:** the crossing check counts vs axis-aligned
boxes; it validates count/parity, not crossing *order* and not
W-connectedness (the attestation's separate Identity 3/3 covers
connectedness). Synthetic stress proves structural scale, not ELK's
aesthetic placement on arbitrary real graphs — a future pathology would
surface as a real corpus/composed graph and be caught by the strengthened
attestation. The refactor is the right primitive; **3-D is now a second
projection against the same NaturalLayout, not a rewrite.**

---

## Dogfood (2026-06-01): the promotion boundary is lived, not just correct

Drove the running app API-level: opened a workshop on
`peirce_cp_4_394_man_mortal`, composed a 2-step chain (DC+ on the whole
proposition, then a vacuous DC+ on the sheet), promoted to a new forked
UoD, confirmed §3.3 passed at the corpus boundary, the chain persisted
(chain.jsonl + 3 state snapshots), `load_chain` round-tripped, and
re-promote was refused. Promote-as-fork confirmed by use. (Throwaway UoD
deleted; pre-existing `practice_43480df3` left intact.)

**Friction = the prioritized signal** (full detail in memory
`project-ergasterion-dogfood-findings`):
1. **No area/polarity introspection over HTTP** — to select for any rule
   beyond empty-DC+, the client must know an element's area + polarity;
   on-canvas the picture shows it, via API it had to be inferred. Agon is
   selection-heavy → it needs this most. **Highest-leverage next add.**
2. **Rule requirements not discoverable over HTTP** —
   `RuleInteraction.steps()` declares them but they aren't surfaced.
3. **§3.3 invisible until it fails** — a pre-promote attestation *preview*
   would show correspondence while composing.
4. **Linear-only** didn't bite at 2 steps; undo/branching will matter for
   real exploration and Agon's move/counter-move (JSONL leaves room).
5. **Promote-as-fork felt right** — keep.

Still unverified: the on-canvas *clicking* UX (hooks + JS validated; no
browser has actually clicked-to-select + promoted).

---

## Next (recommended order)

1. ✅ **Small API introspection addition (friction #1+#2)** — done
   2026-06-01. `web_api/services/introspection.py` (`egi_introspection`)
   exposes per-element area membership + per-area polarity; the
   Ergasterion session payload now carries an `introspection` block.
   `web_api/routes/rules.py` serves `GET /rules` + `/rules/{rule}`,
   surfacing each `RuleInteraction.steps()` descriptor with the request
   field a client must populate (`selected_elements` / `target_area` /
   `egif_content`). Both additive + read-only; no protected module or
   attestation logic touched. Tests: `tests/test_introspection_and_rules.py`.
2. ✅ **Agon web arena (V1, thin flexible slice)** — done 2026-06-01.
   `/agon` hosts the Endoporeutic Game as a dialogical contest, built
   *after research* (Pietarinen, *Signs of Logic* 2006, Ch. 4 + the
   repo's own `docs/ENDOPOREUTIC_GAME_GUIDE.md`) reframed the design away
   from "win → auto-assert thesis." See the Agon section below.

### Agon arena V1 (the research-informed, flexibility-first build)

**Why thin and flexible.** The EPG is genuinely untrod ground — sketched
by Peirce, never fully codified or played. The sources establish that the
game is **triadic, not a duel**: Graphist (proposal G), Grapheus (model
M), and the **Agonothetes** — the *interpretant*, the telic function that
assigns meaning *after* the contest. A two-party true/false duel is, in
Peirce's own terms, a degenerate sign-process. The interesting outcomes
are not "G proved" but the inductive/abductive/revisionary ones: the
**model is tested by the proposal** (revise M, fork the UoD, hold a
hypothesis or conjecture). So the build refuses to hardcode an outcome.

**What landed (V1):**
- `web_api/services/agon_session_manager.py` — wraps the headless engine
  (`endoporeutic_game.py`, untouched) + a structured **dialogical
  episode** (typed move log naming player, Peircean role, rule, area,
  resulting linear form; faithful per-move EGI snapshots for chain build).
- `web_api/services/agonothetes.py` — the **outcome taxonomy as data**
  (13 dispositions across deduction/induction/abduction), `available_
  dispositions`, and a thin `apply_disposition`. Open: every disposition
  is selectable; only *asserting* ones write a corpus record (firing §3.3
  at that boundary, via `save_uod_with_chain`). **Nothing auto-asserts.**
- `web_api/routes/agon.py` — `/agon` routes: start (raw EGIF / M+G frame
  `~[ M ~[ G ] ]` / `uod:<id>` as M), get, move (engine enforces
  territory + polarity), concede, **disposition** (the open Agonothetes
  step), delete, HTML, `/agon/dispositions`. Every payload carries Task-1
  introspection + `legal_areas` + role.
- `web_viewer/agon.html` — hot-seat arena: board, turn/territory banner,
  move panel (selection via `data-element-id`), episode log, and a
  disposition panel surfacing the taxonomy on game end.
- `tests/test_agon_routes.py` (15) — start/move/concede/disposition
  contract, territory enforcement, asserting-disposition chain round-trip,
  §3.3 refusal aborts cleanly.

**Deliberately deferred (kept open):** the **semantic-evaluation inner
layer** (the engine's `goal_egif` win is only a proxy — the real "is G
true in M?" / winning-strategy layer is unbuilt); an **auto-Grapheus**
(V1 is hot-seat, the guide's own model — the one inquirer holds both
roles); **dynamic M** (Pietarinen: the Grapheus may add determinations
mid-play) and the per-disposition corpus semantics (revise-in-place,
fork-the-DAG) beyond the single assert-as-new-UoD path. The taxonomy is
data and the disposition layer is a handler map, so these are additive.

### Linear-form view (all three diagram modes, 2026-06-01)

Every diagram view now carries a collapsible **linear form** beside the
drawing, with a notation selector (EGIF default; CGIF, CLIF; registry-
extensible). Picture and proposition shown together — the correspondence
made visible.
- `web_api/services/linear_forms.py` — single source of truth: an ordered
  registry over the format generators, `linear_forms(egi)` returning
  `{default, formats, forms}` with each notation generated *defensively*
  (one failing notation reports its error, doesn't break the others).
- Wired into all three diagram payloads (Organon detail, Ergasterion
  session, Agon game) — so the form tracks the current state through every
  move / rule application.
- `web_viewer/js/linear-form-panel.js` — shared, self-contained floating
  panel; data-driven selector (a new server-side notation appears with no
  frontend change); selected format + open state persist across
  re-renders. Loaded by all three pages.
- Tests: `tests/test_linear_forms.py` (7).

### Import doorway — admit a linear form at low warrant (2026-06-02)

The read-only Organon implied a doorway *into* the corpus. Built per the
philosophical floor (`docs/MANIFEST_AND_MEANING.md`): an import is
**admitted at low warrant** — parsed (comprehended), attested for §3.3
correspondence, bibliographically attributed, **never asserted as true**.
No promotion gate; no logical/Z3 check (truth isn't ours at admission).
- `web_api/services/bibliography.py` — CSL-style citation model (book,
  chapter, article-journal, webpage, generic) as data: per-type form
  fields, `format_citation`, `authors_list`.
- `web_api/services/import_service.py` — `check` (parse + round-trip
  integrity + §3.3, no persistence) and `admit` (build a standalone
  `LITERATURE_EXAMPLE` UoD, `warrant:low` tag, save_uod fires §3.3,
  persist structured bibliography sidecar).
- `tomos_service.save_bibliography` / `load_bibliography` — sidecar
  (additive to the unprotected module; structured record + formatted).
- `routes/imports.py` (`/import`): page, `/check`, `/admit`,
  `/citation-types`, `/format-citation`. `web_viewer/import.html`:
  input + grammar/round-trip/§3.3 badges + regenerated-form compare,
  data-driven bibliographic form with live citation preview, drawing +
  linear-form panel.
- Organon detail payload + page now surface imported provenance.
- Tests: `tests/test_import_routes.py` (14).

**Warrant note:** warrant is carried by category + `warrant:low` tag +
UI language, *not* a first-class field — that would touch the protected
UoD model and is a deliberate later change. Warrant rises only through
Agon (withstanding challenge) and can fall.

### Export arc + style (the outer loop closed, 2026-06-02)

World → Organon → world is now complete. Style is treated as a **projection
choice**, per `docs/MANIFEST_AND_MEANING.md`: three manifests (Dau / Peirce
/ Sowa), one meaning, each §3.3-attested.
- **Style keystone** — `layout_service.generate_layout(style_name=…)` makes
  the visual style selectable through the render path (default unchanged).
  `GET /styles` lists them. Unlocks export, view-in-style, draw-in-style.
- **Export** — `web_api/services/export_service.py` + `routes/export.py`
  (`/export`, `/export/formats`): EGIF/CGIF/CLIF, styled **SVG**, portable
  **TikZ** (`tikz_export.py`, mirrors the SVG renderer's labels/parity),
  **PNG**/**PDF** via `rsvg-convert` (runtime-guarded; reports cleanly if
  absent). Source = a corpus UoD or inline linear form. Organon detail has
  an export panel (style + format → preview/copy/download).
- **Ergasterion render-in-style** — the workshop draws in a chosen style
  (`?style=` on the session; remembered); composition stays
  style-independent. First step of the bidirectional vision.
- Tests: `tests/test_styles.py` (4), `tests/test_export_routes.py` (12).

### Peirce visual fidelity — Tier 1 (renderer honors the declared style, 2026-06-02)

Dogfood: Dau and Peirce looked nearly identical because the renderer
*under-realized* the declared style (it hardcoded black straight lines and
an upright font, ignoring `cut_shape`, ligature `routing_mode`, ink colors,
and script). Calibrated against the egpeirce documentation gallery (and
Roberts, `docs/references/Existential Graphs of Peirce.pdf`):
- `simple_svg_renderer` now honors **ink color** (cut/ligature/label), a
  **`font_style`** (italic), the **font family**, and **curved lines of
  identity** (Catmull-Rom→Bézier when ligature routing is `organic`). Dau
  output is **byte-identical** (defaults reproduce the old hardcoding); only
  styles that *declare* a difference change. §3.3 unaffected (it reads the
  DTO geometry, not the stroke).
- `peirce-authentic@1.0.json` now sets a cursive script (`Apple Chancery`…)
  + italic; Peirce labels render in Peirce's hand (and survive PNG/PDF
  export on macOS via fontconfig). Vertex dots already suppressed
  (`label_only`).
- Tests: `tests/test_styles.py` (+3).

### Peirce visual fidelity — Tier 2 (oval cuts, 2026-06-03)

Cuts now draw as **inscribed ellipses** for any style whose `cut.shape` is
`oval`/`circle` (Peirce, Sowa); Dau's `rounded_rectangle` is untouched and
**byte-identical**. The convention *feeds the layout*, it is not a cosmetic:
- An ellipse inscribed in a box contains a centered content box only if the
  box is ≥ **√2×** the content, so `ELKLayoutEngine` grows each oval cut with
  **content-proportional padding** (`_oval_padding` = `content·(√2−1)/2 +
  margin`). `cut_shape` is thereby promoted from a descriptive
  `projection_conventions` field to an **honored** one (value sourced from the
  active style).
- Nesting cascades: growing a cut grows its parent's content, so a single
  padding pass under-pads outer cuts. The engine **iterates ELK to a fixpoint**
  on cut contents (`_refit_oval_cuts`, deepest-first convergence, capped at
  `MAX_OVAL_PASSES`); the additive margin keeps it safe if the cap is hit.
- The **axis-aligned bbox stays the §3.3 container** — attestation reads DTO
  geometry, not the drawn stroke, so every styled render still attests.
- Tests: `tests/test_styles.py` (+2 — ellipse-vs-rect, and containment through
  a nested double cut).

### Peirce visual fidelity — Tier 3a (hand-drawn wobble, SVG, 2026-06-03)

`hand_drawn_variation` is now realized in `simple_svg_renderer`: Peirce's oval
cut becomes a closed, gently-wavering loop (low-frequency harmonic radial
deviation, two hashed harmonics — *not* high-frequency noise) and its line of
identity wavers (interior points nudged perpendicular). Both are:
- **Deterministic** — a hash-seeded "hand" (`_jitter`, not Python's salted
  `hash`), so renders are byte-stable across processes (invariant L1).
- **Stroke-only** — perturbs the drawn path, never the DTO geometry §3.3 reads
  (already attested before the renderer runs); amplitude is capped under the
  Tier-2 containment margin, so contents stay enclosed. Same principle as
  Tier 1's curves.
- **Scoped** — `hand_drawn_variation: 0` (Dau, Sowa) leaves a crisp
  rect/ellipse/line, **byte-identical**. Only Peirce declares wobble.
- Tests: `tests/test_styles.py` (+2 — determinism + scoping, `_jitter` bounds).

### Peirce visual fidelity — Tier 3b + 3c (TikZ parity, bridge marks, 2026-06-03)

The SVG and TikZ renderers now share one hand. The hand-drawn geometry —
hash-seeded `jitter`, the perpendicular `hand_drawn_points` waver, the
Catmull-Rom `catmull_rom_segments` curve, plus crossing detection and bridge
geometry — lives in a new coordinate-only module `src/render_geometry.py`;
`simple_svg_renderer` delegates to it (its old `_jitter` / `_hand_drawn_points`
/ `_smooth_path` are thin wrappers, output unchanged) and `tikz_export` imports
the same functions, so the two manifests of a graph agree by construction.

- **Tier 3b — TikZ parity.** A line of identity in TikZ is now an organic
  Catmull-Rom curve (`.. controls .. ..`) when the style routes organically,
  and wavers when the style declares `ligature.hand_drawn_variation` — the same
  seed (`predicate|vertex|port`) and amplitude as the SVG path, so the curves
  coincide. (In practice ELK routes most lines as 2 points, which both
  renderers draw straight; the curve/waver engages on real ≥3-point detours.)
  Dau (orthogonal) and Sowa (manhattan) declare neither → straight `--`,
  byte-identical to before.
- **Tier 3c — bridge-at-crossing marks.** `Conventions.ligature_crossing_marks`
  is now **honored**: a style declaring `ligature.crossing_marks: "bridges"`
  (Peirce does) draws Peirce's hop where two **distinct** lines of identity
  (different `vertex_id` — paths sharing a vertex are one W-class, not a
  crossing) cross in the 2-D projection. The over-line (deterministic key
  order) lifts over via a Bézier arc; the under-line is restored straight
  through. Detection runs on the authorized DTO polylines, and the hop is
  **stroke-only** — it never touches the geometry §3.3 reads (which attests
  before the renderer runs). This is §3.3's "convention compliance" row and
  §3.0's worked example: the bridge recovers a distinction the projection would
  otherwise collapse (the Dau render shows a plain ambiguous X; Peirce shows
  the hop). Verified visually on `(R *x *y) (S y x)` (SVG→PNG and a
  pdflatex-compiled TikZ).
- Tests: `tests/test_styles.py` (+5 — TikZ curve mirrors SVG on a multi-point
  line; deterministic TikZ hand; `ligature_crossings` finds only distinct-line
  crossings; bridges drawn + scoped to the convention; stroke-only + still
  attests). Known limitation (V1): the hop's gap is erased with white, so a
  crossing *inside* an odd-polarity (gray-tinted) cut shows a faint white nick;
  most distinct-line crossings sit on the open sheet.

**Still ahead on this arc:**
- **Stage 3 — authentic Peirce in TikZ (NOT egpeirce/PSTricks)**: the repo
  already chose TikZ/pgf over PSTricks
  (`docs/FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md`, `STYLE_NOTES_PEIRCE.md`),
  and today's `tikz_export.py` is PSTricks-free + LyX-native. `egpeirce.sty`
  has two author-stated limitations — PSTricks, and no connection to the
  underlying logic — and we are past **both** (we emit TikZ; everything is
  EGI/NaturalLayout-derived and §3.3-attested). So Stage 3 keeps
  `egpeirce.sty` as a *visual reference only* and deepens the **TikZ** Peirce
  output to reproduce Peirce's conventions: oval cuts, hand-drawn quality,
  and the **bridge-at-crossing** mark (`Conventions.ligature_crossing_marks
  = "bridges"`). egpeirce used PSTricks *relative* placement because it had
  no layout engine; we own the layout, so absolute-coordinate TikZ is
  simpler and more faithful — Peirce's hand, not his typesetter. Optional
  `pdflatex` compile to PDF. Refs: `egpeirce.sty.txt`,
  `Egpeirce Documentation.pdf` in `docs/references/`.
- **Stage 5 — drawing-first editor** (separate, larger arc): a structured
  drawing surface where placing cuts/spots/lines builds a live EGI rendered
  in a chosen style — the honest "copy a Peirce drawing → EGI". (Image→EGI
  recognition is out of scope; the Import doorway is today's bridge.)

3. **Optional/parallel:** "adopt this import as M / send to Agon as G"
   (the warrant-raising acts that close the Import↔Agon loop); browser
   walkthrough of on-canvas selection (still unverified by a real
   browser); semantic-evaluation layer; per-disposition integrations;
   a first-class warrant gradient; pin sibling-cut ordering convention.

---

## Done: on-canvas element selection

**Why it came first (not Agon, not polish).** The promotion boundary is *correct*
but *unexercised by real reasoning*: rule parameters are currently typed
element-ids (UUIDs), so you can't comfortably build a multi-step proof.
Until someone composes a non-trivial chain and promotes it, we don't know
whether the chain model holds up in use (do the regimes feel right? is
"promote = fork" the right default? does linear-only bite?). That
empirical test — "ongoing reference to and testing of our models" — is
cheap to enable, because the SVG renderer already emits
`data-element-id` / `data-element-type` on every vertex, predicate, and
cut, with `cursor: pointer` and transparent hit areas. So this is pure
frontend work; no renderer change.

**Scope (V1):**
- Click an element → toggle it in the subgraph selection; highlight it;
  sync into the rule's `selected_elements` field.
- Shift-click a cut → mark it as the `target_area` (for INS / IT+);
  distinct highlight; sync into the `target_area` field.
- Text fields remain authoritative and editable (graceful degradation;
  the route API and its tests are untouched).
- Clear selection on successful apply (element ids change).

**Out of scope (follow-ups):** drag-to-pan vs click disambiguation
refinement; regime-3 drag-to-reposition / reshape affordances; multi-step
stepwise interaction split across endpoints; undo / branching in the
workshop.

---

## After this

0. **✅ Per-rule sub-graph selection review DONE (2026-06-04).** Reviewed
   how the Ergasterion UI lets a user select the proper sub-graph (incl. an
   *empty space*) for each rule, against the logic and the actual engine. The
   reviewed design lives in
   [docs/TRANSFORMATION_WORKFLOW_SPEC.md](docs/TRANSFORMATION_WORKFLOW_SPEC.md).
   Outcome (confirmed with the author):
   - **A unified grammar — four beats, two families.** Every rule application
     is **① Spot → ② Subject → ③ Commit → ④ Settle**. The six rules split into
     **Placing** (DC+, INS, IT+ — pick a spot + fill a *buffer* by
     authoring/copying, then a ghost-preview) and **Removing** (ERA, DC−, IT−
     — select a closed sub-graph, spot *implied*, with a *justification
     highlight* of why the move is legal). One skeleton, two visual dialects =
     consistent between rules and within each.
   - **Settle is a keystone, not polish.** The author's central point: a
     transform must preserve the **visual family resemblance** between
     before/after (Peirce's "moving pictures of thought" leans on human
     pattern-recognition). v1 principle = **layout conservatism** (change the
     drawing as little as the new logic allows; the addition/removal stays
     locally legible). Two parts: **④a automatic continuity** (engine) +
     **④b manual touch-up** (regime-3 on canvas).
   - **The one logic-expressiveness gap:** DC+ equates *no selection* with
     *enclose the whole area*, so a **truly empty** double cut is only possible
     in an already-empty area. "A double negative at any spot, even around
     nothing" needs an explicit-empty selection honored by the engine
     (protected change).
   - **The one concrete engine no-op found:** `ELKLayoutEngine.generate_layout`
     accepts `layout_deltas` but **never uses it** — `layout_service`'s
     advertised anchoring is dead, so every transform re-lays-out cold. This is
     the natural hook for ④a conservatism.

   **Build order (keystone-first), from the spec §5:**
   1. **Automatic continuity (④a)** — *revised 2026-06-04 after experiment:
      the ELK-interactive option-flip **regresses** and was reverted (spec §3a).*
      ELK is deterministic, so staged instead:
      - **(1a) stable viewport — ✅ DONE + browser-verified (2026-06-04).** A
        continuation render (rule applied / style changed / Agon move) now
        carries the prior camera across the re-render instead of re-fitting:
        absolute scale (`getZoom × realZoom`) + pan restored, so a surviving
        element keeps its size and screen position and the eye tracks what
        changed; a fresh open still fits/centers. `web_viewer/ergasterion.html`
        + `agon.html` `renderSvg(svg, preserveView)`. Verified via system
        Chrome: across a DC+ apply the viewport transform is preserved exactly
        (Δscale 0.0000, Δpan 0) while a fresh open re-fits.
      - **(1b) animated transition — ✅ DONE + browser-verified (2026-06-04).**
        `web_viewer/js/diagram-transition.js` (shared FLIP helper, loaded by
        ergasterion + agon): captures element screen positions before the SVG
        is replaced, then — with the camera held by 1a — animates each
        surviving element (matched by `data-element-id`) from its old position
        to the new and fades in genuinely new ones, so motion keeps the picture
        followable (the literal "moving picture"). Client-only, §3.3-neutral;
        degrades to an instant cut without the Web Animations API. Verified via
        Chrome: a DC+ apply (3→5 elements) drove 5 concurrent animations (3
        survivors sliding + 2 new cuts fading in), settling to 0 residual
        transforms / 0 running, no page errors.
      - **(1c) pin-and-place — subtractive case DONE (2026-06-04).** Measured
        first: with structural ordering in place, survivors still drift 50–235px
        per step (global ELK re-balances as the graph changes), and rigid
        re-anchoring (translate / similarity) is insufficient (step 3 stays
        232px; similarity overfits to a degenerate flip on few points). So true
        pinning is required. Split by what the step does:
        **subtractive (ERA / IT− / DC−)** — the new element set is a *subset* of
        the old, so survivors keep their **exact** previous positions and removed
        elements vanish (zero new material to place). `layout_service.
        _subtractive_layout` detects this structurally (no rule coupling) and
        reuses the previous DTO's positions/bounds, §3.3-attested with a full
        layout fallback. Verified: beta_modus_ponens DC− and Praeclarum steps 6
        (IT−) & 7 (DC−) now move **0px** (were 51 / 79). Tests:
        `test_layout_service_attestation.py` (+2).
        **Additive — DC+ wrap DONE (2026-06-05).** DC+ adds only *cuts* (no new
        vertices/predicates) and wraps survivors, so
        `layout_service._additive_cut_layout` keeps every element at its exact
        position and recomputes cut bounds bottom-up around them (ancestors grow
        just enough); §3.3-attested, full-layout fallback if a recomputed wrap
        overlaps a sibling. Verified 0px survivor drift on plain / Beta (line of
        identity) / multi-sibling / enclose-all DC+. Tests +1.
        **INS and IT+** still fall back — they add new vertices/predicates that
        need frame-consistent, overlap-aware *placement* of genuinely new
        geometry (the harder remaining increment; the agreed pause point).

      **Diachronic chain player — ✅ DONE + browser-verified (2026-06-04).**
      To actually *watch* 1a/1b on a real proof there has to be a way to play a
      chain; there wasn't. Added `GET /organon/uods/{id}/chain` (loads the
      persisted `TransformationChain`, renders base + one frame per step to
      SVG + linear form, each §3.3-attested) and a player in `organon.html`
      (« ‹ ▶ › » + step counter + the rule's Peirce-label/note; `has_chain:false`
      hides it for synchronic UoDs).

      **View convention — fit-to-content, not hold-camera.** A first cut reused
      the workshop's 1a *hold-camera*, which was wrong for the player: a proof's
      states vary widely in size (blank → full → smaller), so a base-fit that
      was zoomed-in stayed zoomed-in and the graph overflowed; reversing didn't
      re-fit. Corrected to the **fit-to-content + animated camera dolly**
      convention (the standard for guided playback of differently-sized states,
      e.g. yEd / reveal.js): each frame is fitted so the whole (sub-)graph stays
      in scope, and the camera *dollies* (zoom + pan, eased) from the previous
      frame's view to the new fit rather than snapping. Verified across
      Praeclarum 0→7: every frame fits, zoom adapts (3.3→0.5→0.59 as it grows
      then shrinks), and stepping back is exactly reversible. The two
      conventions are now explicit: **workshop = hold-camera (1a, small local
      edits); player = fit-to-content (states change size).**
      Verified via Chrome on `theorem_praeclarum` (8 frames, all 7 rules in
      order, anim peaks 2→19) and `beta_modus_ponens` (autoplay). Tests:
      `tests/test_organon_routes.py` (+3).

      **Drawing chrome (2026-06-05):** removed the per-drawing "Existential
      Graph" title and the `V/P/C/L` stats line from the SVG renderer (redundant
      chrome; counts live in the page UI). The Organon header `shape: V/E/C` now
      updates **per frame** as you step (was stuck on the final state).

      **View-style selector in Organon (2026-06-05):** style is a *projection*
      choice, so viewing a form in Dau / Peirce / Sowa is now a basic option in
      the viewer (a toolbar `<select>`), not only on the Export path. `GET
      /organon/uods/{id}` and `…/chain` take an optional `?style=`; the page
      re-renders the current detail or chain frame in the chosen style
      (frame-preserving), with a "Rendering in <style>… (N frames)" status since
      a whole-chain Peirce render (oval refit + hand-drawn) takes a few seconds.
      §3.3 attests every styled render. Tests: `test_organon_routes.py` (+2).

      **Three bugs fixed while playing it through:**
      - **Empty cuts were invisible.** ELK collapses a childless compound node
        to a zero-size point, so an empty cut (`~[ ]`, and the *inner* cut of an
        empty double cut `~[ ~[ ] ]`) rendered as nothing — step 1 showed one
        shape though the EGI had 2 cuts. `ELKLayoutEngine.EMPTY_CUT_MIN_SIZE`
        (32) now floors childless cuts; §3.3 still attests (inner stays
        contained). Verified: step 1 shows both nested cuts.
      - **An IT+ copy rendered flipped vs its source.** `egi.area` is a
        frozenset, so ELK got children in id-dependent order; a copy (different
        ids) stacked its elements oppositely (step 3: source P-above-R, copy
        R-above-P). The engine now orders area children by an id-independent
        `_structural_key` (edges, then cuts recursively, then vertices), so
        isomorphic subgraphs lay out identically — the copy mirrors its source
        (TRANSFORMATION_WORKFLOW_SPEC §2 IT+ "echo the original's shape"). Also
        makes layout reproducible across runs. Verified: both scrolls now
        P-above-R.
      - **Stale "Unified D3" subtitle** (the archived Qt engine name) → now a
        plain `0V, 6P, 8C, 0L` element count.

      Tests: `tests/test_elk_layout_engine.py` (+4 — empty cut visible, empty
      double cut nests, isomorphic structural keys, id-independent layout). Full
      layout/correspondence/proof suite green (416 passed).
      §3.3-neutral. Includes **ligature continuity** (hold a line of identity's
      surviving geometry fixed).
   2. **Spot/Subject grammar + closure preview** — first-class region select
      (incl. the **sheet**), `/rules`-driven prompts, restored closure preview,
      the two visual dialects (ghost-preview vs justification-highlight). Mostly
      unprotected UI + additive routes.
   3. ✅ **Manual Settle (④b) DONE (2026-06-06)** — `move_vertex`/`reshape_cut`/
      `reroute_ligature` wired onto the canvas (`settle-adjust.js` +
      `/ergasterion/.../adjust`), boundary crossings refused, browser-verified.
   4. ✅ **DC+ empty-double-cut semantics DONE (2026-06-06)** — `enclose_empty`
      on `TransformationContext` + an optional Spot step on `DCPlusInteraction`
      (`formal_transformation_rules.py` / `rule_interaction.py`, protected).

   **Validated against the seeded exemplars** (spec §6): the grammar was
   walked step-by-step over the real `theorem_praeclarum` (7 steps) and
   `beta_modus_ponens` (2 steps) chains. Every step is unambiguously
   Placing or Removing and the Spot/Subject/justification slots fill
   correctly. Refinements: DC+ empty case works only on empty areas
   (confirmed at Praeclarum step 1, the blank sheet); **ligature continuity**
   added as a continuity requirement (Beta steps both act on the shared line
   x). See memory [[project-ui-subgraph-selection-review]] and
   [[project-transformation-workflow-grammar]].

1. **Dogfood by ingesting known proofs → the first diachronic exemplars.**
   The UoD is *fundamentally diachronic* (an evolving reasoning process),
   but today's tomos is almost all synchronic snapshots — only `practice_*`
   UoDs carry a `history/`. Seed the corpus with **canonical worked proofs**
   built as real `TransformationChain`s and persisted via
   `save_uod_with_chain`. First target: **Leibniz's Praeclarum Theorema**,
   `((p⊃r) ∧ (q⊃s)) ⊃ ((p∧q) ⊃ (r∧s))` — Sowa's showcase EG proof
   (`docs/references/Peirce_Rules_of_Inference.pdf`): **7 steps from a blank
   sheet** (vs. Principia's 43 steps from 5 axiom schemata). Pure Alpha, so
   every step maps onto an existing Dau rule — Peirce's three pairs are our
   six: insertion-in-negative → **INS**, erasure-in-positive → **ERA**,
   iteration/deiteration → **IT+ / IT−**, double-cut in/out → **DC+ / DC−**.
   This is the dogfood the plan always wanted, now with a concrete,
   motivating, *famous* target — and it doubles as the diachronic seed the
   Organon timeline and the Agon record both need.
   - **✅ Praeclarum DONE (2026-06-03).** `tools/build_praeclarum_chain.py`
     builds the 7-step proof through the headless `RuleInteraction` protocol
     (every step a *real* rule application, not a hand-authored state) and
     seeds it into the corpus as `theorem_praeclarum` (category
     `THEOREM_PROOF`, historical) via `save_uod_with_chain`. Sequence
     **DC+, INS, IT+, INS, IT+, IT−, DC−** (Peirce 3i,1i,2i,1i,2i,2e,3e),
     conclusion `~[ (P⊃R) (Q⊃S) ~[ ~[ (P)(Q) ~[(R)(S)] ] ] ]`.
     `tests/test_praeclarum_proof.py` (+6) pins shape, conclusion (order-
     insensitive structural signature), **per-step soundness** (each step
     replays from its own `from_state` snapshot), §3.3 at every non-blank
     state, and corpus round-trip. The engine accepted all seven sound moves
     without complaint — the logic core is solid.
   - **Dogfood findings** (update memory `project-ergasterion-dogfood-findings`):
     (a) propositional atoms must be **capitalised** (`(P)`, not `(p)` —
     lowercase is reserved for vertex labels), so the diagram's lowercase
     p/q/r/s can't round-trip verbatim into linear form; (b) confirmed the big
     one — **rule parameters are ephemeral element-ids**, so authoring needed
     bespoke *structural* navigation (`_cut_with_edge` "the cut directly
     containing edge P", etc.) to locate each selection. There is no
     content-addressable / structural selection API; the helpers I wrote want
     a shared home before the next proof. (c) `IT+` source wants the single
     top element of one area (closure expands internally); passing the full
     closed set trips a confusing "All source elements must be in the same
     area". Net: the **logic** is solid; the **authoring ergonomics** (linear
     naming + id-typed selections) are the gap.
   - **✅ Authoring layer DONE (2026-06-03).** The dogfood findings drove a
     reusable layer in `src`, so a proof no longer means hand-navigating ids:
     - `src/eg_navigation.py` — **content-addressable structural selection**:
       name an element by *what it is and where it sits* (`cut_holding_relation`,
       `empty_cut_in`, `child_edges`, `edges_on_vertex`, `vertex_by_label`),
       `area_signature` (Alpha) + `same_graph` (full iso, the Beta authority),
       and `describe` (kind/area/polarity/depth — the introspection finding #1
       wanted, also for a future HTTP selection API). Area topology delegates to
       `presentation_ops`, not redefined.
     - `src/proof_authoring.py` — **`ProofChain`**: a fluent builder that
       applies rules by locator (`callable(egi)→id`, resolved against the
       current state) and records each `ChainStep` with deterministic ids and
       timestamps. `apply_rule` / `replay_step` are the shared engine/replay
       primitives. `tools/build_praeclarum_chain.py` was refactored onto it
       (same chain, test still green) — the abstraction validated on a known
       proof before reuse.
   - **✅ Beta modus ponens DONE (2026-06-03).** `tools/build_beta_modus_ponens_chain.py`
     seeds `beta_modus_ponens` — the corpus's first proof with a **line of
     identity**: `P(x), P(x)→Q(x) ⊢ P(x)∧Q(x)`, two steps (IT-, DC-) anchored
     at the *premises* (not the blank sheet), so the two exemplars together show
     both episode shapes — theorem-from-⊤ and inference-from-a-context.
     `tests/test_beta_modus_ponens_proof.py` (+6) uses `same_graph` (the W-
     partition needs full iso, not a signature) for conclusion + per-step
     soundness, and §3.3 attests at every state (ligatures crossing cuts
     included). Visually confirmed in Peirce style (the shared line crosses the
     wobbled ovals; one line, so no bridge — correctly).
   - **✅ HTTP introspection DONE (2026-06-03).** The content layer is now
     served, fully closing dogfood finding #1 (select-by-meaning over HTTP):
     `egi_introspection` (already carrying area/polarity, wired into the
     Ergasterion + Agon session payloads) now also exposes each edge's
     `relation` / `arity` / `incident_vertices` (ν order) and each vertex's
     `label`, drawn from `eg_navigation`. A standalone read-only **`POST
     /introspect`** (egif or `uod_id`; mode-independent like `/rules`) makes it
     reachable for any graph without a session — so a client can resolve "the
     cut holding P" or detect "the two lines that cross" (shared vertices in
     swapped ν order) entirely from structure. `tests/test_introspection_and_rules.py`
     (+5). (Finding #2, rule-requirement discovery, was already `GET /rules`.)
   - **✅ Crossing-lines exemplar DONE (2026-06-03).** `tools/build_beta_converse_chain.py`
     seeds `beta_converse_mp` — converse modus ponens
     `R(x,y), ∀(R(x,y)→S(y,x)) ⊢ R(x,y)∧S(y,x)` (two steps IT-, DC-). The
     argument swap makes the two lines **cross**, so it is the first corpus
     proof whose Peirce drawing draws the **Tier-3c bridge** (§3.0's worked
     example). `tests/test_beta_converse_proof.py` (+6) asserts the conclusion
     has ≥1 ligature crossing and that Peirce emits `<g id="bridges">` while Dau
     does not; visually confirmed (the over-line hops the under-line at the
     crossing).
   - **✅ Click-to-select UI DONE + browser-verified (2026-06-03).** The
     Ergasterion canvas now *consumes* the introspection: clicking an element
     names it as a chip by **meaning** — relation/label + a recto/verso polarity
     dot (raw id only in the chip's tooltip) — instead of echoing a UUID, and a
     non-blocking **polarity hint** forewarns the common mistakes (INS/IT+ into a
     positive area, ERA from a negative one) using the same introspection. The
     long-standing "unverified in a real browser" flag is **closed**: drove
     system Chrome via Playwright through open-session → click predicate (chip
     "Q") → shift-click cut (chip "cut · depth 1") → INS ("target area is
     negative ✓"). `tests/test_introspection_and_rules.py` (+1) pins the payload
     contract the UI binds to. Text fields stay authoritative (graceful
     degradation; the engine is the final arbiter).
   - **Still open:** the `IT+` "All source elements must be in the same area"
     message is still confusing for a caller passing a full closed set (cosmetic
     engine-message fix). More/longer derivations remain cheap now that the
     authoring layer + introspection + click-to-select all exist.
2. **Agon web arena** — *deferred behind item 0* (the user's call: review
   per-rule sub-graph selection first). Informed by a *lived* promotion
   boundary, not a merely correct one. The fuller notion of regime-2 "asserted"
   (earned by withstanding challenge, not only by §3.3 attestation) is the
   design target — see [docs/CHAIN_OF_SEMIOSIS.md](docs/CHAIN_OF_SEMIOSIS.md),
   "Semiosis is dialogical." The ingested proofs give Agon real records to
   challenge.

---

## Notes on workflow

Primary development is local, on `main`; GitHub is backup, not a
collaboration surface. No PR ceremony (single developer, single site):
commit to `main`, push to back up. Feature branches are optional backup
points, fast-forwarded into `main` rather than merged via PR.
