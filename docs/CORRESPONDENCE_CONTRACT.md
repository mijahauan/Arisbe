# The Correspondence Contract — a prover-agnostic specification

**Status:** SHIPPED (2026-07-07). A standalone, implementation-independent statement of the
linear↔graphical correspondence property that Arisbe enforces, plus a dataset/interchange-schema
card for the [tomos](GLOSSARY.md#tomos) corpus. **Any** tool — a different EG implementation, a
theorem prover, a drawing checker — can implement this contract and interoperate over the same
EGIF text and the same corpus.

- **Grounded in:** [`src/correspondence_attestation.py`](../src/correspondence_attestation.py)
  (the runtime check), [`tests/test_correspondence_invariant.py`](../tests/test_correspondence_invariant.py)
  (the six §7 property tests), and the full narrative contract
  [`LINEAR_GRAPHICAL_CORRESPONDENCE.md`](LINEAR_GRAPHICAL_CORRESPONDENCE.md).
- **Enforced by:** the MCP verifier's `attest` tool ([MCP_VERIFIER.md](MCP_VERIFIER.md)) — this
  document *states* the property that tool *checks*.
- **Why prover-agnostic matters:** the field has no shared diagrammatic-proof benchmark
  ([PROSPECTS_MULTIPERSPECTIVE.md](PROSPECTS_MULTIPERSPECTIVE.md), R2). A stated contract + a
  licensed corpus is the smallest thing that lets two implementations agree on what "the picture
  and the proposition denote the same object" means.

This spec covers **Alpha** (propositional) and **Beta** (first-order, lines of identity)
existential graphs. **Gamma / second-order** is a documented future direction; the contract is
written to *accommodate* it additively (the property list and the failure taxonomy grow; the
regime structure does not change) but does not yet commit to it.

---

## 1. The two objects

The contract is a property of a **pair** `(EGI, drawing)`. It says nothing about *truth* — an
EGI can be false and still be in perfect correspondence with its drawing. It is a property of
**integrity of formation**: picture and proposition denote the same mathematical object.

### 1.1 EGI — the logical object (Dau's formalism)

An **Existential Graph Instance** is Dau's structure `(V, E, ν, ⊤, Cut, area, rel)` with an
alphabet and an optional constant map:

| Component | Meaning |
|---|---|
| `V` | vertices (lines of identity / individuals) |
| `E` | edges (predicate/relation occurrences) |
| `ν` (`nu`) | incidence: each edge → an **ordered** tuple of vertices (argument order matters) |
| `⊤` (`sheet`) | the sheet of assertion (the outermost area) |
| `Cut` | cuts (negations), each an area boundary |
| `area` | for each area (sheet or cut) → the set of elements it directly contains |
| `rel` | each edge → its relation name |
| `rho` (`ρ`) | each vertex → a constant label, or `null` if generic |
| `alphabet` | relation/function/constant symbols with arities |

The interchange form is EGIF (a linear string) or the EGI JSON schema in §5. Two structurally
equal EGIs may differ only in element ids; a **canonical signature** (UUID-independent) gives
each element a stable content-derived label so equality and addressing are id-independent.

### 1.2 Drawing — the graphical object (a layout)

A **drawing** is a projection of the EGI into geometry. Abstractly it is a `LayoutDTO`:

| Field | Meaning |
|---|---|
| `vertex_positions` | each vertex → a point (the drawn dot) |
| `predicate_positions` | each edge → a label box (position + extent) |
| `cut_bounds` | each cut → a bounding geometry, read through the style's **drawn shape** (an inscribed ellipse for oval/circle styles, the box otherwise) |
| `ligature_paths` | for each (edge, port) → a polyline from the predicate hook to a vertex, carrying `port_index` (argument order) |

The drawing is the output of an **optimizer** (a layout engine that *searches* for geometry). It
can fail per-instance and silently. That is exactly why the contract is checked at runtime on
every produced pair, not proven once — a fallible producer demands a per-instance check.

---

## 2. The correspondence properties

A pair `(EGI, drawing)` is **in correspondence** iff *all* of the following hold. Each is a pure
function of `(EGI, drawing)` — it never inspects any linear form. (Reference: `check_correspondence`
in `correspondence_attestation.py`.)

### P1 — Totality and injectivity
Every EGI element (vertex, edge, cut) appears exactly once in the drawing, and the drawing
introduces no element the EGI does not have. The map is a bijection on elements.

### P2 — Containment fidelity
For every area `A` (the sheet or a cut) and every element the EGI places directly in `A`, the
element's drawn geometry lies **inside the drawn shape of every ancestor cut of `A` and outside
every non-ancestor cut**. A dot is tested by point containment; a predicate box and a sub-cut by
whole-shape containment. The cut's **drawn shape is authoritative** — "inside cut `C`" means
inside the curve the renderer actually draws for `C`, identically across styles.

### P3 — Incidence fidelity
For every edge, the multiset of vertices its ligature paths terminate at equals the multiset in
`ν`, and the count of paths equals the edge's arity. (No missing arms, no stray arms.)

### P3′ — Argument order
The ligature paths of an edge, sequenced by ascending `port_index`, reproduce the **ordered**
tuple `ν(edge)` exactly. (A binary `loves(a,b)` is not `loves(b,a)`.)

### P4 — Identity fidelity (three checks)
1. **Endpoint placement.** Each ligature path ends at the drawn position of its vertex, and both
   endpoints lie within their respective areas' drawn cut bounds.
2. **Crossing-multiset equality.** A ligature that connects a predicate in area `Aₚ` to a vertex
   in area `Aᵥ` crosses the boundary of **exactly** the cuts on the area-tree path between `Aₚ`
   and `Aᵥ` (the projection-independent `crossing_sequence`) — each such cut once, and no other
   cut's boundary at all. This is the topological invariant: buffers/metric heuristics fail here;
   the required-vs-actual crossing *multiset* is the correct check.
3. **Shared-identity connectedness.** For a vertex referenced by several predicates, the union of
   the paths ending at it forms **one** connected component rooted at the vertex's drawn dot — the
   drawing shows one line of identity, not several coincidental arms.

**Convention compliance** (P5, extensible): a drawing can fail even with an intact structural map
by breaking a committed projection convention (heavy line of identity, hook placement, oval cuts).
The convention set in force is enumerated in `LINEAR_GRAPHICAL_CORRESPONDENCE.md` §8; it grows as
projections (3-D, accessibility, stylus input) and Gamma extensions arrive.

---

## 3. The six §7 test shapes (operational realization)

The properties above are audited corpus-wide by six families of property test
(`test_correspondence_invariant.py`). An independent implementation demonstrates conformance by
passing analogues of all six:

1. **Totality / injectivity** — P1 on every corpus graph, every engine, every style.
2. **Transformation invariance** — apply each of the six Dau rules; the post-transformation pair
   is still in correspondence. (Correspondence survives *every rule application*, not just the
   initial draw.)
3. **Containment** — P2, incl. correct sub-cut nesting.
4. **Incidence + argument order** — P3 and P3′.
5. **Identity (3-way)** — the three P4 checks, each as its own shape.
6. **Regime-3 non-interference** — every projection-only mutation (vertex translation,
   interior-preserving cut reshape, ligature reroute) preserves correspondence and provably does
   not touch the EGI. (See §4.)

Determinism is a precondition of shape #2: layout of a fixed `(EGI, style, engine)` must be
reproducible within a process, else "transformation invariance" becomes flaky.

---

## 4. Regimes — when the contract applies

The contract is **not monolithic**. It is scoped to three regimes; the scoping is what makes it
useful rather than restrictive.

| Regime | When | Contract status |
|---|---|---|
| **1. Composition** | Ergasterion drafts, a graph being built freehand | **Suspended on purpose** — a half-drawn graph need not correspond to anything yet. |
| **2. Asserted / canonical** | anything that enters the record: every rule application, every corpus load/save, every Agon result | **Mandatory and runtime-attested** — the pair is checked at every boundary event. |
| **3. Presentation-only** | pure appearance nudges (move a dot, reshape a cut without crossing a boundary, reroute a ligature) | **Preserved by construction** — regime-3 operations form a closed algebra over the projection alone; a gesture that *would* change the EGI is by definition not a regime-3 operation and is refused. |

The failure taxonomy (§below) applies in regime 2. A regime-1 draft producing failures is expected,
not a bug. A regime-3 operation that produces *any* structural change is the one thing the algebra
must make impossible.

---

## 5. The failure taxonomy

`attest` (and any conforming checker) returns, on a non-corresponding pair, a list of failures
each tagged by the property it violates. The taxonomy is the checker's diagnostic vocabulary:

| Tag | Property | Example message |
|---|---|---|
| `totality` | P1 | `vertex(s) missing from DTO: [...]` |
| `injectivity` | P1 | `stray cut IDs in DTO: [...]` |
| `containment` | P2 | `elem X in egi.area[C] but drawn outside C` |
| `incidence` | P3 | `predicate E arity mismatch — ν says 2, drawing has 1` |
| `incidence` (order) | P3′ | `argument order for E does not reproduce ν` |
| `identity-endpoint` | P4.1 | `path end does not coincide with vertex position` |
| `identity-crossing` | P4.2 | `ligature crosses cut C (not on its area chain)` / `crosses authorized cut ≠ once` |
| `identity-connectedness` | P4.3 | `identity line is not rooted at the vertex` |
| `convention` | P5 | a committed projection convention silently broken |

An empty list means the pair is in correspondence. A conforming checker need not reproduce the
exact strings, but must partition failures by these property tags so reports are comparable.

---

## 6. Interchange schema card — the tomos corpus

The corpus is the concrete benchmark the contract is stated against: **87+ canonical EG examples**
with EGIF / CGIF / CLIF / FOPL variants, worked proof chains, and provenance.

### 6.1 License
**MIT** (`LICENSE`, © 2025 Michael James Hauan). The corpus and schema are freely reusable,
including for building a competing implementation or a shared benchmark.

### 6.2 EGI JSON (`<name>.egi.json`)
A direct serialization of Dau's structure — the interchange unit a second implementation reads:

```json
{
  "V":     [{"id": "v_…", "is_generic": true, "label": null}],
  "E":     [{"id": "e_…"}],
  "Cut":   [{"id": "c_…"}],
  "sheet": "sheet_…",
  "area":  {"sheet_…": ["c_…", "e_…", "v_…"], "c_…": ["e_…"]},
  "nu":    {"e_…": ["v_…"]},           // ordered incidence (argument order)
  "rel":   {"e_…": "P"},               // edge → relation name
  "rho":   {"v_…": null},              // vertex → constant label or null (generic)
  "alphabet": {"R": ["P","Q","R"], "ar": {"P":1,"Q":1,"R":1}, "C": [], "F": []},
  "layout_deltas": {"v_…": {"type": "vertex_position", "position": [x, y]}}
}
```

`layout_deltas` is the regime-3 free dimension: sparse hand-adjustments to the projection that
carry **no logical content** (a conforming reader may ignore them entirely without changing meaning).

### 6.3 Chain JSONL (`history/chain.jsonl`)
A worked proof is an append-only sequence of sound rule applications. Line 1 declares the initial
state; each subsequent line is one `ChainStep` (rule name + selection/target locators + the
resulting state id). States are stored beside it as `history/states/<id>.egi.json`. Replaying the
chain from the initial state must reproduce every recorded state — the proof-level analogue of the
per-step soundness the `apply_rule` tool checks.

```json
{"type": "initial", "initial_state_id": "s0", "schema_version": 1}
{"type": "step", "rule": "ERA", "selection": [...], "to_state_id": "s1"}
```

### 6.4 Provenance
Each UoD record carries authorship, citation, and creation/modification timestamps (`index.json`,
`<name>.meta.json`). Sourced graphs (theorems, transcribed proofs) carry a citation bundle; a
sourceless graph reports `has_source: false` and fabricates nothing (`scholarly_citation.py`).

---

## 7. Conformance checklist

A second implementation is **contract-conforming** if it:

1. Reads and writes the §6.2 EGI JSON (round-trips a corpus graph to the same structure).
2. Produces a drawing (any projection) and checks all §2 properties on the pair.
3. Passes analogues of all six §3 test shapes against the tomos corpus.
4. Partitions failures by the §5 taxonomy tags.
5. Respects the §4 regime scoping (checks in regime 2; guarantees non-interference in regime 3).

Items 1–2 are the minimum for *interoperation*; 1–5 are the full contract.
