# Examination VII repairs — the author ruled YES on speaker-variance (2026-07-30)

**The ruling:** stage 4 gives the field speaker-variance, and the repairs the
examination identified are authorized.

**Governing constraint on every code task: additive, defaults bit-identical.**
Every existing C-series figure was measured under the current behaviour and the
examination cites those figures throughout. A repair that moves them silently
would invalidate its own evidence. Each task ships with a back-compat assertion,
and the full C suite (178 tests) must stay green with no gate figure moved.

## Code

- [x] **1 · Field speaker-variance** (`src/c_field.py`) — THE RULING.
      Per-observer noise, so one unit's *observation* of a domain can differ
      from another's. Two rates, doing different work: `withhold` makes a unit
      quieter (sees less); `spurious` makes it an **unreliable speaker** — it
      perceives atoms the field never delivered and publishes them in good
      faith. That second one is the cry-wolf structure §11.2(c) names: "his
      failure is not lying — his cry became statistically independent of the
      wolf."
      - `ObserverNoise(withhold, spurious)`; `FieldSpec.observers` a tuple of
        pairs (FieldSpec is frozen and never hashed; a tuple keeps it honest).
      - `Field.deliver(domain, round, observer=None)` — `None` reproduces today
        byte for byte.
      - Own RNG, keyed `f"{seed}:obs:{observer}:{domain}:{round}"`, so it cannot
        disturb either existing stream (the discipline the field already uses to
        keep the antecedent stream clean).
      - Gate: `deliver(d, r) == deliver(d, r, observer="u0")` when u0 has no
        entry; a spurious observer perceives atoms `deliver(d, r)` lacks; two
        observers with equal rates but different ids diverge.

- [x] **2 · The twin control** (`src/c_field.py`) — needs no premise-3 exemption
      (ruling 2: premise 3 governs *content* divergence; the twin probes
      *policy* divergence at fixed content).
      - `apertures_for(..., twin_of="u0")` appends one unit carrying u0's
        aperture. The refusal stays the default; twinning is opt-in and named.
      - Docstring states the caller's obligation: a twin means something only at
        **matching attendance parity**, so it must sit at an index of that parity.
      - Gate (this IS the control): twins at matching parity with no observer
        noise end a run **bit-identical** — the null P-H3 clause 1 currently
        lacks. With observer noise they diverge, so policy divergence becomes
        readable against a real zero.

- [x] **3 · `Unit.peers` stores `(proved, failed)`** (`src/c_unit.py`) —
      amendable (a); Examination V's V.2 remedy, second half. Today `credit`
      writes `proved − failed` as one irreversible integer, so a peer
      10-proved/10-failed reads identical to one never heard from (5 of 96
      records sit on that collision). Keep both; let `whom_to_ask` derive.
      - ~8 test sites read `peers` and move with it.
      - Gate: the collision case distinguishes; `whom_to_ask` returns what it
        returns today at every seed.

## Docs

- [x] **4 · §11.2(b) prose** (spec) — VII.8. "raises how often … a unit queries"
      describes enlarging a budget; `AttentionEconomy.choose(k, …)` takes the
      slot count from the caller and can only reorder. Amend prose to mechanism
      and record the rule: **doubt may reorder a fixed budget, never enlarge
      it** — with the reason (a unit whose per-round cost is free is not a
      terminal unit, so no quantum and no exponent).
- [x] **5 · §11.4 P-H1/P-H2 rewritten** (spec) — VII.9. P-H1 counts **usable**
      distinct fillers (new to the asker AND scoreable by it) with the
      same-parity pair as its null; P-H2 names its two random variables, drops
      the false "at or near zero" baseline, and reports bits beside
      true-laws-held.
- [x] **6 · Two guard clauses** (`docs/THE_MEASURE_OF_KNOWLEDGE.md`) — guard #3's
      missing clause (forbids *aggregating* the index, not comparing within it)
      **explicitly licensing the credential**, plus a sign-freeness guard.
- [x] **7 · Record rulings 1 and 2 in the spec** (§11), so the design carries
      them and not only the examination record.

## Explicitly NOT in scope — still the author's

Retire `net_score` · the `corroboration_window` default · the witness rule ·
the West doc sweep and his grade rulings · and the **credential mechanism
itself**, which is stage-4 build work deserving its own plan rather than being
smuggled in as a repair.

## Review

All seven done; C suite green with no gate figure moved.

**What shipped.** `ObserverNoise` + `FieldSpec.observers` + `Field.deliver(...,
observer=)` — the ruling. Two rates because they make different speakers:
`withhold` produces a quieter unit whose testimony stays sound, `spurious`
produces an unreliable one that perceives what was never delivered and publishes
it in good faith. That second is the cry-wolf structure, and nothing models
deceit — a unit is unreliable exactly insofar as its perceptions are
uncorrelated with the world. `apertures_for(twin_of=)` for the control.
`Unit.peers` keeps `(proved, failed)` with `standing_with` deriving the
difference at read time.

**Back-compat held three ways**, since the examination cites the old figures
throughout: observer noise runs on its own RNG keyed
`f"{seed}:obs:{observer}:{domain}:{round}"`, so naming an observer changes
nothing for anyone else; an id with no entry skips the layer entirely; and
`twin_of=None` reproduces every aperture list exactly. Each is pinned by a test
rather than asserted.

**A design point worth keeping.** Observer noise is keyed on the observer *id*,
so two units carrying identical `ObserverNoise` still meet different things.
Equal rates are equal dispositions, not equal experience — otherwise
"unreliable" would be a property of the spec rather than of a speaker, and
nothing watching could tell two equally-noisy units apart.

**The twin control is now a real instrument**, not just a permission: twins at
matching parity with no observer noise are bit-identical (the null P-H3 clause 1
lacked), and diverge once the field names a speaker (so the null has a live
range rather than only a floor).

**The catch that mattered.** `Field.at(aperture, round_idx)` — the path a unit
actually reads by — called `deliver` without an observer, so observer noise
reached nothing. The whole ruling would have been reachable only from tests: a
mechanism built and never connected, which is precisely the defect Examination V
named as its V.5, "plumbing on unplumbed plumbing, recording what nothing
consumes." The `Aperture` was carrying `unit_id` the whole way and `at` dropped
it. Found by asking who reads the changed surface rather than by a failing test,
then pinned with one (`test_observer_noise_reaches_a_unit_through_its_aperture`)
that fails with `assert 0 > 20` against the unfixed path.

**Caught in passing:** CLAUDE.md said the measure carries "three guards"; it
carries four now.
