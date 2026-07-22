"""The coordinator kytos for the West-in-kytē FED arrangement.

Members export their M as attributed relation-name cells (asserts "folder-k" ⌜rel⌝)
— mention-not-use, structure-only, the coordination currency (spec §4). The digest
is a world-scroll M built one licensed INS-of-cell + one quote_existing_name per new
(folder, relname), mirroring oracle_notes.bank_answer (oracle_notes.py:1439-1470).

The member's own M is never touched: :func:`member_relation_names` only *reads*
it (via ``m_view``), and :meth:`Coordinator.ingest` never passes the member
graph itself to any mutating call — only its distinct relation-name strings
cross into the digest, quoted (mentioned) rather than spliced in (used)."""

from __future__ import annotations

from typing import Set, Tuple

from egi_core_dau import RelationalGraphWithCuts, create_empty_graph
from egif_parser_dau import parse_egif
from world_scroll import m_view, find_world_scroll, wrap_m, enlarge_m
from quotation_overlay import quote_existing_name


def member_relation_names(member_m: RelationalGraphWithCuts) -> frozenset:
    """The distinct relation names present in a member's M (read through
    ``m_view`` so a resident member M and a bare sheet-level fixture both
    work)."""
    view = m_view(member_m)
    return frozenset(view.rel[e.id] for e in view.E if e.id in view.rel)


def _utterance_graph(label: str) -> RelationalGraphWithCuts:
    """Quoted ink: one constant vertex named by the projected relation name."""
    return parse_egif(f'(utterance "{label}")')


class Coordinator:
    """Holds the digest world-scroll M of attributed relation-name cells.

    The digest starts as the **empty residence** ``~[ ~[ ] ]`` (W + hold, zero
    cells — the ``wrap_m`` corollary: from a blank sheet, DC+ alone creates
    it). ``wrap_m(create_empty_graph())`` is used rather than
    ``wrap_m(parse_egif("~[ ]"))``: the latter re-wraps an already-empty cut
    as *content*, which INS's it as a spurious non-empty cell (a cell whose
    interior is itself just an empty cut) — verified empirically against
    ``find_world_scroll`` before settling on the empty-graph form.
    """

    def __init__(self) -> None:
        self._digest, _scroll = wrap_m(create_empty_graph())
        assert find_world_scroll(self._digest) is not None, (
            "Coordinator digest must start as a recognized world-scroll"
        )
        self.held: Set[Tuple[str, str]] = set()
        self.cells_written: int = 0

    def ingest(self, folder: str, member_m: RelationalGraphWithCuts) -> int:
        """Project ``member_m``'s *new* relation names into one attributed
        cell each. Mention-not-use: ``member_m`` is read only by
        ``member_relation_names`` (which reads through ``m_view``, itself
        non-mutating) — it is never passed to ``enlarge_m`` or spliced into
        the digest; only its relation-name strings cross over, quoted."""
        written = 0
        for rel in sorted(member_relation_names(member_m)):
            key = (folder, rel)
            if key in self.held:
                continue
            # One licensed INS-of-cell: (asserts "folder-k" *q), then quote *q.
            attribution = f'(asserts "{folder}" *q)'
            before = set(find_world_scroll(self._digest).cell_ids)
            m2 = enlarge_m(self._digest, attribution)
            scroll2 = find_world_scroll(m2)
            (new_cell,) = set(scroll2.cell_ids) - before
            eid = next(
                e.id
                for e in m2.E
                if m2.get_context(e.id) == new_cell and m2.rel[e.id] == "asserts"
            )
            q_vid = m2.nu[eid][1]
            self._digest, _cut_id = quote_existing_name(
                m2, q_vid, _utterance_graph(rel)
            )
            self.held.add(key)
            written += 1
        self.cells_written += written
        return written


__all__ = ["Coordinator", "member_relation_names"]
