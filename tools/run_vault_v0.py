"""Vault V0 driver — RUN 13's runnable entry point
(spec: docs/superpowers/specs/2026-07-17-vault-cycle-design.md;
plan: docs/superpowers/plans/2026-07-17-vault-v0-metadata-membrane.md, Task 7).

Drives ``agon_evolution.run`` with a ``vault_world.VaultFeed`` proposer — the
metadata membrane over an Obsidian-style vault — for one or more segments,
saving each segment's resulting UoD+chain via ``TomosService`` and printing an
aggregate digest.

**Custody (binding):** every artifact this driver writes (UoDs, chains, per-note
ids embedded in them) lands under ``--runs-dir`` (default ``runs/run13/``),
which ``.gitignore`` excludes wholesale — nothing derived from the real vault
enters git. The digest printed to stdout per segment is NUMBERS ONLY: counts,
snapshot dicts keyed by *kind*/*reason* strings (never a note id, title, or
path), and |M|. A captured log of this driver's stdout carries nothing that
re-identifies a specific note. Real-vault runs are the author's own act; CI and
agents drive only ``--fixture`` (the synthetic fixture vault under
``tests/fixtures/vorago_fixture``), never ``--root`` against the real vault.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import run                      # noqa: E402
from attention_economy import AttentionEconomy, Horizon  # noqa: E402
from egif_generator_dau import generate_egif         # noqa: E402
from probe_feed import _model_signature              # noqa: E402
from tomos_service import TomosService               # noqa: E402
from vault_world import VaultFeed, VaultWorld         # noqa: E402

FIXTURE_ROOT = (
    Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "vorago_fixture"
)


def _decade_counts(atoms) -> dict:
    """``(entry_date "eid" "YYYY-MM")`` sheet atoms, bucketed by decade — counts
    only; the date bucket is a number, never the entry id or its content."""
    counts: Counter = Counter()
    for rel, labels in atoms:
        if rel != "entry_date" or len(labels) < 2 or not labels[1]:
            continue
        year = labels[1][:4]
        if year.isdigit():
            counts[f"{int(year) // 10 * 10}s"] += 1
    return dict(sorted(counts.items()))


def _digest(model_egi, horizon: Horizon, economy: AttentionEconomy) -> dict:
    """Aggregate counts only — reused from ``probe_feed._model_signature`` (the
    same sheet-atom reading the round loop itself uses) rather than re-deriving
    a second atom walk. No id/title/path ever appears in the return value."""
    atoms, cuts = _model_signature(model_egi)
    tally = Counter(rel for rel, _labels in atoms)
    return {
        "m_atoms": len(atoms),
        "m_cuts": cuts,
        "notes_seen": tally.get("note", 0),
        "journal_entries": tally.get("journal_entry", 0),
        "entries_per_decade": _decade_counts(atoms),
        "horizon": horizon.snapshot(),
        "ledger": economy.snapshot(),
    }


def _run_segment(root: Path, rounds: int, seg_idx: int, runs_dir: Path,
                  model_egif: str) -> tuple[dict, str]:
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon)

    uod_id = f"vault_v0_seg{seg_idx}"
    res = run(
        model_egif, feed, rounds=rounds, uod_id=uod_id,
        name=f"Vault V0 segment {seg_idx}",
        description="Vault V0 metadata-membrane drive (RUN 13); "
                     "see docs/superpowers/specs/2026-07-17-vault-cycle-design.md.",
    )

    TomosService(runs_dir / "universes").save_uod_with_chain(res.uod, res.chain)

    digest = _digest(res.uod.current_egi, horizon, economy)
    next_model_egif = generate_egif(res.uod.current_egi)
    return digest, next_model_egif


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="/Users/mjh/Documents/Vorago",
                     help="vault root (ignored when --fixture is given)")
    ap.add_argument("--rounds", type=int, default=200,
                     help="rounds per segment")
    ap.add_argument("--segments", type=int, default=1,
                     help="number of segments to drive, M carried forward between them")
    ap.add_argument("--runs-dir", default="runs/run13",
                     help="where UoDs/chains land (gitignored — never the corpus)")
    ap.add_argument("--fixture", action="store_true",
                     help="drive the synthetic test fixture (tests/fixtures/vorago_fixture) "
                          "instead of --root — the smoke path; never the real vault")
    args = ap.parse_args(argv)

    root = FIXTURE_ROOT if args.fixture else Path(args.root)
    runs_dir = Path(args.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)

    model_egif = ""
    for seg in range(1, args.segments + 1):
        digest, model_egif = _run_segment(root, args.rounds, seg, runs_dir, model_egif)
        print(f"[segment {seg}/{args.segments}] {digest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
