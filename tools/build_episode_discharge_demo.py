"""
Build ``episode_discharge`` — the EPG episode conducted wholly in ink, and its
result discharged to the level of the original M (M_RESIDENCE §10, the
author's construction, ruling (b): the calculus licenses, the citation earns).

The lifecycle, every move a licensed rule:

  s0  M resident in cells: (dog Rex) + the law dog→mammal
   │  ENTERTAIN — DC+ in M's even area (the episode theorem: an EPG episode
   │  requires its DC+ in an even context at depth ≥ 2), IT+ of M into the
   │  arena (the premise is M's own ink, identity-preserved), INS of ~[P];
   │  the empty inner cut — the VACUITY RIDER — keeps the exhibit forceless:
   │  "if M then (mammal Rex)" is entertained, not asserted.
   │  PEEL — the confirmation: materialized (the law fires), P reads TRUE.
   │  DISCHARGE_TO_M — drawn modus ponens: IT− the M′ copies (the warrant
   │  emptied against the original one level up), IT− the rider (licensed
   │  against the residence's standing hold), DC− — P's ink lands in the
   │  agreed context, derived, never inserted (FIDELITY §3b corollary 3).
   │  The step CITES the confirming peel: the ⊥-door makes the licence
   │  unconditional, so the earning rides on the record.
  s4  M carries (mammal Rex) as STANDING ink: a peel with NO materialization
      now reads TRUE — the derived fact became a registered one.

The contrast the exemplar teaches: before the discharge, (mammal Rex) is true
only *through* the materializer's forward chaining (ephemeral closure); after,
it stands in M itself — theorem_registration, drawn. proof_character reads the
chain THEOREMATIC: scribing the candidate into the exhibit is Peirce's
auxiliary line, and the discharge is its corollarial follow-through.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from annotations import SCOPE_CHAIN, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from m_steps import discharge_step, entertain_step, peel_step
from proof_authoring import ProofChain
from proof_character import character_of_chain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from tomos_service import TomosService
from world_scroll import wrap_m

UOD_ID = "episode_discharge"
M0 = '(dog "Rex") ~[ (dog *x) ~[ (mammal x) ] ]'
P = '(mammal "Rex")'


def build():
    pc = ProofChain(wrap_m(parse_egif(M0))[0])

    r0 = peel_step(pc, P, closed=True, materialize=False,
                   note="Before anything: (mammal Rex) does NOT stand in M — "
                        "unmaterialized, the sheet is silent (closed: false).")
    entertain_step(
        pc, P,
        note="ENTERTAIN — the episode's premise 'if M then (mammal Rex)' built "
             "as ink inside the agreed context: DC+ (the arena; the episode "
             "theorem puts it at even depth ≥ 2 — nowhere else can M be "
             "identified by rule and the result handled), IT+ of M (the "
             "premise is M's own ink), INS of ~[P]. The vacuity rider keeps "
             "the exhibit forceless: entertained, not asserted.")
    r1 = peel_step(pc, P, closed=True,
                   note="The confirmation: materialized, the law fires — "
                        "(mammal Rex) reads TRUE. This recorded verdict is "
                        "what the discharge will cite.")
    discharge_step(
        pc, P,
        note="DISCHARGE_TO_M — drawn modus ponens: IT− the iterated premise "
             "(the warrant emptied against the original), IT− the rider "
             "(licensed against the standing hold — the ⊥-door, which is why "
             "the licence alone certifies nothing), DC−. P lands at the level "
             "of the original M: derived, never inserted. The step cites the "
             "confirming PEEL — ruling (b): the earning rides on the record.")
    r2 = peel_step(pc, P, closed=True, materialize=False,
                   note="After the discharge: (mammal Rex) STANDS in M — the "
                        "unmaterialized peel now reads TRUE. The derived fact "
                        "became a registered one (theorem_registration, drawn).")

    assert [r0.verdict.value, r1.verdict.value, r2.verdict.value] == \
        ["false", "true", "true"]
    ch = character_of_chain(pc.to_chain())
    assert ch.character == "theorematic" and not ch.opaque_steps, ch.summary

    return pc.to_uod(
        uod_id=UOD_ID,
        name="An EPG episode, entertained and discharged in ink",
        description=(
            "The Endoporeutic Game episode conducted wholly as licensed rule "
            "applications inside the standing residence (M_RESIDENCE §10). "
            "ENTERTAIN builds the premise 'if M then P' as ink — DC+ in M's "
            "even area (the episode theorem: an EPG episode requires its DC+ "
            "in an even context at depth ≥ 2 — an odd area gives no arena, and "
            "at depth 0 the discharge is unreachable by rule), IT+ of M "
            "(identity-preserved premise), INS of ~[P] — with the empty inner "
            "cut as the vacuity rider, so the contingent conditional stands "
            "forceless while contested. A recorded PEEL confirms P against the "
            "materialized M. DISCHARGE_TO_M is drawn modus ponens — IT− of the "
            "premise copies, IT− of the rider against the standing hold, DC− — "
            "landing P in the agreed content, derived, never inserted. Because "
            "the standing hold is ⊥ in scope (the ⊥-door), this sequence is "
            "licensed whether or not the episode was confirmed — so under "
            "ruling (b) the discharge step must CITE its confirming peel, and "
            "the polarity gate re-asserts the citation and refuses any silent "
            "M-change (the m_view tripwire). The chain reads THEOREMATIC: "
            "scribing the candidate is Peirce's auxiliary line."
        ),
    )


def provenance():
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "theorematic deduction — the auxiliary construction; the "
                     "endoporeutic reading of the scroll"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def annotations():
    return annotations_to_list([
        make_annotation(SCOPE_UOD, P, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "The EPG episode in ink: entertain (DC+ · IT+ · INS behind the "
            "vacuity rider), confirm (a recorded PEEL), discharge (drawn modus "
            "ponens — IT− · IT− · DC−, citing the peel). Watch the audited "
            "proposal (mammal Rex) move: absent → derived-only → STANDING.",
            tags=["demonstration", "episode", "discharge", "theorem-registration",
                  "world-scroll"]),
        make_annotation(SCOPE_CHAIN,
            "The episode theorem (M_RESIDENCE §10): an EPG episode requires its "
            "DC+ in an even context at depth ≥ 2. Parity: only a cut opened in "
            "an even area has a negative arena. Reach: IT+ carries M only into "
            "areas M's own area encloses. Results: the discharge needs the "
            "vacuity rider deiterated against a standing empty cut in an "
            "enclosing area — available exactly inside W (the hold), and NEVER "
            "at depth 0, where soundness forbids a standing ⊥: 'no "
            "unconditioned posit' enforced by rule-reachability.",
            tags=["episode-theorem", "vacuity-rider", "bottom-door"]),
    ])


def main(argv=None) -> int:
    chain, uod = build()
    service = TomosService(Path(__file__).resolve().parent.parent / "tomos")
    service.save_uod_with_chain(uod, chain, provenance=provenance())
    service.save_annotations(uod, annotations())
    print(f"Saved '{UOD_ID}' — the episode lifecycle in ink "
          f"({len(chain.steps)} steps: entertain / peel / discharge, cited).")
    for s in chain.steps:
        p = s.parameters or {}
        print(f"  {s.rule_name:15s} act={p.get('act', '—'):20s} "
              f"derivation={p.get('derivation', p.get('verdict', '—'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
