# Run 4 log — stream + tropism (the F2″ composition: revisit × world-motion)

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §14](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— design + priors P1‴–P7‴ **affirmed by the author 2026-07-03, pre-run**, together with the
run-3 horizon dispositions (atom-unit instruments built · rulebook question deferred to this
run's evidence · attest O(waypoints²) optimized against the seg-17 fixture · spectator surface
still queued). The mandate is RUN_3_LOG F2″: the P2 event needs a value that **changes rank
between two visits** — the stream supplies world-motion (runs 2), the warm set holds the
target standing to meet it (run 3); composed here. With this run the 2×2 closes
(crawl/stream × passive/tropism). Findings are about the game (and Wikidata's editorial
dynamics as represented) — never the world. *Progression, not progress.*

**Driver:** `uv run python tools/run_live_wikidata.py --source recentchanges
--runs-dir runs/run4 --max-seconds 3600` (chunk 8, warm_fraction 0.5 → k=4, per_entity_cap 25,
ttl 30, segment_cap 25, min_interval 5.0, max_m 200, **max_m_atoms 1000** — the new F1″ net).

**Machinery under test (built 2026-07-03, offline-proven in `tests/test_tropism.py` +
`tests/test_live_runner.py`):** the `RecentChangesSource` tropism seam (`inject` front-of-chunk,
`known_labels`, warm_pending persisted; **a quiet stream tick still serves the warm set**) ·
the atom-unit instruments (`m_atoms` digest column, live `atoms=` line, `max_m_atoms` stop) ·
the visibility-graph fix (separation short-circuit + uniform grid + lazy A*; the run3_seg17
fixture: >10 min → 3.8 s). The offline headline: the stream mentions an entity once and moves
on; the world deprecates the admitted value; only the warm re-reach revisits — the denial
meets its **standing** target and is mechanically retracted.

## Session header

| field | value |
|---|---|
| date / operator | *(fill at run)* |
| source | recentchanges (bots excluded), chunk 8, warm_fraction 0.5 (k=4), per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 |
| stops configured | max_seconds 3600 · max_m 200 (names) · max_m_atoms 1000 (atoms — first live outing) · STOP file |
| code version (git SHA) | *(fill at run)* |

**Totals:** *(segments · rounds · polls · checkpoints attested · tropism counters ·
determinism canary)*

## P7‴ first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | < 0.2 (labels lag fresh edits; 0.09 in the run-2 smoke) | | |
| checkpoints §3.3-attest, side store | all | | |
| \|M\| bounded — in BOTH units | names ≈ ttl; atoms visible in the digest (`m_atoms`), net at 1000 | | |
| **attest-cost rider, re-measured** | segment elapsed tracks round compute (run 3: attest ≈ 100 % of wall-clock, 3.3 → 1075 s; the fixture now loads in 3.8 s) | | |
| warm plumbing counters | `warm_injected` > 0; skips counted, never silent | | |
| statements_dropped / unparseable_dropped | counted | | |

## Priors P1‴–P6‴ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1‴ tropism works on the stream | `non_revising` + warm counters | non-revising > 0 (run 2: zero); presence, not magnitude | | | |
| P2‴ **the P2 event, live** | `mechanism_principles`, decay-aware | retract_fact > 0 with the target standing; consensus < 1.0 once overturns occur; a zero = a rate finding, not a machinery finding | | | |
| P3‴ atoms, the honest unit | digest `m_atoms` vs `m_relations` | atoms ≫ names under warm pinning; the atoms-per-warm-name profile = the deferred rulebook decision's evidence | | | |
| P4‴ true:negation, both sides | `gaps` | with-target → retract, without-target → inert, consistently | | | |
| P5‴ attribution (the 2×2 closes) | vs run 2 (tropism effect) and run 3 (source effect) | redundancy/retracts vs run 2 = tropism; contestation mix vs run 3 = source (expect reliable_source-heavy to survive) | | | |
| P6‴ poise, read honestly | `poise_from_digests` | fewer dead segments than run 2 (quiet ticks serve the warm set); ○ read against `non_revising` | | | |

## Findings (dated, disposed)

*(each: prior · evidence · meta-disposition · why / what it changes)*

## Artifacts

`runs/run4/polls.jsonl` (offline replay — the canary input) · `runs/run4/checkpoints/`
(attested UoDs) · `runs/run4/state.json` + `frontier.json` (resume state) ·
`runs/run4_console.txt` (live console)

## Horizon

*(fill at disposal: the rulebook decision on P3‴'s evidence; rigidity-at-exhaustion /
higher warm_fraction probe; the spectator surface, still queued)*
