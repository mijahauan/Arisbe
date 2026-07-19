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
from datetime import date
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import EvolutionResult, run      # noqa: E402
from attention_economy import AttentionEconomy, Horizon  # noqa: E402
from egif_generator_dau import generate_egif         # noqa: E402
from oracle_notes import (                           # noqa: E402
    DEFAULT_BUDGET, OracleLedger, candidates_from_run, conjectures_section,
    note_substantially_answered, parse_note, render_note, seal,
    select_within_budget,
)
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
    # F1¹³ invariant, observable: the longest constant that actually entered M
    # (must stay ≤ vault_world._MAX_CONST or the layout occlusions return).
    max_const = max(
        (len(lab) for _rel, labels in atoms for lab in labels if lab), default=0)
    return {
        "m_atoms": len(atoms),
        "m_cuts": cuts,
        "max_const_len": max_const,
        "notes_seen": tally.get("note", 0),
        "journal_entries": tally.get("journal_entry", 0),
        "entries_per_decade": _decade_counts(atoms),
        "horizon": horizon.snapshot(),
        "ledger": economy.snapshot(),
    }


def _run_segment(
    root: Path, rounds: int, seg_idx: int, runs_dir: Path, model_egif: str,
    ttl: int,
) -> Tuple[dict, str, VaultWorld, Horizon, EvolutionResult]:
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
        ttl=ttl if ttl > 0 else None,
    )

    TomosService(runs_dir).save_uod_with_chain(res.uod, res.chain)

    # Custody sidecar (F1¹³): the id → original decode map for every constant
    # the bound digested — gitignored beside the UoDs; the originals never
    # enter M or stdout.
    if world.long_labels:
        import json
        sidecar = runs_dir / "labels.json"
        existing = {}
        if sidecar.exists():
            existing = json.loads(sidecar.read_text())
        existing.update(world.long_labels)
        sidecar.write_text(json.dumps(existing, indent=1, sort_keys=True))

    digest = _digest(res.uod.current_egi, horizon, economy)
    digest["digested_labels"] = len(world.long_labels)
    next_model_egif = generate_egif(res.uod.current_egi)
    # world/horizon/res carried out too — the oracle cycle (last segment only)
    # needs the actual objects the round loop drove, not fresh ones.
    return digest, next_model_egif, world, horizon, res


def _run_oracle(root: Path, runs_dir: Path, fixture: bool, note_date: str,
                 run_id: str, segment: int, world: VaultWorld, horizon: Horizon,
                 res) -> dict:
    """The V2a.1 oracle cycle (docs/superpowers/plans/2026-07-18-v2a-oracle-notes.md,
    Task 4), run once after the LAST segment only:

    1. Resolve + create the oracle dir: real-vault mode -> ``<root>/Arisbe/``;
       ``--fixture``/test mode -> ``<runs_dir>/arisbe_notes/`` (the fixture
       tree under ``tests/fixtures`` is never written to).
    2. Parse the newest prior ``Questions-*.md`` there, if any: record each
       answer/decline/ignore into the ledger, build reveals, adopt the
       (possibly author-edited) budget knob. A previous note that is not yet
       substantially answered (and hasn't been waved off by deletion) blocks
       a new note this cycle.
    3. Build candidates (suppressing anything the ledger has ever asked),
       budget-select, render, write, and record each asked question.

    Numbers-only stdout throughout: the only path ever printed is the note's
    vault-relative name, never a filesystem path (which in fixture mode lives
    under ``runs_dir``, not any real vault)."""
    oracle_dir = (runs_dir / "arisbe_notes") if fixture else (root / "Arisbe")
    oracle_dir.mkdir(parents=True, exist_ok=True)
    ledger = OracleLedger(runs_dir / "oracle")

    budget = dict(DEFAULT_BUDGET)
    reveals: List[dict] = []
    answers_recorded = 0

    prior = sorted(oracle_dir.glob("Questions-*.md"))
    if prior:
        text = prior[-1].read_text(encoding="utf-8")
        parsed = parse_note(text)
        if not parsed.budget_parsed:
            print("oracle: budget knob unparsed - using defaults")
        budget = parsed.budget

        # record_outcome_once (not record_outcome): a note that sits
        # partially answered gets re-polled on every invocation, and without
        # dedup each re-poll would re-append the same row and pollute the
        # ledger — see oracle_notes.OracleLedger.record_outcome_once.
        for qid, answer in parsed.answers.items():
            if ledger.record_outcome_once(qid, "answered", answer, note_date):
                answers_recorded += 1
        for qid in parsed.declined:
            if ledger.record_outcome_once(qid, "declined", "declined", note_date):
                answers_recorded += 1
        for qid in parsed.ignored:
            ledger.record_outcome_once(qid, "ignored", "", note_date)

        reveals = ledger.build_reveals(parsed)

        if not note_substantially_answered(parsed):
            print("oracle: previous note awaits answers — no new note")
            return {"questions_written": 0, "reveals": len(reveals),
                    "answers_recorded": answers_recorded}

    note_path = oracle_dir / f"Questions-{note_date}.md"
    if note_path.exists():
        # Same-day clobber guard: a re-poll on a date that already has a
        # note (whether still blank or already answered) must never
        # overwrite it — the ledger stays untouched for this skipped write.
        print("oracle: today's note already exists - not overwriting")
        return {"questions_written": 0, "reveals": len(reveals),
                "answers_recorded": answers_recorded}

    candidates = candidates_from_run(world, horizon, list(res.known_laws),
                                      world.labels())
    candidates = [c for c in candidates if not ledger.asked_ever(c.qid)]
    selected = select_within_budget(candidates, budget)

    if not selected:
        # Review-mandated guard: never write a note with zero questions.
        print("oracle: no questions this cycle")
        return {"questions_written": 0, "reveals": len(reveals),
                "answers_recorded": answers_recorded}

    conjectures = conjectures_section(list(res.known_laws), res.discoveries)
    text = render_note(selected, note_date=note_date, run_id=run_id,
                        segment=segment, budget=budget,
                        reveals=reveals or None, conjectures=conjectures)
    note_path.write_text(text, encoding="utf-8")
    for c in selected:
        ledger.record_asked(note_date, c.qid, c.tier, c.forecast, seal(c.forecast))

    print(f"questions_written: {len(selected)} → Arisbe/Questions-{note_date}.md")
    return {"questions_written": len(selected), "reveals": len(reveals),
            "answers_recorded": answers_recorded}


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
    ap.add_argument("--ttl", type=int, default=120,
                     help="disuse-decay ttl in rounds (F1¹³: bounds |M| so the "
                          "segment-save layout stays tractable; 0 disables — "
                          "unbounded M at vault scale makes the save-time layout "
                          "take tens of minutes and risks label occlusion)")
    ap.add_argument("--note-date", default=None,
                     help="ISO date for the oracle note's filename/frontmatter "
                          "(V2a.1); defaults to today — the single sanctioned "
                          "wall-clock read in this driver. Pass explicitly for "
                          "deterministic/test invocations.")
    args = ap.parse_args(argv)

    root = FIXTURE_ROOT if args.fixture else Path(args.root)
    runs_dir = Path(args.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    note_date = args.note_date or date.today().isoformat()

    model_egif = ""
    digest: dict = {}
    for seg in range(1, args.segments + 1):
        digest, model_egif, world, horizon, res = _run_segment(
            root, args.rounds, seg, runs_dir, model_egif, args.ttl)
        if seg == args.segments:
            digest["oracle"] = _run_oracle(
                root, runs_dir, args.fixture, note_date,
                run_id=f"vault_v0_seg{seg}", segment=seg,
                world=world, horizon=horizon, res=res)
        print(f"[segment {seg}/{args.segments}] {digest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
