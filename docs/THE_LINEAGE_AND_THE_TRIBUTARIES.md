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
chapter refuses the flattening, because the two ancestries are not the same
kind of thing.

The first ancestry is a **lineage** in the strict sense: a chain of scholars
who took Peirce's Existential Graphs — hand-drawn, scattered across
manuscripts, half-legible even to sympathetic readers — and made them into
mathematics that can be proved sound. Arisbe's engine applies that
mathematics; every guarantee the system makes, it makes *on their credit*.
If the lineage's theorems failed, nothing downstream — the correspondence
invariant, the game, the autonomous loops — would mean anything at all. That
is why the project's concordance map rules that "the formalization lineage is
not a row": you do not grade your own warrant.

The second ancestry is a set of **tributaries**: twentieth-century traditions
that never touched Existential Graphs, but each of which found a real
phenomenon — a doubt worth a research program — and each of which, on the
project's reading, ran short of the same missing substrate: a way to hold a
model *in signs*, transform it only *soundly*, and keep an *earned record* of
every move. That reading is the proposition this chapter builds toward, and
it is the part a reader is invited to refute.

## 2 · The lineage: from manuscript to mathematics

**Peirce** (1839–1914) invented the Existential Graphs in the late 1890s and
worked on them to the end of his life, calling them "moving pictures of
thought" and describing their reading discipline as *endoporeutic* — meaning
flows from the outside of a nest of ovals inward. He left behind a system of
astonishing reach (the Alpha graphs for propositional logic, Beta for
quantification and identity, Gamma for modality and abstraction) and almost
nothing a modern logician would accept as a soundness proof.

**J. Jay Zeman** (dissertation, 1964) supplied the first: a demonstration
that Alpha and Beta are exactly equivalent to propositional and first-order
logic, and that the Gamma broken-cut fragment corresponds to the modal
systems S4/S5. Zeman made the graphs *answerable* — after him, "the picture
never lies" was a claim that could in principle be checked.

**Don D. Roberts** (monograph, 1973) did the historian's share: the
comprehensive catalogue of what Peirce actually drew, period by period,
including the tangled Gamma strands — modality, higher-order quantification,
metalanguage — that Peirce himself never disentangled. Roberts is the reason
later formalizers knew *what* there was to formalize, and the reason this
book can separate Peirce's modal program from his second-order one (a
separation Arisbe leans on; see
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)).

**Sun-Joo Shin** (*The Iconic Logic of Peirce's Graphs*, 2002) changed what
the graphs were *for*. Against a century of reading diagrams as informal
crutches, Shin argued that the graphs' iconicity is a logical feature —
that some inferences are *visible* in the drawn form in a way no sentential
notation matches. Arisbe's whole drawn-form ambition — the insistence that
the picture is a first-class carrier of the proposition, not an illustration
of it — is Shin's thesis taken as an engineering requirement.

**John F. Sowa** is the living bridge between the graphs and working
knowledge representation. His conceptual graphs descend explicitly from EGs;
his interchange notations — EGIF for the graphs themselves, CGIF within the
ISO/IEC 24707 Common Logic standard — are the linear forms Arisbe implements
(implements, not invented: the formats are his design and the standard's);
his account of the EG↔discourse-representation isomorphism (tracing to Kamp)
and his 2011 telling of the endoporeutic game — from which Arisbe takes even
the word "peel" — supplied the vocabulary this book reasons in. Where the
earlier lineage made the graphs answerable, Sowa made them *usable*.

**Frithjof Dau** (*Mathematical Logic with Diagrams*, habilitation) is the
culmination and the bedrock. Dau gave the graphs a complete modern
formalization — the graph-with-cuts structure Arisbe's data model implements,
the six transformation rules (erasure, insertion, iteration and
de-iteration, double-cut addition and removal) with soundness proved, and
the translations between graphs and first-order formulas that anchor the
linear side of the correspondence. Arisbe's engine is Dau's calculus,
deliberately unimproved; the protected core test suite exists to keep it so.
Two honesty notes belong in the record beside the credit: Dau is the
de-facto standard formalization *for software*, but not uncontested in
philosophy — the standard survey literature treats Zeman, Roberts, and Shin
and omits him — and, as far as the project could find, no machine-checked
formalization of his calculus exists anywhere; Arisbe's executable test
suite is the closest operational guarantor located, and a true mechanization
is named as a field contribution waiting to be made.

**Ahti-Veikko Pietarinen** holds a special position: he is both lineage and
living interlocutor. His *Signs of Logic* (2006) and related work formalized
the endoporeutic, game-theoretic reading Arisbe's evaluation engine
implements (the project keeps a documented conformance check against his
account, divergences listed —
[FIDELITY_ENDOPOREUTIC_CHECK.md](FIDELITY_ENDOPOREUTIC_CHECK.md)); and Ma &
Pietarinen (2018) gave sound and complete graphical calculi for fifteen
modal logics using Peirce's own broken cut — the rehabilitation of Gamma
that Arisbe's no-modal-mark architecture deliberately declines to follow.
That choice is argued as adequacy for this architecture, never as a
refutation of Gamma, and the argument's honest accounting of what it forgoes
is kept where it can be attacked
([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)).

That is the lineage. Everything else in this chapter stands on it.

## 3 · The tributaries: doubts raised, machinery lacked

Told as history, roughly in the order the doubts were raised. Each entry
credits the phenomenon first — every one of these traditions found something
real — and then names the machinery the tradition itself identified as
missing, or that its later readers found wanting. The one-line versions,
with evidence and grades, are the concordance map's rows
([CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md)); the
tellings here are the map read as narrative.

**The Umwelt (von Uexküll, 1934; Hoffmeyer and biosemiotics after him).**
Before anyone built a model-holding machine, von Uexküll saw that every
organism already carries one: its world is not *the* world but the slice its
sign-repertoire can address — the Umwelt — closed by a functional circle of
perceiving and acting. Modern biosemiotics read this through Peirce's sign
theory and made the fit explicit. What the tradition never had was
*soundness*: a membrane, but no calculus behind it — no way to say which
transformations of the organism's sign-world preserve what it knows.
Arisbe's vocabulary-bounded horizon ("enough of the model is what the
proposal touches") is an Umwelt with a calculus inside it.

**Cybernetics (Wiener, 1948; Ashby, 1952; Conant & Ashby, 1970).** The
mechanists' doubt: must every good regulator of a system be a *model* of
that system? Conant and Ashby proved the affirmative, and Ashby's Homeostat
physically demonstrated remodeling driven by environmental friction. This is
the one-line external justification for the model M at Arisbe's interior —
anything that copes with a world must carry a model of it. What cybernetics
lacked was an *assertion calculus*: the model was held in wiring or in
variables, with no licensed way to assert, retract, or test a piece of it.
Arisbe's residence discipline — the model held in signs, revised only by
licensed rule applications, every change an acknowledged act — is that lack
supplied, and it is held by a standing test gate.

**Artificial life (von Neumann's automata; Conway's Game of Life, 1970).**
The doubt: can iterated simple steps yield unscripted global order? Conway's
answer — gliders, guns, universal computation out of a two-state rule —
shaped Arisbe's automated loop directly, and the *differences* became
doctrine: Life advances by a fixed rule on a closed dynamics, so nothing in
it asserts, and no outcome is negotiated. Arisbe's generation is a *round of
a game* — the rule that fires is a disposition chosen and negotiable — and
what bounds the open sheet is selection from outside, not the rule. The
loop is built and gated; the grander reading (that a negotiated sheet
achieves what fixed rules cannot) stays a deliberately unmeasured
conjecture, and the map says so.

**Erotetics (Hamblin, 1958; Belnap; Wiśniewski's inferential erotetic
logic).** The logicians of questions established the doubt that questions
are first-class logical objects with their own inferential structure — not
mere absences of assertion. What the tradition lacked was an *economy*: no
cost, severity, or decay on the standing question, so nothing in the logic
says which open question deserves the next hour. Arisbe's answer — the
question minted from an evaluation's UNKNOWN verdict, traced for the
consequences of each answer, priced by an attention economy, settled only by
a licensed step the record can cite — is told at full length in its own
history ([ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md));
this chapter does not repeat it, because that document is the model this
chapter imitates.

**The sociology of knowledge (Berger & Luckmann, 1966).** Their doubt: how
does the subjective become objective — how does a judgment escape its maker
and harden into an institution? Their answer, reciprocal typification of
habitualized actions, came with a warning the project treats as a
boundary-stone: institutionalization *cannot occur in an individual*. What
the tradition lacked was mechanism — a description of typification with
nothing that executes it. Arisbe supplies an executing model *of* the
process and holds Berger & Luckmann's own line against over-reading it: one
instance simulating a federation models an institution and does not
constitute one ([THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md)).

**Evolutionary epistemology (Popper; Campbell, 1974).** Knowledge grows by
conjecture and refutation; variation is blind, retention selective. The
project accepts the schema and maps its own loop onto it — proposer as
variation, evaluation as selection, decay as the bound on retention. What
the tradition lacked was a *record*: selection with no earned, replayable
transcript, so the history of a belief's survival is gone the moment it has
survived. Arisbe's practice of pre-registered priors, mechanical verdicts,
and refuted priors kept on the record is Lakatos's research-programme
discipline enforced by machinery — exercised on every logged run, and graded
on the map as practice rather than as a measured claim.

**Belief revision and reason maintenance (Doyle, 1979; de Kleer, 1986;
Alchourrón, Gärdenfors & Makinson, 1985).** The doubt: how does a rational
corpus absorb a contradiction? AGM axiomatized the answer as postulates on
set operations; truth-maintenance systems implemented dependency tracking.
What both lacked, on this reading, is *ink*: operators constrained from
outside, with no drawn, derivation-carrying step — a revision happens, but
nothing in the corpus *is* the revision. Arisbe's disposition taxonomy
executes revisions as licensed rule applications whose derivations ride on
the record, so the justification structure is made of sound steps rather
than dependency links.

**Active inference (Helmholtz's unconscious inference; Friston, 2006–).**
The closest formal neighbor: perception and action as one economy of
prediction error, the boundary between model and world formalized as a
Markov blanket — independently coined, doing the same work as Arisbe's
membrane. The difference the project holds up front: free-energy
minimization is a gradient flow that keeps no inspectable chain, where
Arisbe's updates are recorded, warranted, rule-licensed steps; and a
three-valued verdict distinguishes abstention from error, a distinction a
scalar surprisal collapses. What the neighbor has that Arisbe lacks is
named with equal honesty: the action arm — acting on the world to reduce
expected error — which remains the project's designed, unbuilt "directed
engagement."

**Scaling science (West, *Scale*, 2017).** West's doubt: do aggregated
units obey discoverable scaling laws — and what does the unit's economics
determine? This is the one tributary the project has *measured* against
pre-registered priors rather than only read: five experiments and a rider
(the E-series, 2026) asked West's question of units whose metabolism is
knowledge maintenance, and found a federation ~5× cheaper than a monolith at
equal durability, a real diseconomy exponent avoided by coordination
discipline, an interior optimum that is a granularity rather than a
partition, and a multi-basin landscape in which balance strands. The refuted
priors stand in the map's row beside the held ones. What West's framework
lacked, on this reading, is what the unit *does* — an economics of the unit
without its semantic work — and the return-gift offered back is the
conjecture that the allocation layer of such units is vectorial, not scalar
(a self-contained methods account is
[WEST_METHODS_NOTE.md](WEST_METHODS_NOTE.md)).

**Anthropology against the ladder (Graeber & Wengrow, *The Dawn of
Everything*, 2021).** Their doubt: was there ever one ladder of social
development — or many viable forms from the start? The project adopts the
*negative* claim only — plurality, no teleology — and finds its own
plurality in the measured multi-basin landscape above; their historical
evidence of deliberate, reversible movement between social forms is read
beside the model's finding that escaping a dear basin takes coordination,
recorded as a finding about the model, never about history. What the
tradition lacked was instrumentation — evidence of plurality with no cost or
durability measure on a settlement — which is exactly what the model can
supply *for its own synthetic worlds*, and only for them.

**The deliberative interval (the project's own tributary, examined 2026).**
Last, a reading Arisbe contributes rather than inherits: that the freedom
worth the name lives in the determined *considering* between the branching
of alternatives at a doubt and the licensed resolution of one of them — the
interval where determination happens, with responsibility earned
cumulatively by the record rather than claimed by origin. It was queued as
conjecture until it survived an adversarial examination, and its promotion
to ratified doctrine happened by the map's own rule: by the author's ruling,
on the record, with measurement still explicitly ahead.

## 4 · The confluence

For most of the project's life the tributaries above were separate files.
In mid-2026 five of the project's own working structures — the question
minted from an unknown verdict, the attention economy pricing it, the
modality read off contested branches of the record, the deliberative
interval's traced considering, and the mention-ascent machinery that lets a
record cite ink without asserting it — turned out to be one structure
wearing five names: every one of them is a way of *holding alternatives
against a record*. An adversarial examination then added a sixth arrival
nobody had filed under logic at all: hope, as the gap between the record and
an entertained-better held as action-guiding. The joint is told in
[VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §8 ("The unification joint") and
at full historical length in
[ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md);
it matters to *this* chapter because it changed who the history is for. A
reader from erotetics, from belief revision, from the attention literature,
from modal logic, or from the philosophy of action now enters the same room
through different doors.

## 5 · The proposition, and the invitation

Here is the convergence claim this chapter has been building, stated in the
voice the project's vision assigns it — a proposition scribed into a wider
game, in which the traditions named above are the other players:

> The operational Peirce core — **signs + sound transformation + earned
> record** — is the common formal substrate these traditions lacked. Each
> tributary found a real phenomenon; each was missing the same three-part
> floor; and the fact that one small core supplies the missing piece to
> doubts as different as Ashby's, Hamblin's, Berger & Luckmann's, and West's
> is evidence the core is load-bearing rather than local.

The claim *proposes*; it does not assert. Its warrant is not rhetorical: each
telling above carries a grade in the concordance map — built code under a
standing gate, a measurement under pre-registered priors, a ruled doctrine,
or a named and deliberately unexamined conjecture — and the grades can fall
as well as rise. And the claim is *testable by recognition*: if you work in
one of these traditions, the telling of your tradition's row is either a
fair statement of its doubt and its gap, or it is not. If it is not — if the
phenomenon is mis-credited, the lack mis-named, or the machinery claimed
here already exists in your literature — then saying so is not an attack on
this book; it is a move in the game the book is playing, and the project
records refutations with the same discipline it records confirmations. The
standing examinations
([ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md)) are the proof
that the invitation is meant.

One tradition is exempt from all grading, which is where this chapter began:
the lineage. Roberts, Zeman, Shin, Sowa, Dau, Pietarinen — the history told
in §2 is not a row of the map and carries no grade, because it is not a
concordance with the machinery. It *is* the machinery's warrant, and the
only thing this book can add to it is faithful implementation, honest
citation, and the standing offer to be shown wrong on both.
