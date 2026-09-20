"""The admission scan — can this test fail?

The author's principle (2026-09-19): residence in the canonical corpus is *earned*
by passing a formal Dau threshold. A work in progress that is not yet well-formed
belongs in Ergasterion; a graph that loses the EPG may still teach the shape of a
mistake; a graph once accepted and since falsified has its own place in a UoD's
history. What the principle forbids is ink sitting in the canonical corpus that
never passed the gate.

"Our testing of candidates and code must also pass a similar gate." A test that
**cannot fail** has passed no gate at all, and it is residing in the canonical
suite — where it is counted in every "N passing" figure the project quotes.

This module is the mechanical half of clause 1 of that gate: *it can fail*. It is
deliberately a pure AST reader — it imports nothing from ``src/`` and executes no
test — so it can be run over a suite that does not import cleanly, and so it can
never be fooled by the code it is judging.

Clause 2 (*it is reached* — a check that skips on every parameter measures
nothing) is enforced per-suite where the parametrization lives; see
``test_corpus_polarity_discipline.test_every_recorded_act_is_reachable_by_this_gate``
for the first instance. Clause 3 (*it measures what it claims*) is a reading
task, not a scan, and is tracked in ``tasks/todo.md``.

**What counts as being able to fail.** Any one of:

* a plain ``assert`` that is not ``assert True``;
* a ``unittest``-style ``self.assertX(...)`` or ``self.fail(...)``;
* ``pytest.raises`` / ``pytest.fail``;
* an explicit ``raise``;
* a call to a helper that itself asserts — in the same file *or* in any sibling
  test module (``assert_extent`` in ``calculus_run`` is a real check);
* **a call that can raise**, outside any swallowing handler. A does-not-raise
  test is a weak test but not a vacuous one: ``attest_correspondence(egi, dto)``
  with nothing after it fails the moment attestation refuses.

**...and what does not.** An assertion inside a ``try`` whose handler cannot
re-raise is not an assertion: the failure is caught and printed. That is the
dominant shape in the legacy block this scan was written to find —

    equal, message = self._validate_egi_equality(before, after)
    print(f"round-trip fidelity: {equal}")     # a False prints, and passes

So the criterion is sharp: a test is inadmissible when **no outcome of the code
under test can fail it** — no effective assertion, *and* every call that could
raise sits inside a handler that swallows it. Calls to obvious builtins
(``print``, ``len``, ``str``, …) do not count as able to raise, or every
``print`` would vouch for its own test.

A fixture that asserts is *not* counted, deliberately. It would make the scan
depend on collection and on conftest resolution, and a test whose only check
lives in a fixture is one the fixture is testing, not the test.

The scan is intentionally conservative: every rule above is a reason to call a
test *admissible*. A test this scan flags is one no reading has been able to
defend, which is why the ledger asks for a written reason rather than a flag.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List, NamedTuple

TESTS_ROOT = Path(__file__).resolve().parent
LEDGER_PATH = TESTS_ROOT / "admission_ledger.json"


class Inadmissible(NamedTuple):
    """One test that cannot fail."""

    test_id: str        # "<file stem>::<qualified function name>"
    path: str           # repo-relative
    lineno: int
    reason: str         # the shape, mechanically determined


def _swallowing_tries(fn: ast.AST) -> List[ast.Try]:
    """Every ``try`` under ``fn`` with a handler that cannot re-raise.

    An assertion inside one of these cannot fail the test: the ``AssertionError``
    is caught by ``except Exception`` and (typically) printed.
    """
    out: List[ast.Try] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if not any(isinstance(s, ast.Raise) for s in ast.walk(handler)):
                    out.append(node)
                    break
    return out


def _asserting_helpers(tree: ast.Module) -> set:
    """Non-test functions in this module that assert — calling one is a real check."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                continue
            body = ast.unparse(node)
            if "assert" in body or "pytest.fail" in body:
                out.add(node.name)
    return out


# Builtins whose use should never vouch for a test: a `print` must not make its
# own test look able to fail.
_BENIGN = {
    "print", "len", "str", "repr", "format", "range", "enumerate", "sorted",
    "list", "dict", "set", "tuple", "frozenset", "int", "float", "bool", "sum",
    "min", "max", "abs", "any", "all", "zip", "map", "filter", "isinstance",
    "issubclass", "getattr", "hasattr", "setattr", "type", "id", "hash",
    "append", "extend", "add", "update", "join", "split", "strip", "keys",
    "values", "items", "get", "copy", "lower", "upper", "startswith",
    "endswith", "replace", "count", "index", "sort", "pop", "insert",
}


def _asserting_helpers_across_suite(root: Path) -> set:
    """Asserting helper names from *every* test module — a test may import its
    check (``assert_extent`` lives in ``calculus_run``, not beside its callers)."""
    out: set = set()
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        out |= _asserting_helpers(tree)
    return out


def _can_raise_outside_a_swallow(fn: ast.AST, swallowed: list) -> bool:
    """Is there a call that could raise, outside any swallowing handler?

    Such a test fails when the code under test misbehaves, even with no
    assertion — the ``attest_correspondence(egi, dto)  # raises on failure``
    shape. Weak, but not vacuous.
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call) or node in swallowed:
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else None)
        if name is None or name in _BENIGN:
            continue
        return True
    return False


def _qualname(tree: ast.Module, target: ast.AST) -> str:
    """``Class.method`` where it applies, else the bare function name."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if child is target:
                    return f"{node.name}.{target.name}"
    return target.name


def scan_file(path: Path, suite_helpers: set = None) -> List[Inadmissible]:
    """Every test in ``path`` that cannot fail."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    helpers = _asserting_helpers(tree) | (suite_helpers or set())
    found: List[Inadmissible] = []

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test"):
            continue

        text = ast.unparse(fn)
        if "pytest.raises" in text or "pytest.fail" in text:
            continue
        if any(isinstance(r, ast.Raise) for r in ast.walk(fn)):
            continue

        swallowed = [a for t in _swallowing_tries(fn) for a in ast.walk(t)]

        effective = [
            a for a in ast.walk(fn)
            if isinstance(a, ast.Assert)
            and not (isinstance(a.test, ast.Constant) and a.test.value is True)
            and a not in swallowed
        ]
        if effective:
            continue

        unittest_checks = [
            c for c in ast.walk(fn)
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
            and (c.func.attr.startswith("assert") or c.func.attr == "fail")
            and c not in swallowed
        ]
        if unittest_checks:
            continue

        called = {
            c.func.id for c in ast.walk(fn)
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
        }
        if called & helpers:
            continue

        # A call that can raise, outside any swallowing handler, fails the test
        # when the code under test misbehaves. Weak, but not vacuous.
        if _can_raise_outside_a_swallow(fn, swallowed):
            continue

        # Name the shape, so the ledger entry can be read without the source.
        asserts = [a for a in ast.walk(fn) if isinstance(a, ast.Assert)]
        if not asserts and not unittest_checks:
            reason = "no assertion, and every call that could raise is swallowed"
        elif all(isinstance(a.test, ast.Constant) and a.test.value is True
                 for a in asserts):
            reason = "only `assert True`"
        else:
            reason = "every assertion sits inside a try whose handler swallows it"

        try:
            shown = str(path.relative_to(TESTS_ROOT.parent))
        except ValueError:      # a path outside the repo (the falsifier fixture)
            shown = str(path)

        found.append(Inadmissible(
            test_id=f"{path.stem}::{_qualname(tree, fn)}",
            path=shown,
            lineno=fn.lineno,
            reason=reason,
        ))

    return found


def scan_suite(root: Path = TESTS_ROOT) -> List[Inadmissible]:
    """Every test in the suite that cannot fail, sorted for a stable diff."""
    suite_helpers = _asserting_helpers_across_suite(root)
    out: List[Inadmissible] = []
    for path in sorted(root.rglob("test_*.py")):
        out.extend(scan_file(path, suite_helpers))
    return sorted(out, key=lambda f: f.test_id)


def load_ledger(path: Path = LEDGER_PATH) -> Dict[str, dict]:
    """The recorded inadmissibles — each with a written reason and a status."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["entries"]
