"""
Build a domain model revised through dialog **across the inning-outcome taxonomy**
— the companion to ``dialogue_model_revision`` (which walks only the ``new_fact``
disposition). Here M transforms by *different* kinds of inning outcome, each a
distinct **Peircean mode of inference** (docs/ENDOPOREUTIC_GAME_GUIDE.md §"Taxonomy
of Game Outcomes" §IV), enacted by ``src/model_revision.py``'s ``REVISION_TAXONOMY``.

The story is the guide's own canonical example — **the swans** (Case 8 → Case 2b):
the standing proposal under audit is **G = "every swan is white"**
(``~[ (swan *x) ~[ (white x) ] ]``), peeled against M after each revision.

    M0  swans Alba/Bianca (white), Ciel (colour unrecorded)        G: FALSE — Ciel uncovered
     │  inning 1 — observe Ciel is white          new_fact        (3a · induction)
    M1  + (white Ciel)                                             G: TRUE
     │  inning 2 — leap to the law "all swans white"  generalization (Case 8 · induction)
    M2  + ~[ (swan x) ~[ (white x) ] ]                             G: TRUE  (now a law, not a tally)
     │  inning 3 — a new swan, Dover, arrives     new_fact        (3a · induction)
    M3  + (swan Dover)                                             G: TRUE  — the *law covers Dover*
     │  inning 4 — a black swan, Nox: revise M    challenge_to_M  (2b · abduction)
    M4  − the law, + (swan Nox)(black Nox)                         G: FALSE — the law is relinquished

Two teaching points the simple insurance dialogue cannot show:

  * **A law absorbs the newcomer.** At M3 a new individual (Dover) arrives with no
    recorded colour, yet G stays TRUE — the *generalization* materializes (white
    Dover). Contrast ``dialogue_model_revision``, where a new patient (Cal) with no
    rule in M flips the verdict FALSE. Deduction over an inductive law vs a bare tally.
  * **The irritation of doubt revises M.** The black swan (Nox) refutes the law; the
    inning's outcome is *challenge-to-M* (2b) — the over-general law is **relinquished**
    (a genuine Dau ERA in the positive sheet) and the anomaly admitted. M is corrected
    by abduction — "the only logical operation which introduces any new idea."

So the dialogue exercises **all three modes** (induction · deduction · abduction) and
both structural kinds of revision (enlargement · relinquishment). M carries its own
diachronic history, replayable in Organon; the audit lens draws the verdict
trajectory FALSE→TRUE→TRUE→TRUE→FALSE with each transition labelled by its disposition.
Original to Arisbe, low warrant. Import-safe. See docs/EXEMPLARS.md §6.
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
from model_revision import (
    DISPOSITION_CHALLENGE_M,
    DISPOSITION_GENERALIZATION,
    DISPOSITION_NEW_FACT,
    revise_with_disposition,
    revision_taxonomy,
)
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from semantic_game import evaluate
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UOD_ID = "dialogue_swan_revision"
M0_EGIF = '(swan "Alba") (white "Alba") (swan "Bianca") (white "Bianca") (swan "Ciel")'
PROPOSAL_G = '~[ (swan *x) ~[ (white x) ] ]'        # every swan is white
SWAN_LAW = '~[ (swan *x) ~[ (white x) ] ]'          # the inductive law

# Each inning: (disposition, revise-kwargs, peirce-label, narration). The
# disposition's Peircean mode is read from model_revision.REVISION_TAXONOMY.
INNINGS = [
    (DISPOSITION_NEW_FACT, {"fact_egif": '(white "Ciel")'}, "1·M",
     "Inning 1 — observe that Ciel is white; admit the fact. M grows by induction."),
    (DISPOSITION_GENERALIZATION, {"rule_egif": SWAN_LAW}, "2·M",
     "Inning 2 — the inductive leap from the instances to the law 'all swans are "
     "white' (the most Peircean move); admit the rule."),
    (DISPOSITION_NEW_FACT, {"fact_egif": '(swan "Dover")'}, "3·M",
     "Inning 3 — a new swan, Dover, arrives with no recorded colour. The law covers "
     "it: G stays TRUE where a bare fact-list would have been unsettled."),
    (DISPOSITION_CHALLENGE_M, {"subgraph_egif": SWAN_LAW,
                               "fact_egif": '(swan "Nox") (black "Nox")'}, "4·M",
     "Inning 4 — a black swan, Nox. The refutation is evidence against M (the "
     "irritation of doubt): relinquish the over-general law and admit the anomaly. "
     "M is revised by abduction."),
]


def _verdict(model_egif_or_egi, proposal_egif: str = PROPOSAL_G) -> str:
    """Peel the standing proposal G against a model state (closed-world), forward-
    chaining M's Horn fragment first so the swan *law* covers new individuals."""
    m = (model_egif_or_egi if not isinstance(model_egif_or_egi, str)
         else parse_egif(model_egif_or_egi))
    facts, _ = materialize_egi(m)
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


def build_swan_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    pc = ProofChain.from_egif(M0_EGIF)                                       # s0 = M0
    for disposition, kwargs, label, note in INNINGS:
        mode = revision_taxonomy(disposition)["mode"]
        pc.apply_derived(
            "REVISE_M",
            lambda g, _d=disposition, _k=kwargs: revise_with_disposition(g, _d, **_k),
            label=label, note=note,
            params={"disposition": disposition, "mode": mode, **kwargs},
        )
    return pc.to_uod(
        uod_id=UOD_ID,
        name="A model revised across the inning taxonomy (the swans)",
        description=(
            "A reference model M revised through dialog by *different* inning outcomes, "
            "each a distinct Peircean mode (docs/ENDOPOREUTIC_GAME_GUIDE.md). The "
            "standing proposal G = 'every swan is white' is peeled against M after each "
            "revision; the verdict moves FALSE→TRUE→TRUE→TRUE→FALSE as the dialogue "
            "observes Ciel (new_fact, induction), leaps to the law 'all swans are white' "
            "(generalization, induction), admits a new swan the law covers (new_fact — "
            "G stays TRUE where a bare fact-list would flip), then meets a black swan and "
            "relinquishes the over-general law (challenge-to-M, abduction). Enacted by "
            "src/model_revision.py's REVISION_TAXONOMY; the taxonomy of game outcomes "
            "made operational. M carries its own diachronic history."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


def swan_provenance() -> dict:
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "abduction — the only logical operation which introduces a new idea; "
                     "the irritation of doubt drives inquiry"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def swan_annotations(chain: TransformationChain) -> list:
    anns = [
        # The standing proposal this dialogue audits — declared in EGIF (text = the
        # bare EGIF, tag-keyed) so the Organon "audit" lens pre-fills it.
        make_annotation(SCOPE_UOD, PROPOSAL_G, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "A domain model revised across the *taxonomy* of inning outcomes — not one "
            "disposition repeated but four distinct ones, each a Peircean mode. 'Every "
            "swan is white' is audited against M: induction observes Ciel and leaps to "
            "the law; the law then covers a new swan (deduction over an inductive "
            "generalization — G stays TRUE where a bare tally would flip); abduction "
            "meets the black swan and relinquishes the over-general law. The taxonomy of "
            "game outcomes (docs/ENDOPOREUTIC_GAME_GUIDE.md) made operational.",
            tags=["domain-model", "dialogue", "model-revision", "taxonomy",
                  "induction", "abduction", "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Each step is a model-revising disposition from src/model_revision.py's "
            "REVISION_TAXONOMY: new_fact (3a, induction · enlargement), generalization "
            "(Case 8, induction · a law), challenge_to_M (2b, abduction · relinquish the "
            "law by a genuine Dau ERA + admit the anomaly). Enlargement is INS at the "
            "sheet; relinquishment is ERA in the positive sheet — the same calculus that "
            "draws every other graph.",
            tags=["taxonomy", "enlargement", "relinquishment", "low-warrant"]),
    ]
    # Tag each state with the verdict it yields + the disposition that produced it.
    states_in_order = [chain.initial_state_id] + [s.to_state_id for s in chain.steps]
    for i, sid in enumerate(states_in_order):
        v = _verdict(chain.states[sid])
        if i == 0:
            anns.append(make_annotation(SCOPE_UOD,
                f"M0 (the opening record): 'every swan is white' peels to {v.upper()} "
                "— Ciel's colour is unrecorded.",
                tags=["audit", "verdict"]))
        else:
            step = chain.steps[i - 1]
            disp = step.parameters.get("disposition", "?")
            mode = step.parameters.get("mode", "?")
            anns.append(make_annotation(SCOPE_STEP,
                f"M{i}: 'every swan is white' peels to {v.upper()} "
                f"(after {disp} · {mode}).",
                step_id=step.step_id, tags=["audit", "verdict", "taxonomy"]))
    return annotations_to_list(anns)


def main(argv=None) -> int:
    chain, uod = build_swan_chain()
    verdicts = [_verdict(chain.states[chain.initial_state_id])] + [
        _verdict(chain.states[s.to_state_id]) for s in chain.steps]
    assert verdicts == ["false", "true", "true", "true", "false"], (
        f"expected FALSE→TRUE→TRUE→TRUE→FALSE, got {verdicts}")
    # The exemplar must exercise more than one Peircean mode (the whole point).
    modes = {s.parameters.get("mode") for s in chain.steps}
    assert {"induction", "abduction"} <= modes, f"expected ≥2 modes, got {modes}"

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=swan_provenance())
    service.save_annotations(uod, swan_annotations(chain))
    print(f"Saved '{uod.uod_id}' — M revised over {len(chain.steps)} innings.")
    labels = ["M0"] + [f"M{i+1}" for i in range(len(chain.steps))]
    for i, (lab, v) in enumerate(zip(labels, verdicts)):
        disp = chain.steps[i - 1].parameters.get("disposition") if i > 0 else "(opening)"
        print(f"  {lab}: every swan white → {v.upper():6}  [{disp}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
