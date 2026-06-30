# The Chain of Semiosis
**Provenance, immutability, and the sound step — why every move in Arisbe is an attestation event**

---

## Why this document exists

Arisbe records reasoning, not drawings. That sentence is the whole
architecture in miniature, and this document explains what it commits us
to. It names the Peircean grounding that the data model, the
transformation rules, the Universe of Discourse, and the Ergasterion
promotion boundary all serve — so that the *purpose* stays legible as the
code grows, and so a new reader can see why the pieces are shaped the way
they are.

It is a companion to three documents, not a replacement for any:

- [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) — *what* Arisbe is and who it serves.
- [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md) —
  the diachronic process (the film vs. the photograph).
- [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) —
  the §3.3 correspondence contract and its three regimes.

This document adds the connective thesis those three imply but none of
them states outright: **a piece of reasoning in Arisbe is a chain of
sound, attested sign-transitions — a chain of semiosis — and that is the
object the system exists to capture, preserve, and make examinable.**

---

## Peirce's aim: the analysis of thinking

Peirce did not build the Existential Graphs to draw logic prettily. He
built them to *analyze reasoning* — to make the steps of an inference
perspicuous enough that thought could be inspected, criticized, and
improved. He called the graphs a "moving picture of thought" and, more
strikingly, a "rough and generalized diagram of the Mind." The point of a
moving picture is the *motion*: the Existential Graphs ([EGs](GLOSSARY.md#eg)) were meant to show reasoning
happening, step by justified step, not to freeze a conclusion.

His larger project was continuous with this. From the pragmatic maxim of
"How to Make Our Ideas Clear" onward, Peirce's recurring hope was that a
better *analysis* of reasoning would yield greater *clarity* in
reasoning. The graphs are an instrument of that hope. Arisbe inherits both
the instrument and the hope: it is an environment for doing the analysis,
in pictures, with the steps preserved — in the ongoing expectation that
seeing one's reasoning laid out as a chain of warranted moves helps one
think more clearly.

That is the end the rest of this document is in service of. The
correctness machinery (Dau), the correspondence machinery (§3.3), and the
provenance machinery (the chain) are all means. The end is clearer
thinking through better-analyzed reasoning.

---

## Semiosis, and why a proof is a chain of it

In Peirce's semiotics, a **sign** stands for an **object** to an
**interpretant** — and the interpretant is itself a sign, capable of
determining a further interpretant, and so on. **Semiosis** is the name
for this action of signs: the triadic, ongoing process by which a sign
gives rise to the next. It is inherently *processual* and *unbounded*; a
sign that determined no further interpretant would be a dead end, not a
thought.

Read an Existential Graph this way and the architecture falls out almost
on its own:

- **Each Existential Graph Instance ([EGI](GLOSSARY.md#egi)) state is a sign.** A drawn graph stands for a state of the
  universe of discourse. It is a determinate, inspectable object with a
  fixed meaning.
- **Each rule application is an interpretant — a warranted transition.**
  Applying ERA, INS, IT±, or DC± takes one sign (the prior state) and
  produces the next sign (the new state). The rule is not an arbitrary
  edit; it is a *justified* relation between the two signs. It is what
  carries the meaning of the first forward into the second while
  preserving denotation.
- **A reasoning [episode](GLOSSARY.md#episode) is therefore a chain of semiosis.** A proof, an
  argument, an inquiry — each is an unbroken sequence of sign-transitions,
  every link of which is a sound step. The chain *is* the thought, made
  examinable.

This is Arisbe's reading of the graphs, offered as an architectural
thesis rather than as a quotation from Peirce: he gave us *semiosis* in
his semiotics and *the graphs as the analysis of reasoning* in his logic;
joining them — treating an EG derivation as a literal chain of semiosis —
is the move that organizes this codebase. It is a defensible and, we
think, illuminating reading. It is the reason the **chain**, not the
snapshot, is the unit of meaning ([UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)).

---

## Every rule application is an attestation event

Here is the load-bearing claim. In Arisbe, **a step and its [warrant](GLOSSARY.md#warrant) are
the same act.** You do not first make a change and then, separately, check
whether the change was legitimate. The only way to advance the chain is to
apply a rule, and a rule will not apply unless its preconditions hold. The
move *is* its own proof of soundness.

Each link in the chain is attested in two distinct senses, and both fire
at the moment the step is taken:

1. **Logical soundness.** The transformation rules are Dau's six,
   implemented in full compliance, Beta-aware. `RuleInteraction`
   (`src/rule_interaction.py`) enforces each rule's preconditions — area
   polarity, subgraph closure, isomorphism for de-iteration — and refuses
   the move otherwise. A step that survives is a denotation-preserving
   step by construction. (See [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md), "The
   Guarantor — Dau's formalization.")
2. **Correspondence.** When a step's result is asserted — when it becomes
   part of a record claimed to mean something definite — the §3.3
   invariant requires that its *picture* and its *proposition* denote the
   same object. `attest_correspondence` (`src/correspondence_attestation.py`)
   runs the full check; drift raises `CorrespondenceViolation`. (See
   [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §3.3.)

Together these make each asserted link a *fully warranted sign-transition*:
sound as logic and faithful as a picture. A chain of such links is a piece
of reasoning that can be trusted, replayed, and audited end to end —
because every one of its steps attested itself as it was made.

---

## What Arisbe borrows — and where it departs

The intuition that *the record of how something came to be is itself
valuable, and must be immutable to be trustworthy* is not unique to
Arisbe. Several mature systems are built on it, and Arisbe borrows their
hard-won structure freely. But each of them stops short of the one demand
that defines Arisbe, and seeing exactly where they stop is the clearest
way to state what Arisbe is.

| System | Unit of change | Immutability | Provenance | Is the step *required to be sound*? |
|---|---|---|---|---|
| **Git** | Commit (typed, parented, content-addressed) | Commits immutable; history a directed acyclic graph ([DAG](GLOSSARY.md#dag)) | Parent links, author, message | **No.** A commit may contain anything; soundness (tests, review) is a *separate*, optional layer. |
| **Datomic / event sourcing** | Transaction (append-only fact) | Never overwrite; state is a fold over the log; "as-of" queries | The log *is* the provenance | **No.** A transaction records *what changed*, not whether the change was warranted. |
| **Wikis** | Revision | Every revision immutable and addressable | Revision history; sandbox vs. mainspace | **No.** Any edit is a revision; correctness is social and after-the-fact. |
| **Scholarship** | Note → preprint → publication | Published record is fixed | Citation, peer review | **Partly, and socially.** A journal *vouches*; the warrant is external and human, not intrinsic to the act of writing. |
| **Arisbe** | **Rule application** (a sound step) | EGI states immutable; chain append-only | The chain records rule + parent + result per step | **Yes, intrinsically.** The step *cannot be taken* unless it is sound. The warrant is the act. |

Three observations follow.

**The commit already validates.** In Git you can commit nonsense and find
out later; the validation layer is bolted on. In Arisbe the analog of
`git commit` is a rule application, and it *already validates* — Dau's rule
is the soundness check. This makes per-step commits *cheaper* than in Git
(no separate proof obligation: the rule is the proof) and *richer* (each
step carries its rule name, parameters, and parent state — full
provenance, for free, intrinsic to the move).

**Provenance is intrinsic, not bolted on.** Because each EGI state is
immutable (`src/egi_core_dau.py` — use `.with_vertex()`, never
`.add_*()`) and each step records its parent, the chain is a complete,
inspectable derivation by construction. We are not *adding* an audit trail
to a mutable structure; the structure is the audit trail. This is the
event-sourcing insight, sharpened by the soundness requirement: the log
is not just *what happened* but *a sequence of warranted moves*.

**Assertion still resides in a context.** The scholarship model gets one
thing right that the others underplay: a record acquires its *force* from
being asserted into a context that confers standing (a journal, a field).
Arisbe keeps this. A chain composed in the Ergasterion workshop is
regime-1 — drawn, sound at every step, but not yet a public record. It
becomes a regime-2 asserted record only when **promoted** into the corpus
context. Until then it is a *form*: convenient, suggestive, possibly
deceptive, but not yet an assertion. (See "The regimes and the chain,"
below, and [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §4.)

**Two registers, and the [seam](GLOSSARY.md#seam) the textbooks erase.** An EG drawing can stand in
either of two provenances, and the literature's habit of printing both flush
together — "[scribe](GLOSSARY.md#scribe) on the sheet = assert" — erases a real distinction. A
*derived* graph is **demonstrative**: reached from the blank by truth-preserving
steps, it inherits the blank sheet's warrant — this is the **chain** above. A
*posited* graph is **assertoric**: a premise scribed on the Sheet of Assertion,
overwhelmingly contingent, with no warrant from the calculus at all — its warrant
comes from the utterer's exposure and rises only by withstanding challenge. In
Arisbe that is a graph admitted at **low warrant** (import) or **sent to Agon**,
never a product of the chain. The architecture *marks the seam the textbooks
leave unmarked* — derived-truth-preservingly vs. posited-under-warrant are
different relations to a context, not one undifferentiated drawing. See
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md).

---

## The regimes and the chain

The three correspondence regimes are not three arbitrary modes; they are
three relations a chain of semiosis can stand in to a context.

- **Regime 1 — composition (Ergasterion).** The user is composing a chain
  against an explicitly chosen base state (an empty sheet of assertion, or
  an existing corpus UoD). Every step is logically sound — `RuleInteraction`
  guarantees it — but the chain has no assertoric force yet. It is
  semiosis *in private*. §3.3 is suspended at the corpus-record boundary
  because there is no public proposition the picture is yet claimed to
  match. Forms here mean nothing *as assertions*, however well-formed they
  are.
- **Regime 2 — asserted (Organon, Agon, every promoted chain).** The chain
  is anchored into the corpus context. It is now claimed to mean something
  definite. §3.3 is mandatory and runtime-attested; promotion fires the
  check on the final state before any persistence, and refuses cleanly on
  drift. This is the act by which private semiosis becomes a public
  record.
- **Regime 3 — presentation-only.** Repositioning a vertex, reshaping a
  cut, rerouting a ligature — these change the *picture* without touching
  the *sign*. They are indifferent to the chain's logical content by
  construction (`src/presentation_ops.py` refuses any boundary-crossing
  proposal). Semiosis is untouched; only its rendering moves.

**Promotion is the crux.** It is the regime-1 → regime-2 transition: the
moment a chain of sound steps becomes an asserted record. Concretely
([CLAUDE.md](../CLAUDE.md), `tomos_service.save_uod_with_chain`): the
whole chain — base state plus every `ChainStep` — is persisted, with the
final-state §3.3 attestation firing *before* any disk write, so a refusal
aborts with nothing half-saved. The workshop deliberately makes "compose"
and "assert" distinguishable acts, because in Peirce's terms they are
different acts: making a form, and asserting it in a context.

---

## Semiosis is dialogical: where Agon comes in

Everything above describes a chain largely as one reasoner builds it: compose
in the workshop, promote to the corpus. But semiosis in Peirce is neither
finished nor solitary. An interpretant is always a sign *for* a further
interpretant — if only a later phase of the same mind — and his logic is
social to the root: inquiry is a community process, and truth is the limit
toward which a community of inquirers tends. A single chain is the visible
track left by something that is, in its nature, a dialogue.

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

This is why **Agon** — the [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game — is not a third feature
sitting beside Organon and Ergasterion, but the mode in which the
dialogical character the lone chain only *implies* becomes literal. It is
also the most authentically Peircean of the three. "Endoporeutic" is
Peirce's own word for reading a graph from the outside in, as a transaction
between two parties: a defender who asserts the graph and a skeptic who
challenges it. For Peirce the game is not a gloss on the logic — it is how
the logic *means*. A graph's truth is what survives the contest. (The
two-player engine is implemented today, Z3-validated, with a REPL; the web
arena `/agon` is live as a thin, flexible V1. See
[ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).)

Read this way, the three sources of creativity and discovery that an
Arisbe-style environment opens onto are continuous with Peirce's own
commitments:

- **Interaction with the world** — abduction, and the fallibilist
  insistence that a model answers to something outside itself.
- **Interaction between minds** — the dialogical logic and the community
  of inquiry. This is Agon's home ground.
- **Ongoing reference to, and testing of, our models** — the corpus as a
  record *held open to revision*, not a vault of settled truths.

So there is a richer notion of "asserted" latent in the architecture than
promotion alone delivers. Ergasterion yields a chain that is *sound* at
every step. Agon is where a chain is *put at risk* — defended, attacked,
and either carried into the corpus with its meaning tested between minds or
turned back. Regime-2 standing, in its fullest form, is earned not just by
§3.3 attestation but by having withstood challenge. That fuller account is
still ahead of the current implementation in *degree* — Agon does not yet
score winning strategies — but the architecture now **enforces its
direction**: as of 2026-06-06 the workshop has no direct §3.3-only path into
the corpus. A graph leaves Ergasterion either to a regime-1 **scratch** store
(unasserted holding) or by being **sent to Agon** to be tested. §3.3 attests
*correspondence, not truth*, so it cannot on its own confer regime-2 standing;
that is the contract the retirement of the direct promote route makes literal.

---

## What this buys the user

The architecture is not abstract bookkeeping. Because a reasoning episode
is preserved as a chain of sound, attested steps, it becomes an *object* a
person can work with:

- **Replay.** Step through a derivation move by move and watch the thought
  develop — the "moving picture" actually moves.
- **Audit.** Ask of any conclusion: by which steps, from which premises,
  under which rules? The answer is in the chain, not reconstructed.
- **Critique.** Because each step names its rule and parent, a chain can
  be examined for where a move was weak, redundant, or differently
  available — the analysis of reasoning Peirce was after.
- **Trust.** A promoted chain is sound at every link and faithful as a
  picture at every asserted state. There is no "but is the diagram really
  saying that?" gap; §3.3 closed it.

This is the difference between a tool that stores *pictures of logic* and
an environment for *doing logic in pictures*. The former keeps artifacts;
Arisbe keeps semiosis. And in keeping semiosis — sound step after sound
step, each one warranted as it is made — it serves the hope Peirce never
let go of: that the careful analysis of how we think is a path toward
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
The regime-1→2 boundary is now reached through Agon's asserting disposition
(`src/web_api/routes/agon.py` → `save_uod_with_chain`), not a workshop route;
Ergasterion (`src/web_api/routes/ergasterion.py`) holds regime-1 drafts and a
**scratch** store (`src/web_api/services/scratch_store.py`).*

**Created**: 2026-06-01
