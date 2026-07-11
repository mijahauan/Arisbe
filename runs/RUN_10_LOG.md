# Run 10 log — the live precip arm (the non-binned control) — LAUNCHED 2026-07-10

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— Part III §12 (the ledger); the successor to run 9's F1⁹/F2⁹. Run 9 read the temperature limit cycle (F2⁸) as largely a
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
| date / operator | 2026-07-10 07:13 → 21:20 (14 h 07 m; author, delegated) — **completed on `max_seconds`** |
| stations · claim kinds | KIAH KJAX KMIA KMSY KTPA · temp bands (5→20 °F, **centered**), **precip (PoP ≥ 40 %, gate 40→90)** |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 (self-stopped) |
| code version (git SHA) | 0b74912 |

**Totals:** 18 segments · **183 rounds** · **ledger 30 h / 17 m / 27 a · net +13 · accuracy 0.638**
(resolutions only) · claims raised 109 / resolved 74 / dropped 0 · **fetch_errors 4** (KJAX 1, KMIA 2,
KTPA 1, absorbed + per-station counted, **0 crashes / 0 resumes**) · **13 re-generalizations** · **both
seeded laws still standing at the end** · checkpoints all attested (§3.3, no refusals) ·
poise `● ●●●●●●● ✕✕✕✕ ●●●●●` (8 poised · 4 stumble · 5 recovered).
**Per-arm (F3⁸):** temp raised 100 / resolved 65 · **29 h / 11 m / 25 a · net +18** · acc trajectory
0.00→0.25→0.56→0.60→0.88→0.90→0.85 (band pinned at the 20 °F cap from seg 5, reseeded ~1×/segment to
the end); precip raised 9 / resolved 9 · **1 h / 6 m / 2 a · net −5** · acc 0.14 (gate ratcheted
40→50→60→70→80→90 to the cap on a miss-string, then one late hit).

## Priors P1¹⁰–P4¹⁰ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1¹⁰ **the precip arm activates** | precip raises + resolves claims (> 0) — F2⁹ dormancy lifted | precip raised 9 / **resolved 9** (vs run-9's **zero**) | **CONFIRMED.** The lower gate + wet Gulf/SE stations lift the dormancy; precip finally bets and gets resolved by the world. |
| P2¹⁰ **non-binned: converge or limit-cycle?** (headline) | precip re-generalizes then holds/converges (not a persistent limit cycle); or the null — it *also* limit-cycles (noise, not binning) | **NEITHER — a third outcome.** Precip **monotonically ratchets its one knob to the cap** (gate 40→90), ends **net −5 / acc 0.14, standing-but-mis-calibrated**; temp (also centered) runs a **positive-net limit cycle** (net +18, reseeds ~1×/segment) | **REFRAMED (F1¹⁰).** The pre-registered binary omitted the actual shape. The temp↔precip asymmetry is **knob-type, not binned-vs-non-binned** — see F1¹⁰. Tempers F1⁹ (F2¹⁰). |
| P3¹⁰ **the PoP gate is the precip falsifiability knob** | refutation steps the gate up toward the 90 % cap; a well-calibrated gate holds | the gate **does** step up on every miss (40→90); but at the cap the law "holds" only by **betting rarely** — acc stays 0.14, never calibrated | **CONFIRMED-as-falsifiability-knob, REFINED.** It is a *selectivity / bet-frequency* knob, **not a calibration knob**; "a well-calibrated gate holds" is **FALSIFIED** — it holds by abstaining, not by being right. |
| P4¹⁰ floor + F3⁹ closure | console.txt captured (exact reseed count recoverable); fetch resilience; knobs + `bin_mode` carried; §3.3 attests | console.txt **captured** (13 re-gens + per-segment reseeds legible, **no inference**); **4 fetch_errors absorbed + per-station counted, 0 crashes**; all checkpoints §3.3-attested; no resume needed | **CONFIRMED (F3¹⁰, F4¹⁰).** F3⁹ ops gap closed — the re-generalize / `challenge_to_M` count is now a first-class artifact, not reconstructed. |

## Findings (dated, disposed)

**F1¹⁰ (headline) — the recalibration *knob-type*, not binning, governs whether
refute→re-generalize recovers.** Temp's band-width is a **calibration knob**: widening (5→20 °F)
reaches a regime where the actual usually falls in-band, so the law earns hits (net **+18**, acc → ~0.9).
Precip's PoP gate is a **selectivity / bet-frequency knob**: raising it (40→90 %) only makes precip bet
on higher-confidence forecasts — it **cannot convert a structurally-mismatched "forecast→happens" precip
law into a calibrated one** at this horizon/scoring, so the arm ends net **−5 / acc 0.14**. This is the
disposition of P2¹⁰'s third outcome: a non-binned law under a *selectivity-only* knob **neither converges
to good calibration nor limit-cycles** — it ratchets the knob to the cap and settles net-negative but
standing. **Caveat: precip N = 9 resolutions — directional, not statistically settled**; the *mechanism*
(knob-type) is structural, the *magnitude* is under-powered.

**F2¹⁰ — the F2⁸ limit cycle *decomposes*; F1⁹ is tempered, not overturned.** Run 10's **temp** arm
runs a **positive-net limit cycle even with centered bins** (band pinned at the 20 °F cap, law refelled +
reseeded ~1×/segment to the end) — reproducing F2⁸, *not* run 9's clean fixed point. So the cycle has
**two components**: (a) **grid edge-fragility**, removed by centering — run 9's calmer stations settled to
a fixed point (F1⁹ correct *there*); (b) **genuine domain noise**, which survives centering and resurfaces
on run 10's noisier convective Gulf/SE July stations. Both F2⁸ (the cycle is real) and F1⁹ (centering
helps) are **partly right** — centering removes the artifactual component, not the intrinsic one. The
positive-net cycle is the honest dynamic steady state for a noisy discretized domain (as F2⁸ already read).

**F3¹⁰ — F3⁹ ops closure confirmed.** The `console.txt` tee makes the exact re-generalize count (13) and
per-segment `challenge_to_M` / reseed decisions **first-class and legible** — run 9's inferred-from-miss-
trajectory gap is closed. Disposal here is read directly, not reconstructed.

**F4¹⁰ — fetch resilience held under the 5-station wet constellation.** 4 `fetch_errors` across 3 stations
(KJAX 1, KMIA 2, KTPA 1) were absorbed by the F1⁷ backoff and per-station counted; **0 crashes, 0 resumes**
over 14 h. The noisier/wetter station set did not degrade the run.

**Net for the arc:** run 10 closes the precip control cleanly. The seeded naive theory is **not
relinquished** here (unlike run 7) — the run-8 re-generalize machinery keeps both laws *alive*, but
reveals that *keeping a law alive* and *making it accurate* are different: temp's knob does both, precip's
knob does only the former. The live-run resolving arc's open question for a **next** precip probe: give the
precip arm a *calibration* knob (e.g. bin PoP into forecast-centered probability bands, or condition on
lead-time), not just a selectivity gate — the F1¹⁰ prediction is that a calibration knob would let precip
recover the way temp does.

---

**Artifacts:** `runs/run10/console.txt` (the digest stream — F3⁹, 18 segments + final summary) ·
`runs/run10/items.jsonl` (16 recorded polls, offline replay) · `runs/run10/checkpoints` (index +
literature + universes, all §3.3-attested) · `runs/run10/state.json` + `weather_state.json` (carried
state: both laws, ledger, docket). See [runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
