"""Smoke test for the E3b driver (`tools/run_west_e3b.py`).

Contract: the driver runs end-to-end in smoke mode, produces numbers-only output,
and includes all required summary fields."""

import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_run_west_e3b_driver_smoke():
    """Run the driver in smoke mode; verify exit code, required fields, and custody."""
    with tempfile.TemporaryDirectory(prefix="test_e3b_") as tmp:
        dest = Path(tmp)
        result = subprocess.run(
            ["uv", "run", "python", "tools/run_west_e3b.py", "--smoke",
             "--dest", str(dest)],
            cwd=str(REPO),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Driver exited with code {result.returncode}.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

        out = result.stdout

        # Verify required header and fields
        required_fields = [
            "West-in-kytē E3b",
            "mode=",
            "seed=",
            "F0=",
            "structured_starts=",
            "optimum sizes=",
            "consistency_ok=",
            "arm_i_control",
            "priors: {",
            "determinism_canary:",
            "notes:",
        ]
        for field in required_fields:
            assert field in out, (
                f"Missing required field: {field}\n"
                f"stdout:\n{out}"
            )

        # Custody: no folder names in stdout
        assert "Folder-" not in out, (
            f"Folder names leaked into stdout (custody violation).\n"
            f"stdout:\n{out}"
        )
