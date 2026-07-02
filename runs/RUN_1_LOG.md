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
| date / operator | 2026-07-02 · author + Claude (supervised sitting) |
| seeds · chunk · frontier_cap · crawl | Q42 Q7259 Q937 · 8 · 400 · on · per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 |
| stops configured (max_seconds / max_rounds / max_m) | 3600 s per sitting · — · 200 |
| code version (git SHA) | 74b4a90 |
| supervised first hour done? stop-file exercised? kill+resume exercised? | YES (both sittings supervised) · YES (STOP after segment 8 → clean `stop_file` exit) · YES (`--resume` continued as segments 9–12; frontier, decay clock, global counters intact) |

**Totals:** 2 sittings · 12 segments · **300 rounds** · 3 polls · 432 statements fetched (427
disputes; 2362 statements capped by `per_entity_cap`, counted) · 12 checkpoints, all
§3.3-attested. **Determinism canary green:** the offline replay of `polls.jsonl` reproduced the
live trajectory exactly (298 revising + 2 inert).

## P7 first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | ≈ 0.00 throughout | 0.00, 0.00, 0.00 | ✓ |
| checkpoints §3.3-attest, land in side store | all | 12/12, `runs/run1/checkpoints`, no refusals | ✓ |
| \|M\| bounded, per-segment elapsed flat | ≈ ttl; flat | \|M\| 13–30 (ttl 30) ✓ · elapsed **not flat**: 3.5 s → 593 s, bounded oscillation tracking pre-decay atom count | ◐ → F1 |
| resume continues (numbering, decay clock, frontier) | if exercised | exercised: segments 9–12, rounds 200→300, crawl continued | ✓ |
| frontier_dropped / statements_dropped | reported, not silent | 0 frontier drops (cap 400 not reached) · 2362 statements capped, counted | ✓ |

*The elapsed deviation (F1) is wall-clock, not correctness — every attest passed — so it does
not poison P1–P6; it is disposed below as a finding against the §10 capacity model.*

## Priors P1–P6 — observed vs expected

| prior | instrument | expected | observed | meta-disposition* | note |
|---|---|---|---|---|---|
| P1 disposition mix | digest `dispositions` | ≥90% new_fact; retract rare; challenge/generalization ≈ 0 | 298/300 rounds `new_fact` (100% of revising); 2 inert (redundancy); retract/challenge/generalization = 0 | confirmed → `redundancy` | zero retracts is the P2 story, not a P1 deviation |
| P2 mechanism durability | `mechanism_principles` over full-run episodes | reliable_source ≥ consensus; unresolved never durable | reliable_source 1.0 (n=82) · consensus 1.0 (n=237) — **vacuous**: 1 deprecated in 432 statements, 0 overturns fired | **untested** → entertained (horizon) | see F2/F3 — the sample carried almost no contestation |
| P3 working set | digests `m_relations`/`decayed` | \|M\|≈ttl by seg 2–3; majority decay-erased | \|M\| 13–30 from seg 1 on; 234/319 episodes (~73%) decay-erased, counted not folded in | confirmed → `redundancy` | |
| P4 resolution principles | `resolution_principles`/`gaps`/`friction_map` | zero thrash, zero gaps, friction ≈ 0 | one principle: `false:ground → new_fact`, stability **1.0**, support 298; gaps none; max friction 0.0 | confirmed → `theorem_registration` | the rulebook was not indicted this run |
| P5 dialog shape | `proposal_shape` over episodes | ground/negation only; branched = 0 (monological baseline) | ground 426 · negation 1 · law/counterexample/unparseable 0 · branched 0 | confirmed → `redundancy` | the monological-ingestion baseline is now on record |
| P6 poise | `poise_from_digests` + `poise_report` | mostly ●; rigidity late if any; ✕ ≈ 0 | 12/12 segments ● ; episode-level poised_fraction 1.00, 0 stumbles | confirmed, with a caveat | predicted late rigidity did not appear — the frontier (cap 400) was nowhere near exhausted at 300 rounds; the prediction stands for a longer run |

\* meta-disposition (from §11): confirmed prior → `redundancy`/`theorem_registration` ·
surprise inside the frame → `new_fact`/`generalization` about game-with-source ·
contradicted prior → `challenge_to_M` against the prior/rulebook ·
unsettled oddity → entertained, low warrant (horizon, for run 2).

## Findings (dated, disposed)

### F1 — checkpoint attest dominates wall-clock and tracks M's shape, not just |M| (2026-07-02)
prior: P7 · evidence: per-segment elapsed 3.5 s → 593 s against < 1 s of round compute;
isolated *pre-run* via the recorded-polls replay to `save_uod_with_chain`'s §3.3 attest — the
ELK ligature router's visibility graph had no spatial pruning, and a Wikidata entity's M is a
star graph · meta-disposition: **`challenge_to_M` against the §10 capacity model — partially
relinquished before the run** (the exact bbox quick reject, 451.8 s → 3.2 s at ~50 atoms;
`per_entity_cap` bounding the hub at the membrane), residual carried (elapsed still oscillates
135–593 s at run-1 scale).
why / what it changes: the §10 capacity table now carries the *shape rider*; the residual —
the visibility graph's O(waypoints²) pair loop — is a named open engineering issue. Correctness
was never at stake (every attest passed); this is an economy-of-research parameter.

### F2 — overturn visibility is working-set-relative (2026-07-02)
prior: P2 (and the shape of the dialog) · evidence: the feed's single `deprecated` statement
arrived as a denial whose target atom was **not standing** in M at that moment (never admitted,
or already decayed) — the ContradictionAgent correctly abstained and the round disposed *inert*
(situation `true:negation`: under the closed world the denial already held) ·
meta-disposition: **`new_fact` about game-with-source** (M-game enlarges).
why / what it changes: under disuse-decay, a relinquishment only *bites* when the working set
still holds its target — so mechanism-durability findings are conditioned on the source's
revisit rate relative to ttl. Run 2's design must ensure denials meet their standing targets
(recentchanges delivers the deprecation *and* its context together; or the frontier must
re-poll entities whose facts M currently holds).

### F3 — the capped crawl sample carries almost no contestation (2026-07-02)
prior: P2 · evidence: 1 deprecated / 0 admin / 0 unresolved in 432 statements (~0.2%);
both mechanisms' stick-rates 1.0 vacuously · meta-disposition: **entertained (horizon)** —
P2's ordering is neither confirmed nor refuted; it was not exercised.
why / what it changes: `per_entity_cap` takes an entity's *first N* statements, and Wikidata
orders claims by property — deprecated ranks and edit wars live disproportionately in the tail
and in *recent activity*. The rotating crawl characterizes the wiki-world's settled surface;
its disputes live in the change stream. This is the strongest argument yet that **run 2 =
`recentchanges`** is where the interesting evidence is.

### F4 — the game's rulebook was not indicted; the baseline is on record (2026-07-02)
priors: P1 · P3 · P4 · P5 · P6 · evidence: one resolution principle (`false:ground → new_fact`,
stability 1.0, support 298), zero thrash/gaps/friction, shapes ground+1 negation, branched 0,
poise 12/12 ● with zero stumbles, |M| pinned by ttl, ~73% of episodes decay-erased (counted) ·
meta-disposition: **confirmed → `redundancy`/`theorem_registration`**.
why / what it changes: run 1 establishes the **monological-ingestion baseline** §11 wanted —
the reference against which the directed-engagement (tropism) build and the LLM-roles runs
will be measured. A run this clean is load-bearing precisely because it is boring.

## Horizon (carried to run 2)

- **P2 entire** — mechanism durability needs contested evidence; the crawl's settled surface
  cannot supply it (F3). Run 2: the `recentchanges` adapter.
- **Denial/target timing** (F2) — run 2 should deliver a relinquishment *with* its standing
  context, or the frontier should revisit held entities; otherwise overturns keep reading inert.
- **Rigidity-at-exhaustion** (P6's caveat) — untested at 300 rounds against a 400-id frontier;
  a longer unattended run (or a small frontier on purpose) would exercise the rigidity pole and
  the stumble/recovery machinery for real.
- **Attest wall-clock residual** (F1) — the visibility graph's pair loop; engineering, named.
