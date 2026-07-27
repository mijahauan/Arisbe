"""Portability guard: no test may carry a developer-machine absolute path.

The E3b driver smoke test shipped with a hard-coded ``/Users/mjh/...`` cwd and
broke the CI full-suite run on GitHub Actions (2026-07-27), where the workspace
lives elsewhere — the exact class of bug this scan makes unshippable. Tests
must derive the repo root from ``__file__`` (the sibling driver tests' ``REPO``
pattern) or use tmp_path/fixtures. Scope is ``tests/`` only: a tool's
``__main__`` convenience block and the vault driver's intentional ``--root``
default are launcher ergonomics, not CI surface.
"""

from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_MARKER = "/Users/"


def test_no_test_carries_a_developer_absolute_path():
    offenders = []
    for py in sorted(_TESTS_DIR.glob("*.py")):
        if py.name == Path(__file__).name:
            continue
        if _MARKER in py.read_text(encoding="utf-8"):
            offenders.append(py.name)
    assert not offenders, (
        f"developer-machine absolute paths ({_MARKER}…) in tests: {offenders} — "
        "derive the repo root from __file__ (the REPO pattern) or use tmp_path"
    )
