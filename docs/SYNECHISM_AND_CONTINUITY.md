# Synechism and Continuity — the Connective Doctrine

> **What this is.** The housing for Peirce's **synechism** — the doctrine of continuity —
> in the reorganized vision: it enters **Stratum II** as the *connective doctrine*, the
> medium the five tributaries (Conway/aLife · West scaling · Berger & Luckmann · the
> AlternativeSet/erotetics unification · the deliberative-interval reading of agency)
> flow in, and the reason one kytos anatomy recurs across scales — **not a sixth
> tributary**. The compact formula the placement rests on: *continuity is Thirdness
> pushed to its ultimate.* Stratum II is a proposition scribed into the wider
> Endoporeutic Game, so this document **proposes a reading and grades its own claims**
> (grades: *built-and-gated* · *measured-with-priors* · *ratified-doctrine* ·
> *queued-conjecture*); it asserts no settled truth about Peirce scholarship, and none
> about the system beyond what is built or measured.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) (Stratum II, the housing) ·
> [THE_KYTOS.md](THE_KYTOS.md) (the recurring anatomy this doctrine explains) ·
> [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md) §"The graded
> concordance map" (the claim-by-claim examination) ·
> [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) (the
> correspondence contract the homotopy reading re-describes) ·
> [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) (the ledger's form model) ·
> [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) (the trajectory reading the
> DAG row leans on).
>
> *Written 2026-07-26, assistant-drafted, placement and doctrine the author's rulings.*

---

## The placement: medium, not tributary

Each tributary of Stratum II is a body of outside work the project engages on its
merits. Synechism is not one more such body: it is the **medium** in which the
tributaries meet — the claim that the same membrane-and-loop unit recurs from atom to
community (THE_KYTOS.md §2) is intelligible *only if* the levels are continuous with
one another rather than a stack of disjoint kinds. Where a tributary contributes a
mechanism or a measurement, synechism contributes the *connective tissue*: it is what
licenses reading West's allometry, Berger & Luckmann's objectivation, and the
deliberative interval as views of **one** continuum of semiosis rather than three
unrelated subjects. That is why it is housed as doctrine, not concordance.

The discipline this document holds itself to, stated once and enforced by the ledger
below: **synechism here always points at a named invariant or a logged departure,
never a hand-wave.**

## Where continuity is already operational, previously unnamed

The heart of the doctrine is not a promise but a *re-description*: most of what
synechism demands is already shipped and gated — it simply had no name. Each item
below names the machinery and its grade.

### (a) Regime 3 is homotopy — *built-and-gated*

The presentation-only regime (LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3) permits
**continuous deformation** of a drawing — move a vertex, reshape a cut, reroute a
ligature — and forbids exactly the deformations that would change what the drawing
*is*: boundary crossings. The invariants the correspondence check
(LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3) reads off the drawn shape — containment in
the drawn curve, the per-ligature **crossing-sequence** (the ordered multiset of cuts
a ligature must cross) — are *topological invariants of continuous deformation*. So
the proposition is not any one drawing: **it is the homotopy class of its drawings**,
and every regime-3 operation moves within the class. Peirce's line of identity as a
true continuum survives here precisely as *invariance under deformation* — the line's
identity is not its coordinates but what no legal deformation can change. Machinery:
`presentation_ops.py` (the regime-3 algebra, `Regime3Violation` at the class
boundary), the crossing-sequence machinery shared with `natural_layout.py`,
`correspondence_attestation.py`; gates: `tests/test_presentation_ops.py`,
`tests/test_correspondence_invariant.py` (regime-3 non-interference).

### (b) The horizon is the acknowledged continuum — *built-and-gated*

A discrete system that pretended its marks exhausted the world would have quietly
denied continuity. The **horizon registers** (`attention_economy.Horizon`, the
not-yet-legible retained and counted), the AlternativeSet's attestation discipline
(AS1–AS4, `alternative_index.py`), and the standing **count-or-refuse** rule
(`probe_feed.py`: a want the feed cannot voice is refused and counted, never silently
dropped) are the system's standing acknowledgment of the **unmarked continuum beyond
its marks**. And an AlternativeRecord is a *marked discontinuity* in Peirce's exact
sense — a point is not found in a continuum but *created by marking it*; a question
becomes a discrete, addressable record only when an act of surveying or peeling marks
it out of the undifferentiated not-yet-asked. Gates: `tests/test_alternative_loop.py`,
`tests/test_alternative_persistence.py`, `tests/test_alternative_survey.py`.

### (c) Refusals of premature discretization — *built-and-gated*

Three standing refusals keep the system from snapping continua to points before the
record earns it: **Kleene UNKNOWN** (`semantic_game.Verdict3` — a sound open-world
verdict is three-valued; absence of evidence is never forced to FALSE), **generic
lines of identity** (a line asserts *something* without discretizing it to a named
individual until identity is earned), and the **vector-never-scalar guards**
(THE_MEASURE_OF_KNOWLEDGE.md — no agent's standing is collapsed to one number).
Gates: `tests/test_semantic_game.py`, the measure's guards as stated doctrine.

### (d) The commens grounded in synechism — *ratified-doctrine*

Peirce's late formulation — "a person is not absolutely an individual … the circle of
society is a sort of loosely compacted person" (*What Pragmatism Is*, 1905) — is
synechism applied to persons: the boundary of an individual is real but not absolute.
The kytos as **anti-monad** (all windows — nothing in it exists except by traffic
across its membrane, THE_KYTOS.md §1) and the ruling that **judgment is objectivated,
never owned** (THE_COMMENS_AND_THE_COMMUNITY.md §2(c): the licence to judge and its
rationale reside in the objectivated institutionalizations, not in the seat's
occupant) are that formulation operationalized. The commens is what a synechist
*expects* where a nominalist expects an aggregate of self-contained minds.

### (e) West scaling as measured synechism — *measured-with-priors* results, *queued-conjecture* reading

The West-in-kytē program's results are real and pre-registered: E1–E3b ran against
declared priors and the run logs record which held and which fell. The E3b basin map
(`runs/WEST_E3B_LOG.md`) carries the honest complication: the **continuum of possible
organizations condenses into discrete basins by history's marking** — all 36 starts
terminate at the N=3 granularity, yet fragment into 19 distinct local optima, with a
dominant family holding 75% of the attractor mass within 1.4% of the cost floor.
Points-from-continua, observed in a cost landscape: the walk's history *marks* which
of continuum-many organizations become actual. But the two levels must not be
conflated — the measurements are **measured-with-priors**; the *synechist reading* of
them (that this condensation instantiates continuity marking itself into discreteness)
remains **queued-conjecture** even though what it reads is measured.

### (f) The chain: discrete marks on continuous semiosis — *built-and-gated* machinery, *queued-conjecture* reading

A transformation chain is a sequence of discrete, attested marks; the semiosis it
records — the deliberation, the considering, the taking-up — is not itself discrete.
The record is complete *as a record* (every licensed move accounted) while the
**accounting never exhausts the deliberation**: nothing in a transcript marks which
continuum of consideration lay between two steps, and no transcript distinguishes a
fated step from a taken one. That gap is an anti-foretelling ground, and it feeds the
deliberative-interval reading of agency. The free-will reading itself is
**queued-conjecture** — named for the commens rung's examination, deliberately *not*
folded into doctrine here.

## The continuity ledger

In the style of the departures ledger (FIDELITY_A_PLAIN_ACCOUNT.md and its rigorous
companions): every deliberate discretization the system makes is **named**, with the
continuous thing it stands in for and the **invariant that preserves the continuum's
shadow**. A discretization with no named shadow is a debt, not an economy.

| Discretization | Stands in for | The preserved shadow | Where enforced |
|---|---|---|---|
| **Dau ligatures** — vertices and edges | the continuous line of identity | the per-ligature **crossing-sequence** (the required-crossing multiset): the line's topology survives its segmentation | `presentation_ops.crossing_sequence` / `natural_layout.py`; `tests/test_correspondence_invariant.py` |
| **TTL disuse-decay** — a step function | the law of mind's continuous fading of unexercised habit | the *faded* tense in the record: decay is a licensed ERA carrying `flavor: "pruned:disuse"`, counted in digests, split from refutation in stick-rates | `agon_evolution.UsageLedger` / `live_runner.py` (ttl) / `m_steps.retract_step`; `tests/test_agon_evolution.py`, `tests/test_live_runner.py` |
| **DAG states** — discrete snapshots | continuous development of a Universe of Discourse | the **branching structure itself**: ◇/□ read off whole trajectories, not states (MODALITY_WITHOUT_GAMMA.md) | `egi_transformation_history.py` / `modal_query.py`; `tests/test_organon_routes.py` (the modal lens) |
| **Bounded registers** — finite S/A capacities | an unbounded field of possible attention | **counted drops + the horizon**: nothing silently vanishes at a capacity; the not-yet-legible is retained, counted, re-attemptable | `attention_economy.py` (bounded registers, `Horizon`) / `alternative_trace.BoundedRegister`; `tests/test_alternative_loop.py`, `tests/test_alternative_persistence.py` |
| **Layout coordinates** — discrete DTO geometry | the continuous plane of drawing | **regime-3 homotopy-class invariance**: any one drawing is a representative; the class is the fact (item (a) above) | `layout_dto.py` / `presentation_ops.py` / `correspondence_attestation.py`; `tests/test_presentation_ops.py` |
| **Three-valued verdicts** — TRUE/FALSE/UNKNOWN | the continuum of evidential standing | **UNKNOWN as the honest middle** (sound open-world: absence never snaps to denial) + the transcript recording *how far* the peel got | `semantic_game.Verdict3`; `tests/test_semantic_game.py` |
| **Live segments** — a world stream chopped into polls and checkpoints | the world's continuous delivery | queued-never-truncated batches; cross-segment episode accumulation; **the decay clock continuing, not resetting**, across checkpoint and resume | `live_runner.py` (segment/checkpoint/resume); `tests/test_live_runner.py` |

## The scholarly frontier, named not claimed — *queued*

Peirce's mature continuum is **supermultitudinous**: a true continuum exceeds any
multitude of points, and its points exist only *potentially*, actualized by marking —
a doctrine at odds with the point-set continuum of standard analysis, and echoed in
modern non-punctate mathematics (Bell's smooth infinitesimal analysis and the
smooth-topos line, where a continuum is likewise not a set of points). Whether
Arisbe's operational continuities — homotopy classes of drawings, horizons of unmarked
questions, condensing basins — are better modeled by the supermultitudinous continuum
than by the point-set one is a genuine question this project has not earned an answer
to. It stays a **frontier**: one paragraph, no claim, grade *queued-conjecture*.
