"""
Ontology → EGIF encoder — the declarative front end for importing a T-box as an
existential-graph theory (``docs/CORPUS_AND_IMPORT_MODEL.md`` §2, the ``ontology``
import kind).

An ontology axiom is already a shape the corpus knows; this module just names the
constructors so *any* ontology imports declaratively rather than as a hand-written
EGIF blob:

    subsumes(A, B)        A ⊑ B        ∀x (A(x) → B(x))     ~[ (A *x) ~[ (B x) ] ]
    disjoint(A, B)        A ⊓ B ⊑ ⊥    ∀x ¬(A(x) ∧ B(x))    ~[ (A *x) (B x) ]
    domain(R, n, k, C)    arg n of R typed C                ~[ (R …*x…) ~[ (C x) ] ]
    instance(name, C)     C(name)      an A-box assertion    (C "name")

A subsumption is the universal-conditional **scroll** — the same shape as the
man–mortal example and Barbara's premises; an ontology is their conjunction on one
sheet.  Equality / n-ary relations and richer axioms (modal, higher-order) are
*not* first-order-EG-expressible and are out of scope here — an honest importer
reports what it could not bring across (see ``tools/suokif_to_eg.py``).

Each axiom lives in its own cut, so a defining label (``*x``) is scoped to that
cut; the builder still hands out a fresh label per axiom for legibility.  The
resulting EGIF parses, round-trips, and §3.3-attests like any other corpus graph.
"""

from typing import List, Optional


def _ident(name: str) -> str:
    """Validate a class/relation name as an EGIF identifier (the predicate-name
    rule: a letter then alphanumerics).  Ontology vocabularies that use other
    characters must sanitize before reaching the graph — the importer's job."""
    if not name or not name[0].isalpha() or not name.isalnum():
        raise ValueError(
            f"ontology_egif: {name!r} is not a valid EGIF predicate identifier "
            "(letter followed by alphanumerics); sanitize the vocabulary first"
        )
    return name


class OntologyEGIF:
    """Accumulates ontology axioms as EGIF fragments, then assembles the theory.

    Fluent: ``OntologyEGIF().subsumes("Dog", "Mammal").disjoint("Dog", "Cat").egif()``.
    Tracks the vocabulary (classes / relations / individuals) it has seen, for the
    importer's report.
    """

    def __init__(self) -> None:
        self._frags: List[str] = []
        self._n = 0
        self.classes: set = set()
        self.relations: set = set()
        self.individuals: set = set()

    def _fresh(self) -> str:
        self._n += 1
        return f"x{self._n}"

    def subsumes(self, sub: str, sup: str) -> "OntologyEGIF":
        """``sub ⊑ sup`` — every sub is a sup (a subsumption scroll)."""
        _ident(sub); _ident(sup)
        v = self._fresh()
        self._frags.append(f"~[ ({sub} *{v}) ~[ ({sup} {v}) ] ]")
        self.classes.update((sub, sup))
        return self

    def disjoint(self, a: str, b: str) -> "OntologyEGIF":
        """``a ⊓ b ⊑ ⊥`` — nothing is both an a and a b."""
        _ident(a); _ident(b)
        v = self._fresh()
        self._frags.append(f"~[ ({a} *{v}) ({b} {v}) ]")
        self.classes.update((a, b))
        return self

    def domain(self, relation: str, arity: int, position: int, cls: str) -> "OntologyEGIF":
        """Type argument ``position`` (1-based) of ``relation`` (an ``arity``-ary
        relation) to class ``cls``: ∀… (R(…) → cls(arg_position)).  A
        ``domain``/``range`` constraint is just argument typing."""
        _ident(relation); _ident(cls)
        if not (1 <= position <= arity):
            raise ValueError(f"position {position} out of range for arity {arity}")
        vs = [self._fresh() for _ in range(arity)]
        args = " ".join(f"*{v}" for v in vs)
        typed = vs[position - 1]
        self._frags.append(f"~[ ({relation} {args}) ~[ ({cls} {typed}) ] ]")
        self.relations.add(relation)
        self.classes.add(cls)
        return self

    def instance(self, name: str, cls: str) -> "OntologyEGIF":
        """An A-box assertion ``cls(name)`` — a named individual typed by a class."""
        _ident(cls)
        self._frags.append(f'({cls} "{name}")')
        self.classes.add(cls)
        self.individuals.add(name)
        return self

    def egif(self) -> str:
        """The whole theory as one EGIF string (the conjunction of all axioms)."""
        return " ".join(self._frags)

    def __len__(self) -> int:
        return len(self._frags)


# Module-level fragment helpers (for callers that just want a single axiom). ---

def subsumes(sub: str, sup: str, var: str = "x") -> str:
    _ident(sub); _ident(sup)
    return f"~[ ({sub} *{var}) ~[ ({sup} {var}) ] ]"


def disjoint(a: str, b: str, var: str = "x") -> str:
    _ident(a); _ident(b)
    return f"~[ ({a} *{var}) ({b} {var}) ]"


def instance(name: str, cls: str) -> str:
    _ident(cls)
    return f'({cls} "{name}")'


__all__ = ["OntologyEGIF", "subsumes", "disjoint", "instance"]
