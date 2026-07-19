"""
modal_query — read ◇ (possibility) and □ (necessity) off the diachronic
branching DAG, with no modal mark.

This is the *trajectory reading* of [MODALITY_WITHOUT_GAMMA.md](../docs/MODALITY_WITHOUT_GAMMA.md)
§1 made operational. A modal operator is shorthand for a quantifier over a Kripke
frame ⟨W, R⟩, and Arisbe already maintains that frame: the **worlds** are the EGI
states (sheets) of a transformation history, and the **accessibility relation** R
is the legal-transition DAG (``from_state_id → to_state_id``). Under the standard
translation,

    ◇φ  =  ∃ a reachable sheet that scribes φ      ("some legal trajectory scribes φ")
    □φ  =  ∀ reachable sheets, each scribes φ       ("every legal trajectory scribes φ")

— *possibility is the branching of legal trajectories, necessity is their
convergence, and the only necessity is to follow the rules.* This module computes
exactly that, by walking the DAG a chain already carries. It draws **no new mark**:
the frame is the branching history (built by ``proof_authoring.ProofChain`` /
``egi_transformation_history``), and ◇/□ are read off it.

Scope (faithful to the doctrine's honest ledger): this is the *propositional*
trajectory reading — predicates over what a sheet scribes. It does **not** carry a
line of identity across a transition (the first-order-with-identity case
``MODALITY_WITHOUT_GAMMA`` §3 flags as beyond van Benthem), and it is the
derivability/GL-shaped reading, not the alethic one (◇/□ across the corpus's
models M — that is the inverse pivot, ``/agon/where-it-holds``). Geometry-free:
it reads only DAG structure + EGI content, so it is regime-agnostic and adds no
correspondence obligation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from egi_core_dau import RelationalGraphWithCuts
from tomos_service import TransformationChain

# A predicate names what it means for a sheet to "scribe φ": egi → does φ hold here.
Predicate = Callable[[RelationalGraphWithCuts], bool]


# --------------------------------------------------------------------------- #
# The frame — reachability over the legal-transition DAG                       #
# --------------------------------------------------------------------------- #

def _adjacency(chain: TransformationChain) -> Dict[str, List[str]]:
    """state id → list of immediately-accessible state ids (the DAG edges)."""
    adj: Dict[str, List[str]] = {sid: [] for sid in chain.states}
    for step in chain.steps:
        adj.setdefault(step.from_state_id, []).append(step.to_state_id)
    return adj


def reachable_states(
    chain: TransformationChain,
    base: Optional[str] = None,
    *,
    reflexive: bool = True,
) -> Set[str]:
    """Every world accessible from ``base`` (default: the chain's initial state),
    following legal transitions. ``reflexive`` includes ``base`` itself (the
    natural choice — a sheet is trivially reachable from itself, and ◇/□ at a
    world quantify over it)."""
    base = base or chain.initial_state_id
    adj = _adjacency(chain)
    seen: Set[str] = set()
    stack = [base]
    while stack:
        s = stack.pop()
        for nxt in adj.get(s, []):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    if reflexive:
        seen.add(base)
    else:
        seen.discard(base)
    return seen


def leaf_states(chain: TransformationChain, base: Optional[str] = None) -> Set[str]:
    """The reachable *trajectory endpoints* — states with no outgoing transition
    (where a legal line of development comes to rest)."""
    adj = _adjacency(chain)
    return {s for s in reachable_states(chain, base) if not adj.get(s)}


# --------------------------------------------------------------------------- #
# ◇ / □                                                                        #
# --------------------------------------------------------------------------- #

@dataclass
class ModalResult:
    """The verdict of a ◇/□ query, with the worlds that decided it."""

    modality: str               # "possible" (◇) or "necessary" (□)
    holds: bool
    witnesses: List[str] = field(default_factory=list)        # worlds where φ holds
    counterexamples: List[str] = field(default_factory=list)  # worlds where φ fails
    considered: List[str] = field(default_factory=list)       # the worlds quantified over

    @property
    def summary(self) -> str:
        glyph = "◇" if self.modality == "possible" else "□"
        verb = "holds" if self.holds else "fails"
        n = len(self.considered)
        if self.modality == "possible":
            tail = (f"scribed on {len(self.witnesses)} of {n} reachable sheet(s)"
                    if self.holds else f"scribed on none of {n} reachable sheet(s)")
        else:
            tail = (f"scribed on every one of {n} reachable sheet(s)"
                    if self.holds else
                    f"absent on {len(self.counterexamples)} of {n} reachable sheet(s)")
        return f"{glyph}φ {verb} — {tail}."


def _worlds(chain: TransformationChain, base: Optional[str], over: str) -> List[str]:
    if over == "leaves":
        worlds = leaf_states(chain, base)
    elif over == "states":
        worlds = reachable_states(chain, base)
    else:
        raise ValueError(f"over must be 'states' or 'leaves', not {over!r}")
    # Deterministic ordering for stable summaries/tests.
    return sorted(worlds)


def possibly(
    chain: TransformationChain,
    predicate: Predicate,
    *,
    base: Optional[str] = None,
    over: str = "states",
) -> ModalResult:
    """◇φ — does *some* reachable sheet scribe φ? ``over='states'`` quantifies
    over all reachable worlds (standard Kripke ◇); ``over='leaves'`` over the
    trajectory endpoints only."""
    worlds = _worlds(chain, base, over)
    witnesses = [w for w in worlds if predicate(chain.states[w])]
    return ModalResult(
        modality="possible", holds=bool(witnesses),
        witnesses=witnesses,
        counterexamples=[w for w in worlds if w not in witnesses],
        considered=worlds,
    )


def necessarily(
    chain: TransformationChain,
    predicate: Predicate,
    *,
    base: Optional[str] = None,
    over: str = "states",
) -> ModalResult:
    """□φ — does *every* reachable sheet scribe φ? The counterexamples name the
    worlds that refute necessity (necessity is convergence: □φ holds exactly when
    no legal trajectory escapes φ)."""
    worlds = _worlds(chain, base, over)
    counter = [w for w in worlds if not predicate(chain.states[w])]
    return ModalResult(
        modality="necessary", holds=not counter,
        witnesses=[w for w in worlds if w not in counter],
        counterexamples=counter,
        considered=worlds,
    )


# --------------------------------------------------------------------------- #
# Settlement — the forcing three-case table as a named reading                  #
# --------------------------------------------------------------------------- #

@dataclass
class SettlementResult:
    """The three-way classification of φ at a state, over its reachable worlds.

    This is Cohen's forcing table read as trajectory semantics
    (docs/FORCING_AND_THE_GAMMA_CROSSING.md §2): *∅ forces S / some π forces S /
    no π forces S* becomes

        settled   —  □φ            (every reachable sheet scribes φ)
        open      —  ◇φ ∧ ¬□φ      (some trajectory scribes φ, some escapes it)
        excluded  —  ¬◇φ           (no reachable sheet scribes φ)

    It is also the per-statement settled-vs-open join that
    ``discourse_membrane.contested_contents`` gestures at: an *open* φ is the
    ◇-contested point the modal lens reads as not settled.
    """

    status: str                 # "settled" | "open" | "excluded"
    possible: ModalResult       # the underlying ◇ query
    necessary: ModalResult      # the underlying □ query

    @property
    def summary(self) -> str:
        n = len(self.possible.considered)
        if self.status == "settled":
            return f"settled — □φ: scribed on every one of {n} reachable sheet(s)."
        if self.status == "excluded":
            return f"excluded — ¬◇φ: scribed on none of {n} reachable sheet(s)."
        return (f"open — ◇φ ∧ ¬□φ: scribed on {len(self.possible.witnesses)} of "
                f"{n} reachable sheet(s), absent on "
                f"{len(self.necessary.counterexamples)}.")


def settlement(
    chain: TransformationChain,
    predicate: Predicate,
    *,
    base: Optional[str] = None,
    over: str = "states",
) -> SettlementResult:
    """Classify φ at ``base`` as settled / open / excluded over its reachable
    worlds (see :class:`SettlementResult`). Composes :func:`possibly` and
    :func:`necessarily` — no new frame semantics, just the three-case table
    named. Honest scope: this is the *trajectory* trichotomy, sound regardless
    of erasure/retraction along a branch; it is **not** the claim that a verdict
    at ``base`` persists under extension (which holds only on the
    enlargement-only fragment — FORCING_AND_THE_GAMMA_CROSSING §4a)."""
    pos = possibly(chain, predicate, base=base, over=over)
    nec = necessarily(chain, predicate, base=base, over=over)
    if nec.holds:
        status = "settled"
    elif pos.holds:
        status = "open"
    else:
        status = "excluded"
    return SettlementResult(status=status, possible=pos, necessary=nec)


# --------------------------------------------------------------------------- #
# Predicate helpers — what it is for a sheet to "scribe φ"                      #
# --------------------------------------------------------------------------- #

def scribes_relation(name: str) -> Predicate:
    """φ = 'a relation named ``name`` is scribed somewhere on the sheet'.

    Quoted ink does not count as scribed (B-min: a quotation area exhibits
    its contents without force — mention, not use)."""

    def _scribed(egi) -> bool:
        if not egi.quotation:
            return name in set(egi.rel.values())
        from formal_transformation_rules import _inside_quotation

        return any(
            rel_name == name and not _inside_quotation(egi, eid)
            for eid, rel_name in egi.rel.items()
        )

    return _scribed


def equals_graph(egif: str) -> Predicate:
    """φ = 'the sheet is (the whole graph) ``egif``' — same_graph equality."""
    from eg_navigation import same_graph
    from egif_parser_dau import parse_egif
    target = parse_egif(egif)
    return lambda egi: same_graph(egi, target)


def is_blank() -> Predicate:
    """φ = 'the blank sheet' — nothing scribed (the one unconditioned world)."""
    return lambda egi: not egi.E and not egi.Cut and not egi.V


# --------------------------------------------------------------------------- #
# K2 (durability) — trajectory-relative, off the branching DAG                  #
# --------------------------------------------------------------------------- #

def durability_modality(
    history_or_uod: TransformationChain,
    relation: str,
    *,
    over: str = "leaves",
) -> str:
    """K2's modal reading (THE_MEASURE_OF_KNOWLEDGE §3, the DAG sense): where does
    a relation's knowledge STAND across the branching futures?

    On a single (non-branching) line, K2 durability is read off one trajectory —
    a fact either survives to the end or it doesn't. On a *branching* diachronic
    DAG that reading is ambiguous: a relation may survive on some continuations
    and be relinquished on others. This composes the existing ◇/□ machinery
    (:func:`possibly`, :func:`necessarily`) to name the three cases:

        "necessary"  —  □: scribed on every reachable sheet/leaf (K2-box —
                        durable on every legal trajectory)
        "possible"   —  ◇ holds but □ doesn't: scribed on some but not all
                        (K2-diamond — durable somewhere, not everywhere)
        "absent"     —  ¬◇: scribed nowhere reachable

    Pure reader over ``possibly``/``necessarily``; adds no correspondence
    obligation (geometry-free, like the rest of this module).
    """
    predicate = scribes_relation(relation)
    if necessarily(history_or_uod, predicate, over=over).holds:
        return "necessary"
    if possibly(history_or_uod, predicate, over=over).holds:
        return "possible"
    return "absent"
