"""Adjudication of the structure layer and the core's dominating-nodes check
(spec 2026-09-10 §5.2, §6; Task 7). The sibling of calculus_adjudication.

Not a test. It classifies every failing structure instance into its ledger
entry by mechanism, measures the figures the entries' reasons state, and on
request rewrites those entries' instance lists (other layers' entries are kept):

    uv run python tests/calculus_adjudication_structure.py               # figures only
    uv run python tests/calculus_adjudication_structure.py --write       # + rewrite the ledger
    uv run python tests/calculus_adjudication_structure.py --exhaustive  # figures at EXHAUSTIVE_BOUNDS

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
from calculus_apply import apply_move  # noqa: E402
from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, edges_on, tier_a  # noqa: E402
from calculus_expected import _g, iterate, remove  # noqa: E402
from calculus_layers import structure  # noqa: E402
from calculus_ledger import LEDGER, instance_key  # noqa: E402
from calculus_rules import IMPLEMENTED, expand, legal, moves, tops  # noqa: E402
from calculus_run import Record  # noqa: E402
from canonical_signature import compute_canonical_signatures  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from subgraph_closure_validator import SubgraphClosureValidator  # noqa: E402
from tarski import dominating_nodes  # noqa: E402

LAYERS_OWNED = ("structure", "core-dominating")

# id -> (layer, rule, reason). Figures quoted are this script's, at DEFAULT_BOUNDS.
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
    "dc-plus-result-not-an-egi": ("structure", "DC+",
        P + "The structure half of refusal entry dc-plus-strands-a-vertex, the same mechanism: "
        "given a selection holding a vertex but not all of its edges, the engine wraps the vertex "
        "in the double cut and leaves its edges outside, so the result violates Dau Def 12.5 "
        "(p.125: ctx(e) ≤ ctx(v)) and is not an EGI (Def 15.2 double cuts, p.164, yield EGIs). "
        "Measured by calculus_adjudication_structure: 297 moves in 288 keys, every one judged "
        "illegal by legal(), every result non-EGI, and the 288 keys are exactly that refusal "
        "entry's instances."),
    "era-also-erases-the-vertex-it-isolates": ("structure", "ERA",
        P + "Dau Def 15.2 (p.165): erasing an edge e removes e only — V^(e) := V — so its vertex "
        "stays, isolated if e was its last edge. The engine's closure (ErasureRule / ERAInteraction: "
        "analyze_closure(allow_expansion=True, for_erasure=True)) adds that vertex to the selection "
        "and erases it too. Measured by calculus_adjudication_structure on every move in this entry "
        "(216 moves): the result is Dau's erasure followed by erasing each vertex it isolated, the "
        "engine's closure adds exactly those vertices, G ⊨ G′ at domain sizes 1–2, and the engine's "
        "G′ ≡ Dau's G′ there (erasing an isolated vertex is Def 15.2's vertex rule, p.166, an "
        "equivalence; for a constant (164 of the 216) Def 24.10's Existence of Constants, p.271). "
        "Sound, but a larger move than the one named. The same closure is behind refusal entry "
        "era-auto-closes-a-vertex-selection's also_isolated_vertex figure."),
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
        "counterpart of refusal entry era-auto-closes-a-vertex-selection."),
    "it-plus-copies-the-line-fresh-in-its-own-context": ("structure", "IT+",
        P + "Iterating an edge within its own context: the suite's licensed change (legal()'s "
        "shared-vertex reading of Def 15.2, p.166) attaches the copy to the SAME vertex — Θ-linked "
        "and merged, Lemma 16.3 (p.173). The engine's closure (analyze_closure(allow_expansion=True)) "
        "adds the edge's vertex, which completes the Def 12.10 subgraph (p.134: V_e ⊆ V′), and "
        "IterationRule, iterating into the source area, copies that vertex FRESH with no identity "
        "edge — Def 15.2's literal iteration with W_v = ∅ (p.166). Measured by "
        "calculus_adjudication_structure on every move in this entry (225 moves): the result is "
        "exactly the suite's iteration of the engine's closed subgraph, and G ≡ G′ at domain sizes "
        "1–2. Dau-licensed and sound; it departs from the suite's reuse convention (and from the "
        "engine's own deeper-context behaviour, which reuses the line). For the author: should the "
        "expectation accept Dau's literal W_v = ∅ form too?"),
    "it-plus-reuses-a-selected-vertex-in-a-deeper-context": ("structure", "IT+",
        P + "Dau Def 15.2 iteration (p.166) copies every vertex of the subgraph: V′ := V×{1} ∪ "
        "V0×{2}. Iterating into a context deeper than the source, IterationRule maps each selected "
        "top-level vertex to ITSELF ('Beta: do NOT copy vertices from the source area when "
        "iterating into a deeper area'), extending the line instead of copying it — Dau's copy "
        "plus a ligature extension (Def 15.2 second clause, p.164) and a merge (Def 16.6 / Lemma "
        "16.7, p.175–178). Measured by calculus_adjudication_structure on every move in this entry "
        "(74 moves): the result is exactly the suite's iteration with those vertices reused, and "
        "G ≡ G′ at domain sizes 1–2. Where the selection is an isolated vertex (56 of the 74) the "
        "engine reports success and inserts NOTHING — the result is the source graph — where Dau "
        "inserts a copy of the vertex (the two are equivalent by the vertex rule, p.166)."),
}


def _closed(g, m, c0, for_erasure=False):
    return set(SubgraphClosureValidator(g).analyze_closure(
        frozenset(m.selection), allow_expansion=True, context_area=c0,
        for_erasure=for_erasure).closed_subgraph)


def _orphans(g, X):
    vs = {v.id for v in g.V}
    return {v for v in vs - set(X) if edges_on(g, v) and set(edges_on(g, v)) <= set(X)}


def classify(rec):
    g, m, out = rec.g, rec.move, rec.outcome
    if m.rule == "DC+" and not dominating_nodes(out.result):
        return "dc-plus-result-not-an-egi"
    if not rec.verdict:
        return None
    X = expand(g, m.selection)
    if m.rule == "ERA" and nav.same_graph(remove(g, X | _orphans(g, X)), out.result):
        return "era-also-erases-the-vertex-it-isolates"
    if m.rule == "IT+":
        vs = {v.id for v in g.V}
        c0 = g.get_context(tops(g, X)[0])
        added = _closed(g, m, c0) - X
        if any(a in g.nu for a in added):
            return "it-plus-auto-closes-a-vertex-selection"
        if added and m.target == c0:
            return "it-plus-copies-the-line-fresh-in-its-own-context"
        if not added and m.target != c0 and any(x in vs and g.get_context(x) == c0 for x in X):
            return "it-plus-reuses-a-selected-vertex-in-a-deeper-context"
    return None


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
        c["in_refusal_entry"] += rec.key in refusal_keys["dc-plus-strands-a-vertex"]
        return
    X = expand(g, m.selection)
    if eid == "era-also-erases-the-vertex-it-isolates":
        orph = _orphans(g, X)
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


def adjudicate(bounds):
    """Returns (entry id -> keys, entry id -> figures, unclassified)."""
    refusal_keys = defaultdict(set)
    for e in json.loads(LEDGER.read_text())["entries"]:
        refusal_keys[e["id"]] = set(e["instances"])
    keys, figs, unclassified = defaultdict(set), defaultdict(Counter), []
    for gname, g in tier_a(bounds).graphs:
        sigs = compute_canonical_signatures(g)
        for rule in IMPLEMENTED:
            for m in moves(rule.name, g, "A"):
                verdict, why = legal(g, m)
                rec = Record("A", gname, g, m, instance_key("A", gname, g, m, sigs),
                             apply_move(g, m), verdict, why)
                if structure(rec, {})[1] is None:
                    continue
                eid = classify(rec)
                if eid is None:
                    unclassified.append((rec.key, structure(rec, {})[1]))
                    continue
                keys[eid].add(rec.key)
                figs[eid]["moves"] += 1
                measure(rec, eid, figs[eid], refusal_keys)
        if g.has_dominating_nodes() != dominating_nodes(g):
            keys["core-has-dominating-nodes-inverted"].add(f"A|{gname}|graph")
    for eid in figs:
        figs[eid]["keys"] = len(keys[eid])
    return keys, figs, unclassified


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


def write_ledger(keys) -> None:
    owner = defaultdict(set)
    for eid, ks in keys.items():
        for k in ks:
            owner[k].add(eid)
    split = {k: e for k, e in owner.items() if len(e) > 1}
    if split:
        raise SystemExit(f"{len(split)} key(s) classified into two entries: {list(split.items())[:5]}")
    kept = [e for e in json.loads(LEDGER.read_text())["entries"] if e["layer"] not in LAYERS_OWNED]
    mine = [{"id": eid, "layer": REASONS[eid][0], "rule": REASONS[eid][1],
             "reason": REASONS[eid][2], "instances": sorted(ks)}
            for eid, ks in keys.items()]
    entries = sorted(kept + mine, key=lambda e: (e["layer"], e["id"]))
    LEDGER.write_text(json.dumps({"entries": entries}, indent=1, ensure_ascii=False) + "\n")


def main(argv):
    exhaustive = "--exhaustive" in argv
    if exhaustive and "--write" in argv:
        raise SystemExit("exhaustive bounds are not ledgered")
    bounds = EXHAUSTIVE_BOUNDS if exhaustive else DEFAULT_BOUNDS
    keys, figs, unclassified = adjudicate(bounds)
    print("core-has-dominating-nodes-inverted  " + " ".join(
        f"{k}={v}" for k, v in sorted(core_figures(bounds).items())))
    for eid in sorted(figs):
        print(f"{eid:54s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[eid].items())))
    for k, d in unclassified[:20]:
        print("UNCLASSIFIED", k, d)
    if unclassified:
        raise SystemExit(f"{len(unclassified)} unclassified failure(s)")
    if "--write" in argv:
        write_ledger(keys)
        print(f"wrote {LEDGER.name}: {sum(map(len, keys.values()))} keys in {len(keys)} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
