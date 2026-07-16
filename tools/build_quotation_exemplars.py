"""
Build the **quotation exemplars** — the author-blessed slate (2026-07-16) that
crosses the second-order frontier *exemplar-first*. Built at Stage ⓪ on the
overlay stratum; **re-expressed at stage ① B-min** (the authorized core
opening): the sort and the quotation oval now live in the core
(``egi_core_dau.sort``/``.quotation``), each scribing is an explicit QUOTE
chain step, the drawn ovals are committed dotted ink (not chrome), and **S3
(read-back one order up) is CHECKED** wherever the quoted graph is drawn —
the cross-UoD mention's quoted-half stays a named horizon.

Design of record: docs/CROSSING_DECISION_BRIEFS.md (the verdicts) +
docs/SECOND_ORDER_CORE_OPENING.md §5 step 1 (the overlay rung). Three
commentary UoDs, each housing its claims at level 1 of a standing world-scroll
(the validity discipline: nothing contingent at depth 0; DC+ · INS, the gapless
inbound construction) and each carrying a **quotation overlay** — a
proposition-sorted name whose quoted graph resolves and attests:

1. ``swan_third_tense`` — **the swan's third tense.** ``(superseded
   "M_swan_law" "Nox")``: the law ``~[ (swan *x) ~[ (white x) ] ]`` withdrawn
   from ``dialogue_swan_revision`` held before the mind as a *labeled exhibit* —
   present **without force** (first order cannot do this: a double cut around
   old-M still binds). The name resolves via the withdrawal step's own record
   (``REVISE_M``'s ``subgraph_egif``) and, per state (S5, Cohen's R_G), against
   the drawn law at s4–s7 — the horizon (s0–s3, s8–s9) named, never silent.
2. ``forcing_forces`` — **``(forces s φ)``**, the imported-exact nominee under
   the **Montague rider**: ``forces`` enters only as a *defined, grounded,
   decidable* relation (the peel at s; ``modal_query.settlement`` for the
   trajectory) — never an axiomatized primitive with reflection schemas. The
   forcing trichotomy as drawn, state-indexed claims over
   ``forcing_conditions``: ∅ forces *one* (settled — the S5 trajectory resolves
   φ₁ at **every** state), ⟨1,1,0⟩ forces *zero* (open — φ₂ resolves on **one
   branch**), nothing forces *two* (excluded — φ₃ resolves **nowhere**; the
   whole trajectory is horizon). Every claim is recomputed before it is scribed.
3. ``peirce_law_commentary`` — **cross-UoD mention.** A commentary naming
   ``peirce_law`` as *object* (the reference-node increment-2 fork's mention
   side, exercised overlay-first): the quoted graph is the whole theorem UoD's
   graph, resolved without importing one element of it (mention, not use — no
   co-assertion), carrying the real scholarly citation
   (``scholarly_citation.citation_for`` → Peirce 1885).

Every quotation is **attested at build time** (S1 stratification off the drawn
enclosure; S2 quote-equals-quoted against an independent ground + §3.3 one
level down through the real ELK engine; S3 read-back through the second-order
reader where the quoted graph is drawn; S5 per state; S4 horizons named) — the
builder refuses to save what does not recompute. Original to Arisbe, low
warrant. See docs/EXEMPLARS.md.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import SCOPE_CHAIN, SCOPE_UOD, annotations_to_list, make_annotation
from domain_oracle import CorpusOracle
from eg_navigation import same_graph, vertex_by_label
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from modal_query import scribes_relation, settlement
from proof_authoring import ProofChain
from provenance import KIND_EXEMPLAR, authored_proof, make_provenance
from quotation_overlay import (
    ChainStepQuotationResolver,
    EGIFQuotationResolver,
    QuotationMark,
    UoDQuotationResolver,
    attest_quotation_mark,
    attest_quotation_mark_trajectory,
    mark_quotation,
    quotation_marks_to_list,
    quote_step,
    render_quotation_marks,
    run_quotation_mark,
    run_quotation_mark_trajectory,
    sort_step,
)
from second_order_reader import read_quotation_back
from second_order_check import Quotation, run_quotation_trajectory
from semantic_game import evaluate
from simple_svg_renderer import SimpleSVGRenderer
from tomos_service import TomosService
from universe_of_discourse import UoDCategory
from world_scroll import m_view

TOMOS_ROOT = Path(__file__).resolve().parent.parent / "tomos"

SWAN_UOD = "swan_third_tense"
SWAN_LAW = "~[ (swan *x) ~[ (white x) ] ]"
SWAN_CONTENT = '(superseded "M_swan_law" "Nox")'

FORCES_UOD = "forcing_forces"
FORCES_CONTENT = (
    '(forces "s0" "phi-one") (forces "s6" "phi-zero") '
    '~[ (forces *s "phi-two") ]'
)
PHI = {
    "phi-one": ("one", "(one *p)"),
    "phi-zero": ("zero", "(zero *p)"),
    "phi-two": ("two", "(two *p)"),
}

MENTION_UOD = "peirce_law_commentary"
MENTION_CONTENT = '(cites "peirce_law" "Peirce-1885")'
PEIRCE_LAW_GROUND = "~[ ~[ ~[ (P) ~[ (Q) ] ] ~[ (P) ] ] ~[ (P) ] ]"


def _layout_fn(egi):
    """The real ELK path — S2's §3.3 half runs against the engine that serves."""
    from web_api.services.layout_service import generate_layout

    dto, _svg = generate_layout(egi)
    return dto


def _residence(content_egif: str) -> ProofChain:
    """The gapless inbound construction (build_ontologies' pattern): DC+ opens
    the standing scroll (asserts nothing), INS supposes the commentary into its
    negative antecedent area — nothing contingent stands at depth 0."""
    pc = ProofChain.from_blank()
    pc.apply("DC+", into=lambda g: g.sheet,
             note="Open the standing scroll: an empty double cut asserts "
                  "nothing, and until it exists there is nowhere to hold a "
                  "commentary that is not an assertion at the world's level.")
    pc.apply("INS", insert=content_egif,
             into=lambda g: nav.child_cuts(g, g.sheet)[0],
             note="Suppose the commentary into the negative arena — insertion "
                  "is sound there, and the claims are fenced (low warrant).")
    return pc


def _glyph_export(service: TomosService, uod_id: str, egi, marks, resolver) -> None:
    """Render the exemplar once *with* its quotation glyphs — the dotted oval
    made real on the corpus exemplar (chrome only; the attested render path is
    unchanged). Written beside the saved record, wherever the service routed it."""
    dto = _layout_fn(egi)
    svg = SimpleSVGRenderer().render_to_svg(
        dto, egi=egi, quotation_marks=render_quotation_marks(marks, resolver))
    entry = service.get_uod_metadata(uod_id)
    out = service._entry_path(entry) / "exports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "quotation_glyph.svg").write_text(svg, encoding="utf-8")


def _verdict_at(state_egi, proposal_egif: str) -> str:
    """Peel a proposal against one state's M (closed-world: a condition is a
    finite, fully-revealed record) — the forces-claims' condition-local
    semantics, recomputed before scribing."""
    facts, _ = materialize_egi(m_view(state_egi))
    oracle = CorpusOracle([("M", facts)], closed=True)
    return evaluate(parse_egif(proposal_egif), oracle, closed=True).verdict.value


def build_swan_third_tense(service: TomosService) -> Tuple[str, List[str], List[str]]:
    """Exemplar (i): the withdrawn law as labeled exhibit. Returns
    (uod_id, S5 checked states, S5 horizon states)."""
    swan_chain = service.load_chain("dialogue_swan_revision")
    assert swan_chain is not None, "dialogue_swan_revision chain missing"
    withdrawal = next(s for s in swan_chain.steps if s.rule_name == "REVISE_M")

    pc = _residence(SWAN_CONTENT)
    # B-min: the exhibit is DRAWN — the name gains the core sort and a dotted
    # quotation oval holding the law's ink, recorded as an explicit QUOTE step
    # (neutral: a mention asserts nothing).
    quote_step(pc, "M_swan_law", SWAN_LAW,
               note="scribe the withdrawn law into a quotation oval beside "
                    "its name — present without force, now present in ink")
    host = pc.current
    name_vid = vertex_by_label(host, "M_swan_law")
    oval_id = next(c for c, v in host.quotation.items() if v == name_vid)

    resolver = ChainStepQuotationResolver(service)
    mark = mark_quotation(
        host, name_vid, f"dialogue_swan_revision#{withdrawal.step_id}", resolver,
        origin="dialogue_swan_revision",
        shape_egif=SWAN_LAW,
        note="the withdrawn swan law, present without force (the third tense)")

    ground = parse_egif(SWAN_LAW)
    # S1/S2 (+ §3.3 one level down, real ELK) AND S3 — the drawing itself
    # reads back the (sort, quoted) device via the second-order reader.
    host_dto = _layout_fn(host)
    attest_quotation_mark(
        host, mark, resolver, layout_fn=_layout_fn, quoted_ground=ground,
        read_back=lambda: read_quotation_back(host, host_dto, oval_id),
        context=SWAN_UOD)
    s3_report = run_quotation_mark(
        host, mark, resolver, layout_fn=_layout_fn, quoted_ground=ground,
        read_back=lambda: read_quotation_back(host, host_dto, oval_id))
    assert s3_report.read_back_faithful is True, s3_report.failures
    # S5 — the name's reference value per state (Cohen's R_G): the drawn law
    # recovered structurally at s4–s7, the rest named horizon.
    report = run_quotation_mark_trajectory(host, mark, SWAN_LAW, swan_chain.states)
    assert report.ok, report.failures
    assert report.checked_states == ["s4", "s5", "s6", "s7"], report.checked_states
    attest_quotation_mark_trajectory(host, mark, SWAN_LAW, swan_chain.states,
                                     layout_fn=_layout_fn, context=SWAN_UOD)

    chain, uod = pc.to_uod(
        uod_id=SWAN_UOD,
        name="The swan's third tense (superseded ⌜M_swan_law⌝)",
        description=(
            "The first drawable second-order exemplar (Stage ⓪, overlay): the "
            "swan law withdrawn in dialogue_swan_revision held before the mind "
            "as a labeled exhibit — (superseded \"M_swan_law\" \"Nox\") names "
            "the law without re-asserting it (present without force, the third "
            "tense of the validity discipline). At B-min the exhibit is DRAWN: "
            "the name carries the core proposition sort and a dotted quotation "
            "oval holds the law's ink — opaque to the calculus (no rule "
            "operates inside; the peel skips it). The name still resolves to "
            "~[ (swan *x) ~[ (white x) ] ] via the withdrawal step's own "
            "record, checked per state along the swan trajectory (S5): it "
            "stands drawn at s4–s7 and nowhere else — the horizon is named. "
            "S3 (read-back one order up) is CHECKED: the drawing reads back "
            "the (sort, quoted) device through the second-order reader."
        ),
        category=UoDCategory.CANONICAL_PATTERN,
    )
    service.save_uod_with_chain(uod, chain, provenance=make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        kind=KIND_EXEMPLAR).to_dict())
    service.save_annotations(uod, annotations_to_list([
        make_annotation(SCOPE_UOD,
            "Second-order stage ① (B-min, the authorized core opening): the "
            "homegrown nominee (superseded ⌜M⌝ reason). The exhibit says THAT "
            "the law was superseded (by the black swan Nox); the law itself "
            "appears only quoted — named, not asserted, drawn in a dotted "
            "quotation oval the calculus treats as opaque. Predicative (the "
            "quoted state sits strictly below the host), S1's always-legal "
            "case. Attested at build: S1 stratification off the drawn "
            "enclosure, S2 quote-equals-quoted + §3.3 one level down (real "
            "ELK), S3 read-back one order up (the drawing recovers the "
            "(sort, quoted) device — the stage-① reader), S5 per state "
            "(checked s4–s7; horizon s0–s3, s8–s9), S4 horizons named.",
            tags=["quotation", "second-order", "third-tense", "exemplar"]),
        make_annotation(SCOPE_CHAIN,
            "Residence by the gapless inbound construction (DC+ then INS): "
            "the commentary is supposed at level 1 of a standing scroll — "
            "nothing contingent at depth 0.",
            tags=["world-scroll", "low-warrant"]),
    ]))
    service.save_quotations(uod, quotation_marks_to_list([mark]))
    _glyph_export(service, SWAN_UOD, host, [mark], resolver)
    return SWAN_UOD, report.checked_states, report.unresolved_states


def _phi_per_state(
    host, mark: QuotationMark, rel: str, shape_egif: str,
    states: Dict[str, object],
) -> Dict[str, Optional[Quotation]]:
    """Per-state candidates for a forces-claim's φ: at each condition state, φ
    resolves iff the state's M scribes an atom of φ's relation (the
    condition-local reading) — else that state is horizon. The S5 shape of the
    trichotomy: settled resolves everywhere, open on one branch, excluded
    nowhere."""
    shape = parse_egif(shape_egif)
    out: Dict[str, Optional[Quotation]] = {}
    for sid, egi in states.items():
        view = m_view(egi)
        present = any(view.rel[e.id] == rel for e in view.E)
        if not present:
            out[sid] = None
            continue
        out[sid] = Quotation(
            name=f"{mark.target}@{sid}", sort=mark.sort, host=host,
            resolve=lambda g=shape: g, quoted_ground=shape,
            enclosed=True,  # the claims live at level 1 of the standing scroll
        )
    return out


def build_forcing_forces(service: TomosService) -> Tuple[str, Dict[str, List[str]]]:
    """Exemplar (ii): (forces s φ) under the Montague rider. Returns
    (uod_id, {phi_name: S5 checked states})."""
    fc_chain = service.load_chain("forcing_conditions")
    assert fc_chain is not None, "forcing_conditions chain missing"

    # Earn every claim before scribing it — the relation is DEFINED (peel /
    # settlement), never axiomatized (the Montague rider).
    assert _verdict_at(fc_chain.states["s0"], "(one *p)") == "true"
    assert _verdict_at(fc_chain.states["s6"], "(zero *p)") == "true"
    tri = {name: settlement(fc_chain, scribes_relation(rel)).status
           for name, (rel, _) in PHI.items()}
    assert tri == {"phi-one": "settled", "phi-zero": "open",
                   "phi-two": "excluded"}, tri

    pc = _residence(FORCES_CONTENT)
    # B-min: each φ is DRAWN — its name gains the core sort and a dotted
    # oval holding φ's shape, one explicit QUOTE step per claim.
    for name, (rel, shape) in PHI.items():
        quote_step(pc, name, shape,
                   note=f"scribe φ = {shape} into a quotation oval beside "
                        f"⌜{name}⌝")
    host = pc.current
    host_dto = _layout_fn(host)
    resolver = EGIFQuotationResolver()
    marks = []
    for name, (rel, shape) in PHI.items():
        vid = vertex_by_label(host, name)
        marks.append(mark_quotation(
            host, vid, shape, resolver, origin="forcing_conditions",
            relation=rel, settlement=tri[name]))

    oval_of = {v: c for c, v in host.quotation.items()}
    checked: Dict[str, List[str]] = {}
    for mark in marks:
        # S1/S2 (+ §3.3 one level down) AND S3 per claim — the drawn oval
        # reads back φ through the second-order reader.
        oval = oval_of[mark.element_id]
        attest_quotation_mark(
            host, mark, resolver, layout_fn=_layout_fn,
            quoted_ground=parse_egif(mark.target),
            read_back=lambda o=oval: read_quotation_back(host, host_dto, o),
            context=FORCES_UOD)
        # S5 — the trichotomy as trajectory-relative resolution.
        rel = mark.extra["relation"]
        per_state = _phi_per_state(host, mark, rel, mark.target, fc_chain.states)
        rep = run_quotation_trajectory(mark.target, per_state,
                                       layout_fn=_layout_fn)
        assert rep.ok, rep.failures
        checked[mark.extra["relation"]] = rep.checked_states
    assert checked["one"] == sorted(fc_chain.states)          # settled: everywhere
    assert checked["zero"] == ["s6", "s7"]                    # open: one branch
    assert checked["two"] == []                               # excluded: nowhere

    chain, uod = pc.to_uod(
        uod_id=FORCES_UOD,
        name="Forces (state s forces the quoted graph φ)",
        description=(
            "The imported-exact second-order nominee (Stage ⓪, overlay): "
            "(forces s φ) with s a state-name of forcing_conditions and φ a "
            "quotation, its semantics DEFINED by existing machinery — the peel "
            "at s, modal_query.settlement for the trajectory — never an "
            "axiomatized primitive (the Montague rider). The trichotomy drawn: "
            "∅ forces one (settled), ⟨1,1,0⟩ forces zero (open), nothing "
            "forces two (excluded — drawn as the negation ~[ (forces *s "
            "\"phi-two\") ]). At B-min each φ is DRAWN: its name carries the "
            "core proposition sort and a dotted oval holds φ's shape (opaque "
            "to the calculus). Every claim recomputed before scribing; S3 "
            "checked (each oval reads back its φ); S5 reads the trichotomy as "
            "trajectory-relative resolution (φ₁ everywhere, φ₂ on one branch, "
            "φ₃ nowhere — the whole trajectory horizon)."
        ),
        category=UoDCategory.CANONICAL_PATTERN,
    )
    service.save_uod_with_chain(uod, chain, provenance=make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "incollection",
             "author": "Caterina, Gianluca and Gangle, Rocco",
             "title": "Consequences of a Diagrammatic Representation of Paul "
                      "Cohen's Forcing Technique Based on C.S. Peirce's "
                      "Existential Graphs",
             "bibkey": "caterina2010forcing"},
            {"type": "article", "author": "Montague, Richard",
             "title": "Syntactical Treatments of Modality, with Corollaries on "
                      "Reflexion Principles and Finite Axiomatizability",
             "bibkey": "montague1963syntactical",
             "note": "the rider: forces enters as a defined, grounded, "
                     "decidable relation — never an axiomatized predicate on "
                     "sentence names with reflection schemas"},
        ],
        kind=KIND_EXEMPLAR).to_dict())
    service.save_annotations(uod, annotations_to_list([
        make_annotation(SCOPE_UOD,
            "Second-order stage ① (B-min): the forcing trichotomy as drawn, "
            "state-indexed claims. forces(s, φ) is decidable over finite "
            "objects, and at B-min its S3 read-back RUNS: each φ's dotted "
            "oval reads back its shape through the second-order reader. The "
            "excluded case is a genuine drawn negation: no state forces "
            "⌜(two *p)⌝. Attested at build: claims recomputed via the peel + "
            "settlement; S1/S2 (+ §3.3 one level down) + S3 per claim; S5 = "
            "the trichotomy read as trajectory-relative resolution.",
            tags=["quotation", "second-order", "forcing", "exemplar"]),
        make_annotation(SCOPE_CHAIN,
            "Residence by the gapless inbound construction (DC+ then INS); "
            "the forces-claims are fenced at level 1 (low warrant, earned by "
            "recomputation, not asserted at the world's level).",
            tags=["world-scroll", "low-warrant"]),
    ]))
    service.save_quotations(uod, quotation_marks_to_list(marks))
    _glyph_export(service, FORCES_UOD, host, marks, resolver)
    return FORCES_UOD, checked


def build_peirce_law_commentary(service: TomosService) -> Tuple[str, str]:
    """Exemplar (iii): cross-UoD mention. Returns (uod_id, citation line)."""
    import json

    pc = _residence(MENTION_CONTENT)
    # B-min: the cross-UoD mention's name gains the CORE sort but no oval —
    # a whole other universe cannot inline, so the quoted graph stays a
    # resolver-served, S4-named horizon (S3's sort-half is committed drawn
    # ink held total by §3.3; its quoted-half stays honestly skip-named).
    sort_step(pc, "peirce_law", target="peirce_law",
              note="sort ⌜peirce_law⌝ — mention by name, the oval-less state")
    host = pc.current
    name_vid = vertex_by_label(host, "peirce_law")

    prov_path = TOMOS_ROOT / "universes" / "peirce_law" / "provenance.json"
    from scholarly_citation import citation_for
    cite = citation_for(provenance=json.loads(prov_path.read_text()))
    assert cite["has_source"], "peirce_law should carry a theorem_source"

    resolver = UoDQuotationResolver(service)
    mark = mark_quotation(
        host, name_vid, "peirce_law", resolver, origin="tomos",
        bibkey=cite.get("key"),
        note="mention, not use: the theorem named as object, no element imported")

    # The independent ground: the theorem's shape hand-written, not loaded
    # through the resolver's path — S2 has teeth.
    ground = parse_egif(PEIRCE_LAW_GROUND)
    attest_quotation_mark(host, mark, resolver, layout_fn=_layout_fn,
                          quoted_ground=ground, context=MENTION_UOD)
    report = run_quotation_mark(host, mark, resolver, layout_fn=_layout_fn,
                                quoted_ground=ground)
    assert report.ok and report.read_back_faithful is None  # S3 named, not passed

    chain, uod = pc.to_uod(
        uod_id=MENTION_UOD,
        name="Commentary on Peirce's law (cross-UoD mention)",
        description=(
            "The reference-node increment-2 fork's MENTION side, exercised "
            "overlay-first (Stage ⓪): a commentary UoD naming peirce_law as "
            "object — (cites \"peirce_law\" \"Peirce-1885\") — where the name "
            "is a quotation overlay resolving to the whole theorem graph "
            "((P⊃Q)⊃P)⊃P without importing one element of it. Mention is not "
            "use: resolution produces the quoted graph for checking, never "
            "splices it (no co-assertion across universes). Carries the real "
            "scholarly citation (Peirce 1885, On the Algebra of Logic)."
        ),
        category=UoDCategory.CANONICAL_PATTERN,
    )
    service.save_uod_with_chain(uod, chain, provenance=make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        kind=KIND_EXEMPLAR).to_dict())
    service.save_annotations(uod, annotations_to_list([
        make_annotation(SCOPE_UOD,
            f"Second-order Stage ⓪, the mention side of the use/mention fork: "
            f"the quoted object is another UoD's graph, addressed by its "
            f"corpus id. Citation (via scholarly_citation): {cite['citation']} "
            f"Attested at build: S1 (predicative — the quoted theorem sits in "
            f"another universe, no reach-back), S2 against a hand-written "
            f"independent ground + §3.3 one level down (real ELK). At B-min "
            f"the name carries the CORE proposition sort (drawn badge, "
            f"§3.3-total); S3's quoted-half stays honestly skip-named — a "
            f"cross-UoD mention draws no oval (the named B-min horizon).",
            tags=["quotation", "second-order", "mention", "citation", "exemplar"]),
        make_annotation(SCOPE_CHAIN,
            "Residence by the gapless inbound construction (DC+ then INS): a "
            "scholarly commentary is supposed, not asserted at depth 0.",
            tags=["world-scroll", "low-warrant"]),
    ]))
    service.save_quotations(uod, quotation_marks_to_list([mark]))
    _glyph_export(service, MENTION_UOD, host, [mark], resolver)
    return MENTION_UOD, cite["citation"]


def main(argv=None) -> int:
    service = TomosService(TOMOS_ROOT)

    uid, checked, horizon = build_swan_third_tense(service)
    print(f"Saved '{uid}' — the withdrawn law as labeled exhibit.")
    print(f"  S5: law drawn at {checked}; horizon {horizon}")

    uid, tri_checked = build_forcing_forces(service)
    print(f"Saved '{uid}' — (forces s φ) under the Montague rider.")
    for rel, states in tri_checked.items():
        word = {"one": "settled", "zero": "open", "two": "excluded"}[rel]
        print(f"  S5 {word} ({rel}): resolves at {states or 'no state'}")

    uid, citation = build_peirce_law_commentary(service)
    print(f"Saved '{uid}' — cross-UoD mention with citation:")
    print(f"  {citation}")

    print("S3 (read-back one order up): CHECKED on swan + forcing (the "
          "drawing carries the sort and the oval reads back its quoted "
          "graph); the cross-UoD mention's quoted-half stays a named "
          "horizon — an oval cannot inline another universe (B-min limit).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
