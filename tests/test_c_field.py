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


from c_field import Field, default_spec, apertures_for


def test_apertures_differ_between_units():
    spec = default_spec(seed=7)
    aps = apertures_for(spec, n_units=4)
    assert len(aps) == 4
    assert len({a.domains for a in aps}) > 1, "all apertures identical — premise 3 violated"


def test_aperture_delivers_the_union_of_its_domains():
    spec = default_spec(seed=7)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    expected = set()
    for name in ap.domains:
        expected |= set(field.deliver(name, 3))
    assert set(field.at(ap, 3)) == expected
