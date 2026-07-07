# Contributing to Arisbe

Arisbe is a working environment for Peirce's Existential Graphs — *doing logic in pictures*,
with Dau's formalization as the guarantor of correctness. This file orients an outside
contributor. The deep guidance lives in [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md);
this is the map to it. (Written from the STORM documentation audit, G4.)

## The one thing to understand first: protected core vs additive surface

Arisbe has a small **protected mathematical core** — 14 modules that are the genuine
calculus (the immutable data model + IO, the diachronic state, the Dau rules + validators,
the ligature machinery, and the three correspondence enforcers). They cannot be modified
without deliberate authorization:

```bash
uv run python tools/core_protection_system.py --report   # what's protected, and why
touch .core_modification_authorized                       # required before editing one
```

**Almost everything interesting is additive** and touches no protected module — new
membranes, new lenses, new linear formats, new exporters, new agents. If your change
*imports* a core module rather than *modifying* it, you are on the additive surface and the
protection system will not object. Design your contribution to stay there if you possibly
can; a change to the core owes a much higher bar (below).

## The bar

**The mathematical core test suite must always pass** (~118–152 tests covering
`egi_core_dau`, the transformation rules, the validators, the isomorphism engine, the
Beta/logical proof exercises). A commit runs the quality gate automatically:

```bash
uv run pytest tests/ -q                              # full suite (~1000 tests)
uv run python tools/quality_gate_system.py           # the pre-commit gate (core protection + core tests + syntax)
```

Conventions the codebase holds you to:

- **Offline-deterministic first, live behind a flag.** Anything touching the network or an
  LLM takes an *injectable* fetch/client (the real call is never made in CI) and ships a
  `ReplaySource`/record-replay fixture or a scripted fake. See `wikidata_source.py`,
  `weather_source.py`, `agon_llm.py` for the pattern.
- **Every new check needs a falsifier.** A test that proves the check *bites* — an
  adversarial input that must be refused — not only the happy path. The correspondence and
  refusal tests are built this way.
- **Correspondence is the contract.** If your code produces or consumes an (EGI, LayoutDTO)
  pair for an asserted graph, you are likely obligated to attest §3.3 at that boundary
  (`correspondence_attestation.attest_correspondence`). Geometry-free additions (a membrane,
  a headless lens, a meta-learning readout) carry **no** §3.3 obligation — that's why most
  of the automated-inquiry stack is additive and unprotected. Read
  [`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md) before
  touching anything on the asserted path.

## The extension sockets

Most contributions plug into a documented Protocol rather than modifying anything:

- **A new live source or membrane** → implement `LiveSource` (`fetch`/`exhausted`) and/or a
  `Proposer`; wrap it with a `feed_factory`. Copy the closest existing shape:
  raise-only (`discourse_membrane`), raise-and-resolve (`resolving_membrane` /
  `weather_source`), or conflict+resolution (`wiki_dispute_membrane`). Design of record:
  [`docs/AUTOMATED_ENDOPOREUTIC_GAME.md`](docs/AUTOMATED_ENDOPOREUTIC_GAME.md).
- **A new panel agent** → implement `PolicyAgent.vote`; drop it into an `Agonothetes` panel.
- **A new read-only Organon lens** → a `GET /organon/uods/{id}/<lens>` route + a
  `web_viewer/js/<lens>-lens.js` module; geometry-free lenses add no §3.3 obligation. The
  modal and audit lenses are the templates.
- **A new linear format** → a parser + generator pair sharing `canonical_signature.py`, with
  corpus round-trips across the tomos examples (`test_tomos_parsing.py` is the contract). The
  EGIF/CGIF/CLIF parsers are *not* protected — they are application-level I/O.
- **A new reference/definition resolver** → implement `ReferenceResolver`.

## Where knowledge lands

New knowledge a membrane produces reaches the attested corpus only through
`TomosService.save_uod_with_chain` (which attests §3.3 at the write) — and carries a
**warrant label** (imported/live content is low-warrant by construction; nothing
auto-promotes to high warrant, and there is no direct workshop→corpus route). The
philosophical invariants in `MANIFEST_AND_MEANING.md`, `LEVEL_ZERO_AND_THE_REGISTERS.md`, and
`FIDELITY_AND_DEPARTURES.md` are binding, not decorative: *nothing auto-asserts*, *attest
correspondence, not truth*.

## Practical

- **Setup:** `uv sync --extra dev --extra web` (Python 3.12). Run things via `uv run`.
- **API discovery:** never guess a signature — `grep` in
  [`docs/ARISBE_CORE_API_REFERENCE.md`](docs/ARISBE_CORE_API_REFERENCE.md), or hit the live
  HTTP spec at `/openapi.json` (see `install.qmd`).
- **License:** MIT (see [`LICENSE`](LICENSE)).
- **Where truth lives when docs lag code:** the tests are authoritative, then
  `CAPABILITY_MAP.md` and the auto-generated API reference; `CURRENT_PLAN.md` is the
  chronological log of what changed and why.
- **This is a research system under active daily change** by a small author + agent loop. A
  bug report pointing at a failing test or a traceback is the most useful contribution; a new
  exemplar, lens, membrane, or format that respects the bar above is very welcome. Open an
  issue or a PR against `main`.
