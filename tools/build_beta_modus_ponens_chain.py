"""
Build **Beta modus ponens** as a transformation chain — the tomos's second
canonical exemplar, and its first with a *line of identity*.

    P(x)  and  P(x) → Q(x)     ⊢     P(x) ∧ Q(x)

Where Praeclarum is a *theorem* (derived from the blank sheet, ⊤), this is an
*inference from premises*: the chain is anchored at the asserted premise graph
and derives the conclusion. So the two exemplars together exhibit both shapes
of a Peircean reasoning episode — proof-from-nothing and inference-from-a-
context (``docs/CHAIN_OF_SEMIOSIS.md``, "an assertion resides in a context").

The premises, conjoined on a single **line of identity** ``x`` that runs from
the sheet into the cut (this is what makes it Beta, not Alpha):

    (P *x) ~[ (P x) ~[ (Q x) ] ]
     └ P(x) ┘ └────── P(x) → Q(x) ──────┘

Two steps, mirroring the Alpha modus ponens in
``tests/test_logical_proof_exercises.py`` but on one shared line:

    1. IT-  (2e) deiterate the inner P(x) — a copy of the P(x) on the sheet
            (same line of identity), leaving the double cut ~[ ~[ (Q x) ] ]
    2. DC-  (3e) erase that double cut, landing Q(x) on the sheet

Conclusion ``(P *x) (Q x)`` — P and Q on one line: P(x) ∧ Q(x). (EG keeps the
premise P(x); erasing it to leave bare Q(x) would be an optional positive-area
ERA, not part of the inference proper.)

Built on the authoring layer (``proof_authoring.ProofChain`` + ``eg_navigation``):
selections are named by structure, the chain bookkeeping is automatic. Import-
safe; run as a script to seed the corpus.
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


PREMISES_EGIF = "(P *x) ~[ (P x) ~[ (Q x) ] ]"
"""P(x) conjoined with P(x)→Q(x) on a single line of identity x."""

CONCLUSION_EGIF = "(P *x) (Q x)"
"""P(x) ∧ Q(x) — both relations on the one line of identity."""

UOD_ID = "beta_modus_ponens"


# --------------------------------------------------------------------------- #
# Structural locators                                                          #
# --------------------------------------------------------------------------- #

def _implication(g):
    """The implication cut ~[ (P x) ~[ (Q x) ] ] on the sheet."""
    return nav.child_cuts(g, g.sheet)[0]


def _inner_p(g):
    """The P(x) *inside* the implication — the deiteration candidate (an
    iterated copy of the P(x) on the enclosing sheet, same line x)."""
    return nav.child_edges(g, _implication(g), "P")[0]


def _double_cut(g):
    """After the inner P is deiterated, the implication has become a double
    cut ~[ ~[ (Q x) ] ] on the sheet — the outer cut to erase."""
    return nav.child_cuts(g, g.sheet)[0]


# --------------------------------------------------------------------------- #
# The proof                                                                    #
# --------------------------------------------------------------------------- #

def build_beta_modus_ponens_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct the inference as a real ``TransformationChain`` + its UoD,
    anchored at the premise graph."""
    author = (
        ProofChain.from_egif(PREMISES_EGIF)
        .apply("IT-", select=_inner_p, label="2e",
               note="Deiterate the inner P(x) — a copy of the P(x) on the sheet "
                    "(same line of identity).")
        .apply("DC-", select=_double_cut, label="3e",
               note="Erase the resulting double cut, landing Q(x) on the sheet.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Beta Modus Ponens",
        description=(
            "P(x), P(x)→Q(x) ⊢ P(x)∧Q(x) — modus ponens on a single line of "
            "identity (the tomos's first Beta exemplar). Two steps (IT-, DC-) "
            "from the asserted premises; mirrors the Alpha modus ponens in "
            "test_logical_proof_exercises but with a shared line crossing the "
            "cut. Every step a real, attestable Dau-rule application."
        ),
    )


def main(argv=None) -> int:
    """Build the exemplar and save it into the tomos corpus."""
    from tomos_service import TomosService

    chain, uod = build_beta_modus_ponens_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(CONCLUSION_EGIF)), (
        "built inference does not match P(x) ∧ Q(x)"
    )

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain)  # §3.3 attests before any write
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    print(f"  from : {PREMISES_EGIF}")
    print(f"  to   : {CONCLUSION_EGIF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
