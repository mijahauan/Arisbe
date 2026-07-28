# The Chain of Semiosis
**Provenance, immutability, and the sound step — why every move in Arisbe is an attestation event**

---

## Why this document exists

Arisbe records reasoning, not drawings. That sentence holds the whole
architecture in miniature, and this document explains what it commits us
to. It names the Peircean grounding that the data model, the
transformation rules, the Universe of Discourse, and the Ergasterion
promotion boundary all serve, so that the *purpose* stays legible as the
code grows and a new reader can see why the pieces take the shape they
do.

It stands as a companion to three documents and replaces none of them:

- [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) — *what* Arisbe is and who it serves.
- [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md) —
  the diachronic process (the film vs. the photograph).
- [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) —
  the correspondence check (§3.3) contract and its three regimes.

This document adds the connective thesis those three imply but none of
them states outright: **a piece of reasoning in Arisbe forms a chain of
sound, attested sign-transitions — a chain of semiosis — and that chain
names the object the system exists to capture, preserve, and make
examinable.**

---

## Peirce's aim: the analysis of thinking

Peirce did not build the Existential Graphs to draw logic prettily. He
built them to *analyze reasoning* — to make the steps of an inference
perspicuous enough that one could inspect, criticize, and improve
thought. He called the graphs a "moving picture of thought" and, more
strikingly, a "rough and generalized diagram of the Mind." The point of a
moving picture lies in the *motion*. He meant the Existential Graphs ([EGs](GLOSSARY.md#eg)) to show reasoning
happening, step by justified step, not to freeze a conclusion.

His larger project stayed continuous with this. From the pragmatic maxim of
"How to Make Our Ideas Clear" onward, Peirce held to one recurring hope:
that a better *analysis* of reasoning would yield greater *clarity* in
reasoning. The graphs serve that hope as an instrument. Arisbe inherits both
the instrument and the hope. It offers an environment for doing the analysis,
in pictures, with the steps preserved, in the ongoing expectation that
seeing one's reasoning laid out as a chain of warranted moves helps one
think more clearly.

The rest of this document serves that end. The
correctness machinery (Dau), the correspondence machinery (§3.3), and the
provenance machinery (the chain) all function as means. The end remains
clearer thinking through better-analyzed reasoning.

---

## Semiosis, and why a proof is a chain of it

In Peirce's semiotics, a **sign** stands for an **object** to an
**interpretant** — and the interpretant, itself a sign, can determine a
further interpretant, and so on. **Semiosis** names this action of
signs: the triadic, ongoing process by which a sign gives rise to the
next. Semiosis remains inherently *processual* and *unbounded*; a sign
that determined no further interpretant would make a dead end, not a
thought.

Read an Existential Graph this way and the architecture falls out almost
on its own:

- **Each Existential Graph Instance ([EGI](GLOSSARY.md#egi)) state is a sign.** A drawn graph stands for a state of the
  universe of discourse. It stands there as a determinate, inspectable
  object with a fixed meaning.
- **Each rule application is an interpretant — a warranted transition.**
  Applying ERA, INS, IT±, or DC± takes one sign (the prior state) and
  produces the next sign (the new state). The rule makes no arbitrary
  edit; it holds as a *justified* relation between the two signs. It
  carries the meaning of the first forward into the second while
  preserving denotation.
- **A reasoning [episode](GLOSSARY.md#episode) is therefore a chain of semiosis.** A proof, an
  argument, an inquiry — each forms an unbroken sequence of
  sign-transitions, every link of which is a sound step. The chain *is*
  the thought, made examinable.

This reading of the graphs belongs to Arisbe; we offer it as an architectural
thesis rather than as a quotation from Peirce. He gave us *semiosis* in
his semiotics and *the graphs as the analysis of reasoning* in his logic.
Joining them — treating an EG derivation as a literal chain of semiosis —
makes the move that organizes this codebase. A defensible reading, we
think, and an illuminating one. It explains why the **chain**, not the
snapshot, serves as the unit of meaning ([UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)).

---

## Every rule application is an attestation event

Here is the load-bearing claim. In Arisbe, **a step and its [warrant](GLOSSARY.md#warrant) are
the same act.** You do not first make a change and then, separately, check
whether the change was legitimate. The chain advances only by rule
application, and a rule will not apply unless its preconditions hold. The
move *is* its own proof of soundness.

Each link in the chain earns attestation in two distinct senses, and both
fire the moment you take the step:

1. **Logical soundness.** The transformation rules are Dau's six,
   implemented in full compliance, Beta-aware. `RuleInteraction`
   (`src/rule_interaction.py`) enforces each rule's preconditions — area
   polarity, subgraph closure, isomorphism for de-iteration — and refuses
   the move otherwise. A step that survives preserves denotation by
   construction. (See [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md), "The
   Guarantor — Dau's formalization.")
2. **Correspondence.** When a step's result is asserted — when it becomes
   part of a record claimed to mean something definite — the §3.3
   invariant requires that its *picture* and its *proposition* denote the
   same object. `attest_correspondence` (`src/correspondence_attestation.py`)
   runs the full check; drift raises `CorrespondenceViolation`. (See
   [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §3.3.)

Together these make each asserted link a *fully warranted sign-transition*:
sound as logic and faithful as a picture. A chain of such links yields a
piece of reasoning one can trust, replay, and audit end to end, because
every one of its steps attested itself in the making.

---

## What Arisbe borrows — and where it departs

The intuition that *the record of how something came to be is itself
valuable, and must be immutable to be trustworthy* does not belong to
Arisbe alone. Several mature systems build on it, and Arisbe borrows their
hard-won structure freely. But each of them stops short of the one demand
that defines Arisbe. Where, exactly, do they stop? Seeing that gives the
clearest way to state what Arisbe is.

| System | Unit of change | Immutability | Provenance | Is the step *required to be sound*? |
|---|---|---|---|---|
| **Git** | Commit (typed, parented, content-addressed) | Commits immutable; history a directed acyclic graph ([DAG](GLOSSARY.md#dag)) | Parent links, author, message | **No.** A commit may contain anything; soundness (tests, review) is a *separate*, optional layer. |
| **Datomic / event sourcing** | Transaction (append-only fact) | Never overwrite; state is a fold over the log; "as-of" queries | The log *is* the provenance | **No.** A transaction records *what changed*, not whether the change was warranted. |
| **Wikis** | Revision | Every revision immutable and addressable | Revision history; sandbox vs. mainspace | **No.** Any edit is a revision; correctness is social and after-the-fact. |
| **Scholarship** | Note → preprint → publication | Published record is fixed | Citation, peer review | **Partly, and socially.** A journal *vouches*; the warrant is external and human, not intrinsic to the act of writing. |
| **Arisbe** | **Rule application** (a sound step) | EGI states immutable; chain append-only | The chain records rule + parent + result per step | **Yes, intrinsically.** The step *cannot be taken* unless it is sound. The warrant is the act. |

Three observations follow.

**The commit already validates.** In Git you can commit nonsense and find
out later; the validation layer bolts on afterward. In Arisbe the analog of
`git commit` is a rule application, and it *already validates* — Dau's rule
serves as the soundness check. This makes per-step commits *cheaper* than
in Git, since the rule is the proof and no separate proof obligation
remains. It also makes them *richer*, since each step carries its rule
name, parameters, and parent state — full provenance, for free, intrinsic
to the move.

**Provenance is intrinsic, not bolted on.** Because each EGI state stays
immutable (`src/egi_core_dau.py` — use `.with_vertex()`, never
`.add_*()`) and each step records its parent, the chain forms a complete,
inspectable derivation by construction. We do not *add* an audit trail
to a mutable structure; the structure is the audit trail. Here the
event-sourcing insight returns, sharpened by the soundness requirement:
the log records not just *what happened* but *a sequence of warranted
moves*.

**Assertion still resides in a context.** The scholarship model gets one
thing right that the others underplay: a record acquires its *force* from
being asserted into a context that confers standing (a journal, a field).
Arisbe keeps this. A chain composed in the Ergasterion workshop stands at
regime-1: drawn, sound at every step, but not yet a public record. It
becomes a regime-2 asserted record only when **promoted** into the corpus
context. Until then it remains a *form* — convenient, suggestive, possibly
deceptive, but not yet an assertion. (See "The regimes and the chain,"
below, and [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §4.)

**Two registers, and the [seam](GLOSSARY.md#seam) the textbooks erase.** An EG drawing can stand in
either of two provenances, and the literature's habit of printing both flush
together — "[scribe](GLOSSARY.md#scribe) on the sheet = assert" — erases a real distinction. A
*derived* graph is **demonstrative**: reached from the blank by truth-preserving
steps, it inherits the blank sheet's warrant. This is the **chain** above. A
*posited* graph is **assertoric**: a premise scribed on the Sheet of Assertion,
overwhelmingly contingent, with no warrant from the calculus at all. Its warrant
comes from the utterer's exposure and rises only by withstanding challenge. In
Arisbe that means a graph admitted at **low warrant** (import) or **sent to Agon**,
never a product of the chain. The architecture *marks the seam the textbooks
leave unmarked*: derived-truth-preservingly and posited-under-warrant name
different relations to a context, not one undifferentiated drawing. See
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md).

---

## The regimes and the chain

The three correspondence regimes do not name three arbitrary modes; they
name three relations a chain of semiosis can stand in to a context.

- **Regime 1 — composition (Ergasterion).** The user composes a chain
  against an explicitly chosen base state (an empty sheet of assertion, or
  an existing corpus UoD). Every step holds logically sound — `RuleInteraction`
  guarantees it — but the chain carries no assertoric force yet. It
  amounts to semiosis *in private*. §3.3 stays suspended at the
  corpus-record boundary because nobody yet claims the picture matches
  any public proposition. Forms here mean nothing *as assertions*, however
  well-formed they are.
- **Regime 2 — asserted (Organon, Agon, every promoted chain).** The chain
  anchors into the corpus context. It now stands claimed to mean something
  definite. §3.3 becomes mandatory and runtime-attested; promotion fires the
  check on the final state before any persistence, and refuses cleanly on
  drift. By this act private semiosis becomes a public record.
- **Regime 3 — presentation-only.** Repositioning a vertex, reshaping a
  cut, rerouting a ligature — these change the *picture* without touching
  the *sign*. They remain indifferent to the chain's logical content by
  construction (`src/presentation_ops.py` refuses any boundary-crossing
  proposal). Semiosis stays untouched; only its rendering moves.

**Promotion is the crux.** It marks the regime-1 → regime-2 transition,
the moment a chain of sound steps becomes an asserted record. Concretely
([CLAUDE.md](../CLAUDE.md), `tomos_service.save_uod_with_chain`), the
whole chain — base state plus every `ChainStep` — persists, with the
final-state §3.3 attestation firing *before* any disk write, so a refusal
aborts with nothing half-saved. The workshop deliberately makes "compose"
and "assert" distinguishable acts, because in Peirce's terms they differ:
making a form, and asserting it in a context.

---

## Semiosis is dialogical: where Agon comes in

Everything above describes a chain largely as one reasoner builds it: compose
in the workshop, promote to the corpus. But in Peirce semiosis neither
finishes nor stands solitary. An interpretant always serves as a sign *for* a
further interpretant, if only a later phase of the same mind, and his logic
runs social to the root: inquiry proceeds as a community process, and truth
names the limit toward which a community of inquirers tends. A single chain
remains the visible track left by something that amounts, in its nature, to
a dialogue.

*(One divergence, recorded not resolved.* That last clause is Peirce's
**convergence** — the real as the downstream limit of inquiry — and it is the
framing this codebase inherited. The author holds a second, non-convergence view:
the real is the **un-enclosable ground** any inquiry presupposes, "upstream and
around," so that demotion never ends and need not arrive anywhere. On that reading
the chain still records warranted semiosis exactly as below, but it converges on
nothing; "fact" is the last-standing line, conferred yet always answerable. The
two are held in the same chord; the full argument is in
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) §8 and
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md), "The membrane.")*

This is why **Agon** — the [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game — does not sit
beside Organon and Ergasterion as a third feature. It names the mode in
which the dialogical character the lone chain only *implies* becomes
literal. It also stands as the most authentically Peircean of the three.
"Endoporeutic" is
Peirce's own word for reading a graph from the outside in, as a transaction
between two parties: a defender who asserts the graph and a skeptic who
challenges it. For Peirce the game does not gloss the logic — it is how
the logic *means*. A graph's truth is what survives the contest. (The
two-player engine runs today, Z3-validated, with a REPL; the web
arena `/agon` runs live as a thin, flexible V1. See
[ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).)

Read this way, the three sources of creativity and discovery that an
Arisbe-style environment opens onto stay continuous with Peirce's own
commitments:

- **Interaction with the world** — abduction, and the fallibilist
  insistence that a model answers to something outside itself.
- **Interaction between minds** — the dialogical logic and the community
  of inquiry. This is Agon's home ground.
- **Ongoing reference to, and testing of, our models** — the corpus as a
  record *held open to revision*, not a vault of settled truths.

So a richer notion of "asserted" lies latent in the architecture than
promotion alone delivers. Ergasterion yields a chain *sound* at
every step. In Agon a chain gets *put at risk* — defended, attacked,
and either carried into the corpus with its meaning tested between minds or
turned back. A chain earns regime-2 standing, in its fullest form, not just
by §3.3 attestation but by having withstood challenge. That fuller account
still runs ahead of the current implementation in *degree* — Agon does not
yet score winning strategies — but the architecture now **enforces its
direction**: as of 2026-06-06 the workshop has no direct §3.3-only path into
the corpus. A graph leaves Ergasterion either to a regime-1 **scratch** store
(unasserted holding) or by being **sent to Agon** to be tested. §3.3 attests
*correspondence, not truth*, so it cannot on its own confer regime-2 standing;
the retirement of the direct promote route makes that contract literal.

---

## What this buys the user

The architecture amounts to more than abstract bookkeeping. Because a
reasoning episode survives as a chain of sound, attested steps, it becomes
an *object* a person can work with:

- **Replay.** Step through a derivation move by move and watch the thought
  develop — the "moving picture" actually moves.
- **Audit.** Ask of any conclusion: by which steps, from which premises,
  under which rules? The answer lies in the chain, never reconstructed.
- **Critique.** Because each step names its rule and parent, a reader can
  examine a chain for where a move was weak, redundant, or differently
  available — the analysis of reasoning Peirce was after.
- **Trust.** A promoted chain holds sound at every link and faithful as a
  picture at every asserted state. No "but is the diagram really
  saying that?" gap remains; §3.3 closed it.

Here lies the difference between a tool that stores *pictures of logic* and
an environment for *doing logic in pictures*. The former keeps artifacts;
Arisbe keeps semiosis. And in keeping semiosis — sound step after sound
step, each one warranted in the making — it serves the hope Peirce never
let go of: that the careful analysis of how we think offers a path toward
thinking more clearly.

---

*Companion to [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md),
[UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md),
and [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md).
See also [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md): the diachronic
chain *is* the apparatus that carries modality (and the meta-judgment of a
community) without any mark — second-order content displayed as history, not
asserted.
The chain-persistence implementation lands in `src/tomos_service.py`
(`TransformationChain`, `ChainStep`, `save_uod_with_chain`, `load_chain`).
The regime-1→2 boundary now runs through Agon's asserting disposition
(`src/web_api/routes/agon.py` → `save_uod_with_chain`), not a workshop route;
Ergasterion (`src/web_api/routes/ergasterion.py`) holds regime-1 drafts and a
**scratch** store (`src/web_api/services/scratch_store.py`).*

**Created**: 2026-06-01
