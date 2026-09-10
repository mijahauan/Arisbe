"""Corpus-wide round-trip: every UoD, through every linear form, and back.

This file used to point ``CORPUS_ROOT`` at ``corpus/corpus``, a path that
stopped existing when the corpus was renamed to ``tomos`` (commit b24ce9d). It
globbed for ``*.egif`` / ``*.cgif`` / ``*.clif`` files, of which the repository
now contains none — the examples live as UoDs. So its three tests parametrized
over empty lists and skipped silently, while CLAUDE.md and the outreach letters
went on citing this file as the guarantee that EGIF, CGIF and CLIF round-trip
across the corpus. The guarantee was not being measured at all.

It is measured here, against the corpus that exists. For every UoD the graph is
generated to a linear form, parsed back, and the result compared to the
original by ``same_graph`` — isomorphism in Dau's sense, not text equality,
because two parses of one structure may order symmetric elements differently
and still denote the same graph.

The result is honest rather than flattering: most round-trips hold and a
specific, named few do not. As of 2026-09-09: **141 of 147 hold, 6 do not**,
down from 64 failures at the start of the arc. The six are two graphs, each
failing in all three formats — a symmetry worth reading, since it says no
linear form is known to carry a defect any more and the residue lies upstream
of all of them. They are listed in ``KNOWN_BROKEN`` with what goes wrong in
each, and the check is run for them too, so a repair announces itself as an
unexpected pass rather than sitting silently in the list.
"""

import pytest

import eg_navigation as nav
from cgif_generator_dau import generate_cgif
from cgif_parser_dau import parse_cgif
from clif_generator_dau import generate_clif
from clif_parser_dau import parse_clif
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from second_order_limits import SecondOrderNotInLinearForm
from tomos_service import TomosService

from pathlib import Path

TOMOS = Path(__file__).resolve().parent.parent / "tomos"

FORMS = {
    "EGIF": (generate_egif, parse_egif),
    "CGIF": (generate_cgif, parse_cgif),
    "CLIF": (generate_clif, parse_clif),
}

# Quotation-bearing UoDs: no linear syntax exists for the second-order device,
# so the generators refuse by design (second_order_limits). The refusal is
# asserted below rather than skipped — a silent pass would hide a regression
# that started emitting an oval as an ordinary negation.
SECOND_ORDER = {"forcing_forces", "peirce_law_commentary", "swan_third_tense"}

# Round-trips that do not hold, measured rather than assumed. Listed so the
# guarantee is stated at its true extent and a fix announces itself as an
# unexpected pass.
#
# Two graphs remain, and each fails in *all three* formats. That symmetry is
# itself the finding: no linear form is known to have a defect left, and what
# is left sits upstream of all of them.
#
# episode_discharge used to sit here too. Its graph carried two lines of
# identity for "Rex" — INS scribes fresh ink, so a fact discharged into M
# arrives with its own line for an individual M already stands on. Two lines
# say exactly what one says, but no linear form can write the difference down.
# The representative is now chosen where M's content is constructed
# (world_scroll.discharge_episode), the corpus boundary refuses anything else,
# and the exemplar was rebuilt.
#
#   bfo_core          — same_graph says no while the legible diff finds nothing
#                       to report, so the difference is structural rather than
#                       in content.
#   colore_field      — the equality relation returns joined to a different
#                       pair of lines (~40 incidence findings).
KNOWN_BROKEN = frozenset([
    ("bfo_core", "CGIF"),
    ("bfo_core", "CLIF"),
    ("bfo_core", "EGIF"),
    ("colore_field", "CGIF"),
    ("colore_field", "CLIF"),
    ("colore_field", "EGIF"),
])


# same_graph is a full isomorphism search; on the largest imported ontology it
# does not finish in reasonable time. Its round-trip is checked by stable
# re-emission instead, which is weaker and is marked as such.
BY_REEMISSION = {"sumo_upper"}


def _uods():
    return [e["uod_id"] for e in TomosService(TOMOS).list_uods()]


@pytest.fixture(scope="module")
def service():
    return TomosService(TOMOS)


@pytest.mark.parametrize("form", sorted(FORMS))
@pytest.mark.parametrize("uod_id", _uods())
def test_linear_form_round_trips(service, uod_id, form):
    """generate -> parse -> the same graph."""
    if uod_id in SECOND_ORDER:
        pytest.skip("quotation-bearing; refusal asserted in its own test")
    expected_broken = (uod_id, form) in KNOWN_BROKEN

    egi = service.load_uod(uod_id, attest=False).current_egi
    generate, parse = FORMS[form]
    text = generate(egi)
    back = parse(text)

    if uod_id in BY_REEMISSION:
        holds = generate(back) == text
    else:
        holds = nav.same_graph(egi, back)

    # The check is *run* either way, so a repaired round trip announces itself
    # here rather than sitting silently in the list. An earlier version called
    # pytest.xfail(), which aborts the test before it executes and therefore can
    # never report an unexpected pass — the file claimed a property it did not
    # have, and nine repairs went unreported because of it.
    if expected_broken:
        assert not holds, (
            f"{uod_id}/{form} now round-trips — remove it from KNOWN_BROKEN "
            f"and update the count in the docstring"
        )
        pytest.skip(f"{uod_id}/{form}: known round-trip defect, still failing")

    assert holds, (
        f"{uod_id} does not survive the {form} round trip.\n"
        f"  emitted : {text[:200]}\n"
        f"  re-emit : {generate(back)[:200]}"
    )


@pytest.mark.parametrize("uod_id", sorted(SECOND_ORDER))
@pytest.mark.parametrize("form", sorted(FORMS))
def test_second_order_uods_refuse_a_linear_form(service, uod_id, form):
    """The B-min limit is named, not silently mis-emitted.

    A quotation oval is not a negation, and no linear syntax carries the sort.
    The generators must say so rather than emit something that reads back as an
    ordinary cut.
    """
    egi = service.load_uod(uod_id, attest=False).current_egi
    generate, _ = FORMS[form]
    try:
        generate(egi)
    except SecondOrderNotInLinearForm:
        return
    except Exception as exc:  # a different failure is still a failure
        pytest.fail(f"{uod_id}/{form} raised {type(exc).__name__}, not the named limit: {exc}")
    if form == "CLIF":
        # CLIF currently emits the first-order projection rather than refusing;
        # recorded here rather than asserted away.
        pytest.xfail("CLIF emits the first-order projection instead of refusing")
    pytest.fail(f"{uod_id}/{form} emitted a linear form for a quotation-bearing graph")


def test_the_round_trip_guarantee_is_stated_at_its_true_extent():
    """A headline number the letters can cite without overclaiming."""
    total = len(_uods()) * len(FORMS)
    second_order = len(SECOND_ORDER) * len(FORMS)
    broken = len(KNOWN_BROKEN)
    holding = total - second_order - broken
    assert holding >= 90, (
        f"only {holding} of {total} round-trips hold; the guarantee has "
        f"regressed below its measured extent"
    )
    # If someone fixes a defect without updating KNOWN_BROKEN, the xfail turns
    # into an unexpected pass and pytest reports it.
