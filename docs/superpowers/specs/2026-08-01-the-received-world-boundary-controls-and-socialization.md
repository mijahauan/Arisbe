# The received world — boundary errors, objectified controls, and socialization

**Design sitting, 2026-08-01.** A working record of the author's rulings and
hypotheses developed in conversation after the re-measurement pass merged
(`c6ce5a7`). Nothing here is built. Assistant refinements are marked as such and
are **unruled** until the author says otherwise.

Companion to [THE_KYTOS.md](../../THE_KYTOS.md) §1.3 (act-timing, ruled and
recorded) and to the environment-first ruling recorded in `CURRENT_PLAN.md`.

---

## 1 · The scoped hypothesis: parsimony produces boundary errors

**The author's hypothesis**, scoped deliberately — it explains *not every error*,
only those bearing on the **parsimony and economics of viewing, processing and
communicating**:

> Conflation and exposure happen under the pressure to economize. Save steps, let
> something else hold the context, think with constrained resources. We cannot view
> the whole Universe of Discourse at once. We want the critical snippet without its
> entire history. We need to talk without re-inventing language each time.

Three error shapes fall in the class:

- **Conflation** — "pile it all in one graph": too much inside one frame.
- **Exposure** — "expose a fragment isolated and out of context": too little carried
  out with the part.
- **Level slip** — "cart before the horse": the boundary placed at the wrong point in
  a *dependency order* rather than in a containment.

*Assistant reading, unruled:* the three are one mechanism — **the boundary placed
where it was cheap rather than where the structure requires**, the cheap place being
whatever spares one from finding the right one. Conflation and exposure are duals;
the level slip is the same failure along the temporal axis. The economy is over
**what must be held in mind at once**, which is why the same pressure produces both
compression (one graph) and elaboration (a fresh private register) — whichever is
cheaper to think.

## 2 · Where the errors live: at the boundary, not in the calculus

**The author's refinement, and the load-bearing one.** The logic internal to Arisbe
exerts its own integrity; internally none of this admits of doubt because *we ensure
the rules*. The errors belong to interaction — with the user, and with the outside
world — where the internal rigor **does not apply but is assumed**, or where the
work is **subjected to external objectified controls** that do not share its logic.

Two failure modes follow.

**(a) Rigor assumed past its domain.** Arisbe has met this often enough that the
countermeasures are already doctrine, and each has the same shape — *it refuses an
inference the receiver would naturally make*: the correspondence check attests
correspondence, **not truth**; import enters at low warrant; the membrane strips
claimed standing; a graph reaches the corpus only through Agon or a style-only
reprojection. The general form is the **grade vocabulary** (built / measured /
evidenced / partially-evidenced / named-not-built / named-not-modeled /
queued-conjecture), whose only job is to mark how far the rigor extends — and whose
assignment is **the author's by the map's own rule**, because the one who can see
past the instrument is the one who says where it stops. Canonical failure: the West
letter, documents that outran the instrument, corrected by a grade ruling rather
than by code.

**(b) External objectified controls whose model of "checked" is narrower.** Fresh
instance from the merged pass: `pytest` is real, rigorous, and structurally blind to
everything in a file that is not an assertion. A docstring described a world that no
longer existed while the suite, the commit hook and 152 core tests all reported
green. **Four correction rounds happened inside a fully green control.** The control
did not fail; it succeeded at a different question, and nothing inside it could say
so. Generalizes to a journal's format, a repository's model of history, a reviewer's
expectations.

**Guards that bite versus guards that state** *(assistant, unruled)*. A control that
only states its limit travels through the same channel that carries the drift.
`attest_correspondence` raises; `citation_for` reports `has_source: false` rather
than inventing one; the import floor is a value in the record. Those hold whether or
not anyone reads them. The grade table, the low-warrant caveat, and the "attests
correspondence, not truth" sentence are read by humans or not at all — the right
doctrine in the weakest enforcement, sitting exactly where the errors live.

## 3 · Shannon's bracket, and the second limit

**The author's connection.** Information transfer presupposes **pre-coordination** —
transmitter and receiver have already shared what they need to encode and decode.
Given that, accurate communication has a second impediment besides channel noise:
**drift or inaccuracy in the pre-coordinated model.** Something out of scope of the
signal changed how transmitter or receiver interprets the message.

Shannon bracketed the semantic problem explicitly, and the bracket is where this
lives: the codebook is assumed shared and fixed, and the channel model can have no
term for it without representing the agreement it presupposes.

*Assistant, unruled — the operational consequence:* **drift produces confident
error, not detectable error.** Noise announces itself; a message decoded under a
drifted codebook arrives clear and wrong. The merged pass supplied a specimen: one
mis-transcribed window-5 figure, then careful downstream reasoning that produced a
`[sic]` bracket "correcting" a correct number and a parenthetical explaining a
difference between two windows that does not exist. **Care propagates a bad premise
further than sloppiness does.**

Three defenses, of which Arisbe has two:

1. **Carry the decoder rather than assume it** — index-over-ink: the AlternativeSet
   holds pointers to gate-checked chain steps and no evidence of its own, so the
   codebook is re-derivable. The recomputation thesis doing real work.
2. **Redundancy across independent routes** — the −185 figure was trusted because a
   sweep table and three separate tests agree digit for digit.
3. **Periodic re-grounding against something outside both parties** — *absent*. Two
   units with a drifted shared model agree perfectly, forever, and nothing internal
   ever says otherwise. Only a world that pushes back exposes it, which is the
   environment-first ruling arriving from the other direction: **"nothing at stake"
   and "codebook drift is invisible" are one gap seen twice.**

## 4 · The origin of a control: provided or negotiated

**The author's sharpening.** The origin of an objectified control is the crux — *do
we provide it, or does the community negotiate and develop it?* How do I know when
to stop? When I see the stop sign. What fixes the context of "the cat is on the
mat"? Reading Sowa, or hearing someone point at a yard. How do I read "repeat"? As
an artillery man awaiting a command, or off the back of a shampoo bottle.

**The sign carries no marker of its own provenance.** "Repeat" is byte-identical in
both worlds; no examination of the fragment recovers the practice that sustains it.
A **provided** control is valid where we can enforce it; a **negotiated** one where a
community sustains it. They are indistinguishable from inside the message, and
treating one as the other is the level slip in its most consequential form.

Stipulating internally is correct and deliberate — Dau's formalization is the
non-negotiable bedrock. The error is carrying the stipulated form across the
boundary and expecting it to hold where nobody has agreed to it.

**The author's structural answer:** interacting outside requires *situating* it, akin
to what the Endoporeutic Game already does — **in what model does this G fit?**

**The gap this exposes.** The interpretation register *is* that operation, built and
surfaced: `/agon/interpret` peels G against a chosen M, and `/agon/where-it-holds`
runs the inverse pivot, ranking domains as holds / partial (residue named) /
independent / contradicts. **But the models it ranges over are ours** —
`agon_models.py`'s curated scenarios plus corpus UoDs. So it answers "in which of
*our* models does this fit," not "in which practice does this live." The open
membranes (wiki dispute, Wikidata, discourse, the vault) import **content into M**;
nothing imports **an M to situate against**. We built the situating operation and
stocked it from our own shelf.

*Assistant, unruled:* the catalogue asymmetry looks like the cheapest correction on
this list — the inverse pivot's model catalogue should be able to grow from outside,
and an arriving model should earn its place the way arriving content already does.

## 5 · Socialization: a kytos is not born full-grown

**The author's addition.** A portion of total communication goes to **orienting per
model and to model-building** — education, internalization, **primary and secondary
socialization**. A kytos does not emerge like Athena from the head of Zeus; it must
receive its initial modeling from outside as it begins to engage its own internal
reasoning.

Berger & Luckmann's two registers do different work. **Primary socialization** is not
the acquisition of *a* model but of *the* world: significant others unchosen, no
critical distance available, received as objectivated fact rather than as one option
— and that non-optionality is what makes it reality rather than hypothesis.
**Secondary socialization** installs role-specific sub-worlds against the backdrop of
the primary, known *as* sub-worlds, and therefore detachable and revisable.

### 5.1 · The formal resolution — the author's

An apparent tension: the polarity discipline says nothing crosses to even depth
except by a licensed, recorded move, yet the first content has no prior record to be
licensed against. Requiring one would demand the product of socialization as its own
precondition.

**The author's answer, inside the calculus rather than around it:** INS happens in
**verso** (odd depth, where insertion needs no warrant at all), and **IT+** can
immediately place it in **sub-recto** context — *if A then A*.

From the blank sheet: DC+ opens `~[ ~[ ] ]`; INS scribes A at depth 1; IT+ copies it
inward to depth 2; the sheet stands at `~[ A ~[ A ] ]`, which asserts **A → A**.

So the received world enters **held as a conditional whose antecedent is what was
given.** The unit is committed to A only *given* A. Nothing contingent stands at
depth 0; Departure II is untouched; the first content never claimed the standing that
would have required a record. **The child does not assert its parents' world — it
holds it as the consequent of having been given it**, and that reads as fact from
inside precisely because the antecedent is never varied.

### 5.2 · Sophistication is plurality of antecedents

**The author's second half.** With ongoing additions and experience the situation
grows complex and always admits revision and falsification — and the grounds for it
(learning of authoritative adults besides one's parents, of competing ideas besides
theirs) *produce* the growing sophistication and discrimination of a kytos's UoD.

*Assistant reading, unruled:* with a single source the antecedent is constant, drops
from view, and the consequent reads as the world. A second authority does not merely
add content — it makes the first *an* authority rather than *the* world, because two
antecedents now stand where one did and their consequents can differ.
**Falsifiability arrives with plurality, not with scepticism.**

Two rules already in the machinery are this mechanism:

- **`corroborating_witnesses`** demands *distinct records* on Berger & Luckmann
  grounds — a record repeating itself contributes nothing to an objectivated
  reality. That is the second authoritative adult, formalized.
- **The branching DAG** that `modal_query` reads ◇ and □ from is the same structure:
  what holds under some antecedent is possible, what holds under all is necessary. A
  kytos's growing discrimination *is* the growth of that branching, with □ emerging
  as what survives across sources rather than as anything stipulated.

### 5.3 · What is built, and what is missing

**Built, and better than credited:** V2a.2 banking enters an author's answer into M
as `(asserted "author" ⌜…⌝)` — quoted, attributed, one licensed INS-of-cell,
replayable through the polarity gate. Content received from a significant other,
marked as *received* rather than derived: the shape secondary socialization needs,
because the sub-world arrives bearing its provenance and stays revisable.

**Missing — the C-series spends nothing on orientation** *(assistant, unruled but
checkable against the existing runs)*. Every mark on the board is a first-order claim
about the world: a fact, a law, a challenge, a corroboration. **Not one is about how
to read marks.** The pre-coordination Shannon assumes is never paid for; it is
stipulated in the fixtures and thereafter presumed. Units that never spend on
establishing a shared model have no way to notice when theirs have drifted apart —
possibly the cleanest available formulation of why nothing coordinates.

**Missing — the initial model is assigned, not scribed.** A unit is seeded
`Unit(laws={...})`: a Python set assignment, with no chain, no antecedent, no
provenance, and nothing recorded to revise. **The initial model carries exactly the
same defect as the reliability data** (§6). Seeding instead by **DC+ · INS · IT+**
would put primary socialization in the ink, give the received world an antecedent a
later source can stand beside, and make revision a licensed move rather than a Python
mutation.

**Arrow reversed.** [TUTOR_LOOP.md](../../TUTOR_LOOP.md) is designed-and-unbuilt with
the attention economy aimed at a *human* learner. The socialization loop is its
transpose — learner as kytos, teacher as community or user — and most of that design
(learner-ledger, grading events, spaced re-challenge) turns around unchanged.

## 6 · The three-tier diagnosis this arc keeps returning to

Where things live in the codebase today:

| Tier | Contents |
|---|---|
| **In the ink** — EGI, in the DAG, moved only by Dau rules, re-checkable forever | M's contents in world-scroll cells; ENTERTAIN/DISCHARGE/ABANDON; every rule application; PEEL / ADMIT / RETRACT / REVISE with executed derivations; banked author answers; quotations |
| **Index over ink** — a record holding pointers to gate-checked chain steps, recomputable from the DAG | **The AlternativeSet, and only it** (AS1–AS4) |
| **Private Python register** — no ink, not in the DAG, not re-derivable | `Unit.peers` (**reliability**), `MembraneLedger`, `UsageLedger`, `AttentionEconomy`, `Horizon`, the C-series scoring apparatus, `first_seen` / `_credited` / `_supplied_by` |

**Reliability develops in a Python dict.** It is never scribed, never crosses a
membrane, never becomes a mark, is never objectivated, and could not be
reconstructed from the chain. Under the author's own commens doctrine it was
therefore never part of the shared reality — **a prior explanation for typification's
inertness that does not depend on scarcity**, and one that would still stand after
the scarcity test.

*Assistant, unruled:* the author's early instinct toward social insects is a
**forcing function**, not a simplification. A stigmergic unit has no private register
— the trail *is* the memory, external, shared, objectivated by construction, decaying
whether or not anyone attends. Confine the terminal unit so it cannot hold a private
register and the whole third tier becomes unrepresentable.

## 7 · Candidate work, ordered by cost — none authorized

1. **Seed by DC+ · INS · IT+ instead of `Unit(laws={...})`.** Small, needs no new
   environment, and makes the existing units' origins legible and revisable. §5.3.
2. **Let the inverse pivot's model catalogue grow from outside.** §4.
3. **Convert load-bearing boundary controls from stating to biting** — starting with
   the one this session paid for four times: a figure a document asserts about a
   measured world has no mechanism that fails when the world moves. §2.
4. **Reliability as a public decaying mark** rather than `Unit.peers`; test whether a
   mark-borne reliability reproduces what the private dict does. If it does, the
   register was never load-bearing; if it differs, that is the social objectification
   the C-series has never exhibited. §6.
5. **The environment-first D-series sitting** — clock, unit capacities, contested
   source with quantity and replenishment; the design rule *the environment must
   carry structure the unit does not already encode.*
6. **The socialization loop** as TUTOR_LOOP transposed. §5.3.

## 8 · Open decisions, the author's

- Whether this sitting becomes a **book chapter** or stays a working spec. Several
  sections (the received world as A → A; sophistication as plurality of antecedents;
  provided-versus-negotiated controls) read as doctrine rather than as notes.
- The **unruled assistant readings** flagged throughout, most consequentially: the
  boundary-placed-where-cheap unification (§1), guards-that-bite (§2), drift produces
  confident error (§3), the catalogue asymmetry (§4), and falsifiability-arrives-with-
  plurality (§5.2).
- Which of §7's candidates, in what order, and whether any precedes the scarcity test
  — which the §6 diagnosis suggests would otherwise test the *second* reason
  typification is inert while the first still stands.
