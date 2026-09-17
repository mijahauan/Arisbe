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


# The core's refusal to construct a non-EGI (egi_core_dau._validate_dau_constraints,
# Dau Def 12.5 p.125). The engines catch the ValueError and pass its message on,
# so it is recognised by that message however it arrives. It is read as its own
# kind of refusal — never folded into the engine's refusals, never a crash — so
# the moves it stops stay counted under a label of their own.
CORE_NON_EGI = "Dominating nodes violated (Def 12.5)"


@dataclass(frozen=True)
class Outcome:
    applied: bool
    result: Optional[G]
    message: str
    crashed: bool = False
    core_refused_non_egi: bool = False


def engine_entry_points() -> FrozenSet[str]:
    pts = {f"protocol:{k}" for k in RULE_INTERACTIONS}
    pts |= {f"engine:{k}" for k in FormalTransformationEngine().rules if k not in RULE_INTERACTIONS}
    pts |= {f"ligature:{k}" for k in LigatureManipulationEngine().rules}
    pts |= {"split", "merge"}   # two classes, no registry (checked in the tests)
    return frozenset(pts)


def apply_move(g: G, m: Move) -> Outcome:
    out = _apply_move(g, m)
    if not out.applied and CORE_NON_EGI in out.message:
        return Outcome(False, None, out.message, core_refused_non_egi=True)
    return out


def _apply_move(g: G, m: Move) -> Outcome:
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
            # A plain frozenset: the engine's choice of vertex within the
            # selection is a function of the graph (canonical signature), so
            # the suite no longer has to hand an order over to make a run
            # deterministic (Task 7 retired calculus_apply.InOrder).
            r = LigatureManipulationEngine().apply_rule(
                engine.split(":", 1)[1], g, m.target, frozenset(m.selection))
            return Outcome(bool(r.success), r.result_egi if r.success else None, r.error_message or "")
        if engine == "split":
            spec = VertexSplitSpec(source_vertex=m.selection[0], target_context=m.target,
                                   hooks_to_move=list(m.hooks), new_vertex_id="split_new_v")
            return Outcome(True, VertexSplittingRule()._apply_vertex_split(g, spec), "")
        if engine == "merge":
            # Def 16.6 merging names v1 and v2 in order (v2 into v1), which a
            # frozenset selection cannot carry, so this is the rule's ordered
            # entry point rather than apply_transformation. It checks the rule's
            # own preconditions: _apply_vertex_merge, the private operation the
            # suite used to call, performs the merge and checks nothing.
            v1, v2, e = m.selection
            r = VertexMergingRule().merge_vertices(g, v1_id=v1, v2_id=v2, identity_edge_id=e)
            return Outcome(bool(r.success), r.result_egi if r.success else None, r.error_message or "")
    except AssertionError as exc:          # the protocol's own rejection
        return Outcome(False, None, str(exc))
    except Exception as exc:               # anything else is a crash
        return Outcome(False, None, f"{type(exc).__name__}: {exc}", crashed=True)
    raise KeyError(f"{m.rule} has no engine entry point")
