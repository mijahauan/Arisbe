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


def _world(entry_price=0.0, subtract=True, board=None):
    return PricedWorld(Source(1.0, entry_price),
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


def test_tau_is_determined_by_demand_not_set():
    """tau = E1 / demand. Nobody sets it; it is what clears the world's bounded
    supply against what the community actually did (spec ruling 7)."""
    world = _world()
    units = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.demand == 4.0
    assert report.tau == pytest.approx(0.25)


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
    charges E1 and pays nothing back, so the stock falls -- which is how a
    community comes to have a lifespan of its own doing (spec 3.3)."""
    world = _world()
    units = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 10.0)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert report.incomes == {}
    assert world.reserves.total() == pytest.approx(before - 1.0)


def test_the_world_is_conservative_whenever_anyone_hits():
    """Total charge equals total income to the last unit of account. The one
    place a rounding bug would silently create or destroy wealth (spec 10)."""
    world = _world()
    units = [_stub("u0", n_facts=3, n_laws=1, hits=2),
             _stub("u1", n_facts=7, hits=1),
             _stub("u2", n_facts=1, n_laws=4)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 10.0)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert sum(report.charges.values()) == pytest.approx(
        sum(report.incomes.values()))
    assert world.reserves.total() == pytest.approx(before)


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


def test_a_community_with_no_demand_has_no_price():
    """Nothing held and nothing said: tau would divide by zero, so it is None
    and nothing is charged. Named rather than crashed."""
    world = _world()
    units = [_stub("u0"), _stub("u1")]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.demand == 0.0
    assert report.tau is None
    assert report.charges == {}


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
    the remainder burned (spec 3.4)."""
    created = []
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 6.0)
    before = world.reserves.total()
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert len(report.born) == 1
    parent_id, child_id = report.born[0]
    assert parent_id == "u0"
    assert world.reserves.total() == pytest.approx(before)
    assert world.reserves.balance(parent_id) == pytest.approx(
        world.reserves.balance(child_id))
    assert world.reserves.balance(child_id) >= world.source.entry_price
    assert len(created) == 1 and created[0][0] == child_id


def test_a_newborn_takes_a_free_seat_and_inherits_nothing_but_the_board():
    """It arrives with no facts, no laws and no standing, and is socialized by
    marks it never made -- Berger and Luckmann's secondary socialization, and
    already built (spec 3.3)."""
    created = []
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, n_laws=2, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 8.0)
    report = world.settle([parent], 0, make_unit=_maker(created))
    child = [u for u in report.units if u.unit_id != "u0"][0]
    assert child.facts == set() and child.laws == set()
    _, aperture = created[0]
    assert aperture.unit_id == child.unit_id
    assert len(aperture.domains) == 2
    assert child.unit_id != parent.unit_id


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
    world = PricedWorld(Source(1.0, 1.0), Seats([("a", "b")]), MarkBoard())
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
    world = PricedWorld(Source(1.0, 1.0), Seats([("a", "b"), ("a", "c")]),
                        MarkBoard())
    rich = _stub("u0", n_facts=1, hits=1)
    poor = _stub("u1", n_facts=50)
    for u, amount in ((rich, 9.0), (poor, 0.01)):
        world.admit(u)
        world.reserves.seed(u.unit_id, amount)
    report = world.settle([rich, poor], 0, make_unit=_maker(created))
    assert report.died == ("u1",)
    assert len(report.born) == 1


def test_a_newborn_id_is_never_reused():
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
    assert len(seen) == len(created)


def test_conservation_holds_across_a_death():
    """Extraction is bounded by what a unit actually holds, so a dying unit
    lands at exactly 0.0 rather than in debt, and total wealth is conserved
    by construction -- no counter needed (author ruling, fix round 1)."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    before = world.reserves.total()
    world.settle(units, 0)
    assert world.reserves.total() == pytest.approx(before)


def test_a_balance_never_goes_below_zero():
    """u1's nominal charge (0.99) exceeds its balance (0.5); extraction is
    bounded, so it lands at exactly 0.0 -- dead, not in debt."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    world.settle(units, 0)
    assert world.reserves.balance("u1") == pytest.approx(0.0)
    assert not world.reserves.alive("u1")


def test_the_pot_is_short_when_someone_is_insolvent():
    """The world can only redistribute what it actually gathered: when u1
    cannot pay its full nominal charge, the pot falls short of the nominal
    total, and income is paid out of the pot, not the nominal pool."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    report = world.settle(units, 0)
    assert report.pot < sum(report.charges.values())
    assert sum(report.incomes.values()) == pytest.approx(report.pot)
