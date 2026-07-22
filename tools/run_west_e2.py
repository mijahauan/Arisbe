"""West-in-kytē E2 driver — the size sweep, the fitted exponents, the P1²-P4²
verdicts, the ttl rider, the determinism canary.

Numbers-only stdout (custody-safe): no note id, title, path, or body text is
ever printed. Spec: docs/superpowers/specs/2026-07-22-west-in-kyte-e2-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_experiment import (run_e2_config, assemble_e2_report, run_ttl_rider,
                             decide_p4)

# Pre-registered E2 knobs (spec §2 — fixed).
SEED = 20260721
NOTES_PER_FOLDER = 40
P_CROSS = 0.15
JOURNAL_LEN = 40
TTL = 120
THETA, TOL = 0.20, 0.10
FOLDER_SIZES = [2, 4, 6, 8, 12, 16]
RIDER_FOLDERS = 6
RIDER_TTLS = [60, 120, 240, 0]          # 0 == decay off, ordered last
CANARY_FOLDERS = 6

# Smoke grid — for the driver contract test only, never for a real run.
SMOKE_SIZES = [2, 3]
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3


def build_grid():
    """The pre-registered grid as (folders, rounds) pairs: R = 25*(F+1), so every
    member performs exactly 25 rounds at every F (spec §2.1)."""
    return [(f, 25 * (f + 1)) for f in FOLDER_SIZES]


GRID = build_grid()


def _run_point(dest_root, folders, rounds, notes, journal, ttl):
    """Generate a corpus for one grid point and run MONO + traced FED over it."""
    dest = dest_root / f"f{folders}"
    manifest = generate_vault(dest, seed=SEED, folders=folders,
                              notes_per_folder=notes, cross_folder_link_prob=P_CROSS,
                              journal_len=journal)
    return run_e2_config(dest, manifest, folders=folders, rounds=rounds, ttl=ttl), manifest, dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None, help="corpus dir (default: a temp dir)")
    ap.add_argument("--ttl", type=int, default=TTL)
    ap.add_argument("--smoke", action="store_true",
                    help="tiny grid for the driver contract test")
    ap.add_argument("--no-canary", action="store_true")
    ap.add_argument("--no-rider", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest_root = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e2_"))
    dest_root.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        grid = [(f, 4) for f in SMOKE_SIZES]
        notes, journal = SMOKE_NOTES, SMOKE_JOURNAL
        rider_ttls = [120, 0]
    else:
        grid = GRID
        notes, journal = NOTES_PER_FOLDER, JOURNAL_LEN
        rider_ttls = RIDER_TTLS

    print("=== West-in-kytē E2 — the size sweep (numbers only) ===", flush=True)
    print(f"mode={'smoke' if args.smoke else 'full'} "
          f"seed={SEED} n={notes} p={P_CROSS} J={journal} ttl={args.ttl} "
          f"theta={THETA} tol={TOL} points={len(grid)}", flush=True)

    configs = []
    rider_manifest = rider_dest = None
    for folders, rounds in grid:
        t0 = time.time()
        cfg, manifest, dest = _run_point(dest_root, folders, rounds, notes,
                                         journal, args.ttl)
        configs.append(cfg)
        if folders == (SMOKE_SIZES[0] if args.smoke else RIDER_FOLDERS):
            rider_manifest, rider_dest = manifest, dest
        print(f"F={folders} R={rounds} "
              f"mono={cfg.mono.cost.total()} "
              f"fed_incr={cfg.fed_cost_incremental} fed_naive={cfg.fed_cost_naive} "
              f"fed_split(mat={cfg.fed.cost.materialization_atoms} "
              f"peel={cfg.fed.cost.peel_proxy}) "
              f"tax(cells={cfg.tax.cells_written} incr={cfg.tax.incremental} "
              f"naive_global={cfg.tax.naive_global_round} "
              f"naive_member={cfg.tax.naive_member_round}) "
              f"cv={round(cfg.member_reading.cv, 4)} "
              f"mean_member={round(cfg.member_reading.mean, 1)} "
              f"folder_members={cfg.member_reading.folder_member_costs} "
              f"journal_member={cfg.member_reading.journal_member_cost} "
              f"conflicts={cfg.fed.conflicts} "
              f"|M|mono={cfg.mono.quality.final_m_size} "
              f"|M|fed={cfg.fed.quality.final_m_size} "
              f"K2mono={cfg.mono.quality.k2_stick_rate} "
              f"K2fed={cfg.fed.quality.k2_stick_rate} "
              f"K3mono={round(cfg.mono.quality.k3_ratio, 4)} "
              f"K3fed={round(cfg.fed.quality.k3_ratio, 4)} "
              f"gap={round(cfg.gap, 4)} wall_s={round(time.time() - t0, 1)}",
              flush=True)

    rep = assemble_e2_report(configs, theta=THETA, tol=TOL)
    print(f"beta_mono={round(rep.fit_mono.beta, 4)} "
          f"(se={round(rep.fit_mono.stderr, 4)} r2={round(rep.fit_mono.r_squared, 4)} "
          f"weak={rep.fit_mono.weak})", flush=True)
    print(f"beta_fed_incr={round(rep.fit_fed_incremental.beta, 4)} "
          f"(se={round(rep.fit_fed_incremental.stderr, 4)} "
          f"r2={round(rep.fit_fed_incremental.r_squared, 4)} "
          f"weak={rep.fit_fed_incremental.weak})", flush=True)
    # crossover_kind (F3) must always accompany crossover_f: under
    # "below-range" — the strongest confirmation of P3² (FED-naive dearer
    # than MONO at every swept size) — crossover_f is None by construction,
    # so the bare number alone would misread the strongest result as no
    # result at all.
    print(f"beta_fed_naive={round(rep.fit_fed_naive.beta, 4)} "
          f"beta_tax_naive={round(rep.fit_tax_naive.beta, 4)} "
          f"crossover_F={rep.crossover_f} crossover_kind={rep.crossover_kind}",
          flush=True)
    print(f"broker_forced={rep.broker_forced} "
          f"tax_clamped_count={rep.tax_clamped_count}", flush=True)

    p4 = "skipped"
    if not args.no_rider:
        if rider_manifest is not None:
            rider_rounds = 4 if args.smoke else 25 * (RIDER_FOLDERS + 1)
            readings = run_ttl_rider(rider_dest, rider_manifest, rounds=rider_rounds,
                                     ttls=rider_ttls)
            for r in readings:
                print(f"rider ttl={r.ttl} |M|mono={r.mono_m} |M|fed={r.fed_m} "
                      f"ratio={round(r.ratio, 4)}", flush=True)
            p4 = decide_p4(readings)
        else:
            # Minor 3 (final review): the rider's capture point is coupled to
            # grid membership (the loop above only stashes rider_manifest when
            # a swept F equals the rider target) — if RIDER_FOLDERS ever left
            # FOLDER_SIZES this reads P4="skipped" with no explanation. Make
            # the skip explicit rather than silent.
            target = SMOKE_SIZES[0] if args.smoke else RIDER_FOLDERS
            print(f"rider_skipped: target_folders={target} not in swept grid",
                  flush=True)

    priors = dict(rep.priors)
    priors["P4"] = p4
    print(f"priors: {priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        folders = CANARY_FOLDERS
        rounds = 25 * (folders + 1)
        a, _m, _d = _run_point(dest_root, folders, rounds, notes, journal, args.ttl)
        b, _m2, _d2 = _run_point(dest_root, folders, rounds, notes, journal, args.ttl)
        canary = "PASS" if (a.mono.cost.total() == b.mono.cost.total()
                            and a.fed_cost_naive == b.fed_cost_naive
                            and a.fed_cost_incremental == b.fed_cost_incremental) else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    print("notes: A3 PAID DOWN — the coordinator tax is now a true per-round "
          "replay (spec §3.1), exact for the passive coordinator (read-only, so "
          "replaying it cannot perturb what it measures); the active broker is "
          "NOT replay-exact and is not run here. TWO PRE-REGISTERED ARMS: "
          "fed_naive (Arm N, a full O(H^2) scan per member-round export — the "
          "pessimistic bound) and fed_incr (Arm I, delta-scan — totals H(H-1)/2 "
          "for a whole run however long) — P1² is now three-valued: 'refuted' "
          "is reserved for the pre-committed beta_mono<=beta_fed_incr condition, "
          "and a run where the separation holds but beta_mono misses the 1.3 "
          "bar reads 'separation-only', never a bare pass/fail. naive_global "
          "(one scan per synchronized global round) is a DISCLOSED SECONDARY "
          "reading, reported because spec §4.1's 'one scan/round' is ambiguous "
          "between it and Arm N — it is not verdict-bearing and no prior "
          "depends on it. cv is over FOLDER-MEMBERS ONLY (spec §3.3 — E1 "
          "included the ~30x-cheaper journal-member, which alone flips the "
          "verdict at small F); journal_member is reported beside it. K1 = "
          "N/A (raise-only membrane, A1). K3 is expected 0.0 (the vault M "
          "carries no Horn laws — true, not a bug — K3mono/K3fed are printed "
          "per config above so that claim is checkable, not asserted blind). "
          "A weak fit (n<6 or r2<0.90) makes its prior 'undetermined', never "
          "held or refuted. The canary runs ONE config (F=6), not the whole "
          "sweep — a narrowing relative to E1, disclosed. Synthetic corpus: "
          "this is an exponent of the generator's topology, not of real "
          "reasoning corpora. INTERLEAVING ASSUMPTION (verdict-bearing for "
          "P3²): replay_coordinator_tax's Arm N models federation members as "
          "running CONCURRENTLY within a synchronized global round, but this "
          "harness's _fed_members executes them SEQUENTIALLY (one member's "
          "whole round-share, then the next); the two orderings are not "
          "equivalent (~26% apart on a reference case) because Arm N's cost "
          "depends on how big the held-cell set is at each individual "
          "export. Arm N (naive_member/beta_tax_naive) is the SOLE basis for "
          "gamma and the crossover, i.e. all of P3² — a genuinely concurrent "
          "federation is what is being modelled, not what this harness "
          "happens to execute. BROKER_FORCED lists swept F values whose "
          "passive-registry gap exceeded theta (spec §3.1): that config's "
          "coordinator tax is NOT replay-exact and its contribution to "
          "beta_fed(N)/beta_tax_naive/gamma should be discounted accordingly "
          "— it stays folded into the fits above, flagged rather than "
          "excluded, so both readings are visible side by side. "
          "TAX_CLAMPED_COUNT counts configs whose naive_member_round was <=0 "
          "and had to be clamped to 1 to take its log — a nonzero count means "
          "fit_tax_naive contains a FABRICATED (not measured) point and its "
          "weak flag is forced True as a result; it should never by itself "
          "carry a verdict. CROSSOVER_KIND='below-range' means FED-naive was "
          "dearer than MONO at EVERY swept F — no in-range transition to "
          "observe, so crossover_F prints as None BY CONSTRUCTION (the "
          "below-range F itself is never computed) — that is the STRONGEST "
          "possible confirmation of P3², not a missing result; read "
          "crossover_kind, not crossover_F, exactly as with P1²'s "
          "three-valuedness above.", flush=True)


if __name__ == "__main__":
    main()
