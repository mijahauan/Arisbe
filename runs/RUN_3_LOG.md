# Run 3 log — crawl + tropism (the warm-set re-poll)

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §13](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— design + priors P1″–P7″ **drafted and affirmed by the author 2026-07-02** (all five open
decisions as drafted: `source.inject(ids)` seam · decay-adjacent priority · `warm_fraction`
0.5 fixed · crawl + tropism · ambiguous labels skip + count). The mandate is RUN_2_LOG F2′:
neither passive membrane ever revisits, so mechanism durability (P2) was vacuous twice —
*ingestion alone cannot test durability; only directed re-engagement can.* Findings are about
the game (and Wikidata's editorial dynamics as represented) — never the world. *Progression,
not progress.*

**Driver:** `uv run python tools/run_live_wikidata.py --runs-dir runs/run3 --max-seconds 3600`
(frontier source; `--warm-fraction` defaults to 0.5 → k=4 of the 8-id chunk warm; add
`--warm-fraction 0` to reproduce the run-1 passive baseline).

**Machinery under test (built 2026-07-02, offline-proven in `tests/test_tropism.py`):**
`src/tropism.py` (`WarmSetTropism` — M's standing facts → entity ids via the reversed
`LabelCache`, decay-adjacent first; ambiguous/unmapped labels skipped + counted) ·
`RotatingWikidataSource.inject` (front-of-queue, `_seen`-exempt, counted, resume-safe) ·
`LiveRunner(tropism=…)` (one consult per poll boundary). The two offline headlines: a warm
re-delivery reads as a **non-revising round** (the habit holding), and a deprecation arriving
on a warm re-reach **meets its standing target** and is mechanically retracted — the P2 event.

## Session header

| field | value |
|---|---|
| date / operator | *(fill at run)* |
| source | frontier crawl, seeds *(fill)*, chunk 8, warm_fraction 0.5 (k=4), per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 *(confirm at run)* |
| stops configured | max_seconds · max_m 200 · STOP file |
| code version (git SHA) | *(fill)* |

## P7″ first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | < 0.2; sustained rise = degradation | | |
| checkpoints §3.3-attest, side store | all | | |
| \|M\| bounded; elapsed bounded | ≈ ttl; **hub-degree rider**: the warm set concentrates polls on held entities — a star-shaped M is the attest's worst case (the 140× fix helps; `per_entity_cap` drops counted) | | |
| warm plumbing counters | `warm_injected` > 0 per digest; `ambiguous_skipped`/`unmapped_skipped` counted, never silent | | |
| statements_dropped / unparseable_dropped | counted | | |

## Priors P1″–P6″ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1″ the revisit works | digest `non_revising` / episodes | non-revising (redundancy) ≫ 0 — the structural fraction runs 1–2 measured at zero. If ≈ 0 at warm_fraction 0.5, the warm-set recovery is broken (labels not reversing, or ids not reaching the fetch) — an implementation finding, not a world finding | | | |
| P2″ durability, finally populated (**the run's question**) | `mechanism_principles`, decay-aware | retracts > 0 live; consensus stick-rate < 1.0 once overturns occur; reliable_source ≥ consensus — a reversal is a genuine discovery; `decay_erased` reported, not folded in | | | |
| P3″ the ledger under re-poll | digest `m_relations`/`decayed` | warm re-polls touch held facts' relations → decay concentrates on what the tropism *doesn't* choose; \|M\| still ≈ ttl; a working set pinned by re-poll rather than arrival order is the intended change | | | |
| P4″ true:negation, for free | `gaps` | denials meeting standing targets consistently retract; denials without a standing target consistently inert; inconsistency = a rulebook gap | | | |
| P5″ attribution | vs the run-1 baseline (F3′) | the passive baseline replicated across two sources, so any departure — redundancy fraction, retract rate, a second resolution principle — is attributable to the tropism, not source variance | | | |
| P6″ poise, read honestly | `poise_from_digests` | redundancy-heavy windows depress engagement — read ○ against the `non_revising` count (the *normal* case now); the warm/fresh mix is the structural guard against the all-warm rigidity loop | | | |

## Findings (dated, disposed)

*(fill at run)*

## Horizon

*(carried from RUN_2_LOG: true:negation consistency wants denials actually delivered — the
tropism is the delivery mechanism; rigidity-at-exhaustion wants a deliberately small frontier —
note an injection **revives** an exhausted frontier, so the all-warm loop is now reachable on
purpose; attest wall-clock residual.)*
