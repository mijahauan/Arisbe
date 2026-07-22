"""Driver contract for the E2 sweep (numbers-only custody + the pre-registered grid)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "tools" / "run_west_e2.py"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def test_driver_exists():
    assert DRIVER.exists()


def test_grid_matches_the_pre_registered_spec():
    import run_west_e2
    assert run_west_e2.SEED == 20260721
    assert [f for f, _r in run_west_e2.GRID] == [2, 4, 6, 8, 12, 16]
    assert [r for _f, r in run_west_e2.GRID] == [75, 125, 175, 225, 325, 425]
    for folders, rounds in run_west_e2.GRID:
        assert rounds == 25 * (folders + 1), "R = 25*(F+1): 25 rounds per member"


def test_rider_ttls_match_the_spec():
    import run_west_e2
    assert run_west_e2.RIDER_TTLS == [60, 120, 240, 0]   # 0 == off, ordered last


def test_build_grid_is_pure_and_deterministic():
    import run_west_e2
    assert run_west_e2.build_grid() == run_west_e2.build_grid()
    assert run_west_e2.build_grid() == run_west_e2.GRID


def test_driver_runs_a_tiny_sweep_and_prints_numbers_only(tmp_path):
    """End-to-end smoke on a deliberately tiny grid, asserting the custody rule."""
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    assert out.returncode == 0, out.stderr
    text = out.stdout
    assert "beta_mono=" in text and "beta_fed_incr=" in text
    assert "priors:" in text
    # Custody: no path, no note id, no .md filename may reach stdout.
    assert ".md" not in text
    assert str(tmp_path) not in text
    assert "note-" not in text
    assert "Folder-" not in text


def test_driver_reports_the_disclosed_secondary_and_the_a3_note(tmp_path):
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    assert "naive_global" in out.stdout, "the bracket's interior must be reported"
    assert "not verdict-bearing" in out.stdout
