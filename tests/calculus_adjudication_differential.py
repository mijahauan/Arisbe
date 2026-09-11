"""Adjudication of the differential layer (spec 2026-09-10 §5.4, §6; Task 9).
The sibling of calculus_adjudication, _structure and _soundness.

Not a test. It regenerates every figure the differential layer's P-K4 outcome
states, groups any disagreement by source graph with its smallest separating
structure, and shows the instrument bites before its silence means anything:

    uv run python tests/calculus_adjudication_differential.py               # default bounds
    uv run python tests/calculus_adjudication_differential.py --exhaustive  # figures only (Task 10)

Figures (the semantics budget is the mode's own, calculus_run.MODES):
  columns            the layer's counted columns (agree / disagree / unknown, x exhaustive / sampled)
  tarski             tarski's verdicts over the same structures (TRUE / FALSE)
  semantic_game      semantic_game's verdicts (true / false / unknown)
  features           tier-A graphs carrying an identity edge, a constant, a cut, a generic
                     vertex, a 0-ary relation
  bite:no_diagonal   disagreements when the facts graph omits the diagonal (= u u) —
                     semantic_game reads `=` as an ordinary relation, so the encoding owes it
  bite:open_world    semantic_game's verdicts with the same oracle declared open (UNKNOWN
                     then appears; the closed flag is what makes the comparison possible)
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

for _p in (Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent / "src"):
    if str(_p) not in sys.path:     # run as a script, not under pytest's pythonpath
        sys.path.insert(0, str(_p))

from frozendict import frozendict  # noqa: E402

from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, tier_a  # noqa: E402
from calculus_run import MODES  # noqa: E402
from domain_oracle import CorpusOracle  # noqa: E402
from egi_core_dau import Edge, RelationalGraphWithCuts  # noqa: E402
from egif_generator_dau import generate_egif  # noqa: E402
from semantic_game import Verdict3, evaluate  # noqa: E402
from tarski import satisfies, universe, vocabulary  # noqa: E402
from test_calculus_differential import facts_graph  # noqa: E402

G = RelationalGraphWithCuts


def without_diagonal(s) -> G:
    """The facts graph with the (= u u) edges removed — the falsifier."""
    f = facts_graph(s)
    keep = [e for e in f.nu if f.rel[e] != "="]
    return G(V=f.V, E=frozenset(Edge(e) for e in keep), nu=frozendict({e: f.nu[e] for e in keep}),
             sheet=f.sheet, Cut=frozenset(),
             area=frozendict({f.sheet: frozenset([*(v.id for v in f.V), *keep])}),
             rel=frozendict({e: f.rel[e] for e in keep}))


def _egif(x):
    try:
        return generate_egif(x) or "(blank)"
    except Exception as exc:        # a sample line, never a figure
        return f"<{type(exc).__name__}>"


def adjudicate(bounds, sem):
    figs = defaultdict(Counter)
    disagreements = defaultdict(list)       # gname -> [(size, structure, tarski, semantic_game)]
    egifs = {}
    for gname, g in tier_a(bounds).graphs:
        rels, consts = vocabulary(g)
        f = figs["features"]
        f["graphs"] += 1
        f["identity_edge"] += any(g.rel[e] == "=" for e in g.nu)
        f["constant"] += bool(consts)
        f["cut"] += bool(g.Cut)
        f["generic_vertex"] += any(v.is_generic for v in g.V)
        f["zero_ary"] += any(len(g.nu[e]) == 0 for e in g.nu)
        for n in sem.sizes:
            us, exh = universe(rels, consts, n, cap=sem.tuple_cap, sample_n=sem.sample_n,
                               seed=sem.seed, una=True)
            for s in us:
                ours = satisfies(g, s)
                theirs = evaluate(g, CorpusOracle([("M", facts_graph(s))], closed=True)).verdict
                figs["tarski"][str(ours).upper()] += 1
                figs["semantic_game"][theirs.value] += 1
                if theirs is Verdict3.UNKNOWN:
                    col = "unknown"
                elif (theirs is Verdict3.TRUE) == ours:
                    col = "agree"
                else:
                    col = "disagree"
                    disagreements[gname].append((n, repr(s), ours, theirs.value))
                    egifs[gname] = _egif(g)
                figs["columns"][f"{col}:{'exhaustive' if exh else 'sampled'}"] += 1
                bare = evaluate(g, CorpusOracle([("M", without_diagonal(s))], closed=True)).verdict
                if bare is not Verdict3.UNKNOWN and (bare is Verdict3.TRUE) != ours:
                    figs["bite"]["no_diagonal_disagree"] += 1
                opened = evaluate(g, CorpusOracle([("M", facts_graph(s))], closed=False)).verdict
                figs["bite"][f"open_world_{opened.value}"] += 1
    return figs, disagreements, egifs


def main(argv):
    exhaustive = "--exhaustive" in argv
    mode = MODES["exhaustive" if exhaustive else "default"]
    print(f"bounds={mode.name} semantics={mode.sem}")
    figs, dis, egifs = adjudicate(EXHAUSTIVE_BOUNDS if exhaustive else DEFAULT_BOUNDS, mode.sem)
    for name in ("columns", "tarski", "semantic_game", "features", "bite"):
        print(f"{name:14s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[name].items())))
    for gname in sorted(dis, key=lambda k: (len(egifs[k]), egifs[k])):
        n, s, ours, theirs = min(dis[gname], key=lambda d: (d[0], len(d[1]), d[1]))
        print(f"DISAGREE {gname}: {len(dis[gname])} structure(s); {egifs[gname]}  |  "
              f"tarski {ours}, semantic_game {theirs} on {s}")
    print(f"disagreements: {sum(map(len, dis.values()))} in {len(dis)} graph(s)")


if __name__ == "__main__":
    main(sys.argv[1:])
