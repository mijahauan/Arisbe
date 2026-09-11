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
