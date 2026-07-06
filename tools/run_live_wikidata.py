"""Live Wikidata sessions against the automated Endoporeutic Game
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md §10 operating layer + §11/§12 pre-registrations).

Two sources, chosen by --source:
  * frontier (run 1)      — the rotating entity crawl (seeds → crawled Q-ids)
  * recentchanges (run 2) — the change stream: poll which items were just edited and fetch
    those, so the sample skews to live contestation and an edited entity is *revisited*
    (a deprecation arrives while the bare value it overturns still stands in M — the
    RUN_1_LOG F2/F3 findings made operational)

Plus the §13 tropism (--warm-fraction, default 0.5): each poll's chunk mixes warm re-reaches
of the entities backing M's standing facts (decay-adjacent first) with fresh ids — the
directed re-engagement runs 1–2 showed no passive membrane supplies. Composes with either
source (run 3 = crawl + tropism; run 4 = stream + tropism, the §14 F2″ composition:
revisit × world-motion). --warm-fraction 0 reproduces the passive baseline.

Usage (run 4):

    uv run python tools/run_live_wikidata.py --source recentchanges --runs-dir runs/run4 \\
        --max-seconds 3600

Either source → WikiDisputeFeed → LiveRunner, with every §11 control armed:

  * checkpoints to a **side store** (``<runs-dir>/checkpoints`` — never the main corpus);
  * ``state.json`` + ``frontier.json`` so a killed process resumes with ``--resume``
    (the decay clock and the crawl both continue, not reset);
  * every poll **recorded** to ``polls.jsonl`` — the run replays offline afterward
    (``WikidataSource(replay_polls(...))``, the determinism canary);
  * pacing, ``--max-seconds``/``--max-rounds``, and a STOP file for a clean halt;
  * per-segment console digests (dispositions, |M|, decay, legibility, poise) and a final
    §6 summary (mechanism principles + the poise strip) for the run log.

Usage (supervised first hour per §11, then leave it running):

    uv run python tools/run_live_wikidata.py --seeds Q42 Q7259 Q937 --max-seconds 3600
    uv run python tools/run_live_wikidata.py --source recentchanges --runs-dir runs/run2 \
        --max-seconds 3600
    touch runs/run1/STOP                                  # clean stop
    uv run python tools/run_live_wikidata.py --resume     # continue after a kill/stop

Record findings in runs/RUN_<n>_LOG.md against the pre-registered priors.
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
from tomos_service import TomosService
from tropism import WarmSetTropism
from wiki_dispute_membrane import WikiDisputeFeed
from wikidata_source import RecentChangesSource, RotatingWikidataSource

DEFAULT_SEEDS = ["Q42", "Q7259", "Q937"]   # Douglas Adams, Ada Lovelace, Albert Einstein


def _panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["frontier", "recentchanges"], default="frontier",
                    help="frontier = the rotating crawl (run 1); recentchanges = the change "
                         "stream (run 2 — live contestation + natural revisits)")
    ap.add_argument("--seeds", nargs="+", default=DEFAULT_SEEDS, metavar="QID",
                    help="frontier source only")
    ap.add_argument("--chunk", type=int, default=8, help="entity ids per poll")
    ap.add_argument("--frontier-cap", type=int, default=400)
    ap.add_argument("--per-entity-cap", type=int, default=25,
                    help="max statements taken per entity per poll — bounds M's hub degree, "
                         "which the checkpoint attest's ligature routing is super-linear in "
                         "(0 = uncapped; drops are counted, never silent)")
    ap.add_argument("--no-crawl", action="store_true",
                    help="poll only the seeds (no frontier growth)")
    ap.add_argument("--warm-fraction", type=float, default=0.5,
                    help="fraction of each poll's chunk re-reached from M's warm set — the "
                         "§13 tropism (run 3: crawl + tropism at 0.5; run 4: stream + "
                         "tropism — the F2″ composition, revisit × world-motion). 0 = off, "
                         "the runs-1/2 passive baseline")
    ap.add_argument("--docket", action="store_true",
                    help="arm the docket of doubts (§15 increment 2a): thin spots of M "
                         "(rare relations, lonely individuals) become Q1 re-reaches riding "
                         "the same inject seam as the tropism; open/resolved/inexpressible "
                         "counted per segment, never silently dropped")
    ap.add_argument("--docket-asks", type=int, default=2,
                    help="docket Q1 asks emitted per poll (the articulate stratum's budget)")
    ap.add_argument("--ttl", type=int, default=30,
                    help="disuse-decay ttl, denominated by --ttl-unit")
    ap.add_argument("--ttl-unit", choices=["rounds", "polls"], default="rounds",
                    help="the habit clock (RUN_5 F2⁵): 'rounds' collapsed to a ~2 s memory once "
                         "rounds became ~free; 'polls' counts engagement opportunities, so a "
                         "warm-re-reached target persists across poll gaps at any throughput. "
                         "A state file is only resumable under the unit that wrote it")
    ap.add_argument("--max-crashes", type=int, default=50,
                    help="supervisor budget: auto-resume after an in-run crash up to this many "
                         "times (RUN_5 F1⁵ — one unlucky roll must not end an unattended run)")
    ap.add_argument("--segment-cap", type=int, default=25)
    ap.add_argument("--checkpoint-every", type=int, default=1,
                    help="checkpoint (save a browsable UoD, layout+§3.3-attested) every Nth "
                         "segment — RUN_5 F2ᵇ: at the persistent-M steady state the attest "
                         "dominates segment cost; digests/episodes/resume-state stay "
                         "per-segment regardless")
    ap.add_argument("--min-interval", type=float, default=5.0,
                    help="min seconds between polls (API politeness)")
    ap.add_argument("--max-seconds", type=float, default=3600.0)
    ap.add_argument("--max-rounds", type=int, default=None)
    ap.add_argument("--max-m", type=int, default=200, help="safety net on |M| (relation names)")
    ap.add_argument("--max-m-atoms", type=int, default=1000,
                    help="safety net on sheet ATOMS — the F1″ unit (decay bounds names, not "
                         "atoms; under tropism hub names accumulate atoms while |M| reads flat)")
    ap.add_argument("--runs-dir", default="runs/run1")
    ap.add_argument("--resume", action="store_true",
                    help="continue from the state files in --runs-dir")
    args = ap.parse_args(argv)

    runs = Path(args.runs_dir)
    (runs / "checkpoints").mkdir(parents=True, exist_ok=True)
    state_path = str(runs / "state.json")
    frontier_path = str(runs / "frontier.json")
    stop_file = str(runs / "STOP")

    config = LiveRunConfig(
        ttl=args.ttl, ttl_unit=args.ttl_unit, segment_cap=args.segment_cap,
        min_interval_s=args.min_interval,
        max_rounds=args.max_rounds, max_seconds=args.max_seconds,
        max_m_relations=args.max_m, max_m_atoms=args.max_m_atoms, stop_file=stop_file,
        checkpoint=True, checkpoint_refusal="skip",     # RUN_5 F1⁵: count + quarantine, never die
        checkpoint_every=args.checkpoint_every,         # RUN_5 F2ᵇ: cadence ≠ coverage
        state_path=state_path,
    )
    service = TomosService(runs / "checkpoints")
    uod_id = runs.name or "live"                       # runs/run3 → "run3" checkpoints

    def build(resume: bool):
        """Construct (source, tropism, runner) — fresh for the first leg, restored from the
        persisted state/frontier for a resumed one (the RUN_5 F1⁵ supervisor rebuilds this
        after any in-run crash; the decay clock and the crawl continue, never reset)."""
        if args.source == "recentchanges":
            src_kwargs = dict(ids_per_poll=args.chunk,
                              per_entity_cap=args.per_entity_cap or None,
                              record_path=str(runs / "polls.jsonl"))
            source = (RecentChangesSource.load_state(frontier_path, **src_kwargs)
                      if resume else RecentChangesSource(**src_kwargs))
        else:
            src_kwargs = dict(chunk_size=args.chunk, crawl=not args.no_crawl,
                              frontier_cap=args.frontier_cap,
                              per_entity_cap=args.per_entity_cap or None,
                              record_path=str(runs / "polls.jsonl"))
            source = (RotatingWikidataSource.load_state(frontier_path, **src_kwargs)
                      if resume else RotatingWikidataSource(args.seeds, **src_kwargs))
        if resume:
            print(f"resuming: source state restored from {frontier_path}", flush=True)

        tropism = None
        if args.warm_fraction > 0:
            # §13 (affirmed): warm slots = warm_fraction × chunk, front-of-queue via inject —
            # each poll's chunk is then k warm + the remainder fresh (the crawl).
            k = max(1, round(args.warm_fraction * args.chunk))
            tropism = WarmSetTropism(source.known_labels, k=k)

        docket = None
        if args.docket:
            # §15 increment 2a: the articulate stratum beside the warm one — what M
            # *lacks* (thin spots) directs Q1 re-reaches through the same inject seam.
            from query_docket import QueryDocket
            docket = QueryDocket(source.known_labels, k=args.docket_asks)

        holder = {}          # lets `evaluate` read the runner's refusal counter (set below)

        def evaluate(feed, res):
            """Per-segment console digest + persist the frontier beside the runner state."""
            source.save_state(frontier_path)
            from collections import Counter
            dispositions = dict(Counter(o.disposition for o in res.outcomes if o.disposition))
            # P1″'s instrument: a warm re-delivery of an unchanged value is a NON-REVISING round
            # (every agent abstains — the habit holding); runs 1–2 measured this fraction at zero.
            non_revising = sum(1 for o in res.outcomes if o.disposition is None)
            leg = source.legibility[-1] if source.legibility else None
            frontier_dropped = getattr(source, "frontier_dropped", 0)
            # F1″'s live instrument: atoms (pre-decay) beside names — the digest's m_atoms is the
            # post-decay figure; this line is what the operator watches climb under warm hubs.
            atoms = _sheet_atom_count(res.uod.current_egi)
            refused = holder["runner"].checkpoints_refused if "runner" in holder else 0
            print(f"  segment: rounds={len(res.outcomes)} atoms={atoms} dispositions={dispositions}"
                  + (f" non_revising={non_revising}" if non_revising else "")
                  + (f" legibility={leg:.2f}" if leg is not None else "")
                  + (f" warm_injected={source.injected}" if getattr(source, "injected", 0) else "")
                  + (f" ambiguous_skipped={tropism.ambiguous_skipped}"
                     if tropism and tropism.ambiguous_skipped else "")
                  + (f" unmapped_skipped={tropism.unmapped_skipped}"
                     if tropism and tropism.unmapped_skipped else "")
                  + (f" frontier_dropped={frontier_dropped}" if frontier_dropped else "")
                  + (f" statements_dropped={source.statements_dropped}"
                     if source.statements_dropped else "")
                  + (f" ⚠ ckpt_refused={refused}" if refused else "")
                  + (f" docket={len(docket.open_entries)}o/{docket.resolved}r/"
                     f"{docket.emitted}a/{docket.inexpressible}x" if docket else "")
                  + (f" ⚠ unparseable_dropped={source.unparseable_dropped}"
                     if getattr(source, "unparseable_dropped", 0) else ""), flush=True)
            return {"legibility": leg, "non_revising": non_revising, "atoms_pre_decay": atoms}

        # sleep=time.sleep: the runner's injectable sleep DEFAULTS TO A NO-OP (for tests) —
        # without passing the real one, min_interval pacing never sleeps and a quiet stream
        # (empty polls, e.g. overnight hours) becomes a hot spin against the Wikimedia API.
        if resume:
            runner = LiveRunner.resume(state_path, source, WikiDisputeFeed, config,
                                       uod_id=uod_id, panel=_panel(), tropism=tropism,
                                       docket=docket, evaluate=evaluate, service=service,
                                       sleep=time.sleep)
        else:
            runner = LiveRunner("", source, WikiDisputeFeed, config,
                                uod_id=uod_id, panel=_panel(), tropism=tropism,
                                docket=docket, evaluate=evaluate, service=service,
                                sleep=time.sleep)
        holder["runner"] = runner
        return source, tropism, docket, runner

    # ---- the supervisor loop (RUN_5 F1⁵ disposal (b)): an in-run crash is caught, counted, ----
    # ---- and the run RESUMED from the per-segment state — the overall deadline is honored  ----
    # ---- across legs (each resumed leg gets the remaining wall-clock, not a fresh budget). ----
    deadline = (time.monotonic() + args.max_seconds) if args.max_seconds else None
    resume = args.resume
    crashes = 0
    refused_total = 0
    res = None

    started = time.strftime("%Y-%m-%d %H:%M:%S")
    origin = (f"seeds={args.seeds}" if args.source == "frontier"
              else "the recentchanges stream (bots excluded)")
    warm = (f" warm_fraction={args.warm_fraction}" if args.warm_fraction > 0
            else " tropism off (passive baseline)")
    print(f"run start {started} — source={args.source} · {origin} · ttl={args.ttl} "
          f"{args.ttl_unit}{warm} pacing={args.min_interval}s stop: touch {stop_file}", flush=True)

    while True:
        if deadline is not None:
            config.max_seconds = max(1.0, deadline - time.monotonic())
        source, tropism, docket, runner = build(resume)
        try:
            res = runner.run()
            refused_total += runner.checkpoints_refused
            break
        except KeyboardInterrupt:
            raise
        except Exception:
            import traceback
            refused_total += runner.checkpoints_refused
            crashes += 1
            traceback.print_exc()
            if crashes > args.max_crashes:
                print(f"supervisor: crash budget exhausted ({crashes} crashes) — giving up",
                      flush=True)
                raise
            if deadline is not None and time.monotonic() >= deadline - 60:
                print("supervisor: crash at the deadline — stopping; per-segment digests "
                      "above are the record", flush=True)
                break
            can_resume = Path(state_path).exists() and Path(frontier_path).exists()
            resume = can_resume
            print(f"supervisor: crash #{crashes} — "
                  + ("resuming from the persisted state" if can_resume
                     else "no persisted state yet, restarting fresh")
                  + " in 10 s", flush=True)
            time.sleep(10)

    if res is None:
        print(f"\nstopped: crash_at_deadline   crashes survived: {crashes}   "
              f"checkpoints refused (quarantined): {refused_total}")
        return 1

    print(f"\nstopped: {res.stopped_because}   total rounds: {res.total_rounds}"
          + (f"   crashes survived: {crashes}" if crashes else "")
          + (f"   checkpoints refused (quarantined): {refused_total}" if refused_total else ""))
    if crashes:
        print("supervisor note: the final summary below covers the last leg only; "
              "per-segment digests above span the whole run")
    for d in res.segments:
        print(f"  segment {d.segment}: rounds={d.rounds} |M|={d.m_relations} atoms={d.m_atoms} "
              f"dispositions={d.dispositions} decayed={d.decayed} ({d.elapsed_s:.1f}s)")
    if tropism:
        print(f"tropism: warm_emitted={tropism.emitted} injected={source.injected} "
              f"ambiguous_skipped={tropism.ambiguous_skipped} "
              f"unmapped_skipped={tropism.unmapped_skipped}")
    if docket:
        print(f"docket (§15·2a): harvested={docket.harvested} resolved={docket.resolved} "
              f"asks_emitted={docket.emitted} open={len(docket.open_entries)} "
              f"inexpressible={docket.inexpressible} deferred={docket.deferred} "
              f"ambiguous_skipped={docket.ambiguous_skipped} "
              f"unmapped_skipped={docket.unmapped_skipped}")
    mat = runner.materializer
    print(f"materializer (F2⁗ semi-naive): rebuilds={mat.rebuilds} "
          f"extensions={mat.extensions} hits={mat.hits}")
    if source.legibility:
        worst = max(source.legibility)
        print(f"legibility per poll: {['%.2f' % f for f in source.legibility]}"
              + ("   ⚠ labels degrading" if worst > 0.5 else ""))
    if res.episodes:
        from agon_metalearning import mechanism_principles
        print("mechanism principles (decay-aware, cross-segment):")
        for p in mechanism_principles(res.episodes):
            print(f"  {p.mechanism}: n={p.count} stick_rate={p.stick_rate} "
                  f"durable={p.durable} decay_erased={p.decay_erased}")
    if res.segments:
        from agon_metalearning import poise_from_digests
        strip = " ".join("●" if w.poised else ("○" if w.failure == "rigidity" else "✕")
                         for w in poise_from_digests(res.segments))
        print(f"poise per segment (● poised · ○ rigidity · ✕ thrash): {strip}")
    print(f"\nartifacts: {runs}/polls.jsonl (offline replay) · {runs}/checkpoints (UoDs) · "
          f"log your dispositions of the pre-registered priors in runs/RUN_<n>_LOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
