# Run 1 log — the first live session (Wikidata, rotating frontier)

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §11](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— read it before filling anything in. Every finding below is read **against a prior that predates
the run**, and disposed with the game's own taxonomy at the meta level. *Progression, not
progress* governs the wording; findings are about the wiki-world-as-represented and about the
game — never the world.

**Driver:** `uv run python tools/run_live_wikidata.py --seeds … --max-seconds …`
(clean stop: `touch runs/run1/STOP`; after a kill: `--resume`).

## Session header

| field | value |
|---|---|
| date / operator | |
| seeds · chunk · frontier_cap · crawl | |
| ttl · segment_cap · min_interval_s | |
| stops configured (max_seconds / max_rounds / max_m) | |
| code version (git SHA) | |
| supervised first hour done? stop-file exercised? kill+resume exercised? | |

## P7 first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | ≈ 0.00 throughout | | |
| checkpoints §3.3-attest, land in side store | all | | |
| \|M\| bounded, per-segment elapsed flat | ≈ ttl; flat | | |
| resume continues (numbering, decay clock, frontier) | if exercised | | |
| frontier_dropped | reported, not silent | | |

*Any violation halts interpretation of P1–P6 until explained.*

## Priors P1–P6 — observed vs expected

| prior | instrument | expected | observed | meta-disposition* | note |
|---|---|---|---|---|---|
| P1 disposition mix | digest `dispositions` | ≥90% new_fact; retract rare; challenge/generalization ≈ 0 | | | |
| P2 mechanism durability | `mechanism_principles(res.episodes)` | reliable_source ≥ consensus; unresolved never durable | | | |
| P3 working set | digests `m_relations`/`decayed` | \|M\|≈ttl by seg 2–3; majority decay-erased | | | |
| P4 resolution principles | `resolution_principles`/`gaps`/`friction_map` | zero thrash, zero gaps, friction ≈ 0 | | | |
| P5 dialog shape | `proposal_shape` over episodes | ground/negation only; branched = 0 (monological baseline) | | | |
| P6 poise | `poise_from_digests` | mostly ●; rigidity late if any; ✕ ≈ 0 | | | |

\* meta-disposition (from §11): confirmed prior → `redundancy`/`theorem_registration` ·
surprise inside the frame → `new_fact`/`generalization` about game-with-source ·
contradicted prior → `challenge_to_M` against the prior/rulebook ·
unsettled oddity → entertained, low warrant (horizon, for run 2).

## Findings (dated, disposed)

<!-- one entry per finding:
### F1 — <one line>  (YYYY-MM-DD)
prior: P_  · evidence: <instrument + numbers> · meta-disposition: <from the table>
why / what it changes:
-->

## Horizon (carried to run 2)

<!-- oddities entertained but not settled; candidate recentchanges-API questions -->
