"""**Corollarial or theorematic?** — Peirce's distinction, decided from the chain.

Peirce divided necessary reasoning in two, and thought the division his deepest
find in logic (Hintikka 1980 calls it "Peirce's first real discovery"):

* **Corollarial** reasoning "consists merely in carefully taking account of the
  definitions of the terms occurring in the thesis to be proved" (NE IV, 8). You
  construct the diagram the hypothesis prescribes, and read the conclusion off
  it. Nothing enters that the premisses did not already contain.
* **Theorematic** reasoning "requires the invention of an idea not at all forced
  upon us by the terms of the thesis" (ibid.). Euclid I.32 is the type case: to
  prove the angle sum you must *draw an auxiliary line* — a construction the
  statement never mentions. Peirce's own theorem that no multitude is greatest is
  his favourite example.

The distinction has been argued about philosophically for a century because it
was never given a mechanical criterion. In Dau's calculus it has one, and it is
sharp:

    A derivation is COROLLARIAL iff it uses only the rules that *cannot add
    content* — erasure, iteration, deiteration, and the double-cut pair.
    It is THEOREMATIC iff it needs INSERTION: the one rule that scribes a
    subgraph the premisses do not contain.

That is not an analogy. Insertion (sound only in a negative context) is precisely
"scribe something the thesis did not force upon you," and every other rule merely
*rearranges, copies, or deletes* what is already there. The auxiliary line and the
insertion step are the same act.

Arisbe records every rule application in a ``TransformationChain``, so the
character of a proof is a **computed property of an attested artifact**, not a
matter of interpretation: :func:`character_of` reads the chain and says which it
is, and names the exact steps that made it theorematic.

Two honest limits, kept in the report rather than hidden:

* The verdict is about the derivation *as recorded*, not about the theorem. A
  theorem may have a theorematic proof and a corollarial one; finding the latter
  is exactly what a mathematician does when she "finds a better proof." So a
  CHARACTER is a property of a path, and ``theorematic`` means *this* path needed
  an idea from outside. (Peirce would say the same: he speaks of theorematic
  *proofs*, not theorematic truths.)
* A **derived** step (``apply_derived``, e.g. a Beta scaffold) is opaque here: it
  collapses several primitive moves into one chain step. If its expansion
  contains an insertion, the proof is theorematic and this reader cannot see it.
  Such steps are reported in ``opaque_steps`` and make the verdict PROVISIONAL —
  never silently corollarial.

Pure, deterministic, geometry-free: it reads rule names off the chain and nothing
else. See docs/MATHEMATICS_FROM_THE_SHEET.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

# The six rules, split by the only question that matters here: can it put on the
# sheet something that was not already there?
#
#   ERA  erasure           — removes (positive context)
#   IT+  iteration         — copies what is already scribed
#   IT-  deiteration       — removes a copy
#   DC+  double-cut insert — adds a logically inert double cut, no content
#   DC-  double-cut erase  — removes one
#   INS  insertion         — *scribes new content* (negative context). The one
#                            rule that can introduce an idea the premisses do not
#                            contain. Peirce's auxiliary line.
CONTENT_ADDING = frozenset({"INS"})
CONTENT_PRESERVING = frozenset({"ERA", "IT+", "IT-", "DC+", "DC-"})

# Peirce divides reasoning THREE ways — deduction, induction, abduction — and only
# deduction splits into corollarial and theorematic. A step that revises the model
# (admit a fact, induce a law, relinquish a refuted one) is neither: it is
# **ampliative**, adding content no rule of inference compels. Calling such a chain
# "corollarial" would be a category error, so it gets its own verdict.
AMPLIATIVE_RULES = frozenset({
    "REVISE_M", "ADMIT_FACT", "SCRIBE_AXIOM", "SCRIBE_LAW", "FOLD_NUMERAL",
    # the world-scroll vocabulary (M resident in cells at even depth,
    # world_scroll.py): enlargement is a genuine INS-of-cell and retraction a
    # genuine ERA-in-cell, but *choosing* which content M carries is still
    # ampliative — no inference compelled the admission or the retraction
    # (the licence makes the move sound, not obligatory).
    "ADMIT_TO_M", "RETRACT_FROM_M",
    # the live loop's recorded acts (agon_evolution): a disposition injection
    # or a disuse-decay erasure changes M by a choice/economy, not an inference.
    "DECAY",
})

# A recorded observation that changes nothing — the peel's verdict scribed as
# an act (identity transform). Neither content-adding nor a hidden expansion:
# skipping it keeps a corollarial chain corollarial and an ampliative one
# honest about WHICH steps did the amplifying. QUOTE (B-min) joins it: a
# quotation exhibits its ink without force — a mention asserts nothing, so
# scribing one is an act, not an inference.
NEUTRAL_RULES = frozenset({"PEEL", "QUOTE"})

# Derived episode steps whose expansions ARE visible (M_RESIDENCE §10, the
# episode lifecycle in ink — each records its executed derivation):
# ENTERTAIN scribes the candidate into the exhibit (its recorded expansion
# contains the INS) — Peirce's auxiliary line, so it counts as an insertion
# and a discharged chain reads THEOREMATIC, exactly right for "experiment
# upon the diagram". DISCHARGE_TO_M (IT-·IT-·DC-) and ABANDON_EPISODE (ERA)
# expand to content-preserving moves only — transparent, never opaque.
THEOREMATIC_RULES = frozenset({"ENTERTAIN"})
TRANSPARENT_DERIVED = frozenset({"DISCHARGE_TO_M", "ABANDON_EPISODE"})

COROLLARIAL = "corollarial"
THEOREMATIC = "theorematic"
AMPLIATIVE = "ampliative"


@dataclass
class ProofCharacter:
    """The character of one derivation, with its evidence.

    ``character`` is :data:`COROLLARIAL` or :data:`THEOREMATIC`. ``insertions``
    names the steps that introduced content (empty iff corollarial).
    ``opaque_steps`` names derived/collapsed steps whose primitive expansion this
    reader cannot see; while any exist the verdict is ``provisional`` — a
    corollarial reading is not yet earned.
    """

    character: str
    insertions: List[str] = field(default_factory=list)
    opaque_steps: List[str] = field(default_factory=list)
    ampliative_steps: List[str] = field(default_factory=list)
    steps: int = 0

    @property
    def provisional(self) -> bool:
        """True when a derived step hides primitive moves we could not inspect.
        A THEOREMATIC verdict is never provisional (an insertion we *did* see is
        proof enough); only a corollarial reading can be undermined."""
        return bool(self.opaque_steps) and self.character == COROLLARIAL

    @property
    def summary(self) -> str:
        if self.character == AMPLIATIVE:
            n = len(self.ampliative_steps)
            core = (f", around a deductive core of {self.steps - n} step(s)"
                    if self.steps > n else "")
            return (f"ampliative — {n} of {self.steps} step(s) REVISE the model{core}. "
                    f"No rule of inference compels a revision: this is induction or "
                    f"abduction, not deduction, and it is not 'a proof' at all.")
        if self.character == THEOREMATIC:
            return (f"theorematic — {len(self.insertions)} insertion(s) in "
                    f"{self.steps} step(s): the proof had to scribe something the "
                    f"thesis did not contain (Peirce's auxiliary line).")
        if self.provisional:
            return (f"corollarial so far, PROVISIONALLY — {len(self.opaque_steps)} "
                    f"derived step(s) collapse primitive moves this reader cannot "
                    f"see; an insertion could be hiding inside one.")
        return (f"corollarial — {self.steps} step(s), no insertion: the conclusion "
                f"was read off what the definitions already contained.")


def _rule_of(step) -> str:
    return (getattr(step, "rule_name", "") or "").strip()


def _is_derived(step) -> bool:
    params = getattr(step, "parameters", None) or {}
    return bool(params.get("derived"))


def character_of(steps: Sequence) -> ProofCharacter:
    """Decide whether a derivation is corollarial or theorematic.

    ``steps`` is a sequence of ``ChainStep``s (``chain.steps``). The rule is the
    module's whole thesis: an **insertion** is the auxiliary line, and nothing
    else can introduce an idea the premisses do not force."""
    insertions: List[str] = []
    opaque: List[str] = []
    ampliative: List[str] = []
    for s in steps:
        rule = _rule_of(s)
        sid = getattr(s, "step_id", rule or "?")
        if rule in NEUTRAL_RULES:
            # A verdict record (PEEL): an act, not an inference — no content.
            continue
        if rule in AMPLIATIVE_RULES:
            # Not deduction at all — the model was CHANGED, not unfolded.
            ampliative.append(sid)
        elif rule in THEOREMATIC_RULES or rule in CONTENT_ADDING:
            insertions.append(sid)
        elif rule in TRANSPARENT_DERIVED:
            # A derived step whose recorded expansion is wholly
            # content-preserving (IT-/DC-/ERA) — visible, never opaque.
            continue
        elif rule not in CONTENT_PRESERVING or _is_derived(s):
            # A derived/composite step (or an unknown rule) may expand into
            # primitives we cannot see — including an insertion. Never assume.
            opaque.append(sid)

    if ampliative:
        character = AMPLIATIVE          # a revised model is not a proof
    elif insertions:
        character = THEOREMATIC
    else:
        character = COROLLARIAL
    return ProofCharacter(
        character=character,
        insertions=insertions,
        opaque_steps=opaque,
        ampliative_steps=ampliative,
        steps=len(list(steps)),
    )


def character_of_chain(chain) -> ProofCharacter:
    """:func:`character_of` over a ``TransformationChain``."""
    return character_of(getattr(chain, "steps", []) or [])


__all__ = [
    "ProofCharacter", "character_of", "character_of_chain",
    "COROLLARIAL", "THEOREMATIC", "AMPLIATIVE",
    "CONTENT_ADDING", "CONTENT_PRESERVING", "AMPLIATIVE_RULES", "NEUTRAL_RULES",
    "THEOREMATIC_RULES", "TRANSPARENT_DERIVED",
]
