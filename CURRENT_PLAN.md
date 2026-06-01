# Current Plan

**Last Updated**: 2026-06-01 (Agon arena V1: thin, flexible slice)

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

3. **Optional/parallel:** browser walkthrough of on-canvas selection
   (Ergasterion + Agon share the `data-element-id` approach, still
   unverified by a real browser); semantic-evaluation layer; per-
   disposition integrations; pre-promote §3.3 preview; pin sibling-cut
   ordering convention.

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

1. **Dogfood** — compose and promote a real multi-step proof (e.g. a
   propositional tautology or a Beta modus ponens) through the workshop;
   record what the chain model gets right and where it chafes.
2. **Agon web arena** — informed by a *lived* promotion boundary, not a
   merely correct one. The fuller notion of regime-2 "asserted" (earned by
   withstanding challenge, not only by §3.3 attestation) is the design
   target — see [docs/CHAIN_OF_SEMIOSIS.md](docs/CHAIN_OF_SEMIOSIS.md),
   "Semiosis is dialogical."

---

## Notes on workflow

Primary development is local, on `main`; GitHub is backup, not a
collaboration surface. No PR ceremony (single developer, single site):
commit to `main`, push to back up. Feature branches are optional backup
points, fast-forwarded into `main` rather than merged via PR.
