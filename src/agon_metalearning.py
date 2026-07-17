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

import json
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
    ``disagreement`` counts distinct dispositions the agents proposed (0 = unanimous).
    ``stuck`` is ``None`` both for a non-revising round (nothing to stick) and for a move whose
    content later fell to **disuse-decay** — falling out of the working set is no evidence about
    durability either way, so it must not read as *relinquished*; ``erased_by_decay``
    distinguishes the two."""
    run_id: str
    round_idx: int
    situation: str
    verdict: str
    proposal_egif: str
    disposition: Optional[str]
    slate: List[str]
    branched: List[str]
    disagreement: int
    stuck: Optional[bool]   # None ⇒ non-revising, or erased by decay (see erased_by_decay)
    erased_by_decay: bool = False


def _sheet_relations(egif_graph) -> Set[str]:
    """M's standing relation names — read through ``m_view`` (identity on a
    bare sheet-level graph), so a resident M's cells count (sweep #2)."""
    from world_scroll import m_view
    egif_graph = m_view(egif_graph)
    return {
        egif_graph.rel[e.id]
        for e in egif_graph.E
        if area_of(egif_graph, e.id) == egif_graph.sheet and e.id in egif_graph.rel
    }


def _sheet_atoms(egif_graph) -> Set[Tuple[str, Tuple]]:
    """M's standing atoms as ``(relation, (labels…))`` — the atom-precise twin of
    :func:`_sheet_relations` (the atom-level decay rulebook's unit), read
    through ``m_view``."""
    from world_scroll import m_view
    egif_graph = m_view(egif_graph)
    return {
        (egif_graph.rel[e.id],
         tuple(egif_graph.get_vertex(v).label for v in egif_graph.nu.get(e.id, ())))
        for e in egif_graph.E
        if area_of(egif_graph, e.id) == egif_graph.sheet and e.id in egif_graph.rel
    }


def _relations_of(egif: str) -> Set[str]:
    try:
        g = parse_egif(egif)
    except Exception:
        return set()
    return {g.rel[e.id] for e in g.E if e.id in g.rel}


def _atom_from_key(key: str) -> Tuple[str, Tuple]:
    """An ``agon_evolution.atom_key`` string → the ``(relation, (labels…))`` tuple this
    module matches claims by. Tolerant of a pre-2026-07-03 name-level entry (returned as a
    never-matching sentinel rather than raising on an old in-flight result)."""
    try:
        relation, labels = json.loads(key)
        return relation, tuple(labels)
    except Exception:
        return key, ("<name-level>",)


def _last_erasures(result: EvolutionResult) -> Dict[Tuple[str, Tuple], str]:
    """``atom → how`` for the **last** time each sheet atom was erased during the run —
    ``"decay"`` (fell from use, ⑤; ``RoundOutcome.decayed`` carries atom keys) or
    ``"disposition"`` (a game move: ``retract_fact``'s pure denial names its atom). Within a
    round the revision applies before decay, so decay overwrites a same-round retraction —
    matching the loop's order. Atom-precise since the atom-level decay rulebook (2026-07-03):
    an atom decaying under a still-standing name must read decay, not durability."""
    how: Dict[Tuple[str, Tuple], str] = {}
    for o in result.outcomes:
        if o.disposition == "retract_fact":
            for atom in _atoms_of(o.proposal_egif):
                how[atom] = "disposition"
        for key in o.decayed:
            how[_atom_from_key(key)] = "decay"
    return how


def _stickiness(outcome: RoundOutcome, result: EvolutionResult,
                final_atoms: Set[Tuple[str, Tuple]], erasures: Dict[Tuple[str, Tuple], str]
                ) -> Tuple[Optional[bool], bool]:
    """``(stuck, erased_by_decay)`` — did this revising round's move survive to the end of the
    trajectory, and if not, did its content merely *fall from use*?

      * a *relinquishment* (``challenge_to_M`` / ``retract_fact``) reshaped M by removing
        content — it stands unless something re-added it; we read it as stuck (an event that
        happened), which the run's later rounds do not undo in the closed loop.
      * a *generalization* / conditional (a law) sticks iff the law is still among the final
        ``known_laws`` (a later ``challenge_to_M`` may have relinquished it — ``_discoveries``
        calls that ``superseded_law``).
      * any other *enlargement* (a fact/definition/…) sticks iff its **atoms** are all still
        present on the final sheet (atom-precise since the atom-level rulebook, 2026-07-03 —
        a claim's atom decaying under a surviving name is not durability). If atoms are gone
        and every missing atom's **last erasure was disuse-decay**, the move was not
        relinquished — it fell out of the working set, which is no evidence about durability
        either way → ``(None, True)``. Only an erasure the *game* performed reads
        ``(False, False)``.
    """
    disp = outcome.disposition
    if disp is None:
        return None, False
    if disp in ("challenge_to_M", "retract_fact"):
        return True, False
    if disp in ("generalization", "conditional_acceptance"):
        return any(same_graph(parse_egif(l), parse_egif(outcome.proposal_egif))
                   for l in result.known_laws), False
    added = _atoms_of(outcome.proposal_egif)
    if not added:
        return False, False
    missing = added - final_atoms
    if not missing:
        return True, False
    if all(erasures.get(atom) == "decay" for atom in missing):
        return None, True
    return False, False


def stickiness(outcome: RoundOutcome, result: EvolutionResult) -> Tuple[Optional[bool], bool]:
    """``(stuck, erased_by_decay)`` for one outcome — the public stickiness reader for open
    membranes that build their own episode records (e.g. ``wiki_dispute_membrane``). ``stuck``
    is ``None`` for a non-revising round *and* for a decay-erasure (excluded from stick-rates);
    ``erased_by_decay`` says which."""
    return _stickiness(outcome, result,
                       _sheet_atoms(result.uod.current_egi), _last_erasures(result))


def is_stuck(outcome: RoundOutcome, result: EvolutionResult) -> Optional[bool]:
    """Whether ``outcome``'s revising move survived to the final M (``None`` for a non-revising
    round **or** a disuse-decay erasure — use :func:`stickiness` to tell them apart)."""
    return stickiness(outcome, result)[0]


def _atoms_of(egif: str) -> Set[Tuple[str, Tuple]]:
    """Every atom of a graph as ``(relation, (labels…))`` — cuts included, so a denial
    ``~[ (rel …) ]`` yields the atom it denies."""
    try:
        g = parse_egif(egif)
    except Exception:
        return set()
    return {
        (g.rel[e.id], tuple(g.get_vertex(v).label for v in g.nu.get(e.id, ())))
        for e in g.E if e.id in g.rel
    }


def mark_relinquished(episodes: Sequence, result: EvolutionResult,
                      removed_laws: Sequence[str] = ()) -> int:
    """The mirror of :func:`mark_decayed`: retro-mark accumulated episodes whose admitted
    content a **later segment's game move** relinquished — this IS durability evidence, so the
    earlier admission flips to ``stuck=False``. ``result`` is the later segment: its
    ``retract_fact`` rounds name the denied atoms; ``removed_laws`` are laws a later challenge
    relinquished (the runner diffs its carried law registry). Call it on the episodes
    accumulated *before* the segment, then extend with the segment's own records (whose
    within-run stickiness is already correct). Returns how many were re-marked."""
    retracted: Set[Tuple[str, Tuple]] = set()
    for o in result.outcomes:
        if o.disposition == "retract_fact":
            retracted |= _atoms_of(o.proposal_egif)
    if not retracted and not removed_laws:
        return 0
    n = 0
    for e in episodes:
        if e.stuck is not True or e.disposition in ("challenge_to_M", "retract_fact"):
            continue
        claim = getattr(e, "claim_egif", None) or getattr(e, "proposal_egif", "")
        if e.disposition in ("generalization", "conditional_acceptance"):
            if any(same_graph(parse_egif(claim), parse_egif(l)) for l in removed_laws):
                e.stuck = False
                n += 1
            continue
        if retracted and _atoms_of(claim) & retracted:
            e.stuck = False
            n += 1
    return n


def mark_decayed(episodes: Sequence, dropped: Set[str]) -> int:
    """Retro-mark accumulated episodes whose admitted content later fell to disuse-decay
    **outside** the run that produced them — the ``LiveRunner`` decays across segments, after
    each segment's episodes were built. An episode counted ``stuck=True`` whose claim's
    relations were dropped flips to ``stuck=None`` + ``erased_by_decay=True`` (falling out of
    the working set must not read as durable *or* relinquished). Relinquishment episodes
    (``challenge_to_M`` / ``retract_fact``) are events that happened and stay stuck. Works on
    :class:`EpisodeRecord` and :class:`DisputeEpisode` alike. Returns how many were re-marked."""
    if not dropped:
        return 0
    n = 0
    for e in episodes:
        if e.stuck is not True or e.disposition in ("challenge_to_M", "retract_fact"):
            continue
        claim = getattr(e, "claim_egif", None) or getattr(e, "proposal_egif", "")
        rels = _relations_of(claim)
        if rels and rels & dropped:
            e.stuck = None
            e.erased_by_decay = True
            n += 1
    return n


def mark_decayed_atoms(episodes: Sequence, dropped: Set[Tuple[str, Tuple]]) -> int:
    """The atom-precise :func:`mark_decayed` (the atom-level decay rulebook, 2026-07-03):
    ``dropped`` is a set of ``(relation, (labels…))`` atoms the runner's cross-segment
    disuse-decay erased. An episode flips to ``stuck=None`` + ``erased_by_decay=True`` when
    the *specific atoms* its claim delivered fell from use — even while their relation name
    survives on other, still-warm atoms (which name-level marking could not see).
    Relinquishment episodes stay stuck, as in :func:`mark_decayed`."""
    if not dropped:
        return 0
    n = 0
    for e in episodes:
        if e.stuck is not True or e.disposition in ("challenge_to_M", "retract_fact"):
            continue
        claim = getattr(e, "claim_egif", None) or getattr(e, "proposal_egif", "")
        atoms = _atoms_of(claim)
        if atoms and atoms & dropped:
            e.stuck = None
            e.erased_by_decay = True
            n += 1
    return n


def episodes_from(result: EvolutionResult, *, run_id: str = "run") -> List[EpisodeRecord]:
    """Turn one run's outcomes into mining records — the ``(M, G, verdict, slate, disposition,
    did-it-stick)`` tuples §6 mines over."""
    final_atoms = _sheet_atoms(result.uod.current_egi)
    erasures = _last_erasures(result)
    records: List[EpisodeRecord] = []
    for o in result.outcomes:
        dispositions = [d for _agent, d in o.votes]
        stuck, by_decay = _stickiness(o, result, final_atoms, erasures)
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
            stuck=stuck,
            erased_by_decay=by_decay,
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
# §4d — the observable shadow of poise (an instrument, not a target)          #
# --------------------------------------------------------------------------- #
#
# Poise itself — "balance in a dance the inquiry bends" (§4d) — has no absolute frame to be
# measured in. What it casts is a *shadow on the trace*: over a window of rounds, read
#
#   * ENGAGEMENT  — the dance still moves (some rounds revise M);
#   * SETTLEMENT  — habits hold while they are held (no situation disposed inconsistently
#                   within the window — no thrash);
#   * ABSORPTION  — fresh irritations arrive (a relinquishment, a DAG branch, a sharp
#                   disagreement — Secondness intruding) and are disposed without cascading.
#
# A window with all three reads *poised*; one that fails reads toward a pole — RIGIDITY
# (settlement without engagement: nothing moves, the dance has stopped) or THRASH (engagement
# without settlement: the same situation disposed differently, relinquishments cascading). A
# STUMBLE is an event, never a failure; its measure is RECOVERY — how many rounds until a
# poised window resumes. Competence, on this reading, is that stumbles keep arriving AND keep
# being absorbed: a run with no stumbles and no engagement is not poised, it is dead.
#
# Everything is computed from the run's own trace — perspectival by construction, comparative
# across ablation arms, never a distance-to-truth. And it must never become a target: a player
# optimized to maximize this reading would learn to avoid stumbles by avoiding engagement, or
# to manufacture cheap settlements (Goodhart — which is the §7 floor again: *progression, not
# progress*; the observable reads the dance, it must not choreograph it).

STUMBLE_DISPOSITIONS = ("challenge_to_M", "retract_fact")


@dataclass
class Stumble:
    """One fresh irritation on the trace: a relinquishment the game performed, a DAG branch,
    or a sharp disagreement (≥2 distinct dispositions beyond the winner). ``recovery`` is the
    number of rounds until a poised window resumes — ``None`` if the trace ends first (the
    frontier, not a fall)."""
    round_idx: int
    kind: str                       # relinquishment | branch | disagreement
    recovery: Optional[int] = None


@dataclass
class PoiseWindow:
    """One window's reading. ``failure`` names the pole a non-poised window fails toward —
    ``rigidity`` (no engagement) or ``thrash`` (engagement without settlement)."""
    start_round: int
    end_round: int
    engagement: float               # revising rounds / rounds
    thrash_situations: int          # situations disposed inconsistently within the window
    stumbles: int
    poised: bool
    failure: Optional[str]          # rigidity | thrash | None


@dataclass
class PoiseReport:
    """The trajectory read as a dynamics: per-window readings, the stumble events with their
    recoveries, and the aggregate. ``poised_fraction`` is comparative (across a run's phases or
    an ablation's arms), not an absolute score."""
    windows: List[PoiseWindow]
    stumbles: List[Stumble]
    poised_fraction: float
    mean_recovery: Optional[float]  # over recovered stumbles; None if none recovered
    unrecovered: int                # stumbles the trace ended on (the frontier)


def _window_reading(eps: Sequence[EpisodeRecord], *, max_stumbles: int) -> PoiseWindow:
    revising = [e for e in eps if e.disposition is not None]
    engagement = len(revising) / len(eps) if eps else 0.0
    thrash = sum(1 for p in resolution_principles(eps) if p.thrash)
    stumbles = sum(1 for e in eps if _stumble_kind(e))
    if engagement == 0.0:
        poised, failure = False, "rigidity"
    elif thrash > 0 or stumbles > max_stumbles:
        poised, failure = False, "thrash"
    else:
        poised, failure = True, None
    return PoiseWindow(
        start_round=eps[0].round_idx, end_round=eps[-1].round_idx,
        engagement=engagement, thrash_situations=thrash, stumbles=stumbles,
        poised=poised, failure=failure,
    )


def _stumble_kind(e: EpisodeRecord) -> Optional[str]:
    if e.disposition in STUMBLE_DISPOSITIONS:
        return "relinquishment"
    if e.branched:
        return "branch"
    if e.disagreement >= 2:
        return "disagreement"
    return None


def poise_report(episodes: Sequence[EpisodeRecord], *, window: int = 8,
                 max_stumbles: int = 1) -> PoiseReport:
    """Read the observable shadow of poise off a run's episodes: tumbling windows of ``window``
    rounds, each read for engagement / settlement / absorption; stumbles located and their
    recovery measured (rounds until the next poised *sliding* window begins). The thresholds
    (``window``, ``max_stumbles``) belong to the observer — the reading is perspectival and
    comparative, never absolute. See the section comment: an instrument, not a target."""
    eps = list(episodes)
    if not eps:
        return PoiseReport([], [], 0.0, None, 0)

    windows = [
        _window_reading(eps[i:i + window], max_stumbles=max_stumbles)
        for i in range(0, len(eps), window)
    ]

    stumbles: List[Stumble] = []
    for i, e in enumerate(eps):
        kind = _stumble_kind(e)
        if kind is None:
            continue
        recovery: Optional[int] = None
        for j in range(i + 1, len(eps) - window + 1):    # first poised sliding window after it
            w = _window_reading(eps[j:j + window], max_stumbles=max_stumbles)
            if w.poised:
                recovery = eps[j].round_idx - e.round_idx
                break
        stumbles.append(Stumble(e.round_idx, kind, recovery))

    recovered = [s.recovery for s in stumbles if s.recovery is not None]
    return PoiseReport(
        windows=windows,
        stumbles=stumbles,
        poised_fraction=sum(1 for w in windows if w.poised) / len(windows),
        mean_recovery=(sum(recovered) / len(recovered)) if recovered else None,
        unrecovered=sum(1 for s in stumbles if s.recovery is None),
    )


def poise_from_digests(segments: Sequence, *, max_stumbles: int = 1) -> List[PoiseWindow]:
    """The live monitoring surface: one coarse poise reading per ``SegmentDigest`` (a segment
    is the natural window of a live run). Engagement = revising rounds / rounds; stumbles =
    relinquishing dispositions + branches; thrash is not computable from a digest (no
    per-situation record), so a segment fails toward thrash only on cascading stumbles. Watch
    the stream: poised segments with stumbles arriving *and* being absorbed is the shape of
    competence; a wall of rigidity or of thrash is a run to intervene on."""
    out: List[PoiseWindow] = []
    for d in segments:
        revising = sum(d.dispositions.values())
        engagement = revising / d.rounds if d.rounds else 0.0
        stumbles = sum(d.dispositions.get(k, 0) for k in STUMBLE_DISPOSITIONS) + d.branched
        if engagement == 0.0:
            poised, failure = False, "rigidity"
        elif stumbles > max_stumbles:
            poised, failure = False, "thrash"
        else:
            poised, failure = True, None
        out.append(PoiseWindow(
            start_round=d.total_rounds - d.rounds + 1, end_round=d.total_rounds,
            engagement=engagement, thrash_situations=0, stumbles=stumbles,
            poised=poised, failure=failure,
        ))
    return out


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
    ``disposition``, and whether that move *stuck* in the final M. A move whose content later
    fell to disuse-decay reads ``stuck=None`` + ``erased_by_decay=True`` — excluded from
    stick-rates (no durability evidence), never counted as relinquished."""
    claim_egif: str
    mechanism: str
    settled: Optional[bool]
    reverts: int
    disposition: Optional[str]
    stuck: Optional[bool]
    erased_by_decay: bool = False


@dataclass
class MechanismPrinciple:
    """What a *resolution mechanism* empirically buys: how often its resolutions took hold. A
    mechanism whose resolutions all stick (``stick_rate == 1.0``) is ``durable`` — the learned
    finding that (say) reliable-source citations produce lasting knowledge where consensus, when
    overturned, does not. ``decay_erased`` counts the episodes whose content merely fell from
    use — reported, not silently dropped, but carrying no durability evidence either way."""
    mechanism: str
    count: int
    dominant_disposition: Optional[str]
    stick_rate: Optional[float]
    durable: bool
    decay_erased: int = 0


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
            decay_erased=sum(1 for e in recs if e.erased_by_decay),
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
    "EpisodeRecord", "episodes_from", "is_stuck", "stickiness",
    "mark_decayed", "mark_decayed_atoms", "mark_relinquished",
    "Principle", "resolution_principles",
    "FrictionPoint", "friction_map", "gaps",
    "StabilityReport", "stability_report",
    "Stumble", "PoiseWindow", "PoiseReport", "poise_report", "poise_from_digests",
    "STUMBLE_DISPOSITIONS",
    "AblationVariant", "AblationResult", "run_ablation",
    "DisputeEpisode", "MechanismPrinciple", "mechanism_principles",
    "edit_war_friction", "unresolved_frontier",
]
