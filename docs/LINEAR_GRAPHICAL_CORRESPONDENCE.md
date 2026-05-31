# Linear–Graphical Correspondence: The Central Invariant

**Status**: Draft v1 — 2026-05-30
**Scope**: Specification of the correspondence between an EGI's linear written form and its graphical drawn form. This document defines the contract that every other workstream (transformation rules, layout, rendering, sessions, the three modes, the Endoporeutic Game) must respect.

---

## 1. Why this document exists

Arisbe's primary aim is bringing Peirce's "moving pictures of thought" to life — logic done *in* pictures, not pictures of logic. Dau's formalization guarantees the *logical* correctness of every step; this document specifies the contract that guarantees the *pictures* say what the logic says.

We call that contract the **linear–graphical correspondence**: in any state asserted to mean something, the linear written form of an EGI and its graphical drawn form denote the same mathematical object. When they fail to denote the same object, the system has failed its central purpose — not because the logic is wrong (Dau guarantees that), but because the picture and the proposition have come apart.

This spec is the source of truth for:

- Property tests that audit correspondence (the next workstream after this spec).
- Design reviews of features touching parse, generate, layout, render, transform, or undo/redo.
- Decisions about which user interactions are permitted in which mode.
- Future work on alternative projections (3-D visualization, stylus drawing input, accessibility renderings).

---

## 2. Two spaces with different characters

The correspondence is a map between two genuinely different kinds of space.

### 2.1 Logical space — combinatorial

A Dau EGI is a structured tuple `(V, E, ν, ⊤, Cut, area, ρ)`. Read structurally, it carries **two co-resident graph structures over the same element population**, and the hard problems live in their interaction.

- **Cut containment.** A strict hierarchy — in fact a tree, because `area` is a function: each element lives in exactly one area. The sheet `⊤` is the root; each cut is a node; the area of a cut is the set of its immediate children. This structure is *spatial* in nature: "inside" and "outside" matter, polarity alternates with depth.

- **Ligatures.** The partition of `V` induced by `W` (the equivalence relation declaring two vertex occurrences to be the same identity). This is **not** a containment structure. It cuts across the cut hierarchy — that is what makes Beta graphs Beta. A single identity may have occurrences in many different areas; the ligature is the assertion that those occurrences denote one thing.

The two structures interact non-trivially. A Beta-graph existential threading through nested cuts is a ligature whose identity-class spans multiple areas. The `area` mapping records which areas each occurrence is in; the W-partition records which occurrences are the same identity; and a transformation rule (Iteration, in particular) is meaningful exactly because both structures must remain consistent.

Logical space has no positions, no metric, no orientation. Only structure.

### 2.2 Graphical space — geometric, continuous, and projected

A drawing has glyphs at coordinates, cuts as nested regions with continuous boundaries, ligatures as continuous curves, predicates with hooks attached to glyphs. It has metric properties (lengths, intersection counts, region areas) and topological ones (which region a point lies in, how a curve passes through a region boundary).

But graphical space is itself two-layered, and this distinction is load-bearing:

- **Natural representation space — potentially n-dimensional.** Some logical configurations don't embed naturally on a plane. A ligature crossing through many cuts may need to make a path that visually intersects other ligatures it has no logical relation to. Sibling cuts have no logical left/right ordering, yet a planar layout must choose one. Peirce himself worked in a richer space than the page: he invoked the *back* of the sheet for negation (the cut as a *physical cut*, exposing the verso), bridge marks for ligature crossings, distinct curve styles for distinct identities. The space where the logical structure naturally lives may have more degrees of freedom than the page.

- **Projected representation space — typically 2-D, the screen.** What the user actually sees. A *projection* of the natural representation, governed by stated **conventions**: how ligature crossings are disambiguated (bridge marks? gap markers?), how sibling cut order is chosen (canonical labeling? user preference?), how depth or recto/verso is indicated if needed, what shape conventions distinguish ligatures from predicate hooks. Conventions are introduced as the system commits to them; Gamma-level EGs (Peirce's modal, temporal, and abstractional extensions) will require further conventions and are an expected future source of them.

This split matters because the correspondence has to hold *through the projection*. A 2-D drawing that obeys the conventions can be unambiguously parsed back to the natural representation, and from there to the EGI. A 2-D drawing that *silently* breaks a convention is a correspondence failure — even if the underlying logical map is intact. Conventions are part of the contract.

The Obsidian 3-D graph-viewer analogy is apt. Dropping the planarity constraint in display dissolves artifacts of planar embedding (forced crossings, arbitrary sibling ordering) without changing the underlying logical content. A 3-D view of an EGI is the *same* graph under a different projection. Choosing among projections is presentation freedom, not logical mutation.

---

## 3. The correspondence map

The map runs in both directions, and each direction has different obligations.

### 3.1 EGI → drawing (the "render" direction)

Given an EGI, produce a drawing whose structure preserves the EGI. This is what [elk_layout_engine.py](../src/elk_layout_engine.py) + [simple_svg_renderer.py](../src/simple_svg_renderer.py) do today: EGI → `LayoutDTO` → SVG.

The fidelity claim:

> The drawing's structural data (`LayoutDTO`) preserves, distinctly and unambiguously: the cut containment hierarchy, the area mapping for each vertex/edge/cut, the W-partition (which vertex occurrences share an identity), the predicate–vertex incidence `ν` and its argument order, and the relation labeling `ρ`.

The geometric realization (positions, ligature curves, cut bounds) is then a *projection* of this structural data into 2-D under the chosen conventions.

### 3.2 Drawing → EGI (the "parse" direction)

Given a drawing, recover the EGI it represents. Today this direction is *trivially closed*: Arisbe never has to parse pixels back into logic, because every drawing it shows was rendered from an EGI it already holds. The "drawing" and its source EGI are co-resident; the `LayoutDTO` carries the structural information directly.

The harder version of this problem — a user *draws* a graph with a stylus and the system must recover the EGI from pixel input — is a future regime. The spec accommodates it without committing to it: under that regime, the parse direction becomes a real obligation, and the projection conventions become *rules the user's drawing must obey* in order to be parseable.

### 3.3 What "faithful map" requires

For each `(EGI, Drawing)` pair claimed to correspond, all of the following must hold:

| Property | Statement |
|---|---|
| **Totality** | Every EGI element appears exactly once in the drawing's structural data. |
| **Injectivity** | No drawing element traces back to two distinct EGI sources. |
| **Containment fidelity** | The drawing's cut-region nesting matches the EGI's `area` mapping exactly. No two cuts overlap; nesting depth in the drawing equals nesting depth in the EGI. |
| **Identity fidelity** | The drawing's ligature paths realize the W-partition: vertices in the same partition class are joined by exactly one connected ligature; vertices in different classes share no ligature; the ligature passes through exactly the areas given by the `area` mapping of its members, and no others. |
| **Incidence fidelity** | The drawing's predicate hooks realize `ν`: a predicate's drawn arity equals its EGI arity; argument order is visually distinguishable and matches `ν`. |
| **Convention compliance** | All projection conventions in force are obeyed: ligature crossings disambiguated by the named mechanism, sibling-cut ordering follows the named rule, special markers (bridge marks, polarity indicators, recto/verso, etc.) are present where required. |

The **identity fidelity** row is the load-bearing one. It is where the combinatorial→planar projection is thinnest and where issues #5/#9/#11 historically lived. The **convention compliance** row is where the n-dimensional framing surfaces: a projection can violate correspondence not because the underlying map is wrong, but because a convention got silently broken.

---

## 4. Regimes — when the invariant applies

The invariant is not monolithic. It is scoped to three regimes, and the scoping is what makes it useful rather than restrictive.

### 4.1 Composition (Ergasterion drafts) — invariant suspended

A draft is a graph the user is still constructing. It may be malformed (unclosed cuts, dangling ligatures, missing predicates), syntactically incomplete (a vertex with no identity, a hook with no predicate), or semantically nonsensical. The correspondence cannot hold because there is no canonical EGI for the draft to correspond to.

What the system owes here is not enforcement but *help reaching* a correspondence-bearing state: surface what's unclosed, propose completions, distinguish "well-formed but in flux" from "asserted." Drafts may persist (saved sessions, autosaves) but must not be conflated with canonical graphs.

### 4.2 Asserted / canonical — invariant mandatory

When a graph is claimed to mean something definite — saved to the tomos corpus, asserted as the proposition in an Agon game, made the input to a transformation rule, loaded as the starting state of a session — the invariant attaches in full force. The only mutations permitted that touch the EGI from this point are the six Dau rules. Each rule application must preserve the invariant by construction.

Regime 2 is where the property tests live. It is where Agon's correctness depends; it is where Organon's archived UoDs must be trustworthy; it is where Ergasterion's submitted work counts.

### 4.3 Presentation-only — invariant preserved by construction

Within a canonical graph, the user may freely alter the drawing in ways that touch only the *projection*: reposition a vertex, reshape a cut, reroute a ligature path, change a style, switch from 2-D to 3-D viewing, swap one ligature-crossing convention for another. These are operations on `LayoutDeltas` and projection-choice, **indifferent to the EGI by construction**. They preserve the invariant trivially because they cannot disturb the structural data.

Regime 3 is genuinely a free dimension and should be **always available**, even in strict regime 2 contexts. The system must be able to *prove* that a regime-3 operation hasn't touched the EGI (a structural-equality check on `(EGI_before, EGI_after)` is the cheap version).

The research question of *which* presentations best support human comprehension lives entirely in regime 3, and is unblocked by the invariant rather than constrained by it. It is its own legitimate study — how aesthetic choices, projection choices, and convention choices affect how readily and accurately humans interpret diagrammatic logic.

---

## 5. The hard cases — where the map is most stressed

These are the cases where invariant violations have historically arisen, and where future work needs the most care.

### 5.1 Cut containment under regeneration

When a transformation changes the EGI, layout is regenerated. The new layout must preserve the *containment hierarchy* of the unchanged cuts: a cut that was inside another stays inside, its `area` membership stays consistent, no two cuts come to overlap. ELK's natural drive to optimize for aesthetics can violate this if not constrained. The current anchoring in [layout_service.py](../src/web_api/services/layout_service.py) handles positional continuity but does not by itself enforce containment fidelity.

### 5.2 Ligatures across cut boundaries (Beta)

The W-partition is a combinatorial fact; a ligature path is a planar fact. Issues #5, #9, and #11 all concern variants of this single problem. A ligature must enter and exit each cut boundary at well-defined points, must visit *every* area where its vertex occurrences live and *no others*, must rearrange cleanly when the cut topology changes (#11 in particular), and must preserve the W-mapping under transformation. This is the densest source of correspondence bugs and the densest source of recent correctness work.

### 5.3 Sibling cut ordering and ligature crossings

Two sibling cuts at the same depth have no logical left/right ordering, but a 2-D layout must choose one. A ligature with occurrences in both must cross over (or under) something to reach both. These are *projection artifacts*: they don't exist in the natural representation, only in the projection to 2-D. Conventions disambiguate them. The spec must name which conventions are in force — and a 3-D projection could eliminate the artifacts entirely.

### 5.4 Predicate hook order

`ν` is ordered (a predicate's arguments have an order); the drawing must reflect that order distinctly so a reader can tell which hook is argument 1 vs. argument 2. This is a small but real correspondence obligation, and one that becomes more visible the more arity an EGI uses.

### 5.5 The `LayoutDeltas` free dimension — and the structural impossibility of regime-3 abuse

Regime 3 operations must be **structurally incapable** of changing the EGI. This is not a "check after the fact" — it's a constraint on how regime-3 operations are *defined*.

The EG-semantic basis: objects are undefined outside their area. A vertex in area `A` is meaningful as an occurrence-in-`A`; the same identity may also have an occurrence in area `B`, and the ligature between them is the assertion that they are the same identity. A ligature crossing into and out of a cut is therefore not a single object flowing through regions — it is an *equivalence assertion* between distinct in-area occurrences. A user gesture that appears to "drag a vertex across a cut boundary" is not a coordinate update; it would, if completed, define a new object in a new area and violate the EGI.

The consequence: a gesture that *would* change `area`, alter the W-partition, change predicate hook count or order, or otherwise touch the structural data is *by definition* not a regime-3 operation. The system must:

- Expose regime 3 as a closed algebra over the projection alone — operations whose effect on the `(EGI, projection)` pair is provably restricted to the projection component.
- Refuse or redirect any gesture that would cross a regime boundary. An attempted area-crossing drag should snap back, prompt the appropriate transformation-rule dialog, or simply not be accepted as a regime-3 input.
- Reshape operations on cuts and ligature paths must preserve membership: a cut's redrawn boundary cannot move elements into or out of its area; a ligature's rerouted path cannot change which areas the path visits without also changing the W-partition (which would be structural).

The system architecture must enforce this distinction at the API surface, not at a post-hoc check. The cheap defense (recompute `area`, compare) is *not* sufficient: by the time the check runs, the user has already attempted an ill-defined operation, and the right behavior is to refuse the attempt, not to detect and reverse it.

---

## 6. Boundary events — when the invariant attaches

The boundary events that move a graph from regime 1 to regime 2:

- **Save to tomos corpus** — the graph becomes a persistent record; correspondence must hold from this point.
- **Assert in Agon** — the graph becomes a proposition in a game; correspondence must hold.
- **Apply a transformation rule** — the input must be canonical; the output is canonical; both must satisfy the invariant; the rule itself must be verified to preserve it.
- **Load from corpus** — the loaded graph's drawing must correspond to its stored EGI (verified at load time).
- **(Future)** Submit a stylus drawing as a graph — the drawing must parse to a definite EGI under the stated conventions.

At each event, the system should either verify the invariant or refuse the operation. "Verify" need not always mean "run a full property check" — at hot paths a structural hash comparison may suffice — but the contract is that correspondence is *attested*, not assumed.

---

## 7. Property tests — operational realization of the invariant

The next workstream after this spec is a property-test layer in [tests/](../tests/) that asserts the invariant on canonical states. Anticipated test shapes:

1. **Render round-trip.** For every UoD in the tomos corpus: load → render to `LayoutDTO` → serialize → re-parse the structural data → assert structural equality with the source EGI. Catches losses through the render/serialize path.
2. **Transformation invariance.** For every rule applied to every applicable site in a corpus example: assert the post-state's drawing corresponds to the post-state's EGI, and that the rule's claimed semantic effect on the EGI matches what the rule did. Catches rule-induced drift.
3. **Containment fidelity.** For every canonical state, assert the `LayoutDTO`'s cut bounds correctly nest by `area` membership, no two cuts overlap, depth is preserved.
4. **Identity fidelity.** For every canonical state, assert ligature paths realize the W-partition exactly: connectedness within class, disconnection across class, area-visit set equal to the class members' `area` set.
5. **Incidence fidelity.** Predicate hooks match `ν` in count and order.
6. **Regime 3 non-interference.** For every `LayoutDeltas`-only mutation, assert pre- and post-EGIs are structurally equal.

These tests give the spec teeth. The spec gives them a definition.

---

## 8. Projection conventions in force (May 2026)

§3.3 includes a **convention compliance** row: a drawing can fail correspondence by silently breaking a projection convention even when its underlying structural map is intact. This section commits the current implementation to a specific set of conventions, so future divergences become visible. The list will grow as Gamma extensions arrive and as additional projections (3-D, accessibility, stylus-input) are added; everything here describes the *2-D screen projection* as of May 2026.

The conventions are grouped by what they bind:

### 8.1 Layout-level conventions (visible in `LayoutDTO`)

These conventions shape the structural layout output and are testable directly from the DTO.

- **L1. Deterministic layout** — within a single process, two calls to `engine.generate_layout(egi, style)` for the same EGI produce equal `LayoutDTO`s. The flat-file render path is reproducible. *Across* processes, Python frozenset iteration order may differ; if cross-process reproducibility becomes a requirement (e.g., for diff-based PR review of layouts), this commits us to setting `PYTHONHASHSEED` or sorting area contents before feeding ELK.
- **L2. ELK layered algorithm with hierarchy** — every layout is produced by `elk.algorithm: layered` with `elk.hierarchyHandling: INCLUDE_CHILDREN`. Child cuts are laid out *inside* their parent's box; the parent's bounds expand to fit.
- **L3. Left-to-right primary flow** — `elk.direction: RIGHT`. Layered nodes flow left-to-right; ligatures connecting them have a left-to-right tendency.
- **L4. LAYER_SWEEP crossing minimization** — `elk.layered.crossingMinimization.strategy: LAYER_SWEEP`, a heuristic. Best-effort; not a guarantee that no ligatures cross. When they do cross, see R6 below.
- **L5. Predicate ports are FREE with side hints** — every predicate exposes one port per `ν` index (`{elem_id}_port_{port_index}`). The port carries a `port.side` directive (`EAST` for even-indexed ports, `WEST` for odd), but the predicate node uses `portConstraints: FREE`, so ELK is free to relocate ports for routing. The side hint *biases* placement; it does not guarantee a specific side. Per-port positions are not part of the convention contract; only the existence and `port_index → vertex_id` mapping are.
- **L6. `port_index` is the canonical argument-order channel** — argument order is communicated through `LigaturePath.port_index`, sorted ascending to reproduce `ν`. There is no visual-only carrier of argument order today.
- **L7. Cuts contain their `area` children geometrically** — every element the EGI says is in `area[C]` is inside `cut_bounds[C]`; every sub-cut's bounds are fully nested inside its parent's. This is the §3.3 containment row stated as a convention.

### 8.2 Renderer-level conventions (visible in the SVG output)

These conventions shape the SVG that the user sees. They are not currently tested by automated checks; this section commits us to them so future drift is visible.

- **R1. Cut shape** — rounded rectangle. Corner radius from `style.cut_corner_radius`; black 1-pixel stroke.
- **R2. Polarity shading** — when `style.alternating_shading_enabled`, cuts at odd nesting depth (negative areas) are filled with `style.odd_polarity_fill` (gray); even-depth cuts are opaque white. The shading is the visual carrier of polarity — there are no explicit positive/negative symbols.
- **R3. Sheet of assertion is invisible** — the sheet is *not* drawn. This matches Dau's formalism: the sheet is the unbounded space within which everything else exists, not an enclosed region.
- **R4. Cut z-order: shallow-first** — cuts are rendered in ascending depth so that deeper opaque-white fills cover their parent's gray shading. The user sees alternating shading even though the SVG order is back-to-front.
- **R5. Vertex shape** — filled circle, no stroke. Same color as the ligature, by `style.vertex_fill_color`. A vertex with a label has the label drawn to the right of the dot.
- **R6. Ligatures are straight polylines; crossings are unmarked** — ligature paths are rendered as straight polyline segments between their points, no markers, no arrows, no bridge marks at crossings. When two ligatures cross in the 2-D projection, the visual ambiguity is *accepted*; the W-partition disambiguation lives in the structural data (`LigaturePath.predicate_id` + `vertex_id`) and is not recoverable from pixels alone. This is the §5.3 hard case acknowledged honestly: we depend on the structural channel.
- **R7. Predicate shape** — centered text label, optional background rectangle (`style.predicate_label_box_background`, default transparent). No border around the text. No visible hook markers at the ports.
- **R8. Argument order is not visually distinguishable** — corollary of L6 and R7. The user can see *how many* arguments a predicate has (from the number of ligatures meeting it), but cannot tell from the picture alone which argument is argument 1 vs argument 2. Recovery of the order requires the structural `port_index` channel.

### 8.3 What these conventions imply for the parse direction

The parse direction (§3.2) is trivially closed today: Arisbe never has to recover an EGI from pixels because every drawing it shows was rendered from an EGI it already holds. **R6 and R8 make this dependence load-bearing**: a user could not in principle reconstruct the EGI from pixels alone, because ligature crossings are unmarked and argument order is invisible.

When the parse direction becomes real (stylus drawing input, image parsing), these two conventions become *forced choices*: either we add visual markers (bridge marks for R6, numbered hooks for R8), or we accept that pixel-only input is ambiguous and require a separate channel (typed annotations, gesture order, structural pre-binding). The spec doesn't choose yet; it names the trade-off.

### 8.4 What this section does *not* commit to

- Specific port positions per predicate (only port count + index ↔ vertex mapping).
- Specific cut x/y coordinates (only nesting and containment).
- Specific colors beyond polarity shading (style-configurable).
- Cross-process layout reproducibility (only within-process).
- Visual representations of Gamma extensions (modal, temporal, abstractional) — those will arrive with their own conventions; the spec will be extended.

---

## 9. Open questions to resolve as the workstream progresses

- **Runtime assertions at regime boundaries, not only in tests?** *Partially resolved* — the web layout-service boundary attests every (EGI, drawing) pair before it leaves the service (`src/correspondence_attestation.py`). Save/load and Agon session boundaries remain to be wired. Cost: constant-factor overhead at boundary events. Benefit: catches drift in production, not only in CI.
- **How are projection choices represented?** 2-D is the default and the only projection committed to today (§8). Higher-dimensional presentations (3-D viewers, accessibility renderings) remain an open research direction; once a second projection exists, `LayoutDeltas` (or a parallel structure) will need to carry "which projection" alongside the positions and shapes.
- **When and how does parse-from-image become real?** Image-format input (PNG/JPEG/PDF) parsed back to an EGI would be a major feature — out of scope for this spec, but the architecture should not foreclose it. When undertaken, §8.3 names the forced choice: either add visual markers (bridge marks, numbered hooks) or accept ambiguity and require a separate input channel.
