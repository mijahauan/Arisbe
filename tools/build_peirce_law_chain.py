"""
Build **Peirce's Law** as a real transformation chain — the tomos's first
*authored-here* exemplar, and the Alpha half of the Organon import walkthrough
(``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §4.1).

    ((P ⊃ Q) ⊃ P) ⊃ P

Peirce's own *fifth icon* (Peirce 1885, "On the Algebra of Logic"); the canonical
theorem that is **classically valid yet not intuitionistically provable**.  Its EG
proof therefore spotlights exactly where classical logic enters: the unrestricted
double-cut insertion (steps 1 and 5).  Six steps from a blank sheet, pure Alpha,
so Peirce's labels ↔ Dau's rules: 3i→DC+, 1i→INS, 2i→IT+.

    0. (blank)
    1. DC+  ~[ ~[ ] ]                                   empty double cut
    2. INS  ~[ (P) ~[ ] ]                               P into the outer (negative) area
    3. INS  ~[ (P) ~[(Q)] ~[ ] ]                        ~[(Q)] into the outer area
    4. IT+  ~[ (P) ~[(Q)] ~[(P)] ]                      iterate P into the empty cut (the ¬P)
    5. DC+  ~[ ~[ ~[(P) ~[(Q)]] ] ~[(P)] ]              enclose P, ~[(Q)] in a double cut
    6. IT+  ~[ ~[ ~[(P) ~[(Q)]] ~[(P)] ] ~[(P)] ]       iterate ~[(P)] inward → ((P⊃Q)⊃P)⊃P

Provenance is recorded as a typed bundle (``provenance.py``): the *theorem* is
Peirce 1885, but **this derivation is original to Arisbe** (not a transcription
of a published EG proof — only the Praeclarum has one), at low warrant.  The
author's commentary rides in the annotation layer (``annotations.py``) at the
scopes the walkthrough mapped: a chain-level crux ("turns on steps 1 and 5"), a
uod-level remark ("where classicality lives"), and step-level notes on the two
freely-inserted double cuts.  Import-safe (no side effects on import).
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
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from provenance import authored_proof, make_provenance
from tomos_service import TransformationChain
from universe_of_discourse import UniverseOfDiscourse

UOD_ID = "peirce_law"

TARGET_EGIF = "~[ ~[ ~[ (P) ~[ (Q) ] ] ~[ (P) ] ] ~[ (P) ] ]"
"""``((P⊃Q)⊃P)⊃P`` as an Alpha EG — the stored end state."""


# --------------------------------------------------------------------------- #
# Structural locators — name each element by what it is, resolved fresh.       #
# --------------------------------------------------------------------------- #

def _outer(g):
    """The single cut on the sheet — the main implication's outer cut."""
    return nav.child_cuts(g, g.sheet)[0]


def _p_in_outer(g):
    """The (P) directly in the outer area (not the nested copies)."""
    return nav.child_edges(g, _outer(g), "P")[0]


def _q_cut_in_outer(g):
    """The ~[(Q)] cut directly in the outer area."""
    return nav.cut_holding_relation(g, _outer(g), "Q")


def _empty_in_outer(g):
    """The child cut of the outer area holding no direct relation — the empty
    cut (steps 4) and, after step 5, the double-cut shell wrapping the
    antecedent (step 6)."""
    return nav.empty_cut_in(g, _outer(g))


def _consequent_cut(g):
    """The ~[(P)] consequent cut directly in the outer area (the only child cut
    that directly holds a P)."""
    return nav.cut_holding_relation(g, _outer(g), "P")


# --------------------------------------------------------------------------- #
# The proof                                                                    #
# --------------------------------------------------------------------------- #

def build_peirce_law_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct Peirce's Law as a real ``TransformationChain`` + its UoD."""
    author = (
        ProofChain.from_blank()
        .apply("DC+", label="3i",
               note="Insert an empty double cut on the blank sheet.")
        .apply("INS", insert="(P)", into=_outer, label="1i",
               note="Insert P into the outer (negative) area — anything may be "
                    "inserted in an odd area.")
        .apply("INS", insert="~[ (Q) ]", into=_outer, label="1i",
               note="Insert ~[(Q)] into the outer area, building the implication "
                    "(P⊃Q).")
        .apply("IT+", select=_p_in_outer, into=_empty_in_outer, label="2i",
               note="Iterate P into the empty cut — forming the ¬P that becomes "
                    "the consequent.")
        .apply("DC+", select=lambda g: [_p_in_outer(g), _q_cut_in_outer(g)],
               label="3i",
               note="Enclose P and ~[(Q)] in a double cut, growing the "
                    "antecedent's scroll ((P⊃Q)⊃P).")
        .apply("IT+", select=_consequent_cut, into=_empty_in_outer, label="2i",
               note="Iterate the consequent ~[(P)] inward to complete (P⊃Q)⊃P.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Peirce's Law",
        description=(
            "((P⊃Q)⊃P)⊃P — Peirce's fifth icon (Peirce 1885), the classical "
            "tautology that is not intuitionistically provable. A 6-step Alpha "
            "derivation from the blank sheet; the derivation is original to "
            "Arisbe (the theorem is Peirce's). Every step a real, attestable "
            "Dau-rule application."
        ),
    )


# --------------------------------------------------------------------------- #
# Provenance + annotations (the import-walkthrough payload)                    #
# --------------------------------------------------------------------------- #

_THEOREM_SOURCE = {
    "type": "article-journal",
    "author": "Peirce, Charles Sanders",
    "title": "On the Algebra of Logic: A Contribution to the Philosophy of Notation",
    "container_title": "American Journal of Mathematics",
    "volume": "7",
    "year": "1885",
    "pages": "180–202",
    "bibkey": "peirce1885algebra",
    "note": "Peirce's Law is the ‘fifth icon’ (~CP 3.384).",
}
_METHOD_SOURCES = [
    {"type": "book", "author": "Dau, Frithjof",
     "title": "The Logic System of Concept Graphs with Negation",
     "year": "2003", "bibkey": "dau2003logic"},
    {"type": "article-journal", "author": "Sowa, John F.",
     "title": "Peirce's Tutorial on Existential Graphs",
     "container_title": "Semiotica", "year": "2011", "bibkey": "sowa2011tutorial"},
    {"type": "book", "author": "Roberts, Don D.",
     "title": "The Existential Graphs of Charles S. Peirce",
     "year": "1973", "bibkey": "roberts1973existential"},
]


def peirce_law_provenance() -> dict:
    """The typed provenance bundle: Peirce's theorem, an Arisbe-authored
    derivation, in Dau's/Sowa's calculus — all at low warrant."""
    return make_provenance(
        theorem_source=_THEOREM_SOURCE,
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHOD_SOURCES,
    ).to_dict()


def peirce_law_annotations() -> List[dict]:
    """The author's commentary, at the scopes the walkthrough mapped (§4.1)."""
    anns = [
        make_annotation(
            SCOPE_UOD,
            "Peirce's Law is classically valid yet not intuitionistically "
            "provable — the cleanest place to see where classicality lives in "
            "the EG rule set, proved in Peirce's own graphs.",
            tags=["pedagogy"],
        ),
        make_annotation(
            SCOPE_CHAIN,
            "The whole derivation turns on steps 1 and 5 — the two freely-"
            "inserted double cuts. That unrestricted double-cut insertion is "
            "exactly the classical move an intuitionistic restriction would "
            "forbid; everything distinguishing classical from intuitionistic EG "
            "reasoning lives in that one rule.",
            tags=["crux"],
        ),
        make_annotation(
            SCOPE_STEP,
            "The first freely-inserted double cut — half of the classical move "
            "this theorem spotlights.",
            step_id="step-1", tags=["crux"],
        ),
        make_annotation(
            SCOPE_STEP,
            "The second freely-inserted double cut (around P and ~[(Q)]); with "
            "step 1, this is where classicality enters.",
            step_id="step-5", tags=["crux"],
        ),
    ]
    return annotations_to_list(anns)


def main(argv=None) -> int:
    """Build the exemplar and save it into the tomos corpus with its provenance
    and annotation layer."""
    from tomos_service import TomosService

    chain, uod = build_peirce_law_chain()
    assert nav.area_signature(uod.current_egi) == nav.area_signature(
        parse_egif(TARGET_EGIF)
    ), "built proof does not match Peirce's Law"

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    # §3.3 attests inside save_uod before any write; provenance rides along.
    service.save_uod_with_chain(uod, chain, provenance=peirce_law_provenance())
    service.save_annotations(uod, peirce_law_annotations())
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    print(f"  final: {TARGET_EGIF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
