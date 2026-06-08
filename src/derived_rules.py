"""
Derived inference rules — the R7 layer: named moves built *atop* Dau's
primitives, each expanding to a sequence of sound, syntactically-equivalent
rules.  (See ``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §6 — the derived-rule layer
is the prerequisite for scaling EG proofs past toy theorems.)

**`universal_instantiation`** — Dau's *iterate-and-join*: instantiate a
universally-quantified line to an existing line of identity.  This is the move
Barbara's step 1 needs and the one a naive IT+ "quietly drops" (it copies the
line as fresh instead of joining it).  Grounded in:

  * Sowa, *cg_hbook.pdf* Fig. 14 ("Proof of universal instantiation"):
    UI = 2i (copy the line into the negative context as a bound use) → 1i
    (insert a *connection* between the two lines) → 3e.  Sowa: "inserting a
    connection between two nodes has the effect of identifying two nodes."
  * Dau, *Mathematical Logic with Diagrams* §14.2 (iteration), §16.1 *Derived
    Rules for Ligatures* — Lemma 16.2 (extending a ligature in a context) and
    Definition 16.6 / Lemma 16.7 (merging two vertices, with the constraint
    ``ctx(v₁) ≥ ctx(e) = ctx(v₂)``), each proven syntactically equivalent, with
    soundness in §17.

In Arisbe's per-context vertex model a line cannot be *rebound* across cut-depth
(``replace_vertex_on_hook`` rightly refuses to point a deep hook at a shallow
line — that *is* Dau's constraint).  So the join is done by **merge**: copy the
universal (IT+ → a fresh line ``z`` deep in the target), add an identity edge
``=``(target_line, z) in ``z``'s context (the connection, sound as a 1i insertion
in a negative area), then merge ``z`` into the target line (Def 16.6 — the merge
rewrites incidence directly, so it crosses depth that a per-hook rebind cannot).

Composes existing public operations only; touches no protected module.
"""

from typing import Optional

import eg_navigation as nav
from egi_core_dau import Edge, ElementID, RelationalGraphWithCuts
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


__all__ = ["universal_instantiation"]
