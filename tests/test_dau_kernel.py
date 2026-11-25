"""The kernel judges the engine, so it may not consult it.

``src/dau_kernel.py`` holds ``legal()`` and the licensed results — the suite's
oracle, promoted on 2026-11-25 (calculus-conformance specification §3.1). The
property that made the oracle worth having was that it shared no code with the
rules it judged. That property is held here, by reading the kernel's imports,
because a sentence saying so would not notice the day it stopped being true.

Three things are pinned: what the kernel itself imports; what those imports load
in their turn (the trusted base is larger than the three modules named, and the
difference is written down rather than discovered later); and that the suite
judges with the kernel's functions and keeps no copy of its own.
"""
import ast
from dataclasses import fields
from pathlib import Path

import pytest

import dau_kernel

SRC = Path(dau_kernel.__file__).resolve().parent
TESTS = Path(__file__).resolve().parent

# The specification's trusted base (§3.1): the data model, same_graph, and the
# EGIF parser for the content of an insertion.
TRUSTED = {"egi_core_dau", "eg_navigation", "egif_parser_dau"}
# From eg_navigation the kernel may take same_graph and nothing else.
TRUSTED_NAMES = {"eg_navigation": {"same_graph"}}
OUTSIDE_THE_REPOSITORY = {"__future__", "itertools", "dataclasses", "typing", "frozendict"}

# The modules whose moves the kernel judges. None may be loaded by the kernel,
# directly or through anything it imports.
RULE_ENGINE = {
    "formal_transformation_rules", "rule_interaction", "ligature_manipulation_rules",
    "vertex_splitting_merging_rules", "proof_authoring", "derived_rules", "world_scroll",
}


def import_problems(source: str) -> list:
    """Everything in ``source`` that reaches outside the kernel's permitted
    imports — at any depth, so an import inside a function counts — and every
    way of importing that an ``import`` statement would not show."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in TRUSTED_NAMES:
                    problems.append(f"imports the whole of {top}, not the names it is allowed")
                elif top not in TRUSTED | OUTSIDE_THE_REPOSITORY:
                    problems.append(f"imports {top}")
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                problems.append("a relative import")
                continue
            top = (node.module or "").split(".")[0]
            if top not in TRUSTED | OUTSIDE_THE_REPOSITORY:
                problems.append(f"imports {top}")
            extra = {a.name for a in node.names} - TRUSTED_NAMES.get(top, {a.name for a in node.names})
            if extra:
                problems.append(f"takes {sorted(extra)} from {top}")
        elif isinstance(node, ast.Name) and node.id in ("__import__", "importlib", "exec", "eval"):
            problems.append(f"uses {node.id}")
    return sorted(set(problems))


def test_the_kernel_imports_only_the_trusted_base():
    assert import_problems((SRC / "dau_kernel.py").read_text()) == []


@pytest.mark.parametrize("planted, expected", [
    ("from formal_transformation_rules import ErasureRule\n", "imports formal_transformation_rules"),
    ("def f():\n    import rule_interaction\n", "imports rule_interaction"),
    ("from subgraph_closure_validator import SubgraphClosureValidator\n",
     "imports subgraph_closure_validator"),
    ("import eg_navigation as nav\n", "imports the whole of eg_navigation, not the names it is allowed"),
    ("from eg_navigation import describe\n", "takes ['describe'] from eg_navigation"),
    ("m = __import__('proof_authoring')\n", "uses __import__"),
    ("import importlib\n", "imports importlib"),
    ("from . import sibling\n", "a relative import"),
])
def test_the_import_check_bites(planted, expected):
    """The check above is silent on the kernel. That silence means something
    only if the same check speaks when a forbidden import is planted."""
    clean = (SRC / "dau_kernel.py").read_text()
    assert expected in import_problems(clean + "\n" + planted)


def _local_imports(module: str):
    """The repository modules ``module`` imports: (at module level, inside a function)."""
    local = {p.stem for p in SRC.glob("*.py")}
    tree = ast.parse((SRC / f"{module}.py").read_text())

    def named(node):
        if isinstance(node, ast.Import):
            return {a.name.split(".")[0] for a in node.names}
        if isinstance(node, ast.ImportFrom) and not node.level and node.module:
            return {node.module.split(".")[0]}
        return set()

    everywhere = set().union(*(named(n) for n in ast.walk(tree)))
    at_module_level = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            at_module_level |= set().union(*(named(n) for n in ast.walk(node)))
    return at_module_level & local, (everywhere - at_module_level) & local


def _closure(roots, follow_functions: bool) -> set:
    seen, stack = set(), list(roots)
    while stack:
        module = stack.pop()
        if module in seen:
            continue
        seen.add(module)
        top, inner = _local_imports(module)
        stack.extend(top | inner if follow_functions else top)
    return seen


def test_what_the_trusted_base_loads_is_pinned():
    """The specification names three modules. They are not closed under import,
    and the kernel's soundness argument rests on everything they load.

    Loaded the moment the kernel is imported: ``presentation_ops`` and
    ``layout_dto``, because ``eg_navigation`` imports them at its top.

    Reached by the calls the kernel makes: ``hierarchical_index`` (every graph
    builds one; ``area_polarity`` reads it) and ``graph_isomorphism_engine`` with
    ``canonical_signature`` — ``same_graph`` is that engine's verdict, so it is
    where "the result is a licensed one" is actually decided.

    Reachable from those modules by functions the kernel does not call:
    ``subgraph_closure_validator`` (``eg_navigation``'s closure helper) and
    ``render_geometry`` (``presentation_ops``).

    Pinned exactly, so that a module added to any of them is seen here first.
    Found in Phase 1 and reported to the author; whether the kernel should take
    ``same_graph`` by a shorter road is his ruling, not this test's.
    """
    assert _closure(TRUSTED, follow_functions=False) == TRUSTED | {"presentation_ops", "layout_dto"}
    assert _closure(TRUSTED, follow_functions=True) == TRUSTED | {
        "presentation_ops", "layout_dto", "hierarchical_index", "graph_isomorphism_engine",
        "canonical_signature", "subgraph_closure_validator", "render_geometry",
    }


def test_nothing_the_kernel_loads_is_the_rule_engine():
    """Whatever else the trusted base turns out to load, it may not be a module
    whose moves the kernel judges — at module level or inside any function."""
    assert _closure({"dau_kernel"}, follow_functions=True) & RULE_ENGINE == set()


def test_the_closure_walk_bites():
    """``proof_authoring`` reaches the engine; the walk must say so, or its
    silence about the kernel is worth nothing."""
    assert _closure({"proof_authoring"}, follow_functions=True) & RULE_ENGINE


def test_the_suite_judges_with_the_kernel_and_keeps_no_copy():
    """"The tests import the kernel rather than owning it" (§3.1). A copy left
    behind in ``tests/`` would be judged by the suite while the kernel went
    unexercised, with every count still green."""
    import calculus_layers
    import calculus_run

    assert calculus_run.legal is dau_kernel.legal
    assert calculus_layers.acceptable is dau_kernel.acceptable
    assert calculus_layers.postconditions is dau_kernel.postconditions
    assert calculus_layers.maps_carried is dau_kernel.maps_carried

    owned = {"legal", "acceptable", "postconditions", "expected", "theta", "expand", "tops"}
    copies = []
    for path in sorted(TESTS.glob("*.py")):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.FunctionDef) and node.name in owned:
                copies.append(f"{path.name}:{node.name}")
    assert copies == []


def test_the_rule_table_names_dau_s_rules_and_no_entry_point():
    """The kernel says what Dau's rules are; which code performs each is the
    suite's to say (``calculus_rules.ENGINE``) and is no part of the judge."""
    assert {f.name for f in fields(dau_kernel.Rule)} == {"name", "cite", "direction", "judged"}
    assert {r.name for r in dau_kernel.RULE_TABLE if r.judged} == set(dau_kernel._LEGAL)

    import calculus_rules
    assert [r.name for r in calculus_rules.DAU_RULES] == [r.name for r in dau_kernel.RULE_TABLE]
