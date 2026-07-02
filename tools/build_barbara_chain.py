"""
Build **Barbara** as a real transformation chain — the Beta half of the Organon
import walkthrough (``docs/archived/ORGANON_IMPORT_WALKTHROUGH.md`` §4.2), and the first
fixture to exercise the derived **universal-instantiation / iterate-and-join**
move (``derived_rules.universal_instantiation``; Sowa Fig. 14; Dau §16.1).

    ∀x(M(x)⊃P(x)),  ∀x(S(x)⊃M(x))  ⊢  ∀x(S(x)⊃P(x))

Aristotle's first-figure syllogism (the name "Barbara" is the medieval mnemonic
tradition).  Unlike Peirce's Law, this is a deduction **from premises asserted on
the sheet** (Γ ⊢ φ), not from the blank sheet — the premises-vs-blank contrast is
itself worth demonstrating.  Four steps:

    A1. ~[ (M *x) ~[ (P x) ] ]     (every M is P) — asserted
    A2. ~[ (S *y) ~[ (M y) ] ]     (every S is M) — asserted
    1. UI   iterate A1 into A2's scroll, joining the copy's line to y
            (universal instantiation, the one Beta-specific move)
    2. IT-  deiterate the inner (M y) — a copy of the enclosing (M y)
    3. DC-  erase the resulting double cut, leaving (M y)(P y)
    4. ERA  erase (M y) from its positive area → every S is P  ∎

A1 stays asserted on the sheet throughout.  The derivation is original to Arisbe
(the theorem is Aristotle's), at low warrant.  Import-safe (no side effects).
"""

import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import (
    SCOPE_CHAIN,
    SCOPE_STEP,
    SCOPE_UOD,
    annotations_to_list,
    make_annotation,
)
from derived_rules import universal_instantiation
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from provenance import authored_proof, make_provenance
from tomos_service import TransformationChain
from universe_of_discourse import UniverseOfDiscourse

UOD_ID = "barbara"

_A1 = "~[ (M *x) ~[ (P x) ] ]"   # every M is P
_A2 = "~[ (S *y) ~[ (M y) ] ]"   # every S is M
PREMISES_EGIF = f"{_A1} {_A2}"

CONCLUSION_EGIF = "~[ (M *x) ~[ (P x) ] ] ~[ (S *y) ~[ (P y) ] ]"
"""A1 still asserted, plus the derived ∀y(S(y)⊃P(y))."""


# --------------------------------------------------------------------------- #
# Structural locators                                                          #
# --------------------------------------------------------------------------- #

def _a1(g):
    """The 'every M is P' premise — the sheet cut directly holding (M …)."""
    return nav.cut_holding_relation(g, g.sheet, "M")


def _a2(g):
    """The 'every S is M' premise — the sheet cut directly holding (S …)."""
    return nav.cut_holding_relation(g, g.sheet, "S")


def _a2_inner(g):
    """A2's inner cut, holding (M y) — the iterate-and-join target area."""
    return nav.cut_holding_relation(g, _a2(g), "M")


def _ui_step(g):
    """Step 1 — universal instantiation: iterate A1 into A2's scroll and join
    the copied line to A2's y-line (the line at (M y))."""
    a2i = _a2_inner(g)
    y = nav.vertices_of_edge(g, nav.child_edges(g, a2i, "M")[0])[0]
    return universal_instantiation(
        g, universal_cut=_a1(g), target_area=a2i, join_vertex=y,
        edge_id="e_ui_barbara",
    )


def _inner_m(g):
    """The inner (M y) introduced by step 1 — the deiteration candidate."""
    cc = nav.cut_holding_relation(g, _a2_inner(g), "M")  # the copied cut
    return nav.child_edges(g, cc, "M")[0]


def _double_cut(g):
    """After deiteration, the bare double cut ~[ ~[ (P y) ] ] inside A2's scroll."""
    c2i = _a2_inner(g)
    return nav.empty_cut_in(g, c2i) or nav.child_cuts(g, c2i)[0]


def _middle_m(g):
    """The middle term (M y) to erase from A2's (positive) scroll."""
    return nav.child_edges(g, _a2_inner(g), "M")[0]


# --------------------------------------------------------------------------- #
# The proof                                                                    #
# --------------------------------------------------------------------------- #

def build_barbara_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct Barbara as a real ``TransformationChain`` + its UoD."""
    author = (
        ProofChain.from_egif(PREMISES_EGIF)
        .apply_derived(
            "UI", _ui_step, label="2i/1i",
            note="Iterate A1 into A2's scroll and join the copied line to y — "
                 "universal instantiation (Sowa Fig. 14; Dau §16 derived "
                 "ligature rules).",
        )
        .apply("IT-", select=_inner_m, label="2e",
               note="Deiterate the inner (M y) — a copy of the enclosing (M y) "
                    "on the same line.")
        .apply("DC-", select=_double_cut, label="3e",
               note="Erase the resulting double cut, leaving (M y) and (P y) "
                    "together — every S is both M and P.")
        .apply("ERA", select=_middle_m, label="1e",
               note="Erase the middle term (M y) from its positive area → "
                    "every S is P.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Barbara (First-Figure Syllogism)",
        description=(
            "∀x(M⊃P), ∀x(S⊃M) ⊢ ∀x(S⊃P) — Aristotle's first syllogism, proved "
            "from premises asserted on the sheet (Γ⊢φ). Exercises the derived "
            "universal-instantiation / iterate-and-join move on a line of "
            "identity. The derivation is original to Arisbe (the theorem is "
            "Aristotle's); every step a real, attestable rule application."
        ),
    )


# --------------------------------------------------------------------------- #
# Provenance + annotations                                                     #
# --------------------------------------------------------------------------- #

_THEOREM_SOURCE = {
    "type": "book",
    "author": "Aristotle",
    "title": "Prior Analytics",
    "note": "Book I — first-figure universal syllogism. The name ‘Barbara’ is "
            "the medieval mnemonic tradition (Peter of Spain / William of "
            "Sherwood).",
}
_METHOD_SOURCES = [
    {"type": "book", "author": "Dau, Frithjof",
     "title": "Mathematical Logic with Diagrams",
     "note": "§14.2 iteration; §16.1 derived rules for ligatures (Lem 16.2, "
             "Def 16.6); §17 soundness."},
    {"type": "article-journal", "author": "Sowa, John F.",
     "title": "Conceptual Graphs (Handbook of Knowledge Representation, ch. 5)",
     "year": "2008", "note": "Fig. 14, universal instantiation as iterate-and-join."},
    {"type": "book", "author": "Roberts, Don D.",
     "title": "The Existential Graphs of Charles S. Peirce",
     "year": "1973", "bibkey": "roberts1973existential"},
]


def barbara_provenance() -> dict:
    return make_provenance(
        theorem_source=_THEOREM_SOURCE,
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHOD_SOURCES,
    ).to_dict()


def barbara_annotations() -> List[dict]:
    anns = [
        make_annotation(
            SCOPE_UOD,
            "Barbara — Aristotle's first syllogism — proved from premises "
            "asserted on the sheet (Γ⊢φ); the premises-vs-blank-sheet contrast "
            "with Peirce's Law and the Praeclarum is itself worth demonstrating.",
            tags=["pedagogy"],
        ),
        make_annotation(
            SCOPE_CHAIN,
            "A1 ('every M is P') remains asserted on the sheet throughout; erase "
            "it with a final ERA if you want the conclusion standing alone.",
        ),
        make_annotation(
            SCOPE_STEP,
            "The one genuinely Beta-specific move: iterate A1 into A2's scroll "
            "and join the copied line of identity to y — *x becomes a bound use "
            "of y. This iterate-and-join is universal instantiation derived from "
            "the primitives (Sowa Fig. 14; Dau §16 derived ligature rules) — and "
            "the place a naive engine quietly drops the coreference.",
            step_id="step-1", tags=["crux", "beta-crux", "fixture"],
        ),
    ]
    return annotations_to_list(anns)


def main(argv=None) -> int:
    from tomos_service import TomosService

    chain, uod = build_barbara_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(CONCLUSION_EGIF)), (
        "built proof does not match Barbara's conclusion"
    )

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=barbara_provenance())
    service.save_annotations(uod, barbara_annotations())
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    print(f"  final: {CONCLUSION_EGIF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
