# Run 6 log — the docket live (§15 · 2a's own run) — SKELETON, pre-registered

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §17](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— increment 2a (the docket of doubts, Q1-only) BUILT + offline-proven 2026-07-05; §15's
five decisions AFFIRMED by the author 2026-07-05 with the source-diversification ordering
amendment (the run after this one is the first live resolving-membrane source). Launch
delegated by the author's "Proceed" (2026-07-05); priors P1⁶–P6⁶ drafted with the
delegation — amendments welcome at disposal. Findings are about the game (and Wikidata's
editorial dynamics as represented) — never the world. *Progression, not progress.*

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_wikidata.py --source
recentchanges --runs-dir runs/run6 --max-seconds 50400 --ttl 8 --ttl-unit polls --max-m 800
--max-m-atoms 2500 --checkpoint-every 5 --docket --docket-asks 2` (chunk 8 ≈ 4 warm + 2
docket asks + 2 fresh; segment_cap 25; min_interval 5.0 — real sleep; supervisor armed,
`checkpoint_refusal=skip`).

**New machinery under test:** `src/query_docket.py` (thin spots → Q1 asks through the
inject seam; settle/age; counted-never-dropped) · `LiveRunner(docket=)` beside the tropism
· `checkpoint_every=5` (F2ᵇ lever (a)) · the F1ᵇ parser collision fix at live scale.

**Amendment recorded mid-run (author, 2026-07-06 ~05:45):** early stop via the STOP file
at **07:30 local** (≈ 11h47m of the configured 14 h) — the author departs on a trip; the
stop leaves time for a clean disposal and session wrap. All instruments read identically
under a stop-file stop; duration-scaled expectations (P4⁶'s poll multiple, P6⁶'s window)
are read pro-rata.

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-05 19:44:32 → 2026-07-06 ~07:31 (11 h 47 m; author-directed STOP file per the recorded amendment) |
| source · strata | recentchanges · warm 4 + asks 2 + fresh ~2 per chunk |
| ttl · segment_cap · checkpoint_every | 8 polls · 25 · 5 |
| stops | max_seconds 50400 · max_m 800 · max_m_atoms 2500 · **STOP file (fired)** |
| code version (git SHA) | 2e64418 (launch) · materializer sibling fix landed mid-run for future runs |

**Totals:** 1,063 segments · 23,891 rounds · **221 polls** (24,149 statements) · checkpoints
every 5th segment, **one refused → skipped + quarantined** (`refused_seg1060.json` — the F1⁵
occlusion coin-flip's first live loss, absorbed exactly as designed) · dispositions all
`new_fact` + warm non-revising rhythm · **docket whole-run ≈ 765 harvested / ≈ 365 resolved
(~48%) / 438 asks / 0 inexpressible** (the final summary shows only the post-crash leg:
289/89/98 — see F1⁶) · tropism+docket injections 1,311 (leg 2) · 1 crash absorbed (the F1ᵇ
**sibling**: `model_materialization`'s facts-builder vertex ids, fixed same morning —
deterministic `v_m{n}`, the scheme its own edge ids already used) · atoms max 1,000 / final
872, nets never fired · poise ● with the poll-cycle ○ rhythm · mechanism principles at
duration-scale n: consensus 3,591 / reliable_source 2,524 durable · deprecated 27 not.

## Priors P1⁶–P6⁶ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1⁶ docket changes delivery (headline) | asks > 0, resolved > 0; zero-resolutions = Q1-ceiling finding | 438 asks emitted + consumed by the seam; ≈365 of ≈765 wants resolved (~48%) — the register demonstrably turns over. **But attribution (ask-driven vs stream-borne resolution) is UNMEASURED — the instrument gap is the finding (F1⁶)**: asks are counted, never *identified* (no ask journal), and the register+counters reset at the supervisor resume | **partially confirmed; attribution deferred to 2a.1** (ask journal + register persistence) — instruments before claims |
| P2⁶ inexpressible sizes Q2 | grows steadily; magnitude = the Q2 case | **0 all run — the expectation was wrong in an informative way**: every wiki thin spot carries a constant grip. The real Q1 residue surfaced elsewhere: `unmapped_skipped=1,034` (leg 2) — grips that exist but **cannot reverse to entity ids** (value-labels: dates, urls, coordinate blobs as a lone atom's constant) | the Q2 case is carried by *unreversible grips*, not gripless wants — re-frame before sizing the tier (F2⁶) |
| P3⁶ composition safety | strata share the seam; warm texture persists | warm + ask injections rode one seam all run (1,311 in leg 2); non-revising warm rhythm persisted; fresh stream never starved | confirmed |
| P4⁶ floor + F1ᵇ + cadence | no collision crash; polls ≥ ~2× 5b; refusals counted | **the parser fix held** (zero parser collisions); 1 crash = the F1ᵇ *sibling* path (materializer facts-builder — found, fixed, committed same morning), absorbed by the supervisor; **the F1⁵ skip-and-count fired its first live refusal** (seg 1060, occlusion) and the run survived; polls 221/11.8 h ≈ **5.7× run 5b's rate** (expected ≥2×) | confirmed — the floor is now battle-tested on all three defenses |
| P5⁶ sheet bounded | sawtooth ≈ run 5b | atoms sawtooth to max 1,000, final 872; neither net fired | confirmed |
| P6⁶ P2 window | any transition → retract; zero = 2nd rate sample | zero transitions; 27 deprecated-mechanism episodes, all born-deprecated, entertained not durable | confirmed-as-zero — the second duration sample of the rate ceiling; the resolving membrane (next) supplies the event class daily |

## Findings (dated, disposed)

### F1⁶ (2026-07-06) — the docket needs an ask journal and a persisted register (2a.1)

The headline prior could not be fully read because the instrument, not the phenomenon,
fell short: asks are **counted but not identified** (no artifact records which entity was
asked for which want at which poll), so ask-driven resolutions cannot be separated from
stream-borne ones; and the register + counters are **per-leg** (the supervisor resume
rebuilt an empty docket; the final summary's 289/89/98 is only the last leg of ≈765/365/438).
**Queued as 2a.1, before the next docket run:** a per-ask journal line (poll · entity ·
want-key · provenance) appended beside `polls.jsonl`, and the register persisted in
`state.json` like the disuse ledger. Also: `deferred=196,990` over-counts (every re-refused
re-harvest of the same want each observe pass) — count distinct wants deferred instead; and
the cap (200) saturated within two polls on wiki content — admission policy (or a larger
cap) is part of the same decision.

### F2⁶ (2026-07-06) — the Q1 residue is unreversible grips, not gripless wants

`inexpressible` (no constant grip) stayed 0: wiki ground atoms always name their entity.
What actually blocks Q1 is `unmapped_skipped` (1,034 in leg 2): grips whose labels the
cache cannot reverse — overwhelmingly *value*-labels (timestamps, identifiers, coordinate
strings) sitting as the lone atom's constant. Two consequences: the docket's grip choice
should prefer the atom's **entity-position** argument (first arg by construction) and skip
value-typed labels at harvest (cheap heuristic, part of 2a.1); and the Q2 tier's case is
re-framed — its value is *asking about a property/shape* precisely where no reversible
entity handle exists.

### F3⁶ (2026-07-06) — the operational floor is now battle-tested end to end

In one run: the F1ᵇ parser fix held at live scale; the F1ᵇ **sibling** surfaced through the
materializer (the one high-volume path the parser fix didn't cover), was absorbed by the
supervisor, and was fixed the same morning; and the F1⁵ **skip-and-count took its first
live refusal** (seg 1060, the occlusion coin-flip at ~900 atoms) — counted, quarantined,
run unharmed. The checkpoint-cadence lever delivered ~5.7× run 5b's poll rate. The
unattended posture is no longer theoretical.

## Artifacts

`runs/run6/polls.jsonl` · `runs/run6/checkpoints/` · `runs/run6/state.json` +
`frontier.json` · `runs/run6_console.txt`

## Horizon

- **Next after disposal (affirmed ordering):** the first live resolving-membrane source
  (weather/sports forecast-vs-actual behind `ResolvingFeed`) — before any Q2/Q3 build.
- 2b (the proving ground) waits as pre-registered.
- F1⁵ root fix (label placement, protected-core design pass) · spectator surface: queued.
