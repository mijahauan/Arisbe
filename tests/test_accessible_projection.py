"""
Tests for ``accessible_projection`` — the non-visual, screen-reader-native
projection of an EGI (R4).

The projection is a *pure function of the EGI + its natural layout*, so it *is*
the ground truth (there is no drawing in between, hence no §3.3 obligation).
What earns the "faithful" claim, asserted here:

- **totality / injectivity** — every vertex, edge, and cut of the EGI appears in
  the accessible tree exactly once (the accessibility analogue of §7's totality
  shape), corpus-wide;
- **crossing fidelity** — each narrated incidence's required crossings equal
  ``natural_layout(egi)``'s crossing-sequence for that (predicate, vertex, port);
- **dimension-free discipline** — the module imports no geometry (mirrors
  ``test_natural_layout``), so a future non-2-D reading stays additive;
- a handful of **hand-checked readings** (alpha / beta / scroll / named /
  isolated / empty cut), plus a falsifier so the pass is earned.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from egif_parser_dau import parse_egif
from natural_layout import natural_layout
from tomos_service import TomosService
from accessible_projection import (
    accessible_projection,
    projection_to_dict,
    reading_lines,
    spoken_reading,
)


# --------------------------------------------------------------------------- #
# Corpus — the real tomos UoDs (loaded as the route does, structure only)      #
# --------------------------------------------------------------------------- #

TOMOS_DIR = Path(__file__).parent.parent / "tomos"


def _corpus_egis():
    """Every tomos UoD's current EGI, loaded structure-only (attest=False), as
    the ``/accessible`` route loads it. A UoD that fails to load is skipped."""
    out = []
    svc = TomosService(TOMOS_DIR)
    for entry in svc.list_uods():
        uid = entry["uod_id"]
        try:
            uod = svc.load_uod(uid, attest=False)
            egi = uod.current_egi if uod else None
        except Exception:
            egi = None
        if egi is None:
            continue
        out.append(pytest.param(egi, id=uid))
    return out


CORPUS = _corpus_egis()


# --------------------------------------------------------------------------- #
# Totality / injectivity — every element appears exactly once                  #
# --------------------------------------------------------------------------- #

def _collect_ids(proj):
    """(area_ids, vertex_ids, edge_ids) collected from the tree, with counts so
    injectivity (exactly once) is checkable, not just presence."""
    areas, verts, edges = [], [], []

    def walk(area):
        areas.append(area.area_id)
        for ln in area.lines:
            verts.append(ln.vertex_id)
        for pr in area.predicates:
            edges.append(pr.edge_id)
        for c in area.cuts:
            walk(c)

    walk(proj.sheet)
    return areas, verts, edges


@pytest.mark.parametrize("egi", CORPUS)
def test_totality_and_injectivity(egi):
    proj = accessible_projection(egi)
    areas, verts, edges = _collect_ids(proj)

    expect_areas = {egi.sheet} | {c.id for c in egi.Cut}
    expect_verts = {v.id for v in egi.V}
    expect_edges = {e.id for e in egi.E}

    # Totality: the exact element sets, nothing missing, nothing invented.
    assert set(areas) == expect_areas
    assert set(verts) == expect_verts
    assert set(edges) == expect_edges

    # Injectivity: each element appears exactly once.
    assert len(areas) == len(expect_areas)
    assert len(verts) == len(expect_verts)
    assert len(edges) == len(expect_edges)


@pytest.mark.parametrize("egi", CORPUS)
def test_crossing_fidelity(egi):
    """Every narrated incidence's crossings equal the natural layout's — the
    spoken crossings and the drawn ones are the same object."""
    proj = accessible_projection(egi)
    nl = natural_layout(egi)
    required = {
        (lig.predicate_id, lig.vertex_id, lig.port_index): lig.required_crossings
        for lig in nl.ligatures
    }

    def walk(area):
        for pr in area.predicates:
            for arg in pr.arguments:
                key = (pr.edge_id, arg.vertex_id, arg.port - 1)
                assert key in required, f"incidence {key} absent from natural layout"
                assert arg.crossings == required[key]
        for c in area.cuts:
            walk(c)

    walk(proj.sheet)


@pytest.mark.parametrize("egi", CORPUS)
def test_reading_lines_cover_the_tree(egi):
    """The flat reading order lists one line per area, line, and predicate — the
    same nodes the tree presents (a screen reader misses nothing)."""
    proj = accessible_projection(egi)
    areas, verts, edges = _collect_ids(proj)
    lines = reading_lines(proj)
    # One heading line per area + per line-of-identity + per predicate (argument
    # detail lines are extra, only for crossing incidences).
    assert len(lines) >= len(areas) + len(verts) + len(edges)
    assert lines[0].strip() == "Sheet of assertion"


# --------------------------------------------------------------------------- #
# Hand-checked readings                                                        #
# --------------------------------------------------------------------------- #

def test_alpha_scroll_reading():
    egi = parse_egif("~[ (man *x) ~[ (mortal x) ] ]")
    reading = spoken_reading(egi)
    assert reading == (
        "The sheet asserts: it is not the case that: there is something, x; "
        "man holds of x; it is not the case that: mortal holds of x."
    )


def test_conjunction_reading():
    """Two existentials and a faithful argument order. The bound-variable
    *letters* are arbitrary; what must hold is that ``on`` relates the cat's
    line to the mat's line in that order."""
    import re
    egi = parse_egif("(cat *x) (mat *y) (on x y)")
    reading = spoken_reading(egi)
    assert reading.count("there is something,") == 2
    catv = re.search(r"cat holds of (\w+)", reading).group(1)
    matv = re.search(r"mat holds of (\w+)", reading).group(1)
    assert catv != matv
    assert f"on relates {catv} to {matv}" in reading


def test_named_individual_reading():
    egi = parse_egif('(loves "Socrates" "Plato")')
    reading = spoken_reading(egi)
    assert reading == 'The sheet asserts: loves relates "Socrates" to "Plato".'


def test_empty_cut_reading():
    egi = parse_egif("~[ ]")
    reading = spoken_reading(egi)
    assert reading == "The sheet asserts: it is not the case that: nothing."


def test_isolated_vertex_reading():
    egi = parse_egif("[*x]")
    reading = spoken_reading(egi)
    assert reading == "The sheet asserts: there is something, x."


def test_double_cut_polarity_words():
    """A cut's interior stance follows canonical polarity: the outer cut is a
    denial, the inner (double-cut) interior is asserted."""
    egi = parse_egif("~[ ~[ (P *x) ] ]")
    proj = accessible_projection(egi)
    outer = proj.sheet.cuts[0]
    inner = outer.cuts[0]
    assert outer.stance == "denied" and outer.depth == 1
    assert inner.stance == "asserted" and inner.depth == 2
    assert "denied" in outer.heading
    assert "asserted" in inner.heading


def test_reading_is_deterministic():
    """Names/order must not depend on set-iteration (hash-seed) order — two
    projections of the same source read identically."""
    egif = "~[ (man *x) ~[ (mortal x) ] ] (cat *y) (dog *z)"
    r1 = spoken_reading(parse_egif(egif))
    r2 = spoken_reading(parse_egif(egif))
    assert r1 == r2


def test_falsifier_a_doctored_expectation_fails():
    """Guard against a vacuous pass: a wrong expected reading does not match."""
    egi = parse_egif("(man *x)")
    reading = spoken_reading(egi)
    assert reading != "The sheet asserts: it is not the case that: man holds of x."


# --------------------------------------------------------------------------- #
# Serialization + dimension-free discipline                                    #
# --------------------------------------------------------------------------- #

def test_projection_to_dict_shape():
    egi = parse_egif("~[ (man *x) ~[ (mortal x) ] ]")
    d = projection_to_dict(accessible_projection(egi))
    assert set(d.keys()) == {"tree", "reading", "reading_lines"}
    assert d["tree"]["kind"] == "sheet"
    # The tree is JSON-serializable (no dataclasses / tuples-as-keys leak).
    import json
    json.dumps(d)


def test_module_imports_no_geometry():
    """The projection reads the coordinate-free layer only — no geometry — so a
    non-2-D reading (spoken, braille, 3-D audio) stays additive. Mirrors
    ``test_natural_layout``'s dimension-free guard."""
    src = (Path(__file__).parent.parent / "src" / "accessible_projection.py").read_text()
    body = src.split('"""', 2)[-1]     # strip the module docstring (prose mentions these)
    assert "import layout_dto" not in body
    assert "from layout_dto" not in body
    assert "BoundingBox" not in body
    assert "Point" not in body
    for projection_module in (
        "elk_layout_engine", "simple_svg_renderer",
        "projection_conventions", "layout_service",
    ):
        assert projection_module not in body
