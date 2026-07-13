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
from model_revision import DISPOSITION_NEW_FACT, revise_with_disposition
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from semantic_game import evaluate
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UOD_ID = "forcing_conditions"
M0_EGIF = '(one "p1")'                       # the condition ⟨1⟩
PROPOSAL_G = '~[ (zero *p) ]'                # δ₁ membership: no entry is a zero

# (state-to-fork-from, fact, branch, narration). ``None`` = continue the trunk.
REVEALS = [
    (None, '(one "p2")', None,
     "Reveal p2 = 1 — extend the condition to ⟨1,1⟩ (the fork's base)."),
    (None, '(one "p3")', "all-ones",
     "Reveal p3 = 1 — the all-ones extension ⟨1,1,1⟩; δ₁ survives."),
    ("s1", '(zero "p3")', "meets-the-domination",
     "Reveal p3 = 0 — the incompatible extension ⟨1,1,0⟩; the domination "
     "(sequences containing a zero) is met and δ₁ is refuted."),
]


def _verdict(model_egi, proposal_egif: str = PROPOSAL_G) -> str:
    """Peel the correct-set property G against a condition state (closed-world:
    a condition is a finite, fully-revealed record)."""
    facts, _ = materialize_egi(model_egi)
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


def build_forcing_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    pc = ProofChain.from_egif(M0_EGIF)                                    # s0 = ⟨1⟩
    for fork_from, fact, branch, note in REVEALS:
        if fork_from is not None:
            pc.at(fork_from)                     # the fork: two steps share s1
        pc.apply_derived(
            "ADMIT_FACT",
            lambda g, _f=fact: revise_with_disposition(
                g, DISPOSITION_NEW_FACT, fact_egif=_f),
            note=note, branch=branch,
            params={"disposition": DISPOSITION_NEW_FACT, "fact": fact},
        )
    return pc.to_uod(
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
            "Each step is a model-revising 'new_fact' disposition "
            "(src/model_revision.py): a reveal of the next entry, juxtaposed onto "
            "the condition's sheet. The fork (two steps from s1) records the "
            "incompatible extensions ⟨1,1,1⟩ and ⟨1,1,0⟩ — trajectories that never "
            "reconverge.",
            tags=["new-fact", "enlargement", "fork", "low-warrant"]),
    ]
    # Tag each step's resulting state with the audited verdict.
    for step in chain.steps:
        v = _verdict(chain.states[step.to_state_id])
        anns.append(make_annotation(
            SCOPE_STEP,
            f"After this reveal, δ₁ ('no entry is a zero') peels to {v.upper()}.",
            step_id=step.step_id, tags=["audit", "verdict"]))
    return annotations_to_list(anns)


def main(argv=None) -> int:
    import modal_query as mq

    chain, uod = build_forcing_chain()

    # The fork is real: two steps share from_state_id s1, and the branches never
    # reconverge (two trajectory endpoints).
    froms = [s.from_state_id for s in chain.steps]
    assert froms.count("s1") == 2, f"expected the fork at s1, got {froms}"
    assert len(mq.leaf_states(chain)) == 2

    # The audited δ₁ property: holds along the trunk and the all-ones branch,
    # falls where the domination is met.
    verdicts = [_verdict(chain.states[chain.initial_state_id])] + [
        _verdict(chain.states[s.to_state_id]) for s in chain.steps]
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
    print(f"Saved '{UOD_ID}' — {len(chain.steps)} reveals, fork at s1.")
    print(f"  δ₁ audit: {' → '.join(v.upper() for v in verdicts)}")
    for res in (settled, opened, excluded):
        print(f"  settlement: {res.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
