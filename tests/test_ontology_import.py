"""
Tests for the ontology import path: the declarative encoder
(``src/ontology_egif.py``) and the honest SUO-KIF translator
(``tools/suokif_to_eg.py``).  The corpus-level outcome (three ``kind=ontology``
UoDs) is pinned in ``test_corpus_conformance.py``.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

import eg_navigation as nav
from egif_parser_dau import parse_egif
from ontology_egif import OntologyEGIF, disjoint, instance, subsumes
from suokif_to_eg import translate, upper_taxonomy


# --------------------------------------------------------------------------- #
# Encoder                                                                     #
# --------------------------------------------------------------------------- #

def test_subsumes_is_a_scroll():
    g = parse_egif(subsumes("Dog", "Mammal"))
    # ~[ (Dog *x) ~[ (Mammal x) ] ] — one outer cut, an inner cut, two predicates,
    # one shared line of identity.
    assert len(g.Cut) == 2 and len(g.V) == 1
    rels = sorted(g.rel[e.id] for e in g.E)
    assert rels == ["Dog", "Mammal"]


def test_disjoint_is_a_single_negative_conjunction():
    g = parse_egif(disjoint("Dog", "Cat"))
    assert len(g.Cut) == 1 and len(g.V) == 1   # ~[ (Dog *x) (Cat x) ]


def test_instance_is_a_constant_assertion():
    g = parse_egif(instance("Rex", "Dog"))
    assert not g.Cut
    v = next(iter(g.V))
    assert v.label == "Rex" and not v.is_generic


def test_builder_assembles_and_round_trips():
    onto = (OntologyEGIF()
            .subsumes("Dog", "Mammal")
            .subsumes("Mammal", "Animal")
            .disjoint("Dog", "Cat")
            .instance("Rex", "Dog"))
    g = parse_egif(onto.egif())              # the whole theory parses + attests-shaped
    assert len(onto) == 4
    assert {"Dog", "Mammal", "Animal", "Cat"} <= onto.classes
    assert "Rex" in onto.individuals


def test_domain_typing_targets_the_right_argument():
    # arg 2 of the binary knows is typed Person → ~[ (knows *x *y) ~[ (Person y) ] ]
    g = parse_egif(OntologyEGIF().domain("knows", 2, 2, "Person").egif())
    knows = next(e.id for e in g.E if g.rel[e.id] == "knows")
    person = next(e.id for e in g.E if g.rel[e.id] == "Person")
    typed_vertex = g.nu[person][0]
    assert typed_vertex == g.nu[knows][1]    # the 2nd arg of knows is the typed one


def test_encoder_rejects_non_identifier_names():
    with pytest.raises(ValueError):
        subsumes("sub-class", "Thing")       # hyphen is not an EGIF identifier


# --------------------------------------------------------------------------- #
# SUO-KIF translator                                                          #
# --------------------------------------------------------------------------- #

_SAMPLE = """
;; a tiny SUO-KIF fragment
(documentation Entity "The root class.")
(subclass-of Physical Entity)
(subclass-of Abstract Entity)
(subclass-of Object Physical)
(disjoint Physical Abstract)
(instance-of Earth Object)
(<=> (subclass-of ?A ?B) (forall (?x) (=> (instance-of ?x ?A) (instance-of ?x ?B))))
(=> (instance-of ?x Object) (exists (?loc) (located ?x ?loc)))
"""


def test_translate_keeps_ground_facts_and_reports_the_rest():
    egif, report = translate(_SAMPLE)
    assert report["translated"] == {"subclass-of": 3, "disjoint": 1, "instance-of": 1}
    # documentation, the <=> definition (variables), and the => are NOT translated.
    assert report["skipped"]["documentation"] == 1
    assert report["skipped"]["=>"] == 1
    assert report["skipped"]["<=>"] == 1
    # the schematic subclass inside the <=> has variables → not a ground fact
    g = parse_egif(egif)
    assert any(g.rel[e.id] == "Physical" for e in g.E)


def test_translation_is_honest_about_omissions():
    _, report = translate(_SAMPLE)
    # nothing translated is also counted as skipped, and vice-versa — disjoint sets.
    assert set(report["translated"]) & set(report["skipped"]) == set()
    assert sum(report["skipped"].values()) >= 3   # documentation + <=> + =>


def test_upper_taxonomy_limits_by_depth():
    sample = """
    (subclass-of Physical Entity)
    (subclass-of Abstract Entity)
    (subclass-of Object Physical)
    (subclass-of Region Object)
    """
    _, _, kept = upper_taxonomy(sample, root="Entity", max_depth=1)
    classes = set(kept["classes"])
    assert {"Entity", "Physical", "Abstract"} <= classes
    assert "Object" not in classes and "Region" not in classes   # depth 2, 3 dropped


def test_full_sumo_file_translates_and_attests():
    """The bundled SUMO upper spine builds a real, §3.3-shaped EG theory."""
    text = (Path(__file__).parent.parent / "docs" / "references" / "SUMO1.2.txt"
            ).read_text(encoding="latin-1")
    egif, report, kept = upper_taxonomy(text)
    g = parse_egif(egif)
    assert len(kept["subsumptions"]) >= 20
    # the Peircean triad sits directly under Entity
    assert {"Independent", "Relative", "Mediating"} <= set(kept["classes"])
    assert report["translated"]["subclass-of"] >= 100   # full file, before the spine cut
