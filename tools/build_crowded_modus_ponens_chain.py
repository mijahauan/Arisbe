"""Build **crowded modus ponens** — the corpus's first *super-budget* worked
chain, authored to exercise the spatial in-view rules (S1/S2) of
``docs/THE_MINIMAL_IN_VIEW_SET.md`` in the diagram↔narration harness.

Every other narrated chain in the corpus is sub-budget (≤7 visible chunks), so
the overview/collapse metrics degenerate.  This one puts the inference in a
*crowd*: the fact ``(A)`` and the matching rule ``A⊃B`` sit on a sheet beside
**ten unrelated rules** ``Dk⊃Ek`` — twelve sibling chunks, well over the budget.
The proof then performs ordinary modus ponens on the *one* relevant rule:

    1. IT-  deiterate the inner (A) inside the matching rule — a copy of the
            asserted fact (A) on the sheet — leaving the double cut ~[ ~[ (B) ] ]
    2. DC-  erase that double cut, landing (B) on the sheet

The narration legitimately *ignores the ten distractors* — it names only the
fact and the matching rule.  That is the point: an expert keeps the narration
inside a bounded focus-neighborhood (S1), so a focus-centered overview that
collapses the far siblings should leave every narrated item visible.  The
harness's spatial metric (in-view coverage) becomes *live* here, and a doctored
narration that "recalls" a collapsed distractor falsifies it.

An authored *demonstration* (modus ponens is not a new theorem), low warrant,
method-only provenance — every step a real, attestable Dau-rule application.
Import-safe; run as a script to seed the corpus.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import SCOPE_CHAIN, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from provenance import KIND_PROOF, authored_proof, make_provenance
from tomos_service import TransformationChain
from universe_of_discourse import UniverseOfDiscourse

UOD_ID = "crowded_modus_ponens"

N_DISTRACTORS = 10

# The fact (A) and the matching rule A⊃B = ~[ (A) ~[ (B) ] ], among ten unrelated
# rules Dk⊃Ek — twelve sibling chunks on the sheet (fan-out 12 > 7).
_DISTRACTORS = " ".join(
    f"~[ (D{k}) ~[ (E{k}) ] ]" for k in range(1, N_DISTRACTORS + 1)
)
BASE_EGIF = f"(A) ~[ (A) ~[ (B) ] ] {_DISTRACTORS}"

# After MP on the matching rule: (A)(B) plus the ten untouched distractors.
GOAL_EGIF = f"(A) (B) {_DISTRACTORS}"


# --------------------------------------------------------------------------- #
# Structural locators — name the matching rule by content (it alone holds B),  #
# so the proof never depends on sibling order.                                 #
# --------------------------------------------------------------------------- #

def _subtree_has_rel(g, cut, rel) -> bool:
    stack = list(g.area.get(cut, []))
    while stack:
        eid = stack.pop()
        if g.rel.get(eid) == rel:
            return True
        stack.extend(g.area.get(eid, []))
    return False


def _matching_rule(g):
    """The sheet-child cut whose subtree contains (B) — the rule A⊃B, picked
    out of the crowd by content (the distractors carry Dk/Ek, never B)."""
    for c in nav.child_cuts(g, g.sheet):
        if _subtree_has_rel(g, c, "B"):
            return c
    raise LookupError("matching rule (the A⊃B cut) not found")


def _inner_a(g):
    """The (A) *inside* the matching rule — the deiteration candidate, a copy of
    the asserted fact (A) on the enclosing sheet."""
    return nav.child_edges(g, _matching_rule(g), "A")[0]


def _double_cut(g):
    """After the inner (A) is deiterated, the matching rule has become a double
    cut ~[ ~[ (B) ] ] on the sheet — the outer cut to erase."""
    return _matching_rule(g)


def build_crowded_mp_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    author = (
        ProofChain.from_egif(BASE_EGIF)
        .apply("IT-", select=_inner_a, label="2e",
               note="Deiterate the inner (A) inside the matching rule, a copy of "
                    "the asserted fact (A) on the sheet — ignoring the ten "
                    "unrelated rules in the crowd.")
        .apply("DC-", select=_double_cut, label="3e",
               note="Erase the freed double cut → (B) lands on the sheet: modus "
                    "ponens picks the one relevant rule out of the crowd.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Crowded Modus Ponens",
        description=(
            "The fact (A) and the rule A⊃B among ten unrelated rules Dk⊃Ek — a "
            "twelve-chunk sheet (super-budget). Modus ponens on the one matching "
            "rule (IT-, DC-) lands (B); the narration ignores the ten distractors. "
            "Authored to exercise the spatial in-view rules (S1/S2): a focus-"
            "centered overview collapses the far siblings, and every narrated item "
            "stays visible. An authored demonstration (low warrant); every step a "
            "real, attestable Dau-rule application."
        ),
    )


def _provenance() -> dict:
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Dau, Frithjof",
             "title": "Mathematical Logic with Diagrams",
             "note": "Ch. 14 transformation rules (deiteration, double-cut "
                     "erasure); Ch. 17 soundness."},
        ],
        kind=KIND_PROOF,
    ).to_dict()


def _annotations(uod) -> list:
    anns = [
        make_annotation(
            SCOPE_UOD,
            "A super-budget worked chain: the inference sits in a crowd of twelve "
            "sibling chunks, far over the ~7 in-view budget. It exists to make the "
            "diagram↔narration harness's spatial metric (in-view coverage under a "
            "focus-centered overview) live — every other corpus chain is "
            "sub-budget. Low warrant (an authored demonstration of modus ponens).",
            tags=["super-budget", "in-view", "demonstration"],
        ),
        make_annotation(
            SCOPE_CHAIN,
            "Modus ponens picks the one rule whose antecedent matches the asserted "
            "fact (A); the ten distractors are never touched. The narration names "
            "only the fact and the matching rule — evidence for S1 (an expert "
            "keeps the narration within a bounded focus-neighborhood).",
            tags=["modus-ponens", "alpha", "selective-attention"],
        ),
    ]
    return annotations_to_list(anns)


def main(argv=None) -> int:
    from tomos_service import TomosService

    chain, uod = build_crowded_mp_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(GOAL_EGIF)), (
        "built inference does not reach (A)(B) + distractors"
    )

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=_provenance())
    service.save_annotations(uod, _annotations(uod))
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain "
          f"({len(chain.states)} states).")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
