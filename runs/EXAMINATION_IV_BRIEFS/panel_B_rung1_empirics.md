# Panel B brief — Rung-1 S1 Robustness & Yield Attribution
(verbatim from the independent panel, 2026-07-19)

**Examiner:** ablation-and-baselines methodologist. **Charge:** refute, not flatter. **Sources read in full:** `docs/ADVERSARIAL_EXAMINATION.md` (Examination III house standard, line 1019 ff.), `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` §3, `docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md`, `src/attention_economy.py`, `src/arithmetic_world.py`, `src/probe_feed.py`, `tests/test_attention_economy.py`, `tests/test_probe_feed.py`, `tests/test_arithmetic_world.py`, `runs/RUN_13_LOG.md`.

**Method note.** Per the house standard I did not argue from the armchair: I ran deterministic pilot ablations against the shipped modules (scratchpad harness `ablation_pilot.py`; every arm is a one-command reproduction, runtimes 1–27 s). Pilot results below are labeled as pilots — they are the *shape* of the disposal experiments, run once to confirm the charges survive contact.

## Pilot results (deterministic, offline, shipped modules only)

| Arm | Definition | Refutation round | Runtime |
|---|---|---|---|
| A0 economy (shipped) | `ProbeDirectedFeed` + `AttentionEconomy` | **6** (reproduces build record) | 2.7 s / 90 rd |
| A2 severity-greedy | 2-line chooser: sort by `(-severity, cost)`; **no yield, no decay, no learning** | **6** — *identical to economy* | 2.6 s / 90 rd |
| A3 round-robin FIFO | FIFO repaired by one term: fewest-attempts-first | **67** | 2.9 s / 90 rd |
| A4 scatter, `confirm_lattice=6` | shipped scatter, chaff dial turned down | **7** | 1.1 s / 90 rd |
| A5 scatter, `confirm_lattice=60` | as shipped | 127 (reproduces build record; None @ 90) | 11.6 s / 300 rd |
| A1 severity-flattened economy | shipped economy, every `severity=1.0` | **None @ 90, None @ 300** — *worse than scatter* | 26.8 s / 300 rd |

---

## Suspect 3 — The S1 headline's robustness

### (a) Strongest charge, strongest form

**The S1 headline is evidence for "obey a hand-authored label," not for the economy design; the design's actual learned machinery contributes nothing to the result and is counterproductive on its own.**

The mechanics, from the code: `ProbeDirectedFeed._seed` (`src/arithmetic_world.py:121-135`) registers 60 `confirm` wants (cost 1.0, severity 1.0), **6 `hunt` wants — one per Fermat number including F5 — at severity 8.0**, and one musement want. The score is `severity * (Y[kind] + prior) / cost * attempt_decay^attempts` (`src/attention_economy.py:74-77`). At round 1 all yields are zero, so hunts score ≈ 8·0.05/1.0 ≈ 0.4 against confirm's 0.05: **the hunts win from the first round on the severity label alone**, in cost order F0→F5, and the refutation round is 6 because there are six Fermat numbers. The round-6 number is a property of the seed list's length, not of any search or learning: `test_hunt_wants_cover_all_fermat_instances_up_front` (`tests/test_arithmetic_world.py:69-76`) proves F5 is on the menu from round 1, and `atoms_for` exempts Fermat numbers from `range_cap` (`src/arithmetic_world.py:52`, `range_cap=200` ≪ F5) — no exploration was ever required to *reach* F5, only to *pick it from a 67-item menu where the author pre-labeled the 6 winning items 8× heavier*.

Pilot confirmation, three ways:

1. **A2 (severity-greedy): any prioritization that reads the label ties the economy exactly** — refutation at round 6, identical, with the entire learned apparatus (yield EMA, attempt decay, cost division, boredom, musement) deleted. The economy's marginal contribution over "sort by the label" is **zero** on its own headline world.
2. **A1 (severity-flattened): the learned machinery alone never refutes — in 90 or even 300 rounds — performing *worse than uniform random* (scatter: 127).** The yield term actively locks onto `confirm`/`extend` (they deliver atoms early, so their kind-yield self-reinforces) and starves the hunts. The severity label doesn't merely help; it carries 100 % of the result, *against* the drag of the learning component.
3. **A3/A4 (baseline repair + chaff dial): both baselines are degenerate in author-controlled ways.** FIFO repaired by one sort term refutes at 67. And the economy-vs-scatter margin — which the build record itself calls "the meaningful S1 margin" — **is a direct function of `confirm_lattice`, an author-set nuisance parameter**: at lattice 6, scatter refutes at round 7, one round behind the economy. No sensitivity analysis over this dial exists anywhere in the record.

The smoking gun for the dial: the spec's own risk note **pre-licenses tuning the world against the baseline** — "If S1's margin is small (FIFO gets lucky on a short range), widen `n_max` so cheap re-confirmation genuinely starves FIFO" (`docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md:153-155`). A pre-registration that reserves the right to enlarge the chaff pool until the baseline loses is not a pre-registration of the margin.

### (b) Most damaging charge the docs did not anticipate

**"Under budget" is never a budget.** The headline ("reachable under budget only if attention spends on severity," `src/arithmetic_world.py:5-7`; "under identical 90-round budgets," BOOTSTRAP §3 build record) and the spec's framing ("severity is expensive; this is what the economy must justify," spec line 80-81) imply a *cost* constraint. There is none: cost appears only as a ranking denominator (`attention_economy.py:76`); no purse is ever charged, no arm ever stops for spending. The F5 probe "costs" 4.28 units and pays nothing. An arm probing the most expensive item every round finishes 90 rounds exactly like one probing the cheapest. The budget is round-count; economy-of-research's defining trade (expected value *against expenditure*) is asserted in prose and absent from the harness. (Second unanticipated point, subsumed by A1: the record never isolates the learned component's contribution — no severity-flattened arm, no learning-off arm was ever run, so the attribution of S1 to "the economy" over "the label" was never tested.)

### (c) The author's best answer from the record — ANSWERS or DEFLECTS?

- **FIFO degeneracy: ANSWERS.** The build record concedes it plainly ("The FIFO arm is degenerate by construction — it re-probes `("confirm", 0)` every round, so 'never refuted' is a priori for that arm; the meaningful S1 margin is economy's 6 against scatter's 127-in-300," BOOTSTRAP §3, build record). Honest, and correctly identifies where the residual evidence lives.
- **"Severity tuned to win": ANSWERS the narrow reading.** Severity 8.0 is pre-registered at the *shape* level ("the world declares e.g. severity 8.0 for law-instance hunts," spec line 34-37) and is uniform over all hunts — F5 is not favored over F0–F4. My own robustness check agrees: the round-1 win condition is only severity/cost > 0.05-per-unit, so any severity ≳ 1.1 on hunts produces the same trajectory; the specific value 8.0 is not load-bearing. This narrow charge does not stick.
- **The operative claim: DEFLECTS.** The claim as it circulates — CLAUDE.md: "refuted … under budget **only by the economy arm**"; BOOTSTRAP §5.1: "S1's result is the framing doing its work — **severity bought the Fermat refutation**" — slides between two statements. The literal pre-registered S1 (economy strictly beats FIFO and scatter, `tests/test_arithmetic_world.py:170-179`) is true and remains true. The advertised generalization (the *economy design* — decayed-yield-per-cost learning — is what buys the result) was never tested and is false by A1/A2: severity bought the refutation, severity is an authored input, and the thing actually built and named (the learning scorer) contributes zero here and is harmful alone. Note the §5.1 ratification sentence itself, read strictly, concedes this — "severity bought the refutation" — without drawing the consequence that S1 therefore evidences the *label channel*, not the *economy*.

### (d) Disposal path — the runnable experiment

Write `tools/run_rung1_ablation_exam4.py` (offline, deterministic; my scratchpad harness is 80 % of it). Pre-register, then run:

- **Arms** (fresh `ArithmeticWorld`+`AttentionEconomy` per arm, 90 and 300 rounds): ① economy (shipped); ② severity-greedy (`sort by (-severity, cost)`, no learning); ③ severity-flattened economy (all `severity=1.0`); ④ round-robin FIFO (fewest-attempts-first); ⑤ scatter; ⑥ FIFO (shipped). Cross with `confirm_lattice ∈ {6, 60, 600}`.
- **The discriminating world:** a variant where the discovery does *not* live in the severity-8 kind — seed the false law `~[ (square *x) ~[ (even x) ] ]` with **no** hunt wants over its instances, its counterexample (n = 9) reachable only through severity-1 `confirm`/`extend` probes. This tests whether the economy *learns* where yield is or merely obeys labels.
- **Cost-budget arms:** re-run ①②④⑤ under a real purse (cumulative `Want.cost` capped at, say, 30 units; arm stops when spent), reporting refutation-or-exhaustion.
- **REFUTE the headline-as-generalization if** (predicted from pilots): ② ties ① at every lattice; ③ fails at 90 rounds; ⑤'s deficit collapses at lattice 6; and on the discriminating world ① does no better than ⑤. **SUSTAIN if** ① beats ② somewhere real — most plausibly on the discriminating world, where the yield term is the only channel that *could* find the severity-1 counterexample faster than random.
- **Runtime:** < 10 minutes total on this machine (measured: 1–27 s per arm).
- **Paper trail:** file results as F-findings in a run log; amend the CLAUDE.md/BOOTSTRAP headline to name the severity channel, or concede per the mandate.

### (e) Confidence

- That the **headline generalization** ("the economy design's ordering is what buys the refutation; evidence for severity-weighted decayed-yield-per-cost specifically") **falls: 0.92** (pilot already exhibits the refuting arms; residual uncertainty is only whether the discriminating-world arm rescues a partial version).
- That the **literal pre-registered S1** (economy < FIFO, economy < scatter at the shipped lattice) falls: **0.05** — it reproduces; it is just very weak evidence.

---

## Suspect 11 — Yield attribution (round-granular kind-credit smearing)

### (a) Strongest charge, strongest form

**The yield signal is not "yield": it is raw model *churn*, credited at kind granularity to whoever was last chosen — and it violates the design's own stated guard.** BOOTSTRAP §2c is explicit: the target "must be **learning progress** (the rate of improvement of prediction), never raw prediction error." What was built (`src/probe_feed.py:91-98`) is `events = len(atoms ^ prev_atoms) + abs(cuts - prev_cuts)` — the symmetric difference of sheet-level atoms plus cut-count delta, credited to every chosen want's kind. Three concrete mis-credit channels, all in the shipped code:

1. **Decay counts as yield.** An atom *leaving* M (disuse-decay's erasure) lands in the symmetric difference exactly like an admission. Demonstrated: a model shrinking by 4 atoms between calls credits the chosen (utterly barren) kind with `kind_yield = 0.8` (pilot Demo 1). In the S1 arithmetic runs this channel is **dormant** (no `ttl` passed; decay off). In **RUN 13 it is live**: the F1¹³ fix wired `--ttl` default 120 into `tools/run_vault_v0.py` (RUN_13_LOG.md, F1¹³) with 200-round segments — every decay wave after round ~120 hands phantom yield to whatever kind happened to be chosen that round.
2. **The churn pump (the realized noisy TV).** Combine 1 with any persistent re-delivering want (`persistent_kinds`, `probe_feed.py:71`; arithmetic's `confirm` is one): once decay erases an atom, a re-probe re-delivers it, the delta counts it, decay erases it again — a channel that generates unbounded "yield" with zero learning, which the scorer will then *prefer*. This is precisely the noisy-TV failure §2c says the design guards against; the built metric does not guard against it — it is only safe where decay is off or no channel re-delivers.
3. **Kind-level pooling + content-blindness.** Credit accrues to `w.kind`, never the want (`attention_economy.py:117-122`), so one lucky want props up all its siblings; and `_model_signature` counts sheet cuts (`probe_feed.py:25-35`) — a law *replaced* by a different law of equal count reads as zero events.

### (b) Most damaging charge the docs did not anticipate

The carry note (BOOTSTRAP §3: "correct at budget 1, but it double-counts once several wants are chosen per round") **misdescribes the budget>1 failure — it is not double-counting, it is smear-plus-omission, with a rich-get-richer tilt.** From the code path (`probe_feed.py:91-124`): at budget k, the k proposals queue and drain one per round; the observe branch fires only when `_last_chosen` is non-empty, so **proposal #1's delta is credited to all k kinds, and proposals #2…#k's outcomes are never observed by anyone** (`_prev_sig` advances past them). Demonstrated (pilot Demo 2, budget 2): alpha's 3-atom outcome credited to alpha *and* beta at 0.6 each; beta's own 1-atom outcome discarded. Since `_execute` runs in chosen order (highest-scored first), the outcome that *is* observed is systematically the top-scored kind's — feedback that structurally favors incumbents. Dormant today (`probe_budget=1` everywhere, including `VaultFeed`), but it is the socket's contract, `select_within_budget` machinery already contemplates multi-item budgets, and nothing pins it: no test exercises attribution at budget > 1.

### (c) The author's best answer — ANSWERS or DEFLECTS?

**Honest scoping, partial.** The spec concedes "Yield attribution … is approximate at round granularity; acceptable for S1–S3, noted honestly" (spec lines 156-157), and the carry list names the budget>1 issue. That ANSWERS the existence of approximation for the arithmetic cycle — and, crucially, the claim "acceptable for S1–S3" is *vindicated by my own Suspect-3 finding*: S1's success rides on severity, not on yield, so no S1–S3 result rides on the bias. But the record DEFLECTS on the forward exposure: (i) the decay-as-yield channel is nowhere named, and RUN 13 switched it live the same day decay was wired (F1¹³) — the vault run's economy is now learning partly from erasure noise; (ii) the budget>1 note misstates the mechanism (omission, not just double-count); (iii) the built metric contradicts §2c's own "learning progress, never raw error" rule, and no doc reconciles that.

### (d) Disposal path — runnable experiments

1. **Pin the mechanisms as tests** (5 minutes' work; both already written in my scratchpad): (i) shrinking-model → `kind_yield > 0` for a barren kind; (ii) budget-2 → sibling kind credited with first proposal's delta, second proposal's delta unobserved. File as xfail-pins or fix-first, author's choice.
2. **The churn-pump experiment** (arithmetic, offline, deterministic, ~1 min): shipped economy arm with `run(..., ttl=8)`, 120 rounds, plus a persistent `refresh` kind that re-delivers a fixed 5-atom block. **REFUTES the "noisy-TV guard is built" claim if** the `refresh` kind's yield stabilizes positive and its share of choices grows after decay onset; **SUSTAINS if** attempt-decay/yield-decay sink it anyway (possible: `attempt_decay^attempts` may rescue — this is genuinely open, hence worth running).
3. **Attribution-scheme ablation** (the direct test of "does the economy's success ride on the bias," ~5 min): arithmetic + vault-fixture runs at budget 1 and 3, three attribution schemes — shipped; **additions-only** (`events = len(atoms - prev_atoms)`); **sequential per-want** (observe each queued proposal's delta against the sig at its own pop, credited to its own want). Compare choice journals (`replay_choices`) and, for the vault fixture, the digest counts. **REFUTE** ("success rides on bias") **if** corrected schemes change refutation rounds/digests materially in the shipped design's *favor*-direction; **SUSTAIN the fix** if trajectories are invariant at budget 1 (expected) and diverge at budget 3 / ttl-on (expected).
4. **For RUN 13 specifically:** add `added`/`removed` split counters to the digest (numbers-only, custody-safe) so decay-crediting becomes observable in the live stream before the next real-vault launch.

### (e) Confidence

- That the **mechanism is biased as charged** (phantom decay credit; smear+omission at budget>1): **0.97** — demonstrated by execution.
- That **the economy's apparent success rides on the bias**: **falls, 0.12** — the S1/S2 results demonstrably do not ride on yield at all (Suspect 3, arm A2), decay was off, and budget was 1. The bias is real but *currently latent everywhere except RUN 13's live vault runs*, where its effect is unmeasured, not evidenced.

---

## Added suspects (same cluster)

### IV-x1 — S2 as registered was unfalsifiable; the substitute evidences exhaustion, not noise-resistance

(a) The pre-registered S2 ("the planted patternless predicate's probe-kind decays…") could never have failed: **no `coin` probe-kind exists** — coin atoms ride inside every probe's conjunction (`arithmetic_world.py:60-61`) and no coin law is proposable. The substituted evidence (confirm 0.019 vs hunt 2.60) shows a kind decaying because its *pool exhausted* (all 60 confirms probed; re-probes are zero-delta by construction) — a **dead** TV, not a noisy one. A noisy TV emits endless *change*; the only shipped channel that could emit endless change is the decay/re-delivery pump of Suspect 11(a)-2, which the metric would *reward*, not resist. (b) Unanticipated: S2's substitute and §2c's doctrine are in quiet contradiction (yield = raw change). (c) The build record's disclosure (BOOTSTRAP §3, "an honest mechanism disclosure") ANSWERS that the mechanism differs from the registration — the house standard's "honest scoping" — but DEFLECTS in still titling it "S2 HELD" rather than "S2 not testable as registered; a weaker claim held." (d) Disposal: the churn-pump experiment above *is* the real S2; run it. (e) Confidence "S2 HELD as registered" falls: **0.85** (it is a relabeling); that the system passes a *real* noisy-TV test: open, ~0.5.

### IV-x2 — S3's musement is plumbing, not a musement mechanism

(a) The "planted regularity unreachable from the docket" is planted **in the feed itself as a literal payload**: the musement want's payload *is* `MUSEMENT_LAW` verbatim (`arithmetic_world.py:133-135`, `:161-162`), proposed unmodified every ~10th round. S3 therefore demonstrates: hard-code proposing law L ⇒ L is admitted; don't ⇒ it isn't. There is no variation, no generation, no exploration — the thing "musement" names in the design ("keep variation alive," BOOTSTRAP §3) has population size 1, fixed at author time. (b) Unanticipated: with one hard-coded candidate, the musement *reservation arithmetic* (`_musement_slots`) is the only thing S3 tests — and a trivial `if round % 10: propose(L)` reproduces it. (c) The record's honest repair note (peel-tautology → admission test, "verified by the task reviewer as a repair, not a weakening," BOOTSTRAP §3) ANSWERS the *assay* question fully — I verified the tautology reasoning is correct (`tests/test_arithmetic_world.py:203-213`) — but DEFLECTS on what was assayed: the criterion was repaired; the mechanism under it remains a stub. (d) Disposal: a musement arm whose candidates are **generated** (`MutationProposer`-style recombination over the world's unary vocabulary, excluded from every seed list), success = a true law not authored anywhere in the feed gets admitted only with musement on; ~2 min runtime. (e) Confidence "S3 evidences a musement mechanism" falls: **0.8** (as a socket smoke test it stands; as evidence of musement it is circular).

### IV-x3 — "Under budget" (filed under Suspect 3(b); recorded separately for disposition)

Cost is a ranking denominator, never a charged resource; no arm can exhaust a purse. Disposal folded into 3(d)'s cost-budget arms. Confidence the "under budget" phrasing falls as stated: **0.75** (round-budget is *a* budget; the economic reading the docs invite is untested — though the pilot's cumulative-cost arithmetic suggests the economy would win a cost-budgeted rerun too, so this is likely repairable by rewording plus one arm).

---

## Summary for disposition

| # | Charge | Verdict at pilot | Confidence it falls |
|---|---|---|---|
| 3 | S1 evidences the *economy design* | Severity-greedy ties it (6=6); flattened economy never refutes (worse than random); scatter margin is the `confirm_lattice` dial; FIFO degenerate (conceded) | headline-generalization **0.92**; literal S1 0.05 |
| 11 | Attribution mis-credits; success rides on it | Bias demonstrated (decay-as-yield 0.8 on a barren kind; budget-2 smear+omission); but S1 success rides on *severity*, not yield — bias latent except RUN 13 live | bias-exists stands 0.97; "success rides on it" falls **0.12** |
| x1 | S2 held as registered | Unfalsifiable as registered; substitute = exhaustion decay | 0.85 |
| x2 | S3 evidences musement | Population-of-1 hard-coded candidate; plumbing tautology | 0.80 |
| x3 | "Under budget" | No cost purse exists | 0.75 |

**What the record does well, on the house standard:** the FIFO-degeneracy concession, the S2 mechanism disclosure, the S3 repair note, and the spec's attribution caveat are exactly the honest-scoping the mandate asks for — each named before I arrived. **What it missed:** every missing piece is the same shape — *no arm ever isolated the design's own contribution* (no flattened arm, no label-only arm, no chaff-dial sweep, no corrected-attribution arm), and the one dial the spec touched, it licensed turning *against* the baseline. The disposal experiments above are all offline, deterministic, < 15 minutes combined, and pre-registerable this week.

Pilot artifacts: `/private/tmp/claude-501/-Users-mjh-Sync-GitHub-Arisbe/00c8e960-9a64-4a3d-9c6b-b8c42666b33a/scratchpad/ablation_pilot.py` (arms A0–A5; micro-demos inline in this brief's transcript). Key citations: `src/attention_economy.py:74-77, 117-123`; `src/arithmetic_world.py:5-10, 52, 107, 121-135, 161-162`; `src/probe_feed.py:25-35, 91-124`; `tests/test_arithmetic_world.py:69-76, 159-229`; `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` §3 (registration, build record, carry list), §5.1; `docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md:34-37, 52-56, 123-129, 151-159`; `runs/RUN_13_LOG.md` F1¹³/F3¹³.
