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
    LAW_PRECIP, LAW_PRECIP_DRY, LAW_TEMP, SEED_LAWS, SEED_LAWS_CALIBRATED,
    WeatherSource, band_bounds, band_of, replay_item_batches,
)

T0 = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
T_MATURE = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)  # after the 13Z hour ends


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


# --- Run 9 (F2⁸): forecast-centered bins -------------------------------------

def test_band_bounds_grid_and_centered():
    # grid: fixed [k·width, …) alignment (the run-7/8 behaviour band_of wraps)
    assert band_bounds(76.3) == (75, "75-79")
    assert band_bounds(80.0) == (80, "80-84")
    # centered: the band is centered on the forecast, edge-fragility-free
    assert band_bounds(79.0, center=79.0) == (77, "77-81")
    assert band_bounds(80.0, center=80.0) == (78, "78-82")


def test_centered_bins_turn_a_grid_edge_miss_into_a_hit():
    """The F2⁸ mechanism: a forecast (79°F) near a grid edge with an observation
    just past it (81.4°F) *misses* under grid bins ("75-79" vs "80-84") but *hits*
    under forecast-centered bins ("77-81" ∋ 81.4°F)."""
    obs_c = (81.4 - 32) * 5 / 9

    src, clock = _source(T0, forecast_temp_f=79, pop=0, obs_temp_c=obs_c)
    src.fetch()
    clock["now"] = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)
    (grid_item,) = src.fetch()
    assert grid_item.claim_egif == '(temp_band "KTST" "2026-07-06T13Z" "75-79")'
    assert not grid_item.happened                    # grid edge miss

    clock2 = {"now": T0}
    src2 = WeatherSource(stations={"KTST": (0.0, 0.0)}, bin_mode="centered",
                         fetch_json=_fixture_fetch(forecast_temp_f=79, pop=0,
                                                   obs_temp_c=obs_c),
                         clock=lambda: clock2["now"])
    b1 = src2.fetch()
    assert '(forecast_temp_band "KTST" "2026-07-06T13Z" "77-81")' in {
        i.claim_egif for i in b1}
    clock2["now"] = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)
    (c_item,) = src2.fetch()
    assert c_item.claim_egif == '(temp_band "KTST" "2026-07-06T13Z" "77-81")'
    assert c_item.happened                            # centered ∋ 81.4°F


def test_invalid_bin_mode_rejected():
    import pytest
    with pytest.raises(ValueError):
        WeatherSource(stations={"KX": (0.0, 0.0)}, bin_mode="quantile")


# --- Run 9 (F3⁸): per-arm instrumentation ------------------------------------

def test_per_arm_counters_track_raise_and_resolve():
    src, clock = _source(T0, forecast_temp_f=76, pop=80, obs_temp_c=24.5)
    src.fetch()                                        # raises temp + precip
    assert src.claims_raised_by_kind == {"temp": 1, "precip": 1}
    assert src.resolutions_by_kind == {}
    clock["now"] = datetime(2026, 7, 6, 14, 5, tzinfo=timezone.utc)
    src.fetch()                                        # both mature + score
    assert src.resolutions_by_kind == {"temp": 1, "precip": 1}


def test_bin_mode_and_per_arm_counters_round_trip(tmp_path):
    clock = {"now": T0}
    src = WeatherSource(stations={"KTST": (0.0, 0.0)}, bin_mode="centered",
                        fetch_json=_fixture_fetch(forecast_temp_f=76, pop=80,
                                                  obs_temp_c=24.5),
                        clock=lambda: clock["now"])
    src.fetch()
    sp = str(tmp_path / "ws.json")
    src.save_state(sp)
    src2 = WeatherSource.load_state(sp, stations={"KTST": (0.0, 0.0)},
                                    fetch_json=_fixture_fetch(), clock=lambda: T0)
    assert src2._bin_mode == "centered"
    assert src2.claims_raised_by_kind == {"temp": 1, "precip": 1}


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


# --- run 11 (F1¹⁰): the calibrated precip arm — a two-direction cutpoint bet --

def _calibrated_source(pop, *, pop_cut=50, obs_weather="", obs_temp_c=24.5):
    clock = {"now": T0}
    src = WeatherSource(stations={"KTST": (0.0, 0.0)},
                        precip_mode="calibrated", pop_cut=pop_cut,
                        fetch_json=_fixture_fetch(pop=pop, obs_temp_c=obs_temp_c,
                                                  obs_weather=obs_weather),
                        clock=lambda: clock["now"])
    return src, clock


def test_calibrated_precip_bets_wet_above_cut_and_dry_below():
    """The calibrated arm bets a *direction* around ``pop_cut`` — wet at/above,
    dry below — where the gate arm could only ever bet wet."""
    wet, _ = _calibrated_source(pop=80, pop_cut=50)
    claims = {i.claim_egif for i in wet.fetch()}
    assert '(forecast_precip "KTST" "2026-07-06T13Z")' in claims   # PoP 80 ≥ cut → wet

    dry, _ = _calibrated_source(pop=20, pop_cut=50)
    claims = {i.claim_egif for i in dry.fetch()}
    assert '(forecast_dry "KTST" "2026-07-06T13Z")' in claims       # PoP 20 < cut → dry
    assert '(forecast_precip "KTST" "2026-07-06T13Z")' not in claims


def test_calibrated_dry_bet_hits_when_dry_and_misses_law_shape_when_it_rains():
    dry, clock = _calibrated_source(pop=20, obs_weather="")           # forecast dry, no rain
    dry.fetch()
    clock["now"] = T_MATURE
    (item,) = [i for i in dry.fetch() if i.claim_egif.startswith("(dry")]
    assert item.claim_egif == '(dry "KTST" "2026-07-06T13Z")' and item.happened  # dry → hit

    rainy, clock = _calibrated_source(pop=20, obs_weather="rain")     # forecast dry, it rained
    rainy.fetch()
    clock["now"] = T_MATURE
    (item,) = [i for i in rainy.fetch() if i.claim_egif.startswith("(dry")]
    assert not item.happened                                          # the dry law over-reached
    assert '(forecast_dry "KTST" "2026-07-06T13Z")' in item.world_egif
    assert '~[ (dry "KTST" "2026-07-06T13Z") ]' in item.world_egif
    assert '(precip "KTST" "2026-07-06T13Z")' in item.world_egif      # the refuting observation


def test_gate_mode_is_the_default_and_below_gate_raises_no_precip():
    """Run-10 parity: gate mode (default) only ever raises a wet claim, and only
    above the threshold — a below-gate forecast raises nothing (the dormancy)."""
    src, _ = _source(T0, pop=30)                                     # default precip_mode="gate"
    assert src._precip_mode == "gate"
    claims = {i.claim_egif for i in src.fetch()}
    assert not any("precip" in c or "dry" in c for c in claims)      # pop 30 < gate 60 → no bet


def test_calibrated_precip_state_round_trips(tmp_path):
    src, _ = _calibrated_source(pop=20, pop_cut=70)
    src._pop_cut = 80                                                # a mid-run recalibration
    src.fetch()
    sp = str(tmp_path / "ws.json")
    src.save_state(sp)
    src2 = WeatherSource.load_state(sp, stations={"KTST": (0.0, 0.0)},
                                    fetch_json=_fixture_fetch(), clock=lambda: T0)
    assert src2._precip_mode == "calibrated" and src2._pop_cut == 80


def test_F1_10_calibrated_dry_arm_recovers_where_the_gate_wet_arm_loses():
    """The run-11 headline (RUN_10_LOG F1¹⁰), offline through the real loop: in a
    DRY world (rain rare), the calibrated arm bets ``dry`` and *recovers to a
    positive net* — the selectivity gate, which can only ever bet ``wet``, loses
    every bet and relinquishes its law. Same world, opposite outcome, purely from
    the knob's nature."""
    from agon_evolution import (
        Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent,
        ObserverAgent, run,
    )
    from resolving_membrane import ResolvingFeed, ResolvingItem

    # Three dry hours: it does not rain.
    def dry_hours(forecast_atom, claim_atom, happened):
        items = []
        for h in ("H1", "H2", "H3"):
            items.append(ResolvingItem(f'({forecast_atom} "KTST" "{h}")', happened=True))
            items.append(ResolvingItem(f'({claim_atom} "KTST" "{h}")', happened=happened,
                                       world_egif=None if happened else
                                       f'(forecast_precip "KTST" "{h}") ~[ (precip "KTST" "{h}") ]'))
        return items

    panel = lambda: Agonothetes([ObserverAgent(), GeneralizerAgent(),
                                 ChallengerAgent(), ContradictionAgent()])

    # Calibrated arm: bets DRY; the dry event happens (no rain) → hits, and the
    # dry law is never refuted, so it keeps betting and net climbs.
    cal_items = dry_hours("forecast_dry", "dry", happened=True)
    cal = ResolvingFeed(cal_items)
    cal_res = run(" ".join(SEED_LAWS_CALIBRATED), cal, rounds=len(cal_items),
                  uod_id="c", name="c", seed_laws=list(SEED_LAWS_CALIBRATED), panel=panel())
    cal_bets = [e for e in cal.ledger.entries if not e.claim_egif.startswith("(forecast_")]

    # Gate arm: bets WET; it does not rain → the first bet misses, the world
    # relinquishes the law (challenge_to_M) and the arm falls SILENT (predict→
    # refute→silence: the run-7/run-10 trap) — it never recovers a hit.
    gate_items = dry_hours("forecast_precip", "precip", happened=False)
    gate = ResolvingFeed(gate_items)
    gate_res = run(" ".join(SEED_LAWS), gate, rounds=len(gate_items),
                   uod_id="g", name="g", seed_laws=list(SEED_LAWS), panel=panel())

    assert cal.ledger.net_score > 0                       # the calibrated arm RECOVERS
    assert all(e.result == "hit" for e in cal_bets)
    assert any(LAW_PRECIP_DRY.strip() == l.strip() for l in cal_res.known_laws)  # dry law stands

    assert gate.ledger.hits == 0                          # the gate arm NEVER recovers a hit
    assert gate.ledger.net_score < 0                       # and the world scored against it
    assert not any(LAW_PRECIP.strip() == l.strip() for l in gate_res.known_laws)  # law fell


# --- F1⁷: bounded retry/backoff around the flaky NWS endpoints ---------------

def test_fetch_retry_recovers_and_counts_no_error(_capture=None):
    """A transient failure that recovers within the retry budget is invisible —
    no error counted — and the backoff uses the injected sleep (no real waiting)."""
    calls = {"n": 0}
    slept = []

    def flaky(url):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("503")
        return {"ok": 1}

    src = WeatherSource(stations={"KX": (0.0, 0.0)}, fetch_json=flaky,
                        sleep=lambda s: slept.append(s), fetch_tries=3, fetch_backoff=0.5)
    assert src._fetch_retry("u") == {"ok": 1}
    assert calls["n"] == 3
    assert slept == [0.5, 1.0]                     # exponential backoff, injected sleep
    assert src.fetch_errors == 0                   # a recovered retry is not an error


def test_dark_station_is_bounded_and_counted_per_station():
    """A station whose endpoint is always down gives up after the retry budget and
    is counted per-station (the F1⁷ dark-station signal), degrading gracefully."""
    def dead(url):
        raise RuntimeError("down")

    src = WeatherSource(stations={"KX": (0.0, 0.0)}, fetch_json=dead,
                        sleep=lambda s: None, fetch_tries=3)
    assert src._recent_observations("KX") == []    # graceful empty, not a crash
    assert src.fetch_errors == 1                    # one error per exhausted fetch
    assert src.fetch_errors_by_station == {"KX": 1}


def test_per_station_errors_persist_across_state():
    """Per-station error counts + the (possibly re-generalized) claim knobs survive
    a save/load, so a resume reports them and carries the recalibrated discretization."""
    def dead(url):
        raise RuntimeError("down")

    src = WeatherSource(stations={"KX": (0.0, 0.0)}, fetch_json=dead,
                        sleep=lambda s: None, band_width=10, pop_threshold=80)
    src._recent_observations("KX")
    import tempfile, os
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    src.save_state(p)
    src2 = WeatherSource.load_state(p, stations={"KX": (0.0, 0.0)},
                                    fetch_json=dead, sleep=lambda s: None)
    os.unlink(p)
    assert src2.fetch_errors_by_station == {"KX": 1}
    assert src2._width == 10 and src2._pop == 80    # recalibrated knobs carried
