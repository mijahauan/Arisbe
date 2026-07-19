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
from typing import Callable, Dict, List, Optional, Protocol, Sequence, Set

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from egi_io import from_dict, to_dict
from eg_navigation import area_of
from agon_evolution import (
    EvolutionResult, Proposer, UsageLedger, run,
    delivered_atom_keys, parse_atom_key, sheet_atom_keys,
)
from model_materialization import IncrementalMaterializer
from model_revision import retract_atom
from world_scroll import enlarge_m, find_world_scroll, m_view, retract_from_m


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
    ttl_unit: str = "rounds"                  # "rounds" | "polls" — the habit clock's denomination.
                                              # RUN_5 F2⁵: rounds became ~free (17.8/s), so a
                                              # rounds-denominated ttl collapsed to a ~2 s memory
                                              # and no atom survived a poll gap; "polls" ties the
                                              # clock to engagement opportunities, so ttl=N means
                                              # "idle N polls", throughput-invariant. A state file
                                              # written under one unit is not resumable under the
                                              # other (the ledger's clock values change meaning).
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
    checkpoint_every: int = 1                 # checkpoint every Nth segment (RUN_5 F2ᵇ: at the
                                              # persistent-M steady state the checkpoint's
                                              # layout+attest dominates segment cost and collapses
                                              # the poll rate — cadence ≠ coverage: digests, the
                                              # meta-learning episodes, and the resumable state
                                              # file remain PER-SEGMENT; only the browsable UoD
                                              # record thins. 1 = every segment (the old behavior).
    checkpoint_refusal: str = "raise"         # "raise" | "skip" — what a §3.3 refusal at the
                                              # checkpoint save does. "raise" is the corpus-boundary
                                              # contract; "skip" is the unattended posture (RUN_5
                                              # F1⁵: the attest is a content-dependent coin flip —
                                              # long machine-scale labels — and one unlucky roll
                                              # must not end a 14 h run): the refused segment's M
                                              # is QUARANTINED beside the state file, the refusal
                                              # COUNTED (``checkpoints_refused``), and the run
                                              # continues — never a silent skip, never an
                                              # unattested write.
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
    decay_skipped: int = 0                    # decays the licensed ERA refused — the atom stands
                                              # and the refusal is counted, never unlicensed surgery
    linear_form_skipped: int = 0              # tropism/docket/reseed consults skipped THIS segment
                                              # because M has no linear form (a quotation-bearing
                                              # cell) — mirrors decay_skipped's carry so the docket's
                                              # whole settle/age/harvest tick going dark (not merely
                                              # steering going unguided, see _linear_form) shows up
                                              # here rather than needing a runner-attribute read.
                                              # One narrow tail case is NOT attributable here: a poll
                                              # that both skips the linear form and finds the source
                                              # exhausted ends the run before any further segment
                                              # forms to carry it, so it counts only on the runner's
                                              # ``linear_form_skipped`` total. That total is
                                              # therefore the authority; the per-segment sum can be
                                              # a strict undercount by that tail (a ReplaySource-only
                                              # edge — a genuinely live source never exhausts).


@dataclass
class LiveResult:
    """``episodes`` is the cross-segment accumulation of the feed's meta-learning records
    (when the membrane supports ``.episodes``), with runner-level disuse-decay already
    retro-marked (``agon_metalearning.mark_decayed``) — the honest long-run input to
    ``mechanism_principles`` and friends. Per-segment ``extra`` payloads are computed *before*
    that segment's decay; this list is the decay-aware aggregate.

    ``final_model_json`` is M itself (the structural carry); ``final_model_egif``
    is its linear reading, which a second-order M has none of — asking for it
    then raises ``SecondOrderNotInLinearForm``, the named limit."""
    segments: List[SegmentDigest]
    total_rounds: int
    final_model_json: Dict
    stopped_because: str
    episodes: List = field(default_factory=list)

    @property
    def final_model_egif(self) -> str:
        return generate_egif(from_dict(self.final_model_json))


# --------------------------------------------------------------------------- #
# The runner                                                                  #
# --------------------------------------------------------------------------- #

def _sheet_relations(egi) -> set:
    """M's standing relation names — read through ``m_view``, so the counters
    keep meaning "M's content" now that M is resident in the standing
    world-scroll (sweep #2); identity on a bare sheet-level graph."""
    egi = m_view(egi)
    return {egi.rel[e.id] for e in egi.E
            if area_of(egi, e.id) == egi.sheet and e.id in egi.rel}


def _sheet_relation_count(egi) -> int:
    return len(_sheet_relations(egi))


def _sheet_atom_count(egi) -> int:
    """Atoms (relation edges) standing in M — the F1″ unit, read through
    ``m_view``. Distinct from :func:`_sheet_relation_count`: one warm hub
    *name* can hold dozens of atoms."""
    egi = m_view(egi)
    return sum(1 for e in egi.E
               if area_of(egi, e.id) == egi.sheet and e.id in egi.rel)


def _relations_of(egif: str) -> set:
    return _relations_of_egi(parse_egif(egif))


def _relations_of_egi(g) -> set:
    return {g.rel[e.id] for e in g.E if e.id in g.rel}


def _as_model_state(model) -> Dict:
    """M as the structural carry: a graph, its ``egi_io`` dict, or EGIF text.
    Text is accepted for the constructor's callers and legacy checkpoints only —
    it is parsed once here and never re-serialized on the carry path."""
    if isinstance(model, dict):
        return model
    if isinstance(model, str):
        return to_dict(parse_egif(model))
    return to_dict(model)


class LiveRunner:
    """The outer loop: poll a :class:`LiveSource`, run a bounded, decayed segment per non-empty
    batch, checkpoint + prune, pace, and stop on any configured condition. Deterministic given a
    deterministic source, ``clock`` and ``sleep``."""

    def __init__(
        self,
        model,                                 # M as EGIF text, an egi_io dict, or a graph
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
        docket=None,                           # a QueryDocket (§15 · 2a) — the articulate stratum
        clock: Callable[[], float] = None,
        sleep: Callable[[float], None] = None,
    ):
        self._model_state = _as_model_state(model)
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
        # The docket (§15 increment 2a): the player's register of named wants,
        # consulted at the same poll boundary the tropism uses — the two compose
        # (warm re-reach = the cheapest stratum; docket asks = the articulate one).
        if docket is not None and not hasattr(source, "inject"):
            raise ValueError(
                "a docket needs a source with an inject(ids) seam "
                f"({type(source).__name__} has none)")
        self._docket = docket
        if clock is None:
            import time
            clock = time.monotonic
        self._clock = clock
        self._sleep = sleep or (lambda _s: None)
        # Disuse-decay is a LONG-RUN concern, so it lives here (across global rounds), not inside
        # each per-segment run (whose ledger would reset every segment and never bound |M|).
        # ATOM-LEVEL (rulebook 2026-07-03): the ledger keys are atom keys, not relation names.
        self._ledger: Optional[UsageLedger] = UsageLedger(self._cfg.ttl) if self._cfg.ttl else None
        # Atoms whose licensed retraction the rule refused: held aside so the decay pass
        # neither re-registers nor re-refuses them (see _decay) — decay_skipped counts
        # atoms, not events.
        self._decay_refused: Set[str] = set()
        if self._ledger is not None:
            self._ledger.seed(sheet_atom_keys(from_dict(self._model_state)))
        # One materializer for the whole run (F2⁗ semi-naive rider): each segment's peels
        # extend the previous closure instead of rebuilding M from scratch every round.
        # Public so a driver can report its counters (rebuilds ≈ decaying segments).
        self.materializer = IncrementalMaterializer()
        self._round = 0
        self._poll_idx = 0                      # polls made — the habit clock when ttl_unit="polls"
        self.checkpoints_refused = 0            # §3.3 refusals skipped (checkpoint_refusal="skip")
        self.linear_form_skipped = 0            # tropism/docket/reseed consults skipped: M has no
                                                 # linear form — the run-total; ``_lfs_pending``
                                                 # below is the same count since the last segment
                                                 # digest was built, so it can be attributed there
        self._lfs_pending = 0
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
        path so the resumed run keeps checkpointing its state.

        Residence note (sweep #2): a state file written by a pre-relocation run
        carries M as *flat* sheet-level EGIF — ``agon_evolution.run``'s
        ensure-residence houses it in the standing world-scroll on the first
        resumed segment (two recorded rule steps). The ledger/docket are keyed
        by content (``atom_key``), so they survive the re-housing unchanged.

        A pre-④ state file carries M as ``model_egif`` text instead of
        ``model_json``; it is parsed once here and carried structurally from
        then on. That one parse is where the text round-trip's constant-merge
        can still bite, so such a run may see a decay skipped and counted."""
        import json
        with open(state_path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        config = config or LiveRunConfig()
        if config.state_path is None:
            config.state_path = state_path
        model = state.get("model_json")
        if model is None:
            model = state["model_egif"]              # legacy checkpoint
        runner = cls(model, source, feed_factory, config,
                     seed_laws=state.get("laws"), **kwargs)
        runner._round = state.get("round", 0)
        runner._poll_idx = state.get("poll", 0)
        runner._seg0 = state.get("segment", 0)
        runner._total0 = state.get("total_rounds", 0)
        if runner._ledger is not None and state.get("ledger") is not None:
            runner._ledger.restore(state["ledger"])
        runner._decay_refused = set(state.get("decay_refused") or ())
        if runner._docket is not None and state.get("docket") is not None:
            runner._docket.restore(state["docket"])
        return runner

    def _save_state(self, seg_idx: int, total_rounds: int, model_state: Dict) -> None:
        if not self._cfg.state_path:
            return
        import json
        import os
        state = {
            "version": 2,               # 2: M as structural JSON, not EGIF text
            "segment": seg_idx,
            "round": self._round,
            "poll": self._poll_idx,
            "total_rounds": total_rounds,
            "model_json": model_state,
            "laws": list(self._laws),
            "ledger": self._ledger.snapshot() if self._ledger is not None else None,
            # the held-aside refusals ride along, so a resumed run does not re-refuse
            # (and re-count) an atom this run already skipped
            "decay_refused": sorted(self._decay_refused),
            # 2a.1 (RUN_6 F1⁶): the docket register survives a resume like the ledger —
            # a supervisor leg must not restart the wants (or the whole-run counters).
            "docket": self._docket.snapshot() if self._docket is not None else None,
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
        # M is carried between segments STRUCTURALLY (docket ④): EGIF cannot
        # express per-cell vertex privacy or the second-order sort, so a text
        # carry merges a constant shared across sibling cells (which defeats
        # the licensed cell-scoped ERA) and cannot represent a quotation at all.
        model = from_dict(self._model_state)
        seg_idx = self._seg0

        while True:
            stop = self._should_stop(start, total_rounds, model)
            if stop:
                return LiveResult(segments, total_rounds, to_dict(model),
                                  stop, self._episodes)

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
                    # the tropism/docket strata read M as EGIF; generate only
                    # when one is configured (a second-order M has no linear form)
                    m_egif = self._linear_form(model)
                    warm = self._tropism.reaches(m_egif, self._ledger) \
                        if m_egif is not None else []
                    if warm:
                        self._source.inject(warm)
                if self._docket is not None:
                    # The docket's Q1 asks (§15 · 2a): what M *lacks* directs a reach too —
                    # articulated doubt riding the same seam, beside the warm stratum.
                    # The upcoming poll's index rides into the ask journal (2a.1).
                    asks = self._docket.reaches(poll=self._poll_idx + 1)
                    if asks:
                        self._source.inject(asks)
                self._pending.extend(self._source.fetch())
                self._polled = True
                self._poll_idx += 1             # a poll = one engagement opportunity (ttl_unit="polls")
                if not self._pending:
                    if self._source.exhausted():
                        return LiveResult(segments, total_rounds, to_dict(model),
                                          "source_exhausted", self._episodes)
                    continue                    # nothing new yet — poll again (paced above)

            items = self._pending[: cfg.segment_cap]  # bound the segment (checkpoint cadence)
            del self._pending[: len(items)]
            seg_idx += 1
            seg_start = self._clock()
            feed = self._feed_factory(items)
            # ttl=None here: decay is applied by the runner across global rounds (below), not
            # per-segment (which would reset every segment and never bound |M|).
            res = run(model, feed, rounds=len(items),
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
            model = res.uod.current_egi                       # carry M forward structurally
            laws_before, self._laws = self._laws, list(res.known_laws)
            extra = self._evaluate(feed, res) if self._evaluate else {}
            # Re-generalization hook (generic): an evaluate() may return
            # ``reseed_laws`` — laws to re-scribe onto M after a relinquishment
            # (e.g. the weather recalibrator returning a fallen law under a wider,
            # better-calibrated discretization, docs/AUTOMATED_ENDOPOREUTIC_GAME.md
            # §19). Re-supply each law into the carried M + registry so the next
            # segment materializes it and bets again — predict→refute→
            # re-generalize, not predict→refute→silence. NOTE: the carried M is
            # resident in the standing world-scroll (sweep #2), so the re-supply
            # must be an INS-of-cell (``enlarge_m``) — a bare string juxtaposition
            # would put a second cut at sheet level and silently defeat
            # recognition (m_view identity → counters and oracle reading chrome).
            reseeds = (extra or {}).get("reseed_laws", []) or []
            for _law in reseeds:
                if find_world_scroll(model) is not None:
                    model = enlarge_m(model, _law)
                else:                          # legacy sheet-level carry
                    m_egif = self._linear_form(model)
                    if m_egif is None:
                        # can't linearize this non-resident M (guarded like the
                        # tropism/docket seams — see _linear_form): this one
                        # reseed attempt is skipped and counted rather than
                        # crashing on an unguarded generate_egif. ``_law`` is
                        # left off ``self._laws``, so it is not falsely marked
                        # re-supplied; whether it is retried depends on the
                        # evaluate hook proposing it again in a later segment.
                        continue
                    model = parse_egif(f"{m_egif} {_law}".strip())
                if _law not in self._laws:
                    self._laws.append(_law)
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
            names_before = _relations_of_egi(model)
            model, dropped, skipped = self._decay(model, used)
            if dropped:
                names_gone = names_before - _relations_of_egi(model)
                if names_gone:
                    # a law only falls with its vocabulary — when a relation's last atom decays
                    self._laws = [l for l in self._laws if not (_relations_of(l) & names_gone)]
                if self._episodes:
                    # falling from the working set is not relinquishment — keep stick-rates honest
                    from agon_metalearning import mark_decayed_atoms
                    dropped_atoms = {(r, tuple(l)) for r, l in
                                     (parse_atom_key(k) for k in dropped)}
                    mark_decayed_atoms(self._episodes, dropped_atoms)

            if self._docket is not None:
                # One docket tick per segment against the carried (post-decay) M:
                # settle answered wants, age the rest, harvest fresh thin spots.
                # Skipped (and counted via _linear_form) once M carries a
                # quotation — that loses the WHOLE tick, not just steering
                # (settling/aging/harvesting all stop while ``reaches`` keeps
                # re-injecting the same already-open asks); see _linear_form's
                # docstring for the full consequence and why it differs from
                # the tropism's degradation.
                m_egif = self._linear_form(model)
                if m_egif is not None:
                    self._docket.observe(m_egif)

            segments.append(SegmentDigest(
                segment=seg_idx,
                rounds=rounds_done,
                total_rounds=total_rounds,
                m_relations=_sheet_relation_count(model),
                m_atoms=_sheet_atom_count(model),
                dispositions=dispositions,
                decayed=len(dropped),
                branched=branched,
                elapsed_s=self._clock() - seg_start,
                checkpoint_uod=checkpoint_uod,
                extra=extra,
                decay_skipped=len(skipped),
                linear_form_skipped=self._lfs_pending,
            ))
            self._lfs_pending = 0
            # persist the post-decay carried state — what LiveRunner.resume restores
            self._save_state(seg_idx, total_rounds, to_dict(model))

    # -- stop conditions -------------------------------------------------------
    def _should_stop(self, start: float, total_rounds: int, model) -> Optional[str]:
        cfg = self._cfg
        if cfg.max_rounds is not None and total_rounds >= cfg.max_rounds:
            return "max_rounds"
        if cfg.max_seconds is not None and (self._clock() - start) >= cfg.max_seconds:
            return "max_seconds"
        if cfg.stop_file:
            import os
            if os.path.exists(cfg.stop_file):
                return "stop_file"
        if cfg.max_m_relations is not None and \
                _sheet_relation_count(model) > cfg.max_m_relations:
            return "max_m_relations"
        if cfg.max_m_atoms is not None and _sheet_atom_count(model) > cfg.max_m_atoms:
            return "max_m_atoms"
        return None

    def _linear_form(self, g) -> Optional[str]:
        """M as EGIF for the three seams whose published contract is a string —
        the tropism's warm re-reach, the docket's settle/age/harvest tick
        (``QueryDocket.observe``), and the legacy sheet-level reseed branch
        below — or ``None`` when M has no linear form.

        Once V2a.2 banks a quoted attributed cell, M carries a quotation and the
        three linear generators raise the named limit
        (``SecondOrderNotInLinearForm``). Following ``_quarantine``'s precedent
        the limit is **honoured, not hidden**: the calling stratum's use of M
        for that poll/segment is skipped rather than crashing, and the skip is
        counted on ``self.linear_form_skipped`` (the run total) *and*
        ``SegmentDigest.linear_form_skipped`` (the per-segment carry the
        driver prints), so a run losing a stratum shows up in the digest
        rather than only in an attribute nobody reads.

        The three call sites do **not** degrade equally — that is the point of
        naming them here rather than in one shared inline comment:

        * the **tropism** loses only *direction*: M still develops from the
          fresh/random stream, just without this poll's warm steering;
        * the **docket** loses its *whole tick*: ``observe`` is what settles
          answered wants, ages the rest, and harvests fresh thin spots.
          Skipping it freezes the entry set — ``resolved`` stops
          incrementing, nothing ages out — while ``reaches`` is still called
          every poll and keeps re-injecting the same already-open asks.
          Nothing in this loop ever removes a quotation from M once V2a.2
          banks one, so the FIRST banked quotation freezes the docket for the
          rest of the run, not for one poll;
        * the **legacy reseed branch** loses that one law's re-supply for this
          round; the law is left off ``self._laws`` (not falsely marked
          re-applied), so a later segment can still pick it up if the
          ``evaluate`` hook proposes it again.
        """
        from second_order_limits import SecondOrderNotInLinearForm
        try:
            return generate_egif(g)
        except SecondOrderNotInLinearForm:
            self.linear_form_skipped += 1
            self._lfs_pending += 1
            return None

    def _decay(self, g, used: set) -> tuple:
        """Erase **atoms** idle past ``ttl`` global rounds — the only bound on the unbounded
        sheet, applied across segments so |M| (and per-round cost, memory, disk) stays flat.
        Atom-level (the rulebook decision, 2026-07-03): the ledger and the erasure both work
        in :func:`agon_evolution.atom_key` units. Under the residence (sweep #2) the
        erasure is the licensed ERA-in-cell (``retract_from_m``) — the *faded* tense,
        the same move as refutation, D6's ``pruned:disuse`` economy — falling back to
        the sheet-scoped ``retract_atom`` on a legacy sheet-level carry; either way other
        atoms of the same name and any standing law cut survive.

        A retraction the licensed rule refuses is **skipped and counted**, never
        performed unlicensed: no Dau rule permits erasing M's ink by hand, and
        erasing by relation + labels alone would reach into denial cells and
        episode exhibits. This refusal is not confined to a legacy EGIF
        checkpoint: the same cross-cell-constant-merge condition arises the
        moment :func:`agon_evolution.run` houses a *non-resident* seed via its
        own ``generate_egif``-round-trip ensure-residence step (that
        function's docstring names the identical merge) — i.e. it can also
        happen on the very first segment of a run started from a plain
        sheet-level M, not only on a resumed legacy state file.

        The refused atom is then held aside (``_decay_refused``): dropped from
        the ledger *and* withheld from the newcomer seeding, so it is never
        re-registered, never goes stale again, and is never refused a second
        time — hence ``decay_skipped`` counts refused **atoms**, not refusal
        events. The exemption is content-keyed (``atom_key`` = relation +
        labels, not element identity), so it must not outlive the atom it was
        granted to: at the top of every call, ``_decay_refused`` is **pruned**
        to the keys still standing in M. If a refused atom is later
        legitimately retracted by some other path and the same fact is
        re-admitted afterward, that re-admission is a fresh atom — the prune
        has already dropped the stale key, so decay applies to the new atom
        normally rather than inheriting the old exemption. The set is
        checkpointed, so a resume does not recount.
        Returns ``(new_graph, dropped_atom_keys, skipped)``."""
        if self._ledger is None:
            return g, set(), []
        # The habit clock: global rounds, or polls (RUN_5 F2⁵ — once rounds are ~free, "idle N
        # rounds" is a ~2 s memory; "idle N polls" counts engagement opportunities instead).
        now = self._poll_idx if self._cfg.ttl_unit == "polls" else self._round
        all_present = sheet_atom_keys(g)
        self._decay_refused &= all_present        # MINOR 3: the exemption must not outlive the atom
        present = all_present - self._decay_refused
        self._ledger.seed(present, now)          # register any newcomers
        self._ledger.touch(used & present, now)  # mark this segment's re-deliveries
        dropped = set()
        skipped: List[tuple] = []
        for key in self._ledger.stale(now):
            if key in present:
                rel, labels = parse_atom_key(key)
                try:
                    if find_world_scroll(g) is not None:
                        g = retract_from_m(g, relation=rel, labels=labels)[0]
                    else:
                        g = retract_atom(g, rel, labels)
                except (AssertionError, ValueError) as exc:
                    skipped.append((key, str(exc)))
                    self._decay_refused.add(key)  # held aside: never re-seeded, so never re-counted
                    self._ledger.forget(key)
                    continue                     # the atom stands; the skip is counted
                dropped.add(key)
            self._ledger.forget(key)
        return g, dropped, skipped

    def _checkpoint(self, res: EvolutionResult, seg_idx: int) -> Optional[str]:
        if not (self._cfg.checkpoint and self._service is not None):
            return None
        if self._cfg.checkpoint_every > 1 and seg_idx % self._cfg.checkpoint_every != 0:
            return None                     # cadence, not coverage (see LiveRunConfig)
        try:
            self._service.save_uod_with_chain(res.uod, res.chain)   # §3.3 attests before any write
        except Exception as exc:
            # RUN_5 F1⁵: the attest at machine-scale content is a content-dependent coin flip
            # (long-label occlusion, UUID tie-breaks) — under "skip", a refusal is counted and
            # the refused M quarantined (EGIF + error beside the state file: auditable, never
            # silently dropped, never written unattested), and the run continues. "raise"
            # keeps the corpus-boundary contract for attended runs.
            from correspondence_attestation import CorrespondenceViolation
            if self._cfg.checkpoint_refusal != "skip" or not isinstance(
                    exc, CorrespondenceViolation):
                raise
            self.checkpoints_refused += 1
            self._quarantine(res, seg_idx, exc)
            return None
        return res.uod.metadata.uod_id

    def _quarantine(self, res: EvolutionResult, seg_idx: int, exc: Exception) -> None:
        """Write the refused segment's M + the refusal text beside the state file — the
        honest record of a skipped checkpoint (RUN_5 F1⁵ disposal (b)). ``model_json``
        is the record; ``model_egif`` rides along for human legibility, and is null for
        an M that has no linear form."""
        if not self._cfg.state_path:
            return
        import json
        import os
        path = os.path.join(os.path.dirname(self._cfg.state_path) or ".",
                            f"refused_seg{seg_idx}.json")
        from second_order_limits import SecondOrderNotInLinearForm
        try:
            legible = generate_egif(res.uod.current_egi)
        except SecondOrderNotInLinearForm:
            legible = None
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"segment": seg_idx,
                       "uod_id": res.uod.metadata.uod_id,
                       "error": str(exc),
                       "model_egif": legible,
                       "model_json": to_dict(res.uod.current_egi)}, fh, indent=1)


__all__ = [
    "LiveSource", "ReplaySource", "LiveRunConfig",
    "SegmentDigest", "LiveResult", "LiveRunner",
]
