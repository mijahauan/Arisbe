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
    # A single axiom gets per-axiom index 1, so its bound variables are x1/y1/z1
    # (distinct names per axiom prevent parse_clif merging lines of identity).
    ("SubClassOf(:Man :Mortal)", "(forall (x1) (if (Man x1) (Mortal x1)))"),
    ("SubObjectPropertyOf(:hasMother :hasParent)",
     "(forall (x1 y1) (if (hasMother x1 y1) (hasParent x1 y1)))"),
    ("ObjectPropertyDomain(:knows :Person)",
     "(forall (x1 y1) (if (knows x1 y1) (Person x1)))"),
    ("ObjectPropertyRange(:knows :Person)",
     "(forall (x1 y1) (if (knows x1 y1) (Person y1)))"),
    ("SymmetricObjectProperty(:siblingOf)",
     "(forall (x1 y1) (if (siblingOf x1 y1) (siblingOf y1 x1)))"),
    ("TransitiveObjectProperty(:ancestorOf)",
     "(forall (x1 y1 z1) (if (and (ancestorOf x1 y1) (ancestorOf y1 z1)) (ancestorOf x1 z1)))"),
    ("SubClassOf(ObjectIntersectionOf(:Male :Parent) :Father)",
     "(forall (x1) (if (and (Male x1) (Parent x1)) (Father x1)))"),
    ("ClassAssertion(:Dog :Rex)", "(Dog Rex)"),
    ("ObjectPropertyAssertion(:hasParent :Rex :Fido)", "(hasParent Rex Fido)"),
])
def test_axiom_form_translates_to_expected_clif(axiom, expected):
    clif, _ = translate(_onto(axiom))
    assert clif.strip() == expected


def test_distinct_axioms_get_distinct_variables():
    # Two subsumptions must NOT share a bound variable — else parse_clif unifies them
    # into one line of identity threaded through both scrolls (a layout catastrophe).
    clif, _ = translate(_onto("SubClassOf(:A :B)", "SubClassOf(:C :D)"))
    assert "(forall (x1) (if (A x1) (B x1)))" in clif
    assert "(forall (x2) (if (C x2) (D x2)))" in clif
    from egif_parser_dau import parse_egif  # noqa
    from clif_parser_dau import parse_clif
    assert len(parse_clif(clif).V) == 2      # two lines of identity, not one


def test_equivalent_and_disjoint_are_pairwise():
    clif, rep = translate(_onto("EquivalentClasses(:Dog :Canine)",
                                "DisjointClasses(:Dog :Cat)"))
    assert "(forall (x1) (iff (Dog x1) (Canine x1)))" in clif
    assert "(forall (x2) (not (and (Dog x2) (Cat x2))))" in clif


def test_inverse_properties_emit_both_directions():
    clif, rep = translate(_onto("InverseObjectProperties(:hasParent :hasChild)"))
    assert "(forall (x1 y1) (if (hasParent x1 y1) (hasChild y1 x1)))" in clif
    assert "(forall (x1 y1) (if (hasChild x1 y1) (hasParent y1 x1)))" in clif
    assert rep.translated["InverseObjectProperties"] == 2


def test_existential_restriction_in_superclass():
    clif, _ = translate(_onto("SubClassOf(:Dog ObjectSomeValuesFrom(:hasParent :Dog))"))
    assert clif.strip() == (
        "(forall (x1) (if (Dog x1) (exists (w1) (and (hasParent x1 w1) (Dog w1)))))")


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
    assert clif.strip() == "(forall (x1) (if (Man x1) (Mortal x1)))"


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
