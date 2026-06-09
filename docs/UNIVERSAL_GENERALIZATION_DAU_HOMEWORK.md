# Closing ∀x — the Dau homework

**Question.** Parametric totality (`test_totality_assembly_parametric`) leaves us
with `[*x] … ~[ [*Y] ~[ [*z](plus x Y z) ] ]` — a sheet graph whose `x` is a
**free line of identity**. A free line on the sheet of assertion is *existential*
(Peirce CP 4.470; Dau): it reads `∃x ∀Y∃z plus(x,Y,z)`, weaker than the theorem
`∀x∀Y∃z plus(x,Y,z)` we want. How do we close the `∀x` **soundly**, and is the
"derived universal-generalization rule, the dual of `existential_generalization`"
the way to do it?

Source consulted: F. Dau, *Mathematical Logic with Diagrams* (the on-disk copy,
`docs/references/mathematical_logic_with_diagrams.pdf`). Page indices below are
0-based PDF page indices (the tool's numbering), with Dau's printed page in
parentheses where shown.

## Verdict, up front

1. **The "dual rule on the finished graph" is provably impossible — do NOT build
   it.** No sound rule sequence can turn `[*x] G(x)` (∃) into `∀x G(x)` on the
   sheet. This is not a gap to be filled; it is a hard wall.
2. **But ∀x IS reachable with Dau's existing primitives**, via a *scaffold tactic*
   that introduces `x` as a **universal** (oddly-enclosed) line from the start and
   re-derives the body under it. The one load-bearing primitive — **isolated-vertex
   insertion in an arbitrary context** — is an explicit **equivalence rule** in
   Dau's calculus. So: yes, closing ∀x will work; just not the way "(b)" was first
   framed.

## 1. Why a final-graph rewrite ∃→∀ is impossible (model-preservation)

Every rule in Dau's calculus is **sound**: if `G₁ ⊢ G₂` then every model of `G₁`
is a model of `G₂` (soundness, Dau Ch. 17 / Thm 24.11, p.281 (271)). Consequently
a *sequence* of rules from the final state `A, [*x]G(x)` can only ever reach graphs
true in **all** models of `A ∧ ∃x G(x)`. But `A ∧ ∃x G(x)` has models in which
`∀x G(x)` is false (a witness exists, yet some other individual fails `G`). Hence
**no sound derivation from the parametric result yields `∀x G(x)`.**

This is exactly why `existential_generalization` has a sound *dual problem*:
that rule (`src/derived_rules.py`) is a **weakening** — it loosens one relational
hook from a named/shared line onto a fresh existential line (`(P…a…) ⊢ (P…*z…)`),
sound only in **even (positive)** contexts (Dau Def. 16.6 / Lemma 16.7; the erase
half is positive-context ERA). Its literal "dual" would be a **strengthening**
(`∃ ⤳ ∀`), and strengthening is never a sound local rewrite. The dual framing is
a category error: UG is a **side-conditioned metatheorem about a derivation**
(`Γ ⊢ φ(x)`, `x` not free in `Γ` ⟹ `Γ ⊢ ∀x φ(x)`), not a transformation of a graph.

## 2. The sound, Dau-native route: a universal-scaffold tactic

The fix is to never have a free existential `x`. Build `x` **universal** and derive
the body beneath it. Every step is a Dau primitive; the polarity-sensitive ones
stay in legal contexts.

The enabling rule — **Dau's isolated-vertex (heavy-dot) rule** — is an
**equivalence**, valid in *arbitrary* contexts (NOT one of the polarity-restricted
generalization rules):

> "**erasing a vertex** — An isolated vertex may be erased from arbitrary contexts.
> **inserting a vertex** — An isolated vertex may be inserted in arbitrary contexts."
> — Dau, Def. 24.10 (Calculus for vertex-based EGIs), PDF p.280 (271); identical
> wording in the diagrammatic calculus, PDF p.245 (236). Soundness: grouped with
> "double cut … inserting a vertex …" as cases where model-equivalence "is
> straightforward to see," PDF p.282 (273).

Empirically confirmed against our own translator: `(A) ~[ [*x] ~[ ] ]` reduces to
`A` — the introduced universal line is vacuous, so its insertion is meaning-
preserving.

### Construction (`A` = the asserted axioms, which do **not** mention `x`)

1. **Insert a double cut** anywhere on the sheet (double-cut rule — equivalence,
   any context): `A ~[ ~[ ] ]`.
2. **Insert an isolated generic vertex `[*x]`** on the *outer* (negative) cut —
   isolated-vertex insertion, the equivalence rule above. `x` is now oddly
   enclosed = **universal**, bound to nothing (`∀x⊤ ∧ A ≡ A`): `A ~[ [*x] ~[ ] ]`.
3. **Iterate the axioms `A` inward** into the inner cut, and **extend the `x`-line
   inward** through the inner cut (iteration rule — equivalence; clause 2 / "extend
   a line of identity inwardly through cuts," Dau Def. 24.10 iteration, PDF p.279).
   The inner cut is **positive** (depth 2, even).
4. **Re-derive the body `G(x)` inside the inner (positive) area** — replay the
   existing parametric chain (the base + step lemmas, the schema-instance graft, the
   two cut-level `IT-` deiterations). Polarity is preserved: every move that ran on
   the sheet (depth 0, positive) is equally legal at depth 2 (positive).
5. **Erase the spent axiom copies** in the inner area (positive-context erasure).

Result: `A ~[ [*x] ~[ G(x) ] ]` where `G(x) = ~[ [*Y] ~[ [*z](plus x Y z) ] ]`,
i.e. **`∀x ∀Y ∃z plus(x,Y,z)`** — closed totality of addition.

## 3. Implementation notes (for the "finally close ∀x" step)

- This is a **derived tactic** (`universal_generalization`), sound *by
  construction* (re-derivation under a vacuously-introduced universal line), not a
  new object-level rule. It belongs beside `existential_generalization` and
  `instantiate_to_lines` in `src/derived_rules.py` — composing public ops only.
- The universal proof is **self-contained**: it does not post-process the
  parametric result. Keep `test_totality_assembly_parametric` as the lemma-level
  checkpoint; add a `test_totality_universal` that runs the scaffold.
- **No protected-module change is expected.** Step 2 inserts on a *negative* cut,
  which the existing `HeavyDotInsertionRule` already permits. (Note a faithful-ness
  gap, not a bug: our `HeavyDotInsertionRule` restricts heavy-dot insertion to
  negative contexts, whereas Dau allows *any* context. Over-restriction is safe —
  never unsound, only incomplete. Widening it to match Dau is optional cleanup,
  unneeded for UG.)
- Mechanically, the tactic = `DC+` (empty double cut) → heavy-dot insert on the
  outer cut → `IT+` the axioms + extend the line inward → replay the recorded
  base/step/assembly `ChainStep`s with their target areas offset into the inner
  cut → `ERA` the spent axiom copies.

## Bottom line

Confidence that ∀x closes: **high** — but via the scaffold tactic, not a dual rule.
The single fact that makes it sound is Dau's isolated-vertex rule being an
equivalence valid in *any* context (Def. 24.10), which lets us introduce a
universal line for free and re-derive beneath it. The "dual of EG" idea is retired
as provably unsound.
