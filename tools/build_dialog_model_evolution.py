"""
Build a domain model that **transforms through ongoing dialog** — a reference
model M revised inning by inning, persisted as M's own diachronic history.

The standing proposal under audit is **G = "every patient is insured"**
(``~[ (patient *x) ~[ (insured x) ] ]``). We peel G against M after each revision
and watch the verdict move as the dialogue admits — and is unsettled by — evidence.
Each revision is a model-revising disposition enacted by ``src/model_revision.py``
(the ``new_fact`` enlargement: an independent proposal accepted as evidence, a new
posit at low warrant):

    M0  (patient Ann) (patient Ben) (insured Ann)        G: FALSE — Ben is a counterexample
     │  inning 1 — the dialogue establishes Ben is insured  → admit (insured "Ben")
    M1  + (insured Ben)                                   G: TRUE  — the universal now holds
     │  inning 2 — a new patient Cal arrives               → admit (patient "Cal")
    M2  + (patient Cal)                                   G: FALSE — Cal unsettles it (a new individual)
     │  inning 3 — Cal's coverage is confirmed             → admit (insured "Cal")
    M3  + (insured Cal)                                   G: TRUE  — settled again, for now

The point is the manifest floor made operational: a model is **never frozen** — it
grows through the dialogue, a settled universal can be *unsettled* by a new
individual, and "fact" is the defeasible status of the last-standing trajectory
(docs/MANIFEST_AND_MEANING.md floor #1, #4; docs/LEVEL_ZERO_AND_THE_REGISTERS.md §5).

The model carries its own history: M0→M1→M2→M3 is a real ``TransformationChain``
(each step a recorded revision), browsable in Organon as the dialogue that made M
what it is. Original to Arisbe, low warrant. Import-safe. See docs/EXEMPLARS.md.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import SCOPE_CHAIN, SCOPE_STEP, SCOPE_UOD, annotations_to_list, make_annotation
from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from model_revision import DISPOSITION_NEW_FACT, revise_with_disposition
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from semantic_game import evaluate
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UOD_ID = "dialogue_model_revision"
M0_EGIF = '(patient "Ann") (patient "Ben") (insured "Ann")'
PROPOSAL_G = '~[ (patient *x) ~[ (insured x) ] ]'   # every patient is insured

# (disposition, fact, peirce-label, narration) for each inning's revision.
INNINGS = [
    (DISPOSITION_NEW_FACT, '(insured "Ben")', "1·M",
     "Inning 1 — the dialogue establishes Ben is insured; admit it as evidence."),
    (DISPOSITION_NEW_FACT, '(patient "Cal")', "2·M",
     "Inning 2 — a new patient, Cal, arrives; admit the individual."),
    (DISPOSITION_NEW_FACT, '(insured "Cal")', "3·M",
     "Inning 3 — Cal's coverage is confirmed; admit it, settling the audit again."),
]


def _verdict(model_egif_or_egi, proposal_egif: str = PROPOSAL_G) -> str:
    """Peel the standing proposal G against a model state (closed-world)."""
    m = (model_egif_or_egi if not isinstance(model_egif_or_egi, str)
         else parse_egif(model_egif_or_egi))
    facts, _ = materialize_egi(m)
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


def build_dialogue_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    pc = ProofChain.from_egif(M0_EGIF)                                       # s0 = M0
    for disposition, fact, label, note in INNINGS:
        pc.apply_derived(
            "ADMIT_FACT",
            lambda g, _d=disposition, _f=fact: revise_with_disposition(g, _d, fact_egif=_f),
            label=label, note=note,
            params={"disposition": disposition, "fact": fact},
        )
    return pc.to_uod(
        uod_id=UOD_ID,
        name="A model revised through dialog (the insurance audit)",
        description=(
            "A reference model M that transforms through ongoing dialog, persisted as "
            "its own history. The standing proposal G = 'every patient is insured' is "
            "peeled against M after each revision; the verdict moves FALSE→TRUE→FALSE→"
            "TRUE as the dialogue admits Ben's insurance (G holds), a new patient Cal "
            "(G unsettled), then Cal's coverage (G holds again). Each step is a "
            "model-revising 'new_fact' disposition (src/model_revision.py) — a new "
            "posit at low warrant. The exemplar of the manifest floor: a model is never "
            "frozen, and 'fact' is the defeasible status of the last-standing trajectory."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


def dialogue_provenance() -> dict:
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "to assert is to take responsibility; the living, revisable model"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def dialogue_annotations(chain: TransformationChain) -> list:
    anns = [
        make_annotation(SCOPE_UOD,
            "How a domain model transforms through ongoing dialog. The standing "
            "proposal 'every patient is insured' is audited against M after each "
            "revision; the verdict moves FALSE→TRUE→FALSE→TRUE as the dialogue admits "
            "evidence and a new individual unsettles a settled universal. M carries its "
            "own diachronic history — the dialogue that made it what it is, replayable "
            "in Organon. No model is ever frozen (docs/MANIFEST_AND_MEANING.md).",
            tags=["domain-model", "dialogue", "model-revision", "liveness", "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Each step is a model-revising 'new_fact' disposition (src/model_revision.py): "
            "an independent proposal the dialogue accepts as evidence, juxtaposed onto M's "
            "sheet as a new posit at low warrant. Enlargement here; retraction (free to "
            "demote, the ERA dual) is the other licensed move.",
            tags=["new-fact", "enlargement", "low-warrant"]),
    ]
    # Tag each state with the verdict it yields, so a reader can see the audit move.
    states_in_order = [chain.initial_state_id] + [s.to_state_id for s in chain.steps]
    for i, sid in enumerate(states_in_order):
        v = _verdict(chain.states[sid])
        stage = "M0 (the opening record)" if i == 0 else f"M{i}"
        anns.append(make_annotation(SCOPE_STEP if i > 0 else SCOPE_UOD,
            f"{stage}: 'every patient is insured' peels to {v.upper()}.",
            step_id=(chain.steps[i - 1].step_id if i > 0 else None),
            tags=["audit", "verdict"]))
    return annotations_to_list(anns)


def main(argv=None) -> int:
    chain, uod = build_dialogue_chain()
    verdicts = [_verdict(chain.states[chain.initial_state_id])] + [
        _verdict(chain.states[s.to_state_id]) for s in chain.steps]
    assert verdicts == ["false", "true", "false", "true"], (
        f"expected the audit to flip FALSE→TRUE→FALSE→TRUE, got {verdicts}")

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=dialogue_provenance())
    service.save_annotations(uod, dialogue_annotations(chain))
    print(f"Saved '{uod.uod_id}' — M revised over {len(chain.steps)} innings.")
    labels = ["M0"] + [f"M{i+1}" for i in range(len(chain.steps))]
    for lab, v in zip(labels, verdicts):
        print(f"  {lab}: every patient insured → {v.upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
