# Generation and Testing: making (Ergasterion) vs the game (Agon)

**Status**: design-of-record · **Drafted**: 2026-06-11

> The question: the [Endoporeutic](GLOSSARY.md#endoporeutic) Game [peels](GLOSSARY.md#peel) a proposition outside-in against a model
> M (eliminative), whereas proof-building, generalizing, and abducing head the other
> way (additive). Where does the Agon/Ergasterion boundary fall — and what dialogue
> does the arena only stub today?

## The cut: eliminative vs additive

- **Eliminative moves** (IT−, DC−, ERA) decompose G against M — they *peel the
  onion*. **This is the game = Agon (testing).**
- **Additive moves** (INS, IT+, DC+, and the derived rules that build proofs,
  arguments, theorems, generalizations, abductions) — they *construct*. **This is
  making = Ergasterion.**

The directionality the question names holds real, but it does not by itself draw the
mode boundary. It marks the difference between **making** a candidate sign and
**testing** one. Ergasterion generates candidate signs by any of the three reasonings.
Agon puts them at risk and decides what the result means. Generation *claims*
[warrant](GLOSSARY.md#warrant); testing *confers* it.

## An episode of the Endoporeutic Game has three parts

Agon *is* this [episode](GLOSSARY.md#episode). Its basic framing tests **"given M, then G"**: evaluate the
proposal G against the reference world M, then decide what to do with the result.

```
  1. CHOOSE M     the reference context, under a particular model        [opening move]
  2. PEEL         eliminative decomposition of an already-built G,        [semantic_game.py — built]
                  outside-in, until nothing remains (G holds) or a
                  residue remains (G doesn't) → TRUE / FALSE / UNKNOWN
  3. DECIDE       the dialog about what to do with the outcome           [agonothetes — taxonomy]
                  — theorem · new fact · revise/complete M · conjecture …
```

Part 2 runs the semantic game (`src/semantic_game.py`). Part 1 makes a thin opening —
the existing Agon already frames `~[ M ~[ G ] ]`. Part 3 holds the disposition taxonomy
(`agonothetes.py`). The frame `~[ M ~[ G ] ]` reads literally as **M → G**.

## What the episode is *not*

Nobody needs to build a **separate dialogical-contest engine** with commitment
ledgers. The "dialogue" that stood under-described lives in **part 3**, the decision
about the residue. There M becomes **contestable**. "Complete M," "revise M," "accept
as a new fact," "hold as a conjecture" — these name *decisions about the outcome*, not
separate game moves. The genuinely adversarial character lies in the *choices during
the peel* (whose witness, which conjunct) and in the *freedom of the decision*.

## Three clarifications the personas forced (see `ARISBE_IN_PRACTICE.md`)

1. **M is an extensional model; the peel is model-checking, not inference.** A
   *model* means the facts, the extension over a domain; *rules* belong to a *theory*.
   The peel checks G against the facts. It does not run M's rules to derive new ones,
   so the syllogism gets *checked against* a world, not *derived* from it. To make M "as
   full as possible," author it as facts + Horn-shaped rules and **materialize** it
   (forward-chain to the least Herbrand model) *before* the peel. That principled
   bridge keeps model-checking pure while letting rules fill out the world. Full
   FOL rules (existential / disjunctive / negated heads) and modality (no γ-graphs,
   so a single world, not a Kripke frame) fall outside, to the contest/deduction game.
   See [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) §6.1.
2. **The peel checks truth-in-a-model, not validity.** Under three-valued (Kleene)
   logic, `P → P` reads UNKNOWN when P is unknown, so the game does not certify
   tautologies. **Validity** (truth in *all* models) comes by **construction**
   in Ergasterion (the sound-step proof chain), not from the game.
3. **The part-3 disposition stands as a judgment, not a function of the verdict.** Two
   episodes can return the same FALSE and mean opposite things. The student's
   counterexample (Whale, which M *positively* records as warm-blooded) means
   *reject the generalization*; the physician's (Biscuit, on which M is *silent*)
   means *complete M*. The peel makes the **grounds** visible (M's denial vs M's
   silence). The decision rests on collateral warrant the verdict alone cannot
   supply. So part 3 annotates dispositions by the verdict but **never narrows or
   auto-asserts**. The meaning stays the [Agonothetes](GLOSSARY.md#agonothetes)' (the role that turns the game's outcome into an act of inquiry) to assign.

## The reasonings, located

| Reasoning | Truth-preserving? | Where it lives | Earns the corpus by |
|---|---|---|---|
| **Deduction** | yes (Dau) | construct in Ergasterion (ProofChain) | being **tested through Agon** — self-certifies *validity*, not *warrant*; premises stay challengeable |
| **Induction** | no (ampliative) | generalize in Ergasterion (a conjecture-rule) | surviving Agon → `new_fact` disposition |
| **Abduction** | no (ampliative) | leap to a hypothesis in Ergasterion | surviving Agon → `abductive_hypothesis` / the inverse pivot, below |

**Deduction earns the corpus through Agon like everything else.** A sound proof gets
*made* in Ergasterion (each step attested), then *tested* in Agon before assertion —
"asserted = withstood challenge." The contest may amount to a formality the Proposer
always wins, but it produces the provenance of having been offered for challenge. No
direct workshop→corpus route exists.

## The inverse pivot (forward direction)

Because the episode parameterizes on M (part 1 chooses it), the same machinery
turns around. **In what domain does this proposition make sense?** Run the peel
across candidate models and rank by how well G holds. That gives abductive
context-retrieval, and it reuses the oracle unchanged. See
[DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) §7.

## What is built (2026-06-11)

- **Part 2 — the peel:** `src/semantic_game.py` — `evaluate(egi, oracle)` →
  three-valued `Verdict3` + outside-in transcript + structured `winning_witness` /
  `counterexample` (the evidence part 3 rests on). Kleene logic, sound open-world.
- **The model M:** `src/domain_oracle.py` — `CorpusOracle` (resolve / witness /
  match_atoms / individuals). M is queried, not materialised
  ([DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md)).
- **The interpretation register in Agon:** `POST /agon/games/{id}/interpret` (peel G
  against M, non-mutating) and `set-model` (part 1); `available_dispositions(game,
  verdict)` annotates part 3 by the outcome. `src/web_api/routes/agon.py`,
  `agon_session_manager.py`, `agonothetes.py`.

Since then the testing register has also been **automated end to end**. The game plays
autonomously: a proposer (the *membrane*) voices a claim, the peel tests it against a
developing M, a panel (mechanical or LLM) negotiates the disposition, M revises, and disuse
decays what fell from use — including against live external sources (Wikidata). The episode
grammar in this chapter stays unchanged. Only the players are optional. See
[AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) and
[CAPABILITY_MAP.md](CAPABILITY_MAP.md) §H.

Related: [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (the two formalisms),
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the regimes; asserted = withstood
challenge), [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) (M as oracle),
[ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) (the personas + worked episodes).
