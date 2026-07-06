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
from weather_source import DEFAULT_STATIONS, SEED_LAWS, WeatherSource


def _panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


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
                      pop_threshold=args.pop_threshold,
                      record_path=str(runs / "items.jsonl"))

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
            print(f"  segment: rounds={len(res.outcomes)} atoms={atoms} "
                  f"dispositions={dispositions}{bets}"
                  + (f" claims={source.claims_raised} resolved={source.resolutions}"
                     f" dropped={source.unresolved_dropped}")
                  + (f" ⚠ fetch_errors={source.fetch_errors}"
                     if source.fetch_errors else ""), flush=True)
            return {"bets": len(seg_bets), "net": run_ledger.net_score}

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
          f"band={args.band_width}°F · pop≥{args.pop_threshold}% · ttl={args.ttl} polls · "
          f"pacing={args.min_interval}s · laws seeded: what-is-forecast-happens · "
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
    print(f"claims: raised={source.claims_raised} resolved={source.resolutions} "
          f"dropped_unresolved={source.unresolved_dropped} "
          f"fetch_errors={source.fetch_errors}")
    final_laws = getattr(runner, "_laws", [])
    print("laws still standing: " + (" · ".join(final_laws) if final_laws
                                     else "(none — every seeded theory was relinquished)"))
    if res.segments:
        from agon_metalearning import poise_from_digests
        strip = " ".join("●" if w.poised else ("○" if w.failure == "rigidity" else "✕")
                         for w in poise_from_digests(res.segments))
        print(f"poise per segment: {strip}")
    print(f"\nartifacts: {runs}/items.jsonl (offline replay) · {runs}/checkpoints · "
          f"log dispositions in runs/RUN_7_LOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
