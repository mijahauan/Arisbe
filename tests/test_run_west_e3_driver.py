"""Driver contract: tools/run_west_e3.py --smoke runs end-to-end, prints the
numbers-only lines, and leaves ledgers that replay clean."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_smoke_driver_contract(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "run_west_e3.py"),
         "--smoke", "--dest", str(tmp_path)],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "West-in-kytē E3" in out
    for w in ("W1", "W2", "W3", "W4"):
        assert f"walk={w} halt=" in out
    assert "rider biting_ttl=" in out
    assert "priors: {" in out
    assert "determinism_canary: PASS" in out
    assert "notes:" in out
    # Ledgers exist and replay clean.
    sys.path.insert(0, str(REPO / "src"))
    from west_meta_agon import replay_walk
    for w in ("W1", "W2", "W3", "W4"):
        led = tmp_path / f"{w}.jsonl"
        assert led.exists()
        assert replay_walk(led)["ok"] is True
    # Numbers-only: no folder name ever printed.
    assert "Folder-" not in out
