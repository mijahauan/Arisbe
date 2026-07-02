"""The first *live* source — Wikidata — driving the automated Endoporeutic Game
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §4b/§10).

By default this runs OFFLINE on a small recorded slice (no network, no auth), so the pipeline is
tangible without hitting Wikidata: structured statements → disputes → the paced/bounded/checkpointed
LiveRunner → the §6 dispute-learning. The story: a bare (unreferenced) value is admitted, then
Wikidata deprecates it and a reliable-source value replaces it — the ContradictionAgent relinquishes
the bare value, so the referenced one is what stands (a reliable source overturns a bare one, no LLM).

Pass --live Q42 Q7259 … to fetch real entities via wbgetentities (public, no auth). P/Q ids are
resolved to their English labels by default (--no-labels keeps the raw ids), so M reads
(place_of_birth "Douglas Adams" "Cambridge"), not (p19 "Q42" "Q350"). --limit bounds how many
statements are taken, --max-rounds/--ttl bound the run (the peel is super-linear in |M| — see §10).

    uv run python tools/build_wikidata_demo.py
    uv run python tools/build_wikidata_demo.py --live Q42 --limit 60 --ttl 30
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import (
    Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent, ObserverAgent,
)
from live_runner import LiveRunConfig, LiveRunner
from wiki_dispute_membrane import WikiDisputeFeed
from wikidata_source import WikidataSource, WikidataStatement as WS, wbgetentities_fetch

OFFLINE_POLLS = [
    [WS("Douglas_Adams", "place of birth", "Cambridge", "normal", referenced=False)],
    [WS("Douglas_Adams", "place of birth", "Cambridge", "deprecated", referenced=False),
     WS("Douglas_Adams", "place of birth", "London", "normal", referenced=True)],
]


def _panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", nargs="+", metavar="QID",
                    help="fetch these Wikidata entities live (public API, no auth)")
    ap.add_argument("--no-labels", action="store_true",
                    help="keep raw P/Q ids instead of resolving labels")
    ap.add_argument("--limit", type=int, default=60,
                    help="max statements to take from a live fetch (default 60)")
    ap.add_argument("--max-rounds", type=int, default=None,
                    help="stop the run after this many rounds")
    ap.add_argument("--ttl", type=int, default=None,
                    help="disuse-decay ttl in global rounds (bounds |M|)")
    args = ap.parse_args(argv)

    if args.live:
        print(f"Fetching {args.live} from Wikidata…")
        stmts = wbgetentities_fetch(args.live, with_labels=not args.no_labels)
        stmts = stmts[: args.limit]
        source = WikidataSource([stmts])           # one poll of the live slice
        print(f"  {len(stmts)} statements (limit {args.limit}).")
    else:
        source = WikidataSource(OFFLINE_POLLS)

    import time
    runner = LiveRunner("", source, WikiDisputeFeed,
                        LiveRunConfig(ttl=args.ttl, min_interval_s=2.0, checkpoint=False,
                                      max_rounds=args.max_rounds),
                        panel=_panel(),
                        clock=(time.monotonic if args.live else lambda: 0.0),
                        sleep=(time.sleep if args.live else lambda s: None))
    res = runner.run()

    print("\n=== Wikidata → the automated game ===\n")
    for d in res.segments:
        print(f"  segment {d.segment}: rounds={d.rounds} |M|={d.m_relations} "
              f"dispositions={d.dispositions} decayed={d.decayed} ({d.elapsed_s:.1f}s)")
    print(f"\nstopped: {res.stopped_because}   total rounds: {res.total_rounds}")
    if source.legibility:
        worst = max(source.legibility)
        print(f"legibility tripwire (unresolved-id fraction per poll): "
              f"{['%.2f' % f for f in source.legibility]}"
              + ("   ⚠ labels degrading" if worst > 0.5 else ""))
    print(f"final M: {res.final_model_egif}")
    if res.episodes:
        from agon_metalearning import mechanism_principles
        print("\nmechanism principles (decay-aware, cross-segment):")
        for p in mechanism_principles(res.episodes):
            print(f"  {p.mechanism}: n={p.count} stick_rate={p.stick_rate} "
                  f"durable={p.durable} decay_erased={p.decay_erased}")
    if res.segments:
        from agon_metalearning import poise_from_digests
        readings = poise_from_digests(res.segments)
        line = " ".join("●" if w.poised else ("○" if w.failure == "rigidity" else "✕")
                        for w in readings)
        print(f"\npoise per segment (● poised · ○ rigidity · ✕ thrash): {line}")
    if not args.live:
        print("\nThe bare 'Cambridge' was admitted, then Wikidata deprecated it and a "
              "reliably-sourced 'London' replaced it — the ContradictionAgent relinquished the "
              "bare value, so the referenced one stands. A reliable source overturned a bare one, "
              "mechanically, with no LLM. (Correspondence, not truth: Wikidata is low-warrant "
              "input; nothing auto-promotes to the corpus.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
