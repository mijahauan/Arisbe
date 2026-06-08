"""
Unit tests for the derived UI/join moves (``src/derived_rules.py``) — the R7
layer that turns Sowa's "insert a connection between two nodes identifies them"
(Fig. 14) / Dau §16.6 into named, reusable moves.

``universal_instantiation`` (the reuse / iterate-and-join variant) is exercised
end-to-end by Barbara in ``test_fixture_chains.py``.  Here we pin the *consuming,
multi-line* variant ``instantiate_to_lines`` directly: a single line to a sheet
constant, and — the new capability — four lines to two constants in one move.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eg_navigation as nav
from derived_rules import instantiate_to_lines
from egi_core_dau import AreaPolarity, Edge
from egif_parser_dau import parse_egif
from proof_authoring import apply_rule


def _sheet_cuts(g):
    return [c.id for c in g.Cut if nav.area_of(g, c.id) == g.sheet]


def test_single_line_instantiation_to_a_sheet_constant():
    """``~[ [*y] ~[ (M e y y) ] ]`` with e,f on the sheet: instantiate y := f →
    ``~[ ~[ (M e f f) ] ]``, and DC- lands (M e f f) on the sheet."""
    g = parse_egif("[*e] [*f] ~[ [*y] ~[ (M e y y) ] ]")
    cut = _sheet_cuts(g)[0]
    m = nav.child_edges(g, nav.child_cuts(g, cut)[0], "M")[0]
    e_id, y_id = g.nu[m][0], g.nu[m][1]
    f_id = next(v.id for v in g.V if nav.area_of(g, v.id) == g.sheet and v.id != e_id)

    g = instantiate_to_lines(g, universal_cut=cut, joins=[(y_id, f_id)])
    # The quantifier is spent; what remains is a double cut over the instance.
    g = apply_rule("DC-", g, selection=[cut])

    sheet_ms = [e.id for e in g.E if g.rel.get(e.id) == "M" and nav.area_of(g, e.id) == g.sheet]
    assert len(sheet_ms) == 1
    assert g.nu[sheet_ms[0]] == (e_id, f_id, f_id)   # M(e, f, f)
    assert not g.Cut


def test_multi_line_instantiation_joins_four_lines_at_once():
    """A functionality axiom ``~[ [*p][*q][*r][*s] (M p q r)(M p q s) ~[ =(r,s) ] ]``
    instantiated x,y,z,w := e,f,f,e in ONE move → ``~[ (M e f f)(M e f e) ~[ =(e,f) ] ]``."""
    g = parse_egif(
        "[*e] [*f] ~[ [*p][*q][*r][*s] (M p q r) (M p q s) ~[ ] ]"
    )
    cut = _sheet_cuts(g)[0]
    ms = nav.child_edges(g, cut, "M")
    p, q, r, s = g.nu[ms[0]][0], g.nu[ms[0]][1], g.nu[ms[0]][2], g.nu[ms[1]][2]
    inner = nav.child_cuts(g, cut)[0]
    g = g.with_edge(Edge(id="eq"), (r, s), "=", inner)
    e_id = next(v.id for v in g.V if nav.area_of(g, v.id) == g.sheet)
    f_id = next(v.id for v in g.V if nav.area_of(g, v.id) == g.sheet and v.id != e_id)

    g = instantiate_to_lines(
        g, universal_cut=cut, joins=[(p, e_id), (q, f_id), (r, f_id), (s, e_id)]
    )

    # The four declared lines are gone; only the two constants survive.
    assert {v.id for v in g.V} == {e_id, f_id}
    # Both M edges read M(e, f, f) and M(e, f, e).
    m_nus = sorted(g.nu[e.id] for e in g.E if g.rel.get(e.id) == "M")
    assert m_nus == sorted([(e_id, f_id, f_id), (e_id, f_id, e_id)])
    # The consequent equality joins e and f (unordered).
    eq = next(e.id for e in g.E if g.rel.get(e.id) == "=")
    assert set(g.nu[eq]) == {e_id, f_id}


def test_instantiation_refuses_a_positive_area():
    """Inserting an identity edge in a *positive* area would be unsound — the move
    must refuse rather than silently assert something unproven."""
    g = parse_egif("[*a] ~[ ~[ [*y] (R y) ] ] ")
    # The depth-2 inner cut is positive (even).
    outer = _sheet_cuts(g)[0]
    inner = nav.child_cuts(g, outer)[0]
    assert nav.polarity_of(g, inner)[0] is AreaPolarity.POSITIVE
    y = nav.child_vertices(g, inner)[0]
    a = next(v.id for v in g.V if nav.area_of(g, v.id) == g.sheet)
    with pytest.raises(ValueError, match="negative"):
        instantiate_to_lines(g, universal_cut=inner, joins=[(y, a)])
