# Modality without Gamma

*The diachronic sheet, the standard translation, and why the real frontier
is second-order logic about the graphs.*

*A philosophy-spine companion to
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the ground beneath the
chain) and [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the chain itself).
Distilled from a 2026-06 conversation, archived at
[references/EG-modality-conversation.pdf](references/EG-modality-conversation.pdf).*

---

## The thesis, flatly

**Gamma, conceived as a *modal* extension, is not a problem Arisbe needs to
solve.** Beta Existential Graphs in their full Arisbe-*diachronic* form — the
sheet plus the rule-governed history of sheets, plus the corpus of universes —
express the work of the modern □ and ◇ *with no new modal mark*, and express it
with *better clarity*, because the apparatus those operators quietly presuppose is
**drawn** rather than hidden in a metalanguage. *(Scope, post-examination — see §3
and [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) §4: the "expresses
everything □/◇ express, no gap" guarantee is exact for **propositional** modal
logic via van Benthem; the first-order-with-identity modality the §2 construction
features lies beyond that theorem and carries its own declared commitments. The
load-bearing claim — **no new mark** — is untouched; the unconditional
completeness boast is scoped down to adequacy.)* Peirce reached for the broken cut and then
the tinctures to carry modality on a single static sheet; the load they were
meant to bear is carried, exactly and without remainder, by the diachronic
structure Arisbe already maintains and attests.

This is not a stance dressed as a result. It rides on a settled fact of modal
model theory — the **standard translation** of modal logic into first-order
logic — and it leaves a precise residue. The residue is **not** modal and **not**
a tincture: it is *second-order logic about the graphs themselves*, and that —
not Gamma — is the real frontier.

---

## 1. The construction: a modal operator is a drawn quantifier over a frame

A modal operator is not primitive content. It is shorthand for quantification
over a **Kripke frame** — a set of worlds *W*, an accessibility relation *R*
between them, and a valuation. The **standard translation** ST makes this
explicit, sending a modal formula to a first-order formula with a free
world-variable:

> ST(□φ, w)  =  ∀w′ ( R(w, w′) → ST(φ, w′) )
> ST(◇φ, w)  =  ∃w′ ( R(w, w′) ∧ ST(φ, w′) )

The operators vanish into ordinary ∀ and ∃ over the frame. And ∀/∃ over a
relation is exactly what Beta EG draws. So the only thing standing between Beta
EG and modal expressivity is *a representation of the frame* — and that is
precisely what Arisbe's diachronic architecture supplies natively, in two
readings:

- **The trajectory reading** (provability / derivability modality). Worlds are
  **sheets** — the immutable EGI states; *R* is the **legal-transition relation**
  of the derivation DAG. Then "◇φ" is "some legal trajectory scribes φ" and "□φ"
  is "every legal trajectory scribes φ." This is the diachronic gloss the
  conversation reaches by a different road: *possibility is the **branching** of
  legal trajectories, necessity is their **convergence**, and the only necessity
  is to follow the rules.* That sentence **is** the standard translation under the
  legal-transition frame. The frame is the object Arisbe already builds:
  [`src/egi_transformation_history.py`](../src/egi_transformation_history.py) (the
  DAG of states and steps),
  [`src/universe_of_discourse.py`](../src/universe_of_discourse.py) (the diachronic
  entity), surfaced as the
  [derivation-DAG lens](../src/web_viewer/js/derivation-dag-lens.js).

- **The alethic reading** (□ = true in all accessible worlds). Worlds are the
  corpus's several **UoDs / models M**; *R* is an accessibility relation drawn
  **among** them. The corpus is already a *library of universes*, mutually
  inconsistent without contradiction (MANIFEST floor #5). Modal force becomes the
  Endoporeutic Game's quantification over the choice of M — which the interpretation
  register already performs (`/agon/where-it-holds`, the inverse pivot across
  models). The conversation names this lineage outright: *the dialogical
  relativization to M does the modal work the older syntactic operators reached
  for, the same way Kripke/Hintikka relativization to worlds does.*

Either way, **□ and ◇ become Beta quantifiers over a frame that is on the sheet**,
not operators whose meaning lives off-stage.

---

## 2. Carrying exactly the load Peirce gave the broken cut and the tinctures

Peirce's Gamma devices were attempts to make a *single static sheet* bear
modality. Each maps cleanly onto the drawn frame:

| Peirce's device | What it was for | Carried in Arisbe by |
|---|---|---|
| **Broken cut** | ◇ / □ on the sheet | ∃ / ∀ over **accessible sheets**, with the accessibility *visible* (the trajectory branch, or the relation among M's). |
| **Tinctures** (the provinces / universes) | "which universe this region belongs to" | The **explicit identity of the sheet/M** a region inhabits. The corpus *is* the library of tinctured universes — made first-class as separate UoDs, not as colours on one sheet. |
| **The case Peirce kept failing at** — *iterated* broken cuts, and **lines of identity crossing tincture boundaries** (trans-world identity) | the same individual, named across a change of universe | A **line of identity carried across a legal sheet-to-sheet transition.** Trans-world identity becomes identity-across-the-DAG — the very invariant the [linear↔graphical correspondence](LINEAR_GRAPHICAL_CORRESPONDENCE.md) keeps inerrant. |

The third row is the crux, and it is where the diachronic reading earns its keep
rather than merely asserting it. The hardest part of modal *notation* — the part
that drove Peirce through revision after revision because the broken cut "couldn't
handle iteration" — is not a marking problem at all. It is an **identity-across-
worlds** problem, and identity carried faithfully across a change of context is
the one thing Arisbe's architecture exists to guarantee. The notation's hardest
case is Arisbe's home ground.

---

## 3. Why this is complete, and why it is clearer

**Complete — for the propositional fragment, and that is the right scope.** By the
standard translation, *basic propositional* modal logic is a *fragment* of
first-order logic — and van Benthem's theorem pins down which fragment: it is
exactly the **bisimulation-invariant fragment of FOL**. Two consequences follow.
First, there is no expressive demand *propositional* □/◇ can make that
Beta-over-the-drawn-frame cannot already meet — so no modal mark is needed to fill
a gap, because there is no gap. Second, Beta over the frame is *strictly more
expressive* than the propositional modal language. The expressivity inclusion runs
the safe direction.

*An adversarial examination (see [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md)
§4 and [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md)) forced one
correction here, and it is important: van Benthem's theorem is about the
**propositional** modal language. The moment §2's crux carries a **line of
identity across a transition**, we are in **first-order modal logic with identity**
(QML), which that theorem does not govern. So the "no gap" guarantee is genuine for
the propositional fragment and does **not** transfer automatically to the
with-identity case the §2 construction features. The architectural claim — that no
new modal **mark** is needed — is untouched (a line across the DAG is still no
broken cut, no tincture). But the carried line makes substantive, contested
commitments — the **necessity of identity**, and with a fixed carried domain the
**converse Barcan formula** — that depend on a **domain policy** (constant vs.
varying/expanding) we owe and here flag as undischarged, rather than treating
trans-world identity as unproblematic "home ground." The honest claim is therefore
**adequacy, not unconditional completeness.***

**Clearer.** The operator achieves its concision by *hiding* the frame: its
semantics is a quantification deferred to a metalanguage the reader must supply.
The diachronic drawing instead **exhibits** the frame — the worlds are sheets you
can open, the accessibility is a transition you can replay. For a system whose
entire purpose is the *analysis of reasoning* — Peirce's "moving picture of
thought," made examinable — exhibiting the frame is not a cost but the whole
point. What the operator compresses into an opaque glyph, Arisbe spreads into a
structure you can walk.

---

## 4. Honest limits

The claim is definitive *because* it is bounded. Three limits, stated plainly:

1. **First-order-definable frames only.** The standard translation captures the
   modal logics whose frame conditions are first-order definable — K, T, S4, S5.
   Genuinely non-first-order conditions are not first-order expressible and so fall
   outside the construction — and these are **not** exotic: GL/provability
   (Löb well-foundedness), common-knowledge (transitive closure), and
   temporal-liveness modalities are everyday, and the §1 provability/trajectory
   reading is itself GL-shaped — *gestured at* there, not constructed. They are
   honestly reclassified as part of the **§7 second-order residue**, not claimed.
   Counterfactuals (Lewis/Stalnaker sphere semantics, not a single accessibility
   relation R) and the object-language **actuality operator @** (forgone by
   principle — [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) floor #6 forbids
   any mark bearing actuality) are likewise not served. "Modality without Gamma" is
   thus narrower than total, and we flag the boundary rather than paper over it.

2. **Succinctness traded for explicitness.** A modal formula can be exponentially
   more compact than its first-order translation. Arisbe deliberately accepts the
   verbosity to gain a *drawn* frame. This is a real trade, named here, not hidden
   — and §5 shows how much of the lost concision can be recovered safely.

3. **Adequacy argument, not a mechanized theorem.** This document gives an
   *adequacy* argument grounded in the standard translation; it is not a formal
   proof carried out in Arisbe's code. The construction is standard and the
   conclusion is, we judge, secure — but its status is "well-grounded doctrine,"
   not "verified by the test suite."

---

## 5. Abbreviation as concision, not load — a subject for further development

> *Rendered without every detail, but with indicators that more detail exists.*

The succinctness traded away in §4.2 has a principled answer, and it is the right
frame for any future temptation toward a modal-looking glyph. The analogy is a
**map**: a good map omits almost everything, yet marks where the omitted detail
lives and lets you zoom to it. The governing distinction is between a mark that is
**load-bearing** (it asserts content, or — forbidden — bears actuality) and a mark
that is merely **concision-bearing** (it abbreviates structure that genuinely
exists elsewhere and is *mechanically recoverable*).

Arisbe already ships the prototype of exactly this, and it is governed, not
freehand:

- The **adaptive-scope overview** collapses a cut to a placeholder bearing
  *form-only* counts ("rel / cuts / lines · ⇢ N enter") with a "＋ expand"
  affordance — "more detail exists here," *indicated, never asserted*
  ([`src/overview_projection.py`](../src/overview_projection.py); the Organon
  overview lens).
- The **definition-node / φ-hole fold–unfold** does the same locally and
  reversibly ([`src/definitions.py`](../src/definitions.py), `expand_at` / `fold`;
  see [DEFINITION_NODE.md](DEFINITION_NODE.md)).
- The **faithfulness guarantee** is already formalized as the *expansion law* in
  overview attestation: the empty collapse is identical to ordinary
  `attest_correspondence`, and full expansion is the real §3.3 picture
  (`attest_overview` in
  [`src/correspondence_attestation.py`](../src/correspondence_attestation.py)). The
  abbreviation is licit *because* it expands to the attested truth.

So there *is* a door through which a broken-cut-ish or tincture-ish symbol could
one day be readmitted — but only as a **map symbol**: a non-load-bearing
indicator that *the diachronic/FOL detail exists here* and is expansible on
demand, gated by an expansion law that forces it to unfold to the real frame. It
would recover concision without surrendering the drawn frame, and it would bear no
actuality (MANIFEST floor #6). **This is a horizon, not a present build** — recorded
here so that if the temptation returns, it returns through the one gate that keeps
it honest.

---

## 6. Second-order content is displayed as history, not marked

Before naming the frontier, one more thing the diachronic reading discharges. The
*meta-judgments* a reasoning community makes — "this qualifies as an addition to
M," "the dialogists agreed that branch didn't happen," "take a new stand with
respect to P" — are not modal, and they are not ineliminable-as-marks either. They
are **diagrammed as the trajectory itself**: thought about thought made
extensional. You do not predicate "they chose X" with a higher-order operator; you
exhibit the choosing as the transition from sheet to sheet.

The condition that makes a sequence a *record of choosing* rather than an arbitrary
succession is that each step is **legible as a legal move** — recoverable as
permissible under the rules at a point where enclosure-parity assigned that
selection to that player. Arisbe enforces exactly this:
[`RuleInteraction`](../src/rule_interaction.py) makes each step sound-by-construction,
and chain replay ([`proof_authoring.replay_step`](../src/proof_authoring.py))
lets a later reader re-walk the history and recover the same structure. The
markless demonstration is self-sufficient in the sheets *plus the shared game* —
which is what a replay re-supplies. The Agon `Play` record is the dialogical case
of the same thing.

---

## 7. The real frontier: second-order logic about the graphs themselves

Keep the two apart, because conflating them is what made Gamma look like one
problem when it was two:

- **Modality quantifies over *worlds*** — first-order over a frame. Done, by §1–§3.
- **Second-order *proper* quantifies over, or predicates of, the *graphs and
  models themselves*** — graphs of graphs, abstraction, the predication of
  qualities, "every graph true in M remains revisable." This does not reduce to a
  choice of universe or an adjustment of stance; it ranges over the signs.

This second thing is genuinely higher-order and genuinely ineliminable, and it is
"what the harder Gamma examples were always actually about." Its *meta-judgment*
slice is display-as-history (§6); the rest is the live research horizon. Arisbe
already has its toe in the water — the φ-hole / schema node
([`src/schema.py`](../src/schema.py),
[SCHEMA_HOLE_CORRESPONDENCE.md](SCHEMA_HOLE_CORRESPONDENCE.md)) keeps "a graph with
a place for a graph" strictly metalinguistic, and the math track
(Separation/Replacement schemata, the graph-with-holes) is where it grows. That is
where the next real work lies — **not** in a modal mark.

---

## 8. Coda: fact, and the ground no sheet encloses

Two final placements, recorded *alongside* Peirce's framing rather than in place
of it (see the reconciliations in MANIFEST_AND_MEANING.md and CHAIN_OF_SEMIOSIS.md).

**Fact** is not a glow in the object nor a counter we award. It is the **defeasible
status of the last-standing trajectory** — the line that has not been pruned —
*conferred* by the enacted history yet *answerable* beyond it, free to be demoted on
better information or changed need. Conferred-yet-answerable is the needle the whole
account threads, and the diachronic framing threads it without either horn (MANIFEST
floor #4; realized in part by [`src/liveness.py`](../src/liveness.py)). "Free to
demote" even has a formal home in Alpha — model revision is INS on the negative-context
antecedent of the scroll `cut[ M cut[G] ]` — see
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §5.

And the ground. The conversation stakes a **third position** on what "demote"
answers to. Within any chosen game, the modal vocabulary really is just bookkeeping
over legal trajectories — *eliminative about the would-be*. But the **blank sheet**
— the one separation Arisbe cannot draw, the membrane between the whole sheet and
the world it is *of* (MANIFEST, "The membrane") — is not another would-be and not a
bigger model. It is *realist about the ground*: the un-enclosable containment any
game whatsoever presupposes, shown by structure (every graph stands on a sheet it
cannot enclose) and never asserted as a graph. So demotion answers neither to a
future consensus nor to a standing fact, but to *that* — a reality that can overturn
any standing without ever being a standing itself: reality is **upstream and
around**, the condition for there being play. *The last-one-standing is always
standing on something it didn't lay down.*

*Examined (2026-06-19; [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) §2,
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md)). The "third position" is
held with its distance from Peirce now precisely measured, not overstated. What is
**secured**: the eliminative/negative orientation — demotion is driven from behind,
by what overturns a standing (Peirce's own* Fixation of Belief *engine), and the
ground so encountered is cognizable* in its effects*, hence not the incognizable
thing-in-itself. What is **at parity, not won**: the disagreement is no longer
"inquiry never converges" (which dissolved into sophisticated Peirce) but a single
meta-level question — whether the corrected sequence converges on a real
*toward-which* (Peirce) or only ever overturns with no privileged terminus (the
author). Reserving "reality" for the upstream ground is a choice of where to point
the word, **held at parity, not a refutation**; the joint (whether the regress of
standards closes) is undischarged on both sides. We keep the picture and own the
debt.*

---

*Companion to [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md),
[UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md), and
[LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md). Source:
[references/EG-modality-conversation.pdf](references/EG-modality-conversation.pdf).*

**Created**: 2026-06-18
