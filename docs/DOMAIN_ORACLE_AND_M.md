# The Domain Oracle: situating a graph in "enough" of a model M

**Status**: design-of-record · **steps 1–3 + the inverse pivot + theory query (§6.2)
BUILT** (oracle + peel + materialization + `/agon` interpretation register & inverse
search 2026-06-11; ontology-as-M / terminological box ([T-box](GLOSSARY.md#t-box)) theorem deduction 2026-06-12) · remaining:
oracle scale steps 4–6 (cache → horizon → SPARQL) · **Drafted**: 2026-06-11

> **On *rendering* M** (vs. holding it): see [`THE_MINIMAL_IN_VIEW_SET.md`](THE_MINIMAL_IN_VIEW_SET.md) §3, §11.
> M is axis (iii) of the scale problem; the answer is to draw only the relevant *neighborhood* G touches (the
> oracle's ego-graph slice) with a horizon map-symbol — never M in full. "M queried, not held" is itself the
> extended-mind / long-term-working-memory precedent (cues, not content).

> The question this answers: the Endoporeutic Game tests a proposal G against a
> domain model **M** — "the outside" that enables the outside-in interpretation.
> But we can't pull in all knowledge, and yet we need *enough* to ground
> interpretation, confirmation, refutation, or the admission of a new fact. How
> much is enough, and what does the contact surface look like, without getting
> lost or overwhelmed?

This note is the design-of-record for that contact surface. It does not specify
an implementation; it fixes the *shape* of the problem and the first step.

Related: [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (where M comes
from, the outside-in process), [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md)
(warrant gradient; *attest correspondence, not truth*),
[UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)
(the diachronic Universe of Discourse ([UoD](GLOSSARY.md#uod)) that M's growth is an instance of).

---

## 1. The reframe: M is *queried*, not *held*

The game guide already fixes the one operation the game performs against the
domain: a **graph homomorphism** — "the Proposer must show a mapping between *g*
and the objects and relations in M," where *g* is a negation-free outermost
piece of the proposal. That is the *entire* contact surface. The outside-in
process never asks M to enumerate itself; it asks a bounded sequence of strictly
local questions:

- *Does this negation-free subgraph map into you?* (positive area)
- *Give me a witnessing individual for this relation.* (the negative-area pick)

Everything reduces to localized membership / homomorphism / witness queries.

So the contact surface is **an oracle interface, not a bulk import.** The game
engine stays Existential Graph Instance ([EGI](GLOSSARY.md#egi))-native and source-agnostic; behind the oracle sits whatever can
answer those queries — the local tomos corpus, a Wikidata SPARQL endpoint, a
SNOMED service, a WordNet lookup. The consequence is the whole point:

> "Enough" stops being a property of M's *coverage* and becomes a property of
> *what the proposal actually touches.* You never load the ontology; you resolve
> atoms as the unwrapping reaches them.

### The interface (sketch)

```
DomainOracle:
    resolve(g: EGI_fragment) -> Mapping | UNKNOWN | DENIED
        # g is negation-free; returns a homomorphism into M, or
        # UNKNOWN (open-world: M neither confirms nor denies) or
        # DENIED (closed region: g provably fails)

    witness(relation, partial_binding) -> Individual | NONE
        # the negative-area individual pick (game rule 2)
```

Two methods. Pluggable backings implement them. The game logic does not change
when the backing does.

---

## 2. Three reasons "enough" is far smaller than "complete"

1. **Vocabulary-bounded.** The proposal's signature (its predicates and
   individuals) seeds the whole interaction. You only ever touch terms the graph
   mentions, plus their *scrolls* — and subsumption is already a scroll in the
   corpus model, so the relevant **type spine** around those terms is the only
   hierarchy you need, never the instance mass beneath it. An ego-graph of
   radius *n* around the signature, not the ontology.

2. **The open-world horizon is a feature, not a gap.** The game already makes
   "M neither confirms nor denies" a *first-class verdict* — the
   stalemate/independence case that becomes a new fact. So **M never needs to be
   closed to play.** Incompleteness is exactly what distinguishes deduction
   (confirmed) from empirical enlargement (unknown-but-consistent) from
   contradiction (denied). Beyond the horizon the honest answer is "unknown," and
   the game is built to do something meaningful with it.

3. **Demand-driven materialization.** As the outside-in walk reaches an atom,
   resolve it lazily and cache it into a session-local working model with a
   provenance tag. M grows *only along the path the inquiry actually took* —
   which is the guide's "M develops as the players consider new graphs." The
   working model is the diachronic UoD accreting, one resolved query at a time.

This is also just Peirce: the "outside" that enables outside-in interpretation is
**collateral experience**, which is always finite, indexical, and brought to bear
*as needed*. The horizon is not a compromise on an ideal; it *is* the model of
how a situated interpreter stands.

---

## 3. Two knobs that keep it from drowning

- **Horizon radius, widenable mid-game.** Start with the *n*-hop neighborhood
  around the signature; when a query reaches the edge, **"widen the horizon"
  becomes an explicit, recorded move**, not a silent re-config. The reach is
  visible in the transcript.

- **Open vs. closed regions.** Some refutations need closure ("these are *all*
  the mammals" → refute by exhaustion); most reasoning does not. Each imported
  fragment declares whether it is **asserted-complete** (negation-as-failure
  valid here → `DENIED` is reachable) or **sampled** (unknown ≠ false → only
  `UNKNOWN`). That declaration is the *only* place closed-world semantics live:
  local, explicit, and earned. You get exhaustive refutation exactly where you
  have claimed completeness and nowhere else.

---

## 4. Choosing the outside is a *move*, not config

The deepest form of the worry — "who decides what's relevant, and won't it be
arbitrary?" — is resolved by making **the choice of M the opening move of the
game**: an Agonothetes/Grapheus act. *"I will test this against Wikidata,
neighborhood radius 2, this fragment asserted-complete."* Recorded, warranted,
contestable. Relevance *is* a judgment; the honest place for it is owned by
someone and open to challenge, not buried in a config file.

It composes with the warrant gradient: M enters as **low-warrant backdrop** —
not "true," merely "available to map against." Nothing imported pollutes the
corpus; the game's **verdict** is what confers warrant. *Attest correspondence,
not truth* already protects this boundary.

---

## 4a. The Alpha home of the inning: the scroll, and model-revision as INS

The inning "given M, then G" is not an extra-systematic frame bolted onto the
calculus — it has a home in Alpha. "P given M" is the **scroll**
`cut[ M cut[P] ]` = M → P: P sits at *even* depth inside (affirmed-relative-to-M),
M at *odd* depth, in a **negative** context. Two consequences make the register
honest:

- **Choosing M, and revising it, are sound moves — not stance-taking.** Because M
  is in a negative context, the **Insertion rule (INS)** licenses freely adding
  conditions to it. Strengthening the antecedent — refining or revising the model
  under which you assert G — is INS operating on the antecedent, a permission of
  the calculus, not an extra-logical "new stand." This is the Alpha-level warrant
  for "the choice of M is a *move*" (§4) and for the diachronic *"free to
  demote"*: model revision *is* insertion into the conditioning context.
- **The asymmetry is the epistemology.** Erase freely where things are affirmed
  (positive), insert freely where things are conditioned (negative). G held under
  M is *logically defeasible* by construction.

So the semantic-game inning (`src/semantic_game.py`, `src/theory_query.py`,
`/agon/interpret`) and the inverse pivot (§7) are reading and revising a scroll.
The full argument is in
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) §5; it is the
Alpha grounding of the philosophy this document and
[MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) have been asserting.

---

## 5. Cost reality

Web Ontology Language ([OWL](GLOSSARY.md#owl))→Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif))→EGI layout is super-linear (~74s at 127 axioms, observed). So **never
bulk-translate to graphs.** Keep M in native/CLIF form behind the oracle and
translate to a *drawn* EGI only the fragment that enters the **visible** game —
the part the user actually watches get unwrapped. The contested graph is the one
thing that must be a picture; M may answer as data.

---

## 6. Minimal first step

A thin `DomainOracle` with the two methods above, backed first by the **local
tomos corpus**, because the homomorphism machinery already exists
(`graph_isomorphism_engine`, `same_graph`). Prove the demand-driven loop
end-to-end on a tiny neighborhood, with provenance-tagged caching, *before*
pointing it at anything SNOMED-scale. Then add exactly **one** external backing
(Wikidata SPARQL is the cleanest contract) behind the same interface. If the
abstraction holds across "local corpus" and "remote SPARQL," it will hold for
the rest.

Sequence:

1. **[DONE 2026-06-11]** `DomainOracle` interface + `CorpusOracle` (local EGIs)
   — `src/domain_oracle.py`, `tests/test_domain_oracle.py` (16 tests).
   `resolve(g)` is a conjunctive-query homomorphism of a negation-free `g` into a
   model's asserted (sheet-level) atoms, returning `CONFIRMED` (with a `Mapping`)
   / `UNKNOWN` (open) / `DENIED` (closed); constants match by label, argument
   order respected via `nu`, provenance names the model that answered, a cut in
   `g` is refused. `witness(relation, partial_binding)` offers individuals for the
   negative-area pick. Built directly on the public EGI API, not the protected
   isomorphism engine (a negation-free `g` has no cuts, so the embedding is small
   and well-defined).
2. **[DONE 2026-06-11]** The semantic-game seam — `src/semantic_game.py`,
   `tests/test_semantic_game.py` (15 tests). `evaluate(egi, oracle)` reads G
   outside-in and asks the oracle (`match_atoms` / `individuals`, added to the
   interface this step) at each negation-free layer; returns a three-valued
   `Verdict3` (TRUE / FALSE / UNKNOWN) + a legible transcript. **Kleene** logic
   makes open-world sound: an absent atom is UNKNOWN (open) / FALSE (closed); an
   unsatisfied **existential** lifts to UNKNOWN (open) but a ground formula does
   not (so `~[ (man "S") ~[ (mortal "S") ] ]` with both facts present reads TRUE
   even open-world); negation of a *present* atom is a definite FALSE
   (monotonicity). The universal `~[ (man *x) ~[ (mortal x) ] ]` reads TRUE
   closed / UNKNOWN open, FALSE with a closed-world counterexample. This is the
   inner evaluation game; it does **not** yet drive the transformation game's
   moves — that wiring (auto-Grapheus, the dialogical loop) is a later step.
3. **[NEXT] Materialize the model — facts + rules → the fullest extensional M.**
   See §6.1. Resolves the "model-checking, not inference" limit
   ([GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md) clarification 1): a model
   M authored as *facts + Horn-shaped rules* is forward-chained to its **least
   Herbrand model** (the closure of everything the rules entail over the facts), and
   *that* is what the peel checks against. Keeps the peel pure model-checking while
   making M "as full as possible." Reuses `match_atoms`; depends on nothing beyond
   steps 1–2. Precondition for ontology-as-M (T-box rules must be materialized to be
   testable).
4. Provenance-tagged session working-model (the demand-driven cache).
5. Horizon radius + open/closed declaration as M-selection parameters.
6. One remote backing (`SparqlOracle`, Wikidata) behind the same interface.

### 6.1 Materialization spec (step 3)

`materialize(M) → (M′, report)` — forward-chain the **Horn fragment** of M over its
facts to a fixpoint, returning a facts-only model `M′` (the least Herbrand model) and
an honest **skip-report** of the rules left unmaterialized.

- **The Horn line in Existential Graph ([EG](GLOSSARY.md#eg)).** A rule is a scroll `~[ B ~[ H ] ]` (= *B → H*).
  Materializable iff: **B** (the outer cut's area, minus the inner cut) is a
  conjunction of **atoms** over lines of identity; **H** (the inner cut's area) is a
  conjunction of **atoms**; and every line in H also occurs in B (**range-restricted**
  — no fresh existential individual in the head). Not materializable, and reported:
  a **negation in the head** (a cut inside H → not Horn), a **disjunctive head**
  (`~[ ~[A] ~[B] ]` inside H), or an **existential head** (a `*x` in H not bound in B
  → would demand a new individual; skolemization is the contest game's business). A
  bare fact (no scroll) is already in M′.
- **The fixpoint.** Repeatedly: for each Horn rule, find every binding of B into the
  current facts (this is exactly `match_atoms`), and add H's atoms under that binding;
  stop when a pass adds nothing. **Termination is guaranteed** — function-free,
  range-restricted rules generate no new individuals, so the Herbrand base is finite
  (Datalog).
- **Soundness + the closed pairing.** The least Herbrand model is the unique minimal
  model of the Horn theory, so model-checking a *positive* query against M′ equals the
  theory's entailment. For queries with cuts (negation), this is closed-world /
  stratified-negation — which is exactly why materialization pairs with the **closed**
  regime (§3): materialize, then close, then peel.
- **Honest skip-report.** Mirrors the Standard Upper Ontology Knowledge Interchange Format ([SUO-KIF](GLOSSARY.md#suo-kif)) import's report ([[project_ontology_import]]):
  every non-Horn rule is named and left to the contest/deduction game, never silently
  dropped. The user sees precisely how much of M the peel can and cannot use.
- **Wiring.** A standalone `src/model_materialization.py` (`materialize_egi(egi) →
  (facts_egi, report)`), reused at M-construction time: `CorpusOracle.from_egif(...,
  materialize=True)` and an opt-in on the `/agon/interpret` path, so a corpus UoD or a
  hand-authored M that carries rules becomes testable by the peel.

### 6.2 Theory query — deciding a T-box theorem (ontology-as-M) — BUILT 2026-06-12

Materialization makes the peel work for an **A-box-bearing** model: Porphyry carries
`(Man "Socrates")`, so materializing derives Socrates is Animal/Living/Body/Substance,
and a proposal about Socrates model-checks correctly. But a real **T-box ontology** —
the SUMO upper spine, the FOAF schema, Porphyry's genus ladder — is almost entirely
*rules* over few or no individuals. Materializing SUMO's 43 subsumption axioms derives
**0 facts** (no individuals to chain over → the empty model). A subsumption proposal
`~[ (Object *x) ~[ (Entity x) ] ]` then reads **vacuously TRUE** closed (the *wrong*
reason — a nonsense universal `~[ (Object *x) ~[ (Flibbertigibbet x) ] ]` reads TRUE
too) or **UNKNOWN** open. **Model-checking cannot decide a theorem of the theory.**

The decision that can is **deduction**, and for the Horn/Datalog fragment it is the
standard, complete, terminating procedure — **freeze a fresh witness** (`entails` in
`src/theory_query.py`):

1. take the universal `G = ~[ B(x⃗) ~[ H(x⃗) ] ]` (body → head, range-restricted);
2. mint a fresh constant for each line of identity in `B` and assert `B` over those
   constants — an *arbitrary* individual mentioned nowhere in M;
3. **materialize** `M ∪ {frozen B}` (run M's rules over the witness);
4. check `H` over the same constants. Because the witnesses are arbitrary, `H` holding
   of them means G holds *universally* — G is a theorem of M.

**Soundness**: the fresh constants occur nowhere in M, so any derivation of
`H(witnesses)` uses only M's universally-quantified rules and holds for every
substitution. **Completeness (Horn)**: the least Herbrand model is M's unique minimal
model, so a head atom is derivable iff the Horn theory entails it.

**Honest residue.** A *positive* is always `TRUE` (derivation is sound regardless of
what was skipped). A *negative* is `FALSE` only when M is **wholly Horn**; if M carries
non-Horn axioms materialization had to skip, a negative is `UNKNOWN` — the Horn
fragment can't prove G, but the skipped axioms might bear on it. This is exactly right
on the corpus: `Man ⊑ Beast` over Porphyry reads `UNKNOWN`, because Porphyry's
Man/Beast **disjointness** (`~[ (Beast z) (Man z) ]`) is a skipped non-Horn denial that
is precisely what would settle it.

**Wiring.** `/agon/interpret` (and the standalone `_interpret_payload`), when
`materialize` is set and G is a universal Horn scroll, returns a `theorem` block beside
the extensional `verdict` — the authoritative "is G a theorem of M (the theory)?"
answer. This is the deduction the design-of-record (`GENERATION_AND_TESTING.md`
clarification 1) routes to "the contest/deduction game": the peel stays pure
model-checking; the theory query is the inference step that makes a T-box testable.
Verified end-to-end on `sumo_upper` (subsumption theorems), `porphyry_tree` (the ladder
+ the disjointness residue), and `foaf_core` (typing chains through subsumption:
`knows(y,z) → Person(y) → Agent(y)`). Tests: `tests/test_theory_query.py` (15).

---

## 7. The *inverse* game — "what M does this map into?" — BUILT 2026-06-11

**Built** as `POST /agon/where-it-holds` (+ a "🔎 Where does G hold?" button): fix G,
range the peel across the candidate models (the curated examples + the corpus UoDs,
optionally materialized), and rank by relationship — **holds** (at home / a theorem),
**partial** (some of G at home; the residue is its contribution), **independent**, or
**contradicts**. The partial-map residue (below) is surfaced concretely — e.g. a
proposal `(coastal C) (generates_tourism C)` reads *partial* in the wetland model with
residue `(generates_tourism C)`. The interface needed no change to `resolve`/the peel:
the forward inning already parameterizes on M, so the inverse is iteration plus a
coarse sheet-atom fit score. Original sketch below.

The forward game is *given M, test G*. There is an inverse worth naming because
it matches a real and common experience: **an idea that makes sense while you are
still searching for the context in which it does.** You have the graph; you are
hunting the frame that licenses it.

In Peircean terms the forward game is deduction (does it follow?) shading into
induction (is it consistent with the sample?); the inverse is **abduction** — the
search for the hypothesis-context that would make a surprising-but-sensible graph
*a matter of course.*

The oracle abstraction inverts cleanly:

- **Forward:** M fixed → `resolve(G)` against it.
- **Inverse:** G fixed → search candidate backings / horizons for an M where
  `resolve(G)` succeeds, and **rank by how well G maps.**

The ranking is the payload, because the useful answer is rarely a clean yes/no:

| Outcome | Meaning |
|---|---|
| **Full map** | G is already a theorem of M — "at home here; you knew it implicitly." |
| **Partial map** | G maps *except* for a residue. The residue **is the contribution** — what G would newly add to that UoD. The search finds the home *and* isolates what is novel about moving in. |
| **No map in reach** | Genuinely alien — or the horizon is too small, looping back to "widen the horizon." |

This is **context-retrieval-by-abduction** over the same oracle. It directly
serves two things already in the personas: the **researcher** finding the seam
between domains (rather than being told which two to bridge), and **"contribution
as a new fact in the UoD"** — discovered by search rather than asserted by hand.

Not to be built now; recorded so the `DomainOracle` interface is designed to
admit it later (it already does — the inverse needs only iteration over backings
plus a partial-map scorer, no change to `resolve` itself).
