"""Which kind of act a recorded step is (calculus-conformance specification §3.4).

A recorded history is not one derivation: it holds inferences, and it holds
acts that revise a model by choice. The soundness claim covers the inferences
only, so every recorded act carries one of five classes, and the claim reads:
*between any two ampliative acts, the inferential steps form a derivation in
Dau's calculus, every step checked by the kernel.*

The table is §3.4's, name for name. ``proof_character.py`` holds an older
classification made for a different question (is a proof corollarial or
theorematic?); the two agree except on ``QUOTE``, which is neutral there and an
extension here, and ``tests/test_act_classes.py`` holds that difference in view.

Six names the code can record are in §3.4's table nowhere. They are listed in
``UNRULED`` rather than guessed at: classing an act decides whether a history
containing it can be certified, and that is the author's to rule.
"""
from __future__ import annotations

from dau_kernel import RULE_TABLE

INFERENTIAL_PRIMITIVE = "inferential-primitive"   # one kernel-checked step
INFERENTIAL_DERIVED = "inferential-derived"       # a recorded expansion, every step checked
AMPLIATIVE = "ampliative"                         # a choice; never presented as an inference
NEUTRAL = "neutral"                               # the logical content is unchanged
EXTENSION = "extension"                           # outside Dau's Beta; its own argument (§6)
UNRULED_CLASS = "unruled"                         # recordable, and §3.4 does not class it

_PRIMITIVE = {r.name for r in RULE_TABLE} | {"HEAVY_DOT"}     # HEAVY_DOT: the engine's VERTEX_INS
_DERIVED = {"UI", "DISCHARGE_TO_M", "ABANDON_EPISODE", "ENTERTAIN"}
_AMPLIATIVE = {"REVISE_M", "ADMIT_FACT", "SCRIBE_AXIOM", "SCRIBE_LAW", "FOLD_NUMERAL",
               "ADMIT_TO_M", "RETRACT_FROM_M", "DECAY", "BANK_TO_M", "PROPOSE"}
_NEUTRAL = {"PEEL", "TRACE_ALTERNATIVES", "SURVEY_THIN_SPOTS", "SURVEY_BRANCHES"}
_EXTENSION = {"QUOTE"}

# Recordable, unclassed by §3.4. ``compose.`` is a prefix: every regime-1
# composition step is named under it.
UNRULED = frozenset({"EXHIBIT", "REVISE_M(sibling)", "definition.fold", "definition.unfold",
                     "chain.fix"})
UNRULED_PREFIXES = ("compose.",)

ACT_CLASSES = {
    **{name: INFERENTIAL_PRIMITIVE for name in _PRIMITIVE},
    **{name: INFERENTIAL_DERIVED for name in _DERIVED},
    **{name: AMPLIATIVE for name in _AMPLIATIVE},
    **{name: NEUTRAL for name in _NEUTRAL},
    **{name: EXTENSION for name in _EXTENSION},
}


def act_class(rule_name: str) -> str:
    """The §3.4 class of a recorded act, by its rule name. ``UNRULED_CLASS`` for
    the names §3.4 leaves out; ``KeyError`` for a name nothing here knows — a new
    kind of act must be classed before it can be recorded unnoticed."""
    if rule_name in ACT_CLASSES:
        return ACT_CLASSES[rule_name]
    if rule_name in UNRULED or rule_name.startswith(UNRULED_PREFIXES):
        return UNRULED_CLASS
    raise KeyError(f"no class is recorded for the act {rule_name!r}")
