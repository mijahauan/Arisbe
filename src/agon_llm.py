"""The LLM **Graphist** — Stage 1 of the automated Endoporeutic Game.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md``. The automated EPG has three
roles — Graphist (the motive of *doubt*), Grapheus (the motive to *defend* M), Agonothetes
(the *judge*). This module builds the **first** role, plugged into the existing
``agon_evolution`` loop's ``Proposer`` socket; the Grapheus and Agonothetes stay *mechanical*
(``agon_evolution.Agonothetes()``) for now. Staging one role at a time keeps each increment
runnable and measurable.

The governing principle: **the LLM argues; the calculus decides.** The Graphist only
*proposes* a doubt; whether it holds in M is settled by the mechanical peel
(``semantic_game``), never by the agent. And every LLM utterance is **reduced to a calculus
artifact and re-checked**: the model emits first-order logic (its strong suit), Arisbe
converts it deterministically to an EGI (``nl_to_logic.build_proposal``) and *parses* it — an
un-parseable "doubt" never reaches the loop. This mirrors the ``nl_to_logic`` contract
(*LLM proposes, Arisbe disposes*) exactly: the ``anthropic`` SDK is the optional ``nl`` extra
(guarded by ``ANTHROPIC_AVAILABLE``), the client is **injectable** for tests, tool use is
**forced** (a schema-valid object), and the front-end **never raises**.

Attention: the Graphist does not hallucinate doubt from nothing — the *structure of M nominates
the doubts* (relations with few instances, laws with no grounded instance, under-connected
individuals; the ``m_render`` neighbourhood idea) and the *LLM voices them* in M's vocabulary.

Additive, geometry-free, imports no protected module's internals.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts
from eg_navigation import area_of, child_cuts
from nl_to_logic import (
    ANTHROPIC_AVAILABLE,
    DEFAULT_MODEL,
    build_proposal,
    _default_client,
)

# The doubt taxonomy the Graphist declares (logged; shapes the prompt, not the calculus).
DOUBT_TYPES = [
    "gap",                 # M is silent on this — expect UNKNOWN
    "over_generalization", # a standing law may have overreached — a counterexample
    "missing_distinction", # M conflates things a finer relation would separate
    "boundary_case",       # an edge of an existing relation/law
    "novel_relation",      # introduce one new predicate (vocabulary enlargement)
]

_PROPOSE_GRAPH_TOOL = {
    "name": "propose_graph",
    "description": (
        "Voice ONE doubt about the model M as a candidate proposition to be tested against "
        "it. Emit the proposition as first-order logic; do not assert it is true."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "fol": {
                "type": "string",
                "description": (
                    "The doubted proposition in first-order logic using EXACTLY these "
                    "glyphs: ∀ ∃ ¬ ∧ ∨ → ↔ ⊕, predicate(args), lowercase variables, "
                    "Capitalized constants. Parenthesize quantifier bodies, e.g. "
                    "∀x (Swan(x) → White(x))."
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
            "doubt_type": {
                "type": "string",
                "enum": DOUBT_TYPES,
                "description": "Which kind of doubt this proposition raises about M.",
            },
            "rationale": {
                "type": "string",
                "description": (
                    "One sentence: why you doubt M settles this. Logged for the record; "
                    "never load-bearing — the calculus, not this text, decides."
                ),
            },
        },
        "required": ["fol", "predicates", "constants", "doubt_type", "rationale"],
    },
}

_SYSTEM = (
    "You are the GRAPHIST in an Endoporeutic Game. Your single motive is DOUBT: given a "
    "domain model M, propose ONE proposition that stresses it — something you have reason to "
    "think M does not settle. Prefer a proposition M can NEITHER confirm NOR deny (an "
    "UNKNOWN), because open questions drive inquiry; a proposition M trivially already "
    "affirms is worthless. Good doubts: a GAP M is silent on; an OVER_GENERALIZATION where a "
    "standing universal law may have overreached (voice the counterexample — e.g. a swan "
    "that is not white, written Swan(c) ∧ ¬White(c)); a MISSING_DISTINCTION; a BOUNDARY_CASE. "
    "Stay inside M's vocabulary where it fits; introduce at most ONE new predicate, and only "
    "when the vocabulary is genuinely too thin (doubt_type novel_relation). Output ONLY by "
    "calling the propose_graph tool. Use the grammar ∀ ∃ ¬ ∧ ∨ → ↔ ⊕, n-ary predicate(a, b), "
    "lowercase bound variables, Capitalized individual constants; parenthesize quantifier "
    "bodies. Use the model's EXACT relation names as shown in the brief (they are lowercase); "
    "for a genuinely new predicate use a short lowercase name. Translate only the doubt; do "
    "NOT add world knowledge as if asserted."
)


# --------------------------------------------------------------------------- #
# Vocabulary normalization — reduce the LLM's FOL to M's spelling              #
# --------------------------------------------------------------------------- #

# A predicate application is a name *tight* against its paren, ``Swan(x)`` — never the
# quantifier's ``∀x (…)`` (a variable, a space, then the body paren). No ``\s*`` on purpose.
_PRED_APP = re.compile(r"([A-Za-z_]\w*)\(")


def _normalize_fol(fol: str, model_vocab: Set[str]) -> str:
    """FOL convention Capitalizes predicates (``White``), but the corpus writes relations
    lowercase (``white``); left alone, ``White(Ciel)`` becomes a *different* relation than M's
    ``white`` and the Graphist talks past M. Rewrite every predicate application to M's exact
    spelling where a case-insensitive match exists, else to lowercase (the codebase
    convention). Constants (bare Capitalized tokens, not followed by ``(``) are untouched."""
    lower_map = {r.lower(): r for r in model_vocab}

    def repl(m: "re.Match") -> str:
        name = m.group(1)
        return f"{lower_map.get(name.lower(), name.lower())}("

    return _PRED_APP.sub(repl, fol)


# --------------------------------------------------------------------------- #
# Attention — the structure of M nominates the doubts                          #
# --------------------------------------------------------------------------- #

@dataclass
class AttentionBrief:
    """What the Graphist is shown about M before it voices a doubt — vocabulary plus the
    *thin spots* the structure exposes. ``text`` is the rendered user message."""
    vocabulary: List[str]
    constants: List[str]
    thin_relations: List[str]            # relations with ≤1 grounded instance
    ungrounded_laws: List[Tuple[str, str]]  # (body, head) laws with no grounded body instance
    lonely_individuals: List[str]        # constants in exactly one atom
    text: str

    def render(self) -> str:
        return self.text


def _sheet_ground_atoms(
    model: RelationalGraphWithCuts,
) -> List[Tuple[str, List[Optional[str]]]]:
    return [
        (model.rel[e.id], [model.get_vertex(v).label for v in model.nu.get(e.id, ())])
        for e in model.E
        if e.id in model.rel and area_of(model, e.id) == model.sheet
    ]


def _model_laws(model: RelationalGraphWithCuts) -> List[Tuple[str, str]]:
    """(body, head) relation pairs of each sheet-level scroll ``~[ (B *x) ~[ (H x) ] ]``."""
    laws: List[Tuple[str, str]] = []
    for outer in child_cuts(model, model.sheet):
        inner = child_cuts(model, outer)
        if not inner:
            continue
        body = next((model.rel[e.id] for e in model.E
                     if area_of(model, e.id) == outer and e.id in model.rel), None)
        head = next((model.rel[e.id] for e in model.E
                     if area_of(model, e.id) == inner[0] and e.id in model.rel), None)
        if body and head:
            laws.append((body, head))
    return laws


def attention_brief(model: RelationalGraphWithCuts) -> AttentionBrief:
    """Compute the Graphist's attention brief for M. On the blank sheet it invites
    bootstrapping; otherwise it names where M is structurally thin."""
    from dl_reasoning import ontology_signature

    vocabulary = sorted(ontology_signature(model))
    atoms = _sheet_ground_atoms(model)
    constants = sorted({lbl for _, labels in atoms for lbl in labels if lbl})

    if not vocabulary and not atoms:
        text = (
            "The model M is EMPTY (the blank sheet of assertion). Begin the inquiry: posit a "
            "foundational fact, or a small starting vocabulary, for a coherent everyday domain "
            "of your choosing (a household, a zoo, a harbour town, …) — something concrete the "
            "game can then contest. Name at least one individual."
        )
        return AttentionBrief([], [], [], [], [], text)

    rel_counts = Counter(r for r, _ in atoms)
    thin = sorted([r for r in vocabulary if rel_counts.get(r, 0) <= 1])
    grounded = {r for r, _ in atoms}
    ungrounded_laws = [(b, h) for (b, h) in _model_laws(model) if b not in grounded]
    const_counts = Counter(lbl for _, labels in atoms for lbl in labels if lbl)
    lonely = sorted([c for c, n in const_counts.items() if n == 1])

    lines = [
        f"Model M speaks these relations: {', '.join(vocabulary) or '(none)'}.",
        f"Known individuals: {', '.join(constants) or '(none)'}.",
        "Thin spots worth doubting:",
        f"  • relations with ≤1 known instance: {', '.join(thin) or '(none)'}",
        "  • laws with no grounded instance: "
        + (", ".join(f'{b}→{h}' for b, h in ungrounded_laws) or "(none)"),
        f"  • individuals mentioned only once: {', '.join(lonely) or '(none)'}",
        "Voice ONE doubt (per your instructions). Prefer a proposition M can neither confirm "
        "nor deny; if you challenge a standing universal law, voice the concrete counterexample.",
    ]
    return AttentionBrief(vocabulary, constants, thin, ungrounded_laws, lonely, "\n".join(lines))


# --------------------------------------------------------------------------- #
# The LLM Graphist — a Proposer                                                #
# --------------------------------------------------------------------------- #

@dataclass
class GraphistEpisode:
    """One recorded proposal attempt (kept on the agent for the demo / inspection)."""
    round_idx: int
    brief: str
    fol: str
    doubt_type: Optional[str]
    rationale: str
    egif: Optional[str]
    ok: bool
    error: Optional[str] = None


class LLMGraphist:
    """The Graphist as an ``agon_evolution.Proposer``: each round it reads M's thin spots,
    asks the LLM to voice one doubt as FOL, and reduces that to a parsed EGIF — retrying with
    the parse error fed back, and returning ``None`` (ending the run cleanly) only if it
    cannot produce a usable graph or reach the model. Never raises."""

    def __init__(
        self,
        *,
        client=None,
        model: str = DEFAULT_MODEL,
        max_retries: int = 2,
        avoid_repeats: bool = True,
    ):
        self._client = client
        self._model = model
        self._max_retries = max_retries
        self._avoid_repeats = avoid_repeats
        self.episodes: List[GraphistEpisode] = []
        self._seen: set[str] = set()

    # -- the Proposer protocol -------------------------------------------------
    def propose(
        self, model: RelationalGraphWithCuts, round_idx: int
    ) -> Optional[str]:
        brief = attention_brief(model)
        feedback: Optional[str] = None
        data: Dict = {}
        for _ in range(self._max_retries + 1):
            try:
                data = self._invoke(brief.render(), feedback)
            except Exception as exc:   # unreachable model / SDK / key → end run cleanly
                self.episodes.append(GraphistEpisode(
                    round_idx, brief.text, "", None, "", None, False,
                    f"LLM call failed: {exc}"))
                return None
            fol = _normalize_fol(data.get("fol", ""), set(brief.vocabulary))
            # predicates/constants left empty: build_proposal derives the *real* (normalized)
            # vocabulary from the parsed AST, so the LLM's Capitalized self-report can't drift.
            prop = build_proposal("(graphist doubt)", fol=fol, predicates={}, constants=[])
            if prop.usable:
                egif = prop.egif
                if self._avoid_repeats and egif in self._seen:
                    feedback = "that proposition was already proposed — voice a *different* doubt."
                    continue
                self._seen.add(egif)
                self.episodes.append(GraphistEpisode(
                    round_idx, brief.text, prop.fol, data.get("doubt_type"),
                    data.get("rationale", ""), egif, True))
                return egif
            feedback = prop.parse_error or "the FOL did not build a graph — try a simpler form."
        # retries exhausted
        self.episodes.append(GraphistEpisode(
            round_idx, brief.text, data.get("fol", ""), data.get("doubt_type"),
            data.get("rationale", ""), None, False, feedback))
        return None

    # -- the one non-deterministic step ---------------------------------------
    def _invoke(self, brief_text: str, feedback: Optional[str]) -> Dict:
        client = self._client or _default_client()
        user = brief_text
        if feedback:
            user += f"\n\nYour previous attempt was rejected: {feedback}"
        resp = client.messages.create(
            model=self._model,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            system=_SYSTEM,
            tools=[_PROPOSE_GRAPH_TOOL],
            tool_choice={"type": "tool", "name": "propose_graph"},
            messages=[{"role": "user", "content": user}],
        )
        for block in resp.content:
            if (getattr(block, "type", None) == "tool_use"
                    and getattr(block, "name", "") == "propose_graph"):
                return dict(block.input)
        raise RuntimeError("the model did not return a propose_graph tool call")


__all__ = [
    "ANTHROPIC_AVAILABLE", "DOUBT_TYPES",
    "AttentionBrief", "attention_brief",
    "GraphistEpisode", "LLMGraphist",
]
