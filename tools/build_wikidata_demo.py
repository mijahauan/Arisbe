"""The first *live* source — Wikidata — driving the automated Endoporeutic Game
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §4b/§10).

By default this runs OFFLINE on a small recorded slice (no network, no auth), so the pipeline is
tangible without hitting Wikidata: structured statements → disputes → the paced/bounded/checkpointed
LiveRunner → the §6 dispute-learning. The story: a bare (unreferenced) value is admitted, then
Wikidata deprecates it and a reliable-source value replaces it — the ContradictionAgent relinquishes
the bare value, so the referenced one is what stands (a reliable source overturns a bare one, no LLM).

Pass --live Q42 Q7259 … to fetch real entities via wbgetentities (public, no auth). Property/value
names come back as P/Q ids unless you add a label lookup.

    uv run python tools/build_wikidata_demo.py
    uv run python tools/build_wikidata_demo.py --live Q42
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
    args = ap.parse_args(argv)

    if args.live:
        print(f"Fetching {args.live} from Wikidata…")
        stmts = wbgetentities_fetch(args.live)
        source = WikidataSource([stmts])           # one poll of the live slice
        print(f"  {len(stmts)} statements.")
    else:
        source = WikidataSource(OFFLINE_POLLS)

    runner = LiveRunner("", source, WikiDisputeFeed,
                        LiveRunConfig(ttl=None, min_interval_s=2.0, checkpoint=False),
                        panel=_panel(),
                        clock=lambda: 0.0, sleep=lambda s: None)
    res = runner.run()

    print("\n=== Wikidata → the automated game (offline slice) ===\n")
    for d in res.segments:
        print(f"  segment {d.segment}: rounds={d.rounds} |M|={d.m_relations} "
              f"dispositions={d.dispositions}")
    print(f"\nstopped: {res.stopped_because}   total rounds: {res.total_rounds}")
    print(f"final M: {res.final_model_egif}")
    if not args.live:
        print("\nThe bare 'Cambridge' was admitted, then Wikidata deprecated it and a "
              "reliably-sourced 'London' replaced it — the ContradictionAgent relinquished the "
              "bare value, so the referenced one stands. A reliable source overturned a bare one, "
              "mechanically, with no LLM. (Correspondence, not truth: Wikidata is low-warrant "
              "input; nothing auto-promotes to the corpus.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
