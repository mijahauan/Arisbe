from c_field import Field, default_spec


def test_same_seed_delivers_identical_streams():
    a = Field(default_spec(seed=7))
    b = Field(default_spec(seed=7))
    for r in range(5):
        for d in ("alpha", "beta", "gamma", "delta"):
            assert a.deliver(d, r) == b.deliver(d, r)


def test_consequents_lag_their_antecedents_by_one_round():
    spec = default_spec(seed=7)
    field = Field(spec)
    d = spec.domains[0]
    body_rel, head_rel = d.law

    assert not [f for f in field.deliver(d.name, 0) if f[0] == head_rel], \
        "round 0 has no prior round, so no consequent may appear"

    bodies_at_0 = {args for rel, args in field.deliver(d.name, 0) if rel == body_rel}
    heads_at_1 = {args for rel, args in field.deliver(d.name, 1) if rel == head_rel}
    assert bodies_at_0 == heads_at_1, "each consequent follows its antecedent by one round"


import pytest

from c_field import Field, default_spec, apertures_for


def test_apertures_differ_between_units():
    """Pairwise distinct, not merely not-all-identical: a weaker assertion
    would pass while two of the four units silently shared a slice."""
    spec = default_spec(seed=7)
    aps = apertures_for(spec, n_units=4)
    assert len(aps) == 4
    assert len({a.domains for a in aps}) == len(aps), \
        "two units share an aperture — premise 3 (divergence by construction) violated"


def test_more_units_than_domains_is_refused():
    """The assignment cycles with period len(domains); asking for more units
    than that cannot yield distinct apertures, so it raises rather than
    silently colliding."""
    spec = default_spec(seed=7)
    with pytest.raises(ValueError) as exc:
        apertures_for(spec, n_units=len(spec.domains) + 1)
    msg = str(exc.value)
    assert "5" in msg and "4" in msg, "the message must name both numbers"
    assert "distinct" in msg


def test_aperture_delivers_the_union_of_its_domains():
    spec = default_spec(seed=7)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    expected = set()
    for name in ap.domains:
        expected |= set(field.deliver(name, 3))
    assert set(field.at(ap, 3)) == expected


from c_unit import Unit


def test_anticipation_stays_live_late_in_a_run():
    """Saturation check: a lawful unit must still be placing bets after round 40."""
    spec = default_spec(seed=20260728)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    u = Unit("u0", ap)
    u.laws.add(spec.domains[0].law)
    early = late = 0
    for r in range(60):
        bets = len(u.anticipate())
        if r < 20:
            early += bets
        elif r >= 40:
            late += bets
        u.step(field, r)
    assert early > 0
    assert late > 0, "the field saturated — no bets placed after round 40"
