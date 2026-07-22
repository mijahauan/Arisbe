# WEST-IN-KYTĒ E1 — run log

**What.** The first datum of the West-in-kytē program (THE_KYTOS §4; agenda #6): a paired
comparison of two arrangements of reasoning-loop *kytē* over one synthetic vault corpus —
**MONO** (one whole-vault kytos, one big developing M) vs **FED** (one member kytos per folder +
a journal-member + a coordinator kytos). Answers **Q-B** (federation/apportionment) in its paired
form; E2 (the size sweep, the exponent proper) and E3 (endogenous partition) follow.

**Design (pre-registered).** `docs/superpowers/specs/2026-07-21-west-in-kyte-experiment-design.md`
(committed `cb45b7e`, *before* any code). Harness: `docs/superpowers/plans/2026-07-21-west-in-kyte-e1.md`
(branch `west-in-kyte-e1`, 9 TDD tasks, full suite 3933 passed / 0 failed).

**Config (pre-registered, fixed).** `seed=20260721`, `F=6`, `n=40`, `p=0.15`, `J=40`, `R=300`,
`θ=0.20`, `tol=0.10`, `CV<0.5`; round-robin apportionment; oracle unwired.

**Adaptations (author-ratified / disclosed).** A1 — K1 is N/A (raise-only vault membrane, no
world teeth); quality parity judged on **K2 stickiness** (+ K3 ratio + final |M| alongside).
A2 — FED adds a **journal-member** (F+1 members) for work-parity with MONO. A3 (found in the
final review, disclosed) — the coordinator tax is **one end-of-run snapshot**, a *lower bound* on
the pre-registered per-round tax (spec §4.1); it under-counts FED's tax, biasing toward P1.
Refining to a true per-round tax is an E2 candidate.

---

## Result (2026-07-21, `run_west_e1.py`, deterministic, canary PASS)

```
corpus: F=6 n=40 p=0.15 J=40 R=300 seed=20260721 cross_links=47
MONO cost total=188039 (mat=186185 peel=1854)  |M|=752   K2=1.0 K3=0.0 K1=N/A(raise-only)
FED  cost total= 36097 (mat=33584 peel=1847 coord=666)  members=7 (=F+1)
     member_costs=[5888, 5830, 5881, 5895, 5880, 5937, 120]  |M|Σ=1367  K2=1.0 K3=0.0 routes=0
coverage=1.0  gap=0.0  theta=0.2  conflicts=0
priors: {P1: held, P2: held, P3: held, P4: held}
determinism_canary: PASS
```

## Pre-registered priors — mechanical verdicts (author dispositions)

| Prior | Claim | Measured | Verdict |
|---|---|---|---|
| **P1** (Q-B headline) | FED total cost < MONO total cost at comparable quality | 36,097 < 188,039 (**~5.2×** cheaper) at K2 1.0 = 1.0 (within band) | **held** |
| **P2** (Q-C foreshadow) | per-member cost clusters, CV < 0.5 | folder-members 5,830–5,937 (near-identical); CV ≈ 0.40 over all 7 (the journal-member 120 is the only spread) | **held** |
| **P3** (coherence) | passive registry resolves ≥ (1−θ) of cross-folder refs | coverage 1.0 (all 47 cross-links resolved), gap 0.0 ≤ 0.20 → **no broker needed** | **held** |
| **P4** (refutation, pre-committed) | FED refuted if quality falls below band OR coord tax super-linear in F | quality within band; coord tax 666 (sub-linear) | **not refuted (held)** |

**All four priors held.** The federation hypothesis is corroborated in its paired form: at the
pre-registered corpus, FED reasons at ~1/5 the deterministic cost of the monolith while retaining
equal K2 quality, and the *passive* registry alone keeps it coherent (the broker was not needed).

## Notable observations (reported, not verdict-bearing)

- **Cost driver is materialization, as predicted.** MONO mat=186,185 (99.0% of its cost) vs FED
  mat=33,584 — MONO's single M pays the super-linear per-round forward-chain over R=300 as |M|
  fills; each folder-member's M stays folder-bounded and cheap. Peel is ~equal (1,854 vs 1,847)
  and negligible; the coordinator tax (666) is a rounding error against MONO's materialization.
- **Terminal-unit-invariance signal (P2).** The six folder-members cost within ±0.9% of each
  other — a strong clustering signal. This is the Q-C *signal*, not the test; E2's N-sweep across
  community sizes is what actually tests per-kytos invariance.
- **FED retains more total knowledge.** FED |M|Σ = 1,367 vs MONO |M| = 752 — the federation's
  summed model is ~1.8× the monolith's. Consistent with decay pressure: MONO's single attention
  budget over 300 rounds decays more of its working set (ttl=120) than each folder-member's
  smaller, less-contended M does. K2 (stickiness) is 1.0 for both, so this is *more* retained at
  equal durability — a point for FED beyond cost, worth probing in E2.
- **K3 = 0.0 both arrangements.** The vault M carries no Horn laws (all ground metadata facts →
  no `~[ B ~[ H ] ]` to forward-chain), so the compression ratio is trivially 0. True, not a bug.
- **A3 caveat stands.** FED's coord=666 is a lower bound; the per-round tax would be larger but
  remains sub-linear in |M| and negligible against MONO's cost — P1's direction is not at risk.

## Honesty ledger (what E1 does NOT establish — spec §8)

- **The West exponent is not estimable from E1** — two points (N=1 MONO, N=F FED) cannot fit a
  power law. E1 delivers the paired comparison + the harness; the exponent is **E2**.
- **Synthetic ≠ real vault topology** — a real-vault corroboration (structure-only, numbers-only)
  is a deferred check, not part of E1.
- **Q-C only foreshadowed** — P2 reads a variance signal on 6 members of one size; genuine
  terminal-unit invariance needs E2's sweep.
- **Level-transportability caveat** (THE_KYTOS §5) — the community rung E1 probes is where "one
  ledger shape suffices at every level" is a flagged conjecture; E1 is one datum toward it, not a
  proof.

## Disposition & next (the author's)

Program-level rationale, the learnings distilled from this result, and how they shape the next
rungs: **`docs/WEST_IN_KYTE_PROGRAM.md`.**

Mechanically all priors held; the author dispositions whether to accept the paired result and
proceed. **E2** = the size sweep (vary N and/or corpus size, fit the scaling relation — the first
point at which a West exponent is estimable). **E3** = endogenous partition (split/merge as
licensed moves in a meta-Agon over partitions). Candidate refinements surfaced by E1: the
per-round coordinator tax (A3 → true per-round); the FED-retains-more-knowledge observation
(is it a decay artifact or a real federation advantage?); a p-sweep to find where the passive
registry breaks (gap > θ) and E1b (the broker) is forced.
