# Current Plan

**Last Updated**: 2026-06-01

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
| **Agon** (Endoporeutic Game arena) | ⬜ engine + REPL exist; web arena not started |
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

## Active task: on-canvas element selection

**Why now (not Agon, not polish).** The promotion boundary is *correct*
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
