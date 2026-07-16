"""
B-min stage 4 — the second-order reader and the committed drawn convention.

The crossing's hinge: **S3 (read-back one order up) flips from skip-named to
checked**. The sort and the quotation now live in the core, the layout
service decorates every served DTO with the committed marks (dotted oval
stroke + sort badge — the ``order_label`` idiom), the renderer draws them,
``eg_reader.read_drawing`` recovers them from the drawing, and
``second_order_reader.read_quotation_back`` supplies the harness's
``read_back`` injection point.

What is pinned:

1. **Round trip** — render→read recovers ``(sort, quoted)``; S3 checks true
   end-to-end through the real ELK path.
2. **Falsifiers** — an undotted oval fails §3.3's committed-convention check;
   a wrong/missing badge fails; a doctored oval interior fails S3's
   quoted-graph half; an oval drawn away from its name fails the attachment.
3. **First-order silence** — a sortless graph's DTO carries None in both new
   fields, renders byte-identically, and §3.3 runs zero new checks.
"""

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correspondence_attestation import (
    CorrespondenceViolation,
    attest_correspondence,
    check_correspondence,
)
from eg_navigation import same_graph
from eg_reader import read_drawing, reading_matches_egi
from egif_parser_dau import parse_egif
from quotation_overlay import (
    EGIFQuotationResolver,
    QuotationMark,
    quotation_candidate,
    quote_existing_name,
)
from second_order_check import run_quotation
from second_order_reader import quotation_read_backs, read_quotation_back
from web_api.services.layout_service import generate_layout

LAW = "~[ (swan *s) ~[ (white s) ] ]"


@pytest.fixture(scope="module")
def quoted_pair():
    """(host, dto, cut_id, name_id, law) — a core-carried quotation served
    through the real layout path."""
    host = parse_egif('(superseded "M_law" "Nox")')
    name_id = next(v.id for v in host.V if v.label == "M_law")
    law = parse_egif(LAW)
    quoted_host, cut_id = quote_existing_name(host, name_id, law)
    dto, _svg = generate_layout(quoted_host)
    return quoted_host, dto, cut_id, name_id, law


class TestCommittedConvention:
    def test_served_dto_carries_the_marks(self, quoted_pair):
        host, dto, cut_id, name_id, _ = quoted_pair
        assert dto.cut_stroke == {cut_id: "quotation"}
        assert dto.vertex_sorts == {name_id: "proposition"}

    def test_renderer_draws_dotted_oval_and_badge(self, quoted_pair):
        host, dto, *_ = quoted_pair
        from simple_svg_renderer import SimpleSVGRenderer

        svg = SimpleSVGRenderer().render_to_svg(dto, egi=host)
        assert 'data-cut-stroke="quotation"' in svg
        assert "sort-badge" in svg and "stroke-dasharray" in svg

    def test_first_order_dto_is_silent(self):
        egi = parse_egif('~[ (P *x) ~[ (Q x) ] ]')
        dto, _ = generate_layout(egi)
        assert dto.cut_stroke is None and dto.vertex_sorts is None
        assert not check_correspondence(egi, dto)


class TestReadBack:
    def test_reader_recovers_sort_and_quoted(self, quoted_pair):
        host, dto, cut_id, name_id, law = quoted_pair
        reading = read_quotation_back(host, dto, cut_id)
        assert reading.sort == "proposition"
        assert same_graph(reading.quoted, law)

    def test_read_drawing_recovers_the_maps_geometrically(self, quoted_pair):
        host, dto, cut_id, name_id, _ = quoted_pair
        reading = read_drawing(dto)
        assert reading.quotation_areas == {cut_id: name_id}
        assert reading.vertex_sorts == {name_id: "proposition"}
        assert reading_matches_egi(reading, host)

    def test_s3_checks_true_end_to_end(self, quoted_pair):
        host, dto, cut_id, name_id, law = quoted_pair
        mark = QuotationMark(element_id=name_id, target=LAW)
        cand = quotation_candidate(
            host, mark, EGIFQuotationResolver(), quoted_ground=law,
            read_back=quotation_read_backs(host, dto)[cut_id])
        rep = run_quotation(cand)
        assert rep.read_back_faithful is True
        assert rep.ok, rep.failures


class TestFalsifiers:
    def test_undotted_oval_fails_the_committed_convention(self, quoted_pair):
        host, dto, cut_id, *_ = quoted_pair
        doctored = dataclasses.replace(dto, cut_stroke=None)
        with pytest.raises(CorrespondenceViolation, match="dotted stroke"):
            attest_correspondence(host, doctored, context="falsifier")

    def test_wrong_badge_fails(self, quoted_pair):
        host, dto, cut_id, name_id, _ = quoted_pair
        doctored = dataclasses.replace(
            dto, vertex_sorts={name_id: "abstraction"})
        with pytest.raises(CorrespondenceViolation, match="sort"):
            attest_correspondence(host, doctored, context="falsifier")

    def test_missing_badge_fails_read_back(self, quoted_pair):
        host, dto, cut_id, *_ = quoted_pair
        doctored = dataclasses.replace(dto, vertex_sorts=None)
        with pytest.raises(ValueError):
            read_quotation_back(host, doctored, cut_id)

    def test_doctored_oval_interior_fails_s3(self, quoted_pair):
        host, dto, cut_id, name_id, law = quoted_pair
        # doctor the EGI one level down: the oval quotes a DIFFERENT law
        # (structural change) while the mark still claims the swan law
        other = parse_egif("~[ (crow *c) ]")
        bare = host.without_quotation(cut_id)
        # the host-wired name survives de-quoted; re-quote it with other ink
        redone, new_cut = quote_existing_name(bare, name_id, other)
        dto2, _ = generate_layout(redone)
        mark = QuotationMark(element_id=name_id, target=LAW)
        cand = quotation_candidate(
            redone, mark, EGIFQuotationResolver(), quoted_ground=law,
            read_back=lambda: read_quotation_back(redone, dto2, new_cut))
        rep = run_quotation(cand)
        assert rep.read_back_faithful is False
        assert not rep.ok

    def test_oval_away_from_its_name_fails_attachment(self, quoted_pair):
        host, dto, cut_id, name_id, _ = quoted_pair
        # translate the oval's drawn bounds far away — the drawn attachment
        # (same area, the eye's pairing) breaks even though the stroke is right
        from layout_dto import BoundingBox

        b = dto.cut_bounds[cut_id]
        moved = dict(dto.cut_bounds)
        moved[cut_id] = BoundingBox(
            b.min_x + 5000, b.min_y + 5000, b.max_x + 5000, b.max_y + 5000)
        doctored = dataclasses.replace(dto, cut_bounds=moved)
        failures = check_correspondence(host, doctored)
        assert failures  # containment and/or second-order attachment name it

    def test_a_reader_failure_is_an_s3_failure_never_a_pass(self, quoted_pair):
        host, dto, cut_id, name_id, law = quoted_pair
        mark = QuotationMark(element_id=name_id, target=LAW)

        def broken_reader():
            raise ValueError("no device drawn")

        cand = quotation_candidate(
            host, mark, EGIFQuotationResolver(), quoted_ground=law,
            read_back=broken_reader)
        rep = run_quotation(cand)
        assert rep.read_back_faithful is False
        assert not rep.ok
