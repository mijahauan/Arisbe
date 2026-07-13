"""The discrete resolving-membrane source (``src/sports_source.py``, run 12) —
deterministic and offline: the MLB call is injected, the clock is injected, and the
whole loop (raise picks → M bets via the seeded laws → finals resolve → the ledger
scores → a miss relinquishes the law) is exercised with fixtures. The real
``_live_fetch_json`` is never invoked in CI."""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sports_source import (
    HELD_LAWS, LAW_DOG, LAW_FAV, LAW_HOME, LAW_NAIVE, LAW_STRONG, SEED_LAWS,
    SportsSource, favorite_of, pct_of, replay_item_batches,
)

T0 = datetime(2026, 7, 12, 15, 0, tzinfo=timezone.utc)      # before first pitch
T_AFTER = datetime(2026, 7, 13, 3, 0, tzinfo=timezone.utc)  # after the final
GAME_TIME = "2026-07-12T18:05:00Z"
DATE = "2026-07-12"
HOME, AWAY = "Harbor Homers", "Arch Astros"


def _game(pk=776001, state="Preview", detailed="Scheduled",
          home_winner=None, away_winner=None, game_date=GAME_TIME,
          home=HOME, away=AWAY, home_id=1, away_id=2):
    def side(name, tid, winner):
        d = {"team": {"id": tid, "name": name}}
        if winner is not None:
            d["isWinner"] = winner
        return d
    return {"gamePk": pk, "gameDate": game_date,
            "status": {"abstractGameState": state, "detailedState": detailed},
            "teams": {"home": side(home, home_id, home_winner),
                      "away": side(away, away_id, away_winner)}}


def _fixture_fetch(games, records=((1, 60, 40), (2, 50, 50))):
    """A fake MLB API: one slate of games (any date) + one standings table.
    ``games`` may be a callable for phase-dependent payloads."""
    def fetch(url):
        if "/schedule" in url:
            gs = games() if callable(games) else games
            return {"dates": [{"date": DATE, "games": gs}]}
        if "/standings" in url:
            return {"records": [{"teamRecords": [
                {"team": {"id": tid, "name": f"T{tid}"}, "wins": w, "losses": l}
                for tid, w, l in records]}]}
        raise AssertionError(f"unexpected url {url}")
    return fetch


def _source(clock_time, games, records=((1, 60, 40), (2, 50, 50)), **kw):
    clock = {"now": clock_time}
    src = SportsSource(fetch_json=_fixture_fetch(games, records),
                       clock=lambda: clock["now"], **kw)
    return src, clock


def test_pct_and_favorite_helpers():
    assert pct_of(60, 40) == 0.6
    assert pct_of(0, 0) == 0.5                          # no evidence → even
    assert favorite_of("H", "A", 0.6, 0.5) == ("H", "A", 100)
    assert favorite_of("H", "A", 0.45, 0.55) == ("A", "H", 100)
    assert favorite_of("H", "A", 0.5, 0.5) == ("H", "A", 0)   # tie → home


def test_raise_picks_all_arms_favorite_above_cut():
    """Home .600 vs away .500 → diff 100 ≥ cut 50: naive/home pick home, strong
    picks the favorite (home), cal bets the favorite direction."""
    src, _ = _source(T0, [_game()])
    claims = {i.claim_egif for i in src.fetch()}
    assert f'(pick_naive "776001" "{HOME}")' in claims
    assert f'(pick_home "776001" "{HOME}")' in claims
    assert f'(pick_strong "776001" "{HOME}")' in claims
    assert f'(pick_fav "776001" "{HOME}")' in claims
    assert src.claims_raised_by_kind == {"naive": 1, "home": 1, "strong": 1, "fav": 1}


def test_cal_bets_underdog_below_cut():
    """diff 100 < cut 150 → arm B bets the underdog (the two-direction shape the
    F1¹¹ mechanism transplants); the rivals are unaffected."""
    src, _ = _source(T0, [_game()], cut=150)
    claims = {i.claim_egif for i in src.fetch()}
    assert f'(pick_dog "776001" "{AWAY}")' in claims
    assert not any(c.startswith("(pick_fav") for c in claims)
    assert f'(pick_strong "776001" "{HOME}")' in claims


def test_tie_breaks_to_home():
    """Equal records: the favorite is the home team (documented tie-break); at the
    default cut 50, diff 0 < 50 → cal bets the underdog = the away team."""
    src, _ = _source(T0, [_game()], records=((1, 50, 50), (2, 50, 50)))
    claims = {i.claim_egif for i in src.fetch()}
    assert f'(pick_strong "776001" "{HOME}")' in claims
    assert f'(pick_dog "776001" "{AWAY}")' in claims


def test_no_reclaim_across_polls():
    src, _ = _source(T0, [_game()])
    assert len(src.fetch()) == 4
    assert src.fetch() == []                            # same slate, nothing new
    assert src.claims_raised == 4


def test_non_regular_season_games_are_not_picked():
    """sportId=1 also carries the All-Star/exhibition slate (gameType "A", seen
    live 2026-07-12) — only regular-season games ("R", or absent in fixtures) are
    picked; the theories and the P4¹² literature check are regular-season claims."""
    g = _game()
    g["gameType"] = "A"
    src, _ = _source(T0, [g])
    assert src.fetch() == []
    g2 = _game()
    g2["gameType"] = "R"
    src2, _ = _source(T0, [g2])
    assert len(src2.fetch()) == 4


def test_live_or_final_games_are_not_picked():
    """A pick is a forecast — a game already underway (or final) raises nothing."""
    src, _ = _source(T0, [_game(state="Live", detailed="In Progress")])
    assert src.fetch() == []
    src2, _ = _source(T0, [_game(state="Final", detailed="Final",
                                 home_winner=True, away_winner=False)])
    assert src2.fetch() == []


def test_resolve_home_win_scores_every_arm():
    """Home (the favorite) wins → naive/home/strong/fav all hit."""
    phase = {"final": False}
    games = lambda: [_game(state="Final", detailed="Final", home_winner=True,
                           away_winner=False)] if phase["final"] else [_game()]
    src, clock = _source(T0, games)
    src.fetch()
    phase["final"] = True
    clock["now"] = T_AFTER
    batch = {i.claim_egif: i for i in src.fetch()}
    for kind in ("naive", "home", "strong", "fav"):
        item = batch[f'(win_{kind} "776001" "{HOME}")']
        assert item.happened and item.world_egif is None
    assert src.resolutions == 4
    assert src.resolutions_by_kind == {"naive": 1, "home": 1, "strong": 1, "fav": 1}


def test_miss_carries_the_law_refuting_shape():
    """The away team (the underdog) wins → each hit-side arm misses, and the miss
    arrives as body + negated head + the observed outcome — the shape the
    mechanical Challenger relinquishes a standing law over."""
    phase = {"final": False}
    games = lambda: [_game(state="Final", detailed="Final", home_winner=False,
                           away_winner=True)] if phase["final"] else [_game()]
    src, clock = _source(T0, games)
    src.fetch()
    phase["final"] = True
    clock["now"] = T_AFTER
    batch = {i.claim_egif: i for i in src.fetch()}
    item = batch[f'(win_naive "776001" "{HOME}")']
    assert not item.happened
    assert f'(pick_naive "776001" "{HOME}")' in item.world_egif
    assert f'~[ (win_naive "776001" "{HOME}") ]' in item.world_egif
    assert f'(won "776001" "{AWAY}")' in item.world_egif


def test_postponed_game_drops_counted():
    phase = {"post": False}
    games = lambda: [_game(detailed="Postponed")] if phase["post"] else [_game()]
    src, clock = _source(T0, games)
    src.fetch()
    phase["post"] = True
    clock["now"] = T_AFTER
    assert src.fetch() == []
    assert src.postponed_dropped == 4 and not src._pending
    assert src.unresolved_dropped == 0


def test_never_final_game_drops_counted_after_grace():
    src, clock = _source(T0, [_game()], grace_hours=6)
    src.fetch()
    clock["now"] = datetime(2026, 7, 13, 1, 0, tzinfo=timezone.utc)  # start+~7h
    assert src.fetch() == []
    assert src.unresolved_dropped == 4 and not src._pending


def test_within_grace_still_waits():
    src, clock = _source(T0, [_game()], grace_hours=12)
    src.fetch()
    clock["now"] = datetime(2026, 7, 12, 23, 0, tzinfo=timezone.utc)  # start+5h
    assert src.fetch() == []
    assert src.unresolved_dropped == 0 and len(src._pending) == 4


def test_state_round_trips_pending_and_cut(tmp_path):
    """Pending picks, counters, and the (possibly recalibrated) cut survive a
    save/load, and the resumed source resolves the carried claims."""
    phase = {"final": False}
    games = lambda: [_game(state="Final", detailed="Final", home_winner=True,
                           away_winner=False)] if phase["final"] else [_game()]
    fetch = _fixture_fetch(games)
    clock = {"now": T0}
    src = SportsSource(fetch_json=fetch, clock=lambda: clock["now"])
    src.fetch()
    src._cut = 125                                       # a mid-run recalibration
    sp = str(tmp_path / "ss.json")
    src.save_state(sp)

    phase["final"] = True
    src2 = SportsSource.load_state(sp, fetch_json=fetch, clock=lambda: T_AFTER)
    assert src2._cut == 125
    assert src2.claims_raised == 4 and len(src2._pending) == 4
    batch = src2.fetch()
    assert {i.claim_egif for i in batch} == {
        f'(win_{k} "776001" "{HOME}")' for k in ("naive", "home", "strong", "fav")}
    assert all(i.happened for i in batch)


def test_record_and_replay_round_trip(tmp_path):
    rp = str(tmp_path / "items.jsonl")
    phase = {"final": False}
    games = lambda: [_game(state="Final", detailed="Final", home_winner=True,
                           away_winner=False)] if phase["final"] else [_game()]
    clock = {"now": T0}
    src = SportsSource(fetch_json=_fixture_fetch(games), record_path=rp,
                       clock=lambda: clock["now"])
    b1 = src.fetch()
    phase["final"] = True
    clock["now"] = T_AFTER
    b2 = src.fetch()
    batches = replay_item_batches(rp)
    assert [[i.claim_egif for i in b] for b in batches] == [
        [i.claim_egif for i in b1], [i.claim_egif for i in b2]]


def test_standings_failure_degrades_gracefully():
    """A dead standings endpoint: naive/home still raise; strong/cal wait for the
    next poll — degraded and counted, never a crash."""
    def fetch(url):
        if "/standings" in url:
            raise RuntimeError("down")
        return _fixture_fetch([_game()])(url)
    src = SportsSource(fetch_json=fetch, clock=lambda: T0, sleep=lambda s: None)
    claims = {i.claim_egif for i in src.fetch()}
    assert f'(pick_naive "776001" "{HOME}")' in claims
    assert f'(pick_home "776001" "{HOME}")' in claims
    assert not any("strong" in c or "fav" in c or "dog" in c for c in claims)
    assert src.fetch_errors_by_endpoint == {"standings": 1}


def test_fetch_retry_recovers_with_injected_sleep():
    calls = {"n": 0}
    slept = []

    def flaky(url):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("503")
        return {"ok": 1}

    src = SportsSource(fetch_json=flaky, sleep=lambda s: slept.append(s),
                       fetch_tries=3, fetch_backoff=0.5)
    assert src._fetch_retry("u") == {"ok": 1}
    assert slept == [0.5, 1.0]
    assert src.fetch_errors == 0                        # a recovered retry is silent


# --- the run-12 headline: the knob-type causal pair (P1¹² / P2¹²) -------------

def _pair_batches(kind, results):
    """Per-game batches for one arm: a pick raise + a resolution per game.
    ``results`` = one bool per game (did the picked team win)."""
    from resolving_membrane import ResolvingItem
    batches = []
    for i, won in enumerate(results, 1):
        pk, team = f"g{i}", "Harbor Homers"
        batches.append([
            ResolvingItem(f'(pick_{kind} "{pk}" "{team}")', happened=True),
            ResolvingItem(
                f'(win_{kind} "{pk}" "{team}")', happened=won,
                world_egif=None if won else (
                    f'(pick_{kind} "{pk}" "{team}") '
                    f'~[ (win_{kind} "{pk}" "{team}") ] '
                    f'(won "{pk}" "Arch Astros")')),
        ])
    return batches


def _live_run(seed, batches, evaluate=None):
    from live_runner import LiveRunConfig, LiveRunner, ReplaySource
    from resolving_membrane import ResolvingFeed
    from agon_evolution import (
        Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent,
        ObserverAgent,
    )
    runner = LiveRunner(
        " ".join(seed), ReplaySource(batches), ResolvingFeed,
        LiveRunConfig(ttl=None, checkpoint=False, state_path=None),
        uod_id="s", seed_laws=list(seed),
        panel=Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                           ContradictionAgent()]),
        evaluate=evaluate, clock=lambda: 0.0, sleep=lambda s: None)
    return runner


def test_P1_arm_A_no_knob_is_refuted_and_falls_silent():
    """The knob-type null (P1¹²): the naive law loses its first bet, the world
    relinquishes it (challenge_to_M), and — with no knob and no reseed — every
    later bet is an abstention. Refuted and silent: the run-10 trap shape, now in
    a domain with no width to widen."""
    bets = []

    def evaluate(feed, res):
        bets.extend(e for e in feed.ledger.entries
                    if not e.claim_egif.lstrip().startswith("(pick_"))
        return {}

    runner = _live_run([LAW_NAIVE],
                          _pair_batches("naive", [False, True, True, True]),
                          evaluate=evaluate)
    res = runner.run()
    assert res.stopped_because == "source_exhausted"
    assert [e.result for e in bets] == ["miss", "abstain", "abstain", "abstain"]
    assert bets[0].predicted == "true"                  # M genuinely bet, once
    assert not any(LAW_NAIVE.strip() == l.strip() for l in runner._laws)
    assert sum(1 for e in bets if e.result == "hit") == 0   # it NEVER recovers


def test_P2_arm_B_the_manufactured_knob_recovers():
    """The headline causal pair's other half (P2¹²): same refute-first world, but
    the calibrated arm's evaluate hook recalibrates (cut moves on evidence) and
    reseeds the fallen law through the runner's ``reseed_laws`` seam — so the next
    segment BETS AGAIN and scores hits. Refute → recalibrate → re-bet → hit."""
    from resolving_membrane import PredictionLedger
    from sports_recalibration import recalibrate

    run_ledger = PredictionLedger()
    cuts = [50]

    def evaluate(feed, res):
        run_ledger.entries.extend(
            e for e in feed.ledger.entries
            if not e.claim_egif.lstrip().startswith("(pick_"))
        rc = recalibrate(run_ledger, cut=cuts[-1],
                         standing_laws=list(runner._laws), hold_laws=[])
        if rc.changed:
            cuts.append(rc.cut)
        return {"reseed_laws": rc.reseed_laws}

    runner = _live_run([LAW_FAV, LAW_DOG],
                          _pair_batches("fav", [False, True, True, True]),
                          evaluate=evaluate)
    res = runner.run()
    assert res.stopped_because == "source_exhausted"
    results = [e.result for e in run_ledger.entries]
    assert results[0] == "miss"                          # refuted first
    assert "hit" in results[1:]                          # …and it BETS AGAIN and hits
    assert run_ledger.hits >= 2
    assert any(LAW_FAV.strip() == l.strip() for l in runner._laws)  # reseeded, standing
    assert cuts[-1] > 50                                 # the cut moved on evidence


def test_select_best_ranks_rival_theories_over_the_same_games():
    """Arm C's register (P3¹²): three theories scored over the same games — the
    strong rival out-predicts home, and the silent naive arm ranks last."""
    from resolving_membrane import PredictionLedger, ResolvingItem, select_best

    def ledger(kind, results):
        led = PredictionLedger()
        for i, r in enumerate(results):
            predicted = "unknown" if r is None else "true"
            led.record(ResolvingItem(f'(win_{kind} "g{i}" "T")',
                                     happened=bool(r)), predicted, i)
        return led

    strong = ledger("strong", [True, True, True, True, False])      # net +3
    home = ledger("home", [True, False, True, False, True])         # net +1
    naive = ledger("naive", [False, None, None, None, None])        # net −1, silent
    arms = [("home", home), ("strong", strong), ("naive", naive)]
    assert select_best(arms) == "strong"
    assert select_best([("home", home), ("naive", naive)]) == "home"


def test_seed_laws_cover_all_arms_and_held_laws_are_the_rivals():
    assert SEED_LAWS == [LAW_NAIVE, LAW_HOME, LAW_STRONG, LAW_FAV, LAW_DOG]
    assert HELD_LAWS == [LAW_HOME, LAW_STRONG]
    assert LAW_NAIVE not in HELD_LAWS                    # the null is never held
