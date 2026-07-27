# West-in-kytē E3c — the symmetry-breaking rider (run log)

> **Spec:** the E3b design spec §10 (`docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md`
> — the rider pre-registered there before any E3c code; priors PS1/PS2 fixed at pre-registration).
> **Build:** driver `tools/run_west_e3c.py` + smoke contract tests, green before launch
> (2026-07-26 sitting). **Run:** `tools/run_west_e3c.py --dest runs/west_e3c_run1/work`,
> started 2026-07-26 21:50, finished 2026-07-27 ~07:26 local — wall 34,469 s (~9.6 h),
> numbers-only output `runs/west_e3c_run1/e3c_full.txt`. Deterministic; **canary PASS**.
> Memo: 21 hits / 58 misses.
>
> Run facts: mode=full, seed=20260721, F0=12, n=40, p_base=0.15, J=40, ttl=120, R=325,
> θ=0.2, merge_k=3, max_rounds=20; base = the stranded round-robin **4/4/4** (E3b Finding 2,
> the 137,129 terminal optimum 35% dear); cells = ((0,1), (1,2), (2,0)) — three pre-registered
> single-folder perturbations (move one folder between the named buckets), each descended
> through the verbatim Arm-N walk (split/merge only — the walk cannot rebalance to 4/4/4;
> escape vs strand is which basin the descent finds). Sizes only (custody).

## The result, in one paragraph

Single-folder symmetry-breaking does **not** guarantee escape from the dear band. Of the three
perturbed starts, **one** (cell 0→1, start 5/4/3) descends into the dominant **10/1/1 cheap
family** at 102,287 — inside E3b's 1.4% floor band; the other **two** (cell 1→2, start 4/5/3 →
**4/7/1 @ 119,301**; cell 2→0, start 5/4/3 → **7/4/1 @ 119,543**) terminate at **new dear
optima** just above the dear band's lower edge (118,865), both genuinely terminal
(`shadowed=False`). The stranding around balance is therefore not a measure-zero knife-edge at
the exact 4/4/4 point but a **positive-measure dear basin**: breaking the symmetry by one
folder can merely relocate the walk within the dear region. Which perturbation escapes is a
matter of *direction* — the third echo of the direction-selects result (E3's PE2, E3b's PM2/
Finding 3). The two new termini raise the count of known distinct terminal optima **19 → 21**;
the floor is untouched.

## Priors → verdicts

| Prior | Claim (pre-registered) | Observed | Verdict |
|-------|------------------------|----------|---------|
| **PS1** (knife-edge) | every perturbed terminus escapes the dear band (< 118,865) | 1 of 3 escaped (102,287); two termini at 119,301 and 119,543 — above the bar | **refuted** |
| **PS2** (floor) | no perturbed terminus lands below 101,411 (E3's W2 / E3b's floor) | cheapest terminus 102,287 ≥ 101,411 | **held** |

## Disposition (the author, 2026-07-27)

**PS1 refuted-as-finding; PS2 held.** The refutation is adopted as the finding: **stranding is
a basin, not a knife-edge** — E3b's "balance strands" sharpens to *near-balance strands*: the
dear region has positive measure around the balanced configuration, and single-folder
symmetry-breaking guarantees nothing; the escape route exists (one direction found the cheap
family) but is direction-dependent. PS2's hold closes the floor question a second time: no
cheaper basin was hiding under the perturbations either.

**The West E-series is CLOSED at E3c (author ruling, same date).** E1–E3c all disposed. The
standing findings of the series: federation's cost advantage is a *scaling property* (E1, E2);
the interior partition optimum N\*=3 with coordination the binding constraint (E2b);
endogenous partitioning converges to the granularity, multi-basin, direction-selects (E3);
granularity converges absolutely / bucketing fragments / cost concentrates, balance strands
(E3b); the stranding is a positive-measure basin and the floor stands (E3c). Further West
work, if any, emerges from the reorganized spine's queued conjectures (cross-level exponents;
the community rung; open-membrane superlinearity — THE_KYTOS §4/§5), not from a next rider.
