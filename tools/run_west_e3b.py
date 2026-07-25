"""West-in-kytē E3b driver — the basin map (endogenous-partition landscape
census): enumerate the local optima the Arm-N walk reaches from each
structured start, and their watersheds.

Numbers-only stdout (custody convention): bucketings print as sizes, never
folder names. Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_basin_map import (
    assemble_basin_report, bucket_sizes, full_neighbourhood_improver,
    map_basins, structured_starts)
from west_meta_agon import MemoEvaluator, canonical, run_meta_walk

# Pre-registered E3b knobs (spec §2 — fixed).
SEED = 20260721
F0 = 12
N_NOTES = 40
P_BASE = 0.15
JOURNAL = 40
TTL = 120
R = 325
THETA = 0.20
MERGE_K = 3
MAX_ROUNDS = 20
COMP_PARTS = (3, 4)
COMP_CAP = 12

# Smoke — driver contract test only, never a real run.
SMOKE_F0 = 4
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12
SMOKE_PARTS = (2, 3)
SMOKE_CAP = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e3b_"))
    dest.mkdir(parents=True, exist_ok=True)

    # Select smoke or full knobs
    if args.smoke:
        f0 = SMOKE_F0
        notes = SMOKE_NOTES
        journal = SMOKE_JOURNAL
        r = SMOKE_R
        comp_parts = SMOKE_PARTS
        comp_cap = SMOKE_CAP
        mode = "smoke"
    else:
        f0 = F0
        notes = N_NOTES
        journal = JOURNAL
        r = R
        comp_parts = COMP_PARTS
        comp_cap = COMP_CAP
        mode = "full"

    # Header and config
    print("=== West-in-kytē E3b — the basin map (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={f0} n={notes} p_base={P_BASE} "
          f"J={journal} ttl={TTL} R={r} theta={THETA} merge_k={MERGE_K} "
          f"max_rounds={MAX_ROUNDS} comp_parts={comp_parts} comp_cap={comp_cap}",
          flush=True)

    t0 = time.time()

    # Generate vault
    vault = dest / "vault"
    manifest = generate_vault(vault, seed=SEED, folders=f0,
                              notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE,
                              journal_len=journal)

    # Build structured starts
    starts = structured_starts(manifest, comp_parts=comp_parts, comp_cap=comp_cap)
    print(f"structured_starts={len(starts)}", flush=True)

    # One shared MemoEvaluator for all starts
    memo = MemoEvaluator(vault, manifest, rounds=r, ttl=TTL)

    # Descend each start
    bm = map_basins(vault, manifest, starts, rounds=r, ttl=TTL, theta=THETA,
                    merge_k=MERGE_K, max_rounds=MAX_ROUNDS, evaluator=memo)

    # Print one line per start
    for start in starts:
        start_key = ";".join(",".join(b) for b in start)
        wr = bm.terminus_by_start[start_key]
        start_sizes = bucket_sizes(start)
        term_sizes = bucket_sizes(wr.final)
        print(f"start={start_sizes} -> optimum={term_sizes} cost={wr.final_evidence.cost_naive}",
              flush=True)

    # Compute shadowed diagnostic for each terminus
    shadowed: Dict[str, bool] = {}
    for term_key in bm.watersheds.keys():
        wr = bm.terminus_by_start[bm.watersheds[term_key][0]]
        shadowed[term_key] = full_neighbourhood_improver(
            wr.final, manifest, memo.evaluate, theta=THETA, arm="naive")

    # Assemble report
    report = assemble_basin_report(bm, shadowed)

    # Print optima (one per distinct terminus, cost-ascending)
    for opt in report.optima:
        print(f"optimum sizes={opt.sizes} n={opt.n} cost={opt.cost} "
              f"watershed={opt.watershed_count} shadowed={opt.shadowed}",
              flush=True)

    # Summary line
    print(f"consistency_ok={report.consistency_ok} cheapest={report.cheapest_cost} "
          f"distinct_optima={report.distinct_count} memo_hits={memo.hits} "
          f"memo_misses={memo.misses} wall_s={round(time.time() - t0, 1)}",
          flush=True)

    # Arm-I control: run one end-to-end (naive Arm-N) on the finest partition
    fs = sorted(manifest.folders)
    finest = canonical([[f] for f in fs])
    finest_wr = run_meta_walk(finest, name="arm_i", arm="naive", manifest=manifest,
                              evaluate=memo.evaluate, theta=THETA, merge_k=MERGE_K,
                              max_rounds=MAX_ROUNDS, ledger_path=None)
    print(f"arm_i_control final_n={finest_wr.final_evidence.n} "
          f"final_sizes={bucket_sizes(finest_wr.final)}",
          flush=True)

    # Priors
    print(f"priors: {report.priors}", flush=True)

    # Determinism canary
    canary = "skipped"
    if not args.no_canary:
        # Pick a mid-start to re-run (non-vacuous — has revisited bucketings)
        mid_idx = len(starts) // 2
        mid_start = starts[mid_idx]
        mid_start_key = ";".join(",".join(b) for b in mid_start)

        # Re-run with fresh memo
        fresh_memo = MemoEvaluator(vault, manifest, rounds=r, ttl=TTL)
        fresh_wr = run_meta_walk(mid_start, name="canary", arm="naive",
                                 manifest=manifest, evaluate=fresh_memo.evaluate,
                                 theta=THETA, merge_k=MERGE_K,
                                 max_rounds=MAX_ROUNDS, ledger_path=None)

        # Original result
        orig_wr = bm.terminus_by_start[mid_start_key]

        # Compare: moves, final, cost_naive
        same = (fresh_wr.moves == orig_wr.moves
                and fresh_wr.final == orig_wr.final
                and fresh_wr.final_evidence.cost_naive == orig_wr.final_evidence.cost_naive)
        canary = "PASS" if same else "FAIL"

    print(f"determinism_canary: {canary}", flush=True)

    # Notes
    print("notes: E3b enumerates the local optima (Arm-N walk endpoints) reachable "
          "from a systematic seed set of structured starts. The basin map inverts "
          "the collection: each distinct optimum is attributed its attractor set "
          "(all starts that descend to it). PM1 checks interior diversity (N=3 "
          "optima); PM2 checks merge-direction advantage; PM3 checks floor "
          "(no cheaper basin than E3's W2); PM4 checks sparsity (≤5 optima). "
          "Shadowed detects full-neighbourhood improvements (terminal local "
          "optima, no move without gap refusal). Arm-I control runs the finest "
          "partition to check that the naive walk terminates (the Arm-I baseline "
          "for comparison). All bucketings printed as sizes (custody); "
          "determinism canary re-runs a mid-start with cleared memo.",
          flush=True)


if __name__ == "__main__":
    main()
