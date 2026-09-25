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
- [~] **1c. Claim → test map — CLAUSE 3, first pass done 2026-09-21.** Time-boxed to the
      load-bearing claims (the calculus, Def 12.5, the correspondence check, the round
      trips, the calculus map), as the handoff directed. Method: three parallel read-only
      audits, each finding reproduced in the main session before it was acted on
      (standing caution 5). **Nine findings; seven closed by a test, two recorded.**

      **Contradictions fixed.**
      - `CLAUDE.md` said the CLIF/CGIF binder defect was "live and pinned, not fixed
        (6 strict xfails)" forty lines above its own entry saying "**FIXED** 2026-09-21".
        The file passes 6/6, no xfails. Prose corrected; both halves now agree.
      - `CLAUDE.md` said "Six more are correctly refused as the second-order limit". It is
        **nine** (3 UoDs × 3 forms), and `test_tomos_parsing`'s own extent pin has
        asserted 9 all along. Standing caution 8, in the file that states it.
      - `test_calculus_enum.test_every_corpus_graph_is_an_egi`'s docstring justified itself
        by "the core does not enforce it and its own check is inverted". Both halves were
        true when written and **both are now false** (`9482d2c`, `d20b700`). Consequence,
        now written down: tier-B graphs arrive through the core constructor, so a stored
        non-EGI raises at *load* and this test's legible failure path is unreachable. Kept
        — it still proves the corpus loadable and pins `sources` at 230 — but honestly
        labelled. Same for `test_every_kept_graph_has_dominating_nodes`, whose comment
        "the core would not refuse one" is refuted thirty lines above it by
        `TierAReport.refused_by_core`, which exists to count that very refusal.

      **Claims that were true and unmeasured — now measured.**
      - **The round-trip split.** The extent pin held `(total, second_order, broken,
        holding)`; `BY_REEMISSION` was in none of them. Moving a UoD into that set
        downgrades it from `same_graph` to the strictly weaker re-emission check **with
        every pin still green** and the headline still "147". This is the exact defect
        class the arc already caught once. New
        `test_the_split_between_the_strong_and_weak_checks_is_pinned_too` holds the set by
        *name* and 144/3 as a pair. Shown to bite: with a UoD quietly downgraded, the old
        pin passes and the new one fails — the gap demonstrated in one run.
      - **"EGI is immutable."** The first Data Model Invariant in `CLAUDE.md`, and the
        calculus map attests `egi_core_dau.py` as "**the immutable EGI** …" naming
        `test_second_order_core.py` — which contained no immutability assertion. The only
        `FrozenInstanceError` in the whole suite was in `test_c_marks.py`, on an unrelated
        class. Dropping `frozen=True` would have reddened nothing *for that reason*. New
        `TestImmutability` (3): frozen dataclass, `frozenset`/`frozendict` insides (a
        frozen shell around mutable insides is immutability in name), and `with_*` leaves
        the original alone. The attestation is now true.
      - **"166 core tests, 1 of which cannot fail."** Both figures correct, both prose
        only — the shape that let "~118" stand against a real 166. New
        `test_the_core_gates_figures_are_derived_not_narrated` parses
        `tools/quality_gate_system.py`'s own `core_test_files` list (never re-typed), runs
        it, scans it, and pins both. The second figure is the load-bearing one: ten
        unfailable tests once sat inside the core gate.
      - **"`admission_scan` imports nothing from `src/`."** True, unguarded. The exact
        analogue — `test_calculus_legal.test_legal_never_consults_the_engine` — existed
        for `legal()` but had not been applied to the newer instrument. Now it has.

      **Mechanisms weaker than the claim — strengthened.**
      - **The calculus map's "the suite reaches the module"** was a regex over source
        *text*. Verified forgeable four ways: a comment, a docstring, a commented-out
        import and a string literal all read as imports. Now an AST parse. No verdict
        changed on any of the 16 real module→suite pairs — it closes what the check would
        let through.

      **THE ONE THAT MATTERS MOST: the suite's documented "one real failure" had gone
      silent while the defect stayed live.** `CLAUDE.md`'s Testing section opens by saying
      the 2026-09-18 run "also had **1 failure, and it is a real defect, not a threshold**:
      `test_egif_generate_is_idempotent_on_regenerated_output`". That test now **passes**,
      and the defect it names is **entirely unfixed** — parsing and generating
      `(P *u) (P *v) ~[ (Loves v *y) (Loves u *x) ]` 200 times in one process still yields
      two distinct texts (measured today: 102/98). The last full-suite run noticed nothing:
      its only failure was the unrelated `test_memory_stability`.
      **Why it went quiet, and it was structural, not luck.** The property test searches
      `egif_sheet(max_atoms=3, max_cut_depth=1)`; the falsifying input has **four** atoms,
      so that strategy *cannot generate it and never could*. It was only ever reported
      because Hypothesis held the example in the machine-local `.hypothesis` database —
      which `CLAUDE.md` knew and wrote down as the mitigation ("do not delete that entry —
      it is the only thing keeping the defect visible"). That database now has no examples
      directory. A defect whose visibility depends on a gitignored cache is a defect nobody
      is keeping, and this was standing rule 4 suspended in writing, in the file that
      states it.
      **Closed** by `test_egif_generation_is_deterministic_on_symmetric_lines` — hand-built,
      deterministic in its detection, a **strict xfail** (this project's idiom for a live
      defect; cf. the binder-scoping six, which caught both the fix landing and a
      regression it introduced). Stable across three runs. When the tie-break is fixed it
      XPASSes and fails loudly, instead of going green in silence the way its predecessor
      went red in silence. **The underlying defect remains the author's call** (it is the
      alphabet/tie-break question already open from the eighteenth arc) — this changes only
      whether the project can tell.

      **The per-file test counts in `CLAUDE.md`, swept mechanically — 4 of 9 were wrong.**
      Every `(N)` figure quoted beside a test filename, compared against collection:
      `test_second_order_core` 27→**30** (before my 3, now 33), `test_rules_second_order`
      18→**20**, `test_world_scroll` 45→**52**, `test_m_steps` 31→**25**. The last is the
      instructive one: that file holds 25 `def test_` and has **not been touched since the
      commit that wrote "31"**, so the figure was never true — not drift, just never
      checked. (`test_second_order_reader` 12, `test_second_order_conservativity` 15,
      `test_use_mention_fork` 6, `test_calculus_map` 9 and `test_chapter15_formal_calculus`
      23 all hold.) Corrected in place.

      **The correspondence check (§3.3) and the six §7 shapes — the central contract.**
      - **`test_regime3_identity_null_op` asserted that an object equals itself.**
        `egi_before = uod.current_egi` … `egi_after = uod.current_egi`: one attribute read
        twice off one immutable object, 52 UoDs per engine/style, docstring conceding
        "trivially true" while claiming to give the other three regime-3 tests "a
        known-good baseline" — which is precisely what comparing a thing to itself cannot
        give. It now loads a **second, independent** copy and asserts the two are not the
        same object. Worse, and the reason this mattered: **`_structurally_equal_egi`, the
        helper all four of shape 6's tests decide by, had no falsifier at all** — stubbed
        to `return True, []` it would have turned the whole shape green. It has one now
        (three arms: agrees with a graph about itself, rejects a different graph, and
        catches a ρ-only rename built with `dataclasses.replace` so exactly one field
        moves). *A caution for whoever reads this:* my first draft of that falsifier
        guarded an arm with `hasattr(base, "with_rel_name")` — a method that does not
        exist, so the arm silently never ran. I caught it by checking. It is the same
        shape as everything else in this list and it took ten minutes to reproduce inside
        the very audit that hunts it.
      - **S3 — the prose said the opposite of a test.** `CLAUDE.md` read "**S3 CHECKED** on
        `swan_third_tense`/`forcing_forces`" while `test_quotation_overlay
        .test_s3_is_skip_named_never_silently_passed` asserts `read_back_faithful is None`
        and "S3" among the honest limits, *for `swan_third_tense`*. S3 is genuinely checked
        end-to-end with six biting falsifiers — on a **synthetic fixture** in
        `test_second_order_reader.py`. Prose corrected. Related and also corrected:
        **`attest_served_quotations` is referenced by zero tests**, so deleting both of its
        `layout_service` call sites would redden nothing, and S1–S3 do not fire at the
        `tomos_service` save/load boundary at all (only §3.3 does).

      **Recorded, not closed** (judgment calls, not oversights):
      - **§3.3's identity-connectedness half has no independent failure mode.** Verified
        here by probe: whenever `identity-connected` fires, `identity-endpoint` has already
        fired on the same path; and a path that teleports in from 5,000 units away while
        ending correctly at the vertex is **accepted**. Given the endpoint check forces
        every path to terminate at the vertex position, and a polyline is connected through
        its own consecutive points, the "disconnected paths" branch cannot be reached
        alone. *Correction worth recording:* my own first probe reported that §3.3 accepts
        a ligature path displaced 9,999 units, which would have been far worse. It was
        wrong — the engine **aliases** `vertex_positions[vid]` and `path.points[-1]` to one
        `Point` object, so `pt.x += …` moved both and kept them equal. With fresh point
        objects the endpoint check fires correctly. The aliasing is itself worth a thought:
        on engine-produced DTOs that check compares an object with itself, so it bites only
        on doctored or freeform ink — which is its job, but not what a reader would assume.
        `correspondence_attestation.py` is on the calculus map, so this is the author's.
      - **Three §3.3 properties have no falsifier**: `incidence:`, `arg-order:` and
        `identity-connected:` are asserted by no test in the repo, against `CLAUDE.md`'s
        "adversarial unit tests confirming **each** §3.3 property's failure raises". The
        first two **do** bite when doctored (verified), so these are cheap tests somebody
        should write; the third is the item above.
      - **Shape 2 (transformation invariance) covers 3 of 6 rules** — DC+, ERA, IT+ only.
        No test in the repository pairs INS, IT− or DC− with a correspondence check, though
        §7 says "for every rule applied to every applicable site". IT+ reaches only 29 of
        52 UoDs. (The eighteenth arc's note estimated ~100 rule-site skips; measured, it is
        57 plus 28 regime-3.)
      - **Shape 1 is not the test §7 defines.** §7 shape 1 is render → serialize → re-parse
        → structural equality. `test_render_round_trip_totality_and_injectivity` compares
        DTO key sets against element ids — that is §3.3's totality/injectivity row. The
        real round trip (`reading_matches_egi(read_drawing(dto), egi)`) lives in
        `test_eg_reader.py`, a different file than `CLAUDE.md` credits.
      - **"Every served (EGI, drawing) pair is verified" is not true of every path.** The
        deltas path calls `rebuild_ligature_anchors` *after* the last attestation and the
        following `place_clockwise_hooks` swallows `CorrespondenceViolation` with a bare
        `pass`; `GET /api/diagram/session/{id}` and `POST /api/transform/{undo,redo}` serve
        a session-stored DTO with no re-attestation; `generate_overview_layout` attests the
        quotient, and its own docstring says that is not a full §3.3 check. All in `src/`,
        so recorded for the author rather than changed under a time-box.
      - **A question for the author.** Four of nine narrated counts being wrong argues for
        pinning them the way every other extent in this project is pinned — a test that
        parses `CLAUDE.md`'s `(N)` claims and checks them against collection, failing with
        "read why this moved, then re-pin deliberately". I did **not** build it: it would
        make every added test red the suite until the doc is updated, and that is a change
        to the working rhythm, which is the author's call and not a subagent-shaped one.
      - The map's "says *what* it pins" conjunct is measured as a **non-empty string**.
        Replacing every description with `"x"` keeps the file green. Checking prose against
        substance is clause 3 again, one level down, and wants its own thinking.
      - `has_dominating_nodes` now has **no negative case anywhere in the suite** — not
        unmeasured but *unmeasurable*, since `d20b700` means no non-EGI can be constructed
        to test it against. A helper hard-wired to return `True` would pass everything.
- [x] **1d. Falsifier discipline — the admission gate's own halves, CLOSED 2026-09-21.**
      This entry used to end: *"both ledger halves were demonstrated to bite by planting
      and removing an entry."* That demonstration was **manual, and left nothing behind**
      — a falsifier that lives only in prose is a falsifier nobody is keeping, which is
      standing rule 4 turned on the instrument that enforces it. Clause 3 caught it: the
      newest instrument in the project had **zero** falsifiers for its two ledger halves,
      while `test_calculus_ledger.py` — the idiom `test_admission.py`'s own docstring says
      it copies — has carried seven for the same shape since it was written. So the
      semantics were copied and the verification was not.
      Closed by making the comparison the *same code* the gate runs rather than a
      re-written copy: `admission_scan.new_against_ledger` /
      `repaired_against_ledger` (they were inline one-liners inside the two gate tests,
      which is precisely why neither could be exercised), plus three tests — each half
      shown to speak, and both shown to fall silent when the ledger matches the scan, so a
      half hard-wired to report everything cannot pass.
      `test_the_scan_catches_a_test_that_cannot_fail` remains, and is a different guard:
      it falsifies the **scanner**, not the ledger comparison.
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

## Item 8 — The two unattested calculus modules — **DONE 2026-09-21**

The handoff's item 3. `UNATTESTED` is now **empty**, emptied the only way the rule allows: by
giving each module a suite, never by deleting a name.

- [x] **8a. `hierarchical_index.py` → `tests/test_hierarchical_index.py` (24).**
      **It is load-bearing for soundness, which was not obvious and is now written down.**
      Every EGI builds one in `__post_init__`; `egi_core_dau.area_polarity` reads its levels and
      returns POSITIVE iff even (Dau Def 12.4) **with no cross-check** — the fallback fires only
      when the level is `None`, never when it is *wrong*. Measured before writing the suite:
      bumping one level on `(P *x) ~[ (Q x) ]` turns the cut from `(NEGATIVE, 1)` to
      `(POSITIVE, 2)`, and ERA and INS licensing invert in silence.
      Pinned against an index-free oracle (`calculus_enum.ancestors`/`all_areas`) over 341
      graphs / 1,267 areas — levels, chains, completeness — plus `NestingInfo.polarity` held in
      step with `area_polarity` (one convention written in two files, previously unheld), and
      **the staleness invariant**: `hierarchical_index` is a dataclass *field*, so
      `dataclasses.replace(egi, area=…)` carries a stale index and nothing raises. The `with_*`
      constructors rebuild only because they call the constructor rather than `replace` — now
      pinned, since that is exactly the fact a refactor erases. **Shown to bite: one extra level
      of nesting fails 6 of 24.**
- [x] **8b. `single_object_ligature_detector.py` → its own file (13).** Dau **Def 16.8** (p.180),
      quoted verbatim in the docstring. The condition worth the most is the one Dau states
      explicitly and a reimplementation would most likely break — *a single-object ligature may
      contain cycles, as long as the whole cycle sits in one context* — so a flat cycle is
      **accepted**; reading condition 3 as "no cycles" is the likely error. And `<` is the
      context tree's **partial order**, not a depth comparison: two vertices in different
      branches are incomparable however different their depths. **Shown to bite:** replacing
      `_is_context_deeper` with `level(a) > level(b)` fails exactly that test, and it is the only
      test in the repository that would notice.
      Assertions deliberately avoid message counts, exact text and `cycles` — all follow
      set-iteration order under per-process string hashing. *(The recon reported the count
      varying 1–3 across processes; on my fixtures it was stable across 8 fresh runs, so I did
      not pin someone else's unreproduced observation — I pinned only what the module is for,
      the verdict, and wrote down why.)*
- [x] **8c. A trap closed on the way.** `test_an_unattested_module_is_still_reachable_from_src`
      was parametrized over `UNATTESTED`. Emptying that set would have left it ranging over
      nothing — and pytest reports an empty parameter set as a **skip**, so the check would have
      gone quiet at the exact moment its subject disappeared. That is the
      `test_discharges_cite_a_confirming_peel` archetype (19 parameters, 19 skipped) repeating
      inside the file that exists to prevent it. Widened to the whole map: strictly stronger,
      cannot empty, all 14 verified reachable, with a companion test pinning that the
      parametrization still covers every module.

**Recorded, not repaired — and queued below as 6j/6k.** Both modules carry real gaps. They are
pinned as *current behaviour* so the state is written down and a fix is visible as a change;
repairing an uncalled method is a change with no beneficiary and some risk, while leaving it
undescribed is how a landmine stays a landmine.

---

## Item 7 — The 62 ledgered validation-theatre tests — **DONE 2026-09-21**

The handoff's item 2. The debt itself is **bounded historical, not a live leak**: one dated
deposit, all 11 files added 2025-09-19 in "PHASE N COMPLETE" commits, nothing inadmissible
added since. The author's ruling is that they keep their value as **exhibits of the shape** and
so are recorded rather than deleted. Two live consequences remained, and both are now closed.

- [x] **7a. The ruling had no enforcement — and the disposal it forbids was the one that
      looked like success.** The shrink half computed `set(ledger) - set(found)`, and a
      **deleted** test is not found either, so deleting an exhibit reported as *"can now fail
      — shrink this entry"*: indistinguishable from repairing it. Demonstrated, then closed by
      a presence oracle (`admission_scan.all_test_ids`, the same AST walk and id spelling) and
      a split into `repaired_against_ledger(..., present)` and `removed_against_ledger`. The
      two now say different things, with a falsifier pinning that they do — and pinning that
      the old conflating behaviour is what you get if the oracle is omitted.
      *Incidental confirmation:* the new removal guard passes against the real ledger, which
      also proves `all_test_ids` spells ids exactly as the ledger does — had it not, all 63
      would have read as removed.
- [x] **7b. A third quiet route, found while measuring 7a.** A test can stay in the source yet
      stop being **collected** — a class renamed off `Test*`, a file moved under
      `norecursedirs`. It is then present and inadmissible, so both halves stay silent while
      it contributes nothing to any run. Now required to appear in a real collection.
      *An exhibit nobody runs is not an exhibit.*
- [x] **7c. The inflation of every "N passing" figure, stated as a split.** The ledger's own
      README named this and nothing acted on it. This project already has the rule — the round
      trips are never quoted as a total, only "144 by `same_graph`, 3 by re-emission", with
      "always state the split" in writing — so it is applied here: the suite headline is now
      **"5,098 passing, of which 63 cannot fail"**. Measured exactly: all 63 ledgered
      functions collect to exactly one item each (63 of the 95 items in those 11 files), so
      the subtraction is honest. Derived, not narrated.
- [x] **7d. The ledger README rewritten** to name the three routes (REPAIRED / REMOVED /
      UNCOLLECTED) and the split rule. Entries untouched — only `_README` changed.

**Not done, deliberately:** nothing was repaired or deleted. Rewriting 62 tests that were
never real tests is a different job from this arc's, and the author's ruling is that their
value is as exhibits. What changed is that the record can now tell what happens to them.

---

## Item 6 — THE CLAUSE-3 DOCKET (opened 2026-09-21, fourth sitting)

Everything clause 3 found and **deliberately did not change**, promoted out of item 1c's prose
into a docket so it is tracked rather than buried in a closed item. All of these are in `src/`
or on the calculus map, which is why the audit recorded them instead of acting: the convention
is to confirm with the author before changing the calculus.

**Ordered by what I would take first, with the reasoning.** The first two are cheap and
purely additive (new tests, no `src/` change) and would close written claims that are
currently false as written. The rest need a ruling because they change behaviour or scope.

- [x] **6a. DONE 2026-09-22 — two §3.3 falsifiers, both shown to fire on real corpus ink.**
      `test_attest_raises_when_a_predicate_loses_an_argument` (drop one of a binary
      predicate's two lines → `incidence: … arity mismatch`) and
      `test_attest_raises_when_two_arguments_are_drawn_in_the_wrong_order` (swap two
      `port_index` values → `arg-order: …`). The second is the row that makes a drawing a
      *proposition* rather than a diagram of one: everything else is intact and the picture
      now says `(Loves b a)`. Original note follows.
      `CLAUDE.md` claims "adversarial unit tests confirming **each** §3.3 property's failure
      raises `CorrespondenceViolation`". Three properties have none: `incidence:`,
      `arg-order:`, `identity-connected:`. The first two **do** fire when a DTO is doctored —
      confirmed by probe: dropping one of a binary predicate's two ligature paths gives
      *"incidence: predicate e_… arity mismatch — ν says 2, DTO has 1"*, and swapping two
      `port_index` values gives *"arg-order: … sorted vertex sequence ≠ ν"*. Writing those two
      tests is additive, needs no ruling, and makes the sentence true. **Do this one first.**
- [x] **6b. DONE 2026-09-22 — the hook now has three tests.** It fires on the real serve
      path (spied through `layout_service.generate_layout` on `swan_third_tense`), it has
      teeth (an oval served with a `solid` stroke instead of the committed `quotation` one
      is refused), and it is a no-op on a first-order pair. *A guard caught my own wrong
      assumption while writing it:* I asserted the committed stroke was `"dotted"`; it is
      `"quotation"`, and the assertion said so instead of silently testing nothing.
      Original note follows. It is called at two `layout_service`
      boundary sites and referenced by **zero** tests — deleting both calls would redden
      nothing. Additive; the fixture pattern already exists in `test_second_order_reader.py`.
      Consider also pinning S3 on `swan_third_tense`/`forcing_forces` **or** correcting the
      claim further — note that `test_quotation_overlay` currently asserts S3 is *skip-named*
      on `swan_third_tense`, so these two would contradict unless the skip is retired
      deliberately.

> **Process note, learned the hard way on 6c (2026-09-22).** `.core_modification_authorized`
> comes down **after the change is committed**, not after it is written. The pause reads
> `git diff HEAD` plus the index, so an uncommitted edit to a map module with the marker
> already removed is a VIOLATION and the quality gate fails — which is what happened here,
> and is the pause doing its job. CLAUDE.md's "remove it after" means after the commit.

- [x] **6c. RULED + DONE 2026-09-22 — retired; identity is two checks.** The author's
      ruling: remove the unreachable branch rather than keep a check that looked like
      enforcement and was not. `correspondence_attestation.py` is on the calculus map, so
      `.core_modification_authorized` was raised for the change and removed after. The
      spec's §3.3 table and its commentary now say **two** checks — endpoint placement and
      the crossing multiset — and name what the third was and why it went. Nothing that was
      being enforced was lost. Original note follows.
      **Needs a ruling — it is a calculus-map module.** Verified: whenever
      `identity-connected` fires, `identity-endpoint` has already fired on the same path, and
      a path that teleports in from 5,000 units away while *ending* correctly at the vertex is
      **accepted**. Given the endpoint check forces every path to terminate at the vertex
      position, and a polyline is connected through its own consecutive points, the
      "disconnected paths" branch is unreachable alone. The doc calls this row load-bearing.
      Two ways out: strengthen the check to mean something independent (what *should* it
      forbid that endpoint placement does not?), or retire it and say the identity row is two
      checks, not three. Either is honest; leaving it is not.
      *Rider, same module:* the engine **aliases** `vertex_positions[vid]` and
      `path.points[-1]` to one `Point` object, so on engine-produced DTOs the endpoint check
      compares an object with itself. It bites only on doctored or freeform ink — which is its
      job, but not what a reader of the claim would assume, and it is why my first probe
      misread the check as broken.

- [x] **6d. RULED + DONE 2026-09-22 — extended to all six rules.** New
      `test_transformation_invariance_ins` / `_dc_minus` / `_deiteration`, each applying the
      rule and re-checking §3.3 on the post-state's drawing. Corpus site availability,
      measured first: **INS 42 of 52 UoDs, DC- 8 (7 apply; `swan_third_tense` correctly
      refused — a quotation oval is not a negation), IT- 1** (a deiteration needs an
      iterated copy and the corpus mostly has none). 50 pass, 106 skip, every skip naming
      its UoD. Each carries a did-it-actually-happen assertion (INS adds ink, DC- removes
      both cuts, IT- removes ink) — the silent-no-op archetype that reached the web API.
      Original note follows. DC+, ERA, IT+ only. **No test in
      the repository pairs INS, IT− or DC− with a correspondence check**, though §7 says "for
      every rule applied to every applicable site". IT+ reaches only 29 of 52 UoDs. Either
      extend the suite to the missing three, or amend §7 and `CLAUDE.md` to state the real
      extent. (Measured rule-site skips: 57, plus 28 regime-3 — the eighteenth arc's "~100"
      estimate was high.)
- [x] **6e. DONE 2026-09-22 — the credit corrected.** The test's own docstring was already
      honest ("§3.3 Totality, Injectivity"); `CLAUDE.md`'s summary was not. It now states
      the real extent and points at `test_eg_reader.py`, where the genuine
      render→read→`reading_matches_egi` round trip actually lives. Original note follows. §7 shape 1 is render → serialize → re-parse
      → structural equality against the source EGI. What runs under that name in
      `test_correspondence_invariant` compares DTO key sets to element ids — that is §3.3's
      totality/injectivity row. The genuine round trip
      (`reading_matches_egi(read_drawing(dto), egi)`) lives in `test_eg_reader.py`, a
      different file than `CLAUDE.md` credits. Decide whether shape 1 moves, is renamed, or
      the credit is corrected.
- [x] **6f. RULED + PARTLY DONE 2026-09-22 — the deltas path fixed; the other two recorded.**
      The author chose the narrow fix. `rebuild_ligature_anchors` now re-attests, falling
      back to the `apply_deltas`-attested layout on failure — which also makes the
      clockwise block's `except CorrespondenceViolation: pass` sound, since everything it
      can fall back to is now attested. `test_the_deltas_path_never_serves_unattested_geometry`
      compares **geometry, not object identity** (the last two pipeline steps return fresh
      DTOs by design and are annotation-only). It carries a second, deterministic assertion
      because the geometric one only bites when the rebuild actually moves something —
      which is why the defect survived. **Shown to bite by reverting the fix in the source.**
      STILL OPEN: `GET /api/diagram/session/{id}` and `POST /api/transform/{undo,redo}`
      serve stored DTOs unre-attested, and `generate_overview_layout` attests the quotient.
      Original note follows.
      Three gaps, in descending severity: (i) the **deltas path** calls
      `rebuild_ligature_anchors` — a geometry change — *after* the last attestation, and the
      following `place_clockwise_hooks` swallows `CorrespondenceViolation` with a bare
      `pass`, so the returned DTO can be one that was never attested (observed on 2 of 5 runs
      of one fixture; in all five it still satisfied the check, so this is an **unverified
      serve, not a live violation**); (ii) `GET /api/diagram/session/{id}` and
      `POST /api/transform/{undo,redo}` render a session-stored DTO with no re-attestation —
      stale-attested, so a mutation in the session store would not be caught; (iii)
      `generate_overview_layout` attests the collapsed quotient plus `attest_overview`, and
      its own docstring says that is not a full §3.3 correspondence — the flat sentence in
      `CLAUDE.md` hides that.
- [x] **6g. DONE 2026-09-22 — a description must now name something real.** It was
      `assert what.strip()`, so replacing every description with `"x"` kept the file green.
      The check now requires each to name a **symbol defined in the module** or carry a
      **Dau citation**; nine of the fourteen were rewritten to satisfy it. Honest about what
      it is: not a validation of substance (nothing mechanical reads whether the sentence is
      *true* of the suite — that stays a reading task), but a description can no longer be a
      placeholder, be copied from a neighbour, or survive the symbol it names being renamed
      away. Shown to bite on `"x"`. Original note follows.
      Replacing every module's description with `"x"` keeps `test_calculus_map` green. Checking
      prose against substance is clause 3 one level down and wants its own thinking — the
      reachable version is probably "the description names at least one Dau citation or one
      test in the named suite", not free-text validation.
- [x] **6h. DONE 2026-09-22 — it has one now.** Built below the constructor, the seam
      `test_parsers_place_vertices_before_edges` already uses: suppress
      `_validate_dau_constraints`, build the violator (edge on the sheet, its vertex in a
      cut), and ask the helper directly. It answers `False`, and the Dau oracle agrees. This
      matters because the helper was found **inverted** once already. Original note follows. — not
      unmeasured but *unmeasurable*, since `d20b700` means no non-EGI can be constructed to
      test it against. A helper hard-wired to `return True` would pass everything. If it is
      worth pinning, the test has to build the violator **below** the constructor (the
      instrument in `test_parsers_place_vertices_before_edges` does exactly this by
      monkeypatching `_validate_dau_constraints`, and is the model to copy).
- [x] **6l. SOLVED 2026-09-22 (fifth sitting) — and nothing was ever miscounted. The
      instrument was wrong, and the suite has no fixed size.** Both figures are exactly
      right; what did not exist was a term for the tests that are reported without being
      collected, and a name for the gate that decides how many tests there are at all.
      **The mechanism, proved with a controlled fixture rather than inferred:**
      `pytest --collect-only -q` prints the number of collected items and says **nothing**
      about a module that skipped at import. Such a module contributes **no collected item**
      and **one `skipped` outcome** — a two-test fixture beside one gated module collects
      "2 tests" and runs "2 passed, 1 skipped". So the identity is
      `outcomes == selected items + module-level skips`, where *outcomes* sums the buckets
      pytest reports for something it tried (passed/failed/skipped/xfailed/xpassed/errors)
      and excludes *deselected* and *warnings*, which are not outcomes.
      **Both terms move with one environment gate**, which is the finding worth carrying:
      the thirteen `*_e2e.py` modules go through `tests/e2e_support.require_browser`, and
      with a launchable chromium they collect **exactly 66 items** and skip nothing, while
      without one those 66 tests **do not exist** and 13 module skips stand in their place
      (66 measured directly, by satisfying the guard). The two figures in this entry were
      taken on opposite sides of that gate:
      - HEAD: 5,493 collected + 13 module skips = **5,506** — the reported summary exactly.
      - `e7d48a6`: 5,330 collected + **66** e2e items = **5,396** — the reported summary
        exactly, on a tree whose run had a browser.
      Not arithmetic luck: solving the two runs' *independent* passed/skipped deltas forces
      the e2e contribution to be 66, which is the measured 66. And the `+156` in that
      per-file diff is `test_correspondence_invariant.py` (937→ 1093), the 6d rules mostly
      skipping at inapplicable sites — which is what carried skipped +101 against passed +9.
      **Built:** `tools/suite_census.py` computes both terms from one ~5-second collection
      pass (against the suite's 52 minutes), names the gate and which side of it this machine
      is on, and with `--against <run.log>` reconciles a real run and **exits non-zero** when
      it does not add up. `tests/test_suite_census.py` pins the identity the only way a claim
      about pytest's reporting can be pinned — by running real pytest over one throwaway
      suite per shape (plain, module-skip, deselected, xfail/xpass/runtime-skip) and comparing
      the derived total against the summary pytest actually prints — so a future pytest that
      changes its reporting reddens on the day it happens. Shown to bite twice: dropping the
      module-skip term fails 3 tests (the exact 6l defect), and planting a module that stops
      being collected fails `test_no_test_module_goes_uncounted` (the third quiet route item 7
      named). It also pins the identity's **one known exception** — a test that fails and then
      errors in teardown is reported in two buckets, so the sum exceeds the item count
      honestly; an identity trusted past its domain is worse than no identity.
      **The correction stands:** the previous commit's "the arithmetic closes exactly" was
      stated more confidently than the evidence supported. It now closes, and is checkable.
      Original diagnosis follows.
      **6l (original). THE SUITE'S OWN HEADLINE DOES NOT RECONCILE AGAINST COLLECTION — found
      2026-09-22 while verifying 6a–6i, and it is the same shape as everything else here.**
      The full-suite figure this project quotes is a **summary line nobody checks against
      the number of tests that exist**. Measured:
      - At `e7d48a6`, `pytest --collect-only` reports **5,330 selected** (5,340 − 10
        deselected), confirmed in a clean detached worktree at that exact commit.
      - The full run on that same tree reported **5,396 outcomes** (5,152 passed + 241
        skipped + 1 failed + 2 xfailed) — **66 more outcomes than there are tests**.
      - This run: collection **5,493**, progress characters **5,493** (they agree), but the
        summary line says **5,506** — 13 more, which module-level skips would explain,
        since those are counted in the summary and emit no progress character.
      So the discrepancy is real, is **not** something this sitting introduced, and is of
      two different sizes in two consecutive runs. **What is NOT in doubt** (and is why the
      work below was still committed): a per-file collection diff between `e7d48a6` and now
      shows **only the five files this sitting touched**, changed by exactly +1/+2/+156/+1/+3
      = **+163**, with every other file byte-identical in count — so nothing was lost — and
      the only failure is the documented `test_memory_stability` flake.
      **Consequence to face squarely:** the previous commit's message claims "+54 against
      the previous run, every one attributable" and "the arithmetic closes exactly". Given
      this, that claim was **stated more confidently than the evidence supported** — the
      per-file delta was right, the cross-run summary reconciliation was not checked against
      collection at all. The fix is not to re-narrate it but to make the headline derivable:
      pin `collected == passed + skipped + failed + xfailed − module_level_skips`, or stop
      quoting a total that nothing reconciles. This is 6i's lesson one level up, on the
      project's single most-quoted figure.
- [ ] **6j. `hierarchical_index`'s dead half — three real defects, pinned as behaviour.**
      Nine public methods have no caller in `src/`. `get_children` returns **the live internal
      set**, so `hi.get_children(sheet).add(x)` corrupts the index in place. `remove_area`
      **orphans descendants** — after removing a middle cut, its child survives claiming a
      parent that is gone and its ancestor chain never reaches the sheet. `validate_containment`
      compares **depth, not ancestry**, so two unrelated branches validate. All three are pinned
      in `TestTheDeadHalfIsRecordedNotTrusted`; fixing any is a behaviour change and wants a
      ruling. Also: `NestingInfo` is `frozen=True` but holds a mutable `set`, so it is
      unhashable and its contents are mutable through any returned reference.
- [ ] **6k. `single_object_ligature_detector`'s three gaps.** Parallel identity edges are
      **invisible to cycle detection** (adjacency is a `set`, so a second `=` edge between the
      same pair collapses onto the first — under Def 16.8 that *is* a cycle in (W, F));
      **unknown vertex ids pass silently** (no check that W ⊆ V; an empty ligature passes too);
      and `separate_into_single_object_components` is **a stub** returning one singleton per
      vertex whatever the graph, with no caller. Low urgency — nothing in the production path
      constructs the evaluator that reads this module — but the day something does, Def 16.8 is
      what it will be trusting.
- [x] **6i. RULED + DONE 2026-09-22 — the counts are gone from the doc.** The author chose
      neither hand-policing nor a pinning test but removing the class of figure: `CLAUDE.md`
      no longer quotes per-file test counts, and says why. Seven were dropped; the two
      remaining numeric parentheticals were reworded. Original note follows. Four of nine narrated per-file test counts in
      `CLAUDE.md` were wrong, one never true. That argues for pinning them as every other
      extent here is pinned — a test parsing the `(N)` claims and checking them against
      collection, failing with "read why this moved, then re-pin deliberately". **Not built
      on purpose:** it reddens the suite on every added test until the doc is updated, and
      that is a change to the working rhythm, which is the author's call.

---

## Review

*(filled in as items close)*

---

## Item 9 — THE RULED DOCKET (opened 2026-09-24, sixth sitting)

The author ruled on eight decisions after three measurements. Order of execution is by
ascending risk, not by decision number.

- [x] **9a. DONE 2026-09-24 (`cf6d8c7`) — Decision 1A.** Original note: **9a. Decision 1A — re-attest both session serve paths.** `POST /api/transform/{undo,redo}`
      and `GET /session/{session_id}`. **Measured safe before ruling:** 16/16 undo/redo pairs
      across 8 UoDs attest cleanly; both writers go through `generate_layout` (which attests)
      and neither passes `deltas=`, so no regime-3 geometry reaches this store. The `None`-DTO
      caveat is not new: `_render_svg(egi, None)` already raises today.
- [x] **9b. DONE 2026-09-24 (`cf6d8c7`) — Decision 2A.** Original note: **9b. Decision 2A — correct `CLAUDE.md:237`.** It claims "every served (EGI, drawing)
      pair is verified", which 6f showed false. Written AFTER 9a so it describes the end state:
      the serve paths attest; `generate_overview_layout` attests a *quotient* via
      `attest_overview`, which is the right check for a collapsed view and not full §3.3.
- [x] **9c. DONE 2026-09-24 (`e4d1a0f`) — Decision 3, per method.** Original note: **9c. Decision 3 — `hierarchical_index`'s dead half, per method.** `get_children`
      returns a copy; `validate_containment` fixed or deleted (it compares depth, not ancestry,
      and its name invites trust); `remove_area` LEFT pinned (a correct version needs a
      re-parent/cascade policy nothing constrains); `NestingInfo` set → frozenset.
      **On the calculus map** — raise `.core_modification_authorized`, lower it AFTER the commit.
- [x] **9d. DONE 2026-09-24 (`052b3ec`) — Decision 7(ii).** Original note: **9d. Decision 7(ii) — canonical tie-break in the generators.** Not a soundness defect:
      the two emitted texts `same_graph`-match each other and the input. The nondeterminism is
      `sorted(key=sig)` being stable over a `frozenset` of `uuid4` ids when signatures tie by
      design ("intrinsic ambiguity, not a bug"). Fix = individualize a tied element, re-refine,
      emit the lexicographic minimum, under a budget. **Touches no calculus-map module.**
      Retires the strict xfail `test_egif_generation_is_deterministic_on_symmetric_lines` as XPASS.
- [x] **9e-0. DONE 2026-09-24 (`a17c9d3`). PREREQUISITE, found 2026-09-24 while starting 9e: one finaliser, not three,
      and it must stop dropping fields.** `_finalize_alphabet_and_rho` exists in **three
      copies** — `egif_parser_dau:1050`, `cgif_parser_dau:707`, `clif_parser_dau:787` — the
      same "one rule, three implementations" shape the INS defect taught this project. All
      three rebuild `RelationalGraphWithCuts` from an **explicit field list**, so they drop
      `variable_names`, `sort` and `quotation`. Measured: a CGIF- or CLIF-parsed graph carries
      an alphabet and an **empty** `variable_names`; an EGIF-parsed one carries names and **no**
      alphabet. Harmless only because CGIF/CLIF never set those fields — wiring EGIF (9e-2)
      activates the drop and would break the CLIF tie-break, which reads `variable_names`.
      Consolidate into one field-preserving helper in `egi_core_dau` (which owns `AlphabetDAU`),
      beside `_extended_alphabet`, which `formal_transformation_rules` already has and the
      builders will need.
- [~] **9e. PARKED ON BRANCH `alphabet-derived` (`42819a7`) 2026-09-24 — and the question
      changed under measurement.** The author ruled: **the alphabet is derived from the ink,
      not stored**, superseding Decision 6A (there is nothing to extend once nothing is
      stored; the `with_edge` growth written for 6A proved unnecessary and was reverted).
      The prompt for the re-framing was the author's own question — *the EPG lets the
      Graphist name new individuals not yet in the model; does that bear on this?* It did.
      Sources: **Roberts** (*Existential Graphs of Peirce*, ~p.32, citing LN 103r–106r) — the
      universe "becomes more determinate as the graphist … proceeds with his business";
      `ENDOPOREUTIC_GAME_GUIDE.md:124`; `DOMAIN_ORACLE_AND_M.md:267` ("skolemization is the
      contest game's business"). Against which: **Dau fixes the alphabet for the calculus**
      (Def 12.6/23.1 + "EGIs **over** the alphabet", Def 15.2). The two sit at different
      layers, and seeing that exposed the real defect — `alphabet` held *a summary of the
      names used* in a field meaning *the alphabet the graph is over*.
      **Decisive measurements:** 0 of 15 corpus alphabets declare an unused name; 0 of 11
      stored rhos disagree with their vertices; nothing in the codebase ever *declares* a
      vocabulary (all four construction sites derive from ink). So the field has never once
      held a declaration.
      **Dau settled two conventions against expectation:** Def 23.2 — constants label
      **edges**, not vertices; Def 24.1 — `ρ : V → {∗} ∪ C` is **total** on V.
      **Blocks the merge:** all three calculus extents move (structure 1,205; refusal
      agreement + extent; soundness extent) and a 266-instance ledger shrink must be earned.
      See CURRENT_PLAN's ▶ START HERE for the protocol. Original note: **9e. Decisions 5A + 6A — THE ALPHABET. These are ONE change, not two.** Wiring
      `egif_parser_dau._finalize_alphabet_and_rho` is what makes both visible: of the 239 failing
      items, 2 are the two-arity fixtures (5A) and ~237 are builders not growing the alphabet
      (6A). Doing 5 alone is incoherent — nothing fails until the alphabet is wired.
      **Measured before ruling:** 0 of 133 corpus graphs use one name at two arities (the 7
      cross-graph reuses are irrelevant — an alphabet is per-graph), so 5A costs exactly the two
      hand-written fixtures and no corpus migration. 6A touches protected `egi_core_dau`.
      Its own arc; do not fold into the small items above.
- [ ] **9f. Decision 8A — clause 3 over the Architecture module list.** Today's finding
      (CLAUDE.md:237) came from there without anyone looking, which is the argument for it.


### Item 9 — what the four completed items actually found

Each turned up something the docket had not predicted, and the pattern is the
same one this arc keeps meeting: the written claim was *true when written* and
nothing was keeping it.

- **9a.** The two routes are `/api/undo` and `/api/redo`, **not** the
  `/api/transform/*` names the docket used — and `Session.current_layout_dto` is
  its **own field**, not a view onto `history`, so `GET /api/session` and
  undo/redo serve from genuinely different places and a fix to one does not
  cover the other. Neither fact was written down anywhere. The routes had **no
  test of any kind** beforehand.
- **9c.** `validate_containment` was the one worth fixing though nothing calls
  it, because it misleads **by its name**. `remove_area` stays pinned: a correct
  version must choose between re-parenting orphans and cascading, and nothing in
  the codebase constrains that choice — inventing a policy for a method with no
  caller yields a second landmine, not none.
- **9d.** Two findings. (1) The defect was **not** a soundness defect: both
  emitted texts `same_graph`-match each other and the input, so the refinement
  was right to colour the symmetric lines equally and the fix does not belong
  there. (2) Fixing the structural tie left **CLIF still nondeterministic**,
  because it preserves the parser's variable names, so two interchangeable lines
  carried different *emitted* names, every certificate tied, and the pick fell
  back to enumeration order again. Names now ride in the certificate but stay
  out of the colours, where the isomorphism engine would see them.
- **Sizing before designing paid for itself twice.** 341 graphs, ten ties, every
  one a class of two — so exact minimization is affordable everywhere and the
  budget guards a case that does not arise. And 0 of 133 corpus graphs use one
  name at two arities, which is what makes 9e's 5A half cheap.

## Item 10 — THE UoD ALPHABET (opened 2026-09-25, seventh sitting)

Opened by the author's question during the `alphabet-derived` merge: *we are not
talking about an EGI alone any more, but about a view on a UoD that evolves.*
Everything below follows from one distinction that the merge made visible and
did not resolve.

**The distinction.** Dau's Σ is a language a graph is *over* (Def 12.7, p.126;
with constants Def 23.1), not an inventory of what was scribed. All six rules
are maps from EGIs-over-Σ to EGIs-over-Σ with Σ held **fixed** — erasing the
last `Penguin` edge leaves a graph over the same Σ. So the alphabet now derived
in `egi_core_dau.__post_init__` is **not** Dau's Σ. It is the *minimal* Σ that
one state satisfies: exactly right for well-formedness, and silent about
language.

The language belongs to the UoD. The case that separates them is an individual
coming and going: a constant leaving the sheet is not a word leaving the
discourse. It bites hardest in ρ — Def 24.1 (p.250) gives ρ : V → {∗} ∪ C, so a
per-state C means ρ's codomain shrinks every time an erasure takes a constant's
last edge. That is not Dau, and it is not what a UoD means.

**Measured 2026-09-25, before the keys were dropped:** of 245 corpus
`.egi.json`, 27 carried a stored alphabet, **0** declared a relation or constant
it did not use, and **0** stored ρ disagreed with its ink. Nothing was lost —
and note the warning inside that: nothing was lost because nothing was ever
recorded there. No UoD-level alphabet exists in `src/` (checked:
`universe_of_discourse`, `egi_transformation_history`, `tomos_service` do not
mention one).

### 10a — the `maps_carried` clause has a correct form, currently unstatable

`calculus_expected.maps_carried` asserted `g.alphabet.R ⊆ h.alphabet.R` and was
**dropped** in the merge (it tested a stored summary; derived, ERA falsifies it
by design — 1,205 failures in the default mode alone). The right invariant is
not the subset but **"`g` and `h` are EGIs over the same Σ"**, which under a
fixed Σ holds of every rule and is a genuine calculus property. It cannot be
written until Σ has a home. Restore it there, not here.

### 10b — INS may introduce a name in no alphabet at all — **the author has ruled this a SEPARATE ARC**

Dau Def 15.2 (p.164-165) asks that inserted content be an EGI over Σ, so INS
cannot introduce vocabulary. The engine grows Σ instead, and always has:
`formal_transformation_rules._extended_alphabet` / `rule_interaction`. Shown
2026-09-25 — `INS (Zorblatt *y *z)` into a negative context of `~[ (P *x) ]`:
`legal()` true, engine applied, R `['P'] → ['P','Zorblatt']`. Deriving the
alphabet did not fix this; it made it *moot at the state level* while leaving it
untouched where it matters. A pre-existing departure, older than this arc.

**The author's framing, and it sets the arc's direction:** *"languages do
change."* So the arc is not "forbid it" — it is **make language change a
recorded act rather than a silent side effect of assertion**. Enlarging the
language is a different act from asserting a new fact; that is the
enlargement/relinquishment distinction of `model_revision`'s taxonomy, one level
up, applied to vocabulary instead of content. A behaviour change to the
calculus: **do not start it without the author.**

### 10c — arity is pinned within a state and unchecked across a chain

`derive_alphabet` refuses one name at two arities in one graph (Def 12.6: `ar`
is a function) — that discipline now reaches every graph. Across a history
nothing checks anything. Shown 2026-09-25: `(Employee "Peter" "Acme" "2020")`
and `(Employee "Peter" "Acme" "2020" "manager")` each build without complaint;
only together in one graph are they refused.

**The author's reading, and the resolution it points to.** Peter acquiring a
fourth *attribute* needs nothing — four unary edges on one line, a plain INS, no
arity moves. The hard case is the **name** changing arity, and no Dau rule
reaches it, because that is a change *of* the language and not a move *in* it.
But the adjustment can be made a change of **content** instead: let `Employee₃`
and `Employee₄` be two names in Σ (so `ar` stays a function and Dau is
satisfied), and scribe the bridge as an ordinary Beta scroll —
`~[ (Employee₃ x y z) ~[ *w (Employee₄ x y z w) ] ]`. Then the history accounts
for the adjustment by **modus ponens over a law that was written down**:
peelable, doubtable, relinquishable, checked by the same machinery as every
other proposition. Stronger than recording a language-revision act beside the
calculus, because the account lives inside it.

Having to choose the law's direction is the feature. `E₃ → ∃w E₄` says there was
always a role you could not yet name; `E₄ → E₃` says the richer fact carries the
poorer. Silent arity drift lets you have neither and behave as though you had
both.

### 10d — open, and the author's: vocabulary on a branching DAG

Does a name introduced only on a path later abandoned stay in the language? That
is the ◇/□ question (`modal_query`) asked of vocabulary rather than content, and
a UoD Σ must choose between the union over reachable leaves and something
narrower. **Not decided. Not to be guessed at.**

### What the merge did, so 10 is not re-derived

`to_dict` no longer writes `alphabet`/`rho` and `from_dict` no longer reads
them; 245 corpus files were migrated (900 deletions, 0 insertions, `same_graph`
asserted per file before each rewrite). Old files still load — required, since
~99k run artifacts under the gitignored `runs/` carry the keys. Emptying the
slot is what keeps it from being mistaken for the UoD's Σ.
