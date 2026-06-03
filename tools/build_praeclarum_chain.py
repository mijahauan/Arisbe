"""
Build Leibniz's *Praeclarum Theorema* as a real transformation chain —
the tomos's first canonical diachronic exemplar.

    ((P ⊃ R) ∧ (Q ⊃ S))  ⊃  ((P ∧ Q) ⊃ (R ∧ S))

Sowa's showcase EG proof (``docs/references/Peirce_Rules_of_Inference.pdf``)
derives the theorem in **seven steps from a blank sheet** — versus the
Principia's 43 steps from five axiom schemata. It is pure Alpha
(propositional), so each of Peirce's three rule-pairs is one of Dau's six
rules. Peirce's labels ↔ ours:

    3i  double-cut insertion        → DC+
    1i  insertion in a negative area → INS
    2i  iteration                   → IT+
    2e  deiteration                 → IT-
    3e  double-cut erasure          → DC-

The seven steps (Sowa's diagram, read left-to-right then the second row
right-to-left):

    1. DC+  blank → ~[ ~[ ] ]                  (an empty double cut)
    2. INS  insert the antecedent (P⊃R)(Q⊃S) into the outer (negative) area
    3. IT+  iterate (P⊃R) into the inner cut
    4. INS  insert Q into the cut now holding the iterated (P⊃R)
    5. IT+  iterate (Q⊃S) into the cut around R
    6. IT-  deiterate the inner Q (a copy of the enclosing Q)
    7. DC-  erase the double cut around S

Unlike ``tests/test_chain_persistence.py`` (which builds a *synthetic*
chain to exercise the persistence shape), every step here is a **real**
rule application through the headless ``RuleInteraction`` protocol — so the
chain is a genuine Peircean reasoning episode: a sequence of sound,
attestable sign-transitions (``docs/CHAIN_OF_SEMIOSIS.md``).

This module is import-safe (no side effects). ``build_praeclarum_chain()``
returns ``(TransformationChain, UniverseOfDiscourse)``; running it as a
script saves the exemplar into the real tomos corpus.

A note on EGIF: propositional atoms are nullary relations and must be
**capitalised** (``(P)``) — lowercase is reserved for vertex/variable
labels. (First dogfood friction: the linear syntax forces a naming
convention the diagram doesn't.)
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from egif_parser_dau import parse_egif
from rule_interaction import (
    begin_interaction,
    advance_interaction,
    apply_interaction,
)
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)

# Imported lazily-by-name so the module stays importable even from contexts
# that only need the builder (the chain types live in tomos_service).
from tomos_service import ChainStep, TransformationChain


THEOREM_EGIF = (
    "~[ ~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ] "
    "~[ ~[ (P) (Q) ~[ (R) (S) ] ] ] ]"
)
"""The Praeclarum Theorema as an Alpha EG: the outer cut negates the
antecedent conjoined with the negated consequent — i.e. antecedent ⊃
consequent."""

UOD_ID = "theorem_praeclarum"


# --------------------------------------------------------------------------- #
# Structural navigation + equality (order-insensitive)                        #
# --------------------------------------------------------------------------- #

def _cuts_in(egi, area) -> List[str]:
    cut_ids = {c.id for c in egi.Cut}
    return [e for e in egi.area.get(area, ()) if e in cut_ids]


def _edges_in(egi, area, rel=None) -> List[str]:
    edge_ids = {e.id for e in egi.E}
    return [
        e for e in egi.area.get(area, ())
        if e in edge_ids and (rel is None or egi.rel.get(e) == rel)
    ]


def _cut_with_edge(egi, parent_area, rel):
    """The cut directly inside ``parent_area`` that directly contains an edge
    named ``rel`` — how we pick (P⊃R) vs (Q⊃S) vs the inner cut by content
    rather than by ephemeral id."""
    for c in _cuts_in(egi, parent_area):
        if _edges_in(egi, c, rel):
            return c
    return None


def area_signature(egi, area=None):
    """An order-insensitive structural signature of an area subtree.

    Two Alpha graphs are the same graph iff their sheet signatures are
    equal — sibling order is a projection artifact, not logical content
    (spec §5.3). Used to compare the engine's output against the target
    theorem and to verify each replayed step without depending on element
    ids or sibling order."""
    if area is None:
        area = egi.sheet
    rels = sorted(egi.rel.get(e) for e in _edges_in(egi, area))
    subcuts = sorted(area_signature(egi, c) for c in _cuts_in(egi, area))
    return ("rels", tuple(rels), "cuts", tuple(subcuts))


# --------------------------------------------------------------------------- #
# Rule application through the interaction protocol                           #
# --------------------------------------------------------------------------- #

def apply_rule(rule_name, egi, *, selection=None, egif=None, target=None):
    """Apply one Dau rule via the headless ``RuleInteraction`` protocol and
    return the resulting EGI. Raises with the engine's own message on any
    rejected step — so an unsound move fails loudly rather than silently
    producing a wrong graph."""
    state = begin_interaction(rule_name, egi)
    if rule_name == "INS":
        r1 = advance_interaction(state, egif)
        assert r1.valid, f"INS content rejected: {r1.message}"
        r2 = advance_interaction(state, target)
        assert r2.valid, f"INS target rejected: {r2.message}"
    elif rule_name == "IT+":
        r1 = advance_interaction(state, selection)
        assert r1.valid, f"IT+ source rejected: {r1.message}"
        r2 = advance_interaction(state, target)
        assert r2.valid, f"IT+ destination rejected: {r2.message}"
    else:  # DC+, DC-, IT- (and ERA) — single selection step
        r = advance_interaction(state, selection or [])
        assert r.valid, f"{rule_name} rejected: {r.message}"
    result = apply_interaction(state)
    assert result.success, f"{rule_name} apply failed: {result.message}"
    return result.result_egi


def apply_step(egi, params: Dict):
    """Re-apply one chain step to ``egi`` from its persisted ``parameters``.

    The selection / target ids in ``parameters`` index into the step's
    ``from_state`` snapshot, so replay is faithful when ``egi`` is that
    snapshot. Returns the resulting EGI."""
    return apply_rule(
        params["rule"],
        egi,
        selection=params.get("selection"),
        egif=params.get("egif_content"),
        target=params.get("target_area"),
    )


# --------------------------------------------------------------------------- #
# The proof                                                                    #
# --------------------------------------------------------------------------- #

# Peirce's label, our rule, and a human description for each of the 7 steps.
# The element-selection for each step is computed structurally at build time
# (ids are ephemeral), then recorded into the step's parameters so the
# persisted chain replays against its own snapshots.
_ANTECEDENT = "~[ (P) ~[ (R) ] ] ~[ (Q) ~[ (S) ] ]"

_TS_BASE = "2026-06-03T00:00:0"  # deterministic, one second per step


def build_praeclarum_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct the proof as a real ``TransformationChain`` + its UoD.

    Each step is applied through the engine; the resulting states and the
    parameters that produced them are recorded. Deterministic: no clocks or
    randomness, so the chain is byte-stable across runs (good for tests)."""
    states: Dict[str, "object"] = {}
    steps: List[ChainStep] = []

    def record(i, rule, egi_from, egi_to, params, peirce, desc):
        from_id, to_id = f"s{i}", f"s{i + 1}"
        states[from_id] = egi_from
        states[to_id] = egi_to
        steps.append(ChainStep(
            step_id=f"step-{i + 1}",
            rule_name=rule,
            from_state_id=from_id,
            to_state_id=to_id,
            parameters={"rule": rule, "peirce_label": peirce, "description": desc, **params},
            timestamp=f"{_TS_BASE}{i}+00:00",
            user_annotation=f"{peirce}: {desc}",
        ))

    # s0: blank sheet (⊤) — the context the whole proof is asserted against.
    g0 = parse_egif("")

    # 1. DC+  blank → ~[ ~[ ] ]
    g1 = apply_rule("DC+", g0)
    record(0, "DC+", g0, g1, {"selection": []},
           "3i", "Insert an empty double cut on the blank sheet.")

    # 2. INS  insert the antecedent into the outer (negative) area
    O = _cuts_in(g1, g1.sheet)[0]
    g2 = apply_rule("INS", g1, egif=_ANTECEDENT, target=O)
    record(1, "INS", g1, g2, {"egif_content": _ANTECEDENT, "target_area": O},
           "1i", "Insert the antecedent (P⊃R)(Q⊃S) into the outer cut.")

    def _locate(g):
        O = _cuts_in(g, g.sheet)[0]
        A = _cut_with_edge(g, O, "P")
        B = _cut_with_edge(g, O, "Q")
        I = next(c for c in _cuts_in(g, O) if c not in (A, B))
        return O, A, B, I

    # 3. IT+  iterate (P⊃R) into the inner cut
    O, A, B, I = _locate(g2)
    g3 = apply_rule("IT+", g2, selection=[A], target=I)
    record(2, "IT+", g2, g3, {"selection": [A], "target_area": I},
           "2i", "Iterate (P⊃R) into the inner cut.")

    # 4. INS  insert Q into the cut now holding the iterated (P⊃R)
    O, A, B, I = _locate(g3)
    A_prime = _cuts_in(g3, I)[0]
    g4 = apply_rule("INS", g3, egif="(Q)", target=A_prime)
    record(3, "INS", g3, g4, {"egif_content": "(Q)", "target_area": A_prime},
           "1i", "Insert Q into the cut holding the iterated (P⊃R).")

    # 5. IT+  iterate (Q⊃S) into the cut around R
    O, A, B, I = _locate(g4)
    A_prime = _cuts_in(g4, I)[0]
    R_cut = _cut_with_edge(g4, A_prime, "R")
    g5 = apply_rule("IT+", g4, selection=[B], target=R_cut)
    record(4, "IT+", g4, g5, {"selection": [B], "target_area": R_cut},
           "2i", "Iterate (Q⊃S) into the cut around R.")

    # 6. IT-  deiterate the inner Q (a copy of the enclosing Q)
    O, A, B, I = _locate(g5)
    A_prime = _cuts_in(g5, I)[0]
    R_cut = _cut_with_edge(g5, A_prime, "R")
    B_prime = _cut_with_edge(g5, R_cut, "Q")
    inner_Q = _edges_in(g5, B_prime, "Q")[0]
    g6 = apply_rule("IT-", g5, selection=[inner_Q])
    record(5, "IT-", g5, g6, {"selection": [inner_Q]},
           "2e", "Deiterate the inner Q (a copy of the enclosing Q).")

    # 7. DC-  erase the double cut around S
    O, A, B, I = _locate(g6)
    A_prime = _cuts_in(g6, I)[0]
    R_cut = _cut_with_edge(g6, A_prime, "R")
    # B' has lost its Q, so it is now ~[ ~[ (S) ] ] — the cut with no direct edge.
    B_prime = next(c for c in _cuts_in(g6, R_cut) if not _edges_in(g6, c))
    g7 = apply_rule("DC-", g6, selection=[B_prime])
    record(6, "DC-", g6, g7, {"selection": [B_prime]},
           "3e", "Erase the double cut around S.")

    chain = TransformationChain(
        initial_state_id="s0", steps=steps, states=states,
    )

    created = datetime(2026, 6, 3, tzinfo=timezone.utc)
    meta = UoDMetadata(
        uod_id=UOD_ID,
        uod_type=UoDType.HISTORICAL,
        name="Leibniz's Praeclarum Theorema",
        description=(
            "((P⊃R) ∧ (Q⊃S)) ⊃ ((P∧Q) ⊃ (R∧S)) — Sowa's 7-step Existential "
            "Graph proof from a blank sheet (docs/references/"
            "Peirce_Rules_of_Inference.pdf). The tomos's first canonical "
            "diachronic exemplar: every step a real, attestable Dau-rule "
            "application."
        ),
        category=UoDCategory.THEOREM_PROOF,
        created=created,
        last_modified=created,
    )
    uod = UniverseOfDiscourse(metadata=meta, current_egi=g7)
    return chain, uod


def main(argv=None) -> int:
    """Build the exemplar and save it into the tomos corpus."""
    from tomos_service import TomosService

    chain, uod = build_praeclarum_chain()
    final_sig = area_signature(uod.current_egi)
    assert final_sig == area_signature(parse_egif(THEOREM_EGIF)), (
        "built proof does not match the Praeclarum Theorema"
    )

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain)  # §3.3 attests before any write
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    print(f"  final: {THEOREM_EGIF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
