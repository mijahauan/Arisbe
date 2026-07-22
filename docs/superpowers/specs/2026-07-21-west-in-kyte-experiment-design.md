# West-in-kytē — Experiment E1 design (pre-registered)

**Status:** design-spec only — *no code authorized by this document*. The deliverable is the
pre-registered protocol below. Building E1 is a separate authorization.

**Date:** 2026-07-21
**Agenda item:** the author's 9-topic forward agenda #6 — "West-in-kytē experiments" (see
`CURRENT_PLAN.md` ▶ NEXT SESSION). Answers the West-model questions **Q-B** (federation /
apportionment), **Q-C** (terminal-unit invariance), **Q-E** (vector optimand) posed in
`CURRENT_PLAN` item -8 and carried in the apportionment thread.

**Threads extended:** `docs/THE_KYTOS.md` §4 (the quantitative frontier — West); the
apportionment spectrum (one big Arisbe vs many distributed kytē in concert); the vault cycle
(`docs/superpowers/specs/2026-07-17-vault-cycle-design.md`, World #2). The reduction-theorem
question (Q-A) underwrites the coordination protocol but is out of scope here.

---

## 0 · What this is, in plain terms

There is **no spatial field or lattice** (this is *not* a Game-of-Life grid — Arisbe's loops are
an open negotiated sheet, not a fixed-rule lattice). The "field" is a **corpus**: an
Obsidian-style vault — folders of notes, a dated journal, cross-note wikilinks — read
**structure-only** (the custody discipline; no note bodies). In the experiment the vault is
**synthetically generated** so its size and link-density are controlled knobs.

A **kytos** here is *one running instance of the reasoning loop* — one `agon_evolution.run(...)`
call: a membrane (a `VaultFeed` drawing candidate propositions from some slice of the vault), an
interior **M** (the model it builds), the doubt-cycle (each round: propose → peel against M →
dispose → decay unused facts), a budget, and a horizon. That whole unit is the kytos.

The experiment lays out two **arrangements of kytē over the same vault** and measures the cost /
quality / coherence of each:

- **MONO** — **one** kytos whose membrane reads the *whole* vault; one big developing M. (This is
  what `tools/run_vault_v0.py` does today.)
- **FED** — **one member kytos per top-folder** (each reads only its folder → several small Ms)
  **plus one coordinator kytos** whose membrane reads the members' exported digests (not the
  vault). Members cooperate through the coordinator.

The only structural difference between the arrangements is **how the vault is partitioned across
membranes** — one big mouth, or several small mouths and a switchboard.

**UoDs are developing, not pre-seeded.** Each kytos starts from a tiny common seed (a near-empty
M) and *grows* its UoD round by round as its loop admits surviving facts from its slice. The
quantity under study is precisely **the cost of that growth**: MONO's single M grows to cover
everything (per-round cost climbing super-linearly); each FED member's M only ever covers one
folder (staying small and cheap); the coordinator's M grows only in proportion to how much the
folders talk to each other. (An alternative — pre-seed every kytos identically to isolate
steady-state cost — was considered and rejected for E1: growth-cost is the West-relevant
quantity and is what the machinery produces natively. It is a candidate variation for a later
rung.)

---

## 1 · The ladder (E1 full; E2/E3 named)

Per the "E1 only, in full depth" scoping decision, only E1 carries a pre-registered protocol and
priors. E2 and E3 are named here to show the progression; their priors are **not** pre-registered
in this document.

- **E1 — paired comparison (this document).** MONO vs one fixed per-folder FED on one generated
  corpus. Delivers the paired cost/quality/coherence comparison **and the measurement harness**.
  Answers Q-B in its paired form.
- **E2 — the size sweep (future).** Vary the partition granularity (N = 2, 4, 8, … member kytē,
  and/or corpus size) and fit the scaling relation. This is where a West **exponent** first
  becomes estimable (E1's two points, N=1 and N=F, cannot fit one). Tests Q-C (per-kytos
  cost-per-doubt-cycle invariance as the community grows).
- **E3 — endogenous partition (future).** Make apportionment itself a licensed, recorded move:
  split/merge of kytē as proposals in a meta-Agon over partitions, adjudicated by measured
  cost/K curves. Tests whether self-partitioning converges and whether its exponent beats the
  monolith's at equal K1/K2 (Q-B's second form).

---

## 2 · E1 — configurations

### 2.1 MONO

`VaultWorld(root)` → one `VaultFeed` → one `agon_evolution.run(seed, feed, rounds=R, …)`.
Coherent by construction (single M). Pays super-linear per-round cost as |M| fills — the
already-evidenced monolith pain (F1¹³ 53-occlusion save; the 36-min layout at |V|≈1265; the
`live_runner` doc's measured super-linearity in |M|). MONO pays **zero** coherence tax.

### 2.2 FED

For each top-folder `k` in `VaultWorld.top_dirs()`: a **member kytos** = a `VaultFeed` scoped to
folder `k` only → its own `run(...)` with its own small M. Plus one **coordinator kytos** (§3).
FED bounds each member's |M| by folder size but must **buy back** coherence through the
coordinator. E1 measures whether that trade is favorable.

Both arrangements run the **same number of total rounds R** over the **same generated corpus**
so cost/quality are compared on equal work. (FED's R is apportioned across members; the
apportionment policy is a pre-registered constant — round-robin across members by default.)

---

## 3 · The corpus — parameterized synthetic generator

A generator (spec only — a future `tools/` or `src/` module, name TBD at build time) producing a
`VaultWorld`-readable tree:

`vault_generator(seed, folders=F, notes_per_folder=n, cross_folder_link_prob=p, journal_len=J)`

- **Deterministic** given `seed` — fixed, checked-in, publishable.
- **Metadata-only** — sentinel bodies (a `SENTINELBODY`-style marker), honoring the structure-only
  custody constraint; the reader never needs bodies.
- **`p` controls cross-folder link density** — the independent variable that makes the coherence
  tax measurable and, in E2, sweepable. `p` is the per-note probability that a note's wikilink
  points into *another* folder.

**Pre-registered E1 corpus configuration** (chosen to give MONO a non-trivial |M| and to make the
coherence gap straddle the θ threshold interestingly):

| knob | value | rationale |
|------|-------|-----------|
| `seed` | `20260721` | fixed for reproducibility |
| `F` (folders) | `6` | enough members to read variance across FED kytē |
| `n` (notes/folder) | `40` | MONO |M| reaches the super-linear regime (~240 notes total) |
| `p` (cross-folder link prob) | `0.15` | expected to straddle θ = 0.20 (see §4) |
| `J` (journal length) | `40` | a dated spine the journal-want feeds on |
| `R` (total rounds) | `300` | past the per-round-cost divergence point measured in the runs |

These are **priors on the design**, tunable *once* at build if a dry run shows |M| never enters
the super-linear regime — but any change is recorded, and the *comparison logic* and *thresholds*
below are fixed now.

---

## 4 · The coordinator — two variants, one pre-registered decision rule

Both members export the same artifact after each of their rounds: a **digest** = their M
projected to attributed relation-name cells `(asserts "folder-k" ⌜rel⌝)` — **mention-not-use**,
structure-only, so nothing crosses a boundary as a live asserted fact (the attributed-cell /
quotation protocol; Q-A underwrites that arbitrary mention-depth reduces to the one B-min
device).

### 4.1 Passive registry (thin — the baseline)

The coordinator **holds** the union of member digests and runs one **consistency scan** per
round: does folder-A's digest assert what a folder-B digest denies? It does **no** routing.

- **Coherence read (passive):** of the corpus's cross-folder wikilinks, the fraction that land on
  a cell the coordinator holds (**coverage**); the count of digest-level consistency conflicts.
- **Tax:** digest maintenance + one scan/round. Grows with `F` + digest size — **sub-linear in
  |M|**, never |M|².

### 4.2 Active broker

Everything the registry does, **plus** routing: when a member's proposal references a target
resident in another folder (a cross-folder wikilink), it queries the coordinator, which routes to
the owning member and returns the attributed fact (dis-quotation by episode — the community
protocol).

- **Tax:** registry tax + **one route per cross-folder reference actually touched**. This is the
  real coordination workload of a linked vault.

### 4.3 The decision rule (pre-registered — honors "let the data decide")

E1 runs the **passive registry as baseline** and reports the **unresolved-cross-folder-reference
fraction** (the coherence gap = 1 − coverage).

**Pre-committed threshold θ = 0.20:**
- gap ≤ θ → the thin registry suffices; the passive result **is** E1's answer.
- gap > θ → the registry is provably too thin (federation cannot stay coherent passively);
  **E1b** re-runs with the active broker, and the tax comparison uses E1b's numbers.

Either outcome is a recorded finding, not a failure.

---

## 5 · Measurements

### 5.1 Cost — deterministic primary, wall-clock secondary

A pre-registered experiment cannot hinge on non-deterministic timing.

- **Primary (deterministic):**
  `COST = Σ_rounds ( atoms forward-chained by the materializer + peel-layer visits )`,
  read from the `IncrementalMaterializer` counters (`rebuilds` / `extensions` / `hits`) and the
  peel transcript depth. **FED adds coordinator cost** = digest cells written + consistency-scan
  comparisons + broker routes (E1b). Reported three ways: **total**, **per-round**,
  **per-doubt-cycle-per-member**.
- **Secondary (reported, not decisive):** wall-clock — recorded for ecological color; **no
  verdict rests on it** (the irreproducible quantity the apportionment memory flags).

### 5.2 Quality — held equal by tolerance band

- **K1** — severity-weighted track record (`Σ_hits sev − Σ_misses sev`).
- **K2** — durability / stickiness (from `agon_metalearning`).
- For FED, aggregated across members + coordinator. Parity is judged by a **tolerance band**
  (pre-registered `tol = 10%` of MONO's value), not exact equality.

### 5.3 Secondary observations (reported, not verdict-bearing)

- **K3** — `model_materialization.materialization_ratio` per config (per-member + community
  aggregate for FED).
- **Poise** — `agon_metalearning.poise_report` per member and for MONO.
- **Question yield** — P2-style oracle-note count/quality per config, *if* the oracle loop is
  wired into the arrangement; may be deferred (the oracle loop is already per-kytos).

---

## 6 · Pre-registered priors (Pᴱ¹ — committed *before* any run)

- **P1 (Q-B, headline).** `FED total COST < MONO total COST` on the same corpus, at
  `FED K1/K2 ≥ MONO K1/K2 − tol`. Rationale: MONO's per-round cost is super-linear in |M|
  (evidenced); each FED member's |M| is folder-bounded; the coordinator's tax is sub-linear in
  |M|. **Predicted direction: FED wins.**
- **P2 (Q-C foreshadow).** FED's per-kytos cost-per-doubt-cycle is *lower* **and** *lower-variance*
  than MONO's single cost-per-cycle; across the F members it clusters (coefficient of variation
  below a pre-registered bound `CV < 0.5`). This is the terminal-unit-invariance **signal**;
  E2's N-sweep is what actually tests it.
- **P3 (coherence).** The passive registry resolves ≥ (1 − θ) of cross-folder consistency at the
  pre-registered `p`. If violated → P3 refuted → active broker required (E1b). Recorded either
  way.
- **P4 (refutation, pre-committed).** The federation hypothesis is **refuted** if *either*
  (a) coordination tax grows **super-linearly** in `F` (FED loses at scale), *or* (b) FED's K1/K2
  fall below the tolerance band because partitioned Ms cannot derive facts the monolith's single M
  could (the coherence–cost trade is unfavorable). Committing the losing condition in advance is
  the Pⁿ/Fⁿ discipline.

---

## 7 · Determinism canary

Two fresh runs of each configuration must produce **byte-identical** digests and journals — the
S4-style check the arithmetic (`replay_choices`) and vault stages already use. A divergence is a
build defect, not a result.

---

## 8 · Honesty ledger (what E1 does *not* establish)

- The West **exponent proper is not estimable from E1** — two points (N=1 MONO, N=F FED) cannot
  fit a power law. E1 delivers the *paired comparison* and the *measurement harness*; the exponent
  is **E2**.
- **"Equal K1/K2" is a confound** — handled by a tolerance band, not exact equality; a FED win on
  cost *with* a K-quality drop inside the band is a weaker result than a win at equal quality, and
  is reported as such.
- **Synthetic ≠ real vault topology** (ecological validity) — a real-vault corroboration (run once,
  structure-only, numbers-only digest) is a *deferred* check, not part of E1.
- **Level-transportability caveat** stands (THE_KYTOS §5): the measures are instrumented at
  levels 1–4; the community rung E1 probes is where "one ledger shape suffices at every level" is
  a flagged conjecture, and E1 is one datum toward testing it, not a proof of it.
- **Q-C is only foreshadowed** — P2 reads a variance *signal* on F members of one size; genuine
  terminal-unit invariance needs E2's sweep across community sizes.

---

## 9 · Build surface (for a future implementation plan — informational)

E1, when authorized, would need (nothing built by this document):

- a **vault generator** (deterministic, structure-only, sentinel bodies);
- a **coordinator kytos** module — digest projection (`(asserts "folder-k" ⌜rel⌝)`), the
  consistency scan (passive), the router (active); reusing the attributed-cell / `world_scroll`
  residence machinery, mention-not-use;
- an **arrangement runner** — orchestrates MONO and FED over one corpus, apportions R, collects
  the cost/quality/coherence measurements (built on `agon_evolution.run` + the existing
  `IncrementalMaterializer` counters + `agon_metalearning` readers; *not* `run_ablation`, which
  varies parameters on a single kytos and does not model a federation);
- a **report** — the paired comparison, the θ decision, the four priors' verdicts, the
  determinism canary, emitted as a numbers-only digest (custody-safe).

---

## 10 · Decisions (ruled by the author, 2026-07-21)

1. **θ and the E1 corpus knobs** (§3, §4.3) — **ACCEPTED as pre-registered** (seed=20260721,
   F=6, n=40, p=0.15, J=40, R=300; θ=0.20; tol=10%; CV<0.5). Fixed for the pre-registration.
2. **Question-yield inclusion** (§5.3) — **DEFERRED.** The oracle loop is *unwired* in E1;
   question-yield is not measured. A candidate for a later rung.
3. **Round apportionment policy** (§2.2) — **RULED: round-robin now**, with the option to
   introduce a severity-weighted apportionment later *if indicated* by E1's results (recorded
   then as a deliberate variation, its cost-comparison confound noted).
