# Calculus Fix Arc Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Arisbe's calculus engine stay inside what Dau states — fixing every unsound or non-Dau move the property suite found — with each fix proved by its ledger entry shrinking.

**Architecture:** The instrument comes first (four tasks, `tests/` only), so each engine fix afterwards is judged by a suite that can tell a real repair from a partial one. Then six engine fixes, one per commit, at the engine choke points. The seventh step (the alphabet question) is a decision sitting with the author, not built here.

**Tech Stack:** Python 3.12, pytest, `uv`. No new dependencies.

**Spec:** [docs/superpowers/specs/2026-09-12-calculus-fix-arc-design.md](../specs/2026-09-12-calculus-fix-arc-design.md) — read §2 (the author's four decisions) and §5 (the verification discipline) before starting.

## Global Constraints

- **Dau is the authority.** `docs/references/mathematical_logic_with_diagrams.pdf`, PDF page = book page + 10. Every rule-level claim cites a definition and page. The author's standing rule: *"we MUST remain Dau-compliant, testing in a manner that ensures this, and vigilant for examples that stress our implementation."*
- **A fix is proved, not asserted.** A step is done when its ledger entries have been **removed from `tests/calculus_ledger.json`** (not edited) and the extents re-pinned, with the diff read. If a fix does not move its entry, the fix is wrong or the entry was mis-adjudicated — investigate; never delete an entry to make a suite green.
- **Never loosen an assertion.** Not a threshold, not a pin, not a test. If the suite's own `legal()` now disagrees the other way, that is a finding to report, not a licence to adjust `legal()`.
- **Protected modules** (`uv run python tools/core_protection_system.py --report` lists all 14). This arc edits four: `formal_transformation_rules.py`, `ligature_manipulation_rules.py`, `egi_core_dau.py`, and possibly `rule_interaction.py`. `.core_modification_authorized` must exist (gitignored; `touch .core_modification_authorized`). **Each protected edit is confirmed with the author immediately before it is made** — the task says where to stop and ask. `vertex_splitting_merging_rules.py`, `vertex_scope.py` and `derived_rules.py` are **not** protected.
- **Test modules** import `src` and `tests` modules by bare name; `pyproject.toml` puts both on `pythonpath`.
- **Extent pins** are exact. Re-pin with `CALCULUS_EXTENT_WRITE=1 uv run pytest <file> -q -k extent`, then read `git diff tests/calculus_extent.json` before committing. A count that moves for a reason you cannot state is a finding.
- **Do not run `-m exhaustive`** except where a task says so: it takes about 2 h 41 min. The default calculus suite is ~75 s: `uv run pytest tests/test_calculus_*.py tests/tarski.py -q` (tarski has no tests; use `tests/test_tarski.py`).
- **Committing:** the pre-commit hook fails on a missing `python` alias. Run `uv run python tools/quality_gate_system.py`; if it passes, `git commit --no-verify`. Never a `WIP:` prefix. End every message with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. Do not push.
- **Branch:** `calculus-fix-arc`, already created off `main` (`3b237c2`), spec committed at `30065a0`.

## File Structure

| File | Responsibility | Protected |
|---|---|---|
| `tests/calculus_expected.py` (modify) | licensed results; **gains** `postconditions()` for the six rules with no expected form | no |
| `tests/calculus_layers.py` (modify) | the four layer checks; `structure` calls `postconditions`; `refusal` splits its abstention label | no |
| `tests/calculus_enum.py` (modify) | tier A and tier B; **gains** the stress tier | no |
| `tests/calculus_run.py` (modify) | modes and the record stream; **gains** tier S | no |
| `tests/calculus_rules.py` (modify) | Dau's rule table, moves, `legal()`; **gains** `INS_EDGE` moves and its precondition | no |
| `tests/calculus_classifiers.py` (modify) | ledger classifiers; four broad predicates narrowed | no |
| `tests/test_calculus_*.py` (modify) | one file per layer/unit; new cases per task | no |
| `tools/repair_non_egi_corpus_graphs.py` (create) | Task 10's corpus repair, run once, kept as the record | no |
| `src/formal_transformation_rules.py` (modify) | IT+ and IT− preconditions | **yes** |
| `src/ligature_manipulation_rules.py` (modify) | the ligature rules' conditions and survivor choice | **yes** |
| `src/vertex_splitting_merging_rules.py` (modify) | MERGE_VERTICES' generic-only condition | no |
| `src/egi_core_dau.py` (modify) | `_context_dominates`; later Def 12.5 at construction | **yes** |
| `src/vertex_scope.py` (modify) | `normalize_constants` survivor placement | no |
| `src/derived_rules.py` (modify) | one stale comment | no |

---

### Task 1: Real postconditions for the six rules checked only for EGI-hood

**Files:**
- Modify: `tests/calculus_expected.py` (add `postconditions`)
- Modify: `tests/calculus_layers.py` (`structure` calls it; label stays `egi-only`)
- Modify: `tests/test_calculus_structure.py` (hand tests)

**Interfaces:**
- Produces: `calculus_expected.postconditions(g, m, h) -> list[str]` — the problems found, empty when the result satisfies every postcondition. Consumed by `calculus_layers.structure`.

Today `structure` checks an `egi-only` move for EGI-hood and maps only, so a no-op `RETRACT_LIGATURE` passes (spec §3). These rules only re-plumb identity, which gives three postconditions that hold for all six: the result differs from the source; the multiset of non-identity relations is unchanged; and each rule's own element-count delta.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_calculus_structure.py`:

```python
def test_a_no_op_ligature_move_is_now_a_failure():
    """The defect shape the suite could not see: success that changes nothing."""
    g = parse_egif('(= "a" "b")')
    m = Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet)
    rec = Record("A", "hand", g, m, "hand|noop", Outcome(True, g, ""), None, "not judged")
    label, detail = structure(rec, {})
    assert label.endswith("egi-only") and detail and "changes nothing" in detail


def test_a_ligature_move_that_drops_a_relation_is_a_failure():
    g = parse_egif('(P "a") (= "a" "b")')
    h = parse_egif('(= "a" "b")')          # the P edge has vanished
    m = Move("MOVE_BRANCHES", tuple(sorted(v.id for v in g.V)), g.sheet)
    rec = Record("A", "hand", g, m, "hand|dropped", Outcome(True, h, ""), None, "not judged")
    assert "relations" in structure(rec, {})[1]


def test_split_must_add_one_vertex_and_one_identity_edge():
    g = parse_egif("(P *x) (Q x)")
    m = Move("SPLIT_VERTEX", (sorted(v.id for v in g.V)[0],), g.sheet)
    rec = Record("A", "hand", g, m, "hand|split", Outcome(True, g, ""), None, "not judged")
    assert "+1 vertex" in structure(rec, {})[1]


def test_a_real_retraction_passes_its_postconditions():
    """`(= "a" "b")` retracted to one vertex: fewer vertices, no identity edge
    left, and the non-identity relations untouched (there are none)."""
    g = parse_egif('(= "a" "b")')
    h = parse_egif('"a"')
    m = Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet)
    rec = Record("A", "hand", g, m, "hand|real", Outcome(True, h, ""), None, "not judged")
    assert structure(rec, {})[1] is None
```

Add to that file's imports: `from calculus_apply import Outcome`, `from calculus_layers import structure`, `from calculus_rules import Move`, `from calculus_run import Record`, `from egif_parser_dau import parse_egif` (some are already there — do not duplicate).

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_calculus_structure.py -q -k "no_op or drops_a_relation or split_must or real_retraction"`. Expected: 4 failed (`detail` is `None`, or `postconditions` is missing).

- [ ] **Step 3: Implement** — append to `tests/calculus_expected.py`:

```python
# The six rules with no expected form (the four ligature rules, split, merge)
# re-plumb identity and nothing else, so three postconditions hold for all of
# them, and each carries its own element-count delta. Dau: Lemmas 16.1-16.3 and
# Def 16.4 (p.169-175) rewire a ligature; Def 16.6 (p.175-176) splits and
# merges. None of them adds, drops or re-relates a non-identity edge.
_IDENTITY = "="


def _relation_multiset(g: G):
    return sorted((g.rel[e], len(g.nu[e])) for e in g.nu if g.rel[e] != _IDENTITY)


def _counts(g: G):
    ids = sum(1 for e in g.nu if g.rel[e] == _IDENTITY)
    return len(g.V), ids


def postconditions(g: G, m: Move, h: G) -> List[str]:
    """What must hold of a rule whose licensed result the suite does not build.
    Returns the problems; empty means the result satisfies every one."""
    problems: List[str] = []
    if nav.same_graph(g, h):
        problems.append("the move reports success and changes nothing")
    if _relation_multiset(g) != _relation_multiset(h):
        problems.append("the non-identity relations changed: these rules re-plumb "
                        "identity only (Lemmas 16.1-16.3, Def 16.4, Def 16.6)")
    (v0, i0), (v1, i1) = _counts(g), _counts(h)
    if m.rule == "SPLIT_VERTEX" and (v1 - v0, i1 - i0) != (1, 1):
        problems.append(f"split must add +1 vertex and +1 identity edge (Def 16.6, p.175), "
                        f"got {v1 - v0:+d} vertex and {i1 - i0:+d} identity edge")
    if m.rule == "MERGE_VERTICES" and (v1 - v0, i1 - i0) != (-1, -1):
        problems.append(f"merge must drop 1 vertex and 1 identity edge (Def 16.6, p.176), "
                        f"got {v1 - v0:+d} vertex and {i1 - i0:+d} identity edge")
    if m.rule == "MOVE_BRANCHES" and (v1, i1) != (v0, i0):
        problems.append(f"moving a branch changes no counts (Lemma 16.1, p.169), "
                        f"got {v1 - v0:+d} vertex and {i1 - i0:+d} identity edge")
    if m.rule == "RETRACT_LIGATURE" and not (v1 < v0 and i1 < i0):
        problems.append(f"retraction collapses a ligature to one vertex (Lemma 16.3, p.173): "
                        f"fewer vertices and fewer identity edges, got {v1 - v0:+d} and {i1 - i0:+d}")
    if m.rule == "EXTEND_LIGATURE" and not (v1 > v0 and i1 > i0):
        problems.append(f"extension adds vertices and identity edges (Lemma 16.2, p.172), "
                        f"got {v1 - v0:+d} and {i1 - i0:+d}")
    return problems
```

`nav` is already imported in that module as `import eg_navigation as nav`; if not, add it.

Then in `tests/calculus_layers.py`, inside `structure`, after the `maps_carried` line:

```python
    forms = acceptable(g, m) if rec.verdict else None
    if forms is None and m.rule in POSTCONDITION_RULES:
        problems += postconditions(g, m, h)
    if forms is not None and not any(nav.same_graph(f, h) for f in forms):
```

and at the top of the module:

```python
from calculus_expected import acceptable, maps_carried, postconditions

# The rules whose licensed result is not built, so postconditions carry the
# check instead (spec 2026-09-12 §3.1).
POSTCONDITION_RULES = frozenset({
    "MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE",
    "SPLIT_VERTEX", "MERGE_VERTICES",
})
```

Update `structure`'s docstring: `egi-only` now means EGI-hood, maps **and** the rule's postconditions; only an abstention on a *judged* rule is checked for EGI-hood and maps alone.

- [ ] **Step 4: Run the hand tests.** Same command as Step 2. Expected: 4 passed.

- [ ] **Step 5: Run the layer and adjudicate.** `CALCULUS_LEDGER_DUMP=/tmp/fix1 uv run pytest tests/test_calculus_structure.py -q -k "not extent"`. New failures are expected: these postconditions have never run. For each group, reproduce one instance by hand, then decide as in the spec §5 — a real engine departure gets a ledger entry (id, layer `structure`, rule, a reason naming the Dau page and what the engine did, a classifier in `tests/calculus_classifiers.py`, and its instances or counts); a postcondition that is wrong about Dau gets fixed here, with a hand test and the page cited. Expect `REARRANGE_LIGATURE` and `EXTEND_LIGATURE` to be the interesting ones.

- [ ] **Step 6: Re-pin and commit.** `CALCULUS_EXTENT_WRITE=1 uv run pytest tests/test_calculus_structure.py -q -k extent`, read the diff (only structure labels should move), re-run without the variable, then the default calculus suite. Gate, commit: `Calculus suite: the six egi-only rules get real postconditions`.

---

### Task 2: The stress tier

**Files:**
- Modify: `tests/calculus_enum.py` (`STRESS`, `tier_s`)
- Modify: `tests/calculus_run.py` (tier S in `_tiers`, `graphs_for`)
- Modify: `tests/calculus_rules.py` (`moves` treats tier S like tier A)
- Modify: `tests/test_calculus_enum.py` (shape coverage), and the four layer test files' extent pins

**Interfaces:**
- Produces: `calculus_enum.STRESS: tuple[tuple[str, str], ...]` (name, EGIF) for the parseable shapes, `calculus_enum.tier_s() -> list[tuple[str, G]]` (cached), including one graph built directly because no linear form can carry it.

Tier A reaches at most 3 elements by default and 4 at exhaustive, with at most 2 cuts, so the canonical scroll with a line (5 elements) is outside it (spec §3.2). This tier is small, hand-chosen and always run in both modes.

- [ ] **Step 1: Write the failing test** — append to `tests/test_calculus_enum.py`:

```python
def test_the_stress_tier_carries_the_shapes_tier_a_cannot():
    from calculus_enum import tier_s
    from tarski import dominating_nodes
    graphs = dict(tier_s())
    assert set(graphs) == {
        "scroll-with-a-line", "deiteration-across-two-cuts", "arguments-swapped",
        "theta-linked-copy", "parity-depth-3", "parity-depth-4",
        "alphabet-and-quotation", "name-against-name", "edge-insertion-target",
    }
    assert all(dominating_nodes(g) for g in graphs.values())
    # every one is beyond the default tier-A bound of 3 elements
    assert all(len(g.V) + len(g.E) + len(g.Cut) > 3 for g in graphs.values())
    # the one shape no linear form carries: B-min maps, so the maps clause bites
    q = graphs["alphabet-and-quotation"]
    assert q.alphabet is not None and q.sort and q.quotation
```

- [ ] **Step 2: Run to see it fail.** `uv run pytest tests/test_calculus_enum.py -q -k stress` → ImportError.

- [ ] **Step 3: Implement** — append to `tests/calculus_enum.py`:

```python
# The stress tier (spec 2026-09-12 §3.2): hand-chosen shapes beyond tier A's
# bounds, the ones that stress the rules Dau states. Every graph here was named
# by the final whole-branch review of the property suite.
STRESS: Tuple[Tuple[str, str], ...] = (
    ("scroll-with-a-line", "*x ~[ (P x) ~[ (Q x) ] ]"),
    ("deiteration-across-two-cuts", "*x (P x) ~[ ~[ (P x) ] ]"),
    ("arguments-swapped", "*x *y (R x y) ~[ (R y x) ]"),
    ("theta-linked-copy", "*x *y (P x) ~[ (= x y) (P y) ]"),
    ("parity-depth-3", "~[ ~[ ~[ (p) ] ] ]"),
    ("parity-depth-4", "~[ ~[ ~[ ~[ (p) ] ] ] ]"),
    ("name-against-name", '(Q "a") (Q "b") ~[ (P "b") ] ~[ ~[ (P "a") ] ]'),
    ("edge-insertion-target", "*x ~[ ]"),
)


def _alphabet_and_quotation() -> G:
    """The one stress shape no linear form carries: a declared alphabet, a
    sorted quoting name and a quotation oval, so the structure layer's maps
    clause is exercised at a tier that is not the corpus (tier A has no
    maps-bearing record at all). The isolated vertex is the quoting name and
    the cut is its oval; the alphabet is set directly because the parser
    leaves it None. Verified while planning: sort, quotation and alphabet all
    present, a valid EGI of four elements."""
    from dataclasses import replace

    from egi_core_dau import AlphabetDAU
    from egif_parser_dau import parse_egif

    g = parse_egif("[*z] ~[ (P *x) ]")
    used = {v for e in g.nu for v in g.nu[e]}
    quoting_name = next(v.id for v in g.V if v.id not in used)
    oval = next(c.id for c in g.Cut)
    h = g.with_quotation_binding(quoting_name, oval, sort_name="proposition")
    alphabet = AlphabetDAU(
        C=frozenset(), F=frozenset(), R=frozenset({"P"}), ar=frozendict({"P": 1})
    ).with_defaults()
    return replace(h, alphabet=alphabet, rho=frozendict({v.id: None for v in h.V}))


@functools.lru_cache(maxsize=None)
def tier_s() -> List[Tuple[str, G]]:
    from egif_parser_dau import parse_egif
    out = [(name, parse_egif(text)) for name, text in STRESS]
    out.append(("alphabet-and-quotation", _alphabet_and_quotation()))
    return sorted(out)
```

`_alphabet_and_quotation`'s body above is the code verified while planning: `with_quotation_binding(vertex_id, cut_id, *, sort_name)` takes the vertex first and the sort as a keyword, and the result carries `sort`, `quotation` and a non-None `alphabet` — which is what the test asserts.

In `tests/calculus_run.py`:

```python
def graphs_for(mode: Mode, tier: str):
    if tier == "A":
        return tier_a(mode.bounds).graphs
    if tier == "S":
        return tier_s()
    return tier_b(include_chains=(mode.tier_b == "all")).graphs


def _tiers(mode: Mode):
    return ("A", "S") if mode.tier_b == "none" else ("A", "S", "B")
```

(add `tier_s` to the `calculus_enum` import), and in `records`, `budget`/`units_only` must treat S like A:

```python
        budget = None if tier in ("A", "S") else mode.tier_b_budget
        units_only = tier == "B" and mode.tier_b == "current-units"
```

In `tests/calculus_rules.py`, `_selections` must enumerate every subset for tier S:

```python
    if tier in ("A", "S"):
        yield from _subsets(elements(g), lo)
        return
```

- [ ] **Step 4: Run.** `uv run pytest tests/test_calculus_enum.py -q -k stress` → PASS.

- [ ] **Step 5: Run every layer and adjudicate.** `CALCULUS_LEDGER_DUMP=/tmp/fix2 uv run pytest tests/test_calculus_*.py -q -k "not extent"`. The stress tier is the point of this task: expect new failures, and expect some to be the very defects this arc is about to fix (IT+ into its own selection, IT− of a non-copy, the ligature faults). Ledger each under its existing entry where the mechanism matches — a classifier keyed on rule and message will claim tier-S instances automatically — and adjudicate anything new as in spec §5.
- [ ] **Step 6: Re-pin every extent** (`CALCULUS_EXTENT_WRITE=1 uv run pytest tests/test_calculus_*.py -q -k extent`), read the diff: every layer gains `S:` counts. Re-run clean, run the quality gate, commit: `Calculus suite: a stress tier for the shapes tier A cannot reach`.

---

### Task 3: `INS_EDGE`'s candidate moves, counted

**Files:**
- Modify: `tests/calculus_rules.py` (table row's engine, `moves`, `legal`)
- Modify: `tests/calculus_apply.py` (content built from the host graph)
- Modify: `tests/test_calculus_rules.py`, `tests/test_calculus_legal.py`

Dau p.165: erasing an edge keeps its vertices, and insertion is its inverse, so in a negative context an edge may be inserted onto vertices already present. The engine's INS takes standalone EGIF and refuses this ("Undefined variable x"). Task 12 of the previous arc recorded it as unimplemented; now it is enumerated so the gap is counted as INCOMPLETE on every run.

- [ ] **Step 1: Write the failing tests** — in `tests/test_calculus_legal.py`:

```python
def test_ins_edge_is_legal_onto_an_existing_line_in_a_negative_context():
    """Dau p.165: erasing an edge keeps its vertices (V^(e) := V), and insertion
    is its inverse, so `*x ~[ ]` may become `*x ~[ (P x) ]`."""
    g = parse_egif("*x ~[ ]")
    c = _cuts_by_depth(g)[0]
    v = _vertex(g)
    assert ok(g, Move("INS_EDGE", (v,), c, "(P x)")) is True
    assert ok(g, Move("INS_EDGE", (v,), g.sheet, "(P x)")) is False   # positive context
```

and in `tests/test_calculus_rules.py`:

```python
def test_ins_edge_moves_are_enumerated_and_the_engine_refuses_them():
    from calculus_apply import apply_move
    g = parse_egif("*x ~[ ]")
    ms = [m for m in moves("INS_EDGE", g, "A")]
    assert ms, "INS_EDGE must offer at least one candidate on *x ~[ ]"
    out = apply_move(g, ms[0])
    assert not out.applied and not out.crashed        # counted INCOMPLETE, never a crash
```

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_calculus_legal.py tests/test_calculus_rules.py -q -k ins_edge`. Expected: failures (`KeyError: no move generator for INS_EDGE`, and `legal` has no `INS_EDGE` entry).

- [ ] **Step 3: Implement.** In `tests/calculus_rules.py`, change the `INS_EDGE` row to carry the protocol entry point and be judged:

```python
    DauRule("INS_EDGE", "Def 15.2 insertion of an edge onto existing vertices, p.165: negative contexts", "one-way", "protocol:INS", True),
```

`UNIMPLEMENTED` is derived from `engine is None`, so update `test_the_unimplemented_dau_rules_are_exactly_these` to the remaining five, and the three documents that say six (CLAUDE.md, CURRENT_PLAN's seventeenth-arc block, spec §1a.2 of the suite's design) to say: five have no entry point, and INS_EDGE has one that refuses every candidate, counted as INCOMPLETE. Then add the generator:

```python
    elif rule == "INS_EDGE":
        # Dau p.165: an edge inserted into a negative context onto vertices
        # already present. The content names the host's own line by its EGIF
        # bound label, which is what the engine cannot parse.
        for a in areas:
            if positive(g, a):
                continue
            for v in sorted(x.id for x in g.V if x.is_generic):
                label = g.variable_names.get(v)
                # The line must be in scope at the target: ctx(v) encloses it
                # (Def 12.5), i.e. ctx(v) is on the target's ancestor chain.
                if label is None or g.get_context(v) not in ancestors(g, a):
                    continue          # unnamed line, or out of scope here
                yield Move(rule, (v,), a, f"(P {label})")
```

and the precondition:

```python
def _ins_edge(g: G, m: Move) -> Verdict:
    """Def 15.2 insertion, p.165: erasing an edge keeps its vertices
    (V^(e) := V), so its inverse inserts an edge onto vertices already
    present, in a negative context. The selection names those vertices; the
    content is the edge, written with the host's bound label."""
    if m.target is None or positive(g, m.target):
        return False, "the target is not a negative context"
    if len(m.selection) != 1 or m.selection[0] not in {v.id for v in g.V}:
        return False, "select the existing vertex the edge hooks onto"
    v = m.selection[0]
    if m.target not in ancestors(g, m.target) or g.get_context(v) not in ancestors(g, m.target):
        return False, "the vertex's context must enclose the target (Def 12.5)"
    return True, "an edge onto an existing line, negative context"
```

Add `"INS_EDGE": _ins_edge` to `_LEGAL`. In `tests/calculus_apply.py`, INS_EDGE reaches the protocol like INS (`egif=m.content, target=m.target`) — the existing `protocol:` branch already passes both, so no change is needed unless a crash appears; if the protocol raises something other than `AssertionError`, record it as a crash and report it.

- [ ] **Step 4: Run.** Both test files, `-k ins_edge` → PASS.
- [ ] **Step 5: Adjudicate and pin.** Run every layer with `CALCULUS_LEDGER_DUMP=/tmp/fix3`; the INS_EDGE candidates arrive as refused-but-legal, so they need one ledger entry (`ins-edge-has-no-entry-point`, layer `refusal`, INCOMPLETE) with a classifier and the Dau page. Re-pin, re-run, gate, commit: `Calculus suite: Dau's edge insertion is enumerated, not just named`.

---

### Task 4: Abstention reasons, and the four broad classifiers narrowed

**Files:**
- Modify: `tests/calculus_layers.py` (`refusal`'s `not:` label)
- Modify: `tests/calculus_classifiers.py` (four predicates)
- Modify: `tests/test_calculus_refusal.py` (hand tests), extent pins

`not:{rule}` lumps together every abstention: the Θ clause, the IT− search ceiling, the B-min apparatus, and a non-EGI source. And four refusal classifiers match on rule and outcome alone, so a regression that trades one key for another inside the same entry and kind passes silently (the final review's minor).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_calculus_refusal.py`:

```python
def test_an_abstention_is_labelled_by_its_reason():
    g = parse_egif("(P *x)")
    m = Move("MOVE_BRANCHES", (sorted(v.id for v in g.V)[0],), g.sheet)
    rec = Record("A", "hand", g, m, "hand|abst", Outcome(False, None, ""), None,
                 "not judged: MOVE_BRANCHES's parameters underdetermine the move")
    assert refusal(rec, {})[0] == "not:MOVE_BRANCHES:underdetermined"


def test_heavy_dot_classifier_requires_a_positive_context():
    """The entry's reason is about positive contexts (Dau p.166 allows any), so
    its classifier must not claim a refusal in a negative one."""
    from calculus_classifiers import REFUSAL
    g = parse_egif("~[ ]")
    c = next(iter(g.Cut)).id
    neg = Record("A", "hand", g, Move("VERTEX_INS", (), c), "k", Outcome(False, None, "no"), True, "any context")
    pos = Record("A", "hand", g, Move("VERTEX_INS", (), g.sheet), "k", Outcome(False, None, "no"), True, "any context")
    assert not REFUSAL["heavy-dot-negative-only"](neg, "d")
    assert REFUSAL["heavy-dot-negative-only"](pos, "d")
```

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_calculus_refusal.py -q -k "abstention or heavy_dot_classifier"`. Expected: 2 failed.

- [ ] **Step 3: Implement.** In `tests/calculus_layers.py`, replace the abstention line in `refusal`:

```python
    if rec.verdict is None:
        return f"not:{rec.move.rule}:{_abstention(rec.why)}", None
```

and add above it:

```python
# legal()'s abstentions, tagged so the extent shows which reason grew
# (spec 2026-09-12 §3.4). The order is longest-match-first; an unrecognised
# reason is tagged "other", which the tests pin at 0.
_ABSTENTIONS = (
    ("underdetermine", "underdetermined"),
    ("quotation-bearing graph", "quotation-bearing"),
    ("quotation apparatus", "quotation-apparatus"),
    ("Θ clause", "theta-clause"),
    ("search budget", "search-budget"),
    ("not an EGI", "not-an-EGI"),
)


def _abstention(why: str) -> str:
    for needle, tag in _ABSTENTIONS:
        if needle in why:
            return tag
    return "other"
```

In `tests/calculus_classifiers.py`, narrow the four:

```python
    "heavy-dot-negative-only":
        lambda r, d: _rule(r, "VERTEX_INS") and not r.outcome.applied
        and positive(r.g, r.move.target),
    "vertex-era-positive-only":
        lambda r, d: _rule(r, "VERTEX_ERA") and not r.outcome.applied
        and not positive(r.g, r.g.get_context(r.move.selection[0])),
    "vertex-era-erases-a-line-with-its-edges":
        lambda r, d: _rule(r, "VERTEX_ERA") and r.outcome.applied
        and bool(edges_on(r.g, r.move.selection[0])),
```

and give the merge entry its kind guard:

```python
    "merge-vertices-erases-a-constant-vertex":
        lambda r, d: _rule(r, "MERGE_VERTICES") and failure_kind("soundness", d) in
        ("UNSOUND", "NOT AN EQUIVALENCE") and bool(erased_constants(r.g, r.outcome.result)),
```

Import `positive` and `edges_on` (from `calculus_rules` and `calculus_enum`) at the top of the classifiers module.

- [ ] **Step 4: Run.** Step 2's command → PASS.
- [ ] **Step 5: Pin the `other` tag at 0.** Add to `tests/test_calculus_refusal.py`:

```python
def test_no_abstention_reason_is_unrecognised():
    counts = run("default").layers["refusal"].counts
    assert not [k for k in counts if k.endswith(":other")], sorted(counts)
```

- [ ] **Step 6: Re-pin, adjudicate, commit.** The narrowed classifiers may leave failures unclaimed (that is the point): adjudicate each as in spec §5 — a failure whose mechanism no entry describes needs its own entry. Re-pin every extent, read the diff (the `not:` labels all change), gate, commit: `Calculus suite: abstentions named, classifiers narrowed to their mechanism`.

---

### Task 5: IT+ may not copy into its own selection (protected)

**Files:**
- Modify: `src/formal_transformation_rules.py` (`IterationRule.check_preconditions`) — **PROTECTED**
- Modify: `tests/test_calculus_rules.py` (hand test)

**Interfaces:** consumes nothing new; the protocol path already routes here (`ITPlusInteraction._get_rule` returns `IterationRule`), so this single condition covers both entry points.

- [ ] **Step 1: STOP and confirm with the author.** This is the first protected edit of the arc. Report: the file, the function, the condition being added, and that `.core_modification_authorized` is needed. Wait for the go-ahead.
- [ ] **Step 2: Write the failing test** — append to `tests/test_calculus_rules.py`:

```python
def test_the_engine_refuses_iteration_into_its_own_selection():
    """Dau Def 15.2 (p.164, 166): the destination must satisfy c <= ctx(G0) AND
    c not in Cut0. Without the second half, `~[ ~[ ] ]` (true in every
    structure) becomes `~[ ~[ ~[ ] ] ]` (false in every structure)."""
    from calculus_apply import apply_move
    from tarski import Structure, satisfies
    g = parse_egif("~[ ~[ ] ]")
    inner = next(c.id for c in g.Cut if g.get_context(c.id) != g.sheet)
    out = apply_move(g, Move("IT+", (inner,), inner))
    assert not out.applied and not out.crashed, out.message
    assert satisfies(g, Structure(1, {}, {}))          # the source still holds
```

- [ ] **Step 3: Run to see it fail.** `uv run pytest tests/test_calculus_rules.py -q -k iteration_into_its_own`. Expected: FAIL — the move is applied today.
- [ ] **Step 4: Implement.** In `IterationRule.check_preconditions`, after the existing `_is_enclosed_by` check and before the B-min quotation guard:

```python
        # Dau Def 15.2 (p.164, 166): the destination c must satisfy both
        # c <= ctx(G0) *and* c ∉ Cut0 — a cut being copied may not receive the
        # copy. Without the second half, iterating the inner cut of ~[ ~[ ] ]
        # into itself gives ~[ ~[ ~[ ] ] ]: true becomes false.
        expanded = set(context.selected_subgraph)
        stack = list(expanded)
        while stack:
            element = stack.pop()
            for nested in egi.area.get(element, frozenset()):
                if nested not in expanded:
                    expanded.add(nested)
                    stack.append(nested)
        if context.target_area in expanded:
            return False, (
                f"IT+ may not copy into the selection's own cut "
                f"(Dau Def 15.2, p.166: c ∉ Cut₀). Destination "
                f"{context.target_area} lies inside the selected subgraph."
            )
```

- [ ] **Step 5: Run the hand test** (Step 3's command) → PASS.
- [ ] **Step 6: Check for tests that asserted the old behaviour.** Run `uv run pytest tests/test_rule_interaction.py tests/test_chapter15_formal_calculus.py tests/test_beta_proof_exercises.py tests/test_logical_proof_exercises.py tests/test_epg_exemplar_scripts.py tests/test_rules_second_order.py tests/test_corpus_polarity_discipline.py tests/test_ergasterion_routes.py -q`. If any test fails because it iterated into its own selection, that test asserted an unsound move: report it with the Dau page and fix the test, never the condition.
- [ ] **Step 7: Prove it by the ledger.** `uv run pytest tests/test_calculus_*.py -q -k "not extent"`. Expect SHRINK on `it-plus-into-its-own-selection` (refusal) and `it-plus-into-its-own-selection-changes-meaning` (soundness). Delete both entries and their classifiers, re-run, re-pin the extents, read the diff.
- [ ] **Step 8: Commit.** Gate, `--no-verify`: `IT+ stops copying a cut into itself (Dau Def 15.2, p.166)`, the body naming the two retired entries and the `~[ ~[ ] ]` case.

---

### Task 6: IT− may erase only a genuine copy (protected)

**Files:**
- Modify: `src/formal_transformation_rules.py` (`DeiterationRule._check_deiteration_with_isomorphism_engine`) — **PROTECTED**
- Modify: `tests/test_calculus_it_minus_controls.py` (the strict xfails go)

- [ ] **Step 1: STOP and confirm with the author** (protected edit). Report the file, the function, and the condition.
- [ ] **Step 2: See the controls fail as XPASS.** After the fix the three strict xfails flip; first record where they stand: `uv run pytest tests/test_calculus_it_minus_controls.py -q` → 23 passed, 3 xfailed.
- [ ] **Step 3: Implement.** Replace the body of `_check_deiteration_with_isomorphism_engine` with a version that filters the engine's matches:

```python
    def _check_deiteration_with_isomorphism_engine(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """Check deiteration validity: a structural match in the nest of cuts
        that is also a *copy*.

        Dau Def 15.2 (p.166): iteration copies G0's own vertices (V0 × {2}) and
        reaches a vertex outside the copy only through an identity edge
        e_{v,w} with wΘv — the same line. So a candidate whose edge hooks an
        outside vertex is a copy only if the original hooks *that very vertex*
        at that position. The isomorphism engine matches structure alone, which
        is why the engine deiterated non-copies: `*x *y (P x) ~[ (P y) ]` and,
        with names, `(Q "a") (Q "b") ~[ (P "b") ] ~[ ~[ (P "a") ] ]`.
        """
        egi = context.source_egi
        selected = context.selected_subgraph
        nesting_hierarchy = self._get_nesting_hierarchy(egi, context.target_area)
        search_areas = [a for a in nesting_hierarchy if a != context.target_area]

        validator = IsomorphismValidator()
        matches = validator.engine.find_isomorphic_subgraphs(egi, selected, search_areas)
        if not matches:
            return False, "No structurally identical subgraph found in nest of cuts"

        for _area, _image, mapping in matches:
            if self._match_is_a_copy(egi, selected, mapping):
                return True, None
        return False, (
            "No isomorphic original found whose edges reach the same lines: a copy "
            "hooks an outside vertex only along that same line (Dau Def 15.2, p.166)"
        )

    def _match_is_a_copy(self, egi, selected, mapping) -> bool:
        """Every edge of the candidate must reach, at each position, either the
        image of a selected vertex or the very same outside vertex."""
        for edge_id in selected:
            if edge_id not in egi.nu:
                continue
            source_edge = mapping.edge_mapping.get(edge_id)
            if source_edge is None or source_edge not in egi.nu:
                return False
            copy_args, source_args = egi.nu[edge_id], egi.nu[source_edge]
            if len(copy_args) != len(source_args):
                return False
            for position, vertex_id in enumerate(copy_args):
                if vertex_id in selected:
                    if mapping.vertex_mapping.get(vertex_id) != source_args[position]:
                        return False
                elif source_args[position] != vertex_id:
                    return False
        return True
```

- [ ] **Step 4: Run the controls.** `uv run pytest tests/test_calculus_it_minus_controls.py -q`. Expected: the three xfails now XPASS, and strict mode turns each into a failure — that is the signal the fix worked.
- [ ] **Step 5: Retire the xfails.** Remove the `@pytest.mark.xfail(...)` decorator and `XFAIL_REASON`, and rewrite `test_a_non_copy_is_not_deiterated` to assert the new facts: the engine refuses each of the three, with the "same lines" message, and `legal()` still says False. Keep the module docstring's history, marked as fixed with the commit.
- [ ] **Step 6: Regression sweep.** The same suites as Task 5 Step 6, plus `tests/test_it_minus_with_isomorphism.py` and `tests/test_graph_isomorphism_engine.py`. A test that asserted a non-copy could be deiterated asserted an unsound move: report, then fix the test with the page cited.
- [ ] **Step 7: Prove it by the ledger.** Expect SHRINK on `it-minus-erases-a-copy-of-another-line` and `it-minus-erases-a-copy-of-another-line-changes-meaning`. Delete both and their classifiers; re-pin; read the diff.
- [ ] **Step 8: Commit.** `IT- erases only a copy, not a look-alike (Dau Def 15.2, p.166)`.

---

### Task 7: The ligature rules — one context, a deterministic survivor, generic vertices, and Lemma 16.1's side condition (protected)

**Files:**
- Modify: `src/ligature_manipulation_rules.py` — **PROTECTED**
- Modify: `src/vertex_splitting_merging_rules.py` (MERGE_VERTICES; not protected)
- Modify: `tests/test_calculus_rules.py` (hand tests), `tests/calculus_apply.py` (retire `InOrder`)

- [ ] **Step 1: STOP and confirm with the author** (protected edit). Four conditions in one file, each with its Dau page.
- [ ] **Step 2: Write the failing tests** — append to `tests/test_calculus_rules.py`:

```python
def test_retraction_refuses_a_ligature_whose_edge_is_deeper_than_its_vertices():
    """Lemma 16.3 (p.173) requires ctx(w) = c = ctx(f) for every vertex AND
    every identity edge. `*x *y ~[ (= x y) ]` says two things differ; retracting
    it gave `*x ~[ ]`, which is false."""
    from calculus_apply import apply_move
    g = parse_egif("[*x] [*y] ~[ (= x y) ]")
    out = apply_move(g, Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert not out.applied and "same context" in out.message


def test_the_ligature_rules_refuse_constant_vertices():
    """Def 24.10 (p.270-272) states them for generic vertices; joining
    constants is the Constant Identity rule, which requires the same name."""
    from calculus_apply import apply_move
    g = parse_egif('(= "a" "b")')
    out = apply_move(g, Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert not out.applied and "generic" in out.message


def test_the_survivor_does_not_depend_on_the_hash_seed():
    """Two vertices, both generic, one ligature: whichever survives, the
    choice is a function of the graph (canonical signature), not of the
    process."""
    from calculus_apply import apply_move
    g = parse_egif("[*x] [*y] (= x y) (P x)")
    sel = tuple(sorted(v.id for v in g.V))
    first = apply_move(g, Move("RETRACT_LIGATURE", sel, g.sheet))
    second = apply_move(g, Move("RETRACT_LIGATURE", tuple(reversed(sel)), g.sheet))
    assert first.applied and second.applied
    assert sorted(v.id for v in first.result.V) == sorted(v.id for v in second.result.V)


def test_move_branches_refuses_to_move_the_edge_that_witnesses_the_link():
    """Lemma 16.1 (p.169-171) needs v_aΘv_b to hold without the hook being
    moved; its proof's deiteration step is otherwise unlicensed."""
    from calculus_apply import apply_move
    g = parse_egif("[*x] [*y] (= x y)")
    out = apply_move(g, Move("MOVE_BRANCHES", tuple(sorted(v.id for v in g.V)), g.sheet))
    assert not out.applied and "witness" in out.message
```

- [ ] **Step 3: Run to see them fail.** `uv run pytest tests/test_calculus_rules.py -q -k "retraction_refuses or refuse_constant or hash_seed or witnesses_the_link"`. Expected: 4 failed.
- [ ] **Step 4: Implement the one-context condition** in `RetractLigatureRule.check_preconditions` and `LigatureRearrangementRule.check_preconditions`, after their existing "all vertices in the same context" block (both already compute `contexts`):

```python
        # Lemma 16.3 (p.173) / Def 16.4 (p.174): the ligature (W, F) is *placed
        # in* one context — every identity edge of it sits in c too, not only
        # its vertices. Without this, `*x *y ~[ (= x y) ]` retracts to
        # `*x ~[ ]`: true becomes false, because the edge was an assertion
        # under a negation, not wiring.
        (ligature_context,) = contexts
        for edge_id, vertex_sequence in egi.nu.items():
            if (
                egi.rel.get(edge_id) == "="
                and len(vertex_sequence) == 2
                and vertex_sequence[0] in selected_vertices
                and vertex_sequence[1] in selected_vertices
                and egi.get_context(edge_id) != ligature_context
            ):
                return False, (
                    f"The ligature's identity edges must lie in the same context as its "
                    f"vertices (Lemma 16.3, p.173): {edge_id} sits in "
                    f"{egi.get_context(edge_id)}, the vertices in {ligature_context}"
                )
```

- [ ] **Step 5: Implement the generic-only condition** in all four ligature rules' `check_preconditions` and in `VertexMergingRule.check_preconditions`, right after each verifies its selection is vertices:

```python
        # Def 24.10 (p.270-272) states the ligature rules for *generic*
        # vertices ("only generic vertices are considered", p.271-272). The one
        # rule that joins constants is the Constant Identity rule, and it
        # requires ρ(v) = ρ(w).
        named = [
            v_id for v_id in selected_vertices
            if not next(v for v in egi.V if v.id == v_id).is_generic
        ]
        if named:
            return False, (
                f"The ligature rules move generic vertices only (Def 24.10, p.270-272); "
                f"{named[0]} carries a constant name"
            )
```

(In `VertexMergingRule` the local variable is `vertices`, not `selected_vertices` — adapt the name, keep the message.)

- [ ] **Step 6: Implement the deterministic survivor** in `RetractLigatureRule.apply_transformation` (and the same pattern wherever a ligature rule picks a vertex off the frozenset — `LigatureRearrangementRule` and `ExtendRestrictLigatureRule` use `next(iter(...))`):

```python
            # The choice of survivor must be a function of the graph, not of the
            # process: a frozenset's iteration order follows the per-process
            # string hash, so `list(...)[0]` kept "a" under one hash seed and
            # "b" under another. Canonical signatures are UUID- and
            # seed-independent.
            from canonical_signature import compute_canonical_signatures
            vertex_signatures, _, _ = compute_canonical_signatures(egi)
            ligature_vertices = sorted(
                context.selected_subgraph,
                key=lambda v_id: (repr(vertex_signatures.get(v_id)), v_id),
            )
            target_vertex_id = ligature_vertices[0]
            vertices_to_remove = set(ligature_vertices[1:])
```

- [ ] **Step 7: Implement Lemma 16.1's side condition** in `MoveBranchesAlongLigatureRule.check_preconditions`, after the same-ligature check:

```python
        # Lemma 16.1 (p.169-171): the proof deiterates v3/e4/e1 as a copy of
        # v2, which needs v_aΘv_b to hold in the graph *without* the hook being
        # moved. If the only link witnessing v_aΘv_b is the edge carrying that
        # hook, the lemma does not license the move.
        hook_edges = [
            edge_id for edge_id, seq in egi.nu.items() if va_id in seq
        ]
        for edge_id in hook_edges:
            if not self._vertices_on_same_ligature_excluding(egi, va_id, vb_id, edge_id):
                return False, (
                    f"Moving the hook on {edge_id} would move the identity edge that "
                    f"witnesses the link itself (Lemma 16.1, p.169-171)"
                )
```

and add the helper beside `_vertices_on_same_ligature`:

```python
    def _vertices_on_same_ligature_excluding(
        self, egi: RelationalGraphWithCuts, va_id: ElementID, vb_id: ElementID,
        excluded_edge: ElementID,
    ) -> bool:
        """Whether v_aΘv_b still holds with ``excluded_edge`` set aside."""
        adjacency: Dict[ElementID, set] = {}
        for edge_id, seq in egi.nu.items():
            if edge_id == excluded_edge or egi.rel.get(edge_id) != "=" or len(seq) != 2:
                continue
            adjacency.setdefault(seq[0], set()).add(seq[1])
            adjacency.setdefault(seq[1], set()).add(seq[0])
        seen, stack = {va_id}, [va_id]
        while stack:
            current = stack.pop()
            if current == vb_id:
                return True
            for neighbour in adjacency.get(current, ()):
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        return vb_id in seen
```

- [ ] **Step 8: Run the hand tests** (Step 3's command) → 4 passed.
- [ ] **Step 9: Retire the suite's workaround.** `tests/calculus_apply.py`'s `InOrder` exists only because the engine's choice was seed-dependent. Remove it and the ordered-pair enumeration it feeds in `calculus_rules.moves`, then confirm the default records are identical across two hash seeds: `for s in 3 11; do PYTHONHASHSEED=$s uv run pytest tests/test_calculus_*.py -q -k "not extent"; done`.
- [ ] **Step 10: Regression sweep.** `uv run pytest tests/test_chapter16_17_ligature_soundness_simplified.py tests/test_rules_second_order.py tests/test_world_scroll.py tests/test_corpus_polarity_discipline.py -q`, plus `derived_rules`' users: `uv run pytest tests/test_universal_generalization*.py -q` if present, else grep `derived_rules` importers and run their tests.
- [ ] **Step 11: Prove it by the ledger.** Expect SHRINK on `ligature-rules-take-a-join-deeper-than-its-vertices`, `retract-ligature-erases-a-constant-vertex`, `merge-vertices-erases-a-constant-vertex`, `move-branches-moves-the-identity-edge-it-moves-along`. Delete them and their classifiers; re-pin; read the diff.
- [ ] **Step 12: Commit.** `The ligature rules stay inside Lemmas 16.1-16.3 and Def 24.10`.

---

### Task 8: The inverted dominating-nodes helper (protected)

**Files:**
- Modify: `src/egi_core_dau.py` (`_context_dominates`) — **PROTECTED**
- Modify: `src/derived_rules.py` (the stale comment)
- Modify: `tests/test_calculus_structure.py` (the `core-dominating` layer's hand tests)

- [ ] **Step 1: STOP and confirm with the author** (protected edit). One helper, three call sites corrected by it: `has_dominating_nodes`, `replace_vertex_on_hook` (Def 12.9) and `add_vertex_to_ligature` (Def 12.14).
- [ ] **Step 2: Write the failing tests** — append to `tests/test_calculus_structure.py`:

```python
def test_the_core_check_now_agrees_with_dau():
    """Def 12.5 (p.125): ctx(e) <= ctx(v). The helper tested the relation
    backwards and passed any edge on the sheet."""
    from frozendict import frozendict
    from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
    lawful = parse_egif("[*x] ~[ (Q x) ]")
    assert lawful.has_dominating_nodes()
    unlawful = RelationalGraphWithCuts(
        V=frozenset({Vertex("v1")}), E=frozenset({Edge("e1")}),
        nu=frozendict({"e1": ("v1",)}), sheet="S", Cut=frozenset({Cut("c1")}),
        area=frozendict({"S": frozenset({"e1", "c1"}), "c1": frozenset({"v1"})}),
        rel=frozendict({"e1": "P"}))
    assert not unlawful.has_dominating_nodes()


def test_a_lawful_hook_move_is_accepted():
    """Def 12.9 (p.128): a hook may be replaced by a vertex whose context
    encloses the edge's. The inverted helper refused exactly this."""
    g = parse_egif("[*x] ~[ [*y] (Q y) ]")
    outer = next(v.id for v in g.V if g.get_context(v.id) == g.sheet)
    edge = next(iter(g.E)).id
    moved = g.replace_vertex_on_hook(edge, 1, outer)
    assert moved.nu[edge] == (outer,)
```

- [ ] **Step 3: Run to see them fail.** `uv run pytest tests/test_calculus_structure.py -q -k "core_check_now or lawful_hook"`. Expected: 2 failed.
- [ ] **Step 4: Implement.** Replace `_context_dominates`:

```python
    def _context_dominates(self, inner: ElementID, outer: ElementID) -> bool:
        """Whether ``inner ≤ outer`` in Dau's context order (Def 12.2, p.125):
        ``outer`` is ``inner`` itself or encloses it.

        Walk outward from ``inner``. The previous implementation walked out
        from ``outer`` and returned True for any ``inner`` on the sheet, so it
        tested the relation backwards: `has_dominating_nodes` called an
        ordinary `(P *x) ~[ (Q x) ]` malformed and an edge-outside-its-vertex
        graph well formed, and `replace_vertex_on_hook` refused the lawful
        inner-to-outer hook move of Def 12.9.
        """
        current = inner
        while True:
            if current == outer:
                return True
            if current == self.sheet:
                return False
            current = self.get_context(current)
```

Then correct the stale comment in `src/derived_rules.py` (around line 192) that calls `replace_vertex_on_hook`'s refusal of a deep-hook-to-shallow-line move right: it was the inversion, and Def 12.9 licenses that move.

- [ ] **Step 5: Run the hand tests** → PASS.
- [ ] **Step 6: Regression sweep — this one is wide.** `uv run pytest tests/test_derived_rules*.py tests/test_world_scroll.py tests/test_m_steps.py tests/test_corpus_polarity_discipline.py tests/test_rules_second_order.py tests/test_chapter16_17_ligature_soundness_simplified.py -q` (drop any file that does not exist). Anything that depended on the inverted direction is a finding: report it with the page before touching it.
- [ ] **Step 7: Prove it by the ledger.** Expect SHRINK on `core-has-dominating-nodes-inverted` (9 of 208 tier-A graphs). Delete it and its classifier; re-pin; read the diff.
- [ ] **Step 8: Commit.** `Dominating nodes read in Dau's direction (Def 12.5, p.125)`.

---

### Task 9: `normalize_constants` places its survivor lawfully

**Files:**
- Modify: `src/vertex_scope.py` (not protected)
- Modify: `tests/test_vertex_scope.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_vertex_scope.py`:

```python
class TestTheSurvivorIsPlacedLawfully:
    """The ruling is Dau's (Def 24.10's Constant Identity rule, p.271, licenses
    the merge), but the survivor must still dominate every use it inherits
    (Def 12.5, p.125). Keeping it where it sat gave a non-EGI."""

    def _two_spots_in_sibling_cuts(self, first, second):
        from frozendict import frozendict
        from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
        return RelationalGraphWithCuts(
            V=frozenset({Vertex(first, label="a", is_generic=False),
                         Vertex(second, label="a", is_generic=False)}),
            E=frozenset({Edge("eP"), Edge("eQ")}),
            nu=frozendict({"eP": (first,), "eQ": (second,)}), sheet="S",
            Cut=frozenset({Cut("c1"), Cut("c2")}),
            area=frozendict({"S": frozenset({"c1", "c2"}),
                             "c1": frozenset({first, "eP"}),
                             "c2": frozenset({second, "eQ"})}),
            rel=frozendict({"eP": "P", "eQ": "Q"}))

    @pytest.mark.parametrize("order", [("va", "vb"), ("vb", "va")])
    def test_sibling_cuts_normalize_to_an_egi(self, order):
        from tarski import dominating_nodes
        g = self._two_spots_in_sibling_cuts(*order)
        assert dominating_nodes(normalize_constants(g))

    def test_a_survivor_deeper_than_a_twins_edge_is_hoisted(self):
        from frozendict import frozendict
        from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
        from tarski import dominating_nodes
        g = RelationalGraphWithCuts(
            V=frozenset({Vertex("va", label="a", is_generic=False),
                         Vertex("vb", label="a", is_generic=False)}),
            E=frozenset({Edge("eP"), Edge("eQ")}),
            nu=frozendict({"eP": ("va",), "eQ": ("vb",)}), sheet="S",
            Cut=frozenset({Cut("c1")}),
            area=frozendict({"S": frozenset({"vb", "eQ", "c1"}),
                             "c1": frozenset({"va", "eP"})}),
            rel=frozendict({"eP": "P", "eQ": "Q"}))
        assert dominating_nodes(normalize_constants(g))
```

(`pytest` is already imported there; add it if not.)

- [ ] **Step 2: Run to see them fail.** `uv run pytest tests/test_vertex_scope.py -q -k Survivor`. Expected: 3 failed (the results are not EGIs).
- [ ] **Step 3: Implement.** At the end of `normalize_constants`, hoist:

```python
    # The survivor inherits its twins' edges, so it must dominate them all
    # (Def 12.5, p.125). Keeping it where the id sort left it put edges outside
    # their own vertex's context whenever the twins sat in sibling cuts, or the
    # survivor sat deeper than a twin's edge. This is the module's own
    # "outward only" rule, applied to the merged line.
    return hoist_vertices_to_lca(result)
```

- [ ] **Step 4: Run** Step 2's command → 3 passed. Then `uv run pytest tests/test_vertex_scope.py tests/test_world_scroll.py tests/test_m_steps.py tests/test_corpus_polarity_discipline.py -q` (its only caller is `world_scroll.discharge_episode`).
- [ ] **Step 5: Commit.** `normalize_constants hoists its survivor to the least common area`.

---

### Task 10: The two corpus graphs, then Def 12.5 enforced at construction (protected)

**Files:**
- Create: `tools/repair_non_egi_corpus_graphs.py`
- Modify: `tomos/` data for `bfo_core` and `colore_field` (written by the tool)
- Modify: `tests/test_tomos_parsing.py` (`KNOWN_BROKEN`, the extent pin)
- Modify: `src/egi_core_dau.py` (`_validate_dau_constraints`) — **PROTECTED**
- Modify: `tests/test_calculus_enum.py` (the corpus-EGI guard's ledger)

Measured while designing: `hoist_vertices_to_lca` makes each graph an EGI and all three of its round trips then hold.

- [ ] **Step 1: Write the repair tool** — `tools/repair_non_egi_corpus_graphs.py`:

```python
"""Repair the two corpus graphs that are not EGIs (Dau Def 12.5, p.125).

`bfo_core` holds the generic vertex `v_x26`, and `colore_field` holds `v_zero`
and `v_one`, each placed in one cut while edges in *sibling* cuts use them. A
vertex must dominate every edge that uses it, so these stored graphs were never
EGIs — and that, not any linear form, is why their round trips failed: writing
them out and reading them back *repaired* them.

`vertex_scope.hoist_vertices_to_lca` performs exactly the repair: each vertex
moves outward to the least common area of its uses, which is the reading every
parser already applies. Run once:

    uv run python tools/repair_non_egi_corpus_graphs.py --write

Without --write it reports what it would do and changes nothing.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from cgif_generator_dau import generate_cgif
from cgif_parser_dau import parse_cgif
from clif_generator_dau import generate_clif
from clif_parser_dau import parse_clif
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from tomos_service import TomosService
from vertex_scope import hoist_vertices_to_lca

TOMOS = Path(__file__).resolve().parent.parent / "tomos"
GRAPHS = ("bfo_core", "colore_field")
FORMS = (("EGIF", generate_egif, parse_egif), ("CGIF", generate_cgif, parse_cgif),
         ("CLIF", generate_clif, parse_clif))


def dominating(graph) -> bool:
    for edge_id, sequence in graph.nu.items():
        chain, area = [], graph.get_context(edge_id)
        while True:
            chain.append(area)
            if area == graph.sheet:
                break
            area = graph.get_context(area)
        if any(graph.get_context(v) not in chain for v in sequence):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    service = TomosService(TOMOS)
    for uod_id in GRAPHS:
        uod = service.load_uod(uod_id, attest=False)
        before = uod.current_egi
        after = hoist_vertices_to_lca(before)
        moved = [v.id for v in after.V if after.get_context(v.id) != before.get_context(v.id)]
        print(f"{uod_id}: EGI {dominating(before)} -> {dominating(after)}; moved {moved}")
        if not dominating(after):
            print(f"  REFUSING {uod_id}: still not an EGI after the hoist")
            return 1
        for name, generate, parse in FORMS:
            if not nav.same_graph(after, parse(generate(after))):
                print(f"  REFUSING {uod_id}: the {name} round trip does not hold after the hoist")
                return 1
            print(f"  {name} round trip holds")
        if args.write:
            uod.current_egi = after
            uod._current_egif = uod._current_cgif = uod._current_clif = None
            service.save_uod(uod)
            print(f"  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Dry run.** `uv run python tools/repair_non_egi_corpus_graphs.py`. Expected: both graphs go False → True, the moved vertices named, and all three round trips holding for each. If any line refuses, stop and report — do not write.
- [ ] **Step 3: Write.** `uv run python tools/repair_non_egi_corpus_graphs.py --write`, then `git diff --stat tomos/` (two `current.egi.json` files, plus index touches).
- [ ] **Step 4: Retire the six KNOWN_BROKEN entries and re-pin.** In `tests/test_tomos_parsing.py`, empty `KNOWN_BROKEN` and change the pin to `(156, 9, 0, 147)`, with the comment saying why: the two graphs were not EGIs, and the repair is what made their round trips hold. Run `uv run pytest tests/test_tomos_parsing.py -q`: every round trip must now hold, and any entry left in `KNOWN_BROKEN` would fail with "now round-trips".
- [ ] **Step 5: Prove it by the ledger.** `uv run pytest tests/test_calculus_*.py -q -k "not extent"`: the `corpus-graph-not-an-egi` entry's two instances no longer fail, so SHRINK fires. Delete the entry (keep the guard test — it is what keeps a non-EGI out). Re-pin; tier-B counts move because the graphs changed; read the diff.
- [ ] **Step 6: STOP and confirm with the author** before the protected edit that follows.
- [ ] **Step 7: Enforce Def 12.5 at construction.** In `egi_core_dau._validate_dau_constraints`, after the ν checks:

```python
        # Def 12.5 with Def 12.7 (p.125-126): dominating nodes is part of what
        # an EGI *is*, so a structure without it is not one. Enforced here only
        # after the corpus was repaired (two stored graphs violated it), since
        # before that this raised on load.
        for edge_id, sequence in self.nu.items():
            edge_context = self.get_context(edge_id)
            for vertex_id in sequence:
                if not self._context_dominates(edge_context, self.get_context(vertex_id)):
                    raise ValueError(
                        f"Dominating nodes violated (Def 12.5): ctx({edge_id}) ≰ ctx({vertex_id})"
                    )
```

- [ ] **Step 8: The full suite.** `uv run pytest tests/ -q` in the background (~41 min). Every construction path now refuses a non-EGI, so this is where a producer that built one surfaces. Each failure is a finding: report it with the graph it tried to build before changing anything.
- [ ] **Step 9: Re-pin the tier-A enumeration.** `refused_by_core` may now be non-zero (the enumerator counts what construction refuses). Re-pin, read the diff, and state the new count in the commit.
- [ ] **Step 10: Commit** in two commits: `The corpus holds only EGIs again (Dau Def 12.5, p.125)` for the repair and the retired entries, then `Def 12.5 is enforced where graphs are built` for the core edit.

---

### Task 11: The exhaustive run, the write-up, and the alphabet question

**Files:**
- Modify: `tests/calculus_extent.json` (exhaustive pins), `tests/calculus_ledger.json` (whatever remains)
- Modify: `CURRENT_PLAN.md`, `CLAUDE.md`, the fix-arc spec's status line

- [ ] **Step 1: The exhaustive run.** In the background (~2 h 41 min at the measured budget, and the fixes change the counts): `CALCULUS_EXTENT_WRITE=1 uv run pytest tests/test_calculus_*.py -m exhaustive -q > /tmp/exhaustive.log 2>&1`. Then a clean confirming run without the write flag; its wall time is the figure to quote.
- [ ] **Step 2: Adjudicate whatever the exhaustive run surfaces.** A fix can retire a mechanism at default bounds and leave a variant at exhaustive: each is either a new entry with its Dau page, or a real residue of the fix, which means the fix is incomplete — report it rather than ledgering it.
- [ ] **Step 3: The priors.** In the suite's spec §7, record beneath each prior what this arc changed: P-K2 and P-K3 should now read HELD for the fixed rules, with the entries that retired named. Leave the pre-registered statements themselves unedited.
- [ ] **Step 4: The full suite,** foreground or background, and the quality gate. It must be green; `test_memory_stability` may fail as the documented warm-process flake — if it does, say so plainly and do not loosen it.
- [ ] **Step 5: The write-up.** A new dated block at the top of `CURRENT_PLAN.md` (eighteenth arc), the previous marker demoted, carrying: what was fixed and the ledger entries that retired, with every figure read from `tests/calculus_extent.json`, `tests/calculus_ledger.json` and the run output; the corpus at 147/147; what remains ledgered (the INCOMPLETE departures, HEAVY_DOT, DC+ and ERA, and the five rules with no entry point); and the author's standing principle at the head. Update `CLAUDE.md`'s test count and the Testing entries for any new file.
- [ ] **Step 6: The alphabet question — bring it to the author, do not decide it.** Present the two decisions the blocked 11c left (spec §4 step 7): whether the EGIF parser refuses a relation name used at two arities (Def 12.6, p.126), and which tests assert the current behaviour; and whether the core's builders extend the alphabet (protected `egi_core_dau`) or the alphabet is derived rather than stored. Report the 15 failing tests by name and cause, and stop.
- [ ] **Step 7: Commit** and offer the branch's integration (`superpowers:finishing-a-development-branch`).

