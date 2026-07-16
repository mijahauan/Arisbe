"""
The reference-node increment-2 **use/mention fork** — the rider on the B-min
core opening (verdict B3: one core opening, both riders;
REFERENCE_AND_TRANSCLUSION_NODE §7).

The fork's discipline, pinned as tests:

* **Mention** (B named as an object) = second-order naming — now CORE-carried:
  the commentary's name is a proposition-sorted line (``with_sort``), its
  badge committed drawn ink, and resolution produces the target for checking
  **without importing one element of it** (no co-assertion across universes).
* **Use** (B bears on A) = governed import via the scroll ``~[ B ~[ G ] ]`` —
  and ONLY that. There is deliberately no cross-UoD splice resolver in
  ``reference_node``: the deferral is pinned here so building one is a
  knowing act, not drift.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_generator_dau import generate_egif
from quotation_overlay import UoDQuotationResolver, quotation_marks_from_list
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


class TestMentionSide:
    def test_name_is_core_sorted_with_no_oval(self, tomos):
        uod = tomos.load_uod("peirce_law_commentary", attest=False)
        egi = uod.current_egi
        name_id = next(v.id for v in egi.V if v.label == "peirce_law")
        assert egi.sort.get(name_id) == "proposition"
        assert egi.quotation == {}  # cross-UoD cannot inline: no oval

    def test_mention_resolves_without_co_assertion(self, tomos):
        uod = tomos.load_uod("peirce_law_commentary", attest=False)
        host = uod.current_egi
        marks = quotation_marks_from_list(
            [m for m in (tomos.load_quotations("peirce_law_commentary") or [])]
        )
        assert len(marks) == 1 and marks[0].kind == "uod"
        target = UoDQuotationResolver(tomos).resolve(marks[0])
        host_ids = {v.id for v in host.V} | {e.id for e in host.E} | {
            c.id for c in host.Cut
        }
        target_ids = {v.id for v in target.V} | {e.id for e in target.E} | {
            c.id for c in target.Cut
        }
        assert not (host_ids & target_ids), (
            "mention must import no element of the mentioned universe"
        )
        # the target really is Peirce's law, not a copy pasted into the host
        assert "P" in set(target.rel.values())
        assert set(host.rel.values()) == {"cites"}

    def test_sort_badge_is_committed_drawn_ink(self, tomos):
        from web_api.services.layout_service import generate_layout

        uod = tomos.load_uod("peirce_law_commentary", attest=False)
        egi = uod.current_egi
        dto, svg = generate_layout(egi)
        name_id = next(v.id for v in egi.V if v.label == "peirce_law")
        assert (dto.vertex_sorts or {}).get(name_id) == "proposition"
        assert 'data-sort="proposition"' in svg

    def test_s3_quoted_half_stays_honestly_partial(self, tomos):
        """A mention draws no oval, so its quoted graph cannot read back from
        the drawing — S3 skip-named, never silently passed (the B-min
        horizon)."""
        from quotation_overlay import run_quotation_mark

        uod = tomos.load_uod("peirce_law_commentary", attest=False)
        marks = quotation_marks_from_list(
            tomos.load_quotations("peirce_law_commentary"))
        rep = run_quotation_mark(
            uod.current_egi, marks[0], UoDQuotationResolver(tomos))
        assert rep.read_back_faithful is None
        assert any("S3" in lim for lim in rep.honest_limits)


class TestUseSideDeferral:
    def test_no_cross_uod_splice_resolver_exists(self):
        """The use fork (scroll-import) stays additive, later: reference_node
        deliberately ships no UoD-kind resolver whose resolution splices
        another universe into the host. Building one must be a knowing act."""
        import reference_node

        kinds = {
            getattr(getattr(reference_node, n), "kind", None)
            for n in dir(reference_node)
            if isinstance(getattr(reference_node, n), type)
        }
        assert "uod" not in kinds

    def test_quotation_resolution_never_touches_the_host(self, tomos):
        uod = tomos.load_uod("peirce_law_commentary", attest=False)
        host = uod.current_egi
        # linear identity via the projection (the bearing graph refuses)
        from quotation_overlay import project_first_order

        before = generate_egif(project_first_order(host))
        marks = quotation_marks_from_list(
            tomos.load_quotations("peirce_law_commentary"))
        UoDQuotationResolver(tomos).resolve(marks[0])
        assert generate_egif(project_first_order(host)) == before
