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

from c_field import (CYCLIC, PAIRS, Field, FieldSpec, apertures_for,
                     default_spec, units_for_witnesses, witnesses_per_domain)


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
    # And it names the way out, so a caller that needs more units is not left
    # to discover the second scheme by reading the source.
    assert PAIRS in msg and "6" in msg


def test_the_cyclic_scheme_did_not_move_when_a_second_one_was_added():
    """THE GUARD ON EVERY FIGURE MEASURED BEFORE TASK 5f. Adding the `PAIRS`
    scheme changed nothing about the default, and every measurement in this
    suite reads the default — so nothing moved silently. Asserted against the
    assignment written out by hand rather than against the implementation."""
    spec = default_spec(seed=7)
    aps = apertures_for(spec, n_units=4)
    assert [a.domains for a in aps] == [("alpha", "beta"), ("beta", "gamma"),
                                        ("gamma", "delta"), ("delta", "alpha")]
    assert [a.unit_id for a in aps] == ["u0", "u1", "u2", "u3"]
    assert apertures_for(spec, n_units=4, scheme=CYCLIC) == aps


def test_the_pairs_scheme_puts_three_witnesses_on_every_domain():
    """WHAT THE AUTHOR'S CORROBORATION RULING NEEDS FROM THE FIELD. Two
    independent witnesses, with the holder never one of them, means every domain
    must be met by at least three units. The cyclic scheme meets every domain
    exactly twice at any size; six units at distinct 2-domain apertures meet
    every one of the four domains exactly three times — the minimum, with
    nothing to spare."""
    spec = default_spec(seed=7)
    assert witnesses_per_domain(spec, apertures_for(spec, 4)) == {
        "alpha": 2, "beta": 2, "gamma": 2, "delta": 2}
    six = apertures_for(spec, 6, scheme=PAIRS)
    assert [a.domains for a in six] == [
        ("alpha", "beta"), ("alpha", "gamma"), ("alpha", "delta"),
        ("beta", "gamma"), ("beta", "delta"), ("gamma", "delta")]
    assert witnesses_per_domain(spec, six) == {
        "alpha": 3, "beta": 3, "gamma": 3, "delta": 3}
    # Pairwise distinct, so divergence by construction survives the wider
    # community, and the aperture WIDTH is unchanged: two domains, as before.
    assert len({a.domains for a in six}) == 6
    assert all(len(a.domains) == 2 for a in six)


def test_the_two_schemes_agree_on_unit_zero_and_diverge_after_it():
    """NOT INTERCHANGEABLE, AND SAID SO RATHER THAN ASSUMED. Every existing
    measurement that takes `apertures_for(...)[0]` reads the same slice under
    either scheme; anything reading a whole community does not. That is why the
    default was left alone."""
    spec = default_spec(seed=7)
    cyc = apertures_for(spec, 4)
    pair = apertures_for(spec, 4, scheme=PAIRS)
    assert cyc[0].domains == pair[0].domains
    assert [a.domains for a in cyc[1:]] != [a.domains for a in pair[1:]]
    # And the truncated pairs community is LOPSIDED — alpha reaches three
    # witnesses at four units while delta reaches one. This is what makes a
    # four-unit pairs arm a real control: it separates community size from
    # witnesses per domain.
    assert witnesses_per_domain(spec, pair) == {
        "alpha": 3, "beta": 2, "gamma": 2, "delta": 1}


def test_a_community_that_cannot_corroborate_is_refused_not_degraded():
    """REFUSE RATHER THAN DEGRADE. Handing back a community in which some domain
    has too few witnesses is handing back one where a doubt about that domain's
    laws can never be corroborated — the failure this task exists to remove. The
    message names the shortfall by domain and the size that would satisfy it."""
    spec = default_spec(seed=7)
    with pytest.raises(ValueError) as exc:
        apertures_for(spec, 4, scheme=PAIRS, min_witnesses=3)
    msg = str(exc.value)
    assert "'delta': 1" in msg and "'beta': 2" in msg
    assert "6 units would satisfy it" in msg
    # Under the cyclic scheme NO size satisfies it, and the message says that
    # rather than naming an unreachable number.
    with pytest.raises(ValueError) as exc:
        apertures_for(spec, 4, min_witnesses=3)
    assert "no community under scheme 'cyclic'" in str(exc.value)
    # The satisfying community is handed back without complaint.
    assert len(apertures_for(spec, 6, scheme=PAIRS, min_witnesses=3)) == 6


def test_units_for_witnesses_reads_the_community_it_would_build():
    """The size is DERIVED, not guessed: it is computed by building each prefix
    and reading it, so it cannot drift from what `apertures_for` hands back."""
    spec = default_spec(seed=7)
    assert units_for_witnesses(spec, 3) == 6
    assert units_for_witnesses(spec, 1) == 3        # delta arrives at unit 2
    assert units_for_witnesses(spec, 2, scheme=CYCLIC) == 4
    built = apertures_for(spec, units_for_witnesses(spec, 3), scheme=PAIRS)
    assert min(witnesses_per_domain(spec, built).values()) >= 3
    with pytest.raises(ValueError) as exc:
        units_for_witnesses(spec, 3, scheme=CYCLIC)
    assert "cannot witness every domain 3 times at any community size" in str(
        exc.value)


def test_an_unknown_scheme_is_refused():
    spec = default_spec(seed=7)
    with pytest.raises(ValueError) as exc:
        apertures_for(spec, 2, scheme="widest")
    assert "widest" in str(exc.value)


def test_the_pairs_scheme_is_deterministic_and_reads_no_set():
    """Order comes from the domains' DECLARED order through
    `itertools.combinations`, which preserves input order. Two calls agree
    exactly, and reversing the spec's domain order reverses the assignment
    rather than shuffling it — which is what shows the order is the input's and
    not a hash's."""
    spec = default_spec(seed=7)
    assert apertures_for(spec, 6, scheme=PAIRS) == apertures_for(
        spec, 6, scheme=PAIRS)
    flipped = FieldSpec(seed=spec.seed, domains=tuple(reversed(spec.domains)),
                        withhold_rate=spec.withhold_rate,
                        spurious_rate=spec.spurious_rate)
    assert [a.domains for a in apertures_for(flipped, 6, scheme=PAIRS)] == [
        ("delta", "gamma"), ("delta", "beta"), ("delta", "alpha"),
        ("gamma", "beta"), ("gamma", "alpha"), ("beta", "alpha")]
    # Whatever the order, the witness count is the same — the scheme's property
    # is structural, not an artifact of which domain was declared first.
    assert set(witnesses_per_domain(flipped,
                                   apertures_for(flipped, 6, scheme=PAIRS)
                                   ).values()) == {3}


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


def test_noise_withholds_some_consequents_and_adds_some_spurious():
    spec = default_spec(seed=20260728)
    assert spec.withhold_rate > 0 and spec.spurious_rate > 0
    field = Field(spec)
    d = spec.domains[0]
    body_rel, head_rel = d.law

    withheld = spurious = 0
    for r in range(1, 200):
        prev_bodies = {a for rel, a in field._antecedents(d.name, r - 1) if rel == body_rel}
        heads_now = {a for rel, a in field.deliver(d.name, r) if rel == head_rel}
        withheld += len(prev_bodies - heads_now)      # a consequence that did not arrive
        spurious += len(heads_now - prev_bodies)      # a consequent with no antecedent
    assert withheld > 0, "no consequent is ever withheld — the field is exception-free"
    assert spurious > 0, "no spurious consequent ever appears"


def test_noise_is_deterministic():
    a, b = Field(default_spec(seed=5)), Field(default_spec(seed=5))
    for r in range(30):
        assert a.deliver("alpha", r) == b.deliver("alpha", r)


def test_zero_rates_restore_the_exception_free_field():
    import dataclasses
    spec = dataclasses.replace(default_spec(seed=5), withhold_rate=0.0, spurious_rate=0.0)
    field = Field(spec)
    d = spec.domains[0]
    body_rel, head_rel = d.law
    for r in range(1, 60):
        prev = {a for rel, a in field._antecedents(d.name, r - 1) if rel == body_rel}
        now = {a for rel, a in field.deliver(d.name, r) if rel == head_rel}
        assert prev == now


# --- Examination VII: speaker-variance at the observer's membrane ------------
#
# The author ruled YES on giving the field speaker-variance (2026-07-30).
# Before it, `Field.deliver` drew noise from (seed, domain, round) and never
# from the unit, so every witness of a domain met byte-identical deliverances
# and no unit could be a more or less reliable speaker than any other. The
# examination's VII.4 recorded the consequence: alarm reliability, the
# credential, typification and P-H3 all measure a property of speakers, in a
# world whose speakers were interchangeable by construction.


def test_an_observer_with_no_entry_reads_exactly_the_domain_stream():
    """THE BACK-COMPAT GATE. Every C-series figure was measured through the
    two-argument call, and Examination VII cites those figures throughout, so
    the new argument must be inert until someone asks for it."""
    field = Field(default_spec(seed=5))
    for name in ("alpha", "beta", "gamma", "delta"):
        for r in range(40):
            assert field.deliver(name, r) == field.deliver(name, r, observer="u0")


def test_observer_noise_never_disturbs_the_domain_stream():
    """The field already keeps its noise on a separate RNG so that enabling it
    cannot shift the antecedent sequence. Observer noise gets the same
    discipline one level out: a spec that names observers must deliver the
    same domain stream as one that does not."""
    from c_field import ObserverNoise
    import dataclasses
    plain = Field(default_spec(seed=5))
    noisy = Field(dataclasses.replace(
        default_spec(seed=5),
        observers=(("u1", ObserverNoise(withhold=0.5, spurious=0.5)),)))
    for r in range(40):
        assert plain.deliver("alpha", r) == noisy.deliver("alpha", r)
        assert plain.deliver("alpha", r) == noisy.deliver("alpha", r, observer="u0")


def test_a_spurious_observer_perceives_what_the_field_never_delivered():
    """THE CRY-WOLF STRUCTURE, and the reason two rates exist rather than one.

    A unit with a high `withhold` is merely quieter — it sees less, and what it
    does see is true, so its testimony stays sound. A unit with a high
    `spurious` perceives atoms the field never delivered and publishes them in
    good faith, which is the boy's actual failure: not lying, but crying at
    a rate uncorrelated with the wolf (spec 11.2(c))."""
    from c_field import ObserverNoise
    import dataclasses
    spec = dataclasses.replace(
        default_spec(seed=5),
        observers=(("liar", ObserverNoise(spurious=0.9)),))
    field = Field(spec)
    invented = 0
    for r in range(60):
        truth = set(field.deliver("alpha", r))
        seen = set(field.deliver("alpha", r, observer="liar"))
        assert truth <= seen, "spurious noise must add, never remove"
        invented += len(seen - truth)
    assert invented > 20, f"a 0.9-spurious observer invented only {invented} atoms in 60 rounds"


def test_a_withholding_observer_sees_less_and_says_nothing_false():
    from c_field import ObserverNoise
    import dataclasses
    spec = dataclasses.replace(
        default_spec(seed=5),
        observers=(("quiet", ObserverNoise(withhold=0.8)),))
    field = Field(spec)
    missed = 0
    for r in range(60):
        truth = set(field.deliver("alpha", r))
        seen = set(field.deliver("alpha", r, observer="quiet"))
        assert seen <= truth, "withholding must remove, never add"
        missed += len(truth - seen)
    assert missed > 20, f"a 0.8-withhold observer missed only {missed} atoms in 60 rounds"


def test_two_observers_with_equal_rates_still_diverge():
    """The point of keying on the observer. Equal rates are equal DISPOSITIONS,
    not equal experience — otherwise 'unreliable' would be a property of the
    spec rather than of a speaker, and two units carrying the same rate could
    not be told apart by anything that watched them."""
    from c_field import ObserverNoise
    import dataclasses
    n = ObserverNoise(withhold=0.3, spurious=0.3)
    spec = dataclasses.replace(default_spec(seed=5), observers=(("u1", n), ("u2", n)))
    field = Field(spec)
    differ = sum(1 for r in range(60)
                 if field.deliver("alpha", r, observer="u1")
                 != field.deliver("alpha", r, observer="u2"))
    assert differ > 10, f"two equally-noisy observers differed on only {differ} of 60 rounds"


def test_observer_noise_is_deterministic():
    from c_field import ObserverNoise
    import dataclasses
    mk = lambda: Field(dataclasses.replace(
        default_spec(seed=5), observers=(("u1", ObserverNoise(0.3, 0.3)),)))
    a, b = mk(), mk()
    for r in range(40):
        assert a.deliver("alpha", r, observer="u1") == b.deliver("alpha", r, observer="u1")


def test_a_spurious_atom_is_a_head_atom_about_a_real_individual():
    """What a mis-observation may be. It must look like something the domain
    could have delivered, or a receiver could reject it on shape alone and the
    channel would carry a tell rather than a falsehood."""
    from c_field import ObserverNoise
    import dataclasses
    spec = dataclasses.replace(
        default_spec(seed=5), observers=(("liar", ObserverNoise(spurious=0.9)),))
    field = Field(spec)
    d = spec.domains[0]
    known = set(d.individuals)
    sayable = set(d.antecedents) | {d.law[1]}
    for r in range(60):
        for rel, args in (set(field.deliver("alpha", r, observer="liar"))
                          - set(field.deliver("alpha", r))):
            assert rel in sayable, f"invented relation {rel!r} is not one this domain speaks"
            assert args[0][1] in known, f"invented individual {args[0][1]!r} is unknown here"


# --- Examination VII: the twin control --------------------------------------
#
# Panel B held that the control deciding "emergent or seeded?" — two units with
# an identical aperture AND identical attendance parity — needs an explicit
# exemption to premise 3. The author's ruling 2 showed it needs none: premise 3
# exists to stop units converging on near-identical MODELS, which is a claim
# about content, while the twin control holds content and position fixed
# precisely in order to probe whether POLICY diverges. Different axes.


def test_twinning_is_refused_unless_it_is_asked_for():
    """Divergence by construction stays the default. A twin is a control arm,
    named at the call site, never something a caller gets by accident."""
    import pytest
    spec = default_spec()
    with pytest.raises(ValueError, match="cycles after"):
        apertures_for(spec, 5)


def test_a_twin_carries_its_original_aperture_exactly():
    spec = default_spec()
    aps = apertures_for(spec, 4, twin_of="u0")
    assert len(aps) == 5
    assert aps[4].domains == aps[0].domains
    assert aps[4].unit_id == "u4"
    assert [a.domains for a in aps[:4]] == [a.domains for a in apertures_for(spec, 4)]


def test_twinning_an_unknown_unit_is_refused_by_name():
    import pytest
    with pytest.raises(ValueError, match="u9"):
        apertures_for(default_spec(), 4, twin_of="u9")


def test_twinning_leaves_every_untwinned_call_untouched():
    """The back-compat gate for task 2. Every aperture figure in the series was
    measured without this argument."""
    spec = default_spec()
    for scheme in (CYCLIC, PAIRS):
        for n in range(1, 5):
            assert ([a.domains for a in apertures_for(spec, n, scheme=scheme)]
                    == [a.domains for a in
                        apertures_for(spec, n, scheme=scheme, twin_of=None)])


def test_the_twin_control_reads_zero_where_nothing_can_differ():
    """THE NULL P-H3's FIRST CLAUSE LACKS.

    Two units with the same aperture, the same attendance parity and no
    observer noise meet exactly the same world. Any later claim that policy
    "diverged through their own histories" has to beat this reading, and
    without it a divergence counted between units of DIFFERENT aperture or
    parity passes by arithmetic — which is what Examination VII's VII.9 found
    P-H1 doing."""
    spec = default_spec(seed=5)
    field = Field(spec)
    aps = apertures_for(spec, 4, twin_of="u0")
    a, twin = aps[0], aps[4]
    assert a.domains == twin.domains
    for r in range(0, 60, 2):                       # one shared attendance parity
        for name in a.domains:
            assert (field.deliver(name, r, observer=a.unit_id)
                    == field.deliver(name, r, observer=twin.unit_id))


def test_the_twin_control_reads_nonzero_once_the_field_names_a_speaker():
    """And the other half: with observer noise the twins' worlds come apart,
    so the control has a live range rather than only a floor. Without this the
    null would be indistinguishable from an instrument that cannot move."""
    from c_field import ObserverNoise
    import dataclasses
    spec = dataclasses.replace(
        default_spec(seed=5),
        observers=(("u4", ObserverNoise(withhold=0.3, spurious=0.3)),))
    field = Field(spec)
    aps = apertures_for(spec, 4, twin_of="u0")
    a, twin = aps[0], aps[4]
    differ = sum(1 for r in range(0, 60, 2) for name in a.domains
                 if field.deliver(name, r, observer=a.unit_id)
                 != field.deliver(name, r, observer=twin.unit_id))
    assert differ > 5, f"twins diverged on only {differ} attended domain-rounds"


def test_observer_noise_reaches_a_unit_through_its_aperture():
    """THE PLUMBING GATE. `Field.at` is the path a unit actually reads by, and
    it knows the observer already — an `Aperture` carries its `unit_id`. If
    `at` dropped that on the way to `deliver`, the whole speaker-variance
    change would be reachable only from tests: a mechanism built and not
    connected, which is the defect Examination V named as V.5 ("plumbing on
    unplumbed plumbing, recording what nothing consumes")."""
    from c_field import ObserverNoise
    import dataclasses
    spec = dataclasses.replace(
        default_spec(seed=5),
        observers=(("u0", ObserverNoise(spurious=0.9)),))
    field = Field(spec)
    aps = apertures_for(spec, 4)
    noisy, clean = aps[0], aps[1]
    assert noisy.unit_id == "u0"

    invented = sum(len(set(field.at(noisy, r))
                       - set().union(*(set(field.deliver(n, r)) for n in noisy.domains)))
                   for r in range(60))
    assert invented > 20, f"a 0.9-spurious unit met only {invented} invented atoms at its membrane"

    for r in range(60):
        plain = sorted(set().union(*(set(field.deliver(n, r)) for n in clean.domains)))
        assert field.at(clean, r) == plain, "an unnamed unit's membrane must be untouched"
