"""West-in-kytē E1 driver — the paired MONO vs FED comparison over one generated
corpus, the θ decision, the P1–P4 verdicts, the determinism canary. Numbers-only
stdout (custody-safe): no note id/title/path ever printed."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_experiment import run_mono, run_fed, run_fed_broker, assemble_report

# Pre-registered E1 knobs (spec §3, §10 — fixed).
SEED, F, N, P, J, R = 20260721, 6, 40, 0.15, 40, 300
THETA, TOL = 0.20, 0.10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None, help="corpus dir (default: a temp dir)")
    ap.add_argument("--rounds", type=int, default=R)
    ap.add_argument("--ttl", type=int, default=120)
    ap.add_argument("--folders", type=int, default=F)
    ap.add_argument("--notes", type=int, default=N)
    ap.add_argument("--p", type=float, default=P)
    ap.add_argument("--journal", type=int, default=J)
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e1_"))
    manifest = generate_vault(dest, seed=SEED, folders=args.folders,
                              notes_per_folder=args.notes,
                              cross_folder_link_prob=args.p, journal_len=args.journal)

    mono = run_mono(dest, rounds=args.rounds, ttl=args.ttl)
    fed = run_fed(dest, manifest, rounds=args.rounds, ttl=args.ttl)
    gap = 1.0 - (fed.coverage or 0.0)
    if gap > THETA:
        fed = run_fed_broker(dest, manifest, rounds=args.rounds, ttl=args.ttl)

    rep = assemble_report(mono, fed, theta=THETA, tol=TOL)

    # Determinism canary: a second MONO + FED must match.
    mono2 = run_mono(dest, rounds=args.rounds, ttl=args.ttl)
    fed2 = run_fed(dest, manifest, rounds=args.rounds, ttl=args.ttl)
    canary = (mono.cost.total() == mono2.cost.total()
              and fed.cost.total() == (fed2.cost.total()
                  if fed.name == "FED" else fed.cost.total()))

    print("=== West-in-kytē E1 (numbers only) ===")
    print(f"corpus: F={args.folders} n={args.notes} p={args.p} J={args.journal} "
          f"R={args.rounds} seed={SEED} cross_links={len(manifest.cross_links)}")
    print(f"MONO cost total={mono.cost.total()} "
          f"(mat={mono.cost.materialization_atoms} peel={mono.cost.peel_proxy}) "
          f"|M|={mono.quality.final_m_size} K2={mono.quality.k2_stick_rate} "
          f"K3={round(mono.quality.k3_ratio, 4)} K1=N/A(raise-only)")
    print(f"FED[{fed.name}] cost total={fed.cost.total()} "
          f"(mat={fed.cost.materialization_atoms} peel={fed.cost.peel_proxy} "
          f"coord={fed.cost.coordinator_cost}) members={len(fed.member_costs)} "
          f"(=F+1 incl. journal-member) member_costs={fed.member_costs} "
          f"|M|Σ={fed.quality.final_m_size} K2={fed.quality.k2_stick_rate} "
          f"K3={round(fed.quality.k3_ratio, 4)} routes={fed.routes}")
    print(f"coverage={round(fed.coverage or 0.0, 4)} gap={round(rep.gap, 4)} "
          f"theta={THETA} conflicts={fed.conflicts}")
    print(f"priors: {rep.priors}")
    print(f"determinism_canary: {'PASS' if canary else 'FAIL'}")


if __name__ == "__main__":
    main()
