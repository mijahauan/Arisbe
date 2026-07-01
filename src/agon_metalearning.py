"""Meta-learning — the game studying the game.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §6. Because the referee is
mechanical and runs are reproducible (seeded, mocked, or replayed), the automated
Endoporeutic Game is a *microscope on its own rules*. Every round already logs a
checkable tuple — ``(M, G, verdict, the vote slate, the disposition, did-it-stick)`` — and
over many rounds the questions this module answers are empirical, not stipulated:

* **Resolution principles** (:func:`resolution_principles`) — group rounds by *situation*
  (a compact signature: the verdict + the proposal's shape) and ask which disposition each
  situation resolves to. A situation that always maps to ONE disposition is an
  empirically-discovered resolution principle; one that maps to several *thrashes* — a sign
  the rules are ambiguous or a disposition is missing. The hand-assigned dispositions get
  *tested*, not assumed.
* **The friction map** (:func:`friction_map`) — where the agents most disagree (the vote
  slate carries >1 distinct disposition, or the judge branched the DAG) localizes the
  *underspecified* parts of the rules. Smooth functioning = fast, low-disagreement
  resolution; the friction map says which rules to sharpen.
* **Stability** (:func:`stability_report`) — did M settle, how fast, did it thrash, how big
  did it get — the per-run measures an ablation compares.
* **Ablation** (:func:`run_ablation`) — vary the panel / disuse-ttl / disposition priorities
  and *measure* the effect on stabilization. Resolution principles become tested parameters,
  not stipulations.

Geometry-free and deterministic: it reads only the ``EvolutionResult`` an
``agon_evolution.run`` already returns, so it adds no §3.3 obligation (the trajectory is
attested where it is *saved*, unchanged). Nothing here promotes anything to the corpus —
it is a lens on runs, in the *correspondence-not-truth* register (a stable principle is a
regularity of the game, not a truth about the world; "progression, not progress").
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from egif_parser_dau import parse_egif
from eg_navigation import area_of, child_cuts, same_graph

from agon_evolution import EvolutionResult, RoundOutcome, Proposer, run


# --------------------------------------------------------------------------- #
# The situation signature — how a round is classified for mining               #
# --------------------------------------------------------------------------- #

def proposal_shape(egif: str) -> str:
    """A coarse structural class of a proposal G, the half of a *situation* the verdict does
    not carry. ``ground`` (a conjunction of atoms, no cut), ``law`` (a scroll — a sheet cut
    holding a nested cut), ``counterexample`` (a positive atom *and* a negation on the sheet —
    the black-swan shape that refutes a law), ``negation`` (a bare sheet-level negation), or
    ``empty``."""
    try:
        g = parse_egif(egif)
    except Exception:
        return "unparseable"
    cuts = child_cuts(g, g.sheet)
    sheet_atoms = [e for e in g.E if area_of(g, e.id) == g.sheet and e.id in g.rel]
    if not cuts:
        return "ground" if sheet_atoms else "empty"
    if any(child_cuts(g, c) for c in cuts):
        return "law"
    return "counterexample" if sheet_atoms else "negation"


def situation_of(proposal_egif: str, verdict: str) -> str:
    """The compact ``verdict:shape`` signature a round is grouped by. Interpretable and
    stable — the unit over which resolution principles and friction are mined."""
    return f"{verdict}:{proposal_shape(proposal_egif)}"


# --------------------------------------------------------------------------- #
# The episode record — one round, plus whether its move *stuck*                #
# --------------------------------------------------------------------------- #

@dataclass
class EpisodeRecord:
    """One round as a mining datum: the situation, the vote slate, the resolved disposition,
    the siblings branched, and whether the move *stuck* (its effect survives in the final M).
    ``disagreement`` counts distinct dispositions the agents proposed (0 = unanimous)."""
    run_id: str
    round_idx: int
    situation: str
    verdict: str
    proposal_egif: str
    disposition: Optional[str]
    slate: List[str]
    branched: List[str]
    disagreement: int
    stuck: Optional[bool]   # None ⇒ a non-revising round (nothing to stick)


def _sheet_relations(egif_graph) -> Set[str]:
    return {
        egif_graph.rel[e.id]
        for e in egif_graph.E
        if area_of(egif_graph, e.id) == egif_graph.sheet and e.id in egif_graph.rel
    }


def _relations_of(egif: str) -> Set[str]:
    try:
        g = parse_egif(egif)
    except Exception:
        return set()
    return {g.rel[e.id] for e in g.E if e.id in g.rel}


def _stuck(outcome: RoundOutcome, result: EvolutionResult,
           final_relations: Set[str]) -> Optional[bool]:
    """Did this revising round's move survive to the end of the trajectory?

      * a *relinquishment* (``challenge_to_M`` / ``retract_fact``) reshaped M by removing
        content — it stands unless something re-added it; we read it as stuck (an event that
        happened), which the run's later rounds do not undo in the closed loop.
      * a *generalization* / conditional (a law) sticks iff the law is still among the final
        ``known_laws`` (a later ``challenge_to_M`` may have relinquished it — ``_discoveries``
        calls that ``superseded_law``).
      * any other *enlargement* (a fact/definition/…) sticks iff its relations are all still
        present on the final sheet (disuse-decay or a challenge may have erased them).
    """
    disp = outcome.disposition
    if disp is None:
        return None
    if disp in ("challenge_to_M", "retract_fact"):
        return True
    if disp in ("generalization", "conditional_acceptance"):
        return any(same_graph(parse_egif(l), parse_egif(outcome.proposal_egif))
                   for l in result.known_laws)
    added = _relations_of(outcome.proposal_egif)
    return bool(added) and added <= final_relations


def is_stuck(outcome: RoundOutcome, result: EvolutionResult) -> Optional[bool]:
    """Whether ``outcome``'s revising move survived to the final M (``None`` for a non-revising
    round). The public entry to the stickiness reader — used by open membranes that build their
    own episode records (e.g. ``wiki_dispute_membrane``)."""
    return _stuck(outcome, result, _sheet_relations(result.uod.current_egi))


def episodes_from(result: EvolutionResult, *, run_id: str = "run") -> List[EpisodeRecord]:
    """Turn one run's outcomes into mining records — the ``(M, G, verdict, slate, disposition,
    did-it-stick)`` tuples §6 mines over."""
    final_relations = _sheet_relations(result.uod.current_egi)
    records: List[EpisodeRecord] = []
    for o in result.outcomes:
        dispositions = [d for _agent, d in o.votes]
        records.append(EpisodeRecord(
            run_id=run_id,
            round_idx=o.round_idx,
            situation=situation_of(o.proposal_egif, o.verdict),
            verdict=o.verdict,
            proposal_egif=o.proposal_egif,
            disposition=o.disposition,
            slate=dispositions,
            branched=list(o.branched),
            disagreement=max(0, len(set(dispositions)) - 1) + len(o.branched),
            stuck=_stuck(o, result, final_relations),
        ))
    return records


# --------------------------------------------------------------------------- #
# §6 — resolution principles mined from self-play                              #
# --------------------------------------------------------------------------- #

@dataclass
class Principle:
    """A ``situation → disposition`` regularity mined from many rounds. ``stability`` is the
    fraction of the situation's *revising* rounds that chose the dominant disposition (1.0 = a
    clean discovered principle); ``thrash`` marks a situation whose revising rounds split
    across several dispositions (ambiguity or a missing rule). ``stick_rate`` is how often the
    resolved move survived."""
    situation: str
    dominant: Optional[str]
    stability: float
    support: int                    # number of revising rounds in this situation
    distribution: Dict[str, int]
    thrash: bool
    stick_rate: Optional[float]


def resolution_principles(episodes: Sequence[EpisodeRecord]) -> List[Principle]:
    """Mine the stable ``(situation → disposition)`` mappings. Each situation's *revising*
    rounds are tallied; the dominant disposition and its fraction give the principle, and a
    split (>1 disposition, dominant <1.0) flags a thrash. Sorted most-supported first."""
    by_sit: Dict[str, List[EpisodeRecord]] = defaultdict(list)
    for e in episodes:
        if e.disposition is not None:
            by_sit[e.situation].append(e)

    principles: List[Principle] = []
    for situation, recs in by_sit.items():
        dist = Counter(e.disposition for e in recs)
        dominant, top = dist.most_common(1)[0]
        support = sum(dist.values())
        stability = top / support
        stuck = [e.stuck for e in recs if e.stuck is not None]
        principles.append(Principle(
            situation=situation,
            dominant=dominant,
            stability=stability,
            support=support,
            distribution=dict(dist),
            thrash=len(dist) > 1 and stability < 1.0,
            stick_rate=(sum(stuck) / len(stuck)) if stuck else None,
        ))
    principles.sort(key=lambda p: (-p.support, p.situation))
    return principles


# --------------------------------------------------------------------------- #
# §6 — the friction map                                                        #
# --------------------------------------------------------------------------- #

@dataclass
class FrictionPoint:
    """How contested a situation is: the mean disagreement across its rounds (distinct
    dispositions voted, plus branches) — high friction localizes an underspecified rule."""
    situation: str
    rounds: int
    mean_disagreement: float
    max_disagreement: int
    branched_rounds: int


def friction_map(episodes: Sequence[EpisodeRecord]) -> List[FrictionPoint]:
    """Aggregate per-round disagreement into a friction map over situations, most-contested
    first — the design's "where the agents most disagree localizes the underspecified parts of
    the rules."""
    by_sit: Dict[str, List[EpisodeRecord]] = defaultdict(list)
    for e in episodes:
        by_sit[e.situation].append(e)

    points: List[FrictionPoint] = []
    for situation, recs in by_sit.items():
        disagreements = [e.disagreement for e in recs]
        points.append(FrictionPoint(
            situation=situation,
            rounds=len(recs),
            mean_disagreement=sum(disagreements) / len(recs),
            max_disagreement=max(disagreements),
            branched_rounds=sum(1 for e in recs if e.branched),
        ))
    points.sort(key=lambda p: (-p.mean_disagreement, -p.rounds, p.situation))
    return points


def gaps(episodes: Sequence[EpisodeRecord]) -> List[str]:
    """Candidate *missing rules*: situations the game handled **inconsistently** — sometimes
    revising, sometimes leaving M untouched (a non-revising round) — which flags either a
    missing disposition or an ambiguous rule. Reported as human-readable lines."""
    by_sit: Dict[str, Counter] = defaultdict(Counter)
    for e in episodes:
        by_sit[e.situation]["revising" if e.disposition else "inert"] += 1
    out: List[str] = []
    for situation, c in sorted(by_sit.items()):
        if c["revising"] and c["inert"]:
            out.append(
                f"{situation}: handled {c['revising']}× by a disposition and {c['inert']}× "
                f"left inert — a candidate missing/ambiguous rule.")
    return out


# --------------------------------------------------------------------------- #
# §6 — per-run stability (what an ablation compares)                           #
# --------------------------------------------------------------------------- #

@dataclass
class StabilityReport:
    """Whether and how a run settled. ``rounds`` total; ``revising`` = rounds that changed M;
    ``settle_round`` = the last revising round (``None`` if M never changed) — a run that
    stops revising early has *settled*; ``thrash_situations`` split across dispositions;
    ``branched`` rounds forked the DAG; ``final_m_relations`` sizes the resulting sheet."""
    run_id: str
    rounds: int
    revising: int
    settle_round: Optional[int]
    thrash_situations: int
    branched: int
    final_m_relations: int


def stability_report(result: EvolutionResult, *, run_id: str = "run") -> StabilityReport:
    """Summarize how a run settled — the per-run measure :func:`run_ablation` compares across
    parameter variants."""
    episodes = episodes_from(result, run_id=run_id)
    revising = [e for e in episodes if e.disposition is not None]
    thrash = sum(1 for p in resolution_principles(episodes) if p.thrash)
    return StabilityReport(
        run_id=run_id,
        rounds=len(episodes),
        revising=len(revising),
        settle_round=(revising[-1].round_idx if revising else None),
        thrash_situations=thrash,
        branched=sum(1 for e in episodes if e.branched),
        final_m_relations=len(_sheet_relations(result.uod.current_egi)),
    )


# --------------------------------------------------------------------------- #
# §6 — the ablation harness                                                    #
# --------------------------------------------------------------------------- #

@dataclass
class AblationVariant:
    """One arm of an ablation: a label + the ``run`` keyword overrides that define it (e.g. a
    different ``panel``, a ``ttl`` for disuse-decay, a ``standing_proposal``)."""
    label: str
    run_kwargs: Dict[str, object] = field(default_factory=dict)


@dataclass
class AblationResult:
    label: str
    stability: StabilityReport
    principles: List[Principle]


def run_ablation(
    model_egif: str,
    proposer_factory: Callable[[], Proposer],
    variants: Sequence[AblationVariant],
    *,
    rounds: int,
    uod_id: str = "ablation",
    name: str = "ablation run",
) -> List[AblationResult]:
    """Run the loop once per variant (a **fresh** proposer each, from ``proposer_factory``, so
    a stateful membrane is not shared) and measure stabilization — the design's "vary the
    doubt schedule / parsimony weight / branch-vs-force policy and measure." Deterministic
    given deterministic proposers; geometry-free (§3.3 fires only where a run is *saved*)."""
    results: List[AblationResult] = []
    for v in variants:
        res = run(model_egif, proposer_factory(), rounds=rounds,
                  uod_id=f"{uod_id}_{v.label}", name=f"{name} — {v.label}",
                  **v.run_kwargs)  # type: ignore[arg-type]
        results.append(AblationResult(
            label=v.label,
            stability=stability_report(res, run_id=v.label),
            principles=resolution_principles(episodes_from(res, run_id=v.label)),
        ))
    return results


# --------------------------------------------------------------------------- #
# §6 — learning from disputes (conflict + resolution structure)               #
# --------------------------------------------------------------------------- #
#
# A wiki-style dispute (``wiki_dispute_membrane``) carries structure a bare round does not: an
# edit-war intensity (``reverts``) and an editorial *resolution mechanism* (a reliable-source
# citation / consensus / admin / unresolved). That lets the game *learn what wiki conflicts
# teach* — not just replay them:
#
#   * which mechanism produces DURABLE knowledge — a reliable-source resolution that overturns a
#     prior consensus should *stick* where the consensus did not (``mechanism_principles``);
#   * where the contested frontier is — the edit wars, ranked (``edit_war_friction``);
#   * what stays open — the claims no mechanism settled (``unresolved_frontier``), the honest ◇.

@dataclass
class DisputeEpisode:
    """One resolved (or unresolved) dispute as a learning datum: the claim, how it ended
    (``mechanism`` / ``settled``), its edit-war intensity (``reverts``), the loop's
    ``disposition``, and whether that move *stuck* in the final M."""
    claim_egif: str
    mechanism: str
    settled: Optional[bool]
    reverts: int
    disposition: Optional[str]
    stuck: Optional[bool]


@dataclass
class MechanismPrinciple:
    """What a *resolution mechanism* empirically buys: how often its resolutions took hold. A
    mechanism whose resolutions all stick (``stick_rate == 1.0``) is ``durable`` — the learned
    finding that (say) reliable-source citations produce lasting knowledge where consensus, when
    overturned, does not."""
    mechanism: str
    count: int
    dominant_disposition: Optional[str]
    stick_rate: Optional[float]
    durable: bool


def mechanism_principles(episodes: Sequence[DisputeEpisode]) -> List[MechanismPrinciple]:
    """Mine, per resolution mechanism, its dominant disposition and its **stick-rate** — the
    heart of learning from wiki conflicts: *which way of resolving a dispute produces durable
    knowledge.* Sorted most-used first."""
    by_mech: Dict[str, List[DisputeEpisode]] = defaultdict(list)
    for e in episodes:
        by_mech[e.mechanism].append(e)

    out: List[MechanismPrinciple] = []
    for mechanism, recs in by_mech.items():
        dispositions = Counter(e.disposition for e in recs if e.disposition is not None)
        dominant = dispositions.most_common(1)[0][0] if dispositions else None
        stuck = [e.stuck for e in recs if e.stuck is not None]
        rate = (sum(stuck) / len(stuck)) if stuck else None
        out.append(MechanismPrinciple(
            mechanism=mechanism,
            count=len(recs),
            dominant_disposition=dominant,
            stick_rate=rate,
            # an unresolved dispute never yields *durable knowledge*, even if its tentative
            # low-warrant posit happened to linger unchallenged this run.
            durable=(rate == 1.0 and mechanism != "unresolved"),
        ))
    out.sort(key=lambda p: (-p.count, p.mechanism))
    return out


def edit_war_friction(episodes: Sequence[DisputeEpisode]) -> List[DisputeEpisode]:
    """The disputes ranked by contestedness (reverts, then whether still unsettled) — where the
    edit wars are, i.e. the frontier the rules are most stressed on."""
    return sorted(
        episodes,
        key=lambda e: (-e.reverts, e.settled is not None),
    )


def unresolved_frontier(episodes: Sequence[DisputeEpisode]) -> List[str]:
    """The claims no mechanism settled (``mechanism == 'unresolved'`` or ``settled is None``) —
    the honest ◇-contested horizon the modal lens would read as *possible, not necessary*."""
    return [e.claim_egif for e in episodes
            if e.mechanism == "unresolved" or e.settled is None]


__all__ = [
    "proposal_shape", "situation_of",
    "EpisodeRecord", "episodes_from", "is_stuck",
    "Principle", "resolution_principles",
    "FrictionPoint", "friction_map", "gaps",
    "StabilityReport", "stability_report",
    "AblationVariant", "AblationResult", "run_ablation",
    "DisputeEpisode", "MechanismPrinciple", "mechanism_principles",
    "edit_war_friction", "unresolved_frontier",
]
