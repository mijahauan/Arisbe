"""Tests for the sports calibration controller (``sports_recalibration``, run 12)
— the F1¹¹ mechanism transplanted to a discrete domain. Deterministic, offline,
LLM-free: a pure function of a ``PredictionLedger`` + the current cut + standing
laws."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from resolving_membrane import PredictionLedger, ResolvingItem
from sports_recalibration import recalibrate
from sports_source import (
    HELD_LAWS, HELD_LAWS_ODDS, LAW_DOG, LAW_FAV, LAW_HOME, LAW_NAIVE, LAW_ODDS,
    LAW_STRONG, SEED_LAWS, SEED_LAWS_ODDS,
)


def _ledger(fav=(), dog=(), other=()):
    """A ledger of arm-B bets: fav=(bool…) scores (win_fav …), dog=(bool…) scores
    (win_dog …) — True = the picked team won (a hit). ``other`` adds rival-arm
    entries the controller must ignore."""
    led = PredictionLedger()
    r = 0
    for happened in fav:
        led.record(ResolvingItem('(win_fav "g" "T")', happened=happened), "true", r)
        r += 1
    for happened in dog:
        led.record(ResolvingItem('(win_dog "g" "T")', happened=happened), "true", r)
        r += 1
    for happened in other:
        led.record(ResolvingItem('(win_home "g" "T")', happened=happened), "true", r)
        r += 1
    return led


def test_cut_rises_when_favorite_bets_lose():
    """Favorite bets mostly missing = small edges don't cash → raise the cut (bet
    the favorite only on bigger edges, the underdog more)."""
    led = _ledger(fav=[False, False, False, True])
    rc = recalibrate(led, cut=50, standing_laws=list(SEED_LAWS))
    assert rc.cut == 75 and rc.changed
    assert rc.reseed_laws == []                          # everything stands


def test_cut_falls_when_underdog_bets_lose():
    """Underdog bets mostly missing = favorites win even at small edges → lower
    the cut (bet the favorite more)."""
    led = _ledger(dog=[False, False, False, True])
    rc = recalibrate(led, cut=50, standing_laws=list(SEED_LAWS))
    assert rc.cut == 25 and rc.changed


def test_cut_holds_when_both_directions_win():
    led = _ledger(fav=[True, True, False], dog=[True, True, True])
    rc = recalibrate(led, cut=50, standing_laws=list(SEED_LAWS))
    assert rc.cut == 50 and not rc.changed and rc.reseed_laws == []


def test_favorite_losses_take_precedence():
    """When both directions under-perform, the favorite side moves the cut (the
    run-11 wet-precedence rule transplanted) — one step per segment, no tug-of-war."""
    led = _ledger(fav=[False, False], dog=[False, False])
    rc = recalibrate(led, cut=50, standing_laws=list(SEED_LAWS))
    assert rc.cut == 75


def test_cut_bounded_at_floor_and_cap():
    led_dog = _ledger(dog=[False, False, False])
    rc = recalibrate(led_dog, cut=0, standing_laws=list(SEED_LAWS))
    assert rc.cut == 0 and not rc.changed                # floor: always-favorite
    led_fav = _ledger(fav=[False, False, False])
    rc = recalibrate(led_fav, cut=300, standing_laws=list(SEED_LAWS), cut_cap=300)
    assert rc.cut == 300 and not rc.changed              # cap holds


def test_fallen_arm_B_laws_are_reseeded():
    """Either fallen direction of the knob's two-direction bet is re-seeded —
    the reseed contract that keeps arm B betting after a refutation."""
    led = _ledger(fav=[True])
    standing = [l for l in SEED_LAWS if l not in (LAW_FAV, LAW_DOG)]
    rc = recalibrate(led, cut=50, standing_laws=standing)
    assert LAW_FAV in rc.reseed_laws and LAW_DOG in rc.reseed_laws and rc.changed


def test_held_rivals_are_reseeded_verbatim():
    """Arm C's rivals (home-wins / higher-win-pct-wins) are held: a fallen rival
    is re-asserted so the world keeps scoring its ledger — selection needs
    continued betting."""
    led = _ledger()
    standing = [l for l in SEED_LAWS if l not in HELD_LAWS]
    rc = recalibrate(led, cut=50, standing_laws=standing)
    assert LAW_HOME in rc.reseed_laws and LAW_STRONG in rc.reseed_laws
    assert rc.changed and any("held rivals" in n for n in rc.notes)


def test_the_odds_rival_is_held_when_the_run_carries_it():
    """With the keyed odds arm running, the driver holds via HELD_LAWS_ODDS — a
    fallen LAW_ODDS is re-asserted verbatim like the other rivals."""
    led = _ledger()
    standing = [l for l in SEED_LAWS_ODDS if l != LAW_ODDS]
    rc = recalibrate(led, cut=50, standing_laws=standing,
                     hold_laws=HELD_LAWS_ODDS)
    assert LAW_ODDS in rc.reseed_laws and rc.changed
    # …and the default hold set (no odds run) never touches LAW_ODDS.
    rc2 = recalibrate(led, cut=50, standing_laws=standing)
    assert LAW_ODDS not in rc2.reseed_laws


def test_the_naive_null_is_never_reseeded():
    """Arm A is the knob-type null (P1¹²): fallen LAW_NAIVE stays fallen — no
    path in the controller re-seeds it."""
    led = _ledger(fav=[False, False])
    standing = [l for l in SEED_LAWS if l != LAW_NAIVE]
    rc = recalibrate(led, cut=50, standing_laws=standing)
    assert LAW_NAIVE not in rc.reseed_laws


def test_rival_bets_do_not_move_the_cut():
    """The cut reads only arm-B bets — a losing streak on the home rival's ledger
    is not the knob's evidence."""
    led = _ledger(other=[False, False, False, False])
    rc = recalibrate(led, cut=50, standing_laws=list(SEED_LAWS))
    assert rc.cut == 50 and not rc.changed


def test_window_reads_only_recent_bets():
    """Old misses outside the window don't drag the cut once recent bets win."""
    led = _ledger(fav=[False] * 10 + [True] * 5)
    rc = recalibrate(led, cut=50, standing_laws=list(SEED_LAWS), window=5)
    assert rc.cut == 50 and not rc.changed


def test_no_bets_is_a_no_op():
    rc = recalibrate(_ledger(), cut=50, standing_laws=list(SEED_LAWS))
    assert not rc.changed and rc.cut == 50 and rc.reseed_laws == []


def test_deterministic():
    led = _ledger(fav=[False, False, True], dog=[True])
    a = recalibrate(led, cut=50, standing_laws=[LAW_NAIVE])
    b = recalibrate(led, cut=50, standing_laws=[LAW_NAIVE])
    assert (a.cut, a.reseed_laws, a.notes, a.changed) == \
           (b.cut, b.reseed_laws, b.notes, b.changed)
