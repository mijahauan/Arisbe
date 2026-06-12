"""
RDF → OWL → CLIF → EGI import pipeline (``tools/rdf_to_owl`` + ``domain_model_importer``).

The second OWL front-end: real ontologies ship as RDF serializations (Turtle, RDF/XML,
…), which rdflib parses; ``rdf_to_owl`` reconstructs the OWL axioms as the same forms the
functional-syntax translator consumes, so the whole EG-expressible fragment is reused.
Verifies the RDF patterns (subsumption, ∀R.D→Horn restriction, union/complement/hasValue,
intersection lists, disjointness, property axioms, the A-box) translate, that an
untranslatable construct is reported (the manifest floor), and — closing the loop — that
an RDF-imported ontology is a real model M the theory query reasons over.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

pytest.importorskip("rdflib")

from rdf_to_owl import rdf_to_clif, rdf_to_egi
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from theory_query import entails
from model_materialization import materialize_egi

FIXTURE_TTL = ROOT / "tests" / "fixtures" / "zoo.ttl"

PREFIX = """
@prefix :     <http://ex.org/o#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
"""


def _clif(body: str) -> str:
    clif, _ = rdf_to_clif(PREFIX + body, "turtle")
    return clif


def _report(body: str):
    _, rep = rdf_to_clif(PREFIX + body, "turtle")
    return rep


# --------------------------------------------------------------------------- #
# RDF patterns → the right Common-Logic shape                                  #
# --------------------------------------------------------------------------- #


def test_subclass_chain():
    clif = _clif(":Dog rdfs:subClassOf :Mammal . :Mammal rdfs:subClassOf :Animal .")
    assert "(if (Dog x" in clif and "(Mammal x" in clif
    assert "(if (Mammal x" in clif and "(Animal x" in clif


def test_restriction_all_values_becomes_horn_rule():
    clif = _clif(
        ":Dog rdfs:subClassOf "
        "[ a owl:Restriction ; owl:onProperty :hasParent ; owl:allValuesFrom :Dog ] .")
    # ∀R.D in superclass → the flat prenexed Horn rule
    assert "(and (Dog x" in clif and "(hasParent x" in clif


def test_restriction_some_values():
    clif = _clif(
        ":Pet rdfs:subClassOf "
        "[ a owl:Restriction ; owl:onProperty :hasOwner ; owl:someValuesFrom :Person ] .")
    assert "(exists" in clif and "(hasOwner x" in clif and "(Person w" in clif


def test_restriction_has_value():
    clif = _clif(
        ":Dog rdfs:subClassOf "
        "[ a owl:Restriction ; owl:onProperty :hasOwner ; owl:hasValue :Alice ] .")
    assert "(hasOwner x1 Alice)" in clif


def test_restriction_min_cardinality_one_is_existential():
    clif = _clif(
        ":Dog rdfs:subClassOf "
        "[ a owl:Restriction ; owl:onProperty :hasParent ; owl:minCardinality 1 ] .")
    assert "(exists" in clif and "(hasParent x" in clif


def test_intersection_list():
    clif = _clif(
        ":Father owl:equivalentClass "
        "[ a owl:Class ; owl:intersectionOf ( :Male :Parent ) ] .")
    assert "(iff (Father x1) (and (Male x1) (Parent x1)))" in clif


def test_union_list():
    clif = _clif(
        ":Quadruped rdfs:subClassOf [ a owl:Class ; owl:unionOf ( :Dog :Cat ) ] .")
    assert "(or (Dog x1) (Cat x1))" in clif


def test_complement_in_superclass():
    clif = _clif(":Bachelor rdfs:subClassOf [ a owl:Class ; owl:complementOf :Married ] .")
    assert "(not (Married x1))" in clif


def test_disjoint_and_property_axioms():
    clif = _clif(
        ":Cat owl:disjointWith :Dog . "
        ":hasParent owl:inverseOf :hasChild . "
        ":hasParent rdfs:domain :Animal . "
        ":hasAncestor a owl:TransitiveProperty . "
        ":siblingOf a owl:SymmetricProperty .")
    assert "(not (and " in clif                       # disjointness denial
    assert "(hasChild" in clif                         # inverse, both directions
    assert "(if (hasParent x" in clif and "(Animal x" in clif   # domain
    assert clif.count("(hasAncestor") >= 3             # transitivity rule
    assert "(if (siblingOf" in clif                    # symmetry


def test_abox_assertions_even_when_property_undeclared():
    # :hasParent is never typed owl:ObjectProperty here — the object-property assertion is
    # still recovered structurally.
    clif = _clif(":Rex a :Dog . :Rex :hasParent :Fido .")
    assert "(Dog Rex)" in clif
    assert "(hasParent Rex Fido)" in clif


# --------------------------------------------------------------------------- #
# The honest floor — an untranslatable construct is reported                   #
# --------------------------------------------------------------------------- #


def test_max_cardinality_is_reported_not_dropped():
    rep = _report(
        ":Dog rdfs:subClassOf "
        "[ a owl:Restriction ; owl:onProperty :hasParent ; owl:maxCardinality 2 ] .")
    assert any("SubClassOf" in k for k in rep.skipped)


# --------------------------------------------------------------------------- #
# RDF/XML parses through the same path                                         #
# --------------------------------------------------------------------------- #


def test_rdf_xml_serialization():
    rdfxml = (
        '<?xml version="1.0"?>\n'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        ' xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"'
        ' xmlns:owl="http://www.w3.org/2002/07/owl#">\n'
        '  <owl:Class rdf:about="http://ex.org/x#Dog">'
        '<rdfs:subClassOf rdf:resource="http://ex.org/x#Mammal"/></owl:Class>\n'
        '</rdf:RDF>')
    clif, _ = rdf_to_clif(rdfxml, "xml")
    # (the owl:Class declaration shifts the per-axiom variable index, so match shape)
    assert clif.count("forall") == 1
    assert "(if (Dog x" in clif and "(Mammal x" in clif


# --------------------------------------------------------------------------- #
# The fixture file + the loop closes (theory query + materialization)          #
# --------------------------------------------------------------------------- #


def test_fixture_imports_via_importer():
    from domain_model_importer import DomainModelImporter

    result = DomainModelImporter().from_rdf_file(FIXTURE_TTL)
    assert result.source_format == "rdf"
    assert result.egi is not None and len(result.egi.E) > 0
    assert result.warnings                       # the maxCardinality line surfaces
    assert result.num_types >= 4 and result.num_relations >= 2


@pytest.fixture(scope="module")
def zoo_ttl_M():
    egi, _clif, _rep = rdf_to_egi(FIXTURE_TTL.read_text(encoding="utf-8"), "turtle")
    return egi


def test_rdf_model_decides_subsumption(zoo_ttl_M):
    assert entails(zoo_ttl_M, parse_egif("~[ (Dog *x) ~[ (Animal x) ] ]")).verdict == "true"
    # Dog ⊑ Father isn't derivable; but the fixture's owl:equivalentClass (iff) and
    # owl:disjointWith are non-Horn, so the honest open-world answer is UNKNOWN (the
    # non-Horn residue might bear), not FALSE — theory_query's documented behaviour.
    assert entails(zoo_ttl_M, parse_egif("~[ (Dog *x) ~[ (Father x) ] ]")).verdict == "unknown"


def test_rdf_model_decides_all_values_restriction(zoo_ttl_M):
    # Dog ⊑ ∀hasParent.Dog and Dog ⊑ Mammal — a Dog's parent is a Mammal.
    q = "~[ (Dog *x) (hasParent x *y) ~[ (Mammal y) ] ]"
    assert entails(zoo_ttl_M, parse_egif(q)).verdict == "true"


def test_rdf_model_materializes_abox(zoo_ttl_M):
    facts, report = materialize_egi(zoo_ttl_M)
    fe = generate_egif(facts)
    assert '(Dog "Fido")' in fe        # allValues rule fired on the asserted hasParent
    assert '(Animal "Fido")' in fe     # chained through subsumption
