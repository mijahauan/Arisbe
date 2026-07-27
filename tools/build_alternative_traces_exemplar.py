"""Build the trace-bearing corpus exemplar `swan_alternatives` — the UoD
that de-vacuates the polarity gate's trace- and survey-recompute
obligations (spec 2026-07-26-close-the-arc §5, AC17) and discharges AC7's
letter on real saved ink.

The story: the swan M carries an ungrounded dragon→fears law. A peel
surfaces two unknowns; the thin-spot survey surfaces the dragon question;
traces discover dragon is MATERIAL (asserting it derives fears) while black
is bare; two entertained futures fork the DAG; the branch survey reads the
contested weather; an admit introduces the dragon ground — the register
settles citing that step. Every record attests against the saved chain."""
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from annotations import SCOPE_CHAIN, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from tomos_service import TomosService
from universe_of_discourse import UoDCategory
from world_scroll import wrap_m

from alternative_index import AlternativeRegister, record_from_trace_step
from alternative_survey import (branch_survey_step, records_from_survey_step,
                                thin_spot_step)
from alternative_trace import BoundedRegister, trace_batch
from m_steps import admit_step, peel_step

UOD_ID = "swan_alternatives"
M0 = ('(swan "Ciel") (white "Ciel") '
      '~[ (swan *x) ~[ (white x) ] ] '
      '~[ (dragon *y) ~[ (fears y) ] ]')
PROPOSAL = '(swan "Dover") (black "Dover")'


def build_chain():
    wrapped, _ = wrap_m(parse_egif(M0))
    pc = ProofChain(wrapped)
    register = AlternativeRegister(capacity=16)
    s_reg, a_reg = BoundedRegister(32), BoundedRegister(32)

    # 1. PEEL surfaces the proposal's unknowns.
    result = peel_step(pc, PROPOSAL, note="the Dover proposal")
    peel_id = pc.to_chain().steps[-1].step_id

    # 2. The thin-spot survey surfaces the ungrounded dragon law.
    thin_spot_step(pc, note="what is M thin on?")
    thin_id = pc.to_chain().steps[-1].step_id
    for rec in records_from_survey_step(pc.to_chain().steps[-1]):
        register.note(rec, round_idx=0)

    # 3. Trace peel unknowns + survey unknowns (one batch, budgeted).
    unknowns = list(result.unknown_atoms) + [
        (r.relation, r.labels) for r in register.records()]
    batch = trace_batch(pc, unknowns, s_register=s_reg, a_register=a_reg)
    chain = pc.to_chain()
    traced = [s for s in chain.steps
              if (s.parameters or {}).get("act") == "alternatives_traced"]
    for ts in traced[-len(batch.results):]:
        rec = record_from_trace_step(ts)
        if register.get(rec.key) is None:
            rec = dataclasses.replace(rec, emerged_from=peel_id)
        register.note(rec, round_idx=0)

    # 4. Two entertained futures fork the DAG; the branch survey reads them.
    base = pc.current_state_id
    admit_step(pc, '(cloudy "sky")', disposition="new_fact",
               note="future A: weather turns")
    pc.at(base)
    admit_step(pc, '(calm "sea")', disposition="new_fact",
               note="future B: fair passage")
    pc.at(base)
    branch_survey_step(pc, at=base, note="what do the futures contest?")
    for rec in records_from_survey_step(pc.to_chain().steps[-1]):
        register.note(rec, round_idx=1)

    # 5. The introducing resolution: the dragon question closes.
    admit_step(pc, '(dragon "Smaug")', disposition="new_fact",
               note="a dragon is attested")
    register.settle_from_chain(pc.to_chain())
    return pc, register


def build():
    pc, register = build_chain()
    chain, uod = pc.to_uod(
        uod_id=UOD_ID,
        name="Alternatives traced — the swan's thin dragon",
        description=(
            "The trace-bearing corpus exemplar (spec "
            "2026-07-26-close-the-arc §5, AC17): the standing swan M "
            "(swan→white, plus a wholly ungrounded dragon→fears law) meets "
            "a proposal about a new swan, Dover, who is black. A PEEL "
            "surfaces the proposal's unknowns; a thin-spot survey names the "
            "ungrounded dragon law as an open question; a budgeted trace "
            "batch discovers dragon's assertion is MATERIAL (it derives "
            "fears) while black is not. Two entertained futures — a "
            "weather turn and a fair passage — fork the diachronic DAG; a "
            "branch survey reads the contested weather as modal "
            "alternatives. Finally a dragon is attested (Smaug), and the "
            "register settles the dragon question, citing the admitting "
            "step. Every record in the sidecar register re-attests against "
            "the saved chain (AS1-AS4) — this is what de-vacuates the "
            "polarity gate's trace- and survey-recompute obligations, "
            "which every other corpus UoD skips for want of the ink."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )
    return chain, uod, register


def provenance():
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "webpage", "author": "Arisbe",
             "title": "spec 2026-07-26-close-the-arc",
             "bibkey": "arisbe2026closethearc",
             "note": "index-over-ink alternatives: traces + surveys "
                     "(AS1-AS4, D-1..D-3)"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def annotations():
    return annotations_to_list([
        make_annotation(SCOPE_UOD, PROPOSAL, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "Alternatives held in abeyance over the swan M: a peel's "
            "unknowns, a thin-spot survey's ungrounded law, and a branch "
            "survey's contested futures — all traced and indexed, never "
            "held as free-floating evidence (index-over-ink). M is itself "
            "revised along the way (two admits enlarge it, one settling "
            "the dragon question) — a dialogue over open questions, not "
            "just a static board.",
            tags=["dialogue", "demonstration", "alternatives", "trace", "survey"]),
        make_annotation(SCOPE_CHAIN,
            "The dragon→fears law is thin (zero grounded instances) until "
            "the final admit; the trace discovers its materiality BEFORE "
            "the ground arrives, and the register settlement afterwards "
            "cites the admitting step — discovery and resolution are "
            "separate, independently re-checkable acts.",
            tags=["thin-spot", "materiality", "settlement"]),
    ])


def main(argv=None) -> int:
    chain, uod, register = build()
    service = TomosService(Path(__file__).resolve().parent.parent / "tomos")
    service.save_uod_with_chain(uod, chain, provenance=provenance())
    service.save_annotations(uod, annotations())
    service.save_alternative_register(UOD_ID, register, chain=chain)
    print(f"Saved '{UOD_ID}' — {len(chain.steps)} steps, "
          f"{len(register)} alternatives register entries.")
    for s in chain.steps:
        p = s.parameters or {}
        print(f"  {s.rule_name:18s} act={p.get('act', '—'):22s} "
              f"note={s.user_annotation or '—'}")
    resolved = [r for r in register.records() if r.status == "resolved"]
    print(f"  resolved: {[r.key for r in resolved]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
