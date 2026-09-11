"""Adjudication of the structure layer and the core's dominating-nodes check
(spec 2026-09-10 §5.2, §6; Task 7). The sibling of calculus_adjudication.

Not a test. It classifies every failing structure instance into its ledger
entry by mechanism, measures the figures the entries' reasons state, and on
request rewrites those entries' instance lists (other layers' entries are kept):

    uv run python tests/calculus_adjudication_structure.py               # figures only (default mode)
    uv run python tests/calculus_adjudication_structure.py --write       # + rewrite the ledger
    uv run python tests/calculus_adjudication_structure.py --exhaustive  # figures in the exhaustive mode

It walks calculus_run.records(mode) and classifies through calculus_classifiers;
--write replaces this script's entries' instance lists by kind (default) or their
pinned counts by kind (--exhaustive). The core-dominating and corpus-egi entries
are default-mode only (the core check runs on tier A at the default bounds; the
corpus guard on every tier-B source, which no mode changes).

Figures, per entry ("moves" = candidate moves, "keys" = distinct instance keys):
  illegal              moves legal() judges illegal (structure then checks EGI-hood and maps only)
  in_refusal_entry     keys that are also instances of the named refusal entry
  non_egi              the engine's result violates dominating nodes (Def 12.5)
  orphans_erased       the engine's result = Dau's erasure, then each vertex it left isolated erased
  closure_adds_orphans the engine's own closure (analyze_closure, for_erasure) adds exactly those vertices
  orphan_constant      moves where an erased orphan is a constant vertex (the rest are generic)
  sound                G ⊨ G′ at domain sizes 1–2 (exhaustive where tuple bits <= 12, else 256 samples)
  equivalent           G ⊨ G′ and G′ ⊨ G at those sizes
  equivalent_to_dau    G′ (engine) ≡ G′ (Dau's result) at those sizes
  same_context/deeper  where the IT+ target sits relative to the selection's context
  pulls_vertex/pulls_edge  what the engine's closure (analyze_closure, as ITPlusInteraction calls it) added
  explained            the engine's result = the suite's iteration of the engine's closed subgraph
                       (same context), or of it with its top-level vertices reused (deeper context)
  noop                 the engine's result is the source graph unchanged
Core dominating nodes: tier-A graphs, those with a line reaching into a cut, the
disagreements, and a hand-built non-EGI the core accepts.
Corpus graphs (corpus-egi): every tier-B source — UoD current graphs and chain
states — and, for each that is not an EGI, its Def 12.5 violating pairs and vertices.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

for _p in (Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent / "src"):
    if str(_p) not in sys.path:     # run as a script, not under pytest's pythonpath
        sys.path.insert(0, str(_p))

import eg_navigation as nav  # noqa: E402
from calculus_adjudication import P, _entail  # noqa: E402
from calculus_classifiers import classify as _classify, closed as _closed  # noqa: E402
from calculus_classifiers import failure_kind, orphans as _orphans  # noqa: E402
from calculus_enum import DEFAULT_BOUNDS, dominating_violations, tier_a, tier_b_sources  # noqa: E402
from calculus_expected import _g, iterate, remove  # noqa: E402
from calculus_layers import structure  # noqa: E402
from calculus_ledger import LEDGER, refresh_reasons, update_ledger  # noqa: E402
from calculus_rules import expand, tops  # noqa: E402
from calculus_run import records  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from tarski import dominating_nodes  # noqa: E402

LAYERS_OWNED = ("structure", "core-dominating", "corpus-egi")

# id -> (layer, rule, reason). Figures quoted are this script's, in the default mode.
REASONS = {
    "core-has-dominating-nodes-inverted": ("core-dominating", "graph",
        "Dau Def 12.5 (p.125): G has dominating nodes iff ctx(e) ≤ ctx(v) for every edge e and "
        "v ∈ V_e — the edge sits in the vertex's context or deeper (≤ is 'is enclosed by', Def "
        "12.2). The core's RelationalGraphWithCuts.has_dominating_nodes calls "
        "_context_dominates(ctx(e), ctx(v)), which walks UP from ctx(v) looking for ctx(e): it "
        "tests ctx(v) ≤ ctx(e), the converse. Measured by calculus_adjudication_structure: it "
        "answers False on every tier-A graph with a line reaching into a cut (9 of 208 at the "
        "default bounds, e.g. *x ~[ (P x) ]), and True on a hand-built non-EGI (an edge on the "
        "sheet whose vertex sits in a cut). Protected core, not edited; nothing in src/ relies on "
        "it (it is only printed by two __main__ demos). The suite uses tarski.dominating_nodes."),
    "corpus-graph-not-an-egi": ("corpus-egi", "graph",
        "Dau Def 12.7 (p.126) makes dominating nodes part of what an EGI is, and Def 12.5 "
        "(p.125) requires ctx(e) ≤ ctx(v) for every edge e and v ∈ V_e. Two stored corpus "
        "graphs break it — measured by calculus_adjudication_structure over every tier-B "
        "source (52 current graphs, 178 chain states): bfo_core:current (4 edge–vertex pairs on "
        "1 vertex) and colore_field:current (8 pairs on 2 vertices); no chain state does. They "
        "are exactly the linear-form round-trip residue (test_tomos_parsing.KNOWN_BROKEN): the "
        "stored graph is not an EGI and its round trip repairs it (P-K1's recorded outcome). "
        "Nothing else in the repository catches a non-EGI — the core does not enforce Def 12.5, "
        "and its own check is inverted (core-has-dominating-nodes-inverted). Not a rule defect: "
        "a standing guard over the corpus, and the rules' verdicts on these two sources are "
        "counted as not judged (legal() refuses to judge a non-EGI source)."),
    "dc-plus-result-not-an-egi": ("structure", "DC+",
        P + "The structure half of refusal entry dc-plus-strands-a-vertex, the same mechanism: "
        "given a selection holding a vertex but not all of its edges, the engine wraps the vertex "
        "in the double cut and leaves its edges outside, so the result violates Dau Def 12.5 "
        "(p.125: ctx(e) ≤ ctx(v)) and is not an EGI (Def 15.2 double cuts, p.164, yield EGIs). "
        "Measured by calculus_adjudication_structure: 297 moves in 288 keys, every one judged "
        "illegal by legal(), every result non-EGI, and the 288 keys are exactly that refusal "
        "entry's instances (in_refusal_entry). Coupled: the two entries must shrink together "
        "when the engine is fixed. "
        "In the exhaustive mode (calculus_adjudication_structure --exhaustive): 15,652 moves in 15,022 keys, every result non-EGI."),
    "era-also-erases-the-vertex-it-isolates": ("structure", "ERA",
        P + "Dau Def 15.2 (p.165): erasing an edge e removes e only — V^(e) := V — so its vertex "
        "stays, isolated if e was its last edge. The engine's closure (ErasureRule / ERAInteraction: "
        "analyze_closure(allow_expansion=True, for_erasure=True)) adds that vertex to the selection "
        "and erases it too — only a vertex in the erased edge's own context: one isolated in an "
        "outer context is kept, as Dau keeps it. Measured by calculus_adjudication_structure on "
        "every move in this entry (250 moves in the default mode: 216 tier A, 34 tier B): the "
        "result is Dau's erasure followed by erasing each vertex it isolated in that context "
        "(orphans_erased), the engine's closure adds exactly those vertices, G ⊨ G′ at domain "
        "sizes 1–2, and the engine's G′ ≡ Dau's G′ there (erasing an isolated vertex is Def 15.2's "
        "vertex rule, p.166, an equivalence; for a constant (180 of the 250) Def 24.10's Existence "
        "of Constants, p.271); on 1 move a vertex isolated in an outer context is kept "
        "(orphan_outside_its_context_kept). "
        "Sound, but a larger move than the one named. The same closure is behind refusal entry "
        "era-auto-closes-a-vertex-selection's also_isolated_vertex figure. "
        "In the exhaustive mode: 5,904 moves in 5,825 keys, every one orphans_erased, equivalent_to_dau and sound; 4 keep an orphan in an outer context."),
    "it-plus-auto-closes-a-vertex-selection": ("structure", "IT+",
        P + "Dau Def 15.2 iteration (p.164, 166) copies a NOT NECESSARILY CLOSED subgraph "
        "(Def 12.10, p.134), so a vertex named without its edges is iterated as a vertex. "
        "ITPlusInteraction closes the selection first (analyze_closure(allow_expansion=True)), "
        "adding the vertex's same-area edges — and with them any vertices those edges reach in the "
        "context — and IterationRule copies the whole. Measured by calculus_adjudication_structure "
        "on every move in this entry (261 moves: 252 in the selection's own context, 9 deeper): "
        "the result is exactly the suite's iteration of the engine's closed subgraph (with its "
        "top-level vertices reused when the target is deeper), and G ≡ G′ at domain sizes 1–2. "
        "Sound (iteration is an equivalence), but a larger move than the one named — the IT+ "
        "counterpart of refusal entry era-auto-closes-a-vertex-selection. "
        "In the exhaustive mode: 11,244 moves in 10,673 keys (10,451 in the selection's own context, 793 deeper), every one explained and G ≡ G′."),
    "it-plus-reuses-a-selected-vertex-in-a-deeper-context": ("structure", "IT+",
        P + "Dau Def 15.2 iteration (p.166) copies every vertex of the subgraph: V′ := V×{1} ∪ "
        "V0×{2}. Iterating into a context deeper than the source, IterationRule maps each selected "
        "top-level vertex to ITSELF ('Beta: do NOT copy vertices from the source area when "
        "iterating into a deeper area'), extending the line instead of copying it — Dau's copy "
        "plus a ligature extension (Def 15.2 second clause, p.164) and a merge (Def 16.6 / Lemma "
        "16.7, p.175–178). Measured by calculus_adjudication_structure on every move in this entry "
        "(78 moves in 70 keys in the default mode: 74 tier A, 4 tier B): the result is exactly the "
        "suite's iteration with those vertices reused, and G ≡ G′ at domain sizes 1–2. Where the "
        "selection is an isolated vertex (56 of the 78) the "
        "engine reports success and inserts NOTHING — the result is the source graph — where Dau "
        "inserts a copy of the vertex (the two are equivalent by the vertex rule, p.166). "
        "In the exhaustive mode (1,979 moves) the same mechanism appears where the selection "
        "names an edge together with some OTHER vertex — {(P x), y} in *x *y (P x) ~[ ] — and "
        "the engine's closure pulls in the edge's own vertex: it reuses both instead of copying "
        "y (pulls_vertex, 144 of the 1,979; every one explained and G ≡ G′)."),
}


def classify(rec, detail):
    """The structure entry claiming this failure (calculus_classifiers.STRUCTURE)."""
    return _classify("structure", rec, detail)


def _engine_iteration(g, m, closed, c0):
    if m.target == c0:
        return iterate(g, tuple(closed), m.target)
    vs = {v.id for v in g.V}
    rest = closed - {x for x in closed if x in vs and g.get_context(x) == c0}
    return iterate(g, tuple(rest), m.target) if rest else g


def measure(rec, eid, c: Counter, refusal_keys):
    g, m, h = rec.g, rec.move, rec.outcome.result
    if eid == "dc-plus-result-not-an-egi":
        c["illegal"] += rec.verdict is False
        c["non_egi"] += not dominating_nodes(h)
        if refusal_keys is not None:
            c["in_refusal_entry"] += rec.key in refusal_keys["dc-plus-strands-a-vertex"]
        return
    X = expand(g, m.selection)
    if eid == "era-also-erases-the-vertex-it-isolates":
        orph = _orphans(g, X, g.get_context(tops(g, X)[0]))
        c["orphan_outside_its_context_kept"] += bool(_orphans(g, X) - orph)
        c["orphans_erased"] += nav.same_graph(remove(g, X | orph), h)
        c["closure_adds_orphans"] += _closed(g, m, g.get_context(tops(g, X)[0]), True) - X == orph
        c["orphan_constant"] += any(v.label for v in g.V if v.id in orph)
        c["sound"] += _entail(g, h)[0]
        c["equivalent_to_dau"] += all(_entail(remove(g, X), h))
        return
    c0 = g.get_context(tops(g, X)[0])
    closed = _closed(g, m, c0)
    added = closed - X
    c["same_context" if m.target == c0 else "deeper"] += 1
    c["pulls_vertex"] += any(a in {v.id for v in g.V} for a in added)
    c["pulls_edge"] += any(a in g.nu for a in added)
    c["explained"] += nav.same_graph(_engine_iteration(g, m, closed, c0), h)
    c["noop"] += nav.same_graph(g, h)
    c["equivalent"] += all(_entail(g, h))


def _refusal_keys():
    out = defaultdict(set)
    for e in json.loads(LEDGER.read_text())["entries"]:
        out[e["id"]] = {k for ks in e["instances"].values() for k in ks}
    return out


def adjudicate(mode_name):
    """Returns (entry id -> kind -> keys, entry id -> figures, unclassified).
    in_refusal_entry compares with the refusal entries' DEFAULT instance lists,
    so it is measured in the default mode only."""
    refusal_keys = _refusal_keys() if mode_name == "default" else None
    found, figs, unclassified = defaultdict(lambda: defaultdict(set)), defaultdict(Counter), []
    for rec, _ in records(mode_name):
        detail = structure(rec, {})[1]
        if detail is None:
            continue
        eid = classify(rec, detail)
        if eid is None:
            unclassified.append((rec.key, detail))
            continue
        found[eid][failure_kind("structure", detail)].add(rec.key)
        figs[eid]["moves"] += 1
        figs[eid][f"tier_{rec.tier}"] += 1
        measure(rec, eid, figs[eid], refusal_keys)
    if mode_name == "default":
        for gname, g in tier_a(DEFAULT_BOUNDS).graphs:
            if g.has_dominating_nodes() != dominating_nodes(g):
                found["core-has-dominating-nodes-inverted"]["DISAGREE"].add(f"A|{gname}|graph")
        for name, g in tier_b_sources(include_chains=True):
            if not dominating_nodes(g):
                found["corpus-graph-not-an-egi"]["NOT AN EGI"].add(f"B|{name}|graph")
    for eid in figs:
        figs[eid]["keys"] = len(set().union(*found[eid].values()))
    return found, figs, unclassified


def corpus_figures():
    c, lines = Counter(), []
    for name, g in tier_b_sources(include_chains=True):
        c["sources"] += 1
        c["chain_states" if not name.endswith(":current") else "current_graphs"] += 1
        bad = dominating_violations(g)
        if bad:
            c["not_an_egi"] += 1
            c["not_an_egi_chain_states"] += not name.endswith(":current")
            lines.append(f"{name}: {len(bad)} edge-vertex pairs on {len({v for _, v in bad})} vertex(es)")
    return c, lines


def core_figures(bounds) -> Counter:
    c = Counter()
    for _, g in tier_a(bounds).graphs:
        c["graphs"] += 1
        c["line_into_a_cut"] += any(g.get_context(v) != g.get_context(e)
                                    for e, s in g.nu.items() for v in s)
        c["disagree"] += g.has_dominating_nodes() != dominating_nodes(g)
    h = parse_egif("(P *x) ~[ ]")          # move the vertex into the cut: not an EGI
    v, cut = next(iter(h.V)).id, next(iter(h.Cut)).id
    area = {k: set(s) for k, s in h.area.items()}
    area[h.sheet].discard(v)
    area[cut].add(v)
    bad = _g(h, V=h.V, E=h.E, nu=h.nu, Cut=h.Cut, area=area, rel=h.rel)
    c["hand_non_egi_core_accepts"] = int(bad.has_dominating_nodes() and not dominating_nodes(bad))
    return c


def main(argv):
    if "--reasons" in argv:
        print(f"refreshed {refresh_reasons(LAYERS_OWNED, REASONS)} structure/core/corpus reason(s)")
        return
    mode = "exhaustive" if "--exhaustive" in argv else "default"
    print(f"mode={mode}")
    found, figs, unclassified = adjudicate(mode)
    print("core-has-dominating-nodes-inverted  " + " ".join(
        f"{k}={v}" for k, v in sorted(core_figures(DEFAULT_BOUNDS).items())))
    c, lines = corpus_figures()
    print("corpus-graph-not-an-egi  " + " ".join(f"{k}={v}" for k, v in sorted(c.items())))
    for line in lines:
        print("    " + line)
    for eid in sorted(figs):
        print(f"{eid:54s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[eid].items())))
    for k, d in unclassified[:20]:
        print("UNCLASSIFIED", k, d)
    if unclassified:
        raise SystemExit(f"{len(unclassified)} unclassified failure(s)")
    if "--write" in argv:
        update_ledger(LAYERS_OWNED, REASONS, mode, found)
        print(f"wrote this script's entries for mode {mode!r}: "
              f"{sum(len(ks) for kinds in found.values() for ks in kinds.values())} keys in {len(found)} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
