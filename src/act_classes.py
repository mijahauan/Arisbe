"""Which kind of act a recorded step is (calculus-conformance specification §3.4).

A recorded history is not one derivation: it holds inferences, and it holds
acts that revise a model by choice. The soundness claim covers the inferences
only, so every recorded act carries a class, and the claim reads: *between any
two ampliative acts, the inferential steps form a derivation in Dau's
calculus, every step checked by the kernel.*

The table is §3.4's, name for name. ``proof_character.py`` holds an older
classification made for a different question (is a proof corollarial or
theorematic?); the two agree except on ``QUOTE``, which is neutral there and an
extension here, and ``tests/test_act_classes.py`` holds that difference in view.

Six names the code can record were in §3.4's table nowhere. The author ruled
them on 2026-11-25 (R10): ``REVISE_M(sibling)`` is ampliative, as ``REVISE_M``
is; ``EXHIBIT`` and ``chain.fix`` are neutral — neither changes the graph;
``definition.fold`` and ``definition.unfold`` are an extension, since
definitions are not in Dau's Beta; and everything under ``compose.`` is a
**sixth class, composition**: regime-1 drafting, before a graph is fixed. A
workshop history is therefore certified from the point its graph is fixed, and
what came before is declared drafting rather than called a revision.
"""
from __future__ import annotations

from dau_kernel import RULE_TABLE

INFERENTIAL_PRIMITIVE = "inferential-primitive"   # one kernel-checked step
INFERENTIAL_DERIVED = "inferential-derived"       # a recorded expansion, every step checked
AMPLIATIVE = "ampliative"                         # a choice; never presented as an inference
NEUTRAL = "neutral"                               # the logical content is unchanged
EXTENSION = "extension"                           # outside Dau's Beta; its own argument (§6)
COMPOSITION = "composition"                       # drafting, before the graph is fixed

_PRIMITIVE = {r.name for r in RULE_TABLE} | {"HEAVY_DOT"}     # HEAVY_DOT: the engine's VERTEX_INS
_DERIVED = {"UI", "DISCHARGE_TO_M", "ABANDON_EPISODE", "ENTERTAIN"}
_AMPLIATIVE = {"REVISE_M", "ADMIT_FACT", "SCRIBE_AXIOM", "SCRIBE_LAW", "FOLD_NUMERAL",
               "ADMIT_TO_M", "RETRACT_FROM_M", "DECAY", "BANK_TO_M", "PROPOSE",
               "REVISE_M(sibling)"}
_NEUTRAL = {"PEEL", "TRACE_ALTERNATIVES", "SURVEY_THIN_SPOTS", "SURVEY_BRANCHES",
            "EXHIBIT", "chain.fix"}
_EXTENSION = {"QUOTE", "definition.fold", "definition.unfold"}

# Every regime-1 composition step is named under this prefix.
COMPOSITION_PREFIXES = ("compose.",)

ACT_CLASSES = {
    **{name: INFERENTIAL_PRIMITIVE for name in _PRIMITIVE},
    **{name: INFERENTIAL_DERIVED for name in _DERIVED},
    **{name: AMPLIATIVE for name in _AMPLIATIVE},
    **{name: NEUTRAL for name in _NEUTRAL},
    **{name: EXTENSION for name in _EXTENSION},
}


def act_class(rule_name: str) -> str:
    """The §3.4 class of a recorded act, by its rule name. ``KeyError`` for a
    name nothing here knows — a new kind of act must be classed before it can
    be recorded unnoticed."""
    if rule_name in ACT_CLASSES:
        return ACT_CLASSES[rule_name]
    if rule_name.startswith(COMPOSITION_PREFIXES):
        return COMPOSITION
    raise KeyError(f"no class is recorded for the act {rule_name!r}")
