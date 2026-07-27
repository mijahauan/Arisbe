"""West-in-kytē E3c driver — the symmetry-breaking rider (E3b spec §10,
pre-registered 2026-07-26): perturb the stranded round-robin 4/4/4 by one
single-folder move and descend each perturbation through the verbatim E3
Arm-N walk. PS1 (knife-edge): every perturbed terminus < 118,865. PS2 (floor
consistency): none < 101,411.

Numbers-only stdout (custody convention): bucketings print as sizes, never
folder names. Reuses west_basin_map / west_meta_agon machinery verbatim."""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_basin_map import full_neighbourhood_improver
from west_measure import round_robin_buckets
from west_meta_agon import (MemoEvaluator, bucket_sizes, canonical,
                            run_meta_walk)

# Pre-registered knobs — identical to E3b full mode (spec §2/§10, fixed).
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

# The pre-registered perturbation cells: ordered (source, dest) bucket pairs
# on the CANONICAL round-robin N=3 bucketing; move the lexicographically
# first folder of the source bucket into the destination bucket.
CELLS = ((0, 1), (1, 2), (2, 0))

# PS1/PS2 thresholds — from the E3b map (runs/WEST_E3B_LOG.md).
DEAR_FLOOR = 118865
MAP_FLOOR = 101411

# Smoke — driver contract test only, never a real run.
SMOKE_F0 = 4
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12


def perturbed_starts(folders):
    """The three pre-registered single-folder perturbations of the canonical
    round-robin N=3 bucketing. A cell whose source bucket would be emptied
    (only possible at smoke scale) is skipped and counted, never silently
    dropped."""
    base = canonical(round_robin_buckets(folders, 3))
    out, skipped = [], []
    for src, dst in CELLS:
        buckets = [list(b) for b in base]
        if len(buckets[src]) < 2:
            skipped.append((src, dst))
            continue
        moved = buckets[src].pop(0)          # lexicographically first
        buckets[dst].append(moved)
        out.append(((src, dst), canonical(buckets)))
    return base, out, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e3c_"))
    dest.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        f0, notes, journal, r, mode = SMOKE_F0, SMOKE_NOTES, SMOKE_JOURNAL, SMOKE_R, "smoke"
    else:
        f0, notes, journal, r, mode = F0, N_NOTES, JOURNAL, R, "full"

    print("=== West-in-kytē E3c — symmetry-breaking rider (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={f0} n={notes} p_base={P_BASE} "
          f"J={journal} ttl={TTL} R={r} theta={THETA} merge_k={MERGE_K} "
          f"max_rounds={MAX_ROUNDS} cells={CELLS}", flush=True)

    t0 = time.time()
    vault = dest / "vault"
    manifest = generate_vault(vault, seed=SEED, folders=f0,
                              notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE,
                              journal_len=journal)

    base, starts, skipped = perturbed_starts(manifest.folders)
    print(f"base={bucket_sizes(base)} perturbed_starts={len(starts)} "
          f"skipped_cells={len(skipped)}", flush=True)

    memo = MemoEvaluator(vault, manifest, rounds=r, ttl=TTL)

    results = []
    for (src, dst), start in starts:
        wr = run_meta_walk(start, name=f"e3c_{src}to{dst}", arm="naive",
                           manifest=manifest, evaluate=memo.evaluate,
                           theta=THETA, merge_k=MERGE_K,
                           max_rounds=MAX_ROUNDS, ledger_path=None)
        cost = wr.final_evidence.cost_naive
        sizes = bucket_sizes(wr.final)
        cheap_family = sorted(len(b) for b in wr.final) == sorted((10, 1, 1)) \
            if f0 == 12 else None
        shadowed = full_neighbourhood_improver(
            wr.final, manifest, memo.evaluate, theta=THETA, arm="naive")
        results.append(((src, dst), start, wr, cost, sizes, cheap_family, shadowed))
        print(f"cell={src}to{dst} start={bucket_sizes(start)} -> "
              f"optimum={sizes} cost={cost} cheap_family={cheap_family} "
              f"shadowed={shadowed}", flush=True)

    # Priors (full mode only — smoke is a contract run, thresholds meaningless).
    if mode == "full" and results:
        costs = [item[3] for item in results]
        ps1 = "held" if all(c < DEAR_FLOOR for c in costs) else "refuted"
        ps2 = "held" if all(c >= MAP_FLOOR for c in costs) else "refuted"
        print(f"priors: {{'PS1': '{ps1}', 'PS2': '{ps2}'}}", flush=True)

    # Determinism canary: cell (0->1) fresh-memo re-run.
    canary = "skipped"
    if not args.no_canary and results:
        (src, dst), start, orig_wr = results[0][0], results[0][1], results[0][2]
        fresh = MemoEvaluator(vault, manifest, rounds=r, ttl=TTL)
        re_wr = run_meta_walk(start, name="canary", arm="naive",
                              manifest=manifest, evaluate=fresh.evaluate,
                              theta=THETA, merge_k=MERGE_K,
                              max_rounds=MAX_ROUNDS, ledger_path=None)
        same = (re_wr.moves == orig_wr.moves and re_wr.final == orig_wr.final
                and re_wr.final_evidence.cost_naive == orig_wr.final_evidence.cost_naive)
        canary = "PASS" if same else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    print(f"memo_hits={memo.hits} memo_misses={memo.misses} "
          f"wall_s={round(time.time() - t0, 1)}", flush=True)
    print("notes: E3c descends three pre-registered single-folder perturbations "
          "of the stranded round-robin 4/4/4 (E3b Finding 2) through the "
          "verbatim Arm-N walk. PS1 knife-edge: every perturbed terminus "
          "escapes the dear band (< 118865). PS2 floor: none lands below "
          "101411. The walk cannot rebalance to 4/4/4 (split/merge only); "
          "escape vs strand is which basin the descent finds. Sizes only "
          "(custody).", flush=True)


if __name__ == "__main__":
    main()
