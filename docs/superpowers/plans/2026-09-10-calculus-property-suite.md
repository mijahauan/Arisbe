# Calculus Property Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test the calculus directly — every legal (and illegal) rule application on every small graph and on the corpus as used — for refusal agreement, structural exactness, strict semantic soundness, and agreement between two evaluators, with every layer counting and pinning what it covered.

**Architecture:** Five small modules in `tests/` (enumeration · Dau rule table + moves + `legal` · Tarski evaluator · run cache · ledger/extent helpers) feed four layer test files. One cached run per mode applies every move once; the layers read its records. A JSON ledger records known failures and can only shrink; a JSON extent file pins every count exactly.

**Tech Stack:** Python 3.12, pytest, `uv`. No new dependencies.

**Spec:** [docs/superpowers/specs/2026-09-10-calculus-property-suite-design.md](../specs/2026-09-10-calculus-property-suite-design.md) — read §1a first; it corrects the rest of the spec, and this plan follows §1a where they differ.

## Global Constraints

- Nothing under `src/` changes except Task 12's two side items (`drawing_validity.py`, `egif_parser_dau.py` — neither is protected). **Never** edit a protected module (`uv run python tools/core_protection_system.py --report` lists them); a defect found in one goes to the ledger.
- Test modules import `src` modules by bare name (`from egi_core_dau import ...`); `pyproject.toml` already puts `src` and `tests` on `pythonpath`.
- `tests/tarski.py` imports only `egi_core_dau` (and `frozendict`, stdlib). It must stay independent of every rule, evaluator, and oracle module.
- `legal()` imports nothing from `formal_transformation_rules`, `subgraph_closure_validator`, `rule_interaction`, or `vertex_splitting_merging_rules`.
- Extents are pinned **exactly** (`==`), never with a floor.
- A failure is never silenced by weakening an assertion. It is either fixed in the suite (if the suite misread Dau — cite the page) or entered in `tests/calculus_ledger.json` with a reason.
- Commits: the pre-commit hook fails on a missing `python` alias. Run `uv run python tools/quality_gate_system.py`; if it passes, `git commit --no-verify`. Never use a `WIP:` prefix. End every message with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Dau citations are to *Mathematical Logic with Diagrams* (2006), book pages; PDF page = book page + 10.

## File Structure

| File | Responsibility |
|---|---|
| `tests/calculus_enum.py` (create) | Tier-A graph enumeration, tier-B collection, `graph_key`, shape predicates, area helpers |
| `tests/tarski.py` (create) | `dominating_nodes`, `Structure`, `satisfies`, structure universes, `sheet_components` |
| `tests/calculus_rules.py` (create) | `DAU_RULES` table, `Move`, `moves`, `units`, `legal` — imports no rule module |
| `tests/calculus_apply.py` (create) | `Outcome`, `apply_move`, `engine_entry_points` — the only module that calls the engine |
| `tests/calculus_expected.py` (create) | The licensed result of each rule, built from the data model; `maps_carried` |
| `tests/calculus_layers.py` (create) | One per-record check per layer: `refusal`, `structure`, `soundness` |
| `tests/calculus_run.py` (create) | `Mode`, the two modes, one cached streaming `run(mode)` feeding every layer |
| `tests/calculus_ledger.py` (create) | Ledger check, `instance_key`, extent assert/write, a draft helper |
| `tests/calculus_ledger.json`, `tests/calculus_extent.json` (create) | The ledger; the pinned extents |
| `tests/calculus_pk1.py` (create) | The P-K1 falsifier procedure |
| `tests/test_calculus_enum.py`, `test_tarski.py`, `test_calculus_pk1.py`, `test_calculus_rules.py`, `test_calculus_legal.py`, `test_calculus_refusal.py`, `test_calculus_structure.py`, `test_calculus_soundness.py`, `test_calculus_differential.py` (create) | One file per unit / layer |
| `pyproject.toml` (modify) | Register the `exhaustive` marker; deselect it by default |
| `src/drawing_validity.py`, `src/egif_parser_dau.py`, `tests/test_tomos_parsing.py`, `tests/test_drawing_validity.py` (modify) | Task 12 side items |

The spec §2 put moves and `legal` in `calculus_enum.py`; they are split into `calculus_rules.py` so each file keeps one responsibility.

---

### Task 1: Tier-A enumerator, shapes, and the measured bounds

**Files:**
- Create: `tests/calculus_enum.py`
- Create: `tests/test_calculus_enum.py`
- Modify: `pyproject.toml` (the `[tool.pytest.ini_options]` table)

**Interfaces:**
- Produces: `Bounds`, `DEFAULT_BOUNDS`, `EXHAUSTIVE_BOUNDS`, `TierAReport(bounds, built, refused_by_core, duplicates, graphs: list[tuple[str, RelationalGraphWithCuts]])`, `tier_a(bounds) -> TierAReport` (cached), `graph_key(g) -> str`, `dedupe(named_graphs) -> tuple[list[tuple[str, G]], int, int]`, `shapes(g) -> frozenset[str]`, `REQUIRED_SHAPES`, `ancestors(g, area) -> list[str]`, `lca(g, areas) -> str`, `line_above_uses(g, vid) -> bool`, `edges_on(g, vid) -> list[str]`, `all_areas(g) -> list[str]`.

- [ ] **Step 1: Register the marker.** In `pyproject.toml`, inside `[tool.pytest.ini_options]`, after the `norecursedirs = [...]` list, add:

```toml
markers = [
    "exhaustive: the calculus property suite at full extent (run with -m exhaustive)",
]
addopts = "-m 'not exhaustive'"
```

`pytest -m exhaustive` overrides the default because the last `-m` wins.

- [ ] **Step 2: Write the failing tests** — `tests/test_calculus_enum.py`:

```python
"""Tier-A enumeration: built directly, de-duplicated up to isomorphism, shape-complete.

Spec 2026-09-10 §3.1. The old EGIF strategy never offered an empty cut or a
zero-arity relation; these tests make the enumerator prove it offers every
shape the calculus must meet, and that it counts what it discarded.
"""
import eg_navigation as nav
from calculus_enum import (
    DEFAULT_BOUNDS, REQUIRED_SHAPES, Bounds, dedupe, graph_key, lca,
    line_above_uses, shapes, tier_a,
)
from egif_parser_dau import parse_egif


def test_every_required_shape_occurs_in_the_default_slice():
    report = tier_a(DEFAULT_BOUNDS)
    seen = set()
    for _, g in report.graphs:
        seen |= shapes(g)
    assert REQUIRED_SHAPES <= seen, f"missing shapes: {sorted(REQUIRED_SHAPES - seen)}"


def test_no_two_kept_graphs_are_isomorphic():
    report = tier_a(Bounds(max_cuts=1, max_edges=1, max_generics=1,
                           constants=("a",), max_constant_spots=1, max_elements=3,
                           relations=(("P", 1),)))
    gs = [g for _, g in report.graphs]
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            assert not nav.same_graph(gs[i], gs[j])


def test_dedupe_merges_isomorphic_graphs_with_different_ids():
    a = parse_egif("(P *x) ~[ (P x) ]")
    b = parse_egif("(P *y) ~[ (P y) ]")
    kept, dups, key_only = dedupe([("a", a), ("b", b)])
    assert (len(kept), dups, key_only) == (1, 1, 0)
    assert graph_key(a) == graph_key(b)


def test_counts_add_up():
    r = tier_a(DEFAULT_BOUNDS)
    assert r.built == r.refused_by_core + r.duplicates + len(r.graphs)


def test_every_kept_graph_has_dominating_nodes():
    # Dau Def 12.5 is part of what an EGI is (Def 12.7); the enumerator must
    # never build a non-EGI, since the core would not refuse one.
    from tarski import dominating_nodes
    assert all(dominating_nodes(g) for _, g in tier_a(DEFAULT_BOUNDS).graphs)


def test_line_above_uses_is_detected():
    g = parse_egif("[*x] ~[ (P x) ]")
    v = next(iter(g.V)).id
    assert line_above_uses(g, v)
    h = parse_egif("~[ (P *x) ]")
    assert not line_above_uses(h, next(iter(h.V)).id)


def test_lca_of_one_area_is_itself():
    g = parse_egif("~[ (P *x) ]")
    c = next(iter(g.Cut)).id
    assert lca(g, [c]) == c
```

- [ ] **Step 3: Run to see them fail.** Run: `uv run pytest tests/test_calculus_enum.py -q`. Expected: collection error, `No module named 'calculus_enum'` (the `tarski` import fails later; Task 2 supplies it — until then `test_every_kept_graph_has_dominating_nodes` is expected to error).

- [ ] **Step 4: Implement** `tests/calculus_enum.py`:

```python
"""Graph enumeration for the calculus property suite.

Spec: docs/superpowers/specs/2026-09-10-calculus-property-suite-design.md §3.
Tier A builds every small graph directly with the core's constructors, never
from a linear form, so no linear form's blind spots are inherited. Tier B
gathers the corpus as used. Every count is returned so a caller can pin it.
"""
from __future__ import annotations

import functools
import hashlib
import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from frozendict import frozendict

import eg_navigation as nav
from canonical_signature import compute_canonical_signatures
from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex

G = RelationalGraphWithCuts
TOMOS = Path(__file__).resolve().parent.parent / "tomos"

# Above this many elements a key collision is counted as a duplicate without
# an isomorphism search (same_graph does not finish on sumo_upper).
SAME_GRAPH_CEILING = 150


@dataclass(frozen=True)
class Bounds:
    max_cuts: int = 2
    max_edges: int = 3
    max_generics: int = 2
    constants: Tuple[str, ...] = ("a", "b")
    max_constant_spots: int = 2
    max_elements: int = 7
    relations: Tuple[Tuple[str, int], ...] = (("p", 0), ("P", 1), ("=", 2), ("R", 2), ("T", 3))


# Measured in Task 1 Step 6; the decision rule is written there.
DEFAULT_BOUNDS = Bounds(max_cuts=2, max_edges=2, max_generics=1, constants=("a", "b"),
                        max_constant_spots=2, max_elements=4,
                        relations=(("p", 0), ("P", 1), ("=", 2), ("T", 3)))
EXHAUSTIVE_BOUNDS = Bounds()

REQUIRED_SHAPES = frozenset({
    "empty_cut", "zero_arity", "ternary", "identity_edge", "two_names",
    "unnormalized_constant", "line_above_uses", "isolated_vertex",
})


# -- area helpers -------------------------------------------------------------

def all_areas(g: G) -> List[str]:
    return [g.sheet] + sorted(c.id for c in g.Cut)


def ancestors(g: G, area: str) -> List[str]:
    """``area`` and every context enclosing it, innermost first, ending at the sheet."""
    out = [area]
    while area != g.sheet:
        area = g.get_context(area)
        out.append(area)
    return out


def lca(g: G, areas: Iterable[str]) -> str:
    """The innermost context enclosing every area given."""
    chains = [ancestors(g, a) for a in areas]
    common = set(chains[0]).intersection(*map(set, chains[1:]))
    return next(a for a in chains[0] if a in common)


def edges_on(g: G, vid: str) -> List[str]:
    return sorted(e for e, seq in g.nu.items() if vid in seq)


def line_above_uses(g: G, vid: str) -> bool:
    """A vertex placed strictly outside the least common area of its edges."""
    uses = edges_on(g, vid)
    if not uses:
        return False
    return g.get_context(vid) != lca(g, [g.get_context(e) for e in uses])


def shapes(g: G) -> FrozenSet[str]:
    out = set()
    if any(not g.area.get(c.id) for c in g.Cut):
        out.add("empty_cut")
    if any(len(g.nu[e.id]) == 0 for e in g.E):
        out.add("zero_arity")
    if any(len(g.nu[e.id]) == 3 for e in g.E):
        out.add("ternary")
    if any(g.rel[e.id] == "=" for e in g.E):
        out.add("identity_edge")
    labels = [v.label for v in g.V if not v.is_generic]
    if len(set(labels)) >= 2:
        out.add("two_names")
    if len(labels) != len(set(labels)):
        out.add("unnormalized_constant")
    if any(v.is_generic and line_above_uses(g, v.id) for v in g.V):
        out.add("line_above_uses")
    if any(not edges_on(g, v.id) for v in g.V):
        out.add("isolated_vertex")
    return frozenset(out)


# -- canonical key and de-duplication ----------------------------------------

def graph_key(g: G) -> str:
    """A UUID-independent key. Equal keys do NOT prove isomorphism (the
    signature is a Weisfeiler-Leman refinement, not a complete invariant), so
    ``dedupe`` confirms within a bucket with ``same_graph``."""
    vs, es, cs = compute_canonical_signatures(g)
    sheet = sorted(
        ("V" if x in vs else "E" if x in es else "C", repr(vs.get(x) or es.get(x) or cs.get(x)))
        for x in g.area.get(g.sheet, frozenset())
    )
    payload = repr((sorted(map(repr, vs.values())), sorted(map(repr, es.values())),
                    sorted(map(repr, cs.values())), sheet))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _size(g: G) -> int:
    return len(g.V) + len(g.E) + len(g.Cut)


def dedupe(named: Iterable[Tuple[str, G]]) -> Tuple[List[Tuple[str, G]], int, int]:
    """Keep one representative per isomorphism class.

    Returns (kept, duplicates, duplicates_by_key_only). Tier-A graphs are
    keyed ``<graph_key>#<index in bucket>``; a tier-B graph keeps its source name.
    """
    buckets: Dict[str, List[G]] = {}
    kept: List[Tuple[str, G]] = []
    dups = key_only = 0
    for name, g in named:
        k = graph_key(g)
        bucket = buckets.setdefault(k, [])
        hit = False
        for h in bucket:
            if _size(g) > SAME_GRAPH_CEILING:
                key_only += 1
                hit = True
                break
            if nav.same_graph(g, h):
                hit = True
                break
        if hit:
            dups += 1
            continue
        bucket.append(g)
        kept.append((name if name else f"{k}#{len(bucket) - 1}", g))
    return kept, dups, key_only


# -- tier A -------------------------------------------------------------------

def _cut_trees(max_cuts: int) -> List[Dict[str, str]]:
    """Every tree of at most two cuts under the sheet, as child -> parent."""
    if max_cuts > 2:
        raise ValueError("cut trees are enumerated for at most two cuts")
    trees = [{}]
    if max_cuts >= 1:
        trees.append({"c1": "S"})
    if max_cuts >= 2:
        trees += [{"c1": "S", "c2": "S"}, {"c1": "S", "c2": "c1"}]
    return trees


def _chain(parent: Dict[str, str], area: str) -> List[str]:
    out = [area]
    while area != "S":
        area = parent[area]
        out.append(area)
    return out


def build(parent: Dict[str, str], vertices: Sequence[Tuple[Optional[str], str]],
          edges: Sequence[Tuple[str, Tuple[int, ...], str]]) -> G:
    """Construct directly: sheet ``S``, cuts ``c1..``, vertices ``v1..``, edges ``e1..``."""
    area: Dict[str, set] = {a: set() for a in ["S", *parent]}
    for c, p in parent.items():
        area[p].add(c)
    V = []
    for i, (label, a) in enumerate(vertices, 1):
        vid = f"v{i}"
        V.append(Vertex(vid) if label is None else Vertex(vid, label=label, is_generic=False))
        area[a].add(vid)
    E, nu, rel = [], {}, {}
    for j, (name, args, a) in enumerate(edges, 1):
        eid = f"e{j}"
        E.append(Edge(eid))
        nu[eid] = tuple(f"v{k + 1}" for k in args)
        rel[eid] = name
        area[a].add(eid)
    return G(V=frozenset(V), E=frozenset(E), nu=frozendict(nu), sheet="S",
             Cut=frozenset(Cut(c) for c in parent),
             area=frozendict({k: frozenset(v) for k, v in area.items()}),
             rel=frozendict(rel))


@dataclass
class TierAReport:
    bounds: Bounds
    built: int = 0
    refused_by_core: int = 0
    duplicates: int = 0
    graphs: List[Tuple[str, G]] = field(default_factory=list)

    def extent(self) -> Dict[str, int]:
        return {"built": self.built, "refused_by_core": self.refused_by_core,
                "duplicates": self.duplicates, "kept": len(self.graphs)}


def _raw(b: Bounds):
    kinds: List[Optional[str]] = [None, *b.constants]
    for parent in _cut_trees(b.max_cuts):
        areas = ["S", *parent]
        options = [(k, a) for k in kinds for a in areas]
        for nv in range(0, b.max_generics + b.max_constant_spots + 1):
            for vs in itertools.combinations_with_replacement(options, nv):
                if sum(1 for k, _ in vs if k is None) > b.max_generics:
                    continue
                if sum(1 for k, _ in vs if k is not None) > b.max_constant_spots:
                    continue
                if len(parent) + nv > b.max_elements:
                    continue
                edge_opts = [
                    (name, args, a)
                    for name, ar in b.relations
                    for args in itertools.product(range(nv), repeat=ar)
                    for a in areas
                    # dominating nodes (Dau Def 12.5): ctx(e) <= ctx(v)
                    if all(vs[k][1] in _chain(parent, a) for k in args)
                ]
                room = b.max_elements - len(parent) - nv
                for ne in range(0, min(b.max_edges, room) + 1):
                    for es in itertools.combinations_with_replacement(edge_opts, ne):
                        yield parent, vs, es


@functools.lru_cache(maxsize=None)
def tier_a(bounds: Bounds = DEFAULT_BOUNDS) -> TierAReport:
    report = TierAReport(bounds)
    built: List[Tuple[str, G]] = []
    for parent, vs, es in _raw(bounds):
        report.built += 1
        try:
            built.append(("", build(parent, vs, es)))
        except ValueError:
            report.refused_by_core += 1
    report.graphs, report.duplicates, _ = dedupe(built)
    return report
```

- [ ] **Step 5: Run.** `uv run pytest tests/test_calculus_enum.py -q -k "not dominating"`. Expected: PASS (6 tests).

- [ ] **Step 6: Measure and fix the bounds.** Run:

```bash
uv run python -c "
import time, sys; sys.path[:0]=['src','tests']
from calculus_enum import tier_a, Bounds, DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS
for m in (3, 4, 5, 6, 7):
    b = Bounds(max_elements=m); t=time.time(); r=tier_a(b); print(m, r.extent(), f'{time.time()-t:.1f}s')
t=time.time(); print('default', tier_a(DEFAULT_BOUNDS).extent(), f'{time.time()-t:.1f}s')
"
```

**Decision rule (write the outcome into the commit message):** `DEFAULT_BOUNDS` keeps `max_elements` at the largest value whose kept count is ≤ 400 **and** still yields every `REQUIRED_SHAPES` member. `EXHAUSTIVE_BOUNDS.max_elements` is the largest value whose enumeration finishes in ≤ 10 minutes and whose kept count is ≤ 20 000 (the move counts in Task 6 multiply this by ~100). If 7 exceeds that, lower it and say so in the commit. Edit the two constants accordingly.

- [ ] **Step 7: Commit.**

```bash
git add pyproject.toml tests/calculus_enum.py tests/test_calculus_enum.py
uv run python tools/quality_gate_system.py && git commit --no-verify -m "Calculus suite: every small graph, built directly and counted

Tier-A enumerator over cut trees, vertex placements and dominating-node
edge placements, de-duplicated by canonical key confirmed with same_graph.
Bounds measured: <paste the measured extents and the chosen max_elements>.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: The Tarski evaluator, validated before it is trusted

**Files:**
- Create: `tests/tarski.py`
- Create: `tests/test_tarski.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (independent by design).
- Produces: `NotAnEGI(ValueError)`, `dominating_nodes(g) -> bool`, `Structure(size, const, ext)` with `.value(label)` and `.holds(rel, args)`, `satisfies(g, s) -> bool`, `vocabulary(*graphs) -> tuple[rels, consts]`, `tuple_bits(rels, size) -> int`, `universe(rels, consts, size, cap, sample_n, seed, una=False) -> tuple[list[Structure], bool]` (bool = exhaustive), `model_set(g, structures) -> int`, `sheet_components(g) -> list[frozenset[str]]`, `restrict(g, ids) -> G`.

- [ ] **Step 1: Write the failing tests** — `tests/test_tarski.py`:

```python
"""The fresh Dau-faithful evaluator (spec 2026-09-10 §4, §1a.5).

Validated on pairs whose answer is known before anything is trusted to it:
constant multiplicity/placement is inert (names always denote), generic
placement is not. These pairs are built fresh; the 8/8 and 3/8 pairs of the
2026-09-09 ruling were measured ad hoc and never kept.
"""
import pytest
from frozendict import frozendict

from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from tarski import (
    NotAnEGI, Structure, dominating_nodes, model_set, satisfies,
    sheet_components, universe, vocabulary,
)

G = RelationalGraphWithCuts


def g_(V, E, nu, area, rel, cuts=()):
    return G(V=frozenset(V), E=frozenset(Edge(e) for e in E), nu=frozendict(nu), sheet="S",
             Cut=frozenset(Cut(c) for c in cuts),
             area=frozendict({k: frozenset(v) for k, v in area.items()}), rel=frozendict(rel))


def equivalent(a, b, sizes=(1, 2, 3)):
    rels, consts = vocabulary(a, b)
    for n in sizes:
        us, _ = universe(rels, consts, n, cap=12, sample_n=512, seed=1)
        if model_set(a, us) != model_set(b, us):
            return False
    return True


S1 = Structure(2, {"a": 0}, {"P": {(0,)}, "Q": set(), "p": {()}})


def test_atoms_constants_and_zero_arity():
    assert satisfies(parse_egif('(P "a")'), S1)
    assert not satisfies(parse_egif('(Q "a")'), S1)
    zero = g_([], ["e1"], {"e1": ()}, {"S": {"e1"}}, {"e1": "p"})
    assert satisfies(zero, S1)  # 0-ary read as a truth value: a declared extension


def test_generic_line_is_quantified_where_it_is_placed():
    above = parse_egif("[*x] ~[ (Q x) ]")   # ∃x ¬Q(x)
    inside = parse_egif("~[ (Q *x) ]")      # ¬∃x Q(x)
    s = Structure(2, {}, {"Q": {(0,)}})
    assert satisfies(above, s) and not satisfies(inside, s)


def test_identity_is_equality():
    eq = g_([Vertex("v1"), Vertex("v2")], ["e1"], {"e1": ("v1", "v2")},
            {"S": {"v1", "v2", "e1"}}, {"e1": "="})
    assert satisfies(eq, Structure(1, {}, {}))
    neq = g_([Vertex("v1"), Vertex("v2")], ["e1"], {"e1": ("v1", "v2")},
             {"S": {"v1", "v2", "c1"}, "c1": {"e1"}}, {"e1": "="}, cuts=["c1"])
    assert satisfies(neq, Structure(2, {}, {})) and not satisfies(neq, Structure(1, {}, {}))


def test_constants_may_codenote():
    g = parse_egif('(P "a") ~[ (P "b") ]')
    assert not satisfies(g, Structure(1, {"a": 0, "b": 0}, {"P": {(0,)}}))
    assert satisfies(g, Structure(2, {"a": 0, "b": 1}, {"P": {(0,)}}))


# -- validation pairs ---------------------------------------------------------

def _constant_pair_one_vs_two_spots():
    one = g_([Vertex("a1", label="a", is_generic=False)], ["e1", "e2"],
             {"e1": ("a1",), "e2": ("a1",)}, {"S": {"a1", "e1", "c1"}, "c1": {"e2"}},
             {"e1": "P", "e2": "Q"}, cuts=["c1"])
    two = g_([Vertex("a1", label="a", is_generic=False), Vertex("a2", label="a", is_generic=False)],
             ["e1", "e2"], {"e1": ("a1",), "e2": ("a2",)},
             {"S": {"a1", "e1", "c1"}, "c1": {"a2", "e2"}}, {"e1": "P", "e2": "Q"}, cuts=["c1"])
    return one, two


def _constant_pair_placement():
    out = g_([Vertex("a1", label="a", is_generic=False)], ["e1"], {"e1": ("a1",)},
             {"S": {"a1", "c1"}, "c1": {"e1"}}, {"e1": "Q"}, cuts=["c1"])
    inn = g_([Vertex("a1", label="a", is_generic=False)], ["e1"], {"e1": ("a1",)},
             {"S": {"c1"}, "c1": {"a1", "e1"}}, {"e1": "Q"}, cuts=["c1"])
    return out, inn


def _generic_pair_placement():
    return parse_egif("[*x] ~[ (Q x) ]"), parse_egif("~[ (Q *x) ]")


def _generic_pair_one_vs_two_lines():
    one = parse_egif("(P *x) ~[ (Q x) ]")
    two = parse_egif("(P *x) ~[ (Q *y) ]")
    return one, two


@pytest.mark.parametrize("pair", [_constant_pair_one_vs_two_spots, _constant_pair_placement])
def test_constant_multiplicity_and_placement_are_inert(pair):
    assert equivalent(*pair())


@pytest.mark.parametrize("pair", [_generic_pair_placement, _generic_pair_one_vs_two_lines])
def test_generic_multiplicity_and_placement_are_meaning(pair):
    assert not equivalent(*pair())


# -- guards -------------------------------------------------------------------

def test_a_non_egi_is_refused_not_evaluated():
    bad = g_([Vertex("v1")], ["e1"], {"e1": ("v1",)}, {"S": {"e1", "c1"}, "c1": {"v1"}},
             {"e1": "P"}, cuts=["c1"])
    assert not dominating_nodes(bad)
    assert dominating_nodes(parse_egif("(P *x) ~[ (Q x) ]"))
    with pytest.raises(NotAnEGI):
        satisfies(bad, S1)


def test_universe_is_exhaustive_under_the_cap_and_says_so():
    us, exhaustive = universe((("P", 1),), ("a",), 2, cap=12, sample_n=10, seed=1)
    assert exhaustive and len(us) == 2 * 2 ** 2
    us, exhaustive = universe((("T", 3),), (), 3, cap=12, sample_n=10, seed=1)
    assert not exhaustive and len(us) == 10


def test_una_universe_assigns_names_injectively():
    us, _ = universe((), ("a", "b"), 2, cap=12, sample_n=10, seed=1, una=True)
    assert all(s.value("a") != s.value("b") for s in us) and len(us) == 2


def test_sheet_components_split_on_shared_lines_only():
    g = parse_egif("(P *x) ~[ (Q x) ] (R *y *z) ~[ (P *w) ]")
    assert len(sheet_components(g)) == 3
```

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_tarski.py -q` → `No module named 'tarski'`.

- [ ] **Step 3: Implement** `tests/tarski.py`:

```python
"""A small evaluator written from Dau's semantics, independent of Arisbe's.

Dau, Mathematical Logic with Diagrams (2006): Def 13.1 (models: non-empty
universe, ``=`` interpreted as equality), Def 13.4 (endoporeutic evaluation —
each vertex is existentially assigned at its own context), Def 24.2 (a
constant vertex is fixed at the denotation of its name; nothing forbids two
names co-denoting). Declared extension: Def 13.1 as printed covers arities
k >= 1 only, while the syntax admits 0-ary relations (Defs 12.1, 12.6); here a
0-ary relation holds iff its extension contains the empty tuple.

Imports only the data model. Quotation ovals are skipped (mention, not use).
"""
from __future__ import annotations

import itertools
import random
from typing import Dict, FrozenSet, Iterable, List, Mapping, Tuple

from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts

G = RelationalGraphWithCuts


class NotAnEGI(ValueError):
    """The graph violates dominating nodes (Dau Def 12.5), so it is not an EGI."""


def _chain(g: G, area: str) -> List[str]:
    out = [area]
    while area != g.sheet:
        area = g.get_context(area)
        out.append(area)
    return out


def dominating_nodes(g: G) -> bool:
    """Dau Def 12.5: ctx(e) <= ctx(v) — each vertex's context is the edge's or encloses it."""
    for e, seq in g.nu.items():
        chain = _chain(g, g.get_context(e))
        if any(g.get_context(v) not in chain for v in seq):
            return False
    return True


class Structure:
    """(U, I) with U = {0..size-1}; ``const`` names -> individuals; ``ext`` relation -> tuples."""

    __slots__ = ("size", "const", "ext", "_key")

    def __init__(self, size: int, const: Mapping[str, int], ext: Mapping[str, Iterable[tuple]]):
        if size < 1:
            raise ValueError("Dau Def 13.1: the universe is non-empty")
        self.size = size
        self.const = dict(const)
        self.ext = {r: frozenset(map(tuple, ts)) for r, ts in ext.items()}
        self._key = (size, tuple(sorted(self.const.items())),
                     tuple(sorted((r, tuple(sorted(ts))) for r, ts in self.ext.items())))

    def value(self, label: str) -> int:
        return self.const[label]

    def holds(self, rel: str, args: Tuple[int, ...]) -> bool:
        if rel == "=":
            return len(args) == 2 and args[0] == args[1]
        return args in self.ext.get(rel, frozenset())

    def __repr__(self) -> str:
        return f"Structure{self._key}"

    def __eq__(self, other) -> bool:
        return isinstance(other, Structure) and self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)


def satisfies(g: G, s: Structure) -> bool:
    """Dau Def 13.4, read at the sheet with the empty valuation."""
    if not dominating_nodes(g):
        raise NotAnEGI("dominating nodes violated (Dau Def 12.5)")
    vmap = {v.id: v for v in g.V}
    cuts = {c.id for c in g.Cut}
    return _holds(g, s, g.sheet, {}, vmap, cuts)


def _holds(g, s, c, val, vmap, cuts) -> bool:
    contents = g.area.get(c, frozenset())
    local = sorted(x for x in contents if x in vmap and vmap[x].is_generic)
    edges = sorted(x for x in contents if x in g.nu)
    inner = sorted(x for x in contents if x in cuts and x not in g.quotation)
    for combo in itertools.product(range(s.size), repeat=len(local)):
        v2 = {**val, **dict(zip(local, combo))}
        if all(s.holds(g.rel[e], tuple(_value(v, v2, vmap, s) for v in g.nu[e])) for e in edges) \
                and not any(_holds(g, s, d, v2, vmap, cuts) for d in inner):
            return True
    return False


def _value(v, val, vmap, s) -> int:
    vert = vmap[v]
    return val[v] if vert.is_generic else s.value(vert.label)


# -- universes of structures -------------------------------------------------

def vocabulary(*graphs: G):
    rels = sorted({(g.rel[e], len(g.nu[e])) for g in graphs for e in g.nu if g.rel[e] != "="})
    consts = sorted({v.label for g in graphs for v in g.V if not v.is_generic})
    return tuple(rels), tuple(consts)


def tuple_bits(rels, size: int) -> int:
    return sum(size ** ar for _, ar in rels)


def _assignments(consts, size, una):
    for a in itertools.product(range(size), repeat=len(consts)):
        if una and len(set(a)) != len(a):
            continue
        yield dict(zip(consts, a))


def universe(rels, consts, size, *, cap, sample_n, seed, una=False):
    """Every structure over (rels, consts) of this size when the tuple bits fit
    under ``cap``; otherwise a seeded sample of ``sample_n``. Returns
    (structures, exhaustive). ``una`` restricts to injective name assignments."""
    tuples = {r: list(itertools.product(range(size), repeat=ar)) for r, ar in rels}
    flat = [(r, t) for r, _ in rels for t in tuples[r]]
    assigns = list(_assignments(consts, size, una))
    if not assigns:
        return [], True
    if len(flat) <= cap:
        out = []
        for a in assigns:
            for mask in range(2 ** len(flat)):
                ext: Dict[str, set] = {r: set() for r, _ in rels}
                for i, (r, t) in enumerate(flat):
                    if mask >> i & 1:
                        ext[r].add(t)
                out.append(Structure(size, a, ext))
        return out, True
    rng = random.Random(f"{seed}|{rels}|{consts}|{size}|{una}")
    out = []
    for _ in range(sample_n):
        a = rng.choice(assigns)
        ext = {r: set() for r, _ in rels}
        for r, t in flat:
            if rng.random() < 0.5:
                ext[r].add(t)
        out.append(Structure(size, a, ext))
    return out, False


def model_set(g: G, structures: List[Structure]) -> int:
    """The models of ``g`` among ``structures``, as a bitset over their indices."""
    bits = 0
    for i, s in enumerate(structures):
        if satisfies(g, s):
            bits |= 1 << i
    return bits


# -- components ---------------------------------------------------------------

def _subtree(g: G, x: str) -> List[str]:
    out = [x]
    for y in g.area.get(x, frozenset()):
        out += _subtree(g, y)
    return out


def sheet_components(g: G) -> List[FrozenSet[str]]:
    """Sheet-level items joined when they share a sheet vertex; each component
    is the item ids with their whole subtrees. Conjuncts in different
    components share no line, so the graph holds iff each component holds."""
    items = sorted(g.area.get(g.sheet, frozenset()))
    sheet_vertices = {x for x in items if x in {v.id for v in g.V}}
    parent = {x: x for x in items}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for x in items:
        for y in _subtree(g, x):
            for v in g.nu.get(y, ()):
                if v in sheet_vertices and v != x:
                    parent[find(x)] = find(v)
    groups: Dict[str, List[str]] = {}
    for x in items:
        groups.setdefault(find(x), []).append(x)
    return [frozenset(y for x in grp for y in _subtree(g, x)) for _, grp in sorted(groups.items())]


def restrict(g: G, ids: FrozenSet[str]) -> G:
    """The sub-EGI on ``ids`` (a union of sheet components), built directly."""
    keep = set(ids)
    area = {g.sheet: frozenset(x for x in g.area.get(g.sheet, ()) if x in keep)}
    for c in g.Cut:
        if c.id in keep:
            area[c.id] = frozenset(g.area.get(c.id, frozenset()))
    return G(V=frozenset(v for v in g.V if v.id in keep),
             E=frozenset(e for e in g.E if e.id in keep),
             nu=frozendict({e: s for e, s in g.nu.items() if e in keep}), sheet=g.sheet,
             Cut=frozenset(c for c in g.Cut if c.id in keep), area=frozendict(area),
             rel=frozendict({e: r for e, r in g.rel.items() if e in keep}))
```

- [ ] **Step 4: Run.** `uv run pytest tests/test_tarski.py tests/test_calculus_enum.py -q`. Expected: PASS (all, including the enumerator's dominating-nodes test).

- [ ] **Step 5: Commit** (`git add tests/tarski.py tests/test_tarski.py`), gate then `--no-verify`, message: `Calculus suite: a Tarski evaluator written from Dau, checked on pairs whose answer is known`.

---

### Task 3: P-K1 — the falsifier on `colore_field`

**Files:**
- Create: `tests/calculus_pk1.py`
- Create: `tests/test_calculus_pk1.py`
- Modify: `docs/superpowers/specs/2026-09-10-calculus-property-suite-design.md` §7 (record the outcome)

**Interfaces:**
- Consumes: `tarski.{satisfies, vocabulary, universe, sheet_components, restrict}`, `calculus_enum.{graph_key, line_above_uses, edges_on, lca}`.
- Produces: `pk1() -> dict` with keys `components_g, components_back, unmatched_g, unmatched_back, lines_above_uses, lines_in_unmatched, structures_tried, separating, attributed, attributed_lines, whole_graph_confirmed, outcome`.

Pre-registered (spec §7): *`tarski` finds a structure separating `colore_field` from its EGIF round trip, and the separation turns on one of its lines placed above their uses.* The operationalization, fixed here before the run:

1. Split both graphs into sheet components (`sheet_components`); pair components across the two graphs by `same_graph`. The **unmatched** components carry every difference.
2. Search structures (sizes 1–3; exhaustive under a 12-bit tuple cap, else 4000 seeded samples) for `s` with `satisfies(GA, s) != satisfies(GB, s)`, where GA/GB are the unmatched parts.
3. **Attribution:** for a separating `s` and each generic line `v` of GA placed above its uses, build `GA_v` = GA with `v` moved down to the least common area of its uses. `v` accounts for `s` iff `satisfies(GA_v, s) == satisfies(GB, s)`.
4. **Whole graph:** a separating `s` separates the whole graphs iff it also satisfies the matched part M (identical in both). Recorded, not required.
5. **Outcome:** `HELD` iff some separating `s` is attributed. `REFUTED: no separation found at this budget` if none separates — which is *not* evidence the round trip preserves meaning, and must be worded so. `REFUTED: separation not attributed` if separations exist but no line accounts for one.

- [ ] **Step 1: Write the test** — `tests/test_calculus_pk1.py`:

```python
"""P-K1 (spec 2026-09-10 §7), operationalized in docs/superpowers/plans/
2026-09-10-calculus-property-suite.md Task 3 before it was run.

The recorded outcome is pinned: if a change moves it, this fails and the
change must be read, not the number updated.
"""
import pytest

from calculus_pk1 import pk1

RECORDED_OUTCOME = None  # set in Task 3 Step 4 from the first run


@pytest.mark.exhaustive
def test_pk1_outcome_is_the_recorded_one():
    result = pk1()
    print(result)
    assert RECORDED_OUTCOME is not None, f"record the outcome: {result['outcome']!r}"
    assert result["outcome"] == RECORDED_OUTCOME
```

- [ ] **Step 2: Implement** `tests/calculus_pk1.py`:

```python
"""P-K1: does colore_field's EGIF round trip change its meaning, and is a line
placed above its uses the reason? See the plan, Task 3, for the procedure."""
from __future__ import annotations

from pathlib import Path

from frozendict import frozendict

import eg_navigation as nav
from calculus_enum import TOMOS, edges_on, graph_key, lca, line_above_uses
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from tarski import restrict, satisfies, sheet_components, universe, vocabulary
from tomos_service import TomosService

SIZES = (1, 2, 3)
CAP, SAMPLES, SEED = 12, 4000, 20260910


def _match(ga, comps_a, gb, comps_b):
    """Pair components by isomorphism; return the unmatched ids of each side."""
    free_b = list(comps_b)
    unmatched_a = []
    for ca in comps_a:
        sa = restrict(ga, ca)
        hit = next((cb for cb in free_b
                    if graph_key(restrict(gb, cb)) == graph_key(sa)
                    and nav.same_graph(sa, restrict(gb, cb))), None)
        if hit is None:
            unmatched_a.append(ca)
        else:
            free_b.remove(hit)
    return unmatched_a, free_b


def _moved_down(g, vid):
    """g with vertex ``vid`` moved to the least common area of its uses."""
    old = g.get_context(vid)
    new = lca(g, [g.get_context(e) for e in edges_on(g, vid)])
    area = dict(g.area)
    area[old] = area[old] - {vid}
    area[new] = area.get(new, frozenset()) | {vid}
    return type(g)(V=g.V, E=g.E, nu=g.nu, sheet=g.sheet, Cut=g.Cut,
                   area=frozendict(area), rel=g.rel)


def pk1() -> dict:
    g = TomosService(Path(TOMOS)).load_uod("colore_field", attest=False).current_egi
    back = parse_egif(generate_egif(g))
    cg, cb = sheet_components(g), sheet_components(back)
    ua, ub = _match(g, cg, back, cb)
    ids_a = frozenset().union(*ua) if ua else frozenset()
    ids_b = frozenset().union(*ub) if ub else frozenset()
    GA, GB = restrict(g, ids_a), restrict(back, ids_b)
    M = restrict(g, frozenset(x for c in cg if c not in ua for x in c))
    lines = sorted(v.id for v in g.V if v.is_generic and line_above_uses(g, v.id))
    in_a = [v for v in lines if v in ids_a]
    out = dict(components_g=len(cg), components_back=len(cb), unmatched_g=len(ua),
               unmatched_back=len(ub), lines_above_uses=len(lines),
               lines_in_unmatched=len(in_a), structures_tried=0, separating=0,
               attributed=0, attributed_lines=[], whole_graph_confirmed=0)
    moved = {v: _moved_down(GA, v) for v in in_a}
    rels, consts = vocabulary(GA, GB, M)
    for n in SIZES:
        structures, _ = universe(rels, consts, n, cap=CAP, sample_n=SAMPLES, seed=SEED)
        for s in structures:
            out["structures_tried"] += 1
            a, b = satisfies(GA, s), satisfies(GB, s)
            if a == b:
                continue
            out["separating"] += 1
            who = [v for v, h in moved.items() if satisfies(h, s) == b]
            if who:
                out["attributed"] += 1
                out["attributed_lines"] = sorted(set(out["attributed_lines"]) | set(who))
                if satisfies(M, s):
                    out["whole_graph_confirmed"] += 1
    if out["attributed"]:
        out["outcome"] = "HELD"
    elif out["separating"]:
        out["outcome"] = "REFUTED: separation not attributed"
    else:
        out["outcome"] = "REFUTED: no separation found at this budget"
    return out
```

- [ ] **Step 3: Time one evaluation before the full run.** Run:

```bash
uv run python -c "
import sys, time; sys.path[:0]=['src','tests']
from calculus_pk1 import *
g = TomosService(Path(TOMOS)).load_uod('colore_field', attest=False).current_egi
back = parse_egif(generate_egif(g)); cg, cb = sheet_components(g), sheet_components(back)
ua, ub = _match(g, cg, back, cb); print('components', len(cg), len(cb), 'unmatched', len(ua), len(ub))
GA = restrict(g, frozenset().union(*ua)); rels, consts = vocabulary(GA); print('vocab', len(rels), len(consts))
s, _ = universe(rels, consts, 2, cap=0, sample_n=1, seed=1); t=time.time(); satisfies(GA, s[0]); print(f'{time.time()-t:.3f}s')
"
```

If one `satisfies` on GA exceeds 0.05 s, lower `SAMPLES` so the whole run fits in 20 minutes, and write the chosen value and the reason into the commit message. If `unmatched` is 0 and 0, the round trip now holds for `colore_field`: stop, report it, and mark P-K1 `REFUTED: the round trip holds` — `test_tomos_parsing`'s `KNOWN_BROKEN` will already be failing with "now round-trips".

- [ ] **Step 4: Run and record.** `uv run pytest tests/test_calculus_pk1.py -m exhaustive -s -q`. It fails with `record the outcome: '<outcome>'`. Set `RECORDED_OUTCOME` to that string, re-run to PASS. In the spec §7, under `P-K1`, append one line: `**Outcome (2026-09-10 run):** <outcome> — <the printed dict's counts, verbatim>.`

- [ ] **Step 5: Commit** (`tests/calculus_pk1.py tests/test_calculus_pk1.py` + the spec), gate, `--no-verify`, message: `P-K1 run: <outcome>` with the counts in the body.

---

### Task 4: Dau's rule table, the moves, and how each reaches the engine

**Files:**
- Create: `tests/calculus_rules.py` (table, `Move`, `moves`, `units` — `legal` is added in Task 5)
- Create: `tests/calculus_apply.py` (`Outcome`, `apply_move`, `engine_entry_points`) — kept apart so `legal` never shares a module with the engine imports
- Create: `tests/test_calculus_rules.py`

**Interfaces:**
- Consumes: `calculus_enum.{all_areas, edges_on, ancestors}`.
- Produces: `DauRule(name, cite, direction, engine, judged)`, `DAU_RULES`, `RULES: dict[str, DauRule]`, `IMPLEMENTED: tuple[DauRule, ...]`, `UNIMPLEMENTED: frozenset[str]`, `INS_CATALOGUE: tuple[str, ...]`, `Move(rule, selection=(), target=None, content=None, hooks=())`, `elements(g) -> list[str]`, `units(g) -> list[tuple[str, ...]]`, `moves(rule, g, tier, units_only=False) -> Iterator[Move]`; in `calculus_apply`: `Outcome(applied, result, message, crashed=False)`, `apply_move(g, m) -> Outcome`, `engine_entry_points() -> frozenset[str]`.

- [ ] **Step 1: Write the failing tests** — `tests/test_calculus_rules.py`:

```python
"""The rule table follows Dau, not the engine (spec 2026-09-10 §1a.2).

Every engine entry point must map to a Dau rule, and every Dau rule with no
entry point is named — so a rule the engine grows, or one it lacks, cannot go
unnoticed.
"""
import inspect

import pytest

from calculus_apply import Outcome, apply_move, engine_entry_points
from calculus_rules import (
    DAU_RULES, INS_CATALOGUE, RULES, UNIMPLEMENTED, Move, moves, units,
)
from egif_parser_dau import parse_egif


def test_every_engine_entry_point_is_a_dau_rule_and_vice_versa():
    assert {r.engine for r in DAU_RULES if r.engine} == engine_entry_points()


def test_the_unimplemented_dau_rules_are_exactly_these():
    assert UNIMPLEMENTED == {"ORIENT_IDENTITY", "LIGATURE_VERTEX", "CONSTANT_IDENTITY",
                             "CONSTANT_EXISTENCE", "SEPARATE_CONSTANT"}


def test_split_merge_module_holds_exactly_two_rules():
    import vertex_splitting_merging_rules as m
    from formal_transformation_rules import FormalTransformationRule
    found = sorted(n for n, c in inspect.getmembers(m, inspect.isclass)
                   if issubclass(c, FormalTransformationRule)
                   and c is not FormalTransformationRule and c.__module__ == m.__name__)
    assert found == ["VertexMergingRule", "VertexSplittingRule"]


def test_every_rule_has_a_direction_and_a_citation():
    for r in DAU_RULES:
        assert r.direction in ("one-way", "equivalence") and r.cite.startswith(("Def", "Lemma"))
    assert {r.name for r in DAU_RULES if r.direction == "one-way"} == {"ERA", "INS"}


@pytest.mark.parametrize("text", INS_CATALOGUE)
def test_ins_catalogue_parses(text):
    parse_egif(text)


def test_tier_a_move_counts_on_a_known_graph():
    g = parse_egif("(P *x) ~[ ]")          # three elements, two areas
    assert len(list(moves("ERA", g, "A"))) == 7
    assert len(list(moves("DC+", g, "A"))) == 8 * 2
    assert len(list(moves("INS", g, "A"))) == 2 * len(INS_CATALOGUE)
    assert len(list(moves("VERTEX_INS", g, "A"))) == 2


def test_units_are_edges_cuts_closed_vertices_and_areas():
    g = parse_egif("(P *x) ~[ (Q x) ]")
    us = units(g)
    assert any(len(u) == 3 for u in us)    # the vertex with both its edges
    assert len(us) == len(set(us))


def test_apply_move_reports_refusal_without_raising():
    g = parse_egif("~[ (P *x) ]")
    e = next(iter(g.E)).id
    out = apply_move(g, Move("ERA", (e,)))
    assert isinstance(out, Outcome) and not out.applied and not out.crashed


def test_apply_move_applies_a_lawful_erasure():
    g = parse_egif("(P *x) (Q x)")
    q = next(e.id for e in g.E if g.rel[e.id] == "Q")
    out = apply_move(g, Move("ERA", (q,)))
    assert out.applied and len(out.result.E) == 1
```

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_calculus_rules.py -q` → `No module named 'calculus_apply'`.

- [ ] **Step 3: Implement** `tests/calculus_rules.py`:

```python
"""Dau's rules and the moves that try them (spec 2026-09-10 §1a.2–§1a.4, §3.3).

The table is Dau's, cited by definition and book page; each rule names the
engine entry point that performs it, or None. ``legal`` (Task 5) states each
precondition independently of the engine and lives in this module, which
therefore must never import the rule modules — see calculus_apply for that.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

from calculus_enum import all_areas, ancestors, edges_on
from egi_core_dau import RelationalGraphWithCuts

G = RelationalGraphWithCuts


@dataclass(frozen=True)
class DauRule:
    name: str
    cite: str
    direction: str          # "one-way" | "equivalence"
    engine: Optional[str]   # "protocol:X" | "engine:X" | "ligature:X" | "split" | "merge" | None
    judged: bool            # is refusal agreement judged by legal()?


DAU_RULES: Tuple[DauRule, ...] = (
    DauRule("ERA", "Def 15.2 erasure, p.164-165: positive contexts", "one-way", "protocol:ERA", True),
    DauRule("INS", "Def 15.2 insertion, p.164-165: negative contexts", "one-way", "protocol:INS", True),
    DauRule("IT+", "Def 15.2 iteration, p.164, 166: no polarity condition", "equivalence", "protocol:IT+", True),
    DauRule("IT-", "Def 15.2 deiteration, p.164, 166", "equivalence", "protocol:IT-", True),
    DauRule("DC+", "Def 15.2 double cuts, p.164: any context", "equivalence", "protocol:DC+", True),
    DauRule("DC-", "Def 15.2 double cuts, p.164: any context", "equivalence", "protocol:DC-", True),
    DauRule("VERTEX_INS", "Def 15.2 inserting a vertex, p.164, 166: any context", "equivalence", "engine:HEAVY_DOT", True),
    DauRule("VERTEX_ERA", "Def 15.2 erasing a vertex, p.164, 166: any context", "equivalence", "protocol:ERA", True),
    DauRule("MOVE_BRANCHES", "Lemma 16.1, p.169", "equivalence", "ligature:MOVE_BRANCHES", False),
    DauRule("EXTEND_LIGATURE", "Lemma 16.2, p.172", "equivalence", "ligature:EXTEND_LIGATURE", False),
    DauRule("RETRACT_LIGATURE", "Lemma 16.3, p.173", "equivalence", "ligature:RETRACT_LIGATURE", False),
    DauRule("REARRANGE_LIGATURE", "Def 16.4, Cor 16.5, p.174-175", "equivalence", "ligature:REARRANGE_LIGATURE", False),
    DauRule("SPLIT_VERTEX", "Def 16.6, Lemma 16.7, p.175-178", "equivalence", "split", False),
    DauRule("MERGE_VERTICES", "Def 16.6 merging, p.176", "equivalence", "merge", False),
    DauRule("ORIENT_IDENTITY", "Def 12.14 orientation of an identity edge, p.138", "equivalence", None, False),
    DauRule("LIGATURE_VERTEX", "Def 12.14 adding/removing a vertex, p.138", "equivalence", None, False),
    DauRule("CONSTANT_IDENTITY", "Def 24.10 constant identity rule, p.271", "equivalence", None, False),
    DauRule("CONSTANT_EXISTENCE", "Def 24.10 existence of constants, p.271", "equivalence", None, False),
    DauRule("SEPARATE_CONSTANT", "Def 24.6, Def 24.10, p.265-271", "equivalence", None, False),
)
RULES = {r.name: r for r in DAU_RULES}
IMPLEMENTED = tuple(r for r in DAU_RULES if r.engine)
UNIMPLEMENTED = frozenset(r.name for r in DAU_RULES if r.engine is None)
LIGATURE_RULES = ("MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE")

# Standalone EGIF. EGIF cannot write a 0-ary relation or an isolated constant,
# so INS never offers them (spec §1a.6).
INS_CATALOGUE: Tuple[str, ...] = (
    "~[ ]", "[*x]", "(P *x)", '(P "a")', "(R *x *y)", "~[ (P *x) ]", '(R "a" *x)',
)


@dataclass(frozen=True)
class Move:
    rule: str
    selection: Tuple[str, ...] = ()
    target: Optional[str] = None
    content: Optional[str] = None
    hooks: Tuple[Tuple[str, int], ...] = ()   # SPLIT_VERTEX: (edge id, 0-based position)


def elements(g: G) -> List[str]:
    return sorted([v.id for v in g.V] + [e.id for e in g.E] + [c.id for c in g.Cut])


def _subsets(xs, lo=0, hi=None):
    hi = len(xs) if hi is None else min(hi, len(xs))
    for k in range(lo, hi + 1):
        yield from itertools.combinations(xs, k)


def units(g: G) -> List[Tuple[str, ...]]:
    """Each edge; each cut; each vertex with its edges; each non-empty area's contents."""
    out = [(e,) for e in sorted(g.nu)]
    out += [(c,) for c in sorted(c.id for c in g.Cut)]
    out += [tuple(sorted({v, *edges_on(g, v)})) for v in sorted(v.id for v in g.V)]
    out += [tuple(sorted(g.area[a])) for a in all_areas(g) if g.area.get(a)]
    return list(dict.fromkeys(out))


def _selections(g: G, tier: str, lo: int, units_only: bool):
    if tier == "A":
        yield from _subsets(elements(g), lo)
        return
    seen = set()
    first = [()] if lo == 0 else []
    rest = [u for u in units(g) if len(u) >= lo]
    if not units_only:
        rest += list(_subsets(elements(g), max(lo, 1), 2))
    for s in first + rest:
        if s not in seen:
            seen.add(s)
            yield s


def moves(rule: str, g: G, tier: str, units_only: bool = False) -> Iterator[Move]:
    """Every candidate application of ``rule`` to ``g`` — legal or not."""
    areas = all_areas(g)
    sels = lambda lo: _selections(g, tier, lo, units_only)  # noqa: E731
    if rule in ("ERA", "IT-", "DC-"):
        for s in sels(1):
            yield Move(rule, s)
    elif rule == "DC+":
        for s in sels(0):
            for a in areas:
                yield Move(rule, s, a)
    elif rule == "IT+":
        for s in sels(1):
            for a in areas:
                yield Move(rule, s, a)
    elif rule == "INS":
        for a in areas:
            for c in INS_CATALOGUE:
                yield Move(rule, (), a, c)
    elif rule == "VERTEX_INS":
        for a in areas:
            yield Move(rule, (), a)
    elif rule == "VERTEX_ERA":
        for x in elements(g):
            yield Move(rule, (x,))
    elif rule in LIGATURE_RULES:
        for s in _subsets(elements(g), 1, 2):
            for a in areas:
                yield Move(rule, s, a)
    elif rule == "SPLIT_VERTEX":
        # Only Def 16.6's domain: ctx(v) >= c >= ctx(e_k) for every moved hook.
        for v in sorted(x.id for x in g.V):
            hooks = [(e, i) for e in edges_on(g, v) for i, w in enumerate(g.nu[e]) if w == v]
            for hs in _subsets(hooks, 1):
                for a in areas:
                    if g.get_context(v) in ancestors(g, a) and all(
                            a in ancestors(g, g.get_context(e)) for e, _ in hs):
                        yield Move(rule, (v,), a, hooks=hs)
    elif rule == "MERGE_VERTICES":
        # Def 16.6 merging (p.176): e = (v1, v2) with ctx(v1) >= ctx(e) = ctx(v2); v2 into v1.
        for e in sorted(g.nu):
            if g.rel[e] == "=" and len(g.nu[e]) == 2:
                for v1, v2 in (g.nu[e], g.nu[e][::-1]):
                    if g.get_context(v2) == g.get_context(e) and \
                            g.get_context(v1) in ancestors(g, g.get_context(e)) and v1 != v2:
                        yield Move(rule, (v1, v2, e))
    else:
        raise KeyError(f"no move generator for {rule}")
```

Then `tests/calculus_apply.py`:

```python
"""How each Dau rule reaches the engine (spec 2026-09-10 §1a.2).

A refusal is the engine's own rejection; any other exception is a crash, and
a crash is a defect. Kept apart from calculus_rules so legal() never shares a
module with the engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional

from calculus_rules import RULES, Move
from egi_core_dau import RelationalGraphWithCuts
from formal_transformation_rules import FormalTransformationEngine
from ligature_manipulation_rules import LigatureManipulationEngine
from proof_authoring import apply_rule
from rule_interaction import RULE_INTERACTIONS
from vertex_splitting_merging_rules import (
    VertexMergingRule, VertexSplitSpec, VertexSplittingRule,
)

G = RelationalGraphWithCuts


@dataclass(frozen=True)
class Outcome:
    applied: bool
    result: Optional[G]
    message: str
    crashed: bool = False


def engine_entry_points() -> FrozenSet[str]:
    pts = {f"protocol:{k}" for k in RULE_INTERACTIONS}
    pts |= {f"engine:{k}" for k in FormalTransformationEngine().rules if k not in RULE_INTERACTIONS}
    pts |= {f"ligature:{k}" for k in LigatureManipulationEngine().rules}
    pts |= {"split", "merge"}   # two classes, no registry (checked in the tests)
    return frozenset(pts)


def apply_move(g: G, m: Move) -> Outcome:
    engine = RULES[m.rule].engine
    try:
        if engine.startswith("protocol:"):
            res = apply_rule(engine.split(":", 1)[1], g, selection=list(m.selection),
                             egif=m.content, target=m.target)
            return Outcome(True, res, "")
        if engine.startswith("engine:"):
            r = FormalTransformationEngine().apply_rule(
                engine.split(":", 1)[1], g, m.target, frozenset(m.selection))
            return Outcome(bool(r.success), r.result_egi if r.success else None, r.error_message or "")
        if engine.startswith("ligature:"):
            r = LigatureManipulationEngine().apply_rule(
                engine.split(":", 1)[1], g, m.target, frozenset(m.selection))
            return Outcome(bool(r.success), r.result_egi if r.success else None, r.error_message or "")
        if engine == "split":
            spec = VertexSplitSpec(source_vertex=m.selection[0], target_context=m.target,
                                   hooks_to_move=list(m.hooks), new_vertex_id="split_new_v")
            return Outcome(True, VertexSplittingRule()._apply_vertex_split(g, spec), "")
        if engine == "merge":
            v1, v2, e = m.selection
            return Outcome(True, VertexMergingRule()._apply_vertex_merge(
                g, v1_id=v1, v2_id=v2, identity_edge_id=e), "")
    except AssertionError as exc:          # the protocol's own rejection
        return Outcome(False, None, str(exc))
    except Exception as exc:               # anything else is a crash
        return Outcome(False, None, f"{type(exc).__name__}: {exc}", crashed=True)
    raise KeyError(f"{m.rule} has no engine entry point")
```

- [ ] **Step 4: Run.** `uv run pytest tests/test_calculus_rules.py -q`. Expected: PASS. If `test_every_engine_entry_point...` fails, the engine has a rule this table lacks (or the reverse): add or correct the row with its Dau citation — do not delete the test.

- [ ] **Step 5: Commit** (`tests/calculus_rules.py tests/calculus_apply.py tests/test_calculus_rules.py`), gate, `--no-verify`, message: `Calculus suite: Dau's rule table, every candidate move, and the engine's entry points`.

---

### Task 5: `legal()` — Dau's preconditions, stated independently

**Files:**
- Modify: `tests/calculus_rules.py` (append; also narrow the `VERTEX_ERA` generator)
- Create: `tests/test_calculus_legal.py`

**Interfaces:**
- Consumes: `tarski.dominating_nodes`, `calculus_enum.{ancestors, all_areas, edges_on}`, `egif_parser_dau.parse_egif`.
- Produces: `Verdict = tuple[Optional[bool], str]` (None = not judged, with the reason), `legal(g, m) -> Verdict`, `expand(g, ids) -> set[str]`, `tops(g, X) -> list[str]`, `positive(g, area) -> bool`, `IT_MINUS_BUDGET`.

Each rule's docstring states Dau's condition, the page, and — where Arisbe's shared-vertex form differs from Dau's identity edges — the reading and why it is a Dau derivation (spec §1a.4). `legal` must not import `formal_transformation_rules`, `subgraph_closure_validator`, `rule_interaction`, or `vertex_splitting_merging_rules`.

- [ ] **Step 1: Narrow `VERTEX_ERA` to vertices.** In `moves`, replace

```python
    elif rule == "VERTEX_ERA":
        for x in elements(g):
            yield Move(rule, (x,))
```

with

```python
    elif rule == "VERTEX_ERA":
        # Dau's vertex rule is about vertices; an edge offered here would be
        # performed by the ERA entry point and read as applied-but-illegal.
        for x in sorted(v.id for v in g.V):
            yield Move(rule, (x,))
```

- [ ] **Step 2: Write the failing tests** — `tests/test_calculus_legal.py`:

```python
"""legal() against hand-built cases, each cited to Dau (2006), book pages.

These cases fix what the suite means by "legal" before it is compared with
the engine: a disagreement later is then a question about the engine or about
this reading of Dau, never about an unstated assumption.
"""
from calculus_rules import Move, legal
from egif_parser_dau import parse_egif


def _edge(g, rel):
    return next(e for e in sorted(g.nu) if g.rel[e] == rel)


def _cuts_by_depth(g):
    from calculus_enum import ancestors
    return sorted((c.id for c in g.Cut), key=lambda c: len(ancestors(g, c)))


def _vertex(g):
    return sorted(v.id for v in g.V)[0]


def ok(g, m):
    return legal(g, m)[0]


# ERA — Def 15.2, p.164-165
def test_era_single_edge_needs_no_closure():            # p.165, the edge rule
    g = parse_egif("(P *x) (Q x)")
    assert ok(g, Move("ERA", (_edge(g, "Q"),))) is True


def test_era_vertex_alone_would_dangle():
    g = parse_egif("(P *x) (Q x)")
    assert ok(g, Move("ERA", (_vertex(g),))) is False


def test_era_refused_in_a_negative_context():
    g = parse_egif("~[ (P *x) ]")
    assert ok(g, Move("ERA", (_edge(g, "P"),))) is False


def test_era_of_a_cut_on_an_outer_line():               # p.166-167, Dau's own remark
    g = parse_egif("(P *x) ~[ (Q x) ]")
    assert ok(g, Move("ERA", (_cuts_by_depth(g)[0],))) is True


# INS — Def 15.2, p.164-165
def test_ins_into_a_negative_context_only():
    g = parse_egif("~[ ]")
    c = _cuts_by_depth(g)[0]
    assert ok(g, Move("INS", (), c, "(P *x)")) is True
    assert ok(g, Move("INS", (), g.sheet, "(P *x)")) is False


# DC+ / DC- — Def 15.2, p.164
def test_dc_plus_empty_anywhere():
    g = parse_egif("~[ ]")
    assert ok(g, Move("DC+", (), g.sheet)) is True
    assert ok(g, Move("DC+", (), _cuts_by_depth(g)[0])) is True


def test_dc_plus_moves_a_vertex_inward_only_with_its_edges():   # Def 12.5 on the result
    g = parse_egif("(P *x) (Q x)")
    v = _vertex(g)
    assert ok(g, Move("DC+", (v,), g.sheet)) is False
    assert ok(g, Move("DC+", (v, _edge(g, "P"), _edge(g, "Q")), g.sheet)) is True


def test_dc_minus_needs_exactly_one_inner_cut():
    g = parse_egif("~[ ~[ (P *x) ] ]")
    assert ok(g, Move("DC-", (_cuts_by_depth(g)[0],))) is True
    h = parse_egif("~[ (Q *y) ~[ (P *x) ] ]")
    assert ok(h, Move("DC-", (_cuts_by_depth(h)[0],))) is False


# IT+ / IT- — Def 15.2, p.164, 166
def test_it_plus_into_the_same_or_a_nested_context():   # c <= ctx(G0) includes equality
    g = parse_egif("(P *x) ~[ ]")
    p = _edge(g, "P")
    assert ok(g, Move("IT+", (p,), _cuts_by_depth(g)[0])) is True
    assert ok(g, Move("IT+", (p,), g.sheet)) is True


def test_it_plus_never_outward():
    g = parse_egif("~[ (P *x) ]")
    assert ok(g, Move("IT+", (_edge(g, "P"),), g.sheet)) is False


def test_it_minus_finds_the_source_it_was_copied_from():
    g = parse_egif("(P *x) ~[ (P x) ]")
    inner = next(e for e in g.nu if g.get_context(e) != g.sheet)
    assert ok(g, Move("IT-", (inner,))) is True
    h = parse_egif("(P *x) ~[ (Q x) ]")
    assert ok(h, Move("IT-", (_edge(h, "Q"),))) is False


def test_it_minus_in_the_same_context():
    g = parse_egif("(P *x) (P x)")
    assert ok(g, Move("IT-", (sorted(g.nu)[0],))) is True


# Isolated vertices — Def 15.2, p.164, 166: ANY context
def test_vertex_rules_ignore_polarity():
    g = parse_egif("~[ [*x] ]")
    assert ok(g, Move("VERTEX_ERA", (_vertex(g),))) is True
    assert ok(g, Move("VERTEX_INS", (), g.sheet)) is True
    assert ok(g, Move("VERTEX_INS", (), _cuts_by_depth(g)[0])) is True
    h = parse_egif("(P *x)")
    assert ok(h, Move("VERTEX_ERA", (_vertex(h),))) is False


# Not judged
def test_rules_whose_parameters_underdetermine_the_move_are_not_judged():
    g = parse_egif("(P *x)")
    verdict, why = legal(g, Move("MOVE_BRANCHES", (_vertex(g),), g.sheet))
    assert verdict is None and why.startswith("not judged")


def test_a_non_egi_source_is_not_judged():
    from frozendict import frozendict
    from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
    bad = RelationalGraphWithCuts(
        V=frozenset({Vertex("v1")}), E=frozenset({Edge("e1")}), nu=frozendict({"e1": ("v1",)}),
        sheet="S", Cut=frozenset({Cut("c1")}),
        area=frozendict({"S": frozenset({"e1", "c1"}), "c1": frozenset({"v1"})}),
        rel=frozendict({"e1": "P"}))
    assert legal(bad, Move("ERA", ("e1",)))[0] is None


def test_unknown_ids_are_illegal():
    g = parse_egif("(P *x)")
    assert ok(g, Move("ERA", ("nope",))) is False
    assert ok(g, Move("VERTEX_INS", (), "nope")) is False
```

- [ ] **Step 3: Run to see them fail.** `uv run pytest tests/test_calculus_legal.py -q` → `ImportError: cannot import name 'legal'`.

- [ ] **Step 4: Implement** — append to `tests/calculus_rules.py` (and add `from egif_parser_dau import parse_egif` and `from tarski import dominating_nodes` to its imports):

```python
# -- legal -------------------------------------------------------------------

Verdict = Tuple[Optional[bool], str]
IT_MINUS_BUDGET = 20000


def expand(g: G, ids) -> set:
    """``ids`` with the whole contents of every cut among them."""
    out, stack = set(), list(ids)
    while stack:
        x = stack.pop()
        if x not in out:
            out.add(x)
            stack.extend(g.area.get(x, ()))
    return out


def tops(g: G, X: set) -> List[str]:
    return sorted(x for x in X if g.get_context(x) not in X)


def positive(g: G, area: str) -> bool:
    """The sheet is positive; an outermost cut's area is negative (the reading
    the calculus requires — Def 12.4's printed count includes the cut itself)."""
    return (len(ancestors(g, area)) - 1) % 2 == 0


def _one_context(g: G, X: set) -> Optional[str]:
    ctxs = {g.get_context(t) for t in tops(g, X)}
    return next(iter(ctxs)) if len(ctxs) == 1 else None


def _nothing_dangles(g: G, X: set) -> bool:
    vids = {v.id for v in g.V}
    return all(set(edges_on(g, x)) <= X for x in X if x in vids)


def _touches_quotation(g: G, ids, target) -> bool:
    if not g.quotation and not g.sort:
        return False
    apparatus = set(g.quotation) | set(g.quotation.values()) | set(g.sort)
    inside = set().union(*(expand(g, [c]) for c in g.quotation)) if g.quotation else set()
    return any(x in apparatus or x in inside for x in ids) or target in inside


def legal(g: G, m: Move) -> Verdict:
    rule = RULES[m.rule]
    if not rule.judged:
        return None, f"not judged: {m.rule}'s parameters underdetermine the move"
    if not dominating_nodes(g):
        return None, "not judged: the source is not an EGI (Def 12.5)"
    known = set(elements(g))
    if any(x not in known for x in m.selection):
        return False, "the selection names an unknown element"
    if m.target is not None and m.target not in all_areas(g):
        return False, "the target is not a context"
    if _touches_quotation(g, m.selection, m.target):
        return None, "not judged: the quotation apparatus (B-min is Arisbe's, not Dau's)"
    return _LEGAL[m.rule](g, m)


def _era(g: G, m: Move) -> Verdict:
    """Def 15.2 erasure (p.164-165): in a positive context, any directly
    enclosed edge, isolated vertex, or closed subgraph may be erased.

    Shared-vertex reading: an edge may go without its vertex — Dau's edge
    rule carries no closure condition (p.165) — and a selection holding an
    edge on an outer line is Dau's own worked derivation (add a vertex to the
    ligature, erase, erase; p.166-167). A multi-element selection is a run of
    erasures in one context, so it must sit in one positive context and leave
    no edge without its vertex."""
    if not m.selection:
        return False, "empty selection"
    X = expand(g, m.selection)
    c = _one_context(g, X)
    if c is None:
        return False, "the selection spans several contexts"
    if not positive(g, c):
        return False, "the context is negative"
    if not _nothing_dangles(g, X):
        return False, "a selected vertex would leave an edge behind"
    return True, "positive context, nothing left dangling"


def _ins(g: G, m: Move) -> Verdict:
    """Def 15.2 insertion (p.164-165): in a negative context, any edge,
    isolated vertex, or closed subgraph may be inserted. The content is a
    standalone graph, so it is closed and has dominating nodes."""
    try:
        parse_egif(m.content or "")
    except Exception:
        return False, "the content does not parse"
    if m.target is None or positive(g, m.target):
        return False, "the target is not a negative context"
    return True, "negative context"


def _dc_plus(g: G, m: Move) -> Verdict:
    """Def 15.2 double cuts (p.164): area(c1) = {c2}, in any context.
    Insertion reverses erasure, so c1 enters the target and c2 receives some
    of the target's direct contents. A vertex may move inward only with all
    its edges, or the result breaks dominating nodes (Def 12.5)."""
    if m.target is None:
        return False, "no target"
    if any(g.get_context(x) != m.target for x in m.selection):
        return False, "the selection is not directly in the target"
    if not _nothing_dangles(g, expand(g, m.selection)):
        return False, "a vertex would move inside its own edge's context"
    return True, "any context"


def _dc_minus(g: G, m: Move) -> Verdict:
    """Def 15.2 double cuts (p.164): two cuts with area(c1) = {c2} may be erased, any context."""
    cuts = {c.id for c in g.Cut}
    if len(m.selection) != 1 or m.selection[0] not in cuts:
        return False, "select exactly the outer cut"
    inner = g.area.get(m.selection[0], frozenset())
    if len(inner) != 1 or next(iter(inner)) not in cuts:
        return False, "its area is not exactly one cut"
    return True, "a double cut"


def _it_plus(g: G, m: Move) -> Verdict:
    """Def 15.2 iteration (p.164, 166): a (not necessarily closed) subgraph in
    context c0 may be copied into any context c <= c0, c not inside it; no
    polarity condition, and c = c0 is allowed.

    Shared-vertex reading: an unselected vertex of a selected edge is the
    Θ-linked vertex of Def 15.2's second clause, reused by pointing at it
    rather than joined by an identity edge (equivalent by Lemma 16.3)."""
    if not m.selection:
        return False, "empty selection"
    X = expand(g, m.selection)
    c0 = _one_context(g, X)
    if c0 is None:
        return False, "the selection spans several contexts"
    if m.target is None or c0 not in ancestors(g, m.target):
        return False, "the target is not within the source context"
    if m.target in X:
        return False, "the target lies inside the selection"
    return True, "target within the source context"


def _it_minus(g: G, m: Move) -> Verdict:
    """Def 15.2 deiteration (p.164, 166): a subgraph may be erased if it could
    have been inserted by iteration — there is a source, disjoint from it, in
    a context enclosing (or equal to) its own, of which it is a copy: same
    kinds, relation names and constant labels, same nesting, and each edge
    reaching either the copy of its source's vertex or the very same vertex
    (a reused line — the shared-vertex form of the Θ clause)."""
    if not m.selection:
        return False, "empty selection"
    X = expand(g, m.selection)
    c = _one_context(g, X)
    if c is None:
        return False, "the selection spans several contexts"
    if not _nothing_dangles(g, X):
        return False, "erasing it would leave an edge behind"
    found = _source_of_copy(g, X, c)
    if found is None:
        return None, "not judged: the IT- search budget was exceeded"
    return (True, "a source exists") if found else (False, "no source of which this is a copy")


def _source_of_copy(g: G, X: set, c: str) -> Optional[bool]:
    vmap = {v.id: v for v in g.V}
    cuts = {k.id for k in g.Cut}
    order = (sorted((x for x in X if x in cuts), key=lambda x: len(ancestors(g, x)))
             + sorted(x for x in X if x in vmap) + sorted(x for x in X if x in g.nu))
    budget = [IT_MINUS_BUDGET]
    for c1 in ancestors(g, c):
        if _extend(g, X, order, 0, {}, c, c1, vmap, cuts, budget):
            return True
        if budget[0] < 0:
            return None
    return False


def _same_kind(g, x, y, vmap, cuts, X, f) -> bool:
    if x in cuts:
        return y in cuts
    if x in vmap:
        return y in vmap and vmap[x].is_generic == vmap[y].is_generic \
            and vmap[x].label == vmap[y].label
    if y not in g.nu or g.rel[x] != g.rel[y] or len(g.nu[x]) != len(g.nu[y]):
        return False
    for v, w in zip(g.nu[x], g.nu[y]):
        if (f.get(v) != w) if v in X else (v != w):
            return False
    return True


def _extend(g, X, order, i, f, c, c1, vmap, cuts, budget) -> bool:
    if i == len(order):
        return all(set(g.area.get(f[x], ())) == {f[y] for y in g.area.get(x, ())}
                   for x in order if x in cuts)
    x = order[i]
    px = g.get_context(x)
    py = c1 if px == c else f.get(px)
    if py is None:
        return False
    used = set(f.values())
    for y in sorted(g.area.get(py, ())):
        budget[0] -= 1
        if budget[0] < 0:
            return False
        if y in X or y in used or not _same_kind(g, x, y, vmap, cuts, X, f):
            continue
        f[x] = y
        if _extend(g, X, order, i + 1, f, c, c1, vmap, cuts, budget):
            return True
        del f[x]
    return False


def _vertex_ins(g: G, m: Move) -> Verdict:
    """Def 15.2 inserting a vertex (p.164, 166): an isolated vertex may be inserted in ANY context."""
    return (True, "any context") if m.target is not None else (False, "no target")


def _vertex_era(g: G, m: Move) -> Verdict:
    """Def 15.2 erasing a vertex (p.164, 166): an isolated vertex may be erased from ANY context."""
    if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
        return False, "not a single vertex"
    if edges_on(g, m.selection[0]):
        return False, "the vertex is not isolated"
    return True, "an isolated vertex, any context"


_LEGAL = {"ERA": _era, "INS": _ins, "DC+": _dc_plus, "DC-": _dc_minus, "IT+": _it_plus,
          "IT-": _it_minus, "VERTEX_INS": _vertex_ins, "VERTEX_ERA": _vertex_era}
```

- [ ] **Step 5: Run.** `uv run pytest tests/test_calculus_legal.py tests/test_calculus_rules.py -q`. Expected: PASS. A failing case here means `legal` misreads Dau: fix `legal`, never the case — unless the case itself contradicts the cited page, in which case correct the case and quote the page in the commit message.

- [ ] **Step 6: Guard the independence.** Append to `tests/test_calculus_legal.py`:

```python
def test_legal_never_consults_the_engine():
    import calculus_rules
    src = open(calculus_rules.__file__).read()
    for forbidden in ("formal_transformation_rules", "subgraph_closure_validator",
                      "rule_interaction", "vertex_splitting_merging_rules", "proof_authoring"):
        assert forbidden not in src, forbidden
```

Run it; expected PASS.

- [ ] **Step 7: Commit** (`tests/calculus_rules.py tests/test_calculus_legal.py`), gate, `--no-verify`, message: `Calculus suite: legal() — Dau's preconditions, stated without the engine`.

---

### Task 6: The ledger, the extent pins, one streaming run — and the refusal layer

**Files:**
- Create: `tests/calculus_ledger.py`, `tests/calculus_ledger.json`, `tests/calculus_extent.json`
- Create: `tests/calculus_run.py`, `tests/calculus_layers.py`
- Create: `tests/test_calculus_refusal.py`

**Interfaces:**
- Consumes: `calculus_enum.{tier_a, DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, Bounds}`, `calculus_rules.{IMPLEMENTED, moves, legal, Move}`, `calculus_apply.{apply_move, Outcome}`, `canonical_signature.compute_canonical_signatures`.
- Produces:
  - `calculus_ledger`: `Failure(layer, key, detail)`, `instance_key(tier, gname, g, m, sigs) -> str`, `ledgered(layer) -> set[str]`, `check_ledger(layer, evaluated_ledgered, failures) -> list[str]`, `assert_extent(name, extent: dict) -> None`.
  - `calculus_run`: `SemanticsBudget(sizes, tuple_cap, sample_n, seed, max_elements)`, `Mode(name, bounds, tier_b, tier_b_budget, sem)`, `MODES: dict[str, Mode]`, `Record(tier, gname, g, move, key, outcome, verdict, why)`, `LayerResult(failures, evaluated_ledgered, counts)`, `Run(mode, graphs, moves, skipped, layers)` with `.extent()`, `graphs_for(mode, tier) -> list[tuple[str, G]]`, `run(mode_name) -> Run` (cached).
  - `calculus_layers`: `LAYERS: dict[str, Callable[[Record, dict], tuple[str, Optional[str]]]]`, `refusal`.

A check returns `(label, detail)`: `label` is counted in the layer's extent; `detail` is `None` when the instance passes, else the failure text. A label beginning `not:` means the instance was not evaluated by that layer (so a ledgered instance under it is not checked for shrinking).

- [ ] **Step 1: Create the two JSON files.** `tests/calculus_ledger.json`:

```json
{"entries": []}
```

`tests/calculus_extent.json`:

```json
{}
```

- [ ] **Step 2: Implement** `tests/calculus_ledger.py`:

```python
"""The ledger of known failures and the pinned extents (spec 2026-09-10 §6).

Ledger: every failing instance must belong to an entry (else NEW), and every
evaluated instance in an entry must still fail (else SHRINK) — so the ledger
can only shrink by someone deciding it should. Extent: every count a layer
covered is pinned with ==; CALCULUS_EXTENT_WRITE=1 rewrites the pins, and the
diff is then read and committed deliberately.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Set

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "calculus_ledger.json"
EXTENT = HERE / "calculus_extent.json"


@dataclass(frozen=True)
class Failure:
    layer: str
    key: str
    detail: str


def _sig(g, x, sigs) -> str:
    if x == g.sheet:
        return "SHEET"
    vs, es, cs = sigs
    for table in (vs, es, cs):
        if x in table:
            return repr(table[x])
    return f"?{x}"


def instance_key(tier: str, gname: str, g, m, sigs) -> str:
    """UUID-independent: the move's elements by canonical signature. Truly
    symmetric moves share a key, which is intended — they are one move."""
    parts = (m.rule, sorted(_sig(g, x, sigs) for x in m.selection),
             None if m.target is None else _sig(g, m.target, sigs), m.content,
             sorted((_sig(g, e, sigs), i) for e, i in m.hooks))
    return f"{tier}|{gname}|{m.rule}|{hashlib.sha256(repr(parts).encode()).hexdigest()[:12]}"


def _entries() -> List[dict]:
    entries = json.loads(LEDGER.read_text())["entries"]
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "ledger entry ids must be unique"
    for e in entries:
        assert e.get("reason", "").strip(), f"ledger entry {e['id']!r} has no reason"
        assert set(e) == {"id", "layer", "rule", "reason", "instances"}, f"{e['id']!r}: bad fields"
    return entries


def ledgered(layer: str) -> Set[str]:
    return {k for e in _entries() if e["layer"] == layer for k in e["instances"]}


def check_ledger(layer: str, evaluated_ledgered: Set[str], failures: List[Failure]) -> List[str]:
    entries = [e for e in _entries() if e["layer"] == layer]
    known = {k for e in entries for k in e["instances"]}
    failing = {f.key for f in failures}
    problems = []
    new = [f for f in failures if f.key not in known]
    if new:
        problems.append(f"{len(new)} NEW failure(s) in layer {layer!r} (first 20):\n"
                        + "\n".join(f"  {f.key}  {f.detail}" for f in new[:20]))
        dump = os.environ.get("CALCULUS_LEDGER_DUMP")
        if dump:
            Path(f"{dump}.{layer}.json").write_text(json.dumps([asdict(f) for f in new], indent=1))
    for e in entries:
        stale = sorted(k for k in e["instances"] if k in evaluated_ledgered and k not in failing)
        if stale:
            problems.append(f"entry {e['id']!r}: {len(stale)} instance(s) no longer fail — "
                            f"shrink this entry: {stale[:5]}")
    return problems


def assert_extent(name: str, extent: dict) -> None:
    pins = json.loads(EXTENT.read_text())
    if os.environ.get("CALCULUS_EXTENT_WRITE") == "1":
        pins[name] = extent
        EXTENT.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n")
        return
    assert name in pins, f"no pinned extent for {name!r}: run once with CALCULUS_EXTENT_WRITE=1, read the diff"
    assert pins[name] == extent, f"the extent of {name!r} moved:\n  pinned {pins[name]}\n  now    {extent}"


def draft(dump_file: str) -> None:
    """Group a dumped NEW-failure file into draft entries (reasons left blank —
    _entries() refuses a blank reason, so each must be written, with its Dau page)."""
    groups = defaultdict(list)
    for f in json.loads(Path(dump_file).read_text()):
        rule = f["key"].split("|")[2]
        groups[(f["layer"], rule, f["detail"][:48])].append(f["key"])
    out = [{"id": f"{layer}-{rule}-{i}".lower(), "layer": layer, "rule": rule,
            "reason": "", "instances": sorted(keys), "_sample_detail": d}
           for i, ((layer, rule, d), keys) in enumerate(sorted(groups.items()))]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    draft(sys.argv[1])
```

- [ ] **Step 3: Implement** `tests/calculus_layers.py` (the refusal check only; Tasks 7–8 add theirs):

```python
"""Per-record checks, one per layer (spec 2026-09-10 §5). Each returns
(label, detail): the label is counted; detail is None on a pass."""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

Check = Callable[[object, dict], Tuple[str, Optional[str]]]


def refusal(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.1: engine (applied/refused) against legal (true/false). A crash is
    a defect whatever the rule; a not-judged instance is counted, not scored."""
    out = rec.outcome
    if out.crashed:
        return f"{rec.move.rule}:crash", f"CRASH {out.message[:160]}"
    if rec.verdict is None:
        return f"not:{rec.move.rule}", None
    label = f"{rec.move.rule}:{'applied' if out.applied else 'refused'}/" \
            f"{'legal' if rec.verdict else 'illegal'}"
    if out.applied and not rec.verdict:
        return label, f"SEVERE applied but illegal — legal says: {rec.why}"
    if not out.applied and rec.verdict:
        return label, f"INCOMPLETE refused but legal ({rec.why}); engine: {out.message[:120]}"
    return label, None


LAYERS: Dict[str, Check] = {"refusal": refusal}
```

- [ ] **Step 4: Implement** `tests/calculus_run.py`:

```python
"""One streaming pass per mode: every move applied once, every layer's check
run on it, only failures and counts kept (spec 2026-09-10 §6)."""
from __future__ import annotations

import functools
import itertools
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from calculus_apply import Outcome, apply_move
from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, Bounds, tier_a
from calculus_layers import LAYERS
from calculus_ledger import Failure, instance_key, ledgered
from calculus_rules import IMPLEMENTED, Move, legal, moves
from canonical_signature import compute_canonical_signatures


@dataclass(frozen=True)
class SemanticsBudget:
    sizes: Tuple[int, ...]
    tuple_cap: int
    sample_n: int
    seed: int
    max_elements: int     # larger source graphs are counted, not evaluated


@dataclass(frozen=True)
class Mode:
    name: str
    bounds: Bounds
    tier_b: str           # "none" | "current-units" | "all"
    tier_b_budget: int
    sem: SemanticsBudget


MODES: Dict[str, Mode] = {
    "default": Mode("default", DEFAULT_BOUNDS, "none", 200,
                    SemanticsBudget((1, 2), 6, 64, 20260910, 40)),
    "exhaustive": Mode("exhaustive", EXHAUSTIVE_BOUNDS, "none", 2000,
                       SemanticsBudget((1, 2, 3), 12, 512, 20260910, 80)),
}


@dataclass(frozen=True)
class Record:
    tier: str
    gname: str
    g: object
    move: Move
    key: str
    outcome: Outcome
    verdict: Optional[bool]
    why: str


@dataclass
class LayerResult:
    failures: List[Failure] = field(default_factory=list)
    evaluated_ledgered: Set[str] = field(default_factory=set)
    counts: Counter = field(default_factory=Counter)


@dataclass
class Run:
    mode: Mode
    graphs: Counter = field(default_factory=Counter)
    moves: Counter = field(default_factory=Counter)
    skipped: Counter = field(default_factory=Counter)
    layers: Dict[str, LayerResult] = field(default_factory=dict)

    def extent(self) -> dict:
        return {"graphs": dict(sorted(self.graphs.items())),
                "moves": dict(sorted(self.moves.items())),
                "skipped": dict(sorted(self.skipped.items()))}


def graphs_for(mode: Mode, tier: str):
    if tier == "A":
        return tier_a(mode.bounds).graphs
    raise ValueError(f"tier {tier!r} is wired in Task 10")


def _tiers(mode: Mode):
    return ("A",) if mode.tier_b == "none" else ("A", "B")


@functools.lru_cache(maxsize=None)
def run(mode_name: str) -> Run:
    mode = MODES[mode_name]
    result = Run(mode, layers={name: LayerResult() for name in LAYERS})
    known = {name: ledgered(name) for name in LAYERS}
    for tier in _tiers(mode):
        budget = None if tier == "A" else mode.tier_b_budget
        units_only = tier == "B" and mode.tier_b == "current-units"
        for gname, g in graphs_for(mode, tier):
            result.graphs[tier] += 1
            sigs = compute_canonical_signatures(g)
            cache: dict = {}
            for rule in IMPLEMENTED:
                gen = moves(rule.name, g, tier, units_only=units_only)
                taken = list(gen) if budget is None else list(itertools.islice(gen, budget))
                if budget is not None:
                    result.skipped[f"{tier}:{rule.name}"] += sum(1 for _ in gen)
                for m in taken:
                    result.moves[f"{tier}:{rule.name}"] += 1
                    verdict, why = legal(g, m)
                    rec = Record(tier, gname, g, m, instance_key(tier, gname, g, m, sigs),
                                 apply_move(g, m), verdict, why)
                    for name, check in LAYERS.items():
                        label, detail = check(rec, cache)
                        lr = result.layers[name]
                        lr.counts[f"{tier}:{label}"] += 1
                        if not label.startswith("not:") and rec.key in known[name]:
                            lr.evaluated_ledgered.add(rec.key)
                        if detail is not None:
                            lr.failures.append(Failure(name, rec.key, detail))
    return result
```

- [ ] **Step 5: Write the layer test** — `tests/test_calculus_refusal.py`:

```python
"""Refusal agreement (spec 2026-09-10 §5.1): the engine refuses exactly what
Dau forbids. Known disagreements live in calculus_ledger.json, each with its
reason; a new one fails here, and so does a repaired one."""
import pytest

from calculus_ledger import assert_extent, check_ledger
from calculus_run import run


def _agree(mode):
    lr = run(mode).layers["refusal"]
    problems = check_ledger("refusal", lr.evaluated_ledgered, lr.failures)
    assert not problems, "\n\n".join(problems)


def _extent(mode):
    r = run(mode)
    assert_extent(f"{mode}:run", r.extent())
    assert_extent(f"{mode}:refusal", dict(sorted(r.layers["refusal"].counts.items())))


def test_refusal_agreement():
    _agree("default")


def test_refusal_extent():
    _extent("default")


@pytest.mark.exhaustive
def test_refusal_agreement_exhaustive():
    _agree("exhaustive")


@pytest.mark.exhaustive
def test_refusal_extent_exhaustive():
    _extent("exhaustive")
```

- [ ] **Step 6: First run — expect failures, and read them.** Run:

```bash
CALCULUS_LEDGER_DUMP=/tmp/calc uv run pytest tests/test_calculus_refusal.py -q -k "not extent" 2>&1 | tail -40
```

Expected: either PASS, or `NEW failure(s)`. Known to be likely, from probes made while planning: VERTEX_INS refused-but-legal on positive contexts (HEAVY_DOT is negative-only; Dau p.166 allows any context) and VERTEX_ERA refused-but-legal in negative contexts (no entry point but ERA).

- [ ] **Step 7: Adjudicate every group.** `uv run python tests/calculus_ledger.py /tmp/calc.refusal.json > /tmp/drafts.json`. For each draft group, reproduce one instance by hand (build the graph, call `apply_move` and `legal`) and decide **one** of:
  - **`legal` misreads Dau.** Fix `legal`; add a case to `tests/test_calculus_legal.py` that fails before the fix, citing the page. Re-run.
  - **The engine departs from Dau.** Copy the group into `tests/calculus_ledger.json`, give it a stable `id` (e.g. `heavy-dot-negative-only`), and a `reason` that names the Dau page and what the engine does instead. Delete `_sample_detail`.

  Loop Steps 6–7 until the layer passes. **Every SEVERE group is reported to the user before it is ledgered** — it is a claim the engine performs an unsound-looking move.

- [ ] **Step 8: Pin the extent.** `CALCULUS_EXTENT_WRITE=1 uv run pytest tests/test_calculus_refusal.py -q -k extent`, then `git diff tests/calculus_extent.json` and read it: the counts per rule and cell are the finding. Re-run without the variable: PASS. Record P-K2 in the spec §7: `**Outcome:** HELD` if no tier-A `SEVERE` entry exists in the ledger, else `REFUTED — <entry ids>`.

- [ ] **Step 9: Commit** all six files plus the spec, gate, `--no-verify`. Message: `Calculus suite: refusal agreement — <n> ledger entries, P-K2 <outcome>`, the body listing each ledger entry id and reason.

---

### Task 7: Structure — each rule changes exactly what it licenses

**Files:**
- Create: `tests/calculus_expected.py`
- Modify: `tests/calculus_layers.py` (add `structure`, register it)
- Create: `tests/test_calculus_structure.py`

**Interfaces:**
- Consumes: `calculus_rules.{expand, Move}`, `tarski.dominating_nodes`, `eg_navigation.same_graph`, `calculus_run.{Record, run}`, `calculus_ledger.{Failure, check_ledger, ledgered, assert_extent}`.
- Produces: `calculus_expected.{remove, insert, double_cut, erase_double_cut, add_vertex, iterate, expected(g, m) -> Optional[G], maps_carried(g, h) -> list[str]}`; `calculus_layers.structure`.

The expected result is built from the data model directly — never from a rule module — and compared by `same_graph` (spec §5.2). IT+ is built too (a copy with reused outer lines is twenty lines, not a second engine); only the ligature, split and merge rules are postcondition-only.

- [ ] **Step 1: Write the failing tests** — `tests/test_calculus_structure.py`:

```python
"""Structure (spec 2026-09-10 §5.2): a rule changes what it licenses, and
nothing else; the result is an EGI; the B-min maps travel with it."""
import pytest

import eg_navigation as nav
from calculus_apply import Outcome
from calculus_enum import DEFAULT_BOUNDS, tier_a
from calculus_expected import expected, iterate, maps_carried
from calculus_layers import structure
from calculus_ledger import Failure, assert_extent, check_ledger, ledgered
from calculus_rules import Move
from calculus_run import Record, run
from egif_parser_dau import parse_egif
from tarski import dominating_nodes


def _rec(g, m, result):
    return Record("A", "hand", g, m, "hand|key", Outcome(True, result, ""), True, "")


def test_the_instrument_catches_a_rule_that_does_nothing():
    # The shape of the HEAVY_DOT defect found while planning (a second
    # application reports success and inserts nothing), built by hand so the
    # instrument is tested, not the engine.
    g = parse_egif("~[ (P *x) ]")
    c = next(iter(g.Cut)).id
    label, detail = structure(_rec(g, Move("VERTEX_INS", (), c), g), {})
    assert detail and "licensed change" in detail


def test_the_instrument_catches_a_line_moved_inward():
    g = parse_egif("(P *x) ~[ (Q x) ]")
    bad = parse_egif("~[ (P *x) (Q x) ]")
    p = next(e for e in g.nu if g.rel[e] == "P")
    label, detail = structure(_rec(g, Move("IT+", (p,), next(iter(g.Cut)).id), bad), {})
    assert detail


def test_iterate_reuses_outer_lines():
    g = parse_egif("(P *x) ~[ ]")
    p = next(iter(g.nu))
    h = iterate(g, (p,), next(iter(g.Cut)).id)
    assert nav.same_graph(h, parse_egif("(P *x) ~[ (P x) ]"))


def test_maps_carried_names_what_was_dropped():
    # Stubs, not graphs: the core validates rho against an alphabet, and the
    # point here is only which attribute comparison names which loss.
    from types import SimpleNamespace as NS
    before = NS(alphabet=NS(R={"P"}), rho={"v1": "a"}, sort={}, quotation={},
                V=[NS(id="v1")], Cut=[])
    after = NS(alphabet=None, rho={}, sort={}, quotation={}, V=[NS(id="v1")], Cut=[])
    assert maps_carried(before, after) == ["alphabet dropped", "rho lost for 1 vertex"]
    assert maps_carried(before, before) == []


def _layer(mode):
    lr = run(mode).layers["structure"]
    problems = check_ledger("structure", lr.evaluated_ledgered, lr.failures)
    assert not problems, "\n\n".join(problems)


def test_structure():
    _layer("default")


def test_structure_extent():
    assert_extent("default:structure", dict(sorted(run("default").layers["structure"].counts.items())))


@pytest.mark.exhaustive
def test_structure_exhaustive():
    _layer("exhaustive")


@pytest.mark.exhaustive
def test_structure_extent_exhaustive():
    assert_extent("exhaustive:structure",
                  dict(sorted(run("exhaustive").layers["structure"].counts.items())))


def test_core_dominating_nodes_check_agrees_with_dau():
    """Def 12.5 is part of what an EGI is. The core's has_dominating_nodes was
    found inverted while planning; its disagreements are ledgered here."""
    known = ledgered("core-dominating")
    failures, evaluated = [], set()
    for gname, g in tier_a(DEFAULT_BOUNDS).graphs:
        key = f"A|{gname}|graph"
        if key in known:
            evaluated.add(key)
        if g.has_dominating_nodes() != dominating_nodes(g):
            failures.append(Failure("core-dominating", key,
                                    f"core says {g.has_dominating_nodes()}, Def 12.5 says {dominating_nodes(g)}"))
    problems = check_ledger("core-dominating", evaluated, failures)
    assert not problems, "\n\n".join(problems)
```

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_calculus_structure.py -q` → `No module named 'calculus_expected'`.

- [ ] **Step 3: Implement** `tests/calculus_expected.py`:

```python
"""What each rule should produce, built from the data model directly
(spec 2026-09-10 §5.2). No rule module is imported."""
from __future__ import annotations

from typing import List, Optional

from frozendict import frozendict

from calculus_rules import Move, expand
from egi_core_dau import Cut as CutEl
from egi_core_dau import Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif

G = RelationalGraphWithCuts


def _g(g, *, V, E, nu, Cut, area, rel) -> G:
    return G(V=frozenset(V), E=frozenset(E), nu=frozendict(nu), sheet=g.sheet,
             Cut=frozenset(Cut), area=frozendict({k: frozenset(v) for k, v in area.items()}),
             rel=frozendict(rel))


def remove(g: G, X) -> G:
    X = set(X)
    return _g(g, V=[v for v in g.V if v.id not in X], E=[e for e in g.E if e.id not in X],
              nu={e: s for e, s in g.nu.items() if e not in X},
              Cut=[c for c in g.Cut if c.id not in X],
              area={k: set(v) - X for k, v in g.area.items() if k not in X},
              rel={e: r for e, r in g.rel.items() if e not in X})


def insert(g: G, target: str, text: str) -> G:
    h = parse_egif(text)
    p = "ins:{}".format
    area = {k: set(v) for k, v in g.area.items()}
    area.setdefault(target, set()).update(p(x) for x in h.area.get(h.sheet, ()))
    for c in h.Cut:
        area[p(c.id)] = {p(x) for x in h.area.get(c.id, ())}
    return _g(g, V=[*g.V, *(Vertex(p(v.id), label=v.label, is_generic=v.is_generic) for v in h.V)],
              E=[*g.E, *(Edge(p(e.id)) for e in h.E)],
              nu={**g.nu, **{p(e): tuple(p(v) for v in s) for e, s in h.nu.items()}},
              Cut=[*g.Cut, *(CutEl(p(c.id)) for c in h.Cut)], area=area,
              rel={**g.rel, **{p(e): r for e, r in h.rel.items()}})


def double_cut(g: G, S, target: str) -> G:
    S = set(S)
    area = {k: set(v) for k, v in g.area.items()}
    area[target] = (area.get(target, set()) - S) | {"dc:outer"}
    area["dc:outer"], area["dc:inner"] = {"dc:inner"}, S
    return _g(g, V=g.V, E=g.E, nu=g.nu, Cut=[*g.Cut, CutEl("dc:outer"), CutEl("dc:inner")],
              area=area, rel=g.rel)


def erase_double_cut(g: G, c1: str) -> G:
    (c2,) = g.area[c1]
    c0 = g.get_context(c1)
    area = {k: set(v) for k, v in g.area.items() if k not in (c1, c2)}
    area[c0] = (area[c0] - {c1}) | set(g.area.get(c2, ()))
    return _g(g, V=g.V, E=g.E, nu=g.nu, Cut=[c for c in g.Cut if c.id not in (c1, c2)],
              area=area, rel=g.rel)


def add_vertex(g: G, target: str) -> G:
    area = {k: set(v) for k, v in g.area.items()}
    area.setdefault(target, set()).add("hd:new")
    return _g(g, V=[*g.V, Vertex("hd:new")], E=g.E, nu=g.nu, Cut=g.Cut, area=area, rel=g.rel)


def iterate(g: G, S, target: str) -> G:
    """Copy expand(S) into target; a vertex outside the copy is reused."""
    X = expand(g, S)
    p = "it:{}".format
    vmap = {v.id: v for v in g.V}
    cuts = {c.id for c in g.Cut}
    area = {k: set(v) for k, v in g.area.items()}
    for x in X:
        if x in cuts:
            area.setdefault(p(x), set())
    for x in X:
        parent = g.get_context(x)
        area.setdefault(target if parent not in X else p(parent), set()).add(p(x))
    return _g(g, V=[*g.V, *(Vertex(p(x), label=vmap[x].label, is_generic=vmap[x].is_generic)
                         for x in X if x in vmap)],
              E=[*g.E, *(Edge(p(x)) for x in X if x in g.nu)],
              nu={**g.nu, **{p(x): tuple(p(v) if v in X else v for v in g.nu[x])
                             for x in X if x in g.nu}},
              Cut=[*g.Cut, *(CutEl(p(x)) for x in X if x in cuts)], area=area,
              rel={**g.rel, **{p(x): g.rel[x] for x in X if x in g.nu}})


def expected(g: G, m: Move) -> Optional[G]:
    """The licensed result, or None where only postconditions are checked."""
    if m.rule in ("ERA", "VERTEX_ERA", "IT-"):
        return remove(g, expand(g, m.selection))
    if m.rule == "INS":
        return insert(g, m.target, m.content)
    if m.rule == "DC+":
        return double_cut(g, m.selection, m.target)
    if m.rule == "DC-":
        return erase_double_cut(g, m.selection[0])
    if m.rule == "VERTEX_INS":
        return add_vertex(g, m.target)
    if m.rule == "IT+":
        return iterate(g, m.selection, m.target)
    return None


def maps_carried(g: G, h: G) -> List[str]:
    """The B-min maps must survive the step for every element that survives."""
    out = []
    if g.alphabet is not None:
        if h.alphabet is None:
            out.append("alphabet dropped")
        elif not set(g.alphabet.R) <= set(h.alphabet.R):
            out.append("alphabet lost relation names")
    hv, hc = {v.id for v in h.V}, {c.id for c in h.Cut}
    rho = [v for v, c in g.rho.items() if c is not None and v in hv and h.rho.get(v) != c]
    if rho:
        out.append(f"rho lost for {len(rho)} vertex" + ("es" if len(rho) > 1 else ""))
    if [v for v, s in g.sort.items() if v in hv and h.sort.get(v) != s]:
        out.append("sort lost")
    if [c for c, q in g.quotation.items() if c in hc and h.quotation.get(c) != q]:
        out.append("quotation lost")
    return out
```

- [ ] **Step 4: Add the check** — in `tests/calculus_layers.py`, add the imports and function, and register it:

```python
import eg_navigation as nav
from calculus_expected import expected, maps_carried
from tarski import dominating_nodes


def structure(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.2: the result is an EGI, keeps the B-min maps, and — where the
    licensed result can be built — equals it. Only applied moves are checked;
    an applied-but-illegal move is checked for EGI-hood and maps only."""
    out = rec.outcome
    if not out.applied:
        return f"not:{rec.move.rule}:refused", None
    g, h, m = rec.g, out.result, rec.move
    problems = []
    if dominating_nodes(g) and not dominating_nodes(h):
        problems.append("the result is not an EGI (Def 12.5)")
    problems += maps_carried(g, h)
    exp = expected(g, m) if rec.verdict else None
    if exp is not None and not nav.same_graph(exp, h):
        problems.append("the result differs from the licensed change")
    kind = "exact" if exp is not None else ("postcondition" if rec.verdict is None else "illegal")
    return f"{m.rule}:{kind}", "; ".join(problems) or None


LAYERS["structure"] = structure
```

(Place `LAYERS["structure"] = structure` after the `LAYERS = {...}` line.)

- [ ] **Step 5: Run the hand tests.** `uv run pytest tests/test_calculus_structure.py -q -k "instrument or iterate or maps_carried"`. Expected: PASS (4).

- [ ] **Step 6: Run the layer, adjudicate, pin.** As Task 6 Steps 6–8, with `tests/test_calculus_structure.py` and dumps `/tmp/calc.structure.json` / `/tmp/calc.core-dominating.json`. Expected from planning probes: `core-dominating` fails on every tier-A graph with a line reaching into a cut (the inverted helper) — ledger it as one entry `core-has-dominating-nodes-inverted`, reason citing Def 12.5 p.125 and the probe. A structural failure is ledgered only after reproducing it by hand and naming what the engine did (e.g. `_apply_vertex_split rebuilds without rho` — `derived_rules.py` already says so in a comment).

- [ ] **Step 7: Re-run refusal too** (the shared run now has two layers; its counts must not move): `uv run pytest tests/test_calculus_refusal.py -q`. Expected: PASS with unchanged extent.

- [ ] **Step 8: Commit** (`calculus_expected.py calculus_layers.py test_calculus_structure.py calculus_ledger.json calculus_extent.json`), gate, `--no-verify`, message `Calculus suite: structure — <n> ledger entries`, body listing them.

---

### Task 8: Soundness, strict — one-way where Dau says so, equivalence everywhere else

**Files:**
- Modify: `tests/calculus_layers.py` (add `soundness`, register it)
- Modify: `tests/calculus_run.py` (hand the mode's semantics budget to the checks)
- Create: `tests/test_calculus_soundness.py`
- Modify: spec §7 (record P-K3)

**Interfaces:**
- Consumes: `tarski.{vocabulary, universe, model_set, satisfies, dominating_nodes}`, `calculus_rules.RULES`, `calculus_run.SemanticsBudget`.
- Produces: `calculus_layers.soundness(rec, cache)`; the per-graph `cache` now carries `cache["_sem"]: SemanticsBudget`.

For each applied move G→G′ and each domain size: **one-way** (ERA, INS) requires every model of G to model G′; **equivalence** (every other rule, per the table) requires the model sets to be equal. One separating structure is decisive; none found proves nothing beyond the extent, which says whether each pair was exhaustive or sampled (spec §5.3).

- [ ] **Step 1: Write the failing tests** — `tests/test_calculus_soundness.py`:

```python
"""Soundness, strict (spec 2026-09-10 §5.3). The instrument is shown to bite
on hand-built wrong results before its silence on the engine means anything."""
import pytest

from calculus_apply import Outcome
from calculus_layers import soundness
from calculus_ledger import assert_extent, check_ledger
from calculus_rules import Move
from calculus_run import MODES, Record, run
from egif_parser_dau import parse_egif


def _check(rule, g_text, h_text):
    g, h = parse_egif(g_text), parse_egif(h_text)
    rec = Record("A", "hand", g, Move(rule, ()), "hand|key", Outcome(True, h, ""), True, "")
    return soundness(rec, {"_sem": MODES["default"].sem})


def test_the_instrument_catches_an_unsound_erasure():
    # erasing inside a negative context: ~[ (P x) ] -> ~[ ], always false
    label, detail = _check("ERA", "~[ (P *x) ]", "~[ ]")
    assert detail and detail.startswith("UNSOUND")


def test_the_instrument_catches_a_lost_equivalence():
    # sound as an erasure, but DC+ claims an equivalence
    label, detail = _check("DC+", "(P *x) (Q *y)", "(P *x)")
    assert detail and detail.startswith("NOT AN EQUIVALENCE")


def test_the_instrument_passes_a_true_equivalence():
    assert _check("DC+", "(P *x)", "~[ ~[ (P *x) ] ]")[1] is None


def _layer(mode):
    lr = run(mode).layers["soundness"]
    problems = check_ledger("soundness", lr.evaluated_ledgered, lr.failures)
    assert not problems, "\n\n".join(problems)


def test_soundness():
    _layer("default")


def test_soundness_extent():
    assert_extent("default:soundness", dict(sorted(run("default").layers["soundness"].counts.items())))


@pytest.mark.exhaustive
def test_soundness_exhaustive():
    _layer("exhaustive")


@pytest.mark.exhaustive
def test_soundness_extent_exhaustive():
    assert_extent("exhaustive:soundness",
                  dict(sorted(run("exhaustive").layers["soundness"].counts.items())))
```

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_calculus_soundness.py -q` → `ImportError: cannot import name 'soundness'`.

- [ ] **Step 3: Hand the budget to the checks.** In `tests/calculus_run.py`, replace `cache: dict = {}` with `cache: dict = {"_sem": mode.sem}`.

- [ ] **Step 4: Implement** — append to `tests/calculus_layers.py`:

```python
from calculus_rules import RULES
from tarski import model_set, universe, vocabulary


def _first(bits: int) -> int:
    return (bits & -bits).bit_length() - 1


def soundness(rec, cache) -> Tuple[str, Optional[str]]:
    """§5.3: Dau's direction for the rule, checked over finite structures.
    The source's model sets are cached per graph (the cache is reset per
    source graph by the run)."""
    out, m, g = rec.outcome, rec.move, rec.g
    if not out.applied:
        return f"not:{m.rule}:refused", None
    sem = cache["_sem"]
    h = out.result
    if len(g.V) + len(g.E) + len(g.Cut) > sem.max_elements:
        return f"not:{m.rule}:too-large", None
    if not (dominating_nodes(g) and dominating_nodes(h)):
        return f"not:{m.rule}:not-an-EGI", None
    direction = RULES[m.rule].direction
    rels, consts = vocabulary(g, h)
    exhaustive = True
    for n in sem.sizes:
        us, exh = universe(rels, consts, n, cap=sem.tuple_cap, sample_n=sem.sample_n, seed=sem.seed)
        exhaustive &= exh
        k = ("models", rels, consts, n)
        if k not in cache:
            cache[k] = model_set(g, us)
        mg, mh = cache[k], model_set(h, us)
        if mg & ~mh:
            return f"{m.rule}:failed", f"UNSOUND at size {n}: a model of G is not a model of G' — {us[_first(mg & ~mh)]}"
        if direction == "equivalence" and mh & ~mg:
            return f"{m.rule}:failed", f"NOT AN EQUIVALENCE at size {n}: a model of G' is not a model of G — {us[_first(mh & ~mg)]}"
    return f"{m.rule}:{'exhaustive' if exhaustive else 'sampled'}", None


LAYERS["soundness"] = soundness
```

Note the cache key does not include the source: the run creates a fresh `cache` per source graph, so a key is only ever reused for the same G.

- [ ] **Step 5: Run the instrument tests.** `uv run pytest tests/test_calculus_soundness.py -q -k instrument`. Expected: PASS (3).

- [ ] **Step 6: Time the default slice.** `time uv run pytest tests/test_calculus_soundness.py -q -k "soundness and not extent"`. If the whole default run (all layers) exceeds 2 minutes, lower `MODES["default"].sem.sample_n` or `.sizes` — never the tier-A bounds, which Task 1 fixed — and record the change and its reason in the commit message.

- [ ] **Step 7: Adjudicate and pin** as Task 6 Steps 6–8 (dump `/tmp/calc.soundness.json`). **A soundness failure on a legal move is the most serious finding this suite can make: report every one to the user, with the separating structure, before ledgering it.** A failure on an applied-but-illegal move is expected to accompany a refusal-layer SEVERE entry; ledger it with a reason pointing at that entry. Record P-K3 in the spec §7: `HELD` if no tier-A failure on ERA/INS/IT+, else `REFUTED — <entry ids>`.

- [ ] **Step 8: Re-run the earlier layers** (`tests/test_calculus_refusal.py tests/test_calculus_structure.py`): PASS, extents unchanged.

- [ ] **Step 9: Commit** (`calculus_layers.py calculus_run.py test_calculus_soundness.py calculus_ledger.json calculus_extent.json` + spec), gate, `--no-verify`, message `Calculus suite: strict soundness — P-K3 <outcome>`.

---

### Task 9: Differential — `semantic_game` against `tarski`

**Files:**
- Create: `tests/test_calculus_differential.py`
- Modify: spec §7 (record P-K4)

**Interfaces:**
- Consumes: `tarski.{Structure, satisfies, universe, vocabulary}`, `calculus_run.MODES`, `calculus_enum.tier_a`, `calculus_ledger.{Failure, check_ledger, ledgered, assert_extent}`, `domain_oracle.CorpusOracle`, `semantic_game.{evaluate, Verdict3}`.
- Produces: nothing downstream.

Where `semantic_game`'s assumptions hold — unique names, closed world — its verdict on each tier-A graph must equal `tarski`'s on the same structure. The structure is encoded as a facts graph: one constant vertex per individual (named individuals by their name, the rest `u<i>`), one sheet edge per tuple, and the diagonal `(= u u)` for every individual, because `semantic_game` does not treat `=` as equality (spec §1a.5). Three counted columns; UNKNOWN is `semantic_game`'s ceiling and never scores as agreement.

- [ ] **Step 1: Write the test** — `tests/test_calculus_differential.py`:

```python
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
```

- [ ] **Step 2: Run the encoding test.** `uv run pytest tests/test_calculus_differential.py -q -k encoding`. Expected: PASS. If it fails, the encoding — not `semantic_game` — is wrong until shown otherwise: print `evaluate(...).transcript` and fix `facts_graph`.

- [ ] **Step 3: Run, adjudicate, pin** as Task 6 Steps 6–8 (dump `/tmp/calc.differential.json`). For each disagreement group, decide by hand, from Dau Def 13.4, which evaluator is right; if `tarski` is, the entry's reason names what `semantic_game` does instead; if `semantic_game` is, fix `tarski` and add a case to `tests/test_tarski.py`. Record P-K4 in the spec §7: `HELD` if no disagreement was ledgered, else `REFUTED — <entry ids>`, and state the UNKNOWN count beside it.

- [ ] **Step 4: Commit** (`test_calculus_differential.py calculus_ledger.json calculus_extent.json` + spec), gate, `--no-verify`, message `Calculus suite: semantic_game against Dau's semantics — P-K4 <outcome>`.

---

### Task 10: Tier B — the corpus as used — and the exhaustive run

**Files:**
- Modify: `tests/calculus_enum.py` (add `tier_b`)
- Modify: `tests/calculus_run.py` (wire tier B; set both modes' `tier_b`)
- Modify: `tests/test_calculus_enum.py`
- Modify: `tests/calculus_extent.json`, `tests/calculus_ledger.json` (re-pinned / adjudicated)

**Interfaces:**
- Consumes: `tomos_service.TomosService.{list_uods, load_uod, load_chain}`, `calculus_enum.dedupe`.
- Produces: `TierBReport(sources, duplicates, key_only, graphs)` with `.extent()`, `tier_b(include_chains: bool) -> TierBReport` (cached); `graphs_for(mode, "B")`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_calculus_enum.py`:

```python
def test_tier_b_covers_every_uod_and_every_chain_state():
    from calculus_enum import TOMOS, tier_b
    from calculus_ledger import assert_extent
    from tomos_service import TomosService
    svc = TomosService(TOMOS)
    uods = [u["uod_id"] for u in svc.list_uods()]
    states = sum(len(c.states) for c in map(svc.load_chain, uods) if c)
    r = tier_b(include_chains=True)
    assert r.sources == len(uods) + states
    assert r.sources == r.duplicates + len(r.graphs)
    assert tier_b(include_chains=False).sources == len(uods)
    assert_extent("tier_b", r.extent())
```

- [ ] **Step 2: Implement** — append to `tests/calculus_enum.py`:

```python
@dataclass
class TierBReport:
    sources: int = 0
    duplicates: int = 0
    key_only: int = 0
    graphs: List[Tuple[str, G]] = field(default_factory=list)

    def extent(self) -> Dict[str, int]:
        return {"sources": self.sources, "duplicates": self.duplicates,
                "duplicates_by_key_only": self.key_only, "kept": len(self.graphs)}


@functools.lru_cache(maxsize=None)
def tier_b(include_chains: bool = True) -> TierBReport:
    """Every corpus UoD's current graph, and every state of every saved chain."""
    from tomos_service import TomosService
    svc = TomosService(TOMOS)
    named: List[Tuple[str, G]] = []
    for entry in svc.list_uods():
        uid = entry["uod_id"]
        named.append((f"{uid}:current", svc.load_uod(uid, attest=False).current_egi))
        chain = svc.load_chain(uid) if include_chains else None
        if chain:
            named += [(f"{uid}:{sid}", g) for sid, g in sorted(chain.states.items())]
    report = TierBReport(sources=len(named))
    report.graphs, report.duplicates, report.key_only = dedupe(named)
    return report
```

- [ ] **Step 3: Run.** `CALCULUS_EXTENT_WRITE=1 uv run pytest tests/test_calculus_enum.py -q -k tier_b`, read the `tier_b` diff in `tests/calculus_extent.json` (expect sources = 52 + the chain-state count; 178 state files were on disk when planning), then re-run without the variable: PASS.

- [ ] **Step 4: Wire tier B.** In `tests/calculus_run.py`, replace the body of `graphs_for`:

```python
def graphs_for(mode: Mode, tier: str):
    if tier == "A":
        return tier_a(mode.bounds).graphs
    return tier_b(include_chains=(mode.tier_b == "all")).graphs
```

add `tier_b` to the `calculus_enum` import, and set `tier_b="current-units"` in `MODES["default"]` and `tier_b="all"` in `MODES["exhaustive"]`.

- [ ] **Step 5: Run the default layers.** `CALCULUS_LEDGER_DUMP=/tmp/calcB uv run pytest tests/test_calculus_refusal.py tests/test_calculus_structure.py tests/test_calculus_soundness.py -q -k "not extent"`. Adjudicate new tier-B failures as in Task 6 Step 7 (tier-B keys begin `B|<uod>:<state>|`). Expected from planning: quotation-bearing UoDs count under `not:` in refusal; `bfo_core`'s refused single-edge erasures (31 of 52 in a planning probe) now get a verdict — read them before ledgering, since P1 showed a same-area single-edge ERA *is* applied.

- [ ] **Step 6: Time and pin the default slice.** `time uv run pytest tests/test_calculus_*.py -q`. Target ≤ 2 minutes for the calculus files together. If over, lower `MODES["default"].tier_b_budget` (not the bounds) and say so in the commit. Then `CALCULUS_EXTENT_WRITE=1 uv run pytest tests/test_calculus_*.py -q -k extent`, read the diff, re-run: PASS.

- [ ] **Step 7: The exhaustive run.** In the background (it may take hours; use `run_in_background`):

```bash
time CALCULUS_LEDGER_DUMP=/tmp/calcX uv run pytest tests/test_calculus_*.py -m exhaustive -q > /tmp/calc_exhaustive.log 2>&1
```

Adjudicate any new failures exactly as before; pin with `CALCULUS_EXTENT_WRITE=1 ... -m exhaustive -k extent`; re-run the exhaustive extents to confirm. **Decision rule:** if the wall time exceeds 3 hours, lower `MODES["exhaustive"].tier_b_budget` or `.sem.sample_n` (in that order) until it does not, and record the measured time and the change in the commit. The exhaustive mode's wall time goes in the commit message whatever it is.

- [ ] **Step 8: Commit** (`calculus_enum.py calculus_run.py test_calculus_enum.py calculus_extent.json calculus_ledger.json`), gate, `--no-verify`, message `Calculus suite: tier B (<kept> corpus graphs) and the exhaustive run (<wall time>)`, body listing any new ledger entries.

---

### Task 11: The agreed side items

Four independent items, one commit each. None touches a protected module.

**Files:**
- Modify: `src/drawing_validity.py` (before `return ValidityReport(issues=issues)`, line ~327), `tests/test_drawing_validity.py`
- Delete: `tests/test_it_minus_dau_compliance.py` (0 bytes; its coverage lives in `test_it_minus_with_isomorphism.py`)
- Modify: `src/egif_parser_dau.py` (`EGIFParser.parse` and `_finalize_alphabet_and_rho`), create `tests/test_egif_alphabet.py`
- Modify: `tests/test_tomos_parsing.py` (`test_the_round_trip_guarantee_is_stated_at_its_true_extent`)

**11a — a warning for one individual at two spots.**

- [ ] **Step 1: Failing tests** — append to `tests/test_drawing_validity.py`:

```python
def test_one_individual_at_two_spots_warns():
    # A name denotes one individual, so two spots bearing it are one line of
    # identity (constant-normal-form ruling, 2026-09-09). Warned, never merged:
    # §3.3 checks injectivity against the very drawing the EGI is read from.
    dto = _free_dto({"v1": Point(-50, 0), "v2": Point(50, 0)}, {}, {}, [])
    report = validate_drawing(dto, vertex_labels={"v1": "a", "v2": "a"})
    assert "one_individual_two_spots" in _codes(report, "warning")
    assert report.is_well_formed


def test_distinct_names_and_generic_spots_do_not_warn():
    dto = _free_dto({"v1": Point(-50, 0), "v2": Point(50, 0)}, {}, {}, [])
    assert "one_individual_two_spots" not in _codes(
        validate_drawing(dto, vertex_labels={"v1": "a", "v2": "b"}))
    assert "one_individual_two_spots" not in _codes(validate_drawing(dto))
```

- [ ] **Step 2:** `uv run pytest tests/test_drawing_validity.py -q -k spots` → FAIL (code absent).
- [ ] **Step 3: Implement** — in `validate_drawing`, immediately before `return ValidityReport(issues=issues)` (ensure `Dict` and `List` are imported from `typing`):

```python
    # -- WARNING: one individual named at two spots --------------------------- #
    # A name denotes one individual, so two spots bearing it are one line of
    # identity (the constant-normal-form ruling, 2026-09-09). Warned, never
    # merged: §3.3 checks injectivity against this very drawing.
    spots_by_name: Dict[str, List[str]] = {}
    for vid, label in sorted((vertex_labels or {}).items()):
        if label is not None and vid in dto.vertex_positions:
            spots_by_name.setdefault(label, []).append(vid)
    for name, vids in sorted(spots_by_name.items()):
        if len(vids) > 1:
            issues.append(ValidityIssue(
                code="one_individual_two_spots",
                severity="warning",
                message=(f'"{name}" is written at {len(vids)} spots. A name denotes one '
                         "individual, so these are one line of identity: connect them "
                         "with a line, or keep a single spot."),
                elements=tuple(vids),
            ))
```

- [ ] **Step 4:** `uv run pytest tests/test_drawing_validity.py tests/test_ergasterion_freeform.py -q` → PASS. Add the code to the warnings list in `CLAUDE.md`'s `drawing_validity.py` entry (`warnings boundary_band / unwired_predicate / label_overlap / one_individual_two_spots`).
- [ ] **Step 5: Commit** (`src/drawing_validity.py tests/test_drawing_validity.py CLAUDE.md`), gate, `--no-verify`: `A name written at two spots is flagged, not merged`.

**11b — delete the empty test file.**

- [ ] **Step 6:** `test ! -s tests/test_it_minus_dau_compliance.py && git rm tests/test_it_minus_dau_compliance.py` (the `test ! -s` refuses if the file has since gained content). Commit, gate, `--no-verify`: `Remove a zero-byte test file that collected nothing`.

**11c — EGIF-parsed graphs get their alphabet and ρ.**

- [ ] **Step 7: Failing tests** — `tests/test_egif_alphabet.py`:

```python
"""EGIF's _finalize_alphabet_and_rho was defined and never called, so EGIF-
parsed graphs carried no alphabet while CGIF/CLIF-parsed ones did."""
import pytest

from cgif_generator_dau import generate_cgif
from cgif_parser_dau import parse_cgif
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from test_tomos_parsing import SECOND_ORDER, TOMOS, _uods
from tomos_service import TomosService


def test_egif_parsed_graphs_carry_an_alphabet_and_rho():
    g = parse_egif('(P "a") ~[ (R "a" *x) ]')
    assert g.alphabet is not None
    assert {"P", "R"} <= set(g.alphabet.R) and set(g.alphabet.C) == {"a"}
    assert sorted(c for c in g.rho.values() if c) == ["a"]
    assert g.variable_names, "finalizing must keep what parse() already set"


@pytest.mark.parametrize("uod_id", [u for u in _uods() if u not in SECOND_ORDER])
def test_egif_and_cgif_agree_on_the_alphabet(uod_id):
    g = TomosService(TOMOS).load_uod(uod_id, attest=False).current_egi
    a = parse_egif(generate_egif(g)).alphabet
    b = parse_cgif(generate_cgif(g)).alphabet
    assert (set(a.C), set(a.R), dict(a.ar)) == (set(b.C), set(b.R), dict(b.ar))
```

- [ ] **Step 8:** `uv run pytest tests/test_egif_alphabet.py -q` → FAIL (`alphabet is None`).
- [ ] **Step 9: Implement** in `src/egif_parser_dau.py`: change the end of `_finalize_alphabet_and_rho` from constructing a new `RelationalGraphWithCuts(...)` (which would drop `variable_names`, `sort`, `quotation`) to

```python
        return replace(graph, alphabet=alphabet, rho=frozendict(rho_map))
```

and in `EGIFParser.parse`, replace

```python
        final_graph = replace(self.graph, variable_names=frozendict(self.all_variable_names))
        return final_graph
```

with

```python
        final_graph = replace(self.graph, variable_names=frozendict(self.all_variable_names))
        return self._finalize_alphabet_and_rho(final_graph)
```

- [ ] **Step 10:** Run the EGIF-dependent suites — with an alphabet present the core's `_validate_alphabet_and_rho` now runs on every EGIF parse, so this is where a hidden conflict would surface:

```bash
uv run pytest tests/test_egif_alphabet.py tests/test_tomos_parsing.py tests/test_properties_round_trip.py \
  tests/test_properties_rule_reversibility.py tests/test_rule_interaction.py tests/test_rules_second_order.py \
  tests/test_beta_proof_exercises.py tests/test_world_scroll.py tests/test_ergasterion_routes.py \
  tests/test_corpus_polarity_discipline.py -q
```

Expected: PASS. **If anything else fails, stop and report it to the user** with the failing test and the validation message — do not loosen the validation or skip the test. The finding would be that some path builds EGIF graphs whose vocabulary disagrees with their alphabet.
- [ ] **Step 11: Commit** (`src/egif_parser_dau.py tests/test_egif_alphabet.py`), gate, `--no-verify`: `EGIF-parsed graphs get the alphabet the other two parsers already gave theirs`.

**11d — the round-trip extent, pinned exactly.**

- [ ] **Step 12:** In `tests/test_tomos_parsing.py`, in `test_the_round_trip_guarantee_is_stated_at_its_true_extent`, replace the `assert holding >= 90, (...)` statement and the two trailing comment lines (the xfail they describe no longer exists) with:

```python
    # Pinned exactly, never floored: a floor of 90 against a measured 141 let
    # 51 regressions land unseen. A moved count is read, then re-pinned.
    assert (total, second_order, broken, holding) == (156, 9, 6, 141), (
        f"the round-trip extent moved: {total} checks, {second_order} refused as "
        f"second-order, {broken} known broken, {holding} holding — update this pin "
        f"and the module docstring deliberately"
    )
```

- [ ] **Step 13:** `uv run pytest tests/test_tomos_parsing.py -q` → PASS. (If `total` is not 156 the corpus has grown since planning: re-read the numbers, confirm each by hand, then pin them.) Commit, gate, `--no-verify`: `The round-trip guarantee is pinned at its measured extent, not above a floor`.

---

### Task 12: Record what was found, and verify the whole

**Files:**
- Modify: `CURRENT_PLAN.md` (new top block), `CLAUDE.md` (Testing section), the spec (status line)
- Modify: the memory file `project_linear_form_round_trip_arc.md` (or a new `project_calculus_property_suite.md` linked from it and from `MEMORY.md`)

Every figure written here is read from `tests/calculus_extent.json`, `tests/calculus_ledger.json`, the spec's recorded prior outcomes, and the full-suite output — never from memory or from this plan's expectations (standing rule 4: a narrated number is generated or asserted).

- [ ] **Step 1: The full suite**, in the background (~40 minutes):

```bash
uv run pytest tests/ -q > /tmp/full_suite.log 2>&1; tail -5 /tmp/full_suite.log
```

Expected: 0 failed. A failure outside the calculus files is investigated (systematic-debugging) before anything is written about this arc. Then `uv run python tools/quality_gate_system.py`.

- [ ] **Step 2: `CURRENT_PLAN.md`.** Add a new block at the top, dated, above the sixteenth arc's: what was built (the four layers, both tiers, counts from the extent file), the four priors' outcomes as recorded in the spec §7, every ledger entry by id with its one-line reason, the core defects found while planning and confirmed by the suite (`has_dominating_nodes` inverted; HEAVY_DOT negative-only with a fixed id; any others the layers ledgered), and the next task. State plainly which of these are protected-core changes awaiting the author's authorization. Keep the `▶▶▶ NEXT SESSION` marker on the new block.

- [ ] **Step 3: `CLAUDE.md`.** In the Testing section, add one entry per new test file (`test_calculus_enum`, `test_tarski`, `test_calculus_pk1`, `test_calculus_rules`, `test_calculus_legal`, `test_calculus_refusal`, `test_calculus_structure`, `test_calculus_soundness`, `test_calculus_differential`, `test_egif_alphabet`) in the house style — what each proves, and that `-m exhaustive` runs the full extent. Update the test-count line from Step 1's output.

- [ ] **Step 4: The spec.** Change its status line to `**Status:** built <date>; priors recorded in §7.`

- [ ] **Step 5: Memory.** Record the arc's non-obvious findings (not what the repo already says): which ledger entries exist and why they matter, the priors' outcomes, and that Dau's book is in `docs/references/` and was transcribed for §1a. Add the pointer line to `MEMORY.md`.

- [ ] **Step 6: The knowledge graph.** `graphify update .`

- [ ] **Step 7: Commit** (`CURRENT_PLAN.md CLAUDE.md` + the spec), gate, `--no-verify`: `The calculus, tested directly: what the suite found`, the body summarising the ledger and priors. Then offer the author a push of `tier0-readiness` (local is primary; GitHub is the backup).

---

## Self-review notes (for the executor)

- The ledger begins empty and fills only by adjudication; an entry with no reason cannot load. Expect the first runs of Tasks 6–10 to fail — that is the suite working.
- `legal()` is a reading of Dau, and its docstrings say where it reads Dau through Arisbe's shared-vertex form. When the engine and `legal` disagree, neither is presumed right: reproduce, open the cited page, decide.
- Two known defects were found while planning and are **expected** to surface: the inverted `has_dominating_nodes` (Task 7, `core-dominating`) and HEAVY_DOT's negative-only precondition (Task 6, refusal). HEAVY_DOT's fixed-id collision cannot arise from tier-A ids; the instrument that would catch it is tested on a hand-built outcome instead.
- Nothing here changes a protected module. A fix to a ledgered engine defect is a separate, authorized change, and the ledger entry it retires fails with "shrink this entry" to say so.

