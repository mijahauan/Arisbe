# The nineteenth arc — the integrity review

**Authorized 2026-09-19.** The premise, in the author's words: the protected core was
believed to be something we could rely on, and recent review has shown that not
justifiable. The review is aimed at **how we test the core**, because that is where the
false confidence has been living.

**The governing observation.** The last three arcs did not mostly find bad code. They
found *tests whose silence was misread as evidence*:

- `test_tomos_parsing` pointed at a path that stopped existing when the corpus was
  renamed to `tomos`. Three tests skipped quietly while the round-trip guarantee was
  claimed in writing — unmeasured for as long as it had been asserted.
- Re-emission (`generate(parse(generate(g))) == generate(g)`) was counted into the same
  total as a `same_graph` round trip, though it is strictly weaker.
- Five implemented rules are `judged=False`: `legal()` abstains, so the refusal layer
  scores none of their moves. An unsound MOVE_BRANCHES sat in that gap for a whole arc.
- No default-mode graph exercised MOVE_BRANCHES positively, so every layer measured its
  refusals and nothing else.
- `calculus_apply` could not reach MERGE_VERTICES except through an already-ordered
  call, so a real hash-seed dependence lived where no counted record could see it. It
  was found by reading, not by measuring.
- And (2026-09-19) one Dau semantic rule — a line's area is its quantification — turned
  out to have **three** independent implementations, two of them named in no plan.

**"Protected core" is the same category error one level up**: a commit-time speed bump
read as a correctness guarantee. It has never tested anything. And its boundary is drawn
wrong in a demonstrable way — the quantification reading is a core Dau property living
entirely *outside* the protected set, while `has_dominating_nodes` sat **inverted
inside** it and nothing caught it.

**Standing rule for this arc (author, 2026-09-11):** remain Dau-compliant, test so that
this is ensured, stay vigilant for examples that stress the implementation. Nothing is
loosened — not an assertion, not a threshold, not a pin — and no entry is deleted to make
a suite green.

---

## Item 1 — Audit the written claims before the code

For every integrity claim the project makes in writing, name the test that measures it
and **prove that test can fail**.

- [x] **1a. The 220 skips.** *(in progress — first finding landed)* Zero unconditional
      `@pytest.mark.skip`; 65 runtime `pytest.skip(` calls audited. Two families checked
      clean (`test_domain_model_importer`'s corpus paths all exist; `test_presentation_ops`
      runs 40/40 with no skip). **FOUND:** in `test_corpus_polarity_discipline`,
      `test_discharges_cite_a_confirming_peel` was 19 parameters / 19 skipped / **0
      exercised** — the ⊥-door discipline documented in CLAUDE.md as part of the standing
      gate, measured by nothing. `episode_entertained` (0 inside) and `quotation` (0
      inside, 5 outside) sat in the same blind spot. Cause: the only carrier,
      `episode_discharge`, is categorised `theorem_proof` while the parametrization
      admitted `domain_model` only. FIXED by widening `_m_bearing_ids()` to any
      chain-bearing UoD that records an act, and closed as a *class* by the new
      `test_every_recorded_act_is_reachable_by_this_gate` (written red first).
      **Consequence:** widening exposed 3 real corpus defects — see 3d.
- [x] **1a-rest. All 220 skips attributed** (full `-rs` run, 46m47s). Four families:
      **(i) declared environment gates, 21** — Playwright 18, the `nl` extra 2, the `mcp`
      extra 1. Legitimate and reasoned.
      **(ii) chain-shape skips, ~90** — "static board with no chain" 24, "no discharge
      steps" 16, "no thin-spot survey steps" 15, "no branch survey steps" 15, "no TRACE
      steps" 15, "no declared audit-proposal" 11, "no PEEL steps" 9. **This is the family
      that can silently reach zero coverage**, and one member of it did. Now guarded for
      acts by `test_every_recorded_act_is_reachable_by_this_gate`; the *extent* is still
      thin and now measured — traces, thin-spot surveys and branch surveys each run on
      exactly **1 of 19** UoDs, peel verdicts on 7, audit proposals on 8.
      **(iii) per-UoD rule-site skips, ~100** — "no IT+ site accepted", "no ERA site
      accepted", "move_vertex refused every vertex", etc. Healthy in extent (IT+ skips on
      ~20 of 52, ERA on ~6), and each says which UoD and why. The real gap here is not
      extent but coverage: transformation invariance exists for only **3 of the 6 rules**
      (DC+, ERA, IT+) — no INS, IT− or DC−. Folded into item 2b.
      **(iv) quotation opacity, 13** — the B-min refusals, each asserted in its own
      dedicated test. Legitimate.
      **Verdict: no second instance of the `test_tomos_parsing` dead-path archetype.** The
      one real hole was the parametrization filter, not a stale path.
- [x] **1b. Vacuous assertions — DONE, and it is the arc's biggest finding.**
      **102 test functions suite-wide cannot fail**, verified by my own AST scan (a first
      pass said 172; that was wrong — it missed `unittest`-style `self.assertTrue`, which
      falsely condemned `test_rule_interaction.py`. 102 is corrected). **81 of them sit in
      one 12-file "PHASE N" block from a single commit, where 10 of the 12 files are
      wholly incapable of failing**: `except Exception: print(...)` swallows every
      assertion and a trailing `assert True` closes the file.
      **And 13 of the 152 tests in the CORE GATE cannot fail** — including all 9 of
      `test_chapter15_formal_calculus.py`, the file named for the chapter that defines the
      six transformation rules. The gate's own count (152) matches this scan exactly.
      Awaiting the author's steer on delete / repair / quarantine.
- [ ] **1b-old. Vacuous assertions.** Sweep for tests that cannot fail: `assert True`, a
      loop body never entered, an early `return`/`continue` guard that makes the
      assertion unreachable, a `try/except` that swallows the failure.
- [ ] **1c. Claim → test map.** Take the integrity claims in `CLAUDE.md` and
      `CURRENT_PLAN.md`, name the test that measures each, and flag every claim with no
      test or with a test weaker than the claim (the re-emission shape).
- [x] **1d (partial). Falsifier discipline.** The admission gate carries its own falsifier
      (`test_the_scan_catches_a_test_that_cannot_fail`, three shapes, plus two it must
      NOT flag), and both ledger halves were demonstrated to bite by planting and
      removing an entry. Extending this to the remaining layers is still open.
- [ ] **1d-rest. Falsifier discipline, the other layers.** For each layer/harness that reports "clean", confirm
      a demonstrated falsifier exists. The calculus suite already does this in places
      ("the instrument is shown to catch …"); extend it to the layers that lack one.

## Item 2 — No implemented rule unjudged; every rule positively exercised

- [ ] **2a.** Write `legal()` oracles for the five implemented rules that have none:
      EXTEND_LIGATURE (Lemma 16.2 p.172), RETRACT_LIGATURE (Lemma 16.3 p.173),
      REARRANGE_LIGATURE (Def 16.4 / Cor 16.5 p.174–175), SPLIT_VERTEX (Def 16.6 /
      Lemma 16.7 p.175–178), MERGE_VERTICES (Def 16.6 p.176).
- [ ] **2b.** Give every implemented rule at least one default-mode graph on which it
      **applies**, as tier S's `theta-in-one-context` did for MOVE_BRANCHES.
- [ ] **2c.** Make both of these standing tests, so a future rule cannot enter the
      engine unjudged or unexercised.

## Item 3 — One semantic rule, one implementation

- [x] **3e. INS routed through `insert_from_egif`** (2026-09-20, author-authorized,
      protected module). The engine path's own insertion inserted only ids prefixed
      `"new_vertex_"`/`"inserted_"`, so it returned success on an unchanged graph — and
      `POST /api/transform/apply` hit exactly that. Now one rule, one implementation: the
      canonical `rule_interaction.insert_from_egif` the protocol and the game engine
      already shared. A contentless INS refuses instead of no-op'ing. New
      `tests/test_transformation_routes.py` (the route had none); both new files shown to
      bite by reverting the fix.
- [x] **3d. The three quotation exemplars repaired** (author's ruling: repair the graphs,
      they were built not derived). `_residence` now uses `m_steps.admit_step`; the gate
      learned to replay both quotation flavours; all three remain `same_graph`.
- [ ] **3a.** Fix `dl_reasoning._sheet_denials`' area-blind `_keyv` (the third copy,
      found 2026-09-19 and deliberately left out of `b55323a`).
- [ ] **3b.** Collapse the three copies of the area/quantification reading onto a single
      home the others call.
- [ ] **3c.** Sweep for further duplicated semantic rules of the same kind.
- [ ] **3d.** *(found by 1a, awaiting the author's ruling)* The three quotation exemplars
      `swan_third_tense`, `forcing_forces` and `peirce_law_commentary` each carry a
      `step-2` INS that puts content into M with `act: None` — an unacknowledged
      M-change, which is exactly what the m_view tripwire exists to catch. They were
      invisible because the gate never ranged over them. `tools/build_quotation_exemplars
      ._residence` hand-rolls `pc.apply("INS", ...)` instead of using the recorded
      vocabulary (`m_steps.admit_step` → `act: m_enlargement`, `derivation: ["INS"]`).
      Corpus repair was the author's call last arc (Task 10), so it is his again.

## Item 4 — Redraw or rename "protected"

- [ ] **4a.** Decide the criterion: a module is protected only if a named suite pins its
      contract *and* that suite has passed item 1. Otherwise the label stops implying a
      guarantee.
- [ ] **4b.** Re-audit the 14-module set against whatever criterion item 4a settles —
      including the finding that a core Dau property lived outside it in three copies.
      **This one is the author's ruling, not the arc's.**

---

## Review

*(filled in as items close)*
