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
from m_steps import admit_step, peel_step
from model_revision import DISPOSITION_NEW_FACT
from proof_authoring import ProofChain
from world_scroll import wrap_m
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


def build_dialogue_chain() -> Tuple[TransformationChain, UniverseOfDiscourse, list]:
    """Returns (chain, uod, verdicts) — the verdicts are recorded PEEL steps,
    each earned by the peel actually run at build time. M resides at level 1
    of a standing world-scroll (the validity discipline: nothing contingent at
    depth 0), and each inning is an explicit rule-licensed ADMIT_TO_M (a
    genuine INS into the negative arena)."""
    wrapped, _ = wrap_m(parse_egif(M0_EGIF))
    pc = ProofChain(wrapped)                                                 # s0 = M0
    verdicts = [peel_step(pc, PROPOSAL_G, closed=True,
                          note="M0 (the opening record): Ben is a "
                               "counterexample — the audit opens FALSE.").verdict.value]
    for disposition, fact, label, note in INNINGS:
        admit_step(pc, fact, disposition=disposition, mode="induction",
                   warrant="the dialogue's accepted evidence", note=note)
        pc.to_chain().steps[-1].parameters["peirce_label"] = label
        verdicts.append(peel_step(pc, PROPOSAL_G, closed=True).verdict.value)
    chain, uod = pc.to_uod(
        uod_id=UOD_ID,
        name="A model revised through dialog (the insurance audit)",
        description=(
            "A reference model M that transforms through ongoing dialog, persisted as "
            "its own history. The standing proposal G = 'every patient is insured' is "
            "peeled against M after each revision; the verdict moves FALSE→TRUE→FALSE→"
            "TRUE as the dialogue admits Ben's insurance (G holds), a new patient Cal "
            "(G unsettled), then Cal's coverage (G holds again). Each step is a "
            "model-revising 'new_fact' disposition recorded as an explicit ADMIT_TO_M "
            "step — a genuine INS into the standing world-scroll's negative arena "
            "(src/m_steps.py; M resides at level 1, nothing contingent at depth 0), "
            "with each verdict a recorded PEEL step. The exemplar of the manifest "
            "floor: a model is never frozen, and 'fact' is the defeasible status of "
            "the last-standing trajectory."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )
    return chain, uod, verdicts


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
        # The standing proposal this dialogue audits — declared in EGIF (text = the
        # bare EGIF, tag-keyed) so the Organon "audit" lens (GET
        # /organon/uods/{id}/audit) can pre-fill it and peel it against every state of M.
        make_annotation(SCOPE_UOD, PROPOSAL_G, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "How a domain model transforms through ongoing dialog. The standing "
            "proposal 'every patient is insured' is audited against M after each "
            "revision; the verdict moves FALSE→TRUE→FALSE→TRUE as the dialogue admits "
            "evidence and a new individual unsettles a settled universal. M carries its "
            "own diachronic history — the dialogue that made it what it is, replayable "
            "in Organon. No model is ever frozen (docs/MANIFEST_AND_MEANING.md).",
            tags=["domain-model", "dialogue", "model-revision", "liveness", "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Each inning is an explicit ADMIT_TO_M step (src/m_steps.py): an "
            "independent proposal the dialogue accepts as evidence, admitted by a "
            "genuine INS into the world-scroll's negative arena (supposing more is "
            "free); the warrant justifies the choice and rides on the step. Each "
            "verdict is a recorded PEEL step, re-checkable forever. Relinquishment "
            "(the other licensed move) is world-withdrawal — see "
            "dialogue_swan_revision.",
            tags=["new-fact", "enlargement", "world-scroll", "low-warrant"]),
    ]
    # Marginalia: tag each PEEL step with its recorded verdict.
    m_index = 0
    for step in chain.steps:
        p = step.parameters or {}
        if p.get("act") == "peel":
            v = str(p.get("verdict", "?")).upper()
            anns.append(make_annotation(SCOPE_STEP,
                f"M{m_index}: 'every patient is insured' peels to {v}.",
                step_id=step.step_id, tags=["audit", "verdict"]))
            m_index += 1
    return annotations_to_list(anns)


def main(argv=None) -> int:
    chain, uod, verdicts = build_dialogue_chain()
    assert verdicts == ["false", "true", "false", "true"], (
        f"expected the audit to flip FALSE→TRUE→FALSE→TRUE, got {verdicts}")

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=dialogue_provenance())
    service.save_annotations(uod, dialogue_annotations(chain))
    print(f"Saved '{uod.uod_id}' — M revised over {len(chain.steps)} steps "
          f"(world-scroll residence; explicit PEEL/ADMIT_TO_M).")
    for i, v in enumerate(verdicts):
        print(f"  M{i}: every patient insured → {v.upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
