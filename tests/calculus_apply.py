"""How each Dau rule reaches the engine (spec 2026-09-10 §1a.2).

A refusal is the engine's own rejection; any other exception is a crash, and
a crash is a defect. Every application goes through ``calculus_certify.certify``,
so the suite measures the engine by the same door production uses. Kept apart from the kernel (``src/dau_kernel.py``, where
legal() lives) and from calculus_rules, so neither shares a module with the
engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional

from calculus_certify import Act, Certificate, certify
from calculus_rules import RULES
from dau_kernel import Move
from egi_core_dau import RelationalGraphWithCuts
from formal_transformation_rules import FormalTransformationEngine
from ligature_manipulation_rules import LigatureManipulationEngine
from rule_interaction import RULE_INTERACTIONS

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
    certificate: Optional[Certificate] = None    # the kernel's check of an applied move


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


# Each engine entry point the rule table names, as the way into the engine that
# ``calculus_certify`` knows it by, and the rule's name on that way.
def _act(m: Move) -> Act:
    engine = RULES[m.rule].engine
    if engine in ("split", "merge"):
        way, rule = ("split-unchecked", "SPLIT_VERTEX") if engine == "split" \
            else ("merge-checked", "MERGE_VERTICES")
    else:
        way, rule = engine.split(":", 1)
    return Act(way, rule, tuple(m.selection), m.target, m.content, tuple(m.hooks), dau_rule=m.rule)


def _apply_move(g: G, m: Move) -> Outcome:
    """Through ``certify`` — the one door to the engine since 2026-11-25. The
    suite names the Dau rule it means (``dau_rule``), so the certificate judges
    the engine's result under the same rule the ledger's entries are keyed by."""
    if RULES[m.rule].engine is None:
        raise KeyError(f"{m.rule} has no engine entry point")
    try:
        result, certificate = certify(g, _act(m))
        return Outcome(True, result, "", certificate=certificate)
    except AssertionError as exc:          # the engine's own rejection, by any way in
        return Outcome(False, None, str(exc))
    except Exception as exc:               # anything else is a crash
        return Outcome(False, None, f"{type(exc).__name__}: {exc}", crashed=True)
