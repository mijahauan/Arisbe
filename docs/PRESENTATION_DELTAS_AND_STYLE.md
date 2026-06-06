# Presentation deltas & style — persisting the regime-3 free dimension

**Status:** design + foundation + increments 2/2b/3/4-scale-1 shipped
(2026-06-06). Done: a typed, tagged delta vocabulary (`presentation_deltas.py`),
replay-via-`presentation_ops`, recording in the Settle ④b adjust route,
consumption in `layout_service.generate_layout`, scratch + corpus persistence,
chain inheritance (scale 2, by id), and **within-view extrapolation (scale 1):
generalize sparse `move_vertex` exemplars to untouched structural siblings**.
Cross-step extrapolation to new elements, scoped rendering, and crystallization
tooling remain as follow-on increments.

Read alongside [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
§4.3 / §5.5 (regime 3) and [TRANSFORMATION_WORKFLOW_SPEC.md](TRANSFORMATION_WORKFLOW_SPEC.md)
(Manual Settle ④b).

---

## 1. The problem

We let a user edit the *drawn* form of an EGI in ways that are **indifferent to
the logic** — `move_vertex` / `reshape_cut` / `reroute_ligature`, the regime-3
algebra (`presentation_ops`). Today those edits live only in the session's
in-memory `current_layout_dto`; close the session and the nudge is gone. We need
a coherent way to **save the deltas with an EGI** so that:

- **(a)** a consistent style + deltas hold throughout a UoD (a *diachronic*,
  possibly large, evolving reasoning process — not one static diagram);
- **(b)** we can *study* the deltas' effects (what people actually nudge, and how);
- **(c)** we can *develop new stable basic styles* the way we already have Dau,
  Peirce-handwritten, and Sowa.

## 2. The model: a specificity ladder, all regime-3

Three tiers of projection-side data, increasingly specific. All three are
"indifferent to the logic"; they differ in *scope* and *reuse*.

| Tier | What it is | Scope | Home in code |
|---|---|---|---|
| **Convention** | what *can* vary — the grammar of the projection step | universal | `projection_conventions.Conventions` (already splits *honored* vs *descriptive, not-yet-a-knob*) |
| **Style** | a *named, shared* setting of conventions — a stable basic dialect | every graph, any view | `styles/*.json`, `style_loader` |
| **Deltas** | per-state, per-element *human overrides* on a (style + base layout) | one state of one UoD | `presentation_deltas.PresentationDelta` (this work) |

The three goals are the three things this ladder is *for*, one per tier:

- **(a)** persist a **preferred style** + a **delta stream** with the UoD, and
  carry deltas forward along the chain → consistency through the episode.
- **(b)** deltas are **structured, tagged, replayable acts** (not pixels) → a
  queryable dataset.
- **(c)** the lifecycle **delta → convention → style**: a delta pattern that
  recurs and proves stable graduates into a named convention/style. Deltas are
  the *raw material* of styles; the `projection_conventions` *descriptive →
  honored* split is literally the graduation ladder.

## 3. The crux: deltas are **sparse, tagged exemplars** — and we *extrapolate*

A UoD can be **large**. We do **not** draw the whole thing, and we do **not**
store a position for every element. Instead:

- **Style applies universally** — on any viewing, at any scope, to elements that
  have no explicit delta. The default needs no per-element data.
- **Deltas are sparse** — the user nudges a *few* things where the automatic
  layout doesn't read well.
- **We extrapolate** from those few exemplars to everything else. A delta is
  therefore not a one-off pixel fact; it is a **sample of an intent**, and must
  carry the *structural description of its target* — kind / area / polarity /
  depth / relation / label, from `eg_navigation.describe`. That tag is the
  handle for generalization.

**Extrapolation is one operation at three scales — and the third scale is goal (c):**

1. **Within a view** — generalize a delta to untouched elements of the same
   structural description in scope (e.g. "vertices in odd-polarity cuts sit a
   little lower"; "sibling cuts get this much breathing room").
2. **Within the UoD (diachronic)** — survivors keep their element ids across a
   transformation step (the same fact the Settle ④a pin-and-place relies on), so
   a delta inherits forward by id; the *generalized* intent additionally covers
   the **new** elements a step introduces, which never had an explicit delta.
3. **Across the corpus** — when an extrapolated regularity is stable across many
   graphs, **name it**: promote a `projection_conventions` descriptive field to
   honored, and ship a style JSON that sets it. A new basic style **is** a
   crystallized delta pattern.

So extrapolation is not a side feature — it is the crystallization mechanism
that turns hand-deltas into styles. Capturing deltas as *tagged acts* is what
makes all three scales reachable; a DTO snapshot (baked pixels) could not.

## 4. The render equation

A drawing is a **scoped projection** of the EGI, not a whole-graph dump:

```
drawing(scope) = render(
    base   = ELK(EGI | scope, style)              # universal style, any subset
    ⊕ replay(applicable deltas over base)         # sparse human overrides, by id
    ⊕ extrapolate(tagged deltas → untouched in-scope elements)   # [follow-on]
)
attested by §3.3 at the service boundary
```

- **Replay** folds each delta through `presentation_ops` — the op preserves §3.3
  by construction; a delta that no longer applies (target absent, or the op now
  crosses a boundary) is **dropped**, not failed, exactly like the ④a
  incremental builders fall back rather than error.
- **Style binding:** deltas are authored against the UoD's preferred style.
  Translations (`move_vertex dx,dy`) are largely style-robust; absolute
  `reshape_cut` bounds are geometry-specific (Dau rectangle vs Peirce's
  √2-grown oval) and may not attest under a different style — those drop on
  reprojection. A per-style delta map is the upgrade if best-effort proves
  insufficient.

## 5. Persistence shape (follow-on)

- Reuse the **existing** `UniverseOfDiscourse.current_layout_deltas` slot
  (already on the model, already round-tripped as `current.deltas.json`,
  currently vestigial) rather than adding a protected field — repurpose the
  dead field into the live one, extended to **per-state** keying.
- A state's stored deltas are the *acts authored at that state*. Its **effective**
  deltas = parent's surviving-id deltas (filtered to ids still present) ⊕
  authored-here ⊕ extrapolated. This is the same shape as ④a continuity, seeded
  from disk instead of the live prior DTO.
- A UoD carries a **preferred style** (one name); a viewer may still reproject
  transiently (Organon's style selector) without mutating the stored preference.

## 6. Build order

1. **✅ Foundation (this work).**
   - `presentation_deltas.py` — `PresentationDelta` (op + params + target tags),
     `record_delta` (tags via `eg_navigation.describe`), `apply_deltas`
     (best-effort replay through `presentation_ops`, §3.3-attested per delta,
     drops what doesn't apply), `to_dict`/`from_dict`.
   - `layout_service.generate_layout(…, deltas=…)` consumes deltas via
     `apply_deltas` — finally making the dead `layout_deltas` parameter live (at
     the service layer, the right home: the engine stays projection-mechanism).
   - Settle ④b adjust route **records** a tagged delta into the session; the
     `GET /sessions/{id}` re-render (and `?style=` reprojection) **replays** the
     current state's recorded deltas over a fresh base, so a nudge survives a
     full re-layout. `_session_payload` surfaces them.
2. **Persistence** — write per-state deltas + preferred style to disk.
   - **✅ Scratch path (regime-1) done.** `ScratchStore` writes a per-state
     `deltas.json` (`{state_id: [delta-dict]}`) beside the chain, and
     `style_name` (the draft's preferred projection) is already in `meta.json`.
     `save-to-scratch` serializes `session.presentation_deltas` (restricted to
     the active line's states); `open_scratch` rehydrates them and replays the
     tip's over its base, so a reopened draft *looks* the way it was saved.
     `create_session` carries deltas in; navigation
     (`GET …/states/{state_id}`) replays each state's own deltas.
   - **✅ Corpus path (regime-2) done (2b).** `save_uod_with_chain(uod, chain,
     presentation_deltas=…)` writes a parallel `history/deltas.json` (pruned of
     empties; cleared on an overwriting save); §3.3 still fires inside `save_uod`
     *before* any history write, so a refusal leaves no `deltas.json` either.
     `load_chain_deltas(uod_id)` reads it (empty dict if absent; `load_chain`'s
     signature unchanged). The workshop's "open a corpus UoD that carries a
     sequence" path hydrates them and replays the tip's effective deltas. Note:
     no workshop→corpus *writer* carries deltas yet (the promote route was
     retired; Agon assertion doesn't track board deltas) — the corpus read/write
     mechanism is ready for when such a writer exists (e.g. Agon-side deltas).
3. **✅ Chain inheritance done.** `presentation_deltas.merge_inherited` resolves
   a state's *effective* deltas = the authored deltas along its ancestry
   (`ergasterion_session_manager.state_ancestry`), where a descendant re-authoring
   an element (`delta_key`) **replaces** the ancestor's for that key (re-nudging
   supersedes, doesn't stack) and same-key drags within the winning state stay
   ordered (cumulative). Wired into the cold-render paths (`GET /sessions/{id}`,
   `GET …/states/{id}`, `open_scratch` tip) via `manager.effective_deltas`; an
   inherited delta whose survivor was removed/re-boxed is dropped at replay by
   `apply_deltas` (the regime boundary holds). The **apply** path keeps using
   `previous_layout` pinning — which already carries the nudge forward — so
   inheritance is *not* layered on top of it (that would double the offset). This
   is extrapolation **scale 2** (within-UoD, by element id).
4. **Extrapolation — ✅ scale 1 (within-view) done.**
   `presentation_deltas.generalization_key(target, fields)` derives a *coarse*
   structural key from a delta's `describe` tags (default `kind` +
   `area_polarity` — Peirce's odd/even nesting, the example §3 names), distinct
   from `delta_key`'s element *identity*. `extrapolate_deltas(egi, deltas, *,
   key_fields=…)` generalizes the sparse **`move_vertex`** exemplars (a move is
   a transferable *translation*; absolute `reshape_cut` bounds and per-line
   `reroute_ligature` paths are **not** extrapolated — they'd need a relative
   encoding first): it groups exemplars by key, takes each group's **mean**
   translation (one exemplar → itself; several → their average — the raw signal
   a future "study" layer reads), and synthesizes a tagged `move_vertex` delta
   for every in-scope vertex that matches a group's key **and has no explicit
   delta of its own** (the explicit element is never overridden). It returns
   only the synthetic deltas (a disjoint element-set from the explicit ones),
   replayed through the same best-effort §3.3-attested `apply_deltas` — an
   extrapolation that doesn't fit is dropped, not forced.
   `layout_service.generate_layout(…, extrapolate=False)` consumes them
   (opt-in, default off → no change to existing renders); reachable via the
   workshop's `GET /sessions/{id}?extrapolate=true` — a research *view* that
   never mutates the stored deltas. Tests: `test_presentation_deltas.py` (+5)
   and `test_ergasterion_routes.py` (+1). No protected module touched.

   **Scale 1→2 bridge — ✅ done (by composition).** Because `extrapolate_deltas`
   iterates the **current state's** EGI (not the deltas' origin graph), a vertex
   that exists at this state but carries no explicit/inherited delta — e.g. one
   a transformation step just *introduced* — picks up the generalized intent of
   its structural class, while the nudged survivor (still present by id) is
   excluded. So `effective_deltas` (inherited-by-id, scale 2) ⊕ extrapolation
   (over the current EGI, scale 1) covers new elements without extra wiring.
   Reachable on both cold-render routes: `GET /sessions/{id}?extrapolate=true`
   **and** `GET /sessions/{id}/states/{state_id}?extrapolate=true` (the
   move-by-move navigator). Tests: `test_presentation_deltas.py`
   (+1 — new-element coverage) and `test_ergasterion_routes.py` (+1 — the
   states route honors the flag).
   **Remaining:** a relative encoding so `reshape_cut` / `reroute_ligature`
   extrapolate too (currently move-only); variance/agreement gating as the
   study (b) signal; finer/learned key fields beyond kind + polarity.
5. **Scoped rendering** — lay out and draw a *sub-scope* of a large UoD; style +
   deltas are already scope-independent by construction, so this is additive.
6. **Crystallization tooling** — surface the delta dataset (b); a path from a
   stable delta pattern to a new `projection_conventions` knob + style JSON (c).
