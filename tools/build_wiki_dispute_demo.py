"""Learning from wiki conflicts — a dispute record with conflict + resolution structure
drives the game, and the §6 meta-learning harvests what it teaches
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §4b + §6). Runs WITHOUT an LLM.

The story: editors war over three claims; consensus admits a general law; a reliable source
then cites a counterexample that relinquishes it; a third claim never resolves. The
meta-learning learns *which resolution mechanism produces durable knowledge*, ranks the edit
wars, and names the still-contested frontier.

    uv run python tools/build_wiki_dispute_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import run
from agon_metalearning import edit_war_friction, mechanism_principles, unresolved_frontier
from wiki_dispute_membrane import Resolution, WikiDispute, WikiDisputeFeed, WikiEdit

CONSENSUS_LAW = "~[ (author *x) ~[ (reliable x) ] ]"   # 'all authors are reliable'
M0 = '(author "Xavier") (reliable "Xavier")'            # the law holds at the outset

DISPUTES = [
    WikiDispute(CONSENSUS_LAW,
                [WikiEdit("alice", True), WikiEdit("bob", False), WikiEdit("alice", True)],
                Resolution("consensus", True)),
    WikiDispute('(reliable "Yolanda")',
                [WikiEdit("carol", True)],
                Resolution("reliable_source", False),
                world_egif='(author "Yolanda") ~[ (reliable "Yolanda") ]'),
    WikiDispute('(reliable "Zed")',
                [WikiEdit("dan", True), WikiEdit("eve", False),
                 WikiEdit("dan", True), WikiEdit("eve", False)],
                Resolution("unresolved", None),
                world_egif='(reliable "Zed")'),
]


def main() -> int:
    feed = WikiDisputeFeed(DISPUTES)
    res = run(M0, feed, rounds=len(DISPUTES), uod_id="wiki", name="wiki disputes")

    print("=== §4b · a wiki-dispute membrane (conflict + resolution structure) ===\n")
    for d, o in zip(DISPUTES, res.outcomes):
        settled = {True: "stands", False: "rejected", None: "UNRESOLVED"}[d.resolution.settled]
        print(f"  {d.claim_egif[:34]:36} edit-war reverts={d.reverts} "
              f"→ {d.resolution.mechanism:15} ({settled}) → disposition={o.disposition}")

    eps = feed.episodes(res)
    print("\n=== §6 · what the conflicts teach ===\n")
    print("Which resolution mechanism produces DURABLE knowledge:")
    for p in mechanism_principles(eps):
        mark = "  ← durable" if p.durable else ""
        print(f"  {p.mechanism:15} disposition={str(p.dominant_disposition):16} "
              f"stick_rate={p.stick_rate}{mark}")
    print("\nEdit-war friction (the contested frontier, fiercest first):")
    for e in edit_war_friction(eps):
        print(f"  reverts={e.reverts}  {e.claim_egif}")
    print(f"\nUnresolved frontier (◇ possible, not □ necessary): {unresolved_frontier(eps)}")

    print("\nLearned: a reliable-source citation overturned a prior consensus and STOOD, while "
          "the consensus generalization did NOT — reliable sources produce durable knowledge "
          "where a contradicted consensus does not. (Correspondence, not truth: every "
          "resolution is low-warrant; M self-certifies a track record, not truth.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
