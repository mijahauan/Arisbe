# Rung 1 — the attention economy on the arithmetic world (design spec)

**Date:** 2026-07-17 · **Status:** approved design, pre-implementation ·
**Design-of-record context:** `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` §3 (rung 1,
authorized with pre-registered criteria S1–S5) · **Author decisions taken:** staging =
arithmetic → vault → author-as-oracle; scope = 3 pieces (economy scoring, frontier
feedback, musement pole; horizon register waits for the vault stage); architecture =
world-agnostic attention socket + arithmetic as world #1.

## Purpose

Build the economy-of-research ordering of reaches — doubt-directed, noise-guarded
attention — as a **world-agnostic socket**, and prove it on a deterministic
computed-arithmetic world where severity is measurable. The socket (`AttentionEconomy` +
`ProbeDirectedFeed`) is the deliverable the vault and author-as-oracle stages reuse; the
arithmetic world is the falsifiable harness.

## Non-goals (this cycle)

- No horizon register (waits for the vault, where illegibility is real).
- No LLM roles (Stage-0 mechanical throughout; the panel is the existing mechanical one).
- No changes to protected modules, `agon_evolution.run`, `QueryDocket`, or `LiveRunner`.
- No live run — CI-deterministic only. (A live-runner wrapping is possible later; the
  feed is a standard `Proposer`.)
- No vault/Obsidian code of any kind.

## Component 1 — `src/attention_economy.py`

Geometry-free, unprotected, no imports from web/layout.

**`Want`** (dataclass): `kind: str` (e.g. `"docket"`, `"frontier"`, `"musement"`, or a
world-specific kind like `"extend_range"`, `"counterexample_hunt"`, `"confirm_low"`,
`"coin"`), `key: tuple` (identity for dedup), `payload: Any` (world-opaque), `cost: float`
(declared by the source/world; default 1.0), `created_round: int`, `attempts: int`,
`last_yield_round: Optional[int]`.

**`AttentionEconomy`**:
- `register(want)` — dedup by `(kind, key)`; bounded register (`max_wants`, drops counted
  in `dropped`, never silent).
- Intake adapters (pure functions in the same module):
  - `wants_from_docket(docket: QueryDocket) -> list[Want]` — wraps `open_entries()`
    (docket internals untouched).
  - `wants_from_episodes(episodes) -> list[Want]` — `agon_metalearning.unresolved_frontier`
    + `friction_map` outputs become `"frontier"` wants (the feedback edge).
- `choose(k: int, round: int) -> list[Want]` — the scorer:
  - Per-kind yield statistic `Y[kind]`: exponentially decayed mean of yield events per
    probe of that kind (decay factor `yield_decay`, default 0.8). Yield events (fed via
    `observe`): a refutation/counterexample, an M-changing disposition, a docket
    settlement attributable to the probe.
  - Score = `(Y[kind] + prior) / want.cost`, `prior` small (default 0.05) so an unprobed
    kind is explorable but cannot outrank a proven one. Per-want attempt penalty:
    score × `attempt_decay**attempts` (default 0.7) — a want re-probed without yield
    sinks (the noisy-TV guard at want granularity; `Y[kind]` decay is the guard at kind
    granularity).
  - Tie-break: fewest attempts → oldest (`created_round`) — the docket's existing Q1 rule,
    preserved for continuity.
  - **Musement reservation:** `ceil(ε·k)` slots (default `ε=0.1`) filled from
    `"musement"`-kind wants ordered by recency-of-novelty; boredom detector — after
    `boredom_rounds` (default 5) consecutive all-kind zero-yield rounds, ε temporarily
    doubles (capped 0.5), decaying back one step per yielding round.
  - Deterministic: no RNG, no wall clock; musement selection is index-arithmetic on the
    round number.
- `observe(round, want, yield_events: int)` — updates `Y`, attempts, boredom state.
- `snapshot() -> dict` — per-kind stats, ε history, register size, dropped count (the
  run-log legibility surface).
- **Failure posture:** any internal error inside `choose` degrades to the tie-break
  ordering alone (mechanical fallback, same pattern as `LLMAgonothetes`); never raises
  into the loop.

## Component 2 — `src/arithmetic_world.py`

**`ArithmeticWorld`**: bounded ℕ (constant labels `"0"`, `"1"`, …, `str(n_max)`),
vocabulary `even/1, odd/1, prime/1, square/1, fermat_number/1, coin/1`.
- `atoms_for(n) -> list[str]` — EGIF ground atoms, computed + cached. Primality by trial
  division (F5 = 4 294 967 297 factors at 641 — cheap).
- `coin(n)`: deterministic patternless bit (parity of the digit sum of `n·2654435761`
  mod a prime) — atoms exist, no stable law is derivable (the planted noisy TV).
- `probe_cost(n) -> float` — proportional to trial divisions needed for `n` (severity is
  expensive; this is what the economy must justify).
- `test_law_instance(law_egif, n) -> Verdict` — instance check by computation.
- Probe execution returns **facts and/or a denial** `~[ (P n) ]` when computation refutes
  a standing law's instance — the world's resolution, disposed by the existing mechanical
  panel (`ContradictionAgent`/Challenger via `seed_laws`), exactly the resolving-membrane
  shape.
- Range growth is **selected, counted**: `range_cap`, per-round `probe_budget`, drops
  counted (`§1.1` discipline).

**`ProbeDirectedFeed`** (implements `agon_evolution.Proposer` —
`propose(model, round_idx) -> Optional[str]`, one EGIF per round): holds `world`,
`economy`, `docket` (a `QueryDocket`), an internal proposal queue, and a drain-or-refill
round loop:
1. On `propose`, first read yield from the **model delta** since the previous call (the
   Proposer's only lawful window): atoms appeared → a probe's fact was admitted; a seeded
   law vanished → refutation landed. `economy.observe(...)` with these events
   (round-granular attribution, noted honestly).
2. If the queue is empty: intake (docket wants + frontier wants + world musement
   candidates), `economy.choose(k=probe_budget, round)`, execute the chosen probes
   against the world, and queue the resulting facts/denials. **Frontier wants are
   cross-run feedback**: `agon_metalearning` episodes exist post-run, so a feed is
   constructed with a prior run's `unresolved_frontier`/`friction_map` output (the
   test drives two short runs, the second steered by the first's frontier — the honest
   shape, matching how the live runner accumulates episodes across segments).
3. Emit the next queued proposal (or `None` when the world/budget is exhausted).
- Seed: the **Fermat conjecture** law + a small pool of true-law candidates (via
  `MutationProposer`-style recombination over the unary vocabulary) so the Generalizer
  has material.
- **Journal:** every probe (round, want, cost, outcome digest) appended as JSONL;
  `replay(journal)` re-drives the feed offline — the determinism canary.

## Data flow (one round)

```
docket wants ─┐
frontier wants ─┼→ AttentionEconomy.choose(k) → probes → ArithmeticWorld (compute)
musement cands ─┘                                        ↓ facts / denials
        agon_evolution.run round ← one proposal per propose(model, round_idx)
                └── model delta read on next call → economy.observe (yield)
                    · docket.observe(model) · episodes accrue (post-run for frontier wants)
```

## Success criteria (pre-registered in BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3)

S1 economy beats FIFO & random on probes-to-Fermat-refutation (`run_ablation`, fresh
feeds/arms, fixed budget) · S2 `coin` kind decays below productive kinds · S3 a planted
off-docket regularity found only with musement on · S4 identical configs → identical
trajectories + journal replay · S5 zero protected-module changes; polarity gate green;
all growth channels bounded with drops counted.

## Tests

`tests/test_attention_economy.py`: scoring math (yield/cost ordering); kind decay
(noisy-TV at kind level); attempt decay (want level); musement reservation + boredom
spike + decay-back; frontier adapter (a contested episode → a want); dedup + bounded
register with counted drops; degrade-to-mechanical on injected scorer error;
determinism (two identical sequences → identical choices).

`tests/test_arithmetic_world.py`: atom correctness (incl. F5 composite, coin
determinism); cost monotonicity; law instance verdicts; feed round-trip (probe → denial →
Challenger relinquishes the Fermat law); **the S1 ablation headline**; S3 musement
ablation; journal replay (S4); the produced UoD persists + passes the polarity gate (S5).

## Integration & docs (end of build)

- No API changes anywhere else; the feed is a `Proposer` like every membrane.
- BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3: build record + criteria disposition (which of
  S1–S5 held, honestly).
- CLAUDE.md: two module lines; CURRENT_PLAN: item update; memory topic file.

## Risks / open points

- If S1's margin is small (FIFO gets lucky on a short range), widen `n_max` so cheap
  re-confirmation genuinely starves FIFO — the criterion is *strictly fewer probes*, no
  margin requirement.
- Yield attribution (which probe caused a disposition) is approximate at round
  granularity; acceptable for S1–S3, noted honestly in the doc.
- The vault stage will need `Want.payload` to carry NL/note references — kept opaque now
  precisely so that lands without socket change.
