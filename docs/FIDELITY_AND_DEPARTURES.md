# Fidelity and Departures

> **New here? Read the story first.** This document states the departures
> *precisely*, for a reader fluent in the logic. For the same material as a plain
> narrative — what stirred each doubt, how it was argued out, and what changed —
> see **[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md)** (no prior logic
> required; every principle carries a worked example). *Latest change:* the
> worth-ladder's footing was re-grounded — from an imported "equal-dignity" premise
> to a methodological one (*gate the claim by method, never the agent by worth;
> owe every claim its uptake*) — see the Corollary and Examination III.

*What Arisbe owes Peirce, where it leaves him, and why — and a standing
invitation to have the departures tested by an opposing mind.*

*A philosophy-spine document. It gathers into one place the debt that the
rest of the spine assumes and the three departures that
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md), and
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) each argue locally. It is
written to be **answered** — see §6, the charge to the opposition.*

---

## 0. Why this document exists

Arisbe is built in homage to Charles Sanders Peirce. Nearly everything load-
bearing in it is his: the aim, the instrument, the semiotic that makes the
instrument mean, the dialogical test that makes meaning answerable. The author
is not a Peirce scholar and does not pretend to stand above the immense and far
more learned literature that has studied, edited, and applied Peirce in the
century since his death. **He owes that tradition the courtesy of saying clearly
where he has left it, and why.**

Three departures have accumulated in the doctrine. They were drafted boldly,
then **examined adversarially over five rounds** (the record, and the strongest
case against each, is [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md));
the sections below state them in their *post-examination* form, which is in two of
three cases narrower and more honest than the first draft:

1. **Convergence and the real** *(was: "inquiry does not converge")* — the
   first-order question "is this nearer the real?" is a non-locution (secured);
   whether the *whole sequence* converges on a real is an open question held at
   parity, with "reality" reserved for the encountered ground as a choice, not a
   refutation. The committed content is much narrower than the original headline.
2. **Nothing *derived*-contingent floats free at level 0** *(was: "nothing
   contingent can be said")* — the demonstrative recto bears form, not derived
   contingent content; the assertoric register's office to *posit* a premise is
   preserved. Survives, as a scope-correction the docs already half-stated.
3. **Gamma's *modal* program is not needed** *(was: "Gamma is not needed at
   all")* — no new modal *mark* (broken cut, tincture) is needed; the architecture
   stands. The *completeness* boast is scoped to propositional modal logic; the
   second-order program is the real frontier. Survives, amended.

Each is argued, in its home document, *from within* Peirce's own commitments
rather than against them. The point of the examination was that an argument that
flatters its author is worth little: the departures were **handed to opponents**
— a traditional Peircean, a modern logician, a historian of the secondary
literature — and what flattery they carried was burned off. What survived is kept
on better terms than conviction; what did not was revised, in the author's own
voice, below.

---

## 1. The devotion — what Arisbe takes from Peirce wholesale

State the debt first, because the departures are unintelligible without it. None
of these is hedged; they are the floor.

- **The aim.** Peirce did not build the graphs to draw logic prettily but to
  *analyze reasoning* — a "moving picture of thought," a "rough and generalized
  diagram of the Mind," in service of the lifelong hope that better analysis of
  inference yields clearer inference. Arisbe inherits the instrument **and the
  hope** ([CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md)). This is the whole point
  of the project; everything else is means.

- **The instrument.** The Existential Graphs themselves — Alpha (the cut, the
  sheet, juxtaposition) and Beta (the line of identity) — are taken as given, in
  Dau's rigorous formalization. The six transformation rules are Dau's; the
  soundness of every step is non-negotiable bedrock. Arisbe does not improve
  Peirce's calculus; it implements it faithfully and builds outward.

- **The semiotic.** A sign stands for an object to an interpretant which is
  itself a further sign — *semiosis*, triadic and unbounded. Arisbe's deepest
  architectural thesis is that an Existential Graph ([EG](GLOSSARY.md#eg)) derivation **is a chain of semiosis**: each
  state a sign, each rule application a warranted interpretant. The chain, not
  the snapshot, is the unit of meaning. This reading is offered as Peircean in
  spirit, not as a quotation, and the codebase is organized around it.

- **The dialogical test.** "Endoporeutic" is Peirce's own word for reading a
  graph from the outside in, as a transaction between a defender and a skeptic.
  For Peirce the game is not a gloss on the logic — it is *how the logic means*.
  Arisbe's Agon is that conviction made operational: a graph's warrant is what
  survives the contest, not what the drawing asserts.

- **Fallibilism and the community of inquiry.** No belief is incorrigible;
  inquiry is a social process; truth is not a private possession. Arisbe encodes
  this structurally — warrant is a gradient that rises and falls, the corpus is
  held open to revision, and nothing is ever exempt from being drawn back under a
  cut and challenged again.

- **The pragmatic maxim, and the index.** Meaning is settled in conceivable
  effects, in use, in conduct — not in the ink. The sheet of assertion is an
  *index* of the universe of discourse (the object-side hookup), not a neutral
  plane. Arisbe's "attest correspondence, never truth" and its refusal to let any
  mark bear actuality are direct descendants of this.

**The summary of the debt:** if you removed everything Peircean from Arisbe,
there would be no Arisbe. The departures below are three places where the author
believes Peirce — or, more often, the tradition reading him — took a wrong turn
*by Peirce's own lights*, and where being faithful to the deepest commitment
required parting with a surface one.

---

## 2. Departure I — convergence and the real

*This section records the settled result of a five-round adversarial examination
(see [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md)). The original draft
("inquiry does not converge") did not survive: it was a footnote on sophisticated
Peirce. What survives is sharper, narrower, and honestly bounded.*

The realist holds that better inquiry is inquiry *nearer the real*, the real being
the convergence-target of the final opinion. We do not deny convergence and we do
not assert non-convergence — fallibilism humbles both symmetrically. The settled
position is a **joint, not a dissolution**, with two rungs that must not be merged.

**First order — secured.** "Is *P* or ¬*P* nearer the real?" / "this graph is at
distance *d* from the world" is a **non-locution** — pointless, not false. A
representation is a term in the sequence of inquiry; it cannot scribe its own
distance to that sequence's limit, since the limit (if any) is the limit *of* the
sequence, not a coordinate available *within* a term of it. This holds whether or
not the regress of standards closes. It is the same first-order discipline the
engine enforces at every save (§3.3 attests *correspondence, never truth*), at
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) floor #6 (no mark bears
actuality), and at level 0 ([LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md):
the recto bears form, not free-floating contingent content): **no mark may bear
its own distance-to-the-real as a terminus.** This much is won outright.

**Meta level — open, at parity.** The realist's claim lives one rung up: *does the
whole sequence converge on a real?* The success-criterion is Peirce's **belief
fixed under continued experience** (not bare doubt-recession), so there *is* a
well-defined refuter with fixed-point structure: recurrence — "dashed against
recalcitrant fact" — is its correctness signal, the real reasserting against a
settling that did not track it. Whether non-recurrence certifies *tracked a
stationary real* (Peirce wins, stationary case) or merely *not-yet-remade* (the
reflexive/looping case, where the encounter alters the ground so no fixed target
stands still) turns on whether the regress of standards — *do-otherwise-than-L is
itself L′* — closes at a transfinite fixed point. **We have not shown it fails to
close.** If it closes, there is a determinate higher law, the representational
level converges under a law-of-rewriting, and the realist may *name* that
meta-limit "reality." We **refuse** the name — reserving "reality" for the
encountered ground — but refusal is a choice of where to point the word, **held at
parity, not a refutation.**

**The survivor / overturner distinction (kept).** The real we say
nothing-as-terminus about is **not** the 1868 incognizable. It is cognizable *in
its effects* at every corrective step — the hole, the crop, the recalcitrant fact
— which is exactly how Peirce rehabilitated the real against the thing-in-itself.
The **survivor** (an un-overturned representation) is fully sayable, and Misak's
would-survival ("would belief *B* survive all the experience that would bear on
it?") is its correct gloss — it belongs on the **sayable side**, as a property of
survivors. The **overturner / encountered ground** is cognizable-in-effects but
not sayable *as a target scored for nearness*. This distinction survived every
charge in the examination.

**Negative orientation — secured.** Inquiry is driven from behind, away from doubt
and error; a standing is held until overturned by what thinking does not control;
the Agon peels and prunes (IT−, DC−, ERA); liveness retires what falls from use.
This is Peirce's own *Fixation of Belief* engine, and it is convergence *in*
reality under push — granted in full. Peirce's discriminator between science and
tenacity is **overturnability** by what our thinking does not control, not
attraction toward a target; we keep that discriminator and decline only the
separable convergence-clause ("the ultimate conclusion of every man shall be the
same") he states but does not independently derive. The negative reading is a
**friendly reconstruction the text licenses**, not a claim that Peirce was a
negativist.

**Unification across the three departures — analogy, not identity.** Departures I
(convergence-on-reality), II (contingent content at level 0), and III (the
actuality-mark / tincture) share one structural discipline: **a status on the
sayable side (survivor, form, agreement) is illicitly traded for a terminus on the
unsayable side (real-as-target, contingent-content-at-0, actuality).** This
**co-grounds** the three. It is **not** a single rule applied three times (level-0
unsayability is a syntactic theorem about marks; would-survival is sayable).
Departure I is **co-grounded** with II and III, not best-grounded among them.

**What we owe, stated plainly.** The **meta-naming** question above is undischarged
on both sides — it rests on whether the *do-otherwise-than-L is itself L′* regress
closes at a transfinite fixed point (the candidate argument for the open horn is a
reflexive diagonal grounded in the Alpha freedom-to-negate; it does not obviously
close). And the **separability** debt is paid only on the sayable side (the
survivor/real-object pair, honored per "How to Make Our Ideas Clear"); for the
terminal real-as-target it stands open, by the same parity. This is the one place
the departure is undischarged, and it is undischarged on both sides. We do not
paper it over. **This remains the departure most exposed to a careful Peircean** —
its committed content is now exactly: the first-order non-locution (won), the
reservation of "reality" for the encountered ground (a choice at parity), and the
co-grounding analogy (won) — not the original "inquiry does not converge."

*The **axiological corollary** of this departure — that if "nearer the real" is a
non-locution then no reasoner, age, or culture stands *nearer* than another (the
no-ladder claim) — was drawn out and **examined over four rounds** (as "Perspective
B"; see the **Corollary** at the end of this document and the full record in
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) "Examination II") and
**largely absorbed back into this departure**. What survives:
the **metric** terminus is dissolved (this departure's first-order result); the
context-free **comparative efficacy-vector** is *conceded* (structural realism — only
the summit was ever a non-locution, never the vector); and the one genuine residue is
the **worth-ladder denial** against the convergent dreams' fusion of competence with
worth — re-grounded (Examination III) on a **methodological** footing (the gate is
*method-on-the-claim*, not *identity-on-the-agent*; plus the *uptake* duty), no longer the
**imported equal-dignity premise** it once leaned on. Its companion "Perspective A" (the discipline
applied to *ends*) absorbed entirely into this departure + Departure II. See
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) "Examination II".*

---

## 3. Departure II — nothing contingent can be *said* at level 0

**The position Arisbe rejects.** The standard textbook gloss: *to scribe a graph
on the sheet of assertion is to assert it.* The blank sheet is where assertion
lives; depth 0 is the asserted ground; cuts deny.

**The Arisbe position.** Level 0 is not a surface that says something true; on its
depth-0 marks **no contingent saying is constituted by the marks themselves**. The
recto bears *form* — the scroll, the conditional scaffolding, structures valid or
model-relative — and the *demonstrative* recto cannot **derive** contingent
content; the bare depth-0 position does not, by itself, assert it. (We do not deny
the assertoric register its primary office — positing a contingent premise — see
below; the claim is about what the *marks* and the *depth* constitute, not a ban
on positing.) There are **two registers**, and the fault — in the formal and
diagrammatic EG presentations, not in proof theory generally (which marks the seam
with the turnstile Γ⊢φ vs ⊢φ) nor in the dialogical strand (Pietarinen, Hintikka,
which already supplies context-as-ground) — is conflating them:

- **Demonstrative** use — derive theorems from the blank by truth-preserving
  steps. Here the **level-0 theorem** holds: no legitimate derivation from the
  blank yields an unenclosed contingent proposition (the blank denotes truth; the
  rules preserve truth; a contingent atom is not valid; therefore no theorem
  carries one at depth 0).
- **Assertoric** use — scribe on the Sheet of Assertion the contingent premises
  you *assert*. These are overwhelmingly unenclosed and contingent. The SA exists
  precisely to bear them.

The textbook prints both flush together and **leaves the seam unmarked**, so a
reader cannot tell "someone asserts this, take it as given" from "the system
delivers this." Two different provenances — *posited-under-warrant* vs.
*derived-truth-preservingly* — collapsed into one drawing.

**The justification, rooted in Peirce.** Two Peircean sources, not one
invention. First, **soundness**: the level-0 theorem is not a stipulation but a
consequence of the calculus Peirce built and Dau proved sound. Second, the **late
Peirce** himself — the *Phemic Sheet* of the 1906 *Prolegomena*, where assertion
is analyzed not as a graphical permission but as a *normative act*: to assert is
to **assume responsibility**, to expose oneself to penalty should the claim fail.
On that analysis a scribed replica is a *proper* assertion only given a universe
agreed between parties, the conventions fixing the marks, **and** the utterer's
act of taking responsibility. "Assertion" was never a feature of depth; it was
always interpretant-side and act-side. The author's claim is that Peirce knew
this and the *formal/diagrammatic EG presentations left it implicit* — so the
departure is from those presentations, in Peirce's own direction. The novelty is
modest and real: noticing that diagrammatic EG lacks a turnstile-equivalent, and
supplying one operationally as a runtime warrant gradient — not the discovery of a
buried equivocation in the logic.

**A construction, not an unconditioned posit — and no unconditioned posit at all.**
One might object that the scroll `cut[ M cut[P] ]` ("P given M") merely relocates the
unconditioned saying to its antecedent M — M has to be scribed *somewhere*. It does
not. M cannot be scribed *anywhere unconditioned*, because the **Alpha asymmetry**
forbids it: `INS` introduces content only in *negative* contexts, so a contingent M on
the positive recto is not a foundation but a **forbidden move**. M enters legally only
by nesting from the blank (`DC+` opens a negative ring · `INS` places the given · `IT+`
carries it where it must bear · `DC+` opens the next), where it is a *defeasible* given
— sweepable, never incorrigible. The regress of "what conditioned this M?" bottoms out
not in a brute contingent assertion but in the **blank** — unconditioned yet
*contentless* ([LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §5,
§8). The thesis is therefore **gapless**: not merely "no *derived* contingent content
floats free at level 0," but "**no unconditioned posit anywhere** — the blank alone is
unconditioned, and it asserts nothing." What the calculus does not fix is *which* M;
that is the proper contingency, not a gap. *(This closes the `assertion-4` concession
recorded in [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md), Departure II — an
over-concession; the Departure II verdict is otherwise unchanged.)*

**What is genuinely at stake.** The load-bearing move is about **names**: the
hope that calling a positive-context insertion "an assertion" might *license* it
is the same error as hoping a broken cut could seat mode in the proposition — an
attempt to let a name on one correlate purchase a permission on another. One joint
is left honestly open (whether negative-context placement *constitutes*
fallibility or merely *diagrams* it), and that joint is the author's to close, not
the notation's.

---

## 4. Departure III — Gamma is not needed at all

**Peirce's position.** The Alpha/Beta graphs handle truth-functions and first-
order quantification; *modality, higher-order predication, abstraction, and the
logic of the graphs themselves* require a further system — **Gamma**. Peirce
pursued it for years: the **broken cut** for possibility/necessity on a single
static sheet, then the **tinctures** (provinces, modes of being) when the broken
cut "couldn't handle iteration." Gamma was left unfinished at his death and is
widely treated as the great incomplete frontier of the graphs.

**The Arisbe position.** *Gamma conceived as a modal extension is not a problem
Arisbe needs to solve.* The work the broken cut and tinctures were meant to do is
carried, exactly and without remainder, by structure Arisbe already maintains:

- A modal operator is not primitive content. By the **standard translation**, □
  and ◇ are quantifiers over a Kripke frame: □φ at w is ∀w′(R(w,w′)→φ at w′). The
  operators vanish into ∀/∃ over an accessibility relation — and ∀/∃ over a
  relation is exactly what **Beta draws**.
- Arisbe already *builds the frame*: the diachronic directed acyclic graph ([DAG](GLOSSARY.md#dag)) of sheets (worlds =
  states, R = legal transition) and the corpus of universes (worlds = models M).
  So the broken cut becomes ∃/∀ over accessible sheets with the accessibility
  *visible*; tinctures become the explicit identity of which universe a region
  inhabits; and Peirce's hardest case — trans-world identity, the line crossing a
  tincture boundary — becomes a **line of identity carried across a legal
  transition**, the very invariant Arisbe exists to keep inerrant.

**The justification, rooted in Peirce — and in what came after.** Peirce's own
aim was to *exhibit* reasoning, to make the apparatus examinable; the standard
translation lets Arisbe **draw the frame** the modal operator hides in a
metalanguage, which is more Peircean, not less. And **van Benthem's theorem**
(*basic propositional* modal logic = the bisimulation-invariant fragment of FOL)
certifies that no modal mark is needed to fill an expressive gap — **but only for
the propositional fragment**, over a fixed frame. We withdraw the unconditional
boast ("expresses everything □/◇ express," "there is no gap"): once §2's crux
carries a *line of identity* across a transition, we are in **first-order modal
logic with identity** (QML), which van Benthem's theorem does *not* govern. That
carried line makes substantive, contested commitments — **necessity of identity**,
and (with a fixed carried domain) the **converse Barcan formula** — that depend on
a stated **domain policy** (constant vs. varying/expanding). We owe that policy and
flag these as undischarged rather than calling trans-world identity "home ground"
for free. The claim is therefore **adequacy, not completeness**, and bounded
several ways: GL/provability, common-knowledge, and temporal-liveness modalities
are not first-order-definable and are *everyday*, not exotic — they belong to the
§7 second-order residue, and the §1 provability/trajectory reading is *gestured
at*, not constructed; counterfactuals (Lewis/Stalnaker sphere semantics, not one
R) and the object-language actuality operator @ (forgone by floor #6, not served)
are uncovered. Succinctness is traded for explicitness; the result is an *adequacy
argument*, not a mechanized theorem.

**What is genuinely at stake — and what is conceded.** The author does **not**
claim Gamma was empty. He claims its *modal* ambition is dischargeable without new
marks, and that conflating two different things made Gamma look like one problem
when it was two. **The real, irreducible residue is real and is kept:** *second-
order logic about the graphs themselves* — graphs of graphs, abstraction,
predication of qualities — which is genuinely higher-order and genuinely
ineliminable, and which Arisbe treats as the live frontier (the φ-hole/schema
node, the math track), **not** as a colour on the sheet. So the departure is
narrower than "Gamma is unnecessary": it is "Gamma's *modal* program is
unnecessary; Gamma's *second-order* program is the actual frontier, and it is not
modality."

---

## 5. The points of confusion these departures answer

The departures did not arise in a vacuum. Each responds to a genuine knot —
some in Peirce's own unfinished record, some in the tradition that has read him.
Naming them is part of the honesty; they are stated as the author's *reading*,
explicitly open to correction by those who know the corpus better.

**In Peirce's own record:**

- The **unfinished Gamma** itself — years of revision (broken cut → tinctures),
  the explicit complaint that the broken cut "couldn't handle iteration," and no
  settled system at his death. The author reads this not as a project that ran out
  of time but as a project that *conflated modality with second-order content*,
  which is why no single mark ever stabilized.
- The **equivocation around "scribe = assert."** The alpha/beta presentations
  treat scribing on the sheet as assertion; the 1906 Phemic-Sheet material treats
  assertion as an act of assumed responsibility. Both are Peirce. The tension
  between them is the seam Departure II is about.
- The standing tension between **fallibilism** and the **final opinion** — between
  "no belief is incorrigible" and "inquiry is fated to converge on the real."
  Peirce held both; Departure I is a claim about which one is deeper.

**In the secondary literature** (named with appropriate humility — the author is
flagging *where he is pushing against a consensus*, not indicting any scholar):

- **Context-as-enclosure swallowing context-as-ground.** The formal lineage
  (Zeman's dissertation; Roberts' monograph; Dau's formalization) gives a rigorous
  notion of *context = area individuated by enclosure*. It is silent on context as
  *ground* — whose sheet, what universe, under what commitments a scribing counts
  as assertion at all. A careful reader infers the second is handled because the
  first is handled so well. It is not. (Departure II.)
- The **unmarked seam** between the demonstrative and assertoric registers — the
  textbook habit of printing a posited contingent premise (the cat-on-the-mat)
  flush against the demonstrative permissions, as if the calculus delivered it.
  (Departure II.)
- The treatment of **Gamma as an unsolved *modal* extension** to be completed on
  its own terms, rather than as a conflation to be dissolved. *(Credit where due,
  per the examination: Zeman (broken cut ↔ S4/S5) and Roberts (the Gamma-strand
  catalogue) already separated Peirce's modal program from his higher-order one
  decades ago. Arisbe's contribution is to make that separation **operational and
  constructive**, not to first notice it.)* (Departure III.)
- The reception of **convergence-on-agreement as convergence-on-reality** — the
  slide from "inquiry converges (on solutions, on community agreement)," which we
  grant, to "inquiry converges on the real," which the examination showed is a
  *first-order non-locution* and, at the meta-level, an open question held at
  parity (not, as the original draft had it, a settled non-convergence thesis).
  (Departure I.)

The dialogical reading the author leans on most (Pietarinen's endoporeutic work,
Hintikka-style game semantics) is taken as an *ally*, not an opponent: it is the
part of the tradition that already locates meaning in the act and the contest
rather than in the static mark, which is the same instinct all three departures
express.

---

## 6. The charge to the opposition

This is the operative section. The author asks that the three departures be
examined **by an opposing mind** — and the strongest version of the opposition,
not a strawman. Four chairs are set for the prosecution; an examination should
fill each and press the specific charge.

1. **The traditional Peircean.** Charge: the departures misread Peirce. The final
   opinion is not a casual metaphor but a worked-out doctrine tied to his realism
   about generals and his theory of truth; the regulative/constitutive distinction
   the author leans on (Departure I) is not Peirce's and may dissolve under his
   actual texts. Show where the primary corpus contradicts the reading.

2. **The modal logician.** Charge: "modality without Gamma" (Departure III)
   over-claims. The standard translation buys first-order-definable frames at the
   cost of succinctness and of *object-language* modal reasoning; an embedded
   `□(P→◇Q)`, provability logic (GL), the actuality operator, two-dimensional and
   counterfactual constructions, and the practical proof-theory of modal inference
   may not be served by "draw the frame." Is the adequacy argument actually
   adequate, or only adequate for K/T/S4/S5 toy cases?

3. **The level-0 / philosophy-of-assertion scholar.** Charge: the level-0 theorem
   (Departure II) trades on an equivocation between *valid* and *assertible*, or
   proves something trivial dressed as something deep. Does "no unenclosed
   contingent theorem" actually carry the weight of "level 0 cannot say"? Is the
   two-register distinction real, or a re-description of the ordinary premise/
   theorem distinction every logic already marks?

4. **The historian of the secondary literature.** Charge: the "points of
   confusion" in §5 caricature the tradition. Zeman, Roberts, Dau, Shin, Sowa, and
   Pietarinen may have addressed context-as-ground, the assertoric register, and
   the modal/second-order distinction more carefully than the author allows. Where
   has the consensus already said what the author claims it omits?

A complete examination produces, for each chair: the strongest case *against* the
departure; the author's best available answer (drawn from the home documents); and
a verdict — **survives**, **survives with amendment**, or **does not survive** —
with the amendment or the casualty named explicitly. The point is not to win. The
point is to hold each departure only on terms that have been tested by someone who
wanted to break it.

---

## 7. The standard of success

The author's commitment, recorded plainly: **he would rather lose a departure to
a good argument than hold it on conviction.** A departure that survives a serious
adversarial examination is held on better terms than before; a departure that
falls is a correction, not a defeat. What must *not* happen is the comfortable
outcome where the opposition is too weak to land — which is why §6 names the
strongest charges and why the examination should be run, where possible, by minds
(or independent agents instructed to be) genuinely trying to win for the other
side.

This document was the indictment. **The verdict is now in** — a five-round
adversarial examination ran the four chairs above, and the departures in §§2–4
have been amended to their post-examination form. The full record, with the
strongest case against each departure and the rulings, is
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md). Headline: all three
**survive with amendment** — none fell, and none escaped untouched. Departure I
lost its original headline ("inquiry does not converge") and its first lever (the
regulative/constitutive distinction), keeping a narrower, sharper claim resting on
one named open joint; Departures II and III survive as scope-corrections. The
standard was met: the departures are now held on tested terms, with their debts
booked in the open.

---

## Corollary — the larger game and the common sheet (ends and progress, absorbed)

Two further perspectives were drafted after the three departures and tested by the
same standard: **A — "the larger game,"** the discipline applied to *ends* (we hold
no referee's chair; "principalities and powers" invoked, in the manner of the Flying
Spaghetti Monster, to *demote* every context-less ultimate end, tradition's
respectable *terminus ad quem* included); and **B — "the common sheet,"** the
discipline applied to *progress* (the convergent dreams — Peirce's final opinion,
Teilhard's Omega — rank the history of mind as a climb toward a terminus; B removes
the terminus and the worth-ranking). They were examined over four rounds (an opening
panel plus an iterative dissolution-press; the full record is
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md), "Examination II"). **Neither
survived as an independent perspective.** Pressed, both dissolved back into the three
departures plus a conceded structural realism — the outcome §7 courts. This corollary
records what they became; it is not a fourth or fifth departure.

**A is `departure_absorbed`** (≈0.81). It carries no proposition independent of
Departure I and Departure II. Two charges were decisive. First, the claim that a
context-less *end* is *malformed* "just as the unenclosed proposition is at level 0"
is a **category mistake**: level-0 unsayability is a syntactic theorem about *marks*
(Secondness), while an end / final cause is **Thirdness** — a real general that needs
no enclosing cut to be well-formed. Second, run with Departure II's *real* two-register
content the analogy **backfires**: Departure II does not dissolve the unenclosed
contingent thing, it **licenses** it in the assertoric register, so a context-free
ultimate end is a **legitimate low-warrant posit, fully sayable, not malformed**
(admitted at import, exposed to the Agon, never *derived*). Stripped of the over-reach,
A's two refusals *are* Departure I: "inquiry **derives** no context-free end" is the
negative orientation; "the game is not scored against a surveyable terminus" is the
first-order non-locution. (And the posited-vs-served distinction is unstable — a
low-warrant ultimate posit that survives the Agon sits at `withstood` and is then a
*served* terminus on the only reading the warrant gradient permits; only Departure I's
non-locution forbids it.) **A's surviving contribution is one small disciplinary
office — the *no-founder-exemption*:** the non-locution is universally quantified, so
it already ranges over Omega and the Final Opinion; what A *performs* is the refusal to
grant tradition's respectable, on-record termini the dignity-exemption their owners
might have spared. That is a use of owned content and good pedagogy (the FSM is the
memorable way to teach the universal), not a new claim. Ends *in context* — arguments
end, innings end, a player conceives a goal and lays plans to win — are real
throughout; A obviates no ends, only the context-less terminus *the game is said to
serve*.

**B is `departure_narrowed`** (≈0.75), nearly absorbed. Its master-claim ("no progress
outside any context") splits into parts with opposite fates. The context-free **metric
terminus** — a possessed summit, a distance-to-the-real the gradient scores nearness to
— is a non-locution, **dissolved** (this is Departure I's first-order result; "ordinal,
a staircase with no top" defends exactly and only this). But the context-free
**comparative efficacy-vector** is **conceded, not dissolved**: an instrument is scored
by work on a world that does not read our scoreboard (novel prediction, intervention,
the bridge that holds, the augurs' eclipse-failures recurring direction-stably), so
"a genuinely better instrument" is a mind-independent, ordinal, directional fact — and
an order with no greatest element is the textbook objective comparative *without* a
summit. That is **structural realism's** thesis (the vector, never the summit), and it
sits on the **survivor side** (§2's encountered real, cognizable in its effects). B
conceded it the moment it said "better instrument." So B's propositions absorb: metric
terminus = Departure I; efficacy-vector = conceded structural realism; competence ≠
worth = a category-fact. **B's one genuine residue is the *worth-ladder denial aimed at
an asserting opponent*:** the convergent dreams *fuse* competence with worth (later =
nearer, later = holier), and severing that fusion — *a later stage is a better
instrument; its inhabitants are not better souls; the child, the prior age, the
layperson stand at no greater distance in **worth***— is content, because the opponent
is on record. Three qualifications the examination forced: it is held **at parity in
the axiological register, never as a logical theorem** (made an entailment — "nearer
the love of God" — it overreaches into theology and is quarantined); it rests on an
**imported equal-dignity premise** this departure does not derive (own it, do not
smuggle it as following from the enclosure discipline); and it does **not** flatten
progress (abolition over slavery, conservation over the preoperational error are real
ordinal advances *in instrument*, not in the worth of souls).

**Update — the residue's footing, re-grounded (Examination III, 2026-06-22).** The author
moved to replace the *imported equal-dignity premise* with a derivable one — **"fair access
to the Game"** (the capacity to signify is the ticket of admission; competence is only how
well one plays once admitted). A three-opponent panel found "fair access" **falls as a
derivation** — a motte-and-bailey between *semiosis-as-such is open* (trivially true) and
*fair access to actual inquiry* (false: every real inquiry is a method-gated forum); the
anti-gerrymandering support **backfires**, since it is *submission to the method*, not
universal access, that lets convergence track the real. But the examination **re-grounds the
residue better than the import it replaces**, and this is now its footing:
**the only legitimate gate is the *method* applied to a *claim*, judged by content, never by
the author's identity; ranking *agents* by worth-as-inquirers is the gerrymander (an
identity-gate where only a method-gate tracks the real); and the positive duty is *uptake* —
test a claim on its content before dismissing it by its author (the anti-*ad hominem*; its
violation is epistemic injustice).** So the worth-ladder denial **no longer imports equal
dignity**: it follows methodologically from "only method-on-content tracks the real"
(framework-conditional on taking inquiry seriously — symmetric, since refusing that loses the
worth-ladder too). The competence/standing distinction is re-cut as **method-gate-on-claims**
(legitimate; the reactor) vs **identity-gate-on-agents** (the corruption). Full record:
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) Examination III. *Worked instances*
of each principle (adherence and the obvious break — Galileo's telescope, the reactor corridor,
the augurs' contest) are kept there and in the plain-language account
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md).

**One correction this examination forces on the surrounding doctrine.** B set
"context-free progress" against the wrong thing. A real **immanent operative tendency**
— synechism's continuity, habit-taking, the growth of concrete reasonableness — is
operative across contexts *without* being a terminus one stands outside and scores; the
deflationary (FSM / level-0) solvent, scoped to *surveyable* termini, never touches it.
The corpus already **instances** the category: the §3.3 correspondence invariant and the
secured negative orientation *are* exercised, immanent, context-transcending corrective
tendencies. The cap on this is **not a scope-cap** ("operative up to our contexts,
stopping at the cosmos" — that would be the referee's chair A forbids, or a synechist
over-concession) but an **enclosure cap, and it is won, not wagered**: the tendency is
sayable and operative wherever a context encloses it, and enclosure-malformed only when
scribed as the operative structure of the unenclosable whole (the outermost sep cannot
be drawn). Agapism thus wins its *category* (the tendency is real and instanced) and
*nothing* of the cosmic verdict, which remains Departure I's meta-joint, at parity.

**The honest billing, and the live floor.** Counted honestly this is not two new
departures but **one discipline (Departures I + II) + a methodological footing (the gate is
method-on-the-claim, not identity-on-the-agent; plus the uptake duty — Examination III) + a
conceded structural realism, deployed against two targets** (tradition's respectable
termini; the worth-misreading of progress). The double decentering survives, precisely:
*you are not the referee* (no surveyable outside — an epistemic limit, not an agency)
and *you are not nearer a possessed real, nor worth more* (though you may wield a
genuinely better instrument, which is a real, terminus-free fact). What is removed is
the chair and the conflation of *better instrument* with *nearer* and *worth more*; what
is untouched is competence. The doctrine rests; the **vigilance it mandates does not**,
and is meant never to: at every ranking surface Arisbe builds — the **warrant gradient**
(`provenance.standing_of`), the personas, any badge — the ordering must read as
**in-context standing and competence** (including the conceded efficacy-vector) and
**never** as the **worth or dignity of the reasoner**, **metric nearness** to a possessed
real, or **context-free Progress**. A badge read as a worth-ladder *is* the field-guide
dragon ([FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md), no. 6), whatever the
tooltip says. And A's agency-imagery, taken as a positive claim, would bear actuality
across the membrane and is *better not drawn* (floor #6) — kept strictly as imagery.

---

*Companion to [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md),
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md), and the
examination record [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md).
Sources for the three departures: the archived conversations under
[references/](references/).*

**Created**: 2026-06-18 · **Examined and amended**: 2026-06-19 · **Corollary (ends & progress) examined and absorbed**: 2026-06-20 · **Worth-ladder footing re-grounded (Examination III: method-gate + uptake)**: 2026-06-22
