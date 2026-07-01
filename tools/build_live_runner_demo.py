"""Running the automated Endoporeutic Game against a *live* source — bounded, paced, checkpointed
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §4b + the operational section). Runs WITHOUT an LLM: an
offline ReplaySource stands in for a live wiki-dispute stream, the clock/sleep are injected so
there is no real waiting, and the segment digests show pacing + bounded |M| + per-segment learning.

A live adapter (a real wiki/forum or prediction-market API) replaces ReplaySource alone.

    uv run python tools/build_live_runner_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_metalearning import mechanism_principles, unresolved_frontier
from live_runner import LiveRunConfig, LiveRunner, ReplaySource
from wiki_dispute_membrane import Resolution, WikiDispute, WikiDisputeFeed, WikiEdit


def _d(claim, mech, settled, reverts=0, world=None):
    edits = [WikiEdit("alice", True)] + [WikiEdit("bob", False)] * reverts
    return WikiDispute(claim, edits, Resolution(mech, settled), world_egif=world)


# A simulated live stream: successive polls each deliver a fresh batch of disputes. Later polls
# stop reusing early topics, so disuse-decay erases them and |M| stays bounded.
STREAM = [
    [_d('(hosts "Bayside" "Market")', "consensus", True),
     _d('(ferry "Bayside" "Cove")', "reliable_source", True, reverts=1)],
    [_d('(hosts "Hillford" "Fair")', "reliable_source", True),
     _d('(safe "Bayside")', "unresolved", None, world='(safe "Bayside")')],
    [_d('(hosts "Riverton" "Regatta")', "admin", True),
     _d('(clean "Riverton")', "consensus", True, reverts=2)],
    [_d('(hosts "Seacliff" "Gala")', "reliable_source", True)],
]


def evaluate(feed, res):
    eps = feed.episodes(res)
    return {
        "durable_mechanisms": [p.mechanism for p in mechanism_principles(eps) if p.durable],
        "unresolved": unresolved_frontier(eps),
    }


def main() -> int:
    clock = [0.0]
    cfg = LiveRunConfig(ttl=3, segment_cap=25, min_interval_s=2.0, checkpoint=False,
                        max_seconds=100.0)
    runner = LiveRunner(
        "", ReplaySource(STREAM), WikiDisputeFeed, cfg,
        uod_id="live_wiki", evaluate=evaluate,
        clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
    )
    result = runner.run()

    print("=== live automated game — segment digests (an offline wiki-dispute stream) ===\n")
    print(f"{'seg':>3} {'rounds':>6} {'|M|':>4} {'decayed':>7} {'elapsed':>8}  learning / evaluation")
    for d in result.segments:
        learned = ", ".join(d.extra.get("durable_mechanisms", [])) or "—"
        unresolved = d.extra.get("unresolved", [])
        note = f"durable: {learned}" + (f"  ◇unresolved: {unresolved}" if unresolved else "")
        print(f"{d.segment:>3} {d.rounds:>6} {d.m_relations:>4} {d.decayed:>7} "
              f"{d.elapsed_s:>7.1f}s  {note}")

    print(f"\nstopped because: {result.stopped_because}   total rounds: {result.total_rounds}")
    print(f"final |M| (bounded by disuse-decay, ttl={cfg.ttl}): "
          f"{result.segments[-1].m_relations} relations")
    print("\nPacing keeps polls apart (min_interval_s); disuse-decay keeps |M| — and thus "
          "per-round cost, memory, and per-checkpoint disk — flat over an indefinite run; each "
          "segment is checkpointed and then its in-RAM history is pruned. Correspondence, not "
          "truth: a live source is low-warrant input; nothing auto-promotes to the corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
