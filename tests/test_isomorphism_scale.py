"""The isomorphism oracle must answer on graphs the corpus actually contains.

``same_graph`` is the correctness authority for challenge grading, drawing→EGI,
IT- validation, goal detection and the linear-form round-trip acceptance test.
It was unusable at ontology scale: ``VF2``'s node matcher distinguished cuts
only by ``quoted`` and generic vertices only by label and sort, so in
``bfo_core`` all 50 cuts were mutually interchangeable and all 24 generic
vertices likewise. VF2 then searched a factorial space pruned only by edge
structure as it descended.

The symptom was not a wrong answer but no answer: ``same_graph(bfo_core,
bfo_core)`` — the oracle against *itself*, the cheapest possible case — did not
return within 600 seconds, and ``sumo_upper`` never finished at all. Nothing
caught it, because the corpus round-trip test sampled the first 14 UoDs in
index order and the large ontologies were not among them.

The fix attaches the Weisfeiler-Leman colours that ``canonical_signature``
already computes for the generators, and requires them to match. Colour
equality is an isomorphism invariant, so it prunes only what could never match.
"""

import time
from pathlib import Path

import pytest

from eg_navigation import same_graph
from egif_parser_dau import parse_egif
from tomos_service import TomosService

TOMOS = Path(__file__).resolve().parent.parent / "tomos"

# The largest graphs in the corpus, and the ones that hung.
LARGE = ["bfo_core", "sumo_upper", "colore_field"]

# Generous next to the ~0.03-0.08s now observed, but far below the old
# behaviour, which was unbounded. This is a "does it terminate" guard, not a
# benchmark.
BUDGET_S = 20.0


@pytest.fixture(scope="module")
def service():
    return TomosService(TOMOS)


@pytest.mark.parametrize("uod_id", LARGE)
def test_the_oracle_answers_on_large_graphs(service, uod_id):
    """Reflexivity, within a time budget. This used to hang."""
    egi = service.load_uod(uod_id, attest=False).current_egi
    start = time.time()
    result = same_graph(egi, egi)
    elapsed = time.time() - start
    assert result is True, f"{uod_id} is not isomorphic to itself"
    assert elapsed < BUDGET_S, (
        f"same_graph({uod_id}, itself) took {elapsed:.1f}s — the VF2 pruning "
        f"invariant has regressed; without it this does not terminate"
    )


# Pairs the oracle must still judge correctly. Pruning that changed any of
# these would be pruning away real answers.
DISCRIMINATION = [
    ("identical",          '~[ (P *x) ~[ (Q x) ] ]',  '~[ (P *x) ~[ (Q x) ] ]',  True),
    ("relabelled line",    '~[ (P *x) ~[ (Q x) ] ]',  '~[ (P *y) ~[ (Q y) ] ]',  True),
    ("argument order",     '(loves *a *b)',            '(loves *b *a)',           True),
    ("different relation", '(P *x)',                   '(R *x)',                  False),
    ("different nesting",  '~[ (P *x) ~[ (Q x) ] ]',  '~[ (P *x) (Q x) ]',       False),
    ("constant vs generic",'(P "a")',                  '(P *a)',                  False),
    ("extra cut",          '~[ (P *x) ]',              '~[ ~[ (P *x) ] ]',        False),
    ("one line vs two",    '~[ (P *x) ~[ (Q x) ] ]',  '~[ (P *x) ~[ (Q *y) ] ]', False),
]


@pytest.mark.parametrize("name,left,right,expected", DISCRIMINATION)
def test_pruning_changes_no_verdict(name, left, right, expected):
    """The invariant must not cost the oracle any discrimination."""
    assert same_graph(parse_egif(left), parse_egif(right)) is expected, (
        f"{name}: expected same_graph to be {expected}"
    )


def test_corpus_graphs_are_isomorphic_to_themselves(service):
    """Reflexivity across the whole corpus — the floor under every other use."""
    failures = []
    for entry in service.list_uods():
        egi = service.load_uod(entry["uod_id"], attest=False).current_egi
        if not same_graph(egi, egi):
            failures.append(entry["uod_id"])
    assert not failures, f"not isomorphic to themselves: {failures}"


def test_subgraph_embedding_is_not_pruned_by_colour():
    """A pattern must still embed into a host — the colour must not apply here.

    This is the mistake the first version of the fix made. A colour summarises
    an element's place in its *whole* graph, so the same relation sitting in a
    small pattern and in a large host carries different colours. Requiring
    equality there rejects true embeddings, and IT- deiteration is exactly that
    search: find the copy already accounted for. The first attempt coloured
    every build unconditionally and broke 57 tests, none of them in this file,
    because whole-graph comparison — all this file tested — kept working.

    Colouring is now decided at the comparison site and applied only when both
    sides cover their whole graph.
    """
    from egif_parser_dau import parse_egif
    from graph_isomorphism_engine import GraphIsomorphismEngine

    # (Q x) inside a cut, with a copy outside it: the classic IT- shape.
    egi = parse_egif('~[ (P *x) (Q x) ~[ (Q x) ] ]')
    engine = GraphIsomorphismEngine()

    inner_cut = None
    for cut in egi.Cut:
        contents = egi.area.get(cut.id, frozenset())
        rels = {egi.rel.get(c) for c in contents}
        if rels == {"Q"}:
            inner_cut = cut.id
    assert inner_cut is not None, "fixture does not have the expected shape"

    # The copy sits in the cut that *encloses* the inner one, not on the sheet.
    host = next(c.id for c in egi.Cut if inner_cut in egi.area.get(c.id, frozenset()))
    target = frozenset(egi.area[inner_cut])
    matches = engine.find_isomorphic_subgraphs(egi, target, [host])
    assert matches, (
        "the inner (Q x) should embed into its enclosing area, where a copy "
        "stands — an empty result means the WL colour is being applied to a "
        "subgraph embedding again"
    )
