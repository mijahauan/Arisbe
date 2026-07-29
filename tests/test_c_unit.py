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


def test_held_law_beats_no_law_over_a_run():
    spec, field, ap = _setup()
    lawful, lawless = Unit("u0", ap), Unit("u1", ap)
    lawful.laws.add(spec.domains[0].law)
    for r in range(20):
        lawful.step(field, r)
        lawless.step(field, r)
    assert lawful.ledger.hits > 0
    assert lawless.ledger.hits == 0
    assert lawful.ledger.accuracy > lawless.ledger.accuracy
