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
    it has no accuracy at all and comparing against it only exercises the
    ledger's no-bet case (`accuracy is None`, `net_score == 0`); the misled arm
    holds a law the field does not carry, fires on atoms that really arrive,
    and so places genuine bets that genuinely lose. That is the falsifiable
    comparison: a law that does not hold should score badly, not merely
    abstain.

    The rival is `a_head -> shared`, the same one `tests/test_c_stage_gates.py`
    uses (the duplication between these files is deliberate; the divergence
    was not). It bets heavily and loses most of its bets: `shared` draws from
    the domain's own individuals, which include the ten-strong shared core, so
    `shared(a_i)` does arrive now and then and the rival can genuinely win —
    just far less often than it loses.

    Measured at this test's seed (7), 20 rounds: lawful 16 hits / 0 misses =
    1.0000, net +16; misled 4 hits / 110 misses = 0.0351, net −106; lawless
    0 bets, accuracy None, net 0."""
    spec, field, ap = _setup()
    lawful, lawless, misled = Unit("u0", ap), Unit("u1", ap), Unit("u2", ap)
    lawful.laws.add(spec.domains[0].law)
    # body = first domain's head relation (which really arrives), head =
    # `shared`, which also really arrives — so the rival can win, and
    # occasionally does (see the docstring's measured figures).
    misled.laws.add((spec.domains[0].law[1], "shared"))
    for r in range(20):
        lawful.step(field, r)
        lawless.step(field, r)
        misled.step(field, r)
    assert lawful.ledger.hits > 0
    assert lawless.ledger.hits == 0
    assert lawless.ledger.misses == 0        # it places no bet at all
    # The rival genuinely bets — the comparison has a losing side that plays.
    assert misled.ledger.hits + misled.ledger.misses > 0
    assert misled.ledger.misses > 0          # the wrong law bets and loses
    assert lawless.ledger.accuracy is None   # no bet placed, so no ratio
    assert lawful.ledger.net_score > misled.ledger.net_score


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

    Three arms. The `fixed` arm never induces, so it never bets and has NO
    accuracy at all (`None`, not 0.0 — an abstainer's ratio would be
    fabricated); comparing against it therefore uses `net_score`, and shows the
    learner beats total abstention. The `misled` arm holds a wrong law, fires
    on atoms that really arrive, and so places genuine bets that genuinely
    lose. That is the falsifiable comparison: were the induced laws worse than
    useless, the learner would bet and never win, and would NOT outscore an
    arm that does the same.

    The rival is `a_head -> shared`, matching `tests/test_c_stage_gates.py`'s
    Stage 1 gate (the duplication is deliberate; the divergence was not).
    `shared` draws from the domain's own individuals, which include the
    ten-strong shared core, so the rival does occasionally hit — it just loses
    far more often than it wins.

    Measured at this test's seed (7), 60 rounds: learner 61 hits / 0 misses =
    1.0000, net +61; misled 9 hits / 497 misses = 0.0178, net −488; fixed
    0 bets, accuracy None, net 0."""
    spec, field, ap = _setup()
    learner, fixed, misled = Unit("u0", ap), Unit("u1", ap), Unit("u2", ap)
    # body = first domain's head relation (which really arrives), head =
    # `shared`, which also really arrives — so the rival can win, and
    # occasionally does (see the docstring's measured figures).
    misled.laws.add((spec.domains[0].law[1], "shared"))
    for r in range(60):
        learner.step(field, r, induce=True)
        fixed.step(field, r, induce=False)
        misled.step(field, r, induce=False)
    planted = {d.law for d in spec.domains}
    assert learner.laws & planted, "no planted law was induced"
    assert learner.ledger.hits > 0           # it bets and sometimes wins
    # The rival genuinely bets — the comparison has a losing side that plays.
    assert misled.ledger.hits + misled.ledger.misses > 0
    assert misled.ledger.misses > 0          # the wrong law bets and loses
    assert fixed.ledger.accuracy is None     # it never bet; no ratio exists
    assert learner.ledger.net_score > fixed.ledger.net_score
    assert learner.ledger.net_score > misled.ledger.net_score


# --- the unit reasons through the project's real forward-chainer -------------

import pytest

from egi_core_dau import RelationalGraphWithCuts


def test_unit_renders_its_state_as_an_egi():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0", "x1"]))
    u.laws.add(("p1", "q1"))
    egi = u.as_egi()
    assert isinstance(egi, RelationalGraphWithCuts)
    names = {egi.get_relation_name(e.id) for e in egi.E}
    assert {"p1", "q1"} <= names          # the law's body and head both appear
    assert len(egi.Cut) >= 2               # a law is drawn as nested cuts


def test_an_empty_unit_renders_an_empty_egi_and_anticipates_nothing():
    """`parse_egif("")` is valid and yields the blank sheet, so rendering an
    empty unit is sane rather than an error waiting to happen."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    egi = u.as_egi()
    assert (len(egi.V), len(egi.E), len(egi.Cut)) == (0, 0, 0)
    assert u.anticipate() == set()
    assert u.last_provenance == {}


def test_as_egi_refuses_a_generic_individual_rather_than_faking_a_constant():
    """A generic line has no constant label; emitting its vertex id as one
    would silently misrepresent the unit's own content."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.add(("p1", (("g", "v-17"),)))
    with pytest.raises(ValueError, match="non-constant individual"):
        u.as_egi()


def test_anticipation_comes_from_real_forward_chaining_with_provenance():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.add(("p1", "q1"))
    anticipated = u.anticipate()
    assert ("q1", (("c", "x0"),)) in anticipated
    # the derivation's support is now recoverable — provenance is no longer unused
    assert u.last_provenance
    assert u.last_provenance[("q1", (("c", "x0"),))] == frozenset({("p1", (("c", "x0"),))})


def test_forward_chaining_composes_laws_the_old_tuple_match_could_not():
    """The real materializer closes to the least Herbrand model, so a chain of
    held laws yields the chained consequence. The hand-rolled single-pass match
    this replaces stopped after one law and could never reach `r1`."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.update({("p1", "q1"), ("q1", "r1")})
    anticipated = u.anticipate()
    assert {("q1", (("c", "x0"),)), ("r1", (("c", "x0"),))} <= anticipated
    # and the intermediate step is what supports the far end
    assert u.last_provenance[("r1", (("c", "x0"),))] == frozenset(
        {("q1", (("c", "x0"),))})


def test_anticipation_is_deterministic_across_repeated_renderings():
    _spec, field, ap = _setup()
    u = Unit("u0", ap)
    u.laws.update({("a_local", "a_head"), ("a_head", "shared")})
    u.absorb(field, 0)
    first, first_prov = u.anticipate(), dict(u.last_provenance)
    assert (u.anticipate(), dict(u.last_provenance)) == (first, first_prov)
