"""
The NL→logic front-end — *LLM proposes, Arisbe disposes*.

Arisbe's role in turning natural language into logic is to be the **interpretant /
verifier behind the parser, not the parser** (docs: the NL→logic arc). An LLM is good at
the noisy first step — English → a *candidate* logical form — and bad at guaranteeing that
form means anything; Arisbe is the opposite. So the division of labour here is strict:

* the **LLM** reads one English proposition and emits a candidate **first-order-logic
  string** in the existing ``folio_fol`` grammar (``∀ ∃ ¬ ∧ ∨ → ↔ ⊕`` + predicates +
  constants), *plus* a declared vocabulary. It never produces an EGI and never asserts
  truth. If a sentence is understandable but cannot be said in this fragment, it says so
  (``unmappable``) rather than guessing.
* **Arisbe** parses that string **deterministically** (``parse_fol`` → ``folio_fol_to_egi``
  → ``generate_egif``); a malformed candidate is *reported* (``parse_error``), never
  repaired. It then (a) reconciles the proposal's vocabulary against a model M's signature
  — the **vocabulary-miss** ("M can't even address that") vs **fact-miss** ("M can't
  confirm that") distinction the parse use case turns on — and (b) **tests** the proposal
  against M in the interpretation register (the peel), exactly as ``/agon/interpret`` does.

The LLM dependency is optional (guarded by ``ANTHROPIC_AVAILABLE``, like ``folio_fol``'s
``Z3_AVAILABLE``): the whole deterministic half — parse, build, reconcile, interpret —
runs with the SDK absent, driven by a hand-written FOL string (the ``--no-llm`` path). The
LLM client is injectable so tests need no network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

from folio_fol import FolioParseError, parse_fol

try:  # pragma: no cover - exercised only where the SDK is absent
    import anthropic  # noqa: F401
    ANTHROPIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    ANTHROPIC_AVAILABLE = False


DEFAULT_MODEL = "claude-opus-4-8"

# The structured shape the LLM must emit (forced tool use → guaranteed-valid object).
_EMIT_FOL_TOOL = {
    "name": "emit_fol",
    "description": (
        "Record the first-order-logic translation of the English proposition, "
        "or declare it unmappable."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "fol": {
                "type": "string",
                "description": (
                    "The proposition in first-order logic using EXACTLY these glyphs: "
                    "∀ ∃ ¬ ∧ ∨ → ↔ ⊕, predicate(args), lowercase variables, and "
                    "Capitalized constants. Parenthesize quantifier bodies. Empty if "
                    "unmappable is set."
                ),
            },
            "predicates": {
                "type": "object",
                "description": "Each predicate used, mapped to its arity (integer).",
                "additionalProperties": {"type": "integer"},
            },
            "constants": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The individual constants named in the formula.",
            },
            "unmappable": {
                "type": "string",
                "description": (
                    "If the sentence is understandable but cannot be expressed in this "
                    "FOL fragment (modality, higher-order quantification, vague "
                    "gradable terms, etc.), explain why here and leave fol empty. "
                    "Otherwise omit / empty."
                ),
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "How confident the translation captures the sentence.",
            },
        },
        "required": ["fol", "predicates", "constants"],
    },
}

_SYSTEM = (
    "You translate exactly one English proposition into first-order logic. Output ONLY by "
    "calling the emit_fol tool. Use the grammar: ∀ ∃ ¬ ∧ ∨ → ↔ ⊕, n-ary predicate(a, b), "
    "lowercase bound variables, Capitalized individual constants. Parenthesize quantifier "
    "bodies, e.g. ∀x (Bird(x) → Fly(x)). Declare every predicate with its arity and list "
    "every constant. Translate only what the sentence asserts — do not add world knowledge. "
    "If the sentence is understandable but cannot be expressed in this fragment, set "
    "unmappable and leave fol empty rather than forcing a wrong translation."
)


@dataclass
class Proposal:
    """One candidate logical form for an English proposition — the LLM's proposal,
    parsed and rendered by Arisbe (or marked unparseable / unmappable)."""

    nl: str
    fol: str = ""
    predicates: Dict[str, int] = field(default_factory=dict)
    constants: List[str] = field(default_factory=list)
    egif: Optional[str] = None            # the drawable proposal, deterministically derived
    parsed: bool = False                  # did fol parse + build an EGI?
    parse_error: Optional[str] = None     # the reported reason it did not (never guessed)
    unmappable: Optional[str] = None      # the LLM's honest "can't say this here" caveat
    confidence: Optional[str] = None
    vocab_mismatch: List[str] = field(default_factory=list)  # declared≠used (self-report check)

    @property
    def usable(self) -> bool:
        """Ready to test: it parsed into an EGI."""
        return self.parsed and self.egif is not None


@dataclass
class VocabReport:
    """How a proposal's vocabulary lands against a model M — the vocabulary-miss vs
    fact-miss split. ``out_of_signature`` predicates are ones M cannot even address (not
    even wrong); ``addressable`` ones M *could* speak to (whether it confirms them is the
    separate fact question the peel answers)."""

    model_signature: Set[str]
    addressable: List[str] = field(default_factory=list)
    out_of_signature: List[str] = field(default_factory=list)

    @property
    def fully_addressable(self) -> bool:
        return not self.out_of_signature


# ---------------------------------------------------------------------------
# The LLM front-end (the only non-deterministic step)
# ---------------------------------------------------------------------------

def _emit_fol(client, nl: str, vocabulary_hint: Optional[Iterable[str]], model: str) -> dict:
    """Call the LLM and return its structured ``emit_fol`` payload (a dict).  Forced tool
    use guarantees a schema-valid object; we read the tool_use block's ``input``."""
    user = f"Proposition: {nl.strip()}"
    if vocabulary_hint:
        vocab = ", ".join(sorted(set(vocabulary_hint)))
        user += (
            f"\n\nThe model you will be tested against speaks this vocabulary: {vocab}. "
            "Prefer these predicate names where they fit the sentence's meaning; introduce "
            "a new predicate only when none of them captures it."
        )
    resp = client.messages.create(
        model=model,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=_SYSTEM,
        tools=[_EMIT_FOL_TOOL],
        tool_choice={"type": "tool", "name": "emit_fol"},
        messages=[{"role": "user", "content": user}],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == "emit_fol":
            return dict(block.input)
    raise RuntimeError("the model did not return an emit_fol tool call")


def _default_client():  # pragma: no cover - needs the SDK + a key
    if not ANTHROPIC_AVAILABLE:
        raise ImportError(
            "the 'anthropic' SDK is required for propose(); install the 'nl' extra "
            "(uv sync --extra nl) or use the deterministic build_proposal(fol=...) path"
        )
    import anthropic
    return anthropic.Anthropic()


def build_proposal(
    nl: str,
    *,
    fol: str,
    predicates: Optional[Dict[str, int]] = None,
    constants: Optional[List[str]] = None,
    unmappable: Optional[str] = None,
    confidence: Optional[str] = None,
) -> Proposal:
    """The deterministic half: turn a candidate FOL string (from the LLM, or hand-written
    for the ``--no-llm`` path) into a parsed :class:`Proposal`.  Never raises on a bad
    formula — it records ``parse_error`` and leaves ``parsed=False``."""
    prop = Proposal(
        nl=nl,
        fol=(fol or "").strip(),
        predicates=dict(predicates or {}),
        constants=list(constants or []),
        unmappable=(unmappable or None),
        confidence=confidence,
    )
    if prop.unmappable and not prop.fol:
        return prop                                   # honestly unmapped — nothing to build
    if not prop.fol:
        prop.parse_error = "no FOL was produced"
        return prop
    try:
        ast = parse_fol(prop.fol)
        from folio_fol import folio_fol_to_egi
        from egif_generator_dau import generate_egif
        egi = folio_fol_to_egi(prop.fol)
        prop.egif = generate_egif(egi)
        prop.parsed = True
        # The AST is the ground truth for the vocabulary.  When the caller declared
        # predicates (the LLM path), cross-check them against what the formula actually uses
        # and flag any mismatch (don't trust the self-report blindly).  When none were
        # declared (the --no-llm path), derive them from the AST so reconcile has the real
        # vocabulary to test against M.
        from folio_model_finder import _signature
        used_consts, used_preds = _signature([ast])
        if prop.predicates:
            prop.vocab_mismatch = sorted(set(prop.predicates) ^ set(used_preds))
        else:
            prop.predicates = dict(used_preds)
        if not prop.constants:
            prop.constants = list(used_consts)
    except FolioParseError as exc:
        prop.parse_error = str(exc)
    except Exception as exc:                          # build/generate failure — report, don't crash
        prop.parse_error = f"could not build an EGI: {exc}"
    return prop


def propose(
    nl: str,
    *,
    vocabulary_hint: Optional[Iterable[str]] = None,
    model: str = DEFAULT_MODEL,
    client=None,
) -> Proposal:
    """Translate one English proposition into a candidate :class:`Proposal` via the LLM,
    then parse it deterministically.  ``client`` is injectable (tests pass a fake; absent ⇒
    a default ``anthropic.Anthropic()``).  Any API error is captured into the Proposal's
    ``parse_error`` — ``propose`` never raises on a bad model response."""
    try:
        data = _emit_fol(client or _default_client(), nl, vocabulary_hint, model)
    except Exception as exc:
        return Proposal(nl=nl, parse_error=f"LLM front-end failed: {exc}")
    return build_proposal(
        nl,
        fol=data.get("fol", ""),
        predicates=data.get("predicates") or {},
        constants=data.get("constants") or [],
        unmappable=data.get("unmappable") or None,
        confidence=data.get("confidence"),
    )


# ---------------------------------------------------------------------------
# Disposing: reconcile vocabulary + test against M (deterministic, reused engines)
# ---------------------------------------------------------------------------

def reconcile(proposal: Proposal, model_egif: str) -> VocabReport:
    """Split the proposal's predicates into those M can address vs those out of M's
    signature — the vocabulary-miss notion made first-class for the parse use case."""
    from egif_parser_dau import parse_egif
    from dl_reasoning import ontology_signature
    sig = ontology_signature(parse_egif(model_egif))
    addressable, missing = [], []
    for name in sorted(proposal.predicates):
        (addressable if name in sig else missing).append(name)
    return VocabReport(model_signature=sig, addressable=addressable, out_of_signature=missing)


def interpret_against(
    proposal: Proposal, model_egif: str, *, closed: bool = False, materialize: bool = False
) -> dict:
    """Test the proposal against M in the interpretation register — the same peel
    ``/agon/interpret`` runs (mirrors ``_interpret_payload``).  Returns the verdict +
    transcript + witness/counterexample.  Requires ``proposal.usable``."""
    if not proposal.usable:
        raise ValueError("proposal did not parse into an EGI; nothing to interpret")
    from egif_parser_dau import parse_egif
    from domain_oracle import CorpusOracle
    from semantic_game import evaluate as evaluate_semantic

    materialization = None
    if materialize:
        from model_materialization import materialize_egi
        facts_egi, _rep = materialize_egi(parse_egif(model_egif))
        oracle = CorpusOracle([("M", facts_egi)], closed=closed)
        from egif_generator_dau import generate_egif
        materialization = generate_egif(facts_egi)
    else:
        oracle = CorpusOracle.from_egif({"M": model_egif}, closed=closed)

    result = evaluate_semantic(parse_egif(proposal.egif), oracle)
    return {
        "proposal_egif": proposal.egif,
        "model_egif": model_egif,
        "closed": closed,
        "verdict": result.verdict.value,
        "holds": result.holds,
        "summary": result.summary,
        "transcript": result.transcript,
        "winning_witness": result.winning_witness,
        "counterexample": result.counterexample,
        "materialized_egif": materialization,
    }


__all__ = [
    "ANTHROPIC_AVAILABLE",
    "DEFAULT_MODEL",
    "Proposal",
    "VocabReport",
    "build_proposal",
    "propose",
    "reconcile",
    "interpret_against",
]
