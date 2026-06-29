"""The reference node — increment 1: intra-UoD definition (/schema) references.

**Additive. Touches no protected module.** See
``docs/REFERENCE_AND_TRANSCLUSION_NODE.md`` for the design of record.

A *reference* is a **Form-2 edge** (a defined-relation spot, today) plus an
**overlay record** (:class:`ReferenceMark`) that names what the edge points at
and carries its provenance — kept *beside* the EGI, the way annotations / layout
deltas are, so the protected data model is untouched. Resolution reuses the
definition splice machinery (``definitions.expand_at`` / ``fold``); the law
``RESOLVE ≡ INLINED-AND-ATTESTED`` is checked by
:mod:`reference_resolution_check`.

Increment 1 is **intra-UoD on purpose** (``docs/…NODE.md`` §4½): resolving a
reference is co-assertion (juxtaposition = conjunction; the double cut around it
is *inert*), which is a soundness **guarantee** for a same-universe, conservative
definition body — and a universe-merging **hazard** for a foreign UoD. So the
first slice resolves only same-universe targets. The :class:`ReferenceResolver`
seam is shaped exactly like ``cl_import_resolver``'s ``ImportResolver`` Protocol
so widening it to a corpus UoD (the *use* = scroll-import / *mention* =
second-order-naming fork) is additive in increment 2, not a rewrite of callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, Tuple, runtime_checkable

from egi_core_dau import ElementID, RelationalGraphWithCuts
from definitions import DefinitionRegistry, FoldPoint, expand_at, fold
from reference_resolution_check import (
    Reference,
    ReferenceReport,
    attest_reference as _attest_candidate,
    run_reference,
)


# --------------------------------------------------------------------------- #
# The overlay record — reference-ness + provenance, kept beside the EGI.
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ReferenceMark:
    """One reference, recorded as an overlay on a host EGI's edge.

    ``edge_id`` is the Form-2 reference edge in the host (a defined-relation
    spot).  ``target`` names what it points at; ``kind`` is the target family
    (``"definition"`` in increment 1; ``"schema"`` / ``"uod"`` later).  ``origin``
    locates the target's home (a registry label, a UoD id) for provenance, and
    ``warrant`` defaults to ``"low"`` — a reference is an abbreviation, not a
    truth-claim (``docs/MANIFEST_AND_MEANING.md``): it earns standing only through
    what its *resolved* material earns.  Standing propagation
    (``provenance.standing_of``) is the deferred §7 item.

    The mark is *not* part of the EGI — it serialises (``to_dict`` / ``from_dict``)
    so a UoD can persist its references the way it persists annotations, with no
    change to the protected data model.
    """

    edge_id: ElementID
    target: str
    kind: str = "definition"
    origin: Optional[str] = None
    warrant: str = "low"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "target": self.target,
            "kind": self.kind,
            "origin": self.origin,
            "warrant": self.warrant,
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReferenceMark":
        return cls(
            edge_id=d["edge_id"],
            target=d["target"],
            kind=d.get("kind", "definition"),
            origin=d.get("origin"),
            warrant=d.get("warrant", "low"),
            extra=dict(d.get("extra", {})),
        )


# --------------------------------------------------------------------------- #
# The resolver seam — name → body, shaped like cl_import_resolver's Protocol.
# --------------------------------------------------------------------------- #

@runtime_checkable
class ReferenceResolver(Protocol):
    """Resolves a reference edge in place to its inlined body.

    ``resolve_at`` returns ``(resolved_egi, fold_point)`` — the fold point is the
    inverse data when one exists (definitions: an exact ``fold``), else ``None``
    (a resolve-only reference, e.g. a future UoD transclusion).  ``can_resolve``
    lets a host check a mark before committing.  ``kind`` names the target family
    this resolver serves, so a :class:`ChainReferenceResolver` can dispatch.
    """

    kind: str

    def can_resolve(self, egi: RelationalGraphWithCuts, edge_id: ElementID) -> bool: ...

    def resolve_at(
        self, egi: RelationalGraphWithCuts, edge_id: ElementID
    ) -> Tuple[RelationalGraphWithCuts, Optional[FoldPoint]]: ...


class DefinitionReferenceResolver:
    """The increment-1 resolver: a reference whose target is a definition in a
    same-universe :class:`~definitions.DefinitionRegistry`.  Resolution *is*
    ``expand_at`` (with its exact ``fold`` inverse), so the conservative-
    abbreviation guarantee of §4½ holds by construction."""

    kind = "definition"

    def __init__(self, registry: DefinitionRegistry):
        self.registry = registry

    def can_resolve(self, egi: RelationalGraphWithCuts, edge_id: ElementID) -> bool:
        rel = egi.rel.get(edge_id)
        return rel is not None and rel in self.registry

    def resolve_at(
        self, egi: RelationalGraphWithCuts, edge_id: ElementID
    ) -> Tuple[RelationalGraphWithCuts, Optional[FoldPoint]]:
        return expand_at(egi, self.registry, edge_id, return_fold_point=True)


class ChainReferenceResolver:
    """Tries each resolver in order — the seam that lets schema / UoD resolvers
    drop in beside the definition resolver without touching callers (mirrors
    ``cl_import_resolver.ChainResolver``)."""

    kind = "chain"

    def __init__(self, *resolvers: ReferenceResolver):
        self.resolvers = resolvers

    def _pick(self, egi, edge_id) -> Optional[ReferenceResolver]:
        for r in self.resolvers:
            if r.can_resolve(egi, edge_id):
                return r
        return None

    def can_resolve(self, egi: RelationalGraphWithCuts, edge_id: ElementID) -> bool:
        return self._pick(egi, edge_id) is not None

    def resolve_at(
        self, egi: RelationalGraphWithCuts, edge_id: ElementID
    ) -> Tuple[RelationalGraphWithCuts, Optional[FoldPoint]]:
        r = self._pick(egi, edge_id)
        if r is None:
            raise ValueError(f"no resolver can resolve edge {edge_id!r}")
        return r.resolve_at(egi, edge_id)


# --------------------------------------------------------------------------- #
# Authoring, resolving, and attesting a reference.
# --------------------------------------------------------------------------- #

def mark_reference(
    egi: RelationalGraphWithCuts,
    edge_id: ElementID,
    resolver: ReferenceResolver,
    *,
    origin: Optional[str] = None,
    warrant: str = "low",
    **extra: Any,
) -> ReferenceMark:
    """Record edge ``edge_id`` as a reference the ``resolver`` can resolve.

    Raises ``ValueError`` if the resolver cannot resolve the edge (no silent
    dangling reference — the honest-horizon floor, R4).
    """
    if not resolver.can_resolve(egi, edge_id):
        raise ValueError(
            f"edge {edge_id!r} is not a resolvable reference for "
            f"{getattr(resolver, 'kind', '?')!r} resolver"
        )
    return ReferenceMark(
        edge_id=edge_id,
        target=egi.rel.get(edge_id, edge_id),
        kind=getattr(resolver, "kind", "definition"),
        origin=origin,
        warrant=warrant,
        extra=dict(extra),
    )


def resolve_reference(
    egi: RelationalGraphWithCuts,
    mark: ReferenceMark,
    resolver: ReferenceResolver,
) -> Tuple[RelationalGraphWithCuts, Optional[FoldPoint]]:
    """Resolve one marked reference in ``egi`` — the inlined EGI + the inverse
    data (``None`` when the reference is resolve-only)."""
    return resolver.resolve_at(egi, mark.edge_id)


def refold_reference(
    resolved: RelationalGraphWithCuts, fold_point: FoldPoint
) -> RelationalGraphWithCuts:
    """Contract a resolved reference back to its spot — the exact inverse, for the
    reference kinds that have one (definitions)."""
    return fold(resolved, fold_point)


def reference_horizon(
    egi: RelationalGraphWithCuts,
    mark: ReferenceMark,
    resolver: ReferenceResolver,
) -> int:
    """How many elements lie *beyond the view* of this reference — the count of
    graph elements that would appear if it were resolved in place.

    This is the "+N beyond view" the render glyph (increment 1b) shows, reusing
    the overview horizon idiom: a reference spot stands for `N` hidden elements.
    For a definition reference it is exactly the spliced body size
    (``FoldPoint.body_elements``); for a resolve-only reference it is the net new
    elements (resolved − host).
    """
    resolved, fp = resolver.resolve_at(egi, mark.edge_id)
    if fp is not None:
        return len(fp.body_elements)
    host_ids = (
        {v.id for v in egi.V} | {e.id for e in egi.E} | {c.id for c in egi.Cut}
    )
    res_ids = (
        {v.id for v in resolved.V}
        | {e.id for e in resolved.E}
        | {c.id for c in resolved.Cut}
    )
    return len(res_ids - host_ids)


def render_marks(
    egi: RelationalGraphWithCuts,
    marks,
    resolver: ReferenceResolver,
) -> Dict[ElementID, int]:
    """Build the ``{edge_id: horizon}`` map the renderer's ``reference_marks``
    parameter consumes — one entry per reference spot, carrying its horizon."""
    return {m.edge_id: reference_horizon(egi, m, resolver) for m in marks}


def reference_candidate(
    host: RelationalGraphWithCuts,
    mark: ReferenceMark,
    resolver: ReferenceResolver,
    *,
    inlined: Optional[RelationalGraphWithCuts] = None,
) -> Reference:
    """Build the :class:`reference_resolution_check.Reference` for ``mark`` so the
    law can be attested.

    Pass ``inlined`` (an *independent* inlining) for the full R1 check — the
    offline correctness proof, used by tests against ground truth.  At a
    production boundary there is no independent inlining, so ``inlined`` defaults
    to the resolved graph (R1 trivially holds) and the meaningful runtime teeth
    are **R2** (the resolved graph attests §3.3) + **R3** (refold recovers the
    host — the round-trip soundness check).
    """
    resolved, fp = resolver.resolve_at(host, mark.edge_id)
    refold = (lambda r, _fp=fp: fold(r, _fp)) if fp is not None else None
    return Reference(
        name=mark.target,
        origin=f"{mark.kind}:{mark.origin or 'local'}",
        resolve=lambda r=resolved: r,
        inlined=inlined if inlined is not None else resolved,
        host=host,
        refold=refold,
    )


def attest_reference(
    host: RelationalGraphWithCuts,
    mark: ReferenceMark,
    resolver: ReferenceResolver,
    *,
    layout_fn=None,
    inlined: Optional[RelationalGraphWithCuts] = None,
    context: Optional[str] = None,
) -> None:
    """Boundary hook: raise ``ReferenceViolation`` if resolving ``mark`` breaks
    the law (R2 needs ``layout_fn``; R3 runs whenever an inverse exists), else
    None.  The reference analogue of ``layout_service``'s ``attest_correspondence``
    call."""
    cand = reference_candidate(host, mark, resolver, inlined=inlined)
    _attest_candidate(cand, layout_fn=layout_fn, context=context or mark.target)


def run_reference_mark(
    host: RelationalGraphWithCuts,
    mark: ReferenceMark,
    resolver: ReferenceResolver,
    *,
    layout_fn=None,
    inlined: Optional[RelationalGraphWithCuts] = None,
) -> ReferenceReport:
    """Non-raising measurement form — a structured report for a marked reference."""
    cand = reference_candidate(host, mark, resolver, inlined=inlined)
    return run_reference(cand, layout_fn=layout_fn)


__all__ = [
    "ReferenceMark",
    "ReferenceResolver",
    "DefinitionReferenceResolver",
    "ChainReferenceResolver",
    "mark_reference",
    "resolve_reference",
    "refold_reference",
    "reference_horizon",
    "render_marks",
    "reference_candidate",
    "attest_reference",
    "run_reference_mark",
]
