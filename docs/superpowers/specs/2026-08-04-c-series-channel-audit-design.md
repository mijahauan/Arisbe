# The C-series channel audit: were its channels live when its figures were taken?

**Date:** 2026-08-04 · **Status:** design, approved in sitting · **Ruled by:** CURRENT_PLAN
(2026-08-04), *"audit the C-series' channels before building anything else on its figures."*

## 1. The occasion

The D-1 arc found **four channels that ran hundreds of times and did nothing**: challenges
charged but never disposed, `corroborate` minting zero, `settle_credit` never called, and
`answer` structurally dead and then, once revived, dynamically inert. **No economic figure
looked wrong while any of them ran.** The C-series was measured with the same machinery, and
nobody has checked whether its channels were minting when its published numbers were taken.

Two structural echoes are already visible without running anything:

- `_play_challenge` runs **publish before challenge and corroborate**, the same "board
  blanketed first" shape that killed D-1's `answer`.
- The C-series' loudest null — *typification read exactly inert, reproducing fourteen figures
  digit for digit* — has the same signature as D-1's defect (4), where `settle_credit` was
  never called, `Unit.peers` was empty everywhere, and the null had no instrument behind it.

Neither is evidence of a defect. Both are reasons the audit is cheap insurance rather than
speculation.

## 2. What the audit must establish

D-1 exhibited **two** kinds of deadness, and mint-counting alone catches only the first:

| Class | Signature | D-1 instance |
|---|---|---|
| **Dead** | calls > 0, mints == 0 | `answer` before the fix; `corroborate` throughout |
| **Live but inert** | mints > 0, ablation moves nothing | `answer` after the fix — 179 marks, byte-identical results |
| **Live and consequential** | mints > 0, ablation moves published figures | what a channel is supposed to be |

So the audit runs in two passes: **count**, then **ablate**. A mint count alone would have
pronounced D-1's revived `answer` healthy.

## 3. Scope

The C-series has **no driver in `tools/`**. Its published figures come from measurement
harnesses embedded in the test files:

| Harness | File | Channels played |
|---|---|---|
| `_play` | `tests/test_c_channels.py:491` | ask · answer · adopt |
| `_play_challenge` | `tests/test_c_channels.py:1711` | publish · challenge · corroborate · dispose |
| `_play_ask_and_challenge` | `tests/test_c_channels.py:2432` | all eight, incl. `settle_credit` |
| `_arm` | `tests/test_c_speaker_variance.py:41` | `_play_ask_and_challenge` under `liars=` |

`_arm` is a configuration of the third harness rather than a fourth driver, but it carries the
second, independent publication of the typify-inert null — the arm built specifically to give
typification something to sort — so it is audited as its own arm.

Out of scope: `tests/test_c_stage_gates.py`, `test_c_field.py`, `test_c_marks.py`. Those are
single-unit or field-level and play no inter-unit channel, so the probe would have nothing to
count in them.

## 4. The instrument — `tests/c_channel_probe.py`

A helper module, not a test file. It lives in `tests/` because it is an **observer's reading**,
by the same doctrine that keeps `_cost_reading` out of `src/`: putting it in `src/` would hand
a unit a faculty it does not have.

Two context managers over `Unit`, both restoring the originals on exit:

**`channel_calls()`** yields a `ChannelTally` carrying `.calls[name]` and `.effects[name]` for
the eight channel methods — `publish`, `ask`, `answer`, `adopt`, `challenge`, `corroborate`,
`dispose_challenges`, `settle_credit`. Effect is defined per method exactly as
`runs/d1/channel_probe.py` defines it, since that instrument is the one that found the defect:

- list-returning methods (`publish`, `answer`, `challenge`, `corroborate`, `settle_credit`) —
  the number of marks returned;
- `ask` — 1 when a mark went out, 0 on `None`;
- `adopt` — the uptake count it returns;
- `dispose_challenges` — the sum of the five outcome lists on its result.

**`muted(*names)`** **replaces** the named methods with a typed no-op, so the run proceeds with
the channel genuinely absent. Replacement rather than wrapping is what makes it an ablation:
`publish` and `corroborate` mint marks onto the board as a side effect, so a counting wrapper
would leave the channel running.

The harnesses themselves are **not edited**. They are documented as explicit on purpose, and an
audit that alters its subject cannot be read against the published figures.

## 5. The audit run — `runs/c_audit/audit.py`

Imports the harnesses from the test modules — an established pattern here, since
`test_c_speaker_variance.py` already imports `_play_ask_and_challenge` from
`test_c_channels.py` — and for each published arm at that arm's own seeds:

1. **Count.** Replay under `channel_calls()`; print calls and effects per channel per arm.
2. **Ablate.** For each channel that made calls, replay under `muted(channel)` and diff the
   arm's own returned figures — `_play_ask_and_challenge`'s `tally` dict, `_play_challenge`'s
   `(raised, events, tally)`, `_play`'s `(answers, uptakes)` plus each unit's ledger.
3. **Classify** each channel in each arm as dead / live-but-inert / live-and-consequential.

Output: `runs/c_audit/CALLS.txt`, `runs/c_audit/ABLATION.txt`, and a written
`runs/RUN_C_AUDIT_LOG.md` read against §7's priors. No figure is invented: everything reported
is either a call count, a mint count, or a diff of a number the harness already returns.

## 6. The standing discipline

Each measurement gate wraps its plays in `channel_calls()` and asserts that **every channel it
plays minted at least once**, naming the channel and the arm on failure. This generalizes the
assertion `_play`'s gate already carries (`answers > 0 and uptakes > 0`) to all four arms.

A channel that is *meant* to be silent in an arm — a mute control, or corroboration in a
community below its witness threshold — goes in that assertion's **explicit per-arm
allowlist**. A predicted zero and a defect must not read alike; writing the prediction down is
what makes them distinguishable.

The assertion is demonstrated to bite: mute a channel, watch the gate fail, restore.

While reading the harnesses I will also name, in the log, any **docstring that asserts a
liveness property instead of checking it**. That is the defect shape that let D-1's dead channel
survive four fix rounds, and this file's `_play` gate shows the C-series already knows the
remedy in one place out of four.

## 7. Pre-registered priors

Committed **before the probe runs**, each with its failure condition stated.

- **`P-A1` — typify is called and mints, and the null survives it.** `settle_credit` runs in
  phase (i) of every ask arm, so calls > 0; I expect effects > 0 as well, and ablation to move
  the *typified* arm's preference figures (`preferences`, `occ_pref`, `score_*`) while leaving
  the untargeted control's outcome figures alone. **Fails if `settle_credit` effects == 0** —
  in which case the C-series' typification null is D-1's defect (4) repeated and every
  typification finding, in both files, is void.
- **`P-A2` — corroboration's zero is a threshold, not a defect.** `corroborate` mints > 0 in
  the six-unit `PAIRS` witness arms (published: 45 firings) and **exactly 0** in four-unit
  `CYCLIC` arms, where the three-witnesses-per-domain bar cannot be met. **Fails if it mints
  zero at six units** (the published firings unreproducible) **or nonzero where the bar cannot
  be met** (the bar not doing what it is said to do).
- **`P-A3` — the answer channel is live in the combined arm.** `answer` mints > 0 in both
  ask-bearing harnesses. Unlike D-1's driver, `_play_ask_and_challenge` runs answer at phase (d)
  **before** publish at (e), which is the order D-1 identified as the one where the channel is
  not redundant. **Fails if it mints zero there** — the silence-window, typification and both
  stage-3 gate figures would then have been measured on a mute channel.
- **`P-A4` — ablating `answer` under `ask=True` reproduces the `ask=False` arm.** The published
  repair figures (true-law refutations 640 → 349, converse 321 → 20) are the difference between
  those two arms, so muting `answer` should move the `ask=True` figures back toward the
  published mute figures. **Fails if muting `answer` leaves them unmoved** — the published
  repair would then be produced by something other than testimony.
- **`P-A5` — ablating `settle_credit` leaves the control's fourteen figures unmoved**,
  reproducing the published "digit for digit" null from the other side. **Fails if the control's
  figures move** — the claim that the untargeted arm reproduces Tasks 5e/5f exactly would be
  wrong.
- **`P-A6` — the audit finds something.** At least one channel in at least one published arm
  makes ≥ 1 call and mints 0. **Fails if every channel mints wherever it is played** — in which
  case the C-series' channels were live when its numbers were taken and **its figures stand as
  published**, which is a result worth having and is why the probe runs before anything is built
  on them.

`publish`, `ask`, `adopt`, `challenge` and `dispose_challenges` carry no individual prior. They
are counted anyway, and any zero among them is a finding.

## 8. Success criteria

1. Calls-and-mints table produced for all four arms, at each arm's own seeds.
2. Every channel in every arm classified dead / live-but-inert / live-and-consequential.
3. Standing assertion in place in all four gates, with per-arm allowlists, **demonstrated to
   fail** when a channel is muted.
4. The C-series suite passes.
5. `runs/RUN_C_AUDIT_LOG.md` written and read against §7 — each prior held, refuted, or not
   reached, in its own words.
6. Any figure the audit invalidates is corrected where it is published (test docstrings first),
   or flagged in place as unaudited when the repair is out of scope by §9.

## 9. Scope boundary on repairs

**Test-side repairs are in scope**: a phase order, an uncalled method, a missing allowlist. Fix
it, re-run the affected arms, and rewrite the figures it moves — D-1's precedent.

**`src/` is not touched.** If the defect lives in `c_unit.py` — `corroborate`'s
once-per-law-ever gate is the standing candidate — it is named, the findings it taints are
flagged, and it gets its own sitting. A change to `c_unit.py` alters the C-series' subject
matter, not merely its measurement, and cannot be smuggled in as an audit.

## 10. Named limits

- **Muting is not quite deleting a call.** A muted method still costs a call. Nothing in the
  C-series prices acts (D-1 does), so no C-series figure reads call counts and the substitution
  is exact for these arms — but it would not be for a priced world.
- **The audit certifies only figures whose arms are still in the tree.** A number published from
  a harness since changed cannot be re-derived, and is reported as such rather than assumed.
- **A live channel is not a *correct* channel.** This audit asks whether a channel fired and
  whether its firing moved anything. Whether what it minted was the right thing is the
  C-series' own subject, and is not re-opened here.

## 11. Cost

The C-series suite runs ~912 s. Baseline plus one ablation per firing channel across four arms
is roughly 15–40 minutes of compute. Nothing in `src/` is modified.
