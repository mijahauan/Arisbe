# NL→logic — *LLM proposes, Arisbe disposes*

**Status:** increment 1 built 2026-06-18 (`src/nl_to_logic.py`, `tools/nl_to_logic_cli.py`,
`POST /agon/propose-nl`). This front-end of the NL→logic arc waited, deliberately, until both
reasoning backends (DLCore + FOLIO + the Existential Graph Instance ([EGI](GLOSSARY.md#egi)) model-finder bridge) and the vocabulary-miss gate
(`dl_reasoning.OUT_OF_SIGNATURE`) stood in place.

## The idea

Turning English into logic is two problems, and they want opposite tools:

1. **English → a *candidate* logical form** — the noisy parse. LLMs are good at this and bad at
   guaranteeing the result means anything.
2. **candidate form → verified / interpreted / drawable proposition** — Arisbe's home turf. The
   correspondence engine, the [peel](GLOSSARY.md#peel) (reading it from the outside in against the model), the soundness [floor](GLOSSARY.md#floor) (the baseline that may not be gone under).

So Arisbe is the **interpretant / verifier behind the parser, not the parser**. It should never
become a wide-coverage semantic parser; its contribution begins once a candidate form exists.
This is the **FoVer** architecture — *LLM proposes, Arisbe disposes* — and the import↔Agon arc
already embodied it for linear forms; the LLM front-end extends it to natural language.

## The boundary (load-bearing)

The division of labour is strict and is what keeps the addition sound:

| The **LLM** does | Arisbe does |
|---|---|
| read one English proposition | parse the candidate **deterministically** |
| emit a **candidate FOL string** in the `folio_fol` grammar (`∀ ∃ ¬ ∧ ∨ → ↔ ⊕` + predicates + constants) | build the EGI (`parse_fol` → `folio_fol_to_egi` → `generate_egif`) |
| declare its vocabulary (predicates→arities, constants) | reconcile that vocabulary against M |
| flag a sentence it can't express (`unmappable`) | test the proposal against M (the peel) |

The LLM **never produces an EGI and never asserts truth.** A malformed candidate is *reported*
(`parse_error`), never repaired. An LLM that hallucinates a predicate is caught by a
declared-vs-used cross-check. The whole "disposing" half is deterministic and was already
built and tested before the LLM was wired in.

This proposer seat is now **one of three LLM seats**. The automated Endoporeutic Game
(`src/agon_llm.py`) puts an LLM in each role — Graphist (voice a doubt), Grapheus (defend the
model), Agonothetes (judge among the votes) — and every seat honors the same boundary: each
LLM move is reduced to a calculus artifact and re-checked before it counts (*the LLM argues,
the calculus decides*). This chapter's contract (`nl_to_logic`) is the shared reduction path
all three roles use. See [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md).

## Vocabulary-miss vs fact-miss

The distinction the NL-parse use case turns on (and the reason the front-end waited until the
backend could make it):

- **vocabulary miss** — G uses a predicate M never defined: *"M can't even address that"* — the
  integrity-gate "not even wrong". Surfaced by `reconcile()` as `out_of_signature`
  (via `dl_reasoning.ontology_signature`).
- **fact miss** — G speaks M's vocabulary but the fact isn't entailed: *"M can't confirm that"* —
  the open-world `UNKNOWN`/`FALSE` the peel returns.

Conflating these would drown the register in undiagnosable UNKNOWNs; separating them is what
makes "in what world does this make sense?" answerable.

## The API (`src/nl_to_logic.py`)

```python
from nl_to_logic import propose, build_proposal, reconcile, interpret_against

# Full arc (needs the `nl` extra + an API key):
prop = propose("Every mammal is warm-blooded", vocabulary_hint={"mammal", "warmblooded"})

# Deterministic half only (no LLM): hand a candidate FOL straight in.
prop = build_proposal("Every mammal is warm-blooded",
                      fol="∀x (mammal(x) → warmblooded(x))")

prop.parsed        # did it parse into an EGI?
prop.egif          # the drawable proposal G (deterministically derived)
prop.unmappable    # the LLM's honest "can't say this here" caveat (else None)
prop.parse_error   # the reported reason it didn't parse (never a crash)

M = '(mammal "Rex") (warmblooded "Rex")'
reconcile(prop, M).out_of_signature          # predicates M cannot address (vocab-miss)
interpret_against(prop, M, closed=True)["verdict"]   # the peel: true | false | unknown
```

- `propose(nl, *, vocabulary_hint=None, model="claude-opus-4-8", client=None)` — calls Claude
  via the `anthropic` SDK with **forced-tool structured output** (the `emit_fol` tool), adaptive
  thinking. The SDK import is **guarded by `ANTHROPIC_AVAILABLE`** (like `folio_fol`'s
  `Z3_AVAILABLE`); the `client` is injectable so tests need no network. Any API/parse error is
  captured into the returned `Proposal` — `propose` never raises.
- `build_proposal(...)` — the deterministic core; reused by both `propose` and the `--no-llm`
  path. Derives the vocabulary from the AST when none is declared.
- `reconcile(proposal, model_egif) -> VocabReport` — the vocabulary-miss split.
- `interpret_against(proposal, model_egif, *, closed, materialize) -> dict` — the peel; mirrors
  the route helper `_interpret_payload` (returns verdict / transcript / witness / counterexample).

## The CLI (`tools/nl_to_logic_cli.py`)

```bash
# Deterministic — no API key needed (the whole disposing half):
uv run python tools/nl_to_logic_cli.py --no-llm \
    --fol "∀x (mammal(x) → warmblooded(x))" --model-example teacher-mammals

# Full arc (needs `uv sync --extra nl` + ANTHROPIC_API_KEY):
uv run python tools/nl_to_logic_cli.py --nl "Every mammal is warm-blooded" \
    --model-example teacher-mammals
```

Model picks: `--model-example <id>` (curated `agon_models`), `--model-uod <id>` (a corpus Universe of Discourse ([UoD](GLOSSARY.md#uod))),
or `--model-egif <…>` (raw). Prints the candidate FOL + vocabulary, the EGIF, the
vocabulary-reconciliation, and the verdict + witness/counterexample.

## The web route (`POST /agon/propose-nl`)

Takes `{nl, model_egif|model_uod, closed, materialize, model?}` and returns the proposal
(`fol`, `egif`, `predicates`, `confidence`, `unmappable`, `parse_error`, `vocab_mismatch`) plus,
when it parsed, the `vocabulary` reconciliation and the `interpretation` (the peel). An
unmappable sentence or a malformed candidate returns `parsed: false` with the reason — a
successful response, not an error (the honest "can't say that here" surface). Nothing is
asserted or persisted: the proposal sits at **LOW [warrant](GLOSSARY.md#warrant)** and earns warrant only by
withstanding Agon (the import↔Agon floor — the correspondence check (§3.3) attests *correspondence, not truth*).

## Setup

```bash
uv sync --extra dev --extra web --extra nl   # `nl` adds the anthropic SDK
export ANTHROPIC_API_KEY=…                    # only the live LLM path needs it
```

The `nl` extra is optional. The `--no-llm` path, the route's deterministic branches, and every
test except the opt-in live one run with the SDK absent.

## Tests

- `tests/test_nl_to_logic.py` (12 + 1 key-gated live) — the LLM is mocked (a fake client
  returning a canned `emit_fol` payload). Pins: round-trip into the right EGI via `same_graph`;
  malformed → reported, not crashed; `unmappable` honestly unbuilt; API-failure capture;
  declared≠used flag; the reconcile split; the peel verdict + a cross-check that
  `interpret_against` agrees with `/agon/interpret`'s `_interpret_payload`.
- `tests/test_propose_nl_route.py` (5) — the route end to end with the LLM mocked at
  `nl_to_logic._default_client`.

## Out of scope (named fast-follows)

- **Multi-candidate disambiguation** — emit G1,G2,G3 (several readings of an ambiguous sentence),
  test each against M, rank by verdict: *disambiguation by interpretation, not parser
  confidence* — the distinctively-Peircean use no LLM-only pipeline can do.
- **LOW-warrant persistence** — admit a tested proposal via `/import/admit` as a
  `LITERATURE_EXAMPLE` UoD carrying its NL source + LLM provenance as the bibliographic trace.
- The bidirectional reading is already half-built elsewhere: **one G against M1,M2,M3** is the
  existing inverse pivot (`/agon/where-it-holds`).
