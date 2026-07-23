"""West-in-kytē E3 driver — the meta-Agon over folder-bucketings: walks
W1-W4, the rider E2b', the PE1-PE5 verdicts, the determinism canary.

Numbers-only stdout (custody convention): bucketings print as sizes, never
folder names. Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_meta_agon import (MemoEvaluator, assemble_e3_report, bucket_sizes,
                            canonical, find_biting_regime, replay_walk,
                            run_broker_quality, run_meta_walk)

# Pre-registered E3 knobs (spec §2-§6 — fixed).
SEED = 20260721
F0 = 12
N_NOTES = 40
P_BASE = 0.15
JOURNAL = 40
TTL = 120
R_FIXED = 325
THETA = 0.20
TOL = 0.10
MERGE_K = 3
MAX_ROUNDS = 20
RIDER_TTLS = (60, 30, 15)
RIDER_NS = (2, 4)
QUALITY_N = 4

# Smoke — driver contract test only, never a real run.
SMOKE_F0 = 4
SMOKE_NOTES = 3
SMOKE_JOURNAL = 3
SMOKE_R = 12


def sizes_from_key(key: str) -> str:
    """Numbers-only rendering of a walk-round's incumbent/chosen key
    (custody convention — reconstruct the bucketing, print only sizes)."""
    return bucket_sizes(canonical(b.split(",") for b in key.split(";")))


def _starts(manifest, smoke: bool):
    fs = sorted(manifest.folders)
    w1 = canonical([fs])
    w2 = canonical([[f] for f in fs])
    if smoke:
        w3 = canonical([fs[0:2], fs[2:3], fs[3:4]])          # sizes 2/1/1
    else:
        w3 = canonical([fs[0:6], fs[6:9], fs[9:11], fs[11:12]])  # 6/3/2/1
    return w1, w2, w3


def _run_walk(name, start, arm, manifest, memo, dest, max_rounds):
    t0 = time.time()
    # Wrap evaluate to print nothing per eval; per-round lines print below.
    res = run_meta_walk(start, name=name, arm=arm, manifest=manifest,
                        evaluate=memo.evaluate, theta=THETA, merge_k=MERGE_K,
                        max_rounds=max_rounds, ledger_path=dest / f"{name}.jsonl")
    for wr in res.rounds:
        print(f"walk={name} round={wr.round_no} n={wr.incumbent_evidence.n} "
              f"sizes={sizes_from_key(wr.incumbent_key)} "
              f"slate={len(wr.slate)} "
              f"refused={sum(1 for e in wr.slate if e.refused)} "
              f"disposition={wr.disposition} "
              f"cost={wr.incumbent_evidence.cost_naive if arm == 'naive' else wr.incumbent_evidence.cost_incremental} "
              f"gap={round(wr.incumbent_evidence.gap, 4)}", flush=True)
    print(f"walk={name} halt={res.halt} final_n={res.final_evidence.n} "
          f"final_sizes={bucket_sizes(res.final)} "
          f"final_cost={res.final_evidence.cost_naive if arm == 'naive' else res.final_evidence.cost_incremental} "
          f"moves={','.join(res.moves) if res.moves else '-'} "
          f"memo_hits={memo.hits} memo_misses={memo.misses} "
          f"wall_s={round(time.time() - t0, 1)}", flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-canary", action="store_true")
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e3_"))
    dest.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        f0, notes, journal, rfix = SMOKE_F0, SMOKE_NOTES, SMOKE_JOURNAL, SMOKE_R
        rider_ttls, max_rounds = (60,), 6
        mode = "smoke"
    else:
        f0, notes, journal, rfix = F0, N_NOTES, JOURNAL, R_FIXED
        rider_ttls, max_rounds = RIDER_TTLS, MAX_ROUNDS
        mode = "full"

    print("=== West-in-kytē E3 — endogenous partition (numbers only) ===", flush=True)
    print(f"mode={mode} seed={SEED} F0={f0} n={notes} p_base={P_BASE} "
          f"J={journal} ttl={TTL} R={rfix} theta={THETA} tol={TOL} "
          f"merge_k={MERGE_K} max_rounds={max_rounds}", flush=True)

    vault = dest / "vault"
    manifest = generate_vault(vault, seed=SEED, folders=f0,
                              notes_per_folder=notes,
                              cross_folder_link_prob=P_BASE,
                              journal_len=journal)
    w1_start, w2_start, w3_start = _starts(manifest, args.smoke)

    memo = MemoEvaluator(vault, manifest, rounds=rfix, ttl=TTL)
    w1 = _run_walk("W1", w1_start, "naive", manifest, memo, dest, max_rounds)
    w2 = _run_walk("W2", w2_start, "naive", manifest, memo, dest, max_rounds)
    w3 = _run_walk("W3", w3_start, "naive", manifest, memo, dest, max_rounds)
    w4 = _run_walk("W4", w1_start, "incremental", manifest, memo, dest, max_rounds)

    # Rider E2b' (spec §5).
    cells, biting = find_biting_regime(vault, manifest, rounds=rfix,
                                       ttls=rider_ttls, ns=RIDER_NS,
                                       theta=THETA)
    for c in cells:
        print(f"rider cell n={c.n} ttl={c.ttl} gap={round(c.gap, 4)}", flush=True)
    print(f"rider biting_ttl={biting}", flush=True)
    quality = None
    if biting is not None:
        quality = run_broker_quality(vault, manifest, n=QUALITY_N,
                                     rounds=rfix, ttl=biting, tol=TOL)
        print(f"rider quality ttl={quality.ttl} rr_cost={quality.rr_cost} "
              f"la_cost={quality.la_cost} rr_cut={quality.rr_cut} "
              f"la_cut={quality.la_cut} rr_routes={quality.rr_routes} "
              f"la_routes={quality.la_routes} material={quality.material}",
              flush=True)
    else:
        print("rider quality skipped (PE4 refuted)", flush=True)

    sweep_max = f0
    rep = assemble_e3_report(w1, w2, w3, w4, cells, biting, quality,
                             tol=TOL, sweep_max_n=sweep_max)
    print(f"priors: {rep.priors}", flush=True)

    canary = "skipped"
    if not args.no_canary:
        fresh = MemoEvaluator(vault, manifest, rounds=rfix, ttl=TTL)
        again = run_meta_walk(w3_start, name="W3c", arm="naive",
                              manifest=manifest, evaluate=fresh.evaluate,
                              theta=THETA, merge_k=MERGE_K,
                              max_rounds=max_rounds,
                              ledger_path=dest / "W3c.jsonl")
        same = (again.moves == w3.moves
                and again.final == w3.final
                and again.final_evidence.cost_naive == w3.final_evidence.cost_naive)
        canary = "PASS" if same else "FAIL"
    print(f"determinism_canary: {canary}", flush=True)

    for name in ("W1", "W2", "W3", "W4"):
        rp = replay_walk(dest / f"{name}.jsonl")
        print(f"replay {name}: ok={rp['ok']} rounds={rp['rounds']}", flush=True)

    print("notes: E3 tests the convergence of THIS walk discipline "
          "(full-slate steepest descent, top-3 link-guided merge shortlist "
          "— proposer attention, disclosed, never adjudication) on the E2b "
          "corpus. PE1 = W1+W2 converge interior within 1.10x the E2b "
          "trough (137,129); PE2 = the three Arm-N walks agree within tol; "
          "PE3 (control) = the Arm-I walk runs to the finest partition — "
          "the interior optimum is the naive coordinator's, not the "
          "walk's; PE4 = decay (ttl) reaches gap>theta at N=4 — the "
          "coherence force via attention-budget saturation, since link "
          "density cannot reach it (E2b PB3); PE5 conditional on PE4 = "
          "link-aware < round-robin under broker-active costing. The "
          "gap-gate refuses candidates, never the incumbent (the N=1 "
          "start is standing-incoherent, gap 0.58, and escapes via its "
          "first accepted split). Broker tax is an end-of-run snapshot "
          "(A3-style lower bound). Arm-N interleaving assumption carries "
          "(verdict-bearing for PE1/PE2). Synthetic corpus, one seed: the "
          "basin structure is the generator's. A meta-Agon is not a "
          "community (THE_COMMENS): this models negotiation inside one "
          "instance. |M|/K2/K3 recorded, never verdict-bearing. K1 = N/A "
          "(raise-only).", flush=True)


if __name__ == "__main__":
    main()
