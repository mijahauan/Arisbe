# The linear-form round trip: making it total

**Date:** 2026-09-08 · **Status:** specification, nothing built · **Authorized by the author**

> "The integrity of our system relies on demonstrable round-trip equivalence of
> these linear forms of an EGI. It needs definitive fixing."

---

## 1. What is broken, measured

Across the 52 corpus UoDs, each generated to EGIF, CGIF and CLIF and parsed
back, compared by `same_graph` (isomorphism in Dau's sense, not text equality):

| | holds | fails |
|---|---|---|
| EGIF | ~41 | **9** |
| CGIF | ~19 | **30** |
| CLIF | ~23 | **25** |
| **total** | **83** | **64** |

Six more are correctly refused as the second-order limit. `sumo_upper` is
excluded: `same_graph` does not finish on it in reasonable time, which is a
finding of its own (§6).

The numbers are recorded in `tests/test_tomos_parsing.py::KNOWN_BROKEN`, so a
fix announces itself as an unexpected pass rather than needing to be noticed.

## 2. How it went unmeasured

`tests/test_tomos_parsing.py` pointed `CORPUS_ROOT` at `corpus/corpus`, a path
that stopped resolving when the corpus was renamed to `tomos` (`b24ce9d`,
2025-10-14). Its three tests globbed for `*.egif` / `*.cgif` / `*.clif`, got an
empty list, and `@pytest.mark.parametrize` over an empty list yields **zero
tests rather than an error**. Three silent skips inside a green suite of
thousands, for eleven months, while CLAUDE.md, the capability map and the draft
letter to Sowa all cited this file as the guarantee.

The failure mode worth naming: **a test that derives its cases from the
filesystem fails open.** A path that stops resolving is indistinguishable from
a suite with nothing to do.

The project had already been bitten and had worked around it locally.
`live_runner.py:340` carries M as structural JSON rather than EGIF text, and
says why: *"That one parse is where the text round-trip's constant-merge can
still bite, so such a run may see a decay skipped and counted."* The defect was
diagnosed as a run-specific finding (F2¹³) and routed around; the general case
was never chased.

## 3. The root cause, and it is one

The nine EGIF failures split into two symptoms of a single deficiency.

**A — constant merge (6 cases).** The vertex count *drops* on re-parse, by
exactly the number of repeated constants: `would_be_courses` 5→2,
`dialogue_model_revision` 5→3, `dialogue_swan_revision` 6→5,
`agon_evolution_swan` 6→5, `episode_discharge` 3→2,
`arithmetic_from_two_laws` 13→12. Two occurrences of one constant name in
different areas become one vertex.

**B — vertex depth shift (3 cases).** V, E and Cut counts are identical but a
vertex sits at a different depth: `roberts_1973_p57_disjunction` 1→2,
`bfo_core` one vertex 3→2, `colore_field` two vertices 3→2.

Both are the same thing said twice: **the linear form does not record where a
constant's line of identity lives.** A generic vertex is introduced by its
defining occurrence `*x`, which fixes its area. A constant has no defining
occurrence, so the parser must infer the area — and interning at first mention
is the wrong inference whenever the line actually sits further out, or whenever
two same-named constants are genuinely distinct lines.

`roberts_1973_p57_disjunction` is the clean specimen:

```
corpus    ~[ [x] ~[ (P "x") ] ~[ (Q "x") ] ]   constant at depth 1, spanning both disjuncts
emitted   ~[ ~[ (P "x") ] ~[ (Q "x") ] ]        the position is simply not written
reparsed  constant at depth 2, inside one disjunct
```

Same vertex count, same edge count, byte-identical canonical text on
re-emission — and a different graph. This is why text-stability checks pass it
and only isomorphism catches it.

## 4. The governing question, answered

**R1 is settled by the author (2026-09-08):**

> "A line of identity between two cuts, as would obtain in `(P "x")` and
> `(Q "x")`, traverses their least common area only. I believe Dau resolved
> this."

So the position is not missing from the linear form — it is **derivable**. A
constant's vertex belongs in the *least common area* of the areas its
occurrences sit in. Nothing needs to be written that is not already written;
the parser simply has to compute it instead of guessing.

Verified against the corpus — for every shared constant, the stored vertex is
already at the least common area of its occurrences:

| UoD | constant | vertex at | LCA of occurrences | |
|---|---|---|---|---|
| `roberts_1973_p57_disjunction` | `"x"` | depth 1 | depth 1 | matches |
| `dialogue_model_revision` | `"Ann"` | depth 2 | depth 2 | matches |
| `would_be_courses` | `"Clara"` | depth 2 | depth 2 | matches |

**The corpus is right and the parsers are wrong.** They intern a constant at
its first mention; they must place it at the least common area of all its
mentions. That single rule addresses both symptoms in §3 — the merge (two
same-named constants whose LCA is computed rather than assumed identical) and
the depth shift (`roberts`: first mention puts it at depth 2, the LCA puts it
at depth 1, which is where the corpus has it).

**Consequences for the arc.** This is no longer a question of standards
conformance, and there is no risk of an EGIF extension needing to be argued
with Sowa. It is a defect in three parsers, with the correct behaviour already
specified by Dau and already exhibited by the corpus. Arisbe also already has
the machinery: `presentation_ops.area_chain` computes the allowed areas
including the LCA.

## 5. CLIF has defects of its own

Beyond the shared root cause, CLIF shows three that look independent, each
verified by hand:

1. **A constant is re-read as a bound variable.** `(P "x")` returns as
   `(exists (x) (P x))` — `roberts_1973_p57_disjunction`.
2. **A quantifier flips.** `(exists (x) …)` returns as `(forall (x) …)` —
   `sibling_cuts_shared_variable`. This is a **soundness** defect, not a
   formatting one, and it should be treated as the most urgent item in the arc.
3. **A spurious double negation** appears around the body — `barbara`.

## 6. Fixed already, in passing

The CGIF parser accepted a quoted referent in a typed concept
(`[Human: Socrates]`) but not in an untyped one (`[: "0"]`), while the
generator emits untyped constants quoted. So generated CGIF would not re-parse
at all for `arithmetic_from_two_laws` and `peirce_order_1881`. ISO/IEC 24707
permits the quoted form; the parser now accepts it. **Hard parse failures: 2 → 0.**

## 7. Method

Nothing is fixed before it is falsified.

1. **Isolate each cause with a minimal failing test** — a hand-written pair
   (graph, expected round trip) small enough to read, not a corpus UoD. The
   corpus tells us *that* something is wrong; a minimal case tells us *what*.
2. **Settle §4** — the standards question — and record the answer with a
   citation, since it decides whether this is a fix or a documented limit.
3. **Fix in order:** the CLIF quantifier flip first (soundness), then the
   shared root cause, then the remaining CLIF defects, then CGIF.
4. **`KNOWN_BROKEN` shrinks with each fix**, and the suite reports an
   unexpected pass if a fix lands without the list being updated.
5. **Acceptance:** `KNOWN_BROKEN` is empty, 147 of 147 round-trips hold, and
   the claim in CLAUDE.md and the capability map is restored to an unqualified
   one — or, if §4 says the format cannot carry the information, the limit is
   documented, tested, and the claim is narrowed to what is true.

## 8. Also in the blast radius

Checked while mapping the rename:

- `corpus/` still exists and is **live** — 15 files of source material
  (`.ttl`, `.ofn`, `.clif` ontologies and domain models) referenced correctly
  by `tools/build_ontologies.py`, `test_rdf_import.py`, `test_grapheus.py` and
  others. Only `test_tomos_parsing.py` was stale.
- `tests/test_it_minus_dau_compliance.py` is **zero bytes** and collects
  nothing. Emptied in "Clean up orphaned code and stabilize test suite", not by
  the rename, but it is the same failure class: a name that promises coverage
  with nothing behind it. IT− compliance *is* covered by
  `test_it_minus_with_isomorphism.py`, so the fix is to delete the empty file
  rather than to write into it.
- No other test file collects zero, and the one sibling that parametrizes over
  a glob collects 104 tests.
- **`same_graph` does not finish on `sumo_upper`** (86 edges, 26 relations) in
  five seconds. The isomorphism oracle is the correctness authority for
  challenge grading, drawing→EGI and this arc; that it has a practical size
  ceiling deserves its own investigation.

## 9. Open questions

- **R1.** *Answered* — see §4. A line of identity traverses the least common
  area of its occurrences; the position is derivable and the parsers must
  compute it.
- **R2.** Should two same-named constants in different areas ever be *merged*?
  If a corpus graph distinguishes them, is that graph well-formed, or is the
  merge the correct reading and the corpus wrong?
- **R3.** *Addressed 2026-09-08, ahead of this arc.* See §10.
  ~~The `same_graph` size ceiling looks worse than first measured:~~
  `same_graph(bfo_core, bfo_core)` — the oracle against *itself*, 24 vertices,
  52 edges, 50 cuts — did not return within 600 seconds. Reflexivity is the
  cheapest possible case. Every use of the oracle rests on this: challenge
  grading, drawing→EGI, this arc's own acceptance test. Its own arc, and
  arguably ahead of this one, since this arc cannot be *verified* without it.


---

## 10. R3 addressed: the oracle answers again

**The defect.** `GraphIsomorphismEngine._node_match` distinguished cuts only by
`quoted` and generic vertices only by label and sort. In `bfo_core` that made
all 50 cuts mutually interchangeable and all 24 generic vertices likewise, so
VF2 searched a factorial space pruned only by edge structure as it descended.
The symptom was not a wrong answer but **no answer**: `same_graph(bfo_core,
bfo_core)` — the oracle against itself, the cheapest possible case — did not
return within 600 seconds, and `sumo_upper` never finished.

**The fix.** Attach the Weisfeiler-Leman colours that `canonical_signature`
already computes for the generators, and require them to match. On `bfo_core`
they distinguish 24/24 vertices, 50/50 cuts and 49/52 edges where the matcher
previously distinguished none. Colour equality is an isomorphism invariant, so
it prunes only candidates that could never have matched; VF2 still performs the
real test.

| | before | after |
|---|---|---|
| `bfo_core` (24V/52E/50Cut) | > 600 s, no answer | **0.027 s** |
| `sumo_upper` (43V/86E/89Cut) | never finished | **0.075 s** |
| `colore_field` (59V/46E/31Cut) | — | 0.031 s |

Authorized by the author; `graph_isomorphism_engine.py` is a protected module.
Guarded by `tests/test_isomorphism_scale.py`: reflexivity on the large graphs
within a time budget, reflexivity across the whole corpus, and eight
discrimination cases confirming the pruning costs no verdict.

**Why it mattered here.** This arc's acceptance criterion is "147 of 147
round-trips hold", judged by `same_graph`. It was not measurable before.

## 11. Found while fixing it: a drawing→EGI incidence defect

With the oracle working, `bfo_core` still fails the drawing→EGI round trip, so
it is a real defect rather than an artifact. `legible_diff` names it exactly —
six **incidence** findings, all on unary relations sharing a line of identity:

```
IndependentContinuant        connects (line 1, line 1)  but should connect (line 1)
GenericallyDependentContinuant connects ()              but should connect (line 1)
SpecificallyDependentContinuant connects ()             but should connect (line 20)
```

The reader mis-attributes hooks when several unary predicates sit on one line.
Distinct from the linear-form cause, and its own arc.

**How it hid.** `test_drawing_to_egi._corpus_egis` took `list_uods()[:14]` —
the first fourteen in index order — while the test's docstring said "for each
corpus UoD". Which fourteen depended on how the index happened to be written,
so rebuilding the index changed the sample and the failure surfaced. The test
now covers the whole corpus (48 UoDs per style), with the second-order UoDs and
`bfo_core` excluded by name and reason, and asserts that it checked at least 45.

That is the third test in this session found to under-cover silently: a glob
that matched nothing (§2), a zero-byte file (§8), and a sample of fourteen
claiming to be a sample of all. The common shape: **coverage derived from
incidental state, with no assertion about how much was covered.**
