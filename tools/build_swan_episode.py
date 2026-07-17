"""
Build ``swan_episode_unpacked`` — the black-swan episode with its four beats
recorded *individually*, and its choice recorded as a real fork in the DAG.

The old ``dialogue_swan_revision`` packs the whole of inning 4 into one
``challenge_to_M`` step (``model_revision`` does the retraction and the assertion in
one call, ``content: "both"``). ``proof_character`` says so out loud — it reads that
chain as *"4 of 4 steps REVISE the model"*, with the deduction inside them invisible.
Four different acts, of three different logical kinds, were hidden:

  1. **PROPOSE**  a black swan is *entertained* — a candidate, not yet admitted.
  2. **EXHIBIT**  the conflict is **DERIVED**: six ordinary Dau rules ending in the
                  EMPTY CUT. Absurdity, shown rather than declared. This is the beat
                  that never existed: the old panel recognised a refuting *shape* and
                  asserted a conflict; nothing ever *drew* one.
  3. **FORK**     two ways to restore consistency — relinquish the law, or reject the
                  report. A genuine CHOICE, so a genuine branch: both become siblings
                  of the same parent state, and the road not taken stays navigable.
  4. **DISPOSE**  retract + assert, *citing the exhibited conflict as its reason*.
                  Ampliative — no rule of inference compels it.

**The premiss the conflict needs.** A black swan refutes "all swans are white" only
given *nothing is both black and white*. That law lived in the Challenger's code, not
on M's sheet — so the contradiction could not be derived, only recognised. It is now
scribed, and the derivation is checkable.

**Entertaining is enclosure.** The EXHIBIT is conducted on an **iterated working
copy** of M (``revision_episode``): what is derived there does not transfer to M by
deduction — which is exactly right, because the decision to revise M is not a
deduction. The cut boundary is what enforces that.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import revision_episode as ep
from annotations import SCOPE_CHAIN, SCOPE_STEP, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from m_steps import peel_step, retract_step
from model_revision import DISPOSITION_CHALLENGE_M, DISPOSITION_NEW_FACT
from proof_authoring import ProofChain
from world_scroll import enlarge_m, wrap_m
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UOD_ID = "swan_episode_unpacked"

LAW = '~[ (swan *x) ~[ (white x) ] ]'                  # the induced habit
DISJOINT = '~[ (black *y) (white y) ]'                 # the premiss that makes it a refutation
OBSERVATION = '(swan "Nox") (black "Nox")'             # the anomaly

# M as it stands at the end of inning 3: two white swans, the law induced from them,
# and (now explicitly) the background disjointness the conflict will need.
M3 = (f'(swan "Ciel") (white "Ciel") (swan "Dover") (white "Dover") {LAW} {DISJOINT}')

PROPOSAL = '~[ (swan *x) ~[ (white x) ] ]'             # the audited claim: all swans white

# The two ways out. Under the cells residence (M_RESIDENCE §9) each is ONE
# licensed ERA inside a cell — the fallibilist pole: relinquish the law, or
# deny one atom of the report — no whole-world withdrawal needed.


def build_episode_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    wrapped, _ = wrap_m(parse_egif(M3))     # s0 — M3, resident in its world-scroll
    pc = ProofChain(wrapped)

    # ---- beat 0 · the standing audit ---------------------------------------
    peel_step(pc, PROPOSAL, closed=True,
              note="The audited claim at M3: 'all swans are white' holds — for now.")

    # ---- beat 1 · PROPOSE ---------------------------------------------------
    # The report ENTERS as a candidate — INS into the world-scroll's negative
    # arena, rule-licensed. (The supposition is now inconsistent — and that
    # irritation is precisely the point: the doubt is real, beat 2 makes it
    # visible, and the scroll QUARANTINES it: an inconsistent supposition,
    # never an inconsistent assertion.)
    pc.apply_derived(
        "PROPOSE",
        lambda g: enlarge_m(g, OBSERVATION),
        note=("Beat 1 — PROPOSE. A black swan, Nox, is reported. Entertained, not yet "
              "settled: the supposition now says two incompatible things, and the "
              "doubt is real — fenced by the scroll it lives in."),
        params={"beat": ep.PROPOSE, "observation": OBSERVATION,
                "act": "m_enlargement", "disposition": "abductive_hypothesis",
                "mode": "abduction", "derivation": ["INS"], "earned": True})

    # ---- beat 2 · EXHIBIT ---------------------------------------------------
    # The conflict is DERIVED on an iterated working copy — six Dau rules to the
    # empty cut. The step itself changes nothing on M's sheet: exhibiting a
    # contradiction is not revising a model.
    exhibit = ep.exhibit_conflict(
        f'{OBSERVATION} {LAW} {DISJOINT}',
        individual="Nox", law_relation="swan", disjoint_relation="black")
    assert exhibit.absurd, exhibit.summary

    pc.apply_derived(
        "EXHIBIT",
        lambda g: g,                                   # M is untouched: this is a proof
        note=("Beat 2 — EXHIBIT. The conflict is DERIVED, not declared: instantiate "
              "the law at Nox (UI), deiterate, discharge the double cut → (white Nox); "
              "instantiate disjointness at Nox, deiterate both conjuncts → the EMPTY "
              "CUT. Absurdity, in six Dau rules. The contradiction now *appears*."),
        params={"beat": ep.EXHIBIT, "derivation": exhibit.steps,
                "absurd": True, "working_copy": True,
                "reason": exhibit.reason})

    fork_state = pc.current_state_id                   # the state the choice is made AT

    # ---- beat 3+4a · the main line: relinquish the law ----------------------
    # ONE licensed ERA of the law inside its cell (M_RESIDENCE §9: erasure is
    # sound at even depth — the fallibilist pole; the observation was already
    # admitted at beat 1, so nothing else moves). The emptied place stands and
    # the DAG keeps the pre-choice world.
    alts = ep.alternatives("all swans are white", "Nox is a black swan")
    retract_step(
        pc,
        subgraph_egif=LAW,
        disposition=DISPOSITION_CHALLENGE_M, mode="abduction",
        reason="the contradiction exhibited in beat 2",
        note=("Beats 3–4 — FORK, then DISPOSE (this branch). Two ways out were "
              "open; this one keeps the observation and RELINQUISHES the law — "
              "one licensed ERA inside its cell (erasure is sound at even "
              "depth). Ampliative: the exhibited absurdity does not *compel* "
              "this — it compels only that something give. Choosing which is "
              "abduction."),
        branch="relinquish-the-law")
    pc.to_chain().steps[-1].parameters.update(
        {"beat": ep.DISPOSE, "alternative": alts[0].key})
    peel_step(pc, PROPOSAL, closed=True, branch="relinquish-the-law")

    # ---- beat 4b · the sibling: reject the report ---------------------------
    # The road not taken, kept navigable. A scientist's notebook keeps both.
    # Also one licensed ERA — deny the single atom (black Nox); the shared
    # line of identity (Nox himself, still a swan) survives the erasure.
    pc.at(fork_state)
    retract_step(
        pc,
        relation="black", labels=["Nox"],
        disposition="rejection", mode="convention",
        reason="the report is denied — a mis-sighting, a mislabelled bird",
        note=("Beat 4 (the ROAD NOT TAKEN) — keep the law, reject the report. The "
              "other way to restore consistency: deny that Nox is black (a "
              "mis-sighting, a mislabelled bird) — one licensed ERA of that atom; "
              "Nox himself, still a swan, survives on his line of identity. Cheap "
              "now; the cost falls due later if the report was true. Recorded as a "
              "sibling so the choice stays visible — the DAG is where 'having two "
              "alternatives in mind' lives."),
        branch="reject-the-report")
    pc.to_chain().steps[-1].parameters.update(
        {"beat": ep.DISPOSE, "alternative": alts[1].key, "not_taken": True})
    peel_step(pc, PROPOSAL, closed=True, branch="reject-the-report")

    return pc.to_uod(
        uod_id=UOD_ID,
        name="The black swan, unpacked (four beats and a fork)",
        description=(
            "One inning of the Endoporeutic Game, with everything that was packed into "
            "a single 'challenge_to_M' step laid out as the four acts it really is. "
            "PROPOSE: a black swan is entertained. EXHIBIT: the conflict is DERIVED — "
            "six ordinary Dau rules ending in the EMPTY CUT, so the contradiction is "
            "SHOWN, not asserted by a referee (this required scribing the premiss the "
            "conflict always needed: nothing is both black and white). FORK: two ways "
            "to restore consistency, recorded as two branches of the DAG — admit the "
            "swan and relinquish the law, or keep the law and reject the report. "
            "DISPOSE: the choice, which no rule of inference compels — the absurdity "
            "forces only that SOMETHING give, and choosing which is abduction. "
            "Entertaining is enclosure: the exhibit runs on an iterated working copy "
            "of M, and what is derived inside cannot be exported by deduction — which "
            "is exactly why a model revision is not a proof. M's elements reside in "
            "cells at even depth of a standing world-scroll (nothing contingent at "
            "depth 0; the second relocation): the proposal enters by a rule-licensed "
            "INS of a closed cell, and each disposition is ONE licensed ERA inside a "
            "cell — relinquish the law, or deny the report's atom — the fallibilist "
            "pole, with the DAG keeping the road not taken. proof_character reads "
            "this chain as AMPLIATIVE around a deductive core."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


def _provenance() -> dict:
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "the irritation of doubt; abduction as the revision of a habit"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def _annotations(chain: TransformationChain) -> list:
    anns = [
        make_annotation(SCOPE_UOD, PROPOSAL, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "The black-swan episode with its beats separated. What one "
            "'challenge_to_M' step used to hide: a proposal entertained, a "
            "contradiction DERIVED (not declared), a genuine fork between two ways to "
            "restore consistency, and an ampliative choice that no rule compels. The "
            "conflict is now a real derivation ending in the empty cut — which needed "
            "the premiss that was never on the sheet: nothing is both black and white.",
            tags=["dialogue", "model-revision", "demonstration", "abduction",
                  "ampliative", "teaching"]),
        make_annotation(SCOPE_CHAIN,
            "Four beats: PROPOSE (entertain) · EXHIBIT (deduction — six Dau rules to "
            "the empty cut, on an ITERATED WORKING COPY of M, so nothing derived here "
            "transfers to M by deduction) · FORK (a real DAG branch: both alternatives "
            "kept) · DISPOSE (abduction — the choice). proof_character: AMPLIATIVE "
            "around a deductive core.",
            tags=["four-beats", "abduction", "fork"]),
    ]
    for step in chain.steps:
        anns.append(make_annotation(SCOPE_STEP, step.user_annotation or step.rule_name,
                                    step_id=step.step_id, tags=["beat"]))
    return annotations_to_list(anns)


def main(argv=None) -> int:
    from proof_character import character_of_chain

    chain, uod = build_episode_chain()
    service = TomosService(Path(__file__).resolve().parent.parent / "tomos")
    service.save_uod_with_chain(uod, chain, provenance=_provenance())
    service.save_annotations(uod, _annotations(chain))

    froms = [s.from_state_id for s in chain.steps]
    fork = [f for f in set(froms) if froms.count(f) > 1]
    print(f"Saved '{UOD_ID}' — {len(chain.steps)} steps; fork at {fork}")
    for s in chain.steps:
        print(f"  {s.parameters.get('beat', '?'):8s} {s.rule_name:9s} "
              f"branch={s.branch_id or '(main)'}")
    print("\n  character:", character_of_chain(chain).summary)

    exhibit = ep.exhibit_conflict(f'{OBSERVATION} {LAW} {DISJOINT}',
                                  individual="Nox", law_relation="swan",
                                  disjoint_relation="black")
    print(f"  the conflict: {exhibit.summary}")
    print(f"  its derivation: {' → '.join(exhibit.steps)} → ~[ ]  (absurdity)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
