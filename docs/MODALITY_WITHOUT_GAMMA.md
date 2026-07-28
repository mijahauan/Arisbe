# Modality without Gamma

*The diachronic sheet, the standard translation, and why the real frontier
is second-order logic about the graphs.*

*A philosophy-spine companion to
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the ground beneath the
chain) and [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the chain itself).
Distilled from a 2026-06 conversation, archived at
[references/EG-modality-conversation.pdf](references/EG-modality-conversation.pdf).*

*The claim now stands **demonstrated on Peirce's own attempted figures**. The broken
cut, the tinctured would-be, the book of separate sheets all live in the corpus as
exemplars, readable through the Organon lenses:
[GAMMA_DEMONSTRATIONS.md](GAMMA_DEMONSTRATIONS.md) (2026-07-04).*

*Gamma has an **other** half, genuinely second-order — graphs about graphs,
abstraction — which this document names as the real frontier. Its map lives in
[SECOND_ORDER_FRONTIER.md](SECOND_ORDER_FRONTIER.md) (2026-07-08): how far Peirce leads,
where we take other guides, and the rule that the crossing must stay a **drawing**.*

---

## The thesis, flatly

**Gamma, conceived as a *modal* extension, poses no problem Arisbe needs to
solve.** Beta Existential Graphs in their full Arisbe-*diachronic* form — the
sheet, plus the rule-governed history of sheets, plus the corpus of universes —
express the work of the modern □ and ◇ *with no new modal mark*, and express it
with *better clarity*, because the apparatus those operators quietly presuppose
stands **drawn** rather than hidden in a metalanguage. *(Scope, post-examination — see §3
and [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) §4: the "expresses
everything □/◇ express, no gap" guarantee is exact for **propositional** modal
logic via van Benthem; the first-order-with-identity modality the §2 construction
features lies beyond that theorem and carries its own declared commitments. The
load-bearing claim — **no new mark** — is untouched; the unconditional
completeness boast is scoped down to adequacy.)* Peirce reached for the broken cut and then
the [tinctures](GLOSSARY.md#tincture) (Peirce's Gamma colourings) to carry modality on a single static sheet; the diachronic
structure Arisbe already maintains and attests carries the *modal* load they were
meant to bear. To say "without remainder" would claim too much; the ledger below
sets out honestly what does and does not get carried ("What not using Gamma costs").

**One thing needs saying plainly up front, for it carries the heart of the credit owed.**
"No modal *mark* needed" amounts to **no** verdict that Gamma is worthless or unworkable.
Peirce's broken cut stands *rehabilitated*. Zeman (1964) connected it to S4/S5, and
Ma & Pietarinen (2018) give sound-and-complete graphical (broken-cut) calculi for a
family of fifteen normal modal logics — Peirce's own apparatus, needing only three
added rules. Arisbe's choice to draw the frame instead stands as a **defensible
architectural decision**, not a refutation of Gamma; it forgoes a real virtue the
broken cut keeps (the on-sheet topological perspicuity of the modal operator itself),
and we name that cost rather than hide it — see "What Gamma keeps," below.

This does not amount to a stance dressed as a result. It rides on a settled fact
of modal model theory, the **standard translation** of modal logic into
first-order logic (van Benthem), and it leaves a precise residue. The residue
proves **not** modal and **not** a tincture. It consists of *second-order logic
about the graphs themselves*, and that — not Gamma — marks the real frontier.

---

## 1. The construction: a modal operator is a drawn quantifier over a frame

A modal operator carries no primitive content. It abbreviates quantification
over a **Kripke frame** — a set of worlds *W*, an accessibility relation *R*
between them, and a valuation. The **standard translation** ST makes this
explicit, sending a modal formula to a first-order formula with a free
world-variable:

> ST(□φ, w)  =  ∀w′ ( R(w, w′) → ST(φ, w′) )
> ST(◇φ, w)  =  ∃w′ ( R(w, w′) ∧ ST(φ, w′) )

The operators vanish into ordinary ∀ and ∃ over the frame. And ∀/∃ over a
relation is exactly what Beta Existential Graph ([EG](GLOSSARY.md#eg)) draws. So the one thing standing between Beta
EG and modal expressivity remains *a representation of the frame*. Arisbe's
diachronic architecture supplies precisely that, natively, in two
readings:

- **The trajectory reading** (provability / derivability modality). Take the worlds as
  **sheets** — the immutable Existential Graph Instance ([EGI](GLOSSARY.md#egi)) states — and *R* as the **legal-transition relation**
  of the derivation directed acyclic graph ([DAG](GLOSSARY.md#dag)). Then "◇φ" reads "some legal trajectory [scribes](GLOSSARY.md#scribe) φ" and "□φ"
  reads "every legal trajectory scribes φ." This gives the diachronic gloss the
  conversation reaches by a different road: *possibility is the **branching** of
  legal trajectories, necessity is their **convergence**, and the only necessity
  is to follow the rules.* That sentence **is** the standard translation under the
  legal-transition frame. And Arisbe already builds this frame as an object:
  [`src/egi_transformation_history.py`](../src/egi_transformation_history.py) (the
  DAG of states and steps),
  [`src/universe_of_discourse.py`](../src/universe_of_discourse.py) (the diachronic
  entity), surfaced as the
  [derivation-DAG lens](../src/web_viewer/js/derivation-dag-lens.js).

- **The alethic reading** (□ = true in all accessible worlds). Take the worlds as the
  corpus's several **Universes of Discourse ([UoDs](GLOSSARY.md#uod)) / models M**, and *R* as an accessibility relation drawn
  **among** them. The corpus already forms a *library of universes*, mutually
  inconsistent without contradiction (MANIFEST [floor](GLOSSARY.md#floor) (the baseline that may not be gone under) #5). Modal force becomes the
  [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game's quantification over the choice of M. The interpretation
  register already performs that quantification (`/agon/where-it-holds`, the inverse pivot across
  models). The conversation names this lineage outright: *the dialogical
  relativization to M does the modal work the older syntactic operators reached
  for, the same way Kripke/Hintikka relativization to worlds does.*

Either way, **□ and ◇ become Beta quantifiers over a frame that lies on the sheet**,
not operators whose meaning lives off-stage.

---

## 2. Carrying exactly the load Peirce gave the broken cut and the tinctures

Peirce's Gamma devices attempted to make a *single static sheet* bear
modality. Each maps cleanly onto the drawn frame:

| Peirce's device | What it was for | Carried in Arisbe by |
|---|---|---|
| **Broken cut** | ◇ / □ on the sheet | ∃ / ∀ over **accessible sheets**, with the accessibility *visible* (the trajectory branch, or the relation among M's). |
| **Tinctures** (the provinces / universes) | "which universe this region belongs to" | The **explicit identity of the sheet/M** a region inhabits. The corpus *is* the library of tinctured universes — made first-class as separate UoDs, not as colours on one sheet. |
| **The case Peirce kept failing at** — *iterated* broken cuts, and **lines of identity crossing tincture boundaries** (trans-world identity) | the same individual, named across a change of universe | A **line of identity carried across a legal sheet-to-sheet transition.** Trans-world identity becomes identity-across-the-DAG — the very invariant the [linear↔graphical correspondence](LINEAR_GRAPHICAL_CORRESPONDENCE.md) keeps inerrant. |

The third row carries the crux, and there the diachronic reading earns its keep
rather than merely asserting it. Be precise about Peirce's actual difficulty, for it
often gets loosely reported: Peirce did not find the broken cut *unworkable* — he left
its **iteration rule open**. Reading his two broken-cut rules at CP 4.516, Zeman
notes that one "begs for study," the open question being whether to permit iterating
a graph *across* a broken cut and under what restriction; and in MS R 467 Peirce
records his own doubt about *double* broken cuts (whether ◇□g and □◇g are
interderivable — "It is only because I have not sufficiently reflected upon the
subject that I can have any doubt"). The different restrictions on that one rule
separate S4 from S5 exactly — which explains why Zeman had to build several systems,
and why Ma & Pietarinen (2018) could later *settle* the matter with sound-complete
graphical calculi (their Remark 1 even gives the explicit counterexamples showing
the unrestricted rule is unsound). So the broken cut emerges rehabilitated, not defeated.

Arisbe's diachronic reading takes a different road to the *same* underlying object,
because the genuinely hard part lies not in the modal mark but in the **identity-across-
worlds** problem (a line of identity crossing a change of universe; Peirce coined a
"special relation" for it in MS 490 and never reduced it to the ordinary
line-of-identity apparatus). Identity carried faithfully across a change of context
remains the one thing Arisbe's architecture exists to guarantee, so the notation's
hardest case lands on Arisbe's home ground. This gives a reason to *prefer* the drawn
frame for Arisbe's purposes — not evidence that the broken cut cannot be made to work.

---

## 3. Why this is complete, and why it is clearer

**Complete — for the propositional fragment, and that is the right scope.** By the
standard translation, *basic propositional* modal logic forms a *fragment* of
first-order logic, and van Benthem's theorem pins down which fragment: exactly
the **bisimulation-invariant fragment of FOL**. Two consequences follow.
First, *propositional* □/◇ can make no expressive demand that
Beta-over-the-drawn-frame cannot already meet — so no modal mark needs to fill
a gap, because no gap exists. Second, Beta over the frame proves *strictly more
expressive* than the propositional modal language. The expressivity inclusion runs
the safe direction.

*An adversarial examination (see [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md)
§4 and [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md)) forced one
correction here, and it matters: van Benthem's theorem concerns the
**propositional** modal language. The moment §2's crux carries a **line of
identity across a transition**, we stand in **first-order modal logic with identity**
(QML), which that theorem does not govern. So the "no gap" guarantee remains genuine for
the propositional fragment and does **not** transfer automatically to the
with-identity case the §2 construction features. The architectural claim — that no
new modal **mark** is needed — stands untouched (a line across the DAG remains no
broken cut, no tincture). But the carried line makes substantive, contested
commitments — the **necessity of identity**, and with a fixed carried domain the
**converse Barcan formula** — that depend on a **domain policy** (constant vs.
varying/expanding) we owe and here flag as undischarged, rather than treating
trans-world identity as unproblematic "home ground." The honest claim is therefore
**adequacy, not unconditional completeness.***

**Clearer.** The operator achieves its concision by *hiding* the frame: its
semantics amounts to a quantification deferred to a metalanguage the reader must supply.
The diachronic drawing instead **exhibits** the frame. The worlds become sheets you
can open; the accessibility, a transition you can replay. For a system whose
entire purpose lies in the *analysis of reasoning* — Peirce's "moving picture of
thought," made examinable — exhibiting the frame counts not as a cost but as the whole
point. What the operator compresses into an opaque glyph, Arisbe spreads into a
structure you can walk.

---

## What not using Gamma costs — the expressibility ledger

*(Added 2026-06-27, at the author's request: an honest accounting of what the
no-Gamma stance forgoes, distinguishing real expressibility gaps from mere
perspicuity costs. The ledger splits in three.)*

**(1) No object-language loss for *propositional* modality.** By **van Benthem's
characterization theorem**, propositional modal logic amounts to *exactly* the
bisimulation-invariant fragment of first-order logic. So the propositional modal
object-language can state no proposition that Beta-over-the-drawn-frame cannot —
and the frame can state strictly more (count successors, assert irreflexivity ¬Rxx),
which simply are not modal facts. Here the no-Gamma stance loses **nothing of
expressive power**; it trades succinctness and perspicuity (point 3).

**(2) Genuine gaps, beyond the standard translation.** Three things Gamma reached
that a *propositional* standard translation does **not** capture. Arisbe does not
get them "for free" from §1, and routes them honestly to the §7 frontier instead:

- **Second-order / higher-order content** — quantifying over qualities, relations,
  and propositions. Even propositional modal *frame*-validity "implicitly involves a
  higher-order quantification over propositions" — "even propositional modal logic is
  fundamentally second-order in nature" (Goldblatt). Peirce's Gamma reached here on
  purpose (Roberts: "second (and higher) order functional calculi"; the "logic of
  potentials"). **A real gap** — and exactly what §7 names as the genuine frontier.
- **Metalinguistic graphs-of-graphs** — Gamma as a "logic of second intentions,"
  reasoning *about* graphs with graphs. Orthogonal to any object-level FOL-over-*R*
  translation; Arisbe keeps it strictly metalinguistic in the φ-hole / schema node
  (§7), never as a modal mark. (Sowa notes even ISO Common Logic needs its IKL
  extension to reach the relevant constructs.) **A real gap.**
- **Non-first-order-definable frame conditions** — GL/Löb (converse
  well-foundedness), McKinsey, common-knowledge (transitive closure). A single
  explicit *R* in FOL cannot axiomatize these either, so this is a limit of
  first-order frame definability *in general* — shared by the standard-translation
  route, **not** a unique Gamma surplus. Already flagged in §4.1.

**(3) The perspicuity / succinctness / decidability cost.** Even where no
object-language loss occurs, the standard translation carries a cost, and the cost
lands precisely where diagrams exist to spare us:

- **Blow-up** — each modal operator introduces a new world-variable, so deep modal
  nesting becomes deep quantifier alternation (Vardi 1996); a modal formula can be
  exponentially more compact than its translation (§4.2).
- **Loss of the local/internal view** — modal languages give "an internal, local
  perspective on relational structures," evaluated "at a state" (Blackburn–de
  Rijke–Venema); the FOL image dissolves this into global prefixes. And that very
  locality (the tree-model property), Vardi points out, is *why* modal logic is robustly
  decidable — the translation buries the thing that makes it tractable and surveyable.
- **The honest two-sidedness.** Arisbe gives up the operator's on-sheet compression,
  but by *drawing the frame* it keeps a different surveyability — worlds you can open,
  accessibility you can replay. It trades one "free ride" (the operator's locality)
  for another (the examinable, attested frame). Neither proves strictly better; the
  choice remains purposive, not a free lunch.

**Tinctures — the apparent big loss, mostly recovered.** Peirce's tinctures (1906
*Prolegomena*: twelve tinctures in three Modes — Color / Fur / Metal for Possibility /
Intention / Actuality) mark *kinds* of universe, not one accessibility relation. But
marking kinds of modality is exactly **multimodal logic** — an indexed family *Rᵢ* —
which still has a standard translation (FOL with several binary relations). So most of
the tincture apparatus amounts to multimodal convenience the corpus's library of UoDs
already supplies; the irreducible residue lies only where it touches (a) the second-order
content and (b) cross-world individual identity — i.e. it folds back into the genuine
gaps above, **not** into a need for a colour mark.

---

## What Gamma keeps: the broken cut, rehabilitated (Zeman; Ma & Pietarinen)

*(Added 2026-06-27. The credit this document most owes — and it cuts against an easy
reading of the thesis, so we state it fully rather than bury it.)*

**What they prove.** **Zeman (1964)** first connected Peirce's broken-cut graphs to
the modern modal logics S4 and S5. **Ma & Pietarinen (2018)**, "Gamma graph calculi
for modal logics" (*Synthese* 195(8); open-access companion "Graphical Sequent
Calculi for Modal Logics," EPTCS 243, 2017), establish **sound and complete**
graphical (broken-cut) calculi for a family of **fifteen** normal modal logics — base
**Kg** plus extensions through D, T, 4, B, 5, up to **S4g** and **S5g** — with
cut-elimination. *(Caveat owed in turn: their completeness is **algebraic** — with
respect to modal algebras — not Kripke/relational; do not overstate it as
frame-completeness.)* The rehabilitation is concrete: the rules "arise systematically
from Peirce's presentation of broken-cut gamma graphs… **Only (DMN), (B) and (5) are
new**" — and those three are precisely the ones Peirce himself resisted, given his
epistemic (S5-rejecting) reading of the broken cut.

**The diagrammatic advantages they name** — virtues the standard translation
discards, quoted precisely:

- **Position and polarity are read directly off the cut topology** — "the notion of a
  position… is made explicit in graphical logic. This makes such graphical calculi the
  natural home for deep inference." Scope and negation stand *in the picture*, not
  reconstructed from a quantifier prefix.
- **No negation normal form, and no labels** — "graphs need not assume negation normal
  form… Labels are likewise not needed," an advantage over symbolic deep-inference
  systems.
- **The ambient sheet absorbs structural bookkeeping for free** — because the sheet is
  "continuous, compact, open and non-oriented," the permutation/associativity
  equalities "follow from the basic properties of the space and therefore need no
  separate statement." *(This is the nearest thing in their text to a "free ride" —
  but note they do **not** use the terms "free ride," "surveyability," or "continuous
  deformation"; those are not theirs to cite.)*

**Why this matters for the thesis — allies, not opponents.** These advantages support
Arisbe's *deeper* commitment (keep modality diagrammatic and examinable, never buried
in a metalanguage), they do not undercut it. The genuine tension runs narrower and
deserves exact statement: Ma & Pietarinen keep the modal operator's structure **on one
sheet**, so the *form* of necessity is itself surveyable in the topology of the cut;
Arisbe spreads modality across the **diachronic DAG**, so the *frame* is surveyable
but the operator's on-sheet compression is gone. Each keeps a different perspicuity.
Arisbe takes its route because its central guarantee — identity carried inerrantly
across a change of context — is exactly the trans-world-identity problem Peirce never
reduced; but the choice **forgoes the broken cut's on-sheet virtue**, and that cost is
real, made vivid precisely *by* Ma & Pietarinen's result. The defensible claim reads
"no modal *mark* needed for Arisbe's purposes," not "Gamma is dispensable for logic."

**A caution about iconicity, which sits under all of this.** The strong claim that
diagrams are iconic or perspicuous "in senses symbolic notations are not" stands
**contested — by Pietarinen himself** ("Two Dogmas of Diagrammatic Reasoning," 2017).
Arisbe rests on the deflated, defensible claim, in Peirce's own terms: the
graphs aim at "the closest correspondence with the process of reasoning," as "moving
pictures of thought" — examinability, not a metaphysical privilege of the visual.

---

## 4. Honest limits

The claim stands definitive *because* it stays bounded. Three limits, stated plainly:

1. **First-order-definable frames only.** The standard translation captures the
   modal logics whose frame conditions are first-order definable — K, T, S4, S5.
   Genuinely non-first-order conditions are not first-order expressible and so fall
   outside the construction — and these are **not** exotic: GL/provability
   (Löb well-foundedness), common-knowledge (transitive closure), and
   temporal-liveness modalities are everyday, and the §1 provability/trajectory
   reading is itself GL-shaped — *gestured at* there, not constructed. We reclassify
   them honestly as part of the **§7 second-order residue**, not claimed.
   Counterfactuals (Lewis/Stalnaker sphere semantics, not a single accessibility
   relation R) and the object-language **actuality operator @** (forgone by
   principle — [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) floor #6 forbids
   any mark bearing actuality) likewise go unserved. "Modality without Gamma" thus
   runs narrower than total, and we flag the boundary rather than paper over it.

2. **Succinctness traded for explicitness.** A modal formula can be exponentially
   more compact than its first-order translation. Arisbe deliberately accepts the
   verbosity to gain a *drawn* frame. The trade is real, named here rather than
   hidden — and §5 shows how much of the lost concision can be recovered safely.

3. **Adequacy argument, not a mechanized theorem.** This document gives an
   *adequacy* argument grounded in the standard translation; it does not amount to
   a formal proof carried out in Arisbe's code. The construction is standard and the
   conclusion, we judge, stands secure — but its status remains "well-grounded doctrine,"
   not "verified by the test suite."

---

## 5. Abbreviation as concision, not load — a subject for further development

> *Rendered without every detail, but with indicators that more detail exists.*

The succinctness traded away in §4.2 has a principled answer, and it gives the right
frame for any future temptation toward a modal-looking glyph. Think of a
**map**: a good map omits almost everything, yet marks where the omitted detail
lives and lets you zoom to it. The governing distinction separates a
**load-bearing** mark (it asserts content, or — forbidden — bears actuality) from a
merely **concision-bearing** mark (it abbreviates structure that genuinely
exists elsewhere and remains *mechanically recoverable*).

Arisbe already ships the prototype of exactly this, and it comes governed, not
freehand:

- The **adaptive-scope overview** collapses a cut to a placeholder bearing
  *form-only* counts ("rel / cuts / lines · ⇢ N enter") with a "＋ expand"
  affordance — "more detail exists here," *indicated, never asserted*
  ([`src/overview_projection.py`](../src/overview_projection.py); the Organon
  overview lens).
- The **definition-node / φ-hole fold–unfold** does the same locally and
  reversibly ([`src/definitions.py`](../src/definitions.py), `expand_at` / `fold`;
  see [DEFINITION_NODE.md](DEFINITION_NODE.md)).
- The **faithfulness guarantee** already stands formalized as the *expansion law* in
  overview attestation: the empty collapse matches ordinary
  `attest_correspondence` exactly, and full expansion gives the real correspondence check (§3.3) picture
  (`attest_overview` in
  [`src/correspondence_attestation.py`](../src/correspondence_attestation.py)). The
  abbreviation counts as licit *because* it expands to the attested truth.

So a door *does* exist through which a broken-cut-ish or tincture-ish symbol could
one day win readmission — but only as a **map symbol**: a non-load-bearing
indicator that *the diachronic/FOL detail exists here*, expansible on
demand, gated by an expansion law that forces it to unfold to the real frame. It
would recover concision without surrendering the drawn frame, and it would bear no
actuality (MANIFEST floor #6). **This names a [horizon](GLOSSARY.md#horizon), not a present build** — recorded
here so that if the temptation returns, it returns through the one gate that keeps
it honest.

---

## 6. Second-order content is displayed as history, not marked

Before naming the frontier, one more thing the diachronic reading discharges. The
*meta-judgments* a reasoning community makes — "this qualifies as an addition to
M," "the dialogists agreed that branch didn't happen," "take a new stand with
respect to P" — prove not modal, and not ineliminable-as-marks either. They
get **diagrammed as the trajectory itself**: thought about thought made
extensional. You do not predicate "they chose X" with a higher-order operator; you
exhibit the choosing as the transition from sheet to sheet.

What makes a sequence a *record of choosing* rather than an arbitrary
succession? Each step must stand **legible as a legal move** — recoverable as
permissible under the rules at a point where enclosure-parity assigned that
selection to that player. Arisbe enforces exactly this:
[`RuleInteraction`](../src/rule_interaction.py) makes each step sound-by-construction,
and chain replay ([`proof_authoring.replay_step`](../src/proof_authoring.py))
lets a later reader re-walk the history and recover the same structure. The
markless demonstration stands self-sufficient in the sheets *plus the shared game* —
and a replay re-supplies exactly that shared game. The Agon `Play` record gives the
dialogical case of the same thing.

---

## 7. The real frontier: second-order logic about the graphs themselves

Keep the two apart; conflating them made Gamma look like one
problem when it was two:

- **Modality quantifies over *worlds*** — first-order over a frame. Done, by §1–§3.
- **Second-order *proper* quantifies over, or predicates of, the *graphs and
  models themselves*** — graphs of graphs, abstraction, the predication of
  qualities, "every graph true in M remains revisable." This does not reduce to a
  choice of universe or an adjustment of stance; it ranges over the signs.

This second thing runs genuinely higher-order and genuinely ineliminable, and it is
"what the harder Gamma examples were always actually about." Its *meta-judgment*
slice resolves into display as history (§6); the rest remains the live research
horizon. Arisbe already has its toe in the water: the φ-hole / schema node
([`src/schema.py`](../src/schema.py),
[SCHEMA_HOLE_CORRESPONDENCE.md](SCHEMA_HOLE_CORRESPONDENCE.md)) keeps "a graph with
a place for a graph" strictly metalinguistic, and it grows in the math track
(Separation/Replacement schemata, the graph-with-holes). There the next real
work lies — **not** in a modal mark.

The trajectory reading (§1) carries distinguished ancestry worth naming. In Paul
Cohen's forcing technique, the three modal statuses of a statement about a generic
extension — necessary, contingent, impossible — come *derived* from first-order
forcing relations plus the order structure of conditions, never primitively
asserted; and the condition poset takes exactly the shape of Arisbe's derivation DAG.
The dev memo [FORCING_AND_THE_GAMMA_CROSSING.md](FORCING_AND_THE_GAMMA_CROSSING.md)
records the full dictionary, and the modern-landscape survey
[SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md](SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md)
places this chapter's doctrine — modality as a derived reading, the crossing routed
through names of graphs — within the semantics and paradox-control debates of logic
since Peirce.

---

## 8. Coda: fact, and the ground no sheet encloses

Two final placements, recorded *alongside* Peirce's framing rather than in place
of it (see the reconciliations in MANIFEST_AND_MEANING.md and CHAIN_OF_SEMIOSIS.md).

**Fact** names neither a glow in the object nor a counter we award. It names the
**defeasible status of the last-standing trajectory** — the line that has not been pruned —
*conferred* by the enacted history yet *answerable* beyond it, free to be demoted on
better information or changed need. Conferred-yet-answerable names the needle the whole
account threads, and the diachronic framing threads it without either horn (MANIFEST
floor #4; realized in part by [`src/liveness.py`](../src/liveness.py)). "Free to
demote" even has a formal home in Alpha — model revision is INS on the negative-context
antecedent of the [scroll](GLOSSARY.md#scroll) (a nested double cut — "if … then") `cut[ M cut[G] ]` — see
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §5.

And the ground. The conversation stakes a **third position** on what "demote"
answers to. Within any chosen game, the modal vocabulary really amounts to bookkeeping
over legal trajectories — *eliminative about the would-be*. But the **blank sheet**
— the one separation Arisbe cannot draw, the [membrane](GLOSSARY.md#membrane) (the boundary where the sheet meets the world) between the whole sheet and
the world it is *of* (MANIFEST, "The membrane") — makes neither another would-be nor a
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

## References

The modal model theory and the Peirce scholarship this document relies on. Arisbe
*uses* these results; it does not originate them.

- **van Benthem, J.** *Modal Correspondence Theory* (PhD, 1976) and *Modal Logic and
  Classical Logic* (1983) — the standard translation and the characterization theorem
  (modal logic = the bisimulation-invariant fragment of FOL). The basis of §1 and §3.
- **Goldblatt, R.** "Mathematical Modal Logic: A View of its Evolution" / SEP *Modern
  Origins of Modal Logic* — frame-validity as implicitly higher-order ("even
  propositional modal logic is fundamentally second-order in nature"). Ledger point 2.
- **Vardi, M.** "Why Is Modal Logic So Robustly Decidable?" (DIMACS, 1996/97) — the
  locality / tree-model property the standard translation buries. Ledger point 3.
- **Blackburn, de Rijke & Venema.** *Modal Logic* (CUP, 2001) — the internal, local
  perspective of modal languages. Ledger point 3.
- **Zeman, J. J.** *The Graphical Logic of C. S. Peirce* (PhD, 1964) — the broken cut
  ↔ S4/S5 correspondence, and the open iteration rule at CP 4.516.
- **Ma, M. & Pietarinen, A.-V.** "Gamma graph calculi for modal logics," *Synthese*
  195(8):3621–3650 (2018); open companion "Graphical Sequent Calculi for Modal
  Logics," EPTCS 243 (2017), 91–103 — sound-and-complete broken-cut calculi for
  fifteen normal modal logics; the diagrammatic advantages; the broken-cut
  rehabilitation ("only (DMN), (B), (5) are new"). The principal credit of this doc.
- **Roberts, D. D.** *The Existential Graphs of Charles S. Peirce* (1973), esp. p. 64
  — Gamma as second/higher-order + abstraction + graphs-of-graphs; the unfinished
  state of Gamma.
- **Peirce, C. S.** "Prolegomena to an Apology for Pragmaticism," *The Monist* 16
  (1906), CP 4.530ff. — the system of tinctures (twelve tinctures, three Modes); MS R
  467 and MS 490 (the broken-cut doubts; the trans-world "special relation").
- **Pietarinen, A.-V.** "Two Dogmas of Diagrammatic Reasoning" (2017) — the *internal*
  critique of strong iconicity; cited for balance. Sowa, *From Existential Graphs to
  Conceptual Graphs* — the EG/Common-Logic interchange and IKL note.

A consolidated cross-project prior-art ledger lives in
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md).

---

*Companion to [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md),
[UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md), and
[LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md). Source:
[references/EG-modality-conversation.pdf](references/EG-modality-conversation.pdf).*

**Created**: 2026-06-18 · **Credits + expressibility ledger added**: 2026-06-27
