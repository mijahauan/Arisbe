# Run 12 log — sports outcomes (the discrete resolving membrane) — PLANNED 2026-07-12

**Pre-registration.** The weather trilogy (runs 7–11) closed its question: predict → refute →
**re-generalize** works live, and its success condition is the **knob-type law** (AEG Part II
§11.4, twice-evidenced: F1¹⁰ + F1¹¹) — *a refuted theory re-generalizes into a better one only
if its recalibration knob calibrates (moves it toward being right), not merely selects (moves it
toward betting less)*. But both evidences come from one domain with two confounds: weather
**donates a width** (temperature is continuous; even precip's fix leaned on the continuous PoP
signal), and the "forecast" input was **already a skilled model** (NWS) — M calibrated trust in
an expert, it never met raw contingency. Run 12 removes both: **sports outcomes are discrete**
(win/lose — no width anywhere) and adversarial. The question: **is the knob-type law a law of
the game, or a fact about weather?** Findings are about the game and the sources as represented
— never the world. *Progression, not progress.*

## The four arms (what weather structurally could not test)

- **Arm A — the knob-type null.** A naive discrete law with no knob (e.g. *the home team wins*:
  `~[ (home_team *g *t) ~[ (wins t g) ] ]`). The law predicts arm A cannot recover — expect the
  run-10 shape (refuted and trapped/silent), now in a domain with no width to widen. If A
  *recovers*, the knob-type law was under-stated.
- **Arm B — the manufactured calibration knob (headline).** A two-direction bet around a
  **learned cutpoint on a continuous auxiliary signal** — win-percentage differential from the
  standings (the F1¹¹ mechanism transplanted: bet the stronger team when the differential ≥ cut,
  the weaker below it — the "dry law" analog is *the favorite wins*/*the underdog wins*).
  Expected: recovery to positive net — the knob-type law's cross-domain leg.
- **Arm C — competing theories over the same claims.** Three rival seeded laws betting on the
  *same games* — home-wins · higher-win-pct-wins · (optional, keyed) odds-favorite-wins —
  ranked live by `resolving_membrane.select_best`. **This register has never run live**: weather
  had one law per claim kind, so selection-*among*-theories (the §4b Robot-Scientist teeth) is
  still unexercised. Expected ordering: win-pct/favorite > home > naive.
- **Arm D (optional, if time) — law discovery.** Seed nothing; let the Generalizer induce laws
  from the accumulating ledger — stickiness by *origin* (induced vs seeded), a distinction the
  §6 instruments can measure but have never been fed.

**The external-literature check (new for the arc).** Every prior finding was validated only
against its own pre-registration. Arm B/C's learned regularities are checkable against
*documented* ones — MLB home advantage (≈53–54 %), the favorite–longshot bias (if the odds arm
runs). First contact between an induced habit and an independently recorded one — checked in
the correspondence spirit (does the game's habit match the record's?), never claimed as truth.

## Build plan (offline-first, the house pattern)

1. **`src/sports_source.py`** — a `LiveSource` of `ResolvingItem`s over **MLB Stats API**
   (`statsapi.mlb.com` — free, no auth, in-season now, ~15 games/day). Facts per game:
   `(home_team g t)`, `(away_team g t)`, `(winpct_diff …)` (standings-derived, the continuous
   signal); claims raised at scheduled-game time, resolved from finals. Injectable fetch;
   **record/replay JSONL** (the determinism canary): record a played 2026 stretch once, build +
   test fully offline/CI-safe, then the live run swaps the fetch. Postponed/suspended games
   dropped **counted** (grace), never silent.
2. **Calibration controller** — the sports analog of `weather_recalibration.recalibrate`
   (cutpoint on win-pct differential; wet/dry → favorite/underdog; same move-only-on-evidence,
   reseed-fallen-laws contract). Small and additive; reuse the `reseed_laws` runner seam as-is.
3. **Driver `tools/run_live_sports.py`** — clone of `run_live_weather.py` (console tee,
   side-store checkpoints, supervisor + crash/resume, per-arm digest + cut trajectory, STOP
   file), plus `select_best` standings printed per segment (arm C's instrument).
4. **Tests** (offline, mirroring `test_weather_source` / `test_resolving_membrane`): the
   knob-type causal pair (arm A traps, arm B recovers — the F1¹¹ headline test transplanted);
   `select_best` ranks rivals over identical claims; record/replay round-trip; postponement
   grace; controller unit set (cut up/down/hold/reseed).
5. **Cadence note (ops).** Sports resolve in **calendar bursts** (a nightly batch), not an
   hourly stream — first live test of claim-maturation under bursty resolution. A 14 h run
   spans one game day; prefer either a 2–3-day paced run (`min_interval` ~1800 s) or the
   recorded-stretch replay for the first disposal, live after.

**Author decision points:** (a) the odds arm — `the-odds-api` free tier needs a key; without it
arm C runs home vs win-pct only (still a live `select_best` first, and the home-advantage
literature check stands); (b) live-run duration/pacing (one game day vs a multi-day paced run
vs recorded-replay-first).

## Priors P1¹²–P5¹² — pre-registered

| prior | instrument | expected |
|---|---|---|
| P1¹² **the knob-type null holds in a discrete domain** | arm A per-arm net + law standing/reseed trajectory | the no-knob naive law is refuted and does **not** recover (trap or silence — the run-10 shape); its recovery would falsify the knob-type law's necessity half |
| P2¹² **the manufactured calibration knob recovers** (headline) | arm B per-arm net + cut trajectory | the cutpoint moves only on evidence and settles off-cap; arm B crosses to positive net — the law's cross-domain leg. Null: no recovery even with the knob → the law is weather-specific (F1¹⁰/F1¹¹ over-generalized) |
| P3¹² **selection among rival theories is stable** | `select_best` standings per segment (arm C) | a stable ranking emerges (expected win-pct/favorite > home > naive); rank instability under equal exposure is itself a finding (theory-selection thrash) |
| P4¹² **the induced habit meets the literature** | arm B/C learned cut + home-win rate vs documented regularities | home advantage lands near the documented ≈53–54 %; the learned cut is interpretable against favorite–longshot findings (if odds run). First external-literature validation of the arc |
| P5¹² **floor + bursty cadence** | console tee; checkpoints; drop counters | nightly-batch maturation handled (grace; postponements dropped counted); §3.3 attests at every checkpoint; crash/resume continues the cut + ledger |

## Session header

| field | value |
|---|---|
| date / operator | _(pending build + launch)_ |
| source · arms | MLB Stats API (statsapi.mlb.com) · A naive-home / B calibrated win-pct cut / C rival theories + select_best / D optional induction |
| stops | _(pending)_ |
| code version (git SHA) | _(pending)_ |

**Totals:** _(pending)_

## Findings (dated, disposed)

_(pending execution)_

---

**Artifacts (on execution):** `runs/run12/console.txt` · `runs/run12/items.jsonl` (record/replay)
· `runs/run12/checkpoints` · `runs/run12/state.json` + `sports_state.json`. See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
