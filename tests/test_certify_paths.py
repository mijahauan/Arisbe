"""Nothing reaches the rule engine except through ``calculus_certify``.

The specification's §3.3: "a test asserts that no engine entry point is
reachable from a route or a UoD writer except through it." The Phase 0 map
(§3.3a) found five ways in and ten call sites; each now calls a door of
``calculus_certify``, and this file fails if a new one goes round.

It reads calls, not imports. A module may still hold a rule object, or walk the
protocol's validation steps — neither changes a graph. What it may not do is
call one of the functions that does.
"""
import ast
from pathlib import Path

import pytest

import calculus_certify
from calculus_certify import OBSERVED
from dau_kernel import ACCEPTED, REJECTED
from egif_parser_dau import parse_egif

ROOT = Path(__file__).resolve().parent.parent

# The four modules where a rule's transformation is performed (§3.3a), and the door.
ENGINE = {"formal_transformation_rules.py", "rule_interaction.py",
          "ligature_manipulation_rules.py", "vertex_splitting_merging_rules.py"}
DOOR = "calculus_certify.py"

# Functions and methods that perform a rule. ``apply_rule`` and ``apply`` are
# common names, so those two are matched by what they are called on.
ENTRY_POINTS = {"apply_interaction", "apply_transformation", "insert_from_egif",
                "_apply_vertex_merge", "_apply_vertex_split", "merge_vertices"}

# Callers that go round the door, each with the reason it is let stand.
EXEMPT = {
    "src/chapter17_soundness_evaluation.py":
        "an evaluator no module in src/ imports but z3_semantic_validator",
    "src/z3_semantic_validator.py":
        "an evaluator no module in src/ imports but chapter17_soundness_evaluation",
    "tools/demo_proof_serializer.py":
        "a demonstration script; it writes no universe of discourse",
}


def direct_engine_calls(source: str) -> list:
    """The line numbers and names of every call in ``source`` that performs a rule."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in ENTRY_POINTS:
            found.append((node.lineno, func.id))
        elif isinstance(func, ast.Attribute):
            receiver = ast.unparse(func.value)
            if func.attr in ENTRY_POINTS:
                found.append((node.lineno, f"{receiver}.{func.attr}"))
            elif func.attr == "apply_rule" and "ngine" in receiver:
                found.append((node.lineno, f"{receiver}.apply_rule"))      # an engine object
            elif func.attr == "apply" and "nteraction" in receiver:
                found.append((node.lineno, f"{receiver}.apply"))           # a RuleInteraction
    return sorted(found)


def _sources():
    for folder in ("src", "tools"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            if path.name in ENGINE or path.name == DOOR:
                continue
            try:
                source = path.read_text()
                ast.parse(source)
            except SyntaxError:
                continue
            yield str(path.relative_to(ROOT)), source


def test_no_module_reaches_the_engine_except_through_the_door():
    offenders = {name: calls for name, source in _sources()
                 if (calls := direct_engine_calls(source)) and name not in EXEMPT}
    assert offenders == {}


def test_every_exemption_is_still_needed_and_still_true():
    reaching = {name for name, source in _sources() if direct_engine_calls(source)}
    assert reaching == set(EXEMPT), "an exemption with nothing to exempt, or a caller with none"
    # The two evaluators are exempt because nothing in production imports them.
    evaluators = {"chapter17_soundness_evaluation", "z3_semantic_validator"}
    importers = set()
    for name, source in _sources():
        if Path(name).stem in evaluators:
            continue
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in evaluators:
                importers.add(name)
            elif isinstance(node, ast.Import) and \
                    any(a.name.split(".")[0] in evaluators for a in node.names):
                importers.add(name)
    assert importers == set()


@pytest.mark.parametrize("planted, expected", [
    ("r = apply_interaction(state)\n", "apply_interaction"),
    ("r = rule.apply_transformation(context)\n", "rule.apply_transformation"),
    ("r = insert_from_egif(g, area, text)\n", "insert_from_egif"),
    ("g = VertexMergingRule()._apply_vertex_merge(g, v1_id=a, v2_id=b, identity_edge_id=e)\n",
     "VertexMergingRule()._apply_vertex_merge"),
    ("g = VertexSplittingRule()._apply_vertex_split(g, spec)\n",
     "VertexSplittingRule()._apply_vertex_split"),
    ("r = FormalTransformationEngine().apply_rule('ERA', g, a, s)\n",
     "FormalTransformationEngine().apply_rule"),
    ("r = _engine.apply_rule('ERA', g, a, s)\n", "_engine.apply_rule"),
    ("r = LigatureManipulationEngine().apply_rule('MOVE_BRANCHES', g, a, s)\n",
     "LigatureManipulationEngine().apply_rule"),
    ("r = interaction.apply(state)\n", "interaction.apply"),
])
def test_the_scan_bites(planted, expected):
    assert [name for _line, name in direct_engine_calls(planted)] == [expected]


def test_the_scan_leaves_the_doors_own_callers_alone():
    """``proof_authoring.apply_rule`` is the door's own caller, and ``ProofChain.apply``
    records a step. Neither is an engine entry point."""
    harmless = ("g = apply_rule('ERA', g, selection=[e])\n"
                "chain = chain.apply('DC+', select=pick)\n"
                "r = mcp_verifier.apply_rule(text, 'ERA')\n"
                "state = begin_interaction('ERA', g)\n"
                "r = advance_interaction(state, [e])\n")
    assert direct_engine_calls(harmless) == []


# -- each way in is observed -------------------------------------------------

def _count(way, status=None):
    return sum(n for (w, _rule, _dau, s), n in OBSERVED.counts.items()
               if w == way and (status is None or s == status))


def test_the_engine_called_directly_is_observed():
    """``POST /api/transform/apply`` reaches the rules this way (§3.3a, way 2)."""
    g = parse_egif("(P *x)")
    edge = next(iter(g.nu))
    before = _count("engine")
    result, cert = calculus_certify.engine_apply("DC+", g, g.sheet, frozenset({edge}))
    assert result.success and cert is not None and _count("engine") == before + 1


def test_an_empty_double_cut_request_means_two_things_by_two_ways_in():
    """Through the protocol, DC+ of nothing at a spot is an empty double cut
    there. Through the engine it is a double cut around everything in that
    area. Each is certified as the move it is — and they are not one move."""
    g = parse_egif("(P *x)")
    by_protocol, cert = calculus_certify.certify(
        g, calculus_certify.Act("protocol", "DC+", (), g.sheet))
    assert cert.status == ACCEPTED and cert.steps[0].selection == ()
    result, cert = calculus_certify.engine_apply("DC+", g, g.sheet, frozenset())
    assert cert.status == ACCEPTED and set(cert.steps[0].selection) == set(g.area[g.sheet])
    assert not calculus_certify.dau_kernel.same_graph(by_protocol, result.result_egi)


def test_the_two_web_routes_disagree_and_the_certificates_say_so():
    """Finding 1 of the map, now measured through the door. On
    ``(P *x) ~[ (Q *y) ]``, DC+ of the P edge with the cut as its spot: the
    protocol applies it (ignoring the spot) and the kernel rejects the result;
    the engine called directly refuses it."""
    g = parse_egif("(P *x) ~[ (Q *y) ]")
    p_edge = next(e for e in g.nu if g.rel[e] == "P")
    cut = next(c.id for c in g.Cut)
    _h, cert = calculus_certify.certify(g, calculus_certify.Act("protocol", "DC+", (p_edge,), cut))
    assert cert.status == REJECTED
    result, cert = calculus_certify.engine_apply("DC+", g, cut, frozenset({p_edge}))
    assert not result.success and cert is None


def test_the_game_engine_s_way_in_is_observed():
    """A rule object handed a context, with no protocol and no engine between
    (§3.3a, way 3), and INS by ``insert_from_egif``."""
    import endoporeutic_game
    from formal_transformation_rules import DoubleCutInsertionRule, TransformationContext

    game_source = Path(endoporeutic_game.__file__).read_text()
    assert "rule_apply(rule_name, rule, context)" in game_source
    assert "insert_apply(state.current_egi, target_area, insert_egif)" in game_source

    g = parse_egif("(P *x)")
    edge = next(iter(g.nu))
    polarity, depth = g.area_polarity(g.sheet)
    context = TransformationContext(source_egi=g, target_area=g.sheet,
                                    selected_subgraph=frozenset({edge}),
                                    area_polarity=polarity, nesting_depth=depth)
    before = _count("rule")
    result, cert = calculus_certify.rule_apply("DC+", DoubleCutInsertionRule(), context)
    assert result.success and cert.status == ACCEPTED and _count("rule") == before + 1

    h = parse_egif("~[ (P *x) ]")
    cut = next(c.id for c in h.Cut)
    result, cert = calculus_certify.insert_apply(h, cut, "(Q *z)")
    assert result.success and cert.status == ACCEPTED and _count("rule") == before + 2


def test_the_workshop_s_dry_run_is_tallied_apart_and_never_raises(monkeypatch):
    from rule_interaction import advance_interaction, begin_interaction

    g = parse_egif("(P *x)")
    edge = next(iter(g.nu))
    state = begin_interaction("ERA", g)
    advance_interaction(state, [edge])
    monkeypatch.setattr(calculus_certify, "MODE", "enforce")
    before = _count("protocol:dry-run")
    result, cert = calculus_certify.protocol_apply(state, selection=[edge], dry_run=True)
    assert result.success and cert.status == REJECTED          # reported, not raised
    assert _count("protocol:dry-run") == before + 1


def test_production_s_unchecked_merge_and_split_are_observed():
    """Finding 5 of the map: production merges and splits by the operations that
    check nothing. They now come through the door, so the kernel sees each one."""
    import derived_rules

    source = Path(derived_rules.__file__).read_text()
    assert "merge_unchecked(" in source and "split_unchecked(" in source
    import world_scroll
    assert "merge_unchecked(" in Path(world_scroll.__file__).read_text()

    g = parse_egif('(bird "Rex")')
    before = _count("merge-unchecked")
    resident, _scroll = world_scroll.wrap_m(g)
    world_scroll.enlarge_m(resident, '(white "Rex")')
    assert _count("merge-unchecked") == before + 1
