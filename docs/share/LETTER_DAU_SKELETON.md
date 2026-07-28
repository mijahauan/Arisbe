# Letter skeleton — Frithjof Dau

**Status: internal skeleton (2026-07-27), not for sending.**
**Why him:** his *Mathematical Logic with Diagrams* is Arisbe's **bedrock** —
the six transformation rules, the EGI data model, and the soundness guarantees
are his, implemented faithfully and declared non-negotiable. No one is better
placed to refute the project's central engineering claim.

---

## 1 · The debt (open with what is his)

- The calculus is **his, unimproved**: ERA, INS, IT+, IT−, DC+, DC−,
  Beta-aware, over his `RelationalGraphWithCuts` shape; "the picture never
  lies" is a theorem here only because his formalization makes it one.
- As far as we could find, **no machine-checked formalization of his EG
  calculus exists** (Coq/Lean/Isabelle); Arisbe's protected mathematical core
  (~118 always-passing tests over the rules, closure, isomorphism, and the
  Beta proof exercises) is the closest *operational* guarantor we located —
  an executable specification, offered for his inspection.

## 2 · The proposition, in his vocabulary

1. **The correspondence invariant** — the linear form and the drawn form held
   provably to denote one mathematical object, attested at runtime on every
   served pair (`attest_correspondence`, three-regime scoping). His Chapter-18
   translations are the linear side's warrant; the claim is that the drawn
   side now carries equal standing.
2. **The three examined departures** (FIDELITY_AND_DEPARTURES) — each
   adversarially examined, each surviving *with amendment*: (i) convergence
   and "the real"; (ii) nothing derived-contingent at level 0 (the
   two-register account); (iii) Gamma's modal program not *needed* (adequacy,
   not completeness — no new modal mark; the diachronic DAG as the drawn
   Kripke frame). Plus the conceded loss: identity as a spot `(= x y)` where
   Peirce had the line — departure IV. He may consider any of these wrongly
   taken; the record of the examinations is the invitation.
3. **B-min — the one authorized opening of the core** (2026-07-16): two
   parallel maps (`sort`, `quotation`) adding a second-order sort on the
   incidence and a graph-valued area (mention, never use), with **all six
   rules made sort-preserving** and the quotation area opaque to them. The
   standing invariant is **conservativity over the Dau core** (the A3
   three-tier gate: corpus-wide invisibility; the erasure projection — a
   quoted law licenses nothing; rules restraint). "Dau remains the
   guarantor" is not a posture here — it is a testable claim, and we would
   want him to test it.

## 3 · Peels already played (evidence to cite)

- The core suite + the six correspondence test shapes (§7) over the corpus.
- The A3 conservativity gate (`test_second_order_conservativity.py`).
- Worked chains: Peirce's Law, Barbara, *Praeclarum Theorema*, group-identity
  uniqueness — real rule applications, replayable.
- The universal-generalization homework (UNIVERSAL_GENERALIZATION_DAU_HOMEWORK
  — a question we owe to his framework's discipline).

## 4 · The invitation (refutable claims + asks)

1. Does the implementation read to him as *his* calculus? Any divergence he
   finds is a defect on our side by definition — the bedrock is not up for
   negotiation.
2. Is the **conservativity formulation** of the second-order opening the
   right invariant — is A3 the theorem he would demand, or is there a leak
   he can construct?
3. Departure IV (identity as spot): is our concession honest, or is there a
   line-of-identity treatment we should have found?
4. Would a machine-checked mechanization of his calculus interest him as a
   joint or supervised effort? (We flag it as a clear field contribution.)

## 5 · What must stand behind the link (need-list)

- **FIDELITY_AND_DEPARTURES** + the adversarial-examination record (exist;
  hardened by Examination VI).
- **LINEAR_GRAPHICAL_CORRESPONDENCE** (the central contract — exists).
- The **CROSSING_DECISION_BRIEFS / SECOND_ORDER docs** for B-min and A3
  (exist).
- An **intellectual-history chapter** placing him as the culmination of the
  formalization lineage, distinct in kind from the tributaries. *(✅ Written
  Sitting B2 — [THE_LINEAGE_AND_THE_TRIBUTARIES](../THE_LINEAGE_AND_THE_TRIBUTARIES.md),
  §2.)*
- A precise **"how to break it" page**: exact commands to run the core suite,
  the A3 gate, and a worked chain end-to-end. *(✅ Written Sitting B2 —
  GETTING_STARTED's logician door, "How to try to break it"; all three
  commands run and verified 2026-07-27 [132 + 15 + 21 tests passing];
  ARISBE_FOR_SCHOLARS points at it.)*
