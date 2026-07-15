"""**The explicit-step vocabulary for the verdict and for M-modification** —
the corpus half of M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §8.1, as chain steps.

Three acts, each recorded through ``ProofChain`` and each **earned at record
time** — the transform runs real Dau rules or a real evaluation; the parameters
say what happened, they never merely assert it:

* :func:`peel_step` — **PEEL**, the verdict act. An identity transform (the
  EXHIBIT precedent: a fresh state, same graph — never a ``from == to``
  self-loop, which would corrupt the modal leaves) whose parameters carry the
  peel actually run against the current state: proposal, three-valued verdict,
  witness/counterexample. The verdict is thereby *in the record*, re-checkable
  forever (the sweep gate recomputes it).
* :func:`admit_step` — **ADMIT_TO_M**, enlargement. A genuine INS into the
  standing world-scroll's antecedent area (``world_scroll.enlarge_m``) — under
  the polarity shift, adding to M is finally rule-licensed (supposing more is
  free in a negative context); the warrant justifies the *choice* and rides on
  the step, not on the ink.
* :func:`revise_step` — **REVISE_M**, relinquishment as world-withdrawal. One
  step carrying the executed ERA / DC+ / INS triple
  (``world_scroll.withdraw_and_resupply``): you cannot un-suppose piecemeal at
  odd depth, so the whole world is withdrawn and an amended one supplied — and
  the DAG keeps the withdrawn world, because ``from_state`` still holds it.
  Recorded as one step so the audit ribbon never peels the blank/empty-scroll
  intermediates (the triple is still *performed*; the label is earned).

``PEEL`` is registered neutral and ``ADMIT_TO_M`` ampliative in
``proof_character``; ``REVISE_M`` was already ampliative there.

Additive; used by the corpus builders. The live loops keep
``model_revision.revise_with_disposition`` until the §8.1 order is taken.
"""

from __future__ import annotations

from typing import Optional

from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from proof_authoring import ProofChain
from semantic_game import SemanticResult, evaluate
from world_scroll import enlarge_m, find_world_scroll, withdraw_and_resupply

PEEL = "PEEL"
ADMIT_TO_M = "ADMIT_TO_M"
REVISE_M = "REVISE_M"


def peel_step(
    pc: ProofChain,
    proposal_egif: str,
    *,
    closed: bool = False,
    materialize: bool = True,
    note: Optional[str] = None,
    branch: Optional[str] = None,
) -> SemanticResult:
    """Peel ``proposal_egif`` against the chain's **current state** and record
    the verdict as an explicit ``PEEL`` step. Returns the ``SemanticResult``
    (so a builder can also assert the expected trajectory)."""
    state = pc.current
    m = materialize_egi(state)[0] if materialize else state
    result = evaluate(parse_egif(proposal_egif),
                      CorpusOracle([("M", m)], closed=closed),
                      closed=closed)
    params = {
        "act": "peel",
        "earned": True,
        "proposal_egif": proposal_egif,
        "closed": closed,
        "materialized": materialize,
        "verdict": result.verdict.value,
        "winning_witness": result.winning_witness,
        "counterexample": result.counterexample,
        "summary": result.summary,
    }
    pc.apply_derived(PEEL, lambda g: g,
                     note=note or f"peel: {result.summary}",
                     params=params, branch=branch)
    return result


def admit_step(
    pc: ProofChain,
    fact_egif: str,
    *,
    disposition: str = "new_fact",
    mode: str = "induction",
    warrant: Optional[str] = None,
    note: Optional[str] = None,
    branch: Optional[str] = None,
) -> ProofChain:
    """Enlarge M by ``fact_egif`` — a genuine INS into the world-scroll's
    antecedent area — recorded as an explicit ``ADMIT_TO_M`` step."""
    scroll = find_world_scroll(pc.current)
    if scroll is None:
        raise ValueError("admit_step needs a standing world-scroll "
                         "(wrap the initial M first)")
    params = {
        "act": "m_enlargement",
        "earned": True,
        "derivation": ["INS"],
        "target_area": scroll.cut_id,
        "fact_egif": fact_egif,
        "disposition": disposition,
        "mode": mode,
    }
    if warrant:
        params["warrant"] = warrant
    return pc.apply_derived(ADMIT_TO_M, lambda g: enlarge_m(g, fact_egif),
                            note=note, params=params, branch=branch)


def revise_step(
    pc: ProofChain,
    new_m_egif: str,
    *,
    subgraph_egif: Optional[str] = None,
    fact_egif: Optional[str] = None,
    disposition: str = "challenge_to_M",
    mode: str = "abduction",
    reason: Optional[str] = None,
    note: Optional[str] = None,
    branch: Optional[str] = None,
) -> ProofChain:
    """Withdraw the standing world and supply the amended one (the executed
    ERA / DC+ / INS triple), recorded as one explicit ``REVISE_M`` step.
    ``subgraph_egif`` names what was relinquished, ``fact_egif`` what the
    amended world newly carries (the audit lens reads both)."""
    scroll = find_world_scroll(pc.current)
    if scroll is None:
        raise ValueError("revise_step needs a standing world-scroll to withdraw")

    derivation_seen = []

    def transform(g):
        out, derivation = withdraw_and_resupply(g, new_m_egif)
        derivation_seen.extend(derivation)
        return out

    params = {
        "act": "world_withdrawal",
        "earned": True,
        "derivation": ["ERA", "DC+", "INS"],
        "withdrawn_scroll": scroll.cut_id,
        "disposition": disposition,
        "mode": mode,
    }
    if subgraph_egif:
        params["subgraph_egif"] = subgraph_egif
    if fact_egif:
        params["fact_egif"] = fact_egif
    if reason:
        params["reason"] = reason
    pc.apply_derived(REVISE_M, transform, note=note, params=params,
                     branch=branch)
    assert derivation_seen == ["ERA", "DC+", "INS"], "withdrawal not executed"
    return pc


__all__ = ["PEEL", "ADMIT_TO_M", "REVISE_M",
           "peel_step", "admit_step", "revise_step"]
