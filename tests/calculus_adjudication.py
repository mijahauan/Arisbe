"""Adjudication of the refusal layer (spec 2026-09-10 §5.1, §6; Task 6).

Not a test. It classifies every failing refusal instance into its ledger entry
by mechanism, measures the figures the entries' reasons state, and on request
rewrites the ledger's instance lists. Run it by hand whenever the engine,
legal(), the enumerator or the instance key changes:

    uv run python tests/calculus_adjudication.py               # figures only
    uv run python tests/calculus_adjudication.py --write       # + rewrite calculus_ledger.json
    uv run python tests/calculus_adjudication.py --exhaustive  # figures at EXHAUSTIVE_BOUNDS

--write replaces each entry's instance list (ids and reasons come from
REASONS below) and is refused at exhaustive bounds, which are not ledgered.

Figures, per entry ("moves" = candidate moves, "keys" = distinct instance keys):
  moves, keys            how much the entry covers
  cell_ok                moves in the refusal cell the entry describes (must = moves)
  closure_legal          ERA/VERTEX_ERA auto-close: the removed set is legal() as an ERA
  sound                  G ⊨ G′ on every structure of domain size 1-2 (exhaustive where
                         the tuple bits are <= 12, otherwise 256 seeded samples)
  equivalent             G ⊨ G′ and G′ ⊨ G on those structures
  unsound                some structure models G but not G′
  non_egi                the engine's result violates dominating nodes (Def 12.5)
  also_isolated_vertex   the engine also erased a vertex left isolated by the erasure
  same_as_own_context    DC+ result is same_graph to the engine's DC+ at the selection's area
  target_also_ignored    DC+ strand moves whose target was also not the selection's area
  tops_only_applied      the same move named by its top elements alone is applied
  on_sheet / in_a_cut    where a refused same-context deiteration sits
Also reported: failing keys whose moves land in more than one refusal cell (must be 0).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

for _p in (Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent / "src"):
    if str(_p) not in sys.path:     # run as a script, not under pytest's pythonpath
        sys.path.insert(0, str(_p))

from calculus_apply import apply_move  # noqa: E402
from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, edges_on, tier_a
from calculus_layers import refusal
from calculus_ledger import LEDGER, instance_key
from calculus_rules import IMPLEMENTED, Move, expand, legal, moves, tops
from calculus_run import Record
from canonical_signature import compute_canonical_signatures
from tarski import dominating_nodes, satisfies, universe, vocabulary
import eg_navigation as nav

P = "PROVISIONAL — for the author: "
SEVERE, INCOMPLETE = "applied/illegal", "refused/legal"

# id -> (rule, cell, reason). Figures quoted are this script's, at DEFAULT_BOUNDS.
REASONS = {
    "heavy-dot-negative-only": ("VERTEX_INS", INCOMPLETE,
        "Dau Def 15.2 (p.164, 166): an isolated vertex may be inserted in ARBITRARY contexts. "
        "The engine's only vertex-insertion entry point, HEAVY_DOT, refuses every positive context "
        "(sheet included) with 'Heavy dot insertion only allowed in negatively-enclosed areas'. "
        "Incompleteness, not unsoundness: half of an equivalence rule is missing."),
    "vertex-era-positive-only": ("VERTEX_ERA", INCOMPLETE,
        "Dau Def 15.2 (p.164, 166): an isolated vertex may be erased from ARBITRARY contexts; "
        "for a constant vertex Def 24.10's Existence of Constants rule (p.271) says the same. "
        "The engine has no vertex-erasure entry point; its only route is ERA, which refuses "
        "every negative context ('Erasure only allowed in positive (recto) areas')."),
    "vertex-era-erases-a-line-with-its-edges": ("VERTEX_ERA", SEVERE,
        P + "Dau Def 15.2 (p.166): the vertex rule erases a vertex with E_v = ∅ only. Offered "
        "a vertex that has edges, the engine (via ERA, its only entry point) auto-expands the "
        "selection to the vertex with all its incident edges and erases that (and, where an edge's "
        "other vertex is left isolated, that vertex too). Measured by calculus_adjudication on "
        "every move in this entry: the removed set is a Dau-legal ERA of a closed subgraph "
        "(Def 12.10, p.134) and G ⊨ G′ at domain sizes 1–2 — a protocol convention (the selection "
        "generates the closed subgraph), not an unsound step; but the engine performs a larger "
        "move than the one named instead of refusing it."),
    "era-auto-closes-a-vertex-selection": ("ERA", SEVERE,
        P + "Dau Def 15.2 (p.164–165): erasure takes an edge, an isolated vertex, or a CLOSED "
        "subgraph (Def 12.10, p.134: E_v ⊆ E′ for every selected vertex). Named a vertex without "
        "all its edges, the engine auto-expands the selection to the closed subgraph it generates "
        "(ERAInteraction: analyze_closure(allow_expansion=True, for_erasure=True)) and erases that "
        "— and, where an edge's other vertex is left isolated, that vertex too. Measured by "
        "calculus_adjudication on every move in this entry: the removed set is legal as an ERA "
        "and G ⊨ G′ at domain sizes 1–2 — a protocol convention, not an unsound step; but the "
        "engine performs a larger move than the one named instead of refusing it."),
    "era-refuses-a-cut-named-with-its-contents": ("ERA", INCOMPLETE,
        "Dau Def 12.10 (p.134): a subgraph that contains a cut contains that cut's whole area, so "
        "naming a cut together with some of its contents names the same closed subgraph as the "
        "cut alone, and Def 15.2 (p.164–165) lets it be erased from a positive context. The engine "
        "requires every NAMED element to lie in one area and refuses ('All selected elements must "
        "be in the same area'); measured on every move in this entry, the same move named by its "
        "top elements alone is applied. An input-form restriction, not a missing rule."),
    "it-plus-refuses-a-cut-named-with-its-contents": ("IT+", INCOMPLETE,
        "Dau Def 12.10 (p.134) with Def 15.2 iteration (p.164, 166): naming a cut together with "
        "some of its contents names the same subgraph as the cut alone, which may be iterated "
        "into any c ≤ ctx(G0) outside it. The engine requires every NAMED element to lie in one "
        "area ('All source elements must be in the same area'); measured on every move in this "
        "entry, the same move named by its top elements alone is applied. An input-form "
        "restriction, not a missing rule."),
    "dc-plus-refuses-a-cut-named-with-its-contents": ("DC+", INCOMPLETE,
        "Dau Def 12.10 (p.134) with Def 15.2 double cuts (p.164): naming a cut together with "
        "some of its contents names the same subgraph as the cut alone, which a double cut may "
        "be inserted around in its context. The engine requires every NAMED element to lie in "
        "one area ('All selected elements must be in the same area'); measured on every move in "
        "this entry, the same move named by its top elements alone is applied. An input-form "
        "restriction, not a missing rule."),
    "it-minus-refuses-a-cut-named-with-its-contents": ("IT-", INCOMPLETE,
        "Dau Def 12.10 (p.134) with Def 15.2 deiteration (p.164, 166): naming a cut together "
        "with some of its contents names the same subgraph as the cut alone. The engine requires "
        "every NAMED element to lie in one area ('All candidate elements must be in the same "
        "area'). Unlike the ERA/IT+/DC+ entries of this shape, the same move named by its top "
        "elements alone is ALSO refused (tops_only_applied=0 of 8 moves at exhaustive bounds), so "
        "this is not shown to be an input-form restriction alone. (Exhaustive bounds only; not "
        "ledgered.)"),
    "it-plus-into-its-own-selection": ("IT+", SEVERE,
        P + "Dau Def 15.2 iteration (p.164, and formally p.166): the target context must satisfy "
        "c ∉ Cut_0 — a subgraph may not be copied into one of its own cuts. The engine's "
        "destination check (ITPlusInteraction._validate_dest) only asks that the target be the "
        "source area or nested inside it, so it copies a selected cut into itself or into a cut "
        "it contains. Measured by calculus_adjudication at the default bounds: 17 moves are "
        "UNSOUND — a structure satisfies G but not G′ (e.g. ~[ ~[ ] ] (true) becomes "
        "~[ ~[ ~[ ] ] ] (false) by iterating the empty inner cut into itself); on others the "
        "result is merely not the equivalence IT+ must be."),
    "it-minus-strictly-enclosing-only": ("IT-", INCOMPLETE,
        "Dau Def 15.2 (p.164, 166): iteration copies into any c ≤ ctx(G0), c = ctx(G0) included, "
        "and deiteration erases whatever iteration could have inserted — so a copy whose source "
        "sits in the SAME context may be deiterated. The engine searches for the original only in "
        "strictly enclosing areas (ITMinusInteraction excludes the candidate's own area), so it "
        "refuses every same-context deiteration: on the sheet ('No enclosing areas found') and "
        "inside a cut ('No isomorphic original found in enclosing areas')."),
    "dc-plus-strands-a-vertex": ("DC+", SEVERE,
        P + "Dau Def 15.2 double cuts (p.164) define DC+ as the inverse of erasing a double cut, "
        "and the graph it yields must be an EGI with dominating nodes (Def 12.5, p.125: "
        "ctx(e) ≤ ctx(v) for every edge e on v). Given a selection holding a vertex but not all of "
        "its edges, the engine wraps the vertex in the double cut and leaves its edges outside: "
        "measured by calculus_adjudication, every result in this entry violates Def 12.5, so it "
        "is not an EGI and has no Dau semantics (Def 13.4 cannot evaluate it). Includes moves "
        "whose target was also ignored (see dc-plus-ignores-target)."),
    "dc-plus-ignores-target": ("DC+", SEVERE,
        P + "Dau Def 15.2 double cuts (p.164): the double cut is inserted in the context c0 whose "
        "contents it encloses. Given a non-empty selection and a target area that is not the "
        "selection's own area, the engine ignores the target (DCPlusInteraction.build_context: "
        "'Subject given → enclose exactly those, in their common area') and inserts the double "
        "cut in the selection's own area. Measured by calculus_adjudication on every move in this "
        "entry: the result is same_graph to the engine's DC+ at the selection's own area, and "
        "G ⊨ G′ ⊨ G at domain sizes 1–2 — a protocol convention (the spot is ignored when a "
        "subject is given), not an unsound step; but the named move is not the one performed and "
        "the engine does not refuse."),
}


def classify(rec):
    rule, out, why = rec.move.rule, rec.outcome, rec.why
    if rule == "VERTEX_INS" and not out.applied:
        return "heavy-dot-negative-only"
    if rule == "VERTEX_ERA":
        return "vertex-era-positive-only" if not out.applied else "vertex-era-erases-a-line-with-its-edges"
    named_apart = not out.applied and "must be in the same area" in out.message
    if rule == "ERA":
        if out.applied and "leave an edge behind" in why:
            return "era-auto-closes-a-vertex-selection"
        if named_apart:
            return "era-refuses-a-cut-named-with-its-contents"
    if rule == "IT+":
        if out.applied and "inside the selection" in why:
            return "it-plus-into-its-own-selection"
        if named_apart:
            return "it-plus-refuses-a-cut-named-with-its-contents"
    if rule == "IT-":
        if named_apart:
            return "it-minus-refuses-a-cut-named-with-its-contents"
        if not out.applied and ("No enclosing areas" in out.message
                                or "No isomorphic original" in out.message):
            return "it-minus-strictly-enclosing-only"
    if rule == "DC+":
        if named_apart:
            return "dc-plus-refuses-a-cut-named-with-its-contents"
        if out.applied and not dominating_nodes(out.result):
            return "dc-plus-strands-a-vertex"
        if out.applied and "not directly in the target" in why:
            return "dc-plus-ignores-target"
    return None


def _ids(g):
    return {v.id for v in g.V} | set(g.nu) | {c.id for c in g.Cut}


def _entail(g, h):
    """(g ⊨ h, h ⊨ g) over domain sizes 1-2."""
    rels, consts = vocabulary(g, h)
    fwd = bwd = True
    for size in (1, 2):
        for s in universe(rels, consts, size, cap=12, sample_n=256, seed=1)[0]:
            a, b = satisfies(g, s), satisfies(h, s)
            fwd &= not (a and not b)
            bwd &= not (b and not a)
    return fwd, bwd


def measure(rec, eid, c: Counter):
    g, m, out = rec.g, rec.move, rec.outcome
    if eid in ("era-auto-closes-a-vertex-selection", "vertex-era-erases-a-line-with-its-edges"):
        removed = _ids(g) - _ids(out.result)
        c["closure_legal"] += legal(g, Move("ERA", tuple(sorted(removed))))[0] is True
        vs = {v.id for v in g.V}
        sel = expand(g, m.selection)
        base = sel | {e for x in sel if x in vs for e in edges_on(g, x)}
        c["also_isolated_vertex"] += bool(removed - base)
        c["sound"] += _entail(g, out.result)[0]
    elif eid == "dc-plus-ignores-target":
        own = {g.get_context(x) for x in m.selection}
        alt = apply_move(g, Move("DC+", m.selection, own.pop())) if len(own) == 1 else None
        c["same_as_own_context"] += bool(alt and alt.applied and nav.same_graph(alt.result, out.result))
        c["equivalent"] += all(_entail(g, out.result))
    elif eid == "dc-plus-strands-a-vertex":
        c["non_egi"] += not dominating_nodes(out.result)
        c["target_also_ignored"] += any(g.get_context(x) != m.target for x in tops(g, expand(g, m.selection)))
    elif eid == "it-plus-into-its-own-selection":
        fwd, bwd = _entail(g, out.result)
        c["unsound"] += not fwd
        c["equivalent"] += fwd and bwd
    elif eid.endswith("-cut-named-with-its-contents"):
        t = tuple(tops(g, expand(g, m.selection)))
        c["tops_only_applied"] += apply_move(g, Move(m.rule, t, m.target, m.content)).applied
    elif eid == "it-minus-strictly-enclosing-only":
        c["on_sheet" if "No enclosing areas" in out.message else "in_a_cut"] += 1


def adjudicate(bounds):
    """Returns (entry id -> keys, entry id -> figures, unclassified, mixed failing keys)."""
    keys, figs, labels = defaultdict(set), defaultdict(Counter), defaultdict(set)
    unclassified, failing = [], set()
    for gname, g in tier_a(bounds).graphs:
        sigs = compute_canonical_signatures(g)
        for rule in IMPLEMENTED:
            for m in moves(rule.name, g, "A"):
                verdict, why = legal(g, m)
                rec = Record("A", gname, g, m, instance_key("A", gname, g, m, sigs),
                             apply_move(g, m), verdict, why)
                label, detail = refusal(rec, {})
                labels[rec.key].add(label)
                if detail is None:
                    continue
                failing.add(rec.key)
                eid = classify(rec)
                if eid is None:
                    unclassified.append((rec.key, detail))
                    continue
                keys[eid].add(rec.key)
                c = figs[eid]
                c["moves"] += 1
                c["cell_ok"] += label.split(":", 1)[1] == REASONS[eid][1]
                measure(rec, eid, c)
    for eid in figs:
        figs[eid]["keys"] = len(keys[eid])
    mixed = sorted(k for k in failing if len(labels[k]) > 1)
    return keys, figs, unclassified, mixed


def write_ledger(keys) -> None:
    owner = defaultdict(set)
    for eid, ks in keys.items():
        for k in ks:
            owner[k].add(eid)
    split = {k: e for k, e in owner.items() if len(e) > 1}
    if split:
        raise SystemExit(f"{len(split)} key(s) classified into two entries: {list(split.items())[:5]}")
    kept = [e for e in json.loads(LEDGER.read_text())["entries"] if e["layer"] != "refusal"]
    mine = [{"id": eid, "layer": "refusal", "rule": REASONS[eid][0],
             "reason": REASONS[eid][2], "instances": sorted(ks)}
            for eid, ks in keys.items()]
    entries = sorted(kept + mine, key=lambda e: (e["layer"], e["id"]))
    LEDGER.write_text(json.dumps({"entries": entries}, indent=1, ensure_ascii=False) + "\n")


def main(argv):
    exhaustive = "--exhaustive" in argv
    if exhaustive and "--write" in argv:
        raise SystemExit("exhaustive bounds are not ledgered")
    keys, figs, unclassified, mixed = adjudicate(EXHAUSTIVE_BOUNDS if exhaustive else DEFAULT_BOUNDS)
    for eid in sorted(figs):
        print(f"{eid:48s} {REASONS[eid][1]:16s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[eid].items())))
    print(f"failing keys in more than one refusal cell: {len(mixed)} {mixed[:5]}")
    for k, d in unclassified[:20]:
        print("UNCLASSIFIED", k, d)
    if unclassified:
        raise SystemExit(f"{len(unclassified)} unclassified failure(s)")
    if "--write" in argv:
        write_ledger(keys)
        print(f"wrote {LEDGER.name}: {sum(map(len, keys.values()))} keys in {len(keys)} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
