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
lifespan, a genome, or a mutation operator. Every one was considered in the sitting and
refused for a stated reason, recorded in §9.

### 1.1 It is not an attempt to recover the West correspondence

This has to be said at the top, because the opening's §4 pre-registered the reach gradient
as "the conjecture most worth testing" and **the design's own rulings make it unreachable**
(§7's `P-D5`). Under a conservative world the total metabolic cost is pinned to the source
and does not vary with community size at all, and the price of reaching *falls* as the
community grows rather than rising with its extent — the opposite of condition 9.

So the D-series builds the stake because **the stake is what knowledge requires**
(THE_MEASURE_OF_KNOWLEDGE §1: a situation in which mediation brought a genuine doubt to
rest), not because it would yield an exponent. Examination VIII's `predicted-absent` grade
stands undisturbed, and §7 pre-registers that **no exponent is measurable here, by
construction**, so that nobody later fits one to an identity.

### 1.2 The limit that remains

Model content can now vary, spread and be selected — the law is a replicator (§5.1). **Unit
policy cannot**, because `corroboration_window` and the induction criteria are not
transmissible; they are Python, not ink. D-1 therefore measures whether a stake bites and
whether laws have lineages. It does not measure the evolution of policy, and §7's priors
are written so that none of them pretends otherwise. That gap is what D-3 names.

## 2 · The rulings this sitting produced

Nine. The last three came from the author applying one principle — *let it develop rather
than set it* — three times running, each application removing a parameter the assistant had
installed.

1. **Nothing is declined; a unit runs out.** The tariff subtracts regardless. No act is
   ever refused, no reserve is ever consulted, no chooser exists. `reserve ≤ 0` is death,
   which is the opening's mortality prediction with nothing installed to produce it. The
   alternative — the world declining unaffordable acts — was refused because whoever fixes
   the **attempt order** fixes the priority, and which acts get dropped first is a
   substantive claim a designer would be making on the world's behalf.

2. **No sense organ, because there is nothing for one to reach.** Inspection of `c_unit.py`
   found the unit has **no chooser anywhere**: `step` always anticipates and records,
   `publish` publishes everything held unconditionally, `ask` / `challenge` fire on their
   own internal conditions. What the C-series tests call "bounded attention" is not a
   scarcity but a stagger the *test driver* imposes
   (`tests/test_c_channels.py`: `if stagger == 1 or r % stagger == i`).
   `attention_economy.AttentionEconomy` exists and orders reaches by yield-per-cost, but is
   wired to the vault and arithmetic worlds and never to a C-series unit. A perceived
   reserve would therefore reach no decision, and building it a decision to reach is where
   a designer writes the answer and calls it emergent.

3. **Allocation is pro rata by matches, over a pool whose boundary defaults to
   per-community.** Rivalrous, so another unit's success is your loss. The wider boundary
   (one pool serving every community) is **not a rival mechanism but the same rule with a
   wider `Σ`**, and is deferred to D-2: under a shared pool a community's figures move when
   a *neighbouring* community changes, which breaks the standing rule that a moved figure
   has exactly one cause on the very first measurement.

4. **The reach tariff prices acts MINTED, not marks met.** `Unit.read` returns the entire
   board minus the unit's own marks, with no filter and no chooser, so a price per mark
   read would make each unit's reach cost proportional to community size *by construction*:
   total cost `∝ N²`, **β = 2 written rather than found** — the exact defect Examination
   VIII convicted the West mapping of. It also gives `whom_to_ask` — built, fed by `credit`
   and `standing_with`, and recorded in its own docstring as **measured inert** — a reason
   to matter, because a unit that asks the wrong peer now pays for nothing. That is not
   installing typification; the organ has been idle for want of a price.

5. **The opening's sensitization prediction is restated as a finding-in-advance.** It read:
   *"as reserves fall, an unresolved doubt is income not earned, so urgency rises on its
   own."* Under rulings 1 and 2 there is nothing in a unit whose urgency *can* rise —
   doubting is unconditional and the reserve reaches no decision. Leaving it live would put
   an unfalsifiable null on the books. `P-D6` records the claim the rulings entail.

6. **The law, not the unit, is the replicator — and D-3 is habits as ink.** The author's
   objection to the assistant's genome proposal, recorded in §5.1. It corrected the
   assistant rather than the design.

7. **Price is determined, not set.** *"We can set cost or perhaps it will develop as a
   negotiation?"* The assistant had fixed two prices and declared a 50/50 split between
   them. Fixing the **supply** instead and letting the price clear against realised demand
   dissolves both. See §3.3. **Naming it exactly: this is not negotiation** — nobody
   bargains, nobody can refuse or counter, since that would need a chooser. It is
   scarcity-determined price, and calling it negotiated would claim more than the mechanism
   delivers.

8. **Population is found, not set.** *"Letting them adjust as they compete and find their
   solution is another."* This refuted an objection the assistant had made — that birth
   without heredity gives selection nothing to act on — which ruling 6 had already made
   false: birth is what gives the **law** a population to spread through. Without it the
   law-lineage measurement runs over a monotonically shrinking set and reads almost nothing.

9. **The schedule cannot develop, and the no is informative.** For attendance to find an
   optimum something must be able to *not attend* — a chooser, which ruling 1 excludes.
   What changes is that attending is no longer free: a unit that attends accumulates facts,
   raising its demand and its cost share. The pressure becomes real and measurable, and
   nothing can answer it. **This is the same diagnosis as `P-D6`, arriving by a second
   independent road**, and two arrivals at one finding are worth recording as such.

## 3 · Architecture

### 3.1 Where the reserve lives

**Not on `Unit`.** The world holds it, keyed by unit id. This is not a discipline anyone
has to remember — the architecture enforces ruling 2, because a unit cannot read what it
does not have. It also puts the reserve where THE_KYTOS §1.3 says an act's effect resides:
in the **resources**, outside the membrane, never in a private field beside the act.
`c_unit.py` is not modified.

### 3.2 The module

One new module, `src/d_world.py`.

| | |
|---|---|
| `Source` | frozen: `pool_per_round` (E1), `entry_price` (E0) |
| `Reserves` | `{unit_id: amount}` with `charge` / `credit` / `alive` |
| `Seats` | free/occupied apertures from `apertures_for`; hands a newborn the lowest free index, refuses when full |
| `PricedWorld` | owns all three; runs the round |

Deterministic and geometry-free, like every C-series module. Not protected.

### 3.3 The round

```
for each living unit:  unit.step(field, r)             # unchanged C-series code
                       unit.publish / ask / ...        # unchanged

demand_r  =  Σ_i ( |facts_i| + |laws_i| + acts_i )     # acts counted off MarkBoard
τ_r       =  E1 / demand_r                             # DETERMINED, not set
charge_i  =  τ_r · ( |facts_i| + |laws_i| + acts_i )
income_i  =  E1 · ( hits_i / Σ hits )                  # paid only when Σ hits > 0

birth:     reserve_i ≥ 2·E0  and a seat is free  →  split; parent and child take E0 each
death:     reserve_i ≤ 0                          →  leaves; its seat frees
```

Six consequences, each stated rather than left to be inferred.

- **A match is a `MembraneLedger` hit** — anticipated *and* arrived. Already computed; no
  new statistic, so the world scores matches and nothing else.
- **A miss carries no separate penalty.** It is already punished exactly once, by the
  charge paid on a law that earned nothing.
- **An act is a mark minted** — by `publish`, `ask`, `answer`, `challenge` or
  `corroborate`, without distinction. Charging the kinds differently would be a designer's
  claim about which speech is dear.
- **A held fact-round and a minted act each count 1** toward demand. This is a choice of
  units, and it is the *null* one — it asserts no difference between holding and speaking.
  It replaces the 50/50 split, which asserted no difference in a more contrived way (by
  equalising totals, which depends on how many facts and acts happen to occur). §8 records
  it.
- **The world is conservative except on hitless rounds.** τ takes back exactly what the
  pool gives, so total wealth is a fixed stock that birth redistributes and never creates.
  A round in which nobody hits charges `E1` and pays nothing, burning it from the stock.
  **So a community has a lifespan, and it is its own doing** — Bickhard's condition at
  community scale: acting wrongly shortens your life.
- **A newborn takes a free seat, not its parent's.** It inherits **nothing but the board** —
  no facts, no laws, no standing — and is socialized by marks it never made, which is
  Berger & Luckmann's secondary socialization and is already built. Giving it the parent's
  aperture would make it a twin, and twins at scale defeat premise 3's requirement that
  units meet the field differently.

### 3.4 One outside number, and it is measured

The opening proposed four. Ruling 7 dissolved two of them and the split between them;
ruling 8 turned population into a result. What remains:

| | | |
|---|---|---|
| `E1` | the source per round | **= 1, the numéraire.** Free — it fixes the unit of account and nothing else. |
| `E0` | the entry price | **measured** from arm 0 (§4). |
| `N₀` | initial population | **derived**: the smallest community in which every domain has three witnesses — the corroboration ruling's own requirement, computed by `units_for_witnesses`. |
| seats | the population ceiling | **the world's**, from `apertures_for` over the field. |
| the field | 8 domains | **the one remaining outside choice**, set by the author 2026-08-02 on a stated criterion: large enough to leave room for an equilibrium to develop (§8, §11). |

The birth threshold `2·E0` is not a chosen multiple: `E0` *is* the world's entry price, so
the rule reads *you may reproduce when you can pay a newcomer's entry and remain viable
yourself.*

## 4 · Calibrating E0

**Arm 0 — the charge computed and reported but never subtracted — is both the calibration
source and the control.** That is exactly today's system, and exactly the opening's own
sentence: *make the meter a subtraction instead of a reading.* It is also the only coherent
control now that price is determined, since `τ = E1/demand` has no zero.

Arm 0 runs at the reference configuration: **8 domains, PAIRS scheme, `N₀` as derived
above, eight seeds, 60 rounds, every unit inducing** (`induce=True`). Induction rather than
seeding, because `t*` is a fact about learning and a seeded unit never learns anything.

```
t*  =  the MEDIAN, over units and seeds, of the round at which a unit
       induces its first planted law
E0  =  the charge a median unit accrues over rounds 0 … t*
```

Median rather than first-or-mean at both steps, so one lucky unit does not set the world's
entry price. **Why `t*` and not a horizon.** An austere endowment — one round's living —
kills every unit before induction can happen and the run is empty; a horizon chosen by hand
is a free parameter wearing a law's clothes. Reading it off `t*` makes the claim sharp:
**a unit that learns slower than the recorded baseline dies before it learns.**

`E0` is computed once at the reference configuration and used unchanged everywhere.

## 5 · Staging

| | | why here |
|---|---|---|
| **D-0** | retire `Unit.peers` | **must precede pricing.** Once asking is priced, every `peers`-derived figure moves and the retirement's before/after becomes unreadable. `source_reliability` exists and is tested. Its **before/after reading stands as its own note**, not in this record (author's ruling, 2026-08-02) — a retirement's evidence belongs with the retirement. |
| **D-1** | the priced world, determined τ, endogenous population | the core build |
| **D-1b** | seed by DC+ · INS · IT+, with a price and a provenance | separate stage, one figure per cause. `notion_provenance` already supplies the held-until-affirmed shape. |
| **D-2** | the shared pool across **equal-sized** communities | pre-registered, not built — ruling 3. Equal size first (author's ruling, 2026-08-02): unequal communities sharpen the niche argument but confound it with a size difference, and the point of D-2 is that a bounded source is too small for all, not that a big community beats a small one. |
| **D-3** | **habits as ink** | §5.1 |

**The implementation plan that follows this spec covers D-0 and D-1 only.** The rest is
recorded so the sequencing argument survives the sitting; each earns its own spec.

### 5.1 D-3 — habits as ink

The sitting first proposed a genome: promote `corroboration_window`,
`corroborating_witnesses`, `replication_window`, `MIN_SUPPORT` and the induction criteria
to per-unit heritable values, add a birth rule and a mutation operator. **The author
refused it in one line — "yet, somehow, it developed without external programming."** The
refusal is the project's own standing rule applied one level up: *install the problem,
never the solution.* A designed genome installs the thing it was meant to explain, and the
mutation operator is a designed variation-generator.

The right question is what heredity emerged **from**: a substrate in which a pattern could
template itself, plus a world in which persisting was the only criterion.

**Our substrate already affords copying.** `publish` inscribes a law on the board; `adopt`
copies it into another unit's record. Variation is present too — different apertures and
`ObserverNoise` make units induce different laws from the same world. The missing term was
the third: **nothing died, so nothing was selected.** D-1 supplies it, and supplies it for
free. Once holders can die, **the law is a replicator**: laws that spread to units that
survive persist; laws whose holders starve go with them. The assistant had been looking for
the thing that reproduces while it was already reproducing.

**And the limit that names D-3.** Memetic copying varies *model content*. It cannot vary
*policy*, because `corroboration_window` and the induction criteria are not transmissible —
they are not ink, they are Python. Nature had no such split; at the molecular level the
code **is** the machinery. Ours is severed by the architecture.

So D-3 is: **a unit's dispositions written in the same medium as its model** — habits held
as EGs, published and adopted like any other mark, so a habit can spread, mutate in
transmission, and die with its holder. That installs nothing the substrate does not already
afford, and it is about as Peircean a proposition as this codebase could make: habit as
inscribed law. Its real cost is an interpreter over held rules, which makes it a series
rather than a stage. **The genome route stays on the record as rejected, with its reason** —
nobody chooses a smuggle deliberately; they reach for the one already written down.

## 6 · Arms and measurement

| | |
|---|---|
| **A0** | charge computed and reported, **not subtracted** — control and calibration source |
| **A1** | charge subtracted |
| **A2a** | subtracted, mark channel occluded entirely (cost *and* benefit removed) |
| **A2b** | subtracted, acts still minted and charged but peers receive nothing (cost held, sign removed) |

**Why the ablation needs two arms.** A single occlusion is confounded: a unit with the
channel off mints no marks and therefore **pays less**, so it could outlive its peers by
being mute rather than by being right. A2b is the honest ablation of the putative sign,
holding cost fixed. Reporting both keeps the confound visible.

**Configuration.** 8 domains, PAIRS, `N₀` derived, eight seeds, 60 rounds. **Community size
is not an arm** — it is a reported result (`P-D7`).

**There is no stagger.** The C-series "bounded attention" was a schedule imposed from
outside (ruling 2). Under ruling 1 nothing is declined, so every living unit attends every
round and pays for it — *fix the price, let the quantum fall out*, applied to attendance.
Together with the field change and the PAIRS scheme, this means **D-series figures do not
compare with C-series ones**, and no reading should try.

## 7 · Pre-registration

Committed before anything is built or run.

- **P-D1 · mortality is a consequence.** At subtracted charge, at least one reserve reaches
  zero within 60 rounds in a majority of the eight seeds, with no `die()`, TTL or lifespan
  anywhere in `src/`. **Fails** if nobody ever dies, or if everybody dies in round one.

- **P-D2 · laws have lineages, and survival tracks mediation.** Per law-content: how many
  units held it, by adoption or by induction, for how long, and whether its holders lived —
  computable from `MarkBoard` (attributed, dated) against the reserves. Planted true laws
  should show longer lineages and more holders than converses and unplanted regularities.
  **Fails** if lineage length is uncorrelated with a law's truth, which would say the world
  pays for something other than mediating well.

- **P-D3 · the ablation bites, measured in survival time.** A2b's communities die sooner
  than A1's — occlude the marks, prediction worsens, hitless rounds multiply, the stock
  burns faster. This is the standing falsifier *ablate the putative sign*, unrunnable until
  now because nothing survived or failed. **Fails** if occluding the sign changes lifespan
  none. A2a is reported beside it to expose the mute-and-cheaper confound.

- **P-D4 · typification becomes consequential.** Units whose asks go to higher-standing
  peers survive longer. The C-series measured this inert at four units — all 939 uptake
  decisions had exactly one peer standing behind them — so it needs a population where a
  choice exists, which the 8-domain field supplies. **Fails** if the preference stays inert
  once priced.

- **P-D5 · no exponent is measurable here, and that is said in advance.** Under a
  conservative world total cost is **pinned to `E1` every round regardless of `N`**, so
  total metabolic cost does not scale with community size at all and per-capita cost is
  `E1/N` by identity. **Anyone fitting a β to this world is fitting an identity.** The
  opening's condition-9 conjecture is likewise unreachable: the price of reaching *falls*
  as the community grows, the opposite of a cost of reaching that rises with extent. This
  is the second of the opening's §4 predictions restated as a finding-in-advance, and
  §1.1 carries it forward.

- **P-D6 · sensitization is absent, and structurally so.** No measure of urgency varies with
  reserve level, because none can (ruling 5), and the same gap blocks the schedule from
  finding an optimum (ruling 9). Recorded as a result of this sitting rather than of a run.
  **The negative check is weak** — nothing sensitization-like could appear in this build —
  and the prior earns its keep by saying so.

- **P-D7 · population finds a level, and the level is earned.** Community size settles
  rather than running to the seat cap or to extinction in every seed, and `N_eq / N₀` is
  **higher in A1 than in A2b** — a community that predicts better holds its number. Stated
  as a ratio because total wealth starts at `N₀·E0`, so the absolute equilibrium scales
  with `N₀` and only the ratio carries information. **Fails** if size runs to the ceiling
  (the cap is deciding, not the economy) or if the ratio is flat across arms.

## 8 · The cheat register — stated before building, not after

The opening's three, kept:

1. **The world scores matches and nothing else.** No credit for communicating,
   corroborating or typifying. If those pay, they pay only by producing better
   anticipations.
2. **"Success" is not our standard.** The field delivers, a match is a match, and we get no
   vote — THE_MEASURE_OF_KNOWLEDGE §1(d)'s trepanning problem one level up.
3. **Pre-register.** §7, before any build.

What this design adds — shorter than the previous draft's, because rulings 7 and 8 removed
three entries by removing the parameters they guarded:

4. **Unit parity in the demand sum** — a held fact-round and a minted act each count 1. A
   choice of units, and the null one, but still ours.
5. **`E0` inherits `t*` from the measured learner.** A faster induction routine would shrink
   it and kill more units. The entry price is set by an artefact of the baseline.
6. **The field's 8 domains are the one remaining outside choice**, set by the author on the
   criterion *at least enough room for an equilibrium to develop*. The seat ceiling (28)
   must sit well above where the economy settles, or the cap decides the population and
   `P-D7` is uninterpretable. **The escalation rule is stated in advance**: if a measured
   equilibrium reaches 80% of the ceiling in any arm, the field grows and every figure is
   re-measured — a result taken at a binding ceiling is not reported as an equilibrium.
   §11.1 records the standing search for a version of this that needs no number at all.

## 9 · Refused, and why

Recorded so the next reader does not rediscover the hole and fill it.

- **A chooser** — where a designer writes the answer and calls it emergent (ruling 1).
- **A sense organ for the reserve** — reaches no decision without a chooser (ruling 2).
- **An attempt-ordering rule** — the order *is* the priority, and nobody argued for it.
- **A separate penalty for a miss** — already punished once.
- **A price per mark read** — installs `β = 2` (ruling 4).
- **Two fixed prices and a split between them** — dissolved by ruling 7.
- **A weight between holding and speaking** — reintroduces as a knob the ratio parity
  dissolved, and a knob invites a sweep.
- **A genome, a birth threshold chosen by hand, a mutation operator** — installs the
  explanandum (§5.1). The threshold is derived from `E0` instead.
- **Fixing community size** — ruling 8.

Deferred rather than refused, and named so the hole stays visible: the shared pool (D-2) ·
habits as ink (D-3), with its interpreter over held rules · the credential build
(Examination VII stage 4 (c)), which still blocks weighted witnesses.

## 10 · Testing

Beyond ordinary coverage of `Source` / `Reserves` / `Seats` / `PricedWorld`:

- **In arm 0 the wrapper is inert.** A run with the charge computed but not subtracted is
  byte-identical to the same community run without `PricedWorld` at all. This is a claim
  about the wrapper changing nothing, **not** a claim to reproduce published C-series
  figures, which were measured under a different field, a different aperture scheme and an
  imposed stagger (§6).
- **A determinism canary** — two runs agree, as `test_c_stage_gates.py` already keeps.
- **Conservation** — in any round with at least one hit, total charge equals total income
  to the last unit of account. The one place a rounding bug would silently create or
  destroy wealth.
- **Three adversarial checks.** No `die()`, TTL or lifespan anywhere in `src/` — the
  mortality prior is worthless if something installs it. `Unit` carries no reserve
  attribute, so a future chooser cannot read one by accident. And **birth refuses when no
  seat is free** rather than seating a twin.

## 11 · Rulings on the open items

All three ruled by the author, 2026-08-02, and folded into the sections above.

- **D-2 starts with equal-sized communities** (§5). Unequal ones sharpen the niche argument
  but confound it with a size difference; D-2's claim is that a bounded source is too small
  for all, not that a big community beats a small one.
- **D-0's before/after reading stands as its own note** (§5), not in this record. A
  retirement's evidence belongs with the retirement.
- **The field's domain count is set for now**, on the stated criterion *at least enough room
  for an equilibrium to develop* (§3.4, §8 item 6), with the escalation rule pre-registered
  — and the search for an emergent version continues.

### 11.1 · The standing search: a population ceiling that needs no number

The field-size number exists **only** to keep the seat ceiling clear of the equilibrium.
The ceiling itself exists only because apertures are drawn from a finite combinatorial set
and `apertures_for` refuses to seat two units on the same slice. So the number would
disappear entirely if a newborn could take an **occupied** aperture — the population would
then be bounded by the economy alone, which is what ruling 8 wanted.

**There is already textual support for allowing it.** `apertures_for`'s own docstring argues
that the `twin_of` control does not violate premise 3: the premise "requires units to meet
the field through different apertures, or they converge on near-identical models" — *a claim
about CONTENT* — while a twin "holds content and position fixed on purpose, in order to ask a
different question… Different axis, so the premise is untouched."

**The candidate reading, which the author has not ruled on:** premise 3 is a claim about
*initialization*, not about lifetime. A unit **born** onto an occupied aperture is not the
same case as a unit **seeded** onto one — it arrives at a different round, into a board
already carrying marks its aperture-mate helped write, and adopts different content in
consequence. Its history diverges even where its aperture does not.

**And it is checkable rather than hopeful.** Measure model divergence between same-aperture
pairs against different-aperture pairs in a D-1 run that permits twin births. If
same-aperture pairs diverge comparably, premise 3's refusal is over-strict for born units,
the seat cap can go, and the last outside number goes with it. If they converge, the number
stays and the reason for it is now measured rather than assumed.

Recorded here rather than built, so the search has a shape instead of remaining an
intention.
