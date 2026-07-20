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
import random
import secrets
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import EvolutionResult, run      # noqa: E402
from attention_economy import AttentionEconomy, Horizon  # noqa: E402
from oracle_notes import (                           # noqa: E402
    DEFAULT_BUDGET, OracleLedger, bank_answer_step, bankable_outcomes,
    candidates_from_run, conjectures_section, note_substantially_answered,
    opaque_note_qid, parse_note, reask_candidate, render_note,
    resolve_note_qids, seal, select_within_budget,
)
from probe_feed import _model_signature              # noqa: E402
from proof_authoring import ProofChain                # noqa: E402
from tomos_service import TomosService                # noqa: E402
from universe_of_discourse import UoDCategory         # noqa: E402
from vault_world import VaultFeed, VaultWorld         # noqa: E402
from world_scroll import find_world_scroll            # noqa: E402


# -- the P2^13 instrument's docket adapter (docket item 10) ------------------------
#
# The vault loop has no ``QueryDocket`` (Q1 entity-reach is a Wikidata-shaped
# vocabulary — labels reversing to Q-ids — that doesn't fit a vault's
# note/journal/scan wants). Its actual "docket" IS the ``AttentionEconomy``'s
# own ranked want pool from the just-finished segment. ``EconomyDocket``
# wraps that pool to the shape ``oracle_notes``/``attention_economy.
# wants_from_docket`` read (``.open_entries``, each entry's ``.payload`` a
# ``(ref, reason)`` pair) — the minimal honest wiring, not a re-derived
# ranking: ``economy.choose`` (the economy's real scoring) decides the
# order, this class only describes each chosen want in one legible line.


@dataclass
class _EconomyEntry:
    key: tuple
    age: int
    attempts: int
    payload: tuple   # (ref, reason)


def _describe_want(w) -> Tuple[str, str]:
    """(ref, reason) for one ``AttentionEconomy`` ``Want`` — legible enough
    to ask "what is this?" about, without leaking which arm asked (the
    caller controls that separately)."""
    if w.kind == "scan":
        return w.payload, "a folder scan the attention economy has queued"
    if w.kind == "read":
        return w.payload, "flagged for a closer read"
    if w.kind == "journal":
        relpath, idx = w.payload
        return f"{relpath} (batch {idx})", "a journal batch queued for reading"
    return str(w.payload), "flagged by the attention economy"


class EconomyDocket:
    """Docket item 10's ``docket=`` argument for ``candidates_from_run``:
    the segment's ``AttentionEconomy``, wrapped. ``economy.choose`` is
    called ONCE, for every want the economy holds (``len(economy.wants())``
    — nothing is cut before ``wants_from_docket`` gets to see it), which
    DOES increment ``.attempts`` on the underlying wants; that side effect
    is harmless here because this ``economy`` is discarded once the oracle
    cycle finishes (the driver never reuses it for another round)."""

    def __init__(self, economy: AttentionEconomy):
        ranked = economy.choose(len(economy.wants()), 0)
        self._entries = [
            _EconomyEntry(key=w.key, age=0, attempts=w.attempts,
                          payload=_describe_want(w))
            for w in ranked
        ]

    @property
    def open_entries(self) -> List[_EconomyEntry]:
        return self._entries


FIXTURE_ROOT = (
    Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "vorago_fixture"
)

ASKED_WINDOW_NOTES = 6
"""Docket item 11, charge 1: the driver's default ``asked_ever`` window — a
question asked within the last 6 distinct note dates stays suppressed; older
than that it becomes re-eligible (spec thesis 3: silence lowers priority,
never deletes)."""


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


def _digest(model_egi, horizon: Horizon, economy: AttentionEconomy,
            feed: Optional[VaultFeed] = None) -> dict:
    """Aggregate counts only — reused from ``probe_feed._model_signature`` (the
    same sheet-atom reading the round loop itself uses) rather than re-deriving
    a second atom walk. No id/title/path ever appears in the return value.
    Docket item 11, charge 4: ``m_added``/``m_removed`` (the feed's cumulative
    added/removed atom split for this segment — churn under ttl decay, which
    the standing totals alone hide) when a ``feed`` is passed."""
    atoms, cuts = _model_signature(model_egi)
    tally = Counter(rel for rel, _labels in atoms)
    # F1¹³ invariant, observable: the longest constant that actually entered M
    # (must stay ≤ vault_world._MAX_CONST or the layout occlusions return).
    max_const = max(
        (len(lab) for _rel, labels in atoms for lab in labels if lab), default=0)
    out = {
        "m_atoms": len(atoms),
        "m_cuts": cuts,
        "max_const_len": max_const,
        "notes_seen": tally.get("note", 0),
        "journal_entries": tally.get("journal_entry", 0),
        "entries_per_decade": _decade_counts(atoms),
        "horizon": horizon.snapshot(),
        "ledger": economy.snapshot(),
    }
    if feed is not None:
        out["m_added"] = feed.added
        out["m_removed"] = feed.removed
    return out


def _run_segment(
    root: Path, rounds: int, seg_idx: int, runs_dir: Path, model,
    ttl: int,
) -> Tuple[dict, object, VaultWorld, Horizon, EvolutionResult, AttentionEconomy]:
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon)

    uod_id = f"vault_v0_seg{seg_idx}"
    res = run(
        model, feed, rounds=rounds, uod_id=uod_id,
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

    digest = _digest(res.uod.current_egi, horizon, economy, feed=feed)
    digest["digested_labels"] = len(world.long_labels)
    # M carries between segments as the graph itself (docket ④): EGIF cannot
    # express per-cell vertex privacy or a banked quotation's sort, so a text
    # carry would merge constants shared across sibling cells.
    # world/horizon/res/economy carried out too — the oracle cycle (last
    # segment only) needs the actual objects the round loop drove, not fresh
    # ones (docket item 10: the economy IS the P2^13 instrument's docket).
    return digest, res.uod.current_egi, world, horizon, res, economy


def _bank_author_model(runs_dir: Path, ledger: OracleLedger, res) -> dict:
    """V2a.2 item (2): rebuild the cumulative author-model UoD from the
    ledger and save it as a side-store checkpoint.

    The recomputation thesis: the ledger is the durable store; the
    author-model is a REBUILT view of it, never incrementally mutated — so
    this runs every oracle pass regardless of whether the pass also wrote a
    new note (an early-return cycle, e.g. "no questions this cycle" or a
    same-day re-poll, may still have just recorded a fresh answer into the
    ledger, and that answer belongs in the model on THIS pass, not the
    next). Each banked answer becomes one explicit, gate-replayable
    ``BANK_TO_M`` chain step (``oracle_notes.bank_answer_step``).

    Never crashes the oracle pass: ``res.uod.current_egi`` is already
    resident (the loop opens residence before this ever runs), but a
    missing world-scroll is handled defensively — banking is skipped and
    counted rather than raising. Numbers-only return: a count, never a qid
    or answer text (custody)."""
    rows = bankable_outcomes(ledger)
    if not rows:
        return {"banked": 0}
    if find_world_scroll(res.uod.current_egi) is None:
        return {"banked": 0, "bank_skipped": len(rows)}
    pc = ProofChain(res.uod.current_egi)
    for row in rows:
        pc = bank_answer_step(
            pc, row["answer_text"], qid=row["qid"],
            note_date=row.get("answered_note_date", ""))
    chain, uod = pc.to_uod(
        uod_id="vault_v0_author_model",
        name="Vault author-model (V2a.2 banked answers)",
        description="The cumulative author-model: every answered oracle "
                     "question banked as a quoted attributed cell, rebuilt "
                     "from the ledger each oracle pass (recomputation "
                     "thesis). One BANK_TO_M step per answer.",
        category=UoDCategory.DOMAIN_MODEL)
    TomosService(runs_dir).save_uod_with_chain(uod, chain)
    return {"banked": len(rows)}


def _run_oracle(root: Path, runs_dir: Path, fixture: bool, note_date: str,
                 run_id: str, segment: int, world: VaultWorld, horizon: Horizon,
                 res, nonce_factory: Callable[[], str] = lambda: secrets.token_hex(8),
                 p213: bool = False, economy: Optional[AttentionEconomy] = None,
                 rng: Optional[random.Random] = None,
                 ) -> dict:
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
    3. Build candidates (suppressing anything the ledger asked within the
       last ``ASKED_WINDOW_NOTES`` distinct note dates — docket item 11:
       older questions become re-eligible, never deleted), append at most
       one drift re-ask (``reask_candidate`` — an early answered question
       repeated verbatim; a changed answer is counted as ``drift_data``),
       budget-select, render, write, and record each asked question (text
       included, so a later re-ask stays verbatim).
    4. V2a.2 item (2): rebuild the cumulative ``vault_v0_author_model``
       side-store UoD from the ledger's latest-answered-per-qid rows
       (``_bank_author_model`` — the recomputation thesis) and save it —
       every oracle pass, regardless of which step above returned early.
       The return dict's ``"banked"`` (``"bank_skipped"`` on the defensive,
       should-never-happen no-residence path) is a COUNT only.

    Docket item 8: a per-question nonce is generated once, at
    candidate-selection time (``nonce_factory``, injectable for deterministic
    tests; the real default is a fresh ``secrets.token_hex(8)`` per
    question), and threaded to BOTH the rendered note's seal and the ledger's
    stored ``forecast_hash`` — the one coupling that must not drift, since
    the note-seal and the ledger-seal need to agree for a later reveal to
    verify at all.

    Docket item 10 (``p213=True``): switches the candidate build to the
    P2^13 falsifiability instrument (``EconomyDocket`` wrapping ``economy``,
    the just-finished segment's ranked want pool) instead of the V2a.1
    provenance/journal/horizon sources, and records each parsed ``**R:**``
    rating into the ledger. This function's OWN keyword default is ``False``
    (an explicit, library-style default for direct callers/tests); ``main``'s
    ``--p213`` CLI flag defaults to ``True`` instead (review finding
    2026-07-19: the pre-registered RUN 13 launch command carries no flag at
    all, so an off-by-default instrument would never actually run — exactly
    the silent-absence charge item ⑩ answers). Pass ``--no-p213`` at the CLI
    to fall back to the V2a.1 mix for a given invocation; a P2^13 note does
    NOT also carry the V2a.1 questions for that cycle (they compete for the
    same budget slots, and the instrument mode replaces rather than merges) —
    alternating ``--no-p213`` runs is how to get both over time. ``rng`` is
    the injectable seeded ``random.Random`` the random arm and the seeded
    shuffle both use (``None`` real-default -> a fresh, unseeded
    ``random.Random()``).

    Numbers-only stdout throughout: the only path ever printed is the note's
    vault-relative name, never a filesystem path (which in fixture mode lives
    under ``runs_dir``, not any real vault)."""
    oracle_dir = (runs_dir / "arisbe_notes") if fixture else (root / "Arisbe")
    oracle_dir.mkdir(parents=True, exist_ok=True)
    ledger = OracleLedger(runs_dir / "oracle")

    budget = dict(DEFAULT_BUDGET)
    reveals: List[dict] = []
    answers_recorded = 0
    drift_data = 0

    prior = sorted(oracle_dir.glob("Questions-*.md"))
    if prior:
        text = prior[-1].read_text(encoding="utf-8")
        # Blinding fix (2026-07-19): a P2^13 note prints opaque qid aliases;
        # translate them back to the real qids the ledger keys everything by
        # (identity on non-aliased/legacy notes).
        parsed = resolve_note_qids(parse_note(text), ledger.note_qid_map())
        if not parsed.budget_parsed:
            print("oracle: budget knob unparsed - using defaults")
        budget = parsed.budget

        # record_outcome_once (not record_outcome): a note that sits
        # partially answered gets re-polled on every invocation, and without
        # dedup each re-poll would re-append the same row and pollute the
        # ledger — see oracle_notes.OracleLedger.record_outcome_once.
        # Docket item 11 (drift): an answer that CHANGED from a previously
        # recorded answer for the same qid (the drift re-ask's whole point,
        # though any hand-edited answer counts too) appends a new row —
        # counted here as drift_data; the first row stays intact.
        for qid, answer in parsed.answers.items():
            had_prior_answer = any(
                o["qid"] == qid and o["status"] == "answered"
                for o in ledger.outcomes())
            if ledger.record_outcome_once(qid, "answered", answer, note_date):
                answers_recorded += 1
                if had_prior_answer:
                    drift_data += 1
        for qid in parsed.declined:
            if ledger.record_outcome_once(qid, "declined", "declined", note_date):
                answers_recorded += 1
        for qid in parsed.ignored:
            ledger.record_outcome_once(qid, "ignored", "", note_date)
        for qid, rating in parsed.ratings.items():
            ledger.record_rating_once(qid, rating, note_date)

        reveals = ledger.build_reveals(parsed)

        if not note_substantially_answered(parsed):
            print("oracle: previous note awaits answers — no new note")
            return {"questions_written": 0, "reveals": len(reveals),
                    "answers_recorded": answers_recorded,
                    "drift_data": drift_data,
                    **_bank_author_model(runs_dir, ledger, res)}

    note_path = oracle_dir / f"Questions-{note_date}.md"
    if note_path.exists():
        # Same-day clobber guard: a re-poll on a date that already has a
        # note (whether still blank or already answered) must never
        # overwrite it — the ledger stays untouched for this skipped write.
        print("oracle: today's note already exists - not overwriting")
        return {"questions_written": 0, "reveals": len(reveals),
                "answers_recorded": answers_recorded,
                "drift_data": drift_data,
                **_bank_author_model(runs_dir, ledger, res)}

    # One rng for the whole cycle (injectable; fresh unseeded is the real
    # default): the P2^13 shuffle AND the two-option order alternation
    # (docket item 11, charge 3) both draw from it, so the live driver's
    # question wording never carries the forecast as a fixed first option.
    r = rng if rng is not None else random.Random()
    if p213:
        docket = EconomyDocket(economy) if economy is not None else None
        candidates = candidates_from_run(world, horizon, list(res.known_laws),
                                          world.labels(), docket=docket, rng=r)
    else:
        candidates = candidates_from_run(world, horizon, list(res.known_laws),
                                          world.labels(), rng=r)
    # Docket item 11, charge 1: a 6-note window, not forever-suppression.
    candidates = [c for c in candidates
                  if not ledger.asked_ever(
                      c.qid, within_last_n_notes=ASKED_WINDOW_NOTES)]
    # The drift re-ask: at most ONE early answered question, verbatim from
    # the ledger's stored text (reask_candidate caps and chooses); dedup by
    # qid in case the window already made the same question re-eligible.
    reask = reask_candidate(ledger)
    if reask is not None and all(c.qid != reask.qid for c in candidates):
        candidates.append(reask)
    selected = select_within_budget(candidates, budget)

    if not selected:
        # Review-mandated guard: never write a note with zero questions.
        print("oracle: no questions this cycle")
        return {"questions_written": 0, "reveals": len(reveals),
                "answers_recorded": answers_recorded,
                "drift_data": drift_data,
                **_bank_author_model(runs_dir, ledger, res)}

    conjectures = conjectures_section(list(res.known_laws), res.discoveries)
    nonces = {c.qid: nonce_factory() for c in selected}
    # Blinding fix (whole-branch review 2026-07-19, IMPORTANT 3): a P2^13
    # qid's own structure (p213:scan:... docket vs p213:<relpath> random)
    # distinguishes the arms in source mode, where the author sees the
    # <!-- qid --> comments. Every p213-shaped question — armed, or a later
    # verbatim re-ask of one (arm=None but the qid keeps its shape) — gets
    # an opaque note-facing alias; the ledger keeps the real qid, joined
    # back through forecasts.jsonl's note_qid at the next parse.
    note_qids = {
        c.qid: (opaque_note_qid(c.qid, nonces[c.qid])
                if (c.arm is not None or c.qid.startswith("p213:"))
                else c.qid)
        for c in selected
    }
    text = render_note(selected, note_date=note_date, run_id=run_id,
                        segment=segment, budget=budget,
                        reveals=reveals or None, conjectures=conjectures,
                        nonces=nonces, note_qids=note_qids)
    note_path.write_text(text, encoding="utf-8")
    for c in selected:
        nonce = nonces[c.qid]
        ledger.record_asked(note_date, c.qid, c.tier, c.forecast,
                             seal(c.forecast, nonce), nonce=nonce,
                             arm=c.arm, segment=segment, text=c.text,
                             note_qid=note_qids[c.qid])

    print(f"questions_written: {len(selected)} → Arisbe/Questions-{note_date}.md")
    return {"questions_written": len(selected), "reveals": len(reveals),
            "answers_recorded": answers_recorded, "drift_data": drift_data,
            **_bank_author_model(runs_dir, ledger, res)}


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
    ap.add_argument("--p213", action=argparse.BooleanOptionalAction, default=True,
                     help="drive the P2^13 falsifiability instrument (docket "
                          "item 10) instead of the V2a.1 provenance/journal/"
                          "horizon question sources: 2 docket-ranked + 2 "
                          "random notes per segment, unlabeled, rated "
                          "trivial/non-trivial by the author. ON BY DEFAULT "
                          "(review finding 2026-07-19: the pre-registered "
                          "launch command has no flag, so an off-by-default "
                          "instrument would never actually run against the "
                          "real vault) — pass --no-p213 to restore the "
                          "V2a.1 provenance/journal/horizon mix instead. A "
                          "P2^13 note does NOT also exercise the V2a.1 "
                          "sources for that cycle; alternate --no-p213 runs "
                          "if you want both.")
    args = ap.parse_args(argv)

    root = FIXTURE_ROOT if args.fixture else Path(args.root)
    runs_dir = Path(args.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    note_date = args.note_date or date.today().isoformat()

    model = ""
    digest: dict = {}
    for seg in range(1, args.segments + 1):
        digest, model, world, horizon, res, economy = _run_segment(
            root, args.rounds, seg, runs_dir, model, args.ttl)
        if seg == args.segments:
            digest["oracle"] = _run_oracle(
                root, runs_dir, args.fixture, note_date,
                run_id=f"vault_v0_seg{seg}", segment=seg,
                world=world, horizon=horizon, res=res,
                p213=args.p213, economy=economy)
        print(f"[segment {seg}/{args.segments}] {digest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
