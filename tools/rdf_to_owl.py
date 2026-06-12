"""
RDF (Turtle / RDF-XML / N-Triples / JSON-LD / …) → OWL axiom forms → CLIF → EGI.

The second OWL front-end.  Where ``owl_to_clif`` reads OWL **functional syntax** (form-
oriented text), real ontologies are distributed in the **RDF serializations** — Turtle
(``.ttl``), RDF/XML (``.owl`` / ``.rdf``), N-Triples, JSON-LD.  Those are *graphs of triples*,
and OWL's structure is encoded in them (a class restriction is a blank node carrying
``owl:onProperty`` + ``owl:someValuesFrom``; an intersection is an ``rdf:List``; …).

Rather than re-implement that decoding *and* re-implement OWL→CLIF, this module does only the
first half: parse the RDF with **rdflib** (BSD-3, a proven library — we don't hand-roll a
Turtle/XML parser) and **reconstruct the very same functional-syntax ``Node`` AST that
``owl_to_clif`` already consumes**.  Every axiom + class-expression rule there (subsumption
scroll, conjunctive Horn body, ``∀R.D``→Horn prenex, disjunction, complement, ``hasValue``,
``≥1`` cardinality, the honest skip-report) is reused unchanged via ``translate_axiom_forms``.

Covered (the OWL-RL-ish EG-expressible fragment): class axioms (``rdfs:subClassOf``,
``owl:equivalentClass``, ``owl:disjointWith``, ``owl:AllDisjointClasses``); property axioms
(``rdfs:subPropertyOf`` / ``rdfs:domain`` / ``rdfs:range`` / ``owl:inverseOf`` /
``owl:Symmetric|TransitiveProperty``); class expressions (named, ``owl:Restriction`` over
``some``/``all``/``hasValue``/``min`` cardinality, ``owl:intersectionOf`` / ``unionOf`` /
``complementOf``); and assertions (``rdf:type`` class membership, object-property triples,
``owl:sameAs`` / ``owl:differentFrom`` / ``owl:AllDifferent``).  A class expression rdflib
gives us but the EG fragment can't take (datatypes, ``oneOf``, ``hasSelf``, ``max``/exact
cardinality) is reconstructed as a sentinel so the downstream translator *reports* it — the
manifest floor: never a silent drop that reads as "imported the whole ontology".

``rdf_to_clif(text, fmt=None)`` → ``(clif, report)``; ``rdf_to_egi(...)`` pipes through
``parse_clif``.  ``fmt`` defaults to rdflib's guesser (or pass ``"turtle"`` / ``"xml"`` / …).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF, RDFS

from owl_to_clif import Node, OWLReport, translate_axiom_forms

OWL = Namespace("http://www.w3.org/2002/07/owl#")

# Namespaces whose terms are schema vocabulary, never user individuals/classes — used to
# tell a content assertion (``:Rex rdf:type :Dog``) from a structural triple
# (``:Dog rdf:type owl:Class``).
_BUILTIN_NS = (str(RDF), str(RDFS), str(OWL), "http://www.w3.org/2001/XMLSchema#")


def _is_builtin(ref) -> bool:
    return isinstance(ref, URIRef) and any(str(ref).startswith(ns) for ns in _BUILTIN_NS)


def _iri(ref) -> str:
    """A URIRef → the ``<full-iri>`` token owl_to_clif's _localname/_safe_ident expect."""
    return f"<{ref}>"


# --------------------------------------------------------------------------- #
# Class-expression reconstruction:  an RDF node → an owl_to_clif Node          #
# --------------------------------------------------------------------------- #

def _unsupported(label: str) -> Node:
    """A sentinel class expression the downstream translator can't compile, so it is
    *reported* (its axiom skipped) rather than silently dropped."""
    return [f"Unsupported_{label}"]


def _members(g: Graph, list_node) -> List[Node]:
    return [_class_expr(g, m) for m in Collection(g, list_node)]


def _restriction(g: Graph, node) -> Node:
    """An ``owl:Restriction`` blank node → an Object*ValuesFrom / HasValue / cardinality
    Node.  Unsupported shapes (datatypes, hasSelf, max/exact card) → a reported sentinel."""
    prop = g.value(node, OWL.onProperty)
    if prop is None:
        return _unsupported("Restriction")
    P = _iri(prop)
    sv = g.value(node, OWL.someValuesFrom)
    if sv is not None:
        return ["ObjectSomeValuesFrom", P, _class_expr(g, sv)]
    av = g.value(node, OWL.allValuesFrom)
    if av is not None:
        return ["ObjectAllValuesFrom", P, _class_expr(g, av)]
    hv = g.value(node, OWL.hasValue)
    if hv is not None:
        return ["ObjectHasValue", P, _iri(hv)] if isinstance(hv, URIRef) \
            else _unsupported("DataHasValue")
    if g.value(node, OWL.hasSelf) is not None:
        return _unsupported("ObjectHasSelf")
    for pred, name in ((OWL.minCardinality, "ObjectMinCardinality"),
                       (OWL.minQualifiedCardinality, "ObjectMinCardinality"),
                       (OWL.maxCardinality, "ObjectMaxCardinality"),
                       (OWL.maxQualifiedCardinality, "ObjectMaxCardinality"),
                       (OWL.cardinality, "ObjectExactCardinality"),
                       (OWL.qualifiedCardinality, "ObjectExactCardinality")):
        n = g.value(node, pred)
        if n is not None:
            out: List[Node] = [name, str(int(n)), P]
            onclass = g.value(node, OWL.onClass)
            if onclass is not None:
                out.append(_class_expr(g, onclass))
            return out
    return _unsupported("Restriction")


def _class_expr(g: Graph, node) -> Node:
    """An RDF class node → an owl_to_clif class-expression Node."""
    if isinstance(node, URIRef):
        return _iri(node)
    if isinstance(node, BNode):
        if (node, RDF.type, OWL.Restriction) in g:
            return _restriction(g, node)
        lst = g.value(node, OWL.intersectionOf)
        if lst is not None:
            return ["ObjectIntersectionOf", *_members(g, lst)]
        lst = g.value(node, OWL.unionOf)
        if lst is not None:
            return ["ObjectUnionOf", *_members(g, lst)]
        comp = g.value(node, OWL.complementOf)
        if comp is not None:
            return ["ObjectComplementOf", _class_expr(g, comp)]
        if g.value(node, OWL.oneOf) is not None:
            return _unsupported("ObjectOneOf")
    return _unsupported("ClassExpression")


# --------------------------------------------------------------------------- #
# Axiom extraction:  the RDF graph → a list of owl_to_clif axiom Node forms     #
# --------------------------------------------------------------------------- #

def rdf_to_forms(g: Graph) -> List[Node]:
    """Reconstruct OWL functional-syntax axiom ``Node`` forms from an RDF graph."""
    forms: List[Node] = []

    # Vocabulary declarations (so the report counts them, like the functional path).
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if isinstance(s, URIRef):
            forms.append(["Declaration", ["Class", _iri(s)]])
    object_props = set()
    for kind in (OWL.ObjectProperty, OWL.TransitiveProperty, OWL.SymmetricProperty,
                 OWL.InverseFunctionalProperty, OWL.FunctionalProperty):
        for s in g.subjects(RDF.type, kind):
            if isinstance(s, URIRef):
                object_props.add(s)
    for s in sorted(object_props, key=str):
        forms.append(["Declaration", ["ObjectProperty", _iri(s)]])
    for s in set(g.subjects(RDF.type, OWL.NamedIndividual)):
        if isinstance(s, URIRef):
            forms.append(["Declaration", ["NamedIndividual", _iri(s)]])

    # Class axioms.
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        forms.append(["SubClassOf", _class_expr(g, s), _class_expr(g, o)])
    for s, _, o in g.triples((None, OWL.equivalentClass, None)):
        forms.append(["EquivalentClasses", _class_expr(g, s), _class_expr(g, o)])
    for s, _, o in g.triples((None, OWL.disjointWith, None)):
        forms.append(["DisjointClasses", _class_expr(g, s), _class_expr(g, o)])
    for adc in set(g.subjects(RDF.type, OWL.AllDisjointClasses)):
        lst = g.value(adc, OWL.members)
        if lst is not None:
            forms.append(["DisjointClasses", *_members(g, lst)])

    # Property axioms.
    for s, _, o in g.triples((None, RDFS.subPropertyOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            forms.append(["SubObjectPropertyOf", _iri(s), _iri(o)])
    for s, _, o in g.triples((None, RDFS.domain, None)):
        if isinstance(s, URIRef):
            forms.append(["ObjectPropertyDomain", _iri(s), _class_expr(g, o)])
    for s, _, o in g.triples((None, RDFS.range, None)):
        if isinstance(s, URIRef):
            forms.append(["ObjectPropertyRange", _iri(s), _class_expr(g, o)])
    for s, _, o in g.triples((None, OWL.inverseOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            forms.append(["InverseObjectProperties", _iri(s), _iri(o)])
    for s in g.subjects(RDF.type, OWL.SymmetricProperty):
        if isinstance(s, URIRef):
            forms.append(["SymmetricObjectProperty", _iri(s)])
    for s in g.subjects(RDF.type, OWL.TransitiveProperty):
        if isinstance(s, URIRef):
            forms.append(["TransitiveObjectProperty", _iri(s)])
    for s in g.subjects(RDF.type, OWL.FunctionalProperty):
        if isinstance(s, URIRef):
            forms.append(["FunctionalObjectProperty", _iri(s)])      # reported, non-EG

    # Identity axioms.
    for s, _, o in g.triples((None, OWL.sameAs, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            forms.append(["SameIndividual", _iri(s), _iri(o)])
    for s, _, o in g.triples((None, OWL.differentFrom, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            forms.append(["DifferentIndividuals", _iri(s), _iri(o)])
    for ad in set(g.subjects(RDF.type, OWL.AllDifferent)):
        lst = g.value(ad, OWL.distinctMembers) or g.value(ad, OWL.members)
        if lst is not None:
            forms.append(["DifferentIndividuals", *_members(g, lst)])

    # Assertions — the A-box.  A class assertion is ``a rdf:type C`` where C is a user
    # class (not a builtin like owl:Class).  An object-property assertion is any triple
    # ``a P b`` whose predicate is a user property (not in a builtin namespace, not
    # rdf:type) with both ends named (URIRef) — detected *structurally*, since a property
    # need not be explicitly typed owl:ObjectProperty to be asserted.  (A user annotation
    # whose object is a Literal is excluded by the URIRef-object test; schema triples use
    # builtin predicates and are excluded too.)
    for s, _, o in g.triples((None, RDF.type, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) and not _is_builtin(o):
            forms.append(["ClassAssertion", _iri(o), _iri(s)])
    for s, p, o in g:
        if (isinstance(s, URIRef) and isinstance(p, URIRef) and isinstance(o, URIRef)
                and p != RDF.type and not _is_builtin(p)):
            forms.append(["ObjectPropertyAssertion", _iri(p), _iri(s), _iri(o)])

    return forms


def rdf_to_clif(text: str, fmt: Optional[str] = None):
    """Parse an RDF document and translate its OWL axioms to CLIF.

    ``fmt`` is an rdflib format hint (``"turtle"`` / ``"xml"`` / ``"nt"`` / ``"json-ld"``);
    ``None`` lets rdflib guess.  Returns ``(clif_text, OWLReport)``."""
    g = Graph()
    g.parse(data=text, format=fmt) if fmt else g.parse(data=text)
    return translate_axiom_forms(rdf_to_forms(g))


def rdf_to_egi(text: str, fmt: Optional[str] = None):
    """RDF → CLIF → EGI.  Returns ``(egi, clif_text, report)``."""
    from clif_parser_dau import parse_clif

    clif_text, report = rdf_to_clif(text, fmt)
    egi = parse_clif(clif_text) if clif_text.strip() else parse_clif("(true)")
    return egi, clif_text, report


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: rdf_to_owl.py <ontology.ttl|.owl|.rdf> [format]")
        return 2
    fmt = argv[1] if len(argv) > 1 else None
    text = Path(argv[0]).read_text(encoding="utf-8")
    clif_text, report = rdf_to_clif(text, fmt)
    print(f"RDF → OWL → CLIF translation of {argv[0]}:")
    print("  translated  :", dict(report.translated))
    print("  skipped     :", dict(report.skipped))
    print("  declarations:", dict(report.declarations))
    print(f"  → {report.n_axioms} CLIF axioms over {len(report.classes)} classes, "
          f"{len(report.properties)} properties, {len(report.individuals)} individuals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
