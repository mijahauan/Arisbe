# FOLIO on Arisbe — the "Both" evaluation

**Status:** all three increments built and green (2026-06-13); the coverage lever added
2026-06-15 in two halves — the **disjunctive case-split** (refutation) and the **finite-model
finder** (model construction) — taking native coverage 23.0 % → 63.2 %; then 2026-06-17 the
**EPR (Bernays–Schönfinkel) complete decision** took it to **95.1 % at 100 % soundness vs Z3**
(194/204 decided, 0 genuine errors; the remaining 10 are 8 unparsed + 2 non-EPR Skolem-function
entailments). The same finite-model machinery was carried from the FOLIO AST **to the EGI**
(`src/egi_to_fol.py`), so **DLCore's negative half** inherits it: instance non-entailment
coverage 50 % → 75 % at 100 % soundness. Validation split (204 examples) is the
entailment-scorable one (the train split ships no `conclusion-FOL`).

FOLIO (Han et al. 2022, [github.com/Yale-LILY/FOLIO](https://github.com/Yale-LILY/FOLIO))
pairs natural-language premises + a conclusion with **human-authored FOL annotations** and a
three-valued label: `True` (entailed), `False` (the negation is entailed — contradicted),
`Uncertain` (neither). That trichotomy is exactly Arisbe's three-valued stance, which made
FOLIO the right second track of the NL→logic arc (after DL-ReasonSuite's DLCore;
[[project_nl_to_logic_arisbe_as_interpretant]]).

The engine decision was **Both**: score FOLIO with an *authoritative* complete verdict
**and** with Arisbe's *own bounded* reasoner, and report them side by side. The point of the
pair is the honest contrast — a complete decision procedure tells you the right answer; the
bounded reasoner tells you how much of full FOL Arisbe's native machinery can decide *without
ever erring*.

Run it:

```bash
# Authoritative Z3 verdict (accuracy vs gold)
uv run python tools/folio_benchmark.py --data <FOLIO>/data/v0.0/folio-validation.jsonl
# FOL → EG picture + linear↔graphical round-trip fidelity
uv run python tools/folio_benchmark.py --data … --fidelity
# Arisbe's own bounded engine (soundness × coverage)
uv run python tools/folio_benchmark.py --data … --native
```

The dataset is **not vendored**; point `--data` at a FOLIO checkout.

---

## Increment 1 — the authoritative Z3 verdict

`src/folio_fol.py` is a small recursive-descent parser for FOLIO's FOL syntax
(`∀ ∃ ¬ ∧ ∨ → ↔ ⊕` + constants + n-ary predicates) and a **direct** compiler to Z3.
Compiling straight to Z3 — rather than through Arisbe's `EG→FOPL` string, which drops
quantifier scope to free variables — is deliberate: the EG is for the *pictures* (increment
2), not the verdict. The decision is sound and complete (for FOLIO's small instances):

```
entailed   (True)       ⟺  (⋀premises ∧ ¬conclusion) is UNSAT
contradicts(False)      ⟺  (⋀premises ∧  conclusion) is UNSAT
otherwise  (Uncertain)
```

**Validation (204): accuracy 91.2 %, parse coverage 96.1 %** (recall T/F/U = 88/90/96 %). Of
10 disagreements, 9 are X→Uncertain (conservative) and **zero are True↔False flips**. The
~4 % unparsed (comma-as-conjunction, decimal constants, unbalanced parens) abstain as
`Unparsed`, never guessed. Tests: `tests/test_folio_fol.py`.

---

## Increment 2 — the pictures + linear↔graphical fidelity

`folio_fol.ast_to_clif` + `folio_fol_to_egi` render a FOLIO formula as CLIF
(`⊕ → ¬(a↔b)`) and parse it through `clif_parser_dau` into an EGI — the drawable picture.
`tools/folio_benchmark.py --fidelity` then tests the `egi → CLIF → egi` round-trip via
`same_graph`.

**Validation (1288 formulas): built 99.3 % (0 build failures), round-trip exact 85.5 %.**
The round-trip is exact for the EG-native connectives (`∧ ¬ → ∀ ∃`); `∨ / ↔ / ⊕` build but
expand to De Morgan cuts that re-emit *equivalently, not identically* — a real
correspondence boundary, reported rather than hidden.

---

## Increment 3 — Arisbe's own bounded engine (the soundness × coverage half)

`src/folio_native.py` decides FOLIO entailment with Arisbe's *native* machinery — the Horn
materializer (`model_materialization`), the freeze-a-witness theory query (`theory_query`),
and the denial-based consistency check (`dl_reasoning.check_consistency`) — and reports it
the way the DLCore track taught us a *bounded* reasoner deserves: **soundness** (1 −
wrong/decided, must be 1.0) and **coverage** (decided/total), with abstentions counted as
coverage the fragment doesn't reach, **not** as errors.

### The decision

Both directions reduce to one sound primitive:

```
M ⊨ C    ⟺   M ∪ {¬C} is unsatisfiable        (predict True)
M ⊨ ¬C   ⟺   M ∪ { C} is unsatisfiable        (predict False)
```

and unsatisfiability is detected **soundly but incompletely**: materialize the Horn fragment
of the combined theory to its least Herbrand model and test whether any **denial**
(`~[ A… ]` — a disjointness / negative constraint) fires. A denial satisfied in the least
model is violated in *every* model, so the inconsistency is genuine; and because it uses only
a *subset* of the axioms (the Horn rules + the denials), an inconsistency it finds is a real
inconsistency of the whole combined theory — sound regardless of the non-Horn residue it
skipped. Universal/subsumption conclusions (`∀x B(x)→H(x)`) carry no denial to fire, so the
freeze-a-witness `theory_query.entails` recovers them (the same sound + Horn-complete decision
DLCore subsumption uses).

Originally this prover **never predicted `Uncertain`** — soundly certifying "neither C nor ¬C
is entailed" needs more than refutation. The **model-construction lever** (below) supplies it:
a finite model of `M ∪ {¬C}` *and* one of `M ∪ {C}` together certify `Uncertain` soundly. Where
even that bound is exceeded, the engine still abstains (`Unknown`) — decide what it can prove or
model, abstain on the rest.

### Three things that had to be right (the bugs the build surfaced)

The premises + conclusion are compiled to an EGI **directly** (`_build`), not via CLIF/EGIF
text, because three subtleties of the text path are silent soundness traps:

1. **Constants are real constants.** `clif_parser_dau` has no notion of a Dau constant — it
   reads every term as a generic line of identity. The direct builder makes a FOLIO constant
   a single shared `is_generic=False` vertex on the sheet (matched only by itself), so an
   existential's generic witness can't spuriously match a constant atom.
2. **No variable collapse.** Conjoining premises as `(and …)` and parsing makes
   `parse_clif` unify every premise's `∀x` into one line of identity — fusing distinct
   premises. Direct building gives each quantifier its own vertex, so the collapse cannot
   arise (no alpha-renaming needed). This is the same correctness bug the CLIF *importer*
   fixes with `_disambiguate_variables`.
3. **Existential-under-negation guard.** `check_consistency` reads every sheet-level cut
   `~[ A… ]` as a **universal** denial `∀ ¬(A…)`. That holds for a disjointness axiom
   (`∀x ¬(A∧B)`, `x` universal) but **not** for an existential witness under a negation
   (`∃x (P(x) ∧ ¬Q(x))`, where `~[Q(x)]`'s `x` is a witness, not a universal) — reading it
   universally lets it fire against an unrelated individual, a false inconsistency. A
   polarity-aware guard (`_denial_reading_unsound`) abstains the refutation direction whenever
   the combined theory carries a negated atom over an existentially-bound variable. The
   freeze-witness path (which checks a derived *head*, never a denial) is unaffected.

A meaning-preserving `normalize` pass turns the dominant FOLIO disjointness idiom
`A → ¬B ≡ ¬(A∧B)` (plus exportation and conjunctive-head splitting) so those premises build
as the flat denials the materializer fires on.

### The result

**Validation (204): SOUNDNESS 100.0 % vs Z3 (129/129 decided agree with the complete oracle),
COVERAGE 63.2 % (129/204 decided)** — with **both** levers below enabled (23.0 % / 47 with
neither; 28.9 % / 59 with case-split alone). No native verdict that commits to True / False /
Uncertain ever disagrees with Z3. Against FOLIO's *gold label*, 120 / 129 match and the **9
disagreements are all gold-noise** — Z3 (the complete checker) corroborates the native verdict
on every one (they are the same conservative `X → Uncertain` annotation errors increment 1
found). **Zero genuine errors.** The confusion: gold-True → 34 True / 5 Uncertain, gold-False →
25 False / 4 Uncertain, gold-Uncertain → **61 Uncertain / 0 True / 0 False** (was 0 decided).
The 75 abstentions are the residue genuinely beyond the engine's bound (later cut to 10 by the
EPR lever below). Tests: `tests/test_folio_native.py` (21) + `tests/test_folio_model_finder.py`
(14, incl. the EPR decision) + `tests/test_egi_to_fol.py` (14, the EGI bridge) +
`tests/test_dl_reasoning.py` (15, incl. the model-certified negative half).

> **Why soundness is judged against Z3, not gold.** Once the engine soundly decides
> `Uncertain`, it surfaces FOLIO's known gold-vs-FOL noise. The honest soundness claim is
> against the *FOL semantics*: every decided native verdict agrees with the complete decision
> procedure (Z3). Independently of Z3, the model finder's own `satisfies` guard guarantees each
> returned model genuinely satisfies the parsed FOL — so soundness does not *depend* on Z3; Z3
> merely confirms it empirically. `tools/folio_benchmark.py --native` runs this cross-check.

This is the headline the "Both" decision exists to produce, beside Z3's complete 91.2 %: a
**bounded reasoner over a full-FOL benchmark that decides a clear majority and never errs.** It
is the same story DL-ReasonSuite DLCore told (soundness 100 %, coverage 67 % over 3620 tasks),
now over natural-language-grounded full first-order logic instead of description logic.

### The disjunctive case-split lever (built 2026-06-15)

The original Horn-rules-plus-denials fragment cannot reach an entailment that genuinely needs
**reasoning by cases** — `P∨Q, P→R, Q→R ⊢ R` (the constructive dilemma): each disjunct forces
`R`, but no single denial fires. The lever (`folio_native._refutes_cases`) adds the tableau
β-rule on top of the closure: `M ∪ {A∨B}` is unsatisfiable **iff** `M ∪ {A}` and `M ∪ {B}`
both are, so a top-level disjunction is split and *every* branch must close at the sound
Horn+denial primitive `_refutes`. It branches `∨`, and `⊕` / `↔` via their two models
(`A⊕B ≡ (A∧¬B)∨(¬A∧B)`; `A↔B ≡ (A∧B)∨(¬A∧¬B)`); a split budget (`MAX_CASE_SPLITS`) bounds the
search and `all(...)` short-circuits on the first branch it cannot refute.

**Soundness is preserved by construction** — the branches are exhaustive given the disjunctive
conjunct holds, so all-branches-refuted ⇒ the whole refutes; one branch left open ⇒ abstain
(it does *not* over-decide a genuine Uncertain). It splits only **top-level** disjunctions:
a disjunction trapped under a universal (`∀x (P(x)∨Q(x))`) is *not* `(∀x P) ∨ (∀x Q)`, so it
is left to the residue rather than split unsoundly. Lift: **+12 examples (47 → 59), soundness
held at 100 %.**

### The model-construction lever (built 2026-06-15)

Case-split raises the **refutation** (entailment) half. The dual question — soundly certifying
`Uncertain` (neither `C` nor `¬C` is entailed) — needs the opposite capability: **exhibit a
model**. `src/folio_model_finder.py` is a bounded finite-model finder (Arisbe's own, *not* Z3):

```
M ⊭ C   is witnessed by a model of  M ∪ {¬C}      (premises hold, conclusion fails)
M ⊭ ¬C  is witnessed by a model of  M ∪ { C}      (premises hold, conclusion holds)
both models exist                    ⇒  Uncertain (neither entailed — and the two models prove it)
```

Finding a model is a **positive certificate** — sound however incomplete the entailment prover
is; *failing* to find one certifies nothing, so the finder only ever yields `Uncertain` /
non-entailment, never an entailment. FOLIO's fragment is function-free relational FOL (no
equality), so a finite model is a finite domain + a predicate extension. It is found the
MACE way: domain = the constants (**distinct** — a sound unique-names restriction) + a few
anonymous witnesses for existentials; **ground** every quantifier over that domain (`∀`→∧,
`∃`→∨); **Tseitin → CNF → DPLL** (a small home-grown solver). A satisfying assignment is the
model; the true ground atoms are the predicate extension. An independent `satisfies` evaluator
re-checks every found model against the original FOL before it is trusted — the guard the
`Uncertain` verdict's soundness rests on. Bounded by an anonymous-witness cap + a DPLL node
budget; on exhaustion it abstains (`Unknown`).

**Lift: coverage 28.9 % → 63.2 % (59 → 129), soundness held at 100 % vs Z3** — it decides 61 of
69 gold-`Uncertain` examples (0 before) with zero over-firing on the entailed ones.

### The EPR complete-decision lever (built 2026-06-17)

The 75 abstentions the two 2026-06-15 levers left split sharply: **61 were gold-True/False the
engine could not *refute*** (a disjunction trapped *under* a universal — `∀x(P(x)∨Q(x)),
∀x(P→R), ∀x(Q→R) ⊨ ∀x R` — which the top-level case-split cannot reach), and only 6 were
gold-Uncertain needing a bigger model search. So the headroom was in **refutation**, and the
sound way to it is a classical observation: FOLIO is **function-free relational FOL without
equality**, so a sentence whose prenex prefix is `∃*∀*` (no existential in the scope of a
universal — Skolemization yields only constants, no functions) is in the **Bernays–Schönfinkel
(EPR) class** and has the *finite-model property* with a model of size ≤ |constants| +
|∃-quantifiers|. Grounding it over exactly that bound is therefore a **complete** propositional
decision:

> grounded formula UNSAT (DPLL) ⟺ the FOL sentence is unsatisfiable.

`folio_model_finder.decide_epr` reuses the finder's own grounder + Tseitin + DPLL to return
`"sat"`/`"unsat"` for the EPR fragment, or `None` (abstain) for a non-EPR shape (∃-under-∀,
which would need a Skolem function and an infinite Herbrand universe) or a domain over the
budget. No-equality is also what makes the grounder's **unique-names** assumption sound here: a
satisfiable equality-free sentence always has a model with all constants distinct (duplicate
the shared element), so UNA-UNSAT ⟺ UNSAT. `decide_native` calls it **last** (after the cheaper
Horn / case-split / freeze-witness / model-construction paths), so it purely *adds* coverage on
the residue and tags those verdicts `via="epr"`.

**Lift: coverage 63.2 % → 95.1 % (129 → 194), soundness held at 100 % vs Z3** (every EPR verdict
agrees with the complete oracle; the harness cross-checks). The earlier "raise the model bound"
lever proved unnecessary — EPR subsumed the structured headroom, including the gold-Uncertain
cases (both `M∪{¬C}` and `M∪{C}` come back `"sat"` ⇒ a complete, sound `Uncertain`). What still
abstains: 8 **unparsed** (parser limits, not reasoning) + 2 genuine **non-EPR** entailments
(`∃`-under-`∀` → a Skolem function the bounded engine does not introduce) — honest abstention.

### The bridge to the EGI — DLCore's negative half (built 2026-06-17)

The finite-model machinery was carried from the FOLIO `Formula` AST **to any EGI** by
`src/egi_to_fol.py` — the **read-only** inverse of `folio_native._build` (cut → ¬, juxtaposition
→ ∧, generic vertex → ∃ at its home area, constant vertex → a free term). It only *observes* the
immutable graph; it never mutates and is wholly outside the transformation calculus (the same
posture `model_materialization` / `theory_query` / `semantic_game` take). Faithfulness is pinned
by Z3: the formula read back from `_build(φ)`'s EGI is logically equivalent to φ
(`tests/test_egi_to_fol.py`).

With that bridge, `dl_reasoning` gains the **negative half** the Horn engine could only abstain
on: `check_instance` now **exhibits a model of `M ∪ {¬C(a)}`** to certify non-entailment (`a` is
not a `C`), and `check_consistency` can **exhibit a finite model of M** to certify consistency (a
real model is a real model — sound even past the non-Horn residue). The unique-names restriction
is sound for Arisbe EGIs by construction — identity is the shared *line* (the same vertex), never
an equality atom between two named constants, so M cannot force two distinct constants equal —
and it is surfaced in the verdict's detail.

**Measured on DL-ReasonSuite (100 % soundness throughout — 0 wrong):**

| task | before | after |
|------|--------|-------|
| instance_check | 50 % (entailed only; abstains on every `not_entailed`) | **75 %** (countermodels decide the `not_entailed` cases within the bound) |
| consistency | dl 100 % · el 60 % | unchanged in-sample — the abstainers exceed the finder's domain cap |
| subsumption | 100 % | 100 % (positive half, freeze-a-witness) |

The instance-check lift is the headline: half the previously-abstained `not_entailed` cases now
decide soundly. What still abstains (larger ontologies, more individuals than the finder's
domain bound) is the **runtime-bounded frontier** — raising the bound trades coverage for an
exponential model search, so it is left as an explicit, honest boundary rather than pushed
speculatively.
