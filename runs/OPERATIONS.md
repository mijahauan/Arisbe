# Live-run operations runbook

The operator-facing companion to the `runs/RUN_*_LOG.md` lab notebooks. It consolidates the
two things scattered across `--help`, `docs/AUTOMATED_ENDOPOREUTIC_GAME.md` §10, and the run
logs: **what every digest field means (with healthy vs. stop thresholds)** and **how to
dispose of a finished run**. The launch / stop / resume *flow* is in the driver's `--help`;
this is the read-the-instruments and close-the-run half.

Driver: `tools/run_live_wikidata.py`. Launch (the standard duration probe):

```bash
uv run python tools/run_live_wikidata.py --source recentchanges \
    --runs-dir runs/runN --max-seconds 28800 --ttl 8 --ttl-unit polls
```

Stop early: create the STOP file the driver prints at launch (`touch runs/runN/STOP`).
Resume after a crash/kill: re-run the same command with `--resume` (the decay clock and the
crawl continue, never reset).

---

## 1. Digest-field glossary — what to watch, and when to stop

Each segment prints one console line; the final summary repeats them for the whole run. Read
them left to right. "Stop / investigate" means *pause and diagnose* — usually a `touch STOP`,
read the state, and decide — not that the run is ruined (most conditions are absorbed and
counted, by design).

| Field | Means | Healthy | Stop / investigate |
|---|---|---|---|
| `rounds` / `total_rounds` | game rounds this segment / cumulatively | grows steadily | flat across segments = the source stalled (see `fetch_errors`) |
| `\|M\|` (`m_relations`) | distinct relation **names** in M after the segment | **bounded ≈ vocabulary size**; plateaus | climbing without bound = decay not biting on names → check `--ttl` |
| `atoms` (`m_atoms`) | sheet **atoms** in M — the honest unit (a hub name holds many atoms) | bounded ≈ `ttl × active-names`; plateaus | climbing while `\|M\|` is flat is *expected under tropism* (warm hubs accrete atoms); climbing past `--max-m-atoms` trips the safety net |
| `dispositions` | histogram of the round outcomes (`new_fact`, `generalization`, `challenge_to_M`, …) | a **mix** appropriate to the source | 100 % one disposition = a source-monoculture finding (note it), not a fault |
| `non_revising` | rounds that changed nothing (a warm re-delivery — the habit holding) | **~20–35 %** with tropism on (P1″ 23.6 %, P1‴ 31.8 %) | ~0 % with tropism on = tropism isn't reaching the warm set; ~100 % = the world isn't moving (all redundant) |
| `decayed` | atoms erased by disuse this segment | 0 early; **> 0 once M saturates** (decay is working) | 0 forever *while atoms climb* = the decay clock isn't advancing → check `--ttl-unit` |
| `legibility` | fraction of P/Q ids resolved to labels (1.00 = all legible) | **≥ ~0.9**, steady | a downward **spike** = silent label degradation (the `mul`-label failure) → stop, check the label fetch |
| `branched` | DAG forks from panel disagreement | 0 on the mechanical panel | non-zero only with the LLM Agonothetes (expected there) |
| `elapsed_s` (per segment) | wall-clock for the segment | **seconds** | tens of seconds and climbing = the round-compute / attest wall at a large persistent M (F2ᵇ/F2⁗); capture a fixture, consider a smaller `ttl` or `--checkpoint-every` |
| `⚠ ckpt_refused` | §3.3 checkpoint attest refusals (skipped + counted) | **0**, or rare | a rising rate = the F1⁵ label-occlusion coin-flip biting on long labels → the root fix is queued; lower label length / investigate |
| `fetch_errors` / `*_dropped` | source hiccups and bounded-growth drops, all **counted never silent** | small, stable | a spike in `fetch_errors` = the source endpoint is down (F1⁷); `frontier_dropped`/`statements_dropped` climbing = caps doing their job (fine) or the frontier starving (check) |
| `unparseable_dropped` | items that failed the membrane parse gate | 0 | non-zero = a new source-payload shape the parser rejects — capture it (F1′ was one) |
| `docket=No/Nr/Na/Nx` | open / resolved / asked / inexpressible wants | `r` and `a` grow; `x` small | `x` (inexpressible) climbing = the Q1 residue is unreachable grips (F2⁶) — a Q2/Q3 signal, not a fault |
| poise `●/○/✕` | engagement/settlement (`poise_from_digests`) | **● engaged / ○ settling** | ✕ = a pole failure: **rigidity** (nothing moves) or **thrash** (no disposition sticks) → read which pole and why |

**The single most important invariant:** `atoms` (and `\|M\|`) must **plateau**, not climb without
bound. A bounded M at steady state is decay working; an unbounded one is the run's one real
failure mode (every other condition above is absorbed and counted). If atoms climb past the
plateau you expect, `touch STOP` and check `--ttl` / `--ttl-unit` before relaunching.

---

## 2. One-page disposal checklist

A run is not *done* until it is **disposed** — turned into evidence in a `RUN_N_LOG.md`. Every
finished run gets this treatment, whether it confirmed the priors or crashed at minute 32.

1. **Stop cleanly.** STOP file or deadline reached. Confirm the driver printed
   `stopped: <reason>` and the final per-segment summary. A crash is fine — note it; the
   supervisor's `crashes survived` count and the resume state are themselves data.
2. **Confirm the floor held.** `resume` state persisted? Checkpoints attested (or refusals
   skipped-and-counted, not silent)? The correspondence floor (P6-series) is a standing prior
   every run re-tests.
3. **Score each pre-registered prior.** For every `Pn` in the run's pre-registration
   (`AUTOMATED_ENDOPOREUTIC_GAME.md` §-whatever + the `RUN_N_LOG.md` skeleton): write
   **expected → observed → meta-disposition** (confirmed / partially confirmed / refuted /
   vacuous). A prior that couldn't be tested (no events of its kind) is **vacuous**, not
   confirmed — say so.
4. **File findings `Fn`, dated and disposed.** Each surprise gets a numbered finding: what
   happened, why, and its disposition — *fixed now* / *queued* (name the next artifact) /
   *noted*. A finding with no disposition is unfinished work, not a finding.
5. **Run the determinism canary.** Replay `polls.jsonl` / `items.jsonl` offline and confirm the
   run reproduces (the recorded-source replay is the canary). A canary that diverges is an F-level
   finding.
6. **Capture fixtures for any wall hit.** If a segment ballooned (attest or round-compute),
   save the offending segment as a fixture (e.g. `run4_seg92`) so the perf work has a
   regression target.
7. **Propagate machinery changes.** If the run motivated a code change, update `CLAUDE.md`
   module bullets, the relevant `docs/` design-of-record, and the auto-memory index. A run that
   changed the rules of the game must leave the rulebook current.
8. **Commit with the log.** One commit carrying `runs/RUN_N_LOG.md` (disposed) + any fixes +
   the `CURRENT_PLAN.md` `▶ NEXT SESSION` update naming what the run teed up. Push (backup).

**Disposal is done when:** every prior is scored, every surprise is a disposed finding, the
canary is green, and `CURRENT_PLAN.md` names the next move. Only then is the run evidence rather
than a loose end.

---

## 3. Where the rest lives

- **Launch / stop / resume flags:** `tools/run_live_wikidata.py --help`.
- **Why the loop is shaped this way** (segment → checkpoint → prune → carry M forward; disuse
  decay; the super-linear-in-\|M\| round cost): `docs/AUTOMATED_ENDOPOREUTIC_GAME.md` §10.
- **The pre-registration discipline** (priors as bets, meta-dispositions): the same doc's
  run-pre-registration sections + each `runs/RUN_N_LOG.md` skeleton.
- **Prior runs as worked examples:** `runs/RUN_1_LOG.md` … `runs/RUN_7_LOG.md`.
