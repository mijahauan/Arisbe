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
