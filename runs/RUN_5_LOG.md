# Run 5 log — the duration probe (overnight unattended stream + tropism) — EXECUTED & DISPOSED

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §16](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the atom-level decay rulebook + semi-naive materialization + the canonical-signature fix
BUILT 2026-07-03 (offline-proven); run priors P1⁵–P6⁵ **AFFIRMED as drafted by the author
2026-07-03, pre-launch**. The mandate is RUN_4_LOG
F1⁗: the P2 event is a rank-*transition* event with a base rate below the one-hour horizon even
under revisit × world-motion — duration is the cheapest lever, and the F2⁗ round-compute wall
that would have choked an overnight run is dealt with (atom-decay bounds the sheet in the honest
unit; the incremental materializer keeps round compute flat). Findings are about the game (and
Wikidata's editorial dynamics as represented) — never the world. *Progression, not progress.*

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_wikidata.py --source
recentchanges --runs-dir runs/run5 --max-seconds 50400` (chunk 8, warm_fraction 0.5 → k=4,
per_entity_cap 25, ttl 30, segment_cap 25, min_interval 5.0, max_m 200, max_m_atoms 1000).
**Amendment recorded pre-launch (author, 2026-07-03):** `max_seconds` 28800 → **50400 (14 h)**
— start ~15:00 local, self-stop just before 05:00 so the author reads results on rising;
duration is the very lever the probe pulls, all other knobs as affirmed. Supervised the first
~15 min; STOP file available but not expected to be needed; `--resume` after any crash.

**Machinery under test (built 2026-07-03, offline-proven):** atom-level disuse-decay
(`UsageLedger` in `atom_key` units; use = re-delivery; erasure via the structural
`retract_atom`; F1″ pinning dissolved — `test_atom_level_decay_dissolves_the_warm_hub_name_pinning`)
· atom-precise tropism decay-adjacency · atom-precise stickiness (`mark_decayed_atoms`) ·
semi-naive `IncrementalMaterializer` (counters in the final console summary) · **the
canonical-signature fix** (§16.2 — profiling found F2⁗'s dominant term was
`generate_egif`'s WL refinement, not the peel: 15.7 s → 3.3 ms on the 200-atom hub sheet,
~4800×; a 25-round segment at 200 atoms now ~1.5 s).

## Outcome in one line

**The 14-hour probe died at 32.1 minutes** — not on compute, rate, memory, or the world, but on
its own checkpoint gate: a §3.3 `CorrespondenceViolation` (occlusion) at the segment-1531 save,
a **content-dependent coin flip** the run had won 1,530 times. And the offline post-mortem found
the probe could not have delivered its P1⁵ event even at 14 h: the atom-level rulebook silently
dissolved the persistence mechanism P2 depended on (F2⁵ below). Both walls are named and
actionable — the run failed operationally and succeeded evidentially.

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-03 14:46:09 → 15:18:20 local (32.1 min of a planned 14 h) · launched by author, unattended after ~15 min |
| source | recentchanges (bots excluded), chunk 8, warm_fraction 0.5 (k=4), per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 |
| stops configured | max_seconds **50400** (amended) · max_m 200 · max_m_atoms 1000 · STOP file |
| code version (git SHA) | 0d4b618 |
| how it ended | **crash** — `CorrespondenceViolation` at `save_uod(run5_seg1531)`; no stop condition fired |

**Totals:** 1,531 segments · **34,272 rounds** · 335 polls · **1,530/1,531 checkpoints
§3.3-attested + saved** (the 1,531st refused → fatal) · dispositions {new_fact: 24,350} +
9,922 non-revising (29.0%) · tropism warm_injected 1,088 / ambiguous_skipped 41 /
unparseable_dropped 0 · statements: 34,549 kept, 19,593 cap-dropped (36%, counted never silent)
· 128 deprecated-rank arrivals · materializer counters **lost to the crash** (final summary
never printed) · poise 1,387/1,531 windows ● (144 ○ rigidity, 0 ✕ thrash).

Throughput: **17.8 rounds/s** (~32× run 4's 0.56/s) — the run was *pacing-limited* (335 polls
≈ 5.75 s apart), not compute-limited. ~102 rounds/poll.

## P5⁵ first — the unattended operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| checkpoints §3.3-attest, side store | all | 1,530/1,531 attested + saved; **the 1,531st refused and the refusal killed the process** | **FAIL** (see F1⁵) |
| legibility per poll | < 0.2 sustained | ≤ 0.07 sustained after warm-up (first 3 polls 0.26/0.22 = small-sample warm-up) | ✓ |
| canary (offline replay of a prefix) | green | **green** — seg-1531 replayed offline from `state.json` + `polls.jsonl[-1][50:75]` reproduces the console digest exactly (25 rounds, all new_fact, atoms=75) | ✓ |
| crash/resume (if exercised) | decay clock continues | **not exercised** — the crash hit an unattended run at 15:18; no human awake to `--resume`, and no auto-resume supervisor exists. `state.json` (post-seg-1530) is intact and resumable | — |

The floor failed at a clause the pre-registration never wrote down: **attest robustness under
machine-scale content**. Refusal-aborts-cleanly is the right contract at the corpus boundary;
in an unattended loop it converts one unlucky layout into the end of the run.

## Findings (dated, disposed)

### F1⁵ (2026-07-04) — the checkpoint attest is a content-dependent coin flip, and it ended the run

**What happened.** At `save_uod(run5_seg1531)`, `attest_correspondence` refused with two
occlusion failures: vertex label box overlaps vertex label box (text-on-text), and a line of
identity striking through a label box it is not incident to. The colliding pair (offline
reproduction): constants **`'Warner Bros. Studio Tours'`** and **`'Warner Bros. Studio Tour
London – The Making of Harry Potter'`** (61 chars) — adjacent via `part_of`, both with very
long label boxes.

**Reproduction & mechanism.** The exact segment replays offline (canary green) — and the attest
then **passes or fails ~50/50 across re-rolls** (10/20 fails observed). The layout is
deterministic given a parsed EGI; the nondeterminism enters at parse: fresh UUIDs shift
`canonical_signature` tie-breaks among symmetric elements → different ELK input order →
different geometry → the long labels do or don't collide. The run won this flip 1,530 times on
easier content (short labels), then drew a Warner-Bros-shaped M and lost. Over a 14 h horizon
(~40k segments) a fatal roll is a **near-certainty**; duration runs cannot ship on this gate.

**What it is not.** Not a §3.3 falsehood — the EGI is fine; the *drawing* failed the occlusion
quality clause. Not the F2⁗ compute wall (dealt with). Not specific to this entity — the class
is *machine-scale label lengths* (Wikidata entity names), the same lineage as run-1's
star-graph attest finding: checkpoint §3.3 cost/robustness scales with M's **shape and content**.

**Disposal (analysis session; author decisions queued below).** Three levers, not exclusive:
- **(a) retry-the-drawing at the checkpoint** — §3.3 stays mandatory (never write an unattested
  pair); on refusal, re-roll the layout (fresh parse → fresh tie-breaks) up to N times before
  giving up. At p≈0.5 per roll, 4 retries ≈ 97%; content-dependent p means it's mitigation,
  not proof.
- **(b) supervisor / auto-resume in the driver** — catch the refusal (or any crash), count it,
  quarantine the refused segment's EGIF beside the checkpoints, and continue the run (the state
  file already makes this correct; the decay clock continues). Converts a fatal roll into a
  counted skip — the honest unattended posture.
- **(c) the root fix** — the layout defect is real: ELK is not reserving vertex-*label* boxes
  as placement geometry, so long constant labels overlap even when their dots are apart.
  Reserve label extents in `_compute_element_sizes` (or place labels collision-aware).
  This removes the flakiness rather than routing around it.

### F2⁵ (2026-07-04) — the atom-level rulebook dissolved P2's persistence mechanism; ttl was never re-derived in the new regime

**The event arrived and the game missed it.** The stream delivered a **genuine rank
transition inside the 32-minute window**: Vrej-Armen Artinian's ISNI `0000000373895135`
arrived normal-rank at poll 317, then **deprecated at polls 321, 322, 329, 330, 333** — five
redeliveries, the revisit design working exactly as built. Zero `retract_fact` fired. The
target atom had decayed **~400 rounds before** its deprecation returned: ttl=30 *global rounds*
at 17.8 rounds/s is a **~2-second wall-clock memory** (~1.7 segments). (Of 128 deprecated-rank
arrivals: 70 shared an (item, prop) with a standing value — mostly born-deprecated beside their
replacement, the F1⁗ inert shape — and exactly **1** was a true cross-poll value transition.
It was missed for the structural reason, not the base-rate reason.)

**Why this is new.** In runs 3–4, decay was *name-level*: one warm atom pinned every atom of
its name — the very F1″ "bug" the rulebook dissolved was **load-bearing for P2**: name-pinning
was the only thing holding a target standing across poll gaps. The affirmed rulebook (the habit
is the fact — philosophically right, and it did bound the sheet in the honest unit, P2⁵ below)
removed that pinning, and ttl=30 was carried forward undere-derived. With ~102 rounds/poll,
**no atom can survive even one poll gap** unless re-delivered — the warm set is *memoryless*
(it is simply the tail of the current batch), and the tropism's stated purpose ("re-checked
while the target still stands, before decay erases the evidence-bearer") is unfulfillable at
these knobs. **P1⁵'s premise — a warm-*held* target — was structurally unsatisfiable regardless
of duration.** Duration was never the binding lever; persistence was.

**Disposal (analysis session; author decisions queued below).** The tension is real: decay is
the *only* bound on the unbounded sheet, but the P2 event needs targets that persist for hours.
Candidate resolutions:
- **(i) re-derive ttl in the new unit** — ttl must exceed the warm re-reach period
  (warm-set size W entities ÷ k=4 per poll × ~102 rounds/poll). ttl ≈ 600–1000 rounds → M
  carries ~everything from the last ~6–10 polls (~600–1000 atoms — inside max_m_atoms=1000,
  barely). Blunt but no new machinery.
- **(ii) re-denominate ttl in polls (or wall seconds)** — the habit clock should track
  *engagement opportunities*, not raw rounds; ttl=10 polls survives ten gaps at any throughput.
  Small `UsageLedger` change; semantics honest ("idle N polls" is closer to disuse than
  "idle N rounds" once rounds are ~free).
- **(iii) an explicit pinned warm set** — the tropism *pins* the atoms of its W warm entities
  (exempt from decay while pinned, W bounded); persistence decoupled from the sheet bound.
  Cleanest mechanism, but a genuine rulebook change (a new habit class: attended habits
  outlive unattended ones) — needs its own affirmation.

## Priors P1⁵–P4⁵, P6⁵ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1⁵ the P2 event at duration | `mechanism_principles` + retract count | ≥1 rank transition on a warm-held target in ~8 h; a zero = a measured rate ceiling | **0 retracts in 32 min — but NOT a rate measurement**: 1 genuine transition arrived, was redelivered 5×, and missed because the target had decayed (F2⁵) | **instrument unsatisfiable as configured** — the zero measures the knobs, not the world; re-run only after an F2⁵ decision | the "warm-held" premise cannot hold at ttl=30 rounds / ~102 rounds/poll |
| P2⁵ sheet bounded in atoms | `m_atoms` digest + net | stabilises ≈ ttl-scaled; net never fires; F1″ not reproduced | **CONFIRMED** — atoms 25–76, mean 61, vs cap 1000; `max_m_atoms` never fired; no name pinning observed | confirmed | the rulebook's bound works — indeed *too* well (F2⁵) |
| P3⁵ round compute flat (F2⁗) | segment `elapsed_s` + materializer counters | no super-linear tail; extensions ≫ rebuilds | **CONFIRMED emphatically** — 1.26 s/segment mean, flat across all 1,530 checkpoints (bucket means 1.09–1.41 s, max single gap 3.4 s); ~32× run-4 round throughput; materializer counters lost to the crash but flatness is the evidence | confirmed | the F2⁗ wall is gone in the field; the run became pacing-limited |
| P4⁵ tropism at atom precision | warm counters + `non_revising` | warm set rotates by atom age; counters exact; texture persists | counters exact (1,088 injected, 41 ambiguous, 0 unmapped); non-revising texture persists (29.0%) — but "rotates by atom age" is **degenerate**: at this throughput the warm set is memoryless (= the current batch tail) | partially confirmed | the healthy-looking counters masked F2⁵ — non-revising ≠ persistence |
| P6⁵ poise at duration | `poise_from_digests` | quiet hours served by the warm set; ○ = genuine lulls | 1,387/1,531 ● (90.6%), 144 ○, 0 ✕ — over 32 min only; the quiet-hours claim **untested** (run never reached the night) | untested at duration | re-read on the re-run |

## Author decisions — AFFIRMED ("Proceed.", author, 2026-07-04) and BUILT same sitting

1. **F1⁵ mitigation — BUILT (both):** `LiveRunConfig.checkpoint_refusal="skip"` — a §3.3
   refusal at the checkpoint is **counted** (`checkpoints_refused`, surfaced in the digest as
   `⚠ ckpt_refused=`) and the refused segment's M **quarantined** (`refused_seg<n>.json`:
   EGIF + error beside the state file — auditable, never silent, never an unattested write);
   "raise" stays the default (the attended/corpus contract). Plus the driver **supervisor**:
   any in-run crash is caught, printed, and the run **auto-resumed** from the persisted
   state/frontier (decay clock and crawl continue; the overall deadline is honored across
   legs; `--max-crashes` budget, default 50). Verified by an offline smoke: injected crash at
   poll 2 → resume → completion with global segment numbering and the decay clock continuing.
   *Note on the retry-the-drawing variant:* rejected on inspection — no DTO is persisted, so
   attesting a re-rolled isomorph while saving the original ids would plant a load-time bomb
   (the load boundary re-attests the original and would refuse it ~50% of rolls). Skip-and-count
   is the honest form.
2. **F1⁵ root fix — QUEUED (not gating the re-run):** inspection shows the defect is deeper
   than ELK sizing: `presentation_ops.vertex_label_box` places the label in the *freest angular
   gap* post-layout (cut-aware but not sibling-label-aware), so ELK cannot reserve for it
   without a global, deterministic label-placement pass shared by renderer and attest —
   `presentation_ops` is **protected core**; the change wants its own design + corpus attest
   pass. Skip-and-count covers the run meanwhile (observed refusal base rate: 1/1,531 segments
   on live content).
3. **F2⁵ persistence — BUILT as (ii):** `LiveRunConfig.ttl_unit="polls"` (+ driver
   `--ttl-unit`) — the habit clock counts **engagement opportunities**, not rounds; the poll
   clock is persisted in `state.json` ("poll") and continues through resume. Calibration for
   the re-run: with k=4 warm re-reaches/poll, the decay-adjacent-first policy sustains a warm
   set of ≈ k·ttl entities; **ttl = 8 polls** → ~30 sustained entities (~400–700 atoms
   expected steady state), and the observed Artinian event (a 4-poll gap) would have been
   caught. Safety nets re-derived for the new steady state: `max_m` 200 → **800** names,
   `max_m_atoms` 1000 → **2500** atoms (nets, not targets — sized ~4× expected so they catch
   runaway, not normal operation).
4. **Re-run — run 5b relaunched** (see the pre-launch record below).

**Rider found and fixed while building (2026-07-04):** the runner's injectable `sleep`
defaults to a no-op and the driver never passed the real one — so `min_interval` pacing has
**never actually slept** in any run (runs 1–5 were paced by compute time alone), and a quiet
stream (empty polls — exactly overnight hours) would have **hot-spun against the Wikimedia
API**. The driver now passes `sleep=time.sleep`. Etiquette-relevant for the first run that
will genuinely see quiet hours.

## Run 5b — pre-launch record (2026-07-04)

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_wikidata.py --source
recentchanges --runs-dir runs/run5b --max-seconds 50400 --ttl 8 --ttl-unit polls --max-m 800
--max-m-atoms 2500` (chunk 8, warm_fraction 0.5 → k=4, per_entity_cap 25, segment_cap 25,
min_interval 5.0 — now actually slept, `checkpoint_refusal=skip`, supervisor `--max-crashes 50`).
**Amendments vs run 5, all F1⁵/F2⁵-mandated and recorded here pre-launch:** ttl 30 rounds →
8 polls (F2⁵ (ii)); nets 200/1000 → 800/2500 (re-derived, above); skip-and-count + supervisor
(F1⁵ (a)+(b)); real pacing sleep (the rider). All other knobs as affirmed for run 5. Priors
P1⁵–P6⁵ carry over unchanged — P1⁵ is now *satisfiable as instrumented* (a warm-held target
can exist); expected new observables: `ckpt_refused` count (F1⁵ base rate at duration),
`m_atoms` at the new steady state (~400–700), segment `elapsed_s` at that |M| (checkpoint
attest cost grows with atoms — self-limiting cadence, watch it).

## Run 5b — EXECUTED & DISPOSED (2026-07-04, the duration probe achieved)

**The 14 hours ran to completion.** 08:35:59 → 22:36 (stop: `max_seconds`, on schedule).
**Totals:** 253 segments · 5,817 rounds · 46 polls (5,975 statements) · **253/253
checkpoints §3.3-attested — zero refusals** · **1 crash, absorbed by the supervisor**
(resumed in 10 s, decay clock continuing; at most one in-flight segment lost) ·
dispositions all `new_fact` + whole warm segments non-revising · tropism warm_emitted 92 /
injected 180 (≈3.9/poll, k=4) / ambiguous 18 / unmapped 0 · materializer rebuilds 24 ·
extensions 2,090 · hits 566 · legibility ≤ 0.09 throughout · poise strip: ● with a periodic
○ at each poll-boundary decay/warm segment (the breathing rhythm of the new regime).

### P5⁵ — the unattended operational floor: **PASSED, exercised for real**

The floor did its job twice over: (1) **zero attest refusals in 253 checkpoints** at the
~1,000-atom steady state — the F1⁵ coin flip never lost this run (the skip-and-count path
stood armed and unneeded); (2) the **supervisor absorbed a genuine mid-run crash** — not
the attest, a **new bug** (F1ᵇ below) — and the run continued to its scheduled stop. The
canary artifacts are on disk (`runs/run5b/polls.jsonl`); crash/resume passed its first
real unattended test.

### Priors — observed at duration

| prior | observed | disposition |
|---|---|---|
| P1⁵ the P2 event | **0 rank transitions arrived in 14 h** — 18 deprecated-rank statements, 11 sharing an (item,prop) with a standing value, but *all born-deprecated beside their replacement* (the F1⁗ inert shape); the 10 `deprecated`-mechanism episodes were entertained and read not-durable. Unlike run 5's 32 minutes (which caught one), the 14 h window had none. | **a measured rate ceiling, instrument now valid** — persistence held (885 ledger atoms; targets stood across polls), so the zero measures the world's rate on this sample, not the knobs. The event is real but lumpy; see F2ᵇ for why the *effective* sampling rate matters more than wall-clock. |
| P2⁵ sheet bounded in atoms | **CONFIRMED in the new regime** — atoms sawtooth 860–1,030 across 14 h (decay bursts of 63–129 at poll boundaries — the polls-ttl firing in batches); \|M\| names ~245–280; neither net fired. | confirmed |
| P3⁵ round compute flat | **CONFIRMED at the new operating point** — segment elapsed stabilised (~284 s mean segs 51–100 ≈ ~282 s segs 101–118; no divergence), extensions ≫ rebuilds (2,090 vs 24). Not run 5's 1.26 s/segment: the *persistent* ~1,000-atom M costs ~3–10 min/segment (layout+attest+peel at scale) — flat, but heavy (F2ᵇ). | confirmed (flat ≠ cheap) |
| P4⁵ tropism at atom precision | counters exact; warm re-reach every poll; whole non-revising segments at poll boundaries = the habit holding under re-delivery. | confirmed |
| P6⁵ poise at duration | 14 h of strip: poised with a rhythmic ○ per poll cycle (decay/warm segments) — engagement/settlement/absorption visible at duration; no thrash. The run spanned daytime (08:36–22:36), so the overnight-quiet-hours clause is still only partially exercised. | confirmed (daytime) |

### F1ᵇ (2026-07-04) — 32-bit vertex ids collide at machine scale

`ValueError: Vertex v_4599e538 already exists`, raised inside a revision's EGIF parse
(`egif_parser_dau._parse_argument` → `with_vertex_in_context`). Element ids are
`v_{uuid4().hex[:8]}` (`egi_core_dau` ~L1115) — **32 bits**. A ~1,000-vertex sheet parsed
thousands of times makes a birthday collision statistically due (~10⁻⁴ per parse at that
size; tens of thousands of parses per run). The supervisor absorbed it — but it will
recur on every long run. **Fix queued (author):** regenerate-on-collision at the parser
layer (application-level, no protected-core change), or widen the id; the parser-side
retry is the minimal honest fix.

### F2ᵇ (2026-07-04) — the persistence fix moved the bottleneck to segment cost; the
duration lever buys fewer polls than it seems

Run 5 polled 335 times in 32 minutes; run 5b polled **46 times in 14 hours** (~18 min/poll
cycle: ~5–6 segments × ~250 s each per batch). The persistent ~1,000-atom M makes every
segment (checkpoint layout+attest + peel) expensive, so the *world-sampling rate* — what
the P2 event probability actually scales with — collapsed to ~1/40th of run 5's. Duration
alone no longer buys proportionate exposure. Levers for a run 6, in ascending
invasiveness: **(a)** checkpoint every Nth segment (cadence ≠ coverage — the digests and
state remain per-segment); **(b)** smaller steady state (ttl 4–6 polls ≈ 500–700 atoms);
**(c)** lighter checkpoint attest at scale (ties into the F1⁵ root fix). Queued for the
author with the §15 gate re-exam.

### §6 payoff — mechanism principles at live scale

The first duration-scale dispute-learning read: `consensus` n=1,637 (durable, 760
decay-erased) · `reliable_source` n=1,033 (durable, 598 decay-erased) · `deprecated` n=10
(not durable) — the mechanism differentiation the wiki-dispute program wanted, from a real
14 h live stream, decay-aware throughout.

## Artifacts

**Run 5:** `runs/run5/polls.jsonl` (335 polls, 34,549 statements — replays green) ·
`runs/run5/checkpoints/` (1,530 attested UoDs) · `runs/run5/state.json` (post-seg-1530,
resumable) + `frontier.json` · `runs/run5_console.txt` (full digests + the fatal traceback).
**Run 5b:** `runs/run5b/polls.jsonl` (46 polls, 5,975 statements) · `runs/run5b/checkpoints/`
(253 attested UoDs) · `runs/run5b/state.json` (final, poll 46) + `frontier.json` ·
`runs/run5b_console.txt` (full digests, the F1ᵇ traceback + supervisor recovery, the §6
final summary).

## Horizon

- **§15 gate re-examined on this run's disposal:** the duration probe is now **achieved**
  (run 5b) — the gate question (the docket of doubts, content direction) is ripe for the
  author's re-examination, informed by F2ᵇ (duration buys less world-exposure than polls
  do) and the §6 mechanism read.
- **F1ᵇ fix** (vertex-id collision, parser-side regenerate) — before any run 6.
- **F2ᵇ decision** (checkpoint cadence / ttl / attest cost) — with the §15 gate.
- **The F1⁵ root fix** (global deterministic label placement shared by renderer + attest;
  protected-core design pass): also implicated in three *intermittent* `test_eg_reader`
  clockwise failures observed 2026-07-04 (fail in a full-suite roll, pass in isolation —
  the same fresh-UUID → tie-break → layout-luck mechanism). One fix retires both the
  checkpoint flakiness and the flaky tests.
- Rigidity-at-exhaustion (carried from runs 2–4): the small-frontier / high-warm-fraction probe.
- The spectator surface (RATE_AND_INTELLIGIBILITY + ADAPTIVE_SCOPE_VIEWER §10): still queued.
