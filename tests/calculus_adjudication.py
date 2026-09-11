"""Adjudication of the refusal layer (spec 2026-09-10 §5.1, §6; Task 6).

Not a test. It classifies every failing refusal instance into its ledger entry
by mechanism, measures the figures the entries' reasons state, and on request
rewrites the ledger's instance lists. Run it by hand whenever the engine,
legal(), the enumerator or the instance key changes:

    uv run python tests/calculus_adjudication.py               # figures only (default mode)
    uv run python tests/calculus_adjudication.py --write       # + rewrite calculus_ledger.json
    uv run python tests/calculus_adjudication.py --exhaustive  # figures in the exhaustive mode

It walks calculus_run.records(mode) — tier A and tier B, exactly the extent the
tests pin — and classifies through calculus_classifiers, the classifiers the
exhaustive ledger check uses. --write replaces, for the mode run, each entry's
instance lists by kind (default) or its pinned counts by kind (--exhaustive);
ids and reasons come from REASONS below.

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
from calculus_classifiers import classify as _classify, failure_kind  # noqa: E402
from calculus_enum import edges_on  # noqa: E402
from calculus_layers import refusal  # noqa: E402
from calculus_ledger import refresh_reasons, update_ledger  # noqa: E402
from calculus_rules import Move, expand, legal, tops  # noqa: E402
from calculus_run import records  # noqa: E402
from tarski import dominating_nodes, satisfies, universe, vocabulary
import eg_navigation as nav

P = "PROVISIONAL — for the author: "
SEVERE, INCOMPLETE = "applied/illegal", "refused/legal"

# id -> (rule, cell, reason). Figures quoted are this script's, in the default mode.
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
    "ins-mixes-arities-without-an-alphabet": ("INS", SEVERE,
        P + "Dau Def 12.6 (p.126): an alphabet gives each relation name ONE arity; Def 12.7 "
        "(p.126): an EGI over it labels every edge within it, |e| = ar(κ(e)). The engine "
        "enforces arity only when the graph declares an alphabet (it refuses such an insertion "
        "on dau_2006_p112_ligature, whose alphabet makes R unary). On a graph with no declared "
        "alphabet it inserts content that uses a name at a second arity — the propositional "
        "exemplars use P as a 0-ary name ((P)), and inserting (P *x) makes P both 0-ary and "
        "unary — so the result is an EGI over no single alphabet. Measured by "
        "calculus_adjudication in the default mode on every move in this entry: none of the "
        "sources declares an alphabet (no_declared_alphabet), legal() rejects every move, and "
        "G ⊨ G′ at domain sizes 1–2 (sound) — but only because tarski reads the two arities "
        "of one name as two relations; Dau's semantics has no reading for such a graph. Tier A "
        "cannot reach it (its bounds give each name one arity, the INS catalogue's). "
        "In the exhaustive mode: 244 moves in 244 keys, none on a source with a declared alphabet, all sound under tarski's reading."),
    "era-closure-drags-a-quoting-name": ("ERA", INCOMPLETE,
        "Dau Def 15.2 (p.165): erasing an edge removes the edge only (V^(e) := V) — its vertex "
        "stays, even when the edge was its last. Offered an edge whose argument is a QUOTING NAME "
        "(a proposition-sorted vertex bound to a quotation oval, B-min), the engine's erasure "
        "closure (analyze_closure, for_erasure) adds the vertex the erasure would isolate — the "
        "same closure as structure entry era-also-erases-the-vertex-it-isolates — and the "
        "quotation guard then refuses the whole move ('Quoting name … selected without its "
        "oval: the quotation moves only whole'). The move named — erase the edge, keep the name "
        "and its oval — touches no quotation apparatus. Measured by calculus_adjudication in the "
        "default mode on every move in this entry: the refused name is a vertex the erasure "
        "isolates (name_is_isolated) and legal() judges the named move legal. Incompleteness, "
        "not unsoundness. "
        "In the exhaustive mode: 18 moves in 18 keys, the refused name the isolated vertex on all 18."),
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
        "area'). Measured by calculus_adjudication --exhaustive (the default mode reaches none): "
        "22 moves in 18 keys — 8 tier A, 14 tier B. At tier A, unlike the ERA/IT+/DC+ entries of "
        "this shape, the same move named by its top elements alone is ALSO refused (0 of the 8), "
        "so there it is not shown to be an input-form restriction alone; at tier B the top-"
        "elements move is applied on all 14 (tops_only_applied 14 of 22). Ledgered by count in "
        "the exhaustive mode."),
    "it-plus-into-its-own-selection": ("IT+", SEVERE,
        P + "Dau Def 15.2 iteration (p.164, and formally p.166): the target context must satisfy "
        "c ∉ Cut_0 — a subgraph may not be copied into one of its own cuts. The engine's "
        "destination check (ITPlusInteraction._validate_dest) only asks that the target be the "
        "source area or nested inside it, so it copies a selected cut into itself or into a cut "
        "it contains. Measured by calculus_adjudication in the default mode: 70 of the entry's 483 "
        "moves are UNSOUND (unsound) — a structure satisfies G but not G′ (e.g. ~[ ~[ ] ] (true) becomes "
        "~[ ~[ ~[ ] ] ] (false) by iterating the empty inner cut into itself); on others the "
        "result is merely not the equivalence IT+ must be. "
        "In the exhaustive mode: 6,619 moves in 6,322 keys (4,430 tier A, 2,189 tier B), 704 of them UNSOUND at sizes 1–2."),
    "it-minus-erases-a-copy-of-another-line": ("IT-", SEVERE,
        P + "Dau Def 15.2 deiteration (p.164, 166): a subgraph may be erased only if iteration "
        "could have inserted it, and iteration copies every vertex of the source fresh "
        "(V′ := V×{1} ∪ V₀×{2}), linking a copy to an outside vertex w only by an identity edge, "
        "and only where wΘv (the same line). So an edge that hooks a DIFFERENT vertex from the "
        "source edge — another line, or a name where the source has a line — is not a copy. "
        "The engine's search for the original (ITMinusInteraction via graph_isomorphism_engine) "
        "matches such an edge anyway and erases it. Measured by calculus_adjudication in the "
        "default mode: every move in this entry is a tier-B move legal() rejects ('no source of "
        "which this is a copy'), and on every one a source exists once each outside vertex may "
        "match ANY vertex (source_on_any_vertex); on only some does one exist when it must match "
        "a vertex of the same kind (source_on_another_line) — e.g. foaf_core's Person(x) erased "
        "because Person(\"Bob\") stands in an enclosing context. None of those corpus results "
        "separates from G at domain sizes 1–2 (the difference is inert where they sit). It is "
        "not inert in general: the hand-built controls (IT_MINUS_CONTROLS, printed with their "
        "separating structures) — *x *y (P x) ~[ (P y) ] (satisfiable) is deiterated to "
        "*x *y (P x) ~[ ] (unsatisfiable), UNSOUND; and *y (P \"a\") ~[ (P y) ] likewise. The "
        "engine does not ignore names everywhere: (P \"a\") ~[ (P \"b\") ] is refused. Tier A "
        "cannot build these shapes (the exhaustive bound is four elements), which is why tier B "
        "found it. "
        "In the exhaustive mode (calculus_adjudication --exhaustive): 64 moves in 64 keys, all tier B; a source exists for all 64 once any vertex may match, for 24 with a vertex of the same kind; 59 are equivalences at sizes 1–2, and the other 5 — on group_identity's chain states — change meaning, some UNSOUND (soundness entry it-minus-erases-a-copy-of-another-line-changes-meaning)."),
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
        "whose target was also ignored (see dc-plus-ignores-target). Coupled: structure entry "
        "dc-plus-result-not-an-egi holds exactly these keys (its in_refusal_entry figure), so "
        "the two must shrink together when the engine is fixed."),
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


def classify(rec, detail):
    """The refusal entry claiming this failure (calculus_classifiers.REFUSAL)."""
    return _classify("refusal", rec, detail)


def _ids(g):
    return {v.id for v in g.V} | set(g.nu) | {c.id for c in g.Cut}


# Above this many structures an exhaustive universe is sampled instead: a corpus
# vocabulary's constant assignments are otherwise uncapped (2^bits x n^consts —
# millions on colore_between / peirce_order), the same explosion
# calculus_run.SemanticsBudget.tier_b_max_structures caps in the layer. Every
# tier-A universe at sizes 1-2 is far below it, so tier-A figures are unchanged.
ENTAIL_MAX_STRUCTURES = 36864


def _entail(g, h):
    """(g ⊨ h, h ⊨ g) over domain sizes 1-2 — every structure where the tuple
    bits fit under 12 and the universe under ENTAIL_MAX_STRUCTURES, else a
    seeded sample of 256."""
    rels, consts = vocabulary(g, h)
    fwd = bwd = True
    for size in (1, 2):
        bits = sum(size ** ar for _, ar in rels)
        cap = 12 if 2 ** bits * size ** len(consts) <= ENTAIL_MAX_STRUCTURES else -1
        for s in universe(rels, consts, size, cap=cap, sample_n=256, seed=1)[0]:
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
    elif eid == "it-minus-erases-a-copy-of-another-line":
        X = expand(g, m.selection)
        c["source_on_another_line"] += bool(_relaxed_source(g, X))
        c["source_on_any_vertex"] += bool(_relaxed_source(g, X, any_vertex=True))
        c["equivalent"] += all(_entail(g, out.result))
    elif eid == "ins-mixes-arities-without-an-alphabet":
        c["no_declared_alphabet"] += g.alphabet is None
        c["sound"] += _entail(g, out.result)[0]
    elif eid == "era-closure-drags-a-quoting-name":
        import re
        X = expand(g, m.selection)
        name = re.search(r"Quoting name (\S+) selected", out.message)
        iso = {v for v in {x.id for x in g.V} - X if edges_on(g, v) and set(edges_on(g, v)) <= X}
        c["name_is_isolated"] += bool(name and name.group(1) in iso)
    elif eid == "it-minus-strictly-enclosing-only":
        c["on_sheet" if "No enclosing areas" in out.message else "in_a_cut"] += 1


def _relaxed_source(g, X, any_vertex=False) -> bool:
    """legal()'s deiteration search with line identity ignored: an edge's
    vertex outside the copy may match another vertex of the same kind (same
    constant, or any generic line) — or, with ``any_vertex``, ANY vertex, name
    or line. True means the engine's match is a copy up to that choice."""
    import calculus_rules as cr
    strict = cr._same_kind

    def outside(g_, v, w, vmap, cuts):
        return w in vmap if any_vertex else strict(g_, v, w, vmap, cuts, set(), {})

    def relaxed(g_, x, y, vmap, cuts, X_, f):
        if x in g_.nu and y in g_.nu and g_.rel[x] == g_.rel[y] and len(g_.nu[x]) == len(g_.nu[y]):
            return all((f.get(v) == w) if v in X_ else outside(g_, v, w, vmap, cuts)
                       for v, w in zip(g_.nu[x], g_.nu[y]))
        return strict(g_, x, y, vmap, cuts, X_, f)
    cr._same_kind = relaxed
    try:
        c = cr._one_context(g, X)
        return c is not None and bool(cr._source_of_copy(g, X, c))
    finally:
        cr._same_kind = strict


IT_MINUS_CONTROLS = ("*x *y (P x) ~[ (P y) ]", '*y (P "a") ~[ (P y) ]', '(P "a") ~[ (P "b") ]')


def it_minus_control() -> Counter:
    """The hand-built shapes tier A cannot reach (five and four elements with a
    second name): does the engine deiterate an edge whose supposed original
    hooks another line, or another name, and is the result unsound?"""
    from egif_parser_dau import parse_egif
    from tarski import model_set
    c = Counter()
    for text in IT_MINUS_CONTROLS:
        g = parse_egif(text)
        inner = next(e for e in g.nu if g.get_context(e) != g.sheet)
        m = Move("IT-", (inner,))
        out = apply_move(g, m)
        c[f"{text} legal"] = int(bool(legal(g, m)[0]))
        c[f"{text} applied"] = int(out.applied)
        if out.applied:
            fwd, _ = _entail(g, out.result)
            c[f"{text} unsound"] = int(not fwd)
            rels, consts = vocabulary(g, out.result)
            for n in (1, 2):
                us = universe(rels, consts, n, cap=12, sample_n=256, seed=1)[0]
                mg, mh = model_set(g, us), model_set(out.result, us)
                if mg & ~mh:
                    print(f"    control_separating {text}: {us[(mg & ~mh & -(mg & ~mh)).bit_length() - 1]}")
                    break
    return c


def adjudicate(mode_name):
    """Returns (entry id -> kind -> keys, entry id -> figures, unclassified, mixed failing keys)."""
    found, figs, labels = defaultdict(lambda: defaultdict(set)), defaultdict(Counter), defaultdict(set)
    unclassified, failing = [], set()
    for rec, _ in records(mode_name):
        label, detail = refusal(rec, {})
        labels[rec.key].add(label)
        if detail is None:
            continue
        failing.add(rec.key)
        eid = classify(rec, detail)
        if eid is None:
            unclassified.append((rec.key, detail))
            continue
        found[eid][failure_kind("refusal", detail)].add(rec.key)
        c = figs[eid]
        c["moves"] += 1
        c["cell_ok"] += label.split(":", 1)[1] == REASONS[eid][1]
        c[f"tier_{rec.tier}"] += 1
        measure(rec, eid, c)
    for eid in figs:
        figs[eid]["keys"] = len(set().union(*found[eid].values()))
    mixed = sorted(k for k in failing if len(labels[k]) > 1)
    return found, figs, unclassified, mixed


def main(argv):
    if "--reasons" in argv:
        n = refresh_reasons(("refusal",), {eid: ("refusal", r[0], r[2]) for eid, r in REASONS.items()})
        print(f"refreshed {n} refusal reason(s)")
        return
    mode = "exhaustive" if "--exhaustive" in argv else "default"
    found, figs, unclassified, mixed = adjudicate(mode)
    print(f"mode={mode}")
    for eid in sorted(figs):
        print(f"{eid:48s} {REASONS[eid][1]:16s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[eid].items())))
    print(f"failing keys in more than one refusal cell: {len(mixed)} {mixed[:5]}")
    print("it-minus controls: " + " ".join(
        f"{k}={v}" for k, v in sorted(it_minus_control().items())))
    for k, d in unclassified[:20]:
        print("UNCLASSIFIED", k, d)
    if unclassified:
        raise SystemExit(f"{len(unclassified)} unclassified failure(s)")
    if "--write" in argv:
        update_ledger(("refusal",), {eid: ("refusal", r[0], r[2]) for eid, r in REASONS.items()},
                      mode, found)
        print(f"wrote the refusal entries for mode {mode!r}: "
              f"{sum(len(ks) for kinds in found.values() for ks in kinds.values())} keys in {len(found)} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
