"""The second-order reader — S3's ``read_back``, built at ① B-min.

``read_drawing``'s second-order sibling: recover the quotation device — the
quoting line's **sort** and the dotted oval's **quoted graph** — from the
drawing, so :mod:`second_order_check`'s S3 (read-back one order up) runs for
real instead of skip-named. The harness is unchanged; this module supplies
its ``read_back`` injection point (``second_order_check.Quotation.read_back``).

Division of labor (the same one first-order §3.3 embodies): the *structure* —
area tree, incidence, quoted-ness (dotted stroke), sort (drawn badge), and
the name↔oval attachment (same drawn area, nearest) — is recovered from the
drawing by :func:`eg_reader.read_drawing`; symbol *text* (labels, relation
names) pairs from the EGI, exactly as ``reading_matches_egi`` already does.
The reader **raises** when the drawing does not carry the device (an undotted
oval, a missing badge, a doctored area tree) — S3 then *fails*, never
silently passes.

Honest limit, named: a cross-UoD mention draws the sorted name but no oval
(a whole other universe cannot inline), so its S3 stays skip-named — the sort
badge is still committed ink held total by §3.3's committed-convention check,
and the quoted graph remains a resolver-served S4 horizon.
"""

from __future__ import annotations

from egi_core_dau import ElementID, RelationalGraphWithCuts
from eg_reader import read_drawing, reading_matches_egi
from layout_dto import LayoutDTO
from quotation_overlay import lift_quotation
from second_order_check import QuotationReading


def read_quotation_back(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    cut_id: ElementID,
) -> QuotationReading:
    """Recover the second-order device at ``cut_id`` from the drawing.

    Reads the whole drawing geometrically (``read_drawing``), demands that the
    reading — area tree, incidence, sort badges, dotted ovals, attachments —
    is exactly the EGI's (``reading_matches_egi``, now second-order-aware),
    then returns the ``(sort, quoted)`` pair: the drawn badge's sort and the
    oval's contents lifted as a standalone graph.

    Raises ``ValueError`` when the drawing does not carry the device — the
    caller's S3 records a failure, never a silent pass."""
    reading = read_drawing(dto)
    if not reading_matches_egi(reading, egi):
        raise ValueError(
            f"the drawing does not read back to the EGI (quotation {cut_id}): "
            f"the second-order device was not recovered from geometry"
        )
    name_id = reading.quotation_areas.get(cut_id)
    if name_id is None:
        raise ValueError(
            f"the drawing carries no dotted oval read as quotation {cut_id}"
        )
    sort = reading.vertex_sorts.get(name_id)
    if sort is None:
        raise ValueError(
            f"the quoting name {name_id} carries no drawn sort badge"
        )
    return QuotationReading(sort=sort, quoted=lift_quotation(egi, cut_id))


def quotation_read_backs(egi: RelationalGraphWithCuts, dto: LayoutDTO):
    """One ``read_back`` thunk per quotation cut in ``egi`` — the shape a
    boundary hook feeds into ``second_order_check.Quotation.read_back``.
    Returns ``{cut_id: callable}`` (empty for a first-order pair)."""
    return {
        cut_id: (lambda c=cut_id: read_quotation_back(egi, dto, c))
        for cut_id in getattr(egi, "quotation", {}) or {}
    }


def attest_served_quotations(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    *,
    layout_fn=None,
    attest_fn=None,
    context: str = None,
) -> None:
    """The regime-2 second-order boundary hook (SECOND_ORDER_CORE_OPENING §5
    step 3): a served, asserted second-order (EGI, drawing) pair verifies
    S1–S3 the way ``layout_service`` verifies §3.3.

    Candidates are built from the core maps alone (no overlay needed at a
    production boundary): the quoted ground defaults to the drawn oval's own
    contents — S2's structural half holds trivially, and the runtime teeth are
    S1 (stratification off the drawing), S2's §3.3 half one level down (iff
    ``layout_fn``), and S3 (the served drawing reads the device back).
    Raises ``SecondOrderViolation``; no-op on a first-order pair."""
    quotation_map = getattr(egi, "quotation", None) or {}
    if not quotation_map:
        return
    from quotation_overlay import is_enclosed
    from second_order_check import Quotation, attest_quotation

    for cut_id, name_id in quotation_map.items():
        quoted = lift_quotation(egi, cut_id)
        cand = Quotation(
            name=cut_id,
            sort=egi.sort.get(name_id, ""),
            host=egi,
            resolve=lambda g=quoted: g,
            quoted_ground=quoted,
            enclosed=is_enclosed(egi, name_id),
            read_back=lambda c=cut_id: read_quotation_back(egi, dto, c),
        )
        attest_quotation(
            cand, layout_fn=layout_fn, attest_fn=attest_fn,
            context=context or f"served quotation {cut_id}")


__all__ = [
    "read_quotation_back",
    "quotation_read_backs",
    "attest_served_quotations",
]
