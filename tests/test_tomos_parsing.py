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

The result is now total, and the "how" matters as much as the count: as of
2026-09-13, of 147 round trips checked, **144 hold by ``same_graph`` and 3 hold
by stable re-emission** — up from 83 holding at the start of the arc. The three
are ``sumo_upper``'s (one per format), listed in ``BY_REEMISSION`` below: on
that ontology the isomorphism search does not finish in reasonable time, so the
check is ``generate(parse(generate(g))) == generate(g)`` instead. That is
strictly weaker. It says the text survives a second pass, which a defect that
both the generator and the parser share — or one that loses information the
generator never emits — would also survive; it does not say the graph that came
back is the graph that went out. Any statement of this guarantee should carry
the split, not the total alone.

The last six failures were two graphs failing in all three formats, and that
symmetry was the finding: no linear form had a defect left, and what remained
sat upstream of all of them. ``bfo_core`` and
``colore_field`` were stored with a generic vertex placed in one cut while
edges in *sibling* cuts used it, so neither graph dominated its own edges
(Dau Def 12.5, p.125) and neither was an EGI. Generating and re-parsing
*repaired* them — which is exactly why the graph that came back was not the
graph that went out. They were repaired in place by
``tools/repair_non_egi_corpus_graphs.py``.

``KNOWN_BROKEN`` is empty, and the machinery around it is kept: the check is
run for anything listed there, so a stale entry fails with "now round-trips"
rather than sitting silently in the list.
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
# unexpected pass. Nothing is listed: every round trip in the corpus holds.
#
# Two families were retired from here rather than excused.
#
# episode_discharge's graph carried two lines of identity for "Rex" — INS
# scribes fresh ink, so a fact discharged into M arrives with its own line for
# an individual M already stands on. Two lines say exactly what one says, but
# no linear form can write the difference down. The representative is now
# chosen where M's content is constructed (world_scroll.discharge_episode),
# the corpus boundary refuses anything else, and the exemplar was rebuilt.
#
# bfo_core and colore_field were not linear-form failures at all: each stored a
# generic vertex in one cut while edges in sibling cuts used it, so the graph
# did not dominate its own edges (Dau Def 12.5, p.125) and was never an EGI.
# The round trip *repaired* them, which is why what came back differed. The
# stored graphs were repaired in place — each such vertex hoisted to the least
# common area of its uses, the reading every parser already applies — by
# tools/repair_non_egi_corpus_graphs.py, and their six round trips then held.
KNOWN_BROKEN = frozenset()


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

    All three forms are held to this, with no exemption. There used to be one:
    a ``pytest.xfail("CLIF emits the first-order projection instead of
    refusing")`` on the CLIF leg, added 2026-09-08. CLIF had gained the refusal
    on 2026-07-16 (``caa5f45``, the B-min opening), so the exemption was stale
    the day it was written and never once fired — and because ``pytest.xfail()``
    aborts the test where it stands, it could never report an unexpected pass to
    say so. It sat in the very file whose docstring warns about that archetype.
    Its only remaining effect would have been to absorb a future CLIF regression
    back into silence, so it is gone rather than "recorded".
    """
    egi = service.load_uod(uod_id, attest=False).current_egi
    generate, _ = FORMS[form]
    try:
        generate(egi)
    except SecondOrderNotInLinearForm:
        return
    except Exception as exc:  # a different failure is still a failure
        pytest.fail(f"{uod_id}/{form} raised {type(exc).__name__}, not the named limit: {exc}")
    pytest.fail(f"{uod_id}/{form} emitted a linear form for a quotation-bearing graph")


def test_the_round_trip_guarantee_is_stated_at_its_true_extent():
    """A headline number the letters can cite without overclaiming."""
    total = len(_uods()) * len(FORMS)
    second_order = len(SECOND_ORDER) * len(FORMS)
    broken = len(KNOWN_BROKEN)
    holding = total - second_order - broken
    # Pinned exactly, never floored: a floor of 90 against a measured 141 let
    # 51 regressions land unseen. A moved count is read, then re-pinned. The
    # last move, 141 -> 147, was earned: the six were the two graphs that were
    # not EGIs (Def 12.5, p.125), and repairing the stored graphs is what made
    # their round trips hold — no check here was weakened to reach it.
    assert (total, second_order, broken, holding) == (156, 9, 0, 147), (
        f"the round-trip extent moved: {total} checks, {second_order} refused as "
        f"second-order, {broken} known broken, {holding} holding — update this pin "
        f"and the module docstring deliberately"
    )


def test_the_split_between_the_strong_and_weak_checks_is_pinned_too():
    """147 is not one number. Pin *how* each of the 147 holds, not just that it does.

    The headline above cannot see the difference between the two checks this
    file runs. ``same_graph`` is isomorphism in Dau's sense: the graph that came
    back is the graph that went out. Re-emission —
    ``generate(parse(generate(g))) == generate(g)`` — compares two outputs of
    the same generator and never re-touches the original EGI, so it is blind to
    exactly the defect class the eighteenth arc repaired (one the generator and
    the parser share, or one that loses what the generator never emits).

    Until this test existed, moving a UoD into ``BY_REEMISSION`` downgraded it
    from the strong check to the weak one **with every pin still green**: the
    tuple above counts a re-emission pass into ``holding`` indistinguishably,
    so the headline stayed 147 while the split slid from 144/3. The project has
    already been bitten once by re-emission counted into a ``same_graph`` total;
    the escape hatch that does it was the one quantity left unmeasured.

    So the weak set is pinned by *name*, not only by size — a swap of equal size
    would otherwise pass — and the split is pinned alongside the total.
    """
    assert BY_REEMISSION == {"sumo_upper"}, (
        f"the set checked by the weaker re-emission test moved: {sorted(BY_REEMISSION)}. "
        f"Adding a UoD here silently downgrades its guarantee — do it deliberately, "
        f"say why in the docstring, and re-pin the split below."
    )

    total = len(_uods()) * len(FORMS)
    second_order = len(SECOND_ORDER) * len(FORMS)
    broken = len(KNOWN_BROKEN)
    holding = total - second_order - broken
    by_reemission = len(BY_REEMISSION & set(_uods())) * len(FORMS)
    by_same_graph = holding - by_reemission

    assert (by_same_graph, by_reemission) == (144, 3), (
        f"the round-trip SPLIT moved: {by_same_graph} hold by same_graph and "
        f"{by_reemission} by stable re-emission (total still {holding}). Always "
        f"state the split, never the total alone."
    )
