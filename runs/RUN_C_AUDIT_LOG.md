# RUN_C_AUDIT — were the C-series' channels live when its figures were taken? (run log)

> **Spec:** [the C-series channel audit](../docs/superpowers/specs/2026-08-04-c-series-channel-audit-design.md)
> — priors `P-A1`…`P-A6` in its §7, **committed at `9209e2d` before the probe was written**;
> the scope boundary on repairs in its §9; the named limits in its §10.
> **Instrument:** `tests/c_channel_probe.py` (`channel_calls()` counts calls against mints,
> `muted()` replaces a method with a typed no-op so the run proceeds with the channel genuinely
> absent). **Driver:** `runs/c_audit/audit.py`, 23 arms at each arm's own seeds.
> **Record:** `runs/c_audit/CALLS.txt` (count pass) · `runs/c_audit/ABLATION.txt` (ablation pass).
> Nothing under `src/` was modified. Neither harness was edited. Every number below is a call
> count, a mint count, or a diff of a figure the harness already returns.

## The result, in one paragraph

**`Unit.corroborate` is dead in every one of the twenty arms that play it.** 1920 to 2880 calls
per arm, **zero mints, everywhere** — including the six-unit community whose published table
reports 45 corroborations. It is not empirically silent, it is **structurally preempted**: both
harnesses run `publish` and `challenge` before `corroborate` in the same round, and
`corroborate` mints only through keys those two have already spent. The published figure of 45
is nevertheless **correct**, because it never came from that method: `dispose_challenges`
computes it by counting distinct foreign authors of *challenge* marks. So `P-A2` is refuted
more sharply than its failure condition anticipated — corroboration mints zero at six units
*and* at four — while the finding it was checking survives with its number intact and its
causal story wrong. The second finding is `answer`: it mints 668 marks in K1 and moves **not
one of that arm's 43 figures**, and the same in all eleven full-community arms. `P-A4` is
refuted with it — muting `answer` leaves K1 byte-identical to its own baseline, while muting
`adopt` reproduces K2 exactly (net −433, uptakes 0, bets 455). The published repair effect is
`ask` + `adopt`; `answer` is a redundant re-mint of what `publish` emits a few lines later in
the same round. **`P-A1`, `P-A5` and `P-A6` hold; `P-A3` holds literally and is hollowed out by
`P-A4`.** And the audit's baseline pass re-derived every published figure it touched — C1's
`(60, 6, 0, 46, 4)`, C5's 45, K1's −185/1258/1151, K2's −433/455 — **so no published C-series
number is falsified by a channel defect.** What the two dead channels cost is attribution, in
three docstrings. One published table *is* wrong (§6), for an unrelated reason: docstring drift
after the window ruling, which the audit found while re-deriving and which no channel touches.

## What was audited

23 arms, at each arm's own seeds, over the four measurement harnesses the C-series publishes
from. There is no driver in `tools/`; the figures come from the test files.

| harness | file | arms | channels played |
|---|---|---|---|
| `_play` | `tests/test_c_channels.py:491` | P1, P2 | ask · answer · adopt |
| `_play_challenge` | `tests/test_c_channels.py:1711` | C1–C8 | publish · challenge · corroborate · dispose |
| `_play_ask_and_challenge` | `tests/test_c_channels.py:2432` | K1–K10 | all eight, incl. `settle_credit` |
| `_arm` (`_play_ask_and_challenge` under `liars=`) | `tests/test_c_speaker_variance.py:41` | L1–L3 | all eight |

Two passes, in order: **count** (23 arms, ~15 min), then **ablate** — for each channel that
minted in an arm, replay the arm with that method replaced by a no-op and diff the arm's own
returned figures (~45 min, run one arm per invocation after the ten-minute foreground cap
forced it). K3 (`ask=False, mute=True`) makes **zero calls on every channel** and so has no
rows: it is the fully silenced control, and it reads exactly as its name says.

## The classification table

**dead** = calls > 0, mints 0 · **live but inert** = mints > 0, ablation moves nothing ·
**live and consequential** = ablation moves the arm's own figures. Mints are aggregated over
the arm's own seeds. Largest movers are quoted from `ABLATION.txt`, which shows the eight
largest of however many moved.

### The two `_play` arms

| arm | channel | calls | mints | verdict | largest movers |
|---|---|---|---|---|---|
| P1 | ask | 1680 | 444 | **consequential** (5/6) | answers 410→0, uptakes 406→0, misses 35→423 |
| P1 | answer | 1680 | 410 | **consequential** (5/6) | answers 410→0, uptakes 406→0, misses 35→423 |
| P1 | adopt | 406 | 406 | **consequential** (4/6) | uptakes 406→0, misses 35→423, abstentions 4984→4786 |
| P2 | ask | 1120 | 696 | **consequential** (1/6) | answers 189→0 |
| P2 | answer | 1120 | 328 | **consequential** (1/6) | answers 189→0 |
| P2 | adopt | 323 | **0** | **dead — and predicted** | (never reached the ablation pass) |

P1 is the one arm in the whole inventory where `answer` does real work, and the reason is
structural: `_play` **never calls `publish`**, so `answer` is the only route from a unit's facts
to the board. P2's dead `adopt` is not a defect — its own gate asserts `uptakes == 0` and gives
the reason in the same breath ("a shared domain delivers identically to both units, so every
answer arrives after the asker met the atom itself"). That is the spec §6 allowlist discipline
already in place, in the one gate that has it.

**Seed caveat on P2.** The count pass ran P2 over the full 14-seed `SEEDS`; the ablation pass
ran it over `SEEDS[:8]`, which is what the published call site (`:698`) actually uses. P2's
mint counts above are therefore a **six-seed-wider superset** of the published arm, and its
ablation figures are the published arm. `adopt`'s zero holds at both widths.

### The eight challenge arms

Every one of the eight reads the same shape. `publish`, `challenge` and `dispose_challenges`
each move 5–10 of the arm's 11 figures; `corroborate` mints nothing.

| arm | publish | challenge | corroborate | dispose | verdict |
|---|---|---|---|---|---|
| C1 | 5834 | 60 | **0** | 116 | three consequential, **corroborate dead** |
| C2 | 5866 | 92 | **0** | 179 | ″ |
| C3 | 4092 | 96 | **0** | 132 | ″ |
| C4 | 4098 | 88 | **0** | 160 | ″ |
| C5 | 6136 | 160 | **0** | 288 | ″ |
| C6 | 6136 | 160 | **0** | 288 | ″ |
| C7 | 8749 | 90 | **0** | 180 | ″ |
| C8 | 8749 | 90 | **0** | 174 | ″ |

Calls on `corroborate`: 1920 in C1–C4, 2880 in C5–C8. Representative movers, C5:
`-publish` → marks 6850→0, disp_asked 410→0, raised 160→0, **disp_corroborated 45→0**;
`-challenge` → the same eight figures, marks 6850→6136; `-dispose_challenges` → seven of them.
The 45 corroborations survive `corroborate`'s absence entirely, because they never depended on it.

### The thirteen full-community arms

| arm | publish | ask | answer | adopt | challenge | corrob. | dispose | settle_credit |
|---|---|---|---|---|---|---|---|---|
| K1 | 4144 ● | 1173 ● | 668 ○ | 1151 ● | 96 ● | **0 ✗** | 132 ● | 1049 ◐ |
| K2 | 4092 ● | — | — | — | 96 ● | **0 ✗** | 132 ● | — |
| K3 | *no calls on any channel* | | | | | | | |
| K4 | 4144 ● | 1173 ● | 668 ○ | 1151 ● | 96 ● | **0 ✗** | 132 ● | 1049 ● |
| K5 | 3674 ● | 1173 ● | 668 ○ | 466 ● | 96 ● | **0 ✗** | 132 ● | 466 ● |
| K6 | 6330 ● | 1205 ● | 535 ○ | 1213 ● | 160 ● | **0 ✗** | 288 ● | 1116 ◐ |
| K7 | 6330 ● | 1205 ● | 535 ○ | 1213 ● | 160 ● | **0 ✗** | 288 ● | 1116 ● |
| K8 | 4323 ● | 557 ● | 117 ○ | 563 ● | 96 ● | **0 ✗** | 132 ● | 518 ◐ |
| K9 | 4144 ● | 1173 ● | 668 ○ | 1151 ● | 96 ● | **0 ✗** | 132 ● | 1049 ◐ |
| K10 | 6330 ● | 1205 ● | 535 ○ | 1213 ● | 160 ● | **0 ✗** | 288 ● | 1116 ◐ |
| L1 | 4523 ● | 1006 ● | 565 ○ | 978 ● | 96 ● | **0 ✗** | 144 ● | 907 ◐ |
| L2 | 4523 ● | 1006 ● | 565 ○ | 978 ● | 96 ● | **0 ✗** | 144 ● | 907 ● |
| L3 | 5617 ● | 446 ● | 369 ○ | 569 ● | 96 ● | **0 ✗** | 176 ● | 557 ● |

● live and consequential · ○ **live but inert** · ✗ **dead** · ◐ live, but only its own
credit ledger moves — no decision figure does.

Movers, K1, in the order `ABLATION.txt` reports them:

```
-publish   moved 21/43: questions 1258->1483, adopted_licensed 697->907, uptakes 1151->1348,
                        bets 193->358, true_ref 220->60, repairable 170->10, net -185->-340
-ask       moved 23/43: questions 1258->206, uptakes 1151->187, bets 193->968, net -185->-914
-answer    INERT: not one figure moved
-adopt     moved 23/43: uptakes 1151->0, adopted_licensed 697->0, failed 618->0,
                        proved 431->0, true_ref 220->640, repairable 170->590
-settle_credit moved 5/43: pending 102->1151, failed 618->0, proved 431->0, score_neg 94->0
```

The ◐ / ● split on `settle_credit` is the honest one. In the six ◐ arms (`typify=None`: K1, K6,
K8, K9, K10, L1) every figure that moves is `settle_credit`'s **own output** — `proved`/`failed`/`pending` census
`u._credited`, `score_*` iterate `u.peers`, and only `settle_credit` writes either. Removing the
function that produces a number necessarily changes that number. Every figure that would show
something *acting on* the credit — net, bets, misses, hits, uptakes, questions,
adopted_licensed, adopted_body, true_ref, repairable — is unchanged. In the five ● arms
(`typify` set) a behavioural figure moves too: `occ_pref` 53→0 (K4, L2), 72→0 plus
`pref_choice` 25→0 (K7), 76→0 (L3), and K5 (`typify="distrust"`) moves **18/43** with
net −745→−185 and uptakes 466→1151. The scale runs exactly with how much of `peers` the setting
reads.

## The priors, each in its own words

### `P-A1` — *"typify is called and mints, and the null survives it."* — **HELD**

> Fails if `settle_credit` effects == 0 — in which case the C-series' typification null is
> D-1's defect (4) repeated and every typification finding, in both files, is void.

`settle_credit` mints **1049 in K1 and K4**, **1116 in K6 and K7**, 466 in K5, 518 in K8, 907 in
L1/L2, 557 in L3. Effects are not zero anywhere it is played. The prior's second clause holds
too: ablation moves the *typified* arm's preference figure (`occ_pref` 53→0 in K4, 72→0 in K7)
and leaves the untargeted control's outcome figures alone. **The C-series' typification null is
not D-1's defect (4).** The mechanism ran, decided 53 and 72 uptakes, and changed nothing — which
is a real null, and the most reassuring result in this audit.

### `P-A2` — *"corroboration's zero is a threshold, not a defect."* — **REFUTED**

> Fails if it mints zero at six units (the published firings unreproducible) or nonzero where
> the bar cannot be met (the bar not doing what it is said to do).

It mints zero at six units. It also mints zero at four. It mints zero in **all twenty arms that
call it**, on 1920–2880 calls each. The failure condition fires, and it fires wider than it was
written: the prior imagined a defect confined to the six-unit arms, and what the probe found is
a method that has never minted a mark in any published C-series measurement.

The preemption is exact, and it is in two places:

- `Unit.corroborate`'s **counterexample branch** mints through `_mint_challenge`
  (`src/c_unit.py:1488–1506`), keyed `(CHALLENGE, law)` in `self._published`. `Unit.challenge`
  mints through the same key, and both harnesses run `challenge` **before** `corroborate` in the
  same round (`_play_challenge` phases (c) then (d); `_play_ask_and_challenge` phases (f) then
  (g)). `challenge` scans the board for every foreign LAW mark it can counterexample, so any law
  a call could name has already been offered to `_mint_challenge` that round. The key is always
  spent.
- Its **head branch** mints keyed `(FACT, head)`, which `Unit.publish` — phase (b) and phase (e)
  respectively — has already spent for every fact the unit holds.

**What carries this finding is `CALLS.txt`: `corroborate` mints 0 on 1920–2880 calls, in twenty
arms.** That figure is in the artefact, twenty times over, and the two-branch reading above is
verifiable from the source alone. A third piece of evidence is *corroborative only and is not in
either artefact*: an instrumented rerun of C3 during the count pass counted `_mint_challenge`
9 399 calls inside the corroborate phase, returning non-`None` zero times. It has not been
independently reproduced, and nothing above depends on it.

The published "CORROB" column comes from a different mechanism entirely: `dispose_challenges`
counting **distinct foreign authors** of challenge marks against one law — the ruling stated at
`src/c_unit.py:1764` ("WHAT IS COUNTED IS DISTINCT FOREIGN AUTHORS") and implemented at
`:1807–1818` — read as `tally["corroborated"]` in `_witness_arm`.

### `P-A3` — *"the answer channel is live in the combined arm."* — **HELD, and hollow**

> Fails if it mints zero there — the silence-window, typification and both stage-3 gate figures
> would then have been measured on a mute channel.

`answer` mints **410 in P1** and **668 in K1**, and in all eleven ask-bearing full-community
arms. It does not mint zero, so the prior holds on its terms and its named consequence does not
follow. But it must be read beside `P-A4`, which shows the 668 marks buy nothing: the prior was
written on the reasoning that `_play_ask_and_challenge` runs answer at phase (d) **before**
publish at (e), "which is the order D-1 identified as the one where the channel is not
redundant." That reasoning is wrong. The order does not rescue it, because the redundancy is not
about which phase mints first — it is about `(FACT, content)` being one key per unit and
`answer_to` matching author-blind and round-blind. Whichever of the two methods mints, the same
content from the same author is on the board before the next round's adopt phase reads it.

### `P-A4` — *"ablating `answer` under `ask=True` reproduces the `ask=False` arm."* — **REFUTED**

> Fails if muting `answer` leaves them unmoved — the published repair would then be produced by
> something other than testimony.

Muting `answer` leaves them unmoved. K1 base and K1 with `answer` muted are **byte-identical
across all 43 figures**: net −185, misses 189, hits 4, bets 193, uptakes 1151, questions 1258 in
both. K2, the arm K1 was supposed to be moved toward, reads net −433, uptakes 0, bets 455. K1
moved zero distance on every axis.

**What produces the effect is `adopt`.** Muting `adopt` on K1 gives net −433, uptakes 0, bets 455
— an exact match to K2's own run. **Provenance:** `net` and `bets` fall outside the eight-mover
truncation on that `ABLATION.txt` line (23 figures moved, 8 shown), so they are not readable from
the artefact; they were recomputed from the full base/ablated dicts during the ablation pass and
independently recomputed in review, agreeing both times. `uptakes 1151→0` is on the line itself.
(`questions` differs, 726 against K2's 0, only because muting
`adopt` leaves `ask` running: units still ask, they just never take a reply up.) Muting `ask`
overshoots past K2 (net −185→−914), because it also removes the questions peers would have
answered. The published K1/K2 repair — true-law refutations 640 → 220, converses 321 → 21, net
−433 → −185 — is real, and it is carried by **`ask` + `adopt`**, the targeted question-and-uptake
machinery. The `answer` method is a redundant re-mint of what `publish` emits in the same round.

### `P-A5` — *"ablating `settle_credit` leaves the control's fourteen figures unmoved."* — **HELD**

> Fails if the control's figures move — the claim that the untargeted arm reproduces Tasks 5e/5f
> exactly would be wrong.

**The prior names fourteen figures, and they are a specific fourteen.** They are `_ASK_KEYS`
(`tests/test_c_channels.py:2976`), the set the digit-for-digit null at `:3044` is asserted over:
true_ref, conv_ref, true_lost, conv_lost, repairable, unrepairable, questions, uptakes, net,
suspended, internal, corroborated, rebutted, silence. **None of the fourteen moves.** The failure
condition does not fire. Held.

What does move in K1 is five figures — pending 102→1151, failed 618→0, proved 431→0, score_neg
94→0, score_zero 2→0 — and **not one of them is in the fourteen**. All five are `settle_credit`'s
own bookkeeping: `self.peers` is written **only** in `Unit.credit`, which is called **only** from
`settle_credit`, so a figure computed by iterating `peers` cannot survive the function that fills
it. They appear here only because the audit's own `figures()` reduces the whole 43-key tally
rather than the gate's fourteen; that is instrument granularity, not a moved control.

An earlier draft of this log graded the prior "refuted literally" on those five. That was wrong,
and wrong in the shape this audit exists to catch — an agreement asserted against a set nobody
checked membership in, here in the refuting direction. The substantive claim stands as it did:
the untargeted control's choices do not consult `peers`, and K4 moves `occ_pref` 53→0 exactly as
predicted.

### `P-A6` — *"the audit finds something."* — **HELD**

> Fails if every channel mints wherever it is played — in which case the C-series' channels were
> live when its numbers were taken and its figures stand as published.

It found two, in two different classes: a dead channel in twenty arms and an inert one in eleven.
The failure condition did not fire, so the C-series' figures do **not** stand unexamined — but
see the next section, because the two findings turn out to be about *attribution* rather than
about the numbers.

`publish`, `ask`, `adopt`, `challenge` and `dispose_challenges` carried no prior. All five mint
and all five are consequential in every arm that plays them, which is a finding in the direction
nobody has to act on.

## Which published findings this touches

The distinction this section keeps is the one the brief insisted on: **a published number that is
wrong** and **a published number that is right whose causal attribution is wrong** are two
different findings, and only one of them requires re-measurement.

### 1. `test_corroboration_fires_once_a_domain_has_three_witnesses` — **the number survives, the mechanism it is named after never ran**

The table is the whole gate:

> ```
> arm                witnesses  raised  susp  CORROB  window  true lost
> 4 units cyclic     2 2 2 2        96    66       0      66      64/64
> 4 units PAIRS      3 2 2 1        88    80       4      76      56/64
> 6 units pairs      3 3 3 3       160   144      45      99      96/96
> 6 units pairs w=3  3 3 3 3       160   144       0     144      96/96
> ```
> **THE FIRST CLAUSE HOLDS: 45 corroborations at six units against 0 at four under the cyclic
> scheme, which is what the whole task was built to produce.**

**Four of the table's six columns are reproduced by the audit's baseline pass**, each arm against
its own row — raised / susp / CORROB / window: C3 (96, 66, **0**, 66), C4 (88, 80, **4**, 76),
C5 (160, 144, **45**, 99), C6 (160, 144, **0**, 144), read from `raised`, `disp_suspended`,
`disp_corroborated` and `disp_internal`. **The other two columns the audit did not compute.**
`witnesses` is a property of the aperture layout, and `true lost` comes from `_witness_arm`'s own
`true_defeats`/`true_held` (`tests/test_c_channels.py:2231–2236`), neither of which is among the
eleven keys `figures()` returns for `_play_challenge` (`runs/c_audit/audit.py:137–144`) — so
64/64, 56/64 and 96/96 stand on the gate's own assertions and are not re-derived here. The
number 45 is right, and the finding it supports (`P-F2`: corroboration goes 0 → 4 → 45 while
true laws held goes 0 → 8 → 0) is right on its corroboration half and untouched by this audit on
its true-laws half.

What is wrong is what the series says 45 *is*. The lifecycle comment in `src/c_unit.py:1521`
describes the external arm as:

> (external) The author cannot rebut the cited individual from its own record, so it publishes a
> call for corroboration and **the community answers from its own records**.

and `Unit.corroborate`'s own docstring opens:

> THE OTHER HALF OF THE CALL, exactly as `answer` is the other half of `ask`.

**In no published C-series sweep was a call for corroboration ever answered.** 66 calls at C3,
80 at C4 and 144 at C5 (the gates' own asserted figures — `board.corroboration_calls()` is not in
the audit's figure set and was not re-derived), and `Unit.corroborate` — their only reader
anywhere in `src/` or in either harness — returned an empty list every one of the 1920–2880 times
it was invoked. That last number *is* the audit's, and it is the one the finding rests on. The
units the tally counts as corroborators had published their counterexamples in phase (c), before
the call existed, and would have published them identically had no call ever been minted.

So the finding survives read as **"a law is eliminated once two distinct foreign records have
independently published a counterexample to it"** — which is what `dispose_challenges` actually
implements and what its own docstring at `c_unit.py:1764` states correctly. It does **not**
survive read as *soliciting and receiving* corroboration. In particular the stage-3 summary
recorded in the project's memory —

> corroboration *eliminates* whatever it is **asked about** (45 firings, 96/96 true laws lost)

— keeps its numbers and loses two words. Nothing was asked-and-answered. "Whatever two records
independently dispute" is the correct phrase, and the difference matters, because the wrong one
implies an inquiry the community never conducted.

The same reading applies unchanged to `test_on_the_induce_arm_corroboration_buys_churn` (C7's 24
and C8's 0, both reproduced) and to `test_the_corroborating_bar_is_the_author_s_to_set`'s sweep
claim that `witnesses=3` reads 0 of 144 (reproduced at C6).

One sentence is contradicted outright. `test_under_bounded_attention_the_discrimination_still_inverts_and_now_internally`:

> Now **all 66 doubts are suspended, all 66 calls are published, 159 questions go out**, every
> doubt runs its full five-round window — and all 66 end in retraction anyway, because nothing
> arrives to repair the record. **The apparatus is no longer dead code.** It is a channel with
> nothing coming down it.

The first half is right: the audit reproduces C3's 96 raised and 66 suspended, and the 66 calls
are the gate's own assertion (`tests/test_c_channels.py:2199`), which the audit does not compute
either way. The bolded claim is false: the apparatus **is** dead code, and it stayed dead when
the community grew
to six units and corroboration started "firing". The gate attributes the silence to the cyclic
scheme's two-disputant ceiling, which is a correct explanation of why *eliminations* are zero
there and not an explanation of why *the method* is zero everywhere.

### 2. The `corroborate` unit tests (`:1185`–`:1360`) — sound, and they do not discriminate the method they name

They pass, and they pass because they construct a state the sweeps structurally cannot reach.
In `test_a_peer_answers_the_call_with_its_own_counterexample`,
`test_a_peer_answers_the_call_by_publishing_the_disputed_individual_with_the_head` and
`test_independent_corroboration_eliminates_the_law`, the corroborating unit `u2` is hand-built:
it has never called `publish` on the head and never called `challenge` on the law, so both keys
`corroborate` needs are free. In every sweep every unit calls both, in every round, before
`corroborate` runs.

`test_independent_corroboration_eliminates_the_law` goes one step further and is worth naming:
its `u2.corroborate(board, 3)` mints the identical mark that `u2.challenge(board, 3)` would mint,
through the identical `_mint_challenge` call. The test would pass unchanged with the method
swapped. It is a correct test of the corroboration **rule**; it is not, and was never, evidence
that the corroboration **channel** runs.

### 3. The ask-channel claim — **survives outright, numbers and attribution both**

`test_asking_and_answering_beats_being_mute_at_equal_run_length`:

> Live wins at 14 of 14 seeds and at all 28 individual arms; pair totals −33 against −412, so the
> channel recovers 92% of what bounded attention costs. **About 31 questions go out per run and
> about 29 are answered and taken up.**

Measured: ask 444 mints / 14 seeds = **31.7 questions per run**; answer 410 / 14 = **29.3
answered**; adopt 406 / 14 = **29.0 taken up**. And in this arm `answer` is genuinely
load-bearing — `_play` never calls `publish`, so muting `answer` takes uptakes 406→0 and misses
35→423, which is the mute arm. This is the one place in the C-series where the `answer` method
carries the finding attributed to it, and it survives without qualification.

### 4. The typification findings — **survive, and the audit strengthens them**

`test_typified_asking_changes_nothing_and_the_reason_is_that_nobody_had_a_choice` and
`test_typification_is_still_exactly_inert_with_speakers_to_sort` are measured on arms where
`answer` is inert. That does **not** taint them, and the reason is precise: muting `answer`
leaves the arm byte-identical, which means `publish` mints the same content, in the same round,
from the same author. The testimony the typify arms sort is unchanged; only which method minted
it differs. The null is a null about typification, not an artefact of a dead channel.

The stated *reason* for the null is also correct as written, and it names the right mechanism:

> One peer is the perpetual answerer, so `many_suppliers` is 0 for a reason about **publication
> order** rather than about what anybody could have said.

That is `MarkBoard.answer_to` returning the first-published mark, and it is exactly what the
ablation shows. And `P-A1` supplies what the finding previously lacked: `settle_credit` mints
1049/1116, `occ_pref` reads 53/72 and collapses to 0 when it is muted — so the preference
machinery genuinely ran and genuinely decided uptakes before deciding nothing.

### 5. The liar findings — **numbers survive, the causal sentence is wrong**

`test_a_liar_cannot_volunteer_a_lie_because_the_channel_only_answers`:

> THE REASON IS THE CHANNEL'S SHAPE, not the ledger's weakness. **`Unit.answer` answers open
> questions from its own facts**, and a question names an atom the asker's own record already
> licenses — so an answer either carries THAT atom or is not an answer. A fabricated atom is one
> nobody asked about, and **there is no move in this channel by which a unit volunteers
> something.**

`adopted_fabricated` is one of the 43 figures, and it does not move when `answer` is muted in
L1/L2/L3 — so the finding (0 fabricated adoptions with one unreliable speaker, >10 with four)
stands. Both bolded clauses are wrong about the mechanism:

- `Unit.answer` filters nothing that `publish` does not also emit, in the same round, from the
  same author. Ablating it changes no figure in any liar arm.
- There **is** a move by which a unit volunteers something: `publish`, phase (e), which puts
  every held fact — every fabrication included — on the board unprompted, 4523 marks a run in
  L1.

What actually blocks the lie is at the **asker's** end, not the speaker's: the harness adopts
only `board.answer_to(q)` for a question `q` that unit itself asked, and `answer_to` matches on
content, so a fabricated atom nobody asked about is never taken up. The gate's title — "the
channel only answers" — is right about the channel and names the wrong method. Importantly this
does not weaken the file's conclusion in
`test_the_binding_constraint_is_the_question_not_the_field`: "an answer must carry the atom the
question named" is a property of `answer_to`, which is live and consequential, so the
pre-registered slot-question claim stands as written.

### 6. One published table **is** wrong, and not for a channel reason

`test_typification_is_still_exactly_inert_with_speakers_to_sort` narrates:

> ```
> no liar             true_lost 36  conv_lost  0  uptakes 939  fab  0
> u1 unreliable       true_lost 45  conv_lost  2  uptakes 798  fab  0
> all four unreliable true_lost 58  conv_lost 21  uptakes 474  fab 23
> ```

The audit's baseline pass reads **uptakes 1151 / 978 / 569** on those three arms (K1, L1/L2, L3
in `ABLATION.txt`). Those are window-5 figures narrated under the window-8 default ruled
2026-07-31 — the same drift the neighbouring gates' "0 fabricated adoptions of **798** uptakes"
and "23 of **474** uptakes" carry. The tests still pass, because every clause they assert is an
inequality (`> 500`, `> 10`), a zero, or a cross-arm equality; not one of the narrated counts is
checked. `test_under_bounded_attention_...`'s "**159 questions go out**" is stale the same way —
the audit counts 248 inquiry questions on that arm (C3, `dispose asked`). Test-side, in scope by
§9, not repaired here.

**The drift reached this audit's own spec, which is the clearest evidence of how far it runs.**
`P-A4` as pre-registered reads *"the published repair figures (true-law refutations 640 → 349,
converse 321 → 20)"*. The gate it cites asserts **640 → 220** and **321 → 21**; 349 and 20 are
its window-5 column. The prior was written against numbers the tree had already moved past — the
same drift, from the same ruling, propagating into a document written to catch exactly this. It
changes nothing about `P-A4`'s verdict, which turns on whether ablating `answer` moves K1 at all,
and it is recorded rather than corrected: **the priors are pre-registered and stand as written.**

## Unchecked liveness claims

The scan the spec asked for, run over both files. D-1's lesson is that a docstring asserting a
property instead of checking it is how a defect survives four fix rounds; this is the list of
where that shape is present.

**Gates that CHECK — the pattern the others should follow**

| gate | the clause |
|---|---|
| `test_the_liar_really_does_mis_observe` (`variance:51`) | a whole test whose only job is the check: *"THE MECHANISM-IS-EXERCISED GATE… A finding of 'no effect' from a mechanism that never ran is worth nothing at all"* |
| `test_asking_and_answering_beats_being_mute_at_equal_run_length` (`:541`) | `assert answers > 0 and uptakes > 0, "the channel carried nothing, so nothing was tested"` |
| `test_with_full_attention_the_ask_channel_is_inert_rather_than_harmful` (`:669`) | `assert answers > 0` **plus** the predicted zero written down: `assert uptakes == 0` with its reason |
| `test_suspension_saves_the_true_laws…` (`:1893`) | `assert raised > 0 and tally["suspended"] > 0` under the comment *"THE GUARD IS THAT THE CHANNEL RAN, not that a law died"* |
| `test_under_bounded_attention…` (`:2116`) | `assert raised > 0` per seed |
| `test_peer_testimony_repairs…` (`:2762`) | `assert agg["questions"] > 0 and agg["uptakes"] > 0` |
| `test_typified_asking_changes_nothing…` (`:3044`) | questions/uptakes pinned *"so inertness is a result rather than a measurement that never ran"*, plus `occ_pref == 53` — the preference machinery's behavioural fingerprint |
| `test_no_fabricated_fact_is_ever_adopted…` (`:3160`) | `assert arm["adopted_licensed"] > 0` |
| `test_a_liar_cannot_volunteer_a_lie…` (`variance:74`) | `assert hi["uptakes"] > 500, "the channel must be carrying something"` |
| `test_gate_two…` (`:3577`) | `sum(consult.values()) == uptakes == 1151` |
| `test_the_channel_leaves_anticipate_before_observe_alone` (`:717`, `:3768`) | `assert answers > 0 and uptakes > 0` / `assert raised > 0 and events` + `tally["suspended"] > 0` |

**Gates that ASSERT without checking — Task 6's targets**

| gate | what it asserts in prose and never checks |
|---|---|
| **`test_corroboration_fires_once_a_domain_has_three_witnesses` (`:2243`)** | the entire corroboration lifecycle — a call published, the community answering it. Asserts only `tally["corroborated"]`, which `dispose_challenges` computes from challenge marks. **No clause anywhere requires `Unit.corroborate` to have minted, and it never does.** The strongest instance in either file. |
| `test_on_the_induce_arm_corroboration_buys_churn` (`:2323`) | the same, on the induce arm |
| `test_typification_is_still_exactly_inert_with_speakers_to_sort` (`variance:123`) | *"Preferences are earned (1, 3 and 5 of them) and never once disagree"* — `occ_bite == 0` is checked; `preferences > 0` is not, so an inertness verdict rests on an unchecked non-zero. Its whole narrated table is also stale (§6 above). |
| `test_the_binding_constraint_is_the_question_not_the_field` (`variance:163`) | asserts a pair of zeros as the baseline a future claim will be read against, with no clause that anything ran. **A fully mute arm passes it.** |
| `test_a_lie_enters_by_being_asked_about_not_by_being_told` (`variance:100`) | `> 10` is a liveness check of a sort; the "of 474 uptakes" denominator is narrated, unasserted, and wrong |
| `test_the_corroborating_bar_is_the_author_s_to_set` (`:1359`) | narrates a sweep figure ("0 corroborations of 144 doubts") the test itself does not run |

**Named separately, because it has no explicit clause and does not need one.**
`test_the_silence_window_at_three_five_and_eight` (`:2917`) carries no named liveness assertion,
and its `mute[0] == mute[1] == mute[2]` control is a three-way equality that three dead arms
would satisfy. But it goes on to pin about fourteen concrete non-zero figures — `internal ==
[64, 36, 20]`, `rebutted == [0, 25, 44]`, `corroborated == [45, 45, 45]`, `net == [−41, −106,
−185]` and their six-unit twins — and every one of those is produced by the channels under test
(`ask`, `adopt`, `publish`, `challenge`, `dispose_challenges`), all of which this audit finds
live and consequential. A dead channel fails those assertions. That is real de-facto protection,
unlike the corroboration gate, whose pinned tally is computed by a *different* channel from the
one its prose credits — which is exactly why that gate's zero went unnoticed and this one's
figures could not. **Task 6 should give this gate a named clause for legibility, not a repair.**

## What is deferred to `src/`

Per the spec's §9: a change to `c_unit.py` alters the C-series' subject matter, not merely its
measurement, and cannot be smuggled in as an audit. Named, with the findings each taints.

**D-A1 — `_mint_challenge`'s once-per-law-ever key is shared between `challenge` and
`corroborate`** (`src/c_unit.py:1488–1506`), and both harnesses run `challenge` first. The key is
therefore always spent by the time a call is read, and `Unit.corroborate`'s counterexample branch
cannot mint in any community where units also challenge. Its head branch is preempted the same
way by `publish` through `(FACT, head)`. The shared key is deliberate and documented — *"a unit
answering a call for help must not be able to enter a second inscription of evidence it has
already published"* — so the defect is not the key; it is that **with the key in place, the
method has no reachable state left**. Whether corroboration should be a distinct act at all, or
whether the phase order should let a call be answered before the same evidence goes out
unprompted, is a question about what the C-series is modelling.

*Taints:* nothing numerically. Every published **elimination-by-corroboration** count is computed
by `dispose_challenges` from challenge marks, and the audit reproduces each one (C3 0, C4 4,
C5 45, C6 0, C7 24, C8 0). The published **call** counts are outside the audit's figure set and
were neither re-derived nor disturbed. What it taints is the
**reading** of those figures as a solicited inquiry — §1 above — and the claim that the external
apparatus "is no longer dead code."

**D-A2 — `Unit.answer` and `Unit.publish` share the per-unit `(FACT, content)` key, and
`MarkBoard.answer_to` matches author-blind and round-blind.** `answer`'s output is therefore
always a subset of what `publish` emits in the same round, in any harness that publishes
unprompted — which is D-1's finding reproduced at scale in eleven independent arms. The phase
order does not fix it: `_play_ask_and_challenge` already runs answer at (d) before publish at
(e), and the channel is inert anyway.

*Taints:* nothing numerically, and no finding — the testimony reaches the board either way. What
it taints is every sentence that attributes a property of this world to `Unit.answer` — §5 above
— and the standing description of `answer` as "the other half of the division of labour", which
is true only in `_play`, the one harness with no `publish`.

**Out of scope and unmeasured.** This audit asked whether a channel fired and whether its firing
moved anything. Whether what it minted was the *right* thing is the C-series' own subject and was
not re-opened (spec §10). The audit certifies only figures whose arms are still in the tree; the
stale window-5 tables in §6 are the one place a published number could not be re-derived, and
they are reported as stale rather than corrected.
