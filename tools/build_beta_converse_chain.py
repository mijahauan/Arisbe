"""
Build **converse modus ponens** as a transformation chain — the tomos's
first exemplar whose conclusion has two *crossing* lines of identity, and so
the first whose faithful Peirce drawing needs the **bridge** mark (Tier 3c).

    R(x, y)  and  ∀x∀y( R(x, y) → S(y, x) )     ⊢     R(x, y) ∧ S(y, x)

It is modus ponens (the same two steps as ``build_beta_modus_ponens_chain``)
but over a *binary* relation whose consequent swaps the arguments. That swap
is the whole point: in the conclusion the line ``x`` runs to R's first hook
and S's second, while ``y`` runs to R's second and S's first — so the two
lines must cross in any 2-D drawing. Two distinct lines sharing a point yet
staying distinct is exactly §3.0's worked example; the bridge is the
convention that recovers the distinction the projection would collapse.

The premises, on two shared lines ``x`` and ``y``:

    (R *x *y) ~[ (R x y) ~[ (S y x) ] ]

Two steps:

    1. IT-  (2e) deiterate the inner R(x, y) — a copy of the R(x, y) on the
            sheet (same two lines), leaving the double cut ~[ ~[ (S y x) ] ]
    2. DC-  (3e) erase that double cut, landing S(y, x) on the sheet

Conclusion ``(R *x *y) (S y x)`` — R(x,y) ∧ S(y,x), the two lines crossing.

Built on the authoring layer (``proof_authoring.ProofChain`` + ``eg_navigation``).
Import-safe; run as a script to seed the corpus.
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


PREMISES_EGIF = "(R *x *y) ~[ (R x y) ~[ (S y x) ] ]"
"""R(x,y) conjoined with ∀x∀y(R(x,y)→S(y,x)) on two lines of identity."""

CONCLUSION_EGIF = "(R *x *y) (S y x)"
"""R(x,y) ∧ S(y,x) — the two lines cross (R uses (x,y), S uses (y,x))."""

UOD_ID = "beta_converse_mp"


def _implication(g):
    """The implication cut ~[ (R x y) ~[ (S y x) ] ] on the sheet."""
    return nav.child_cuts(g, g.sheet)[0]


def _inner_r(g):
    """The R(x,y) *inside* the implication — the deiteration candidate (an
    iterated copy of the R(x,y) on the sheet, same two lines)."""
    return nav.child_edges(g, _implication(g), "R")[0]


def _double_cut(g):
    """After the inner R is deiterated, the implication is a double cut
    ~[ ~[ (S y x) ] ] on the sheet — the outer cut to erase."""
    return nav.child_cuts(g, g.sheet)[0]


def build_beta_converse_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct the converse inference as a real ``TransformationChain`` +
    its UoD, anchored at the premise graph."""
    author = (
        ProofChain.from_egif(PREMISES_EGIF)
        .apply("IT-", select=_inner_r, label="2e",
               note="Deiterate the inner R(x,y) — a copy of the R(x,y) on the "
                    "sheet (same two lines of identity).")
        .apply("DC-", select=_double_cut, label="3e",
               note="Erase the resulting double cut, landing S(y,x) on the "
                    "sheet — its two lines cross R's.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Converse Modus Ponens (crossing lines)",
        description=(
            "R(x,y), ∀x∀y(R(x,y)→S(y,x)) ⊢ R(x,y)∧S(y,x) — modus ponens over a "
            "binary relation whose consequent swaps the arguments, so the two "
            "lines of identity cross. The tomos's first exemplar that exercises "
            "the Peirce bridge-at-crossing mark (Tier 3c, §3.0's worked "
            "example). Two steps (IT-, DC-) from the asserted premises; every "
            "step a real, attestable Dau-rule application."
        ),
    )


def main(argv=None) -> int:
    """Build the exemplar and save it into the tomos corpus."""
    from tomos_service import TomosService

    chain, uod = build_beta_converse_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(CONCLUSION_EGIF)), (
        "built inference does not match R(x,y) ∧ S(y,x)"
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
