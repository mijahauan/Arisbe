"""A legible diff between two EGIs — the discrepancy report, in EG vocabulary.

``same_graph`` answers *whether* two EGIs denote the same graph (full isomorphism).
When they don't, this module answers *how they differ*, phrased the way a reader
thinks about a graph — containment / scope, incidence, argument order, and what is
missing or extra — rather than as raw element-id deltas.

It is the discrepancy report behind challenge mode (docs/FREEFORM_COMPOSITION_AND_
LEARNING.md, build step 3): present a linear form, the learner draws it freehand,
``read_drawing`` recovers their EGI, and this diff against the parsed target *is the
pedagogy* — and especially the **scope** findings (a relation in the wrong cut, the
classic Beta error). It is content-aligned, not id-aligned: the two EGIs come from
different sources (a parse vs a drawing), so it matches elements by what they *are*:

- **constants** by their label (a named individual);
- **relations** by name, then by their argument signature (best match within a name);
- **generic vertices** (bare lines of identity) by their *incidence* — the set of
  (relation, argument-position) they attach to — so "the same line" in both graphs
  lines up even with different ids.

Each element's **scope** is its polarity + nesting depth (how many cuts enclose it),
so "wrong cut" reads as "inside 1 cut (negative) but should be inside 2 (positive)".
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from eg_navigation import same_graph
from egi_core_dau import RelationalGraphWithCuts
from presentation_ops import element_area

# Finding kinds, in the order a report reads most naturally.
_KIND_ORDER = {"structure": 0, "missing": 1, "extra": 2,
               "scope": 3, "incidence": 4, "order": 5}


@dataclass(frozen=True)
class DiffFinding:
    """One way two EGIs differ, in EG terms.

    ``kind`` ∈ ``structure`` (cut/line counts), ``missing`` / ``extra`` (a relation
    or constant present in one graph only), ``scope`` (right thing, wrong cut /
    polarity), ``incidence`` (a relation connects different things), ``order`` (a
    relation's arguments are in the wrong order).  ``message`` is the human-facing
    explanation; ``subject`` names the relation / constant involved.
    """

    kind: str
    message: str
    subject: str = ""


@dataclass
class DiffReport:
    """The discrepancy report: empty (and ``matches`` true) iff the two EGIs are the
    same graph; otherwise a list of EG-vocabulary findings explaining how they
    differ."""

    matches: bool
    findings: List[DiffFinding] = field(default_factory=list)

    def by_kind(self, kind: str) -> List[DiffFinding]:
        return [f for f in self.findings if f.kind == kind]

    @property
    def summary(self) -> str:
        if self.matches:
            return "The drawing denotes the same graph."
        n = len(self.findings)
        return f"{n} difference{'' if n == 1 else 's'} from the target."


# --------------------------------------------------------------------------- #
# Per-EGI introspection (scope, incidence, tokens).
# --------------------------------------------------------------------------- #


def _nu_index(egi) -> Dict[str, List[Tuple[str, int]]]:
    """vertex id → the (edge id, argument position) it sits at — its incidence."""
    idx: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for e in egi.E:
        for port, vid in enumerate(egi.nu.get(e.id, ())):
            idx[vid].append((e.id, port))
    return idx


def _scope(egi, area_map, elem_id) -> Tuple[str, int]:
    """An element's scope: (polarity, nesting depth) of the area it sits in."""
    area = area_map.get(elem_id, egi.sheet)
    pol, depth = egi.area_polarity(area)
    return (pol.value, depth)


def _scope_desc(scope: Tuple[str, int]) -> str:
    pol, depth = scope
    if depth == 0:
        return "on the sheet"
    return f"inside {depth} cut{'' if depth == 1 else 's'} ({pol})"


def _gsig(view, vid) -> set:
    """A generic line's incidence signature: the (relation-name, port) it sits at."""
    return {(view.egi.get_relation_name(e), p) for (e, p) in view.nu_idx.get(vid, [])}


def _align_lines(T: "_View", A: "_View") -> Dict[Tuple[str, str], str]:
    """Match generic lines across the two graphs by greatest incidence overlap, and
    give each matched pair (and each leftover) a shared display id ``line N``.

    Aligning lines *first* keeps a relation's incidence stable when an *unrelated*
    relation is added/removed: removing Q must read as "missing Q", not as "P now
    connects something different", even though it changed the shared line's full
    incidence signature.  Returns a map ``(side, vertex_id) -> "line N"`` with
    ``side`` in {"t","a"}."""
    t_gen = sorted((v.id for v in T.egi.V if v.is_generic),
                   key=lambda vid: -len(_gsig(T, vid)))
    a_gen = [v.id for v in A.egi.V if v.is_generic]
    out: Dict[Tuple[str, str], str] = {}
    used: set = set()
    n = 0
    for tv in t_gen:
        ts = _gsig(T, tv)
        best, best_ov = None, 0
        for av in a_gen:
            if av in used:
                continue
            ov = len(ts & _gsig(A, av))
            if ov > best_ov:
                best, best_ov = av, ov
        n += 1
        out[("t", tv)] = f"line {n}"
        if best is not None:           # overlap > 0 → the same line in both
            used.add(best)
            out[("a", best)] = f"line {n}"
    for av in a_gen:                   # leftover attempt lines get fresh ids
        if ("a", av) not in out:
            n += 1
            out[("a", av)] = f"line {n}"
    return out


class _View:
    """Cached per-EGI views the diff needs."""

    def __init__(self, egi: RelationalGraphWithCuts, side: str):
        self.egi = egi
        self.side = side
        self.area_map = element_area(egi)
        self.vmap = {v.id: v for v in egi.V}
        self.nu_idx = _nu_index(egi)
        self.line_id: Dict[Tuple[str, str], str] = {}   # set by _align_lines

    def _token(self, vid) -> str:
        v = self.vmap[vid]
        if v.label:
            return v.label
        return self.line_id.get((self.side, vid), "a line")

    def args(self, eid) -> List[Tuple[str, str]]:
        """The edge's arguments as (key, display) pairs in ν order — key and display
        coincide here (a constant's label, or an aligned ``line N``)."""
        return [(self._token(vid), self._token(vid))
                for vid in self.egi.nu.get(eid, ())]

    def scope(self, eid) -> Tuple[str, int]:
        return _scope(self.egi, self.area_map, eid)


# --------------------------------------------------------------------------- #
# The diff.
# --------------------------------------------------------------------------- #


def legible_diff(
    target: RelationalGraphWithCuts, attempt: RelationalGraphWithCuts
) -> DiffReport:
    """How ``attempt`` differs from ``target``, in EG vocabulary.

    Empty findings (and ``matches`` True) iff the two are the same graph.  Otherwise
    the findings explain the differences — missing/extra relations and constants,
    scope (wrong cut/polarity), incidence (wrong connections), and argument order —
    aligned by content, not by element id.
    """
    if same_graph(target, attempt):
        return DiffReport(matches=True, findings=[])

    T, A = _View(target, "t"), _View(attempt, "a")
    line_id = _align_lines(T, A)
    T.line_id = A.line_id = line_id
    findings: List[DiffFinding] = []

    # -- structure: cut count (the shape of the area tree) ------------------- #
    if len(attempt.Cut) != len(target.Cut):
        findings.append(DiffFinding(
            "structure",
            f"The drawing has {len(attempt.Cut)} cut"
            f"{'' if len(attempt.Cut) == 1 else 's'}; the target has "
            f"{len(target.Cut)}.",
        ))

    # -- constants: a named individual present in one graph only / mis-scoped - #
    t_consts = Counter(v.label for v in target.V if v.label)
    a_consts = Counter(v.label for v in attempt.V if v.label)
    for lbl in sorted(t_consts - a_consts):
        findings.append(DiffFinding("missing", f"Missing the individual “{lbl}”.", lbl))
    for lbl in sorted(a_consts - t_consts):
        findings.append(DiffFinding("extra", f"Extra individual “{lbl}” not in the target.", lbl))
    for lbl in sorted(set(t_consts) & set(a_consts)):
        t_sc = sorted(T.scope(v.id) for v in target.V if v.label == lbl)
        a_sc = sorted(A.scope(v.id) for v in attempt.V if v.label == lbl)
        if t_sc != a_sc and len(t_sc) == 1 and len(a_sc) == 1:
            findings.append(DiffFinding(
                "scope",
                f"“{lbl}” is {_scope_desc(a_sc[0])} but should be {_scope_desc(t_sc[0])}.",
                lbl,
            ))

    # -- relations: align by name, then best-match by argument signature ----- #
    t_by_name: Dict[str, List[str]] = defaultdict(list)
    a_by_name: Dict[str, List[str]] = defaultdict(list)
    for e in target.E:
        t_by_name[target.get_relation_name(e.id)].append(e.id)
    for e in attempt.E:
        a_by_name[attempt.get_relation_name(e.id)].append(e.id)

    def _disp_args(args) -> str:
        return ", ".join(d for _, d in args)

    for name in sorted(set(t_by_name) | set(a_by_name)):
        tl = list(t_by_name.get(name, []))
        al = list(a_by_name.get(name, []))
        used: set = set()
        for teid in tl:
            targs = T.args(teid)
            tkeys = [k for k, _ in targs]
            # Best unused attempt edge of this name: prefer same arg order, then
            # same multiset, then any overlap.
            best, best_score = None, -1
            for j, aeid in enumerate(al):
                if j in used:
                    continue
                akeys = [k for k, _ in A.args(aeid)]
                if akeys == tkeys:
                    score = 3
                elif Counter(akeys) == Counter(tkeys):
                    score = 2
                elif set(akeys) & set(tkeys):
                    score = 1
                else:
                    score = 0
                if score > best_score:
                    best, best_score = j, score
            if best is None:
                findings.append(DiffFinding(
                    "missing",
                    f"Missing relation {name}({_disp_args(targs)}), "
                    f"{_scope_desc(T.scope(teid))}.",
                    name,
                ))
                continue
            used.add(best)
            aeid = al[best]
            aargs = A.args(aeid)
            akeys = [k for k, _ in aargs]
            if akeys != tkeys:
                if Counter(akeys) == Counter(tkeys):
                    findings.append(DiffFinding(
                        "order",
                        f"Relation {name}: arguments are ({_disp_args(aargs)}) "
                        f"but should be ({_disp_args(targs)}).",
                        name,
                    ))
                else:
                    findings.append(DiffFinding(
                        "incidence",
                        f"Relation {name} connects ({_disp_args(aargs)}) "
                        f"but should connect ({_disp_args(targs)}).",
                        name,
                    ))
            if A.scope(aeid) != T.scope(teid):
                findings.append(DiffFinding(
                    "scope",
                    f"Relation {name} is {_scope_desc(A.scope(aeid))} "
                    f"but should be {_scope_desc(T.scope(teid))}.",
                    name,
                ))
        for j, aeid in enumerate(al):
            if j not in used:
                aargs = A.args(aeid)
                findings.append(DiffFinding(
                    "extra",
                    f"Extra relation {name}({_disp_args(aargs)}), "
                    f"{_scope_desc(A.scope(aeid))}.",
                    name,
                ))

    findings.sort(key=lambda f: (_KIND_ORDER.get(f.kind, 9), f.subject, f.message))
    return DiffReport(matches=False, findings=findings)


__all__ = ["DiffFinding", "DiffReport", "legible_diff"]
