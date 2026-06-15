"""Build a **branching** reasoning episode — the fixture that exercises the
derivation-DAG lens (``docs/ADAPTIVE_SCOPE_VIEWER.md`` §10).

Almost every seeded chain is a single line; the derivation-DAG view needs a real
*fork* (two lines of development from one state) and ideally a *convergence* (the
two lines reaching the same conclusion — the Metamath ``…ALT`` / alternate-proofs
shape, realised here natively in Dau's calculus rather than imported from a foreign
prover, so every step stays a sound, attestable rule application).

The episode — **confluence of erasure**.  From ``(P) (Q) (R)`` on the sheet, erase
the two side assertions ``(P)`` and ``(Q)`` in *either order*, keeping ``(R)``:

    (P)(Q)(R)  --ERA (P)-->  (Q)(R)  --ERA (Q)-->  (R)
       |                                            ^
       +-------- ERA (Q) --> (P)(R) -- ERA (P) -----+

A diamond: one fork at the start, two two-step lines, one convergence at ``(R)``.
It demonstrates that erasure order doesn't matter (a local-confluence fact) while
giving the DAG lens a genuine branch-and-merge to draw.  Original to Arisbe (a
demonstration of branch structure, not a cited theorem), at low warrant; every
edge a real ERA application, so the whole DAG is §3.3-attestable.  Import-safe.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import (
    SCOPE_CHAIN, SCOPE_UOD, annotations_to_list, make_annotation,
)
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from provenance import KIND_PROOF, authored_proof, make_provenance
from tomos_service import TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UOD_ID = "branching_confluence"
BASE_EGIF = "(P) (Q) (R)"
GOAL_EGIF = "(R)"

# Sheet-level relation locators (resolved against the current state each apply).
_P = lambda g: nav.child_edges(g, g.sheet, "P")[0]   # noqa: E731
_Q = lambda g: nav.child_edges(g, g.sheet, "Q")[0]   # noqa: E731


def build_branching_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct the confluence-of-erasure episode as a branching chain + UoD."""
    pc = ProofChain.from_egif(BASE_EGIF)                                   # s0
    # Line A — erase P, then Q.
    pc.apply("ERA", select=_P, branch="erase-P-first", label="1e",
             note="Erase (P) from the sheet — one line of inquiry.")        # s0→s1 (Q)(R)
    pc.apply("ERA", select=_Q, branch="erase-P-first", label="2e",
             note="Then erase (Q), leaving (R).")                           # s1→s2 (R)
    # Line B — back to the start, erase Q, then P.
    pc.at("s0")
    pc.apply("ERA", select=_Q, branch="erase-Q-first", label="1e",
             note="Back at the start: erase (Q) first — the other line.")   # s0→s3 (P)(R)
    pc.apply("ERA", select=_P, branch="erase-Q-first", label="2e",
             note="Then erase (P), reaching the same (R).")                 # s3→s4 (R)
    # The two lines reach the same graph — converge them (the diamond).
    pc.converge_last_into("s2")

    return pc.to_uod(
        uod_id=UOD_ID,
        name="Confluence of erasure (a branching episode)",
        description=(
            "From (P)(Q)(R), erase (P) and (Q) in either order — two lines of "
            "development that fork at the start and converge at (R). A native "
            "demonstration of branch-and-merge structure (the derivation-DAG view): "
            "every edge a real ERA application, so the whole DAG is attestable; the "
            "order-independence it shows is a local-confluence fact about erasure."
        ),
        category=UoDCategory.THEOREM_PROOF,
    )


def branching_provenance() -> dict:
    # No theorem_source — this is an authored *demonstration* of branch structure,
    # not a cited theorem (the order-independence it shows is a local-confluence
    # observation). Method-only provenance keeps the honesty floor (a synthetic
    # exemplar must not carry a fabricated citation).
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Dau, Frithjof",
             "title": "Mathematical Logic with Diagrams",
             "note": "Ch. 14 transformation rules (the erasure rule); Ch. 17 soundness."},
        ],
        kind=KIND_PROOF,   # a worked derivation that carries a chain
    ).to_dict()


def branching_annotations(uod) -> list:
    anns = [
        make_annotation(
            SCOPE_UOD,
            "A branching episode: two lines of development fork from the start "
            "state and converge at the same conclusion (R). The derivation-DAG "
            "lens draws the fork and the merge; the storyboard / time-stack lenses "
            "(which assume a single line) are not offered for it.",
            tags=["branching", "derivation-dag", "demonstration"],
        ),
        make_annotation(
            SCOPE_CHAIN,
            "Erasure order is immaterial — erase (P) then (Q), or (Q) then (P); "
            "both reach (R). The episode exists to exercise branch structure, not "
            "to assert a new theorem (low warrant, authored here).",
            tags=["confluence", "alpha"],
        ),
    ]
    return annotations_to_list(anns)


def main(argv=None) -> int:
    from tomos_service import TomosService

    chain, uod = build_branching_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(GOAL_EGIF)), (
        "built episode does not reach (R)"
    )
    # Sanity: a genuine branch-and-merge (one fork, one convergence).
    from collections import Counter
    frm = Counter(s.from_state_id for s in chain.steps)
    to = Counter(s.to_state_id for s in chain.steps)
    assert any(v > 1 for v in frm.values()), "no fork — not a branching chain"
    assert any(v > 1 for v in to.values()), "no convergence — not a diamond"

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=branching_provenance())
    service.save_annotations(uod, branching_annotations(uod))
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step branching chain "
          f"({len(chain.states)} states).")
    for s in chain.steps:
        print(f"  {s.from_state_id} → {s.to_state_id}  {s.rule_name}  [{s.branch_id}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
