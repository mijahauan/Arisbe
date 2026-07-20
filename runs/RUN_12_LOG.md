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
| date / operator | built 2026-07-12 (Claude) · **executed 2026-07-14 → 07-17 by the author** (PID 28386, `--max-seconds 259200`, ran to its cap) |
| source · arms | MLB Stats API (statsapi.mlb.com) + The Odds API (h2h consensus, keyed) · A naive-home / B calibrated win-pct cut / C rivals home·win-pct·**odds** + select_best / D optional induction (not built) |
| stops | `--max-seconds 259200` → **stopped: max_seconds** (the 3-day cap, as launched) |
| code version (git SHA) | the "Run 12 built" commit, 2026-07-12 (pre-sweep-#2: the run played the level-1 residence regime) |

**Totals (recorded 2026-07-17 from `runs/run12/console.txt` + `state.json`; disposal below is
the author's):** 9 segments · 85 rounds · 144 polls · final |M| ≈ 90 atoms · dispositions
`{new_fact: 85}` (no challenge/retraction fired) · learned cut 225 (seeded 50) ·
re-generalizations 7 · 5 laws standing (one per arm) · poise per segment `● ● ✕ ● ● ● ● ● ●`
(one stumble, absorbed).

**Ledger — and the honest caveat that governs every prior below:** picks **raised=80**,
**resolved=5**, dropped_unresolved=0, postponed=0, odds_skipped=0, **fetch_errors=12
(schedule:12)**. So the whole run produced **one resolution per arm** — net −1, accuracy 0.000
for all five arms, `select_best` "choosing" naive on a 5-way tie at −1. The run is
**evidentially thin**: the raise path worked (80 picks, laws re-generalized, |M| bounded, poise
read), but the *resolution* path — the world's teeth — barely engaged.

## Findings (dated, disposed)

**F0¹² — the run is evidentially thin, and the cause is the ALL-STAR BREAK: the run spent its
whole budget inside it (2026-07-17; the author's hypothesis, confirmed against the run's own
state by Claude).** 80 raised : 5 resolved. The three priors that need resolutions — **P3¹²**
(select_best discriminates between arms), **P4¹²** (home-win rate ≈53–54 % vs the literature;
measured **0.000 over 1** decided home-rival bet), and the ledger half of **P2¹²** — are
**UNDISPOSED**: never given data, so neither confirmed nor refuted. What *is* evidenced:
**P1¹²/P5¹²** — the floor held (9 segments checkpointed and §3.3-attested, crash-free to the cap,
the cut learned 50→225 and carried, decay bounded |M|, poise legible with one absorbed stumble).

**The evidence for the break, from `sports_state.json`:** **all 75 pending claims are dated
`2026-07-17`** — the day play resumes — with `game_time` `2026-07-17T17:35:00Z` and later. The run
started **2026-07-13 07:30** and stopped **~2026-07-17 03:14**, i.e. it opened at the break, found
essentially nothing to bet on for three days (one game resolved: the 5 `challenge_to_M` at
segment 3, all five arms picking the loser — hence 0h/5m and the five-way −1 tie), raised its
first real slate on the resumption day, and **hit its cap ~14 h before those games started**.
Not a bug: an empty world. `unresolved_dropped=0` and `postponed_dropped=0` confirm nothing was
lost — the picks are *still pending*, waiting on games that had not yet been played.

**Correction to this log's first draft (recorded honestly):** the `schedule:12` fetch errors are
**a startup artifact, not a persistent fault**. The console shows `fetch_errors=12` *already at
segment 1* and never incrementing across the following 8 segments — the count is carried in the
state from the run's two false starts (`run start` lines at 06:02 and 06:16 on 07-13, before the
real 07:30 start that added the odds rival). Twelve errors at the beginning, zero thereafter. The
earlier reading ("never moves ⇒ persistent fault") had the inference exactly backwards.

**Disposition — LEG 2 LAUNCHED 2026-07-17 07:52 local (the author), as a FRESH start.** The
recommendation had been `--resume` (to inherit the 75 pending claims + the learned cut + the
ledger); the launched command omitted `--resume`, so `SportsSource` started clean and
`sports_state.json` was overwritten at 07:53. **Verified 13:08Z: this cost nothing evidential,
and bought a cleaner run.** The fresh source **re-raised the same 75 picks** — the identical
resumption slate (75 pending, all `2026-07-17`, earliest `17:35:00Z`), because those games sit
inside the 18 h horizon either way — so tonight's resolutions land as planned (~20:30Z onward).
What was discarded: (a) the learned cut 225→50 — but leg 1's cut was **stepping mechanically**
(50→75→…→225, one +25 per segment) on ~1 resolution, so it encoded noise, and arm B re-learns it
from real outcomes now; (b) leg 1's ledger (0h/5m on a single game) — noise; (c) the 81-entry
disuse ledger — moot, M is rebuilt from tonight's picks. What was gained: **`fetch_errors=0`**
(independently confirming the `schedule:12` were a stale startup artifact carried in state, not a
live fault), and — the real prize — **the regime confound is gone**: leg 2 is a clean, single-regime
run wholly under sweep #2's cells, rather than a chain that changes residence mid-run.

**Leg 2 (running):** `--runs-dir runs/run12 --regenerate --max-seconds 259200`, started
2026-07-17 07:52 local; 75 picks raised across 15 games × 5 arms; cut re-seeded at 50; stop via
the 3-day cap or `touch runs/run12/STOP`. **This is the leg that tests P2¹²/P3¹²/P4¹².**

**Resume verified against this state (2026-07-17):** the carried `model_egif` is *flat*
(pre-sweep-#2), so it meets the new residence code — tested directly: `run()`'s ensure-residence
recognizes it after wrapping (1 cell), `m_view` is `same_graph` to the flat M, and the **81 atom
keys are identical before and after re-housing**, so the ledger and its decay clock survive
exactly (the keys are content-based). The resumed chain opens `DC+ · INS`. One honest confound to
note in any write-up: the run's first leg played the *pre*-sweep-#2 sheet-level regime and the
resumed leg plays cells — the M-content and the ledger are unaffected, but the residence regime
changes mid-run.

**Watch-note, leg 2 near its cap (2026-07-19 20:45 CDT; Claude's observation, not a
disposal — the disposal remains the author's).** The run is alive (PID 11143, caps
2026-07-20 07:52 local) and evidentially rich where leg 1 was thin: **225 raised / 210
resolved / 0 dropped / 10 postponed-dropped**, run ledger net +10; the only pending picks
are the 5 arms on one game (Yankees–Dodgers, started 23:20Z tonight), so the slate should
finish before the cap. The three undisposed priors now have data on the record:
**P3¹²** — `select_best` standings at resolved=210 spread cleanly (odds net=8 acc 0.633 ·
home net=5 acc 0.593 · naive net=1 · strong/cal negative), with the leader having flipped
home↔odds across segments; **P4¹²** — the home arm reads **16h/11m over 27 decided ≈ 0.593**
vs the literature's ≈0.53–0.54 (small n; the author's read); **P2¹²** — the calibrated arm's
cut walked 50→300→275 (first cut-*down* at seg with `acc_dog=0.42`) yet sits last or
next-to-last on net, so the ledger half finally has something to say. **One operational
finding to dispose: a supervisor crash-loop.** Eight crashes since 2026-07-18 ~19:00, each
auto-resumed in 10 s from `sports_state.json` with nothing lost (resolved kept climbing
145→210; `dropped=0` throughout; checkpoints seg18–seg25 all §3.3-saved). **Cause
identified same evening (the author supplied the terminal scrollback; all 8 tracebacks
are ONE bug):** `live_runner._decay` → `world_scroll.retract_from_m` → `ERA apply
failed: Rule rejected: Selected subgraph contains elements not in target area` — the
disuse-decay erasure refused by the licensed rule's target-area guard, and the pre-fix
code let the `AssertionError` escape the segment loop. The condition is the known
**EGIF-carry cross-cell constant merge** (F2¹³'s family): the leg's segment carry was
EGIF text, whose round-trip re-scopes a constant shared across cells, so a stale atom's
vertex sits outside the cell the ERA targets. **Already fixed on `main`, two days ahead
of the live evidence, by Examination IV docket ④+⑥** (`9fa6287`+`549c386`+`71e0fcf`,
2026-07-19): ④ makes the carry structural `to_dict` JSON (the trigger unreachable —
`test_carry_preserves_resident_M_structurally*`), ⑥ makes a refused decay
**skip-and-count** (`decay_skipped`, `_decay_refused` held aside and pruned —
`test_a_refused_decay_is_counted_once_across_segments`). The running process predates
those commits, so it keeps crashing harmlessly at each decay attempt until the cap;
the supervisor absorbs each (max-crashes 50). This is live confirmation the docket
items were load-bearing, worth one line in the disposal. Separately fixed forward in
all three live drivers: crash tracebacks now go through the stdout tee into
`console.txt` (`print_exc(file=sys.stdout)`) instead of bare stderr, which had left
them only in the terminal scrollback. Also noted: leg 2's `fetch_errors` stepped 0→3→12
(`schedule`), the 3 before crash #1 and the jump to 12 at crash #2's resume —
plausibly counted in the crashed segments' retries, worth one line in the disposal.

---

**Artifacts (on execution):** `runs/run12/console.txt` · `runs/run12/items.jsonl` (record/replay)
· `runs/run12/checkpoints` · `runs/run12/state.json` + `sports_state.json`. See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.

## Run ended — 2026-07-20 (author STOP, honored at the 14:42 poll boundary)

The author touched `runs/run12/STOP` at 14:18; the runner exited cleanly at its next
poll boundary (14:42) and wrote the full closing block to `console.txt`. Totals:
**359 rounds, 16 crashes survived** (all the known pre-fix decay-refusal family —
already fixed on `main` by Examination IV docket ④+⑥, so each crash was harmless
confirmation), 300 picks raised · 215 resolved · 0 dropped · 10 postponed ·
12 fetch_errors (all `schedule`).

**Final per-arm standings (P3¹² answered — `select_best` discriminates):**

| arm | net | acc | record |
|---|---|---|---|
| odds | +8 | 0.633 | 19h/11m/13a ◄ select_best |
| home | +6 | 0.607 | 17h/11m/15a |
| naive | +1 | 0.667 | 2h/1m/40a |
| cal | −1 | 0.484 | 15h/16m/12a |
| strong | −3 | 0.448 | 13h/16m/14a |

The leader flipped home↔odds across the run rather than being fixed from the start.
**P4¹²:** home-win rate over decided home-rival bets 0.607 over 28 (literature
≈0.53–0.54) — small-n, interpretation the author's. **P2¹² (ledger half):** the
calibrated arm walked its cut 50→300 with 33 re-generalizations and finished
next-to-last. Run-level ledger (resolutions only): 66 hits · 55 misses ·
94 abstentions · net 11 · accuracy 0.545. All five arm laws still standing at exit.

Disposal of the F¹² findings against the pre-registered priors remains the author's.
