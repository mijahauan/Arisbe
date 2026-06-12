"""
OWL → CLIF → EGI import pipeline (``tools/owl_to_clif`` + ``domain_model_importer``).

The front half of the named pipeline: OWL 2 functional syntax → CLIF (the robust
existing interlingua) → EGI.  Verifies each translatable axiom form produces the right
Common-Logic shape, that untranslatable constructs are reported (never silently
dropped — the manifest floor), and — closing this session's loop — that an
OWL-imported ontology is a real domain model M the **theory query** can reason over.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from owl_to_clif import owl_to_egi, translate
from egif_parser_dau import parse_egif
from theory_query import entails

FIXTURE = ROOT / "tests" / "fixtures" / "zoo.ofn"


def _onto(*axioms: str) -> str:
    return "Ontology(<x>\n  " + "\n  ".join(axioms) + "\n)"


# --------------------------------------------------------------------------- #
# Each axiom form → its Common-Logic shape                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("axiom, expected", [
    ("SubClassOf(:Man :Mortal)", "(forall (x) (if (Man x) (Mortal x)))"),
    ("SubObjectPropertyOf(:hasMother :hasParent)",
     "(forall (x y) (if (hasMother x y) (hasParent x y)))"),
    ("ObjectPropertyDomain(:knows :Person)",
     "(forall (x y) (if (knows x y) (Person x)))"),
    ("ObjectPropertyRange(:knows :Person)",
     "(forall (x y) (if (knows x y) (Person y)))"),
    ("SymmetricObjectProperty(:siblingOf)",
     "(forall (x y) (if (siblingOf x y) (siblingOf y x)))"),
    ("TransitiveObjectProperty(:ancestorOf)",
     "(forall (x y z) (if (and (ancestorOf x y) (ancestorOf y z)) (ancestorOf x z)))"),
    ("SubClassOf(ObjectIntersectionOf(:Male :Parent) :Father)",
     "(forall (x) (if (and (Male x) (Parent x)) (Father x)))"),
    ("ClassAssertion(:Dog :Rex)", "(Dog Rex)"),
    ("ObjectPropertyAssertion(:hasParent :Rex :Fido)", "(hasParent Rex Fido)"),
])
def test_axiom_form_translates_to_expected_clif(axiom, expected):
    clif, _ = translate(_onto(axiom))
    assert clif.strip() == expected


def test_equivalent_and_disjoint_are_pairwise():
    clif, rep = translate(_onto("EquivalentClasses(:Dog :Canine)",
                                "DisjointClasses(:Dog :Cat)"))
    assert "(forall (x) (iff (Dog x) (Canine x)))" in clif
    assert "(forall (x) (not (and (Dog x) (Cat x))))" in clif


def test_inverse_properties_emit_both_directions():
    clif, rep = translate(_onto("InverseObjectProperties(:hasParent :hasChild)"))
    assert "(forall (x y) (if (hasParent x y) (hasChild y x)))" in clif
    assert "(forall (x y) (if (hasChild x y) (hasParent y x)))" in clif
    assert rep.translated["InverseObjectProperties"] == 2


def test_existential_restriction_in_superclass():
    clif, _ = translate(_onto("SubClassOf(:Dog ObjectSomeValuesFrom(:hasParent :Dog))"))
    assert clif.strip() == (
        "(forall (x) (if (Dog x) (exists (y1) (and (hasParent x y1) (Dog y1)))))")


# --------------------------------------------------------------------------- #
# The honest floor — untranslatable constructs are reported, not dropped       #
# --------------------------------------------------------------------------- #


def test_subclass_of_thing_is_trivial_skip():
    clif, rep = translate(_onto("SubClassOf(:Mammal owl:Thing)"))
    assert clif.strip() == ""
    assert any("Thing" in k for k in rep.skipped)


@pytest.mark.parametrize("axiom, marker", [
    ("SubClassOf(:Dog ObjectMinCardinality(2 :hasParent))", "SubClassOf"),
    ("SubClassOf(:Dog ObjectUnionOf(:Mammal :Bird))", "SubClassOf"),
    ("FunctionalObjectProperty(:hasMother)", "FunctionalObjectProperty"),
    ('AnnotationAssertion(rdfs:label :Dog "a dog")', "AnnotationAssertion"),
])
def test_untranslatable_is_skipped_and_named(axiom, marker):
    clif, rep = translate(_onto(axiom))
    assert clif.strip() == ""
    assert any(marker in k for k in rep.skipped)


def test_declarations_counted_not_skipped():
    _, rep = translate(_onto("Declaration(Class(:Animal))",
                             "Declaration(ObjectProperty(:hasParent))"))
    assert rep.declarations["Class"] == 1
    assert rep.declarations["ObjectProperty"] == 1
    assert sum(rep.skipped.values()) == 0


def test_iri_and_prefixed_names_reduce_to_local():
    clif, _ = translate(_onto(
        "SubClassOf(<http://example.org/onto#Man> <http://example.org/onto#Mortal>)"))
    assert clif.strip() == "(forall (x) (if (Man x) (Mortal x)))"


# --------------------------------------------------------------------------- #
# End to end — the fixture file parses to a real EGI via the importer          #
# --------------------------------------------------------------------------- #


def test_fixture_imports_to_egi_via_importer():
    from domain_model_importer import DomainModelImporter

    result = DomainModelImporter().from_owl_file(FIXTURE)
    assert result.source_format == "owl-functional"
    assert result.egi is not None and len(result.egi.E) > 0
    # The cardinality / union / annotation lines surface as warnings, not silence.
    assert result.warnings
    assert result.num_types >= 5 and result.num_relations >= 4


# --------------------------------------------------------------------------- #
# The loop closes — an OWL-imported ontology is testable as M (theory query)    #
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def zoo_M():
    owl = _onto(
        "SubClassOf(:Mammal :Animal)",
        "SubClassOf(:Dog :Mammal)",
        "SubClassOf(ObjectIntersectionOf(:Male :Parent) :Father)",
        "TransitiveObjectProperty(:hasAncestor)",
        "ClassAssertion(:Dog :Rex)",
    )
    egi, _clif, _rep = owl_to_egi(owl)
    return egi


def _verdict(M, query: str) -> str:
    return entails(M, parse_egif(query)).verdict


def test_owl_model_decides_subsumption_theorems(zoo_M):
    assert _verdict(zoo_M, "~[ (Dog *x) ~[ (Animal x) ] ]") == "true"     # chained
    assert _verdict(zoo_M, "~[ (Dog *x) ~[ (Father x) ] ]") == "false"    # not entailed


def test_owl_model_decides_intersection_rule(zoo_M):
    # Male ⊓ Parent ⊑ Father — the conjunctive Horn body imported from OWL.
    assert _verdict(zoo_M, "~[ (Male *x) (Parent x) ~[ (Father x) ] ]") == "true"


def test_owl_model_decides_transitivity(zoo_M):
    q = "~[ (hasAncestor *a *b) (hasAncestor b *c) ~[ (hasAncestor a c) ] ]"
    assert _verdict(zoo_M, q) == "true"
