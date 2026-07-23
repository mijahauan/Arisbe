"""Driver contract for the E2b calibration (numbers-only custody + the grid)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "tools" / "run_west_e2b.py"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def test_driver_exists():
    assert DRIVER.exists()


def test_grid_matches_the_pre_registered_spec():
    import run_west_e2b
    assert run_west_e2b.SEED == 20260721
    assert run_west_e2b.F0 == 12
    assert run_west_e2b.SWEEP_N == [1, 2, 3, 4, 6, 12]
    assert run_west_e2b.R_FIXED == 325
    assert run_west_e2b.P_LIST == [0.15, 0.30, 0.45, 0.60, 0.75]
    assert run_west_e2b.THETA == 0.20


def test_build_config_is_pure_and_deterministic():
    import run_west_e2b
    assert run_west_e2b.build_config() == run_west_e2b.build_config()


def test_driver_runs_a_tiny_sweep_numbers_only(tmp_path):
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=1200, cwd=str(ROOT),
    )
    assert out.returncode == 0, out.stderr
    text = out.stdout
    assert "priors:" in text
    assert "PB1" in text and "PB4" in text
    # Custody: no path, note id, .md filename, or folder name may reach stdout.
    assert ".md" not in text
    assert str(tmp_path) not in text
    assert "note-" not in text
    assert "Folder-" not in text


def test_driver_reports_ucurve_and_shoulder(tmp_path):
    out = subprocess.run(
        [sys.executable, str(DRIVER), "--dest", str(tmp_path), "--smoke",
         "--no-canary"],
        capture_output=True, text=True, timeout=1200, cwd=str(ROOT),
    )
    assert "argmin_n" in out.stdout
    assert "shoulder" in out.stdout
