"""
Derived inference rules — the R7 layer: named moves built *atop* Dau's
primitives, each expanding to a sequence of sound, syntactically-equivalent
rules.  (See ``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §6 — the derived-rule layer
is the prerequisite for scaling EG proofs past toy theorems.)

Both moves here are realizations of the *same* underlying idea — Sowa's
"**insert a connection** between two nodes has the effect of identifying two
nodes" (`cg_hbook.pdf` Fig. 14) = a coreference/identity link = (Arisbe) a shared
line of identity, formalized by Dau, *Mathematical Logic with Diagrams* §16.1
*Derived Rules for Ligatures* (Lemma 16.2 extending a ligature; Definition 16.6 /
Lemma 16.7 merging two vertices under ``ctx(v₁) ≥ ctx(e) = ctx(v₂)``; soundness in
§17).  They differ only in whether the universal is **reused** or **consumed**:

**`universal_instantiation`** — the *reuse* variant (iterate-and-join).
Instantiate a universally-quantified line to a *deeper* existing line while
leaving the universal asserted: IT+ (copy the universal into the deeper target,
producing a fresh line ``z``) → insert ``=``(target, z) in ``z``'s context → merge
``z`` into the target.  This is the move Barbara's step 1 needs and the one a naive
IT+ "quietly drops" (it copies the line as fresh instead of joining it).  In
Arisbe's per-context vertex model a line cannot be *rebound* across cut-depth
(``replace_vertex_on_hook`` rightly refuses a deep hook → shallow line — that *is*
Dau's constraint), so the join is a **merge**, which rewrites incidence directly.

**`instantiate_to_lines`** — the *consuming, multi-line* variant (in-place).
Instantiate the universal's own lines to *shallower* existing individuals (e.g.
sheet-level constants), spending the quantifier and leaving the instance in
place: for each ``(source, target)`` insert ``=``(target, source) in the
universal's own (negative) area — a sound insertion — then merge ``source`` into
the (enclosing) ``target``.  ``joins`` may carry several pairs at once, so a
functionality axiom's four lines instantiate to two constants in a single move
(uniqueness-of-group-identity, ``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §4.3).  The
caller discharges the result (a double cut for a single-line universal, the
instantiated scroll for an implication) with the primitive rules.

Composes existing public operations only; touches no protected module.
"""

from typing import Iterable, Optional, Tuple

import eg_navigation as nav
from egi_core_dau import AreaPolarity, Edge, ElementID, RelationalGraphWithCuts
from proof_authoring import apply_rule
from vertex_splitting_merging_rules import VertexMergingRule


def universal_instantiation(
    egi: RelationalGraphWithCuts,
    *,
    universal_cut: ElementID,
    target_area: ElementID,
    join_vertex: ElementID,
    edge_id: str = "e_ui",
) -> RelationalGraphWithCuts:
    """Instantiate a single-line universal to an existing line — Dau's
    iterate-and-join (see module docstring).

    Args:
        universal_cut: the cut subgraph of the universal to iterate (it defines
            its own single line of identity, e.g. A1 = ``~[ (M *x) ~[ (P x) ] ]``).
        target_area: the (more deeply nested) area to iterate the copy into.
        join_vertex: the existing line of identity running through
            ``target_area`` that the copy's line is identified with (it survives
            as the single line; the copy's fresh line is merged into it).
        edge_id: id for the transient identity edge (must be unique in ``egi``).

    Returns the EGI after the join.  Raises ``ValueError`` if the universal is
    not single-line (multi-line instantiation — e.g. a functionality axiom —
    is a later extension).
    """
    before = {v.id for v in egi.V}
    g = apply_rule("IT+", egi, selection=[universal_cut], target=target_area)
    fresh = [vid for vid in ({v.id for v in g.V} - before)]
    if len(fresh) != 1:
        raise ValueError(
            "universal_instantiation expects a single-line universal; "
            f"the iteration introduced {len(fresh)} new lines"
        )
    z = fresh[0]
    # 1i — insert the connection (identity edge) in z's context; sound because
    # insertion in a (negative) context is always permitted, and the edge meets
    # the dominating-nodes condition (join_vertex dominates ctx(z)).
    g = g.with_edge(Edge(id=edge_id), (join_vertex, z), "=", nav.area_of(g, z))
    # Def 16.6 — merge z into join_vertex (ctx(join_vertex) ≥ ctx(e) = ctx(z)).
    g = VertexMergingRule()._apply_vertex_merge(
        g, v1_id=join_vertex, v2_id=z, identity_edge_id=edge_id
    )
    return g


def instantiate_to_lines(
    egi: RelationalGraphWithCuts,
    *,
    universal_cut: ElementID,
    joins: Iterable[Tuple[ElementID, ElementID]],
    edge_id_prefix: str = "e_inst",
) -> RelationalGraphWithCuts:
    """Instantiate a universal's own lines *in place* to existing (enclosing)
    lines — the consuming, multi-line variant of the derived UI/join move (see
    module docstring).

    For each ``(source, target)`` in ``joins``: insert an identity edge
    ``=``(target, source) into the universal's negative area (sound — insertion
    in a negative context is always permitted) and merge ``source`` into
    ``target`` (Def 16.6 — the target encloses the source, so
    ``ctx(target) ≥ ctx(edge) = ctx(source)`` holds).  The universal's quantifier
    is thereby spent and the instance is left in place; the caller discharges the
    remaining structure with the primitive rules.

    Args:
        universal_cut: the universal's outer cut.  Its directly-declared lines are
            the instantiation variables, and the identity edges are inserted into
            its area.  Must be a negative (verso/odd) area.
        joins: pairs ``(source_line, target_line)`` — each ``source_line`` declared
            in ``universal_cut`` is identified with the enclosing ``target_line``.
            Several pairs instantiate several lines at once (e.g. four lines of a
            functionality axiom to two constants).
        edge_id_prefix: prefix for the transient identity edges (each merge
            removes its own edge, so the prefix need only be unique per call).

    Returns the EGI after all joins.  Raises ``ValueError`` if the insertion area
    is not negative (an in-place insertion there would be unsound).
    """
    polarity, _ = nav.polarity_of(egi, universal_cut)
    if polarity is not AreaPolarity.NEGATIVE:
        raise ValueError(
            "instantiate_to_lines requires the universal's area to be negative "
            "(verso/odd); an identity-edge insertion in a positive area is unsound"
        )
    g = egi
    for i, (source, target) in enumerate(joins):
        edge_id = f"{edge_id_prefix}_{i}"
        # 1i — insert the connection (identity edge) in the source line's area.
        g = g.with_edge(Edge(id=edge_id), (target, source), "=", universal_cut)
        # Def 16.6 — merge source into the enclosing target (target survives).
        g = VertexMergingRule()._apply_vertex_merge(
            g, v1_id=target, v2_id=source, identity_edge_id=edge_id
        )
    return g


__all__ = ["universal_instantiation", "instantiate_to_lines"]
