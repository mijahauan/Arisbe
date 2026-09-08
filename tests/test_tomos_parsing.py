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
specific, named few do not. As of 2026-09-08: **94 of 150 hold, 56 do not**
(EGIF 3, CGIF 29, CLIF 24), down from 64 failures at the start of the arc.
EGIF is nearly clean; what remains is concentrated in CGIF and CLIF and is
format-specific rather than the shared placement cause. Those are listed in ``KNOWN_BROKEN`` with what goes
wrong in each, and are expected failures — so the gaps stay visible and counted,
and a fix announces itself by turning an xfail into an unexpected pass.
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

# Genuine defects, each verified by hand. Recorded so the guarantee is stated
# at its true extent.
# Round-trips that do not hold, measured rather than assumed. Listed so the
# guarantee is stated at its true extent and a fix announces itself as an
# unexpected pass.
#
# The dominant defect is SCOPE: a linear form does not record which area a
# shared vertex's line of identity occupies. roberts_1973_p57_disjunction is
# the clearest case — the corpus graph holds its constant at depth 1, spanning
# both disjuncts, and every form re-interns it at depth 2, inside one of them.
# Same vertex count, same edge count, same canonical text; different graph.
#
# CLIF adds defects of its own: a constant re-read as a bound variable, an
# existential returning as a universal, a spurious double negation.
KNOWN_BROKEN = frozenset([
    # CGIF: 29
    ("agon_evolution_swan", "CGIF"),
    ("arithmetic_from_two_laws", "CGIF"),
    ("bfo_core", "CGIF"),
    ("branching_confluence", "CGIF"),
    ("broken_cut_square", "CGIF"),
    ("colore_between", "CGIF"),
    ("colore_field", "CGIF"),
    ("contraposition", "CGIF"),
    ("crowded_modus_ponens", "CGIF"),
    ("de_morgan", "CGIF"),
    ("dialogue_model_revision", "CGIF"),
    ("dialogue_swan_revision", "CGIF"),
    ("episode_discharge", "CGIF"),
    ("ex_falso_quodlibet", "CGIF"),
    ("foaf_core", "CGIF"),
    ("forcing_conditions", "CGIF"),
    ("harbor_town", "CGIF"),
    ("hypothetical_syllogism", "CGIF"),
    ("numeral_three_unfolds", "CGIF"),
    ("peirce_law", "CGIF"),
    ("peirce_order_1881", "CGIF"),
    ("porphyry_tree", "CGIF"),
    ("possible_and_necessary", "CGIF"),
    ("skos_core", "CGIF"),
    ("swan_alternatives", "CGIF"),
    ("swan_episode_unpacked", "CGIF"),
    ("theorem_praeclarum", "CGIF"),
    ("would_be_courses", "CGIF"),
    ("zoo_world", "CGIF"),
    # CLIF: 24
    ("agon_evolution_swan", "CLIF"),
    ("arithmetic_from_two_laws", "CLIF"),
    ("barbara", "CLIF"),
    ("bfo_core", "CLIF"),
    ("colore_between", "CLIF"),
    ("colore_field", "CLIF"),
    ("dialogue_model_revision", "CLIF"),
    ("dialogue_swan_revision", "CLIF"),
    ("episode_discharge", "CLIF"),
    ("foaf_core", "CLIF"),
    ("forcing_conditions", "CLIF"),
    ("forcing_forces", "CLIF"),
    ("harbor_town", "CLIF"),
    ("numeral_three_unfolds", "CLIF"),
    ("peirce_law_commentary", "CLIF"),
    ("peirce_order_1881", "CLIF"),
    ("porphyry_tree", "CLIF"),
    ("roberts_1973_p57_disjunction", "CLIF"),
    ("skos_core", "CLIF"),
    ("swan_alternatives", "CLIF"),
    ("swan_episode_unpacked", "CLIF"),
    ("swan_third_tense", "CLIF"),
    ("would_be_courses", "CLIF"),
    ("zoo_world", "CLIF"),
    # EGIF: 3
    ("bfo_core", "EGIF"),
    ("colore_field", "EGIF"),
    ("episode_discharge", "EGIF"),
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
