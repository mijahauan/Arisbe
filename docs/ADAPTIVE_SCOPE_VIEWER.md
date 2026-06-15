# Adaptive-Scope Viewer: Overview + Expand, and the Navigation-Projection Attestation

**Status:** Design of record (2026-06-14). Written *before* the build, as the
`▶ NEXT SESSION` task requires — this is the one piece of the adaptive-scope work
that touches the correspondence story *conceptually*, so it earns a design doc, not
just code.

**Prior art in this repo (read first):**
- `docs/ADAPTIVE_SCOPE_SPIKE.md` — the decide-by-prototype spike. The lenses
  (2.5-D negation well + storyboard) shipped 2026-06-14 over the coordinate-free
  structure substrate. This doc is the spike's deferred **core**.
- `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` — §3.3 ("What 'faithful map' requires"),
  §4 (the three regimes), §6 (boundary events). The contract `attest_overview`
  extends.
- `docs/MANIFEST_AND_MEANING.md` — "The membrane, and what a mark may bear" (§48–80)
  and the practical floor (#3 *attest correspondence, never truth*; #6 *no mark bears
  actuality*). The philosophical floor the placeholder obeys.
- `src/eg_structure.py` — `egi_structure` + `subtree_summary`, the O(n) coordinate-free
  facts a placeholder is built from.
- `src/correspondence_attestation.py` — `check_correspondence` / `attest_correspondence`,
  the full §3.3 check `attest_overview` reuses and weakens honestly.

---

## 1. The problem: structure is O(n), the styled *drawing* is not

Arisbe's logic is essentially complete. The remaining gap is the **experience of the
pictures**, walled off by the **layout-perf frontier**: ELK is super-linear in the breadth
of sibling scrolls and the lines of identity routed among them, so the full 246-cut SUMO
taxonomy takes **≈289 s** to lay out (measured 2026-06-15, `tools/overview_frontier_benchmark.py`;
`docs/CORPUS_AND_IMPORT_MODEL.md` cites ≈74 s on a faster host), and a 130-cut relational
theory chokes the §3.3 save boundary. The coordinate-free *structure* of such a graph is already O(n) —
`eg_structure.egi_structure` returns the 86-cut SUMO structure in ~8 ms — and the
read-only **lenses** (negation well, storyboard) exploit exactly that: they project the
cheap structure, never a styled SVG.

But the canonical **Drawing** lens — the §3.3-attested EGI→SVG that all three modes
share — must run a real layout engine, and *that* is what the frontier blocks. We cannot
draw the 250-cut taxonomy faithfully and fast.

The display-side answer is **adaptive scope**: don't draw the whole graph at full
fidelity. Draw the part the reader is looking at faithfully, and **collapse the rest into
content-sized placeholders** — the "map app" semantic-zoom move
([[project_organon_adaptive_scope_viewer]]). A placeholder is cheap (one box + a badge),
so the drawn graph the engine actually lays out stays small and within budget no matter
how large the underlying EGI is.

This raises the one genuinely new question in the whole adaptive-scope arc, and the
reason for this doc: **what does it mean for a deliberately incomplete drawing to be
faithful?** A collapsed view, by construction, omits elements the EGI contains, so it
**cannot** satisfy §3.3 totality. It is not a §3.3-correspondent drawing — and pretending
otherwise would be a lie of exactly the kind §3.3 exists to prevent. We need a separate,
weaker-but-honest contract: `attest_overview`.

---

## 2. What an overview *is*

An **overview** is a **navigation projection**: a read-only, lossy view onto an EGI whose
*canonical* drawing (the fully-expanded one) is still governed by full §3.3. It is
defined by an **expanded set** `X` of cuts:

- A cut is **open** (drawn with its real interior) iff it is in `X` and every ancestor of
  it is in `X`. The sheet is always open.
- The **frontier** is the set of cuts that are *not* open but whose parent *is* open. Each
  frontier cut is **collapsed** to a **placeholder** — a single content-sized box drawn in
  the cut's place, bearing a faithful summary of everything it hides, and nothing of the
  hidden interior itself.
- Everything inside a collapsed cut is **hidden**: not laid out, not drawn, not in the DTO.

`X = {all cuts}` is the ordinary full drawing (no placeholders) — full §3.3 applies, and
`attest_overview` reduces to `attest_correspondence`. `X = {}` shows the sheet's direct
content with every top-level cut as a placeholder. The user **expands** by adding a cut to
`X` (which auto-includes its ancestor chain) and **collapses** by removing one (which
auto-removes its descendants). Expansion is **monotone**: each step reveals strictly more,
lays out a strictly larger visible part, and re-attests it.

The overview never produces a graph that re-enters the corpus. It is strictly a *view
onto* an already-attested object — it cannot be asserted, promoted, or used as a
style-only reprojection to cross a gate. It sits **outside the three regimes**, on the
read/navigation side, exactly like pan/zoom (§4 below makes this precise).

---

## 3. `attest_overview` — the navigation-projection attestation

```
attest_overview(egi, dto, collapsed_cuts) -> None        # raises OverviewViolation
check_overview(egi, dto, collapsed_cuts) -> List[str]     # failures, [] = faithful
```

where `collapsed_cuts` is the frontier set (the placeholders present in `dto`).

The contract is **not** "the picture and the proposition denote the same object" — they
deliberately do not. It is the honest, checkable claim a lossy map *can* make:

> **Everything you can see is exactly right, and everything hidden is honestly
> summarized, and the two together lose nothing about the whole.**

Three properties, each a function of `(egi, dto, collapsed_cuts)` alone:

### P1 — Visible-part correspondence (full §3.3 on the quotient)

Form the **quotient EGI** `egi/X`: `egi` with every collapsed subtree removed, each
frontier cut kept as a *leaf* placeholder holding only **synthetic boundary predicates**
(§5.2) for the lines that enter it. The visible elements of `dto` — open cuts, their
vertices and predicates, the visible ligature segments, the frontier placeholders, and the
boundary lines — must be in **full §3.3 correspondence with `egi/X`** via the existing
`check_correspondence`. Containment, incidence, crossing-multiset, argument order,
occlusion: all the §3.3 properties hold on what is drawn. Nothing visible is wrong.

This is the load-bearing reuse: a placeholder is a real (small) cut in `egi/X`, so the
*visible* drawing is a genuine §3.3-correspondent drawing of a real, smaller EGI. We get
P1 — **and P3 (below) with it** — essentially for free from `correspondence_attestation`.
The server's whole overview layout is therefore just `collapse_quotient(egi, X)` →
`generate_layout(quotient)`, which already self-attests §3.3 on the quotient.

### P2 — Faithful summary (the placeholder tells the whole truth about what it hides)

Each placeholder for a collapsed cut `C` bears a badge that must **exactly** equal the
coordinate-free facts of `C`'s hidden subtree — no over- or under-counting:

- `subtree_summary(egi, C)` — recursive `{cuts, vertices, predicates}` inside `C`
  (already implemented in `eg_structure`);
- `polarity(C)` — recto/verso from negation depth (value channel only; see §4);
- **boundary degree** — the number of ligature hooks that cross into `C` (a hidden
  predicate inside `C` wired to a visible vertex outside it; see §5.2). A property of `C`
  alone, computed by `overview_projection.boundary_degree`.

`check_overview` recomputes each of these from `egi` and asserts equality with what the
DTO/badge claims. A placeholder that says "3 predicates inside" when there are 4 fails P2.
(The *drawing*'s faithfulness — that it omits exactly the hidden elements and no others —
is already covered by P1's totality/injectivity against the quotient; P2 is specifically
about the **numeric badge** the reader is shown.)

### P3 — Boundary integrity (a line into the fog ends honestly at the membrane)

**Realized through P1, not as a separate check** (see §5.2). A line of identity enters a
collapsed cut `C` when a predicate *hidden inside* `C` is wired to a vertex *visible
outside* it — the only boundary shape, because a vertex always sits at the **outermost**
area its line reaches, so the hidden end is the predicate and the visible end is the
vertex. In the quotient each such hook becomes a **synthetic boundary predicate** placed
inside `C`'s placeholder, wired to the visible vertex. Full §3.3 on the quotient then
checks, for free, that the drawn line:

- crosses each authorized intermediate cut once and enters `C` **exactly once** (the §3.3
  crossing-multiset, via `crossing_sequence` / `count_cut_crossings`);
- crosses **no** unauthorized boundary, and terminates **inside** `C`'s placeholder (the
  §3.3 identity-endpoint check against the synthetic predicate's position);
- is present once per boundary hook (the §3.3 incidence check), so the drawn count equals
  `C`'s boundary degree.

A synthetic boundary predicate is **anonymous** (`overview_projection.BOUNDARY_REL` — a
small spot the client styles as a cap): it leaks neither the hidden relation's name nor
which hidden predicates share a vertex. Beyond the boundary the line is **summarized, not
drawn**. (A fully-hidden ligature — predicate and vertex both inside the collapsed subtree
— is invisible and contributes only to the interior counts.)

### The expansion law (how the weak contract stays tethered to the strong one)

> For all `egi` and all expanded sets `X`, if `dto` is the overview at `X`, then
> `attest_overview(egi, dto, frontier(X))` succeeds **iff** the visible part is §3.3-faithful
> and the placeholders are exact; and at `X = {all cuts}` the placeholder set is empty and
> `attest_overview` ≡ `attest_correspondence`.

So an overview is a faithful lossy reduction of an object whose canonical (fully-expanded)
drawing is fully §3.3-attested. Drilling all the way down always lands on the real,
attested picture. The overview never *replaces* §3.3 — it is a disciplined view *toward*
it.

---

## 4. What a placeholder may bear — the membrane discipline

A collapsed cut is a **local membrane**: an inner face turned toward content we *choose not
to seize right now*, drawn honestly as opaque. This is the small, reversible, internal echo
of the manifest's outermost membrane — the one separation Arisbe cannot draw, honored by
the blank sheet rather than depicted (`MANIFEST_AND_MEANING.md` §48–64). A placeholder
honors a chosen boundary the same way: it does not depict what lies beyond, it *reports*
it.

What it may report is strictly **form and structure** — how many negations, relations, and
lines of identity lie within, of what polarity, with how many lines crossing in. It may
**never** report **actuality** (`MANIFEST_AND_MEANING.md` floor #6, *no mark bears
actuality*; floor #3, *attest correspondence, never truth*). A placeholder says "a denied
region holding N relations and M nested cuts," never "this region is true / false / the
world." Concretely, inherited verbatim from the lenses ([[project_adaptive_scope_viewer]]):

- **Polarity rides the value channel only** — white = recto, gray = verso. **Hue, texture,
  and line-style stay reserved for a future Gamma foray** (Peirce's tinctures; the broken
  cut / dotted lines of identity). Do **not** reach for modal marking on a placeholder.
- The badge is a count, a polarity, and a boundary degree — all exact functions of the EGI,
  all *notional* (about the representation), none *actual* (about the world).

A placeholder is a fold in the notional, not a claim about the world. That is precisely why
`attest_overview` can be sound: it attests *correspondence of form*, the only thing a mark
is ever permitted to bear.

---

## 5. The collapse model (server side)

### 5.1 The quotient and the reduced LayoutDTO

Given `egi` and an expanded set `X`, the server:

1. Computes the **frontier** (drawn placeholders = collapsed cuts with no collapsed
   ancestor) and the **hidden** element set, via
   `overview_projection.frontier_placeholders`.
2. Builds the **quotient** (`overview_projection.collapse_quotient`): open cuts keep their
   real interiors; each frontier cut becomes a **leaf placeholder** holding only the
   synthetic boundary predicates for the lines that enter it (§5.2). The quotient is a
   real, smaller `RelationalGraphWithCuts`.
3. Runs the existing layout engine on the quotient (`generate_layout(quotient)`). Because
   the drawn graph is small (open content + leaf placeholders), ELK stays within budget
   regardless of `|egi|`, and that call **already self-attests §3.3** on the quotient.
   *(Layout polish: a placeholder is currently sized like an empty cut; sizing it from
   `subtree_summary(egi, C)` so a deeper/larger subtree gets a larger box — treemap-style —
   is a deferred presentation refinement, not part of the contract.)*
4. The resulting `LayoutDTO` already carries the placeholder boxes (as `cut_bounds`) and the
   boundary lines (to the synthetic predicates). The route additionally returns the
   `collapsed` badge map (`overview_projection.overview_summary`) so the client can render
   badges and expand affordances.
5. Hooks `attest_overview(egi, dto, collapsed_map)` **before the DTO leaves the service** —
   the navigation-projection analogue of the §3.3 hook in `layout_service.generate_layout`.

P1 is checked by the unmodified `check_correspondence` against the quotient; P2 is the new
badge-faithfulness layer; P3 falls out of P1 (§5.2).

### 5.2 The boundary-ligature treatment (the one subtlety) — synthetic boundary predicates

A line of identity crosses into a collapsed cut `C` exactly when a predicate *hidden inside*
`C` is wired to a vertex *visible outside* it. (It is always this way around: a vertex sits
at the **outermost** area its line reaches — verified against the EGI, e.g.
`~[ (P *x) ~[ (Q x) ] ]` places the vertex in the outer cut and `Q` in the inner — so the
hidden end is the predicate, never the vertex; a hidden vertex's incident edges are all
at-or-deeper, hence also hidden.)

Dropping the hidden predicate would leave the visible vertex with a dangling line and
nothing in the quotient to attest. Instead, for each boundary hook the quotient mints a
**synthetic unary boundary predicate** (`BOUNDARY_REL`) inside `C`'s placeholder, wired to
the visible vertex. Two payoffs:

- **The quotient stays a valid EGI** (`_validate_dau_constraints` doesn't enforce dominating
  nodes; a synthetic edge in `area[C]` referencing an outer vertex is well-formed), so P1's
  `check_correspondence` runs unmodified.
- **§3.3 attests the boundary line for free** — the line really does cross `C` once and
  terminate inside the placeholder (at the synthetic predicate), which is exactly P3.

A synthetic predicate is **anonymous**: distinct hidden predicates sharing a vertex become
distinct synthetic predicates, so the placeholder leaks neither the hidden relation's name
nor its internal joins — only "k lines enter here." When no ligature crosses any collapse
boundary the placeholder is a clean empty leaf cut and P3 is vacuous (the common
shallow-graph case). Implemented in `overview_projection.collapse_quotient` /
`boundary_incidences`; the synthetic ids are deterministic (`synthetic_boundary_id`) so a
served DTO and its check agree.

### 5.3 Default auto-expand policy

`lod=overview` with no explicit `expand` must still show something legible at the top. The
default policy expands breadth-first from the sheet while the drawn-cut budget allows
(target: the largest cut count ELK lays out comfortably — tune empirically, ~40 to start),
collapsing the rest to placeholders. This yields a legible top-level view of *any* graph
that the engine can actually lay out, with the deep mass folded into badges. The user then
drills via `expand`. The budget is a knob, not a constant baked into the contract —
`attest_overview` is indifferent to *which* cuts are collapsed, only that the result is
faithful.

### 5.4 The route

Add to the Organon read surface (read-only, no session):

```
GET /organon/uods/{uod_id}?lod=overview&expand=<cutId>,<cutId>,...
```

- `lod=full` (default, current behavior) → `generate_layout` + `attest_correspondence`,
  unchanged.
- `lod=overview` → the collapse path above + `attest_overview`. `expand` is the user's
  drilled-into set (ancestors auto-included); absent ⇒ §5.3 default policy.
- The response carries the reduced `layout_dto` + `svg` exactly as today, plus a
  `collapsed` map `{cutId: {summary, polarity, boundary_degree, expandable: true}}` so the
  client can render badges and wire expand/collapse affordances.

A `POST /organon/overview` raw-EGIF sibling can follow the `POST /organon/structure`
precedent if needed; not required for V1.

---

## 6. Client wiring

The shipped lenses already own the **collapse/expand UI model**
([[project_adaptive_scope_viewer]]): the negation well renders nested footprints and
already knows the containment tree from the structure endpoint. Adding overview to the
**Drawing** lens is incremental:

- The Drawing lens gains an expanded-set `X` (default = §5.3 policy result, surfaced by the
  server's `collapsed` map). A placeholder renders as a sized box with its badge; a tap
  toggles membership in `X` and re-requests `?lod=overview&expand=…`.
- `web_viewer/js/diagram-viewer.js` already does pan/zoom/camera; overview adds nothing to
  the camera — it is a *content* reduction, orthogonal to geometric zoom. (Semantic zoom
  and geometric zoom compose: you can pan/zoom within whatever scope is currently drawn.)
- Expanding re-fetches and re-renders; the camera holds (`camera:'hold'`) so the reader's
  context is preserved as detail appears, the map-app feel.

No new rendering engine: overview is the same server-side EGI→SVG, fed a reduced DTO.

---

## 7. Where this sits in the regimes

`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` §4 names three regimes (composition / asserted /
presentation-only). Overview is **none of them** — it is a *viewing* operation, like
pan/zoom, that produces no graph capable of re-entering the corpus:

- It is **not composition** (it authors nothing).
- It is **not asserted/canonical** (it is deliberately incomplete; §3.3 mandatory there).
- It is **not presentation-only/regime-3** — regime-3 ops *preserve* §3.3 by construction
  (`presentation_ops`), whereas overview *deliberately drops* §3.3 totality. It is weaker,
  and honestly labeled so.

The safe statement: **the canonical drawable (full expansion) is §3.3-governed; the
overview is a faithful lossy navigation projection over it, attested by the weaker
`attest_overview`, and can never be a promotion source.** This keeps the bedrock
non-negotiable — every graph that reaches the attested corpus still does so through a full
§3.3 drawing — while letting the reader *navigate* graphs too large to draw whole.

---

## 8. Test plan

`tests/test_overview_attestation.py` (module contract, mirroring
`test_correspondence_attestation.py`):

- **Happy path, corpus-wide:** for representative UoDs and several expanded sets (incl. the
  empty set, a mid drill, and the full set), `attest_overview` succeeds; at `X = {all cuts}`
  it agrees with `attest_correspondence` (the expansion law's base case).
- **P1 adversarial:** corrupt a *visible* element (misplace a vertex, drop a visible
  ligature) → `OverviewViolation` from the reused §3.3 check on the quotient.
- **P2 adversarial:** off-by-one a placeholder badge (wrong cut/predicate/vertex count, or
  wrong polarity) → violation.
- **P3 adversarial:** a boundary line that crosses a forbidden cut, terminates off the
  placeholder, or a boundary-degree tally that disagrees with the EGI → violation.
- **Monotonicity:** expanding a single placeholder yields a still-faithful overview with a
  strictly larger visible set and one fewer placeholder.

`tests/test_eg_structure.py` already pins `subtree_summary`; extend it with **boundary
degree** if that helper lands in `eg_structure`.

Route + E2E (mirroring `test_organon_routes.py` / `test_organon_lenses_e2e.py`):

- `?lod=overview` returns a reduced DTO + `collapsed` map; `attest_overview` fires per
  request; a corrupted reduced DTO is refused.
- The 250-cut frontier UoD that ELK cannot draw whole **does** return an overview within
  budget (the actual frontier win, measured).
- Playwright: drill into a placeholder, see detail appear with the camera held; collapse
  restores the badge.

---

## 9. Build order

1. **✅ DONE (2026-06-14) — `attest_overview` / `check_overview` + the quotient builder.**
   `src/overview_projection.py` (`collapse_quotient` w/ synthetic boundary predicates,
   `boundary_incidences` / `boundary_degree`, `frontier_placeholders`, `overview_summary`,
   `synthetic_boundary_id`) + `attest_overview` / `check_overview` / `OverviewViolation` in
   `src/correspondence_attestation.py`. Unit-tested against hand-built cases —
   `tests/test_overview_attestation.py` (22: happy + expansion-law base case, frontier-vs-
   hidden, P1 adversarial, boundary integrity via P1, P2 lying-badge, monotonicity, quotient
   validity). The contract is settled and runs.
2. **Server overview path** — the collapse + reduced-DTO build in a new
   `layout_service` function (`generate_overview_layout(egi, expanded)` = `collapse_quotient`
   → `generate_layout(quotient)`), hooked to `attest_overview`; the `?lod=overview&expand=…`
   branch in `GET /organon/uods/{id}` returning the DTO + the `overview_summary` badge map.
3. **Client** — Drawing-lens expanded-set + badge rendering + tap-to-expand, camera-hold.
4. **✅ DONE (2026-06-15) — E2E + the frontier measurement (which also found & fixed a budget
   mis-tuning).** E2E shipped 2026-06-15 (`tests/test_overview_e2e.py`). The **headline
   wall-clock measurement** — `tools/overview_frontier_benchmark.py`, the paired baseline on
   the genuine frontier UoD: the **full SUMO ground taxonomy** (123 subsumptions → **246
   cuts**, 132 vertices, 255 edges), rebuilt from `docs/references/SUMO1.2.txt` via
   `tools/suokif_to_eg.py` (it is *not* stored — only the depth-≤2 `sumo_upper` spine, 86 cuts,
   ~1 s, is; the full taxonomy is the ELK super-linear shape that cannot be saved as a drawn
   UoD, which is the very frontier this measures).

   **Result (this laptop):** full ELK `generate_layout` of all 246 cuts = **≈289 s** (unusable
   interactively); the **overview at the default budget = ≈0.8 s** — a **~340×** speedup — and
   it §3.3-attests (`attest_overview` passes). Overview lays ELK out over **147 cuts** (24
   opened with their interior + 123 leaf placeholders) instead of 246 cuts with full interiors
   *and* 255 cross-cutting lines of identity; 99 cuts hidden entirely. The structural guarantee
   (overview ≤ `budget` *opened* cuts regardless of `|egi|`) is unit-tested in
   `tests/test_overview_routes.py`; this is its empirical confirmation.

   **Finding — the frontier is *breadth*, not depth.** SUMO's taxonomy is only **depth 2**
   (each subsumption `A ⊑ B` is a double-cut scroll `~[ (A x) ~[ (B x) ] ]`), yet 289 s slow:
   ELK's super-linear cost here is **packing 123 sibling scrolls and routing 255 lines of
   identity among them**, not nesting depth (a deep nested *chain* measured ~0.2 s — already
   noted in `CURRENT_PLAN.md`). Overview wins by collapsing most siblings into cheap leaf
   placeholders.

   **The budget cliff (and the fix).** The cost is driven by the lines of identity routed
   *among* opened cuts, **not** the opened *count* — so the budget has a sharp cliff. A
   deterministic budget sweep on the frontier graph (`--sweep`): budgets **0→35 all lay out in
   <1 s**, but **40 → ≈210 s** and **60 → ≈275 s** (reproducibly, ≈ the whole-graph time). The
   original `DEFAULT_OVERVIEW_BUDGET = 40` therefore put the *default* overview of the frontier
   graph back over the cliff — defeating the feature. Two fixes landed: (a) `_resolve_collapsed`
   now **sorts** the auto-expand BFS so *which* cuts open is deterministic (Python per-process
   hash randomization had made it vary run-to-run — and which cross-linked scrolls open drives
   the time, which is exactly why an early ad-hoc run fluked a fast 1.1 s); (b) the default was
   lowered to **24** (≈0.8 s, comfortable margin below the cliff). The principled future
   refinement is a **degree-aware** budget (opening a high-degree hub scroll forces global line
   routing — cheap to count, costly to lay out); the conservative count cap is the pragmatic
   guard. Run it: `uv run python tools/overview_frontier_benchmark.py --full-elk --sweep` (the
   baseline + slow budgets are minutes and opt-in; overview-at-default always runs).

## 10. Deferred (author's stated order, after overview+expand)

- **✅ DONE (2026-06-15) — Time-stack production lens.** `src/web_viewer/js/time-stack-lens.js`
  (ES module, lazy-imported), wired into `organon.html`'s Lens selector beside Storyboard (both
  revealed only for a chained UoD). The recorded derivation as a navigable 2.5-D solid: each
  sheet the *real styled* drawing at that state, stacked along the (earned) derivation z-axis,
  with **blue survivor threads** (an element persisting step→step), **green/red entry/exit dots**
  (what a rule added / erased), and a per-sheet rule label. **The spike's flagged "sloping
  threads" fixed correctly:** a surviving element can't be moved independently of its drawn sheet
  (the thread must touch it — correspondence), so instead of a conservative *layout*, each frame
  is **rigidly registered** onto the previous by the similarity (uniform scale + translation, no
  distortion) that best matches their shared survivors — survivors then stand columnar; a thread
  slopes only where the element genuinely moved relative to its cohort (an honest relayout).
  Validated on the 8-frame Praeclarum chain: mean survivor drift **45.9 → 11.9** world units
  (~75 % reduction). E2E `tests/test_organon_lenses_e2e.py::test_time_stack_lens_for_a_chained_uod`
  (mounts the WebGL canvas, zero console errors, Drawing restores). Screenshot:
  `docs/assets/adaptive_scope_spike/d2-timestack-praeclarum-aligned.png`.
- **✅ DONE (2026-06-15) — Liveness / desuetude tracking** (manifest floor #7 — *two deaths, so
  track liveness*). `src/liveness.py`: a `LivenessLog` (one compact summary per UoD: first/last/
  count/per-kind tally/retired, in a single `tomos/.liveness.json`, gitignored as local usage
  churn) with a desuetude policy (`alive` if consulted within `DORMANT_AFTER_DAYS=90`, else
  `dormant`; `unconsulted` if never; `retired` if deliberately so — and re-consulting revives).
  **Consultations recorded at two chokepoints:** opening a UoD in Organon (`GET /uods/{id}` →
  `viewed`) and pressing a corpus UoD into service as a model M in Agon (`_resolve_model_egif` →
  `model`). **Surfaced** as a forward-facing facet in the Organon detail panel (status dot +
  "consulted N× · last …" + a reversible **Retire/Revive** toggle, `POST /uods/{id}/liveness/
  retire`; read-only `GET /uods/{id}/liveness`) and a status dot on list rows
  (`liveness_status`). Outside §3.3 (consulting a sign is not a sign); never mutates the UoD.
  Tests: `test_liveness.py` (8, the policy/reversibility) + `test_liveness_routes.py` (6, both
  chokepoints + retire) + an E2E facet toggle in `test_organon_lenses_e2e.py`.
- **✅ DONE (2026-06-15) — Derivation-DAG lens** (branch structure). A reasoning episode is a
  DAG, not always a line: two rule applications from one state **fork** the development, two
  reaching the same graph **converge** it (the alternate-proofs diamond). Pieces:
  - **Substrate made DAG-capable** (the persisted chain was V1-linear): `ChainStep` gained an
    optional `branch_id`; `ProofChain` gained `at(state_id)` (fork — the next `apply` shares a
    `from_state_id`), a `branch=` label, and `converge_last_into(state_id)` (merge — redirect the
    last step onto a `same_graph` state, refusing a non-match). Persistence round-trips
    `branch_id` and the fork/merge topology. The DAG is carried by the `from`/`to` ids; the
    branch label only colours a line of development.
  - **Native fixture** (`tools/build_branching_demo_chain.py` → corpus UoD `branching_confluence`):
    *confluence of erasure* — from `(P)(Q)(R)`, erase `(P)` and `(Q)` in either order, converging
    at `(R)`. A real ERA at every edge (so the whole DAG is §3.3-attestable), authored as a
    demonstration of branch structure (no theorem citation — method-only provenance). The
    alternate-proofs idea realised *natively* in Dau's calculus rather than imported from a foreign
    prover (TSTP/Metamath were considered — see [[project_organon_adaptive_scope_viewer]] notes —
    but their steps aren't Peirce rules, so they'd violate the sound-step floor).
  - **Endpoint** — `/history-structure` now emits a `dag` block (one node per unique state with its
    drawing/layout/summary + longest-path `depth`; one edge per step with rule/branch/diff) and a
    `branching` flag; `/chain` carries `branching` too, so the client offers the *linear* lenses
    (storyboard / time-stack) only for a line and the **derivation-DAG** lens for any chain.
  - **Lens** — `src/web_viewer/js/derivation-dag-lens.js`: states layered by depth, the real styled
    drawing in each node, edges arrowed + coloured by branch with rule/diff pills (prior art:
    Sutcliffe's IDV, borrowed in spirit). Tests: `test_branching_chain.py` (8) + an E2E in
    `test_organon_lenses_e2e.py`. Screenshot `docs/assets/adaptive_scope_spike/d3-derivation-dag-confluence.png`.
- **Cross-mode UX consistency** — shared `design-system.css`, camera unification across the
  three modes, step/move terminology (the round-1 cross-mode findings).
