"""Refusal agreement (spec 2026-09-10 §5.1): the engine refuses exactly what
Dau forbids. Known disagreements live in calculus_ledger.json, each with its
reason; a new one fails here, and so does a repaired one."""
import pytest

from calculus_ledger import assert_extent, check_ledger
from calculus_run import run


def _agree(mode):
    lr = run(mode).layers["refusal"]
    problems = check_ledger("refusal", lr.evaluated_ledgered, lr.failures)
    assert not problems, "\n\n".join(problems)


def _extent(mode):
    r = run(mode)
    assert_extent(f"{mode}:run", r.extent())
    assert_extent(f"{mode}:refusal", dict(sorted(r.layers["refusal"].counts.items())))


def test_refusal_agreement():
    _agree("default")


def test_refusal_extent():
    _extent("default")


@pytest.mark.exhaustive
def test_refusal_agreement_exhaustive():
    _agree("exhaustive")


@pytest.mark.exhaustive
def test_refusal_extent_exhaustive():
    _extent("exhaustive")
