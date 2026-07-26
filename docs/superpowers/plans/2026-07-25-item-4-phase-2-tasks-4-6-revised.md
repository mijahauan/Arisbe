# Item 4 Phase 2: Tasks 4–6 (Revised) — Wiring AlternativeSet with Inquiry Principle

**Status:** Revised task specifications incorporating discovery-of-distinctions principle  
**Basis:** `docs/superpowers/specs/2026-07-25-alternative-set-inquiry-principle.md`  
**Date:** 2026-07-25

---

## Overview

Tasks 4–6 wire AlternativeSet into where alternatives actually arise in the system. The revised principle: **do not pre-filter alternatives; discover distinctions through inquiry, and track expansions of S (sign-space) and A (action-space).**

Each task follows this pattern:
1. Detect alternatives (unfiltered)
2. Generate meta-questions about consequences
3. Trace inquiry paths
4. Discover finer distinctions
5. Track S/A expansions
6. Update warrant based on discoveries
7. Record in UoD for future reference

---

## Task 4: QueryDocket Wiring (UNKNOWN Verdicts → Interrogative Alternatives)

**What:** When QueryDocket encounters an UNKNOWN verdict, create an interrogative AlternativeSet and trace what each alternative path leads to.

**Current state:** QueryDocket registers UNKNOWN verdicts as "wants" (ephemeral).  
**New state:** Generate interrogative AlternativeSet + trace consequences + discover distinctions.

### Implementation

**When UNKNOWN verdict occurs:**

1. **Detect alternatives (unfiltered)**
   ```
   alternatives = {TRUE, FALSE, ...other possible verdicts}
   kind = "interrogative"
   ```

2. **Generate meta-questions**
   ```
   For each alternative A:
     Q: "If we assume A, what M-revisions would follow?"
     Q: "What dispositions would be triggered?"
     Q: "How would K1/K2/K3/K4 change?"
   ```

3. **Trace inquiry paths** (internal discovery — dry-run, no actual revision)
   ```
   For each alternative A:
     path_A = [
       "peel(M, A) → verdict V_A",
       "disposition_of(V_A) → dispo_A",
       "revise_with(dispo_A) → M_A",
       "measure K-vector(M_A) → k-vector_A"
     ]
   ```

3b. **Listen to membrane** (external input)
   ```
   Watch for:
     - Is there external feedback on this verdict?
     - Does another system suggest a different interpretation?
     - Does the world (empirical test, human input) contradict the trace?
   
   Record external input with source and warrant < 1.0 (received, not derived)
   ```

4. **Discover distinctions** (integration)
   ```
   Compare outcomes from BOTH sources (internal trace + external input):
     - Do M-revisions differ? → new vocabulary: "M-revision-path"
     - Do K-vectors differ? → new vocabulary: "K-trajectory"
     - Do dispositions differ? → new vocabulary: "disposition-consequence"
     - Does external input suggest novel vocabulary? → integrate it
   
   Materiality check:
     If all paths lead to identical M, K, dispositions → spurious (collapse)
     If paths differ (internal) → material alternative (lock in)
     If external input enriches the picture → material alternative (integrate)
     If internal trace and external input conflict → mid warrant (requires further inquiry)
   ```

5. **Refine S/A within bounded capacity**
   ```
   Discovered distinctions: {M-revision-path, K-trajectory, disposition-consequence}
   
   S refinement (within this kyte's limited vocabulary capacity):
     Add: {"M-revision-path", "K-trajectory", "disposition-consequence"}
     Constraint: This kyte can only hold N vocabulary terms total
     Decision: What unused vocabulary is deprecated? (disuse-decay)
     Result: S_refined (reordered priorities, some old vocabulary fades)
   
   A refinement (within this kyte's limited action capacity):
     Add: {"choose-M-revision-by-path", "optimize-for-K-trajectory", ...}
     Constraint: This kyte can only deploy M action strategies total
     Decision: What unused actions are deprioritized? (disuse-decay)
     Result: A_refined (specialized in new actions, some old strategies fade)
   ```

6. **Track disuse-decay**
   ```
   Vocabulary deprecated: {...old terms unused by this inquiry...}
   Actions deprecated: {...old strategies superseded by new ones...}
   Reason: Rational capacity management (this kyte is finite)
   Record: For succession (next kyte may specialize differently)
   ```

7. **Update warrant**
   ```
   If material distinctions found:
     warrant = 1.0 (lock in)
   Else:
     warrant = 0.0 (collapse to one)
   
   External validation: Did membrane (other kytes) agree?
     external_warrant = 1.0 if membrane confirms, 0.5 if partial, 0.0 if contradicts
   ```

8. **Record in UoD**
   ```
   AlternativeSet(
     id="unknown_{proposal_id}",
     context=M_at_point_of_unknown,
     alternatives={TRUE, FALSE, ...},
     kind="interrogative",
     emerged_at_state=state_id_of_unknown,
     consequence_description=discovered_distinctions,
     s_expansion={"M-revision-path", "K-trajectory", "disposition-consequence"},
     s_decayed={...vocabulary no longer used by this kyte...},
     a_expansion={"choose-M-revision-by-path", "optimize-for-K-trajectory", ...},
     a_decayed={...actions superseded by new ones...},
     warrant=warrant_value,  # internal discovery
     external_input=membrane_feedback,
     external_warrant=external_warrant_value
   )
   ```

### Tests

- **Detect alternatives:** UNKNOWN verdict → creates interrogative AlternativeSet
- **Trace paths:** Each alternative's consequences are computed (dry-run)
- **Discover distinctions:** Material differences are found and documented
- **S/A expansion:** New vocabulary and actions are added
- **Warrant updates:** Based on actual discovered differences
- **Record persistence:** AlternativeSet is saved to alternatives.jsonl
- **Edge cases:** All-paths-identical (collapse), partial distinctions (mid-warrant)

---

## Task 5: attention_brief Wiring (Thin Spots → Hypothetical Alternatives)

**What:** When attention_brief identifies a thin spot (rare or ungrounded relation), create a hypothetical AlternativeSet exploring different groundings and trace their consequences.

**Current state:** attention_brief lists thin spots as alert items (ephemeral).  
**New state:** Generate hypothetical AlternativeSet + trace consequence of different groundings + discover distinctions.

### Implementation

**When thin spot is detected (e.g., R has ≤1 instance):**

1. **Detect alternatives (unfiltered)**
   ```
   alternatives = {grounding-A, grounding-B, grounding-C, ...}
   kind = "hypothetical"
   ```
   (Generate from domain: what are plausible groundings for R?)

2. **Generate meta-questions**
   ```
   For each grounding G:
     Q: "If we assume R is grounded via G, what inferences follow?"
     Q: "What new rules become derivable?"
     Q: "How would M change?"
   ```

3. **Trace inquiry paths**
   ```
   For each grounding G:
     path_G = [
       "assert_grounding(R, G) into M → M_G",
       "materialize(M_G) → facts_G",
       "what_infers(facts_G) → inferences_G",
       "measure K-vector(M_G) → k-vector_G"
     ]
   ```

4. **Discover distinctions**
   ```
   Compare outcomes:
     - Do inferences differ by grounding? → new vocabulary: "inference-consequence"
     - Do K-vectors diverge? → new vocabulary: "grounding-stability"
     - Do derivable rules differ? → new vocabulary: "rule-consequence"
   
   Materiality check:
     If all groundings lead to identical inferences/K/rules → spurious
     If groundings differ → material alternative
   ```

5. **Refine S/A within bounded capacity**
   ```
   Discovered distinctions: {inference-consequence, grounding-stability, rule-consequence}
   
   S refinement (within this kyte's vocabulary capacity):
     Add: {"inference-consequence", "grounding-stability", "rule-consequence"}
     Constraint: Limited vocabulary space; prioritize what matters
     Decision: Deprecate unused vocabulary from prior inquiry cycles
     Result: S_refined (new distinctions added, old ones decay)
   
   A refinement (within this kyte's action capacity):
     Add: {"prefer-grounding-by-inference", "condition-on-stability", ...}
     Constraint: Limited action space; specialize in what works
     Decision: Deprecate grounding heuristics superseded by new evidence
     Result: A_refined (new strategies added, old ones fade)
   ```

6. **Track disuse-decay**
   ```
   Vocabulary deprecated: {...old grounding concepts no longer used...}
   Actions deprecated: {...old grounding heuristics superseded...}
   Reason: This kyte is finite; repurpose capacity for better groundings
   Record: For succession
   ```

7. **Update warrant**
   ```
   Based on actual differences discovered in inferences/K/rules
   High warrant if groundings differ significantly in consequences
   Low warrant if all groundings converge (collapse to one)
   External warrant: Do other kytes agree on which groundings matter?
   ```

8. **Record in UoD**
   ```
   AlternativeSet(
     id="thin_spot_{relation_name}",
     context=M_at_point_of_thin_spot,
     alternatives={grounding-A, grounding-B, ...},
     kind="hypothetical",
     emerged_at_state=state_id_of_thin_spot,
     consequence_description=discovered_inference_distinctions,
     s_expansion={"inference-consequence", "grounding-stability", "rule-consequence"},
     s_decayed={...old vocabulary no longer used...},
     a_expansion={"prefer-grounding-by-inference", "condition-on-stability", ...},
     a_decayed={...old heuristics superseded...},
     warrant=warrant_value,  # internal discovery
     external_input=membrane_feedback,
     external_warrant=external_warrant_value
   )
   ```

### Tests

- **Detect thin spots:** Relation with ≤N instances → creates hypothetical AlternativeSet
- **Generate groundings:** Plausible groundings enumerated from domain
- **Trace paths:** Each grounding's inference consequences computed
- **Discover distinctions:** Which groundings differ in inferences/K/rules?
- **S/A expansion:** New vocabulary and actions added
- **Warrant updates:** Based on actual inference differences
- **Record persistence:** AlternativeSet saved to alternatives.jsonl
- **Edge cases:** All groundings identical (collapse), partial differences (mid-warrant)

---

## Task 6: modal_query Wiring (Branch Points → Modal Alternatives)

**What:** When modal_query detects a branch point (◇M but not □M), create a modal AlternativeSet exploring reachable futures and trace their material differences.

**Current state:** modal_query reads ◇/□ off the DAG (transient).  
**New state:** Generate modal AlternativeSet + trace branch consequences + discover distinctions.

### Implementation

**When branch point is detected (multiple reachable futures):**

1. **Detect alternatives (unfiltered)**
   ```
   alternatives = {future-branch-1, future-branch-2, ...}
   kind = "modal"
   ```

2. **Generate meta-questions**
   ```
   For each branch B:
     Q: "If this branch is realized, what would the state be?"
     Q: "How would K1/K2/K3/K4 differ?"
     Q: "Would the same relations hold?"
   ```

3. **Trace inquiry paths**
   ```
   For each branch B:
     path_B = [
       "reach_state(B) → state_B",
       "materialize(state_B) → facts_B",
       "measure K-vector(state_B) → k-vector_B",
       "compare(facts_B vs facts_current) → differences_B"
     ]
   ```

4. **Discover distinctions**
   ```
   Compare outcomes:
     - Do K-vectors differ significantly? → new vocabulary: "K-trajectory-divergence"
     - Do reachable facts differ? → new vocabulary: "future-consequence"
     - Do futures split on durability/stability? → new vocabulary: "branch-durability"
   
   Materiality check:
     If all branches converge on same K/facts → spurious (no real difference)
     If branches diverge → material alternative (real choice point)
   ```

5. **Refine S/A within bounded capacity**
   ```
   Discovered distinctions: {K-trajectory-divergence, future-consequence, branch-durability}
   
   S refinement (within this kyte's vocabulary capacity):
     Add: {"K-trajectory-divergence", "future-consequence", "branch-durability"}
     Constraint: Limited vocabulary; focus on distinctions this kyte can make
     Decision: Deprecate unused modal vocabulary from prior cycles
     Result: S_refined (branch-point vocabulary added, old modal concepts decay)
   
   A refinement (within this kyte's action capacity):
     Add: {"optimize-for-K-trajectory", "condition-on-future-consequence", ...}
     Constraint: Limited action space; specialize in explorable branches
     Decision: Deprecate actions irrelevant to these branches
     Result: A_refined (specialized for this branch topology, others fade)
   ```

6. **Track disuse-decay**
   ```
   Vocabulary deprecated: {...old branch-point vocabulary no longer activated...}
   Actions deprecated: {...actions irrelevant to observed branches...}
   Reason: This kyte is finite; focus capacity on what it actually encounters
   Record: For succession (if branches change, other kytes may need old actions)
   ```

7. **Update warrant**
   ```
   Based on actual K/fact divergence across branches:
   If branches are near-identical → warrant low (collapse to one)
   If branches diverge significantly → warrant high (lock in)
   External warrant: Do other kytes see the same branch divergence?
   ```

8. **Record in UoD**
   ```
   AlternativeSet(
     id="branch_point_{state_id}",
     context=M_at_branch_point,
     alternatives={future-branch-1, future-branch-2, ...},
     kind="modal",
     emerged_at_state=state_id,
     consequence_description=discovered_branch_distinctions,
     s_expansion={"K-trajectory-divergence", "future-consequence", "branch-durability"},
     s_decayed={...old modal vocabulary not activated by these branches...},
     a_expansion={"optimize-for-K-trajectory", "condition-on-future-consequence", ...},
     a_decayed={...actions irrelevant to observed topology...},
     warrant=warrant_value,  # internal discovery
     external_input=membrane_feedback,
     external_warrant=external_warrant_value
   )
   ```

### Tests

- **Detect branches:** ◇M but not □M → creates modal AlternativeSet
- **Enumerate futures:** All reachable branches from this state
- **Trace K-vectors:** Each branch's K1/K2/K3/K4 computed
- **Discover distinctions:** Which branches diverge in K or facts?
- **S/A expansion:** New vocabulary and actions added
- **Warrant updates:** Based on actual branch divergence
- **Record persistence:** AlternativeSet saved to alternatives.jsonl
- **Edge cases:** Branches converge (collapse), partial divergence (mid-warrant)

---

## Cross-Task Principles (4–6)

### 1. **Never Pre-Filter**
Do not assume which alternatives are material. Detect all, then test.

### 2. **Always Trace Consequences** (Internal Discovery)
For each alternative, compute the full inquiry path (peel, revise, measure, infer).

### 3. **Listen to the Membrane** (External Input)
Watch for corrections, suggestions, novelty coming from outside the system.
- From QueryDocket: does an external query suggest a different framing?
- From attention_brief: does external feedback contradict the thin-spot diagnosis?
- From modal_query: does the world suggest a branch that wasn't detected internally?

### 4. **Discover Distinctions, Don't Assume Them** (Integration)
Compare outcomes from BOTH sources (internal trace + external input).
Let the differences that emerge define materiality.

### 5. **Refine S/A Within Bounded Capacity** (from both sources)
Document what new vocabulary (S) and new actions (A) this kyte refined.
**Key: This is refinement within limits, not unbounded expansion.**
- Internal source: vocabulary from traced consequences
- External source: vocabulary from membrane input
- Bounded capacity: What must decay/be forgotten to make room?
- Heterogeneity: Different kytes will refine differently (different bounds, different priorities)

### 6. **Track Disuse-Decay** (rational capacity management)
Document what vocabulary and actions were deprioritized.
- This is not loss; it's rational resource management.
- The kyte is finite and mortal.
- Track what decayed (for succession: next generation may need it in different context).

### 7. **Update Warrant Based on Discovery AND Reception**
- Internal distinctions: warrant reflects traced evidence
- External input: warrant starts lower (received, not derived), updates as it integrates
- Aligned sources: high warrant (robust)
- Conflicting sources: mid warrant (requires further inquiry)

### 8. **Record Everything for Diachronic Learning**
AlternativeSet persists so future inquiries and successor kytes can learn:
- What distinctions matter (internal discovery)
- What was forgotten and why (disuse-decay)
- What external input was valuable (membrane dialogue)
- How internal and external sources interact
- What the next generation might specialize in (given their different bounds)

---

## Integration with Existing Systems

### QueryDocket
- Currently registers wants from UNKNOWN
- Now: Creates interrogative AlternativeSet + traces consequences
- Learns: Which verdicts lead to materially different M-revisions?

### attention_brief
- Currently alerts on thin spots
- Now: Creates hypothetical AlternativeSet + traces grounding consequences
- Learns: Which groundings lead to different inferences?

### modal_query
- Currently reads ◇/□ off DAG
- Now: Creates modal AlternativeSet + traces branch consequences
- Learns: Which branches truly diverge in material outcomes?

### UniverseOfDiscourse
- Stores AlternativeSets in `alternatives_by_state`
- Tracks S/A expansions as attributes on AlternativeSet
- Enables longitudinal study: did this system grow its perceptual/action capacity?

---

## Testing Strategy

**Per-task tests:**
- Detect alternatives (unfiltered)
- Trace inquiry paths (consequences computed)
- Discover distinctions (material differences found)
- S/A expansion tracked
- Warrant updates based on discoveries
- Persistence (JSONL round-trip)
- Edge cases (spurious alternatives, partial distinctions)

**Integration tests:**
- QueryDocket + Task 4: UNKNOWN → interrogative AlternativeSet
- attention_brief + Task 5: thin spot → hypothetical AlternativeSet
- modal_query + Task 6: branch point → modal AlternativeSet

**Learning tests:**
- After N inquiries, does S/A grow measurably?
- Do warrant updates correlate with actual material differences?
- Can system use learned distinctions to detect finer alternatives next round?

---

## Success Criteria

- ✓ All alternatives detected and recorded (unfiltered)
- ✓ Inquiry paths traced for each alternative
- ✓ Distinctions discovered through comparison, not assumption
- ✓ S/A expansions documented and persistent
- ✓ Warrant reflects actual discovered differences
- ✓ System demonstrates capacity growth over multiple inquiries
- ✓ Zero pre-filtering; all materiality claims justified by traced inquiry
