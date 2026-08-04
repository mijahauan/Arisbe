"""The D-series priced world: reserves, a determined price, and a found population."""

import ast
import dataclasses
import re

from c_field import (CORE, PAIRS, Field, apertures_for, default_spec,
                     units_for_witnesses, wide_spec, witnesses_per_domain)
from c_unit import Unit


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


def test_dropping_a_solvent_unit_removes_its_balance_from_the_total():
    """FIX ROUND 5 (the final review): `Reserves.drop` had ZERO OBSERVABLE
    COVERAGE. Replacing the `self.reserves.drop(...)` call in
    `_settle_population` with `pass` left all 56 tests passing, and the one
    test that called `drop` at all
    (`test_living_is_sorted_and_excludes_the_dropped`) dropped a unit already
    charged to exactly 0.0, so `total()` could not move and `living()` already
    excluded it -- every assertion held identically with the method gutted.

    The call SITE cannot be covered through `total()`, and that is worth
    stating rather than working around: `_settle_population` drops only units
    the world has just found dead, whose balance is 0.0 by construction, so
    removing the key changes no sum. What is covered here is `drop` ITSELF, on
    the only input that can distinguish it from a no-op -- a unit with a
    POSITIVE balance. The wealth leaves with it, which is what makes `drop` a
    removal rather than a bookkeeping flourish."""
    r = Reserves()
    r.seed("u0", 3.0)
    r.seed("u1", 7.0)
    assert r.total() == pytest.approx(10.0)
    r.drop("u1")
    assert r.total() == pytest.approx(3.0), \
        "dropping a solvent unit must take its balance out of the total"
    assert r.balance("u1") == 0.0
    assert r.living() == ["u0"]
    # And the id is genuinely gone, not merely zeroed: a zeroing implementation
    # would still refuse a re-seed, since `seed` keys on presence.
    r.seed("u1", 2.0)
    assert r.total() == pytest.approx(5.0)


def test_dropping_an_unknown_unit_is_silent():
    """`_settle_population` drops after `release`, and a caller that has
    already dropped must not be punished for it."""
    r = Reserves()
    r.seed("u0", 1.0)
    r.drop("ghost")
    assert r.total() == pytest.approx(1.0)


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


from d_world import Seats, SeatsFull, seats_from


def test_seats_hand_out_the_lowest_free_slice():
    seats = Seats([("a", "b"), ("a", "c"), ("b", "c")])
    assert seats.take("u0").domains == ("a", "b")
    assert seats.take("u1").domains == ("a", "c")
    assert seats.free() == 1
    assert seats.occupied() == 2


def test_a_seat_carries_the_occupant_s_own_id():
    """Field.at reads aperture.unit_id as the OBSERVER, so a newcomer taking a
    vacated slice must observe through its own membrane, not the dead unit's."""
    seats = Seats([("a", "b")])
    first = seats.take("u0")
    assert first.unit_id == "u0"
    seats.release("u0")
    second = seats.take("u9")
    assert second.unit_id == "u9"
    assert second.domains == first.domains


def test_release_frees_the_slice_for_reuse():
    seats = Seats([("a", "b"), ("a", "c")])
    seats.take("u0")
    seats.take("u1")
    assert seats.free() == 0
    seats.release("u0")
    assert seats.free() == 1
    assert seats.take("u2").domains == ("a", "b")


def test_a_full_world_refuses_rather_than_seating_a_twin():
    """The ceiling is the world's. Seating two units on one slice would defeat
    premise 3's requirement that units meet the field differently -- and the
    candidate reading that would permit it for BORN units is unruled (spec
    section 11.1)."""
    seats = Seats([("a", "b")])
    seats.take("u0")
    with pytest.raises(SeatsFull, match="no free seat"):
        seats.take("u1")


def test_releasing_an_unseated_unit_refuses():
    seats = Seats([("a", "b")])
    with pytest.raises(ValueError, match="not seated"):
        seats.release("ghost")


def test_seats_from_the_wide_spec_gives_twenty_eight():
    seats = seats_from(wide_spec())
    assert seats.free() == 28


from dataclasses import dataclass, field as dc_field
from typing import List, Set, Tuple

from c_marks import FACT, Mark, MarkBoard
from d_world import PricedWorld, RoundReport, demand_of, hits_of


@dataclass
class _Entry:
    round_idx: int
    result: str


@dataclass
class _Ledger:
    entries: List[_Entry] = dc_field(default_factory=list)


@dataclass
class _StubUnit:
    """A unit-shaped stand-in. The world reads only these four things, so the
    stub pins exactly the surface `PricedWorld` depends on -- and if the real
    Unit ever stops offering it, Task 6's integration test says so."""
    unit_id: str
    facts: Set[Tuple[str, tuple]] = dc_field(default_factory=set)
    laws: Set[Tuple[str, str]] = dc_field(default_factory=set)
    ledger: _Ledger = dc_field(default_factory=_Ledger)


def _stub(uid, n_facts=0, n_laws=0, hits=0, round_idx=0):
    u = _StubUnit(uid)
    u.facts = {(f"r{i}", (("c", "a"),)) for i in range(n_facts)}
    u.laws = {(f"b{i}", f"h{i}") for i in range(n_laws)}
    u.ledger.entries = [_Entry(round_idx, "hit") for _ in range(hits)]
    return u


def _world(entry_price=0.0, subtract=True, board=None, tariff=0.25):
    """A world at a FIXED tariff (fix round 3). `tariff` used to be derived
    inside `settle` as `pool_per_round / demand`; it is now a calibrated
    constant carried on the `Source`, so every unit test that expects a charge
    has to say what price is in force. `0.25` is a stand-in for a calibrated
    value -- a legible round number, not a measurement -- and it is a
    CONSTANT here in the sense that matters: it does not move when the
    community's demand does."""
    return PricedWorld(Source(1.0, entry_price, tariff),
                       seats_from(wide_spec()),
                       board if board is not None else MarkBoard(),
                       subtract=subtract)


def test_demand_counts_held_content_and_acts_minted_this_round():
    """A held fact-round and a minted act each count 1 -- the NULL choice of
    units, asserting no difference between holding and speaking (spec 3.3)."""
    board = MarkBoard()
    board.publish(Mark(author="u0", content=("p", (("c", "a"),)),
                       kind=FACT, round_idx=7))
    board.publish(Mark(author="u0", content=("q", (("c", "a"),)),
                       kind=FACT, round_idx=7))
    board.publish(Mark(author="u1", content=("z", (("c", "a"),)),
                       kind=FACT, round_idx=7))
    board.publish(Mark(author="u0", content=("old", (("c", "a"),)),
                       kind=FACT, round_idx=6))
    u = _stub("u0", n_facts=3, n_laws=2)
    # 3 facts + 2 laws + 2 acts minted AT ROUND 7 (the round-6 mark is not this
    # round's act, and u1's is not this unit's).
    assert demand_of(u, board, 7) == 7.0


def test_hits_are_this_round_s_only():
    u = _stub("u0")
    u.ledger.entries = [_Entry(4, "hit"), _Entry(5, "hit"),
                        _Entry(5, "miss"), _Entry(5, "abstain")]
    assert hits_of(u, 5) == 1
    assert hits_of(u, 4) == 1
    assert hits_of(u, 6) == 0


def test_tau_is_the_calibrated_constant_and_does_not_move_with_demand():
    """FIX ROUND 3, and the property this round exists for. `tau =
    pool_per_round / demand` was retired: normalising the charge to the pool
    every round makes total collected EXACTLY the pool no matter what the
    community does, so a unit that mints ten times its peers' acts pays only
    by lowering everyone's share and never by paying more. `tau` is now the
    calibrated constant `source.tariff` -- it is the same price at four units
    of demand as at forty, and the charge is `tariff * demand`, which is what
    gives the tariff its aggregate bite."""
    world = _world(tariff=0.25)
    small = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
    for u in small:
        world.admit(u)
    report = world.settle(small, 0)
    assert report.demand == 4.0
    assert report.tau == pytest.approx(0.25)
    assert sum(report.charges.values()) == pytest.approx(1.0)

    # TEN TIMES THE DEMAND AT THE SAME PRICE. Under the retired form tau would
    # have fallen to 1/40 and the total would still have been exactly 1.0.
    big_world = _world(tariff=0.25)
    big = [_stub("u2", n_facts=20), _stub("u3", n_facts=20)]
    for u in big:
        big_world.admit(u)
    big_report = big_world.settle(big, 0)
    assert big_report.demand == 40.0
    assert big_report.tau == pytest.approx(0.25)
    assert sum(big_report.charges.values()) == pytest.approx(10.0)


def test_income_is_pro_rata_by_hits():
    world = _world()
    units = [_stub("u0", n_facts=1, hits=3), _stub("u1", n_facts=1, hits=1)]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.incomes["u0"] == pytest.approx(0.75)
    assert report.incomes["u1"] == pytest.approx(0.25)


def test_a_hitless_round_pays_nothing_and_burns_the_pool():
    """THE WORLD'S TEETH. A round in which nobody predicted anything correctly
    charges the tariff on all demand and pays nothing back, so the stock falls
    -- which is how a community comes to have a lifespan of its own doing
    (spec 3.3). FIX ROUND 3: the outflow is `tariff * demand` (here 0.25 * 4),
    not the pool; it happens to equal the pool at this demand and would not at
    any other."""
    world = _world(tariff=0.25)
    units = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 10.0)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert report.incomes == {}
    assert report.collected == pytest.approx(0.25 * report.demand)
    assert world.reserves.total() == pytest.approx(before - report.collected)


def test_the_world_is_conservative_whenever_anyone_hits():
    """`total_after == total_before - collected + incomes`, to the last unit of
    account. The one place a rounding bug would silently create or destroy
    wealth (spec 10).

    FIX ROUND 3: this used to assert `sum(charges) == sum(incomes)` and read
    `total_after == total_before`. That is the retired `tau = pool / demand`
    identity, not conservation -- it held BECAUSE the old price normalised
    total collection to exactly the pool every round, which is precisely the
    defect this round removes. The world is OPEN: outflow and inflow are two
    independent quantities and there is no reason for them to be equal. What
    must hold, and is asserted here, is that the books balance across them."""
    world = _world(tariff=0.25)
    units = [_stub("u0", n_facts=3, n_laws=1, hits=2),
             _stub("u1", n_facts=7, hits=1),
             _stub("u2", n_facts=1, n_laws=4)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 10.0)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert world.reserves.total() == pytest.approx(
        before - report.collected + sum(report.incomes.values()))
    # THE BITE: 16 units of demand at 0.25 is 4.0 out against a 1.0 pool in.
    # Under the retired form these two were equal by construction.
    assert report.collected == pytest.approx(4.0)
    assert sum(report.incomes.values()) == pytest.approx(1.0)


def test_charge_is_proportional_to_a_unit_s_own_demand():
    world = _world()
    units = [_stub("u0", n_facts=3), _stub("u1", n_facts=1)]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.charges["u0"] == pytest.approx(0.75)
    assert report.charges["u1"] == pytest.approx(0.25)


def test_arm_zero_computes_the_charge_and_does_not_subtract_it():
    """A0 -- the control and the calibration source. The meter READ, which is
    exactly today's system, so the wrapper must change nothing (spec 6)."""
    world = _world(subtract=False)
    units = [_stub("u0", n_facts=2, hits=1), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 5.0)
    report = world.settle(units, 0)
    assert report.charges["u0"] == pytest.approx(0.5)   # reported
    assert world.reserves.balance("u0") == pytest.approx(5.0)   # not subtracted
    assert world.reserves.balance("u1") == pytest.approx(5.0)


def test_a_community_with_no_demand_is_charged_nothing():
    """Nothing held and nothing said: nothing is charged.

    FIX ROUND 3: this used to assert `tau is None` -- the guard against the
    division in `tau = pool / demand`. There is no division any more, so
    there is nothing to guard: a zero-demand round reports the standing
    tariff like any other round and simply prices every unit at zero. The
    price of a thing does not become undefined because nobody bought
    any."""
    world = _world(tariff=0.25)
    units = [_stub("u0"), _stub("u1")]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.demand == 0.0
    assert report.tau == pytest.approx(0.25)
    assert set(report.charges) == {"u0", "u1"}
    assert all(c == 0.0 for c in report.charges.values())
    assert report.collected == 0.0


def test_at_a_fixed_tariff_minting_costs_strictly_more():
    """THE PROPERTY THIS FIX ROUND EXISTS FOR, and the one whose ABSENCE caused
    it. Under the retired `tau = pool_per_round / demand` the world collected
    exactly `pool_per_round` every round no matter what anyone did, so the
    tariff had no aggregate bite: measured directly, `A2a` (the channel off
    entirely, minting nothing) and `A2b` (minting thousands of acts that reach
    nobody) collected THE SAME TOTAL every round and finished every seed with
    IDENTICAL survivor, birth and death counts. Cost was purely positional --
    a unit paid for out-speaking its peers, never for speaking as such.

    The contrast is built here at the settle boundary, where `collected` can be
    read directly: two worlds at the SAME fixed tariff, holding the same
    content, in the same round, differing ONLY in whether the units minted
    acts. Minting must cost strictly more in absolute terms."""
    def collected_when_minting(n_acts: int) -> float:
        board = MarkBoard()
        for i in range(n_acts):
            board.publish(Mark(author="u0", content=(f"p{i}", (("c", "a"),)),
                               kind=FACT, round_idx=0))
        world = _world(board=board, tariff=0.25)
        units = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
        for u in units:
            world.admit(u)
            world.reserves.seed(u.unit_id, 100.0)   # rich enough to pay in full
        return world.settle(units, 0).collected

    a2a_collected = collected_when_minting(0)    # the channel off: nothing minted
    a2b_collected = collected_when_minting(6)    # mints, is charged, reaches nobody

    assert a2b_collected > a2a_collected
    # And by exactly the tariff on the extra demand -- six acts at 0.25.
    assert a2b_collected - a2a_collected == pytest.approx(1.5)


def test_settle_is_deterministic():
    def run():
        world = _world()
        units = [_stub("u1", n_facts=2, hits=1), _stub("u0", n_facts=3)]
        for u in units:
            world.admit(u)
            world.reserves.seed(u.unit_id, 4.0)
        return world.settle(units, 0)
    a, b = run(), run()
    assert a.charges == b.charges and a.incomes == b.incomes
    assert a.tau == b.tau


def _maker(created):
    def make_unit(unit_id, aperture):
        u = _stub(unit_id)
        created.append((unit_id, aperture))
        return u
    return make_unit


def test_a_unit_that_runs_out_leaves_and_frees_its_seat():
    """Mortality is a CONSEQUENCE: no die(), no TTL, no lifespan (spec P-D1)."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    seated = world.seats.occupied()
    report = world.settle(units, 0)
    assert "u1" in report.died
    assert [u.unit_id for u in report.units] == ["u0"]
    assert world.seats.occupied() == seated - 1


def test_a_rich_unit_splits_and_the_split_is_conservative():
    """Each takes HALF the parent's reserve, so wealth is redistributed and
    never created -- a parent at 3*E0 yields two at 1.5*E0, not two at E0 with
    the remainder burned (spec 3.4).

    FIX ROUND 3: the total is read against the round's own flows rather than
    against `before` alone. `total_after == before` held only because the
    retired `tau = pool / demand` made this round's outflow exactly equal its
    inflow; the SPLIT's own conservation -- the claim this test is named for
    -- is that the two halves are equal and nothing is burned, which is
    asserted directly."""
    created = []
    world = _world(entry_price=1.0, tariff=0.25)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 6.0)
    before = world.reserves.total()
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert len(report.born) == 1
    parent_id, child_id = report.born[0]
    assert parent_id == "u0"
    assert world.reserves.total() == pytest.approx(
        before - report.collected + sum(report.incomes.values()))
    assert world.reserves.balance(parent_id) == pytest.approx(
        world.reserves.balance(child_id))
    assert world.reserves.balance(child_id) >= world.source.entry_price
    assert len(created) == 1 and created[0][0] == child_id


def test_a_newborn_takes_a_free_seat_and_inherits_nothing_but_the_board():
    """It arrives with no facts, no laws and no standing, and is socialized by
    marks it never made -- Berger and Luckmann's secondary socialization, and
    already built (spec 3.3).

    FIX ROUND 5 (the final review): the old body asserted `child.facts ==
    set()` against a child built by this file's own `_stub`, whose fields
    default empty -- TRUE BY CONSTRUCTION OF THE TEST, and it would have held
    just as well if the world had handed the maker the parent's entire
    record. Two changes make it a claim about the world. (1) The child is a
    REAL `c_unit.Unit`, exactly as `run_d1.play`'s `make_unit` builds it, so
    emptiness is a property of the newborn rather than of the stub. (2) The
    parent is loaded with content first and the maker records everything the
    world passed it: what the world hands a maker is `(child_id, aperture)`
    AND NOTHING ELSE, so there is no channel through which inheritance could
    travel even if a future maker wanted it. That is the checkable half of
    "inherits nothing"; the seat is the other half."""
    handed = []

    def make_real_unit(unit_id, aperture):
        handed.append((unit_id, aperture))
        return Unit(unit_id, aperture)

    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=4, n_laws=2, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 8.0)
    assert parent.facts and parent.laws, "the parent must have content to withhold"
    report = world.settle([parent], 0, make_unit=make_real_unit)

    child = [u for u in report.units if u.unit_id != "u0"][0]
    assert isinstance(child, Unit)
    assert child.facts == set() and child.laws == set()
    assert child.peers == {} and child.ledger.entries == []
    # THE WORLD HANDED THE MAKER NOTHING ELSE. One call, two arguments, and
    # neither of them is the parent or anything the parent holds.
    assert len(handed) == 1
    child_id, aperture = handed[0]
    assert (child_id, aperture) == (child.unit_id, child.aperture)
    assert aperture.unit_id == child.unit_id
    assert len(aperture.domains) == 2
    assert child.unit_id != parent.unit_id


def test_the_breeding_threshold_is_twice_the_entry_price_exactly():
    """FIX ROUND 5 (the final review): THE DESIGN'S LOAD-BEARING NUMBER WAS
    ENTIRELY UNTESTED. Changing `2.0 * self.source.entry_price` in
    `_settle_population` to `1.0 *` left all 56 tests passing -- every birth
    test seeded a parent far above either threshold, so no test could tell the
    two apart. The multiple is not decoration: it is the whole reading of the
    rule, "you may reproduce when you can pay a newcomer's entry AND REMAIN
    VIABLE YOURSELF" (spec 3.4). At `1.0 *` a unit breeds by handing over half
    of exactly what a newcomer costs and dropping below entry itself.

    Read at a ZERO TARIFF with no hits, so `settle` moves no balance and the
    threshold is the only thing deciding: the reserve the parent carries into
    `_settle_population` is exactly the one seeded here."""
    e0 = 1.0
    def born_at(balance: float):
        created = []
        world = _world(entry_price=e0, tariff=0.0)
        parent = _stub("u0")                      # no facts, no laws, no hits
        world.admit(parent)
        world.reserves.seed("u0", balance)
        report = world.settle([parent], 0, make_unit=_maker(created))
        assert report.charges["u0"] == 0.0 and report.incomes == {}
        assert world.reserves.balance("u0") + sum(
            world.reserves.balance(c) for _, c in report.born) == \
            pytest.approx(balance), "nothing may move but the split itself"
        return report.born

    # BELOW the threshold and NOT below `1.0 * E0` -- the mutation's own range.
    assert born_at(1.5 * e0) == (), \
        "1.5*E0 is above the entry price and below twice it: no birth"
    assert born_at(2.0 * e0 - 1e-9) == (), "just below 2*E0: no birth"
    # AT and ABOVE it.
    assert len(born_at(2.0 * e0)) == 1, "at exactly 2*E0 the unit may breed"
    assert len(born_at(2.0 * e0 + 1e-9)) == 1
    # And the split leaves BOTH sides viable, which is what the multiple means.
    world = _world(entry_price=e0, tariff=0.0)
    parent = _stub("u0")
    world.admit(parent)
    world.reserves.seed("u0", 2.0 * e0)
    report = world.settle([parent], 0, make_unit=_maker([]))
    _, child_id = report.born[0]
    assert world.reserves.balance("u0") == pytest.approx(e0)
    assert world.reserves.balance(child_id) == pytest.approx(e0)


def test_birth_needs_a_positive_entry_price():
    """The calibration arm does not breed: E0 is not yet known there, so a zero
    threshold would make every unit split every round (spec 3.4)."""
    created = []
    world = _world(entry_price=0.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 100.0)
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert report.born == ()
    assert created == []


def test_birth_needs_a_maker():
    """Without one the world cannot construct a unit, and it says so rather than
    silently declining to reproduce."""
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 9.0)
    report = world.settle([parent], 0)          # no make_unit
    assert report.born == ()


def test_a_full_world_simply_does_not_breed():
    """SeatsFull is a refusal at the seat, but a world with no room is a world
    where births do not happen -- not an error the run should die on."""
    created = []
    world = PricedWorld(Source(1.0, 1.0, 0.25), Seats([("a", "b")]),
                        MarkBoard())
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 9.0)
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert report.born == ()
    assert created == []


def test_death_is_settled_before_birth():
    """A seat freed this round is available this round: the world settles who
    left before it asks who may arrive, so a community at the ceiling can still
    turn over."""
    created = []
    world = PricedWorld(Source(1.0, 1.0, 0.25),
                        Seats([("a", "b"), ("a", "c")]), MarkBoard())
    rich = _stub("u0", n_facts=1, hits=1)
    poor = _stub("u1", n_facts=50)
    for u, amount in ((rich, 9.0), (poor, 0.01)):
        world.admit(u)
        world.reserves.seed(u.unit_id, amount)
    report = world.settle([rich, poor], 0, make_unit=_maker(created))
    assert report.died == ("u1",)
    assert len(report.born) == 1


def test_a_newborn_id_is_never_reused():
    """FIX ROUND 5 (the final review): this test had an empty loop body and
    `0 == 0` for a closing assertion whenever no birth occurred, so DISABLING
    BIRTHS ENTIRELY left it passing -- verified by injection. A uniqueness
    check over an empty set is not a uniqueness check. The birth count is now
    asserted first, so the loop below has something to be about."""
    created = []
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 40.0)
    seen = set()
    units = [parent]
    for r in range(4):
        report = world.settle(units, r, make_unit=_maker(created))
        for _, child_id in report.born:
            assert child_id not in seen
            seen.add(child_id)
        units = list(report.units)
    assert len(seen) >= 4, (
        f"only {len(seen)} births in four rounds from a 40.0 reserve at a 1.0 "
        f"entry price -- with no births this test checks nothing at all"
    )
    assert len(seen) == len(created)


def test_conservation_holds_across_a_death():
    """The world is OPEN, not closed: what leaves is `collected` (bounded by
    what each unit actually holds), what enters is the pool-derived income,
    and total_after == total_before - collected + sum(incomes) holds exactly
    by construction, even across a death (author ruling, fix round 2).

    FIX ROUND 5 (the final review): the death is now ASSERTED. The docstring
    said "across a death" and the body never checked that one happened, so
    the test would have gone on passing as a plain conservation check if
    `u1`'s starvation ever stopped being fatal -- which is the one condition
    the name promises to cover."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert report.died == ("u1",), \
        "no death occurred, so this checks conservation and not the name"
    assert world.reserves.total() == pytest.approx(
        before - report.collected + sum(report.incomes.values()))


def test_a_balance_never_goes_below_zero():
    """u1's nominal charge (99 units of demand at 0.25, so 24.75) far exceeds
    its balance (0.5); extraction is bounded, so it lands at exactly 0.0 --
    dead, not in debt. FIX ROUND 3: the nominal charge used to be 0.99, the
    retired `pool / demand` share; a flat tariff makes the same point far more
    starkly, since the meter reading is now absolute rather than a slice of a
    fixed pool."""
    world = _world(entry_price=1.0, tariff=0.25)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    world.settle(units, 0)
    assert world.reserves.balance("u1") == pytest.approx(0.0)
    assert not world.reserves.alive("u1")


def test_collection_falls_short_while_the_full_pool_still_arrives():
    """u1 cannot pay its full nominal charge, so less leaves the community
    than the tariff nominally demanded -- but the full pool still enters,
    since the inflow is external and does not depend on what was collected.
    Total wealth can RISE on a round where a peer starves; that is accepted,
    not compensated for (author ruling, fix round 2)."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert report.collected < sum(report.charges.values())
    assert sum(report.incomes.values()) == pytest.approx(
        world.source.pool_per_round)
    assert world.reserves.total() == pytest.approx(
        before + (world.source.pool_per_round - report.collected))


import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from run_d1 import ARMS, ArmResult, calibrate, play   # noqa: E402


def test_all_four_arms_run_and_report():
    for arm in ARMS:
        result = play(arm, seed=1, rounds=8, source=Source(1.0, 0.05, 0.05))
        assert isinstance(result, ArmResult)
        assert result.arm == arm
        assert result.survivors >= 0


def test_arm_zero_never_subtracts_so_nobody_dies():
    """A0 is the control: the meter READ. Reserves must not move at all.

    FIX ROUND 3: played at a NONZERO tariff. With `tariff=0.0` every charge is
    zero anyway, so "reserves untouched" held for the wrong reason and the
    control tested nothing. A standing price of 0.25 makes the claim real --
    the meter reads, and `subtract=False` still moves nothing."""
    result = play("A0", seed=1, rounds=12, source=Source(1.0, 0.0, 0.25))
    assert result.died == 0
    assert result.born == 0
    balances = {uid: result.world.reserves.balance(uid)
                for uid in result.world.reserves.living()}
    assert balances, "A0 must still seat and endow its units"
    assert len(set(round(b, 9) for b in balances.values())) == 1, \
        "every A0 balance is its untouched endowment"


def test_a_founder_is_endowed_at_the_entry_price_and_must_double_to_breed():
    """The endowment is E0 exactly, so a founder starts ON the entry price and
    has to double before it may breed. An endowment floored at 1.0 would put
    every founder above the threshold whenever the measured E0 fell below 1.0,
    and round 0 would be a birth wave that measured the endowment rather than
    the world.

    FIX ROUND 2 (finding 3): this now checks what its name claims.
    `rounds=1` let one round of settling run before reading balances, so the
    old body actually checked "nobody breeds after paying a round's tariff",
    which holds for essentially any sub-threshold entry price -- no income is
    possible before the consequent lag elapses regardless of the exact
    endowment. `rounds=0` runs the loop zero times, so `play` still seats and
    endows every founder (the seeding happens before the round loop) but
    nothing ever touches a balance, and the test can assert the endowment
    itself: each founder's balance is `source.entry_price` EXACTLY, and it
    sits strictly below the `2 * entry_price` breeding threshold by
    construction (entry_price > 0), so no birth is possible from the
    endowment alone. The tariff is carried but never applied: `rounds=0` means
    `settle` is never reached, so this reads the endowment and nothing
    else."""
    source = Source(1.0, 0.25, 0.25)
    result = play("A1", seed=1, rounds=0, source=source)
    living = result.world.reserves.living()
    assert living, "the arm must seat and endow its founders"
    for uid in living:
        assert result.world.reserves.balance(uid) == pytest.approx(
            source.entry_price)
    assert result.born == 0


def test_the_real_unit_offers_the_surface_the_world_reads():
    """The stub in the unit tests pins a surface; this pins that the REAL Unit
    still offers it, so the two cannot drift apart.

    ENDOWMENT 10.0 AT A TARIFF OF 0.05 (fix round 3, replacing fix round 2's
    `entry_price=0.5` at the retired demand-normalised price). A flat tariff
    charges in ABSOLUTE terms, so the old sub-1.0 endowments no longer buy a
    single round: measured directly at 6 rounds, `(E=5.0, T=0.05)` and
    `(E=2.0, T=0.05)` both go extinct 18/18 while `(E=10.0, T=0.05)` holds all
    18. This test pins the real `Unit`'s SURFACE, not the economy, so the
    endowment is deliberately generous -- it buys the cohort's survival so
    there is something to inspect, and it is not a claim about what a
    community can afford.

    FIX ROUND 2 (finding 2): guarded explicitly rather than relying on the
    entry price alone to keep it that way -- this test's own docstring named
    the vacuous-pass failure mode, and finding 1's wiring of corroborate/
    dispose_challenges changes law counts and therefore demand, so the guard
    matters more now, not less."""
    result = play("A1", seed=1, rounds=6, source=Source(1.0, 10.0, 0.05))
    assert result.final_units, (
        "the founding cohort must survive to round 6, or this loop silently "
        "checks nothing"
    )
    for u in result.final_units:
        assert isinstance(u.unit_id, str)
        assert isinstance(u.facts, set) and isinstance(u.laws, set)
        assert hasattr(u.ledger, "entries")


def test_a2b_mints_and_is_charged_while_nothing_reaches_anyone():
    """The honest ablation: cost held, sign removed.

    FIX ROUND 3, the whole-arm reading of `test_at_a_fixed_tariff_minting_
    costs_strictly_more`. ONE round, deliberately: at round 0 the two arms
    hold identical content and differ only in that A2b minted, so the charge
    difference is exactly the tariff on the minted acts and nothing else.

    IT IS READ AT ROUND 0 AND NOT CUMULATIVELY, because cumulative charge is
    NOT monotone in activity and asserting that it were would be false --
    measured directly at 10 rounds: A2b pays more per round, so it starves
    SOONER, and a community that dies in round 4 accrues less total charge
    than one that limps to round 10. That is the tariff biting, not failing
    to. The per-round bite is the claim, and it is the claim that was
    unavailable under the retired price."""
    tariff = 0.25
    a2b = play("A2b", seed=1, rounds=1, source=Source(1.0, 1.0, tariff))
    a2a = play("A2a", seed=1, rounds=1, source=Source(1.0, 1.0, tariff))
    # A2a mints nothing at all; A2b mints and pays for it.
    assert a2b.acts_minted > 0
    assert a2a.acts_minted == 0
    assert sum(a2b.charges_by_unit.values()) > sum(a2a.charges_by_unit.values())
    # The gap IS the minted acts at the standing price, to the last unit.
    assert (sum(a2b.charges_by_unit.values())
            - sum(a2a.charges_by_unit.values())) == pytest.approx(
                tariff * a2b.acts_minted)


def test_calibrate_returns_both_measured_prices():
    """E0 is MEASURED -- the charge a median unit accrues through t*, the median
    round at which a unit's ledger first records a hit (spec 4; fix round 1:
    first HIT, not first law -- holding a law earns nothing, only a hit
    earns, so t* must mark the time to first earning).

    FIX ROUND 3: `calibrate` now returns a whole `Source`, not a bare float,
    because there are two measured numbers and a caller needs both. `tariff`
    is the flat price per unit of demand at which the baseline community
    breaks even over its own run; it must be measured, positive, and carried
    on the returned source rather than left at the unpriced default."""
    source = calibrate([1, 2], rounds=25)
    assert isinstance(source, Source)
    assert source.entry_price > 0.0
    assert source.tariff > 0.0
    assert source.pool_per_round == 1.0


def test_two_runs_of_one_arm_agree():
    """The determinism canary. FIX ROUND 3: at a nonzero tariff, so the
    `charges_by_unit` comparison is between real charges rather than between
    two dictionaries of zeros."""
    a = play("A1", seed=7, rounds=10, source=Source(1.0, 0.05, 0.05))
    b = play("A1", seed=7, rounds=10, source=Source(1.0, 0.05, 0.05))
    assert (a.survivors, a.born, a.died) == (b.survivors, b.born, b.died)
    assert a.charges_by_unit == b.charges_by_unit


def test_the_calibrated_world_is_viable():
    """Fix round 1: a calibration that endows a community too poorly to
    survive its own learning period has not calibrated anything. This tests
    the CALIBRATION itself, not the underlying experimental finding -- at the
    E0 `calibrate` actually returns, a real priced arm must survive past its
    founding cohort's learning period with both births and deaths occurring,
    not go extinct before anyone could earn a thing.

    A small seed set keeps this quick: calibration alone (2 seeds, 25 rounds)
    plus one 40-round play is a few seconds, not minutes.

    FIX ROUND 3: the calibrated `Source` is played AS RETURNED, carrying both
    measured prices. Rebuilding it as `Source(1.0, e0)` would silently drop
    the measured tariff back to the unpriced default and play an arm in which
    nothing is ever subtracted -- a viability check that could not fail.

    FIX ROUND 5 (the final review): DEATHS ARE NOW ASSERTED. The docstring
    promised "with both births and deaths occurring" and the body checked only
    births, so a calibration that priced the world into total safety -- every
    founder immortal, nothing ever running out -- would have passed a test
    named for viability while quietly refuting `P-D1`. A world where nobody
    dies is not a viable priced world; it is an unpriced one."""
    source = calibrate([1, 2], rounds=25)
    assert source.tariff > 0.0, "an unpriced world cannot test viability"
    result = play("A1", seed=1, rounds=40, source=source)
    assert result.survivors > 0
    assert result.born > 0
    assert result.died > 0, (
        "nobody ran out in 40 rounds at the calibrated price: the world has "
        "no teeth, and P-D1's mortality would be reading an unpriced arm"
    )


def test_first_hit_is_never_earlier_than_first_law():
    """A unit cannot hit on a law it has not yet induced. Checked on the
    MEDIANS, not per unit: a unit may hit off a law it induced earlier than
    the first PLANTED one (any correctly-shaped body->head pair the field
    happens to satisfy counts as a hit), so a per-unit ordering is not
    guaranteed even though the aggregate trend is."""
    result = play("A0", seed=1, rounds=25, source=Source(1.0, 0.0))
    assert result.first_hit_round, "A0 at 25 rounds must produce some hits"
    assert result.first_law_round, "A0 at 25 rounds must induce some laws"
    assert (statistics.median(result.first_hit_round.values())
            >= statistics.median(result.first_law_round.values()))


# ---------------------------------------------------------------------------
# THE GUARDS (spec section 10). These test the DESIGN, not a behaviour: each
# one fails loudly if a future change quietly reinstalls what this design
# deliberately refused. `ast`, `Unit` and `SRC` are imported at the top of
# this file.
# ---------------------------------------------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src"


def test_no_die_no_ttl_no_lifespan_in_the_d_world():
    """P-D1 is worthless if something installs mortality. Death must be
    `reserve <= 0` and nothing else (spec ruling 1).

    THE GUARD READS THE CODE, NOT THE PROSE. A regex over the file text would
    fire on the module docstring, which names `die()`, TTL and lifespan
    precisely to say they are absent -- and a guard that punishes a design for
    documenting its own refusals teaches the next author to stop documenting
    them. Walking the AST for IDENTIFIERS asks the question actually worth
    asking: does any name in this module install mortality?

    THE GAP THAT MATTERED WAS NOT THE ONE THIS DOCSTRING NAMED (fix round 5,
    the final review). The previous version matched EXACTLY and did not strip
    a leading underscore, unlike its sibling `test_the_world_holds_no_chooser`
    which had already been widened. Verified by injection, all three of these
    passed the old guard clean: `def _die(...)`, `def _ttl_expired(...)`,
    `def reap_by_age(...)`. A fully installed TTL sailed through the guard on
    which `P-D1`'s entire credibility rests, and the docstring meanwhile
    advertised a much narrower hole. Matching is now SUBSTRING over the
    underscore-stripped, lower-cased name, and each of those three fails.

    THE GAPS THAT REMAIN, named honestly. (i) `ast.keyword` -- a call-site
    keyword argument's name, as in `dict(expires=True)` -- is a distinct node
    type from `ast.arg` (a *parameter* name in a `def`) and is still not
    walked, so a banned name used only as a call-site keyword passes. (ii) The
    banned list is a list of synonyms and can never be the concept: mortality
    installed under `sunset`, `reap_at`, `cull` or `retire` is invisible here.
    (iii) The guard reads `d_world.py` and nothing else, so mortality
    installed in the DRIVER (`tools/run_d1.py`) is out of its reach entirely.
    As with the chooser guard, THE REAL GUARANTEE IS REVIEW; this catches the
    cheapest way of writing the refused thing, and one underscore used to be
    enough to defeat it.

    MATCHING IS PER IDENTIFIER SEGMENT, NOT OVER THE RAW STRING, and the
    reason is measured rather than aesthetic: a flat substring test fires on
    `_settle_population`, because `se-TTL-e` contains `ttl`. A guard that
    accuses this module's own population routine of installing a TTL is a
    guard the next author disables. So the name is split on underscores and
    at camelCase boundaries and each SEGMENT is matched by equality or by
    prefix -- which still catches every injection the old exact test let
    through (`_die`, `_ttl_expired`, `reap_by_age`) while leaving `settle`
    alone. It remains blunt at the segment level and will fire on an innocent
    `age` or `expires`; that is the right trade, since a false alarm costs one
    reading and a missed TTL costs `P-D1`."""
    tree = ast.parse((SRC / "d_world.py").read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    banned = ("die", "ttl", "lifespan", "maxage", "age", "expire")
    recorded = {"died"}
    """WHAT THE WORLD MAY STILL SAY, AND THE EXEMPTION IS THE WHOLE IDENTIFIER
    (fix round 5, second pass). `RoundReport.died` is the world REPORTING who
    ran out -- an observation of a consequence, which is the whole point of
    `P-D1` and must remain sayable. A mechanism is a name the world CALLS
    (`_die`, `_ttl_expired`, `reap_by_age`); a report is a name it FILLS IN.
    Static analysis cannot tell those apart, so one name is allowed.

    THE FIRST VERSION OF THIS EXEMPTION FILTERED THE SEGMENT `died` OUT OF
    EVERY IDENTIFIER, and so re-opened the hole this guard had just been
    repaired to close: `def _died(unit_id)` and `def died_by_starvation(units)`
    both passed by injection, because the offending segment was stripped before
    the stems were tried. Its docstring meanwhile claimed the allowance was "by
    name and by name only" -- narrower than the behaviour, which is the exact
    pattern this round's review was convened to catch, reproduced by the repair
    itself. The check is now `raw in recorded`: the identifier must BE `died`,
    not merely contain it. `died` is the only name in `d_world.py` carrying that
    segment, so nothing legitimate is caught, and `_died`, `died_by_starvation`,
    `die`, `dies` and `dying` all fail."""

    def _segments(raw_name: str):
        spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", raw_name)
        return [s for s in spaced.lstrip("_").lower().split("_") if s]

    for raw in sorted(names):
        if raw in recorded:
            continue
        hit = [stem for stem in banned
               for seg in _segments(raw) if seg.startswith(stem)]
        assert not hit, (
            f"{raw!r} is spelled like {hit[0]!r} and installs the mortality "
            f"P-D1 predicts must EMERGE from running out (spec ruling 1)"
        )


_BASELINE_UNIT_FIELDS = {
    "_credited", "_doubts", "_published", "_spent", "_supplied_by",
    "adopted_at", "aperture", "attended", "corroborating_witnesses",
    "corroboration_window", "facts", "first_seen", "last_provenance",
    "laws", "ledger", "peers", "replication_window", "suspended", "unit_id",
}
"""Every field `Unit` declares, frozen at the moment this guard was written
(fix round 1). Not a claim that this set is somehow correct or minimal --
just the shape `Unit` had when the D-series guard was last looked at."""


def test_the_unit_never_gains_a_reserve():
    """The architecture enforces the ruling: a unit STORES no balance
    (spec 3.1, THE_KYTOS 1.3).

    WHAT THIS CHECKS IS STORAGE, NOT READING -- the older claim that "a unit
    cannot READ what it does not have" overstated it (fix round 5, the final
    review). This guard compares `dataclasses.fields(Unit)` against a frozen
    baseline: it can say a unit HOLDS no reserve field, and it says nothing
    whatever about reading. A method that reached out for the world's
    `Reserves` -- taking it as an argument, importing `d_world`, walking a
    board back to a balance -- would keep the field set untouched and pass
    here clean. Nothing does that today, and nothing in this file would
    notice if something did.

    STRUCTURAL, NOT A NAME ALLOWLIST (fix round 1, finding 1). The first
    version of this guard checked `hasattr` against five chosen names
    (`reserve`, `reserves`, `balance`, `wealth`, `budget`), and a reviewer
    defeated it completely by adding `_balance: float = 0.0` to `Unit` --
    the guard passed, undetected, because gaming a name allowlist only
    requires a name outside the list (`_balance`, `credits`, `funds`,
    `purse`, ...). A list of synonyms can never be the concept it stands in
    for. This version instead snapshots EVERY field `Unit` declares
    (`dataclasses.fields`) and compares it against `_BASELINE_UNIT_FIELDS`,
    frozen above: ANY new field fails the guard, not only one that happens
    to be spelled like a reserve.

    THIS DELIBERATELY FIRES ON INNOCENT ADDITIONS TOO -- a field with
    nothing to do with reserves will also trip it, and the assertion message
    says so rather than accusing the maintainer of having added a reserve,
    which the guard has no way to know. That is the cost of a guard that
    cannot be evaded by a naming choice, and it is the right trade for this
    particular refusal: the reserve living OUTSIDE the membrane, keyed by
    unit id in `d_world.Reserves`, is load-bearing for the whole design
    (THE_KYTOS section 1.3 -- an act's effect resides in resources, never in
    a private field beside the act). Failing here is not damning. It means:
    look at the new field, confirm by hand it is not a reserve the world
    should be holding instead, and then update `_BASELINE_UNIT_FIELDS`
    deliberately -- the same "ask a human, don't guess" shape as
    `test_c_unit_is_not_modified_by_this_series` already accepts for its own
    weak spot."""
    current = {f.name for f in dataclasses.fields(Unit)}
    added = current - _BASELINE_UNIT_FIELDS
    assert not added, (
        f"Unit gained field(s) {sorted(added)!r} since this guard's baseline "
        f"was frozen. This may be entirely innocent -- the guard cannot tell "
        f"-- but confirm by hand that none of them is a reserve a unit "
        f"should not be able to read (spec 3.1) before updating "
        f"_BASELINE_UNIT_FIELDS to include it."
    )


def test_c_unit_is_not_modified_by_this_series():
    """The whole design rests on the units being unchanged.

    WEAK BY CONSTRUCTION, AND KNOWINGLY SO. This reads `git log`, so it
    catches only a commit that touched `src/c_unit.py` AND labelled itself
    with the `D-1:` prefix -- a real edit committed under a different message
    (or squashed, or made outside this series' convention) sails through
    silently. It is a commit-message-convention check, not an edit detector;
    kept because the brief calls for it, not because it is a strong guard."""
    import subprocess
    changed = subprocess.run(
        ["git", "log", "--oneline", "-n", "50", "--", "src/c_unit.py"],
        capture_output=True, text=True,
        cwd=str(SRC.parent)).stdout
    assert "D-1:" not in changed, "no D-1 commit may touch src/c_unit.py"


def test_the_wrapper_is_inert_when_it_does_not_subtract():
    """ARM 0 changes nothing. This is a claim about the WRAPPER, not a claim to
    reproduce published C-series figures, which were measured on a different
    field, a different aperture scheme and an imposed stagger (spec 10).

    THE TARIFF MUST BE NONZERO, OR THIS PASSES FOR THE WRONG REASON. `Source`
    is now a three-field dataclass; the brief's own `Source(1.0, 0.0)` leaves
    `tariff` at its default of 0.0, and a zero tariff prices every act at
    zero regardless of whether `subtract=False` did anything at all -- the
    exact vacuity Task 6 found and repaired twice already. `tariff=0.25`
    makes the meter read something real, and the closing assertion pins that
    it did, so this guard cannot silently go vacuous again."""
    spec = wide_spec(seed=3)
    aps = apertures_for(spec, 3, scheme=PAIRS)

    bare = [Unit(a.unit_id, a) for a in aps]
    for r in range(15):
        for u in bare:
            u.step(Field(spec), r, induce=True)

    wrapped = [Unit(a.unit_id, a) for a in aps]
    world = PricedWorld(Source(1.0, 0.0, 0.25), seats_from(spec), MarkBoard(),
                        subtract=False)
    for u in wrapped:
        world.admit(u)
        world.reserves.seed(u.unit_id, 1.0)
    units = wrapped
    last_report = None
    for r in range(15):
        for u in units:
            u.step(Field(spec), r, induce=True)
        last_report = world.settle(units, r)
        units = list(last_report.units)

    assert [u.unit_id for u in units] == [u.unit_id for u in bare]
    for a, b in zip(sorted(units, key=lambda u: u.unit_id),
                    sorted(bare, key=lambda u: u.unit_id)):
        assert a.facts == b.facts
        assert a.laws == b.laws
        assert a.ledger.hits == b.ledger.hits
        assert a.ledger.misses == b.ledger.misses

    # THE METER MUST BE NON-TRIVIAL: if the tariff had reverted to 0.0 (or
    # `subtract=False` had been bypassed some other way) this closing check,
    # not the identical-trajectory checks above, is what would catch it.
    assert sum(last_report.charges.values()) > 0, \
        "the meter never read anything -- the trajectory match above would " \
        "hold even if subtract=False were broken"
    for uid in world.reserves.living():
        assert world.reserves.balance(uid) == pytest.approx(1.0), \
            "a reserve moved even though subtract=False"


def test_the_world_holds_no_chooser():
    """Nothing in d_world may decide WHICH act a unit performs, skip one, or
    order them. The world charges and pays; it never selects.

    IT DOES NOT GOVERN THE ACT ORDER, AND THE ACT ORDER IS NOT IN THIS FILE.
    The rule deciding which act each unit performs, in what sequence, is the
    round loop in `tools/run_d1.py:play` -- outside this guard's reach
    entirely. What `d_world.py` must not acquire is a chooser of its own; that
    the DRIVER orders the round is not a violation but a fact the reader needs,
    because a guard named "the world holds no chooser" invites the inference
    that nothing anywhere chooses, and something does.

    THIS IS A NAMING TRAP, NOT A SEMANTIC CHOOSER DETECTOR -- SAY SO PLAINLY
    (fix round 1, finding 2). It asks only whether some function, parameter,
    assigned name, or attribute CONTAINS one of six stems (`choose`, `select`,
    `prioriti`, `decline`, `refuse_act`, `rank`, leading underscore stripped).
    MATCHING IS SUBSTRING, NOT PREFIX, AND PARAMETERS ARE SCANNED (fix round
    5, the final review): under the old `startswith` over def/Name/Attribute
    nodes only, all four of these passed clean by injection -- `def
    act_selector(self, acts, choose=None)` (both the name, which does not
    START with a stem, and the `choose` parameter, which is an `ast.arg` and
    was not walked), `unit_selector`, `de_select`, and `rank_acts`. All four
    now fail: `rank` was added on the review's suggestion after checking that
    no identifier in `d_world.py` contains it, so the widening costs no false
    positive. That closing four named holes required two passes, and that the
    list can only ever enumerate holes somebody named, is the paragraph below.

    A chooser written under any other name defeats it completely:
    a method named `pick`, a dict-based dispatch table for ordering assigned
    to a variable called `order_of` or `next_act`, a lambda bound to
    `handler` -- none contain a banned stem, so all pass silently, and no
    amount of widening the stem list closes that in general, because the
    list can only ever enumerate synonyms someone thought of. A detector
    that actually understood "this callable decides which act runs" is not
    achievable by static analysis over this module and was deliberately NOT
    attempted -- it would also misfire on innocent code (a `select` used for
    something unrelated, a `prioriti`-stemmed docstring reference), which is
    worse than a guard with a known, named gap. THE REAL GUARANTEE IS
    REVIEW, not this test -- the same posture `test_c_unit_is_not_modified_
    by_this_series` already takes toward its own weak spot: this guard
    catches the cheapest, most naive way of writing exactly the refused
    thing, and no more.

    WIDENED FROM DEF-ONLY TO NAME/ATTRIBUTE TARGETS (fix round 1): the prior
    version scanned only `FunctionDef`/`AsyncFunctionDef` names, so a lambda
    bound to a variable literally named `choose` (`choose = lambda acts:
    acts[0]`) passed clean -- confirmed by injection during review. Scanning
    `ast.Name`, `ast.Attribute` and (fix round 5) `ast.arg` nodes too closes
    those specific holes without pretending to understand what the assigned
    value does."""
    tree = ast.parse((SRC / "d_world.py").read_text())
    stems = ("choose", "select", "prioriti", "decline", "refuse_act", "rank")

    def _spelled_like_a_chooser(raw_name: str) -> bool:
        name = raw_name.lstrip("_").lower()
        return any(stem in name for stem in stems)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raw = node.name
        elif isinstance(node, ast.Name):
            raw = node.id
        elif isinstance(node, ast.Attribute):
            raw = node.attr
        elif isinstance(node, ast.arg):
            raw = node.arg
        else:
            continue
        assert not _spelled_like_a_chooser(raw), \
            f"{raw!r} is spelled like the chooser the design refuses"


def test_a_wider_field_moves_the_seat_ceiling_and_the_founding_population():
    """The escalation rule (spec section 8 item 6) needs the field's width to
    be an ARGUMENT, and it needs widening to move the two numbers the rule is
    about: the seat ceiling a population could run to, and the N0 the
    community starts at.

    Under PAIRS a field of k domains offers C(k, 2) apertures -- 28, 66, 120 at
    8, 12 and 16 -- and `units_for_witnesses` needs more founders to put three
    witnesses on every domain as the field widens. A `--domains` option that
    left either number where it was would let a re-measurement report the same
    binding ceiling under a different name, which is exactly the failure the
    escalation rule exists to catch."""
    from c_field import PAIRS, units_for_witnesses, wide_spec

    seen = {}
    for k, expected_ceiling in ((8, 28), (12, 66), (16, 120)):
        spec = wide_spec(seed=1, n_domains=k)
        assert seats_from(spec).free() == expected_ceiling
        result = play("A1", seed=1, rounds=2,
                      source=Source(1.0, 0.25, 0.05), n_domains=k)
        assert result.n_domains == k
        assert result.seat_ceiling == expected_ceiling
        assert result.n0 == units_for_witnesses(spec, 3, PAIRS)
        seen[k] = (result.seat_ceiling, result.n0)

    ceilings = [c for c, _ in seen.values()]
    founders = [n for _, n in seen.values()]
    assert ceilings == sorted(set(ceilings)), \
        "a wider field must offer strictly more seats"
    assert founders == sorted(set(founders)), \
        "a wider field must need strictly more founders to witness it"
    assert play("A1", seed=1, rounds=2,
                source=Source(1.0, 0.25, 0.05)).n_domains == 8, \
        "the default field is unchanged, so every prior figure still reads"


def test_calibration_is_re_measured_at_each_field_width():
    """No price carries across a widening. `calibrate` takes the same
    `n_domains` the arms will be played at, so tariff and E0 are measured in
    the world they will be charged in -- a price measured at 8 domains and
    applied at 16 would be a chosen number wearing a measurement's clothes."""
    narrow = calibrate([1], rounds=10, n_domains=8)
    wide = calibrate([1], rounds=10, n_domains=12)
    assert narrow.tariff > 0 and wide.tariff > 0
    assert narrow != wide, \
        "a different field must yield a different measured pair of prices"


def test_settling_credit_populates_peers_and_moves_no_dynamics():
    """The typify channel's other half, and the reason P-D4 reads the way it
    does.

    FOUND BY RUNNING THE MEASUREMENT (fix round 4). The driver's round order
    omitted `settle_credit`, which is `credit`'s only caller, so `Unit.peers`
    was EMPTY at every unit of every arm of every seed -- zero peer records,
    not zero positive ones -- and the prior about typification had no
    instrument rather than an inert one.

    TWO CLAIMS, AND THE SECOND IS THE FINDING. (1) With the step in place the
    community does accumulate peer records, so there is something to read.
    (2) Adding it moves NO survivor, birth, death, act or charge figure --
    because nothing in the round consults `peers`. `ask` publishes its
    question to the whole board and `adopt` takes `answer_to`, the first
    matching fact, whoever wrote it; `whom_to_ask` has no consumer. So the
    preference cannot reach an act, and the price cannot reach the
    preference."""
    source = Source(1.0, 0.08, 0.0004)
    result = play("A1", seed=1, rounds=25, source=source)

    records = sum(len(relations)
                  for u in result.final_units
                  for relations in u.peers.values())
    assert records > 0, \
        "settle_credit is credit's only caller: without it peers stays empty"

    # The same run with the credit step suppressed -- every other call in the
    # round is untouched, so any difference in the figures below would have to
    # come from `settle_credit` itself.
    import unittest.mock as _mock
    with _mock.patch.object(Unit, "settle_credit", lambda self, r: []):
        muted = play("A1", seed=1, rounds=25, source=source)
        assert sum(len(rel) for u in muted.final_units
                   for rel in u.peers.values()) == 0

    assert (result.survivors, result.born, result.died, result.acts_minted) == \
        (muted.survivors, muted.born, muted.died, muted.acts_minted), \
        "the typify channel is causally disconnected from the economy"
    assert result.total_charge == pytest.approx(muted.total_charge)
