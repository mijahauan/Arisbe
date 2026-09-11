"""P-K1 (spec 2026-09-10 §7), operationalized in docs/superpowers/plans/
2026-09-10-calculus-property-suite.md Task 3 before it was run.

The recorded outcome is pinned: if a change moves it, this fails and the
change must be read, not the number updated.
"""
import pytest

from calculus_pk1 import pk1

RECORDED_OUTCOME = ("REFUTED: premise — colore_field is not an EGI (Def 12.5); "
                     "the round trip repairs it")


@pytest.mark.exhaustive
def test_pk1_outcome_is_the_recorded_one():
    result = pk1()
    print(result)
    assert RECORDED_OUTCOME is not None, f"record the outcome: {result['outcome']!r}"
    assert result["outcome"] == RECORDED_OUTCOME
