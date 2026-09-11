"""Differential (spec 2026-09-10 §5.4): Agon's evaluator measured against a
fresh reading of Dau's semantics, on every tier-A graph."""
import functools
import hashlib

import pytest
from frozendict import frozendict

from calculus_enum import tier_a
from calculus_ledger import Failure, assert_extent, check_ledger, ledgered
from calculus_run import MODES
from domain_oracle import CorpusOracle
from egi_core_dau import Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from semantic_game import Verdict3, evaluate
from tarski import Structure, satisfies, universe, vocabulary

G = RelationalGraphWithCuts


def facts_graph(s: Structure) -> G:
    names = {i: n for n, i in s.const.items()}
    V = [Vertex(f"m{i}", label=names.get(i, f"u{i}"), is_generic=False) for i in range(s.size)]
    nu, rel = {}, {}

    def add(r, t):
        eid = f"f{len(nu)}"
        nu[eid] = tuple(f"m{i}" for i in t)
        rel[eid] = r

    for r in sorted(s.ext):
        for t in sorted(s.ext[r]):
            add(r, t)
    for i in range(s.size):
        add("=", (i, i))
    return G(V=frozenset(V), E=frozenset(Edge(e) for e in nu), nu=frozendict(nu), sheet="S",
             Cut=frozenset(), area=frozendict({"S": frozenset([*(v.id for v in V), *nu])}),
             rel=frozendict(rel))


def test_the_encoding_round_trips_through_semantic_game():
    s = Structure(2, {"a": 0}, {"P": {(0,)}})
    oracle = CorpusOracle([("M", facts_graph(s))], closed=True)
    assert evaluate(parse_egif('(P "a")'), oracle).verdict is Verdict3.TRUE
    assert evaluate(parse_egif("[*x] ~[ (P x) ]"), oracle).verdict is Verdict3.TRUE


@functools.lru_cache(maxsize=None)
def _compare(mode_name: str):
    mode = MODES[mode_name]
    sem = mode.sem
    known = ledgered("differential")
    counts, failures, evaluated = {}, [], set()
    oracles = {}
    for gname, g in tier_a(mode.bounds).graphs:
        rels, consts = vocabulary(g)
        for n in sem.sizes:
            us, exh = universe(rels, consts, n, cap=sem.tuple_cap, sample_n=sem.sample_n,
                               seed=sem.seed, una=True)
            for s in us:
                if s not in oracles:
                    oracles[s] = CorpusOracle([("M", facts_graph(s))], closed=True)
                ours = satisfies(g, s)
                theirs = evaluate(g, oracles[s]).verdict
                key = f"A|{gname}|diff|{hashlib.sha256(repr(s).encode()).hexdigest()[:12]}"
                if theirs is Verdict3.UNKNOWN:
                    col = "unknown"
                elif (theirs is Verdict3.TRUE) == ours:
                    col = "agree"
                else:
                    col = "disagree"
                    failures.append(Failure("differential", key,
                                            f"tarski {ours}, semantic_game {theirs.value} on {s}"))
                if col != "unknown" and key in known:
                    evaluated.add(key)
                label = f"{col}:{'exhaustive' if exh else 'sampled'}"
                counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items())), failures, evaluated


def _layer(mode):
    counts, failures, evaluated = _compare(mode)
    problems = check_ledger("differential", evaluated, failures)
    assert not problems, "\n\n".join(problems)


def test_differential():
    _layer("default")


def test_differential_extent():
    assert_extent("default:differential", _compare("default")[0])


@pytest.mark.exhaustive
def test_differential_exhaustive():
    _layer("exhaustive")


@pytest.mark.exhaustive
def test_differential_extent_exhaustive():
    assert_extent("exhaustive:differential", _compare("exhaustive")[0])
