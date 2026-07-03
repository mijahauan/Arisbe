# Run 3 log — crawl + tropism (the warm-set re-poll)

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §13](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— design + priors P1″–P7″ **drafted and affirmed by the author 2026-07-02** (all five open
decisions as drafted: `source.inject(ids)` seam · decay-adjacent priority · `warm_fraction`
0.5 fixed · crawl + tropism · ambiguous labels skip + count). The mandate is RUN_2_LOG F2′:
neither passive membrane ever revisits, so mechanism durability (P2) was vacuous twice —
*ingestion alone cannot test durability; only directed re-engagement can.* Findings are about
the game (and Wikidata's editorial dynamics as represented) — never the world. *Progression,
not progress.*

**Driver:** `uv run python tools/run_live_wikidata.py --runs-dir runs/run3 --max-seconds 3600`
(frontier source; `--warm-fraction` defaults to 0.5 → k=4 of the 8-id chunk warm; add
`--warm-fraction 0` to reproduce the run-1 passive baseline).

**Machinery under test (built 2026-07-02, offline-proven in `tests/test_tropism.py`):**
`src/tropism.py` (`WarmSetTropism` — M's standing facts → entity ids via the reversed
`LabelCache`, decay-adjacent first; ambiguous/unmapped labels skipped + counted) ·
`RotatingWikidataSource.inject` (front-of-queue, `_seen`-exempt, counted, resume-safe) ·
`LiveRunner(tropism=…)` (one consult per poll boundary). The two offline headlines: a warm
re-delivery reads as a **non-revising round** (the habit holding), and a deprecation arriving
on a warm re-reach **meets its standing target** and is mechanically retracted — the P2 event.

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-03 · author + Claude (supervised sitting, full hour) |
| source | frontier crawl, seeds Q42 Q7259 Q937, chunk 8, warm_fraction 0.5 (k=4), per_entity_cap 25, frontier_cap 400, crawl on |
| ttl · segment_cap · min_interval_s | 30 · 25 · 5.0 (defaults, matching run 1 for P5″ attribution) |
| stops configured | max_seconds 3600 (**fired**, at the seg-17 boundary, 3858 s summed segment time) · max_m 200 (name-units — see F1″; never fired at 10–27) · STOP file available, unexercised (exercised run 1) |
| code version (git SHA) | ff510ad |

**Totals:** 1 sitting · **17 segments · 423 rounds · 3 polls** (75 + 200 + 200 recorded
statements post-cap; 3392 statements capped by `per_entity_cap`, counted) · 17/17 checkpoints
§3.3-attested to the side store. **Tropism counters:** `warm_emitted=6 injected=6
ambiguous_skipped=0 unmapped_skipped=0` (3 injected at each of the poll-2 and poll-3
boundaries; k=4 configured — the warm set held only 3 reachable distinct entities per
boundary). **Determinism canary GREEN:** the offline replay of `polls.jsonl` (no checkpoints,
no pacing) reproduced all 17 live segments **exactly** — rounds, dispositions, and
`non_revising` per segment — then continued to 469 rounds / `source_exhausted` (the live run
stopped on max_seconds with ~46 disputes still queued: **queued, never truncated**, as
designed). The whole 469-round replay + episode mining completed in ~a minute offline —
checkpoint attest is essentially 100 % of live wall-clock (see F1″).

## P7″ first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | < 0.2; sustained rise = degradation | 0.00, 0.00, 0.00 | ✓ |
| checkpoints §3.3-attest, side store | all | 17/17, `runs/run3/checkpoints`, no refusals | ✓ |
| \|M\| bounded; elapsed bounded | ≈ ttl; **hub-degree rider**: the warm set concentrates polls on held entities | **✓ in the instrument's units, ✗ in the units that cost wall-clock** → F1″. Digest \|M\| 10–27 throughout (ttl 30) — but `m_relations` counts relation *names*; the seg-17 checkpointed sheet holds **135 atoms / 136 vertices with five hubs of degree 20–25**. Elapsed **not bounded**: 3.3 s → **1075 s**, worse than run 1's 593 s max | ◐ → F1″ |
| warm plumbing counters | `warm_injected` > 0 per digest; skips counted, never silent | injected appears from poll 2 onward; all skip counters 0 (and would have printed if non-zero) | ✓ |
| statements_dropped / unparseable_dropped | counted | 3392 capped, counted; unparseable 0 (the run-2 parse gate never fired) | ✓ |

*Honesty note: a ~2-minute exploratory ELK layout (supervision-side, unrelated to the runner)
overlapped roughly segments 8–9 and may have inflated their elapsed slightly; the 582 s /
1075 s tail (segments 16–17) ran uncontended and is real.*

## Priors P1″–P6″ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1″ the revisit works | digest `non_revising` / episodes | non-revising ≫ 0 — the structural fraction runs 1–2 measured at zero | **CONFIRMED: 100 of 423 rounds (23.6 %)** non-revising (segs 4–6: 31 · seg 10: 2 · segs 12–14: 67), first appearing exactly at the poll-2 boundary with `warm_injected` 0→3 | `theorem_registration` | the §13 design did what it pre-registered; the habit-holding hum is now a measured, structural fraction of the game |
| P2″ durability, finally populated (**the run's question**) | `mechanism_principles`, decay-aware | retracts > 0 live; consensus stick-rate < 1.0 once overturns occur | **Partially populated, no retracts.** The table now carries real cross-segment mass with the decay split (consensus n=281 stick 1.0 `decay_erased=128` · reliable_source n=140 stick 1.0 `decay_erased=86` · **deprecated n=2** stick None durable False) — but both deprecated deliveries were *inert* | `challenge_to_M` **against the prior's sufficiency claim** → F2″ | revisit is *necessary, not sufficient*: the P2 event needs the value to **change rank between visits**. Both deprecations were the *same born-deprecated statement* — never admitted, so its denial had no standing target (run-1 F2's shape, now reproduced *on a warm re-reach*) |
| P3″ the ledger under re-poll | digest `m_relations`/`decayed` | decay concentrates on what the tropism doesn't choose; a working set pinned by re-poll rather than arrival order | **CONFIRMED — and stronger than intended** → F1″. Decay continued every segment (1–12 names/seg) while the warm names stayed pinned; the pinning works so well it defeats the *atom*-bound entirely (atoms accumulate unboundedly under warm names) | `new_fact` about the game + `challenge_to_M` against the §10 capacity model's units | the intended change (re-poll pins the working set) is observed; its unintended consequence is F1″ |
| P4″ true:negation, for free | `gaps` | denials meeting standing targets retract; denials without a standing target inert; inconsistency = a rulebook gap | **CONFIRMED on the weak side only:** the only denials delivered (the deprecated pair) were both inert, consistently, and correctly (target never standing — under the closed world the denial already held). No denial-with-standing-target case arose live (that is F2″'s gap) | `redundancy` (the rule held; the interesting case never fired) | the offline test (`test_tropism.py`) remains the only witness of the retract path — still true after run 3 |
| P5″ attribution | vs the run-1 baseline (F3′) | any departure is attributable to the tropism, not source variance | **CONFIRMED:** same seeds/config/source as run 1; the two departures — redundancy fraction 0 → 23.6 %, and the atom-pile-up under warm names (F1″) — are both tropism-attributable; retract rate unchanged (0 → 0) consistent with F2″ | `theorem_registration` | the two-passive-baselines investment (runs 1–2) pays off exactly as designed |
| P6″ poise, read honestly | `poise_from_digests` | redundancy-heavy windows depress engagement — read ○ against `non_revising`; the warm/fresh mix guards the all-warm rigidity loop | **CONFIRMED, surprise on the good side: 17/17 segments ●** — even segs 12–14 (84–96 % non-revising) read poised; the fresh half of the 0.5 mix kept every window engaged | `redundancy` + a small `new_fact` | the predicted ○ depression did not appear at warm_fraction 0.5; whether it appears at higher fractions (the deliberate all-warm loop) is the rigidity-at-exhaustion probe, still open |

## Findings (dated, disposed)

### F1″ — decay bounds the *vocabulary*, not the *sheet*; the tropism pins the vocabulary warm, so atoms grow without bound under hot names (2026-07-03)
prior: P3″/P7″ · evidence: digest `|M|` 10–27 all run (ttl 30) while the seg-17 checkpointed
sheet holds **135 atoms / 136 vertices, five hubs of degree 20–25**; per-segment elapsed
3.3 s → 1075 s tracking the real sheet, not the digest; isolated post-run — `_sheet_relations`
(the digest's `m_relations`, the `max_m` safety net) counts distinct relation **names**, and
`UsageLedger` decay erases per **name**; a warm re-delivery refreshes exactly the held names'
last-use, so decay never reaches them, while each re-poll of a hub entity adds *new atoms
under the same names* (one Wikidata property ↦ dozens of statements). Round compute is
innocent: the full 469-round replay ran in ~a minute without checkpoints — **checkpoint
attest is essentially the entire live wall-clock**, and it is super-linear in atoms × hub
degree (the RUN_1 F1 residual, now with five hubs instead of one; the seg-17 load-boundary
attest exceeds 10 minutes offline).
meta-disposition: **`challenge_to_M` against the §10 capacity model's units — "disuse-decay
bounds |M|" is relinquished in atom-units under tropism** (it stands in name-units). The
displayed instrument under-reports in exactly the units that cost wall-clock — an
honest-instruments finding of the same family as the legibility tripwire.
why / what it changes: three candidate prescriptions, **author decisions for the §13
follow-up** — (a) an atom-unit column in the digest + an atom-unit safety net (cheap,
instrument-only, no behavior change); (b) a per-name atom cap or atom-level decay (a real
rulebook change: what does it *mean* for one fact under a warm name to fall from use?);
(c) the attest-cost engineering residual (the visibility graph's O(waypoints²) pair loop)
now has a concrete worst case to optimize against. Correctness was never at stake — every
attest passed; this is the economy-of-research parameter, sharpened.

### F2″ — the P2 event = revisit × world-motion; revisit alone is necessary but not sufficient (2026-07-03)
prior: P2″ · evidence: the run's only two deprecated deliveries are the *same statement*
(`female_form_of_label` on the screenwriter item, reverts=13), delivered in two polls — the
second on a warm re-reach (the entity backs M's standing facts). Both rounds disposed
**inert**: the value is **born-deprecated** (Wikidata already ranked it deprecated), so M
never admitted it, so the denial's target was never standing and the ContradictionAgent
correctly abstained (run-1 F2's working-set-relativity, now reproduced *with* the revisit
the tropism was built to supply).
meta-disposition: **`challenge_to_M` against P2″'s sufficiency claim, disposed by
re-registration:** the P2 event needs a value that **changes rank between two visits** — the
crawl's settled surface did not move within the hour. The machinery's own correctness is
unaffected (the offline test delivers the retract when the target *is* standing).
why / what it changes: two routes to the event, both pre-registrable — **run 4 = stream +
tropism** (the change stream samples the world *moving*; the tropism holds the target
standing until the edit arrives — the two halves runs 2 and 3 proved separately, composed),
or a much longer crawl window (days, unattended — the crash/resume + STOP machinery is
proven ready). Run 4 is the cheaper experiment and was already §12/§13's named candidate.

### F3″ — the redundancy fraction is structural and the mix shows through at segment granularity (2026-07-03)
prior: P1″/P6″ · evidence: non-revising rounds arrive in warm-shaped waves (segs 4–6 after
poll 2; segs 12–14 after poll 3, peaking at 24/25) and vanish in fresh-shaped ones (segs
7–9, 15–17 all `new_fact`), because injected warm ids sit at the front of each chunk and the
segment cap slices the batch in delivery order. Poise reads ● through both phases at
warm_fraction 0.5.
meta-disposition: `new_fact` about the game — a legible, structural warm/fresh texture at
segment scale, useful as the *expected* signature for reading future digests (and the
concrete instance of the rate-domain "hum" the same sitting's
[docs/RATE_AND_INTELLIGIBILITY.md](../docs/RATE_AND_INTELLIGIBILITY.md) pre-registers
hypotheses about).

## Artifacts

`runs/run3/polls.jsonl` (offline replay — the canary input) · `runs/run3/checkpoints/` (17
attested UoDs; **run3_seg17 is the F1″ attest worst-case fixture**) · `runs/run3/state.json`
+ `frontier.json` (resume state) · `runs/run3_console.txt` (live console) ·
`runs/run3/filmstrip/` — 10 of 17 frames (`render.py` beside them; 240 s frame budget; frame
cost tracked sheet growth 3.5 s @ 25 atoms → 197 s @ 82; seg 10 blew the budget and the
hub-heavy tail was stopped at wrap — **F1″ made visible in the display path**, the
layout-budget rider RATE_AND_INTELLIGIBILITY §6.3 names).

## Horizon

- **Run 4 = stream + tropism** (F2″'s prescription; §12/§13's named candidate): the
  composition that makes the P2 event *reachable* — the stream supplies world-motion, the
  warm set holds the target standing to meet it. Needs the driver's
  `--source recentchanges --warm-fraction` refusal lifted (one guard line) + a §14-style
  pre-registration (priors P1‴…, incl. the F1″ atom-unit instruments).
- **F1″ decisions for the author:** atom-unit digest/safety-net (cheap, recommended
  regardless); per-name atom cap vs atom-level decay (a rulebook question — what is *one
  fact's* disuse under a warm name?); the attest O(waypoints²) residual now has a named
  worst case (135 atoms, five hubs — the seg-17 checkpoint is the fixture).
- **Carried from RUN_2:** true:negation consistency now *half*-delivered (denials do arrive
  on re-reaches; the standing-target case still awaits world-motion — merges into run 4);
  rigidity-at-exhaustion (deliberately small frontier / higher warm_fraction — note an
  injection **revives** an exhausted frontier, so the all-warm loop is reachable on purpose;
  P6″'s all-● at 0.5 makes the higher-fraction probe more interesting, not less).
- **The spectator surface** (born this sitting, watching this run happen invisibly): the
  read-only store wire + rate axis, pre-registered as hypotheses in
  [docs/RATE_AND_INTELLIGIBILITY.md](../docs/RATE_AND_INTELLIGIBILITY.md) and queued as a
  candidate in ADAPTIVE_SCOPE_VIEWER §10 — *not yet affirmed*. F1″ is also its layout-budget
  rider: the filmstrip/live view inherits the attest worst case, arguing for coarse-first
  rendering at wide temporal zoom.
