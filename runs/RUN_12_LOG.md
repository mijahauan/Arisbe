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

## Build — DONE 2026-07-12 (offline-first, the house pattern)

Shipped: **`src/sports_source.py`** (the MLB `LiveSource`; injectable fetch, bounded
retry/backoff, record/replay JSONL, `save_state`/`load_state` carrying pending picks + the
learned cut) · **`src/sports_recalibration.py`** (the cut controller) ·
**`tools/run_live_sports.py`** (driver: console tee, side-store checkpoints, supervisor +
crash/resume, STOP file, per-segment per-arm digest + cut trajectory + `select_best`
standings, final P4¹² home-win-rate line) · **`tests/test_sports_source.py` +
`tests/test_sports_recalibration.py`** (32 offline tests — the knob-type causal pair through
the real `LiveRunner` loop: P1¹² the naive law is refuted and falls silent
(miss→abstain→abstain→abstain, no recovery path exists); P2¹² the calibrated arm is refuted,
the cut moves on evidence, the fallen law reseeds through the runner seam, and it **bets again
and hits**; plus `select_best` ranking, record/replay round-trip, postponement + grace
counters, state round-trip, controller unit set).

Design decisions (within the pre-registration, for the author to affirm at launch):

- **Per-arm vocabularies in one M** (the temp/precip precedent): arm A `pick_naive`/`win_naive`
  (`LAW_NAIVE`), arm C rivals `pick_home`/`win_home` + `pick_strong`/`win_strong`, arm B
  `pick_fav`/`win_fav` + `pick_dog`/`win_dog` around the cut. A miss arrives as
  `(pick_… g t) ~[ (win_… g t) ] (won g winner)` — body + negated head + observed outcome.
- **Arm A carries no mechanism at all** — never recalibrated, never reseeded (there is no
  width; the null is the *absence* of the knob, not a weaker knob).
- **Arm C's rivals are held** — a fallen `LAW_HOME`/`LAW_STRONG` is reseeded *verbatim*
  (`HELD_LAWS`), because the selection register's instrument is the ledger (`select_best`
  over track records), not law standing; holding is not calibration (nothing about the
  rival's claim moves). Arm A remains the standing instrument.
- **Cut units**: win-pct differential in integer thousandths (`.556−.481 → 75`); favorite =
  higher win pct, **tie breaks to the home team**; defaults cut=50, step=25, cap=300, floor
  0 — settling at 0 (*always the favorite*) is a genuine calibration endpoint in a discrete
  domain, and the F3¹¹ discriminator is the cut *trajectory* (moves only on evidence,
  settles), not the endpoint alone.
- **Regular season only** (`gameType == "R"`): sportId=1 also carries the All-Star slate
  (verified live 2026-07-12 — gameType "A"); the theories and the P4¹² literature check are
  regular-season claims.
- **Not built:** arm D induction-from-blank (optional-if-time, per the pre-registration).
- **Decision (a) TAKEN 2026-07-13 — the odds rival is built.** The author supplied a The Odds
  API free-tier key; `pick_odds`/`win_odds` (`LAW_ODDS`, held via `HELD_LAWS_ODDS`) joins arm C
  so `select_best` ranks **five** theories (naive · home · strong · cal · odds). The pick is
  the **bookmaker-consensus favorite** — lower *average decimal price* across the returned
  books' `h2h` markets (`regions=us`); a cross-book tie is skipped *counted*
  (`odds_skipped`); an event with no posted market is retried until ~2 h before first pitch,
  then given up counted; a doubleheader matches its two odds events by nearest commence time
  (≤ 6 h). Quota: free tier 500 req/month; one lazy odds call per poll *only while unclaimed
  games await a pick* (~1–3/game-day — a 3-day run uses ≈ tens). Verified against the live v4
  API 2026-07-13 (list-of-events shape, decimal `h2h`, quota headers; 499 remaining after the
  probe). **The key lives only in the `ODDS_API_KEY` env var / `--odds-key` flag at launch** —
  it rides in the request URL only, never in recorded items, state files, console, or the
  repo (grep-verified). This also arms the P4¹² favorite–longshot half of the literature
  check.

Verified beyond the offline suites: a **live smoke** of the driver against the real API
(2026-07-12 ~22:30 MDT, scratch dir) — clean start/poll/stop/report, zero fetch errors; the
empty slate is *real* (the All-Star break: 0 games 07-13, only the ASG 07-14), and the
schedule/standings payload shapes match the parser exactly (15 finals 07-12 with `isWinner`;
30 teams in standings). Neighboring suites green (101: resolving/live-runner/weather/agon).

**Launch (the author's):** regular-season play resumes **2026-07-16** (1 game) / **07-17**
(full 15-game slate). Recommended (morning of 07-17, or evening 07-16 to catch that day's
single game):

    export ODDS_API_KEY=<the key>
    uv run python tools/run_live_sports.py --runs-dir runs/run12 --regenerate \
        --max-seconds 259200

(3 days ≈ 07-17→07-20 covers ~45 games; pacing 1800 s; STOP file honored; `--resume` after a
kill. Launching earlier works too — it just polls quietly through the break; then prefer
`--max-seconds 604800` so the budget survives to cover three game days.) Decision (a) is
taken (odds rival built, above); decision (b) is the `--max-seconds` choice. Priors
P1¹²–P5¹² below stand as pre-registered, unmodified by the build.

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
| date / operator | built 2026-07-12 (Claude, this session) · launch _(pending — the author's; play resumes 07-16)_ |
| source · arms | MLB Stats API (statsapi.mlb.com) + The Odds API (h2h consensus, keyed) · A naive-home / B calibrated win-pct cut / C rivals home·win-pct·**odds** + select_best / D optional induction (not built) |
| stops | _(pending launch — recommended `--max-seconds 259200`, STOP file)_ |
| code version (git SHA) | the "Run 12 built" commit, 2026-07-12 |

**Totals:** _(pending)_

## Findings (dated, disposed)

_(pending execution)_

---

**Artifacts (on execution):** `runs/run12/console.txt` · `runs/run12/items.jsonl` (record/replay)
· `runs/run12/checkpoints` · `runs/run12/state.json` + `sports_state.json`. See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
