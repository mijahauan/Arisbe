"""The first *raise-and-resolve* membrane — a membrane with world-teeth
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §4b). Runs WITHOUT an LLM: recorded world outcomes make
the Robot-Scientist selection tangible offline.

Two theories of the same little world compete; the world resolves claims over time; M
*predicts* via its laws and is *empirically falsified* where it over-reaches; the ledger's
track record lets selection pick the better predictor.

    uv run python tools/build_resolving_membrane_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import run
from resolving_membrane import ResolvingFeed, ResolvingItem, select_best

FACTS = '(swan "Nox") (swan "Dove") (bird "Nox") (bird "Dove")'
LAW_FLIES = '~[ (bird *x) ~[ (flies x) ] ]'    # correct in this world: birds fly
LAW_WHITE = '~[ (swan *x) ~[ (white x) ] ]'    # over-general: not all swans are white

WORLD = [
    ResolvingItem('(flies "Nox")', happened=True),                       # the world: Nox flies
    ResolvingItem('(white "Nox")', happened=False,                       # the world: Nox is NOT white
                  world_egif='(swan "Nox") ~[ (white "Nox") ]'),
]


def _arm(label: str, law: str):
    feed = ResolvingFeed(WORLD)
    res = run(f"{FACTS} {law}", feed, rounds=len(WORLD),
              uod_id=label, name=label, seed_laws=[law])
    return label, feed, res


def main() -> int:
    arms = [
        _arm("theory_flies (bird→flies, correct)", LAW_FLIES),
        _arm("theory_white (swan→white, over-general)", LAW_WHITE),
    ]

    print("=== §4b · a raise-and-resolve membrane (the world returns verdicts over time) ===\n")
    for label, feed, res in arms:
        led = feed.ledger
        print(f"— {label}")
        for e, o in zip(led.entries, res.outcomes):
            world = "happened" if e.happened else "did NOT happen"
            print(f"    forecast {e.claim_egif:16} = {e.predicted:8} | world: {world:14} "
                  f"→ {e.result.upper():7} | disposition={o.disposition}")
        print(f"    track record: hits={led.hits} misses={led.misses} "
              f"abstentions={led.abstentions}  net={led.net_score}  accuracy={led.accuracy}\n")

    best = select_best([(label, feed.ledger) for label, feed, _ in arms])
    print(f"THE WORLD SELECTS: {best}")
    print("\nThe over-general law forecast a non-white swan white and was empirically falsified "
          "(challenge_to_M relinquished it); the conservative theory abstained where it had no "
          "basis and predicted correctly where it did. Selection is by track record, not "
          "coherence — the Robot-Scientist teeth. (Correspondence, not truth: a resolved outcome "
          "is low-warrant data; M self-certifies a track record, not truth about the world.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
