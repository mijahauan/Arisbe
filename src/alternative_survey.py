"""Survey producers for the alternatives register — the emergence half of
Tasks 5–6 (spec 2026-07-26-close-the-arc-tasks-5-6-design §2).

Both surveys are PEEL-twins (Task 4 adds the recording steps): pure,
deterministic readers whose whole result rides in step params, recomputable
forever. Every surfaced question is the proven interrogative pair re-emerged
(D-1): the {atom, denial} alternatives, differing only in emergence ink.

D-2: only ZERO-grounded thin spots become questions — a 1-instance
relation's ``(r *x)`` already holds (the instance witnesses the existential;
a record would be born settled); those and lonely individuals are named,
recordless — the docket's beat. D-3: only ground atoms contested across
reachable futures and not held at the reference state become questions.

The structural readers mirror ``agon_llm.attention_brief``'s (kept local so
this module never imports the LLM layer)."""
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from eg_navigation import area_of, child_cuts
from egi_core_dau import RelationalGraphWithCuts
from world_scroll import m_view


@dataclass(frozen=True)
class ThinSpotSurvey:
    """What the thin-spot survey saw: surfaced unknowns + the named-recordless
    remainder (honest full brief)."""
    unknowns: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]
    thin_but_grounded: Tuple[str, ...]
    lonely_individuals: Tuple[str, ...]


@dataclass(frozen=True)
class BranchSurvey:
    """What the branch survey saw: fork states, contested-across-futures
    ground atoms, and the ◇-not-□ evidence (witness/counterexample leaves)
    per surfaced atom, keyed by alt_key."""
    fork_states: Tuple[str, ...]
    unknowns: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]
    evidence: Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...]], ...]


def _sheet_ground_atoms(egi: RelationalGraphWithCuts
                        ) -> Set[Tuple[str, Tuple[Optional[str], ...]]]:
    """Sheet-level atoms of M through m_view (generic slots read None)."""
    m = m_view(egi)
    out: Set[Tuple[str, Tuple[Optional[str], ...]]] = set()
    for e in m.E:
        if e.id in m.rel and area_of(m, e.id) == m.sheet:
            labels = tuple(m.get_vertex(v).label for v in m.nu.get(e.id, ()))
            out.add((m.rel[e.id], labels))
    return out


def _model_laws(egi: RelationalGraphWithCuts) -> List[Tuple[str, str]]:
    """(body, head) relation pairs of each standing scroll of M."""
    m = m_view(egi)
    laws: List[Tuple[str, str]] = []
    for outer in child_cuts(m, m.sheet):
        inner = child_cuts(m, outer)
        if not inner:
            continue
        body = next((m.rel[e.id] for e in m.E
                     if area_of(m, e.id) == outer and e.id in m.rel), None)
        head = next((m.rel[e.id] for e in m.E
                     if area_of(m, e.id) == inner[0] and e.id in m.rel), None)
        if body and head:
            laws.append((body, head))
    return laws


def survey_thin_spots(egi: RelationalGraphWithCuts) -> ThinSpotSurvey:
    """Read M for zero-grounded vocabulary relations and ungrounded law
    bodies (→ the unary existential question ``(r *x)`` each), naming the
    1-instance relations and lonely individuals recordless (D-2)."""
    from dl_reasoning import ontology_signature
    vocabulary = sorted(ontology_signature(egi))
    atoms = _sheet_ground_atoms(egi)
    rel_counts = Counter(r for r, _ in atoms)
    grounded = {r for r, _ in atoms}
    zero = {r for r in vocabulary if rel_counts.get(r, 0) == 0}
    zero |= {b for (b, _h) in _model_laws(egi) if b not in grounded}
    unknowns = tuple((r, (None,)) for r in sorted(zero))
    thin_but_grounded = tuple(sorted(
        r for r in vocabulary if rel_counts.get(r, 0) == 1))
    const_counts = Counter(
        lbl for _, labels in atoms for lbl in labels if lbl)
    lonely = tuple(sorted(c for c, n in const_counts.items() if n == 1))
    return ThinSpotSurvey(unknowns=unknowns,
                          thin_but_grounded=thin_but_grounded,
                          lonely_individuals=lonely)


def survey_branches(chain, *, upto: Optional[str] = None,
                    at: Optional[str] = None) -> BranchSurvey:
    """Enumerate fork states over the step prefix (all steps before ``upto``,
    or all steps) and surface the ground atoms contested across reachable
    leaves and not held at the reference state ``at`` (default: the prefix's
    current state). Pure DAG + m_view reading — recompute is re-reading."""
    from alternative_index import alt_key
    from modal_query import leaf_states
    from tomos_service import TransformationChain
    steps = list(chain.steps)
    if upto is not None:
        idx = next((i for i, s in enumerate(steps) if s.step_id == upto),
                   len(steps))
        steps = steps[:idx]
    prefix = TransformationChain(initial_state_id=chain.initial_state_id,
                                 steps=steps, states=chain.states)
    frm = Counter(s.from_state_id for s in steps)
    forks = tuple(sorted(sid for sid, n in frm.items() if n > 1))
    if not forks:
        return BranchSurvey((), (), ())
    ref = at if at is not None else prefix.current_state_id
    held = {a for a in _sheet_ground_atoms(chain.states[ref])
            if all(l is not None for l in a[1])}
    leaves = sorted(leaf_states(prefix))
    per_leaf: Dict[str, Set] = {
        leaf: {a for a in _sheet_ground_atoms(chain.states[leaf])
               if all(l is not None for l in a[1])}
        for leaf in leaves}
    universe = sorted(set().union(*per_leaf.values()))
    unknowns: List[Tuple[str, Tuple[Optional[str], ...]]] = []
    evidence: List[Tuple[str, Tuple[str, ...], Tuple[str, ...]]] = []
    for atom in universe:
        ins = tuple(l for l in leaves if atom in per_leaf[l])
        outs = tuple(l for l in leaves if atom not in per_leaf[l])
        if ins and outs and atom not in held:
            unknowns.append(atom)
            evidence.append((alt_key(atom[0], atom[1]), ins, outs))
    return BranchSurvey(fork_states=forks, unknowns=tuple(unknowns),
                        evidence=tuple(evidence))


SURVEY_THIN_SPOTS = "SURVEY_THIN_SPOTS"
THIN_SPOTS_ACT = "thin_spots_surveyed"
SURVEY_BRANCHES = "SURVEY_BRANCHES"
BRANCHES_ACT = "branches_surveyed"

_KIND_BY_ACT = {THIN_SPOTS_ACT: "hypothetical", BRANCHES_ACT: "modal"}


def _star(labels) -> List[str]:
    return ["*" if l is None else l for l in labels]


def thin_spot_step(pc, *, budget: int = 8, note: Optional[str] = None,
                   branch: Optional[str] = None) -> ThinSpotSurvey:
    """Record the thin-spot survey as a PEEL-twin identity step, earned at
    record time: the scan actually runs against pc.current; params carry the
    whole result; the gate recomputes it forever. Over-budget surfacings are
    refused-and-counted, never dropped."""
    from alternative_index import alt_key
    survey = survey_thin_spots(pc.current)
    surfaced = survey.unknowns[:budget]
    refused = survey.unknowns[budget:]
    params = {
        "act": THIN_SPOTS_ACT, "earned": True, "budget": budget,
        "unknown_atoms": [[r, _star(labels)] for r, labels in surfaced],
        "refused_budget": [alt_key(r, labels) for r, labels in refused],
        "thin_but_grounded": list(survey.thin_but_grounded),
        "lonely_individuals": list(survey.lonely_individuals),
    }
    pc.apply_derived(SURVEY_THIN_SPOTS, lambda g: g,
                     note=note or "thin-spot survey", params=params,
                     branch=branch)
    return survey


def branch_survey_step(pc, *, budget: int = 8, at: Optional[str] = None,
                       note: Optional[str] = None,
                       branch: Optional[str] = None) -> BranchSurvey:
    """Record the branch survey as a PEEL-twin identity step over the steps
    recorded so far (recompute = re-survey the prefix before this step)."""
    from alternative_index import alt_key
    ref = at if at is not None else pc.current_state_id
    survey = survey_branches(pc.to_chain(), at=ref)
    surfaced = survey.unknowns[:budget]
    refused = survey.unknowns[budget:]
    keys = {alt_key(r, labels) for r, labels in surfaced}
    params = {
        "act": BRANCHES_ACT, "earned": True, "budget": budget, "at": ref,
        "fork_states": list(survey.fork_states),
        "unknown_atoms": [[r, _star(labels)] for r, labels in surfaced],
        "refused_budget": [alt_key(r, labels) for r, labels in refused],
        "evidence": [[k, list(ins), list(outs)]
                     for k, ins, outs in survey.evidence if k in keys],
    }
    pc.apply_derived(SURVEY_BRANCHES, lambda g: g,
                     note=note or "branch survey", params=params,
                     branch=branch)
    return survey


def records_from_survey_step(step, *, round_idx: int = 0) -> List:
    """Mint AlternativeRecords from a recorded survey step's params alone —
    the survey twin of record_from_trace_step (the index stays a cache over
    the chain). Kind by act (D-1: one pair, three emergences)."""
    from alternative_index import AlternativeRecord, alt_key
    from alternative_trace import UnrepresentableAtomError, atom_and_denial_egif
    p = step.parameters or {}
    kind = _KIND_BY_ACT.get(p.get("act"))
    if kind is None:
        raise ValueError(f"step {step.step_id} is not a survey step")
    out: List[AlternativeRecord] = []
    for rel, labels in (p.get("unknown_atoms") or []):
        labs = tuple(None if l == "*" else l for l in labels)
        try:
            atom, denial = atom_and_denial_egif(rel, labs)
        except UnrepresentableAtomError:
            continue                      # refused at survey time too
        out.append(AlternativeRecord(
            key=alt_key(rel, labs), relation=rel, labels=labs,
            alternatives=(atom, denial), kind=kind,
            emerged_from=step.step_id, emerged_round=round_idx,
            last_touched_round=round_idx))
    return out


__all__ = ["ThinSpotSurvey", "BranchSurvey", "survey_thin_spots",
           "survey_branches", "SURVEY_THIN_SPOTS", "THIN_SPOTS_ACT",
           "SURVEY_BRANCHES", "BRANCHES_ACT", "thin_spot_step",
           "branch_survey_step", "records_from_survey_step"]
