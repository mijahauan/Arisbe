"""Enumerate the branches of a persisted reasoning chain — the orientation
substrate for the history navigation.

A ``TransformationChain`` is a DAG in general: two steps sharing a
``from_state_id`` **fork** a line of development, two sharing a
``to_state_id`` **converge** it (the alternate-proofs diamond). The topology
lives entirely in those ids; ``ChainStep.branch_id`` is a human label for
grouping and colouring (see ``tomos_service.ChainStep``). Until now that
label was write-only and no consumer could answer *"which branch am I on,
and how many are there?"* — the Transparency Charter P1 question a reader
of a branching UoD must be able to answer from visible text alone.

This module is that answer's data half:

* a **branch** is one root→leaf path, enumerated in authored step order
  (branch 0 = the earliest-authored line = "main" — Ergasterion's
  vocabulary, one word everywhere per charter P2);
* a branch is tracked by its **steps**, not its states — the convergence
  diamond makes a state id ambiguous (``possible_and_necessary``'s s2 is
  reached by two different steps), so paths key on ``step_id``;
* a state may belong to **several** branches (the shared prefix; a
  convergence state) — ``membership`` says which, and the UI renders that
  honestly ("lines converge here") rather than pretending exclusivity;
* labels: the ordered-unique non-null ``branch_id``s along the line, joined
  with ``" → "`` (a line may be relabeled mid-journey:
  ``"prosperity → late-ruin"``); fallback ``"main"`` / ``"branch N"``.

Pure and geometry-free — walks only ids (the same walk as
``modal_query._adjacency``, kept local so this module depends on nothing
but the chain shape); adds no §3.3 obligation. Never raises on a weird
chain: a corrupted cycle edge is skipped and a runaway DAG is capped, both
reported via ``truncated``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from tomos_service import ChainStep, TransformationChain

# A runaway backstop, far above any real episode (the biggest corpus chain
# has 2 branches). Enumeration stops here and reports truncated=True.
MAX_BRANCHES = 64


@dataclass(frozen=True)
class Branch:
    """One line of development: a root→leaf path through the chain."""

    index: int                 # stable: authored-order DFS; 0 = "main"
    label: str                 # "wind-rises" | "prosperity → late-ruin" | "main" | "branch 2"
    state_ids: List[str]       # root→leaf, initial state first, leaf last
    step_ids: List[str]        # the path's steps in order (len == len(state_ids) - 1)
    leaf_state_id: str
    step_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "label": self.label,
            "state_ids": list(self.state_ids),
            "step_ids": list(self.step_ids),
            "leaf_state_id": self.leaf_state_id,
            "step_count": self.step_count,
        }


@dataclass(frozen=True)
class BranchReport:
    """The full orientation picture of a chain's DAG."""

    branching: bool
    truncated: bool
    branches: List[Branch]
    membership: Dict[str, List[int]]           # state_id -> branch indices
    fork_state_ids: List[str]                  # >1 outgoing step
    convergence_state_ids: List[str]           # >1 incoming step
    continuations: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.branches)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branching": self.branching,
            "count": self.count,
            "truncated": self.truncated,
            "branches": [b.to_dict() for b in self.branches],
            "membership": {k: list(v) for k, v in self.membership.items()},
            "fork_state_ids": list(self.fork_state_ids),
            "convergence_state_ids": list(self.convergence_state_ids),
            "continuations": {
                k: [dict(c) for c in v] for k, v in self.continuations.items()
            },
        }


def _children(chain: TransformationChain) -> Dict[str, List[ChainStep]]:
    """state id → its outgoing steps, in authored order (the DFS visit order,
    so branch 0 is the earliest-authored line)."""
    out: Dict[str, List[ChainStep]] = {}
    for step in chain.steps:
        out.setdefault(step.from_state_id, []).append(step)
    return out


def _labels_along(steps: List[ChainStep]) -> List[str]:
    """The ordered-unique non-null branch_id labels along a step sequence."""
    seen: List[str] = []
    for s in steps:
        if s.branch_id and s.branch_id not in seen:
            seen.append(s.branch_id)
    return seen


def _label_for(index: int, steps: List[ChainStep]) -> str:
    labels = _labels_along(steps)
    if labels:
        return " → ".join(labels)
    return "main" if index == 0 else f"branch {index}"


def branch_report(chain: TransformationChain) -> BranchReport:
    """Enumerate the chain's branches (one per root→leaf path) and the
    orientation maps the UI needs. Deterministic; never raises."""
    children = _children(chain)
    root = chain.initial_state_id

    truncated = False
    paths: List[List[ChainStep]] = []

    def dfs(state: str, path: List[ChainStep], on_path: set) -> None:
        nonlocal truncated
        if len(paths) >= MAX_BRANCHES:
            truncated = True
            return
        outgoing = children.get(state, [])
        if not outgoing:
            paths.append(list(path))
            return
        for step in outgoing:
            if step.to_state_id in on_path:
                truncated = True  # a corrupted cycle edge — skip, report
                continue
            path.append(step)
            on_path.add(step.to_state_id)
            dfs(step.to_state_id, path, on_path)
            on_path.discard(step.to_state_id)
            path.pop()

    dfs(root, [], {root})
    if not paths:
        paths = [[]]  # a bare initial state is one (empty) line

    branches: List[Branch] = []
    for i, steps in enumerate(paths):
        state_ids = [root] + [s.to_state_id for s in steps]
        branches.append(Branch(
            index=i,
            label=_label_for(i, steps),
            state_ids=state_ids,
            step_ids=[s.step_id for s in steps],
            leaf_state_id=state_ids[-1],
            step_count=len(steps),
        ))

    membership: Dict[str, List[int]] = {}
    for b in branches:
        for sid in b.state_ids:
            entry = membership.setdefault(sid, [])
            if b.index not in entry:
                entry.append(b.index)

    incoming: Dict[str, int] = {}
    for step in chain.steps:
        incoming[step.to_state_id] = incoming.get(step.to_state_id, 0) + 1
    fork_state_ids = [sid for sid, outs in children.items() if len(outs) > 1]
    convergence_state_ids = [sid for sid, n in incoming.items() if n > 1]

    # Per fork: one continuation per outgoing step, labeled by the labels
    # from that step onward on its (first) containing branch — so the fork
    # cue can say "wind-rises | clears-first" even where the shared prefix
    # is unlabeled.
    step_to_branches: Dict[str, List[int]] = {}
    for b in branches:
        for sid in b.step_ids:
            step_to_branches.setdefault(sid, []).append(b.index)
    branch_steps = {b.index: steps for b, steps in zip(branches, paths)}

    continuations: Dict[str, List[Dict[str, Any]]] = {}
    for fork in fork_state_ids:
        conts = []
        for step in children[fork]:
            owners = step_to_branches.get(step.step_id, [])
            label = None
            if owners:
                owner_steps = branch_steps[owners[0]]
                at = next(
                    (k for k, s in enumerate(owner_steps)
                     if s.step_id == step.step_id), 0)
                suffix_labels = _labels_along(owner_steps[at:])
                label = (" → ".join(suffix_labels) if suffix_labels
                         else branches[owners[0]].label)
            conts.append({
                "to_state_id": step.to_state_id,
                "step_id": step.step_id,
                "rule": step.rule_name,
                "label": label or "?",
                "branch_indices": owners,
            })
        continuations[fork] = conts

    return BranchReport(
        branching=len(branches) > 1,
        truncated=truncated,
        branches=branches,
        membership=membership,
        fork_state_ids=sorted(fork_state_ids),
        convergence_state_ids=sorted(convergence_state_ids),
        continuations=continuations,
    )


__all__ = ["Branch", "BranchReport", "branch_report", "MAX_BRANCHES"]
