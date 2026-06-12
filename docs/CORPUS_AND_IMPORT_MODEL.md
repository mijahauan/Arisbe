# The Corpus and the Import Model

**Status:** active (2026-06-08). The corpus retrofit (§3) and the first **ontology
import** (§5) are *done*; the import-kind taxonomy (§2) is implemented in the
provenance bundle. §4 (the Agon warrant lifecycle) remains the forward edge.

This doc sits downstream of two others and should be read after them:
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the philosophical floor —
*attest correspondence, not truth*; the warrant gradient) and
[ORGANON_IMPORT_WALKTHROUGH.md](ORGANON_IMPORT_WALKTHROUGH.md) (how a worked proof
reaches the corpus through the provenance/annotation doorway). It answers a
question those raise but don't settle: **what kinds of things do we import, and
what is the corpus *for*?**

---

## 1. One doorway, one floor

Everything enters the corpus through a single doorway —
`tomos_service.save_uod_with_chain(uod, chain, provenance=…)` for a worked proof,
or `save_uod` + `save_provenance` + `save_annotations` for a bare exemplar — and
everything enters at **low warrant**. Arisbe attests that an EG's drawn form and
its linear form denote the same mathematical object (§3.3); it does **not** assert
that the proposition is *true*. A classical theorem and a synthetic test graph
arrive at the same floor. Warrant is a gradient (`blank → low → tested`); the only
thing that lifts an item above `low` is **surviving the Endoporeutic Game** — see
§4. Provenance and annotations are **outside §3.3**: they describe the source,
they are not signs in the graph.

The honesty consequence, enforced by `tests/test_corpus_conformance.py`: a
**synthetic** exemplar must never carry a fabricated citation. A graph named
`ternary_relation_challenge` is *authored here*; pinning a page number on it would
be the un-attested truth-claim the floor forbids. The split below is not
bookkeeping — it is the floor made operational.

## 2. The import-kind taxonomy

The provenance bundle (`src/provenance.py`) carries a coarse **import kind**,
orthogonal to warrant and to the transcribed-vs-authored discriminator, so
Organon can shelve an item and Agon can query it:

| Kind | What it is | Provenance shape | Corpus role |
|---|---|---|---|
| `exemplar` | a single depicted graph, no derivation | one source layer; `proof_source` empty | notation reference / teaching |
| `proof` | a worked derivation (carries a chain) | full bundle: theorem + proof + method | demonstration; **Agon target** |
| `pattern` | an argument *form* (MP, syllogism, dilemma…) | method source (the inference form) | **Agon move/strategy library** |
| `domain_model` | a small modelled universe of discourse | a domain source | **Agon board** (the UoD played *in*) |
| `ontology` | a published vocabulary / T-box | an ontology citation | reference vocabulary; background theory |

Two independent axes ride alongside the kind:

- **transcribed vs authored-here** (`proof_source.kind`): was *this artifact*
  copied from a published source, or constructed in Arisbe? Only
  `theorem_praeclarum` is a *transcribed proof* (Dau's animated EG derivation);
  Peirce's Law, Barbara, and group-identity are *authored* derivations of
  historical theorems.
- **cited vs synthetic** (`theorem_source` present vs absent): is there a real
  published proposition behind it, or is it a structural/pedagogical test graph?

A graph can be a *cited exemplar* (Sowa's cat-on-mat), an *authored pattern*
(`peirce_modus_ponens`), or a *synthetic exemplar* (`sibling_cuts_shared_variable`)
— the three fields name three different facts and must not be collapsed.

## 3. The corpus today (after the retrofit)

`tools/retrofit_corpus.py` brought all pre-existing UoDs up to spec and retired
one throwaway practice session. The curated corpus is **20 items**:

- **6 cited exemplars** — `peirce_cp_4_394_man_mortal` (CP 4.394),
  `roberts_1973_p57_disjunction` (Roberts 1973 p.57), `sowa_2011_p356_quantification`
  (Sowa 2011 p.356), `sowa_cat_on_mat` (Sowa, canonical), `dau_2006_p112_ligature`
  (Dau, *Math. Logic with Diagrams* — page to verify).
- **1 transcribed proof** — `theorem_praeclarum` (theorem: Leibniz 1966; proof:
  Dau 2008 animated).
- **3 authored proofs** (the import-walkthrough fixtures) — `peirce_law`,
  `barbara`, `group_identity`.
- **1 argument pattern** — `peirce_modus_ponens`.
- **1 domain model** — `roberts_domain_modeling`.
- **8 synthetic exemplars** — structural/pedagogical test graphs
  (`mixed_quantifier_complex`, `peirce_complex_scope`, `shared_constant_disjunction`,
  `sibling_cuts_shared_variable`, `ternary_relation_challenge`,
  `stanford_nested_quantifiers`, `beta_modus_ponens`, `beta_converse_mp`,
  `dau_theorem_proving`).

All five kinds are now populated (`ontology` was added with the import in §5).
The curated corpus is **23 items**. Citations cross-reference
`docs/references/eg_proofs.bib` by bibkey where one exists.

## 4. The corpus serves two masters

The corpus is at once a **demonstration/education core** and a set of **reference
models for the Endoporeutic Game** — the same items, read two ways.

- **As a textbook** (Organon, read-only): exemplars teach the notation; worked
  proofs show the rules in motion; the annotation layer is the margin commentary.
- **As Agon material**: a `proof` is a *goal* to derive; a `pattern` is a *move*
  in a player's repertoire; a `domain_model`/`ontology` is the *board* — the
  Universe of Discourse a game is played within. The `kind` field is what lets
  Agon ask "give me a domain model to play in" or "an argument pattern to apply."

This is also where warrant becomes dynamic. An item enters at `low`; when a graph
is *tested through Agon* — asserted, challenged dialogically, and left standing —
its warrant rises to `tested`. That transition is the only route above the floor,
and it is the reason the corpus needs reference models in the first place: the
game needs a board, an opponent's repertoire, and a goal, all drawn from here.

## 5. Ontology import (done)

An ontology is a T-box, and every T-box axiom is already a shape the corpus knows
(`src/ontology_egif.py` names the constructors):

| Axiom | DL | EG |
|---|---|---|
| subsumption | `A ⊑ B` | `~[ (A *x) ~[ (B x) ] ]` (a scroll) |
| disjointness | `A ⊓ B ⊑ ⊥` | `~[ (A *x) (B x) ]` |
| argument typing | `domain/range(R) ⊑ C` | `~[ (R …*x…) ~[ (C x) ] ]` |
| A-box | `C(a)` | `(C "a")` |

So an ontology imports as the **conjunction of those axioms on one sheet** — a
single `kind=ontology` UoD (shelved under the `domain_model` category). Three were
imported, in ascending realism — the general model exercised end to end:

- **`porphyry_tree`** — Porphyry's Isagoge (c. 270 CE), hand-encoded: the
  genus–species spine + the rational/irrational division + Socrates. The T-box
  the corpus's `barbara` reasons over.
- **`foaf_core`** — a FOAF slice (Brickley & Miller, W3C), hand-encoded: `Person ⊑
  Agent` plus domain/range typing on `knows`.
- **`sumo_upper`** — the upper spine of SUMO (Niles & Pease 2001), **translated**
  from `docs/references/SUMO1.2.txt` by `tools/suokif_to_eg.py`.

Two findings worth keeping:

- **Honest partial translation.** SUMO is large, merged, and partly modal/
  higher-order. The translator brings across only the EG-expressible *ground*
  axioms (`subclass-of`, `disjoint`, `instance-of`) and **reports everything it
  drops** by operator (89 `documentation`, 34 `nth-domain`, the `=>`/`<=>`/modal
  forms, the mereology predicates). That report rides in the UoD's annotation —
  no silent cap that would read as "imported all of SUMO." This *is* the manifest
  floor applied to import: bring across what's expressible, at low warrant, and be
  explicit about the rest.
- **The upper ontology is Peircean.** SUMO 1.2 is built on Sowa's upper ontology,
  whose top division — `Independent / Relative / Mediating` directly under
  `Entity` — *is* Peirce's Firstness / Secondness / Thirdness. The root of a
  modern merged ontology is the same triad the rest of the corpus rests on.
- **Layout cost scales super-linearly.** The full 127-axiom ground taxonomy
  attests but takes ~74 s to lay out (250 cuts through ELK); the depth-≤2 upper
  spine (43 axioms) lays out in ~0.3 s. The displayed UoD is the spine; the full
  taxonomy is reproducible from the translator. A large *theory* is correct but
  not yet cheap to *draw* — a real layout-performance frontier.

### 5.1 The OWL→CLIF→EGI pipeline (BUILT 2026-06-12)

The SUO-KIF translator brings one specific dialect across. The general path for the
**web's** ontology language is **OWL → CLIF → EGI**, and its back half already exists
and is robust: `clif_parser_dau.parse_clif` turns a Common Logic sentence into exactly
the EG shapes — `(forall (x)(if (Man x)(Mortal x)))` → the subsumption scroll, an
intersection body → a conjunctive Horn body, an `exists` head → an existential scroll,
`(not (and …))` → a disjointness denial. So bringing a real OWL ontology in as a model
M reduces to **OWL → CLIF**, the front half built in `tools/owl_to_clif.py`.

It reads **OWL 2 Functional-Style Syntax** (`.ofn` — the structural-specification
serialization; form-oriented, so no RDF triple store or blank-node restriction
decoding) and translates the EG-expressible axioms, class expressions limited to named
classes, `ObjectIntersectionOf`, and `ObjectSomeValuesFrom`:

| OWL axiom | CLIF |
|---|---|
| `SubClassOf(C D)` | `(forall (x)(if 〚C〛 〚D〛))` |
| `EquivalentClasses` / `DisjointClasses` | pairwise `iff` / `not-and` |
| `SubObjectPropertyOf(R S)` | `(forall (x y)(if (R x y)(S x y)))` |
| `ObjectPropertyDomain` / `Range` | typing scrolls on `x` / `y` |
| `InverseObjectProperties` / `Symmetric` / `Transitive` | the Horn rule for each |
| `ClassAssertion` / `ObjectPropertyAssertion` | A-box facts |
| `SameIndividual` / `DifferentIndividuals` | `(= a b)` / `(not (= a b))` |

Same honest floor as the SUO-KIF path: cardinality, union, complement,
`AllValuesFrom`, datatypes, functional/key axioms, and annotations are **reported by
construct** (`⊑ owl:Thing` is dropped as trivial), never silently truncated.
`Declaration(…)` is counted as vocabulary, not skipped. `domain_model_importer`
exposes `from_owl_text` / `from_owl_file` (warnings carry the skip-report), so an OWL
file composes with the CLIF path and wraps as a `kind=ontology` UoD. The loop closes
with this session's theory query: an OWL-imported ontology is a real M whose
subsumption / intersection / transitivity theorems `theory_query.entails` decides
(`tests/test_owl_import.py`, 23). *Not yet surfaced:* a web import-doorway notation
(it would flatten a multi-axiom ontology into one "linear form" and lose the
skip-report) and a real-world OWL ontology as a shipped corpus UoD.

**COLORE (Common Logic) is the back half, directly.** COLORE files are *already* CLIF,
so `from_clif_file` / `from_clif_directory` import them with no front-end —  including
the `cl-text` / `cl-module` wrappers (inner sentences extracted) and disjointness /
conjunctive heads. The test-as-M loop now works on them too: materialization +
`theory_query` were hardened (2026-06-12) to build their working graphs **directly**
through the EGI API rather than round-tripping through EGIF *text*, which a CLIF model
carrying names EGIF can't express (e.g. `Warm-blooded`, `Can-fly`) would otherwise
crash. Verified on `corpus/domain_models/animal_taxonomy/animal_taxonomy.clif` (14 Horn
rules forward-chain over the A-box; subsumption theorems decide; the disjointness and
the defeasible penguin-can't-fly exception are honestly the non-Horn residue). **Two
real COLORE gaps remain:** `cl-imports` is parsed as a **no-op** (cross-module URI
resolution isn't done — you must supply all modules together, e.g. one directory); and
because the **EGIF query surface** rejects hyphenated identifiers, querying a relation
like `Warm-blooded` needs a clean alias until either EGIF admits those names or the CLIF
importer sanitizes them (as the OWL path already does).

**Validated against the real COLORE repository (2026-06-12).** Pulling actual modules
from `github.com/gruninger/colore` surfaced — and fixed — what synthetic content hid:

- **The `/* */` header blocked *every* COLORE file.** Each carries a `/* Copyright …
  University of Toronto **and** others … */` block; the protected CLIF lexer strips only
  `;;` comments, so "and"/"if"/"not" inside the header tokenised as keywords and broke
  the parse. Fixed at the importer boundary (`_strip_block_comments` removes `/* */`,
  leaving `//` alone so `http://` IRIs survive).
- **Reused bound variables collapsed independent universals — a correctness bug.** A file
  with many `(forall (x) …)` sentences had every `x` unified by `parse_clif` into one line
  of identity, turning `(∀x A→B) ∧ (∀x C→D)` into the weaker `∃x (A→B)∧(C→D)` (and a
  layout catastrophe: one vertex through every scroll). Fixed by **alpha-renaming** all
  quantified variables to globally-unique names before parsing (`_disambiguate_variables`,
  applied in `from_clif_text` and `compose_models`) — the CLIF analogue of the OWL
  translator's per-axiom fresh variables.
- **`colore_between` landed** (`tools/build_ontologies.py` `colore_between()`): the COLORE
  *betweenness* ontology — the resolved `cl-imports` closure betweenness → weak_between →
  bet, verbatim COLORE content (CC BY-SA, attributed) — as a cited `kind=ontology` UoD,
  selectable in `/agon`. The **first corpus ontology from a real external CL repository**.

What stays a boundary, honestly: COLORE is mostly **non-Horn FOL** (`iff` / `exists`-heads
/ equality / negated bodies → materialization's skip residue, so a relational theory like
betweenness forward-chains *nothing* — its reasoning value is in the contest, not the Horn
closure); it uses **function terms** like `(dmv v m)`, which **our CLIF parser** does not
yet handle (a parse error — an *implementation* gap, not a limit of EG: functions are
expressible by relationalisation — a function is a relation whose output is uniquely
determined, `(density (dmv v m))` ↦ `∃z (dmv(v,m,z) ∧ density(z))` + functionality — and
Dau gives a direct extension, *Constants and Functions in Peirce's Existential Graphs*,
ICCS 2007; EGIF even has an explicit `(Type … | output)` function form. The fix is to
relationalise function terms on import; the uniqueness axioms are non-Horn, so they fall
to the contest residue like the rest); and `cl-imports` still needs hand resolution.
COLORE names are **underscored, not hyphenated**, and underscores round-trip
through EGIF cleanly — so COLORE does *not* exercise the hyphen fix (that remains pinned by
the in-repo hyphenated `animal_taxonomy`).

## 6. Forward edges

- **By-hand import & edit (the reading desk)** — the next big one. So far every
  corpus item was built by a Python tool (`build_*_chain.py`, `build_ontologies.py`,
  `retrofit_corpus.py`). What's missing is the *interactive* path: a person reading
  a book or magazine, transcribing a graph and its provenance **by hand** through
  the UI. That means an editor where you draw/enter the EG (or paste a linear form),
  fill the provenance bundle (kind, the source citation, transcribed-vs-authored,
  warrant stays `low`) and the annotations, see it §3.3-attest live, and save it to
  scratch / send it to Agon — and the same editor reopened on an existing item to
  revise its graph or its outside-record. This is the Ergasterion's job extended
  with a provenance/annotation form; the building blocks exist (the workshop editor,
  `save_provenance` / `save_annotations`, the linear-form parsers), but the
  hand-transcription surface does not. It is the human counterpart to the
  translators in §5: a translator brings a *file* across; the reading desk brings a
  *page* across.
- **Pattern library for Agon** — two tiers. A *depicted* pattern (`kind=pattern`,
  a graph you can read) imports trivially; promoting it to a *computable* pattern
  means registering it as a **derived rule** (`src/derived_rules.py`, where
  `universal_instantiation` / `instantiate_to_lines` already live) so the engine
  can actually apply it. The library is the bridge: a "lesson learned / established
  method" enters as a depiction and graduates to a move. A *depicted* pattern (`kind=pattern`,
  a graph you can read) imports trivially; promoting it to a *computable* pattern
  means registering it as a **derived rule** (`src/derived_rules.py`, where
  `universal_instantiation` / `instantiate_to_lines` already live) so the engine
  can actually apply it. The library is the bridge: a "lesson learned / established
  method" enters as a depiction and graduates to a move.
- **Warrant lifecycle** — wire the `low → tested` transition to an actual Agon
  outcome, so a graph that survives the game is re-saved at `tested` with the game
  record as its proof-of-standing. *(Blocked: Agon does not yet emit outcomes.)*
- **Layout performance for large theories** — make a 100+-axiom ontology drawable
  (the 74 s case above); until then large taxonomies live as spines + translators.
- **`dau_2006_p112_ligature` page** — verify against a fixed copy and drop the
  `verify-page` tag.
