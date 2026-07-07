"""The mechanical referee as a set of prover-agnostic verifier functions.

This module is the *logic* half of Arisbe's MCP verifier service (R3, the
consolidate/adopt track): it exposes the calculus core — parse+validate, the
three-valued peel against a supplied model M, sound Dau-rule application, and
§3.3 correspondence attestation — as plain functions that take and return
JSON-serialisable dicts. An LLM-agent framework (or any external prover) drives
those functions through the thin ``mcp_server`` wrapper; **this module imports no
MCP SDK**, so the whole contract is testable in CI with the optional ``mcp``
extra absent.

Governing principle (the same one the automated Endoporeutic Game runs on): the
LLM argues, the calculus decides. Every function here reduces its input to a
calculus artifact and re-checks it — an unparseable EGIF, an unsound rule move,
or a drawing that violates §3.3 fails loudly with a legible message rather than
being silently accepted.

The functions never raise on *content* errors (a malformed EGIF, a rejected
rule): they return ``{"ok": False, "error": ...}``. They raise only on a
genuine programming error (wrong argument type), so a caller can trust that a
returned dict is always a well-formed answer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

# Bare imports (src/ is on the path) — the project's standard pattern.
from egif_parser_dau import parse_egif
from egif_generator_dau import EGIFGenerator
from egi_core_dau import RelationalGraphWithCuts


# ---------------------------------------------------------------------------
# Canonical content-addressing.
#
# Parse-time element ids are per-parse UUID fragments (unstable across calls),
# so an external agent cannot discover an id in one call and reference it in the
# next. Canonical signatures (``canonical_signature``, UUID-independent) give a
# stable, content-derived label to every element: two parses of the same EGIF
# text produce the same ``sheet`` / ``v0`` / ``e0`` / ``cut0`` assignment. The
# rule tools accept these labels in ``selection`` / ``target`` and resolve them
# against the live parse — making the discover-then-apply flow stateless.
# ---------------------------------------------------------------------------

def _canonical_labels(egi: RelationalGraphWithCuts) -> Dict[str, str]:
    """Map each real element id (incl. the sheet) → a stable canonical label.

    The label is a pure function of graph *structure*, so it is identical
    across independent parses of the same EGIF. Truly symmetric elements may
    receive interchangeable labels — harmless, since selecting either yields an
    isomorphic result.
    """
    from canonical_signature import compute_canonical_signatures

    vs, es, cs = compute_canonical_signatures(egi)
    labels: Dict[str, str] = {egi.sheet: "sheet"}
    for prefix, sig in (("v", vs), ("e", es), ("cut", cs)):
        for i, (eid, _s) in enumerate(sorted(sig.items(), key=lambda kv: repr(kv[1]))):
            labels[eid] = f"{prefix}{i}"
    return labels


def _resolve_label(egi: RelationalGraphWithCuts, label: str) -> str:
    """Resolve a canonical label (or a raw element id) back to a live parse id."""
    inverse = {v: k for k, v in _canonical_labels(egi).items()}
    if label in inverse:
        return inverse[label]
    # Accept a raw id passed straight through (e.g. the caller kept one).
    if label == egi.sheet or any(label == e.id for e in egi.V) \
            or any(label == e.id for e in egi.E) or any(label == c.id for c in egi.Cut):
        return label
    raise KeyError(label)


def _element_index(egi: RelationalGraphWithCuts) -> List[Dict[str, Any]]:
    """A canonical, content-addressed listing of every element — the ids an
    agent references in :func:`apply_rule` / :func:`validate_step`."""
    from eg_navigation import kind_of, area_of

    def polarity_word(area_id: str) -> Optional[str]:
        try:
            pol, _depth = egi.area_polarity(area_id)
            name = getattr(pol, "name", str(pol)).lower()
            return "negative" if "neg" in name else "positive"
        except Exception:
            return None

    labels = _canonical_labels(egi)
    entries: List[Dict[str, Any]] = []
    real_ids = [egi.sheet] + [v.id for v in egi.V] + [e.id for e in egi.E] + [c.id for c in egi.Cut]
    for rid in real_ids:
        is_sheet = rid == egi.sheet
        entry: Dict[str, Any] = {"id": labels[rid], "kind": "sheet" if is_sheet else kind_of(egi, rid)}
        if not is_sheet:
            area = area_of(egi, rid)
            if area is not None:
                entry["area"] = labels.get(area, area)
        # Polarity of the region this element governs: the interior of a cut /
        # the sheet, or the containing area of a vertex or edge.
        gov = rid if (is_sheet or rid in {c.id for c in egi.Cut}) else area_of(egi, rid)
        pw = polarity_word(gov) if gov is not None else None
        if pw is not None:
            entry["polarity"] = pw
        if rid in egi.rel:
            entry["relation"] = egi.rel[rid]
        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _egif_summary(egi: RelationalGraphWithCuts, *, with_elements: bool = False) -> Dict[str, Any]:
    """A structural fingerprint of a parsed EGI — proof it is a well-formed
    graph, and enough shape for a caller to reason about without re-parsing."""
    relations = sorted({name for name in egi.rel.values()})
    summary: Dict[str, Any] = {
        "vertices": len(egi.V),
        "edges": len(egi.E),
        "cuts": len(egi.Cut),
        "relations": relations,
        # The canonical round-trip: a well-formed EGI regenerates to EGIF, and
        # two parses of one structure emit identical text (canonical_signature).
        "egif_canonical": EGIFGenerator(egi).generate(),
    }
    if with_elements:
        summary["elements"] = _element_index(egi)
    return summary


def _model_to_named_egifs(model: Union[str, Dict[str, str]]) -> Dict[str, str]:
    """Normalise the ``model`` argument of :func:`peel` to ``{name: egif}``.

    A bare string is the common case (one model M); a dict lets the caller
    supply several named models, tried in order (the ``CorpusOracle`` contract).
    """
    if isinstance(model, str):
        return {"M": model}
    if isinstance(model, dict):
        if not model:
            raise ValueError("model dict is empty; supply at least one named EGIF")
        return dict(model)
    raise TypeError(
        f"model must be an EGIF string or a {{name: egif}} dict, got {type(model).__name__}"
    )


# ---------------------------------------------------------------------------
# check_egif — parse + validate
# ---------------------------------------------------------------------------

def check_egif(egif: str) -> Dict[str, Any]:
    """Parse an EGIF string and confirm it is a well-formed EGI.

    Returns ``{"ok": True, ...structural summary...}`` on success, or
    ``{"ok": False, "error": <message>}`` when the text does not parse to a
    well-formed graph. The summary carries vertex/edge/cut counts, the relation
    names, and the canonical round-trip EGIF (``egif_canonical``) — the same
    text any second parse of this structure would emit.
    """
    if not isinstance(egif, str):
        raise TypeError(f"egif must be a string, got {type(egif).__name__}")
    try:
        egi = parse_egif(egif)
    except Exception as exc:  # parser raises many concrete types on bad input
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, **_egif_summary(egi, with_elements=True)}


# ---------------------------------------------------------------------------
# peel — the three-valued semantic game against a supplied model M
# ---------------------------------------------------------------------------

def peel(
    egif: str,
    model: Union[str, Dict[str, str]],
    *,
    closed: bool = False,
) -> Dict[str, Any]:
    """Evaluate the proposition ``egif`` (G) against a model ``model`` (M).

    ``model`` is an EGIF string (one model) or a ``{name: egif}`` dict (several,
    tried in order). ``closed`` selects the closed-world reading (M asserted
    complete → a miss is FALSE) vs. the default open-world reading (a miss is
    UNKNOWN).

    Returns a dict carrying the three-valued verdict (``"TRUE"`` / ``"FALSE"`` /
    ``"UNKNOWN"``), a one-line ``summary``, ``holds`` (True only on TRUE), the
    outside-in ``transcript``, and — when decisive — a ``witness`` (the
    assignment that made an existential hold) or ``counterexample`` (the
    individual that defeated a universal). Content errors (unparseable G or M)
    come back as ``{"ok": False, "error": ...}``.
    """
    from domain_oracle import CorpusOracle
    from semantic_game import evaluate

    try:
        g = parse_egif(egif)
    except Exception as exc:
        return {"ok": False, "error": f"G did not parse — {type(exc).__name__}: {exc}"}

    try:
        named = _model_to_named_egifs(model)
        oracle = CorpusOracle.from_egif(named, closed=closed)
    except Exception as exc:
        return {"ok": False, "error": f"M did not parse — {type(exc).__name__}: {exc}"}

    try:
        result = evaluate(g, oracle, closed=closed)
    except Exception as exc:
        return {"ok": False, "error": f"peel failed — {type(exc).__name__}: {exc}"}

    out: Dict[str, Any] = {
        "ok": True,
        "verdict": result.verdict.value,
        "summary": result.summary,
        "holds": result.holds,
        "closed": closed,
        "transcript": list(result.transcript),
    }
    if result.winning_witness:
        out["witness"] = dict(result.winning_witness)
    if result.counterexample:
        out["counterexample"] = dict(result.counterexample)
    return out


# ---------------------------------------------------------------------------
# apply_rule / validate_step — sound Dau-rule application
# ---------------------------------------------------------------------------

def apply_rule(
    egif: str,
    rule: str,
    *,
    selection: Optional[List[str]] = None,
    egif_content: Optional[str] = None,
    target: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply one Dau transformation rule to ``egif`` and return the result.

    ``rule`` is one of ``DC+`` / ``DC-`` / ``INS`` / ``ERA`` / ``IT+`` / ``IT-``.
    The other parameters mirror the ``RuleInteraction`` protocol:

      * ``INS``  — ``egif_content`` (the content to insert) + ``target`` (a
        negative area id)
      * ``IT+``  — ``selection`` (source elements) + ``target`` (a nested area)
      * ``DC+``  — ``selection`` and/or ``target`` (empty selection + target
        inserts a truly empty double cut there)
      * ``DC-`` / ``ERA`` / ``IT-`` — ``selection`` only

    ``selection`` / ``target`` name elements by the **canonical labels**
    (``sheet`` / ``v0`` / ``e0`` / ``cut0``) that :func:`check_egif` returns in
    its ``elements`` list — stable, content-derived, and identical across parses
    of the same EGIF (raw parse ids are also accepted if a caller kept one). The
    move is soundness-checked by the engine; an unsound move returns
    ``{"ok": False, "error": <the engine's own rejection message>}``. On success
    the result carries the new graph's canonical EGIF (``result_egif``) and its
    structural summary + element index.
    """
    from proof_authoring import apply_rule as _apply_rule

    try:
        egi = parse_egif(egif)
    except Exception as exc:
        return {"ok": False, "error": f"did not parse — {type(exc).__name__}: {exc}"}

    try:
        real_selection = (
            [_resolve_label(egi, s) for s in selection] if selection is not None else None
        )
        real_target = _resolve_label(egi, target) if target is not None else None
    except KeyError as exc:
        return {"ok": False, "error": f"unknown element label {exc}; call check_egif to list valid labels"}

    try:
        new_egi = _apply_rule(
            rule,
            egi,
            selection=real_selection,
            egif=egif_content,
            target=real_target,
        )
    except AssertionError as exc:
        # The engine's loud rejection of an unsound / ill-specified move.
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return {"ok": True, **_egif_summary(new_egi, with_elements=True), "result_egif": EGIFGenerator(new_egi).generate()}


def validate_step(
    egif: str,
    rule: str,
    *,
    selection: Optional[List[str]] = None,
    egif_content: Optional[str] = None,
    target: Optional[str] = None,
) -> Dict[str, Any]:
    """Check whether a Dau-rule move *would* be sound, without keeping the result.

    Same parameters as :func:`apply_rule`. Returns ``{"ok": True}`` if the move
    is a sound, well-specified rule application, or ``{"ok": False, "error":
    ...}`` with the rejection reason otherwise. Use this to let an agent probe a
    move before committing to it.
    """
    result = apply_rule(
        egif,
        rule,
        selection=selection,
        egif_content=egif_content,
        target=target,
    )
    # Drop the result graph; report validity only.
    return {"ok": result["ok"], **({} if result["ok"] else {"error": result["error"]})}


# ---------------------------------------------------------------------------
# attest — §3.3 correspondence between an EGI and its drawing
# ---------------------------------------------------------------------------

def attest(egif: str, *, style: Optional[str] = None) -> Dict[str, Any]:
    """Lay out ``egif`` and attest §3.3 correspondence between graph and drawing.

    Parses the EGIF, generates a real ELK-based drawing, and runs the runtime
    §3.3 check (``attest_correspondence``) — the guarantee that the picture and
    the proposition denote the same mathematical object (totality/injectivity,
    containment, incidence + argument order, identity, crossing-multiset).

    ``style`` selects the visual style (``None`` = the default dau-compliant
    style); style varies the manifest, never the meaning, so every valid style
    attests. Returns ``{"ok": True, "attested": True, ...}`` on success, or
    ``{"ok": False, "attested": False, "failures": [...]}`` when the drawn form
    departs from the graph.
    """
    from elk_layout_engine import ELKLayoutEngine
    from style_loader import load_default_style, load_style
    from correspondence_attestation import attest_correspondence, CorrespondenceViolation

    try:
        egi = parse_egif(egif)
    except Exception as exc:
        return {"ok": False, "attested": False, "error": f"did not parse — {type(exc).__name__}: {exc}"}

    try:
        spec = load_style(style) if style else load_default_style()
        dto = ELKLayoutEngine().generate_layout(egi, spec)
    except Exception as exc:
        return {"ok": False, "attested": False, "error": f"layout failed — {type(exc).__name__}: {exc}"}

    try:
        attest_correspondence(egi, dto, context=f"mcp_verifier.attest (style={style or 'default'})")
    except CorrespondenceViolation as exc:
        return {
            "ok": False,
            "attested": False,
            "failures": [str(f) for f in getattr(exc, "failures", []) or [str(exc)]],
            "error": str(exc),
        }

    return {
        "ok": True,
        "attested": True,
        "style": style or "default",
        **_egif_summary(egi),
    }


# ---------------------------------------------------------------------------
# Tool registry — the single source of truth the MCP server wraps.
# ---------------------------------------------------------------------------

#: name → (callable, one-line description). The ``mcp_server`` module registers
#: each of these as an MCP tool; tests iterate over it to confirm coverage.
TOOLS = {
    "check_egif": (check_egif, "Parse an EGIF string and confirm it is a well-formed existential graph."),
    "peel": (peel, "Evaluate a proposition G against a model M (three-valued: TRUE/FALSE/UNKNOWN, with witness/counterexample)."),
    "apply_rule": (apply_rule, "Apply one sound Dau transformation rule and return the resulting graph."),
    "validate_step": (validate_step, "Check whether a Dau-rule move would be sound, without keeping the result."),
    "attest": (attest, "Lay out a graph and attest §3.3 correspondence between the graph and its drawing."),
}
