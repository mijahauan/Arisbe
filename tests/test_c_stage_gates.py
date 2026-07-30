"""The two gates the spec sets for stages 1 and 2, asserted in one place.

This file deliberately restates gates that `tests/test_c_unit.py` and
`tests/test_c_use.py` also cover. The duplication is intentional (author
ruling): a reviewer should be able to check both stage gates here without
reading five test modules. Do not refactor it into imports from those files.
"""

from c_field import Field, default_spec, apertures_for
from c_unit import Unit
from c_use import WorkUsageLedger
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi

ROUNDS = 60
SEED = 20260728


def _arms():
    """The field, the aperture, and the two wrong laws the gate compares
    against. Built once per test so no ledger is shared between tests."""
    spec = default_spec(seed=SEED)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    # The converse of alpha's own law: ("a_head", "a_local").
    converse = (spec.domains[0].law[1], spec.domains[0].law[0])
    # A wrong law that bets heavily and loses more than it wins:
    # ("a_head", "shared"). It has a real, nonzero ceiling — `shared` draws
    # from the domain's own individuals, which include the shared core, so
    # `shared(x)` for an x already carrying `a_head` does sometimes arrive.
    # Measured 6–15 hits against 241–565 misses across 14 seeds (under noise).
    shared_head = (spec.domains[0].law[1], "shared")
    return spec, field, ap, converse, shared_head


def test_stage_1_gate_a_unit_learns_a_planted_law_and_its_score_rises():
    """Stage 1 gate: induction earns its keep.

    The learner must (a) induce a law the field actually planted and (b)
    outscore a unit that holds a WRONG law and bets on it — and (c) outscore
    total abstention.

    THIS GATE NOW PASSES ON THE MERITS, at all fourteen seeds. It carried
    `xfail(strict=True)` for one reason: `MembraneLedger.score` charged a miss
    for each anticipated atom EVERY round, so a consequent the field withheld
    became a standing bet re-charged for the rest of the run, misses grew with
    the square of the run length while hits grew linearly, and clause (c) failed
    at 9 of 14 seeds. A forecast now resolves EXACTLY ONCE, at the round it is
    due. No assertion here was weakened.

    THE STATISTIC IS `net_score` (hits − misses), not `accuracy`. Two reasons.
    A ratio over few bets is unstable — one lucky hit reads as a perfect score,
    which is what made an earlier version of this gate flip across seeds. And
    the `fixed` arm never bets, so its `accuracy` is `None` (an abstainer has no
    accuracy rather than a zero one); comparing a ratio against it would raise.
    `net_score` puts a better and an abstainer on one honest scale: abstention
    is 0, betting and winning is positive, betting and losing is negative.

    RE-MEASURED at this seed (20260728), 60 rounds, under noise, with a forecast
    resolving once: learner 35 hits / 4 misses, net +31, accuracy 0.8974, holding
    exactly the two planted laws; rival 2 hits / 12 misses, net −10; `fixed` 0
    bets, net 0. The margin over the rival is +41, over abstention +31. The
    learner's 4 misses are 4 DISTINCT atoms — zero re-charges — and its 31 late
    arrivals are the price of the discipline (a missed atom that turned up after
    its due round takes no credit for arriving).

    SATURATION IS STILL GONE, though the shape of the answer changed. This
    aperture's atom universe is 230 atoms (five relations over alpha's and
    beta's forty individuals, which overlap in the ten-strong shared core); the
    learner holds 181 of them after 60 rounds. It places 39 stakes across 31
    bet-rounds, the first at round 10 and the last at round 58, with 7
    bet-rounds at or after round 40 — anticipation stays live to the end of the
    run. Because each proposition is staked once, the stake count is bounded by
    the atom universe rather than by the run length, so a much longer run adds
    evidence at a falling rate rather than at a rising one. (Measured: a single
    planted law at seed 3 finishes +13 at 20 rounds, +20 at 60, +23 at 120 and
    +23 at 240 — it plateaus, where under the old contract it fell without
    bound. A stage-3 gate reading `net_score` should therefore compare arms at
    EQUAL run length, which it does.)

    SEED ROBUSTNESS, RE-MEASURED. Over 1, 2, 3, 4, 5, 7, 42, 99, 555, 808, 2026,
    12345, 20260728 and 31337 the learner outranks the RIVAL at 14 of 14 and
    ABSTENTION at 14 of 14 (net +4 at the worst seed, 2, and +32 at the best,
    808 and 2026). Both orderings are now robust; previously only the first was.

    THE RIVAL CAN WIN, AND SOMETIMES DOES — that is what makes this a real
    falsifier rather than a walkover. `shared` draws from the domain's own
    individuals, which include the ten-strong core, so `shared(x)` for an x
    already carrying `a_head` genuinely arrives now and then (2 hits here
    against 12 misses). It loses on volume, not on impossibility. A sweep of all
    twenty body→head pairs over this aperture's five relations at seed 20260728
    now makes the sharpest possible version of the point: the two PLANTED laws
    are the ONLY TWO that pay (`a_local -> a_head` 28h/2m = +26 and
    `b_local -> b_head` 26h/2m = +24), and all eighteen others finish negative,
    from −2 (the two converses, which bet and take zero hits) down to −46. Under
    the old contract the second planted law itself finished at −16; a law the
    field really carries can no longer lose money, which is what this fix was
    for.

    WHAT THE GATE SHOWS. The learner's induction is exact — `Unit.induce` takes
    direction from temporal precedence as well as support and a proportional
    pending tolerance, so at all 14 seeds it proposes ONLY planted laws, no
    converse and nothing unplanted (pinned in `tests/test_c_unit.py`:
    `test_the_learner_induces_only_planted_laws_across_many_seeds`) — AND that
    holding a true law now beats both holding a false one and holding none.
    """
    spec, field, ap, _converse, shared_head = _arms()
    learner = Unit("u0", ap)
    fixed = Unit("u1", ap)
    misled = Unit("u2", ap, laws={shared_head})
    for r in range(ROUNDS):
        learner.step(field, r, induce=True)
        fixed.step(field, r, induce=False)
        misled.step(field, r, induce=False)

    # (a) A law the field really planted was found.
    assert learner.laws & {d.law for d in spec.domains}
    # (b) The learner bets and wins some of them.
    assert learner.ledger.hits > 0
    # The rival genuinely bets — the comparison has a losing side that plays.
    assert misled.ledger.hits + misled.ledger.misses > 0
    # It can also WIN some of them; that the ceiling is nonzero is a property
    # of the field, pinned in tests/test_c_field.py rather than restated here.
    # And the learner beats it, and beats abstention — on `net_score`, the
    # statistic that is stable at low bet volumes and that an abstainer can
    # share a scale with (its `accuracy` is None, not 0.0).
    assert learner.ledger.net_score > misled.ledger.net_score
    assert learner.ledger.net_score > fixed.ledger.net_score
    assert fixed.ledger.accuracy is None      # it never bet; no ratio exists


def test_a_true_law_held_alone_makes_money_at_every_seed():
    """THE DECISIVE TEST OF THE SCORING CONTRACT, and the one the whole of stage
    3 rests on: a law the field genuinely carries must not lose money.

    It used not to be so. Because `MembraneLedger.score` charged an anticipated
    atom every round rather than once, a single withheld consequent became a
    perpetual miss, and the planted `b_local -> b_head` held ALONE over 60
    rounds finished 28 hits / 44 misses = −16. That is a scoring contract
    measuring run length, not knowledge, and every statistic built on it — K1
    track record, durability, any live-versus-mute comparison — inherited the
    error.

    RE-MEASURED with a forecast resolving once, at the round it is due: both
    planted laws finish POSITIVE at all fourteen seeds, 28 of 28 arms, with net
    scores from +17 to +29 (median +24). At seed 20260728: `a_local -> a_head`
    28h/2m = +26, `b_local -> b_head` 26h/2m = +24.

    This is asserted per-arm rather than in aggregate, so a single losing seed
    fails the gate and names itself."""
    seeds = [1, 2, 3, 4, 5, 7, 42, 99, 555, 808, 2026, 12345, 20260728, 31337]
    for seed in seeds:
        spec = default_spec(seed=seed)
        field = Field(spec)
        ap = apertures_for(spec, n_units=4)[0]
        # Only the two domains this aperture actually meets can be tested: a
        # law over relations the unit never sees would abstain, not earn.
        for domain in spec.domains[:2]:
            u = Unit("u0", ap, laws={domain.law})
            for r in range(ROUNDS):
                u.step(field, r)
            led = u.ledger
            assert led.hits + led.misses > 0, (
                f"seed {seed} {domain.law}: never bet, so nothing was tested")
            assert led.net_score > 0, (
                f"seed {seed}: the planted law {domain.law} held alone LOSES "
                f"money — {led.hits}h/{led.misses}m net {led.net_score}")
            # And it loses no bet twice: one charge per distinct atom.
            assert led.misses == len({e.fact for e in led.entries
                                     if e.result == "miss"})
            assert led.restaked == 0


def test_the_converse_law_arm_now_bets_and_loses():
    """A measured finding, RE-MEASURED after the field became fallible.

    WHAT THIS GATE USED TO SAY, and why it no longer says it. On the noiseless
    field a unit seeded with the converse of a planted law (`a_head -> a_local`)
    never placed a single bet, so it was indistinguishable from an abstainer and
    could not serve as a falsifier. The reason was structural: `anticipate` drops
    any candidate already in `facts`, and the field delivered `a_head(y)` at
    round r ONLY because `a_local(y)` had been delivered at r-1 and absorbed
    then, so the converse's head was always already held.

    NOISE REMOVED THAT PREMISE ON PURPOSE. A spurious head atom arrives with no
    antecedent to license it, so `a_head(z)` can now reach an individual for
    which `a_local(z)` was never delivered — and the converse law finally has
    something to predict.

    RE-MEASURED with a forecast resolving once, at the round it is due: at this
    seed (20260728), 60 rounds, 0 hits / 3 misses, net −3. Across the fourteen
    seeds 1, 2, 3, 4, 5, 7, 42, 99, 555, 808, 2026, 12345, 20260728, 31337 it
    still bets at ALL FOURTEEN and still finishes negative every time, now with
    ZERO hits and 1–5 misses. The hits it used to take (0–3) were an artifact of
    re-charging: a standing bet held open for the rest of the run eventually
    coincided with a delivery. Bet once, due next round, and the converse is
    revealed as predicting nothing at all — a stronger reading of the same
    finding, on a smaller absolute scale.

    WHY THIS MATTERS MORE THAN THE OLD READING. The converse arm betting is
    exactly what exposed the induction criterion's defect: support and
    counterexample tolerance are SYMMETRIC between a law and its converse, so
    the old criterion admitted both, and under noise the converse finally cost
    something. `Unit.induce` now takes direction from temporal precedence and
    refuses the converse outright (`tests/test_c_unit.py`:
    `test_induction_admits_a_law_and_refuses_its_converse`). This gate pins the
    other half: the converse is a law worth refusing, because held it loses.

    The lawless arm is still the honest zero — no bet, so NO accuracy (`None`,
    not 0.0) and net 0. Fabricating a ratio for an abstainer would let it be
    ranked as if it had played and lost."""
    _spec, field, ap, converse, _shared_head = _arms()
    conv_arm = Unit("u3", ap, laws={converse})
    lawless = Unit("u4", ap)
    for r in range(ROUNDS):
        conv_arm.step(field, r, induce=False)
        lawless.step(field, r, induce=False)

    # It bets now — the noise gave it something to be wrong about.
    assert conv_arm.ledger.hits + conv_arm.ledger.misses > 0
    # And it loses: a converse held is a converse that costs.
    assert conv_arm.ledger.misses > conv_arm.ledger.hits
    assert conv_arm.ledger.net_score < 0
    # The abstainer is unchanged, and remains the honest zero.
    assert lawless.ledger.hits + lawless.ledger.misses == 0
    assert lawless.ledger.accuracy is None
    assert lawless.ledger.net_score == 0
    assert conv_arm.ledger.net_score < lawless.ledger.net_score


def test_stage_2_gate_support_is_recoverable_and_changes_what_survives():
    """Stage 2 gate: a derived fact's support is recoverable, and scoring use
    as participation in work retains different atoms than scoring it as
    re-delivery."""
    prov = {}
    materialize_egi(parse_egif('~[ (p1 *x) ~[ (q1 x) ] ] (p1 "a")'),
                    provenance=prov)
    assert prov, "no support recorded"

    p_a = ("p1", (("c", "a"),))
    noise = ("noise", (("c", "z"),))
    led = WorkUsageLedger(ttl=3)
    led.touch_arrival({p_a, noise}, 0)
    for r in range(1, 10):
        led.touch_work(prov, r)
        led.touch_arrival({noise}, r)

    work_stale = set(led.stale(9, mode="work"))
    arrival_stale = set(led.stale(9, mode="arrival"))
    assert work_stale != arrival_stale
    # Named concretely: the atom that did work every round but arrived once
    # survives the work clock and is stale on the arrival clock, and the
    # atom that arrived every round and did nothing is the mirror image.
    assert p_a in arrival_stale and p_a not in work_stale
    assert noise in work_stale and noise not in arrival_stale


def test_determinism_canary_two_runs_agree():
    """Two identical runs must agree exactly — the field is a pure function
    of (seed, domain, round), so nothing here may depend on iteration or
    hash order."""
    def run():
        spec = default_spec(seed=SEED)
        field = Field(spec)
        ap = apertures_for(spec, n_units=4)[0]
        u = Unit("u0", ap)
        for r in range(30):
            u.step(field, r, induce=True)
        return sorted(u.laws), u.ledger.hits, u.ledger.misses

    assert run() == run()
