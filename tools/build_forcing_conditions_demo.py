"""
Build the **forcing-conditions exemplar** — Cohen's binary-sequence conditions as a
small diachronic episode, read through the modal and audit lenses.

Design-of-record: docs/FORCING_AND_THE_GAMMA_CROSSING.md (§2 the dictionary, §6 the
build). The occasioning paper (Caterina & Gangle 2010) models Cohen's forcing in
Peirce's Existential Graphs; this exemplar puts its running example — the poset of
finite binary sequences — into the corpus using **only existing machinery**: the
diachronic DAG is the condition poset, a condition-extension is a *game move* (a
``new_fact`` revision, not a deduction), and the modal lens reads the forcing
trichotomy off the branching history.

    s0  (one "p1")                    the condition ⟨1⟩
     │   reveal p2 = 1
    s1  + (one "p2")                  the condition ⟨1,1⟩ — the fork's base
     ├── reveal p3 = 1  → s2  + (one "p3")    ⟨1,1,1⟩   (the all-ones branch)
     └── reveal p3 = 0  → s3  + (zero "p3")   ⟨1,1,0⟩   (the domination met)

The two children of s1 are **incompatible extensions** — the paper's "every
condition is dominated by two incompatible conditions" (the splitting property),
drawn as a genuine DAG fork (two chain steps sharing ``from_state_id``). The
**correct-set property** δ₁ ("all entries are ones") is the standing proposal under
audit, G = ``~[ (zero *p) ]``: it holds along the all-ones branch and is refuted the
moment the domination is met — the structural reason a correct set discernible in M
cannot be generic. The modal lens reads the forcing table (□one · ◇zero), and
``modal_query.settlement`` names the trichotomy: *one* is **settled** (∅ forces it),
*zero* is **open** (some condition forces it), *two* is **excluded** (no condition
forces it). Original to Arisbe, low warrant. Import-safe. See docs/EXEMPLARS.md.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

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

UOD_ID = "forcing_conditions"
M0_EGIF = '(one "p1")'                       # the condition ⟨1⟩
PROPOSAL_G = '~[ (zero *p) ]'                # δ₁ membership: no entry is a zero

# (fork?, fact, branch, narration). ``fork=True`` = return to the fork base
# (the ⟨1,1⟩ state, captured dynamically) before extending.
REVEALS = [
    (False, '(one "p2")', None,
     "Reveal p2 = 1 — extend the condition to ⟨1,1⟩ (the fork's base)."),
    (False, '(one "p3")', "all-ones",
     "Reveal p3 = 1 — the all-ones extension ⟨1,1,1⟩; δ₁ survives."),
    (True, '(zero "p3")', "meets-the-domination",
     "Reveal p3 = 0 — the incompatible extension ⟨1,1,0⟩; the domination "
     "(sequences containing a zero) is met and δ₁ is refuted."),
]


def _verdict(model_egi, proposal_egif: str = PROPOSAL_G) -> str:
    """Peel the correct-set property G against a condition state (closed-world:
    a condition is a finite, fully-revealed record)."""
    facts, _ = materialize_egi(model_egi)
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


def build_forcing_chain() -> Tuple[TransformationChain, UniverseOfDiscourse, list, str]:
    """Returns (chain, uod, verdicts, fork_base_id). The condition record
    resides at level 1 of a standing world-scroll (the validity discipline);
    each reveal is an explicit rule-licensed ADMIT_TO_M and each audit of δ₁ a
    recorded PEEL step, threaded through the trunk (identity states) so the
    branch structure — and the modal reading of the leaves — is untouched."""
    wrapped, _ = wrap_m(parse_egif(M0_EGIF))
    pc = ProofChain(wrapped)                                              # s0 = ⟨1⟩
    verdicts = [peel_step(pc, PROPOSAL_G, closed=True,
                          note="The opening condition ⟨1⟩: δ₁ holds.").verdict.value]
    fork_base = None
    for fork, fact, branch, note in REVEALS:
        if fork:
            pc.at(fork_base)          # the fork: two extensions share the base
        admit_step(pc, fact, disposition=DISPOSITION_NEW_FACT,
                   mode="induction", warrant="the next entry revealed",
                   note=note, branch=branch)
        verdicts.append(peel_step(pc, PROPOSAL_G, closed=True,
                                  branch=branch).verdict.value)
        if fork_base is None:
            fork_base = pc.current_state_id      # the ⟨1,1⟩ state (post-audit)
    chain, uod = pc.to_uod(
        uod_id=UOD_ID,
        name="Forcing conditions (Cohen's binary sequences)",
        description=(
            "Cohen's poset of finite binary conditions as a diachronic episode: "
            "each reveal extends the condition (a game move, not a deduction), and "
            "the fork at ⟨1,1⟩ is the splitting property — two incompatible "
            "extensions from one condition. The correct-set property δ₁ = 'no entry "
            "is a zero' (~[ (zero *p) ]) is audited against every state: it holds "
            "along the all-ones branch and falls where the domination is met. The "
            "modal lens reads the forcing trichotomy off the DAG: □one (settled — "
            "∅ forces it), ◇zero (open — some condition forces it), no 'two' "
            "anywhere (excluded). After Caterina & Gangle 2010; see "
            "docs/FORCING_AND_THE_GAMMA_CROSSING.md."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )
    return chain, uod, verdicts, fork_base


def forcing_provenance() -> dict:
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "incollection", "author": "Caterina, Gianluca and Gangle, Rocco",
             "title": "Consequences of a Diagrammatic Representation of Paul "
                      "Cohen's Forcing Technique Based on C.S. Peirce's "
                      "Existential Graphs",
             "bibkey": "caterina2010forcing",
             "note": "Model-Based Reasoning in Science & Technology, SCI 314, "
                     "Springer 2010, 429–443"},
            {"type": "book", "author": "Cohen, Paul",
             "title": "Set Theory and the Continuum Hypothesis",
             "bibkey": "cohen1966set",
             "note": "the condition poset, dominations, and the generic set"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def forcing_annotations(chain: TransformationChain) -> list:
    anns = [
        # The standing proposal (δ₁ membership) for the Organon audit lens.
        make_annotation(SCOPE_UOD, PROPOSAL_G, tags=["audit-proposal"]),
        make_annotation(SCOPE_UOD,
            "Cohen's forcing conditions as a branching history. A condition is a "
            "state of the developing record; an extension is a revision (a game "
            "move); the fork is the splitting property — every condition is "
            "dominated by two incompatible extensions. The modal lens reads the "
            "forcing trichotomy: 'one' is settled (□ — scribed on every reachable "
            "sheet), 'zero' is open (◇ — some trajectory scribes it, some escapes "
            "it), 'two' is excluded (no trajectory). The audited δ₁ property shows "
            "why a correct set discernible in M cannot be generic: the domination "
            "that refutes it is always one extension away.",
            tags=["domain-model", "forcing", "modality", "branching", "demonstration"]),
        make_annotation(SCOPE_CHAIN,
            "Each reveal is an explicit ADMIT_TO_M step (src/m_steps.py): the next "
            "entry admitted by a genuine INS into the condition's standing "
            "world-scroll (nothing contingent at depth 0). The fork (two ADMIT "
            "steps from the ⟨1,1⟩ state) records the incompatible extensions "
            "⟨1,1,1⟩ and ⟨1,1,0⟩ — trajectories that never reconverge. Each δ₁ "
            "verdict is a recorded PEEL step.",
            tags=["new-fact", "enlargement", "fork", "world-scroll", "low-warrant"]),
    ]
    # Marginalia: tag each PEEL step with its recorded verdict.
    for step in chain.steps:
        prm = step.parameters or {}
        if prm.get("act") == "peel":
            v = str(prm.get("verdict", "?")).upper()
            anns.append(make_annotation(
                SCOPE_STEP,
                f"δ₁ ('no entry is a zero') peels to {v} here.",
                step_id=step.step_id, tags=["audit", "verdict"]))
    return annotations_to_list(anns)


def main(argv=None) -> int:
    import modal_query as mq

    chain, uod, verdicts, fork_base = build_forcing_chain()

    # The fork is real: two ADMIT steps share the fork base, and the branches
    # never reconverge (two trajectory endpoints — the final audit states).
    froms = [s.from_state_id for s in chain.steps]
    assert froms.count(fork_base) == 2, (
        f"expected the fork at {fork_base}, got {froms}")
    assert len(mq.leaf_states(chain)) == 2

    # The audited δ₁ property (the recorded PEEL verdicts): holds along the
    # trunk and the all-ones branch, falls where the domination is met.
    assert verdicts == ["true", "true", "true", "false"], verdicts

    # The forcing trichotomy, read by the settlement lens.
    settled = mq.settlement(chain, mq.scribes_relation("one"))
    opened = mq.settlement(chain, mq.scribes_relation("zero"))
    excluded = mq.settlement(chain, mq.scribes_relation("two"))
    assert (settled.status, opened.status, excluded.status) == (
        "settled", "open", "excluded")

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=forcing_provenance())
    service.save_annotations(uod, forcing_annotations(chain))
    print(f"Saved '{UOD_ID}' — {len(chain.steps)} steps (world-scroll residence; "
          f"explicit PEEL/ADMIT_TO_M), fork at {fork_base}.")
    print(f"  δ₁ audit: {' → '.join(v.upper() for v in verdicts)}")
    for res in (settled, opened, excluded):
        print(f"  settlement: {res.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
