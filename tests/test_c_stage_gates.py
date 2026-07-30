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
    # Measured 7–15 hits against 239–516 misses across 14 seeds.
    shared_head = (spec.domains[0].law[1], "shared")
    return spec, field, ap, converse, shared_head


def test_stage_1_gate_a_unit_learns_a_planted_law_and_its_score_rises():
    """Stage 1 gate: induction earns its keep.

    The learner must (a) induce a law the field actually planted and (b)
    outscore a unit that holds a WRONG law and bets on it — not merely
    outscore total abstention.

    THE STATISTIC IS `net_score` (hits − misses), not `accuracy`. Two reasons.
    A ratio over few bets is unstable — one lucky hit reads as a perfect score,
    which is what made an earlier version of this gate flip across seeds. And
    the `fixed` arm never bets, so its `accuracy` is `None` (an abstainer has no
    accuracy rather than a zero one); comparing a ratio against it would raise.
    `net_score` puts a better and an abstainer on one honest scale: abstention
    is 0, betting and winning is positive, betting and losing is negative.

    MEASURED at this seed (20260728), 60 rounds: learner 55 hits / 0 misses,
    net +55; rival 11 hits / 241 misses, net −230; `fixed` 0 bets, net 0.
    The gate's margin is therefore +285 over the rival and +55 over abstention.

    SATURATION IS GONE. This aperture's atom universe is 230 atoms (five
    relations over alpha's and beta's forty individuals, which overlap in the
    ten-strong shared core). The learner holds 179 of them after 60 rounds and
    is still betting at the end: 39 of the 60 rounds carry a bet, the first at
    round 4 and the last at round 59, with 9 bet-rounds at or after round 40.
    Anticipation stays live for the whole run, so a longer run adds evidence
    rather than silence — the earlier field (30 atoms, all held by round 18,
    7 bets total) could not say that.

    SEED FRAGILITY IS GONE, and here are the seeds: over 1, 2, 3, 4, 5, 7, 42,
    99, 555, 808, 2026, 12345, 20260728 and 31337, the learner outranks the
    rival on `net_score` at 14 of 14 — and on `accuracy` at 14 of 14 as well.
    The two seeds that used to break the ordering (99 and 808) no longer do.

    THE RIVAL CAN WIN, AND SOMETIMES DOES — that is what makes this a real
    falsifier rather than a walkover. `shared` draws from the domain's own
    individuals, which include the ten-strong core, so `shared(x)` for an x
    already carrying `a_head` genuinely arrives now and then: 7–15 hits per
    run across the 14 seeds (11 here), against 239–516 misses. It loses on
    volume, not on impossibility. A sweep of all twenty body→head pairs over
    this aperture's five relations at seed 20260728 makes the point: the two
    PLANTED laws score 32/0 and 29/0, the two converses never bet (their head
    is always already held), and every one of the remaining sixteen bets AND
    hits — from 2 hits (`a_local -> b_local`, reaching across domains through
    the core) to 18 (`shared -> a_local`) — while all sixteen finish deeply
    negative. Accidental regularities are possible in this field; none of them
    pays.

    WHAT THE GATE STILL CANNOT SHOW: the learner takes 0 misses at all 14
    seeds. That is now a property of the induction criterion, not of the field.
    `Unit.induce` admits a law only when at most ONE individual carries the
    body without the head, and every wrong law leaves fifteen-plus such
    individuals outstanding, so the learner proposes exactly the two planted
    laws and their two inert converses and never bets on anything false.
    Loosening `max_pending` would let it err; whether it should is a stage-2
    question about the induction rule, deliberately not answered here.
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


def test_the_converse_law_arm_places_no_bets_at_all():
    """A measured finding, pinned so it cannot silently change.

    A unit seeded with the converse of a planted law (`a_head -> a_local`)
    never places a single bet, so it is indistinguishable from a unit holding
    no laws and cannot serve as a falsifier for the gate above.

    The reason is structural, not statistical: `Unit.anticipate` drops any
    candidate already in `facts`, and the field delivers `a_head(y)` at round
    r only because `a_local(y)` was delivered at r-1 and absorbed then. The
    converse law's head is therefore ALWAYS already held, so it never yields
    a prediction. Re-verified on the shared-core field at seeds 7 / 99 / 808 /
    12345 / 20260728 and out to 200 rounds: zero bets in every case. It is the
    ONLY law shape in this field that cannot bet — every other wrong law now
    both bets and sometimes hits.

    Both arms therefore have NO accuracy — `None`, not 0.0. A unit that placed
    no bet has no ratio to report, and fabricating one for it would let an
    abstainer be ranked as if it had played and lost. `net_score` is 0 for
    both, which is the honest reading: nothing ventured either way.
    """
    _spec, field, ap, converse, _shared_head = _arms()
    conv_arm = Unit("u3", ap, laws={converse})
    lawless = Unit("u4", ap)
    for r in range(ROUNDS):
        conv_arm.step(field, r, induce=False)
        lawless.step(field, r, induce=False)

    assert conv_arm.ledger.hits + conv_arm.ledger.misses == 0
    assert conv_arm.ledger.accuracy is None
    assert lawless.ledger.accuracy is None
    assert conv_arm.ledger.net_score == lawless.ledger.net_score == 0


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
