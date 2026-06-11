# Arisbe by Persona: What You Can Do Now, and When It Is Complete

*An introduction for people who have never heard of Arisbe — told through the
people who might use it.*

**Status**: active development · **Drafted**: 2026-06-11

---

## Before the personas: what Arisbe is for

Charles Sanders Peirce called his Existential Graphs "moving pictures of
thought." He meant that literally. A graph is not a diagram *about* a
proposition the way a bar chart is a picture about some numbers; the graph
**is** the proposition, drawn — a sign you can reason *in*, not merely look at.
To assert something is to scribe it on the sheet; to prove something is to
transform the picture by rules that never let it say something false; to ask
what a claim means is to play it out against what you already hold true.

Arisbe is an environment for **doing logic in pictures, not pictures of logic** —
Peirce's vision made operational. You draw, transform, and contest Existential
Graphs directly, as diagrams that evolve over a course of inquiry. Frithjof
Dau's formalization is the **guarantor of correctness** underneath — the
bedrock that makes "the picture never lies" a theorem rather than a hope — but
the *aim* is Peirce's: to think in pictures, and to let the picture and the
sentence be two faces of one and the same thought.

That last clause is the engineering heart of the system, and it is worth
naming because every persona below leans on it: Arisbe holds the **drawn form**
and the **written form** of a graph in *provable correspondence*. The oval you
draw and the formula `~[ (man *x) ~[ (rich x) ~[ (happy x) ] ] ]` denote the
**same mathematical object**, and they keep denoting it across every edit,
every re-layout, every transformation, every round-trip. A runtime check
refuses to show you a picture that means something other than what it says.

The personas differ in what they bring to that sheet and what they want back
from it. What follows is, for each, *what you can do today* and *what you will
be able to do once Arisbe is complete*.

---

## The teacher

**Maria teaches introductory logic.** She is tired of students who can push
symbols around a truth table but cannot say what an implication *means*. She
wants logic to be something her students *do*, not a notation they decode.

**Now.** Maria opens **Organon**, the archive, and pulls up a worked proof —
Peirce's Law, or Barbara, or the uniqueness of a group identity — each one a
real chain of sound steps she can walk through forward and back. She drops a
small domain model in front of the class ("every mammal is warm-blooded; dogs
are mammals…") and, in the **Agon** arena, lets a student propose a claim and
watch the Endoporeutic Game *unwrap* it from the outside in until it resolves
to a theorem, a contradiction, or a genuinely new fact. The companion narrative
[ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) gives her six classroom-ready
scenarios in plain language. Nothing she shows is a static slide; every diagram
on screen is live and inspectable.

**When complete.** The game becomes fully two-sided — a proof mode for the
constructive direction and an automated opponent — so Maria can set a graph as
a *challenge* and let each student play it solo, the system refereeing every
move. Challenge mode (the next build) lets her hand a student a target graph
and grade a freehand attempt against it, with a **legible diff** that says, in
the student's own vocabulary, *exactly* where the attempt and the target part
ways — wrong scope, missing line of identity, arguments in the wrong order.
Logic class becomes a workshop with a tireless, honest referee.

---

## The student

**Amara is learning, not performing.** She does not yet trust her own
reasoning, and abstract rules slide off her. She needs to *see* why a step is
allowed and to be caught — kindly and immediately — when it is not.

**Now.** In **Ergasterion**, the workshop, Amara composes a graph by hand on a
freeform canvas: she places relations, draws cuts as ovals, drags lines of
identity between them. Then she asks the graph **"what do you say?"** — and it
reads itself back to her as a determinate sign with its linear form shown,
*or* it tells her, in the vocabulary of graphs, why it is not yet well-formed
(a line dangling into nothing, two cuts improperly overlapping). A
**Graph↔Argument** switch makes the difference between a sketch and a committed
claim unmistakable: you cannot apply a rule to an unfixed drawing, and you
cannot silently change the meaning of a fixed one. She practices the six
transformation rules and the system validates every application against the
mathematics.

**When complete.** Challenge mode turns practice into a game she can win:
reproduce *this* graph, prove *that* theorem, and get told move-by-move how
close she is. The "reading desk" lets her transcribe a graph straight out of a
textbook and have Arisbe confirm she copied it faithfully. Over a term she
accumulates not memorized facts but the *experience of having reasoned her way*
to them — which is the only thing that ever transfers.

---

## The researcher

**Kwame works across two fields that have never been formally introduced.** He
has a well-developed body of knowledge in ecology and another in economics, and
a hunch that a claim spanning both might hold. He needs to find the precise
logical seam where one domain's conclusions become another's premises.

**Now.** Kwame studies two corpora side by side in **Organon**, identifies the
concept they share, and in **Ergasterion** builds a bridging argument step by
step. He tests it in **Agon**, which *sorts* the argument for him: this part is
a theorem of the merged model, this part is a reasonable extension that needs
to be agreed, this part is an open conjecture that needs evidence the game
cannot supply. He can move a claim between EGIF, CGIF, and CLIF without loss,
import external material through a doorway that admits it honestly at **low
warrant** — parsed and attributed, never asserted true — and read the whole
provenance trail of any item in the corpus.

**When complete.** The **warrant lifecycle** becomes first-class: a graph earns
its way from *low* to *tested* by surviving Agon, and that promotion is
recorded, so a reader can always see *how much* a claim has been challenged and
by whom. Larger ontologies (OWL→CLIF→EGI from WordNet, SNOMED, Wikidata) become
the model a proposal is contested against. Research becomes a diachronic record
of inquiry — not a pile of results, but a documented history of how a community
of minds tested its way to them.

---

## The logician / mathematician

**Sofia cares about the mathematics being right, all the way down.** She is not
satisfied by a tool that draws nice diagrams; she wants the diagram and the
formal object to be the *same thing*, provably, and she wants to interrogate the
claim that they are.

**Now.** Sofia works with Dau's six transformation rules (ERA, INS, IT+, IT−,
DC+, DC−), Beta-aware — lines of identity, shared vertices across cut
boundaries — through a headless stepwise protocol that lets her construct and
replay a proof move by move with deterministic provenance. The mathematical
core has a protected test suite that must always pass; correctness is not
advisory. She can read the **correspondence invariant** as a runtime
attestation that *refuses* any (picture, proposition) pair that does not denote
one object — an operational, mechanized claim about the **iconicity** of EGs
that she can try to break by reading and running the module. Layout is treated
as a *projection* of a coordinate-free structure, so she can swap the ELK
engine for the experimental "tension" engine that draws a line of identity as a
single taut thread through the cut nest — the authentic Peircean single-line
reading.

**When complete.** Exhaustive, hypothesis-driven testing enumerates *every*
applicable site for each rule rather than one deterministic example; a
theorem-prover bridge (Coq/Lean via CLIF) connects Arisbe's diagrammatic proofs
to the wider mechanized-proof world; and the math horizon — universal
generalization via a Dau-native scaffold, fold/unfold of named definitions, a
graph-with-holes schema node — opens EGs onto real mathematics (ZFC separation,
Peirce's 1881 axioms of arithmetic). The system becomes a place to *do new
mathematics* in pictures, not only to reproduce known proofs.

---

## The physician

**Dr. Okonkwo reasons under a body of clinical knowledge** that is large,
revisable, and occasionally self-contradictory. She does not want a black box
that outputs a diagnosis; she wants to see *which* of her commitments forces a
conclusion, and to be shown — explicitly — when a new finding contradicts the
rules she has been trusting.

**Now.** She lays out the relevant clinical knowledge in **Organon**, frames a
specific question in **Ergasterion** ("given everything we hold, does this
patient need temperature regulation under anaesthesia?"), and watches **Agon**
unwrap it link by visible link until every step checks out — a theorem she can
*defend*, not a number she has to trust. When a new observation collides with an
existing rule, the game does not just say "invalid"; it surfaces the genuine
conflict and lays out the options — reject the finding, revise the rule, or hold
it as a hypothesis pending investigation — exactly the move clinical knowledge
actually makes when a textbook generalization meets a real exception.

**When complete.** A large medical ontology (SNOMED, say) becomes the model
every proposal is tested against, and the warrant lifecycle keeps a standing
record of which clinical rules have withstood challenge and which are provisional.
The result is reasoning that is **auditable**: not "the system said so," but a
drawn, inspectable chain from accepted premises to a defensible conclusion — and
an honest account of where that chain is still open.

---

## The editor

**Étienne is preparing Peirce for publication.** He works on the long, patient
labor of bringing Peirce's voluminous journals, notebooks, and loose manuscript
pages into a coherent, citable, *published* form — the kind of critical edition
that lets every later scholar quote a graph and trust that what is on the page
is what Peirce drew. His problem is not invention but **fidelity**: Peirce's
graphs survive as hand-drawn marks across thousands of manuscript pages, and a
printed edition needs each one rendered faithfully, captioned, attributed, and
typeset to professional standard. This is the persona the LaTeX package
[`egpeirce.sty`](references/egpeirce.sty.txt) (and its
[documentation](references/Egpeirce%20Documentation.pdf)) was written to serve:
someone producing publication-grade typeset versions of Peirce's handwritten
existential graphs.

**Now.** Étienne transcribes a manuscript diagram into a linear form he is sure
of — EGIF, CGIF, or CLIF — and loads it into Arisbe, where it parses to a formal
EGI and renders in a chosen visual style, including a **Peirce-authentic** style
alongside the Dau and Sowa conventions. Because layout is a free,
presentation-only regime, he can nudge vertices, reshape a cut, and reroute a
ligature by hand to match the *spatial arrangement of the original page* — and
the correspondence attestation guarantees that all this hand-adjustment is pure
appearance: it never changes what the graph asserts. He can round-trip the same
graph between linear forms to cross-check his transcription, and he carries the
manuscript's provenance — source, date, page — as typed metadata on the corpus
item.

**When complete.** The decisive frontier for Étienne is **LaTeX/TikZ export** —
the bridge from Arisbe's drawn form to the publication-ready vector graphics
that `egpeirce.sty` produces, so a graph he has verified on screen becomes a
figure he can drop straight into the edition, compiled and citable. With it come
the rest of the editorial toolchain sketched in
[FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md](FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md):
an **overlay-comparison mode** to fade between Peirce's original scan and the
recreation and confirm spatial accuracy; **batch export** of a whole
manuscript's worth of graphs into one appendix; an **auto-citation** generator
in the edition's house format; and the **by-hand reading desk** — an interactive
transcription surface where the graph *and* its scholarly apparatus (provenance,
editorial annotations, variant readings) are captured together, the human
counterpart to Arisbe's file translators. The promise is that the inerrant
linear↔graphical correspondence at Arisbe's core becomes, for the editor, a
guarantee at the level that matters most to an edition: **the printed graph and
the manuscript graph denote the same thought** — and the apparatus says so, in
citable form.

---

## What the personas share

Six people, one sheet. The teacher wants logic to be *done*; the student wants
to be *caught*; the researcher wants the *seam* between domains; the logician
wants the mathematics *exact*; the physician wants reasoning that is
*auditable*; the editor wants fidelity that is *citable*. What lets one system
serve all six is the single commitment underneath: **the picture and the
proposition are the same sign, and Arisbe keeps them so.** Peirce supplies the
aim — thinking in pictures, logic as a living practice of assertion, challenge,
and revision. Dau supplies the guarantee. The personas supply the reasons it
matters.

---

## Pointers

- **Narrative scenarios (plain language):** [ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md)
- **For Peirce scholars in particular:** [ARISBE_FOR_SCHOLARS.md](ARISBE_FOR_SCHOLARS.md)
- **The editor's frontier, in detail:** [FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md](FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md)
- **The central contract (picture = proposition):** [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
- **The formal account of the game:** [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md)
- **Run it:** `uv sync --extra dev` then
  `uv run uvicorn web_api.main:app --reload --port 8000` and open `/organon`.
