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


def test_domains_share_individuals_so_atoms_can_overlap():
    """Overlap lives in the domains' own individual lists: each holds the
    ten-strong core `s1..s10` alongside its thirty private names, so alpha and
    beta genuinely emit atoms about the same individual.

    Measured over 60 rounds at 14 seeds: alpha and beta both mention between 5
    and 9 of the ten core individuals (mean 6.2), and 21.2% of alpha's `shared`
    draws land in the core (10/40 = 25% expected)."""
    spec = default_spec(seed=20260728)
    field = Field(spec)
    seen = {}
    for d in spec.domains:
        args = set()
        for r in range(40):
            args |= {a for rel, a in field.deliver(d.name, r) if rel == "shared"}
        seen[d.name] = args
    alpha, beta = seen["alpha"], seen["beta"]
    assert alpha & beta, "no individual is shared across domains — overlap is naming only"


def test_shared_and_a_local_relation_can_name_the_same_individual():
    """The property whose absence was the defect this field was repaired for.

    When `shared` drew from a pool of s-individuals disjoint from every
    domain's own, `shared(a20)` could never arrive, so any law of the form
    *domain-relation -> shared* was structurally unsatisfiable and a rival
    holding one had a hit ceiling of exactly zero. With the core inside each
    domain's list, `shared` and `a_head` draw from the same forty names and
    overlap heavily: 28 of 33 shared-arguments also carry `a_head` at seed
    20260728, 22 of 28 at seed 7."""
    field = Field(default_spec(seed=20260728))
    shared_args, head_args = set(), set()
    for r in range(60):
        for rel, args in field.deliver("alpha", r):
            if rel == "shared":
                shared_args.add(args)
            elif rel == "a_head":
                head_args.add(args)
    assert shared_args & head_args, (
        "no individual carries both `shared` and `a_head` — a "
        "*domain-relation -> shared* law could never hit, which is the defect "
        "the shared core was added to remove"
    )


def test_a_wrong_law_has_a_nonzero_hit_ceiling():
    """The Stage 1 gate's rival must be able to WIN, not merely to bet.

    A rival that can only lose is a walkover, and the gate reading it says
    nothing about induction beating a plausible competitor. `a_head -> shared`
    is the rival the gate uses; on this field it scores 7–15 hits against
    239–516 misses across 14 seeds (11/241 here). A sweep of all twenty
    body→head pairs over the aperture's five relations finds every wrong law
    that bets at all also hitting at least twice — accidental regularities are
    possible in this field, and none of them pays."""
    spec = default_spec(seed=20260728)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    rival = Unit("rival", ap, laws={(spec.domains[0].law[1], "shared")})
    for r in range(60):
        rival.step(field, r, induce=False)
    assert rival.ledger.hits > 0, "the wrong law cannot win — no real falsifier"
    assert rival.ledger.net_score < 0, "the wrong law must still lose overall"
