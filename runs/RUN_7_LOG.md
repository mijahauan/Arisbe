# Run 7 log — the first live resolving membrane (NWS weather) — SKELETON, pre-registered

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §18](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the affirmed §15.1 ordering enacted: the first raise-and-resolve source before the
docket's Q2/Q3 tiers. Launch delegated by the author's "Let's proceed" (2026-07-06); priors
P1⁷–P6⁷ drafted with the delegation — amendments welcome at disposal. The seeded theory
("what is forecast, happens") is the object under empirical fire; findings are about the
game and NWS forecasts as represented — never the world. *Progression, not progress.*

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_weather.py
--runs-dir runs/run7 --max-seconds 50400` (stations KAUS KSEA KBOS KDEN KMIA · horizon 6 h
· band 5 °F · PoP ≥ 60% · min_interval 600 s · ttl 48 polls · segment_cap 25 ·
checkpoint_every 1 · supervisor + `checkpoint_refusal=skip` armed).

**New machinery under test:** `src/weather_source.py` (two-phase raise/resolve; pending
claims persisted; recorded batches → offline replay canary) · the n-ary
`_refuted_law`/`_law_signature` generalization · `ResolvingFeed`+`PredictionLedger` at
live scale for the first time.

## Session header

| field | value |
|---|---|
| date / operator | |
| stations · claim kinds | KAUS KSEA KBOS KDEN KMIA · temp bands (5 °F), precip (PoP ≥ 60) |
| horizon · grace · ttl | 6 h · 3 h · 48 polls |
| stops | max_seconds 50400 · max_m 400 · max_m_atoms 2000 · STOP file |
| code version (git SHA) | |

**Totals:** _segments · rounds · polls · claims raised / resolved / dropped · ledger
(hits/misses/abstentions/net/accuracy) · law survival (which fell, at what round, with
what track record) · dispositions · crashes · poise_

## Priors P1⁷–P6⁷ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1⁷ world exercises the registers (headline) | M bets; ≥1 hit + ≥1 miss; first miss → challenge_to_M relinquishes a law | | |
| P2⁷ honest epistemic change | post-fall bets → abstentions | | |
| P3⁷ two arms, independent fates | temp and precip laws fall/survive independently | | |
| P4⁷ floor on a new membrane | resume keeps pending claims; canary replays; drops counted | | |
| P5⁷ two-clock texture | claims from poll 1; first bets ~6–8 polls later | | |
| P6⁷ correspondence floor | all checkpoints attest | | |

## Findings (dated, disposed)

_(none yet)_

## Artifacts

`runs/run7/items.jsonl` (recorded batches — offline replay) · `runs/run7/checkpoints/` ·
`runs/run7/state.json` + `weather_state.json` (pending claims) · `runs/run7_console.txt`

## Horizon

- After disposal: 2a.1 ran in parallel (the docket instrument fixes are BUILT, this run
  doesn't use the docket); the next docket run composes the two membranes' lessons.
- Q2/Q3 tiers: sized by run 6's F2⁶ re-frame, built only after this membrane's disposal.
- 2b (proving ground) · F1⁵ root fix · spectator surface: queued.
