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
# Figures quoted are this script's: default ones in the default mode with MODES["default"].sem,
# exhaustive ones (--exhaustive) at EXHAUSTIVE_BOUNDS with MODES["exhaustive"].sem.
REASONS = {
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
        "and pass, every one with G ≡ G′ over the budget. "
        "In the exhaustive mode: 1,910 moves in 1,898 keys (1,888 tier A, 22 tier B), all sound, none an equivalence."),
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
    if ref and refusal_keys:
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
    # The refusal-entry figures compare with DEFAULT instance lists: default mode only.
    refusal_keys = defaultdict(set)
    if mode_name == "default":
        for e in json.loads(LEDGER.read_text())["entries"]:
            refusal_keys[e["id"]] = {k for ks in e["instances"].values() for k in ks}
    watched = {r[1] for r in REASONS.values() if r[1]} if mode_name == "default" else set()
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
        if ref and ref in watched:
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
