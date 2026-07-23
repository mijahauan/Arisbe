from pathlib import Path
from vault_generator import generate_vault
from west_experiment import (run_mono, run_fed, run_fed_broker, ArrangementResult,
                             assemble_report, ExperimentReport)


def test_run_mono_on_tiny_corpus(tmp_path):
    generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.15, journal_len=5)
    res = run_mono(tmp_path, rounds=30, ttl=120)
    assert isinstance(res, ArrangementResult)
    assert res.name == "MONO"
    assert res.cost.total() > 0
    assert res.quality.final_m_size >= 0
    assert res.member_costs == []          # MONO is a single kytos
    assert res.coverage is None            # MONO pays zero coherence tax


def test_run_mono_is_deterministic(tmp_path):
    generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.15, journal_len=5)
    a = run_mono(tmp_path, rounds=30, ttl=120)
    b = run_mono(tmp_path, rounds=30, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.quality.final_m_size == b.quality.final_m_size


def test_run_fed_on_tiny_corpus(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    res = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    assert res.name == "FED"
    assert res.cost.total() > 0
    assert res.cost.coordinator_cost > 0            # the coherence tax is real
    assert len(res.member_costs) == 3 + 1           # F folders + journal-member (A2)
    assert res.coverage is not None
    assert 0.0 <= res.coverage <= 1.0


def test_run_fed_is_deterministic(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    a = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    b = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.coverage == b.coverage


def test_run_fed_broker_drives_routes_and_costs_them(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    assert len(manifest.cross_links) > 0     # the fixture must actually exercise routing
    res = run_fed_broker(tmp_path, manifest, rounds=32, ttl=120)
    assert res.name == "FED-broker"
    assert res.routes == len(manifest.cross_links)
    assert res.routes > 0
    assert res.cost.coordinator_cost >= res.routes   # route count folded into the tax
    assert len(res.member_costs) == 3 + 1
    assert res.coverage is not None


def test_run_fed_broker_is_deterministic(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    a = run_fed_broker(tmp_path, manifest, rounds=32, ttl=120)
    b = run_fed_broker(tmp_path, manifest, rounds=32, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.coverage == b.coverage
    assert a.routes == b.routes


def test_assemble_report_and_priors(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=5,
                              cross_folder_link_prob=0.15, journal_len=6)
    mono = run_mono(tmp_path, rounds=40, ttl=120)
    fed = run_fed(tmp_path, manifest, rounds=40, ttl=120)
    rep = assemble_report(mono, fed, theta=0.20, tol=0.10)
    assert isinstance(rep, ExperimentReport)
    assert set(rep.priors) == {"P1", "P2", "P3", "P4"}
    # P1 is a direction check: FED total cost vs MONO total cost
    assert rep.priors["P1"] in ("held", "refuted")
    assert 0.0 <= rep.gap <= 1.0


def test_determinism_canary(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=5,
                              cross_folder_link_prob=0.15, journal_len=6)
    m1 = run_mono(tmp_path, rounds=40, ttl=120)
    m2 = run_mono(tmp_path, rounds=40, ttl=120)
    f1 = run_fed(tmp_path, manifest, rounds=40, ttl=120)
    f2 = run_fed(tmp_path, manifest, rounds=40, ttl=120)
    assert (m1.cost.total(), m1.quality.final_m_size) == (m2.cost.total(), m2.quality.final_m_size)
    assert (f1.cost.total(), f1.coverage) == (f2.cost.total(), f2.coverage)


def test_pair_comparisons_matches_the_real_naive_scan():
    """The closed form is earned: it must equal what Coordinator.consistency_scan
    actually counts for the same held set."""
    from west_experiment import _pair_comparisons
    from west_coordinator import Coordinator
    from egif_parser_dau import parse_egif
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b") (has_tag "a" "t")'))
    coord.ingest("F1", parse_egif('(links_to "c" "d") (in_folder "c" "F1")'))
    coord.consistency_scan()
    assert coord.scan_comparisons == _pair_comparisons(len(coord.held))


def test_incremental_comparisons_matches_the_real_incremental_scan():
    """Pinned across two scans so ``old > 0`` on the second one — otherwise
    deleting the ``new_count * old`` term from ``_incremental_comparisons``
    leaves this test passing (the first scan alone has ``old == 0``, so that
    term contributes nothing there)."""
    from west_experiment import _incremental_comparisons
    from west_coordinator import Coordinator
    from egif_parser_dau import parse_egif
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b") (has_tag "a" "t")'))
    first_new = set(coord._unscanned)
    expected = _incremental_comparisons(len(coord.held), len(first_new))
    coord.consistency_scan_incremental()
    assert coord.scan_comparisons_incremental == expected

    # Second ingest, different folder, at least one new relation name: this
    # scan has old > 0, so it genuinely exercises the new_count * old term.
    coord.ingest("F1", parse_egif('(links_to "c" "d") (in_folder "c" "F1")'))
    second_new = set(coord._unscanned)
    assert len(coord.held - second_new) > 0            # old > 0, for real
    expected += _incremental_comparisons(len(coord.held), len(second_new))
    coord.consistency_scan_incremental()
    assert coord.scan_comparisons_incremental == expected


def test_replay_incremental_equals_one_full_scan_of_the_final_held_set():
    """Arm I's whole-run invariant, at replay level."""
    from west_experiment import replay_coordinator_tax, _pair_comparisons
    traj = {
        "F0": [frozenset({"a"}), frozenset({"a", "b"}), frozenset({"a", "b"})],
        "F1": [frozenset({"a"}), frozenset({"a"}), frozenset({"a", "c"})],
    }
    tax = replay_coordinator_tax(traj)
    # held = {(F0,a),(F0,b),(F1,a),(F1,c)} => H = 4
    assert tax.cells_written == 4
    assert tax.incremental == _pair_comparisons(4)


def test_replay_naive_member_round_exceeds_global_round_by_the_member_factor():
    from west_experiment import replay_coordinator_tax
    traj = {
        "F0": [frozenset({"a"}), frozenset({"a", "b"})],
        "F1": [frozenset({"a"}), frozenset({"a", "c"})],
    }
    tax = replay_coordinator_tax(traj)
    assert tax.naive_member_round > tax.naive_global_round > 0
    assert tax.naive_global_round >= tax.incremental


def test_replay_naive_grows_with_rounds_but_incremental_does_not():
    """The bracket's whole point: extra quiet rounds cost Arm N and are free to Arm I."""
    from west_experiment import replay_coordinator_tax
    short = {"F0": [frozenset({"a", "b"})], "F1": [frozenset({"a"})]}
    long = {"F0": [frozenset({"a", "b"})] * 5, "F1": [frozenset({"a"})] * 5}
    t_short, t_long = replay_coordinator_tax(short), replay_coordinator_tax(long)
    assert t_long.naive_member_round > t_short.naive_member_round
    assert t_long.incremental == t_short.incremental
    assert t_long.cells_written == t_short.cells_written


def test_replay_is_empty_for_empty_trajectories():
    from west_experiment import replay_coordinator_tax
    tax = replay_coordinator_tax({})
    assert (tax.cells_written, tax.naive_member_round,
            tax.naive_global_round, tax.incremental) == (0, 0, 0, 0)


def test_replay_is_deterministic():
    from west_experiment import replay_coordinator_tax
    traj = {
        "F1": [frozenset({"b", "a"}), frozenset({"a", "b", "c"})],
        "F0": [frozenset({"a"}), frozenset({"a", "z"})],
    }
    a = replay_coordinator_tax(traj)
    b = replay_coordinator_tax(traj)
    assert a == b


def _tiny_vault(tmp_path):
    from vault_generator import generate_vault
    return generate_vault(tmp_path, seed=20260721, folders=2, notes_per_folder=4,
                          cross_folder_link_prob=0.15, journal_len=4)


def test_run_fed_traced_returns_a_tax_and_matches_run_fed_member_count(tmp_path):
    from west_experiment import run_fed_traced
    manifest = _tiny_vault(tmp_path)
    fed, tax = run_fed_traced(tmp_path, manifest, rounds=6, ttl=120)
    assert len(fed.member_costs) == 3          # F=2 folder-members + journal-member
    assert tax.cells_written > 0
    assert tax.incremental <= tax.naive_global_round <= tax.naive_member_round


def test_run_fed_traced_tax_exceeds_the_e1_snapshot_lower_bound(tmp_path):
    """A3 paid down: the per-round tax must be at least the end-of-run snapshot."""
    from west_experiment import run_fed, run_fed_traced
    manifest = _tiny_vault(tmp_path)
    e1 = run_fed(tmp_path, manifest, rounds=6, ttl=120)
    _fed, tax = run_fed_traced(tmp_path, manifest, rounds=6, ttl=120)
    # Arm N's final term is exactly C(H,2) — the same scan the end-of-run
    # snapshot performs — and cells_written matches the snapshot's. This is the
    # structurally guaranteed comparison; the bare comparison_count alone is
    # coincidentally sufficient only at certain round counts.
    assert tax.cells_written + tax.naive_member_round >= e1.cost.coordinator_cost


def test_run_e2_config_reports_both_arms_and_they_differ(tmp_path):
    from west_experiment import run_e2_config
    manifest = _tiny_vault(tmp_path)
    cfg = run_e2_config(tmp_path, manifest, folders=2, rounds=6, ttl=120)
    assert cfg.folders == 2 and cfg.rounds == 6
    assert cfg.mono.cost.total() > 0
    assert cfg.fed_cost_naive >= cfg.fed_cost_incremental
    assert cfg.member_reading.journal_member_cost is not None
    assert 0.0 <= cfg.gap <= 1.0


def test_run_e2_config_is_deterministic(tmp_path):
    from west_experiment import run_e2_config
    manifest = _tiny_vault(tmp_path)
    a = run_e2_config(tmp_path, manifest, folders=2, rounds=6, ttl=120)
    b = run_e2_config(tmp_path, manifest, folders=2, rounds=6, ttl=120)
    assert a.mono.cost.total() == b.mono.cost.total()
    assert a.fed_cost_naive == b.fed_cost_naive
    assert a.fed_cost_incremental == b.fed_cost_incremental


def test_e1_run_fed_is_unchanged_by_e2_additions(tmp_path):
    """E1 reproducibility guard."""
    from west_experiment import run_fed
    manifest = _tiny_vault(tmp_path)
    a = run_fed(tmp_path, manifest, rounds=6, ttl=120)
    b = run_fed(tmp_path, manifest, rounds=6, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.name == "FED"


def _fake_config(folders, mono_cost, fed_naive, fed_incr, cv=0.03, mean=1000.0,
                 gap=0.0, tax_naive=None):
    """A hand-built E2ConfigResult for verdict-logic tests — no vault run needed.

    ``tax_naive`` defaults to ``fed_naive`` (the two coincide in every ordinary
    test) but can be set independently to pin ``CoordinatorTax.naive_member_round``
    apart from ``fed_cost_naive`` — needed for the F6 clamp test, where the tax
    reading must go non-positive while the reported FED-naive cost stays
    positive (as `fit_power_law`'s positivity contract requires)."""
    from west_experiment import E2ConfigResult, CoordinatorTax, ArrangementResult
    from west_measure import CostBreakdown, QualityReading, MemberCostReading
    if tax_naive is None:
        tax_naive = fed_naive
    mono = ArrangementResult(
        name="MONO",
        cost=CostBreakdown(materialization_atoms=mono_cost, peel_proxy=0),
        quality=QualityReading(k2_stick_rate=1.0, k3_ratio=0.0, final_m_size=100))
    fed = ArrangementResult(
        name="FED",
        cost=CostBreakdown(materialization_atoms=fed_incr, peel_proxy=0),
        quality=QualityReading(k2_stick_rate=1.0, k3_ratio=0.0, final_m_size=100),
        member_costs=[1000, 1000, 120], coverage=1.0 - gap)
    return E2ConfigResult(
        folders=folders, rounds=25 * (folders + 1), ttl=120, mono=mono, fed=fed,
        tax=CoordinatorTax(cells_written=1, naive_member_round=tax_naive,
                           naive_global_round=fed_naive // 2, incremental=1),
        member_reading=MemberCostReading([1000, 1000], 120, mean, cv),
        fed_cost_naive=fed_naive, fed_cost_incremental=fed_incr, gap=gap)


SIZES = [2, 4, 6, 8, 12, 16]


def test_p1_holds_when_mono_scales_worse_than_fed():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert abs(rep.fit_mono.beta - 1.8) < 0.01
    assert abs(rep.fit_fed_incremental.beta - 1.0) < 0.01
    assert rep.priors["P1"] == "held"


def test_p1_refuted_when_mono_does_not_scale_worse():
    """The pre-committed refutation (beta_mono <= beta_fed_incremental) — the
    *only* condition Ruling B (2026-07-22) reserves "refuted" for."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f), int(50 * f ** 3),
                            int(500 * f ** 1.5)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.beta <= rep.fit_fed_incremental.beta
    assert rep.priors["P1"] == "refuted"


def test_p1_undetermined_on_a_weak_fit():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in [2, 4, 8]]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.weak is True
    assert rep.priors["P1"] == "undetermined"


def test_p1_undetermined_on_a_weak_fit_from_low_r_squared_not_few_points():
    """The n<6 path and the R²<0.90 path are independent branches of the same
    weak-fit rule (spec §4) — this exercises R²<0.90 alone, at the full n=6
    point count, so a mutant that only checks ``n < MIN_FIT_POINTS`` cannot
    hide behind "well there just weren't enough points"."""
    from west_experiment import assemble_e2_report
    noisy_mono = [10, 900, 30, 5000, 60, 12000]     # no power law here (n=6)
    configs = [_fake_config(f, mc, int(50 * f ** 3), int(500 * f))
              for f, mc in zip(SIZES, noisy_mono)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.n == 6
    assert rep.fit_mono.r_squared < 0.90
    assert rep.fit_mono.weak is True
    assert rep.priors["P1"] == "undetermined"


def test_p1_undetermined_when_only_fed_incremental_is_weak():
    """Pins P1's *second* weak-fit gate separately from the first: MONO fits
    cleanly here, only FED(I) is weak, and the verdict must still be
    "undetermined" — kills a mutant that drops ``fit_fed_incr.weak`` from the
    gate (which would compute a "refuted"/"held"/"separation-only" answer off
    a numerically meaningless noisy fit instead)."""
    from west_experiment import assemble_e2_report
    noisy_fed_incr = [10, 900, 30, 5000, 60, 12000]
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), fi)
              for f, fi in zip(SIZES, noisy_fed_incr)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.weak is False
    assert rep.fit_fed_incremental.weak is True
    assert rep.priors["P1"] == "undetermined"


def test_p1_held_just_above_the_1_3_beta_bar():
    """Boundary: beta_mono fitted just above 1.3, separation holds — "held"."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.31), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.beta > 1.3
    assert rep.fit_mono.beta > rep.fit_fed_incremental.beta
    assert rep.priors["P1"] == "held"


def test_p1_separation_only_just_below_the_1_3_beta_bar():
    """Boundary: beta_mono fitted just below 1.3, separation still holds — per
    Ruling B (2026-07-22) that is "separation-only", not "refuted" (the
    pre-committed refutation is beta_mono <= beta_fed_incremental, which does
    not hold here) and not "held" (the magnitude bar is missed)."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.29), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.beta < 1.3
    assert rep.fit_mono.beta > rep.fit_fed_incremental.beta
    assert rep.priors["P1"] == "separation-only"


def test_p2_holds_when_per_member_cost_is_flat_and_tight():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            cv=0.03, mean=1000.0) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "held"


def test_p2_refuted_when_a_single_config_has_loose_members():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            cv=0.03 if f != 8 else 0.7) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "refuted"


def test_p2_refuted_when_mean_per_member_cost_drifts_across_the_sweep():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            mean=1000.0 * f) for f in SIZES]   # 8x drift
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "refuted"


def test_p2_held_just_below_the_1_25_mean_ratio_bar():
    """Boundary: max/min per-folder-member mean ratio = 1.24, tight CV
    everywhere — held."""
    from west_experiment import assemble_e2_report
    means = [1000.0] * 5 + [1240.0]     # ratio exactly 1.24
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            cv=0.03, mean=m) for f, m in zip(SIZES, means)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "held"


def test_p2_refuted_just_above_the_1_25_mean_ratio_bar():
    """Boundary: max/min per-folder-member mean ratio = 1.26 — refuted. Kills
    a mutant that widens ``P2_MAX_MEAN_RATIO`` (e.g. to 5.0), which would read
    this same 1.26 drift as flat."""
    from west_experiment import assemble_e2_report
    means = [1000.0] * 5 + [1260.0]     # ratio exactly 1.26
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            cv=0.03, mean=m) for f, m in zip(SIZES, means)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "refuted"


def test_p2_undetermined_with_no_configs():
    """F4: P2² is a cross-size claim; zero configs must never read as a
    refutation from no data."""
    from west_experiment import assemble_e2_report
    rep = assemble_e2_report([], theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "undetermined"


def test_p2_undetermined_with_a_single_config():
    """F4: one config makes max/min == 1 trivially and CV meaningless as a
    cross-size flatness claim — must not read "held" on that technicality."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(4, int(100 * 4 ** 1.8), int(50 * 4 ** 3), int(500 * 4))]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P2"] == "undetermined"


def test_p3_holds_and_reports_an_observed_crossover():
    from west_experiment import assemble_e2_report
    # naive tax/cost ∝ F^3 starts BELOW mono ∝ F^1.8 at F=2 (240 < 348) and
    # overtakes it inside the swept range, first at F=4 (1920 > 1212) — a
    # genuine within-range transition, not FED already above MONO at F_min.
    configs = [_fake_config(f, int(100 * f ** 1.8), int(30 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.priors["P3"] == "held"
    assert rep.crossover_f is not None
    assert rep.crossover_kind == "observed"
    assert rep.crossover_f == 4.0


def test_p3_reports_extrapolated_crossover_when_none_is_observed():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(1e7 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert all(c.fed_cost_naive < c.mono.cost.total() for c in configs)
    assert rep.crossover_f is not None and rep.crossover_f > 16
    assert rep.crossover_kind == "extrapolated"
    # gamma >= 2 and an (extrapolated) crossover both hold: P3 reads "held".
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.priors["P3"] == "held"


def test_p3_fed_above_mono_at_f_min_is_not_misreported_as_a_crossover_there():
    """F2, the literal case named in the finding: FED-naive is above MONO
    already at the smallest swept F, and stays above at every point. A
    pre-F2 ``_crossover`` scanned for the first F with ``fed > mono`` and
    would report F_min itself — indistinguishable from a genuine in-range
    crossing. There is no below-to-above transition anywhere in the data
    (there is no "below" at all), so it is not ``"observed"``. Per the Task 7
    re-review (Finding 1, 2026-07-22) that is *not* the same as no crossover:
    FED dominating the whole sweep means the crossover, if any, lies below
    the range — ``"below-range"``, the strongest possible confirmation that
    coordination binds, not ``"none"``."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 3.0), int(50000 * f),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert all(c.fed_cost_naive > c.mono.cost.total() for c in configs)
    assert rep.crossover_f is None
    assert rep.crossover_kind == "below-range"


def test_p3_held_on_a_below_range_crossover_fed_dearer_throughout():
    """The other half of Finding 1: FED-naive is above MONO at every swept F
    *and* gamma >= 2.0 clears the tax bar — coordination is shown to bind at
    every measured point, which P3² must read as "held", not "refuted" (the
    pre-fix behaviour, which would have required an in-range or forward
    extrapolation to exist)."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(10 * f), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert all(c.fed_cost_naive > c.mono.cost.total() for c in configs)
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.crossover_kind == "below-range"
    assert rep.crossover_f is None
    assert rep.priors["P3"] == "held"


def test_crossover_extrapolated_inside_the_range_is_reported_honestly():
    """Finding 1's second half: an extrapolated F* must lie ABOVE the swept
    range to be reported as ``"extrapolated"`` — a run once produced a
    physically meaningless ``crossover_f`` of ~0.02 folders this way. Here
    FED-naive sits below MONO at every swept point (so there is no in-range
    transition and FED does not dominate the sweep either), but the fitted
    intercepts happen to cross at F*~10 -- inside [2, 16]. That must fall
    back to "none" honestly, never claim "extrapolated" at a value the swept
    data itself contradicts."""
    from west_experiment import _crossover
    from west_measure import PowerLawFit

    class _Cost:
        def __init__(self, total):
            self._total = total
        def total(self):
            return self._total

    class _Mono:
        def __init__(self, total):
            self.cost = _Cost(total)

    class _Cfg:
        def __init__(self, folders, fed_cost_naive, mono_total):
            self.folders = folders
            self.fed_cost_naive = fed_cost_naive
            self.mono = _Mono(mono_total)

    configs = [_Cfg(f, 100, 175) for f in [2, 4, 6, 8, 16]]   # fed <= mono always
    fit_fed = PowerLawFit(beta=2.0, stderr=0.0, r_squared=1.0, n=5, weak=False)
    fit_mono = PowerLawFit(beta=1.0, stderr=0.0, r_squared=1.0, n=5, weak=False)
    crossover_f, crossover_kind = _crossover(fit_fed, fit_mono, configs)
    assert crossover_kind == "none"
    assert crossover_f is None


def test_p3_refuted_when_gamma_holds_but_no_crossover_exists():
    """Ruling A (2026-07-22): gamma >= 2 alone is not enough. Here FED-naive's
    tax exponent (~2.5) clears P3_MIN_TAX_BETA, but FED never overtakes
    MONO — MONO's own exponent (~3.5) is larger, so the curves never cross,
    observed or extrapolated. Under the old rule this held; under Ruling A it
    must read "refuted" (coordination diverges but is never shown to be the
    binding constraint)."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(1000 * f ** 3.5), int(50 * f ** 2.5),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.crossover_f is None
    assert rep.crossover_kind == "none"
    assert rep.priors["P3"] == "refuted"


def test_p3_undetermined_on_a_weak_tax_fit():
    """Explicit weak-fit case: too few points to fit the tax exponent at all,
    regardless of what beta or crossover a 3-point line would suggest."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(30 * f ** 3),
                            int(500 * f)) for f in [2, 4, 8]]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.weak is True
    assert rep.priors["P3"] == "undetermined"


def test_p3_refuted_just_below_the_2_0_tax_beta_bar_with_crossover_present():
    """Boundary: an observed crossover exists in both this test and the next,
    isolating the beta_tax >= 2.0 check on its own. Here beta_tax fits just
    below 2.0 — refuted, even though a crossover is observed."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(60 * f ** 1.99),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta < 2.0
    assert rep.crossover_f is not None
    assert rep.priors["P3"] == "refuted"


def test_p3_undetermined_when_an_extrapolated_crossover_rests_on_a_weak_fed_naive_fit():
    """Finding 2 (Task 7 re-review, 2026-07-22): the demonstrated bug — a
    noisy FED-naive fit (weak, low R²) still produced an "extrapolated"
    crossover and P3² read "held" off it. FED-naive sits below MONO at every
    swept point here (no observed transition), the fit is genuinely weak,
    and the fitted lines nonetheless cross beyond the range — but that
    extrapolation must not carry the verdict: P3² must read "undetermined",
    never "held", when it rests on a weak fit."""
    from west_experiment import assemble_e2_report
    mono_vals = [int(1e6 * f ** 1.2) for f in SIZES]
    noisy_fed = [10, 900, 30, 5000, 60, 12000]
    tax_vals = [int(60 * f ** 2.5) for f in SIZES]     # clean, gamma >= 2.0
    configs = [_fake_config(f, mv, fv, int(500 * f), tax_naive=tv)
              for f, mv, fv, tv in zip(SIZES, mono_vals, noisy_fed, tax_vals)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_fed_naive.weak is True
    assert rep.crossover_kind == "extrapolated"
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.priors["P3"] == "undetermined"


def test_p3_below_range_crossover_is_not_gated_by_a_weak_fed_naive_fit():
    """The companion boundary to the test above: a ``"below-range"``
    crossover is read directly off the swept data (FED-naive above MONO at
    every point), not off ``fit_fed_naive``/``fit_mono`` — so unlike an
    extrapolated crossover it needs no weak-fit gate on those two fits. Here
    FED-naive is noisy enough to make ``fit_fed_naive`` weak yet still
    dominates MONO throughout, so P3² reads "held" (gamma clears the bar and
    the crossover exists) despite the weak fed-naive fit."""
    from west_experiment import assemble_e2_report
    mono_vals = [10 * f for f in SIZES]
    noisy_fed = [1000, 90000, 3000, 500000, 6000, 1200000]   # always > mono_vals
    tax_vals = [int(60 * f ** 2.5) for f in SIZES]
    configs = [_fake_config(f, mv, fv, int(500 * f), tax_naive=tv)
              for f, mv, fv, tv in zip(SIZES, mono_vals, noisy_fed, tax_vals)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_fed_naive.weak is True
    assert all(fv > mv for fv, mv in zip(noisy_fed, mono_vals))
    assert rep.crossover_kind == "below-range"
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.priors["P3"] == "held"


def test_p3_held_just_above_the_2_0_tax_beta_bar_with_crossover_present():
    """Boundary: same shape as above, beta_tax fits just above 2.0 — held."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(60 * f ** 2.01),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.crossover_f is not None
    assert rep.priors["P3"] == "held"


def test_p3_refuted_on_strong_gamma_below_2_even_when_crossover_fits_are_weak():
    """Finding 1 (third re-review, 2026-07-22): P3² is a conjunction
    (gamma >= 2 AND a crossover exists), so a determinate gamma < 2 refutation
    must be decided off ``fit_tax_naive`` alone, *before* the crossover-fit
    weak-fit gate is even consulted. ``fit_tax_naive`` here is strong
    (tax = 60*F^1.5, measured beta~1.502, weak=False) and clearly below 2.0;
    ``fit_mono`` is also strong (mono = 1e6*F^1.2). FED-naive is noisy enough
    to be a weak fit (measured weak=True), which forces ``crossover_kind`` to
    ``"extrapolated"`` — and under the *pre-fix* ordering the weak-crossover
    gate ran before the gamma check and swallowed this into "undetermined".
    Since gamma < 2.0 is decided by the tax fit alone, the crossover's
    reliability is irrelevant here: P3² must read "refuted"."""
    from west_experiment import assemble_e2_report
    mono_vals = [int(1e6 * f ** 1.2) for f in SIZES]
    noisy_fed = [10, 900, 30, 5000, 60, 12000]
    tax_vals = [int(60 * f ** 1.5) for f in SIZES]     # strong, beta ~1.5 < 2.0
    configs = [_fake_config(f, mv, fv, int(500 * f), tax_naive=tv)
              for f, mv, fv, tv in zip(SIZES, mono_vals, noisy_fed, tax_vals)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta < 2.0
    assert rep.fit_fed_naive.weak is True
    assert rep.crossover_kind == "extrapolated"
    assert rep.priors["P3"] == "refuted"


def test_p3_undetermined_on_a_none_crossover_resting_on_weak_fed_and_mono_fits():
    """Finding 2 (third re-review, 2026-07-22): a ``"none"`` crossover reading
    is decided *entirely* by ``fit_fed_naive``/``fit_mono`` (either
    beta_fed_naive <= beta_mono, or an extrapolated F* landing inside the
    range) — the same two fits the weak-fit gate exists to distrust for
    ``"extrapolated"``. Here both are noisy enough to be weak (measured
    weak=True for each) while ``fit_tax_naive`` is strong and clears the
    gamma >= 2.0 bar (tax = 60*F^2.5). The pre-fix gate only checked
    ``crossover_kind == "extrapolated"``, so a ``"none"`` reading resting on
    the same two untrustworthy fits fell through to "refuted" ungated. P3²
    must read "undetermined" instead."""
    from west_experiment import assemble_e2_report
    noisy_mono = [10, 900, 30, 5000, 60, 12000]
    noisy_fed = [int(0.001 * f ** 4 + 1) for f in SIZES]
    tax_vals = [int(60 * f ** 2.5) for f in SIZES]     # strong, gamma >= 2.0
    configs = [_fake_config(f, mv, fv, int(500 * f), tax_naive=tv)
              for f, mv, fv, tv in zip(SIZES, noisy_mono, noisy_fed, tax_vals)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.fit_mono.weak is True
    assert rep.fit_fed_naive.weak is True
    assert rep.crossover_kind == "none"
    assert rep.priors["P3"] == "undetermined"


def test_p3_tax_weak_gate_is_checked_before_the_gamma_refutation():
    """Finding B (Task 7 fix-4 review, 2026-07-22): the tax-weak gate
    (``fit_tax_naive.weak`` -> "undetermined") must be checked *before* the
    determinate ``gamma < 2.0`` refutation, not after. The existing
    ``test_p3_undetermined_on_a_weak_tax_fit`` only exercises this gate with a
    3-point fixture whose measured beta (~2.98) sits comfortably *above*
    2.0 -- swapping the two branches (gamma-check first, tax-weak-check
    second) still reads "undetermined" there via the n<6 weak-fit path
    reached from the *other* direction, so that test cannot discriminate the
    ordering.

    This fixture is a genuine 6-point weak fit (measured beta=1.758,
    r-squared=0.564 < 0.90 -> weak=True) whose beta *also* happens to read
    below 2.0. Under the correct ordering (weak-check first) this reads
    "undetermined". Under the swapped ordering the gamma<2.0 branch would
    fire first and read "refuted" off a fit already established to be
    unusable.

    Verified to bite: swapping the ``if fit_tax_naive.weak`` and
    ``elif fit_tax_naive.beta < P3_MIN_TAX_BETA`` branches in
    ``assemble_e2_report`` makes this test fail (reads "refuted" instead of
    "undetermined"); restoring the original order makes it pass again."""
    from west_experiment import assemble_e2_report
    tax_values = [3, 40, 9, 200, 25, 300]
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f), tax_naive=tv)
              for f, tv in zip(SIZES, tax_values)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_tax_naive.weak is True
    assert rep.fit_tax_naive.beta < 2.0
    assert rep.priors["P3"] == "undetermined"


def test_p3_crossover_weak_gate_also_fires_on_a_weak_mono_fit():
    """Finding C (Task 7 fix-4 review, 2026-07-22): the crossover weak-fit
    gate on an ``"extrapolated"``/``"none"`` reading must distrust *both*
    ``fit_fed_naive`` and ``fit_mono`` -- either one being weak makes the
    reading untrustworthy, since both feed the intercept computation (or the
    beta comparison, for "none"). Both existing gate tests
    (``test_p3_undetermined_when_an_extrapolated_crossover_rests_on_a_weak_fed_naive_fit``
    and ``test_p3_undetermined_on_a_none_crossover_resting_on_weak_fed_and_mono_fits``)
    have ``fit_fed_naive`` weak (the second has *both* weak), so neither can
    discriminate ``or fit_mono.weak`` from the gate on its own.

    Here MONO is the noisy one (measured weak=True, r-squared~0.36) while
    FED-naive is a clean ``F^1.5`` fit (weak=False) and the tax clears the
    gamma bar (``60*F^2.5``, weak=False, beta~2.5) -- this reproduces the
    reviewer's fixture, giving ``crossover_kind == "none"``. P3² must read
    "undetermined" (the "none" reading rests on the weak MONO fit), not
    "refuted" off an unreliable comparison.

    Verified to bite: dropping ``or fit_mono.weak`` from the gate condition
    in ``assemble_e2_report`` makes this test fail (reads "refuted" instead
    of "undetermined"); restoring it makes it pass again."""
    from west_experiment import assemble_e2_report
    mono_values = [10, 900, 30, 5000, 60, 12000]
    fed_values = [int(f ** 1.5) for f in SIZES]
    tax_values = [int(60 * f ** 2.5) for f in SIZES]
    configs = [_fake_config(f, mv, fv, int(500 * f), tax_naive=tv)
              for f, mv, fv, tv in zip(SIZES, mono_values, fed_values, tax_values)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.fit_mono.weak is True
    assert rep.fit_fed_naive.weak is False
    assert rep.fit_tax_naive.weak is False
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.crossover_kind == "none"
    assert rep.priors["P3"] == "undetermined"


def test_crossover_overflow_error_falls_back_honestly_instead_of_crashing():
    """Finding D (Task 7 fix-4 review, 2026-07-22): ``math.exp`` in
    ``_crossover`` can raise ``OverflowError`` when
    ``beta_fed_naive - beta_mono`` is near-degenerate and the intercept gap
    is large -- pre-existing, implausible on real cost data, but an unguarded
    crash in the honesty layer. Here MONO (``1e15*F^2``) towers over FED-naive
    (``1e6*F^2.0000001``) at every swept point, so FED never crosses it (no
    in-range or below-range signal) while the two betas are close enough that
    the intercept-difference exponent overflows a float.

    ``assemble_e2_report`` must return a report, not raise -- and the
    fallback must read honestly: FED never dominates the sweep here (MONO is
    always dearer), so the crossover reads ``"none"``, and gamma>=2.0 (tax
    ``60*F^2.5``) with no crossover reads P3² "refuted" per Ruling A, not a
    fabricated "held"."""
    from west_experiment import assemble_e2_report
    mono_values = [int(1e15 * f ** 2) for f in SIZES]
    fed_values = [int(1e6 * f ** 2.0000001) for f in SIZES]
    tax_values = [int(60 * f ** 2.5) for f in SIZES]
    configs = [_fake_config(f, mv, fv, int(500 * f), tax_naive=tv)
              for f, mv, fv, tv in zip(SIZES, mono_values, fed_values, tax_values)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)   # must not raise
    assert rep.crossover_f is None
    assert rep.crossover_kind == "none"
    assert rep.fit_tax_naive.beta >= 2.0
    assert rep.priors["P3"] == "refuted"


def test_p4_is_deferred_to_the_rider():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3),
                            int(500 * f)) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.priors["P4"] == "deferred"


def test_e2_report_carries_theta_and_tol_and_flags_the_configs_that_breach_theta():
    """F5: theta/tol were accepted but silently dropped — a later task (spec
    §3.1, broker-forced configs) needs theta on the record. One config here
    breaches theta (gap 0.30 > theta 0.20); the rest do not."""
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            gap=0.30 if f == 8 else 0.0) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.theta == 0.20
    assert rep.tol == 0.10
    assert rep.broker_forced == [8]


def test_e2_report_broker_forced_is_empty_when_no_config_breaches_theta():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            gap=0.05) for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.broker_forced == []


def test_tax_clamp_is_recorded_and_forces_the_fit_weak():
    """F6: ``max(naive_member_round, 1)`` used to silently alter verdict-bearing
    data. Here one config's tax reading is non-positive (won't happen on real
    data — see CoordinatorTax's docstring — but must be handled honestly if
    it ever does): the clamp must be counted, and the resulting fit must never
    be trusted un-flagged.

    The *six-point* fit that includes the clamped point (max(0, 1) -> 1) is
    strong on its own merits (measured: beta=3.11, r-squared=0.942,
    weak=False) — it clears both MIN_FIT_POINTS and the r-squared bar without
    any help from the forcing. So it is the F6 forcing alone — not a
    borderline fit — that turns this "weak"; a data shape whose fit is
    already weak on its own merits (as the prior version of this test used,
    r-squared=0.871 < 0.90) pins nothing, since the assertion would hold even
    with the forcing deleted. Verified by deleting the forcing line and
    confirming this test fails, then restoring it and confirming it passes
    again."""
    from west_experiment import assemble_e2_report
    tax_values = [0 if f == 2 else int(2 * f ** 2.2) for f in SIZES]
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f),
                            tax_naive=tv) for f, tv in zip(SIZES, tax_values)]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.tax_clamped_count == 1
    assert rep.fit_tax_naive.beta > 2.0    # would clear P3_MIN_TAX_BETA on its own
    assert rep.fit_tax_naive.weak is True
    assert rep.priors["P3"] == "undetermined"


def test_tax_clamp_count_is_zero_on_ordinary_data():
    from west_experiment import assemble_e2_report
    configs = [_fake_config(f, int(100 * f ** 1.8), int(50 * f ** 3), int(500 * f))
              for f in SIZES]
    rep = assemble_e2_report(configs, theta=0.20, tol=0.10)
    assert rep.tax_clamped_count == 0


def test_decide_p4_holds_on_a_monotonically_narrowing_ratio():
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 300, 3.0), TtlReading(120, 100, 200, 2.0),
                TtlReading(240, 100, 150, 1.5), TtlReading(0, 100, 100, 1.0)]
    assert decide_p4(readings) == "held"


def test_decide_p4_refuted_when_the_ratio_does_not_narrow():
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 150, 1.5), TtlReading(120, 100, 200, 2.0),
                TtlReading(240, 100, 210, 2.1), TtlReading(0, 100, 250, 2.5)]
    assert decide_p4(readings) == "refuted"


def test_decide_p4_treats_ttl_zero_as_the_largest_ttl():
    """`off` must sort last however the caller ordered the list."""
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(0, 100, 100, 1.0), TtlReading(240, 100, 150, 1.5),
                TtlReading(60, 100, 300, 3.0), TtlReading(120, 100, 200, 2.0)]
    assert decide_p4(readings) == "held"


def test_decide_p4_undetermined_on_too_few_points():
    from west_experiment import decide_p4, TtlReading
    assert decide_p4([TtlReading(120, 100, 200, 2.0)]) == "undetermined"
    assert decide_p4([]) == "undetermined"


def test_decide_p4_refuted_on_an_exactly_constant_ratio():
    """Final review Important 1: a flat ratio is pairwise-monotonic (each step's
    slack is exactly 0) but spec §5 requires a genuine narrowing to read
    'held' — retention insensitive to decay pressure is the most interesting
    possible result and must not be silently folded into 'held'."""
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 150, 1.5), TtlReading(120, 100, 150, 1.5),
                TtlReading(240, 100, 150, 1.5), TtlReading(0, 100, 150, 1.5)]
    assert decide_p4(readings) == "refuted"


def test_decide_p4_refuted_on_a_near_flat_ratio():
    """A ratio that moves within noise (0.6% end to end) must not read 'held'
    off pairwise monotonicity alone."""
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 181, 1.81), TtlReading(120, 100, 180, 1.80),
                TtlReading(240, 100, 180, 1.80), TtlReading(0, 100, 180, 1.80)]
    assert decide_p4(readings) == "refuted"


def test_decide_p4_holds_on_a_genuinely_narrowing_ratio():
    """A real, non-trivial net decrease still reads 'held' (the fix must not
    over-tighten the pass case)."""
    from west_experiment import decide_p4, TtlReading
    readings = [TtlReading(60, 100, 250, 2.5), TtlReading(120, 100, 200, 2.0),
                TtlReading(240, 100, 170, 1.7), TtlReading(0, 100, 130, 1.3)]
    assert decide_p4(readings) == "held"


def test_run_ttl_rider_produces_one_reading_per_ttl(tmp_path):
    from west_experiment import run_ttl_rider
    manifest = _tiny_vault(tmp_path)
    readings = run_ttl_rider(tmp_path, manifest, rounds=6, ttls=[120, 0])
    assert [r.ttl for r in readings] == [120, 0]
    assert all(r.mono_m >= 0 and r.fed_m >= 0 for r in readings)
    assert all(r.ratio >= 0.0 for r in readings)


def _bucket_vault(tmp_path, folders=6, notes=4, p=0.15, journal=4):
    from vault_generator import generate_vault
    return generate_vault(tmp_path, seed=20260721, folders=folders,
                          notes_per_folder=notes, cross_folder_link_prob=p,
                          journal_len=journal)


def test_run_fed_bucketed_one_member_per_bucket_plus_journal(tmp_path):
    from west_experiment import run_fed_bucketed
    from west_measure import round_robin_buckets
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    buckets = round_robin_buckets(manifest.folders, 3)     # 3 buckets of 2 folders
    fed, tax = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    assert len(fed.member_costs) == 4                       # 3 buckets + journal
    assert fed.coverage is not None and 0.0 <= fed.coverage <= 1.0
    assert tax.incremental <= tax.naive_global_round <= tax.naive_member_round


def test_run_fed_bucketed_n1_covers_every_cross_link(tmp_path):
    """A single bucket holds every folder, so coverage must be 1.0 (gap 0) —
    every cross-link's target folder is in the one member's folder set."""
    from west_experiment import run_fed_bucketed
    from west_measure import round_robin_buckets
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)  # dense links
    buckets = round_robin_buckets(manifest.folders, 1)
    fed, _tax = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    assert len(fed.member_costs) == 2                       # 1 bucket + journal
    assert fed.coverage == 1.0


def test_run_fed_bucketed_matches_run_fed_traced_at_singletons(tmp_path):
    """One-folder-per-bucket must reproduce run_fed_traced's cost exactly —
    the bucketed runner is a faithful generalisation, not a new measurement."""
    from west_experiment import run_fed_bucketed, run_fed_traced
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    singletons = [frozenset({f}) for f in manifest.folders]
    fedb, taxb = run_fed_bucketed(tmp_path, manifest, buckets=singletons,
                                  rounds=24, ttl=120)
    fedt, taxt = run_fed_traced(tmp_path, manifest, rounds=24, ttl=120)
    assert fedb.cost.materialization_atoms == fedt.cost.materialization_atoms
    assert fedb.cost.peel_proxy == fedt.cost.peel_proxy
    assert taxb == taxt
    assert fedb.coverage == fedt.coverage


def test_run_fed_bucketed_is_deterministic(tmp_path):
    from west_experiment import run_fed_bucketed
    from west_measure import round_robin_buckets
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    buckets = round_robin_buckets(manifest.folders, 2)
    a, ta = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    b, tb = run_fed_bucketed(tmp_path, manifest, buckets=buckets, rounds=24, ttl=120)
    assert a.cost.total() == b.cost.total() and ta == tb


def test_run_sweepb_point_reports_both_arms_and_cut(tmp_path):
    from west_experiment import run_sweepb_point
    manifest = _bucket_vault(tmp_path, folders=6, notes=4)
    pt = run_sweepb_point(tmp_path, manifest, n=3, rounds=24, ttl=120)
    assert pt.n == 3
    assert pt.fed_cost_naive >= pt.fed_cost_incremental
    assert pt.member_reading.journal_member_cost is not None
    assert pt.cut_links >= 0
    assert 0.0 <= pt.gap <= 1.0


def test_run_sweepb_point_link_aware_cuts_no_more_than_round_robin(tmp_path):
    from west_experiment import run_sweepb_point
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)
    rr = run_sweepb_point(tmp_path, manifest, n=2, rounds=24, ttl=120,
                          bucketing="round_robin")
    la = run_sweepb_point(tmp_path, manifest, n=2, rounds=24, ttl=120,
                          bucketing="link_aware")
    assert la.cut_links <= rr.cut_links


def test_run_p_sweep_produces_one_point_per_p_ordered(tmp_path):
    from west_experiment import run_p_sweep
    res = run_p_sweep(tmp_path, folders=4, notes=4, journal=4, rounds=16,
                      ttl=120, seed=20260721, ps=[0.15, 0.45], theta=0.20)
    assert [round(pt.p, 2) for pt in res.points] == [0.15, 0.45]
    assert all(0.0 <= pt.gap <= 1.0 for pt in res.points)
    assert all(pt.coverage == 1.0 - pt.gap for pt in res.points)


def test_run_p_sweep_records_shoulder_and_fires_broker_once(tmp_path):
    """A synthetic threshold: force theta so low that even p=0.15's gap can breach
    it, and confirm the broker fires (routes recorded) at the first breaching p."""
    from west_experiment import run_p_sweep
    res = run_p_sweep(tmp_path, folders=4, notes=4, journal=4, rounds=8,
                      ttl=120, seed=20260721, ps=[0.15, 0.45, 0.75], theta=-1.0)
    # theta=-1 => every gap (>= 0) breaches, so the shoulder is the first p.
    assert res.shoulder_p == 0.15
    assert res.broker_routes is not None and res.broker_routes >= 0
    assert res.broker_coord_cost is not None


def test_run_p_sweep_no_shoulder_leaves_broker_none(tmp_path):
    """theta=2.0 can never be breached (gap <= 1), so no broker run."""
    from west_experiment import run_p_sweep
    res = run_p_sweep(tmp_path, folders=4, notes=4, journal=4, rounds=8,
                      ttl=120, seed=20260721, ps=[0.15, 0.45], theta=2.0)
    assert res.shoulder_p is None
    assert res.broker_routes is None and res.broker_coord_cost is None


def test_run_quality_arm_reports_both_bucketings(tmp_path):
    from west_experiment import run_quality_arm
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)
    r = run_quality_arm(tmp_path, manifest, n=2, rounds=24, ttl=120, tol=0.10)
    assert r.n == 2
    assert r.link_aware_cut <= r.round_robin_cut       # link-aware cuts no more
    assert r.round_robin_cost > 0 and r.link_aware_cost > 0
    assert isinstance(r.material, bool)


def test_run_quality_arm_material_flag_follows_the_tol_threshold(tmp_path):
    from west_experiment import run_quality_arm
    manifest = _bucket_vault(tmp_path, folders=6, notes=4, p=0.6)
    r = run_quality_arm(tmp_path, manifest, n=2, rounds=24, ttl=120, tol=0.10)
    expected = r.link_aware_cost <= r.round_robin_cost * (1 - 0.10)
    assert r.material == expected


def _sbpoint(n, cn, ci, cv=0.02, mean=1000.0):
    from west_experiment import SweepBPoint
    from west_measure import MemberCostReading
    return SweepBPoint(
        n=n, fed_cost_naive=cn, fed_cost_incremental=ci,
        member_reading=MemberCostReading([int(mean)] * max(n, 1), 120, mean, cv),
        m_fed=100, k2_fed=1.0, k3_fed=0.0, gap=0.0, cut_links=0)


def _presult(shoulder):
    from west_experiment import PSweepResult
    return PSweepResult(points=[], shoulder_p=shoulder,
                        broker_routes=(0 if shoulder is not None else None),
                        broker_coord_cost=(0 if shoulder is not None else None))


def _quality(material):
    from west_experiment import QualityArmResult
    return QualityArmResult(n=4, round_robin_cost=1000,
                            link_aware_cost=(800 if material else 990),
                            round_robin_cut=10, link_aware_cut=2, material=material)


NS = [1, 2, 3, 4, 6, 12]


def test_pb1_held_on_interior_naive_minimum():
    from west_experiment import assemble_e2b_report
    # naive U with min at n=4; incremental monotone down.
    naive = {1: 1000, 2: 600, 3: 450, 4: 400, 6: 700, 12: 1500}
    incr = {1: 900, 2: 500, 3: 350, 4: 300, 6: 250, 12: 200}
    pts = [_sbpoint(n, naive[n], incr[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB1"] == "held"
    assert rep.priors["PB2"] == "held"


def test_pb1_refuted_when_naive_minimum_is_at_an_endpoint():
    from west_experiment import assemble_e2b_report
    naive = {n: 100 * n for n in NS}                    # monotone up -> min at n=1
    pts = [_sbpoint(n, naive[n], naive[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB1"] == "refuted"


def test_pb2_refuted_when_incremental_has_an_interior_dip():
    from west_experiment import assemble_e2b_report
    naive = {n: 100 * n for n in NS}
    incr = {1: 500, 2: 400, 3: 300, 4: 200, 6: 350, 12: 600}   # interior min at 4
    pts = [_sbpoint(n, naive[n], incr[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB2"] == "refuted"


def test_pb2_refuted_when_incremental_is_monotone_but_plateaus_interior():
    """Gap 1: monotone_nonincreasing=True AND interior=True (a plateau at
    n=4,6,12 — argmin ties to the smallest, n=4, which is interior). PB2 must
    read "refuted" — pins the ``and not ui.interior`` conjunct: dropping it
    would flip this fixture to "held"."""
    from west_experiment import assemble_e2b_report
    naive = {n: 100 * n for n in NS}                    # monotone up; keeps PB1 out of the way
    incr = {1: 1000, 2: 900, 3: 850, 4: 800, 6: 800, 12: 800}
    pts = [_sbpoint(n, naive[n], incr[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB2"] == "refuted"


def test_pb2_refuted_when_incremental_is_nonmonotone_with_endpoint_minimum():
    """Gap 2: monotone_nonincreasing=False AND interior=False (min at the
    n=12 endpoint, but 500->600 breaks monotonicity). PB2 must read
    "refuted" — pins the ``ui.monotone_nonincreasing`` conjunct: replacing it
    with True would flip this fixture to "held"."""
    from west_experiment import assemble_e2b_report
    naive = {n: 100 * n for n in NS}
    incr = {1: 500, 2: 600, 3: 400, 4: 300, 6: 200, 12: 100}
    pts = [_sbpoint(n, naive[n], incr[n]) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB2"] == "refuted"


def test_pb3_and_pb4_held_with_a_shoulder():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.60), _quality(True), tol=0.10)
    assert rep.priors["PB3"] == "held" and rep.priors["PB4"] == "held"


def test_pb4_undetermined_when_no_shoulder():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100) for n in NS]
    rep = assemble_e2b_report(pts, _presult(None), _quality(False), tol=0.10)
    assert rep.priors["PB3"] == "refuted"
    assert rep.priors["PB4"] == "undetermined"          # conditional on PB3


def test_pb4_refuted_when_shoulder_but_quality_immaterial():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.60), _quality(False), tol=0.10)
    assert rep.priors["PB4"] == "refuted"


def test_pb5_refuted_when_member_cost_drifts_across_n():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100, mean=1000.0 * n) for n in NS]   # 12x drift
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB5"] == "refuted"


def test_pb5_held_when_member_cost_is_flat():
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100, cv=0.02, mean=1000.0) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB5"] == "held"


def test_pb5_refuted_when_flat_means_but_high_cv():
    """Gap 3: means flat across n (flat=True) but per-point CV is high
    (tight=False). PB5 must read "refuted" — pins the ``cv < 0.5`` conjunct:
    broadening PB5_MAX_CV to 100 would flip this fixture to "held", since the
    other two pb5 fixtures both use cv=0.02 and never exercise it."""
    from west_experiment import assemble_e2b_report
    pts = [_sbpoint(n, 100, 100, cv=0.6, mean=1000.0) for n in NS]
    rep = assemble_e2b_report(pts, _presult(0.45), _quality(True), tol=0.10)
    assert rep.priors["PB5"] == "refuted"
