"""
Build two **domain-model exemplars** — small modelled universes of discourse,
saved as ``kind=domain_model`` UoDs in the tomos corpus. They are the *boards*
the Endoporeutic Game is played on: an inning is *given M, then G*, and you can
only play if there is an M to choose. These two give a contrasting pair —

  * **zoo_world** — a *closed* taxonomy with Horn rules. Materialization
    forward-chains it (dog ⊑ mammal ⊑ warm-blooded, …), so "every mammal is
    warm-blooded" is a *theorem* of the world (TRUE) while "every warm-blooded
    thing is a mammal" is *refuted* (FALSE — the sparrow Pip is the
    counterexample). The board for the holds / fails outcomes.

  * **harbor_town** — an *open* civic world (facts only, no closure). A claim
    the record neither confirms nor denies reads UNKNOWN — the *independent /
    candidate-new-fact* outcome the open-world horizon produces.

Both are real corpus UoDs: browsable read-only in Organon and selectable as M in
the Agon model picker (``GET /agon/models`` lists every corpus UoD). The curated
``ExampleModel`` entries in ``src/agon_models.py`` pair each with a ready sample
proposal so a newcomer can play immediately. Import-safe; run as a script to seed.

**Under the validity discipline** (docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §3):
each board resides at level 1 of a **standing world-scroll** ``~[ M ~[ ] ]`` —
nothing contingent at depth 0 — and is built by the gapless inbound construction,
recorded as a real two-step chain from the blank sheet: **DC+** (open the standing
scroll; asserts nothing) then **INS** (posit the board into the negative arena;
sound). Both steps are ordinary Dau rules, replayable. The oracle/peel reads the
antecedent area (``world_scroll.m_view``), so the boards play exactly as before.

See docs/EXEMPLARS.md, docs/DOMAIN_ORACLE_AND_M.md, docs/GENERATION_AND_TESTING.md.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import SCOPE_UOD, annotations_to_list, make_annotation
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, make_provenance
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

_WHEN = datetime(2026, 6, 29, tzinfo=timezone.utc)


def _uod(uod_id: str, name: str, description: str, egif: str):
    """Build the board by the gapless inbound construction — DC+ then INS, both
    real Dau rules from the blank sheet — so the board resides in its standing
    world-scroll and carries the two-step chain that put it there."""
    pc = ProofChain.from_blank()
    pc.apply("DC+", into=lambda g: g.sheet,
             note="Open the standing world-scroll: an empty double cut asserts "
                  "nothing, and until it exists there is nowhere to suppose a "
                  "model that is not an assertion.")
    pc.apply("INS", insert=egif,
             into=lambda g: nav.child_cuts(g, g.sheet)[0],
             note="Posit the board into the negative arena — insertion is sound "
                  "there, and the supposition is fenced: nothing contingent "
                  "stands at depth 0.")
    return pc.to_uod(uod_id=uod_id, name=name, description=description,
                     category=UoDCategory.DOMAIN_MODEL, created=_WHEN)


# --------------------------------------------------------------------------- #
# zoo_world — a closed taxonomy with Horn rules                               #
# --------------------------------------------------------------------------- #

ZOO_EGIF = (
    '(dog "Rex") (cat "Tom") (whale "Moby") (sparrow "Pip") '
    '~[ (dog *x) ~[ (mammal x) ] ] '
    '~[ (cat *x) ~[ (mammal x) ] ] '
    '~[ (whale *x) ~[ (mammal x) ] ] '
    '~[ (sparrow *x) ~[ (bird x) ] ] '
    '~[ (mammal *x) ~[ (warmblooded x) ] ] '
    '~[ (bird *x) ~[ (warmblooded x) ] ]'
)


def zoo_world() -> Tuple[TransformationChain, UniverseOfDiscourse, dict, List[dict]]:
    chain, uod = _uod(
        "zoo_world", "Zoo world — a closed taxonomy",
        "A small closed zoology authored as facts plus Horn rules: four named "
        "animals (Rex the dog, Tom the cat, Moby the whale, Pip the sparrow) and a "
        "subsumption spine — dog/cat/whale ⊑ mammal, sparrow ⊑ bird, mammal ⊑ "
        "warm-blooded, bird ⊑ warm-blooded. Materialized (forward-chained) it derives "
        "every animal's kind and warmth. As a game board: 'every mammal is "
        "warm-blooded' is a theorem of this world (holds); 'every warm-blooded thing "
        "is a mammal' is refuted by Pip the sparrow (fails). Closed-world: an "
        "unrecorded trait counts as absent.",
        ZOO_EGIF,
    )
    prov = make_provenance(
        proof_source={},
        method_sources=[{"type": "book", "author": "Peirce, Charles Sanders",
                         "title": "Collected Papers", "bibkey": "peirce1931collected",
                         "note": "existential-graph notation"}],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()
    anns = annotations_to_list([
        make_annotation(SCOPE_UOD,
            "A board built to exercise the holds/fails outcomes of the interpretation "
            "register. Six scrolls encode the taxonomy as Horn rules; the Agon "
            "materializes them (least Herbrand model) before peeling a proposal, so a "
            "universal like 'every dog is warm-blooded' is decided through the "
            "dog→mammal→warm-blooded chain. The closed flag is what licenses ∀: a "
            "silence is read as 'no', so a refuting individual (Pip) makes the over-broad "
            "universal definitely FALSE.",
            tags=["domain-model", "synthetic", "closed-world", "horn", "agon-board"]),
    ])
    return chain, uod, prov, anns


# --------------------------------------------------------------------------- #
# harbor_town — an open civic world                                          #
# --------------------------------------------------------------------------- #

HARBOR_EGIF = (
    '(town "Bayside") (harbor "Bayside") (island "Greyrock") '
    '(ferry "Bayside" "Greyrock") (lighthouse "Greyrock")'
)


def harbor_town() -> Tuple[TransformationChain, UniverseOfDiscourse, dict, List[dict]]:
    chain, uod = _uod(
        "harbor_town", "Harbor town — an open civic world",
        "A small open-world geography: Bayside is a harbor town; Greyrock is an "
        "island with a lighthouse; a ferry runs Bayside→Greyrock. Authored as facts "
        "only, with no closure — so the record is a sample of a larger world, not the "
        "whole of it. As a game board it produces the *independent* outcome: a "
        "proposal the facts neither confirm nor deny (e.g. 'Bayside hosts a market') "
        "reads UNKNOWN — a candidate new fact, not a falsehood. The contrast piece to "
        "zoo_world's closed taxonomy.",
        HARBOR_EGIF,
    )
    prov = make_provenance(
        proof_source={},
        method_sources=[{"type": "book", "author": "Peirce, Charles Sanders",
                         "title": "Collected Papers", "bibkey": "peirce1931collected"}],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()
    anns = annotations_to_list([
        make_annotation(SCOPE_UOD,
            "An open-world board: the binary ferry relation gives the peel something "
            "relational to witness, and the absence of closure means an unrecorded "
            "claim is UNKNOWN rather than FALSE — the open-world horizon that turns a "
            "miss into a proposal rather than a refutation (the 'new fact' disposition). "
            "Pair it with zoo_world to show how the same kind of universal reads "
            "differently open vs. closed.",
            tags=["domain-model", "synthetic", "open-world", "relational", "agon-board"]),
    ])
    return chain, uod, prov, anns


# --------------------------------------------------------------------------- #
# Driver                                                                      #
# --------------------------------------------------------------------------- #

BUILDERS = [zoo_world, harbor_town]


def main(argv=None) -> int:
    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    for build in BUILDERS:
        chain, uod, prov, anns = build()
        # sanity: the board resides in its standing world-scroll and reads back
        from world_scroll import find_world_scroll, m_view
        from egif_parser_dau import parse_egif as _parse
        assert find_world_scroll(uod.current_egi) is not None
        service.save_uod_with_chain(uod, chain, provenance=prov)  # §3.3 attests
        service.save_annotations(uod, anns)
        print(f"Saved domain model '{uod.uod_id}' — {uod.metadata.name} "
              f"({len(chain.steps)}-step DC+·INS construction)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
