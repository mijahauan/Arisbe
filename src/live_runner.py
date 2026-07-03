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

  * **bound \\|M\\| with disuse-decay** (``ttl``) — an **atom** idle for ``ttl`` rounds is erased
    (atom-level since 2026-07-03: the habit is the fact, not the name — use = re-delivery, so a
    warm hub name no longer pins an unbounded atom pile, RUN_3 F1″/RUN_4 F2⁗), keeping \\|M\\| —
    and thus per-round cost, per-state disk, and segment memory — roughly constant;
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
from agon_evolution import (
    EvolutionResult, Proposer, UsageLedger, run,
    delivered_atom_keys, parse_atom_key, sheet_atom_keys,
)
from model_materialization import IncrementalMaterializer
from model_revision import retract_atom


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
    max_m_atoms: Optional[int] = None         # hard cap in ATOM units — under tropism, decay bounds
                                              # names, not atoms (RUN_3 F1″): hub names accumulate
                                              # atoms unboundedly while m_relations reads flat
    stop_file: Optional[str] = None           # stop cleanly when this path exists (external control)
    checkpoint: bool = True                   # save a UoD+chain per segment (needs a service)
    state_path: Optional[str] = None          # persist runner state per segment → LiveRunner.resume


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
    m_atoms: int = 0                          # sheet ATOMS after the segment — the honest unit
                                              # (RUN_3 F1″: names stay flat while atoms grow; attest
                                              # wall-clock tracks atoms × hub degree, not names)


@dataclass
class LiveResult:
    """``episodes`` is the cross-segment accumulation of the feed's meta-learning records
    (when the membrane supports ``.episodes``), with runner-level disuse-decay already
    retro-marked (``agon_metalearning.mark_decayed``) — the honest long-run input to
    ``mechanism_principles`` and friends. Per-segment ``extra`` payloads are computed *before*
    that segment's decay; this list is the decay-aware aggregate."""
    segments: List[SegmentDigest]
    total_rounds: int
    final_model_egif: str
    stopped_because: str
    episodes: List = field(default_factory=list)


# --------------------------------------------------------------------------- #
# The runner                                                                  #
# --------------------------------------------------------------------------- #

def _sheet_relations(egi) -> set:
    return {egi.rel[e.id] for e in egi.E
            if area_of(egi, e.id) == egi.sheet and e.id in egi.rel}


def _sheet_relation_count(egi) -> int:
    return len(_sheet_relations(egi))


def _sheet_atom_count(egi) -> int:
    """Atoms (relation edges) on the sheet — the F1″ unit. Distinct from
    :func:`_sheet_relation_count`: one warm hub *name* can hold dozens of atoms."""
    return sum(1 for e in egi.E
               if area_of(egi, e.id) == egi.sheet and e.id in egi.rel)


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
        panel=None,                            # an Agonothetes panel (default: the mechanical one)
        evaluate: Optional[Callable[[Proposer, EvolutionResult], Dict]] = None,
        service=None,                          # a TomosService for checkpoints (or None to skip)
        tropism=None,                          # a WarmSetTropism (§13) — consulted at each poll boundary
        clock: Callable[[], float] = None,
        sleep: Callable[[float], None] = None,
    ):
        self._model_egif = model_egif
        self._source = source
        self._feed_factory = feed_factory
        self._cfg = config or LiveRunConfig()
        self._uod_id = uod_id
        self._laws: List[str] = list(seed_laws or [])
        self._panel = panel
        self._evaluate = evaluate
        self._service = service
        # Tropism (§13): a player-side policy emitting warm re-reaches. The runner stays thin —
        # one consult per poll boundary — and the source carries the one seam it needs.
        if tropism is not None and not hasattr(source, "inject"):
            raise ValueError(
                "a tropism needs a source with an inject(ids) seam "
                f"({type(source).__name__} has none)")
        self._tropism = tropism
        if clock is None:
            import time
            clock = time.monotonic
        self._clock = clock
        self._sleep = sleep or (lambda _s: None)
        # Disuse-decay is a LONG-RUN concern, so it lives here (across global rounds), not inside
        # each per-segment run (whose ledger would reset every segment and never bound |M|).
        # ATOM-LEVEL (rulebook 2026-07-03): the ledger keys are atom keys, not relation names.
        self._ledger: Optional[UsageLedger] = UsageLedger(self._cfg.ttl) if self._cfg.ttl else None
        if self._ledger is not None:
            self._ledger.seed(delivered_atom_keys(model_egif) if model_egif else set())
        # One materializer for the whole run (F2⁗ semi-naive rider): each segment's peels
        # extend the previous closure instead of rebuilding M from scratch every round.
        # Public so a driver can report its counters (rebuilds ≈ decaying segments).
        self.materializer = IncrementalMaterializer()
        self._round = 0
        self._pending: List = []                # fetched items awaiting a segment (never dropped)
        self._polled = False
        self._episodes: List = []               # cross-segment meta-learning records
        self._seg0 = 0                          # segment/round offsets a resume restores
        self._total0 = 0

    @classmethod
    def resume(cls, state_path: str, source: LiveSource,
               feed_factory: Callable[[Sequence], Proposer],
               config: Optional[LiveRunConfig] = None, **kwargs) -> "LiveRunner":
        """Reconstruct a runner from the state file a previous run wrote (``state_path``) and
        continue where it stopped: M and its live laws are restored, segment/round numbering
        continues, and the disuse-decay ledger's clock **continues rather than resets** (a
        resumed run must not grant every relation a fresh ttl). A killed process therefore
        loses at most its in-flight segment — the crash/resume gap for an unattended run.
        The caller supplies a fresh ``source``; ``config.state_path`` defaults to the same
        path so the resumed run keeps checkpointing its state."""
        import json
        with open(state_path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        config = config or LiveRunConfig()
        if config.state_path is None:
            config.state_path = state_path
        runner = cls(state["model_egif"], source, feed_factory, config,
                     seed_laws=state.get("laws"), **kwargs)
        runner._round = state.get("round", 0)
        runner._seg0 = state.get("segment", 0)
        runner._total0 = state.get("total_rounds", 0)
        if runner._ledger is not None and state.get("ledger") is not None:
            runner._ledger.restore(state["ledger"])
        return runner

    def _save_state(self, seg_idx: int, total_rounds: int, model_egif: str) -> None:
        if not self._cfg.state_path:
            return
        import json
        import os
        state = {
            "version": 1,
            "segment": seg_idx,
            "round": self._round,
            "total_rounds": total_rounds,
            "model_egif": model_egif,
            "laws": list(self._laws),
            "ledger": self._ledger.snapshot() if self._ledger is not None else None,
        }
        tmp = f"{self._cfg.state_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
        os.replace(tmp, self._cfg.state_path)   # atomic: a crash never leaves a torn state

    def run(self) -> LiveResult:
        cfg = self._cfg
        start = self._clock()
        segments: List[SegmentDigest] = []
        total_rounds = self._total0
        model_egif = self._model_egif
        seg_idx = self._seg0

        while True:
            stop = self._should_stop(start, total_rounds, model_egif)
            if stop:
                return LiveResult(segments, total_rounds, model_egif, stop, self._episodes)

            # A batch larger than segment_cap is queued, not truncated — the remainder becomes
            # the next segment(s). Poll the source only when the queue is empty.
            if not self._pending:
                if self._polled and cfg.min_interval_s:
                    self._sleep(cfg.min_interval_s)   # pacing / rate limit between polls
                if self._tropism is not None:
                    # The warm-set re-poll (§13): the player's state directs the next reaches.
                    # Injected ids ride front-of-queue, so this poll's chunk = warm + fresh.
                    # Note an injection can revive an exhausted frontier — the configured stop
                    # conditions, not exhaustion, then end the run.
                    warm = self._tropism.reaches(model_egif, self._ledger)
                    if warm:
                        self._source.inject(warm)
                self._pending.extend(self._source.fetch())
                self._polled = True
                if not self._pending:
                    if self._source.exhausted():
                        return LiveResult(segments, total_rounds, model_egif,
                                          "source_exhausted", self._episodes)
                    continue                    # nothing new yet — poll again (paced above)

            items = self._pending[: cfg.segment_cap]  # bound the segment (checkpoint cadence)
            del self._pending[: len(items)]
            seg_idx += 1
            seg_start = self._clock()
            feed = self._feed_factory(items)
            # ttl=None here: decay is applied by the runner across global rounds (below), not
            # per-segment (which would reset every segment and never bound |M|).
            res = run(model_egif, feed, rounds=len(items),
                      uod_id=f"{self._uod_id}_seg{seg_idx}", name=f"{self._uod_id} segment {seg_idx}",
                      ttl=None, seed_laws=self._laws, panel=self._panel,
                      materializer=self.materializer)

            rounds_done = len(res.outcomes)
            total_rounds += rounds_done
            self._round += rounds_done
            dispositions = dict(Counter(o.disposition for o in res.outcomes if o.disposition))
            branched = sum(len(o.branched) for o in res.outcomes)
            # use = re-delivery (atom-level): every atom a proposal delivered this segment,
            # revising or not — a redundant warm re-delivery refreshes exactly its own atoms.
            used = set().union(*(delivered_atom_keys(o.proposal_egif) for o in res.outcomes)) \
                if res.outcomes else set()
            model_egif = generate_egif(res.uod.current_egi)   # carry M forward as EGIF
            laws_before, self._laws = self._laws, list(res.known_laws)
            extra = self._evaluate(feed, res) if self._evaluate else {}
            if hasattr(feed, "episodes"):       # accumulate the meta-learning records
                if self._episodes:
                    # a relinquishment in THIS segment of content admitted in an EARLIER one is
                    # durability evidence the earlier record must carry (stuck → False)
                    from agon_metalearning import mark_relinquished
                    mark_relinquished(self._episodes, res,
                                      [l for l in laws_before if l not in self._laws])
                self._episodes.extend(feed.episodes(res))
            checkpoint_uod = self._checkpoint(res, seg_idx)
            # PRUNE: drop the ProofChain so memory is bounded by one segment, not the whole run.
            del res, feed

            # Cross-segment disuse-decay: bound |M| (and thus per-round cost + disk) over the long
            # run. Atoms re-delivered this segment stay; those idle past ttl are erased from M
            # (atom-level — one warm atom no longer keeps its name-siblings alive).
            names_before = _relations_of(model_egif)
            model_egif, dropped = self._decay(model_egif, used)
            if dropped:
                names_gone = names_before - _relations_of(model_egif)
                if names_gone:
                    # a law only falls with its vocabulary — when a relation's last atom decays
                    self._laws = [l for l in self._laws if not (_relations_of(l) & names_gone)]
                if self._episodes:
                    # falling from the working set is not relinquishment — keep stick-rates honest
                    from agon_metalearning import mark_decayed_atoms
                    dropped_atoms = {(r, tuple(l)) for r, l in
                                     (parse_atom_key(k) for k in dropped)}
                    mark_decayed_atoms(self._episodes, dropped_atoms)

            carried = parse_egif(model_egif)
            segments.append(SegmentDigest(
                segment=seg_idx,
                rounds=rounds_done,
                total_rounds=total_rounds,
                m_relations=_sheet_relation_count(carried),
                m_atoms=_sheet_atom_count(carried),
                dispositions=dispositions,
                decayed=len(dropped),
                branched=branched,
                elapsed_s=self._clock() - seg_start,
                checkpoint_uod=checkpoint_uod,
                extra=extra,
            ))
            # persist the post-decay carried state — what LiveRunner.resume restores
            self._save_state(seg_idx, total_rounds, model_egif)

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
        if cfg.max_m_relations is not None or cfg.max_m_atoms is not None:
            from egif_parser_dau import parse_egif
            g = parse_egif(model_egif)
            if cfg.max_m_relations is not None and _sheet_relation_count(g) > cfg.max_m_relations:
                return "max_m_relations"
            if cfg.max_m_atoms is not None and _sheet_atom_count(g) > cfg.max_m_atoms:
                return "max_m_atoms"
        return None

    def _decay(self, model_egif: str, used: set) -> tuple:
        """Erase **atoms** idle past ``ttl`` global rounds — the only bound on the unbounded
        sheet, applied across segments so |M| (and per-round cost, memory, disk) stays flat.
        Atom-level (the rulebook decision, 2026-07-03): the ledger and the erasure both work
        in :func:`agon_evolution.atom_key` units, retracting via ``retract_atom`` so other
        atoms of the same name — and any standing law cut — survive. Returns
        ``(new_model_egif, dropped_atom_keys)``."""
        if self._ledger is None:
            return model_egif, set()
        g = parse_egif(model_egif)
        present = sheet_atom_keys(g)
        self._ledger.seed(present, self._round)          # register any newcomers
        self._ledger.touch(used & present, self._round)  # mark this segment's re-deliveries
        dropped = set()
        for key in self._ledger.stale(self._round):
            if key in present:
                rel, labels = parse_atom_key(key)
                g = retract_atom(g, rel, labels)
                dropped.add(key)
            self._ledger.forget(key)
        if dropped:
            model_egif = generate_egif(g)
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
