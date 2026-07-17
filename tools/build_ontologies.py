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

**Under the validity discipline** (docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE
§3, the phase-2 ontology wrap, 2026-07-15): each imported theory resides at
level 1 of a **standing world-scroll** ``~[ M ~[ ] ]`` — nothing contingent at
depth 0. An ontology is *supposed* (imported, low-warrant), not derived, so the
preferred construction is the gapless inbound chain from the blank sheet —
**DC+** (open the standing scroll; asserts nothing) then **INS** (suppose the
theory into the negative arena; sound there) — recorded as a real two-step
chain, exactly like the domain-model boards. Three imports are instead housed
by the id-preserving structural adapter (``world_scroll.wrap_state``), each
recorded honestly in its annotations: ``bfo_core`` and ``colore_field`` cannot
ride the EGIF INS vehicle at all — their importers emit edges whose vertices
sit in *sibling* cuts (the OWL pairwise-disjointness expansion / a
relationalised shared constant), which no linear EGIF can express, so an INS
would silently rescope them — and ``skos_core`` is EGIF-expressible but the
INS reparse re-orders siblings past the geometric reader's ELK inversion
frontier, so the id-preserving wrap keeps its drawn record invertible. Every
builder verifies the residence: scroll recognized, ligature-closed, and M
reads back ``same_graph``-identical through ``m_view``.

Import-safe (no side effects on import).  Run to seed the corpus.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eg_navigation as nav
from annotations import SCOPE_UOD, annotations_to_list, make_annotation
from eg_navigation import same_graph
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from ontology_egif import OntologyEGIF
from proof_authoring import ProofChain
from provenance import KIND_ONTOLOGY, make_provenance
from suokif_to_eg import upper_taxonomy
from tomos_service import TransformationChain
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)
from world_scroll import find_world_scroll, is_ligature_closed, m_view, wrap_state

_WHEN = datetime(2026, 6, 8, tzinfo=timezone.utc)
_WHEN_BFO = datetime(2026, 6, 12, tzinfo=timezone.utc)
_SUMO = Path(__file__).resolve().parent.parent / "docs" / "references" / "SUMO1.2.txt"
_BFO = Path(__file__).resolve().parent.parent / "corpus" / "ontologies" / "bfo_core.ofn"
_COLORE_BETWEEN = (Path(__file__).resolve().parent.parent / "corpus" / "ontologies"
                   / "colore_between.clif")
_COLORE_CACHE = (Path(__file__).resolve().parent.parent / "corpus" / "ontologies"
                 / "colore_cache")
_SKOS_TTL = (Path(__file__).resolve().parent.parent / "corpus" / "ontologies"
             / "skos_core.ttl")


def _check_residence(egi, m) -> None:
    """The builder-side gate: the standing world-scroll is recognized, no line
    of identity crosses its boundary (the withdrawal ERA stays available), and
    M reads back ``same_graph``-identical through the shared read primitive."""
    scroll = find_world_scroll(egi)
    assert scroll is not None, "no standing world-scroll after the wrap"
    assert is_ligature_closed(egi, scroll), (
        "a line of identity crosses the world-scroll boundary")
    assert same_graph(m_view(egi), m), (
        "M does not read back identically through m_view — the wrap changed "
        "the imported theory")


def _meta(uod_id: str, name: str, description: str,
          created: datetime) -> UoDMetadata:
    return UoDMetadata(
        uod_id=uod_id, uod_type=UoDType.STANDALONE, name=name,
        description=description, category=UoDCategory.DOMAIN_MODEL,
        created=created, last_modified=created,
    )


def _uod(uod_id: str, name: str, description: str, egif: str,
         *, created: datetime = _WHEN, m=None,
         ) -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Build the theory's residence by the gapless inbound construction — DC+
    then INS, both real Dau rules from the blank sheet — so the imported
    theory resides in its standing world-scroll and carries the two-step chain
    that put it there (an ontology is *supposed*, not derived).

    ``m`` (optional) is the authoritative imported EGI when ``egif`` was
    generated from one — the residence check then verifies faithfulness to
    the *import*, not merely to a reparse of its text."""
    pc = ProofChain.from_blank()
    pc.apply("DC+", into=lambda g: g.sheet,
             note="Open the standing residence: an empty double cut asserts "
                  "nothing, and until it exists there is nowhere to hold an "
                  "imported theory that is not an assertion.")
    pc.apply("INS", insert=f"~[ {egif.strip()} ]",
             into=lambda g: nav.child_cuts(g, g.sheet)[0],
             note="Supply the imported theory as one closed cell — insertion "
                  "is sound in the negative arena, and the content lands at "
                  "even depth (in-context agreement), where retraction is a "
                  "licensed ERA: nothing contingent stands at depth 0.")
    _check_residence(pc.current, m if m is not None else parse_egif(egif))
    uod = UniverseOfDiscourse(metadata=_meta(uod_id, name, description, created),
                              current_egi=pc.current)
    return pc.to_chain(), uod


def _uod_structural(uod_id: str, name: str, description: str, m_egi,
                    *, created: datetime,
                    ) -> Tuple[Optional[TransformationChain], UniverseOfDiscourse]:
    """House an imported EGI in the standing world-scroll **structurally**
    (``world_scroll.wrap_state``, id-preserving) — for the imports whose graphs
    carry cross-sibling vertex references no linear EGIF can express, so the
    rule-licensed INS (which parses EGIF) would silently rescope them. No chain
    is recorded (there was no rule application); the residence is documented in
    the UoD's annotations and verified here like every other."""
    wrapped, _ = wrap_state(m_egi)
    _check_residence(wrapped, m_egi)
    uod = UniverseOfDiscourse(metadata=_meta(uod_id, name, description, created),
                              current_egi=wrapped)
    return None, uod


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
    chain, uod = _uod(
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
    return chain, uod, prov, anns


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
    chain, uod = _uod(
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
    return chain, uod, prov, anns


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
    chain, uod = _uod(
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
    return chain, uod, prov, anns


# --------------------------------------------------------------------------- #
# BFO core — imported through the OWL→CLIF→EGI pipeline                        #
# --------------------------------------------------------------------------- #

def bfo():
    """The Basic Formal Ontology upper taxonomy, imported from OWL functional
    syntax — the OWL→CLIF→EGI pipeline exercised end to end into the corpus."""
    from domain_model_importer import from_owl_file

    result = from_owl_file(_BFO)
    chain, uod = _uod_structural(
        "bfo_core", "BFO (core taxonomy)",
        (
            "The upper is-a taxonomy of the Basic Formal Ontology (BFO 2.0): Entity ⊐ "
            "{Continuant, Occurrent}; IndependentContinuant ⊐ MaterialEntity ⊐ "
            "{Object, FiatObjectPart, ObjectAggregate}; the realizable line "
            "Quality / Role / Disposition ⊐ Function; with Continuant/Occurrent and "
            "the three dependence kinds disjoint. A pure T-box and a second real upper "
            "ontology beside SUMO — imported from OWL functional syntax through the "
            "OWL→CLIF→EGI pipeline."),
        result.egi, created=_WHEN_BFO,
    )
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
        ("Residence (phase-2 wrap, 2026-07-15): M is housed at level 1 of the "
         "standing world-scroll ~[ M ~[ ] ] by the id-preserving structural "
         "adapter (world_scroll.wrap_state), not the DC+·INS chain — the OWL "
         "pairwise-disjointness expansion reuses one variable across the three "
         "sibling disjointness cuts, so the imported graph carries edge→vertex "
         "references no linear EGIF can express, and an INS (which parses EGIF) "
         "would silently rescope them. Honest structural residence beats a "
         "forced rescope; the content is same_graph-identical to the import and "
         "the residence is verified (scroll recognized, ligature-closed, m_view "
         "reads back identical).",
         ["residence", "world-scroll", "structural-wrap"]),
    )
    return chain, uod, prov, anns


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
    chain, uod = _uod(
        "colore_between",
        "COLORE betweenness",
        (
            "The betweenness ontology from COLORE (the Common Logic Ontology "
            "Repository, M. Grüninger et al., University of Toronto): a ternary "
            "between(x,y,z) relation axiomatised by symmetry, identity-of-ends, and "
            "two transitivity laws — the resolved import closure betweenness → "
            "weak_between → bet. The first corpus ontology imported from a real "
            "external CL repository, validating the OWL/CLIF→EGI pipeline on foreign "
            "first-order content."),
        generate_egif(g), created=_WHEN_BFO, m=g,
    )
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
         f"honest reasoning value is in the contest, not the Horn closure. This "
         f"module's cl-imports chain was resolved by hand; the colore_field UoD beside "
         f"it now resolves its chain **automatically** (cl_import_resolver), and COLORE "
         f"function-term modules import too — function terms relationalise on import "
         f"((density (dmv v m)) ↦ ∃z (dmv(v,m,z) ∧ density(z))).",
         ["provenance", "clif-import", "honest-partial-import", "non-horn-residue"]),
    )
    return chain, uod, prov, anns


# --------------------------------------------------------------------------- #
# COLORE "field" — a cl-imports closure resolved automatically                 #
# --------------------------------------------------------------------------- #

def colore_field():
    """The COLORE real-number *field* algebra, imported through **automatic
    cl-imports resolution**.

    Where ``colore_between`` had its import chain resolved *by hand* into one
    file, this resolves ``field → commutative_ring → ring → semiring``
    automatically (``cl_import_resolver.DirectoryResolver`` over the vendored
    ``colore_cache``), then relationalises the closure's **nested function
    terms** (the ring axioms are stated with function terms, e.g.
    ``(= (sum (sum x y) z) (sum x (sum y z)))``) on import — the two import-breadth
    capabilities (closure resolution + function relationalisation) exercised
    together on genuinely foreign Common Logic, landed as a drawn, §3.3-attested
    corpus UoD."""
    from cl_import_resolver import COLORE_PREFIX, DirectoryResolver, resolve_from_iri
    from domain_model_importer import from_clif_text

    resolver = DirectoryResolver(_COLORE_CACHE)
    closure = resolve_from_iri(COLORE_PREFIX + "ringoids/field.clif", resolver)
    result = from_clif_text(closure.combined_clif)
    g = result.egi
    modules = ", ".join(m.iri.replace(COLORE_PREFIX, "") for m in closure.modules)
    chain, uod = _uod_structural(
        "colore_field", "COLORE field algebra",
        (
            "The real-number field algebra from COLORE (the Common Logic Ontology "
            "Repository, M. Grüninger et al., University of Toronto): the ringoid "
            "tower field ⊃ commutative_ring ⊃ ring ⊃ semiring, with sum and prod "
            "axiomatised by associativity, commutativity, distributivity, identity "
            "and inverse. Imported through automatic cl-imports closure resolution "
            "(field → commutative_ring → ring → semiring) with the ring axioms' "
            "nested function terms relationalised on import — the first corpus UoD "
            "whose import chain was resolved by the machine, not by hand."),
        g, created=_WHEN_BFO,
    )
    prov = make_provenance(
        theorem_source={"type": "webpage",
                        "author": "Grüninger, Michael and others",
                        "title": "COLORE: Common Logic Ontology Repository — "
                                 "ringoids / field",
                        "publisher": "University of Toronto",
                        "url": "https://github.com/gruninger/colore/tree/master/"
                               "ontologies/ringoids",
                        "note": "Common Logic (ISO 24707), CC BY-SA 4.0; cl-imports "
                                "closure field → commutative_ring → ring → semiring, "
                                "auto-resolved + function terms relationalised"},
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "existential-graph notation"},
        ],
        kind=KIND_ONTOLOGY,
    )
    anns = _anns(
        ("COLORE field algebra — the ringoid tower (field ⊃ commutative_ring ⊃ "
         "ring ⊃ semiring) as an EG theory. The first corpus ontology whose "
         "cl-imports chain was resolved **automatically** (the resolver fetched "
         "and conjuncted the closure), and a heavily function-bearing one: the "
         "ring axioms use nested function terms like (= (sum (sum x y) z) (sum x "
         "(sum y z))), each relationalised to its graph relation on import. Proof "
         "that import breadth — closure resolution + function relationalisation — "
         "carries a real foreign algebra into the corpus.",
         ["ontology", "cited", "colore", "common-logic", "cl-imports", "algebra"]),
        (f"Imported from corpus/ontologies/colore_cache/ (verbatim COLORE content, "
         f"CC BY-SA 4.0) through automatic cl-imports resolution — closure: {modules}. "
         f"A **relational FOL** theory using equality throughout (totality/uniqueness "
         f"of the functions left to the contest game; materialization forward-chains "
         f"nothing). The fuller density closure (density → amount/spatial_volume → "
         f"ringoids, 130 cuts) is cached beside this as the source of record but "
         f"imported as *data*, not stored as a drawn UoD — a 130-cut relational theory "
         f"is super-linear to lay out at the §3.3 save boundary (the layout-perf "
         f"frontier, as with bfo_core's full axiomatisation; M is data, draw only the "
         f"contested fragment).",
         ["provenance", "clif-import", "cl-imports-auto-resolved", "non-horn-residue"]),
        ("Residence (phase-2 wrap, 2026-07-15): M is housed at level 1 of the "
         "standing world-scroll ~[ M ~[ ] ] by the id-preserving structural "
         "adapter (world_scroll.wrap_state), not the DC+·INS chain — the "
         "relationalised shared constants (the ring's zero and one) are each a "
         "single vertex referenced by edges in *sibling* axiom cuts, a shape no "
         "linear EGIF can express, so an INS (which parses EGIF) would silently "
         "rescope them. Honest structural residence beats a forced rescope; the "
         "content is same_graph-identical to the import and the residence is "
         "verified (scroll recognized, ligature-closed, m_view reads back "
         "identical).",
         ["residence", "world-scroll", "structural-wrap"]),
    )
    return chain, uod, prov, anns


# --------------------------------------------------------------------------- #
# SKOS core — imported from real RDF (Turtle) through the RDF→OWL→CLIF→EGI path #
# --------------------------------------------------------------------------- #

def skos_core():
    """The semantic-relation core of W3C SKOS, imported from **Turtle** — the RDF
    front-end (rdflib) exercised end to end into the corpus.

    The first corpus UoD imported from an RDF serialization (the others come from OWL
    functional syntax or Common Logic).  SKOS is distributed natively as RDF; the
    drawn fragment is its reasoning core — sub-property + transitivity + symmetry —
    plus a small illustrative concept scheme so the broaderTransitive closure
    forward-chains (a *populated, rule-bearing* domain, unlike the pure-T-box SUMO/
    BFO).  The full official vocabulary is vendored beside it (skos.rdf) as the source
    of record; its 124 relational-scroll cuts are super-linear to draw, so it imports
    as data — "M is data, draw only the contested fragment"."""
    from domain_model_importer import from_rdf_file

    result = from_rdf_file(_SKOS_TTL)
    chain, uod = _uod_structural(
        "skos_core", "SKOS (semantic-relation core)",
        (
            "The semantic-relation core of the W3C Simple Knowledge Organization "
            "System (SKOS, Miles & Bechhofer 2009): the Concept / ConceptScheme / "
            "Collection classes (pairwise disjoint) and the semantic relations — "
            "broader ⊑ broaderTransitive (transitive) and the symmetric related, all "
            "rolling up to semanticRelation — over a small illustrative animal "
            "thesaurus (Animal ⊐ Mammal ⊐ Carnivore ⊐ {Dog, Cat, Wolf}). The first "
            "corpus ontology imported from RDF (Turtle) through the RDF→OWL→CLIF→EGI "
            "front-end, and a *populated, rule-bearing* model: the broader chain "
            "closes under transitivity (Dog broaderTransitive Animal) and related "
            "closes symmetrically — a live target for the semantic game."),
        result.egi, created=_WHEN_BFO,
    )
    prov = make_provenance(
        theorem_source={"type": "techreport",
                        "author": "Miles, Alistair and Bechhofer, Sean",
                        "title": "SKOS Simple Knowledge Organization System Reference",
                        "publisher": "W3C", "year": "2009",
                        "url": "http://www.w3.org/TR/skos-reference/",
                        "note": "W3C Recommendation; vocabulary skos:core, vendored "
                                "verbatim as corpus/ontologies/skos.rdf"},
        method_sources=[
            {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers", "bibkey": "peirce1931collected",
             "note": "existential-graph notation"},
        ],
        kind=KIND_ONTOLOGY,
    )
    skips = ", ".join(w for w in result.warnings) or "none"
    anns = _anns(
        ("SKOS semantic-relation core (Miles & Bechhofer 2009) as an EG theory — the "
         "first corpus ontology read from RDF/Turtle. Where SUMO and BFO are pure "
         "T-boxes, SKOS here carries an A-box (an animal thesaurus): broader ⊑ "
         "broaderTransitive with broaderTransitive transitive means a chain of "
         "broader links forward-chains to the full ancestor relation (Dog "
         "broaderTransitive Animal), and the symmetric related closes both ways. A "
         "populated, rule-bearing model — a live semantic-game / Grapheus target, "
         "not just a subsumption lattice.",
         ["ontology", "cited", "skos", "rdf-turtle", "semantic-web", "a-box"]),
        (f"Imported from corpus/ontologies/skos_core.ttl through the RDF→OWL→CLIF→EGI "
         f"front-end (rdflib parses the Turtle; {result.num_axioms} CLIF axioms over "
         f"{result.num_types} classes). The DRAWN fragment is the reasoning core "
         f"(sub-property + transitivity + symmetry) + the illustrative scheme; the "
         f"FULL official W3C vocabulary is vendored verbatim beside it as "
         f"corpus/ontologies/skos.rdf — 62 EG axioms incl. every inverse / domain / "
         f"range pair (124 relational-scroll cuts), super-linear to lay out at the "
         f"§3.3 save boundary, so it is the source of record and imports as data, not "
         f"a drawn UoD (the layout-perf frontier, as with bfo_core; M is data, draw "
         f"only the contested fragment). The `ex:` animal thesaurus is authored here "
         f"to populate the scheme, not part of SKOS. Translator skips: {skips}.",
         ["provenance", "rdf-import", "honest-partial-import", "no-silent-caps"]),
        ("Residence (phase-2 wrap, 2026-07-15): M is housed at level 1 of the "
         "standing world-scroll ~[ M ~[ ] ] by the id-preserving structural "
         "adapter (world_scroll.wrap_state), not the DC+·INS chain. Unlike "
         "bfo_core/colore_field this import IS EGIF-expressible — but the INS "
         "vehicle implies a reparse whose re-ordered siblings ELK packs past the "
         "geometric reader's inversion frontier (read_drawing no longer recovers "
         "the graph under ELK/peirce), while the id-preserving wrap keeps the "
         "drawn record invertible, as it was at sheet level. The stronger drawn "
         "property was kept over the two-step chain; content is same_graph-"
         "identical to the import and the residence is verified (scroll "
         "recognized, ligature-closed, m_view reads back identical).",
         ["residence", "world-scroll", "structural-wrap"]),
    )
    return chain, uod, prov, anns


def build_all() -> List[Tuple]:
    return [porphyry(), foaf(), sumo(), bfo(), colore_between(), colore_field(),
            skos_core()]


def main(argv=None) -> int:
    from tomos_service import TomosService

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    built = build_all()
    for chain, uod, prov, anns in built:
        prov.validate()
        if chain is not None:
            # §3.3 attests inside save_uod before any chain files are written
            service.save_uod_with_chain(uod, chain, provenance=prov.to_dict())
            how = f"{len(chain.steps)}-step DC+·INS residence chain"
        else:
            service.save_uod(uod)                   # §3.3 attests at the boundary
            service.save_provenance(uod, prov.to_dict())
            how = "structural residence (wrap_state; see annotations)"
        service.save_annotations(uod, anns)
        g = uod.current_egi
        print(f"  saved {uod.uod_id:16} kind=ontology  "
              f"V{len(g.V)} E{len(g.E)} Cut{len(g.Cut)}  [{how}]")
    print(f"\nimported {len(built)} ontologies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
