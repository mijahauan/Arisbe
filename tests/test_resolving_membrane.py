"""Tests for the first raise-and-resolve membrane (``resolving_membrane``) — §4b of the
automated Endoporeutic Game. Offline and deterministic (recorded world outcomes, no network):
M *predicts* via its laws, the world *resolves*, an over-general law is empirically falsified
(disposed ``challenge_to_M`` by the existing mechanical panel), and the ledger's track record
lets selection pick the better predictor — the Robot-Scientist teeth, no LLM."""

from agon_evolution import run
from resolving_membrane import (
    PredictionLedger, ResolvingFeed, ResolvingItem, ScoreEntry, classify, select_best,
)

FACTS = '(swan "Nox") (swan "Dove") (bird "Nox") (bird "Dove")'
LAW_WHITE = '~[ (swan *x) ~[ (white x) ] ]'    # over-general — the world has a non-white swan
LAW_FLIES = '~[ (bird *x) ~[ (flies x) ] ]'    # correct in this world

ITEMS = [
    ResolvingItem('(flies "Nox")', happened=True),
    ResolvingItem('(white "Nox")', happened=False,
                  world_egif='(swan "Nox") ~[ (white "Nox") ]'),
]


def _arm(law):
    feed = ResolvingFeed(ITEMS)
    res = run(f"{FACTS} {law}", feed, rounds=2, uod_id="rr", name="rr", seed_laws=[law])
    return feed, res


# --------------------------------------------------------------------------- #
# Scoring primitives                                                           #
# --------------------------------------------------------------------------- #

def test_classify_scores_forecast_against_the_world():
    assert classify("true", True) == "hit"
    assert classify("true", False) == "miss"
    assert classify("false", False) == "hit"
    assert classify("false", True) == "miss"
    assert classify("unknown", True) == "abstain"     # open-world: no bet placed


def test_ledger_tallies_net_and_accuracy():
    led = PredictionLedger()
    led.record(ResolvingItem("(a)", True), "true", 1)      # hit
    led.record(ResolvingItem("(b)", False), "true", 2)     # miss
    led.record(ResolvingItem("(c)", True), "unknown", 3)   # abstain
    assert (led.hits, led.misses, led.abstentions) == (1, 1, 1)
    assert led.net_score == 0
    assert led.accuracy == 0.5                             # abstentions excluded


def test_ground_truth_defaults():
    assert ResolvingItem("(p)", True).ground_truth() == "(p)"
    assert ResolvingItem("(p)", False).ground_truth() == "~[ (p) ]"
    assert ResolvingItem("(p)", False, world_egif="(q) ~[ (p) ]").ground_truth() == "(q) ~[ (p) ]"


# --------------------------------------------------------------------------- #
# The feed drives the loop; the world resolves                                 #
# --------------------------------------------------------------------------- #

def test_feed_records_forecast_and_exhausts():
    feed = ResolvingFeed([ResolvingItem('(flies "Nox")', happened=True)])
    m = None
    from egif_parser_dau import parse_egif
    m = parse_egif(f"{FACTS} {LAW_FLIES}")
    assert feed.propose(m, 1) == '(flies "Nox")'           # M forecasts, then the truth is scribed
    assert feed.ledger.entries[-1].predicted == "true"     # bird→flies entails it
    assert feed.propose(m, 2) is None                      # exhausted


def test_world_falsifies_the_overgeneral_law_via_challenge():
    feed, res = _arm(LAW_WHITE)
    # M forecast white(Nox)=TRUE via the law; the world said no → a miss, and the panel
    # relinquishes the over-general law (challenge_to_M).
    white = next(e for e in feed.ledger.entries if e.claim_egif == '(white "Nox")')
    assert white.predicted == "true" and white.result == "miss"
    assert "challenge_to_M" in [o.disposition for o in res.outcomes]
    assert feed.ledger.net_score == -1


def test_conservative_theory_abstains_and_is_not_falsified():
    feed, res = _arm(LAW_FLIES)
    assert feed.ledger.hits == 1 and feed.ledger.misses == 0   # flies(Nox) hit; white abstained
    assert feed.ledger.net_score == 1
    assert "challenge_to_M" not in [o.disposition for o in res.outcomes]


def test_seed_laws_is_what_lets_the_world_falsify_a_standing_law():
    # without seed_laws the standing law is invisible to the Challenger → no falsification
    feed = ResolvingFeed(ITEMS)
    res = run(f"{FACTS} {LAW_WHITE}", feed, rounds=2, uod_id="rr", name="rr")  # no seed_laws
    assert "challenge_to_M" not in [o.disposition for o in res.outcomes]


# --------------------------------------------------------------------------- #
# Selection — the world ranks the predictors                                   #
# --------------------------------------------------------------------------- #

def test_select_best_picks_the_better_predictor():
    correct, _ = _arm(LAW_FLIES)
    overgeneral, _ = _arm(LAW_WHITE)
    winner = select_best([
        ("overgeneral", overgeneral.ledger),
        ("correct", correct.ledger),
    ])
    assert winner == "correct"                             # the world selects against over-reach


def test_select_best_empty_is_none():
    assert select_best([]) is None
