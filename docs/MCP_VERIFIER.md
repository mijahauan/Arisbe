# The MCP verifier service — Arisbe's referee, callable from outside

**Status:** SHIPPED (2026-07-07). **Modules:** [`src/mcp_verifier.py`](../src/mcp_verifier.py)
(logic) · [`src/mcp_server.py`](../src/mcp_server.py) (transport). **Tests:**
[`tests/test_mcp_verifier.py`](../tests/test_mcp_verifier.py). Additive, non-core.

## What it is

Arisbe's mechanical referee — the part that *decides*, not the part that argues — exposed
as [Model Context Protocol](https://modelcontextprotocol.io) tools any MCP-speaking agent
framework (Claude Desktop, an SDK agent, another orchestrator) can call over stdio. It is
the highest external-leverage adoption move on the [consolidate/adopt track](PROSPECTS_MULTIPERSPECTIVE.md):
LLM agents are fluent at *proposing* logic and unreliable at *checking* it; Arisbe already
owns a sound, attested checker. The MCP wave makes that checker a drop-in dependency.

The governing principle is the one the [automated Endoporeutic Game](AUTOMATED_ENDOPOREUTIC_GAME.md)
runs on: **the LLM argues, the calculus decides.** Every tool reduces its input to a
calculus artifact and re-checks it. An unparseable graph, an unsound rule move, or a drawing
that violates §3.3 fails loudly with a legible message. Nothing is taken on the agent's word.

## The five tools

Propositions and models are supplied as **EGIF** strings (the linear form of an existential
graph — see [GLOSSARY.md](GLOSSARY.md#egif)). Every tool returns a JSON object; a *content*
error (bad EGIF, unsound move) comes back as `{"ok": false, "error": ...}` rather than
raising, so an agent always receives a usable answer.

| Tool | Does | Backed by |
|---|---|---|
| `check_egif(egif)` | Parse + validate a graph. Returns vertex/edge/cut counts, relation names, the canonical round-trip EGIF, and an `elements` list giving each element a **stable, content-addressed id** (`sheet` / `v0` / `e0` / `cut0`). | `egif_parser_dau`, `canonical_signature` |
| `peel(egif, model, closed=False)` | Evaluate a proposition **G** against a model **M** (an EGIF string, or a `{name: egif}` object for several models tried in order). Three-valued: `TRUE` / `FALSE` / `UNKNOWN` (open-world by default; `closed=True` makes a miss FALSE). Returns a transcript and, when decisive, a `witness` or `counterexample`. | `semantic_game.evaluate`, `domain_oracle.CorpusOracle` |
| `apply_rule(egif, rule, …)` | Apply one **sound Dau transformation rule** (`DC+` `DC-` `INS` `ERA` `IT+` `IT-`) and return the resulting graph. Elements are named by the canonical ids from `check_egif`. An unsound move returns the engine's own rejection message. | `proof_authoring.apply_rule` (via `rule_interaction`) |
| `validate_step(egif, rule, …)` | Dry-run: is the move sound? `{"ok": true}` or `{"ok": false, "error": …}`, no result graph kept. | same |
| `attest(egif, style=None)` | Lay the graph out and **attest §3.3 correspondence** between graph and drawing — the guarantee that picture and proposition denote the same object. Returns the §3.3 failures on a mismatch. | `elk_layout_engine`, `correspondence_attestation.attest_correspondence` |

### Content-addressed element ids

Parse-time ids are per-parse UUID fragments (unstable across calls), so an agent can't
discover an id in one tool call and reference it in the next. `check_egif` therefore assigns
each element a **canonical label** derived from graph structure via `canonical_signature`
(UUID-independent): two parses of the same EGIF produce the same `sheet` / `v0` / `e0` /
`cut0` assignment. The rule tools resolve those labels against their own fresh parse, making
the discover-then-apply flow stateless. Truly symmetric elements may receive interchangeable
labels — harmless, since selecting either yields an isomorphic result. (Raw parse ids are
also accepted, for a caller that kept one.)

## Scope

**Alpha** (propositional) and **Beta** (first-order, lines of identity) existential graphs —
the whole of the calculus the rest of Arisbe serves. **Gamma / second-order** features are a
documented future direction ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md),
[ROADMAP.md](ROADMAP.md)), not yet served by this interface; the server's instructions say so
to the agent.

## Running it

The `mcp` dependency is an **optional extra**, import-guarded so the rest of the codebase is
unaffected when it is absent (the pattern of the `nl` extra):

```bash
uv sync --extra mcp                          # install the extra
uv run --extra mcp python -m mcp_server      # stdio server on stdin/stdout
```

Point an MCP client's server config at that command. Example (Claude Desktop
`claude_desktop_config.json`; adjust the path):

```json
{
  "mcpServers": {
    "arisbe-verifier": {
      "command": "uv",
      "args": ["run", "--extra", "mcp", "--directory", "/path/to/Arisbe",
               "python", "-m", "mcp_server"]
    }
  }
}
```

## Design notes

- **Two modules by intent.** `mcp_verifier.py` holds *all* the logic as plain functions
  taking and returning JSON-serialisable dicts, and imports **no** MCP SDK — so the whole
  contract is testable in CI whether or not the extra is installed. `mcp_server.py` is a thin
  transport wrapper that registers those functions as `FastMCP` tools. The single source of
  truth is `mcp_verifier.TOOLS` (name → callable + description); tests iterate it to confirm
  coverage.
- **A wrapper, not new logic.** Every tool delegates to machinery that already existed and is
  already tested elsewhere. The one small addition is the canonical-id addressing layer
  (above), reusing `canonical_signature`.
- **No live model, ever.** The server exposes a checker; there is no LLM inside it. The gated
  server test runs an in-process tool round-trip; the pure-function tests need nothing beyond
  the base install.
- **Companion spec.** The `attest` tool *enforces* the correspondence contract that
  [CORRESPONDENCE_CONTRACT.md](CORRESPONDENCE_CONTRACT.md) states prover-agnostically — a
  second implementation could check the same property and interoperate over the same EGIF +
  tomos corpus.
