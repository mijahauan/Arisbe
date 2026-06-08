# Organon Import — Walkthrough, Issues, and the Path "Up to Spec"

*Where this sits on the arc: Organon is the attested, read-only archive (the
[mode contract](#) — a graph reaches the corpus via Agon or as a style-only
reprojection). This document is the **issues memo** from walking the act of
**importing two outside proofs** into that archive **with comments**, and the
design those issues converge on. Read it beside
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the low-warrant import
floor) and [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the proof as a chain of
attested sign-transitions).*

Status: **building (2026-06-08)** — steps 1–3 done, step 4 in progress (§8/§9).

---

## 0. The probe

Two proofs in hand are the probe:

- **Peirce's Law** `((P→Q)→P)→P` — classical, pure-implicational, no lines of
  identity → an **Alpha** double-cut derivation. The safe first import: it
  exercises *comments* and *warrant* without any Beta layout risk.
- **Barbara** `∀x(M(x)→P(x)), ∀x(S(x)→M(x)) ⊢ ∀x(S(x)→P(x))` → **Beta**, shared
  vertices across cut boundaries. Imported second, deliberately, as the case
  that proves the comment + warrant surface is **regime-agnostic**.

They differ in **base state**, and that contrast is itself a demonstration:
Peirce's Law derives from the **blank sheet** (`ProofChain.from_blank()`), the
way Leibniz's Praeclarum does in
[`tools/build_praeclarum_chain.py`](../tools/build_praeclarum_chain.py); **Barbara
is a deduction from premises asserted on the sheet** (the two universals A1, A2),
not from nothing. Both base states are *explicit* — the principle that makes the
chain the unit of meaning (assertion-resides-in-a-context) — but a non-blank base
is a capability the build phase must support (§4.2).

> The proofs are a **probe**, not the destination. What the exercise teaches
> about importing and storing **outside records** — bibliographic provenance,
> warrant, and commentary — and integrating them into a UoD's *understanding*,
> we then apply to the **items already in the Tomos** to bring them up to spec
> (§5). The corpus is currently bare on exactly these records.

---

## 1. Two doorways — and a proof hits the wrong one

There are two import paths, and they admit different *kinds* of thing:

| Doorway | Admits | Warrant | Mechanism |
|---|---|---|---|
| **`/import`** (UI) — [`imports.py`](../src/web_api/routes/imports.py), [`import_service.py`](../src/web_api/services/import_service.py) | a **single linear form** — one graph, the *thesis* | **low**: `warrant:low` tag + bibliographic record, §3.3-attested at the corpus boundary, never asserted true | `POST /import/admit` → `tomos.save_uod()` |
| **`tools/build_*_chain.py`** (CLI) — [`build_praeclarum_chain.py`](../tools/build_praeclarum_chain.py) | a worked **`TransformationChain`** — the *proof* | **none assigned** — seeded as a fully-worked exemplar | `ProofChain` → `save_uod_with_chain()` |

Peirce's Law and Barbara are **proofs**, not single graphs. So the user-facing
`/import` page can only admit *the conclusion as a static graph* — it discards
the derivation. The path that preserves a derivation
(`build_*_chain.py`) is a **developer CLI tool, not a UI import**.

**Issue 1.** The import *experience* a user reaches cannot import a proof; the
thing that can is authoring code. There is no user-facing "import this worked
proof" path. *(Recommendation R1 below.)*

---

## 2. Warrant attaches to the wrong doorway

The low-warrant story ([MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) §"Import")
lives entirely on the **static-graph** doorway: *import admits a fragment at low
warrant, attested for correspondence, never asserted true.*

But a **seeded proof-chain** (`save_uod_with_chain`) carries **no warrant at
all**. It is persisted as a fully-worked exemplar that, in Organon, looks like
canonical content. Yet an *imported* proof — taken from Sowa, Dau, or a
historical source, with our comments — has exactly the provenance warrant is
meant to track: it came from an un-hosted dialogue, it should enter **low**, and
it earns more only by withstanding Agon.

**Issue 2.** Importing a proof *as a chain* should be a low-warrant act (it is a
citation, not a contest you won), but the chain doorway has no warrant gradient.
The proof-import case wants the **union** of the two doorways: a chain
(doorway 2) **carrying** a bibliographic + warrant record (doorway 1). *(R1.)*

---

## 2.5 Provenance has two layers — theorem vs. derivation

Pinning the citations surfaced a structural fact the single `source_citation`
field cannot hold: **each example has provenance at two (really three) distinct
layers that do not share a source.**

1. **The theorem.** Peirce's Law: Peirce, "On the Algebra of Logic" (*AJM* 7,
   1885), the *fifth icon*, ~CP 3.384. Barbara: Aristotle, *Prior Analytics* I;
   the *name* is the medieval mnemonic tradition (Peter of Spain / William of
   Sherwood — disputed). Praeclarum: Leibniz, *Logical Papers* (Parkinson 1966);
   classical proof at PM ✶3.47 (43 steps).
2. **The EG derivation.** Praeclarum: Sowa 2011 (*Semiotica* 186) — a *published,
   transcribable* proof. **Peirce's Law and Barbara: original to Arisbe** (the
   author's constructions in Peirce–Sowa style), **not** transcriptions of any
   published EG proof.
3. **The calculus / method.** Peirce MS 514 (ed. Sowa); Sowa, "Peirce's Rules of
   Inference" (2002); **Dau, *LNAI 2892* (2003)** for the rigorous Beta rules +
   defining→bound relabeling; Roberts 1973 (the historical standard).

**The honesty flag (carried into the record).** Only Praeclarum has a published
EG proof. For the other two, **cite the theorem to its historical source, but
attribute the derivation to the author / Arisbe.** A record that flattens these
into one citation would *misattribute an authored derivation to a historical
source* — the kind of un-attested truth-claim the floor forbids.

**Design consequence — the provenance bundle.** The "bibliographic record" R1/R5
refer to is therefore not one CSL entry but a small **typed bundle**:
`theorem_source` (CSL), `proof_source` (CSL *or* the literal "original to Arisbe /
⟨author⟩"), `method_source` (CSL list), plus a **transcribed-vs-authored-here**
flag on the derivation. Warrant then attaches **per layer**: a known classical
theorem (high external standing — but we still attest correspondence, not truth)
carried by an *authored, machine-checkable, not-yet-Agon-tested* derivation (low
warrant on the proof, §3.3-attestable per step). **Warrant has two objects,
exactly as provenance has two layers.** This generalizes straight into §5:
every corpus item gains the theorem/derivation/method split, and
`theorem_praeclarum` becomes the one item whose `proof_source` is a real external
citation (Sowa) rather than "authored here." The full citation set, split across
the three layers, is captured in
[`docs/references/eg_proofs.bib`](references/eg_proofs.bib).

---

## 3. Where the comments attach — the annotation layer (decided)

The annotation surface today has **one of the three levels** a commented proof
needs:

| Target | Today | |
|---|---|---|
| **step** — "why this rule, here" | ✅ `ChainStep.user_annotation`, set by `ProofChain.apply(note=…)`, persisted in `chain.jsonl`, shown in the Organon chain viewer ([`organon.py`](../src/web_api/routes/organon.py)) | exists |
| **chain / proof-level** — "this is the classic non-intuitionistic move" | ❌ no field — smeared across steps or stuffed into `description` | **gap** |
| **element / area within a state** — "*this* double cut is the crux" | ❌ nothing anchors a note to a vertex / cut / region | **gap** |

### Decision: annotation-as-layer (not annotation-as-record)

A comment is a **telling *about* the proof, not part of it.** Baking comments
into the `ChainStep` / `UoDMetadata` records would make commentary part of the
thing the §3.3 chord and the chain's integrity answer for — exactly what the
philosophical floor forbids ("everything upon the sheet surrenderable"; a
comment must be addable and removable without disturbing the EGI or the chain).

So annotations live in a **side layer**, mirroring the established
**`deltas.json`** precedent (a per-UoD side-file keyed by `(state_id,
element_id)`, never baked into the EGI). The annotation layer is:

- **`annotations.json`** beside `uod.meta.json` (and a `history/annotations.json`
  for chain-bearing UoDs), gitignored only if scratch; persisted in the corpus.
- A **list**, not a keyed dict — unlike a delta (one per element), a target may
  carry **many** annotations (a thread of marginalia). Each entry names its
  target:

```jsonc
{
  "annotations": [
    {
      "id": "ann-…",
      "scope": "uod" | "chain" | "step" | "element",
      "state_id": "s1",        // present for scope ∈ {step, element}
      "step_id": "step-2",     // present for scope == step
      "element_id": "c_…",     // present for scope == element (vertex/edge/cut)
      "text": "…the crux: Peirce's Law is where the double negation can't be …",
      "author": "mjh",
      "created": "2026-06-08T…",
      "tags": ["crux", "historical-note"]
    }
  ]
}
```

**Properties of the layer:**

- **Outside the chord.** Annotations are *not* §3.3-attested — they are not signs
  in the EG, they are commentary about it. §3.3 keeps attesting only the
  (EGI, drawing) correspondence; the layer rides alongside, untouched by it.
- **Regime-indifferent.** Like presentation deltas, an annotation is pure
  metadata — it never affects the logic, so it is free in all three regimes.
- **`user_annotation` and the layer both stay (decided 2026-06-08: "keep
  both").** The per-step `user_annotation` is the *author's own rationale baked
  into the chain* — it travels with the proof as authored, and the existing chain
  viewer + seeding tools keep using it unchanged. The layer is **additive**: it
  adds *marginal / external* commentary at any of the four scopes (and can add
  *further* step-scoped notes alongside the baked-in one). Nothing migrates.

**Issue 3 → resolved by design.** Three annotation targets (chain-level and
element-level are new); a side-layer keyed like deltas; many-per-target;
outside §3.3.

---

## 4. The proofs

Legend (Sowa's numbering, as the author gave it): rule **1** = erase (1e, any
graph in an even/positive area) / insert (1i, any graph in an odd/negative area);
rule **2** = iterate (2i) / deiterate (2e); rule **3** = double cut, draw (3i) /
erase (3e). The sheet is positive; each `~[…]` flips parity. A proposition is the
medad `(p)`; implication `p⊃q` is `~[ (p) ~[ (q) ] ]`.

### 4.1 Peirce's Law — Alpha, from the blank sheet

Stored end state: `~[ ~[ ~[(p) ~[(q)]] ~[(p)] ] ~[(p)] ]`.

```
0.        (blank)
1.  3i    ~[ ~[ ] ]
2.  1i    ~[ (p) ~[ ] ]
3.  1i    ~[ (p) ~[(q)] ~[ ] ]
4.  2i    ~[ (p) ~[(q)] ~[(p)] ]
5.  3i    ~[ ~[ ~[(p) ~[(q)]] ] ~[(p)] ]
6.  2i    ~[ ~[ ~[(p) ~[(q)]] ~[(p)] ] ~[(p)] ]
```

Comment → scope (the concrete evidence the layer's four targets are the right
ones — and that the two *new* scopes carry the most important remarks):

| Author's comment | Scope |
|---|---|
| "the whole thing turns on steps **1 and 5** — the freely-inserted double cuts… precisely the classical move an intuitionistic restriction would forbid" | **chain** *and* **element** (those specific double cuts) — *the crux, and it has nowhere to live today* |
| "classically valid yet **not** intuitionistically provable… the cleanest place to *see* where classicality lives" | **uod** (what the whole example demonstrates) |
| "step 4 iterates `(p)` into the empty cut to form the `¬p` that becomes the consequent"; the per-step readings of 2–3, 5–6 | **step** |

### 4.2 Barbara — Beta, from premises asserted on the sheet

Base state is **not** blank — two universals stand asserted on the sheet
(`~[ [*x] (S ?x) ~[ (P ?x) ] ]` is the "every S is P" shape):

```
A1.        ~[ [*x] (M ?x) ~[ (P ?x) ] ]               (every M is P)
A2.        ~[ [*y] (S ?y) ~[ (M ?y) ] ]               (every S is M)
1.  2i     ~[ [*y] (S ?y) ~[ (M ?y) ~[ (M ?y) ~[ (P ?y) ] ] ] ]
2.  2e     ~[ [*y] (S ?y) ~[ (M ?y) ~[ ~[ (P ?y) ] ] ] ]
3.  3e     ~[ [*y] (S ?y) ~[ (M ?y) (P ?y) ] ]
4.  1e     ~[ [*y] (S ?y) ~[ (P ?y) ] ]               (every S is P) ∎
```

Comment → scope:

| Author's comment | Scope |
|---|---|
| "**Step 1** is the one genuinely Beta-specific move… iterates A1 into A2's scroll *and joins the copied line of identity to the y-line* — `*x` becomes bound `?y` (Sowa relabeling) = universal instantiation derived from the primitives" | **step** + **element** (the iterated line / the join) |
| "A1 remains asserted on the sheet throughout; erase with a final 1e if you want the conclusion standing alone" | **chain** (a note on the derivation's standing assertions) |
| "the premises-vs-blank-sheet contrast with the Praeclarum is itself worth demonstrating" | **uod** (cross-example pedagogy) |
| "if line 1 is where your Beta implementation is least settled, it's also the most useful single test" | **step**, but *engineering metadata* — handled by an annotation **`tag`** (`["fixture","beta-crux"]`), no new scope needed |

**What the mapping confirms.** Real commentary uses **all four scopes**, and the
two scopes that don't exist today (**chain**, **element**) carry the *most
important* remarks — the "steps 1 and 5 are the classical move" crux is
chain+element and has nowhere to live now. A fifth flavor appears — a comment
that is *engineering metadata* — but it rides on the entry's `tags`, not a new
scope. This is the empirical backing for the §3 layer design.

**Base-state finding (refines R3).** Peirce's Law is `from_blank()`; **Barbara
runs from premises asserted on the sheet** — a non-blank base. The build phase's
`ProofChain` must admit an explicit non-blank base (premises asserted), and the
*meaning* differs: a deduction-from-premises vs. a theorem-from-nothing. The
contrast is a teaching feature, not a wrinkle to smooth away.

**Both chains double as regression fixtures.** Peirce's Law must normalize to the
stored `~[ ~[ ~[(p) ~[(q)]] ~[(p)] ] ~[(p)] ]`; Barbara to "every S is P". Barbara
**step 1** (iterate-and-join, `*x`→`?y`) is the highest-value single Beta test —
where an EG engine either keeps the ligature coreference or quietly drops it.

### 4.3 Uniqueness of the group identity — Beta, theory-relative (from axioms)

The third fixture steps past *logical* validity to a **genuinely mathematical**
theorem — true *relative to axioms*, the Barbara-from-premises pattern scaled up
(Γ ⊢ φ rather than ⊢ φ). It is finite-axiom, first-order, short in primitives, and
exercises the **line of identity on equality itself**, which Barbara does not.

**Equality decision (a representational fork, and the sharpest regression
target).** Equality is written the native Peircean way — a **coreference node /
ligature** `[a b]` (two lines joined), *not* a dyadic predicate. Deliberate: it
stresses the ligature machinery on equality. If Arisbe's parser carries equality
as a relation, substitute `(= a b)` throughout (one-to-one; makes the CLIF
round-trip `(= e f)` exact).

Axioms (product `x·y = z` is the ternary `(M x y z)`; A1/A2 are the minimal halves
the proof consumes, A3 is single-valuedness):

```
A1  ∀y. e·y = y     ~[ [*y] ~[ (M e ?y ?y) ] ]
A2  ∀x. x·f = x     ~[ [*x] ~[ (M ?x f ?x) ] ]
A3  single-valued   ~[ [*x][*y][*z][*w] (M ?x ?y ?z) (M ?x ?y ?w) ~[ [?z ?w] ] ]
```

Macro derivation (the one-liner `e = e·f = f`, mechanized):

```
sheet: A1 A2 A3                                       (given)
1. UI  A1 at y:=f                                     (M e f f)
2. UI  A2 at x:=e                                     (M e f e)
3. UI  A3 at x:=e,y:=f,z:=f,w:=e   ~[ (M e f f) (M e f e) ~[ [e f] ] ]
4. 2e  deiterate (M e f f)         ~[ (M e f e) ~[ [e f] ] ]
5. 2e  deiterate (M e f e)         ~[ ~[ [e f] ] ]
6. 3e  erase the double cut        [e f]                            ∎
```

Steps **1–3 are universal instantiation** (a *derived* rule, not a primitive);
**4–6 are detachment** (modus ponens in EG form, primitives). Coreference is
unordered, so A3's consequent landing as `[f e]` is the *same node* as the goal
`[e f]` — the symmetry does silently what "`e=f` vs `f=e`" would otherwise need.

**Primitive-level expansion (granularity match to Peirce's Law).** UI-to-a-named
individual is not one primitive but a fixed subroutine — shown once on the clean
A1 case:

```
0.       ~[ [*y] ~[ (M e ?y ?y) ] ]                  (A1)
1. 1i    ~[ [*y] [?y f] ~[ (M e ?y ?y) ] ]           insert ligature ?y—f (neg. depth-1)
2. 2i    ~[ [*y] [?y f] ~[ [?y f] (M e ?y ?y) ] ]    iterate it inward (depth 1→2)
(—)      …ligature identification: inner ?y is now one line with f  (representational)
3. 2e    ~[ [*y] [?y f] ~[ (M e f f) ] ]             deiterate the spent inner link
4. 2e    ~[ ~[ (M e f f) ] ]                         discharge depth-1 f-segment (an
                                                     inward copy of the sheet's own f-line)
5. 3e    (M e f f)                                   erase the freed double cut
```

So **UI-to-a-name = 1i · 2i · 2e · 2e · 3e, plus one free ligature reading.** Step
4 is a *deiteration* (not illegal negative-area erasure) precisely because `f`
occurs elsewhere on the sheet (A2): the depth-1 segment is an inward extension of
the sheet's own `f`-line. If `f` did not occur elsewhere the discharge correctly
fails — you cannot instantiate to an individual you have not introduced. A2's UI
mirrors this; **A3 runs the subroutine over four bound lines in series inside an
implication** (the real stress case): all four joins are 1i, substitutions must
reach the *consequent* ligature (`[?z ?w]` → `[f e]`), and discharge order matters
to keep the shared `?x`/`?y` lines connected.

**The sharpest regression target** is the `(—)` ligature-identification micro-step:
whether Arisbe materializes the relabel as a graph rewrite or treats a coreference
link as definitional identity decides whether the engine emits a step there at all
— bookkeeping that differs between Roberts, Sowa, and Dau and depends on how
Arisbe stores a ligature. The fixture should assert the expected behavior
explicitly, either way.

---

## 5. "Up to spec" — retrofitting the existing Tomos

What the import exercise defines, the corpus then inherits. The inventory of the
**18 stored UoDs** shows the corpus is **bare on provenance**:

| Record | Populated | |
|---|---|---|
| name / description / category / timestamps / `current.egi.json` | 18 / 18 | ✅ |
| `history/chain.jsonl` | 4 / 18 | ✅ (the HISTORICAL proof-chains) |
| `current.deltas.json` | 5 / 18 | partial |
| **`source_citation`** | **0 / 18** | ✗ always null |
| **`bibliography.json`** | **0 / 18** | ✗ never written |
| **warrant tag** (`warrant:*`) | **0 / 18** | ✗ always empty |
| **annotations** | **0 / 18** | ✗ no layer yet |

Yet the ids already **encode the citations**: `peirce_cp_4_394_man_mortal`,
`dau_2006_p112_ligature`, `sowa_cat_on_mat`, `theorem_praeclarum`. The provenance
is *known*; it is simply not *recorded*.

**"Up to spec" = each corpus item carries an integrated outside-record:**

1. a **provenance bundle** (§2.5) — `theorem_source` / `proof_source` /
   `method_source` typed citations plus a transcribed-vs-authored-here flag, a
   generalization of the single CSL `bibliography.json`
   ([`bibliography.py`](../src/web_api/services/bibliography.py)) — the trace of
   the un-hosted dialogue *each layer* came from. `theorem_praeclarum` is the one
   existing item whose `proof_source` is a real external citation (Sowa), not
   "authored here";
2. a **warrant** level — and the exercise is the natural moment to make warrant
   **first-class** (a field/record), not a magic `warrant:low` tag (see the
   open memory: *warrant not yet first-class*);
3. an **annotation layer** (§3) carrying our understanding of the item — its
   crux, its source's argument, what an Agon challenge to it would target.

The retrofit is a one-time pass over the 18, reusing the *same* record shapes the
import flow defines — so **import and retrofit are one mechanism at two times**:
import builds the provenance bundle at admission; retrofit applies it to legacy
items. (This mirrors the deltas/style "one operation at three scales" pattern.)

---

## 6. Beyond the probe — can we translate a *real* mathematical proof?

Underneath everything: Beta existential graphs **are** first-order logic with
equality, and Peirce's Alpha+Beta rules are **sound and complete for classical
FOL** (Roberts 1973; Dau 2003) — Sowa goes further and derives modus ponens,
universal instantiation, even resolution as *derived* rules. So translating
**statements** is genuinely lossless: FOL formula ↔ EGIF graph is a clean
bijection (the tidy fact behind the whole import question). The real question is
not "can we translate a proof" but *what kind*, and three things bite:

1. **Theory-relative vs. logical truth — no barrier.** Praeclarum and Peirce's Law
   are logical validities (provable from the blank sheet). A real theorem
   ("inverses are unique") is true *relative to axioms*: assert the axioms on the
   sheet, transform to the conclusion — Γ ⊢ φ, exactly the Barbara / §4.3 pattern.
   Only the starting graph changes.
2. **First-order is the ceiling.** Most mathematics in natural phrasing isn't
   first-order (quantifying over sets / functions / properties; induction is
   second-order, or a first-order *schema* = infinitely many axioms). Capturable by
   committing to a first-order axiomatization first (ZFC, PA are both first-order),
   inheriting the verbosity. Genuinely higher-order content pushes into Peirce's
   **Gamma graphs** — never finished, still open research. **Steer Arisbe away from
   that frontier for now.**
3. **Granularity — the limit that actually bites.** The five rules are primitive
   (Hilbert-level: each step inserts/erases one subgraph). A human proof compresses
   millions of such steps behind "by induction," "WLOG," "clearly." Raw
   insert/erase of, say, the infinitude of primes would be astronomical — the same
   explosion as real analysis in unsugared Metamath. **For EG to scale past toy
   theorems, Arisbe needs a layer of *derived rules* and *named lemmas* atop the
   five primitives** — itself a faithful Peircean move (Sowa derives and reuses
   rules). UI and detachment in §4.3 are that layer earning its keep.

**Ingestion caveat.** If we ever ingest *existing* formal proofs rather than author
them: statements port losslessly from TPTP / Mizar / Lean, but proof *steps* will
not — resolution, natural deduction, and tactic scripts don't map onto
erase/insert/double-cut. **Re-derive in Peirce's calculus; don't transliterate.**
This sharpens the doctrine and vindicates §2.5's two layers: import the *theorem*
(lossless), author or re-derive the *proof* (the "authored-here" layer).

**Sweet spot for the next demonstrations:** equational / algebraic theorems from a
small finite first-order axiomatization. §4.3 (group-identity uniqueness) is the
cleanest; order-theory facts and the COLORE mereology axioms work the same way.

## 7. Recommendations (agreed; build deferred)

- **R1 — unify the doorways for the proof case.** A worked proof should be
  importable as a **chain that carries a low-warrant provenance bundle** (§2.5):
  `save_uod_with_chain` gaining the warrant + typed citations that
  `import_service` already knows how to build. (Issues 1 + 2.)
- **R2 — annotation-as-layer** (Issue 3, **decided**): `annotations.json` side
  layer, list-of-targeted-entries, four scopes (uod / chain / step / element),
  keyed like deltas, **outside §3.3**. **Keep both** `user_annotation` (baked-in
  authored rationale) *and* the additive layer (decided 2026-06-08).
- **R3 — explicit but *different* base states.** Peirce's Law first (Alpha,
  `from_blank()`; comment + warrant); Barbara second (Beta, **from premises
  asserted on the sheet** — the build must admit a non-blank base). Proves the
  layer is regime-agnostic *and* demonstrates the premises-vs-blank contrast.
- **R4 — warrant first-class** *and per-layer* (§2.5): warrant on the *theorem*
  vs. warrant on the *derivation* are distinct objects; introduce it by this
  exercise rather than leaving it a `warrant:low` tag.
- **R5 — retrofit the Tomos to spec** (§5) using the same provenance-bundle +
  annotation-layer shapes — the payoff that makes the two-proof probe worth more
  than two proofs.
- **R6 — the chains double as regression fixtures** (§4.2, §4.3): normalize-to-
  stored end states. Highest-value single tests: Barbara step 1 (defining→bound
  relabeling) and §4.3's `(—)` ligature-identification micro-step.
- **R7 — a derived-rule + named-lemma layer** (§6.3): the prerequisite for
  importing *real* mathematics. Build derived rules (universal instantiation,
  detachment, …) and reusable lemmas atop the five primitives; let a fixture be
  authored at *macro* (derived-rule) granularity and **expanded** to primitives
  on demand (§4.3 shows both granularities of one proof). A faithful Peircean move
  (Sowa), and the only way past toy theorems.
- **R8 — pin the equality representation** (§4.3): coreference ligature `[a b]` vs.
  dyadic `(= a b)`. Decide it explicitly; the ligature-identification micro-step is
  the sharpest Beta regression target, and the fixture should assert the engine's
  expected behavior there. Keep the `(= a b)` substitution exact for CLIF
  round-trips.

**Three fixtures, ascending the layers:** Peirce's Law (Alpha, blank sheet,
*where classicality lives*) → Barbara (Beta, from premises, *universal
instantiation along a line*) → group-identity uniqueness (Beta, theory-relative,
*equality on ligatures*). Each adds exactly one capability.

**Companions noted for later** (the author's): a gentler Alpha warm-up —
hypothetical syllogism `((p⊃q)∧(q⊃r))⊃(p⊃r)`; and a second Beta with a teaching
twist — the valid quantifier shift `∃x∀y R(xy) ⊃ ∀y∃x R(xy)`, whose *converse
stalls* (you can't deiterate what isn't there), making cut-nesting and line scope
vivid. **Checked (2026-06-08): the corpus's `beta_converse_mp` is *not* this
shape** — it is *Converse Modus Ponens (crossing lines)*, `R(x,y),
∀x∀y(R(x,y)→S(y,x)) ⊢ R(x,y)∧S(y,x)`, a Tier-3c bridge-at-crossing exemplar (the
consequent swaps arguments, so the lines cross), from premises via 2e/3e. So the
quantifier-shift companion is a genuinely new fixture, not already seeded.
(`beta_converse_mp` also confirms §5 first-hand: per-step `user_annotation`
populated, but `source_citation` / `tags` / `authors` all bare.)

**Open sub-decisions for the build phase:** whether `chain` scope collapses into
`uod` for single-chain UoDs; whether warrant lives on `UoDMetadata` or inside the
provenance bundle; the on-disk home of the bundle (extend `bibliography.json` vs.
a new `provenance.json`).

---

## 8. Build queue (ordered)

1. **Annotation layer** (R2) — `src/` model + `annotations.json` side-store keyed
   like `deltas.json` (list-of-targeted-entries, four scopes), Organon/Ergasterion
   read paths surface it, **outside §3.3**. `user_annotation` untouched.
2. **Provenance bundle + warrant** (R1, R4) — typed `theorem_source` /
   `proof_source` / `method_source` + transcribed-vs-authored flag + per-layer
   warrant; `save_uod_with_chain` carries it (the doorway-union), so a worked proof
   imports as a low-warrant chain.
3. **Non-blank base for `ProofChain`** (R3) — admit premises-asserted base states
   (Barbara, §4.3) alongside `from_blank()`.
4. **Seed the three fixtures** (R3, R6) via `tools/build_*_chain.py`: Peirce's Law
   (Alpha) → Barbara (Beta, from premises) → group-identity uniqueness (Beta,
   theory-relative). Each carries provenance + comments at the scopes §4 mapped;
   each asserted as a normalize-to-stored regression fixture. Decide R8 (equality
   representation) here — it gates the §4.3 fixture.
5. **Retrofit pass** (R5) — apply the provenance-bundle + annotation shapes to the
   18 existing corpus items (ids already encode their citations).
6. **Later** (R7, companions) — the derived-rule + named-lemma layer (the gate to
   real mathematics); the quantifier-shift and hypothetical-syllogism companions.

Steps 1–2 are the foundation; 3–4 prove it on real proofs; 5 generalizes it; 6 is
the horizon. Nothing here touches a protected core module except possibly step 3
(`ProofChain` base state) — confirm before authorizing.

---

## 9. Build log (2026-06-08)

**Step 1 — annotation layer. ✅ Done.** [`src/annotations.py`](../src/annotations.py)
(model: four scopes, per-scope validation, deterministic ids, query helpers — no
layout/attestation imports, **outside §3.3** by construction);
`tomos_service.save_annotations`/`load_annotations` (a `annotations.json`
side-file, mirroring `bibliography.json`; clears on empty); Organon detail +
chain routes surface it (step-scoped notes onto the matching frame,
chain-/uod-scoped at the top), with the baked-in `user_annotation` preserved
alongside (the "keep both" decision visible in the payload). Tests:
[`tests/test_annotations.py`](../tests/test_annotations.py) (9).

**Step 2 — provenance bundle + warrant. ✅ Done.** [`src/provenance.py`](../src/provenance.py)
(`Provenance`: typed `theorem_source` / `proof_source` / `method_sources`, a
**transcribed-vs-authored-here** discriminator, **per-layer warrant**;
self-contained citation formatter so it stays importable by build tools and
`tomos_service` without pulling the web layer; outside §3.3).
`save_provenance`/`load_provenance` + `save_uod_with_chain(provenance=…)` — the
**doorway-union** (a worked proof imports as a chain carrying its low-warrant
attribution). Organon detail surfaces it. **Warrant lives in the bundle, not on
`UoDMetadata`** (that module is protected, and per-layer warrant wants structure
a flat field can't give — resolving that open sub-decision). Tests:
[`tests/test_provenance.py`](../tests/test_provenance.py) (10).

**Step 3 — non-blank base. ✅ Already supported.** `ProofChain.from_egif(egif)`
already exists and is documented as "the conjunction of premises for a
derivation." Barbara's premises-asserted base is `from_egif(<A1> <A2>)`. No code
needed; R3's "the build must admit a non-blank base" was satisfied before we
started.

**Step 4 — seed the fixtures. 🟡 In progress.**
- **Peirce's Law (Alpha) ✅ seeded.**
  [`tools/build_peirce_law_chain.py`](../tools/build_peirce_law_chain.py) — the
  6-step derivation runs end-to-end through the real Dau engine (incl. the
  multi-element `DC+` enclosing `(P)` and `~[(Q)]`), conclusion matches by
  area-signature, §3.3 attests at save. Carries the authored-here provenance
  bundle (theorem = Peirce 1885; method = Dau/Sowa/Roberts) and the §4.1 comments
  as annotations (uod "where classicality lives"; chain + step-1/step-5 "the two
  freely-inserted double cuts"). Now in the corpus as `peirce_law`. Tests:
  [`tests/test_fixture_chains.py`](../tests/test_fixture_chains.py) (4).
- **Barbara (Beta) ⚠️ surfaced the predicted engine gap.** Probing step 1 (the
  iterate-and-join) confirms the memo's §4.2 warning **first-hand**: `IT+`
  iterating A1 into A2's inner area produces a **fresh line** `*z`
  (`~[ (M y) ~[ *z (M z) ~[ (P z) ] ] ]`) — it **copies the line rather than
  joining the copy to the existing `y`**. So *universal-instantiation-to-an-
  existing-line is not a current derived move*; the engine "quietly makes a new
  line" — exactly the coreference-drop §4.2 named as the highest-value test.
  Barbara as authored therefore needs a **derived UI / ligature-join move** (the
  R7 derived-rule layer, arriving early). **Author chose: build it.**

**Step 4b — the derived universal-instantiation move: design (grounded in Sowa
`cg_hbook.pdf` Fig. 14) + a decisive engine discovery.**

- **Spec (Sowa Fig. 14, "Proof of universal instantiation").** UI is a derived
  rule expanding to three primitives:
  **2i** (copy the universal's line/body into its own negative context as a
  *bound* use) → **1i** (*insert a connection between the two lines* — the join)
  → **3e** (erase the freed double negation). Sowa's note seals **R8**: *"the
  operation of inserting a connection between two nodes has the effect of
  identifying two nodes (a substitution of a value for a variable)"* — the
  "connection" **is** a coreference/identity link, i.e. (Arisbe) a shared line of
  identity (equivalently a `=` edge), **not** a dyadic `Equal` predicate. So
  equality is the ligature; the group-identity fixture's `[a b]` is this same
  connection.
- **Discovery (why it's non-trivial — confirmed by probe).** IT+ alone copies the
  universal's line as a **fresh** `z` (probed: `~[(M y) ~[*z (M z) ~[(P z)]]]`).
  The naive fix — rebind `z`'s hooks to the existing `y` — is **rejected by the
  engine's dominating-nodes constraint**: `replace_vertex_on_hook` refuses to
  point a *deep* edge (`(P z)` at depth 4) at a *shallow* vertex (`y`, declared at
  depth 1). **That refusal is correct**: in Arisbe's per-context vertex model a
  line cannot be rebound across depth — it must be **extended** down through the
  cut nest (a coreferent vertex + identity edge at each level) and *then* merged.
  This is exactly Sowa's 1i ("insert a connection") realized here, and exactly the
  point "where most EG engines quietly drop a coreference."
- **Dau confirmation (author's gate to proceed).** Dau, *Mathematical Logic with
  Diagrams* §16.1 *Derived Rules for Ligatures* formalizes the move's pieces as
  derived rules, each proven **syntactically equivalent** (sound + reversible),
  with soundness in §17: **Lemma 16.2** (extending a ligature in a context, from
  iteration + adding-a-vertex), **Definition 16.6 / Lemma 16.7** (merging two
  vertices, constraint `ctx(v₁) ≥ ctx(e) = ctx(v₂)` — exactly the constraint the
  probe hit), Lem 16.1 / Def 16.4 (moving / rearranging). So the derived UI move
  is Dau-formalized, not improvised.

- **Built (Step 4c). ✅** [`src/derived_rules.py`](../src/derived_rules.py)
  `universal_instantiation` = `IT+` (2i copy → fresh line `z`) → insert identity
  edge `=`(target_line, z) in `z`'s context (the 1i connection) → **merge** `z`
  into the target line (Def 16.6 — the merge rewrites incidence directly, so it
  crosses the depth a per-hook rebind cannot). `ProofChain.apply_derived` records
  a derived move as one readable `ChainStep`. Composes public ops only; no
  protected module touched.

**Step 4d — Barbara (Beta) ✅ seeded.**
[`tools/build_barbara_chain.py`](../tools/build_barbara_chain.py): from premises
asserted on the sheet (`from_egif`), **UI → IT- → DC- → ERA**, reaching
∀y(S⊃P) with A1 still asserted (verified by full isomorphism). All five chain
states render and §3.3-attest (incl. the post-UI state with `y` crossing three
cuts). Authored-here provenance (theorem = Aristotle; method = Dau §16 / Sowa
Fig.14 / Roberts) + the §4.2 comments as annotations (the step-1 iterate-and-join
crux, the A1-stays-asserted chain note, the premises-vs-blank uod note). Now in
the corpus as `barbara`. Tests: +4 in `test_fixture_chains.py`.

**Step 4e — uniqueness of the group identity (Beta, theory-relative) ✅ seeded.**
[`tools/build_group_identity_chain.py`](../tools/build_group_identity_chain.py):
from the three axioms (A1 left-identity, A2 right-identity, A3 single-valued)
asserted on the sheet, **UI → UI → UI → IT- → IT- → DC- → ERA → ERA**, reducing
to the bare equality `e = f` (an `=` ligature on the sheet). All 8 steps run
through the real engine; all 9 chain states render and §3.3-attest; the
conclusion is pinned structurally (`_is_bare_equality` — the `=` relation is off
the EGIF surface, so no parse-and-compare). Authored-here provenance (theorem =
folklore; method = Dau §16.6 / Sowa Fig.14 / Roberts) + the §4.3 comments as
annotations (the multi-line crux, the e=e·f=f chain note, the theory-relative
uod note). Now in the corpus as `group_identity`. Tests: +4 in
`test_fixture_chains.py`.

The **multi-line UI** is a new derived move,
[`derived_rules.instantiate_to_lines`](../src/derived_rules.py) — the *consuming,
multi-line* sibling of `universal_instantiation`. Both are Sowa's "insert a
connection ↔ identify two nodes" (Fig.14) / Dau §16.6; they differ only in
whether the universal is **reused** (iterate-and-join, deeper target, universal
stays — Barbara) or **consumed** (in-place: insert `=`(target, source) in the
universal's own negative area, merge source into the enclosing target — group
identity). `joins` carries several `(source, target)` pairs, so A3's **four**
lines instantiate to the two constants `e`/`f` in one move (the consequent
`=(z,w)` lands as the goal `=(e,f)`; coreference is unordered, so f=e *is* e=f —
no symmetry bookkeeping). The move refuses a positive insertion area (would be
unsound). A representational note settling the §4.3 fork: constants intern
*per-area* in this EGIF dialect, so `e` and `f` are **shared generic lines on the
sheet**, not `"e"`/`"f"` tokens (which would duplicate across cuts) — the faithful
encoding of a named individual referenced across contexts. Unit tests:
[`tests/test_derived_rules.py`](../tests/test_derived_rules.py) (3: single-line,
multi-line, positive-area refusal).

**Next:** step 5 (retrofit the 18 existing corpus items to spec — the
provenance-bundle + annotation shapes; ids already encode their citations).
