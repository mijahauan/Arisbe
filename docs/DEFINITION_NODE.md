# The definition node — drawing, and local fold/unfold

Companion to [docs/SCHEMA_HOLE_CORRESPONDENCE.md](SCHEMA_HOLE_CORRESPONDENCE.md).
Both answer "how does an abbreviation draw," but the honest answers differ, and the
difference is the whole point.

## The asymmetry (the historical finding)

| | **Definition node** (`src/definitions.py`) | **φ-hole / schema** (`src/schema.py`) |
|---|---|---|
| what it is | a named abbreviation of **one** determinate graph | a **pattern** — a function from graphs to graphs |
| precedent | strong: Sowa's CG **lambda / formal-parameter** type & relation definitions (ISO/IEC 24707 Common Logic); Peircean root in the **selective** (a capital letter standing for a line, least-enclosed = defining — exactly EGIF `*x`/`?x`) | **none at the object level**: Peirce/Roberts/Dau/Sowa denote "any graph G" only in the **metalanguage** of the rules, never as a mark on the sheet |
| draws? | **yes** — a named **spot** carrying **hooks** (its ports), exactly like a relation; faithful because the logical sign *is* an edge | **no object glyph** — it is metalinguistic; it appears only as the EGIF annotation `⟨φ: ?x⟩` and **never survives instantiation** |
| information | **conservative**: folded ≡ unfolded carry *identical* content (the defining biconditional adds no theorems) | **not** inert: each instance is a genuine axiom; induction really adds strength |
| unfolds to | one (possibly huge) primitive graph | nothing — until you pick a φ, then exactly one readable instance |

**The guardrail this buys.** If Arisbe ever tried to make φ a first-class
object-graph node it would drift from Peirce into ad-hoc Gamma. φ stays a
metavariable in the *precept*; the `instance-of-schema` rule turns schema + concrete
graph into an ordinary Beta instance — which is precisely how the whole tradition
treats "any graph G". Object graphs stay pure Beta with clean Common Logic
semantics; no notational novelty to defend. (If object-level quantification over
propositions is ever wanted, that is Sowa's Proposition-typed **context node** /
Gamma tinctures — a different, second-order job, out of scope.)

## Drawing a definition node

A defined relation is, in the EGI, an ordinary `Edge` with `rel[eid] = name` and
`nu[eid] = (port lines…)`. So it **already draws faithfully today** — a named spot
with its argument lines as hooks — and `natural_layout` + §3.3 attest it exactly as
they attest any relation (same argument as the hole: the drawn shape *is* the
logical sign, and the sign is an edge, so the drawing is a spot, never a region).
The ports are Sowa's formal parameters; instantiation/expansion welds them onto the
host lines. No renderer change is needed for a definition to draw.

## Why you must not unfold everything (the Borges map)

Unfold every definition down to primitive `∈` and "3 is prime" becomes a graph
nobody can read — Borges's map of the empire at 1:1, coinciding with the territory
and equally useless; the same blowup that makes Metamath's `set.mm` enormous. The
resolution is sharper than "abstraction is a necessary evil":

- A definitional expansion is **not lossy compression**. A real map throws detail
  away; the folded and unfolded graphs carry *identical* information. The giant
  expanded picture isn't more faithful — it's the *same* representation drowning in
  redundant ink. You lose nothing by staying folded.
- Expansion is **anti-iconic**. Peirce's whole claim for EGs is that they are
  *icons* — you reason by experimenting on the picture. Unfold "successor" into
  nested `∈` and you can no longer *see* successor as a unit; the icon becomes an
  inventory. Abbreviation is Peirce's own move (selectives, hypostatic
  abstraction): you reason at the level of the named unit, per a precept.

So the working object is the **folded** graph; the fully-expanded primitive graph is
a **referent you compute on demand**, locally, for a soundness check at the one spot
you're standing on — then discard. This is exactly how `unfold` in Lean, δ-reduction
in Coq, and compressed Metamath proofs operate: store folded, expand locally, refold.

## The operations (`src/definitions.py`)

- `expand_at(egi, registry, edge_id, *, return_fold_point=False)` — unfold **one**
  defined spot in place; every other spot stays folded. With
  `return_fold_point=True` it also returns a `FoldPoint` (the inverse data).
- `fold(egi, fold_point)` — contract an unfolded body back to its named spot; the
  **exact inverse**: `fold(expand_at(g, e)) == g` up to `same_graph`.
- `expand(egi, registry)` — the **whole-territory** unfold (every spot, to
  primitives). Retained for **verification only** — proving a defined form is a
  conservative abbreviation of a definite primitive graph (`test_definitions`
  checks `same_graph` to the raw fixture). **Not** the working/reading move; it is
  the 1:1 map.

**The structural guarantee:** fold/unfold are inverse operations on a *selected
spot*, and `fold ∘ expand_at = id`. There is deliberately **no global
"normalize-everything for reading" path** — `expand` is quarantined as a
verification witness. So Arisbe structurally cannot paint itself the Borges map in
the course of ordinary reasoning. (Tests: `test_expand_at_is_local_leaving_siblings_folded`,
`test_expand_at_then_fold_is_identity`, `test_local_expansion_reaches_the_same_territory_as_global`.)

## Open / next

- **Selection-driven fold** (recognize an arbitrary drawn body as an instance of a
  definition and contract it, via the isomorphism engine) — the current `fold`
  takes a `FoldPoint` (the provenance of a just-performed `expand_at`); a UI "fold
  this selection under definition D" wants an iso-matching front door. Sound gate:
  the selection must be isomorphic to the body with ports aligned.
- **CG/ISO 24707 conformance write-up** for the marked-parameter syntax (so the
  definition node is standards-conformant, not bespoke) — cite alongside the
  fixture file.
