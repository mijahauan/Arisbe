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
    # A cross-domain law: ("a_head", "b_head").
    cross = (spec.domains[0].law[1], spec.domains[1].law[1])
    return spec, field, ap, converse, cross


def test_stage_1_gate_a_unit_learns_a_planted_law_and_its_score_rises():
    """Stage 1 gate: induction earns its keep.

    The learner must (a) induce a law the field actually planted and (b)
    outscore a unit that holds a WRONG law and bets on it — not merely
    outscore total abstention, which any nonzero accuracy achieves.

    The betting rival here is the cross-domain arm `a_head -> b_head`, which
    places 264 real bets over these rounds and wins none. See
    `test_the_converse_law_arm_places_no_bets_at_all` for why the converse
    law, the other candidate rival, cannot serve — a finding, not a choice.
    """
    spec, field, ap, _converse, cross = _arms()
    learner = Unit("u0", ap)
    fixed = Unit("u1", ap)
    misled = Unit("u2", ap, laws={cross})
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
    # And the learner beats it, and beats abstention.
    assert learner.ledger.accuracy > misled.ledger.accuracy
    assert learner.ledger.accuracy > fixed.ledger.accuracy


def test_the_converse_law_arm_places_no_bets_at_all():
    """A measured finding, pinned so it cannot silently change.

    A unit seeded with the converse of a planted law (`a_head -> a_local`)
    never places a single bet, so it is indistinguishable from a unit holding
    no laws and cannot serve as a falsifier for the gate above.

    The reason is structural, not statistical: `Unit.anticipate` drops any
    candidate already in `facts`, and the field delivers `a_head(y)` at round
    r only because `a_local(y)` was delivered at r-1 and absorbed then. The
    converse law's head is therefore ALWAYS already held, so it never yields
    a prediction. Verified at seeds 7 / 20260728 / 99 / 12345 and out to 200
    rounds: zero bets in every case.
    """
    _spec, field, ap, converse, _cross = _arms()
    conv_arm = Unit("u3", ap, laws={converse})
    lawless = Unit("u4", ap)
    for r in range(ROUNDS):
        conv_arm.step(field, r, induce=False)
        lawless.step(field, r, induce=False)

    assert conv_arm.ledger.hits + conv_arm.ledger.misses == 0
    assert conv_arm.ledger.accuracy == lawless.ledger.accuracy == 0.0


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
