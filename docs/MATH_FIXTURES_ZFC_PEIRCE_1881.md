# EGIF Fixtures — ZFC and Peirce's 1881 Arithmetic

**Status:** built (2026-06-09). **Part I (7 ZFC axioms) and Part IV
(P1–P6 Peirce) are validated against Arisbe's parser** — all 13 parse and
round-trip (parse → generate → parse, (V,E,Cut) preserved). **Both new
capabilities are now built (all unprotected):** the **definition layer**
([`src/definitions.py`](../src/definitions.py)) and the **graph-with-holes /
schema node** ([`src/schema.py`](../src/schema.py)), both layered on a shared
graph-splice primitive ([`src/eg_splice.py`](../src/eg_splice.py)). The schema
fixtures (Part II Separation/Replacement, P7 induction) parse as `Schema`s and
instantiate to hole-free Beta graphs. The parser-exact canonical EGIF lives in
[`tests/test_math_fixtures.py`](../tests/test_math_fixtures.py); deep coverage in
[`tests/test_definitions.py`](../tests/test_definitions.py),
[`tests/test_schema.py`](../tests/test_schema.py),
[`tests/test_eg_splice.py`](../tests/test_eg_splice.py). The consistency contract
(Dau · Common Logic · CGIF · FOPL) is **Part III-bis** below.

**Validation outcome (2026-06-08) — two adjustments from this brief's notation:**
1. **Bound labels are bare `x`, not `?x`.** Arisbe EGIF writes a defining label
   `*x` and a bound use `x`; the `?` prefix is this brief's own convention. (The
   canonical forms in the test use bare labels.)
2. **Equality is `(= a b)`, Dau's identity edge — not the coreference bracket
   `[a b]`.** Checked against Dau, *Mathematical Logic with Diagrams*, Ch. 11:
   "Vertices will denote objects, and the identity relation is formalized by
   edges. Identity is a special dyadic relation … captured by 2-ary edges,
   labeled with the special relation name `=`." Dau explicitly *refines away* the
   "two coincident points merge into one line" reading; `egi_core_dau` keeps `x`
   and `y` as distinct vertices joined by a `=`-labeled edge. This is also exactly
   what the shipped `group_identity` fixture builds, and it round-trips to CLIF
   `(= a b)`. The EGIF **lexer** was updated (protected change) to read `=` as the
   special relation name — the generator already *emitted* `(= x y)`, so this
   closed a latent generator↔parser round-trip gap. Every `[a b]` / `[?x ?y]`
   below should be read as `(= a b)`.

This is the natural continuation of the Organon-import arc
([CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md)) into real mathematics.
Two pieces connect it to what's already built:

- The **definition layer** below is the term-level twin of the derived-rule layer
  already shipped in [`src/derived_rules.py`](../src/derived_rules.py) (named moves
  atop Peirce's primitives). `(subset …)`, `(succ …)`, `(plus …)` are named graphs
  the way `universal_instantiation` is a named rule.
- The **graph-with-holes / schema node** (Part III) is genuinely new: it is what
  lets Beta store ZFC's Separation/Replacement and Peirce's induction as *finitely
  many* hole-bearing graphs + one instantiation routine + one side-rule. First-order
  EG cannot quantify over formulas, so a schema cannot be a single ordinary graph.

The fixtures are also the first real exercise of the equality-as-ligature decision
settled this session (R8: equality is a shared line / `=` edge, not a dyadic
predicate; constants intern per-area, so a named individual referenced across cuts
is a shared *generic* line). Every `[a b]` below is that ligature.

---

## Conventions

- **Membership** `x ∈ y`  →  relation `(in x y)`
- **Equality** `x = y`  →  `(= x y)`, Dau's special dyadic identity relation
  (a 2-ary `=` edge; Ch. 11). This is what Arisbe's parser reads and what CLIF
  `(= a b)` round-trips to. *(This brief originally proposed the coreference
  bracket `[a b]`; see the Validation outcome above for why the `=` edge is the
  Dau-faithful choice.)*
- **Cut / negation**  `~[ … ]`  ;  **conjunction** = juxtaposition.
- **Defining label** `*v` introduces a line of identity (existential);
  **bound label** `?v` is a coreference use.
- Derived shapes (all by pushing negation through, normal EG form):
  - `∀x φ`            →  `~[ [*x] ~[ φ ] ]`
  - `∃x φ`            →  `[*x] φ`
  - `∀x (A ⊃ B)`      →  `~[ [*x] A ~[ B ] ]`
  - `A ∨ B`           →  `~[ ~[ A ] ~[ B ] ]`
  - `A ↔ B`           →  `~[ A ~[ B ] ]  ~[ B ~[ A ] ]`   (two implications, juxtaposed)

The ONLY nonlogical vocabulary in Part I–III is `(in …)` plus the equality
ligature. In Part IV it is `(lt …)` plus the equality ligature.

---

## Part I — ZFC: the seven non-schema axioms (one graph each)

### 1. Extensionality
Sets with the same members are equal.

`∀x∀y [ ∀z(z∈x ↔ z∈y) → x=y ]`

```
~[ [*x] [*y]
   ~[ [*z] ~[ ~[ (in ?z ?x) ~[ (in ?z ?y) ] ]
              ~[ (in ?z ?y) ~[ (in ?z ?x) ] ] ] ]
   ~[ [?x ?y] ] ]
```
Note: the inner `~[ [*z] ~[ … ↔ … ] ]` is the antecedent "x and y have the same
members," sitting in the negative area; the consequent `x=y` is the ligature
`~[ [?x ?y] ]`. No native `↔`, so it expands to the two implications.

### 2. Empty Set
There is a set with no members. (Often derived from Separation + Infinity; kept
here as a standalone fixture.)

`∃x ∀y ¬(y∈x)`

```
[*x] ~[ [*y] (in ?y ?x) ]
```
Note: `~[ [*y] (in ?y ?x) ]` is `¬∃y(y∈x)` = "nothing is in x." Cleanest axiom
in the set.

### 3. Pairing (existence form)
For any x, y there is a set containing both. (Separation later trims it to the
exact pair; the exact-pair version needs the `↔` expansion as in Extensionality.)

`∀x∀y ∃z (x∈z ∧ y∈z)`

```
~[ [*x] [*y] ~[ [*z] (in ?x ?z) (in ?y ?z) ] ]
```
Note: the canonical `∀∀∃` rhythm — two defining labels just inside the leading
cut, one more cut for the existential.

### 4. Union
For any family F there is a set A containing every member of every member of F.

`∀F ∃A ∀x [ ∃B(x∈B ∧ B∈F) → x∈A ]`

```
~[ [*F] ~[ [*A]
   ~[ [*x] [*B] (in ?x ?B) (in ?B ?F) ~[ (in ?x ?A) ] ] ] ]
```
Note: the inner `∃B(…)` in the antecedent becomes a `[*B]` alongside `[*x]` under
the same cut — the prenex equivalence `∀x(∃B φ → ψ) ≡ ∀x∀B(φ → ψ)` (ψ free of B)
makes this exact and saves a cut.

### 5. Power Set
For any x there is a set y containing every subset of x.

`∀x ∃y ∀z ( z⊆x → z∈y )`,  where `z⊆x ≡ ∀w(w∈z → w∈x)`

```
~[ [*x] ~[ [*y]
   ~[ [*z] ~[ [*w] (in ?w ?z) ~[ (in ?w ?x) ] ]
            ~[ (in ?z ?y) ] ] ] ]
```
Note: the subset relation is inlined as `~[ [*w] (in ?w ?z) ~[ (in ?w ?x) ] ]`.
This is the first axiom that visibly screams for a defined relation
`(subset ?z ?x)` — see Part III, definition layer.

### 6. Infinity
There is a set I containing the empty set and closed under successor s = x ∪ {x}.

`∃I [ ∃e(e∈I ∧ ∀z¬(z∈e))`
`     ∧ ∀x( x∈I → ∃s( s∈I ∧ ∀w(w∈s ↔ (w∈x ∨ w=x)) ) ) ]`

```
[*I]
  [*e] (in ?e ?I) ~[ [*z] (in ?z ?e) ]
  ~[ [*x] (in ?x ?I)
     ~[ [*s] (in ?s ?I)
        ~[ [*w] ~[ ~[ (in ?w ?s) ~[ ~[ ~[ (in ?w ?x) ] ~[ [?w ?x] ] ] ] ]
                   ~[ ~[ ~[ (in ?w ?x) ] ~[ [?w ?x] ] ] ~[ (in ?w ?s) ] ] ] ] ] ]
```
Note: this is the deliberate monster. `(w∈x ∨ w=x)` is the disjunction
`~[ ~[ (in ?w ?x) ] ~[ [?w ?x] ] ]`, appearing once in each arm of the `w∈s ↔ …`
biconditional. With defined relations `(empty ?e)` and `(succ ?x ?s)` it
collapses to:
`[*I] [*e] (empty ?e) (in ?e ?I) ~[ [*x] (in ?x ?I) ~[ [*s] (in ?s ?I) (succ ?x ?s) ] ]`

### 7. Foundation (Regularity)
Every nonempty set has an ∈-minimal member.

`∀x [ ∃y(y∈x) → ∃u( u∈x ∧ ¬∃z(z∈u ∧ z∈x) ) ]`

```
~[ [*x] [*y] (in ?y ?x)
   ~[ [*u] (in ?u ?x) ~[ [*z] (in ?z ?u) (in ?z ?x) ] ] ]
```
Note: the antecedent's witness `y` and the consequent's minimal element `u` are
distinct bound lines — distinct labels are mandatory.

### (Choice)
For any family of nonempty pairwise-disjoint sets there is a set meeting each in
exactly one element. Stated faithfully it is long; recommended as a defined-relation
fixture (`(pairwise_disjoint ?F)`, `(meets_once ?C ?F)`) rather than raw `in`.
Flagged here, deferred to the definition layer.

---

## Part II — ZFC: the two schemas (graph-with-holes)

Each is ONE hole-bearing graph standing for infinitely many axioms. `⟨φ: ports⟩`
denotes the hole; all occurrences of the same `φ` co-instantiate.

### 8. Separation (Specification) — hole arity 1
For each formula φ(x) (with parameters p̄): the φ-definable subclass of any set A
is a set.

`∀p ∀A ∃B ∀x ( x∈B ↔ (x∈A ∧ φ(x)) )`

```
~[ [*p] ~[ [*A] ~[ [*B]
   ~[ [*x] ~[ ~[ (in ?x ?B) ~[ (in ?x ?A) ⟨φ: ?x⟩ ] ]
              ~[ (in ?x ?A) ⟨φ: ?x⟩ ~[ (in ?x ?B) ] ] ] ]
] ] ]
```
- Hole `⟨φ: ?x⟩`: one port `?x`, TWO occurrences (different depth/polarity).
- φ may use `?x` and parameters `?p`; it may NOT bind `B`, `A`, or `x`.
- Sample instantiation `⟨φ: ?x⟩ := (in ?x ?p)` yields A ∩ p.

### 9. Replacement — hole arity 2
For each formula φ(x,y) functional on A, the φ-image of A is a set.

`∀A [ ∀x( x∈A → ∃!y φ(x,y) )`
`     → ∃B ∀x( x∈A → ∃y( y∈B ∧ φ(x,y) ) ) ]`

```
~[ [*A]
   ~[ [*x] (in ?x ?A) ~[ [*y] ⟨φ: ?x ?y⟩
                          ~[ [*y2] ⟨φ: ?x ?y2⟩ ~[ [?y ?y2] ] ] ] ]   % functionality hyp (∃!)
   ~[ [*B]
      ~[ [*x] (in ?x ?A) ~[ [*y] (in ?y ?B) ⟨φ: ?x ?y⟩ ] ] ] ]
```
- Hole `⟨φ: ?x ?y⟩`: two ports. THREE occurrences here (twice in the `∃!y`
  uniqueness hypothesis, once in the image clause) — and the second port differs
  per occurrence (`?y` vs `?y2`), so the instantiation routine must rename the
  port wiring, not just copy.
- This is the stress case for the hole node: multiple ports, multiple occurrences,
  per-occurrence port relabeling. If the design survives Replacement it survives
  everything.

---

## Part III — The graph-with-holes node (spec for Arisbe)

A **schema** = a Beta graph plus ≥1 holes. A **hole** record carries:

1. **Ports** — an ordered list of line references the plugged subgraph may attach
   to. Arity = |ports|. (Separation 1, Replacement 2, Peirce least-number 1.)
2. **Schema-occurrence id** — every occurrence of the same φ shares one id, so a
   single instantiation fills all of them. Sharing is enforced, not re-derived.
3. **Scope / capture rule** — the plugged graph g must have free lines ⊆ ports ∪
   ambient parameters; g's own `*`-nodes are α-renamed fresh on splice so they
   cannot weld onto schema lines.
4. **Parity independence** — occurrences may sit at different depths/polarities;
   occurrence-equality compares graph CONTENT modulo surrounding cuts.

**Instantiation** `instantiate(schema, g)`:
- check arity(g.free_lines) == arity(ports);
- for each occurrence: copy g, α-rename g's bound labels fresh, weld g's
  port-lines to the schema lines recorded at that occurrence;
- result is an ordinary hole-free Beta graph = one axiom.

**New inference side-rule** `instance-of-schema`: licenses asserting any
`instantiate(schema, g)` when `schema` is on the sheet. This is the *only* new
primitive the schema machinery adds on top of Peirce's five rules. Storing
PA / ZFC = finitely many hole-bearing graphs + this routine + this side-rule.

**Definition layer (companion, strongly recommended):** a named graph
`name(ports) := body` that expands to `body` on demand — the term-level twin of
named lemmas / derived rules. Lets `(subset ?z ?x)`, `(empty ?e)`, `(succ ?x ?s)`,
`(pairwise_disjoint ?F)` stand in for their bodies, which is what makes Power Set,
Infinity, and Choice readable and storable.

---

## Part III-bis — Consistency contract (Dau · Common Logic · CGIF · FOPL)

These two additions must stay faithful to the formalisms Arisbe already
round-trips (EGIF/CGIF/CLIF/FOPL) and to Dau's Beta. They do so for **different
reasons**, and only the definition layer touches the round-trip. Dau's
*Mathematical Logic with Diagrams* formalizes Alpha + Beta as **first-order logic
with identity** plus the six rules; it contains **neither** a definition mechanism
**nor** schemas as object-level primitives (and no Gamma). Both additions are
therefore extensions *on top of* Dau's Beta — but faithful ones, governed by three
rules:

**1. Definitions stay eliminable (a conservative/definitional extension).**
A named graph is *abbreviation only*: it always carries its expansion, and every
defined graph reduces to a Dau-primitive graph. Expansion is the fallback;
**§3.3 attestation and all logic run on the expanded form**, never on the name.
Expressive power is unchanged — Dau's Beta admits this the way FOL admits defined
predicates.
- *CLIF:* a definition `name(p̄) := body` **is** the biconditional
  `(forall (p̄) (iff (name p̄) body))` — handled natively by the existing parser
  (`clif_parser_dau.py` expands `(iff P Q)` to `(and (if P Q) (if Q P))`). Round-trips
  with no new logic.
- *CGIF / Sowa CGs:* conceptual graphs already have a native definition mechanism
  (lambda abstraction defining new type/relation labels). The definition layer
  *adopts* a CG feature EGIF currently lacks — it strengthens the bridge rather
  than strains it.
- *Net on the round-trip:* an **enhancement in fidelity and readability**
  (`(subset …)` survives the trip instead of exploding into raw `(in …)` plumbing),
  with **zero** added power and **zero** risk, because it reduces to what already
  round-trips.

**2. The schema's round-trippable unit is the INSTANCE, not the schema (a
metalevel generator).** A schema cannot be an object-level Beta graph (quantifying
over formulas is beyond Beta), and Common Logic / CGIF are first-order with **no
schema construct** — so a schema must **never** be exported as a single counterfeit
first-order CLIF/CGIF sentence. Instead:
- The schema is an **EG/Arisbe-native object**; the hole token `⟨φ: ?x⟩` is an
  Arisbe extension to EGIF, not standard EGIF/CLIF/CGIF.
- Every `instantiate(schema, g)` **instance** is pure Beta = pure FOL and
  round-trips cleanly through the existing EGIF↔CGIF↔CLIF↔FOPL path.
- CLIF/CGIF *export* of a schema = its instances, or a flagged metalevel object —
  never a fake sentence. This mirrors how Common Logic itself handles ZFC/PA:
  instances are object-level, the schema is metalogical.

**3. Gamma stays the boundary.** Both devices are valuable precisely because they
reach first-order mathematics (ZFC, PA, Peirce 1881) *without* crossing into
Gamma. The moment one would *quantify over* a hole **inside** the logic — rather
than fill it by the external `instance-of-schema` rule — that is Gamma (predicate
quantification), and is deliberately out of scope. The schema device buys ZFC/PA's
reach while keeping every asserted graph in Dau-Beta.

---

## Part IV — Peirce 1881 arithmetic (Shields reconstruction)

Source: C. S. Peirce, "On the Logic of Number," *American Journal of Mathematics*
4 (1881), 85–95. The crisp axiom list is Paul Shields' reconstruction (diss. 1981;
"Peirce's Axiomatization of Arithmetic," in Houser/Roberts/Van Evra eds.,
*Studies in the Logic of C. S. Peirce*, Indiana UP, 1997), proven equivalent to
Dedekind (1888) and Peano (1889). Peirce's naturals = a discrete linear order with
a least element and no greatest; his induction is the least-number principle.

Primitive: strict order `(lt ?x ?y)` for `x < y`. Equality via ligature.

### P1. Irreflexivity
`∀x ¬(x<x)`
```
~[ [*x] (lt ?x ?x) ]
```

### P2. Transitivity
`∀x∀y∀z ( x<y ∧ y<z → x<z )`
```
~[ [*x] [*y] [*z] (lt ?x ?y) (lt ?y ?z) ~[ (lt ?x ?z) ] ]
```

### P3. Trichotomy (linearity)
`∀x∀y ( x<y ∨ x=y ∨ y<x )`
```
~[ [*x] [*y] ~[ (lt ?x ?y) ] ~[ [?x ?y] ] ~[ (lt ?y ?x) ] ]
```

### P4. Discreteness (immediate successor exists)
`∀x ∃y ( x<y ∧ ¬∃z(x<z ∧ z<y) )`
```
~[ [*x] ~[ [*y] (lt ?x ?y) ~[ [*z] (lt ?x ?z) (lt ?z ?y) ] ] ]
```

### P5. Least element (Peirce starts the count at 1)
`∃x ∀y ( x<y ∨ x=y )`
```
[*x] ~[ [*y] ~[ (lt ?x ?y) ] ~[ [?x ?y] ] ]
```

### P6. No greatest element (unboundedness)
`∀x ∃y ( x<y )`
```
~[ [*x] ~[ [*y] (lt ?x ?y) ] ]
```

### P7. Induction = least-number principle — SCHEMA, hole arity 1
For each formula ψ(n): every nonempty ψ-class has a <-least member.

`∀… [ ∃x ψ(x) → ∃u( ψ(u) ∧ ∀y(ψ(y) → ¬(y<u)) ) ]`

```
~[ [*x] ⟨ψ: ?x⟩
   ~[ [*u] ⟨ψ: ?u⟩
      ~[ [*y] ⟨ψ: ?y⟩ (lt ?y ?u) ] ] ]
```
- Hole `⟨ψ: ?n⟩`: one port, THREE occurrences (`?x`, `?u`, `?y`).
- Same hole node as ZFC Separation — Peirce's induction validates the schema
  machinery a second time, on an arithmetic theory instead of a set theory.

### Recursive operations — `+`, `×` as primitive relations + recursion axioms (BUILT)
Peirce gave recursive definitions of `+` and `×` (recursion equations on the
successor, `x + 0 = x`, `x + S(y) = S(x + y)`, and likewise for `×`). **These are
NOT definition-layer entries** — a recursive body never bottoms out, so it is not
an *eliminable* definition (the definition layer's `expand` correctly refuses it).
They are ordinary first-order **(Beta) axioms** constraining new relation symbols
`plus`/`times`, grounded in `succ` (immediate successor) + `zero`. Built and pinned
in [`tests/test_math_fixtures.py`](../tests/test_math_fixtures.py)
(`RECURSION_FIXTURES`):

```
plus_base   ~[ [*x] [*z] (zero z) ~[ (plus x z x) ] ]                                  % x + 0 = x
plus_step   ~[ [*x][*y][*z][*sy][*sz] (plus x y z) (succ y sy) (succ z sz) ~[ (plus x sy sz) ] ]  % x + S(y) = S(x+y)
times_base  ~[ [*x] [*z] (zero z) ~[ (times x z z) ] ]                                 % x · 0 = 0
times_step  ~[ [*x][*y][*p][*sy] (times x y p) (succ y sy) ~[ [*q] (plus p x q) (times x sy q) ] ]  % x·S(y) = x·y + x
```

Reasoning *about* recursively-defined operations uses the **induction schema** (P7);
see [`tests/test_induction_proofs.py`](../tests/test_induction_proofs.py). Gamma is
needed only for the *second-order* recursion theorem (∃! function f …); Peirce 1881
— like first-order PA — sidesteps it exactly this way, taking `+`/`×` as primitives
axiomatized by their recursion equations + induction.

---

## Notes / caveats

- Verbosity of Infinity / Power Set / Choice is inherited from raw single-relation
  ZFC, not from EG; the definition layer is the fix.
- Schemas (Separation, Replacement, Peirce induction) cannot be single graphs in
  Beta — first-order logic can't quantify over formulas. They require the hole node.
- Second-order/categorical versions (full induction, second-order ZFC) need
  predicate quantification = Peirce's Gamma graphs, deliberately out of scope.
- All EGIF here is a proposed first draft for validation against Arisbe's parser;
  expect to adjust label-scoping details to match the implementation's exact rules.
