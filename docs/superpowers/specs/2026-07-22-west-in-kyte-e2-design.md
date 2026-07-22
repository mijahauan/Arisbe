# West-in-kytē E2 — the size sweep (design spec, pre-registered)

> **Status:** design spec, committed *before* any E2 code. The Pⁿ/Fⁿ discipline: the priors in §6
> are committed here, in advance, with a pre-committed refutation.
>
> **Predecessors.** E1 design spec `2026-07-21-west-in-kyte-experiment-design.md` · E1 harness plan
> `2026-07-21-west-in-kyte-e1.md` · E1 result `runs/WEST_E1_LOG.md` · program-level design-of-record
> `docs/WEST_IN_KYTE_PROGRAM.md` (§5 shapes this spec).
>
> **Companions.** `docs/THE_KYTOS.md` §4 (the quantitative frontier) · `docs/THE_MEASURE_OF_KNOWLEDGE.md`
> (K1–K4) · `docs/THE_COMMENS_AND_THE_COMMUNITY.md` (why the community rung is a change in kind).

---

## 0 · What this is, in plain terms

E1 compared **one** whole-vault reasoning kytos (MONO) against **one** fixed federation of
per-folder kytē (FED) on **one** corpus, and found FED ~5.2× cheaper at equal K2. Two points
cannot fit a power law, so E1 established a paired result and a reusable harness — not an
exponent.

E2 **grows the system** and fits the curve. We vary corpus size and the member count together
(one kytos per folder, so system size and community size grow as one), give each folder a constant
share of attention, and read how total reasoning cost scales. The output is two exponents — β_mono
and β_fed — and the answer to whether apportionment's advantage is a fixed-size artifact or a
scaling property.

E2 also pays down the one fidelity debt E1 disclosed (A3, the coordinator tax measured as an
end-of-run snapshot), fixes a measurement defect found while designing this spec (§3), and carries
one rider probing E1's most surprising observation (§5).

**What this is not.** E2 does not test endogenous partition (that is E3), does not use a real
vault (a deferred corroboration), and — per `docs/THE_COMMENS_AND_THE_COMMUNITY.md` — *models* a
federation of kytē without constituting a community. The coordinator is a switchboard, not a
society. That flag binds every number here.

---

## 1 · The question E2 answers

**Q-C (terminal-unit invariance), primary.** As the community of kytē grows, does per-kytos
cost-per-doubt-cycle stay invariant? Equivalently: fitting `COST ∝ S^β` over system size S, is
β_fed materially below β_mono?

**Q-B (federation/apportionment), in its scaling form.** E1 answered Q-B pairwise at one size. E2
asks whether the advantage *survives growth* — or whether coordination cost eventually eats it.

**Q-E (the vector optimand), touched by the rider.** E1's FED retained ~1.8× more total knowledge
at equal K2. If that survives a ttl sweep it is a vector effect the scalar exponent cannot see.

---

## 2 · The sweep grid (pre-registered, fixed)

| knob | value | rationale |
|---|---|---|
| `F` (folders = folder-members) | **{2, 4, 6, 8, 12, 16}** | six points; enough to fit a power law with a reported fit quality |
| `n` (notes per folder) | `40` | E1's value, held fixed so F alone carries system size |
| `R` (total rounds) | **`25·(F+1)`** (75, 125, 175, 225, 325, 425) | *proportional-R*, §2.1 |
| `p` (cross-folder link prob) | `0.15` | E1's value; the p-sweep is deferred (§8) |
| `J` (journal length) | `40` | E1's value |
| `seed` | `20260721` | E1's seed — same generator, same topology family |
| `ttl` | `120` for the sweep; `{60, 120, 240, off}` for the rider | E1's value; §5 |
| `θ`, `tol` | `0.20`, `0.10` | E1's decision rule carried forward unchanged |

System size **S := F**. Because `n`, `p`, `J` are fixed, total notes = `F·n + J` is affine in F,
and the member count is `F + 1` (A2's journal-member). Reporting uses S = F throughout; the
affine offset from J is disclosed with the fit.

### 2.1 Why proportional-R (author-ruled)

Under `R = 25·(F+1)`, FED apportions R round-robin across `F+1` members
(`west_experiment._apportion`), so **each member performs exactly 25 rounds at every F** — per-unit
attention is constant while the system grows. That is West's setup: system size grows, per-unit
demand is held fixed, read total cost against size. β<1 would be a genuine economy of scale;
β>1 a diseconomy.

The `F+1` (rather than `F`) is deliberate: a bare `R = 25·F` would hand each member
`25F/(F+1)` rounds — 16.7 at F=2 rising to 23.5 at F=16, a ~40% drift in per-unit attention across
the sweep, which would contaminate P2² (§6) precisely where it measures per-member flatness.

*Disclosed consequence of the fix:* MONO's round count is now **affine** in F, so
`COST_mono ∝ (F+1)^1.2·F^0.6` is not a pure power law and carries slight curvature at small F. The
fit is still reported as β over `log F` (§4); the curvature is disclosed with it, and the fitted β
is understood as the large-F asymptote (≈1.8).

Fixed-R (the alternative, not chosen) holds total effort constant while the corpus grows, which
measures coverage-at-constant-work — a different question, and not West's.

**Disclosed consequence.** Under proportional-R, MONO runs `25·(F+1)` rounds against a single growing
M while each FED member runs ~25 rounds against a folder-bounded M. This is not a thumb on the
scale: it is the arrangement difference under test, at equal total doubt-cycles.

---

## 3 · Measurement corrections carried into E2

### 3.1 A3 paid down — the true per-round coordinator tax

E1 measured the coordinator tax as **one end-of-run snapshot** (ingest each member's final M once,
plus one scan/coverage pass) — disclosed as a *lower bound* on the pre-registered per-round tax
(E1 spec §4.1), biasing toward P1.

**E2 implements the per-round tax by post-hoc coordinator replay.** Member runs are unchanged;
each member's per-round M is recovered from the states its `EvolutionResult.chain` already holds,
and the coordinator is replayed round-by-round over those states. This is **exact** for the passive
arrangement, because the passive coordinator is read-only — it never routes and never affects
member dynamics — so replaying it cannot change what it measures. Determinism is preserved.

*Limit, disclosed:* the replay is exact only for the **passive** coordinator. The active broker
feeds routes back to members, so a broker arm would require true lockstep. E1 found gap = 0 at
p=0.15 (the broker never fired), so E2 runs passive; if any swept F yields gap > θ, that config is
reported as broker-forced and its tax is marked *not replay-exact* rather than silently reported.

### 3.2 The two coordinator cost models (author-ruled: report both)

Designing this spec revealed that `west_coordinator.consistency_scan` is **O(H²)** in held cells
(its own docstring says so), where the held-cell count fits **`H ≈ 5.9·F`** exactly against E1's
measured totals (`H(H+1)/2` = 66 at F=2 → H=11; 666 at F=6 → H=36; 1128 at F=8 → H=47). The
per-round tax therefore depends entirely on *what a coordinator does each round*, and the two
defensible answers give opposite verdicts:

- **Arm N (naive rescan).** A full O(H²) scan every round — what E1 spec §4.1 literally
  pre-registered ("one scan/round"). Tax ≈ `H + R·H(H−1)/2` ≈ **17·F²·R**, which under
  proportional-R is **∝ F³**.
- **Arm I (incremental scan).** Only cells that changed this round are compared against the held
  set. Since ΣΔH over a run equals H, total scan work ≈ O(H²) **for the whole run regardless of R**
  — which means E1's "lower-bound snapshot" was in fact the correct number for an incremental
  coordinator.

Both arms replay the *same* captured member states, so reporting both costs nothing extra. Both are
reported at every F, and both β_fed values are published. Choosing one model in advance would have
been choosing the verdict in advance; this is the "let the data decide" commitment applied to a
design assumption rather than to a result.

### 3.3 P2's CV statistic — a defect found and fixed

E1 read the per-member cost CV over **all** `F+1` members, including the journal-member. A probe at
F=2 returned `member_costs=[4506, 4288, 120]` and `P2: refuted` — but the two folder-members are
within 2.5% of each other (CV ≈ 0.035); the journal-member's 120 is a ~30× outlier that alone drives
the all-member CV to 0.68. At F=6 five more folder-members dilute the same outlier to CV ≈ 0.40 and
P2 reads "held".

**E1's P2 statistic therefore moves with F for reasons unrelated to terminal-unit invariance** —
fatal for a size sweep. E2 reads CV over **folder-members only** and reports the journal-member's
cost separately as a disclosed non-member figure. This is a correction to the instrument, not a
re-reading of E1's data; E1's F=6 verdict is unaffected in direction (folder-member CV at F=6 is far
below θ).

---

## 4 · Measurements

**Primary (deterministic), unchanged from E1 spec §5.1:**
`COST = Σ_rounds (atoms forward-chained by the materializer + peel-layer visits)`, from
`CountingMaterializer`, plus for FED the coordinator cost — reported **twice**, once per arm (§3.2).

**Reported per config:** `COST_mono`, `COST_fed(N)`, `COST_fed(I)`, the FED split
(materialisation / peel / coordinator), per-folder-member costs, folder-member CV, journal-member
cost, final |M| (MONO) and |M|Σ (FED), K2, K3, coverage, gap, conflicts, routes.

**The fit.** Ordinary least squares of `log COST` on `log F` across the six points, reporting β, its
standard error, and R². Reported for MONO, FED(N), and FED(I) separately. Fewer than six usable
points, or R² < 0.90, is reported as a **weak fit** and the corresponding prior is recorded
*undetermined* rather than held or refuted.

**Secondary (never verdict-bearing):** wall-clock, recorded for ecological color. Measured scaling
from the design probe: MONO wall ∝ F^1.0·R^1.6, ~9× FED at F=2. Projected sweep budget **≈ 3 h**
(MONO ≈ 141 min, FED ≈ 2 min, ttl rider ≈ 28 min, one determinism canary at F=6 ≈ 7 min). This is a
launch-and-check-back run, not an interactive one.

**K1 remains N/A** (adaptation A1 — the vault membrane is raise-only, no world teeth). Quality
parity is judged on K2 within `tol`, with K3 and |M| reported alongside. K3 is expected to remain
0.0 (the vault M carries no Horn laws); that is true, not a bug.

---

## 5 · The rider — |M| retention vs decay pressure

E1's most surprising observation: FED |M|Σ = 1367 vs MONO |M| = 752 (~1.8×) at equal K2. The
working hypothesis is **decay pressure** — MONO's single attention budget over R rounds decays more
of its working set than each member's smaller, less-contended M does.

**Rider design.** One mid-size config (F=6, R=175), MONO and FED, at `ttl ∈ {60, 120, 240, off}`.
Read the FED/MONO |M| ratio at each.

- If the ratio **narrows monotonically** as ttl → off: FED-retains-more is a decay artifact (P4²
  held). It remains a real operational advantage under decay, but not a structural one.
- If it **does not narrow**: the decay explanation is refuted and the retention advantage is
  structural — a Q-E vector effect invisible to the cost exponent, and an input to E3's fitness.

`ttl=off` means no disuse-decay. Journal-spine pinning (`JOURNAL_SPINE_RELATIONS`, the RUN-13 F4¹³
fix) stays on in every rider cell so the arm varies decay pressure only.

---

## 6 · Pre-registered priors (Pᴱ² — committed before any run)

- **P1² (headline exponent, Ruling B — 2026-07-22).** Three-valued, not two: **"held"** requires
  β_mono > β_fed(I) *and* β_mono > 1.3; **"separation-only"** is the genuinely different case where
  separation holds (β_mono > β_fed(I)) but the 1.3 magnitude bar is missed — it gets its own name
  rather than being folded into a refutation it isn't; **"refuted"** is reserved for the one
  pre-committed condition below. Either fit weak → "undetermined", checked first.
  *Predicted from the design probe:* β_mono ≈ 1.8 (measured `cost ∝ F^0.6·R^1.2`, times R ∝ F);
  β_fed(I) ≈ 1.0 (FED cost is flat in F at fixed R — 8,980 → 9,214 → 9,575 across F=2,4,8 — so
  under proportional-R it is `F+1` members × constant work).
- **P2² (Q-C terminal-unit invariance).** Per-kytos cost-per-cycle stays flat as the community
  grows: **folder-member CV < 0.5 at every F**, *and* the mean per-folder-member cost's
  **max/min ratio across the six configs < 1.25**.
- **P3² (coordination is the binding constraint, Ruling A — 2026-07-22).** Under **Arm N**,
  coordinator tax ∝ F^γ with **γ ≥ 2**, **and** a crossover exists where `COST_fed(N) > COST_mono`.
  A crossover is read one of three ways, most informative first: **observed** — a genuine
  within-range transition (FED at-or-below MONO at a smaller swept F, above it at a larger one);
  **below-range** — FED-naive is above MONO at *every* swept F, so no transition is observed but
  none is needed either — the crossover, if any, lies below the range, which is the *strongest*
  confirmation coordination binds, not a refutation; **extrapolated** — the two fitted lines cross
  strictly above the swept range (`> max(F)`). An extrapolated F* that lands at or inside the range
  is a fit artifact, not a finding, and falls back to **below-range** (if FED dominated the whole
  swept range) or **none** (otherwise) rather than being reported as a number (a review probe once
  produced a physically meaningless `crossover_f` of ~0.02 folders this way — no E2 run has been
  executed yet). γ ≥ 2 with no crossover of any kind reads "refuted" — coordination diverging without
  ever being shown to overtake MONO is not the binding constraint the prior claims.
  **Weak-fit gating, checked in this order (Task 7 re-review, third pass, 2026-07-22):** (1)
  `fit_tax_naive` weak → "undetermined", checked first, since γ itself is unusable. (2) The
  determinate **γ < 2** refutation is decided next, off `fit_tax_naive` alone, *before* the
  crossover is consulted at all — a weak crossover fit must never suppress a refutation the tax fit
  alone already settles. (3) Only once γ ≥ 2 is established, a second gate applies to a crossover
  reading of **extrapolated** *or* **none** — both are decided entirely off
  `fit_fed_naive`/`fit_mono` (an extrapolated F* is read off their intercepts; a "none" reading is
  either β_fed_naive ≤ β_mono or an extrapolated F* landing inside the range), so if either of
  *those* fits is weak the reading cannot be trusted: P3² reads "undetermined" rather than "held"
  (extrapolated) or "refuted" (none) off a fit too blunt to support it. An **observed** or
  **below-range** crossover is read off the swept data, not off a fit, and needs no such gate.
- **P4² (the rider).** The FED/MONO |M| ratio narrows monotonically as ttl → off.

**Pre-committed refutation.** **β_mono ≤ β_fed(I)** refutes the federation hypothesis in its
*scaling* form: E1's paired win would then be an artifact of one corpus size rather than a property
of apportionment. This is recorded as a finding, not a failure. Per Ruling B this is the *only*
condition "refuted" is reserved for in P1² — a below-bar-but-separated result is "separation-only".

**Stated in advance, so it is not spun afterward:** *no arrangement is predicted to show West's
sublinear β < 1.* A federation of independent kytē is linear by construction. What E2 can establish
is **diseconomy avoided**, not economy of scale achieved. Any post-hoc claim of a West-style
economy of scale from these numbers would be unwarranted.

---

## 7 · Determinism canary

One config (F=6, R=175) is run twice end-to-end; MONO and FED total costs must match exactly.
Reported PASS/FAIL on every run. The full six-point sweep is not double-run (wall-clock), and that
narrowing relative to E1 is disclosed.

---

## 8 · Honesty ledger — what E2 does *not* establish

- **Synthetic ≠ real.** An exponent fitted on the generator's topology is an exponent *of that
  generator*. A real-vault corroboration (structure-only, numbers-only, custody-safe) remains
  deferred.
- **One seed, one topology family.** All six points share `seed=20260721` and `p=0.15`. Sensitivity
  to seed and to link density is not measured; the **p-sweep crossover** (program doc learning 4 —
  where the passive registry breaks and the broker is forced) is explicitly **deferred to E2b**.
- **Six points.** A power-law fit on six points with one varying knob is a weak instrument; β is
  reported with standard error and R², and a weak fit yields *undetermined*, not a verdict.
- **Arm N may be a strawman; Arm I may be a steelman.** Neither is the "true" coordinator. E2
  reports the *bracket* the two arms define, and where in that bracket a real coordinator would sit
  is an open question, not a result.
- **Broker untested at scale.** §3.1's replay is exact only for the passive coordinator.
- **The community rung is modelled, never constituted** (THE_COMMENS). The level-transportability
  conjecture (THE_KYTOS §5, "one ledger shape suffices at every level") is where a skeptic should
  attack; E2 is a datum toward it, not a proof.

---

## 9 · Build surface (informational — for the implementation plan)

E2 is chiefly a **driver plus a measurement refinement**, not a new subsystem. The E1 harness is
already parameterised on F/n/p/R/ttl.

- `src/west_coordinator.py` — add an incremental scan path alongside the existing O(H²) rescan so
  both arms are measurable; keep the existing behaviour intact and default.
- `src/west_experiment.py` — capture per-round member states and expose the post-hoc coordinator
  replay (§3.1); read folder-member CV separately from the journal-member (§3.3).
- `src/west_measure.py` — the OLS log-log fit returning (β, stderr, R²), with the weak-fit rule.
- `tools/run_west_e2.py` — the sweep driver: loops the grid, runs the ttl rider, emits the fit and
  the P1²–P4² verdicts, **numbers-only stdout** (custody: never a note id/title/path), plus the
  determinism canary.
- Tests mirror E1's per-module test files.

Zero protected-core modification is anticipated. Any need for one halts the build for authorization.

---

## 10 · Decisions (ruled by the author, 2026-07-22)

1. **Sweep A only** — corpus size at fixed granularity. The granularity sweep (fixed corpus, varying
   N — the optimal-terminal-unit U-curve) is **not** part of E2; it becomes a candidate only if E2
   shows a rising coordination tax worth chasing.
2. **Proportional-R primary** (`R = 25·(F+1)`, so each member gets exactly 25 rounds). Fixed-R is
   not run.
3. **Both coordinator arms reported** (§3.2), rather than picking one model in advance.
4. **ttl rider included** (§5). The **p-sweep crossover is deferred** to E2b.
5. **Task 7 re-review, crossover + weak-fit refinement (2026-07-22).** §6's P1²/P3² text above is
   corrected to match what the code actually decides: P1² is three-valued (Ruling B) and P3²'s
   crossover clause admits a **below-range** reading, distinct from "none" (Ruling A implemented
   honestly) — FED dearer than MONO across the whole sweep is the strongest support for the prior,
   not a refutation-by-omission. An extrapolated crossover additionally requires (a) landing above
   `max(F)`, never a fit artifact reported as a number, and (b) `fit_fed_naive`/`fit_mono` both
   strong — an extrapolation resting on a weak fit reads "undetermined", never "held".
6. **Task 7 fix-4 doc pass (2026-07-22).** §6's "Weak-fit gating" paragraph had drifted from the
   code it describes: it named the second gate as covering only an **extrapolated** crossover
   (it also covers **none**), said the suppressed verdict for that case was "held" (for "none" it
   is "refuted"), and left the checking order — tax-weak, then the determinate γ < 2 refutation,
   then the crossover weak-gate — undocumented. Corrected to match `assemble_e2_report`'s docstring
   exactly, which remains the source of truth for this ordering.
