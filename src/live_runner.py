"""Running the automated Endoporeutic Game against a *live* source — with pacing,
checkpointing, and bounded resource use.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b (the open membranes) + a new
operational section. The membranes (``discourse_membrane`` / ``resolving_membrane`` /
``wiki_dispute_membrane``) are ``agon_evolution.Proposer``s over a *replayable* record; a **live**
source is one whose items arrive over wall-clock time and may never end. Running that safely needs
more than the round loop, because the loop was measured to be **super-linear in \\|M\\|**:

    accumulated \\|M\\|:   ~25 facts     ~100 facts    ~250 facts
    per mechanical round:  ~4 ms         ~73 ms        ~1.1 s

(the peel forward-chains M's Horn fragment each round, and ``ProofChain`` snapshots the *whole*
graph every round and holds *every* state in RAM). So an unbounded run against one growing M
degrades on rate, memory, and disk together. The two controls that keep it flat:

  * **bound \\|M\\| with disuse-decay** (``ttl``) — a relation idle for ``ttl`` rounds is erased, so
    \\|M\\| — and thus per-round cost, per-state disk, and segment memory — stay roughly constant;
  * **run in checkpointed segments that prune history** — each segment runs K rounds from the
    current M, saves a checkpoint (a UoD + chain), records an evaluation digest, then **drops the
    in-memory ProofChain** and carries only M (as EGIF) + its live laws forward. The full
    diachronic history is the *sequence of segment checkpoints*, not one ever-growing chain in RAM.

This module is that outer loop. It is membrane-agnostic (a ``feed_factory`` wraps a batch of
source items into any Proposer) and deterministic under test (the ``clock`` and ``sleep`` are
injectable, so pacing and duration stops are exercised with no real waiting). Additive,
geometry-free; §3.3 is attested where each checkpoint is *saved* (``TomosService.save_uod_with_chain``),
unchanged. Correspondence-not-truth holds: a live source is low-warrant input; nothing
auto-promotes to the attested corpus.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Protocol, Sequence

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from eg_navigation import area_of
from agon_evolution import EvolutionResult, Proposer, UsageLedger, run
from model_revision import retract_relation


# --------------------------------------------------------------------------- #
# The live source — a batch of items arriving over time                       #
# --------------------------------------------------------------------------- #

class LiveSource(Protocol):
    """A source of membrane items that arrive over wall-clock time. ``fetch`` returns the items
    available *now* (possibly empty — nothing new yet), and ``exhausted`` says whether the source
    will never yield again (a bounded replay ends; a truly live stream returns ``False`` forever).
    A real wiki/forum or prediction-market adapter implements this same shape; the runner does not
    care which."""

    def fetch(self) -> Sequence: ...
    def exhausted(self) -> bool: ...


class ReplaySource:
    """An offline live source: a fixed schedule of item-batches, one handed out per ``fetch``
    (a poll). Exhausts when the schedule runs out — so CI drives the whole runner deterministically
    with no network. A live adapter replaces this class alone."""

    def __init__(self, batches: Sequence[Sequence]):
        self._batches = [list(b) for b in batches]
        self._i = 0

    def fetch(self) -> Sequence:
        if self._i >= len(self._batches):
            return []
        batch = self._batches[self._i]
        self._i += 1
        return batch

    def exhausted(self) -> bool:
        return self._i >= len(self._batches)


# --------------------------------------------------------------------------- #
# Configuration — the operational knobs                                       #
# --------------------------------------------------------------------------- #

@dataclass
class LiveRunConfig:
    """The pacing / bounding / stopping knobs. Defaults are conservative for an indefinite run."""
    ttl: Optional[int] = 8                    # disuse-decay — REQUIRED to keep |M| (and cost) flat
    segment_cap: int = 25                     # max rounds per segment (a checkpoint cadence)
    min_interval_s: float = 0.0               # min wall-clock between polls (rate limit / pacing)
    max_rounds: Optional[int] = None          # stop after this many rounds total
    max_seconds: Optional[float] = None       # stop after this much wall-clock
    max_m_relations: Optional[int] = None     # hard cap: stop if |M| blows past this (a safety net)
    stop_file: Optional[str] = None           # stop cleanly when this path exists (external control)
    checkpoint: bool = True                   # save a UoD+chain per segment (needs a service)


# --------------------------------------------------------------------------- #
# Per-segment evaluation digest                                               #
# --------------------------------------------------------------------------- #

@dataclass
class SegmentDigest:
    """What happened in one segment — the evaluation surface. ``extra`` carries membrane-specific
    metrics from the optional ``evaluate`` hook (e.g. a ResolvingFeed's ledger accuracy, or a
    WikiDisputeFeed's mechanism principles)."""
    segment: int
    rounds: int
    total_rounds: int
    m_relations: int                          # |M| after the segment — watch this stay bounded
    dispositions: Dict[str, int]
    decayed: int
    branched: int
    elapsed_s: float
    checkpoint_uod: Optional[str]
    extra: Dict = field(default_factory=dict)


@dataclass
class LiveResult:
    segments: List[SegmentDigest]
    total_rounds: int
    final_model_egif: str
    stopped_because: str


# --------------------------------------------------------------------------- #
# The runner                                                                  #
# --------------------------------------------------------------------------- #

def _sheet_relations(egi) -> set:
    return {egi.rel[e.id] for e in egi.E
            if area_of(egi, e.id) == egi.sheet and e.id in egi.rel}


def _sheet_relation_count(egi) -> int:
    return len(_sheet_relations(egi))


def _relations_of(egif: str) -> set:
    g = parse_egif(egif)
    return {g.rel[e.id] for e in g.E if e.id in g.rel}


class LiveRunner:
    """The outer loop: poll a :class:`LiveSource`, run a bounded, decayed segment per non-empty
    batch, checkpoint + prune, pace, and stop on any configured condition. Deterministic given a
    deterministic source, ``clock`` and ``sleep``."""

    def __init__(
        self,
        model_egif: str,
        source: LiveSource,
        feed_factory: Callable[[Sequence], Proposer],
        config: Optional[LiveRunConfig] = None,
        *,
        uod_id: str = "live",
        seed_laws: Optional[Sequence[str]] = None,
        evaluate: Optional[Callable[[Proposer, EvolutionResult], Dict]] = None,
        service=None,                          # a TomosService for checkpoints (or None to skip)
        clock: Callable[[], float] = None,
        sleep: Callable[[float], None] = None,
    ):
        self._model_egif = model_egif
        self._source = source
        self._feed_factory = feed_factory
        self._cfg = config or LiveRunConfig()
        self._uod_id = uod_id
        self._laws: List[str] = list(seed_laws or [])
        self._evaluate = evaluate
        self._service = service
        if clock is None:
            import time
            clock = time.monotonic
        self._clock = clock
        self._sleep = sleep or (lambda _s: None)
        # Disuse-decay is a LONG-RUN concern, so it lives here (across global rounds), not inside
        # each per-segment run (whose ledger would reset every segment and never bound |M|).
        self._ledger: Optional[UsageLedger] = UsageLedger(self._cfg.ttl) if self._cfg.ttl else None
        if self._ledger is not None:
            self._ledger.seed(_relations_of(model_egif) if model_egif else set())
        self._round = 0

    def run(self) -> LiveResult:
        cfg = self._cfg
        start = self._clock()
        segments: List[SegmentDigest] = []
        total_rounds = 0
        model_egif = self._model_egif
        seg_idx = 0

        while True:
            stop = self._should_stop(start, total_rounds, model_egif)
            if stop:
                return LiveResult(segments, total_rounds, model_egif, stop)

            # pacing / rate limit: never poll faster than min_interval_s
            if segments and cfg.min_interval_s:
                self._sleep(cfg.min_interval_s)

            items = list(self._source.fetch())
            if not items:
                if self._source.exhausted():
                    return LiveResult(segments, total_rounds, model_egif, "source_exhausted")
                continue                        # nothing new yet — poll again (paced above)

            items = items[: cfg.segment_cap]     # bound the segment (checkpoint cadence)
            seg_idx += 1
            seg_start = self._clock()
            feed = self._feed_factory(items)
            # ttl=None here: decay is applied by the runner across global rounds (below), not
            # per-segment (which would reset every segment and never bound |M|).
            res = run(model_egif, feed, rounds=len(items),
                      uod_id=f"{self._uod_id}_seg{seg_idx}", name=f"{self._uod_id} segment {seg_idx}",
                      ttl=None, seed_laws=self._laws)

            rounds_done = len(res.outcomes)
            total_rounds += rounds_done
            self._round += rounds_done
            dispositions = dict(Counter(o.disposition for o in res.outcomes if o.disposition))
            branched = sum(len(o.branched) for o in res.outcomes)
            used = set().union(*(_relations_of(o.proposal_egif) for o in res.outcomes)) \
                if res.outcomes else set()
            model_egif = generate_egif(res.uod.current_egi)   # carry M forward as EGIF
            self._laws = list(res.known_laws)
            extra = self._evaluate(feed, res) if self._evaluate else {}
            checkpoint_uod = self._checkpoint(res, seg_idx)
            # PRUNE: drop the ProofChain so memory is bounded by one segment, not the whole run.
            del res, feed

            # Cross-segment disuse-decay: bound |M| (and thus per-round cost + disk) over the long
            # run. Relations used this segment stay; those idle past ttl are erased from M.
            model_egif, dropped = self._decay(model_egif, used)
            if dropped:
                self._laws = [l for l in self._laws if not (_relations_of(l) & dropped)]

            segments.append(SegmentDigest(
                segment=seg_idx,
                rounds=rounds_done,
                total_rounds=total_rounds,
                m_relations=_sheet_relation_count(parse_egif(model_egif)),
                dispositions=dispositions,
                decayed=len(dropped),
                branched=branched,
                elapsed_s=self._clock() - seg_start,
                checkpoint_uod=checkpoint_uod,
                extra=extra,
            ))

    # -- stop conditions -------------------------------------------------------
    def _should_stop(self, start: float, total_rounds: int, model_egif: str) -> Optional[str]:
        cfg = self._cfg
        if cfg.max_rounds is not None and total_rounds >= cfg.max_rounds:
            return "max_rounds"
        if cfg.max_seconds is not None and (self._clock() - start) >= cfg.max_seconds:
            return "max_seconds"
        if cfg.stop_file:
            import os
            if os.path.exists(cfg.stop_file):
                return "stop_file"
        if cfg.max_m_relations is not None:
            from egif_parser_dau import parse_egif
            if _sheet_relation_count(parse_egif(model_egif)) > cfg.max_m_relations:
                return "max_m_relations"
        return None

    def _decay(self, model_egif: str, used: set) -> tuple:
        """Erase relations idle past ``ttl`` global rounds — the only bound on the unbounded
        sheet, applied across segments so |M| (and per-round cost, memory, disk) stays flat.
        Returns ``(new_model_egif, dropped_relations)``."""
        if self._ledger is None:
            return model_egif, set()
        present = _relations_of(model_egif)
        self._ledger.seed(present, self._round)          # register any newcomers
        self._ledger.touch(used & present, self._round)  # mark this segment's use
        dropped = set()
        for rel in self._ledger.stale(self._round):
            if rel in present:
                model_egif = generate_egif(retract_relation(parse_egif(model_egif), rel))
                dropped.add(rel)
            self._ledger.forget(rel)
        return model_egif, dropped

    def _checkpoint(self, res: EvolutionResult, seg_idx: int) -> Optional[str]:
        if not (self._cfg.checkpoint and self._service is not None):
            return None
        self._service.save_uod_with_chain(res.uod, res.chain)   # §3.3 attests before any write
        return res.uod.metadata.uod_id


__all__ = [
    "LiveSource", "ReplaySource", "LiveRunConfig",
    "SegmentDigest", "LiveResult", "LiveRunner",
]
