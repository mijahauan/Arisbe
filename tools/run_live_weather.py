"""Live weather sessions against the automated Endoporeutic Game — the first
**resolving-membrane** run (docs/AUTOMATED_ENDOPOREUTIC_GAME.md §18, run 7).

NWS hourly forecasts are raised as claims; observations resolve them. M is seeded with
the naive theory *"what is forecast, happens"* (one law per claim kind), bets through
the open-world peel, and is scored by the world: hits/misses in the
``PredictionLedger``, and a miss arriving in the law-refuting shape lets the mechanical
Challenger relinquish the over-general law — the registers the wiki stream never
exercised, live. Findings are about the game (and NWS forecasts as represented), never
the world. Usage:

    uv run python tools/run_live_weather.py --runs-dir runs/run7 --max-seconds 50400

Controls mirror tools/run_live_wikidata.py: side-store checkpoints, per-segment state
(+ pending claims in weather_state.json) for --resume, recorded item batches for the
offline replay canary, STOP file, supervisor auto-resume, checkpoint cadence.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import (
    Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent, ObserverAgent,
)
from live_runner import LiveRunConfig, LiveRunner, _sheet_atom_count
from resolving_membrane import PredictionLedger, ResolvingFeed
from tomos_service import TomosService
from weather_recalibration import recalibrate
from weather_source import DEFAULT_STATIONS, SEED_LAWS, WeatherSource


def _panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


def _arm_of(claim_egif: str):
    """The claim arm of a resolution entry ("temp" | "precip"), or None for a
    raise-phase (forecast_…) item (never scored as a bet)."""
    s = claim_egif.lstrip()
    if s.startswith("(temp_band"):
        return "temp"
    if s.startswith("(precip"):
        return "precip"
    return None


def _per_arm(ledger):
    """Per-arm hits/misses/abstentions/net over a ledger's resolution bets (F3⁸)."""
    tally = {"temp": [0, 0, 0], "precip": [0, 0, 0]}  # hits, misses, abstains
    idx = {"hit": 0, "miss": 1, "abstain": 2}
    for e in ledger.entries:
        arm = _arm_of(e.claim_egif)
        if arm is not None and e.result in idx:
            tally[arm][idx[e.result]] += 1
    return tally


def _fmt_arm(arm, t, src):
    h, m, a = t
    raised = src.claims_raised_by_kind.get(arm, 0)
    resolved = src.resolutions_by_kind.get(arm, 0)
    return (f"{arm}: raised={raised} resolved={resolved} "
            f"{h}h/{m}m/{a}a net={h - m}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stations", nargs="+", default=list(DEFAULT_STATIONS),
                    metavar="ICAO", help="METAR stations (must be in the built-in table "
                                         "or given as ICAO:lat:lon)")
    ap.add_argument("--horizon-hours", type=int, default=6)
    ap.add_argument("--grace-hours", type=int, default=3)
    ap.add_argument("--band-width", type=int, default=5,
                    help="temperature band width, °F — the claim discretization")
    ap.add_argument("--pop-threshold", type=int, default=60,
                    help="probability-of-precipitation %% at/above which a precip claim is raised")
    # Run 9 (F2⁸): forecast-centered bins. "grid" = the run-7/8 fixed-grid bins
    # (a forecast near a bin edge is fragile); "centered" = the band is centered
    # on the forecast, so a miss needs |obs−forecast| > band/2 — testing whether
    # the sharper discretization converts the F2⁸ limit cycle to a fixed point.
    ap.add_argument("--bin-mode", choices=("grid", "centered"), default="grid",
                    help="temperature-band discretization (run 9: centered)")
    # F1⁷: bounded retry/backoff around the flaky NWS endpoints.
    ap.add_argument("--fetch-tries", type=int, default=3,
                    help="bounded retries per NWS fetch (F1⁷)")
    ap.add_argument("--fetch-backoff", type=float, default=0.5,
                    help="base backoff seconds between fetch retries (doubles each try)")
    # Run 8: predict→refute→re-generalize. After a law is relinquished, widen its
    # discretization (temp band / PoP threshold) from the ledger track record and
    # re-seed it, so the game bets again instead of falling silent (F2⁷).
    ap.add_argument("--regenerate", action="store_true",
                    help="enable re-generalization of relinquished/under-performing laws")
    ap.add_argument("--regen-target", type=float, default=0.6,
                    help="reliability target below which a standing law is recalibrated")
    ap.add_argument("--band-cap", type=int, default=20, help="max temperature band width (°F)")
    ap.add_argument("--pop-cap", type=int, default=90, help="max PoP threshold (%%)")
    ap.add_argument("--ttl", type=int, default=48, help="disuse-decay ttl (polls)")
    ap.add_argument("--segment-cap", type=int, default=25)
    ap.add_argument("--checkpoint-every", type=int, default=1)
    ap.add_argument("--min-interval", type=float, default=600.0,
                    help="seconds between polls (NWS etiquette; obs update ~5–20 min)")
    ap.add_argument("--max-seconds", type=float, default=50400.0)
    ap.add_argument("--max-rounds", type=int, default=None)
    ap.add_argument("--max-m", type=int, default=400)
    ap.add_argument("--max-m-atoms", type=int, default=2000)
    ap.add_argument("--max-crashes", type=int, default=50)
    ap.add_argument("--runs-dir", default="runs/run7")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    stations = {}
    for s in args.stations:
        if ":" in s:
            sid, lat, lon = s.split(":")
            stations[sid] = (float(lat), float(lon))
        elif s in DEFAULT_STATIONS:
            stations[s] = DEFAULT_STATIONS[s]
        else:
            raise SystemExit(f"unknown station {s!r} — give ICAO:lat:lon")

    runs = Path(args.runs_dir)
    (runs / "checkpoints").mkdir(parents=True, exist_ok=True)
    state_path = str(runs / "state.json")
    weather_state = str(runs / "weather_state.json")

    # RUN_9_LOG F3⁹: the per-segment digest (bets, dispositions, reseed count,
    # per-station errors, poise) and the final report go to stdout — tee them to a
    # file so the stream is a first-class replayable artifact, not lost with the
    # terminal. Append (a resume continues the same log), flush per line.
    _console = open(runs / "console.txt", "a", encoding="utf-8", buffering=1)

    class _Tee:
        def __init__(self, *streams):
            self._streams = streams

        def write(self, s):
            for st in self._streams:
                st.write(s)
                st.flush()

        def flush(self):
            for st in self._streams:
                st.flush()

    sys.stdout = _Tee(sys.__stdout__, _console)
    stop_file = str(runs / "STOP")

    config = LiveRunConfig(
        ttl=args.ttl, ttl_unit="polls", segment_cap=args.segment_cap,
        min_interval_s=args.min_interval,
        max_rounds=args.max_rounds, max_seconds=args.max_seconds,
        max_m_relations=args.max_m, max_m_atoms=args.max_m_atoms, stop_file=stop_file,
        checkpoint=True, checkpoint_refusal="skip",
        checkpoint_every=args.checkpoint_every, state_path=state_path,
    )
    service = TomosService(runs / "checkpoints")
    uod_id = runs.name or "weather"

    # The run-level track record (feeds are per-segment; this accumulates).
    run_ledger = PredictionLedger()

    src_kwargs = dict(stations=stations, horizon_hours=args.horizon_hours,
                      grace_hours=args.grace_hours, band_width=args.band_width,
                      pop_threshold=args.pop_threshold, bin_mode=args.bin_mode,
                      fetch_tries=args.fetch_tries, fetch_backoff=args.fetch_backoff,
                      record_path=str(runs / "items.jsonl"))
    # Run-level re-generalization tally (surfaced in the final report).
    regen_count = {"n": 0}

    def build(resume: bool):
        if resume and Path(weather_state).exists():
            source = WeatherSource.load_state(weather_state, **src_kwargs)
            print(f"resuming: pending claims restored from {weather_state}", flush=True)
        else:
            source = WeatherSource(**src_kwargs)

        def evaluate(feed, res):
            source.save_state(weather_state)
            from collections import Counter
            dispositions = dict(Counter(o.disposition for o in res.outcomes
                                        if o.disposition))
            # Fold this segment's forecasts into the run ledger — RESOLUTION claims
            # only (forecast-arrival items, claim prefix "(forecast_", are raise-phase
            # bookkeeping, not bets).
            seg_bets = [e for e in feed.ledger.entries
                        if not e.claim_egif.startswith("(forecast_")]
            run_ledger.entries.extend(seg_bets)
            atoms = _sheet_atom_count(res.uod.current_egi)
            bets = (f" bets={len(seg_bets)} (run: {run_ledger.hits}h/"
                    f"{run_ledger.misses}m/{run_ledger.abstentions}a "
                    f"net={run_ledger.net_score})") if seg_bets else ""

            # Run 8: re-generalize a relinquished/under-performing law from the
            # run-level track record — widen its discretization + re-seed it (the
            # runner re-scribes reseed_laws onto M). Off by default (run-7 parity).
            reseed: list = []
            if args.regenerate:
                rc = recalibrate(
                    run_ledger, band_width=source._width, pop_threshold=source._pop,
                    standing_laws=list(getattr(runner, "_laws", [])),
                    target=args.regen_target, band_cap=args.band_cap, pop_cap=args.pop_cap)
                if rc.changed:
                    source._width, source._pop = rc.band_width, rc.pop_threshold
                    reseed = rc.reseed_laws
                    regen_count["n"] += 1
                    print(f"    re-generalize: band={rc.band_width}°F pop≥{rc.pop_threshold}%"
                          f" reseed={len(reseed)} — {'; '.join(rc.notes)}", flush=True)

            # F1⁷: surface per-station error rates so a dark station is visible.
            dark = " ".join(f"{st}:{n}" for st, n in sorted(
                source.fetch_errors_by_station.items()) if n)
            print(f"  segment: rounds={len(res.outcomes)} atoms={atoms} "
                  f"dispositions={dispositions}{bets}"
                  + (f" claims={source.claims_raised} resolved={source.resolutions}"
                     f" dropped={source.unresolved_dropped}")
                  + (f" ⚠ fetch_errors={source.fetch_errors} [{dark}]"
                     if source.fetch_errors else ""), flush=True)
            # F3⁸: per-arm bet counts, disambiguating a dormant arm (few
            # resolutions) from a well-calibrated one (many resolutions, all hits).
            arm_tally = _per_arm(run_ledger)
            print("    per-arm (run): "
                  + " | ".join(_fmt_arm(a, arm_tally[a], source)
                               for a in ("temp", "precip")), flush=True)
            return {"bets": len(seg_bets), "net": run_ledger.net_score,
                    "reseed_laws": reseed}

        if resume:
            runner = LiveRunner.resume(state_path, source, ResolvingFeed, config,
                                       uod_id=uod_id, panel=_panel(),
                                       evaluate=evaluate, service=service,
                                       sleep=time.sleep)
        else:
            runner = LiveRunner(" ".join(SEED_LAWS), source, ResolvingFeed, config,
                                uod_id=uod_id, seed_laws=list(SEED_LAWS),
                                panel=_panel(), evaluate=evaluate, service=service,
                                sleep=time.sleep)
        return source, runner

    deadline = (time.monotonic() + args.max_seconds) if args.max_seconds else None
    resume = args.resume
    crashes = 0
    res = None
    print(f"run start {time.strftime('%Y-%m-%d %H:%M:%S')} — NWS resolving membrane · "
          f"stations={sorted(stations)} · horizon={args.horizon_hours}h · "
          f"band={args.band_width}°F ({args.bin_mode}) · pop≥{args.pop_threshold}% · "
          f"ttl={args.ttl} polls · "
          f"pacing={args.min_interval}s · laws seeded: what-is-forecast-happens · "
          f"regenerate={'on' if args.regenerate else 'off'} · "
          f"stop: touch {stop_file}", flush=True)

    while True:
        if deadline is not None:
            config.max_seconds = max(1.0, deadline - time.monotonic())
        source, runner = build(resume)
        try:
            res = runner.run()
            break
        except KeyboardInterrupt:
            raise
        except Exception:
            import traceback
            crashes += 1
            traceback.print_exc()
            if crashes > args.max_crashes:
                print(f"supervisor: crash budget exhausted ({crashes})", flush=True)
                raise
            if deadline is not None and time.monotonic() >= deadline - 60:
                print("supervisor: crash at the deadline — stopping", flush=True)
                break
            resume = Path(state_path).exists()
            print(f"supervisor: crash #{crashes} — "
                  + ("resuming" if resume else "restarting fresh") + " in 10 s",
                  flush=True)
            time.sleep(10)

    if res is None:
        print(f"\nstopped: crash_at_deadline   crashes survived: {crashes}")
        return 1

    print(f"\nstopped: {res.stopped_because}   total rounds: {res.total_rounds}"
          + (f"   crashes survived: {crashes}" if crashes else ""))
    print(f"ledger (run-level, resolutions only): {run_ledger.hits} hits · "
          f"{run_ledger.misses} misses · {run_ledger.abstentions} abstentions · "
          f"net {run_ledger.net_score} · accuracy "
          f"{run_ledger.accuracy if run_ledger.accuracy is not None else '—'}")
    by_st = " ".join(f"{st}:{n}" for st, n in sorted(
        source.fetch_errors_by_station.items()) if n) or "none"
    print(f"claims: raised={source.claims_raised} resolved={source.resolutions} "
          f"dropped_unresolved={source.unresolved_dropped} "
          f"fetch_errors={source.fetch_errors} (per-station: {by_st})")
    arm_tally = _per_arm(run_ledger)
    print("per-arm (run-level, F3⁸):")
    for a in ("temp", "precip"):
        print("  " + _fmt_arm(a, arm_tally[a], source))
    if args.regenerate:
        print(f"re-generalizations: {regen_count['n']}")
    final_laws = getattr(runner, "_laws", [])
    print("laws still standing: " + (" · ".join(final_laws) if final_laws
                                     else "(none — every seeded theory was relinquished)"))
    if res.segments:
        from agon_metalearning import poise_from_digests
        strip = " ".join("●" if w.poised else ("○" if w.failure == "rigidity" else "✕")
                         for w in poise_from_digests(res.segments))
        print(f"poise per segment: {strip}")
    print(f"\nartifacts: {runs}/items.jsonl (offline replay) · {runs}/checkpoints · "
          f"log dispositions in the run's RUN_N_LOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
