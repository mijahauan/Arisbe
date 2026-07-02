"""
Derived inference rules — the R7 layer: named moves built *atop* Dau's
primitives, each expanding to a sequence of sound, syntactically-equivalent
rules.  (See ``docs/archived/ORGANON_IMPORT_WALKTHROUGH.md`` §6 — the derived-rule layer
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
(uniqueness-of-group-identity, ``docs/archived/ORGANON_IMPORT_WALKTHROUGH.md`` §4.3).  The
caller discharges the result (a double cut for a single-line universal, the
instantiated scroll for an implication) with the primitive rules.

Composes existing public operations only; touches no protected module.
"""

from dataclasses import replace
from typing import Callable, Iterable, Optional, Tuple

import eg_navigation as nav
from egi_core_dau import AreaPolarity, Edge, ElementID, RelationalGraphWithCuts
from proof_authoring import apply_rule
from vertex_splitting_merging_rules import (
    VertexMergingRule,
    VertexSplitSpec,
    VertexSplittingRule,
)


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


def existential_generalization(
    egi: RelationalGraphWithCuts,
    *,
    edge_id: ElementID,
    position: int,
    new_vertex_id: str = "v_eg",
) -> RelationalGraphWithCuts:
    """Detach the hook at ``position`` of ``edge_id`` from its current line onto a
    fresh existential line — the sound *generalization* (weakening) move, the
    inverse twin of the join in :func:`universal_instantiation`.

    ``(P … a …) ⊢ (P … *z …)``: a relation argument tied to a named/shared line
    ``a`` is loosened to "some line."  Realized as **Dau's vertex split**
    (Def. 16.6 / Lemma 16.7 — split ``a`` into ``a, a'`` joined by ``=``, moving
    this one hook to ``a'``; split/merge are syntactically equivalent) **followed
    by erasing the resulting identity edge** in its (positive) context (the basic
    erasure rule — erasing in an even area is sound and is exactly the weakening
    that turns ``a = a'`` into "``a'`` is some line").

    Precedents: Sowa's **detach** generalization rule (the inverse of join,
    ``u ⊃ v``; CG handbook Fig. 11/14); Peirce's permission to erase an
    evenly-enclosed branch of a line of identity (``Signs of Logic``; CP 4.505 —
    "a line of identity whose outermost part is evenly enclosed refers to
    *something*").  The split half is ``VertexSplittingRule`` (Lemma 16.7); the
    erase half is the ``ERA`` primitive.

    Args:
        edge_id: the relation edge one of whose hooks is being loosened.
        position: the hook index in ``ν(edge_id)`` to detach (0-based).
        new_vertex_id: id for the fresh existential line (must be unique).

    Returns the EGI with that hook on a fresh existential line.  Raises (via the
    ``ERA`` engine) if the identity edge's context is not positive — generalization
    is only sound in an even area.
    """
    v = egi.nu[edge_id][position]
    target_context = nav.area_of(egi, edge_id)

    spec = VertexSplitSpec(
        source_vertex=v,
        target_context=target_context,
        hooks_to_move=[(edge_id, position)],
        new_vertex_id=new_vertex_id,
    )
    g = VertexSplittingRule()._apply_vertex_split(egi, spec)
    # _apply_vertex_split rebuilds without rho/variable_names/alphabet — restore
    # them (the split touches neither; the new line is simply absent from both).
    g = replace(
        g, rho=egi.rho, variable_names=egi.variable_names, alphabet=egi.alphabet
    )

    # Erase the freed identity edge =(v, v') in its positive context: this is the
    # weakening (a = a' ↦ a' existential).
    identity_edge_id = f"id_{v}_{new_vertex_id}"
    return apply_rule("ERA", g, selection=[identity_edge_id])


def universal_generalization(
    egi: RelationalGraphWithCuts,
    *,
    derive_body: Callable[
        [RelationalGraphWithCuts, ElementID, ElementID], RelationalGraphWithCuts
    ],
    axioms: Iterable = (),
) -> RelationalGraphWithCuts:
    """Close a universal ``∀x G(x)`` via the Dau-native **scaffold tactic** —
    NOT a final-graph rewrite ``∃ ⤳ ∀`` (which is provably unsound; see
    ``docs/UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md``).  The tactic realizes the
    UG metatheorem (``Γ ⊢ φ(x)``, ``x`` not free in ``Γ`` ⟹ ``Γ ⊢ ∀x φ(x)``)
    as a construction in which ``x`` is **universal from the start** and the
    body is re-derived beneath it:

    1. ``DC+`` an empty double cut on the sheet — the universal scaffold
       ``~[ ~[ ] ]`` (double-cut rule, an equivalence in any context).
    2. Insert an isolated generic vertex ``[*x]`` on the *outer* (negative)
       cut — Dau's isolated-vertex rule (Def. 24.10), an **equivalence valid in
       arbitrary contexts**; our ``HeavyDotInsertionRule`` permits exactly the
       negative context this step needs.  ``x`` is now oddly enclosed =
       universal, bound to nothing (``∀x⊤ ∧ A ≡ A``).
    3. ``IT+`` each of ``axioms`` (sheet subgraphs that do **not** mention
       ``x``) into the *inner* (positive, depth-2) cut — iteration, an
       equivalence.
    4. Hand the inner area to ``derive_body(egi, inner_area, x_vertex)``, which
       must re-derive the body ``G(x)`` there **composing sound public ops
       only** (every polarity-sensitive move that ran on the sheet, depth 0
       positive, is equally legal at depth 2 positive) and erase the spent
       axiom copies, leaving the inner cut holding exactly ``G(x)``.

    Result: ``A ~[ [*x] ~[ G(x) ] ]`` = ``A ∧ ∀x G(x)`` — sound *by
    construction*: every step is a Dau primitive or a composition of them; the
    one load-bearing primitive (isolated-vertex insertion as an equivalence in
    any context) is Dau Def. 24.10.

    Args:
        derive_body: callable ``(egi, inner_area_id, x_vertex_id) -> egi``
            that derives ``G(x)`` inside the inner area via public ops.
        axioms: sheet subgraphs to iterate into the inner area before the body
            derivation runs — each an element id, a list of ids, or a locator
            ``callable(egi) -> id|list`` resolved against the current state.

    Returns the EGI with the closed universal on the sheet.
    """
    from formal_transformation_rules import FormalTransformationEngine

    # 1 — DC+ an empty double cut on the sheet (equivalence, any context).
    cuts_before = {c.id for c in egi.Cut}
    g = apply_rule("DC+", egi, selection=[], target=egi.sheet)
    new_cuts = {c.id for c in g.Cut} - cuts_before
    outer = next(c for c in new_cuts if nav.area_of(g, c) == g.sheet)
    inner = next(c for c in new_cuts if c != outer)

    # 2 — insert the isolated generic vertex [*x] on the negative outer cut
    # (Dau Def. 24.10 — equivalence; HeavyDotInsertionRule's negative-context
    # restriction is stricter than Dau's "arbitrary contexts", and sufficient).
    verts_before = {v.id for v in g.V}
    result = FormalTransformationEngine().apply_rule(
        "HEAVY_DOT", g, target_area=outer, selected_subgraph=frozenset()
    )
    if not result.success:
        raise ValueError(f"isolated-vertex insertion failed: {result.error_message}")
    # The engine rebuilds without rho/variable_names/alphabet — restore them
    # (the insertion touches none; the new line is simply absent from each).
    g = replace(
        result.result_egi,
        rho=g.rho, variable_names=g.variable_names, alphabet=g.alphabet,
    )
    x = next(iter({v.id for v in g.V} - verts_before))

    # 3 — iterate the axioms into the positive inner cut (equivalence).
    for spec in axioms:
        sel = spec(g) if callable(spec) else spec
        if isinstance(sel, str):
            sel = [sel]
        g = apply_rule("IT+", g, selection=sel, target=inner)

    # 4 — re-derive the body G(x) in the inner (positive) area.
    return derive_body(g, inner, x)


__all__ = [
    "universal_instantiation",
    "instantiate_to_lines",
    "existential_generalization",
    "universal_generalization",
]
