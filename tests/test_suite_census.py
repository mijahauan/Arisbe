"""The suite census — deriving the headline instead of narrating it.

``CLAUDE.md`` quotes a figure for the size of this suite, and on 2026-09-22 that
figure did not reconcile against collection: the run reported 5,396 outcomes on a
tree that collects 5,330 tests, 66 more than exist. The gap was recorded as
docket 6l with the honest instruction — *derive the headline, or stop quoting a
total nothing reconciles.*

Nothing was miscounted. The **instrument** was wrong, in two ways that compound:

1. ``pytest --collect-only -q`` prints the number of collected items and says
   **nothing** about modules that skipped at import. A module-level skip
   contributes **no collected item** and **one ``skipped`` outcome**, so the run
   legitimately reports more outcomes than collection ever mentioned. Thirteen
   of this project's modules do exactly that (the ``*_e2e.py`` suites, through
   ``tests/e2e_support.require_browser``).
2. **This suite has no fixed size.** That same browser gate moves 66 tests
   across the boundary of existence: with a launchable chromium the thirteen
   modules collect 66 items and skip no modules; without one, those 66 tests do
   not exist and thirteen module skips are reported instead. The two figures in
   the docket were measured on the two sides of that gate, which is the whole of
   the 66 — and the arithmetic closes exactly once the gate is named.

So the identity worth keeping is

    outcomes  ==  selected items  +  module-level skips

where *outcomes* sums every bucket pytest reports for something it tried
(passed, failed, skipped, xfailed, xpassed, errors) and excludes the two buckets
that are not outcomes at all: *deselected* (filtered before the run) and
*warnings*.

This file pins that identity the only way a claim about pytest's reporting can be
pinned — by **running real pytest** over tiny throwaway suites, one per shape,
and comparing the census's derived total against the summary pytest actually
prints. If a future pytest changes how it reports a module-level skip, these go
red on the day it happens rather than the day someone next re-does the
arithmetic by hand.

It also pins the identity's **one known exception**, because an identity trusted
past its domain is worse than no identity: a test that fails and then errors in
teardown is reported in two buckets, and the sum exceeds the item count honestly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CENSUS = ROOT / "tools" / "suite_census.py"

sys.path.insert(0, str(ROOT / "tools"))
from suite_census import parse_summary  # noqa: E402 - needs the path above

PLAIN = {
    "pytest.ini": "[pytest]\n",
    "test_plain.py": (
        "def test_a():\n    assert True\n\n"
        "def test_b():\n    assert True\n\n"
        "def test_c():\n    assert True\n"
    ),
}

MODULE_SKIP = {
    "pytest.ini": "[pytest]\n",
    "test_plain.py": "def test_a():\n    assert True\n\ndef test_b():\n    assert True\n",
    "test_gated.py": (
        "import pytest\n"
        "pytest.skip('the gate is shut', allow_module_level=True)\n\n"
        "def test_c():\n    assert True\n\n"
        "def test_d():\n    assert True\n\n"
        "def test_e():\n    assert True\n"
    ),
}

DESELECTED = {
    "pytest.ini": "[pytest]\nmarkers =\n    slow: excluded by -m\naddopts = -m 'not slow'\n",
    "test_mixed.py": (
        "import pytest\n\n"
        "def test_a():\n    assert True\n\n"
        "@pytest.mark.slow\ndef test_b():\n    assert True\n\n"
        "@pytest.mark.slow\ndef test_c():\n    assert True\n"
    ),
}

EXPECTED_FAILURES = {
    "pytest.ini": "[pytest]\n",
    "test_x.py": (
        "import pytest\n\n"
        "@pytest.mark.xfail(reason='known')\ndef test_a():\n    assert False\n\n"
        "@pytest.mark.xfail(reason='fixed but not strict')\ndef test_b():\n    assert True\n\n"
        "def test_c():\n    pytest.skip('at runtime')\n"
    ),
}

IMPORT_ERROR = {
    "pytest.ini": "[pytest]\n",
    "test_plain.py": "def test_a():\n    assert True\n",
    "test_broken.py": (
        "import a_module_that_is_not_installed_anywhere  # noqa: F401\n\n"
        "def test_b():\n    assert True\n\n"
        "def test_c():\n    assert True\n"
    ),
}

TEARDOWN_ERROR = {
    "pytest.ini": "[pytest]\n",
    "test_te.py": (
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def breaks_on_the_way_out():\n"
        "    yield\n"
        "    raise RuntimeError('teardown')\n\n"
        "def test_a(breaks_on_the_way_out):\n    assert False\n"
    ),
}


def _write(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        (tmp_path / name).write_text(body)
    return tmp_path


def _census(target: Path) -> dict:
    """The census as a user takes it — the real CLI, in a subprocess."""
    done = subprocess.run(
        [sys.executable, str(CENSUS), "--json", str(target)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert done.returncode == 0, f"census failed:\n{done.stdout}\n{done.stderr}"
    return json.loads(done.stdout)


def _run(target: Path) -> dict:
    """Really run the suite, and read the summary pytest prints."""
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(target)],
        capture_output=True,
        text=True,
        cwd=str(target),
    )
    summary = parse_summary(done.stdout)
    assert summary is not None, f"no summary line found in:\n{done.stdout}"
    return summary


class TestReadingASummaryLine:
    """``parse_summary`` is what every other test here decides by, so it is
    measured directly rather than only through them."""

    def test_this_projects_own_summary_line(self):
        summary = parse_summary(
            "1 failed, 5161 passed, 342 skipped, 10 deselected, 2 xfailed "
            "in 3124.53s (0:52:04)"
        )
        assert summary["outcomes"] == 5506, "1 + 5161 + 342 + 2; deselected is not one"
        assert summary["deselected"] == 10

    def test_warnings_and_deselected_are_not_outcomes(self):
        summary = parse_summary("3 passed, 2 deselected, 7 warnings in 1.20s")
        assert summary["outcomes"] == 3
        assert (summary["deselected"], summary["warnings"]) == (2, 7)

    def test_error_singular_and_plural_both_count(self):
        assert parse_summary("1 failed, 1 error in 0.12s")["errors"] == 1
        assert parse_summary("2 failed, 3 errors in 0.12s")["errors"] == 3

    def test_the_decorated_form_reads_the_same(self):
        """``-q`` prints a bare line, the default form pads it with ``=``. The
        counts must not care; only the recorded ``line`` differs."""
        bare = parse_summary("1 failed, 2 passed in 0.50s")
        decorated = parse_summary("=========== 1 failed, 2 passed in 0.50s ===========")
        assert {k: v for k, v in bare.items() if k != "line"} == {
            k: v for k, v in decorated.items() if k != "line"
        }
        assert bare["outcomes"] == 3

    def test_the_last_summary_wins_over_earlier_count_lines(self):
        """A log holds a collection line too, and it must not be mistaken for the
        verdict."""
        summary = parse_summary(
            "5493/5503 tests collected (10 deselected) in 3.68s\n"
            "...F...\n"
            "1 failed, 5 passed in 12.00s\n"
        )
        assert summary["outcomes"] == 6

    def test_a_run_with_no_summary_is_not_reported_as_zero(self):
        assert parse_summary("collecting ...\nkilled\n") is None

    def test_no_tests_ran_is_a_real_zero(self):
        assert parse_summary("no tests ran in 0.01s")["outcomes"] == 0


class TestTheIdentityOnRealPytestRuns:
    """One shape per case: derive the total, then run and compare."""

    def test_a_plain_suite_reconciles(self, tmp_path):
        target = _write(tmp_path, PLAIN)
        census, run = _census(target), _run(target)
        assert census["selected"] == 3
        assert census["module_skips"] == 0
        assert census["expected_outcomes"] == run["outcomes"] == 3

    def test_a_module_level_skip_is_an_outcome_that_collects_nothing(self, tmp_path):
        target = _write(tmp_path, MODULE_SKIP)
        census, run = _census(target), _run(target)
        assert census["selected"] == 2, "the gated module's three tests do not exist"
        assert census["module_skips"] == 1
        assert census["expected_outcomes"] == run["outcomes"] == 3
        assert run["skipped"] == 1

    def test_the_module_skip_term_is_what_makes_the_identity_hold(self, tmp_path):
        """Shown to bite: drop the term and the plain suite still reconciles while
        this one does not. This is the exact defect docket 6l recorded."""
        target = _write(tmp_path, MODULE_SKIP)
        census, run = _census(target), _run(target)
        assert census["selected"] != run["outcomes"], (
            "without the module-skip term the identity is off by the number of "
            "gated modules — which is how 66 unexplained outcomes were recorded"
        )
        assert census["expected_outcomes"] == run["outcomes"]

    def test_the_gated_module_is_named_with_its_reason(self, tmp_path):
        target = _write(tmp_path, MODULE_SKIP)
        census = _census(target)
        (skip,) = census["module_skips_detail"]
        assert skip["path"].endswith("test_gated.py")
        assert "the gate is shut" in skip["reason"]

    def test_deselected_items_are_not_outcomes(self, tmp_path):
        target = _write(tmp_path, DESELECTED)
        census, run = _census(target), _run(target)
        assert (census["selected"], census["deselected"]) == (1, 2)
        assert census["expected_outcomes"] == run["outcomes"] == 1
        assert run["deselected"] == 2

    def test_a_module_that_cannot_be_imported_cancels_the_run(self, tmp_path):
        """A collection error is *not* one more outcome — it aborts the session.

        Measured: pytest reports ``1 error`` and the healthy module's test never
        runs at all. So there is no total to publish, and the census must say so
        rather than name a figure for a run that cannot happen.
        """
        target = _write(tmp_path, IMPORT_ERROR)
        run = _run(target)
        assert run["errors"] == 1
        assert run["passed"] == 0, "the healthy module's test never ran"

        done = subprocess.run(
            [sys.executable, str(CENSUS), "--json", str(target)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert done.returncode != 0, "a suite that cannot be collected has no headline"
        census = json.loads(done.stdout)
        assert census["suite_can_run"] is False
        assert census["expected_outcomes"] is None
        assert census["collect_errors"] == 1
        assert any("test_broken" in name for name in census["collect_errors_detail"])

    def test_xfail_xpass_and_runtime_skip_are_one_outcome_each(self, tmp_path):
        target = _write(tmp_path, EXPECTED_FAILURES)
        census, run = _census(target), _run(target)
        assert census["selected"] == 3
        assert census["expected_outcomes"] == run["outcomes"] == 3
        assert (run["xfailed"], run["xpassed"], run["skipped"]) == (1, 1, 1)


class TestTheCensusCanSayNo:
    """The instrument must refuse, not report a confident zero.

    While this tool was being written, a dataclass ``__eq__`` made its own pytest
    plugin unhashable; pytest died in ``pytest_sessionstart`` and the census
    cheerfully reported **0 selected items, 0 module skips, 0 expected outcomes**
    against the real suite. A censuser that answers zero when it has measured
    nothing is the exact shape this whole arc is about, committed inside the
    instrument built to close it.
    """

    def test_a_collection_that_did_not_happen_is_refused(self, tmp_path):
        """The reachable case: a mistyped path. pytest exits 4 without collecting,
        and the honest answer is a refusal, not a census of nothing."""
        done = subprocess.run(
            [sys.executable, str(CENSUS), "--json", str(tmp_path / "no_such_dir")],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert done.returncode != 0, "a failed collection must not report a census"
        assert done.stdout.strip() == "", "no census may be printed when none was taken"
        assert "collection did not complete" in done.stderr.lower()

    def test_an_empty_target_is_not_the_same_as_a_failed_one(self, tmp_path):
        """Zero tests is a real answer; zero *because nothing ran* is not."""
        (tmp_path / "pytest.ini").write_text("[pytest]\n")
        census = _census(tmp_path)
        assert census["selected"] == 0
        assert census["expected_outcomes"] == 0


class TestTheIdentitysOneKnownException:
    """An identity trusted past its domain is worse than no identity."""

    def test_a_failure_plus_a_teardown_error_reports_twice(self, tmp_path):
        target = _write(tmp_path, TEARDOWN_ERROR)
        census, run = _census(target), _run(target)
        assert census["selected"] == 1
        assert (run["failed"], run["errors"]) == (1, 1)
        assert run["outcomes"] == 2 > census["expected_outcomes"], (
            "one item, two buckets: the identity is an equality only while no "
            "test is reported in two of them"
        )


class TestTheRealSuite:
    """Cheap checks on this project's own suite — collection only, no run."""

    @pytest.fixture(scope="class")
    def census(self) -> dict:
        return _census(ROOT / "tests")

    def test_the_census_is_self_consistent(self, census):
        assert census["expected_outcomes"] == census["selected"] + census["module_skips"]
        assert census["selected"] > 5000, "sanity: this is the real suite"

    def test_no_test_module_goes_uncounted(self, census):
        """The third quiet route: a module can sit in ``tests/`` and contribute
        nothing while every count stays green — a class renamed off ``Test*``, a
        file moved, an import guard that stops firing. Every module on disk must
        be accounted for: it yields items, or it is named by a module-level skip,
        or it is wholly deselected, or it holds no tests at all.
        """
        unaccounted = census["unaccounted_modules"]
        assert unaccounted == [], (
            "these test modules contribute nothing and nothing says why: "
            f"{unaccounted}"
        )

    def test_the_browser_gate_is_visible_in_the_census(self, census):
        """Whichever side of the gate this machine is on, the census says so —
        so the figure can never again be compared across it in silence."""
        gated = [s for s in census["module_skips_detail"] if "e2e_support" in s["reason_location"]]
        e2e_items = [n for n in census["per_file"] if n.endswith("_e2e.py")]
        if gated:
            assert not e2e_items, "gated modules cannot also yield items"
        else:
            assert e2e_items, (
                "no browser gate fired and no e2e module collected anything — "
                "the e2e suites have gone missing by some third route"
            )
