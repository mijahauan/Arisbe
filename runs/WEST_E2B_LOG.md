# WEST-IN-KYTĒ E2B — run log

**What.** The calibration: characterize **E3's fitness landscape** *before* E3 is designed
(mirrors E1→E2). Three parts, all FED-only, partition unit = the **folder** (a partition is a
bucketing of folders): **Sweep-B** (fixed corpus F₀=12, fixed total effort R=325, bucket count
N ∈ {1,2,3,4,6,12}, both coordinator arms → the cost U-curve); the **p-sweep** (F=6 anchor,
cross-link density p ∈ {0.15..0.75} → does passive coherence break, forcing the broker's first
exercise); the **quality arm** (round-robin vs greedy link-aware bucketing at N=4 → does
partition *quality* have cost teeth). E2b measures a *landscape*, not a *trajectory* — nothing
here tests whether a meta-Agon converges to the optimum; that is E3.

**Design (pre-registered, before any code).**
`docs/superpowers/specs/2026-07-22-west-in-kyte-e2b-design.md` (priors PB1–PB5 in spec §6, each
with a pre-committed refutation; PB5 **amended pre-data** 2026-07-23 to the within-N conjunct
only — the cross-N conjunct compared non-comparable units under fixed-R apportionment). 7-task
subagent-driven build, merged to `main` `6241e24` before the run; full suite **4048 passed / 0
failed**. E1/E2 entry points byte-frozen.

**Config (pre-registered, fixed).** `seed=20260721, F0=12, n=40/folder, p_base=0.15, J=40,
ttl=120, θ=0.20, tol=0.10`; Sweep-B `R=325` fixed (constant total effort at every N); p-sweep
`F=6, R=175`; quality arm `N=4`. Run 2026-07-23 07:02:48–07:38:39 CDT (**35m51s**; the ~1.5–2h
estimate was conservative — only N=1 is expensive), deterministic, canary PASS. Runner: the
assistant, at the author's request (2026-07-23), launched via `tools/run_west_e2b.py` →
`runs/west_e2b_run1/` (numbers-only console: `runs/west_e2b_run1_console.txt`).

---

## Result (2026-07-23, `run_west_e2b.py`, deterministic, canary PASS)

**Part 1 — Sweep-B (fixed corpus F₀=12, fixed R=325, round-robin bucketings, both arms):**

| N | FED Arm N (naive) | FED Arm I (incr) | cut links | member CV | mean member | \|M\|fed | gap | wall s |
|---|---|---|---|---|---|---|---|---|
| 1 | 162,907 | 160,725 | 0 | 0.0 | 160,584.0 | 739 | **0.5795** | 696.0 |
| 2 | 147,688 | 135,326 | 47 | 0.0086 | 67,564.0 | 1,724 | 0.0 | 365.9 |
| **3** | **137,129** | 105,548 | 70 | 0.0088 | 35,085.7 | 1,806 | 0.0 | 212.2 |
| 4 | 146,562 | 86,473 | 71 | 0.0027 | 21,513.2 | 1,853 | 0.0 | 135.5 |
| 6 | 206,565 | 64,114 | 84 | 0.0128 | 10,554.7 | 1,909 | 0.0 | 74.2 |
| 12 | 573,487 | 37,917 | 88 | 0.0024 | 2,954.2 | 1,958 | 0.0 | 29.2 |

K2 = 1.0 and K3 = 0.0 at every point (K3 printed, not asserted; K1 = N/A, raise-only membrane).

**Part 2 — the p-sweep (F=6, R=175):**

| p | gap | coverage | coordinator cost |
|---|---|---|---|
| 0.15 | 0.0 | 1.0 | 595 |
| 0.30 | 0.0 | 1.0 | 666 |
| 0.45 | 0.0 | 1.0 | 666 |
| 0.60 | 0.0 | 1.0 | 666 |
| 0.75 | 0.0 | 1.0 | 666 |

`shoulder_p=None` — no p in range breaches θ=0.20; **the broker was never forced** (its first
exercise did not happen; `broker_routes=None`).

**Part 3 — the quality arm** (N=4, fallback `p=0.75`, flagged **coherence-force-weak(p=max)**
since PB3 refuted): round-robin cost 158,885 vs link-aware 159,050 → link-aware is **0.10%
dearer** (not `tol`=10% cheaper); cut links 296 vs 284 (a 4% reduction). `material=False`.

```
ucurve_naive  argmin_n=3   interior=True
ucurve_incr   argmin_n=12  monotone=True  interior=False
priors: {PB1: held, PB2: held, PB3: refuted, PB4: undetermined, PB5: held}
determinism_canary: PASS
```

## Pre-registered priors — mechanical verdicts

| Prior | Claim | Measured | Verdict |
|---|---|---|---|
| **PB1** (E3's target exists) | Arm-N U-curve has an interior minimum 1 < N\* < 12 | argmin **N\*=3**, interior (162,907 → 137,129 → 573,487) | **held** |
| **PB2** (control — the optimum is coordination, not materialisation) | Arm-I series monotone non-increasing, no interior min | 160,725 → 135,326 → 105,548 → 86,473 → 64,114 → 37,917; argmin at the N=12 endpoint | **held** |
| **PB3** (the coherence force is reachable via link density) | some p\* ∈ (0.15, 0.75] with passive gap > θ=0.20 | gap = 0.0, coverage = 1.0 at **every** p | **refuted** |
| **PB4** (partition quality has teeth), conditional on PB3 | link-aware ≥10% cheaper than round-robin at N=4, coherence-active p | PB3 refuted → force absent; observed at p=0.75: −0.1% (null), cut −4% | **undetermined** (as pre-registered, never refuted on a PB3-null) |
| **PB5** (terminal-unit invariance, amended pre-data) | per-N folder-member CV < 0.5 | max CV **0.0128** (N=6); all others ≤ 0.0088 | **held** |

## What E2b establishes

1. **E3's convergence target exists (PB1).** Under the naive coordinator the cost landscape over
   bucketings has a genuine interior optimum at **N\*=3** (4 folders per bucket at F₀=12): the
   trough is 16% below the N=1 content-monolith and the N=12 full federation is **4.2× the
   trough**. A meta-Agon over folder-bucketings has something non-trivial to find — neither
   endpoint is the answer.

2. **The optimum is a coordination effect, not a materialisation one (PB2, the control).** Under
   the incremental coordinator the same corpus, same bucketings, same rounds cost monotonically
   *less* as N grows — no interior minimum. At N=12 the same federation costs **37,917 (Arm I)
   vs 573,487 (Arm N)** — a **15× spread from coordinator scan discipline alone**, E2's 25×
   finding reproduced at the bucketing level. So the U-curve's right wall is the naive
   coordinator's O(H²) rescan tax, exactly as the two-arm design intended to isolate. E3's
   landscape *has* an interior optimum only under a naive coordinator; under an incremental one
   "more buckets is always cheaper" (at this scale, gap=0).

3. **The coherence force is NOT reachable via link density at this corpus scale (PB3 refuted —
   a reported finding, as the spec provides).** Passive coverage stayed 1.0 across the entire
   pre-registered p-range; the registry never broke and the broker's first exercise did not
   happen. At F=6/n=40/R=175, every member surfaces its whole folder-set, so every cross-link
   target resolves no matter how dense the cross-linking. E3 (or a follow-up p-sweep) must run
   coarser (fewer rounds per member, or smaller ttl, or a larger corpus per member) to exercise
   the broker.

4. **But the coherence force IS real — it arrived by decay, not by link density (the run's
   unplanned finding).** The N=1 Sweep-B point shows **gap = 0.5795**: exactly 51 of the
   corpus's 88 cross-folder links fail to resolve against the content-monolith's own M. The
   mechanism is E2's P4² decay mechanism surfacing as a *coherence* failure: one attention
   budget over 480 notes with `ttl=120` decays 58% of cross-link targets out of its working set
   (|M| saturates at 739 — numerically the same ~740 plateau E2 measured for MONO), while every
   N≥2 bucketing's members hold their folder-sets comfortably (|M|Σ 1,724–1,958, gap 0). So the
   U-curve's left edge is not merely *dearer* — the monolith **cannot even hold the corpus
   coherently at constant total effort**. Coherence in this harness breaks by attention-budget
   saturation, not by cross-link density. This is disposition evidence E3 should carry: the
   force that punishes under-partitioning is decay, and the force that punishes
   over-partitioning is the coordination tax.

5. **Partition quality remains an open premise (PB4 undetermined — honestly).** The observed
   null at p=0.75 (link-aware 0.1% *dearer*, cut links only 4% fewer) is PB3's consequence, not
   evidence about partition quality: with gap=0 the coordinator never pays a coherence price for
   cut links, and at p=0.75 the link graph is near-uniform, so even the greedy min-cut can only
   shave 4% of the cut. The pre-registration's conditional structure did its job — a two-valued
   PB4 would have printed "refuted" and buried E3's quality-search premise on a run where the
   force it tests was absent. **E3's premise that partition quality matters is untested, not
   false.**

6. **Terminal-unit invariance persists across bucketings (PB5, amended form).** Within every N,
   round-robin folder-members cost the same to CV ≤ 0.0128 — the E2 P2² signature carried from
   the size sweep to the bucketing sweep. (The dropped cross-N conjunct was indeed structurally
   doomed: mean member cost runs 160,584 → 2,954 across the sweep because the terminal *unit*
   changes size with N — the pre-data amendment was correct.)

7. **Free cross-experiment consistency check passed.** The N=12 point (per-folder federation,
   R=325) reproduces E2's F=12 FED row **exactly**: Arm I 37,917, |M|fed 1,958, mean member
   2,954.2 — two independently-built drivers, one number. The run is also internally
   deterministic (canary PASS: the N=4 point re-run twice, both arms byte-equal).

## Honesty ledger (what E2b does NOT establish)

- **Landscape, not trajectory.** Whether a meta-Agon *converges* to N\*=3 or *discovers* a
  link-aware bucketing is E3, unbuilt. E3's priors will be registered against these curves.
- **Synthetic, one seed, one topology.** All parts share `seed=20260721`; the U-curve's trough
  location, the 88 cross-links, and the p-sweep null are the generator's, not real reasoning
  corpora. A real-vault corroboration is deferred.
- **The Arm-N interleaving assumption carries over** (members modelled concurrent, harness runs
  them sequentially, ~26% on E2's reference case) — verdict-bearing for **PB1**, the naive-arm
  reading. PB2's arm and the p-sweep/quality parts don't depend on it.
- **The broker was never exercised.** PB3's refutation means the disclosed broker-cost caveat
  (end-of-run snapshot, lower bound) was never even reached; the broker's first exercise is
  still owed.
- **The N=1 gap is an end-of-run snapshot reading.** Coverage is measured against the decayed
  final M (A3-style), so 0.5795 is the *standing* incoherence after R rounds, not a per-round
  trajectory. The mechanism attribution (decay) rests on |M|=739 matching E2's MONO decay
  plateau, not on a per-round trace.
- **N=1 is the content-monolith at constant total effort** (shares R=325 with the journal
  member), NOT E2's dedicated-R MONO — the two monoliths are different fixtures and their
  costs are not comparable across logs.
- **Quality arm ran at the fallback** (p=0.75, coherence-force-weak flag), so its null is
  doubly conditioned. Wall-clock is secondary, never verdict-bearing.
- **The community rung is modelled, never constituted** (THE_COMMENS). The coordinator is a
  switchboard; E3 will *model* partition negotiation inside one instance, not enact a society.

## Disposition & next (the author's)

Mechanically: **PB1, PB2, PB5 held; PB3 refuted (a reported finding with a named remedy); PB4
undetermined (as the conditional pre-registration provides).** E3's fitness landscape is
characterized: an interior optimum N\*=3 exists under the naive coordinator; the right wall is
the coordination tax (scan discipline, 15× at N=12); the left wall is decay-driven incoherence
(gap 0.58 at N=1) — *not* link-density-driven, which never bit in range.

Shaping consequences for **E3** (endogenous partition / meta-Agon over folder-bucketings, next
to be brainstormed→spec'd with these curves in hand):

- E3 has a non-trivial target under Arm N — but under Arm I the optimum is the trivial
  finest partition, so **E3's disposition evidence must name its coordinator arm**.
- The split/merge forces are now measured: **decay-incoherence punishes under-partitioning;
  the naive scan tax punishes over-partitioning**. Both are visible in currencies the panel
  already reads (gap, cost).
- The broker + partition-quality premises remain unexercised; forcing them needs a coarser
  regime (larger per-member corpus, tighter ttl, or fewer rounds) — a candidate E3 rider or a
  small E2b′ cell, the author's call.
