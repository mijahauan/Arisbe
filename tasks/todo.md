# The 2026-07-31 rulings — execution status

Six rulings taken. **Six are done and committed** (`43096ba`, `c2ee801`, and the
re-measurement pass below, `remeasurement-pass-2026-07-31`, based at `3ba6816`).
One code ruling remains, sized below, blocked on a decision.

## Done

- [x] **Make the nested reading doctrinal** — asymmetry (Thirdness ⇒ Secondness
      and Firstness, never the converse; pre-semiosis preserved), the cut
      correspondence verified against the protected core, premise 1 grounded in
      the categories rather than in method.
- [x] **Pattee as the threshold of record** (+ the author's **Intent 0** /
      discriminated-binding proposal; Bickhard and Deacon examined and set
      aside with reasons). Promoted to ratified-doctrine in the map.
- [x] **The West corrections** — both canonical lists 6 → 8 conditions;
      spec §8's self-contradiction closed; five book sentences corrected; E3c's
      stale "in flight" fixed; the C-series finally has a capability-map row.
- [x] **Keep the current title for now.**
- [x] **Retire `net_score` as a gate statistic.** Not deleted — demoted. It
      survives as a property, docstring changed to "observability, never a
      gate," and the rule now reads: no gate decided by comparing hits −
      misses BETWEEN arms; a cross-arm gate decides on the law components with
      a participation clause; within one arm a held law pays on `hits`/`misses`
      directly; pinning an exact measured value is reporting and stays. Six
      net comparisons survive (the final review pass found two more the
      tracing grep had missed, both in the asking-vs-mute test — see
      `tests/test_c_channels.py`'s "KEPT CLAUSE FIVE"/"SIX"), each annotated
      as asserting a pathology OF the statistic rather than deciding BY it;
      two of the six are the forbidden cross-arm comparison unfolded into its
      hit/miss components, kept only because the arm they sit in cannot lose
      a law. Phase ran and verified at 204 C tests passing, identical to the
      pre-change baseline — no figure moved.
- [x] **`corroboration_window` default 5 → 8.** One line
      (`src/c_unit.py:226`), plus the uniformity guard the rider in ruling 2
      required (`_assert_uniform_rate`, refusing a community whose units
      disagree on the rate triple — fired zero times in the existing suite,
      meaning uniformity was already being held in practice). Re-measured: 204
      C tests pass at the new window; every touched docstring keeps both
      readings, each labelled by window. See Review below for the headline
      figures.

## Remaining, with honest sizing

- [ ] **BLOCKED — weight witnesses rather than count them.** The count sits at
      `src/c_unit.py:1807-1814`: `witnesses = {m.author for m in live} -
      {self.unit_id}`, then `len(witnesses) >= corroborating_witnesses`.
      Replacing the count with a weighted sum needs **something to weight by**,
      and the natural weight is the **credential** — which is designed
      (author's ruling 1) and not built.
      **Two ways not to take:** weighting by the challenger's private `peers`
      standing would make corroboration depend on one unit's private opinion,
      defeating the "socially available, objectified reality" that §9d's ruling
      grounds corroboration in; and inventing a weight to get the code compiling
      would be installing the solution, which the standing rule forbids.
      **So this ruling directs the stage-4 credential build rather than naming a
      change available today.** It needs either the credential first, or an
      author ruling on an interim weight.

## Recommended order

1. ~~The `net_score` + window pass together (one re-measurement).~~ Done, see above.
2. The credential build (stage 4 part (c)), which unblocks weighted witnesses.
3. The scarcity test — cap answering, re-run typify — which is small and tests
   the thesis this session produced.

## Review

**What moved.** One figure, by design: `corroboration_window` 5 → 8 (phase 3), the
single re-measurement the plan called for. Every narrated figure downstream of the
window moved and now carries both readings, labelled. Two representative headline
moves: GATE 1's live-world net −106 → −185; four-unit scoring preferences 1 → 0.

**What did not move.** Phases 1 (`Unit.attended` + the cost reader + the
uniformity guard) and 2 (the `net_score` retirement itself) each ran the full C
suite at 204 passed, byte-identical to the pre-phase baseline — no measured
figure moved in either phase. This was the non-interference rule under test
(THE_KYTOS §1.3): an instrument that changes the act it measures has got out in
front of it. Neither phase got out in front of it.

**Phase 1/2 canary result.** 204 C tests green at every checkpoint (199 baseline
+ 5 added by the guard/attendance tests); the uniformity guard fired **zero
times** in the existing suite — a community's units already agreed on their rate
triple in practice, and the guard now makes that structural rather than
incidental.

**Honest correction to this file's own sizing.** The "18 assertions" estimate
above was an undercount, built by grepping `assert.*net_score`, and it stayed
an undercount through three rounds of correction: comparisons whose
`net_score` reads happened upstream in `append` lines (found reviewing the
ask-vs-mute gate); then more of the same shape (three further survivors, each
now annotated); then the corrected verification grep itself missed `assert
live_total > mute_total`, whose variables carry no "net" in their name at all.
The standing method now is: enumerate every read of the statistic, trace its
variable to every consuming assertion, and require each consumer to be a pin,
a message, or an annotated kept clause. A grep matches names; what matters is
roles.

**Three findings worth recording beyond the mechanical result:**

1. **The ruling's own sweep table predicted GATE 1's move, and it held.**
   −106 → −185 is exactly the four-unit/window-8 row already sitting in
   `corroboration_window`'s measured table (internal 20 / rebutted 44 /
   20-of-64 true laws lost / net −185) — the ruling's evidence and this gate's
   re-measurement are the same run read twice, agreeing digit for digit.
2. **Typification lost its last foothold.** Scoring preferences at four units
   fell 1 → 0. Across eight seeds exactly one unit ever held a preference about
   whom to ask at four units; at window 8 there are none, so
   `test_gate_two_...`'s subject — "no unit at four ever had a choice" — is now
   true without qualification, not needing the surrounding docstring's old
   carve-out.
3. **The methodological finding above (the undercount) matters more than
   either measured figure.** Separately, stale narration needed four
   correction rounds in a single file (`test_c_stage_gates.py`) before every
   digit token in its docstring was accounted for — because only pinned
   assertions fail when the world moves, and every figure living only in prose
   is unprotected.
