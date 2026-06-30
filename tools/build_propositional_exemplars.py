"""
Build a quartet of **propositional (Alpha) reasoning exemplars** as real
transformation chains — classic logical laws, each derived by legal Dau-rule
moves and saved into the tomos corpus for Organon to browse.

Together the four exercise **all six transformation rules**, so the set doubles
as a tour of the calculus:

    de_morgan               ¬(P∧Q) ⊢ ¬P∨¬Q          DC+, DC+
    contraposition          P→Q   ⊢ ¬Q→¬P            DC+              (one move!)
    ex_falso_quodlibet      ¬P    ⊢ P→Q              INS
    hypothetical_syllogism  P→Q, Q→R ⊢ P→R           IT+, IT-, DC-, ERA, ERA

Two of these teach an EG-specific insight worth more than the theorem:

  * **Contraposition is one DC+.** In EG, ``P→Q`` and ``¬Q→¬P`` are the *same
    graph* up to a double cut — ``~[ (P) ~[(Q)] ]`` ≡ ``~[ ~[~[(P)]] ~[(Q)] ]``.
    The "proof" is a single double-cut insertion; the contrapositive isn't
    derived so much as *read off the same picture*.
  * **De Morgan is the double-cut law.** A disjunction ``A∨B`` is drawn
    ``~[ ~[A] ~[B] ]``, so ``¬P∨¬Q`` is literally ``~[ (P) (Q) ]`` with a double
    cut grown around each conjunct — De Morgan's equivalence is two DC+ moves.

Built on the authoring layer (``proof_authoring.ProofChain`` + ``eg_navigation``):
selections are named by structure, the chain bookkeeping is automatic. Each
derivation is original to Arisbe (a real Peircean chain, ``docs/CHAIN_OF_SEMIOSIS.md``),
the theorem itself classical and cited. Import-safe; run as a script to seed
the corpus.
"""

import sys
from pathlib import Path
from typing import Callable, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import SCOPE_CHAIN, SCOPE_STEP, SCOPE_UOD, annotations_to_list, make_annotation
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from provenance import KIND_PROOF, authored_proof, make_provenance
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import UniverseOfDiscourse

# Methods shared by every authored Alpha derivation here.
_METHODS = [
    {"type": "book", "author": "Dau, Frithjof",
     "title": "The Logic System of Concept Graphs with Negation", "year": "2003",
     "bibkey": "dau2003logic", "note": "the six-rule formalization Arisbe enforces"},
    {"type": "book", "author": "Roberts, Don D.",
     "title": "The Existential Graphs of Charles S. Peirce", "year": "1973",
     "note": "EG rule presentation"},
]


# =========================================================================== #
# 1. De Morgan — ¬(P∧Q) ⊢ ¬P∨¬Q                                               #
# =========================================================================== #

def build_de_morgan() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """``~[ (P) (Q) ]`` (not both P and Q) grows a double cut around each
    conjunct, reaching ``~[ ~[~[(P)]] ~[~[(Q)]] ]`` = ¬P ∨ ¬Q."""
    def cut(g):
        return nav.child_cuts(g, g.sheet)[0]
    def p_edge(g):
        return nav.child_edges(g, cut(g), "P")[0]
    def q_edge(g):
        return nav.child_edges(g, cut(g), "Q")[0]
    author = (
        ProofChain.from_egif("~[ (P) (Q) ]")
        .apply("DC+", select=p_edge, into=cut, label="3i",
               note="Grow a double cut around P — turning the conjunct into ¬¬P, "
                    "the first disjunct of the De Morgan dual.")
        .apply("DC+", select=q_edge, into=cut, label="3i",
               note="Grow a double cut around Q likewise. The sheet now reads "
                    "~[ ~[¬P] ~[¬Q] ] = ¬P ∨ ¬Q.")
    )
    return author.to_uod(
        uod_id="de_morgan",
        name="De Morgan (¬(P∧Q) ⊢ ¬P∨¬Q)",
        description=(
            "De Morgan's law in Existential Graphs: the negation of a "
            "conjunction equals the disjunction of the negations. Because a "
            "disjunction A∨B is drawn ~[ ~[A] ~[B] ], the law is just the "
            "double-cut equivalence — two DC+ moves grow a double cut around "
            "each conjunct of ~[ (P) (Q) ], reaching ~[ ~[~[(P)]] ~[~[(Q)]] ]. "
            "A worked demonstration that EG disjunction is a double-negated form."
        ),
    )


def de_morgan_provenance() -> dict:
    return make_provenance(
        theorem_source={"type": "book", "author": "De Morgan, Augustus",
                        "title": "Formal Logic", "year": "1847",
                        "note": "De Morgan's laws"},
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHODS, kind=KIND_PROOF,
    ).to_dict()


def de_morgan_annotations() -> List[dict]:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "De Morgan's law is not a separate axiom in EG — it falls out of how "
            "disjunction is drawn. ¬P∨¬Q is ~[ ~[¬P] ~[¬Q] ], and ¬¬X is X under a "
            "double cut, so ¬(P∧Q) = ~[ (P)(Q) ] becomes ¬P∨¬Q by growing a double "
            "cut around each conjunct.",
            tags=["alpha", "cited", "double-cut", "disjunction"]),
        make_annotation(SCOPE_CHAIN,
            "Two DC+ moves, each meaning-preserving (a double cut adds nothing). "
            "The equivalence runs both ways: DC- twice returns the conjunction.",
            tags=["strategy"]),
    ])


# =========================================================================== #
# 2. Contraposition — P→Q ⊢ ¬Q→¬P  (one move)                                 #
# =========================================================================== #

def build_contraposition() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """``~[ (P) ~[(Q)] ]`` (P→Q) becomes its contrapositive ¬Q→¬P with a single
    double cut around P — they are the *same graph* (¬(P∧¬Q))."""
    def cut(g):
        return nav.child_cuts(g, g.sheet)[0]
    def p_edge(g):
        return nav.child_edges(g, cut(g), "P")[0]
    author = (
        ProofChain.from_egif("~[ (P) ~[ (Q) ] ]")
        .apply("DC+", select=p_edge, into=cut, label="3i",
               note="Grow a double cut around P, giving ~[ ~[~[(P)]] ~[(Q)] ] = "
                    "¬(P∧¬Q) — the very same proposition, now wearing the scroll "
                    "shape of ¬Q→¬P.")
    )
    return author.to_uod(
        uod_id="contraposition",
        name="Contraposition (P→Q ⊢ ¬Q→¬P)",
        description=(
            "Contraposition in Existential Graphs — and the EG insight that it is "
            "almost free: P→Q and ¬Q→¬P are the *same graph* up to a double cut, "
            "both ¬(P∧¬Q). Starting from the scroll ~[ (P) ~[(Q)] ], one DC+ around "
            "P yields ~[ ~[~[(P)]] ~[(Q)] ], which reads as the scroll 'if ¬Q then "
            "¬P'. The contrapositive isn't derived so much as read off the same "
            "picture — a vivid case of the diagram being the proposition."
        ),
    )


def contraposition_provenance() -> dict:
    return make_provenance(
        theorem_source={"type": "book", "author": "Aristotle",
                        "title": "Prior Analytics", "year": "c. 350 BCE",
                        "note": "contraposition (conversion by contradiction)"},
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHODS, kind=KIND_PROOF,
    ).to_dict()


def contraposition_annotations() -> List[dict]:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "The classic equivalence of a conditional with its contrapositive. In a "
            "symbolic calculus this needs several steps; in EG both forms are one and "
            "the same graph ¬(P∧¬Q), differing only by where you draw a (logically "
            "inert) double cut. The single DC+ makes the contrapositive's scroll shape "
            "literal.",
            tags=["alpha", "cited", "double-cut", "iconicity"]),
    ])


# =========================================================================== #
# 3. Ex falso quodlibet — ¬P ⊢ P→Q                                           #
# =========================================================================== #

def build_ex_falso() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """From ``~[ (P) ]`` (¬P), insert ``~[ (Q) ]`` into the negative cut, reaching
    ``~[ (P) ~[(Q)] ]`` = P→Q — anything follows from a denied antecedent."""
    def cut(g):
        return nav.child_cuts(g, g.sheet)[0]
    author = (
        ProofChain.from_egif("~[ (P) ]")
        .apply("INS", insert="~[ (Q) ]", into=cut, label="1i",
               note="Insert ¬Q into the negative cut beside P. Insertion is legal "
                    "in any negative context, and it builds the consequent of the "
                    "scroll ~[ (P) ~[(Q)] ] = P→Q.")
    )
    return author.to_uod(
        uod_id="ex_falso_quodlibet",
        name="Ex falso quodlibet (¬P ⊢ P→Q)",
        description=(
            "From a denied antecedent, anything follows: ¬P ⊢ (P→Q). The proof is a "
            "single insertion — ~[ (P) ] (which is ¬P, and also the empty scroll's "
            "antecedent) admits ~[ (Q) ] into its negative interior by the insertion "
            "rule, producing the scroll ~[ (P) ~[(Q)] ] = P→Q. A clean illustration "
            "of the one place insertion is licensed: inside a negative context, where "
            "you may entertain anything without yet asserting it."
        ),
    )


def ex_falso_provenance() -> dict:
    return make_provenance(
        theorem_source={"type": "book", "author": "Duns Scotus (attrib.)",
                        "title": "ex contradictione / falso quodlibet", "year": "c. 1300",
                        "note": "the principle of explosion"},
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHODS, kind=KIND_PROOF,
    ).to_dict()


def ex_falso_annotations() -> List[dict]:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "The principle of explosion, drawn. The single move is the insertion "
            "rule (INS), which is legal precisely — and only — in a negative "
            "context: you may scribe anything inside an odd number of cuts, because "
            "there it is entertained, not asserted (docs/LEVEL_ZERO_AND_THE_REGISTERS.md).",
            tags=["alpha", "insertion", "negative-context"]),
    ])


# =========================================================================== #
# 4. Hypothetical syllogism — P→Q, Q→R ⊢ P→R                                  #
# =========================================================================== #

def build_hypothetical_syllogism() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Transitivity of implication, the meaty one: iterate Q→R into P→Q, splice
    the two together by deiteration, then clear the scaffolding."""
    def A(g):       # P→Q
        return nav.cut_holding_relation(g, g.sheet, "P")
    def B(g):       # Q→R
        return nav.cut_holding_relation(g, g.sheet, "Q")
    def innerQ(g):  # the ~[(Q)] inside A
        return nav.cut_holding_relation(g, A(g), "Q")
    def b_copy_q(g):  # the Q inside the iterated copy of B
        return nav.child_edges(g, nav.child_cuts(g, innerQ(g))[0], "Q")[0]
    def dbl(g):     # the ~[ ~[(R)] ] left after deiteration
        return nav.child_cuts(g, innerQ(g))[0]
    def q_in_inner(g):  # the surviving Q at positive depth, now removable
        return nav.child_edges(g, innerQ(g), "Q")[0]
    author = (
        ProofChain.from_egif("~[ (P) ~[ (Q) ] ] ~[ (Q) ~[ (R) ] ]")
        .apply("IT+", select=B, into=innerQ, label="2i",
               note="Iterate the premise Q→R into the inner cut of P→Q (the area "
                    "holding its Q), so the two scrolls overlap on Q.")
        .apply("IT-", select=b_copy_q, label="2e",
               note="Deiterate the copied Q against the Q already there, leaving "
                    "~[ ~[(R)] ] — R under a double cut.")
        .apply("DC-", select=dbl, label="3e",
               note="Remove that double cut, landing R beside Q: P→(Q∧R).")
        .apply("ERA", select=q_in_inner, label="1e",
               note="Erase Q (it sits in a positive context now), leaving P→R inside "
                    "the first scroll.")
        .apply("ERA", select=B, label="1e",
               note="Erase the spent Q→R premise from the sheet, leaving the "
                    "conclusion P→R standing alone.")
    )
    return author.to_uod(
        uod_id="hypothetical_syllogism",
        name="Hypothetical Syllogism (P→Q, Q→R ⊢ P→R)",
        description=(
            "Transitivity of implication — the chain rule for conditionals. Five "
            "legal moves splice two scrolls into one: iterate Q→R into the body of "
            "P→Q (IT+), deiterate the shared Q (IT-), peel the resulting double cut "
            "(DC-) to reach P→(Q∧R), erase the now-positive Q (ERA) to get P→R, and "
            "erase the spent second premise (ERA). The substantial derivation of the "
            "set — every step a real, attestable Dau-rule application."
        ),
    )


def hypothetical_syllogism_provenance() -> dict:
    return make_provenance(
        theorem_source={"type": "book", "author": "Chrysippus / the Stoics",
                        "title": "hypothetical syllogism (the chain argument)",
                        "year": "c. 250 BCE",
                        "note": "transitivity of the conditional"},
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHODS, kind=KIND_PROOF,
    ).to_dict()


def hypothetical_syllogism_annotations() -> List[dict]:
    return annotations_to_list([
        make_annotation(SCOPE_UOD,
            "The transitivity of implication, drawn. Unlike the other three exemplars "
            "(each one or two moves), this is a genuine multi-step derivation, showing "
            "iteration and deiteration doing the real work of splicing two conditionals "
            "on their shared middle term Q.",
            tags=["alpha", "cited", "iteration", "transitivity"]),
        make_annotation(SCOPE_CHAIN,
            "The crux is steps 1–2: iterating Q→R inside P→Q and then deiterating the "
            "duplicated Q is the EG form of 'discharge the middle term'. Everything "
            "after is bookkeeping — peel the double cut, erase the spent material.",
            tags=["strategy"]),
        make_annotation(SCOPE_STEP,
            "Iteration places a copy of the second premise exactly where it can meet "
            "the first premise's consequent — the move that makes the splice possible.",
            step_id="step-1", tags=["crux"]),
    ])


# =========================================================================== #
# Registry + driver                                                           #
# =========================================================================== #

# (build_fn, conclusion_egif, provenance_fn, annotations_fn)
EXEMPLARS: List[Tuple[Callable, str, Callable, Callable]] = [
    (build_de_morgan, "~[ ~[ ~[ (P) ] ] ~[ ~[ (Q) ] ] ]",
     de_morgan_provenance, de_morgan_annotations),
    (build_contraposition, "~[ ~[ (Q) ] ~[ ~[ (P) ] ] ]",
     contraposition_provenance, contraposition_annotations),
    (build_ex_falso, "~[ (P) ~[ (Q) ] ]",
     ex_falso_provenance, ex_falso_annotations),
    (build_hypothetical_syllogism, "~[ (P) ~[ (R) ] ]",
     hypothetical_syllogism_provenance, hypothetical_syllogism_annotations),
]


def main(argv=None) -> int:
    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    for build, conclusion, prov_fn, anns_fn in EXEMPLARS:
        chain, uod = build()
        assert nav.same_graph(uod.current_egi, parse_egif(conclusion)), (
            f"built proof '{uod.uod_id}' does not match {conclusion}"
        )
        service.save_uod_with_chain(uod, chain, provenance=prov_fn())  # §3.3 attests
        service.save_annotations(uod, anns_fn())
        rules = " → ".join(s.rule_name for s in chain.steps)
        print(f"Saved '{uod.uod_id}': {len(chain.steps)} steps ({rules}) → {conclusion}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
