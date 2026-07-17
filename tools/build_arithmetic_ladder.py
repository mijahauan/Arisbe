"""
Seed the corpus with **the arithmetic ladder** — mathematics grown from the sheet,
rung by rung, so that each step teaches one device of the graphs and earns one
piece of mathematics with it (docs/MATHEMATICS_FROM_THE_SHEET.md).

Three UoDs, meant to be read in order:

1. ``peirce_order_1881`` — the order. Peirce's 1881 axioms (P1–P6) scribed as
   graphs on one sheet, together with a concrete stretch of the numbers for them
   to be true of. This is where a reader learns to *see* quantifiers: cut depth
   IS quantifier alternation, and the line of identity is the variable.

2. ``arithmetic_from_two_laws`` — addition. The successor chain, and two drawn
   laws. Materializing them **grows the whole addition table on the sheet**;
   `2 + 3 = 5` is then read off the diagram, not typed in. The audited proposal
   is `(sum "2" "3" "5")` — so the Organon audit lens shows the claim going from
   UNKNOWN (before the laws act) to TRUE (after). Peirce's *corollarial*
   reasoning, performed.

3. ``numeral_three_unfolds`` — the numeral. "Three" is not an object but a
   *place*: a definition that unfolds to three steps up from zero, and folds back.
   A diagram is a type, shown through a token.

The chains are real ``TransformationChain``s (each rung a recorded step), so the
ladder is browsable move-by-move in Organon, and its *character* is computable
(``proof_character``: these are corollarial — nothing enters that the definitions
did not already contain).

Original to Arisbe, low warrant; the mathematics is Peirce's. Import-safe.
"""

import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import peirce_arithmetic as pa
from annotations import SCOPE_CHAIN, SCOPE_STEP, SCOPE_UOD, annotations_to_list, make_annotation
from m_steps import peel_step
from world_scroll import wrap_m
from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from proof_authoring import ProofChain
from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
from semantic_game import evaluate
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory

UPTO = 5
PROPOSAL = pa.sum_claim(2, 3, 5)          # (sum "2" "3" "5")


def _scribe(egif: str):
    """A composing move under the validity discipline: admit the graph into the
    standing world-scroll's negative arena — a genuine INS (supposing an axiom
    is rule-licensed; adopting it is still the mathematician's act)."""
    from world_scroll import enlarge_m
    return lambda g: enlarge_m(g, egif)


def _verdict(egi, claim: str = PROPOSAL, *, closed: bool = True) -> str:
    """Peel the audited claim. **Both readings are worth seeing**, and the ladder
    shows them: *closed* (the default the audit lens uses) says the bare
    successor-chain HAS no addition, so `2 + 3 = 5` is FALSE *of that system* —
    the laws are what make it true, which is Peirce's whole point (mathematics
    traces the consequences of hypotheses). *Open* says UNKNOWN — the sheet is
    merely silent. Neither is a defect; they answer different questions."""
    facts, _ = materialize_egi(egi)
    oracle = CorpusOracle([("M", facts)], closed=closed)
    return evaluate(parse_egif(claim), oracle, closed=closed).verdict.value


# --------------------------------------------------------------------------- #
# 1 · the order                                                                #
# --------------------------------------------------------------------------- #

def build_order_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Rungs 1–3: a relation, the scroll, the order. Each axiom is one move, so a
    reader watches the order *assemble* rather than meeting it whole."""
    pc = ProofChain(wrap_m(parse_egif(pa.order_facts(UPTO)))[0])  # s0: the `lt` stretch
    for name, egif, gloss in pa.ORDER_AXIOMS:
        pc.apply_derived("ADMIT_TO_M", _scribe(egif),
                         note=f"{name} — {gloss}",
                         params={"axiom": name, "egif": egif,
                                 "act": "m_enlargement", "earned": True,
                                 "derivation": ["INS"],
                                 "disposition": "new_fact", "mode": "convention"})
    return pc.to_uod(
        uod_id="peirce_order_1881",
        name="Peirce's order (On the Logic of Number, 1881)",
        description=(
            "The order, assembled one axiom at a time. Peirce's primitive is the "
            "*relative*, not the number: a number is a position in a relational "
            "system, so the system comes first. P1–P6 (Shields' reconstruction, "
            "proven equivalent to Dedekind and Peano) make the naturals a discrete "
            "linear order with a least element and no greatest — each scribed as an "
            "ordinary Beta graph over the single dyadic spot (lt x y). Read the "
            "cuts: a cut inside a cut is if–then, and cut DEPTH is quantifier "
            "alternation — P4 (each number has a next, with nothing between) is "
            "three cuts deep, and that is exactly its ∀∃¬∃ shape. The line of "
            "identity is the variable. Nothing here is a number yet; this is the "
            "ground on which numbers stand. See docs/MATHEMATICS_FROM_THE_SHEET.md."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


# --------------------------------------------------------------------------- #
# 2 · addition — two laws grow the table                                       #
# --------------------------------------------------------------------------- #

def build_addition_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Rungs 5 and 7: position, then addition. The claim `2 + 3 = 5` is UNKNOWN
    on the bare succ-chain and TRUE once the two laws are on the sheet — the
    audit lens shows arithmetic *arriving*."""
    pc = ProofChain(wrap_m(parse_egif(
        f"{pa.successor_chain(UPTO)} {pa.numbers(UPTO)}"))[0])    # s0: the positions
    peel_step(pc, PROPOSAL, closed=True,
              note="Before the laws: the bare successor-chain HAS no addition — "
                   "closed-world, 2+3=5 is FALSE of that system.")
    pc.apply_derived("ADMIT_TO_M", _scribe(pa.SUM_BASE),
                     note="x + 0 = x — the base of the recursion",
                     params={"law": "sum_base", "egif": pa.SUM_BASE,
                             "act": "m_enlargement", "earned": True,
                             "derivation": ["INS"],
                             "disposition": "generalization", "mode": "convention"})
    peel_step(pc, PROPOSAL, closed=True)
    pc.apply_derived("ADMIT_TO_M", _scribe(pa.SUM_STEP),
                     note=("x + s(y) = s(x + y) — the step. With this the whole "
                           "addition table follows by itself."),
                     params={"law": "sum_step", "egif": pa.SUM_STEP,
                             "act": "m_enlargement", "earned": True,
                             "derivation": ["INS"],
                             "disposition": "generalization", "mode": "convention"})
    peel_step(pc, PROPOSAL, closed=True,
              note="The claim ARRIVES: with both laws in the arena the table "
                   "grows itself and 2+3=5 is read off the diagram.")
    return pc.to_uod(
        uod_id="arithmetic_from_two_laws",
        name="Addition, grown from two drawn laws",
        description=(
            "A number is a *place*: the successor is a relation (existential graphs "
            "have no function symbols), and a numeral names a position in the chain. "
            "Then addition needs exactly two graphs — x + 0 = x, and "
            "x + s(y) = s(x + y). Forward-chaining them grows the ENTIRE addition "
            "table on the sheet; '2 + 3 = 5' is then *read off the diagram*, never "
            "typed in. That is Peirce's COROLLARIAL reasoning in his own words: "
            "nothing entered that the definitions did not already contain. Watch "
            "the audited claim (sum \"2\" \"3\" \"5\") ARRIVE as the second law lands — "
            "and pause on the two readings of that arrival: closed-world, the bare "
            "successor-chain HAS no addition, so the claim is FALSE *of that system* "
            "until the laws make it true (Peirce exactly: mathematics traces the "
            "consequences of hypotheses); open-world, the sheet is merely SILENT and "
            "the claim reads UNKNOWN. Commutativity, too, can be *seen* to hold across "
            "this stretch — but seeing it for EVERY number needs induction, and "
            "induction is where the sheet ends (a schema, not a graph). See "
            "docs/MATHEMATICS_FROM_THE_SHEET.md."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


# --------------------------------------------------------------------------- #
# 3 · the numeral                                                              #
# --------------------------------------------------------------------------- #

def build_numeral_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Rung 6: "three" is a definition — a *type*, shown through a token."""
    pc = ProofChain(wrap_m(parse_egif(
        '(succ "0" *a) (succ a *b) (succ b *k) (num k)'))[0])
    pc.apply_derived(
        "FOLD_NUMERAL",
        lambda g: wrap_m(parse_egif('(three *k) (num k)'))[0],
        note=("Fold the chain into the numeral: 'three' abbreviates 'three steps up "
              "from zero'. The abbreviation is conservative — unfolding returns the "
              "same graph (same_graph), so the numeral adds no content, only a name."),
        params={"definition": "three", "body": pa.NUMERAL_DEFINITIONS["three"],
                "act": "m_refold", "earned": True,
                "derivation": ["definition.fold"]},
    )
    return pc.to_uod(
        uod_id="numeral_three_unfolds",
        name="The numeral 'three' — a place, folded into a name",
        description=(
            "Peirce: a diagram is a TYPE, and can only be shown through a replica of "
            "it — a TOKEN. So it is with a numeral. '3' is not an object the sheet "
            "contains; it is the third position in the order, and the numeral is a "
            "*definition* that folds that chain into one spot and unfolds it back "
            "again, losing nothing (the fold is checked conservative by same_graph). "
            "This is why arithmetic can be practical and logical at once: the numeral "
            "is a working abbreviation, and the logic underneath it is always "
            "recoverable — one click of 'unfold'."
        ),
        category=UoDCategory.DOMAIN_MODEL,
    )


# --------------------------------------------------------------------------- #

def _provenance() -> dict:
    return make_provenance(
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=[
            {"type": "article", "author": "Peirce, Charles Sanders",
             "title": "On the Logic of Number",
             "bibkey": "peirce1881logicofnumber",
             "note": "American Journal of Mathematics 4 (1881), 85–95 — the first "
                     "successful axiom system for the natural numbers"},
            {"type": "incollection", "author": "Carter, Jessica",
             "title": "Logic of Relations and Diagrammatic Reasoning: Structuralist "
                      "Elements in the Work of Charles Sanders Peirce",
             "bibkey": "carter2020logicofrelations",
             "note": "in Reck & Schiemer (eds.), The Prehistory of Mathematical "
                     "Structuralism, OUP 2020, ch. 10"},
            {"type": "incollection", "author": "Shields, Paul",
             "title": "Peirce's Axiomatization of Arithmetic",
             "bibkey": "shields1997axiomatization",
             "note": "in Houser et al. (eds.), Studies in the Logic of C. S. Peirce, "
                     "Indiana UP 1997 — the reconstruction P1–P6 used here"},
        ],
        kind=KIND_DOMAIN_MODEL,
    ).to_dict()


def _annotations(chain: TransformationChain, *, audit: bool) -> list:
    anns = []
    if audit:
        anns.append(make_annotation(SCOPE_UOD, PROPOSAL, tags=["audit-proposal"]))
    anns.append(make_annotation(
        SCOPE_CHAIN,
        "Each step ADMITS one graph into the standing world-scroll's arena (a "
        "genuine INS — the system resides at level 1; nothing contingent at depth "
        "0) — and adopting a hypothesis is "
        "ampliative, not deduction (proof_character reads this chain as AMPLIATIVE): "
        "no rule of inference compels you to adopt an axiom. Peirce exactly — "
        "mathematics 'frames and studies the consequences of hypotheses.' The "
        "COROLLARIAL reasoning is what happens next, when the laws are materialized "
        "and the addition table grows itself: THAT is the diagram doing the work, and "
        "nothing enters it that the definitions did not already contain.",
        tags=["ampliative", "corollarial", "mathematics", "teaching"]))
    for step in chain.steps:
        note = (step.user_annotation or step.rule_name)
        anns.append(make_annotation(SCOPE_STEP, note, step_id=step.step_id,
                                    tags=["rung"]))
    return annotations_to_list(anns)


def main(argv=None) -> int:
    from proof_character import character_of_chain

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)

    builders = [
        (build_order_chain, False),
        (build_addition_chain, True),
        (build_numeral_chain, False),
    ]
    for build, audit in builders:
        chain, uod = build()
        service.save_uod_with_chain(uod, chain, provenance=_provenance())
        service.save_annotations(uod, _annotations(chain, audit=audit))
        c = character_of_chain(chain)
        print(f"Saved '{uod.uod_id}' — {len(chain.steps)} rungs · {c.character}")

    # The headline the addition UoD exists to show: the claim ARRIVES — and the
    # two readings of its arrival are themselves a lesson. The closed reading is
    # the recorded PEEL trajectory; both are recomputed from the M-states.
    chain, _uod = build_addition_chain()
    states = [chain.initial_state_id] + [
        s.to_state_id for s in chain.steps
        if (s.parameters or {}).get("act") != "peel"]
    closed = [_verdict(chain.states[s]) for s in states]
    open_ = [_verdict(chain.states[s], closed=False) for s in states]
    peels = [s.parameters["verdict"] for s in chain.steps
             if (s.parameters or {}).get("act") == "peel"]
    assert peels == closed, (peels, closed)   # the record is earned
    print(f"\n  2 + 3 = 5, closed-world: {' → '.join(v.upper() for v in closed)}"
          "   (the system HAS no addition until the laws land)")
    print(f"  2 + 3 = 5, open-world:   {' → '.join(v.upper() for v in open_)}"
          "   (the sheet is merely silent)")
    assert closed == ["false", "false", "true"], closed
    assert open_ == ["unknown", "unknown", "true"], open_

    table, _ = pa.derive_sums(UPTO)
    print(f"  the two laws grew {len(table)} sums on the sheet "
          f"(e.g. {', '.join(str(f) for f in table if f.x=='2' and f.y=='3')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
