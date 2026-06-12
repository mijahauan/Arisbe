"""
Import three ontologies as existential-graph theories — the ``ontology`` import
kind made real (``docs/CORPUS_AND_IMPORT_MODEL.md`` §2, §5).  Each is a single
``kind=ontology`` UoD: a conjunction of subsumption / disjointness / typing axioms
on one sheet, the standing theory Agon plays *within* and Organon shelves.

Three, in ascending realism — the general import model exercised end to end:

  * **porphyry_tree** — Porphyry's Tree (Isagoge, c. 270 CE), *hand-encoded*: the
    genus–species spine Substance ⊐ Body ⊐ Living ⊐ Animal ⊐ {Man, Beast}, the
    rational/irrational division, and Socrates as a Man.  The ancestor of all
    ontologies, and the very T-box Barbara (already in the corpus) reasons over.
  * **foaf_core** — a slice of FOAF (Brickley & Miller, W3C), *hand-encoded*:
    Person ⊑ Agent plus domain/range typing on the ``knows`` relation — a modern
    web ontology, showing argument-typing axioms.
  * **sumo_upper** — the upper spine of SUMO (Niles & Pease 2001, built on Sowa's
    upper ontology, KR 2000), *translated* from ``docs/references/SUMO1.2.txt`` by
    ``tools/suokif_to_eg.py``.  An **honest partial import**: only the
    EG-expressible ground axioms cross; documentation / modal / higher-order forms
    are reported, not silently dropped.  SUMO's top is Sowa's reading of Peirce's
    three categories — Independent / Relative / Mediating = Firstness / Secondness
    / Thirdness — so the upper ontology is, at root, Peircean.

Import-safe (no side effects on import).  Run to seed the corpus.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from annotations import SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from ontology_egif import OntologyEGIF
from provenance import KIND_ONTOLOGY, make_provenance
from suokif_to_eg import upper_taxonomy
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)

_WHEN = datetime(2026, 6, 8, tzinfo=timezone.utc)
_WHEN_BFO = datetime(2026, 6, 12, tzinfo=timezone.utc)
_SUMO = Path(__file__).resolve().parent.parent / "docs" / "references" / "SUMO1.2.txt"
_BFO = Path(__file__).resolve().parent.parent / "corpus" / "ontologies" / "bfo_core.ofn"
_COLORE_BETWEEN = (Path(__file__).resolve().parent.parent / "corpus" / "ontologies"
                   / "colore_between.clif")


def _uod(uod_id: str, name: str, description: str, egif: str) -> UniverseOfDiscourse:
    meta = UoDMetadata(
        uod_id=uod_id, uod_type=UoDType.STANDALONE, name=name,
        description=description, category=UoDCategory.DOMAIN_MODEL,
        created=_WHEN, last_modified=_WHEN,
    )
    return UniverseOfDiscourse(metadata=meta, current_egi=parse_egif(egif))


def _anns(*texts_tags) -> List[dict]:
    return annotations_to_list(
        [make_annotation(SCOPE_UOD, t, tags=tg) for t, tg in texts_tags]
    )


# --------------------------------------------------------------------------- #
# Porphyry's Tree                                                              #
# --------------------------------------------------------------------------- #

def porphyry():
    onto = (OntologyEGIF()
            .subsumes("Body", "Substance")
            .subsumes("Living", "Body")
            .subsumes("Animal", "Living")
            .subsumes("Man", "Animal")
            .subsumes("Beast", "Animal")
            .disjoint("Man", "Beast")
            .instance("Socrates", "Man"))
    uod = _uod(
        "porphyry_tree", "Porphyry's Tree",
        "The classic genus–species hierarchy of Porphyry's Isagoge (c. 270 CE): "
        "Substance ⊐ Body ⊐ Living ⊐ Animal, divided into Man (rational) and Beast "
        "(irrational), with Socrates as a Man. The ancestor of all ontologies and "
        "the T-box the syllogism Barbara reasons over.",
        onto.egif(),
    )
    prov = make_provenance(
        theorem_source={"type": "book", "author": "Porphyry",
                        "title": "Isagoge", "year": "c. 270",
                        "note": "the Tree of Porphyry — genus, species, differentia"},
        method_sources=[{"type": "book", "author": "Peirce, Charles Sanders",
                         "title": "Collected Papers", "bibkey": "peirce1931collected",
                         "note": "existential-graph notation"}],
        kind=KIND_ONTOLOGY,
    )
    anns = _anns(
        ("Porphyry's Tree (Isagoge, c. 270 CE) — the original ontology: a "
         "subsumption spine with a binary differentia (rational/irrational) "
         "dividing Animal into Man and Beast. Each ⊑ is a scroll; the whole tree "
         "is their conjunction. The very T-box the corpus's Barbara reasons over, "
         "and the context the man–mortal scroll presupposes.",
         ["ontology", "cited", "history-of-logic", "t-box"]),
    )
    return uod, prov, anns


# --------------------------------------------------------------------------- #
# FOAF core                                                                   #
# --------------------------------------------------------------------------- #

def foaf():
    onto = (OntologyEGIF()
            .subsumes("Person", "Agent")
            .domain("knows", 2, 1, "Person")   # domain(knows) ⊑ Person
            .domain("knows", 2, 2, "Person")   # range(knows)  ⊑ Person
            .instance("Alice", "Person")
            .instance("Bob", "Person"))
    uod = _uod(
        "foaf_core", "FOAF (core)",
        "A core slice of the FOAF (Friend of a Friend) vocabulary: Person ⊑ Agent, "
        "with the knows relation typed Person→Person (domain and range), and two "
        "individuals. A modern web ontology rendered as an EG theory.",
        onto.egif(),
    )
    prov = make_provenance(
        theorem_source={"type": "webpage", "author": "Brickley, Dan and Miller, Libby",
                        "title": "FOAF Vocabulary Specification",
                        "publisher": "W3C / FOAF project", "year": "2014",
                        "note": "core terms: Agent, Person, knows"},
        method_sources=[{"type": "book", "author": "Peirce, Charles Sanders",
                         "title": "Collected Papers", "bibkey": "peirce1931collected"}],
        kind=KIND_ONTOLOGY,
    )
    anns = _anns(
        ("FOAF core — a modern semantic-web vocabulary as an EG theory. Beyond "
         "subsumption (Person ⊑ Agent) it shows argument typing: domain/range on "
         "the binary knows relation become two scrolls ~[ (knows *x *y) ~[ (Person …) ] ]. "
         "A small populated board (Alice, Bob) for the game.",
         ["ontology", "cited", "semantic-web", "domain-range"]),
    )
    return uod, prov, anns


# --------------------------------------------------------------------------- #
# SUMO upper spine (translated)                                               #
# --------------------------------------------------------------------------- #

def sumo():
    text = _SUMO.read_text(encoding="latin-1")
    egif, report, kept = upper_taxonomy(text, root="Entity", max_depth=2)
    n_sub = len(kept["subsumptions"])
    n_dis = len(kept["disjoints"])
    n_cls = len(kept["classes"])
    skipped = report["skipped"]
    n_skipped = sum(skipped.values())
    uod = _uod(
        "sumo_upper", "SUMO (upper taxonomy)",
        f"The upper structural spine of the Suggested Upper Merged Ontology — "
        f"{n_sub} subsumptions over {n_cls} classes (depth ≤ 2 from Entity), "
        f"translated from docs/references/SUMO1.2.txt. SUMO's top is Sowa's upper "
        f"ontology, itself built on Peirce's three categories: Independent / "
        f"Relative / Mediating = Firstness / Secondness / Thirdness.",
        egif,
    )
    prov = make_provenance(
        theorem_source={"type": "paper-conference",
                        "author": "Niles, Ian and Pease, Adam",
                        "title": "Towards a Standard Upper Ontology",
                        "container_title": "FOIS", "year": "2001",
                        "note": "SUMO 1.2 (docs/references/SUMO1.2.txt), a merge "
                                "of several SUO sources"},
        method_sources=[
            {"type": "book", "author": "Sowa, John F.",
             "title": "Knowledge Representation: Logical, Philosophical, and "
                      "Computational Foundations", "publisher": "Brooks/Cole",
             "year": "2000", "bibkey": "sowa2000eg2cg",
             "note": "the upper ontology SUMO's merge is based on; ch. 2"},
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "the three categories underlying Sowa's top level"},
        ],
        kind=KIND_ONTOLOGY,
    )
    # The honest skip report, verbatim, as a uod annotation (no silent caps).
    skip_str = ", ".join(f"{v}× {k}" for k, v in sorted(
        skipped.items(), key=lambda kv: -kv[1]))
    anns = _anns(
        (f"Upper spine of SUMO (Niles & Pease 2001): {n_sub} subsumptions + "
         f"{n_dis} disjoints over {n_cls} classes, depth ≤ 2 from Entity. SUMO's "
         f"top is Sowa's ontology on Peirce's categories — Independent/Relative/"
         f"Mediating = Firstness/Secondness/Thirdness, the Peircean triad at the "
         f"root of a modern upper ontology.",
         ["ontology", "cited", "sumo", "peircean-categories", "t-box"]),
        (f"Honest partial import: the full SUMO file yields "
         f"{report['translated']} EG axioms; {n_skipped} forms were NOT "
         f"translated because they are not first-order-EG-expressible — {skip_str}. "
         f"Documentation strings are metadata; =>/<=>/nth-domain/modal forms exceed "
         f"first-order EG. The displayed UoD is the depth≤2 upper spine for layout "
         f"legibility; the full ground taxonomy (123 subsumptions) is reproducible "
         f"via tools/suokif_to_eg.py.",
         ["provenance", "honest-partial-import", "no-silent-caps"]),
    )
    return uod, prov, anns


# --------------------------------------------------------------------------- #
# BFO core — imported through the OWL→CLIF→EGI pipeline                        #
# --------------------------------------------------------------------------- #

def bfo():
    """The Basic Formal Ontology upper taxonomy, imported from OWL functional
    syntax — the OWL→CLIF→EGI pipeline exercised end to end into the corpus."""
    from domain_model_importer import from_owl_file

    result = from_owl_file(_BFO)
    meta = UoDMetadata(
        uod_id="bfo_core", uod_type=UoDType.STANDALONE, name="BFO (core taxonomy)",
        description=(
            "The upper is-a taxonomy of the Basic Formal Ontology (BFO 2.0): Entity ⊐ "
            "{Continuant, Occurrent}; IndependentContinuant ⊐ MaterialEntity ⊐ "
            "{Object, FiatObjectPart, ObjectAggregate}; the realizable line "
            "Quality / Role / Disposition ⊐ Function; with Continuant/Occurrent and "
            "the three dependence kinds disjoint. A pure T-box and a second real upper "
            "ontology beside SUMO — imported from OWL functional syntax through the "
            "OWL→CLIF→EGI pipeline."),
        category=UoDCategory.DOMAIN_MODEL, created=_WHEN_BFO, last_modified=_WHEN_BFO,
    )
    uod = UniverseOfDiscourse(metadata=meta, current_egi=result.egi)
    prov = make_provenance(
        theorem_source={"type": "book",
                        "author": "Arp, Robert and Smith, Barry and Spear, Andrew D.",
                        "title": "Building Ontologies with Basic Formal Ontology",
                        "publisher": "MIT Press", "year": "2015",
                        "note": "BFO 2.0 upper taxonomy; partial faithful encoding"},
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "existential-graph notation"},
        ],
        kind=KIND_ONTOLOGY,
    )
    skips = ", ".join(w for w in result.warnings) or "none"
    anns = _anns(
        ("BFO core — the Basic Formal Ontology upper taxonomy (Arp, Smith & Spear "
         "2015) as an EG theory. A *pure-ish T-box*: a deep subsumption spine "
         "(Object ⊑ MaterialEntity ⊑ IndependentContinuant ⊑ Continuant ⊑ Entity) "
         "with Continuant/Occurrent disjoint and the three dependence kinds "
         "pairwise disjoint. The case the *theorem query* is for — model-checking a "
         "subsumption over its sparse A-box reads vacuously; freezing a witness "
         "decides it. Complements SUMO as a second real upper ontology to test "
         "proposals against.",
         ["ontology", "cited", "bfo", "upper-ontology", "t-box"]),
        (f"Imported from corpus/ontologies/bfo_core.ofn through the OWL→CLIF→EGI "
         f"pipeline ({result.num_axioms} CLIF axioms over {result.num_types} classes). "
         f"Honest partial encoding: BFO's principal is-a spine + the three top "
         f"disjointness axioms — a pure T-box, not the full BFO/RO axiomatisation. "
         f"BFO's Relation-Ontology relations and any A-box are omitted from the stored "
         f"UoD because relational scrolls are super-linear to lay out at the §3.3 save "
         f"boundary while the taxonomy is cheap (the layout-perf frontier; M is data, "
         f"draw only the contested fragment). Translator skips: {skips}.",
         ["provenance", "owl-import", "honest-partial-import", "no-silent-caps"]),
    )
    return uod, prov, anns


# --------------------------------------------------------------------------- #
# COLORE "between" — imported from a real Common Logic Ontology Repository file #
# --------------------------------------------------------------------------- #

def colore_between():
    """The COLORE *betweenness* ontology, imported from real Common Logic.

    The first corpus UoD drawn from an external CL ontology repository (COLORE,
    github.com/gruninger/colore).  Validates the whole CLIF→EGI path on genuinely
    foreign content; the cl-imports closure (betweenness → weak_between → bet) is
    resolved by hand into one self-contained source."""
    from domain_model_importer import from_clif_file
    from model_materialization import materialize_egi

    result = from_clif_file(_COLORE_BETWEEN)
    g = result.egi
    facts, rep = materialize_egi(g)  # honest report: a relational FOL theory
    meta = UoDMetadata(
        uod_id="colore_between", uod_type=UoDType.STANDALONE,
        name="COLORE betweenness",
        description=(
            "The betweenness ontology from COLORE (the Common Logic Ontology "
            "Repository, M. Grüninger et al., University of Toronto): a ternary "
            "between(x,y,z) relation axiomatised by symmetry, identity-of-ends, and "
            "two transitivity laws — the resolved import closure betweenness → "
            "weak_between → bet. The first corpus ontology imported from a real "
            "external CL repository, validating the OWL/CLIF→EGI pipeline on foreign "
            "first-order content."),
        category=UoDCategory.DOMAIN_MODEL, created=_WHEN_BFO, last_modified=_WHEN_BFO,
    )
    uod = UniverseOfDiscourse(metadata=meta, current_egi=g)
    prov = make_provenance(
        theorem_source={"type": "webpage",
                        "author": "Grüninger, Michael and others",
                        "title": "COLORE: Common Logic Ontology Repository — "
                                 "betweenness",
                        "publisher": "University of Toronto",
                        "url": "https://github.com/gruninger/colore/tree/master/"
                               "ontologies/between",
                        "note": "Common Logic (ISO 24707), CC BY-SA 4.0; cl-imports "
                                "closure betweenness → weak_between → bet"},
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "existential-graph notation"},
        ],
        kind=KIND_ONTOLOGY,
    )
    anns = _anns(
        ("COLORE betweenness — the first corpus ontology imported from a real "
         "external Common Logic repository (Grüninger's COLORE). A ternary "
         "between(x,y,z) with symmetry between(x,y,z)→between(z,y,x), "
         "identity-of-ends, and transitivity. Proof that the CLIF→EGI pipeline reads "
         "genuinely foreign first-order ontologies, not only Arisbe-authored ones.",
         ["ontology", "cited", "colore", "common-logic", "betweenness"]),
        (f"Imported from corpus/ontologies/colore_between.clif (verbatim COLORE "
         f"content, CC BY-SA 4.0). {rep.summary}. This is a **relational FOL** theory "
         f"— its axioms use equality and negation in bodies/heads, so materialization "
         f"leaves them to the contest/deduction game (no A-box to forward-chain); the "
         f"honest reasoning value is in the contest, not the Horn closure. The "
         f"cl-imports chain was resolved by hand (auto-resolution is not yet built); "
         f"COLORE function-term modules are out of scope (EGs are relational).",
         ["provenance", "clif-import", "honest-partial-import", "non-horn-residue"]),
    )
    return uod, prov, anns


def build_all() -> List[Tuple]:
    return [porphyry(), foaf(), sumo(), bfo(), colore_between()]


def main(argv=None) -> int:
    from tomos_service import TomosService

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    for uod, prov, anns in build_all():
        prov.validate()
        service.save_uod(uod)                       # §3.3 attests at the boundary
        service.save_provenance(uod, prov.to_dict())
        service.save_annotations(uod, anns)
        g = uod.current_egi
        print(f"  saved {uod.uod_id:16} kind=ontology  "
              f"V{len(g.V)} E{len(g.E)} Cut{len(g.Cut)}")
    print(f"\nimported {len(build_all())} ontologies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
