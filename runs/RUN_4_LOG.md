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
| date / operator | 2026-07-03 09:33–10:33 · author + Claude (supervised sitting, full hour) |
| source | recentchanges (bots excluded), chunk 8, warm_fraction 0.5 (k=4), per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 |
| stops configured | max_seconds 3600 (**fired**) · max_m 200 (names; never fired at 14–43) · max_m_atoms 1000 (atoms — first live outing; never fired at ≤207) · STOP file available, unexercised |
| code version (git SHA) | 8b037ad |

**Totals:** 1 sitting · **92 segments · 2009 rounds · 23 polls** (2085 recorded statements
post-cap) · 92/92 checkpoints §3.3-attested to the side store · **~4.8× run 3's round
throughput in the same hour** (423 → 2009 — the visibility-graph fix moved the attest wall;
see F2⁗). **Tropism counters:** `warm_emitted=88 injected=88 ambiguous_skipped=0
unmapped_skipped=0` (4 per poll boundary from poll 2 on, exactly k=4 as configured).
**Dispositions:** `new_fact` 1371 · `non_revising` **638 (31.8 %** — vs run 3's 23.6 % on the
crawl**)** · retract/generalization/challenge 0. **Mechanism episodes (decay-aware):**
consensus n=1186 stick 1.0 `decay_erased=709` · reliable_source n=820 stick 1.0
`decay_erased=484` · deprecated n=3 stick None durable False. Poise **88 ● / 4 ○**.
**Determinism canary GREEN on the verified prefix:** the streaming offline replay reproduced
live segments **1–41 exactly** (rounds + dispositions, zero mismatches) before the
supervision budget ended it — and per-segment replay compute ≈ live elapsed (the replay has
no checkpoints, no attest, no network: seg 27 = 36.4 s replay vs 42.4 s live), which is
F2⁗'s decomposition measured directly. The full 92-segment replay is itself compute-bounded
by the very cost F2⁗ names — the prefix is the honest read.

## P7‴ first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | < 0.2 (labels lag fresh edits; 0.09 in the run-2 smoke) | 0.13–0.29 over the first 13 polls (5 polls above 0.2, oscillating not rising), then **falling to 0.00–0.08** as the cache warmed — the trend is the healthy direction | ✓ (with note: the 0.2 line is poll-local lag on a fresh cache, not degradation) |
| checkpoints §3.3-attest, side store | all | 92/92, `runs/run4/checkpoints`, no refusals | ✓ |
| \|M\| bounded — in BOTH units | names ≈ ttl; atoms visible in the digest, net at 1000 | names 14–43 (ttl 30) ✓ · **atoms visible all run** (25 → 207 max), net never fired — the F1″ instrument did its job: the atom pile-up is now *watched*, not silent | ✓ |
| **attest-cost rider, re-measured** | segment elapsed tracks round compute (run 3: attest ≈ 100 %) | **Attest confirmed cheap live**: post-run load-attest seg10/50/92 = 0.5 / 1.5 / **1.7 s at 195 atoms** (run 3: 1075 s at 135). But segment elapsed still grew 1.3 s (first-10 avg) → **125 s** (last-10 avg): the wall MOVED from attest to **round compute** → F2⁗ | ◐ → F2⁗ |
| warm plumbing counters | `warm_injected` > 0; skips counted, never silent | 88 = 88, both skip counters 0, k=4 per boundary exactly | ✓ |
| statements_dropped / unparseable_dropped | counted | 133 capped (hub entities, counted); unparseable 0 (the run-2 parse gate never fired) | ✓ |

## Priors P1‴–P6‴ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1‴ tropism works on the stream | `non_revising` + warm counters | non-revising > 0 (run 2: zero); presence, not magnitude | **CONFIRMED, stronger than the crawl: 638/2009 = 31.8 %** (run 3: 23.6 %), arriving in the same warm-shaped waves (full 24–25/25 segments at injection boundaries), counters exact (88=88, zero skips) | `theorem_registration` | the seam ported to the stream cleanly; the quiet-tick-serves-warm-set semantics kept the texture continuous |
| P2‴ **the P2 event, live** | `mechanism_principles`, decay-aware | retract_fact > 0 with the target standing; a zero = a rate finding, not a machinery finding | **Zero events — the pre-registered rate branch fires.** All 3 deprecated deliveries were **born-deprecated** (each arrived in the same poll as its rank-siblings, on first visit; none was a rank *change* between visits). 88 revisits × an hour of stream motion did not catch a mid-flight flip | `challenge_to_M` against the one-hour horizon, **not** against the machinery (offline the composition retracts — `test_stream_plus_tropism_composition_delivers_the_p2_event`) | → F1⁗: the P2 event is a *rank-transition* event; its base rate at chunk 8 / 1 h is below 1. The composition is correct and starved — the duration lever (a multi-hour unattended run, crash/resume proven) is the named next probe |
| P3‴ atoms, the honest unit | digest `m_atoms` vs `m_relations` | atoms ≫ names under warm pinning; the profile = the rulebook decision's evidence | **CONFIRMED: atoms 25 → 207 max against names 14–43** (≈5–7× and growing); the net (1000) never fired; the instrument read the pile-up live, in-console, all run | `new_fact` about the game | the rulebook evidence is in: growth is steady accumulation under warm names, not a hub blow-up (per_entity_cap 25 held hub degree; 133 drops counted) — see F2⁗ for why atoms now also *cost* |
| P4‴ true:negation, both sides | `gaps` | with-target → retract, without-target → inert, consistently | **Weak side only, again, consistently:** all 3 born-deprecated denials inert (target never standing — correct under the closed world). The with-target case never arose live (that is P2‴'s zero) | `redundancy` (the rule held; the interesting case is still starved) | the offline tests remain the only witnesses of the retract path — three runs running |
| P5‴ attribution (the 2×2 closes) | vs run 2 (tropism effect) and run 3 (source effect) | redundancy vs run 2 = tropism; contestation mix vs run 3 = source | **CONFIRMED both margins:** vs run 2 (same source, passive): non-revising 0 → 31.8 % — tropism. vs run 3 (same tropism, crawl): mechanism mix flipped to the stream's shape (reliable_source n=820 vs consensus n=1186 — richer in referenced values than the crawl's settled surface), deprecations present (3 vs run 3's 1 statement) — source | `theorem_registration` | the 2×2 is closed; every cell has a measured run behind it |
| P6‴ poise, read honestly | `poise_from_digests` | fewer dead segments than run 2; ○ read against `non_revising` | **88 ● / 4 ○** across 92 segments; no dead stretches (the quiet tick serving the warm set kept every window engaged); the 4 ○ fall in low-throughput slices, not redundancy waves | `redundancy` + a small `new_fact` | ● through 24–25/25 non-revising segments replicates run 3's P6″ surprise at stream scale |

## Findings (dated, disposed)

### F1⁗ — the P2 event is a rank-*transition* event, and its base rate is below the one-hour horizon even under revisit × stream (2026-07-03)
prior: P2‴ · evidence: 2085 statements / 23 polls / 88 warm revisits produced 3 deprecated
deliveries, **all born-deprecated** (each delivered in the same poll as its rank-siblings, on
the entity's first visit — `polls.jsonl`, entities "Roman Rudenko" and "The Literary Society
of Gräfelfing"). Nothing changed rank *between* two visits within the hour. The composition's
machinery is not in question — offline, a rank change between visits retracts through the
whole driver path (`test_stream_plus_tropism_composition_delivers_the_p2_event`, plus the
driver-level smoke) — the live world simply did not supply a transition inside the window.
meta-disposition: **`challenge_to_M` against the one-hour horizon, not the machinery.** The
pre-registered "a zero is a rate finding" branch fires: what runs 2–4 have jointly measured is
that *observable* rank transitions (deprecation landing on a value the run already admitted)
are rarer than chunk 8 × 1 h can sample, even when recency-selection and directed re-reach
stack the odds.
why / what it changes: the levers are now enumerable, all pre-registrable: (a) **duration** —
the multi-hour/overnight unattended run (crash/resume, STOP, checkpoints, tripwires all
proven; the cheapest lever and the §11 design's original intent); (b) **width** — a larger
chunk / higher ids_per_poll samples more of the stream's motion per poll; (c) **content
direction** — probes aimed at *contested* regions rather than whatever moved (the §15 docket's
mandate question — this run does NOT yet mandate it, because the starvation is in the world's
transition rate, not in probe aiming; a longer run must first show whether duration alone
suffices).

### F2⁗ — the wall moved: attest is fixed, round compute is the new super-linear cost (2026-07-03)
prior: P7‴ (the attest rider) · evidence: post-run load-attest of the checkpoints reads
**0.5 s / 1.5 s / 1.7 s at 73 / 142 / 195 atoms** (run 3: 1075 s at 135 — the visibility-graph
fix, confirmed live at run scale by 92 segments · 2009 rounds vs run 3's 17 · 423 in the same
hour). But segment elapsed still climbed 1.3 s → ~125 s (first-10 vs last-10 average) as the
sheet grew to ~200 atoms — with attest at ~2 s, essentially all of the late-segment cost is
**per-round compute**: the peel re-materializes M every round and `ProofChain` snapshots the
whole graph per step, both super-linear in *atoms* (the §10 capacity model's units problem,
F1″, now with the attest layer peeled off).
meta-disposition: **`challenge_to_M` against §10's remaining cost model** — "decay keeps
per-round cost flat" was true in name-units and attest-dominated regimes; under tropism the
atom-unit sheet grows and round compute inherits the super-linearity attest used to mask.
why / what it changes: sharpens the **deferred rulebook question exactly as hoped** — atom-level
decay (or a per-name atom cap) would bound precisely the unit that now costs wall-clock; the
run-4 atoms profile (steady accumulation under warm names, 25 → 207, hub degree already capped
at 25) is the evidence the author decision was waiting for. Engineering alternatives that
avoid the rulebook (incremental materialization; a ProofChain that snapshots deltas rather
than whole graphs) are real but second-order: the honest question remains what *one fact's
disuse* means under a warm name.

## Artifacts

`runs/run4/polls.jsonl` (23 polls / 2085 statements — the canary input) ·
`runs/run4/checkpoints/` (92 attested UoDs; run4_seg92 = the ~200-atom round-compute
fixture) · `runs/run4/state.json` + `frontier.json` (resume state) · `runs/run4_console.txt`
(live console)

## Horizon

- **The rulebook decision, now evidence-backed (F2⁗ + P3‴):** what is *one fact's* disuse
  under a warm name — atom-level decay vs per-name atom cap. Deferred pre-run by the author
  (one variable at a time); F2⁗ upgraded it from hygiene to the binding cost model (round
  compute is super-linear in exactly the unit name-decay cannot bound). The run-4 atoms
  profile (steady accumulation, 25 → 207, hubs already capped) is the decision's evidence.
  Engineering second-orders (incremental materialization; delta-snapshot ProofChain) noted in
  F2⁗, subordinate to the rulebook question.
- **The duration lever (F1⁗):** the P2 event's base rate is below the 1-hour horizon — the
  named probe is a **multi-hour/overnight unattended stream+tropism run** (crash/resume, STOP,
  tripwires, checkpoints all proven; the F2⁗ round-compute wall argues for deciding the
  rulebook first or accepting slower late segments).
- **Rigidity-at-exhaustion** (carried from runs 2–3): the deliberate small-frontier /
  high-warm-fraction probe; still open, cheaper now that segments are fast.
- **The spectator surface** (RATE_AND_INTELLIGIBILITY + ADAPTIVE_SCOPE_VIEWER §10): still
  queued, unaffirmed. Run 4 sharpened its layout-budget rider the good way (attest fixed →
  frame cost falls with it).
- **§15 pre-registered during this run** (the §13 pattern — the design predates its mandate):
  [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §15](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md) — **the
  docket of doubts**, the two-faced surprise artifact (outward: content-directed membrane
  queries on a Q1–Q4 vocabulary ladder; inward: the abduction seed whose deduced consequences
  return as probes via a proving-ground DAG branch). Its **mandate gate is this run's
  disposal**: build increment 2a only if the findings name content-undirected probing (or
  UNKNOWN starvation) as the operative bottleneck. **Gate verdict (F1⁗): NOT fired by this
  run** — the starvation is the world's transition rate, not probe aiming; the duration lever
  is cheaper and must be tried first. §15 waits without prejudice; five author decisions
  remain queued there.
