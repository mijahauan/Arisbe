# tests/test_c_unit.py
from c_field import Field, default_spec, apertures_for
from c_unit import Unit


def _setup(seed=7):
    spec = default_spec(seed=seed)
    return spec, Field(spec), apertures_for(spec, n_units=4)[0]


def test_lawless_unit_anticipates_nothing():
    _spec, field, ap = _setup()
    u = Unit("u0", ap)
    u.absorb(field, 0)
    assert u.anticipate() == set()


def test_unit_holding_the_law_anticipates_the_consequent():
    spec, field, ap = _setup()
    u = Unit("u0", ap)
    first = spec.domains[0]
    u.laws.add(first.law)
    u.absorb(field, 0)          # now holds round 0's antecedents
    anticipated = u.anticipate()
    assert anticipated, "a held law should license some anticipation"
    head = first.law[1]
    assert all(rel == head for rel, _ in anticipated)


def test_held_law_beats_a_wrong_law_over_a_run():
    """Three arms over the same rounds. The lawless arm abstains entirely, so
    comparing against it only exercises the ledger's zero-case; the misled arm
    holds a law the field does not carry, fires on atoms that really arrive,
    and so places genuine bets that genuinely lose. That is the falsifiable
    comparison: a law that does not hold should score badly, not merely
    abstain."""
    spec, field, ap = _setup()
    lawful, lawless, misled = Unit("u0", ap), Unit("u1", ap), Unit("u2", ap)
    lawful.laws.add(spec.domains[0].law)
    # body = first domain's head relation (which really arrives), head = the
    # SECOND domain's head relation (which never arrives for those individuals)
    misled.laws.add((spec.domains[0].law[1], spec.domains[1].law[1]))
    for r in range(20):
        lawful.step(field, r)
        lawless.step(field, r)
        misled.step(field, r)
    assert lawful.ledger.hits > 0
    assert lawless.ledger.hits == 0
    assert lawless.ledger.misses == 0        # it places no bet at all
    assert misled.ledger.misses > 0          # the wrong law bets and loses
    assert lawful.ledger.accuracy > misled.ledger.accuracy


def _unary(rel, names):
    return {(rel, (("c", n),)) for n in names}


def test_induction_needs_enough_support():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p", ["x0", "x1", "x2"]))
    u.facts.update(_unary("q", ["x0", "x1", "x2"]))
    assert ("p", "q") in u.induce(min_support=3)

    v = Unit("u1", ap)
    v.facts.update(_unary("p", ["y0", "y1"]))
    v.facts.update(_unary("q", ["y0", "y1"]))
    assert ("p", "q") not in v.induce(min_support=3)


def test_one_pending_antecedent_is_tolerated_two_are_not():
    """The lag leaves exactly one antecedent awaiting its consequent."""
    _spec, _field, ap = _setup()
    lagging = Unit("u0", ap)
    lagging.facts.update(_unary("p", ["x0", "x1", "x2", "x3"]))
    lagging.facts.update(_unary("q", ["x0", "x1", "x2"]))       # x3 pending
    assert ("p", "q") in lagging.induce(min_support=3, max_pending=1)

    refuted = Unit("u1", ap)
    refuted.facts.update(_unary("p", ["y0", "y1", "y2", "y3", "y4"]))
    refuted.facts.update(_unary("q", ["y0", "y1", "y2"]))       # y3, y4 refute
    assert ("p", "q") not in refuted.induce(min_support=3, max_pending=1)


def test_inducing_unit_learns_the_planted_law_and_its_score_rises():
    """The Stage 1 gate: a unit that may induce ends up holding a law the
    regime actually planted, and outperforms both a unit that may not induce
    and a unit seeded with a law the field does not carry.

    Three arms. The `fixed` arm never induces, so it never bets and its
    accuracy is 0.0 by construction — comparing against it only shows the
    learner beats total abstention. The `misled` arm holds a wrong law, fires
    on atoms that really arrive, and so places genuine bets that genuinely
    lose. That is the falsifiable comparison: were the induced laws worse than
    useless, the learner would bet and never win, and would NOT outscore an
    arm that does the same."""
    spec, field, ap = _setup()
    learner, fixed, misled = Unit("u0", ap), Unit("u1", ap), Unit("u2", ap)
    # body = first domain's head relation (which really arrives), head = the
    # SECOND domain's head relation (which never arrives for those individuals)
    misled.laws.add((spec.domains[0].law[1], spec.domains[1].law[1]))
    for r in range(60):
        learner.step(field, r, induce=True)
        fixed.step(field, r, induce=False)
        misled.step(field, r, induce=False)
    planted = {d.law for d in spec.domains}
    assert learner.laws & planted, "no planted law was induced"
    assert learner.ledger.hits > 0           # it bets and sometimes wins
    assert misled.ledger.misses > 0          # the wrong law bets and loses
    assert learner.ledger.accuracy > fixed.ledger.accuracy
    assert learner.ledger.accuracy > misled.ledger.accuracy
