# Run 5 log — the duration probe (overnight unattended stream + tropism) — SKELETON, pre-registered

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §16](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the atom-level decay rulebook + semi-naive materialization + the canonical-signature fix
BUILT 2026-07-03 (offline-proven); run priors P1⁵–P6⁵ **AFFIRMED as drafted by the author
2026-07-03, pre-launch**. The mandate is RUN_4_LOG
F1⁗: the P2 event is a rank-*transition* event with a base rate below the one-hour horizon even
under revisit × world-motion — duration is the cheapest lever, and the F2⁗ round-compute wall
that would have choked an overnight run is dealt with (atom-decay bounds the sheet in the honest
unit; the incremental materializer keeps round compute flat). Findings are about the game (and
Wikidata's editorial dynamics as represented) — never the world. *Progression, not progress.*

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_wikidata.py --source
recentchanges --runs-dir runs/run5 --max-seconds 50400` (chunk 8, warm_fraction 0.5 → k=4,
per_entity_cap 25, ttl 30, segment_cap 25, min_interval 5.0, max_m 200, max_m_atoms 1000).
**Amendment recorded pre-launch (author, 2026-07-03):** `max_seconds` 28800 → **50400 (14 h)**
— start ~15:00 local, self-stop just before 05:00 so the author reads results on rising;
duration is the very lever the probe pulls, all other knobs as affirmed. Supervised the first
~15 min; STOP file available but not expected to be needed; `--resume` after any crash.

**Machinery under test (built 2026-07-03, offline-proven):** atom-level disuse-decay
(`UsageLedger` in `atom_key` units; use = re-delivery; erasure via the structural
`retract_atom`; F1″ pinning dissolved — `test_atom_level_decay_dissolves_the_warm_hub_name_pinning`)
· atom-precise tropism decay-adjacency · atom-precise stickiness (`mark_decayed_atoms`) ·
semi-naive `IncrementalMaterializer` (counters in the final console summary) · **the
canonical-signature fix** (§16.2 — profiling found F2⁗'s dominant term was
`generate_egif`'s WL refinement, not the peel: 15.7 s → 3.3 ms on the 200-atom hub sheet,
~4800×; a 25-round segment at 200 atoms now ~1.5 s).

## Session header

| field | value |
|---|---|
| date / operator | |
| source | recentchanges (bots excluded), chunk 8, warm_fraction 0.5 (k=4), per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 |
| stops configured | max_seconds 28800 · max_m 200 · max_m_atoms 1000 · STOP file |
| code version (git SHA) | |

**Totals:** _segments · rounds · polls · checkpoints attested · dispositions · tropism counters ·
materializer (rebuilds/extensions/hits) · poise strip_

## P5⁵ first — the unattended operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| checkpoints §3.3-attest, side store | all | | |
| legibility per poll | < 0.2 sustained | | |
| canary (offline replay of a prefix) | green | | |
| crash/resume (if exercised) | decay clock continues | | |

## Priors P1⁵–P4⁵, P6⁵ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1⁵ the P2 event at duration | `mechanism_principles` + retract count | ≥1 rank transition on a warm-held target in ~8 h; a zero = a measured rate ceiling | | | |
| P2⁵ sheet bounded in atoms | `m_atoms` digest + net | stabilises ≈ ttl-scaled; net never fires; F1″ not reproduced | | | |
| P3⁵ round compute flat (F2⁗) | segment `elapsed_s` + materializer counters | no super-linear tail; extensions ≫ rebuilds | | | |
| P4⁵ tropism at atom precision | warm counters + `non_revising` | warm set rotates by atom age; counters exact; texture persists | | | |
| P6⁵ poise at duration | `poise_from_digests` | quiet hours served by the warm set; ○ = genuine lulls | | | |

## Findings (dated, disposed)

_(none yet)_

## Artifacts

`runs/run5/polls.jsonl` · `runs/run5/checkpoints/` · `runs/run5/state.json` + `frontier.json` ·
`runs/run5_console.txt`

## Horizon

- **§15 gate re-examined on this run's disposal** (duration before content direction).
- Rigidity-at-exhaustion (carried from runs 2–4): the small-frontier / high-warm-fraction probe.
- The spectator surface (RATE_AND_INTELLIGIBILITY + ADAPTIVE_SCOPE_VIEWER §10): still queued.
