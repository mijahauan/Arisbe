"""
Build the **Gamma demonstrations** — three UoDs that express, in Beta + the
diachronic branching DAG, specific modal meanings Peirce attempted to draw with
his never-completed Gamma graphs (docs/GAMMA_DEMONSTRATIONS.md; doctrine in
docs/MODALITY_WITHOUT_GAMMA.md).

Every Peirce citation below was verified against the in-repo Roberts extract
(docs/derived/"Existential Graphs of Peirce_extracted.txt" — Roberts 1973):

1. ``broken_cut_square`` — the **broken cut** of the 1903 Lowell Lectures
   (Lecture IV, CP 4.510–4.516; convention C10 at CP 4.410: "the broken cut
   expresses that the entire graph on its area is logically contingent
   (non-necessary)"). Peirce's own Fig. 1 proposition is *It rains* — the broken
   cut around it reads "it is possible that it does not rain". Here the same four
   modal statuses are the *shape of a derivation DAG* (derivability register,
   every edge a sound ERA), read off by ``src/modal_query.py``:

       (rains)(daylight)(mist)  --ERA mist-->  (rains)(daylight)  --ERA rains--+
           |                                                                   v
           +-------- ERA rains --> (daylight)(mist) -- ERA mist -->        (daylight)

   * □ daylight        — solid-around-broken: "not possibly-not" (necessary)
   * ◇ rains, ◇ mist   — broken-around-solid: possible, not necessary
   * ◇¬ rains          — the broken cut itself: some reachable sheet lacks it
   * □¬ thunders       — broken cut denied: scribed on no reachable sheet

2. ``would_be_de_inesse`` — Peirce's **P-de-inesse** (Prolegomena 1906, CP 4.546,
   4.549; parallel CP 4.580 = Ms 490): "There is some married woman who will
   commit suicide in case her husband fails in business", read as a material
   conditional on one synchronic sheet. Its truth is "too easily guaranteed"
   (Roberts p. 96): it holds if some husband merely does not fail, no connection
   between failure and suicide required. Synchronic — no chain, so the modal lens
   correctly reports *no branching frame*: the de inesse reading is all there is.

3. ``would_be_courses`` — Peirce's **would-be**: his blue-tinted figure (Ms 490,
   the passage omitted at the end of CP 4.575; Roberts p. 89) asserts "It is not
   possible that a man fails in business without suiciding" — a strict
   implication, *more than* the conditional de inesse. Here the tinted possibility
   is a DAG of **courses of experience** (experiential register — each branch a
   ``new_fact`` revision, the assertoric move class of ``model_revision``):
   prosperity, ruin, and prosperity-then-late-ruin. The would-be
   G = ``~[ (fails_in_business "Otto") ~[ (commits_suicide "Clara") ] ]`` peels
   TRUE at *every* reachable world (□G) — while a contrast proposal
   G2 = fails→prospers is refuted by the ruin course (◇ only). Constant labels
   ("Clara", "Otto") carry identity across worlds — the rigid-designator /
   constant-domain policy, stated not solved (MODALITY_WITHOUT_GAMMA.md §3).

Provenance: the Peirce figure each UoD reconstructs is its ``theorem_source``
(a real citation — unlike the synthetic weather diamond, which rightly carries
none); the reconstruction itself is authored, low warrant. Import-safe.
See docs/EXEMPLARS.md and docs/GAMMA_DEMONSTRATIONS.md.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import SCOPE_CHAIN, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from model_revision import DISPOSITION_NEW_FACT, revise_with_disposition
from proof_authoring import ProofChain
from provenance import (
    KIND_DOMAIN_MODEL, KIND_EXEMPLAR, KIND_PROOF, authored_proof, make_provenance,
)
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import (
    UniverseOfDiscourse, UoDCategory, UoDMetadata, UoDType,
)

_WHEN = datetime(2026, 7, 4, tzinfo=timezone.utc)

_ROBERTS = {"type": "book", "author": "Roberts, Don D.",
            "title": "The Existential Graphs of Charles S. Peirce",
            "publisher": "Mouton", "year": "1973", "bibkey": "roberts1973existential"}

_DAU = {"type": "book", "author": "Dau, Frithjof",
        "title": "Mathematical Logic with Diagrams",
        "note": "Ch. 14 erasure rule; Ch. 17 soundness — each derivability edge a sound move"}

_VAN_BENTHEM = {"type": "book", "author": "van Benthem, Johan",
                "title": "Modal Correspondence Theory", "year": "1976",
                "note": "the standard translation — modal operators as quantifiers over a frame"}


# --------------------------------------------------------------------------- #
# 1. broken_cut_square — the Lowell 1903 broken cut, all four modal statuses  #
# --------------------------------------------------------------------------- #

SQUARE_ID = "broken_cut_square"
SQUARE_BASE = "(rains) (daylight) (mist)"
SQUARE_GOAL = "(daylight)"

_rains = lambda g: nav.child_edges(g, g.sheet, "rains")[0]      # noqa: E731
_mist = lambda g: nav.child_edges(g, g.sheet, "mist")[0]        # noqa: E731


def build_broken_cut_square() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    pc = ProofChain.from_egif(SQUARE_BASE)                                   # s0
    pc.apply("ERA", select=_mist, branch="mist-lifts", label="1e",
             note="The mist lifts — erase (mist). One legal line of development.")
    pc.apply("ERA", select=_rains, branch="mist-lifts", label="2e",
             note="The rain passes — erase (rains), leaving (daylight).")
    pc.at("s0")
    pc.apply("ERA", select=_rains, branch="rain-passes-first", label="1e",
             note="Back at the start: the rain passes first — erase (rains).")
    pc.apply("ERA", select=_mist, branch="rain-passes-first", label="2e",
             note="Then the mist lifts — erase (mist), reaching the same (daylight).")
    pc.converge_last_into("s2")

    return pc.to_uod(
        uod_id=SQUARE_ID,
        name="The broken cut, without the broken cut (Lowell 1903)",
        description=(
            "Peirce's broken cut (Lowell Lectures 1903, Lecture IV; CP 4.510–4.516) "
            "predicates possibility of a proposition: convention C10 (CP 4.410) makes "
            "the broken cut say the graph on its area is contingent — his own Fig. 1 "
            "reads 'it is possible that it does not rain'. This UoD expresses every "
            "status the broken cut and its combinations drew, with no modal mark: the "
            "branching derivation DAG is the frame, and src/modal_query.py reads it. "
            "□ daylight (on every reachable sheet — Peirce's solid-around-broken, "
            "'necessary'); ◇ rains and ◇ mist without □ (broken-around-solid, "
            "'possible'); ◇¬ rains (the broken cut itself — some sheet lacks it); "
            "□¬ thunders (no sheet scribes it — 'impossible'). Derivability register: "
            "every edge a sound ERA."
        ),
        category=UoDCategory.THEOREM_PROOF,
    )


def square_provenance() -> dict:
    return make_provenance(
        theorem_source={
            "type": "manuscript", "author": "Peirce, Charles Sanders",
            "title": "The Lowell Lectures of 1903, Lecture IV — the Gamma part of "
                     "Existential Graphs (the broken cut)",
            "year": "1903",
            "note": "CP 4.510–4.516 (exposition; the 'It rains' figure); convention "
                    "C10 at CP 4.410 (Syllabus); rules for the broken cut at Ms 478 "
                    "p. 158. Verified against Roberts 1973, pp. 82–84.",
        },
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[_ROBERTS, _VAN_BENTHEM, _DAU],
        kind=KIND_PROOF,
    ).to_dict()


def square_annotations() -> list:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "Peirce's four broken-cut shapes, each mapped to a reading of this DAG "
            "(the trajectory semantics of docs/MODALITY_WITHOUT_GAMMA.md §1): "
            "(1) the broken cut around g — '◇¬g, it is possible that not-g' (CP 4.410 "
            "C10; his Fig. 1 'It rains') — here: (rains) has counterexample worlds; "
            "(2) a solid cut around a broken cut — '□g' — here: (daylight) is on every "
            "reachable sheet; (3) a broken cut around a solid cut — '◇g' — here: "
            "(rains)/(mist) on some sheet but not all; (4) the denial of ◇g — '□¬g, "
            "impossible' — here: (thunders) on no reachable sheet. The modal lens's "
            "green/amber/absent columns display exactly this square.",
            tags=["modality", "broken-cut", "gamma", "lowell-1903", "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Peirce's Lowell-IV inferences hold here as frame facts on the reflexive "
            "states reading: □g ⊨ g (his Figs. 2→4, via R6(b) then R5), □g ⊨ ◇g "
            "(Figs. 2→5, via R6(a)), □¬g ⊨ ¬g (Figs. 6→8). His R6 cut-conversion — "
            "(a) an evenly enclosed solid cut may be half-erased into a broken cut, "
            "(b) an oddly enclosed broken cut may be filled up into a solid cut — is "
            "the modal weakening/strengthening the trajectory reading validates. And "
            "his caution stands: g and ◇□g 'can neither of them be inferred from the "
            "other' (CP 4.519) — on this frame (rains) holds at the base while ◇□rains "
            "fails. No iteration across the broken cut (R3/R4 withheld) — and none is "
            "needed: no mark crosses anything; the modality is the DAG's shape.",
            tags=["broken-cut-rules", "cut-conversion", "modal-frame", "cp-4-519"]),
    ])


# --------------------------------------------------------------------------- #
# 2. would_be_de_inesse — the Prolegomena material conditional, one sheet     #
# --------------------------------------------------------------------------- #

DE_INESSE_ID = "would_be_de_inesse"
DE_INESSE_EGIF = ('(married_woman *w) (husband *h w) '
                  '~[ (fails_in_business h) ~[ (commits_suicide w) ] ]')


def build_would_be_de_inesse() -> UniverseOfDiscourse:
    meta = UoDMetadata(
        uod_id=DE_INESSE_ID, uod_type=UoDType.STANDALONE,
        name="P de inesse — the married woman (Prolegomena 1906)",
        description=(
            "Peirce's proposition P: 'There is some married woman who will commit "
            "suicide in case her husband fails in business' (CP 4.546, 4.549; parallel "
            "CP 4.580 = Ms 490), read *de inesse* — the material conditional on one "
            "synchronic sheet. Its truth is too easily guaranteed: it holds if some "
            "husband merely does not fail (or some wife happens to suicide), no "
            "connection between failure and suicide required — Roberts (1973, p. 96) "
            "shows the two-move derivation that makes it true from 'some married man "
            "does not fail in business'. A synchronic sheet has no branching frame, so "
            "the modal lens rightly has nothing to read: the de inesse reading is all "
            "there is. The would-be this proposition *meant* lives in the companion "
            "UoD 'would_be_courses'."
        ),
        category=UoDCategory.LITERATURE_EXAMPLE,
        created=_WHEN, last_modified=_WHEN,
    )
    return UniverseOfDiscourse(metadata=meta, current_egi=parse_egif(DE_INESSE_EGIF))


def de_inesse_provenance() -> dict:
    return make_provenance(
        theorem_source={
            "type": "article-journal", "author": "Peirce, Charles Sanders",
            "title": "Prolegomena to an Apology for Pragmaticism",
            "container-title": "The Monist", "year": "1906",
            "note": "CP 4.546, 4.549 — the married-woman proposition and the argument "
                    "that its de inesse reading is too easily true; parallel argument "
                    "CP 4.580 (Ms 490). Verified against Roberts 1973, pp. 95–96.",
        },
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[_ROBERTS],
        kind=KIND_EXEMPLAR,
    ).to_dict()


def de_inesse_annotations() -> list:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "The de inesse (material) reading of Peirce's married-woman proposition: "
            "∃w∃h — a married woman with a husband — and a scroll 'if he fails, she "
            "suicides'. Two generic lines of identity cross into the scroll: pure "
            "Beta. Peirce's complaint (CP 4.546): this is true if the husband simply "
            "never fails — the conditional asserts no connection. What he reached for "
            "with the tinctures — 'it is NOT POSSIBLE that he fails without her "
            "suiciding' (the blue-tinted figure of Ms 490) — needs worlds, and lives "
            "next door in 'would_be_courses' as a branching DAG of courses of "
            "experience.",
            tags=["de-inesse", "would-be", "prolegomena", "gamma", "demonstration"]),
    ])


# --------------------------------------------------------------------------- #
# 3. would_be_courses — the would-be as a DAG of courses of experience        #
# --------------------------------------------------------------------------- #

COURSES_ID = "would_be_courses"
COURSES_BASE = '(married_woman "Clara") (husband "Otto" "Clara")'
WOULD_BE_G = '~[ (fails_in_business "Otto") ~[ (commits_suicide "Clara") ] ]'
CONTRAST_G2 = '~[ (fails_in_business "Otto") ~[ (prospers "Otto") ] ]'

# (branch, fact, label, narration) — each course a new_fact revision (enlargement).
_COURSES = [
    ("prosperity", '(prospers "Otto")', "1·M",
     "A course of experience in which Otto prospers — no failure ever occurs."),
    ("ruin", '(fails_in_business "Otto") (commits_suicide "Clara")', "1·M",
     "A course in which Otto fails — and Clara, as the would-be has it, follows."),
    ("late-ruin", '(fails_in_business "Otto") (commits_suicide "Clara")', "2·M",
     "Prosperity first, ruin later — the would-be holds however late failure comes."),
]


def build_would_be_courses() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    pc = ProofChain.from_egif(COURSES_BASE)                                  # s0
    # prosperity: s0 → s1
    b, fact, label, note = _COURSES[0]
    pc.apply_derived("ADMIT_FACT",
                     lambda g, _f=fact: revise_with_disposition(
                         g, DISPOSITION_NEW_FACT, fact_egif=_f),
                     label=label, note=note, branch=b,
                     params={"disposition": DISPOSITION_NEW_FACT, "fact": fact,
                             "course": b})
    # ruin: s0 → s2
    pc.at("s0")
    b, fact, label, note = _COURSES[1]
    pc.apply_derived("ADMIT_FACT",
                     lambda g, _f=fact: revise_with_disposition(
                         g, DISPOSITION_NEW_FACT, fact_egif=_f),
                     label=label, note=note, branch=b,
                     params={"disposition": DISPOSITION_NEW_FACT, "fact": fact,
                             "course": b})
    # late-ruin: s1 → s3
    pc.at("s1")
    b, fact, label, note = _COURSES[2]
    pc.apply_derived("ADMIT_FACT",
                     lambda g, _f=fact: revise_with_disposition(
                         g, DISPOSITION_NEW_FACT, fact_egif=_f),
                     label=label, note=note, branch=b,
                     params={"disposition": DISPOSITION_NEW_FACT, "fact": fact,
                             "course": b})

    return pc.to_uod(
        uod_id=COURSES_ID,
        name="The would-be — courses of experience (Prolegomena 1906)",
        description=(
            "Peirce's would-be, expressed without a tincture: his blue-tinted figure "
            "(Ms 490, the passage omitted at the end of CP 4.575) asserts 'it is not "
            "possible that a man fails in business without suiciding' — a strict "
            "implication, more than the conditional de inesse (see the companion UoD "
            "'would_be_de_inesse'). Here the tinted possibility is a branching DAG of "
            "courses of experience — prosperity, ruin, prosperity-then-late-ruin — "
            "each branch a new_fact revision (the experiential register: what the "
            "dialogue with the world admits, not what the rules derive). The would-be "
            "G = 'if Otto fails, Clara suicides' peels TRUE at every reachable world "
            "(□G — the strict implication), while the contrast G2 = 'if Otto fails, "
            "he prospers' is refuted by the ruin course (◇ only). Constant labels "
            "carry identity across worlds — the rigid-designator policy, stated not "
            "solved (docs/MODALITY_WITHOUT_GAMMA.md §3)."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


def courses_provenance() -> dict:
    return make_provenance(
        theorem_source={
            "type": "article-journal", "author": "Peirce, Charles Sanders",
            "title": "Prolegomena to an Apology for Pragmaticism",
            "container-title": "The Monist", "year": "1906",
            "note": "The would-be as strict implication: the blue-tinted figure of "
                    "Ms 490 (passage omitted at the end of CP 4.575) — 'it is not "
                    "possible that a man fails in business without suiciding'; the "
                    "de inesse/would-be contrast at CP 4.546, 4.549. Verified against "
                    "Roberts 1973, pp. 89, 95–96.",
        },
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[_ROBERTS, _VAN_BENTHEM],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def courses_annotations() -> list:
    return annotations_to_list([
        # The standing proposal — pre-fills both the audit lens and the modal lens's
        # proposal reading (□G/◇G over the worlds).
        make_annotation(SCOPE_UOD, WOULD_BE_G, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "The would-be made drawable: 'should Otto fail, Clara would suicide' is "
            "not a fact of one sheet but a habit of every course of experience. The "
            "worlds are the reachable sheets of this DAG; the modal lens's proposal "
            "reading peels G = ~[ (fails_in_business \"Otto\") ~[ (commits_suicide "
            "\"Clara\") ] ] at each world: TRUE everywhere — □G, Peirce's 'not "
            "possible that he fails without her suiciding' (Ms 490). Try the contrast "
            "proposal ~[ (fails_in_business \"Otto\") ~[ (prospers \"Otto\") ] ] — "
            "the ruin course refutes it (◇ only, with a counterexample world). Note "
            "the de inesse trap is visible per-world: at the prosperity worlds G is "
            "TRUE merely because Otto has not failed.",
            tags=["would-be", "strict-implication", "modality", "prolegomena",
                  "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Experiential register: each edge is a new_fact enlargement "
            "(src/model_revision.py) — a course of experience admitting what happens, "
            "not a Dau inference. Choosing this accessibility relation R (courses) "
            "rather than derivability (the broken_cut_square's R) is exactly what "
            "Peirce's tinctures chose: the mode of the modality is which R the frame "
            "ranges over (docs/MODALITY_WITHOUT_GAMMA.md §2 — the multimodal point).",
            tags=["experiential-register", "tinctures", "accessibility", "new-fact"]),
    ])


# --------------------------------------------------------------------------- #
# Self-checking driver                                                        #
# --------------------------------------------------------------------------- #

def _closed_verdict(state_egi, proposal_egif: str) -> str:
    """Peel a proposal against one world's sheet, closed-world (the audit-lens
    semantics — a course's record is read as a closed record)."""
    from domain_oracle import CorpusOracle
    from model_materialization import materialize_egi
    from semantic_game import evaluate
    facts, _ = materialize_egi(state_egi)
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


def main(argv=None) -> int:
    import modal_query as mq
    from collections import Counter

    # -- 1. the broken-cut square ------------------------------------------------
    sq_chain, sq_uod = build_broken_cut_square()
    assert nav.same_graph(sq_uod.current_egi, parse_egif(SQUARE_GOAL))
    frm = Counter(s.from_state_id for s in sq_chain.steps)
    to = Counter(s.to_state_id for s in sq_chain.steps)
    assert any(v > 1 for v in frm.values()), "no fork"
    assert any(v > 1 for v in to.values()), "no convergence"
    # The four statuses of Peirce's square:
    assert mq.necessarily(sq_chain, mq.scribes_relation("daylight")).holds        # □g
    assert mq.possibly(sq_chain, mq.scribes_relation("rains")).holds              # ◇g
    assert not mq.necessarily(sq_chain, mq.scribes_relation("rains")).holds       # ◇¬g
    assert not mq.possibly(sq_chain, mq.scribes_relation("thunders")).holds       # □¬g
    # Lowell-IV inferences as frame facts (reflexive states reading):
    base = sq_chain.states[sq_chain.initial_state_id]
    assert mq.scribes_relation("daylight")(base)                                  # □g ⊨ g
    assert mq.possibly(sq_chain, mq.scribes_relation("daylight")).holds           # □g ⊨ ◇g
    # CP 4.519 — g at the base does NOT give ◇□g:
    assert mq.scribes_relation("rains")(base)
    assert not any(
        mq.necessarily(sq_chain, mq.scribes_relation("rains"), base=w).holds
        for w in mq.reachable_states(sq_chain))

    # -- 2. de inesse --------------------------------------------------------------
    di_uod = build_would_be_de_inesse()
    assert nav.same_graph(di_uod.current_egi, parse_egif(DE_INESSE_EGIF))

    # -- 3. the would-be over courses ----------------------------------------------
    co_chain, co_uod = build_would_be_courses()
    frm = Counter(s.from_state_id for s in co_chain.steps)
    assert any(v > 1 for v in frm.values()), "no fork — not a branching frame"
    worlds = mq.reachable_states(co_chain)
    verdicts = {w: _closed_verdict(co_chain.states[w], WOULD_BE_G) for w in worlds}
    assert all(v == "true" for v in verdicts.values()), f"□G must hold: {verdicts}"
    v2 = {w: _closed_verdict(co_chain.states[w], CONTRAST_G2) for w in worlds}
    assert any(v == "false" for v in v2.values()), "the ruin course must refute G2"
    assert any(v == "true" for v in v2.values()), "G2 should still be ◇"

    # -- save ------------------------------------------------------------------------
    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(sq_uod, sq_chain, provenance=square_provenance())
    service.save_annotations(sq_uod, square_annotations())
    service.save_uod(di_uod)
    service.save_provenance(di_uod, de_inesse_provenance())
    service.save_annotations(di_uod, de_inesse_annotations())
    service.save_uod_with_chain(co_uod, co_chain, provenance=courses_provenance())
    service.save_annotations(co_uod, courses_annotations())

    print(f"Saved '{SQUARE_ID}' — {len(sq_chain.steps)} steps, "
          f"{len(sq_chain.states)} states (□ daylight · ◇ rains/mist · □¬ thunders).")
    print(f"Saved '{DE_INESSE_ID}' — synchronic (the de inesse sheet).")
    print(f"Saved '{COURSES_ID}' — {len(co_chain.steps)} courses; "
          f"the would-be G peels TRUE at every world (□G).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
