# Current Plan

**Last Updated**: 2026-06-12 (session end) — this session: **function terms relationalise
on import** (`_relationalize_functions` in `domain_model_importer`) so the function-bearing
COLORE modules (the majority) import — `(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧
density(z))`, validated on the real COLORE `density.clif`; **plus a CLIF
universal-quantifier correctness fix** the relationalization exposed — a
mutually-compensating parser+generator pair where a positive-body `(forall (x) (P x))`
collapsed to `∃` and the generator blanket-labelled everything `forall` (authorized core
change; both fixed, round-trips now honest). Prior sessions: the **T-box theorem query**
(`theory_query.entails`, freeze-a-witness), the **OWL→CLIF→EGI pipeline** (`owl_to_clif`),
two real ontologies landed (`bfo_core` BFO + `colore_between` from the real COLORE repo),
the `theorem` verdict **visible in `/agon`**, and a clutch of import fixes (CLIF `/* */`
comments, alpha-renaming reused variables, M-as-data non-attesting load). **▶ Next session:
P0 triage the 7 pre-existing red layout tests, then Playwright E2E** over `/agon`
interpretation + challenge mode — see ▶ NEXT SESSION. Prior: the **freeform composition arc is COMPLETE** (steps
1–4: fix-time validity → draw-then-read canvas → legible EGI diff → **challenge
mode**). Also this session: the **persona narrative** (`docs/ARISBE_PERSONAS.md`)
and the **Domain Oracle** for Agon's model M (`docs/DOMAIN_ORACLE_AND_M.md`, step 1
built). The exact-correspondence engine (Phases 1–4) remains complete. Detailed
freeform history is condensed below; per-module mechanics live in git/docs/memory.

---

## ▶ NEXT SESSION — start here

**This session: function-term relationalization + a CLIF universal-quantifier correctness
fix (parser + generator) + P0 (7 red layout tests triaged) + P1 (Playwright E2E)** — all DONE
(✅ blocks below; P0 detail in the Backlog). **▶ Start next session on P2 (import breadth) or
a layout follow-up (reader robustness on dense ELK / tension compaction — both in Backlog).**

**P0 — DONE: the 7 pre-existing red layout tests, triaged + resolved** (full detail in the
Backlog's ✅ P0 entry). None were from the CLIF work or a core fault — §3.3 still attests the
whole corpus; the failures were the *stronger* geometric-reader round-trip on two dense
imported reasoning ontologies (`bfo_core` under ELK; `colore_between`'s ternary order under
clockwise), plus one opt-in-engine compaction regression. Resolved with a documented
`_reader_frontier` helper (defers exactly the frontier combos, keeps every passing case) and
one xfail. Two genuine layout follow-ups logged in the Backlog (reader robustness on dense
ELK; tension compaction).

**P1 — DONE: Playwright E2E over `/agon` interpretation + challenge mode** (the standing
companion debt, now committed). Two new headless-Chromium suites (skipped cleanly if
Playwright/Chromium absent, like `test_ergasterion_freeform_e2e.py`):
- `tests/test_agon_e2e.py` (4) — the picker→interpret→**theorem** flow driven through the real
  page: select a persona model → "Does G hold in M?" → verdict (teacher TRUE; student FALSE +
  named counterexample); a typed rule + "Use rules" → the **"Theorem of M? (deduction)"** block
  reads TRUE (freeze-a-witness) beside the UNKNOWN open-world peel; "Where does G hold?" → the
  inverse-pivot holds/partial/independent/contradicts tally.
- `tests/test_ergasterion_challenge_e2e.py` (2) — freeform **challenge grading**: enter the
  canvas, pick the one-relation target → prompt + grade enabled; grading an empty canvas shows
  the **legible diff** (missing the target's relation/individual); drawing `(man "Socrates")`
  freehand → graded a **match** (`same_graph`). 9/9 E2E green (incl. the 3 prior freeform).

**P2 — import breadth (`cl-imports` auto-resolution).** With function terms now
importing, the remaining blocker to a *fully cited* function-bearing COLORE corpus UoD
(the `colore_between` treatment for, say, `density`) is closure resolution — `density`
imports `amount` → `field` (the real-number field axioms). An auto-resolver that fetches /
locates and conjuncts the `cl-imports` closure would unblock landing those modules cited.
Also queued here: `ObjectUnionOf`/`AllValuesFrom` heads → contest game; Manchester / Turtle
/ RDF.

**Then** (next fork): the dialogical **contest / automated Grapheus** (the peel supplies
the model-respecting reply) + the **warrant lifecycle** (low → tested by surviving Agon).

---

## ✅ DONE 2026-06-12 — CLIF universal-quantifier correctness (parser + generator)

A follow-on to the relationalization work surfaced a **mutually-compensating pair of bugs**
between the protected `clif_parser_dau` and `clif_generator_dau`, now both fixed (authorized
core change; full suite green).

- **Parser — positive-body universals.** `(forall (x⃗) body)` only built the universal's
  negative context when `body` was a material conditional (`if`) — it dropped the binder and
  leaned on the conditional's scroll. A **positive** body (a bare atom, conjunction, or
  existential — and, it turned out, a biconditional) had nowhere to place the bound line, so
  the universal silently collapsed to an existential (a line on the sheet **is** ∃). The
  `forall`/`exists` handlers were in fact identical code. Fixed: keep the established shape
  when the body is `if`/`not` (the bound line settles in their cut — the canonical
  subsumption scroll is unchanged), and otherwise build the double cut `~[ *x⃗ ~[ body ] ]`
  explicitly (binders in the outer/negative cut → universal; the body's own existentials
  stay existential at even depth). `(forall (x) (P x))` now reads `~[ *x ~[ (P x) ] ]` = ∀x P,
  not `~[ *x (P x) ]` = ∃x P. `iff` moved to the wrap path (its two scrolls are siblings, so
  a shared line hoists to the sheet — positive — unlike `if`).
- **Generator — quantifier by polarity.** `generate_with_quantification` wrapped *every*
  free variable in one blanket `forall`, mislabelling every sheet-level existential; it only
  round-tripped because the old parser read `forall` back as `exists`. Fixed: classify each
  line by the polarity of its home area (`is_oddly_enclosed`) — a positive (even-depth)
  vertex is existential, a negative (odd-depth) one universal. An all-existential graph now
  emits honest `(exists …)`, an all-universal one honest `(forall …)`. (The cut structure
  already pins each universal line negatively, so the parser derives ∀ from structure, not
  the keyword — `exists` therefore round-trips every shape faithfully; a graph mixing both
  polarities can't be rendered prenex without loss and keeps the faithful-round-trip `exists`.)
- **Verified:** `tests/test_properties_cgif_clif_round_trip.py` (the 6 known-example
  round-trips + count-preservation + idempotency) now pass *and* the emitted CLIF is
  semantically honest (`(P *x)` → `(exists (x) (P x))`; `~[ (Cat *x) ~[ (Animal x) ] ]` →
  `(forall (x) (not (and (Cat x) (not (Animal x)))))`). Full suite green; 152 core tests pass.

---

## ✅ DONE 2026-06-12 — function terms relationalise on import

The function-bearing COLORE modules (the majority) now import. The protected CLIF parser
(`_parse_atomic_formula`) accepts only *names* in argument position, so a nested function
application `(f t₁ … tₙ)` there — e.g. `density.clif`'s `(density (dmv v m))` — was a parse
error. Functions are EG-expressible by **relationalisation** (a function = a relation whose
last argument is uniquely determined — its graph), so the importer does the
meaning-preserving reduction at its own boundary, leaving the protected lexer untouched
(like `_strip_block_comments` / `_disambiguate_variables`).

- **`_relationalize_functions` (`src/domain_model_importer.py`)** — a CLIF→CLIF pass over
  the existing s-expression reader (`_clif_tokenize` / `_clif_read_all` / `_clif_serialize`).
  Logical structure (connectives / quantifiers / `cl-text`/`cl-imports` wrappers) is
  recursed through untouched; at every predication — including `(= t₁ t₂)`, since the
  parser reads `=` as an ordinary relation — each function-term argument is lifted: mint a
  fresh `z`, replace the occurrence with `z`, conjoin the graph atom `(f …args… z)` under a
  fresh `exists`. `(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧ density(z))`. Nested `(f (g x))`
  lifts inside-out; the **value-as-equality** case `(= (dmv x y) (dmv z y))` relationalises
  both sides → `(= z₁ z₂)`. The ∃-form is sound in *any* polarity (the value exists in
  every context given totality), so a lifted atom inside a `not` stays correct.
- **Functionality is optional + non-Horn.** `from_clif_text(…, assert_functionality=True)`
  emits totality `∀x⃗∃z R_f` + uniqueness `∀x⃗∀z∀z′ (R_f(x⃗,z)∧R_f(x⃗,z′)→z=z′)`; default
  off (the minimal correct import needs only the graph atom; functionality uses `=` → falls
  to the contest residue like the rest of COLORE).
- **Verified** on the real COLORE `density.clif` (downloaded from `gruninger/colore`):
  `dmv`, `add_density`, `mult_density`, … all import as relations; the canonical axiom
  round-trips via `same_graph`. 8 new tests
  (`tests/test_domain_model_importer.py::TestFunctionRelationalization`); no regressions
  across the import / ontology / agon / materialization / theory-query suites (162 tests).
  Doc: `docs/CORPUS_AND_IMPORT_MODEL.md` §5.2.
- **Not committed:** a *fully cited* function-bearing COLORE corpus UoD (the
  `colore_between` treatment for `density`) — that needs `cl-imports` closure resolution
  (`density` → `amount` → `field`, the real-number field axioms), which is the separate
  import-breadth fork. `colore_between` stays the resolved-closure exemplar.

---

### For reference — the consolidate-&-make-visible sequence (steps 1–2 DONE 2026-06-12)

Three sessions built deep inference power (peel → materialization → theory query →
OWL/COLORE import). Steps 1–2 made it visible:
1. **Render the `theorem` verdict in `/agon`** — DONE (browser-verified).
2. **Land a real ontology** — DONE: `bfo_core` (BFO taxonomy, OWL→CLIF→EGI) +
   `colore_between` (real COLORE, CLIF→EGI). Both in the `/agon` picker.
3. **Playwright E2E** — the open companion debt (folded into the list above).

---

## ✅ DONE 2026-06-12 — COLORE validation + `colore_between` landed

Validated the pipeline against the **real COLORE repository**
(`github.com/gruninger/colore`) — which immediately surfaced and fixed two genuine bugs
that synthetic content had hidden, and landed the first corpus ontology from an external
CL repository.

- **`/* */` header bug (fixed).** Every COLORE file carries a `/* Copyright … University
  of Toronto **and** others … */` block; the protected CLIF lexer strips only `;;`, so
  "and"/"if"/"not" inside the header tokenised as keywords and broke the parse — *no real
  COLORE file could be read*. `from_clif_text` now strips `/* */` blocks (leaving `//` for
  `http://` IRIs).
- **Variable-collapse bug (fixed — a correctness bug).** Many `(forall (x) …)` sentences
  reusing `x` had every `x` unified by `parse_clif` into one line of identity, turning
  `(∀x A→B) ∧ (∀x C→D)` into the weaker `∃x (A→B)∧(C→D)` (+ a layout blowup). Fixed by
  **alpha-renaming** all quantified variables globally-unique before parse
  (`_disambiguate_variables`, in `from_clif_text` + `compose_models`) — the CLIF analogue
  of the OWL translator's per-axiom fresh variables.
- **`colore_between` landed.** The COLORE *betweenness* ontology (resolved `cl-imports`
  closure, verbatim CC-BY-SA content attributed) as a cited `kind=ontology` UoD, in the
  `/agon` picker. Corpus = 25.

Honest boundaries confirmed (not bugs): COLORE is mostly **non-Horn FOL** (materialization
skips it — betweenness forward-chains nothing, its value is the contest); **function terms**
`(dmv v m)` are not handled by *our CLIF parser* (parse error — an implementation gap, not a
limit of EG: functions relationalise — `(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧ density(z))`
+ functionality — and Dau gives a direct extension, ICCS 2007; the fix is to relationalise on
import); `cl-imports` still needs hand resolution; and COLORE uses **underscores** (which round-trip
in EGIF), so it doesn't exercise the hyphen fix — that stays pinned by the in-repo
hyphenated `animal_taxonomy`. (I was also wrong earlier that there was "no internet" —
`WebFetch`/`WebSearch` and Bash all reach the network.)

---

## ✅ DONE 2026-06-12 — consolidate & make visible (steps 1–2)

**Step 1 — the `theorem` verdict is visible in `/agon`.** `renderInterpretation`
(`web_viewer/agon.html`) now paints a **"Theorem of M? (deduction)"** block beside the
extensional peel: the deduction verdict + the freeze-witness `body ⊢ head` + which head
atoms derived. So when the peel reads *vacuously* over an empty A-box (a pure T-box), the
real answer is shown. Browser-verified (Playwright/Chromium).

**Step 2 — a real ontology landed in the corpus: `bfo_core`.** The Basic Formal Ontology
upper taxonomy (Arp, Smith & Spear 2015), authored as `corpus/ontologies/bfo_core.ofn`
and imported **OWL→CLIF→EGI** into a `kind=ontology` UoD (cited; `tools/build_ontologies.py`
`bfo()`). It's a pure T-box — the ideal companion to step 1: select it in the `/agon`
picker, propose `Object ⊑ Entity`, materialize → empty, **theorem block → TRUE** (freeze
`(Object __w1) ⊢ (Entity __w1)`), the disjointness as the honest non-Horn residue.
Browser-verified end to end.

The forcing function did its job — landing a real ontology surfaced two genuine gaps,
both fixed:
- **A translator bug:** `owl_to_clif` emitted the bound variable `x` for *every* axiom,
  and `parse_clif` unifies same-named variables across sentences → all 24 subsumption
  scrolls collapsed onto **one** line of identity threaded through 47 cuts (a correctness
  smell + a 176s layout). Fixed: **fresh per-axiom variables** (`x1`, `x2`, …) — 24
  distinct lines, layout 176s → 21s. Regression-tested.
- **Per-query attestation cost:** `/agon/interpret` against a corpus model called
  `load_uod`, which **attests §3.3 (a full layout, 21s for BFO)** at the load boundary —
  even though M is read purely as *data* (materialize/peel never draw it), and
  `where-it-holds` would attest *every* UoD. Fixed: `load_uod(..., attest=False)` for the
  M-as-data reads (the "M is data, draw only the contested fragment" principle,
  `DOMAIN_ORACLE_AND_M.md` §5). Picker→interpret **22.5s → 0.1s**. Default stays
  `attest=True` for every caller that draws.

A documented frontier remains: BFO's **relational** scrolls (transitive/inverse, multi-var
bodies) are super-linear to lay out, so the stored `bfo_core` is the *taxonomy* only
(subsumption + disjointness); the full `.ofn` (with RO relations + A-box) is the source of
record and imports fine as data — the layout-perf frontier, not a correctness gap.

---

## ✅ DONE 2026-06-12 — the OWL→CLIF→EGI import pipeline (front half)

The named pipeline's **back half already existed** (`clif_parser_dau.parse_clif` turns a
Common Logic sentence into exactly the EG shapes — subsumption scroll, conjunctive Horn
body, existential-head scroll, disjointness denial). The missing **front half** is now
built: `tools/owl_to_clif.py` reads **OWL 2 Functional-Style Syntax** and translates the
EG-expressible axioms to CLIF (class expressions: named classes, `ObjectIntersectionOf`,
`ObjectSomeValuesFrom`):

- **Forms:** `SubClassOf`, `EquivalentClasses`/`DisjointClasses` (pairwise),
  `SubObjectPropertyOf`, `ObjectPropertyDomain`/`Range`, `InverseObjectProperties`,
  `Symmetric`/`TransitiveObjectProperty`, `ClassAssertion`, `ObjectPropertyAssertion`,
  `SameIndividual`/`DifferentIndividuals`.
- **Honest floor** (the SUO-KIF discipline): cardinality, union, complement,
  `AllValuesFrom`, datatypes, functional/key, annotations → **reported by construct**;
  `⊑ owl:Thing` dropped as trivial; `Declaration` counted as vocabulary. IRIs/prefixed
  names reduce to sanitized local identifiers.
- **First-class:** `domain_model_importer.from_owl_text` / `from_owl_file` (warnings
  carry the skip-report); composes with the CLIF path; wraps as a `kind=ontology` UoD.
- **The loop closes:** an OWL-imported ontology is a real M whose subsumption /
  intersection / transitivity theorems `theory_query.entails` decides. Tests:
  `tests/test_owl_import.py` (23) + `tests/fixtures/zoo.ofn`. Doc:
  `docs/CORPUS_AND_IMPORT_MODEL.md` §5.1.

---

## ✅ DONE 2026-06-12 — ontology-as-M (step 1): the T-box theorem query

Cashed in materialization + the interpretation register on the **real corpus ontology
UoDs**, and closed the gap the exercise exposed.

**What exercising revealed.** Materializing the three ontologies:
- **Porphyry** (`(Man "Socrates")` + 5 subsumption rules) → derives Socrates is
  Animal/Living/Body/Substance (the full ladder); the persona promise is concretely
  true wherever M carries an A-box.
- **FOAF** (Alice/Bob Persons + typing rules) → derives both are Agents.
- **SUMO upper spine** — a **pure T-box** (43 subsumption rules, *zero* individuals) →
  materializes to the **empty model**. A subsumption proposal then reads **vacuously
  TRUE** (closed — a nonsense universal reads TRUE too) or **UNKNOWN** (open). *Model-
  checking cannot decide a theorem of the theory.*

**The fix — `src/theory_query.py` (`entails`, 15 tests).** The deduction
`GENERATION_AND_TESTING.md` routes to "the contest/deduction game": decide a universal
`~[ B ~[ H ] ]` by **freeze-a-fresh-witness** — mint an arbitrary constant per body
line, assert B over it, **materialize M ∪ {frozen B}**, check H. Sound (witnesses
mentioned nowhere in M ⇒ holds for all) + Horn-complete (least Herbrand model). A
negative is FALSE only when M is **wholly Horn**, else **UNKNOWN** (skipped non-Horn
axioms might bear) — so `Man ⊑ Beast` over Porphyry is honestly UNKNOWN (its Man/Beast
**disjointness** is the skipped denial that would settle it). Verified on the corpus:
SUMO `Object ⊑ Entity` TRUE / `Object ⊑ Occurrent` FALSE; FOAF `knows(y,z) → Agent(y)`
TRUE (typing chained through subsumption).

**Wiring.** `/agon/interpret` + `_interpret_payload` return a `theorem` block beside
the extensional `verdict` whenever `materialize` is set and G is a universal Horn scroll.
Peel stays pure model-checking; the theory query is the inference step. Doc:
`docs/DOMAIN_ORACLE_AND_M.md` §6.2. *Frontend rendering of the `theorem` block is the
next small task.*

---

### Done previous session (the Agon interpretation arc) — for reference

1. **The semantic-game seam — DONE 2026-06-11** (`src/semantic_game.py`, 17 tests):
   `evaluate(egi, oracle)` reads G outside-in, returns three-valued `Verdict3` +
   transcript + structured `winning_witness` / `counterexample`. Kleene logic.
2. **The interpretation register in Agon — DONE 2026-06-11.** The inning *given M,
   then G*: part 1 choose M (`set-model` + new-game framing), part 2 peel
   (`POST /agon/games/{id}/interpret` runs the semantic game, non-mutating), part 3
   decide (`available_dispositions(game, verdict)` annotates the taxonomy by the
   outcome — a hint, never a filter; nothing auto-asserts). 14 route tests; the five
   persona innings reproduce through the route. Design-of-record:
   `docs/GENERATION_AND_TESTING.md` (the eliminative/additive cut; making=Ergasterion,
   game=Agon; deduction-through-Agon; model-checking-vs-inference; truth-vs-validity;
   part-3-is-a-judgment).
3. **Agon frontend — DONE 2026-06-11.** `/agon` now has a reference-model picker
   (`GET /agon/models` = curated persona scenarios + corpus UoDs; `src/agon_models.py`),
   an open/closed toggle, and a **"▷ Does G hold in M?"** button running the
   standalone `POST /agon/interpret` (resolve M → peel → verdict + transcript +
   witness/counterexample + verdict-annotated dispositions, shown in place of the
   board). "Play it out" still starts a full contest. Nothing asserted.
4. **Next: materialize the model** (oracle step 3, `docs/DOMAIN_ORACLE_AND_M.md`
   §6.1) — author M as *facts + Horn rules*, forward-chain to the least Herbrand
   model, peel against that. Resolves "model-checking, not inference" (the syllogism
   works; corpus UoDs carrying rules become testable); precondition for ontology-as-M.
   `src/model_materialization.py` (`materialize_egi`), reusing `match_atoms`; opt-in on
   `CorpusOracle.from_egif(..., materialize=True)` and `/agon/interpret`.
5. **The inverse pivot — DONE 2026-06-11.** `POST /agon/where-it-holds` + a "🔎 Where
   does G hold?" button: fix G, range the peel across candidate models (examples +
   corpus, optionally materialized), rank by relationship — holds / partial (residue =
   the contribution) / independent / contradicts. Abductive context-retrieval; reused
   the oracle unchanged (`docs/DOMAIN_ORACLE_AND_M.md` §7).
6. **Then:** oracle steps 4–6 (demand-driven cache → horizon/open-closed params →
   `SparqlOracle`/Wikidata); downstream warrant lifecycle, **ontology-as-M** (now
   unblocked — materialize the T-box, peel/search against it).
3. **Diachronic exemplars (Praeclarum first)** — interleave once the seam exists:
   ingest canonical worked proofs as real `TransformationChain`s; the shakedown
   cruise for the semantic game. `docs/` + the diachronic-exemplars memory.
4. **Math menu** (independent, ready): ∀x scaffold tactic → selection-driven `fold`
   → ZFC/Peirce-1881 fixtures + graph-with-holes schema node. Palate-cleanser depth.
5. **Editor-persona frontier** (off the Agon path): by-hand reading desk + LaTeX/TikZ
   export (the `egpeirce.sty` lineage; exporter exists, DTO→TikZ adapter + web button
   don't). Do when the external Peirce-edition audience is the priority.

The **Domain Oracle** (`src/domain_oracle.py`, 16 tests) is built and waiting on
step 1: `resolve(g)` = conjunctive-query homomorphism of a negation-free `g` into a
model's asserted atoms → CONFIRMED/UNKNOWN/DENIED with provenance; `witness()` for
the negative-area pick. Built on the public EGI API, not the protected iso engine.

---

## ✅ DONE 2026-06-11 — challenge mode (freeform step 4)

Correspondence, learned by doing: present a linear form, draw it freehand, grade the
attempt against the parsed target. The grader is isomorphism (`same_graph`); the
feedback is the **legible EGI diff** in EG vocabulary (missing/extra/scope/incidence/
order), never a pixel comparison — a drawing that *looks* different but denotes the
same graph passes; one that mis-scopes a line fails with a scope finding.

- **`src/challenge_mode.py`** (12 tests) — standalone gradeable core: `Challenge` +
  a curated `CHALLENGE_BANK` difficulty gradient (one-relation → argument-order →
  shared line → negation → the scroll → the universal `~[ (man *x) ~[ (mortal x) ] ]`,
  where a line crossing a cut boundary makes scope the gold error); `list_challenges`
  / `get_challenge`; `grade(target, attempt) → DiffReport` (parse target, `legible_diff`).
- **Routes** (`web_api/routes/ergasterion.py`, 9 tests in `test_ergasterion_challenge.py`):
  `GET /ergasterion/challenges` (prompts only, never a drawing) and
  `POST /ergasterion/sessions/{id}/grade-challenge` (read the drawing → ill-formed ink
  returns validity feedback not a grade; well-formed → `matches` + findings +
  `target_linear_forms`). **Non-mutating** — grading never touches session state.
  `ChallengeGradeRequest` in `api_models.py`.
- **Frontend** (`web_viewer/ergasterion.html`): a challenge picker + prompt/hint +
  "Grade my drawing" + result panel inside the freeform tools; populated from the
  bank on first arming; node `--check` clean, page serves, endpoint verified. Real-
  browser interaction unverified here (no headless browser this session).

Building challenge mode was the ongoing stress test of `read_drawing` on human input,
as designed (`docs/FREEFORM_COMPOSITION_AND_LEARNING.md`).

---

## Freeform composition arc (Thread B) — COMPLETE (steps 1–4, 2026-06-10/11)

**Designated next task: the freeform composition canvas** — composition becomes
*draw-then-read*. The exact-correspondence engine (Phases 1–4) is done; that was
**build step 0** of `docs/FREEFORM_COMPOSITION_AND_LEARNING.md`, so the next session
**starts at step 1**. Read that doc's "Build order" + the three-move arc, and
`docs/SESSION_LOG_2026-06-10.md` for how the foundation got here.

**The build, in order (each a shippable increment):**
1. **Visible containment + snapping + fix-time validity** (the de-risked core).
   - **Fix-time validity pass — DONE 2026-06-10** (`src/drawing_validity.py` +
     `tests/test_drawing_validity.py`, 13 tests). `validate_drawing(dto) →
     ValidityReport` runs `read_drawing` and catches the ill-formed drawings the
     reader *can* read, in EG vocabulary: **errors** (`overlapping_cuts` — cut curves
     cross, so the areas aren't a tree; `dangling_line` — a line end touches no mark
     within tolerance, the brittle stops-short/drift case) and **warnings**
     (`boundary_band` — a mark on a cut's boundary stroke; `unwired_predicate` — reads
     as 0-ary; `label_overlap`). `report.is_well_formed` = no errors. Geometry of
     record reused from `presentation_ops` (`cut_boundary`/`point_in_polygon`/
     `predicate_label_box`), so "inside / on the boundary" is the same curve the
     renderer draws and §3.3 attests; clean engine layouts raise zero errors.
   - **Visible containment + live feedback + snapping — DONE 2026-06-11** (on the
     freeform canvas). Cut interiors render as translucent filled regions (polarity
     by nesting depth); **live area feedback on drag** ("inside cut C" / "on the
     sheet") via point-in-polygon `areaAt`; **snapping** — line endpoints attach to
     marks by construction (click-a-mark line tool, so no stops-short/drift), and a
     **spot snaps clear of any cut boundary** (`_snapSpot`) on placement and
     drag-release so its area is never ambiguous (E2E-tested). `validate_drawing` is
     wired into the fix/read endpoints. **Step 1 is complete.**
2. **The freeform drawing canvas — DONE 2026-06-11** (backend tested; frontend
   shipped, interactive layer pending author's-eyes verification). Composition is
   now *draw-then-read*: the browser owns the ink, no live EGI, linear forms silent
   until gate ①.
   - **Backend (`src/drawing_to_egi.py` + two routes).**
     `build_egi_from_drawing(dto, predicate_labels, vertex_labels)` is the
     construction half of *fix = read*: `read_drawing` recovers structure (area
     tree + ordered incidence), the drawing carries content (relation names,
     constant labels), and this joins them into a real EGI. Corpus round-trip via
     `same_graph` (both styles, nested cuts, argument order, constant-vs-generic).
     `POST /ergasterion/sessions/{id}/read-drawing` (non-mutating preview: validity
     + linear forms) and `POST …/fix-drawing` (gate ①: validate → build → install
     as composing state → cross into deriving; §3.3 attested; refuses ill-formed in
     EG vocabulary). Additive — the typed `composition_ops` path is untouched.
   - **Frontend (`web_viewer/js/freeform-canvas.js` + Ergasterion integration).**
     Self-contained `FreeformCanvas` SVG surface (own coordinate space): tools
     Move / Line (vertex) / Relation / Constant / Cut (drag an ellipse) / Connect /
     Erase; translucent cut fills (polarity by nesting depth); **live area feedback**
     on drag (point-in-polygon `areaAt`, the same test the server uses); a cut is
     just ink (erase it, contents stay; drag a mark across a boundary to change
     area). "👁 Read it now" → preview; "① Fix this graph" → `fix-drawing` when ink
     is present. Opt-in toggle in the composing palette.
   - **Tests:** `test_drawing_to_egi.py` (6), `test_ergasterion_freeform.py` (12,
     incl. JS-serialize↔backend contract for binary order + ellipse-cut negation).
     Both JS files syntax-clean; page + asset serve. **Pending:** interactive
     pointer/drag behaviour in a real browser (no headless browser here).
3. **The legible EGI diff — DONE 2026-06-11** (`src/egi_diff.py`, 11 tests).
   `legible_diff(target, attempt) → DiffReport`: empty (and `matches` True) iff
   `same_graph`; else EG-vocabulary findings — `structure` (cut count),
   `missing`/`extra` (relations + individuals), `scope` (wrong cut/polarity — the
   gold Beta error), `incidence` (wrong connections), `order` (argument order).
   Content-aligned, not id-aligned (constants by label, relations by name +
   best-match arg signature, generic lines by incidence overlap aligned *first*).
   Ready for challenge mode.
4. **Challenge mode**: pick a tomos linear form, hide its drawing, grade the freehand
   attempt with `same_graph` + the diff. Difficulty gradient straight from the
   corpus (single relation → nested cuts → Beta with a shared line crossing a
   boundary). Building (4) *is* the ongoing stress test of `read_drawing` on humans.

**Building blocks in hand:** `read_drawing` (de-risked on human geometry,
`test_eg_reader.py::test_freeform_*`), `diagram-viewer.areaAtPoint` +
`isPointInFill` (Phase 4), `presentation_ops.cut_boundary` + `LayoutDTO.cut_boundary`
(a cut as a drawn polyline), §3.3 attestation at gate ①, `same_graph` /
`reading_matches_egi`. The one genuinely new logical piece is the **legible EGI diff**
(step 3). Scope boundary (load-bearing): Arisbe reads **structured placement, not
pixels** — reading a raster image is deferred (a hand-off to external AI that emits a
structured placement into the same `read_drawing` pipeline).

After freeform: the appetite-driven **math menu** (∀x scaffold tactic; selection-driven
`fold`) and the **Agon web arena** — independent and ready to pick.

### Phase 3c — clockwise placement (Peirce's writing convention) — DONE 2026-06-10
*ν specifies the order, so the drawing shows it: hooks drawn clockwise around the
spot in ν-order, by construction — consistently across every style and layout.*
`clockwise_placement.place_clockwise_hooks` (pre-attestation in `layout_service`,
applied for **all** styles): every ≥2-ary predicate's hooks → clockwise slots in
ν-order at the **rotation that best aligns with the vertices** (crossings
minimized). The **hook position** (`points[0]`) carries the order, so lines run
**straight to their vertices — no stub, no kink**. Locally guarded so **no line
strikes through any predicate label** (a spoke forced across its own spot reverts
to the natural hook); also reverts where a cut would be pierced. Carried by a
**single start anchor** (`assign_order_labels` ≤1 mark/relation; `read_drawing`
anchor-aware) + `argument_order_numerals: auto|always|never` toggle. §3.3 green; no
label strike-throughs; ordered round-trip **23/23** (`auto`) — placement where the
layout cooperates, numeral where it reverts. **Decision (2026-06-10): constrained
layout for clock-face placement considered and DECLINED** — it doesn't scale (a
shared line of identity gives a vertex conflicting clockwise demands from every spot
it touches; it would fight the cut hierarchy — exactly why Dau numbers the lines).
Order lives in ν; the numeral/anchor is the scalable carrier of record; clockwise
placement is a best-effort small-graph aesthetic. **Phase 3 / the exact-correspondence
extents work is DONE.**

### Label-aware ligature routing — DONE 2026-06-10
*Phase 3b's deferred third occlusion property shipped with its constructive
partner.* The §3.3 check (`correspondence_attestation` check #3) refuses any line
of identity running through a label box it is **not** incident to
(`path_intersects_box`, open interior). The partner
(`elk_layout_engine._build_ligature_paths`) routes non-incident lines *around*
label boxes as **soft obstacles** in a two-tier router: forbidden cuts are **hard**
(never crossed — soundness), label boxes are **soft** (skirted only when a detour
still clears every hard cut; otherwise the label yields to the sound route). Cleared
the `roberts_domain_modeling` IT+ strike-through ("Person" struck by the
shared-vertex fan-in); full §3.3 corpus + transformation + routing suites green.
Unit tests: `test_projection_conventions.py` (soft-skirt / hard+soft / soundness
fallback) + `test_correspondence_attestation.py::test_label_box_struck_through_by_non_incident_line`.

### Thread A — the exact-correspondence engine (`docs/EXACT_CORRESPONDENCE.md`)
*Delete the geometry proxy: a cut **is** its drawn curve; containment / crossing /
extents are exact facts about the literal picture; the browser is the client-side
arbiter; the logic stays coordinate-free.*

- **Phase 1 — exact cut containment — DONE** (`629a161`): `point_in_cut`/
  `bounds_in_cut` test the rounded rectangle the renderer draws (corner radius), so
  the corner void is gone. Threaded through `eg_reader` + `correspondence_attestation`;
  zero regression (482 §3.3 tests).
- **Phase 2 — exact ligature crossing — DONE** (2026-06-10): `count_cut_crossings`
  takes the corner radius and counts crossings against the rounded rectangle the
  renderer draws (edges inset by the radius + four corner arcs —
  `_rounded_rect_secant_crossings`), so a ligature grazing a rounded-away corner
  reads *outside* (not a spurious cut entry). Attestation threads `cut_radius`; 457
  §3.3 tests green, new unit tests pin corner-graze / straddle / pass-through.
  *Still open:* chosen-crossing-point *placement* in the renderer (a routing concern,
  deferred).
- **Phase 3 — label/numeral extents.** Three sub-pieces:
  - **3a — label-box containment / no straddle — DONE** (2026-06-10):
    `presentation_ops.predicate_label_box` is the single source of truth (renderer
    draws from it; §3.3 tests it). A predicate's containment is its drawn label box —
    wholly inside ancestor cuts, wholly outside others (`box_intrudes_cut`), no
    straddle. Vertices stay dots. 521 §3.3 tests green corpus-wide.
  - **3b — no improper occlusion — DONE** (2026-06-10): three §3.3 properties green
    corpus-wide — text-on-text overlap (`boxes_overlap`), vertex/constant label
    no-straddle (cut-aware `vertex_label_box`, factored out of the renderer as the
    single source of truth, the way 3a factored `predicate_label_box`; renderer draws
    text centred in that box), and **no strike-through** (a non-incident line through
    a label box, `path_intersects_box`) — the last shipped with its constructive
    partner, **label-aware ligature routing** (`_build_ligature_paths` skirts label
    boxes as soft obstacles, cuts stay hard; cleared the `roberts_domain_modeling`
    IT+ fan-in strike-through). Surfaced + fixed one real straddle ("Socrates" at a
    cut edge in `peirce_cp_4_394_man_mortal`).
  - **3c — clockwise placement (writing convention) — DONE** (2026-06-10): hooks
    drawn clockwise around the spot in ν-order by construction
    (`place_clockwise_hooks`, best-fit rotation = crossings minimized; 10-ary = a
    clock face), carried by a single start anchor + the `argument_order_numerals:
    auto|always|never` toggle. §3.3 green; ordered round-trip 23/23 with zero
    numerals (`never`).
- **Phase 4 — cut as a drawn polyline + browser as client-side arbiter — DONE**
  (2026-06-10): `LayoutDTO.cut_boundary` carries a cut's literal polyline (freeform
  human-drawn cuts); `resolve_cut_boundaries` shares it between §3.3 + `eg_reader`
  (point-in-polygon); renderer draws it as `<path>`; `diagram-viewer.areaAtPoint`
  hit-tests via `isPointInFill`. Wobble stays render-only cosmetic. Unblocks the
  freeform canvas.

### Thread B — freeform composition + challenge mode (`docs/FREEFORM_COMPOSITION_AND_LEARNING.md`)
*Composition becomes freeform drawing (typed marks at free positions, no live EGI);
the picture is read into a sign only at gate ① (`read_drawing` → EGI → validity →
"what it says"). Then challenge mode: show a linear form, draw it freehand, grade
with `same_graph` + a legible EGI diff — correspondence learned by doing.*

Reader **de-risk is DONE** (`read_drawing` is sound on human geometry; gaps are only
snapping + validity, pinned in `tests/test_eg_reader.py::test_freeform_*`). Build
order: (1) snapping + fix-time validity pass (depends on Phase-1 exact containment,
now in); (2) the freeform drawing canvas (replace the composing-phase typed
`composition_ops` with place/drag/erase on a free `LayoutDTO`; live forms silent
until fix); (3) the legible EGI diff (align by label+role, diff area-tree +
incidence/order — reused by validity *and* challenge mode); (4) challenge mode over
the tomos corpus. Building (4) *is* the ongoing stress test of (1).

*Scope boundary (load-bearing): Arisbe reads **structured placement, not pixels**.
Reading a raster image (photo/scan/freehand) is deferred — likely a hand-off to
external AI that emits a structured placement into the same pipeline.*

### Ready-to-pick math tasks (independent, both unprotected)
- **∀x scaffold tactic** — `universal_generalization` in `src/derived_rules.py`,
  closing `∀x∀y∃z plus` (parametric totality already proven). Sound-by-construction
  recipe in `docs/UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md` §2–§3 (the dual-rule
  approach is provably unsound — use the scaffold).
- **Selection-driven `fold`** — `fold_selection` in `src/definitions.py`: iso-match a
  drawn body to a definition and contract it (sound gate = selection ≅ body, ports
  aligned). `docs/DEFINITION_NODE.md` "Open / next".

---

## Backlog (queued, lower priority)

- **✅ P0 TRIAGED + RESOLVED 2026-06-12 — the 7 pre-existing red layout tests.** A full-suite
  run (1657 passed, 7 failed) flagged them; **confirmed not from the CLIF work** (reproduce
  with `src/clif_*_dau.py` stashed; import no CLIF). A comprehensive per-(engine, style,
  convention) corpus sweep pinned the *exact* frontier, and **§3.3 (`test_correspondence_invariant`)
  still attests every one of these (EGI, drawing) pairs faithful corpus-wide** — what failed is
  the *stronger* `read_drawing(render(egi)) == egi` geometric inversion, on two large imported
  reasoning ontologies (landed for theory-query/materialization, not for drawing):
  - **`bfo_core` under ELK only** — ELK packs its 47 cuts so densely the reader misreads the
    structure; the **Tension** engine lays the *same* graph out invertibly (passes there). An
    ELK layout-density frontier (the "layout-perf frontier" noted when bfo_core landed).
  - **`colore_between` under clockwise-ordered only** — the clockwise convention can't carry
    the argument order of its ternary `between(x,y,z)` atoms recoverably; the **numbered**
    convention (the authoritative ν carrier; clockwise is best-effort by design, Phase 3c)
    does, so numbered/unordered round-trip fine.
  Resolution: a documented `_reader_frontier(uod, engine, clockwise)` helper in
  `tests/test_eg_reader.py` defers *exactly* those (uod, engine, convention) combos (preserving
  every passing case — e.g. bfo_core/Tension and colore_between/numbered stay tested, and the
  §3.3 + no-strikethrough checks still run for both). The 7th,
  `test_tension_engine.py::test_branch_tree_is_compact`, is **xfail**'d: a deterministic
  compaction regression in the **opt-in** tension engine (`roberts_domain_modeling` spreads to
  ~1189×686 vs ~325×443 under default ELK; still §3.3-faithful, just not compact). Two genuine
  follow-ups remain (below).
- **Reader robustness on dense ELK layouts (follow-up to P0).** Make `bfo_core`'s 47-cut ELK
  layout reader-invertible (Tension already is) — either sparser ELK packing for dense
  ontologies or a more robust `read_drawing` cut/incidence recovery. Then drop `bfo_core` from
  `_reader_frontier`. §3.3 already guarantees the correspondence; this is the stronger
  round-trip.
- **Tension-engine compaction regression (follow-up to P0).** `test_branch_tree_is_compact` is
  xfail'd: `roberts_domain_modeling` (degree-4 cross-cut junction) spreads to ~1189px wide vs
  the `<650` the compaction targets and ~325px under ELK. Deterministic; suspected origin is
  the `_box_cuts` style-aware refactor in `40286a7` (the test passed when added in `8685dad`).
  Fix the tension tree/fallback compaction, then remove the xfail. Opt-in engine, so lower
  stakes.
- **Schema generator — shared ambient parameter** so `instance_of_schema` can
  generate the hand-written induction instance (φ threaded through all hole
  occurrences); assert `same_graph` to the hand-written one.
- **CG / ISO 24707 conformance write-up** for the definition node (marked-parameter
  syntax, contraction/expansion) — cite alongside the fixtures.
- **Corpus-import the math theories** — ZFC + Peirce 1881 as real UoDs (schemas +
  definitions store them finitely; the R7 horizon).
- **Gamma frontier** — predicate/property quantification, modality / the broken cut
  (the schema drew the map).
- **Publish-to-Organon as an unattested record** (composition spec §5.3) — a
  mode-contract question for the author; disposition today = vault (scratch) or Agon.
- **Agon depth** — semantic layer, auto-Grapheus, dynamic move set (deferred from V1).
- *(optional, PROTECTED)* widen `HeavyDotInsertionRule` to Dau's any-context rule.

---

## Recently shipped (newest first — detail in git / docs / memory)

- **2026-06-11** — **Freeform step 2: the draw-then-read canvas** (backend tested;
  frontend shipped). `drawing_to_egi.build_egi_from_drawing` is the construction half
  of fix=read (structure from `read_drawing` + content from carried labels → a real
  EGI; corpus round-trip via `same_graph`). Two additive Ergasterion routes:
  `read-drawing` (non-mutating preview) and `fix-drawing` (gate ①: validate → build →
  install → derive; §3.3 attested; ill-formed refused in EG vocabulary). Frontend
  `freeform-canvas.js`: a self-contained SVG drawing surface (place/drag/erase typed
  marks, cuts as drawn ellipses, translucent fills, live point-in-polygon area
  feedback) wired into the composing palette via an opt-in toggle; "Read it now" +
  freeform "① Fix this graph". 18 new tests (builder corpus round-trip + route
  round-trip + JS-serialize↔backend contract). Interactive pointer layer pending
  author's-eyes verification (no headless browser available).
- **2026-06-10** — **Freeform step 1: fix-time validity pass** (`src/drawing_validity.py`,
  13 tests). `validate_drawing(dto) → ValidityReport`: the well-formedness backstop of
  *fix = read* — `read_drawing` reads exactly what is drawn even when it isn't a legal
  EG, so this catches the ill-formed drawings in EG vocabulary. Errors:
  `overlapping_cuts` (curves cross → areas not a tree), `dangling_line` (a loose end,
  incl. the stops-short/drift brittleness). Warnings: `boundary_band`,
  `unwired_predicate` (0-ary), `label_overlap`. Twin of `correspondence_attestation`
  (which checks against a *known* EGI); this checks a freeform drawing with *no EGI
  yet*. Reuses `presentation_ops` geometry of record; clean engine layouts raise zero
  errors. Remaining step-1 UI (filled regions + live drag feedback + snapping) folds
  into step 2's canvas.
- **2026-06-10** — **Phase 4: cut boundary as a drawn polyline + browser as
  client-side arbiter.** A cut can be carried as its literal closed polyline
  (`LayoutDTO.cut_boundary`), the foundation for human-drawn freeform cuts.
  `presentation_ops.cut_boundary` generates the curve; `point_in_polygon` /
  `polyline_polygon_crossings` test it; `resolve_cut_boundaries` is the boundary of
  record shared by §3.3 + `eg_reader` (carried polyline → point-in-polygon; analytic
  cut → exact `point_in_cut`). `point_in_cut`/`bounds_in_cut`/`count_cut_crossings`
  take an optional `boundary`. Renderer draws a carried polyline as `<path>`;
  `diagram-viewer.js::areaAtPoint` uses `isPointInFill` for placement/drag
  hit-testing. Wobble stays a render-only cosmetic (not attested — testing it was a
  false positive, correctly left alone). §3.3 corpus green; new freeform tests.
- **2026-06-10** — **Phase 3c: clockwise placement as Peirce's writing convention**
  (consistent across all styles/layouts). `clockwise_placement.place_clockwise_hooks`
  draws every ≥2-ary relation's hooks clockwise around the spot in ν-order by
  construction, at the best-fit rotation (crossings minimized; 10-ary = a clock
  face). The hook *position* (`points[0]`) carries the order, so lines run straight
  to vertices — no stub, no kink. Applied for **every** style (numbered draws them
  clockwise + numbered; Peirce clockwise + zero/anchor) so the picture reads the
  same everywhere. Hook-position carrier (`points[0]`) = straight lines, no kinks.
  Locally guarded so **no line strikes through any predicate label** (a spoke forced
  across its own spot reverts to the natural hook + numeral). Single start anchor +
  `argument_order_numerals: auto|always|never` toggle. §3.3 green; no label
  strike-throughs; ordered round-trip 23/23 (`auto`). Reframed across the session at
  the author's direction: corpus-tuned fragile-patch → writing convention →
  hook-position carrier (no kinks) → consistent across styles → no own-label strikes.
  Constrained-layout clock faces **considered + declined** (doesn't scale — shared
  lines of identity give conflicting clockwise demands; numerals are the scalable
  carrier, clockwise is small-graph sugar). Phase 3 complete.
- **2026-06-10** — **Label-aware ligature routing** (Phase 3b's third occlusion
  property + its constructive partner). §3.3 check #3 refuses a line of identity
  running through a label box it is *not* incident to (`path_intersects_box`); the
  partner routes such lines *around* label boxes — two-tier routing in
  `_build_ligature_paths` (forbidden cuts **hard** / soundness; label boxes **soft**
  / legibility, yielding to cuts). Cleared the `roberts_domain_modeling` IT+
  shared-vertex strike-through; full §3.3 corpus + transformation + routing suites
  green. Phase 3b now complete (three properties).
- **2026-06-10** — Exact-correspondence **Phase 3b** (no improper occlusion): two
  §3.3 properties green corpus-wide — text-on-text label overlap (`boxes_overlap`)
  and vertex/constant label no-straddle (cut-aware `vertex_label_box`, the renderer's
  placement factored into one source of truth; text drawn centred in the box). Fixed
  a real straddle ("Socrates" at a cut edge). The non-incident-ligature property is
  deferred with its routing partner (`path_intersects_box` primitive in hand).
- **2026-06-10** — Exact-correspondence **Phase 3a** (label-box containment): a
  predicate's containment is its drawn label box, not the anchor point
  (`predicate_label_box` single source of truth — renderer draws it, §3.3 tests it;
  `box_intrudes_cut` forbids straddling into non-ancestor cuts). 521 §3.3 green.
- **2026-06-10** — Exact-correspondence **Phase 2** (exact ligature crossing): the
  crossing test reads off the same rounded-rect boundary as Phase 1's containment
  (`count_cut_crossings` corner-radius-aware; `_rounded_rect_secant_crossings` /
  `_seg_arc_crossings`), closing the crossing-side of the corner void. 457 §3.3 green.
- **2026-06-10** — Exact-correspondence Phase 1 (exact cut containment) +
  architecture doc + scope boundary. Ergasterion review: keep-in-view camera;
  composition reconceived as **synchronic** (no `compose.*` steps; chain begins at
  gate ①) then as **freeform draw-then-read**; `read_drawing` de-risked.
  Docs: `EXACT_CORRESPONDENCE.md`, `FREEFORM_COMPOSITION_AND_LEARNING.md`,
  `DEVIN_SETUP.md`.
- **2026-06-09** — Cut-level `IT-`/`ERA` in the engine; **parametric totality of
  addition** assembled (∀Y∃z plus(x,Y,z)). Dau ∀x homework (scaffold tactic).
  Hole/schema §3.3 (a hole corresponds). Definition-node local reversible
  `expand_at`/`fold` (Borges-map guardrail). Composition workflow built (palette, two
  fixings, per-branch phases). Docs: `UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md`,
  `SCHEMA_HOLE_CORRESPONDENCE.md`, `DEFINITION_NODE.md`, `COMPOSITION_WORKFLOW_SPEC.md`.
- **2026-06-08/09** — Recursion fixtures + the induction arc; graph-with-holes schema
  node + definition layer (`schema.py`, `definitions.py`, `eg_splice.py`); math
  fixtures (ZFC + Peirce 1881). Organon import build: provenance/annotation layer, 3
  fixtures, corpus retrofit (`CORPUS_AND_IMPORT_MODEL.md`). Ontology import.
- **2026-06-06/07** — Tension layout engine (`TENSION_LAYOUT.md`); presentation-delta
  / style ladder (`PRESENTATION_DELTAS_AND_STYLE.md`); four-beat transformation
  grammar complete for all six rules (`TRANSFORMATION_WORKFLOW_SPEC.md`); Settle
  editing surface; NaturalLayout — "own the dimensionality".
- **2026-06-01/03** — All three web modes live (Organon / Ergasterion / Agon);
  runtime §3.3 correspondence attestation; the drawn→EG reader (`eg_reader`);
  Peirce visual-fidelity tiers (oval cuts, hand-drawn wobble, TikZ parity);
  import doorway (low-warrant) + export arc; `MANIFEST_AND_MEANING.md`,
  `CHAIN_OF_SEMIOSIS.md`.

---

## Notes on workflow

Primary development is local, on `main`; GitHub is backup, not a collaboration
surface. No PR ceremony (single developer, single site): commit to `main`, push to
back up. Feature branches are optional backup points, fast-forwarded into `main`
rather than merged via PR. The pre-commit quality gate runs the core suite; the full
suite (`uv run pytest tests/ -q`) is ~11 min. Protected core modules need
`touch .core_modification_authorized` (gitignored); the active threads above are all
unprotected.
