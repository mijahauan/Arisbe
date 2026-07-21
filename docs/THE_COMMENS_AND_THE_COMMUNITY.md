# The Commens and the Community

> **What this is.** Design-of-record for a doctrinal arc built in dialogue on 2026-07-19/20:
> the UoD/commens distinction, why institutionalization cannot occur in an individual, the
> three Endoporeutic Game (EPG) roles as a *model* of that institution, the S/A
> parameterization and its West correspondence, the refusal of "final," and the standing
> statement that the higher-order frontier is deliberately not crossed. The author's spine is
> ratified doctrine; assistant elaborations are carried but marked `*[flagged]*` and gathered
> in [§11](#11--open-verdicts) for later ruling. **Not in `_quarto.yml`** — book membership
> deferred to workstream B.
>
> *Written 2026-07-20, assistant-drafted from the sitting, the spine the author's.*

---

> By the hearing of the ear I heard You,
> and now my eye has seen You.
> Therefore do I recant, and I repent in dust and ashes.
>
> — Job 42:5–6, trans. Robert Alter

---

## 1 · The pair: UoD and commens *[ratified]*

The Universe of Discourse (UoD) is the immediately accessible, controllable, and attested
internal model *inside* a [kytos](THE_KYTOS.md#1--the-unit-named)'s membrane — what a kytos
*thinks with*. It is what Arisbe already builds: the synchronic EGI plus its diachronic
history, internalized and attested at the [§3.3](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
boundary.

The commens is the pair's other half, and it is not an Arisbe structure. It is the
between/outside/before/after that makes communication possible without being possessed —
interacted-with, never internalized. It is a **regulative** concept, not something to be
operationalized: there is no data structure in this codebase, and there should never be one,
called "the commens."

**The category-mistake warning, stated explicitly:** the attested corpus is the
*internalized* UoD, **not** the commens. Naming the corpus "the commens" was an error made and
corrected in this sitting, and it is the single most important sentence in this document —
every other section depends on keeping the two apart.

**The commens is a social construct** (author, 2026-07-20), in Berger and Luckmann's precise
sense: an objectivated reality that is *real for its participants* — it confronts them with
facticity and exceeds any one of them — and yet is **sustained only by participation**. It is
not pre-given, not timeless, not standing on its own the way a Platonic form would stand: *if
we do not participate, it disappears.* Its "before us and after us" character is the
persistence of a continuously reproduced activity across finite, mortal participants, not the
standing of an eternal thing. It is **open, and therefore precarious** — the same act that
makes it real (participation) is the only thing keeping it there.

**Import and export** are the two directions of traffic across the membrane: import
internalizes a portion of the outside into a UoD; export contributes to the outside, which
then becomes part of *others'* potential commens — and, in doing so, helps sustain the
commens itself. Neither direction is automatic or costless; both are acts.

## 2 · What the pair grounds *[flagged]*

Two consequences follow from keeping the UoD/commens pair exactly as drawn:

*[flagged]* (a) The knowledge measure ([THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md))
is a **vector, never a scalar over agents** *because* no commens-scaled denominator exists to
normalize across agents. This is not a policy choice made for prudence — it is a consequence
of the un-possessability of the commens itself: there is no shared, measurable "whole" that a
scalar could divide by, since the commens is precarious and un-owned rather than a fixed
quantity held in reserve.

*[flagged]* (b) The correspondence-not-truth floor — the standing refusal to claim that §3.3
attestation certifies truth rather than internal correspondence — is the instance's own
acknowledgment that its UoD is a finite internalization facing a commens it does not own. A
kytos can attest that its picture and its proposition agree with each other; it cannot attest
that either agrees with a commens it can only interact with, never hold.

## 3 · The institution and the sub-roles *[ratified spine / flagged detail]*

Berger and Luckmann's account of institutionalization: it is a **reciprocal typification of
habitualized actions by types of actors**. Actor-type A does typical action X, actor-type B
does typical action Y, and each anticipates the other's typical action as a matter of course —
that reciprocal anticipation, sedimented over time and handed to newcomers as "how it's done,"
*is* an institution. The load-bearing consequence: institutionalization **cannot occur in an
individual**. It takes at least two distinguishable types of actor, actually reciprocating,
for an institution to exist.

This is why Arisbe's three EPG roles — Graphist, Grapheus, Agonothetes — are not, by
themselves, an institution. They are **internalized typifications** carried as sub-roles
within one process (see `agon_llm.py`'s three roles, or the mechanical panel in
`agon_evolution.py`). Conant and Ashby's good-regulator theorem (requisite variety: a
regulator that manages a system well must, in effect, contain a model of that system) supplies
the right frame: to manage its own belief-fixation, a kytos's process must model the social
division of labor by which belief actually gets fixed elsewhere — Graphist doubts, Grapheus
defends, Agonothetes judges. The three roles are a **model of** the institution of inquiry,
carried internally as sub-roles — never an **instance of** that institution. Model-of, never
instance-of.

*[flagged]* The Agonothetes-negotiation account, stated precisely: the Agonothetes does not
decide *truth* — the peel does that, mechanically, against the reference model. What the
Agonothetes decides is what a round's outcome does to the *UoD's own attested record*:
resolving the non-trivial cases by policy priority among an `Agonothetes` panel's votes, by
forking the DAG to carry genuine dissent forward as siblings (`agon_llm.py`'s
`branch_votes` hook), or, with an LLM judge, by choosing among votes already cast without
fabricating a disposition. **Commens-entry is a separate act** — circulation and uptake by
other kytē — never automatic just because a round resolved inside one process.

## 4 · S and A, made measurable *[ratified spine / flagged coupling]*

The Minimal Predictive Automaton's decomposition (`docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md`)
becomes, read at the kytos's scale, two named and separately measurable capabilities:

**S** — the UoD-management capability, the **interior**. This is already instrumented
throughout the codebase: |M| (the resident model's size), the K3 materialization/compression
ratio (`model_materialization.materialization_ratio`), the peel's super-linear cost curve, the
decay TTL (`UsageLedger`), admission/retraction rates (`model_revision.py`,
`m_steps.py`).

**A** — the interaction capability, the **membrane**. This is the automaton's *missing fifth*,
the action arm first reached at rung 1 (`attention_economy.py`), and honestly the younger,
thinner-instrumented axis: import/export throughput, proposal/doubt rate, horizon size
(`Horizon`/`HorizonItem`), severity-weighted yield.

*[flagged]* S and A are **not independent** — they are coupled by one shared attention budget.
The interesting variable is not either axis alone but the **allocation** between them, and
**poise is its reading** (`agon_metalearning.poise_report`): rigidity names S starving A (the
process stops engaging with the outside), thrash names A starving S (the process never settles
enough to consolidate what it takes in).

## 5 · West, operationalized *[ratified intent / flagged mapping]*

Because each kytos now has measurable S, measurable A, and a measurable allocation between
them, a community of kytē becomes something that can be modeled — "possibly to better
understand the components of mentation" (the author's own hedge, kept as stated: a possibility
being pursued, not a settled finding).

*[flagged]* The specific conjecture under that possibility: **sublinear cost scaling** from a
shared substrate (the commens functioning as common infrastructure that many kytē draw on
without each rebuilding it) paired with **superlinear production or K-generation** from
interaction density (more connected kytē producing disproportionately more knowledge, not
merely more talk). The conjecture is to be fit against the exponents recovered from the Q-B
apportionment / West experiment (the Q-B sketch, CURRENT_PLAN.md item -8: one big
Arisbe vs. distributed kytē plus a coordinator, measuring cost curves, K3 exponents, and
poise). This is a **conjecture-until-measured**, and stays one permanently in the sense that
matters here — the measurement itself is an ongoing act, never a closing one (see [§7](#7--no-final)).

## 6 · The rung-boundary *[flagged formulation]*

*[flagged]* Three rungs, one boundary that matters:

- **sub-role** — models a *type of actor* (Graphist, Grapheus, Agonothetes as internalized
  typifications, §3).
- **instance** — models the *institution*: a good regulator with requisite internal variety,
  one process carrying all three sub-roles.
- **community** — genuine reciprocal typification: the actual institution, the actual
  commens, realized among distinct kytē rather than modeled within one.

The jump from instance to community is a change in **kind**, not degree. Genuine
institutionalization and the commens itself are **community-level emergents**, not properties
an instance can approximate by internal elaboration however sophisticated — this is the same
claim as §3's "cannot occur in an individual," restated as a rung boundary and pointed at the
open Q-B community-of-kytē question.

## 7 · No "final" *[ratified]*

The ink/act separation, applied to Peircean convergence: to scribe a name for inquiry's
supposed terminus — the phrase this section's ban-list forbids below — into a document or a
UI label is to lift an act's *telos* — the direction an inquiry tends toward — into static
ink, the same move the dragon-9 reification names as an error elsewhere in the codebase's
vocabulary. What survives, and all that survives, is convergence as a **direction of an
act**, never a nameable terminus.

This is enforced by the machinery itself, not merely by editorial discipline: the diachronic
DAG has no terminal leaf; □ (necessity, `modal_query.py`) is read *at a time* over the
reachable states and stays defeasible as the history grows; the ink an inquiry leaves behind
is **re-runnable act-record** — the polarity gate (`test_corpus_polarity_discipline.py`)
recomputes every recorded verdict, chains replay, §3.3 re-attests. Nothing is ever sealed.

The commens, correspondingly, is **un-closed in space** (no one holds it, §1) and **un-closed
in time** (no one ends it, §1's precarity).

**Editorial ban-list, standing for the whole corpus.** The following words and phrases scribe
a terminus and are licensed to appear in this codebase's documentation **only inside this
ban-list**, quoted, to forbid them — never as an assertion anywhere else:

> "final," "converges to [truth]," "the answer"

The register to use instead: "tends," "the current best-attested," "open."

## 8 · Keeping thirdness where it belongs *[flagged formulation / ratified direction]*

The standing statement, ratified: the higher-order frontier is **deliberately not crossed**.
Thirdness — mediation, law, interpretation, in Peirce's own sense — is realized
**operationally, not representationally** throughout Arisbe: in the teridentity ink (the
reduction thesis, `docs/CATEGORIES_AND_THE_THREE_PARTS.md`), in §3.3 attestation (the
interpretant treated as a prerequisite for correspondence rather than an afterthought), in the
diachronic DAG (would-be, modality, read without a modal mark per
`docs/MODALITY_WITHOUT_GAMMA.md`), and in the Agonothetes (the game's own interpretant,
deciding what a round means for the record, §3). Thirdness is **not** realized as a
higher-order object layer one quantifies over, and **not** realized as a Gamma tincture.

*[flagged]* Dau's Chapter 26 reduction — teridentity plus the algebraic operations construct
every finitary relation — is read here as the proof that the ascent to a genuine higher-order
layer is **optional for expressiveness**: nothing first-order-expressible is out of reach
without it. Only iconicity (wanting the *picture itself* to show a graph-about-a-graph
relationship, rather than achieving the same expressiveness by other first-order means) could
ever motivate crossing that frontier.

This is the doctrinal ground under [Mention-ascent](GLOSSARY.md#mention-ascent) — Arisbe's
scoped, conservative slice of Gamma (quotation as mention-not-use, B-min) — which crosses only
as much of the frontier as iconicity demands and no further.

## 9 · The honesty guard *[flagged]*

*[flagged]* The automated EPG (`agon_llm.py`'s three LLM roles, `agon_evolution.py`'s panel)
**does not institutionalize**, and claiming otherwise would be the precise Berger-and-Luckmann
reification this document exists to forbid: mistaking an internalized model for the social
reality it models. Three LLM roles remain **sub-roles within one individual's process** even
when each is played by a separately-invoked model — the process is still one UoD's history,
one kytos's interior. Branch-on-disagreement (the DAG fork on irreducible Agonothetes
disagreement, §3) is the nearest gesture toward genuine plurality the automated loop makes,
and it is still **intra-individual**: the branches are siblings in one process's diachronic
DAG, not distinct actors reciprocating.

This extends the built/evidenced/conjectured honesty ledger already kept in
[THE_KYTOS.md §5](THE_KYTOS.md) — the automated EPG is built and evidenced as a model of
institutional reasoning; it is not evidence of an institution.

## 10 · The entailment: connection outward *[ratified]*

The solitary ceiling — what one kytos, however well-instrumented, can achieve alone — sits
below the community's **by kind, not effort** (§6). Some components of knowledge, K2 read at
community scale foremost among them, and the commens itself, are simply unavailable to one
agent working harder; no amount of internal elaboration reaches them, because they are
community-level emergents (§6).

And because the commens is a social construct sustained only by participation (§1), connecting
outward is not merely instrumental — it does not just *reach* a standing resource that would
otherwise sit there waiting. Connecting outward **keeps the commens in being**. Withdrawal,
correspondingly, is not only self-limiting for the withdrawing kytos; it is **dissolving** for
the commens itself, in however small a degree. The need to connect is a need to **sustain**,
not only a need to access.

Publication is the first push of this project's own membrane into the scholarly commens; the
purpose of the coming documentation sweep (workstream B) is **legibility** — takeable-up by
readers who were not present while any of this was made — not merely tidiness. Arisbe-the-project
is itself a kytos: its UoD is what author and assistant have internalized and attested here,
and it grows only from what crosses its membrane from a commens it does not and cannot
possess. This is the FIDELITY-licensed reading of "Arisbe as a proposition in the wider EPG"
([FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md)), now standing on the right
ontology beneath it.

## 11 · Open verdicts

The following are assistant elaborations the author engaged with in the 2026-07-19/20 sitting
but has not yet ruled on. Each is carried in place above, marked `*[flagged]*`, and restated
here as a crisp question for a later ruling. Nothing below is settled doctrine.

1. **§2(a) — the vector-not-scalar ground.** Is "no commens-scaled denominator exists to
   normalize across agents" the *correct and complete* ground for the measure being a vector
   rather than a scalar, or is this one ground among others (e.g., a separate prudential
   argument against ranking agents) that should be stated alongside it rather than as the sole
   reason?
2. **§2(b) — correspondence-not-truth as self-acknowledgment.** Accept or revise the reading
   that the correspondence-not-truth floor *is* a UoD's acknowledgment of facing an un-owned
   commens, as opposed to a narrower, purely formal reading (§3.3 attests structural agreement
   and nothing about truth-conditions at all, independent of any commens-facing story)?
3. **§3-detail — the Agonothetes-negotiation account.** Is the three-way resolution mechanism
   (priority among votes / DAG-fork on dissent / LLM choice-without-fabrication) the right and
   complete inventory of how the Agonothetes decides record-effects, or does it need a fourth
   case, and is "commens-entry is a separate act" stated with the right emphasis?
4. **§4-coupling — S/A coupled by one attention budget, poise as its reading.** Rule on
   whether this coupling claim is doctrine (S and A *necessarily* share one budget by
   construction) or a currently-true implementation fact that a future architecture could
   relax; and whether "poise is its reading" should be stated more strongly (poise *measures*
   allocation) or more cautiously (poise *correlates with* allocation).
5. **§5-mapping — the West conjecture's specific shape.** Rule on the sublinear-cost /
   superlinear-production conjecture as stated: is this the right pair of exponent directions
   to pre-register for the Q-B apportionment experiment, or should the conjecture be phrased
   more provisionally (direction unknown, magnitude the only pre-registered claim) until the
   experiment exists?
6. **§6 — the rung-boundary formulation.** Rule on whether "sub-role → instance → community"
   is the right three-rung ladder, and whether "a change in kind, not degree" at the top jump
   is the correct way to state the boundary, versus some gentler formulation (e.g., a
   continuum with a sharp practical threshold rather than a categorical kind-change).
7. **§8-formulation — Dau Ch. 26 as proof of optionality.** Rule on whether "only iconicity
   could ever motivate crossing the frontier" is too strong a claim (are there other honest
   motivations for a full higher-order layer besides wanting the picture itself to show
   graphs-about-graphs?), and whether the formulation of thirdness's four operational homes
   (teridentity / §3.3 / the DAG / the Agonothetes) is complete or missing a fifth.
8. **§9 — the honesty guard's scope.** Rule on whether "branch-on-disagreement is the nearest
   gesture toward genuine plurality, and still intra-individual" fully closes the question of
   whether a sufficiently elaborate automated EPG (many independently-invoked LLM instances,
   deep branching) could ever cross into modeling something institution-*like* in a stronger
   sense than "model-of," or whether that possibility should be left more explicitly open.

## Cross-links

[World-scroll](GLOSSARY.md#world-scroll) · [Kytos](GLOSSARY.md#kytos-the-semiotic-cell) ·
[Mention-ascent](GLOSSARY.md#mention-ascent) ·
[THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md) ·
[BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md) ·
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) ·
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) ·
[CATEGORIES_AND_THE_THREE_PARTS.md](CATEGORIES_AND_THE_THREE_PARTS.md) ·
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md)
