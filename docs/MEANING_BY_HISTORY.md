# Meaning by History

**Why the path is part of the sign — and the sneak that would reify it**

*A philosophy-spine companion to [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md),
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md), and
[FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md).*

> **What this is.** Peirce's Endoporeutic Game reads a graph *from the outside in* — meaning
> accrues by **context** (which cut encloses what, which model the assertion is peeled against).
> But re-reading Berger & Luckmann, one notices a second source: meaning accrues by **history**
> too. Two graphs can look identical yet have arrived at that form by different paths through
> their [Universe of Discourse](GLOSSARY.md#uod). This essay locates that
> idea precisely in Peirce (it is there, at a specific level of the sign), shows that Arisbe
> already builds the distinction into its architecture — and then turns the point *critically*:
> the same history that carries meaning must not be **reified** into a telos scribed on the
> blank sheet. That last danger is the field guide's ninth dragon.

## Two halves of meaning

The [peel](GLOSSARY.md#peel) — the outside-in reading Arisbe operationalizes in Agon
(`src/semantic_game.py`, `SemanticGame.evaluate`) — is the *evaluative* half of meaning. It takes
a **finished** graph and asks what it says, and whether that holds in a model. This is meaning by
context: the nesting of cuts fixes scope, and the surrounding model fixes reference. It is
synchronic — a photograph.

But Peirce's theory of meaning is not exhausted by evaluation. On the wider theory a sign's
meaning is shaped by where it *came from* — the prior signs that determined it, the habits that
interpret it, the collateral experience the interpreter brings. That is meaning by history, and
it is diachronic — a film. The question this essay answers is: when two drawings coincide, are
they *the same sign*? The answer is: **at one level yes, at another no** — and Peirce gives us the
exact levels.

## Same picture, different argument

Peirce classifies signs, by the interpretant they call for, into a trichotomy: **Rheme /
[Dicisign / Argument](GLOSSARY.md#dicisign-and-argument)**. A **Dicisign** (a Dicent sign) asserts
a proposition — it is the kind of thing that is true or false. An **Argument** is a sign whose
interpretant presents it *as the conclusion of a lawful process*; an argument **carries its own
genesis**.

This is the joint the puzzle turns on. Two Existential Graphs identical in form assert the same
**proposition** — the same Dicisign. At *that* level history is simply irrelevant, and rightly so:
that is what the soundness of Dau's calculus and the correspondence check (§3.3) between them
*guarantee* — equivalent graphs denote the same object, whatever route reached them. But the same
conclusion can be the terminus of two different demonstrations, and *as demonstrations* those are
two different **Arguments**. The path-dependence you feel when you say "these two arrived
differently" is real, and it lives at the Argument level, not the Dicisign level.

So the dictum "moving picture of thought" cuts deeper than it first appears. The graph is a
Dicisign; the *transformation* of graphs — the proof, the derivation, the reasoning that produced
this graph rather than merely coinciding with it — is an Argument. Form fixes the proposition;
only history supplies the argument.

Note carefully that this is **orthogonal** to the distinction Arisbe already draws between the
*demonstrative* and *assertoric* registers (a derived theorem versus a posited premise — see
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §4, and "the two registers" in
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md)). That distinction sorts graphs by *how they got their
warrant*. The present one is finer: even **within** the derived register — two graphs both honestly
derived, both true — two identical final forms can be different arguments, because they descend
through different steps. Register is one axis of history; the argument's path is a second.

## Why the correspondence check cannot carry it

It is worth being explicit about why the drawing itself cannot hold the difference. The
correspondence check (§3.3) attests that a picture and its proposition denote the same graph — and
nothing more. It is **form-level and history-blind**; as [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md)
puts it (floor #3), Arisbe attests *correspondence, not truth*. Two same-form graphs pass §3.3
identically because §3.3 cannot see where either came from. The Argument-level difference therefore
*must* be carried somewhere other than the drawing — namely in the preserved **history**. This is
not a shortcoming of the correspondence check; it is a division of labour. The picture carries the
proposition; the chain carries the argument.

## What Peirce already says

The historicity of meaning is not a modern gloss on Peirce; it is his own doctrine, stated flatly.

- **Symbols grow.** "Symbols grow," Peirce writes; a symbol "comes into being by development out
  of other signs," and once in being "the body of the symbol changes slowly, but its meaning
  inevitably grows, incorporates new elements and throws off old ones" (c. 1893–1903). Meaning is
  something a symbol *accumulates over its life*, not a function read off its present shape.
- **Semiosis is an unbroken chain.** In "Some Consequences of Four Incapacities" (1868) every
  thought-sign is determined by a *previous* thought and addresses a *subsequent* interpretant; no
  sign arises from nothing. A sign's identity includes its genetic relation to what determined it.
- **The ultimate interpretant is an acquired habit.** In the 1907 "Pragmatism" manuscript the
  final logical interpretant is a *habit-change* — and a habit has a history of takings. The
  meaning that a sign finally delivers is a disposition built up in time.
- **Collateral experience.** To interpret any sign at all, Peirce insists, one must already be
  acquainted with its object *collaterally* to the sign. Two interpreters — or one interpreter at
  two times — read the "same" sign differently because they bring different prior acquaintance.
  This is the individual-history analogue of Berger & Luckmann's social *stock of knowledge*.
- **Synechism.** Even the laws — the habits of nature — evolve; the universe is, for Peirce, "a
  developing argument." History goes all the way down.

The endoporeutic (outside-in) reading is thus the *evaluative* face of a semiotic that is, in its
depths, thoroughly historical.

## Where Arisbe already keeps the two apart

The striking thing is that Arisbe's architecture already holds the Dicisign and the Argument as
**distinct, computable objects** — arguably more operationally than the secondary literature does.

- **`same_graph` answers "same proposition?"** (`src/eg_navigation.py`, full Alpha/Beta
  isomorphism). It is the authority for proof-conclusion equality — the Dicisign level. It is
  deliberately **history-blind**: two graphs reached by any two routes test equal iff they are the
  same proposition.
- **The transformation chain *is* the argument.** A `TransformationChain` of `ChainStep`s
  (`src/tomos_service.py`) records the path: each step names its rule, its parent state
  (`from_state_id`) and its result (`to_state_id`). A chain *branches* when two steps share a
  parent and *converges* when two share a result — so two arguments reaching one conclusion are
  exactly two lines meeting at a shared `to_state_id`. As [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md)
  puts it, "the chain, not the snapshot, is the unit of meaning." `same_graph` says *same
  proposition*; the chain says *different argument*.
- **The warrant gradient makes meaning-by-history a badge.** `standing_of` (`src/provenance.py`)
  projects a graph's [warrant](GLOSSARY.md#warrant) as a gradient — **blank ○** ▸
  **posited ◇** ▸ **derived ⛓** ▸ **withstood ⚔** — and which face a graph wears depends on *the
  path that reached it*, not its form. Two identical EGIs can carry different standing. "Fact,"
  in this reading, "is the last-standing trajectory," never a property of the ink. That is
  meaning-by-history rendered as a computable attribute of a node.
- **The modal lens reads necessity off trajectories.** `src/modal_query.py` reads ◇ and □ off the
  branching history: ◇φ is "some legal trajectory scribes φ," □φ is "every legal trajectory scribes
  φ." Whether a proposition counts as *necessary* is a fact about *which histories reached it* — read
  from the path, not the picture. (See [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md).)

The synchronic/diachronic split of the [UoD](GLOSSARY.md#uod) is precisely
the machinery that lets Arisbe say both things at once: the picture is the proposition, and the
history is the argument.

## Two histories, one graph — worked

The point is easy to see across *two* universes: `(mortal Socrates)` means one thing in a UoD of
Greek biography and another in a UoD of worked syllogisms — but there the two graphs are only
*homographs*, tokens in separate books, and no one is tempted to confuse them. The sharper case —
the one that shows history doing work the picture cannot — is **two histories to the same graph
inside one UoD**, where the derivation history genuinely *converges*: two `ChainStep` lines meeting
at a shared `to_state_id`, the same synchronic frame reached by different roads.

**Example A — one conclusion, two grounds.** A single UoD opens with two facts and two implications
on its sheet:

```
(sprinkler_on)   ~[ (sprinkler_on) ~[ (grass_wet) ] ]
(rained)         ~[ (rained)        ~[ (grass_wet) ] ]
```

— *if the sprinkler is on, the grass is wet; if it rained, the grass is wet.* The grass is wet twice
over, and two histories now reach the very same conclusion graph `(grass_wet)`:

- **History A** deiterates `(sprinkler_on)` from the first scroll (it is a copy of the fact already
  on the sheet) and removes the resulting double cut — `(grass_wet)` *because the sprinkler was on*.
- **History B** does the same with `(rained)` and the second scroll — `(grass_wet)` *because it
  rained*.

Erase the scaffolding (erasure is free on the positive sheet) and both histories leave the sheet
asserting exactly `(grass_wet)`: byte-for-byte the same graph, and `same_graph` returns true. Yet
the two are different **Arguments**, and the difference is not idle. Suppose a later round of the
game retracts `(sprinkler_on)` — a challenge shows the sprinkler was off all week. The
synchronically identical `(grass_wet)` now behaves differently depending on which history laid it
down: History A's grass-wet is **undercut** — its only recorded ground is gone — while History B's is
**untouched**, the rain still standing. *Same picture, different future — because different past.* A
claim's vulnerability is written in its history, not its form; Arisbe keeps that history in the chain
precisely so the undercut one can fall and the other be spared.

**Example B — proved versus observed.** In the same UoD, let the shared graph be a lone assertion
`(grass_wet)`. One history *derives* it — a theorem read off premises since erased — and it wears the
**derived ⛓** face: sound *given its base*. Another history *posits* it — someone looked out the
window — and, sent to Agon and surviving, it wears the **withstood ⚔** face: warranted *because it
met the world and held*. `same_graph` cannot tell the two apart; `standing_of` can, because standing
is read from the path, not the picture. A proof and an observation may arrive at the identical
sentence and still not be the same sign.

Both examples are one lesson: what is shared is the Dicisign; what differs — the ground, the
defeasibility, the standing — is the Argument, and it lives in the history the diachronic UoD keeps.

## The sneak: reifying a history

Here the essay turns critical, and here Berger & Luckmann earn their place. Their term for the
central sin of the sociology of knowledge is **[reification](GLOSSARY.md#reification)**: treating a
humanly produced, history-bound product as if it were a natural, given, authorless fact —
forgetting its genesis. And their account of *why* it happens is exactly the mechanism this essay
has been describing: **sedimentation**. The longer a meaning is carried, the more it is used and
re-used, the more its authored, path-bound origin fades from view and the more it comes to *look
like* brute fact. History is what makes reification easy.

Now the specific danger. A history — a chain, a trajectory through a UoD — does not only *carry*
meaning; it also *implies a shape*. A sequence of steps suggests a direction: "this inquiry was
always heading toward X"; "there is a progression here." The sneak is to lift that implied **telos**
*out of* the diachronic record and **scribe it on the blank sheet of assertion** as though it were
an earned proposition. That is reification in Arisbe's own idiom: forgetting that the telos is an
artifact of the path — the momentum of one history — and posting it as a fact about the world.

It is a seductive error precisely because the machinery that makes history meaning-bearing (good,
necessary, the whole first half of this essay) is the same machinery that makes the telos *available*
to be smuggled. The remedy is not to forget the history. It is to keep it in its place.

## Four guards Arisbe already carries

The reassuring finding is that Arisbe already holds four locks against this particular door. Each
was built for its own reasons; together they are exactly the anti-reification discipline the danger
demands.

1. **The mode contract — no inheritance onto the sheet.** A graph reaches the attested corpus, as
   [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) states it, "*only* by being tested through Agon, or as
   a style-only reprojection of an already-attested graph." "Promotion is the crux,"
   [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) says of the regime-1 → regime-2 transition; and "the
   workshop has no direct §3.3-only path into the corpus." A telos smuggled from a path was never
   *peeled* — it has not earned the sheet. There is no channel by which a history's mere momentum
   becomes an assertion.

2. **The warrant floor — competence, never Progress.** Arisbe's standing gradient "must read as
   in-context competence, **never** as worth, nearness, or context-free Progress"
   ([ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md), Examination II; and the standing floor,
   *"warrant = in-context competence, never worth/Progress"*). A "progression" is exactly the
   worth-ladder the floor was written to refuse. The gradient measures *what has withstood challenge
   here*, not *where the story is going*.

3. **The modal reading — ◇ is not □.** A telos read off **one** history is, in the trajectory
   reading, at most ◇: *some* legal trajectory scribes it. To assert it as settled is to claim □:
   *every* legal trajectory converges on it. But "possibility is the branching of legal
   trajectories, necessity is their convergence" ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)) —
   and one path is a branch, not a convergence. So the reification is, precisely, a **◇ misread as
   □**: mistaking the direction *a* history took for a necessity *all* histories share. The modal
   lens will not report □ for something only one trajectory reached; the guard is mechanical.

4. **The enclosure cap — a tendency is sayable *within* a context, malformed as the structure of
   the whole.** This is the deepest guard, and it is Peirce's own. A real growth-tendency —
   synechism's continuity, "the growth of concrete reasonableness" — is, as
   [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) puts it, "won, not wagered": "sayable and
   operative wherever a context encloses it, and enclosure-malformed only when scribed as the
   operative structure of the unenclosable whole (the outermost sep cannot be drawn)." A telos is
   legitimate *enclosed in a context* — under a cut, inside a scroll, as an antecedent one conditions
   on. It becomes malformed exactly when it is scribed flat, on the outermost sheet, as the structure
   of everything. Reifying a history is drawing the sep that cannot be drawn.

## The nuance: a telos is a hope, not an assertion

None of this says "no telos, ever." Peirce himself affirms one — the growth of concrete
reasonableness, the agapism of "Evolutionary Love" (1893). The point is a discipline of *register*,
not a denial. Peirce's telos is a **regulative hope** — a
[would-be](GLOSSARY.md#would-be--de-inesse), a habit that would hold across every course of
experience — and not a *de inesse* assertion, a flat fact on one sheet. To scribe the would-be as
though it were de inesse is a category error Arisbe already names: it is reading a strict,
across-all-courses habit (□G over the branching history) as a plain present assertion. Keep the
telos where it belongs — a hope that *regulates* inquiry, drawn under enclosure — and it is sound.
Post it on the blank sheet as an earned fact, and it is the sneak.

## The synthesis, and the dragon

The two halves meet here. Meaning **is** carried by history: the argument, not just the
proposition, is part of the sign, and Arisbe keeps it — auditable, replayable — in the diachronic
UoD. And that same history must **not** be reified: no telos it merely implies may cross onto the
blank sheet except by earning it through the contest. The synchronic/diachronic split is exactly
what makes both possible at once — the path lives at the Argument level, in the chain; the sheet
stays free of any telos the path did not earn.

That double discipline — *keep the history, do not reify it* — is the ninth dragon of the
[field guide](FIELD_GUIDE_AND_DRAGONS.md): **the reified telos.** The antidote is this whole essay
in one breath: a progression is a feature of a path, not a fact of the world; the history is
precious, and it belongs in the record, not on the sheet.

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
