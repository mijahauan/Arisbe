"""Adjudication of the soundness layer (spec 2026-09-10 §5.3, §6; Task 8).
The sibling of calculus_adjudication and calculus_adjudication_structure.

Not a test. It classifies every failing soundness instance into its ledger
entry by mechanism, measures the figures the entries' reasons state, prints
one reproducible sample per entry (the smallest source, by EGIF), and on
request rewrites the soundness entries' instance lists (other layers' entries
are kept):

    uv run python tests/calculus_adjudication_soundness.py               # figures only (default mode)
    uv run python tests/calculus_adjudication_soundness.py --write       # + rewrite the ledger
    uv run python tests/calculus_adjudication_soundness.py --exhaustive  # figures in the exhaustive mode

It walks calculus_run.records(mode) and classifies through calculus_classifiers;
--write replaces the soundness entries' instance lists by kind (default) or their
pinned counts by kind (--exhaustive).

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
Controls (hand-built, not tier A, default semantics): each ligature rule on the
generic line (= *x *y) (P x) (Q y) and on (= "a" *y) (P y) — a constant joined to a
generic vertex that carries a relation, where erasing the constant vertex loses P(a) —
applied / equivalent / equivalent_iff_constant_kept.
Also printed: every failure by (rule, legal verdict, kind) and the legal-move count
over ALL of them; every unclassified group in full with its count and a sample; the
evaluated passes by (rule, legal verdict).
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
from calculus_classifiers import classify as _classify, erased_constants as _erased_constants  # noqa: E402
from calculus_classifiers import failure_kind, moved_join as _moved_join  # noqa: E402
from calculus_classifiers import join_deeper_than_its_vertices  # noqa: E402
from calculus_layers import layer_universe, soundness  # noqa: E402
from calculus_ledger import LEDGER, refresh_reasons, update_ledger  # noqa: E402
from calculus_rules import moves  # noqa: E402
from calculus_run import MODES, records  # noqa: E402
from egif_generator_dau import generate_egif  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from tarski import model_set, universe, vocabulary  # noqa: E402

LAYER = "soundness"

# id -> (rule, refusal entry it is the soundness half of, or None, reason).
# Figures quoted are this script's: default ones at DEFAULT_BOUNDS with MODES["default"].sem,
# exhaustive ones (--exhaustive) at EXHAUSTIVE_BOUNDS with MODES["exhaustive"].sem.
REASONS = {
    "ligature-rules-take-a-join-deeper-than-its-vertices": ("RETRACT_LIGATURE", None,
        P + "Dau Lemma 16.3 (p.173) retracts, and Def 16.4 / Cor 16.5 (p.174-175) rearranges, a "
        "ligature placed in ONE context, and Θ itself (Def 24.9, p.269) needs ctx(e_i) = "
        "ctx(v_{i+1}): an identity edge in a cut deeper than the vertices it joins does not make "
        "them one line there — *x *y ~[ (= x y) ] says two things differ. RetractLigatureRule and "
        "RearrangeLigatureRule check only that the selected vertices share a context and are "
        "joined by identity edges (_vertices_form_ligature ignores the edges' contexts), so they "
        "retract such a pair — *x *y ~[ (= x y) ] becomes *x ~[ ] (false) — or rewire it. "
        "Includes both rules (the entry's rule field names the first); not judged by legal(). "
        "Measured by calculus_adjudication_soundness --exhaustive (the figures below, "
        "join_deeper on every move); the default mode reaches none (a pair plus a cut plus an "
        "identity edge exceeds its three-element bound). Separate from "
        "retract-ligature-erases-a-constant-vertex, which erases a name."),
    "it-plus-into-its-own-selection-changes-meaning": ("IT+", "it-plus-into-its-own-selection",
        P + "The soundness half of refusal entry it-plus-into-its-own-selection, the same "
        "mechanism: Dau Def 15.2 iteration (p.164, 166) requires the target c ∉ Cut₀, and the "
        "engine (ITPlusInteraction._validate_dest) copies a selected cut into itself or into a "
        "cut it contains — a move legal() rejects. Iteration is an equivalence (deiteration is its "
        "inverse, Def 15.2), so the result must keep the source's models exactly. Measured by "
        "calculus_adjudication_soundness in the default mode: 265 moves in 262 keys — 261 illegal, "
        "every key an instance of that refusal entry (in_refusal_entry), and 4 on quotation-"
        "bearing corpus graphs where legal() abstains from IT± altogether, the engine again "
        "iterating a cut into itself (not_judged). 74 are UNSOUND — a structure satisfies G but "
        "not G′: ~[ ~[ ] ] (true in every structure) becomes ~[ ~[ ~[ ] ] ] (false in every "
        "structure), separating structure Structure(1, (), ()) — and the other 191 gain models "
        "(~[ ] becomes ~[ ~[ ] ]: false to true). Of the refusal entry's 462 keys, 204 are "
        "evaluated here and pass, every one with G ≡ G′ over the budget (refusal_entry_passing, "
        "passing_equivalent). No failure on a move legal() judges legal."),
    "vertex-era-erases-a-line-not-an-equivalence": ("VERTEX_ERA", "vertex-era-erases-a-line-with-its-edges",
        P + "The soundness half of refusal entry vertex-era-erases-a-line-with-its-edges, the "
        "same mechanism: Dau Def 15.2 (p.164, 166) erases a vertex with E_v = ∅ only, and that "
        "rule is an equivalence (it is reversed by inserting a vertex; for a constant, Def 24.10's "
        "Existence of Constants, p.271). Offered a vertex that has edges, the engine (via ERA, its "
        "only entry point) erases the vertex with all its edges — an erasure, which is one-way. "
        "Measured by calculus_adjudication_soundness in the default mode: 111 moves in 111 keys, "
        "every one illegal and every key an instance of that refusal entry; G ⊨ G′ on all 111 "
        "(sound) and G′ ⊭ G — e.g. *x (P x) becomes the blank sheet, separating structure "
        "Structure(1, (), (('P', ()),)). Of the refusal entry's 198 keys, 69 are evaluated here "
        "and pass, every one with G ≡ G′ over the budget."),
    "merge-vertices-erases-a-constant-vertex": ("MERGE_VERTICES", None,
        P + "Dau Def 16.6 merging (p.175–176) erases v2 and the identity edge e = (v1, v2) and "
        "puts v1 on v2's hooks — derived (Lemma 16.7, p.176–178) for EGIs without constants. "
        "With constants, the ligature transformation rules consider only generic vertices (Def "
        "24.10, p.270; p.272: 'only generic vertices are considered'): a constant vertex's name "
        "is part of what the graph says. The engine (VertexMergingRule._apply_vertex_merge) "
        "merges a constant vertex v2 away regardless, and its name goes with it. Measured by "
        "calculus_adjudication_soundness in the default mode: 4 moves in 2 keys, every one "
        "erasing a constant vertex whose name then appears nowhere in G′ (name_lost 4) and "
        "dissolving the identity edge between two different names (distinct_constants_joined 4): "
        "(= \"a\" \"b\") becomes a lone constant vertex, the assertion a = b lost; G ⊨ G′ on all "
        "4 and G′ ⊭ G, separating structure Structure(2, (('a', 0), ('b', 1)), ()). legal() does "
        "not judge MERGE_VERTICES (its parameters underdetermine the move). At exhaustive bounds and semantics, sizes 1–3 "
        "(figures only; ledgered in Task 10): 156 moves in 108 keys, 12 of them UNSOUND — in a "
        "negative context the lost name flips the direction: *x ~[ (= \"a\" x) ] (something is "
        "not a) becomes *x ~[ ] (false), separating structure Structure(2, (('a', 0),), ()). "
        "Controls: on the hand-built generic line (= *x *y) (P x) (Q y) every applied merge is an "
        "equivalence (2 of 2); on (= \"a\" *y) (P y) the merge that erases the constant vertex "
        "loses P(a) and the one that keeps it is an equivalence (1 of 2; "
        "equivalent_iff_constant_kept 1)."),
    "retract-ligature-erases-a-constant-vertex": ("RETRACT_LIGATURE", None,
        P + "Dau Lemma 16.3 (p.173) retracts a ligature to one of its vertices w0, erasing the "
        "rest — derived for EGIs without constants; with constants the ligature rules consider "
        "only generic vertices (Def 24.10, p.270; p.272). The engine (RetractLigatureRule, w0 = "
        "the first vertex of the unordered selection) retracts away a constant vertex "
        "regardless, and its name goes with it. Measured by calculus_adjudication_soundness at "
        "the default mode: 4 moves in 4 keys (both orders of the selection — calculus_apply."
        "InOrder), every one erasing a constant vertex whose name "
        "then appears nowhere in G′ (name_lost 4) and dissolving the identity edge between two "
        "different names (distinct_constants_joined 4): (= \"a\" \"b\") becomes a lone constant "
        "vertex — which one depends on the unordered selection — the assertion a = b lost; "
        "G ⊨ G′ on both and G′ ⊭ G, separating structure Structure(2, (('a', 0), ('b', 1)), ()). "
        "Not judged by legal(). At exhaustive bounds and semantics, sizes 1–3 (figures only; ledgered in Task 10): 49 "
        "moves in 49 keys, 8 UNSOUND — ~[ (= \"a\" \"b\") ] (a ≠ b) becomes a cut around a lone "
        "constant vertex (false), separating structure Structure(2, (('a', 0), ('b', 1)), ()). "
        "10 further UNSOUND retractions there erase no constant and are not this entry: the join "
        "sits in a cut deeper than its vertices (*x *y ~[ (= x y) ] becomes *x ~[ ]) — left "
        "unclassified for Task 10. "
        "Controls: on the hand-built generic line (= *x *y) (P x) (Q y) the retraction is an "
        "equivalence (1 of 1); on (= \"a\" *y) (P y) it is an equivalence exactly when the "
        "constant vertex survives (equivalent_iff_constant_kept 1; which vertex survives depends "
        "on the unordered selection)."),
    "move-branches-moves-the-identity-edge-it-moves-along": ("MOVE_BRANCHES", None,
        P + "Dau Lemma 16.1 (p.169): given v_aΘv_b in one context and a hook (e,i) on v_a, "
        "putting v_b on that hook yields an equivalent graph. The engine "
        "(MoveBranchesAlongLigatureRule) is not told which hook to move: v_a is the first vertex "
        "of the unordered selection, and it takes the first edge it finds on v_a — here the "
        "identity edge that joins the two selected vertices, i.e. the edge that makes v_aΘv_b — "
        "and re-hooks it: (= \"a\" \"b\") becomes an isolated constant vertex beside a "
        "self-identity of the other name, losing a = b. Not judged by legal(). Measured by "
        "calculus_adjudication_soundness in the default mode: 4 moves in 4 keys (both orders of the "
        "selection), the moved edge is the join in all 4; G ⊨ G′ and G′ ⊭ G, separating structure Structure(2, (('a', 0), "
        "('b', 1)), ()). Not a constants effect: on the hand-built generic control (= *x *y) "
        "(P x) (Q y) the same move yields *x *y (= x x) (P x) (Q y), again not an equivalence "
        "(0 of 1 applied moves equivalent). At exhaustive bounds and semantics, sizes 1–3 (figures only; ledgered in Task "
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


def _sem(exhaustive: bool = False):
    """The layer's own budget for the bounds in use — never one mode's budget on the other's bounds."""
    return MODES["exhaustive" if exhaustive else "default"].sem


def _directions(g, h, sem, tier="A"):
    """(G ⊨ G′, G′ ⊨ G) over every size in the budget, on the layer's structures."""
    rels, consts = vocabulary(g, h)
    fwd = bwd = True
    for n in sem.sizes:
        us, _ = layer_universe(rels, consts, n, sem, tier)
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


def _names_lost(g, h):
    return {v.label for v in g.V if v.label} - {v.label for v in h.V if v.label}


def classify(rec, detail):
    """The soundness entry claiming this failure (calculus_classifiers.SOUNDNESS)."""
    return _classify("soundness", rec, detail)


def measure(rec, detail, c: Counter, refusal_keys, eid, sem):
    g, h = rec.g, rec.outcome.result
    c["unsound" if detail.startswith("UNSOUND") else "not_equivalent"] += 1
    c[{True: "legal", False: "illegal", None: "not_judged"}[rec.verdict]] += 1
    c["sound"] += _directions(g, h, sem, rec.tier)[0]
    ref = REASONS[eid][1]
    if ref:
        c["in_refusal_entry"] += rec.key in refusal_keys[ref]
    if rec.move.rule in ("MERGE_VERTICES", "RETRACT_LIGATURE"):
        c["distinct_constants_joined"] += _dissolved_joins(g, h) > 0
        c["name_lost"] += bool(_names_lost(g, h))
        c["in_a_cut"] += any(g.get_context(v.id) != g.sheet for v in _erased_constants(g, h))
    if rec.move.rule in ("RETRACT_LIGATURE", "REARRANGE_LIGATURE"):
        c["join_deeper"] += join_deeper_than_its_vertices(g, rec.move.selection)
        c[f"rule:{rec.move.rule}"] += 1
    if rec.move.rule == "MOVE_BRANCHES":
        e = next(e for e in g.nu if h.nu.get(e) != g.nu[e])
        c["join_deeper_than_its_vertices"] += any(g.get_context(e) != g.get_context(v) for v in g.nu[e])
        c["generic_line"] += not any(_label(g, v) for v in g.nu[e])
        c["moved_edge_is_the_join"] += _moved_join(rec)


def _egif(x):
    try:
        return generate_egif(x) or "(blank)"
    except Exception as exc:        # a sample line, never a figure
        return f"<{type(exc).__name__}>"


VERDICT = {True: "legal", False: "illegal", None: "not-judged"}


def adjudicate(mode_name):
    """Returns (entry id -> keys, entry id -> figures, entry id -> sample,
    unclassified groups, every failure by group, evaluated passes by group).
    A group is (rule, legal() verdict, failure kind); the last two tallies
    cover ALL moves, classified or not, so the legal-move count cannot miss one."""
    sem = MODES[mode_name].sem
    refusal_keys = defaultdict(set)
    for e in json.loads(LEDGER.read_text())["entries"]:
        refusal_keys[e["id"]] = {k for ks in e["instances"].values() for k in ks}
    watched = {r[1] for r in REASONS.values() if r[1]}
    found, figs, samples = defaultdict(lambda: defaultdict(set)), defaultdict(Counter), {}
    unclassified = {}                # group -> [moves, smallest sample line]
    every, passes = Counter(), Counter()
    passing = defaultdict(set)       # refusal entry -> keys evaluated and passing
    passing_equiv = defaultdict(set)
    failing = set()
    for rec, cache in records(mode_name):
        g, m, verdict = rec.g, rec.move, rec.verdict
        label, detail = soundness(rec, cache)
        if detail is None:
            if not label.startswith("not:"):
                passes[(m.rule, VERDICT[verdict])] += 1
                for ref in watched:
                    if rec.key in refusal_keys[ref]:
                        passing[ref].add(rec.key)
                        if all(_directions(g, rec.outcome.result, sem, rec.tier)):
                            passing_equiv[ref].add(rec.key)
            continue
        failing.add(rec.key)
        group = (m.rule, VERDICT[verdict], detail.split(" at ")[0])
        every[group] += 1
        eid = classify(rec, detail)
        if eid is None:
            line = f"{_egif(g)}  --{m.rule}->  {_egif(rec.outcome.result)}  |  {detail}"
            u = unclassified.setdefault(group, [0, line])
            u[0] += 1
            if (len(line), line) < (len(u[1]), u[1]):
                u[1] = line
            continue
        found[eid][failure_kind("soundness", detail)].add(rec.key)
        figs[eid]["moves"] += 1
        figs[eid][f"tier_{rec.tier}"] += 1
        measure(rec, detail, figs[eid], refusal_keys, eid, sem)
        line = f"{_egif(g)}  --{m.rule}->  {_egif(rec.outcome.result)}  |  {detail}"
        if eid not in samples or (len(line), line) < (len(samples[eid]), samples[eid]):
            samples[eid] = line
    for eid in figs:
        figs[eid]["keys"] = len(set().union(*found[eid].values()))
        ref = REASONS[eid][1]
        if ref:
            figs[eid]["refusal_entry_keys"] = len(refusal_keys[ref])
            figs[eid]["refusal_entry_passing"] = len(passing[ref] - failing)
            figs[eid]["passing_equivalent"] = len(passing_equiv[ref] - failing)
    return found, figs, samples, unclassified, every, passes


# A generic line, and a line joining a constant to a generic vertex that carries a
# relation — the second can fail (erasing the constant vertex loses P(a)).
CONTROLS = ("(= *x *y) (P x) (Q y)", '(= "a" *y) (P y)')


def controls() -> Counter:
    """Each ligature rule on the hand-built controls, per applied move: whether
    it erased a constant vertex, and whether it is an equivalence. RETRACT_LIGATURE
    picks its survivor from an unordered selection, so which vertex it erases may
    vary by process; ``equivalent_iff_constant_kept`` is the invariant figure."""
    sem, c = _sem(), Counter()
    for text in CONTROLS:
        g = parse_egif(text)
        for rule in ("MERGE_VERTICES", "RETRACT_LIGATURE", "MOVE_BRANCHES"):
            iff = True
            for m in moves(rule, g, "A"):
                out = apply_move(g, m)
                if out.applied:
                    equiv = all(_directions(g, out.result, sem))
                    erased = bool(_erased_constants(g, out.result))
                    c[f"{text} {rule}:applied"] += 1
                    c[f"{text} {rule}:equivalent"] += equiv
                    iff &= equiv == (not erased)
            c[f"{text} {rule}:equivalent_iff_constant_kept"] = int(iff)
    return c


def main(argv):
    if "--reasons" in argv:
        n = refresh_reasons((LAYER,), {eid: (LAYER, r[0], r[2]) for eid, r in REASONS.items()})
        print(f"refreshed {n} soundness reason(s)")
        return
    mode = "exhaustive" if "--exhaustive" in argv else "default"
    print(f"mode={mode} semantics={MODES[mode].sem}")
    found, figs, samples, unclassified, every, passes = adjudicate(mode)
    for eid in sorted(figs):
        print(f"{eid:54s} " + " ".join(f"{k}={v}" for k, v in sorted(figs[eid].items())))
        print(f"    sample: {samples[eid]}")
    print("controls (default semantics)  " + " ".join(f"{k}={v}" for k, v in sorted(controls().items())))
    print("evaluated moves that pass, by (rule, legal verdict): " + " ".join(
        f"{r}/{v}={n}" for (r, v), n in sorted(passes.items())))
    print("every failure, by (rule, legal verdict, kind): " + " ".join(
        f"{r}/{v}/{k}={n}" for (r, v, k), n in sorted(every.items())))
    legal_failures = sum(n for (_, v, _), n in every.items() if v == "legal")
    print(f"failures on moves legal() judges LEGAL (over ALL failures, classified or not): {legal_failures}")
    for (r, v, k), (n, line) in sorted(unclassified.items()):
        print(f"UNCLASSIFIED {r}/{v}/{k}: {n} move(s); sample: {line}")
    if unclassified:
        raise SystemExit(f"{sum(n for n, _ in unclassified.values())} unclassified failure(s)")
    if "--write" in argv:
        update_ledger((LAYER,), {eid: (LAYER, r[0], r[2]) for eid, r in REASONS.items()}, mode, found)
        print(f"wrote the soundness entries for mode {mode!r}: "
              f"{sum(len(ks) for kinds in found.values() for ks in kinds.values())} keys in {len(found)} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
