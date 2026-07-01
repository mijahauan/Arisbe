"""Seed a corpus UoD developed *automatically* by the Agon-evolution loop.

This is the demo for ``src/agon_evolution.py`` (docs/AUTOMATED_MODEL_DEVELOPMENT.md):
a model M is grown move-by-move by automated game rounds — produce → test →
negotiate → inject → decay — rather than hand-authored. The closed membrane
replays the swan pool, and the loop *reproduces the hand-played
``dialogue_swan_revision`` trajectory on its own* (the validation the design names):
new_fact → generalization → new_fact → challenge_to_M, the standing proposal
"every swan is white" flipping TRUE→…→FALSE exactly when the over-general law is
relinquished.

The result is saved with an ``audit-proposal`` annotation so Organon's **audit
lens** pre-fills the standing proposal and draws the verdict ribbon over the
automated trajectory.
"""

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from annotations import SCOPE_UOD, annotations_to_list, make_annotation
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from tomos_service import TomosService

from agon_evolution import run, CorpusProposer

UOD_ID = "agon_evolution_swan"
M0 = ('(swan "Alba") (white "Alba") (swan "Bianca") (white "Bianca") '
      '(swan "Ciel")')
LAW = '~[ (swan *x) ~[ (white x) ] ]'
POOL = [
    '(white "Ciel")',                       # observe — new_fact (induction)
    LAW,                                    # leap to the law — generalization
    '(swan "Dover")',                       # the law covers the newcomer — new_fact
    '(swan "Nox") ~[ (white "Nox") ]',     # a non-white swan — challenge_to_M
]


def build():
    return run(
        M0, CorpusProposer(POOL), rounds=4,
        uod_id=UOD_ID, name="A model developed automatically by the Agon (the swans)",
        standing_proposal=LAW,
        description=(
            "A domain model grown move-by-move by the automated Agon-evolution loop "
            "(src/agon_evolution.py): each state is a round of the Endoporeutic Game "
            "— produce a graph, peel it against the developing M, negotiate a "
            "disposition among the Agonothetes panel, inject the revision. Fed a "
            "closed membrane (the swan pool), the loop reproduces the hand-played "
            "dialogue_swan_revision trajectory on its own: observe Ciel (new_fact), "
            "leap to 'all swans are white' (generalization), admit a swan the law "
            "covers (new_fact), then meet a non-white swan and relinquish the "
            "over-general law (challenge_to_M, abduction). The engine of change is "
            "the game, not deterministic rules; selection from outside is the only "
            "bound on the unbounded sheet. See docs/AUTOMATED_MODEL_DEVELOPMENT.md."
        ),
    )


def provenance():
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "inquiry as the fixation of belief — observation, the inductive "
                     "leap, and the irritation of doubt that relinquishes a belief"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def annotations():
    return annotations_to_list([
        make_annotation(SCOPE_UOD, LAW, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "Developed automatically by the Agon-evolution loop — not hand-authored. "
            "Each state is one game round; the disposition that drove it is recorded "
            "on the step (disposition / mode), so the audit lens labels each "
            "transition. The standing proposal 'every swan is white' is audited "
            "across the run."),
    ])


def main(argv=None) -> int:
    res = build()
    dispositions = [o.disposition for o in res.outcomes]
    modes = [o.mode for o in res.outcomes]
    standing = [o.standing_verdict for o in res.outcomes]
    assert dispositions == ["new_fact", "generalization", "new_fact", "challenge_to_M"], \
        f"the loop did not reproduce the swan trajectory: {dispositions}"
    assert standing == ["true", "true", "true", "false"], \
        f"unexpected audited-proposal trajectory: {standing}"

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(res.uod, res.chain, provenance=provenance())
    service.save_annotations(res.uod, annotations())

    print(f"Saved '{UOD_ID}' — M developed automatically over {len(res.outcomes)} rounds.")
    for o in res.outcomes:
        print(f"  round {o.round_idx}: {o.disposition:15} [{o.mode:9}]  "
              f"every swan white → {o.standing_verdict.upper()}")
    print("Discoveries:")
    for d in res.discoveries:
        print(f"  • {d.kind}: {d.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
