# Meaning by History

**Why the path belongs to the sign — and the sneak that would reify it**

*A philosophy-spine companion to [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md),
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md), and
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md).*

> **What this is.** Peirce's Endoporeutic Game reads a graph *from the outside in* — meaning
> accrues by **context**: which cut encloses what, which model the assertion peels against.
> But re-reading Berger & Luckmann, one notices a second source. Meaning accrues by **history**
> too. Two graphs can look identical yet arrive at that form by different paths through
> their [Universe of Discourse](GLOSSARY.md#uod). This essay locates that
> idea precisely in Peirce (it lives there, at a specific level of the sign), shows that Arisbe
> already builds the distinction into its architecture, and then turns the point *critically*:
> the same history that carries meaning must not be **reified** into a telos scribed on the
> blank sheet. That last danger names the field guide's ninth dragon.

## Two halves of meaning

The [peel](GLOSSARY.md#peel), the outside-in reading Arisbe operationalizes in Agon
(`src/semantic_game.py`, `SemanticGame.evaluate`), gives the *evaluative* half of meaning. It takes
a **finished** graph and asks what it says, and whether that holds in a model. Call this meaning by
context. The nesting of cuts fixes scope, and the surrounding model fixes reference. It reads
synchronically — a photograph.

But evaluation does not exhaust Peirce's theory of meaning. On the wider theory a sign's
meaning takes shape from where it *came from*: the prior signs that determined it, the habits that
interpret it, the collateral experience the interpreter brings. That names meaning by history, and
it runs diachronic — a film. When two drawings coincide, do they make *the same sign*? **At one
level yes, at another no** — and Peirce gives us the exact levels.

## Same picture, different argument

Peirce classifies signs, by the interpretant they call for, into a trichotomy: **Rheme /
[Dicisign / Argument](GLOSSARY.md#dicisign-and-argument)**. A **Dicisign** (a Dicent sign) asserts
a proposition — the kind of thing that holds true or false. An **Argument** names a sign whose
interpretant presents it *as the conclusion of a lawful process*; an argument **carries its own
genesis**.

The puzzle turns on this joint. Two Existential Graphs identical in form assert the same
**proposition**, the same Dicisign. At *that* level history simply does not matter, and rightly so.
The soundness of Dau's calculus and the correspondence check (§3.3) between them *guarantee*
exactly this: equivalent graphs denote the same object, whatever route reached them. But the same
conclusion can end two different demonstrations, and *as demonstrations* those make
two different **Arguments**. The path-dependence you feel when you say "these two arrived
differently" names something real, and it lives at the Argument level, not the Dicisign level.

So the dictum "moving picture of thought" cuts deeper than it first appears. The graph stands as a
Dicisign. The *transformation* of graphs — the proof, the derivation, the reasoning that produced
this graph rather than merely coinciding with it — stands as an Argument. Form fixes the
proposition; only history supplies the argument.

Note carefully that this distinction runs **orthogonal** to the one Arisbe already draws between the
*demonstrative* and *assertoric* registers (a derived theorem versus a posited premise — see
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §4, and "the two registers" in
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md)). That distinction sorts graphs by *how they got their
warrant*. The present one cuts finer: even **within** the derived register — two graphs both honestly
derived, both true — two identical final forms can make different arguments, because they descend
through different steps. Register gives one axis of history; the argument's path gives a second.

## Why the correspondence check cannot carry it

Why can the drawing itself not hold the difference? The
correspondence check (§3.3) attests that a picture and its proposition denote the same graph — and
nothing more. It works **form-level and history-blind**; as [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md)
puts it (floor #3), Arisbe attests *correspondence, not truth*. Two same-form graphs pass §3.3
identically because §3.3 cannot see where either came from. Something other than the drawing
therefore *must* carry the Argument-level difference — namely the preserved **history**. This marks
no shortcoming of the correspondence check; it marks a division of labour. The picture carries the
proposition; the chain carries the argument.

## What Peirce already says

The historicity of meaning does not come as a modern gloss on Peirce; it stands as his own
doctrine, stated flatly.

- **Symbols grow.** "Symbols grow," Peirce writes; a symbol "comes into being by development out
  of other signs," and once in being "the body of the symbol changes slowly, but its meaning
  inevitably grows, incorporates new elements and throws off old ones" (c. 1893–1903). Meaning
  names something a symbol *accumulates over its life*, not a function read off its present shape.
- **Semiosis is an unbroken chain.** In "Some Consequences of Four Incapacities" (1868) a
  *previous* thought determines every thought-sign, which addresses a *subsequent* interpretant; no
  sign arises from nothing. A sign's identity includes its genetic relation to what determined it.
- **The ultimate interpretant is an acquired habit.** In the 1907 "Pragmatism" manuscript the
  final logical interpretant amounts to a *habit-change* — and a habit has a history of takings.
  The meaning a sign finally delivers consists in a disposition built up in time.
- **Collateral experience.** To interpret any sign at all, Peirce insists, one must already be
  acquainted with its object *collaterally* to the sign. Two interpreters — or one interpreter at
  two times — read the "same" sign differently because they bring different prior acquaintance.
  This stands as the individual-history analogue of Berger & Luckmann's social *stock of knowledge*.
- **Synechism.** Even the laws — the habits of nature — evolve; the universe is, for Peirce, "a
  developing argument." History goes all the way down.

The endoporeutic (outside-in) reading thus gives the *evaluative* face of a semiotic that runs,
in its depths, thoroughly historical.

## Where Arisbe already keeps the two apart

Strikingly, Arisbe's architecture already holds the Dicisign and the Argument as
**distinct, computable objects** — arguably more operationally than the secondary literature does.

- **`same_graph` answers "same proposition?"** (`src/eg_navigation.py`, full Alpha/Beta
  isomorphism). It serves as the authority for proof-conclusion equality, the Dicisign level. It
  stays deliberately **history-blind**: two graphs reached by any two routes test equal iff they
  assert the same proposition.
- **The transformation chain *is* the argument.** A `TransformationChain` of `ChainStep`s
  (`src/tomos_service.py`) records the path: each step names its rule, its parent state
  (`from_state_id`) and its result (`to_state_id`). A chain *branches* when two steps share a
  parent and *converges* when two share a result — so two arguments reaching one conclusion appear
  as exactly two lines meeting at a shared `to_state_id`. As [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md)
  puts it, "the chain, not the snapshot, is the unit of meaning." `same_graph` says *same
  proposition*; the chain says *different argument*.
- **The warrant gradient makes meaning-by-history a badge.** `standing_of` (`src/provenance.py`)
  projects a graph's [warrant](GLOSSARY.md#warrant) as a gradient — **blank ○** ▸
  **posited ◇** ▸ **derived ⛓** ▸ **withstood ⚔** — and which face a graph wears depends on *the
  path that reached it*, not its form. Two identical EGIs can carry different standing. "Fact,"
  in this reading, "is the last-standing trajectory," never a property of the ink. That renders
  meaning-by-history as a computable attribute of a node.
- **The modal lens reads necessity off trajectories.** `src/modal_query.py` reads ◇ and □ off the
  branching history: ◇φ reads "some legal trajectory scribes φ," □φ "every legal trajectory scribes
  φ." Whether a proposition counts as *necessary* states a fact about *which histories reached it* —
  read from the path, not the picture. (See [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md).)

The synchronic/diachronic split of the [UoD](GLOSSARY.md#uod) supplies precisely
the machinery that lets Arisbe say both things at once: the picture carries the proposition, and
the history carries the argument.

## Two histories, one graph — worked

Across *two* universes the point comes easy: `(mortal Socrates)` means one thing in a UoD of
Greek biography and another in a UoD of worked syllogisms. But there the two graphs remain mere
*homographs*, tokens in separate books, and no one feels tempted to confuse them. The sharper case,
the one that shows history doing work the picture cannot, puts **two histories to the same graph
inside one UoD**, where the derivation history genuinely *converges*: two `ChainStep` lines meet
at a shared `to_state_id`, the same synchronic frame reached by different roads.

**Example A — one conclusion, two grounds.** A single UoD opens with two facts and two implications
on its sheet:

```
(sprinkler_on)   ~[ (sprinkler_on) ~[ (grass_wet) ] ]
(rained)         ~[ (rained)        ~[ (grass_wet) ] ]
```

— *if the sprinkler is on, the grass is wet; if it rained, the grass is wet.* The grass is wet twice
over, and two histories now reach the very same conclusion graph `(grass_wet)`:

- **History A** deiterates `(sprinkler_on)` from the first scroll (a copy of the fact already
  on the sheet) and removes the resulting double cut — `(grass_wet)` *because the sprinkler was on*.
- **History B** does the same with `(rained)` and the second scroll — `(grass_wet)` *because it
  rained*.

Erase the scaffolding (erasure comes free on the positive sheet) and both histories leave the sheet
asserting exactly `(grass_wet)`: byte-for-byte the same graph, and `same_graph` returns true. Yet
the two make different **Arguments**, and the difference does not sit idle. Suppose a later round of
the game retracts `(sprinkler_on)`; a challenge shows the sprinkler was off all week. The
synchronically identical `(grass_wet)` now behaves differently depending on which history laid it
down. History A's grass-wet stands **undercut**, its only recorded ground gone. History B's stands
**untouched**, the rain still standing. *Same picture, different future — because different past.* A
claim's vulnerability lies written in its history, not its form; Arisbe keeps that history in the
chain precisely so the undercut one can fall and the other be spared.

**Example B — proved versus observed.** In the same UoD, let the shared graph be a lone assertion
`(grass_wet)`. One history *derives* it, a theorem read off premises since erased, and it wears the
**derived ⛓** face: sound *given its base*. Another history *posits* it — someone looked out the
window — and, sent to Agon and surviving, it wears the **withstood ⚔** face: warranted *because it
met the world and held*. `same_graph` cannot tell the two apart; `standing_of` can, because standing
reads from the path, not the picture. A proof and an observation may arrive at the identical
sentence and still not make the same sign.

Both examples teach one lesson: the shared part names the Dicisign; the differing part — the ground,
the defeasibility, the standing — names the Argument, and it lives in the history the diachronic
UoD keeps.

## The sneak: reifying a history

Here the essay turns critical, and here Berger & Luckmann earn their place. They name the
central sin of the sociology of knowledge **[reification](GLOSSARY.md#reification)**: treating a
humanly produced, history-bound product as if it were a natural, given, authorless fact —
forgetting its genesis. And their account of *why* it happens names exactly the mechanism this essay
has been describing: **sedimentation**. The longer a meaning gets carried, the more it gets used and
re-used, the more its authored, path-bound origin fades from view and the more it comes to *look
like* brute fact. History makes reification easy.

Now the specific danger. A history — a chain, a trajectory through a UoD — does not only *carry*
meaning; it also *implies a shape*. A sequence of steps suggests a direction: "this inquiry was
always heading toward X"; "there is a progression here." The sneak lifts that implied **telos**
*out of* the diachronic record and **scribes it on the blank sheet of assertion** as though it were
an earned proposition. That amounts to reification in Arisbe's own idiom: forgetting that the telos
remains an artifact of the path, the momentum of one history, and posting it as a fact about the
world.

The error seduces precisely because the machinery that makes history meaning-bearing (good,
necessary, the whole first half of this essay) also makes the telos *available* for smuggling. The
remedy does not lie in forgetting the history. It lies in keeping the history in its place.

## Four guards Arisbe already carries

Reassuringly, Arisbe already holds four locks against this particular door. Each was built for its
own reasons; together they amount to exactly the anti-reification discipline the danger demands.

1. **The mode contract — no inheritance onto the sheet.** A graph reaches the attested corpus, as
   [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) states it, "*only* by being tested through Agon, or as
   a style-only reprojection of an already-attested graph." "Promotion is the crux,"
   [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) says of the regime-1 → regime-2 transition; and "the
   workshop has no direct §3.3-only path into the corpus." A telos smuggled from a path was never
   *peeled*; it has not earned the sheet. No channel lets a history's mere momentum become an
   assertion.

2. **The warrant floor — competence, never Progress.** Arisbe's standing gradient "must read as
   in-context competence, **never** as worth, nearness, or context-free Progress"
   ([ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md), Examination II; and the standing floor,
   *"warrant = in-context competence, never worth/Progress"*). A "progression" names exactly the
   worth-ladder the floor was written to refuse. The gradient measures *what has withstood challenge
   here*, not *where the story is going*.

3. **The modal reading — ◇ is not □.** A telos read off **one** history counts, in the trajectory
   reading, as at most ◇: *some* legal trajectory scribes it. To assert it as settled claims □:
   *every* legal trajectory converges on it. But "possibility is the branching of legal
   trajectories, necessity is their convergence" ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)) —
   and one path makes a branch, not a convergence. So the reification amounts, precisely, to a
   **◇ misread as □**: mistaking the direction *a* history took for a necessity *all* histories
   share. The modal lens will not report □ for something only one trajectory reached; the guard
   works mechanically.

4. **The enclosure cap — a tendency is sayable *within* a context, malformed as the structure of
   the whole.** This guard cuts deepest, and it comes from Peirce himself. A real growth-tendency —
   synechism's continuity, "the growth of concrete reasonableness" — is, as
   [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) puts it, "won, not wagered": "sayable and
   operative wherever a context encloses it, and enclosure-malformed only when scribed as the
   operative structure of the unenclosable whole (the outermost sep cannot be drawn)." A telos
   stands legitimate *enclosed in a context* — under a cut, inside a scroll, as an antecedent one
   conditions on. It becomes malformed exactly when scribed flat, on the outermost sheet, as the
   structure of everything. Reifying a history means drawing the sep that cannot be drawn.

## The nuance: a telos is a hope, not an assertion

None of this says "no telos, ever." Peirce himself affirms one: the growth of concrete
reasonableness, the agapism of "Evolutionary Love" (1893). The point concerns a discipline of
*register*, not a denial. Peirce's telos stands as a **regulative hope** — a
[would-be](GLOSSARY.md#would-be--de-inesse), a habit that would hold across every course of
experience — not a *de inesse* assertion, a flat fact on one sheet. To scribe the would-be as
though it were de inesse commits a category error Arisbe already names: reading a strict,
across-all-courses habit (□G over the branching history) as a plain present assertion. Keep the
telos where it belongs, a hope that *regulates* inquiry, drawn under enclosure, and it stays sound.
Post it on the blank sheet as an earned fact, and it becomes the sneak.

## The synthesis, and the dragon

The two halves meet here. History **does** carry meaning: the argument, not just the
proposition, belongs to the sign, and Arisbe keeps it, auditable and replayable, in the diachronic
UoD. And that same history must **not** suffer reification: no telos it merely implies may cross
onto the blank sheet except by earning it through the contest. The synchronic/diachronic split
makes exactly both possible at once. The path lives at the Argument level, in the chain; the sheet
stays free of any telos the path did not earn.

That double discipline — *keep the history, do not reify it* — names the ninth dragon of the
[field guide](FIELD_GUIDE_AND_DRAGONS.md): **the reified telos.** The antidote compresses this
whole essay into one breath: a progression counts as a feature of a path, not a fact of the world;
the history remains precious, and it belongs in the record, not on the sheet.

## Sources & further reading

**Peirce (primary).** "Symbols grow" and "its meaning inevitably grows, incorporates new elements
and throws off old ones" — Collected Papers CP 2.302 (c. 1893) and CP 2.222 (1903). The chain of
thought-signs — "Some Consequences of Four Incapacities" (1868, CP 5.283 ff). The final logical
interpretant as acquired habit — the "Pragmatism" survey (1907, CP 5.464–496). Collateral
experience — the letters to Lady Welby (1908–09) and *Prolegomena to an Apology for Pragmaticism*
(1906). Synechism and agapism — "The Law of Mind" (1892) and "Evolutionary Love" (1893). The
Rheme / Dicisign / Argument trichotomy — the 1903 Syllabus (CP 2.243–253). *(CP locators are given
for the reader's convenience; the prose follows the house style of citing work and phrase.)*

**Secondary.** T. L. Short, *Peirce's Theory of Signs* (2007), esp. the chapter "How Symbols Grow"
— the systematic modern treatment of interpretants as developmental. Ahti-Veikko Pietarinen,
*Signs of Logic* (2006) and the endoporeutic-method entry (Commens) — the game-theoretic
formalization of the outside-in reading, i.e. the *evaluative* half. Frederik Stjernfelt,
*Diagrammatology* (2007) and *Natural Propositions* (2014) — on the Dicisign and diagrammatic
reasoning. Vincent Colapietro, *Peirce's Approach to the Self* (1989) — the interpreting self as
historically constituted, the nearest Peircean neighbour to Berger & Luckmann's socially
constructed subject.

**The sociology bridge, and an open joint.** Peter Berger & Thomas Luckmann, *The Social
Construction of Reality* (1966) — *reification* and *sedimentation*. Their lineage runs through
Alfred Schütz to Husserl's account of *sedimentation* and the historicity of ideal objects (*The
Origin of Geometry*). There is genuine comparative work on Peirce and Husserl (the "semiotic
lifeworld" literature; Peirce on collateral experience as the lifeworld hook). But a *direct*
treatment tying Peirce's Argument/habit doctrine to Berger & Luckmann's reification appears to be
**open** — a bridge one might build rather than cite.

---

*Companion to [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md), [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md), and
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md); the field guide's
[dragon 9](FIELD_GUIDE_AND_DRAGONS.md). Machinery: `src/eg_navigation.py` (`same_graph`),
`src/tomos_service.py` (`TransformationChain`), `src/provenance.py` (`standing_of`),
`src/modal_query.py` (the modal lens), `src/semantic_game.py` (the peel).*

**Created**: 2026-07-08.
