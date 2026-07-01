"""The game studying the game — a microscope on the automated Endoporeutic Game
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §6 + §4b). Runs WITHOUT an LLM: the mechanical loop
over reproducible pools makes the instruments tangible offline.

Two boards:
  1. the **meta-learning instruments** (§6) over the swan run — resolution principles mined
     from the trajectory (situation → disposition), the friction map, stickiness, and a small
     ablation (with vs without disuse-decay);
  2. the first **open membrane** (§4b) — a raise-only, sourced, dated discourse feed driving
     the loop, and the cross-source consistency report (contested vs settled).

    uv run python tools/build_metalearning_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import CorpusProposer, run
from agon_metalearning import (
    AblationVariant, episodes_from, friction_map, gaps,
    resolution_principles, run_ablation, stability_report,
)
from discourse_membrane import DiscourseFeed, DiscourseItem, consistency_report

SWAN_M0 = '(swan "Alba") (white "Alba") (swan "Ciel")'
SWAN_LAW = '~[ (swan *x) ~[ (white x) ] ]'
SWAN_POOL = ['(white "Ciel")', SWAN_LAW, '(swan "Nox") ~[ (white "Nox") ]']


def meta_board() -> None:
    res = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=3, uod_id="ml", name="ml swan",
              standing_proposal=SWAN_LAW)
    eps = episodes_from(res, run_id="swan")

    print("=== §6 · the game studying the game (swan run) ===\n")
    print("Episodes (situation → resolved disposition; did it stick?):")
    for e in eps:
        print(f"  r{e.round_idx}  {e.situation:22} → {e.disposition:16} "
              f"stuck={e.stuck}")
    print("\nResolution principles mined:")
    for p in resolution_principles(eps):
        tag = " THRASH" if p.thrash else ""
        print(f"  {p.situation:22} ⇒ {p.dominant:16} "
              f"stability={p.stability:.2f} support={p.support} "
              f"stick_rate={p.stick_rate}{tag}")
    print("\nFriction map (most contested first):")
    for f in friction_map(eps):
        print(f"  {f.situation:22} mean_disagreement={f.mean_disagreement:.2f} "
              f"branched={f.branched_rounds}")
    g = gaps(eps)
    print("\nCandidate missing rules:", g or "(none — every situation handled consistently)")

    print("\nAblation — disuse-decay off vs on:")
    for r in run_ablation(SWAN_M0, lambda: CorpusProposer(SWAN_POOL),
                          [AblationVariant("no_decay", {}),
                           AblationVariant("decay_ttl2", {"ttl": 2})], rounds=3):
        s = r.stability
        print(f"  {r.label:11} settled@{s.settle_round} revising={s.revising} "
              f"thrash={s.thrash_situations} final_relations={s.final_m_relations}")


def membrane_board() -> None:
    feed = DiscourseFeed([
        DiscourseItem("mon", "alice", '(hosts "Bayside" "Market")'),
        DiscourseItem("mon", "bob", '(hosts "Bayside" "Market")', deny=True),
        DiscourseItem("tue", "carol", '(ferry "Bayside" "Cove")'),
    ])
    res = run("", feed, rounds=5, uod_id="disc", name="discourse membrane")

    print("\n\n=== §4b · the first open membrane (raise-only discourse feed) ===\n")
    print(f"Days (generations): {feed.days}")
    for it, o in zip(feed.emitted, res.outcomes):
        print(f"  {it.day}  {it.source:6} {'DENIES ' if it.deny else 'asserts'} "
              f"{it.egif:32} → disposition={o.disposition}")
    print("\nCross-source consistency (the raise-only referee reports, does not adjudicate):")
    conflicts = consistency_report(feed.emitted)
    if not conflicts:
        print("  (the sources are consistent)")
    for c in conflicts:
        print(f"  CONTESTED {c.content_egif}: asserted by {c.asserted_by}, "
              f"denied by {c.denied_by} — a challenge_to_M or a DAG branch for the Agonothetes.")
    print("\nModel the discourse, not the world: settled facts stand; contested ones await "
          "the game (or the modal lens reads ◇ vs □ off the trajectory).")


def main() -> int:
    meta_board()
    membrane_board()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
