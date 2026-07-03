# Session 2026-07-03 (3rd sitting) — atom-level decay + semi-naive materialization → duration-probe readiness

The rulebook decision is AFFIRMED (author, 2026-07-03, RUN_4_LOG horizon): **atom-level decay**
— the habit is the fact, not the name; use = re-delivery (first increment); erasure via
`model_revision.retract_atom`; `per_entity_cap` stays as membrane flow-control; per-name cap
rejected. Riding along (correctness-preserving, no affirmation needed): **semi-naive
materialization** against F2⁗'s round-compute wall.

## Build

- [x] 1. Atom-key vocabulary (`agon_evolution.py`): `atom_key` / `parse_atom_key` /
      `sheet_atom_keys` / `delivered_atom_keys` (sheet-level ground atoms of a proposal —
      "use = re-delivery"; a denial refreshes nothing).
- [x] 2. `model_revision.retract_atom` → structural (`without_element` + orphan-vertex prune):
      cut-preserving, so per-atom decay on a sheet carrying laws never silently drops a law
      (the old text-rebuild dropped every cut).
- [x] 3. `agon_evolution.run` ttl path → atom-level: seed/touch/stale/decay per atom
      (touch on every round — a redundant re-delivery is the habit holding);
      `RoundOutcome.decayed` carries atom keys; decay step retracts via `retract_atom`.
- [x] 4. `live_runner.LiveRunner` cross-segment decay → atom-level; laws dropped only when a
      relation *name* vanishes from the sheet; episodes retro-marked atom-precisely
      (`mark_decayed_atoms`); state.json ledger keys are the atom keys (old name-keyed state
      degrades gracefully).
- [x] 5. `tropism.WarmSetTropism.reaches` → atom-precise decay-adjacency (the fact nearest its
      ttl, not the name), name-key fallback for old ledgers.
- [x] 6. `agon_metalearning` — `_last_erasures`/`_stickiness` atom-precise (an atom decaying
      under a surviving name must read decay, not durability); add `mark_decayed_atoms`.
- [x] 7. Semi-naive materialization (`model_materialization.py`): delta-driven fixpoint
      (exact same closure; empty-body rules seeded); rule canonicalization;
      `IncrementalMaterializer` (hit / extension / rebuild, counters observable);
      `peel(materializer=)` + `run(materializer=)` + one per `LiveRunner`;
      `_match_body` kept for `dl_reasoning`.
- [x] 7b. **UNPLANNED, PROFILE-MANDATED — the actual F2⁗ wall:** `canonical_signature`'s WL
      refinement (unshared tree colors; termination check never fired → always |V|+1 rounds)
      dominated round compute via `assert_fact`'s `generate_egif`. Fixed exactly: hash-cons
      colors to canonical rank strings + stop at partition stabilization. 15.7 s → 3.3 ms on
      the 200-atom hub sheet; canonicality canaries pass; module unprotected.

## Verify

- [x] 8. Updated pinned tests (agon_evolution decay → atom keys; live_runner
      warm-name-defeats-decay → the dissolution headline; tropism ordering → atom keys).
- [x] 9. New tests: incremental-vs-full equivalence (growth/retraction/recursive/reparse +
      peel-verdict match); atom-level decay headlines; `mark_decayed_atoms` +
      within-run atom-precise stickiness; atom-precise tropism rotation + name fallback.
- [x] 10. Arc suites green (295 passed, 1 key-gated skip) + core suites (111) + demos clean.
      Post-signature-fix referee: round-trip + correspondence suites (running at wrap; see
      review note).
- [x] 11. Timing: 25-round segment at 200 atoms ~450 s (extrapolated pre-fix) → 2.6 s
      (signature fix) → 1.55 s (+ incremental materializer).

## Duration probe readiness (launch is the author's call, per the pre-registration discipline)

- [x] 12. §16 written: 16.1 rulebook record · 16.2 the F2⁗ decomposition + both riders ·
      16.3 run-5 priors P1⁵–P6⁵ (DRAFT, affirm pre-launch) + runs/RUN_5_LOG.md skeleton +
      driver command (`--source recentchanges --runs-dir runs/run5 --max-seconds 28800`).
- [x] 13. Docs currency: CLAUDE.md (agon_evolution/live_runner/model_revision/
      model_materialization bullets + the canonical-signature note), §10 atom units,
      CURRENT_PLAN session block + NEXT SESSION, memory + MEMORY.md.

## Review

The affirmed rulebook is built verbatim (atom unit, use = re-delivery, retract_atom erasure,
per_entity_cap untouched, per-name cap not built). Two deviations, both surfaced honestly:
(1) `retract_atom` was made structural — the affirmation said "the existing retract_atom",
but the existing one rebuilt M from sheet atoms only, silently dropping every cut; at
atom-decay frequency that latent bug would have bitten any sheet carrying a law. Contract
unchanged (drop exactly one atom), tests pass. (2) The F2⁗ rider grew a second half:
profiling showed the round-compute wall was `generate_egif`'s canonical signatures, not the
peel — fixed exactly (hash-consing, same canonical guarantee, tie-breaks among truly
symmetric elements may differ), with the corpus round-trip + correspondence suites as
referee. In-run decay now also fires on non-revising rounds (⑤ runs every generation, per
the design's loop); previously erasure was deferred to the next revising round.
Run 5 is NOT launched: §16.3's priors are a DRAFT and the discipline is affirm-then-run.
