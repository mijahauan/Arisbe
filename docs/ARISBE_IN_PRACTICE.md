# Arisbe in Practice: Who Uses It, and How

*An introduction for people who have never heard of Arisbe — told through the
people who might use it and the work they actually do.*

**Status**: active development · **Last refreshed**: 2026-06-22
*(Combines the former `ARISBE_PERSONAS.md` and the original scenario narrative.)*

*New to the **ideas** rather than the tool? The plain-language
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) tells the story of what
Arisbe challenged in Peirce and the traditions that read him, and what changed — no
logic required. This document is its practical companion: who uses Arisbe, and how.*

---

## What Arisbe is for

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

That last clause is the engineering heart of the system, and every persona
below leans on it: Arisbe holds the **drawn form** and the **written form** of a
graph in *provable correspondence*. The oval you draw and the formula
`~[ (man *x) ~[ (rich x) ~[ (happy x) ] ] ]` denote the **same mathematical
object**, and they keep denoting it across every edit, every re-layout, every
transformation, every round-trip. A runtime check refuses to show you a picture
that means something other than what it says.

What Arisbe is **not**: it is not a natural-language parser, and not a black-box
reasoner that hands you a verdict. When something must be turned from English
into logic, that is a separate, noisy job best left to a language model or a
semantic parser; Arisbe's contribution begins once a candidate logical form
exists — to *verify* it, *draw* it, *interpret* it against a world, and keep its
*warrant*. It is the trustworthy interpretant behind the parser, not the parser.

---

## How it works: the cycle of inquiry

Arisbe offers three complementary ways of working, modelled on how reasoning
actually happens:

- **Organon** — the library. Browse, study, and compare what is already known
  (read-only, every item attested in correspondence).
- **Ergasterion** — the workshop. Build new claims by drawing them freehand and
  having Arisbe *read* the drawing back as a determinate sign; practise the
  transformation rules; keep private drafts.
- **Agon** — the arena. Test a new claim against established knowledge to
  discover what it *means* — does it follow, contradict, extend, or open a new
  question?

These form a cycle: **Know** (Organon) → **Make** (Ergasterion) → **Contest**
(Agon) → **Integrate**, and the result flows back into what you know. One rule
keeps the cycle honest: *work in the workshop never lands directly in the
library.* A graph reaches the trusted corpus only by being **tested through
Agon**, or as a presentation-only restyling of something already trusted. Until
then a draft lives in a private scratch space. So where a scenario below says a
claim "becomes part of what she knows," read it as: *made in the workshop, then
earned its place by being contested.*

---

# Part I — By persona: what you can do, and what you gain

For each: *what you can do today*, and *what you will be able to do once Arisbe
is complete.* The line between them keeps moving — several items that were
"when complete" a few months ago have since shipped, and are now under "Now."

## The teacher

**Maria teaches introductory logic.** She is tired of students who can push
symbols around a truth table but cannot say what an implication *means*. She
wants logic to be something her students *do*, not a notation they decode.

**Now.** Maria opens **Organon** and pulls up a worked proof — Peirce's Law,
Barbara, the uniqueness of a group identity — each a real chain of sound steps
she can walk forward and back. She drops a small domain model in front of the
class ("every mammal is warm-blooded; dogs are mammals…") and in **Agon** lets a
student propose a claim and watch the game *unwrap* it from the outside in until
it resolves to a theorem, a contradiction, or a genuinely new fact — now against
an **automated opponent** (the machine plays the model side optimally), with the
running play and its verdict shown move by move. She can hand a student a target
graph and let **challenge mode** grade a freehand attempt against it, with a
**legible diff** that says, in the student's own vocabulary, *exactly* where the
attempt and the target part ways — wrong scope, missing line of identity,
arguments in the wrong order. Nothing on screen is a static slide; every diagram
is live and inspectable.

**When complete.** A fully constructive *proof mode* to complement the
model-checking game, so a challenge can be played as "find the derivation," with
the system refereeing each rule application; and richer authored challenge banks
graded automatically. Logic class becomes a workshop with a tireless, honest
referee.

## The student

**Amara is learning, not performing.** She does not yet trust her own reasoning,
and abstract rules slide off her. She needs to *see* why a step is allowed and to
be caught — kindly and immediately — when it is not.

**Now.** In **Ergasterion** Amara composes a graph by hand on a freeform canvas:
she places relations, draws cuts as ovals, drags lines of identity. Then she
asks the graph **"what do you say?"** — and it reads itself back as a determinate
sign with its linear form shown, *or* tells her, in the vocabulary of graphs,
why it is not yet well-formed (a line dangling into nothing, two cuts improperly
overlapping). A **Graph↔Argument** switch makes the difference between a sketch
and a committed claim unmistakable: you cannot apply a rule to an unfixed
drawing, nor silently change the meaning of a fixed one. She practises the six
transformation rules with every application validated against the mathematics,
and **challenge mode** turns practice into a game she can win — reproduce *this*
graph, and get told precisely how close she is (the trickiest targets are marked
with a 🐉, the field guide's "dragons," and a wrong attempt hands her back the
antidote). And because a lone graph is so easy to misread, a small **context
panel** rides alongside every picture, answering the beginner's first question —
*what whole is this a fragment of, and on whose sheet does it stand?* — with the
chain of cuts that enclose whatever she clicks. She never mistakes an extract for
a finished thought.

**When complete.** The "reading desk" — transcribe a graph straight out of a
textbook and have Arisbe confirm she copied it faithfully. Over a term she
accumulates not memorized facts but the *experience of having reasoned her way*
to them — the only thing that ever transfers.

## The researcher

**Kwame works across two fields that have never been formally introduced.** He
has bodies of knowledge in ecology and economics and a hunch that a claim
spanning both might hold. He needs the precise logical seam where one domain's
conclusions become another's premises.

**Now.** Kwame studies two corpora side by side in **Organon**, identifies the
shared concept, and in **Ergasterion** builds a bridging argument. He tests it in
**Agon**, which *sorts* it: this part is a theorem of the merged model, this part
a reasonable extension to be agreed, this part an open conjecture needing
evidence the game cannot supply. He moves a claim between Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)), Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)), and Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif))
without loss; imports external material through a doorway that admits it honestly
at **low warrant** — parsed and attributed, never asserted true; and reads the
full provenance of any corpus item. Real ontologies are already in hand as
models to contest against — SUMO, BFO, FOAF, SKOS, Common Logic Ontology Repository ([COLORE](GLOSSARY.md#colore)) — imported through the
Web Ontology Language ([OWL](GLOSSARY.md#owl))/Resource Description Framework ([RDF](GLOSSARY.md#rdf))→CLIF→EGI pipeline. He can ask the **interpretation register** "given this
world M, does G hold?" (true / false / *unknown*, with a witness or
counterexample), run the **inverse pivot** — "*in what world does G hold*, and
what is its residual contribution?" — and, when a Graphist-won contest is worth
keeping, mint a **warrant**: G enters the corpus as "withstood Agon," carrying
its play as proof. Every corpus item now wears its **standing** on a badge —
*posited* (admitted at low warrant), *derived* (a sound chain reaches it), or
*withstood* (it has survived the arena) — and the badge's own tooltip states the
non-claim it must never be read against: *correspondence is attested, truth is
not*. The badge ranks the **claim**, never the person who entered it.

**When complete.** Larger ontologies (WordNet, SNOMED, Wikidata) as routine
opponents; a sharper account of *vocabulary the model cannot even address*
(distinct from "addressable but unconfirmed"); and a fuller warrant lifecycle
that records *how much* a claim has been challenged and by whom. Research becomes
a diachronic record of inquiry — not a pile of results, but a documented history
of how a community tested its way to them.

## The logician / mathematician

**Sofia cares about the mathematics being right, all the way down.** She wants
the diagram and the formal object to be the *same thing*, provably, and to
interrogate the claim that they are.

**Now.** Sofia works with Dau's six transformation rules (ERA, INS, IT+, IT−,
DC+, DC−), Beta-aware — lines of identity, shared vertices across cut
boundaries — through a headless stepwise protocol that constructs and replays a
proof move by move with deterministic provenance. The mathematical core has a
protected test suite that must always pass; correctness is not advisory. She
reads the **correspondence invariant** as a runtime attestation that *refuses*
any (picture, proposition) pair that does not denote one object — an operational
claim about the iconicity of Existential Graphs ([EGs](GLOSSARY.md#eg)) she can try to break by running the module.
Layout is a *projection* of a coordinate-free structure, so she can swap the Eclipse Layout Kernel ([ELK](GLOSSARY.md#elk))
engine for the experimental "tension" engine that draws a line of identity as a
single taut thread through the cut nest — the authentic Peircean single-line
reading. Beyond proof, she has the **semantic game** (truth-in-a-model,
three-valued and open-world), the **theory query** ("is this universal a theorem
of that theory?", decided by freezing a fresh witness), and a fragment-honest
**Description Logic ([DL](GLOSSARY.md#dl)) reasoning** layer (subsumption / instance / consistency) she can run against
a benchmark — and which reports *soundness and coverage separately*: it abstains
where its bounded fragment can't decide rather than ever answering wrongly.

She can also **fold** a drawn subgraph under a named definition and **unfold** it
again — abstracting a reusable piece whose legitimacy rests on its *expansion*
(the rules accept the swap), never on its name.

**When complete.** Exhaustive, hypothesis-driven testing that enumerates *every*
applicable site for each rule; a theorem-prover bridge (Coq/Lean via CLIF); and the
rest of the **mathematics horizon** — universal generalization via a Dau-native
scaffold tactic and a graph-with-holes schema node — which opens EGs onto real
mathematics (ZFC separation, Peirce's 1881 axioms of arithmetic). *(This track is
in progress: the fold/unfold definition layer has shipped, the soundness homework
for universal generalization is done, and draft fixtures exist; the schema node is
next.)* The system becomes a place to *do new mathematics* in pictures, not only to
reproduce known proofs.

## The physician

**Dr. Okonkwo reasons under a body of clinical knowledge** that is large,
revisable, and occasionally self-contradictory. She does not want a black box
that outputs a diagnosis; she wants to see *which* of her commitments forces a
conclusion, and to be shown — explicitly — when a new finding contradicts the
rules she has trusted.

**Now.** She lays out the relevant knowledge in **Organon**, frames a question in
**Ergasterion** ("given everything we hold, does this patient need temperature
regulation under anaesthesia?"), and puts it to **Agon**'s interpretation
register, which unwraps it link by visible link and returns a defensible verdict
with the **witness** that satisfies it or the **counterexample** that defeats it —
and, crucially, an honest *unknown* when her knowledge neither confirms nor
denies. When a new observation collides with an existing rule, the disposition
taxonomy lays out the genuine options — reject the finding, revise the rule, hold
it as a hypothesis — exactly the move clinical knowledge makes when a textbook
generalization meets a real exception. Nothing auto-asserts; the judgment is
hers.

**When complete.** A large medical ontology (SNOMED) as the standing model, with
guideline rules materialized so the reasoning fires automatically; and the
warrant lifecycle keeping a record of which clinical rules have withstood
challenge and which remain provisional. The result is reasoning that is
**auditable**: not "the system said so," but a drawn, inspectable chain from
accepted premises to a defensible conclusion — and an honest account of where
that chain is still open. *(This applied-clinical loop is the least-exercised of
the personas; the machinery is built, the domain modelling is the work ahead.)*

## The editor (Peirce scholar)

**Étienne is preparing Peirce for publication.** His problem is not invention but
**fidelity**: Peirce's graphs survive as hand-drawn marks across thousands of
manuscript pages, and a critical edition needs each rendered faithfully,
captioned, attributed, and typeset to professional standard. This is the persona
the LaTeX package [`egpeirce.sty`](references/egpeirce.sty.txt) (and its
[documentation](references/Egpeirce%20Documentation.pdf)) was written to serve.

**Now.** Étienne transcribes a manuscript diagram into a linear form he is sure
of — EGIF, CGIF, or CLIF — loads it into Arisbe, where it parses to a formal Existential Graph Instance ([EGI](GLOSSARY.md#egi))
and renders in a chosen style (a **Peirce-authentic** style alongside the Dau and
Sowa conventions). Because layout is a free, presentation-only regime, he can
nudge vertices, reshape a cut, and reroute a ligature by hand to match the
*spatial arrangement of the original page* — and the correspondence attestation
guarantees that all this hand-adjustment is pure appearance: it never changes
what the graph asserts. He round-trips a graph between linear forms to
cross-check his transcription, and carries the manuscript's provenance — source,
date, page — as typed metadata on the corpus item.

**When complete.** The decisive frontier is **LaTeX/TikZ export** — the bridge
from Arisbe's drawn form to publication-ready vector graphics, so a verified
graph becomes a figure he drops straight into the edition. With it: an
**overlay-comparison mode** to fade between Peirce's scan and the recreation;
**batch export** of a whole manuscript's graphs; an **auto-citation** generator;
and the **by-hand reading desk** — an interactive transcription surface that
captures the graph *and* its scholarly apparatus (provenance, editorial
annotations, variant readings) together. The promise: the printed graph and the
manuscript graph denote the same thought, and the apparatus says so, citably.
(See [FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md](FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md).)

## What the personas share

Seven people, one sheet. The teacher wants logic *done*; the student wants to be
*caught*; the researcher wants the *seam* between domains; the logician wants the
mathematics *exact*; the physician wants reasoning that is *auditable*; the
editor wants fidelity that is *citable*. What lets one system serve them all is
the single commitment underneath: **the picture and the proposition are the same
sign, and Arisbe keeps them so.** Peirce supplies the aim; Dau supplies the
guarantee; the personas supply the reasons it matters.

And they share one more thing, easy to miss because it is built so deep: **the
graph is judged, never the grapher.** A claim earns its standing by passing the
*method* — the rules, the §3.3 check, the contest — *on its content*, whoever
drew it. The newcomer's graph and the expert's graph meet exactly the same
scrutiny; the doorway gates *what* you propose, not *who* you are; the warrant
badge reports how a *claim* has fared, never the worth of a person. The opposite —
dismissing a claim because of who made it rather than testing it — is the one move
the system is built to refuse (it has a name in the wider world: *epistemic
injustice*). Adherence: the augurs were rightly demoted by **losing the contest**.
Breaking: refusing to look through Galileo's telescope because of who was holding
it. *(The argument behind this — and where it parts from the grand "ladder of
progress" readings of Peirce — is told in
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md), Doubt 4.)*

---

# Part II — In practice: six scenarios

The personas above describe *who*; these scenarios show *how the cycle feels*, in
language meant for anyone. Each is a concrete instance of one of the game's
outcome cases (the formal account is in
[ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md); its Part II gives the
scenario-by-scenario mapping).

## Scenario 1: What you already knew — *deduction*

**Dr. Melo, a veterinarian**, holds: every mammal is warm-blooded; every
warm-blooded animal needs temperature regulation under anaesthesia; dogs are
mammals. A client brings in a dog, Biscuit, for surgery.

In **Organon** she reviews the three assertions. In **Ergasterion** she
constructs the proposal "Biscuit needs temperature regulation during surgery." In
**Agon** the game unwraps it from the outside in: Biscuit is a dog (the client
brought one) → dogs are mammals (established) → mammals are warm-blooded → 
warm-blooded animals need regulation. Every link checks out: the claim is a
**theorem** — already implicit in what she knew. The conclusion can be added to
the patient's record.

*This is deduction* — drawing out what is already contained in what you know. The
Agon did not surprise her; it confirmed her reasoning was sound.

## Scenario 2: Something genuinely new — *empirical enlargement*

**Tomás, a birdwatcher**, logs a wetland reserve: herons are wading birds;
wading birds have long legs; kingfishers are diving birds; diving birds nest near
riverbanks. One morning he spots a bird he has never recorded — bright blue, long
bill, diving from a branch.

**Organon** has no matching entry. In **Ergasterion** he describes the bird and
drafts an identification: "Azure Kingfisher." In **Agon** the game reaches a
**stalemate** — not because anything is wrong, but because the proposal is
*independent* of existing knowledge: it neither contradicts nor follows. Since
the claim is compatible with everything known and he has direct observational
evidence, he accepts it as a **new fact**; the knowledge base grows.

*This is empirical enlargement* — the game's role was not to prove or refute but
to *sort* the proposal: consistent with, and independent of, what was known —
exactly the condition under which a new fact can be accepted.

## Scenario 3: A contradiction that teaches — *knowledge revision*

**A community garden** holds: tomatoes require full sun; the north bed is in full
shade — so everyone has accepted that tomatoes cannot grow in the north bed. Then
Priya plants cherry tomatoes there with reflective mulch, and they fruit
abundantly.

In **Agon** her claim **contradicts** the established knowledge — but a
contradiction is not a verdict. The game's interpretive function lays out the
options: reject the proposal, revise the knowledge base, or hold it as a
hypothesis pending investigation. The evidence is real, so the group **revises**:
"tomatoes require adequate light" replaces "tomatoes require full sun," and
"reflective mulch can supplement light" is added.

*This is knowledge revision* — the hardest and most powerful outcome. The old
rule was not wrong; it was *incomplete*, and the game exposed the incompleteness
and guided the repair.

## Scenario 4: Building an argument — *a mixed verdict*

**Keiko, a town planner**, wants a park on a disused lot. From the council's
accepted positions (green spaces cool the air; cooler air lowers energy costs;
lower costs raise property values; the lot is residential and currently a
drain), she builds a six-step argument to "a park is a net financial benefit."

In **Agon** the argument *sorts*: steps 1–4 are a **theorem** of what the council
already accepts; step 5 ("higher values → higher tax revenue") is a **reasonable
extension** they could agree to add; step 6 ("revenue exceeds cost") is an **open
conjecture** needing financial projections the game cannot supply. Keiko now
knows exactly where her argument is strong and where it needs evidence.

*Real arguments are rarely pure deductions.* The Agon tells you which parts are
certain, which are plausible-but-need-agreement, and which are open — far more
useful than "valid / invalid."

## Scenario 5: A course of study — *learning through inquiry*

**Amara learns zoology** through guided investigation rather than lecture. Week 1
establishes a small model (mammals warm-blooded; reptiles cold-blooded; …). Week
2: "can whales regulate their temperature?" — "whales are mammals" is a **new
fact** they accept on authority, after which the rest follows as a **theorem**,
and she understands *why*. Week 3: "are all sea creatures cold-blooded?" — a
**contradiction** with "whales are warm-blooded," so she learns to refute by
counterexample. Week 4: "some fish regulate partially" — a contradiction she
resolves by **revising** the rule. 

*Education is not the transfer of facts.* It is the guided construction of
understanding through proposing, testing, and revising — each episode leaving her
with a richer model and the experience of having reasoned her way to it.

## Scenario 6: Bridging two bodies of knowledge — *a merged theorem*

**Kwame** has an ecology base (wetlands filter pollutants → fisheries →
coastal communities) and an economics base (coastal communities → tourism
revenue → infrastructure → population growth). He wants to know whether
"preserving wetlands supports population growth."

In **Organon** he finds the shared concept — "coastal communities." In
**Ergasterion** he builds the bridging chain. In **Agon** each step is a theorem
within its domain, and the critical link holds because the domains share that
concept: the conclusion is a **theorem of the merged model**. The two bases are
now connected by an explicit chain, recorded for further inquiry.

*Interdisciplinary insight* works not by blurring boundaries but by finding the
precise logical links between well-understood domains.

---

## The cycle, once more

Every scenario follows the same pattern: **Know** (study what is established) →
**Make** (construct a claim) → **Contest** (test it — does it follow, contradict,
extend, or open a question?) → **Integrate** (add a fact, revise a rule, flag a
hypothesis, record a refutation). This is Peirce's vision of logic as a **living
practice** — not a static catalogue of truths but an ongoing process in which
knowledge grows, corrects itself, and deepens through assertion, challenge, and
resolution.

The participants need not be logicians. The formal machinery — the graph
structures, the transformation rules, the game protocol — handles the rigour.
What participants bring is clarity about what they know, honesty about what they
claim, and willingness to revise when the evidence demands it: the habits of
good reasoning Peirce spent his life trying to cultivate.

---

## Pointers

- **The ideas, in plain language** (what Arisbe challenged in Peirce and the
  tradition, and what changed): [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md)
- **The beginner's on-ramp to the graphs themselves** (with the pitfalls marked):
  [FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md)
- **For Peirce scholars in particular:** [ARISBE_FOR_SCHOLARS.md](ARISBE_FOR_SCHOLARS.md)
- **The editor's frontier, in detail:** [FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md](FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md)
- **The central contract (picture = proposition):** [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
- **The formal account of the game:** [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md)
- **Run it:** `uv sync --extra dev --extra web` then
  `uv run uvicorn --app-dir src web_api.main:app --reload --port 8000` and open `/organon`.
