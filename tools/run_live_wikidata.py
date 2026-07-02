"""Live Wikidata sessions against the automated Endoporeutic Game
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §10 operating layer + §11/§12 pre-registrations).

Two sources, chosen by --source:
  * frontier (run 1)      — the rotating entity crawl (seeds → crawled Q-ids)
  * recentchanges (run 2) — the change stream: poll which items were just edited and fetch
    those, so the sample skews to live contestation and an edited entity is *revisited*
    (a deprecation arrives while the bare value it overturns still stands in M — the
    RUN_1_LOG F2/F3 findings made operational)

Either source → WikiDisputeFeed → LiveRunner, with every §11 control armed:

  * checkpoints to a **side store** (``<runs-dir>/checkpoints`` — never the main corpus);
  * ``state.json`` + ``frontier.json`` so a killed process resumes with ``--resume``
    (the decay clock and the crawl both continue, not reset);
  * every poll **recorded** to ``polls.jsonl`` — the run replays offline afterward
    (``WikidataSource(replay_polls(...))``, the determinism canary);
  * pacing, ``--max-seconds``/``--max-rounds``, and a STOP file for a clean halt;
  * per-segment console digests (dispositions, |M|, decay, legibility, poise) and a final
    §6 summary (mechanism principles + the poise strip) for the run log.

Usage (supervised first hour per §11, then leave it running):

    uv run python tools/run_live_wikidata.py --seeds Q42 Q7259 Q937 --max-seconds 3600
    uv run python tools/run_live_wikidata.py --source recentchanges --runs-dir runs/run2 \
        --max-seconds 3600
    touch runs/run1/STOP                                  # clean stop
    uv run python tools/run_live_wikidata.py --resume     # continue after a kill/stop

Record findings in runs/RUN_<n>_LOG.md against the pre-registered priors.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import (
    Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent, ObserverAgent,
)
from live_runner import LiveRunConfig, LiveRunner
from tomos_service import TomosService
from wiki_dispute_membrane import WikiDisputeFeed
from wikidata_source import RecentChangesSource, RotatingWikidataSource

DEFAULT_SEEDS = ["Q42", "Q7259", "Q937"]   # Douglas Adams, Ada Lovelace, Albert Einstein


def _panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["frontier", "recentchanges"], default="frontier",
                    help="frontier = the rotating crawl (run 1); recentchanges = the change "
                         "stream (run 2 — live contestation + natural revisits)")
    ap.add_argument("--seeds", nargs="+", default=DEFAULT_SEEDS, metavar="QID",
                    help="frontier source only")
    ap.add_argument("--chunk", type=int, default=8, help="entity ids per poll")
    ap.add_argument("--frontier-cap", type=int, default=400)
    ap.add_argument("--per-entity-cap", type=int, default=25,
                    help="max statements taken per entity per poll — bounds M's hub degree, "
                         "which the checkpoint attest's ligature routing is super-linear in "
                         "(0 = uncapped; drops are counted, never silent)")
    ap.add_argument("--no-crawl", action="store_true",
                    help="poll only the seeds (no frontier growth)")
    ap.add_argument("--ttl", type=int, default=30, help="disuse-decay ttl (global rounds)")
    ap.add_argument("--segment-cap", type=int, default=25)
    ap.add_argument("--min-interval", type=float, default=5.0,
                    help="min seconds between polls (API politeness)")
    ap.add_argument("--max-seconds", type=float, default=3600.0)
    ap.add_argument("--max-rounds", type=int, default=None)
    ap.add_argument("--max-m", type=int, default=200, help="safety net on |M|")
    ap.add_argument("--runs-dir", default="runs/run1")
    ap.add_argument("--resume", action="store_true",
                    help="continue from the state files in --runs-dir")
    args = ap.parse_args(argv)

    runs = Path(args.runs_dir)
    (runs / "checkpoints").mkdir(parents=True, exist_ok=True)
    state_path = str(runs / "state.json")
    frontier_path = str(runs / "frontier.json")
    stop_file = str(runs / "STOP")

    if args.source == "recentchanges":
        src_kwargs = dict(ids_per_poll=args.chunk,
                          per_entity_cap=args.per_entity_cap or None,
                          record_path=str(runs / "polls.jsonl"))
        if args.resume:
            source = RecentChangesSource.load_state(frontier_path, **src_kwargs)
            print(f"resuming: change-stream state restored from {frontier_path}")
        else:
            source = RecentChangesSource(**src_kwargs)
    else:
        src_kwargs = dict(chunk_size=args.chunk, crawl=not args.no_crawl,
                          frontier_cap=args.frontier_cap,
                          per_entity_cap=args.per_entity_cap or None,
                          record_path=str(runs / "polls.jsonl"))
        if args.resume:
            source = RotatingWikidataSource.load_state(frontier_path, **src_kwargs)
            print(f"resuming: frontier restored from {frontier_path}")
        else:
            source = RotatingWikidataSource(args.seeds, **src_kwargs)

    def evaluate(feed, res):
        """Per-segment console digest + persist the frontier beside the runner state."""
        source.save_state(frontier_path)
        from collections import Counter
        dispositions = dict(Counter(o.disposition for o in res.outcomes if o.disposition))
        leg = source.legibility[-1] if source.legibility else None
        frontier_dropped = getattr(source, "frontier_dropped", 0)
        print(f"  segment: rounds={len(res.outcomes)} dispositions={dispositions}"
              + (f" legibility={leg:.2f}" if leg is not None else "")
              + (f" frontier_dropped={frontier_dropped}" if frontier_dropped else "")
              + (f" statements_dropped={source.statements_dropped}"
                 if source.statements_dropped else ""), flush=True)
        return {"legibility": leg}

    config = LiveRunConfig(
        ttl=args.ttl, segment_cap=args.segment_cap, min_interval_s=args.min_interval,
        max_rounds=args.max_rounds, max_seconds=args.max_seconds,
        max_m_relations=args.max_m, stop_file=stop_file,
        checkpoint=True, state_path=state_path,
    )
    service = TomosService(runs / "checkpoints")

    if args.resume:
        runner = LiveRunner.resume(state_path, source, WikiDisputeFeed, config,
                                   uod_id="run1", panel=_panel(),
                                   evaluate=evaluate, service=service)
    else:
        runner = LiveRunner("", source, WikiDisputeFeed, config,
                            uod_id="run1", panel=_panel(),
                            evaluate=evaluate, service=service)

    started = time.strftime("%Y-%m-%d %H:%M:%S")
    origin = (f"seeds={args.seeds}" if args.source == "frontier"
              else "the recentchanges stream (bots excluded)")
    print(f"run start {started} — source={args.source} · {origin} · ttl={args.ttl} "
          f"pacing={args.min_interval}s stop: touch {stop_file}", flush=True)
    res = runner.run()

    print(f"\nstopped: {res.stopped_because}   total rounds: {res.total_rounds}")
    for d in res.segments:
        print(f"  segment {d.segment}: rounds={d.rounds} |M|={d.m_relations} "
              f"dispositions={d.dispositions} decayed={d.decayed} ({d.elapsed_s:.1f}s)")
    if source.legibility:
        worst = max(source.legibility)
        print(f"legibility per poll: {['%.2f' % f for f in source.legibility]}"
              + ("   ⚠ labels degrading" if worst > 0.5 else ""))
    if res.episodes:
        from agon_metalearning import mechanism_principles
        print("mechanism principles (decay-aware, cross-segment):")
        for p in mechanism_principles(res.episodes):
            print(f"  {p.mechanism}: n={p.count} stick_rate={p.stick_rate} "
                  f"durable={p.durable} decay_erased={p.decay_erased}")
    if res.segments:
        from agon_metalearning import poise_from_digests
        strip = " ".join("●" if w.poised else ("○" if w.failure == "rigidity" else "✕")
                         for w in poise_from_digests(res.segments))
        print(f"poise per segment (● poised · ○ rigidity · ✕ thrash): {strip}")
    print(f"\nartifacts: {runs}/polls.jsonl (offline replay) · {runs}/checkpoints (UoDs) · "
          f"log your dispositions of the P1–P7 priors in runs/RUN_1_LOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
