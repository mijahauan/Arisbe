# Run 9 log — forecast-centered bins + per-arm instrumentation (NWS weather) — LAUNCHED 2026-07-09

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §20](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the successor to run 8's F2⁸/F3⁸. Run 8 established that at the 20 °F band-cap the
re-generalized temperature law settles into a **positive-net limit cycle**, not a fixed point,
and that the precip arm stayed **dormant** the whole run. Run 9 turns two knobs to interrogate
both: **forecast-centered bins** (does removing grid-edge fragility convert the limit cycle to a
fixed point, or do noisy domains always limit-cycle?) and **per-arm instrumentation** (was precip
well-calibrated, or did its claims rarely mature?). Launch delegated to the author (this
session); priors P1⁹–P4⁹ affirmed as drafted. The seeded theory ("what is forecast, happens")
remains the object under empirical fire; findings are about the game and NWS forecasts as
represented — never the world. *Progression, not progress.*

**Driver (to launch):** `caffeinate -i uv run python tools/run_live_weather.py
--runs-dir runs/run9 --regenerate --bin-mode centered --max-seconds 50400`
(stations KAUS KBOS KDEN KMIA KSEA · horizon 6 h · band 5 °F **centered** · PoP ≥ 60% ·
min_interval 600 s · ttl 48 polls · supervisor + crash/resume armed · re-generalize on,
band-cap 20 °F, pop-cap 90%).

**New machinery under test:** `src/weather_source.py` — `band_bounds` (grid | forecast-centered)
+ `PendingClaim.band_lo` (resolution by half-open containment, mode-independent) + `bin_mode`
knob (carried across resume) + per-arm counters (`claims_raised_by_kind` /
`resolutions_by_kind`); `tools/run_live_weather.py` — `--bin-mode` + per-arm digest (`_per_arm` /
`_fmt_arm`). F1⁸ (`retract_subgraph` structural ERA) already fixed and banked.

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-09 (author, delegated) — launched; running |
| stations · claim kinds | KAUS KBOS KDEN KMIA KSEA · temp bands (5→20 °F, **centered**), precip (PoP ≥ 60%) |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 |
| code version (git SHA) | _(pending launch)_ |

**Totals:** _(pending)_

## Priors P1⁹–P4⁹ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1⁹ **centered bins raise reliability at a given band** (headline) | temp accuracy at a given width exceeds run 8's grid accuracy; the controller widens less (narrower converged band, fewer reseeds) | _(pending)_ | _(pending)_ |
| P2⁹ **fixed point vs limit cycle** | the sharper discretization converts F2⁸'s limit cycle toward a fixed point (reseeds fall, band converges below cap and holds) — or the honest null: a noisy domain still limit-cycles even centered | _(pending)_ | _(pending)_ |
| P3⁹ **per-arm instrumentation disambiguates the dormant precip arm** | the digest resolves F3⁸: precip resolved-many-all-hits (well-calibrated) vs raised-but-rarely-resolved (dormant) | _(pending)_ | _(pending)_ |
| P4⁹ floor + parity unchanged | grid mode reproduces run 8; §3.3 attests; `--resume` carries `bin_mode` + per-arm counters + knobs; correspondence-not-truth holds | _(pending)_ | _(pending)_ |

## Findings (dated, disposed)

_(pending execution)_

---

**Artifacts (on execution):** `runs/run9/items.jsonl` (offline replay) · `runs/run9/checkpoints`
· `runs/run9/state.json` + `weather_state.json` (carried state). See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
