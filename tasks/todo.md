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

## Item 2b — DONE (2026-09-21): EXTEND_LIGATURE now extends at any vertex

Found 2026-09-20 by the new oracle, on its first sweep — the same way MOVE_BRANCHES'
oracle paid for itself the moment it existed. **Ledgered, not fixed** (entry
`extend-ligature-wants-an-existing-ligature`, INCOMPLETE, 524 moves: tier A 336,
tier B 166, tier S 22).

**The defect.** Lemma 16.2 (p.172): *"Let a EGI 𝔊 be given with a vertex v. Let V' be a
set of fresh vertices and E' be a set of fresh edges ... placed in the context ctx(v)
... such that we have vΘv' for each v' ∈ V'."* The only precondition on the source is
that v be a vertex; every other clause governs what is **built**. Dau does not require v
to lie on an existing ligature — a lone vertex is a ligature of one.
`ExtendRestrictLigatureRule.check_preconditions` refuses with *"Selected vertex must be
on an existing ligature"*, declining half of an equivalence rule wherever the chosen
vertex carries no identity edge.

**The module already contradicts itself**, which is the strongest evidence for the
reading: the comment immediately above the offending block says *"No genericity condition
on the anchor: Def 24.10 (p.270) is explicit that the vertex an extension hangs from is
any `v ∈ V`"* — and then the next ten lines demand that v carry an identity edge. (Same
shape as `model_materialization`, which rendered a sheet line as a fixed individual in
its own output while its rule extraction called it a variable.)

**The fix.** Delete the `has_identity_connections` block,
`src/ligature_manipulation_rules.py` ~467-476. Ten lines.

**Why it is its own arc, not a drive-by.**
- [ ] `ligature_manipulation_rules.py` is protected → needs the author's authorization
      and `.core_modification_authorized`, removed afterwards.
- [ ] It converts **524 refusals into applications**, and newly-enabled ligature
      applications are exactly where this project's unsoundness has hidden before
      (MOVE_BRANCHES, caught only by an exhaustive soundness sweep at the end of an arc).
      So it needs its **own fresh exhaustive pass** (~2.5 h) to prove it changed no
      meaning — not the one that pins the oracles.
- [ ] Never start it while another measurement is in flight. Editing `src/` under a
      running pass makes that pass describe a tree that no longer exists; editing a
      JSON the suite reads at *runtime* (the ledger, the extent) corrupts the run
      outright. Both were learned the hard way on 2026-09-20.
- [x] **Proof of the fix is the ledger entry VANISHING**, not being edited.
      **It vanished**: the gate reported *"507 instance(s) no longer fail — shrink this
      entry"* — every instance — and the entry was deleted, taking the ledger 19 → 18.
      The extent diff reads exactly as predicted: `EXTEND_LIGATURE:refused/legal` → **0
      in all three tiers** with `applied/legal` up by the same +336 / +166 / +22 = **524**,
      totals conserved, and **no `applied/illegal` cell appeared** — the engine now
      applies what Lemma 16.2 licenses and nothing more. In the structure layer those 524
      moved from `refused` into `postcondition`, and every non-extent structure test
      passed, so the postconditions hold on all of them.

**What the fix was.** Deleting the `has_identity_connections` block was the whole change;
`apply_transformation` needed nothing, because it was *already* building two fresh
vertices and two fresh identity edges in `ctx(v)` — Lemma 16.2's construction verbatim.
The module's own comment had said the anchor is any `v ∈ V` all along.

**New:** `tests/test_chapter16_ligature_rules.py` — seven hand-built cases citing p.172
(a lone vertex extends; fresh material lands in `ctx(v)`, cut included; every fresh edge
is an identity edge; the anchor's ink survives; an already-ligatured vertex still
extends; an edge is refused; two anchors are refused). Shown to bite: **4 of 7 fail**
without the fix. Deliberately a new file rather than
`test_chapter16_17_ligature_soundness_simplified.py`, which is itself ledgered validation
theatre — repairing that one stays queued under item 1b.

## Item 5 — finding 3, CLIF/CGIF binder scoping — **FIXED 2026-09-21, UNCOMMITTED**

**⚠ IN-FLIGHT STATE (written down so it does not depend on conversation memory).**
The fix is made and locally verified; the full suite is the only thing outstanding
before commit. Uncommitted files: `src/clif_parser_dau.py`, `src/cgif_parser_dau.py`,
`tests/test_linear_form_binder_scoping.py`, plus this file. Neither parser is protected,
so no authorization was needed and none was raised.

**What was done.**
- **CLIF** — added `_binder_vertex` (name → the line its innermost enclosing binder
  introduced) and `_binder_count` (binder occurrences per name), plus `_open_binder` /
  `_close_binder`. This extends the save/restore discipline `exists` already had from
  *area only* to *identity and area*. Wired at three sites: the atomic branch, `exists`,
  and **both** `forall` paths — the delegating `if`/`not` path registered no binder at
  all, so a second `(forall (x) (if ...))` reused the first's line.
- **CGIF** — added `_bind_label` / `_label_count` and a scope push-pop on the negation
  branch, so a defining label scopes to its context **and its descendants**. Wired at
  seven sites.
- Both keep `v_{name}` for a name's **first** binder, so every corpus graph parses to
  exactly the ids it always did. That is why the round trips are untouched.
- **All 6 strict xfails converted to ordinary passing tests** in the same change, as the
  queued conditions required — a strict xfail left behind turns a fix into a failure.

**Verified locally:** `test_linear_form_binder_scoping.py` 6 passed; round-trip corpus
(`test_tomos_parsing`, `test_clif_unit`, `test_properties_round_trip`, `test_owl_import`,
`test_theory_query`) **226 passed, 0 failed**.

**A regression I introduced, and the strict xfail caught it.** Binding the `if`-bodied
`forall`'s *area* to the quantifier's own area dragged the line out to the sheet:
`(forall (x) (if (Cat x) (Animal x)))` came back as `*x ~[ (Cat x) ~[ (Animal x) ] ]` —
the **existential** reading of a universal. Fixed by binding the identity while leaving
the area to the body's structure and the least-common-area hoist. `_open_binder` takes
`area_id=None` for exactly that case, and says so.

**Still to do on this item.**
- [ ] Full suite + quality gate, then commit and push.
- [ ] Consider restoring `test_clif_imported_names_with_hyphens_do_not_break`'s fixture to
      its original reused-binder form. It was changed on 2026-09-19 (author's ruling) to
      route *around* this defect; with the parser correct it would again test the thing
      that used to break, and the comment there explains the history.

### The investigation that preceded it (blast radius, measured)

**The defect.** Both parsers key a generic vertex by the variable's *name*, so two binders
that reuse a name share one line. `(forall (x) (P x)) (forall (x) (Q x))` comes back as a
single existential line spanning both. Dau: a quantifier binds only the occurrences in its
own formula (Def 18.1, p.197; ∀ as ¬∃¬, p.198; α-conversion Def 18.3, p.199; Ψ's
existential step, p.207). Held by 6 strict xfails in
`tests/test_linear_form_binder_scoping.py`, so a fix shows up as XPASS and fails loudly.

**Now known to reach past the linear forms.** It was silently cancelling against the
materializer's quantification defect in a *passing* test
(`test_clif_imported_names_with_hyphens_do_not_break`): the parser merged two universals
into one sheet-level line, and the materializer then misread that line as a universal
variable, so two wrongs gave the right answer. Fixing one exposed the other.

**Exactly where.**
- `src/clif_parser_dau.py:524` (atomic branch) and `:665` (the ∀ branch) — `f"v_{name}"`
  with `if not any(v.id == vertex_id ...)`, so a second binder *finds and reuses* the
  first's vertex. `self._binder_area` is likewise a name→area map assuming one binder
  per name.
- `src/cgif_parser_dau.py:584` (defining label), `:602` (bound), `:623`, `:637-639` —
  same shape, plus a global `self._label_to_vertex_id`.

**The fix.** A lexical **scope stack**: entering a quantifier pushes a fresh vertex id per
bound name, leaving pops it, and an atom's argument resolves against the innermost
enclosing binding (else free/constant). That is Def 18.1 directly, and α-conversion falls
out of it.

**Blast radius, measured over all 245 stored corpus graphs (2026-09-21) — small.**
- [x] **CLIF: 0** graphs emit a reused binder name. Zero corpus exposure.
- [x] **CGIF: 18** graphs emit a repeated `*label`, but **all are same-scope
      coreference** — `[* x] [Human: *x] [Mortal: *x]`, one line with three coreferent
      mentions in one area, which is how CGIF writes coreference and which the scope-stack
      fix preserves by construction. None exhibits the defect's shape (two binders in
      disjoint scopes).
- [ ] Re-measure after the fix: the 147 round trips must hold at their stated split
      (144 `same_graph` + 3 by re-emission), and `KNOWN_BROKEN` must stay empty.

**Conditions.**
- [ ] Neither parser is protected (both were removed from the set 2026-06-27), so no
      authorization is needed — but the round-trip corpus is the thing to watch.
- [ ] The 6 strict xfails become XPASS. Convert them to ordinary passing tests in the same
      change; a strict xfail left in place turns a fix into a suite failure.
- [ ] Check whether `test_clif_imported_names_with_hyphens_do_not_break`'s fixture can go
      back to its original reused-binder form once the parser is right — it was changed on
      2026-09-19 to route around this defect, and the comment there says so.

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
