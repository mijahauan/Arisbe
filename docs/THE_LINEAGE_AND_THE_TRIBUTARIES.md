# The Lineage and the Tributaries: An Intellectual History

> **What this is.** The book's history chapter. It tells where Arisbe's
> ideas came from, generously and precisely, and it tells that story as
> *two different kinds* of ancestry, because the project owes two different
> kinds of debt. The **formalization lineage** (Roberts, Zeman, Shin, Sowa,
> culminating in Dau) supplies the mathematics that makes the instrument
> sound. That lineage serves as the machinery's *warrant*, and it never gets
> graded, ranked, or mapped — only credited. The **tributary traditions**
> (cybernetics, artificial life, erotetics, evolutionary epistemology,
> belief revision, biosemiotics, the sociology of knowledge, active
> inference, scaling science, and the rest) each raised a genuine doubt and
> each lacked a piece of machinery; this chapter tells each one's story with
> the phenomenon credited *first* and the lack named second. The claim that
> binds the tellings together — that one operational core supplies the
> substrate they were all missing — speaks at the end as a **proposition,
> not an assertion**, testable by practitioner recognition, with refutation
> invited in the text.
>
> **Companions:** [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md)
> (the claim-by-claim verdicts, the graded concordance map — this chapter's
> evidence table — and the full citations) ·
> [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §8 (the proposition's voice and
> grades) ·
> [ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md)
> (one tributary's history told at full length) ·
> [SYNECHISM_AND_CONTINUITY.md](SYNECHISM_AND_CONTINUITY.md) (why one map can
> carry rows of such different kinds).
>
> *Written 2026-07-27 (Sitting B2), assistant-drafted; the two-strata ruling
> and the voice the author's.*

---

## 1 · Two kinds of ancestry

Every intellectual history of a working system faces a temptation: to flatten
its ancestors into one list of "influences," ordered by importance. This
chapter refuses the flattening, because the two ancestries differ in kind.

The first ancestry forms a **lineage** in the strict sense: a chain of scholars
who took Peirce's Existential Graphs — hand-drawn, scattered across
manuscripts, half-legible even to sympathetic readers — and made them into
mathematics that can be proved sound. Arisbe's engine applies that
mathematics; every guarantee the system makes, it makes *on their credit*.
If the lineage's theorems failed, nothing downstream — the correspondence
invariant, the game, the autonomous loops — would mean anything at all. That
explains why the project's concordance map rules that "the formalization
lineage is not a row": you do not grade your own warrant.

The second ancestry gathers a set of **tributaries**: twentieth-century
traditions that never touched Existential Graphs. Each of them found a real
phenomenon, a doubt worth a research program, and each, on the project's
reading, ran short of the same missing substrate — a way to hold a model *in
signs*, transform it only *soundly*, and keep an *earned record* of every
move. That reading forms the proposition this chapter builds toward, and a
reader stands invited to refute it.

## 2 · The lineage: from manuscript to mathematics

**Peirce** (1839–1914) invented the Existential Graphs in the late 1890s and
worked on them to the end of his life, calling them "moving pictures of
thought" and describing their reading discipline as *endoporeutic* — meaning
flows from the outside of a nest of ovals inward. He left behind a system of
astonishing reach (the Alpha graphs for propositional logic, Beta for
quantification and identity, Gamma for modality and abstraction) and almost
nothing a modern logician would accept as a soundness proof.

**J. Jay Zeman** (dissertation, 1964) supplied the first: a demonstration
that Alpha and Beta match propositional and first-order logic exactly, and
that the Gamma broken-cut fragment corresponds to the modal systems S4/S5.
Zeman made the graphs *answerable*. After him, "the picture never lies"
named a claim that could in principle be checked.

**Don D. Roberts** (monograph, 1973) did the historian's share: the
comprehensive catalogue of what Peirce actually drew, period by period,
including the tangled Gamma strands — modality, higher-order quantification,
metalanguage — that Peirce himself never disentangled. Roberts stands as the
reason later formalizers knew *what* there was to formalize, and the reason
this book can separate Peirce's modal program from his second-order one (a
separation Arisbe leans on; see
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)).

**Sun-Joo Shin** (*The Iconic Logic of Peirce's Graphs*, 2002) changed what
the graphs were *for*. Against a century of reading diagrams as informal
crutches, Shin argued that the graphs' iconicity counts as a logical
feature: some inferences stand *visible* in the drawn form in a way no
sentential notation matches. Arisbe's whole drawn-form ambition takes Shin's
thesis as an engineering requirement, insisting that the picture carries the
proposition first-class rather than illustrating it.

**John F. Sowa** serves as the living bridge between the graphs and working
knowledge representation. His conceptual graphs descend explicitly from EGs;
his interchange notations — EGIF for the graphs themselves, CGIF within the
ISO/IEC 24707 Common Logic standard — name the linear forms Arisbe
implements (implements, not invented: the formats remain his design and the
standard's);
his account of the EG↔discourse-representation isomorphism (tracing to Kamp)
and his 2011 telling of the endoporeutic game — from which Arisbe takes even
the word "peel" — supplied the vocabulary this book reasons in. Where the
earlier lineage made the graphs answerable, Sowa made them *usable*.

**Frithjof Dau** (*Mathematical Logic with Diagrams*, habilitation) stands as
the culmination and the bedrock. Dau gave the graphs a complete modern
formalization — the graph-with-cuts structure Arisbe's data model implements,
the six transformation rules (erasure, insertion, iteration and
de-iteration, double-cut addition and removal) with soundness proved, and
the translations between graphs and first-order formulas that anchor the
linear side of the correspondence. Arisbe's engine runs Dau's calculus,
deliberately unimproved, and the protected core test suite exists to keep it
so. Two honesty notes belong in the record beside the credit. Dau stands as
the de-facto standard formalization *for software*, though not uncontested in
philosophy: the standard survey literature treats Zeman, Roberts, and Shin
and omits him. And, as far as the project could find, no machine-checked
formalization of his calculus exists anywhere. Arisbe's executable test
suite serves as the closest operational guarantor located, and a true
mechanization waits as a field contribution to be made.

**Ahti-Veikko Pietarinen** holds a special position: he belongs to the
lineage and still answers as a living interlocutor. His *Signs of Logic*
(2006) and related work formalized the endoporeutic, game-theoretic reading
that Arisbe's evaluation engine implements; the project keeps a documented
conformance check against his account, with the divergences listed
([FIDELITY_ENDOPOREUTIC_CHECK.md](FIDELITY_ENDOPOREUTIC_CHECK.md)). And Ma &
Pietarinen (2018) gave sound and complete graphical calculi for fifteen
modal logics using Peirce's own broken cut — the rehabilitation of Gamma
that Arisbe's no-modal-mark architecture deliberately declines to follow.
The project argues that choice as adequacy for this architecture, never as a
refutation of Gamma, and keeps the argument's honest accounting of what it
forgoes where a reader can attack it
([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)).

That completes the lineage. Everything else in this chapter stands on it.

## 3 · The tributaries: doubts raised, machinery lacked

These read as history, roughly in the order the doubts arose. Each entry
credits the phenomenon first, because every one of these traditions found
something real, and then names the machinery the tradition itself identified
as missing, or that its later readers found wanting. The one-line versions,
with evidence and grades, stand as the concordance map's rows
([CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md)); the
tellings here read the map as narrative.

**The Umwelt (von Uexküll, 1934; Hoffmeyer and biosemiotics after him).**
Before anyone built a model-holding machine, von Uexküll saw that every
organism already carries one. Its world amounts not to *the* world but to
the slice its sign-repertoire can address, the Umwelt, closed by a functional
circle of perceiving and acting. Modern biosemiotics read this through
Peirce's sign theory and made the fit explicit. The tradition never had
*soundness*. It described a membrane with no calculus behind it, so it could
not say which transformations of the organism's sign-world preserve what the
organism knows. Arisbe's vocabulary-bounded horizon ("enough of the model is
what the proposal touches") gives that Umwelt a calculus inside it.

**Cybernetics (Wiener, 1948; Ashby, 1952; Conant & Ashby, 1970).** The
mechanists asked a hard question. Must every good regulator of a system be a
*model* of that system? Conant and Ashby proved the affirmative, and Ashby's
Homeostat physically demonstrated remodeling driven by environmental
friction. That supplies the one-line external justification for the model M
at Arisbe's interior: anything that copes with a world must carry a model of
it. Cybernetics lacked an *assertion calculus*. It held the model in wiring
or in variables, with no licensed way to assert, retract, or test a piece of
it. Arisbe's residence discipline supplies that lack. The model resides in
signs, revision comes only by licensed rule applications, and every change
stands as an acknowledged act, with a standing test gate holding it so.

**Artificial life (von Neumann's automata; Conway's Game of Life, 1970).**
Can iterated simple steps yield unscripted global order? Conway answered with
gliders, guns, and universal computation out of a two-state rule, and that
answer shaped Arisbe's automated loop directly. Then the *differences* became
doctrine. Life advances by a fixed rule on a closed dynamics, so nothing in
it asserts, and no outcome gets negotiated. Arisbe's generation plays as a
*round of a game*, where the rule that fires stands as a disposition chosen
and negotiable, and selection from outside bounds the open sheet, not the
rule. The loop stands built and gated. The grander reading — that a
negotiated sheet achieves what fixed rules cannot — stays a deliberately
unmeasured conjecture, and the map says so.

**Erotetics (Hamblin, 1958; Belnap; Wiśniewski's inferential erotetic
logic).** The logicians of questions raised the doubt that questions carry
first-class logical standing, with an inferential structure of their own,
rather than marking mere absences of assertion. The tradition lacked an
*economy*. No cost, severity, or decay attaches to the standing question, so
nothing in the logic says which open question deserves the next hour.
Arisbe's answer mints the question from an evaluation's UNKNOWN verdict,
traces the consequences of each answer, prices it by an attention economy,
and settles it only by a licensed step the record can cite. Its own history
tells that at full length
([ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md));
this chapter does not repeat it, because that document serves as the model
this chapter imitates.

**The sociology of knowledge (Berger & Luckmann, 1966).** Their doubt ran as
a question. How does the subjective become objective? How does a judgment
escape its maker and harden into an institution? Their answer, reciprocal
typification of habitualized actions, came with a warning the project treats
as a boundary-stone: institutionalization *cannot occur in an individual*.
The tradition lacked mechanism. It described typification and left nothing
that executes it. Arisbe supplies an executing model *of* the process and
holds Berger & Luckmann's own line against over-reading it. One instance
simulating a federation models an institution; it does not constitute one
([THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md)).

**Evolutionary epistemology (Popper; Campbell, 1974).** Knowledge grows by
conjecture and refutation; variation stays blind, retention selective. The
project accepts the schema and maps its own loop onto it. The proposer
varies, evaluation selects, and decay bounds retention. The tradition lacked
a *record*. Selection ran with no earned, replayable transcript, so the
history of a belief's survival vanishes the moment it has survived. Arisbe's
practice of pre-registered priors, mechanical verdicts, and refuted priors
kept on the record enacts Lakatos's research-programme discipline, enforced
by machinery. Every logged run exercises it, and the map grades it as
practice rather than as a measured claim.

**Belief revision and reason maintenance (Doyle, 1979; de Kleer, 1986;
Alchourrón, Gärdenfors & Makinson, 1985).** Their doubt asked a plain
question. How does a rational corpus absorb a contradiction? AGM axiomatized
the answer as postulates on set operations; truth-maintenance systems
implemented dependency tracking. Both lacked, on this reading, *ink*. Their
operators take their constraint from outside, with no drawn,
derivation-carrying step. A revision happens, but nothing in the corpus *is*
the revision. Arisbe's disposition taxonomy executes revisions as licensed
rule applications whose derivations ride on the record, so sound steps
compose the justification structure rather than dependency links.

**Active inference (Helmholtz's unconscious inference; Friston, 2006–).**
This stands as the closest formal neighbor. It reads perception and action
as one economy of prediction error and formalizes the boundary between model
and world as a Markov blanket, coined independently and doing the same work
as Arisbe's membrane. The project holds the difference up front. Free-energy
minimization runs as a gradient flow that keeps no inspectable chain, where
Arisbe's updates come as recorded, warranted, rule-licensed steps. And a
three-valued verdict distinguishes abstention from error, a distinction a
scalar surprisal collapses. What the neighbor has and Arisbe lacks gets
named with equal honesty. The action arm, acting on the world to reduce
expected error, remains the project's designed, unbuilt "directed
engagement."

**Scaling science (West, *Scale*, 2017).** West's doubt came as two
questions. Do aggregated units obey discoverable scaling laws? And what does
the unit's economics determine? This stands as the one tributary the project
has *measured* against pre-registered priors rather than only read. Five
experiments and a rider (the E-series, 2026) put West's question to units
that maintain a body of knowledge, and found that partitioning one
maintenance workload across bounded units cut total upkeep ~5× under a
meter charging the size of what each unit holds — with the magnitude turning
far more on the coordinator's scan discipline than on the partition, an
interior optimum that names a granularity rather than a partition, and a
multi-basin landscape in which balance strands. The refuted priors stand in
the map's row beside the held ones. Those units accumulate and forget
without reasoning or exchanging content, so the runs measure partition
economics and leave West's law proper — how a *community's* rate scales with
its size — standing as the prospect it always was, with much still to teach
whoever builds the harness for it (see the West program document, section 8).
What West's framework lacked, on this reading, concerns what the unit
*does*: an economics of the unit without its semantic work. The return-gift
offered back holds as a conjecture, that the allocation layer of such units
runs vectorial, not scalar (a self-contained methods account stands at
[WEST_METHODS_NOTE.md](WEST_METHODS_NOTE.md)).

**Anthropology against the ladder (Graeber & Wengrow, *The Dawn of
Everything*, 2021).** Was there ever one ladder of social development, or
many viable forms from the start? That names their doubt. The project adopts
the *negative* claim only, plurality with no teleology, and finds its own
plurality in the measured multi-basin landscape above. It reads their
historical evidence of deliberate, reversible movement between social forms
beside the model's finding that escaping a dear basin takes coordination,
and records that as a finding about the model, never about history. The
tradition lacked instrumentation. It offered evidence of plurality with no
cost measure on a settlement, which the model can supply *for its own
synthetic worlds*, and only for them.

**The deliberative interval (the project's own tributary, examined 2026).**
Last comes a reading Arisbe contributes rather than inherits. The freedom
worth the name lives in the determined *considering* between the branching
of alternatives at a doubt and the licensed resolution of one of them.
Determination happens in that interval, and responsibility gets earned
cumulatively by the record rather than claimed by origin. It stood queued as
conjecture until it survived an adversarial examination, and its promotion
to ratified doctrine followed the map's own rule — the author's ruling, on
the record, with measurement still explicitly ahead.

## 4 · The confluence

For most of the project's life the tributaries above sat in separate files.
In mid-2026 five of the project's own working structures turned out to wear
five names for one structure: the question minted from an unknown verdict,
the attention economy pricing it, the modality read off contested branches
of the record, the deliberative interval's traced considering, and the
mention-ascent machinery that lets a record cite ink without asserting it.
Every one of them amounts to a way of *holding alternatives against a
record*. An adversarial examination then added a sixth arrival nobody had
filed under logic at all: hope, the gap between the record and an
entertained-better, held as action-guiding.
[VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §8 ("The unification joint")
tells the joint, and
[ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md)
tells it at full historical length. It matters to *this* chapter because it
changed who the history serves. A reader from erotetics, from belief
revision, from the attention literature, from modal logic, or from the
philosophy of action now enters the same room through different doors.

## 5 · The proposition, and the invitation

The convergence claim this chapter has been building follows, stated in the
voice the project's vision assigns it: a proposition scribed into a wider
game, in which the traditions named above play as the other players.

> The operational Peirce core — **signs + sound transformation + earned
> record** — supplies the common formal substrate these traditions lacked.
> Each tributary found a real phenomenon; each lacked the same three-part
> floor; and the fact that one small core supplies the missing piece to
> doubts as different as Ashby's, Hamblin's, Berger & Luckmann's, and West's
> is evidence the core is load-bearing rather than local.

The claim *proposes*; it does not assert. Its warrant rests on more than
rhetoric. Each telling above carries a grade in the concordance map — built
code under a standing gate, a measurement under pre-registered priors, a
ruled doctrine, or a named and deliberately unexamined conjecture — and the
grades can fall as well as rise. And the claim stands *testable by
recognition*. If you work in one of these traditions, the telling of your
tradition's row either states its doubt and its gap fairly, or it does not.
If it does not — if this chapter mis-credits the phenomenon, mis-names the
lack, or claims machinery your literature already holds — then saying so
mounts no attack on this book. It makes a move in the game the book plays,
and the project records refutations with the same discipline it records
confirmations. The standing examinations
([ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md)) stand as the proof
that the invitation is meant.

One tradition escapes all grading, which is where this chapter began:
the lineage. Roberts, Zeman, Shin, Sowa, Dau, Pietarinen — the history told
in §2 forms no row of the map and carries no grade, because it holds no
concordance with the machinery. It *is* the machinery's warrant, and this
book can add only faithful implementation, honest citation, and the standing
offer to be shown wrong on both.
