"""The test-admission gate — clause 1: can this test fail?

The author's principle (2026-09-19): admission to the canonical corpus is gated,
and residence in a UoD means passing a formal Dau threshold. A work in progress
that is not yet well-formed belongs in Ergasterion. A graph that *loses* the EPG
may still teach the shape of a mistake. A graph once accepted and since falsified
has its own status in the history of a UoD. What the principle forbids is ink
sitting in the canonical corpus that never passed the gate.

"In our provision of exemplars, they must pass this gate. Our testing of
candidates and code must also pass a similar gate."

A test that **cannot fail** has passed no gate at all — and it is counted in
every "N passing" figure the project quotes. When this gate was first run it
found **72** such tests, 10 of them inside the 152-test core suite that
``tools/quality_gate_system.py`` runs and that CLAUDE.md says "must always pass";
nine of those ten are the whole of ``test_chapter15_formal_calculus.py``, the
file named for the chapter that defines the six transformation rules.

The gate's three clauses, mirroring the threshold:

1. **It can fail.** Measured here, mechanically, by ``admission_scan``.
2. **It is reached.** A check that skips on every parameter measures nothing.
   Enforced where the parametrization lives — see
   ``test_corpus_polarity_discipline.test_every_recorded_act_is_reachable_by_this_gate``.
3. **It measures what it claims.** A reading task, not a scan (the re-emission
   shape: a weaker check counted toward a stronger claim). Tracked in
   ``tasks/todo.md``.

**Ledger semantics, deliberately the same as ``tests/calculus_ledger.json``** —
the idiom this project already trusts. A newly inadmissible test fails as **new**.
A repaired one fails with **"shrink this entry"**, so a fix cannot land silently
and a stale entry cannot linger. Nothing is ever deleted from the ledger to make
the suite green; an entry leaves only by being *earned* out.
"""

from __future__ import annotations

import json

from admission_scan import LEDGER_PATH, scan_suite


def _ledger() -> dict:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def test_no_new_test_that_cannot_fail():
    """A test that cannot fail may not enter the suite unrecorded.

    This is the standing half of the gate. It does not demand that the existing
    debt be paid today; it demands that the debt stop growing.
    """
    ledger = _ledger()["entries"]
    found = {f.test_id: f for f in scan_suite()}
    new = sorted(set(found) - set(ledger))
    assert not new, (
        f"{len(new)} test(s) that CANNOT FAIL entered the suite:\n  "
        + "\n  ".join(f"{t}  ({found[t].path}:{found[t].lineno}) — {found[t].reason}"
                      for t in new)
        + "\n\nA test that cannot fail has passed no gate. Give it a real "
          "assertion, or record it in tests/admission_ledger.json with a written "
          "reason and a status.")


def test_a_repaired_test_is_read_off_the_ledger():
    """A ledger entry that now CAN fail must be removed — 'shrink this entry'.

    Without this, a repair reads as no change at all, and the ledger drifts into
    a list of things that used to be true. It is the exact discipline
    `calculus_ledger.json` enforces, and the reason this arc could prove its
    fixes rather than assert them.
    """
    ledger = _ledger()["entries"]
    found = {f.test_id for f in scan_suite()}
    repaired = sorted(set(ledger) - found)
    assert not repaired, (
        f"{len(repaired)} ledgered test(s) can now fail — shrink this entry:\n  "
        + "\n  ".join(repaired)
        + "\n\nRemove them from tests/admission_ledger.json and update its "
          "_counts. A repair must show up as a change.")


def test_the_ledger_counts_match_its_entries():
    """The headline numbers are derived, never narrated.

    Standing rule 4 of this project: "A narrated number is generated or asserted.
    A figure that lives only in prose is a figure nobody is keeping."
    """
    doc = _ledger()
    entries, counts = doc["entries"], doc["_counts"]
    assert counts["total"] == len(entries)
    for status in ("in_the_core_gate", "validation_theatre", "unclassified"):
        actual = sum(1 for v in entries.values()
                     if v["status"] == status.replace("_", "-"))
        assert counts[status] == actual, (
            f"_counts.{status} says {counts[status]}, entries say {actual}")


def test_every_ledger_entry_carries_a_written_reason():
    """A flag is not a reason. An entry says which shape it is and what it is for.

    The statuses are the author's own taxonomy: `in-the-core-gate` (a non-test
    certifying the calculus — the thing the principle most forbids),
    `validation-theatre` (keeps value as an exhibit of the shape, earns no
    residence), `unclassified` (scanned, not yet read).
    """
    allowed = {"in-the-core-gate", "validation-theatre", "unclassified"}
    for test_id, entry in _ledger()["entries"].items():
        assert entry.get("status") in allowed, f"{test_id}: bad status"
        assert entry.get("note", "").strip(), f"{test_id}: no written reason"
        assert entry.get("shape", "").strip(), f"{test_id}: no shape recorded"


def test_the_scan_catches_a_test_that_cannot_fail():
    """The instrument is shown to bite before its silence means anything.

    Three shapes, hand-built: a swallowed assertion, `assert True` alone, and a
    body whose only call is swallowed. Plus two that must NOT be flagged — an
    imported asserting helper, and a does-not-raise test — because a scan that
    over-reports would fill the ledger with tests that are fine.
    """
    import tempfile
    from pathlib import Path

    from admission_scan import _asserting_helpers_across_suite, scan_file

    source = '''
def helper_that_asserts(x):
    assert x

def test_swallowed():
    try:
        assert 1 == 2
    except Exception as e:
        print(e)

def test_only_true():
    print("ok")
    assert True

def test_swallowed_call():
    try:
        compute_something()
    except Exception as e:
        print(e)

def test_uses_an_asserting_helper():
    helper_that_asserts(compute_something())

def test_does_not_raise():
    attest_correspondence(1, 2)
'''
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "test_fixture.py"
        p.write_text(source)
        flagged = {f.test_id.split("::")[1]
                   for f in scan_file(p, _asserting_helpers_across_suite(Path(d)))}

    assert flagged == {"test_swallowed", "test_only_true", "test_swallowed_call"}, (
        f"the scan flagged {sorted(flagged)}")
