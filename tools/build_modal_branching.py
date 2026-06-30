"""
Build a **branching UoD that expresses possibility and necessity** — the
diachronic, mark-free reading of ◇ and □ (docs/MODALITY_WITHOUT_GAMMA.md §1).

The thesis: a modal operator is a quantifier over a Kripke frame, and Arisbe's
branching history *is* that frame (worlds = sheets, accessibility = legal
transitions). So ◇φ = "some legal trajectory scribes φ" and □φ = "every legal
trajectory scribes φ" — *possibility is the branching of trajectories, necessity
is their convergence.* No broken cut, no tincture; the modality is the shape of the
DAG, read off by ``src/modal_query.py``.

The episode — **a morning's weather, legally developed.** From a fully-specified
morning ``(cloudy) (cold) (calm)``, two lines of development drop a feature in turn
(each step a real ERA in a positive context — a legal relinquishment):

    (cloudy)(cold)(calm)  --ERA calm-->  (cloudy)(cold)  --ERA cloudy-->  (cold)
        |                                                                   ^
        +------------- ERA cloudy --> (cold)(calm) -- ERA calm ------------+

Both lines converge on ``(cold)``. Reading ◇/□ off the four reachable sheets:

  * **□ cold** — *cold* is scribed on every reachable sheet: it survives every
    legal trajectory. Necessity as convergence.
  * **◇ cloudy**, **◇ calm** — each is scribed on *some* reachable sheet but not
    all: possible, not necessary. Possibility as branching.

Original to Arisbe (a demonstration of the modal frame, not a cited theorem), low
warrant; every edge a sound ERA, so the whole DAG is §3.3-attestable. Import-safe.
See docs/EXEMPLARS.md.
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
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UOD_ID = "possible_and_necessary"
BASE_EGIF = "(cloudy) (cold) (calm)"
GOAL_EGIF = "(cold)"

_cloudy = lambda g: nav.child_edges(g, g.sheet, "cloudy")[0]   # noqa: E731
_calm = lambda g: nav.child_edges(g, g.sheet, "calm")[0]       # noqa: E731


def build_modal_branching_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    pc = ProofChain.from_egif(BASE_EGIF)                                    # s0
    # Line A — the wind picks up (calm goes), then it clears (cloudy goes).
    pc.apply("ERA", select=_calm, branch="wind-rises", label="1e",
             note="The calm lifts — erase (calm). One legal line of development.")
    pc.apply("ERA", select=_cloudy, branch="wind-rises", label="2e",
             note="Then it clears — erase (cloudy), leaving (cold).")
    # Line B — back at the start: it clears first, then the wind picks up.
    pc.at("s0")
    pc.apply("ERA", select=_cloudy, branch="clears-first", label="1e",
             note="Back at the morning: it clears first — erase (cloudy).")
    pc.apply("ERA", select=_calm, branch="clears-first", label="2e",
             note="Then the calm lifts — erase (calm), reaching the same (cold).")
    pc.converge_last_into("s2")  # both lines rest at (cold)

    return pc.to_uod(
        uod_id=UOD_ID,
        name="Possibility and necessity (a branching episode)",
        description=(
            "A diachronic, mark-free reading of ◇ and □ (docs/MODALITY_WITHOUT_GAMMA.md): "
            "the branching history is the Kripke frame, so ◇φ = 'some legal trajectory "
            "scribes φ' and □φ = 'every legal trajectory scribes φ'. From a morning "
            "(cloudy)(cold)(calm), two lines of development each drop a feature and "
            "converge on (cold). Across the reachable sheets, (cold) is necessary "
            "(□ — on every trajectory), while (cloudy) and (calm) are each merely "
            "possible (◇ — on some). Read off the DAG by src/modal_query.py; no broken "
            "cut, no tincture — necessity is convergence, possibility is branching."
        ),
        category=UoDCategory.THEOREM_PROOF,
    )


def modal_provenance() -> dict:
    # An authored *demonstration* of the modal frame, not a cited theorem — method
    # provenance only (a synthetic exemplar must carry no fabricated citation).
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "van Benthem, Johan",
             "title": "Modal Correspondence Theory", "year": "1976",
             "note": "the standard translation — modal operators as quantifiers over a frame"},
            {"type": "book", "author": "Dau, Frithjof",
             "title": "Mathematical Logic with Diagrams",
             "note": "Ch. 14 erasure rule; Ch. 17 soundness — each edge a sound move"},
        ],
        kind=KIND_PROOF,
    ).to_dict()


def modal_annotations() -> list:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "Possibility and necessity drawn as the shape of a derivation, not as a "
            "modal mark (docs/MODALITY_WITHOUT_GAMMA.md §1, the trajectory reading). The "
            "worlds are the four reachable sheets; accessibility is the legal-transition "
            "DAG. src/modal_query.py reads ◇/□ off it: □(cold) holds (cold is on every "
            "reachable sheet — necessity as convergence), while ◇(cloudy) and ◇(calm) "
            "hold without □ (each on some sheet but not all — possibility as branching).",
            tags=["modality", "branching", "derivation-dag", "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Two legal lines of development drop (cloudy) and (calm) in either order and "
            "converge on (cold). Every edge is a sound ERA in a positive context (a "
            "relinquishment the rules license), so the whole frame is §3.3-attestable — "
            "the modal frame is drawn and checkable, never asserted by a glyph.",
            tags=["confluence", "alpha", "modal-frame"]),
    ])


def main(argv=None) -> int:
    chain, uod = build_modal_branching_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(GOAL_EGIF)), "episode must reach (cold)"
    from collections import Counter
    frm = Counter(s.from_state_id for s in chain.steps)
    to = Counter(s.to_state_id for s in chain.steps)
    assert any(v > 1 for v in frm.values()), "no fork — not a branching chain"
    assert any(v > 1 for v in to.values()), "no convergence — not a diamond"

    # Confirm the modal reading the exemplar exists to demonstrate.
    import modal_query as mq
    assert mq.necessarily(chain, mq.scribes_relation("cold")).holds, "cold should be □"
    assert mq.possibly(chain, mq.scribes_relation("cloudy")).holds, "cloudy should be ◇"
    assert not mq.necessarily(chain, mq.scribes_relation("cloudy")).holds, "cloudy is not □"

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=modal_provenance())
    service.save_annotations(uod, modal_annotations())
    print(f"Saved '{uod.uod_id}' — {len(chain.steps)} steps, {len(chain.states)} states.")
    print(f"  □ cold: {mq.necessarily(chain, mq.scribes_relation('cold')).summary}")
    print(f"  ◇ cloudy: {mq.possibly(chain, mq.scribes_relation('cloudy')).summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
