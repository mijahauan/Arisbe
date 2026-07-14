"""**Mathematics from the sheet** — Peirce's arithmetic, built rung by rung in EGs.

Design-of-record: ``docs/MATHEMATICS_FROM_THE_SHEET.md``. Occasioned by Jessica
Carter, "Logic of Relations and Diagrammatic Reasoning" (in Reck & Schiemer eds.,
*The Prehistory of Mathematical Structuralism*, OUP 2020, ch. 10).

The point is not to *encode* arithmetic in EGs but to **grow** it, in the order
Peirce himself grows it, so that each step teaches one device of the graphs and
earns one piece of mathematics with it. Carter's thesis: for Peirce a number is
not an object but a **position in a relational system** — "the numbers are defined
as a relational system, that is, as a collection on which is defined a certain
order relation." Mathematics is then the *activity* of drawing necessary
conclusions by constructing a diagram, experimenting on it, and observing what
must be so.

The ladder (:data:`RUNGS`), each rung a graph you can draw and read:

  0. **the blank sheet** — asserts nothing. The one unconditioned context.
  1. **a relation** — `(lt "1" "2")`. Peirce's primitive is the *relative*, not
     the number. A dyadic spot with two hooks.
  2. **the scroll** — transitivity. A cut inside a cut is *if–then*; the line of
     identity carries the variable across the boundary. One picture, one law.
  3. **the order** — Peirce's 1881 axioms P1–P6: a discrete linear order with a
     least element and no greatest. Cut *depth* is quantifier alternation: this is
     where ∀ and ∃ are read off the drawing rather than written.
  4. **identity** — the line of identity *is* equality. (Where Arisbe departs from
     Peirce, and why: see :data:`EQUALITY_DEPARTURE`.)
  5. **position** — successor as a relation; "3" is *where you stand* in the
     order, not a thing you hold.
  6. **the numeral** — "3" as a *definition* that folds/unfolds to the succ-chain.
     Peirce: a diagram is a type, shown through a token.
  7. **addition** — two Horn laws. Materializing them *grows the whole addition
     table on the sheet*, and `2 + 3 = 5` is then read off it. **Corollarial**
     reasoning, in Peirce's exact sense: nothing entered that the definitions did
     not already contain.
  8. **the character of a proof** — corollarial vs theorematic, decided from the
     chain (``proof_character``). Peirce's deepest distinction, mechanized.
  9. **induction** — the least-number principle. Here first-order EG *stops*: the
     axiom quantifies over propositions, so it is a **schema** (``schema.py``'s
     φ-hole), not a graph. The honest edge of the sheet.

Everything here is ordinary Beta EG plus Horn materialization — no new primitive.
Rung 9 is the exception, and it is the exception *by name*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------- #
# Rungs 2–3 · the order (Peirce, "On the Logic of Number", 1881)              #
# Shields' reconstruction; proven equivalent to Dedekind (1888) / Peano (1889).#
# Primitive: the strict order `(lt x y)` — the *relative*, not the number.     #
# --------------------------------------------------------------------------- #

P1_IRREFLEXIVE = "~[ [*x] (lt x x) ]"
P2_TRANSITIVE = "~[ [*x] [*y] [*z] (lt x y) (lt y z) ~[ (lt x z) ] ]"
P3_TRICHOTOMY = "~[ [*x] [*y] ~[ (lt x y) ] ~[ (= x y) ] ~[ (lt y x) ] ]"
P4_DISCRETE = "~[ [*x] ~[ [*y] (lt x y) ~[ [*z] (lt x z) (lt z y) ] ] ]"
P5_LEAST = "[*x] ~[ [*y] ~[ (lt x y) ] ~[ (= x y) ] ]"
P6_NO_GREATEST = "~[ [*x] ~[ [*y] (lt x y) ] ]"

ORDER_AXIOMS = [
    ("P1 irreflexivity", P1_IRREFLEXIVE, "nothing is less than itself"),
    ("P2 transitivity", P2_TRANSITIVE, "the scroll: if x<y and y<z, then x<z"),
    ("P3 trichotomy", P3_TRICHOTOMY, "any two are ordered, or the same"),
    ("P4 discreteness", P4_DISCRETE, "each has a next — nothing squeezes between"),
    ("P5 least element", P5_LEAST, "the count starts somewhere"),
    ("P6 no greatest", P6_NO_GREATEST, "and never has to stop"),
]

# Rung 4 · the departure, named rather than smuggled.
EQUALITY_DEPARTURE = """\
For Peirce identity is not a relation but the **line of identity** itself: two
hooks joined by one continuous line ARE one individual — an icon of identity, not
a statement about it. That works perfectly where identity is *asserted*. It fails
where identity must be **concluded**: trichotomy and antisymmetry put "x = y" in
the consequent of a scroll, and you cannot make two lines become one line as the
*head* of an implication — a ligature is drawn or it is not; it is not inferred.

So the fixtures above use `(= x y)`, an equality **spot**, exactly as first-order
logic with equality does. This is a real departure from Peirce's iconicity and is
recorded as one (docs/FIDELITY_AND_DEPARTURES.md). What is kept: wherever identity
is merely asserted, Arisbe still draws it Peirce's way — as one shared line.
"""

# --------------------------------------------------------------------------- #
# Rungs 5–7 · position, numeral, addition                                     #
# No function symbols exist in EG, so the successor is a RELATION and a numeral#
# is a CONSTANT naming a position in the order.                               #
# --------------------------------------------------------------------------- #

# x + 0 = x.
SUM_BASE = '~[ (num *x) ~[ (sum x "0" x) ] ]'
# x + s(y) = s(x + y)  — recursion on the second argument, as Peirce defines it.
SUM_STEP = '~[ (sum *x *y *z) (succ y *sy) (succ z *sz) ~[ (sum x sy sz) ] ]'
SUM_LAWS = [SUM_BASE, SUM_STEP]

# The numeral as a DEFINITION (rung 6): "three" is not a thing, it is a place —
# the third step up from the least element. Unfolding it yields the succ-chain;
# folding it back gives the numeral. (definitions.Definition ports = ["n"].)
NUMERAL_DEFINITIONS = {
    "one": '(succ "0" *n)',
    "two": '(succ "0" *a) (succ a *n)',
    "three": '(succ "0" *a) (succ a *b) (succ b *n)',
}


def successor_chain(upto: int) -> str:
    """The order made concrete: 0 → 1 → … → upto, as ground `succ` facts.

    This is the *token* of the type: the axioms (P1–P6) say what an order IS; this
    is one stretch of one, laid on the sheet so we can compute in it."""
    if upto < 1:
        return ""
    return " ".join(f'(succ "{i}" "{i + 1}")' for i in range(upto))


def numbers(upto: int) -> str:
    """`(num "i")` for each position — the domain the laws range over."""
    return " ".join(f'(num "{i}")' for i in range(upto + 1))


def order_facts(upto: int) -> str:
    """The `lt` facts of that stretch, so the ORDER axioms have something to be
    true of (P2 transitivity is then observable, not merely asserted)."""
    return " ".join(f'(lt "{i}" "{j}")'
                    for i in range(upto + 1) for j in range(i + 1, upto + 1))


def arithmetic_theory(upto: int = 5, *, with_order: bool = False) -> str:
    """**The sheet a mathematician works on**: the numbers as positions, the
    successor that steps between them, and the two laws of addition.

    Materializing this grows the entire addition table (``derive_sums``); peeling
    a claim against it then *reads off* facts like `2 + 3 = 5` — Peirce's
    corollarial reasoning, performed. ``with_order`` also lays down the `lt`
    facts + the 1881 order axioms, so the order and the arithmetic are visibly
    one system."""
    parts = [successor_chain(upto), numbers(upto), SUM_BASE, SUM_STEP]
    if with_order:
        parts.append(order_facts(upto))
        parts.extend(a for _n, a, _g in ORDER_AXIOMS)
    return " ".join(p for p in parts if p)


@dataclass
class SumFact:
    """One entry of the derived addition table: ``x + y = z``."""
    x: str
    y: str
    z: str

    @property
    def egif(self) -> str:
        return f'(sum "{self.x}" "{self.y}" "{self.z}")'

    def __str__(self) -> str:
        return f"{self.x} + {self.y} = {self.z}"


def derive_sums(upto: int = 5) -> Tuple[List[SumFact], object]:
    """Forward-chain the two addition laws to the least Herbrand model — i.e.
    **grow the addition table on the sheet** — and return it, with the
    materialized EGI (the sheet as it now stands).

    This is the whole pedagogical point of rung 7: the table is not typed in. Two
    drawn laws plus the succ-chain *produce* it, and every entry is then a fact
    you can peel."""
    from egif_parser_dau import parse_egif
    from model_materialization import materialize_egi

    facts_egi, _report = materialize_egi(parse_egif(arithmetic_theory(upto)))
    out: List[SumFact] = []
    for eid, rel in facts_egi.rel.items():
        if rel != "sum":
            continue
        args = [facts_egi.get_vertex(v).label for v in facts_egi.nu[eid]]
        if len(args) == 3 and all(a is not None for a in args):
            out.append(SumFact(*args))
    out.sort(key=lambda f: (int(f.x), int(f.y)))
    return out, facts_egi


def check(claim_egif: str, upto: int = 5) -> str:
    """Peel a claim against the arithmetic — *read it off the diagram*.

    Returns the three-valued verdict ("true" / "false" / "unknown"). Closed-world:
    a finite stretch of the numbers is a complete record of itself."""
    from domain_oracle import CorpusOracle
    from egif_parser_dau import parse_egif
    from semantic_game import evaluate

    _facts, egi = derive_sums(upto)
    oracle = CorpusOracle([("arithmetic", egi)], closed=True)
    return evaluate(parse_egif(claim_egif), oracle, closed=True).verdict.value


def sum_claim(x: int, y: int, z: int) -> str:
    """The EGIF for `x + y = z` — the thing you ask the diagram."""
    return f'(sum "{x}" "{y}" "{z}")'


# --------------------------------------------------------------------------- #
# Rung 9 · where the sheet ends                                               #
# --------------------------------------------------------------------------- #

INDUCTION_SCHEMA = (
    "~[ [*x] <psi: x>\n"
    "   ~[ [*u] <psi: u>\n"
    "      ~[ [*y] <psi: y> (lt y u) ] ] ]"
)

INDUCTION_NOTE = """\
Peirce's induction is the **least-number principle**: every non-empty class of
numbers has a least member. Written out, it says "*for every property ψ* …" — and
there the sheet runs out. A first-order existential graph can quantify over
individuals (that is what a line of identity is) but it cannot quantify over
*propositions*: there is no line you can draw whose end is a graph.

So induction is not a graph but a **schema** — a graph with a hole (``schema.py``,
the φ-hole), plus an external rule licensing every instance. That is exactly how
PA and ZFC do it, and it is not a defeat: it is the precise location of the border
between the first order and the second, drawn where Peirce himself left it. The
frontier that would let the hole become a *line* — a graph about graphs — is
docs/SECOND_ORDER_FRONTIER.md.
"""

# The ladder, as data — the teaching order (docs/MATHEMATICS_FROM_THE_SHEET.md).
RUNGS: Sequence[Tuple[int, str, str]] = (
    (0, "the blank sheet", "Nothing is scribed; nothing is asserted."),
    (1, "a relation", "Peirce's primitive is the relative, not the number."),
    (2, "the scroll", "A cut in a cut is if–then; the line carries the variable."),
    (3, "the order", "P1–P6: cut depth IS quantifier alternation."),
    (4, "identity", "The line of identity is equality — and where that fails."),
    (5, "position", "A number is a place in the order, not an object."),
    (6, "the numeral", "'three' is a definition that unfolds to the chain."),
    (7, "addition", "Two laws grow the whole table; 2+3=5 is read off it."),
    (8, "the character of a proof", "Corollarial or theorematic, from the chain."),
    (9, "induction", "The sheet ends: a schema, not a graph."),
)


__all__ = [
    "P1_IRREFLEXIVE", "P2_TRANSITIVE", "P3_TRICHOTOMY", "P4_DISCRETE",
    "P5_LEAST", "P6_NO_GREATEST", "ORDER_AXIOMS", "EQUALITY_DEPARTURE",
    "SUM_BASE", "SUM_STEP", "SUM_LAWS", "NUMERAL_DEFINITIONS",
    "successor_chain", "numbers", "order_facts", "arithmetic_theory",
    "SumFact", "derive_sums", "check", "sum_claim",
    "INDUCTION_SCHEMA", "INDUCTION_NOTE", "RUNGS",
]
