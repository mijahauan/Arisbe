# Item 4: Phase 1 Pilot — Erotetic Modeling of E3 Branch Points

**Date:** 2026-07-25  
**Status:** Pilot (Phase 1 of "Do we model questions?")  
**Data source:** West-in-kytē E3 (complete, deterministic)  
**Question:** Can we model branch points in the DAG as erotetic questions, and does this reveal patterns E3 missed?

---

## Background: E3's Branch Point

At N=3 granularity, the three Arm-N walks diverge into **different basins**:
- **W1** (from N=1 monolith): settles at **3/8/1** (cost 119,935)
- **W2** (from N=12 singletons): settles at **10/1/1** (cost 101,411)
- **W3** (from N=4 mid-start): settles at **10/1/1** (cost 102,099)

**The question:** Why do W1 and W2/W3 diverge, even though all reach N=3?  
**The E3 finding:** "The landscape has multiple N=3 basins, and which one the walk finds depends on where it starts" (PE2 refuted).

---

## Erotetic Formulation

### Branch Point: The State N=3 (Any N=3 Bucketing)

**The question:** "Which N=3 basin will this descent path reach?"

**Presupposition:**
```
Given:
- Current state M₀ is a valid bucketing of the 12 folders
- At least two legal N=3 partitions exist (3/8/1 and 10/1/1 are both valid)
- Both are local optima under Arm-N steepest descent
- The current position in the search landscape is deterministic

Then the question is well-posed: Which basin will the walk reach?
```

**Erotetic core (the answer set):**
```
{
  Answer₁: "The 10/1/1 basin (cost ≈101–102k)"
    → Expected for N≥3 merge-direction starts (fewer folders to merge down from)
  
  Answer₂: "The 3/8/1 basin (cost ≈120k)"
    → Expected for N=1 split-direction starts (fewer splits to refine)
  
  Answer₃: "Some other N=3 basin"
    → Possible but unmeasured by E3 (E3b will explore this)
}
```

**Factors that determine the answer:**
1. **Start position** (N₀): whether approaching from above (merges) or below (splits)
2. **Path history** (trajectory so far): earlier decisions that constrained later moves
3. **Landscape structure** (the cost manifold): which basin is reachable from this point via steepest descent

### What Each Walk Answered

| Walk | Start | Answer | Cost | Explanation |
|------|-------|--------|------|-------------|
| **W1** | N=1 monolith | 3/8/1 basin | 119,935 | Split-direction start → path leads uphill from merged-down basin |
| **W2** | N=12 singletons | 10/1/1 basin | 101,411 | Merge-direction start → path descends into denser basin |
| **W3** | N=4 (6/3/2/1) | 10/1/1 basin | 102,099 | Mid-start, close to N=3 → path finds denser basin |

### Resolution of the Question

**Before the walk (branch point):** ◇(3/8/1) ∧ ◇(10/1/1) — both basins are reachable  
**After the walk (answer locked in):** □(3/8/1) for W1; □(10/1/1) for W2/W3

The **answer doesn't uniquely select a basin**—it selects a *path* through the landscape that *locks in* one basin by the walk's termination condition (no improving step available).

---

## Insight: Start Position as Presupposition

The erotetic formulation reveals:

**PE2 ("basin agreement") is not a logic error—it's a misframed question.**

- **E3 asked:** "Do all starts converge to the same partition?" (presupposes one optimum)
- **The landscape answers:** "No. The presupposition was false—the landscape has multiple N=3 optima."

**Reframed erotetically:**
- **Correct question:** "Given a start position, which basin is reachable?" (presupposition: the start is given)
- **Answer:** Depends on the start—W1→3/8/1, W2→10/1/1

**This is not a contradiction; it's the correct erotetic resolution.**

---

## Pattern Recognition: The Start-Basin Mapping

From E3's three walks, we can infer a **start-to-basin mapping** that PE2 missed:

```
Inferred Rule:
- IF start is merge-direction (N≥3) THEN reach 10/1/1 basin (≈101–102k)
- IF start is split-direction (N=1) THEN reach 3/8/1 basin (≈120k)
- IF start is mid-position (N=3) THEN defaults to merge direction (→10/1/1)
```

**E3b will test this** by sampling many N=3 start positions and measuring which basin each reaches.

---

## What This Reveals That E3 Missed

1. **The landscape is **asymmetric** around N=3:**
   - The merge-direction approach (merging from singles) reaches a **denser, cheaper basin**
   - The split-direction approach (splitting from the monolith) reaches a **sparser, dearer basin**
   - **Cost difference:** 18% (120k vs. 102k) — substantial and directional

2. **The basin structure is **stratified by approach**, not symmetrical:**
   - "The optimum" (singular) doesn't exist; instead, there's a **reachability gradient**
   - The question "which basin?" has no universal answer—only "which basin from this start?"

3. **This is a discovery about the coordination mechanism:**
   - **Merge-based coordination** (top-down) finds cheaper optima
   - **Split-based coordination** (bottom-up) finds more expensive optima
   - This suggests **federation (merge-direction) is operationally superior** to monolithic decomposition (split-direction)

---

## Proposal for E3b

**E3b will enumerate ~36 start positions (N=1..12 + contiguous compositions).**

**Erotetic interpretation:**
- Each of the 36 starts is **a different presupposition** (a different branch point)
- The erotetic core for each is the set of N=3 basins it can reach
- E3b's full-neighbourhood diagnostic answers: "For each presupposition, which basins are reachable?"

**Expected finding:** A **presupposition-to-basin reachability matrix** that shows:
- Which N=3 basins are reachable from each start
- Whether the merge→10/1/1 and split→3/8/1 rules hold across all 36
- Whether there are intermediate starts that reach both basins (the boundary region)

This matrix is the **answer** to the erotetic question "how does the landscape partition into basins?"

---

## Validation: Does Erotetic Modeling Add Value?

**Comparison:**

| Framing | Insight | Revealed By |
|---------|---------|------------|
| **E3's statistical framing** (PE1–PE5) | PE2 refutes: "no unique optimum" | Post-hoc pattern matching |
| **Erotetic framing** (Q: "which basin?") | Presupposition matters: start position determines reachability | Structural reformulation |
| **Result** | Same finding, but now causally grounded | E3b's reachability matrix will confirm it |

**Early verdict:** Erotetic framing doesn't *contradict* E3; it **reorganizes the findings** into question-answer structure. The value appears in:
1. **Clarity:** The question ("which basin from this start?") is sharper than the prior ("does it converge uniquely?")
2. **Prediction:** We can now *predict* where new starts land (the merge→10/1/1 rule)
3. **Composability:** Erotetic structure lets us reason about **chains of questions** (if 10/1/1 is cheaper, *why* is it cheaper? → next question)

---

## Conclusion

**Item 4 Phase 1 verdict: PROCEEDING TO PHASE 2**

Erotetic modeling of E3's branch points reveals:
- ✓ Branch points naturally decompose into presupposition + erotetic core
- ✓ The formalism clarifies why PE2 "refuted" (the presupposition was wrong, not the landscape)
- ✓ Patterns emerge: start-direction predicts basin reachability
- ✓ Predictive power: we can test the inference on E3b when it completes

**Next: Phase 2 will generalize this to a corpus-persistent representation** — storing branch points and their erotetic answers in the UoD archive so we can reason about **when branch points repeat** and **whether the same start always reaches the same basin**.

---

## References

- **E3 results:** `runs/WEST_E3_LOG.md` (PE1–PE5 verdicts, four walks)
- **E3 design:** `docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md`
- **Erotetic logic foundation:** Hamblin (1958) "Questions in Logic"; Wisniewski (2001) "Erotetic implication"
- **Field position:** See Item 4 field overview (this session)
