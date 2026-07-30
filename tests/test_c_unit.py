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

    RE-MEASURED at this test's seed (7), 20 rounds, with a forecast resolving
    once at the round it is due: lawful 14 hits / 1 miss = 0.9333, net +13
    (3 late arrivals — atoms it missed that turned up afterwards and took no
    credit); misled 1 hit / 12 misses = 0.0769, net −11; lawless 0 bets,
    accuracy None, net 0."""
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
    assert ("p", "q") in u.induce(0, min_support=3)

    v = Unit("u1", ap)
    v.facts.update(_unary("p", ["y0", "y1"]))
    v.facts.update(_unary("q", ["y0", "y1"]))
    assert ("p", "q") not in v.induce(0, min_support=3)


def test_induction_tolerance_is_a_rate_not_a_count():
    """A large body set tolerates proportionally more pending cases; a small one
    does not. An absolute count would treat both alike — and, measured against a
    fact set that only ever grows, would silently tighten over a run.

    THE PENDING INDIVIDUALS ARE DATED HERE, and they have to be: since the
    open-world reading went in, an individual only counts against a law once its
    body has been held longer than the field's consequent lag. Undated bodies
    would be set aside as unknown and neither arm would refuse anything — which
    is `test_an_undated_pending_body_is_unknown_not_counter_evidence`, a
    different claim from this one."""
    _spec, _field, ap = _setup()
    big = Unit("u0", ap)
    big._record(_unary("p1", [f"x{i}" for i in range(100)]), 0)
    big._record(_unary("q1", [f"x{i}" for i in range(97)]), 1)     # 3 pending of 100
    assert ("p1", "q1") in big.induce(2, min_support=3, max_pending_rate=0.05)

    small = Unit("u1", ap)
    small._record(_unary("p1", [f"y{i}" for i in range(10)]), 0)
    small._record(_unary("q1", [f"y{i}" for i in range(7)]), 1)    # 3 pending of 10
    assert ("p1", "q1") not in small.induce(2, min_support=3,
                                            max_pending_rate=0.05)


def test_a_withheld_consequent_is_tolerated_only_in_proportion():
    """A consequent the field withheld leaves its individual pending forever, and
    once the lag has elapsed the unit cannot tell that from a genuine refutation.
    Such cases are tolerable in a large record and not in a small one — which is
    the point of a rate, and the reason the tolerance has to sit somewhere in
    relation to the field's withhold rate (see `MAX_PENDING_RATE`).

    RENAMED from `test_a_pending_antecedent_is_tolerated_only_in_proportion`,
    because the two cases it used to run together have come apart: an antecedent
    still awaiting its consequent is no longer TOLERATED by the rate, it is not
    counted at all (`test_a_body_delivered_within_the_lag_is_not_counter_evidence`)."""
    _spec, _field, ap = _setup()
    lagging = Unit("u0", ap)
    lagging._record(_unary("p", [f"x{i}" for i in range(20)]), 0)
    lagging._record(_unary("q", [f"x{i}" for i in range(19)]), 1)   # x19 withheld
    assert ("p", "q") in lagging.induce(2, min_support=3, max_pending_rate=0.05)

    refuted = Unit("u1", ap)
    refuted._record(_unary("p", ["y0", "y1", "y2", "y3", "y4"]), 0)
    refuted._record(_unary("q", ["y0", "y1", "y2"]), 1)        # y3, y4 refute
    assert ("p", "q") not in refuted.induce(2, min_support=3,
                                            max_pending_rate=0.05)


# --- the open world: what could not have been observed is not counter-evidence


def test_a_body_delivered_within_the_lag_is_not_counter_evidence():
    """THE FIRST OF THE THREE ROUTES INTO THE PENDING SET, and the one that
    repairs itself. The field delivers a consequent `CONSEQUENT_LAG` rounds after
    its antecedent, so an individual whose body arrived this round HAS no head
    yet and cannot have one; reading it as a refutation charges the law for the
    passage of time.

    Twenty supporters and five bodies delivered at round 5. Asked at round 5 the
    five are unknown and the law stands; asked at round 6 the lag has elapsed,
    they are refuting, and 5 of 25 is 20% — past the tolerance."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("p1", [f"x{i}" for i in range(20)]), 0)
    u._record(_unary("q1", [f"x{i}" for i in range(20)]), 1)
    u._record(_unary("p1", [f"z{i}" for i in range(5)]), 5)
    assert u._meets_criterion(("p1", "q1"), 5)
    assert not u._meets_criterion(("p1", "q1"), 6)


def test_an_undated_pending_body_is_unknown_not_counter_evidence():
    """THE SAME PRINCIPLE `_body_precedes_head` ALREADY KEEPS: absent timing
    evidence is not counter-evidence. A fact placed directly, or adopted from a
    peer — which `adopt` deliberately does not date — leaves the unit unable to
    say whether the head has had time to arrive, so it says nothing either way.

    THE COST IS REAL AND IT IS NAMED: undated testimony can no longer refute a
    law. Adopted content still counts as SUPPORT (that reading needs no date),
    so the channel is now asymmetric — a peer can bear a law out and cannot
    weigh against it. See `test_adopted_facts_still_count_as_support` in
    tests/test_c_marks.py."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("p1", [f"x{i}" for i in range(20)]), 0)
    u._record(_unary("q1", [f"x{i}" for i in range(20)]), 1)
    u.facts.update(_unary("p1", [f"z{i}" for i in range(5)]))   # undated
    assert not any(f in u.first_seen for f in _unary("p1", ["z0"]))
    assert u._meets_criterion(("p1", "q1"), 99)


def test_an_unknown_individual_leaves_the_denominator_as_well():
    """AN ABSTENTION MUST NOT BE SILENTLY CONVERTED INTO A PASS. The rate is read
    over what was observed — `refuting / (refuting + confirmed)` — so setting an
    individual aside removes it from the numerator AND from the denominator.

    Three supporters, two elapsed refutations and fifty individuals whose bodies
    arrived this round: 2 of 5 observed is 40% and the law is refused. Padding
    the denominator with the fifty would read 2 of 55, under 4%, and admit it."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("p1", ["x0", "x1", "x2"]), 0)
    u._record(_unary("q1", ["x0", "x1", "x2"]), 1)
    u._record(_unary("p1", ["y0", "y1"]), 2)                # elapsed: refuting
    u._record(_unary("p1", [f"z{i}" for i in range(50)]), 9)  # this round: unknown
    confirmed, refuting, unknown = u._pending_split("p1", "q1", 9)
    assert (len(confirmed), len(refuting), len(unknown)) == (3, 2, 50)
    assert not u._meets_criterion(("p1", "q1"), 9)


def test_the_tolerance_still_depends_on_a_withhold_rate_no_unit_can_observe():
    """THE MEASUREMENT THAT DECIDED NOT TO MOVE `MAX_PENDING_RATE`, pinned so it
    cannot drift out of the docstring that quotes it.

    Setting aside what could not have been observed removes the LAG's
    contribution to the pending set; it cannot remove a consequent the field
    withheld outright, which after the lag looks exactly like a refutation. So
    the tolerance still has to cover the withhold rate, and the criterion's grip
    on a true law slackens as that rate rises.

    One unit absorbing the field, fourteen seeds, 60 rounds, asked at every round
    from 10 to 59 about the two laws its aperture's domains actually carry: at
    withhold 0.00 the law meets its own criterion at 100.0% of rounds, at 0.10 at
    52.8%, at 0.20 at 18.2% — the 0.05 tolerance unchanged throughout. The
    converses read 0.0% at all three, refused by precedence rather than by the
    rate.

    A UNIT CANNOT OBSERVE ITS FIELD'S WITHHOLD RATE, so this is a dependence on a
    quantity outside the membrane. It is reported rather than tuned away: raising
    the tolerance repairs nothing the loop still suffers from (the open-world
    reading already took permanent true-law loss to zero) and admits accidental
    `x -> shared` laws that 0.05 refuses."""
    from dataclasses import replace
    seeds = [1, 2, 3, 4, 5, 7, 42, 99, 555, 808, 2026, 12345, 20260728, 31337]
    reading = {}
    for withhold in (0.0, 0.10, 0.20):
        true_pass = true_n = conv_pass = conv_n = 0
        for seed in seeds:
            spec = replace(default_spec(seed=seed), withhold_rate=withhold)
            field = Field(spec)
            ap = apertures_for(spec, n_units=4)[0]
            planted = [field.domain(n).law for n in ap.domains]
            u = Unit("u0", ap)
            for r in range(60):
                u.absorb(field, r)
                if r < 10:
                    continue
                for body, head in planted:
                    true_n += 1
                    true_pass += u._meets_criterion((body, head), r)
                    conv_n += 1
                    conv_pass += u._meets_criterion((head, body), r)
        reading[withhold] = (true_pass / true_n, conv_pass / conv_n)
    assert [round(reading[w][0], 3) for w in (0.0, 0.10, 0.20)] == [
        1.0, 0.528, 0.182]
    assert [reading[w][1] for w in (0.0, 0.10, 0.20)] == [0.0, 0.0, 0.0]


def test_a_law_with_nothing_observed_either_way_is_stopped_by_support():
    """When the denominator is zero the rate abstains and passes, and
    `min_support` is what still stops a law with no evidence. It has to be:
    otherwise a law about individuals nobody has observed would pass the
    tolerance vacuously."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0", "x1", "x2"]))        # undated bodies only
    confirmed, refuting, unknown = u._pending_split("p1", "q1", 9)
    assert (len(confirmed), len(refuting), len(unknown)) == (0, 0, 3)
    assert not u._meets_criterion(("p1", "q1"), 9)
    assert ("p1", "q1") not in u.induce(9)


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
    found = u.induce(2, min_support=3, max_pending_rate=0.05)
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
    assert ("p1", "q1") in u.induce(3, min_support=3, max_pending_rate=0.05)


def test_precedence_refuses_when_the_head_leads_by_a_majority():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("q1", [f"x{i}" for i in range(20)]), 0)   # heads lead 20-0
    u._record(_unary("p1", [f"x{i}" for i in range(20)]), 1)
    assert ("p1", "q1") not in u.induce(2, min_support=3, max_pending_rate=0.05)


def test_a_tie_counts_as_precedence_rather_than_against_it():
    """Two facts first held in the same round say nothing against either
    direction, so the test is `<=` and a tie does not refuse."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u._record(_unary("p1", [f"x{i}" for i in range(20)])
              | _unary("q1", [f"x{i}" for i in range(20)]), 0)
    assert ("p1", "q1") in u.induce(1, min_support=3, max_pending_rate=0.05)


def test_absent_timing_evidence_is_not_counter_evidence():
    """Facts placed directly rather than absorbed carry no first-arrival. The
    precedence test then abstains and passes, rather than silently refusing
    every law a unit could ever propose."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p", [f"x{i}" for i in range(20)]))
    u.facts.update(_unary("q", [f"x{i}" for i in range(20)]))
    assert not u.first_seen
    assert ("p", "q") in u.induce(9, min_support=3, max_pending_rate=0.05)


def test_the_learner_induces_only_planted_laws_across_many_seeds():
    """MEASURED, and the honest half of this task's result.

    With direction from precedence the learner's induction is exact on this
    field: at all fourteen seeds it holds AT LEAST ONE planted law, NO converse,
    and NO law that was not planted. Before precedence it induced each planted
    law's converse alongside it at every seed.

    Exactness of induction and PROFITABILITY are separate claims, measured
    separately: this test asserts only the former. The latter is
    `test_inducing_unit_learns_the_planted_law_and_its_score_rises` (a positive
    `net_score` at all 14 seeds, now that a forecast resolves once) and
    `test_every_miss_is_a_distinct_atom_no_bet_is_charged_twice` (why it used
    not to be)."""
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


def test_every_miss_is_a_distinct_atom_no_bet_is_charged_twice():
    """THE FIX TO THE SCORING CONTRACT, pinned at the seed that measured the
    defect — and pinned as a COUNT of distinct atoms, so it cannot regress
    quietly.

    WHAT WAS WRONG. `anticipate` returned everything derivable-and-not-held and
    `MembraneLedger.score` charged a miss for each anticipated atom EVERY round,
    with no memory of having charged for it before, so a consequent the field
    withheld outright became a STANDING prediction re-charged for the rest of
    the run. At this very seed that was stark: 177 misses arising from just 8
    distinct atoms (169 of them, 95.5%, re-charges of a bet already lost;
    `a_head(a17)` alone missed 50 times), so misses grew with the SQUARE of the
    run length while hits grew linearly and lengthening the run made any true
    law look worse.

    WHAT IS TRUE NOW, measured at seed 3 over the same 60 rounds: 37 hits / 8
    misses, net +29, and the 8 misses are 8 DISTINCT atoms — zero re-charges.
    The 8 are unchanged; what changed is that each is charged once. 36 late
    arrivals record the price of that discipline (a missed atom that turned up
    after its due round takes no credit).

    The remaining assertions are the ones the old test made about the misses'
    provenance, retained: they are all head atoms a held law licensed and the
    field withheld, not a wrong law firing."""
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
        u.induce(r)
        for f in anticipated - arrived:
            missed[f] += 1

    assert not (u.laws - {d.law for d in spec.domains})   # clean laws
    # NO BET IS CHARGED TWICE: one miss per distinct atom, exactly.
    assert max(missed.values()) == 1, f"a bet was re-charged: {missed}"
    assert u.ledger.misses == len(missed)
    assert u.ledger.restaked == 0     # the unit never even re-offers a settled bet
    # And with the re-charges gone, a record holding only true laws PAYS.
    assert u.ledger.net_score > 0
    # Every miss is still a head atom the unit's law licensed but the field
    # withheld — not a wrong law firing.
    heads = {d.law[1] for d in spec.domains}
    assert all(rel in heads for rel, _ in missed)


def test_misses_no_longer_grow_with_the_run_length():
    """The quadratic is gone, and this is what proves it rather than asserting
    it: a single planted law held over a run four times as long takes only a
    handful more misses, because each proposition is staked once.

    MEASURED (seed 3, `a_local -> a_head` held alone): 20 rounds 14h/1m = +13;
    60 rounds 24h/4m = +20; 240 rounds 28h/5m = +23. Under the old contract the
    same arm's misses rose without bound with the run length."""
    from c_field import Field, default_spec, apertures_for
    spec = default_spec(seed=3)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]

    def misses_over(rounds):
        u = Unit("u0", ap, laws={spec.domains[0].law})
        for r in range(rounds):
            u.step(field, r)
        return u.ledger.misses, u.ledger.net_score

    short_m, short_net = misses_over(20)
    long_m, long_net = misses_over(80)
    assert long_m <= short_m + 5, "misses still scale with run length"
    assert short_net > 0 and long_net > 0
    assert long_net >= short_net, "a longer run made a true law look worse"


def test_inducing_unit_learns_the_planted_law_and_its_score_rises():
    """The Stage 1 gate: a unit that may induce ends up holding a law the
    regime actually planted, and outperforms both a unit that may not induce
    and a unit seeded with a law the field does not carry.

    THIS GATE NOW PASSES ON THE MERITS. It carried `xfail(strict=True)` while
    `MembraneLedger.score` re-charged a standing bet every round; with a
    forecast resolved once, at the round it is due, the clause that failed
    (`learner.net_score > fixed.net_score` — beating ABSTENTION) holds at all
    fourteen seeds. Nothing here was weakened to get there.

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

    RE-MEASURED at this test's seed (7), 60 rounds, under noise, with a forecast
    resolving once: learner 33 hits / 7 misses = 0.8250, net +26, holding exactly
    the two planted laws; misled 1 hit / 17 misses = 0.0556, net −16; fixed 0
    bets, accuracy None, net 0. The learner's margin over the rival is +42; over
    abstention, +26. (Both arms' absolute volumes fell, because a bet is now
    counted once rather than once per remaining round; the ORDERING is what the
    gate asserts, and it is now the same ordering at every seed.)"""
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


def test_a_settled_forecast_is_not_offered_again_even_though_the_law_licenses_it():
    """THE SEMANTIC CHOICE, pinned. The law still licenses `q1(x0)` after
    `q1(x0)` was staked and lost — the body is still held, the law is still
    held, the head is still not held — and the unit does NOT bet it again. The
    record's unit of account is the proposition, so a second stake would enter a
    second verdict on one claim, which is precisely how a withheld consequent
    used to become a perpetual miss.

    Note that `last_provenance` still carries the derivation: what the unit
    takes to be derivable is unchanged, and only the STAKE is spent."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.add(("p1", "q1"))
    q_x0 = ("q1", (("c", "x0"),))

    assert u.anticipate() == {q_x0}
    u.ledger.score({q_x0}, arrived=set(), round_idx=0)      # staked and lost
    assert u.ledger.misses == 1

    assert u.anticipate() == set(), "a settled claim was staked a second time"
    assert q_x0 in u.last_provenance    # still derivable, just no longer bet
    assert u.ledger.misses == 1         # and no second charge could arise


def test_a_forecast_that_hits_is_not_offered_again_either():
    """The symmetric half of the same choice — and here the reason is the older
    one: a fact that arrives is HELD, so it was never re-derivable-and-not-held.
    Both filters point the same way, which is why resolving once costs nothing
    on the winning side."""
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.add(("p1", "q1"))
    q_x0 = ("q1", (("c", "x0"),))
    u.ledger.score(u.anticipate(), arrived={q_x0}, round_idx=0)
    u._record({q_x0}, 0)
    assert u.ledger.hits == 1
    assert u.anticipate() == set()
    assert u.ledger.restaked == 0


def test_anticipation_is_deterministic_across_repeated_renderings():
    _spec, field, ap = _setup()
    u = Unit("u0", ap)
    u.laws.update({("a_local", "a_head"), ("a_head", "shared")})
    u.absorb(field, 0)
    first, first_prov = u.anticipate(), dict(u.last_provenance)
    assert (u.anticipate(), dict(u.last_provenance)) == (first, first_prov)
