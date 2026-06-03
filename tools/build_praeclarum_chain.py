"""
Build Leibniz's *Praeclarum Theorema* as a real transformation chain —
the tomos's first canonical diachronic exemplar.

    ((P ⊃ R) ∧ (Q ⊃ S))  ⊃  ((P ∧ Q) ⊃ (R ∧ S))

Sowa's showcase EG proof (``docs/references/Peirce_Rules_of_Inference.pdf``)
derives the theorem in **seven steps from a blank sheet** — versus the
Principia's 43 steps from five axiom schemata. It is pure Alpha
(propositional), so each of Peirce's three rule-pairs is one of Dau's six
rules. Peirce's labels ↔ ours: 3i→DC+, 1i→INS, 2i→IT+, 2e→IT-, 3e→DC-.

The seven steps (Sowa's diagram, read left-to-right then the second row
right-to-left):

    1. DC+  blank → ~[ ~[ ] ]                  (an empty double cut)
    2. INS  insert the antecedent (P⊃R)(Q⊃S) into the outer (negative) area
    3. IT+  iterate (P⊃R) into the inner cut
    4. INS  insert Q into the cut now holding the iterated (P⊃R)
    5. IT+  iterate (Q⊃S) into the cut around R
    6. IT-  deiterate the inner Q (a copy of the enclosing Q)
    7. DC-  erase the double cut around S

Every step is a *real* rule application through the authoring layer
(``proof_authoring.ProofChain`` + ``eg_navigation``): selections are named by
**structure** ("the cut holding P", "the inner cut") rather than by ephemeral
id, and the chain bookkeeping is automatic. Contrast
``tests/test_chain_persistence.py``, which hand-builds a *synthetic* chain to
exercise the persistence shape. This module is import-safe (no side effects).

A note on EGIF: propositional atoms are nullary relations and must be
**capitalised** (``(P)``) — lowercase is reserved for vertex/variable labels.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from tomos_service import TransformationChain
from universe_of_discourse import UniverseOfDiscourse


THEOREM_EGIF = (
    "~[ ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] "
    "~[ ~[ (P) (Q) ~[ (R) (S) ] ] ] ]"
)
"""The Praeclarum Theorema as an Alpha EG: the outer cut negates the
antecedent conjoined with the negated consequent — i.e. antecedent ⊃
consequent."""

UOD_ID = "theorem_praeclarum"

_ANTECEDENT = "~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ]"


# --------------------------------------------------------------------------- #
# Structural locators — each names an element by *what it is*, resolved fresh #
# against whatever state the step is applied to (ids change every step).      #
# --------------------------------------------------------------------------- #

def _outer(g):
    """The main implication's outer cut (the only cut on the sheet)."""
    return nav.child_cuts(g, g.sheet)[0]


def _implication(rel):
    """A locator for the antecedent conjunct whose antecedent is ``rel`` —
    (P⊃R) for "P", (Q⊃S) for "Q"."""
    return lambda g: nav.cut_holding_relation(g, _outer(g), rel)


def _inner(g):
    """The scroll's inner cut inside the outer cut (the one holding no direct
    relation of its own)."""
    return nav.empty_cut_in(g, _outer(g))


def _copied_implication(g):
    """The (P⊃R) copy iterated into the inner cut."""
    return nav.child_cuts(g, _inner(g))[0]


def _r_cut(g):
    """The cut around R inside the copied implication — destination for the
    (Q⊃S) iteration."""
    return nav.cut_holding_relation(g, _copied_implication(g), "R")


def _b_prime(g):
    """The (Q⊃S) copy iterated next to R (its outer cut directly holds Q)."""
    return nav.cut_holding_relation(g, _r_cut(g), "Q")


def _inner_q(g):
    """The Q inside that copy — the deiteration candidate (a copy of the
    enclosing Q)."""
    return nav.child_edges(g, _b_prime(g), "Q")[0]


def _double_cut_s(g):
    """After the inner Q is deiterated, the (Q⊃S) copy is ~[ ~[ (S) ] ] — the
    cut around R that now holds no direct relation. Its erasure leaves S."""
    return nav.empty_cut_in(g, _r_cut(g))


# --------------------------------------------------------------------------- #
# The proof                                                                    #
# --------------------------------------------------------------------------- #

def build_praeclarum_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct the proof as a real ``TransformationChain`` + its UoD."""
    author = (
        ProofChain.from_blank()
        .apply("DC+", label="3i",
               note="Insert an empty double cut on the blank sheet.")
        .apply("INS", insert=_ANTECEDENT, into=_outer, label="1i",
               note="Insert the antecedent (P⊃R)(Q⊃S) into the outer cut.")
        .apply("IT+", select=_implication("P"), into=_inner, label="2i",
               note="Iterate (P⊃R) into the inner cut.")
        .apply("INS", insert="(Q)", into=_copied_implication, label="1i",
               note="Insert Q into the cut holding the iterated (P⊃R).")
        .apply("IT+", select=_implication("Q"), into=_r_cut, label="2i",
               note="Iterate (Q⊃S) into the cut around R.")
        .apply("IT-", select=_inner_q, label="2e",
               note="Deiterate the inner Q (a copy of the enclosing Q).")
        .apply("DC-", select=_double_cut_s, label="3e",
               note="Erase the double cut around S.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Leibniz's Praeclarum Theorema",
        description=(
            "((P⊃R) ∧ (Q⊃S)) ⊃ ((P∧Q) ⊃ (R∧S)) — Sowa's 7-step Existential "
            "Graph proof from a blank sheet (docs/references/"
            "Peirce_Rules_of_Inference.pdf). The tomos's first canonical "
            "diachronic exemplar: every step a real, attestable Dau-rule "
            "application."
        ),
    )


def main(argv=None) -> int:
    """Build the exemplar and save it into the tomos corpus."""
    from tomos_service import TomosService

    chain, uod = build_praeclarum_chain()
    assert nav.area_signature(uod.current_egi) == nav.area_signature(
        parse_egif(THEOREM_EGIF)
    ), "built proof does not match the Praeclarum Theorema"

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain)  # §3.3 attests before any write
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    print(f"  final: {THEOREM_EGIF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
