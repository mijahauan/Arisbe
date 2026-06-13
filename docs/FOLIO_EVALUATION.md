# FOLIO on Arisbe — the "Both" evaluation

**Status:** all three increments built and green (2026-06-13). Validation split (204
examples) is the entailment-scorable one (the train split ships no `conclusion-FOL`).

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

It **never predicts `Uncertain`**: soundly certifying "neither C nor ¬C is entailed" needs a
completeness the bounded fragment doesn't have over full FOL, so the honest move is to abstain
(`Unknown`). This is exactly the DL instance-checking shape — decide every entailment /
contradiction it can prove, abstain on the rest.

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

**Validation (204): SOUNDNESS 100.0 % (47/47 decided correct), COVERAGE 23.0 % (47/204
decided).** The confusion is clean — gold-True → 27 True / 0 False, gold-False → 20 False / 0
True, gold-Uncertain → 0 decided. The 157 abstentions are principled: non-Horn premises
(disjunction, `⊕`, existential-under-negation) and every `Uncertain` gold (which the bounded
fragment can never soundly decide). **Zero unsound verdicts.** Tests:
`tests/test_folio_native.py` (16).

This is the headline the "Both" decision exists to produce, beside Z3's complete 91.2 %: a
**bounded, sound reasoner over a full-FOL benchmark — it abstains, it never errs.** It is the
same story DL-ReasonSuite DLCore told (soundness 100 %, coverage 67 % over 3620 tasks), now
over natural-language-grounded full first-order logic instead of description logic.

### The coverage lever (the real extension, deferred)

Coverage is bounded by the Horn-rules-plus-denials fragment. The principled way to raise it —
not a bugfix — is a **disjunctive / model-construction** capability (case split on `∨` and
`⊕`, or an explicit closed-world / refutation-search mode) for the FOLIO instances whose
entailment genuinely needs reasoning by cases. That is the FOLIO twin of DLCore's deferred
"refutation / model-construction for the negative half" lever.
