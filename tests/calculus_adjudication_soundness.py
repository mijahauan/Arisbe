"""Adjudication of the soundness layer (spec 2026-09-10 §5.3, §6; Task 8).
The sibling of calculus_adjudication and calculus_adjudication_structure.

Not a test. It classifies every failing soundness instance into its ledger
entry by mechanism, measures the figures the entries' reasons state, prints
one reproducible sample per entry (the smallest source, by EGIF), and on
request rewrites the soundness entries' instance lists (other layers' entries
are kept):

    uv run python tests/calculus_adjudication_soundness.py               # figures only
    uv run python tests/calculus_adjudication_soundness.py --write       # + rewrite the ledger
    uv run python tests/calculus_adjudication_soundness.py --exhaustive  # figures at EXHAUSTIVE_BOUNDS

The semantics budget is the mode's own (calculus_run.MODES), so "sound" and
"equivalent" below are measured over exactly the structures the layer used.

Figures, per entry ("moves" = candidate moves, "keys" = distinct instance keys):
  unsound / not_equivalent   the layer's verdict on the move (first failure found)
  illegal / not_judged / legal   legal()'s verdict on the move
  sound                      G ⊨ G′ over every size in the budget (G′ loses no model of G)
  in_refusal_entry           keys that are also instances of the named refusal entry
  refusal_entry_keys         the size of that refusal entry
  refusal_entry_passing      that entry's keys the soundness layer evaluates and passes
  passing_equivalent         of those, G ≡ G′ over the budget (the named rule's direction holds)
  distinct_constants_joined  the move dissolves an identity edge between two different names
  name_lost                  a constant name of G appears nowhere in G′
  in_a_cut                   an erased constant vertex sat in a cut, not on the sheet
  moved_edge_is_the_join     MOVE_BRANCHES re-hooked the identity edge joining the two
                             selected vertices (the edge that made them one line)
  join_deeper_than_its_vertices  that edge sits in a deeper context than a vertex it joins,
                             so the two are not Θ-related at all (Def 24.9, p.269)
  generic_line               that edge joins two generic vertices
Controls (hand-built, generic lines, not tier A): each ligature rule on
(= *x *y) (P x) (Q y) and (= "a" *y), applied / equivalent.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

for _p in (Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent / "src"):
    if str(_p) not in sys.path:     # run as a script, not under pytest's pythonpath
        sys.path.insert(0, str(_p))

from calculus_adjudication import P  # noqa: E402
from calculus_apply import apply_move  # noqa: E402
from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, tier_a  # noqa: E402
from calculus_layers import soundness  # noqa: E402
from calculus_ledger import LEDGER, instance_key  # noqa: E402
from calculus_rules import IMPLEMENTED, legal, moves  # noqa: E402
from calculus_run import MODES, Record  # noqa: E402
from canonical_signature import compute_canonical_signatures  # noqa: E402
from egif_generator_dau import generate_egif  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from tarski import model_set, universe, vocabulary  # noqa: E402

LAYER = "soundness"

# id -> (rule, refusal entry it is the soundness half of, or None, reason).
# Figures quoted are this script's, at DEFAULT_BOUNDS with MODES["default"].sem.
REASONS = {
    "it-plus-into-its-own-selection-changes-meaning": ("IT+", "it-plus-into-its-own-selection",
        P + "The soundness half of refusal entry it-plus-into-its-own-selection, the same "
        "mechanism: Dau Def 15.2 iteration (p.164, 166) requires the target c ∉ Cut₀, and the "
        "engine (ITPlusInteraction._validate_dest) copies a selected cut into itself or into a "
        "cut it contains — a move legal() rejects. Iteration is an equivalence (deiteration is its "
        "inverse, Def 15.2), so the result must keep the source's models exactly. Measured by "
        "calculus_adjudication_soundness at the default bounds: 171 moves in 168 keys, every one "
        "illegal and every key an instance of that refusal entry; 17 are UNSOUND — a structure "
        "satisfies G but not G′: ~[ ~[ ] ] (true in every structure) becomes ~[ ~[ ~[ ] ] ] (false "
        "in every structure), separating structure Structure(1, (), ()) — and the other 154 gain "
        "models (~[ ] becomes ~[ ~[ ] ]: false to true). The refusal entry's other 65 keys pass "
        "here (their G ≡ G′ over the budget). No failure on a move legal() judges legal. At "
        "exhaustive bounds (figures only; ledgered in Task 10): 3,228 moves in 3,161 keys, 289 "
        "UNSOUND, every one illegal."),
    "vertex-era-erases-a-line-not-an-equivalence": ("VERTEX_ERA", "vertex-era-erases-a-line-with-its-edges",
        P + "The soundness half of refusal entry vertex-era-erases-a-line-with-its-edges, the "
        "same mechanism: Dau Def 15.2 (p.164, 166) erases a vertex with E_v = ∅ only, and that "
        "rule is an equivalence (it is reversed by inserting a vertex; for a constant, Def 24.10's "
        "Existence of Constants, p.271). Offered a vertex that has edges, the engine (via ERA, its "
        "only entry point) erases the vertex with all its edges — an erasure, which is one-way. "
        "Measured by calculus_adjudication_soundness at the default bounds: 95 moves in 95 keys, "
        "every one illegal and every key an instance of that refusal entry; G ⊨ G′ on all 95 "
        "(sound) and G′ ⊭ G — e.g. *x (P x) becomes the blank sheet, separating structure "
        "Structure(1, (), (('P', ()),)). The refusal entry's other 38 keys pass here (their "
        "G ≡ G′ over the budget). At exhaustive bounds (figures only; ledgered in Task 10): "
        "1,888 moves in 1,876 keys, all illegal, all sound, none UNSOUND."),
    "merge-vertices-erases-a-constant-vertex": ("MERGE_VERTICES", None,
        P + "Dau Def 16.6 merging (p.175–176) erases v2 and the identity edge e = (v1, v2) and "
        "puts v1 on v2's hooks — derived (Lemma 16.7, p.176–178) for EGIs without constants. "
        "With constants, the ligature transformation rules consider only generic vertices (Def "
        "24.10, p.270; p.272: 'only generic vertices are considered'): a constant vertex's name "
        "is part of what the graph says. The engine (VertexMergingRule._apply_vertex_merge) "
        "merges a constant vertex v2 away regardless, and its name goes with it. Measured by "
        "calculus_adjudication_soundness at the default bounds: 4 moves in 2 keys, every one "
        "erasing a constant vertex whose name then appears nowhere in G′ (name_lost 4) and "
        "dissolving the identity edge between two different names (distinct_constants_joined 4): "
        "(= \"a\" \"b\") becomes a lone constant vertex, the assertion a = b lost; G ⊨ G′ on all "
        "4 and G′ ⊭ G, separating structure Structure(2, (('a', 0), ('b', 1)), ()). legal() does "
        "not judge MERGE_VERTICES (its parameters underdetermine the move). At exhaustive bounds "
        "(figures only; ledgered in Task 10): 156 moves in 108 keys, 12 of them UNSOUND — in a "
        "negative context the lost name flips the direction: *x ~[ (= \"a\" x) ] (something is "
        "not a) becomes *x ~[ ] (false), separating structure Structure(2, (('a', 0),), ()). "
        "Controls: on the hand-built (= *x *y) (P x) (Q y) and (= \"a\" *y) every applied merge "
        "is an equivalence (2 of 2 on each)."),
    "retract-ligature-erases-a-constant-vertex": ("RETRACT_LIGATURE", None,
        P + "Dau Lemma 16.3 (p.173) retracts a ligature to one of its vertices w0, erasing the "
        "rest — derived for EGIs without constants; with constants the ligature rules consider "
        "only generic vertices (Def 24.10, p.270; p.272). The engine (RetractLigatureRule, w0 = "
        "the first vertex of the unordered selection) retracts away a constant vertex "
        "regardless, and its name goes with it. Measured by calculus_adjudication_soundness at "
        "the default bounds: 2 moves in 2 keys, every one erasing a constant vertex whose name "
        "then appears nowhere in G′ (name_lost 2) and dissolving the identity edge between two "
        "different names (distinct_constants_joined 2): (= \"a\" \"b\") becomes a lone constant "
        "vertex — which one depends on the unordered selection — the assertion a = b lost; "
        "G ⊨ G′ on both and G′ ⊭ G, separating structure Structure(2, (('a', 0), ('b', 1)), ()). "
        "Not judged by legal(). At exhaustive bounds (figures only; ledgered in Task 10): 49 "
        "moves in 49 keys, 8 UNSOUND — ~[ (= \"a\" \"b\") ] (a ≠ b) becomes a cut around a lone "
        "constant vertex (false), separating structure Structure(2, (('a', 0), ('b', 1)), ()). "
        "Controls: on the hand-built (= *x *y) (P x) (Q y) and (= \"a\" *y) every applied "
        "retraction is an equivalence (1 of 1 on each)."),
    "move-branches-moves-the-identity-edge-it-moves-along": ("MOVE_BRANCHES", None,
        P + "Dau Lemma 16.1 (p.169): given v_aΘv_b in one context and a hook (e,i) on v_a, "
        "putting v_b on that hook yields an equivalent graph. The engine "
        "(MoveBranchesAlongLigatureRule) is not told which hook to move: v_a is the first vertex "
        "of the unordered selection, and it takes the first edge it finds on v_a — here the "
        "identity edge that joins the two selected vertices, i.e. the edge that makes v_aΘv_b — "
        "and re-hooks it: (= \"a\" \"b\") becomes an isolated constant vertex beside a "
        "self-identity of the other name, losing a = b. Not judged by legal(). Measured by "
        "calculus_adjudication_soundness at the default bounds: 2 moves in 2 keys, the moved edge "
        "is the join in both; G ⊨ G′ and G′ ⊭ G, separating structure Structure(2, (('a', 0), "
        "('b', 1)), ()). Not a constants effect: on the hand-built generic control (= *x *y) "
        "(P x) (Q y) the same move yields *x *y (= x x) (P x) (Q y), again not an equivalence "
        "(0 of 1 applied moves equivalent). At exhaustive bounds (figures only; ledgered in Task "
        "10): 106 moves in 106 keys, the join moved in all, 10 on generic lines, 18 UNSOUND — "
        "*x *y ~[ (= x y) ] (two things differ) becomes *x *y ~[ (= y y) ] (false), separating "
        "structure Structure(2, (), ()); in 14 the join sits deeper than a vertex it joins, so "
        "the two are not Θ-related at all (Def 24.9, p.269: ctx(e_i) = ctx(v_{i+1})) — the "
        "engine's check (_vertices_on_same_ligature) ignores contexts. "
        "For the author, a question about the text as well as the engine: Lemma 16.1 as printed "
        "does not exclude e being the only identity edge witnessing v_aΘv_b, and read that way it "
        "is false (the control); its proof (p.170–171) deiterates v3, e4, e1 as a copy of v2, "
        "which needs v2Θv_a without them — available only if v_aΘv_b holds without the moved "
        "hook. The lemma appears to carry that side condition implicitly."),
}


def _sem():
    return MODES["default"].sem


def _directions(g, h, sem):
    """(G ⊨ G′, G′ ⊨ G) over every size in the budget, on the layer's structures."""
    rels, consts = vocabulary(g, h)
    fwd = bwd = True
    for n in sem.sizes:
        us, _ = universe(rels, consts, n, cap=sem.tuple_cap, sample_n=sem.sample_n, seed=sem.seed)
        mg, mh = model_set(g, us), model_set(h, us)
        fwd &= not (mg & ~mh)
        bwd &= not (mh & ~mg)
    return fwd, bwd


def _label(g, v):
    return next(x.label for x in g.V if x.id == v)


def _dissolved_joins(g, h):
    """Identity edges of g joining two different names that h no longer carries
    (removed, or re-hooked so it no longer joins them)."""
    out = 0
    for e, seq in g.nu.items():
        if g.rel[e] == "=" and len(seq) == 2:
            a, b = (_label(g, v) for v in seq)
            if a and b and a != b and h.nu.get(e) != seq:
                out += 1
    return out


def _erased_constants(g, h):
    """Constant vertices of g that h no longer has."""
    kept = {v.id for v in h.V}
    return [v for v in g.V if v.label and v.id not in kept]


def _names_lost(g, h):
    return {v.label for v in g.V if v.label} - {v.label for v in h.V if v.label}


def classify(rec):
    rule, why = rec.move.rule, rec.why
    if rule == "IT+" and rec.verdict is False and "inside the selection" in why:
        return "it-plus-into-its-own-selection-changes-meaning"
    if rule == "VERTEX_ERA" and rec.verdict is False and "not isolated" in why:
        return "vertex-era-erases-a-line-not-an-equivalence"
    h = rec.outcome.result
    if rule == "MERGE_VERTICES" and _erased_constants(rec.g, h):
        return "merge-vertices-erases-a-constant-vertex"
    if rule == "RETRACT_LIGATURE" and _erased_constants(rec.g, h):
        return "retract-ligature-erases-a-constant-vertex"
    if rule == "MOVE_BRANCHES" and _moved_join(rec):
        return "move-branches-moves-the-identity-edge-it-moves-along"
    return None


def _moved_join(rec):
    g, h = rec.g, rec.outcome.result
    changed = [e for e in g.nu if h.nu.get(e) != g.nu[e]]
    return len(changed) == 1 and g.rel[changed[0]] == "=" and \
        set(g.nu[changed[0]]) == set(rec.move.selection)


def measure(rec, detail, c: Counter, refusal_keys, eid, sem):
    g, h = rec.g, rec.outcome.result
    c["unsound" if detail.startswith("UNSOUND") else "not_equivalent"] += 1
    c[{True: "legal", False: "illegal", None: "not_judged"}[rec.verdict]] += 1
    c["sound"] += _directions(g, h, sem)[0]
    ref = REASONS[eid][1]
    if ref:
        c["in_refusal_entry"] += rec.key in refusal_keys[ref]
    if rec.move.rule in ("MERGE_VERTICES", "RETRACT_LIGATURE"):
        c["distinct_constants_joined"] += _dissolved_joins(g, h) > 0
        c["name_lost"] += bool(_names_lost(g, h))
        c["in_a_cut"] += any(g.get_context(v.id) != g.sheet for v in _erased_constants(g, h))
    if rec.move.rule == "MOVE_BRANCHES":
        e = next(e for e in g.nu if h.nu.get(e) != g.nu[e])
        c["join_deeper_than_its_vertices"] += any(g.get_context(e) != g.get_context(v) for v in g.nu[e])
        c["generic_line"] += not any(_label(g, v) for v in g.nu[e])
    if rec.move.rule == "MOVE_BRANCHES":
        c["moved_edge_is_the_join"] += _moved_join(rec)


def _egif(x):
    try:
        return generate_egif(x) or "(blank)"
    except Exception as exc:        # a sample line, never a figure
        return f"<{type(exc).__name__}>"


def adjudicate(bounds):
    """Returns (entry id -> keys, entry id -> figures, entry id -> sample, unclassified)."""
    sem = _sem()
    refusal_keys = defaultdict(set)
    for e in json.loads(LEDGER.read_text())["entries"]:
        refusal_keys[e["id"]] = set(e["instances"])
    watched = {r[1] for r in REASONS.values() if r[1]}
    keys, figs, samples, unclassified = defaultdict(set), defaultdict(Counter), {}, []
    passing = defaultdict(set)       # refusal entry -> keys evaluated and passing
    passing_equiv = defaultdict(set)
    failing = set()
    for gname, g in tier_a(bounds).graphs:
        sigs = compute_canonical_signatures(g)
        cache = {"_sem": sem}
        for rule in IMPLEMENTED:
            for m in moves(rule.name, g, "A"):
                verdict, why = legal(g, m)
                rec = Record("A", gname, g, m, instance_key("A", gname, g, m, sigs),
                             apply_move(g, m), verdict, why)
                label, detail = soundness(rec, cache)
                if detail is None:
                    if not label.startswith("not:"):
                        for ref in watched:
                            if rec.key in refusal_keys[ref]:
                                passing[ref].add(rec.key)
                                if all(_directions(g, rec.outcome.result, sem)):
                                    passing_equiv[ref].add(rec.key)
                    continue
                failing.add(rec.key)
                eid = classify(rec)
                if eid is None:
                    unclassified.append((rec.key, detail))
                    continue
                keys[eid].add(rec.key)
                figs[eid]["moves"] += 1
                measure(rec, detail, figs[eid], refusal_keys, eid, sem)
                line = f"{_egif(g)}  --{m.rule}->  {_egif(rec.outcome.result)}  |  {detail}"
                if eid not in samples or (len(line), line) < (len(samples[eid]), samples[eid]):
                    samples[eid] = line
    for eid in figs:
        figs[eid]["keys"] = len(keys[eid])
        ref = REASONS[eid][1]
        if ref:
            figs[eid]["refusal_entry_keys"] = len(refusal_keys[ref])
            figs[eid]["refusal_entry_passing"] = len(passing[ref] - failing)
            figs[eid]["passing_equivalent"] = len(passing_equiv[ref] - failing)
    return keys, figs, samples, unclassified


CONTROLS = ("(= *x *y) (P x) (Q y)", '(= "a" *y)')


def controls() -> Counter:
    """Each ligature rule on hand-built generic-line graphs: applied / equivalent."""
    sem, c = _sem(), Counter()
    for text in CONTROLS:
        g = parse_egif(text)
        for rule in ("MERGE_VERTICES", "RETRACT_LIGATURE", "MOVE_BRANCHES"):
            for m in moves(rule, g, "A"):
                out = apply_move(g, m)
                if out.applied:
                    c[f"{text} {rule}:applied"] += 1
                    c[f"{text} {rule}:equivalent"] += all(_directions(g, out.result, sem))
    return c


def write_ledger(keys) -> None:
    owner = defaultdict(set)
    for eid, ks in keys.items():
        for k in ks:
            owner[k].add(eid)
    split = {k: e for k, e in owner.items() if len(e) > 1}
    if split:
        raise SystemExit(f"{len(split)} key(s) classified into two entries: {list(split.items())[:5]}")
    kept = [e for e in json.loads(LEDGER.read_text())["entries"] if e["layer"] != LAYER]
    mine = [{"id": eid, "layer": LAYER, "rule": REASONS[eid][0],
             "reason": REASONS[eid][2], "instances": sorted(ks)}
            for eid, ks in keys.items()]
    entries = sorted(kept + mine, key=lambda e: (e["layer"], e["id"]))
    LEDGER.write_text(json.dumps({"entries": entries}, indent=1, ensure_ascii=False) + "\n")


def main(argv):
    exhaustive = "--exhaustive" in argv
    if exhaustive and "--write" in argv:
        raise SystemExit("exhaustive bounds are not ledgered")
    keys, figs, samples, unclassified = adjudicate(EXHAUSTIVE_BOUNDS if exhaustive else DEFAULT_BOUNDS)
    for eid in sorted(figs):
        print(f"{eid:54s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[eid].items())))
        print(f"    sample: {samples[eid]}")
    print("controls  " + " ".join(f"{k}={v}" for k, v in sorted(controls().items())))
    legal_failures = sum(f["legal"] for f in figs.values())
    print(f"failures on moves legal() judges LEGAL: {legal_failures}")
    for k, d in unclassified[:20]:
        print("UNCLASSIFIED", k, d)
    if unclassified:
        raise SystemExit(f"{len(unclassified)} unclassified failure(s)")
    if "--write" in argv:
        write_ledger(keys)
        print(f"wrote {LEDGER.name}: {sum(map(len, keys.values()))} keys in {len(keys)} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
