# The Reference / Transclusion Node — Design of Record

> **Status (2026-06-29): DESIGNED + increment 1 (1a logic + 1b glyph) SHIPPED.**
> The law is de-risked (§1); this doc fixes *form*, *calculus entry*, and the *attestation contract*,
> scopes an **additive-first** increment that touches no protected module, and banks the one invariant
> that keeps the second-order frontier open. **Built: `src/reference_node.py`** (the Form-2 reference
> edge + overlay mark + resolver seam + `attest_reference` boundary hook + `reference_horizon`) +
> the **render glyph** in `simple_svg_renderer` (`reference_marks=` → a dashed accent spot + a "+N
> beyond view" badge, default-off / byte-identical, no §3.3 change) + `tests/test_reference_node.py` (11)
> + `tests/test_reference_glyph.py` (3). **Next: increment 2 — cross-UoD (the use/mention fork, §7).**
>
> **Companions:** [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §12 (the open fork, option (b)) ·
> [DEFINITION_NODE.md](DEFINITION_NODE.md) (the node this generalizes) ·
> [LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) (calculus entry) ·
> [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §3.3 (the attested invariant) ·
> [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) / [ROADMAP.md](ROADMAP.md) #13 (the 2nd-order frontier).

---

## 1. What is already settled (the de-risk)

A **reference / transclusion node** is Nelson's "the same content, knowably, in more than one place":
a spot that points at material defined elsewhere — a definition body, another corpus UoD, an imported
module — **by name + provenance** instead of inlining it. It is the open architectural fork because a
first-class version touches the protected core (`egi_core_dau` + the §3.3 correspondence contract).

Before opening the core, the **law** such a node must satisfy was prototyped and proven on real graphs,
with no core change — `src/reference_resolution_check.py` (+ runner + 11 tests, all green incl. the
real-ELK §3.3 path). The law, the analogue of `attest_overview`:

> **RESOLVE ≡ INLINED-AND-ATTESTED.**

Checks: **R1** resolve-equals-inline (`same_graph(resolve(), inlined)`), **R2** the resolved graph is
in full §3.3 correspondence, **R3** recoverable (`same_graph(refold(resolve()), host)`, where an
inverse exists), **R4** honest horizon (anything unresolved is *named*, never silently dropped). It
holds on definition references (Power Set, Infinity) **and** an inter-graph transclusion reference
(a cl-imports text-assembly model). Falsifiers bite, so the pass is earned.

**The finding that shapes every decision below:** the reference node already exists in miniature in
*unprotected* code. A **defined-relation edge** ([definitions.py](../src/definitions.py)) is a spot
whose body lives elsewhere; `expand` / `expand_at` *are* resolve; `fold` is the exact inverse. And the
**schema node** ([schema.py](../src/schema.py)) is a graph-with-holes — a *hole is a relation-shaped
placeholder edge* instantiated by the shared `eg_splice.splice`, the very primitive `expand_at` uses.
Definition, schema, and reference are **one family**: named / parametrized / referenced graphs, all
relation-shaped, all port-bearing, all resolved by `splice`.

---

## 2. Decision 1 — Form: a relation-shaped reference *edge* (generalize the definition node)

Three forms were compared (full table in the session log / [ROADMAP.md](ROADMAP.md) #3):

| Form | In the EGI 7-tuple | §3.3 cost | resolve/refold | Scale benefit | Core blast radius |
|---|---|---|---|---|---|
| 1 — new element kind | new 4th set `Ref` (→ 8-tuple) | **must extend** totality + glyph | new machinery | full | **highest** |
| **2 — annotated edge** | a normal `Edge` in `E` | **none** (already a predicate) | **`expand`/`fold`, built** | full | **low–none** |
| 3 — overlay only | nothing (no EGI element) | none | none (material inlined) | **none** | zero |

**Chosen: Form 2.** A reference is an `Edge` in `E` whose `rel` names what it points at and whose
`ν`-ports are the interface — the identity lines that cross into the referenced material, exactly as a
definition's ports are. §3.3 totality/injectivity already cover it (it is in `E`, drawn as a
predicate), *proven* by the harness's R2. `resolve` = `expand` / `expand_at`; `refold` = `fold` — both
already built and round-trip-tested.

Form 1's only edge is referencing material that has *no* clean port-interface; but a port-set is just
"the identity lines crossing the boundary," which definitions already handle, and a propositional
(0-ary) reference is a medad — the harness exercised `(P)`. Form 1 would also park references *outside*
the splice/port family, forcing a later reconciliation with schemas (see §6). Form 3 is retained as a
cheap **complement** (provenance over already-drawn material — the "knowably the same" half), not a
substitute (it buys no scale).

**The relation-shaped framing is a feature, not a limitation** — see §6.

---

## 3. Decision 2 — Calculus entry: it enters like a definition, conditioned in a cut

A reference edge enters the graph exactly as any predicate/definition edge does — and is therefore
already **level-0 clean** ([LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md)):

- It is never *naked on the recto* claiming unconditioned assertion; like every given, it is conditioned
  by the context it sits in (nested into a negative context to be entertained at low warrant).
- It carries **LOW warrant** until tested. A reference is an abbreviation, not a truth-claim: resolving
  it yields whatever the target asserts, at whatever standing the target earned. The reference itself
  asserts only "this material lives there" — `attest_correspondence` attests *correspondence, not truth*
  ([MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) floor).
- Composition (regime 1) may place a reference freely; the correspondence invariant binds only when the
  *resolved* graph reaches the asserted/canonical regime — and there it is an ordinary EGI, fully §3.3.

No new calculus rule is needed. Resolve/refold are the existing definition moves; the reference does not
add an inference step, it abbreviates a sub-derivation (the math register's "by Lemma 3" /
reference-not-inline, [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §9).

---

## 4. Decision 3 — The attestation contract: `attest_reference` = the harness's R-checks

The production hook a reference node calls at its boundary, mirroring `attest_correspondence` /
`attest_overview` (and already prototyped as `reference_resolution_check.attest_reference`):

- **R1 resolve-equals-inline** — `same_graph(resolve(), inlined)`. The abbreviation denotes the same
  mathematical object as writing the material out in full.
- **R2 resolved-is-attested** — run *ordinary* §3.3 on the resolved EGI. **No new §3.3 machinery**: the
  resolved graph is just an EGI; the expansion law ties the weak (referenced) drawing to the strong
  contract exactly as `attest_overview`'s does. A reference with nothing left to resolve *is* the
  inlined, fully-attested graph.
- **R3 recoverable** — `same_graph(refold(resolve()), host)`, where an inverse exists. Lossless
  abbreviation, not lossy summary (contrast `attest_overview`'s P2, which *is* lossy and must declare
  what it hides).
- **R4 honest horizon** — whatever a resolver cannot locate is *named* (`unresolved`), never silently
  dropped. The Borges floor: the map never claims to be the territory.

**Recoverability is a real asymmetry, surfaced honestly.** Definitions have a clean local inverse
(`fold`); a transclusion of another UoD does *not*, today (R3 → N/A, recorded in the harness's
`honest_limits`). The design accepts resolve-only for inter-graph references in increment 1; a
fold-equivalent for transclusion is deferred (§7), not pretended.

---

## 4½. What resolution *means* — co-assertion, and why intra-UoD comes first

A reference is **not a new logical operator.** Resolution splices the body into the area where the
reference sits and welds its ports; juxtaposition in an area *is* conjunction, so a resolved reference
is `G_host ∧ G_target` in one context. The double-cut framing is exact: `~[ ~[ G_host  G_target ] ]` ≡
`G_host  G_target` — DC is an *equivalence*, so the wrapper is **inert**. A resolved reference adds no
logical content; it is an honest abbreviation of co-assertion, and that inertness is precisely what R1
(`same_graph(resolve(), inlined)`) certifies. The real question is *co-location of what with what, at
what cost* — and that splits the design:

- **Intra-UoD (definition / schema) — the inert DC is a *guarantee*.** The co-assertion is inside one
  universe and conservative by construction: the body enters at the reference edge's *position*
  (`expand_at` splices at `_edge_area`, inheriting that context's polarity), it was authored to be
  substitutable, and there is **no second universe** (`DefinitionRegistry` is local) — so no UoD-identity
  merge and no warrant question. The inert double cut is the *soundness witness*, not a leak. This is the
  math register's "by Lemma 3": reference-not-inline, same universe.

- **Cross-UoD — the same inertness becomes the *hazard*.** A transparent common context collapses the
  referenced universe **into** the referencing one — its content co-asserted, its warrant imported
  wholesale, its sheet-of-assertion merged. The bedrock forbids exactly this: level-0 doctrine
  ([LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md)) — nothing enters naked on the
  recto; the import model ([CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md)) — foreign material
  enters at **LOW, attributed warrant**. A naive transparent double-cut around both violates both floors.

  So cross-UoD reference is forced into a **use / mention** fork, and *neither branch is "just a
  reference"*:
  - **Use** (B is to bear on A): the doctrine-clean structure is **not** the transparent DC+ but the
    **scroll** `~[ B ~[ G ] ]` ≡ *B ⊃ G* — B enters in a single (negative) **conditioning** cut,
    referenced as the *ground*, not co-asserted on the recto. This *is* the Agon interpretation-register
    architecture (*given M, then G*) and the level-zero scroll `cut[M cut[P]]`. "Use done right" =
    governed import / conditioning, not co-assertion.
  - **Mention** (point at B *as an object*, without asserting it): B is **not spliced into A's
    assertion** at all — drawn as the read-only "fourth thing" (the [`m_render`](../src/m_render.py)
    idiom, M drawn never asserted), and the reference is a **second-order naming** — the ROADMAP #13
    frontier.

**Consequence for sequencing.** Intra-UoD reference is therefore *conceptually prior, not merely easier*:
it validates the conservative-abbreviation law in the one setting where the inert DC is a guarantee, and
it lets us defer the use/mention decision — which in turn reveals that "cross-UoD reference" is not a
third primitive but **use = import (the scroll)** or **mention = second-order naming**, each riding on
machinery we already have. Increment 1 is intra-UoD; cross-UoD is increment 2+, recorded as that fork
(§7).

---

## 5. First increment — additive, no protected-core change

Build order chosen with the author: **additive-first, core later.** Increment 1 is deliberately
**intra-UoD** — a *resolvable, provenance-bearing* reference to a **definition / schema in the same
universe**, with **zero** change to any protected module. This is the setting where the inert-DC
co-assertion of §4½ is a *soundness guarantee*, not a universe-merge; cross-UoD reference (the use/mention
fork) is held to increment 2+ (§7).

1. **The resolver seam (intra-UoD scope).** ✅ `reference_node.ReferenceResolver` — a Protocol shaped
   like `cl_import_resolver`'s `ImportResolver`, with `DefinitionReferenceResolver` (resolution *is*
   `expand_at`, with its exact `fold` inverse) and `ChainReferenceResolver` so a schema / corpus-UoD
   (`TomosService.load_uod`) resolver drops in additively in increment 2.
2. **Reference-ness + provenance in the overlay** (Form 3 mechanism on a Form 2 edge). ✅
   `reference_node.ReferenceMark` — a serialisable record (`to_dict`/`from_dict`) keyed by edge id,
   carrying target / kind / origin / `warrant="low"`, kept *beside* the EGI. The EGI stays an ordinary
   graph; nothing in `egi_core_dau` moves. (Persisting marks alongside a UoD in `tomos_service` is a
   thin follow-on.)
3. **A reference glyph at render time.** ✅ `SimpleSVGRenderer.render_to_svg(..., reference_marks=...)`
   draws a marked predicate spot distinctly — a **dashed accent box** + a **"+N beyond view"** horizon
   badge (`reference_node.reference_horizon` = the spliced-body size; `render_marks` builds the
   `{edge_id: horizon}` map). Pure chrome: reads the overlay, never the EGI, and changes **no DTO
   geometry**, so §3.3 (which reads the DTO) is untouched. Default `None` is byte-identical to before
   (regression-tested + 95 corpus-wide §3.3/render tests green). Wiring `layout_service` / the web routes
   to *supply* marks is a thin follow-on (no UI authors references yet).
4. **`attest_reference` as the boundary hook.** ✅ `reference_node.attest_reference` builds the
   `reference_resolution_check.Reference` and attests it — R2 (the resolved graph attests §3.3, real-ELK
   tested) + R3 (refold recovers the host). At a production boundary there is no independent inlining, so
   R1 is trivial and R3 carries the round-trip weight; R1 against ground truth is the offline correctness
   proof in tests.

Increment 1a is tested end-to-end (a graph that references a same-universe definition by name resolves to
the inlined raw fixture and §3.3-attests, recoverable via `fold`; the hook bites on a doctored inlining)
and is **reversible** — it commits no structure to the bedrock.

---

## 6. The invariant to bank — keeping the second-order door open

The long-horizon frontier ([ROADMAP.md](ROADMAP.md) #13, [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md))
is **second-order logic about the graphs themselves** — graphs of graphs, abstraction, predication of
qualities. The form decision bears on it, **for the better**, *if* one invariant is preserved:

> **Keep references in the `splice` / port / expansion family, and preserve the abstraction hook — a
> reference must be foldable/abstractable and nameable by a line of identity.**

Why this is alignment (not advancement — the honest scope):

- **The soundness story is reused, not reinvented.** schema.py stays Beta-side by a deliberate dodge: it
  is a *metalevel generator* — a template plus an expansion-to-instances law where every instance is a
  pure Dau-Beta graph. That law *is* `RESOLVE ≡ INLINED-AND-ATTESTED`. A Form-2 reference inherits the
  schema node's existing argument for staying on the right side of the boundary.
- **Hypostatic abstraction is already in the stratum.** Turning a predicate into a subject (Peirce's
  move toward second-order — "honey is sweet" → "honey has sweetness") is
  `definitions.definition_from_selection` + a line of identity. A Form-2 edge *is* abstractable that
  way; a Form-1 sui-generis element is not, without new machinery.
- **Relation-shaped is where predicate-quantification lives.** Quantifying over predicates in EG = running
  identity to predicate-spots. Keeping references relation-shaped keeps them in exactly that stratum, so
  definition / schema / reference remain **one mechanism to extend**, not three to unify.

**Honest caveat.** Form 2 does *not* deliver second-order logic. schema.py explicitly *dodges* in-logic
quantification over formulas; nothing here crosses into quantifying over graphs *inside* the calculus.
The claim is only that Form 2 + the invariant leave the frontier a single-mechanism extension rather
than a three-way reconciliation. The **additive-first** timing protects this directly: it lets us watch
schema ↔ reference unify in practice *before* any structure is committed to the protected core.

---

## 7. Deferred (needs the core, or a later increment)

- **Structural distinguishability + the glyph in §3.3.** If a consumer must tell "this edge is a
  reference, not an asserted relation" at the *EGI* level (rather than via the overlay), or the renderer's
  reference glyph must be attested as a distinct drawn kind, then `egi_core_dau` and §3.3 totality grow a
  branch. This is the one genuine protected-core touch; it is deferred until increment 1 shows it is
  needed. Form 1 effectively front-loads this cost.
- **Cross-UoD reference — the use/mention fork (increment 2+).** Per §4½, this is *not* "more of the
  same reference." **Use** (B bears on A) = governed import via the **scroll** `~[ B ~[ G ] ]` (B
  conditioned, LOW/attributed warrant — the Agon *given-M-then-G* architecture + CORPUS_AND_IMPORT_MODEL),
  **never** the transparent double-cut co-assertion that would merge the universes. **Mention** (B named
  as an object) = the second-order naming of §6, B drawn as the read-only "fourth thing" (`m_render`),
  not spliced into A's assertion. The fork must be chosen before any cross-UoD splice is built.
- **A fold-equivalent for transclusion** (the R3 asymmetry of §4) — an inverse that recovers the
  reference from an inlined corpus graph, so inter-graph references are as lossless as definitions.
- **Reference into non-port-shaped material** — wrapping an arbitrary asserted context that exposes no
  clean identity-line interface (Form 1's niche), if it proves necessary.
- **Transclusion provenance / standing propagation** — how the resolved material's warrant
  ([provenance.standing_of](../src/provenance.py)) surfaces through a reference.

---

## 8. Open questions for the author

1. **Increment 1 acceptance — resolved toward intra-UoD (§4½).** First slice = a reference to a
   *definition/schema in the same universe* (resolve→inline→§3.3-attest, `fold`-recoverable), because
   that is where the inert-DC co-assertion is a guarantee rather than a universe-merge. Confirm; and
   confirm cross-UoD is increment 2+ as the **use (scroll-import) / mention (second-order naming)** fork
   of §7, not a continuation of the same primitive.
2. **Where the reference marker lives** in the long run: overlay (additive, chosen for increment 1) vs.
   in-core (a principled `egi_core_dau` change) — decided by whether non-render consumers must branch on
   reference-ness.
3. **The 2nd-order invariant (§6):** adopt it as a standing design constraint now, so increment 1 and the
   schema track are reviewed against it?
