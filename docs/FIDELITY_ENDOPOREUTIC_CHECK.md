# The Endoporeutic Check

> **What this is.** A reality check of Arisbe's implementation against a published
> scholarly account of Peirce's semantics for Existential Graphs — Ahti-Veikko
> Pietarinen's "The Compositionality of Concepts and Peirce's Pragmatic Logic"
> (2005). The author requested it mid-arc (2026-07-03), while work extended the
> automated Endoporeutic Game with the tropism module. It stands as a companion to
> [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md): where that document
> states Arisbe's departures from *Peirce*, this one checks the implementation
> against *the literature's reading of Peirce*, in the person of one careful
> witness, and records what corresponds, what diverges, and whether the
> divergences were chosen or accidental.

*The source: Pietarinen, Ahti-Veikko (2005). "The Composition of Concepts and
Peirce's Pragmatic Logic", in E. Machery, M. Werning and G. Schurz (eds), **The
Compositionality of Concepts and Meanings: Foundational Issues**, Ontos Verlag,
247–270. A copy is archived at
[references/The_Compositionality_of_Concepts_and_Pei.pdf](references/The_Compositionality_of_Concepts_and_Pei.pdf).
This note cites the Peirce manuscript (MS) and Collected Papers (CP) passages
below as Pietarinen quotes them.*

---

## 0 · Why this check, and what it can honestly claim

Arisbe's engine-room vocabulary — the peel, the Graphist and Grapheus, the
Endoporeutic Game, truth-as-habit — descends from Peirce through secondary
literature, working notes, and the project's own dogfooding. Does the
implementation still correspond to what the scholarship says Peirce built? The
question stays fair at any point in that descent. This note answers for one
substantial witness: Pietarinen's 2005 account of the **Endoporeutic Principle** (EP) and
the two-player semantic game, which he wrote against the backdrop of the
compositionality debate (Shin's proposal to re-found EGs on an inside-out,
negation-normal-form reading).

The check can claim *correspondence with a reading*, not proof of fidelity to
Peirce himself — the same modesty
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) §0 owes the tradition.
In one line, it found that **the implementation sits squarely on the
endoporeutic side of the argument the paper stages, and its two significant
divergences are standing doctrine, not drift.**

## 1 · The account being checked, in brief

Pietarinen's reconstruction has five load-bearing parts:

1. **The Endoporeutic Principle.** Interpretation proceeds **outside-in**:
   evaluation takes the outermost cuts against the model *M* first, then the
   inner, contextually-constrained ones; values instantiated at a ligature's
   outermost extremity propagate inward (the *selectives*). Crucially, the EP "was not a
   matter of reading the graphs, but a necessary consequence of the
   diagrammatisation" (§3) — "a nest sucks the meaning from without inwards unto
   its centre, as a sponge absorbs water" (MS 650: 18).
2. **The two-player game.** Evaluation proceeds as a make-believe dialogue
   between the **Graphist** (utterer; scribes the graphs, proposes
   modifications; the verifier) and the **Grapheus** (interpreter; **authorises
   the modifications**). Polarity assigns the choices: existential selections to
   the verifier, universal to the falsifier, with role-swap under cuts (§2).
3. **Truth as habit.** Truth of a graph consists in the existence of a winning
   strategy for the Graphist — in Peirce's own terms "a habit … of a tolerable stable
   nature" (MS 280: 30). The players share **common knowledge of the universe of
   discourse** — a common ground without which the discoursing could not proceed.
   (This Pietarinen restatement serves as the **scholarly citation** behind Arisbe's own
   settled two-player account; read
   [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §3 as the canonical
   frame — Graphist = proposal-side, Grapheus = Model-M-side, binary outcome, no referee, the
   Agonothetes not a player but the risked fate-selector. The citation stands uncontradicted:
   §3 names by *devotion* what Pietarinen names by *game role*.)
4. **Meaning as consequences.** "The meaning of any graph-instance is the
   meaning of the sum total or aggregate of all the propositions which that
   graph-instance enables the interpreter to scribe" (MS 280: 35) — explicitly
   both *experimental and evidenced facts* and *inferential propositions* by the
   transformation rules. Whence the paper's Pragmatic Principle of Context: "a
   proposition that has no consequences is meaningless" (§2).
5. **Against normal-form compositionality.** Against Shin's proposal to compile
   graphs to negation-normal form and read them inside-out, the paper argues the
   EP is constitutive: alternatives multiply the rule set and lose the dialogical
   structure; and the ligature examples (three drawings, one proposition — §6,
   Figs. 3–4) show that binding proceeds by **ligature extension**, not syntactic scope.

## 2 · Correspondences

**2.1 The peel is the EP.** `semantic_game.evaluate` reads a graph outside-in by
negation layer, querying the oracle at each negation-free stratum and recording
the march in a transcript. This gives the sponge passage its operational form.
What the implementation *refuses* matters just as much: evaluation never
compiles to a normal form. The evaluation walks the graph as asserted, on its
own area tree, taking the EP as constitutive rather than as one reading among
several. The wider correspondence doctrine
([EXACT_CORRESPONDENCE.md](EXACT_CORRESPONDENCE.md): the cut *is* its drawn
curve; containment is read off the drawn shape) applies the same commitment to
the picture itself.

**2.2 The two players, correctly assigned.** The paper divides the labor — the
Graphist scribes and proposes, the Grapheus *authorises the modifications* —
and that division survives end to end. In the automated game
([ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md)) the Graphist role
proposes (voices a doubt, scribes G) and the Grapheus role authorises how M may
revise (votes the minimal disposition). The truth-functional choice-making by
polarity — the *selectives* — lives in the peel and in the automated Grapheus'
minimax over it. The structured `winning_witness` / `counterexample` record the
plays of the paper's conventions 2–4, and the contest register's hot-seat game
keeps the literal two-player form.

**2.3 Truth as a "habit of a tolerable stable nature."** The deepest
correspondence, and the one that reaches the present frontier. Peirce identifies
truth with the existence of a *stable habit*, not a static satisfaction
relation. Arisbe's meta-learning layer measures precisely that stability:
[stickiness](GLOSSARY.md#stickiness), mechanism durability, decay-aware
stick-rates. The two executed live runs found that passive ingestion never
re-tests a settled habit at all — it revisits nothing — and that
finding mandated the **[tropism](GLOSSARY.md#tropism)** module, in which the
model's own state directs re-engagement, so that a settled habit deliberately
meets again the world that could break it. Put in the 1905 vocabulary: if truth
consists in a habit of tolerably stable nature, a system that never re-tests
its habits never engages the question of truth at all. The warm-set re-poll
gives operational form to the question whether a habit stays
"tolerably stable."

**2.4 Meaning as consequences — both registers.** The MS 280 formula, with its
explicit pairing of *experimental facts* and *inferential propositions*,
amounts to Arisbe's two registers. The Agon's testing/interpretation register
delivers the experimental side (the peel against a model, dispositions, model
revision), and the transformation chains deliver the inferential side.
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) makes the "outward-looking,
indefinitely-progressing principle for meaning" structural: the chain, not the
isolated graph, serves as the unit of meaning. The diachronic Universe of
Discourse embodies meaning-as-consequences as a data structure, and the modal
reading ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)) even gives the
formula's "under all circumstances" a mechanical form. Necessity there reads as
convergence across every legal trajectory.

**2.5 The Context Principle, operationalized.** "A proposition that has no
consequences is meaningless." [Disuse-decay](GLOSSARY.md#disuse-decay) enacts
this on the living sheet: when a relation stops participating in any round —
when it ceases to have consequences in the ongoing dialogue — the sheet erases
it. Nobody designed the connection from this passage; finding it already
implemented supplies the kind of convergence a reality check exists to catch.

**2.6 Ligature scope-indifference.** The paper's Figures 3–4 give three
drawings of one proposition: spots become bound the moment the ligature extends
to them, regardless of drawn scope. The three-regime correspondence doctrine
holds exactly this. Those variants form a *single* EGI; `same_graph` judges by
incidence and area rather than by ink; presentation operations move the ink
freely; and the per-ligature crossing-sequence invariant keeps the topology
honest across all of it.

**2.7 Common ground, constructed and shown.** The paper's players hold a common
ground "well understood between the two of them," without which the discoursing
fails. Arisbe renders that condition inspectable rather than presumed: the
render-M legend shows exactly how G's and M's vocabularies meet, the fragment
shows the neighborhood of M that G touches, and the report names any
**addressability gap** — the honest failure mode when common ground is absent
([DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md)).

## 3 · Divergences

The first two stand as doctrine, chosen, argued, and recorded elsewhere; this
section only registers that they count as divergences *from this account too*.

**3.1 Two-valued game over a held M → three-valued game over a queried M.**
Pietarinen's players evaluate against a completed model held in common
knowledge; truth there consists in the existence of a total winning strategy.
Arisbe's M stays **queried, not held**
([DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md)): the peel returns Kleene
three-valued verdicts, and UNKNOWN counts as a sound abstention at the
open-world horizon. The verdict-with-witness therefore amounts to a strategy
*certificate over the queried fragment*, not a total strategy. Arisbe pays that
price willingly, for the sake of playing the game against partial, low-warrant,
world-facing models — and where the paper assumes common ground as given,
Arisbe constructs and displays it (§2.7).

**3.2 Warrant, not satisfaction.** "The truth of the true consists in his being
satisfied with it" (MS 280: 29). Arisbe refuses that equation everywhere: the
correspondence attestation vouches for *correspondence, not truth*
([MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md)), and surviving the Agon
yields **warrant** (the ⚔ *withstood* badge), never Truth. This departs from
the quoted passage while staying close to Peirce's long-run fallibilism;
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) defends the same floor.

**3.3 Arisbe lifts the game a level.** The paper's players choose semantic
values *inside* one evaluation. The automated Endoporeutic Game's players argue
*around* the evaluation, about what a verdict should do to M (dispositions,
revision, branching). The semantic game survives intact inside the loop as the
incorruptible mechanical peel; the outer game remains a different game, one the
paper does not describe. The account itself half-licenses the lift (the Grapheus
"authorises modifications"; meaning includes the experimental register), but the
distinction deserves keeping crisp. **The calculus plays Peirce's game; the
agents play a game about its outcomes.**

**3.4 The third player.** The Agonothetes (judge) has no counterpart in the
two-player make-believe, and could not have one: Pietarinen's players never
disagree about a verdict, because the model settles it. The judge exists
precisely because the *outer* game (what to do with a verdict) admits
irreducible disagreement. Judgment resolves it, or the diachronic record
carries it forward as a branch.

**3.5 Continuity — the honest residue.** The paper's continuous predicates and
its topological reading of graph-morphing (synechism; §5) lie mostly beyond
Arisbe's scope. Two small, real implementations of the continuity intuition
exist: the ligature crossing-sequence invariant stays deliberately *topological,
not metric*, and the tension layout reads a line of identity as a taut
continuous thread. The check claims no more.

## 4 · What the check says about the trend

The implementation moves in one direction: dialogical, outside-in, refusing
normal-form compilation, habit-centered, meaning-as-consequences, common ground
constructed rather than presumed. That direction lands on the endoporeutic side
of the compositionality argument the paper stages against Shin, and it holds
consistently from the evaluation engine to the drawing doctrine. The
divergences that matter (3.1, 3.2) stand chosen and defended elsewhere in the
spine; the lift of the game (3.3, 3.4) counts as an *extension* the source
half-anticipates rather than a contradiction of it; the residue (3.5) stands
named.

One forward-looking corroboration deserves its own sentence. The account
identifies truth with a *stable habit*, and that identification independently
vouches for the arc's newest mandate — that only directed re-engagement
(tropism) can test the durability of what the game settles. The 1905
formulation and the 2026 run finding say the same thing.

---

*Companion to [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md),
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md),
[ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md),
[GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md), and
[DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md). Source PDF:
[references/The_Compositionality_of_Concepts_and_Pei.pdf](references/The_Compositionality_of_Concepts_and_Pei.pdf).*

**Created**: 2026-07-03 (the reality check requested and performed mid-arc,
between the tropism build and live run 3).
