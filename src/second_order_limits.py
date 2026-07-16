"""The B-min linear-form limit, named (author-ratified 2026-07-16).

EGIF/CGIF/CLIF have **no syntax for the second-order layer** — a sorted line
and its quotation oval cannot be written linearly at B-min (inventing surface
syntax on the central linear↔graphical invariant waits for its own authorized
rider; see docs/SECOND_ORDER_CORE_OPENING.md §7). The honest position:

* the EGI JSON carries ``sort``/``quotation`` (the record is total);
* the drawing carries them as committed ink (dotted oval + sort badge, §3.3);
* a linear generator **refuses loudly** rather than silently emitting the
  oval as a negation — the linear picture must never lie;
* corpus/linear-form surfaces show the **first-order projection**
  (``quotation_overlay.project_first_order``) plus this named limit.

This module is import-cycle-free on purpose (the generators import it; the
overlay machinery must not be in their import graph).
"""

from __future__ import annotations


class SecondOrderNotInLinearForm(ValueError):
    """Raised when a linear generator is handed a quotation-bearing graph.

    The caller's options: hand it ``project_first_order(egi)`` (and say so),
    or surface this refusal — never a silent negation-shaped emission."""


def refuse_second_order_in_linear_form(egi, format_name: str) -> None:
    """Raise :class:`SecondOrderNotInLinearForm` iff ``egi`` carries the
    second-order layer (non-empty ``sort``/``quotation``). No-op — zero cost,
    zero behavior change — on a first-order graph."""
    if getattr(egi, "sort", None) or getattr(egi, "quotation", None):
        raise SecondOrderNotInLinearForm(
            f"{format_name} has no syntax for the second-order layer at "
            f"B-min: this graph carries "
            f"{len(getattr(egi, 'sort', {}) or {})} sorted line(s) and "
            f"{len(getattr(egi, 'quotation', {}) or {})} quotation oval(s), "
            f"which a linear form would silently misread as ordinary "
            f"ink/negations. Generate quotation_overlay.project_first_order("
            f"egi) instead, and name the limit."
        )


__all__ = ["SecondOrderNotInLinearForm", "refuse_second_order_in_linear_form"]
