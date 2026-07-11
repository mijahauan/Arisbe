"""Tests for the weather re-generalization controller (``weather_recalibration``,
run 8) — the mechanism that turns predict→refute→**silence** into
predict→refute→**re-generalize**. Deterministic, offline, LLM-free: a pure function
of a ``PredictionLedger`` + current knobs + standing laws.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from resolving_membrane import PredictionLedger, ResolvingItem
from weather_recalibration import recalibrate
from weather_source import LAW_PRECIP, LAW_PRECIP_DRY, LAW_TEMP


def _precip_ledger(wet=(), dry=()):
    """A ledger of calibrated precip bets: wet=(bool…) scores (precip …), dry=(bool…)
    scores (dry …) — True = the forecast direction happened (a hit)."""
    led = PredictionLedger()
    r = 0
    for happened in wet:
        led.record(ResolvingItem('(precip "K" "h")', happened=happened), "true", r); r += 1
    for happened in dry:
        led.record(ResolvingItem('(dry "K" "h")', happened=happened), "true", r); r += 1
    return led


_CAL_LAWS = [LAW_TEMP, LAW_PRECIP, LAW_PRECIP_DRY]


def test_calibrated_cut_rises_when_wet_bets_lose():
    """Wet bets mostly missing = rain rarer than the cut assumes → raise the cut
    (bet wet less, dry more). The gate-mode pop_threshold is untouched."""
    led = _precip_ledger(wet=[False, False, False, False, True])
    rc = recalibrate(led, band_width=5, pop_threshold=60, pop_cut=50,
                     precip_mode="calibrated", standing_laws=_CAL_LAWS)
    assert rc.pop_cut == 60 and rc.changed              # cut stepped up
    assert rc.pop_threshold == 60                        # the selectivity gate is not the knob


def test_calibrated_cut_falls_when_dry_bets_lose():
    """Dry bets mostly missing = rain commoner than the cut assumes → lower the cut."""
    led = _precip_ledger(dry=[False, False, False, True])
    rc = recalibrate(led, band_width=5, pop_threshold=60, pop_cut=50,
                     precip_mode="calibrated", standing_laws=_CAL_LAWS)
    assert rc.pop_cut == 40 and rc.changed


def test_calibrated_cut_holds_when_both_directions_win():
    """A calibrated cut where each direction is right more than half the time is a
    no-op — the arm has found the crossing."""
    led = _precip_ledger(wet=[True, True, False], dry=[True, True, True])
    rc = recalibrate(led, band_width=5, pop_threshold=60, pop_cut=50,
                     precip_mode="calibrated", standing_laws=_CAL_LAWS)
    assert rc.pop_cut == 50 and not rc.changed


def test_calibrated_reseeds_a_fallen_dry_law():
    """A relinquished dry law (absent from standing_laws) is marked for re-seeding
    so the second act is prediction, not silence — the run-8 mechanism, dry side."""
    led = _precip_ledger(dry=[False, False, True])
    rc = recalibrate(led, band_width=5, pop_threshold=60, pop_cut=50,
                     precip_mode="calibrated", standing_laws=[LAW_TEMP, LAW_PRECIP])
    assert LAW_PRECIP_DRY in rc.reseed_laws and rc.changed


def test_calibrated_cut_is_capped():
    """The cut cannot exceed pop_cap — a persistently-dry world pins it at the cap
    (almost always betting dry, the recovering majority-outcome regime)."""
    led = _precip_ledger(wet=[False] * 6)
    rc = recalibrate(led, band_width=5, pop_threshold=60, pop_cut=90,
                     precip_mode="calibrated", standing_laws=_CAL_LAWS, pop_cap=90)
    assert rc.pop_cut == 90                              # already at cap → no further rise


def _ledger(temp=(), precip=()):
    """A ledger of resolution bets: temp/precip are iterables of bools (True=hit)."""
    led = PredictionLedger()
    r = 0
    for happened in temp:
        led.record(ResolvingItem('(temp_band "K" "h" "60-64")', happened=happened),
                   "true", r)
        r += 1
    for happened in precip:
        led.record(ResolvingItem('(precip "K" "h")', happened=happened), "true", r)
        r += 1
    return led


def test_a_fallen_temp_law_widens_the_band_and_reseeds():
    """The temp law was relinquished (absent from standing_laws); after temp misses
    the controller widens the band one step and marks the law for re-seeding."""
    led = _ledger(temp=[False, False, False])
    rc = recalibrate(led, band_width=5, pop_threshold=60, standing_laws=[LAW_PRECIP])
    assert rc.band_width == 10                       # widened one step
    assert rc.pop_threshold == 60                    # precip untouched (still standing, no bets)
    assert LAW_TEMP in rc.reseed_laws and LAW_PRECIP not in rc.reseed_laws
    assert rc.changed


def test_a_healthy_standing_law_is_left_alone():
    """A kind that is standing and meets the reliability target is a no-op."""
    led = _ledger(temp=[True, True, True, True])
    rc = recalibrate(led, band_width=5, pop_threshold=60,
                     standing_laws=[LAW_TEMP, LAW_PRECIP])
    assert not rc.changed and rc.band_width == 5 and rc.reseed_laws == []


def test_underperforming_but_still_standing_widens_without_reseed():
    """A standing law whose recent accuracy is below target is recalibrated (band
    widened) but not re-seeded — it is still on M, only its discretization moves."""
    led = _ledger(temp=[True, False, False, False])   # 0.25 accuracy < 0.6
    rc = recalibrate(led, band_width=5, pop_threshold=60,
                     standing_laws=[LAW_TEMP, LAW_PRECIP])
    assert rc.band_width == 10
    assert rc.reseed_laws == []                       # still standing → not reseeded
    assert rc.changed


def test_precip_raises_the_pop_threshold():
    """Precip re-generalizes by *raising* the PoP threshold (only confident
    forecasts claimed) — better calibration = higher reliability."""
    led = _ledger(precip=[False, False])
    rc = recalibrate(led, band_width=5, pop_threshold=60, standing_laws=[LAW_TEMP])
    assert rc.pop_threshold == 70 and LAW_PRECIP in rc.reseed_laws
    assert rc.band_width == 5                          # temp untouched


def test_the_band_cap_terminates_but_still_reseeds_a_fallen_law():
    """At the cap the knob can't move, but a fallen law is still brought back so the
    game doesn't stay silent."""
    led = _ledger(temp=[False, False])
    rc = recalibrate(led, band_width=20, pop_threshold=60, standing_laws=[LAW_PRECIP],
                     band_cap=20)
    assert rc.band_width == 20 and LAW_TEMP in rc.reseed_laws and rc.changed


def test_never_tried_kind_is_skipped():
    """A kind with no bets in the ledger is left alone even if its law is absent."""
    led = _ledger(temp=[True])                         # only temp bets
    rc = recalibrate(led, band_width=5, pop_threshold=60, standing_laws=[LAW_TEMP])
    # precip has no bets and is absent from standing_laws, but is not touched
    assert rc.pop_threshold == 60 and LAW_PRECIP not in rc.reseed_laws


def test_deterministic():
    led = _ledger(temp=[False, False], precip=[False])
    a = recalibrate(led, band_width=5, pop_threshold=60, standing_laws=[])
    b = recalibrate(led, band_width=5, pop_threshold=60, standing_laws=[])
    assert (a.band_width, a.pop_threshold, a.reseed_laws) == \
           (b.band_width, b.pop_threshold, b.reseed_laws)
