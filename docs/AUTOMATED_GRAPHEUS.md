# The Automated Grapheus — making Agon a dialogical contest

**Status:** BUILT (2026-06-12, same day as this design-of-record — `src/grapheus.py`, contest
routes, frontend, and the increment-4 warrant step all shipped in commit `012b2af` and after;
CAPABILITY_MAP.md marks the Automated Grapheus SHIPPED). The document below is left in its
original design-of-record voice as the build record of what shipped; read it as historical
plan-that-became-fact, not an open proposal. Supersedes the "shape of the work" sketch in
`CURRENT_PLAN.md`'s ▶ NEXT SESSION block.

**Read alongside:** `docs/ENDOPOREUTIC_GAME_GUIDE.md` (the two games, the triad),
`docs/DOMAIN_ORACLE_AND_M.md` §6 (the semantic-game seam), `docs/GENERATION_AND_TESTING.md`
(eliminative = game / additive = making; deduction earns the corpus *through* Agon),
`docs/CHAIN_OF_SEMIOSIS.md` (semiosis is dialogical; fuller regime-2 = an assertion that has
*withstood challenge*). Scholarly anchor: A.-V. Pietarinen, *Signs of Logic*
(`docs/references/Signs_of_Logic.pdf`), Ch. 4 "Existential graphs on the move", pp. 134–137,
and the janus-faced-cut discussion pp. 164–166.

> **One regime (updated 2026-07-16, sweep #2 — the second relocation).** Corpus *and* live Agon
> loops hold M's elements in **cells at even depth** of the standing world-scroll
> `~[ ~[cell] … ~[ ] ]`, with explicit M-steps (PEEL / ADMIT_TO_M / RETRACT_FROM_M / REVISE_M —
> `src/world_scroll.py` + `src/m_steps.py`; `docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md`
> §9, and `docs/ENDOPOREUTIC_GAME_GUIDE.md` §"Taxonomy" case 3a for the admission mechanics).
> Every reader goes through `m_view`; the §8.1 loop migration is discharged.

---

## 0. What this is, in one paragraph

Today `/agon/interpret` runs the **peel** once — `semantic_game.evaluate(G, oracle)` reads G
outside-in against a model M and returns a Kleene verdict + a `winning_witness` /
`counterexample`. That is a one-shot evaluation. The **automated Grapheus** turns it into a
**move-by-move dialogical contest**: a human plays the **Graphist** (proposes G, defends it),
and the machine plays the **Grapheus** (the model side — Nature/Falsifier and the adjudicator
of atoms against M), choosing each of *its* moves by the strategy the model warrants. The
existing evaluator already computes every subgame's value, so the Grapheus's strategy is *read
off it*; the build is to **lift the evaluator into an interactive extensive-form driver**, not
to write new logic.

---

## 1. Two games — and which one this is

"The Endoporeutic Game" names two distinct things in this codebase. Keep them apart:

- **The transformation game** (`src/endoporeutic_game.py`, Dau Ch. 21) — proof-theoretic.
  PROPOSER defends in negative areas (INS/IT+/DC+), SKEPTIC attacks in positive areas
  (ERA/IT−/DC−); the apparatus is Dau's six rules. This decides **validity / provability**,
  and is the engine behind the *contest register* hot-seat. It is **not** what the automated
  Grapheus drives.
- **The semantic game** (`src/semantic_game.py`) — model-theoretic. Reads G against a model M
  outside-in (endoporeutically), each choice owned by a player, atoms adjudicated by M.
  Truth-in-M = a winning strategy for the Graphist. **This is the contest the automated
  Grapheus plays.**

Pietarinen maps EGs *directly* onto the semantic game (*Signs of Logic*, p. 135: "The mapping
from alpha graphs to semantic games is straightforward"), with the Grapheus as the *malin
génie* "determining the truth of the irreducible, terminal graphs" (p. 134). The
transformation game is a separate apparatus for proof. The "walk through the levels of
negation until the whole proposal is traversed" is the semantic game's extensive form.

The division of labour is the one `GENERATION_AND_TESTING.md` already fixes: **eliminative =
the game (Agon, testing G in M)**; **additive = making (Ergasterion)**. The automated Grapheus
is the eliminative engine made interactive.

---

## 2. The rules of the contest (Pietarinen-pinned)

The game is played between the **Graphist** (Myself / Verifier; the human; proposes G) and the
**Grapheus** (Nature / Falsifier; the machine; keeper of M). It proceeds **outside-in** from
the sheet toward the spots. Ownership of every choice is fixed by **polarity** (even depth =
positive; odd depth = negative), and is *total* — at every non-terminal history exactly one
player chooses (p. 135).

| At a … | positive area (even depth) | negative area (odd depth) |
|---|---|---|
| **juxtaposition** (conjunction of subgraphs) | **Grapheus** picks which subgraph to pursue | **Graphist** picks |
| **ligature** (a line of identity = ∃), owned by polarity of its **outermost extremity** | **Graphist** picks the individual from dom(M) — "refers to something" (4.458) | **Grapheus** picks — "refers to anything there may be" |
| **spot** (atom) reached — terminal | true in M → Graphist wins the play | false in M → Grapheus wins |

(*Signs of Logic*, pp. 135–136, the four game rules.) The selected individual is instantiated
at the **outermost end** of the line and "propagates continuously inward along the LI toward
the interiors of the inner cuts and to the spots" (p. 136) — exactly the `beta` carry in
`semantic_game._holds`. "The winning conventions change with respect to choices on negative
areas" (rule 1): the same act (choosing a satisfied subgraph) is a Graphist win on a positive
area and a Graphist **loss** inside a cut.

G is **true in M** iff a **winning strategy exists for the Graphist**; **false** iff one exists
for the Grapheus (p. 136, rule 4).

---

## 3. Role-switching: the janus-faced cut

The role swap is the *semantics of negation*, not an extra operation. Peirce's cut is
**janus-faced** (Pietarinen pp. 164–166, citing CP 4.556):

1. the **cutting** severs the interior from the sheet of assertion → weak, contradictory
   negation ("what is scribed there is not asserted");
2. the **reversal** — "when the player interpreting the graph enters the enclosure of the cut,
   his or her strategic role will change to that of his or her opponent" → strong,
   game-theoretic negation.

CP 3.480: the encirclement reverses, *at once*, (a) the quality of spots (affirmative ↔
negative), (b) **"the selection of the haecceities as performable by advocate or opponent"**
(who names the individual), and (c) conjunction ↔ disjunction (simultaneous ↔ alternative
choice). CP 4.458: "any line of identity whose outermost part is evenly enclosed refers to
*something*; any one whose outermost part is oddly enclosed refers to *anything* there may be …
the interpretation must begin outside of all seps and proceed inward."

**Consequence for the engine — two granularities, both real and compatible:**

- **Semantic granularity:** the role swaps **exactly once per cut entered**, continuously,
  as internal bookkeeping of the walk (depth parity). Non-negotiable.
- **Interaction granularity:** a *turn* (a unit of human ↔ machine exchange) runs from one
  **contested** frontier to the next. The driver advances through model-forced choices (and
  through the cut-by-cut swaps) autonomously, pausing only where a genuinely free choice is
  owned by the human.

So "does a turn cross one cut or run to the next decision?" — the *swap* is per-cut (internal);
the *turn* is to-the-next-contested-choice (external). No conflict.

---

## 4. The auto-Grapheus is a strategy over the existing evaluator

`semantic_game._holds` already computes, for every area under every binding, the subgame's
Kleene value (`_or3` over witness choices, `_and3` over the conjunction-and-negated-cuts
matrix). A **winning strategy is exactly minimax over that valued tree**:

- at a node the **Grapheus** owns, it plays a child whose subgame value is a Grapheus win
  (`FALSE`); the peel's `counterexample` *is* that selective (the defeating individual, or
  the conjunct/cut that fails);
- at a node the **Graphist** owns, the winning move is a child evaluating `TRUE`; the peel's
  `winning_witness` is that selective — used to *check* the human's choice, or to play the
  Graphist automatically in self-play / hint mode.

So the automated Grapheus needs **no new search**. It is a thin driver that, at each history,
(1) asks the polarity table who chooses, (2) if that's the Grapheus, queries the evaluator for
a winning child and plays it, (3) if that's the human, surfaces the legal choices and waits.
The oracle methods it leans on already exist: `oracle.individuals()`, `oracle.match_atoms(...)`,
`oracle.individual_label(...)`, `oracle.resolve(...)`, `oracle.witness(...)`
(`src/domain_oracle.py`).

---

## 5. The extensive-form data model

Lift the recursion into explicit, serialisable state — the "bookkeeping device" Pietarinen
identifies as answering Hammer (1998) (p. 136). Sketch (final shapes in code):

```
Selective   = { line: str,          # the ligature token (x, x2, …)
                individual: str,     # the M individual's label
                by: "graphist"|"grapheus",
                at_polarity: "+"|"−" }   # polarity of the outermost extremity

Choice      = { kind: "juxtaposition"|"ligature"|"descend",
                area_id: str, depth: int, polarity: "+"|"−",
                owner: "graphist"|"grapheus",
                # juxtaposition: which subgraph; ligature: which individual
                options: [...], picked: <option>|null,
                forced: bool }       # only one option warranted → auto-advanced

History     = ordered [Choice|Selective]      # the path so far (the play)
Play        = { history: History,
                bindings: { line: individual },  # selectives accumulated
                frontier: Choice|null,           # the next contested choice, or null at terminal
                value: "true"|"false"|"unknown", # subgame value at the frontier (from the peel)
                outcome: "graphist_wins"|"grapheus_wins"|"independent"|null }
```

A `Play` is the contest's primary artifact. It is **not** a Dau `TransformationChain` — it is a
**game record** (the selectives + binary choices + the payoff), lighter and of a different
kind. This is the load-bearing decision of the design (see §7).

---

## 6. Open-world overlay — the one deliberate divergence from Pietarinen

Pietarinen's base game is **two-valued, perfect-information, closed-world**: a winning strategy
exists for *exactly one* player. Our oracle is open-world, so the evaluator is **three-valued
Kleene** — an absent atom or an unsatisfiable existential lifts to `UNKNOWN`, not `FALSE`
(`semantic_game.py` docstring; sound for supervaluation). We keep this overlay deliberately:

- At a frontier the **Grapheus** owns where M returns `UNKNOWN` (no warranted move either way),
  the Grapheus **declines**, and the Agonothetes records the episode as **independent** — G is
  neither confirmed nor refuted *in this M*. This is the honest open-world stalemate
  `ENDOPOREUTIC_GAME_GUIDE.md` makes first-class, and it is the natural hand-off to the
  **inverse pivot** (`/agon/where-it-holds`: "in what M *does* it hold?") and to widening M
  ("choosing the outside is itself a move", `DOMAIN_ORACLE_AND_M.md` §4).
- `closed=True` (an oracle asserting completeness) collapses the overlay back to Pietarinen's
  two-valued game — negation-as-failure, `UNKNOWN → FALSE`. Both modes are already in the
  evaluator (`SemanticGame.closed`).

Pietarinen *does* develop imperfect-information EG games (Nature's role hidden; players "not
informed whether they are to act as verifiers or falsifiers", pp. ~395+) — but that is the
**information** axis, orthogonal to open-world, and out of scope here. We note it as the
principled place a richer future variant would go, not a contradiction of the present design.

---

## 7. The record, and the warrant lifecycle

This is the seam to the import↔Agon arc (`project_import_low_warrant_and_floor`,
`CHAIN_OF_SEMIOSIS.md`). Two artifacts, two purposes:

1. **The `Play`** (the game record, §5) is what the contest *produces* and what
   "withstood challenge" *is*: a concrete extensive-form play in which the Graphist had a
   winning strategy against the model-warranted Grapheus. It carries the selectives (which
   individuals M supplied) and the path — auditable evidence, not a bare verdict.
2. **The chain step** is minted only at the **corpus boundary**, and only on a Graphist win the
   author chooses to assert: a single `ChainStep` "asserted, having withstood Agon against M",
   referencing the `Play` as its warrant. This is how a **low-warrant import becomes fuller
   regime-2** — the missing link. The §3.3 attestation still attests *correspondence, not
   truth* (`mode contract`); the *warrant* the Play certifies is a separate, new axis.

A Grapheus win records nothing to the corpus (G failed in M); an `independent` episode records
nothing but is worth surfacing (it is a result, and a prompt for the inverse pivot). Per the
mode contract, **nothing auto-asserts** — the Agonothetes annotates a disposition, the human
acts.

**The disposition taxonomy needs no new keys.** The three contest outcomes *are* the
semantic-game verdict trichotomy (Graphist win ⟺ `true`, Grapheus win ⟺ `false`, independent
⟺ `unknown`), so they slot straight into the existing `_COHERENT_WITH` bands in
`web_api/services/agonothetes.py` — `true` → theorem/redundancy/conditional/tautology, `false`
→ rejection/challenge-to-M/reductio/fork/self-contradictory, `unknown` →
new-fact/hypothesis/conjecture/definition/fork. The verdict only **annotates** the band; it
**under-determines** the disposition, which the human-as-Agonothetes decides on *collateral
warrant the contest cannot supply* (the same `false` is the physician's "reject — M is
complete" or the student's "challenge M"). Input to the adjudication is therefore **(verdict,
`Play`, identity-of-M, + the human's collateral judgment)** — three from the machine, one
irreducibly from the interpreter.

**One persistence seam for increment 4 to mind.** The existing asserting path
(`agonothetes.apply_disposition` → `_episode_to_chain`) builds the corpus `TransformationChain`
from **transformation-game moves** (`move.rule`/`move.role`, Dau rules + per-move EGI
snapshots). The semantic-game contest's record is a **`Play`** (selectives + choices), which
§5 deliberately keeps *distinct* from a `TransformationChain`. So the asserting disposition
needs a **`Play`-aware warrant** — either a `Play`→chain adapter or a `ChainStep` that carries
the `Play` as provenance directly — rather than reusing `_episode_to_chain` unchanged. The
disposition *selection* (`available_dispositions`) needs nothing new; only the *persistence*
does.

The Agonothetes' disposition taxonomy (`available_dispositions`, already verdict-annotated)
gains the contest outcome as its evidence: a *deduction* disposition is warranted by a Graphist
win; *independent* by an UNKNOWN episode; a Grapheus win blocks assertion.

---

## 8. Wiring (reuse, don't rebuild)

The interpretation register is already most of the machinery; the contest is its interactive
form. Concretely:

- **New module** `src/grapheus.py` — the extensive-form driver over `semantic_game`. Pure,
  headless, deterministic (no I/O). Exposes: start a `Play` from `(G, oracle, closed)`; given
  a human Graphist choice, apply it and **auto-advance** through forced choices and Grapheus
  moves to the next contested frontier (or terminal); return the updated `Play`. Self-play /
  hint mode = the driver plays *both* sides from the evaluator.
- **Routes** (`src/web_api/routes/agon.py`) — beside the one-shot `/agon/interpret`, add the
  move-by-move contest: start (reuse `_interpret_payload`'s model resolution + the `materialize`
  flag), apply-graphist-move, get-play, concede. Non-mutating to the corpus until the explicit
  assert step. The model picker (`/agon/models`, curated + corpus UoDs incl. the new
  `skos_core`) is unchanged — every model M is already a contest opponent.
- **Frontend** (`web_viewer/agon.html`) — render the `Play`: the current frontier as the
  human's legal choices, the Grapheus's last move + its selective, the accumulated bindings,
  the running outside-in transcript (the evaluator already produces it), and the outcome with
  its disposition annotations. Reuse `diagram-viewer.js` to show the current sub-graph under
  contest.

A good first opponent is **`skos_core`** (landed 2026-06-12): a populated, rule-bearing M whose
materialised closure gives the Grapheus non-trivial selectives — e.g. proposing
`~[ (broaderTransitive "Dog" "Animal") ]`-style challenges, or defending `Dog ⊳ Animal` against
a Grapheus that must concede because the transitive closure supplies the witness.

---

## 9. Build order (each a shippable increment)

1. **`src/grapheus.py` + tests** — the headless driver: `Play` state, the polarity-owned choice
   enumeration, auto-advance through forced/Grapheus moves, terminal detection, `independent`
   on UNKNOWN. Self-play reproduces `evaluate()`'s verdict on the corpus (the conformance test:
   driver-to-terminal value == one-shot peel value, every tomos G × the example models).
2. **Routes + payload** — start/apply/get/concede over the driver; reuse model resolution +
   `materialize`. Route tests: the five persona episodes replay move-by-move to the same verdict;
   a `skos_core` episode closes the broaderTransitive challenge.
3. **Frontend** — the interactive board; Playwright E2E (draw a proposal → contest a corpus M →
   reach a verdict → see the disposition).
4. **The warrant step** — the corpus-boundary `ChainStep` "withstood Agon", referencing the
   `Play`; the import↔Agon arc closed for a single G. (Design the warrant axis in
   `CHAIN_OF_SEMIOSIS.md` terms before building.) **Mind the §7 persistence seam:** the existing
   `agonothetes._episode_to_chain` is transformation-game-shaped, so this needs a `Play`-aware
   warrant, not a reuse. Disposition *selection* (`available_dispositions`) is already correct —
   the outcome trichotomy fits the taxonomy with no new keys.

Increment 1 is the whole logical core; 2–4 are surface + persistence.

---

## 10. Open questions deferred (not blocking increment 1)

- **Beta sub-game ordering.** When an area has several local ligatures *and* several
  conjuncts, the order in which the owner is asked is a strategic detail; the *value* is
  order-independent (the evaluator already exhausts it), but the *play* (and the transcript's
  legibility) depends on a chosen order. Default: outermost-first, then left-to-right by area
  signature — confirm against a few hand-played episodes.
- **Imperfect information** (Pietarinen's hidden-role variant) — a later register, not now.
- **Materialised vs. queried M during a long contest.** Materialising once up front (current
  `/interpret` behaviour) is simplest; demand-driven oracle queries mid-contest
  (`DOMAIN_ORACLE_AND_M.md` step 4) would scale to large/remote M. Defer until a contest needs
  an M too big to materialise.
- **Two-Grapheus / dialogue between minds** — `CHAIN_OF_SEMIOSIS.md`'s fuller social regime-2
  (an assertion tested *between two parties*, not one human vs. the model) is the horizon past
  this; the automated Grapheus is the machine standing in for Nature, the first step toward it.
