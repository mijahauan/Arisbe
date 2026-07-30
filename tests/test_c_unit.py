# tests/test_c_unit.py
import pytest

from c_field import Field, default_spec, apertures_for
from c_unit import Unit
from egi_core_dau import RelationalGraphWithCuts


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


def test_induction_tolerance_is_a_rate_not_a_count():
    """A large body set tolerates proportionally more pending cases; a small one
    does not. An absolute count would treat both alike — and, measured against a
    fact set that only ever grows, would silently tighten over a run."""
    _spec, _field, ap = _setup()
    big = Unit("u0", ap)
    big.facts.update(_unary("p1", [f"x{i}" for i in range(100)]))
    big.facts.update(_unary("q1", [f"x{i}" for i in range(97)]))   # 3 pending of 100
    assert ("p1", "q1") in big.induce(min_support=3, max_pending_rate=0.05)

    small = Unit("u1", ap)
    small.facts.update(_unary("p1", [f"y{i}" for i in range(10)]))
    small.facts.update(_unary("q1", [f"y{i}" for i in range(7)]))  # 3 pending of 10
    assert ("p1", "q1") not in small.induce(min_support=3, max_pending_rate=0.05)


def test_a_pending_antecedent_is_tolerated_only_in_proportion():
    """The lag leaves the just-delivered antecedent awaiting its consequent, and
    noise leaves a withheld one pending forever. Both are tolerable in a large
    record and not in a small one — which is the point of a rate."""
    _spec, _field, ap = _setup()
    lagging = Unit("u0", ap)
    lagging.facts.update(_unary("p", [f"x{i}" for i in range(20)]))
    lagging.facts.update(_unary("q", [f"x{i}" for i in range(19)]))  # x19 pending
    assert ("p", "q") in lagging.induce(min_support=3, max_pending_rate=0.05)

    refuted = Unit("u1", ap)
    refuted.facts.update(_unary("p", ["y0", "y1", "y2", "y3", "y4"]))
    refuted.facts.update(_unary("q", ["y0", "y1", "y2"]))       # y3, y4 refute
    assert ("p", "q") not in refuted.induce(min_support=3, max_pending_rate=0.05)


# --- retraction: a law can now be given up, not merely outlived --------------


def test_retract_law_removes_it_and_reports_whether_it_was_held():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.laws.add(("p1", "q1"))
    assert u.retract_law(("p1", "q1")) is True
    assert ("p1", "q1") not in u.laws
    assert u.retract_law(("p1", "q1")) is False      # already gone


def test_a_retracted_law_stops_licensing_anticipations():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.add(("p1", "q1"))
    assert u.anticipate()
    u.retract_law(("p1", "q1"))
    assert u.anticipate() == set()


# --- direction: precedence tells a law from its converse ---------------------


def test_first_seen_records_the_first_arrival_and_never_revises_it():
    """A fact re-delivered later does not move its first arrival — the record is
    of when the unit came to hold it, not of the last time it was mentioned."""
    _spec, field, ap = _setup()
    u = Unit("u0", ap)
    u.absorb(field, 0)
    round_0 = dict(u.first_seen)
    assert round_0 and set(round_0.values()) == {0}
    for r in range(1, 6):
        u.absorb(field, r)
    for f, at in round_0.items():
        assert u.first_seen[f] == at            # unrevised
    assert set(u.first_seen) == u.facts         # every held fact is dated


def test_step_dates_facts_too_not_only_absorb():
    _spec, field, ap = _setup()
    u = Unit("u0", ap)
    u.step(field, 0)
    u.step(field, 1)
    assert set(u.first_seen) == u.facts
    assert min(u.first_seen.values()) == 0


def test_induction_admits_a_law_and_refuses_its_converse():
    """THE HEADLINE. Support and pending-tolerance are symmetric between a law
    and its converse — both are carried by exactly the same individuals — so a
    criterion built on them alone admits both. Precedence breaks the symmetry:
    the body arrived first, so only one direction is proposed."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    body = _unary("p1", [f"x{i}" for i in range(20)])
    head = _unary("q1", [f"x{i}" for i in range(20)])
    u._record(body, 0)          # bodies first ...
    u._record(head, 1)          # ... heads one round later, as the field lags
    found = u.induce(min_support=3, max_pending_rate=0.05)
    assert ("p1", "q1") in found, "the law the timing supports was not admitted"
    assert ("q1", "p1") not in found, "the CONVERSE was admitted — precedence failed"


def test_precedence_tolerates_a_minority_of_heads_arriving_first():
    """A spurious head has no antecedent to license it, so it can reach an
    individual before that individual's body ever arrives. Requiring precedence
    of EVERY supporting individual would let one such case veto a true law
    forever, so the criterion is a strict majority. Here 3 of 20 supporters have
    the head first — a 0.85 proportion, comfortably above the 0.5 cut."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("q1", ["x0", "x1", "x2"]), 0)          # spurious heads first
    u._record(_unary("p1", [f"x{i}" for i in range(20)]), 1)
    u._record(_unary("q1", [f"x{i}" for i in range(20)]), 2)
    assert ("p1", "q1") in u.induce(min_support=3, max_pending_rate=0.05)


def test_precedence_refuses_when_the_head_leads_by_a_majority():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("q1", [f"x{i}" for i in range(20)]), 0)   # heads lead 20-0
    u._record(_unary("p1", [f"x{i}" for i in range(20)]), 1)
    assert ("p1", "q1") not in u.induce(min_support=3, max_pending_rate=0.05)


def test_a_tie_counts_as_precedence_rather_than_against_it():
    """Two facts first held in the same round say nothing against either
    direction, so the test is `<=` and a tie does not refuse."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("p1", [f"x{i}" for i in range(20)])
              | _unary("q1", [f"x{i}" for i in range(20)]), 0)
    assert ("p1", "q1") in u.induce(min_support=3, max_pending_rate=0.05)


def test_absent_timing_evidence_is_not_counter_evidence():
    """Facts placed directly rather than absorbed carry no first-arrival. The
    precedence test then abstains and passes, rather than silently refusing
    every law a unit could ever propose."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p", [f"x{i}" for i in range(20)]))
    u.facts.update(_unary("q", [f"x{i}" for i in range(20)]))
    assert not u.first_seen
    assert ("p", "q") in u.induce(min_support=3, max_pending_rate=0.05)


def test_the_learner_induces_only_planted_laws_across_many_seeds():
    """MEASURED, and the honest half of this task's result.

    With direction from precedence the learner's induction is exact on this
    field: at all fourteen seeds it holds AT LEAST ONE planted law, NO converse,
    and NO law that was not planted. Before precedence it induced each planted
    law's converse alongside it at every seed.

    What this test deliberately does NOT assert is a positive `net_score` — see
    `test_the_learners_net_score_is_negative_because_a_stale_bet_is_recharged`,
    which measures why."""
    from c_field import Field, default_spec, apertures_for
    seeds = [1, 2, 3, 4, 5, 7, 42, 99, 555, 808, 2026, 12345, 20260728, 31337]
    for seed in seeds:
        spec = default_spec(seed=seed)
        field = Field(spec)
        ap = apertures_for(spec, n_units=4)[0]
        u = Unit("u0", ap)
        for r in range(60):
            u.step(field, r, induce=True)
        planted = {d.law for d in spec.domains}
        converses = {(h, b) for b, h in planted}
        assert u.laws & planted, f"seed {seed}: no planted law induced"
        assert not (u.laws & converses), f"seed {seed}: a converse was induced"
        assert not (u.laws - planted), f"seed {seed}: unplanted law {u.laws - planted}"


def test_the_learners_net_score_is_negative_because_a_stale_bet_is_recharged():
    """MEASURED FINDING, pinned so it cannot silently change — and NOT patched
    around here, because the cause lies outside this task's scope.

    After precedence the learner holds ONLY planted laws (see the test above),
    yet its `net_score` is negative at 9 of the same 14 seeds. The cause is not
    the induction criterion. It is that `anticipate` returns everything
    derivable-and-not-held, and `MembraneLedger.score` charges a miss for each
    anticipated atom EVERY round, with no memory of having charged for it
    before. So a consequent the field withholds outright becomes a STANDING
    prediction: the unit re-bets it every remaining round and is charged every
    time.

    At seed 3 that is stark: 177 misses arise from just 8 distinct atoms, so 169
    of the 177 (95.5%) are re-charges of a bet already lost. `a_head(a17)` alone
    is missed 50 times. Misses therefore grow with the SQUARE of the run length
    while hits grow linearly, so lengthening the run makes any true law look
    worse — which is a defect of the scoring contract, not of induction.

    Fixing it means either retiring a stale anticipation or scoring an atom once
    per bet rather than once per round; both live in `anticipate` /
    `MembraneLedger`, outside this task's two files, and the brief forbids
    tuning a rate to hide the number."""
    from collections import Counter
    from c_field import Field, default_spec, apertures_for
    spec = default_spec(seed=3)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    u = Unit("u0", ap)
    missed = Counter()
    for r in range(60):
        anticipated = u.anticipate()
        arrived = set(field.at(ap, r))
        u.ledger.score(anticipated, arrived, r)
        u._record(arrived, r)
        u.induce()
        for f in anticipated - arrived:
            missed[f] += 1

    assert u.ledger.net_score < 0                     # the bare fact
    assert not (u.laws - {d.law for d in spec.domains})   # ... with clean laws
    # The misses are overwhelmingly repeats of the same few standing bets.
    assert len(missed) <= 10
    repeats = u.ledger.misses - len(missed)
    assert repeats / u.ledger.misses > 0.9
    # And every one of them is a head atom the unit's law licensed but the
    # field withheld — not a wrong law firing.
    heads = {d.law[1] for d in spec.domains}
    assert all(rel in heads for rel, _ in missed)


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN FAILING — the twin of tests/test_c_stage_gates.py's Stage 1 gate; "
    "read that marker for the full diagnosis. In short: induction is now exact "
    "(only planted laws, at all 14 seeds) and the learner beats the betting "
    "rival at 14/14, but a withheld consequent becomes a standing bet that "
    "`MembraneLedger.score` re-charges every round, so net_score is negative at "
    "9/14 and loses to abstention. The fix belongs in "
    "`anticipate`/`MembraneLedger`, not in the induction criterion. "
    "strict=True so this fails loudly when that lands."))
def test_inducing_unit_learns_the_planted_law_and_its_score_rises():
    """The Stage 1 gate: a unit that may induce ends up holding a law the
    regime actually planted, and outperforms both a unit that may not induce
    and a unit seeded with a law the field does not carry.

    THIS GATE DOES NOT CURRENTLY PASS — see the `xfail` marker. The clause that
    fails is `learner.net_score > fixed.net_score`, i.e. beating ABSTENTION;
    beating the betting rival still holds at every seed.

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

    Measured at this test's seed (7), 60 rounds, UNDER NOISE: learner 38 hits /
    69 misses = 0.3551, net −31, holding exactly the two planted laws; misled
    9 hits / 501 misses = 0.0177, net −492; fixed 0 bets, accuracy None, net 0.
    The learner's margin over the rival is +461; over abstention it is −31."""
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
