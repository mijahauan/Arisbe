# Drawing a hole — schema correspondence

**The question.** We built a graph-with-holes / schema node (`src/schema.py`) and
used it to do real proof work (induction, parametric totality). A hole is written
`⟨name: args⟩` in EGIF. *How does a hole draw, and does the §3.3 correspondence
invariant apply to it?*

**The short answer — settled, and empirically verified.** A hole is **not** a
bounded region with an opaque interior (my first guess, wrong). In the EGI it is an
ordinary `Edge`: `rel[eid] = "phi"`, `nu[eid] = (port lines…)`, flagged as a hole
*only* by the wrapper-side `Schema.holes` dict (`{name: arity}`). So **a hole is
structurally a predicate-position placeholder spot with ports** — it occupies
exactly the slot a relation would, and at instantiation a whole filler graph is
spliced onto its ports (`eg_splice.splice`). The "opaque interior" is *conceptual*
(you don't yet know which graph fills it), not a drawn area.

Because a hole IS relation-shaped, the whole projection-independent stack already
handles it:

- `natural_layout(schema.egi)` builds cleanly — one `NaturalLigature` per
  (hole, port), identical to a relation's incidence. **(verified)**
- `attest_correspondence(schema.egi, dto)` — the full §3.3 check — **PASSES on a
  schema's EGI today, unchanged**: totality, containment, incidence+arity,
  argument-order, the per-ligature crossing-sequence, identity connectedness are
  all well-defined for a hole's ports. **(verified)**
- An **instance** (holes filled) is an ordinary Beta graph and attests normally;
  instantiation **preserves** §3.3. **(verified)**

This is the deep point, and it lands squarely on the project's contract: **§3.3
attests *correspondence*, not assertion/truth** (`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`).
A hole's *boundary* (its ports, its containing area, its argument order, the cuts
its lines must cross) denotes a definite structure, and the picture must denote that
same structure — that is fully attestable. What the hole does *not* carry is a
*committed predicate* (it is a metalevel placeholder, never asserted true — exactly
why `Schema.to_clif` refuses). Correspondence governs the *sign*, not the
*assertion*; so nothing about §3.3 needs to be "suspended" for a hole. There is no
fourth regime here.

## What corresponds, and what is open by design

For a hole `⟨phi: a b⟩` the §3.3-attested boundary data is:

| Boundary datum | Source | §3.3 property |
|---|---|---|
| identity / arity | `Schema.holes["phi"] = 2` | incidence count, argument-order |
| ports (which lines attach) | `nu[eid] = (a, b)` | incidence multiset, identity connectedness |
| containing area | `element_area[eid]` | containment fidelity |
| line crossings | `natural_layout` crossing-sequence | identity crossing-multiset |

Open *by design* (and **not** a correspondence gap): **which graph fills the hole.**
That under-determination is the schema's whole purpose. It is resolved at
`instantiate`, and the resolution is itself checkable — see "instantiation
preserves correspondence" below.

## Refinement (after the historical homework): φ stays metalinguistic

The precedent search (see [docs/DEFINITION_NODE.md](DEFINITION_NODE.md) for the full
finding and citations) sharpens the stance below. **A φ-hole has no object-level
drawing precedent** — Peirce/Roberts/Dau/Sowa denote "any graph G" only in the
*metalanguage* of the rules, never as a mark on the sheet. So the right answer is:

- The φ-hole is **metalinguistic**. In Arisbe it lives only as the EGIF annotation
  `⟨φ: ?x⟩` and **never survives instantiation** (`instance-of-schema` turns schema +
  concrete graph into an ordinary Beta instance — exactly how the tradition treats
  "any graph G"). We do **not** give φ a first-class object-level glyph; doing so
  would drift from Peirce into ad-hoc Gamma. (A real object-level "graph-valued"
  node would be Sowa's Proposition-typed context node — second-order, out of scope.)
- The §3.3 results below still hold and are still worth having: *if* a schema EGI is
  drawn, it corresponds (a hole is relation-shaped). But the normal artifact you
  draw is an **instance**, not a schema. So the "placeholder glyph" build is
  **demoted** — not needed for the schema node, and only ever a typographic nicety
  for the linear/annotation view.

The genuinely *drawable* abbreviation is the **definition node**, which has full
CG/ISO 24707 lineage — see [docs/DEFINITION_NODE.md](DEFINITION_NODE.md).

## Where this sits on the second-order frontier (the deliberate stop)

The line above — "a real object-level *graph-valued* node would be Sowa's
Proposition-typed context node — second-order, out of scope" — is exactly the device
the second-order correspondence contract calls **the node S1 would license**
([SECOND_ORDER_CORRESPONDENCE_CONTRACT.md](SECOND_ORDER_CORRESPONDENCE_CONTRACT.md) §7;
[SECOND_ORDER_CORE_OPENING.md](SECOND_ORDER_CORE_OPENING.md)). The φ-hole is a
**predicative** placeholder: it holds an argument *position* whose filler is supplied
at instantiation and then vanishes (`instance-of-schema`), so it never carries a graph
as a drawn subject and never reaches its own level. That is why it attests §3.3 today
with **no comprehension floor** — a predicative quote is always well-formed (S1's easy
half). The graph-valued node would be the *impredicative-capable* device: a line whose
subject is a whole graph, drawn and read back, which S1 must gate by enclosure (dragon
9: ◇, not □) and which S3 can only attest if the sort is in the drawing (the crossing,
[SECOND_ORDER_CORE_OPENING.md](SECOND_ORDER_CORE_OPENING.md) §4).

So the φ-hole is not an unfinished graph-valued node — it is the **one step short** of
one, on purpose: it does the placeholder work the schema machinery needs *without*
opening the core, exactly as the second-order overlay (option A) does the second-order
work that doesn't require read-back. The schema hole is, in miniature, the frontier's
"ship the predicative device now; hold the graph-valued node for a demonstrated need"
recommendation already enacted.

## Spot, not region — and why that's forced

There is a tempting "region" picture: draw a hole as a labelled box and imagine a
graph dropping inside it. We **reject** it, and the rejection is principled, not
aesthetic: the central commitment is **the drawn shape IS the logical sign**
(`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`; memory *drawn-shape-authoritative*). The
logical sign here is an **edge**, so its faithful drawing is a **spot with hooks**,
not an area. A box-with-interior would draw a *cut/area* — a different logical
object than the edge the hole actually is — i.e. a correspondence violation in
spirit. (If we ever *wanted* hole-as-area semantics, that would be a different
representation — a cut flagged as a hole — and a separate decision; it is not what
`schema.py` builds, and the spot model is what keeps instantiation = splice-at-ports
clean.)

So: **a hole draws where a predicate draws, with its argument lines attaching as
ordinary hooks, glyphed distinctly to read as a placeholder rather than an asserted
relation.** The glyph is the only genuinely new presentation element.

## The one build gap: the placeholder glyph (presentation)

Today `SimpleSVGRenderer` labels a predicate via `egi.get_relation_name(p_id)`
(`simple_svg_renderer.py:423`) and draws every predicate the same way. A hole edge
therefore currently renders **identically to a real relation named "phi"** — which
is the only thing wrong with drawing a schema right now. To fix:

1. **Plumb the hole set to the renderer.** The bare EGI does not know which edges
   are holes (hole-ness lives in `Schema.holes`). Pass the hole-edge id set (or
   hole names) into `render_to_svg` / the layout service, or mark hole predicates in
   the `LayoutDTO` (a `hole_predicates: frozenset[ElementID]` field — additive, and
   it travels with the drawing so a served schema stays self-describing).
2. **Render the placeholder glyph.** A hole predicate draws with a distinct mark —
   candidates: angle-bracketed name `⟨φ⟩`; a dashed/hairline label box; a tinted
   placeholder fill. The argument lines attach exactly as a relation's hooks. This
   is a style knob, defaulted, not a hardcode.
3. **Keep §3.3 intact.** Since the change is label/box styling only (the predicate
   *position* and *ports* are unchanged), attestation is unaffected — a schema with
   the glyph still passes the same check it already passes.

Everything above the renderer (natural layout, attestation) needs **no change** and
**no protected-module edit**.

## Instantiation preserves correspondence (the schema §3.3 theorem)

The property that makes the schema machinery honest:

> For a schema `S` and fillers `F`, let `inst = instance_of_schema(S, F)`. Then
> `inst` is a hole-free EGI that attests §3.3, **and** the boundary the filler
> presents at each former hole occurrence (its ports, in order; its containing
> area) equals the boundary the hole presented — i.e. the splice welds port *i* of
> the filler onto the *i*-th argument line of the hole, in the hole's area.

This is what `eg_splice.splice(host, occ, filler, ports=…, weld=…)` already does;
the theorem just makes it an attested invariant. Pinned by tests (below): the
schema EGI attests, every fixture instance attests, and the per-occurrence port/area
correspondence holds.

## Status / build order

- **DONE (verified, locked by tests):** schema EGIs and their instances attest
  §3.3; instantiation preserves correspondence. *(The conceptual question — "does
  §3.3 apply to a hole" — is answered: yes, fully, as boundary correspondence.)*
- **DEMOTED (after the homework):** the placeholder glyph. φ is metalinguistic, so
  there is no object-level hole glyph to build; at most a typographic `⟨φ: ?x⟩` in
  the linear/annotation view. Not needed for the schema node.
- **The drawable abbreviation is the definition node** —
  [docs/DEFINITION_NODE.md](DEFINITION_NODE.md): it draws as a named spot today, and
  local reversible `expand_at`/`fold` (the Borges-map guardrail) are now built.
- **Later / optional:** if hole-as-*area* semantics ever wanted, that is a separate
  representation (a cut flagged as a hole) and a separate correspondence story; not
  needed for the current schema node.
