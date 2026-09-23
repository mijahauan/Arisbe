#!/usr/bin/env python3
"""The suite census — generate the headline figure instead of narrating it.

``CLAUDE.md``'s Testing section quotes a total for this suite, and on 2026-09-22
that total did not reconcile: the run reported **5,396** outcomes on a tree that
collects **5,330** tests. Sixty-six outcomes for tests that, on the face of it,
did not exist. Recorded as docket 6l with the honest instruction — *derive the
headline, or stop quoting a total nothing reconciles.*

**Nothing was miscounted.** The instrument was wrong, twice over:

1. ``pytest --collect-only -q`` reports the number of collected items and says
   **nothing** about a module that skipped at import. Such a module contributes
   **no collected item** and **one ``skipped`` outcome**, so a run truthfully
   reports more outcomes than collection ever mentioned. Thirteen modules here do
   exactly that — the ``*_e2e.py`` suites, through
   ``tests/e2e_support.require_browser``.
2. **This suite has no fixed size.** That same gate moves 66 tests across the
   boundary of existence. With a launchable chromium the thirteen modules collect
   66 items and skip nothing; without one, those 66 tests *are not there* and 13
   module skips stand in their place. The docket's two figures were measured on
   opposite sides of the gate, and that is the whole of the 66.

So there is one identity worth keeping, and this tool computes both of its terms
from a single collection pass — about five seconds, against the suite's fifty-two
minutes:

    outcomes  ==  selected items  +  module-level skips

*outcomes* sums every bucket pytest reports for something it tried — passed,
failed, skipped, xfailed, xpassed, errors — and excludes the two buckets that are
not outcomes: *deselected* (filtered out before the run) and *warnings*.

The identity has **one known exception**, pinned in ``tests/test_suite_census.py``
so that nobody trusts it past its domain: a test that fails and then errors in
teardown is reported in two buckets, so the sum exceeds the item count honestly.

Usage::

    uv run python tools/suite_census.py                 # census the suite
    uv run python tools/suite_census.py --json           # the same, as JSON
    uv run python tools/suite_census.py --against run.log   # reconcile a real run

``--against`` takes a file holding a pytest run's output (``uv run pytest tests/ -q
| tee run.log``), reads the summary line, and exits non-zero if the identity does
not hold — which is how a quoted headline stops being a narrated one.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The buckets pytest reports for something it actually tried. "deselected" is not
# here because a deselected item never ran; "warnings" is not an outcome at all.
OUTCOME_BUCKETS = ("passed", "failed", "skipped", "xfailed", "xpassed", "errors")

_COUNT = re.compile(
    r"(\d+)\s+(passed|failed|skipped|deselected|xfailed|xpassed|errors?|warnings?)\b"
)


# --------------------------------------------------------------------------- #
# Reading a run's summary line                                                #
# --------------------------------------------------------------------------- #


def parse_summary(text: str) -> dict | None:
    """Read the counts out of a pytest run's summary line.

    Pure, so it can be tested against real pytest output without running pytest.
    Returns ``None`` when the text holds no summary line at all — which is itself
    worth surfacing, since it means the run did not finish.
    """
    best: dict | None = None
    for line in text.splitlines():
        if not re.search(r"\bin \d+(\.\d+)?s", line):
            continue
        found = _COUNT.findall(line)
        # "no tests ran in 0.01s" is a run that FINISHED with zero outcomes, which
        # is a different fact from a run that never reported at all. Without this,
        # an empty suite and a killed one read identically.
        if not found and "no tests ran" not in line:
            continue
        counts = {bucket: 0 for bucket in (*OUTCOME_BUCKETS, "deselected", "warnings")}
        for number, word in found:
            key = "errors" if word.startswith("error") else (
                "warnings" if word.startswith("warning") else word
            )
            counts[key] += int(number)
        counts["outcomes"] = sum(counts[bucket] for bucket in OUTCOME_BUCKETS)
        counts["line"] = line.strip()
        best = counts  # the last such line wins: pytest's own final summary
    return best


# --------------------------------------------------------------------------- #
# Taking the census                                                           #
# --------------------------------------------------------------------------- #


@dataclass(eq=False)  # eq=False keeps it hashable: pytest registers plugins in a set
class _Plugin:
    """Records what collection knows, including what ``-q`` declines to print."""

    selected: list[str] = field(default_factory=list)
    deselected: list[str] = field(default_factory=list)
    module_skips: list[dict] = field(default_factory=list)
    collect_errors: list[str] = field(default_factory=list)
    rootpath: Path = ROOT
    finished: bool = False

    def pytest_collection_finish(self, session) -> None:
        self.selected = [item.nodeid for item in session.items]
        self.rootpath = Path(session.config.rootpath)
        self.finished = True

    def pytest_deselected(self, items) -> None:
        self.deselected.extend(item.nodeid for item in items)

    def pytest_collectreport(self, report) -> None:
        if report.outcome == "skipped":
            self.module_skips.append(
                {
                    "path": report.nodeid,
                    "reason": _skip_reason(report),
                    "reason_location": _skip_location(report),
                }
            )
        elif report.outcome == "failed":
            self.collect_errors.append(report.nodeid)


def _skip_reason(report) -> str:
    longrepr = getattr(report, "longrepr", None)
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2]).removeprefix("Skipped: ")
    return str(longrepr) if longrepr else ""


def _skip_location(report) -> str:
    longrepr = getattr(report, "longrepr", None)
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return f"{longrepr[0]}:{longrepr[1]}"
    return ""


def _holds_tests(path: Path) -> bool:
    """Does this module define anything pytest would collect?

    An AST read, not an import: a module that cannot be imported still has to be
    accounted for, and this must not be fooled into running anything.
    """
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError):
        return True  # unreadable is not the same as empty; let it be accounted for
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test"
        ):
            return True
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            return True
    return False


class CensusFailed(RuntimeError):
    """Collection did not finish, so there is nothing to report.

    This exists because the alternative is worse than an error. While this tool
    was being written a dataclass ``__eq__`` made its own plugin unhashable;
    pytest died in ``pytest_sessionstart`` and the census reported **0 selected,
    0 module skips, 0 expected outcomes** against the real suite, in the confident
    tone of a measurement. An instrument that answers zero when it has measured
    nothing is the shape this whole arc is about.
    """


def take_census(paths: list[str]) -> dict:
    """Collect (never run) and return both terms of the identity.

    Raises :class:`CensusFailed` when collection did not finish — a mistyped path,
    a broken plugin — rather than reporting zeros as though they were counted.
    """
    import pytest  # deferred: the tool is importable without a pytest session

    plugin = _Plugin()
    argv = ["--collect-only", "-q", "-p", "no:cacheprovider", *paths]
    # Collection prints the whole item list; this tool's stdout is its report.
    with contextlib.redirect_stdout(io.StringIO()) as noise:
        status = pytest.main(argv, plugins=[plugin])

    # pytest 9 fires pytest_collection_finish even on a usage error, so the hook
    # alone does not tell you a census happened. These two exit codes mean nothing
    # was measured: 3 an internal error (the unhashable-plugin case above), 4 a
    # usage error (a mistyped path). Exit 5 — collected nothing — is a real zero
    # and is reported as one.
    if not plugin.finished or int(status) in (3, 4):
        raise CensusFailed(
            f"collection did not complete (pytest exit {int(status)}); "
            "no census was taken.\n" + noise.getvalue().strip()[-2000:]
        )

    per_file: dict[str, int] = {}
    for nodeid in plugin.selected:
        per_file[nodeid.split("::")[0]] = per_file.get(nodeid.split("::")[0], 0) + 1
    deselected_files = {nodeid.split("::")[0] for nodeid in plugin.deselected}
    skipped_files = {skip["path"] for skip in plugin.module_skips}
    errored_files = {nodeid.split("::")[0] for nodeid in plugin.collect_errors}

    unaccounted = []
    for target in paths:
        base = Path(target)
        if not base.is_dir():
            continue
        for module in sorted(base.rglob("test_*.py")):
            if "__pycache__" in module.parts:
                continue
            try:
                rel = str(module.resolve().relative_to(plugin.rootpath))
            except ValueError:
                rel = str(module)
            if rel in per_file or rel in skipped_files or rel in deselected_files:
                continue
            if rel in errored_files or not _holds_tests(module):
                continue
            unaccounted.append(rel)

    # A collection error is NOT one more outcome. Measured: pytest reports
    # "Interrupted: 1 error during collection", runs nothing at all, and
    # summarises "1 error" — so a suite with one is a suite that does not run, and
    # it has no headline to publish. (Under --continue-on-collection-errors, which
    # this project does not use, each error would instead join the identity as one
    # more outcome beside the module skips.)
    can_run = not plugin.collect_errors
    return {
        "suite_can_run": can_run,
        "selected": len(plugin.selected),
        "deselected": len(plugin.deselected),
        "module_skips": len(plugin.module_skips),
        "module_skips_detail": plugin.module_skips,
        "collect_errors": len(plugin.collect_errors),
        "collect_errors_detail": plugin.collect_errors,
        "expected_outcomes": (
            len(plugin.selected) + len(plugin.module_skips) if can_run else None
        ),
        "per_file": per_file,
        "unaccounted_modules": unaccounted,
        "rootdir": str(plugin.rootpath),
        "collection_status": int(status),
    }


# --------------------------------------------------------------------------- #
# Reporting                                                                   #
# --------------------------------------------------------------------------- #


def _render(census: dict, run: dict | None) -> tuple[str, bool]:
    lines = [
        "Suite census — the headline, derived",
        f"  rootdir                {census['rootdir']}",
        f"  selected items         {census['selected']}",
        f"  deselected (not run)   {census['deselected']}",
        f"  module-level skips     {census['module_skips']}",
    ]
    # Grouped by gate, the way pytest's own "SKIPPED [13] ..." reports it: one
    # gate shutting thirteen modules is one fact, not thirteen.
    by_gate: dict[tuple[str, str], list[str]] = {}
    for skip in census["module_skips_detail"]:
        by_gate.setdefault((skip["reason_location"], skip["reason"]), []).append(skip["path"])
    for (location, reason), modules in by_gate.items():
        lines.append(f"      [{len(modules)}] {location}")
        lines.append(f"          {reason}")
        lines += [f"            {name}" for name in modules]
    if census["suite_can_run"]:
        lines += [
            "",
            f"  EXPECTED OUTCOMES      {census['expected_outcomes']}"
            f"   (= {census['selected']} selected + {census['module_skips']} module skips)",
        ]
    else:
        lines += [
            f"  collection errors      {census['collect_errors']}",
            *[f"      {nodeid}" for nodeid in census["collect_errors_detail"]],
            "",
            "  NO HEADLINE. A collection error does not add an outcome — it aborts",
            "  the session: pytest reports the error and runs nothing. Fix the",
            "  import before asking what this suite's total is.",
        ]
    if census["unaccounted_modules"]:
        lines += [
            "",
            "  UNACCOUNTED test modules — present, contributing nothing, and "
            "nothing says why:",
        ]
        lines += [f"      {name}" for name in census["unaccounted_modules"]]

    ok = bool(census["suite_can_run"])
    if run is not None and census["suite_can_run"]:
        lines += ["", f"Against the recorded run: {run['line']}"]
        for bucket in OUTCOME_BUCKETS:
            if run[bucket]:
                lines.append(f"  {bucket:<22} {run[bucket]}")
        lines.append(f"  reported outcomes      {run['outcomes']}")
        ok = run["outcomes"] == census["expected_outcomes"]
        if ok:
            lines.append(
                f"  RECONCILES             {run['outcomes']} == "
                f"{census['selected']} + {census['module_skips']}"
            )
        else:
            delta = run["outcomes"] - census["expected_outcomes"]
            lines += [
                f"  DOES NOT RECONCILE     off by {delta:+d}",
                "  Before suspecting the count, check the two things that moved it",
                "  last time: a browser-gated module (the suite has no fixed size),",
                "  and a run measured on a different tree than the collection.",
            ]
    return "\n".join(lines), ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        default=[str(ROOT / "tests")],
        help="what to census (default: this project's tests/)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON on stdout")
    parser.add_argument(
        "--against",
        metavar="FILE",
        help="a file holding a pytest run's output; reconcile it and exit 1 if it fails",
    )
    args = parser.parse_args(argv)

    try:
        census = take_census(args.paths)
    except CensusFailed as failure:
        print(failure, file=sys.stderr)
        return 3

    run = None
    if args.against:
        run = parse_summary(Path(args.against).read_text())
        if run is None:
            print(f"no pytest summary line found in {args.against}", file=sys.stderr)
            return 2
        census["run"] = run

    reconciles = run is None or run["outcomes"] == census["expected_outcomes"]
    if args.json:
        print(json.dumps(census, indent=2))
        return 0 if census["suite_can_run"] and reconciles else 1

    report, ok = _render(census, run)
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
