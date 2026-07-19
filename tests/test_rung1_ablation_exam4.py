"""Smoke test for the Examination IV disposal harness
(``tools/run_rung1_ablation_exam4.py``): every arm runs a short round budget
without error, and — since every arm must be deterministic and offline — two
identical invocations of the same arm produce identical choice journals. This
is a smoke test, not a re-assertion of any run's *result*: the harness is a
run artifact (panel B, 3(d)/(11)d), and its outputs are read by a human, not
graded by CI."""
from arithmetic_world import replay_choices
from tools.run_rung1_ablation_exam4 import (
    arm, discriminating_arm, purse_arm, run_churn_pump,
    severity_greedy, round_robin,
)
from arithmetic_world import scatter_chooser


def test_a0_economy_runs_ten_rounds_and_is_deterministic():
    r1, f1, res1 = arm("smoke_a0", rounds=10)
    r2, f2, res2 = arm("smoke_a0", rounds=10)
    assert len(res1.outcomes) <= 10
    assert replay_choices(f1.journal) == replay_choices(f2.journal)
    assert r1 == r2


def test_baseline_choosers_run_ten_rounds_and_are_deterministic():
    for chooser in (severity_greedy, round_robin, scatter_chooser):
        r1, f1, res1 = arm("smoke_baseline", chooser=chooser, rounds=10)
        r2, f2, res2 = arm("smoke_baseline", chooser=chooser, rounds=10)
        assert len(res1.outcomes) <= 10
        assert replay_choices(f1.journal) == replay_choices(f2.journal)
        assert r1 == r2


def test_discriminating_arm_runs_ten_rounds_and_is_deterministic():
    r1, f1, _ = discriminating_arm("smoke_disc", rounds=10)
    r2, f2, _ = discriminating_arm("smoke_disc", rounds=10)
    assert replay_choices(f1.journal) == replay_choices(f2.journal)
    assert r1 == r2


def test_discriminating_arm_choosers_all_run():
    for chooser in (severity_greedy, scatter_chooser):
        r, feed, res = discriminating_arm("smoke_disc_c", chooser=chooser, rounds=10)
        assert len(res.outcomes) <= 10


def test_cost_purse_arm_runs_ten_rounds_and_is_deterministic():
    r1, f1, res1 = purse_arm("smoke_purse", rounds=10, purse=30.0)
    r2, f2, res2 = purse_arm("smoke_purse", rounds=10, purse=30.0)
    assert replay_choices(f1.journal) == replay_choices(f2.journal)
    assert r1 == r2
    assert f1.spent == f2.spent


def test_cost_purse_stops_on_exhaustion():
    # a small purse must exhaust well before a generous round budget
    r, feed, res = purse_arm("smoke_purse_small", rounds=1000, purse=5.0)
    assert feed.spent >= 5.0
    assert len(res.outcomes) < 1000


def test_churn_pump_runs_ten_rounds_and_is_deterministic():
    f1, res1 = run_churn_pump(rounds=10, ttl=8)
    f2, res2 = run_churn_pump(rounds=10, ttl=8)
    assert replay_choices(f1.journal) == replay_choices(f2.journal)
    assert [o.disposition for o in res1.outcomes] == [o.disposition for o in res2.outcomes]
