# The Corpus and the Import Model

**Status:** active (2026-06-08). The corpus retrofit described in §3 is *done*;
the import-kind taxonomy in §2 is implemented in the provenance bundle; §4 (the
Agon roles) and §5 (ontology import) are the forward edges.

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

Four of the five kinds are populated; `ontology` is the one not yet exercised
(§5). Citations cross-reference `docs/references/eg_proofs.bib` by bibkey where
one exists.

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

## 5. Forward edges

- **Ontology import** — the one unused kind. An ontology (a published T-box) would
  enter as background theory: a `domain_model`-shaped UoD whose provenance cites
  the vocabulary, available to Agon as the standing context a game presupposes.
  The natural first target is a small, well-known vocabulary so the
  correspondence story stays legible.
- **Pattern library for Agon** — promote `pattern`-kind items into a queryable
  move set the game engine can offer a player, and let a *derived rule*
  (`src/derived_rules.py`) register itself as a named pattern.
- **Warrant lifecycle** — wire the `low → tested` transition to an actual Agon
  outcome, so a graph that survives the game is re-saved at `tested` with the
  game record as its proof-of-standing.
- **`dau_2006_p112_ligature` page** — verify the citation against a fixed copy of
  *Mathematical Logic with Diagrams* and drop the `verify-page` tag.
