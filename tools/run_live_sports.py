"""Live MLB sessions against the automated Endoporeutic Game — run 12, the
**discrete** resolving membrane (runs/RUN_12_LOG.md, pre-registered 2026-07-12).

Scheduled games are raised as picks (one per arm: naive-home null / held rivals
home + win-pct / the calibrated win-pct-differential cut); finals resolve them. M is
seeded with all the arm theories, bets through the open-world peel, and is scored by
the world: hits/misses in the ``PredictionLedger``; a miss arriving in the
law-refuting shape lets the mechanical Challenger relinquish the over-general law.
Per segment the driver prints per-arm tallies, the cut trajectory, and the
``select_best`` standings (arm C — the first *live* theory-selection register).
Findings are about the game (and MLB data as represented), never the world. Usage:

    uv run python tools/run_live_sports.py --runs-dir runs/run12 --regenerate \
        --max-seconds 259200

Controls mirror tools/run_live_weather.py: console tee, side-store checkpoints,
per-segment state (+ pending picks and the learned cut in sports_state.json) for
--resume, recorded item batches for the offline replay canary, STOP file,
supervisor auto-resume, checkpoint cadence. Cadence note (ops): sports resolve in
**calendar bursts** (a nightly batch), so pacing defaults to 1800 s and a 2–3 day
window; a 14 h run spans only one game day.
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
from resolving_membrane import PredictionLedger, ResolvingFeed, select_best
from sports_recalibration import recalibrate
from sports_source import SEED_LAWS, SportsSource
from tomos_service import TomosService


def _panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


# The reporting arms; arm B's fav/dog directions fold into "cal".
ARMS = ("naive", "home", "strong", "cal")


def _arm_of(claim_egif: str):
    """The claim arm of a resolution entry, or None for a raise-phase (pick_…)
    item (never scored as a bet)."""
    s = claim_egif.lstrip()
    if s.startswith("(win_naive"):
        return "naive"
    if s.startswith("(win_home"):
        return "home"
    if s.startswith("(win_strong"):
        return "strong"
    if s.startswith("(win_fav") or s.startswith("(win_dog"):
        return "cal"
    return None


def _per_arm(ledger):
    """Per-arm hits/misses/abstentions over a ledger's resolution bets."""
    tally = {a: [0, 0, 0] for a in ARMS}
    idx = {"hit": 0, "miss": 1, "abstain": 2}
    for e in ledger.entries:
        arm = _arm_of(e.claim_egif)
        if arm is not None and e.result in idx:
            tally[arm][idx[e.result]] += 1
    return tally


def _fmt_arm(arm, t, src):
    h, m, a = t
    kinds = ("fav", "dog") if arm == "cal" else (arm,)
    raised = sum(src.claims_raised_by_kind.get(k, 0) for k in kinds)
    resolved = sum(src.resolutions_by_kind.get(k, 0) for k in kinds)
    return (f"{arm}: raised={raised} resolved={resolved} "
            f"{h}h/{m}m/{a}a net={h - m}")


def _arm_ledgers(ledger):
    """Slice the run ledger into per-theory ledgers — arm C's ``select_best``
    input (each theory's world-scored track record over the same games)."""
    arms = []
    for a in ARMS:
        led = PredictionLedger(
            entries=[e for e in ledger.entries if _arm_of(e.claim_egif) == a])
        arms.append((a, led))
    return arms


def _standings_lines(ledger):
    """The select_best ranking, one line per theory (winner first)."""
    arms = _arm_ledgers(ledger)

    def key(arm):
        _label, led = arm
        acc = led.accuracy if led.accuracy is not None else 0.0
        return (led.net_score, acc, -(led.hits + led.misses))

    winner = select_best(arms)
    lines = []
    for label, led in sorted(arms, key=key, reverse=True):
        acc = "—" if led.accuracy is None else f"{led.accuracy:.3f}"
        mark = " ◄ select_best" if label == winner else ""
        lines.append(f"{label}: net={led.net_score} acc={acc} "
                     f"({led.hits}h/{led.misses}m/{led.abstentions}a){mark}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--horizon-hours", type=int, default=18,
                    help="raise picks for games starting within this window")
    ap.add_argument("--grace-hours", type=int, default=12,
                    help="drop a started-but-never-final game counted after this")
    ap.add_argument("--cut", type=int, default=50,
                    help="arm B's initial win-pct-differential cutpoint "
                         "(thousandths): >= bets the favorite, < the underdog")
    ap.add_argument("--cut-step", type=int, default=25,
                    help="recalibration step for the cut (thousandths)")
    ap.add_argument("--cut-cap", type=int, default=300,
                    help="max cut (thousandths); the floor is 0 = always-favorite")
    ap.add_argument("--window", type=int, default=30,
                    help="recent-bet window the recalibrator reads")
    ap.add_argument("--fetch-tries", type=int, default=3,
                    help="bounded retries per MLB fetch")
    ap.add_argument("--fetch-backoff", type=float, default=0.5,
                    help="base backoff seconds between fetch retries (doubles each try)")
    # Run 12 arm B: predict→refute→re-generalize. Off = every arm is a null
    # (nothing recalibrates or reseeds — every law falls silent on its first miss).
    ap.add_argument("--regenerate", action="store_true",
                    help="enable the arm-B cut recalibration + reseed and the "
                         "arm-C rival holds (the pre-registered configuration)")
    ap.add_argument("--ttl", type=int, default=48, help="disuse-decay ttl (polls)")
    ap.add_argument("--segment-cap", type=int, default=25)
    ap.add_argument("--checkpoint-every", type=int, default=1)
    ap.add_argument("--min-interval", type=float, default=1800.0,
                    help="seconds between polls (bursty nightly resolution — "
                         "sub-hourly polling buys nothing)")
    ap.add_argument("--max-seconds", type=float, default=259200.0,
                    help="default 3 days — one game day is too short a sample")
    ap.add_argument("--max-rounds", type=int, default=None)
    ap.add_argument("--max-m", type=int, default=400)
    ap.add_argument("--max-m-atoms", type=int, default=2000)
    ap.add_argument("--max-crashes", type=int, default=50)
    ap.add_argument("--runs-dir", default="runs/run12")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    runs = Path(args.runs_dir)
    (runs / "checkpoints").mkdir(parents=True, exist_ok=True)
    state_path = str(runs / "state.json")
    sports_state = str(runs / "sports_state.json")

    # F3⁹: tee the digest stream to console.txt — a first-class replayable
    # artifact, not lost with the terminal. Append (a resume continues the log).
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
    uod_id = runs.name or "sports"

    # The run-level track record (feeds are per-segment; this accumulates).
    run_ledger = PredictionLedger()

    src_kwargs = dict(horizon_hours=args.horizon_hours, grace_hours=args.grace_hours,
                      cut=args.cut, fetch_tries=args.fetch_tries,
                      fetch_backoff=args.fetch_backoff,
                      record_path=str(runs / "items.jsonl"))
    seed_laws = list(SEED_LAWS)
    regen_count = {"n": 0}

    def build(resume: bool):
        if resume and Path(sports_state).exists():
            source = SportsSource.load_state(sports_state, **src_kwargs)
            print(f"resuming: pending picks + cut restored from {sports_state}",
                  flush=True)
        else:
            source = SportsSource(**src_kwargs)

        def evaluate(feed, res):
            source.save_state(sports_state)
            from collections import Counter
            dispositions = dict(Counter(o.disposition for o in res.outcomes
                                        if o.disposition))
            # RESOLUTION claims only — pick_… items are raise-phase bookkeeping.
            seg_bets = [e for e in feed.ledger.entries
                        if not e.claim_egif.lstrip().startswith("(pick_")]
            run_ledger.entries.extend(seg_bets)
            atoms = _sheet_atom_count(res.uod.current_egi)
            bets = (f" bets={len(seg_bets)} (run: {run_ledger.hits}h/"
                    f"{run_ledger.misses}m/{run_ledger.abstentions}a "
                    f"net={run_ledger.net_score})") if seg_bets else ""

            # Arm B's knob + arm C's holds — the pre-registered mechanism.
            reseed: list = []
            if args.regenerate:
                rc = recalibrate(
                    run_ledger, cut=source._cut,
                    standing_laws=list(getattr(runner, "_laws", [])),
                    window=args.window, cut_step=args.cut_step,
                    cut_cap=args.cut_cap)
                if rc.changed:
                    source._cut = rc.cut
                    reseed = rc.reseed_laws
                    regen_count["n"] += 1
                    print(f"    re-generalize: cut={rc.cut} "
                          f"reseed={len(reseed)} — {'; '.join(rc.notes)}",
                          flush=True)

            errs = " ".join(f"{ep}:{n}" for ep, n in sorted(
                source.fetch_errors_by_endpoint.items()) if n)
            print(f"  segment: rounds={len(res.outcomes)} atoms={atoms} "
                  f"dispositions={dispositions}{bets}"
                  + (f" picks={source.claims_raised} resolved={source.resolutions}"
                     f" dropped={source.unresolved_dropped}"
                     f" postponed={source.postponed_dropped} cut={source._cut}")
                  + (f" ⚠ fetch_errors={source.fetch_errors} [{errs}]"
                     if source.fetch_errors else ""), flush=True)
            arm_tally = _per_arm(run_ledger)
            print("    per-arm (run): "
                  + " | ".join(_fmt_arm(a, arm_tally[a], source) for a in ARMS),
                  flush=True)
            # Arm C: the live theory-selection standings (P3¹²).
            print("    select_best standings: "
                  + " | ".join(_standings_lines(run_ledger)), flush=True)
            return {"bets": len(seg_bets), "net": run_ledger.net_score,
                    "cut": source._cut, "reseed_laws": reseed}

        if resume:
            runner = LiveRunner.resume(state_path, source, ResolvingFeed, config,
                                       uod_id=uod_id, panel=_panel(),
                                       evaluate=evaluate, service=service,
                                       sleep=time.sleep)
        else:
            runner = LiveRunner(" ".join(seed_laws), source, ResolvingFeed, config,
                                uod_id=uod_id, seed_laws=list(seed_laws),
                                panel=_panel(), evaluate=evaluate, service=service,
                                sleep=time.sleep)
        return source, runner

    deadline = (time.monotonic() + args.max_seconds) if args.max_seconds else None
    resume = args.resume
    crashes = 0
    res = None
    print(f"run start {time.strftime('%Y-%m-%d %H:%M:%S')} — MLB resolving membrane "
          f"(run 12, discrete) · horizon={args.horizon_hours}h · "
          f"grace={args.grace_hours}h · cut={args.cut} "
          f"(step {args.cut_step}, cap {args.cut_cap}) · ttl={args.ttl} polls · "
          f"pacing={args.min_interval}s · arms: naive-null / home+win-pct rivals / "
          f"calibrated cut · regenerate={'on' if args.regenerate else 'off'} · "
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
    by_ep = " ".join(f"{ep}:{n}" for ep, n in sorted(
        source.fetch_errors_by_endpoint.items()) if n) or "none"
    print(f"picks: raised={source.claims_raised} resolved={source.resolutions} "
          f"dropped_unresolved={source.unresolved_dropped} "
          f"postponed={source.postponed_dropped} "
          f"fetch_errors={source.fetch_errors} (per-endpoint: {by_ep})")
    arm_tally = _per_arm(run_ledger)
    print("per-arm (run-level):")
    for a in ARMS:
        print("  " + _fmt_arm(a, arm_tally[a], source))
    print("select_best standings (final, P3¹²):")
    for line in _standings_lines(run_ledger):
        print("  " + line)
    print(f"final cut: {source._cut} (seeded {args.cut})")
    # P4¹²: the external-literature check — home-win rate vs the documented ≈53–54%.
    home = _per_arm(run_ledger)["home"]
    decided = home[0] + home[1]
    if decided:
        print(f"home-win rate over decided home-rival bets: "
              f"{home[0] / decided:.3f} over {decided} "
              f"(literature: ≈0.53–0.54 — P4¹²)")
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
          f"log dispositions in runs/RUN_12_LOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
