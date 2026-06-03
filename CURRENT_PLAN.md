# Current Plan

**Last Updated**: 2026-06-03 (Peirce fidelity Tier 3b/3c — TikZ parity + bridge marks)

Living scratchpad for where development stands and what's next. The
durable vision lives in [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md);
this file tracks the active front. The pre-commit quality gate reads the
**Last Updated** date here, so keep it current.

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
| **Organon** (archive, read-only) | ✅ live — `/organon` |
| **Ergasterion** (workshop, composition) | ✅ live — `/ergasterion` |
| Chain persistence (regime-1 → regime-2 boundary) | ✅ `tomos_service.save_uod_with_chain` / `load_chain` |
| **Agon** (Endoporeutic Game arena) | 🟢 V1 live — `/agon` (thin, flexible slice) |
| On-canvas element selection for rule application | 🟡 **in progress** |
| Transformation UI w/ regime-3 (drag/reshape) affordances | ⬜ not started |

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
   - **Still open:** the `IT+` "All source elements must be in the same area"
     message is still confusing for a caller passing a full closed set (cosmetic
     engine-message fix). The introspection content is served but no web UI yet
     *consumes* it for click-to-select (the on-canvas selection arc). More/longer
     derivations remain cheap now that the authoring layer + introspection
     exist.
2. **Agon web arena** — informed by a *lived* promotion boundary, not a
   merely correct one. The fuller notion of regime-2 "asserted" (earned by
   withstanding challenge, not only by §3.3 attestation) is the design
   target — see [docs/CHAIN_OF_SEMIOSIS.md](docs/CHAIN_OF_SEMIOSIS.md),
   "Semiosis is dialogical." The ingested proofs give Agon real records to
   challenge.

---

## Notes on workflow

Primary development is local, on `main`; GitHub is backup, not a
collaboration surface. No PR ceremony (single developer, single site):
commit to `main`, push to back up. Feature branches are optional backup
points, fast-forwarded into `main` rather than merged via PR.
