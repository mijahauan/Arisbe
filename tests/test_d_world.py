"""The D-series priced world: reserves, a determined price, and a found population."""

from c_field import (CORE, PAIRS, Field, apertures_for, default_spec,
                     units_for_witnesses, wide_spec, witnesses_per_domain)


def test_wide_spec_gives_eight_domains_and_twenty_eight_seats():
    """The seat ceiling must sit well clear of any equilibrium, or the cap
    decides the population and P-D7 is uninterpretable (spec section 8 item 6)."""
    spec = wide_spec()
    assert len(spec.domains) == 8
    # 28 = C(8,2): the world's own ceiling, not a number anyone chose.
    assert len(apertures_for(spec, n_units=28, scheme=PAIRS)) == 28
    # Every domain carries its own law and its own local antecedent.
    assert len({d.law for d in spec.domains}) == 8
    assert all("shared" in d.antecedents for d in spec.domains)


def test_wide_spec_individuals_are_shared_core_plus_private():
    """Same construction as default_spec: the ten-strong core every domain
    knows, plus thirty private names per domain that no other domain uses."""
    spec = wide_spec()
    for d in spec.domains:
        assert set(CORE) <= set(d.individuals)
        assert len(d.individuals) == 40
    private = [set(d.individuals) - set(CORE) for d in spec.domains]
    for i, a in enumerate(private):
        for b in private[i + 1:]:
            assert not (a & b), "private individuals must not collide"


def test_wide_spec_reaches_three_witnesses_per_domain():
    """N0 is DERIVED, not chosen: the smallest community in which every domain
    has the three witnesses the corroboration ruling requires (spec 3.4)."""
    spec = wide_spec()
    n0 = units_for_witnesses(spec, 3, PAIRS)
    counts = witnesses_per_domain(spec, apertures_for(spec, n0, scheme=PAIRS))
    assert min(counts.values()) >= 3
    assert n0 < 28, "N0 must leave room to grow toward the ceiling"


def test_wide_spec_is_deterministic_and_delivers():
    spec = wide_spec()
    assert wide_spec().domains == spec.domains
    field = Field(spec)
    assert field.deliver("dom0", 5) == field.deliver("dom0", 5)
    assert any(field.deliver(f"dom{i}", r) for i in range(8) for r in range(5))


def test_default_spec_is_untouched():
    """The additive guarantee: no existing C-series figure may move."""
    assert len(default_spec().domains) == 4
    assert [d.name for d in default_spec().domains] == [
        "alpha", "beta", "gamma", "delta"]


import pytest

from d_world import Reserves, Source


def test_source_defaults_to_the_numeraire():
    """E1 = 1 fixes the unit of account and nothing else (spec 3.4)."""
    assert Source().pool_per_round == 1.0
    assert Source().entry_price == 0.0


def test_reserves_credit_charge_and_balance():
    r = Reserves()
    r.seed("u0", 10.0)
    r.credit("u0", 2.5)
    r.charge("u0", 4.0)
    assert r.balance("u0") == pytest.approx(8.5)


def test_death_is_reserve_at_or_below_zero():
    """No die(), no TTL, no lifespan -- running out IS death (spec ruling 1)."""
    r = Reserves()
    r.seed("u0", 1.0)
    assert r.alive("u0")
    r.charge("u0", 1.0)
    assert not r.alive("u0"), "exactly zero is dead, not the last breath"
    r.seed("u1", 1.0)
    r.charge("u1", 5.0)
    assert not r.alive("u1")


def test_living_is_sorted_and_excludes_the_dropped():
    r = Reserves()
    for uid in ("u2", "u0", "u1"):
        r.seed(uid, 3.0)
    assert r.living() == ["u0", "u1", "u2"]
    r.charge("u1", 3.0)
    assert r.living() == ["u0", "u2"]
    r.drop("u1")
    assert r.living() == ["u0", "u2"]
    assert r.total() == pytest.approx(6.0)


def test_an_unknown_unit_has_no_balance_and_is_not_alive():
    r = Reserves()
    assert r.balance("ghost") == 0.0
    assert not r.alive("ghost")


def test_seeding_twice_refuses():
    """A unit is endowed once, at entry. Re-seeding would create wealth from
    nothing and break the conservation the whole design rests on."""
    r = Reserves()
    r.seed("u0", 1.0)
    with pytest.raises(ValueError, match="already"):
        r.seed("u0", 1.0)
