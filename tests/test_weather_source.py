"""The first live resolving-membrane source (``src/weather_source.py``, §18) —
deterministic and offline: the NWS call is injected, the clock is injected, and the
whole loop (raise → M bets via the seeded law → the world resolves → the ledger
scores → a miss relinquishes the law) is exercised with fixtures. The real
``_live_fetch_json`` is never invoked in CI."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from weather_source import (
    LAW_PRECIP, LAW_TEMP, SEED_LAWS, WeatherSource, band_of, replay_item_batches,
)

T0 = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _fixture_fetch(forecast_temp_f=76, pop=80, obs_temp_c=None, obs_weather=""):
    """A fake NWS: one station, one forecast hour (13Z), observations at 13:40Z."""
    def fetch(url):
        if "/points/" in url:
            return {"properties": {"forecastHourly": "https://x/forecast"}}
        if "forecast" in url:
            return {"properties": {"periods": [{
                "startTime": "2026-07-06T13:00:00+00:00",
                "temperature": forecast_temp_f,
                "probabilityOfPrecipitation": {"value": pop},
            }]}}
        if "/observations" in url:
            return {"features": [{"properties": {
                "timestamp": "2026-07-06T13:40:00+00:00",
                "temperature": {"value": obs_temp_c},
                "textDescription": obs_weather,
                "presentWeather": [],
                "precipitationLastHour": {"value": None},
            }}]}
        raise AssertionError(f"unexpected url {url}")
    return fetch


def _source(clock_time, **fx):
    clock = {"now": clock_time}
    src = WeatherSource(stations={"KTST": (0.0, 0.0)},
                        fetch_json=_fixture_fetch(**fx),
                        clock=lambda: clock["now"])
    return src, clock


def test_band_discretization():
    assert band_of(76.3) == "75-79"
    assert band_of(80.0) == "80-84"
    assert band_of(-3.0) == "-5--1"


def test_raise_then_resolve_hit():
    src, clock = _source(T0, forecast_temp_f=76, pop=80, obs_temp_c=24.5)  # 76.1°F → 75-79
    batch1 = src.fetch()
    claims = {i.claim_egif for i in batch1}
    assert '(forecast_temp_band "KTST" "2026-07-06T13Z" "75-79")' in claims
    assert '(forecast_precip "KTST" "2026-07-06T13Z")' in claims
    assert all(i.happened for i in batch1)                    # arrivals, not yet bets
    assert src.claims_raised == 2 and not src.exhausted()

    clock["now"] = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)   # hour matured
    batch2 = src.fetch()
    by_claim = {i.claim_egif: i for i in batch2}
    temp = by_claim['(temp_band "KTST" "2026-07-06T13Z" "75-79")']
    assert temp.happened                                       # 24.5°C = 76.1°F → same band
    precip = by_claim['(precip "KTST" "2026-07-06T13Z")']
    assert not precip.happened                                 # no precip observed
    assert "~[ (precip" in precip.world_egif                   # the law-refuting shape
    assert src.resolutions == 2


def test_miss_carries_the_law_refuting_shape():
    src, clock = _source(T0, forecast_temp_f=76, pop=0, obs_temp_c=30.0)  # 86°F → 85-89
    src.fetch()
    clock["now"] = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)
    (item,) = src.fetch()
    assert not item.happened
    assert '(forecast_temp_band "KTST" "2026-07-06T13Z" "75-79")' in item.world_egif
    assert '~[ (temp_band "KTST" "2026-07-06T13Z" "75-79") ]' in item.world_egif
    assert '(temp_band "KTST" "2026-07-06T13Z" "85-89")' in item.world_egif


def test_unresolved_claim_drops_counted_after_grace():
    src, clock = _source(T0, forecast_temp_f=76, pop=0, obs_temp_c=None)
    def no_obs(url):
        if "/observations" in url:
            return {"features": []}
        return _fixture_fetch()(url)
    src._fetch = no_obs
    src.fetch()                    # the delegate's default pop=80 raises temp + precip
    clock["now"] = datetime(2026, 7, 6, 18, 30, tzinfo=timezone.utc)  # past grace (3h)
    assert src.fetch() == []
    assert src.unresolved_dropped == 2 and not src._pending


def test_state_round_trips_pending_claims(tmp_path):
    src, clock = _source(T0, forecast_temp_f=76, pop=80, obs_temp_c=24.5)
    src.fetch()
    sp = str(tmp_path / "ws.json")
    src.save_state(sp)
    src2 = WeatherSource.load_state(sp, stations={"KTST": (0.0, 0.0)},
                                    fetch_json=_fixture_fetch(obs_temp_c=24.5),
                                    clock=lambda: datetime(2026, 7, 6, 14, 5,
                                                           tzinfo=timezone.utc))
    assert src2.claims_raised == 2 and len(src2._pending) == 2
    batch = src2.fetch()                                      # resumed claims resolve
    assert {i.claim_egif for i in batch} == {
        '(temp_band "KTST" "2026-07-06T13Z" "75-79")',
        '(precip "KTST" "2026-07-06T13Z")'}


def test_record_and_replay_round_trip(tmp_path):
    rp = str(tmp_path / "items.jsonl")
    clock = {"now": T0}
    src = WeatherSource(stations={"KTST": (0.0, 0.0)},
                        fetch_json=_fixture_fetch(obs_temp_c=24.5), record_path=rp,
                        clock=lambda: clock["now"])
    b1 = src.fetch()
    clock["now"] = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)
    b2 = src.fetch()
    batches = replay_item_batches(rp)
    assert [[i.claim_egif for i in b] for b in batches] == [
        [i.claim_egif for i in b1], [i.claim_egif for i in b2]]


def test_end_to_end_the_naive_law_bets_and_is_falsified_by_a_miss():
    """The §18 headline, offline: M seeded with 'what is forecast, happens' BETS on
    the resolution claim (peel TRUE via materialization), scores a hit on a matching
    hour and a miss on a wrong band — and the miss, arriving in the law-refuting
    shape, makes the mechanical panel relinquish LAW_TEMP (challenge_to_M)."""
    from agon_evolution import (
        Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent,
        ObserverAgent, run,
    )
    from resolving_membrane import ResolvingFeed, ResolvingItem

    items = [
        ResolvingItem('(forecast_temp_band "KTST" "H1" "75-79")', happened=True),
        ResolvingItem('(temp_band "KTST" "H1" "75-79")', happened=True),        # hit
        ResolvingItem('(forecast_temp_band "KTST" "H2" "75-79")', happened=True),
        ResolvingItem('(temp_band "KTST" "H2" "75-79")', happened=False,        # miss
                      world_egif=('(forecast_temp_band "KTST" "H2" "75-79") '
                                  '~[ (temp_band "KTST" "H2" "75-79") ] '
                                  '(temp_band "KTST" "H2" "85-89")')),
    ]
    feed = ResolvingFeed(items)
    panel = Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                         ContradictionAgent()])
    res = run(" ".join(SEED_LAWS), feed, rounds=len(items), uod_id="w", name="w",
              seed_laws=list(SEED_LAWS), panel=panel)

    bets = [e for e in feed.ledger.entries
            if not e.claim_egif.startswith("(forecast_")]
    assert [e.result for e in bets] == ["hit", "miss"]        # M genuinely bet TRUE twice
    assert all(e.predicted == "true" for e in bets)
    dispositions = [o.disposition for o in res.outcomes]
    assert "challenge_to_M" in dispositions                    # the law fell to the world
    assert LAW_TEMP not in res.known_laws                      # relinquished
    assert any(LAW_PRECIP.strip() == l.strip() for l in res.known_laws)  # the other stands
