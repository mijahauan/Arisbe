"""Arisbe's mechanical referee, exposed as an MCP stdio server.

This is the *transport* half of the MCP verifier service (R3): a thin wrapper
that registers the pure functions in :mod:`mcp_verifier` as Model Context
Protocol tools, so any MCP-speaking agent framework (Claude Desktop, an SDK
agent, another orchestrator) can call Arisbe's calculus core — parse+validate,
the three-valued peel against a supplied model M, sound Dau-rule application,
and §3.3 correspondence attestation — over stdio.

The wrapper holds **no logic**: every tool delegates to :mod:`mcp_verifier`,
which imports no MCP SDK and is fully tested in CI. The ``mcp`` dependency is an
optional extra (``pip install 'arisbe[mcp]'`` / ``uv sync --extra mcp``); this
module import-guards it so the rest of the codebase is unaffected when the extra
is absent.

Run it:

    uv run --extra mcp python -m mcp_server         # stdio server on stdin/stdout

or point an MCP client's server config at that command. Every tool returns a
JSON object; a content error (unparseable EGIF, unsound move) comes back as
``{"ok": false, "error": ...}`` rather than raising, so the agent always gets a
legible answer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import mcp_verifier

try:  # The optional `mcp` extra. Guarded so the module imports cleanly without it.
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised by the extra-absent CI path
    FastMCP = None  # type: ignore[assignment]
    MCP_AVAILABLE = False


SERVER_NAME = "arisbe-verifier"

SERVER_INSTRUCTIONS = """\
Arisbe is a mechanical referee for Existential Graphs (Peirce's diagrammatic
logic, formalised by Dau). Propositions and models are supplied as EGIF strings
(the linear form of an existential graph). The referee decides; it does not
argue — every tool reduces its input to a calculus artifact and re-checks it.

Tools:
  • check_egif(egif)  — parse + validate a graph; returns its structure and a
    canonical, content-addressed `elements` list (ids like sheet/v0/e0/cut0).
  • peel(egif, model) — evaluate a proposition G against a model M (three-valued:
    TRUE / FALSE / UNKNOWN, open-world by default), with witness/counterexample.
  • apply_rule(egif, rule, ...) / validate_step(...) — apply or dry-run one sound
    Dau transformation rule (DC+ DC- INS ERA IT+ IT-); reference elements by the
    canonical ids from check_egif.
  • attest(egif) — lay the graph out and attest §3.3 correspondence between the
    graph and its drawing (picture and proposition denote the same object).

Scope: Alpha (propositional) and Beta (first-order, lines of identity) graphs.
Gamma / second-order features are a documented future direction, not yet served.
"""


def build_server() -> "FastMCP":
    """Construct the FastMCP server with every verifier tool registered.

    Raises ``RuntimeError`` if the optional ``mcp`` extra is not installed.
    """
    if not MCP_AVAILABLE:
        raise RuntimeError(
            "the 'mcp' extra is not installed; run `uv sync --extra mcp` "
            "(or `pip install 'arisbe[mcp]'`) to serve the verifier"
        )

    mcp = FastMCP(SERVER_NAME, instructions=SERVER_INSTRUCTIONS)

    @mcp.tool()
    def check_egif(egif: str) -> Dict[str, Any]:
        """Parse an EGIF string and confirm it is a well-formed existential graph.

        Returns the vertex/edge/cut counts, the relation names, the canonical
        round-trip EGIF, and an `elements` list giving each element a stable,
        content-addressed id (sheet / v0 / e0 / cut0) to use in apply_rule.
        """
        return mcp_verifier.check_egif(egif)

    @mcp.tool()
    def peel(
        egif: str,
        model: Union[str, Dict[str, str]],
        closed: bool = False,
    ) -> Dict[str, Any]:
        """Evaluate proposition G (`egif`) against model M (`model`).

        `model` is an EGIF string, or a {name: egif} object for several models
        tried in order. `closed` = closed-world (a miss is FALSE) vs. the default
        open-world (a miss is UNKNOWN). Returns the three-valued verdict, a
        transcript, and — when decisive — a witness or counterexample.
        """
        return mcp_verifier.peel(egif, model, closed=closed)

    @mcp.tool()
    def apply_rule(
        egif: str,
        rule: str,
        selection: Optional[List[str]] = None,
        egif_content: Optional[str] = None,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply one sound Dau transformation rule and return the resulting graph.

        `rule` is DC+ / DC- / INS / ERA / IT+ / IT-. Reference elements by the
        canonical ids from check_egif. INS needs egif_content + a negative
        `target` area; IT+ needs `selection` + a nested `target`; DC+ takes
        `selection` and/or `target`; DC-/ERA/IT- take `selection`. An unsound
        move returns {ok: false, error: ...}.
        """
        return mcp_verifier.apply_rule(
            egif, rule, selection=selection, egif_content=egif_content, target=target
        )

    @mcp.tool()
    def validate_step(
        egif: str,
        rule: str,
        selection: Optional[List[str]] = None,
        egif_content: Optional[str] = None,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check whether a Dau-rule move would be sound, without keeping the result.

        Same parameters as apply_rule; returns {ok: true} or {ok: false, error}.
        """
        return mcp_verifier.validate_step(
            egif, rule, selection=selection, egif_content=egif_content, target=target
        )

    @mcp.tool()
    def attest(egif: str, style: Optional[str] = None) -> Dict[str, Any]:
        """Lay the graph out and attest §3.3 correspondence (graph ↔ drawing).

        Returns {ok: true, attested: true, ...} when the drawn form denotes the
        same object as the graph, or the §3.3 failures otherwise. `style` selects
        a visual style (default = dau-compliant); style never changes meaning.
        """
        return mcp_verifier.attest(egif, style=style)

    return mcp


def serve() -> None:
    """Run the stdio MCP server (blocking). Entry point for ``python -m mcp_server``."""
    build_server().run()


if __name__ == "__main__":
    serve()
