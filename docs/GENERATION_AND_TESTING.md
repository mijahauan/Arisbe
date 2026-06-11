# Generation and Testing: making (Ergasterion) vs the game (Agon)

**Status**: design-of-record · **Drafted**: 2026-06-11

> The question: the Endoporeutic Game peels a proposition outside-in against a model
> M (eliminative), whereas proof-building, generalizing, and abducing head the other
> way (additive). Where does the Agon/Ergasterion boundary fall — and what is the
> dialogue the arena only stubs today?

## The cut: eliminative vs additive

- **Eliminative moves** (IT−, DC−, ERA) decompose G against M — they *peel the
  onion*. **This is the game = Agon (testing).**
- **Additive moves** (INS, IT+, DC+, and the derived rules that build proofs,
  arguments, theorems, generalizations, abductions) — they *construct*. **This is
  making = Ergasterion.**

The directionality the question names is real, but it is not the mode boundary by
itself; it is the difference between **making** a candidate sign and **testing** one.
Ergasterion generates candidate signs by any of the three reasonings; Agon puts them
at risk and decides what the result means. Generation is warrant-*claiming*; testing
is warrant-*conferring*.

## An inning of the Endoporeutic Game has three parts

Agon *is* this inning. Its basic framing tests **"given M, then G"** — evaluate the
proposal G against the reference world M, and decide what to do with the result.

```
  1. CHOOSE M     the reference context, under a particular model        [opening move]
  2. PEEL         eliminative decomposition of an already-built G,        [semantic_game.py — built]
                  outside-in, until nothing remains (G holds) or a
                  residue remains (G doesn't) → TRUE / FALSE / UNKNOWN
  3. DECIDE       the dialog about what to do with the outcome           [agonothetes — taxonomy]
                  — theorem · new fact · revise/complete M · conjecture …
```

Part 2 is the semantic game (`src/semantic_game.py`); part 1 is a thin opening (the
existing Agon already frames `~[ M ~[ G ] ]`); part 3 is the disposition taxonomy
(`agonothetes.py`). The frame `~[ M ~[ G ] ]` reads literally as **M → G**.

## What the inning is *not*

There is **no separate dialogical-contest engine** with commitment ledgers to build.
The "dialogue" that was under-described is **part 3** — the decision about the
residue. That is where M becomes **contestable**: "complete M," "revise M," "accept
as a new fact," "hold as a conjecture" are *decisions about the outcome*, not
separate game moves. The genuinely adversarial character is the *choices during the
peel* (whose witness, which conjunct) plus the *freedom of the decision*.

## Three clarifications the personas forced (see `ARISBE_PERSONAS.md`)

1. **M is an extensional model; the peel is model-checking, not inference.** The
   oracle reads M's ground atomic facts; it does not run M's rules to derive new
   facts. The syllogism is *checked against* a world, not *derived* from it.
   Rules-in-M (forward chaining) is a separate, deferred question.
2. **The peel checks truth-in-a-model, not validity.** Under three-valued (Kleene)
   logic, `P → P` reads UNKNOWN when P is unknown — the game does not certify
   tautologies. **Validity** (truth in *all* models) is established by **construction**
   in Ergasterion (the sound-step proof chain), not by the game.
3. **The part-3 disposition is a judgment, not a function of the verdict.** Two
   innings can return the same FALSE and mean opposite things — the student's
   counterexample (Whale, which M *positively* records as warm-blooded) means
   *reject the generalization*; the physician's (Biscuit, on which M is *silent*)
   means *complete M*. The peel makes the **grounds** visible (M's denial vs M's
   silence); the decision rests on collateral warrant the verdict alone cannot
   supply. So part 3 annotates dispositions by the verdict but **never narrows or
   auto-asserts** — the meaning stays the Agonothetes' to assign.

## The reasonings, located

| Reasoning | Truth-preserving? | Where it lives | Earns the corpus by |
|---|---|---|---|
| **Deduction** | yes (Dau) | construct in Ergasterion (ProofChain) | being **tested through Agon** — self-certifies *validity*, not *warrant*; premises stay challengeable |
| **Induction** | no (ampliative) | generalize in Ergasterion (a conjecture-rule) | surviving Agon → `new_fact` disposition |
| **Abduction** | no (ampliative) | leap to a hypothesis in Ergasterion | surviving Agon → `abductive_hypothesis` / the inverse pivot, below |

**Deduction earns the corpus through Agon like everything else.** A sound proof is
*made* in Ergasterion (each step attested), then *tested* in Agon before assertion —
"asserted = withstood challenge." The contest may be a formality the Proposer always
wins, but it produces the provenance of having been offered for challenge. There is
no direct workshop→corpus route.

## The inverse pivot (forward direction)

Because the inning parameterizes on M (part 1 is choosing it), the same machinery
turns around: **"in what domain does this proposition make sense?"** — run the peel
across candidate models and rank by how well G holds. That is abductive
context-retrieval; it reuses the oracle unchanged. See
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

Related: [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (the two formalisms),
[CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) (the regimes; asserted = withstood
challenge), [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) (M as oracle),
[ARISBE_PERSONAS.md](ARISBE_PERSONAS.md) (the worked innings).
