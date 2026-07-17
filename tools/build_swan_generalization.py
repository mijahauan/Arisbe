"""
Build a domain model revised through dialog **across the inning-outcome taxonomy**
— the companion to ``dialogue_model_revision`` (which walks only the ``new_fact``
disposition). Here M transforms by *different* kinds of inning outcome, each a
distinct **Peircean mode of inference** (docs/ENDOPOREUTIC_GAME_GUIDE.md §"Taxonomy
of Game Outcomes" §IV).

**Under the validity discipline** (docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §3–§4,
the elements relocated to cells at even depth by §9, ratified 2026-07-16): M's
elements reside in **cells beside the hold** of a standing world-scroll
``~[ ~[cell] … ~[ ] ]`` — nothing contingent at depth 0 — and every change to M is
an **explicit, rule-licensed single move** (``src/m_steps.py``): enlargement =
``ADMIT_TO_M`` (a genuine INS of a closed cell), the challenge = ``REVISE_M``
(ONE composite step: a licensed ERA of the law inside its cell + the INS of the
anomaly's cell — the emptied husk stands as a visible scar), and each verdict is a
recorded **PEEL** step whose parameters carry the peel actually run.

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
     │  inning 4 — a black swan, Nox: ONE licensed ERA  challenge_to_M  (2b · abduction)
    M4  − the law (its husk a scar), + (swan Nox)(black Nox)       G: FALSE

Two teaching points the simple insurance dialogue cannot show:

  * **A law absorbs the newcomer.** At M3 a new individual (Dover) arrives with no
    recorded colour, yet G stays TRUE — the *generalization* materializes (white
    Dover). Deduction over an inductive law vs a bare tally.
  * **The refuted law dies in one move.** The black swan (Nox) refutes the law; the
    inning's outcome is *challenge-to-M* (2b) — and under the cells residence the
    over-general law is relinquished by a **single licensed ERA** inside its cell
    (erasure is sound at even depth — the fallibilist pole), the anomaly admitted
    as a fresh cell, and the emptied husk left standing as the scar the synchronic
    drawing carries. M is corrected by abduction — "the only logical operation
    which introduces any new idea." The DAG keeps the pre-challenge world.

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

from annotations import SCOPE_CHAIN, SCOPE_STEP, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from m_steps import admit_step, challenge_step, peel_step
from model_revision import (
    DISPOSITION_CHALLENGE_M,
    DISPOSITION_GENERALIZATION,
    DISPOSITION_NEW_FACT,
    revision_taxonomy,
)
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory
from world_scroll import wrap_m

UOD_ID = "dialogue_swan_revision"
M0_EGIF = '(swan "Alba") (white "Alba") (swan "Bianca") (white "Bianca") (swan "Ciel")'
PROPOSAL_G = '~[ (swan *x) ~[ (white x) ] ]'        # every swan is white
SWAN_LAW = '~[ (swan *x) ~[ (white x) ] ]'          # the inductive law


def _verdict(model_egif_or_egi, proposal_egif: str = PROPOSAL_G) -> str:
    """Peel the standing proposal G against a model state (closed-world),
    forward-chaining M's Horn fragment first so the swan *law* covers new
    individuals. A resident state is read through its cells (the read path
    is m_view-aware). Kept public: tests reuse it."""
    from domain_oracle import CorpusOracle
    from model_materialization import materialize_egi
    from semantic_game import evaluate

    m = (model_egif_or_egi if not isinstance(model_egif_or_egi, str)
         else parse_egif(model_egif_or_egi))
    facts, _ = materialize_egi(m)
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


# The three enlargement innings: (disposition, fact/rule EGIF, peirce-label,
# narration). The disposition's Peircean mode comes from REVISION_TAXONOMY.
ENLARGEMENTS = [
    (DISPOSITION_NEW_FACT, '(white "Ciel")', "1·M",
     "Inning 1 — observe that Ciel is white; admit the fact into the standing "
     "residence as its own cell (a genuine INS). M grows by induction."),
    (DISPOSITION_GENERALIZATION, SWAN_LAW, "2·M",
     "Inning 2 — the inductive leap from the instances to the law 'all swans are "
     "white' (the most Peircean move); admit the rule as its own cell."),
    (DISPOSITION_NEW_FACT, '(swan "Dover")', "3·M",
     "Inning 3 — a new swan, Dover, arrives with no recorded colour. The law covers "
     "it: G stays TRUE where a bare fact-list would have been unsettled."),
]


def build_swan_chain() -> Tuple[TransformationChain, UniverseOfDiscourse, list]:
    """Returns (chain, uod, verdicts) — verdicts are the five recorded PEEL
    results over M0..M4, each earned by an actual peel at build time."""
    wrapped, _ = wrap_m(parse_egif(M0_EGIF))
    pc = ProofChain(wrapped)                                             # s0 = M0

    verdicts = [peel_step(pc, PROPOSAL_G, closed=True,
                          note="M0 (the opening record): Ciel's colour is "
                               "unrecorded — the audit opens FALSE.").verdict.value]

    for disposition, egif, label, note in ENLARGEMENTS:
        mode = revision_taxonomy(disposition)["mode"]
        admit_step(pc, egif, disposition=disposition, mode=mode,
                   warrant="the dialogue's reported observation", note=note)
        # label rides on the params the same way apply() would carry it
        pc.to_chain().steps[-1].parameters["peirce_label"] = label
        verdicts.append(peel_step(pc, PROPOSAL_G, closed=True).verdict.value)

    challenge_step(
        pc,
        subgraph_egif=SWAN_LAW,
        fact_egif='(swan "Nox") (black "Nox")',
        disposition=DISPOSITION_CHALLENGE_M,
        mode=revision_taxonomy(DISPOSITION_CHALLENGE_M)["mode"],
        reason="the black swan refutes the law — the irritation of doubt",
        note="Inning 4 — a black swan, Nox. The refuted law dies in ONE "
             "licensed move: ERA inside its cell (erasure is sound at even "
             "depth — the fallibilist pole), the anomaly admitted as a fresh "
             "cell, the emptied husk standing as the scar. Abduction; the DAG "
             "keeps the pre-challenge world.")
    pc.to_chain().steps[-1].parameters["peirce_label"] = "4·M"
    verdicts.append(peel_step(pc, PROPOSAL_G, closed=True).verdict.value)

    chain, uod = pc.to_uod(
        uod_id=UOD_ID,
        name="A model revised across the inning taxonomy (the swans)",
        description=(
            "A reference model M — its elements resident in cells at even depth of "
            "a standing world-scroll (nothing contingent at depth 0; the validity "
            "discipline, second relocation) — revised through dialog by *different* "
            "inning outcomes, each a distinct Peircean mode "
            "(docs/ENDOPOREUTIC_GAME_GUIDE.md). The standing proposal G = 'every "
            "swan is white' is peeled against M after each revision, each verdict a "
            "recorded PEEL step; the trajectory moves FALSE→TRUE→TRUE→TRUE→FALSE as "
            "the dialogue observes Ciel (new_fact, induction — ADMIT_TO_M, a genuine "
            "INS of a closed cell), leaps to the law 'all swans are white' "
            "(generalization, induction), admits a new swan the law covers (new_fact — "
            "G stays TRUE where a bare fact-list would flip), then meets a black swan "
            "and relinquishes the over-general law by ONE licensed ERA inside its "
            "cell (challenge-to-M, abduction — the emptied husk stands as the scar; "
            "the DAG keeps the pre-challenge world). The taxonomy of game outcomes "
            "made operational, every step rule-licensed."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )
    return chain, uod, verdicts


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
            "meets the black swan and relinquishes the over-general law in one "
            "licensed move. M's elements reside in cells at even depth of a standing "
            "world-scroll — nothing contingent at depth 0 — and every verdict is a "
            "recorded PEEL step. The taxonomy of game outcomes "
            "(docs/ENDOPOREUTIC_GAME_GUIDE.md) made operational.",
            tags=["domain-model", "dialogue", "model-revision", "taxonomy",
                  "induction", "abduction", "demonstration", "world-scroll"]),
        make_annotation(SCOPE_CHAIN,
            "Every M-change is an explicit rule-licensed step (src/m_steps.py): "
            "ADMIT_TO_M = enlargement, a genuine INS of a closed cell into the "
            "residence (each admitted batch its own cell); REVISE_M = the challenge "
            "composite, ONE step executing the licensed ERA of the law inside its "
            "cell (erasure is sound at even depth — retraction is finally one move, "
            "the fallibilist pole) + the INS of the anomaly's cell; the emptied husk "
            "stands as a visible scar and the DAG keeps the pre-challenge world. "
            "Each PEEL step records the verdict actually computed at that state — "
            "the record is re-checkable forever.",
            tags=["taxonomy", "enlargement", "relinquishment", "world-scroll",
                  "low-warrant"]),
    ]
    # Marginalia: tag each PEEL step with its recorded verdict (the structured
    # record IS the step's parameters; these keep the lens legible).
    m_index = 0
    for step in chain.steps:
        p = step.parameters or {}
        if p.get("act") == "peel":
            v = str(p.get("verdict", "?")).upper()
            anns.append(make_annotation(SCOPE_STEP,
                f"M{m_index}: 'every swan is white' peels to {v}.",
                step_id=step.step_id, tags=["audit", "verdict", "taxonomy"]))
            m_index += 1
    return annotations_to_list(anns)


def main(argv=None) -> int:
    chain, uod, verdicts = build_swan_chain()
    assert verdicts == ["false", "true", "true", "true", "false"], (
        f"expected FALSE→TRUE→TRUE→TRUE→FALSE, got {verdicts}")
    # The exemplar must exercise more than one Peircean mode (the whole point).
    modes = {s.parameters.get("mode") for s in chain.steps
             if (s.parameters or {}).get("act") != "peel"}
    assert {"induction", "abduction"} <= modes, f"expected ≥2 modes, got {modes}"
    # The challenge is ONE composite licensed step: ERA then INS.
    challenge = next(s for s in chain.steps
                     if (s.parameters or {}).get("act") == "m_revision")
    assert challenge.parameters["derivation"] == ["ERA", "INS"], (
        f"expected the single-step ERA·INS challenge, got "
        f"{challenge.parameters.get('derivation')}")

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=swan_provenance())
    service.save_annotations(uod, swan_annotations(chain))
    print(f"Saved '{uod.uod_id}' — M revised over {len(chain.steps)} steps "
          f"(cells residence; explicit PEEL/ADMIT_TO_M/REVISE_M).")
    for i, v in enumerate(verdicts):
        print(f"  M{i}: every swan white → {v.upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
