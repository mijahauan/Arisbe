# The D-series — building the stake (design)

**Design sitting, 2026-08-02.** The successor to
[the design opening](2026-08-02-d-series-building-the-stake-design-opening.md), which
recorded the author's framing and left §3–§4 for his amendment. This spec records the
amendments he made and the design they entail. **Nothing here is built.**

Companions: [Examination VIII](2026-08-01-examination-viii-the-west-mapping-on-trial.md)
(what the autonomous form lacks, measured) ·
[the received-world sitting](2026-08-01-the-received-world-boundary-controls-and-socialization.md)
(environment-first) · [FROM_THERMODYNAMICS_TO_SEMIOSIS](../../FROM_THERMODYNAMICS_TO_SEMIOSIS.md)
(Secondness → Thirdness) · [THE_MEASURE_OF_KNOWLEDGE](../../THE_MEASURE_OF_KNOWLEDGE.md) §1
(the definition this is meant to make instrumentable) ·
[THE_KYTOS](../../THE_KYTOS.md) §1.3 (where an act's effect resides).

---

## 1 · What this builds, and what it does not

It builds **one world that subtracts.** The E-series meter charging `Σ|M|` per round, the
`MembraneLedger` scoring hits and misses, `Field.deliver` delivering and `Unit.anticipate`
anticipating — all of it exists, and all of it is an observer's scorecard, computed beside
the system and affecting nothing. This turns the reading into a subtraction. Nothing was
ever subtracted from anything; that is the whole omission.

It does **not** build a chooser, a sense organ for the reserve, a `die()`, a TTL, a
lifespan, a genome, a mutation operator, or a birth rule. Every one of those was
considered in the sitting and refused for a stated reason, recorded in §9.

**The limit of D-1, stated plainly so nothing reads past it.** With no reproduction the
world can only shrink. Units die, survivors coast, nothing new is tried. D-1 can measure
whether a stake bites at all; **it cannot measure evolution of unit policy**, and §7's
priors are written so that none of them pretends otherwise. What it *can* measure —
because the substrate already affords it — is selection over **laws**, which is §5's D-3
finding and §7's `P-D2`.

## 2 · The rulings this sitting produced

Seven, each with the reason it was made.

1. **Nothing is declined; a unit runs out.** The tariff subtracts regardless. No act is
   ever refused, no reserve is ever consulted, no chooser exists. `reserve ≤ 0` is death,
   which is §4's mortality prediction with nothing installed to produce it. The
   alternative — the world declining unaffordable acts — was refused because whoever fixes
   the **attempt order** fixes the priority, and which acts get dropped first is a
   substantive claim a designer would be making on the world's behalf.

2. **No sense organ, because there is nothing for one to reach.** Inspection of `c_unit.py`
   found that the unit has **no chooser anywhere**: `step` always anticipates and records,
   `publish` publishes everything held unconditionally, `ask` / `challenge` fire on their
   own internal conditions. What the C-series tests call "bounded attention" is not a
   scarcity but a stagger the *test driver* imposes
   (`tests/test_c_channels.py`: `if stagger == 1 or r % stagger == i`).
   `attention_economy.AttentionEconomy` exists and orders reaches by yield-per-cost, but is
   wired to the vault and arithmetic worlds and never to a C-series unit. A perceived
   reserve would therefore reach no decision, and building it a decision to reach is where
   a designer writes the answer and calls it emergent.

3. **Allocation is pro rata by matches, over a pool whose boundary defaults to
   per-community.** Rivalrous, so another unit's success is your loss and a crowded niche
   starves everyone in it — which is the only form under which community size could bend
   anything. The wider boundary (one pool serving every community, so communities compete
   directly) is **not a rival mechanism but the same rule with a wider `Σ`**, costs one
   named parameter to add, and is deferred to D-2 for two reasons: under a shared pool a
   community's figures move when a *neighbouring* community changes, which breaks the
   standing rule that a moved figure has exactly one cause on the very first measurement;
   and without a single community's own survival curve, extinction-by-crowding cannot be
   told from extinction-by-profligacy.

4. **Prices are calibrated to the measured baseline, not chosen.** §4 of the opening warned
   that four numbers is a small enough space to tune until something appears. Calibration
   removes the search: the numbers are derived from a zero-price arm of this same world,
   which serves twice — as the calibration source and as the control. See §4.

5. **The reach tariff prices acts MINTED, not marks met.** `Unit.read` returns the entire
   board minus the unit's own marks, with no filter and no chooser, so a price per mark
   read would make each unit's reach cost proportional to community size *by construction*:
   total cost `∝ N²`, **β = 2 written rather than found** — the exact defect Examination
   VIII convicted the West mapping of. Pricing minted acts leaves per-unit cost independent
   of `N`, so any superlinearity has to be earned. It also gives `whom_to_ask` — built, fed
   by `credit` and `standing_with`, and recorded in its own docstring as **measured inert**
   — a reason to matter, because a unit that asks the wrong peer now pays for nothing. That
   is not installing typification; the organ has been idle for want of a price.

6. **§4's sensitization prediction is restated as a finding-in-advance.** It read: *"as
   reserves fall, an unresolved doubt is income not earned, so urgency rises on its own."*
   Under rulings 1 and 2 there is nothing in a unit whose urgency *can* rise — doubting is
   unconditional and the reserve reaches no decision. Leaving it as a live prediction would
   put an unfalsifiable null on the books. It becomes the claim the rulings entail:
   **scarcity alone cannot produce sensitization.** §7's `P-D6` records it with its weak
   negative check acknowledged.

7. **The law, not the unit, is the replicator — and D-3 is habits as ink.** This ruling came
   from the author's objection to the whole preceding line of reasoning, and it corrected
   the assistant rather than the design. Recorded in §5.

## 3 · Architecture

### 3.1 Where the reserve lives

**Not on `Unit`.** The world holds it, keyed by unit id. This is not a discipline anyone
has to remember to keep — the architecture enforces ruling 2, because a unit cannot read
what it does not have. It also puts the reserve where THE_KYTOS §1.3 says an act's effect
resides: in the **resources**, outside the membrane, never in a private field beside the
act. `c_unit.py` is not modified.

### 3.2 The module

One new module, `src/d_world.py`, holding three things and no more.

| | |
|---|---|
| `Prices` | frozen: `pool_per_round`, `maintenance`, `reach`, `endowment` |
| `Reserves` | `{unit_id: amount}` with `charge` / `credit` / `alive` |
| `PricedWorld` | owns both; runs the round |

Deterministic and geometry-free, like every module in the C-series. Not protected.

### 3.3 The round

```
for each living unit:   unit.step(field, r)            # unchanged C-series code
                        unit.publish / ask / ...       # unchanged

charge maintenance:     E2 · (|facts| + |laws|)        # per living unit
charge reach:           E3 · (acts minted this round)  # counted off MarkBoard
allocate income:        E1 · (hits_i / Σ hits)         # pro rata, this round's hits
retire:                 reserve ≤ 0  →  leaves the community
```

Three consequences worth stating rather than leaving to be inferred.

- **A match is a `MembraneLedger` hit** — anticipated *and* arrived. Already computed;
  no new statistic is introduced, and the world therefore scores matches and nothing
  else, which is §6's discipline in the opening.
- **A miss carries no separate penalty.** It is already punished exactly once, by the
  maintenance paid on a law that earned nothing. A penalty would be another number
  buying nothing.
- **An act is a mark minted** — by `publish`, `ask`, `answer`, `challenge` or
  `corroborate`, without distinction between them. Charging the kinds at different rates
  would be a designer's claim about which speech is dear, which is exactly what ruling 5
  was made to avoid.
- **Acts are counted off `MarkBoard`**, which already attributes and dates every one.
  Nothing new is instrumented; an existing reading becomes a subtraction. This is the
  same discipline the 2026-07-31 re-measurement pass adopted after its own first draft
  was refused for building a private instrument beside the act.

### 3.4 It is five numbers, not four

The opening proposed four. Reserves starting at zero die in round one, before any income
can arrive, so an **endowment** is unavoidable. Named here rather than buried inside E1.
§4 derives it from measurement, so it is not a fifth *free* number — but it is a fifth
number and the register in §8 says so.

## 4 · The numbers, and how they are set

**Arm 0 — the same world at zero prices — is both the calibration source and the control.**
Calibrating against a C-series figure instead would inherit the imposed stagger and the
cyclic aperture convention; running the calibration inside the D-world removes both
dependencies.

Two conventions are **declared rather than derived**, and both are in §8's register:

- **E1 = 1, the numéraire.** The pool is the unit of account and the other prices are
  pool-shares.
- **A 50/50 split at baseline** — maintenance and reach each carry half the community's
  total cost, so neither holding nor speaking is the dearer habit before anything runs.

**The reference configuration, fixed once.** Arm 0 runs at **four units, PAIRS scheme,
eight seeds, 60 rounds, every unit inducing** (`induce=True`). Induction rather than
seeding, because `t*` is a fact about learning and a seeded unit never learns anything. The
resulting prices are then **used unchanged at both sizes**: re-calibrating at six units
would make the size comparison a comparison of two price regimes.

Arm 0 supplies `R` (rounds), `S_M` (model size summed over units and rounds), `S_A` (acts
minted, summed over units), and `t*` — the **median**, over units and seeds, of the round
at which a unit induces its first planted law. Median rather than first-or-mean, so one
lucky unit does not set the world's knife edge. The prices follow with nothing left to
choose:

```
E1 = 1
E2 = R / (2 · S_M)          maintenance, per held fact-or-law per round
E3 = R / (2 · S_A)          reach, per act minted
E0 = the cost of surviving rounds 0 … t*  at those prices
```

**Why the endowment is `t*` and not a horizon.** An austere endowment — one round's living
— kills every unit before induction can happen and the run is empty. A horizon chosen by
hand is a free parameter wearing a law's clothes. Reading it off `t*` makes the claim
sharp: **a unit that learns slower than the recorded baseline dies before it learns.**

**The community runs at a deficit, by exactly the hitless rounds.** The calibration assumes
the pool is fully allocated every round, but a round in which nobody hits allocates
nothing. So realised income is `R` minus the hitless rounds, and the shortfall is precisely
*how often nobody predicted anything correctly*. That is the world having teeth rather than
a defect, and it is preferred to the exact-break-even alternative (calibrating on
rounds-with-hits) for that reason. It is a third declared convention; §8 records it.

## 5 · Staging

| | | why here |
|---|---|---|
| **D-0** | retire `Unit.peers` (the opening's §7.3 / step 4) | **must precede pricing.** Once asking is priced, every `peers`-derived figure moves and the retirement's before/after becomes unreadable. `source_reliability` exists and is tested, so the replacement is ready. |
| **D-1a** | the priced world, seeding unchanged | the core build |
| **D-1b** | seed by DC+ · INS · IT+, with a price and a provenance (the opening's §7.2 / step 3) | separate stage, so one figure moves per cause. Under a priced world a unit's initial model needs a price and a provenance rather than an assignment; `notion_provenance` already supplies the held-until-affirmed shape. |
| **D-2** | the shared pool across communities | pre-registered, not built — ruling 3 |
| **D-3** | **habits as ink** | see below |

**The implementation plan that follows this spec covers D-0 and D-1a only.** D-1b, D-2 and
D-3 are recorded here so that the sequencing argument survives the sitting; each earns its
own spec when its turn comes.

### 5.1 D-3 — habits as ink

The sitting first proposed a genome: promote `corroboration_window`,
`corroborating_witnesses`, `replication_window`, `MIN_SUPPORT` and the induction criteria
to per-unit heritable values, add a birth rule and a mutation operator. **The author
refused it in one line — "yet, somehow, it developed without external programming."** The
refusal is right and it is the project's own standing rule applied one level up: *install
the problem, never the solution.* A designed genome installs the very thing it was meant
to explain, and the mutation operator is a designed variation-generator.

The correct question is what heredity emerged **from**: a substrate in which a pattern
could template itself at all, plus a world in which persisting was the only criterion.

**Our substrate already affords copying.** `publish` inscribes a law on the board; `adopt`
copies it into another unit's record. Variation is present too — different apertures and
`ObserverNoise` make units induce different laws from the same world. The missing term was
the third: **nothing died, so nothing was selected.** D-1 supplies it, and supplies it for
free. Once holders can die, **the law is a replicator**: laws that spread to units that
survive persist; laws whose holders starve go with them. No genome, no birth rule, no
mutation operator. The assistant had been looking for the thing that reproduces while it
was already reproducing.

**And the limit that names D-3.** Memetic copying varies *model content*. It cannot vary
*policy*, because `corroboration_window` and the induction criteria are not transmissible
— they are not ink, they are Python. Nature had no such split; at the molecular level the
code **is** the machinery. Ours is severed by the architecture.

So D-3 is: **a unit's dispositions written in the same medium as its model** — habits held
as EGs, published and adopted like any other mark, so that a habit can spread, mutate in
transmission, and die with its holder. That installs nothing the substrate does not already
afford, and it is about as Peircean a proposition as this codebase could make: habit as
inscribed law. Its real cost is an interpreter over held rules, which makes it a series
rather than a stage.

**The genome route is kept on the record as rejected, with its reason**, rather than
silently dropped — because nobody chooses a smuggle deliberately; they reach for the one
already written down.

## 6 · Arms and measurement

**Arms for D-1a.**

| | |
|---|---|
| **A0** | zero prices — control, and the calibration source |
| **A1** | calibrated prices |
| **A2a** | calibrated, mark channel occluded entirely (cost *and* benefit removed) |
| **A2b** | calibrated, acts still minted and charged but peers receive nothing (cost held, sign removed) |

**Why the ablation needs two arms.** A single occlusion is confounded: a unit with the
channel switched off mints no marks and therefore **pays no reach tariff**, so it could
outlive its peers by being mute rather than by being right. A2b is the honest ablation of
the putative sign, holding cost fixed. Reporting both is what keeps the confound visible.

**Configuration.** Eight seeds, 60 rounds, sizes 4 and 6 — the C-series conventions.

**There is no stagger.** The C-series "bounded attention" was a schedule imposed from
outside (ruling 2), and the whole point of a priced world is that a unit's rate should fall
out of what it can afford rather than be set. Under ruling 1 nothing is declined, so every
living unit attends every round and pays for it. The stagger is therefore **not carried
into the D-world at all** — which is the opening's *fix the price, let the quantum fall
out* applied to attendance, and another reason D-series figures do not compare with
C-series ones.

**One consequence to accept.** A size comparison needs the **PAIRS** aperture scheme at
*both* 4 and 6, since cyclic cannot give six distinct apertures (`apertures_for` refuses
rather than handing two units the same slice). PAIRS is not the C-series default, so
**D-series figures are not cross-comparable with C-series ones.** Stated now rather than
discovered later.

## 7 · Pre-registration

Committed before anything is built or run.

- **P-D1 · mortality is a consequence.** At calibrated prices at least one reserve reaches
  zero within 60 rounds in a majority of the eight seeds, with no `die()`, TTL or lifespan
  anywhere in `src/`. **Fails** if nobody ever dies, or if everybody dies in round one.

- **P-D2 · survival tracks mediation, and laws have lineages.** Two readings, the second
  being the sharper one the author's D-3 objection produced. (a) Units alive at round 60
  hold more planted true laws than units that died. (b) **Per law-content**: how many units
  held it, by adoption or by induction, for how long, and whether its holders lived —
  computable from `MarkBoard` (attributed, dated) against the reserves. **Fails** if
  survival is uncorrelated with holding true laws, which would say the world pays for
  something other than mediating well.

- **P-D3 · the ablation bites.** A2b shows shorter mean survival than A1. This is the
  standing falsifier *ablate the putative sign*, unrunnable until now because nothing
  survived or failed. **Fails** if occluding the sign changes nothing — in which case the
  marks were never doing work. A2a is reported beside it to expose the mute-and-rich
  confound.

- **P-D4 · typification becomes consequential.** Units whose asks go to higher-standing
  peers survive longer. **Testable only at six units**: the C-series measured that at four,
  all 939 uptake decisions had exactly one peer standing behind them, so there is nothing
  to prefer against. **Fails** if the preference remains inert once priced.

- **P-D5 · β ≈ 1, said first.** Per-unit cost is size-independent by construction (ruling
  5), so total community cost should scale about linearly from 4 to 6 units. A superlinear
  reading would be a surprise owing an explanation, not a result to celebrate. **β is not
  measured in D-1** — two sizes is not a scaling measurement. The realised ask/answer
  topology is *recorded* for a later series and nothing is fitted to it.

- **P-D6 · sensitization is absent, and structurally so.** No measure of urgency varies
  with reserve level, because none can (ruling 6). Recorded as a result of this sitting
  rather than of a run. **The negative check is weak** — nothing sensitization-like could
  appear in this build — and the prior earns its keep by saying so rather than by being
  refutable here.

## 8 · The cheat register — stated before building, not after

The opening's three, kept:

1. **E4 scores matches and nothing else.** No credit for communicating, corroborating or
   typifying. If those pay, they pay only by producing better anticipations.
2. **"Success" is not our standard.** The field delivers, a match is a match, and we get
   no vote — THE_MEASURE_OF_KNOWLEDGE §1(d)'s trepanning problem one level up.
3. **Pre-register.** §7 above, before any build.

Three this design adds:

4. **E1 = 1 and the 50/50 baseline split are declared, not derived.** The split in
   particular decides whether *holding* or *speaking* is the dearer habit, and a different
   one could change who dies.
5. **The endowment inherits `t*` from the measured learner.** A faster induction routine
   would shrink it and kill more units. The knife edge is set by an artefact of the
   baseline, not by the world.
6. **Income is calibrated against all rounds, so the community runs a deficit equal to its
   hitless rounds** (§4). Chosen deliberately over exact break-even, and therefore a choice
   that has to be declared.

## 9 · Refused, and why

Each of these was considered in the sitting and refused for a reason, recorded so the next
reader does not rediscover the hole and fill it.

- **A chooser** — where a designer writes the answer and calls it emergent (ruling 1).
- **A sense organ for the reserve** — reaches no decision without a chooser, so it changes
  nothing while reopening what ruling 1 closed (ruling 2).
- **An attempt-ordering rule** — the order *is* the priority, and nobody argued for it.
- **A separate penalty for a miss** — already punished once, by maintenance paid on a law
  that earned nothing.
- **A price per mark read** — installs `β = 2` (ruling 5).
- **A genome, a birth rule, a mutation operator** — installs the explanandum (§5.1).
- **Building the genome and the stake together** — relaxes the uniformity guard and
  introduces the mutation operator in the same pass that first subtracts a cost, so a null
  could not be attributed and a positive result could not be trusted.

Deferred rather than refused, and named so the hole stays visible:

- The shared pool (D-2).
- **E1 as a replenishing stock** rather than a per-round flow — the opening's "quantity +
  replenishment rate" collapsed into one number here.
- Habits as ink (D-3), with its interpreter over held rules.
- The credential build (Examination VII's stage 4 part (c)), which still blocks weighted
  witnesses.

## 10 · Testing

Beyond the ordinary unit coverage of `Prices` / `Reserves` / `PricedWorld`:

- **At zero prices the wrapper is inert.** A run through `PricedWorld` with all prices at
  zero is byte-identical to the same community run without it — same units, same field,
  same board, same scheme. This is a claim about the wrapper changing nothing, **not** a
  claim to reproduce published C-series figures, which were measured under a different
  aperture scheme and an imposed stagger (§6).
- **A determinism canary** — two runs agree, as `test_c_stage_gates.py` already keeps for
  the C-series.
- **Two adversarial checks.** That no `die()`, TTL or lifespan exists in `src/` — the
  mortality prior is worthless if something installs it. And that `Unit` carries no reserve
  attribute, so there is nothing for a future chooser to read by accident.
- **The seat cap is a refusal, not a truncation** — `apertures_for` already refuses more
  units than distinct slices, and D-1 must not paper over it.

## 11 · Open for the author

- The 50/50 baseline split (§4) is the assistant's, chosen for symmetry. Whether holding or
  speaking *should* be the dearer habit is his to rule, and the ruling would move who dies.
- Whether D-2's shared pool should serve communities of **equal or unequal** size — the
  latter makes the niche argument sharper and the measurement harder.
- Whether D-0 (retiring `Unit.peers`) should carry its before/after reading into this
  spec's record or stand as its own note.
