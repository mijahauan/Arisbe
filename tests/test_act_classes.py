"""Every recorded act has a class (calculus-conformance specification §3.4).

The soundness claim is about inferences, and a recorded history also holds
choices. So the claim is only as good as the table that tells them apart — and
a table is only kept if something fails when a new kind of act appears without
being classed.
"""
import ast
import json
from collections import Counter
from pathlib import Path

import pytest

import proof_character
from act_classes import (
    ACT_CLASSES, AMPLIATIVE, COMPOSITION, EXTENSION, INFERENTIAL_DERIVED,
    INFERENTIAL_PRIMITIVE, NEUTRAL, act_class,
)
from dau_kernel import RULE_TABLE

ROOT = Path(__file__).resolve().parent.parent


def _corpus_steps():
    for path in sorted((ROOT / "tomos").rglob("chain.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                params = record.get("parameters", record)
                if params.get("rule") is not None:
                    yield path, params


def test_every_step_the_corpus_records_has_a_class_and_the_counts_are_pinned():
    """35 chains, 146 steps. Generated from ``tomos/**/chain.jsonl``."""
    steps = list(_corpus_steps())
    assert len({path for path, _ in steps}) == 35
    assert Counter(act_class(params["rule"]) for _, params in steps) == {
        INFERENTIAL_PRIMITIVE: 66, AMPLIATIVE: 35, NEUTRAL: 34, INFERENTIAL_DERIVED: 6,
        EXTENSION: 5,
    }


def test_no_derived_inference_in_the_corpus_carries_an_expansion_that_can_be_checked():
    """§3.4: "Opaque derived steps are not admitted to a certified history."
    Today all six are opaque to the kernel. Four UI steps record no expansion;
    ENTERTAIN and DISCHARGE_TO_M each record a list of rule *names*, with no
    selection or target, which cannot be re-applied. Pinned as it stands: the
    legacy expansion of Phase 4 is what changes it."""
    derived = Counter()
    for _path, params in _corpus_steps():
        if act_class(params["rule"]) == INFERENTIAL_DERIVED:
            expansion = params.get("derivation")
            if not expansion:
                shape = "none"
            elif all(isinstance(step, str) for step in expansion):
                shape = "rule names only"
            else:
                shape = "steps"
            derived[(params["rule"], shape)] += 1
    assert derived == {("UI", "none"): 4, ("ENTERTAIN", "rule names only"): 1,
                       ("DISCHARGE_TO_M", "rule names only"): 1}


def _recordable_names():
    """The first argument of every ``apply_derived`` call in ``src/`` and
    ``tools/``: a string, or a name bound to a string at the top of its module."""
    found = {}
    for path in sorted(list((ROOT / "src").rglob("*.py")) + list((ROOT / "tools").rglob("*.py"))):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue          # a tool that does not parse cannot record anything
        constants = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        constants[target.id] = node.value.value
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    constants.setdefault(alias.asname or alias.name, None)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "apply_derived" and node.args:
                first = node.args[0]
                where = f"{path.relative_to(ROOT)}:{node.lineno}"
                if isinstance(first, ast.Constant):
                    found[where] = first.value
                elif isinstance(first, ast.Name):
                    found[where] = constants.get(first.id) or first.id
                else:
                    found[where] = None           # a computed name: reported below
    return found


def test_every_name_the_code_can_record_has_a_class():
    names = _recordable_names()
    assert len(names) >= 20, "the scan found too few apply_derived calls to mean anything"
    computed = sorted(where for where, name in names.items() if name is None)
    # `ProofChain.apply_derived` itself forwards a caller's name; nothing else computes one.
    assert computed == [], f"an act is recorded under a computed name: {computed}"
    unclassed = {}
    for where, name in names.items():
        try:
            act_class(name)
        except KeyError:
            unclassed[where] = name
    assert unclassed == {}


def test_a_name_nothing_knows_is_refused():
    with pytest.raises(KeyError):
        act_class("SOME_NEW_ACT")


def test_the_six_names_the_author_ruled_on_2026_11_25():
    """R10. They were recordable and in §3.4's table nowhere, and were held as
    unruled until the author classed them. Pinned as ruled."""
    assert act_class("REVISE_M(sibling)") == AMPLIATIVE == act_class("REVISE_M")
    assert act_class("EXHIBIT") == NEUTRAL
    assert act_class("chain.fix") == NEUTRAL
    assert act_class("definition.fold") == act_class("definition.unfold") == EXTENSION
    # Composition is a class of its own and a prefix, not a list of names.
    assert act_class("compose.fix_graph") == act_class("compose.add_cut") == COMPOSITION
    assert COMPOSITION not in set(ACT_CLASSES.values())


def test_the_gate_step_that_fixes_a_graph_is_composition_and_the_seal_is_neutral():
    """The two fixings (``composition_ops``): ``compose.fix_graph`` ends the
    drafting and is the last composition step; ``chain.fix`` seals a chain and
    changes nothing. A workshop history is certified from the first onward."""
    import composition_ops

    assert act_class(composition_ops.FIX_GRAPH_STEP) == COMPOSITION
    assert act_class(composition_ops.FIX_CHAIN_STEP) == NEUTRAL
    assert composition_ops.FIX_GRAPH_STEP.startswith(composition_ops.COMPOSE_STEP_PREFIX)


def test_the_six_rules_and_every_other_dau_rule_are_primitives():
    assert all(act_class(rule.name) == INFERENTIAL_PRIMITIVE for rule in RULE_TABLE)
    assert act_class("HEAVY_DOT") == INFERENTIAL_PRIMITIVE


def test_where_this_table_and_proof_character_disagree():
    """One name, and it is the specification's doing: ``QUOTE`` is neutral in
    ``proof_character`` and an extension in §3.4 (ruling R6). Everything else
    the older module classes, this table classes compatibly."""
    assert {n for n in proof_character.AMPLIATIVE_RULES if act_class(n) != AMPLIATIVE} == set()
    assert {n for n in proof_character.NEUTRAL_RULES if act_class(n) != NEUTRAL} == {"QUOTE"}
    assert act_class("QUOTE") == EXTENSION
    derived = proof_character.THEOREMATIC_RULES | proof_character.TRANSPARENT_DERIVED
    assert {n for n in derived if act_class(n) != INFERENTIAL_DERIVED} == set()
    primitive = proof_character.CONTENT_ADDING | proof_character.CONTENT_PRESERVING
    assert {n for n in primitive if act_class(n) != INFERENTIAL_PRIMITIVE} == set()
