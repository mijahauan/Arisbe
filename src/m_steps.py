"""**The explicit-step vocabulary for the verdict and for M-modification** —
M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §8.1's step layer, updated to the §9
residence (cells at even depth, ratified 2026-07-16), as chain steps.

Every act is recorded through ``ProofChain`` and **earned at record time** —
the transform runs real Dau rules or a real evaluation; the parameters say
what happened, they never merely assert it:

* :func:`peel_step` — **PEEL**, the verdict act. An identity transform (the
  EXHIBIT precedent: a fresh state, same graph — never a ``from == to``
  self-loop, which would corrupt the modal leaves) whose parameters carry the
  peel actually run against the current state: proposal, three-valued verdict,
  witness/counterexample. The verdict is thereby *in the record*, re-checkable
  forever (the sweep gate recomputes it).
* :func:`admit_step` — **ADMIT_TO_M**, enlargement. A genuine INS of a closed
  **cell** into the standing residence (``world_scroll.enlarge_m``) — one
  licensed move; each admitted batch is its own cell (verdict D2); the warrant
  justifies the *choice* and rides on the step, not on the ink.
* :func:`retract_step` — **RETRACT_FROM_M**, retraction. One licensed **ERA**
  inside a cell (``world_scroll.retract_from_m``) — the §9 fallibilist pole:
  the refuted (or merely faded) content dies in one move, the emptied husk
  stands as a scar, and the DAG keeps the prior state. Refutation-driven
  retraction and disuse-driven fading are the *same* move; the recorded
  ``disposition`` / ``flavor`` distinguish surprise from entropy
  (``flavor="pruned:disuse"`` is the *faded* tense-flavor).
* :func:`challenge_step` — **REVISE_M**, the challenge-to-M composite: ONE
  step executing the licensed retraction(s) *and* the admission of the
  refuting anomaly (ERA then INS), so the audit ribbon reads the revision as
  the single dialogical event it is.
* :func:`revise_step` — **REVISE_M** as world-withdrawal (the executed
  ERA / DC+ / INS triple, ``world_scroll.withdraw_and_resupply``). Under cells
  this is the *rare* full-replacement case (a husk is a cut at odd depth, not
  ERA-licensed); piecemeal relinquishment is :func:`retract_step`.

``PEEL`` is registered neutral; ``ADMIT_TO_M``, ``RETRACT_FROM_M`` and
``REVISE_M`` are ampliative in ``proof_character`` (the family criterion:
each changes M by a choice no inference compelled).

Additive; used by the corpus builders and (since sweep #2) the live loops
through ``model_revision.revise_with_disposition``'s residence-aware dispatch.
"""

from __future__ import annotations

from typing import List, Optional

from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from proof_authoring import ProofChain
from semantic_game import SemanticResult, evaluate
from world_scroll import (
    enlarge_m,
    find_world_scroll,
    retract_from_m,
    withdraw_and_resupply,
)

PEEL = "PEEL"
ADMIT_TO_M = "ADMIT_TO_M"
RETRACT_FROM_M = "RETRACT_FROM_M"
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
    """Enlarge M by ``fact_egif`` — a genuine INS of a closed cell into the
    standing residence — recorded as an explicit ``ADMIT_TO_M`` step."""
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


def retract_step(
    pc: ProofChain,
    *,
    subgraph_egif: Optional[str] = None,
    relation: Optional[str] = None,
    labels: Optional[List[Optional[str]]] = None,
    disposition: str = "retract_fact",
    flavor: Optional[str] = None,
    mode: str = "abduction",
    reason: Optional[str] = None,
    note: Optional[str] = None,
    branch: Optional[str] = None,
) -> ProofChain:
    """Retract content from M — one licensed ERA inside a cell
    (``world_scroll.retract_from_m``) — recorded as an explicit
    ``RETRACT_FROM_M`` step. ``subgraph_egif`` names a law/negation cut,
    ``relation`` (+ optional exact ``labels``) an atom; ``flavor`` records the
    D6 pruning disposition when the erasure is entropy rather than surprise
    (``"pruned:disuse"`` — the *faded* tense-flavor)."""
    scroll = find_world_scroll(pc.current)
    if scroll is None:
        raise ValueError("retract_step needs a standing world-scroll")

    # Dry-run against the current state to learn the executed derivation
    # (deterministic: apply_derived will run the same transform on the same
    # graph), so the recorded params carry what actually happened.
    _, expected = retract_from_m(
        pc.current, subgraph_egif=subgraph_egif, relation=relation,
        labels=labels)

    derivation_seen: List[str] = []

    def transform(g):
        out, derivation = retract_from_m(
            g, subgraph_egif=subgraph_egif, relation=relation, labels=labels)
        derivation_seen.extend(derivation)
        return out

    params = {
        "act": "m_retraction",
        "earned": True,
        "derivation": list(expected),
        "disposition": disposition,
        "mode": mode,
    }
    if subgraph_egif:
        params["subgraph_egif"] = subgraph_egif
    if relation:
        params["relation"] = relation
    if labels is not None:
        params["labels"] = list(labels)
    if flavor:
        params["flavor"] = flavor
    if reason:
        params["reason"] = reason
    pc.apply_derived(RETRACT_FROM_M, transform, note=note, params=params,
                     branch=branch)
    assert derivation_seen == list(expected) and set(derivation_seen) == {"ERA"}, \
        "retraction not executed as licensed ERA"
    return pc


def challenge_step(
    pc: ProofChain,
    *,
    subgraph_egif: Optional[str] = None,
    relation: Optional[str] = None,
    labels: Optional[List[Optional[str]]] = None,
    fact_egif: Optional[str] = None,
    disposition: str = "challenge_to_M",
    mode: str = "abduction",
    reason: Optional[str] = None,
    note: Optional[str] = None,
    branch: Optional[str] = None,
) -> ProofChain:
    """The **challenge-to-M composite** — the black-swan move as ONE recorded
    ``REVISE_M`` step: ERA the impugned law (``subgraph_egif``) and/or atoms
    (``relation``) inside their cells, then INS the refuting anomaly
    (``fact_egif``) as a fresh cell. The derivation records the executed
    licensed list (e.g. ``["ERA", "INS"]``); the emptied husk stands as the
    scar; the DAG keeps the pre-challenge world."""
    scroll = find_world_scroll(pc.current)
    if scroll is None:
        raise ValueError("challenge_step needs a standing world-scroll")
    if not (subgraph_egif or relation) and not fact_egif:
        raise ValueError("challenge_step requires something to relinquish "
                         "and/or an anomaly to admit")

    derivation_seen: List[str] = []

    def transform(g):
        out = g
        if subgraph_egif or relation:
            out, derivation = retract_from_m(
                out, subgraph_egif=subgraph_egif, relation=relation,
                labels=labels)
            derivation_seen.extend(derivation)
        if fact_egif:
            out = enlarge_m(out, fact_egif)
            derivation_seen.append("INS")
        return out

    # Dry-run to learn the executed derivation (deterministic; see retract_step)
    transform(pc.current)
    expected, derivation_seen = list(derivation_seen), []

    params = {
        "act": "m_revision",
        "earned": True,
        "derivation": expected,
        "disposition": disposition,
        "mode": mode,
    }
    if subgraph_egif:
        params["subgraph_egif"] = subgraph_egif
    if relation:
        params["relation"] = relation
    if labels is not None:
        params["labels"] = list(labels)
    if fact_egif:
        params["fact_egif"] = fact_egif
    if reason:
        params["reason"] = reason
    pc.apply_derived(REVISE_M, transform, note=note, params=params,
                     branch=branch)
    assert derivation_seen == expected, "challenge not executed as recorded"
    return pc


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
    ERA / DC+ / INS triple), recorded as one explicit ``REVISE_M`` step —
    under cells, the *rare* full-replacement path (husk removal / wholesale
    resupply); piecemeal relinquishment is :func:`retract_step`.
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


__all__ = ["PEEL", "ADMIT_TO_M", "RETRACT_FROM_M", "REVISE_M",
           "peel_step", "admit_step", "retract_step", "challenge_step",
           "revise_step"]
