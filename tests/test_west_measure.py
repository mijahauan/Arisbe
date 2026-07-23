from west_measure import (CountingMaterializer, read_quality, peel_proxy,
                          CostBreakdown, QualityReading, TracingMaterializer,
                          MemberCostReading, read_member_costs)
from agon_evolution import run, CorpusProposer


def test_counting_materializer_accumulates_per_round():
    cm = CountingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '~[ (swan *x) ~[ (white x) ] ]']
    res = run("", CorpusProposer(pool), rounds=6, uod_id="cm-test",
              name="cm", materializer=cm)
    assert len(cm.per_round_atoms) >= 1
    assert cm.total_atoms() == sum(cm.per_round_atoms)
    assert cm.total_atoms() >= 0


def test_read_quality_shape():
    pool = ['(bird "tweety")', '~[ (bird *x) ~[ (flies x) ] ]', '(bird "robin")']
    res = run("", CorpusProposer(pool), rounds=8, uod_id="q-test", name="q")
    q = read_quality(res)
    assert isinstance(q, QualityReading)
    assert q.final_m_size >= 0
    assert 0.0 <= q.k3_ratio <= 1.0
    assert q.k2_stick_rate is None or 0.0 <= q.k2_stick_rate <= 1.0


def test_cost_breakdown_total():
    cb = CostBreakdown(materialization_atoms=100, peel_proxy=20, coordinator_cost=5)
    assert cb.total() == 125


def test_tracing_materializer_records_one_relation_set_per_round():
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '(bird "robin")']
    run("", CorpusProposer(pool), rounds=5, uod_id="trace-test",
        name="trace", materializer=tm)
    assert len(tm.per_round_relations) == len(tm.per_round_atoms), (
        "one captured relation set per materialization call (== per round)"
    )
    assert all(isinstance(s, frozenset) for s in tm.per_round_relations)
    assert tm.total_atoms() == sum(tm.per_round_atoms)   # base behaviour intact


def test_tracing_materializer_sees_relations_appear_as_m_grows():
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")']
    run("", CorpusProposer(pool), rounds=6, uod_id="trace-grow",
        name="trace-grow", materializer=tm, ttl=None)
    # CorpusProposer exhausts after len(pool) rounds regardless of the
    # requested `rounds`, so this run captures 2 rounds, not 6.
    assert len(tm.per_round_relations) >= 2, (
        "need at least two captured rounds to observe growth"
    )
    union = set()
    for s in tm.per_round_relations:
        union |= s
    assert union, "some relation name must have entered M over the run"
    # Genuine growth check: each round's capture (taken *before* that round's
    # own revision lands, since materialize() is called on the pre-round
    # model) is a subset of the next, and the trajectory ends strictly larger
    # than it started — relation names accumulate as M grows in this fixture,
    # they do not vanish (no decay/relinquishment is in play: ttl=None and
    # both proposals are ground new_fact admissions, not laws).
    for prev, nxt in zip(tm.per_round_relations, tm.per_round_relations[1:]):
        assert prev <= nxt, "a relation name disappeared from M between rounds"
    assert tm.per_round_relations[-1] > tm.per_round_relations[0], (
        "the relation set must have strictly grown by the last captured round"
    )


def test_tracing_materializer_is_a_counting_materializer():
    assert issubclass(TracingMaterializer, CountingMaterializer)


def test_tracing_materializer_standing_proposal_breaks_1to1_alignment():
    """Pins the known limit documented on TracingMaterializer: when run() is
    given a standing_proposal, its loop calls _verdict_or_none() every round
    on top of the round's own peel() — a second materialize() call through
    the same shared materializer — so per_round_relations no longer aligns
    1:1 with rounds. This test exists to make that landmine regression-visible,
    not to endorse it as desired behaviour."""
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '(bird "robin")']
    res = run("", CorpusProposer(pool), rounds=5, uod_id="trace-standing",
              name="trace-standing", materializer=tm,
              standing_proposal='(bird *x)')
    rounds_run = len(res.outcomes)
    assert rounds_run == len(pool)   # CorpusProposer exhausts after len(pool)
    # One peel() for the round's own proposal + one for the standing-proposal
    # audit on every round => twice as many materialize() calls as rounds.
    assert len(tm.per_round_relations) == 2 * rounds_run
    assert len(tm.per_round_relations) > rounds_run, (
        "with standing_proposal set, per_round_relations does NOT align "
        "1:1 with rounds — see TracingMaterializer's docstring"
    )


def test_read_member_costs_excludes_the_trailing_journal_member():
    from west_measure import read_member_costs
    r = read_member_costs([4506, 4288, 120])      # the measured F=2 case
    assert r.folder_member_costs == [4506, 4288]
    assert r.journal_member_cost == 120
    assert r.cv < 0.05, "two folder-members within 2.5% must read as tight"


def test_the_journal_outlier_would_have_flipped_the_verdict():
    """Pins the defect this fix exists for: all-member CV crosses 0.5, folder-only does not."""
    from west_measure import read_member_costs
    costs = [4506, 4288, 120]
    mean_all = sum(costs) / len(costs)
    var_all = sum((c - mean_all) ** 2 for c in costs) / len(costs)
    cv_all = (var_all ** 0.5) / mean_all
    assert cv_all > 0.5                            # E1's statistic: "refuted"
    assert read_member_costs(costs).cv < 0.5       # E2's statistic: "held"


def test_read_member_costs_mean_is_over_folder_members_only():
    from west_measure import read_member_costs
    r = read_member_costs([100, 200, 3])
    assert r.mean == 150.0


def test_read_member_costs_handles_degenerate_inputs():
    from west_measure import read_member_costs
    empty = read_member_costs([])
    assert empty.folder_member_costs == [] and empty.journal_member_cost is None
    assert empty.cv == 0.0 and empty.mean == 0.0
    only_journal = read_member_costs([120])
    assert only_journal.folder_member_costs == []
    assert only_journal.journal_member_cost == 120
    assert only_journal.cv == 0.0


def test_read_member_costs_zero_mean_does_not_divide_by_zero():
    from west_measure import read_member_costs
    r = read_member_costs([0, 0, 0])
    assert r.cv == 0.0


def test_fit_power_law_recovers_a_known_exponent():
    from west_measure import fit_power_law
    sizes = [2, 4, 6, 8, 12, 16]
    costs = [3.0 * (s ** 1.8) for s in sizes]      # exact power law
    fit = fit_power_law(sizes, costs)
    assert abs(fit.beta - 1.8) < 1e-6
    assert fit.r_squared > 0.9999
    assert fit.n == 6 and fit.weak is False
    assert fit.stderr < 1e-6


def test_fit_power_law_recovers_a_linear_exponent():
    from west_measure import fit_power_law
    sizes = [2, 4, 6, 8, 12, 16]
    costs = [500.0 * s for s in sizes]
    fit = fit_power_law(sizes, costs)
    assert abs(fit.beta - 1.0) < 1e-6
    assert fit.weak is False


def test_fit_power_law_marks_too_few_points_weak():
    from west_measure import fit_power_law
    sizes = [2, 4, 8]
    costs = [3.0 * (s ** 1.8) for s in sizes]
    fit = fit_power_law(sizes, costs)
    assert fit.n == 3 and fit.weak is True, "fewer than six points is a weak fit"


def test_fit_power_law_marks_a_poor_fit_weak():
    from west_measure import fit_power_law
    sizes = [2, 4, 6, 8, 12, 16]
    costs = [10.0, 900.0, 30.0, 5000.0, 60.0, 12000.0]   # no power law here
    fit = fit_power_law(sizes, costs)
    assert fit.r_squared < 0.90 and fit.weak is True


def test_fit_power_law_refuses_nonpositive_and_mismatched_input():
    import pytest
    from west_measure import fit_power_law
    with pytest.raises(ValueError):
        fit_power_law([2, 4], [1.0])                 # length mismatch
    with pytest.raises(ValueError):
        fit_power_law([2, 0, 4], [1.0, 2.0, 3.0])    # log(0) undefined
    with pytest.raises(ValueError):
        fit_power_law([2, 4, 8], [1.0, -2.0, 3.0])   # log of a negative


def test_fit_power_law_is_weak_not_crashing_on_degenerate_sizes():
    from west_measure import fit_power_law
    fit = fit_power_law([4, 4, 4], [10.0, 20.0, 30.0])   # zero variance in x
    assert fit.weak is True and fit.beta == 0.0


def _manifest(folders, links):
    """A minimal VaultManifest for bucketing tests: folders = ("Folder-0",...),
    links = list of (src_folder, tgt_folder) pairs."""
    from vault_generator import VaultManifest, CrossLink
    cls = tuple(
        CrossLink(source_note="x", source_folder=s, target_note="y", target_folder=t)
        for s, t in links
    )
    return VaultManifest(folders=tuple(folders), notes=(), cross_links=cls, journal_len=0)


def test_round_robin_buckets_partitions_all_folders():
    from west_measure import round_robin_buckets
    folders = tuple(f"Folder-{k}" for k in range(12))
    buckets = round_robin_buckets(folders, 4)
    assert len(buckets) == 4
    assert all(len(b) == 3 for b in buckets)             # 12 / 4, balanced
    union = set().union(*buckets)
    assert union == set(folders)                          # every folder placed once
    assert sum(len(b) for b in buckets) == 12             # disjoint


def test_round_robin_n1_is_the_monolith_bucketing():
    from west_measure import round_robin_buckets
    folders = tuple(f"Folder-{k}" for k in range(12))
    buckets = round_robin_buckets(folders, 1)
    assert buckets == [frozenset(folders)]


def test_round_robin_is_deterministic():
    from west_measure import round_robin_buckets
    folders = tuple(f"Folder-{k}" for k in range(6))
    assert round_robin_buckets(folders, 3) == round_robin_buckets(folders, 3)


def test_link_aware_groups_heavily_linked_folders_together():
    from west_measure import link_aware_buckets, cut_link_count, round_robin_buckets
    folders = [f"Folder-{k}" for k in range(6)]
    # Two tight clusters {0,1,2} and {3,4,5}, each internally linked, no cross-cluster links.
    links = [("Folder-0","Folder-1"),("Folder-1","Folder-2"),("Folder-0","Folder-2"),
             ("Folder-3","Folder-4"),("Folder-4","Folder-5"),("Folder-3","Folder-5")]
    m = _manifest(folders, links)
    la = link_aware_buckets(m, 2)                          # cap 3 per bucket
    assert len(la) == 2 and all(len(b) == 3 for b in la)
    assert frozenset({"Folder-0","Folder-1","Folder-2"}) in la
    assert frozenset({"Folder-3","Folder-4","Folder-5"}) in la
    # link-aware cuts 0 of these links; round-robin (0,2,4 | 1,3,5) cuts 4 of
    # the 6 (Folder-0/Folder-2 and Folder-3/Folder-5 happen to land in the
    # same bucket under k mod n, so only those two escape the cut).
    assert cut_link_count(la, m) == 0
    assert cut_link_count(round_robin_buckets(folders, 2), m) == 4


def test_cut_link_count_counts_cross_bucket_links():
    from west_measure import cut_link_count
    folders = [f"Folder-{k}" for k in range(4)]
    m = _manifest(folders, [("Folder-0","Folder-1"), ("Folder-2","Folder-3")])
    same = [frozenset({"Folder-0","Folder-1"}), frozenset({"Folder-2","Folder-3"})]
    split = [frozenset({"Folder-0","Folder-2"}), frozenset({"Folder-1","Folder-3"})]
    assert cut_link_count(same, m) == 0
    assert cut_link_count(split, m) == 2


def test_link_aware_is_deterministic_and_partitions():
    from west_measure import link_aware_buckets
    folders = [f"Folder-{k}" for k in range(12)]
    links = [("Folder-0","Folder-1")] * 3 + [("Folder-6","Folder-7")] * 2
    m = _manifest(folders, links)
    a = link_aware_buckets(m, 4)
    b = link_aware_buckets(m, 4)
    assert a == b
    assert set().union(*a) == set(folders) and sum(len(x) for x in a) == 12


def test_read_ucurve_finds_an_interior_minimum():
    from west_measure import read_ucurve
    class P:
        def __init__(s, n, cn, ci): s.n, s.fed_cost_naive, s.fed_cost_incremental = n, cn, ci
    # naive: U-shaped with min at n=4; incremental: monotone down.
    pts = [P(1, 1000, 900), P(2, 600, 500), P(4, 400, 300),
           P(6, 700, 250), P(12, 1500, 200)]
    naive = read_ucurve(pts, "naive")
    assert naive.argmin_n == 4 and naive.interior is True
    assert naive.monotone_nonincreasing is False
    incr = read_ucurve(pts, "incremental")
    assert incr.argmin_n == 12 and incr.interior is False
    assert incr.monotone_nonincreasing is True


def test_read_ucurve_endpoint_minimum_is_not_interior():
    from west_measure import read_ucurve
    class P:
        def __init__(s, n, c): s.n, s.fed_cost_naive, s.fed_cost_incremental = n, c, c
    pts = [P(1, 100), P(2, 200), P(4, 300)]            # min at the left endpoint
    r = read_ucurve(pts, "naive")
    assert r.argmin_n == 1 and r.interior is False
