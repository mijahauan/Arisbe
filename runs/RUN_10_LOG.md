# Run 10 log — the live precip arm (the non-binned control) — PRE-REGISTERED

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §21](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the successor to run 9's F1⁹/F2⁹. Run 9 read the temperature limit cycle (F2⁸) as largely a
**grid edge-fragility artifact** of the binning: forecast-centered bins converted it toward a
fixed point. The untested control is the **precipitation** arm — **non-binned** (rain / no-rain, no
bin, no edge-fragility), and dormant through runs 7–9 (PoP never reached the gate — F2⁹). Run 10
activates it (wetter Gulf/SE stations + a lower PoP gate) and asks: does a **non-binned** law,
refuted by the world, **converge/hold**, or does it **also limit-cycle**? Converge → corroborates
F1⁹ (binning drove the temp cycle); limit-cycle → weather noise drives it, tempering F1⁹. The
seeded theory ("what is forecast, happens") remains the object under fire; findings are about the
game and NWS forecasts as represented — never the world. *Progression, not progress.*

**Driver (to launch):** `caffeinate -i uv run python tools/run_live_weather.py
--runs-dir runs/run10 --stations KMIA KTPA KMSY KIAH KJAX --pop-threshold 40 --bin-mode centered
--regenerate --max-seconds 50400` (Gulf/SE July-convection stations · horizon 6 h · temp band
5 °F **centered** · **PoP ≥ 40 %** · min_interval 600 s · ttl 48 polls · supervisor + crash/resume
armed · re-generalize on, band-cap 20 °F, pop-cap 90 %).

**New machinery under test:** `weather_source.WET_STATIONS` / `KNOWN_STATIONS` (a wet Gulf/SE
constellation the driver resolves by ICAO); the F3⁹ **console tee** (`runs/run10/console.txt` —
the per-segment digest is now a first-class artifact, so the exact per-arm reseed /
`challenge_to_M` count is recoverable). The precip arm, PoP-gate recalibration, and per-arm
counters already existed (runs 7–9); this run finally gives them something to contest.

## Session header

| field | value |
|---|---|
| date / operator | _(pending launch)_ |
| stations · claim kinds | KMIA KTPA KMSY KIAH KJAX · temp bands (5→20 °F, centered), **precip (PoP ≥ 40 %, gate 40→90)** |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 |
| code version (git SHA) | _(pending launch)_ |

**Totals:** _(pending)_

## Priors P1¹⁰–P4¹⁰ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1¹⁰ **the precip arm activates** | with the lower gate + wet stations, precip raises and resolves claims (> 0) — F2⁹ dormancy lifted | _(pending)_ | _(pending)_ |
| P2¹⁰ **non-binned: converge or limit-cycle?** (headline) | the precip law re-generalizes by raising the gate then holds/converges — it does *not* persistently limit-cycle like binned temp did before centering; or the honest null: it also limit-cycles (weather noise, not binning) | _(pending)_ | _(pending)_ |
| P3¹⁰ **the PoP gate is the precip falsifiability knob** | refutation steps the gate up toward the 90 % cap (analog of the temp band 5→20); a well-calibrated gate holds | _(pending)_ | _(pending)_ |
| P4¹⁰ floor + F3⁹ closure | the digest is captured to `runs/run10/console.txt` (exact reseed count recoverable); 0-fetch resilience; both knobs + `bin_mode` carried across resume; §3.3 attests | _(pending)_ | _(pending)_ |

## Findings (dated, disposed)

_(pending execution)_

---

**Artifacts (on execution):** `runs/run10/console.txt` (the digest stream — F3⁹) ·
`runs/run10/items.jsonl` (offline replay) · `runs/run10/checkpoints` · `runs/run10/state.json` +
`weather_state.json` (carried state). See [runs/OPERATIONS.md](OPERATIONS.md) for the digest
glossary.
