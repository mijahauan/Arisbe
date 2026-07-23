"""West-in-kytē E2b driver — the calibration: the Sweep-B cost U-curve, the
p-sweep coherence shoulder + the first broker exercise, the partition-quality
arm, and the PB1-PB5 verdicts.

Numbers-only stdout (custody-safe): no note id, title, path, or folder name is
ever printed. Spec: docs/superpowers/specs/2026-07-22-west-in-kyte-e2b-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_experiment import (run_sweepb_point, run_p_sweep, run_quality_arm,
                             assemble_e2b_report)

# Pre-registered E2b knobs (spec §2-§4 — fixed).
SEED = 20260721
F0 = 12
N_NOTES = 40
P_BASE = 0.15
JOURNAL = 40
TTL = 120
R_FIXED = 325
SWEEP_N = [1, 2, 3, 4, 6, 12]
P_SWEEP_F = 6
P_SWEEP_R = 175
P_LIST = [0.15, 0.30, 0.45, 0.60, 0.75]
THETA = 0.20
TOL = 0.10
QUALITY_N = 4
CANARY_N = 4

# Smoke — for the driver contract test only, never a real run.
SMOKE_N = [1, 2, 4]
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12


def build_config():
    """The pre-registered config as a dict (spec §2-§4). Pure."""
    return {"seed": SEED, "F0": F0, "sweep_n": list(SWEEP_N), "R": R_FIXED,
            "p_list": list(P_LIST), "theta": THETA, "quality_n": QUALITY_N}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest_root = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e2b_"))
    dest_root.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        sweep_n, notes, journal, rfix = SMOKE_N, SMOKE_NOTES, SMOKE_JOURNAL, SMOKE_R
        p_list, psweep_f, psweep_r, quality_n = [0.15, 0.6], 4, SMOKE_R, 2
        mode = "smoke"
    else:
        sweep_n, notes, journal, rfix = SWEEP_N, N_NOTES, JOURNAL, R_FIXED
        p_list, psweep_f, psweep_r, quality_n = P_LIST, P_SWEEP_F, P_SWEEP_R, QUALITY_N
        mode = "full"

    print("=== West-in-kytē E2b — the calibration (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={F0} n={notes} p_base={P_BASE} J={journal} "
          f"ttl={TTL} R={rfix} theta={THETA} tol={TOL}", flush=True)

    # Part 1 — Sweep-B (fixed corpus, vary N, round-robin, both arms).
    sb_dest = dest_root / "sweepb"
    manifest = generate_vault(sb_dest, seed=SEED, folders=F0, notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE, journal_len=journal)
    sweepb = []
    for n in sweep_n:
        t0 = time.time()
        pt = run_sweepb_point(sb_dest, manifest, n=n, rounds=rfix, ttl=TTL)
        sweepb.append(pt)
        print(f"sweepb N={n} fed_naive={pt.fed_cost_naive} "
              f"fed_incr={pt.fed_cost_incremental} cut={pt.cut_links} "
              f"cv={round(pt.member_reading.cv, 4)} "
              f"mean_member={round(pt.member_reading.mean, 1)} "
              f"|M|fed={pt.m_fed} K2={pt.k2_fed} K3={round(pt.k3_fed, 4)} "
              f"gap={round(pt.gap, 4)} wall_s={round(time.time() - t0, 1)}",
              flush=True)

    # Part 2 — the p-sweep + the first broker exercise.
    ps = run_p_sweep(dest_root / "psweep", folders=psweep_f, notes=notes,
                     journal=journal, rounds=psweep_r, ttl=TTL, seed=SEED,
                     ps=p_list, theta=THETA)
    for pt in ps.points:
        print(f"psweep p={pt.p} gap={round(pt.gap, 4)} "
              f"coverage={round(pt.coverage, 4)} coord={pt.coordinator_cost}",
              flush=True)
    print(f"shoulder_p={ps.shoulder_p} broker_routes={ps.broker_routes} "
          f"broker_coord={ps.broker_coord_cost}", flush=True)

    # Part 3 — the quality arm, at the shoulder p (else 0.75, flagged).
    q_p = ps.shoulder_p if ps.shoulder_p is not None else p_list[-1]
    q_flag = "at-shoulder" if ps.shoulder_p is not None else "coherence-force-weak(p=max)"
    q_dest = dest_root / "quality"
    q_manifest = generate_vault(q_dest, seed=SEED, folders=F0, notes_per_folder=notes,
                                cross_folder_link_prob=q_p, journal_len=journal)
    quality = run_quality_arm(q_dest, q_manifest, n=quality_n, rounds=rfix, ttl=TTL,
                              tol=TOL)
    print(f"quality N={quality_n} p={q_p} ({q_flag}) "
          f"round_robin_cost={quality.round_robin_cost} "
          f"link_aware_cost={quality.link_aware_cost} "
          f"round_robin_cut={quality.round_robin_cut} "
          f"link_aware_cut={quality.link_aware_cut} material={quality.material}",
          flush=True)

    rep = assemble_e2b_report(sweepb, ps, quality, tol=TOL)
    print(f"ucurve_naive argmin_n={rep.ucurve_naive.argmin_n} "
          f"interior={rep.ucurve_naive.interior}", flush=True)
    print(f"ucurve_incr argmin_n={rep.ucurve_incremental.argmin_n} "
          f"monotone={rep.ucurve_incremental.monotone_nonincreasing} "
          f"interior={rep.ucurve_incremental.interior}", flush=True)
    print(f"priors: {rep.priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        a = run_sweepb_point(sb_dest, manifest, n=CANARY_N if not args.smoke else 2,
                             rounds=rfix, ttl=TTL)
        b = run_sweepb_point(sb_dest, manifest, n=CANARY_N if not args.smoke else 2,
                             rounds=rfix, ttl=TTL)
        canary = "PASS" if (a.fed_cost_naive == b.fed_cost_naive
                            and a.fed_cost_incremental == b.fed_cost_incremental) else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    print("notes: E2b CHARACTERIZES E3's fitness landscape; it does NOT test "
          "convergence (that is E3). PB1 = the naive-arm Sweep-B U-curve has an "
          "INTERIOR cost minimum (1 < argmin_n < 12) — E3's target exists; PB2 "
          "(control) = the incremental-arm curve is monotone non-increasing (no "
          "interior min), so the optimum is a COORDINATION effect not a "
          "materialization one. PB3 = a coherence shoulder (gap > theta) exists "
          "in the p-sweep, forcing the broker (its first exercise; broker cost "
          "is an END-OF-RUN SNAPSHOT, A3-style, NOT replay-exact — a lower "
          "bound, disclosed). PB4 (partition quality has teeth: link-aware "
          "cheaper than round-robin at equal N) is CONDITIONAL on PB3 — "
          "'undetermined' if no shoulder exists (the force it tests is absent), "
          "never refuted. PB5 = terminal-unit invariance persists across the N "
          "sweep. The partition unit is the FOLDER, not the note (spec §1). N=1 "
          "shares R with the journal member, so it is the content-monolith at "
          "constant total effort, NOT E2's dedicated-R mono. The Arm-N "
          "interleaving assumption (concurrent members) carries over from E2 "
          "and is verdict-bearing for every naive-arm reading. Synthetic "
          "corpus, one seed: these are the generator's curves, not real "
          "reasoning corpora. K1 = N/A (raise-only). K3 printed per point "
          "(expected 0.0, checkable not asserted).", flush=True)


if __name__ == "__main__":
    main()
