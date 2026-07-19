# The Tutor Loop — a Design

> **What this is.** The design pass the author authorized on 2026-07-17
> (THE_MEASURE_OF_KNOWLEDGE §6, decision 5): a tutor that chooses a learner's next
> challenge by the **learner's economy of research**, grades it with the incorruptible
> referee, and records everything — the attention socket rung 1 built
> (`attention_economy.py`), pointed at a human learner's growth. **Design only; nothing
> here is built.** The build is a separate authorization with the pre-registered
> criteria of §6.
>
> **Companions:** [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md) §5 (the
> doctrine this executes: weight-bearing scaffold = the measure read didactically) ·
> [BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md) §3 (the
> socket and its guards) · [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md)
> Doubt 4 (the ethical floor) · [GETTING_STARTED.md](GETTING_STARTED.md) +
> [EXEMPLARS.md](EXEMPLARS.md) (the existing on-ramp and challenge stock).
>
> *Written 2026-07-17. Assistant-drafted; open decisions in §7 are the author's.*

---

## 1 · Purpose

Bloom's two-sigma problem (1984): one-to-one tutoring outperforms classroom instruction
by about two standard deviations, and the open question has always been how to get the
tutor's *judgment* — what to ask next, when to let a thing fade, when to change register
— without the tutor. Arisbe's answer is that the judgment is an **attention economy over
the learner's model**: expected learning progress per unit cost, probed in the band
where severity is affordable (Vygotsky's zone of proximal development stated as a
scoring rule), with the calculus as a referee that lets the human teacher — or no
teacher at all — be fallible safely.

## 2 · The learner-ledger

The tutor's model of the learner: a per-learner record over **skill atoms** (the
teachable units — cut parity, line-of-identity binding, a specific rule's
applicability, reading order, each dragon's trap), each carrying the knowledge measure
read didactically:

- **K1 (severity-weighted record):** attempts and outcomes per skill, weighted by the
  challenge's difficulty tier — a pass on a discriminating challenge (one that
  separates rule-mastery from instance-memorization) counts for more than a pass on a
  drill.
- **K2 (durability):** retention across sessions — did the skill survive the gap since
  its last exercise?
- **K3 (compression):** does the learner wield the *rule* or the memorized instance?
  Operationalized: success on *unseen* instances of the same law-shape vs. success on
  repeats.
- **K4 (use):** recency of exercise; the fade clock that schedules re-challenge.

**Shape:** start as a side-store JSON (the scratch-store pattern — private, local-first,
regime-free), graduating to a Universe of Discourse only if provenance ever matters.
The grading events that feed it already exist: `same_graph` verdicts and
`legible_diff`'s finding categories (`structure`/`missing`/`extra`/`scope`/
`incidence`/`order`) from challenge mode — the diff categories are precisely the
skill-atom indexing, delivered in the learner's own sign vocabulary.

**The Doubt 4 clause, structural:** the ledger is the learner's **own record**, never
aggregated into a scalar rank of learners (the vector-not-scalar guard, ratified as the
measure's doctrine), never used to gate the learner's *access* — only to choose their
next challenge. For any learner other than the author, consent and local-first custody
are preconditions, not features.

## 3 · The economy mapping — the socket's third consumer

`AttentionEconomy` is reused **unchanged**; only the wants and the yield reading are
new (the same relationship the arithmetic world has to it):

| Socket concept | Tutor-loop realization |
|---|---|
| Want | A candidate challenge: from `CHALLENGE_BANK`'s gradient, the dragons, or a generated variant of a law-shape the learner has met |
| kind | The skill atom(s) the challenge exercises |
| cost | Estimated learner effort — difficulty tier and expected time; the ZPD is the **affordable-severity band**, adapted from the recent success rate |
| severity | What mastery a pass would *settle* — highest for challenges that discriminate rule-wielding from memorization (the K3 probes) |
| yield (observe) | **Learning progress**, not raw error: a first pass on a previously failed skill; a shrinking diff-finding count; a retention save at re-challenge |
| noisy-TV guard | A skill yielding no progress under repetition decays in priority — re-drilling a patternless error is the tutor's noisy TV |
| boredom detector | When nothing yields, **change register**, not intensity: gloss (`eg_to_english`), primer, a worked exemplar from the corpus — a different sign-channel, then return |
| musement | A budgeted fraction of sessions is free draw — play on the open canvas, ungraded; the pull that keeps the drive alive |
| decay | **Spaced re-challenge**: the fade clock schedules retrieval practice (the testing effect run deliberately); what fades unexercised and unmissed was scaffold, not structure |

## 4 · The dialogue protocol

The Endoporeutic Game as tutorial, three seats:

- **Teacher as Graphist** — voices the chosen challenge as a *doubt* scaled to the
  learner's M ("can this really be drawn with one cut?"). With no human teacher, the
  economy plays this seat mechanically; with one, the economy is the teacher's
  instrument panel, not their replacement.
- **Learner as Grapheus** — draws, defends, revises. The learner's model is *theirs*;
  the tutor models it (a level-4 act: knowledge about this learner's
  knowledge-formation) but never overwrites it.
- **The calculus as referee** — `same_graph` for the verdict, `legible_diff` for the
  *how-it-differs*, in EG vocabulary. This is what makes teacher fallibility safe: the
  learner can win, and the referee doesn't care who drew what (the method-gate; every
  attempt owed its uptake — the diff report *is* the uptake, never withheld).

**Scaffold removal is decay by design:** warrant is in-context competence and does not
transfer by testimony, so whatever the teacher's authority temporarily supplied must be
re-earned as the learner's own record — the ledger literally implements the fading that
Wood, Bruner & Ross built into the scaffolding concept from the start.

## 5 · Surfaces

Ergasterion's challenge mode is the arena (it already grades freehand drawings against
targets). The tutor adds one panel: the **next-challenge recommendation with its
reasons** — the want's skill, severity, cost, and the ledger evidence behind the choice,
rendered from `AttentionEconomy.snapshot()`. The pedagogy must be inspectable: the
picture-never-lies principle applies to the tutor's choices too (UI Transparency
Charter), and an inspectable tutor is also a *teachable* one — the learner who reads
the panel is learning the economy of research itself, which is the deepest skill on
offer.

## 6 · Staging and pre-registered criteria (for the eventual build)

- **T0 — the scripted learner (offline, deterministic, CI-safe).** A simulated learner
  with planted misconceptions (e.g. systematically misreading cut parity at depth ≥ 2)
  and a defined learning rule. Criteria, registered now:
  - **TS1** the economy-ordered tutor reaches each planted misconception's severe test
    and drives it to mastery in strictly fewer challenges than FIFO and
    deterministic-scatter orderings (the Fermat shape, didactic);
  - **TS2** a planted patternless-error generator never captures the docket (noisy-TV);
  - **TS3** spaced re-challenge beats a no-decay control on the retention curve;
  - **TS4** identical configurations yield identical challenge sequences;
  - **TS5** zero protected-module changes; the ledger is never reduced to a scalar over
    learners (the Doubt 4 clause, asserted in tests).
- **T1 — the author as live learner** (dogfooding; consent trivial, custody local).
- **T2 — a real neophyte**, only after T1's findings are disposed, with §2's consent
  and custody preconditions in force.

## 7 · Decisions — ✅ ALL RULED 2026-07-19 (the author, working the docket)

1. **Ledger shape** — side-store JSON first. RULED.
2. **The skill-atom inventory** — `legible_diff`'s finding categories + the dragons
   as the seed set. RULED.
3. **T0's misconception trio** — cut parity at depth ≥ 2; defining-vs-bound label
   misuse; argument-order misreading. RULED.
4. **Build timing** — T0 builds **after** the vault cycle's oracle loop has run one
   real round with the author (the learner-ledger is a person-model sibling and
   inherits what that round teaches about answer handling). RULED.
