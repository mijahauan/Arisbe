"""``certify`` in observe mode, and the gate of Phase 2.

The directive's gate: *the kernel rejects exactly the moves the ledger's SEVERE,
DIFFERS and NOT-AN-EQUIVALENCE entries describe, and nothing else.* It is stated
here over the calculus suite's default run, where every move reaches the engine
through ``calculus_certify.certify`` and carries the certificate that came back.

What that sentence covers and what it does not: the suite drives the protocol
for the six rules (and the other ways in for the rules only they serve), so the
gate is a statement about those paths. The engine called directly and the game
engine's way in are measured by ``tests/test_certify_paths.py`` instead.
"""
from collections import Counter

import pytest

import calculus_certify
import dau_kernel
from calculus_certify import Act, CalculusViolation, certify, name_move
from calculus_classifiers import failure_kind
from calculus_run import run
from dau_kernel import ACCEPTED, REJECTED, UNJUDGED, Move
from egif_parser_dau import parse_egif


@pytest.fixture(scope="module")
def observed():
    """Every applied move of the default run, by key: the kernel's verdict on
    it, and the kinds of failure the three layers found on it."""
    result = run("default")
    verdicts = result.verdicts
    moves = {key: key.split("|")[2] for key in verdicts}
    kinds = {}
    for layer, result in result.layers.items():
        for failure in result.failures:
            kinds.setdefault(failure.key, set()).add(failure_kind(layer, failure.detail))
    return verdicts, kinds, moves


def test_every_applied_move_is_certified_and_the_kernel_never_crashes(observed):
    verdicts, _kinds, _moves = observed
    statuses = Counter(s for ss in verdicts.values() for s in ss)
    assert set(statuses) <= {ACCEPTED, REJECTED, UNJUDGED}, statuses
    assert statuses[ACCEPTED] and statuses[REJECTED] and statuses[UNJUDGED]


def test_one_instance_key_gets_one_verdict(observed):
    """The ledger is keyed by instance. If two moves sharing a key were judged
    differently, the comparison below would be about keys and not about moves."""
    verdicts, _kinds, _moves = observed
    assert {k: v for k, v in verdicts.items() if len(v) != 1} == {}


GATE_KINDS = {"SEVERE", "DIFFERS", "NOT AN EQUIVALENCE"}


def test_the_kernel_rejects_exactly_what_the_ledger_describes(observed):
    """The gate. Left side: the instances the kernel rejected. Right side: the
    instances on which a layer recorded a failure of one of the three kinds —
    all of them ledgered, since the suite is green."""
    verdicts, kinds, moves = observed
    rejected = {k for k, v in verdicts.items() if v == {REJECTED}}
    described = {k for k, ks in kinds.items() if ks & GATE_KINDS and k in verdicts}
    only_kernel = Counter(moves[k] for k in rejected - described)
    only_ledger = Counter(moves[k] for k in described - rejected)
    assert (only_kernel, only_ledger) == (Counter(), Counter()), (
        f"rejected by the kernel and described by no such entry: {dict(only_kernel)}; "
        f"described by an entry and not rejected: {dict(only_ledger)}")
    assert rejected, "the kernel rejected nothing: the comparison is empty"


def test_the_failure_kinds_are_the_ones_the_gate_names(observed):
    """The gate names three kinds. If the layers grow a fourth that describes
    an applied move, the gate must be re-read rather than quietly pass."""
    _verdicts, kinds, _moves = observed
    assert set().union(*kinds.values()) <= GATE_KINDS | {"INCOMPLETE"}


# -- naming ------------------------------------------------------------------

def _ids(g):
    edge = next(iter(g.nu))
    return edge, g.nu[edge][0] if g.nu[edge] else None


def test_a_request_is_named_by_dau_s_rule_not_the_engine_s():
    g = parse_egif("[*x] ~[ (P *y) ]")
    lone = next(v.id for v in g.V if not dau_kernel.edges_on(g, v.id))
    cut = next(c.id for c in g.Cut)
    edge, y = _ids(g)
    assert name_move(g, "HEAVY_DOT", (), cut) == Move("VERTEX_INS", (), cut)
    assert name_move(g, "ERA", [lone]) == Move("VERTEX_ERA", (lone,))
    assert name_move(g, "ERA", [y]).rule == "ERA"            # a vertex with an edge on it
    assert name_move(g, "ERA", [edge], target=cut) == Move("ERA", (edge,))   # Dau's ERA has no target
    assert name_move(g, "INS", (), cut, "(Q *z)") == Move("INS", (), cut, "(Q *z)")


def test_a_double_cut_with_no_spot_is_named_as_the_engine_reads_it():
    """R4: the convenience is kept, and what it enclosed is recorded."""
    g = parse_egif("(P *x) ~[ (Q *y) ]")
    q = next(e for e in g.nu if g.rel[e] == "Q")
    cut = next(c.id for c in g.Cut)
    assert name_move(g, "DC+", [q]) == Move("DC+", (q,), cut)
    whole = name_move(g, "DC+", [])
    assert whole.target == g.sheet and set(whole.selection) == set(g.area[g.sheet])


# -- the door ----------------------------------------------------------------

def test_certify_returns_the_engine_s_graph_and_an_accepted_certificate():
    g = parse_egif("(P *x)")
    edge, _ = _ids(g)
    h, cert = certify(g, Act("protocol", "DC+", (edge,), g.sheet))
    assert cert.accepted and cert.steps == (Move("DC+", (edge,), g.sheet),)
    assert len(h.Cut) == 2


def test_observe_mode_counts_a_rejection_and_changes_nothing():
    """ERA of an edge also erases the vertex it isolates — the ledger's
    ``era-also-erases-the-vertex-it-isolates``. The engine's result comes back
    untouched; the certificate says the kernel did not accept it."""
    g = parse_egif("(P *x)")
    edge, _ = _ids(g)
    before = calculus_certify.OBSERVED.counts[("protocol", "ERA", "ERA", REJECTED)]
    h, cert = certify(g, Act("protocol", "ERA", (edge,)))
    assert cert.status == REJECTED and "differs from the licensed change" in cert.why
    assert len(h.V) == 0                       # the engine did what it does today
    assert calculus_certify.OBSERVED.counts[("protocol", "ERA", "ERA", REJECTED)] == before + 1


def test_enforce_mode_raises_on_the_same_move(monkeypatch):
    """The switch Phase 4 throws. Shown working now, so that throwing it is a
    one-line change whose effect is already known."""
    g = parse_egif("(P *x)")
    edge, _ = _ids(g)
    monkeypatch.setattr(calculus_certify, "MODE", "enforce")
    with pytest.raises(CalculusViolation) as caught:
        certify(g, Act("protocol", "ERA", (edge,)))
    assert caught.value.certificate.status == REJECTED
    h, cert = certify(g, Act("protocol", "DC+", (edge,), g.sheet))     # an accepted move still passes
    assert cert.accepted


def test_a_refusal_is_the_engine_s_own_and_carries_no_certificate():
    g = parse_egif("~[ (P *x) ]")
    edge, _ = _ids(g)
    with pytest.raises(AssertionError):        # ERA in a negative context
        certify(g, Act("protocol", "ERA", (edge,)))


def test_a_kernel_crash_is_counted_and_never_reaches_the_caller(monkeypatch):
    g = parse_egif("(P *x)")
    edge, _ = _ids(g)

    def broken(*_a, **_k):
        raise RuntimeError("the judge fell over")

    monkeypatch.setattr(dau_kernel, "check_step", broken)
    h, cert = certify(g, Act("protocol", "DC+", (edge,), g.sheet))
    assert cert.status == calculus_certify.KERNEL_CRASHED and len(h.Cut) == 2


# Every applied move of the default run, by Dau rule and the kernel's verdict.
# Generated, not narrated: `run("default").certified`, summed over the tiers.
# Phase 3's gate for each family is its `rejected` row falling to zero.
CERTIFIED_DEFAULT = {
    "DC+:accepted": 2117, "DC+:rejected": 2542, "DC+:unjudged": 79,
    "DC-:accepted": 29,
    "ERA:accepted": 1141, "ERA:rejected": 578, "ERA:unjudged": 3,
    "EXTEND_LIGATURE:accepted": 589, "EXTEND_LIGATURE:unjudged": 4,
    "INS:accepted": 1447,
    "IT+:accepted": 1661, "IT+:rejected": 514, "IT+:unjudged": 15,
    "IT-:accepted": 6,
    "MERGE_VERTICES:accepted": 29,
    "MOVE_BRANCHES:accepted": 1,
    "REARRANGE_LIGATURE:accepted": 10,
    "RETRACT_LIGATURE:accepted": 6,
    "SPLIT_VERTEX:accepted": 1837, "SPLIT_VERTEX:unjudged": 13,
    "VERTEX_ERA:accepted": 98, "VERTEX_ERA:rejected": 235, "VERTEX_ERA:unjudged": 1,
    "VERTEX_INS:accepted": 302,
}


def test_the_certificate_counts_are_pinned():
    """13,257 applied moves: 9,273 accepted, 3,869 rejected, 115 unjudged. The
    rejections are the refusal layer's 3,070 SEVERE and the structure layer's
    799 DIFFERS, move for move; four rules carry all of them."""
    counted = Counter()
    for key, n in run("default").certified.items():
        _tier, rule, status = key.split(":")
        counted[f"{rule}:{status}"] += n
    assert dict(counted) == CERTIFIED_DEFAULT
    by_status = Counter()
    for key, n in counted.items():
        by_status[key.split(":")[1]] += n
    assert by_status == {ACCEPTED: 9273, REJECTED: 3869, UNJUDGED: 115}


def test_the_rejections_are_the_two_layers_failures_move_for_move():
    result = run("default")
    kinds = Counter(failure_kind(layer, f.detail)
                    for layer, lr in result.layers.items() for f in lr.failures)
    rejected = sum(n for key, n in result.certified.items() if key.endswith(":" + REJECTED))
    assert rejected == kinds["SEVERE"] + kinds["DIFFERS"]
