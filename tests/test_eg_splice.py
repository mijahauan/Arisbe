"""The graph splice — the shared primitive under the definition layer and the
graph-with-holes node (``src/eg_splice.py``).

The keystone property: splicing a definition *body* in for its placeholder edge
yields exactly the hand-written inline form (full-isomorphism equal), with the
filler's own bound lines α-renamed so they can never fuse onto host lines.
"""

import pytest

from eg_splice import splice
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from eg_navigation import same_graph


def port(graph, name):
    """The id of the body vertex carrying EGIF variable ``name`` (its port)."""
    for vid, vname in graph.variable_names.items():
        if vname == name:
            return vid
    raise AssertionError(f"no vertex named {name!r} in body")


def edge_named(graph, relation):
    for eid, rel in graph.rel.items():
        if rel == relation:
            return eid
    raise AssertionError(f"no edge with relation {relation!r}")


def counts(graph):
    return (len(graph.V), len(graph.E), len(graph.Cut))


# The running example: `subset` inlined as ~[ [*w] (in w z) ~[ (in w x) ] ].
SUBSET_BODY = "[*z] [*x] ~[ [*w] (in w z) ~[ (in w x) ] ]"


def test_splice_equals_handwritten_inline_form():
    """The keystone: expand `(subset z x)` and get the hand-written inline form."""
    host = parse_egif("[*z] [*x] (subset z x)")
    body = parse_egif(SUBSET_BODY)
    placeholder = edge_named(host, "subset")

    result = splice(host, placeholder, body, ports=[port(body, "z"), port(body, "x")])

    # placeholder gone
    assert "subset" not in set(result.rel.values())
    # and the result IS the inlined subset, up to isomorphism
    expected = parse_egif(SUBSET_BODY)
    assert same_graph(result, expected)


def test_spliced_result_round_trips():
    host = parse_egif("[*z] [*x] (subset z x)")
    body = parse_egif(SUBSET_BODY)
    placeholder = edge_named(host, "subset")
    result = splice(host, placeholder, body, ports=[port(body, "z"), port(body, "x")])

    reparsed = parse_egif(generate_egif(result))
    assert counts(reparsed) == counts(result)
    assert same_graph(reparsed, result)


def test_splice_into_a_cut_preserves_nesting():
    """A placeholder inside a cut lands the body inside that cut."""
    host = parse_egif("~[ [*z] [*x] (subset z x) ]")
    body = parse_egif(SUBSET_BODY)
    placeholder = edge_named(host, "subset")
    result = splice(host, placeholder, body, ports=[port(body, "z"), port(body, "x")])

    expected = parse_egif("~[ [*z] [*x] ~[ [*w] (in w z) ~[ (in w x) ] ] ]")
    assert same_graph(result, expected)


def test_filler_bound_lines_are_alpha_renamed_not_fused():
    """A host line sharing the body's bound-label name must NOT fuse with it."""
    host = parse_egif("[*w] [*z] [*x] (subset z x)")  # host has its own, unrelated w
    body = parse_egif(SUBSET_BODY)
    placeholder = edge_named(host, "subset")
    result = splice(host, placeholder, body, ports=[port(body, "z"), port(body, "x")])

    # host w + z + x + body's (renamed) w  ->  four distinct vertices
    assert len(result.V) == 4
    expected = parse_egif("[*w] [*z] [*x] ~[ [*q] (in q z) ~[ (in q x) ] ]")
    assert same_graph(result, expected)


def test_arity_mismatch_raises():
    host = parse_egif("[*z] [*x] (subset z x)")
    body = parse_egif(SUBSET_BODY)
    placeholder = edge_named(host, "subset")
    with pytest.raises(ValueError, match="Arity mismatch"):
        splice(host, placeholder, body, ports=[port(body, "z")])  # only one port


def test_unknown_placeholder_raises():
    host = parse_egif("[*z] [*x] (subset z x)")
    body = parse_egif(SUBSET_BODY)
    with pytest.raises(ValueError, match="not in host"):
        splice(host, "e_nope", body, ports=[port(body, "z"), port(body, "x")])
