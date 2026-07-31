# The 2026-07-31 rulings — execution status

Six rulings taken. **Four are done and committed** (`43096ba`, `c2ee801`). Three
code rulings remain, sized below; one of them is blocked on a decision.

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

## Remaining, with honest sizing

- [ ] **Retire `net_score` as a gate statistic.** 18 assertions across the C
      test files; 5 are load-bearing gates that must be re-expressed on the
      vector (*bets placed · hits among bets · true laws held · converses
      held*), and 5 in `test_c_membrane.py` pin the ledger's arithmetic and
      survive untouched. Per ruling 2, the vector also **gains a per-unit cost
      component**, or terminal-unit invariance stays unmeasurable.
      *Cost: a day's work, mostly re-expression, plus one suite run to confirm.*

- [ ] **`corroboration_window` default 5 → 8.** The constant is one line
      (`src/c_unit.py:226`). The expense is everything downstream: the C suite
      narrates measured figures throughout, and the window is the most
      consequential knob in the arm, so **many narrated figures and some
      assertions move**. The suite runs 14 minutes, so this is an iterative
      re-measurement pass, not an edit.
      *Do it in the same pass as the `net_score` retirement — one
      re-measurement, not two.*

- [ ] **BLOCKED — weight witnesses rather than count them.** The count sits at
      `src/c_unit.py:1759-1766`: `witnesses = {m.author for m in live} -
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

1. The `net_score` + window pass together (one re-measurement).
2. The credential build (stage 4 part (c)), which unblocks weighted witnesses.
3. The scarcity test — cap answering, re-run typify — which is small and tests
   the thesis this session produced.

## Review

(filled in on completion)
