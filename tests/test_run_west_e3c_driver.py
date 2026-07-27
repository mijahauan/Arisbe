"""E3c driver smoke contract (E3b spec §10): the symmetry-breaking rider's
driver runs end-to-end at smoke scale, prints the contract lines, and its
perturbation constructor honors the pre-registered cell rules."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

ROOT = Path(__file__).parent.parent


class TestPerturbedStarts:
    def test_cells_move_first_folder_and_preserve_n(self):
        from run_west_e3c import perturbed_starts
        folders = [f"Folder-{i}" for i in range(12)]
        base, starts, skipped = perturbed_starts(folders)
        assert len(starts) == 3 and skipped == []
        assert sorted(len(b) for b in base) == [4, 4, 4]
        for (_src, _dst), b in starts:
            # one folder moved: sizes 3/4/5 as a multiset, N stays 3
            assert sorted(len(x) for x in b) == [3, 4, 5]
            # nothing lost or duplicated
            flat = [f for bucket in b for f in bucket]
            assert sorted(flat) == sorted(folders)

    def test_deterministic(self):
        from run_west_e3c import perturbed_starts
        folders = [f"Folder-{i}" for i in range(12)]
        assert perturbed_starts(folders) == perturbed_starts(folders)

    def test_source_singleton_skipped_and_counted(self):
        from run_west_e3c import perturbed_starts
        # 4 folders round-robin into 3 buckets -> sizes 2/1/1: cells whose
        # source bucket is a singleton must be skipped-and-counted.
        folders = [f"Folder-{i}" for i in range(4)]
        _base, starts, skipped = perturbed_starts(folders)
        assert len(starts) + len(skipped) == 3
        assert len(skipped) >= 1


class TestDriverSmoke:
    def test_smoke_prints_contract_lines(self, tmp_path):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "run_west_e3c.py"),
             "--smoke", "--no-canary", "--dest", str(tmp_path)],
            capture_output=True, text=True, timeout=600)
        assert proc.returncode == 0, proc.stderr
        out = proc.stdout
        assert "West-in-kytē E3c" in out
        assert re.search(r"base=\d+(/\d+)* perturbed_starts=\d+ skipped_cells=\d+", out)
        assert re.search(r"cell=\dto\d start=\d+(/\d+)* -> optimum=", out)
        assert "determinism_canary: skipped" in out
        assert "notes:" in out
        # custody: no folder names on stdout
        assert "Folder-" not in out
